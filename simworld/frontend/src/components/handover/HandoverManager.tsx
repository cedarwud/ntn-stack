import React, { useState, useEffect, useCallback, useRef } from 'react'
import TimePredictionTimeline from './TimePredictionTimeline'
import SatelliteConnectionIndicator from './SatelliteConnectionIndicator'
import HandoverControlPanel from './HandoverControlPanel'
import SynchronizedAlgorithmVisualization from './SynchronizedAlgorithmVisualization'
import UnifiedHandoverStatus from './UnifiedHandoverStatus'
import {
    HandoverState,
    SatelliteConnection,
    TimePredictionData,
    BinarySearchIteration,
    HandoverEvent,
} from '../../types/handover'
import { VisibleSatelliteInfo } from '../../types/satellite'
import './HandoverManager.scss'

interface HandoverManagerProps {
    satellites: VisibleSatelliteInfo[]
    selectedUEId?: number
    isEnabled: boolean
    onHandoverEvent?: (event: HandoverEvent) => void
    mockMode?: boolean // 用於開發測試
    hideUI?: boolean // 隱藏 UI 但保持邏輯運行
    handoverMode?: 'demo' | 'real' // 換手模式控制
    // 3D 動畫狀態更新回調
    onHandoverStateChange?: (state: HandoverState) => void
    onCurrentConnectionChange?: (connection: SatelliteConnection | null) => void
    onPredictedConnectionChange?: (
        connection: SatelliteConnection | null
    ) => void
    onTransitionChange?: (isTransitioning: boolean, progress: number) => void
    // 🚀 演算法結果回調 - 用於對接視覺化
    onAlgorithmResults?: (results: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }) => void
    // 🎮 衛星速度同步
    speedMultiplier?: number
}

