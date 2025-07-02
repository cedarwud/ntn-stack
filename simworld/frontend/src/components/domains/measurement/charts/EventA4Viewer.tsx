/**
 * Event A4 Viewer Component
 * 彈窗式 3GPP TS 38.331 Event A4 視覺化組件
 * 結合 event-a4 分支的設計風格和 main 分支的正確 RSRP 數據
 */

import React, { useState, useMemo, useRef, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, ChartOptions } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import { loadCSVData, interpolateRSRP } from '../../../../utils/csvDataParser'
import { ViewerProps } from '../../../../types/viewer'
import './EventA4Viewer.scss'

// 擴展 ViewerProps 以支援事件選擇
interface EventA4ViewerProps extends ViewerProps {
  selectedEvent?: string
  onEventChange?: (event: string) => void
}

// 註冊 Chart.js 組件
ChartJS.register(annotationPlugin)

const EventA4Viewer: React.FC<EventA4ViewerProps> = React.memo(({
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar,
  selectedEvent = 'A4',
  onEventChange
}) => {
  console.log('🎯 EventA4Viewer render')
  
  // 參數狀態管理 - 使用 event-a4 分支的滑桿設計
  const [threshold, setThreshold] = useState(-70)
  const [hysteresis, setHysteresis] = useState(3)
  const [timeToTrigger, setTimeToTrigger] = useState(160)
  const [reportInterval, setReportInterval] = useState(1000)
  const [reportAmount, setReportAmount] = useState(8)
  const [reportOnLeave, setReportOnLeave] = useState(true)
  
  // 圖表和數據狀態
  const [rsrpData, setRsrpData] = useState<Array<{x: number, y: number}>>([])
  const [loading, setLoading] = useState(true)
  const [animationState, setAnimationState] = useState({
    isPlaying: false,
    currentTime: 0,
    nodePosition: null as {x: number, y: number} | null
  })
  
  const chartRef = useRef<ChartJS<'line'>>(null)

  // 載入真實的 RSRP 數據
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        reportIsLoadingToNavbar?.(true)
        
        const csvData = await loadCSVData()
        setRsrpData(csvData.points)
        
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
  }, [onReportLastUpdateToNavbar, reportRefreshHandlerToNavbar, reportIsLoadingToNavbar])

  // 計算觸發和取消條件的時間點
  const { _triggerTime, _cancelTime } = useMemo(() => {
    const triggerThreshold = threshold + hysteresis
    const cancelThreshold = threshold - hysteresis
    
    let triggerTime = null
    let cancelTime = null
    
    // 找到觸發點 (首次穿越 threshold + hys)
    for (const point of rsrpData) {
      if (point.y > triggerThreshold && triggerTime === null) {
        triggerTime = point.x
      }
      // 找到取消點 (穿回 threshold - hys)
      if (triggerTime !== null && point.y < cancelThreshold && cancelTime === null) {
        cancelTime = point.x
        break
      }
    }
    
    return { _triggerTime: triggerTime, _cancelTime: cancelTime }
  }, [rsrpData, threshold, hysteresis])

  // Chart.js 數據配置
  const chartData = useMemo(() => {
    console.log('🔄 chartData recalculating', { rsrpDataLength: rsrpData.length, threshold, hysteresis })
    const baseDatasets = [
      {
        label: 'Neighbor Cell RSRP',
        data: rsrpData,
        borderColor: '#2E86AB', // 保持 event-a4 分支的藍色
        backgroundColor: 'transparent',
        borderWidth: 3,
        fill: false,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 8,
        cubicInterpolationMode: 'monotone' as const,
        borderCapStyle: 'round' as const,
        borderJoinStyle: 'round' as const,
      },
      {
        label: 'a4-Threshold',
        data: rsrpData.map(point => ({ x: point.x, y: threshold })),
        borderColor: '#E74C3C',
        borderDash: [10, 5],
        borderWidth: 2,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 0,
      },
      {
        label: 'Threshold + Hys',
        data: rsrpData.map(point => ({ x: point.x, y: threshold + hysteresis })),
        borderColor: 'rgba(231, 76, 60, 0.6)',
        borderDash: [5, 3],
        borderWidth: 1,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 0,
      },
      {
        label: 'Threshold - Hys',
        data: rsrpData.map(point => ({ x: point.x, y: threshold - hysteresis })),
        borderColor: 'rgba(231, 76, 60, 0.6)',
        borderDash: [5, 3],
        borderWidth: 1,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 0,
      }
    ]

    // 添加動畫節點
    if (animationState.nodePosition) {
      baseDatasets.push({
        label: 'Current Position',
        data: [animationState.nodePosition],
        borderColor: '#FF5722',
        backgroundColor: '#FF5722',
        borderWidth: 0,
        pointRadius: 8,
        pointHoverRadius: 10,
        showLine: false,
      } as const)
    }

    return { datasets: baseDatasets }
  }, [rsrpData, threshold, hysteresis, animationState.nodePosition])

  // Chart.js 選項配置 - 使用 useMemo 防止重新渲染
  const chartOptions: ChartOptions<'line'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    devicePixelRatio: 2,
    animation: { duration: 0 },
    plugins: {
      title: {
        display: true,
        text: 'Event A4 - Neighbour becomes better than threshold',
        color: '#E74C3C',
        font: { size: 18, weight: 'bold' }
      },
      legend: {
        position: 'bottom',
        labels: {
          color: 'white',
          font: { size: 12 }
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          title: (context) => `Time: ${context[0].label}s`,
          label: (context) => {
            if (context.datasetIndex === 0) {
              return `RSRP: ${context.parsed.y.toFixed(1)} dBm`
            }
            return context.dataset.label + `: ${context.parsed.y} dBm`
          }
        }
      }
    },
    scales: {
      x: {
        type: 'linear',
        title: {
          display: true,
          text: 'Time (s)',
          color: 'white',
          font: { size: 14 }
        },
        ticks: {
          color: 'white',
          callback: function(value) {
            return `${value}s`
          }
        },
        grid: { color: 'rgba(255, 255, 255, 0.1)' }
      },
      y: {
        title: {
          display: true,
          text: 'RSRP (dBm)',
          color: 'white',
          font: { size: 14 }
        },
        ticks: {
          color: 'white',
          callback: function(value) {
            return `${value} dBm`
          }
        },
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        min: -110,
        max: -40
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  }), []) // 固定配置，不依賴任何狀態

  // 參數重置
  const handleReset = () => {
    setThreshold(-70)
    setHysteresis(3)
    setTimeToTrigger(160)
    setReportInterval(1000)
    setReportAmount(8)
    setReportOnLeave(true)
  }

  // 動畫控制
  const startAnimation = () => {
    setAnimationState(prev => ({ ...prev, isPlaying: true }))
  }

  const stopAnimation = () => {
    setAnimationState(prev => ({ ...prev, isPlaying: false }))
  }

  const resetAnimation = () => {
    setAnimationState({
      isPlaying: false,
      currentTime: 0,
      nodePosition: null
    })
  }

  // 動畫循環 - 使用穩定的間隔避免閃爍
  useEffect(() => {
    let intervalId: NodeJS.Timeout

    if (animationState.isPlaying && rsrpData.length > 0) {
      intervalId = setInterval(() => {
        setAnimationState(prev => {
          const timeStep = 0.5 // 固定時間步長
          const newTime = prev.currentTime + timeStep
          const maxTime = rsrpData[rsrpData.length - 1]?.x || 0

          if (newTime >= maxTime) {
            return { ...prev, isPlaying: false, currentTime: maxTime }
          }

          const currentRsrp = interpolateRSRP(rsrpData, newTime)
          const nodePosition = { x: newTime, y: currentRsrp }

          return {
            ...prev,
            currentTime: newTime,
            nodePosition
          }
        })
      }, 150) // 每 150ms 更新，更穩定的間隔
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [animationState.isPlaying, rsrpData])

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

          <div className="control-group">
            <label>
              <input
                type="checkbox"
                checked={reportOnLeave}
                onChange={(e) => setReportOnLeave(e.target.checked)}
              />
              Report on Leave
            </label>
          </div>

          <div className="control-buttons">
            <button className="reset-button" onClick={handleReset}>
              重置參數
            </button>
          </div>

          {/* 動畫控制 */}
          <div className="animation-controls">
            <h4>動畫控制</h4>
            <div className="animation-buttons">
              <button 
                onClick={startAnimation} 
                disabled={animationState.isPlaying}
                className="btn btn-primary"
              >
                ▶ 播放
              </button>
              <button 
                onClick={stopAnimation} 
                disabled={!animationState.isPlaying}
                className="btn btn-secondary"
              >
                ⏸ 暫停
              </button>
              <button 
                onClick={resetAnimation}
                className="btn btn-secondary"
              >
                ⏹ 重置
              </button>
            </div>
            <div className="time-display">
              當前時間: {animationState.currentTime.toFixed(1)}s
            </div>
          </div>
        </div>

        {/* 圖表顯示區域 */}
        <div className="chart-area">
          <div className="chart-container">
            <Line ref={chartRef} data={chartData} options={chartOptions} />
          </div>
          
          {/* 參數顯示區域 - 採用 event-a4 分支設計 */}
          <div className="chart-parameters">
            <div className="parameter-row">
              <span>triggerType = event</span>
              <span>eventID = eventA4</span>
            </div>
            <div className="parameter-row">
              <span>a4-Threshold: {threshold} dBm</span>
              <span>Hysteresis: {hysteresis} dB</span>
              <span>TimeToTrigger: {timeToTrigger} ms</span>
            </div>
            <div className="parameter-row">
              <span>reportInterval: {reportInterval} ms</span>
              <span>reportAmount: {reportAmount}</span>
              <span>reportOnLeave: {reportOnLeave ? 'true' : 'false'}</span>
            </div>
          </div>
          
          {/* 數學公式顯示 */}
          <div className="formula-display">
            <h4>Inequality A4-1 (Entering condition)</h4>
            <p>Mn + Ofn + Ocn - Hys &gt; Thresh</p>
            <h4>Inequality A4-2 (Leaving condition)</h4>
            <p>Mn + Ofn + Ocn + Hys &lt; Thresh</p>
          </div>
        </div>
      </div>
    </div>
  )
})

EventA4Viewer.displayName = 'EventA4Viewer'

export default EventA4Viewer