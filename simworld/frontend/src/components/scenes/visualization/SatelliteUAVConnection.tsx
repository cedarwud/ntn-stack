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
    const [satellitePositions, setSatellitePositions] = useState<Map<string, [number, number, number]>>(new Map()) // 修復：在主組件中定義
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
            
            // 使用與 StaticSatelliteManager 相同的真實衛星配置
            const realSatelliteConfigs = [
                { id: '45417', name: 'STARLINK-1318', elevation: 75, azimuth: 45 },
                { id: '46045', name: 'STARLINK-1297', elevation: 68, azimuth: 120 },
                { id: '46059', name: 'STARLINK-1326', elevation: 72, azimuth: 200 },
                { id: '44720', name: 'STARLINK-1089', elevation: 45, azimuth: 90 },
                { id: '45074', name: 'STARLINK-1245', elevation: 52, azimuth: 180 },
                { id: '45395', name: 'STARLINK-1432', elevation: 38, azimuth: 270 },
                { id: '45778', name: 'STARLINK-1567', elevation: 25, azimuth: 30 },
                { id: '46060', name: 'STARLINK-1612', elevation: 18, azimuth: 300 },
                { id: '45416', name: 'STARLINK-1401', elevation: 32, azimuth: 150 },
                { id: '45057', name: 'STARLINK-1234', elevation: 28, azimuth: 240 }
            ]
            
            satelliteConnections = realSatelliteConfigs.map((config, index) => ({
                id: config.id,
                norad_id: config.id,
                name: config.name,
                position: null,
                elevation: config.elevation,
                azimuth: config.azimuth,
                orbitIndex: index,
                isAlwaysVisible: true
            }))
            
            console.log('🛰️ 使用完全靜態衛星配置，避免外部數據依賴和重新載入問題')
            
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
                // 重新設計：基於 UAV-衛星直線距離的換手決策
                // 獲取 UAV 當前位置（統一坐標系）
                const uavPos = [
                    uav.position_x || 0,      // X軸：東西方向
                    (uav.position_z || 0) + 10, // Y軸：高度（加10米偏移）
                    uav.position_y || 0       // Z軸：南北方向
                ]
                
                // 計算所有可見衛星的質量分數（仰角為主要因素）
                const satelliteQuality = satelliteConnections
                    .map(sat => {
                        const realTimePos = satellitePositions.get(sat.id)
                        if (!realTimePos) return null
                        
                        const [x, y, z] = realTimePos // 衛星位置：(x, height, y)
                        
                        // 計算相對於UAV的仰角（修正坐標映射）
                        const dx = x - uavPos[0]        // X方向差異
                        const dy = y - uavPos[1]        // 高度差異（衛星height - UAV高度）
                        const dz = z - uavPos[2]        // Z方向差異
                        const horizontalDist = Math.sqrt(dx*dx + dz*dz) // 水平距離只考慮X和Z
                        const elevation = Math.atan2(dy, horizontalDist) * (180 / Math.PI) // 仰角 = 高度差/水平距離
                        
                        // 修正：更嚴格的仰角檢查，避免負仰角連線
                        if (elevation <= 15) {
                            return null // 仰角必須大於15度才考慮，避免水平線以下連線
                        }
                        
                        // 計算3D直線距離（修正坐標）
                        const distance3D = Math.sqrt(dx*dx + dy*dy + dz*dz)
                        
                        // 修正：仰角越高質量越好的邏輯
                        // 仰角是主要因素（85%權重），距離是次要因素（15%權重）
                        const elevationScore = Math.pow(elevation / 90, 1.5) * 100 // 仰角1.5次方，讓高仰角更優先
                        const distanceScore = Math.max(0, (1500 - distance3D) / 1500 * 20) // 距離越近越好，1500km基準
                        const qualityScore = elevationScore * 0.85 + distanceScore * 0.15 // 仰角85%權重
                        
                        return {
                            satellite: sat,
                            distance: distance3D,
                            position: realTimePos,
                            elevation: elevation,
                            qualityScore: qualityScore
                        }
                    })
                    .filter(Boolean) // 移除 null 值
                    .sort((a, b) => b.qualityScore - a.qualityScore) // 按質量分數從高到低排序
                
                if (satelliteQuality.length < 2) {
                    console.log(`⚠️ UAV ${uav.id}: 可用衛星不足 (${satelliteQuality.length}/2) - 無法進行換手`)
                    return
                }
                
                
                // 當前最佳衛星（仰角最高的）作為穩定連線
                const currentBest = satelliteQuality[0]
                const nextBest = satelliteQuality[1]
                
                // 調試：只對第一個UAV顯示前兩顆衛星的質量分析
                if (index === 0 && Math.random() < 0.1) { // 10%機率顯示，避免過多日誌
                    console.log(`UAV ${uav.id} 衛星排序:`, 
                               `最佳: ${currentBest.satellite.name} (仰角:${currentBest.elevation.toFixed(1)}°, 質量:${currentBest.qualityScore.toFixed(1)}), `,
                               `次佳: ${nextBest.satellite.name} (仰角:${nextBest.elevation.toFixed(1)}°, 質量:${nextBest.qualityScore.toFixed(1)})`)
                }
                
                // 修正：更合理的換手決策閾值，優先選擇高仰角衛星
                const QUALITY_DIFFERENCE_THRESHOLD = 15 // 質量分數差異閾值
                const MIN_ELEVATION_THRESHOLD = 30 // 最小可接受仰角
                const PREFERRED_ELEVATION_THRESHOLD = 50 // 偏好仰角閾值
                
                const shouldHandover = 
                    currentBest.elevation < MIN_ELEVATION_THRESHOLD || // 當前衛星仰角過低，必須換手
                    (nextBest.elevation > PREFERRED_ELEVATION_THRESHOLD && 
                     nextBest.elevation > currentBest.elevation + 10) // 或有仰角明顯更高的衛星
                
                
                // 換手狀態管理
                const connectionKey = `uav_${uav.id}`
                const currentState = connectionStates.get(connectionKey)
                
                if (!currentState) {
                    // 初始化：連接到最佳衛星
                    connectionStates.set(connectionKey, {
                        status: 'stable',
                        currentSatellite: currentBest.satellite.id,
                        lastChange: currentTime,
                        handoverPhase: 'stable'
                    })
                    console.log(`🔗 UAV ${uav.id} 初始連接: ${currentBest.satellite.name} (仰角: ${currentBest.elevation.toFixed(1)}°)`)
                } else {
                    const timeSinceLastChange = currentTime - currentState.lastChange
                    const HANDOVER_INTERVAL = 8000 // 8秒間隔，更快觸發換手
                    
                    // 檢查當前連接的衛星質量
                    const currentConnectedSat = satelliteQuality.find(s => s.satellite.id === currentState.currentSatellite)
                    const elevationDifference = currentConnectedSat ? currentBest.elevation - currentConnectedSat.elevation : 50
                    
                    // 調試：顯示換手決策信息（減少頻率）
                    if (index === 0 && Math.random() < 0.02) { // 2%機率顯示
                        console.log(`UAV ${uav.id} 換手檢查:`, 
                                   `時間間隔: ${(timeSinceLastChange/1000).toFixed(1)}s, `,
                                   `當前衛星: ${currentConnectedSat?.satellite.name}(${currentConnectedSat?.elevation.toFixed(1)}°), `,
                                   `最佳衛星: ${currentBest.satellite.name}(${currentBest.elevation.toFixed(1)}°), `,
                                   `仰角差: ${elevationDifference.toFixed(1)}°, `,
                                   `需要換手: ${timeSinceLastChange > HANDOVER_INTERVAL && 
                                               currentBest.satellite.id !== currentState.currentSatellite &&
                                               (elevationDifference > 15 || 
                                                (currentConnectedSat && currentConnectedSat.elevation < MIN_ELEVATION_THRESHOLD))}`)
                    }
                    
                    // 換手決策：強制觸發換手進行測試
                    const shouldForceHandover = timeSinceLastChange > HANDOVER_INTERVAL && 
                                               (elevationDifference > 5 || // 降低到5度差異
                                                Math.random() < 0.3 || // 提高到30%隨機機會
                                                (nextBest && nextBest.satellite.id !== currentState.currentSatellite)) // 或有不同的次佳衛星
                    
                    if (shouldForceHandover) {
                        // 選擇換手目標：如果當前最佳還是同一顆，就換到次佳衛星
                        const handoverTarget = (currentBest.satellite.id === currentState.currentSatellite && nextBest) 
                                              ? nextBest.satellite 
                                              : currentBest.satellite
                        
                        // 開始換手流程
                        connectionStates.set(connectionKey, {
                            status: 'handover',
                            currentSatellite: currentState.currentSatellite, // 保持當前衛星
                            targetSatellite: handoverTarget.id, // 目標衛星
                            lastChange: currentTime,
                            handoverStartTime: currentTime,
                            handoverPhase: 'preparing'
                        })
                        
                        console.log(`🔄 UAV ${uav.id} 開始換手: ${currentConnectedSat?.satellite.name} → ${handoverTarget.name}`)
                        console.log(`   仰角變化: ${currentConnectedSat?.elevation.toFixed(1)}° → ${handoverTarget === currentBest.satellite ? currentBest.elevation.toFixed(1) : nextBest.elevation.toFixed(1)}°`)
                        
                    }
                    
                    // 換手進度管理
                    if (currentState.status === 'handover' && currentState.handoverStartTime) {
                        const handoverDuration = currentTime - currentState.handoverStartTime
                        const HANDOVER_COMPLETE_TIME = 5000 // 5秒完成換手
                        
                        if (handoverDuration > HANDOVER_COMPLETE_TIME) {
                            // 完成換手：確保切換到目標衛星
                            const oldSat = satelliteQuality.find(s => s.satellite.id === currentState.currentSatellite)?.satellite.name || 'Unknown'
                            const newSatId = currentState.targetSatellite || currentBest.satellite.id
                            const newSat = satelliteQuality.find(s => s.satellite.id === newSatId)?.satellite.name || 'Unknown'
                            
                            // 確保目標衛星存在且有效
                            if (newSatId && satelliteQuality.find(s => s.satellite.id === newSatId)) {
                                connectionStates.set(connectionKey, {
                                    status: 'stable',
                                    currentSatellite: newSatId, // 確實切換到目標衛星
                                    lastChange: currentTime,
                                    handoverPhase: 'stable'
                                })
                                
                                console.log(`✅ UAV ${uav.id} 換手完成: ${oldSat} → ${newSat} (ID: ${currentState.currentSatellite} → ${newSatId})`)
                            } else {
                                // 如果目標衛星無效，回退到最佳衛星
                                connectionStates.set(connectionKey, {
                                    status: 'stable',
                                    currentSatellite: currentBest.satellite.id,
                                    lastChange: currentTime,
                                    handoverPhase: 'stable'
                                })
                                console.log(`⚠️ UAV ${uav.id} 換手回退到最佳衛星: ${currentBest.satellite.name}`)
                            }
                        }
                    }
                }
                
                // 清理的連線邏輯：確保每個 UAV 只有正確的連線
                const activeState = connectionStates.get(connectionKey)
                
                if (activeState) {
                    if (activeState.status === 'handover' && activeState.targetSatellite) {
                        // 換手進行中：同時顯示舊連線和新連線（Make-Before-Break）
                        const currentSat = satelliteQuality.find(s => s.satellite.id === activeState.currentSatellite)?.satellite
                        const targetSat = satelliteQuality.find(s => s.satellite.id === activeState.targetSatellite)?.satellite
                        
                        // 計算換手進度
                        const handoverDuration = currentTime - (activeState.handoverStartTime || currentTime)
                        const progress = Math.min(1, handoverDuration / 5000) // 5秒完成換手
                        
                        if (currentSat && progress < 0.8) {
                            // 舊連線：正在斷開（80%進度後不再顯示）
                            const oldConnection = createConnection(uav, currentSat, 'disconnecting', 'current', progress, activeState)
                            if (oldConnection) newConnections.push(oldConnection)
                        }
                        
                        if (targetSat) {
                            // 新連線：正在建立
                            const newConnection = createConnection(uav, targetSat, 'establishing', 'target', progress, activeState)
                            if (newConnection) newConnections.push(newConnection)
                        }
                    } else {
                        // 穩定狀態：只顯示當前連線的衛星
                        const activeSatellite = satelliteQuality.find(s => s.satellite.id === activeState.currentSatellite)?.satellite || currentBest.satellite
                        const stableConnection = createConnection(uav, activeSatellite, 'active', 'current', 1.0, activeState)
                        if (stableConnection) newConnections.push(stableConnection)
                    }
                }
            })
            
            // 基於實際距離的連接創建函數
            function createConnection(uav: any, satellite: any, status: string, type: 'current' | 'target', progress: number, handoverState?: any): SatelliteConnection {
                // 獲取實時衛星位置和 UAV 位置（統一坐標系）
                const realTimePos = satellitePositions.get(satellite.id)
                const uavPos = [
                    uav.position_x || 0,      // X軸：東西方向
                    (uav.position_z || 0) + 10, // Y軸：高度（加10米偏移）
                    uav.position_y || 0       // Z軸：南北方向
                ]
                
                let distance = 1200 // 預設距離
                let elevation = 45 // 預設仰角
                let azimuth = 0
                
                if (realTimePos) {
                    const [x, y, z] = realTimePos // 衛星位置：(x, height, y)
                    
                    // 計算實際的 UAV-衛星直線距離（修正坐標映射）
                    const dx = x - uavPos[0]        // X方向差異
                    const dy = y - uavPos[1]        // 高度差異（衛星height - UAV高度）
                    const dz = z - uavPos[2]        // Z方向差異
                    distance = Math.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    // 修正：正確計算相對於UAV的仰角
                    const horizontalDist = Math.sqrt(dx*dx + dz*dz) // 水平距離只考慮X和Z
                    elevation = Math.atan2(dy, horizontalDist) * (180 / Math.PI) // 仰角 = 高度差/水平距離
                    
                    // 確保仰角不會為負值，且強制最低15度
                    elevation = Math.max(15, elevation)
                    
                    // 計算方位角（基於XZ平面）
                    azimuth = Math.atan2(dx, dz) * (180 / Math.PI)
                }
                
                // 基於仰角的信號質量計算（仰角越高信號越強）
                const signalStrength = Math.max(-100, -40 - (90 - elevation) * 0.8) // 仰角90度最佳
                const snr = Math.max(5, 40 - (90 - elevation) * 0.4)
                
                // 性能基於仰角計算
                const elevationQuality = Math.max(0, Math.min(1, elevation / 90)) // 仰角質量 (0-1)
                const throughput = 50 + elevationQuality * 100
                const latency = 20 + (1 - elevationQuality) * 40
                
                return {
                    id: `conn_${type}_${uav.id}_${satellite.id}_${Math.floor(currentTime / 1000)}`,
                    satelliteId: String(satellite.id),
                    uavId: uav.id,
                    beamId: `beam_${satellite.id}_${uav.id}`,
                    status: status as any,
                    connectionType: type,
                    quality: {
                        signalStrength: Math.round(signalStrength * 10) / 10,
                        snr: Math.round(snr * 10) / 10,
                        elevation: Math.round(elevation * 10) / 10,
                        azimuth: Math.round(azimuth * 10) / 10,
                        distance: Math.round(distance),
                        doppler: Math.round((distance - 600) * 0.05) // 基於距離變化的多普勒效應
                    },
                    performance: {
                        throughput: Math.round(throughput * 10) / 10,
                        latency: Math.round(latency * 10) / 10,
                        jitter: Math.round((1 - elevationQuality) * 8 * 10) / 10,
                        packetLoss: Math.round((1 - elevationQuality) * 3 * 100) / 100
                    },
                    beam: {
                        beamWidth: 0.3 + elevationQuality * 0.5,
                        eirp: 50 + elevationQuality * 15,
                        frequency: 12.0 + (satellite.orbitIndex || 0) * 0.5,
                        polarization: ((satellite.orbitIndex || 0) % 2) === 0 ? 'LHCP' : 'RHCP'
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
        const interval = setInterval(analyzeConnections, 1000) // 每1秒更新，配合加速的衛星運動

        return () => {
            clearInterval(interval)
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
                satellitePositions={satellitePositions}
                setSatellitePositions={setSatellitePositions}
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
    satellitePositions: Map<string, [number, number, number]>
    setSatellitePositions: React.Dispatch<React.SetStateAction<Map<string, [number, number, number]>>>
}> = ({ connections, devices, satellites, enabled, satellitePositions, setSatellitePositions }) => {
    const { scene } = useThree()
    
    // 直觀的雙連線視覺效果
    const getConnectionVisualProps = (connection: any) => {
        const status = connection.status
        const type = connection.connectionType
        const now = Date.now()
        
        switch (status) {
            case 'active':
                // 穩定連線：粗實線，亮綠色
                return {
                    color: '#00ff00',
                    opacity: 1.0,
                    dashed: false,
                    lineWidth: 5,
                    label: '當前連線'
                }
                
            case 'establishing':
                // 新建立連線：逐漸變粗變亮的藍色虛線
                const buildProgress = Math.min(1, (now % 3000) / 3000)
                return {
                    color: '#00aaff',
                    opacity: 0.4 + 0.6 * buildProgress,
                    dashed: true,
                    lineWidth: 2 + 3 * buildProgress,
                    label: '建立中'
                }
                
            case 'disconnecting':
                // 斷開連線：逐漸變細變暗的紅色虛線
                const fadeProgress = (now % 3000) / 3000
                return {
                    color: '#ff6600',
                    opacity: 1.0 - 0.6 * fadeProgress,
                    dashed: true,
                    lineWidth: 5 - 3 * fadeProgress,
                    label: '斷開中'
                }
                
            case 'handover':
                // 換手狀態：閃爍的橙色
                const pulse = 0.6 + 0.4 * Math.sin(now / 200)
                return {
                    color: '#ff8800',
                    opacity: pulse,
                    dashed: true,
                    lineWidth: 4,
                    label: '換手中'
                }
                
            default:
                return {
                    color: '#ffffff',
                    opacity: 0.5,
                    dashed: false,
                    lineWidth: 2,
                    label: '未知'
                }
        }
    }

    // 修復：實時同步衛星位置，直接讀取 groupRef 位置而非通過 scene 遍歷
    useFrame(() => {
        if (!enabled) return
        
        const newPositions = new Map<string, [number, number, number]>()
        
        // 直接查找衛星群組並讀取其當前位置
        scene.traverse((child) => {
            // 修復：更精確的衛星檢測條件，支援多種ID格式
            if (child.type === 'Group' && child.userData && child.name) {
                let satelliteId = null
                
                // 方法1：優先使用 userData.satelliteId (最可靠)
                if (child.userData.satelliteId !== undefined) {
                    satelliteId = String(child.userData.satelliteId)
                }
                
                // 方法2：從 name 中提取 ID (備用方案)
                if (!satelliteId && child.name && child.name.startsWith('satellite-')) {
                    satelliteId = child.name.replace('satellite-', '')
                }
                
                // 調試：記錄衛星群組發現（減少頻率）
                if (Math.random() < 0.002 && child.name && satelliteId) { // 0.2%機率顯示，只顯示有效的衛星
                    console.log(`🔍 發現衛星群組: name="${child.name}", satelliteId="${satelliteId}"`)
                }
                
                // 如果找到有效的衛星ID且有實際位置，記錄位置（不檢查visible狀態）
                if (satelliteId && child.position) {
                    const currentPos = child.position
                    // 確保位置不是默認的 [0,0,0]，並且記錄所有衛星位置（包括不可見的）
                    if (currentPos.x !== 0 || currentPos.y !== 0 || currentPos.z !== 0) {
                        newPositions.set(satelliteId, [currentPos.x, currentPos.y, currentPos.z])
                    }
                }
            }
        })
        
        // 調試：監控衛星位置變化（減少頻率）
        if (Math.random() < 0.005) { // 0.5%機率顯示
            console.log(`🔍 衛星位置同步: 找到 ${newPositions.size} 個衛星 (${newPositions.size})`, Array.from(newPositions.keys()))
        }
        
        
        // 即時更新位置，確保實時同步
        setSatellitePositions(newPositions)
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

                // 獲取連接線的視覺屬性
                const visualProps = getConnectionVisualProps(connection)

                // 優先使用實時位置，提供多層備用方案
                let satellitePos = satellitePositions.get(connection.satelliteId)
                
                if (!satellitePos) {
                    // 備用方案1：從 processedSatellites 配置中查找
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
                        // 備用方案2：為測試衛星或使用預設位置
                        let config;
                        if (connection.satelliteId.startsWith('test-sat-')) {
                            const testIndex = parseInt(connection.satelliteId.split('-')[2]) || 0
                            config = { elevation: 60 - testIndex * 15, azimuth: testIndex * 120 }
                        } else {
                            const satelliteIndex = parseInt(connection.satelliteId) || 0
                            const defaultConfigs = [
                                { elevation: 65, azimuth: 180 },
                                { elevation: 45, azimuth: 220 },
                                { elevation: 55, azimuth: 140 }
                            ]
                            config = defaultConfigs[satelliteIndex % defaultConfigs.length]
                        }
                        
                        const PI_DIV_180 = Math.PI / 180
                        const GLB_SCENE_SIZE = 1200
                        const MIN_SAT_HEIGHT = 200
                        const MAX_SAT_HEIGHT = 400
                        
                        const elevationRad = config.elevation * PI_DIV_180
                        const azimuthRad = config.azimuth * PI_DIV_180
                        const distance = GLB_SCENE_SIZE * 0.4
                        
                        const x = distance * Math.sin(azimuthRad)
                        const y = distance * Math.cos(azimuthRad)
                        const z = MIN_SAT_HEIGHT + (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * Math.sin(elevationRad)
                        
                        satellitePos = [x, z, y]
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