/**
 * BaseEventViewer 組件
 * 統一的事件查看器基礎組件，整合所有共享功能
 * 提供插件化的架構，支持不同事件類型的特定邏輯
 */

import React, { useMemo, useCallback, useState, useEffect } from 'react'
import type { 
  BaseEventViewerProps, 
  MeasurementEventParams
} from '../types'
import { 
  NarrationPanel, 
  EventControlPanel, 
  BaseChart 
} from './index'
import { createChartConfig } from '../utils'
import { loadCSVData } from '../../../../../utils/csvDataParser'

// 事件選擇器組件
interface EventSelectorProps {
  selectedEvent: string
  onEventChange: (event: string) => void
  availableEvents?: string[]
}

const EventSelector: React.FC<EventSelectorProps> = ({ 
  selectedEvent, 
  onEventChange, 
  availableEvents = ['A4', 'D1', 'D2', 'T1'] 
}) => (
  <div className="event-selector-compact">
    <label>事件類型:</label>
    <div className="event-buttons-compact">
      {availableEvents.map((eventType) => (
        <button
          key={eventType}
          className={`event-btn-compact ${selectedEvent === eventType ? 'active' : ''}`}
          onClick={() => onEventChange(eventType)}
        >
          {eventType}
        </button>
      ))}
    </div>
  </div>
)

