import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Line } from '@react-three/drei'

interface UAVSwarmCoordinationProps {
    devices: unknown[]
    enabled: boolean
}

interface SwarmFormation {
    id: string
    name: string
    type: 'line' | 'v_shape' | 'circle' | 'grid' | 'diamond'
    leader: string | number
    members: (string | number)[]
    status: 'forming' | 'formed' | 'moving' | 'maintaining' | 'dispersing'
    quality: number // 0-100
    targetPositions: { [key: string]: [number, number, number] }
    color: string
}

interface CoordinationTask {
    id: string
    type:
        | 'area_coverage'
        | 'formation_flight'
        | 'search_rescue'
        | 'communication_relay'
        | 'surveillance'
    priority: 'low' | 'medium' | 'high' | 'critical'
    progress: number
    assignedSwarms: string[]
    description: string
}

const UAVSwarmCoordination: React.FC<UAVSwarmCoordinationProps> = ({
    devices,
    enabled,
}) => {
    const [swarmFormations, setSwarmFormations] = useState<SwarmFormation[]>([])
    const [coordinationTasks, setCoordinationTasks] = useState<
        CoordinationTask[]
    >([])
    const [swarmMetrics, setSwarmMetrics] = useState({
        totalUAVs: 0,
        activeSwarms: 0,
        formationCompliance: 0,
        communicationQuality: 0,
        coordinationEfficiency: 0,
    })

    // 分析和創建群集編隊
    useEffect(() => {
        if (!enabled) {
            setSwarmFormations([])
            setCoordinationTasks([])
            return
        }

        const analyzeSwarmsAndFormations = () => {
            const receivers = devices.filter((d) => d.role === 'receiver')
            if (receivers.length < 2) return

            const formations = createSwarmFormations(receivers)
            setSwarmFormations(formations)

            const tasks = generateCoordinationTasks(formations)
            setCoordinationTasks(tasks)

            // 更新群集指標
            const metrics = calculateSwarmMetrics(formations, receivers)
            setSwarmMetrics(metrics)
        }

        analyzeSwarmsAndFormations()
        const interval = setInterval(analyzeSwarmsAndFormations, 5000) // 每5秒更新

        return () => clearInterval(interval)
    }, [devices, enabled])

    if (!enabled) return null

    return (
        <>
            {/* 群集編隊可視化 */}
            {swarmFormations.map((formation) => (
                <SwarmFormationVisualization
                    key={formation.id}
                    formation={formation}
                    devices={devices}
                />
            ))}

            {/* 群集連接線 */}
            <SwarmConnectionLines
                formations={swarmFormations}
                devices={devices}
            />

            {/* 群集狀態顯示 */}
            <SwarmStatusDisplay
                formations={swarmFormations}
                metrics={swarmMetrics}
            />

            {/* 協調任務顯示 */}
            <CoordinationTaskDisplay tasks={coordinationTasks} />

            {/* 編隊路徑預測 */}
            <FormationTrajectoryPrediction
                formations={swarmFormations}
                devices={devices}
            />
        </>
    )
}

// 創建群集編隊
const createSwarmFormations = (receivers: unknown[]): SwarmFormation[] => {
    const formations: SwarmFormation[] = []

    if (receivers.length >= 3) {
        // 主要編隊 - V字形
        const leaderId = receivers[0].id
        const memberIds = receivers
            .slice(0, Math.min(5, receivers.length))
            .map((r) => r.id)

        formations.push({
            id: 'primary_v_formation',
            name: '主編隊 Alpha',
            type: 'v_shape',
            leader: leaderId,
            members: memberIds,
            status: 'formed',
            quality: 85 + Math.random() * 10,
            targetPositions: calculateVFormationPositions(
                receivers.slice(0, memberIds.length)
            ),
            color: '#00ff88',
        })
    }

    if (receivers.length >= 6) {
        // 支援編隊 - 圓形
        const supportMembers = receivers.slice(5).map((r) => r.id)
        formations.push({
            id: 'support_circle_formation',
            name: '支援編隊 Beta',
            type: 'circle',
            leader: supportMembers[0],
            members: supportMembers,
            status: 'maintaining',
            quality: 75 + Math.random() * 15,
            targetPositions: calculateCircleFormationPositions(
                receivers.slice(5)
            ),
            color: '#ff8800',
        })
    }

    return formations
}

