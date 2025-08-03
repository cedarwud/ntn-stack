/**
 * Enhanced A4 Event Viewer
 * 增強版 A4 信號強度測量事件查看器
 *
 * 整合功能：
 * 1. 增強版 A4 圖表
 * 2. 實時信號強度監測
 * 3. 位置補償參數配置
 * 4. 切換事件觸發歷史
 * 5. SIB19 位置補償狀態監控
 * 6. 衛星信號品質管理
 */

import React, { useState, useCallback, useEffect } from 'react'
import EnhancedA4Chart from './EnhancedA4Chart'
import { netstackFetch } from '../../../../config/api-config'
import './EnhancedA4Viewer.scss'

interface UEPosition {
    latitude: number
    longitude: number
    altitude: number
}

interface A4Parameters {
    a4_threshold: number // A4 信號強度門檻值 (dB)
    hysteresis: number // 遲滯值 (dB)
    time_to_trigger: number // 觸發時間 (ms)
}

interface EventTriggerRecord {
    timestamp: string
    trigger_details: unknown
    measurement_values: unknown
    compensation_status: string
    neighbor_satellite: string
}

interface SIB19PositionStatus {
    status: string
    compensation_enabled: boolean
    last_calculation_time: string
    position_accuracy_m: number
    satellites_used: number
    compensation_range_km: number
    signal_compensation_db_range: number[]
}

interface A4Statistics {
    total_measurements: number
    trigger_events: number
    trigger_rate: number
    avg_serving_rsrp: number
    avg_neighbor_rsrp: number
    avg_position_compensation: number
    avg_signal_compensation: number
    best_neighbor_distribution: Record<string, number>
}

