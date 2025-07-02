/**
 * Chart Analysis Dashboard Data Service - 階段三重構版本
 * 移除直接API調用，改用統一API服務層
 * 保持向後兼容的接口，減少對使用者的影響
 */

import UnifiedChartApiService from './unifiedChartApiService'

export interface SatellitePosition {
  latitude: number
  longitude: number
  altitude: number
  speed?: number
  heading?: number
  last_updated?: string
}

export interface SatelliteData {
  name?: string
  orbit_altitude_km?: number
  [key: string]: unknown
}

export interface ComponentData {
  availability?: number
  accuracy_ms?: number
  latency_ms?: number
  throughput_mbps?: number
  error_rate?: number
  speed?: number
  altitude?: number
  [key: string]: number | string | boolean | undefined
}

/**
 * 重構後的圖表數據服務
 * 所有方法現在都使用統一API服務層
 */
export class ChartDataService {
  /**
   * 獲取 UAV 位置數據 - 使用統一API服務
   */
  static async fetchRealUAVData(): Promise<SatellitePosition[]> {
    try {
      console.log('🚁 ChartDataService: 獲取UAV位置數據')
      return await UnifiedChartApiService.getUAVPositions()
    } catch (error) {
      console.warn('ChartDataService: UAV數據獲取失敗:', error)
      return []
    }
  }

