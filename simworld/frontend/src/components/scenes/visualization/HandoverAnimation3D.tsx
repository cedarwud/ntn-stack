import React, { useState, useEffect, useRef, useMemo } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import { Text, Line, Sphere, Ring } from '@react-three/drei'
import {
    HandoverState,
    SatelliteConnection,
    HandoverEvent,
} from '../../../types/handover'

interface HandoverAnimation3DProps {
    devices: any[]
    enabled: boolean
    satellites?: any[]
    satellitePositions?: Map<string, [number, number, number]> // 🔗 新增：來自 DynamicSatelliteRenderer 的位置
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
    satellitePositions,
    handoverState,
    currentConnection,
    predictedConnection,
    isTransitioning = false,
    transitionProgress = 0,
    onHandoverEvent,
}) => {
    const { scene } = useThree()
    const [animationState, setAnimationState] = useState<AnimationState>({
        phase: 'idle',
        progress: 0,
        startTime: 0,
    })

    const [beamAnimations, setBeamAnimations] = useState<Map<string, number>>(
        new Map()
    )
    const animationRef = useRef<{
        pulseTime: number
        beamRotation: number
        connectionPulse: number
    }>({
        pulseTime: 0,
        beamRotation: 0,
        connectionPulse: 0,
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
                    startTime: Date.now(),
                })
            }
        } else if (
            handoverState.status === 'predicting' &&
            predictedConnection
        ) {
            setAnimationState({
                phase: 'preparing',
                progress: 0.5,
                fromSatellite: currentConnection?.satelliteId,
                toSatellite: predictedConnection.satelliteId,
                startTime: Date.now(),
            })
        } else if (handoverState.status === 'complete') {
            setAnimationState({
                phase: 'completing',
                progress: 1.0,
                fromSatellite: undefined,
                toSatellite: currentConnection?.satelliteId,
                startTime: Date.now(),
            })

            // 2秒後回到 idle 狀態
            setTimeout(() => {
                setAnimationState((prev) => ({ ...prev, phase: 'idle' }))
            }, 2000)
        } else {
            setAnimationState({
                phase: 'idle',
                progress: 0,
                startTime: Date.now(),
            })
        }
    }, [
        enabled,
        handoverState,
        isTransitioning,
        transitionProgress,
        currentConnection,
        predictedConnection,
    ])

    // 🔗 移除舊的 scene traversal 邏輯，現在直接從 DynamicSatelliteRenderer 獲取位置
    useFrame((state, delta) => {
        // 只更新動畫時鐘
        animationRef.current.pulseTime += delta
        animationRef.current.beamRotation += delta * 0.5
        animationRef.current.connectionPulse += delta * 2
    })

    // 🔗 獲取衛星位置 - 優先使用來自 DynamicSatelliteRenderer 的實時位置
    const getSatellitePosition = (
        satelliteId: string
    ): [number, number, number] => {
        // 優先使用實時位置
        if (satellitePositions) {
            const realtimePos = satellitePositions.get(satelliteId)
            if (realtimePos) return realtimePos

            // 嘗試通過名稱匹配
            for (const [key, position] of satellitePositions.entries()) {
                if (key.includes(satelliteId) || satelliteId.includes(key)) {
                    return position
                }
            }
        }

        // 備用：從 satellites 數組獲取（可能不準確）
        const satellite = satellites.find(
            (sat) => sat.id === satelliteId || sat.norad_id === satelliteId
        )
        if (satellite && satellite.position) return satellite.position

        // 🔧 調試信息：如果找不到衛星，返回預設位置但不在控制台顯示警告
        // 這是正常的，因為可能正在使用模擬數據或者衛星還未加載
        return [0, 200, 0] // 預設位置
    }

    // 獲取 UAV 位置
    const getUAVPositions = (): Array<[number, number, number]> => {
        return devices
            .filter((d) => d.role === 'receiver')
            .map((uav) => [
                uav.position_x || 0,
                (uav.position_z || 0) + 10,
                uav.position_y || 0,
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

// 🎯 目標衛星準備指示器 - 階段 1：準備換手時的光圈效果
const TargetSatelliteIndicator: React.FC<{
    position: [number, number, number]
    animationRef: React.MutableRefObject<any>
}> = ({ position, animationRef }) => {
    const pulse = Math.sin(animationRef.current.connectionPulse * 2) * 0.4 + 0.6

    return (
        <group position={position}>
            {/* 內圈光圈 */}
            <Ring args={[25, 35, 16]} rotation={[-Math.PI / 2, 0, 0]}>
                <meshBasicMaterial
                    color="#ffff00" // 黃色 = 準備狀態
                    transparent
                    opacity={pulse * 0.6}
                    side={THREE.DoubleSide}
                />
            </Ring>

            {/* 外圈光圈 */}
            <Ring args={[35, 45, 32]} rotation={[-Math.PI / 2, 0, 0]}>
                <meshBasicMaterial
                    color="#ffff00"
                    transparent
                    opacity={pulse * 0.3}
                    side={THREE.DoubleSide}
                />
            </Ring>

            {/* 準備狀態文字 */}
            <Text
                position={[0, 15, 0]}
                fontSize={4}
                color="#ffff00"
                anchorX="center"
                anchorY="middle"
            >
                🎯 即將連接
            </Text>
        </group>
    )
}

// 換手狀態指示器 - 提供詳細的階段資訊
const HandoverStatusIndicator: React.FC<{
    animationState: AnimationState
    handoverState?: HandoverState
}> = () => {
    // 移除 3D 場景中的狀態文字顯示 - 改為在 UI 面板中顯示
    // 狀態資訊將由 HandoverControlPanel 或 SatelliteConnectionIndicator 顯示
    return null
}

// 🚀 新連接線動畫系統 - 實現 handover.md 中的 5 階段換手視覺化
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
    animationRef,
}) => {
    // 🎯 換手階段時間定義 (45秒總週期)
    const getHandoverStage = (
        progress: number
    ): {
        stage:
            | 'stable'
            | 'preparing'
            | 'establishing'
            | 'switching'
            | 'completing'
        stageProgress: number
        description: string
    } => {
        const totalTime = 45 // 45秒總週期
        const currentTime = progress * totalTime

        if (currentTime <= 30) {
            return {
                stage: 'stable',
                stageProgress: currentTime / 30,
                description: '📡 連接穩定',
            }
        } else if (currentTime <= 35) {
            return {
                stage: 'preparing',
                stageProgress: (currentTime - 30) / 5,
                description: `🔄 準備換手 (倒數 ${Math.ceil(
                    35 - currentTime
                )} 秒)`,
            }
        } else if (currentTime <= 38) {
            return {
                stage: 'establishing',
                stageProgress: (currentTime - 35) / 3,
                description: '🔗 建立新連接',
            }
        } else if (currentTime <= 40) {
            return {
                stage: 'switching',
                stageProgress: (currentTime - 38) / 2,
                description: '⚡ 切換連接中',
            }
        } else {
            return {
                stage: 'completing',
                stageProgress: (currentTime - 40) / 5,
                description: '✅ 換手完成',
            }
        }
    }

    // 📊 根據換手階段計算連接線屬性
    const getCurrentLineProps = () => {
        if (!animationState || animationState.phase === 'idle') {
            // 穩定期：實線 + 正常亮度 = 穩定連接
            return {
                color: '#00ff88', // 綠色 = 穩定/成功
                opacity: 1.0,
                lineWidth: 4,
                dashed: false,
            }
        }

        const handoverStage = getHandoverStage(animationState.progress)

        switch (handoverStage.stage) {
            case 'stable':
                return {
                    color: '#00ff88', // 綠色 = 穩定
                    opacity: 1.0,
                    lineWidth: 4, // 標準粗細 = 正常狀態
                    dashed: false, // 實線 = 穩定連接
                }

            case 'preparing':
                // 準備階段：實線 + 閃爍 = 準備斷開
                const preparePulse =
                    Math.sin(animationRef.current.connectionPulse * 3) * 0.3 +
                    0.7
                return {
                    color: '#ffff00', // 黃色 = 準備/警告
                    opacity: preparePulse * 0.9,
                    lineWidth: 4,
                    dashed: false, // 實線但閃爍
                }

            case 'establishing':
            case 'switching':
                // 建立/切換階段：虛線 + 逐漸變淡 = 斷開中
                const switchAlpha = 1 - handoverStage.stageProgress
                return {
                    color: '#808080', // 灰色 = 斷開/非活躍
                    opacity: switchAlpha * 0.6,
                    lineWidth: 2, // 較細 = 非活躍連接
                    dashed: true, // 虛線 = 斷開中
                }

            case 'completing':
                // 完成階段：淡出
                const completeAlpha = 1 - handoverStage.stageProgress
                return {
                    color: '#808080',
                    opacity: completeAlpha * 0.3,
                    lineWidth: 1,
                    dashed: true,
                }

            default:
                return {
                    color: '#00ff88',
                    opacity: 1.0,
                    lineWidth: 4,
                    dashed: false,
                }
        }
    }

    const getPredictedLineProps = () => {
        if (
            !animationState ||
            animationState.phase === 'idle' ||
            !predictedConnection
        ) {
            return null // 穩定期不顯示預測線
        }

        const handoverStage = getHandoverStage(animationState.progress)

        switch (handoverStage.stage) {
            case 'preparing':
                // 準備階段：目標衛星光圈，不顯示連接線
                return null

            case 'establishing':
                // 建立階段：虛線 + 逐漸變實 = 建立中
                const establishAlpha = handoverStage.stageProgress
                return {
                    color: '#4080ff', // 藍色 = 建立中
                    opacity: establishAlpha * 0.8,
                    lineWidth: 3,
                    dashed: true, // 虛線逐漸變實
                }

            case 'switching':
                // 切換階段：實線 + 正常亮度 = 穩定連接 (Make-Before-Break)
                return {
                    color: '#4080ff',
                    opacity: 0.9,
                    lineWidth: 5, // 較粗 = 主要/活躍連接
                    dashed: false, // 實線 = 穩定連接
                }

            case 'completing':
                // 完成階段：新連接已建立
                return {
                    color: '#00ff88', // 綠色 = 成功建立
                    opacity: 1.0,
                    lineWidth: 4,
                    dashed: false,
                }

            default:
                return null
        }
    }

    return (
        <>
            {/* 🔗 當前連接線 - 舊連接逐漸斷開 */}
            {currentConnection &&
                uavPositions.map((uavPos, index) => {
                    const satPos = getSatellitePosition(
                        currentConnection.satelliteId
                    )
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

            {/* 🔗 預測連接線 - 新連接逐漸建立 */}
            {(() => {
                const predictedProps = getPredictedLineProps()
                if (!predictedProps || !predictedConnection) return null

                return uavPositions.map((uavPos, index) => {
                    const satPos = getSatellitePosition(
                        predictedConnection.satelliteId
                    )

                    return (
                        <Line
                            key={`predicted-${index}`}
                            points={[satPos, uavPos]}
                            {...predictedProps}
                            transparent
                        />
                    )
                })
            })()}

            {/* 🎯 目標衛星準備指示器 */}
            {predictedConnection && animationState?.phase === 'preparing' && (
                <TargetSatelliteIndicator
                    position={getSatellitePosition(
                        predictedConnection.satelliteId
                    )}
                    animationRef={animationRef}
                />
            )}
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
    animationRef,
}) => {
    return (
        <>
            {/* 當前衛星波束 */}
            {currentConnection && (
                <SatelliteBeam
                    position={getSatellitePosition(
                        currentConnection.satelliteId
                    )}
                    color="#40e0ff"
                    intensity={
                        animationState.phase === 'switching'
                            ? 1 - animationState.progress
                            : 1
                    }
                    rotation={animationRef.current.beamRotation}
                />
            )}

            {/* 預測衛星波束 */}
            {predictedConnection && animationState.phase !== 'idle' && (
                <SatelliteBeam
                    position={getSatellitePosition(
                        predictedConnection.satelliteId
                    )}
                    color={
                        animationState.phase === 'switching'
                            ? '#44ff44'
                            : '#ffaa00'
                    }
                    intensity={
                        animationState.phase === 'switching'
                            ? animationState.progress
                            : 0.6
                    }
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
    uavPositions,
}) => {
    if (
        animationState.phase !== 'switching' ||
        !currentConnection ||
        !predictedConnection
    ) {
        return null
    }

    const fromPos = getSatellitePosition(currentConnection.satelliteId)
    const toPos = getSatellitePosition(predictedConnection.satelliteId)

    // 創建弧形軌跡
    const midPoint: [number, number, number] = [
        (fromPos[0] + toPos[0]) / 2,
        Math.max(fromPos[1], toPos[1]) + 50,
        (fromPos[2] + toPos[2]) / 2,
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
    const position = useMemo((): [number, number, number] => {
        if (trajectoryPoints.length < 3) return [0, 0, 0]

        // 三次貝塞爾曲線插值
        const t = progress
        const [p0, p1, p2] = trajectoryPoints

        const x =
            (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        const y =
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        const z =
            (1 - t) ** 2 * p0[2] + 2 * (1 - t) * t * p1[2] + t ** 2 * p2[2]

        return [x, y, z]
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

            <Ring args={[20, 25, 32]} rotation={[-Math.PI / 2, 0, 0]}>
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
