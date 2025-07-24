import { useState, useEffect, useRef } from 'react'
import '../../styles/Sidebar.scss'
import { UAVManualDirection } from '../domains/device/visualization/UAVFlight' // Assuming UAVFlight exports this
import { Device } from '../../types/device'
import SidebarStarfield from '../ui/SidebarStarfield' // Import the new component
import DeviceItem from '../devices/DeviceItem' // Import DeviceItem
import { useReceiverSelection } from '../../hooks/useReceiverSelection' // Import the hook
import { VisibleSatelliteInfo } from '../../types/satellite' // Import the new satellite type
import { ApiRoutes } from '../../config/apiRoutes' // 引入API路由配置
import { SATELLITE_CONFIG } from '../../config/satellite.config' // 引入衛星配置
import { generateDeviceName as utilGenerateDeviceName } from '../../utils/deviceName' // 修正路徑

interface SidebarProps {
    devices: Device[]
    loading: boolean
    apiStatus: 'disconnected' | 'connected' | 'error'
    onDeviceChange: (id: number, field: keyof Device, value: unknown) => void
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
    satelliteEnabled?: boolean // 衛星開關狀態
    onSatelliteEnabledChange?: (enabled: boolean) => void // 衛星開關回調
}

// Helper function to fetch visible satellites from multiple constellations
async function fetchVisibleSatellites(): Promise<VisibleSatelliteInfo[]> {
    const allSatellites: VisibleSatelliteInfo[] = []
    
    // 支援的星座列表（根據後端數據庫實際擁有的星座）
    const constellations = ['starlink', 'oneweb', 'kuiper'] // 資料庫中有 Starlink (15628顆)、OneWeb (20顆) 和 Kuiper (54顆) 數據
    
    // 台灣觀測者位置：24°56'39"N 121°22'17"E (根據 CLAUDE.md 要求使用真實地理位置)
    const TAIWAN_OBSERVER = {
        lat: 24.94417,    // 24°56'39"N = 24 + 56/60 + 39/3600
        lon: 121.37139,   // 121°22'17"E = 121 + 22/60 + 17/3600
        alt: 100          // 台灣平均海拔約100公尺
    }
    
    try {
        // 並行獲取多個星座的衛星數據
        const fetchPromises = constellations.map(async (constellation) => {
            const apiUrl = `${ApiRoutes.satelliteOps.getVisibleSatellites}?count=${Math.floor(SATELLITE_CONFIG.VISIBLE_COUNT / constellations.length)}&min_elevation_deg=${SATELLITE_CONFIG.MIN_ELEVATION}&constellation=${constellation}&observer_lat=${TAIWAN_OBSERVER.lat}&observer_lon=${TAIWAN_OBSERVER.lon}&observer_alt=${TAIWAN_OBSERVER.alt}&global_view=false`
            
            try {
                const response = await fetch(apiUrl)
                if (!response.ok) {
                    console.warn(
                        `Warning fetching ${constellation} satellites: ${response.status} ${response.statusText}`
                    )
                    return []
                }
                const data = await response.json()
                const satellites = data.satellites || []
                
                // 標記衛星所屬星座
                satellites.forEach((sat: VisibleSatelliteInfo) => {
                    sat.constellation = constellation.toUpperCase()
                })
                
                console.log(`🛰️ 獲取到 ${satellites.length} 顆 ${constellation.toUpperCase()} 衛星`)
                return satellites
            } catch (error) {
                console.warn(`Error fetching ${constellation} satellites:`, error)
                return []
            }
        })
        
        // 等待所有星座數據獲取完成
        const constellationResults = await Promise.all(fetchPromises)
        
        // 合併所有星座的衛星數據
        constellationResults.forEach(satellites => {
            allSatellites.push(...satellites)
        })
        
        console.log(`🌍 總共獲取到 ${allSatellites.length} 顆可見衛星`)
        return allSatellites
        
    } catch (error) {
        console.error('Network error fetching satellites:', error)
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
    satelliteEnabled, // 衛星開關狀態
    onSatelliteEnabledChange, // 衛星開關回調
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
    const [skyfieldSatellites, setSkyfieldSatellites] = useState<
        VisibleSatelliteInfo[]
    >([])
    const [showSkyfieldSection, setShowSkyfieldSection] =
        useState<boolean>(false)
    const [loadingSatellites, setLoadingSatellites] = useState<boolean>(false)

    // 新增：衛星數據自動刷新定時器
    const satelliteRefreshIntervalRef = useRef<ReturnType<
        typeof setInterval
    > | null>(null)

    // Effect to fetch satellites when count changes or on mount
    useEffect(() => {
        const loadSatellites = async () => {
            if (!satelliteEnabled) {
                // 如果衛星開關關閉，清空數據並返回
                setSkyfieldSatellites([])
                if (onSatelliteDataUpdate) {
                    onSatelliteDataUpdate([])
                }
                setLoadingSatellites(false)
                return
            }

            setLoadingSatellites(true)
            const satellites = await fetchVisibleSatellites()

            // 默認按仰角從高到低排序
            const sortedSatellites = [...satellites]
            sortedSatellites.sort((a, b) => b.elevation_deg - a.elevation_deg)

            setSkyfieldSatellites(sortedSatellites)

            // 通知父元件衛星資料已更新
            if (onSatelliteDataUpdate) {
                onSatelliteDataUpdate(sortedSatellites)
            }

            setLoadingSatellites(false)
        }

        // 清理現有定時器
        if (satelliteRefreshIntervalRef.current) {
            clearInterval(satelliteRefreshIntervalRef.current)
            satelliteRefreshIntervalRef.current = null
        }

        if (satelliteEnabled) {
            // 立即加載衛星數據
            loadSatellites()

            // 設置每分鐘刷新一次衛星數據
            satelliteRefreshIntervalRef.current = setInterval(() => {
                console.log('自動刷新衛星數據...')
                loadSatellites()
            }, 60000) // 每60秒刷新一次
        } else {
            // 如果衛星開關關閉，清空數據
            loadSatellites()
        }

        // 清理定時器
        return () => {
            if (satelliteRefreshIntervalRef.current) {
                clearInterval(satelliteRefreshIntervalRef.current)
                satelliteRefreshIntervalRef.current = null
            }
        }
    }, [onSatelliteDataUpdate, satelliteEnabled])

    // 移除衛星顯示數量變更處理函數

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
    }, [devices, orientationInputs])

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
                        <div
                            onClick={() => onAutoChange(!auto)}
                            className={`toggle-badge ${auto ? 'active' : ''}`}
                        >
                            自動飛行
                        </div>
                        <div
                            onClick={() => onUavAnimationChange(!uavAnimation)}
                            className={`toggle-badge ${
                                uavAnimation ? 'active' : ''
                            }`}
                        >
                            動畫
                        </div>
                        <div
                            onClick={() =>
                                onSatelliteEnabledChange &&
                                onSatelliteEnabledChange(!satelliteEnabled)
                            }
                            className={`toggle-badge ${
                                satelliteEnabled ? 'active' : ''
                            }`}
                        >
                            衛星
                        </div>
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
                {satelliteEnabled && (
                    <>
                        <h3
                            className={`section-title collapsible-header ${
                                showSkyfieldSection ? 'expanded' : ''
                            } ${
                                tempDevices.length > 0 ? 'extra-margin-top' : ''
                            } ${
                                tempDevices.length > 0 ? 'with-border-top' : ''
                            }`}
                            onClick={() =>
                                setShowSkyfieldSection(!showSkyfieldSection)
                            }
                        >
                            衛星 gNB ({loadingSatellites ? '讀取中...' : skyfieldSatellites.length})
                            {!loadingSatellites && skyfieldSatellites.length > 0 && (
                                <div style={{ fontSize: '0.7em', color: '#888', marginTop: '2px' }}>
                                    {(() => {
                                        const constellationCounts = skyfieldSatellites.reduce((acc, sat) => {
                                            const constellation = sat.constellation || 'UNKNOWN'
                                            acc[constellation] = (acc[constellation] || 0) + 1
                                            return acc
                                        }, {} as Record<string, number>)
                                        
                                        return Object.entries(constellationCounts)
                                            .map(([constellation, count]) => `${constellation}: ${count}`)
                                            .join(' | ')
                                    })()}
                                </div>
                            )}
                            {SATELLITE_CONFIG.MIN_ELEVATION > 0 && (
                                <div style={{ fontSize: '0.7em', color: '#666', marginTop: '2px' }}>
                                    最低仰角: {SATELLITE_CONFIG.MIN_ELEVATION}°
                                </div>
                            )}
                        </h3>
                        {showSkyfieldSection && (
                            <div className="satellite-list">
                                {loadingSatellites ? (
                                    <p className="loading-text">
                                        正在載入衛星資料...
                                    </p>
                                ) : skyfieldSatellites.length > 0 ? (
                                    skyfieldSatellites.map((sat) => {
                                        // 根據星座決定顏色
                                        const getConstellationColor = (constellation?: string) => {
                                            switch (constellation?.toUpperCase()) {
                                                case 'STARLINK': return '#ff6b35' // 橙色
                                                case 'ONEWEB': return '#4dabf7' // 藍色
                                                case 'KUIPER': return '#51cf66' // 綠色
                                                default: return '#868e96' // 灰色
                                            }
                                        }
                                        
                                        const constellationColor = getConstellationColor(sat.constellation)
                                        
                                        return (
                                            <div
                                                key={sat.norad_id}
                                                className="satellite-item"
                                                style={{ 
                                                    borderLeft: `3px solid ${constellationColor}`,
                                                    paddingLeft: '8px'
                                                }}
                                            >
                                                <div className="satellite-name">
                                                    <span 
                                                        style={{ 
                                                            color: constellationColor,
                                                            fontWeight: 'bold',
                                                            fontSize: '0.8em'
                                                        }}
                                                    >
                                                        [{sat.constellation || 'UNKNOWN'}]
                                                    </span>{' '}
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
                                                    | 方位角: {sat.azimuth_deg.toFixed(2)}° |
                                                    距離: {sat.distance_km.toFixed(2)} km
                                                </div>
                                            </div>
                                        )
                                    })
                                ) : (
                                    <p className="no-data-text">
                                        無衛星資料可顯示。請調整最低仰角後重試。
                                    </p>
                                )}
                            </div>
                        )}
                    </>
                )}

                {/* 接收器 (Rx) */}
                {receiverDevices.length > 0 && (
                    <>
                        <h3
                            className={`section-title collapsible-header ${
                                showReceiverDevices ? 'expanded' : ''
                            } ${
                                tempDevices.length > 0 ||
                                (satelliteEnabled &&
                                    skyfieldSatellites.length > 0)
                                    ? 'extra-margin-top'
                                    : ''
                            } ${
                                tempDevices.length > 0 ||
                                (satelliteEnabled &&
                                    skyfieldSatellites.length > 0) ||
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

export default Sidebar
