/**
 * Event T1 Viewer Component
 * 提供完整的 Event T1 測量事件查看功能
 * 包含參數控制和 3GPP TS 38.331 規範實現
 */

import React, { useState, useMemo, useCallback } from 'react'
import PureT1Chart from './PureT1Chart'
import type { EventT1Params } from '../types'
import './EventA4Viewer.scss' // 重用 A4 的樣式
import './NarrationPanel.scss' // 動畫解說面板樣式

interface EventT1ViewerProps {
    isDarkTheme?: boolean
    onThemeToggle?: () => void
    initialParams?: Partial<EventT1Params>
}

export const EventT1Viewer: React.FC<EventT1ViewerProps> = React.memo(
    ({ isDarkTheme = true, onThemeToggle, initialParams = {} }) => {
        // Event T1 參數狀態 - 基於 3GPP TS 38.331 規範 (CondEvent T1)
        const [params, setParams] = useState<EventT1Params>(() => ({
            Thresh1: initialParams.Thresh1 ?? 5000, // t1-Threshold in milliseconds
            Duration: initialParams.Duration ?? 10000, // Duration parameter in milliseconds
            timeToTrigger: initialParams.timeToTrigger ?? 0, // 通常為 0，T1 has built-in time logic
            reportAmount: initialParams.reportAmount ?? 1, // 條件事件用途
            reportInterval: initialParams.reportInterval ?? 1000, // 條件事件用途 (ms)
            reportOnLeave: initialParams.reportOnLeave ?? true, // 條件事件用途
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
            (key: keyof EventT1Params, value: unknown) => {
                setParams((prev) => ({
                    ...prev,
                    [key]: value,
                }))
            },
            []
        )

        // 動畫控制
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
                setAnimationState(prev => {
                    const newTime = prev.currentTime + 100 * prev.speed
                    if (newTime >= 25000) { // 25 seconds max
                        return { ...prev, isPlaying: false, currentTime: 0 }
                    }
                    return { ...prev, currentTime: newTime }
                })
            }, 100)

            return () => clearInterval(interval)
        }, [animationState.isPlaying, animationState.speed])

        const toggleThresholdLines = useCallback(() => {
            setShowThresholdLines((prev) => !prev)
        }, [])

        // 計算 Event T1 條件狀態 - 基於 3GPP TS 38.331 規範
        const eventStatus = useMemo(() => {
            // 使用動畫當前時間作為 Mt
            const currentMt = animationState.currentTime

            // T1 進入條件: Mt > t1-Threshold
            const condition1 = currentMt > params.Thresh1
            // T1 離開條件: Mt > t1-Threshold + Duration
            const leaveCondition = currentMt > params.Thresh1 + params.Duration
            // T1 事件激活: Mt 在 [Thresh1, Thresh1+Duration] 區間內
            const eventTriggered = condition1 && !leaveCondition

            return {
                condition1, // 基本條件
                conditionMet: eventTriggered, // 完整觸發條件
                leaveCondition, // 離開條件
                eventTriggered,
                description: eventTriggered
                    ? 'T1 事件已觸發'
                    : condition1 && leaveCondition
                    ? '事件已結束'
                    : condition1
                    ? '等待持續時間滿足'
                    : '等待條件滿足',
                currentMt: currentMt,
                timeInCondition: Math.max(0, currentMt - params.Thresh1),
            }
        }, [params.Thresh1, params.Duration, animationState.currentTime])
        
        // 動畫解說內容生成 - 基於時間窗口和持續時間
        const narrationContent = useMemo(() => {
            const currentTime = animationState.currentTime
            const threshold = params.Thresh1
            const duration = params.Duration
            const endTime = threshold + duration
            
            // 判斷當前階段
            let phase = 'waiting'
            let phaseTitle = ''
            let description = ''
            let technicalNote = ''
            let nextAction = ''
            
            if (currentTime < threshold) {
                phase = 'waiting'
                phaseTitle = '⏳ 等待階段 - 時間尚未達到門檻'
                description = `當前時間 (${currentTime.toFixed(0)}ms) 仍低於時間門檻 (${threshold}ms)。系統正在等待時間窗口達到觸發時間。`
                technicalNote = `3GPP 條件: Mt > t1-Threshold\\n當前 Mt: ${currentTime.toFixed(0)}ms < 門檻: ${threshold}ms`
                nextAction = `還需等待 ${(threshold - currentTime).toFixed(0)}ms 才會進入事件窗口`
            } else if (currentTime >= threshold && currentTime <= endTime) {
                phase = 'triggered'
                phaseTitle = '✅ Event T1 已觸發 - 時間窗口內'
                description = `當前時間 (${currentTime.toFixed(0)}ms) 在事件窗口內 [${threshold}ms - ${endTime}ms]。T1 事件正在活躍中，系統正在執行時間相關的操作。`
                technicalNote = `3GPP 條件: t1-Threshold < Mt < t1-Threshold + Duration\\n${threshold}ms < ${currentTime.toFixed(0)}ms < ${endTime}ms\\n已持續: ${(currentTime - threshold).toFixed(0)}ms / ${duration}ms`
                nextAction = `事件將在 ${(endTime - currentTime).toFixed(0)}ms 後結束`
            } else {
                phase = 'completed'
                phaseTitle = '✓ Event T1 已結束 - 超出時間窗口'
                description = `當前時間 (${currentTime.toFixed(0)}ms) 已超過事件窗口結束點 (${endTime}ms)。T1 事件已完成，系統返回正常狀態。`
                technicalNote = `3GPP 條件: Mt > t1-Threshold + Duration\\n${currentTime.toFixed(0)}ms > ${endTime}ms\\n已超過: ${(currentTime - endTime).toFixed(0)}ms`
                nextAction = '監控新的時間窗口和條件變化'
            }
            
            // 根據時間添加情境解說
            let scenarioContext = ''
            if (currentTime < 5000) {
                scenarioContext = '🚀 場景：系統啟動，時間計數器初始化'
            } else if (currentTime < 15000) {
                scenarioContext = '🕒 場景：接近時間門檻，準備事件觸發'
            } else {
                scenarioContext = '🏁 場景：進入時間窗口，時間相關事件處理'
            }
            
            return {
                phase,
                phaseTitle,
                description,
                technicalNote,
                nextAction,
                scenarioContext,
                currentTime: currentTime.toFixed(0),
                threshold: threshold.toString(),
                duration: duration.toString(),
                timeProgress: `${currentTime.toFixed(0)}ms / 25000ms`,
                remainingTime: phase === 'triggered' ? `${(endTime - currentTime).toFixed(0)}ms` : 'N/A',
                progressPercent: phase === 'triggered' ? 
                    `${(((currentTime - threshold) / duration) * 100).toFixed(1)}%` : '0%'
            }
        }, [animationState.currentTime, params.Thresh1, params.Duration])

        // 穩定的圖表 props
        const chartProps = useMemo(
            () => ({
                threshold: params.Thresh1,
                duration: params.Duration,
                currentTime: animationState.currentTime,
                showThresholdLines,
                isDarkTheme,
                onThemeToggle,
            }),
            [
                params.Thresh1,
                params.Duration,
                animationState.currentTime,
                showThresholdLines,
                isDarkTheme,
                onThemeToggle,
            ]
        )

        // 參數控制面板渲染 - 採用 A4 的分類設計
        const controlPanelComponent = useMemo(
            () => (
                <div className="control-panel">
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
                        
                        {/* 解說系統控制 */}
                        <div className="control-group control-group--buttons">
                            <button
                                className={`control-btn ${
                                    showNarration
                                        ? 'control-btn--active'
                                        : ''
                                }`}
                                onClick={() => setShowNarration(!showNarration)}
                            >
                                💬 動畫解說
                            </button>
                            <button
                                className={`control-btn ${
                                    showTechnicalDetails
                                        ? 'control-btn--active'
                                        : ''
                                }`}
                                onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                            >
                                🔍 技術細節
                            </button>
                        </div>
                    </div>

                    {/* T1 時間參數 */}
                    <div className="control-section">
                        <h3 className="control-section__title">
                            ⏱️ T1 時間參數
                        </h3>
                        <div className="control-group">
                            <div className="control-item">
                                <label className="control-label">
                                    t1-Threshold (時間閾值)
                                    <span className="control-unit">毫秒</span>
                                </label>
                                <input
                                    type="range"
                                    min="1000"
                                    max="20000"
                                    step="500"
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
                                    {params.Thresh1}ms
                                </span>
                            </div>

                            <div className="control-item">
                                <label className="control-label">
                                    當前時間 Mt (動畫時間)
                                    <span className="control-unit">毫秒</span>
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="25000"
                                    step="100"
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
                                    {animationState.currentTime}ms
                                </span>
                            </div>

                            <div className="control-item">
                                <label className="control-label">
                                    Duration (持續時間)
                                    <span className="control-unit">毫秒</span>
                                </label>
                                <input
                                    type="range"
                                    min="2000"
                                    max="30000"
                                    step="1000"
                                    value={params.Duration}
                                    onChange={(e) =>
                                        updateParam(
                                            'Duration',
                                            Number(e.target.value)
                                        )
                                    }
                                    className="control-slider"
                                />
                                <span className="control-value">
                                    {params.Duration}ms
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 報告參數 - CondEvent T1 特殊用途 */}
                    <div className="control-section">
                        <h3 className="control-section__title">📊 報告參數 (條件事件用途)</h3>
                        <div className="condition-note" style={{
                            fontSize: '12px',
                            color: '#ffa500',
                            marginBottom: '10px',
                            padding: '8px',
                            backgroundColor: 'rgba(255, 165, 0, 0.1)',
                            borderRadius: '4px',
                            border: '1px solid rgba(255, 165, 0, 0.3)'
                        }}>
                            ⚠️ 注意：CondEvent T1 通常不直接觸發測量報告，主要用於條件切換判斷
                        </div>
                        <div className="control-group control-group--reporting">
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
                                        checked={params.reportOnLeave}
                                        onChange={(e) =>
                                            updateParam(
                                                'reportOnLeave',
                                                e.target.checked
                                            )
                                        }
                                    />
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* Event T1 狀態 */}
                    <div className="control-section">
                        <h3 className="control-section__title">
                            📡 T1 事件狀態
                        </h3>
                        <div className="event-status">
                            <div className="status-item">
                                <span className="status-label">
                                    進入條件 T1-1:
                                </span>
                                <span
                                    className={`status-value ${
                                        eventStatus.condition1
                                            ? 'status-value--active'
                                            : ''
                                    }`}
                                >
                                    Mt &gt; t1-Threshold (持續 Duration 時間)
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">
                                    離開條件 T1-2:
                                </span>
                                <span
                                    className={`status-value ${
                                        eventStatus.leaveCondition
                                            ? 'status-value--active'
                                            : ''
                                    }`}
                                >
                                    Mt &gt; t1-Threshold + Duration
                                    (時間超出範圍)
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">事件狀態:</span>
                                <span
                                    className={`status-badge ${
                                        eventStatus.eventTriggered
                                            ? 'status-badge--triggered'
                                            : eventStatus.condition1
                                            ? 'status-badge--pending'
                                            : 'status-badge--waiting'
                                    }`}
                                >
                                    {eventStatus.description}
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">
                                    當前時間測量值:
                                </span>
                                <span className="status-value">
                                    {eventStatus.currentMt}ms
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">
                                    條件持續時間:
                                </span>
                                <span className="status-value">
                                    {eventStatus.timeInCondition}ms
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            ),
            [
                params,
                animationState,
                showThresholdLines,
                toggleAnimation,
                resetAnimation,
                toggleThresholdLines,
                updateParam,
                eventStatus,
            ]
        )

        return (
            <div className="event-a4-viewer">
                <div className="event-viewer__content">
                    {/* 控制面板 */}
                    <div className="event-viewer__controls">
                        {controlPanelComponent}
                    </div>
                    
                    {/* 圖表區域 */}
                    <div className="event-viewer__chart-container">
                        <div className="chart-area">
                            {/* 動畫解說面板 */}
                            {showNarration && (
                                <div className={`narration-panel ${isNarrationExpanded ? 'expanded' : 'compact'}`}>
                                    <div className="narration-header">
                                        <h3 className="narration-title">{narrationContent.phaseTitle}</h3>
                                        <div className="narration-controls">
                                            <div className="narration-time">🕰 {narrationContent.timeProgress}</div>
                                            <button
                                                className="narration-toggle"
                                                onClick={() => setIsNarrationExpanded(!isNarrationExpanded)}
                                                title={isNarrationExpanded ? "收起詳細說明" : "展開詳細說明"}
                                            >
                                                {isNarrationExpanded ? '▲' : '▼'}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    {isNarrationExpanded && (
                                        <div className="narration-content">
                                            <div className="narration-scenario">
                                                {narrationContent.scenarioContext}
                                            </div>
                                            
                                            <div className="narration-description">
                                                {narrationContent.description}
                                            </div>
                                            
                                            {showTechnicalDetails && (
                                                <div className="narration-technical">
                                                    <h4>🔧 技術細節：</h4>
                                                    <div className="technical-formula">
                                                        {narrationContent.technicalNote.split('\\n').map((line, index) => (
                                                            <div key={index}>{line}</div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            <div className="narration-next">
                                                <strong>下一步：</strong> {narrationContent.nextAction}
                                            </div>
                                        </div>
                                    )}
                                    
                                    <div className="narration-metrics">
                                        <div className="metric">
                                            <span className="metric-label">當前時間：</span>
                                            <span className="metric-value">{narrationContent.currentTime} ms</span>
                                        </div>
                                        <div className="metric">
                                            <span className="metric-label">時間門檻：</span>
                                            <span className="metric-value">{narrationContent.threshold} ms</span>
                                        </div>
                                        <div className="metric">
                                            <span className="metric-label">持續時間：</span>
                                            <span className="metric-value">{narrationContent.duration} ms</span>
                                        </div>
                                        {narrationContent.phase === 'triggered' && (
                                            <div className="metric">
                                                <span className="metric-label">進度：</span>
                                                <span className="metric-value">{narrationContent.progressPercent}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                            
                            <div className="chart-container">
                                <PureT1Chart {...chartProps} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* 3GPP 規範說明 - 移到底部 */}
                <div className="event-viewer__specification">
                    <h3 className="spec-title">📖 3GPP TS 38.331 規範</h3>
                    <div className="spec-content">
                        <div className="spec-section">
                            <h4>條件事件 T1 (CondEvent T1)：</h4>
                            <ul>
                                <li>
                                    <strong>進入條件：</strong> Mt &gt; t1-Threshold (持續 Duration 時間)
                                </li>
                                <li>
                                    <strong>離開條件：</strong> Mt &gt; t1-Threshold + Duration (時間超出範圍)
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>參數說明：</h4>
                            <ul>
                                <li>
                                    <strong>Mt：</strong>UE 測得的時間測量值（毫秒）
                                </li>
                                <li>
                                    <strong>t1-Threshold：</strong>設定的時間門檻值（毫秒）
                                </li>
                                <li>
                                    <strong>Duration：</strong>事件持續時間長度（毫秒）
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>應用場景：</h4>
                            <ul>
                                <li>
                                    <strong>條件切換：</strong>
                                    基於時間窗口的條件事件觸發
                                </li>
                                <li>
                                    <strong>時間同步：</strong>
                                    確保網路同步和時序控制
                                </li>
                                <li>
                                    <strong>資源管理：</strong>
                                    基於時間條件的資源分配
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
)

EventT1Viewer.displayName = 'EventT1Viewer'

export default EventT1Viewer
