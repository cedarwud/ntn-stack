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
    // 🚀 新增：演算法結果對接接口
    algorithmResults?: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }
    onSatelliteClick?: (satelliteId: string) => void
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
    speedMultiplier = 60,
    algorithmResults,
    onSatelliteClick
}) => {
    const [orbits, setOrbits] = useState<SatelliteOrbit[]>([])
    const timeRef = useRef(0)
    
    // 演算法狀態對接 - 用於顯示後端演算法結果
    const [algorithmHighlights, setAlgorithmHighlights] = useState<{
        currentSatellite?: string
        predictedSatellite?: string
        handoverPath?: string[]
        algorithmStatus?: 'idle' | 'calculating' | 'handover_ready'
    }>({})

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
                // 🔥 對接演算法結果 - 優先使用後端演算法狀態
                // 支援多種 ID 匹配模式：完全匹配、名稱匹配、部分匹配
                const isAlgorithmCurrent = algorithmResults?.currentSatelliteId === orbit.id || 
                                         algorithmResults?.currentSatelliteId === orbit.name ||
                                         (algorithmResults?.currentSatelliteId && orbit.name.includes(algorithmResults.currentSatelliteId))
                const isAlgorithmPredicted = algorithmResults?.predictedSatelliteId === orbit.id ||
                                           algorithmResults?.predictedSatelliteId === orbit.name ||
                                           (algorithmResults?.predictedSatelliteId && orbit.name.includes(algorithmResults.predictedSatelliteId))
                const isCurrent = isAlgorithmCurrent || currentConnection?.satelliteId === orbit.id
                const isPredicted = isAlgorithmPredicted || predictedConnection?.satelliteId === orbit.id
                
                // 🐛 調試信息 - 只在有演算法結果時顯示
                if (algorithmResults?.currentSatelliteId && index === 0) {
                    console.log('🔍 演算法結果匹配檢查:', {
                        algorithmCurrent: algorithmResults.currentSatelliteId,
                        algorithmPredicted: algorithmResults.predictedSatelliteId,
                        sampleOrbitId: orbit.id,
                        sampleOrbitName: orbit.name,
                        matchFound: isAlgorithmCurrent || isAlgorithmPredicted
                    })
                }
                
                // 🎨 根據演算法狀態決定顏色
                let statusColor = '#ffffff' // 預設白色
                let opacity = 0.8
                let scale = 1
                
                // 🧪 測試模式：如果沒有真實演算法結果，使用假數據測試視覺效果
                if (!algorithmResults?.currentSatelliteId) {
                    // 強制前兩顆可見衛星展示不同狀態，便於測試
                    if (index === 0) {
                        statusColor = '#00ff00' // 綠色 - 模擬當前最佳
                        opacity = 1.0
                        scale = 1.5
                    } else if (index === 1) {
                        statusColor = '#ff6600' // 橙色 - 模擬預測目標
                        opacity = 0.9
                        scale = 1.3
                    }
                } else {
                    // 真實演算法結果
                    if (isAlgorithmCurrent) {
                        statusColor = '#00ff00' // 綠色 - 當前最佳衛星
                        opacity = 1.0
                        scale = 1.5 // 稍微放大
                    } else if (isAlgorithmPredicted) {
                        statusColor = '#ff6600' // 橙色 - 預測目標衛星
                        opacity = 0.9
                        scale = 1.3
                    } else if (algorithmResults?.handoverStatus === 'calculating') {
                        statusColor = '#ffff00' // 黃色 - 計算中
                        opacity = 0.6
                    } else if (algorithmResults?.binarySearchActive && (isCurrent || isPredicted)) {
                        statusColor = '#ff0080' // 粉紅色 - Binary Search 活躍
                        opacity = 0.8
                    }
                }
                
                // 保留舊的連接狀態邏輯作為備用
                if (isCurrent && statusColor === '#ffffff') {
                    statusColor = '#00ff00'
                } else if (isPredicted && statusColor === '#ffffff') {
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
                        
                        {/* 🎯 演算法狀態指示器 - 根據後端計算結果動態變化 */}
                        <mesh 
                            position={[
                                orbit.currentPosition[0], 
                                orbit.currentPosition[1] + 15, 
                                orbit.currentPosition[2]
                            ]}
                            onClick={() => onSatelliteClick?.(orbit.id)}
                        >
                            <sphereGeometry args={[3 * scale, 8, 8]} />
                            <meshBasicMaterial
                                color={statusColor}
                                transparent
                                opacity={opacity}
                            />
                        </mesh>
                        
                        {/* 🔬 Binary Search 活躍指示器 */}
                        {algorithmResults?.binarySearchActive && (isAlgorithmCurrent || isAlgorithmPredicted) && (
                            <mesh position={[
                                orbit.currentPosition[0], 
                                orbit.currentPosition[1] + 25, 
                                orbit.currentPosition[2]
                            ]}>
                                <sphereGeometry args={[2, 6, 6]} />
                                <meshBasicMaterial
                                    color="#ff0080"
                                    transparent
                                    opacity={0.8}
                                />
                            </mesh>
                        )}

                        {showLabels && (
                            <Text
                                position={[
                                    orbit.currentPosition[0], 
                                    orbit.currentPosition[1] + (algorithmResults?.binarySearchActive && (isAlgorithmCurrent || isAlgorithmPredicted) ? 35 : 25), 
                                    orbit.currentPosition[2]
                                ]}
                                fontSize={4}
                                color={statusColor}
                                anchorX="center"
                                anchorY="middle"
                            >
                                {/* 🏷️ 顯示衛星名稱 + 演算法狀態 */}
                                {orbit.name}
                                {isAlgorithmCurrent && "\n[當前]"}
                                {isAlgorithmPredicted && "\n[預測]"}
                                {algorithmResults?.predictionConfidence && isAlgorithmPredicted && 
                                    `\n${(algorithmResults.predictionConfidence * 100).toFixed(1)}%`}
                            </Text>
                        )}
                    </group>
                )
            })}
        </group>
    )
}

export default DynamicSatelliteRenderer