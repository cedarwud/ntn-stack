import { Device } from '../types/device'

// 轉換後端設備到前端設備格式
export const convertBackendToFrontend = (backendDevice: Device): Device => {
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
        role: backendDevice.role,
    }
}

// 輔助函數：計算啟用設備的數量
export const countActiveDevices = (
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