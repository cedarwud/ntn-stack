import React, { useState, useEffect, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Ring, Text } from '@react-three/drei'

interface HandoverAnimation3DProps {
    devices: any[]
    enabled: boolean
    satellitePositions?: Map<string, [number, number, number]>
    stableDuration?: number // 穩定期時間（秒）
    onStatusUpdate?: (statusInfo: any) => void // 狀態更新回調
    onHandoverStateUpdate?: (state: any) => void // 換手狀態回調，供衛星光球使用
}

// 🎯 狀態面板組件（在Canvas外部顯示）
interface HandoverStatusPanelProps {
    enabled: boolean
    statusInfo: any
}

const HandoverStatusPanel: React.FC<HandoverStatusPanelProps> = ({
    enabled,
    statusInfo,
}) => {
    if (!enabled || !statusInfo) return null

    return (
        <div
            style={{
                position: 'fixed',
                top: '80px', // 增加間距，不直接貼齊
                right: '20px',
                zIndex: 800, // 低於換手性能監控
                pointerEvents: 'none',
                background:
                    'linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 41, 59, 0.8))',
                backdropFilter: 'blur(16px)',
                border: '1px solid rgba(148, 163, 184, 0.3)',
                borderRadius: '16px',
                padding: '20px 24px',
                color: 'white',
                fontFamily:
                    '"SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: '16px',
                minWidth: '280px',
                boxShadow:
                    '0 20px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(59, 130, 246, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
            }}
        >
            {/* 狀態標題與狀態說明 */}
            <div
                style={{
                    fontSize: '16px',
                    fontWeight: '700',
                    color: 'white',
                    marginBottom: '12px',
                    borderLeft: `6px solid ${
                        statusInfo.status === 'stable'
                            ? '#22c55e' // 綠色=連接正常
                            : statusInfo.status === 'preparing'
                            ? '#f59e0b' // 橙色=準備換手
                            : statusInfo.status === 'establishing'
                            ? '#3b82f6' // 藍色=建立新連接
                            : statusInfo.status === 'switching'
                            ? '#8b5cf6' // 紫色=正在切換
                            : statusInfo.status === 'completing'
                            ? '#22c55e' // 綠色=換手完成
                            : '#6b7280' // 灰色=搜尋中
                    }`,
                    paddingLeft: '16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                }}
            >
                <span>{statusInfo.title}</span>
                <span
                    style={{
                        fontSize: '12px',
                        opacity: 0.9,
                        fontWeight: '500',
                    }}
                >
                    {statusInfo.status === 'stable'
                        ? '連接正常'
                        : statusInfo.status === 'preparing'
                        ? '準備換手'
                        : statusInfo.status === 'establishing'
                        ? '建立連接'
                        : statusInfo.status === 'switching'
                        ? '正在切換'
                        : statusInfo.status === 'completing'
                        ? '換手完成'
                        : '搜尋中'}
                </span>
            </div>

            {/* 衛星名稱 */}
            <div
                style={{
                    fontSize: '15px',
                    color: '#e5e7eb',
                    marginBottom:
                        statusInfo.progress !== undefined ||
                        statusInfo.countdown
                            ? '12px'
                            : '0',
                }}
            >
                {statusInfo.subtitle}
            </div>

            {/* 進度顯示 */}
            {statusInfo.progress !== undefined && (
                <div style={{ marginBottom: '8px' }}>
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '4px',
                        }}
                    >
                        <span style={{ fontSize: '14px', color: '#cbd5e1' }}>
                            {statusInfo.status === 'establishing'
                                ? '建立進度'
                                : statusInfo.status === 'switching'
                                ? '切換進度'
                                : statusInfo.status === 'completing'
                                ? '完成進度'
                                : '執行進度'}
                        </span>
                        <span
                            style={{
                                fontSize: '14px',
                                color: 'white',
                                fontWeight: '700',
                            }}
                        >
                            {statusInfo.progress}%
                        </span>
                    </div>
                    <div
                        style={{
                            width: '100%',
                            height: '4px',
                            background: 'rgba(255, 255, 255, 0.1)',
                            borderRadius: '2px',
                        }}
                    >
                        <div
                            style={{
                                width: `${statusInfo.progress}%`,
                                height: '100%',
                                background:
                                    statusInfo.status === 'establishing'
                                        ? '#3b82f6' // 藍色=建立中
                                        : statusInfo.status === 'switching'
                                        ? '#8b5cf6' // 紫色=切換中
                                        : statusInfo.status === 'completing'
                                        ? '#22c55e' // 綠色=完成中
                                        : '#6b7280',
                                borderRadius: '2px',
                                transition: 'width 0.3s ease',
                            }}
                        />
                    </div>
                </div>
            )}

            {/* 倒數時間 */}
            {statusInfo.countdown && (
                <div
                    style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginTop: '4px',
                    }}
                >
                    <span style={{ fontSize: '14px', color: '#cbd5e1' }}>
                        換手倒數
                    </span>
                    <span
                        style={{
                            fontSize: '16px',
                            fontWeight: '700',
                            color: '#f59e0b', // 橙色=準備中
                        }}
                    >
                        {statusInfo.countdown} 秒
                    </span>
                </div>
            )}
        </div>
    )
}

