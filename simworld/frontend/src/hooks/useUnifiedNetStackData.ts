/**
 * 統一的 NetStack 數據管理 Hook
 * 替代多個 Hook 重複調用相同 API 的問題
 * 提供統一的數據快取和狀態管理
 */

import { useState, useEffect, useCallback } from 'react'
import { unifiedDataService, DataSourceStatus } from '../services/unified-data-service'

// 統一數據狀態接口
interface UnifiedDataState {
  coreSync: {
    data: unknown | null
    status: DataSourceStatus
    error?: string
    lastUpdate?: string
  }
  satelliteData: {
    data: unknown
    status: DataSourceStatus
    error?: string
    lastUpdate?: string
  }
  healthStatus: {
    data: unknown | null
    status: DataSourceStatus
    error?: string
    lastUpdate?: string
  }
  handoverLatency: {
    data: unknown | null
    status: DataSourceStatus
    error?: string
    lastUpdate?: string
  }
}

export const useUnifiedNetStackData = (isEnabled: boolean = true) => {
  const [dataState, setDataState] = useState<UnifiedDataState>({
    coreSync: { data: null, status: 'loading' },
    satelliteData: { data: {}, status: 'loading' },
    healthStatus: { data: null, status: 'loading' },
    handoverLatency: { data: null, status: 'loading' }
  })

  // 刷新所有數據
  const refreshAllData = useCallback(async () => {
    if (!isEnabled) return

    console.log('🔄 Refreshing all NetStack data via unified service')

    const [coreSync, satelliteData, healthStatus, handoverLatency] = await Promise.allSettled([
      unifiedDataService.getCoreSync(),
      unifiedDataService.getSatelliteData(),
      unifiedDataService.getHealthStatus(),
      unifiedDataService.getHandoverLatencyMetrics()
    ])

    setDataState({
      coreSync: coreSync.status === 'fulfilled' ? coreSync.value : { 
        data: null, 
        status: 'error', 
        error: 'Failed to fetch core sync data' 
      },
      satelliteData: satelliteData.status === 'fulfilled' ? satelliteData.value : { 
        data: {}, 
        status: 'error', 
        error: 'Failed to fetch satellite data' 
      },
      healthStatus: healthStatus.status === 'fulfilled' ? healthStatus.value : { 
        data: null, 
        status: 'error', 
        error: 'Failed to fetch health status' 
      },
      handoverLatency: handoverLatency.status === 'fulfilled' ? handoverLatency.value : { 
        data: null, 
        status: 'error', 
        error: 'Failed to fetch handover latency' 
      }
    })

    console.log('✅ All NetStack data refreshed')
  }, [isEnabled])

  // 刷新核心同步數據
  const refreshCoreSync = useCallback(async () => {
    if (!isEnabled) return

    const result = await unifiedDataService.getCoreSync()
    setDataState(prev => ({
      ...prev,
      coreSync: result
    }))
    
    return result
  }, [isEnabled])

  // 刷新衛星數據
  const refreshSatelliteData = useCallback(async () => {
    if (!isEnabled) return

    const result = await unifiedDataService.getSatelliteData()
    setDataState(prev => ({
      ...prev,
      satelliteData: result
    }))
    
    return result
  }, [isEnabled])

  // 刷新健康狀態
  const refreshHealthStatus = useCallback(async () => {
    if (!isEnabled) return

    const result = await unifiedDataService.getHealthStatus()
    setDataState(prev => ({
      ...prev,
      healthStatus: result
    }))
    
    return result
  }, [isEnabled])

  // 刷新換手延遲數據
  const refreshHandoverLatency = useCallback(async () => {
    if (!isEnabled) return

    const result = await unifiedDataService.getHandoverLatencyMetrics()
    setDataState(prev => ({
      ...prev,
      handoverLatency: result
    }))
    
    return result
  }, [isEnabled])

  // 強制刷新快取
  const invalidateCache = useCallback(() => {
    unifiedDataService.invalidateAllCache()
    refreshAllData()
  }, [refreshAllData])

  // 獲取整體數據狀態
  const getOverallStatus = useCallback((): DataSourceStatus => {
    const statuses = [
      dataState.coreSync.status,
      dataState.satelliteData.status,
      dataState.healthStatus.status,
      dataState.handoverLatency.status
    ]

    if (statuses.some(status => status === 'loading')) {
      return 'loading'
    }

    if (statuses.every(status => status === 'real')) {
      return 'real'
    }

    if (statuses.some(status => status === 'real' || status === 'calculated')) {
      return 'calculated'
    }

    if (statuses.every(status => status === 'error')) {
      return 'error'
    }

    return 'fallback'
  }, [dataState])

  // 初始化數據
  useEffect(() => {
    if (isEnabled) {
      refreshAllData()

      // 設置定時更新 (30秒)
      const interval = setInterval(() => {
        refreshAllData()
      }, 30000)

      return () => clearInterval(interval)
    }
  }, [isEnabled, refreshAllData])

  // 獲取快取狀態
  const getCacheStatus = useCallback(() => {
    return unifiedDataService.getCacheStatus()
  }, [])

  return {
    // 數據狀態
    ...dataState,
    
    // 整體狀態
    overallStatus: getOverallStatus(),
    
    // 刷新函數
    refresh: {
      all: refreshAllData,
      coreSync: refreshCoreSync,
      satelliteData: refreshSatelliteData,
      healthStatus: refreshHealthStatus,
      handoverLatency: refreshHandoverLatency
    },
    
    // 工具函數
    invalidateCache,
    getCacheStatus,
    
    // 便利屬性
    isLoading: getOverallStatus() === 'loading',
    hasError: getOverallStatus() === 'error',
    hasRealData: getOverallStatus() === 'real'
  }
}