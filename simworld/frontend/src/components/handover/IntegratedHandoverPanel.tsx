import React, { useState, useEffect } from 'react'
import {
    HandoverState,
    SatelliteConnection,
    HandoverEvent,
} from '../../types/handover'
import { VisibleSatelliteInfo } from '../../types/satellite'
import HandoverControlPanel from './HandoverControlPanel'
import SatelliteConnectionIndicator from './SatelliteConnectionIndicator'
import TimePredictionTimeline from './TimePredictionTimeline'
import './IntegratedHandoverPanel.scss'

interface HandoverMetrics {
    totalPredictions: number
    successfulHandovers: number
    failedHandovers: number
    averageHandoverTime: number
    predictionAccuracy: number
    currentHandovers: number
}

interface TimePredictionData {
    currentTime: number
    futureTime: number
    handoverTime?: number
    iterations: any[]
    accuracy: number
}

interface IntegratedHandoverPanelProps {
    satellites: VisibleSatelliteInfo[]
    selectedUEId?: string
    isEnabled: boolean
    onHandoverEvent?: (event: HandoverEvent) => void
    onHandoverStateChange?: (state: HandoverState) => void
    onCurrentConnectionChange?: (connection: SatelliteConnection | null) => void
    onPredictedConnectionChange?: (
        connection: SatelliteConnection | null
    ) => void
    onTransitionChange?: (isTransitioning: boolean) => void
}

