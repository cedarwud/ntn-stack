/**
 * Event A4 Viewer Component
 * 彈窗式 3GPP TS 38.331 Event A4 視覺化組件
 * 結合 event-a4 分支的設計風格和 main 分支的正確 RSRP 數據
 * 優化版本：避免不必要的重新渲染
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { loadCSVData } from '../../../../utils/csvDataParser'
import { ViewerProps } from '../../../../types/viewer'
import PureA4Chart from './PureA4Chart'
import './EventA4Viewer.scss'

// 擴展 ViewerProps 以支援事件選擇
interface EventA4ViewerProps extends ViewerProps {
    selectedEvent?: string
    onEventChange?: (event: string) => void
    isDarkTheme?: boolean
}

// 註冊已移除 - 使用原生 Chart.js

const EventA4Viewer: React.FC<EventA4ViewerProps> = React.memo(
    ({
        onReportLastUpdateToNavbar,
        reportRefreshHandlerToNavbar,
        reportIsLoadingToNavbar,
        selectedEvent = 'A4',
        onEventChange,
        isDarkTheme: externalIsDarkTheme,
    }) => {
        // console.log('🎯 EventA4Viewer render') // 移除除錯日誌

        // Event A4 參數狀態管理 - 基於 3GPP TS 38.331 規範
        const [a4Threshold, setA4Threshold] = useState(-70) // dBm, 鄰近基站 RSRP 門檻
        const [hysteresis, setHysteresis] = useState(3) // dB, 信號遲滯參數
        const [offsetFreq, setOffsetFreq] = useState(0) // dB, 頻率偏移 Ofn
        const [offsetCell, setOffsetCell] = useState(0) // dB, 小區偏移 Ocn
        const [timeToTrigger, setTimeToTrigger] = useState(160) // ms
        const [reportInterval, setReportInterval] = useState(1000) // ms
        const [reportAmount, setReportAmount] = useState(8) // 次數
        const [reportOnLeave, setReportOnLeave] = useState(true)

        // 動畫和顯示控制狀態
        const [showThresholdLines, setShowThresholdLines] = useState(true)
        const [animationState, setAnimationState] = useState({
            isPlaying: false,
            currentTime: 0,
            speed: 1,
        })

        // 主題狀態 - 使用外部傳入的主題或預設值
        const [isDarkTheme, setIsDarkTheme] = useState(
            externalIsDarkTheme ?? true
        )

        // 當外部主題變化時更新內部狀態
        useEffect(() => {
            if (externalIsDarkTheme !== undefined) {
                setIsDarkTheme(externalIsDarkTheme)
            }
        }, [externalIsDarkTheme])

        // 圖表和數據狀態
        const [loading, setLoading] = useState(true)

        // 動畫控制功能
        const toggleAnimation = useCallback(() => {
            setAnimationState(prev => ({
                ...prev,
                isPlaying: !prev.isPlaying
            }))
        }, [])

        const resetAnimation = useCallback(() => {
            setAnimationState(prev => ({
                ...prev,
                isPlaying: false,
                currentTime: 0
            }))
        }, [])

        // 動畫進度更新
        useEffect(() => {
            if (!animationState.isPlaying) return

            const interval = setInterval(() => {
                setAnimationState(prev => {
                    const newTime = prev.currentTime + 0.1 * prev.speed // 0.1 second steps
                    const maxTime = 30 // 30 seconds max for A4
                    if (newTime >= maxTime) {
                        return { ...prev, isPlaying: false, currentTime: 0 }
                    }
                    return { ...prev, currentTime: newTime }
                })
            }, 100) // Update every 100ms

            return () => clearInterval(interval)
        }, [animationState.isPlaying, animationState.speed])

        // 穩定的數據載入函數
        const loadData = useCallback(async () => {
            try {
                setLoading(true)
                reportIsLoadingToNavbar?.(true)

                const _csvData = await loadCSVData()

                onReportLastUpdateToNavbar?.(new Date().toLocaleTimeString())
            } catch (error) {
                console.error('Error loading RSRP data:', error)
            } finally {
                setLoading(false)
                reportIsLoadingToNavbar?.(false)
            }
        }, [onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

        // 載入真實的 RSRP 數據 - 穩定化依賴
        useEffect(() => {
            loadData()

            // 註冊刷新處理器
            reportRefreshHandlerToNavbar?.(loadData)
        }, [loadData, reportRefreshHandlerToNavbar])

        // 參數重置函數 - 使用 useCallback 穩定化
        const handleReset = useCallback(() => {
            setA4Threshold(-70)
            setHysteresis(3)
            setOffsetFreq(0)
            setOffsetCell(0)
            setTimeToTrigger(160)
            setReportInterval(1000)
            setReportAmount(8)
            setReportOnLeave(true)
        }, [])

        // 主題切換函數 - 使用 useCallback 穩定化
        const _toggleTheme = useCallback(() => {
            setIsDarkTheme(!isDarkTheme)
        }, [isDarkTheme])

        // 事件選擇器渲染 - 使用 useMemo 穩定化
        const eventSelectorComponent = useMemo(() => {
            if (!onEventChange) return null

            return (
                <div className="event-selector-compact">
                    <label>事件類型:</label>
                    <div className="event-buttons-compact">
                        {['A4', 'D1', 'D2', 'T1'].map((eventType) => (
                            <button
                                key={eventType}
                                className={`event-btn-compact ${
                                    selectedEvent === eventType ? 'active' : ''
                                } ${
                                    !['A4', 'D1'].includes(eventType)
                                        ? 'disabled'
                                        : ''
                                }`}
                                onClick={() =>
                                    ['A4', 'D1'].includes(eventType) &&
                                    onEventChange(eventType)
                                }
                                disabled={!['A4', 'D1'].includes(eventType)}
                            >
                                {eventType}
                            </button>
                        ))}
                    </div>
                </div>
            )
        }, [onEventChange, selectedEvent])

        // 動畫控制回調已在上面定義

        const toggleThresholdLines = useCallback(() => {
            setShowThresholdLines((prev) => !prev)
        }, [])

        // 計算 Event A4 條件狀態 - 基於 3GPP TS 38.331 規範
        const eventStatus = useMemo(() => {
            // 模擬鄰近基站的 RSRP 測量值（實際應從圖表數據獲取）
            const simulatedRSRP = -75 // dBm (Mn)
            // A4-1 進入條件: Mn + Ofn + Ocn - Hys > Thresh
            const effectiveRSRP = simulatedRSRP + offsetFreq + offsetCell
            const condition1 = effectiveRSRP - hysteresis > a4Threshold
            // A4-2 離開條件: Mn + Ofn + Ocn + Hys < Thresh  
            const condition2 = effectiveRSRP + hysteresis < a4Threshold

            return {
                condition1, // A4-1 進入條件
                condition2, // A4-2 離開條件
                eventTriggered: condition1,
                description: condition1 ? '事件已觸發' : '等待條件滿足',
                currentRSRP: simulatedRSRP,
                effectiveRSRP: effectiveRSRP,
            }
        }, [a4Threshold, hysteresis, offsetFreq, offsetCell, animationState.currentTime])

        // 參數控制面板渲染 - 使用 useMemo 穩定化，採用 D1 的分類設計
        const controlPanelComponent = useMemo(
            () => (
                <div className="control-panel">
                    {eventSelectorComponent}

                    {/* 動畫控制 */}
                    <div className="control-section">
                        <h3 className="control-section__title">🎬 動畫控制</h3>
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
                        
                        {/* 時間遊標控制 */}
                        <div className="control-group">
                            <div className="control-item">
                                <label className="control-label">
                                    當前時間 (動畫時間)
                                    <span className="control-unit">秒</span>
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="30"
                                    step="0.1"
                                    value={animationState.currentTime}
                                    onChange={(e) =>
                                        setAnimationState(prev => ({
                                            ...prev,
                                            currentTime: Number(e.target.value)
                                        }))
                                    }
                                    className="control-slider"
                                />
                                <span className="control-value">
                                    {animationState.currentTime.toFixed(1)}s
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Event A4 信號參數 */}
                    <div className="control-section">
                        <h3 className="control-section__title">🎯 A4 信號參數</h3>
                        <div className="control-group">
                            <div className="control-item">
                                <label className="control-label">
                                    a4-Threshold (RSRP門檻)
                                    <span className="control-unit">dBm</span>
                                </label>
                                <input
                                    type="range"
                                    min="-100"
                                    max="-40"
                                    value={a4Threshold}
                                    onChange={(e) =>
                                        setA4Threshold(parseInt(e.target.value))
                                    }
                                    className="control-slider"
                                />
                                <span className="control-value">
                                    {a4Threshold} dBm
                                </span>
                            </div>

                            <div className="control-item">
                                <label className="control-label">
                                    Hysteresis (信號遲滯)
                                    <span className="control-unit">dB</span>
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="10"
                                    value={hysteresis}
                                    onChange={(e) =>
                                        setHysteresis(parseInt(e.target.value))
                                    }
                                    className="control-slider"
                                />
                                <span className="control-value">
                                    {hysteresis} dB
                                </span>
                            </div>

                            <div className="control-item">
                                <label className="control-label">
                                    Offset Freq (Ofn 頻率偏移)
                                    <span className="control-unit">dB</span>
                                </label>
                                <input
                                    type="range"
                                    min="-10"
                                    max="10"
                                    value={offsetFreq}
                                    onChange={(e) =>
                                        setOffsetFreq(parseInt(e.target.value))
                                    }
                                    className="control-slider"
                                />
                                <span className="control-value">
                                    {offsetFreq} dB
                                </span>
                            </div>

                            <div className="control-item">
                                <label className="control-label">
                                    Offset Cell (Ocn 小區偏移)
                                    <span className="control-unit">dB</span>
                                </label>
                                <input
                                    type="range"
                                    min="-10"
                                    max="10"
                                    value={offsetCell}
                                    onChange={(e) =>
                                        setOffsetCell(parseInt(e.target.value))
                                    }
                                    className="control-slider"
                                />
                                <span className="control-value">
                                    {offsetCell} dB
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 時間參數 */}
                    <div className="control-section">
                        <h3 className="control-section__title">⏱️ 時間參數</h3>
                        <div className="control-group">
                            <div className="control-item control-item--horizontal">
                                <span className="control-label">
                                    TimeToTrigger
                                </span>
                                <select
                                    value={timeToTrigger}
                                    onChange={(e) =>
                                        setTimeToTrigger(
                                            parseInt(e.target.value)
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
                                    <option value={1000}>1000</option>
                                </select>
                                <span className="control-unit">毫秒</span>
                            </div>
                        </div>
                    </div>

                    {/* 報告參數 */}
                    <div className="control-section">
                        <h3 className="control-section__title">📊 報告參數</h3>
                        <div className="control-group">
                            <div className="control-item control-item--horizontal">
                                <span className="control-label">
                                    Report Interval
                                </span>
                                <select
                                    value={reportInterval}
                                    onChange={(e) =>
                                        setReportInterval(
                                            parseInt(e.target.value)
                                        )
                                    }
                                    className="control-select"
                                >
                                    <option value={200}>200</option>
                                    <option value={240}>240</option>
                                    <option value={480}>480</option>
                                    <option value={640}>640</option>
                                    <option value={1000}>1000</option>
                                    <option value={1024}>1024</option>
                                    <option value={2048}>2048</option>
                                    <option value={5000}>5000</option>
                                </select>
                                <span className="control-unit">毫秒</span>
                            </div>

                            <div className="control-item control-item--horizontal">
                                <span className="control-label">
                                    Report Amount
                                </span>
                                <select
                                    value={reportAmount}
                                    onChange={(e) =>
                                        setReportAmount(
                                            parseInt(e.target.value)
                                        )
                                    }
                                    className="control-select"
                                >
                                    <option value={1}>1</option>
                                    <option value={2}>2</option>
                                    <option value={4}>4</option>
                                    <option value={8}>8</option>
                                    <option value={16}>16</option>
                                    <option value={20}>20</option>
                                    <option value={-1}>無限制</option>
                                </select>
                                <span className="control-unit">次數</span>
                            </div>

                            <div className="control-item control-item--horizontal">
                                <span className="control-label">
                                    Report On Leave
                                </span>
                                <label className="control-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={reportOnLeave}
                                        onChange={(e) =>
                                            setReportOnLeave(e.target.checked)
                                        }
                                    />
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* Event A4 狀態 */}
                    <div className="control-section">
                        <h3 className="control-section__title">📡 A4 事件狀態</h3>
                        <div className="event-status">
                            <div className="status-item">
                                <span className="status-label">
                                    進入條件 A4-1:
                                </span>
                                <span
                                    className={`status-value ${
                                        eventStatus.condition1
                                            ? 'status-value--active'
                                            : ''
                                    }`}
                                >
                                    Mn + Ofn + Ocn - Hys &gt; a4-Thresh
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">
                                    離開條件 A4-2:
                                </span>
                                <span
                                    className={`status-value ${
                                        eventStatus.condition2
                                            ? 'status-value--active'
                                            : ''
                                    }`}
                                >
                                    Mn + Ofn + Ocn + Hys &lt; a4-Thresh
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">事件狀態:</span>
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
                                <span className="status-label">原始 RSRP (Mn):</span>
                                <span className="status-value">
                                    {eventStatus.currentRSRP} dBm
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">有效 RSRP:</span>
                                <span className="status-value">
                                    {eventStatus.effectiveRSRP} dBm
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 重置按鈕 */}
                    <div className="control-section">
                        <div className="control-group control-group--buttons">
                            <button
                                className="control-btn control-btn--reset"
                                onClick={handleReset}
                            >
                                🔄 重置所有參數
                            </button>
                        </div>
                    </div>
                </div>
            ),
            [
                eventSelectorComponent,
                a4Threshold,
                hysteresis,
                offsetFreq,
                offsetCell,
                timeToTrigger,
                reportInterval,
                reportAmount,
                reportOnLeave,
                showThresholdLines,
                animationState,
                eventStatus,
                handleReset,
                toggleAnimation,
                resetAnimation,
                toggleThresholdLines,
            ]
        )

        // 圖表區域渲染 - 使用 useMemo 穩定化
        const chartAreaComponent = useMemo(
            () => (
                <div className="chart-area">
                    <div className="chart-container">
                        <PureA4Chart
                            threshold={a4Threshold}
                            hysteresis={hysteresis}
                            currentTime={animationState.currentTime}
                            showThresholdLines={showThresholdLines}
                            isDarkTheme={isDarkTheme}
                        />
                    </div>
                </div>
            ),
            [a4Threshold, hysteresis, animationState.currentTime, showThresholdLines, isDarkTheme]
        )

        // 載入中組件 - 使用 useMemo 穩定化
        const loadingComponent = useMemo(
            () => (
                <div className="event-a4-viewer loading">
                    <div className="loading-content">
                        <div className="loading-spinner"></div>
                        <p>正在載入 RSRP 數據...</p>
                    </div>
                </div>
            ),
            []
        )

        if (loading) {
            return loadingComponent
        }

        return (
            <div className="event-a4-viewer">
                <div className="event-viewer__content">
                    <div className="event-viewer__controls">
                        {controlPanelComponent}
                    </div>
                    <div className="event-viewer__chart-container">
                        {chartAreaComponent}
                    </div>
                </div>

                {/* 3GPP 規範說明 */}
                <div className="event-viewer__specification">
                    <h3 className="spec-title">📖 3GPP TS 38.331 規範</h3>
                    <div className="spec-content">
                        <div className="spec-section">
                            <h4>Event A4 條件：</h4>
                            <ul>
                                <li>
                                    <strong>進入條件：</strong> Mn + Ofn + Ocn -
                                    Hys &gt; Thresh
                                </li>
                                <li>
                                    <strong>離開條件：</strong> Mn + Ofn + Ocn +
                                    Hys &lt; Thresh
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>參數說明：</h4>
                            <ul>
                                <li>
                                    <strong>Mn：</strong>鄰近基站的 RSRP
                                    測量值（dBm）
                                </li>
                                <li>
                                    <strong>Ofn：</strong>鄰近基站的頻率偏移量
                                </li>
                                <li>
                                    <strong>Ocn：</strong>鄰近基站的載波偏移量
                                </li>
                                <li>
                                    <strong>Thresh：</strong>設定的 RSRP
                                    門檻值（a4-Threshold）
                                </li>
                                <li>
                                    <strong>Hys：</strong>hysteresis
                                    遲滯參數，避免頻繁切換
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>應用場景：</h4>
                            <ul>
                                <li>
                                    <strong>換手準備：</strong>
                                    當鄰近基站信號強度超過門檻時觸發
                                </li>
                                <li>
                                    <strong>負載平衡：</strong>
                                    協助網路進行負載分散
                                </li>
                                <li>
                                    <strong>覆蓋優化：</strong>確保 UE
                                    連接到最佳的基站
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
)

EventA4Viewer.displayName = 'EventA4Viewer'

export default EventA4Viewer
