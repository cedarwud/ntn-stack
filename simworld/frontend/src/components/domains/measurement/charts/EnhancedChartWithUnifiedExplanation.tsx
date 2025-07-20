/**
 * Enhanced 圖表與統一說明系統整合示例
 * 展示如何在現有的 Enhanced 組件中整合統一圖表說明系統
 */

import React, { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import { 
  UnifiedChartExplanation, 
  generateUnifiedChartConfig,
  EventType,
  DataType 
} from '../shared/components/UnifiedChartExplanation'
import './EnhancedChartWithUnifiedExplanation.scss'

interface EnhancedChartWithUnifiedExplanationProps {
  eventType: EventType
  dataType?: DataType
  data: any
  isDarkTheme?: boolean
  showExplanation?: boolean
  className?: string
}

export const EnhancedChartWithUnifiedExplanation: React.FC<EnhancedChartWithUnifiedExplanationProps> = ({
  eventType,
  dataType = 'enhanced',
  data,
  isDarkTheme = true,
  showExplanation = true,
  className = ''
}) => {
  const [explanationExpanded, setExplanationExpanded] = useState(false)
  const [chartConfig, setChartConfig] = useState<any>(null)

  useEffect(() => {
    // 生成統一的圖表配置
    const config = generateUnifiedChartConfig(eventType, dataType, isDarkTheme)
    setChartConfig(config)
  }, [eventType, dataType, isDarkTheme])

  if (!chartConfig) {
    return <div className="loading-placeholder">載入圖表配置中...</div>
  }

  return (
    <div className={`enhanced-chart-with-explanation ${className} ${isDarkTheme ? 'dark-theme' : 'light-theme'}`}>
      {/* 統一圖表說明 */}
      {showExplanation && (
        <UnifiedChartExplanation
          eventType={eventType}
          dataType={dataType}
          isExpanded={explanationExpanded}
          onToggle={setExplanationExpanded}
          showPhysicalModels={true}
          showEducationalNotes={true}
        />
      )}

      {/* 圖表容器 */}
      <div className="chart-container">
        <div className="chart-wrapper">
          <Line
            data={data}
            options={{
              ...chartConfig,
              responsive: true,
              maintainAspectRatio: false,
              interaction: {
                mode: 'index' as const,
                intersect: false,
              },
              elements: {
                point: {
                  radius: 3,
                  hoverRadius: 6,
                },
                line: {
                  tension: 0.1,
                  borderWidth: 2,
                }
              },
              animation: {
                duration: 750,
                easing: 'easeInOutQuart'
              }
            }}
          />
        </div>

        {/* 圖表底部資訊 */}
        <div className="chart-footer">
          <div className="data-quality-info">
            <span className="quality-badge research-grade">
              🎓 論文研究級數據
            </span>
            <span className="accuracy-info">
              精度: {getAccuracyInfo(eventType)}
            </span>
            <span className="standards-info">
              標準: {getStandardsInfo(eventType)}
            </span>
          </div>
          
          <div className="chart-actions">
            <button 
              className="explanation-toggle"
              onClick={() => setExplanationExpanded(!explanationExpanded)}
              aria-label={explanationExpanded ? '收起說明' : '展開說明'}
            >
              {explanationExpanded ? '📖 收起說明' : '📖 展開說明'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// 輔助函數
const getAccuracyInfo = (eventType: EventType): string => {
  switch (eventType) {
    case 'A4':
      return '< 1 dB (信號強度)'
    case 'D1':
      return '< 1 km (距離測量)'
    case 'D2':
      return '< 500 m (參考位置)'
    case 'T1':
      return '< 1 ns (時間同步)'
  }
}

const getStandardsInfo = (eventType: EventType): string => {
  switch (eventType) {
    case 'A4':
      return '3GPP TR 38.811, ITU-R P.618'
    case 'D1':
      return '3GPP TS 38.331, CCSDS 502.0-B-2'
    case 'D2':
      return '3GPP TS 38.331, 3GPP TS 38.455'
    case 'T1':
      return '3GPP TS 38.331, ITU-R TF.460-6'
  }
}

// 使用示例組件
export const EnhancedA4ChartExample: React.FC = () => {
  // 模擬 A4 事件數據
  const mockA4Data = {
    labels: Array.from({ length: 50 }, (_, i) => i * 2), // 0, 2, 4, ..., 98 秒
    datasets: [
      {
        label: '服務衛星 RSRP',
        data: Array.from({ length: 50 }, (_, i) => -80 + Math.sin(i * 0.2) * 10 + Math.random() * 5),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
      },
      {
        label: '鄰居衛星 RSRP',
        data: Array.from({ length: 50 }, (_, i) => -90 + Math.cos(i * 0.15) * 8 + Math.random() * 4),
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
      },
      {
        label: 'A4 閾值',
        data: Array.from({ length: 50 }, () => -85),
        borderColor: '#fbbf24',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        pointRadius: 0,
      }
    ]
  }

  return (
    <EnhancedChartWithUnifiedExplanation
      eventType="A4"
      dataType="enhanced"
      data={mockA4Data}
      isDarkTheme={true}
      showExplanation={true}
      className="a4-chart-example"
    />
  )
}

export const EnhancedD1ChartExample: React.FC = () => {
  // 模擬 D1 事件數據
  const mockD1Data = {
    labels: Array.from({ length: 60 }, (_, i) => i * 5), // 0, 5, 10, ..., 295 秒
    datasets: [
      {
        label: '服務衛星距離',
        data: Array.from({ length: 60 }, (_, i) => 800 + Math.sin(i * 0.1) * 200 + Math.random() * 50),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
      },
      {
        label: '目標衛星距離',
        data: Array.from({ length: 60 }, (_, i) => 1200 - Math.cos(i * 0.12) * 300 + Math.random() * 60),
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        fill: true,
      }
    ]
  }

  return (
    <EnhancedChartWithUnifiedExplanation
      eventType="D1"
      dataType="real"
      data={mockD1Data}
      isDarkTheme={true}
      showExplanation={true}
      className="d1-chart-example"
    />
  )
}

export const EnhancedT1ChartExample: React.FC = () => {
  // 模擬 T1 事件數據
  const mockT1Data = {
    labels: Array.from({ length: 40 }, (_, i) => i * 10), // 0, 10, 20, ..., 390 秒
    datasets: [
      {
        label: '時間同步精度',
        data: Array.from({ length: 40 }, (_, i) => Math.abs(Math.sin(i * 0.3)) * 2 + Math.random() * 0.5),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        fill: true,
      },
      {
        label: 'T1 閾值',
        data: Array.from({ length: 40 }, () => 1.5),
        borderColor: '#ef4444',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        pointRadius: 0,
      }
    ]
  }

  return (
    <EnhancedChartWithUnifiedExplanation
      eventType="T1"
      dataType="enhanced"
      data={mockT1Data}
      isDarkTheme={true}
      showExplanation={true}
      className="t1-chart-example"
    />
  )
}

// 統一圖表說明展示組件
export const UnifiedExplanationShowcase: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState<EventType>('A4')
  const [selectedDataType, setSelectedDataType] = useState<DataType>('enhanced')

  const eventTypes: EventType[] = ['A4', 'D1', 'D2', 'T1']
  const dataTypes: DataType[] = ['real', 'enhanced', 'simulated']

  return (
    <div className="unified-explanation-showcase">
      <div className="showcase-header">
        <h2>統一圖表說明系統展示</h2>
        <p>展示 Phase 3.2 圖表說明統一改進的成果</p>
      </div>

      <div className="showcase-controls">
        <div className="control-group">
          <label>事件類型:</label>
          <select 
            value={selectedEvent} 
            onChange={(e) => setSelectedEvent(e.target.value as EventType)}
          >
            {eventTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>數據類型:</label>
          <select 
            value={selectedDataType} 
            onChange={(e) => setSelectedDataType(e.target.value as DataType)}
          >
            {dataTypes.map(type => (
              <option key={type} value={type}>
                {type === 'real' ? '真實數據' : 
                 type === 'enhanced' ? '增強數據' : '模擬數據'}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="showcase-content">
        <UnifiedChartExplanation
          eventType={selectedEvent}
          dataType={selectedDataType}
          isExpanded={true}
          showPhysicalModels={true}
          showEducationalNotes={true}
        />
      </div>
    </div>
  )
}

export default EnhancedChartWithUnifiedExplanation