const IntegratedHandoverPanel: React.FC<IntegratedHandoverPanelProps> = ({
    satellites,
    selectedUEId,
    isEnabled,
    onHandoverEvent,
    onHandoverStateChange,
    onCurrentConnectionChange,
    onPredictedConnectionChange,
    onTransitionChange,
}) => {
    const [activeTab, setActiveTab] = useState<
        'status' | 'prediction' | 'performance'
    >('status')
    const [controlMode, setControlMode] = useState<'auto' | 'manual'>('auto')

    // 換手狀態
    const [handoverState, setHandoverState] = useState<HandoverState>({
        currentSatellite: '',
        predictedSatellite: '',
        handoverTime: 0,
        status: 'idle',
        confidence: 0.95,
        deltaT: 10,
    })

    // 連接狀態
    const [currentConnection, setCurrentConnection] =
        useState<SatelliteConnection | null>(null)
    const [predictedConnection, setPredictedConnection] =
        useState<SatelliteConnection | null>(null)
    const [isTransitioning, setIsTransitioning] = useState(false)
    const [transitionProgress, setTransitionProgress] = useState(0)

    // 性能指標
    const [metrics, setMetrics] = useState<HandoverMetrics>({
        totalPredictions: 0,
        successfulHandovers: 0,
        failedHandovers: 0,
        averageHandoverTime: 0,
        predictionAccuracy: 0,
        currentHandovers: 0,
    })

    // 時間預測數據
    const [timePredictionData, setTimePredictionData] =
        useState<TimePredictionData>({
            currentTime: Date.now(),
            futureTime: Date.now() + 10000,
            iterations: [],
            accuracy: 0.95,
        })

    // 模擬換手預測邏輯
    useEffect(() => {
        if (!isEnabled || satellites.length === 0) return

        const generatePrediction = () => {
            const now = Date.now()
            const futureTime = now + handoverState.deltaT * 1000

            // 選擇當前最佳衛星
            const currentBest = satellites.reduce((best, sat) =>
                !best || sat.elevation_deg > best.elevation_deg ? sat : best
            )

            // 模擬未來時間點的最佳衛星（可能不同）
            const futureBest =
                satellites.find(
                    (sat) =>
                        sat.norad_id !== currentBest?.norad_id &&
                        sat.elevation_deg > 20
                ) || currentBest

            if (currentBest) {
                const newCurrentConnection: SatelliteConnection = {
                    satelliteId: currentBest.norad_id,
                    satelliteName: currentBest.name,
                    isConnected: true,
                    isPredicted: false,
                    signalStrength:
                        -65 - (90 - currentBest.elevation_deg) * 0.5,
                    elevation: currentBest.elevation_deg,
                    azimuth: currentBest.azimuth_deg,
                    distance: currentBest.distance_km,
                    quality: { snr: 25, rssi: -65, bandwidth: 100 },
                    performance: { latency: 50, throughput: 150, jitter: 5 },
                }

                setCurrentConnection(newCurrentConnection)
                onCurrentConnectionChange?.(newCurrentConnection)
            }

            if (futureBest && futureBest.norad_id !== currentBest?.norad_id) {
                const newPredictedConnection: SatelliteConnection = {
                    satelliteId: futureBest.norad_id,
                    satelliteName: futureBest.name,
                    isConnected: false,
                    isPredicted: true,
                    signalStrength: -65 - (90 - futureBest.elevation_deg) * 0.5,
                    elevation: futureBest.elevation_deg,
                    azimuth: futureBest.azimuth_deg,
                    distance: futureBest.distance_km,
                    quality: { snr: 25, rssi: -65, bandwidth: 100 },
                    performance: { latency: 50, throughput: 150, jitter: 5 },
                }

                setPredictedConnection(newPredictedConnection)
                onPredictedConnectionChange?.(newPredictedConnection)

                // 更新換手狀態
                const newHandoverState = {
                    ...handoverState,
                    currentSatellite: currentBest?.norad_id || '',
                    predictedSatellite: futureBest.norad_id,
                    handoverTime: now + 5000,
                    status: 'predicting' as const,
                }

                setHandoverState(newHandoverState)
                onHandoverStateChange?.(newHandoverState)

                // 更新時間預測數據
                setTimePredictionData({
                    currentTime: now,
                    futureTime,
                    handoverTime: now + 5000,
                    iterations: [],
                    accuracy: 0.95 + Math.random() * 0.04,
                })
            } else {
                setPredictedConnection(null)
                onPredictedConnectionChange?.(null)

                const newHandoverState = {
                    ...handoverState,
                    handoverTime: 0,
                    status: 'idle' as const,
                }

                setHandoverState(newHandoverState)
                onHandoverStateChange?.(newHandoverState)
            }

            // 更新性能指標
            setMetrics((prev) => ({
                totalPredictions: prev.totalPredictions + 1,
                successfulHandovers:
                    prev.successfulHandovers + (Math.random() > 0.1 ? 1 : 0),
                failedHandovers:
                    prev.failedHandovers + (Math.random() < 0.1 ? 1 : 0),
                averageHandoverTime: 4.5 + Math.random() * 2,
                predictionAccuracy: 85 + Math.random() * 15,
                currentHandovers: Math.floor(Math.random() * 3),
            }))
        }

        generatePrediction()
        const interval = setInterval(generatePrediction, 8000)

        return () => clearInterval(interval)
    }, [isEnabled, satellites, handoverState.deltaT])

    // 手動換手處理
    const handleManualHandover = async (targetSatelliteId: string) => {
        const targetSatellite = satellites.find(
            (s) => s.norad_id === targetSatelliteId
        )
        if (!targetSatellite || !currentConnection) return

        setHandoverState((prev) => ({ ...prev, status: 'handover' }))
        setIsTransitioning(true)
        setTransitionProgress(0)
        onTransitionChange?.(true)

        // 模擬換手過程
        const handoverDuration = 3500 + Math.random() * 3000
        const startTime = Date.now()

        const progressInterval = setInterval(() => {
            const elapsed = Date.now() - startTime
            const progress = Math.min(elapsed / handoverDuration, 1)
            setTransitionProgress(progress)

            if (progress >= 1) {
                clearInterval(progressInterval)

                // 換手完成
                const newConnection: SatelliteConnection = {
                    satelliteId: targetSatelliteId,
                    satelliteName: targetSatellite.name,
                    isConnected: true,
                    isPredicted: false,
                    signalStrength:
                        -65 - (90 - targetSatellite.elevation_deg) * 0.5,
                    elevation: targetSatellite.elevation_deg,
                    azimuth: targetSatellite.azimuth_deg,
                    distance: targetSatellite.distance_km,
                    quality: { snr: 25, rssi: -65, bandwidth: 100 },
                    performance: { latency: 50, throughput: 150, jitter: 5 },
                }

                setCurrentConnection(newConnection)
                onCurrentConnectionChange?.(newConnection)

                const completedState = {
                    ...handoverState,
                    currentSatellite: targetSatelliteId,
                    status: 'complete' as const,
                }

                setHandoverState(completedState)
                onHandoverStateChange?.(completedState)

                setIsTransitioning(false)
                setTransitionProgress(0)
                onTransitionChange?.(false)

                // 發送換手事件
                if (onHandoverEvent) {
                    const handoverEvent: HandoverEvent = {
                        id: `handover_${Date.now()}`,
                        timestamp: Date.now(),
                        fromSatellite: currentConnection.satelliteId,
                        toSatellite: targetSatelliteId,
                        duration: handoverDuration,
                        success: true,
                        reason: 'manual',
                    }
                    onHandoverEvent(handoverEvent)
                }

                // 3秒後重置狀態
                setTimeout(() => {
                    setHandoverState((prev) => ({ ...prev, status: 'idle' }))
                }, 3000)
            }
        }, 100)
    }

    const handleCancelHandover = () => {
        setHandoverState((prev) => ({ ...prev, status: 'idle' }))
        setIsTransitioning(false)
        setTransitionProgress(0)
        onTransitionChange?.(false)
    }

    if (!isEnabled) {
        return (
            <div className="integrated-handover-panel disabled">
                <div className="disabled-message">
                    <h3>🔒 換手管理系統已停用</h3>
                    <p>請啟用換手相關功能來使用此面板</p>
                </div>
            </div>
        )
    }

    return (
        <div className="integrated-handover-panel">
            <div className="panel-header">
                <h2>🔄 LEO 衛星換手管理系統</h2>
                {selectedUEId && (
                    <div className="selected-ue">
                        <span>控制 UE: {selectedUEId}</span>
                    </div>
                )}
            </div>

            {/* 模式換手控制 */}
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

            {/* 標籤頁導航 */}
            <div className="tab-navigation">
                <button
                    className={`tab-button ${
                        activeTab === 'status' ? 'active' : ''
                    }`}
                    onClick={() => setActiveTab('status')}
                >
                    🔗 連接狀態
                </button>
                <button
                    className={`tab-button ${
                        activeTab === 'prediction' ? 'active' : ''
                    }`}
                    onClick={() => setActiveTab('prediction')}
                >
                    🔮 預測分析
                </button>
                <button
                    className={`tab-button ${
                        activeTab === 'performance' ? 'active' : ''
                    }`}
                    onClick={() => setActiveTab('performance')}
                >
                    📊 性能監控
                </button>
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

                {activeTab === 'prediction' && (
                    <div className="prediction-tab">
                        <TimePredictionTimeline data={timePredictionData} />

                        <div className="prediction-metrics">
                            <h4>🎯 預測精度分析</h4>
                            <div className="metrics-grid">
                                <div className="metric-card">
                                    <span className="metric-label">
                                        預測準確率
                                    </span>
                                    <span className="metric-value">
                                        {metrics.predictionAccuracy.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="metric-card">
                                    <span className="metric-label">
                                        預測總數
                                    </span>
                                    <span className="metric-value">
                                        {metrics.totalPredictions}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'performance' && (
                    <div className="performance-tab">
                        <h4>📈 換手性能統計</h4>
                        <div className="performance-metrics">
                            <div className="metric-row">
                                <span className="metric-label">成功換手</span>
                                <span className="metric-value success">
                                    {metrics.successfulHandovers}
                                </span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">失敗換手</span>
                                <span className="metric-value failed">
                                    {metrics.failedHandovers}
                                </span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">平均時間</span>
                                <span className="metric-value">
                                    {metrics.averageHandoverTime.toFixed(1)}s
                                </span>
                            </div>
                            <div className="metric-row">
                                <span className="metric-label">進行中</span>
                                <span className="metric-value handover">
                                    {metrics.currentHandovers}
                                </span>
                            </div>
                        </div>

                        <div className="performance-chart">
                            <h5>成功率趨勢</h5>
                            <div className="success-rate-bar">
                                <div
                                    className="success-fill"
                                    style={{
                                        width: `${
                                            (metrics.successfulHandovers /
                                                (metrics.successfulHandovers +
                                                    metrics.failedHandovers +
                                                    1)) *
                                            100
                                        }%`,
                                    }}
                                ></div>
                                <span className="success-rate-text">
                                    {(
                                        (metrics.successfulHandovers /
                                            (metrics.successfulHandovers +
                                                metrics.failedHandovers +
                                                1)) *
                                        100
                                    ).toFixed(1)}
                                    %
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default IntegratedHandoverPanel
