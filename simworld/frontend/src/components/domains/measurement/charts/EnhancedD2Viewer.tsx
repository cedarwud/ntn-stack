/**
 * Enhanced D2 Event Viewer
 * 增強版 D2 移動參考位置距離事件查看器
 * 
 * 整合功能：
 * 1. 增強版 D2 圖表
 * 2. 實時數據控制面板
 * 3. 參數配置界面
 * 4. 事件觸發歷史
 * 5. 移動參考位置視覺化
 * 6. 多因子衛星選擇狀態
 */

import React, { useState, useCallback, useEffect } from 'react'
import EnhancedD2Chart from './EnhancedD2Chart'
import { netstackFetch } from '../../../../config/api-config'
import './EnhancedD2Viewer.scss'

interface UEPosition {
    latitude: number
    longitude: number
    altitude: number
}

interface D2Parameters {
    thresh1: number // 衛星距離門檻 (m)
    thresh2: number // 地面距離門檻 (m)
    hysteresis: number // 遲滯值 (m)
    time_to_trigger: number // 觸發時間 (ms)
}

interface EventTriggerRecord {
    timestamp: string
    trigger_details: any
    measurement_values: any
    satellite_id: string
}

const EnhancedD2Viewer: React.FC = () => {
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
    
    // D2 參數
    const [d2Params, setD2Params] = useState<D2Parameters>({
        thresh1: 800000,  // 800km
        thresh2: 30000,   // 30km
        hysteresis: 500,  // 500m
        time_to_trigger: 160 // 160ms
    })
    
    // 觸發歷史
    const [triggerHistory, setTriggerHistory] = useState<EventTriggerRecord[]>([])
    const [availableSatellites, setAvailableSatellites] = useState<any[]>([])
    const [currentReferenceSatellite, setCurrentReferenceSatellite] = useState<string>('')
    
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
            satellite_id: eventData.measurement_values?.reference_satellite || 'unknown'
        }
        
        setTriggerHistory(prev => [newRecord, ...prev.slice(0, 19)]) // 保留最近20條記錄
        setCurrentReferenceSatellite(newRecord.satellite_id)
    }, [])

    // 切換主題
    const toggleTheme = useCallback(() => {
        setIsDarkTheme(prev => !prev)
    }, [])

    // 切換數據模式
    const toggleDataMode = useCallback(() => {
        setUseRealData(prev => !prev)
    }, [])

    // 重置 D2 參數
    const resetParameters = useCallback(() => {
        setD2Params({
            thresh1: 800000,
            thresh2: 30000,
            hysteresis: 500,
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

    // 初始化
    useEffect(() => {
        fetchAvailableSatellites()
    }, [fetchAvailableSatellites])

    return (
        <div className={`enhanced-d2-viewer ${isDarkTheme ? 'dark-theme' : 'light-theme'}`}>
            {/* 主標題和控制欄 */}
            <div className="viewer-header">
                <div className="title-section">
                    <h2>🛰️ 增強版 D2 移動參考位置距離事件監測</h2>
                    <div className="subtitle">
                        基於 3GPP TS 38.331 規範 | 多因子衛星選擇算法 | 論文研究級數據精度
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
                    <EnhancedD2Chart
                        thresh1={d2Params.thresh1}
                        thresh2={d2Params.thresh2}
                        hysteresis={d2Params.hysteresis}
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
                            <h3>📋 D2 參數配置</h3>
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

                            {/* D2 參數配置 */}
                            <div className="config-section">
                                <h4>🎯 D2 事件參數</h4>
                                <div className="input-group">
                                    <label>衛星距離門檻 (km)</label>
                                    <input
                                        type="number"
                                        min="400"
                                        max="2000"
                                        value={d2Params.thresh1 / 1000}
                                        onChange={(e) => setD2Params(prev => ({
                                            ...prev,
                                            thresh1: parseFloat(e.target.value) * 1000 || 800000
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>地面距離門檻 (km)</label>
                                    <input
                                        type="number"
                                        min="0.1"
                                        max="50"
                                        step="0.1"
                                        value={d2Params.thresh2 / 1000}
                                        onChange={(e) => setD2Params(prev => ({
                                            ...prev,
                                            thresh2: parseFloat(e.target.value) * 1000 || 30000
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>遲滯值 (m)</label>
                                    <input
                                        type="number"
                                        min="100"
                                        max="5000"
                                        value={d2Params.hysteresis}
                                        onChange={(e) => setD2Params(prev => ({
                                            ...prev,
                                            hysteresis: parseInt(e.target.value) || 500
                                        }))}
                                    />
                                </div>
                                <div className="input-group">
                                    <label>觸發時間 (ms)</label>
                                    <select
                                        value={d2Params.time_to_trigger}
                                        onChange={(e) => setD2Params(prev => ({
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
                                    <span className="stat-label">當前參考衛星:</span>
                                    <span className="stat-value">{currentReferenceSatellite || 'N/A'}</span>
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
                                                <div>衛星: {record.satellite_id}</div>
                                                <div>
                                                    衛星距離: {(record.measurement_values?.satellite_distance / 1000)?.toFixed(1)} km
                                                </div>
                                                <div>
                                                    地面距離: {(record.measurement_values?.ground_distance / 1000)?.toFixed(2)} km
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

export default EnhancedD2Viewer