const HandoverManager: React.FC<HandoverManagerProps> = ({
    satellites,
    selectedUEId,
    isEnabled,
    onHandoverEvent,
    // mockMode = false, // 使用真實後端數據，true 時啟用模擬模式
    hideUI = false,
    handoverMode = 'demo',
    onHandoverStateChange,
    onCurrentConnectionChange,
    onPredictedConnectionChange,
    onTransitionChange,
    onAlgorithmResults,
    speedMultiplier = 60,
}) => {
    // 調試輸出 - 檢查接收到的衛星數據
    useEffect(() => {
        console.log('🛰️ HandoverManager 接收到的衛星數據:', {
            satellites: satellites,
            count: satellites?.length || 0,
            enabled: isEnabled,
        })
    }, [satellites, isEnabled])

    // 換手狀態管理
    const [handoverState, setHandoverState] = useState<HandoverState>({
        currentSatellite: '',
        predictedSatellite: '',
        handoverTime: 0,
        status: 'idle',
        confidence: 0.95,
        deltaT: 5, // 5秒間隔 - 論文標準
    })

    // 🎯 時間預測數據
    const [timePredictionData, setTimePredictionData] =
        useState<TimePredictionData>({
            currentTime: Date.now(),
            futureTime: Date.now() + 5000, // 5秒後
            handoverTime: undefined,
            iterations: [],
            accuracy: 0.95,
        })

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
        cooldownPeriod: handoverMode === 'demo' ? 90000 : 120000, // 演示模式90秒，真實模式120秒（統一加強防護）
    })

    // 衛星連接狀態
    const [currentConnection, setCurrentConnection] =
        useState<SatelliteConnection | null>(null)
    const [predictedConnection, setPredictedConnection] =
        useState<SatelliteConnection | null>(null)
    const [isTransitioning, setIsTransitioning] = useState(false)
    const [transitionProgress, setTransitionProgress] = useState(0)

    // 控制面板模式換手
    const [controlMode, setControlMode] = useState<'auto' | 'manual'>('auto')
    
    // 調試控制模式變化
    useEffect(() => {
        console.log('🎮 HandoverManager 控制模式:', controlMode, 'isEnabled:', isEnabled)
    }, [controlMode, isEnabled])

    // 標籤頁狀態管理
    const [activeTab, setActiveTab] = useState<'status' | 'algorithm'>('status')

    // 可用衛星數據狀態 - 供 HandoverControlPanel 使用
    const [availableSatellitesForControl, setAvailableSatellitesForControl] =
        useState<VisibleSatelliteInfo[]>([])

    // 🚀 演算法結果狀態 - 供統一狀態組件使用
    const [algorithmPredictionResult, setAlgorithmPredictionResult] = useState<any>(null)
    const [algorithmRunning, setAlgorithmRunning] = useState(false)
    const [currentDeltaT, setCurrentDeltaT] = useState<number>(5) // 預設5秒 (論文標準)

    // 模擬數據生成器（開發用）
    const generateMockSatelliteConnection = useCallback(
        (
            satellite: VisibleSatelliteInfo,
            isConnected: boolean = false
        ): SatelliteConnection => {
            return {
                satelliteId: satellite.norad_id.toString(),
                satelliteName: satellite.name
                    .replace(' [DTC]', '')
                    .replace('[DTC]', ''),
                elevation: satellite.elevation_deg,
                azimuth: satellite.azimuth_deg,
                distance: satellite.distance_km,
                signalStrength: -60 - Math.random() * 40, // -60 to -100 dBm
                isConnected,
                isPredicted: !isConnected,
            }
        },
        []
    )

    // 🔗 模擬二點預測算法 - 與 DynamicSatelliteRenderer 的 ID 系統兼容
    const simulateTwoPointPrediction = useCallback(() => {
        // 🚀 使用真實的衛星數據，如果沒有則回退到模擬數據
        let availableSatellites: VisibleSatelliteInfo[] = []

        if (satellites && satellites.length > 0) {
            // 使用真實的衛星數據
            availableSatellites = satellites.map((sat) => ({
                ...sat,
                norad_id:
                    typeof sat.norad_id === 'string'
                        ? parseInt(sat.norad_id)
                        : sat.norad_id,
            }))
        } else {
            // 回退到模擬數據
            availableSatellites = Array.from({ length: 18 }, (_, i) => ({
                norad_id: 1000 + i,
                name: `STARLINK-${1000 + i}`,
                elevation_deg: 30 + Math.random() * 60,
                azimuth_deg: Math.random() * 360,
                distance_km: 500 + Math.random() * 500,
                line1: `1 ${
                    1000 + i
                }U 20001001.00000000  .00000000  00000-0  00000-0 0  9999`,
                line2: `2 ${
                    1000 + i
                }  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000`,
            }))
        }

        // 將處理後的衛星數據設置到狀態中，以便 HandoverControlPanel 使用
        setAvailableSatellitesForControl(availableSatellites)

        const now = Date.now()
        const futureTime = now + currentDeltaT * 1000

        // 🎯 模擬選擇當前最佳衛星 - 優先選擇前幾個衛星以提高匹配機率
        const currentBestIndex = Math.floor(
            Math.random() * Math.min(6, availableSatellites.length)
        ) // 前6個衛星
        const currentBest = availableSatellites[currentBestIndex]

        // 🚫 核心修復：確保不會選擇自己作為換手目標
        // 先過濾掉當前衛星，確保候選列表不包含自己
        let availableTargets = availableSatellites.filter(
            (_, index) => index !== currentBestIndex
        )

        // 🚫 如果沒有可用目標，直接返回不換手
        if (availableTargets.length === 0) {
            console.warn('⚠️ 沒有可用的換手目標衛星')
            setHandoverState((prev) => ({
                ...prev,
                currentSatellite: currentBest?.norad_id.toString() || '',
                predictedSatellite: '', // 清空預測衛星
                handoverTime: 0,
                status: 'idle',
            }))

            if (currentBest) {
                const currentConn = generateMockSatelliteConnection(
                    currentBest,
                    true
                )
                setCurrentConnection(currentConn)
            }
            setPredictedConnection(null)
            return
        }

        // 🚫 清理過期的換手記錄
        const history = handoverHistoryRef.current
        history.recentHandovers = history.recentHandovers.filter(
            (record) => now - record.timestamp < history.cooldownPeriod
        )

        // 🔄 如果有當前衛星，檢查換手歷史
        if (currentBest && availableTargets.length > 0) {
            const currentSatId = currentBest.norad_id.toString()

            // 找出最近與當前衛星有換手記錄的衛星
            const recentPartners = new Set<string>()

            history.recentHandovers.forEach((record) => {
                // 檢查雙向換手記錄
                if (record.from === currentSatId) {
                    recentPartners.add(record.to)
                } else if (record.to === currentSatId) {
                    recentPartners.add(record.from)
                }
            })

            // 🎯 優先選擇沒有最近換手記錄的衛星
            const preferredTargets = availableTargets.filter(
                (sat) => !recentPartners.has(sat.norad_id.toString())
            )

            if (preferredTargets.length > 0) {
                availableTargets = preferredTargets
            }
        }

        // 🎯 智能選擇換手目標 - 基於多種策略
        let futureBest: VisibleSatelliteInfo | null = null

        if (availableTargets.length > 0) {
            // 策略1：優先選擇相鄰的衛星（更符合軌道換手邏輯）
            const adjacentCandidates = []
            if (currentBestIndex < availableSatellites.length - 1) {
                const nextSat = availableSatellites[currentBestIndex + 1]
                if (availableTargets.includes(nextSat)) {
                    adjacentCandidates.push(nextSat)
                }
            }
            if (currentBestIndex > 0) {
                const prevSat = availableSatellites[currentBestIndex - 1]
                if (availableTargets.includes(prevSat)) {
                    adjacentCandidates.push(prevSat)
                }
            }

            if (adjacentCandidates.length > 0 && Math.random() < 0.6) {
                // 60% 機率選擇相鄰衛星
                futureBest =
                    adjacentCandidates[
                        Math.floor(Math.random() * adjacentCandidates.length)
                    ]
            } else {
                // 策略2：選擇信號品質最佳的衛星
                futureBest = availableTargets.reduce((best, sat) =>
                    !best || sat.elevation_deg > best.elevation_deg ? sat : best
                )
            }
        }

        // 🚫 最終安全檢查：確保選擇的衛星不是當前衛星
        if (!futureBest || futureBest.norad_id === currentBest?.norad_id) {
            console.warn('⚠️ 無法找到合適的換手目標，保持當前連接')
            setHandoverState((prev) => ({
                ...prev,
                currentSatellite: currentBest?.norad_id.toString() || '',
                predictedSatellite: '', // 清空預測衛星
                handoverTime: 0,
                status: 'idle',
            }))

            if (currentBest) {
                const currentConn = generateMockSatelliteConnection(
                    currentBest,
                    true
                )
                setCurrentConnection(currentConn)
            }
            setPredictedConnection(null)
            return
        }

        // ✅ 成功選擇換手目標
        setHandoverState((prev) => ({
            ...prev,
            currentSatellite: currentBest?.norad_id.toString() || '',
            predictedSatellite: futureBest?.norad_id.toString() || '',
            status: 'predicting',
        }))

        // 🔗 更新連接狀態
        if (currentBest) {
            const currentConn = generateMockSatelliteConnection(
                currentBest,
                true
            )
            setCurrentConnection(currentConn)
        }

        // 🎯 由於我們已經確保futureBest不等於currentBest，這裡一定會執行換手邏輯
        const predictedConn = generateMockSatelliteConnection(futureBest, false)
        setPredictedConnection(predictedConn)

        // 更新時間預測數據 - 基於論文邏輯計算換手時間
        const currentDeltaTValue = currentDeltaTRef.current
        const deltaT = Math.max(3, currentDeltaTValue) * 1000 // 使用當前的 delta-t (秒轉換為毫秒)，最小3秒
        
        // console.log(`🚀 simulateTwoPointPrediction 被調用! currentDeltaT=${currentDeltaTValue}s, deltaT=${deltaT}ms`)
        
        // 🔧 計算新的換手時間 - 每次新時間軸都重新計算
        const randomPosition = 0.3 + Math.random() * 0.4 // 30%-70% 範圍內隨機
        const handoverOffset = deltaT * randomPosition
        const handoverTime = now + handoverOffset
        
        // console.log(`🎯 新時間軸: T=${new Date(now).toLocaleTimeString()}, T+Δt=${new Date(now + deltaT).toLocaleTimeString()}, 換手=${new Date(handoverTime).toLocaleTimeString()}`)
        
        // 先生成 Binary Search 數據
        const binarySearchData = generateBinarySearchData(now, now + deltaT)

        const newTimePredictionData = {
            currentTime: now,
            futureTime: now + deltaT,
            handoverTime: handoverTime, // 在時間軸期間保持固定
            iterations: binarySearchData.iterations, // 直接設置生成的 iterations
            accuracy: 0.95 + Math.random() * 0.04, // 95-99%
        }
        
        // console.log(`📊 setTimePredictionData 被調用，iterations 數量:`, newTimePredictionData.iterations.length)
        setTimePredictionData(newTimePredictionData)

        // 同時更新 handoverState
        setHandoverState((prev) => ({
            ...prev,
            handoverTime: binarySearchData.finalHandoverTime,
            status: 'idle',
        }))

        // 換手決策完成
    }, []) // 🔧 暫時移除所有依賴，專注於修復時間軸跳動問題

    // 生成 Binary Search 數據 - 同步函數，避免狀態競態
    const generateBinarySearchData = (startTime: number, endTime: number) => {
        const iterations: BinarySearchIteration[] = []
        const totalDuration = endTime - startTime
        let currentStart = 0 // 使用相對時間
        let currentEnd = totalDuration / 1000 // 轉換為秒
        
        // 動態調整精度目標，讓迭代次數有更大變化
        const timeVariation = Math.floor(startTime / 12000) % 5 // 每 12 秒變化一次
        const targetPrecision = [0.01, 0.05, 0.1, 0.2, 0.4][timeVariation] // 10ms, 50ms, 100ms, 200ms, 400ms 精度
        // 預期迭代次數: 9次, 7次, 6次, 5次, 4次
        
        // 生成所有迭代步驟
        let iterationCount = 0
        let tempStart = currentStart
        let tempEnd = currentEnd
        
        while (tempEnd - tempStart > targetPrecision && iterationCount < 10) {
            iterationCount++
            const midTime = (tempStart + tempEnd) / 2
            const precision = tempEnd - tempStart
            
            // 基於時間戳生成動態衛星名稱，確保每次都不同
            const timeHash = Math.floor(startTime / 10000) % 1000 // 10秒變化一次
            const satelliteBase = 1000 + (timeHash + iterationCount) % 500
            const satelliteName = `STARLINK-${satelliteBase.toString().padStart(4, '0')}`
            
            const iteration: BinarySearchIteration = {
                iteration: iterationCount,
                startTime: startTime + tempStart * 1000,
                endTime: startTime + tempEnd * 1000,
                midTime: startTime + midTime * 1000,
                satellite: satelliteName,
                precision,
                completed: false, // 初始都設為未完成，將由 TimePredictionTimeline 動態更新
            }
            
            iterations.push(iteration)
            
            // 模擬二分搜尋縮小範圍 - 交替選擇前半段和後半段
            if (iterationCount % 2 === 1) {
                tempStart = midTime // 換手在後半段
            } else {
                tempEnd = midTime // 換手在前半段
            }
        }
        
        const finalHandoverTime = iterations.length > 0 
            ? iterations[iterations.length - 1].midTime 
            : startTime + totalDuration * 0.6
            
        // console.log(`🔄 Binary Search 更新: ${iterations.length} 次迭代, 目標精度: ${targetPrecision}s (${targetPrecision*1000}ms), 最終精度: ${(iterations[iterations.length-1]?.precision || 0).toFixed(3)}s`)
        
        return {
            iterations,
            finalHandoverTime
        }
    }


    // 手動換手處理
    const handleManualHandover = useCallback(
        async (targetSatelliteId: string) => {
            const targetSatellite = satellites.find(
                (s) => s.norad_id.toString() === targetSatelliteId
            )
            if (!targetSatellite || !currentConnection) return

            setHandoverState((prev) => ({ ...prev, status: 'handover' }))
            setIsTransitioning(true)
            setTransitionProgress(0)

            // 創建換手事件
            const handoverEvent: HandoverEvent = {
                id: `handover_${Date.now()}`,
                timestamp: Date.now(),
                fromSatellite: currentConnection.satelliteId,
                toSatellite: targetSatelliteId,
                duration: 0,
                success: false,
                reason: 'manual',
            }

            // 模擬換手過程
            const startTime = Date.now()
            const handoverDuration = 3500 + Math.random() * 3000 // 3.5-6.5秒 - 平衡速度與真實感

            const progressInterval = setInterval(() => {
                const elapsed = Date.now() - startTime
                const progress = Math.min(elapsed / handoverDuration, 1)
                setTransitionProgress(progress)

                if (progress >= 1) {
                    clearInterval(progressInterval)

                    // 換手完成
                    const success = Math.random() > 0.1 // 90% 成功率
                    const newConnection = generateMockSatelliteConnection(
                        targetSatellite,
                        true
                    )

                    setCurrentConnection(newConnection)
                    setPredictedConnection(null)
                    setIsTransitioning(false)
                    setTransitionProgress(0)

                    setHandoverState((prev) => ({
                        ...prev,
                        currentSatellite: targetSatelliteId,
                        status: success ? 'complete' : 'failed',
                    }))

                    // 📝 記錄換手事件到歷史記錄（只有成功的換手才記錄）
                    if (success) {
                        recordHandover(
                            currentConnection.satelliteId,
                            targetSatelliteId
                        )
                    }

                    // 發送換手事件
                    const completedEvent: HandoverEvent = {
                        ...handoverEvent,
                        duration: Date.now() - startTime,
                        success,
                    }
                    onHandoverEvent?.(completedEvent)

                    // 2秒後重置狀態
                    setTimeout(() => {
                        setHandoverState((prev) => ({
                            ...prev,
                            status: 'idle',
                        }))
                    }, 2000)
                }
            }, 100)
        },
        [
            satellites,
            currentConnection,
            generateMockSatelliteConnection,
            onHandoverEvent,
        ]
    )

    // 取消換手
    const handleCancelHandover = useCallback(() => {
        setIsTransitioning(false)
        setTransitionProgress(0)
        setHandoverState((prev) => ({ ...prev, status: 'idle' }))
    }, [])

    // 使用 useRef 避免依賴循環和閉包問題
    const simulateTwoPointPredictionRef = useRef(simulateTwoPointPrediction)
    simulateTwoPointPredictionRef.current = simulateTwoPointPrediction
    
    const timePredictionDataRef = useRef(timePredictionData)
    timePredictionDataRef.current = timePredictionData
    
    const currentDeltaTRef = useRef(currentDeltaT)
    currentDeltaTRef.current = currentDeltaT

    // 初始化和智能更新 - 只在時間軸完成後才重新開始
    useEffect(() => {
        if (!isEnabled || controlMode !== 'auto') {
            return
        }

        // console.log('🚀 HandoverManager: 初始化時間軸管理')

        // 初始化
        simulateTwoPointPredictionRef.current()

        // 智能檢查時間軸是否完成 - 每秒檢查一次
        const interval = setInterval(() => {
            const now = Date.now()
            const futureTime = timePredictionDataRef.current.futureTime
            const timelineFinished = now >= futureTime
            const remaining = Math.max(0, (futureTime - now) / 1000)
            
            if (timelineFinished) {
                // console.log('✅ 時間軸完成，開始新預測')
                simulateTwoPointPredictionRef.current()
            }
        }, 1000) // 每秒檢查一次，而不是每 deltaT 秒強制重置

        return () => {
            clearInterval(interval)
        }
    }, [
        isEnabled,
        controlMode,
        // 完全移除 simulateTwoPointPrediction 依賴
    ])

    // 初始化衛星數據 - 無論模式如何都要載入
    useEffect(() => {
        if (satellites && satellites.length > 0) {
            const processedSatellites = satellites.map((sat) => ({
                ...sat,
                norad_id:
                    typeof sat.norad_id === 'string'
                        ? parseInt(sat.norad_id)
                        : sat.norad_id,
            }))
            setAvailableSatellitesForControl(processedSatellites)
        }
    }, [satellites])

    // 移除了 handleTimeUpdate 函數，避免無限循環更新

    // 狀態同步到 3D 動畫
    useEffect(() => {
        if (onHandoverStateChange) {
            onHandoverStateChange(handoverState)
        }
    }, [handoverState, onHandoverStateChange])

    useEffect(() => {
        if (onCurrentConnectionChange) {
            onCurrentConnectionChange(currentConnection)
        }
    }, [currentConnection, onCurrentConnectionChange])

    useEffect(() => {
        if (onPredictedConnectionChange) {
            onPredictedConnectionChange(predictedConnection)
        }
    }, [predictedConnection, onPredictedConnectionChange])

    useEffect(() => {
        if (onTransitionChange) {
            onTransitionChange(isTransitioning, transitionProgress)
        }
    }, [isTransitioning, transitionProgress, onTransitionChange])

    // 📝 記錄換手事件
    const recordHandover = useCallback(
        (fromSatellite: string, toSatellite: string) => {
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

            // 換手記錄已更新
        },
        [handoverMode]
    )

    // 🔄 當換手模式改變時，更新冷卻期並清理歷史記錄
    useEffect(() => {
        const newCooldown = handoverMode === 'demo' ? 90000 : 120000
        if (handoverHistoryRef.current.cooldownPeriod !== newCooldown) {
            handoverHistoryRef.current.cooldownPeriod = newCooldown
            // 清空所有歷史記錄，避免模式切換時的衝突
            handoverHistoryRef.current.recentHandovers = []
            // 模式切換完成
        }
    }, [handoverMode])

    if (!isEnabled) {
        return (
            <div className="handover-manager disabled">
                <div className="disabled-message">
                    <h3>🔒 換手管理器已停用</h3>
                    <p>請啟用換手相關功能來使用此面板</p>
                </div>
            </div>
        )
    }

    // 🚀 如果 hideUI 為 true，則隱藏所有 UI 但保持邏輯運行
    if (hideUI) {
        return null
    }

    return (
        <div className="handover-manager">
            <div className="manager-header">
                <h2>🔄 LEO 衛星換手管理系統</h2>
                {selectedUEId && (
                    <div className="selected-ue">
                        <span>控制 UE: {selectedUEId}</span>
                    </div>
                )}
            </div>

            {/* 模式換手控制 - 移到最頂部作為全局控制 */}
            <div className="mode-switcher">
                <div className="switcher-header">
                    <span className="switcher-title">換手控制模式</span>
                </div>
                <div className="switcher-tabs">
                    <button
                        className={`switcher-tab ${
                            controlMode === 'auto' ? 'active' : ''
                        }`}
                        onClick={() => setControlMode('auto')}
                    >
                        <span className="tab-icon">🤖</span>
                        <span className="tab-label">自動預測</span>
                    </button>
                    <button
                        className={`switcher-tab ${
                            controlMode === 'manual' ? 'active' : ''
                        }`}
                        onClick={() => setControlMode('manual')}
                    >
                        <span className="tab-icon">🎮</span>
                        <span className="tab-label">手動控制</span>
                    </button>
                </div>
            </div>

            <div className="manager-content">
                {/* 二點預測時間軸 - 在兩種模式下都顯示 */}
                <TimePredictionTimeline
                    data={timePredictionData}
                    isActive={isEnabled}
                    onTimeUpdate={undefined} // 🔧 移除時間更新回調，避免無限循環
                />

                {/* 統一的狀態顯示 */}
                <div className="unified-content">
                    {controlMode === 'auto' ? (
                        <UnifiedHandoverStatus
                            currentConnection={currentConnection}
                            predictedConnection={predictedConnection}
                            handoverState={handoverState}
                            isTransitioning={isTransitioning}
                            transitionProgress={transitionProgress}
                            predictionResult={algorithmPredictionResult}
                            algorithmRunning={algorithmRunning}
                            deltaT={currentDeltaT}
                        />
                    ) : (
                        <HandoverControlPanel
                            handoverState={handoverState}
                            availableSatellites={availableSatellitesForControl}
                            currentConnection={currentConnection}
                            onManualHandover={handleManualHandover}
                            onCancelHandover={handleCancelHandover}
                            isEnabled={isEnabled}
                        />
                    )}
                </div>

                {/* 詳細演算法監控 - 可摺疊 */}
                {controlMode === 'auto' && (
                    <details className="algorithm-details" open>
                        <summary className="algorithm-summary">
                            <span className="summary-icon">🧮</span>
                            <span className="summary-text">詳細演算法監控</span>
                            <span className="summary-indicator">▼</span>
                        </summary>
                        <div className="algorithm-content">
                            <SynchronizedAlgorithmVisualization
                                satellites={satellites}
                                selectedUEId={selectedUEId}
                                isEnabled={isEnabled} // 🔧 重新啟用，使用 useRef 避免依賴循環
                                speedMultiplier={speedMultiplier}
                                onAlgorithmStep={() => {
                                    // 處理算法步驟事件
                                }}
                                onAlgorithmResults={(results) => {
                                    // 更新統一狀態組件的資料
                                    setAlgorithmRunning(results.handoverStatus === 'calculating' || results.handoverStatus === 'executing')
                                    
                                    // 如果有預測結果，更新狀態
                                    if (results.predictionResult) {
                                        setAlgorithmPredictionResult(results.predictionResult)
                                        
                                        // 🔧 只在必要時更新 currentDeltaT，避免干擾時間軸
                                        const now = Date.now()
                                        const timelineFinished = now >= timePredictionDataRef.current.futureTime
                                        const newDeltaT = results.predictionResult.delta_t_seconds || 5
                                        
                                        // console.log(`🔄 SynchronizedAlgorithmVisualization 結果: newDeltaT=${newDeltaT}s, timelineFinished=${timelineFinished}, currentDeltaT=${currentDeltaT}s`)
                                        
                                        // 只在時間軸完成且 deltaT 真的改變時才更新
                                        if (timelineFinished && Math.abs(newDeltaT - currentDeltaT) > 0.1) {
                                            // console.log(`✅ 更新 currentDeltaT: ${currentDeltaT}s → ${newDeltaT}s`)
                                            setCurrentDeltaT(newDeltaT)
                                        }
                                    }
                                    
                                    onAlgorithmResults?.(results)
                                }}
                            />
                        </div>
                    </details>
                )}

                {/* 移除重複的後台組件 - 統一使用可見的組件 */}
            </div>
        </div>
    )
}

export default HandoverManager
