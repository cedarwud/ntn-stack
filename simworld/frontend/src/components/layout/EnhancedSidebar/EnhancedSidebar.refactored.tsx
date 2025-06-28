/**
 * 重構後的 Enhanced Sidebar 組件
 * 使用模組化架構，減少主組件複雜度
 */

import React, { useState, Suspense } from 'react'
import '../../../styles/Sidebar.scss'

// 重構後的模組導入
import { EnhancedSidebarProps } from './types'
import { FeatureConfigService } from './services/featureConfigService'
import { useSatelliteData } from './hooks/useSatelliteData'
import { useDeviceManagement } from './hooks/useDeviceManagement'
import FeatureToggleSection from './components/FeatureToggleSection'
import DeviceManagementSection from './components/DeviceManagementSection'
import SidebarStarfield from '../../shared/ui/effects/SidebarStarfield'

// 懶加載組件
const HandoverManager = React.lazy(
  () => import('../../domains/handover/execution/HandoverManager')
)

const EnhancedSidebarRefactored: React.FC<EnhancedSidebarProps> = (props) => {
  const {
    devices,
    loading,
    apiStatus,
    onDeviceChange,
    onDeleteDevice,
    onAddDevice,
    onApply,
    onCancel,
    hasTempDevices,
    auto,
    onAutoChange,
    onManualControl,
    activeComponent,
    uavAnimation,
    onUavAnimationChange,
    onSelectedReceiversChange,
    onSatelliteDataUpdate,
    satelliteEnabled,
    onSatelliteEnabledChange,
    manualControlEnabled,
    onManualControlEnabledChange,
  } = props

  // 本地狀態
  const [activeCategory, setActiveCategory] = useState('uav')
  const [searchQuery, setSearchQuery] = useState('')

  // 衛星數據管理
  const satelliteData = useSatelliteData({
    enabled: satelliteEnabled || false,
    onDataUpdate: onSatelliteDataUpdate,
  })

  // 設備管理
  const deviceManagement = useDeviceManagement({
    devices,
    onDeviceChange,
    onSelectedReceiversChange,
  })

  // 功能配置
  const featureToggles = FeatureConfigService.getFeatureToggles(props)
  const categories = FeatureConfigService.getCategories()

  // 處理衛星啟用切換
  const handleSatelliteEnabledToggle = (enabled: boolean) => {
    if (onSatelliteEnabledChange) {
      onSatelliteEnabledChange(enabled)
    }
  }

  // 處理衛星-UAV 連接切換
  const handleSatelliteUavConnectionToggle = (enabled: boolean) => {
    if (props.onSatelliteUavConnectionChange) {
      props.onSatelliteUavConnectionChange(enabled)
    }
  }

  // 渲染標籤頁內容
  const renderTabContent = () => {
    switch (activeCategory) {
      case 'uav':
      case 'satellite':
      case 'quality':
        return (
          <FeatureToggleSection
            features={FeatureConfigService.getFeaturesByCategory(featureToggles, activeCategory)}
            categories={categories.filter(c => c.id === activeCategory)}
            activeCategory={activeCategory}
            onCategoryChange={setActiveCategory}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
          />
        )

      case 'handover_mgr':
        return (
          <Suspense fallback={<div className="loading">載入換手管理器...</div>}>
            <HandoverManager />
          </Suspense>
        )

      case 'devices':
        return (
          <DeviceManagementSection
            devices={devices}
            loading={loading}
            onDeviceChange={onDeviceChange}
            onDeleteDevice={onDeleteDevice}
            onAddDevice={onAddDevice}
            onApply={onApply}
            onCancel={onCancel}
            hasTempDevices={hasTempDevices}
            manualControlEnabled={manualControlEnabled}
            onManualControl={onManualControl}
            onSelectedReceiversChange={onSelectedReceiversChange}
            orientationInputs={deviceManagement.orientationInputs}
            onOrientationInputChange={deviceManagement.handleDeviceOrientationInputChange}
            onOrientationApply={deviceManagement.applyDeviceOrientationChange}
          />
        )

      default:
        return <div>未知的標籤頁</div>
    }
  }

  // 渲染標籤頁導航
  const renderTabNavigation = () => {
    const tabs = [
      ...categories,
      { id: 'devices', label: '設備管理', icon: '📱' },
    ]

    return (
      <div className="tab-navigation">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-button ${activeCategory === tab.id ? 'active' : ''}`}
            onClick={() => setActiveCategory(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
    )
  }

  // 渲染狀態指示器
  const renderStatusIndicator = () => {
    const getStatusColor = () => {
      switch (apiStatus) {
        case 'connected': return '#4ade80'
        case 'error': return '#ef4444'
        case 'disconnected': return '#6b7280'
        default: return '#6b7280'
      }
    }

    const getStatusText = () => {
      switch (apiStatus) {
        case 'connected': return '已連接'
        case 'error': return '連接錯誤'
        case 'disconnected': return '未連接'
        default: return '未知狀態'
      }
    }

    return (
      <div className="status-indicator">
        <div
          className="status-dot"
          style={{ backgroundColor: getStatusColor() }}
        />
        <span className="status-text">{getStatusText()}</span>
      </div>
    )
  }

  // 渲染衛星狀態
  const renderSatelliteStatus = () => {
    if (!satelliteEnabled) return null

    return (
      <div className="satellite-status">
        <div className="satellite-info">
          <span className="satellite-icon">🛰️</span>
          <span className="satellite-count">
            {satelliteData.isLoading ? '載入中...' : `${satelliteData.satellites.length} 顆衛星`}
          </span>
        </div>
        
        {satelliteData.error && (
          <div className="satellite-error">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{satelliteData.error}</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={`enhanced-sidebar ${activeComponent}`}>
      {/* 背景效果 */}
      <SidebarStarfield />

      {/* Sidebar 標題 */}
      <div className="sidebar-header">
        <h2 className="sidebar-title">🚀 SimWorld 控制台</h2>
        {renderStatusIndicator()}
      </div>

      {/* 衛星狀態 */}
      {renderSatelliteStatus()}

      {/* 標籤頁導航 */}
      {renderTabNavigation()}

      {/* 主要內容區域 */}
      <div className="sidebar-content">
        {renderTabContent()}
      </div>

      {/* 底部操作區 */}
      <div className="sidebar-footer">
        {/* 全域搜尋 */}
        <div className="global-search">
          <input
            type="text"
            placeholder="搜尋功能或設備..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        {/* 快速操作 */}
        <div className="quick-actions">
          <button
            className={`quick-action ${auto ? 'active' : ''}`}
            onClick={() => onAutoChange(!auto)}
            title="切換自動/手動模式"
          >
            {auto ? '🤖' : '🕹️'}
          </button>
          
          <button
            className={`quick-action ${uavAnimation ? 'active' : ''}`}
            onClick={() => onUavAnimationChange(!uavAnimation)}
            title="切換動畫效果"
          >
            🎬
          </button>
          
          <button
            className={`quick-action ${satelliteEnabled ? 'active' : ''}`}
            onClick={() => handleSatelliteEnabledToggle(!satelliteEnabled)}
            title="切換衛星顯示"
          >
            🛰️
          </button>
        </div>
      </div>
    </div>
  )
}

export default EnhancedSidebarRefactored