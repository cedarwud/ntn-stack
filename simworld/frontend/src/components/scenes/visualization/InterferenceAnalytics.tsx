import React, { useState, useEffect } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text, Line } from '@react-three/drei'

interface InterferenceAnalyticsProps {
    devices: any[]
    enabled: boolean
}

interface InterferencePattern {
    id: string
    type: 'intentional' | 'unintentional' | 'multipath' | 'co_channel'
    sourceId: string | number
    affectedDevices: string[]
    severity: 'low' | 'medium' | 'high' | 'critical'
    frequency: number
    power: number
    duration: number
    predictedImpact: number
    mitigation: string[]
}

interface AnalyticsResult {
    timestamp: string
    totalPatterns: number
    criticalCount: number
    predictedOutages: number
    systemEfficiency: number
    recommendations: string[]
}

const InterferenceAnalytics: React.FC<InterferenceAnalyticsProps> = ({ devices, enabled }) => {
    const [interferencePatterns, setInterferencePatterns] = useState<InterferencePattern[]>([])
    const [analyticsResult, setAnalyticsResult] = useState<AnalyticsResult | null>(null)
    const [scanProgress, setScanProgress] = useState(0)
    const [isScanning, setIsScanning] = useState(false)

    // 干擾模式分析引擎
    useEffect(() => {
        if (!enabled) {
            setInterferencePatterns([])
            setAnalyticsResult(null)
            return
        }

        const runAnalytics = async () => {
            setIsScanning(true)
            setScanProgress(0)

            // 模擬分析過程
            for (let i = 0; i <= 100; i += 20) {
                setScanProgress(i)
                await new Promise(resolve => setTimeout(resolve, 300))
            }

            // 分析干擾模式
            const patterns = analyzeInterferencePatterns(devices)
            setInterferencePatterns(patterns)

            // 生成分析結果
            const result = generateAnalyticsResult(patterns)
            setAnalyticsResult(result)

            setIsScanning(false)
        }

        runAnalytics()
        const interval = setInterval(runAnalytics, 15000) // 每15秒重新分析

        return () => clearInterval(interval)
    }, [devices, enabled])

    if (!enabled) return null

    return (
        <>
            {/* 掃描進度顯示 */}
            {isScanning && <ScanProgressDisplay progress={scanProgress} />}
            
            {/* 干擾模式可視化 */}
            {interferencePatterns.map((pattern) => (
                <InterferencePatternVisualization
                    key={pattern.id}
                    pattern={pattern}
                    devices={devices}
                />
            ))}
            
            {/* 分析結果顯示 */}
            {analyticsResult && <AnalyticsResultDisplay result={analyticsResult} />}
            
            {/* 干擾路徑線條 */}
            <InterferencePathLines patterns={interferencePatterns} devices={devices} />
        </>
    )
}

// 分析干擾模式
const analyzeInterferencePatterns = (devices: any[]): InterferencePattern[] => {
    const patterns: InterferencePattern[] = []
    const jammers = devices.filter(d => d.role === 'jammer')
    const receivers = devices.filter(d => d.role === 'receiver')
    const transmitters = devices.filter(d => d.role === 'desired')

    jammers.forEach((jammer, index) => {
        // 分析故意干擾模式
        const affectedRx = receivers.filter(rx => {
            const distance = Math.sqrt(
                Math.pow((rx.position_x || 0) - (jammer.position_x || 0), 2) +
                Math.pow((rx.position_y || 0) - (jammer.position_y || 0), 2)
            )
            return distance < 80
        })

        if (affectedRx.length > 0) {
            const severity = getSeverityLevel(affectedRx.length, 80)
            patterns.push({
                id: `intentional_${jammer.id}_${index}`,
                type: 'intentional',
                sourceId: jammer.id,
                affectedDevices: affectedRx.map(rx => rx.id),
                severity,
                frequency: 2400 + Math.random() * 200, // MHz
                power: 20 + Math.random() * 10, // dBm
                duration: Math.random() * 3600, // seconds
                predictedImpact: calculatePredictedImpact(affectedRx.length, severity),
                mitigation: generateMitigationStrategies(severity, 'intentional')
            })
        }

        // 分析同頻干擾
        transmitters.forEach(tx => {
            const txToJammerDistance = Math.sqrt(
                Math.pow((tx.position_x || 0) - (jammer.position_x || 0), 2) +
                Math.pow((tx.position_y || 0) - (jammer.position_y || 0), 2)
            )

            if (txToJammerDistance < 120) {
                patterns.push({
                    id: `co_channel_${tx.id}_${jammer.id}`,
                    type: 'co_channel',
                    sourceId: jammer.id,
                    affectedDevices: [tx.id],
                    severity: txToJammerDistance < 60 ? 'high' : 'medium',
                    frequency: 2400,
                    power: 15,
                    duration: Math.random() * 1800,
                    predictedImpact: txToJammerDistance < 60 ? 80 : 50,
                    mitigation: generateMitigationStrategies('high', 'co_channel')
                })
            }
        })
    })

    // 分析多徑干擾
    receivers.forEach(rx => {
        const nearbyTx = transmitters.filter(tx => {
            const distance = Math.sqrt(
                Math.pow((rx.position_x || 0) - (tx.position_x || 0), 2) +
                Math.pow((rx.position_y || 0) - (tx.position_y || 0), 2)
            )
            return distance > 30 && distance < 100
        })

        if (nearbyTx.length > 1) {
            patterns.push({
                id: `multipath_${rx.id}`,
                type: 'multipath',
                sourceId: rx.id,
                affectedDevices: [rx.id],
                severity: 'medium',
                frequency: 2400,
                power: -10,
                duration: 300,
                predictedImpact: 30,
                mitigation: generateMitigationStrategies('medium', 'multipath')
            })
        }
    })

    return patterns
}

