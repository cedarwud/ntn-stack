/**
 * Chart Analysis Dashboard Data Service
 * 將所有 API 獲取邏輯從主組件中分離出來
 */

import { netStackApi } from '../../../../../services/netstack-api'
import { satelliteCache } from '../../../../../utils/satellite-cache'

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

export class ChartDataService {
  /**
   * 獲取 UAV 位置數據
   */
  static async fetchRealUAVData(): Promise<SatellitePosition[]> {
    try {
      const response = await fetch('http://localhost:8888/api/v1/uav/positions')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      return Array.isArray(data) ? data : []
    } catch (error) {
      console.warn('Failed to fetch UAV data:', error)
      return []
    }
  }

  /**
   * 獲取換手測試數據
   */
  static async fetchHandoverTestData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/test-data')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch handover test data:', error)
      return {}
    }
  }

  /**
   * 獲取六種場景比較數據
   */
  static async fetchSixScenarioData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/six-scenario-comparison')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch six scenario data:', error)
      return {}
    }
  }

  /**
   * 獲取 Celestrak TLE 軌道數據
   */
  static async fetchCelestrakTLEData(): Promise<SatelliteData[]> {
    try {
      const cachedData = satelliteCache.getCachedData()
      if (cachedData && cachedData.length > 0) {
        console.log('Using cached TLE data from satelliteCache')
        return cachedData
      }

      const response = await fetch(
        'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json'
      )
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      const processedData = Array.isArray(data) ? data.slice(0, 100) : []
      
      if (processedData.length > 0) {
        satelliteCache.setCachedData(processedData)
      }
      
      return processedData
    } catch (error) {
      console.warn('Failed to fetch Celestrak TLE data:', error)
      return []
    }
  }

  /**
   * 獲取策略效果數據
   */
  static async fetchStrategyEffectData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/strategy-effect-comparison')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch strategy effect data:', error)
      return {}
    }
  }

  /**
   * 獲取複雜度分析數據
   */
  static async fetchComplexityAnalysisData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/complexity-analysis')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch complexity analysis data:', error)
      return {}
    }
  }

  /**
   * 獲取換手失敗率數據
   */
  static async fetchHandoverFailureRateData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/failure-rate-analysis')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch handover failure rate data:', error)
      return {}
    }
  }

  /**
   * 獲取系統資源數據
   */
  static async fetchSystemResourceData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/system-resource-allocation')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch system resource data:', error)
      return {}
    }
  }

  /**
   * 獲取時間同步精度數據
   */
  static async fetchTimeSyncPrecisionData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/time-sync-precision')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch time sync precision data:', error)
      return {}
    }
  }

  /**
   * 獲取性能雷達數據
   */
  static async fetchPerformanceRadarData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/performance-radar')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch performance radar data:', error)
      return {}
    }
  }

  /**
   * 獲取協議堆疊延遲數據
   */
  static async fetchProtocolStackDelayData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/protocol-stack-delay')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch protocol stack delay data:', error)
      return {}
    }
  }

  /**
   * 獲取異常處理數據
   */
  static async fetchExceptionHandlingData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/exception-handling-statistics')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch exception handling data:', error)
      return {}
    }
  }

  /**
   * 獲取 QoE 時間序列數據
   */
  static async fetchQoETimeSeriesData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/qoe-timeseries')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch QoE time series data:', error)
      return {}
    }
  }

  /**
   * 獲取全球覆蓋範圍數據
   */
  static async fetchGlobalCoverageData(): Promise<Record<string, unknown>> {
    try {
      const response = await netStackApi.get('/handover/global-coverage')
      return response.data || {}
    } catch (error) {
      console.warn('Failed to fetch global coverage data:', error)
      return {}
    }
  }
}