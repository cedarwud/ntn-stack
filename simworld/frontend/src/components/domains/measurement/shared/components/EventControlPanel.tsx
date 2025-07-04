/**
 * EventControlPanel 組件
 * 抽取自各事件 Viewer 的參數控制面板邏輯
 * 提供統一的參數控制、主題切換、重置等功能
 */

import React, { useMemo, useCallback } from 'react'
import type { EventControlPanelProps, MeasurementEventParams, ParameterDefinition } from '../types'
// import AnimationController from './AnimationController' // 未使用，暫時註釋

// 參數控制組件
interface ParameterControlProps {
  definition: ParameterDefinition
  value: unknown
  onChange: (key: string, value: unknown) => void
}

const ParameterControl: React.FC<ParameterControlProps> = ({ definition, value, onChange }) => {
  const handleChange = useCallback((newValue: unknown) => {
    onChange(definition.key, newValue)
  }, [definition.key, onChange])

  const renderControl = () => {
    switch (definition.type) {
      case 'number':
        return (
          <div className="control-item">
            <label className="control-label">
              {definition.label}
              {definition.unit && <span className="control-unit">{definition.unit}</span>}
            </label>
            <input
              type="range"
              min={definition.min ?? 0}
              max={definition.max ?? 100}
              step={definition.step ?? 1}
              value={value}
              onChange={(e) => handleChange(parseFloat(e.target.value))}
              className="control-slider"
            />
            <span className="control-value">
              {typeof value === 'number' ? value.toFixed(1) : value}
              {definition.unit}
            </span>
          </div>
        )

      case 'boolean':
        return (
          <div className="control-item control-item--horizontal">
            <span className="control-label">{definition.label}</span>
            <label className="control-checkbox">
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => handleChange(e.target.checked)}
              />
            </label>
          </div>
        )

      case 'select':
        return (
          <div className="control-item control-item--horizontal">
            <span className="control-label">{definition.label}</span>
            <select
              value={value}
              onChange={(e) => handleChange(definition.options?.[0]?.value === 'number' ? parseFloat(e.target.value) : e.target.value)}
              className="control-select"
            >
              {definition.options?.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {definition.unit && <span className="control-unit">{definition.unit}</span>}
          </div>
        )

      case 'location':
        return (
          <div className="control-item">
            <label className="control-label">{definition.label}</label>
            <div className="location-inputs">
              <input
                type="number"
                placeholder="緯度"
                value={value?.lat || ''}
                onChange={(e) => handleChange({ ...value, lat: parseFloat(e.target.value) })}
                className="control-input control-input--small"
                step="0.000001"
              />
              <input
                type="number"
                placeholder="經度"
                value={value?.lon || ''}
                onChange={(e) => handleChange({ ...value, lon: parseFloat(e.target.value) })}
                className="control-input control-input--small"
                step="0.000001"
              />
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="parameter-control">
      {renderControl()}
      {definition.description && (
        <small className="parameter-description">{definition.description}</small>
      )}
    </div>
  )
}

// 主控制面板組件
const EventControlPanel = <T extends MeasurementEventParams>({
  eventType,
  params,
  onParamsChange,
  onReset,
  showThresholdLines,
  onToggleThresholdLines,
  isDarkTheme,
  onToggleTheme,
  className = '',
  children
}: EventControlPanelProps<T> & { children?: React.ReactNode }) => {

  // 參數變更處理
  const handleParameterChange = useCallback((key: string, value: unknown) => {
    const newParams = { ...params, [key]: value }
    onParamsChange(newParams)
  }, [params, onParamsChange])

  // 獲取事件特定的參數定義（這裡可以從配置文件或 props 獲取）
  const parameterDefinitions = useMemo((): ParameterDefinition[] => {
    // 基礎參數定義（所有事件共有）
    const baseDefinitions: ParameterDefinition[] = [
      {
        key: 'Hys',
        label: 'Hysteresis',
        type: 'number',
        unit: eventType === 'A4' ? 'dB' : 'm',
        min: 0,
        max: eventType === 'A4' ? 10 : 1000,
        step: eventType === 'A4' ? 0.5 : 10,
        description: '遲滯參數，避免頻繁觸發'
      },
      {
        key: 'timeToTrigger',
        label: 'Time To Trigger',
        type: 'select',
        unit: 'ms',
        options: [
          { value: 0, label: '0' },
          { value: 40, label: '40' },
          { value: 64, label: '64' },
          { value: 80, label: '80' },
          { value: 100, label: '100' },
          { value: 128, label: '128' },
          { value: 160, label: '160' },
          { value: 256, label: '256' },
          { value: 320, label: '320' },
          { value: 480, label: '480' },
          { value: 512, label: '512' },
          { value: 640, label: '640' },
          { value: 1000, label: '1000' }
        ],
        description: '觸發前的等待時間'
      },
      {
        key: 'reportInterval',
        label: 'Report Interval',
        type: 'select',
        unit: 'ms',
        options: [
          { value: 200, label: '200' },
          { value: 240, label: '240' },
          { value: 480, label: '480' },
          { value: 640, label: '640' },
          { value: 1000, label: '1000' },
          { value: 1024, label: '1024' },
          { value: 2048, label: '2048' },
          { value: 5000, label: '5000' }
        ],
        description: '報告發送間隔'
      },
      {
        key: 'reportAmount',
        label: 'Report Amount',
        type: 'select',
        unit: '次數',
        options: [
          { value: 1, label: '1' },
          { value: 2, label: '2' },
          { value: 4, label: '4' },
          { value: 8, label: '8' },
          { value: 16, label: '16' },
          { value: 20, label: '20' },
          { value: -1, label: '無限制' }
        ],
        description: '報告發送次數'
      },
      {
        key: 'reportOnLeave',
        label: 'Report On Leave',
        type: 'boolean',
        description: '離開條件時是否報告'
      }
    ]

    // 事件特定參數
    const eventSpecificDefinitions: ParameterDefinition[] = []

    switch (eventType) {
      case 'A4':
        eventSpecificDefinitions.push(
          {
            key: 'Thresh',
            label: 'a4-Threshold',
            type: 'number',
            unit: 'dBm',
            min: -100,
            max: -40,
            step: 1,
            description: 'RSRP 門檻值'
          },
          {
            key: 'Ofn',
            label: 'Offset Frequency',
            type: 'number',
            unit: 'dB',
            min: -15,
            max: 15,
            step: 0.5,
            description: '頻率偏移'
          },
          {
            key: 'Ocn',
            label: 'Offset Cell',
            type: 'number',
            unit: 'dB',
            min: -15,
            max: 15,
            step: 0.5,
            description: '小區偏移'
          }
        )
        break

      case 'D1':
        eventSpecificDefinitions.push(
          {
            key: 'Thresh1',
            label: 'Distance Threshold 1',
            type: 'number',
            unit: 'm',
            min: 50,
            max: 10000,
            step: 50,
            description: '距離門檻 1'
          },
          {
            key: 'Thresh2',
            label: 'Distance Threshold 2',
            type: 'number',
            unit: 'm',
            min: 50,
            max: 10000,
            step: 50,
            description: '距離門檻 2'
          },
          {
            key: 'referenceLocation1',
            label: 'Reference Location 1',
            type: 'location',
            description: '參考位置 1'
          },
          {
            key: 'referenceLocation2',
            label: 'Reference Location 2',
            type: 'location',
            description: '參考位置 2'
          }
        )
        break

      case 'D2':
        eventSpecificDefinitions.push(
          {
            key: 'Thresh1',
            label: 'Distance Threshold 1',
            type: 'number',
            unit: 'm',
            min: 50,
            max: 10000,
            step: 50,
            description: '距離門檻 1'
          },
          {
            key: 'Thresh2',
            label: 'Distance Threshold 2',
            type: 'number',
            unit: 'm',
            min: 50,
            max: 10000,
            step: 50,
            description: '距離門檻 2'
          },
          {
            key: 'movingReferenceLocation',
            label: 'Moving Reference Location',
            type: 'location',
            description: '移動參考位置（衛星位置）'
          },
          {
            key: 'referenceLocation',
            label: 'Fixed Reference Location',
            type: 'location',
            description: '固定參考位置'
          }
        )
        break

      case 'T1':
        eventSpecificDefinitions.push(
          {
            key: 't1Threshold',
            label: 't1-Threshold',
            type: 'number',
            unit: 's',
            min: 1,
            max: 3600,
            step: 1,
            description: '測量時間門檻'
          }
        )
        break
    }

    return [...eventSpecificDefinitions, ...baseDefinitions]
  }, [eventType])

  // 按類別分組參數
  const parameterGroups = useMemo(() => {
    const eventSpecific = parameterDefinitions.filter(def => 
      !['Hys', 'timeToTrigger', 'reportInterval', 'reportAmount', 'reportOnLeave'].includes(def.key)
    )
    const common = parameterDefinitions.filter(def => 
      ['Hys', 'timeToTrigger'].includes(def.key)
    )
    const reporting = parameterDefinitions.filter(def => 
      ['reportInterval', 'reportAmount', 'reportOnLeave'].includes(def.key)
    )

    return { eventSpecific, common, reporting }
  }, [parameterDefinitions])

  return (
    <div className={`event-control-panel ${isDarkTheme ? 'dark-theme' : 'light-theme'} ${className}`}>
      {/* 標題區域 */}
      <div className="control-panel__header">
        <h2 className="control-panel__title">
          📡 Event {eventType} 控制面板
        </h2>
        
        {/* 主題和顯示控制 */}
        <div className="control-panel__actions">
          <button
            className={`control-btn ${showThresholdLines ? 'control-btn--active' : ''}`}
            onClick={onToggleThresholdLines}
            title="切換門檻線顯示"
          >
            📏 門檻線
          </button>
          
          <button
            className="control-btn control-btn--theme"
            onClick={onToggleTheme}
            title="切換主題"
          >
            {isDarkTheme ? '☀️' : '🌙'}
          </button>
        </div>
      </div>

      {/* 事件特定參數 */}
      {parameterGroups.eventSpecific.length > 0 && (
        <div className="control-section">
          <h3 className="control-section__title">
            🎯 {eventType} 特定參數
          </h3>
          <div className="control-group">
            {parameterGroups.eventSpecific.map((definition) => (
              <ParameterControl
                key={definition.key}
                definition={definition}
                value={params[definition.key as keyof T]}
                onChange={handleParameterChange}
              />
            ))}
          </div>
        </div>
      )}

      {/* 通用測量參數 */}
      <div className="control-section">
        <h3 className="control-section__title">⚙️ 測量參數</h3>
        <div className="control-group">
          {parameterGroups.common.map((definition) => (
            <ParameterControl
              key={definition.key}
              definition={definition}
              value={params[definition.key as keyof T]}
              onChange={handleParameterChange}
            />
          ))}
        </div>
      </div>

      {/* 報告參數 */}
      <div className="control-section">
        <h3 className="control-section__title">📊 報告參數</h3>
        <div className="control-group">
          {parameterGroups.reporting.map((definition) => (
            <ParameterControl
              key={definition.key}
              definition={definition}
              value={params[definition.key as keyof T]}
              onChange={handleParameterChange}
            />
          ))}
        </div>
      </div>

      {/* 自定義內容區域 */}
      {children && (
        <div className="control-section">
          {children}
        </div>
      )}

      {/* 重置按鈕 */}
      <div className="control-section">
        <div className="control-group control-group--buttons">
          <button
            className="control-btn control-btn--reset"
            onClick={onReset}
          >
            🔄 重置所有參數
          </button>
        </div>
      </div>
    </div>
  )
}

export default EventControlPanel