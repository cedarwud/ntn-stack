import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import { Text, Line } from '@react-three/drei'

interface SatelliteUAVConnectionProps {
    devices: any[]
    enabled: boolean
    satellites?: any[] // 從 props 傳入的衛星數據
    onConnectionsUpdate?: (connections: SatelliteConnection[]) => void // 新增：傳遞連線數據給父組件
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
    satellites = [],
    onConnectionsUpdate
}) => {
    const [connections, setConnections] = useState<SatelliteConnection[]>([])
    const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([])
    const [beamCoverages, setBeamCoverages] = useState<BeamCoverage[]>([])
    const [processedSatellites, setProcessedSatellites] = useState<any[]>([])
    const [connectionStates, setConnectionStates] = useState<Map<string, { status: string, lastChange: number }>>(new Map())
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
            setConnectionStates(new Map())
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
            
            // 修復：統一 ID 生成邏輯，確保與 SimplifiedSatellite 完全一致
            if (satellites && satellites.length > 0) {
                satelliteConnections = satellites.slice(0, Math.min(5, satellites.length)).map((sat, index) => {
                    // 修復：確保 ID 生成與 SimplifiedSatellite.tsx 第360-361行完全一致
                    const satelliteId = sat.norad_id || sat.id || `satellite_${index}`
                    
                    return {
                        id: satelliteId,
                        name: sat.name || `Satellite-${satelliteId}`,
                        position: null, // 完全依賴實時追蹤
                        elevation: sat.elevation_deg || 45,
                        azimuth: sat.azimuth_deg || index * 60,
                        velocity: [0, 0, 0],
                        norad_id: sat.norad_id
                    }
                })
            } else {
                // 預設衛星配置，使用數字 ID 格式與 SimplifiedSatellite 一致
                satelliteConnections = [
                    { id: '0', name: 'Default-Sat-0', elevation: 65, azimuth: 180 },
                    { id: '1', name: 'Default-Sat-1', elevation: 45, azimuth: 220 },
                    { id: '2', name: 'Default-Sat-2', elevation: 55, azimuth: 140 }
                ].map(config => ({
                    id: config.id,
                    name: config.name,
                    position: null,
                    elevation: config.elevation,
                    azimuth: config.azimuth,
                    velocity: [0, 0, 0]
                }))
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
                    // 修復：穩定的連線狀態計算，減少閃爍
                    const getStableConnectionStatus = (satellite: any, uav: any) => {
                        const connectionKey = `${uav.id}_${satellite.id}`
                        const currentTime = Date.now()
                        const existingState = connectionStates.get(connectionKey)
                        
                        // 如果連線狀態在過去10秒內沒有變化，保持原狀態
                        if (existingState && (currentTime - existingState.lastChange) < 10000) {
                            return existingState.status
                        }
                        
                        const elevation = satellite.elevation || 45
                        const signalStrength = -65 + Math.random() * 10 - 5
                        let newStatus: string
                        
                        // 基於條件決定連線狀態，但更穩定
                        if (elevation < 10) {
                            newStatus = 'blocked'
                        } else if (signalStrength < -80) {
                            newStatus = 'lost'
                        } else {
                            // 更穩定的狀態分配：大部分為 active
                            const rand = Math.random()
                            if (rand < 0.02) newStatus = 'handover'  // 2% 機率
                            else if (rand < 0.03) newStatus = 'establishing'  // 1% 機率
                            else newStatus = 'active' // 97% 機率
                        }
                        
                        // 更新狀態記錄
                        connectionStates.set(connectionKey, { 
                            status: newStatus, 
                            lastChange: currentTime 
                        })
                        
                        return newStatus
                    }
                    
                    const connectionStatus = getStableConnectionStatus(satellite, uav)
                    
                    newConnections.push({
                        id: `conn_${uav.id}_${satellite.id}`,
                        satelliteId: satellite.id,
                        uavId: uav.id,
                        beamId: `beam_${satellite.id}_${uav.id}`,
                        status: connectionStatus,
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
            
            // 傳遞連線數據給父組件（用於 UI 面板顯示）
            if (onConnectionsUpdate) {
                onConnectionsUpdate(newConnections)
            }

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
        const interval = setInterval(analyzeConnections, 15000) // 每15秒更新，減少閃爍

        return () => {
            clearInterval(interval)
            // 清理連線狀態記錄
            setConnectionStates(new Map())
        }
    }, [devices, enabled, satellites])

    if (!enabled) return null

    return (
        <>
            {/* 衛星-UAV 連接線 */}
            <ConnectionLinksVisualization 
                connections={connections} 
                devices={devices} 
                satellites={processedSatellites}
                enabled={enabled}
            />
            
            {/* 移除 3D 場景中的連接狀態顯示，改為在 UI 面板中顯示 */}
            
            {/* 簡化的連接質量指示器 - 只顯示前3個，沒有文字 */}
            {connections.slice(0, 3).map((connection) => (
                <ConnectionQualityIndicator
                    key={connection.id}
                    connection={connection}
                    devices={devices}
                    enabled={enabled}
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
    enabled: boolean
}> = ({ connections, devices, satellites, enabled }) => {
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

    // 修復：實時同步衛星位置，直接讀取 groupRef 位置而非通過 scene 遍歷
    useFrame(() => {
        if (!enabled) return
        
        const newPositions = new Map<string, [number, number, number]>()
        
        // 直接查找衛星群組並讀取其當前位置
        scene.traverse((child) => {
            // 修復：更寬鬆的衛星檢測條件，支援多種ID格式
            if (child.type === 'Group') {
                let satelliteId = null
                
                // 方法1：使用 userData.satelliteId
                if (child.userData?.satelliteId) {
                    satelliteId = child.userData.satelliteId
                }
                
                // 方法2：從 name 中提取 ID
                if (!satelliteId && child.name && child.name.startsWith('satellite-')) {
                    satelliteId = child.name.replace('satellite-', '')
                }
                
                // 如果找到有效的衛星ID，記錄位置
                if (satelliteId) {
                    const currentPos = child.position
                    newPositions.set(satelliteId, [currentPos.x, currentPos.y, currentPos.z])
                }
            }
        })
        
        // 即時更新位置，移除變化檢測以確保實時同步
        if (newPositions.size > 0) {
            setSatellitePositions(newPositions)
        }
    })

    // 如果功能被關閉，不渲染任何連接線
    if (!enabled) {
        return null
    }

    return (
        <>
            {connections.map((connection) => {
                const uav = devices.find(d => d.id === connection.uavId)
                if (!uav) return null

                // 修復：優先使用實時位置，但提供備用方案以確保連線可见
                let satellitePos = satellitePositions.get(connection.satelliteId)
                
                // 如果沒有實時位置，使用計算得出的基礎位置作為備用
                if (!satellitePos) {
                    // 尋找對應的衛星配置數據
                    const satelliteConfig = satellites.find(sat => sat.id === connection.satelliteId)
                    if (satelliteConfig) {
                        // 使用基礎位置計算作為備用
                        const PI_DIV_180 = Math.PI / 180
                        const GLB_SCENE_SIZE = 1200
                        const MIN_SAT_HEIGHT = 200
                        const MAX_SAT_HEIGHT = 400
                        
                        const elevationRad = satelliteConfig.elevation * PI_DIV_180
                        const azimuthRad = satelliteConfig.azimuth * PI_DIV_180
                        const distance = GLB_SCENE_SIZE * 0.4
                        
                        const x = distance * Math.sin(azimuthRad)
                        const y = distance * Math.cos(azimuthRad)
                        const z = MIN_SAT_HEIGHT + (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * Math.sin(elevationRad)
                        
                        satellitePos = [x, z, y]
                    } else {
                        return null // 如果連配置都沒有，才跳過
                    }
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

// 精簡的連接質量指示器 - 只顯示核心指標
const ConnectionQualityIndicator: React.FC<{
    connection: SatelliteConnection
    devices: any[]
    enabled: boolean
}> = ({ connection, devices, enabled }) => {
    const uav = devices.find(d => d.id === connection.uavId)
    if (!uav || !enabled) return null

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return '#00ff00'
            case 'handover': return '#ffaa00'
            case 'establishing': return '#0088ff'
            case 'lost': return '#ff0000'
            case 'blocked': return '#666666'
            default: return '#ffffff'
        }
    }

    const getStatusText = (status: string) => {
        switch (status) {
            case 'active': return '✓'
            case 'handover': return '🔄'
            case 'establishing': return '🔗'
            case 'lost': return '✗'
            case 'blocked': return '🚫'
            default: return '?'
        }
    }

    return (
        <group position={[
            uav.position_x || 0,
            (uav.position_z || 0) + 30,
            uav.position_y || 0
        ]}>
            <Text
                position={[0, 0, 0]}
                fontSize={4}
                color={getStatusColor(connection.status)}
                anchorX="center"
                anchorY="middle"
            >
                {getStatusText(connection.status)}
            </Text>
        </group>
    )
}

// 移除切換事件可視化以提升性能

// 連接狀態顯示已移至 UI 面板，不再在 3D 場景中顯示
const ConnectionStatusDisplay: React.FC<{ metrics: any; enabled: boolean }> = ({ metrics, enabled }) => {
    // 不再渲染 3D 文字，改為使用 HTML UI 面板
    return null
}

// 移除信號質量監控和多普勒效應可視化以提升性能

export default SatelliteUAVConnection