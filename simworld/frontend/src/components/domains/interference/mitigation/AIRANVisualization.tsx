import React, { useState, useEffect } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'

interface AIRANVisualizationProps {
    devices: any[]
    enabled: boolean
}

interface AIDecision {
    id: string
    type: 'beam_optimization' | 'power_control' | 'interference_mitigation'
    position: [number, number, number]
    status: 'analyzing' | 'executing' | 'completed'
    improvement: number
}

const AIRANVisualization: React.FC<AIRANVisualizationProps> = ({ devices, enabled }) => {
    const [decisions, setDecisions] = useState<AIDecision[]>([])

    // 模擬 AI 決策生成
    useEffect(() => {
        if (!enabled) {
            setDecisions([])
            return
        }

        const interval = setInterval(() => {
            // 為有問題的設備生成 AI 決策
            const receiverDevices = devices.filter(d => d.role === 'receiver')
            const jammerDevices = devices.filter(d => d.role === 'jammer')
            
            const newDecisions: AIDecision[] = []
            
            receiverDevices.forEach((receiver, index) => {
                // 檢查 Rx 是否靠近 Jammer 干擾源
                const nearJammer = jammerDevices.some(jammer => {
                    const distance = Math.sqrt(
                        Math.pow((receiver.position_x || 0) - (jammer.position_x || 0), 2) +
                        Math.pow((receiver.position_y || 0) - (jammer.position_y || 0), 2)
                    )
                    return distance < 80 // 干擾影響範圍
                })

                if (nearJammer) {
                    const decisionTypes = ['interference_mitigation', 'beam_optimization', 'power_control']
                    const randomType = decisionTypes[Math.floor(Math.random() * decisionTypes.length)]
                    
                    newDecisions.push({
                        id: `decision_${receiver.id || index}`,
                        type: randomType as any,
                        position: [
                            receiver.position_x || 0, 
                            (receiver.position_z || 0) + 25, 
                            receiver.position_y || 0
                        ],
                        status: 'analyzing',
                        improvement: Math.random() * 15 + 5 // 5-20dB 改善
                    })
                }
            })
            
            setDecisions(newDecisions)
        }, 3000)

        return () => clearInterval(interval)
    }, [devices, enabled])

    // 更新決策狀態
    useEffect(() => {
        if (decisions.length === 0) return

        const statusUpdateInterval = setInterval(() => {
            setDecisions(prev => prev.map(decision => {
                if (decision.status === 'analyzing') {
                    return { ...decision, status: 'executing' }
                } else if (decision.status === 'executing') {
                    return { ...decision, status: 'completed' }
                }
                return decision
            }))
        }, 2000)

        return () => clearInterval(statusUpdateInterval)
    }, [decisions])

    if (!enabled) return null

    return (
        <>
            {decisions.map((decision) => (
                <AIDecisionVisualization
                    key={decision.id}
                    decision={decision}
                />
            ))}
            <AISystemStatus enabled={enabled} totalDecisions={decisions.length} />
        </>
    )
}

interface AIDecisionVisualizationProps {
    decision: AIDecision
}

const AIDecisionVisualization: React.FC<AIDecisionVisualizationProps> = ({ decision }) => {
    const meshRef = React.useRef<THREE.Group>(null)

    useFrame((state) => {
        if (meshRef.current) {
            const time = state.clock.getElapsedTime()
            
            if (decision.status === 'analyzing') {
                // 分析階段：旋轉動畫
                meshRef.current.rotation.y = time * 2
            } else if (decision.status === 'executing') {
                // 執行階段：脈動效果
                const scale = 1 + Math.sin(time * 4) * 0.2
                meshRef.current.scale.setScalar(scale)
            }
        }
    })

    const getDecisionColor = () => {
        switch (decision.type) {
            case 'beam_optimization': return '#00ff88'
            case 'power_control': return '#4488ff'
            case 'interference_mitigation': return '#ff8844'
            default: return '#ffffff'
        }
    }

    const getStatusColor = () => {
        switch (decision.status) {
            case 'analyzing': return '#ffff00'
            case 'executing': return '#ff8800'
            case 'completed': return '#00ff00'
            default: return '#ffffff'
        }
    }

    return (
        <group ref={meshRef} position={decision.position}>
            {/* 決策指示器 */}
            <mesh>
                <cylinderGeometry args={[8, 2, 15, 8]} />
                <meshStandardMaterial
                    color={getDecisionColor()}
                    transparent
                    opacity={0.7}
                    emissive={getDecisionColor()}
                    emissiveIntensity={0.2}
                />
            </mesh>
            
            {/* 狀態環 */}
            <mesh position={[0, 8, 0]}>
                <torusGeometry args={[12, 2, 8, 16]} />
                <meshStandardMaterial
                    color={getStatusColor()}
                    emissive={getStatusColor()}
                    emissiveIntensity={0.5}
                />
            </mesh>
            
            {/* 決策標籤 */}
            <Text
                position={[0, 20, 0]}
                fontSize={4}
                color={getDecisionColor()}
                anchorX="center"
                anchorY="middle"
            >
                {decision.type.replace('_', ' ').toUpperCase()}
            </Text>
            
            <Text
                position={[0, 15, 0]}
                fontSize={3}
                color={getStatusColor()}
                anchorX="center"
                anchorY="middle"
            >
                {decision.status.toUpperCase()}
            </Text>
            
            {decision.status === 'completed' && (
                <Text
                    position={[0, 10, 0]}
                    fontSize={2.5}
                    color="#00ff00"
                    anchorX="center"
                    anchorY="middle"
                >
                    +{decision.improvement.toFixed(1)}dB
                </Text>
            )}
        </group>
    )
}

interface AISystemStatusProps {
    enabled: boolean
    totalDecisions: number
}

const AISystemStatus: React.FC<AISystemStatusProps> = ({ enabled, totalDecisions }) => {
    const [stats, setStats] = useState({
        decisionsPerMinute: 0,
        successRate: 95,
        energySavings: 12,
        spectralEfficiency: 8
    })

    useEffect(() => {
        if (!enabled) return

        const interval = setInterval(() => {
            setStats(prev => ({
                decisionsPerMinute: Math.floor(Math.random() * 5) + totalDecisions,
                successRate: 90 + Math.random() * 10,
                energySavings: 10 + Math.random() * 5,
                spectralEfficiency: 5 + Math.random() * 8
            }))
        }, 5000)

        return () => clearInterval(interval)
    }, [enabled, totalDecisions])

    if (!enabled) return null

    return (
        <group position={[80, 50, 80]}>
            <Text
                position={[0, 20, 0]}
                fontSize={5}
                color="#00ffff"
                anchorX="center"
                anchorY="middle"
            >
                AI-RAN 系統狀態
            </Text>
            
            <Text
                position={[0, 10, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                決策/分鐘: {stats.decisionsPerMinute}
            </Text>
            
            <Text
                position={[0, 5, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                成功率: {stats.successRate.toFixed(1)}%
            </Text>
            
            <Text
                position={[0, 0, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                能耗節省: {stats.energySavings.toFixed(1)}%
            </Text>
            
            <Text
                position={[0, -5, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                頻譜效率提升: {stats.spectralEfficiency.toFixed(1)}%
            </Text>
        </group>
    )
}

export default AIRANVisualization