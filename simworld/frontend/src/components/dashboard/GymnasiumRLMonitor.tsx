import React, { useState, useEffect, useCallback, useRef } from 'react'
import './GymnasiumRLMonitor.scss'
import { apiClient } from '../../services/api-client' // 導入統一的 API 客戶端
import { RLEngineMetrics } from '../../types/rl_types'

// Note: Removed unused interfaces EnvironmentState and DecisionHistory
// They can be re-added when needed for future features

/**
 * 將後端返回的數據適配到前端的 RLEngineMetrics 介面
 * @param data 從 API 獲取的原始數據
 * @returns 適配後的 RLEngineMetrics 對象
 */
const _transformDataToMetrics = (data: unknown): RLEngineMetrics => {
    const dataObj = data as Record<string, unknown>
    return {
        engine_type: (dataObj.active_algorithm as string) || 'null',
        algorithm: ((dataObj.algorithm_details as Record<string, unknown>)?.name as string) || 'Unknown',
        environment: ((dataObj.environment as Record<string, unknown>)?.name as string) || 'Unknown',
        model_status: (dataObj.status as string) || 'idle',
        episodes_completed: ((dataObj.training_stats as Record<string, unknown>)?.episodes_completed as number) || 0,
        average_reward: ((dataObj.training_stats as Record<string, unknown>)?.average_reward as number) || 0,
        current_epsilon: ((dataObj.training_stats as Record<string, unknown>)?.current_epsilon as number) || 0,
        training_progress: ((dataObj.training_stats as Record<string, unknown>)?.progress as number) || 0,
        prediction_accuracy: ((dataObj.performance_metrics as Record<string, unknown>)?.prediction_accuracy as number) || 0,
        response_time_ms: ((dataObj.performance_metrics as Record<string, unknown>)?.avg_response_time_ms as number) || 0,
        memory_usage: ((dataObj.system_resources as Record<string, unknown>)?.memory_usage_mb as number) || 0,
        gpu_utilization: ((dataObj.system_resources as Record<string, unknown>)?.gpu_utilization_percent as number) || 0,
    }
}

/**
 * 將訓練會話數據轉換為前端所需的格式
 * @param sessions 訓練會話數據
 * @param decisionStatus 決策引擎狀態
 * @returns 適配後的 RLEngineMetrics 對象
 */
const transformTrainingSessionsToMetrics = (sessions: unknown[], decisionStatus: unknown): RLEngineMetrics => {
    // 找到最近的活躍訓練會話
    const sessionArray = sessions as Array<Record<string, unknown>>
    const activeSession = sessionArray.find(s => s.status === 'active') || sessionArray[0]
    
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
    const progress = ((activeSession.episodes_completed as number) / (activeSession.episodes_target as number)) * 100
    const decisionStatusObj = decisionStatus as Record<string, unknown>

    return {
        engine_type: activeSession.algorithm_name as 'dqn' | 'ppo' | 'sac' | 'null',
        algorithm: `${(activeSession.algorithm_name as string).toUpperCase()} Training`,
        environment: 'HandoverEnvironment-v0',
        model_status: activeSession.status === 'active' ? 'training' : 
                     activeSession.status === 'completed' ? 'inference' : 'idle',
        episodes_completed: activeSession.episodes_completed as number,
        average_reward: activeSession.current_reward as number,
        current_epsilon: Math.max(0.1, 1.0 - progress / 100), // 模擬epsilon衰減
        training_progress: progress,
        prediction_accuracy: ((decisionStatusObj.performance_metrics as Record<string, unknown>)?.prediction_accuracy as number) || 0.85,
        response_time_ms: ((decisionStatusObj.performance_metrics as Record<string, unknown>)?.avg_response_time_ms as number) || 25,
        memory_usage: ((decisionStatusObj.system_resources as Record<string, unknown>)?.memory_usage_mb as number) || 1024,
        gpu_utilization: ((decisionStatusObj.system_resources as Record<string, unknown>)?.gpu_utilization_percent as number) || 0,
    }
}

