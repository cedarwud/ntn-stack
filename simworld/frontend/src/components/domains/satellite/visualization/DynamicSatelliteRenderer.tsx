/**
 * 重構後的動態衛星渲染器
 * 統一軌道計算邏輯，基於真實SGP4數據，實現正確的升降軌跡
 * 🎯 整合動態池支持：自動使用Stage 6優化的156顆衛星池數據
 */

import React, { useRef, useState, useCallback, useMemo, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import StaticModel from '../../../scenes/StaticModel'
import { SATELLITE_CONFIG } from '../../../../config/satellite.config'
import { useSatelliteData } from '../../../../contexts/SatelliteDataContext'

// 🚀 使用統一的類型和工具
import { 
    StandardSatelliteData,
    SatelliteRendererProps,
    HandoverState,
    AlgorithmResults
} from '../../../../types/satellite'
import { 
    SatelliteOrbitCalculator,
    OrbitCalculationResult
} from '../../../../utils/satellite/SatelliteOrbitCalculator'

interface SatelliteRenderState {
    id: string
    name: string
    position: [number, number, number]
    isVisible: boolean
    progress: number
    signalStrength: number
    visualState: {
        color: string
        scale: number
        opacity: number
        isHighlighted: boolean
    }
}

const SATELLITE_MODEL_URL = '/static/models/sat.glb'

/**
 * 重構後的動態衛星渲染器
 * 簡化邏輯，統一計算，消除重複代碼
 */
const DynamicSatelliteRenderer: React.FC<SatelliteRendererProps> = ({
    enabled,
    satellites,
    showLabels = true,
    speedMultiplier = 1,
    algorithmResults,
    handoverState,
    onSatelliteClick,
    onSatellitePositions,
}) => {
    // 狀態管理
    const [renderStates, setRenderStates] = useState<SatelliteRenderState[]>([])
    const timeRef = useRef(0)
    const lastPositionsRef = useRef<Map<string, [number, number, number]>>(new Map())
    
    // 🎯 獲取動態池狀態
    const { getPoolStatistics } = useSatelliteData()
    const [poolStats, setPoolStats] = useState<any>(null)
    
    // 🎯 核心：預處理衛星時間序列數據
    const satelliteTimeseriesMap = useMemo(() => {
        const map = new Map<string, StandardSatelliteData>()
        satellites.forEach(sat => {
            if (sat.position_timeseries && sat.position_timeseries.length > 0) {
                map.set(sat.id, sat)
            }
        })
        
        // 收到的是池過濾後的數據
        
        return map
    }, [satellites])

    // 🚀 統一軌道計算和狀態更新
    const updateSatelliteStates = useCallback(() => {
        const newStates: SatelliteRenderState[] = []
        const positionMap = new Map<string, [number, number, number]>()
        
        satelliteTimeseriesMap.forEach((satellite) => {
            if (!satellite.position_timeseries) return
            
            // ✅ 使用統一的軌道計算器
            const orbitResult: OrbitCalculationResult = SatelliteOrbitCalculator.calculateOrbitPosition(
                satellite.position_timeseries,
                timeRef.current,
                speedMultiplier
            )
            
            // 🎨 計算視覺狀態
            const visualState = calculateVisualState(satellite, algorithmResults, handoverState)
            
            // 📊 生成渲染狀態
            const renderState: SatelliteRenderState = {
                id: satellite.id,
                name: satellite.name,
                position: orbitResult.position,
                isVisible: orbitResult.isVisible,
                progress: orbitResult.progress,
                signalStrength: satellite.signal_quality.estimated_signal_strength,
                visualState
            }
            
            newStates.push(renderState)
            
            // 記錄位置用於回調
            if (orbitResult.isVisible) {
                positionMap.set(satellite.id, orbitResult.position)
                positionMap.set(satellite.name, orbitResult.position)
            }
        })
        
        setRenderStates(newStates)
        
        // 🔄 位置回調（避免過度調用）
        if (onSatellitePositions && positionMap.size > 0) {
            const hasChanges = checkPositionChanges(positionMap)
            if (hasChanges) {
                lastPositionsRef.current = positionMap
                onSatellitePositions(positionMap)
            }
        }
    }, [satelliteTimeseriesMap, speedMultiplier, algorithmResults, handoverState, onSatellitePositions])

    // 📊 更新池統計信息
    useEffect(() => {
        const stats = getPoolStatistics()
        setPoolStats(stats)
    }, [getPoolStatistics, satellites])

    // 🔄 動畫幀更新
    useFrame(() => {
        if (!enabled) return
        
        // 更新時間（每幀遞增）
        timeRef.current += speedMultiplier / 60
        
        // 更新衛星狀態
        updateSatelliteStates()
    })

    // 📍 檢查位置變化（避免無意義的回調）
    const checkPositionChanges = useCallback((
        newPositions: Map<string, [number, number, number]>
    ): boolean => {
        const threshold = 2.0 // 2單位的變化才觸發回調
        
        for (const [id, newPos] of newPositions) {
            const lastPos = lastPositionsRef.current.get(id)
            if (!lastPos || 
                Math.abs(lastPos[0] - newPos[0]) > threshold ||
                Math.abs(lastPos[1] - newPos[1]) > threshold ||
                Math.abs(lastPos[2] - newPos[2]) > threshold) {
                return true
            }
        }
        return false
    }, [])

    // 🎨 計算視覺狀態（顏色、縮放、透明度等）
    const calculateVisualState = (
        satellite: StandardSatelliteData,
        algorithmResults?: AlgorithmResults,
        handoverState?: HandoverState
    ) => {
        let color = '#ffffff' // 默認白色
        let scale = 0.8
        const opacity = 0.8
        let isHighlighted = false

        // 🎯 演算法結果高亮
        const isAlgorithmCurrent = algorithmResults?.currentSatelliteId === satellite.id ||
            algorithmResults?.currentSatelliteId === satellite.name
        const isAlgorithmPredicted = algorithmResults?.predictedSatelliteId === satellite.id ||
            algorithmResults?.predictedSatelliteId === satellite.name

        // 🔗 換手狀態處理
        const isHandoverCurrent = handoverState?.currentSatelliteId === satellite.id ||
            handoverState?.currentSatelliteId === satellite.name
        const isHandoverTarget = handoverState?.targetSatelliteId === satellite.id ||
            handoverState?.targetSatelliteId === satellite.name

        if (handoverState && (isHandoverCurrent || isHandoverTarget)) {
            isHighlighted = true
            
            if (isHandoverCurrent) {
                // 當前連接衛星
                switch (handoverState.phase) {
                    case 'stable':
                        color = '#00ff00' // 綠色
                        scale = 1.3
                        break
                    case 'preparing':
                        color = '#ffaa00' // 橙色
                        scale = 1.3
                        break
                    case 'switching':
                        color = '#aaaaaa' // 灰色
                        scale = 1.1
                        break
                    default:
                        color = '#00ff00'
                        scale = 1.3
                }
            } else if (isHandoverTarget) {
                // 目標衛星
                switch (handoverState.phase) {
                    case 'preparing':
                        color = '#0088ff' // 藍色
                        scale = 1.2
                        break
                    case 'establishing':
                        color = '#0088ff'
                        scale = 1.3
                        break
                    case 'switching':
                        color = '#00ff00' // 成為主要連接
                        scale = 1.4
                        break
                    default:
                        color = '#0088ff'
                        scale = 1.2
                }
            }
        } else if (isAlgorithmCurrent || isAlgorithmPredicted) {
            // 演算法結果高亮
            color = isAlgorithmCurrent ? '#00ff00' : '#0088ff'
            scale = 1.2
            isHighlighted = true
        }

        return {
            color,
            scale,
            opacity: isHighlighted ? 1.0 : opacity,
            isHighlighted
        }
    }

    // 📋 處理衛星點擊
    const handleSatelliteClick = useCallback((satelliteId: string) => {
        if (onSatelliteClick) {
            onSatelliteClick(satelliteId)
        }
    }, [onSatelliteClick])

    // 🚫 組件未啟用時不渲染
    if (!enabled) {
        return null
    }

    // 🎮 渲染可見衛星
    const visibleSatellites = renderStates.filter(state => state.isVisible)

    return (
        <group>
            {visibleSatellites.map((state) => (
                <group key={`${state.id}-${state.name}`}>
                    {/* 🛰️ 衛星3D模型 */}
                    <StaticModel
                        url={SATELLITE_MODEL_URL}
                        position={state.position}
                        scale={[
                            SATELLITE_CONFIG.SAT_SCALE * state.visualState.scale,
                            SATELLITE_CONFIG.SAT_SCALE * state.visualState.scale,
                            SATELLITE_CONFIG.SAT_SCALE * state.visualState.scale,
                        ]}
                        pivotOffset={[0, 0, 0]}
                        onClick={() => handleSatelliteClick(state.id)}
                    />

                    {/* 🌟 狀態指示球 */}
                    <mesh
                        position={[
                            state.position[0],
                            state.position[1] + 15,
                            state.position[2],
                        ]}
                    >
                        <sphereGeometry args={[3 * state.visualState.scale, 16, 16]} />
                        <meshBasicMaterial
                            color={state.visualState.color}
                            transparent
                            opacity={state.visualState.opacity}
                        />
                    </mesh>

                    {/* 🏷️ 衛星標籤 */}
                    {showLabels && (
                        <Text
                            position={[
                                state.position[0],
                                state.position[1] + 35,
                                state.position[2],
                            ]}
                            fontSize={3.5}
                            color={state.visualState.color}
                            anchorX="center"
                            anchorY="middle"
                        >
                            {/* 清理衛星名稱 */}
                            {state.name.replace(' [DTC]', '').replace('[DTC]', '')}
                            
                            {/* 演算法狀態標記 */}
                            {algorithmResults?.currentSatelliteId === state.id && '\n[當前]'}
                            {algorithmResults?.predictedSatelliteId === state.id && '\n[預測]'}
                            
                            {/* 信號強度 */}
                            {state.signalStrength > 0 && 
                                `\n信號: ${state.signalStrength.toFixed(1)}dBm`}
                        </Text>
                    )}
                </group>
            ))}
            
            {/* 調試信息 - 優化版本 */}
            {process.env.NODE_ENV === 'development' && (
                <Text
                    position={[0, 300, 0]}
                    fontSize={4}
                    color="#ffffff"
                    anchorX="center"
                >
                    {`可見: ${visibleSatellites.length}/${satellites.length} | 速度: ${speedMultiplier}x`}
                </Text>
            )}
        </group>
    )
}

export default DynamicSatelliteRenderer