/**
 * 數據狀態指示器組件
 * 顯示數據來源、連接狀態和錯誤信息
 */

import React from 'react'
import { DataSourceStatus } from '../hooks/useRealChartData'

interface DataStatusIndicatorProps {
  status: DataSourceStatus
  error?: string
  lastUpdate?: string
  label?: string
  compact?: boolean
}

const getStatusConfig = (status: DataSourceStatus) => {
  switch (status) {
    case 'real':
      return {
        icon: '✅',
        text: '即時數據',
        color: '#4ade80',
        bgColor: 'rgba(74, 222, 128, 0.1)',
        borderColor: 'rgba(74, 222, 128, 0.3)'
      }
    case 'calculated':
      return {
        icon: '🔄',
        text: '計算數據',
        color: '#3b82f6',
        bgColor: 'rgba(59, 130, 246, 0.1)',
        borderColor: 'rgba(59, 130, 246, 0.3)'
      }
    case 'fallback':
      return {
        icon: '⚠️',
        text: '模擬數據',
        color: '#f59e0b',
        bgColor: 'rgba(245, 158, 11, 0.1)',
        borderColor: 'rgba(245, 158, 11, 0.3)'
      }
    case 'loading':
      return {
        icon: '🔄',
        text: '載入中...',
        color: '#6b7280',
        bgColor: 'rgba(107, 114, 128, 0.1)',
        borderColor: 'rgba(107, 114, 128, 0.3)'
      }
    case 'error':
      return {
        icon: '❌',
        text: 'API 錯誤',
        color: '#ef4444',
        bgColor: 'rgba(239, 68, 68, 0.1)',
        borderColor: 'rgba(239, 68, 68, 0.3)'
      }
    default:
      return {
        icon: '❓',
        text: '未知狀態',
        color: '#6b7280',
        bgColor: 'rgba(107, 114, 128, 0.1)',
        borderColor: 'rgba(107, 114, 128, 0.3)'
      }
  }
}

const DataStatusIndicator: React.FC<DataStatusIndicatorProps> = ({
  status,
  error,
  lastUpdate,
  label,
  compact = false
}) => {
  const config = getStatusConfig(status)
  
  if (compact) {
    return (
      <span
        className="data-status-indicator compact"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 6px',
          borderRadius: '4px',
          fontSize: '0.75rem',
          fontWeight: '500',
          color: config.color,
          backgroundColor: config.bgColor,
          border: `1px solid ${config.borderColor}`,
        }}
        title={error || `數據狀態: ${config.text}${lastUpdate ? ` | 更新: ${new Date(lastUpdate).toLocaleTimeString()}` : ''}`}
      >
        <span>{config.icon}</span>
        <span>{config.text}</span>
      </span>
    )
  }

  return (
    <div
      className="data-status-indicator"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 12px',
        borderRadius: '8px',
        fontSize: '0.875rem',
        fontWeight: '500',
        color: config.color,
        backgroundColor: config.bgColor,
        border: `1px solid ${config.borderColor}`,
        margin: '8px 0',
      }}
    >
      <span style={{ fontSize: '1rem' }}>{config.icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {label && (
            <span style={{ color: 'white', opacity: 0.8 }}>
              {label}:
            </span>
          )}
          <span>{config.text}</span>
        </div>
        
        {error && (
          <div
            style={{
              fontSize: '0.75rem',
              color: '#ef4444',
              marginTop: '2px',
              opacity: 0.9,
            }}
          >
            {error}
          </div>
        )}
        
        {lastUpdate && !error && (
          <div
            style={{
              fontSize: '0.75rem',
              color: 'white',
              opacity: 0.6,
              marginTop: '2px',
            }}
          >
            更新時間: {new Date(lastUpdate).toLocaleString()}
          </div>
        )}
      </div>
      
      {status === 'loading' && (
        <div
          style={{
            width: '16px',
            height: '16px',
            border: '2px solid transparent',
            borderTop: `2px solid ${config.color}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
      )}
    </div>
  )
}

// 組合狀態指示器 - 顯示多個數據源的狀態
interface MultiDataStatusIndicatorProps {
  statuses: Array<{
    label: string
    status: DataSourceStatus
    error?: string
    lastUpdate?: string
  }>
  overallStatus: DataSourceStatus
}

export const MultiDataStatusIndicator: React.FC<MultiDataStatusIndicatorProps> = ({
  statuses,
  overallStatus
}) => {
  const overallConfig = getStatusConfig(overallStatus)
  
  return (
    <div className="multi-data-status-indicator" style={{ marginBottom: '16px' }}>
      {/* 整體狀態 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 12px',
          borderRadius: '8px',
          fontSize: '0.9rem',
          fontWeight: '600',
          color: overallConfig.color,
          backgroundColor: overallConfig.bgColor,
          border: `2px solid ${overallConfig.borderColor}`,
          marginBottom: '8px',
        }}
      >
        <span style={{ fontSize: '1.1rem' }}>{overallConfig.icon}</span>
        <span>整體數據狀態: {overallConfig.text}</span>
      </div>
      
      {/* 個別數據源狀態 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '8px',
        }}
      >
        {statuses.map((item, index) => (
          <DataStatusIndicator
            key={index}
            status={item.status}
            error={item.error}
            lastUpdate={item.lastUpdate}
            label={item.label}
            compact
          />
        ))}
      </div>
    </div>
  )
}

export default DataStatusIndicator

// CSS 動畫
const style = document.createElement('style')
style.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`
document.head.appendChild(style)