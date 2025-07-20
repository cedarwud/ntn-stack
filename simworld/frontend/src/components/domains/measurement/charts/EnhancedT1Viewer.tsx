/**
 * Enhanced T1 Event Viewer
 * 增強版 T1 時間條件測量事件查看器
 * 
 * 整合功能：
 * 1. 增強版 T1 圖表
 * 2. 實時數據控制面板
 * 3. 參數配置界面
 * 4. 事件觸發歷史
 * 5. 時間同步狀態監控
 * 6. 服務時間窗口管理
 */

import React, { useState, useCallback, useEffect } from 'react'
import EnhancedT1Chart from './EnhancedT1Chart'
import { netstackFetch } from '../../../../config/api-config'
import './EnhancedT1Viewer.scss'

interface UEPosition {
    latitude: number
    longitude: number
    altitude: number
}

interface T1Parameters {
    t1_threshold: number // 時間門檻 (秒)
    duration: number // 要求持續時間 (秒)
    time_to_trigger: number // 觸發時間 (ms)
}

interface EventTriggerRecord {
    timestamp: string
    trigger_details: any
    measurement_values: any
    sync_status: string
}

interface SIB19Status {
    status: string
    broadcast_id: string
    broadcast_time: string
    validity_hours: number
    time_to_expiry_hours: number
    satellites_count: number
    time_sync_accuracy_ms: number
}

