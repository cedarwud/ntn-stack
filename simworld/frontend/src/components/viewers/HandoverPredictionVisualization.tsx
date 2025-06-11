import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text, Line } from '@react-three/drei'

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

    // 模擬換手預測數據
    useEffect(() => {
        if (!enabled) {
            setPredictions([])
            setHandoverEvents([])
            return
        }

        const generatePredictions = () => {
            const uavs = devices.filter(d => d.role === 'receiver')
            const availableSatellites = satellites.length > 0 ? satellites : [
                { id: 'sat_001', name: 'OneWeb-1234' },
                { id: 'sat_002', name: 'OneWeb-5678' },
                { id: 'sat_003', name: 'OneWeb-9012' }
            ]

            const newPredictions: HandoverPrediction[] = []
            const newEvents: HandoverEvent[] = []

            uavs.forEach((uav) => {
                // 30% 機率產生換手預測
                if (Math.random() < 0.3) {
                    const currentSat = availableSatellites[Math.floor(Math.random() * availableSatellites.length)]
                    const targetSat = availableSatellites.find(s => s.id !== currentSat.id) || availableSatellites[0]
                    
                    const timeToHandover = 5 + Math.random() * 25 // 5-30秒
                    const currentSignal = -65 + Math.random() * 20 - 10
                    const currentElevation = 15 + Math.random() * 60
                    
                    const prediction: HandoverPrediction = {
                        id: `pred_${uav.id}_${Date.now()}`,
                        uavId: uav.id,
                        currentSatelliteId: currentSat.id,
                        targetSatelliteId: targetSat.id,
                        predictedTime: Date.now() + timeToHandover * 1000,
                        confidence: timeToHandover > 20 ? 'high' : timeToHandover > 10 ? 'medium' : 'low',
                        reason: determineHandoverReason(currentSignal, currentElevation),
                        executionStatus: 'pending',
                        timeToHandover,
                        signalStrength: {
                            current: currentSignal,
                            predicted: currentSignal - 10 - Math.random() * 15,
                            threshold: -80
                        },
                        elevation: {
                            current: currentElevation,
                            predicted: Math.max(5, currentElevation - 15 - Math.random() * 20),
                            threshold: 10
                        }
                    }
                    
                    newPredictions.push(prediction)
                }

                // 15% 機率產生換手事件
                if (Math.random() < 0.15) {
                    const fromSat = availableSatellites[Math.floor(Math.random() * availableSatellites.length)]
                    const toSat = availableSatellites.find(s => s.id !== fromSat.id) || availableSatellites[0]
                    
                    const event: HandoverEvent = {
                        id: `event_${uav.id}_${Date.now()}`,
                        uavId: uav.id,
                        fromSatellite: fromSat.id,
                        toSatellite: toSat.id,
                        startTime: Date.now() - Math.random() * 10000,
                        endTime: Date.now() + Math.random() * 5000,
                        status: Math.random() > 0.1 ? 'success' : 'failed',
                        duration: 2000 + Math.random() * 3000,
                        type: Math.random() > 0.5 ? 'soft' : 'hard'
                    }
                    
                    newEvents.push(event)
                }
            })

            setPredictions(newPredictions)
            setHandoverEvents(prev => [...prev.slice(-10), ...newEvents])
            
            // 傳遞預測數據給父組件
            if (onPredictionsUpdate) {
                onPredictionsUpdate(newPredictions)
            }

            // 更新指標
            const totalPreds = newPredictions.length
            const successEvents = newEvents.filter(e => e.status === 'success').length
            const failedEvents = newEvents.filter(e => e.status === 'failed').length
            const avgTime = newEvents.reduce((sum, e) => sum + e.duration, 0) / (newEvents.length || 1) / 1000

            setMetrics(prev => ({
                totalPredictions: prev.totalPredictions + totalPreds,
                successfulHandovers: prev.successfulHandovers + successEvents,
                failedHandovers: prev.failedHandovers + failedEvents,
                averageHandoverTime: avgTime,
                predictionAccuracy: 85 + Math.random() * 15,
                currentHandovers: newEvents.filter(e => e.status === 'in_progress').length
            }))
        }

        generatePredictions()
        const interval = setInterval(generatePredictions, 8000)

        return () => clearInterval(interval)
    }, [devices, enabled, satellites])

    if (!enabled) return null

    return (
        <>
            {/* 換手預測可視化 */}
            <HandoverPredictionDisplay predictions={predictions} devices={devices} />
            
            {/* 換手時間軸 */}
            <HandoverTimelineVisualization predictions={predictions} devices={devices} />
            
            {/* 3D 換手動畫 */}
            <HandoverAnimationDisplay events={handoverEvents} devices={devices} satellites={satellites} />
            
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