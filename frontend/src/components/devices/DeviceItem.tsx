import React from 'react'
import { Device } from '../../types/device'

interface DeviceItemProps {
    device: Device
    orientationInput: { x: string; y: string; z: string }
    onDeviceChange: (id: number, field: keyof Device, value: any) => void
    onDeleteDevice: (id: number) => void
    onOrientationInputChange: (
        deviceId: number,
        axis: 'x' | 'y' | 'z',
        value: string
    ) => void
    onDeviceRoleChange?: (deviceId: number, newRole: string) => void
}

const DeviceItem: React.FC<DeviceItemProps> = ({
    device,
    orientationInput,
    onDeviceChange,
    onDeleteDevice,
    onOrientationInputChange,
    onDeviceRoleChange,
}) => {
    const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newRole = e.target.value
        if (onDeviceRoleChange) {
            onDeviceRoleChange(device.id, newRole)
        } else {
            onDeviceChange(device.id, 'role', newRole)
        }
    }

    return (
        <div key={device.id} className="device-item">
            <div className="device-header">
                <input
                    type="text"
                    value={device.name}
                    onChange={(e) =>
                        onDeviceChange(device.id, 'name', e.target.value)
                    }
                    className="device-name-input"
                />
                <button
                    className="delete-btn"
                    onClick={() => onDeleteDevice(device.id)}
                >
                    &#10006;
                </button>
            </div>
            <div className="device-content">
                <table className="device-table">
                    <thead>
                        <tr>
                            <th>類型</th>
                            <th>X 位置</th>
                            <th>Y 位置</th>
                            <th>Z 位置</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>
                                <select
                                    value={device.role}
                                    onChange={handleRoleChange}
                                    className="device-type-select"
                                >
                                    <option value="receiver">接收器</option>
                                    <option value="desired">發射器</option>
                                    <option value="jammer">干擾源</option>
                                </select>
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={device.position_x}
                                    onChange={(e) =>
                                        onDeviceChange(
                                            device.id,
                                            'position_x',
                                            parseFloat(e.target.value) || 0
                                        )
                                    }
                                />
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={device.position_y}
                                    onChange={(e) =>
                                        onDeviceChange(
                                            device.id,
                                            'position_y',
                                            parseFloat(e.target.value) || 0
                                        )
                                    }
                                />
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={device.position_z}
                                    onChange={(e) =>
                                        onDeviceChange(
                                            device.id,
                                            'position_z',
                                            parseInt(e.target.value, 10) || 0
                                        )
                                    }
                                />
                            </td>
                        </tr>
                    </tbody>
                </table>

                {device.role !== 'receiver' && (
                    <table className="device-table orientation-table">
                        <thead>
                            <tr>
                                <th>功率 (dBm)</th>
                                <th>X 方向</th>
                                <th>Y 方向</th>
                                <th>Z 方向</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>
                                    <input
                                        type="number"
                                        value={device.power_dbm || 0}
                                        onChange={(e) =>
                                            onDeviceChange(
                                                device.id,
                                                'power_dbm',
                                                parseInt(e.target.value, 10) ||
                                                    0
                                            )
                                        }
                                    />
                                </td>
                                <td>
                                    <input
                                        type="text"
                                        value={orientationInput.x}
                                        onChange={(e) =>
                                            onOrientationInputChange(
                                                device.id,
                                                'x',
                                                e.target.value
                                            )
                                        }
                                    />
                                </td>
                                <td>
                                    <input
                                        type="text"
                                        value={orientationInput.y}
                                        onChange={(e) =>
                                            onOrientationInputChange(
                                                device.id,
                                                'y',
                                                e.target.value
                                            )
                                        }
                                    />
                                </td>
                                <td>
                                    <input
                                        type="text"
                                        value={orientationInput.z}
                                        onChange={(e) =>
                                            onOrientationInputChange(
                                                device.id,
                                                'z',
                                                e.target.value
                                            )
                                        }
                                    />
                                </td>
                            </tr>
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}

export default DeviceItem