const GymnasiumRLMonitor: React.FC = () => {
    const [rlMetrics, setRLMetrics] = useState<RLEngineMetrics | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [allEngineMetrics, setAllEngineMetrics] = useState<{
        dqn: RLEngineMetrics | null,
        ppo: RLEngineMetrics | null,
        sac: RLEngineMetrics | null
    }>({
        dqn: null,
        ppo: null,
        sac: null
    })
    const [_isTraining, _setIsTraining] = useState(false)
    const [autoRefresh] = useState(true)
    const [isLoading, setLoading] = useState(false)
    const [backendConnected, setBackendConnected] = useState(false)
    const [connectionError, setConnectionError] = useState<string | null>(null)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)
    const fetchRLStatusRef = useRef<() => Promise<void>>(null)
    const syncFrontendStateRef = useRef<() => Promise<void>>(null)
    const lastSyncStateRef = useRef<string>('')  // 跟蹤上次同步的狀態


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

            // 為每個算法更新指標並發送事件到 useRLMonitoring hook
            setAllEngineMetrics(prevMetrics => {
                const newAllEngineMetrics = { ...prevMetrics }
                
                const sessionArray = trainingSessions as Array<Record<string, unknown>>
                sessionArray.forEach(session => {
                    const progress = ((session.episodes_completed as number) / (session.episodes_target as number)) * 100
                    const sessionMetrics = {
                        engine_type: session.algorithm_name,
                        algorithm: `${(session.algorithm_name as string).toUpperCase()} Training`,
                        environment: 'HandoverEnvironment-v0',
                        model_status: session.status === 'active' ? 'training' : 
                                     session.status === 'completed' ? 'inference' : 'idle',
                        episodes_completed: session.episodes_completed as number,
                        average_reward: session.current_reward as number,
                        current_epsilon: Math.max(0.1, 1.0 - progress / 100),
                        training_progress: progress,
                        prediction_accuracy: ((decisionStatus as Record<string, unknown>).performance_metrics as Record<string, unknown>)?.prediction_accuracy as number || 0.85,
                        response_time_ms: ((decisionStatus as Record<string, unknown>).performance_metrics as Record<string, unknown>)?.avg_response_time_ms as number || 25,
                        memory_usage: ((decisionStatus as Record<string, unknown>).system_resources as Record<string, unknown>)?.memory_usage_mb as number || 1024,
                        gpu_utilization: ((decisionStatus as Record<string, unknown>).system_resources as Record<string, unknown>)?.gpu_utilization_percent as number || 0,
                    }
                    
                    // 更新對應算法的指標
                    if (session.algorithm_name === 'dqn') {
                        newAllEngineMetrics.dqn = sessionMetrics
                    } else if (session.algorithm_name === 'ppo') {
                        newAllEngineMetrics.ppo = sessionMetrics
                    } else if (session.algorithm_name === 'sac') {
                        newAllEngineMetrics.sac = sessionMetrics
                    }
                    
                    // 發送事件到 useRLMonitoring hook - 延遲執行避免渲染衝突
                    if (session.status === 'active') {
                        setTimeout(() => {
                            window.dispatchEvent(
                                new CustomEvent('rlMetricsUpdate', {
                                    detail: {
                                        engine: session.algorithm_name,
                                        metrics: sessionMetrics,
                                    },
                                })
                            )
                        }, 0)
                    }
                })
                
                return newAllEngineMetrics
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
    }, [backendConnected]) // 移除 allEngineMetrics 依賴避免無限循環

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
            
            // 檢查狀態是否有變化
            const currentStateKey = statusSummary.active_algorithms.sort().join(',')
            const hasStateChanged = lastSyncStateRef.current !== currentStateKey
            
            if (hasStateChanged) {
                console.log('🔄 狀態變化檢測到，獲取到狀態摘要:', statusSummary)
                lastSyncStateRef.current = currentStateKey
            }

            // 發送狀態同步事件到 useRLMonitoring hook
            ;['dqn', 'ppo', 'sac'].forEach(algorithm => {
                const isActive = statusSummary.active_algorithms.includes(algorithm)
                
                if (hasStateChanged) {
                    console.log(`🔄 同步 ${algorithm} 狀態: ${isActive ? '訓練中' : '停止'}`)
                }
                
                setTimeout(() => {
                    window.dispatchEvent(
                        new CustomEvent('trainingStateSync', {
                            detail: {
                                engine: algorithm,
                                isTraining: isActive,
                            },
                        })
                    )
                }, 0)
            })

            if (hasStateChanged) {
                console.log(`🔄 狀態同步完成 - 活躍算法: [${statusSummary.active_algorithms.join(', ')}]`)
            }
            
        } catch (error) {
            console.warn('狀態同步失敗:', error)
        }
    }, [backendConnected])

    // 更新 ref 引用 - 在 useEffect 中處理
    useEffect(() => {
        fetchRLStatusRef.current = fetchRLStatus
        syncFrontendStateRef.current = syncFrontendState
    }, [fetchRLStatus, syncFrontendState])

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
                // 每60秒重新同步一次狀態，減少頻率避免循環
                const syncInterval = setInterval(() => {
                    syncFrontendState()
                }, 60000) // 改為 60 秒，減少同步頻率
                
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
            _setIsTraining(isTraining)

            // 發送訓練狀態變更事件到 useRLMonitoring hook
            setTimeout(() => {
                window.dispatchEvent(
                    new CustomEvent('trainingStateUpdate', {
                        detail: {
                            engine: 'dqn',
                            isTraining: isTraining,
                        },
                    })
                )
            }, 0)

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
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to start DQN training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
            } else {
                // 停止訓練 - 先獲取會話然後停止
                apiClient.getRLTrainingSessions()
                    .then((sessions) => {
                        const dqnSession = (sessions as Array<Record<string, unknown>>).find(s => s.algorithm_name === 'dqn' && s.status === 'active')
                        if (dqnSession) {
                            return apiClient.stopTrainingSession(dqnSession.session_id as string)
                        } else {
                            console.warn('沒有找到活躍的 DQN 訓練會話')
                            return Promise.resolve()
                        }
                    })
                    .then((response) => {
                        console.log('DQN Training stop successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to stop DQN training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
            }
        }

        const handlePpoToggle = (event: CustomEvent) => {
            const isTraining = (event.detail as { isTraining: boolean })
                .isTraining
            console.log('收到 PPO 切換事件:', { isTraining })
            _setIsTraining(isTraining)

            // 發送訓練狀態變更事件到 useRLMonitoring hook
            setTimeout(() => {
                window.dispatchEvent(
                    new CustomEvent('trainingStateUpdate', {
                        detail: {
                            engine: 'ppo',
                            isTraining: isTraining,
                        },
                    })
                )
            }, 0)

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
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to start PPO training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
            } else {
                // 停止訓練 - 先獲取會話然後停止
                apiClient.getRLTrainingSessions()
                    .then((sessions) => {
                        const ppoSession = (sessions as Array<Record<string, unknown>>).find(s => s.algorithm_name === 'ppo' && s.status === 'active')
                        if (ppoSession) {
                            return apiClient.stopTrainingSession(ppoSession.session_id as string)
                        } else {
                            console.warn('沒有找到活躍的 PPO 訓練會話')
                            return Promise.resolve()
                        }
                    })
                    .then((response) => {
                        console.log('PPO Training stop successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to stop PPO training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
            }
        }
        const handleSacToggle = (event: CustomEvent) => {
            const isTraining = (event.detail as { isTraining: boolean })
                .isTraining
            console.log('收到 SAC 切換事件:', { isTraining })
            _setIsTraining(isTraining)

            // 發送訓練狀態變更事件到 useRLMonitoring hook
            setTimeout(() => {
                window.dispatchEvent(
                    new CustomEvent('trainingStateUpdate', {
                        detail: {
                            engine: 'sac',
                            isTraining: isTraining,
                        },
                    })
                )
            }, 0)

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
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to start SAC training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
            } else {
                // 停止訓練 - 先獲取會話然後停止
                apiClient.getRLTrainingSessions()
                    .then((sessions) => {
                        const sacSession = (sessions as Array<Record<string, unknown>>).find(s => s.algorithm_name === 'sac' && s.status === 'active')
                        if (sacSession) {
                            return apiClient.stopTrainingSession(sacSession.session_id as string)
                        } else {
                            console.warn('沒有找到活躍的 SAC 訓練會話')
                            return Promise.resolve()
                        }
                    })
                    .then((response) => {
                        console.log('SAC Training stop successful:', response)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
                    .catch((error) => {
                        console.error('Failed to stop SAC training:', error)
                        setTimeout(() => {
                            if (backendConnected) {
                                fetchRLStatusRef.current?.()
                                syncFrontendStateRef.current?.()
                            }
                        }, 100)
                    })
            }
        }

        console.log('註冊事件監聽器')
        window.addEventListener('dqnToggle', handleDqnToggle as EventListener)
        window.addEventListener('ppoToggle', handlePpoToggle as EventListener)
        window.addEventListener('sacToggle', handleSacToggle as EventListener)

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
        }
    }, [backendConnected]) // 簡化依賴項避免無限重新註冊

    // 渲染單個算法的監控面板
    const renderAlgorithmPanel = (algorithm: 'dqn' | 'ppo' | 'sac', metrics: RLEngineMetrics | null) => {
        const algorithmName = algorithm.toUpperCase()
        const isActive = metrics?.model_status === 'training'
        
        return (
            <div key={algorithm} className={`algorithm-panel ${algorithm}-panel ${isActive ? 'active' : ''}`}>
                <div className="algorithm-header">
                    <h4>{algorithmName} Engine</h4>
                    <div className={`status-badge ${isActive ? 'active' : 'idle'}`}>
                        {isActive ? '🔴 訓練中' : '⚪ 待機'}
                    </div>
                </div>
                
                {metrics ? (
                    <div className="algorithm-metrics">
                        <div className="metrics-row">
                            <div className="metric-item">
                                <span className="metric-label">平均獎勵</span>
                                <span className="metric-value">
                                    {metrics.average_reward.toFixed(2)}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">Episodes</span>
                                <span className="metric-value">
                                    {metrics.episodes_completed}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">訓練狀態</span>
                                <span className="metric-value">
                                    {metrics.model_status === 'training' ? '🔴 進行中' : 
                                     metrics.model_status === 'inference' ? '🟡 推理' : '⚪ 待機'}
                                </span>
                            </div>
                        </div>
                        
                        <div className="progress-section">
                            <div className="progress-label">
                                <span>訓練進度</span>
                                <span>{metrics.training_progress.toFixed(1)}%</span>
                            </div>
                            <div className="progress-bar">
                                <div
                                    className={`progress-fill ${algorithm}-progress`}
                                    style={{
                                        width: `${metrics.training_progress}%`,
                                    }}
                                ></div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="no-data">
                        <span>無訓練數據</span>
                    </div>
                )}
            </div>
        )
    }

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
            </div>
            
            {error && <div className="error-message">{error}</div>}
            {!backendConnected && !error && (
                <div className="loading-message">正在連接到後端服務...</div>
            )}
            {backendConnected && isLoading && !rlMetrics && (
                <div className="loading-message">正在加載RL引擎數據...</div>
            )}
            
            {backendConnected && (
                <div className="monitor-content">
                    {/* 系統概覽 - 只顯示有意義的真實指標 */}
                    {rlMetrics && (
                        <div className="system-overview">
                            <div className="overview-metrics">
                                <div className="metric-item">
                                    <span className="metric-label">記憶體</span>
                                    <span className="metric-value">
                                        {rlMetrics.memory_usage.toFixed(0)} MB
                                    </span>
                                </div>
                                <div className="metric-item">
                                    <span className="metric-label">GPU 使用率</span>
                                    <span className="metric-value">
                                        {rlMetrics.gpu_utilization.toFixed(0)}%
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                    
                    {/* 三個算法的監控面板 */}
                    <div className="algorithms-grid">
                        {renderAlgorithmPanel('dqn', allEngineMetrics.dqn)}
                        {renderAlgorithmPanel('ppo', allEngineMetrics.ppo)}
                        {renderAlgorithmPanel('sac', allEngineMetrics.sac)}
                    </div>
                </div>
            )}
        </div>
    )
}

export default GymnasiumRLMonitor
