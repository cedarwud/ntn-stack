/**
 * EventConfigPanel - 通用事件配置介面
 * 提供統一的事件參數配置、預設值管理、匯入匯出功能
 */

import React, { useState, useCallback, useMemo } from 'react'
import { EVENT_CONFIGS, getEventConfig } from '../config/eventConfig'
import type { EventType } from '../config/eventConfig'
import type { EventA4Params, EventD1Params, EventD2Params, EventT1Params } from '../types'
import './EventConfigPanel.scss'

type AllEventParams = EventA4Params | EventD1Params | EventD2Params | EventT1Params

interface EventConfigPanelProps {
    selectedEvent: EventType
    onEventChange: (eventType: EventType) => void
    onParamsChange?: (eventType: EventType, params: AllEventParams) => void
    showPresets?: boolean
    showExport?: boolean
    className?: string
}

// 事件預設配置
const EVENT_PRESETS = {
    A4: {
        default: { Thresh: -70, Hys: 3, Ofn: 0, Ocn: 0, timeToTrigger: 160, reportAmount: 8, reportInterval: 1000, reportOnLeave: true },
        urban: { Thresh: -75, Hys: 5, Ofn: 2, Ocn: 0, timeToTrigger: 320, reportAmount: 4, reportInterval: 1000, reportOnLeave: true },
        rural: { Thresh: -65, Hys: 2, Ofn: -2, Ocn: 0, timeToTrigger: 80, reportAmount: 16, reportInterval: 500, reportOnLeave: true }
    },
    D1: {
        default: { Thresh1: 400, Thresh2: 250, Hys: 20, timeToTrigger: 320, reportAmount: 3, reportInterval: 1000, reportOnLeave: true, referenceLocation1: { lat: 25.0330, lon: 121.5654 }, referenceLocation2: { lat: 25.0478, lon: 121.5173 } },
        indoor: { Thresh1: 100, Thresh2: 50, Hys: 10, timeToTrigger: 160, reportAmount: 8, reportInterval: 500, reportOnLeave: true, referenceLocation1: { lat: 25.0330, lon: 121.5654 }, referenceLocation2: { lat: 25.0478, lon: 121.5173 } },
        outdoor: { Thresh1: 800, Thresh2: 500, Hys: 50, timeToTrigger: 640, reportAmount: 2, reportInterval: 2000, reportOnLeave: false, referenceLocation1: { lat: 25.0330, lon: 121.5654 }, referenceLocation2: { lat: 25.0478, lon: 121.5173 } }
    },
    D2: {
        default: { Thresh1: 550000, Thresh2: 6000, Hys: 20, timeToTrigger: 320, reportAmount: 3, reportInterval: 1000, reportOnLeave: true, movingReferenceLocation: { lat: 0, lon: 0 }, referenceLocation: { lat: 25.0330, lon: 121.5654 } },
        leo_satellite: { Thresh1: 600000, Thresh2: 5000, Hys: 100, timeToTrigger: 160, reportAmount: 8, reportInterval: 500, reportOnLeave: true, movingReferenceLocation: { lat: 0, lon: 0 }, referenceLocation: { lat: 25.0330, lon: 121.5654 } },
        geo_satellite: { Thresh1: 35786000, Thresh2: 10000, Hys: 500, timeToTrigger: 1000, reportAmount: 1, reportInterval: 5000, reportOnLeave: false, movingReferenceLocation: { lat: 0, lon: 0 }, referenceLocation: { lat: 25.0330, lon: 121.5654 } }
    },
    T1: {
        default: { Thresh1: 5000, Duration: 10000, timeToTrigger: 0, reportAmount: 1, reportInterval: 1000, reportOnLeave: true },
        short_window: { Thresh1: 2000, Duration: 5000, timeToTrigger: 0, reportAmount: 3, reportInterval: 500, reportOnLeave: true },
        long_window: { Thresh1: 10000, Duration: 30000, timeToTrigger: 0, reportAmount: 1, reportInterval: 2000, reportOnLeave: false }
    }
}

