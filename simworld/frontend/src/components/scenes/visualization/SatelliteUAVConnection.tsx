import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import { Line } from '@react-three/drei'

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
    connectionType?: 'current' | 'new' // 新增：標記連接類型
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
                console.log('SatelliteUAVConnection 接收到的衛星數據:', satellites.length, '個衛星')
                satelliteConnections = satellites.slice(0, Math.min(5, satellites.length)).map((sat, index) => {
                    // 修復：確保 ID 生成與 SimplifiedSatellite 完全一致
                    const satelliteId = sat.norad_id || sat.id || `satellite_${index}`
                    
                    return {
                        id: satelliteId, // 使用統一的ID
                        norad_id: satelliteId, // 保持一致性
                        name: sat.name || `Satellite-${satelliteId}`,
                        position: null, // 完全依賴實時追蹤
                        elevation: sat.elevation_deg || 45,
                        azimuth: sat.azimuth_deg || index * 60,
                        velocity: [0, 0, 0]
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
            
            // 重新設計的換手邏輯：支援雙連接線和 Make-Before-Break
            const newConnections: SatelliteConnection[] = []
            const currentTime = Date.now()
            const handoverCycle = 45000 // 45秒一個換手週期
            const handoverProgress = (currentTime % handoverCycle) / handoverCycle
            
            // 時間階段定義（按照 process.md）
            const isStablePhase = handoverProgress >= 0 && handoverProgress <= 0.67     // 0-30秒：穩定期
            const isPreparePhase = handoverProgress > 0.67 && handoverProgress <= 0.78  // 30-35秒：準備期
            const isEstablishPhase = handoverProgress > 0.78 && handoverProgress <= 0.84 // 35-38秒：建立期
            const isSwitchPhase = handoverProgress > 0.84 && handoverProgress <= 0.89   // 38-40秒：切換期
            const isCompletePhase = handoverProgress > 0.89                             // 40-45秒：完成期
            
            uavs.forEach((uav, index) => {
                const baseIndex = index % satelliteConnections.length
                const currentSatIndex = baseIndex
                const nextSatIndex = (baseIndex + 1) % satelliteConnections.length
                
                const currentSat = satelliteConnections[currentSatIndex]
                const nextSat = satelliteConnections[nextSatIndex]
                
                // 根據階段創建相應的連接
                if (isStablePhase || isPreparePhase) {
                    // 穩定期和準備期：只有舊連接
                    if (currentSat) {
                        const status = isPreparePhase ? 'handover' : 'active'
                        newConnections.push(createConnection(uav, currentSat, status, 'current', handoverProgress))
                    }
                } else if (isEstablishPhase) {
                    // 建立期：舊連接 + 正在建立的新連接
                    if (currentSat) {
                        newConnections.push(createConnection(uav, currentSat, 'handover', 'current', handoverProgress))
                    }
                    if (nextSat) {
                        newConnections.push(createConnection(uav, nextSat, 'establishing', 'new', handoverProgress))
                    }
                } else if (isSwitchPhase) {
                    // 切換期：雙連接期（Make-Before-Break）
                    if (currentSat) {
                        newConnections.push(createConnection(uav, currentSat, 'lost', 'current', handoverProgress))
                    }
                    if (nextSat) {
                        newConnections.push(createConnection(uav, nextSat, 'establishing', 'new', handoverProgress))
                    }
                } else if (isCompletePhase) {
                    // 完成期：只有新連接
                    if (nextSat) {
                        newConnections.push(createConnection(uav, nextSat, 'active', 'new', handoverProgress))
                    }
                }
            })
            
            // 連接創建輔助函數
            function createConnection(uav: any, satellite: any, status: string, type: 'current' | 'new', progress: number): SatelliteConnection {
                const connectionKey = `${uav.id}_${satellite.id}`
                const stableHash = (str: string) => {
                    let hash = 0
                    for (let i = 0; i < str.length; i++) {
                        const char = str.charCodeAt(i)
                        hash = ((hash << 5) - hash) + char
                        hash = hash & hash
                    }
                    return Math.abs(hash)
                }
                
                const hash = stableHash(connectionKey)
                const signalBase = -65 + (hash % 10) - 5
                const elevation = satellite.elevation || 45
                const elevationBonus = Math.max(0, (elevation - 30) * 0.5)
                const finalSignalStrength = signalBase + elevationBonus
                
                return {
                    id: `conn_${type}_${uav.id}_${satellite.id}_${Math.floor(progress * 1000)}`,
                    satelliteId: satellite.id,
                    uavId: uav.id,
                    beamId: `beam_${satellite.id}_${uav.id}`,
                    status: status as any,
                    connectionType: type, // 標記連接類型
                    quality: {
                        signalStrength: finalSignalStrength,
                        snr: 25 + (hash % 10) - 5,
                        elevation: satellite.elevation,
                        azimuth: satellite.azimuth,
                        distance: 500 + (hash % 200),
                        doppler: 1000 + ((hash * 7) % 500) - 250
                    },
                    performance: {
                        throughput: 100 + (hash % 50),
                        latency: 20 + (hash % 10),
                        jitter: 3 + ((hash * 3) % 4),
                        packetLoss: (hash % 100) / 50
                    },
                    beam: {
                        beamWidth: 0.7 + ((hash % 30) / 100),
                        eirp: 60 + (hash % 10),
                        frequency: 13 + ((hash % 20) / 10),
                        polarization: (hash % 2) === 0 ? 'LHCP' : 'RHCP'
                    }
                }
            }
            
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
            
            {/* 移除3D場景中的連接質量指示器 - 所有資訊移至UI面板 */}
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
    
    // 獲取連接線的視覺屬性（顏色、透明度、虛實、粗細）
    const getConnectionVisualProps = (connection: any, handoverProgress: number) => {
        const status = connection.status
        const type = connection.connectionType
        
        // 基礎顏色設定
        let color = '#ffffff'
        let opacity = 1.0
        let dashed = false
        let lineWidth = 2
        
        switch (status) {
            case 'active':
                color = '#00ff00' // 綠色 = 穩定
                opacity = 1.0
                dashed = false
                lineWidth = 3
                break
                
            case 'handover':
                color = '#ffaa00' // 黃色 = 準備/警告
                // 準備期開始閃爍效果
                opacity = 0.7 + 0.3 * Math.sin(Date.now() / 200)
                dashed = false
                lineWidth = 2
                break
                
            case 'establishing':
                color = '#0088ff' // 藍色 = 建立中
                if (type === 'new') {
                    // 新連接：從虛線逐漸變實線
                    const establishProgress = handoverProgress > 0.78 ? (handoverProgress - 0.78) / 0.06 : 0
                    opacity = 0.3 + 0.7 * establishProgress
                    dashed = establishProgress < 0.5
                    lineWidth = 1 + 2 * establishProgress
                } else {
                    opacity = 0.8
                    dashed = true
                    lineWidth = 2
                }
                break
                
            case 'lost':
                color = '#666666' // 灰色 = 斷開中
                if (type === 'current') {
                    // 舊連接：逐漸淡出
                    const fadeProgress = handoverProgress > 0.84 ? (handoverProgress - 0.84) / 0.05 : 0
                    opacity = 1.0 - 0.7 * fadeProgress
                    dashed = true
                    lineWidth = 3 - 2 * fadeProgress
                }
                break
                
            case 'blocked':
                color = '#333333'
                opacity = 0.3
                dashed = true
                lineWidth = 1
                break
        }
        
        return { color, opacity, dashed, lineWidth }
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

                // 計算當前換手進度（用於動畫效果）
                const currentTime = Date.now()
                const handoverCycle = 45000
                const handoverProgress = (currentTime % handoverCycle) / handoverCycle

                // 獲取連接線的視覺屬性
                const visualProps = getConnectionVisualProps(connection, handoverProgress)

                // 優先使用實時位置，但提供備用方案
                let satellitePos = satellitePositions.get(connection.satelliteId)
                
                if (!satellitePos) {
                    const satelliteConfig = satellites.find(sat => sat.id === connection.satelliteId)
                    if (satelliteConfig) {
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
                        return null
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
                        color={visualProps.color}
                        lineWidth={visualProps.lineWidth}
                        dashed={visualProps.dashed}
                        transparent
                        opacity={visualProps.opacity}
                    />
                )
            })}
        </>
    )
}

// 移除波束覆蓋可視化以提升性能

// 移除 ConnectionQualityIndicator - 所有資訊移至UI面板

// 移除切換事件可視化以提升性能

// 連接狀態顯示已移至 UI 面板，不再在 3D 場景中顯示
const ConnectionStatusDisplay: React.FC<{ metrics: any; enabled: boolean }> = ({ metrics, enabled }) => {
    // 不再渲染 3D 文字，改為使用 HTML UI 面板
    return null
}

// 移除信號質量監控和多普勒效應可視化以提升性能

export default SatelliteUAVConnection