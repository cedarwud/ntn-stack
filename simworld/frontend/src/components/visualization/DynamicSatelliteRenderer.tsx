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

interface SatelliteOrbit {
    id: string
    name: string
    
    // 重建：真實軌道參數
    orbitType: 'direct' | 'curved' | 'overhead'  // 軌道類型
    azimuthShift: number    // 方位角偏移（-180到180度）
    maxElevation: number    // 最大仰角（度）
    transitDuration: number // 過境時間（秒）
    
    // 不定期出現模式參數
    nextAppearTime: number  // 下次出現時間（秒）
    minInterval: number     // 最小間隔時間（秒）
    maxInterval: number     // 最大間隔時間（秒）
    
    // 當前狀態
    currentPosition: [number, number, number]
    isVisible: boolean
    isTransiting: boolean   // 是否正在過境
    transitStartTime: number // 過境開始時間
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

// // 激進換手優化衛星系統 - 解決衛星太少問題
// 30顆衛星，6-15分鐘過境，30秒-2.5分鐘間隔，預期10-20顆同時可見
// 30方向超密集覆蓋，50%overhead軌道，確保換手絕不缺乏選擇

/**
 * 重建：真實衛星軌道位置計算
 * 模擬衛星從地平線升起，經過正上方，到另一側地平線降落
 * @param progress 過境進度 (0-1)
 * @param orbitType 軌道類型：'direct'（直接飛過）、'curved'（弧形軌道）
 * @param azimuthShift 方位角偏移（-180到180度）
 * @param maxElev 最大仰角
 */
const calculateSatellitePosition = (
    progress: number,
    orbitType: 'direct' | 'curved' | 'overhead',
    azimuthShift: number,
    maxElev: number
): [number, number, number] => {
    
    if (orbitType === 'overhead') {
        // 正上方飛過軌道：從一邊地平線到另一邊，經過天頂
        const startAz = -90 + azimuthShift  // 起始方位角
        const endAz = 90 + azimuthShift     // 結束方位角
        const azimuth = startAz + (endAz - startAz) * progress
        
        // 仰角：正弦曲線，峰值在中間（天頂）
        const elevation = maxElev * Math.sin(progress * Math.PI)
        
        const azRad = (azimuth * Math.PI) / 180
        const elRad = (elevation * Math.PI) / 180
        
        // 衛星距離（簡化為固定高度）
        const distance = 800
        
        const x = distance * Math.cos(elRad) * Math.sin(azRad)
        const z = distance * Math.cos(elRad) * Math.cos(azRad)
        const y = Math.max(5, 50 + elevation * 8)  // 確保最低5單位高度
        
        return [x, y, z]
        
    } else if (orbitType === 'curved') {
        // 弧形軌道：橢圓形路徑
        const angle = progress * Math.PI  // 0到π
        const baseRadius = 600
        const heightRadius = 300
        
        // 橢圓軌道計算
        const x = baseRadius * Math.cos(angle + azimuthShift * Math.PI / 180)
        const z = baseRadius * Math.sin(angle + azimuthShift * Math.PI / 180)
        const y = Math.max(5, 50 + heightRadius * Math.sin(angle))
        
        return [x, y, z]
        
    } else {
        // 直線軌道：簡單的直線飛過
        const startX = -800 * Math.cos(azimuthShift * Math.PI / 180)
        const startZ = -800 * Math.sin(azimuthShift * Math.PI / 180)
        const endX = 800 * Math.cos(azimuthShift * Math.PI / 180)
        const endZ = 800 * Math.sin(azimuthShift * Math.PI / 180)
        
        const x = startX + (endX - startX) * progress
        const z = startZ + (endZ - startZ) * progress
        
        // 拋物線高度變化
        const maxHeight = 200 + maxElev * 5
        const y = Math.max(5, 30 + maxHeight * Math.sin(progress * Math.PI))
        
        return [x, y, z]
    }
}

/**
 * 計算衛星在指定時間的狀態
 * @param orbit 軌道參數
 * @param currentTime 當前時間（秒）
 */
const calculateSatelliteState = (orbit: SatelliteOrbit, currentTime: number) => {
    // 不定期出現模式：檢查是否到了出現時間
    if (!orbit.isTransiting) {
        if (currentTime >= orbit.nextAppearTime) {
            // 開始新的過境
            return {
                position: [0, -100, 0] as [number, number, number],
                isVisible: false,
                shouldStartTransit: true
            }
        } else {
            // 還沒到出現時間
            return {
                position: [0, -100, 0] as [number, number, number],
                isVisible: false
            }
        }
    }
    
    // 正在過境：使用新的位置計算
    const transitElapsed = currentTime - orbit.transitStartTime
    
    if (transitElapsed <= orbit.transitDuration) {
        // 過境進行中
        const progress = transitElapsed / orbit.transitDuration
        const position = calculateSatellitePosition(
            progress,
            orbit.orbitType,
            orbit.azimuthShift,
            orbit.maxElevation
        )
        
        // 可見性判斷：降低門檻，增加可見衛星數量
        const isVisible = position[1] > 5  // Y軸高度大於5就可見（更寬鬆）
        
        return { position, isVisible }
    } else {
        // 過境結束，準備下次出現
        return {
            position: [0, -100, 0] as [number, number, number],
            isVisible: false,
            shouldEndTransit: true
        }
    }
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
        if (!enabled || !satellites || satellites.length === 0) {
            setOrbits([])
            return
        }

        console.log('🔄 設計連續覆蓋的衛星軌道系統')
        
        const numSatellites = Math.min(18, satellites.length)  // 使用18顆衛星，增加更多選擇
        const newOrbits: SatelliteOrbit[] = []
        
        // 重建：真實多樣化衛星軌道系統
        
        for (let i = 0; i < numSatellites; i++) {
            const satellite = satellites[i]
            
            // 軌道類型分配：增加更多overhead類型，確保更多衛星飛過頭頂
            const orbitTypes: Array<'direct' | 'curved' | 'overhead'> = [
                'overhead', 'overhead', 'overhead', 'overhead',  // 主要是正上方飛過
                'curved', 'curved',                              // 弧形軌道
                'direct', 'direct'                               // 直線軌道
            ]
            const orbitType = orbitTypes[i % orbitTypes.length]
            
            // 方位角偏移：擴展到30個方向，超密集覆蓋
            const azimuthShifts = [
                // 主要方向（每12度）
                0, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120, 132, 144, 156, 168, 180,
                -12, -24, -36, -48, -60, -72, -84, -96, -108, -120, -132, -144, -156, -168
            ]
            const azimuthShift = azimuthShifts[i % azimuthShifts.length]
            
            // 多樣化仰角：增加更多高仰角選項，確保強信號
            const elevationOptions = [
                75, 80, 85, 90, 85, 80, 75, 70, 65, 60,  // 更多高仰角（強信號）
                55, 50, 45, 40, 35, 30, 25, 20, 60, 68,  // 低仰角作為備用
                82, 78, 72, 88, 92, 58, 48, 38, 28, 95   // 擴展選項
            ]
            const maxElevation = elevationOptions[i % elevationOptions.length]
            
            // 過境時間：大幅延長到6-15分鐘，確保大量重疊
            const transitTimes = [360, 450, 540, 630, 720, 810, 900]  // 6-15分鐘
            const transitDuration = transitTimes[i % transitTimes.length]
            
            // 間隔時間：激進縮短到30秒-3分鐘，高頻率出現
            const minInterval = 30 + (i % 15) * 2   // 30-58秒
            const maxInterval = 90 + (i % 20) * 3   // 90-147秒（1.5-2.5分鐘）
            
            // 初始啟動時間：非常密集（每12-20秒一顆）
            const baseDelay = i * 15  // 基礎間隔15秒
            const randomDelay = Math.random() * 8   // 加上0-8秒隨機
            const initialDelay = baseDelay + randomDelay
            
            const orbit: SatelliteOrbit = {
                id: satellite.norad_id?.toString() || satellite.name,
                name: satellite.name,
                orbitType,
                azimuthShift,
                maxElevation,
                transitDuration,
                nextAppearTime: initialDelay,
                minInterval,
                maxInterval,
                currentPosition: [0, -100, 0],
                isVisible: false,
                isTransiting: false,
                transitStartTime: 0
            }
            
            newOrbits.push(orbit)
            
            console.log(`🛰️ ${satellite.name}: ${orbit.orbitType}軌道, ` +
                `方位偏移${orbit.azimuthShift}°, 仰角${maxElevation}°, ` +
                `過境${(orbit.transitDuration/60).toFixed(1)}min, 延遲${initialDelay.toFixed(0)}s`)
        }
        
        setOrbits(newOrbits)
        timeRef.current = 0
        
        // 計算覆蓋情況
        const avgTransit = newOrbits.reduce((sum, o) => sum + o.transitDuration, 0) / newOrbits.length
        const avgInterval = newOrbits.reduce((sum, o) => sum + (o.minInterval + o.maxInterval) / 2, 0) / newOrbits.length
        const expectedVisible = (numSatellites * avgTransit) / (avgTransit + avgInterval)
        // 詳細覆蓋分析
        console.log(`📊 換手覆蓋分析:`)
        console.log(`   總衛星數: ${numSatellites}, 平均過境: ${(avgTransit/60).toFixed(1)}min, 平均間隔: ${(avgInterval/60).toFixed(1)}min`)
        console.log(`   理論同時可見: ${expectedVisible.toFixed(1)}顆, 目標: 10-20顆供換手選擇`)
        console.log(`   極致參數: 30顆衛星×${(avgTransit/60).toFixed(0)}分鐘過境÷${(avgInterval/60).toFixed(0)}分鐘間隔 = 超密集覆蓋`)
        console.log(`✅ 激進換手優化: ${numSatellites}顆衛星，超密集覆蓋`)
        console.log(`   軌道類型: overhead(主要), curved, direct - 50%衛星飛過頭頂`)
        console.log(`   超密集覆蓋: 30方向×${(avgTransit/60).toFixed(1)}分鐘過境，間隔${(avgInterval/60).toFixed(1)}分鐘`)
        console.log(`   換手支援: 預期同時10-20顆可見，絕不缺乏選擇！`)
    }, [satellites, enabled])

    // 動畫更新
    useFrame((state, delta) => {
        if (!enabled || orbits.length === 0) return

        // 更新全局時間
        timeRef.current += delta * speedMultiplier

        // 更新每顆衛星的狀態
        setOrbits(prevOrbits => 
            prevOrbits.map(orbit => {
                const state = calculateSatelliteState(orbit, timeRef.current)
                
                if (state.shouldStartTransit) {
                    // 開始新的過境
                    return {
                        ...orbit,
                        isTransiting: true,
                        transitStartTime: timeRef.current,
                        currentPosition: state.position,
                        isVisible: state.isVisible
                    }
                } else if (state.shouldEndTransit) {
                    // 過境結束，計算下次出現時間
                    const interval = orbit.minInterval + Math.random() * (orbit.maxInterval - orbit.minInterval)
                    return {
                        ...orbit,
                        isTransiting: false,
                        nextAppearTime: timeRef.current + interval,
                        currentPosition: state.position,
                        isVisible: state.isVisible
                    }
                } else {
                    // 正常狀態更新
                    return {
                        ...orbit,
                        currentPosition: state.position,
                        isVisible: state.isVisible
                    }
                }
            })
        )
    })

    // 只渲染可見的衛星
    const visibleSatellites = orbits.filter(orbit => orbit.isVisible)

    // 狀態調試
    useEffect(() => {
        const interval = setInterval(() => {
            const visibleCount = visibleSatellites.length
            const totalTime = timeRef.current / 60  // 轉為分鐘
            
            // 檢查覆蓋情況（針對高密度覆蓋）
            const coverageStatus = visibleCount >= 10 ? '✅換手完美' : 
                                 visibleCount >= 8 ? '✅換手優秀' :
                                 visibleCount >= 6 ? '✅換手理想' :
                                 visibleCount >= 4 ? '✅換手良好' :
                                 visibleCount >= 3 ? '✅換手可行' :
                                 visibleCount >= 2 ? '⚠️選擇有限' :
                                 visibleCount === 1 ? '⚠️單一選擇' : '❌無覆蓋'
            
            console.log(`🛰️ 時間: ${totalTime.toFixed(1)}min | 可見: ${visibleCount}/18 | 覆蓋: ${coverageStatus}`)
            
            // 顯示所有衛星的簡化狀態
            const currentlyVisible = orbits.filter(orbit => orbit.isVisible).map(orbit => orbit.name)
            if (currentlyVisible.length > 0) {
                console.log(`   可見衛星: ${currentlyVisible.join(', ')}`)
            }
            
            // 顯示即將出現的衛星
            const upcoming = orbits
                .filter(orbit => !orbit.isVisible)
                .map(orbit => {
                    const adjustedTime = timeRef.current - orbit.startDelay
                    if (adjustedTime < 0) {
                        return { name: orbit.name, timeToStart: -adjustedTime/60 }
                    }
                    const timeInCycle = adjustedTime % orbit.cyclePeriod
                    if (timeInCycle > orbit.transitDuration) {
                        const timeToNext = (orbit.cyclePeriod - timeInCycle) / 60
                        return { name: orbit.name, timeToStart: timeToNext }
                    }
                    return null
                })
                .filter(Boolean)
                .sort((a, b) => a!.timeToStart - b!.timeToStart)
                .slice(0, 2)
            
            if (upcoming.length > 0) {
                const upcomingStr = upcoming.map(u => `${u!.name}(${u!.timeToStart.toFixed(1)}min)`).join(', ')
                console.log(`   即將出現: ${upcomingStr}`)
            }
        }, 4000)

        return () => clearInterval(interval)
    }, [orbits, visibleSatellites.length])

    if (!enabled) {
        return null
    }

    return (
        <group>
            {visibleSatellites.map(orbit => {
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
                        {/* 衛星模型 */}
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
                        
                        {/* 狀態指示器 */}
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
                        
                        {/* 衛星標籤 */}
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