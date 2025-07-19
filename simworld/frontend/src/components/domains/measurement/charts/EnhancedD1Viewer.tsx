/**
 * Enhanced D1 Event Viewer
 * 增強版 D1 雙重距離測量事件查看器
 * 
 * 整合功能：
 * 1. 增強版 D1 圖表
 * 2. 實時數據控制面板
 * 3. 參數配置界面
 * 4. 事件觸發歷史
 * 5. 智能服務衛星選擇視覺化
 * 6. 多重參考位置支援
 */

import React, { useState, useCallback, useEffect } from 'react'
import EnhancedD1Chart from './EnhancedD1Chart'
import { netstackFetch } from '../../../../config/api-config'
import './EnhancedD1Viewer.scss'

interface UEPosition {
    latitude: number
    longitude: number
    altitude: number
}

interface D1Parameters {
    thresh1: number // 服務衛星距離門檻 (m)
    thresh2: number // 固定參考位置距離門檻 (m)
    hysteresis: number // 遲滯值 (m)
    time_to_trigger: number // 觸發時間 (ms)
    min_elevation_angle: number // 最小仰角 (度)
    serving_satellite_id: string // 指定服務衛星
    reference_location_id: string // 參考位置 ID
    time_window_ms: number // 時間窗口過濾 (ms)
}

interface EventTriggerRecord {
    timestamp: string
    trigger_details: any
    measurement_values: any
    satellite_id: string
}

