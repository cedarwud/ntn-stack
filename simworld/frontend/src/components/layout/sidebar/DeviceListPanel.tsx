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
    // 設備計數邏輯
    const totalDevices = receiverDevices.length + desiredDevices.length + jammerDevices.length;
    const hasDeviceData = totalDevices > 0;
    
    // 本地展開/收合狀態 - 預設收合所有UAV設備分類
    const [showTempDevices, setShowTempDevices] = useState(false)
    const [showReceiverSection, setShowReceiverSection] = useState(false)
    const [showDesiredSection, setShowDesiredSection] = useState(false)
    const [showJammerSection, setShowJammerSection] = useState(false)
    
    // 衛星 gNB 預設開啟
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

            {/* UAV設備分類 - 只在有UAV設備數據且不是純衛星模式時顯示 */}
            {hasDeviceData && (
                <>
                    {/* 接收器 Rx 區塊 */}
                    {receiverDevices.length > 0 && (
                        <>
                            <h3
                                className={`section-header ${
                                    showReceiverSection ? 'expanded' : ''
                                }`}
                                onClick={() =>
                                    setShowReceiverSection(!showReceiverSection)
                                }
                            >
                                <span className="header-icon">📡</span>
                                <span className="header-title">接收器 Rx</span>
                                <span className="header-count">
                                    ({receiverDevices.length})
                                </span>
                            </h3>
                            {showReceiverSection &&
                                receiverDevices.map((device, index) => (
                                    <DeviceItem
                                        key={device.id || `receiver-${index}`}
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

                    {/* 發射器 Tx 區塊 */}
                    {desiredDevices.length > 0 && (
                        <>
                            <h3
                                className={`section-header ${
                                    showDesiredSection ? 'expanded' : ''
                                }`}
                                onClick={() =>
                                    setShowDesiredSection(!showDesiredSection)
                                }
                            >
                                <span className="header-icon">📶</span>
                                <span className="header-title">發射器 Tx</span>
                                <span className="header-count">
                                    ({desiredDevices.length})
                                </span>
                            </h3>
                            {showDesiredSection &&
                                desiredDevices.map((device, index) => (
                                    <DeviceItem
                                        key={device.id || `desired-${index}`}
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

                    {/* 干擾源 Jam 區塊 */}
                    {jammerDevices.length > 0 && (
                        <>
                            <h3
                                className={`section-header ${
                                    showJammerSection ? 'expanded' : ''
                                }`}
                                onClick={() =>
                                    setShowJammerSection(!showJammerSection)
                                }
                            >
                                <span className="header-icon">⚡</span>
                                <span className="header-title">干擾源 Jam</span>
                                <span className="header-count">
                                    ({jammerDevices.length})
                                </span>
                            </h3>
                            {showJammerSection &&
                                jammerDevices.map((device, index) => (
                                    <DeviceItem
                                        key={device.id || `jammer-${index}`}
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
                </>
            )}

            {/* 衛星資料區塊 - 只在衛星模式啟用時顯示 */}
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
                                        key={sat.norad_id || sat.name || `sat-${Math.random()}`}
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

        </div>
    )
}

export default DeviceListPanel