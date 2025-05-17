// src/App.tsx
import { useState, useEffect, useCallback } from 'react'
import SceneView from './components/StereogramView'
import Layout from './components/Layout'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import SceneViewer from './components/FloorView'
import './App.css'
import {
    Device as BackendDevice,
    getDevices,
    createDevice,
    updateDevice,
    deleteDevice,
} from './services/api'

// 前端設備介面 - 與後端保持一致
export interface Device {
    id: number
    name: string
    position_x: number
    position_y: number
    position_z: number
    orientation_x?: number
    orientation_y?: number
    orientation_z?: number
    power_dbm?: number
    active: boolean
    role: string // 使用角色字段
}

// 轉換後端設備到前端設備格式 - 不再需要轉換，因為結構一致
const convertBackendToFrontend = (backendDevice: BackendDevice): Device => {
    return {
        id: backendDevice.id,
        name: backendDevice.name,
        position_x: backendDevice.position_x,
        position_y: backendDevice.position_y,
        position_z: backendDevice.position_z,
        orientation_x: backendDevice.orientation_x,
        orientation_y: backendDevice.orientation_y,
        orientation_z: backendDevice.orientation_z,
        power_dbm: backendDevice.power_dbm,
        active: backendDevice.active,
        role: backendDevice.role, // 保持與後端一致使用 role
    }
}

// 輔助函數：計算啟用設備的數量
const countActiveDevices = (
    deviceList: Device[]
): { activeTx: number; activeRx: number } => {
    let activeTx = 0
    let activeRx = 0
    deviceList.forEach((d) => {
        if (d.active) {
            if (d.role === 'desired') {
                activeTx++
            } else if (d.role === 'receiver') {
                activeRx++
            }
        }
    })
    return { activeTx, activeRx }
}

