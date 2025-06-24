import React, { useState, useEffect, useCallback, useRef } from 'react'
import './GymnasiumRLMonitor.scss'

// API 响应类型定义
interface TrainingSession {
    session_id: string
    algorithm: string
    status: 'idle' | 'running' | 'paused' | 'completed' | 'failed' | 'stopped'
    start_time?: string
    end_time?: string
    current_episode: number
    total_episodes: number
    current_reward: number
    average_reward: number
    best_reward: number
    success_rate: number
    training_time_seconds: number
    progress_percent: number
    estimated_remaining_seconds?: number
    error_message?: string
}

interface SystemStatus {
    status: string
    system_resources: {
        cpu_percent: number
        memory_percent: number
        disk_percent: number
        available_memory_gb: number
    }
    available_models: Array<{
        name: string
        size_mb: number
        created: string
    }>
    active_training_sessions: number
    total_sessions: number
    supported_algorithms: string[]
    timestamp: string
}

interface TrainingConfig {
    algorithm: 'dqn' | 'ppo' | 'sac'
    episodes: number
    learning_rate: number
    batch_size: number
    buffer_size: number
    environment_config: {
        num_ues: number
        num_satellites: number
        simulation_time: number
    }
    save_frequency: number
    evaluation_frequency: number
}

interface AlgorithmComparisonResult {
    comparison_id: string
    status: 'starting' | 'running' | 'completed' | 'failed'
    progress_percent: number
    algorithms: string[]
    completed_algorithms: string[]
    start_time: string
    results: Record<string, any>
    error_message?: string
}

