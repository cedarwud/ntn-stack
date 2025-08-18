import React, { useRef, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import StaticModel from '../../../scenes/StaticModel'
import { SATELLITE_CONFIG } from '../../../../config/satellite.config'

// 🚀 使用新的統一衛星數據管理
import { useSatellites } from '../../../../contexts/SatelliteDataContext'
import { UnifiedSatelliteInfo } from '../../../../services/satelliteDataService'

interface DynamicSatelliteRendererProps {
    enabled: boolean
    currentConnection?: Record<string, unknown>
    predictedConnection?: Record<string, unknown>
    showLabels?: boolean
    speedMultiplier?: number
    // 🚀 演算法結果對接接口
    algorithmResults?: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }
    // 🔗 換手狀態信息
    handoverState?: {
        phase: 'stable' | 'preparing' | 'establishing' | 'switching' | 'completing'
        currentSatelliteId: string | null
        targetSatelliteId: string | null
        progress: number
    }
    onSatelliteClick?: (satelliteId: string) => void
    // 🔗 衛星位置回調
    onSatellitePositions?: (positions: Map<string, [number, number, number]>) => void
    
    // ⚠️ 向後兼容props - 現在由Context管理，但保留接口
    satellites?: unknown[]
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
    // 🚀 統一數據格式
    unifiedData: UnifiedSatelliteInfo
    signalStrength: number
    elevation: number
    azimuth: number
}

const SATELLITE_MODEL_URL = '/static/models/sat.glb'

// 🚀 Phase 1 優化：基於真實數據的衛星軌道位置計算（使用統一數據格式）
const calculateOrbitPosition = (
    currentTime: number,
    orbit: SatelliteOrbit,
    speedMultiplier: number
): { position: [number, number, number]; isVisible: boolean } => {
    // ✅ 使用統一衛星數據進行軌跡計算
    if (orbit.unifiedData) {
        const unifiedData = orbit.unifiedData;
        
        // 基於真實仰角和方位角計算3D位置
        const elevation = (unifiedData.elevation_deg * Math.PI) / 180;
        const azimuth = (unifiedData.azimuth_deg * Math.PI) / 180;
        const range = unifiedData.distance_km || 1000;
        
        // 3D球面座標轉換 (基於真實軌道參數)
        const scaledRange = Math.min(range / 3, 800);
        const x = scaledRange * Math.cos(elevation) * Math.sin(azimuth);
        const z = scaledRange * Math.cos(elevation) * Math.cos(azimuth);
        const y = Math.max(15, scaledRange * Math.sin(elevation) + 80);
        
        // ✅ 基於真實仰角判定可見性 (符合物理原理)
        const isVisible = unifiedData.elevation_deg > 0;
        
        return {
            position: [x, y, z] as [number, number, number],
            isVisible: isVisible
        };
    }
    
    // 🔙 Fallback：當沒有真實數據時使用簡化軌道計算
    const totalOrbitPeriod = 5400; // 真實 LEO 軌道週期 (90分鐘)
    const relativeTime = currentTime - orbit.transitStartTime;
    const normalizedTime = ((relativeTime % totalOrbitPeriod) + totalOrbitPeriod) % totalOrbitPeriod;
    const isInTransit = normalizedTime <= orbit.transitDuration;

    if (!isInTransit) {
        return {
            position: [0, -200, 0] as [number, number, number],
            isVisible: false,
        };
    }

    const transitProgress = normalizedTime / orbit.transitDuration;
    const realVelocity = orbit.unifiedData?.position.velocity || 7.5;
    const velocityFactor = (realVelocity / 7.5) * speedMultiplier;
    const adjustedProgress = Math.min(1.0, transitProgress * velocityFactor);

    const azimuthShift = (orbit.azimuthShift * Math.PI) / 180;
    const angle = adjustedProgress * Math.PI;

    const baseRadius = 600;
    const heightRadius = 300;

    const x = baseRadius * Math.cos(angle) * Math.cos(azimuthShift);
    const z = baseRadius * Math.cos(angle) * Math.sin(azimuthShift);
    const y = Math.max(15, 80 + heightRadius * Math.sin(angle));

    const isVisible = y > 25;
    return { position: [x, y, z], isVisible };
}

