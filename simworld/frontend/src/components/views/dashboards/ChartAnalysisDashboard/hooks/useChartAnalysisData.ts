/**
 * Chart Analysis Data Management Hook
 * 管理所有圖表分析相關的數據獲取和狀態
 */

import { useState, useEffect, useCallback } from 'react'
import { ChartDataService, SatellitePosition, SatelliteData } from '../services/chartDataService'

interface ChartAnalysisState {
  // UAV 和衛星數據
  uavData: SatellitePosition[]
  satelliteData: SatelliteData[]
  tleDataStatus: 'loading' | 'loaded' | 'error'
  
  // 測試和分析數據
  handoverTestData: Record<string, unknown>
  sixScenarioData: Record<string, unknown>
  strategyMetrics: Record<string, unknown>
  
  // 性能數據
  complexityAnalysisData: Record<string, unknown>
  handoverFailureRateData: Record<string, unknown>
  systemResourceData: Record<string, unknown>
  timeSyncPrecisionData: Record<string, unknown>
  performanceRadarData: Record<string, unknown>
  protocolStackDelayData: Record<string, unknown>
  exceptionHandlingData: Record<string, unknown>
  qoeTimeSeriesData: Record<string, unknown>
  globalCoverageData: Record<string, unknown>
  
  // 錯誤狀態
  realDataError: string | null
  
  // 載入狀態
  isLoading: boolean
}

const initialState: ChartAnalysisState = {
  uavData: [],
  satelliteData: [],
  tleDataStatus: 'loading',
  handoverTestData: {},
  sixScenarioData: {},
  strategyMetrics: {},
  complexityAnalysisData: {},
  handoverFailureRateData: {},
  systemResourceData: {},
  timeSyncPrecisionData: {},
  performanceRadarData: {},
  protocolStackDelayData: {},
  exceptionHandlingData: {},
  qoeTimeSeriesData: {},
  globalCoverageData: {},
  realDataError: null,
  isLoading: false,
}

