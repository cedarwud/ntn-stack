import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Ring } from '@react-three/drei'
import {
    realConnectionManager,
    RealConnectionInfo,
    RealHandoverStatus,
    getConnectionLineColor,
    getConnectionLineOpacity,
    getConnectionLineRadius,
} from '../../../../services/realConnectionService'
import { Device } from '../../../../types/device'
import { VisibleSatelliteInfo } from '../../../../types/satellite'

interface HandoverAnimation3DProps {
    satellites: VisibleSatelliteInfo[]
    devices: Device[]
    enabled: boolean
    satellitePositions?: Map<string, [number, number, number]>
    stableDuration?: number // 穩定期時間（秒）
    handoverMode?: 'demo' | 'real' // 換手模式：演示模式 vs 真實模式
    onStatusUpdate?: (statusInfo: {
        currentSatellite?: string
        targetSatellite?: string
        phase?: string
        progress?: number
    }) => void // 狀態更新回調
    onHandoverStateUpdate?: (state: {
        isHandover?: boolean
        progress?: number
        phase?: string
    }) => void // 換手狀態回調，供衛星光球使用
    useRealConnections?: boolean // 是否使用真實連接數據
}

// 🎯 狀態面板組件（在Canvas外部顯示）
interface HandoverStatusPanelProps {
    enabled: boolean
    statusInfo: {
        phase?: string
        progress?: number
        satellite_id?: number
        signal_strength?: number
        message?: string
        status?: string
        title?: string
        subtitle?: string
        countdown?: number
        handoverReason?: {
            urgency: string
            icon: string
            reasonText: string
            currentValue: number
            targetValue: number
            unit: string
            improvement: string
        }
    } | null
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
    useRealConnections = false, // 預設不使用真實連接數據
}) => {
    // 🔗 真實連接狀態管理
    const [realConnectionInfo, setRealConnectionInfo] =
        useState<RealConnectionInfo | null>(null)
    const [realHandoverStatus, setRealHandoverStatus] =
        useState<RealHandoverStatus | null>(null)
    const realConnectionUpdateInterval = useRef<NodeJS.Timeout | null>(null)

    // 更新真實連接數據
    useEffect(() => {
        if (!enabled || !useRealConnections) {
            // 清理定時器
            if (realConnectionUpdateInterval.current) {
                clearInterval(realConnectionUpdateInterval.current)
                realConnectionUpdateInterval.current = null
            }
            setRealConnectionInfo(null)
            setRealHandoverStatus(null)
            return
        }

        const updateRealConnectionData = async () => {
            try {
                // 獲取真實連接狀態
                const connectionStatus =
                    realConnectionManager.getConnectionStatus('ue_001')
                const handoverStatus =
                    realConnectionManager.getHandoverStatus('ue_001')

                if (connectionStatus) {
                    setRealConnectionInfo(connectionStatus)
                }

                if (handoverStatus) {
                    setRealHandoverStatus(handoverStatus)
                }
            } catch (error) {
                console.error('Error updating real connection data:', error)
            }
        }

        // 立即更新一次
        updateRealConnectionData()

        // 每2秒更新一次真實數據
        realConnectionUpdateInterval.current = setInterval(
            updateRealConnectionData,
            2000
        )

        return () => {
            if (realConnectionUpdateInterval.current) {
                clearInterval(realConnectionUpdateInterval.current)
            }
        }
    }, [enabled, useRealConnections])

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
        lastCompletedSatellite: string | null // 最近完成換手的衛星，絕對禁止
        lastCompletedTime: number // 最近完成時間
    }>({
        recentHandovers: [],
        cooldownPeriod: handoverMode === 'demo' ? 90000 : 120000, // 演示模式90秒，真實模式120秒（加強防護）
        lastCompletedSatellite: null,
        lastCompletedTime: 0,
    })

    // 🔄 當換手模式改變時，更新冷卻期（只執行一次）
    useEffect(() => {
        const newCooldown = handoverMode === 'demo' ? 90000 : 120000
        if (handoverHistoryRef.current.cooldownPeriod !== newCooldown) {
            handoverHistoryRef.current.cooldownPeriod = newCooldown
            // 清空所有歷史記錄，避免模式切換時的衝突
            handoverHistoryRef.current.recentHandovers = []
            handoverHistoryRef.current.lastCompletedSatellite = null
            handoverHistoryRef.current.lastCompletedTime = 0
        }
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
    const getUAVPositions = useCallback((): Array<[number, number, number]> => {
        return devices
            .filter((d) => d.role === 'receiver')
            .map((uav) => [
                uav.position_x || 0,
                uav.position_z || 0,
                uav.position_y || 0,
            ])
    }, [devices])

    // 🔗 獲取可用衛星列表 - 修復：支援內建模擬衛星
    const getAvailableSatellites = useCallback((): string[] => {
        // 🔧 修復：如果 satellitePositions 為空（DynamicSatelliteRenderer 未啟用），
        // 使用內建的模擬衛星列表
        if (!satellitePositions || satellitePositions.size === 0) {
            return Array.from({ length: 18 }, (_, i) => `sat_${i}`)
        }

        return Array.from(satellitePositions.keys())
    }, [satellitePositions])

    // 🔗 獲取衛星位置 - 支援內建模擬和外部位置
    const getSatellitePosition = useCallback(
        (satelliteId: string): [number, number, number] => {
            // 優先使用外部位置數據
            if (satellitePositions && satellitePositions.has(satelliteId)) {
                return satellitePositions.get(satelliteId)!
            }

            // 回退到內建模擬位置
            const satIndex = parseInt(satelliteId.replace('sat_', '')) || 0
            const angle = (satIndex * 20 * Math.PI) / 180 // 每20度一顆衛星
            const radius = 600
            const height = 150 + Math.sin(angle * 2) * 100 // 高度變化

            return [radius * Math.cos(angle), height, radius * Math.sin(angle)]
        },
        [satellitePositions]
    )

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

    // 🎯 選擇衛星（智能多樣化選擇 - 擴大換手範圍）
    const selectNearestSatellite = useCallback(
        (excludeId?: string): string | null => {
            const uavPositions = getUAVPositions()
            const availableSatellites = getAvailableSatellites()

            if (uavPositions.length === 0 || availableSatellites.length === 0) {
                return null
            }

            const uavPos = uavPositions[0]

            // 🚫 第一層防護：排除當前衛星
            let candidates = availableSatellites.filter(
                (satId) => satId !== excludeId
            )

            // 🚫 第二層防護：排除冷卻期內的衛星（加強互換防護）
            const now = Date.now()
            const history = handoverHistoryRef.current

            // 清理過期記錄
            history.recentHandovers = history.recentHandovers.filter(
                (record) => now - record.timestamp < history.cooldownPeriod
            )

            candidates = candidates.filter((satId) => {
                // 檢查是否與當前衛星有任何換手記錄（雙向檢查）
                const hasRecentHandover = history.recentHandovers.some(
                    (record) =>
                        (record.from === excludeId && record.to === satId) ||
                        (record.from === satId && record.to === excludeId)
                )
                return !hasRecentHandover
            })

            // 🚫 第三層防護：排除最近完成換手的衛星（縮短禁止時間，增加多樣性）
            if (history.lastCompletedSatellite && history.lastCompletedTime) {
                const timeSinceLastCompleted = now - history.lastCompletedTime
                // 縮短禁止時間到冷卻期的0.8倍，增加可選衛星
                if (timeSinceLastCompleted < history.cooldownPeriod * 0.8) {
                    candidates = candidates.filter(
                        (satId) => satId !== history.lastCompletedSatellite
                    )
                }
            }

            // 🚫 第四層防護：如果候選太少，降低要求
            if (candidates.length < 1) {
                return null // 至少需要1個候選
            }

            // 📊 計算所有候選衛星的距離和選擇權重
            const candidateInfo = candidates
                .map((satId) => {
                    const satPos = getSatellitePosition(satId)
                    if (!satPos) return null

                    const distance = calculateDistance(uavPos, satPos)
                    return { satId, distance, satPos }
                })
                .filter((info) => info !== null)

            if (candidateInfo.length === 0) return null

            // 🎯 智能選擇策略：多樣化選擇，避免總是選同樣的衛星
            let selectedSatellite: string | null = null

            // 按距離排序
            candidateInfo.sort((a, b) => a.distance - b.distance)

            // 🎲 多樣化選擇策略
            const strategy = Math.random()

            if (strategy < 0.4) {
                // 40%機率選擇最近的衛星
                selectedSatellite = candidateInfo[0].satId
            } else if (strategy < 0.7) {
                // 30%機率從前50%的衛星中隨機選擇
                const topHalf = candidateInfo.slice(
                    0,
                    Math.max(1, Math.ceil(candidateInfo.length / 2))
                )
                const randomIndex = Math.floor(Math.random() * topHalf.length)
                selectedSatellite = topHalf[randomIndex].satId
            } else if (strategy < 0.9) {
                // 20%機率從所有候選中隨機選擇（增加多樣性）
                const randomIndex = Math.floor(
                    Math.random() * candidateInfo.length
                )
                selectedSatellite = candidateInfo[randomIndex].satId
            } else {
                // 10%機率選擇最遠的衛星（最大多樣性）
                selectedSatellite =
                    candidateInfo[candidateInfo.length - 1].satId
            }

            // 🚫 第五層防護：最終安全檢查
            if (selectedSatellite === excludeId) {
                // 如果意外選到自己，選擇其他候選
                const alternatives = candidateInfo.filter(
                    (info) => info.satId !== excludeId
                )
                selectedSatellite =
                    alternatives.length > 0 ? alternatives[0].satId : null
            }

            // 🚫 第六層防護：再次檢查是否是最近完成的衛星
            if (
                selectedSatellite === history.lastCompletedSatellite &&
                candidateInfo.length > 1
            ) {
                // 如果選到最近完成的衛星且有其他選擇，選擇其他的
                const alternatives = candidateInfo.filter(
                    (info) => info.satId !== history.lastCompletedSatellite
                )
                selectedSatellite =
                    alternatives.length > 0
                        ? alternatives[0].satId
                        : selectedSatellite
            }

            return selectedSatellite
        },
        [getAvailableSatellites, getSatellitePosition, getUAVPositions]
    )

    // 📝 記錄換手事件（加強防護檢查）
    const recordHandover = (fromSatellite: string, toSatellite: string) => {
        // 🚫 防止自我換手記錄
        if (fromSatellite === toSatellite) {
            return
        }

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
    }

    // 🔗 獲取當前連接距離（用於顯示）
    // const getCurrentConnectionDistance = (): number | null => {
    //     if (!handoverState.currentSatelliteId) return null

    //     const uavPositions = getUAVPositions()
    //     if (uavPositions.length === 0) return null

    //     const satPos = getSatellitePosition(handoverState.currentSatelliteId)
    //     if (!satPos) return null

    //     return calculateDistance(uavPositions[0], satPos)
    // }

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
                case 'stable': {
                    // 穩定期結束，嘗試開始換手
                    const currentSatId = handoverState.currentSatelliteId

                    // 基本檢查：必須有當前衛星
                    if (!currentSatId) {
                        // 重新開始穩定期
                        newState = {
                            ...handoverState,
                            phaseStartTime: now,
                            progress: 0,
                        }
                        break
                    }

                    const targetSatellite = selectNearestSatellite(currentSatId)

                    if (targetSatellite && targetSatellite !== currentSatId) {
                        // 找到有效的換手目標，開始換手流程
                        handoverReasonCounterRef.current += 1
                        newState = {
                            phase: 'preparing',
                            currentSatelliteId: currentSatId,
                            targetSatelliteId: targetSatellite,
                            progress: 0,
                            phaseStartTime: now,
                            totalElapsed:
                                handoverState.totalElapsed + phaseElapsed,
                        }
                    } else {
                        // 沒有找到有效的換手目標，重新開始穩定期
                        newState = {
                            ...handoverState,
                            phaseStartTime: now,
                            progress: 0,
                        }
                    }
                    break
                }

                case 'preparing': {
                    newState = {
                        ...handoverState,
                        phase: 'establishing',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed,
                    }
                    break
                }

                case 'establishing': {
                    newState = {
                        ...handoverState,
                        phase: 'switching',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed,
                    }
                    break
                }

                case 'switching': {
                    newState = {
                        ...handoverState,
                        phase: 'completing',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed,
                    }
                    break
                }

                case 'completing': {
                    // 換手完成，切換到新衛星
                    // const newSatellite = handoverState.targetSatelliteId

                    // 📝 記錄換手事件到歷史記錄
                    if (
                        handoverState.currentSatelliteId &&
                        handoverState.targetSatelliteId
                    ) {
                        recordHandover(
                            handoverState.currentSatelliteId,
                            handoverState.targetSatelliteId
                        )

                        // 設置最近完成換手的衛星
                        const history = handoverHistoryRef.current
                        history.lastCompletedSatellite =
                            handoverState.targetSatelliteId
                        history.lastCompletedTime = now
                    }

                    // 清除模擬數據，下次重新生成
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
                setHandoverState((prev) => ({
                    ...prev,
                    currentSatelliteId: firstSatellite,
                    phaseStartTime: Date.now(),
                }))
            }
        }
    }, [
        enabled,
        satellitePositions,
        handoverState.currentSatelliteId,
        selectNearestSatellite,
    ])

    // 🔄 動態更新換手歷史冷卻期
    useEffect(() => {
        handoverHistoryRef.current.cooldownPeriod =
            handoverMode === 'demo' ? 90000 : 120000 // 加強防護
    }, [handoverMode])

    // 🔄 狀態更新回調（修復useEffect無限循環）
    const statusInfo = useMemo(() => {
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
                    title: '換手連接',
                    subtitle: `換手至: ${targetSatName}`,
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
    }, [
        handoverState.phase,
        handoverState.currentSatelliteId,
        handoverState.targetSatelliteId,
        handoverState.progress,
        handoverState.phaseStartTime,
        PHASE_DURATIONS.preparing,
    ])

    // 狀態更新回調 - 修復無限循環
    const onStatusUpdateRef = useRef(onStatusUpdate)
    onStatusUpdateRef.current = onStatusUpdate

    const onHandoverStateUpdateRef = useRef(onHandoverStateUpdate)
    onHandoverStateUpdateRef.current = onHandoverStateUpdate

    // 使用穩定的引用避免無限循環
    const stableStatusInfoRef = useRef(statusInfo)
    const stableHandoverStateRef = useRef(handoverState)

    useEffect(() => {
        const statusChanged =
            JSON.stringify(stableStatusInfoRef.current) !==
            JSON.stringify(statusInfo)
        if (enabled && onStatusUpdateRef.current && statusChanged) {
            stableStatusInfoRef.current = statusInfo
            onStatusUpdateRef.current(statusInfo)
        }
    }, [statusInfo, enabled])

    useEffect(() => {
        const stateChanged =
            JSON.stringify(stableHandoverStateRef.current) !==
            JSON.stringify(handoverState)
        if (enabled && onHandoverStateUpdateRef.current && stateChanged) {
            stableHandoverStateRef.current = handoverState
            onHandoverStateUpdateRef.current(handoverState)
        }
    }, [handoverState, enabled])

    // 🔗 渲染連接線（支援雙線和動畫效果）
    const renderConnections = () => {
        if (!enabled) return null

        const uavPositions = getUAVPositions()
        const connections: React.ReactElement[] = []

        // 🟢 當前/舊連接線
        if (handoverState.currentSatelliteId) {
            const smoothedPos = smoothedPositionsRef.current.get(
                handoverState.currentSatelliteId
            )
            const satellitePos =
                smoothedPos ||
                getSatellitePosition(handoverState.currentSatelliteId)

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

        // 🔵 目標連接線
        if (
            handoverState.targetSatelliteId &&
            (handoverState.phase === 'establishing' ||
                handoverState.phase === 'switching' ||
                handoverState.phase === 'completing')
        ) {
            const smoothedPos = smoothedPositionsRef.current.get(
                handoverState.targetSatelliteId
            )
            const satellitePos =
                smoothedPos ||
                getSatellitePosition(handoverState.targetSatelliteId)

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

    // 🎨 當前連接線屬性 - 整合真實信號質量數據

    const getCurrentLineProperties = () => {
        // 如果有真實連接求據，優先使用
        if (useRealConnections && realConnectionInfo) {
            const signalQuality = realConnectionInfo.signal_quality
            const baseColor = getConnectionLineColor(signalQuality)
            const baseOpacity = getConnectionLineOpacity(signalQuality)
            const baseRadius = getConnectionLineRadius(signalQuality)

            // 根據連接狀態調整效果
            switch (realConnectionInfo.status) {
                case 'connected': {
                    return {
                        color: baseColor,
                        opacity: baseOpacity,
                        radius: baseRadius,
                    }
                }
                case 'handover_preparing': {
                    const flicker = Math.sin(Date.now() * 0.012) * 0.3 + 0.7
                    return {
                        color: baseColor,
                        opacity: baseOpacity * flicker,
                        radius: baseRadius * 0.9,
                    }
                }
                case 'handover_executing': {
                    return {
                        color: baseColor,
                        opacity: baseOpacity * 0.6,
                        radius: baseRadius * 0.7,
                    }
                }
                case 'disconnected': {
                    return { color: '#ff0000', opacity: 0.3, radius: 0.2 }
                }
                default:
                    return {
                        color: baseColor,
                        opacity: baseOpacity,
                        radius: baseRadius,
                    }
            }
        }

        // 預設模擬行為
        switch (handoverState.phase) {
            case 'stable': {
                return { color: '#00ff00', opacity: 0.9, radius: 0.6 }
            }
            case 'preparing': {
                const flicker = Math.sin(Date.now() * 0.012) * 0.4 + 0.8
                return { color: '#ffaa00', opacity: flicker, radius: 0.5 }
            }
            case 'establishing': {
                return { color: '#ffdd00', opacity: 0.8, radius: 0.4 }
            }
            case 'switching': {
                return { color: '#aaaaaa', opacity: 0.6, radius: 0.4 }
            }
            case 'completing': {
                const fadeOutOpacity = Math.max(
                    0.2,
                    0.6 - handoverState.progress * 0.4
                )
                return {
                    color: '#aaaaaa',
                    opacity: fadeOutOpacity,
                    radius: 0.3,
                }
            }
            default:
                return { color: '#00ff00', opacity: 0.9, radius: 0.6 }
        }
    }

    // 🎨 目標連接線屬性 - 整合真實換手狀態

    const getTargetLineProperties = () => {
        // 如果有真實換手狀態，使用真實數據
        if (useRealConnections && realHandoverStatus) {
            const targetSignalQuality =
                realHandoverStatus.signal_quality_target || -70
            const baseColor = getConnectionLineColor(targetSignalQuality)
            const baseOpacity = getConnectionLineOpacity(targetSignalQuality)
            const baseRadius = getConnectionLineRadius(targetSignalQuality)

            // 根據換手狀態調整效果
            switch (realHandoverStatus.handover_status) {
                case 'predicting':
                case 'preparing': {
                    const establishOpacity =
                        0.3 +
                        (realHandoverStatus.prediction_confidence || 0.5) * 0.5
                    return {
                        color: baseColor,
                        opacity: establishOpacity,
                        radius: baseRadius * 0.8,
                    }
                }
                case 'executing':
                    return {
                        color: baseColor,
                        opacity: baseOpacity * 0.9,
                        radius: baseRadius,
                    }
                case 'completed':
                    return {
                        color: baseColor,
                        opacity: baseOpacity,
                        radius: baseRadius,
                    }
                default:
                    return {
                        color: baseColor,
                        opacity: baseOpacity * 0.5,
                        radius: baseRadius * 0.7,
                    }
            }
        }

        // 預設模擬行為
        switch (handoverState.phase) {
            case 'establishing': {
                const establishOpacity = 0.4 + handoverState.progress * 0.5
                return {
                    color: '#0088ff',
                    opacity: establishOpacity,
                    radius: 0.4,
                }
            }
            case 'switching':
                return { color: '#00ff00', opacity: 0.9, radius: 0.6 }
            case 'completing':
                return { color: '#00ff00', opacity: 0.9, radius: 0.6 }
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

        const smoothedPos = smoothedPositionsRef.current.get(
            handoverState.targetSatelliteId
        )
        const satellitePos =
            smoothedPos || getSatellitePosition(handoverState.targetSatelliteId)

        if (!satellitePos) return null

        const pulseScale = 1 + Math.sin(Date.now() * 0.008) * 0.3

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
