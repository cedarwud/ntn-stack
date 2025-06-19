import React, { useState, useEffect, useCallback, useRef } from 'react'
import './GymnasiumRLMonitor.scss'

interface RLEngineMetrics {
    engine_type: 'gymnasium' | 'legacy' | 'null'
    algorithm: string
    environment: string
    model_status: 'training' | 'inference' | 'idle' | 'error'
    episodes_completed: number
    average_reward: number
    current_epsilon: number
    training_progress: number
    prediction_accuracy: number
    response_time_ms: number
    memory_usage: number
    gpu_utilization?: number
}

// Note: Removed unused interfaces EnvironmentState and DecisionHistory
// They can be re-added when needed for future features

interface RLServiceStatus {
    interference_mitigation: {
        enabled: boolean
        health_status: string
        request_count: number
        error_rate: number
        avg_response_time: number
    }
    network_optimization: {
        enabled: boolean
        health_status: string
        request_count: number
        error_rate: number
        avg_response_time: number
    }
    uav_formation: {
        enabled: boolean
        health_status: string
        request_count: number
        error_rate: number
        avg_response_time: number
    }
}

const GymnasiumRLMonitor: React.FC = () => {
    const [rlMetrics, setRLMetrics] = useState<RLEngineMetrics | null>(null)
    const [serviceStatus, setServiceStatus] = useState<RLServiceStatus | null>(
        null
    )
    const [selectedEngine, setSelectedEngine] = useState<
        'gymnasium' | 'legacy'
    >('gymnasium')
    const [isTraining, setIsTraining] = useState(false)
    const [autoRefresh, setAutoRefresh] = useState(true)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)

    // 獲取 RL 系統狀態
    const fetchRLStatus = useCallback(async () => {
        try {
            await fetch('/api/v1/ai-decision/status')

            // 模擬 RL 指標數據
            const mockMetrics: RLEngineMetrics = {
                engine_type: selectedEngine,
                algorithm:
                    selectedEngine === 'gymnasium' ? 'DQN' : 'Traditional',
                environment: 'InterferenceMitigation-v0',
                model_status: isTraining ? 'training' : 'inference',
                episodes_completed: Math.floor(Math.random() * 1000) + 500,
                average_reward: Math.random() * 100 + 50,
                current_epsilon: Math.random() * 0.3 + 0.05,
                training_progress: Math.random() * 100,
                prediction_accuracy: Math.random() * 0.3 + 0.7,
                response_time_ms: Math.random() * 50 + 10,
                memory_usage: Math.random() * 2048 + 512,
                gpu_utilization: Math.random() * 100,
            }

            setRLMetrics(mockMetrics)

            // 模擬服務狀態
            const mockServiceStatus: RLServiceStatus = {
                interference_mitigation: {
                    enabled: true,
                    health_status: 'healthy',
                    request_count: Math.floor(Math.random() * 1000),
                    error_rate: Math.random() * 0.1,
                    avg_response_time: Math.random() * 100 + 20,
                },
                network_optimization: {
                    enabled: true,
                    health_status: Math.random() > 0.8 ? 'warning' : 'healthy',
                    request_count: Math.floor(Math.random() * 500),
                    error_rate: Math.random() * 0.05,
                    avg_response_time: Math.random() * 80 + 15,
                },
                uav_formation: {
                    enabled: false,
                    health_status: 'disabled',
                    request_count: 0,
                    error_rate: 0,
                    avg_response_time: 0,
                },
            }

            setServiceStatus(mockServiceStatus)
        } catch (error) {
            console.error('Failed to fetch RL status:', error)
        }
    }, [selectedEngine, isTraining])

    // 換手 RL 引擎
    const switchEngine = async (newEngine: 'gymnasium' | 'legacy') => {
        try {
            const endpoint =
                newEngine === 'gymnasium'
                    ? '/api/v1/ai-decision/switch-to-gymnasium'
                    : '/api/v1/ai-decision/switch-to-legacy'

            const response = await fetch(endpoint, { method: 'POST' })

            if (response.ok) {
                setSelectedEngine(newEngine)
                console.log(`Switched to ${newEngine} engine`)
            }
        } catch (error) {
            console.error('Failed to switch engine:', error)
        }
    }

    // 開始/停止訓練
    const toggleTraining = async () => {
        try {
            if (isTraining) {
                // 停止訓練的邏輯
                setIsTraining(false)
            } else {
                const response = await fetch(
                    '/api/v1/ai-decision/ai-ran/train',
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            training_episodes: 100,
                            save_interval: 50,
                        }),
                    }
                )

                if (response.ok) {
                    setIsTraining(true)
                }
            }
        } catch (error) {
            console.error('Failed to toggle training:', error)
        }
    }

    // 自動刷新
    useEffect(() => {
        if (autoRefresh) {
            intervalRef.current = setInterval(fetchRLStatus, 5000)
            fetchRLStatus() // 立即獲取一次
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
    }, [autoRefresh, fetchRLStatus])

    const getHealthStatusColor = (status: string) => {
        switch (status) {
            case 'healthy':
                return '#28a745'
            case 'warning':
                return '#ffc107'
            case 'error':
                return '#dc3545'
            case 'disabled':
                return '#6c757d'
            default:
                return '#17a2b8'
        }
    }

    const getEngineStatusIcon = (engineType: string) => {
        switch (engineType) {
            case 'gymnasium':
                return '🤖'
            case 'legacy':
                return '⚙️'
            case 'null':
                return '❌'
            default:
                return '❓'
        }
    }

    return (
        <div className="gymnasium-rl-monitor">
            <div className="monitor-header">
                <h2>🧠 Gymnasium RL 智能監控中心</h2>
                <div className="header-controls">
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                        />
                        自動刷新
                    </label>
                    <button onClick={fetchRLStatus} className="refresh-btn">
                        🔄 手動刷新
                    </button>
                </div>
            </div>

            <div className="monitor-grid">
                {/* 引擎控制面板 */}
                <div className="control-panel">
                    <h3>🎮 引擎控制</h3>
                    <div className="engine-selector">
                        <button
                            className={`engine-btn ${
                                selectedEngine === 'gymnasium' ? 'active' : ''
                            }`}
                            onClick={() => switchEngine('gymnasium')}
                        >
                            🤖 Gymnasium RL
                        </button>
                        <button
                            className={`engine-btn ${
                                selectedEngine === 'legacy' ? 'active' : ''
                            }`}
                            onClick={() => switchEngine('legacy')}
                        >
                            ⚙️ Traditional ML
                        </button>
                    </div>

                    <div className="training-controls">
                        <button
                            className={`training-btn ${
                                isTraining ? 'training' : ''
                            }`}
                            onClick={toggleTraining}
                        >
                            {isTraining ? '⏹️ 停止訓練' : '▶️ 開始訓練'}
                        </button>
                    </div>
                </div>

                {/* RL 引擎狀態 */}
                {rlMetrics && (
                    <div className="engine-metrics">
                        <h3>
                            {getEngineStatusIcon(rlMetrics.engine_type)}{' '}
                            引擎狀態
                        </h3>
                        <div className="metrics-grid">
                            <div className="metric-item">
                                <span className="metric-label">算法:</span>
                                <span className="metric-value">
                                    {rlMetrics.algorithm}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">環境:</span>
                                <span className="metric-value">
                                    {rlMetrics.environment}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">模型狀態:</span>
                                <span
                                    className={`metric-value status-${rlMetrics.model_status}`}
                                >
                                    {rlMetrics.model_status}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">完成集數:</span>
                                <span className="metric-value">
                                    {rlMetrics.episodes_completed}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">平均獎勵:</span>
                                <span className="metric-value">
                                    {rlMetrics.average_reward.toFixed(2)}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">
                                    探索率 (ε):
                                </span>
                                <span className="metric-value">
                                    {rlMetrics.current_epsilon.toFixed(3)}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">訓練進度:</span>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{
                                            width: `${rlMetrics.training_progress}%`,
                                        }}
                                    />
                                    <span className="progress-text">
                                        {rlMetrics.training_progress.toFixed(1)}
                                        %
                                    </span>
                                </div>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">
                                    預測準確率:
                                </span>
                                <span className="metric-value">
                                    {(
                                        rlMetrics.prediction_accuracy * 100
                                    ).toFixed(1)}
                                    %
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">響應時間:</span>
                                <span className="metric-value">
                                    {rlMetrics.response_time_ms.toFixed(1)}ms
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">
                                    記憶體使用:
                                </span>
                                <span className="metric-value">
                                    {rlMetrics.memory_usage.toFixed(0)}MB
                                </span>
                            </div>
                            {rlMetrics.gpu_utilization && (
                                <div className="metric-item">
                                    <span className="metric-label">
                                        GPU 使用率:
                                    </span>
                                    <span className="metric-value">
                                        {rlMetrics.gpu_utilization.toFixed(1)}%
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* 服務狀態總覽 */}
                {serviceStatus && (
                    <div className="service-status">
                        <h3>📊 服務狀態總覽</h3>
                        <div className="service-list">
                            {Object.entries(serviceStatus).map(
                                ([serviceName, status]) => (
                                    <div
                                        key={serviceName}
                                        className="service-item"
                                    >
                                        <div className="service-header">
                                            <span className="service-name">
                                                {serviceName
                                                    .replace(/_/g, ' ')
                                                    .toUpperCase()}
                                            </span>
                                            <span
                                                className="service-status-indicator"
                                                style={{
                                                    backgroundColor:
                                                        getHealthStatusColor(
                                                            status.health_status
                                                        ),
                                                }}
                                            />
                                        </div>
                                        <div className="service-metrics">
                                            <div className="service-metric">
                                                <span>
                                                    請求數:{' '}
                                                    {status.request_count}
                                                </span>
                                            </div>
                                            <div className="service-metric">
                                                <span>
                                                    錯誤率:{' '}
                                                    {(
                                                        status.error_rate * 100
                                                    ).toFixed(2)}
                                                    %
                                                </span>
                                            </div>
                                            <div className="service-metric">
                                                <span>
                                                    平均響應:{' '}
                                                    {status.avg_response_time.toFixed(
                                                        1
                                                    )}
                                                    ms
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                )
                            )}
                        </div>
                    </div>
                )}

                {/* 決策歷史圖表 */}
                <div className="decision-chart">
                    <h3>📈 決策效果趨勢</h3>
                    <div className="chart-placeholder">
                        <p>獎勵趨勢圖表</p>
                        <div className="mini-chart">
                            {/* 這裡可以集成 Chart.js 或其他圖表庫 */}
                            <div className="chart-line" />
                        </div>
                    </div>
                </div>

                {/* 實時日誌 */}
                <div className="realtime-logs">
                    <h3>📝 實時日誌</h3>
                    <div className="log-container">
                        <div className="log-entry success">
                            ✅ [14:15:30] Gymnasium DQN 決策成功 - 干擾緩解
                        </div>
                        <div className="log-entry info">
                            ℹ️ [14:15:25] 引擎換手至 Gymnasium 模式
                        </div>
                        <div className="log-entry warning">
                            ⚠️ [14:15:20] 網路優化服務響應時間較慢
                        </div>
                        <div className="log-entry success">
                            ✅ [14:15:15] AI-RAN 模型訓練完成 100 episodes
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default GymnasiumRLMonitor
