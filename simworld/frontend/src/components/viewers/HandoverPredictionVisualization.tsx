import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text, Line } from '@react-three/drei'
import { netStackApi } from '../../services/netstack-api'
import { simWorldApi, useVisibleSatellites } from '../../services/simworld-api'

interface HandoverPredictionVisualizationProps {
    devices: any[]
    enabled: boolean
    satellites?: any[]
    onPredictionsUpdate?: (predictions: HandoverPrediction[]) => void
}

interface HandoverPrediction {
    id: string
    uavId: string | number
    currentSatelliteId: string
    targetSatelliteId: string
    predictedTime: number
    confidence: 'high' | 'medium' | 'low'
    reason: 'signal_degradation' | 'satellite_elevation' | 'orbital_transition' | 'load_balancing'
    executionStatus: 'pending' | 'preparing' | 'executing' | 'completed' | 'failed'
    timeToHandover: number // seconds
    signalStrength: {
        current: number
        predicted: number
        threshold: number
    }
    elevation: {
        current: number
        predicted: number
        threshold: number
    }
}

interface HandoverEvent {
    id: string
    uavId: string | number
    fromSatellite: string
    toSatellite: string
    startTime: number
    endTime: number
    status: 'success' | 'failed' | 'in_progress'
    duration: number
    type: 'soft' | 'hard' | 'make_before_break'
}

interface HandoverMetrics {
    totalPredictions: number
    successfulHandovers: number
    failedHandovers: number
    averageHandoverTime: number
    predictionAccuracy: number
    currentHandovers: number
}