// V字形編隊位置計算
const calculateVFormationPositions = (
    uavs: unknown[]
): { [key: string]: [number, number, number] } => {
    const positions: { [key: string]: [number, number, number] } = {}
    const leadPosition = uavs[0]
        ? [
              uavs[0].position_x || 0,
              uavs[0].position_z || 0,
              uavs[0].position_y || 0,
          ]
        : [0, 0, 0]

    uavs.forEach((uav, index) => {
        if (index === 0) {
            // 領導位置
            positions[uav.id] = leadPosition as [number, number, number]
        } else {
            // V字形位置計算
            const side = index % 2 === 1 ? -1 : 1
            const depth = Math.floor((index + 1) / 2)
            positions[uav.id] = [
                leadPosition[0] + side * depth * 30,
                leadPosition[1],
                leadPosition[2] - depth * 25,
            ]
        }
    })

    return positions
}

// 圓形編隊位置計算
const calculateCircleFormationPositions = (
    uavs: unknown[]
): { [key: string]: [number, number, number] } => {
    const positions: { [key: string]: [number, number, number] } = {}
    const centerX =
        uavs.reduce((sum, uav) => sum + (uav.position_x || 0), 0) / uavs.length
    const centerY =
        uavs.reduce((sum, uav) => sum + (uav.position_y || 0), 0) / uavs.length
    const centerZ =
        uavs.reduce((sum, uav) => sum + (uav.position_z || 0), 0) / uavs.length
    const radius = 40

    uavs.forEach((uav, index) => {
        const angle = (index / uavs.length) * Math.PI * 2
        positions[uav.id] = [
            centerX + Math.cos(angle) * radius,
            centerZ,
            centerY + Math.sin(angle) * radius,
        ]
    })

    return positions
}

// 生成協調任務
const generateCoordinationTasks = (
    formations: SwarmFormation[]
): CoordinationTask[] => {
    return [
        {
            id: 'area_coverage_task',
            type: 'area_coverage',
            priority: 'high',
            progress: 65 + Math.random() * 20,
            assignedSwarms: formations.map((f) => f.id),
            description: '區域覆蓋巡邏任務',
        },
        {
            id: 'communication_relay_task',
            type: 'communication_relay',
            priority: 'medium',
            progress: 80 + Math.random() * 15,
            assignedSwarms: formations.slice(0, 1).map((f) => f.id),
            description: '通訊中繼維護任務',
        },
    ]
}

// 計算群集指標
const calculateSwarmMetrics = (
    formations: SwarmFormation[],
    allUAVs: unknown[]
) => {
    const totalUAVs = allUAVs.length
    const activeSwarms = formations.length
    const avgQuality =
        formations.reduce((sum, f) => sum + f.quality, 0) /
        (formations.length || 1)

    return {
        totalUAVs,
        activeSwarms,
        formationCompliance: avgQuality,
        communicationQuality: 88 + Math.random() * 10,
        coordinationEfficiency: 82 + Math.random() * 12,
    }
}

// 群集編隊可視化組件

