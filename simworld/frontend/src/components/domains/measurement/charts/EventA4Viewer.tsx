/**
 * Event A4 Viewer Component
 * 彈窗式 3GPP TS 38.331 Event A4 視覺化組件
 * 結合 event-a4 分支的設計風格和 main 分支的正確 RSRP 數據
 */

import React, { useState, useEffect } from 'react'
import { loadCSVData } from '../../../../utils/csvDataParser'
import { ViewerProps } from '../../../../types/viewer'
import PureA4Chart from './PureA4Chart'
import './EventA4Viewer.scss'

// 擴展 ViewerProps 以支援事件選擇
interface EventA4ViewerProps extends ViewerProps {
  selectedEvent?: string
  onEventChange?: (event: string) => void
  isDarkTheme?: boolean
}

// 註冊已移除 - 使用原生 Chart.js

const EventA4Viewer: React.FC<EventA4ViewerProps> = React.memo(({
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar,
  selectedEvent = 'A4',
  onEventChange,
  isDarkTheme: externalIsDarkTheme
}) => {
  // console.log('🎯 EventA4Viewer render') // 移除除錯日誌
  
  // 參數狀態管理 - 使用 event-a4 分支的滑桿設計
  const [threshold, setThreshold] = useState(-70)
  const [hysteresis, setHysteresis] = useState(3)
  const [timeToTrigger, setTimeToTrigger] = useState(160)
  const [reportInterval, setReportInterval] = useState(1000)
  const [reportAmount, setReportAmount] = useState(8)
  const [reportOnLeave, setReportOnLeave] = useState(true)
  
  // 主題狀態 - 使用外部傳入的主題或預設值
  const [isDarkTheme, setIsDarkTheme] = useState(externalIsDarkTheme ?? true)

  // 當外部主題變化時更新內部狀態
  React.useEffect(() => {
    if (externalIsDarkTheme !== undefined) {
      setIsDarkTheme(externalIsDarkTheme)
    }
  }, [externalIsDarkTheme])
  
  // 圖表和數據狀態
  const [loading, setLoading] = useState(true)

  // 載入真實的 RSRP 數據 - 穩定化依賴
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        reportIsLoadingToNavbar?.(true)
        
        const _csvData = await loadCSVData()
        
        onReportLastUpdateToNavbar?.(new Date().toLocaleTimeString())
      } catch (error) {
        console.error('Error loading RSRP data:', error)
      } finally {
        setLoading(false)
        reportIsLoadingToNavbar?.(false)
      }
    }

    loadData()
    
    // 註冊刷新處理器
    reportRefreshHandlerToNavbar?.(loadData)
  }, [])


  // 參數重置
  const handleReset = () => {
    setThreshold(-70)
    setHysteresis(3)
    setTimeToTrigger(160)
    setReportInterval(1000)
    setReportAmount(8)
    setReportOnLeave(true)
  }

  // 主題切換
  const toggleTheme = () => {
    setIsDarkTheme(!isDarkTheme)
  }


  if (loading) {
    return (
      <div className="event-a4-viewer loading">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <p>正在載入 RSRP 數據...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="event-a4-viewer">
      <div className="viewer-content">
        {/* 參數控制面板 - 採用 event-a4 分支設計 */}
        <div className="control-panel">
          {/* 事件類型選擇器 */}
          {onEventChange && (
            <div className="event-selector-compact">
              <label>事件類型:</label>
              <div className="event-buttons-compact">
                {['A4', 'D1', 'D2', 'T1'].map((eventType) => (
                  <button
                    key={eventType}
                    className={`event-btn-compact ${selectedEvent === eventType ? 'active' : ''} ${eventType !== 'A4' ? 'disabled' : ''}`}
                    onClick={() => eventType === 'A4' && onEventChange(eventType)}
                    disabled={eventType !== 'A4'}
                  >
                    {eventType}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          <h3>參數調整</h3>
          
          <div className="control-group">
            <label>
              a4-Threshold (dBm):
              <input
                type="range"
                min="-100"
                max="-40"
                value={threshold}
                onChange={(e) => setThreshold(parseInt(e.target.value))}
              />
              <span>{threshold} dBm</span>
            </label>
          </div>

          <div className="control-group">
            <label>
              Hysteresis (dB):
              <input
                type="range"
                min="0"
                max="10"
                value={hysteresis}
                onChange={(e) => setHysteresis(parseInt(e.target.value))}
              />
              <span>{hysteresis} dB</span>
            </label>
          </div>

          <div className="control-group">
            <label>
              TimeToTrigger (ms):
              <input
                type="range"
                min="0"
                max="1000"
                step="40"
                value={timeToTrigger}
                onChange={(e) => setTimeToTrigger(parseInt(e.target.value))}
              />
              <span>{timeToTrigger} ms</span>
            </label>
          </div>

          <div className="control-group">
            <label>
              Report Interval (ms):
              <input
                type="range"
                min="200"
                max="5000"
                step="200"
                value={reportInterval}
                onChange={(e) => setReportInterval(parseInt(e.target.value))}
              />
              <span>{reportInterval} ms</span>
            </label>
          </div>

          <div className="control-group">
            <label>
              Report Amount:
              <input
                type="range"
                min="1"
                max="20"
                value={reportAmount}
                onChange={(e) => setReportAmount(parseInt(e.target.value))}
              />
              <span>{reportAmount}</span>
            </label>
          </div>

          <div className="control-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={reportOnLeave}
                onChange={(e) => setReportOnLeave(e.target.checked)}
              />
              <span>Report on Leave</span>
            </label>
          </div>

          <div className="control-buttons">
            <button className="reset-button" onClick={handleReset}>
              重置參數
            </button>
          </div>

        </div>

        {/* 圖表顯示區域 */}
        <div className="chart-area">
          <div className="chart-container">
            <PureA4Chart 
              threshold={threshold}
              hysteresis={hysteresis}
              showThresholdLines={true}
              isDarkTheme={isDarkTheme}
            />
          </div>
          
          {/* 數學公式顯示 - 2列左右併排 */}
          <div className="formula-display">
            <div className="formula-row">
              <div className="formula-item">
                <h4>Inequality A4-1 (Entering condition)</h4>
                <p>Mn + Ofn + Ocn - Hys &gt; Thresh</p>
              </div>
              <div className="formula-item">
                <h4>Inequality A4-2 (Leaving condition)</h4>
                <p>Mn + Ofn + Ocn + Hys &lt; Thresh</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
})

EventA4Viewer.displayName = 'EventA4Viewer'

export default EventA4Viewer