// 🔄 換手階段定義
type HandoverPhase =
    | 'stable'
    | 'preparing'
    | 'establishing'
    | 'switching'
    | 'completing'

interface HandoverState {
    phase: HandoverPhase
    currentSatelliteId: string | null
    targetSatelliteId: string | null
    progress: number // 0-1
    phaseStartTime: number
    totalElapsed: number
}

const HandoverAnimation3D: React.FC<HandoverAnimation3DProps> = ({
    devices,
    enabled,
    satellitePositions,
    stableDuration = 5, // 預設5秒穩定期
    onStatusUpdate,
    onHandoverStateUpdate,
}) => {
    // 🔗 換手狀態管理
    const [handoverState, setHandoverState] = useState<HandoverState>({
        phase: 'stable',
        currentSatelliteId: null,
        targetSatelliteId: null,
        progress: 0,
        phaseStartTime: Date.now(),
        totalElapsed: 0,
    })

    // 🔧 位置平滑處理
    const smoothedPositionsRef = useRef<Map<string, [number, number, number]>>(
        new Map()
    )
    const geometryUpdateIntervalRef = useRef<number>(0)

    // 🔗 獲取UAV位置
    const getUAVPositions = (): Array<[number, number, number]> => {
        return devices
            .filter((d) => d.role === 'receiver')
            .map((uav) => [
                uav.position_x || 0,
                uav.position_z || 0,
                uav.position_y || 0,
            ])
    }

    // 🔗 獲取可用衛星列表
    const getAvailableSatellites = (): string[] => {
        if (!satellitePositions) return []
        return Array.from(satellitePositions.keys())
    }

    // 🔗 隨機選擇衛星（排除當前衛星）
    const selectRandomSatellite = (excludeId?: string): string | null => {
        const availableSatellites = getAvailableSatellites()
        if (availableSatellites.length === 0) return null

        const candidates = availableSatellites.filter((id) => id !== excludeId)
        if (candidates.length === 0) return availableSatellites[0]

        const randomIndex = Math.floor(Math.random() * candidates.length)
        return candidates[randomIndex]
    }

    // 🏷️ 獲取衛星名稱（基於ID匹配DynamicSatelliteRenderer的命名規則）
    const getSatelliteName = (satelliteId: string | null): string => {
        if (!satelliteId) return '未知衛星'

        // 從 sat_0 格式轉換為 STARLINK-1000 格式
        const match = satelliteId.match(/sat_(\d+)/)
        if (match) {
            const index = parseInt(match[1])
            return `STARLINK-${1000 + index}`
        }

        // 如果已經是 STARLINK 格式，直接返回
        if (satelliteId.includes('STARLINK')) {
            return satelliteId
        }

        // 如果是純數字，添加 STARLINK 前綴
        if (/^\d+$/.test(satelliteId)) {
            return `STARLINK-${satelliteId}`
        }

        // 其他情況，嘗試保留原始ID但添加說明
        return `衛星-${satelliteId}`
    }

    // 🔧 位置平滑插值
    const lerpPosition = (
        current: [number, number, number],
        target: [number, number, number],
        factor: number
    ): [number, number, number] => {
        return [
            current[0] + (target[0] - current[0]) * factor,
            current[1] + (target[1] - current[1]) * factor,
            current[2] + (target[2] - current[2]) * factor,
        ]
    }

    // ⏰ 階段時間配置（穩定期可調整，其他階段固定）
    const PHASE_DURATIONS = {
        stable: stableDuration * 1000, // 可調整穩定期（毫秒）
        preparing: 5000, // 準備期（倒數5秒）
        establishing: 3000, // 建立期（3秒）
        switching: 2000, // 切換期（2秒）
        completing: 5000, // 完成期（5秒）
    }

    // 🔄 換手邏輯核心
    useFrame((state, delta) => {
        if (!enabled) return

        const now = Date.now()
        const phaseElapsed = now - handoverState.phaseStartTime
        const availableSatellites = getAvailableSatellites()

        // 移除位置平滑處理，直接使用實際衛星位置確保一致性

        // 🚨 緊急換手：當前衛星消失
        if (
            handoverState.currentSatelliteId &&
            !availableSatellites.includes(handoverState.currentSatelliteId)
        ) {
            const newSatellite = selectRandomSatellite(
                handoverState.currentSatelliteId
            )
            if (newSatellite) {
                setHandoverState({
                    phase: 'stable',
                    currentSatelliteId: newSatellite,
                    targetSatelliteId: null,
                    progress: 0,
                    phaseStartTime: now,
                    totalElapsed: 0,
                })
                return
            }
        }

        // 📊 更新當前階段進度
        const currentPhaseDuration = PHASE_DURATIONS[handoverState.phase]
        const progress = Math.min(phaseElapsed / currentPhaseDuration, 1.0)

        // 🔄 階段轉換邏輯
        let newState = { ...handoverState, progress }

        if (progress >= 1.0) {
            switch (handoverState.phase) {
                case 'stable':
                    // 進入準備期，選擇目標衛星
                    const targetSatellite = selectRandomSatellite(
                        handoverState.currentSatelliteId
                    )
                    if (targetSatellite) {
                        newState = {
                            phase: 'preparing',
                            currentSatelliteId:
                                handoverState.currentSatelliteId,
                            targetSatelliteId: targetSatellite,
                            progress: 0,
                            phaseStartTime: now,
                            totalElapsed:
                                handoverState.totalElapsed + phaseElapsed,
                        }
                    }
                    break

                case 'preparing':
                    newState = {
                        ...handoverState,
                        phase: 'establishing',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed,
                    }
                    break

                case 'establishing':
                    newState = {
                        ...handoverState,
                        phase: 'switching',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed,
                    }
                    break

                case 'switching':
                    newState = {
                        ...handoverState,
                        phase: 'completing',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed,
                    }
                    break

                case 'completing':
                    newState = {
                        phase: 'stable',
                        currentSatelliteId: handoverState.targetSatelliteId,
                        targetSatelliteId: null,
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: 0, // 重置週期
                    }
                    break
            }
            setHandoverState(newState)
        } else {
            // 只在進度有顯著變化時更新 (避免無限渲染)
            const progressDiff = Math.abs(
                newState.progress - handoverState.progress
            )
            if (progressDiff >= 0.01) {
                // 只有進度變化 >= 1% 才更新
                setHandoverState(newState)
            }
        }
    })

    // 🎯 初始化第一個連接
    useEffect(() => {
        if (!handoverState.currentSatelliteId && enabled) {
            const firstSatellite = selectRandomSatellite()
            if (firstSatellite) {
                setHandoverState((prev) => ({
                    ...prev,
                    currentSatelliteId: firstSatellite,
                    phaseStartTime: Date.now(),
                }))
            }
        }
    }, [enabled, satellitePositions])

    // 🔗 渲染連接線（支援雙線和動畫效果）
    const renderConnections = () => {
        if (!enabled) return null

        const uavPositions = getUAVPositions()
        const connections = []

        // 🟢 當前/舊連接線（在 completing 階段顯示舊連接）
        if (handoverState.currentSatelliteId) {
            // 直接使用實際衛星位置，不使用平滑插值，確保連接線端點與衛星位置一致
            const satellitePos = satellitePositions?.get(handoverState.currentSatelliteId)

            if (satellitePos) {
                const currentLineProps = getCurrentLineProperties()

                uavPositions.forEach((uavPos, index) => {
                    const curve = new THREE.CatmullRomCurve3([
                        new THREE.Vector3(...satellitePos),
                        new THREE.Vector3(...uavPos),
                    ])

                    connections.push(
                        <mesh
                            key={`current-${handoverState.currentSatelliteId}-${index}`}
                        >
                            <tubeGeometry
                                args={[
                                    curve,
                                    20,
                                    currentLineProps.radius,
                                    8,
                                    false,
                                ]}
                            />
                            <meshBasicMaterial
                                color={currentLineProps.color}
                                transparent
                                opacity={currentLineProps.opacity}
                            />
                        </mesh>
                    )
                })
            }
        }

        // 🔵 目標連接線（在 establishing, switching, completing 階段顯示）
        if (
            handoverState.targetSatelliteId &&
            (handoverState.phase === 'establishing' ||
                handoverState.phase === 'switching' ||
                handoverState.phase === 'completing')
        ) {
            // 直接使用實際衛星位置，確保連接線端點與衛星位置一致
            const satellitePos = satellitePositions?.get(handoverState.targetSatelliteId)

            if (satellitePos) {
                const targetLineProps = getTargetLineProperties()

                uavPositions.forEach((uavPos, index) => {
                    const curve = new THREE.CatmullRomCurve3([
                        new THREE.Vector3(...satellitePos),
                        new THREE.Vector3(...uavPos),
                    ])

                    connections.push(
                        <mesh
                            key={`target-${handoverState.targetSatelliteId}-${index}`}
                        >
                            <tubeGeometry
                                args={[
                                    curve,
                                    20,
                                    targetLineProps.radius,
                                    8,
                                    false,
                                ]}
                            />
                            <meshBasicMaterial
                                color={targetLineProps.color}
                                transparent
                                opacity={targetLineProps.opacity}
                            />
                        </mesh>
                    )
                })
            }
        }

        return connections
    }

    // 🎨 當前連接線屬性
    const getCurrentLineProperties = () => {
        switch (handoverState.phase) {
            case 'stable':
                return { color: '#00ff00', opacity: 0.9, radius: 0.6 } // 綠色實線，更亮更粗
            case 'preparing':
                // 閃爍效果，更明顯
                const flicker = Math.sin(Date.now() * 0.012) * 0.4 + 0.8
                return { color: '#ffaa00', opacity: flicker, radius: 0.5 } // 橙黃色閃爍，更亮
            case 'establishing':
                return { color: '#ffdd00', opacity: 0.8, radius: 0.4 } // 亮黃色，不再太淡
            case 'switching':
                return { color: '#aaaaaa', opacity: 0.6, radius: 0.4 } // 淺灰色，增加透明度
            case 'completing':
                // 在完成期逐漸淡出舊連接
                const fadeOutOpacity = Math.max(
                    0.2,
                    0.6 - handoverState.progress * 0.4
                )
                return {
                    color: '#aaaaaa',
                    opacity: fadeOutOpacity,
                    radius: 0.3,
                } // 淺灰色逐漸淡出但保持更可見
            default:
                return { color: '#00ff00', opacity: 0.9, radius: 0.6 }
        }
    }

    // 🎨 目標連接線屬性
    const getTargetLineProperties = () => {
        switch (handoverState.phase) {
            case 'establishing':
                // 逐漸變實，起始透明度更高
                const establishOpacity = 0.4 + handoverState.progress * 0.5
                return {
                    color: '#0088ff',
                    opacity: establishOpacity,
                    radius: 0.4,
                } // 亮藍色漸現，更粗
            case 'switching':
                return { color: '#00ff00', opacity: 0.9, radius: 0.6 } // 綠色實線，更亮更粗
            case 'completing':
                // 在完成期成為主要連接，保持穩定綠色
                return { color: '#00ff00', opacity: 0.9, radius: 0.6 } // 綠色實線穩定，更亮更粗
            default:
                return { color: '#0088ff', opacity: 0.5, radius: 0.4 }
        }
    }

    // 🌟 目標衛星光圈
    const renderTargetSatelliteRing = () => {
        if (
            !handoverState.targetSatelliteId ||
            handoverState.phase === 'stable'
        )
            return null

        const satellitePos = satellitePositions?.get(handoverState.targetSatelliteId)

        if (!satellitePos) return null

        const pulseScale = 1 + Math.sin(Date.now() * 0.008) * 0.3 // 脈衝效果

        return (
            <group position={satellitePos}>
                <Ring
                    args={[8 * pulseScale, 12 * pulseScale, 32]}
                    rotation={[Math.PI / 2, 0, 0]}
                >
                    <meshBasicMaterial
                        color="#0080ff"
                        transparent
                        opacity={0.3}
                        side={THREE.DoubleSide}
                    />
                </Ring>
            </group>
        )
    }

    // 📱 狀態資訊
    const getStatusInfo = () => {
        const countdown =
            handoverState.phase === 'preparing'
                ? Math.ceil(
                      (PHASE_DURATIONS.preparing -
                          (Date.now() - handoverState.phaseStartTime)) /
                          1000
                  )
                : 0

        const currentSatName = getSatelliteName(
            handoverState.currentSatelliteId
        )
        const targetSatName = getSatelliteName(handoverState.targetSatelliteId)
        const progress = Math.round(handoverState.progress * 100)

        switch (handoverState.phase) {
            case 'stable':
                return {
                    title: '正常連接',
                    subtitle: `連接衛星: ${currentSatName}`,
                    status: 'stable' as const,
                    progress: undefined,
                }
            case 'preparing':
                return {
                    title: '準備換手',
                    subtitle: `即將連接: ${targetSatName}`,
                    status: 'preparing' as const,
                    countdown: countdown,
                }
            case 'establishing':
                return {
                    title: '建立連接',
                    subtitle: `連接中: ${targetSatName}`,
                    status: 'establishing' as const,
                    progress: progress,
                }
            case 'switching':
                return {
                    title: '切換連接',
                    subtitle: `切換至: ${targetSatName}`,
                    status: 'switching' as const,
                    progress: progress,
                }
            case 'completing':
                return {
                    title: '換手完成',
                    subtitle: `已連接: ${targetSatName}`,
                    status: 'completing' as const,
                    progress: progress,
                }
            default:
                return {
                    title: '搜尋衛星',
                    subtitle: '正在搜尋可用衛星...',
                    status: 'waiting' as const,
                    progress: undefined,
                }
        }
    }

    // 🔄 狀態更新回調
    useEffect(() => {
        if (onStatusUpdate && enabled) {
            const statusInfo = getStatusInfo()
            onStatusUpdate(statusInfo)
        }
        
        // 🔗 換手狀態回調，供衛星光球使用
        if (onHandoverStateUpdate && enabled) {
            onHandoverStateUpdate(handoverState)
        }
    }, [handoverState, enabled, onStatusUpdate, onHandoverStateUpdate])

    if (!enabled) return null

    return (
        <group>
            {renderConnections()}
            {renderTargetSatelliteRing()}
        </group>
    )
}

export default HandoverAnimation3D
export { HandoverStatusPanel }
