/**
 * Event D2 Viewer Component
 * 提供完整的 Event D2 移動參考位置測量事件查看功能
 * 包含參數控制和 3GPP TS 38.331 規範實現
 * 基於 EventD1Viewer.tsx 修改以支援移動參考位置
 * 樣式完全參考 A4/D1 的設計模式
 */

import React, { useState, useMemo, useCallback } from 'react'
import PureD2Chart from './PureD2Chart'
import type { EventD2Params } from '../types'
import './EventA4Viewer.scss' // 完全重用 A4 的樣式，確保左側控制面板風格一致
import './NarrationPanel.scss' // 動畫解說面板樣式

interface EventD2ViewerProps {
    isDarkTheme?: boolean
    onThemeToggle?: () => void
    initialParams?: Partial<EventD2Params>
    // 新增：支援 Modal 模式的屬性
    onReportLastUpdateToNavbar?: (timestamp: number) => void
    reportRefreshHandlerToNavbar?: React.MutableRefObject<(() => void) | null>
    reportIsLoadingToNavbar?: (loading: boolean) => void
    currentScene?: string
}

export const EventD2Viewer: React.FC<EventD2ViewerProps> = React.memo(
    ({ isDarkTheme = true, onThemeToggle, initialParams = {} }) => {
        // Event D2 參數狀態 - 基於 3GPP TS 38.331 規範
        const [params, setParams] = useState<EventD2Params>(() => ({
            Thresh1: initialParams.Thresh1 ?? 550000, // meters (距離門檻1 - 移動參考位置，衛星距離)
            Thresh2: initialParams.Thresh2 ?? 6000, // meters (距離門檻2 - 固定參考位置)
            Hys: initialParams.Hys ?? 20, // meters (hysteresisLocation)
            timeToTrigger: initialParams.timeToTrigger ?? 320, // ms
            reportAmount: initialParams.reportAmount ?? 3,
            reportInterval: initialParams.reportInterval ?? 1000, // ms
            reportOnLeave: initialParams.reportOnLeave ?? true,
            movingReferenceLocation: initialParams.movingReferenceLocation ?? {
                lat: 25.0478,
                lon: 121.5319,
            }, // 移動參考位置（衛星初始位置）
            referenceLocation: initialParams.referenceLocation ?? {
                lat: 25.0173,
                lon: 121.4695,
            }, // 固定參考位置（中正紀念堂）
        }))

        const [showThresholdLines, setShowThresholdLines] = useState(true)
        const [animationState, setAnimationState] = useState({
            isPlaying: false,
            currentTime: 0,
            speed: 1,
        })

        // 動畫解說系統狀態
        const [showNarration, setShowNarration] = useState(true)
        const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)
        const [isNarrationExpanded, setIsNarrationExpanded] = useState(false)

        // 穩定的參數更新回調
        const updateParam = useCallback(
            (key: keyof EventD2Params, value: unknown) => {
                setParams((prev) => ({
                    ...prev,
                    [key]: value,
                }))
            },
            []
        )

        // 穩定的動畫控制回調
        const toggleAnimation = useCallback(() => {
            setAnimationState((prev) => ({
                ...prev,
                isPlaying: !prev.isPlaying,
            }))
        }, [])

        const resetAnimation = useCallback(() => {
            setAnimationState((prev) => ({
                ...prev,
                isPlaying: false,
                currentTime: 0,
            }))
        }, [])

        // 動畫進度更新
        React.useEffect(() => {
            if (!animationState.isPlaying) return

            const interval = setInterval(() => {
                setAnimationState((prev) => {
                    const newTime = prev.currentTime + 0.1 * prev.speed // 0.1 second steps
                    const maxTime = 95 // 95 seconds max for D2 (matching chart X-axis)
                    if (newTime >= maxTime) {
                        return { ...prev, isPlaying: false, currentTime: 0 }
                    }
                    return { ...prev, currentTime: newTime }
                })
            }, 100) // Update every 100ms (0.1 second)

            return () => clearInterval(interval)
        }, [animationState.isPlaying, animationState.speed])

        // 穩定的閾值線切換回調
        const toggleThresholdLines = useCallback(() => {
            setShowThresholdLines((prev) => !prev)
        }, [])

        // 計算衛星位置（模擬移動參考位置）
        const calculateSatellitePosition = useCallback(
            (timeSeconds: number) => {
                const centerLat = params.movingReferenceLocation.lat
                const centerLon = params.movingReferenceLocation.lon
                const orbitRadius = 0.01 // 軌道半徑（度）
                const orbitPeriod = 120 // 軌道週期（秒）

                const angle = (timeSeconds / orbitPeriod) * 2 * Math.PI

                return {
                    lat: centerLat + orbitRadius * Math.cos(angle),
                    lon: centerLon + orbitRadius * Math.sin(angle),
                    altitude: 550000, // LEO 衛星高度
                    velocity: 7.5, // km/s
                }
            },
            [params.movingReferenceLocation]
        )

        // 動畫解說內容生成 - 基於衛星軌道和 LEO 星座切換策略
        const narrationContent = useMemo(() => {
            const currentTime = animationState.currentTime
            const satellitePosition = calculateSatellitePosition(currentTime)

            // 模擬 UE 位置
            const _uePosition = { lat: 25.048, lon: 121.528 }

            // 計算軌道參數
            const orbitalVelocity = 7.5 // km/s for LEO at 550km
            const _orbitalPeriod = 5570 // seconds for real LEO orbit
            const groundTrackSpeed = orbitalVelocity * Math.cos(Math.PI / 180 * 53) // 軌道傾角53度

            // 模擬距離值（實際應用中會基於真實地理計算）
            let simulatedDistance1, simulatedDistance2

            // 在特定時間段模擬事件觸發條件
            if (currentTime >= 20 && currentTime <= 80) {
                // 觸發區間：距離1 > Thresh1, 距離2 < Thresh2
                simulatedDistance1 = 552000 // meters - 超過 Thresh1 (550km)
                simulatedDistance2 = 5500 // meters - 低於 Thresh2 (6km)
            } else if (currentTime < 20) {
                // 觸發前：距離1 < Thresh1, 距離2 > Thresh2
                simulatedDistance1 = 548000 // meters - 低於 Thresh1
                simulatedDistance2 = 6500 // meters - 高於 Thresh2
            } else {
                // 觸發後：條件不滿足
                simulatedDistance1 = 547000 // meters - 低於 Thresh1
                simulatedDistance2 = 6800 // meters - 高於 Thresh2
            }

            // 判斷當前階段和 LEO 星座切換策略
            let phase = 'monitoring'
            let phaseTitle = ''
            let description = ''
            let technicalNote = ''
            let nextAction = ''
            let constellationStrategy = ''
            let handoverScenario = ''

            const condition1 = simulatedDistance1 - params.Hys > params.Thresh1
            const condition2 = simulatedDistance2 + params.Hys < params.Thresh2
            const eventTriggered = condition1 && condition2

            if (eventTriggered) {
                phase = 'triggered'
                phaseTitle = '🛰️ Event D2 已觸發 - LEO 星座切換決策啟動'
                description = `衛星距離 (${(simulatedDistance1 / 1000).toFixed(1)} km) 超過門檻1，同時固定參考點距離 (${(simulatedDistance2 / 1000).toFixed(1)} km) 低於門檻2。LEO 星座系統正在執行智能切換決策。`
                
                // LEO 星座切換策略說明
                constellationStrategy = '🌌 LEO 星座切換策略：多衛星協調切換'
                handoverScenario = `實際星座切換場景：當前服務衛星即將離開最佳服務區域，系統啟動：
• 🔍 候選衛星搜尋：掃描同軌道面和相鄰軌道面的可用衛星
• 📊 鏈路品質評估：比較候選衛星的仰角、RSRP、干擾水平
• ⚡ 預測性切換：基於軌道預測，提前2-3分鐘準備切換
• 🔄 無縫切換執行：使用 make-before-break 策略確保服務連續性
• 🛡️ 負載平衡：考慮目標衛星的用戶負載和資源可用性
• 📡 波束管理：協調衛星波束指向和功率分配優化`
                
                technicalNote = `3GPP 條件: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2\\n衛星距離: ${(simulatedDistance1 / 1000).toFixed(1)} - ${params.Hys / 1000} = ${((simulatedDistance1 - params.Hys) / 1000).toFixed(1)} > ${(params.Thresh1 / 1000).toFixed(1)} km\\n固定距離: ${(simulatedDistance2 / 1000).toFixed(1)} + ${params.Hys / 1000} = ${((simulatedDistance2 + params.Hys) / 1000).toFixed(1)} < ${(params.Thresh2 / 1000).toFixed(1)} km\\n\\nLEO 星座參數：\\n• 軌道高度：${satellitePosition.altitude / 1000} km\\n• 軌道速度：${orbitalVelocity} km/s\\n• 地面軌跡速度：${groundTrackSpeed.toFixed(1)} km/s\\n• 可見時間窗口：8-12 分鐘\\n• 切換決策時延：${params.timeToTrigger} ms`
                nextAction = '執行多衛星協調切換，確保服務連續性和最佳QoS'
            } else if (condition1 && !condition2) {
                phase = 'partial'
                phaseTitle = '⚠️ 星座監控中 - 準備切換候選衛星'
                description = `衛星距離條件已滿足 (${(simulatedDistance1 / 1000).toFixed(1)} km > ${(params.Thresh1 / 1000).toFixed(1)} km)，但固定參考點距離 (${(simulatedDistance2 / 1000).toFixed(1)} km) 仍高於門檻。`
                constellationStrategy = '👁️ 星座狀態：候選衛星識別階段'
                handoverScenario = `準備階段切換策略：當前衛星開始遠離最佳位置，系統準備：
• 🔭 軌道預測：計算未來5-10分鐘內所有可見衛星的軌跡
• 📈 性能建模：預測每顆候選衛星的服務品質變化趨勢
• 🎯 最佳時機計算：確定最佳切換時間點以最小化服務中斷
• 📋 資源預留：在候選衛星上預留必要的網路資源
• 🔧 設備準備：調整天線指向和功率設定準備新連接`
                technicalNote = `條件1: ✅ Ml1 - Hys = ${((simulatedDistance1 - params.Hys) / 1000).toFixed(1)} > ${(params.Thresh1 / 1000).toFixed(1)}\\n條件2: ❌ Ml2 + Hys = ${((simulatedDistance2 + params.Hys) / 1000).toFixed(1)} ≮ ${(params.Thresh2 / 1000).toFixed(1)}\\n\\n候選衛星評估：\\n• 仰角門檻：> 15度\\n• 預期服務時間：> 8分鐘\\n• 負載容量：< 80%\\n• 切換延遲：< 50ms`
                nextAction = '繼續監控並準備候選衛星資源，等待最佳切換時機'
            } else if (!condition1 && condition2) {
                phase = 'partial'
                phaseTitle = '⚠️ 星座監控中 - 當前衛星服務中'
                description = `固定參考點距離條件已滿足 (${(simulatedDistance2 / 1000).toFixed(1)} km < ${(params.Thresh2 / 1000).toFixed(1)} km)，但衛星距離 (${(simulatedDistance1 / 1000).toFixed(1)} km) 仍在最佳服務範圍內。`
                constellationStrategy = '⭐ 星座狀態：最佳服務階段'
                handoverScenario = `服務維持階段策略：當前衛星在最佳位置，系統執行：
• 🎯 服務優化：動態調整波束形成和功率分配
• 📊 性能監控：持續監測信號品質和用戶體驗指標
• 🔮 軌道追蹤：實時追蹤衛星位置和預測未來軌跡
• 🚀 預備切換：提前識別下一個服務窗口的候選衛星
• 🔄 負載均衡：在多個可見衛星間動態分配用戶負載`
                technicalNote = `條件1: ❌ Ml1 - Hys = ${((simulatedDistance1 - params.Hys) / 1000).toFixed(1)} ≯ ${(params.Thresh1 / 1000).toFixed(1)}\\n條件2: ✅ Ml2 + Hys = ${((simulatedDistance2 + params.Hys) / 1000).toFixed(1)} < ${(params.Thresh2 / 1000).toFixed(1)}\\n\\n最佳服務參數：\\n• 當前仰角：45-70度\\n• 傳播延遲：< 5ms\\n• 都卜勒頻移補償：±3 kHz\\n• 預期服務剩餘時間：${(70 - currentTime).toFixed(0)}秒`
                nextAction = '維持最佳服務品質，準備未來切換規劃'
            } else {
                phaseTitle = '🔍 LEO 星座正常監控階段'
                description = `雙重距離條件均未滿足。衛星距離 (${(simulatedDistance1 / 1000).toFixed(1)} km) 和固定參考點距離 (${(simulatedDistance2 / 1000).toFixed(1)} km) 均在正常範圍內。`
                constellationStrategy = '🌐 星座狀態：連續覆蓋保障'
                handoverScenario = `標準監控模式：多衛星星座提供連續覆蓋，系統執行：
• 🛰️ 星座追蹤：實時追蹤所有可見LEO衛星的位置和狀態
• 📡 信號監測：監控多個衛星的信號強度和品質參數
• 🧭 軌道預測：使用TLE數據預測未來24小時的衛星可見性
• 🔄 自動切換：基於預設規則執行自動衛星切換
• 📊 性能分析：收集並分析星座覆蓋性能和用戶體驗數據
• 🛡️ 容錯機制：監控衛星健康狀態，準備故障切換方案`
                technicalNote = `衛星距離: ${(simulatedDistance1 / 1000).toFixed(1)} km, 固定距離: ${(simulatedDistance2 / 1000).toFixed(1)} km\\n\\nLEO 星座監控重點：\\n• 多衛星可見性分析\\n• 信號品質趨勢預測\\n• 軌道機動影響評估\\n• 星座完整性驗證\\n• 切換演算法性能優化\\n• 用戶移動性適應`
                nextAction = '持續星座監控，優化切換演算法和服務品質'
            }

            // 根據時間添加詳細的 LEO 軌道情境解說
            let scenarioContext = ''
            let orbitalScenario = ''
            if (currentTime < 30) {
                scenarioContext = '🚀 場景：LEO衛星從地平線升起，開始進入服務範圍'
                orbitalScenario = `軌道動力學：衛星以 ${orbitalVelocity} km/s 的速度快速接近，仰角從5度快速增加到30度`
            } else if (currentTime < 70) {
                scenarioContext = '🌍 場景：衛星接近天頂，處於最佳服務位置'
                orbitalScenario = `軌道動力學：衛星在40-70度仰角範圍內，提供最低延遲和最強信號品質`
            } else {
                scenarioContext = '🏠 場景：衛星向地平線下降，準備離開服務範圍'
                orbitalScenario = `軌道動力學：衛星仰角降至15度以下，系統準備切換到下一顆衛星`
            }

            return {
                phase,
                phaseTitle,
                description,
                technicalNote,
                nextAction,
                scenarioContext,
                orbitalScenario,
                constellationStrategy,
                handoverScenario,
                satelliteDistance: (simulatedDistance1 / 1000).toFixed(1),
                fixedDistance: (simulatedDistance2 / 1000).toFixed(1),
                timeProgress: `${currentTime.toFixed(1)}s / 95s`,
                satelliteLat: satellitePosition.lat.toFixed(4),
                satelliteLon: satellitePosition.lon.toFixed(4),
                orbitalVelocity: `${orbitalVelocity} km/s`,
                groundTrack: `${groundTrackSpeed.toFixed(1)} km/s`,
            }
        }, [
            animationState.currentTime,
            params.Thresh1,
            params.Thresh2,
            params.Hys,
            params.timeToTrigger,
            calculateSatellitePosition,
        ])

        // 計算 Event D2 條件狀態 - 基於 3GPP TS 38.331 規範
        const eventStatus = useMemo(() => {
            // 根據當前時間計算條件
            const currentTime = animationState.currentTime || 45 // 預設時間

            // 模擬 UE 位置
            const _uePosition = { lat: 25.048, lon: 121.528 }

            // 計算移動參考位置（衛星當前位置）
            const satellitePosition = calculateSatellitePosition(currentTime)

            // 模擬距離值（實際應用中會基於真實地理計算）
            let simulatedDistance1, simulatedDistance2

            // 在特定時間段模擬事件觸發條件
            if (currentTime >= 20 && currentTime <= 80) {
                // 觸發區間：距離1 > Thresh1, 距離2 < Thresh2
                simulatedDistance1 = 552000 // meters - 超過 Thresh1 (550km)
                simulatedDistance2 = 5500 // meters - 低於 Thresh2 (6km)
            } else if (currentTime < 20) {
                // 觸發前：距離1 < Thresh1, 距離2 > Thresh2
                simulatedDistance1 = 548000 // meters - 低於 Thresh1
                simulatedDistance2 = 6500 // meters - 高於 Thresh2
            } else {
                // 觸發後：條件不滿足
                simulatedDistance1 = 547000 // meters - 低於 Thresh1
                simulatedDistance2 = 6800 // meters - 高於 Thresh2
            }

            // D2-1 進入條件: Ml1 - Hys > Thresh1 (移動參考位置)
            const condition1 = simulatedDistance1 - params.Hys > params.Thresh1
            // D2-2 進入條件: Ml2 + Hys < Thresh2 (固定參考位置)
            const condition2 = simulatedDistance2 + params.Hys < params.Thresh2
            // 事件觸發需要兩個條件同時滿足
            const eventTriggered = condition1 && condition2

            return {
                condition1, // D2-1 進入條件
                condition2, // D2-2 進入條件
                eventTriggered,
                description: eventTriggered
                    ? 'D2 事件已觸發 (20-80s)'
                    : '等待條件滿足',
                currentDistance1: simulatedDistance1, // UE 到移動參考位置
                currentDistance2: simulatedDistance2, // UE 到固定參考位置
                triggerTimeRange: '20-80秒',
                satellitePosition, // 當前衛星位置
            }
        }, [params, animationState.currentTime, calculateSatellitePosition])

        return (
            <div className="event-a4-viewer">
                <div className="event-viewer__content">
                    {/* 控制面板 */}
                    <div className="event-viewer__controls">
                        <div className="control-panel">
                            {/* 動畫控制 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🎬 動畫控制
                                </h3>
                                <div className="control-group control-group--buttons">
                                    <button
                                        className={`control-btn ${
                                            animationState.isPlaying
                                                ? 'control-btn--pause'
                                                : 'control-btn--play'
                                        }`}
                                        onClick={toggleAnimation}
                                    >
                                        {animationState.isPlaying
                                            ? '⏸️ 暫停'
                                            : '▶️ 播放'}
                                    </button>
                                    <button
                                        className="control-btn control-btn--reset"
                                        onClick={resetAnimation}
                                    >
                                        🔄 重置
                                    </button>
                                    <button
                                        className={`control-btn ${
                                            showThresholdLines
                                                ? 'control-btn--active'
                                                : ''
                                        }`}
                                        onClick={toggleThresholdLines}
                                    >
                                        📏 門檻線
                                    </button>
                                </div>

                                {/* 解說系統控制 */}
                                <div className="control-group control-group--buttons">
                                    <button
                                        className={`control-btn ${
                                            showNarration
                                                ? 'control-btn--active'
                                                : ''
                                        }`}
                                        onClick={() =>
                                            setShowNarration(!showNarration)
                                        }
                                    >
                                        💬 動畫解說
                                    </button>
                                    <button
                                        className={`control-btn ${
                                            showTechnicalDetails
                                                ? 'control-btn--active'
                                                : ''
                                        }`}
                                        onClick={() =>
                                            setShowTechnicalDetails(
                                                !showTechnicalDetails
                                            )
                                        }
                                    >
                                        🔍 技術細節
                                    </button>
                                </div>

                                {/* 時間遊標控制 */}
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            當前時間 (動畫時間)
                                            <span className="control-unit">
                                                秒
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="95"
                                            step="0.1"
                                            value={animationState.currentTime}
                                            onChange={(e) =>
                                                setAnimationState((prev) => ({
                                                    ...prev,
                                                    currentTime: Number(
                                                        e.target.value
                                                    ),
                                                }))
                                            }
                                            className="control-slider"
                                        />
                                        <span className="control-value">
                                            {animationState.currentTime.toFixed(
                                                1
                                            )}
                                            s
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Event D2 距離門檻參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🎯 D2 距離門檻
                                </h3>
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            distanceThreshFromReference1
                                            (movingReferenceLocation)
                                            <span className="control-unit">
                                                公尺 (衛星距離)
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="540000"
                                            max="560000"
                                            step="1000"
                                            value={params.Thresh1}
                                            onChange={(e) =>
                                                updateParam(
                                                    'Thresh1',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-slider"
                                        />
                                        <span className="control-value">
                                            {(params.Thresh1 / 1000).toFixed(1)}
                                            km
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            distanceThreshFromReference2
                                            (referenceLocation)
                                            <span className="control-unit">
                                                公尺 (固定參考位置)
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="3000"
                                            max="10000"
                                            step="100"
                                            value={params.Thresh2}
                                            onChange={(e) =>
                                                updateParam(
                                                    'Thresh2',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-slider"
                                        />
                                        <span className="control-value">
                                            {(params.Thresh2 / 1000).toFixed(1)}
                                            km
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            hysteresisLocation (位置遲滯)
                                            <span className="control-unit">
                                                公尺
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="5"
                                            max="50"
                                            step="5"
                                            value={params.Hys}
                                            onChange={(e) =>
                                                updateParam(
                                                    'Hys',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-slider"
                                        />
                                        <span className="control-value">
                                            {params.Hys}m
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* 時間參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    ⏱️ 時間參數
                                </h3>
                                <div className="control-group">
                                    <div className="control-item control-item--horizontal">
                                        <span className="control-label">
                                            TimeToTrigger
                                        </span>
                                        <select
                                            value={params.timeToTrigger}
                                            onChange={(e) =>
                                                updateParam(
                                                    'timeToTrigger',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-select"
                                        >
                                            <option value={0}>0</option>
                                            <option value={40}>40</option>
                                            <option value={64}>64</option>
                                            <option value={80}>80</option>
                                            <option value={100}>100</option>
                                            <option value={128}>128</option>
                                            <option value={160}>160</option>
                                            <option value={256}>256</option>
                                            <option value={320}>320</option>
                                            <option value={480}>480</option>
                                            <option value={512}>512</option>
                                            <option value={640}>640</option>
                                        </select>
                                        <span className="control-unit">
                                            毫秒
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* 報告參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📊 報告參數
                                </h3>
                                <div className="control-group">
                                    <div className="control-item control-item--horizontal">
                                        <span className="control-label">
                                            Report Amount
                                        </span>
                                        <select
                                            value={params.reportAmount}
                                            onChange={(e) =>
                                                updateParam(
                                                    'reportAmount',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-select"
                                        >
                                            <option value={1}>1</option>
                                            <option value={2}>2</option>
                                            <option value={4}>4</option>
                                            <option value={8}>8</option>
                                            <option value={16}>16</option>
                                            <option value={32}>32</option>
                                            <option value={64}>64</option>
                                            <option value={-1}>無限制</option>
                                        </select>
                                        <span className="control-unit">
                                            次數
                                        </span>
                                    </div>
                                    <div className="control-item control-item--horizontal">
                                        <span className="control-label">
                                            Report Interval
                                        </span>
                                        <select
                                            value={params.reportInterval}
                                            onChange={(e) =>
                                                updateParam(
                                                    'reportInterval',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-select"
                                        >
                                            <option value={120}>120</option>
                                            <option value={240}>240</option>
                                            <option value={480}>480</option>
                                            <option value={640}>640</option>
                                            <option value={1024}>1024</option>
                                            <option value={2048}>2048</option>
                                            <option value={5120}>5120</option>
                                            <option value={10240}>10240</option>
                                        </select>
                                        <span className="control-unit">
                                            毫秒
                                        </span>
                                    </div>
                                    <div className="control-item control-item--horizontal">
                                        <span className="control-label">
                                            離開時報告
                                        </span>
                                        <label className="control-checkbox">
                                            <input
                                                type="checkbox"
                                                checked={params.reportOnLeave}
                                                onChange={(e) =>
                                                    updateParam(
                                                        'reportOnLeave',
                                                        e.target.checked
                                                    )
                                                }
                                            />
                                            Report On Leave
                                        </label>
                                    </div>
                                </div>
                            </div>

                            {/* Event D2 狀態 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📡 D2 事件狀態
                                </h3>
                                <div className="event-status">
                                    <div className="status-item">
                                        <span className="status-label">
                                            進入條件 D2-1 (移動參考位置):
                                        </span>
                                        <span
                                            className={`status-value ${
                                                eventStatus.condition1
                                                    ? 'status-value--active'
                                                    : ''
                                            }`}
                                        >
                                            Ml1 - Hys &gt; Thresh1
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            進入條件 D2-2 (固定參考位置):
                                        </span>
                                        <span
                                            className={`status-value ${
                                                eventStatus.condition2
                                                    ? 'status-value--active'
                                                    : ''
                                            }`}
                                        >
                                            Ml2 + Hys &lt; Thresh2
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            事件狀態:
                                        </span>
                                        <span
                                            className={`status-badge ${
                                                eventStatus.eventTriggered
                                                    ? 'status-badge--triggered'
                                                    : 'status-badge--waiting'
                                            }`}
                                        >
                                            {eventStatus.eventTriggered
                                                ? '✅ 已觸發'
                                                : '⏳ 等待中'}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            距離1 (Ml1):
                                        </span>
                                        <span className="status-value">
                                            {(
                                                eventStatus.currentDistance1 /
                                                1000
                                            ).toFixed(1)}
                                            km
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            距離2 (Ml2):
                                        </span>
                                        <span className="status-value">
                                            {(
                                                eventStatus.currentDistance2 /
                                                1000
                                            ).toFixed(1)}
                                            km
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            觸發時間範圍:
                                        </span>
                                        <span
                                            className={`status-value ${
                                                eventStatus.eventTriggered
                                                    ? 'status-value--active'
                                                    : ''
                                            }`}
                                        >
                                            {eventStatus.triggerTimeRange}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Event D2 特有參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📡 D2 移動參考位置參數
                                </h3>
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            movingReferenceLocation
                                            <span className="control-unit">
                                                (衛星初始位置)
                                            </span>
                                        </label>
                                        <div className="location-coords">
                                            {params.movingReferenceLocation.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {params.movingReferenceLocation.lon.toFixed(
                                                4
                                            )}
                                        </div>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            referenceLocation
                                            <span className="control-unit">
                                                (固定參考位置)
                                            </span>
                                        </label>
                                        <div className="location-coords">
                                            {params.referenceLocation.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {params.referenceLocation.lon.toFixed(
                                                4
                                            )}
                                        </div>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            satelliteEphemeris
                                            <span className="control-unit">
                                                (SIB19廣播)
                                            </span>
                                        </label>
                                        <select
                                            className="control-select"
                                            disabled
                                        >
                                            <option>LEO-550km-Circular</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* 衛星軌道參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🛰️ 衛星軌道參數
                                </h3>
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            軌道半徑
                                            <span className="control-unit">
                                                度
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0.005"
                                            max="0.02"
                                            step="0.001"
                                            value={0.01}
                                            className="control-slider"
                                            readOnly
                                        />
                                        <span className="control-value">
                                            0.01°
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            軌道週期
                                            <span className="control-unit">
                                                秒
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="60"
                                            max="300"
                                            step="10"
                                            value={120}
                                            className="control-slider"
                                            readOnly
                                        />
                                        <span className="control-value">
                                            120s
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            軌道類型
                                        </label>
                                        <select
                                            className="control-select"
                                            disabled
                                        >
                                            <option value="circular">
                                                圓形軌道
                                            </option>
                                            <option value="elliptical">
                                                橢圓軌道
                                            </option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* 衛星軌道信息 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🛰️ 衛星軌道信息
                                </h3>
                                <div className="location-info">
                                    <div className="location-item">
                                        <span className="location-label">
                                            當前衛星位置:
                                        </span>
                                        <span className="location-coords">
                                            {eventStatus.satellitePosition.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {eventStatus.satellitePosition.lon.toFixed(
                                                4
                                            )}
                                        </span>
                                    </div>
                                    <div className="location-item">
                                        <span className="location-label">
                                            軌道週期:
                                        </span>
                                        <span className="location-coords">
                                            120秒
                                        </span>
                                    </div>
                                    <div className="location-item">
                                        <span className="location-label">
                                            固定參考點:
                                        </span>
                                        <span className="location-coords">
                                            {params.referenceLocation.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {params.referenceLocation.lon.toFixed(
                                                4
                                            )}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 圖表區域 */}
                    <div className="event-viewer__chart-container">
                        <div className="chart-area">
                            {/* 動畫解說面板 */}
                            {showNarration && (
                                <div
                                    className={`narration-panel ${
                                        isNarrationExpanded
                                            ? 'expanded'
                                            : 'compact'
                                    }`}
                                >
                                    <div className="narration-header">
                                        <h3 className="narration-title">
                                            {narrationContent.phaseTitle}
                                        </h3>
                                        <div className="narration-controls">
                                            <div className="narration-time">
                                                🕰{' '}
                                                {narrationContent.timeProgress}
                                            </div>
                                            <button
                                                className="narration-toggle"
                                                onClick={() =>
                                                    setIsNarrationExpanded(
                                                        !isNarrationExpanded
                                                    )
                                                }
                                                title={
                                                    isNarrationExpanded
                                                        ? '收起詳細說明'
                                                        : '展開詳細說明'
                                                }
                                            >
                                                {isNarrationExpanded
                                                    ? '▲'
                                                    : '▼'}
                                            </button>
                                        </div>
                                    </div>

                                    {isNarrationExpanded && (
                                        <div className="narration-content">
                                            <div className="narration-scenario">
                                                {narrationContent.scenarioContext}
                                                <div className="mobility-scenario">
                                                    {narrationContent.orbitalScenario}
                                                </div>
                                            </div>

                                            <div className="constellation-strategy-stage">
                                                <h4>{narrationContent.constellationStrategy}</h4>
                                                <div className="constellation-handover">
                                                    {narrationContent.handoverScenario.split('\\n').map((line, index) => (
                                                        <div key={index} className="handover-line">
                                                            {line}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="narration-description">
                                                {narrationContent.description}
                                            </div>

                                            {showTechnicalDetails && (
                                                <div className="narration-technical">
                                                    <h4>🔧 技術細節：</h4>
                                                    <div className="technical-formula">
                                                        {narrationContent.technicalNote
                                                            .split('\\n')
                                                            .map(
                                                                (
                                                                    line,
                                                                    index
                                                                ) => (
                                                                    <div
                                                                        key={
                                                                            index
                                                                        }
                                                                    >
                                                                        {line}
                                                                    </div>
                                                                )
                                                            )}
                                                    </div>
                                                </div>
                                            )}

                                            <div className="narration-next">
                                                <strong>下一步：</strong>{' '}
                                                {narrationContent.nextAction}
                                            </div>
                                        </div>
                                    )}

                                    <div className="narration-metrics">
                                        <div className="metric">
                                            <span className="metric-label">
                                                衛星距離：
                                            </span>
                                            <span className="metric-value">
                                                {
                                                    narrationContent.satelliteDistance
                                                }{' '}
                                                km
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="metric-label">
                                                固定距離：
                                            </span>
                                            <span className="metric-value">
                                                {narrationContent.fixedDistance}{' '}
                                                km
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="metric-label">
                                                衛星位置：
                                            </span>
                                            <span className="metric-value">
                                                {narrationContent.satelliteLat},{' '}
                                                {narrationContent.satelliteLon}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className="chart-container">
                                <PureD2Chart
                                    thresh1={params.Thresh1}
                                    thresh2={params.Thresh2}
                                    hysteresis={params.Hys}
                                    currentTime={animationState.currentTime}
                                    showThresholdLines={showThresholdLines}
                                    isDarkTheme={isDarkTheme}
                                    onThemeToggle={onThemeToggle}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* 3GPP 規範說明 */}
                <div className="event-viewer__specification">
                    <h3 className="spec-title">📖 3GPP TS 38.331 規範</h3>
                    <div className="spec-content">
                        <div className="spec-section">
                            <h4>Event D2 條件：</h4>
                            <ul>
                                <li>
                                    <strong>進入條件：</strong> 
                                    <br/>條件1: Ml1 - Hys &gt; Thresh1 (移動參考位置距離)
                                    <br/>條件2: Ml2 + Hys &lt; Thresh2 (固定參考位置距離)
                                    <br/><em>同時滿足: 條件1 <strong>且</strong> 條件2</em>
                                </li>
                                <li>
                                    <strong>離開條件：</strong> 
                                    <br/>條件1: Ml1 + Hys &lt; Thresh1 (接近移動參考位置)
                                    <br/>條件2: Ml2 - Hys &gt; Thresh2 (遠離固定參考位置)
                                    <br/><em>任一滿足: 條件1 <strong>或</strong> 條件2</em>
                                </li>
                                <li>
                                    <strong>TimeToTrigger：</strong>
                                    條件滿足後需持續的時間長度
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>參數說明：</h4>
                            <ul>
                                <li>
                                    <strong>Ml1：</strong>UE 與移動參考位置（衛星）的距離（公尺）
                                    <br/><em>動態變化，反映 LEO 衛星軌道運動</em>
                                </li>
                                <li>
                                    <strong>Ml2：</strong>UE 與固定參考位置的距離（公尺）
                                    <br/><em>相對穩定，基於地面固定參考點</em>
                                </li>
                                <li>
                                    <strong>Thresh1：</strong>移動參考位置距離門檻值（公尺）
                                    <br/><em>distanceThreshFromReference1，通常設置較大值（如 550km）</em>
                                </li>
                                <li>
                                    <strong>Thresh2：</strong>固定參考位置距離門檻值（公尺）
                                    <br/><em>distanceThreshFromReference2，通常設置較小值（如 6km）</em>
                                </li>
                                <li>
                                    <strong>Hys：</strong>hysteresisLocation 遲滯參數（公尺）
                                    <br/><em>防止事件頻繁觸發，提供穩定性緩衝</em>
                                </li>
                                <li>
                                    <strong>movingReferenceLocation：</strong>移動參考位置坐標（衛星初始位置）
                                    <br/><em>配合衛星軌道預測模型進行動態更新</em>
                                </li>
                                <li>
                                    <strong>referenceLocation：</strong>固定參考位置坐標（地面參考點）
                                    <br/><em>提供穩定的地理基準，通常為重要地標</em>
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>應用場景：</h4>
                            <ul>
                                <li>
                                    <strong>衛星通信：</strong>
                                    基於衛星軌道運動的動態距離管理
                                </li>
                                <li>
                                    <strong>移動基站：</strong>
                                    當服務小區位置發生移動時的事件觸發
                                </li>
                                <li>
                                    <strong>LEO 衛星星座：</strong>
                                    低軌道衛星快速移動場景下的資源調度
                                </li>
                                <li>
                                    <strong>位置感知服務：</strong>
                                    結合固定和移動參考點的複合位置服務
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
)

EventD2Viewer.displayName = 'EventD2Viewer'

export default EventD2Viewer
