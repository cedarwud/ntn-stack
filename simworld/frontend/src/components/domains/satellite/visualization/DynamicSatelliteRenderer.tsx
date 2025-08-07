import React, { useRef, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import StaticModel from '../../../scenes/StaticModel'
import { ApiRoutes } from '../../../../config/apiRoutes'
import { SATELLITE_CONFIG } from '../../../../config/satellite.config'
import {
    realSatelliteDataManager,
    RealSatelliteInfo,
} from '../../../../services/realSatelliteService'
import {
    historicalTrajectoryService,
    SatelliteTrajectory,
    TrajectoryPoint,
} from '../../../../services/HistoricalTrajectoryService'

interface DynamicSatelliteRendererProps {
    satellites: Record<string, unknown>[]
    enabled: boolean
    currentConnection?: Record<string, unknown>
    predictedConnection?: Record<string, unknown>
    showLabels?: boolean
    speedMultiplier?: number
    // 🚀 新增：演算法結果對接接口
    algorithmResults?: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }
    // 🔗 新增：換手狀態信息
    handoverState?: {
        phase:
            | 'stable'
            | 'preparing'
            | 'establishing'
            | 'switching'
            | 'completing'
        currentSatelliteId: string | null
        targetSatelliteId: string | null
        progress: number
    }
    onSatelliteClick?: (satelliteId: string) => void
    // 🔗 新增：衛星位置回調，供 HandoverAnimation3D 使用
    onSatellitePositions?: (
        positions: Map<string, [number, number, number]>
    ) => void
}

