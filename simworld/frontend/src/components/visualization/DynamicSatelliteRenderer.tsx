import React, { useRef, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
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
}

interface SatelliteState {
    id: string
    name: string
    basePosition: [number, number, number]
    currentPosition: [number, number, number]
    timeOffset: number
    isVisible: boolean
    elevation: number
    azimuth: number
    startAzimuth: number
    azimuthSpan: number
    maxElevation: number
    orbitSpeed: number
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

// 計算3D場景位置
const calculatePosition = (elevation: number, azimuth: number): [number, number, number] => {
    const PI_DIV_180 = Math.PI / 180
    const GLB_SCENE_SIZE = 1200
    const MIN_SAT_HEIGHT = 200
    const MAX_SAT_HEIGHT = 600
    
    const elevationRad = elevation * PI_DIV_180
    const azimuthRad = azimuth * PI_DIV_180
    
    const range = GLB_SCENE_SIZE * 0.4
    const horizontalDist = range * Math.cos(elevationRad)
    
    const x = horizontalDist * Math.sin(azimuthRad)
    const z = horizontalDist * Math.cos(azimuthRad)
    const y = MIN_SAT_HEIGHT + (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * Math.sin(elevationRad)

    return [x, y, z]
}

const DynamicSatelliteRenderer: React.FC<DynamicSatelliteRendererProps> = ({
    satellites,
    enabled,
    currentConnection,
    predictedConnection,
    showLabels = true,
    speedMultiplier = 60
}) => {
    const [satelliteStates, setSatelliteStates] = useState<SatelliteState[]>([])
    const timeRef = useRef(0)

    // 初始化衛星狀態
    useEffect(() => {
        if (!enabled || !satellites || satellites.length === 0) {
            setSatelliteStates([])
            return
        }

        console.log('🛰️ 初始化動態衛星系統 - 12 顆衛星多樣化軌道')
        
        const states: SatelliteState[] = satellites.slice(0, 12).map((satellite, index) => {
            // 每顆衛星錯開 6 分鐘（確保穩定的3-4顆同時可見）
            const timeOffset = index * 6 * 60 // 轉為秒

            // 真實多樣化軌道參數
            const satelliteHash = satellite.norad_id ? parseInt(satellite.norad_id) : satellite.name.length + index * 1000
            
            // 8個主要方向的起始方位角
            const directions = [0, 45, 90, 135, 180, 225, 270, 315] // 北、東北、東、東南、南、西南、西、西北
            const startAzimuth = directions[index % 8] + (satelliteHash % 30) - 15 // 加入隨機偏移
            
            // 多樣化的方位跨度（模擬不同軌道傾角）
            const azimuthSpans = [60, 80, 100, 120, 140, 160, 180] // 不同的跨越角度
            const azimuthSpan = azimuthSpans[index % azimuthSpans.length]
            
            // 多樣化的最大仰角（模擬不同距離）
            const elevationLevels = [15, 25, 35, 45, 55, 65, 75, 85] // 從低空到高空過境
            const maxElevation = elevationLevels[index % elevationLevels.length]
            
            // 不同的軌道速度（模擬真實LEO衛星速度差異）
            const orbitSpeeds = [0.8, 0.9, 1.0, 1.1, 1.2, 0.85, 0.95, 1.05] // 速度倍數
            const orbitSpeed = orbitSpeeds[index % orbitSpeeds.length]

            const basePosition = calculatePosition(satellite.elevation_deg, satellite.azimuth_deg)
            
            console.log(`🚀 衛星 ${satellite.name}: 索引=${index}, 時間偏移=${timeOffset/60}分鐘, 起始=${startAzimuth}°, 跨度=${azimuthSpan}°, 最高=${maxElevation}°, 速度=${orbitSpeed}x`)

            return {
                id: satellite.norad_id?.toString() || satellite.name,
                name: satellite.name,
                basePosition,
                currentPosition: basePosition,
                timeOffset,
                isVisible: false,
                elevation: 0,
                azimuth: startAzimuth,
                startAzimuth,
                azimuthSpan,
                maxElevation,
                orbitSpeed
            }
        })

        setSatelliteStates(states)
        timeRef.current = 0 // 重置時間
        
        console.log('⏰ 時間調度: 6分鐘間隔，20分鐘可見期，16分鐘休眠期')
        console.log('🌍 軌跡多樣性: 8個主要方向，15°-85°仰角變化')
        console.log('🔄 換手最佳化: 維持3-4顆衛星同時可見，提供充分選擇')
    }, [satellites, enabled])

    // 動畫更新
    useFrame((state, delta) => {
        if (!enabled || satelliteStates.length === 0) return

        // 更新全局時間
        timeRef.current += delta * speedMultiplier

        setSatelliteStates(prevStates => 
            prevStates.map(sat => {
                // 計算這顆衛星的本地時間
                const localTime = (timeRef.current + sat.timeOffset) % (36 * 60) // 36分鐘週期
                
                // 前 20 分鐘可見，後 16 分鐘不可見
                const isVisible = localTime < (20 * 60)
                
                if (isVisible) {
                    // 計算過境進度 (0 到 1) - 使用個別軌道速度
                    const transitProgress = localTime / (20 * 60)
                    const speedAdjustedProgress = Math.min(transitProgress * sat.orbitSpeed, 1.0)
                    
                    // 使用衛星特定的軌道參數
                    const currentAzimuth = (sat.startAzimuth + sat.azimuthSpan * speedAdjustedProgress) % 360
                    
                    // 當前仰角（拋物線變化 - 升起到降落）
                    const currentElevation = sat.maxElevation * Math.sin(speedAdjustedProgress * Math.PI)
                    
                    // 計算新位置
                    const newPosition = calculatePosition(currentElevation, currentAzimuth)
                    
                    return {
                        ...sat,
                        currentPosition: newPosition,
                        isVisible: true,
                        elevation: currentElevation,
                        azimuth: currentAzimuth
                    }
                } else {
                    // 不可見時設置為地平線以下
                    return {
                        ...sat,
                        isVisible: false,
                        elevation: -10,
                        azimuth: sat.azimuth
                    }
                }
            })
        )
    })

    // 只渲染可見的衛星
    const visibleSatellites = satelliteStates.filter(sat => sat.isVisible)

    // 調試輸出
    useEffect(() => {
        const interval = setInterval(() => {
            const visibleCount = visibleSatellites.length
            const statusList = satelliteStates.map(sat => {
                const localTime = ((timeRef.current + sat.timeOffset) % (36 * 60)) / 60
                return `${sat.name}:${localTime.toFixed(1)}min${sat.isVisible ? '✅' : '❌'}`
            }).join(' | ')
            console.log(`🛰️ [${visibleCount}/12可見] ${statusList}`)
        }, 3000)

        return () => clearInterval(interval)
    }, [satelliteStates, visibleSatellites.length])

    if (!enabled) {
        return null
    }

    return (
        <group>
            {visibleSatellites.map(satellite => {
                const isCurrent = currentConnection?.satelliteId === satellite.id
                const isPredicted = predictedConnection?.satelliteId === satellite.id
                
                let statusColor = '#ffffff'
                if (isCurrent) {
                    statusColor = '#00ff00'
                } else if (isPredicted) {
                    statusColor = '#ffaa00'
                }

                return (
                    <group key={satellite.id}>
                        {/* 衛星模型 */}
                        <StaticModel
                            url={SATELLITE_MODEL_URL}
                            position={satellite.currentPosition}
                            scale={[SATELLITE_CONFIG.SAT_SCALE, SATELLITE_CONFIG.SAT_SCALE, SATELLITE_CONFIG.SAT_SCALE]}
                            pivotOffset={[0, 0, 0]}
                        />
                        
                        {/* 狀態指示器 */}
                        <mesh position={[
                            satellite.currentPosition[0], 
                            satellite.currentPosition[1] + 15, 
                            satellite.currentPosition[2]
                        ]}>
                            <sphereGeometry args={[3, 8, 8]} />
                            <meshBasicMaterial
                                color={statusColor}
                                transparent
                                opacity={0.8}
                            />
                        </mesh>
                        
                        {/* 衛星標籤 */}
                        {showLabels && (
                            <Text
                                position={[
                                    satellite.currentPosition[0], 
                                    satellite.currentPosition[1] + 25, 
                                    satellite.currentPosition[2]
                                ]}
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
                                position={[
                                    satellite.currentPosition[0], 
                                    satellite.currentPosition[1] + 20, 
                                    satellite.currentPosition[2]
                                ]}
                                fontSize={3}
                                color="#ffffff"
                                anchorX="center"
                                anchorY="middle"
                            >
                                {satellite.elevation.toFixed(1)}°
                            </Text>
                        )}
                    </group>
                )
            })}
        </group>
    )
}

export default DynamicSatelliteRenderer