const HandoverPredictionVisualization: React.FC<HandoverPredictionVisualizationProps> = ({ 
    devices, 
    enabled, 
    satellites = [],
    onPredictionsUpdate
}) => {
    const [predictions, setPredictions] = useState<HandoverPrediction[]>([])
    const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([])
    const [metrics, setMetrics] = useState<HandoverMetrics>({
        totalPredictions: 0,
        successfulHandovers: 0,
        failedHandovers: 0,
        averageHandoverTime: 0,
        predictionAccuracy: 0,
        currentHandovers: 0
    })
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // 使用真實衛星數據
    const { 
        satellites: realSatellites, 
        loading: satellitesLoading, 
        error: satellitesError 
    } = useVisibleSatellites(10, 20, 30000)

    // 使用真實 API 進行換手預測
    useEffect(() => {
        if (!enabled) {
            setPredictions([])
            setHandoverEvents([])
            setError(null)
            return
        }

        const generateRealPredictions = async () => {
            setIsLoading(true)
            setError(null)

            try {
                const uavs = devices.filter(d => d.role === 'receiver')
                const availableSatellites = realSatellites.length > 0 ? realSatellites : satellites

                if (availableSatellites.length === 0) {
                    console.warn('No satellites available for handover prediction')
                    return
                }

                const newPredictions: HandoverPrediction[] = []
                const newEvents: HandoverEvent[] = []

                // 為每個 UAV 進行真實的換手預測
                for (const uav of uavs) {
                    try {
                        // 選擇當前衛星（第一顆可見衛星）
                        const currentSatellite = availableSatellites[0]
                        
                        // 準備候選衛星列表（其他可見衛星）
                        const candidateSatellites = availableSatellites
                            .slice(1, Math.min(5, availableSatellites.length)) // 最多4個候選
                            .map(sat => sat.satellite_id || sat.norad_id?.toString() || sat.id || 'unknown')
                            .filter(id => id !== 'unknown')

                        if (candidateSatellites.length === 0) {
                            console.warn(`No candidate satellites for UAV ${uav.id}`)
                            continue
                        }

                        // 🔥 調用真實的 NetStack 快速預測 API
                        const predictionRequest = {
                            ue_id: uav.id.toString(),
                            ue_lat: uav.x || 24.7854, // 使用 UAV 位置，或默認為台北
                            ue_lon: uav.y || 121.0005,
                            ue_alt: uav.z || 100,
                            current_satellite: currentSatellite.satellite_id || 
                                             currentSatellite.norad_id?.toString() || 
                                             'STARLINK-1',
                            candidate_satellites: candidateSatellites,
                            search_range_seconds: 300 // 5分鐘搜索範圍
                        }

                        console.log('🚀 調用真實 NetStack 快速預測 API:', predictionRequest)

                        const apiResult = await netStackApi.predictHandover(predictionRequest)
                        
                        console.log('✅ NetStack 快速預測 API 回應:', apiResult)

                        // 轉換 API 結果為組件格式
                        apiResult.predicted_handovers.forEach((handover, index) => {
                            const timeToHandover = handover.handover_time - Date.now() / 1000
                            
                            if (timeToHandover > 0) { // 只顯示未來的換手
                                newPredictions.push({
                                    id: `${apiResult.prediction_id}_${index}`,
                                    uavId: uav.id,
                                    currentSatelliteId: apiResult.current_satellite,
                                    targetSatelliteId: handover.target_satellite,
                                    predictedTime: handover.handover_time,
                                    confidence: handover.confidence_score > 0.8 ? 'high' : 
                                               handover.confidence_score > 0.6 ? 'medium' : 'low',
                                    reason: handover.reason,
                                    executionStatus: 'pending',
                                    timeToHandover: timeToHandover,
                                    signalStrength: {
                                        current: handover.signal_quality_prediction.current_snr,
                                        predicted: handover.signal_quality_prediction.predicted_snr,
                                        threshold: handover.signal_quality_prediction.signal_threshold
                                    },
                                    elevation: {
                                        current: handover.elevation_prediction.current_elevation,
                                        predicted: handover.elevation_prediction.predicted_elevation,
                                        threshold: handover.elevation_prediction.min_elevation_threshold
                                    }
                                })
                            }
                        })

                    } catch (error) {
                        console.error(`Failed to predict handover for UAV ${uav.id}:`, error)
                        // 繼續處理其他 UAV，不要因為一個失敗就停止全部
                    }
                }

                setPredictions(newPredictions)
                setHandoverEvents(newEvents)

                // 更新指標
                setMetrics(prev => ({
                    ...prev,
                    totalPredictions: prev.totalPredictions + newPredictions.length,
                    predictionAccuracy: apiResult?.algorithm_metadata?.prediction_accuracy || prev.predictionAccuracy,
                    currentHandovers: newPredictions.filter(p => p.executionStatus === 'executing').length
                }))

                // 通知父組件
                onPredictionsUpdate?.(newPredictions)

            } catch (error) {
                console.error('❌ 換手預測失敗:', error)
                setError(error instanceof Error ? error.message : 'Unknown error')
            } finally {
                setIsLoading(false)
            }
        }

        generateRealPredictions()

        // 設置定期更新（每30秒更新一次真實預測）
        const interval = setInterval(() => {
            generateRealPredictions()
        }, 30000)

        return () => clearInterval(interval)
    }, [devices, enabled, realSatellites, satellites])

    if (!enabled) return null

    return (
        <>
            {/* 真實數據狀態指示器 */}
            <div style={{ 
                position: 'absolute', 
                top: '10px', 
                right: '10px', 
                background: 'rgba(0, 0, 0, 0.8)', 
                padding: '8px 12px', 
                borderRadius: '6px',
                color: 'white',
                fontSize: '12px',
                zIndex: 1000
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ color: isLoading ? '#ffa500' : error ? '#ff4444' : '#44ff44' }}>
                        {isLoading ? '⏳' : error ? '❌' : '✅'}
                    </span>
                    <span>
                        {isLoading ? 'Loading predictions...' : 
                         error ? `Error: ${error}` : 
                         `${predictions.length} real predictions`}
                    </span>
                </div>
                {realSatellites.length > 0 && (
                    <div style={{ fontSize: '10px', color: '#aaa', marginTop: '4px' }}>
                        Using {realSatellites.length} real satellites from SimWorld
                    </div>
                )}
            </div>

            {/* 換手預測可視化 */}
            <HandoverPredictionDisplay predictions={predictions} devices={devices} />
            
            {/* 換手時間軸 */}
            <HandoverTimelineVisualization predictions={predictions} devices={devices} />
            
            {/* 3D 換手動畫 */}
            <HandoverAnimationDisplay events={handoverEvents} devices={devices} satellites={realSatellites.length > 0 ? realSatellites : satellites} />
            
            {/* 預測信心度指示器 */}
            <PredictionConfidenceIndicator predictions={predictions} devices={devices} />
            
            {/* 換手統計面板 */}
            <HandoverMetricsPanel metrics={metrics} />
            
            {/* 候選衛星顯示 */}
            <CandidateSatelliteDisplay predictions={predictions} devices={devices} />
        </>
    )
}

// 決定換手原因
const determineHandoverReason = (signal: number, elevation: number): HandoverPrediction['reason'] => {
    if (signal < -80) return 'signal_degradation'
    if (elevation < 15) return 'satellite_elevation'
    if (Math.random() < 0.3) return 'load_balancing'
    return 'orbital_transition'
}

