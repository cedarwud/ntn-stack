import React, { useRef, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import StaticModel from '../scenes/StaticModel'
import { ApiRoutes } from '../../config/apiRoutes'
import { SATELLITE_CONFIG } from '../../config/satellite.config'

interface DynamicSatelliteRendererProps {
    satellites: any[]
    enabled: boolean
    currentConnection?: any
    predictedConnection?: any
    showLabels?: boolean
    speedMultiplier?: number
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
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

// 衛星軌道位置計算函數 - 支持循環軌道
const calculateOrbitPosition = (
    currentTime: number,
    orbit: SatelliteOrbit,
    speedMultiplier: number
): { position: [number, number, number]; isVisible: boolean } => {
    // 計算總軌道週期 (過境時間 + 不可見時間)
    const totalOrbitPeriod = orbit.transitDuration + 120 // 2分鐘不可見間隔
    
    // 計算從開始時間到現在的相對時間
    const relativeTime = currentTime - orbit.transitStartTime
    
    // 使用模運算實現循環軌道
    const normalizedTime = ((relativeTime % totalOrbitPeriod) + totalOrbitPeriod) % totalOrbitPeriod
    
    // 檢查是否在過境期間
    const isInTransit = normalizedTime <= orbit.transitDuration
    
    if (!isInTransit) {
        return {
            position: [0, -200, 0] as [number, number, number], // 隱藏在地下
            isVisible: false
        }
    }

    // 計算過境進度 (0 到 1)
    const transitProgress = normalizedTime / orbit.transitDuration
    
    // 計算軌道位置 - 完整的半圓弧軌道
    const azimuthShift = orbit.azimuthShift * Math.PI / 180
    const angle = transitProgress * Math.PI // 0 到 π 的半圓
    
    const baseRadius = 600
    const heightRadius = 300
    
    // 3D 軌道計算
    const x = baseRadius * Math.cos(angle) * Math.cos(azimuthShift)
    const z = baseRadius * Math.cos(angle) * Math.sin(azimuthShift)
    const y = Math.max(15, 80 + heightRadius * Math.sin(angle))
    
    // 只有高度足夠才可見
    const isVisible = y > 25
    
    return { position: [x, y, z], isVisible }
}

const DynamicSatelliteRenderer: React.FC<DynamicSatelliteRendererProps> = ({
    satellites,
    enabled,
    currentConnection,
    predictedConnection,
    showLabels = true,
    speedMultiplier = 60
}) => {
    const [orbits, setOrbits] = useState<SatelliteOrbit[]>([])
    const timeRef = useRef(0)

    // 初始化衛星軌道
    useEffect(() => {
        if (!enabled) {
            setOrbits([])
            return
        }

        // 創建 18 顆模擬衛星軌道 - 更好的分佈和時間間隔
        const initialOrbits: SatelliteOrbit[] = Array.from({ length: 18 }, (_, i) => {
            const orbitGroup = Math.floor(i / 6) // 3 個軌道平面，每個6顆衛星
            const satelliteInGroup = i % 6
            
            return {
                id: `sat_${i}`,
                name: `STARLINK-${1000 + i}`,
                azimuthShift: orbitGroup * 60 + satelliteInGroup * 10, // 更分散的分佈
                transitDuration: 90 + Math.random() * 60, // 1.5-2.5 分鐘過境時間
                transitStartTime: i * 15 + Math.random() * 30, // 錯開開始時間，避免全部同時出現
                isTransiting: false,
                isVisible: false,
                nextAppearTime: 0,
                currentPosition: [0, -200, 0]
            }
        })

        setOrbits(initialOrbits)
    }, [enabled, satellites])

    // 更新軌道動畫
    useFrame(() => {
        if (!enabled) return

        timeRef.current += speedMultiplier / 60

        setOrbits(prevOrbits =>
            prevOrbits.map(orbit => {
                const state = calculateOrbitPosition(timeRef.current, orbit, speedMultiplier)
                return {
                    ...orbit,
                    currentPosition: state.position,
                    isVisible: state.isVisible
                }
            })
        )
    })

    const satellitesToRender = orbits.filter(orbit => orbit.isVisible)

    if (!enabled) {
        return null
    }

    return (
        <group>
            {satellitesToRender.map((orbit, index) => {
                const isCurrent = currentConnection?.satelliteId === orbit.id
                const isPredicted = predictedConnection?.satelliteId === orbit.id
                
                let statusColor = '#ffffff'
                if (isCurrent) {
                    statusColor = '#00ff00'
                } else if (isPredicted) {
                    statusColor = '#ffaa00'
                }

                return (
                    <group key={orbit.id}>
                        <StaticModel
                            url={SATELLITE_MODEL_URL}
                            position={orbit.currentPosition}
                            scale={[
                                SATELLITE_CONFIG.SAT_SCALE,
                                SATELLITE_CONFIG.SAT_SCALE,
                                SATELLITE_CONFIG.SAT_SCALE
                            ]}
                            pivotOffset={[0, 0, 0]}
                        />
                        
                        <mesh position={[
                            orbit.currentPosition[0], 
                            orbit.currentPosition[1] + 15, 
                            orbit.currentPosition[2]
                        ]}>
                            <sphereGeometry args={[3, 8, 8]} />
                            <meshBasicMaterial
                                color={statusColor}
                                transparent
                                opacity={0.8}
                            />
                        </mesh>

                        {showLabels && (
                            <Text
                                position={[
                                    orbit.currentPosition[0], 
                                    orbit.currentPosition[1] + 25, 
                                    orbit.currentPosition[2]
                                ]}
                                fontSize={4}
                                color={statusColor}
                                anchorX="center"
                                anchorY="middle"
                            >
                                {orbit.name}
                            </Text>
                        )}
                    </group>
                )
            })}
        </group>
    )
}

export default DynamicSatelliteRenderer