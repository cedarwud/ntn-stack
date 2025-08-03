import React, { useState } from 'react'
import { DeviceListPanelProps } from '../types/sidebar.types'
import DeviceItem from '../../domains/device/management/DeviceItem'

const DeviceListPanel: React.FC<DeviceListPanelProps> = ({
    devices: _devices,
    tempDevices,
    receiverDevices,
    desiredDevices,
    jammerDevices,
    skyfieldSatellites,
    satelliteEnabled,
    loadingSatellites,
    orientationInputs,
    onDeviceChange,
    onDeleteDevice,
    onOrientationInputChange,
    onDeviceRoleChange,
}) => {
    // 本地展開/收合狀態
    const [showTempDevices, setShowTempDevices] = useState(true)
    const [showReceiverDevices, setShowReceiverDevices] = useState(false)
    const [showDesiredDevices, setShowDesiredDevices] = useState(false)
    const [showJammerDevices, setShowJammerDevices] = useState(false)
    const [showSkyfieldSection, setShowSkyfieldSection] = useState(true)

    return (
        <div className="device-list-panel">
            {/* 新增設備區塊 */}
            {tempDevices.length > 0 && (
                <>
                    <h3
                        className={`section-header ${
                            showTempDevices ? 'expanded' : ''
                        }`}
                        onClick={() => setShowTempDevices(!showTempDevices)}
                    >
                        <span className="header-icon">➕</span>
                        <span className="header-title">新增設備</span>
                        <span className="header-count">
                            ({tempDevices.length})
                        </span>
                    </h3>
                    {showTempDevices &&
                        tempDevices.map((device, index) => (
                            <DeviceItem
                                key={device.id || `temp-device-${index}`}
                                device={device}
                                orientationInput={
                                    orientationInputs[device.id] || {
                                        x: '0',
                                        y: '0',
                                        z: '0',
                                    }
                                }
                                onDeviceChange={onDeviceChange}
                                onDeleteDevice={onDeleteDevice}
                                onOrientationInputChange={
                                    onOrientationInputChange
                                }
                                onDeviceRoleChange={onDeviceRoleChange}
                            />
                        ))}
                </>
            )}

            {/* 衛星資料區塊 */}
            {satelliteEnabled && (
                <>
                    <h3
                        className={`section-header ${
                            showSkyfieldSection ? 'expanded' : ''
                        }`}
                        onClick={() =>
                            setShowSkyfieldSection(!showSkyfieldSection)
                        }
                    >
                        <span className="header-icon">🛰️</span>
                        <span className="header-title">衛星 gNB</span>
                        <span className="header-count">
                            (
                            {loadingSatellites
                                ? '...'
                                : skyfieldSatellites.length}
                            )
                        </span>
                    </h3>
                    {showSkyfieldSection && (
                        <div className="satellite-list">
                            {loadingSatellites ? (
                                <div className="loading-text">
                                    正在載入衛星資料...
                                </div>
                            ) : skyfieldSatellites.length > 0 ? (
                                skyfieldSatellites.map((sat) => (
                                    <div
                                        key={sat.norad_id}
                                        className="satellite-item"
                                    >
                                        <div className="satellite-name">
                                            {sat.name} (NORAD: {sat.norad_id})
                                        </div>
                                        <div className="satellite-details">
                                            仰角:{' '}
                                            <span
                                                style={{
                                                    color:
                                                        (sat.elevation_deg ??
                                                            0) > 45
                                                            ? '#ff3300'
                                                            : '#0088ff',
                                                }}
                                            >
                                                {(
                                                    sat.elevation_deg ?? 0
                                                ).toFixed(2)}
                                                °
                                            </span>
                                            {' | '}方位角:{' '}
                                            {(sat.azimuth_deg ?? 0).toFixed(2)}°
                                            {' | '}
                                            距離:{' '}
                                            {(sat.distance_km ?? 0).toFixed(
                                                2
                                            )}{' '}
                                            km
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="no-data-text">
                                    無衛星資料可顯示。請調整最低仰角後重試。
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* 接收器 */}
            {receiverDevices.length > 0 && (
                <>
                    <h3
                        className={`section-header ${
                            showReceiverDevices ? 'expanded' : ''
                        }`}
                        onClick={() =>
                            setShowReceiverDevices(!showReceiverDevices)
                        }
                    >
                        <span className="header-icon">📱</span>
                        <span className="header-title">接收器 Rx</span>
                        <span className="header-count">
                            ({receiverDevices.length})
                        </span>
                    </h3>
                    {showReceiverDevices &&
                        receiverDevices.map((device, index) => (
                            <DeviceItem
                                key={device.id || `receiver-device-${index}`}
                                device={device}
                                orientationInput={
                                    orientationInputs[device.id] || {
                                        x: '0',
                                        y: '0',
                                        z: '0',
                                    }
                                }
                                onDeviceChange={onDeviceChange}
                                onDeleteDevice={onDeleteDevice}
                                onOrientationInputChange={
                                    onOrientationInputChange
                                }
                                onDeviceRoleChange={onDeviceRoleChange}
                            />
                        ))}
                </>
            )}

            {/* 發射器 */}
            {desiredDevices.length > 0 && (
                <>
                    <h3
                        className={`section-header ${
                            showDesiredDevices ? 'expanded' : ''
                        }`}
                        onClick={() =>
                            setShowDesiredDevices(!showDesiredDevices)
                        }
                    >
                        <span className="header-icon">📡</span>
                        <span className="header-title">發射器 Tx</span>
                        <span className="header-count">
                            ({desiredDevices.length})
                        </span>
                    </h3>
                    {showDesiredDevices &&
                        desiredDevices.map((device, index) => (
                            <DeviceItem
                                key={device.id || `desired-device-${index}`}
                                device={device}
                                orientationInput={
                                    orientationInputs[device.id] || {
                                        x: '0',
                                        y: '0',
                                        z: '0',
                                    }
                                }
                                onDeviceChange={onDeviceChange}
                                onDeleteDevice={onDeleteDevice}
                                onOrientationInputChange={
                                    onOrientationInputChange
                                }
                                onDeviceRoleChange={onDeviceRoleChange}
                            />
                        ))}
                </>
            )}

            {/* 干擾源 */}
            {jammerDevices.length > 0 && (
                <>
                    <h3
                        className={`section-header ${
                            showJammerDevices ? 'expanded' : ''
                        }`}
                        onClick={() => setShowJammerDevices(!showJammerDevices)}
                    >
                        <span className="header-icon">⚡</span>
                        <span className="header-title">干擾源 Jam</span>
                        <span className="header-count">
                            ({jammerDevices.length})
                        </span>
                    </h3>
                    {showJammerDevices &&
                        jammerDevices.map((device, index) => (
                            <DeviceItem
                                key={device.id || `jammer-device-${index}`}
                                device={device}
                                orientationInput={
                                    orientationInputs[device.id] || {
                                        x: '0',
                                        y: '0',
                                        z: '0',
                                    }
                                }
                                onDeviceChange={onDeviceChange}
                                onDeleteDevice={onDeleteDevice}
                                onOrientationInputChange={
                                    onOrientationInputChange
                                }
                                onDeviceRoleChange={onDeviceRoleChange}
                            />
                        ))}
                </>
            )}
        </div>
    )
}

export default DeviceListPanel
