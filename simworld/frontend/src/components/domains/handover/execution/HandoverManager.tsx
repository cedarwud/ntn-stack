import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useStrategy } from '../../../../hooks/useStrategy'
import { HandoverStrategy } from '../../../../contexts/StrategyContext'
import TimePredictionTimeline from '../prediction/TimePredictionTimeline'
import SynchronizedAlgorithmVisualization from '../synchronization/SynchronizedAlgorithmVisualization'
import UnifiedHandoverStatus from './UnifiedHandoverStatus'
import {
    HandoverState,
    SatelliteConnection,
    TimePredictionData,
    BinarySearchIteration,
    HandoverEvent,
} from '../../../../types/handover'
import { VisibleSatelliteInfo } from '../../../../types/satellite'
import {
    HANDOVER_CONFIG,
    getHandoverCooldownPeriod,
    getBinarySearchPrecision,
} from '../config/handoverConfig'
import { HandoverDecisionEngine } from '../utils/handoverDecisionEngine'
import {
    generateMockSatelliteConnection,
    generateMockSatellites,
} from '../utils/satelliteUtils'
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
    // 🎯 換手策略
    handoverStrategy?: HandoverStrategy
}

const HandoverManager: React.FC<HandoverManagerProps> = ({
    satellites,
    selectedUEId,
    isEnabled,
    // onHandoverEvent,
    // mockMode = false, // 使用真實後端數據，true 時啟用模擬模式
    hideUI = false,
    handoverMode = 'demo',
    onHandoverStateChange,
    onCurrentConnectionChange,
    onPredictedConnectionChange,
    onTransitionChange,
    onAlgorithmResults,
    speedMultiplier = 60,
    handoverStrategy: propStrategy,
}) => {
    // 🎯 使用全域策略狀態 - 添加錯誤邊界
    let currentStrategy: HandoverStrategy = 'flexible'
    let globalSwitchStrategy: (
        strategy: HandoverStrategy
    ) => Promise<void> = async () => {}
    let strategyLoading = false

    try {
        const strategyContext = useStrategy()
        currentStrategy = strategyContext.currentStrategy
        globalSwitchStrategy = strategyContext.switchStrategy
        strategyLoading = strategyContext.isLoading
    } catch (error) {
        console.warn(
            '⚠️ HandoverManager: 無法獲取策略上下文，使用預設值:',
            error
        )
    }

    const activeStrategy = propStrategy || currentStrategy

    // 換手狀態管理 - 添加安全初始化
    const [handoverState, setHandoverState] = useState<HandoverState>(() => {
        try {
            return {
                currentSatellite: '',
                predictedSatellite: '',
                handoverTime: 0,
                status: 'idle',
                confidence:
                    HANDOVER_CONFIG?.ACCURACY?.DEFAULT_CONFIDENCE || 0.95,
                deltaT: HANDOVER_CONFIG?.TIMING?.DEFAULT_DELTA_T_SECONDS || 5,
            }
        } catch (error) {
            console.error(
                '⚠️ HandoverManager: 配置初始化失敗，使用後備值:',
                error
            )
            return {
                currentSatellite: '',
                predictedSatellite: '',
                handoverTime: 0,
                status: 'idle',
                confidence: 0.95,
                deltaT: 5,
            }
        }
    })

    // 🎯 時間預測數據
    const [timePredictionData, setTimePredictionData] =
        useState<TimePredictionData>({
            currentTime: Date.now(),
            futureTime:
                Date.now() +
                HANDOVER_CONFIG.TIMING.DEFAULT_DELTA_T_SECONDS * 1000,
            handoverTime: undefined,
            iterations: [],
            accuracy: HANDOVER_CONFIG.ACCURACY.DEFAULT_CONFIDENCE,
        })

    // 🔄 換手歷史記錄 - 防止頻繁互換 - 添加安全初始化
    const handoverHistoryRef = useRef<{
        recentHandovers: Array<{
            from: string
            to: string
            timestamp: number
        }>
        cooldownPeriod: number // 冷卻期（毫秒）
    }>({
        recentHandovers: [],
        cooldownPeriod: (() => {
            try {
                return getHandoverCooldownPeriod(
                    handoverMode as 'demo' | 'real'
                )
            } catch (error) {
                console.warn(
                    '⚠️ HandoverManager: 冷卻期配置失敗，使用預設值:',
                    error
                )
                return 90000 // 90秒預設值
            }
        })(),
    })

    // 衛星連接狀態
    const [currentConnection, setCurrentConnection] =
        useState<SatelliteConnection | null>(null)
    const [predictedConnection, setPredictedConnection] =
        useState<SatelliteConnection | null>(null)
    const [isTransitioning] = useState(false)
    const [transitionProgress] = useState(0)

    // 🚀 演算法結果狀態 - 供統一狀態組件使用
    const [algorithmPredictionResult, setAlgorithmPredictionResult] =
        useState<unknown>(null)
    const [algorithmRunning, setAlgorithmRunning] = useState(false)
    const [currentDeltaT, setCurrentDeltaT] = useState<number>(
        HANDOVER_CONFIG.TIMING.DEFAULT_DELTA_T_SECONDS
    )
    const [realHandoverRequired, setRealHandoverRequired] =
        useState<boolean>(false) // 真實換手需求狀態
    const [connectionDataSource, setConnectionDataSource] = useState<
        'simulation' | 'algorithm'
    >('simulation') // 連接數據來源
    const algorithmDataTimeoutRef = useRef<NodeJS.Timeout | null>(null) // 演算法數據超時計時器

    // 🔗 模擬二點預測算法 - 與 DynamicSatelliteRenderer 的 ID 系統兼容
    const simulateTwoPointPrediction = useCallback(() => {
        // 🚀 使用真實的衛星數據，如果沒有則回退到模擬數據
        let availableSatellites: VisibleSatelliteInfo[] = []

        if (satellites && satellites.length > 0) {
            // 使用真實的衛星數據 (已經是 VisibleSatelliteInfo[] 類型)
            availableSatellites = satellites
        } else {
            // 回退到模擬數據
            availableSatellites = generateMockSatellites()
        }

        const now = Date.now()
        // const futureTime = now + currentDeltaT * 1000

        // 🎯 模擬選擇當前最佳衛星 - 優先選擇前幾個衛星以提高匹配機率
        const currentBestIndex = Math.floor(
            Math.random() *
                Math.min(
                    HANDOVER_CONFIG.SATELLITE_SELECTION.MAX_FRONT_SATELLITES,
                    availableSatellites.length
                )
        )
        const currentBest = availableSatellites[currentBestIndex]

        // 🎯 使用統一的換手決策引擎
        const decision = HandoverDecisionEngine.shouldHandover(
            currentBest,
            availableSatellites,
            now,
            handoverHistoryRef.current.recentHandovers,
            handoverHistoryRef.current.cooldownPeriod
        )

        // 清理過期的換手記錄
        handoverHistoryRef.current.recentHandovers =
            handoverHistoryRef.current.recentHandovers.filter(
                (record) =>
                    now - record.timestamp <
                    handoverHistoryRef.current.cooldownPeriod
            )

        // 更新換手狀態
        setHandoverState((prev) => ({
            ...prev,
            currentSatellite: currentBest?.norad_id.toString() || '',
            predictedSatellite: decision.needsHandover
                ? decision.targetSatellite?.norad_id.toString() || ''
                : '',
            status: decision.needsHandover ? 'predicting' : 'idle',
            confidence: decision.confidence,
        }))

        // 🔗 更新連接狀態 (只在沒有演算法數據時)
        if (connectionDataSource === 'simulation') {
            if (currentBest) {
                const currentConn = generateMockSatelliteConnection(
                    currentBest,
                    true
                )
                setCurrentConnection(currentConn)
            }

            if (decision.needsHandover && decision.targetSatellite) {
                const predictedConn = generateMockSatelliteConnection(
                    decision.targetSatellite,
                    false
                )
                setPredictedConnection(predictedConn)
            } else {
                setPredictedConnection(null)
            }
        }

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
    }, [connectionDataSource, satellites]) // 加回必要的依賴

    // 🎯 策略變更監聽器
    useEffect(() => {
        const handleStrategyChange = (event: CustomEvent) => {
            const { strategy } = event.detail
            console.log(`📵 HandoverManager 接收到策略變更: ${strategy}`)

            // 根據策略調整換手參數
            if (strategy === 'consistent') {
                // Consistent 策略：更頻繁的換手、更高精確度
                setHandoverState((prev) => ({
                    ...prev,
                    confidence: 0.97 + Math.random() * 0.02, // 97-99%
                    deltaT: 2, // 更短的時間間隔
                }))
                console.log('🔥 已切換到 Consistent 策略：高精確度、短周期')
            } else {
                // Flexible 策略：較少換手、節省資源
                setHandoverState((prev) => ({
                    ...prev,
                    confidence: 0.92 + Math.random() * 0.03, // 92-95%
                    deltaT: 5, // 更長的時間間隔
                }))
                console.log('🔋 已切換到 Flexible 策略：中等精確度、長周期')
            }
        }

        window.addEventListener(
            'strategyChanged',
            handleStrategyChange as EventListener
        )

        // 初始化時也根據當前策略設定
        handleStrategyChange({
            detail: { strategy: activeStrategy },
        } as CustomEvent)

        return () => {
            window.removeEventListener(
                'strategyChanged',
                handleStrategyChange as EventListener
            )
        }
    }, [activeStrategy])

    // 生成 Binary Search 數據 - 同步函數，避免狀態競態
    const generateBinarySearchData = (startTime: number, endTime: number) => {
        const iterations: BinarySearchIteration[] = []
        const totalDuration = endTime - startTime
        const currentStart = 0 // 使用相對時間
        const currentEnd = totalDuration / 1000 // 轉換為秒

        // 動態調整精度目標，讓迭代次數有更大變化
        const targetPrecision = getBinarySearchPrecision(startTime)
        // 預期迭代次數: 9次, 7次, 6次, 5次, 4次

        // 生成所有迭代步驟
        let iterationCount = 0
        let tempStart = currentStart
        let tempEnd = currentEnd

        while (
            tempEnd - tempStart > targetPrecision &&
            iterationCount < HANDOVER_CONFIG.BINARY_SEARCH.MAX_ITERATIONS
        ) {
            iterationCount++
            const midTime = (tempStart + tempEnd) / 2
            const precision = tempEnd - tempStart

            // 使用統一的衛星名稱生成器
            const satelliteName =
                HandoverDecisionEngine.generateDynamicSatelliteName(
                    startTime,
                    iterationCount
                )

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

        const finalHandoverTime =
            iterations.length > 0
                ? iterations[iterations.length - 1].midTime
                : startTime + totalDuration * 0.6

        // console.log(`🔄 Binary Search 更新: ${iterations.length} 次迭代, 目標精度: ${targetPrecision}s (${targetPrecision*1000}ms), 最終精度: ${(iterations[iterations.length-1]?.precision || 0).toFixed(3)}s`)

        return {
            iterations,
            finalHandoverTime,
        }
    }

    // 使用 useRef 避免依賴循環和閉包問題
    const simulateTwoPointPredictionRef = useRef(simulateTwoPointPrediction)
    simulateTwoPointPredictionRef.current = simulateTwoPointPrediction

    const timePredictionDataRef = useRef(timePredictionData)
    timePredictionDataRef.current = timePredictionData

    const currentDeltaTRef = useRef(currentDeltaT)
    currentDeltaTRef.current = currentDeltaT

    // 初始化和智能更新 - 只在時間軸完成後才重新開始
    useEffect(() => {
        if (!isEnabled) {
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
            // const remaining = Math.max(0, (futureTime - now) / 1000)

            if (timelineFinished) {
                // console.log('✅ 時間軸完成，開始新預測')
                simulateTwoPointPredictionRef.current()
            }
        }, HANDOVER_CONFIG.TIMING.ALGORITHM_CHECK_INTERVAL_MS)

        return () => {
            clearInterval(interval)
        }
    }, [
        isEnabled,
        // 完全移除 simulateTwoPointPrediction 依賴
    ])

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
    /*
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
    */

    // 🔄 當換手模式改變時，更新冷卻期並清理歷史記錄
    useEffect(() => {
        const newCooldown = getHandoverCooldownPeriod(
            handoverMode as 'demo' | 'real'
        )
        if (handoverHistoryRef.current.cooldownPeriod !== newCooldown) {
            handoverHistoryRef.current.cooldownPeriod = newCooldown
            // 清空所有歷史記錄，避免模式切換時的衝突
            handoverHistoryRef.current.recentHandovers = []
        }
    }, [handoverMode])

    // 組件卸載時清理計時器
    useEffect(() => {
        return () => {
            if (algorithmDataTimeoutRef.current) {
                clearTimeout(algorithmDataTimeoutRef.current)
            }
        }
    }, [])

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

            {/* IEEE INFOCOM 2024 自動預測系統 */}
            <div className="algorithm-header">
                <div className="algorithm-title">
                    <span className="title-icon">🤖</span>
                    <span className="title-text">
                        IEEE INFOCOM 2024 自動預測算法
                    </span>
                </div>
                <div className="algorithm-subtitle">
                    二點預測 + Binary Search 優化換手決策
                </div>
            </div>

            {/* 🎯 換手策略切換控制 */}
            <div className="strategy-control-panel">
                <div className="strategy-title">
                    <span className="strategy-icon">🎯</span>
                    <span>換手策略控制</span>
                </div>
                <div className="strategy-toggle">
                    <label
                        className={
                            currentStrategy === 'flexible' ? 'active' : ''
                        }
                    >
                        <input
                            type="radio"
                            name="handover-strategy"
                            value="flexible"
                            checked={currentStrategy === 'flexible'}
                            onChange={async (e) => {
                                await globalSwitchStrategy(
                                    e.target.value as 'flexible' | 'consistent'
                                )
                            }}
                            disabled={strategyLoading}
                        />
                        <span className="strategy-label">
                            🔋 Flexible
                            <small>節能模式、長周期(5s)</small>
                        </span>
                    </label>
                    <label
                        className={
                            currentStrategy === 'consistent' ? 'active' : ''
                        }
                    >
                        <input
                            type="radio"
                            name="handover-strategy"
                            value="consistent"
                            checked={currentStrategy === 'consistent'}
                            onChange={async (e) => {
                                await globalSwitchStrategy(
                                    e.target.value as 'flexible' | 'consistent'
                                )
                            }}
                            disabled={strategyLoading}
                        />
                        <span className="strategy-label">
                            ⚡ Consistent
                            <small>效能模式、短周期(2s)</small>
                        </span>
                    </label>
                </div>
                <div className="strategy-status">
                    {strategyLoading ? (
                        <>🔄 策略切換中...</>
                    ) : (
                        <>
                            🟢 當前策略：
                            {currentStrategy === 'flexible'
                                ? 'Flexible (低資源使用)'
                                : 'Consistent (高效能模式)'}
                        </>
                    )}
                </div>
            </div>

            <div className="manager-content">
                {/* 二點預測時間軸 - 在兩種模式下都顯示 */}
                <TimePredictionTimeline
                    data={timePredictionData}
                    isActive={isEnabled}
                    onTimeUpdate={undefined} // 🔧 移除時間更新回調，避免無限循環
                    handoverRequired={realHandoverRequired} // 🎯 傳遞真實換手需求狀態
                />

                {/* 統一的狀態顯示 */}
                <div className="unified-content">
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
                </div>

                {/* 詳細演算法監控 - 可摺疊 */}
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
                                setAlgorithmRunning(
                                    results.handoverStatus === 'calculating' ||
                                        results.handoverStatus === 'executing'
                                )

                                // 如果有預測結果，更新狀態
                                if (results.predictionResult) {
                                    setAlgorithmPredictionResult(
                                        results.predictionResult
                                    )

                                    // 🎯 更新真實換手需求狀態
                                    const handoverRequired =
                                        results.predictionResult
                                            .handover_required || false
                                    setRealHandoverRequired(handoverRequired)

                                    // 🔄 更新連接狀態以同步顯示 (設置為演算法數據源)
                                    setConnectionDataSource('algorithm')

                                    // 清除之前的超時計時器
                                    if (algorithmDataTimeoutRef.current) {
                                        clearTimeout(
                                            algorithmDataTimeoutRef.current
                                        )
                                    }

                                    // 設置超時，30秒後回到模擬數據源
                                    algorithmDataTimeoutRef.current =
                                        setTimeout(() => {
                                            setConnectionDataSource(
                                                'simulation'
                                            )
                                        }, 30000)

                                    if (
                                        results.predictionResult
                                            .current_satellite
                                    ) {
                                        const currentSat =
                                            results.predictionResult
                                                .current_satellite
                                        setCurrentConnection({
                                            satelliteId:
                                                currentSat.satellite_id,
                                            satelliteName: currentSat.name,
                                            elevation: currentSat.elevation,
                                            azimuth: 0, // API 結果沒有提供，使用預設值
                                            distance: 0, // API 結果沒有提供，使用預設值
                                            signalStrength:
                                                currentSat.signal_strength,
                                            isConnected: true,
                                            isPredicted: false,
                                        })
                                    }

                                    // 如果需要換手且有預測的未來衛星，設置預測連接
                                    if (
                                        handoverRequired &&
                                        results.predictionResult
                                            .future_satellite
                                    ) {
                                        const futureSat =
                                            results.predictionResult
                                                .future_satellite
                                        setPredictedConnection({
                                            satelliteId: futureSat.satellite_id,
                                            satelliteName: futureSat.name,
                                            elevation: futureSat.elevation,
                                            azimuth: 0, // API 結果沒有提供，使用預設值
                                            distance: 0, // API 結果沒有提供，使用預設值
                                            signalStrength:
                                                futureSat.signal_strength,
                                            isConnected: false,
                                            isPredicted: true,
                                        })
                                    } else {
                                        // 如果不需要換手，清空預測連接
                                        setPredictedConnection(null)
                                    }

                                    // 🔧 只在必要時更新 currentDeltaT，避免干擾時間軸
                                    const now = Date.now()
                                    const timelineFinished =
                                        now >=
                                        timePredictionDataRef.current.futureTime
                                    const newDeltaT =
                                        results.predictionResult
                                            .delta_t_seconds || 5

                                    // console.log(`🔄 SynchronizedAlgorithmVisualization 結果: newDeltaT=${newDeltaT}s, timelineFinished=${timelineFinished}, currentDeltaT=${currentDeltaT}s`)

                                    // 只在時間軸完成且 deltaT 真的改變時才更新
                                    if (
                                        timelineFinished &&
                                        Math.abs(newDeltaT - currentDeltaT) >
                                            0.1
                                    ) {
                                        // console.log(`✅ 更新 currentDeltaT: ${currentDeltaT}s → ${newDeltaT}s`)
                                        setCurrentDeltaT(newDeltaT)
                                    }
                                }

                                onAlgorithmResults?.(results)
                            }}
                        />
                    </div>
                </details>

                {/* 移除重複的後台組件 - 統一使用可見的組件 */}
            </div>
        </div>
    )
}

export default HandoverManager
