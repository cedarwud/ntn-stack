import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import { Text, Line } from '@react-three/drei'

interface SatelliteUAVConnectionProps {
    devices: any[]
    enabled: boolean
    satellites?: any[] // 從 props 傳入的衛星數據
}

interface SatelliteConnection {
    id: string
    satelliteId: string
    uavId: string | number
    beamId: string
    status: 'active' | 'handover' | 'establishing' | 'lost' | 'blocked'
    quality: {
        signalStrength: number // dBm
        snr: number // dB
        elevation: number // degrees
        azimuth: number // degrees
        distance: number // km
        doppler: number // Hz
    }
    performance: {
        throughput: number // Mbps
        latency: number // ms
        jitter: number // ms
        packetLoss: number // %
    }
    beam: {
        beamWidth: number // degrees
        eirp: number // dBm
        frequency: number // GHz
        polarization: 'LHCP' | 'RHCP' | 'Linear'
    }
}

interface HandoverEvent {
    id: string
    uavId: string | number
    fromSatellite: string
    toSatellite: string
    startTime: number
    status: 'preparing' | 'executing' | 'completed' | 'failed'
    reason: 'elevation' | 'blockage' | 'quality' | 'load_balancing'
    progress: number // 0-100
}

interface BeamCoverage {
    satelliteId: string
    position: [number, number, number]
    coverageArea: {
        center: [number, number]
        radius: number
        elevation: number
    }[]
    activeBeams: number
    maxBeams: number
}

