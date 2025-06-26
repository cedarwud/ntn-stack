import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text, Line } from '@react-three/drei'

interface SatelliteHandoverDecisionVisualizationProps {
    devices: any[]
    enabled: boolean
    satellites?: any[]
}

interface HandoverDecision {
    id: string
    uavId: string | number
    currentSatellite: {
        id: string
        name: string
        position: [number, number, number]
        signalStrength: number
        elevation: number
        loadPercentage: number
    }
    candidateSatellites: Array<{
        id: string
        name: string
        position: [number, number, number]
        signalStrength: number
        elevation: number
        score: number
        distance: number
        loadPercentage: number
        isSelected: boolean
    }>
    decisionFactors: {
        signalQuality: number // 0-100
        elevation: number // 0-100
        loadBalancing: number // 0-100
        distance: number // 0-100
        interference: number // 0-100
    }
    finalScore: number
    decisionTime: number
    reason: string
}

interface HandoverPath {
    id: string
    uavId: string | number
    path: [number, number, number][]
    currentSatellitePos: [number, number, number]
    targetSatellitePos: [number, number, number]
    progress: number // 0-1
    type: 'signal_prediction' | 'path_planning' | 'execution'
}

const SatelliteHandoverDecisionVisualization: React.FC<
    SatelliteHandoverDecisionVisualizationProps
> = ({ devices, enabled, satellites = [] }) => {
    const [decisions, setDecisions] = useState<HandoverDecision[]>([])
    const [handoverPaths, setHandoverPaths] = useState<HandoverPath[]>([])
    const [selectedDecision, setSelectedDecision] = useState<string | null>(
        null
    )

    // 生成換手決策數據
    useEffect(() => {
        if (!enabled) {
            setDecisions([])
            setHandoverPaths([])
            return
        }

        const generateDecisions = () => {
            const uavs = devices.filter((d) => d.role === 'receiver')
            const availableSatellites =
                satellites.length > 0 ? satellites : generateDefaultSatellites()

            // 安全檢查：確保有可用的衛星
            if (availableSatellites.length === 0) {
                return
            }

            const newDecisions: HandoverDecision[] = []
            const newPaths: HandoverPath[] = []

            uavs.forEach((uav) => {
                // 25% 機率產生換手決策分析
                if (Math.random() < 0.25) {
                    const currentSat =
                        availableSatellites[
                            Math.floor(
                                Math.random() * availableSatellites.length
                            )
                        ]
                    const candidates = availableSatellites
                        .filter((sat) => sat.id !== currentSat.id)
                        .slice(0, 3)
                        .map((sat) => ({
                            id: sat.id || sat.norad_id,
                            name: sat.name || `Sat-${sat.id}`,
                            position: calculateSatellitePosition(sat, uav),
                            signalStrength: -60 + Math.random() * 20 - 10,
                            elevation: 20 + Math.random() * 50,
                            score: Math.random() * 100,
                            distance: 500 + Math.random() * 300,
                            loadPercentage: Math.random() * 80,
                            isSelected: false,
                        }))

                    // 選擇最佳候選衛星 - 檢查是否有候選衛星
                    if (candidates.length === 0) {
                        return // 跳過此次迭代，沒有候選衛星
                    }

                    const bestCandidate = candidates.reduce((best, current) =>
                        current.score > best.score ? current : best
                    )
                    bestCandidate.isSelected = true

                    const decision: HandoverDecision = {
                        id: `decision_${uav.id}_${Date.now()}_${Math.random()
                            .toString(36)
                            .substr(2, 9)}`,
                        uavId: uav.id,
                        currentSatellite: {
                            id: currentSat.id || currentSat.norad_id,
                            name: currentSat.name || `Current-${currentSat.id}`,
                            position: calculateSatellitePosition(
                                currentSat,
                                uav
                            ),
                            signalStrength: -70 + Math.random() * 10 - 5,
                            elevation: 15 + Math.random() * 10,
                            loadPercentage: 60 + Math.random() * 30,
                        },
                        candidateSatellites: candidates,
                        decisionFactors: {
                            signalQuality: 60 + Math.random() * 30,
                            elevation: 70 + Math.random() * 25,
                            loadBalancing: 50 + Math.random() * 40,
                            distance: 65 + Math.random() * 25,
                            interference: 80 + Math.random() * 15,
                        },
                        finalScore: bestCandidate.score,
                        decisionTime: 50 + Math.random() * 200, // ms
                        reason: generateDecisionReason(bestCandidate),
                    }

                    newDecisions.push(decision)

                    // 生成換手路徑
                    const path: HandoverPath = {
                        id: `path_${uav.id}_${Date.now()}_${Math.random()
                            .toString(36)
                            .substr(2, 9)}`,
                        uavId: uav.id,
                        path: generateHandoverPath(
                            [
                                uav.position_x || 0,
                                (uav.position_z || 0) + 10,
                                uav.position_y || 0,
                            ],
                            decision.currentSatellite.position,
                            bestCandidate.position
                        ),
                        currentSatellitePos: decision.currentSatellite.position,
                        targetSatellitePos: bestCandidate.position,
                        progress: Math.random(),
                        type: 'signal_prediction',
                    }

                    newPaths.push(path)
                }
            })

            setDecisions(newDecisions)
            setHandoverPaths(newPaths)
        }

        generateDecisions()
        const interval = setInterval(generateDecisions, 10000)

        return () => clearInterval(interval)
    }, [enabled, devices.length, satellites.length])

    if (!enabled) return null

    return (
        <>
            {/* 決策可視化主體 */}
            <DecisionVisualizationMain
                decisions={decisions}
                devices={devices}
                selectedDecision={selectedDecision}
                onSelectDecision={setSelectedDecision}
            />

            {/* 候選衛星比較 */}
            <CandidateSatelliteComparison
                decisions={decisions}
                devices={devices}
            />

            {/* 決策因子雷達圖 */}
            <DecisionFactorsRadar decisions={decisions} devices={devices} />

            {/* 換手路徑可視化 */}
            <HandoverPathVisualization
                paths={handoverPaths}
                devices={devices}
            />

            {/* 決策時間分析 */}
            <DecisionTimeAnalysis decisions={decisions} />

            {/* 3D 決策矩陣 */}
            <DecisionMatrix3D decisions={decisions} devices={devices} />
        </>
    )
}

