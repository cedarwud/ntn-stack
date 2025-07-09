import React, { useState, useEffect, useCallback, useRef } from 'react'
import './GymnasiumRLMonitor.scss'
import { apiClient } from '../../services/api-client' // 導入統一的 API 客戶端
import { RLEngineMetrics } from '../../types/rl_types'

// Note: Removed unused interfaces EnvironmentState and DecisionHistory
// They can be re-added when needed for future features

// 定義真實API端點的基礎URL - 通過Vite代理訪問
const API_BASE = '/netstack'

/**
 * 將後端返回的數據適配到前端的 RLEngineMetrics 介面
 * @param data 從 API 獲取的原始數據
 * @returns 適配後的 RLEngineMetrics 對象
 */
const transformDataToMetrics = (data: any): RLEngineMetrics => {
    return {
        engine_type: data.active_algorithm || 'null',
        algorithm: data.algorithm_details?.name || 'Unknown',
        environment: data.environment?.name || 'Unknown',
        model_status: data.status || 'idle',
        episodes_completed: data.training_stats?.episodes_completed || 0,
        average_reward: data.training_stats?.average_reward || 0,
        current_epsilon: data.training_stats?.current_epsilon || 0,
        training_progress: data.training_stats?.progress || 0,
        prediction_accuracy: data.performance_metrics?.prediction_accuracy || 0,
        response_time_ms: data.performance_metrics?.avg_response_time_ms || 0,
        memory_usage: data.system_resources?.memory_usage_mb || 0,
        gpu_utilization: data.system_resources?.gpu_utilization_percent || 0,
    }
}

/**
 * 將訓練會話數據轉換為前端所需的格式
 * @param sessions 訓練會話數據
 * @param decisionStatus 決策引擎狀態
 * @returns 適配後的 RLEngineMetrics 對象
 */
const transformTrainingSessionsToMetrics = (sessions: any[], decisionStatus: any): RLEngineMetrics => {
    // 找到最近的活躍訓練會話
    const activeSession = sessions.find(s => s.status === 'active') || sessions[0]
    
    if (!activeSession) {
        // 沒有訓練會話，使用預設值
        return {
            engine_type: 'null',
            algorithm: 'No active training',
            environment: 'Unknown',
            model_status: 'idle',
            episodes_completed: 0,
            average_reward: 0,
            current_epsilon: 0,
            training_progress: 0,
            prediction_accuracy: 0,
            response_time_ms: 0,
            memory_usage: 0,
            gpu_utilization: 0,
        }
    }

    // 計算訓練進度
    const progress = (activeSession.episodes_completed / activeSession.episodes_target) * 100

    return {
        engine_type: activeSession.algorithm_name as 'dqn' | 'ppo' | 'sac' | 'null',
        algorithm: `${activeSession.algorithm_name.toUpperCase()} Training`,
        environment: 'HandoverEnvironment-v0',
        model_status: activeSession.status === 'active' ? 'training' : 
                     activeSession.status === 'completed' ? 'inference' : 'idle',
        episodes_completed: activeSession.episodes_completed,
        average_reward: activeSession.current_reward,
        current_epsilon: Math.max(0.1, 1.0 - progress / 100), // 模擬epsilon衰減
        training_progress: progress,
        prediction_accuracy: decisionStatus.performance_metrics?.prediction_accuracy || 0.85,
        response_time_ms: decisionStatus.performance_metrics?.avg_response_time_ms || 25,
        memory_usage: decisionStatus.system_resources?.memory_usage_mb || 1024,
        gpu_utilization: decisionStatus.system_resources?.gpu_utilization_percent || 0,
    }
}