const DynamicSatelliteRenderer: React.FC<DynamicSatelliteRendererProps> = ({
    enabled,
    currentConnection,
    predictedConnection,
    showLabels = true,
    speedMultiplier = 1,
    algorithmResults,
    handoverState,
    onSatelliteClick: _onSatelliteClick,
    onSatellitePositions,
    satellites: _propSatellites, // 向後兼容，但不使用
}) => {
    // 🚀 使用統一衛星數據管理
    const { satellites: unifiedSatellites, loading: satellitesLoading } = useSatellites()
    
    const [orbits, setOrbits] = useState<SatelliteOrbit[]>([])
    const timeRef = useRef(0)
    const lastPositionsRef = useRef<Map<string, [number, number, number]>>(new Map())

    // 演算法狀態對接
    const [_algorithmHighlights, _setAlgorithmHighlights] = useState<{
        currentSatellite?: string
        predictedSatellite?: string
        handoverPath?: string[]
        algorithmStatus?: 'idle' | 'calculating' | 'handover_ready'
    }>({})

    // 🚀 基於統一數據初始化衛星軌道
    useEffect(() => {
        if (!enabled) {
            setOrbits([])
            return
        }

        if (unifiedSatellites && unifiedSatellites.length > 0) {
            console.log(`🛰️ DynamicSatelliteRenderer: 使用統一數據源初始化 ${unifiedSatellites.length} 顆衛星`)
            
            const initialOrbits: SatelliteOrbit[] = unifiedSatellites.map((sat, i) => {
                return {
                    id: sat.id,
                    name: sat.name,
                    azimuthShift: (i % 6) * 60 + Math.floor(i / 6) * 10,
                    transitDuration: 90 + Math.random() * 60,
                    transitStartTime: i * 15 + Math.random() * 30,
                    isTransiting: false,
                    isVisible: false,
                    nextAppearTime: 0,
                    currentPosition: [0, -200, 0],
                    // 🚀 使用統一數據格式
                    unifiedData: sat,
                    signalStrength: sat.signal_strength,
                    elevation: sat.elevation_deg,
                    azimuth: sat.azimuth_deg,
                }
            })

            setOrbits(initialOrbits)
        } else if (!satellitesLoading) {
            // 只有當數據載入完成且沒有衛星時才使用Fallback
            console.log('🔙 DynamicSatelliteRenderer: 使用Fallback衛星數據')
            const fallbackOrbits: SatelliteOrbit[] = Array.from({ length: 18 }, (_, i) => {
                const satelliteId = `sat_${i}`
                const satelliteName = `STARLINK-${1000 + i}`

                return {
                    id: satelliteId,
                    name: satelliteName,
                    azimuthShift: Math.floor(i / 6) * 60 + (i % 6) * 10,
                    transitDuration: 90 + Math.random() * 60,
                    transitStartTime: i * 15 + Math.random() * 30,
                    isTransiting: false,
                    isVisible: false,
                    nextAppearTime: 0,
                    currentPosition: [0, -200, 0],
                    // 空的統一數據
                    unifiedData: {
                        id: satelliteId,
                        norad_id: satelliteId,
                        name: satelliteName,
                        elevation_deg: 0,
                        azimuth_deg: 0,
                        distance_km: 1000,
                        signal_strength: 0.5,
                        is_visible: false,
                        constellation: 'starlink',
                        last_updated: new Date().toISOString(),
                        position: {
                            latitude: 0, longitude: 0, altitude: 550,
                            elevation: 0, azimuth: 0, range: 1000,
                            velocity: 7.5, doppler_shift: 0
                        },
                        signal_quality: {
                            rsrp: -100, rsrq: -10, sinr: 10,
                            estimated_signal_strength: 0.5
                        }
                    },
                    signalStrength: 0.5,
                    elevation: 0,
                    azimuth: 0,
                }
            })

            setOrbits(fallbackOrbits)
        }
    }, [enabled, unifiedSatellites, satellitesLoading])

    // 🚀 統一數據更新時立即重算軌道
    useEffect(() => {
        if (unifiedSatellites.length > 0) {
            setOrbits(prevOrbits => 
                prevOrbits.map(orbit => {
                    // 尋找對應的統一數據
                    const matchingData = unifiedSatellites.find(sat => 
                        sat.id === orbit.id || sat.norad_id === orbit.id || sat.name === orbit.name
                    )
                    
                    if (matchingData) {
                        return {
                            ...orbit,
                            unifiedData: matchingData,
                            elevation: matchingData.elevation_deg,
                            azimuth: matchingData.azimuth_deg,
                            signalStrength: matchingData.signal_strength,
                        }
                    }
                    return orbit
                })
            )
        }
    }, [unifiedSatellites])

    // 🚀 Phase 1 優化：使用真實速度的動畫更新
    useFrame(() => {
        if (!enabled) return

        setOrbits((prevOrbits) => {
            return prevOrbits.map((orbit) => {
                // ✅ 基於統一數據的真實速度調整時間步長
                const realVelocity = orbit.unifiedData?.position.velocity || 7.5;
                const normalizedVelocity = realVelocity / 7.5;
                const timeStep = speedMultiplier * normalizedVelocity / 60;
                
                timeRef.current += timeStep;
                
                const state = calculateOrbitPosition(
                    timeRef.current,
                    orbit,
                    speedMultiplier
                );
                
                return {
                    ...orbit,
                    currentPosition: state.position,
                    isVisible: state.isVisible,
                };
            });
        });
    })

    // 使用 useRef 來避免在 useEffect 中依賴不斷變化的 orbits
    const orbitsRef = useRef<SatelliteOrbit[]>([])
    orbitsRef.current = orbits

    // 使用 useRef 存儲最新的回調函數
    const onSatellitePositionsRef = useRef(onSatellitePositions)

    useEffect(() => {
        onSatellitePositionsRef.current = onSatellitePositions
    }, [onSatellitePositions])

    // 位置更新邏輯
    useEffect(() => {
        if (!enabled || !onSatellitePositionsRef.current) return

        const updatePositions = () => {
            const positionMap = new Map<string, [number, number, number]>()
            let hasChanges = false

            orbitsRef.current.forEach((orbit) => {
                if (orbit.isVisible) {
                    positionMap.set(orbit.id, orbit.currentPosition)
                    positionMap.set(orbit.name, orbit.currentPosition)

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

            if (hasChanges && onSatellitePositionsRef.current) {
                lastPositionsRef.current = positionMap
                onSatellitePositionsRef.current(positionMap)
            }
        }

        const interval = setInterval(updatePositions, 250)
        return () => clearInterval(interval)
    }, [enabled])

    const satellitesToRender = orbits.filter((orbit) => orbit.isVisible)

    if (!enabled) {
        return null
    }

    return (
        <group>
            {satellitesToRender.map((orbit, index) => {
                // 🔥 對接演算法結果
                const isAlgorithmCurrent =
                    algorithmResults?.currentSatelliteId === orbit.id ||
                    algorithmResults?.currentSatelliteId === orbit.name ||
                    (algorithmResults?.currentSatelliteId &&
                        orbit.name.includes(algorithmResults.currentSatelliteId))
                        
                const isAlgorithmPredicted =
                    algorithmResults?.predictedSatelliteId === orbit.id ||
                    algorithmResults?.predictedSatelliteId === orbit.name ||
                    (algorithmResults?.predictedSatelliteId &&
                        orbit.name.includes(algorithmResults.predictedSatelliteId))

                const _isCurrent = isAlgorithmCurrent || currentConnection?.satelliteId === orbit.id
                const _isPredicted = isAlgorithmPredicted || predictedConnection?.satelliteId === orbit.id

                // 🎨 根據換手狀態決定顏色
                let statusColor = '#ffffff'
                let _opacity = 1.0
                let _scale = 1

                // 🔗 檢查是否為換手狀態中的衛星
                const isHandoverCurrent =
                    handoverState?.currentSatelliteId === orbit.id ||
                    handoverState?.currentSatelliteId === orbit.name
                const isHandoverTarget =
                    handoverState?.targetSatelliteId === orbit.id ||
                    handoverState?.targetSatelliteId === orbit.name

                // 🎯 換手狀態顏色邏輯
                if (handoverState && (isHandoverCurrent || isHandoverTarget)) {
                    if (isHandoverCurrent) {
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
                    statusColor = '#ffffff'
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

                        {/* 🌟 光球指示器 */}
                        <mesh
                            position={[
                                orbit.currentPosition[0],
                                orbit.currentPosition[1] + 15,
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
                                        (isAlgorithmCurrent || isAlgorithmPredicted)
                                            ? 45
                                            : 35),
                                    orbit.currentPosition[2],
                                ]}
                                fontSize={3.5}
                                color={statusColor}
                                anchorX="center"
                                anchorY="middle"
                            >
                                {/* 🏷️ 顯示衛星名稱 + 演算法狀態 + 統一數據 */}
                                {orbit.name.replace(' [DTC]', '').replace('[DTC]', '')}
                                {isAlgorithmCurrent && '\n[當前]'}
                                {isAlgorithmPredicted && '\n[預測]'}
                                {algorithmResults?.predictionConfidence &&
                                    isAlgorithmPredicted &&
                                    `\n${(algorithmResults.predictionConfidence * 100).toFixed(1)}%`}
                                {/* 🚀 統一數據資訊 */}
                                {orbit.unifiedData && (
                                    <>
                                        {`\n仰角: ${orbit.unifiedData.elevation_deg.toFixed(1)}°`}
                                        {`\n信號: ${orbit.unifiedData.signal_quality.estimated_signal_strength.toFixed(1)}dBm`}
                                        {`\n星座: ${orbit.unifiedData.constellation.toUpperCase()}`}
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