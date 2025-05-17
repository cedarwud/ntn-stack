import { useState, useCallback } from 'react'
import {
    getDevices as apiGetDevices,
    createDevice as apiCreateDevice,
    updateDevice as apiUpdateDevice,
    deleteDevice as apiDeleteDevice,
    Device as BackendDevice,
    DeviceCreate,
    DeviceUpdate,
} from '../services/api'

export function useDevices() {
    const [devices, setDevices] = useState<BackendDevice[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const syncDevices = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await apiGetDevices()
            setDevices(data)
        } catch (e: any) {
            setError(e.message || '取得設備失敗')
        } finally {
            setLoading(false)
        }
    }, [])

    const createDevice = useCallback(async (payload: DeviceCreate) => {
        setLoading(true)
        setError(null)
        try {
            const newDevice = await apiCreateDevice(payload)
            setDevices((prev) => [...prev, newDevice])
            return newDevice
        } catch (e: any) {
            setError(e.message || '新增設備失敗')
            throw e
        } finally {
            setLoading(false)
        }
    }, [])

    const updateDevice = useCallback(async (id: number, payload: DeviceUpdate) => {
        setLoading(true)
        setError(null)
        try {
            const updated = await apiUpdateDevice(id, payload)
            setDevices((prev) => prev.map((d) => (d.id === id ? updated : d)))
            return updated
        } catch (e: any) {
            setError(e.message || '更新設備失敗')
            throw e
        } finally {
            setLoading(false)
        }
    }, [])

    const deleteDevice = useCallback(async (id: number) => {
        setLoading(true)
        setError(null)
        try {
            await apiDeleteDevice(id)
            setDevices((prev) => prev.filter((d) => d.id !== id))
        } catch (e: any) {
            setError(e.message || '刪除設備失敗')
            throw e
        } finally {
            setLoading(false)
        }
    }, [])

    return {
        devices,
        setDevices,
        loading,
        error,
        createDevice,
        updateDevice,
        deleteDevice,
        syncDevices,
    }
} 