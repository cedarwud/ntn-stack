import React, { useState, useEffect, useRef } from 'react'
import '../../styles/Sidebar.scss'
import { UAVManualDirection } from '../scene/UAVFlight' // Assuming UAVFlight exports this
import { Device } from '../../types/device'
import SidebarStarfield from '../ui/SidebarStarfield' // Import the new component
import DeviceItem from '../devices/DeviceItem' // Import DeviceItem
import { useReceiverSelection } from '../../hooks/useReceiverSelection' // Import the hook
import { VisibleSatelliteInfo } from '../../types/satellite' // Import the new satellite type
import { ApiRoutes } from '../../config/apiRoutes' // 引入API路由配置
import { generateDeviceName as utilGenerateDeviceName } from '../../utils/deviceName' // 修正路徑

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
    onSatelliteDataUpdate?: (satellites: VisibleSatelliteInfo[]) => void // 衛星資料更新回調
    onSatelliteCountChange?: (count: number) => void // 衛星顯示數量變更回調
    satelliteDisplayCount?: number // 衛星顯示數量
}

// Helper function to fetch visible satellites
async function fetchVisibleSatellites(
    count: number,
    minElevation: number = 0
): Promise<VisibleSatelliteInfo[]> {
    // 使用ApiRoutes定義的路徑
    const apiUrl = `${ApiRoutes.satelliteOps.getVisibleSatellites}?count=${count}&min_elevation_deg=${minElevation}`
    try {
        const response = await fetch(apiUrl)
        if (!response.ok) {
            console.error(
                `Error fetching satellites: ${response.status} ${response.statusText}`
            )
            const errorBody = await response.text()
            console.error('Error body:', errorBody)
            return []
        }
        const data = await response.json()
        return data.satellites || [] // Assuming the API returns { satellites: [...] }
    } catch (error) {
        console.error(
            'Network error or JSON parsing error fetching satellites:',
            error
        )
        return []
    }
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
    onSatelliteDataUpdate, // 新增衛星資料更新回調
    onSatelliteCountChange, // 新增衛星顯示數量變更回調
    satelliteDisplayCount: propSatelliteDisplayCount = 10, // 使用props或默認值
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

    // 新增：控制各個設備列表的展開狀態
    const [showTempDevices, setShowTempDevices] = useState(true)
    const [showReceiverDevices, setShowReceiverDevices] = useState(false)
    const [showDesiredDevices, setShowDesiredDevices] = useState(false)
    const [showJammerDevices, setShowJammerDevices] = useState(false)

    // 新增：Skyfield 衛星資料相關狀態
    const [satelliteDisplayCount, setSatelliteDisplayCount] = useState<number>(
        propSatelliteDisplayCount
    )
    const [skyfieldSatellites, setSkyfieldSatellites] = useState<
        VisibleSatelliteInfo[]
    >([])
    const [showSkyfieldSection, setShowSkyfieldSection] =
        useState<boolean>(false)
    const [loadingSatellites, setLoadingSatellites] = useState<boolean>(false)
    const [minElevation, setMinElevation] = useState<number>(0) // 新增：最低仰角過濾

    // 新增：衛星數據自動刷新定時器
    const satelliteRefreshIntervalRef = useRef<ReturnType<
        typeof setInterval
    > | null>(null)

    // 監聽 prop 變化，同步更新本地狀態
    useEffect(() => {
        setSatelliteDisplayCount(propSatelliteDisplayCount)
    }, [propSatelliteDisplayCount])

    // Effect to fetch satellites when count changes or on mount
    useEffect(() => {
        const loadSatellites = async () => {
            setLoadingSatellites(true)
            const satellites = await fetchVisibleSatellites(
                satelliteDisplayCount,
                minElevation // 使用最低仰角過濾
            )

            // 默認按仰角從高到低排序
            let sortedSatellites = [...satellites]
            sortedSatellites.sort((a, b) => b.elevation_deg - a.elevation_deg)

            setSkyfieldSatellites(sortedSatellites)

            // 通知父元件衛星資料已更新
            if (onSatelliteDataUpdate) {
                onSatelliteDataUpdate(sortedSatellites)
            }

            setLoadingSatellites(false)
        }

        // 立即加載衛星數據
        loadSatellites()

        // 設置每分鐘刷新一次衛星數據
        if (satelliteRefreshIntervalRef.current) {
            clearInterval(satelliteRefreshIntervalRef.current)
        }

        satelliteRefreshIntervalRef.current = setInterval(() => {
            console.log('自動刷新衛星數據...')
            loadSatellites()
        }, 60000) // 每60秒刷新一次

        // 清理定時器
        return () => {
            if (satelliteRefreshIntervalRef.current) {
                clearInterval(satelliteRefreshIntervalRef.current)
                satelliteRefreshIntervalRef.current = null
            }
        }
    }, [satelliteDisplayCount, minElevation, onSatelliteDataUpdate])

    // 處理衛星顯示數量變更
    const handleSatelliteCountChange = (count: number) => {
        setSatelliteDisplayCount(count)
        if (onSatelliteCountChange) {
            onSatelliteCountChange(count)
        }
    }

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

    // 處理設備角色變更的函數
    const handleDeviceRoleChange = (deviceId: number, newRole: string) => {
        // 計算新名稱
        const newName = utilGenerateDeviceName(
            newRole,
            devices.map((d) => ({ name: d.name }))
        )

        // 更新角色
        onDeviceChange(deviceId, 'role', newRole)
        // 更新名稱
        onDeviceChange(deviceId, 'name', newName)
    }

    return (
        <div className="sidebar-container">
            <SidebarStarfield />
            {activeComponent !== '2DRT' && (
                <>
                    <div className="sidebar-auto-row">
                        <button
                            onClick={() => onAutoChange(!auto)}
                            className="button-auto-toggle"
                        >
                            {auto ? '自動飛行：開啟' : '自動飛行：關閉'}
                        </button>
                        <button
                            onClick={() => onUavAnimationChange(!uavAnimation)}
                            className="button-animation-toggle"
                        >
                            {uavAnimation ? '動畫：開啟' : '動畫：關閉'}
                        </button>
                    </div>
                    {!auto && (
                        <div className="manual-control-row">
                            {/* 第一排：↖ ↑ ↗ */}
                            <div className="manual-button-group with-margin-bottom">
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('left-up')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ↖
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('descend')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ↑
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('right-up')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ↗
                                </button>
                            </div>
                            {/* 第二排：← ⟲ ⟳ → */}
                            <div className="manual-button-group with-margin-bottom">
                                <button
                                    onMouseDown={() => handleManualDown('left')}
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ←
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('rotate-left')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ⟲
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('rotate-right')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ⟳
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('right')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    →
                                </button>
                            </div>
                            {/* 第三排：↙ ↓ ↘ */}
                            <div className="manual-button-group with-margin-bottom">
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('left-down')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ↙
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('ascend')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ↓
                                </button>
                                <button
                                    onMouseDown={() =>
                                        handleManualDown('right-down')
                                    }
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    ↘
                                </button>
                            </div>
                            {/* 升降排 */}
                            <div className="manual-button-group">
                                <button
                                    onMouseDown={() => handleManualDown('up')}
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    升
                                </button>
                                <button
                                    onMouseDown={() => handleManualDown('down')}
                                    onMouseUp={handleManualUp}
                                    onMouseLeave={handleManualUp}
                                >
                                    降
                                </button>
                            </div>
                        </div>
                    )}

                    {/* UAV 名稱徽章區塊 */}
                    <div className="uav-name-badges-container">
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
                                        className={`uav-name-badge ${
                                            isSelected ? 'selected' : ''
                                        }`}
                                        onClick={() =>
                                            handleBadgeClick(
                                                device.id as number
                                            )
                                        }
                                    >
                                        {device.name}
                                    </span>
                                )
                            })}
                    </div>
                </>
            )}

            {/* 衛星設置區域 - 獨立於API狀態 */}
            <div className="satellite-settings-section">
                <div className="satellite-count-control">
                    <div>
                        <label htmlFor="satellite-count-input">衛星數:</label>
                        <input
                            id="satellite-count-input"
                            type="number"
                            value={satelliteDisplayCount}
                            onChange={(e) => {
                                const count = parseInt(e.target.value, 10)
                                if (!isNaN(count) && count > 0) {
                                    handleSatelliteCountChange(count)
                                } else if (e.target.value === '') {
                                    // Allow clearing to type new number
                                    handleSatelliteCountChange(1) // Or some default minimum
                                }
                            }}
                            min="1"
                            className="satellite-count-input-field"
                        />
                    </div>
                    <div>
                        {/* 保留最低仰角控制 */}
                        <label
                            htmlFor="min-elevation-input"
                            style={{ marginLeft: '10px' }}
                        >
                            最低仰角:
                        </label>
                        <input
                            id="min-elevation-input"
                            type="number"
                            value={minElevation}
                            onChange={(e) => {
                                const value = parseInt(e.target.value, 10)
                                if (
                                    !isNaN(value) &&
                                    value >= 0 &&
                                    value <= 90
                                ) {
                                    setMinElevation(value)
                                } else if (e.target.value === '') {
                                    setMinElevation(0)
                                }
                            }}
                            min="0"
                            max="90"
                            className="satellite-count-input-field"
                        />
                    </div>
                </div>
            </div>

            <div className="sidebar-actions-combined">
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
                        className="add-device-btn button-apply-action"
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
                            className={`section-title collapsible-header ${
                                showTempDevices ? 'expanded' : ''
                            }`}
                            onClick={() => setShowTempDevices(!showTempDevices)}
                        >
                            新增設備
                        </h3>
                        {showTempDevices &&
                            tempDevices.map((device) => (
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
                                    onDeviceRoleChange={handleDeviceRoleChange}
                                />
                            ))}
                    </>
                )}

                {/* Skyfield 衛星資料區塊 */}
                <>
                    <h3
                        className={`section-title collapsible-header ${
                            showSkyfieldSection ? 'expanded' : ''
                        } ${tempDevices.length > 0 ? 'extra-margin-top' : ''} ${
                            tempDevices.length > 0 ? 'with-border-top' : ''
                        }`}
                        onClick={() =>
                            setShowSkyfieldSection(!showSkyfieldSection)
                        }
                    >
                        衛星 gNB (
                        {loadingSatellites
                            ? '讀取中...'
                            : skyfieldSatellites.length}
                        ){' '}
                        {minElevation > 0 ? `[最低仰角: ${minElevation}°]` : ''}
                    </h3>
                    {showSkyfieldSection && (
                        <div className="satellite-list">
                            {loadingSatellites ? (
                                <p className="loading-text">
                                    正在載入衛星資料...
                                </p>
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
                                                        sat.elevation_deg > 45
                                                            ? '#ff3300'
                                                            : '#0088ff',
                                                }}
                                            >
                                                {sat.elevation_deg.toFixed(2)}°
                                            </span>{' '}
                                            | 方位角:{' '}
                                            {sat.azimuth_deg.toFixed(2)}° |
                                            距離: {sat.distance_km.toFixed(2)}{' '}
                                            km
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="no-data-text">
                                    無衛星資料可顯示。請調整最低仰角後重試。
                                </p>
                            )}
                        </div>
                    )}
                </>

                {/* 接收器 (Rx) */}
                {receiverDevices.length > 0 && (
                    <>
                        <h3
                            className={`section-title collapsible-header ${
                                showReceiverDevices ? 'expanded' : ''
                            } ${
                                tempDevices.length > 0 ||
                                skyfieldSatellites.length > 0
                                    ? 'extra-margin-top'
                                    : '' // Adjusted condition
                            } ${
                                tempDevices.length > 0 ||
                                skyfieldSatellites.length > 0 || // Adjusted condition
                                desiredDevices.length > 0 ||
                                jammerDevices.length > 0
                                    ? 'with-border-top'
                                    : ''
                            }`}
                            onClick={() =>
                                setShowReceiverDevices(!showReceiverDevices)
                            }
                        >
                            接收器 Rx ({receiverDevices.length})
                        </h3>
                        {showReceiverDevices &&
                            receiverDevices.map((device) => (
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
                                    onDeviceRoleChange={handleDeviceRoleChange}
                                />
                            ))}
                    </>
                )}
                {/* 發射器 (Tx) */}
                {desiredDevices.length > 0 && (
                    <>
                        <h3
                            className={`section-title extra-margin-top collapsible-header ${
                                showDesiredDevices ? 'expanded' : ''
                            }`}
                            onClick={() =>
                                setShowDesiredDevices(!showDesiredDevices)
                            }
                        >
                            發射器 Tx ({desiredDevices.length})
                        </h3>
                        {showDesiredDevices &&
                            desiredDevices.map((device) => (
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
                                    onDeviceRoleChange={handleDeviceRoleChange}
                                />
                            ))}
                    </>
                )}
                {/* 干擾源 (Jam) */}
                {jammerDevices.length > 0 && (
                    <>
                        <h3
                            className={`section-title extra-margin-top collapsible-header ${
                                showJammerDevices ? 'expanded' : ''
                            }`}
                            onClick={() =>
                                setShowJammerDevices(!showJammerDevices)
                            }
                        >
                            干擾源 Jam ({jammerDevices.length})
                        </h3>
                        {showJammerDevices &&
                            jammerDevices.map((device) => (
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
                                    onDeviceRoleChange={handleDeviceRoleChange}
                                />
                            ))}
                    </>
                )}
            </div>
        </div>
    )
}

// 添加新的CSS樣式
const styleSheet = document.createElement('style')
styleSheet.type = 'text/css'
styleSheet.innerHTML = `
.api-status-section {
    padding: 8px;
    margin-bottom: 10px;
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
    text-align: center;
}

.satellite-settings-section {
    padding: 8px;
    margin-bottom: 10px;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
}
`
document.head.appendChild(styleSheet)

export default Sidebar
