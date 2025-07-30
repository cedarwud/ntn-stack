/**
 * Phase 2: 衛星軌跡動畫控制器
 *
 * 基於 Phase 0 預計算數據實現平滑的衛星動畫
 * 支援 60 倍加速、距離縮放和時間軸控制
 */

import React, { useRef, useEffect, useState, useCallback } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import {
    PrecomputedOrbitService,
    AnimationConfig,
} from '../../../../services/PrecomputedOrbitService'
import type {
    OrbitData,
    SatelliteTrajectory,
    HandoverEvent,
} from '../../../../types/satellite'

export interface SatelliteAnimationControllerProps {
    enabled: boolean
    location: string
    constellation: 'starlink' | 'oneweb'
    animationConfig: AnimationConfig
    onHandoverEvent?: (event: HandoverEvent) => void
    onSatellitePositions?: (
        positions: Map<string, [number, number, number]>
    ) => void
    // 修復：使用統一的衛星數據源
    unifiedSatellites?: any[]
    children?: React.ReactNode
}

export interface TimelineControl {
    isPlaying: boolean
    currentTime: number
    totalDuration: number
    speed: number
    onPlay: () => void
    onPause: () => void
    onSeek: (time: number) => void
    onSpeedChange: (speed: number) => void
}

interface PrecomputedSatellite {
    norad_id: string
    name: string
    trajectory: SatelliteTrajectory
    handoverEvents: HandoverEvent[]
    isVisible: boolean
    currentPosition: [number, number, number]
    currentVelocity: [number, number, number]
}

export const SatelliteAnimationController: React.FC<
    SatelliteAnimationControllerProps