const GymnasiumRLMonitor: React.FC = () => {
    const [rlMetrics, setRLMetrics] = useState<RLEngineMetrics | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [selectedEngine, setSelectedEngine] = useState<'dqn' | 'ppo' | 'sac'>(
        'dqn'
    )
    const [isTraining, setIsTraining] = useState(false)
    const [autoRefresh] = useState(true)
    const [isLoading, setLoading] = useState(false)
    const [backendConnected, setBackendConnected] = useState(false)
    const [connectionError, setConnectionError] = useState<string | null>(null)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)

    // 獲取 RL 系統狀態 - 使用真實的訓練會話數據
    const fetchRLStatus = useCallback(async () => {
        if (!backendConnected) {
            return
        }
        setLoading(true)
        setError(null)

        try {
            // 獲取真實的訓練會話狀態
            const trainingSessions = await apiClient.getRLTrainingSessions()
            
            // 獲取基本的決策引擎狀態
            const decisionStatus = await apiClient.getAIDecisionEngineStatus()
            
            // 合併數據並轉換為前端需要的格式
            const metrics = transformTrainingSessionsToMetrics(trainingSessions, decisionStatus)

            setRLMetrics(metrics)

            // 為每個算法發送事件到 useRLMonitoring hook 以更新圖表數據
            trainingSessions.forEach(session => {
                if (session.status === 'active') {
                    const progress = (session.episodes_completed / session.episodes_target) * 100
                    const sessionMetrics = {
                        engine_type: session.algorithm_name,
                        algorithm: `${session.algorithm_name.toUpperCase()} Training`,
                        environment: 'HandoverEnvironment-v0',
                        model_status: 'training',
                        episodes_completed: session.episodes_completed,
                        average_reward: session.current_reward,
                        current_epsilon: Math.max(0.1, 1.0 - progress / 100),
                        training_progress: progress,
                        prediction_accuracy: decisionStatus.performance_metrics?.prediction_accuracy || 0.85,
                        response_time_ms: decisionStatus.performance_metrics?.avg_response_time_ms || 25,
                        memory_usage: decisionStatus.system_resources?.memory_usage_mb || 1024,
                        gpu_utilization: decisionStatus.system_resources?.gpu_utilization_percent || 0,
                    }
                    
                    window.dispatchEvent(
                        new CustomEvent('rlMetricsUpdate', {
                            detail: {
                                engine: session.algorithm_name,
                                metrics: sessionMetrics,
                            },
                        })
                    )
                }
            })
        } catch (error) {
            console.error('Failed to fetch RL status:', error)
            // 後端無法連接，顯示錯誤訊息
            setError(
                `無法獲取 RL 狀態: ${
                    error instanceof Error ? error.message : '未知錯誤'
                }`
            )
            setRLMetrics(null)
        } finally {
            setLoading(false)
        }
    }, [backendConnected]) // 移除 isTraining 依賴

    // 檢查後端連接狀態 - 使用統一的 API Client
    const checkBackendConnection = useCallback(async () => {
        try {
            const data = await apiClient.getAIDecisionEngineHealth()
            // 修正健康檢查邏輯，適配新的後端響應格式
            const isHealthy = data.overall_health === true
            setBackendConnected(isHealthy)
            if (!isHealthy) {
                throw new Error('AI Decision Engine is not healthy')
            }
            setConnectionError(null)
            console.log('後端連接成功，將使用真實 API 數據')
            return true
        } catch (error) {
            setBackendConnected(false)
            setConnectionError(
                error instanceof Error ? error.message : '連接失敗'
            )
            console.warn('後端連接失敗，將使用模擬數據:', error)
            return false
        }
    }, [])

    // 同步前端按鈕狀態與後端訓練狀態
    const syncFrontendState = useCallback(async () => {
        if (!backendConnected) {
            return
        }

        try {
            // 獲取訓練狀態摘要
            const statusSummary = await apiClient.getTrainingStatusSummary()
            
            console.log('🔄 獲取到狀態摘要:', statusSummary)

            // 發送狀態同步事件到 useRLMonitoring hook
            ['dqn', 'ppo', 'sac'].forEach(algorithm => {
                const isActive = statusSummary.active_algorithms.includes(algorithm)
                
                console.log(`🔄 同步 ${algorithm} 狀態: ${isActive ? '訓練中' : '停止'}`)
                
                window.dispatchEvent(
                    new CustomEvent('trainingStateSync', {
                        detail: {
                            engine: algorithm,
                            isTraining: isActive,
                        },
                    })
                )
            })

            console.log(`🔄 狀態同步完成 - 活躍算法: [${statusSummary.active_algorithms.join(', ')}]`)
            
        } catch (error) {
            console.warn('狀態同步失敗:', error)
        }
    }, [backendConnected])

    // 初始化時檢查連接並同步狀態
    useEffect(() => {
        const initializeConnection = async () => {
            console.log('🔄 開始初始化連接和狀態同步')
            const connected = await checkBackendConnection()
            if (connected) {
                console.log('🔄 後端連接成功，開始狀態同步')
                // 連接成功後，立即同步狀態
                setTimeout(() => {
                    syncFrontendState()
                }, 100)
                // 每5秒重新同步一次狀態，確保前端狀態與後端一致
                const syncInterval = setInterval(() => {
                    syncFrontendState()
                }, 5000)
                
                // 清理定時器
                return () => {
                    clearInterval(syncInterval)
                }
            }
        }
        initializeConnection()
    }, [checkBackendConnection, syncFrontendState])

    // 自動刷新和動態數據更新
    useEffect(() => {
        if (autoRefresh && backendConnected) {
            // 後端連接成功後才啟動定時刷新，更頻繁地獲取真實數據
            intervalRef.current = setInterval(fetchRLStatus, 2000) // 縮短至2秒
            fetchRLStatus() // 立即獲取一次
        }

        // 清理函數
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [autoRefresh, backendConnected, fetchRLStatus])

    // 事件監聽器，用於接收來自儀表板其他組件的訓練控制信號
    useEffect(() => {
        const handleDqnToggle = (
            event: CustomEvent<{ isTraining: boolean }>
        ) => {
            const isTraining = event.detail.isTraining
            console.log('收到 DQN 切換事件:', { isTraining })
            setIsTraining(isTraining)
            setSelectedEngine('dqn')

            // 發送訓練狀態變更事件到 useRLMonitoring hook
            window.dispatchEvent(
                new CustomEvent('trainingStateUpdate', {
                    detail: {
                        engine: 'dqn',
                        isTraining: isTraining,
                    },
                })
            )

            console.log(
                `Sending training command: ${
                    isTraining ? 'start' : 'stop'
                } for dqn`
            )
            
            if (isTraining) {
                // 啟動訓練
                apiClient
                    .controlTraining('start', 'dqn')
                    .then((response) => {
                        console.log('DQN Training start successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to start DQN training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
            } else {
                // 停止訓練 - 先獲取會話然後停止
                apiClient.getRLTrainingSessions()
                    .then((sessions) => {
                        const dqnSession = sessions.find(s => s.algorithm_name === 'dqn' && s.status === 'active')
                        if (dqnSession) {
                            return apiClient.stopTrainingSession(dqnSession.session_id)
                        } else {
                            console.warn('沒有找到活躍的 DQN 訓練會話')
                            return Promise.resolve()
                        }
                    })
                    .then((response) => {
                        console.log('DQN Training stop successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to stop DQN training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
            }
        }

        const handlePpoToggle = (event: CustomEvent) => {
            const isTraining = (event.detail as { isTraining: boolean })
                .isTraining
            console.log('收到 PPO 切換事件:', { isTraining })
            setIsTraining(isTraining)
            setSelectedEngine('ppo')

            // 發送訓練狀態變更事件到 useRLMonitoring hook
            window.dispatchEvent(
                new CustomEvent('trainingStateUpdate', {
                    detail: {
                        engine: 'ppo',
                        isTraining: isTraining,
                    },
                })
            )

            console.log(
                `Sending training command: ${
                    isTraining ? 'start' : 'stop'
                } for ppo`
            )
            
            if (isTraining) {
                // 啟動訓練
                apiClient
                    .controlTraining('start', 'ppo')
                    .then((response) => {
                        console.log('PPO Training start successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to start PPO training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
            } else {
                // 停止訓練 - 先獲取會話然後停止
                apiClient.getRLTrainingSessions()
                    .then((sessions) => {
                        const ppoSession = sessions.find(s => s.algorithm_name === 'ppo' && s.status === 'active')
                        if (ppoSession) {
                            return apiClient.stopTrainingSession(ppoSession.session_id)
                        } else {
                            console.warn('沒有找到活躍的 PPO 訓練會話')
                            return Promise.resolve()
                        }
                    })
                    .then((response) => {
                        console.log('PPO Training stop successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to stop PPO training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
            }
        }
        const handleSacToggle = (event: CustomEvent) => {
            const isTraining = (event.detail as { isTraining: boolean })
                .isTraining
            console.log('收到 SAC 切換事件:', { isTraining })
            setIsTraining(isTraining)
            setSelectedEngine('sac')

            // 發送訓練狀態變更事件到 useRLMonitoring hook
            window.dispatchEvent(
                new CustomEvent('trainingStateUpdate', {
                    detail: {
                        engine: 'sac',
                        isTraining: isTraining,
                    },
                })
            )

            console.log(
                `Sending training command: ${
                    isTraining ? 'start' : 'stop'
                } for sac`
            )
            
            if (isTraining) {
                // 啟動訓練
                apiClient
                    .controlTraining('start', 'sac')
                    .then((response) => {
                        console.log('SAC Training start successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to start SAC training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
            } else {
                // 停止訓練 - 先獲取會話然後停止
                apiClient.getRLTrainingSessions()
                    .then((sessions) => {
                        const sacSession = sessions.find(s => s.algorithm_name === 'sac' && s.status === 'active')
                        if (sacSession) {
                            return apiClient.stopTrainingSession(sacSession.session_id)
                        } else {
                            console.warn('沒有找到活躍的 SAC 訓練會話')
                            return Promise.resolve()
                        }
                    })
                    .then((response) => {
                        console.log('SAC Training stop successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to stop SAC training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatus()
                                syncFrontendState()
                            }
                        }, 100)
                    })
            }
        }

        const handleAllToggle = (event: CustomEvent) => {
            const isTraining = (event.detail as { isTraining: boolean })
                .isTraining
            console.log('收到 ALL 切換事件:', { isTraining })
            setIsTraining(isTraining)

            // 發送訓練狀態變更事件到 useRLMonitoring hook（所有引擎）
            const allEngines = ['dqn', 'ppo', 'sac'] as const
            allEngines.forEach((engine) => {
                window.dispatchEvent(
                    new CustomEvent('trainingStateUpdate', {
                        detail: {
                            engine: engine,
                            isTraining: isTraining,
                        },
                    })
                )
            })

            if (isTraining) {
                // 啟動所有引擎訓練
                const engines = ['dqn', 'ppo', 'sac'] as const
                engines.forEach((engine) => {
                    console.log(`啟動 ${engine.toUpperCase()} 訓練`)
                    apiClient
                        .controlTraining('start', engine)
                        .then((response) => {
                            console.log(`${engine.toUpperCase()} training start successful:`, response)
                        })
                        .catch((error) => {
                            console.error(`Failed to start ${engine.toUpperCase()} training:`, error)
                        })
                })
            } else {
                // 停止所有引擎訓練 - 使用 stopAllTraining API
                console.log('停止所有引擎訓練')
                apiClient
                    .stopAllTraining()
                    .then((response) => {
                        console.log('Stop all training successful:', response)
                    })
                    .catch((error) => {
                        console.error('Failed to stop all training:', error)
                    })
            }

            // 立即獲取真實的 API 數據
            setTimeout(() => {
                if (backendConnected) {
                    fetchRLStatus()
                    syncFrontendState()
                }
            }, 100)
        }

        console.log('註冊事件監聽器')
        window.addEventListener('dqnToggle', handleDqnToggle as EventListener)
        window.addEventListener('ppoToggle', handlePpoToggle as EventListener)
        window.addEventListener('sacToggle', handleSacToggle as EventListener)
        window.addEventListener('allToggle', handleAllToggle as EventListener)

        return () => {
            console.log('移除事件監聽器')
            window.removeEventListener(
                'dqnToggle',
                handleDqnToggle as EventListener
            )
            window.removeEventListener(
                'ppoToggle',
                handlePpoToggle as EventListener
            )
            window.removeEventListener(
                'sacToggle',
                handleSacToggle as EventListener
            )
            window.removeEventListener(
                'allToggle',
                handleAllToggle as EventListener
            )
        }
    }, [fetchRLStatus]) // 保留依賴，但將通過 useCallback 穩定化

    return (
        <div className="gymnasium-rl-monitor">
            <div className="monitor-header">
                <h3>Gymnasium RL Monitor</h3>
                <div
                    className={`status-indicator ${
                        backendConnected ? 'connected' : 'disconnected'
                    }`}
                    title={
                        backendConnected
                            ? '已連接到後端'
                            : `連接失敗: ${connectionError || error || 'N/A'}`
                    }
                ></div>
                {/* 連接狀態指示器 */}
            </div>
            {error && <div className="error-message">{error}</div>}
            {!backendConnected && !error && (
                <div className="loading-message">正在連接到後端服務...</div>
            )}
            {backendConnected && isLoading && !rlMetrics && (
                <div className="loading-message">正在加載RL引擎數據...</div>
            )}
            {backendConnected && rlMetrics && (
                <div className="monitor-content">
                    <div className="metrics-grid">
                        <div className="metric-item">
                            <span className="metric-label">引擎</span>
                            <span className="metric-value">
                                {rlMetrics.algorithm}
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">狀態</span>
                            <span
                                className={`metric-value status-${rlMetrics.model_status}`}
                            >
                                {rlMetrics.model_status}
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">平均獎勵</span>
                            <span className="metric-value">
                                {rlMetrics.average_reward.toFixed(2)}
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">準確率</span>
                            <span className="metric-value">
                                {(rlMetrics.prediction_accuracy * 100).toFixed(
                                    1
                                )}
                                %
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">響應時間</span>
                            <span className="metric-value">
                                {rlMetrics.response_time_ms.toFixed(0)} ms
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">記憶體</span>
                            <span className="metric-value">
                                {rlMetrics.memory_usage.toFixed(0)} MB
                            </span>
                        </div>
                    </div>
                    <div className="progress-bar-container">
                        <div className="progress-bar-label">
                            <span>
                                訓練進度 ({rlMetrics.episodes_completed}{' '}
                                episodes)
                            </span>
                            <span>
                                {rlMetrics.training_progress.toFixed(1)}%
                            </span>
                        </div>
                        <div className="progress-bar">
                            <div
                                className="progress-bar-fill"
                                style={{
                                    width: `${rlMetrics.training_progress}%`,
                                }}
                            ></div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default GymnasiumRLMonitor
