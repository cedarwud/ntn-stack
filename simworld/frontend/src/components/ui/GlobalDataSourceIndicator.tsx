/**
 * 全局數據源狀態指示器
 * 顯示 NetStack ↔ SimWorld ↔ Frontend 三層數據流的同步狀態
 */

import React from 'react'
import { useDataSync, useDataSourceStatus, useSyncStatus } from '../../contexts/DataSyncContext'
import './GlobalDataSourceIndicator.scss'

interface GlobalDataSourceIndicatorProps {
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
  compact?: boolean
  showDetails?: boolean
}

const GlobalDataSourceIndicator: React.FC<GlobalDataSourceIndicatorProps> = ({
  position = 'top-right',
  compact = false,
  showDetails = true
}) => {
  const { forceSync } = useDataSync()
  const { netstack, simworld, overall, dataSource } = useDataSourceStatus()
  const { isActive, consistency, errors, lastSyncTime } = useSyncStatus()

  const getOverallStatusColor = () => {
    if (isActive) return '#ffa500'
    switch (overall) {
      case 'fully_connected': return '#44ff44'
      case 'partially_connected': return '#ffaa00'
      default: return '#ff4444'
    }
  }

  const getOverallStatusIcon = () => {
    if (isActive) return '⏳'
    switch (overall) {
      case 'fully_connected': return '✅'
      case 'partially_connected': return '⚠️'
      default: return '❌'
    }
  }

  const getOverallStatusText = () => {
    if (isActive) return 'Syncing...'
    switch (overall) {
      case 'fully_connected': return 'All Systems Connected'
      case 'partially_connected': return 'Partial Connection'
      default: return 'Disconnected'
    }
  }

  const getDataSourceLabel = () => {
    switch (dataSource) {
      case 'real': return 'Real Data'
      case 'mixed': return 'Mixed Data'
      case 'simulated': return 'Simulated Data'
      default: return 'Unknown'
    }
  }

  const formatLastSyncTime = () => {
    if (!lastSyncTime) return 'Never'
    const now = Date.now()
    const diff = Math.floor((now - lastSyncTime) / 1000)
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    return `${Math.floor(diff / 3600)}h ago`
  }

  return (
    <div className={`global-data-source-indicator ${position} ${compact ? 'compact' : ''}`}>
      {/* 主要狀態顯示 */}
      <div className="main-status">
        <div 
          className="status-indicator"
          style={{ color: getOverallStatusColor() }}
        >
          <span className="status-icon">{getOverallStatusIcon()}</span>
          {!compact && (
            <span className="status-text">{getOverallStatusText()}</span>
          )}
        </div>
        
        {!compact && (
          <div className="data-source-label">
            {getDataSourceLabel()}
          </div>
        )}
      </div>

      {/* 詳細狀態 */}
      {showDetails && !compact && (
        <div className="details">
          {/* 服務狀態 */}
          <div className="service-status">
            <div className={`service ${netstack ? 'connected' : 'disconnected'}`}>
              <span className="service-icon">
                {netstack ? '🟢' : '🔴'}
              </span>
              <span className="service-name">NetStack</span>
            </div>
            
            <div className={`service ${simworld ? 'connected' : 'disconnected'}`}>
              <span className="service-icon">
                {simworld ? '🟢' : '🔴'}
              </span>
              <span className="service-name">SimWorld</span>
            </div>
          </div>

          {/* 同步信息 */}
          <div className="sync-info">
            <div className="sync-row">
              <span className="sync-label">Consistency:</span>
              <span className={`sync-value ${consistency}`}>
                {consistency.replace('_', ' ')}
              </span>
            </div>
            
            <div className="sync-row">
              <span className="sync-label">Last Sync:</span>
              <span className="sync-value">{formatLastSyncTime()}</span>
            </div>
          </div>

          {/* 錯誤信息 */}
          {errors.length > 0 && (
            <div className="error-info">
              <div className="error-header">
                Recent Errors ({errors.length}):
              </div>
              <div className="error-list">
                {errors.slice(-2).map((error, index) => (
                  <div key={index} className="error-item">
                    {error.length > 40 ? `${error.slice(0, 40)}...` : error}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 操作按鈕 */}
      <div className="actions">
        <button 
          className="sync-button"
          onClick={forceSync}
          disabled={isActive}
          title="Force sync all services"
        >
          🔄
        </button>
      </div>

      {/* 加載動畫 */}
      {isActive && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}
    </div>
  )
}

export default GlobalDataSourceIndicator