// 換手預測顯示組件
const HandoverPredictionDisplay: React.FC<{
    predictions: HandoverPrediction[]
    devices: any[]
}> = ({ predictions, devices }) => {
    const getConfidenceColor = (confidence: string) => {
        switch (confidence) {
            case 'high': return '#00ff00'
            case 'medium': return '#ffaa00'
            case 'low': return '#ff6600'
            default: return '#ffffff'
        }
    }

    const getReasonIcon = (reason: string) => {
        switch (reason) {
            case 'signal_degradation': return '📶'
            case 'satellite_elevation': return '📐'
            case 'orbital_transition': return '🛰️'
            case 'load_balancing': return '⚖️'
            default: return '🔄'
        }
    }

    return (
        <>
            {predictions.map((prediction) => {
                const uav = devices.find(d => d.id === prediction.uavId)
                if (!uav) return null

                return (
                    <group
                        key={prediction.id}
                        position={[
                            uav.position_x || 0,
                            (uav.position_z || 0) + 50,
                            uav.position_y || 0
                        ]}
                    >
                        <Text
                            position={[0, 15, 0]}
                            fontSize={4}
                            color={getConfidenceColor(prediction.confidence)}
                            anchorX="center"
                            anchorY="middle"
                        >
                            {getReasonIcon(prediction.reason)} 換手預測
                        </Text>
                        
                        <Text
                            position={[0, 10, 0]}
                            fontSize={3}
                            color="#ffffff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            時間: {Math.ceil(prediction.timeToHandover)}s
                        </Text>
                        
                        <Text
                            position={[0, 6, 0]}
                            fontSize={2.5}
                            color={getConfidenceColor(prediction.confidence)}
                            anchorX="center"
                            anchorY="middle"
                        >
                            信心度: {prediction.confidence.toUpperCase()}
                        </Text>
                        
                        <Text
                            position={[0, 2, 0]}
                            fontSize={2}
                            color="#aaaaaa"
                            anchorX="center"
                            anchorY="middle"
                        >
                            {prediction.currentSatelliteId} → {prediction.targetSatelliteId}
                        </Text>
                    </group>
                )
            })}
        </>
    )
}

// 換手時間軸可視化組件
const HandoverTimelineVisualization: React.FC<{
    predictions: HandoverPrediction[]
    devices: any[]
}> = ({ predictions, devices }) => {
    const timelineRef = useRef<THREE.Group>(null)

    useFrame(() => {
        if (timelineRef.current) {
            // 輕微旋轉時間軸以增加視覺效果
            timelineRef.current.rotation.y += 0.001
        }
    })

    return (
        <group ref={timelineRef} position={[-100, 100, 0]}>
            <Text
                position={[0, 25, 0]}
                fontSize={6}
                color="#00aaff"
                anchorX="center"
                anchorY="middle"
            >
                ⏱️ 換手時間軸
            </Text>
            
            {predictions.slice(0, 5).map((prediction, index) => (
                <group key={prediction.id} position={[0, 18 - index * 8, 0]}>
                    <Text
                        position={[0, 3, 0]}
                        fontSize={3}
                        color="#ffffff"
                        anchorX="center"
                        anchorY="middle"
                    >
                        UAV-{prediction.uavId}
                    </Text>
                    
                    <Text
                        position={[0, 0, 0]}
                        fontSize={2.5}
                        color="#88ccff"
                        anchorX="center"
                        anchorY="middle"
                    >
                        T-{Math.ceil(prediction.timeToHandover)}s
                    </Text>
                    
                    <Text
                        position={[0, -3, 0]}
                        fontSize={2}
                        color="#cccccc"
                        anchorX="center"
                        anchorY="middle"
                    >
                        {prediction.targetSatelliteId}
                    </Text>
                </group>
            ))}
        </group>
    )
}

// 3D 換手動畫顯示組件
const HandoverAnimationDisplay: React.FC<{
    events: HandoverEvent[]
    devices: any[]
    satellites: any[]
}> = ({ events, devices, satellites }) => {
    return (
        <>
            {events.filter(e => e.status === 'in_progress').map((event) => {
                const uav = devices.find(d => d.id === event.uavId)
                if (!uav) return null

                return (
                    <group
                        key={event.id}
                        position={[
                            uav.position_x || 0,
                            (uav.position_z || 0) + 60,
                            uav.position_y || 0
                        ]}
                    >
                        {/* 旋轉的換手動畫環 */}
                        <mesh rotation={[0, 0, 0]}>
                            <torusGeometry args={[8, 2, 8, 16]} />
                            <meshBasicMaterial
                                color="#00ff88"
                                transparent
                                opacity={0.7}
                            />
                        </mesh>
                        
                        <Text
                            position={[0, 12, 0]}
                            fontSize={4}
                            color="#00ff88"
                            anchorX="center"
                            anchorY="middle"
                        >
                            🔄 執行換手
                        </Text>
                        
                        <Text
                            position={[0, 8, 0]}
                            fontSize={3}
                            color="#ffffff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            {event.type.toUpperCase()}
                        </Text>
                    </group>
                )
            })}
        </>
    )
}

