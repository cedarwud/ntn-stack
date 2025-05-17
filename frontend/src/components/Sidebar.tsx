import React, { useState, useEffect, useRef } from 'react'
import { Device } from '../App'
import '../styles/Sidebar.css'
import { UAVManualDirection } from './UAVFlight' // Assuming UAVFlight exports this

interface SidebarProps {
    devices: Device[]
    loading: boolean
    apiStatus: 'disconnected' | 'connected' | 'error'
    onDeviceChange: (id: number, field: keyof Device, value: any) => void
    onDeleteDevice: (id: number) => void
    onAddDevice: () => void
    onApply: () => void
    onCancel: () => void
    hasTempDevices: boolean
    auto: boolean
    onAutoChange: (auto: boolean) => void // Parent will use selected IDs
    onManualControl: (direction: UAVManualDirection) => void // Parent will use selected IDs
    activeComponent: string
    uavAnimation: boolean
    onUavAnimationChange: (val: boolean) => void // Parent will use selected IDs
    onSelectedReceiversChange?: (selectedIds: number[]) => void // New prop
}

// 星空星點動畫元件
const STAR_COUNT = 60
interface Star {
    left: number
    top: number
    size: number
    baseOpacity: number
    phase: number
    speed: number
    animOpacity: number
}
function createStars(): Star[] {
    return Array.from({ length: STAR_COUNT }, () => {
        const baseOpacity = Math.random() * 0.7 + 0.3
        return {
            left: Math.random() * 100,
            top: Math.random() * 100,
            size: Math.random() * 1.5 + 0.5,
            baseOpacity,
            phase: Math.random() * Math.PI * 2,
            speed: Math.random() * 1.0 + 1.0,
            animOpacity: baseOpacity,
        }
    })
}
const SidebarStarfield: React.FC = () => {
    const [starAnim, setStarAnim] = useState<Star[]>(() => createStars())
    useEffect(() => {
        let mounted = true
        let frame = 0
        const interval = setInterval(() => {
            if (!mounted) return
            setStarAnim((prev) =>
                prev.map((star) => {
                    const t = frame / 30
                    const flicker = Math.sin(t * star.speed + star.phase) * 0.5
                    let opacity = star.baseOpacity + flicker
                    opacity = Math.max(0.15, Math.min(1, opacity))
                    return { ...star, animOpacity: opacity }
                })
            )
            frame++
        }, 60)
        return () => {
            mounted = false
            clearInterval(interval)
        }
    }, [])
    return (
        <div
            style={{
                position: 'absolute',
                inset: 0,
                zIndex: 0,
                pointerEvents: 'none',
            }}
        >
            {starAnim.map((star, i) => (
                <div
                    key={i}
                    style={{
                        position: 'absolute',
                        left: `${star.left}%`,
                        top: `${star.top}%`,
                        width: `${star.size}px`,
                        height: `${star.size}px`,
                        borderRadius: '50%',
                        background: 'white',
                        opacity: star.animOpacity,
                        filter: 'blur(0.5px)',
                        transition: 'opacity 0.2s linear',
                    }}
                />
            ))}
        </div>
    )
}