export const EventConfigPanel: React.FC<EventConfigPanelProps> = React.memo(({
    selectedEvent,
    onEventChange,
    onParamsChange,
    showPresets = true,
    showExport = true,
    className = ''
}) => {
    const [currentParams, setCurrentParams] = useState<AllEventParams>(() => 
        EVENT_PRESETS[selectedEvent].default as AllEventParams
    )
    const [selectedPreset, setSelectedPreset] = useState<string>('default')
    const [isEditing, setIsEditing] = useState(false)
    
    const eventConfig = useMemo(() => getEventConfig(selectedEvent), [selectedEvent])
    const availablePresets = useMemo(() => EVENT_PRESETS[selectedEvent], [selectedEvent])
    
    const handleEventSelect = useCallback((eventType: EventType) => {
        setSelectedPreset('default')
        setCurrentParams(EVENT_PRESETS[eventType].default as AllEventParams)
        setIsEditing(false)
        onEventChange(eventType)
    }, [onEventChange])
    
    const handlePresetSelect = useCallback((presetName: string) => {
        const preset = availablePresets[presetName] as AllEventParams
        if (preset) {
            setSelectedPreset(presetName)
            setCurrentParams(preset)
            setIsEditing(false)
            onParamsChange?.(selectedEvent, preset)
        }
    }, [availablePresets, selectedEvent, onParamsChange])
    
    const handleParamChange = useCallback((paramName: string, value: number | boolean) => {
        setCurrentParams(prev => ({
            ...prev,
            [paramName]: value
        }))
        setIsEditing(true)
        setSelectedPreset('custom')
    }, [])
    
    const handleApplyChanges = useCallback(() => {
        onParamsChange?.(selectedEvent, currentParams)
        setIsEditing(false)
    }, [selectedEvent, currentParams, onParamsChange])
    
    const handleExportConfig = useCallback(() => {
        const config = {
            eventType: selectedEvent,
            parameters: currentParams,
            timestamp: new Date().toISOString(),
            version: '1.0'
        }
        
        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `event-${selectedEvent.toLowerCase()}-config.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }, [selectedEvent, currentParams])
    
    const handleImportConfig = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0]
        if (!file) return
        
        const reader = new FileReader()
        reader.onload = (e) => {
            try {
                const config = JSON.parse(e.target?.result as string)
                if (config.eventType === selectedEvent && config.parameters) {
                    setCurrentParams(config.parameters)
                    setSelectedPreset('custom')
                    setIsEditing(true)
                }
            } catch (error) {
                console.error('Failed to import config:', error)
            }
        }
        reader.readAsText(file)
    }, [selectedEvent])
    
    const renderParameterInputs = () => {
        const primaryParams = eventConfig.parameters.primary
        const secondaryParams = eventConfig.parameters.secondary
        const units = eventConfig.parameters.units
        
        return (
            <div className="parameter-inputs">
                <div className="param-section">
                    <h4 className="param-section-title">🎯 主要參數</h4>
                    {primaryParams.map(paramName => {
                        const key = paramName.includes('-') ? paramName.replace(/[-\s]/g, '') : paramName
                        const value = (currentParams as any)[key] || (currentParams as any)[paramName]
                        const unit = units[paramName] || ''
                        
                        return (
                            <div key={paramName} className="param-input">
                                <label className="param-label">
                                    {paramName}
                                    <span className="param-unit">{unit}</span>
                                </label>
                                <input
                                    type="number"
                                    value={value || 0}
                                    onChange={(e) => handleParamChange(key, Number(e.target.value))}
                                    className="param-field"
                                />
                            </div>
                        )
                    })}
                </div>
                
                <div className="param-section">
                    <h4 className="param-section-title">⚙️ 次要參數</h4>
                    {secondaryParams.map(paramName => {
                        const key = paramName.includes('-') ? paramName.replace(/[-\s]/g, '') : paramName
                        const value = (currentParams as any)[key] || (currentParams as any)[paramName]
                        const unit = units[paramName] || ''
                        
                        if (paramName === 'TimeToTrigger') {
                            return (
                                <div key={paramName} className="param-input">
                                    <label className="param-label">
                                        {paramName}
                                        <span className="param-unit">{unit}</span>
                                    </label>
                                    <select
                                        value={value || 0}
                                        onChange={(e) => handleParamChange('timeToTrigger', Number(e.target.value))}
                                        className="param-select"
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
                                        <option value={1024}>1024</option>
                                        <option value={1280}>1280</option>
                                        <option value={2560}>2560</option>
                                        <option value={5120}>5120</option>
                                    </select>
                                </div>
                            )
                        }
                        
                        return (
                            <div key={paramName} className="param-input">
                                <label className="param-label">
                                    {paramName}
                                    <span className="param-unit">{unit}</span>
                                </label>
                                <input
                                    type="number"
                                    value={value || 0}
                                    onChange={(e) => handleParamChange(key, Number(e.target.value))}
                                    className="param-field"
                                />
                            </div>
                        )
                    })}
                </div>
            </div>
        )
    }
    
    return (
        <div className={`event-config-panel ${className}`}>
            <div className="config-header">
                <h3 className="config-title">
                    {eventConfig.icon} 事件配置管理
                </h3>
                <div className="config-actions">
                    {isEditing && (
                        <button
                            className="action-btn action-btn--apply"
                            onClick={handleApplyChanges}
                        >
                            ✅ 應用變更
                        </button>
                    )}
                </div>
            </div>
            
            {/* 事件選擇器 */}
            <div className="event-selector-section">
                <h4 className="section-title">📡 事件類型</h4>
                <div className="event-type-buttons">
                    {Object.keys(EVENT_CONFIGS).map((eventType) => {
                        const config = EVENT_CONFIGS[eventType as EventType]
                        return (
                            <button
                                key={eventType}
                                className={`event-type-btn ${selectedEvent === eventType ? 'active' : ''}`}
                                onClick={() => handleEventSelect(eventType as EventType)}
                                style={{
                                    borderColor: selectedEvent === eventType ? config.color.primary : '#444',
                                    backgroundColor: selectedEvent === eventType ? config.color.background : 'transparent'
                                }}
                            >
                                <span className="btn-icon">{config.icon}</span>
                                <span className="btn-text">{config.shortName}</span>
                            </button>
                        )
                    })}
                </div>
            </div>
            
            {/* 預設配置選擇 */}
            {showPresets && (
                <div className="preset-section">
                    <h4 className="section-title">🎛️ 預設配置</h4>
                    <div className="preset-buttons">
                        {Object.keys(availablePresets).map((presetName) => (
                            <button
                                key={presetName}
                                className={`preset-btn ${selectedPreset === presetName ? 'active' : ''}`}
                                onClick={() => handlePresetSelect(presetName)}
                            >
                                {presetName === 'default' ? '🔧 預設' :
                                 presetName === 'urban' ? '🏙️ 都市' :
                                 presetName === 'rural' ? '🌾 郊區' :
                                 presetName === 'indoor' ? '🏠 室內' :
                                 presetName === 'outdoor' ? '🌍 戶外' :
                                 presetName === 'leo_satellite' ? '🛰️ LEO' :
                                 presetName === 'geo_satellite' ? '🌌 GEO' :
                                 presetName === 'short_window' ? '⚡ 短窗口' :
                                 presetName === 'long_window' ? '⏳ 長窗口' :
                                 presetName}
                            </button>
                        ))}
                        {selectedPreset === 'custom' && (
                            <div className="custom-indicator">
                                ✏️ 自訂
                            </div>
                        )}
                    </div>
                </div>
            )}
            
            {/* 參數配置 */}
            <div className="parameters-section">
                <h4 className="section-title">⚙️ 參數配置</h4>
                {renderParameterInputs()}
            </div>
            
            {/* 匯入匯出功能 */}
            {showExport && (
                <div className="export-section">
                    <h4 className="section-title">💾 配置管理</h4>
                    <div className="export-actions">
                        <button
                            className="action-btn action-btn--export"
                            onClick={handleExportConfig}
                        >
                            📤 匯出配置
                        </button>
                        <label className="action-btn action-btn--import">
                            📥 匯入配置
                            <input
                                type="file"
                                accept=".json"
                                onChange={handleImportConfig}
                                style={{ display: 'none' }}
                            />
                        </label>
                    </div>
                </div>
            )}
            
            {/* 當前配置預覽 */}
            <div className="config-preview">
                <h4 className="section-title">👁️ 配置預覽</h4>
                <div className="config-summary">
                    <div className="summary-item">
                        <span className="summary-label">事件類型:</span>
                        <span className="summary-value">{eventConfig.name}</span>
                    </div>
                    <div className="summary-item">
                        <span className="summary-label">進入條件:</span>
                        <code className="summary-formula">{eventConfig.conditions.enter}</code>
                    </div>
                    <div className="summary-item">
                        <span className="summary-label">離開條件:</span>
                        <code className="summary-formula">{eventConfig.conditions.leave}</code>
                    </div>
                    {isEditing && (
                        <div className="summary-warning">
                            ⚠️ 配置已修改，記得點擊「應用變更」
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
})

EventConfigPanel.displayName = 'EventConfigPanel'

export default EventConfigPanel