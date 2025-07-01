/**
 * 統一的分析圖表API服務層
 * 集中管理所有API調用，避免Hook中的直接API調用
 * 階段三重構：關注點分離
 */

import { netStackApi } from '../../../../../services/netstack-api'
import { satelliteCache } from '../../../../../utils/satellite-cache'

// ==================== 接口定義 ====================

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

export interface QoEMetricsData {
  stalling_time?: number[]
  rtt?: number[]
  packet_loss?: number[]
  throughput?: number[]
  timestamps?: string[]
}

export interface ComplexityAnalysisData {
  time_complexity?: unknown[]
  space_complexity?: unknown[]
  scalability_metrics?: unknown[]
}

export interface AlgorithmData {
  beamforming?: unknown[]
  handover_prediction?: unknown[]
  qos_optimization?: unknown[]
}

// ==================== 統一錯誤處理 ====================

class ApiError extends Error {
  constructor(
    message: string,
    public endpoint: string,
    public statusCode?: number,
    public originalError?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// ==================== 統一API服務類 ====================

export class UnifiedChartApiService {
  
  // ==================== 基礎API方法 ====================
  
  /**
   * 統一的NetStack API調用方法
   */
  private static async callNetStackApi(endpoint: string): Promise<Record<string, unknown>> {
    try {
      console.log(`📡 調用NetStack API: ${endpoint}`)
      const response = await netStackApi.get(endpoint)
      return response.data || {}
    } catch (error) {
      console.warn(`⚠️ NetStack API調用失敗 ${endpoint}:`, error)
      throw new ApiError(
        `NetStack API調用失敗: ${endpoint}`,
        endpoint,
        undefined,
        error
      )
    }
  }

  /**
   * 統一的直接fetch調用方法
   */
  private static async callDirectFetch(
    url: string,
    options: RequestInit = {}
  ): Promise<Record<string, unknown>> {
    try {
      console.log(`🌐 直接API調用: ${url}`)
      const response = await fetch(url, {
        timeout: 10000, // 10秒超時
        ...options
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      return data || {}
    } catch (error) {
      console.warn(`⚠️ 直接API調用失敗 ${url}:`, error)
      throw new ApiError(
        `直接API調用失敗: ${url}`,
        url,
        undefined,
        error
      )
    }
  }

  // ==================== 基礎數據獲取方法 ====================

  /**
   * 獲取核心同步數據
   */
  static async getCoreSync(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/api/v1/core/sync')
  }

  /**
   * 獲取健康狀態
   */
  static async getHealthStatus(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/api/v1/health')
  }

  /**
   * 獲取換手延遲指標
   */
  static async getHandoverLatencyMetrics(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/api/v1/handover/latency-metrics')
  }

  // ==================== 性能監控相關API ====================

  /**
   * 獲取QoE時間序列數據 (POST方法)
   */
  static async getQoETimeSeries(): Promise<QoEMetricsData> {
    try {
      const data = await this.callDirectFetch('/api/v1/handover/qoe-timeseries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      })
      
      return {
        stalling_time: data.stalling_time as number[] || [],
        rtt: data.rtt as number[] || [],
        packet_loss: data.packet_loss as number[] || [],
        throughput: data.throughput as number[] || [],
        timestamps: data.timestamps as string[] || []
      }
    } catch (error) {
      console.warn('QoE時間序列數據獲取失敗，使用預設數據:', error)
      return {
        stalling_time: [],
        rtt: [],
        packet_loss: [],
        throughput: [],
        timestamps: []
      }
    }
  }

  /**
   * 獲取複雜度分析數據
   */
  static async getComplexityAnalysis(): Promise<ComplexityAnalysisData> {
    try {
      const data = await this.callDirectFetch('/api/v1/handover/complexity-analysis')
      
      return {
        time_complexity: data.time_complexity as unknown[] || [],
        space_complexity: data.space_complexity as unknown[] || [],
        scalability_metrics: data.scalability_metrics as unknown[] || []
      }
    } catch (error) {
      console.warn('複雜度分析數據獲取失敗，使用預設數據:', error)
      return {
        time_complexity: [],
        space_complexity: [],
        scalability_metrics: []
      }
    }
  }

  // ==================== 算法分析相關API ====================

  /**
   * 獲取時間同步精度數據
   */
  static async getTimeSyncPrecision(): Promise<Record<string, unknown>> {
    try {
      return await this.callDirectFetch('/api/v1/handover/time-sync-precision')
    } catch (error) {
      console.warn('時間同步精度數據獲取失敗，使用NetStack API替代:', error)
      return this.callNetStackApi('/handover/time-sync-precision')
    }
  }

  /**
   * 獲取算法分析數據
   */
  static async getAlgorithmAnalysis(): Promise<AlgorithmData> {
    try {
      const data = await this.getComplexityAnalysis()
      
      return {
        beamforming: data.time_complexity || [],
        handover_prediction: data.space_complexity || [],
        qos_optimization: data.scalability_metrics || []
      }
    } catch (error) {
      console.warn('算法分析數據獲取失敗，使用預設數據:', error)
      return {
        beamforming: [],
        handover_prediction: [],
        qos_optimization: []
      }
    }
  }

  // ==================== UAV和衛星數據 ====================

  /**
   * 獲取UAV位置數據
   */
  static async getUAVPositions(): Promise<SatellitePosition[]> {
    try {
      const data = await this.callDirectFetch('http://localhost:8888/api/v1/uav/positions')
      return Array.isArray(data) ? data as SatellitePosition[] : []
    } catch (error) {
      console.warn('UAV位置數據獲取失敗:', error)
      return []
    }
  }

  /**
   * 獲取Celestrak TLE軌道數據 (帶快取)
   */
  static async getCelestrakTLEData(): Promise<SatelliteData[]> {
    try {
      // 檢查快取
      const cachedData = satelliteCache.getCachedData()
      if (cachedData && cachedData.length > 0) {
        console.log('🗃️ 使用快取的TLE數據')
        return cachedData as SatelliteData[]
      }

      // 獲取新數據
      const data = await this.callDirectFetch(
        'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json'
      )
      
      const processedData = Array.isArray(data) ? data.slice(0, 100) as SatelliteData[] : []
      
      if (processedData.length > 0) {
        satelliteCache.setCachedData(processedData)
        console.log('💾 TLE數據已快取')
      }
      
      return processedData
    } catch (error) {
      console.warn('Celestrak TLE數據獲取失敗:', error)
      return []
    }
  }

  // ==================== 換手相關數據 ====================

  /**
   * 獲取換手測試數據
   */
  static async getHandoverTestData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/test-data')
  }

  /**
   * 獲取六種場景比較數據
   */
  static async getSixScenarioData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/six-scenario-comparison')
  }

  /**
   * 獲取策略效果數據
   */
  static async getStrategyEffectData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/strategy-effect-comparison')
  }

  /**
   * 獲取換手失敗率數據
   */
  static async getHandoverFailureRateData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/failure-rate-analysis')
  }

  /**
   * 獲取系統資源數據
   */
  static async getSystemResourceData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/system-resource-allocation')
  }

