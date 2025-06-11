import React, { useState, useEffect, useRef, useMemo } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import { Text, Line, Sphere, Ring } from '@react-three/drei'
import { HandoverState, SatelliteConnection, HandoverEvent } from '../../../types/handover'

interface HandoverAnimation3DProps {
    devices: any[]
    enabled: boolean
    satellites?: any[]
    handoverState?: HandoverState
    currentConnection?: SatelliteConnection | null
    predictedConnection?: SatelliteConnection | null
    isTransitioning?: boolean
    transitionProgress?: number
    onHandoverEvent?: (event: HandoverEvent) => void
}

interface AnimationState {
    phase: 'idle' | 'preparing' | 'switching' | 'completing'
    progress: number
    fromSatellite?: string
    toSatellite?: string
    startTime: number
}

const HandoverAnimation3D: React.FC<HandoverAnimation3DProps> = ({
    devices,
    enabled,
    satellites = [],
    handoverState,
    currentConnection,
    predictedConnection,
    isTransitioning = false,
    transitionProgress = 0,
    onHandoverEvent
}) => {
    const { scene } = useThree()
    const [animationState, setAnimationState] = useState<AnimationState>({
        phase: 'idle',
        progress: 0,
        startTime: 0
    })
    const [satellitePositions, setSatellitePositions] = useState<Map<string, [number, number, number]>>(new Map())
    const [beamAnimations, setBeamAnimations] = useState<Map<string, number>>(new Map())
    const animationRef = useRef<{
        pulseTime: number
        beamRotation: number
        connectionPulse: number
    }>({
        pulseTime: 0,
        beamRotation: 0,
        connectionPulse: 0
    })

    // 更新動畫狀態基於換手狀態
    useEffect(() => {
        if (!enabled || !handoverState) return

        if (isTransitioning) {
            if (currentConnection && predictedConnection) {
                setAnimationState({
                    phase: 'switching',
                    progress: transitionProgress,
                    fromSatellite: currentConnection.satelliteId,
                    toSatellite: predictedConnection.satelliteId,
                    startTime: Date.now()
                })
            }
        } else if (handoverState.status === 'predicting' && predictedConnection) {
            setAnimationState({
                phase: 'preparing',
                progress: 0.5,
                fromSatellite: currentConnection?.satelliteId,
                toSatellite: predictedConnection.satelliteId,
                startTime: Date.now()
            })
        } else if (handoverState.status === 'complete') {
            setAnimationState({
                phase: 'completing',
                progress: 1.0,
                fromSatellite: undefined,
                toSatellite: currentConnection?.satelliteId,
                startTime: Date.now()
            })
            
            // 2秒後回到 idle 狀態
            setTimeout(() => {
                setAnimationState(prev => ({ ...prev, phase: 'idle' }))
            }, 2000)
        } else {
            setAnimationState({
                phase: 'idle',
                progress: 0,
                startTime: Date.now()
            })
        }
    }, [enabled, handoverState, isTransitioning, transitionProgress, currentConnection, predictedConnection])

    // 實時更新衛星位置
    useFrame((state, delta) => {
        const newPositions = new Map<string, [number, number, number]>()
        
        // 從場景中獲取衛星位置
        scene.traverse((child) => {
            if (child.type === 'Group' && child.userData?.satelliteId) {
                const satelliteId = child.userData.satelliteId
                const pos = child.position
                newPositions.set(satelliteId, [pos.x, pos.y, pos.z])
            }
            
            if (child.name && child.name.includes('satellite-')) {
                const nameMatch = child.name.match(/satellite-(.+)/)
                if (nameMatch) {
                    const satelliteId = nameMatch[1]
                    const pos = child.position
                    newPositions.set(satelliteId, [pos.x, pos.y, pos.z])
                }
            }
        })
        
        setSatellitePositions(newPositions)
        
        // 更新動畫時鐘
        animationRef.current.pulseTime += delta
        animationRef.current.beamRotation += delta * 0.5
        animationRef.current.connectionPulse += delta * 2
    })

    // 獲取衛星位置
    const getSatellitePosition = (satelliteId: string): [number, number, number] => {
        const realtimePos = satellitePositions.get(satelliteId)
        if (realtimePos) return realtimePos
        
        const satellite = satellites.find(sat => sat.id === satelliteId || sat.norad_id === satelliteId)
        if (satellite && satellite.position) return satellite.position
        
        return [0, 200, 0] // 預設位置
    }

    // 獲取 UAV 位置
    const getUAVPositions = (): Array<[number, number, number]> => {
        return devices
            .filter(d => d.role === 'receiver')
            .map(uav => [
                uav.position_x || 0,
                (uav.position_z || 0) + 10,
                uav.position_y || 0
            ])
    }

    if (!enabled) return null

    const uavPositions = getUAVPositions()
    
    return (
        <>
            {/* 換手狀態指示器 */}
            <HandoverStatusIndicator 
                animationState={animationState}
                handoverState={handoverState}
            />
            
            {/* 連接線動畫 */}
            <ConnectionLinesAnimation
                animationState={animationState}
                currentConnection={currentConnection}
                predictedConnection={predictedConnection}
                getSatellitePosition={getSatellitePosition}
                uavPositions={uavPositions}
                animationRef={animationRef}
            />
            
            {/* 衛星波束動畫 */}
            <SatelliteBeamAnimation
                animationState={animationState}
                currentConnection={currentConnection}
                predictedConnection={predictedConnection}
                getSatellitePosition={getSatellitePosition}
                animationRef={animationRef}
            />
            
            {/* 換手軌跡可視化 */}
            <HandoverTrajectoryVisualization
                animationState={animationState}
                currentConnection={currentConnection}
                predictedConnection={predictedConnection}
                getSatellitePosition={getSatellitePosition}
                uavPositions={uavPositions}
            />
            
            {/* 換手時間點標記 */}
            {handoverState?.handoverTime && (
                <HandoverTimingMarker
                    handoverTime={handoverState.handoverTime}
                    currentTime={Date.now()}
                    animationRef={animationRef}
                />
            )}
        </>
    )
}