const SatelliteUAVConnection: React.FC<SatelliteUAVConnectionProps> = ({ 
    devices, 
    enabled, 
    satellites = [] 
}) => {
    const [connections, setConnections] = useState<SatelliteConnection[]>([])
    const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([])
    const [beamCoverages, setBeamCoverages] = useState<BeamCoverage[]>([])
    const [processedSatellites, setProcessedSatellites] = useState<any[]>([])
    const [connectionMetrics, setConnectionMetrics] = useState({
        totalConnections: 0,
        activeConnections: 0,
        averageSignalStrength: 0,
        averageLatency: 0,
        handoverSuccessRate: 0,
        networkCapacity: 0
    })

    // 分析衛星-UAV 連接
    useEffect(() => {
        if (!enabled) {
            setConnections([])
            setHandoverEvents([])
            setBeamCoverages([])
            return
        }

        const analyzeConnections = () => {
            const uavs = devices.filter(d => d.role === 'receiver')
            
            // 如果沒有 UAV，直接返回
            if (uavs.length === 0) {
                setConnections([])
                return
            }
            
            let satelliteConnections: any[] = []
            
            // 檢查是否有真實衛星數據
            if (satellites && satellites.length > 0) {
                // 使用真實衛星數據並應用 SimplifiedSatellite 相同的位置計算
                satelliteConnections = satellites.slice(0, Math.min(5, satellites.length)).map((sat, index) => {
                    const PI_DIV_180 = Math.PI / 180
                    const GLB_SCENE_SIZE = 1200
                    const MIN_SAT_HEIGHT = 0
                    const MAX_SAT_HEIGHT = 300
                    
                    const elevationRad = (sat.elevation_deg || 45) * PI_DIV_180
                    const azimuthRad = (sat.azimuth_deg || index * 60) * PI_DIV_180
                    
                    // 使用與 SimplifiedSatellite 相同的位置計算
                    const range = GLB_SCENE_SIZE * 0.45
                    const horizontalDist = range * Math.cos(elevationRad)
                    
                    const x = horizontalDist * Math.sin(azimuthRad)
                    const y = horizontalDist * Math.cos(azimuthRad)
                    const height = MIN_SAT_HEIGHT + (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * Math.pow(Math.sin(elevationRad), 0.8)
                    
                    return {
                        id: sat.norad_id || sat.id || `sat_${index}`,
                        name: sat.name || `Satellite-${index}`,
                        position: [x, height, y], // 與 SimplifiedSatellite 相同的坐標系統
                        elevation: sat.elevation_deg || 45,
                        azimuth: sat.azimuth_deg || index * 60,
                        velocity: [0, 0, 0],
                        norad_id: sat.norad_id // 保持原始ID用於匹配
                    }
                })
            } else {
                // 如果沒有衛星數據，使用預設數據
                const defaultSatelliteConfigs = [
                    { id: 'sat_001', name: 'OneWeb-1234', elevation: 65, azimuth: 180 },
                    { id: 'sat_002', name: 'OneWeb-5678', elevation: 45, azimuth: 220 },
                    { id: 'sat_003', name: 'OneWeb-9012', elevation: 55, azimuth: 140 }
                ]
                
                const PI_DIV_180 = Math.PI / 180
                const GLB_SCENE_SIZE = 1200
                const MIN_SAT_HEIGHT = 0
                const MAX_SAT_HEIGHT = 300
                
                satelliteConnections = defaultSatelliteConfigs.map(config => {
                    const elevationRad = config.elevation * PI_DIV_180
                    const azimuthRad = config.azimuth * PI_DIV_180
                    
                    const range = GLB_SCENE_SIZE * 0.45
                    const horizontalDist = range * Math.cos(elevationRad)
                    
                    const x = horizontalDist * Math.sin(azimuthRad)
                    const y = horizontalDist * Math.cos(azimuthRad)
                    const height = MIN_SAT_HEIGHT + (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * Math.pow(Math.sin(elevationRad), 0.8)
                    
                    return {
                        id: config.id,
                        name: config.name,
                        position: [x, height, y],
                        elevation: config.elevation,
                        azimuth: config.azimuth,
                        velocity: [0, 0, 0]
                    }
                })
            }
            
            // 存儲處理過的衛星數據
            setProcessedSatellites(satelliteConnections)
            
            // 為每個 UAV 建立連接
            const newConnections: SatelliteConnection[] = []
            uavs.forEach((uav, index) => {
                // 循環使用衛星（如果 UAV 比衛星多）
                const satelliteIndex = index % satelliteConnections.length
                const satellite = satelliteConnections[satelliteIndex]
                
                if (satellite) {
                    newConnections.push({
                        id: `conn_${uav.id}_${satellite.id}`,
                        satelliteId: satellite.id,
                        uavId: uav.id,
                        beamId: `beam_${satellite.id}_${uav.id}`,
                        status: 'active',
                        quality: {
                            signalStrength: -65 + Math.random() * 10 - 5,
                            snr: 25 + Math.random() * 10 - 5,
                            elevation: satellite.elevation,
                            azimuth: satellite.azimuth,
                            distance: 500 + Math.random() * 200,
                            doppler: 1000 + Math.random() * 500 - 250
                        },
                        performance: {
                            throughput: 100 + Math.random() * 50,
                            latency: 20 + Math.random() * 10,
                            jitter: 3 + Math.random() * 2,
                            packetLoss: Math.random() * 2
                        },
                        beam: {
                            beamWidth: 0.7 + Math.random() * 0.3,
                            eirp: 60 + Math.random() * 10,
                            frequency: 13 + Math.random() * 2,
                            polarization: Math.random() > 0.5 ? 'LHCP' : 'RHCP'
                        }
                    })
                }
            })
            
            setConnections(newConnections)
            setHandoverEvents([])
            setBeamCoverages([])

            // 更新指標
            setConnectionMetrics({
                totalConnections: newConnections.length,
                activeConnections: newConnections.length,
                averageSignalStrength: newConnections.reduce((sum, c) => sum + c.quality.signalStrength, 0) / (newConnections.length || 1),
                averageLatency: newConnections.reduce((sum, c) => sum + c.performance.latency, 0) / (newConnections.length || 1),
                handoverSuccessRate: 95 + Math.random() * 4,
                networkCapacity: newConnections.reduce((sum, c) => sum + c.performance.throughput, 0)
            })
        }

        analyzeConnections()
        const interval = setInterval(analyzeConnections, 5000) // 每5秒更新

        return () => clearInterval(interval)
    }, [devices, enabled, satellites])

    if (!enabled) return null

    return (
        <>
            {/* 衛星-UAV 連接線 */}
            <ConnectionLinksVisualization 
                connections={connections} 
                devices={devices} 
                satellites={processedSatellites} 
            />
            
            {/* 連接狀態顯示 */}
            <ConnectionStatusDisplay metrics={connectionMetrics} />
            
            {/* 簡化的連接質量指示器 - 只顯示前3個 */}
            {connections.slice(0, 3).map((connection) => (
                <ConnectionQualityIndicator
                    key={connection.id}
                    connection={connection}
                    devices={devices}
                />
            ))}
        </>
    )
}

// 移除了未使用的複雜計算函數以提升性能

// 連接線可視化組件
const ConnectionLinksVisualization: React.FC<{
    connections: SatelliteConnection[]
    devices: any[]
    satellites: any[]
}> = ({ connections, devices, satellites }) => {
    const { scene } = useThree()
    const [satellitePositions, setSatellitePositions] = useState<Map<string, [number, number, number]>>(new Map())
    
    const getConnectionColor = (status: SatelliteConnection['status']) => {
        switch (status) {
            case 'active': return '#00ff00'
            case 'handover': return '#ffaa00'
            case 'establishing': return '#0088ff'
            case 'lost': return '#ff0000'
            case 'blocked': return '#666666'
            default: return '#ffffff'
        }
    }

    // 使用 useFrame 實時更新衛星位置
    useFrame(() => {
        const newPositions = new Map<string, [number, number, number]>()
        
        scene.traverse((child) => {
            // 查找衛星組件的 group（SimplifiedSatellite 使用 group）
            if (child.type === 'Group' && child.userData?.satelliteId) {
                const satelliteId = child.userData.satelliteId
                const pos = child.position
                newPositions.set(satelliteId, [pos.x, pos.y, pos.z])
            }
            
            // 也嘗試通過名稱匹配
            if (child.name && child.name.includes('satellite-')) {
                const nameMatch = child.name.match(/satellite-(.+)/)
                if (nameMatch) {
                    const satelliteId = nameMatch[1]
                    const pos = child.position
                    newPositions.set(satelliteId, [pos.x, pos.y, pos.z])
                }
            }
        })
        
        // 只有當位置有變化時才更新state
        if (newPositions.size > 0) {
            setSatellitePositions(prevPositions => {
                // 避免不必要的重新渲染，只有位置真正變化時才更新
                const hasChanged = Array.from(newPositions.entries()).some(([id, pos]) => {
                    const prevPos = prevPositions.get(id)
                    if (!prevPos) return true
                    const [x, y, z] = pos
                    const [px, py, pz] = prevPos
                    return Math.abs(x - px) > 0.1 || Math.abs(y - py) > 0.1 || Math.abs(z - pz) > 0.1
                })
                
                return hasChanged ? newPositions : prevPositions
            })
        }
    })

    return (
        <>
            {connections.map((connection) => {
                const uav = devices.find(d => d.id === connection.uavId)
                if (!uav) return null

                // 首先嘗試從實時位置Map中找到衛星位置
                let satellitePos: [number, number, number] | null = satellitePositions.get(connection.satelliteId) || null
                
                // 如果沒找到實際位置，使用預設數據
                if (!satellitePos) {
                    const satellite = satellites.find(sat => sat.id === connection.satelliteId)
                    if (!satellite) return null
                    satellitePos = satellite.position
                }

                const uavPos: [number, number, number] = [
                    uav.position_x || 0,
                    (uav.position_z || 0) + 10,
                    uav.position_y || 0
                ]

                const points = [satellitePos, uavPos]

                return (
                    <Line
                        key={connection.id}
                        points={points}
                        color={getConnectionColor(connection.status)}
                        lineWidth={connection.status === 'active' ? 3 : 2}
                        dashed={connection.status === 'handover'}
                        transparent
                        opacity={0.8}
                    />
                )
            })}
        </>
    )
}

// 移除波束覆蓋可視化以提升性能

// 連接質量指示器組件
const ConnectionQualityIndicator: React.FC<{
    connection: SatelliteConnection
    devices: any[]
}> = ({ connection, devices }) => {
    const uav = devices.find(d => d.id === connection.uavId)
    if (!uav) return null

    const getQualityColor = (signalStrength: number) => {
        if (signalStrength > -60) return '#00ff00'
        if (signalStrength > -80) return '#ffaa00'
        return '#ff4400'
    }

    return (
        <group position={[
            uav.position_x || 0,
            (uav.position_z || 0) + 40,
            uav.position_y || 0
        ]}>
            <Text
                position={[0, 8, 0]}
                fontSize={3}
                color={getQualityColor(connection.quality.signalStrength)}
                anchorX="center"
                anchorY="middle"
            >
                📶 {connection.quality.signalStrength.toFixed(1)} dBm
            </Text>
            
            <Text
                position={[0, 4, 0]}
                fontSize={2.5}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                SNR: {connection.quality.snr.toFixed(1)} dB
            </Text>
            
            <Text
                position={[0, 0, 0]}
                fontSize={2.5}
                color="#aaaaaa"
                anchorX="center"
                anchorY="middle"
            >
                仰角: {connection.quality.elevation.toFixed(1)}°
            </Text>
        </group>
    )
}

// 移除切換事件可視化以提升性能

// 連接狀態顯示組件
const ConnectionStatusDisplay: React.FC<{ metrics: any }> = ({ metrics }) => {
    return (
        <group position={[-80, 80, 80]}>
            <Text
                position={[0, 25, 0]}
                fontSize={6}
                color="#00aaff"
                anchorX="center"
                anchorY="middle"
            >
                🛰️ 衛星連接狀態
            </Text>
            
            <Text
                position={[0, 18, 0]}
                fontSize={4}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                總連接數: {metrics.totalConnections}
            </Text>
            
            <Text
                position={[0, 13, 0]}
                fontSize={4}
                color="#00ff88"
                anchorX="center"
                anchorY="middle"
            >
                活躍連接: {metrics.activeConnections}
            </Text>
            
            <Text
                position={[0, 8, 0]}
                fontSize={3.5}
                color="#88ff88"
                anchorX="center"
                anchorY="middle"
            >
                平均信號: {metrics.averageSignalStrength.toFixed(1)} dBm
            </Text>
            
            <Text
                position={[0, 3, 0]}
                fontSize={3.5}
                color="#ffaa88"
                anchorX="center"
                anchorY="middle"
            >
                平均延遲: {metrics.averageLatency.toFixed(1)} ms
            </Text>
            
            <Text
                position={[0, -2, 0]}
                fontSize={3.5}
                color="#aaffff"
                anchorX="center"
                anchorY="middle"
            >
                切換成功率: {metrics.handoverSuccessRate.toFixed(1)}%
            </Text>
            
            <Text
                position={[0, -7, 0]}
                fontSize={3.5}
                color="#ffaaff"
                anchorX="center"
                anchorY="middle"
            >
                網路容量: {metrics.networkCapacity.toFixed(0)} Mbps
            </Text>
        </group>
    )
}

// 移除信號質量監控和多普勒效應可視化以提升性能

export default SatelliteUAVConnection