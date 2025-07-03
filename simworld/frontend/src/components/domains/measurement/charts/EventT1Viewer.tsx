/**
 * Event T1 Viewer Component
 * 提供完整的 Event T1 測量事件查看功能
 * 包含參數控制和 3GPP TS 38.331 規範實現
 */

import React, { useState, useMemo, useCallback } from 'react'
import PureT1Chart from './PureT1Chart'
import type { EventT1Params } from '../types'
import './EventA4Viewer.scss' // 重用 A4 的樣式

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
                    
                    {/* 圖表區域 - 只保留標題和圖表 */}
                    <div className="event-viewer__chart-container">
                        <div className="chart-area">
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
