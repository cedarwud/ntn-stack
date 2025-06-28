/**
 * 設備管理區塊組件
 * 顯示設備列表和管理操作
 */

import React from 'react'
import { Device } from '../../../../types/device'
import DeviceItem from '../../../domains/device/management/DeviceItem'
import { useReceiverSelection } from '../../../../hooks/useReceiverSelection'
import { UAVManualDirection } from '../../../domains/device/visualization/UAVFlight'

interface DeviceManagementSectionProps {
  devices: Device[]
  loading: boolean
  onDeviceChange: (id: number, field: keyof Device, value: unknown) => void
  onDeleteDevice: (id: number) => void
  onAddDevice: () => void
  onApply: () => void
  onCancel: () => void
  hasTempDevices: boolean
  
  // 手動控制
  manualControlEnabled?: boolean
  onManualControl?: (direction: UAVManualDirection) => void
  
  // 接收器選擇
  onSelectedReceiversChange?: (selectedIds: number[]) => void
  
  // 方向輸入處理
  orientationInputs?: Record<number, { x: string; y: string; z: string }>
  onOrientationInputChange?: (deviceId: number, axis: 'x' | 'y' | 'z', value: string) => void
  onOrientationApply?: (deviceId: number, axis: 'x' | 'y' | 'z') => void
}

const DeviceManagementSection: React.FC<DeviceManagementSectionProps> = ({
  devices,
  loading,
  onDeviceChange,
  onDeleteDevice,
  onAddDevice,
  onApply,
  onCancel,
  hasTempDevices,
  manualControlEnabled,
  onManualControl,
  onSelectedReceiversChange,
  orientationInputs = {},
  onOrientationInputChange,
  onOrientationApply,
}) => {
  const { selectedReceivers, toggleReceiver, clearSelection } = useReceiverSelection({
    devices,
    onSelectedReceiversChange,
  })

  // 手動控制按鈕配置
  const manualControlButtons = [
    { direction: 'forward' as UAVManualDirection, label: '前進', icon: '⬆️' },
    { direction: 'backward' as UAVManualDirection, label: '後退', icon: '⬇️' },
    { direction: 'left' as UAVManualDirection, label: '左轉', icon: '⬅️' },
    { direction: 'right' as UAVManualDirection, label: '右轉', icon: '➡️' },
    { direction: 'up' as UAVManualDirection, label: '上升', icon: '🔺' },
    { direction: 'down' as UAVManualDirection, label: '下降', icon: '🔻' },
  ]

  // 渲染手動控制面板
  const renderManualControlPanel = () => {
    if (!manualControlEnabled || !onManualControl) {
      return null
    }

    return (
      <div className="manual-control-panel">
        <div className="panel-header">
          <h4>🕹️ UAV 手動控制</h4>
        </div>
        <div className="control-grid">
          {manualControlButtons.map((button) => (
            <button
              key={button.direction}
              className="control-button"
              onClick={() => onManualControl(button.direction)}
              title={button.label}
            >
              <span className="control-icon">{button.icon}</span>
              <span className="control-label">{button.label}</span>
            </button>
          ))}
        </div>
      </div>
    )
  }

  // 渲染設備統計
  const renderDeviceStats = () => {
    const stats = {
      total: devices.length,
      transmitters: devices.filter(d => d.role === 'transmitter').length,
      receivers: devices.filter(d => d.role === 'receiver').length,
      selected: selectedReceivers.length,
    }

    return (
      <div className="device-stats">
        <div className="stats-row">
          <span className="stats-item">
            總計: <strong>{stats.total}</strong>
          </span>
          <span className="stats-item">
            發射器: <strong>{stats.transmitters}</strong>
          </span>
        </div>
        <div className="stats-row">
          <span className="stats-item">
            接收器: <strong>{stats.receivers}</strong>
          </span>
          <span className="stats-item">
            已選: <strong>{stats.selected}</strong>
          </span>
        </div>
      </div>
    )
  }

  // 渲染操作按鈕
  const renderActionButtons = () => {
    return (
      <div className="device-actions">
        <div className="action-row">
          <button
            className="action-button add-button"
            onClick={onAddDevice}
            disabled={loading}
          >
            ➕ 新增設備
          </button>
          
          {selectedReceivers.length > 0 && (
            <button
              className="action-button clear-button"
              onClick={clearSelection}
            >
              🗑️ 清除選擇
            </button>
          )}
        </div>

        {hasTempDevices && (
          <div className="action-row">
            <button
              className="action-button apply-button"
              onClick={onApply}
              disabled={loading}
            >
              ✅ 套用變更
            </button>
            <button
              className="action-button cancel-button"
              onClick={onCancel}
              disabled={loading}
            >
              ❌ 取消變更
            </button>
          </div>
        )}
      </div>
    )
  }

  // 渲染設備列表
  const renderDeviceList = () => {
    if (loading) {
      return (
        <div className="device-list-loading">
          <div className="loading-spinner"></div>
          <span>載入設備中...</span>
        </div>
      )
    }

    if (devices.length === 0) {
      return (
        <div className="no-devices">
          <span className="no-devices-icon">📱</span>
          <span className="no-devices-text">尚無設備</span>
          <button className="add-first-device" onClick={onAddDevice}>
            新增第一個設備
          </button>
        </div>
      )
    }

    return (
      <div className="device-list">
        {devices.map((device) => (
          <DeviceItem
            key={device.id}
            device={device}
            isSelected={selectedReceivers.includes(device.id)}
            onToggleSelection={() => toggleReceiver(device.id)}
            onDeviceChange={onDeviceChange}
            onDeleteDevice={onDeleteDevice}
            orientationInput={orientationInputs[device.id]}
            onOrientationInputChange={onOrientationInputChange}
            onOrientationApply={onOrientationApply}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="device-management-section">
      {/* 設備統計 */}
      {renderDeviceStats()}

      {/* 手動控制面板 */}
      {renderManualControlPanel()}

      {/* 操作按鈕 */}
      {renderActionButtons()}

      {/* 設備列表 */}
      {renderDeviceList()}
    </div>
  )
}

export default DeviceManagementSection