const SwarmFormationVisualization: React.FC<{
    formation: SwarmFormation
    devices: unknown[]
}> = ({ formation, devices }) => {
    const meshRef = useRef<THREE.Group>(null)

    const getFormationColor = (status: string) => {
        switch (status) {
            case 'formed':
                return '#00ff88'
            case 'forming':
                return '#ffaa00'
            case 'moving':
                return '#00aaff'
            case 'maintaining':
                return '#88ff00'
            case 'dispersing':
                return '#ff6600'
            default:
                return '#ffffff'
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const getFormationIcon = (type: string) => {
        switch (type) {
            case 'line':
                return '➡️'
            case 'v_shape':
                return '✈️'
            case 'circle':
                return '⭕'
            case 'grid':
                return '⬜'
            case 'diamond':
                return '💎'
            default:
                return '🚁'
        }
    }

    useFrame((state) => {
        if (meshRef.current) {
            const time = state.clock.getElapsedTime()
            meshRef.current.rotation.y = time * 0.5

            const scale = 1 + Math.sin(time * 2) * 0.1
            meshRef.current.scale.setScalar(scale)
        }
    })

    // 找到領導設備

    const leaderDevice = devices.find((d) => d.id === formation.leader)
    if (!leaderDevice) return null

    return (
        <group
            ref={meshRef}
            position={[
                leaderDevice.position_x || 0,
                (leaderDevice.position_z || 0) + 60,
                leaderDevice.position_y || 0,
            ]}
        >
            {/* 編隊指示器 */}
            <mesh>
                <sphereGeometry args={[12, 16, 16]} />
                <meshStandardMaterial
                    color={getFormationColor(formation.status)}
                    transparent
                    opacity={0.6}
                    emissive={getFormationColor(formation.status)}
                    emissiveIntensity={0.3}
                />
            </mesh>

            {/* 編隊標籤 */}
        </group>
    )
}

// 群集連接線組件
const SwarmConnectionLines: React.FC<{
    formations: SwarmFormation[]
    devices: unknown[]
}> = ({ formations, devices }) => {
    return (
        <>
            {formations.map((formation) => {
                const leaderDevice = devices.find(
                    (d) => d.id === formation.leader
                )
                if (!leaderDevice) return null

                return formation.members.map((memberId) => {
                    const memberDevice = devices.find((d) => d.id === memberId)
                    if (!memberDevice || memberId === formation.leader)
                        return null

                    const points = [
                        [
                            leaderDevice.position_x || 0,
                            (leaderDevice.position_z || 0) + 15,
                            leaderDevice.position_y || 0,
                        ],
                        [
                            memberDevice.position_x || 0,
                            (memberDevice.position_z || 0) + 15,
                            memberDevice.position_y || 0,
                        ],
                    ]

                    return (
                        <Line
                            key={`${formation.id}_${memberId}`}
                            points={points}
                            color={formation.color}
                            lineWidth={2}
                            dashed={formation.status === 'forming'}
                        />
                    )
                })
            })}
        </>
    )
}

// 群集狀態顯示組件

const SwarmStatusDisplay: React.FC<{
    formations: SwarmFormation[]
    metrics: Record<string, unknown>
}> = ({ formations: _formations, metrics: _metrics }) => {
    // 移除所有文字顯示，返回 null
    console.log(
        'SwarmStatus data available:',
        _formations.length,
        Object.keys(_metrics).length
    )
    return null
}

// 協調任務顯示組件

const CoordinationTaskDisplay: React.FC<{
    tasks: CoordinationTask[]
}> = ({ tasks: _tasks }) => {
    // TODO: Use tasks for task visualization in future versions
    console.log('Coordination tasks available:', _tasks.length)

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const getTaskIcon = (type: string) => {
        switch (type) {
            case 'area_coverage':
                return '🗺️'
            case 'formation_flight':
                return '✈️'
            case 'search_rescue':
                return '🔍'
            case 'communication_relay':
                return '📡'
            case 'surveillance':
                return '👁️'
            default:
                return '📋'
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'low':
                return '#88ff88'
            case 'medium':
                return '#ffaa00'
            case 'high':
                return '#ff6600'
            case 'critical':
                return '#ff0000'
            default:
                return '#ffffff'
        }
    }

    // 移除所有文字顯示，返回 null
    return null
}

// 編隊軌跡預測組件
const FormationTrajectoryPrediction: React.FC<{
    formations: SwarmFormation[]
    devices: unknown[]
}> = ({ formations, devices }) => {
    return (
        <>
            {formations.map((formation) => {
                const leaderDevice = devices.find(
                    (d) => d.id === formation.leader
                )
                if (!leaderDevice) return null

                // 預測未來5個位置點
                const futurePoints = []
                for (let i = 1; i <= 5; i++) {
                    futurePoints.push([
                        (leaderDevice.position_x || 0) +
                            Math.sin(Date.now() / 1000 + i) * 20,
                        (leaderDevice.position_z || 0) + 5,
                        (leaderDevice.position_y || 0) + i * 15,
                    ])
                }

                return (
                    <group key={`trajectory_${formation.id}`}>
                        <Line
                            points={futurePoints}
                            color={formation.color}
                            lineWidth={1}
                            dashed={true}
                            transparent
                            opacity={0.6}
                        />

                        {/* 預測點標記 */}
                        {futurePoints.map((point, index) => (
                            <mesh
                                key={index}
                                position={point as [number, number, number]}
                            >
                                <sphereGeometry args={[2, 8, 8]} />
                                <meshBasicMaterial
                                    color={formation.color}
                                    transparent
                                    opacity={0.4}
                                />
                            </mesh>
                        ))}
                    </group>
                )
            })}
        </>
    )
}

export default UAVSwarmCoordination