function App() {
    const [tempDevices, setTempDevices] = useState<Device[]>([])
    const [originalDevices, setOriginalDevices] = useState<Device[]>([])
    const [loading, setLoading] = useState<boolean>(true)
    const [error, setError] = useState<string | null>(null)
    const [apiStatus, setApiStatus] = useState<
        'disconnected' | 'connected' | 'error'
    >('disconnected')
    const [hasTempDevices, setHasTempDevices] = useState<boolean>(false)
    const [activeComponent, setActiveComponent] = useState<string>('2DRT')
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
    const [uavPosition, setUavPosition] = useState<
        [number, number, number] | null
    >(null)
    const [uavAnimation, setUavAnimation] = useState(true)

    // 新增：追蹤選中的 receiver IDs
    const [selectedReceiverIds, setSelectedReceiverIds] = useState<number[]>([])

    // 新增狀態來記錄每個 UAV 的初始位置偏移
    const [uavOffsets, setUavOffsets] = useState<{
        [key: number]: { x: number; y: number; z: number }
    }>({})

    // 記錄是否已經初始化了偏移量
    const [offsetsInitialized, setOffsetsInitialized] = useState(false)

    // 從API獲取設備數據
    const fetchDevices = useCallback(async () => {
        try {
            setLoading(true)
            setApiStatus('disconnected')
            console.log('嘗試從API獲取設備數據...')
            const backendDevices = await getDevices()
            console.log('成功獲取設備數據:', backendDevices)

            const frontendDevices = backendDevices.map(convertBackendToFrontend)

            setTempDevices(frontendDevices)
            setOriginalDevices(frontendDevices)
            setError(null)
            setApiStatus('connected')

            // 預設全選所有 receiver 設備
            const receiverIds = frontendDevices
                .filter(
                    (device) => device.role === 'receiver' && device.id !== null
                )
                .map((device) => device.id as number)
            setSelectedReceiverIds(receiverIds)
        } catch (err: any) {
            console.error('獲取設備失敗:', err)
            const errorMessage = err.message || '未知錯誤'
            setError(`獲取設備數據時發生錯誤: ${errorMessage}`)
            setApiStatus('error')

            // 如果API連接失敗，使用一些默認設備數據進行開發測試
            const defaultDevices: Device[] = Array.from(
                { length: 3 },
                (_, i) => ({
                    id: -(i + 1), // 負數ID表示臨時數據
                    name: `測試設備 ${i + 1}`,
                    position_x: i * 10,
                    position_y: i * 10,
                    position_z: 0,
                    orientation_x: 0,
                    orientation_y: 0,
                    orientation_z: 0,
                    power_dbm: 0,
                    active: true,
                    role: ['desired', 'receiver', 'jammer'][i % 3] as string,
                })
            )
            setTempDevices(defaultDevices)
            setOriginalDevices(defaultDevices)
        } finally {
            setLoading(false)
        }
    }, [])

    // Effect to fetch devices on mount
    useEffect(() => {
        fetchDevices()
    }, [fetchDevices])

    // Define the refresh function based on the stable fetchDevices
    const refreshDeviceData = useCallback(() => {
        fetchDevices()
    }, [fetchDevices])

    // 處理應用更改 - 將修改保存到後端
    const handleApply = async () => {
        // --- 開始：加入檢查邏輯 ---
        const { activeTx: currentActiveTx, activeRx: currentActiveRx } =
            countActiveDevices(tempDevices)

        if (currentActiveTx < 1 || currentActiveRx < 1) {
            alert(
                '套用失敗：操作後必須至少保留一個啟用的發射器 (desired) 和一個啟用的接收器 (receiver)。請檢查設備的啟用狀態。'
            )
            return
        }
        // --- 結束：加入檢查邏輯 ---

        if (apiStatus !== 'connected') {
            setError('無法保存更改：API連接未建立')
            return
        }

        try {
            setLoading(true)
            setError(null)

            // 1. 處理需要創建的新設備（ID 為負數的臨時設備）
            const newDevices = tempDevices.filter((device) => device.id < 0)

            // 2. 找出需要更新的已存在設備
            const devicesToUpdate = tempDevices.filter((tempDevice) => {
                // 只處理已存在於後端的設備（ID > 0）
                if (tempDevice.id <= 0) return false

                // 找到對應的原始設備
                const originalDevice = originalDevices.find(
                    (org) => org.id === tempDevice.id
                )

                // 如果找不到原始設備，或者設備內容與原始狀態不同，則標記為需要更新
                return (
                    !originalDevice ||
                    JSON.stringify(tempDevice) !==
                        JSON.stringify(originalDevice)
                )
            })

            if (newDevices.length === 0 && devicesToUpdate.length === 0) {
                console.log('沒有檢測到需要保存的更改。')
                setLoading(false)
                return // 沒有更改，提前退出
            }

            // 首先創建新設備
            for (const device of newDevices) {
                console.log('準備創建新設備:', device)

                const backendData = {
                    name: device.name,
                    position_x: Math.round(device.position_x),
                    position_y: Math.round(device.position_y),
                    position_z: Math.round(device.position_z),
                    orientation_x: device.orientation_x,
                    orientation_y: device.orientation_y,
                    orientation_z: device.orientation_z,
                    role: device.role,
                    power_dbm: device.power_dbm,
                    active: device.active,
                }

                console.log('調用 API 創建設備，數據:', backendData)
                try {
                    await createDevice(backendData)
                    console.log('新設備創建成功')
                } catch (error: any) {
                    // 詳細記錄錯誤
                    console.error(
                        '創建設備錯誤詳情:',
                        error.response?.data || error.message
                    )

                    // 處理422錯誤的詳細信息
                    let errorDetail = '未知錯誤'
                    if (error.response?.data?.detail) {
                        if (Array.isArray(error.response.data.detail)) {
                            errorDetail = error.response.data.detail
                                .map((item: any) => {
                                    if (item.msg && item.loc) {
                                        return `${item.msg} at ${item.loc.join(
                                            '.'
                                        )}`
                                    }
                                    return JSON.stringify(item)
                                })
                                .join('; ')
                        } else {
                            errorDetail = error.response.data.detail
                        }
                    } else {
                        errorDetail = error.message || '未知錯誤'
                    }

                    throw new Error(
                        `創建設備 "${device.name}" 失敗: ${errorDetail}`
                    )
                }
            }

            // 然後更新已有設備
            for (const device of devicesToUpdate) {
                const backendData = {
                    name: device.name,
                    position_x: Math.round(device.position_x),
                    position_y: Math.round(device.position_y),
                    position_z: Math.round(device.position_z),
                    orientation_x: device.orientation_x,
                    orientation_y: device.orientation_y,
                    orientation_z: device.orientation_z,
                    role: device.role,
                    power_dbm: device.power_dbm,
                    active: device.active,
                }

                console.log(`正在更新設備 ID: ${device.id}，數據:`, backendData)
                try {
                    await updateDevice(device.id, backendData)
                    console.log(`設備 ID: ${device.id} 更新成功`)
                } catch (error: any) {
                    // 詳細記錄錯誤
                    console.error(
                        `更新設備錯誤詳情:`,
                        error.response?.data || error.message
                    )

                    // 處理422錯誤的詳細信息
                    let errorDetail = '未知錯誤'
                    if (error.response?.data?.detail) {
                        if (Array.isArray(error.response.data.detail)) {
                            errorDetail = error.response.data.detail
                                .map((item: any) => {
                                    if (item.msg && item.loc) {
                                        return `${item.msg} at ${item.loc.join(
                                            '.'
                                        )}`
                                    }
                                    return JSON.stringify(item)
                                })
                                .join('; ')
                        } else {
                            errorDetail = error.response.data.detail
                        }
                    } else {
                        errorDetail = error.message || '未知錯誤'
                    }

                    throw new Error(
                        `更新設備 ID: ${device.id} 失敗: ${errorDetail}`
                    )
                }
            }

            // 所有更改完成後，重新獲取設備列表
            console.log('所有更新完成，正在重新獲取設備列表...')
            const updatedBackendDevices = await getDevices()
            const updatedFrontendDevices = updatedBackendDevices.map(
                convertBackendToFrontend
            )
            setTempDevices(updatedFrontendDevices)
            setOriginalDevices(updatedFrontendDevices)
            setHasTempDevices(false)
            console.log('設備列表已更新，前端應已觸發重新渲染')
        } catch (err: any) {
            console.error('保存設備更新失敗:', err)
            const errorMessage = err.message || '未知錯誤'
            setError(`保存設備更新時發生錯誤: ${errorMessage}`)
        } finally {
            setLoading(false)
        }
    }

    // 處理取消更改
    const handleCancel = () => {
        setTempDevices([...originalDevices])
        setHasTempDevices(false)
        setError(null)
    }

    // 處理刪除設備
    const handleDeleteDevice = async (id: number) => {
        // 如果是新添加的、未保存的設備 (ID 為負數)
        if (id < 0) {
            setTempDevices((prev) => prev.filter((device) => device.id !== id))
            setHasTempDevices(true)
            console.log(`已從前端移除臨時設備 ID: ${id}`)
            return
        }

        // --- 開始：現有設備的檢查邏輯 ---
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
        // --- 結束：現有設備的檢查邏輯 ---

        if (apiStatus !== 'connected') {
            setError('無法刪除設備：API連接未建立')
            return
        }

        // 添加確認對話框
        if (!window.confirm('確定要刪除這個設備嗎？此操作將立即生效。')) {
            return
        }

        try {
            setLoading(true)
            setError(null)
            console.log(`調用 API 刪除設備 ID: ${id}`)
            await deleteDevice(id)
            console.log(`設備 ID: ${id} 刪除成功`)

            // 從前端狀態中移除已刪除的設備
            setTempDevices((prev) => prev.filter((device) => device.id !== id))
            setOriginalDevices((prev) =>
                prev.filter((device) => device.id !== id)
            )
            setHasTempDevices(
                JSON.stringify(tempDevices) !== JSON.stringify(originalDevices)
            )
        } catch (err: any) {
            console.error(`刪除設備ID ${id} 失敗:`, err)
            setError(
                `刪除設備 ID: ${id} 失敗: ${
                    err.response?.data?.detail || err.message || '未知錯誤'
                }`
            )
        } finally {
            setLoading(false)
        }
    }

    // 處理添加新設備
    const handleAddDevice = () => {
        // 產生一個負數 ID，用於標識臨時設備
        const tempId = -Math.floor(Math.random() * 1000000) - 1

        // 根據選定的設備類型生成不同的名稱前綴
        const getPrefix = (role: string = 'receiver') => {
            switch (role) {
                case 'desired':
                    return 'tx'
                case 'receiver':
                    return 'rx'
                case 'jammer':
                    return 'jam'
                default:
                    return 'device'
            }
        }

        // 獲取已存在的設備名稱列表，以確保不會重複
        const existingNames = tempDevices.map((device) => device.name)

        // 修改默認設備類型為 'receiver'
        const defaultRole: string = 'receiver'
        const prefix = getPrefix(defaultRole)

        // 尋找一個可用的名稱（不在現有名稱列表中）
        let index = 1
        let newName = `${prefix}${index}`
        while (existingNames.includes(newName)) {
            index++
            newName = `${prefix}${index}`
        }

        // 創建一個新的臨時設備
        const newDevice: Device = {
            id: tempId,
            name: newName,
            position_x: 0,
            position_y: 0,
            position_z: 40,
            orientation_x: 0,
            orientation_y: 0,
            orientation_z: 0,
            power_dbm: 0,
            active: true,
            role: defaultRole,
        }

        // 更新 tempDevices 狀態，添加新的臨時設備
        setTempDevices((prev) => [...prev, newDevice])
        // 標記有臨時設備
        setHasTempDevices(true)

        console.log('已在前端創建臨時設備:', newDevice)
    }

    // 處理單個設備屬性更改
    const handleDeviceChange = (
        id: number,
        field: keyof Device,
        value: any
    ) => {
        setTempDevices((prev) => {
            if (field === 'role') {
                const deviceToUpdate = prev.find((d) => d.id === id)
                if (deviceToUpdate) {
                    const currentName = deviceToUpdate.name
                    const isDefaultNamingFormat = /^(tx|rx|jam)\d+$/.test(
                        currentName
                    )
                    const newRole = value as string

                    // Only auto-update name if it was default or it's a new device
                    if (isDefaultNamingFormat || deviceToUpdate.id < 0) {
                        const getPrefix = (role: string): string => {
                            switch (role) {
                                case 'desired':
                                    return 'tx'
                                case 'receiver':
                                    return 'rx'
                                case 'jammer':
                                    return 'jam'
                                default:
                                    return 'device'
                            }
                        }
                        const newPrefix = getPrefix(newRole)

                        // Find the max number among existing devices of the NEW type (excluding the current one)
                        let maxNum = 0
                        prev.forEach((device) => {
                            // Skip the device being edited
                            if (device.id === id) return

                            if (device.name.startsWith(newPrefix)) {
                                const match = device.name.match(/-(\d+)$/)
                                if (match) {
                                    const num = parseInt(match[1], 10)
                                    if (!isNaN(num) && num > maxNum) {
                                        maxNum = num
                                    }
                                }
                            }
                        })

                        const newNumber = maxNum + 1
                        const newName = `${newPrefix}${newNumber}`

                        // Note: Uniqueness check might be redundant now but kept for safety
                        let uniqueName = newName
                        let suffix = newNumber
                        const otherNames = prev
                            .filter((d) => d.id !== id)
                            .map((d) => d.name)
                        while (otherNames.includes(uniqueName)) {
                            suffix++
                            uniqueName = `${newPrefix}${suffix}`
                        }

                        // Update role and the newly generated name
                        return prev.map((device) =>
                            device.id === id
                                ? { ...device, role: newRole, name: uniqueName }
                                : device
                        )
                    }
                    // If name wasn't default and it's not a new device, just update role
                    else {
                        return prev.map((device) =>
                            device.id === id
                                ? { ...device, role: newRole }
                                : device
                        )
                    }
                }
            }

            // Handle other field changes (non-role)
            return prev.map((device) =>
                device.id === id ? { ...device, [field]: value } : device
            )
        })

        // 標記為有變更
        setHasTempDevices(true)
    }

    // 處理導航菜單點擊
    const handleMenuClick = (component: string) => {
        setActiveComponent(component)
    }

    // 處理 receiver 選擇變更
    const handleSelectedReceiversChange = (ids: number[]) => {
        console.log('選中的 receiver IDs:', ids)
        setSelectedReceiverIds(ids)
    }

    // 處理手動控制 UAV 方向
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
        // 如果沒有選擇任何 receiver，則不進行控制
        if (selectedReceiverIds.length === 0) {
            console.log('沒有選中的 receiver，無法控制 UAV')
            return
        }

        setManualDirection(direction)
    }

    // 處理 UAV 位置更新
    const handleUAVPositionUpdate = (
        pos: [number, number, number],
        deviceId?: number
    ) => {
        // 如果沒有指定設備 ID，或者該設備 ID 不在選中的 receivers 中，則不做處理
        if (deviceId === undefined || !selectedReceiverIds.includes(deviceId)) {
            return
        }

        setUavPosition(pos)

        // 更新特定設備的座標
        setTempDevices((prevDevices) => {
            const updatedDevices = [...prevDevices]
            const deviceIndex = updatedDevices.findIndex(
                (d) => d.id === deviceId
            )

            if (deviceIndex !== -1) {
                // 座標轉換：Sidebar X = UAV X, Sidebar Y = UAV Z, Sidebar Z = UAV Y
                const newX = parseFloat(pos[0].toFixed(2))
                const newY = parseFloat(pos[2].toFixed(2))
                const newZ = parseFloat(pos[1].toFixed(2))

                // 只有當座標確實變化時才更新
                if (
                    updatedDevices[deviceIndex].position_x !== newX ||
                    updatedDevices[deviceIndex].position_y !== newY ||
                    updatedDevices[deviceIndex].position_z !== newZ
                ) {
                    updatedDevices[deviceIndex] = {
                        ...updatedDevices[deviceIndex],
                        position_x: newX,
                        position_y: newY,
                        position_z: newZ,
                    }

                    // 標記為有未保存的變更
                    setTimeout(() => setHasTempDevices(true), 0)
                    return updatedDevices
                }
            }

            return prevDevices
        })
    }

    // 當選中的 receiver ID 列表變化時，計算並保存每個 UAV 的相對位置偏移
    useEffect(() => {
        if (selectedReceiverIds.length <= 1) {
            // 如果只有一個或沒有選中的 receiver，不需要計算偏移
            setUavOffsets({})
            setOffsetsInitialized(false)
            return
        }

        // 找出選中的 receiver 設備
        const selectedReceivers = tempDevices.filter(
            (device) =>
                device.role === 'receiver' &&
                device.id !== null &&
                selectedReceiverIds.includes(device.id)
        )

        if (selectedReceivers.length <= 1) return

        // 以第一個選中的 receiver 為參考點
        const referenceDevice = selectedReceivers[0]
        const newOffsets: {
            [key: number]: { x: number; y: number; z: number }
        } = {}

        // 計算其他 receiver 相對於參考點的位置偏移
        selectedReceivers.forEach((device) => {
            if (device.id === null) return

            newOffsets[device.id] = {
                x: device.position_x - referenceDevice.position_x,
                y: device.position_y - referenceDevice.position_y,
                z: device.position_z - referenceDevice.position_z,
            }
        })

        setUavOffsets(newOffsets)
        setOffsetsInitialized(true)
    }, [selectedReceiverIds, tempDevices])

    // 渲染當前選中的組件
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
                                // 定義角色排序優先級
                                const roleOrder: { [key: string]: number } = {
                                    receiver: 1,
                                    desired: 2,
                                    jammer: 3,
                                }
                                const roleA = roleOrder[a.role] || 99
                                const roleB = roleOrder[b.role] || 99

                                // 首先按角色排序
                                if (roleA !== roleB) {
                                    return roleA - roleB
                                }

                                // 如果角色相同，則按名稱排序
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
