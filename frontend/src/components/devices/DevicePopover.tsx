import React from 'react'

export interface DevicePopoverProps {
    show: boolean
    position: {
        x: number
        y: number
        clientX: number
        clientY: number
        sceneX?: number
        sceneY?: number
    } | null
    device: any
    isEditing: boolean
    onChange: (field: string, value: any) => void
    onOrientationInput: (axis: 'x' | 'y' | 'z', value: string) => void
    orientationInputs: { [key: string]: { x: string; y: string; z: string } }
    onApply: (e: React.FormEvent) => void
    onDelete: () => void
    onClose: () => void
    onRoleChange: (role: string) => void
}

const DevicePopover: React.FC<DevicePopoverProps> = ({
    show,
    position,
    device,
    isEditing,
    onChange,
    onOrientationInput,
    orientationInputs,
    onApply,
    onDelete,
    onClose,
    onRoleChange,
}) => {
    if (!show || !position) return null
    return (
        <div
            style={{
                position: 'fixed',
                background: '#1e2536',
                color: '#eaf6ff',
                boxShadow: '0 4px 24px 0 rgba(0,0,0,0.45)',
                borderRadius: '8px',
                border: '1px solid #3a4a6a',
                padding: '18px 18px 12px 18px',
                zIndex: 1000,
                left: `${position.clientX}px`,
                top: `${position.clientY + 10}px`,
                transform: 'translateX(-50%)',
                width: '340px',
                fontSize: '0.95rem',
            }}
        >
            <div className="device-header">
                <input
                    type="text"
                    value={device.name}
                    onChange={(e) => onChange('name', e.target.value)}
                    placeholder="設備名稱"
                    className="device-name-input"
                />
                <button
                    className="delete-btn"
                    onClick={isEditing ? onDelete : onClose}
                    title={isEditing ? '刪除設備' : '關閉'}
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
                                    onChange={(e) =>
                                        onRoleChange(e.target.value)
                                    }
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
                                        onChange('position_x', e.target.value)
                                    }
                                />
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={device.position_y}
                                    onChange={(e) =>
                                        onChange('position_y', e.target.value)
                                    }
                                />
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={device.position_z}
                                    onChange={(e) =>
                                        onChange('position_z', e.target.value)
                                    }
                                    step="0.1"
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
                                            onChange(
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
                                        value={
                                            orientationInputs['popover']?.x ||
                                            '0'
                                        }
                                        onChange={(e) =>
                                            onOrientationInput(
                                                'x',
                                                e.target.value
                                            )
                                        }
                                    />
                                </td>
                                <td>
                                    <input
                                        type="text"
                                        value={
                                            orientationInputs['popover']?.y ||
                                            '0'
                                        }
                                        onChange={(e) =>
                                            onOrientationInput(
                                                'y',
                                                e.target.value
                                            )
                                        }
                                    />
                                </td>
                                <td>
                                    <input
                                        type="text"
                                        value={
                                            orientationInputs['popover']?.z ||
                                            '0'
                                        }
                                        onChange={(e) =>
                                            onOrientationInput(
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
            <div className="action-buttons">
                <button
                    onClick={onApply}
                    className="add-device-btn"
                    disabled={!device.name}
                >
                    套用
                </button>
                <button onClick={onClose} className="add-device-btn">
                    取消
                </button>
            </div>
        </div>
    )
}

export default DevicePopover