const Sidebar: React.FC<SidebarProps> = ({
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
    onSelectedReceiversChange, // 接收從父組件傳來的回調函數
}) => {
    // 為每個設備的方向值創建本地狀態
    const [orientationInputs, setOrientationInputs] = useState<{
        [key: string]: { x: string; y: string; z: string }
    }>({})

    // 新增：持續發送控制指令的 interval id
    const manualIntervalRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    // 修改：初始化 selectedReceiverIds 包含所有 receiver ID
    // 這樣當 Sidebar 首次渲染時，所有 receiver badge 會呈現選中狀態
    const [selectedReceiverIds, setSelectedReceiverIds] = useState<number[]>(
        () => {
            // 獲取設備列表中所有合法的 receiver ID
            return devices
                .filter(
                    (device) => device.role === 'receiver' && device.id !== null
                )
                .map((device) => device.id as number)
        }
    )

    // 同步 selectedReceiverIds 與父組件
    useEffect(() => {
        // 當組件掛載時，通知父組件當前選中的 receiver IDs
        if (onSelectedReceiversChange) {
            onSelectedReceiversChange(selectedReceiverIds)
        }
    }, []) // 僅在組件掛載時執行一次

    // Effect to synchronize selectedReceiverIds with the current devices list
    useEffect(() => {
        const currentReceiverDeviceIds = devices
            .filter((d) => d.role === 'receiver' && d.id !== null)
            .map((d) => d.id as number)

        setSelectedReceiverIds((prevSelected) => {
            // 計算有效的 selectedIds（只包含當前存在的 receiver）
            const newSelected = prevSelected.filter((id) =>
                currentReceiverDeviceIds.includes(id)
            )

            // 如果沒有選中的接收器，則自動選中所有接收器
            const finalSelected =
                newSelected.length > 0
                    ? newSelected
                    : [...currentReceiverDeviceIds]

            // 如果選擇變更，通知父組件
            if (
                JSON.stringify(finalSelected) !== JSON.stringify(prevSelected)
            ) {
                if (onSelectedReceiversChange) {
                    onSelectedReceiversChange(finalSelected)
                }
            }
            return finalSelected
        })
    }, [devices, onSelectedReceiversChange])

    // 當 devices 更新時，初始化或更新本地輸入狀態
    useEffect(() => {
        const newInputs: {
            [key: string]: { x: string; y: string; z: string }
        } = {}
        devices.forEach((device) => {
            // 如果該設備已有本地輸入狀態，保留它；否則，從設備初始化
            if (!orientationInputs[device.id]) {
                newInputs[device.id] = {
                    x: device.orientation_x?.toString() || '0',
                    y: device.orientation_y?.toString() || '0',
                    z: device.orientation_z?.toString() || '0',
                }
            } else {
                newInputs[device.id] = orientationInputs[device.id]
            }
        })
        setOrientationInputs(newInputs)
    }, [devices])

    // Handler for badge click
    const handleBadgeClick = (deviceId: number | null) => {
        if (deviceId === null) return // Should not happen for displayed receiver badges

        setSelectedReceiverIds((prevSelected) => {
            const newSelected = prevSelected.includes(deviceId)
                ? prevSelected.filter((id) => id !== deviceId)
                : [...prevSelected, deviceId]

            // Notify parent component of the change in selection
            if (onSelectedReceiversChange) {
                onSelectedReceiversChange(newSelected)
            }
            return newSelected
        })
    }

    // 處理方向輸入的變化
    const handleOrientationInput = (
        deviceId: number,
        axis: 'x' | 'y' | 'z',
        value: string
    ) => {
        // 更新本地狀態
        setOrientationInputs((prev) => ({
            ...prev,
            [deviceId]: {
                ...prev[deviceId],
                [axis]: value,
            },
        }))

        // 檢查輸入是否包含分數格式
        if (value.includes('/')) {
            const parts = value.split('/')
            if (parts.length === 2) {
                const numerator = parseFloat(parts[0])
                const denominator = parseFloat(parts[1])
                if (
                    !isNaN(numerator) &&
                    !isNaN(denominator) &&
                    denominator !== 0
                ) {
                    // 計算分數值並乘以 π
                    const calculatedValue = (numerator / denominator) * Math.PI
                    // 更新設備狀態
                    const orientationKey = `orientation_${axis}` as keyof Device
                    onDeviceChange(deviceId, orientationKey, calculatedValue)
                }
            }
        } else {
            // 嘗試將值解析為數字
            const numValue = parseFloat(value)
            if (!isNaN(numValue)) {
                // 更新設備狀態
                const orientationKey = `orientation_${axis}` as keyof Device
                onDeviceChange(deviceId, orientationKey, numValue)
            }
        }
    }

    // 處理按鈕按下
    const handleManualDown = (
        direction:
            | 'up'
            | 'down'
            | 'left'
            | 'right'
            | 'ascend'
            | 'descend'
            | 'left-up'
            | 'right-up'
            | 'left-down'
            | 'right-down'
            | 'rotate-left'
            | 'rotate-right'
    ) => {
        onManualControl(direction)
        if (manualIntervalRef.current) clearInterval(manualIntervalRef.current)
        manualIntervalRef.current = setInterval(() => {
            onManualControl(direction)
        }, 60)
    }
    // 處理按鈕放開
    const handleManualUp = () => {
        if (manualIntervalRef.current) {
            clearInterval(manualIntervalRef.current)
            manualIntervalRef.current = null
        }
        onManualControl(null)
    }

    // 分組設備
    const tempDevices = devices.filter(
        (device) => device.id == null || device.id < 0
    )
    const receiverDevices = devices.filter(
        (device) =>
            device.id != null && device.id >= 0 && device.role === 'receiver'
    )
    const desiredDevices = devices.filter(
        (device) =>
            device.id != null && device.id >= 0 && device.role === 'desired'
    )
    const jammerDevices = devices.filter(
        (device) =>
            device.id != null && device.id >= 0 && device.role === 'jammer'
    )

    const renderDeviceItem = (device: Device) => (
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
                                    onChange={(e) =>
                                        onDeviceChange(
                                            device.id,
                                            'role',
                                            e.target.value
                                        )
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
                                        value={
                                            orientationInputs[device.id]?.x ||
                                            '0'
                                        }
                                        onChange={(e) =>
                                            handleOrientationInput(
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
                                        value={
                                            orientationInputs[device.id]?.y ||
                                            '0'
                                        }
                                        onChange={(e) =>
                                            handleOrientationInput(
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
                                        value={
                                            orientationInputs[device.id]?.z ||
                                            '0'
                                        }
                                        onChange={(e) =>
                                            handleOrientationInput(
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

    return (
        <div className="sidebar-container" style={{ position: 'relative' }}>
            <SidebarStarfield />
            {activeComponent !== '2DRT' && (
                <>
                    <div
                        className="sidebar-auto-row"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            marginBottom: 8,
                        }}
                    >
                        <button
                            onClick={() => onAutoChange(!auto)}
                            style={{ marginRight: 12 }}
                        >
                            {auto ? '自動飛行：開啟' : '自動飛行：關閉'}
                        </button>
                        <button
                            onClick={() => onUavAnimationChange(!uavAnimation)}
                            style={{ marginLeft: 12 }}
                        >
                            {uavAnimation ? '動畫：開啟' : '動畫：關閉'}
                        </button>
                    </div>
                    {!auto && (
                        <div
                            className="manual-control-row"
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                marginBottom: 8,
                                paddingBottom: 8,
                                borderBottom: '1px solid var(--dark-border)',
                            }}
                        >
                            {/* 第一排：↖ ↑ ↗ */}
                            <div
                                style={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    marginBottom: 4,
                                }}
                            >
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('left-up')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ↖
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('descend')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ↑
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('right-up')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ↗
                                </button>
                            </div>
                            {/* 第二排：← ⟲ ⟳ → */}
                            <div
                                style={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    marginBottom: 4,
                                }}
                            >
                                <button
                                    onMouseDown={() => handleManualDown('left')}
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ←
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('rotate-left')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ⟲
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('rotate-right')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ⟳
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('right')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    →
                                </button>
                            </div>
                            {/* 第三排：↙ ↓ ↘ */}
                            <div
                                style={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    marginBottom: 4,
                                }}
                            >
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('left-down')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ↙
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('ascend')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ↓
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('right-down')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    ↘
                                </button>
                            </div>
                            {/* 升降排 */}
                            <div
                                style={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                }}
                            >
                                <button
                                    onMouseDown={() => handleManualDown('up')}
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    升
                                </button>
                                <button
                                    onMouseDown={() => handleManualDown('down')}
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                    style={{ margin: 2 }}
                                >
                                    降
                                </button>
                            </div>
                        </div>
                    )}

                    {/* UAV 名稱徽章區塊 */}
                    <div
                        className="uav-name-badges-container"
                        style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '5px', // 徽章之間的間距
                            padding: '10px 0', // 容器的上下內邊距
                            marginTop: '10px', // 與上方元素的間距
                        }}
                    >
                        {devices
                            .filter(
                                (device) =>
                                    device.name &&
                                    device.role === 'receiver' &&
                                    device.id !== null // Ensure device has a valid ID
                            )
                            .map((device) => {
                                const isSelected = selectedReceiverIds.includes(
                                    device.id as number
                                )
                                return (
                                    <span
                                        key={device.id} // device.id is not null here
                                        className="uav-name-badge"
                                        onClick={() =>
                                            handleBadgeClick(
                                                device.id as number
                                            )
                                        }
                                        style={{
                                            backgroundColor: isSelected
                                                ? 'rgba(50, 50, 75, 0.95)' // 更新：再次調暗選中背景
                                                : 'rgba(40, 40, 70, 0.8)',
                                            color: '#e0e0e0',
                                            padding: '4px 10px',
                                            borderRadius: '12px',
                                            fontSize: '0.9em',
                                            margin: '3px',
                                            border: isSelected
                                                ? '2px solid rgba(120, 120, 160, 0.8)' // 更新：再次調暗選中邊框
                                                : '1px solid rgba(100, 100, 150, 0.5)',
                                            cursor: 'pointer', // Indicate clickable
                                            transition:
                                                'background-color 0.2s ease, border-color 0.2s ease', // Smooth transition
                                        }}
                                    >
                                        {device.name}
                                    </span>
                                )
                            })}
                    </div>
                </>
            )}
            <div className="api-status">
                API 狀態:{' '}
                {apiStatus === 'connected' ? (
                    <span className="status-connected">已連接</span>
                ) : apiStatus === 'error' ? (
                    <span className="status-error">錯誤</span>
                ) : (
                    <span className="status-disconnected">未連接</span>
                )}
            </div>

            <div
                className="sidebar-actions-combined"
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: '10px', // Preserve some top padding
                    paddingBottom: '10px', // Add some bottom padding
                    borderBottom: '1px solid var(--dark-border)', // Optional: add a separator line
                    marginBottom: '10px', // Optional: add some margin below
                }}
            >
                <button onClick={onAddDevice} className="add-device-btn">
                    添加設備
                </button>
                <div>
                    <button
                        onClick={onApply}
                        disabled={
                            loading ||
                            apiStatus !== 'connected' ||
                            !hasTempDevices ||
                            auto
                        }
                        className="add-device-btn"
                        style={{ marginRight: '8px' }} // Add some space between apply and cancel
                    >
                        套用
                    </button>
                    <button
                        onClick={onCancel}
                        disabled={loading}
                        className="add-device-btn"
                    >
                        取消
                    </button>
                </div>
            </div>

            <div className="devices-list">
                {/* 新增設備區塊 */}
                {tempDevices.length > 0 && (
                    <>
                        <h3
                            style={{
                                marginTop: '10px',
                                marginBottom: '5px',
                                paddingTop: '10px',
                                borderTop: '1px solid var(--dark-border)',
                            }}
                        >
                            新增設備
                        </h3>
                        {tempDevices.map(renderDeviceItem)}
                    </>
                )}
                {/* 接收器 (Rx) */}
                {receiverDevices.length > 0 && (
                    <>
                        <h3
                            style={{
                                marginTop:
                                    tempDevices.length > 0 ? '20px' : '10px',
                                marginBottom: '5px',
                                paddingTop: '10px',
                                borderTop:
                                    desiredDevices.length > 0 ||
                                    jammerDevices.length > 0 ||
                                    tempDevices.length > 0
                                        ? '1px solid var(--dark-border)'
                                        : 'none',
                            }}
                        >
                            接收器 (Rx)
                        </h3>
                        {receiverDevices.map(renderDeviceItem)}
                    </>
                )}
                {/* 發射器 (Tx) */}
                {desiredDevices.length > 0 && (
                    <>
                        <h3
                            style={{
                                marginTop: '20px',
                                marginBottom: '5px',
                                paddingTop: '10px',
                                borderTop: '1px solid var(--dark-border)',
                            }}
                        >
                            發射器 (Tx)
                        </h3>
                        {desiredDevices.map(renderDeviceItem)}
                    </>
                )}
                {/* 干擾源 (Jam) */}
                {jammerDevices.length > 0 && (
                    <>
                        <h3
                            style={{
                                marginTop: '20px',
                                marginBottom: '5px',
                                paddingTop: '10px',
                                borderTop: '1px solid var(--dark-border)',
                            }}
                        >
                            干擾源 (Jam)
                        </h3>
                        {jammerDevices.map(renderDeviceItem)}
                    </>
                )}
            </div>
        </div>
    )
}

export default Sidebar
