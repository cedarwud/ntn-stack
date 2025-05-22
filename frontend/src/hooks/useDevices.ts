import { useState, useEffect, useCallback } from 'react'
import {
    getDevices as apiGetDevices,
    createDevice as apiCreateDevice,
    updateDevice as apiUpdateDevice,
    deleteDevice as apiDeleteDevice,
} from '../services'
import { Device, DeviceCreate, DeviceUpdate } from '../types/device'
import { convertBackendToFrontend } from '../utils/deviceUtils'

export const useDevices = () => {
    const [tempDevices, setTempDevices] = useState<Device[]>([])
    const [originalDevices, setOriginalDevices] = useState<Device[]>([])
    const [loading, setLoading] = useState<boolean>(true)
    const [error, setError] = useState<string | null>(null)
    const [apiStatus, setApiStatus] = useState<
        'disconnected' | 'connected' | 'error'
    >('disconnected')
    const [hasTempDevices, setHasTempDevices] = useState<boolean>(false)

    const fetchDevices = useCallback(async () => {
        try {
            setLoading(true)
            setApiStatus('disconnected')
            console.log('嘗試從API獲取設備數據 (來自 useDevices Hook)...')
            const backendDevices = await apiGetDevices()
            console.log('成功獲取設備數據 (來自 useDevices Hook):', backendDevices)

            const frontendDevices = backendDevices.map(convertBackendToFrontend)

            setTempDevices(frontendDevices)
            setOriginalDevices(frontendDevices)
            setError(null)
            setApiStatus('connected')
            setHasTempDevices(false)

            // 注意：原 App.tsx 中 setSelectedReceiverIds 的邏輯已移除，
            // App.tsx 將在拿到 tempDevices 後自行處理 selectedReceiverIds
        } catch (err: any) {
            console.error('獲取設備失敗 (來自 useDevices Hook):', err)
            const errorMessage = err.message || '未知錯誤'
            setError(`獲取設備數據時發生錯誤: ${errorMessage}`)
            setApiStatus('error')

            const defaultDevices: Device[] = Array.from(
                { length: 3 },
                (_, i) => ({
                    id: -(i + 1),
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
            setHasTempDevices(false)
        } finally {
            setLoading(false)
        }
    }, [convertBackendToFrontend])

    useEffect(() => {
        fetchDevices()
    }, [fetchDevices])

    const applyDeviceChanges = async () => {
        if (apiStatus !== 'connected') {
            setError('無法保存更改：API連接未建立')
            return false
        }

        setLoading(true)
        setError(null)

        try {
            const newDevices = tempDevices.filter((device) => device.id < 0)
            const devicesToUpdate = tempDevices.filter((tempDevice) => {
                if (tempDevice.id <= 0) return false
                const originalDevice = originalDevices.find(
                    (org) => org.id === tempDevice.id
                )
                return (
                    !originalDevice ||
                    JSON.stringify(tempDevice) !== JSON.stringify(originalDevice)
                )
            })

            if (newDevices.length === 0 && devicesToUpdate.length === 0) {
                console.log('useDevices: 沒有檢測到需要保存的更改。')
                setLoading(false)
                setHasTempDevices(false)
                return true
            }

            for (const device of newDevices) {
                const payload: DeviceCreate = {
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
                await apiCreateDevice(payload)
            }

            for (const device of devicesToUpdate) {
                const payload: DeviceUpdate = {
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
                await apiUpdateDevice(device.id, payload)
            }

            console.log('useDevices: 所有更新完成，正在重新獲取設備列表...')
            await fetchDevices()
            setHasTempDevices(false)
            return true
        } catch (err: any) {
            console.error('useDevices: 保存設備更新失敗:', err)
            const errorMessage = err.response?.data?.detail || err.message || '未知錯誤'
            let detailedError = errorMessage
            if (Array.isArray(err.response?.data?.detail)) {
                detailedError = err.response.data.detail
                    .map((item: any) => item.msg || JSON.stringify(item))
                    .join('; ')
            }
            setError(`保存設備更新時發生錯誤: ${detailedError}`)
            return false
        } finally {
            setLoading(false)
        }
    }

    const deleteDeviceById = async (id: number): Promise<boolean> => {
        if (apiStatus !== 'connected') {
            setError('無法刪除設備：API連接未建立')
            return false
        }

        setLoading(true)
        setError(null)
        try {
            console.log(`useDevices: 調用 API 刪除設備 ID: ${id}`)
            await apiDeleteDevice(id)
            console.log(`useDevices: 設備 ID: ${id} 刪除成功`)
            await fetchDevices()
            return true
        } catch (err: any) {
            console.error(`useDevices: 刪除設備ID ${id} 失敗:`, err)
            setError(
                `刪除設備 ID: ${id} 失敗: ${ err.response?.data?.detail || err.message || '未知錯誤' }`
            )
            return false
        } finally {
            setLoading(false)
        }
    }

    const addNewDevice = () => {
        const tempId = -Math.floor(Math.random() * 1000000) - 1;
        const getPrefix = (role: string = 'receiver'): string => {
            switch (role) {
                case 'desired': return 'tx';
                case 'receiver': return 'rx';
                case 'jammer': return 'jam';
                default: return 'device';
            }
        };
        const existingNames = tempDevices.map((device) => device.name);
        const defaultRole: string = 'receiver';
        const prefix = getPrefix(defaultRole);
        let index = 1;
        let newName = `${prefix}${index}`;
        while (existingNames.includes(newName)) {
            index++;
            newName = `${prefix}${index}`;
        }
        const newDevice: Device = {
            id: tempId, name: newName,
            position_x: 0, position_y: 0, position_z: 40,
            orientation_x: 0, orientation_y: 0, orientation_z: 0,
            power_dbm: 0, active: true, role: defaultRole,
        };
        setTempDevices((prev) => [...prev, newDevice]);
        setHasTempDevices(true);
        console.log('useDevices: 已在前端創建臨時設備:', newDevice);
    };

    // 新增：處理單個設備屬性更改的函數
    const updateDeviceField = (
        id: number,
        field: keyof Device, // 在 Hook 內部，我們可以堅持使用 keyof Device
        value: any
    ) => {
        setTempDevices((prev) => {
            const newDevices = prev.map((device) => {
                if (device.id === id) {
                    // 如果是角色變更，需要處理名稱自動更新的邏輯
                    if (field === 'role') {
                        const deviceToUpdate = device; // device 已經是當前要更新的對象
                        const currentName = deviceToUpdate.name;
                        const isDefaultNamingFormat = /^(tx|rx|jam)\d+$/.test(currentName);
                        const newRole = value as string;

                        if (isDefaultNamingFormat || deviceToUpdate.id < 0) {
                            const getPrefix = (role: string): string => {
                                switch (role) {
                                    case 'desired': return 'tx';
                                    case 'receiver': return 'rx';
                                    case 'jammer': return 'jam';
                                    default: return 'device';
                                }
                            };
                            const newPrefix = getPrefix(newRole);
                            let maxNum = 0;
                            // 遍歷的是 prev (更新前的列表)，以確定新編號
                            prev.forEach((d) => {
                                if (d.id === id) return; // 跳過正在編輯的設備自身
                                if (d.role === newRole && d.name.startsWith(newPrefix)) { // 確保是同類型且是預設前綴開頭
                                    // 修改正則表達式以匹配 tx1, rx2 等，而不是 tx-1, rx-2
                                    const match = d.name.match(new RegExp(`^${newPrefix}(\d+)$`));
                                    if (match) {
                                        const num = parseInt(match[1], 10);
                                        if (!isNaN(num) && num > maxNum) maxNum = num;
                                    }
                                }
                            });
                            const newNumber = maxNum + 1;
                            let uniqueName = `${newPrefix}${newNumber}`;
                            // 檢查新名稱是否與 *其他* 設備衝突 (再次遍歷 prev)
                            const otherNames = prev.filter(d => d.id !== id).map(d => d.name);
                            let suffix = newNumber;
                            while(otherNames.includes(uniqueName)){
                                suffix++;
                                uniqueName = `${newPrefix}${suffix}`;
                            }
                            return { ...device, role: newRole, name: uniqueName };
                        }
                        // 如果名稱不是默認格式，或者不是新設備，則僅更新角色
                        return { ...device, role: newRole }; 
                    }
                    // 其他欄位直接更新
                    return { ...device, [field]: value };
                }
                return device;
            });
            return newDevices;
        });
        setHasTempDevices(true);
    };

    // 新增：處理取消更改的函數
    const cancelDeviceChanges = () => {
        setTempDevices([...originalDevices]); // 從 originalDevices 恢復
        setHasTempDevices(false);             // 清除臨時更改標記
        setError(null);                       // 清除錯誤信息
        console.log('useDevices: 更改已取消，已恢復到原始設備狀態。');
    };

    // 新增：處理來自 UAV 的設備位置更新
    const updateDevicePositionFromUAV = (deviceId: number, pos: [number, number, number]) => {
        setTempDevices((prevDevices) => {
            const updatedDevices = [...prevDevices];
            const deviceIndex = updatedDevices.findIndex(
                (d) => d.id === deviceId
            );

            if (deviceIndex !== -1) {
                const newX = parseFloat(pos[0].toFixed(2));
                const newY = parseFloat(pos[2].toFixed(2)); // 注意 App.tsx 中 y 和 z 的對應關係
                const newZ = parseFloat(pos[1].toFixed(2)); // 注意 App.tsx 中 y 和 z 的對應關係

                // 檢查位置是否有實際變化
                if (
                    updatedDevices[deviceIndex].position_x !== newX ||
                    updatedDevices[deviceIndex].position_y !== newY || // 通常後端是 y，但 App.tsx 用的是 pos[2] for y
                    updatedDevices[deviceIndex].position_z !== newZ    // 通常後端是 z，但 App.tsx 用的是 pos[1] for z
                ) {
                    updatedDevices[deviceIndex] = {
                        ...updatedDevices[deviceIndex],
                        position_x: newX,
                        position_y: newY, // 假設後端是 y
                        position_z: newZ, // 假設後端是 z
                    };
                    // 使用 setTimeout 確保狀態更新在下一個事件循環中觸發，
                    // 這與 App.tsx 中的原始實現一致。
                    setTimeout(() => setHasTempDevices(true), 0);
                    return updatedDevices;
                }
            }
            return prevDevices; // 如果沒有找到設備或位置未改變，返回原始列表
        });
        // console.log(`useDevices: 已更新設備 ID ${deviceId} 的位置信息來自 UAV:`, pos); // 註解掉飛行時的 log
    };

    return {
        tempDevices,
        originalDevices,
        loading,
        error,
        apiStatus,
        hasTempDevices,
        fetchDevices,
        setTempDevices,
        setOriginalDevices,
        setHasTempDevices,
        setError,
        applyDeviceChanges,
        deleteDeviceById,
        addNewDevice,
        updateDeviceField,
        cancelDeviceChanges,
        updateDevicePositionFromUAV,
    }
} 