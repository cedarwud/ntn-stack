import { useState, useEffect, useMemo } from 'react'
import { Device } from '../../../types/device'
import { UseDeviceManagementReturn, DeviceOrientationInputs } from '../types/sidebar.types'
import { generateDeviceName as utilGenerateDeviceName } from '../../../utils/deviceName'

interface UseDeviceManagementProps {
    devices: Device[]
    onDeviceChange: (id: number, field: keyof Device, value: unknown) => void
}

export const useDeviceManagement = ({
    devices,
    onDeviceChange,
}: UseDeviceManagementProps): UseDeviceManagementReturn => {
    // 方向輸入狀態管理
    const [orientationInputs, setOrientationInputs] = useState<DeviceOrientationInputs>({})

    // 同步後端方向數據到前端輸入框
    useEffect(() => {
        let hasChanges = false
        const newInputs: DeviceOrientationInputs = { ...orientationInputs }

        devices.forEach((device) => {
            const existingInput = orientationInputs[device.id]
            const backendX = device.orientation_x?.toString() || '0'
            const backendY = device.orientation_y?.toString() || '0'
            const backendZ = device.orientation_z?.toString() || '0'

            if (existingInput) {
                // 如果前端輸入為空，則從後端補充數據
                if (!existingInput.x && backendX !== '0') {
                    existingInput.x = backendX
                    hasChanges = true
                }
                if (!existingInput.y && backendY !== '0') {
                    existingInput.y = backendY
                    hasChanges = true
                }
                if (!existingInput.z && backendZ !== '0') {
                    existingInput.z = backendZ
                    hasChanges = true
                }
            } else {
                // 如果設備沒有輸入記錄，創建新的記錄
                newInputs[device.id] = {
                    x: backendX,
                    y: backendY,
                    z: backendZ,
                }
                hasChanges = true
            }
        })

        if (hasChanges) {
            setOrientationInputs(newInputs)
        }
    }, [devices, orientationInputs])

    // 設備分組（使用 useMemo 優化性能）
    const tempDevices = useMemo(
        () => devices.filter((device) => device.id == null || device.id < 0),
        [devices]
    )

    const receiverDevices = useMemo(
        () =>
            devices.filter(
                (device) =>
                    device.id != null && device.id >= 0 && device.role === 'receiver'
            ),
        [devices]
    )

    const desiredDevices = useMemo(
        () =>
            devices.filter(
                (device) =>
                    device.id != null && device.id >= 0 && device.role === 'desired'
            ),
        [devices]
    )

    const jammerDevices = useMemo(
        () =>
            devices.filter(
                (device) =>
                    device.id != null && device.id >= 0 && device.role === 'jammer'
            ),
        [devices]
    )

    // 方向輸入處理
    const handleOrientationInputChange = (
        deviceId: number,
        axis: 'x' | 'y' | 'z',
        value: string
    ) => {
        setOrientationInputs((prev) => ({
            ...prev,
            [deviceId]: {
                ...prev[deviceId],
                [axis]: value,
            },
        }))

        // 處理分數輸入 (如 "1/2" 轉換為 π/2)
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
            // 處理數值輸入
            const numValue = parseFloat(value)
            if (!isNaN(numValue)) {
                const orientationKey = `orientation_${axis}` as keyof Device
                onDeviceChange(deviceId, orientationKey, numValue)
            }
        }
    }

    // 設備角色變更處理
    const handleDeviceRoleChange = (deviceId: number, newRole: string) => {
        const newName = utilGenerateDeviceName(
            newRole,
            devices.map((d) => ({ name: d.name }))
        )
        onDeviceChange(deviceId, 'role', newRole)
        onDeviceChange(deviceId, 'name', newName)
    }

    return {
        orientationInputs,
        tempDevices,
        receiverDevices,
        desiredDevices,
        jammerDevices,
        handleOrientationInputChange,
        handleDeviceRoleChange,
    }
}