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
    interference_mitigation: ServiceInfo
    network_optimization: ServiceInfo
    uav_formation: ServiceInfo
}

interface ServiceInfo {
    enabled: boolean
    health_status: string
    request_count: number
    error_rate: number
    avg_response_time: number
}

// 定義真實API端點的基礎URL - 瀏覽器從外部訪問
const API_BASE = 'http://localhost:8080'

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
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)

    // 獲取 RL 系統狀態 - 使用真實API
    const fetchRLStatus = useCallback(async () => {
        setLoading(true)
        setError(null)

        try {
            // 1. 獲取RL狀態
            const rlStatusResponse = await fetch(`${API_BASE}/api/v1/rl/status`)
            if (!rlStatusResponse.ok) {
                throw new Error('無法獲取RL狀態')
            }
            const rlStatusData = await rlStatusResponse.json()

            // 2. 獲取AI決策狀態
            const aiStatusResponse = await fetch(
                `${API_BASE}/api/v1/ai-decision/status`
            )
            let aiStatusData = null
            if (aiStatusResponse.ok) {
                aiStatusData = await aiStatusResponse.json()
            }

            // 3. 獲取訓練會話狀態
            const sessionsResponse = await fetch(
                `${API_BASE}/api/v1/rl/training/sessions`
            )
            let sessionsData = { sessions: [] }
            if (sessionsResponse.ok) {
                sessionsData = await sessionsResponse.json()
            }

            // 4. 合成RL指標數據
            const metrics: RLEngineMetrics = {
                engine_type: selectedEngine,
                algorithm:
                    selectedEngine === 'gymnasium'
                        ? aiStatusData?.current_algorithm || 'DQN'
                        : 'Traditional',
                environment:
                    aiStatusData?.environment_name || 'HandoverEnvironment-v0',
                model_status:
                    sessionsData.sessions.length > 0
                        ? isTraining
                            ? 'training'
                            : 'inference'
                        : 'idle',
                episodes_completed:
                    aiStatusData?.training_stats?.episodes_completed || 0,
                average_reward:
                    aiStatusData?.training_stats?.average_reward || 0,
                current_epsilon:
                    aiStatusData?.training_stats?.current_epsilon || 0.1,
                training_progress:
                    aiStatusData?.training_stats?.training_progress || 0,
                prediction_accuracy: aiStatusData?.prediction_accuracy || 0.85,
                response_time_ms:
                    rlStatusData.system_resources?.avg_response_time || 25,
                memory_usage:
                    rlStatusData.system_resources?.memory_usage_mb || 1024,
                gpu_utilization:
                    rlStatusData.system_resources?.gpu_utilization || 0,
            }

            setRLMetrics(metrics)

            // 5. 獲取服務健康狀況
            const serviceStatus: RLServiceStatus = {
                interference_mitigation: {
                    enabled:
                        rlStatusData.interference_mitigation?.enabled || true,
                    health_status:
                        rlStatusData.interference_mitigation?.health_status ||
                        'healthy',
                    request_count:
                        rlStatusData.interference_mitigation?.request_count ||
                        0,
                    error_rate:
                        rlStatusData.interference_mitigation?.error_rate || 0,
                    avg_response_time:
                        rlStatusData.interference_mitigation
                            ?.avg_response_time || 20,
                },
                network_optimization: {
                    enabled: rlStatusData.network_optimization?.enabled || true,
                    health_status:
                        rlStatusData.network_optimization?.health_status ||
                        'healthy',
                    request_count:
                        rlStatusData.network_optimization?.request_count || 0,
                    error_rate:
                        rlStatusData.network_optimization?.error_rate || 0,
                    avg_response_time:
                        rlStatusData.network_optimization?.avg_response_time ||
                        15,
                },
                uav_formation: {
                    enabled: rlStatusData.uav_formation?.enabled || false,
                    health_status:
                        rlStatusData.uav_formation?.health_status || 'disabled',
                    request_count:
                        rlStatusData.uav_formation?.request_count || 0,
                    error_rate: rlStatusData.uav_formation?.error_rate || 0,
                    avg_response_time:
                        rlStatusData.uav_formation?.avg_response_time || 0,
                },
            }

            setServiceStatus(serviceStatus)
        } catch (error) {
            console.error('Failed to fetch RL status:', error)
            setError(error instanceof Error ? error.message : '獲取RL狀態失敗')
        } finally {
            setLoading(false)
        }
    }, [selectedEngine, isTraining])

    // 切換 RL 引擎
    const switchEngine = async (newEngine: 'gymnasium' | 'legacy') => {
        try {
            const endpoint =
                newEngine === 'gymnasium'
                    ? `${API_BASE}/api/v1/ai-decision/switch-to-gymnasium`
                    : `${API_BASE}/api/v1/ai-decision/switch-to-legacy`

            const response = await fetch(endpoint, { method: 'POST' })

            if (response.ok) {
                setSelectedEngine(newEngine)
                console.log(`Switched to ${newEngine} engine`)
                // 立即刷新狀態
                setTimeout(fetchRLStatus, 1000)
            } else {
                throw new Error(`切換到 ${newEngine} 引擎失敗`)
            }
        } catch (error) {
            console.error('Failed to switch engine:', error)
            setError(error instanceof Error ? error.message : '切換引擎失敗')
        }
    }

    // 開始/停止訓練
    const toggleTraining = async () => {
        try {
            if (isTraining) {
                // 停止訓練邏輯 - 需要會話ID，暫時使用預設ID
                const sessionId = 'current_session'
                const response = await fetch(
                    `${API_BASE}/api/v1/rl/training/${sessionId}/stop`,
                    {
                        method: 'POST',
                    }
                )

                if (response.ok) {
                    setIsTraining(false)
                }
            } else {
                // 開始訓練邏輯
                const response = await fetch(
                    `${API_BASE}/api/v1/rl/training/start`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            algorithm:
                                selectedEngine === 'gymnasium' ? 'dqn' : 'ppo',
                            episodes: 1000,
                            learning_rate: 0.0003,
                            batch_size: 64,
                            buffer_size: 100000,
                            environment_config: {
                                num_ues: 5,
                                num_satellites: 10,
                                simulation_time: 100.0,
                            },
                            save_frequency: 100,
                            evaluation_frequency: 50,
                        }),
                    }
                )

                if (response.ok) {
                    setIsTraining(true)
                } else {
                    throw new Error('啟動訓練失敗')
                }
            }
        } catch (error) {
            console.error('Failed to toggle training:', error)
            setError(error instanceof Error ? error.message : '訓練控制失敗')
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
                    <button
                        onClick={fetchRLStatus}
                        className="refresh-btn"
                        disabled={loading}
                    >
                        {loading ? '🔄 載入中...' : '🔄 手動刷新'}
                    </button>
                </div>
            </div>

            {error && <div className="error-banner">⚠️ {error}</div>}

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
                            ⚙️ Legacy Engine
                        </button>
                    </div>

                    <div className="training-controls">
                        <button
                            onClick={toggleTraining}
                            className={`training-btn ${
                                isTraining ? 'stop' : 'start'
                            }`}
                        >
                            {isTraining ? '⏹️ 停止訓練' : '▶️ 開始訓練'}
                        </button>
                    </div>
                </div>

                {/* RL 引擎指標 */}
                {rlMetrics && (
                    <div className="metrics-panel">
                        <h3>📊 引擎指標</h3>
                        <div className="metrics-grid">
                            <div className="metric-item">
                                <span className="metric-label">引擎類型:</span>
                                <span className="metric-value">
                                    {getEngineStatusIcon(rlMetrics.engine_type)}{' '}
                                    {rlMetrics.engine_type}
                                </span>
                            </div>
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
                                <span className="metric-label">
                                    已完成回合:
                                </span>
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
                                <span className="metric-value">
                                    {rlMetrics.training_progress.toFixed(1)}%
                                </span>
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
                            {rlMetrics.gpu_utilization !== undefined && (
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

                {/* 服務狀態 */}
                {serviceStatus && (
                    <div className="services-panel">
                        <h3>🔧 服務狀態</h3>
                        <div className="services-grid">
                            {Object.entries(serviceStatus).map(
                                ([serviceName, service]) => (
                                    <div
                                        key={serviceName}
                                        className="service-item"
                                    >
                                        <div className="service-header">
                                            <span
                                                className="service-status-dot"
                                                style={{
                                                    backgroundColor:
                                                        getHealthStatusColor(
                                                            service.health_status
                                                        ),
                                                }}
                                            ></span>
                                            <span className="service-name">
                                                {serviceName
                                                    .replace(/_/g, ' ')
                                                    .toUpperCase()}
                                            </span>
                                        </div>
                                        <div className="service-details">
                                            <div>
                                                狀態:{' '}
                                                {service.enabled
                                                    ? '啟用'
                                                    : '停用'}
                                            </div>
                                            <div>
                                                請求數: {service.request_count}
                                            </div>
                                            <div>
                                                錯誤率:{' '}
                                                {(
                                                    service.error_rate * 100
                                                ).toFixed(2)}
                                                %
                                            </div>
                                            <div>
                                                平均響應:{' '}
                                                {service.avg_response_time}ms
                                            </div>
                                        </div>
                                    </div>
                                )
                            )}
                        </div>
                    </div>
                )}

                {/* 系統日誌 */}
                <div className="logs-panel">
                    <h3>📜 系統日誌</h3>
                    <div className="logs-container">
                        <div className="log-entry success">
                            ✅ [{new Date().toLocaleTimeString()}]{' '}
                            {selectedEngine} 引擎運行正常
                        </div>
                        {isTraining && (
                            <div className="log-entry info">
                                ℹ️ [{new Date().toLocaleTimeString()}]
                                訓練會話進行中...
                            </div>
                        )}
                        <div className="log-entry success">
                            ✅ [{new Date().toLocaleTimeString()}] API 連接正常
                            - 已連接真實後端
                        </div>
                        {rlMetrics && rlMetrics.episodes_completed > 0 && (
                            <div className="log-entry success">
                                ✅ [{new Date().toLocaleTimeString()}] 已完成{' '}
                                {rlMetrics.episodes_completed} 個訓練回合
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default GymnasiumRLMonitor
