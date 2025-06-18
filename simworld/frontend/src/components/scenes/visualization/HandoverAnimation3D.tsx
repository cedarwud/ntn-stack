import React, { useState, useEffect, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Ring, Text } from '@react-three/drei'

interface HandoverAnimation3DProps {
    devices: any[]
    enabled: boolean
    satellitePositions?: Map<string, [number, number, number]>
    stableDuration?: number // 穩定期時間（秒）
    handoverMode?: 'demo' | 'real' // 換手模式：演示模式 vs 真實模式
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
                            ? '#8b5cf6' // 紫色=正在換手
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
                        ? '正在換手'
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
                                ? '換手進度'
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
                                        ? '#8b5cf6' // 紫色=換手中
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

            {/* 🎯 換手原因資訊 */}
            {statusInfo.handoverReason && (
                <div
                    style={{
                        marginTop: '16px',
                        padding: '12px',
                        background: 'rgba(255, 255, 255, 0.04)',
                        borderRadius: '8px',
                        border: `1px solid ${
                            statusInfo.handoverReason.urgency === 'emergency'
                                ? '#ef4444'
                                : statusInfo.handoverReason.urgency === 'high'
                                ? '#f59e0b'
                                : statusInfo.handoverReason.urgency === 'medium'
                                ? '#3b82f6'
                                : '#22c55e'
                        }`,
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            marginBottom: '8px',
                        }}
                    >
                        <span style={{ fontSize: '16px' }}>
                            {statusInfo.handoverReason.icon}
                        </span>
                        <span
                            style={{
                                fontSize: '14px',
                                fontWeight: '600',
                                color: '#e5e7eb',
                            }}
                        >
                            換手原因: {statusInfo.handoverReason.reasonText}
                        </span>
                    </div>

                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            marginBottom: '4px',
                        }}
                    >
                        <span style={{ fontSize: '12px', color: '#cbd5e1' }}>
                            當前值
                        </span>
                        <span style={{ fontSize: '12px', color: '#cbd5e1' }}>
                            目標值
                        </span>
                    </div>

                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '8px',
                        }}
                    >
                        <span
                            style={{
                                fontSize: '14px',
                                fontWeight: '600',
                                color:
                                    statusInfo.handoverReason.urgency ===
                                    'emergency'
                                        ? '#ef4444'
                                        : '#fbbf24',
                            }}
                        >
                            {statusInfo.handoverReason.currentValue.toFixed(1)}
                            {statusInfo.handoverReason.unit}
                        </span>
                        <span style={{ fontSize: '12px', color: '#6b7280' }}>
                            →
                        </span>
                        <span
                            style={{
                                fontSize: '14px',
                                fontWeight: '600',
                                color: '#22c55e',
                            }}
                        >
                            {statusInfo.handoverReason.targetValue.toFixed(1)}
                            {statusInfo.handoverReason.unit}
                        </span>
                    </div>

                    <div
                        style={{
                            fontSize: '12px',
                            color: '#22c55e',
                            fontWeight: '500',
                        }}
                    >
                        ✨ {statusInfo.handoverReason.improvement}
                    </div>
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
    handoverMode = 'demo', // 預設演示模式
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

    // 🔄 換手歷史記錄 - 防止頻繁互換
    const handoverHistoryRef = useRef<{
        recentHandovers: Array<{
            from: string
            to: string
            timestamp: number
        }>
        cooldownPeriod: number // 冷卻期（毫秒）
    }>({
        recentHandovers: [],
        cooldownPeriod: handoverMode === 'demo' ? 60000 : 30000, // 演示模式60秒，真實模式30秒
    })

    // 🔄 當換手模式改變時，更新冷卻期
    useEffect(() => {
        handoverHistoryRef.current.cooldownPeriod =
            handoverMode === 'demo' ? 60000 : 30000
        console.log(
            `🔄 HandoverAnimation3D: 換手模式變更為: ${handoverMode}，冷卻期: ${
                handoverHistoryRef.current.cooldownPeriod / 1000
            }秒`
        )
    }, [handoverMode])

    // 🎲 換手原因計數器
    const handoverReasonCounterRef = useRef<number>(0)

    // 🎯 模擬數據緩存
    const simulatedDataRef = useRef<{
        load: { currentLoad: number; targetLoad: number } | null
        elevation: { currentElevation: number; targetElevation: number } | null
        signal: { currentSignal: number; targetSignal: number } | null
    }>({
        load: null,
        elevation: null,
        signal: null,
    })

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

    // 📏 計算兩點之間的3D距離
    const calculateDistance = (
        pos1: [number, number, number],
        pos2: [number, number, number]
    ): number => {
        const dx = pos1[0] - pos2[0]
        const dy = pos1[1] - pos2[1]
        const dz = pos1[2] - pos2[2]
        return Math.sqrt(dx * dx + dy * dy + dz * dz)
    }

    // 🎯 智能選擇最近的衛星（排除當前衛星，並考慮換手歷史）
    const selectNearestSatellite = (excludeId?: string): string | null => {
        const availableSatellites = getAvailableSatellites()
        if (availableSatellites.length === 0) return null

        let candidates = availableSatellites.filter((id) => id !== excludeId)
        if (candidates.length === 0) return null

        // 🚫 清理過期的換手記錄
        const now = Date.now()
        const history = handoverHistoryRef.current
        history.recentHandovers = history.recentHandovers.filter(
            (record) => now - record.timestamp < history.cooldownPeriod
        )

        // 🔄 如果有當前衛星，檢查換手歷史
        if (excludeId) {
            // 找出最近與當前衛星有換手記錄的衛星
            const recentPartners = new Set<string>()

            history.recentHandovers.forEach((record) => {
                // 檢查雙向換手記錄
                if (record.from === excludeId) {
                    recentPartners.add(record.to)
                } else if (record.to === excludeId) {
                    recentPartners.add(record.from)
                }
            })

            // 🎯 優先選擇沒有最近換手記錄的衛星
            const preferredCandidates = candidates.filter(
                (id) => !recentPartners.has(id)
            )

            if (preferredCandidates.length > 0) {
                candidates = preferredCandidates
                console.log(
                    `🔄 避免頻繁互換，排除最近換手的衛星: ${Array.from(
                        recentPartners
                    )
                        .map((id) => getSatelliteName(id))
                        .join(', ')}`
                )
            } else {
                console.log(`⚠️ 所有候選衛星都有最近換手記錄，使用全部候選者`)
            }
        }

        const uavPositions = getUAVPositions()
        if (uavPositions.length === 0) return candidates[0]

        // 使用第一個UAV的位置來計算距離
        const uavPos = uavPositions[0]
        let nearestSatellite = candidates[0]
        let minDistance = Infinity

        console.log('🔍 計算衛星距離:')
        candidates.forEach((satId) => {
            const satPos = satellitePositions?.get(satId)
            if (satPos) {
                const distance = calculateDistance(uavPos, satPos)
                console.log(
                    `  ${getSatelliteName(satId)}: ${distance.toFixed(1)}km`
                )

                if (distance < minDistance) {
                    minDistance = distance
                    nearestSatellite = satId
                }
            }
        })

        console.log(
            `✅ 選擇最近衛星: ${getSatelliteName(
                nearestSatellite
            )} (距離: ${minDistance.toFixed(1)}km)`
        )
        return nearestSatellite
    }

    // 📝 記錄換手事件
    const recordHandover = (fromSatellite: string, toSatellite: string) => {
        const now = Date.now()
        handoverHistoryRef.current.recentHandovers.push({
            from: fromSatellite,
            to: toSatellite,
            timestamp: now,
        })

        // 清理過期記錄（超過冷卻期的記錄）
        handoverHistoryRef.current.recentHandovers =
            handoverHistoryRef.current.recentHandovers.filter(
                (record) =>
                    now - record.timestamp <
                    handoverHistoryRef.current.cooldownPeriod
            )

        console.log(
            `📝 記錄換手: ${getSatelliteName(
                fromSatellite
            )} → ${getSatelliteName(toSatellite)}，` +
                `歷史記錄數量: ${handoverHistoryRef.current.recentHandovers.length}，` +
                `模式: ${handoverMode}，冷卻期: ${
                    handoverHistoryRef.current.cooldownPeriod / 1000
                }秒`
        )
    }

    // 🔗 獲取當前連接距離（用於顯示）
    const getCurrentConnectionDistance = (): number | null => {
        if (!handoverState.currentSatelliteId) return null

        const uavPositions = getUAVPositions()
        if (uavPositions.length === 0) return null

        const satPos = satellitePositions?.get(handoverState.currentSatelliteId)
        if (!satPos) return null

        return calculateDistance(uavPositions[0], satPos)
    }

    // 🏷️ 獲取衛星名稱（基於ID匹配DynamicSatelliteRenderer的命名規則）
    const getSatelliteName = (
        satelliteId: string | null | undefined
    ): string => {
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

    // ⏰ 階段時間配置 - 根據模式調整
    const PHASE_DURATIONS =
        handoverMode === 'demo'
            ? {
                  // 演示模式：20秒完美週期，適合展示
                  stable: stableDuration * 1000, // 可調整穩定期（毫秒）
                  preparing: 5000, // 準備期（倒數5秒）
                  establishing: 3000, // 建立期（3秒）
                  switching: 2000, // 換手期（2秒）
                  completing: 5000, // 完成期（5秒）
              }
            : {
                  // 真實模式：快速換手，符合5G標準
                  stable: stableDuration * 1000, // 可調整穩定期（更長，30秒-5分鐘）
                  preparing: 500, // 準備期（0.5秒）
                  establishing: 300, // 建立期（0.3秒）
                  switching: 200, // 換手期（0.2秒）
                  completing: 1000, // 完成期（1秒）
              }

    // 🔄 換手邏輯核心
    useFrame((state, delta) => {
        if (!enabled) return

        const now = Date.now()
        const phaseElapsed = now - handoverState.phaseStartTime
        const availableSatellites = getAvailableSatellites()

        // 🔧 輕量級位置平滑處理 - 減少連接線跳動但保持與衛星位置基本一致
        geometryUpdateIntervalRef.current += delta * 1000
        if (geometryUpdateIntervalRef.current >= 50 && satellitePositions) {
            geometryUpdateIntervalRef.current = 0
            const smoothingFactor = 0.25 // 較高的平滑係數，減少延遲

            for (const [satId, targetPos] of satellitePositions.entries()) {
                const currentSmoothed = smoothedPositionsRef.current.get(satId)
                if (!currentSmoothed) {
                    // 新出現的衛星直接設置為目標位置
                    smoothedPositionsRef.current.set(satId, targetPos)
                } else {
                    // 現有衛星進行輕量平滑
                    const smoothedPos = lerpPosition(
                        currentSmoothed,
                        targetPos,
                        smoothingFactor
                    )
                    smoothedPositionsRef.current.set(satId, smoothedPos)
                }
            }

            // 清理消失的衛星
            for (const satId of smoothedPositionsRef.current.keys()) {
                if (!satellitePositions.has(satId)) {
                    smoothedPositionsRef.current.delete(satId)
                }
            }
        }

        // 🚨 緊急換手：當前衛星消失
        if (
            handoverState.currentSatelliteId &&
            !availableSatellites.includes(handoverState.currentSatelliteId)
        ) {
            const newSatellite = selectNearestSatellite(
                handoverState.currentSatelliteId
            )
            if (newSatellite) {
                console.log('🚨 緊急換手：當前衛星消失，切換到最近衛星')
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
                    // 進入準備期，選擇最近的目標衛星
                    const targetSatellite = selectNearestSatellite(
                        handoverState.currentSatelliteId || undefined
                    )
                    if (targetSatellite) {
                        console.log('🔄 開始換手：選擇最近衛星作為目標')

                        // 🎲 遞增換手原因計數器，下次換手使用不同原因
                        handoverReasonCounterRef.current += 1

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
                    } else {
                        // 沒有其他衛星可用，保持當前狀態
                        console.log('🔄 沒有其他衛星可用，保持當前連接')
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
                    // 計算換手前後的距離變化
                    const oldDistance = getCurrentConnectionDistance()
                    const newSatellite = handoverState.targetSatelliteId

                    if (newSatellite && oldDistance) {
                        const uavPos = getUAVPositions()[0]
                        const newSatPos = satellitePositions?.get(newSatellite)
                        if (uavPos && newSatPos) {
                            const newDistance = calculateDistance(
                                uavPos,
                                newSatPos
                            )
                            const improvement = oldDistance - newDistance
                            console.log(
                                `🎯 換手完成: ${getSatelliteName(
                                    handoverState.currentSatelliteId
                                )} -> ${getSatelliteName(newSatellite)}`
                            )
                            console.log(
                                `📏 距離變化: ${oldDistance.toFixed(
                                    1
                                )}km -> ${newDistance.toFixed(1)}km (${
                                    improvement > 0 ? '改善' : '增加'
                                } ${Math.abs(improvement).toFixed(1)}km)`
                            )
                        }
                    }

                    // 📝 記錄換手事件到歷史記錄
                    if (
                        handoverState.currentSatelliteId &&
                        handoverState.targetSatelliteId
                    ) {
                        recordHandover(
                            handoverState.currentSatelliteId,
                            handoverState.targetSatelliteId
                        )
                    }

                    // 清除所有模擬數據，下次換手重新生成
                    simulatedDataRef.current = {
                        load: null,
                        elevation: null,
                        signal: null,
                    }

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

    // 🎯 初始化第一個連接 - 選擇最近的衛星
    useEffect(() => {
        if (!handoverState.currentSatelliteId && enabled) {
            const firstSatellite = selectNearestSatellite()
            if (firstSatellite) {
                console.log('🚀 初始化連接：選擇最近衛星')
                setHandoverState((prev) => ({
                    ...prev,
                    currentSatelliteId: firstSatellite,
                    phaseStartTime: Date.now(),
                }))
            }
        }
    }, [enabled, satellitePositions])

    // 🔄 動態更新換手歷史冷卻期
    useEffect(() => {
        handoverHistoryRef.current.cooldownPeriod =
            handoverMode === 'demo' ? 60000 : 30000
        console.log(
            `🔄 更新換手冷卻期: ${
                handoverMode === 'demo' ? '60秒 (演示模式)' : '30秒 (真實模式)'
            }`
        )
    }, [handoverMode])

    // 🔗 渲染連接線（支援雙線和動畫效果）
    const renderConnections = () => {
        if (!enabled) return null

        const uavPositions = getUAVPositions()
        const connections: React.ReactElement[] = []

        // 🟢 當前/舊連接線（在 completing 階段顯示舊連接）
        if (handoverState.currentSatelliteId) {
            // 優先使用平滑位置以實現平滑移動，回退到實際位置
            const smoothedPos = smoothedPositionsRef.current.get(
                handoverState.currentSatelliteId
            )
            const satellitePos =
                smoothedPos ||
                satellitePositions?.get(handoverState.currentSatelliteId)

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
            // 優先使用平滑位置以實現平滑移動，回退到實際位置
            const smoothedPos = smoothedPositionsRef.current.get(
                handoverState.targetSatelliteId
            )
            const satellitePos =
                smoothedPos ||
                satellitePositions?.get(handoverState.targetSatelliteId)

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

        // 優先使用平滑位置以實現平滑移動，回退到實際位置
        const smoothedPos = smoothedPositionsRef.current.get(
            handoverState.targetSatelliteId
        )
        const satellitePos =
            smoothedPos ||
            satellitePositions?.get(handoverState.targetSatelliteId)

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

    // 🎯 獲取換手原因分析
    const getHandoverReason = () => {
        if (!handoverState.targetSatelliteId) return null

        const uavPos = getUAVPositions()[0]
        if (!uavPos) return null

        const currentSatPos = handoverState.currentSatelliteId
            ? satellitePositions?.get(handoverState.currentSatelliteId)
            : null
        const targetSatPos = satellitePositions?.get(
            handoverState.targetSatelliteId
        )

        if (!currentSatPos || !targetSatPos) return null

        const currentDistance = calculateDistance(uavPos, currentSatPos)
        const targetDistance = calculateDistance(uavPos, targetSatPos)

        // 計算仰角 (簡化計算)
        const currentElevation =
            (Math.atan2(
                currentSatPos[1] - uavPos[1],
                Math.sqrt(
                    Math.pow(currentSatPos[0] - uavPos[0], 2) +
                        Math.pow(currentSatPos[2] - uavPos[2], 2)
                )
            ) *
                180) /
            Math.PI

        const targetElevation =
            (Math.atan2(
                targetSatPos[1] - uavPos[1],
                Math.sqrt(
                    Math.pow(targetSatPos[0] - uavPos[0], 2) +
                        Math.pow(targetSatPos[2] - uavPos[2], 2)
                )
            ) *
                180) /
            Math.PI

        // 模擬信號強度 (基於距離的簡化模型)
        const currentSignal = Math.max(
            -130,
            -50 - 20 * Math.log10(currentDistance / 100)
        )
        const targetSignal = Math.max(
            -130,
            -50 - 20 * Math.log10(targetDistance / 100)
        )

        // 🎲 輪換換手原因，讓4種狀態都有機會發生
        const reasonType = handoverReasonCounterRef.current % 4

        switch (reasonType) {
            case 0: // 📐 仰角過低
                // 生成固定的仰角數據，避免跳動
                if (!simulatedDataRef.current.elevation) {
                    simulatedDataRef.current.elevation = {
                        currentElevation: Math.max(
                            5,
                            currentElevation + (Math.random() - 0.7) * 20
                        ),
                        targetElevation: Math.max(
                            15,
                            targetElevation + Math.random() * 15
                        ),
                    }
                }

                const elevationData = simulatedDataRef.current.elevation
                return {
                    primaryReason: 'elevation' as const,
                    reasonText: '衛星仰角過低',
                    currentValue: elevationData.currentElevation,
                    targetValue: elevationData.targetElevation,
                    improvement: `提升 ${(
                        elevationData.targetElevation -
                        elevationData.currentElevation
                    ).toFixed(1)}°`,
                    urgency:
                        elevationData.currentElevation < 10
                            ? ('emergency' as const)
                            : ('high' as const),
                    icon: '📐',
                    unit: '°',
                }

            case 1: // 📶 信號強度不足
                // 生成固定的信號數據，避免跳動
                if (!simulatedDataRef.current.signal) {
                    simulatedDataRef.current.signal = {
                        currentSignal: currentSignal - Math.random() * 15, // 降低信號
                        targetSignal: targetSignal + Math.random() * 10, // 改善信號
                    }
                }

                const signalData = simulatedDataRef.current.signal
                return {
                    primaryReason: 'signal' as const,
                    reasonText: '信號強度不足',
                    currentValue: signalData.currentSignal,
                    targetValue: signalData.targetSignal,
                    improvement: `改善 ${(
                        signalData.targetSignal - signalData.currentSignal
                    ).toFixed(1)}dBm`,
                    urgency:
                        signalData.currentSignal < -120
                            ? ('high' as const)
                            : ('medium' as const),
                    icon: '📶',
                    unit: 'dBm',
                }

            case 2: // 📏 距離優化
                return {
                    primaryReason: 'distance' as const,
                    reasonText: '距離優化',
                    currentValue: currentDistance,
                    targetValue: targetDistance,
                    improvement: `縮短 ${Math.max(
                        0,
                        currentDistance - targetDistance
                    ).toFixed(1)}km`,
                    urgency: 'medium' as const,
                    icon: '📏',
                    unit: 'km',
                }

            case 3: // ⚖️ 負載平衡
            default:
                // 生成固定的負載數據，避免跳動
                if (!simulatedDataRef.current.load) {
                    simulatedDataRef.current.load = {
                        currentLoad: 75 + Math.random() * 20, // 75-95%
                        targetLoad: 30 + Math.random() * 20, // 30-50%
                    }
                }

                const loadData = simulatedDataRef.current.load
                return {
                    primaryReason: 'load' as const,
                    reasonText: '負載平衡',
                    currentValue: loadData.currentLoad,
                    targetValue: loadData.targetLoad,
                    improvement: `降低 ${(
                        loadData.currentLoad - loadData.targetLoad
                    ).toFixed(1)}%`,
                    urgency: 'low' as const,
                    icon: '⚖️',
                    unit: '%',
                }
        }
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
        const currentDistance = getCurrentConnectionDistance()
        const handoverReason = getHandoverReason()

        switch (handoverState.phase) {
            case 'stable':
                return {
                    title: '正常連接',
                    subtitle: `連接衛星: ${currentSatName}`,
                    status: 'stable' as const,
                    progress: undefined,
                }
            case 'preparing':
                // 計算目標衛星距離
                const targetDistance = handoverState.targetSatelliteId
                    ? (() => {
                          const uavPos = getUAVPositions()[0]
                          const satPos = satellitePositions?.get(
                              handoverState.targetSatelliteId
                          )
                          return uavPos && satPos
                              ? calculateDistance(uavPos, satPos)
                              : null
                      })()
                    : null

                return {
                    title: '準備換手',
                    subtitle: `即將連接: ${targetSatName}${
                        targetDistance
                            ? ` (${targetDistance.toFixed(1)}km)`
                            : ''
                    }`,
                    status: 'preparing' as const,
                    countdown: countdown,
                    handoverReason: handoverReason,
                }
            case 'establishing':
                return {
                    title: '建立連接',
                    subtitle: `連接中: ${targetSatName}`,
                    status: 'establishing' as const,
                    progress: progress,
                    handoverReason: handoverReason,
                }
            case 'switching':
                return {
                    title: '換手連接',
                    subtitle: `換手至: ${targetSatName}`,
                    status: 'switching' as const,
                    progress: progress,
                    handoverReason: handoverReason,
                }
            case 'completing':
                return {
                    title: '換手完成',
                    subtitle: `已連接: ${targetSatName}`,
                    status: 'completing' as const,
                    progress: progress,
                    handoverReason: handoverReason,
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