const EnhancedRLMonitor: React.FC = () => {
    // 状态管理
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
    const [trainingSessions, setTrainingSessions] = useState<TrainingSession[]>([])
    const [activeSession, setActiveSession] = useState<TrainingSession | null>(null)
    const [comparisonResults, setComparisonResults] = useState<AlgorithmComparisonResult | null>(null)
    
    // UI 状态
    const [selectedTab, setSelectedTab] = useState<'monitoring' | 'training' | 'comparison'>('monitoring')
    const [autoRefresh, setAutoRefresh] = useState(true)
    const [showTrainingConfig, setShowTrainingConfig] = useState(false)
    const [showComparisonConfig, setShowComparisonConfig] = useState(false)
    
    // 配置状态
    const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>({
        algorithm: 'dqn',
        episodes: 1000,
        learning_rate: 0.0003,
        batch_size: 64,
        buffer_size: 100000,
        environment_config: {
            num_ues: 5,
            num_satellites: 10,
            simulation_time: 100.0
        },
        save_frequency: 100,
        evaluation_frequency: 50
    })
    
    const [comparisonConfig, setComparisonConfig] = useState({
        algorithms: ['dqn', 'ppo', 'sac', 'infocom2024', 'simple_threshold'],
        test_scenarios: 100
    })
    
    const intervalRef = useRef<NodeJS.Timeout | null>(null)
    
    // API 调用函数
    const fetchSystemStatus = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/rl/status')
            if (response.ok) {
                const data = await response.json()
                setSystemStatus(data)
            }
        } catch (error) {
            console.error('Failed to fetch system status:', error)
        }
    }, [])
    
    const fetchTrainingSessions = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/rl/training/sessions?limit=10')
            if (response.ok) {
                const data = await response.json()
                setTrainingSessions(data.sessions)
            }
        } catch (error) {
            console.error('Failed to fetch training sessions:', error)
        }
    }, [])
    
    const fetchActiveSession = useCallback(async (sessionId: string) => {
        try {
            const response = await fetch(`/api/v1/rl/training/${sessionId}/status`)
            if (response.ok) {
                const data = await response.json()
                setActiveSession(data)
            }
        } catch (error) {
            console.error('Failed to fetch active session:', error)
        }
    }, [])
    
    const startTraining = async () => {
        try {
            const response = await fetch('/api/v1/rl/training/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(trainingConfig)
            })
            
            if (response.ok) {
                const result = await response.json()
                setShowTrainingConfig(false)
                // 开始监控新的训练会话
                setActiveSession({
                    session_id: result.session_id,
                    algorithm: trainingConfig.algorithm,
                    status: 'running',
                    current_episode: 0,
                    total_episodes: trainingConfig.episodes,
                    current_reward: 0,
                    average_reward: 0,
                    best_reward: 0,
                    success_rate: 0,
                    training_time_seconds: 0,
                    progress_percent: 0
                })
                await fetchTrainingSessions()
            }
        } catch (error) {
            console.error('Failed to start training:', error)
        }
    }
    
    const stopTraining = async (sessionId: string) => {
        try {
            const response = await fetch(`/api/v1/rl/training/${sessionId}/stop`, {
                method: 'POST'
            })
            
            if (response.ok) {
                await fetchTrainingSessions()
                if (activeSession?.session_id === sessionId) {
                    setActiveSession(null)
                }
            }
        } catch (error) {
            console.error('Failed to stop training:', error)
        }
    }
    
    const startComparison = async () => {
        try {
            const response = await fetch('/api/v1/rl/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    algorithms: comparisonConfig.algorithms,
                    test_scenarios: comparisonConfig.test_scenarios,
                    environment_config: {
                        num_ues: 5,
                        num_satellites: 10
                    }
                })
            })
            
            if (response.ok) {
                const result = await response.json()
                setComparisonResults({
                    comparison_id: result.comparison_id,
                    status: 'starting',
                    progress_percent: 0,
                    algorithms: result.algorithms,
                    completed_algorithms: [],
                    start_time: new Date().toISOString(),
                    results: {}
                })
                setShowComparisonConfig(false)
            }
        } catch (error) {
            console.error('Failed to start comparison:', error)
        }
    }
    
    const fetchComparisonStatus = useCallback(async (comparisonId: string) => {
        try {
            const response = await fetch(`/api/v1/rl/compare/${comparisonId}/status`)
            if (response.ok) {
                const data = await response.json()
                setComparisonResults(data)
            }
        } catch (error) {
            console.error('Failed to fetch comparison status:', error)
        }
    }, [])
    
    // 自动刷新逻辑
    useEffect(() => {
        if (autoRefresh) {
            intervalRef.current = setInterval(() => {
                fetchSystemStatus()
                fetchTrainingSessions()
                
                if (activeSession?.status === 'running') {
                    fetchActiveSession(activeSession.session_id)
                }
                
                if (comparisonResults?.status === 'running') {
                    fetchComparisonStatus(comparisonResults.comparison_id)
                }
            }, 3000)
            
            // 立即执行一次
            fetchSystemStatus()
            fetchTrainingSessions()
        } else {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
        
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [autoRefresh, activeSession, comparisonResults, fetchSystemStatus, fetchTrainingSessions, fetchActiveSession, fetchComparisonStatus])
    
    // 工具函数
    const formatDuration = (seconds: number): string => {
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        const secs = Math.floor(seconds % 60)
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'running': return '#28a745'
            case 'completed': return '#17a2b8'
            case 'failed': case 'error': return '#dc3545'
            case 'stopped': case 'paused': return '#ffc107'
            default: return '#6c757d'
        }
    }
    
    const getResourceColor = (percentage: number): string => {
        if (percentage < 50) return '#28a745'
        if (percentage < 80) return '#ffc107'
        return '#dc3545'
    }
    
    return (
        <div className="gymnasium-rl-monitor enhanced">
            {/* 顶部导航 */}
            <div className="monitor-header">
                <h2>🧠 Enhanced RL Training Monitor</h2>
                <div className="header-controls">
                    <div className="tab-selector">
                        <button 
                            className={selectedTab === 'monitoring' ? 'active' : ''}
                            onClick={() => setSelectedTab('monitoring')}
                        >
                            📊 监控
                        </button>
                        <button 
                            className={selectedTab === 'training' ? 'active' : ''}
                            onClick={() => setSelectedTab('training')}
                        >
                            🎯 训练
                        </button>
                        <button 
                            className={selectedTab === 'comparison' ? 'active' : ''}
                            onClick={() => setSelectedTab('comparison')}
                        >
                            🏆 对比
                        </button>
                    </div>
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                        />
                        自动刷新
                    </label>
                </div>
            </div>
            
            {/* 系统状态概览 */}
            {systemStatus && (
                <div className="system-overview">
                    <div className="status-card">
                        <h4>🖥️ 系统资源</h4>
                        <div className="resource-metrics">
                            <div className="resource-item">
                                <span>CPU</span>
                                <div className="resource-bar">
                                    <div 
                                        className="resource-fill"
                                        style={{ 
                                            width: `${systemStatus.system_resources.cpu_percent}%`,
                                            backgroundColor: getResourceColor(systemStatus.system_resources.cpu_percent)
                                        }}
                                    />
                                    <span>{systemStatus.system_resources.cpu_percent.toFixed(1)}%</span>
                                </div>
                            </div>
                            <div className="resource-item">
                                <span>内存</span>
                                <div className="resource-bar">
                                    <div 
                                        className="resource-fill"
                                        style={{ 
                                            width: `${systemStatus.system_resources.memory_percent}%`,
                                            backgroundColor: getResourceColor(systemStatus.system_resources.memory_percent)
                                        }}
                                    />
                                    <span>{systemStatus.system_resources.memory_percent.toFixed(1)}%</span>
                                </div>
                            </div>
                            <div className="resource-item">
                                <span>磁盘</span>
                                <div className="resource-bar">
                                    <div 
                                        className="resource-fill"
                                        style={{ 
                                            width: `${systemStatus.system_resources.disk_percent}%`,
                                            backgroundColor: getResourceColor(systemStatus.system_resources.disk_percent)
                                        }}
                                    />
                                    <span>{systemStatus.system_resources.disk_percent.toFixed(1)}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div className="status-card">
                        <h4>📈 训练状态</h4>
                        <div className="training-stats">
                            <div className="stat-item">
                                <span className="stat-label">活跃会话</span>
                                <span className="stat-value">{systemStatus.active_training_sessions}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">总会话数</span>
                                <span className="stat-value">{systemStatus.total_sessions}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">可用模型</span>
                                <span className="stat-value">{systemStatus.available_models.length}</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* 主要内容区域 */}
            <div className="monitor-content">
                {selectedTab === 'monitoring' && (
                    <div className="monitoring-tab">
                        {/* 活跃训练会话 */}
                        {activeSession && (
                            <div className="active-session">
                                <div className="session-header">
                                    <h3>🎯 活跃训练会话: {activeSession.session_id}</h3>
                                    <div className="session-controls">
                                        <span 
                                            className="status-indicator"
                                            style={{ backgroundColor: getStatusColor(activeSession.status) }}
                                        >
                                            {activeSession.status}
                                        </span>
                                        {activeSession.status === 'running' && (
                                            <button 
                                                className="stop-btn"
                                                onClick={() => stopTraining(activeSession.session_id)}
                                            >
                                                ⏹️ 停止
                                            </button>
                                        )}
                                    </div>
                                </div>
                                
                                <div className="session-metrics">
                                    <div className="metric-row">
                                        <div className="metric-item">
                                            <span className="metric-label">算法</span>
                                            <span className="metric-value">{activeSession.algorithm.toUpperCase()}</span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-label">进度</span>
                                            <span className="metric-value">{activeSession.progress_percent.toFixed(1)}%</span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-label">当前回合</span>
                                            <span className="metric-value">{activeSession.current_episode}/{activeSession.total_episodes}</span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-label">训练时间</span>
                                            <span className="metric-value">{formatDuration(activeSession.training_time_seconds)}</span>
                                        </div>
                                    </div>
                                    
                                    <div className="metric-row">
                                        <div className="metric-item">
                                            <span className="metric-label">当前奖励</span>
                                            <span className="metric-value">{activeSession.current_reward.toFixed(2)}</span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-label">平均奖励</span>
                                            <span className="metric-value">{activeSession.average_reward.toFixed(2)}</span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-label">最佳奖励</span>
                                            <span className="metric-value">{activeSession.best_reward.toFixed(2)}</span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-label">成功率</span>
                                            <span className="metric-value">{(activeSession.success_rate * 100).toFixed(1)}%</span>
                                        </div>
                                    </div>
                                    
                                    {/* 进度条 */}
                                    <div className="progress-section">
                                        <div className="progress-bar">
                                            <div 
                                                className="progress-fill"
                                                style={{ width: `${activeSession.progress_percent}%` }}
                                            />
                                        </div>
                                        {activeSession.estimated_remaining_seconds && (
                                            <div className="estimated-time">
                                                预计剩余: {formatDuration(activeSession.estimated_remaining_seconds)}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        {/* 训练会话历史 */}
                        <div className="sessions-history">
                            <h3>📚 训练会话历史</h3>
                            <div className="sessions-list">
                                {trainingSessions.map((session) => (
                                    <div key={session.session_id} className="session-item">
                                        <div className="session-info">
                                            <span className="session-id">{session.session_id}</span>
                                            <span className="session-algorithm">{session.algorithm.toUpperCase()}</span>
                                            <span 
                                                className="session-status"
                                                style={{ color: getStatusColor(session.status) }}
                                            >
                                                {session.status}
                                            </span>
                                        </div>
                                        <div className="session-stats">
                                            <span>进度: {session.progress_percent.toFixed(1)}%</span>
                                            <span>平均奖励: {session.average_reward.toFixed(2)}</span>
                                        </div>
                                        <div className="session-actions">
                                            <button 
                                                onClick={() => fetchActiveSession(session.session_id)}
                                                disabled={session.status === 'failed'}
                                            >
                                                👁️ 查看
                                            </button>
                                            {session.status === 'running' && (
                                                <button 
                                                    onClick={() => stopTraining(session.session_id)}
                                                    className="danger"
                                                >
                                                    ⏹️ 停止
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
                
                {selectedTab === 'training' && (
                    <div className="training-tab">
                        <div className="training-controls">
                            <h3>🎯 启动新的训练会话</h3>
                            <button 
                                className="config-btn"
                                onClick={() => setShowTrainingConfig(true)}
                            >
                                ⚙️ 配置训练参数
                            </button>
                        </div>
                        
                        {showTrainingConfig && (
                            <div className="config-modal">
                                <div className="config-content">
                                    <h4>训练配置</h4>
                                    
                                    <div className="config-section">
                                        <label>算法</label>
                                        <select 
                                            value={trainingConfig.algorithm}
                                            onChange={(e) => setTrainingConfig({
                                                ...trainingConfig,
                                                algorithm: e.target.value as 'dqn' | 'ppo' | 'sac'
                                            })}
                                        >
                                            <option value="dqn">DQN</option>
                                            <option value="ppo">PPO</option>
                                            <option value="sac">SAC</option>
                                        </select>
                                    </div>
                                    
                                    <div className="config-section">
                                        <label>训练回合数</label>
                                        <input 
                                            type="number"
                                            value={trainingConfig.episodes}
                                            onChange={(e) => setTrainingConfig({
                                                ...trainingConfig,
                                                episodes: parseInt(e.target.value)
                                            })}
                                        />
                                    </div>
                                    
                                    <div className="config-section">
                                        <label>学习率</label>
                                        <input 
                                            type="number"
                                            step="0.0001"
                                            value={trainingConfig.learning_rate}
                                            onChange={(e) => setTrainingConfig({
                                                ...trainingConfig,
                                                learning_rate: parseFloat(e.target.value)
                                            })}
                                        />
                                    </div>
                                    
                                    <div className="config-section">
                                        <label>批次大小</label>
                                        <input 
                                            type="number"
                                            value={trainingConfig.batch_size}
                                            onChange={(e) => setTrainingConfig({
                                                ...trainingConfig,
                                                batch_size: parseInt(e.target.value)
                                            })}
                                        />
                                    </div>
                                    
                                    <div className="config-actions">
                                        <button onClick={startTraining} className="primary">
                                            🚀 开始训练
                                        </button>
                                        <button onClick={() => setShowTrainingConfig(false)}>
                                            ❌ 取消
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
                
                {selectedTab === 'comparison' && (
                    <div className="comparison-tab">
                        <div className="comparison-controls">
                            <h3>🏆 算法性能对比</h3>
                            <button 
                                className="config-btn"
                                onClick={() => setShowComparisonConfig(true)}
                            >
                                ⚙️ 配置对比参数
                            </button>
                        </div>
                        
                        {showComparisonConfig && (
                            <div className="config-modal">
                                <div className="config-content">
                                    <h4>对比配置</h4>
                                    
                                    <div className="config-section">
                                        <label>选择算法</label>
                                        <div className="algorithm-checkboxes">
                                            {['dqn', 'ppo', 'sac', 'infocom2024', 'simple_threshold', 'random'].map(algo => (
                                                <label key={algo} className="checkbox-label">
                                                    <input 
                                                        type="checkbox"
                                                        checked={comparisonConfig.algorithms.includes(algo)}
                                                        onChange={(e) => {
                                                            if (e.target.checked) {
                                                                setComparisonConfig({
                                                                    ...comparisonConfig,
                                                                    algorithms: [...comparisonConfig.algorithms, algo]
                                                                })
                                                            } else {
                                                                setComparisonConfig({
                                                                    ...comparisonConfig,
                                                                    algorithms: comparisonConfig.algorithms.filter(a => a !== algo)
                                                                })
                                                            }
                                                        }}
                                                    />
                                                    {algo.toUpperCase()}
                                                </label>
                                            ))}
                                        </div>
                                    </div>
                                    
                                    <div className="config-section">
                                        <label>测试场景数量</label>
                                        <input 
                                            type="number"
                                            value={comparisonConfig.test_scenarios}
                                            onChange={(e) => setComparisonConfig({
                                                ...comparisonConfig,
                                                test_scenarios: parseInt(e.target.value)
                                            })}
                                        />
                                    </div>
                                    
                                    <div className="config-actions">
                                        <button onClick={startComparison} className="primary">
                                            🏁 开始对比
                                        </button>
                                        <button onClick={() => setShowComparisonConfig(false)}>
                                            ❌ 取消
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        {comparisonResults && (
                            <div className="comparison-results">
                                <h4>对比结果: {comparisonResults.comparison_id}</h4>
                                <div className="comparison-progress">
                                    <div className="progress-bar">
                                        <div 
                                            className="progress-fill"
                                            style={{ width: `${comparisonResults.progress_percent}%` }}
                                        />
                                    </div>
                                    <span>{comparisonResults.progress_percent.toFixed(1)}% 完成</span>
                                </div>
                                
                                <div className="algorithm-progress">
                                    {comparisonResults.algorithms.map(algo => (
                                        <div key={algo} className="algo-item">
                                            <span className="algo-name">{algo.toUpperCase()}</span>
                                            <span className={`algo-status ${
                                                comparisonResults.completed_algorithms.includes(algo) ? 'completed' : 'pending'
                                            }`}>
                                                {comparisonResults.completed_algorithms.includes(algo) ? '✅' : '⏳'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                                
                                {comparisonResults.status === 'completed' && Object.keys(comparisonResults.results).length > 0 && (
                                    <div className="results-table">
                                        <h5>对比结果</h5>
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>算法</th>
                                                    <th>平均延迟</th>
                                                    <th>成功率</th>
                                                    <th>决策时间</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {Object.entries(comparisonResults.results).map(([algo, result]: [string, any]) => (
                                                    <tr key={algo}>
                                                        <td>{algo.toUpperCase()}</td>
                                                        <td>{result.average_latency?.toFixed(2) || 'N/A'}</td>
                                                        <td>{result.success_rate ? (result.success_rate * 100).toFixed(1) + '%' : 'N/A'}</td>
                                                        <td>{result.average_decision_time?.toFixed(2) || 'N/A'}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}

export default EnhancedRLMonitor