const EnhancedT1Viewer: React.FC = () => {
    // 基本狀態
    const [isDarkTheme, setIsDarkTheme] = useState(true)
    const [useRealData, setUseRealData] = useState(true)
    const [showThresholdLines, setShowThresholdLines] = useState(true)
    const [autoUpdate, setAutoUpdate] = useState(true)
    
    // UE 位置
    const [uePosition, setUePosition] = useState<UEPosition>({
        latitude: 25.0478,  // 台北101
        longitude: 121.5319,
        altitude: 100
    })
    
    // T1 參數
    const [t1Params, setT1Params] = useState<T1Parameters>({
        t1_threshold: 300.0,   // 5分鐘
        duration: 60.0,        // 1分鐘
        time_to_trigger: 160   // 160ms
    })
    
    // 觸發歷史和狀態
    const [triggerHistory, setTriggerHistory] = useState<EventTriggerRecord[]>([])
    const [sib19Status, setSib19Status] = useState<SIB19Status | null>(null)
    const [currentSyncAccuracy, setCurrentSyncAccuracy] = useState<number>(0)
    
    // UI 狀態
    const [showParameterPanel, setShowParameterPanel] = useState(false)
    const [showHistoryPanel, setShowHistoryPanel] = useState(false)
    const [showSyncPanel, setShowSyncPanel] = useState(false)

    // 獲取 SIB19 狀態
    const fetchSIB19Status = useCallback(async () => {
        try {
            const response = await netstackFetch('/api/measurement-events/sib19-status')
            if (response.ok) {
                const data = await response.json()
                setSib19Status(data)
            }
        } catch (error) {
            console.error('❌ SIB19 狀態獲取失敗:', error)
        }
    }, [])

    // 處理事件觸發
    const handleTriggerEvent = useCallback((eventData: any) => {
        const newRecord: EventTriggerRecord = {
            timestamp: new Date().toISOString(),
            trigger_details: eventData.trigger_details,
            measurement_values: eventData.measurement_values,
            sync_status: eventData.trigger_details.sync_accuracy_ms < 50 ? 'good' : 'poor'
        }
        
        setTriggerHistory(prev => [newRecord, ...prev.slice(0, 19)]) // 保留最近20條記錄
        setCurrentSyncAccuracy(eventData.trigger_details.sync_accuracy_ms)
    }, [])

    // 切換主題
    const toggleTheme = useCallback(() => {
        setIsDarkTheme(prev => !prev)
    }, [])

    // 切換數據模式
    const toggleDataMode = useCallback(() => {
        setUseRealData(prev => !prev)
    }, [])

    // 重置 T1 參數
    const resetParameters = useCallback(() => {
        setT1Params({
            t1_threshold: 300.0,
            duration: 60.0,
            time_to_trigger: 160
        })
    }, [])

    // 載入預設位置
    const loadPresetLocation = useCallback((preset: string) => {
        const presets = {
            taipei: { latitude: 25.0478, longitude: 121.5319, altitude: 100 },
            kaohsiung: { latitude: 22.6273, longitude: 120.3014, altitude: 50 },
            taichung: { latitude: 24.1477, longitude: 120.6736, altitude: 80 },
            offshore: { latitude: 24.0, longitude: 122.0, altitude: 10 }
        }
        
        const newPosition = presets[preset as keyof typeof presets]
        if (newPosition) {
            setUePosition(newPosition)
        }
    }, [])

    // 預設 T1 場景
    const loadPresetScenario = useCallback((scenario: string) => {
        const scenarios = {
            'short-session': { t1_threshold: 60.0, duration: 30.0, time_to_trigger: 160 },      // 短會話
            'normal-session': { t1_threshold: 300.0, duration: 60.0, time_to_trigger: 160 },   // 正常會話
            'long-session': { t1_threshold: 1800.0, duration: 300.0, time_to_trigger: 320 },   // 長會話
            'critical-timing': { t1_threshold: 10.0, duration: 5.0, time_to_trigger: 40 }      // 關鍵時序
        }
        
        const newParams = scenarios[scenario as keyof typeof scenarios]
        if (newParams) {
            setT1Params(newParams)
        }
    }, [])

    // 初始化
    useEffect(() => {
        fetchSIB19Status()
        const interval = setInterval(fetchSIB19Status, 30000) // 每30秒更新一次
        return () => clearInterval(interval)
    }, [fetchSIB19Status])

    return (
        <div className={`enhanced-t1-viewer ${isDarkTheme ? 'dark-theme' : 'light-theme'}`}>
            {/* 主標題和控制欄 */}
            <div className="viewer-header">
                <div className="title-section">
                    <h2>⏰ 增強版 T1 時間條件測量事件監測</h2>
                    <div className="subtitle">
                        基於 3GPP TS 38.331 規範 | GNSS 時間同步 | 服務時間窗口管理
                    </div>
                </div>
                
                <div className="control-buttons">
                    <button 
                        className={`control-btn ${showParameterPanel ? 'active' : ''}`}
                        onClick={() => setShowParameterPanel(!showParameterPanel)}
                        title="參數配置"
                    >
                        ⚙️
                    </button>
                    <button 
                        className={`control-btn ${showHistoryPanel ? 'active' : ''}`}
                        onClick={() => setShowHistoryPanel(!showHistoryPanel)}
                        title="觸發歷史"
                    >
                        📊
                    </button>
                    <button 
                        className={`control-btn ${showSyncPanel ? 'active' : ''}`}
                        onClick={() => setShowSyncPanel(!showSyncPanel)}
                        title="同步狀態"
                    >
                        🕐
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

            {/* 側邊面板容器 */}
            <div className="viewer-content">
                {/* 主圖表區域 */}
                <div className="chart-container">
                    <EnhancedT1Chart
                        t1Threshold={t1Params.t1_threshold}
                        requiredDuration={t1Params.duration}
                        timeToTrigger={t1Params.time_to_trigger}
                        uePosition={uePosition}
                        showThresholdLines={showThresholdLines}
                        isDarkTheme={isDarkTheme}
                        useRealData={useRealData}
                        autoUpdate={autoUpdate}
                        updateInterval={2000}
                        onThemeToggle={toggleTheme}
                        onDataModeToggle={toggleDataMode}
                        onTriggerEvent={handleTriggerEvent}
                    />
                </div>

                {/* 參數配置面板 */}
                {showParameterPanel && (
                    <div className="side-panel parameter-panel">
                        <div className="panel-header">
                            <h3>📋 T1 參數配置</h3>
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
                                        onChange={(e) => setUePosition(prev => ({
                                            ...prev,
                                            latitude: parseFloat(e.target.value) || 0
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>經度 (°)</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        value={uePosition.longitude}
                                        onChange={(e) => setUePosition(prev => ({
                                            ...prev,
                                            longitude: parseFloat(e.target.value) || 0
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>高度 (m)</label>
                                    <input
                                        type="number"
                                        value={uePosition.altitude}
                                        onChange={(e) => setUePosition(prev => ({
                                            ...prev,
                                            altitude: parseInt(e.target.value) || 0
                                        }))}
                                    />
                                </div>
                                
                                {/* 預設位置 */}
                                <div className="preset-buttons">
                                    <button onClick={() => loadPresetLocation('taipei')}>台北</button>
                                    <button onClick={() => loadPresetLocation('kaohsiung')}>高雄</button>
                                    <button onClick={() => loadPresetLocation('taichung')}>台中</button>
                                    <button onClick={() => loadPresetLocation('offshore')}>離岸</button>
                                </div>
                            </div>

                            {/* T1 參數配置 */}
                            <div className="config-section">
                                <h4>⏰ T1 事件參數</h4>
                                <div className="input-group">
                                    <label>時間門檻 (秒)</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="3600"
                                        step="1"
                                        value={t1Params.t1_threshold}
                                        onChange={(e) => setT1Params(prev => ({
                                            ...prev,
                                            t1_threshold: parseFloat(e.target.value) || 300
                                        }))}
                                    />
                                    <small>服務經過時間超過此值時觸發</small>
                                </div>
                                <div className="input-group">
                                    <label>要求持續時間 (秒)</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="300"
                                        step="1"
                                        value={t1Params.duration}
                                        onChange={(e) => setT1Params(prev => ({
                                            ...prev,
                                            duration: parseFloat(e.target.value) || 60
                                        }))}
                                    />
                                    <small>剩餘服務時間須大於此值</small>
                                </div>
                                <div className="input-group">
                                    <label>觸發時間 (ms)</label>
                                    <select
                                        value={t1Params.time_to_trigger}
                                        onChange={(e) => setT1Params(prev => ({
                                            ...prev,
                                            time_to_trigger: parseInt(e.target.value)
                                        }))}
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
                                        <button onClick={() => loadPresetScenario('short-session')}>
                                            短會話 (1分鐘)
                                        </button>
                                        <button onClick={() => loadPresetScenario('normal-session')}>
                                            正常會話 (5分鐘)
                                        </button>
                                        <button onClick={() => loadPresetScenario('long-session')}>
                                            長會話 (30分鐘)
                                        </button>
                                        <button onClick={() => loadPresetScenario('critical-timing')}>
                                            關鍵時序 (10秒)
                                        </button>
                                    </div>
                                </div>
                                
                                <button className="reset-btn" onClick={resetParameters}>
                                    🔄 重置參數
                                </button>
                            </div>

                            {/* 顯示選項 */}
                            <div className="config-section">
                                <h4>🎨 顯示選項</h4>
                                <div className="checkbox-group">
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={showThresholdLines}
                                            onChange={(e) => setShowThresholdLines(e.target.checked)}
                                        />
                                        顯示門檻線
                                    </label>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={useRealData}
                                            onChange={(e) => setUseRealData(e.target.checked)}
                                        />
                                        使用真實數據
                                    </label>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={autoUpdate}
                                            onChange={(e) => setAutoUpdate(e.target.checked)}
                                        />
                                        自動更新
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
                            <button 
                                className="close-btn"
                                onClick={() => setShowHistoryPanel(false)}
                            >
                                ✕
                            </button>
                        </div>
                        
                        <div className="panel-content">
                            <div className="history-stats">
                                <div className="stat-item">
                                    <span className="stat-label">總觸發次數:</span>
                                    <span className="stat-value">{triggerHistory.length}</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">當前同步精度:</span>
                                    <span className="stat-value">{currentSyncAccuracy.toFixed(2)}ms</span>
                                </div>
                            </div>
                            
                            <div className="history-list">
                                {triggerHistory.length === 0 ? (
                                    <div className="no-data">暫無觸發記錄</div>
                                ) : (
                                    triggerHistory.map((record, index) => (
                                        <div key={index} className="history-item">
                                            <div className="history-time">
                                                {new Date(record.timestamp).toLocaleTimeString()}
                                            </div>
                                            <div className="history-details">
                                                <div>經過時間: {record.measurement_values?.elapsed_time?.toFixed(1)}s</div>
                                                <div>剩餘時間: {record.measurement_values?.remaining_service_time?.toFixed(1)}s</div>
                                                <div>同步精度: {record.trigger_details?.sync_accuracy_ms?.toFixed(2)}ms</div>
                                                <div className="trigger-conditions">
                                                    時間條件: {record.trigger_details?.threshold_condition_met ? '✅' : '❌'}
                                                    持續條件: {record.trigger_details?.duration_condition_met ? '✅' : '❌'}
                                                    同步狀態: {record.sync_status === 'good' ? '✅' : '⚠️'}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* 同步狀態面板 */}
                {showSyncPanel && (
                    <div className="side-panel sync-panel">
                        <div className="panel-header">
                            <h3>🕐 時間同步狀態</h3>
                            <button 
                                className="close-btn"
                                onClick={() => setShowSyncPanel(false)}
                            >
                                ✕
                            </button>
                        </div>
                        
                        <div className="panel-content">
                            {sib19Status ? (
                                <div className="sync-status">
                                    <div className="status-item">
                                        <span className="status-label">SIB19 狀態:</span>
                                        <span className={`status-value ${sib19Status.status}`}>
                                            {sib19Status.status}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">廣播 ID:</span>
                                        <span className="status-value">{sib19Status.broadcast_id}</span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">廣播時間:</span>
                                        <span className="status-value">
                                            {new Date(sib19Status.broadcast_time).toLocaleString()}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">有效期:</span>
                                        <span className="status-value">{sib19Status.validity_hours}小時</span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">剩餘時間:</span>
                                        <span className="status-value">
                                            {sib19Status.time_to_expiry_hours.toFixed(1)}小時
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">衛星數量:</span>
                                        <span className="status-value">{sib19Status.satellites_count}</span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">同步精度:</span>
                                        <span className={`status-value ${sib19Status.time_sync_accuracy_ms < 50 ? 'good' : 'warning'}`}>
                                            {sib19Status.time_sync_accuracy_ms.toFixed(2)}ms
                                        </span>
                                    </div>
                                </div>
                            ) : (
                                <div className="loading-status">載入同步狀態中...</div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default EnhancedT1Viewer