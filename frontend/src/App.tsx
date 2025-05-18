// src/App.tsx
import { useState, useEffect } from 'react'
import SceneView from './components/StereogramView'
import Layout from './components/Layout'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import SceneViewer from './components/FloorView'
import './App.css'
import { Device } from './types/device'
import { countActiveDevices } from './utils/deviceUtils'
import { useDevices } from './hooks/useDevices'

function App() {
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

    const [activeComponent, setActiveComponent] = useState<string>('3DRT')
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
    const [uavAnimation, setUavAnimation] = useState(true)
    const [selectedReceiverIds, setSelectedReceiverIds] = useState<number[]>([])

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

    const handleSelectedReceiversChange = (ids: number[]) => {
        console.log('選中的 receiver IDs:', ids)
        setSelectedReceiverIds(ids)
    }

    const handleManualControl = (
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
    }

    const handleUAVPositionUpdate = (
        pos: [number, number, number],
        deviceId?: number
    ) => {
        if (deviceId === undefined || !selectedReceiverIds.includes(deviceId)) {
            return
        }
        updateDevicePositionFromUAV(deviceId, pos)
    }

    const renderActiveComponent = () => {
        switch (activeComponent) {
            case '2DRT':
                return (
                    <SceneViewer
                        devices={tempDevices}
                        refreshDeviceData={refreshDeviceData}
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
                    />
                )
            default:
                return (
                    <SceneViewer
                        devices={tempDevices}
                        refreshDeviceData={refreshDeviceData}
                    />
                )
        }
    }

    if (loading) {
        return <div className="loading">載入中...</div>
    }

    return (
        <div className="app-container">
            <Navbar
                onMenuClick={handleMenuClick}
                activeComponent={activeComponent}
            />
            <div className="content-wrapper">
                <Layout
                    sidebar={
                        <Sidebar
                            devices={[...tempDevices].sort((a, b) => {
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
                            })}
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
                        />
                    }
                    content={renderActiveComponent()}
                    activeComponent={activeComponent}
                />
            </div>
        </div>
    )
}

export default App
