import React, { useState } from 'react'
import { UAVSelectionPanelProps } from '../types/sidebar.types'

const UAVSelectionPanel: React.FC<UAVSelectionPanelProps> = ({
    devices,
    selectedReceiverIds,
    isVisible,
    onSelectionChange,
    onBadgeClick,
}) => {
    const [showUavSelection, setShowUavSelection] = useState(false)

    if (!isVisible) {
        return null
    }

    return (
        <div className="uav-selection-container">
            <div
                className={`uav-selection-header ${
                    showUavSelection ? 'expanded' : ''
                }`}
                onClick={() => setShowUavSelection(!showUavSelection)}
            >
                <span className="selection-title">🚁 UAV 接收器選擇</span>
                <span className="selection-count">
                    {selectedReceiverIds.length} /{' '}
                    {
                        devices.filter(
                            (d) => d.role === 'receiver' && d.id !== null
                        ).length
                    }
                </span>
                <span
                    className={`header-arrow ${
                        showUavSelection ? 'expanded' : ''
                    }`}
                >
                    ▼
                </span>
            </div>
            {showUavSelection && (
                <>
                    <div className="uav-badges-grid">
                        {devices
                            .filter(
                                (device) =>
                                    device.name &&
                                    device.role === 'receiver' &&
                                    device.id !== null
                            )
                            .map((device) => {
                                const isSelected = selectedReceiverIds.includes(
                                    device.id as number
                                )
                                // 設備狀態數據
                                const connectionStatus = device.active
                                    ? 'connected'
                                    : 'disconnected'
                                // 基於設備ID生成穩定的模擬數據
                                const deviceIdNum =
                                    typeof device.id === 'number'
                                        ? device.id
                                        : 0
                                const signalStrength = (deviceIdNum % 4) + 1 // 1-4 bars，基於ID固定
                                const batteryLevel = Math.max(
                                    20,
                                    100 - ((deviceIdNum * 7) % 80)
                                ) // 20-100%，基於ID固定

                                return (
                                    <div
                                        key={device.id}
                                        className={`enhanced-uav-badge ${
                                            isSelected ? 'selected' : ''
                                        } ${connectionStatus}`}
                                        onClick={() =>
                                            onBadgeClick(device.id as number)
                                        }
                                        title={`點擊${
                                            isSelected ? '取消選擇' : '選擇'
                                        } ${device.name}`}
                                    >
                                        <div className="badge-header">
                                            <span className="device-name">
                                                {device.name}
                                            </span>
                                            <div className="status-indicators">
                                                <span
                                                    className={`connection-dot ${connectionStatus}`}
                                                ></span>
                                                <span className="signal-bars">
                                                    {Array.from(
                                                        { length: 4 },
                                                        (_, i) => (
                                                            <span
                                                                key={i}
                                                                className={`signal-bar ${
                                                                    i <
                                                                    signalStrength
                                                                        ? 'active'
                                                                        : ''
                                                                }`}
                                                            ></span>
                                                        )
                                                    )}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="badge-info">
                                            <div className="info-item">
                                                <span className="info-label">
                                                    位置:
                                                </span>
                                                <span className="info-value">
                                                    (
                                                    {device.position_x !== undefined
                                                        ? device.position_x.toFixed(1)
                                                        : '0.0'}
                                                    ,{' '}
                                                    {device.position_y !== undefined
                                                        ? device.position_y.toFixed(1)
                                                        : '0.0'}
                                                    ,{' '}
                                                    {device.position_z !== undefined
                                                        ? device.position_z.toFixed(1)
                                                        : '0.0'}
                                                    )
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="info-label">
                                                    功率:
                                                </span>
                                                <span className="info-value">
                                                    {device.power_dbm?.toFixed(1) ??
                                                        'N/A'}{' '}
                                                    dBm
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="info-label">
                                                    電量:
                                                </span>
                                                <span
                                                    className={`battery-level ${
                                                        batteryLevel > 60
                                                            ? 'high'
                                                            : batteryLevel > 30
                                                            ? 'medium'
                                                            : 'low'
                                                    }`}
                                                >
                                                    {batteryLevel}%
                                                </span>
                                            </div>
                                        </div>
                                        {isSelected && (
                                            <div className="selection-indicator">
                                                <span className="checkmark">
                                                    ✓
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                    </div>
                    {selectedReceiverIds.length > 0 && (
                        <div className="selection-actions">
                            <button
                                className="action-btn clear-selection"
                                onClick={() =>
                                    onSelectionChange && onSelectionChange([])
                                }
                            >
                                清除選擇
                            </button>
                            <button
                                className="action-btn select-all"
                                onClick={() => {
                                    const allIds = devices
                                        .filter(
                                            (d) =>
                                                d.role === 'receiver' &&
                                                d.id !== null
                                        )
                                        .map((d) => d.id as number)
                                    if (onSelectionChange) {
                                        onSelectionChange(allIds)
                                    }
                                }}
                            >
                                全部選擇
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default UAVSelectionPanel