// 主要的 BaseEventViewer 組件
const BaseEventViewer = <T extends MeasurementEventParams>({
  eventType,
  params,
  onParamsChange,
  chartComponent,
  narrationGenerator,
  className = '',
  children,
  // ViewerProps 相容性
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar,
  // 事件選擇器支持
  selectedEvent,
  onEventChange,
  // 主題支持
  isDarkTheme: externalIsDarkTheme,
  // 其他擴展屬性
  showEventSelector = false,
  availableEvents,
  onDataPointClick
}: BaseEventViewerProps<T> & {
  children?: React.ReactNode
  onReportLastUpdateToNavbar?: (time: string) => void
  reportRefreshHandlerToNavbar?: (handler: () => void) => void
  reportIsLoadingToNavbar?: (loading: boolean) => void
  selectedEvent?: string
  onEventChange?: (event: string) => void
  isDarkTheme?: boolean
  showEventSelector?: boolean
  availableEvents?: string[]
  onDataPointClick?: (point: unknown, datasetIndex: number) => void
}) => {
  // 載入狀態
  const [loading, setLoading] = useState(true)

  // 內部主題狀態
  const [internalIsDarkTheme, setInternalIsDarkTheme] = useState(
    externalIsDarkTheme ?? true
  )

  // 內部控制狀態
  const [showThresholdLines, setShowThresholdLines] = useState(true)
  const [narrationPanel, setNarrationPanel] = useState({
    isVisible: true,
    isMinimized: false,
    showTechnicalDetails: false,
    position: { x: 20, y: 20 },
    opacity: 0.95
  })

  // 同步外部主題狀態
  useEffect(() => {
    if (externalIsDarkTheme !== undefined) {
      setInternalIsDarkTheme(externalIsDarkTheme)
    }
  }, [externalIsDarkTheme])

  // 數據載入
  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      reportIsLoadingToNavbar?.(true)

      // 載入真實數據（如果需要）
      const _csvData = await loadCSVData()

      onReportLastUpdateToNavbar?.(new Date().toLocaleTimeString())
    } catch (error) {
      console.error('Error loading measurement data:', error)
    } finally {
      setLoading(false)
      reportIsLoadingToNavbar?.(false)
    }
  }, [onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

  // 初始化數據載入
  useEffect(() => {
    loadData()
    reportRefreshHandlerToNavbar?.(loadData)
  }, [loadData, reportRefreshHandlerToNavbar])

  // 重置參數處理
  const handleReset = useCallback(() => {
    // 這裡應該重置到事件的默認參數
    // 具體的默認值由各事件的 Hook 提供
    if (typeof onParamsChange === 'function') {
      // 基礎重置邏輯，具體實現由調用方決定
      console.log('Reset params for event:', eventType)
    }
  }, [eventType, onParamsChange])

  // 主題切換
  const toggleTheme = useCallback(() => {
    setInternalIsDarkTheme(prev => !prev)
  }, [])

  // 門檻線切換
  const toggleThresholdLines = useCallback(() => {
    setShowThresholdLines(prev => !prev)
  }, [])

  // 解說面板更新
  const updateNarrationPanel = useCallback((updates: Partial<typeof narrationPanel>) => {
    setNarrationPanel(prev => ({ ...prev, ...updates }))
  }, [])

  // 生成圖表配置
  const chartConfig = useMemo(() => {
    try {
      return createChartConfig(eventType, params, internalIsDarkTheme)
    } catch (error) {
      console.error('Error creating chart config:', error)
      return null
    }
  }, [eventType, params, internalIsDarkTheme])

  // 事件選擇器
  const eventSelectorComponent = useMemo(() => {
    if (!showEventSelector || !onEventChange) return null

    return (
      <EventSelector
        selectedEvent={selectedEvent || eventType}
        onEventChange={onEventChange}
        availableEvents={availableEvents}
      />
    )
  }, [showEventSelector, onEventChange, selectedEvent, eventType, availableEvents])

  // 解說內容生成
  const narrationContent = useMemo(() => {
    if (!narrationGenerator) {
      return {
        phaseTitle: `Event ${eventType} 運行中`,
        timeProgress: '0.0s (0%)',
        mainDescription: '系統正在運行中...',
        technicalDetails: '詳細技術信息暫不可用'
      }
    }

    // 這裡需要動畫狀態，暫時使用默認值
    const mockAnimationState = {
      isPlaying: false,
      currentTime: 0,
      speed: 1,
      nodePosition: null,
      eventConditions: [],
      activeEvents: []
    }

    try {
      return narrationGenerator(params, mockAnimationState)
    } catch (error) {
      console.error('Error generating narration content:', error)
      return {
        phaseTitle: `Event ${eventType} 錯誤`,
        timeProgress: '錯誤',
        mainDescription: '解說內容生成失敗',
        technicalDetails: '請檢查配置'
      }
    }
  }, [narrationGenerator, params, eventType])

  // 載入中狀態
  if (loading) {
    return (
      <div className="base-event-viewer loading">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <p>正在載入 {eventType} 事件數據...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`base-event-viewer ${internalIsDarkTheme ? 'dark-theme' : 'light-theme'} ${className}`}>
      <div className="event-viewer__content">
        {/* 控制面板區域 */}
        <div className="event-viewer__controls">
          {/* 事件選擇器 */}
          {eventSelectorComponent}

          {/* 動畫控制 */}
          <div className="control-section">
            <h3 className="control-section__title">🎬 動畫控制</h3>
            {/* 注意：這裡需要實際的動畫狀態，目前是佔位符 */}
            <div className="animation-placeholder">
              <p>動畫控制器將在集成時添加</p>
            </div>
          </div>

          {/* 事件參數控制 */}
          <EventControlPanel
            eventType={eventType}
            params={params}
            onParamsChange={onParamsChange}
            onReset={handleReset}
            showThresholdLines={showThresholdLines}
            onToggleThresholdLines={toggleThresholdLines}
            isDarkTheme={internalIsDarkTheme}
            onToggleTheme={toggleTheme}
          />

          {/* 自定義內容區域 */}
          {children}
        </div>

        {/* 圖表區域 */}
        <div className="event-viewer__chart-container">
          <div className="chart-area">
            <div className="chart-container">
              {chartConfig ? (
                chartComponent ? (
                  // 使用自定義圖表組件
                  React.createElement(chartComponent, {
                    eventType,
                    params,
                    animationState: { currentTime: 0, isPlaying: false, speed: 1 }, // 佔位符
                    isDarkTheme: internalIsDarkTheme,
                    showThresholdLines,
                    onDataPointClick
                  })
                ) : (
                  // 使用基礎圖表組件
                  <BaseChart
                    eventType={eventType}
                    params={params}
                    animationState={{ currentTime: 0, isPlaying: false, speed: 1 }} // 佔位符
                    isDarkTheme={internalIsDarkTheme}
                    showThresholdLines={showThresholdLines}
                    config={chartConfig}
                    onDataPointClick={onDataPointClick}
                  />
                )
              ) : (
                <div className="chart-error">
                  <p>無法載入 {eventType} 事件圖表</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 浮動解說面板 */}
      {narrationPanel.isVisible && (
        <NarrationPanel
          isVisible={narrationPanel.isVisible}
          isMinimized={narrationPanel.isMinimized}
          showTechnicalDetails={narrationPanel.showTechnicalDetails}
          content={`
            <h4>${narrationContent.phaseTitle}</h4>
            <div class="time-progress">${narrationContent.timeProgress}</div>
            ${narrationContent.mainDescription}
            ${narrationPanel.showTechnicalDetails ? narrationContent.technicalDetails || '' : ''}
          `}
          position={narrationPanel.position}
          opacity={narrationPanel.opacity}
          onToggleVisibility={() => updateNarrationPanel({ isVisible: false })}
          onToggleMinimized={() => updateNarrationPanel({ isMinimized: !narrationPanel.isMinimized })}
          onToggleTechnicalDetails={() => updateNarrationPanel({ showTechnicalDetails: !narrationPanel.showTechnicalDetails })}
          onPositionChange={(position) => updateNarrationPanel({ position })}
          onOpacityChange={(opacity) => updateNarrationPanel({ opacity })}
          className={internalIsDarkTheme ? 'dark-theme' : 'light-theme'}
        />
      )}
    </div>
  )
}

export default BaseEventViewer