// 生成預設衛星數據
const generateDefaultSatellites = () => {
    return [
        {
            id: 'sat_001',
            name: 'OneWeb-1234',
            elevation_deg: 45,
            azimuth_deg: 180,
        },
        {
            id: 'sat_002',
            name: 'OneWeb-5678',
            elevation_deg: 60,
            azimuth_deg: 220,
        },
        {
            id: 'sat_003',
            name: 'OneWeb-9012',
            elevation_deg: 35,
            azimuth_deg: 140,
        },
        {
            id: 'sat_004',
            name: 'OneWeb-3456',
            elevation_deg: 55,
            azimuth_deg: 300,
        },
        {
            id: 'sat_005',
            name: 'OneWeb-7890',
            elevation_deg: 40,
            azimuth_deg: 60,
        },
    ]
}

// 計算衛星位置
const calculateSatellitePosition = (
    satellite: any,
    uav: any
): [number, number, number] => {
    const PI_DIV_180 = Math.PI / 180
    const GLB_SCENE_SIZE = 1200
    const MIN_SAT_HEIGHT = 200
    const MAX_SAT_HEIGHT = 400

    const elevationRad = (satellite.elevation_deg || 45) * PI_DIV_180
    const azimuthRad = (satellite.azimuth_deg || 180) * PI_DIV_180

    const range = GLB_SCENE_SIZE * 0.45
    const horizontalDist = range * Math.cos(elevationRad)

    const x = horizontalDist * Math.sin(azimuthRad)
    const y = horizontalDist * Math.cos(azimuthRad)
    const height =
        MIN_SAT_HEIGHT +
        (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) *
            Math.pow(Math.sin(elevationRad), 0.8)

    return [x, height, y]
}