  /**
   * 獲取換手測試數據 - 使用統一API服務
   */
  static async fetchHandoverTestData(): Promise<Record<string, unknown>> {
    try {
      console.log('🔄 ChartDataService: 獲取換手測試數據')
      return await UnifiedChartApiService.getHandoverTestData()
    } catch (error) {
      console.warn('ChartDataService: 換手測試數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取六種場景比較數據 - 使用統一API服務
   */
  static async fetchSixScenarioData(): Promise<Record<string, unknown>> {
    try {
      console.log('📊 ChartDataService: 獲取六種場景比較數據')
      return await UnifiedChartApiService.getSixScenarioData()
    } catch (error) {
      console.warn('ChartDataService: 六種場景數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取 Celestrak TLE 軌道數據 - 使用統一API服務
   */
  static async fetchCelestrakTLEData(): Promise<SatelliteData[]> {
    try {
      console.log('🛰️ ChartDataService: 獲取Celestrak TLE軌道數據')
      return await UnifiedChartApiService.getCelestrakTLEData()
    } catch (error) {
      console.warn('ChartDataService: Celestrak TLE數據獲取失敗:', error)
      return []
    }
  }

  /**
   * 獲取策略效果數據 - 使用統一API服務
   */
  static async fetchStrategyEffectData(): Promise<Record<string, unknown>> {
    try {
      console.log('🎯 ChartDataService: 獲取策略效果數據')
      return await UnifiedChartApiService.getStrategyEffectData()
    } catch (error) {
      console.warn('ChartDataService: 策略效果數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取複雜度分析數據 - 使用統一API服務
   */
  static async fetchComplexityAnalysisData(): Promise<Record<string, unknown>> {
    try {
      console.log('🧮 ChartDataService: 獲取複雜度分析數據')
      const data = await UnifiedChartApiService.getComplexityAnalysis()
      return data as Record<string, unknown>
    } catch (error) {
      console.warn('ChartDataService: 複雜度分析數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取換手失敗率數據 - 使用統一API服務
   */
  static async fetchHandoverFailureRateData(): Promise<Record<string, unknown>> {
    try {
      console.log('❌ ChartDataService: 獲取換手失敗率數據')
      return await UnifiedChartApiService.getHandoverFailureRateData()
    } catch (error) {
      console.warn('ChartDataService: 換手失敗率數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取系統資源數據 - 使用統一API服務
   */
  static async fetchSystemResourceData(): Promise<Record<string, unknown>> {
    try {
      console.log('💻 ChartDataService: 獲取系統資源數據')
      return await UnifiedChartApiService.getSystemResourceData()
    } catch (error) {
      console.warn('ChartDataService: 系統資源數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取時間同步精度數據 - 使用統一API服務
   */
  static async fetchTimeSyncPrecisionData(): Promise<Record<string, unknown>> {
    try {
      console.log('⏰ ChartDataService: 獲取時間同步精度數據')
      return await UnifiedChartApiService.getTimeSyncPrecision()
    } catch (error) {
      console.warn('ChartDataService: 時間同步精度數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取性能雷達數據 - 使用統一API服務
   */
  static async fetchPerformanceRadarData(): Promise<Record<string, unknown>> {
    try {
      console.log('📡 ChartDataService: 獲取性能雷達數據')
      return await UnifiedChartApiService.getPerformanceRadarData()
    } catch (error) {
      console.warn('ChartDataService: 性能雷達數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取協議堆疊延遲數據 - 使用統一API服務
   */
  static async fetchProtocolStackDelayData(): Promise<Record<string, unknown>> {
    try {
      console.log('🔗 ChartDataService: 獲取協議堆疊延遲數據')
      return await UnifiedChartApiService.getProtocolStackDelayData()
    } catch (error) {
      console.warn('ChartDataService: 協議堆疊延遲數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取異常處理數據 - 使用統一API服務
   */
  static async fetchExceptionHandlingData(): Promise<Record<string, unknown>> {
    try {
      console.log('⚠️ ChartDataService: 獲取異常處理數據')
      return await UnifiedChartApiService.getExceptionHandlingData()
    } catch (error) {
      console.warn('ChartDataService: 異常處理數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取 QoE 時間序列數據 - 使用統一API服務
   */
  static async fetchQoETimeSeriesData(): Promise<Record<string, unknown>> {
    try {
      console.log('📈 ChartDataService: 獲取QoE時間序列數據')
      const data = await UnifiedChartApiService.getQoETimeSeries()
      return data as Record<string, unknown>
    } catch (error) {
      console.warn('ChartDataService: QoE時間序列數據獲取失敗:', error)
      return {}
    }
  }

  /**
   * 獲取全球覆蓋範圍數據 - 使用統一API服務
   */
  static async fetchGlobalCoverageData(): Promise<Record<string, unknown>> {
    try {
      console.log('🌍 ChartDataService: 獲取全球覆蓋範圍數據')
      return await UnifiedChartApiService.getGlobalCoverageData()
    } catch (error) {
      console.warn('ChartDataService: 全球覆蓋範圍數據獲取失敗:', error)
      return {}
    }
  }

  // ==================== 新增：批量數據獲取方法 ====================

  /**
   * 批量獲取性能相關數據
   */
  static async fetchPerformanceData(): Promise<{
    qoeTimeSeries: Record<string, unknown>
    complexityAnalysis: Record<string, unknown>
    performanceRadar: Record<string, unknown>
  }> {
    try {
      console.log('🚀 ChartDataService: 批量獲取性能數據')
      const batchData = await UnifiedChartApiService.getPerformanceData()
      
      return {
        qoeTimeSeries: batchData.qoeMetrics || {},
        complexityAnalysis: batchData.complexityAnalysis || {},
        performanceRadar: {}
      }
    } catch (error) {
      console.warn('ChartDataService: 批量性能數據獲取失敗:', error)
      return {
        qoeTimeSeries: {},
        complexityAnalysis: {},
        performanceRadar: {}
      }
    }
  }

  /**
   * 批量獲取算法相關數據
   */
  static async fetchAlgorithmData(): Promise<{
    timeSyncPrecision: Record<string, unknown>
    algorithmAnalysis: Record<string, unknown>
    complexityAnalysis: Record<string, unknown>
  }> {
    try {
      console.log('🚀 ChartDataService: 批量獲取算法數據')
      const batchData = await UnifiedChartApiService.getAlgorithmData()
      
      return {
        timeSyncPrecision: batchData.timeSyncPrecision || {},
        algorithmAnalysis: batchData.algorithmAnalysis || {},
        complexityAnalysis: batchData.algorithmAnalysis || {}
      }
    } catch (error) {
      console.warn('ChartDataService: 批量算法數據獲取失敗:', error)
      return {
        timeSyncPrecision: {},
        algorithmAnalysis: {},
        complexityAnalysis: {}
      }
    }
  }

  /**
   * 批量獲取系統相關數據
   */
  static async fetchSystemData(): Promise<{
    systemResource: Record<string, unknown>
    healthStatus: Record<string, unknown>
    protocolStack: Record<string, unknown>
  }> {
    try {
      console.log('🚀 ChartDataService: 批量獲取系統數據')
      const batchData = await UnifiedChartApiService.getSystemArchitectureData()
      
      return {
        systemResource: batchData.systemResource || {},
        healthStatus: batchData.healthStatus || {},
        protocolStack: batchData.protocolStack || {}
      }
    } catch (error) {
      console.warn('ChartDataService: 批量系統數據獲取失敗:', error)
      return {
        systemResource: {},
        healthStatus: {},
        protocolStack: {}
      }
    }
  }

  // ==================== 新增：便利方法 ====================

  /**
   * 獲取基礎API數據（用於向後兼容）
   */
  static async fetchBasicApiData(): Promise<{
    coreSync: Record<string, unknown>
    healthStatus: Record<string, unknown>
  }> {
    try {
      console.log('🚀 ChartDataService: 獲取基礎API數據')
      const [coreSync, healthStatus] = await Promise.allSettled([
        UnifiedChartApiService.getCoreSync(),
        UnifiedChartApiService.getHealthStatus()
      ])
      
      return {
        coreSync: coreSync.status === 'fulfilled' ? coreSync.value : {},
        healthStatus: healthStatus.status === 'fulfilled' ? healthStatus.value : {}
      }
    } catch (error) {
      console.warn('ChartDataService: 基礎API數據獲取失敗:', error)
      return {
        coreSync: {},
        healthStatus: {}
      }
    }
  }

  /**
   * 檢查API服務可用性
   */
  static async checkApiAvailability(): Promise<boolean> {
    try {
      const healthData = await UnifiedChartApiService.getHealthStatus()
      return !!(healthData && Object.keys(healthData).length > 0)
    } catch (error) {
      console.warn('ChartDataService: API可用性檢查失敗:', error)
      return false
    }
  }
}