// 換手狀態指示器
const HandoverStatusIndicator: React.FC<{
    animationState: AnimationState
    handoverState?: HandoverState
}> = ({ animationState, handoverState }) => {
    const getStatusColor = () => {
        switch (animationState.phase) {
            case 'preparing': return '#ffaa00'
            case 'switching': return '#ff6b35'
            case 'completing': return '#44ff44'
            default: return '#40e0ff'
        }
    }

    const getStatusText = () => {
        switch (animationState.phase) {
            case 'preparing': return '🔮 準備換手'
            case 'switching': return '🔄 執行換手'
            case 'completing': return '✅ 換手完成'
            default: return '📡 連接穩定'
        }
    }

    // 移除 3D 場景中的狀態文字顯示 - 改為在 UI 面板中顯示
    return null
}

// 連接線動畫
const ConnectionLinesAnimation: React.FC<{
    animationState: AnimationState
    currentConnection?: SatelliteConnection | null
    predictedConnection?: SatelliteConnection | null
    getSatellitePosition: (id: string) => [number, number, number]
    uavPositions: Array<[number, number, number]>
    animationRef: React.MutableRefObject<any>
}> = ({ 
    animationState, 
    currentConnection, 
    predictedConnection, 
    getSatellitePosition, 
    uavPositions,
    animationRef 
}) => {
    const getCurrentLineProps = () => {
        if (animationState.phase === 'switching') {
            const alpha = 1 - animationState.progress
            return {
                color: '#40e0ff',
                opacity: alpha * 0.8,
                lineWidth: 4,
                dashed: true
            }
        }
        return {
            color: '#40e0ff',
            opacity: 0.8,
            lineWidth: 4,
            dashed: false
        }
    }

    const getPredictedLineProps = () => {
        if (animationState.phase === 'switching') {
            const alpha = animationState.progress
            return {
                color: '#44ff44',
                opacity: alpha * 0.8,
                lineWidth: 4,
                dashed: false
            }
        } else if (animationState.phase === 'preparing') {
            const pulse = Math.sin(animationRef.current.connectionPulse) * 0.3 + 0.7
            return {
                color: '#ffaa00',
                opacity: pulse * 0.6,
                lineWidth: 3,
                dashed: true
            }
        }
        return {
            color: '#ffaa00',
            opacity: 0.4,
            lineWidth: 2,
            dashed: true
        }
    }

    return (
        <>
            {/* 當前連接線 */}
            {currentConnection && uavPositions.map((uavPos, index) => {
                const satPos = getSatellitePosition(currentConnection.satelliteId)
                const lineProps = getCurrentLineProps()
                
                return (
                    <Line
                        key={`current-${index}`}
                        points={[satPos, uavPos]}
                        {...lineProps}
                        transparent
                    />
                )
            })}
            
            {/* 預測連接線 */}
            {predictedConnection && animationState.phase !== 'idle' && uavPositions.map((uavPos, index) => {
                const satPos = getSatellitePosition(predictedConnection.satelliteId)
                const lineProps = getPredictedLineProps()
                
                return (
                    <Line
                        key={`predicted-${index}`}
                        points={[satPos, uavPos]}
                        {...lineProps}
                        transparent
                    />
                )
            })}
        </>
    )
}

// 衛星波束動畫
const SatelliteBeamAnimation: React.FC<{
    animationState: AnimationState
    currentConnection?: SatelliteConnection | null
    predictedConnection?: SatelliteConnection | null
    getSatellitePosition: (id: string) => [number, number, number]
    animationRef: React.MutableRefObject<any>
}> = ({ 
    animationState, 
    currentConnection, 
    predictedConnection, 
    getSatellitePosition,
    animationRef 
}) => {
    return (
        <>
            {/* 當前衛星波束 */}
            {currentConnection && (
                <SatelliteBeam
                    position={getSatellitePosition(currentConnection.satelliteId)}
                    color="#40e0ff"
                    intensity={animationState.phase === 'switching' ? 1 - animationState.progress : 1}
                    rotation={animationRef.current.beamRotation}
                />
            )}
            
            {/* 預測衛星波束 */}
            {predictedConnection && animationState.phase !== 'idle' && (
                <SatelliteBeam
                    position={getSatellitePosition(predictedConnection.satelliteId)}
                    color={animationState.phase === 'switching' ? '#44ff44' : '#ffaa00'}
                    intensity={animationState.phase === 'switching' ? animationState.progress : 0.6}
                    rotation={-animationRef.current.beamRotation}
                />
            )}
        </>
    )
}

