import React, { useState, useEffect, useCallback, useRef } from 'react'
import TimePredictionTimeline from './TimePredictionTimeline'
import SatelliteConnectionIndicator from './SatelliteConnectionIndicator'
import HandoverControlPanel from './HandoverControlPanel'
import SynchronizedAlgorithmVisualization from './SynchronizedAlgorithmVisualization'
import {
    HandoverState,
    SatelliteConnection,
    TimePredictionData,
    BinarySearchIteration,
    HandoverEvent,
} from '../../types/handover'
import { VisibleSatelliteInfo } from '../../types/satellite'
import './HandoverManager.scss'

interface HandoverManagerProps {
    satellites: VisibleSatelliteInfo[]
    selectedUEId?: number
    isEnabled: boolean
    onHandoverEvent?: (event: HandoverEvent) => void
    mockMode?: boolean // 用於開發測試
    hideUI?: boolean // 隱藏 UI 但保持邏輯運行
    handoverMode?: 'demo' | 'real' // 換手模式控制
    // 3D 動畫狀態更新回調
    onHandoverStateChange?: (state: HandoverState) => void
    onCurrentConnectionChange?: (connection: SatelliteConnection | null) => void
    onPredictedConnectionChange?: (
        connection: SatelliteConnection | null
    ) => void
    onTransitionChange?: (isTransitioning: boolean, progress: number) => void
    // 🚀 演算法結果回調 - 用於對接視覺化
    onAlgorithmResults?: (results: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }) => void
    // 🎮 衛星速度同步
    speedMultiplier?: number
}

