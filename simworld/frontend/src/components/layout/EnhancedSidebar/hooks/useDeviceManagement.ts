/**
 * 設備管理 Hook
 * 管理設備的方向輸入、接收器選擇等功能
 */

import { useState, useEffect, useCallback } from 'react'
import { Device } from '../../../../types/device'
import { OrientationInput, DeviceManagementState } from '../types'

interface UseDeviceManagementOptions {
  devices: Device[]
  onDeviceChange: (id: number, field: keyof Device, value: unknown) => void
  onSelectedReceiversChange?: (selectedIds: number[]) => void
}

export function useDeviceManagement(options: UseDeviceManagementOptions) {
  const { devices, onDeviceChange, onSelectedReceiversChange } = options

  const [state, setState] = useState<DeviceManagementState>({
    orientationInputs: {},
    selectedReceivers: [],
    tempDevices: [],
  })

  /**
   * 更新方向輸入
   */
  const updateOrientationInputs = useCallback(() => {
    const newInputs: Record<number, OrientationInput> = {}
    let hasChanges = false

    devices.forEach((device) => {
      const existingInput = state.orientationInputs[device.id]
      const backendX = device.orientation_x?.toString() || '0'
      const backendY = device.orientation_y?.toString() || '0'
      const backendZ = device.orientation_z?.toString() || '0'

      if (existingInput) {
        const newInput = {
          x: existingInput.x !== '0' && existingInput.x !== backendX
            ? existingInput.x
            : backendX,
          y: existingInput.y !== '0' && existingInput.y !== backendY
            ? existingInput.y
            : backendY,
          z: existingInput.z !== '0' && existingInput.z !== backendZ
            ? existingInput.z
            : backendZ,
        }
        newInputs[device.id] = newInput

        // 檢查是否有實際變化
        if (JSON.stringify(existingInput) !== JSON.stringify(newInput)) {
          hasChanges = true
        }
      } else {
        newInputs[device.id] = {
          x: backendX,
          y: backendY,
          z: backendZ,
        }
        hasChanges = true
      }
    })

    // 只有在有實際變化時才更新狀態
    if (hasChanges) {
      setState(prev => ({
        ...prev,
        orientationInputs: newInputs,
      }))
    }
  }, [devices, state.orientationInputs])

  /**
   * 處理設備方向輸入變更
   */
  const handleDeviceOrientationInputChange = useCallback((
    deviceId: number,
    axis: 'x' | 'y' | 'z',
    value: string
  ) => {
    setState(prev => ({
      ...prev,
      orientationInputs: {
        ...prev.orientationInputs,
        [deviceId]: {
          ...prev.orientationInputs[deviceId],
          [axis]: value,
        },
      },
    }))
  }, [])

  /**
   * 應用設備方向變更
   */
  const applyDeviceOrientationChange = useCallback((
    deviceId: number,
    axis: 'x' | 'y' | 'z'
  ) => {
    const input = state.orientationInputs[deviceId]
    if (!input) return

    const value = parseFloat(input[axis]) || 0
    const field = `orientation_${axis}` as keyof Device
    
    onDeviceChange(deviceId, field, value)
  }, [state.orientationInputs, onDeviceChange])

  /**
   * 處理接收器選擇變更
   */
  const handleReceiverSelectionChange = useCallback((selectedIds: number[]) => {
    setState(prev => ({
      ...prev,
      selectedReceivers: selectedIds,
    }))
    
    if (onSelectedReceiversChange) {
      onSelectedReceiversChange(selectedIds)
    }
  }, [onSelectedReceiversChange])

  /**
   * 重置設備輸入
   */
  const resetDeviceInputs = useCallback(() => {
    setState(prev => ({
      ...prev,
      orientationInputs: {},
    }))
  }, [])

  /**
   * 獲取設備的當前輸入值
   */
  const getDeviceInput = useCallback((deviceId: number): OrientationInput | undefined => {
    return state.orientationInputs[deviceId]
  }, [state.orientationInputs])

  /**
   * 檢查設備輸入是否有變更
   */
  const hasDeviceInputChanges = useCallback((deviceId: number): boolean => {
    const device = devices.find(d => d.id === deviceId)
    const input = state.orientationInputs[deviceId]
    
    if (!device || !input) return false

    const backendX = device.orientation_x?.toString() || '0'
    const backendY = device.orientation_y?.toString() || '0'
    const backendZ = device.orientation_z?.toString() || '0'

    return input.x !== backendX || input.y !== backendY || input.z !== backendZ
  }, [devices, state.orientationInputs])

  /**
   * 獲取所有有變更的設備
   */
  const getDevicesWithChanges = useCallback((): number[] => {
    return devices
      .map(device => device.id)
      .filter(deviceId => hasDeviceInputChanges(deviceId))
  }, [devices, hasDeviceInputChanges])

  // 設備變更時更新方向輸入
  useEffect(() => {
    updateOrientationInputs()
  }, [updateOrientationInputs])

  return {
    orientationInputs: state.orientationInputs,
    selectedReceivers: state.selectedReceivers,
    tempDevices: state.tempDevices,
    
    // 方法
    handleDeviceOrientationInputChange,
    applyDeviceOrientationChange,
    handleReceiverSelectionChange,
    resetDeviceInputs,
    getDeviceInput,
    hasDeviceInputChanges,
    getDevicesWithChanges,
  }
}