  /**
   * 獲取性能雷達數據
   */
  static async getPerformanceRadarData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/performance-radar')
  }

  /**
   * 獲取協議堆疊延遲數據
   */
  static async getProtocolStackDelayData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/protocol-stack-delay')
  }

  /**
   * 獲取異常處理數據
   */
  static async getExceptionHandlingData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/exception-handling-statistics')
  }

  /**
   * 獲取全球覆蓋範圍數據
   */
  static async getGlobalCoverageData(): Promise<Record<string, unknown>> {
    return this.callNetStackApi('/handover/global-coverage')
  }

  // ==================== 批量數據獲取 ====================

  /**
   * 批量獲取性能監控數據
   */
  static async getPerformanceData() {
    try {
      const [qoeData, complexityData, coreSync, healthStatus] = await Promise.allSettled([
        this.getQoETimeSeries(),
        this.getComplexityAnalysis(),
        this.getCoreSync(),
        this.getHealthStatus()
      ])

      return {
        qoeMetrics: qoeData.status === 'fulfilled' ? qoeData.value : {},
        complexityAnalysis: complexityData.status === 'fulfilled' ? complexityData.value : {},
        coreSync: coreSync.status === 'fulfilled' ? coreSync.value : {},
        healthStatus: healthStatus.status === 'fulfilled' ? healthStatus.value : {}
      }
    } catch (error) {
      console.warn('批量性能數據獲取部分失敗:', error)
      throw error
    }
  }

  /**
   * 批量獲取算法分析數據
   */
  static async getAlgorithmData() {
    try {
      const [timeSyncData, algorithmAnalysis, coreSync, latencyMetrics] = await Promise.allSettled([
        this.getTimeSyncPrecision(),
        this.getAlgorithmAnalysis(),
        this.getCoreSync(),
        this.getHandoverLatencyMetrics()
      ])

      return {
        timeSyncPrecision: timeSyncData.status === 'fulfilled' ? timeSyncData.value : {},
        algorithmAnalysis: algorithmAnalysis.status === 'fulfilled' ? algorithmAnalysis.value : {},
        coreSync: coreSync.status === 'fulfilled' ? coreSync.value : {},
        latencyMetrics: latencyMetrics.status === 'fulfilled' ? latencyMetrics.value : {}
      }
    } catch (error) {
      console.warn('批量算法數據獲取部分失敗:', error)
      throw error
    }
  }

  /**
   * 批量獲取系統架構數據
   */
  static async getSystemArchitectureData() {
    try {
      const [coreSync, healthStatus, resourceData, protocolData] = await Promise.allSettled([
        this.getCoreSync(),
        this.getHealthStatus(),
        this.getSystemResourceData(),
        this.getProtocolStackDelayData()
      ])

      return {
        coreSync: coreSync.status === 'fulfilled' ? coreSync.value : {},
        healthStatus: healthStatus.status === 'fulfilled' ? healthStatus.value : {},
        systemResource: resourceData.status === 'fulfilled' ? resourceData.value : {},
        protocolStack: protocolData.status === 'fulfilled' ? protocolData.value : {}
      }
    } catch (error) {
      console.warn('批量系統架構數據獲取部分失敗:', error)
      throw error
    }
  }
}

// ==================== 預設導出 ====================

export default UnifiedChartApiService