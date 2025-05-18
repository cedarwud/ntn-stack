import React, { useState, useEffect, useRef } from 'react'
import '../styles/Sidebar.css'
import { UAVManualDirection } from './UAVFlight' // Assuming UAVFlight exports this
import { Device } from '../types/device'
import SidebarStarfield from './SidebarStarfield' // Import the new component
import DeviceItem from './DeviceItem' // Import DeviceItem
import { useReceiverSelection } from '../hooks/useReceiverSelection' // Import the hook

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

    // Use the new hook for receiver selection
    const { selectedReceiverIds, handleBadgeClick } = useReceiverSelection({
        devices,
        onSelectedReceiversChange,
    })

    // 當 devices 更新時，初始化或更新本地輸入狀態
    useEffect(() => {
        const newInputs: {
            [key: string]: { x: string; y: string; z: string }
        } = {}
        devices.forEach((device) => {
            // 檢查 orientationInputs[device.id] 是否存在，如果不存在或其值與 device object 中的值不同，則進行初始化
            const existingInput = orientationInputs[device.id]
            const backendX = device.orientation_x?.toString() || '0'
            const backendY = device.orientation_y?.toString() || '0'
            const backendZ = device.orientation_z?.toString() || '0'

            if (existingInput) {
                // 如果存在本地狀態，比較後決定是否使用後端值來覆蓋（例如，如果外部更改了設備數據）
                // 這裡的邏輯是，如果本地輸入與後端解析後的數值不直接對應（例如本地是 "1/2", 後端是 1.57...），
                // 且後端的值不是初始的 '0'，則可能意味著後端的值已被更新，我們可能需要一種策略來決定是否刷新本地輸入框。
                // 目前的策略是：如果 device object 中的 orientation 值不再是 0 (或 undefined)，
                // 且 orientationInputs 中對應的值是 '0'，則用 device object 的值更新 input。
                // 這有助於在外部修改了方向後，輸入框能反映這些更改，除非用戶已經開始編輯。
                // 更複雜的同步邏輯可能需要考慮編輯狀態。
                // 為了簡化，如果本地已有值，我們傾向於保留本地輸入，除非是從 '0' 開始。
                newInputs[device.id] = {
                    x:
                        existingInput.x !== '0' && existingInput.x !== backendX
                            ? existingInput.x
                            : backendX,
                    y:
                        existingInput.y !== '0' && existingInput.y !== backendY
                            ? existingInput.y
                            : backendY,
                    z:
                        existingInput.z !== '0' && existingInput.z !== backendZ
                            ? existingInput.z
                            : backendZ,
                }
            } else {
                newInputs[device.id] = {
                    x: backendX,
                    y: backendY,
                    z: backendZ,
                }
            }
        })
        setOrientationInputs(newInputs)
    }, [devices]) // 依賴 devices prop

    // 處理方向輸入的變化 (重命名並調整)
    const handleDeviceOrientationInputChange = (
        deviceId: number,
        axis: 'x' | 'y' | 'z',
        value: string
    ) => {
        // 更新本地狀態以反映輸入框中的原始文本
        setOrientationInputs((prev) => ({
            ...prev,
            [deviceId]: {
                ...prev[deviceId],
                [axis]: value,
            },
        }))

        // 解析輸入值並更新實際的設備數據
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
                    const calculatedValue = (numerator / denominator) * Math.PI
                    const orientationKey = `orientation_${axis}` as keyof Device
                    onDeviceChange(deviceId, orientationKey, calculatedValue)
                }
            }
        } else {
            const numValue = parseFloat(value)
            if (!isNaN(numValue)) {
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
                        {tempDevices.map((device) => (
                            <DeviceItem
                                key={device.id}
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
                                    handleDeviceOrientationInputChange
                                }
                            />
                        ))}
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
                        {receiverDevices.map((device) => (
                            <DeviceItem
                                key={device.id}
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
                                    handleDeviceOrientationInputChange
                                }
                            />
                        ))}
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
                        {desiredDevices.map((device) => (
                            <DeviceItem
                                key={device.id}
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
                                    handleDeviceOrientationInputChange
                                }
                            />
                        ))}
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
                        {jammerDevices.map((device) => (
                            <DeviceItem
                                key={device.id}
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
                                    handleDeviceOrientationInputChange
                                }
                            />
                        ))}
                    </>
                )}
            </div>
        </div>
    )
}

export default Sidebar