> = ({
    enabled,
    location,
    constellation,
    animationConfig,
    onHandoverEvent,
    onSatellitePositions,
    unifiedSatellites = [],
    children,
}) => {
    const [orbitService] = useState(() => new PrecomputedOrbitService())
    const [precomputedData, setPrecomputedData] = useState<OrbitData | null>(
        null
    )
    const [satellites, setSatellites] = useState<
        Map<string, PrecomputedSatellite>
    >(new Map())
    const [timelineControl, setTimelineControl] = useState<TimelineControl>({
        isPlaying: true,
        currentTime: 0,
        totalDuration: 21600, // 6 小時 (秒)
        speed: animationConfig.acceleration,
        onPlay: () =>
            setTimelineControl((prev) => ({ ...prev, isPlaying: true })),
        onPause: () =>
            setTimelineControl((prev) => ({ ...prev, isPlaying: false })),
        onSeek: (time: number) =>
            setTimelineControl((prev) => ({ ...prev, currentTime: time })),
        onSpeedChange: (speed: number) =>
            setTimelineControl((prev) => ({ ...prev, speed })),
    })

    const animationStartTime = useRef<number>(Date.now())
    const lastHandoverCheck = useRef<number>(0)

    // 修復：優先使用統一的衛星數據，回退到預計算數據載入
    useEffect(() => {
        if (!enabled) return

        // 修復：完全依賴統一的衛星數據，不再回退到獨立的預計算數據載入
        if (unifiedSatellites && unifiedSatellites.length > 0) {
            // 只在數據異常時記錄日誌
            if (unifiedSatellites.length === 0) {
                console.log(`⚠️ SatelliteAnimationController: [${constellation.toUpperCase()}] 無衛星數據`)
            } else if (unifiedSatellites.length > 20) {
                console.log(`⚠️ SatelliteAnimationController: [${constellation.toUpperCase()}] 衛星數量異常: ${unifiedSatellites.length}顆`)
            }
            initializeSatellitesFromUnified(unifiedSatellites)
        } else {
            // 如果沒有統一數據，清空衛星顯示
            console.log(
                `⚠️ SatelliteAnimationController: 沒有統一衛星數據 [${constellation.toUpperCase()}]，清空顯示`
            )
            setSatellites(new Map())
        }
    }, [enabled, location, constellation, unifiedSatellites, orbitService])

    // 修復：從統一衛星數據初始化
    const initializeSatellitesFromUnified = useCallback(
        (unifiedSats: any[]) => {
            const satelliteMap = new Map<string, PrecomputedSatellite>()

            unifiedSats.forEach((sat: any) => {
                // 將統一數據轉換為動畫控制器格式
                const satellite: PrecomputedSatellite = {
                    norad_id:
                        sat.norad_id?.toString() ||
                        sat.id?.toString() ||
                        'unknown',
                    name: sat.name || `SAT-${sat.norad_id || sat.id}`,
                    trajectory: {
                        timePoints: [0], // 簡化：使用當前時間點
                        positions: [
                            [
                                // 修復：支援多種字段名格式
                                // 使用球面座標轉換為3D位置（簡化版）
                                (sat.distance_km || sat.range_km || 1000) *
                                    Math.cos(
                                        ((sat.elevation_deg ||
                                            sat.elevation ||
                                            0) *
                                            Math.PI) /
                                            180
                                    ) *
                                    Math.cos(
                                        ((sat.azimuth_deg || sat.azimuth || 0) *
                                            Math.PI) /
                                            180
                                    ),
                                (sat.distance_km || sat.range_km || 1000) *
                                    Math.sin(
                                        ((sat.elevation_deg ||
                                            sat.elevation ||
                                            0) *
                                            Math.PI) /
                                            180
                                    ),
                                (sat.distance_km || sat.range_km || 1000) *
                                    Math.cos(
                                        ((sat.elevation_deg ||
                                            sat.elevation ||
                                            0) *
                                            Math.PI) /
                                            180
                                    ) *
                                    Math.sin(
                                        ((sat.azimuth_deg || sat.azimuth || 0) *
                                            Math.PI) /
                                            180
                                    ),
                            ],
                        ],
                        velocities: [[0, 0, 0]], // 簡化：無速度數據
                        visibilityWindows: sat.is_visible
                            ? [{ start: 0, end: 3600 }]
                            : [],
                    },
                    handoverEvents: [],
                    isVisible: sat.is_visible || false,
                    // 修復：使用計算出的實際位置，而不是 [0, 0, 0]
                    currentPosition: [
                        // 使用球面座標轉換為3D位置（簡化版）
                        (sat.distance_km || sat.range_km || 1000) *
                            Math.cos(
                                ((sat.elevation_deg || sat.elevation || 0) *
                                    Math.PI) /
                                    180
                            ) *
                            Math.cos(
                                ((sat.azimuth_deg || sat.azimuth || 0) *
                                    Math.PI) /
                                    180
                            ),
                        (sat.distance_km || sat.range_km || 1000) *
                            Math.sin(
                                ((sat.elevation_deg || sat.elevation || 0) *
                                    Math.PI) /
                                    180
                            ),
                        (sat.distance_km || sat.range_km || 1000) *
                            Math.cos(
                                ((sat.elevation_deg || sat.elevation || 0) *
                                    Math.PI) /
                                    180
                            ) *
                            Math.sin(
                                ((sat.azimuth_deg || sat.azimuth || 0) *
                                    Math.PI) /
                                    180
                            ),
                    ],
                    currentVelocity: [0, 0, 0],
                }

                satelliteMap.set(satellite.norad_id, satellite)
            })

            setSatellites(satelliteMap)

            // 只在轉換失敗時記錄日誌
            if (satelliteMap.size === 0 && unifiedSats.length > 0) {
                console.warn(`⚠️ SatelliteAnimationController: 衛星數據轉換失敗，原始: ${unifiedSats.length}，轉換: ${satelliteMap.size}`)
            }
        },
        []
    )

    // 初始化衛星數據（預計算數據）
    const initializeSatellites = useCallback((data: OrbitData) => {
        const satelliteMap = new Map<string, PrecomputedSatellite>()

        // 從預計算數據中提取衛星軌跡
        data.filtered_satellites?.forEach((sat: any) => {
            const satellite: PrecomputedSatellite = {
                norad_id: sat.norad_id,
                name: sat.name || `SAT-${sat.norad_id}`,
                trajectory: {
                    timePoints: [],
                    positions: [],
                    velocities: [],
                    visibilityWindows: [],
                },
                handoverEvents: [],
                isVisible: false,
                currentPosition: [0, 0, 0],
                currentVelocity: [0, 0, 0],
            }

            satelliteMap.set(sat.norad_id, satellite)
        })

        setSatellites(satelliteMap)
    }, [])

    // 插值計算衛星位置
    const interpolatePosition = useCallback(
        (
            trajectory: SatelliteTrajectory,
            currentTime: number,
            recursionDepth: number = 0
        ): {
            position: [number, number, number]
            velocity: [number, number, number]
            isVisible: boolean
        } => {
            // 防止無限遞歸
            if (recursionDepth > 5) {
                console.warn(
                    'interpolatePosition: 達到最大遞歸深度，返回預設值'
                )
                return {
                    position: [0, -1000, 0],
                    velocity: [0, 0, 0],
                    isVisible: false,
                }
            }

            if (!trajectory.timePoints || trajectory.timePoints.length === 0) {
                return {
                    position: [0, -1000, 0], // 隱藏在地下
                    velocity: [0, 0, 0],
                    isVisible: false,
                }
            }

            // 修復：對於統一數據的衛星（只有一個時間點），直接返回固定位置
            if (
                trajectory.timePoints.length === 1 &&
                trajectory.timePoints[0] === 0
            ) {
                return {
                    position: trajectory.positions[0] || [0, -1000, 0],
                    velocity: trajectory.velocities[0] || [0, 0, 0],
                    isVisible:
                        trajectory.visibilityWindows.some(
                            (window) =>
                                currentTime >= window.start &&
                                currentTime <= window.end
                        ) || true, // 統一數據的衛星預設可見
                }
            }

            // 找到當前時間對應的軌跡點
            const timeIndex = trajectory.timePoints.findIndex(
                (t) => t > currentTime
            )

            if (timeIndex === -1) {
                // 超出軌跡範圍，使用最後一個點而非遞歸
                const lastIndex = trajectory.timePoints.length - 1
                const maxTime = trajectory.timePoints[lastIndex]

                // 如果時間點無效，直接返回最後一個位置
                if (!maxTime || maxTime <= 0) {
                    return {
                        position: trajectory.positions[lastIndex] || [
                            0, -1000, 0,
                        ],
                        velocity: trajectory.velocities[lastIndex] || [0, 0, 0],
                        isVisible: false,
                    }
                }

                // 循環到軌跡開始（但限制遞歸深度）
                const cycleTime = currentTime % maxTime
                return interpolatePosition(
                    trajectory,
                    cycleTime,
                    recursionDepth + 1
                )
            }

            if (timeIndex === 0) {
                // 在軌跡開始之前，使用第一個點
                return {
                    position: trajectory.positions[0] || [0, -1000, 0],
                    velocity: trajectory.velocities[0] || [0, 0, 0],
                    isVisible: trajectory.visibilityWindows.some(
                        (window) =>
                            currentTime >= window.start &&
                            currentTime <= window.end
                    ),
                }
            }

            // 線性插值
            const t1 = trajectory.timePoints[timeIndex - 1]
            const t2 = trajectory.timePoints[timeIndex]
            const factor = (currentTime - t1) / (t2 - t1)

            const pos1 = trajectory.positions[timeIndex - 1] || [0, 0, 0]
            const pos2 = trajectory.positions[timeIndex] || [0, 0, 0]
            const vel1 = trajectory.velocities[timeIndex - 1] || [0, 0, 0]
            const vel2 = trajectory.velocities[timeIndex] || [0, 0, 0]

            const interpolatedPosition: [number, number, number] = [
                pos1[0] + (pos2[0] - pos1[0]) * factor,
                pos1[1] + (pos2[1] - pos1[1]) * factor,
                pos1[2] + (pos2[2] - pos1[2]) * factor,
            ]

            const interpolatedVelocity: [number, number, number] = [
                vel1[0] + (vel2[0] - vel1[0]) * factor,
                vel1[1] + (vel2[1] - vel1[1]) * factor,
                vel1[2] + (vel2[2] - vel1[2]) * factor,
            ]

            // 應用距離縮放
            const scaledPosition: [number, number, number] = [
                interpolatedPosition[0] * animationConfig.distanceScale,
                interpolatedPosition[1] * animationConfig.distanceScale,
                interpolatedPosition[2] * animationConfig.distanceScale,
            ]

            return {
                position: scaledPosition,
                velocity: interpolatedVelocity,
                isVisible: trajectory.visibilityWindows.some(
                    (window) =>
                        currentTime >= window.start && currentTime <= window.end
                ),
            }
        },
        [animationConfig.distanceScale]
    )

    // 動畫更新循環
    useFrame((state, delta) => {
        if (!enabled || !timelineControl.isPlaying || satellites.size === 0)
            return

        // 更新動畫時間
        const newTime =
            timelineControl.currentTime + delta * timelineControl.speed

        if (newTime > timelineControl.totalDuration) {
            // 循環播放
            setTimelineControl((prev) => ({ ...prev, currentTime: 0 }))
            animationStartTime.current = Date.now()
            return
        }

        setTimelineControl((prev) => ({ ...prev, currentTime: newTime }))

        // 更新所有衛星位置
        const updatedSatellites = new Map(satellites)
        const currentPositions = new Map<string, [number, number, number]>()

        updatedSatellites.forEach((satellite, noradId) => {
            const { position, velocity, isVisible } = interpolatePosition(
                satellite.trajectory,
                newTime
            )

            satellite.currentPosition = position
            satellite.currentVelocity = velocity
            satellite.isVisible = isVisible

            if (isVisible) {
                currentPositions.set(noradId, position)
            }
        })

        setSatellites(updatedSatellites)

        // 通知父組件衛星位置更新
        if (onSatellitePositions) {
            onSatellitePositions(currentPositions)
        }

        // 檢查換手事件 (每秒檢查一次)
        if (newTime - lastHandoverCheck.current >= 1.0) {
            checkHandoverEvents(newTime)
            lastHandoverCheck.current = newTime
        }
    })

    // 檢查換手事件
    const checkHandoverEvents = useCallback(
        (currentTime: number) => {
            satellites.forEach((satellite) => {
                satellite.handoverEvents.forEach((event) => {
                    if (
                        Math.abs(event.timestamp - currentTime) < 0.5 &&
                        onHandoverEvent
                    ) {
                        onHandoverEvent(event)
                    }
                })
            })
        },
        [satellites, onHandoverEvent]
    )

    // 渲染衛星
    const renderSatellites = () => {
        const visibleSatellites = Array.from(satellites.values()).filter(
            (sat) => sat.isVisible
        )

        return visibleSatellites.map((satellite) => (
            <group
                key={satellite.norad_id}
                position={satellite.currentPosition}
            >
                {/* 衛星模型 */}
                <mesh>
                    <sphereGeometry args={[2, 8, 8]} />
                    <meshBasicMaterial color="#00ff00" />
                </mesh>

                {/* 衛星標籤 */}
                <group position={[0, 5, 0]}>
                    <mesh>
                        <planeGeometry args={[20, 4]} />
                        <meshBasicMaterial
                            color="#000000"
                            transparent
                            opacity={0.7}
                        />
                    </mesh>
                    {/* 這裡可以添加 Text 組件顯示衛星名稱 */}
                </group>

                {/* 軌跡線 */}
                {animationConfig.smoothing && (
                    <line>
                        <bufferGeometry>
                            <bufferAttribute
                                attach="attributes-position"
                                count={satellite.trajectory.positions.length}
                                array={
                                    new Float32Array(
                                        satellite.trajectory.positions.flat()
                                    )
                                }
                                itemSize={3}
                            />
                        </bufferGeometry>
                        <lineBasicMaterial
                            color="#ffffff"
                            opacity={0.3}
                            transparent
                        />
                    </line>
                )}
            </group>
        ))
    }

    if (!enabled || !precomputedData) {
        return <>{children}</>
    }

    return (
        <group>
            {renderSatellites()}
            {children}
        </group>
    )
}

export default SatelliteAnimationController