const getSeverityLevel = (affectedCount: number, distance: number): 'low' | 'medium' | 'high' | 'critical' => {
    if (affectedCount >= 3 || distance < 30) return 'critical'
    if (affectedCount >= 2 || distance < 50) return 'high'
    if (affectedCount >= 1 || distance < 70) return 'medium'
    return 'low'
}

const calculatePredictedImpact = (affectedCount: number, severity: string): number => {
    const baseImpact = affectedCount * 20
    const severityMultiplier = {
        'low': 0.5,
        'medium': 1.0,
        'high': 1.5,
        'critical': 2.0
    }
    return Math.min(baseImpact * (severityMultiplier[severity as keyof typeof severityMultiplier] || 1), 100)
}

const generateMitigationStrategies = (severity: string, type: string): string[] => {
    const strategies: { [key: string]: string[] } = {
        'intentional': ['頻率跳躍', '功率控制', '波束成形', '加密通訊'],
        'co_channel': ['頻率分配', '空間分隔', '時分多址', '載波聚合'],
        'multipath': ['等化器', '分集接收', 'OFDM調變', '通道編碼'],
        'unintentional': ['濾波器', '屏蔽', '協調機制', '檢測算法']
    }
    
    const severityStrategies: { [key: string]: string[] } = {
        'low': ['監控', '記錄'],
        'medium': ['自動優化', '告警'],
        'high': ['立即緩解', '重新路由'],
        'critical': ['緊急處理', '系統隔離']
    }
    
    return [...(strategies[type] || []), ...(severityStrategies[severity] || [])]
}

const generateAnalyticsResult = (patterns: InterferencePattern[]): AnalyticsResult => {
    const criticalCount = patterns.filter(p => p.severity === 'critical').length
    const totalImpact = patterns.reduce((sum, p) => sum + p.predictedImpact, 0)
    
    return {
        timestamp: new Date().toISOString(),
        totalPatterns: patterns.length,
        criticalCount,
        predictedOutages: Math.floor(totalImpact / 100),
        systemEfficiency: Math.max(0, 100 - totalImpact / 10),
        recommendations: [
            criticalCount > 0 ? '立即處理關鍵干擾源' : '系統運行正常',
            patterns.length > 5 ? '建議頻率重新規劃' : '頻率使用合理',
            totalImpact > 200 ? '啟動緊急干擾緩解' : '監控持續進行'
        ]
    }
}

const ScanProgressDisplay: React.FC<{ progress: number }> = ({ progress }) => {
    return (
        <group position={[0, 60, 0]}>
            <Text
                position={[0, 10, 0]}
                fontSize={5}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
            >
                🔍 干擾分析掃描中...
            </Text>
            
            <Text
                position={[0, 5, 0]}
                fontSize={4}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                進度: {progress}%
            </Text>
            
            {/* 進度條 */}
            <mesh position={[0, 0, 0]}>
                <boxGeometry args={[60, 3, 1]} />
                <meshBasicMaterial color="#333333" />
            </mesh>
            
            <mesh position={[-30 + (progress * 60) / 200, 0, 0.1]}>
                <boxGeometry args={[(progress * 60) / 100, 3, 1]} />
                <meshBasicMaterial color="#00ff88" />
            </mesh>
        </group>
    )
}