const HandoverManager: React.FC<HandoverManagerProps> = ({
    satellites,
    selectedUEId,
    isEnabled,
    onHandoverEvent,
    mockMode = true, // 開發階段使用模擬數據
    hideUI = false,
    handoverMode = 'demo',
    onHandoverStateChange,
    onCurrentConnectionChange,
    onPredictedConnectionChange,
    onTransitionChange,
    onAlgorithmResults,
    speedMultiplier = 60,
}) => {
    // 換手狀態管理
    const [handoverState, setHandoverState] = useState<HandoverState>({
        currentSatellite: '',
        predictedSatellite: '',
        handoverTime: 0,
        status: 'idle',
        confidence: 0.95,
        deltaT: 10, // 10秒間隔 - 平衡演示效果與真實感
    })

    // 🎯 時間預測數據
    const [timePredictionData, setTimePredictionData] =
        useState<TimePredictionData>({
            currentTime: Date.now(),
            futureTime: Date.now() + 10000,
            handoverTime: undefined,
            iterations: [],
            accuracy: 0.95,
        })

    // 🔄 換手歷史記錄 - 防止頻繁互換
    const handoverHistoryRef = useRef<{
        recentHandovers: Array<{
            from: string
            to: string
            timestamp: number
        }>
        cooldownPeriod: number // 冷卻期（毫秒）
    }>({
        recentHandovers: [],
        cooldownPeriod: handoverMode === 'demo' ? 90000 : 120000, // 演示模式90秒，真實模式120秒（統一加強防護）
    })

    // 衛星連接狀態
    const [currentConnection, setCurrentConnection] =
        useState<SatelliteConnection | null>(null)
    const [predictedConnection, setPredictedConnection] =
        useState<SatelliteConnection | null>(null)
    const [isTransitioning, setIsTransitioning] = useState(false)
    const [transitionProgress, setTransitionProgress] = useState(0)

    // 控制面板模式換手
    const [controlMode, setControlMode] = useState<'auto' | 'manual'>('auto')

    // 標籤頁狀態管理
    const [activeTab, setActiveTab] = useState<'status' | 'algorithm'>('status')

    // 模擬數據生成器（開發用）
    const generateMockSatelliteConnection = useCallback(
        (
            satellite: VisibleSatelliteInfo,
            isConnected: boolean = false
        ): SatelliteConnection => {
            return {
                satelliteId: satellite.norad_id.toString(),
                satelliteName: satellite.name,
                elevation: satellite.elevation_deg,
                azimuth: satellite.azimuth_deg,
                distance: satellite.distance_km,
                signalStrength: -60 - Math.random() * 40, // -60 to -100 dBm
                isConnected,
                isPredicted: !isConnected,
            }
        },
        []
    )

    // 🔗 模擬二點預測算法 - 與 DynamicSatelliteRenderer 的 ID 系統兼容
    const simulateTwoPointPrediction = useCallback(() => {
        // 🚀 使用固定的模擬衛星 ID，與 DynamicSatelliteRenderer 完全匹配
        const simulatedSatellites: VisibleSatelliteInfo[] = Array.from(
            { length: 18 },
            (_, i) => ({
                norad_id: 1000 + i, // 修復：使用數字類型
                name: `STARLINK-${1000 + i}`,
                elevation_deg: 30 + Math.random() * 60,
                azimuth_deg: Math.random() * 360,
                distance_km: 500 + Math.random() * 500,
                line1: `1 ${
                    1000 + i
                }U 20001001.00000000  .00000000  00000-0  00000-0 0  9999`,
                line2: `2 ${
                    1000 + i
                }  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000`,
            })
        )

        const now = Date.now()
        const futureTime = now + handoverState.deltaT * 1000

        // 🎯 模擬選擇當前最佳衛星 - 優先選擇前幾個衛星以提高匹配機率
        const currentBestIndex = Math.floor(
            Math.random() * Math.min(6, simulatedSatellites.length)
        ) // 前6個衛星
        const currentBest = simulatedSatellites[currentBestIndex]

        // 🚫 核心修復：確保不會選擇自己作為換手目標
        // 先過濾掉當前衛星，確保候選列表不包含自己
        let availableTargets = simulatedSatellites.filter(
            (sat, index) => index !== currentBestIndex
        )

        // 🚫 如果沒有可用目標，直接返回不換手
        if (availableTargets.length === 0) {
            console.warn('⚠️ 沒有可用的換手目標衛星')
            setHandoverState((prev) => ({
                ...prev,
                currentSatellite: currentBest?.norad_id.toString() || '',
                predictedSatellite: '', // 清空預測衛星
                handoverTime: 0,
                status: 'idle',
            }))

            if (currentBest) {
                const currentConn = generateMockSatelliteConnection(
                    currentBest,
                    true
                )
                setCurrentConnection(currentConn)
            }
            setPredictedConnection(null)
            return
        }

        // 🚫 清理過期的換手記錄
        const history = handoverHistoryRef.current
        history.recentHandovers = history.recentHandovers.filter(
            (record) => now - record.timestamp < history.cooldownPeriod
        )

        // 🔄 如果有當前衛星，檢查換手歷史
        if (currentBest && availableTargets.length > 0) {
            const currentSatId = currentBest.norad_id.toString()

            // 找出最近與當前衛星有換手記錄的衛星
            const recentPartners = new Set<string>()

            history.recentHandovers.forEach((record) => {
                // 檢查雙向換手記錄
                if (record.from === currentSatId) {
                    recentPartners.add(record.to)
                } else if (record.to === currentSatId) {
                    recentPartners.add(record.from)
                }
            })

            // 🎯 優先選擇沒有最近換手記錄的衛星
            const preferredTargets = availableTargets.filter(
                (sat) => !recentPartners.has(sat.norad_id.toString())
            )

            if (preferredTargets.length > 0) {
                availableTargets = preferredTargets
            }
        }

        // 🎯 智能選擇換手目標 - 基於多種策略
        let futureBest: VisibleSatelliteInfo | null = null

        if (availableTargets.length > 0) {
            // 策略1：優先選擇相鄰的衛星（更符合軌道換手邏輯）
            const adjacentCandidates = []
            if (currentBestIndex < simulatedSatellites.length - 1) {
                const nextSat = simulatedSatellites[currentBestIndex + 1]
                if (availableTargets.includes(nextSat)) {
                    adjacentCandidates.push(nextSat)
                }
            }
            if (currentBestIndex > 0) {
                const prevSat = simulatedSatellites[currentBestIndex - 1]
                if (availableTargets.includes(prevSat)) {
                    adjacentCandidates.push(prevSat)
                }
            }

            if (adjacentCandidates.length > 0 && Math.random() < 0.6) {
                // 60% 機率選擇相鄰衛星
                futureBest =
                    adjacentCandidates[
                        Math.floor(Math.random() * adjacentCandidates.length)
                    ]
            } else {
                // 策略2：選擇信號品質最佳的衛星
                futureBest = availableTargets.reduce((best, sat) =>
                    !best || sat.elevation_deg > best.elevation_deg ? sat : best
                )
            }
        }

        // 🚫 最終安全檢查：確保選擇的衛星不是當前衛星
        if (!futureBest || futureBest.norad_id === currentBest?.norad_id) {
            console.warn('⚠️ 無法找到合適的換手目標，保持當前連接')
            setHandoverState((prev) => ({
                ...prev,
                currentSatellite: currentBest?.norad_id.toString() || '',
                predictedSatellite: '', // 清空預測衛星
                handoverTime: 0,
                status: 'idle',
            }))

            if (currentBest) {
                const currentConn = generateMockSatelliteConnection(
                    currentBest,
                    true
                )
                setCurrentConnection(currentConn)
            }
            setPredictedConnection(null)
            return
        }

        // ✅ 成功選擇換手目標
        setHandoverState((prev) => ({
            ...prev,
            currentSatellite: currentBest?.norad_id.toString() || '',
            predictedSatellite: futureBest?.norad_id.toString() || '',
            status: 'predicting',
        }))

        // 🔗 更新連接狀態
        if (currentBest) {
            const currentConn = generateMockSatelliteConnection(
                currentBest,
                true
            )
            setCurrentConnection(currentConn)
        }

        // 🎯 由於我們已經確保futureBest不等於currentBest，這裡一定會執行換手邏輯
        const predictedConn = generateMockSatelliteConnection(futureBest, false)
        setPredictedConnection(predictedConn)
        // 模擬需要換手
        simulateBinarySearch(now, futureTime)

        // 更新時間預測數據
        setTimePredictionData({
            currentTime: now,
            futureTime,
            handoverTime: now + 5000, // 調整為 5 秒，在 10 秒區間的中點
            iterations: [],
            accuracy: 0.95 + Math.random() * 0.04, // 95-99%
        })

        // 換手決策完成
    }, [handoverState.deltaT, generateMockSatelliteConnection]) // 移除 satellites 依賴，使用自己的模擬數據

    // 模擬 Binary Search Refinement
    const simulateBinarySearch = useCallback(
        (startTime: number, endTime: number) => {
            const iterations: BinarySearchIteration[] = []
            let currentStart = startTime
            let currentEnd = endTime
            let iterationCount = 0
            const targetPrecision = 0.1 // 100ms

            const performIteration = () => {
                iterationCount++
                const midTime = (currentStart + currentEnd) / 2
                const precision = (currentEnd - currentStart) / 1000 // 轉換為秒

                const iteration: BinarySearchIteration = {
                    iteration: iterationCount,
                    startTime: currentStart,
                    endTime: currentEnd,
                    midTime,
                    satellite: `SAT-${Math.floor(Math.random() * 1000)}`,
                    precision,
                    completed: precision <= targetPrecision,
                }

                iterations.push(iteration)

                if (precision > targetPrecision && iterationCount < 10) {
                    // 模擬縮小搜索範圍
                    if (Math.random() < 0.5) {
                        currentEnd = midTime
                    } else {
                        currentStart = midTime
                    }

                    setTimeout(() => performIteration(), 750) // 0.75秒延遲平衡計算時間
                } else {
                    // 搜索完成
                    const finalHandoverTime = midTime
                    setHandoverState((prev) => ({
                        ...prev,
                        handoverTime: finalHandoverTime,
                        status: 'idle',
                    }))

                    setTimePredictionData((prev) => ({
                        ...prev,
                        handoverTime: finalHandoverTime,
                        iterations,
                    }))
                }
            }

            performIteration()
        },
        []
    )

    // 手動換手處理
    const handleManualHandover = useCallback(
        async (targetSatelliteId: string) => {
            const targetSatellite = satellites.find(
                (s) => s.norad_id.toString() === targetSatelliteId
            )
            if (!targetSatellite || !currentConnection) return

            setHandoverState((prev) => ({ ...prev, status: 'handover' }))
            setIsTransitioning(true)
            setTransitionProgress(0)

            // 創建換手事件
            const handoverEvent: HandoverEvent = {
                id: `handover_${Date.now()}`,
                timestamp: Date.now(),
                fromSatellite: currentConnection.satelliteId,
                toSatellite: targetSatelliteId,
                duration: 0,
                success: false,
                reason: 'manual',
            }

            // 模擬換手過程
            const startTime = Date.now()
            const handoverDuration = 3500 + Math.random() * 3000 // 3.5-6.5秒 - 平衡速度與真實感

            const progressInterval = setInterval(() => {
                const elapsed = Date.now() - startTime
                const progress = Math.min(elapsed / handoverDuration, 1)
                setTransitionProgress(progress)

                if (progress >= 1) {
                    clearInterval(progressInterval)

                    // 換手完成
                    const success = Math.random() > 0.1 // 90% 成功率
                    const newConnection = generateMockSatelliteConnection(
                        targetSatellite,
                        true
                    )

                    setCurrentConnection(newConnection)
                    setPredictedConnection(null)
                    setIsTransitioning(false)
                    setTransitionProgress(0)

                    setHandoverState((prev) => ({
                        ...prev,
                        currentSatellite: targetSatelliteId,
                        status: success ? 'complete' : 'failed',
                    }))

                    // 📝 記錄換手事件到歷史記錄（只有成功的換手才記錄）
                    if (success) {
                        recordHandover(
                            currentConnection.satelliteId,
                            targetSatelliteId
                        )
                    }

                    // 發送換手事件
                    const completedEvent: HandoverEvent = {
                        ...handoverEvent,
                        duration: Date.now() - startTime,
                        success,
                    }
                    onHandoverEvent?.(completedEvent)

                    // 2秒後重置狀態
                    setTimeout(() => {
                        setHandoverState((prev) => ({
                            ...prev,
                            status: 'idle',
                        }))
                    }, 2000)
                }
            }, 100)
        },
        [
            satellites,
            currentConnection,
            generateMockSatelliteConnection,
            onHandoverEvent,
        ]
    )

    // 取消換手
    const handleCancelHandover = useCallback(() => {
        setIsTransitioning(false)
        setTransitionProgress(0)
        setHandoverState((prev) => ({ ...prev, status: 'idle' }))
    }, [])

    // 初始化和定期更新
    useEffect(() => {
        if (!isEnabled || !mockMode || controlMode !== 'auto') return

        // 初始化
        simulateTwoPointPrediction()

        // 定期更新預測（每 deltaT 秒）- 僅在自動模式下
        const interval = setInterval(() => {
            simulateTwoPointPrediction()
        }, handoverState.deltaT * 1000)

        return () => clearInterval(interval)
    }, [
        isEnabled,
        mockMode,
        controlMode,
        simulateTwoPointPrediction,
        handoverState.deltaT,
    ])

    // 時間更新處理
    const handleTimeUpdate = useCallback((currentTime: number) => {
        setTimePredictionData((prev) => ({
            ...prev,
            currentTime,
        }))
    }, [])

    // 狀態同步到 3D 動畫
    useEffect(() => {
        if (onHandoverStateChange) {
            onHandoverStateChange(handoverState)
        }
    }, [handoverState, onHandoverStateChange])

    useEffect(() => {
        if (onCurrentConnectionChange) {
            onCurrentConnectionChange(currentConnection)
        }
    }, [currentConnection, onCurrentConnectionChange])

    useEffect(() => {
        if (onPredictedConnectionChange) {
            onPredictedConnectionChange(predictedConnection)
        }
    }, [predictedConnection, onPredictedConnectionChange])

    useEffect(() => {
        if (onTransitionChange) {
            onTransitionChange(isTransitioning, transitionProgress)
        }
    }, [isTransitioning, transitionProgress, onTransitionChange])

    // 📝 記錄換手事件
    const recordHandover = useCallback(
        (fromSatellite: string, toSatellite: string) => {
            const now = Date.now()
            handoverHistoryRef.current.recentHandovers.push({
                from: fromSatellite,
                to: toSatellite,
                timestamp: now,
            })

            // 清理過期記錄（超過冷卻期的記錄）
            handoverHistoryRef.current.recentHandovers =
                handoverHistoryRef.current.recentHandovers.filter(
                    (record) =>
                        now - record.timestamp <
                        handoverHistoryRef.current.cooldownPeriod
                )

            // 換手記錄已更新
        },
        [handoverMode]
    )

    // 🔄 當換手模式改變時，更新冷卻期並清理歷史記錄
    useEffect(() => {
        const newCooldown = handoverMode === 'demo' ? 90000 : 120000
        if (handoverHistoryRef.current.cooldownPeriod !== newCooldown) {
            handoverHistoryRef.current.cooldownPeriod = newCooldown
            // 清空所有歷史記錄，避免模式切換時的衝突
            handoverHistoryRef.current.recentHandovers = []
            // 模式切換完成
        }
    }, [handoverMode])

    if (!isEnabled) {
        return (
            <div className="handover-manager disabled">
                <div className="disabled-message">
                    <h3>🔒 換手管理器已停用</h3>
                    <p>請啟用換手相關功能來使用此面板</p>
                </div>
            </div>
        )
    }

    // 🚀 如果 hideUI 為 true，則隱藏所有 UI 但保持邏輯運行
    if (hideUI) {
        return null
    }

    return (
        <div className="handover-manager">
            <div className="manager-header">
                <h2>🔄 LEO 衛星換手管理系統</h2>
                {selectedUEId && (
                    <div className="selected-ue">
                        <span>控制 UE: {selectedUEId}</span>
                    </div>
                )}
            </div>

            {/* 模式換手控制 - 移到最頂部作為全局控制 */}
            <div className="mode-switcher">
                <div className="switcher-header">
                    <span className="switcher-title">換手控制模式</span>
                </div>
                <div className="switcher-tabs">
                    <button
                        className={`switcher-tab ${
                            controlMode === 'auto' ? 'active' : ''
                        }`}
                        onClick={() => setControlMode('auto')}
                    >
                        <span className="tab-icon">🤖</span>
                        <span className="tab-label">自動預測</span>
                    </button>
                    <button
                        className={`switcher-tab ${
                            controlMode === 'manual' ? 'active' : ''
                        }`}
                        onClick={() => setControlMode('manual')}
                    >
                        <span className="tab-icon">🎮</span>
                        <span className="tab-label">手動控制</span>
                    </button>
                </div>
            </div>

            <div className="manager-content">
                {/* 二點預測時間軸 - 在兩種模式下都顯示 */}
                <TimePredictionTimeline
                    data={timePredictionData}
                    isActive={isEnabled}
                    onTimeUpdate={handleTimeUpdate}
                />

                {/* 標籤頁導航 */}
                <div className="tab-navigation">
                    <button
                        className={`tab-button ${
                            activeTab === 'status' ? 'active' : ''
                        }`}
                        onClick={() => setActiveTab('status')}
                    >
                        <span className="tab-icon">📡</span>
                        <span className="tab-label">
                            {controlMode === 'auto'
                                ? '衛星接入狀態'
                                : '手動控制面板'}
                        </span>
                    </button>
                    {controlMode === 'auto' && (
                        <button
                            className={`tab-button ${
                                activeTab === 'algorithm' ? 'active' : ''
                            }`}
                            onClick={() => setActiveTab('algorithm')}
                        >
                            <span className="tab-icon">🧮</span>
                            <span className="tab-label">
                                Fine-Grained Algorithm
                            </span>
                        </button>
                    )}
                </div>

                {/* 標籤頁內容 */}
                <div className="tab-content">
                    {activeTab === 'status' && (
                        <div className="status-tab">
                            {controlMode === 'auto' ? (
                                <SatelliteConnectionIndicator
                                    currentConnection={currentConnection}
                                    predictedConnection={predictedConnection}
                                    isTransitioning={isTransitioning}
                                    transitionProgress={transitionProgress}
                                />
                            ) : (
                                <HandoverControlPanel
                                    handoverState={handoverState}
                                    availableSatellites={satellites}
                                    currentConnection={currentConnection}
                                    onManualHandover={handleManualHandover}
                                    onCancelHandover={handleCancelHandover}
                                    isEnabled={isEnabled}
                                />
                            )}
                        </div>
                    )}

                    {activeTab === 'algorithm' && controlMode === 'auto' && (
                        <div className="algorithm-tab">
                            <SynchronizedAlgorithmVisualization
                                satellites={satellites}
                                selectedUEId={selectedUEId}
                                isEnabled={isEnabled}
                                speedMultiplier={speedMultiplier}
                                onAlgorithmStep={(step) => {
                                    // 可以在這裡處理算法步驟事件
                                }}
                                onAlgorithmResults={(results) => {
                                    // 向 App.tsx 傳遞演算法結果，用於更新 3D 視覺化
                                    onAlgorithmResults?.(results)
                                }}
                            />
                        </div>
                    )}
                </div>
            </div>

            {/* {mockMode && (
                <div className="mock-mode-indicator">
                    ⚠️ 開發模式 - 使用模擬數據
                </div>
            )} */}
        </div>
    )
}

export default HandoverManager