// 衛星波束組件
const SatelliteBeam: React.FC<{
    position: [number, number, number]
    color: string
    intensity: number
    rotation: number
}> = ({ position, color, intensity, rotation }) => {
    return (
        <group position={position} rotation={[0, rotation, 0]}>
            <Ring
                args={[15, 25, 16]}
                position={[0, -5, 0]}
                rotation={[-Math.PI / 2, 0, 0]}
            >
                <meshBasicMaterial
                    color={color}
                    transparent
                    opacity={intensity * 0.3}
                    side={THREE.DoubleSide}
                />
            </Ring>
            
            <Ring
                args={[25, 35, 32]}
                position={[0, -10, 0]}
                rotation={[-Math.PI / 2, 0, 0]}
            >
                <meshBasicMaterial
                    color={color}
                    transparent
                    opacity={intensity * 0.2}
                    side={THREE.DoubleSide}
                />
            </Ring>
        </group>
    )
}

// 換手軌跡可視化
const HandoverTrajectoryVisualization: React.FC<{
    animationState: AnimationState
    currentConnection?: SatelliteConnection | null
    predictedConnection?: SatelliteConnection | null
    getSatellitePosition: (id: string) => [number, number, number]
    uavPositions: Array<[number, number, number]>
}> = ({ 
    animationState, 
    currentConnection, 
    predictedConnection, 
    getSatellitePosition, 
    uavPositions 
}) => {
    if (animationState.phase !== 'switching' || !currentConnection || !predictedConnection) {
        return null
    }

    const fromPos = getSatellitePosition(currentConnection.satelliteId)
    const toPos = getSatellitePosition(predictedConnection.satelliteId)
    
    // 創建弧形軌跡
    const midPoint: [number, number, number] = [
        (fromPos[0] + toPos[0]) / 2,
        Math.max(fromPos[1], toPos[1]) + 50,
        (fromPos[2] + toPos[2]) / 2
    ]
    
    const trajectoryPoints = [fromPos, midPoint, toPos]
    
    return (
        <>
            {/* 換手軌跡線 */}
            <Line
                points={trajectoryPoints}
                color="#ff6b35"
                lineWidth={6}
                transparent
                opacity={0.8}
                dashed
            />
            
            {/* 移動的數據包動畫 */}
            <MovingDataPacket
                trajectoryPoints={trajectoryPoints}
                progress={animationState.progress}
            />
        </>
    )
}

// 移動數據包動畫
const MovingDataPacket: React.FC<{
    trajectoryPoints: Array<[number, number, number]>
    progress: number
}> = ({ trajectoryPoints, progress }) => {
    const position = useMemo(() => {
        if (trajectoryPoints.length < 3) return [0, 0, 0]
        
        // 三次貝塞爾曲線插值
        const t = progress
        const [p0, p1, p2] = trajectoryPoints
        
        const x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        const y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        const z = (1 - t) ** 2 * p0[2] + 2 * (1 - t) * t * p1[2] + t ** 2 * p2[2]
        
        return [x, y, z] as [number, number, number]
    }, [trajectoryPoints, progress])

    return (
        <group position={position}>
            <Sphere args={[3]}>
                <meshBasicMaterial color="#ffffff" />
            </Sphere>
            
            <Text
                position={[0, 8, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                📦 數據
            </Text>
        </group>
    )
}

// 換手時間點標記
const HandoverTimingMarker: React.FC<{
    handoverTime: number
    currentTime: number
    animationRef: React.MutableRefObject<any>
}> = ({ handoverTime, currentTime, animationRef }) => {
    const timeUntilHandover = (handoverTime - currentTime) / 1000
    
    if (timeUntilHandover < 0) return null
    
    const pulse = Math.sin(animationRef.current.pulseTime * 3) * 0.3 + 0.7
    
    return (
        <group position={[0, 150, 0]}>
            <Text
                position={[0, 0, 0]}
                fontSize={6}
                color="#ff6b35"
                anchorX="center"
                anchorY="middle"
            >
                ⏰ 換手倒數: {timeUntilHandover.toFixed(1)}s
            </Text>
            
            <Ring
                args={[20, 25, 32]}
                rotation={[-Math.PI / 2, 0, 0]}
            >
                <meshBasicMaterial
                    color="#ff6b35"
                    transparent
                    opacity={pulse * 0.6}
                    side={THREE.DoubleSide}
                />
            </Ring>
        </group>
    )
}

export default HandoverAnimation3D