// 生成決策原因
const generateDecisionReason = (candidate: any): string => {
    if (candidate.signalStrength > -65) return '最佳信號強度'
    if (candidate.elevation > 60) return '優良仰角位置'
    if (candidate.loadPercentage < 50) return '負載平衡考量'
    return '綜合評估最佳'
}

// 生成換手路徑
const generateHandoverPath = (
    uavPos: [number, number, number],
    currentSatPos: [number, number, number],
    targetSatPos: [number, number, number]
): [number, number, number][] => {
    const path: [number, number, number][] = []
    const steps = 10

    for (let i = 0; i <= steps; i++) {
        const t = i / steps
        const x = uavPos[0] + (targetSatPos[0] - currentSatPos[0]) * t * 0.3
        const y = uavPos[1] + Math.sin(t * Math.PI) * 20
        const z = uavPos[2] + (targetSatPos[2] - currentSatPos[2]) * t * 0.3
        path.push([x, y, z])
    }

    return path
}

// 決策可視化主體組件
const DecisionVisualizationMain: React.FC<{
    decisions: HandoverDecision[]
    devices: any[]
    selectedDecision: string | null
    onSelectDecision: (id: string | null) => void
}> = ({ decisions, devices, selectedDecision, onSelectDecision }) => {
    return (
        <>
            {decisions.map((decision) => {
                const uav = devices.find((d) => d.id === decision.uavId)
                if (!uav) return null

                const isSelected = selectedDecision === decision.id

                return (
                    <group
                        key={decision.id}
                        position={[
                            uav.position_x || 0,
                            (uav.position_z || 0) + 70,
                            uav.position_y || 0,
                        ]}
                        onClick={() =>
                            onSelectDecision(isSelected ? null : decision.id)
                        }
                    >
                        {/* 決策指示器 */}
                        <mesh>
                            <sphereGeometry args={[6, 16, 16]} />
                            <meshBasicMaterial
                                color={isSelected ? '#00ff88' : '#0088ff'}
                                transparent
                                opacity={0.8}
                            />
                        </mesh>

                        <Text
                            position={[0, 12, 0]}
                            fontSize={4}
                            color="#00aaff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            🧠 決策分析
                        </Text>

                        <Text
                            position={[0, 8, 0]}
                            fontSize={3}
                            color="#ffffff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            評分: {decision.finalScore.toFixed(1)}
                        </Text>

                        <Text
                            position={[0, 4, 0]}
                            fontSize={2.5}
                            color="#88ff88"
                            anchorX="center"
                            anchorY="middle"
                        >
                            {decision.reason}
                        </Text>

                        <Text
                            position={[0, 0, 0]}
                            fontSize={2}
                            color="#cccccc"
                            anchorX="center"
                            anchorY="middle"
                        >
                            決策時間: {decision.decisionTime.toFixed(0)}ms
                        </Text>
                    </group>
                )
            })}
        </>
    )
}

