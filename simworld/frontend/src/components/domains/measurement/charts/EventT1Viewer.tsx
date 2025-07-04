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
        // Event T1 參數狀態 - 基於 3GPP TS 38.331 Section 5.5.4.16 規範
        const [params, setParams] = useState<EventT1Params>(() => ({
            t1Threshold: initialParams.t1Threshold ?? 5000, // t1-Threshold in milliseconds - 測量時間門檻
            timeToTrigger: initialParams.timeToTrigger ?? 0, // 通常為 0，T1 has built-in time logic
            reportAmount: initialParams.reportAmount ?? 1, // 報告次數
            reportInterval: initialParams.reportInterval ?? 1000, // 報告間隔 (ms)
            reportOnLeave: initialParams.reportOnLeave ?? true, // 離開時報告
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

        // 計算 Event T1 條件狀態 - 基於 3GPP TS 38.331 Section 5.5.4.16 規範
        const eventStatus = useMemo(() => {
            // 模擬測量時間 Mt (可以是實際的測量持續時間)
            // 在此演示中，我們模擬測量過程的時間累積
            const currentMt = animationState.currentTime * 100 // 將動畫時間轉換為測量時間(ms)

            // T1 進入條件: Mt > t1-Threshold  
            const enterCondition = currentMt > params.t1Threshold
            // T1 離開條件: Mt ≤ t1-Threshold (當測量時間重置或降低時)
            const leaveCondition = currentMt <= params.t1Threshold
            // T1 事件觸發狀態
            const eventTriggered = enterCondition

            return {
                enterCondition, // T1 進入條件
                leaveCondition, // T1 離開條件
                eventTriggered,
                description: eventTriggered
                    ? 'T1 事件已觸發 - 測量時間超過門檻'
                    : '等待測量時間達到門檻',
                currentMt: currentMt,
                exceedTime: Math.max(0, currentMt - params.t1Threshold),
            }
        }, [params.t1Threshold, animationState.currentTime])
        
        // 動畫解說內容生成 - 基於測量時間和時間門檻，包含時間同步重要性教學
        const narrationContent = useMemo(() => {
            const currentTime = animationState.currentTime
            const currentMt = currentTime * 100 // 測量時間(ms)
            const threshold = params.t1Threshold
            
            // 判斷當前階段
            let phase = 'measuring'
            let phaseTitle = ''
            let description = ''
            let technicalNote = ''
            let nextAction = ''
            let timeSyncImportance = ''
            let practicalUseCase = ''
            
            if (currentMt <= threshold) {
                phase = 'measuring'
                phaseTitle = '📏 測量進行中 - 等待時間條件滿足'
                description = `測量時間 Mt (${currentMt.toFixed(0)}ms) 尚未超過時間門檻 (${threshold}ms)。系統正在累積測量時間，等待達到觸發條件。`
                
                timeSyncImportance = '⏰ 時間同步重要性：測量階段'
                practicalUseCase = `測量階段時間同步應用：
• 🎯 精確測量：確保測量時間的準確性和一致性
• 📡 多點協調：多個測量點的時間戳同步
• 🔄 週期性測量：定時測量任務的精確調度
• 📊 數據關聯：將測量結果與正確的時間窗口關聯
• 🛡️ 防止時間漂移：補償時鐘漂移對測量精度的影響`
                
                technicalNote = `3GPP 條件: Mt > t1-Threshold\\n當前 Mt: ${currentMt.toFixed(0)}ms ≤ 門檻: ${threshold}ms\\n\\n時間同步參數：\\n• 測量精度要求：±1ms\\n• 時鐘同步間隔：${params.reportInterval}ms\\n• 累積誤差容忍：<0.1%\\n• 時間校正頻率：每${params.reportAmount}次測量`
                nextAction = `繼續累積測量時間，還需 ${(threshold - currentMt).toFixed(0)}ms 達到門檻`
            } else {
                phase = 'triggered'
                phaseTitle = '✅ Event T1 已觸發 - 時間同步事件啟動'
                description = `測量時間 Mt (${currentMt.toFixed(0)}ms) 已超過時間門檻 (${threshold}ms)。T1 事件觸發，系統啟動時間同步相關的網路優化和服務調整。`
                
                timeSyncImportance = '🌐 時間同步重要性：網路服務優化'
                practicalUseCase = `時間同步服務優化應用：
• 🔄 網路同步：觸發網路時間協議(NTP)校正
• 📡 基站協調：同步多個基站的時間基準
• 🎯 精確定位：提高GPS/GNSS時間輔助精度
• 🚀 服務優化：調整時間敏感型服務的QoS
• 📊 性能監控：啟動高精度的網路性能測量
• 🛰️ 衛星同步：LEO衛星時間基準校正和軌道預測`
                
                technicalNote = `3GPP 條件: Mt > t1-Threshold\\n當前 Mt: ${currentMt.toFixed(0)}ms > 門檻: ${threshold}ms\\n超過時間: ${(currentMt - threshold).toFixed(0)}ms\\n\\n時間同步優化：\\n• 同步精度提升：從±10ms提升到±1ms\\n• 網路延遲補償：動態調整傳播延遲\\n• 時鐘漂移校正：每秒校正${((currentMt - threshold)/1000).toFixed(2)}ppm\\n• 服務優先級：提升時間敏感服務優先級`
                nextAction = '執行時間同步優化，提升網路服務品質和測量精度'
            }
            
            // 根據時間添加詳細的時間同步情境解說
            let scenarioContext = ''
            let mobilityScenario = ''
            if (currentTime < 25) {
                scenarioContext = '🚀 場景：網路啟動，建立基礎時間同步'
                mobilityScenario = '典型應用：5G基站初始化，建立與核心網的時間同步連接'
            } else if (currentTime < 75) {
                scenarioContext = '📡 場景：高精度時間同步需求觸發'
                mobilityScenario = '典型應用：高速移動場景下的換手時間協調，衛星通訊的時間校正'
            } else {
                scenarioContext = '🎯 場景：持續時間同步服務優化'
                mobilityScenario = '典型應用：工業IoT精密控制，金融交易時間戳認證'
            }
            
            return {
                phase,
                phaseTitle,
                description,
                technicalNote,
                nextAction,
                scenarioContext,
                mobilityScenario,
                timeSyncImportance,
                practicalUseCase,
                currentTime: currentTime.toFixed(1),
                currentMt: currentMt.toFixed(0),
                threshold: threshold.toString(),
                timeProgress: `${currentTime.toFixed(1)}s / 100s`,
                exceedTime: Math.max(0, currentMt - threshold).toFixed(0),
                measurementAccuracy: `±${(1 + currentTime/100).toFixed(1)}ms`,
            }
        }, [animationState.currentTime, params.t1Threshold, params.reportInterval, params.reportAmount])

        // 穩定的圖表 props
        const chartProps = useMemo(
            () => ({
                threshold: params.t1Threshold,
                currentTime: animationState.currentTime,
                showThresholdLines,
                isDarkTheme,
                onThemeToggle,
            }),
            [
                params.t1Threshold,
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
                                    t1-Threshold (測量時間門檻)
                                    <span className="control-unit">毫秒</span>
                                </label>
                                <input
                                    type="range"
                                    min="1000"
                                    max="20000"
                                    step="500"
                                    value={params.t1Threshold}
                                    onChange={(e) =>
                                        updateParam(
                                            't1Threshold',
                                            Number(e.target.value)
                                        )
                                    }
                                    className="control-slider"
                                />
                                <span className="control-value">
                                    {params.t1Threshold}ms
                                </span>
                            </div>

                            <div className="control-item">
                                <label className="control-label">
                                    當前測量時間 Mt
                                    <span className="control-unit">毫秒</span>
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    step="1"
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
                                    {(animationState.currentTime * 100).toFixed(0)}ms
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
                                    進入條件 T1:
                                </span>
                                <span
                                    className={`status-value ${
                                        eventStatus.enterCondition
                                            ? 'status-value--active'
                                            : ''
                                    }`}
                                >
                                    Mt &gt; t1-Threshold
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">
                                    離開條件 T1:
                                </span>
                                <span
                                    className={`status-value ${
                                        eventStatus.leaveCondition
                                            ? 'status-value--active'
                                            : ''
                                    }`}
                                >
                                    Mt ≤ t1-Threshold
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
                                    {eventStatus.description}
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">
                                    當前測量時間 Mt:
                                </span>
                                <span className="status-value">
                                    {eventStatus.currentMt.toFixed(0)}ms
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="status-label">
                                    超過門檻時間:
                                </span>
                                <span className="status-value">
                                    {eventStatus.exceedTime.toFixed(0)}ms
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
                showNarration,
                showTechnicalDetails,
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
                                                <div className="mobility-scenario">
                                                    {narrationContent.mobilityScenario}
                                                </div>
                                            </div>

                                            <div className="time-sync-stage">
                                                <h4>{narrationContent.timeSyncImportance}</h4>
                                                <div className="time-sync-use-case">
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
                                            <span className="metric-label">測量時間：</span>
                                            <span className="metric-value">{narrationContent.currentMt} ms</span>
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
                                    <strong>進入條件：</strong> Mt &gt; t1-Threshold
                                </li>
                                <li>
                                    <strong>離開條件：</strong> Mt ≤ t1-Threshold
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
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>應用場景：</h4>
                            <ul>
                                <li>
                                    <strong>時間同步：</strong>
                                    確保網路同步和時序控制
                                </li>
                                <li>
                                    <strong>測量時間觸發：</strong>
                                    基於測量時間門檻的事件觸發
                                </li>
                                <li>
                                    <strong>網路優化：</strong>
                                    基於時間測量的網路服務調整
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