// 預測信心度指示器組件
const PredictionConfidenceIndicator: React.FC<{
    predictions: HandoverPrediction[]
    devices: any[]
}> = ({ predictions, devices }) => {
    const highConfidence = predictions.filter(p => p.confidence === 'high').length
    const mediumConfidence = predictions.filter(p => p.confidence === 'medium').length
    const lowConfidence = predictions.filter(p => p.confidence === 'low').length

    return (
        <group position={[100, 100, 0]}>
            <Text
                position={[0, 25, 0]}
                fontSize={6}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
            >
                🎯 預測信心度
            </Text>
            
            <Text
                position={[0, 18, 0]}
                fontSize={4}
                color="#00ff00"
                anchorX="center"
                anchorY="middle"
            >
                高: {highConfidence}
            </Text>
            
            <Text
                position={[0, 13, 0]}
                fontSize={4}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
            >
                中: {mediumConfidence}
            </Text>
            
            <Text
                position={[0, 8, 0]}
                fontSize={4}
                color="#ff6600"
                anchorX="center"
                anchorY="middle"
            >
                低: {lowConfidence}
            </Text>
            
            <Text
                position={[0, 3, 0]}
                fontSize={3.5}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                總計: {predictions.length}
            </Text>
        </group>
    )
}

// 換手統計面板組件
const HandoverMetricsPanel: React.FC<{ metrics: HandoverMetrics }> = ({ metrics }) => {
    return (
        <group position={[0, 100, -100]}>
            <Text
                position={[0, 25, 0]}
                fontSize={6}
                color="#ff8800"
                anchorX="center"
                anchorY="middle"
            >
                📊 換手統計
            </Text>
            
            <Text
                position={[0, 18, 0]}
                fontSize={4}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                預測總數: {metrics.totalPredictions}
            </Text>
            
            <Text
                position={[0, 13, 0]}
                fontSize={4}
                color="#00ff88"
                anchorX="center"
                anchorY="middle"
            >
                成功: {metrics.successfulHandovers}
            </Text>
            
            <Text
                position={[0, 8, 0]}
                fontSize={4}
                color="#ff4444"
                anchorX="center"
                anchorY="middle"
            >
                失敗: {metrics.failedHandovers}
            </Text>
            
            <Text
                position={[0, 3, 0]}
                fontSize={3.5}
                color="#88ff88"
                anchorX="center"
                anchorY="middle"
            >
                平均時間: {metrics.averageHandoverTime.toFixed(1)}s
            </Text>
            
            <Text
                position={[0, -2, 0]}
                fontSize={3.5}
                color="#ffaa88"
                anchorX="center"
                anchorY="middle"
            >
                準確率: {metrics.predictionAccuracy.toFixed(1)}%
            </Text>
        </group>
    )
}

// 候選衛星顯示組件
const CandidateSatelliteDisplay: React.FC<{
    predictions: HandoverPrediction[]
    devices: any[]
}> = ({ predictions, devices }) => {
    return (
        <>
            {predictions.map((prediction) => {
                const uav = devices.find(d => d.id === prediction.uavId)
                if (!uav) return null

                return (
                    <group
                        key={`candidate_${prediction.id}`}
                        position={[
                            uav.position_x || 0,
                            (uav.position_z || 0) + 35,
                            uav.position_y || 0
                        ]}
                    >
                        <Text
                            position={[0, 6, 0]}
                            fontSize={3}
                            color="#00aaff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            🎯 候選衛星
                        </Text>
                        
                        <Text
                            position={[0, 2, 0]}
                            fontSize={2.5}
                            color="#ffffff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            {prediction.targetSatelliteId}
                        </Text>
                        
                        <Text
                            position={[0, -2, 0]}
                            fontSize={2}
                            color="#cccccc"
                            anchorX="center"
                            anchorY="middle"
                        >
                            信號: {prediction.signalStrength.predicted.toFixed(1)} dBm
                        </Text>
                    </group>
                )
            })}
        </>
    )
}

export default HandoverPredictionVisualization