// 候選衛星比較組件
const CandidateSatelliteComparison: React.FC<{
    decisions: HandoverDecision[]
    devices: any[]
}> = ({ decisions, devices }) => {
    return (
        <>
            {decisions.map((decision) => {
                const uav = devices.find((d) => d.id === decision.uavId)
                if (!uav) return null

                return decision.candidateSatellites.map((candidate, index) => (
                    <group
                        key={`candidate_${decision.id}_${candidate.id}`}
                        position={[
                            (uav.position_x || 0) + (index - 1) * 20,
                            (uav.position_z || 0) + 90,
                            uav.position_y || 0,
                        ]}
                    >
                        {/* 候選衛星指示器 */}
                        <mesh>
                            <cylinderGeometry args={[3, 3, 8, 8]} />
                            <meshBasicMaterial
                                color={
                                    candidate.isSelected ? '#00ff00' : '#ffaa00'
                                }
                                transparent
                                opacity={0.7}
                            />
                        </mesh>

                        <Text
                            position={[0, 8, 0]}
                            fontSize={2.5}
                            color={candidate.isSelected ? '#00ff00' : '#ffaa00'}
                            anchorX="center"
                            anchorY="middle"
                        >
                            {candidate.isSelected ? '✓' : '○'} {candidate.name}
                        </Text>

                        <Text
                            position={[0, 4, 0]}
                            fontSize={2}
                            color="#ffffff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            評分: {candidate.score.toFixed(1)}
                        </Text>

                        <Text
                            position={[0, 0, 0]}
                            fontSize={1.8}
                            color="#cccccc"
                            anchorX="center"
                            anchorY="middle"
                        >
                            信號: {candidate.signalStrength.toFixed(1)}dBm
                        </Text>

                        <Text
                            position={[0, -3, 0]}
                            fontSize={1.8}
                            color="#cccccc"
                            anchorX="center"
                            anchorY="middle"
                        >
                            仰角: {candidate.elevation.toFixed(1)}°
                        </Text>
                    </group>
                ))
            })}
        </>
    )
}

// 決策因子雷達圖組件
const DecisionFactorsRadar: React.FC<{
    decisions: HandoverDecision[]
    devices: any[]
}> = ({ decisions, devices }) => {
    return (
        <>
            {decisions.map((decision) => {
                const uav = devices.find((d) => d.id === decision.uavId)
                if (!uav) return null

                const factors = decision.decisionFactors
                const factorNames = Object.keys(factors)
                const factorValues = Object.values(factors)

                return (
                    <group
                        key={`radar_${decision.id}`}
                        position={[
                            (uav.position_x || 0) + 40,
                            (uav.position_z || 0) + 50,
                            uav.position_y || 0,
                        ]}
                    >
                        <Text
                            position={[0, 15, 0]}
                            fontSize={3}
                            color="#ff8800"
                            anchorX="center"
                            anchorY="middle"
                        >
                            📊 決策因子
                        </Text>

                        {factorNames.map((name, index) => {
                            const angle =
                                (index / factorNames.length) * Math.PI * 2
                            const radius = 8
                            const value = factorValues[index] / 100

                            const x = Math.cos(angle) * radius
                            const z = Math.sin(angle) * radius

                            return (
                                <group key={name}>
                                    {/* 因子標籤 */}
                                    <Text
                                        position={[x * 1.3, 0, z * 1.3]}
                                        fontSize={2}
                                        color="#ffffff"
                                        anchorX="center"
                                        anchorY="middle"
                                    >
                                        {name}
                                    </Text>

                                    {/* 因子值指示器 */}
                                    <mesh position={[x * value, 0, z * value]}>
                                        <sphereGeometry args={[1, 8, 8]} />
                                        <meshBasicMaterial
                                            color={`hsl(${
                                                value * 120
                                            }, 100%, 50%)`}
                                            transparent
                                            opacity={0.8}
                                        />
                                    </mesh>

                                    {/* 連接線 */}
                                    <Line
                                        points={[
                                            [0, 0, 0],
                                            [x * value, 0, z * value],
                                        ]}
                                        color="#888888"
                                        lineWidth={2}
                                        transparent
                                        opacity={0.6}
                                    />
                                </group>
                            )
                        })}
                    </group>
                )
            })}
        </>
    )
}

