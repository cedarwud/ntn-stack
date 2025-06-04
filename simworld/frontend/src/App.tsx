// src/App.tsx
import { useState, useCallback, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import SceneView from './components/scenes/StereogramView'
import Layout from './components/layout/Layout'
import Sidebar from './components/layout/Sidebar'
import Navbar from './components/layout/Navbar'
import SceneViewer from './components/scenes/FloorView'
import ErrorBoundary from './components/ui/ErrorBoundary'
import './styles/App.scss'
import { Device } from './types/device'
import { countActiveDevices } from './utils/deviceUtils'
import { useDevices } from './hooks/useDevices'
import { VisibleSatelliteInfo } from './types/satellite'
import './styles/Dashboard.scss'

interface AppProps {
    activeView: 'stereogram' | 'floor-plan'
}

function App({ activeView }: AppProps) {
    const { scenes } = useParams<{ scenes: string }>()

    // 確保有預設場景
    const currentScene = scenes || 'nycu'

    // 根據 activeView 設定初始組件
    const initialComponent = activeView === 'stereogram' ? '3DRT' : '2DRT'

    const {
        tempDevices,
        loading,
        apiStatus,
        hasTempDevices,
        fetchDevices: refreshDeviceData,
        setTempDevices,
        setHasTempDevices,
        applyDeviceChanges,
        deleteDeviceById,
        addNewDevice,
        updateDeviceField,
        cancelDeviceChanges,
        updateDevicePositionFromUAV,
    } = useDevices()

    const [skyfieldSatellites, setSkyfieldSatellites] = useState<
        VisibleSatelliteInfo[]
    >([])
    const [satelliteDisplayCount, setSatelliteDisplayCount] =
        useState<number>(10)
    const [satelliteEnabled, setSatelliteEnabled] = useState<boolean>(false)

    const [activeComponent, setActiveComponent] =
        useState<string>(initialComponent)
    const [auto, setAuto] = useState(false)
    const [manualDirection, setManualDirection] = useState<
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
        | null
    >(null)
    const [uavAnimation, setUavAnimation] = useState(false)
    const [selectedReceiverIds, setSelectedReceiverIds] = useState<number[]>([])

    const sortedDevicesForSidebar = useMemo(() => {
        return [...tempDevices].sort((a, b) => {
            const roleOrder: { [key: string]: number } = {
                receiver: 1,
                desired: 2,
                jammer: 3,
            }
            const roleA = roleOrder[a.role] || 99
            const roleB = roleOrder[b.role] || 99

            if (roleA !== roleB) {
                return roleA - roleB
            }

            return a.name.localeCompare(b.name)
        })
    }, [tempDevices])

    const handleApply = async () => {
        const { activeTx: currentActiveTx, activeRx: currentActiveRx } =
            countActiveDevices(tempDevices)

        if (currentActiveTx < 1 || currentActiveRx < 1) {
            alert(
                '套用失敗：操作後必須至少保留一個啟用的發射器 (desired) 和一個啟用的接收器 (receiver)。請檢查設備的啟用狀態。'
            )
            return
        }

        await applyDeviceChanges()
    }

    const handleCancel = () => {
        cancelDeviceChanges()
    }

    const handleDeleteDevice = async (id: number) => {
        if (id < 0) {
            setTempDevices((prev) => prev.filter((device) => device.id !== id))
            setHasTempDevices(true)
            console.log(`已從前端移除臨時設備 ID: ${id}`)
            return
        }

        const devicesAfterDelete = tempDevices.filter(
            (device) => device.id !== id
        )
        const { activeTx: futureActiveTx, activeRx: futureActiveRx } =
            countActiveDevices(devicesAfterDelete)

        if (futureActiveTx < 1 || futureActiveRx < 1) {
            alert(
                '刪除失敗：操作後必須至少保留一個啟用的發射器 (desired) 和一個啟用的接收器 (receiver)。'
            )
            return
        }

        if (!window.confirm('確定要刪除這個設備嗎？此操作將立即生效。')) {
            return
        }

        await deleteDeviceById(id)
    }

    const handleAddDevice = () => {
        addNewDevice()
    }

    const handleDeviceChange = (
        id: number,
        field: string | number | symbol,
        value: any
    ) => {
        updateDeviceField(id, field as keyof Device, value)
    }

    const handleMenuClick = (component: string) => {
        setActiveComponent(component)
    }

    const handleSelectedReceiversChange = useCallback((ids: number[]) => {
        // console.log('選中的 receiver IDs:', ids) // 註解掉飛行時的 log
        setSelectedReceiverIds(ids)
    }, [])

    const handleSatelliteDataUpdate = useCallback(
        (satellites: VisibleSatelliteInfo[]) => {
            setSkyfieldSatellites(satellites)
        },
        []
    )

    const handleSatelliteCountChange = useCallback((count: number) => {
        setSatelliteDisplayCount(count)
    }, [])

    const handleManualControl = useCallback(
        (
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
                | null
        ) => {
            if (selectedReceiverIds.length === 0) {
                console.log('沒有選中的 receiver，無法控制 UAV')
                return
            }

            setManualDirection(direction)
        },
        [selectedReceiverIds, setManualDirection]
    )

    const handleUAVPositionUpdate = useCallback(
        (pos: [number, number, number], deviceId?: number) => {
            if (
                deviceId === undefined ||
                !selectedReceiverIds.includes(deviceId)
            ) {
                return
            }
            updateDevicePositionFromUAV(deviceId, pos)
        },
        [selectedReceiverIds, updateDevicePositionFromUAV]
    )

    const renderActiveComponent = useCallback(() => {
        switch (activeComponent) {
            case '2DRT':
                return (
                    <SceneViewer
                        devices={tempDevices}
                        refreshDeviceData={refreshDeviceData}
                        sceneName={currentScene}
                    />
                )
            case '3DRT':
                return (
                    <SceneView
                        devices={tempDevices}
                        auto={auto}
                        manualDirection={manualDirection}
                        onManualControl={handleManualControl}
                        onUAVPositionUpdate={handleUAVPositionUpdate}
                        uavAnimation={uavAnimation}
                        selectedReceiverIds={selectedReceiverIds}
                        satellites={satelliteEnabled ? skyfieldSatellites : []}
                        sceneName={currentScene}
                    />
                )
            default:
                return (
                    <SceneViewer
                        devices={tempDevices}
                        refreshDeviceData={refreshDeviceData}
                        sceneName={currentScene}
                    />
                )
        }
    }, [
        activeComponent,
        tempDevices,
        auto,
        manualDirection,
        handleManualControl,
        handleUAVPositionUpdate,
        uavAnimation,
        selectedReceiverIds,
        refreshDeviceData,
        skyfieldSatellites,
        satelliteEnabled,
        currentScene,
    ])

    if (loading) {
        return <div className="loading">載入中...</div>
    }

    return (
        <ErrorBoundary>
            <div className="app-container">
                <Navbar
                    onMenuClick={handleMenuClick}
                    activeComponent={activeComponent}
                    currentScene={currentScene}
                />
                <div className="content-wrapper">
                    <Layout
                        sidebar={
                            <ErrorBoundary fallback={<div>側邊欄發生錯誤</div>}>
                                <Sidebar
                                    devices={sortedDevicesForSidebar}
                                    onDeviceChange={handleDeviceChange}
                                    onDeleteDevice={handleDeleteDevice}
                                    onAddDevice={handleAddDevice}
                                    onApply={handleApply}
                                    onCancel={handleCancel}
                                    loading={loading}
                                    apiStatus={apiStatus}
                                    hasTempDevices={hasTempDevices}
                                    auto={auto}
                                    onAutoChange={setAuto}
                                    onManualControl={handleManualControl}
                                    activeComponent={activeComponent}
                                    uavAnimation={uavAnimation}
                                    onUavAnimationChange={setUavAnimation}
                                    onSelectedReceiversChange={
                                        handleSelectedReceiversChange
                                    }
                                    onSatelliteDataUpdate={
                                        handleSatelliteDataUpdate
                                    }
                                    onSatelliteCountChange={
                                        handleSatelliteCountChange
                                    }
                                    satelliteDisplayCount={
                                        satelliteDisplayCount
                                    }
                                    satelliteEnabled={satelliteEnabled}
                                    onSatelliteEnabledChange={
                                        setSatelliteEnabled
                                    }
                                />
                            </ErrorBoundary>
                        }
                        content={
                            <ErrorBoundary fallback={<div>主視圖發生錯誤</div>}>
                                {renderActiveComponent()}
                            </ErrorBoundary>
                        }
                        activeComponent={activeComponent}
                    />
                </div>
            </div>
        </ErrorBoundary>
    )
}

export default App
