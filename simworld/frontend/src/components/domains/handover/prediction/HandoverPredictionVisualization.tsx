import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'

interface Device {
    id: string | number
    position_x?: number
    position_y?: number
    position_z?: number
    x?: number
    y?: number
    z?: number
    role?: string
}

interface Satellite {
    id: string | number
    name?: string
    position?: { x: number; y: number; z: number }
    [key: string]: unknown
}

interface HandoverPredictionVisualizationProps {
    devices: Device[]
    enabled: boolean
    satellites?: Satellite[]
    onPredictionsUpdate?: (predictions: HandoverPrediction[]) => void
}

interface HandoverPrediction {
    id: string
    uavId: string | number
    currentSatelliteId: string
    targetSatelliteId: string
    predictedTime: number
    confidence: 'high' | 'medium' | 'low'
    reason:
        | 'signal_degradation'
        | 'satellite_elevation'
        | 'orbital_transition'
        | 'load_balancing'
    executionStatus:
        | 'pending'
        | 'preparing'
        | 'executing'
        | 'completed'
        | 'failed'
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

         
         
const HandoverPredictionVisualization: React.FC<
    HandoverPredictionVisualizationProps
> = ({
    devices,
    enabled,
     
    satellites: _satellites = [],
    onPredictionsUpdate,
}) => {
    const [predictions, setPredictions] = useState<HandoverPrediction[]>([])
    const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([])
     
     
    const [metrics, setMetrics] = useState<HandoverMetrics>({
        totalPredictions: 0,
        successfulHandovers: 0,
        failedHandovers: 0,
        averageHandoverTime: 0,
        predictionAccuracy: 0,
        currentHandovers: 0,
    })
    // const [isLoading, setIsLoading] = useState(false)
    // const [error, setError] = useState<string | null>(null)

    // 移除真實衛星數據依賴 - 使用模擬數據

    // 使用模擬數據進行換手預測 - 與3D視覺化分離
    useEffect(() => {
        if (!enabled) {
            setPredictions([])
            setHandoverEvents([])
            //setError(null)
            return
        }

        const generateMockPredictions = async () => {
            //setIsLoading(true)
            //setError(null)

            try {
                 
                 
                const uavs = devices.filter((d) => d.role === 'receiver')

                if (uavs.length === 0) {
                    console.warn('No UAVs available for handover prediction')
                    //setIsLoading(false)
                    return
                }

                const newPredictions: HandoverPrediction[] = []
                const newEvents: HandoverEvent[] = []

                // 🎲 模擬衛星數據 - 使用與DynamicSatelliteRenderer一致的ID系統
                const mockSatellites = Array.from({ length: 18 }, (_, i) => ({
                    id: `sat_${i}`,
                    name: `STARLINK-${1000 + i}`,
                    norad_id: `sat_${i}`,
                    elevation_deg: 30 + Math.random() * 60,
                    azimuth_deg: Math.random() * 360,
                    distance_km: 500 + Math.random() * 500,
                }))

                // 為每個 UAV 生成模擬換手預測
                for (const uav of uavs) {
                    // 隨機選擇當前和目標衛星
                    const currentSatellite =
                        mockSatellites[Math.floor(Math.random() * 6)] // 前6個衛星
                    const targetSatellite =
                        mockSatellites[Math.floor(Math.random() * 6) + 6] // 後6個衛星

                    // 隨機決定是否需要換手 (60%機率)
                    if (Math.random() < 0.6) {
                        const timeToHandover = 5 + Math.random() * 25 // 5-30秒
                        const confidence = Math.random()

                        newPredictions.push({
                            id: `prediction_${
                                uav.id
                            }_${Date.now()}_${Math.random()}`,
                            uavId: uav.id,
                            currentSatelliteId: currentSatellite.id,
                            targetSatelliteId: targetSatellite.id,
                            predictedTime: Date.now() / 1000 + timeToHandover,
                            confidence:
                                confidence > 0.8
                                    ? 'high'
                                    : confidence > 0.6
                                    ? 'medium'
                                    : 'low',
                            reason: [
                                'signal_degradation',
                                'satellite_elevation',
                                'orbital_transition',
                                'load_balancing',
                            ][
                                Math.floor(Math.random() * 4)
                            ] as HandoverPrediction['reason'],
                            executionStatus: 'pending',
                            timeToHandover: timeToHandover,
                            signalStrength: {
                                current: -60 - Math.random() * 20, // -60 to -80 dBm
                                predicted: -55 - Math.random() * 15, // -55 to -70 dBm
                                threshold: -75,
                            },
                            elevation: {
                                current: currentSatellite.elevation_deg,
                                predicted: targetSatellite.elevation_deg,
                                threshold: 15,
                            },
                        })
                    }
                }

                setPredictions(newPredictions)
                setHandoverEvents(newEvents)

                // 更新指標
                setMetrics((prev) => ({
                    ...prev,
                    totalPredictions:
                        prev.totalPredictions + newPredictions.length,
                    predictionAccuracy: 85 + Math.random() * 10, // 85-95%
                    currentHandovers: newPredictions.filter(
                        (p) => p.executionStatus === 'executing'
                    ).length,
                    successfulHandovers:
                        prev.successfulHandovers +
                        Math.floor(Math.random() * 2),
                    failedHandovers:
                        prev.failedHandovers + (Math.random() < 0.1 ? 1 : 0),
                    averageHandoverTime: 3.5 + Math.random() * 2, // 3.5-5.5秒
                }))

                // 通知父組件
                onPredictionsUpdate?.(newPredictions)
            } catch (error) {
                console.error('❌ 模擬換手預測失敗:', error)
                // setError(
                //     error instanceof Error
                //         ? error.message
                //         : 'Mock prediction error'
                // )
            } finally {
                //setIsLoading(false)
            }
        }

        generateMockPredictions()

        // 設置定期更新（每20秒更新一次模擬預測）
        const interval = setInterval(() => {
            generateMockPredictions()
        }, 20000)

        return () => clearInterval(interval)
    }, [enabled, devices, onPredictionsUpdate])

    if (!enabled) return null

    return (
        <>
            {/* 換手預測可視化 */}
            <HandoverPredictionDisplay
                predictions={predictions}
                devices={devices}
            />

            {/* 換手時間軸 */}
            <HandoverTimelineVisualization predictions={predictions} />

            {/* 3D 換手動畫 */}
            <HandoverAnimationDisplay
                events={handoverEvents}
                devices={devices}
            />

            {/* 預測信心度指示器 */}
            <PredictionConfidenceIndicator predictions={predictions} />

            {/* 換手統計面板 */}
            <HandoverMetricsPanel metrics={metrics} />

            {/* 候選衛星顯示 */}
            <CandidateSatelliteDisplay
                predictions={predictions}
                devices={devices}
            />
        </>
    )
}

// 決定換手原因（暫時不使用）
// const determineHandoverReason = (
//     signal: number,
//     elevation: number
// ): HandoverPrediction['reason'] => {
//     if (signal < -80) return 'signal_degradation'
//     if (elevation < 15) return 'satellite_elevation'
//     if (Math.random() < 0.3) return 'load_balancing'
//     return 'orbital_transition'
// }

// 換手預測顯示組件
         
         
const HandoverPredictionDisplay: React.FC<{
    predictions: HandoverPrediction[]
    devices: Device[]
}> = ({ predictions, devices }) => {
         
         
    const getConfidenceColor = (confidence: string) => {
        switch (confidence) {
            case 'high':
                return '#00ff00'
            case 'medium':
                return '#ffaa00'
            case 'low':
                return '#ff6600'
            default:
                return '#ffffff'
        }
    }

         
         
    const getReasonIcon = (reason: string) => {
        switch (reason) {
            case 'signal_degradation':
                return '📶'
            case 'satellite_elevation':
                return '📐'
            case 'orbital_transition':
                return '🛰️'
            case 'load_balancing':
                return '⚖️'
            default:
                return '🔄'
        }
    }

    return (
        <>
            {predictions.map((prediction) => {
                 
                 
                const uav = devices.find((d) => d.id === prediction.uavId)
                if (!uav) return null

                return (
                    <group
                        key={prediction.id}
                        position={[
                            uav.position_x || 0,
                            (uav.position_z || 0) + 50,
                            uav.position_y || 0,
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
                            {prediction.currentSatelliteId} →{' '}
                            {prediction.targetSatelliteId}
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
}> = ({ predictions }) => {
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
    devices: Device[]
}> = ({ events, devices }) => {
    return (
        <>
            {events
                .filter((e) => e.status === 'in_progress')
                .map((event) => {
                     
                     
                    const uav = devices.find((d) => d.id === event.uavId)
                    if (!uav) return null

                    return (
                        <group
                            key={event.id}
                            position={[
                                uav.position_x || 0,
                                (uav.position_z || 0) + 60,
                                uav.position_y || 0,
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
}> = ({ predictions }) => {
    const highConfidence = predictions.filter(
        (p) => p.confidence === 'high'
    ).length
    const mediumConfidence = predictions.filter(
        (p) => p.confidence === 'medium'
    ).length
    const lowConfidence = predictions.filter(
        (p) => p.confidence === 'low'
    ).length

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
 
 
const HandoverMetricsPanel: React.FC<{ metrics: HandoverMetrics }> = ({
    metrics,
}) => {
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
    devices: Device[]
}> = ({ predictions, devices }) => {
    return (
        <>
            {predictions.map((prediction) => {
                 
                 
                const uav = devices.find((d) => d.id === prediction.uavId)
                if (!uav) return null

                return (
                    <group
                        key={`candidate_${prediction.id}`}
                        position={[
                            uav.position_x || 0,
                            (uav.position_z || 0) + 35,
                            uav.position_y || 0,
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
                            信號:{' '}
                            {prediction.signalStrength.predicted.toFixed(1)} dBm
                        </Text>
                    </group>
                )
            })}
        </>
    )
}

export default HandoverPredictionVisualization
