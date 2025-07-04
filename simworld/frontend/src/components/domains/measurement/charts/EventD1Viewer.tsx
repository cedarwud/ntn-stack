/**
 * Event D1 Viewer Component
 * 提供完整的 Event D1 測量事件查看功能
 * 包含參數控制和 3GPP TS 38.331 規範實現
 */

import React, { useState, useMemo, useCallback } from 'react'
import PureD1Chart from './PureD1Chart'
import type { EventD1Params } from '../types'
import './EventA4Viewer.scss' // 重用 A4 的樣式
import './NarrationPanel.scss' // 動畫解說面板樣式

interface EventD1ViewerProps {
    isDarkTheme?: boolean
    onThemeToggle?: () => void
    initialParams?: Partial<EventD1Params>
}

export const EventD1Viewer: React.FC<EventD1ViewerProps> = React.memo(
    ({ isDarkTheme = true, onThemeToggle, initialParams = {} }) => {
        // Event D1 參數狀態 - 基於 3GPP TS 38.331 規範
        const [params, setParams] = useState<EventD1Params>(() => ({
            Thresh1: initialParams.Thresh1 ?? 400, // meters (distanceThreshFromReference1)
            Thresh2: initialParams.Thresh2 ?? 250, // meters (distanceThreshFromReference2)
            Hys: initialParams.Hys ?? 20, // meters (hysteresisLocation)
            timeToTrigger: initialParams.timeToTrigger ?? 320, // ms
            reportAmount: initialParams.reportAmount ?? 3,
            reportInterval: initialParams.reportInterval ?? 1000, // ms
            reportOnLeave: initialParams.reportOnLeave ?? true,
            referenceLocation1: initialParams.referenceLocation1 ?? {
                lat: 25.0478,
                lon: 121.5319,
            }, // 台北101 (referenceLocation1)
            referenceLocation2: initialParams.referenceLocation2 ?? {
                lat: 25.0173,
                lon: 121.4695,
            }, // 中正紀念堂 (referenceLocation2)
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
            (key: keyof EventD1Params, value: unknown) => {
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
                    const maxTime = 100 // 100 seconds max for D1 (matching chart X-axis)
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

        // 計算 Event D1 條件狀態 - 基於 3GPP TS 38.331 規範
        const eventStatus = useMemo(() => {
            // 根據當前時間模擬 UE 與參考位置的距離測量值
            // 在 30-70s 時間段內，兩個條件同時滿足觸發 Event D1
            const currentTime = animationState.currentTime || 45 // 預設在觸發區間內

            let simulatedDistance1, simulatedDistance2

            if (currentTime >= 30 && currentTime <= 70) {
                // 觸發區間：距離1 > Thresh1, 距離2 < Thresh2
                simulatedDistance1 = 480 // meters - 超過 Thresh1 (400m)
                simulatedDistance2 = 200 // meters - 低於 Thresh2 (250m)
            } else if (currentTime < 30) {
                // 觸發前：距離1 < Thresh1, 距離2 > Thresh2
                simulatedDistance1 = 350 // meters - 低於 Thresh1
                simulatedDistance2 = 350 // meters - 高於 Thresh2
            } else {
                // 觸發後：距離1 < Thresh1, 距離2 > Thresh2
                simulatedDistance1 = 320 // meters - 低於 Thresh1
                simulatedDistance2 = 300 // meters - 高於 Thresh2
            }

            // D1-1 進入條件: Ml1 - Hys > Thresh1
            const condition1 = simulatedDistance1 - params.Hys > params.Thresh1
            // D1-2 進入條件: Ml2 + Hys < Thresh2
            const condition2 = simulatedDistance2 + params.Hys < params.Thresh2
            // 事件觸發需要兩個條件同時滿足
            const eventTriggered = condition1 && condition2

            return {
                condition1, // D1-1 進入條件
                condition2, // D1-2 進入條件
                eventTriggered,
                description: eventTriggered
                    ? 'D1 事件已觸發 (30-70s)'
                    : '等待條件滿足',
                currentDistance1: simulatedDistance1,
                currentDistance2: simulatedDistance2,
                triggerTimeRange: '30-70秒',
            }
        }, [params, animationState.currentTime])

        // 動畫解說內容生成 - 基於雙重距離測量和位置服務實際用例
        const narrationContent = useMemo(() => {
            const currentTime = animationState.currentTime

            // 模擬 UE 位置
            const uePosition = { lat: 25.048, lon: 121.528 }

            // 模擬距離值（實際應用中會基於真實地理計算）
            let simulatedDistance1, simulatedDistance2

            // 在特定時間段模擬事件觸發條件
            if (currentTime >= 30 && currentTime <= 70) {
                // 觸發區間：距離1 > Thresh1, 距離2 < Thresh2
                simulatedDistance1 = 480 // meters - 超過 Thresh1 (400m)
                simulatedDistance2 = 200 // meters - 低於 Thresh2 (250m)
            } else if (currentTime < 30) {
                // 觸發前：距離1 < Thresh1, 距離2 > Thresh2
                simulatedDistance1 = 350 // meters - 低於 Thresh1
                simulatedDistance2 = 350 // meters - 高於 Thresh2
            } else {
                // 觸發後：距離1 < Thresh1, 距離2 > Thresh2
                simulatedDistance1 = 320 // meters - 低於 Thresh1
                simulatedDistance2 = 300 // meters - 高於 Thresh2
            }

            // 判斷當前階段和位置服務應用
            let phase = 'monitoring'
            let phaseTitle = ''
            let description = ''
            let technicalNote = ''
            let nextAction = ''
            let locationService = ''
            let practicalUseCase = ''

            const condition1 = simulatedDistance1 - params.Hys > params.Thresh1
            const condition2 = simulatedDistance2 + params.Hys < params.Thresh2
            const eventTriggered = condition1 && condition2

            if (eventTriggered) {
                phase = 'triggered'
                phaseTitle = '📍 Event D1 已觸發 - 位置服務啟動'
                description = `UE 與參考位置1的距離 (${simulatedDistance1}m) 超過門檻1，同時與參考位置2的距離 (${simulatedDistance2}m) 低於門檻2。雙重距離條件同時滿足，觸發位置感知服務。`
                
                // 實際位置服務用例
                locationService = '🎯 位置服務應用：地理圍欄觸發'
                practicalUseCase = `實際用例：用戶進入台北101商圈範圍 (遠離台北101但接近中正紀念堂)，系統自動啟動：
• 🛍️ 商圈推薦服務：推送附近商店優惠資訊
• 🚇 交通導航優化：提供最佳大眾運輸路線
• 💰 位置差異化計費：啟動商圈內的特殊資費方案
• 🔔 區域廣播：推送該區域的重要公告或緊急資訊
• 📊 用戶行為分析：記錄區域停留時間和偏好分析`
                
                technicalNote = `3GPP 條件: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2\\n參考位置1: ${simulatedDistance1} - ${params.Hys} = ${simulatedDistance1 - params.Hys} > ${params.Thresh1} m\\n參考位置2: ${simulatedDistance2} + ${params.Hys} = ${simulatedDistance2 + params.Hys} < ${params.Thresh2} m\\n\\n位置服務啟動參數：\\n• 觸發延遲：${params.timeToTrigger}ms\\n• 報告間隔：${params.reportInterval}ms\\n• 報告次數：${params.reportAmount === -1 ? '無限制' : params.reportAmount}次`
                nextAction = '執行位置感知服務，開始提供差異化服務內容'
            } else if (condition1 && !condition2) {
                phase = 'partial'
                phaseTitle = '⚠️ 位置監控中 - 等待進入服務區域'
                description = `UE 與參考位置1的距離條件已滿足 (${simulatedDistance1}m > ${params.Thresh1}m)，但與參考位置2的距離 (${simulatedDistance2}m) 仍高於門檻。`
                locationService = '👀 位置服務狀態：準備階段'
                practicalUseCase = `準備階段用例：用戶正離開台北101，但尚未到達中正紀念堂商圈
• 📱 預載入服務：開始預載入目標區域的服務內容
• 🔄 網路優化：調整網路配置準備提供更好的服務品質
• 📍 軌跡預測：基於移動模式預測用戶可能的目的地
• ⚡ 快取準備：預載入可能需要的地圖資料和服務資訊`
                technicalNote = `條件1: ✅ Ml1 - Hys = ${simulatedDistance1 - params.Hys} > ${params.Thresh1}\\n條件2: ❌ Ml2 + Hys = ${simulatedDistance2 + params.Hys} ≮ ${params.Thresh2}\\n\\n等待進入條件：UE需要更接近參考位置2`
                nextAction = '繼續監控UE與參考位置2的距離變化，準備位置服務'
            } else if (!condition1 && condition2) {
                phase = 'partial'
                phaseTitle = '⚠️ 位置監控中 - 等待離開原始區域'
                description = `UE 與參考位置2的距離條件已滿足 (${simulatedDistance2}m < ${params.Thresh2}m)，但與參考位置1的距離 (${simulatedDistance1}m) 仍低於門檻。`
                locationService = '🔄 位置服務狀態：過渡階段'
                practicalUseCase = `過渡階段用例：用戶已接近中正紀念堂，但尚未完全離開台北101商圈
• 🔀 服務切換準備：準備從原始區域服務切換到新區域
• 💾 狀態保存：保存當前服務狀態和用戶偏好設定
• 🎯 精準定位：提高位置測量精度確保平滑的服務轉換
• 📋 服務清單更新：準備新區域的可用服務列表`
                technicalNote = `條件1: ❌ Ml1 - Hys = ${simulatedDistance1 - params.Hys} ≯ ${params.Thresh1}\\n條件2: ✅ Ml2 + Hys = ${simulatedDistance2 + params.Hys} < ${params.Thresh2}\\n\\n等待離開條件：UE需要更遠離參考位置1`
                nextAction = '等待UE遠離參考位置1，監控距離變化以完成條件'
            } else {
                phaseTitle = '🔍 位置正常監控階段'
                description = `雙重距離條件均未滿足。UE 與參考位置1 (${simulatedDistance1}m) 和參考位置2 (${simulatedDistance2}m) 的距離均在正常範圍內。`
                locationService = '🏠 位置服務狀態：標準服務模式'
                practicalUseCase = `標準服務模式用例：用戶在一般區域，提供基本位置服務
• 📍 基礎定位：提供標準精度的位置服務
• 🌐 通用服務：提供通用的網路服務和應用支援
• 🔋 省電模式：降低位置測量頻率以節省電池
• 📊 背景監控：持續監控位置變化，準備未來的服務觸發
• 🛡️ 隱私保護：在非特殊區域時加強位置隱私保護`
                technicalNote = `參考位置1距離: ${simulatedDistance1}m\\n參考位置2距離: ${simulatedDistance2}m\\n\\n監控重點：\\n• 距離變化趨勢分析\\n• 用戶移動模式學習\\n• 位置預測準確性提升\\n• 網路資源優化`
                nextAction = '繼續監控UE位置變化和距離計算，準備位置服務觸發'
            }

            // 根據時間添加詳細的位置情境解說
            let scenarioContext = ''
            let mobilityScenario = ''
            if (currentTime < 25) {
                scenarioContext = '🚀 場景：UE 在台北101商圈外圍，準備進入監控區域'
                mobilityScenario = '典型移動情境：用戶從信義區外圍步行或搭乘交通工具前往台北101'
            } else if (currentTime < 40) {
                scenarioContext = '🌍 場景：UE 開始遠離台北101，朝向中正紀念堂方向移動'
                mobilityScenario = '典型移動情境：用戶從信義區商圈前往中正區，可能是觀光行程或商務活動'
            } else if (currentTime < 75) {
                scenarioContext = '📍 場景：UE 在雙重距離條件的理想觸發區域內'
                mobilityScenario = '典型移動情境：用戶在台北車站周邊活動，距離兩個地標都在最佳範圍內'
            } else {
                scenarioContext = '🏠 場景：UE 離開特殊服務區域，回到一般監控狀態'
                mobilityScenario = '典型移動情境：用戶完成區域內活動，前往其他地區或返回住所'
            }

            return {
                phase,
                phaseTitle,
                description,
                technicalNote,
                nextAction,
                scenarioContext,
                mobilityScenario,
                locationService,
                practicalUseCase,
                distance1: simulatedDistance1.toString(),
                distance2: simulatedDistance2.toString(),
                timeProgress: `${currentTime.toFixed(1)}s / 100s`,
                reference1: '參考位置1 (台北101)',
                reference2: '參考位置2 (中正紀念堂)',
                uePosition: `${uePosition.lat.toFixed(4)}, ${uePosition.lon.toFixed(4)}`,
            }
        }, [
            animationState.currentTime,
            params.Thresh1,
            params.Thresh2,
            params.Hys,
            params.timeToTrigger,
            params.reportInterval,
            params.reportAmount,
        ])

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
                                            max="100"
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

                            {/* Event D1 距離門檻參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🎯 D1 距離門檻
                                </h3>
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            distanceThreshFromReference1
                                            <span className="control-unit">
                                                公尺
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="200"
                                            max="800"
                                            step="10"
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
                                            {params.Thresh1}m
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            distanceThreshFromReference2
                                            <span className="control-unit">
                                                公尺
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="100"
                                            max="400"
                                            step="10"
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
                                            {params.Thresh2}m
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

                            {/* Event D1 狀態 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📡 D1 事件狀態
                                </h3>
                                <div className="event-status">
                                    <div className="status-item">
                                        <span className="status-label">
                                            進入條件 D1-1 (參考位置1):
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
                                            進入條件 D1-2 (參考位置2):
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
                                            {eventStatus.currentDistance1}m
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            距離2 (Ml2):
                                        </span>
                                        <span className="status-value">
                                            {eventStatus.currentDistance2}m
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

                            {/* 參考位置信息 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📍 參考位置
                                </h3>
                                <div className="location-info">
                                    <div className="location-item">
                                        <span className="location-label">
                                            參考點1:
                                        </span>
                                        <span className="location-coords">
                                            {params.referenceLocation1.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {params.referenceLocation1.lon.toFixed(
                                                4
                                            )}
                                        </span>
                                    </div>
                                    <div className="location-item">
                                        <span className="location-label">
                                            參考點2:
                                        </span>
                                        <span className="location-coords">
                                            {params.referenceLocation2.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {params.referenceLocation2.lon.toFixed(
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
                                                    {narrationContent.mobilityScenario}
                                                </div>
                                            </div>

                                            <div className="location-service-stage">
                                                <h4>{narrationContent.locationService}</h4>
                                                <div className="location-use-case">
                                                    {narrationContent.practicalUseCase.split('\\n').map((line, index) => (
                                                        <div key={index} className="use-case-line">
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
                                                距離1：
                                            </span>
                                            <span className="metric-value">
                                                {narrationContent.distance1} m
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="metric-label">
                                                距離2：
                                            </span>
                                            <span className="metric-value">
                                                {narrationContent.distance2} m
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="metric-label">
                                                UE位置：
                                            </span>
                                            <span className="metric-value">
                                                {narrationContent.uePosition}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className="chart-container">
                                <PureD1Chart
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
                            <h4>Event D1 條件：</h4>
                            <ul>
                                <li>
                                    <strong>進入條件：</strong> 
                                    <br/>條件1: Ml1 - Hys &gt; Thresh1 (參考位置1距離)
                                    <br/>條件2: Ml2 + Hys &lt; Thresh2 (參考位置2距離)
                                    <br/><em>同時滿足: 條件1 <strong>且</strong> 條件2</em>
                                </li>
                                <li>
                                    <strong>離開條件：</strong> 
                                    <br/>條件1: Ml1 + Hys &lt; Thresh1 (遠離參考位置1)
                                    <br/>條件2: Ml2 - Hys &gt; Thresh2 (接近參考位置2)
                                    <br/><em>任一滿足: 條件1 <strong>或</strong> 條件2</em>
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>參數說明：</h4>
                            <ul>
                                <li>
                                    <strong>Ml1：</strong>UE 與
                                    referenceLocation1 的距離（公尺）
                                </li>
                                <li>
                                    <strong>Ml2：</strong>UE 與
                                    referenceLocation2 的距離（公尺）
                                </li>
                                <li>
                                    <strong>Thresh1：</strong>
                                    distanceThreshFromReference1 門檻值
                                </li>
                                <li>
                                    <strong>Thresh2：</strong>
                                    distanceThreshFromReference2 門檻值
                                </li>
                                <li>
                                    <strong>Hys：</strong>hysteresisLocation
                                    遲滯參數
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>應用場景：</h4>
                            <ul>
                                <li>
                                    <strong>位置感知服務：</strong>
                                    基於 UE 與特定參考點的距離關係觸發服務
                                </li>
                                <li>
                                    <strong>區域管理：</strong>當 UE
                                    進入或離開特定地理區域時進行管理
                                </li>
                                <li>
                                    <strong>資源調度：</strong>
                                    根據 UE 位置進行網路資源的動態分配
                                </li>
                                <li>
                                    <strong>位置相關計費：</strong>
                                    在特定區域內提供差異化的服務計費
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
)

EventD1Viewer.displayName = 'EventD1Viewer'

export default EventD1Viewer
