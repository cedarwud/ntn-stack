import React, { useState, useEffect, useCallback } from 'react'
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
    // 3D 動畫狀態更新回調
    onHandoverStateChange?: (state: HandoverState) => void
    onCurrentConnectionChange?: (connection: SatelliteConnection | null) => void
    onPredictedConnectionChange?: (connection: SatelliteConnection | null) => void
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

    // 時間預測數據
    const [timePredictionData, setTimePredictionData] =
        useState<TimePredictionData>({
            currentTime: Date.now(),
            futureTime: Date.now() + 10000, // 對應 deltaT 的 10 秒
            iterations: [],
            accuracy: 0.95,
        })

    // 衛星連接狀態
    const [currentConnection, setCurrentConnection] =
        useState<SatelliteConnection | null>(null)
    const [predictedConnection, setPredictedConnection] =
        useState<SatelliteConnection | null>(null)
    const [isTransitioning, setIsTransitioning] = useState(false)
    const [transitionProgress, setTransitionProgress] = useState(0)

    // 控制面板模式切換
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
                satelliteId: satellite.norad_id,
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

    // 模擬二點預測算法
    const simulateTwoPointPrediction = useCallback(() => {
        if (!satellites.length) return

        const now = Date.now()
        const futureTime = now + handoverState.deltaT * 1000

        // 模擬選擇當前最佳衛星
        const sortedSatellites = [...satellites].sort(
            (a, b) => b.elevation_deg - a.elevation_deg
        )
        const currentBest = sortedSatellites[0]
        const futureBest = sortedSatellites[Math.random() < 0.7 ? 0 : 1] // 70% 機率保持相同

        setHandoverState((prev) => ({
            ...prev,
            currentSatellite: currentBest?.norad_id || '',
            predictedSatellite: futureBest?.norad_id || '',
            status: 'predicting',
        }))

        // 更新連接狀態
        if (currentBest) {
            setCurrentConnection(
                generateMockSatelliteConnection(currentBest, true)
            )
        }
        if (futureBest && futureBest.norad_id !== currentBest?.norad_id) {
            setPredictedConnection(
                generateMockSatelliteConnection(futureBest, false)
            )
            // 模擬需要換手
            simulateBinarySearch(now, futureTime)
        } else {
            setPredictedConnection(null)
            setHandoverState((prev) => ({
                ...prev,
                handoverTime: 0,
                status: 'idle',
            }))
        }

        // 更新時間預測數據
        setTimePredictionData({
            currentTime: now,
            futureTime,
            handoverTime:
                futureBest?.norad_id !== currentBest?.norad_id
                    ? now + 5000 // 調整為 5 秒，在 10 秒區間的中點
                    : undefined,
            iterations: [],
            accuracy: 0.95 + Math.random() * 0.04, // 95-99%
        })
    }, [satellites, handoverState.deltaT, generateMockSatelliteConnection])

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
                (s) => s.norad_id === targetSatelliteId
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
    }, [isEnabled, mockMode, controlMode, simulateTwoPointPrediction, handoverState.deltaT])

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

            {/* 模式切換控制 - 移到最頂部作為全局控制 */}
            <div className="mode-switcher">
                <div className="switcher-header">
                    <span className="switcher-title">換手控制模式</span>
                </div>
                <div className="switcher-tabs">
                    <button
                        className={`switcher-tab ${controlMode === 'auto' ? 'active' : ''}`}
                        onClick={() => setControlMode('auto')}
                    >
                        <span className="tab-icon">🤖</span>
                        <span className="tab-label">自動預測</span>
                    </button>
                    <button
                        className={`switcher-tab ${controlMode === 'manual' ? 'active' : ''}`}
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
                        className={`tab-button ${activeTab === 'status' ? 'active' : ''}`}
                        onClick={() => setActiveTab('status')}
                    >
                        <span className="tab-icon">📡</span>
                        <span className="tab-label">
                            {controlMode === 'auto' ? '衛星接入狀態' : '手動控制面板'}
                        </span>
                    </button>
                    {controlMode === 'auto' && (
                        <button 
                            className={`tab-button ${activeTab === 'algorithm' ? 'active' : ''}`}
                            onClick={() => setActiveTab('algorithm')}
                        >
                            <span className="tab-icon">🧮</span>
                            <span className="tab-label">Fine-Grained Algorithm</span>
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
                                    console.log('🧮 算法步驟:', step)
                                    // 可以在這裡處理算法步驟事件
                                }}
                                onAlgorithmResults={(results) => {
                                    console.log('🚀 演算法結果:', results)
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