// 換手路徑可視化組件
const HandoverPathVisualization: React.FC<{
    paths: HandoverPath[]
    devices: any[]
}> = ({ paths, devices }) => {
    const pathRefs = useRef<{ [key: string]: THREE.Group }>({})

    useFrame(() => {
        // 更新路徑動畫
        paths.forEach((path) => {
            const ref = pathRefs.current[path.id]
            if (ref) {
                // 路徑的動態效果
                ref.rotation.y += 0.01
            }
        })
    })

    return (
        <>
            {paths.map((path) => {
                const uav = devices.find((d) => d.id === path.uavId)
                if (!uav) return null

                return (
                    <group
                        key={path.id}
                        ref={(ref) => {
                            if (ref) pathRefs.current[path.id] = ref
                        }}
                    >
                        {/* 路徑線 */}
                        <Line
                            points={path.path}
                            color="#00ff88"
                            lineWidth={3}
                            dashed
                            transparent
                            opacity={0.8}
                        />

                        {/* 當前位置指示器 */}
                        <mesh
                            position={
                                path.path[
                                    Math.floor(
                                        path.progress * (path.path.length - 1)
                                    )
                                ]
                            }
                        >
                            <sphereGeometry args={[2, 8, 8]} />
                            <meshBasicMaterial
                                color="#00ff88"
                                transparent
                                opacity={0.9}
                            />
                        </mesh>
                    </group>
                )
            })}
        </>
    )
}

// 決策時間分析組件
const DecisionTimeAnalysis: React.FC<{ decisions: HandoverDecision[] }> = ({
    decisions,
}) => {
    const avgDecisionTime =
        decisions.reduce((sum, d) => sum + d.decisionTime, 0) /
        (decisions.length || 1)
    const maxDecisionTime = Math.max(...decisions.map((d) => d.decisionTime), 0)
    const minDecisionTime = Math.min(...decisions.map((d) => d.decisionTime), 0)

    return (
        <group position={[-100, 80, -80]}>
            <Text
                position={[0, 20, 0]}
                fontSize={5}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
            >
                ⏱️ 決策時間分析
            </Text>

            <Text
                position={[0, 12, 0]}
                fontSize={3.5}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                平均: {avgDecisionTime.toFixed(1)}ms
            </Text>

            <Text
                position={[0, 7, 0]}
                fontSize={3}
                color="#88ff88"
                anchorX="center"
                anchorY="middle"
            >
                最快: {minDecisionTime.toFixed(1)}ms
            </Text>

            <Text
                position={[0, 2, 0]}
                fontSize={3}
                color="#ff8888"
                anchorX="center"
                anchorY="middle"
            >
                最慢: {maxDecisionTime.toFixed(1)}ms
            </Text>

            <Text
                position={[0, -3, 0]}
                fontSize={2.5}
                color="#cccccc"
                anchorX="center"
                anchorY="middle"
            >
                決策數量: {decisions.length}
            </Text>
        </group>
    )
}

// 3D 決策矩陣組件
const DecisionMatrix3D: React.FC<{
    decisions: HandoverDecision[]
    devices: any[]
}> = ({ decisions, devices }) => {
    return (
        <group position={[100, 80, -80]}>
            <Text
                position={[0, 25, 0]}
                fontSize={5}
                color="#ff8800"
                anchorX="center"
                anchorY="middle"
            >
                🎲 決策矩陣
            </Text>

            {decisions.slice(0, 3).map((decision, index) => (
                <group key={decision.id} position={[0, 15 - index * 12, 0]}>
                    <Text
                        position={[0, 5, 0]}
                        fontSize={3}
                        color="#ffffff"
                        anchorX="center"
                        anchorY="middle"
                    >
                        UAV-{decision.uavId}
                    </Text>

                    <Text
                        position={[0, 2, 0]}
                        fontSize={2.5}
                        color="#00ff88"
                        anchorX="center"
                        anchorY="middle"
                    >
                        最佳:{' '}
                        {decision.candidateSatellites.find((c) => c.isSelected)
                            ?.name || 'N/A'}
                    </Text>

                    <Text
                        position={[0, -1, 0]}
                        fontSize={2}
                        color="#ffaa88"
                        anchorX="center"
                        anchorY="middle"
                    >
                        評分: {decision.finalScore.toFixed(1)}
                    </Text>
                </group>
            ))}
        </group>
    )
}

export default SatelliteHandoverDecisionVisualization