const EnhancedA4Viewer: React.FC = () => {
    // 基本狀態
    const [isDarkTheme, setIsDarkTheme] = useState(true)
    const [useRealData, setUseRealData] = useState(true)
    const [isActive, setIsActive] = useState(true)
    const [updateInterval, setUpdateInterval] = useState(2000)

    // UE 位置
    const [uePosition, setUePosition] = useState<UEPosition>({
        latitude: 25.0478, // 台北101
        longitude: 121.5319,
        altitude: 100,
    })

    // A4 參數
    const [a4Params, setA4Params] = useState<A4Parameters>({
        a4_threshold: -90.0, // -90 dBm 門檻
        hysteresis: 2.0, // 2 dB 遲滯
        time_to_trigger: 160, // 160ms
    })

    // 觸發歷史和狀態
    const [triggerHistory, setTriggerHistory] = useState<EventTriggerRecord[]>(
        []
    )
    const [sib19Status, setSib19Status] = useState<SIB19PositionStatus | null>(
        null
    )
    const [a4Statistics, setA4Statistics] = useState<A4Statistics | null>(null)
    const [currentSignalQuality, setCurrentSignalQuality] = useState<{
        serving: number
        neighbor: number
    }>({ serving: 0, neighbor: 0 })

    // UI 狀態
    const [showParameterPanel, setShowParameterPanel] = useState(false)
    const [showHistoryPanel, setShowHistoryPanel] = useState(false)
    const [showCompensationPanel, setShowCompensationPanel] = useState(false)
    const [showStatisticsPanel, setShowStatisticsPanel] = useState(false)

    // 獲取 SIB19 位置補償狀態
    const fetchSIB19PositionStatus = useCallback(async () => {
        try {
            const response = await netstackFetch(
                '/api/measurement-events/sib19-status'
            )
            if (response.ok) {
                const data = await response.json()
                setSib19Status(data)
            }
        } catch (error) {
            console.error('❌ SIB19 位置補償狀態獲取失敗:', error)
        }
    }, [])

    // 獲取 A4 統計信息
    const fetchA4Statistics = useCallback(async () => {
        try {
            const response = await netstackFetch(
                '/api/measurement-events/A4/statistics'
            )
            if (response.ok) {
                const data = await response.json()
                setA4Statistics(data)
            }
        } catch (error) {
            console.error('❌ A4 統計信息獲取失敗:', error)
        }
    }, [])

    // 處理 A4 事件觸發
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleTriggerEvent = useCallback((eventData: any) => {
        const newRecord: EventTriggerRecord = {
            timestamp: new Date().toISOString(),
            trigger_details: eventData.trigger_details,
            measurement_values: eventData.measurement_values,
            compensation_status:
                Math.abs(eventData.position_compensation_m) > 1000
                    ? 'high'
                    : 'normal',
            neighbor_satellite: eventData.best_neighbor_id,
        }

        setTriggerHistory((prev) => [newRecord, ...prev.slice(0, 19)]) // 保留最近20條記錄
        setCurrentSignalQuality({
            serving: eventData.serving_rsrp,
            neighbor: eventData.compensated_neighbor_rsrp,
        })
    }, [])

    // 處理錯誤
    const handleError = useCallback((error: string) => {
        console.error('❌ A4 圖表錯誤:', error)
    }, [])

    // 切換主題
    const toggleTheme = useCallback(() => {
        setIsDarkTheme((prev) => !prev)
    }, [])

    // 切換數據模式
    const _toggleDataMode = useCallback(() => {
        setUseRealData((prev) => !prev)
    }, [])

    // 切換監測狀態
    const toggleMonitoring = useCallback(() => {
        setIsActive((prev) => !prev)
    }, [])

    // 重置 A4 參數
    const resetParameters = useCallback(() => {
        setA4Params({
            a4_threshold: -90.0,
            hysteresis: 2.0,
            time_to_trigger: 160,
        })
    }, [])

    // 載入預設位置
    const loadPresetLocation = useCallback((preset: string) => {
        const presets = {
            global_ref1: { latitude: 0.0478, longitude: 0.5319, altitude: 100 },
            global_ref2: { latitude: 0.6273, longitude: 0.3014, altitude: 50 },
            global_ref3: { latitude: 0.1477, longitude: 0.6736, altitude: 80 },
            global_ref4: { latitude: 0.0, longitude: 1.0, altitude: 10 },
            global_ref5: { latitude: 0.8, longitude: 0.0, altitude: 1500 },
            global_ref6: { latitude: 0.5, longitude: 0.5, altitude: 50 },
        }

        const newPosition = presets[preset as keyof typeof presets]
        if (newPosition) {
            setUePosition(newPosition)
        }
    }, [])

    // 預設 A4 信號強度場景
    const loadPresetScenario = useCallback((scenario: string) => {
        const scenarios = {
            'strong-signal': {
                a4_threshold: -80.0,
                hysteresis: 3.0,
                time_to_trigger: 160,
            }, // 強信號環境
            'normal-signal': {
                a4_threshold: -90.0,
                hysteresis: 2.0,
                time_to_trigger: 160,
            }, // 正常信號環境
            'weak-signal': {
                a4_threshold: -100.0,
                hysteresis: 1.0,
                time_to_trigger: 320,
            }, // 弱信號環境
            'handover-sensitive': {
                a4_threshold: -85.0,
                hysteresis: 0.5,
                time_to_trigger: 40,
            }, // 敏感切換
            'handover-stable': {
                a4_threshold: -95.0,
                hysteresis: 5.0,
                time_to_trigger: 640,
            }, // 穩定切換
            indoor: {
                a4_threshold: -105.0,
                hysteresis: 1.5,
                time_to_trigger: 256,
            }, // 室內環境
        }

        const newParams = scenarios[scenario as keyof typeof scenarios]
        if (newParams) {
            setA4Params(newParams)
        }
    }, [])

    // 清除觸發歷史
    const clearHistory = useCallback(() => {
        setTriggerHistory([])
    }, [])

    // 初始化
    useEffect(() => {
        fetchSIB19PositionStatus()
        fetchA4Statistics()

        const statusInterval = setInterval(fetchSIB19PositionStatus, 30000) // 每30秒更新一次
        const statsInterval = setInterval(fetchA4Statistics, 60000) // 每60秒更新一次

        return () => {
            clearInterval(statusInterval)
            clearInterval(statsInterval)
        }
    }, [fetchSIB19PositionStatus, fetchA4Statistics])

    return (
        <div
            className={`enhanced-a4-viewer ${
                isDarkTheme ? 'dark-theme' : 'light-theme'
            }`}
        >
            {/* 主標題和控制欄 */}
            <div className="viewer-header">
                <div className="title-section">
                    <h2>📡 增強版 A4 信號強度測量事件監測</h2>
                    <div className="subtitle">
                        基於 3GPP TS 38.331 規範 | SIB19 位置補償 |
                        鄰居衛星信號監測
                    </div>
                </div>

                <div className="control-buttons">
                    <button
                        className={`control-btn ${
                            showParameterPanel ? 'active' : ''
                        }`}
                        onClick={() =>
                            setShowParameterPanel(!showParameterPanel)
                        }
                        title="參數配置"
                    >
                        ⚙️
                    </button>
                    <button
                        className={`control-btn ${
                            showHistoryPanel ? 'active' : ''
                        }`}
                        onClick={() => setShowHistoryPanel(!showHistoryPanel)}
                        title="觸發歷史"
                    >
                        📊
                    </button>
                    <button
                        className={`control-btn ${
                            showCompensationPanel ? 'active' : ''
                        }`}
                        onClick={() =>
                            setShowCompensationPanel(!showCompensationPanel)
                        }
                        title="位置補償"
                    >
                        🗺️
                    </button>
                    <button
                        className={`control-btn ${
                            showStatisticsPanel ? 'active' : ''
                        }`}
                        onClick={() =>
                            setShowStatisticsPanel(!showStatisticsPanel)
                        }
                        title="統計信息"
                    >
                        📈
                    </button>
                    <button
                        className={`control-btn ${isActive ? 'active' : ''}`}
                        onClick={toggleMonitoring}
                        title={isActive ? '暫停監測' : '開始監測'}
                    >
                        {isActive ? '⏸️' : '▶️'}
                    </button>
                    <button
                        className="control-btn"
                        onClick={toggleTheme}
                        title="切換主題"
                    >
                        {isDarkTheme ? '🌙' : '☀️'}
                    </button>
                </div>
            </div>

            {/* 實時狀態指示 */}
            <div className="status-bar">
                <div className="status-item">
                    <span className="status-label">監測狀態:</span>
                    <span
                        className={`status-value ${
                            isActive ? 'active' : 'inactive'
                        }`}
                    >
                        {isActive ? '🟢 監測中' : '🔴 已暫停'}
                    </span>
                </div>
                <div className="status-item">
                    <span className="status-label">數據模式:</span>
                    <span className="status-value">
                        {useRealData ? '📡 真實數據' : '🎲 模擬數據'}
                    </span>
                </div>
                <div className="status-item">
                    <span className="status-label">服務信號:</span>
                    <span
                        className={`status-value ${
                            currentSignalQuality.serving > -90 ? 'good' : 'poor'
                        }`}
                    >
                        {currentSignalQuality.serving.toFixed(1)} dBm
                    </span>
                </div>
                <div className="status-item">
                    <span className="status-label">鄰居信號:</span>
                    <span
                        className={`status-value ${
                            currentSignalQuality.neighbor > -90
                                ? 'good'
                                : 'poor'
                        }`}
                    >
                        {currentSignalQuality.neighbor.toFixed(1)} dBm
                    </span>
                </div>
                <div className="status-item">
                    <span className="status-label">觸發次數:</span>
                    <span className="status-value">
                        {triggerHistory.length}
                    </span>
                </div>
            </div>

            {/* 側邊面板容器 */}
            <div className="viewer-content">
                {/* 主圖表區域 */}
                <div className="chart-container">
                    <EnhancedA4Chart
                        uePosition={uePosition}
                        a4Parameters={a4Params}
                        isActive={isActive}
                        updateInterval={updateInterval}
                        maxDataPoints={100}
                        onTriggerEvent={handleTriggerEvent}
                        onError={handleError}
                        theme={isDarkTheme ? 'dark' : 'light'}
                    />
                </div>

                {/* 參數配置面板 */}
                {showParameterPanel && (
                    <div className="side-panel parameter-panel">
                        <div className="panel-header">
                            <h3>📋 A4 參數配置</h3>
                            <button
                                className="close-btn"
                                onClick={() => setShowParameterPanel(false)}
                            >
                                ✕
                            </button>
                        </div>

                        <div className="panel-content">
                            {/* UE 位置配置 */}
                            <div className="config-section">
                                <h4>📍 UE 位置</h4>
                                <div className="input-group">
                                    <label>緯度 (°)</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        value={uePosition.latitude}
                                        onChange={(e) =>
                                            setUePosition((prev) => ({
                                                ...prev,
                                                latitude:
                                                    parseFloat(
                                                        e.target.value
                                                    ) || 0,
                                            }))
                                        }
                                    />
                                </div>
                                <div className="input-group">
                                    <label>經度 (°)</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        value={uePosition.longitude}
                                        onChange={(e) =>
                                            setUePosition((prev) => ({
                                                ...prev,
                                                longitude:
                                                    parseFloat(
                                                        e.target.value
                                                    ) || 0,
                                            }))
                                        }
                                    />
                                </div>
                                <div className="input-group">
                                    <label>高度 (m)</label>
                                    <input
                                        type="number"
                                        value={uePosition.altitude}
                                        onChange={(e) =>
                                            setUePosition((prev) => ({
                                                ...prev,
                                                altitude:
                                                    parseInt(e.target.value) ||
                                                    0,
                                            }))
                                        }
                                    />
                                </div>

                                {/* 預設位置 */}
                                <div className="preset-buttons">
                                    <button
                                        onClick={() =>
                                            loadPresetLocation('taipei')
                                        }
                                    >
                                        台北
                                    </button>
                                    <button
                                        onClick={() =>
                                            loadPresetLocation('kaohsiung')
                                        }
                                    >
                                        高雄
                                    </button>
                                    <button
                                        onClick={() =>
                                            loadPresetLocation('taichung')
                                        }
                                    >
                                        台中
                                    </button>
                                    <button
                                        onClick={() =>
                                            loadPresetLocation('offshore')
                                        }
                                    >
                                        離岸
                                    </button>
                                    <button
                                        onClick={() =>
                                            loadPresetLocation('mountain')
                                        }
                                    >
                                        山區
                                    </button>
                                    <button
                                        onClick={() =>
                                            loadPresetLocation('rural')
                                        }
                                    >
                                        鄉村
                                    </button>
                                </div>
                            </div>

                            {/* A4 參數配置 */}
                            <div className="config-section">
                                <h4>📡 A4 事件參數</h4>
                                <div className="input-group">
                                    <label>A4 門檻 (dBm)</label>
                                    <input
                                        type="number"
                                        min="-120"
                                        max="-50"
                                        step="0.5"
                                        value={a4Params.a4_threshold}
                                        onChange={(e) =>
                                            setA4Params((prev) => ({
                                                ...prev,
                                                a4_threshold:
                                                    parseFloat(
                                                        e.target.value
                                                    ) || -90,
                                            }))
                                        }
                                    />
                                    <small>
                                        鄰居信號超過服務信號此值時觸發
                                    </small>
                                </div>
                                <div className="input-group">
                                    <label>遲滯值 (dB)</label>
                                    <input
                                        type="number"
                                        min="0"
                                        max="10"
                                        step="0.1"
                                        value={a4Params.hysteresis}
                                        onChange={(e) =>
                                            setA4Params((prev) => ({
                                                ...prev,
                                                hysteresis:
                                                    parseFloat(
                                                        e.target.value
                                                    ) || 2.0,
                                            }))
                                        }
                                    />
                                    <small>防止頻繁切換的遲滯值</small>
                                </div>
                                <div className="input-group">
                                    <label>觸發時間 (ms)</label>
                                    <select
                                        value={a4Params.time_to_trigger}
                                        onChange={(e) =>
                                            setA4Params((prev) => ({
                                                ...prev,
                                                time_to_trigger: parseInt(
                                                    e.target.value
                                                ),
                                            }))
                                        }
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
                                </div>

                                {/* 預設場景 */}
                                <div className="preset-scenarios">
                                    <h5>預設場景</h5>
                                    <div className="scenario-buttons">
                                        <button
                                            onClick={() =>
                                                loadPresetScenario(
                                                    'strong-signal'
                                                )
                                            }
                                        >
                                            強信號環境
                                        </button>
                                        <button
                                            onClick={() =>
                                                loadPresetScenario(
                                                    'normal-signal'
                                                )
                                            }
                                        >
                                            正常信號環境
                                        </button>
                                        <button
                                            onClick={() =>
                                                loadPresetScenario(
                                                    'weak-signal'
                                                )
                                            }
                                        >
                                            弱信號環境
                                        </button>
                                        <button
                                            onClick={() =>
                                                loadPresetScenario(
                                                    'handover-sensitive'
                                                )
                                            }
                                        >
                                            敏感切換
                                        </button>
                                        <button
                                            onClick={() =>
                                                loadPresetScenario(
                                                    'handover-stable'
                                                )
                                            }
                                        >
                                            穩定切換
                                        </button>
                                        <button
                                            onClick={() =>
                                                loadPresetScenario('indoor')
                                            }
                                        >
                                            室內環境
                                        </button>
                                    </div>
                                </div>

                                <button
                                    className="reset-btn"
                                    onClick={resetParameters}
                                >
                                    🔄 重置參數
                                </button>
                            </div>

                            {/* 監測控制 */}
                            <div className="config-section">
                                <h4>🎛️ 監測控制</h4>
                                <div className="input-group">
                                    <label>更新間隔 (ms)</label>
                                    <select
                                        value={updateInterval}
                                        onChange={(e) =>
                                            setUpdateInterval(
                                                parseInt(e.target.value)
                                            )
                                        }
                                    >
                                        <option value={1000}>1000 (1秒)</option>
                                        <option value={2000}>2000 (2秒)</option>
                                        <option value={3000}>3000 (3秒)</option>
                                        <option value={5000}>5000 (5秒)</option>
                                    </select>
                                </div>
                                <div className="checkbox-group">
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={useRealData}
                                            onChange={(e) =>
                                                setUseRealData(e.target.checked)
                                            }
                                        />
                                        使用真實數據
                                    </label>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={isActive}
                                            onChange={(e) =>
                                                setIsActive(e.target.checked)
                                            }
                                        />
                                        啟用監測
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* 觸發歷史面板 */}
                {showHistoryPanel && (
                    <div className="side-panel history-panel">
                        <div className="panel-header">
                            <h3>📊 觸發歷史</h3>
                            <div className="panel-controls">
                                <button
                                    className="clear-btn"
                                    onClick={clearHistory}
                                    title="清除歷史"
                                >
                                    🗑️
                                </button>
                                <button
                                    className="close-btn"
                                    onClick={() => setShowHistoryPanel(false)}
                                >
                                    ✕
                                </button>
                            </div>
                        </div>

                        <div className="panel-content">
                            <div className="history-stats">
                                <div className="stat-item">
                                    <span className="stat-label">
                                        總觸發次數:
                                    </span>
                                    <span className="stat-value">
                                        {triggerHistory.length}
                                    </span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">
                                        當前服務信號:
                                    </span>
                                    <span className="stat-value">
                                        {currentSignalQuality.serving.toFixed(
                                            1
                                        )}{' '}
                                        dBm
                                    </span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">
                                        當前鄰居信號:
                                    </span>
                                    <span className="stat-value">
                                        {currentSignalQuality.neighbor.toFixed(
                                            1
                                        )}{' '}
                                        dBm
                                    </span>
                                </div>
                            </div>

                            <div className="history-list">
                                {triggerHistory.length === 0 ? (
                                    <div className="no-data">暫無觸發記錄</div>
                                ) : (
                                    triggerHistory.map((record, index) => (
                                        <div
                                            key={index}
                                            className="history-item"
                                        >
                                            <div className="history-time">
                                                {new Date(
                                                    record.timestamp
                                                ).toLocaleTimeString()}
                                            </div>
                                            <div className="history-details">
                                                <div>
                                                    服務 RSRP:{' '}
                                                    {record.trigger_details?.serving_rsrp?.toFixed(
                                                        1
                                                    )}{' '}
                                                    dBm
                                                </div>
                                                <div>
                                                    原始鄰居 RSRP:{' '}
                                                    {record.trigger_details?.original_neighbor_rsrp?.toFixed(
                                                        1
                                                    )}{' '}
                                                    dBm
                                                </div>
                                                <div>
                                                    補償後 RSRP:{' '}
                                                    {record.trigger_details?.compensated_neighbor_rsrp?.toFixed(
                                                        1
                                                    )}{' '}
                                                    dBm
                                                </div>
                                                <div>
                                                    位置補償:{' '}
                                                    {(
                                                        record.trigger_details
                                                            ?.position_compensation_m /
                                                        1000
                                                    )?.toFixed(2)}{' '}
                                                    km
                                                </div>
                                                <div>
                                                    信號補償:{' '}
                                                    {record.trigger_details?.signal_compensation_db?.toFixed(
                                                        1
                                                    )}{' '}
                                                    dB
                                                </div>
                                                <div>
                                                    鄰居衛星:{' '}
                                                    {record.neighbor_satellite}
                                                </div>
                                                <div className="trigger-conditions">
                                                    補償狀態:{' '}
                                                    {record.compensation_status ===
                                                    'high'
                                                        ? '⚠️ 高補償'
                                                        : '✅ 正常'}
                                                    觸發條件:{' '}
                                                    {record.trigger_details
                                                        ?.condition_met
                                                        ? '✅'
                                                        : '❌'}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* 位置補償面板 */}
                {showCompensationPanel && (
                    <div className="side-panel compensation-panel">
                        <div className="panel-header">
                            <h3>🗺️ 位置補償狀態</h3>
                            <button
                                className="close-btn"
                                onClick={() => setShowCompensationPanel(false)}
                            >
                                ✕
                            </button>
                        </div>

                        <div className="panel-content">
                            {sib19Status ? (
                                <div className="compensation-status">
                                    <div className="status-item">
                                        <span className="status-label">
                                            SIB19 狀態:
                                        </span>
                                        <span
                                            className={`status-value ${sib19Status.status}`}
                                        >
                                            {sib19Status.status}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            位置補償:
                                        </span>
                                        <span
                                            className={`status-value ${
                                                sib19Status.compensation_enabled
                                                    ? 'enabled'
                                                    : 'disabled'
                                            }`}
                                        >
                                            {sib19Status.compensation_enabled
                                                ? '✅ 啟用'
                                                : '❌ 停用'}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            最後計算:
                                        </span>
                                        <span className="status-value">
                                            {new Date(
                                                sib19Status.last_calculation_time
                                            ).toLocaleTimeString()}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            位置精度:
                                        </span>
                                        <span className="status-value">
                                            {sib19Status.position_accuracy_m.toFixed(
                                                0
                                            )}{' '}
                                            m
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            使用衛星:
                                        </span>
                                        <span className="status-value">
                                            {sib19Status.satellites_used}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            補償範圍:
                                        </span>
                                        <span className="status-value">
                                            ±
                                            {sib19Status.compensation_range_km.toFixed(
                                                1
                                            )}{' '}
                                            km
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            信號補償範圍:
                                        </span>
                                        <span className="status-value">
                                            {sib19Status.signal_compensation_db_range[0].toFixed(
                                                1
                                            )}{' '}
                                            ~
                                            {sib19Status.signal_compensation_db_range[1].toFixed(
                                                1
                                            )}{' '}
                                            dB
                                        </span>
                                    </div>
                                </div>
                            ) : (
                                <div className="loading-status">
                                    載入位置補償狀態中...
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* 統計信息面板 */}
                {showStatisticsPanel && (
                    <div className="side-panel statistics-panel">
                        <div className="panel-header">
                            <h3>📈 統計信息</h3>
                            <button
                                className="close-btn"
                                onClick={() => setShowStatisticsPanel(false)}
                            >
                                ✕
                            </button>
                        </div>

                        <div className="panel-content">
                            {a4Statistics ? (
                                <div className="statistics-display">
                                    <div className="stats-section">
                                        <h4>📊 測量統計</h4>
                                        <div className="stat-item">
                                            <span className="stat-label">
                                                總測量次數:
                                            </span>
                                            <span className="stat-value">
                                                {
                                                    a4Statistics.total_measurements
                                                }
                                            </span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">
                                                觸發事件:
                                            </span>
                                            <span className="stat-value">
                                                {a4Statistics.trigger_events}
                                            </span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">
                                                觸發率:
                                            </span>
                                            <span className="stat-value">
                                                {(
                                                    a4Statistics.trigger_rate *
                                                    100
                                                ).toFixed(1)}
                                                %
                                            </span>
                                        </div>
                                    </div>

                                    <div className="stats-section">
                                        <h4>📡 信號統計</h4>
                                        <div className="stat-item">
                                            <span className="stat-label">
                                                平均服務 RSRP:
                                            </span>
                                            <span className="stat-value">
                                                {a4Statistics.avg_serving_rsrp.toFixed(
                                                    1
                                                )}{' '}
                                                dBm
                                            </span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">
                                                平均鄰居 RSRP:
                                            </span>
                                            <span className="stat-value">
                                                {a4Statistics.avg_neighbor_rsrp.toFixed(
                                                    1
                                                )}{' '}
                                                dBm
                                            </span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">
                                                平均位置補償:
                                            </span>
                                            <span className="stat-value">
                                                {(
                                                    a4Statistics.avg_position_compensation /
                                                    1000
                                                ).toFixed(2)}{' '}
                                                km
                                            </span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">
                                                平均信號補償:
                                            </span>
                                            <span className="stat-value">
                                                {a4Statistics.avg_signal_compensation.toFixed(
                                                    1
                                                )}{' '}
                                                dB
                                            </span>
                                        </div>
                                    </div>

                                    <div className="stats-section">
                                        <h4>🛰️ 鄰居衛星分布</h4>
                                        {Object.entries(
                                            a4Statistics.best_neighbor_distribution
                                        ).map(([satellite, count]) => (
                                            <div
                                                key={satellite}
                                                className="stat-item"
                                            >
                                                <span className="stat-label">
                                                    {satellite}:
                                                </span>
                                                <span className="stat-value">
                                                    {count}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="loading-status">
                                    載入統計信息中...
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default EnhancedA4Viewer
