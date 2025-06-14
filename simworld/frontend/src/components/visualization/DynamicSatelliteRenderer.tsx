import React, { useMemo, useRef, useEffect, useState, useCallback } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text, Line } from '@react-three/drei'
import { Vector3 } from 'three'
import StaticModel from '../scenes/StaticModel'
import { ApiRoutes } from '../../config/apiRoutes'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { SATELLITE_CONFIG } from '../../config/satellite.config'

interface DynamicSatelliteRendererProps {
    satellites: VisibleSatelliteInfo[]
    enabled: boolean
    currentConnection?: any
    predictedConnection?: any
    showLabels?: boolean
    speedMultiplier?: number
    showOrbitTracks?: boolean
}

interface SatelliteOrbitPoint {
    timestamp: number
    position: [number, number, number]
    elevation: number
    azimuth: number
}

interface AnimatedSatellite extends VisibleSatelliteInfo {
    animationState: {
        currentPosition: [number, number, number]
        targetPosition: [number, number, number]
        orbitPoints: SatelliteOrbitPoint[]
        lastUpdateTime: number
        orbitIndex: number
        velocity: [number, number, number]
        orbitPhase?: number  // 軌道相位（秒）
        independentTime?: number  // 獨立時間週期（秒）
    }
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

const DynamicSatelliteRenderer: React.FC<DynamicSatelliteRendererProps> = ({
    satellites,
    enabled,
    currentConnection,
    predictedConnection,
    showLabels = true,
    speedMultiplier = SATELLITE_CONFIG.ANIMATION_SPEED,
    showOrbitTracks = SATELLITE_CONFIG.SHOW_ORBIT_TRAILS
}) => {
    const [animatedSatellites, setAnimatedSatellites] = useState<AnimatedSatellite[]>([])
    const animationRef = useRef<{ [key: string]: AnimatedSatellite }>({})
    const orbitCacheRef = useRef<{ [key: string]: { data: SatelliteOrbitPoint[], timestamp: number } }>({})
    const lastFetchTime = useRef<number>(0)

    // 計算衛星在3D場景中的位置
    const calculateScenePosition = (elevation: number, azimuth: number): [number, number, number] => {
        const PI_DIV_180 = Math.PI / 180
        const GLB_SCENE_SIZE = 1200
        const MIN_SAT_HEIGHT = 200
        const MAX_SAT_HEIGHT = 600  // 增加最大高度範圍
        
        const elevationRad = elevation * PI_DIV_180
        const azimuthRad = azimuth * PI_DIV_180
        
        // 計算水平距離（仰角越高，水平距離越小）
        const range = GLB_SCENE_SIZE * 0.4
        const horizontalDist = range * Math.cos(elevationRad)
        
        // X-Z平面是水平面，Y是垂直高度
        const x = horizontalDist * Math.sin(azimuthRad)
        const z = horizontalDist * Math.cos(azimuthRad)  // 注意：z軸，不是y軸
        
        // Y軸是高度，仰角越高，衛星在場景中的高度越高
        const y = MIN_SAT_HEIGHT + (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * Math.sin(elevationRad)

        return [x, y, z]  // [x, 高度, z] 而不是 [x, 高度, y]
    }

    // 獲取衛星軌跡數據（帶緩存）
    const fetchSatelliteOrbit = async (satelliteId: string): Promise<SatelliteOrbitPoint[]> => {
        const now = Date.now()
        const cacheKey = satelliteId
        const CACHE_DURATION = 5 * 60 * 1000 // 5分鐘緩存
        
        // 檢查緩存
        if (orbitCacheRef.current[cacheKey] && 
            (now - orbitCacheRef.current[cacheKey].timestamp) < CACHE_DURATION) {
            return orbitCacheRef.current[cacheKey].data
        }
        
        try {
            const response = await fetch(
                `/api/v1/satellite-ops/orbit/${satelliteId}?duration=${SATELLITE_CONFIG.TRAJECTORY_PREDICTION_TIME}&step=${SATELLITE_CONFIG.ORBIT_CALCULATION_STEP}`
            )
            
            if (!response.ok) {
                throw new Error(`Failed to fetch orbit for satellite ${satelliteId}`)
            }
            
            const orbitData = await response.json()
            
            // 將軌跡數據轉換為3D場景坐標
            const allOrbitPoints = orbitData.points.map((point: any, index: number) => {
                const position = calculateScenePosition(point.elevation_deg, point.azimuth_deg)
                
                return {
                    timestamp: new Date(point.timestamp).getTime(),
                    position,
                    elevation: point.elevation_deg,
                    azimuth: point.azimuth_deg
                }
            })
            
            // 用於動畫的完整軌跡（包括地平線以下）
            const orbitPoints = allOrbitPoints
            
            // 緩存結果
            orbitCacheRef.current[cacheKey] = {
                data: orbitPoints,
                timestamp: now
            }
            return orbitPoints
        } catch (error) {
            console.warn(`Failed to fetch orbit for satellite ${satelliteId}:`, error)
            return []
        }
    }

    // 初始化衛星動畫狀態
    useEffect(() => {
        if (!enabled || !satellites || satellites.length === 0) {
            setAnimatedSatellites([])
            animationRef.current = {}
            return
        }

        const initializeAnimations = async () => {
            const newAnimatedSatellites: AnimatedSatellite[] = []
            
            for (const satellite of satellites) {
                const satelliteKey = satellite.norad_id?.toString() || satellite.name
                
                // 檢查是否已經初始化過這個衛星
                if (animationRef.current[satelliteKey]) {
                    newAnimatedSatellites.push(animationRef.current[satelliteKey])
                    continue
                }
                
                const currentPosition = calculateScenePosition(satellite.elevation_deg, satellite.azimuth_deg)
                
                // 暫時不加載軌跡數據，使用空數組
                const orbitPoints: SatelliteOrbitPoint[] = []
                
                const animatedSat: AnimatedSatellite = {
                    ...satellite,
                    animationState: {
                        currentPosition,
                        targetPosition: currentPosition,
                        orbitPoints,
                        lastUpdateTime: Date.now(),
                        orbitIndex: 0,
                        velocity: [0, 0, 0]
                    }
                }
                
                newAnimatedSatellites.push(animatedSat)
                animationRef.current[satelliteKey] = animatedSat
            }
            
            setAnimatedSatellites(newAnimatedSatellites)
        }

        initializeAnimations()
    }, [satellites?.length, enabled]) // 只在衛星數量或enabled狀態改變時觸發

    // 升降軌跡動畫邏輯 - 模擬真實衛星過境
    useFrame((state, delta) => {
        if (!enabled || animatedSatellites.length === 0) return

        const frameSpeedMultiplier = speedMultiplier
        let hasUpdated = false

        // 更新每個衛星的動畫狀態
        for (const satellite of animatedSatellites) {
            const satelliteKey = satellite.norad_id?.toString() || satellite.name
            const animState = satellite.animationState
            
            // 全新的連續覆蓋邏輯
            const deltaTime = delta * frameSpeedMultiplier
            
            // 優化：減少同時可見衛星，專注換手研究
            const transitDuration = 12 * 60 // 12分鐘可見（縮短）
            const cycleDuration = 40 * 60   // 40分鐘完整週期（增加間隔）
            
            // 初始化每顆衛星的獨立時間偏移
            if (animState.independentTime === undefined) {
                // 使用衛星ID或名稱的hash來確定穩定的索引
                const satelliteHash = satellite.norad_id ? parseInt(satellite.norad_id) : satellite.name.length
                const stableIndex = satelliteHash % 3 // 確保0-2的索引
                
                // 3顆衛星，每顆錯開13.3分鐘（40分鐘÷3 = 13.3分鐘）
                const timeOffset = stableIndex * (40 / 3) * 60 // 轉為秒
                animationRef.current[satelliteKey].animationState.independentTime = timeOffset
                
                // 調試：輸出初始化信息
                console.log(`🚀 初始化衛星 ${satellite.name}: 穩定索引=${stableIndex}, 時間偏移=${(timeOffset/60).toFixed(1)}分鐘`)
            }
            
            // 更新獨立時間
            const currentIndependentTime = (animState.independentTime + deltaTime) % cycleDuration
            animationRef.current[satelliteKey].animationState.independentTime = currentIndependentTime
            
            // 判斷是否可見：前15分鐘可見，後15分鐘不可見
            const isVisible = currentIndependentTime < transitDuration
            
            if (isVisible) {
                // 在可見過境期間 - 實現升降軌跡
                const transitProgress = currentIndependentTime / transitDuration // 0 到 1
                
                // 每個衛星有不同的過境參數（基於ID生成穩定的參數）
                const satelliteHash = satellite.norad_id ? parseInt(satellite.norad_id) : satellite.name.length
                const startAzimuth = (satelliteHash * 45) % 360 // 起始方位角，增加分散度
                const azimuthSpan = 100 + (satelliteHash % 80) // 方位角跨度，增加變化
                const maxElevation = 30 + (satelliteHash % 45) // 最大仰角 30-75°，提高可見性
                
                // 方位角線性變化（從起始到結束）
                const currentAzimuth = (startAzimuth + azimuthSpan * transitProgress) % 360
                
                // 仰角拋物線變化（升起-到最高點-降落）
                const currentElevation = maxElevation * Math.sin(transitProgress * Math.PI)
                
                // 計算3D位置
                const newPosition = calculateScenePosition(currentElevation, currentAzimuth)
                
                if (animationRef.current[satelliteKey]) {
                    animationRef.current[satelliteKey].animationState.currentPosition = newPosition
                    animationRef.current[satelliteKey].elevation_deg = currentElevation
                    animationRef.current[satelliteKey].azimuth_deg = currentAzimuth
                    hasUpdated = true
                }
            } else {
                // 在不可見期間 - 衛星在地平線以下
                const hiddenDuration = cycleDuration - transitDuration
                const hiddenProgress = (currentIndependentTime - transitDuration) / hiddenDuration
                const satelliteHash = satellite.norad_id ? parseInt(satellite.norad_id) : satellite.name.length
                const hiddenElevation = -10 - (hiddenProgress * 30) // 地平線以下
                const hiddenAzimuth = ((satelliteHash * 30) % 360 + 240 * hiddenProgress) % 360
                
                // 計算地平線以下的位置（不渲染，但保持狀態）
                const newPosition = calculateScenePosition(hiddenElevation, hiddenAzimuth)
                
                if (animationRef.current[satelliteKey]) {
                    animationRef.current[satelliteKey].animationState.currentPosition = newPosition
                    animationRef.current[satelliteKey].elevation_deg = hiddenElevation
                    animationRef.current[satelliteKey].azimuth_deg = hiddenAzimuth
                    hasUpdated = true
                }
            }
        }

        // 觸發重新渲染
        if (hasUpdated) {
            setAnimatedSatellites(prev => {
                const updated = [...prev.map(sat => {
                    const key = sat.norad_id?.toString() || sat.name
                    return animationRef.current[key] || sat
                })]
                
                // 調試：每5秒輸出詳細時間狀態
                const now = Date.now()
                if (now % 5000 < 100) {
                    const visibleCount = updated.filter(sat => sat.elevation_deg > 0).length
                    const satDetails = updated.map(sat => {
                        const timeInCycle = (sat.animationState.independentTime || 0) / 60 // 轉為分鐘
                        const isVisible = sat.elevation_deg > 0 ? '✅' : '❌'
                        return `${sat.name}:${timeInCycle.toFixed(1)}min${isVisible}`
                    }).join(' | ')
                    console.log(`🛰️ 狀態 [${visibleCount}/3可見]: ${satDetails}`)
                }
                
                return updated
            })
        }
    })

    // 渲染衛星網格 - 需要響應animatedSatellites變化
    if (!enabled || !animatedSatellites || animatedSatellites.length === 0) {
        return null
    }

    const satelliteMeshes = animatedSatellites
        .filter(satellite => satellite.elevation_deg > 0) // 只渲染可見的衛星（地平線以上）
        .map((satellite, index) => {
            const isCurrent = currentConnection?.satelliteId === satellite.norad_id
            const isPredicted = predictedConnection?.satelliteId === satellite.norad_id
            
            const position = satellite.animationState.currentPosition
            
            let statusColor = '#ffffff'
            if (isCurrent) {
                statusColor = '#00ff00'
            } else if (isPredicted) {
                statusColor = '#ffaa00'
            }

            // 暫時移除軌跡線，專注於衛星移動
            const orbitTrackPoints: Vector3[] = []
        

        return (
            <group key={satellite.norad_id || `sat-${index}`}>
                {/* 衛星模型 */}
                <StaticModel
                    url={SATELLITE_MODEL_URL}
                    position={position}
                    scale={[SATELLITE_CONFIG.SAT_SCALE, SATELLITE_CONFIG.SAT_SCALE, SATELLITE_CONFIG.SAT_SCALE]}
                    pivotOffset={[0, 0, 0]}
                />
                
                {/* 狀態指示器 */}
                <mesh position={[position[0], position[1] + 15, position[2]]}>
                    <sphereGeometry args={[3, 8, 8]} />
                    <meshBasicMaterial
                        color={statusColor}
                        transparent
                        opacity={0.8}
                    />
                </mesh>
                
                {/* 軌跡線 */}
                {showOrbitTracks && orbitTrackPoints.length > 1 && (
                    <Line
                        points={orbitTrackPoints}
                        color={SATELLITE_CONFIG.TRAJECTORY_ADJUSTMENT?.TRACK_COLOR || '#4CAF50'}
                        transparent={true}
                        opacity={0.6}
                        lineWidth={3}
                    />
                )}
                
                {/* 衛星標籤 */}
                {showLabels && (
                    <Text
                        position={[position[0], position[1] + 25, position[2]]}
                        fontSize={4}
                        color={statusColor}
                        anchorX="center"
                        anchorY="middle"
                    >
                        {satellite.name}
                    </Text>
                )}
                
                {/* 仰角資訊 */}
                {(isCurrent || isPredicted) && (
                    <Text
                        position={[position[0], position[1] + 20, position[2]]}
                        fontSize={3}
                        color="#ffffff"
                        anchorX="center"
                        anchorY="middle"
                    >
                        {satellite.elevation_deg.toFixed(1)}°
                    </Text>
                )}
            </group>
        )
    })

    return <group>{satelliteMeshes}</group>
}

export default DynamicSatelliteRenderer