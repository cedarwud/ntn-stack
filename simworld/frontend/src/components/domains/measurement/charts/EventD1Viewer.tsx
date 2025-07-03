/**
 * Event D1 Viewer Component
 * 提供完整的 Event D1 測量事件查看功能
 * 包含參數控制和 3GPP TS 38.331 規範實現
 */

import React, { useState, useMemo, useCallback } from 'react'
import PureD1Chart from './PureD1Chart'
import type { EventD1Params } from '../types'
import './EventA4Viewer.scss' // 重用 A4 的樣式

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
                description: eventTriggered ? 'D1 事件已觸發 (30-70s)' : '等待條件滿足',
                currentDistance1: simulatedDistance1,
                currentDistance2: simulatedDistance2,
                triggerTimeRange: '30-70秒',
            }
        }, [params, animationState.currentTime])

        return (
            <div className="event-d1-viewer">
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
                                            進入條件 D1-1:
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
                                            進入條件 D1-2:
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
                                        <span className="status-label">距離1 (Ml1):</span>
                                        <span className="status-value">
                                            {eventStatus.currentDistance1}m
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">距離2 (Ml2):</span>
                                        <span className="status-value">
                                            {eventStatus.currentDistance2}m
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">觸發時間範圍:</span>
                                        <span className={`status-value ${
                                            eventStatus.eventTriggered 
                                                ? 'status-value--active'
                                                : ''
                                        }`}>
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
                        <PureD1Chart
                            thresh1={params.Thresh1}
                            thresh2={params.Thresh2}
                            hysteresis={params.Hys}
                            showThresholdLines={showThresholdLines}
                            isDarkTheme={isDarkTheme}
                            onThemeToggle={onThemeToggle}
                        />
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
                                    <strong>進入條件：</strong> Ml1 - Hys &gt;
                                    Thresh1 <strong>且</strong> Ml2 + Hys &lt;
                                    Thresh2
                                </li>
                                <li>
                                    <strong>離開條件：</strong> Ml1 + Hys &lt;
                                    Thresh1 <strong>或</strong> Ml2 - Hys &gt;
                                    Thresh2
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