const EnhancedD1Viewer: React.FC = () => {
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
    
    // D1 參數
    const [d1Params, setD1Params] = useState<D1Parameters>({
        thresh1: 10000,    // 10km
        thresh2: 5000,     // 5km
        hysteresis: 500,   // 500m
        time_to_trigger: 160, // 160ms
        min_elevation_angle: 5.0, // 5度
        serving_satellite_id: '',  // 自動選擇
        reference_location_id: 'default', // 預設參考位置
        time_window_ms: 1000 // 1秒
    })
    
    // 觸發歷史
    const [triggerHistory, setTriggerHistory] = useState<EventTriggerRecord[]>([])
    const [availableSatellites, setAvailableSatellites] = useState<any[]>([])
    const [currentServingSatellite, setCurrentServingSatellite] = useState<string>('')
    
    // UI 狀態
    const [showParameterPanel, setShowParameterPanel] = useState(false)
    const [showHistoryPanel, setShowHistoryPanel] = useState(false)
    const [showSatelliteInfo, setShowSatelliteInfo] = useState(false)

    // 獲取可用衛星列表
    const fetchAvailableSatellites = useCallback(async () => {
        try {
            const response = await netstackFetch('/api/measurement-events/orbit-data/satellites?constellation=starlink')
            if (response.ok) {
                const data = await response.json()
                setAvailableSatellites(data.satellites || [])
            }
        } catch (error) {
            console.error('❌ 衛星列表獲取失敗:', error)
        }
    }, [])

    // 處理事件觸發
    const handleTriggerEvent = useCallback((eventData: any) => {
        const newRecord: EventTriggerRecord = {
            timestamp: new Date().toISOString(),
            trigger_details: eventData.trigger_details,
            measurement_values: eventData.measurement_values,
            satellite_id: eventData.measurement_values?.serving_satellite || 'unknown'
        }
        
        setTriggerHistory(prev => [newRecord, ...prev.slice(0, 19)]) // 保留最近20條記錄
        setCurrentServingSatellite(newRecord.satellite_id)
    }, [])

    // 切換主題
    const toggleTheme = useCallback(() => {
        setIsDarkTheme(prev => !prev)
    }, [])

    // 切換數據模式
    const toggleDataMode = useCallback(() => {
        setUseRealData(prev => !prev)
    }, [])

    // 重置 D1 參數
    const resetParameters = useCallback(() => {
        setD1Params({
            thresh1: 10000,
            thresh2: 5000,
            hysteresis: 500,
            time_to_trigger: 160,
            min_elevation_angle: 5.0,
            serving_satellite_id: '',
            reference_location_id: 'default',
            time_window_ms: 1000
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

    // 初始化
    useEffect(() => {
        fetchAvailableSatellites()
    }, [fetchAvailableSatellites])

    return (
        <div className={`enhanced-d1-viewer ${isDarkTheme ? 'dark-theme' : 'light-theme'}`}>
            {/* 主標題和控制欄 */}
            <div className="viewer-header">
                <div className="title-section">
                    <h2>🎯 增強版 D1 雙重距離測量事件監測</h2>
                    <div className="subtitle">
                        基於 3GPP TS 38.331 規範 | 智能衛星選擇算法 | 論文研究級數據精度
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
                        className={`control-btn ${showSatelliteInfo ? 'active' : ''}`}
                        onClick={() => setShowSatelliteInfo(!showSatelliteInfo)}
                        title="衛星資訊"
                    >
                        🛰️
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
                    <EnhancedD1Chart
                        thresh1={d1Params.thresh1}
                        thresh2={d1Params.thresh2}
                        hysteresis={d1Params.hysteresis}
                        uePosition={uePosition}
                        minElevationAngle={d1Params.min_elevation_angle}
                        servingSatelliteId={d1Params.serving_satellite_id}
                        referenceLocationId={d1Params.reference_location_id}
                        timeWindowMs={d1Params.time_window_ms}
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
                            <h3>📋 D1 參數配置</h3>
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

                            {/* D1 參數配置 */}
                            <div className="config-section">
                                <h4>🎯 D1 事件參數</h4>
                                <div className="input-group">
                                    <label>服務衛星距離門檻 (km)</label>
                                    <input
                                        type="number"
                                        min="5"
                                        max="50"
                                        step="0.5"
                                        value={d1Params.thresh1 / 1000}
                                        onChange={(e) => setD1Params(prev => ({
                                            ...prev,
                                            thresh1: parseFloat(e.target.value) * 1000 || 10000
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>參考位置距離門檻 (km)</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="20"
                                        step="0.1"
                                        value={d1Params.thresh2 / 1000}
                                        onChange={(e) => setD1Params(prev => ({
                                            ...prev,
                                            thresh2: parseFloat(e.target.value) * 1000 || 5000
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>遲滯值 (m)</label>
                                    <input
                                        type="number"
                                        min="100"
                                        max="2000"
                                        value={d1Params.hysteresis}
                                        onChange={(e) => setD1Params(prev => ({
                                            ...prev,
                                            hysteresis: parseInt(e.target.value) || 500
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>最小仰角 (度)</label>
                                    <input
                                        type="number"
                                        min="0"
                                        max="45"
                                        step="0.5"
                                        value={d1Params.min_elevation_angle}
                                        onChange={(e) => setD1Params(prev => ({
                                            ...prev,
                                            min_elevation_angle: parseFloat(e.target.value) || 5.0
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>服務衛星 ID</label>
                                    <input
                                        type="text"
                                        placeholder="留空自動選擇"
                                        value={d1Params.serving_satellite_id}
                                        onChange={(e) => setD1Params(prev => ({
                                            ...prev,
                                            serving_satellite_id: e.target.value
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>參考位置 ID</label>
                                    <select
                                        value={d1Params.reference_location_id}
                                        onChange={(e) => setD1Params(prev => ({
                                            ...prev,
                                            reference_location_id: e.target.value
                                        }))}
                                    >
                                        <option value="default">預設位置</option>
                                        <option value="taipei">台北</option>
                                        <option value="kaohsiung">高雄</option>
                                        <option value="taichung">台中</option>
                                    </select>
                                </div>
                                <div className="input-group">
                                    <label>觸發時間 (ms)</label>
                                    <select
                                        value={d1Params.time_to_trigger}
                                        onChange={(e) => setD1Params(prev => ({
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
                                    <span className="stat-label">當前服務衛星:</span>
                                    <span className="stat-value">{currentServingSatellite || 'N/A'}</span>
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
                                                <div>服務衛星: {record.satellite_id}</div>
                                                <div>
                                                    服務衛星距離: {(record.measurement_values?.serving_satellite_distance / 1000)?.toFixed(2)} km
                                                </div>
                                                <div>
                                                    參考位置距離: {(record.measurement_values?.reference_position_distance / 1000)?.toFixed(2)} km
                                                </div>
                                                <div>
                                                    仰角: {record.measurement_values?.serving_satellite_elevation?.toFixed(1)}°
                                                </div>
                                                <div className="trigger-conditions">
                                                    條件1: {record.trigger_details?.condition1_met ? '✅' : '❌'}
                                                    條件2: {record.trigger_details?.condition2_met ? '✅' : '❌'}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* 衛星資訊面板 */}
                {showSatelliteInfo && (
                    <div className="side-panel satellite-panel">
                        <div className="panel-header">
                            <h3>🛰️ 衛星資訊</h3>
                            <button 
                                className="close-btn"
                                onClick={() => setShowSatelliteInfo(false)}
                            >
                                ✕
                            </button>
                        </div>
                        
                        <div className="panel-content">
                            <div className="satellite-stats">
                                <div className="stat-item">
                                    <span className="stat-label">可用衛星:</span>
                                    <span className="stat-value">{availableSatellites.length}</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">當前服務衛星:</span>
                                    <span className="stat-value">{currentServingSatellite || 'N/A'}</span>
                                </div>
                            </div>
                            
                            <div className="satellite-list">
                                {availableSatellites.slice(0, 10).map((satellite, index) => (
                                    <div key={index} className="satellite-item">
                                        <div className="satellite-id">{satellite.satellite_id}</div>
                                        <div className="satellite-name">{satellite.satellite_name}</div>
                                        <div className="satellite-epoch">
                                            Epoch: {new Date(satellite.epoch).toLocaleDateString()}
                                        </div>
                                    </div>
                                ))}
                                {availableSatellites.length > 10 && (
                                    <div className="more-satellites">
                                        ...還有 {availableSatellites.length - 10} 顆衛星
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default EnhancedD1Viewer