export function useChartAnalysisData(isActive: boolean = true) {
  const [state, setState] = useState<ChartAnalysisState>(initialState)

  // 更新單個數據項目的輔助函數
  const updateData = useCallback((updates: Partial<ChartAnalysisState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  // 設置錯誤狀態
  const setError = useCallback((error: string | null) => {
    updateData({ realDataError: error })
  }, [updateData])

  // 獲取 UAV 數據
  const fetchUAVData = useCallback(async () => {
    try {
      const data = await ChartDataService.fetchRealUAVData()
      updateData({ uavData: data })
      if (data.length === 0) {
        setError('No UAV data available')
      } else {
        setError(null)
      }
    } catch (error) {
      console.error('Error fetching UAV data:', error)
      setError('Failed to fetch UAV data')
    }
  }, [updateData, setError])

  // 獲取衛星 TLE 數據
  const fetchSatelliteData = useCallback(async () => {
    try {
      updateData({ tleDataStatus: 'loading' })
      const data = await ChartDataService.fetchCelestrakTLEData()
      updateData({ 
        satelliteData: data,
        tleDataStatus: data.length > 0 ? 'loaded' : 'error'
      })
    } catch (error) {
      console.error('Error fetching satellite data:', error)
      updateData({ tleDataStatus: 'error' })
      setError('Failed to fetch satellite data')
    }
  }, [updateData, setError])

  // 獲取換手測試數據
  const fetchHandoverData = useCallback(async () => {
    try {
      const data = await ChartDataService.fetchHandoverTestData()
      updateData({ handoverTestData: data })
    } catch (error) {
      console.error('Error fetching handover data:', error)
      setError('Failed to fetch handover test data')
    }
  }, [updateData, setError])

  // 獲取六場景數據
  const fetchSixScenarioData = useCallback(async () => {
    try {
      const data = await ChartDataService.fetchSixScenarioData()
      updateData({ sixScenarioData: data })
    } catch (error) {
      console.error('Error fetching six scenario data:', error)
      setError('Failed to fetch six scenario data')
    }
  }, [updateData, setError])

  // 獲取策略效果數據
  const fetchStrategyData = useCallback(async () => {
    try {
      const data = await ChartDataService.fetchStrategyEffectData()
      updateData({ strategyMetrics: data })
    } catch (error) {
      console.error('Error fetching strategy data:', error)
      setError('Failed to fetch strategy effect data')
    }
  }, [updateData, setError])

  // 獲取所有性能分析數據
  const fetchPerformanceData = useCallback(async () => {
    try {
      updateData({ isLoading: true })
      
      const [
        complexityData,
        failureRateData,
        resourceData,
        timeSyncData,
        radarData,
        protocolData,
        exceptionData,
        qoeData,
        coverageData,
      ] = await Promise.allSettled([
        ChartDataService.fetchComplexityAnalysisData(),
        ChartDataService.fetchHandoverFailureRateData(),
        ChartDataService.fetchSystemResourceData(),
        ChartDataService.fetchTimeSyncPrecisionData(),
        ChartDataService.fetchPerformanceRadarData(),
        ChartDataService.fetchProtocolStackDelayData(),
        ChartDataService.fetchExceptionHandlingData(),
        ChartDataService.fetchQoETimeSeriesData(),
        ChartDataService.fetchGlobalCoverageData(),
      ])

      updateData({
        complexityAnalysisData: complexityData.status === 'fulfilled' ? complexityData.value : {},
        handoverFailureRateData: failureRateData.status === 'fulfilled' ? failureRateData.value : {},
        systemResourceData: resourceData.status === 'fulfilled' ? resourceData.value : {},
        timeSyncPrecisionData: timeSyncData.status === 'fulfilled' ? timeSyncData.value : {},
        performanceRadarData: radarData.status === 'fulfilled' ? radarData.value : {},
        protocolStackDelayData: protocolData.status === 'fulfilled' ? protocolData.value : {},
        exceptionHandlingData: exceptionData.status === 'fulfilled' ? exceptionData.value : {},
        qoeTimeSeriesData: qoeData.status === 'fulfilled' ? qoeData.value : {},
        globalCoverageData: coverageData.status === 'fulfilled' ? coverageData.value : {},
        isLoading: false,
      })

      // 檢查是否有任何失敗的請求
      const failedRequests = [
        complexityData, failureRateData, resourceData, timeSyncData,
        radarData, protocolData, exceptionData, qoeData, coverageData
      ].filter(result => result.status === 'rejected')

      if (failedRequests.length > 0) {
        console.warn(`${failedRequests.length} performance data requests failed`)
      }

    } catch (error) {
      console.error('Error fetching performance data:', error)
      updateData({ isLoading: false })
      setError('Failed to fetch performance data')
    }
  }, [updateData, setError])

  // 重新整理所有數據
  const refreshAllData = useCallback(() => {
    if (!isActive) return

    fetchUAVData()
    fetchSatelliteData()
    fetchHandoverData()
    fetchSixScenarioData()
    fetchStrategyData()
    fetchPerformanceData()
  }, [
    isActive,
    fetchUAVData,
    fetchSatelliteData,
    fetchHandoverData,
    fetchSixScenarioData,
    fetchStrategyData,
    fetchPerformanceData,
  ])

  // 初始化數據載入
  useEffect(() => {
    if (isActive) {
      refreshAllData()
    }
  }, [isActive, refreshAllData])

  // 定期更新數據（每 30 秒）
  useEffect(() => {
    if (!isActive) return

    const interval = setInterval(() => {
      fetchUAVData()
      fetchHandoverData()
    }, 30000)

    return () => clearInterval(interval)
  }, [isActive, fetchUAVData, fetchHandoverData])

  return {
    ...state,
    actions: {
      refreshAllData,
      fetchUAVData,
      fetchSatelliteData,
      fetchHandoverData,
      fetchSixScenarioData,
      fetchStrategyData,
      fetchPerformanceData,
      setError,
    },
  }
}