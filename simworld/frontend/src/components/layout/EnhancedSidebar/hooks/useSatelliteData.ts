/**
 * 衛星數據管理 Hook
 * 管理衛星數據的載入、更新和狀態
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { VisibleSatelliteInfo } from '../../../../types/satellite'
import { SATELLITE_CONFIG } from '../../../../config/satellite.config'
import { simWorldApi } from '../../../../services/simworld-api'

interface UseSatelliteDataOptions {
  enabled: boolean
  onDataUpdate?: (satellites: VisibleSatelliteInfo[]) => void
  visibleCount?: number
  minElevation?: number
}

interface SatelliteDataState {
  satellites: VisibleSatelliteInfo[]
  isLoading: boolean
  isInitialized: boolean
  error: string | null
}

export function useSatelliteData(options: UseSatelliteDataOptions) {
  const {
    enabled,
    onDataUpdate,
    visibleCount = SATELLITE_CONFIG.VISIBLE_COUNT,
    minElevation = SATELLITE_CONFIG.MIN_ELEVATION,
  } = options

  const [state, setState] = useState<SatelliteDataState>({
    satellites: [],
    isLoading: false,
    isInitialized: false,
    error: null,
  })

  const initializationRef = useRef(false)
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null)

  /**
   * 獲取可見衛星數據
   */
  const fetchVisibleSatellites = useCallback(async (
    count: number,
    elevation: number
  ): Promise<VisibleSatelliteInfo[]> => {
    try {
      console.log(`🛰️ 獲取可見衛星數據 (數量: ${count}, 最小仰角: ${elevation}°)`)
      
      const response = await simWorldApi.getSatellites({
        limit: count,
        min_elevation: elevation,
      })

      if (response.success && response.data) {
        return response.data as VisibleSatelliteInfo[]
      } else {
        throw new Error(response.error || '獲取衛星數據失敗')
      }
    } catch (error) {
      console.error('獲取衛星數據失敗:', error)
      throw error
    }
  }, [])

  /**
   * 初始化衛星數據
   */
  const initializeSatellites = useCallback(async () => {
    if (!enabled) {
      setState(prev => ({
        ...prev,
        satellites: [],
        isInitialized: false,
        error: null,
      }))
      
      if (onDataUpdate) {
        onDataUpdate([])
      }
      
      initializationRef.current = false
      return
    }

    // 如果已經初始化過，就不再重新載入
    if (initializationRef.current) {
      console.log('🛰️ 衛星數據已初始化，使用內在軌道運動，避免重新載入')
      return
    }

    console.log('🛰️ 首次初始化衛星數據...')
    
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const satellites = await fetchVisibleSatellites(visibleCount, minElevation)
      
      // 按仰角排序
      const sortedSatellites = [...satellites].sort(
        (a, b) => b.elevation_deg - a.elevation_deg
      )

      setState(prev => ({
        ...prev,
        satellites: sortedSatellites,
        isLoading: false,
        isInitialized: true,
        error: null,
      }))

      if (onDataUpdate) {
        onDataUpdate(sortedSatellites)
      }

      initializationRef.current = true
      console.log(`🛰️ 衛星數據初始化完成，載入 ${sortedSatellites.length} 顆衛星`)
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知錯誤'
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }))
      
      console.error('🛰️ 衛星數據初始化失敗:', errorMessage)
    }
  }, [enabled, onDataUpdate, fetchVisibleSatellites, visibleCount, minElevation])

  /**
   * 清理資源
   */
  const cleanup = useCallback(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current)
      refreshIntervalRef.current = null
    }
  }, [])

  /**
   * 重新載入衛星數據
   */
  const reloadSatellites = useCallback(() => {
    initializationRef.current = false
    initializeSatellites()
  }, [initializeSatellites])

  /**
   * 更新衛星可見數量
   */
  const updateVisibleCount = useCallback((newCount: number) => {
    if (newCount !== visibleCount) {
      initializationRef.current = false
      // 這裡需要外部更新 visibleCount，然後重新初始化
      reloadSatellites()
    }
  }, [visibleCount, reloadSatellites])

  // 主要效果：衛星啟用狀態變化時初始化
  useEffect(() => {
    cleanup()
    initializeSatellites()
    
    return cleanup
  }, [enabled, initializeSatellites, cleanup])

  return {
    satellites: state.satellites,
    isLoading: state.isLoading,
    isInitialized: state.isInitialized,
    error: state.error,
    reloadSatellites,
    updateVisibleCount,
  }
}