const InterferencePatternVisualization: React.FC<{ 
    pattern: InterferencePattern
    devices: any[]
}> = ({ pattern, devices }) => {
    const meshRef = React.useRef<THREE.Group>(null)
    
    const sourceDevice = devices.find(d => d.id === pattern.sourceId)
    if (!sourceDevice) return null

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'low': return '#ffff00'
            case 'medium': return '#ff8800'
            case 'high': return '#ff4400'
            case 'critical': return '#ff0000'
            default: return '#ffffff'
        }
    }

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'intentional': return '🎯'
            case 'unintentional': return '📻'
            case 'multipath': return '🔀'
            case 'co_channel': return '📡'
            default: return '⚡'
        }
    }

    useFrame((state) => {
        if (meshRef.current) {
            const time = state.clock.getElapsedTime()
            const intensity = pattern.severity === 'critical' ? 2 : pattern.severity === 'high' ? 1.5 : 1
            meshRef.current.rotation.y = time * intensity
            
            const scale = 1 + Math.sin(time * intensity * 2) * 0.2
            meshRef.current.scale.setScalar(scale)
        }
    })

    return (
        <group
            ref={meshRef}
            position={[
                sourceDevice.position_x || 0,
                (sourceDevice.position_z || 0) + 40,
                sourceDevice.position_y || 0
            ]}
        >
            {/* 干擾模式指示器 */}
            <mesh>
                <coneGeometry args={[8, 16, 6]} />
                <meshStandardMaterial
                    color={getSeverityColor(pattern.severity)}
                    transparent
                    opacity={0.8}
                    emissive={getSeverityColor(pattern.severity)}
                    emissiveIntensity={0.3}
                />
            </mesh>
            
            {/* 干擾類型標籤 */}
            <Text
                position={[0, 20, 0]}
                fontSize={4}
                color={getSeverityColor(pattern.severity)}
                anchorX="center"
                anchorY="middle"
            >
                {getTypeIcon(pattern.type)} {pattern.type.toUpperCase()}
            </Text>
            
            <Text
                position={[0, 15, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                嚴重度: {pattern.severity.toUpperCase()}
            </Text>
            
            <Text
                position={[0, 10, 0]}
                fontSize={2.5}
                color="#cccccc"
                anchorX="center"
                anchorY="middle"
            >
                影響: {pattern.predictedImpact.toFixed(0)}%
            </Text>
        </group>
    )
}

const InterferencePathLines: React.FC<{
    patterns: InterferencePattern[]
    devices: any[]
}> = ({ patterns, devices }) => {
    return (
        <>
            {patterns.map((pattern) => {
                const sourceDevice = devices.find(d => d.id === pattern.sourceId)
                if (!sourceDevice) return null

                return pattern.affectedDevices.map((deviceId) => {
                    const targetDevice = devices.find(d => d.id === deviceId)
                    if (!targetDevice) return null

                    const points = [
                        [sourceDevice.position_x || 0, (sourceDevice.position_z || 0) + 10, sourceDevice.position_y || 0],
                        [targetDevice.position_x || 0, (targetDevice.position_z || 0) + 10, targetDevice.position_y || 0]
                    ]

                    return (
                        <Line
                            key={`${pattern.id}_${deviceId}`}
                            points={points}
                            color={pattern.severity === 'critical' ? '#ff0000' : '#ff8800'}
                            lineWidth={pattern.severity === 'critical' ? 3 : 2}
                            dashed={pattern.type === 'multipath'}
                        />
                    )
                })
            })}
        </>
    )
}

const AnalyticsResultDisplay: React.FC<{ result: AnalyticsResult }> = ({ result }) => {
    return (
        <group position={[80, 60, 80]}>
            <Text
                position={[0, 20, 0]}
                fontSize={5}
                color="#00ffaa"
                anchorX="center"
                anchorY="middle"
            >
                🔍 干擾分析結果
            </Text>
            
            <Text
                position={[0, 14, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                檢測到 {result.totalPatterns} 個干擾模式
            </Text>
            
            <Text
                position={[0, 10, 0]}
                fontSize={3}
                color={result.criticalCount > 0 ? '#ff0000' : '#00ff00'}
                anchorX="center"
                anchorY="middle"
            >
                關鍵威脅: {result.criticalCount} 個
            </Text>
            
            <Text
                position={[0, 6, 0]}
                fontSize={3}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
            >
                系統效率: {result.systemEfficiency.toFixed(1)}%
            </Text>
            
            <Text
                position={[0, 2, 0]}
                fontSize={3}
                color="#ff8800"
                anchorX="center"
                anchorY="middle"
            >
                預測中斷: {result.predictedOutages} 次
            </Text>
            
            {/* 建議 */}
            {result.recommendations.map((rec, index) => (
                <Text
                    key={index}
                    position={[0, -4 - index * 3, 0]}
                    fontSize={2}
                    color="#88ccff"
                    anchorX="center"
                    anchorY="middle"
                >
                    • {rec}
                </Text>
            ))}
        </group>
    )
}

export default InterferenceAnalytics