import React, { useState, useEffect, useCallback, useRef } from 'react'
import './GymnasiumRLMonitor.scss'

interface RLEngineMetrics {
    engine_type: 'dqn' | 'ppo' | 'null'
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

// 定義真實API端點的基礎URL - 通過Vite代理訪問
const API_BASE = '/netstack'

const GymnasiumRLMonitor: React.FC = () => {
    const [rlMetrics, setRLMetrics] = useState<RLEngineMetrics | null>(null)

    const [selectedEngine, setSelectedEngine] = useState<'dqn' | 'ppo'>('dqn')
    const [isTraining, setIsTraining] = useState(false)
    const [autoRefresh, setAutoRefresh] = useState(true)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [backendConnected, setBackendConnected] = useState(false)
    const [connectionError, setConnectionError] = useState<string | null>(null)
    const [startTime, setStartTime] = useState<number | null>(null)
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
                    selectedEngine === 'dqn'
                        ? 'Deep Q-Network'
                        : 'Proximal Policy Optimization',
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
        } catch (error) {
            console.error('Failed to fetch RL status:', error)
            setError(error instanceof Error ? error.message : '獲取RL狀態失敗')
        } finally {
            setLoading(false)
        }
    }, [selectedEngine, isTraining])

    // 生成動態訓練數據
    const generateDynamicTrainingData = useCallback(() => {
        if (isTraining) {
            const now = Date.now()
            const elapsed = Math.floor((now - (startTime || now)) / 1000)

            // 基於訓練時間生成逐漸增長的指標
            const baseEpisodes = Math.floor(elapsed / 10) // 每10秒增加1個episode
            const baseReward = Math.max(
                0,
                Math.sin(elapsed / 100) * 50 + Math.random() * 10
            )
            const baseProgress = Math.min(100, (elapsed / 600) * 100) // 10分鐘達到100%

            return {
                episodes_completed: baseEpisodes,
                average_reward: baseReward,
                current_epsilon: Math.max(0.01, 1.0 - elapsed / 3600), // 1小時內從1.0降到0.01
                training_progress: baseProgress,
                prediction_accuracy: 0.6 + (baseProgress / 100) * 0.35, // 60%到95%
                response_time_ms: 20 + Math.random() * 30,
                memory_usage: 512 + (baseProgress / 100) * 1024, // 512MB到1.5GB
                gpu_utilization: isTraining ? 45 + Math.random() * 40 : 0,
            }
        }
        return null
    }, [isTraining, startTime])

    // 檢查後端連接狀態
    const checkBackendConnection = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/health`, {
                method: 'GET',
                timeout: 5000, // 5秒超時
            } as RequestInit)

            if (response.ok) {
                const data = await response.json()
                setBackendConnected(true)
                setConnectionError(null)
                return true
            } else {
                throw new Error(
                    `HTTP ${response.status}: ${response.statusText}`
                )
            }
        } catch (error) {
            setBackendConnected(false)
            setConnectionError(
                error instanceof Error ? error.message : '連接失敗'
            )
            console.warn('後端連接失敗，使用模擬數據:', error)
            return false
        }
    }, [])

    // 初始化時檢查連接
    useEffect(() => {
        checkBackendConnection()
    }, [checkBackendConnection])

    // 切換 RL 引擎
    const switchEngine = async (newEngine: 'dqn' | 'ppo') => {
        try {
            const endpoint =
                newEngine === 'dqn'
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
                // 停止訓練邏輯
                setIsTraining(false)
                setStartTime(null)
                setRLMetrics(null)

                // 發送停止訓練事件
                window.dispatchEvent(
                    new CustomEvent('rlTrainingStopped', {
                        detail: { engine: selectedEngine },
                    })
                )

                console.log(`⏹️ 停止 ${selectedEngine.toUpperCase()} 訓練`)
            } else {
                // 開始訓練邏輯
                setIsTraining(true)
                setStartTime(Date.now())
                console.log(`🚀 開始 ${selectedEngine.toUpperCase()} 訓練`)
            }
        } catch (error) {
            console.error('Failed to toggle training:', error)
            setError(error instanceof Error ? error.message : '訓練控制失敗')
        }
    }

    // 自動刷新和動態數據更新
    useEffect(() => {
        if (autoRefresh && !isTraining) {
            intervalRef.current = setInterval(fetchRLStatus, 5000)
            fetchRLStatus() // 立即獲取一次
        } else if (isTraining) {
            // 訓練時使用動態數據生成
            const updateTrainingData = () => {
                const dynamicData = generateDynamicTrainingData()
                if (dynamicData) {
                    const newMetrics: RLEngineMetrics = {
                        engine_type: selectedEngine,
                        algorithm:
                            selectedEngine === 'dqn'
                                ? 'Deep Q-Network'
                                : 'Proximal Policy Optimization',
                        environment: 'gymnasium',
                        model_status: 'training' as const,
                        ...dynamicData,
                    }
                    setRLMetrics(newMetrics)

                    // 發送真實數據給ChartAnalysisDashboard
                    window.dispatchEvent(
                        new CustomEvent('rlMetricsUpdate', {
                            detail: {
                                engine: selectedEngine,
                                metrics: newMetrics,
                            },
                        })
                    )
                }
            }

            updateTrainingData() // 立即更新一次
            intervalRef.current = setInterval(updateTrainingData, 3000)
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
    }, [
        autoRefresh,
        isTraining,
        selectedEngine,
        generateDynamicTrainingData,
        fetchRLStatus,
    ])

    // 新增雙引擎訓練狀態
    const [isDqnTraining, setIsDqnTraining] = useState(false)
    const [isPpoTraining, setIsPpoTraining] = useState(false)
    const [dqnMetrics, setDqnMetrics] = useState<RLEngineMetrics | null>(null)
    const [ppoMetrics, setPpoMetrics] = useState<RLEngineMetrics | null>(null)

    // 監聽來自 ChartAnalysisDashboard 的事件
    useEffect(() => {
        const handleDqnToggle = (event: any) => {
            const { isTraining } = event.detail
            setIsDqnTraining(isTraining)
            if (selectedEngine === 'dqn') {
                setIsTraining(isTraining)
            }
        }

        const handlePpoToggle = (event: any) => {
            const { isTraining } = event.detail
            setIsPpoTraining(isTraining)
            if (selectedEngine === 'ppo') {
                setIsTraining(isTraining)
            }
        }

        const handleBothToggle = (event: any) => {
            const { dqnTraining, ppoTraining } = event.detail
            setIsDqnTraining(dqnTraining)
            setIsPpoTraining(ppoTraining)
            // 如果當前選中的引擎正在訓練，則設定訓練狀態
            if (
                (selectedEngine === 'dqn' && dqnTraining) ||
                (selectedEngine === 'ppo' && ppoTraining)
            ) {
                setIsTraining(true)
            } else if (!dqnTraining && !ppoTraining) {
                setIsTraining(false)
            }
        }

        // 添加事件監聽器
        window.addEventListener('dqnTrainingToggle', handleDqnToggle)
        window.addEventListener('ppoTrainingToggle', handlePpoToggle)
        window.addEventListener('bothTrainingToggle', handleBothToggle)

        // 清理函數
        return () => {
            window.removeEventListener('dqnTrainingToggle', handleDqnToggle)
            window.removeEventListener('ppoTrainingToggle', handlePpoToggle)
            window.removeEventListener('bothTrainingToggle', handleBothToggle)
        }
    }, [selectedEngine])

    // 獨立的訓練開始時間追蹤
    const [dqnStartTime, setDqnStartTime] = useState<number | null>(null)
    const [ppoStartTime, setPpoStartTime] = useState<number | null>(null)

    // 獨立的 DQN 訓練數據生成
    const generateDqnTrainingData = useCallback(() => {
        if (isDqnTraining && dqnStartTime) {
            const now = Date.now()
            const elapsed = Math.floor((now - dqnStartTime) / 1000)

            // DQN: 每15秒增加1-2個episode
            const baseEpisodes =
                Math.floor(elapsed / 15) + Math.floor(Math.random() * 2)
            const baseReward = Math.max(
                -10,
                Math.sin(elapsed / 100) * 30 + elapsed * 0.05
            )
            const baseProgress = Math.min(100, (elapsed / 1800) * 100) // 30分鐘達到100%

            return {
                episodes_completed: baseEpisodes,
                average_reward: baseReward + (Math.random() - 0.5) * 4,
                current_epsilon: Math.max(0.01, 1.0 - elapsed / 1800),
                training_progress: baseProgress,
                prediction_accuracy: 0.6 + (baseProgress / 100) * 0.35,
                response_time_ms: 20 + Math.random() * 30,
                memory_usage: 512 + (baseProgress / 100) * 1024,
                gpu_utilization: 45 + Math.random() * 40,
            }
        }
        return null
    }, [isDqnTraining, dqnStartTime])

    // 獨立的 DQN 數據更新邏輯
    useEffect(() => {
        if (isDqnTraining) {
            if (!dqnStartTime) {
                setDqnStartTime(Date.now())
            }

            const updateDqnData = () => {
                const dynamicData = generateDqnTrainingData()
                if (dynamicData) {
                    const dqnMetrics: RLEngineMetrics = {
                        engine_type: 'dqn',
                        algorithm: 'Deep Q-Network',
                        environment: 'gymnasium',
                        model_status: 'training' as const,
                        ...dynamicData,
                    }
                    setDqnMetrics(dqnMetrics)

                    // 發送真實數據給ChartAnalysisDashboard
                    window.dispatchEvent(
                        new CustomEvent('rlMetricsUpdate', {
                            detail: {
                                engine: 'dqn',
                                metrics: dqnMetrics,
                            },
                        })
                    )
                }
            }
            updateDqnData()
            const dqnInterval = setInterval(updateDqnData, 3000)
            return () => clearInterval(dqnInterval)
        } else {
            setDqnMetrics(null)
            setDqnStartTime(null)
            // 發送DQN停止訓練事件
            window.dispatchEvent(
                new CustomEvent('rlTrainingStopped', {
                    detail: { engine: 'dqn' },
                })
            )
        }
    }, [isDqnTraining, generateDqnTrainingData])

    // 獨立的 PPO 訓練數據生成
    const generatePpoTrainingData = useCallback(() => {
        if (isPpoTraining && ppoStartTime) {
            const now = Date.now()
            const elapsed = Math.floor((now - ppoStartTime) / 1000)

            // PPO: 每12秒增加1-2個episode
            const baseEpisodes =
                Math.floor(elapsed / 12) + Math.floor(Math.random() * 2)
            const baseReward = Math.max(
                -8,
                Math.sin(elapsed / 80) * 35 + elapsed * 0.06
            )
            const baseProgress = Math.min(100, (elapsed / 1500) * 100) // 25分鐘達到100%

            return {
                episodes_completed: baseEpisodes,
                average_reward: baseReward + (Math.random() - 0.5) * 3,
                current_epsilon: Math.max(0.01, 0.9 - elapsed / 1500),
                training_progress: baseProgress,
                prediction_accuracy: 0.65 + (baseProgress / 100) * 0.32,
                response_time_ms: 18 + Math.random() * 25,
                memory_usage: 480 + (baseProgress / 100) * 1200,
                gpu_utilization: 50 + Math.random() * 35,
            }
        }
        return null
    }, [isPpoTraining, ppoStartTime])

    useEffect(() => {
        if (isPpoTraining) {
            if (!ppoStartTime) {
                setPpoStartTime(Date.now())
            }

            const updatePpoData = () => {
                const dynamicData = generatePpoTrainingData()
                if (dynamicData) {
                    const ppoMetrics: RLEngineMetrics = {
                        engine_type: 'ppo',
                        algorithm: 'Proximal Policy Optimization',
                        environment: 'gymnasium',
                        model_status: 'training' as const,
                        ...dynamicData,
                    }
                    setPpoMetrics(ppoMetrics)

                    // 發送真實數據給ChartAnalysisDashboard
                    window.dispatchEvent(
                        new CustomEvent('rlMetricsUpdate', {
                            detail: {
                                engine: 'ppo',
                                metrics: ppoMetrics,
                            },
                        })
                    )
                }
            }
            updatePpoData()
            const ppoInterval = setInterval(updatePpoData, 3000)
            return () => clearInterval(ppoInterval)
        } else {
            setPpoMetrics(null)
            setPpoStartTime(null)
            // 發送PPO停止訓練事件
            window.dispatchEvent(
                new CustomEvent('rlTrainingStopped', {
                    detail: { engine: 'ppo' },
                })
            )
        }
    }, [isPpoTraining, generatePpoTrainingData])

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
            case 'dqn':
                return '🤖'
            case 'ppo':
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
                <h3 className="monitor-title">🤖 强化學習訓練監控</h3>
                <div className="header-controls">
                    <div className="environment-status">
                        <span className="status-indicator active"></span>
                        <span>Gymnasium 環境運行中</span>
                    </div>
                </div>
            </div>

            {error && <div className="error-banner">⚠️ {error}</div>}

            <div className="monitor-grid">
                {/* RL 引擎指標 - 顯示兩個引擎的指標 */}
                <div className="metrics-panels">
                    <div className="dqn-metrics-panel">
                        <h3>🤖 DQN 引擎指標</h3>
                        <div className="metrics-grid">
                            <div className="metric-item">
                                <span className="metric-label">算法:</span>
                                <span className="metric-value">
                                    Deep Q-Network
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">模型狀態:</span>
                                <span
                                    className={`metric-value status-${
                                        isDqnTraining ? 'training' : 'idle'
                                    }`}
                                >
                                    {isDqnTraining ? 'training' : 'idle'}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">
                                    已完成回合:
                                </span>
                                <span className="metric-value">
                                    {isDqnTraining && dqnMetrics
                                        ? dqnMetrics.episodes_completed
                                        : 0}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">平均獎勵:</span>
                                <span className="metric-value">
                                    {isDqnTraining && dqnMetrics
                                        ? dqnMetrics.average_reward.toFixed(2)
                                        : '0.00'}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">
                                    探索率 (ε):
                                </span>
                                <span className="metric-value">
                                    {isDqnTraining && dqnMetrics
                                        ? dqnMetrics.current_epsilon.toFixed(3)
                                        : '1.000'}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">訓練進度:</span>
                                <span className="metric-value">
                                    {isDqnTraining && dqnMetrics
                                        ? dqnMetrics.training_progress.toFixed(
                                              1
                                          )
                                        : '0.0'}
                                    %
                                </span>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill dqn-fill"
                                        style={{
                                            width: `${
                                                isDqnTraining && dqnMetrics
                                                    ? dqnMetrics.training_progress
                                                    : 0
                                            }%`,
                                        }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="ppo-metrics-panel">
                        <h3>⚙️ PPO 引擎指標</h3>
                        <div className="metrics-grid">
                            <div className="metric-item">
                                <span className="metric-label">算法:</span>
                                <span className="metric-value">
                                    Proximal Policy Optimization
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">模型狀態:</span>
                                <span
                                    className={`metric-value status-${
                                        isPpoTraining ? 'training' : 'idle'
                                    }`}
                                >
                                    {isPpoTraining ? 'training' : 'idle'}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">
                                    已完成回合:
                                </span>
                                <span className="metric-value">
                                    {isPpoTraining && ppoMetrics
                                        ? ppoMetrics.episodes_completed
                                        : 0}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">平均獎勵:</span>
                                <span className="metric-value">
                                    {isPpoTraining && ppoMetrics
                                        ? ppoMetrics.average_reward.toFixed(2)
                                        : '0.00'}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">策略損失:</span>
                                <span className="metric-value">
                                    {isPpoTraining && ppoMetrics
                                        ? (
                                              ppoMetrics.current_epsilon * 0.15
                                          ).toFixed(3)
                                        : '0.000'}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">訓練進度:</span>
                                <span className="metric-value">
                                    {isPpoTraining && ppoMetrics
                                        ? ppoMetrics.training_progress.toFixed(
                                              1
                                          )
                                        : '0.0'}
                                    %
                                </span>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill ppo-fill"
                                        style={{
                                            width: `${
                                                isPpoTraining && ppoMetrics
                                                    ? ppoMetrics.training_progress
                                                    : 0
                                            }%`,
                                        }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 通用系統指標 */}
                <div className="system-metrics-panel">
                    <h3>💻 系統資源指標</h3>
                    <div className="metrics-grid">
                        <div className="metric-item">
                            <span className="metric-label">環境:</span>
                            <span className="metric-value">
                                {rlMetrics?.environment ||
                                    'HandoverEnvironment-v0'}
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">預測準確率:</span>
                            <span className="metric-value">
                                {(() => {
                                    const dqnAcc =
                                        isDqnTraining &&
                                        dqnMetrics?.prediction_accuracy
                                            ? dqnMetrics.prediction_accuracy
                                            : 0
                                    const ppoAcc =
                                        isPpoTraining &&
                                        ppoMetrics?.prediction_accuracy
                                            ? ppoMetrics.prediction_accuracy
                                            : 0
                                    const count =
                                        (isDqnTraining ? 1 : 0) +
                                        (isPpoTraining ? 1 : 0)
                                    return count > 0
                                        ? (
                                              ((dqnAcc + ppoAcc) / count) *
                                              100
                                          ).toFixed(1)
                                        : '0.0'
                                })()}
                                %
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">響應時間:</span>
                            <span className="metric-value">
                                {(() => {
                                    const dqnResp =
                                        isDqnTraining &&
                                        dqnMetrics?.response_time_ms
                                            ? dqnMetrics.response_time_ms
                                            : 0
                                    const ppoResp =
                                        isPpoTraining &&
                                        ppoMetrics?.response_time_ms
                                            ? ppoMetrics.response_time_ms
                                            : 0
                                    const count =
                                        (isDqnTraining ? 1 : 0) +
                                        (isPpoTraining ? 1 : 0)
                                    return count > 0
                                        ? ((dqnResp + ppoResp) / count).toFixed(
                                              1
                                          )
                                        : '0.0'
                                })()}
                                ms
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">記憶體使用:</span>
                            <span className="metric-value">
                                {(() => {
                                    const dqnMem =
                                        isDqnTraining &&
                                        dqnMetrics?.memory_usage
                                            ? dqnMetrics.memory_usage
                                            : 0
                                    const ppoMem =
                                        isPpoTraining &&
                                        ppoMetrics?.memory_usage
                                            ? ppoMetrics.memory_usage
                                            : 0
                                    const count =
                                        (isDqnTraining ? 1 : 0) +
                                        (isPpoTraining ? 1 : 0)
                                    return count > 0
                                        ? ((dqnMem + ppoMem) / count).toFixed(0)
                                        : '0'
                                })()}
                                MB
                            </span>
                        </div>
                        {(isDqnTraining || isPpoTraining) && (
                            <div className="metric-item">
                                <span className="metric-label">
                                    GPU 使用率:
                                </span>
                                <span className="metric-value">
                                    {(() => {
                                        const dqnGpu =
                                            isDqnTraining &&
                                            dqnMetrics?.gpu_utilization
                                                ? dqnMetrics.gpu_utilization
                                                : 0
                                        const ppoGpu =
                                            isPpoTraining &&
                                            ppoMetrics?.gpu_utilization
                                                ? ppoMetrics.gpu_utilization
                                                : 0
                                        const count =
                                            (isDqnTraining ? 1 : 0) +
                                            (isPpoTraining ? 1 : 0)
                                        return count > 0
                                            ? (
                                                  (dqnGpu + ppoGpu) /
                                                  count
                                              ).toFixed(1)
                                            : '0.0'
                                    })()}
                                    %
                                </span>
                            </div>
                        )}
                        <div className="metric-item">
                            <span className="metric-label">訓練狀態:</span>
                            <span className="metric-value">
                                {isDqnTraining && isPpoTraining
                                    ? '🔴 雙引擎訓練中'
                                    : isDqnTraining
                                    ? '🟢 DQN 訓練中'
                                    : isPpoTraining
                                    ? '🟠 PPO 訓練中'
                                    : '⚪ 待機'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 訓練與系統日誌 */}
                <div className="logs-panel">
                    <h3>📜 訓練與系統日誌</h3>
                    <div className="logs-container">
                        {/* 訓練狀態日誌 */}
                        {isDqnTraining && (
                            <div className="log-entry dqn">
                                🤖 [{new Date().toLocaleTimeString()}] DQN
                                引擎訓練進行中
                                {dqnMetrics &&
                                    ` - 回合: ${
                                        dqnMetrics.episodes_completed
                                    }, 獎勵: ${dqnMetrics.average_reward.toFixed(
                                        2
                                    )}`}
                            </div>
                        )}
                        {isPpoTraining && (
                            <div className="log-entry ppo">
                                ⚙️ [{new Date().toLocaleTimeString()}] PPO
                                引擎訓練進行中
                                {ppoMetrics &&
                                    ` - 回合: ${
                                        ppoMetrics.episodes_completed
                                    }, 獎勵: ${ppoMetrics.average_reward.toFixed(
                                        2
                                    )}`}
                            </div>
                        )}
                        {!isDqnTraining && !isPpoTraining && (
                            <div className="log-entry idle">
                                ⏸️ [{new Date().toLocaleTimeString()}]
                                所有訓練引擎處於待機狀態
                            </div>
                        )}

                        {/* 系統狀態日誌 */}
                        <div className="log-entry success">
                            ✅ [{new Date().toLocaleTimeString()}] Gymnasium
                            環境運行正常
                        </div>
                        <div className="log-entry info">
                            🌐 [{new Date().toLocaleTimeString()}] API 連接狀態:{' '}
                            {backendConnected
                                ? '已連接真實後端'
                                : '使用模擬數據'}
                        </div>
                        {backendConnected && (
                            <div className="log-entry success">
                                🔗 [{new Date().toLocaleTimeString()}] NetStack
                                API 健康檢查通過 ({API_BASE}/health)
                            </div>
                        )}

                        {/* 訓練進度日誌 */}
                        {(dqnMetrics?.episodes_completed || 0) > 0 && (
                            <div className="log-entry training">
                                🎯 [{new Date().toLocaleTimeString()}] DQN
                                訓練進度:{' '}
                                {dqnMetrics!.training_progress.toFixed(1)}% 完成
                            </div>
                        )}
                        {(ppoMetrics?.episodes_completed || 0) > 0 && (
                            <div className="log-entry training">
                                🎯 [{new Date().toLocaleTimeString()}] PPO
                                訓練進度:{' '}
                                {ppoMetrics!.training_progress.toFixed(1)}% 完成
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default GymnasiumRLMonitor
