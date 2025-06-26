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

interface DynamicSatelliteRendererProps {
    satellites: unknown[]
    enabled: boolean
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    currentConnection?: any
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

// 衛星軌道位置計算函數 - 支持循環軌道
const calculateOrbitPosition = (
    currentTime: number,
    orbit: SatelliteOrbit,
    _speedMultiplier: number // Reserved for future use
): { position: [number, number, number]; isVisible: boolean } => {
    // 計算總軌道週期 (過境時間 + 不可見時間)
    const totalOrbitPeriod = orbit.transitDuration + 120 // 2分鐘不可見間隔

    // 計算從開始時間到現在的相對時間
    const relativeTime = currentTime - orbit.transitStartTime

    // 使用模運算實現循環軌道
    const normalizedTime =
        ((relativeTime % totalOrbitPeriod) + totalOrbitPeriod) %
        totalOrbitPeriod

    // 檢查是否在過境期間
    const isInTransit = normalizedTime <= orbit.transitDuration

    if (!isInTransit) {
        return {
            position: [0, -200, 0] as [number, number, number], // 隱藏在地下
            isVisible: false,
        }
    }

    // 計算過境進度 (0 到 1)
    const transitProgress = normalizedTime / orbit.transitDuration

    // 計算軌道位置 - 完整的半圓弧軌道
    const azimuthShift = (orbit.azimuthShift * Math.PI) / 180
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
    // speedMultiplier is currently fixed to 1x real time and not configurable
    algorithmResults,
    handoverState,
    // onSatelliteClick is reserved for future satellite interaction features
    onSatellitePositions,
}) => {
    const [orbits, setOrbits] = useState<SatelliteOrbit[]>([])
    const timeRef = useRef(0)
    const lastPositionsRef = useRef<Map<string, [number, number, number]>>(
        new Map()
    )

    // 🔄 使用 useRef 保存回調函數，避免依賴變化
    const onSatellitePositionsRef = useRef(onSatellitePositions)
    onSatellitePositionsRef.current = onSatellitePositions

    // 演算法狀態對接 - 用於顯示後端演算法結果
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [algorithmHighlights, setAlgorithmHighlights] = useState<{
        currentSatellite?: string
        predictedSatellite?: string
        handoverPath?: string[]
        algorithmStatus?: 'idle' | 'calculating' | 'handover_ready'
    }>({})

    // 真實衛星數據狀態
    const [realSatelliteMapping, setRealSatelliteMapping] = useState<
        Map<string, RealSatelliteInfo>
    >(new Map())

    const [useRealData, __setUseRealData] = useState(true) // 預設使用真實數據疊加
    const [realDataStatus, setRealDataStatus] = useState<
        'loading' | 'success' | 'error' | 'stale'
    >('loading')

    // 更新真實衛星數據
    useEffect(() => {
        if (!enabled || !useRealData) return

        const updateRealData = () => {
            const mapping = realSatelliteDataManager.getAllMappings()
            const isDataFresh = realSatelliteDataManager.isDataFresh()

            setRealSatelliteMapping(mapping)
            setRealDataStatus(
                mapping.size > 0 ? (isDataFresh ? 'success' : 'stale') : 'error'
            )

            // 更新真實衛星數據映射 (無需記錄)
        }

        // 立即更新一次
        updateRealData()

        // 定期檢查更新
        const interval = setInterval(updateRealData, 5000) // 每5秒檢查一次

        return () => clearInterval(interval)
    }, [enabled, useRealData])

    // 初始化衛星軌道
    useEffect(() => {
        if (!enabled) {
            setOrbits([])
            return
        }

        // 創建 18 顆模擬衛星軌道 - 更好的分佈和時間間隔
        const initialOrbits: SatelliteOrbit[] = Array.from(
            { length: 18 },
            (_, i) => {
                const orbitGroup = Math.floor(i / 6) // 3 個軌道平面，每個6顆衛星
                const satelliteInGroup = i % 6
                const satelliteId = `sat_${i}`

                // 嘗試獲取真實衛星數據
                const realData = realSatelliteMapping.get(satelliteId)
                const satelliteName = realData?.name || `STARLINK-${1000 + i}`

                return {
                    id: satelliteId,
                    name: satelliteName,
                    azimuthShift: orbitGroup * 60 + satelliteInGroup * 10, // 更分散的分佈
                    transitDuration: 90 + Math.random() * 60, // 1.5-2.5 分鐘過境時間
                    transitStartTime: i * 15 + Math.random() * 30, // 錯開開始時間，避免全部同時出現
                    isTransiting: false,
                    isVisible: false,
                    nextAppearTime: 0,
                    currentPosition: [0, -200, 0],
                    // 整合真實數據
                    realData: realData,
                    signalStrength:
                        realData?.signal_quality.estimated_signal_strength,
                    elevation: realData?.position.elevation,
                    azimuth: realData?.position.azimuth,
                }
            }
        )

        setOrbits(initialOrbits)
    }, [enabled, satellites, realSatelliteMapping])

    // 更新軌道動畫
    useFrame(() => {
        if (!enabled) return

        timeRef.current += 1 / 60 // Fixed to 1x real time

        // 使用 ref 直接更新位置，避免觸發 React re-render
        const hasChanges = orbitsRef.current.some((orbit) => {
            const state = calculateOrbitPosition(
                timeRef.current,
                orbit,
                1 // Fixed to 1x real time
            )

            // 檢查位置是否有顯著變化
            const positionChanged =
                Math.abs(orbit.currentPosition[0] - state.position[0]) > 1.0 ||
                Math.abs(orbit.currentPosition[1] - state.position[1]) > 1.0 ||
                Math.abs(orbit.currentPosition[2] - state.position[2]) > 1.0 ||
                orbit.isVisible !== state.isVisible

            if (positionChanged) {
                orbit.currentPosition = state.position
                orbit.isVisible = state.isVisible
                return true
            }
            return false
        })

        // 只有在有顯著變化時才觸發 React 更新
        if (hasChanges) {
            setOrbits([...orbitsRef.current])
        }
    })

    // 🔗 使用 useRef 來避免在 useEffect 中依賴不斷變化的 orbits
    const orbitsRef = useRef<SatelliteOrbit[]>([])
    orbitsRef.current = orbits

    // 🔄 位置更新邏輯 - 修復無限循環問題
    useEffect(() => {
        if (!enabled) return

        const updatePositions = () => {
            // 使用 ref 檢查回調函數是否存在
            if (!onSatellitePositionsRef.current) return

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
    }, [enabled]) // 只依賴 enabled

    const satellitesToRender = orbits.filter((orbit) => orbit.isVisible)

    if (!enabled) {
        return null
    }

    return (
        <group>
            {satellitesToRender.map((orbit) => {
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
                const opacity = 1.0 // 完全不透明
                let scale = 1

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
                                scale = 1.3
                                break
                            case 'preparing':
                                statusColor = '#ffaa00' // 橙黃色 - 準備換手
                                scale = 1.3
                                break
                            case 'establishing':
                                statusColor = '#ffdd00' // 亮黃色 - 建立新連接
                                scale = 1.2
                                break
                            case 'switching':
                                statusColor = '#aaaaaa' // 淺灰色 - 換手中
                                scale = 1.1
                                break
                            case 'completing':
                                statusColor = '#aaaaaa' // 淺灰色 - 完成中
                                scale = 1.0
                                break
                            default:
                                statusColor = '#00ff00'
                                scale = 1.3
                        }
                    } else if (isHandoverTarget) {
                        // 目標衛星
                        switch (handoverState.phase) {
                            case 'preparing':
                                statusColor = '#0088ff' // 藍色 - 準備連接
                                scale = 1.2
                                break
                            case 'establishing':
                                statusColor = '#0088ff' // 藍色 - 建立連接中
                                scale = 1.3
                                break
                            case 'switching':
                                statusColor = '#00ff00' // 綠色 - 換手為主要連接
                                scale = 1.4
                                break
                            case 'completing':
                                statusColor = '#00ff00' // 綠色 - 新的主要連接
                                scale = 1.4
                                break
                            default:
                                statusColor = '#0088ff'
                                scale = 1.2
                        }
                    }
                } else {
                    // 普通衛星 - 保持白色
                    statusColor = '#ffffff' // 預設白色
                    // opacity and scale are set but could be used for future customization
                }

                return (
                    <group key={orbit.id}>
                        <StaticModel
                            url={SATELLITE_MODEL_URL}
                            position={orbit.currentPosition}
                            scale={[
                                SATELLITE_CONFIG.SAT_SCALE * (scale || 1),
                                SATELLITE_CONFIG.SAT_SCALE * (scale || 1),
                                SATELLITE_CONFIG.SAT_SCALE * (scale || 1),
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
                                opacity={opacity || 0.7}
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
                                {!orbit.realData &&
                                    useRealData &&
                                    realDataStatus === 'success' &&
                                    '\n[演示模擬]'}
                            </Text>
                        )}
                    </group>
                )
            })}
        </group>
    )
}

export default DynamicSatelliteRenderer