interface SatelliteOrbit {
    id: string
    name: string
    azimuthShift: number
    transitDuration: number
    transitStartTime: number
    isTransiting: boolean
    isVisible: boolean
    nextAppearTime: number
    currentPosition: [number, number, number]
    // 新增：真實衛星數據
    realData?: RealSatelliteInfo
    signalStrength?: number
    elevation?: number
    azimuth?: number
    // 🚀 新增：真實軌跡數據
    trajectoryPoints?: [number, number, number][]
    // 🌍 新增：完整軌跡數據
    fullTrajectory?: SatelliteTrajectory
    currentTrajectoryPoint?: TrajectoryPoint
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

// 🚀 真實軌跡位置計算函數 - 基於歷史數據的軌跡插值
const calculateRealTrajectoryPosition = (
    currentTime: number,
    orbit: SatelliteOrbit,
    speedMultiplier: number
): { position: [number, number, number]; isVisible: boolean } => {
    // 優先使用完整的歷史軌跡數據
    if (
        orbit.fullTrajectory &&
        orbit.fullTrajectory.trajectory_points.length > 0
    ) {
        // 使用歷史軌跡服務進行插值
        const currentTimeSeconds =
            Date.now() / 1000 + currentTime * speedMultiplier
        const interpolatedPoint =
            historicalTrajectoryService.interpolatePosition(
                orbit.fullTrajectory,
                currentTimeSeconds
            )

        if (interpolatedPoint) {
            // 將真實軌跡點轉換為3D座標
            const position = historicalTrajectoryService.trajectoryPointTo3D(
                interpolatedPoint,
                1200, // 場景縮放
                600 // 高度縮放
            )

            return {
                position,
                isVisible: interpolatedPoint.elevation_deg > 0, // 只有在地平線以上才可見
            }
        }
    }

    // 備用：使用預計算的軌跡點
    if (orbit.trajectoryPoints && orbit.trajectoryPoints.length > 0) {
        const totalDuration = 600 // 10分鐘真實軌跡
        const adjustedTime = Math.max(0, currentTime * speedMultiplier)
        const cyclicTime = adjustedTime % totalDuration
        const pointInterval =
            totalDuration / (orbit.trajectoryPoints.length - 1)
        const pointIndex = Math.min(
            Math.floor(cyclicTime / pointInterval),
            orbit.trajectoryPoints.length - 1
        )
        const nextIndex = Math.min(
            pointIndex + 1,
            orbit.trajectoryPoints.length - 1
        )

        if (
            !orbit.trajectoryPoints[pointIndex] ||
            !orbit.trajectoryPoints[nextIndex]
        ) {
            return {
                position: orbit.currentPosition || [0, 50, 0],
                isVisible: false,
            }
        }

        // 線性插值
        const t = (cyclicTime % pointInterval) / pointInterval
        const pos1 = orbit.trajectoryPoints[pointIndex]
        const pos2 = orbit.trajectoryPoints[nextIndex]

        const interpolatedPosition: [number, number, number] = [
            pos1[0] + (pos2[0] - pos1[0]) * t,
            pos1[1] + (pos2[1] - pos1[1]) * t,
            pos1[2] + (pos2[2] - pos1[2]) * t,
        ]

        // 根據高度判斷可見性（低於地平線時不可見）
        const isVisible = interpolatedPosition[1] > 10

        return {
            position: interpolatedPosition,
            isVisible: isVisible,
        }
    }

    // Fallback: 使用原來的半圓弧軌道
    const totalOrbitPeriod = 21600
    const relativeTime = currentTime - orbit.transitStartTime
    const normalizedTime =
        ((relativeTime % totalOrbitPeriod) + totalOrbitPeriod) %
        totalOrbitPeriod
    const isInTransit = normalizedTime <= orbit.transitDuration

    if (!isInTransit) {
        return {
            position: [0, -200, 0] as [number, number, number],
            isVisible: false,
        }
    }

    const transitProgress = normalizedTime / orbit.transitDuration
    const azimuthShift = (orbit.azimuthShift * Math.PI) / 180
    const angle = transitProgress * Math.PI

    const baseRadius = 600
    const heightRadius = 300

    const x = baseRadius * Math.cos(angle) * Math.cos(azimuthShift)
    const z = baseRadius * Math.cos(angle) * Math.sin(azimuthShift)
    const y = Math.max(15, 80 + heightRadius * Math.sin(angle))

    return { position: [x, y, z], isVisible: y > 25 }
}

const DynamicSatelliteRenderer: React.FC<DynamicSatelliteRendererProps> = ({
    satellites,
    enabled,
    currentConnection,
    predictedConnection,
    showLabels = true,
    speedMultiplier = 1, // 固定為1x真實時間
    algorithmResults,
    handoverState,
    onSatelliteClick: _onSatelliteClick,
    onSatellitePositions,
}) => {
    const [orbits, setOrbits] = useState<SatelliteOrbit[]>([])
    const timeRef = useRef(0)
    const lastPositionsRef = useRef<Map<string, [number, number, number]>>(
        new Map()
    )

    // 🌍 獲取衛星ID列表 (未使用，保留以備將來使用)
    const _satelliteIds = satellites
        .map((sat) => sat.norad_id?.toString() || sat.id?.toString() || '')
        .filter((id) => id !== '')

    // 🚀 使用 satellite-ops 數據作為真實軌跡數據源
    const historicalTrajectories = new Map()
    const _trajectoriesLoading = false
    
    // 🌟 將 satellite-ops 數據轉換為軌跡格式
    useEffect(() => {
        if (!enabled || satellites.length === 0) return
        
        // 為每顆衛星創建基於真實數據的軌跡
        satellites.forEach((sat) => {
            const satelliteId = sat.norad_id?.toString() || sat.id?.toString()
            if (!satelliteId) return
            
            // 基於真實數據創建軌跡點
            const realTrajectory = {
                satellite_id: satelliteId,
                duration_hours: 1, // 1小時軌跡
                total_points: 120, // 每30秒一個點
                trajectory_points: Array.from({ length: 120 }, (_, i) => ({
                    timestamp: Date.now() / 1000 + i * 30,
                    latitude: sat.position?.latitude || sat.latitude || 0,
                    longitude: sat.position?.longitude || sat.longitude || 0,
                    altitude_km: sat.position?.altitude || sat.altitude || 550,
                    elevation_deg: sat.elevation_deg || sat.position?.elevation || 0,
                    azimuth_deg: sat.azimuth_deg || sat.position?.azimuth || 0,
                    distance_km: sat.distance_km || sat.position?.range || 0,
                    is_visible: sat.is_visible !== false
                }))
            }
            
            historicalTrajectories.set(satelliteId, realTrajectory)
        })
        
        console.log(`🛰️ 創建真實軌跡數據: ${historicalTrajectories.size} 顆衛星`)
    }, [enabled, satellites.length])

    // 演算法狀態對接 - 用於顯示後端演算法結果
    const [_algorithmHighlights, _setAlgorithmHighlights] = useState<{
        currentSatellite?: string
        predictedSatellite?: string
        handoverPath?: string[]
        algorithmStatus?: 'idle' | 'calculating' | 'handover_ready'
    }>({})

    // 真實衛星數據狀態
    const [realSatelliteMapping, setRealSatelliteMapping] = useState<
        Map<string, RealSatelliteInfo>
    >(new Map())
    
    // 使用 useRef 存儲最新的回調函數和數據，避免 useEffect 依賴問題
    const onSatellitePositionsRef = useRef(onSatellitePositions)
    const realSatelliteMappingRef = useRef(realSatelliteMapping)
    
    useEffect(() => {
        onSatellitePositionsRef.current = onSatellitePositions
    }, [onSatellitePositions])
    
    useEffect(() => {
        realSatelliteMappingRef.current = realSatelliteMapping
    }, [realSatelliteMapping])
    const [useRealData, _setUseRealData] = useState(true) // 預設使用真實數據疊加
    const [realDataStatus, setRealDataStatus] = useState<
        'loading' | 'success' | 'error' | 'stale'
    >('loading')

    // 更新真實衛星數據
    useEffect(() => {
        if (!enabled || !useRealData) return

        const updateRealData = () => {
            const mapping = realSatelliteDataManager.getAllMappings()
            const isDataFresh = realSatelliteDataManager.isDataFresh()

            // 使用 ref 避免在每次渲染時觸發狀態更新
            const prevMappingSize = realSatelliteMapping.size
            const newStatus =
                mapping.size > 0 ? (isDataFresh ? 'success' : 'stale') : 'error'

            // 只在數據實際變化時才更新狀態
            if (
                mapping.size !== prevMappingSize ||
                realDataStatus !== newStatus
            ) {
                setRealSatelliteMapping(mapping)
                setRealDataStatus(newStatus)
            }
        }

        // 立即更新一次
        updateRealData()

        // 定期檢查更新 - 降低頻率避免過度渲染
        const interval = setInterval(updateRealData, 10000) // 每10秒檢查一次

        return () => clearInterval(interval)
    }, [enabled, useRealData]) // 移除循環依賴

    // 初始化衛星軌道 - 使用真實歷史軌跡數據
    useEffect(() => {
        if (!enabled) {
            setOrbits([])
            return
        }

        // 🚀 優先使用真實歷史軌跡數據，404 錯誤時 Fallback 到模擬軌跡
        if (satellites && satellites.length > 0) {
            // Removed verbose initialization logging

            const initialOrbits: SatelliteOrbit[] = satellites.map((sat, i) => {
                const satelliteId =
                    sat.norad_id?.toString() || sat.id?.toString() || `sat_${i}`
                const satelliteName = sat.name || `SAT-${satelliteId}`

                // 獲取真實衛星數據匹配
                const realData = realSatelliteMapping.get(satelliteId)

                // 🌍 獲取歷史軌跡數據
                const fullTrajectory = historicalTrajectories.get(satelliteId)

                if (
                    fullTrajectory &&
                    fullTrajectory.trajectory_points.length > 0
                ) {
                    // 使用真實歷史軌跡
                    // Real trajectory data loaded

                    // 找到當前時間點的位置
                    const currentTimeSeconds = Date.now() / 1000
                    const currentPoint =
                        historicalTrajectoryService.interpolatePosition(
                            fullTrajectory,
                            currentTimeSeconds
                        )

                    // 生成3D軌跡點預覽
                    const trajectoryPoints: [number, number, number][] =
                        fullTrajectory.trajectory_points.map((point) =>
                            historicalTrajectoryService.trajectoryPointTo3D(
                                point,
                                1200,
                                600
                            )
                        )

                    return {
                        id: satelliteId,
                        name: satelliteName,
                        azimuthShift: 0, // 不需要人為偏移
                        transitDuration: fullTrajectory.duration_hours * 3600, // 轉換為秒
                        transitStartTime: 0,
                        isTransiting: true,
                        isVisible: currentPoint
                            ? currentPoint.elevation_deg > 0
                            : false,
                        nextAppearTime: 0,
                        currentPosition: currentPoint
                            ? historicalTrajectoryService.trajectoryPointTo3D(
                                  currentPoint,
                                  1200,
                                  600
                              )
                            : [0, -200, 0],
                        trajectoryPoints: trajectoryPoints,
                        fullTrajectory: fullTrajectory,
                        currentTrajectoryPoint: currentPoint,
                        realData: realData,
                        signalStrength: currentPoint?.distance_km
                            ? 100 - currentPoint.distance_km / 20
                            : 50,
                        elevation: currentPoint?.elevation_deg || 0,
                        azimuth: currentPoint?.azimuth_deg || 0,
                    }
                }

                // 📡 Fallback: 軌跡 API 404 時使用模擬軌跡（真實數據基礎）
                // Using simulated trajectory (API unavailable)
                const baseElevation = sat.elevation_deg || sat.elevation || 45
                const baseAzimuth = sat.azimuth_deg || sat.azimuth || 180
                const baseDistance = sat.distance_km || sat.range_km || (550 / Math.sin(Math.max(5, baseElevation) * Math.PI / 180))

                // 生成模擬軌跡（從地平線升起到落下）
                const visibleDuration = 600 // 10分鐘可見窗口
                const trajectoryPoints: [number, number, number][] = []

                for (let t = 0; t <= visibleDuration; t += 30) {
                    const progress = t / visibleDuration

                    // 模擬真實的衛星軌跡
                    let currentElevation: number
                    if (progress < 0.5) {
                        // 上升階段：從 -5° 上升到最高仰角
                        currentElevation =
                            -5 +
                            (baseElevation + 5) * Math.sin(progress * Math.PI)
                    } else {
                        // 下降階段：從最高仰角下降到 -5°
                        currentElevation =
                            baseElevation *
                                Math.cos((progress - 0.5) * Math.PI) -
                            5
                    }

                    const currentAzimuth = (baseAzimuth + progress * 90) % 360
                    const _currentDistance =
                        baseDistance /
                        Math.cos((currentElevation * Math.PI) / 180)

                    const elevRad = (currentElevation * Math.PI) / 180
                    const azimRad = (currentAzimuth * Math.PI) / 180

                    const sceneScale = 1200
                    const heightScale = 600

                    const x = sceneScale * Math.cos(elevRad) * Math.sin(azimRad)
                    const z = sceneScale * Math.cos(elevRad) * Math.cos(azimRad)
                    const y =
                        currentElevation > 0
                            ? Math.max(
                                  10,
                                  heightScale * Math.sin(elevRad) + 100
                              )
                            : -200 // 地平線以下隱藏

                    trajectoryPoints.push([x, y, z])
                }

                // 🚀 修復：基於索引的智能相位分散 - 避免衛星同時出現/消失
                let initialPhase = 0.5 // 預設在軌道中間
                const phaseOffset = (i * 0.618) % 1.0 // 黃金比例分散，確保均勻分布
                
                if (baseElevation > 60) {
                    // 高仰角：基於索引錯開，避免聚集在頂點
                    initialPhase = 0.35 + (phaseOffset * 0.3) // 35%-65% 範圍內分散
                } else if (baseElevation > 30) {
                    // 中等仰角：交替分配 + 索引偏移
                    initialPhase = (i % 2 === 0 ? 0.25 : 0.75) + (phaseOffset * 0.1)
                } else {
                    // 低仰角：交替分配 + 索引偏移，避免同時升起/落下
                    initialPhase = (i % 2 === 0 ? 0.05 : 0.95) + (phaseOffset * 0.05)
                }
                
                // 確保相位在有效範圍內
                initialPhase = initialPhase % 1.0

                const startTimeOffset = -initialPhase * visibleDuration
                const currentIndex = Math.floor(
                    initialPhase * trajectoryPoints.length
                )

                return {
                    id: satelliteId,
                    name: satelliteName,
                    azimuthShift: 0,
                    transitDuration: visibleDuration,
                    transitStartTime: startTimeOffset,
                    isTransiting: true,
                    isVisible: trajectoryPoints[currentIndex]?.[1] > 10,
                    nextAppearTime: 0,
                    currentPosition:
                        trajectoryPoints[currentIndex] || trajectoryPoints[0],
                    trajectoryPoints: trajectoryPoints,
                    realData: realData,
                    signalStrength:
                        sat.estimated_signal_strength ||
                        realData?.signal_quality.estimated_signal_strength,
                    elevation: baseElevation,
                    azimuth: baseAzimuth,
                }
            })

            setOrbits(initialOrbits)

            const trajectoriesWithData = initialOrbits.filter(
                (o) => o.fullTrajectory
            ).length
            console.log(`🛰️ ${trajectoriesWithData} 真實軌跡 + ${initialOrbits.length - trajectoriesWithData} 模擬軌跡`)
        }
    }, [
        enabled,
        satellites.length, // 使用長度而不是整個陣列避免深度比較
    ]) // 固定依賴項，避免循環依賴

    // 更新軌道動畫
    useFrame((_, delta) => {
        if (!enabled) return

        // 時間累積（不在這裡乘以速度倍數，在計算位置時處理）
        timeRef.current += delta

        setOrbits((prevOrbits) => {
            const updatedOrbits = prevOrbits.map((orbit) => {
                // 🚀 使用真實軌跡計算函數（速度倍數在函數內部處理）
                const adjustedTime = timeRef.current - orbit.transitStartTime
                const state = calculateRealTrajectoryPosition(
                    adjustedTime,
                    orbit,
                    speedMultiplier
                )
                return {
                    ...orbit,
                    currentPosition: state.position,
                    isVisible: state.isVisible,
                }
            })

            return updatedOrbits
        })
    })

    // 🔗 使用 useRef 來避免在 useEffect 中依賴不斷變化的 orbits
    const orbitsRef = useRef<SatelliteOrbit[]>([])
    orbitsRef.current = orbits

    // 🔄 位置更新邏輯 - 修復無限循環問題
    useEffect(() => {
        if (!enabled || !onSatellitePositions) return

        const updatePositions = () => {
            const positionMap = new Map<string, [number, number, number]>()
            let hasChanges = false

            orbitsRef.current.forEach((orbit) => {
                if (orbit.isVisible) {
                    positionMap.set(orbit.id, orbit.currentPosition)
                    positionMap.set(orbit.name, orbit.currentPosition) // 同時支援名稱查找

                    // 檢查位置是否有變化 - 降低閾值以實現更平滑的更新
                    const lastPos = lastPositionsRef.current.get(orbit.id)
                    if (
                        !lastPos ||
                        Math.abs(lastPos[0] - orbit.currentPosition[0]) > 2.0 ||
                        Math.abs(lastPos[1] - orbit.currentPosition[1]) > 2.0 ||
                        Math.abs(lastPos[2] - orbit.currentPosition[2]) > 2.0
                    ) {
                        hasChanges = true
                    }
                }
            })

            // 只在位置有顯著變化時才調用回調
            if (hasChanges && onSatellitePositionsRef.current) {
                lastPositionsRef.current = positionMap
                onSatellitePositionsRef.current(positionMap)
            }
        }

        // 每 250ms 更新一次位置回調，提高平滑度
        const interval = setInterval(updatePositions, 250)

        return () => clearInterval(interval)
    }, [enabled]) // 移除 onSatellitePositions 依賴，使用 useRef 來訪問最新的回調

    const satellitesToRender = orbits.filter((orbit) => orbit.isVisible)

    if (!enabled) {
        return null
    }

    return (
        <group>
            {satellitesToRender.map((orbit, index) => {
                // 🔥 對接演算法結果 - 優先使用後端演算法狀態
                // 支援多種 ID 匹配模式：完全匹配、名稱匹配、部分匹配
                const isAlgorithmCurrent =
                    algorithmResults?.currentSatelliteId === orbit.id ||
                    algorithmResults?.currentSatelliteId === orbit.name ||
                    (algorithmResults?.currentSatelliteId &&
                        orbit.name.includes(
                            algorithmResults.currentSatelliteId
                        ))
                const isAlgorithmPredicted =
                    algorithmResults?.predictedSatelliteId === orbit.id ||
                    algorithmResults?.predictedSatelliteId === orbit.name ||
                    (algorithmResults?.predictedSatelliteId &&
                        orbit.name.includes(
                            algorithmResults.predictedSatelliteId
                        ))
                const _isCurrent =
                    isAlgorithmCurrent ||
                    currentConnection?.satelliteId === orbit.id
                const _isPredicted =
                    isAlgorithmPredicted ||
                    predictedConnection?.satelliteId === orbit.id

                // 🎨 根據換手狀態決定顏色
                let statusColor = '#ffffff' // 預設白色
                let _opacity = 1.0 // 完全不透明
                let _scale = 1

                // 🔗 檢查是否為換手狀態中的衛星
                const isHandoverCurrent =
                    handoverState?.currentSatelliteId === orbit.id ||
                    handoverState?.currentSatelliteId === orbit.name
                const isHandoverTarget =
                    handoverState?.targetSatelliteId === orbit.id ||
                    handoverState?.targetSatelliteId === orbit.name

                // 🎯 只有在有明確換手狀態且匹配的衛星才變色，其他都保持白色
                if (handoverState && (isHandoverCurrent || isHandoverTarget)) {
                    if (isHandoverCurrent) {
                        // 當前連接的衛星
                        switch (handoverState.phase) {
                            case 'stable':
                                statusColor = '#00ff00' // 綠色 - 穩定連接
                                _scale = 1.3
                                break
                            case 'preparing':
                                statusColor = '#ffaa00' // 橙黃色 - 準備換手
                                _scale = 1.3
                                break
                            case 'establishing':
                                statusColor = '#ffdd00' // 亮黃色 - 建立新連接
                                _scale = 1.2
                                break
                            case 'switching':
                                statusColor = '#aaaaaa' // 淺灰色 - 換手中
                                _scale = 1.1
                                break
                            case 'completing':
                                statusColor = '#aaaaaa' // 淺灰色 - 完成中
                                _scale = 1.0
                                break
                            default:
                                statusColor = '#00ff00'
                                _scale = 1.3
                        }
                    } else if (isHandoverTarget) {
                        // 目標衛星
                        switch (handoverState.phase) {
                            case 'preparing':
                                statusColor = '#0088ff' // 藍色 - 準備連接
                                _scale = 1.2
                                break
                            case 'establishing':
                                statusColor = '#0088ff' // 藍色 - 建立連接中
                                _scale = 1.3
                                break
                            case 'switching':
                                statusColor = '#00ff00' // 綠色 - 換手為主要連接
                                _scale = 1.4
                                break
                            case 'completing':
                                statusColor = '#00ff00' // 綠色 - 新的主要連接
                                _scale = 1.4
                                break
                            default:
                                statusColor = '#0088ff'
                                _scale = 1.2
                        }
                    }
                } else {
                    // 普通衛星 - 保持白色
                    statusColor = '#ffffff' // 預設白色
                    _opacity = 0.8
                    _scale = 0.8
                }

                return (
                    <group key={`${orbit.id}-${orbit.name}-${index}`}>
                        <StaticModel
                            url={SATELLITE_MODEL_URL}
                            position={orbit.currentPosition}
                            scale={[
                                SATELLITE_CONFIG.SAT_SCALE,
                                SATELLITE_CONFIG.SAT_SCALE,
                                SATELLITE_CONFIG.SAT_SCALE,
                            ]}
                            pivotOffset={[0, 0, 0]}
                        />

                        {/* 🌟 光球指示器 - 位置在衛星和文字中間，適度透明 */}
                        <mesh
                            position={[
                                orbit.currentPosition[0],
                                orbit.currentPosition[1] + 15, // 衛星上方15單位
                                orbit.currentPosition[2],
                            ]}
                        >
                            <sphereGeometry args={[3, 16, 16]} />
                            <meshBasicMaterial
                                color={statusColor}
                                transparent
                                opacity={0.7}
                            />
                        </mesh>

                        {showLabels && (
                            <Text
                                position={[
                                    orbit.currentPosition[0],
                                    orbit.currentPosition[1] +
                                        (algorithmResults?.binarySearchActive &&
                                        (isAlgorithmCurrent ||
                                            isAlgorithmPredicted)
                                            ? 45
                                            : 35),
                                    orbit.currentPosition[2],
                                ]}
                                fontSize={3.5}
                                color={statusColor}
                                anchorX="center"
                                anchorY="middle"
                            >
                                {/* 🏷️ 顯示衛星名稱 + 演算法狀態 + 真實數據 */}
                                {orbit.name
                                    .replace(' [DTC]', '')
                                    .replace('[DTC]', '')}
                                {isAlgorithmCurrent && '\n[當前]'}
                                {isAlgorithmPredicted && '\n[預測]'}
                                {algorithmResults?.predictionConfidence &&
                                    isAlgorithmPredicted &&
                                    `\n${(
                                        algorithmResults.predictionConfidence *
                                        100
                                    ).toFixed(1)}%`}
                                {/* 真實數據資訊 */}
                                {orbit.realData && useRealData && (
                                    <>
                                        {`\n仰角: ${orbit.realData.position.elevation.toFixed(
                                            1
                                        )}°`}
                                        {`\n信號: ${orbit.realData.signal_quality.estimated_signal_strength.toFixed(
                                            1
                                        )}dBm`}
                                        {realDataStatus === 'stale' &&
                                            '\n[數據較舊]'}
                                    </>
                                )}
                            </Text>
                        )}
                    </group>
                )
            })}
        </group>
    )
}

export default DynamicSatelliteRenderer
