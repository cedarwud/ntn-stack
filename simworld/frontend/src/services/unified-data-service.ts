/**
 * 統一數據服務
 * 解決多個 Hook 重複調用相同 API 的問題
 * 提供全域數據快取和共享機制
 */

import { unifiedNetStackApi } from './unified-netstack-api'
import { satelliteCache } from '../utils/satellite-cache'

// 數據快取接口
interface DataCache<T> {
  data: T | null
  lastUpdate: number
  isLoading: boolean
  error?: string
}

// 數據來源狀態
export type DataSourceStatus = 'real' | 'calculated' | 'fallback' | 'loading' | 'error'

// 數據狀態接口
interface DataState<T> {
  data: T
  status: DataSourceStatus
  error?: string
  lastUpdate?: string
}

// API數據接口
interface ComponentData {
  availability?: number
  accuracy_ms?: number
  latency_ms?: number
  throughput_mbps?: number
  error_rate?: number
  speed?: number
  altitude?: number
  [key: string]: number | string | boolean | undefined
}

interface CoreSyncData {
  component_states?: Record<string, ComponentData>
  sync_performance?: {
    overall_accuracy_ms?: number
  }
}

interface SatelliteData {
  starlink?: {
    delay?: number
    period?: number
    altitude?: number
  }
  kuiper?: {
    delay?: number
    period?: number
    altitude?: number
  }
}

interface HealthStatusData {
  status?: string
  components?: Record<string, unknown>
  overall_health?: number
}

interface HandoverLatencyData {
  latency_metrics?: Record<string, number>
  response_time?: number
}

class UnifiedDataService {
  private static instance: UnifiedDataService
  
  // 數據快取
  private coreSync: DataCache<CoreSyncData> = {
    data: null,
    lastUpdate: 0,
    isLoading: false
  }
  
  private satelliteData: DataCache<SatelliteData> = {
    data: null,
    lastUpdate: 0,
    isLoading: false
  }
  
  private healthStatus: DataCache<HealthStatusData> = {
    data: null,
    lastUpdate: 0,
    isLoading: false
  }
  
  private handoverLatency: DataCache<HandoverLatencyData> = {
    data: null,
    lastUpdate: 0,
    isLoading: false
  }
  
  // 快取有效期 (30秒)
  private readonly CACHE_DURATION = 30 * 1000
  
  // 單例模式
  public static getInstance(): UnifiedDataService {
    if (!UnifiedDataService.instance) {
      UnifiedDataService.instance = new UnifiedDataService()
    }
    return UnifiedDataService.instance
  }
  
  // 檢查快取是否有效
  private isCacheValid(cache: DataCache<unknown>): boolean {
    return Date.now() - cache.lastUpdate < this.CACHE_DURATION
  }
  
  // 獲取 Core Sync 數據
  async getCoreSync(): Promise<DataState<CoreSyncData | null>> {
    if (this.isCacheValid(this.coreSync) && this.coreSync.data) {
      console.log('✅ Using cached Core Sync data')
      return {
        data: this.coreSync.data,
        status: 'real',
        lastUpdate: new Date(this.coreSync.lastUpdate).toISOString()
      }
    }
    
    if (this.coreSync.isLoading) {
      console.log('⏳ Core Sync request already in progress')
      // 等待正在進行的請求
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!this.coreSync.isLoading) {
            clearInterval(checkInterval)
            resolve({
              data: this.coreSync.data,
              status: this.coreSync.error ? 'error' : 'real',
              error: this.coreSync.error,
              lastUpdate: new Date(this.coreSync.lastUpdate).toISOString()
            })
          }
        }, 100)
      })
    }
    
    this.coreSync.isLoading = true
    
    try {
      console.log('🔄 Fetching fresh Core Sync data')
      const syncData = await unifiedNetStackApi.getCoreSync()
      
      this.coreSync = {
        data: syncData,
        lastUpdate: Date.now(),
        isLoading: false
      }
      
      console.log('✅ Core Sync data fetched and cached')
      return {
        data: syncData,
        status: 'real',
        lastUpdate: new Date().toISOString()
      }
    } catch (error) {
      console.warn('❌ Failed to fetch Core Sync data:', error)
      this.coreSync = {
        data: null,
        lastUpdate: Date.now(),
        isLoading: false,
        error: 'NetStack Core Sync API 連接失敗'
      }
      
      return {
        data: null,
        status: 'error',
        error: 'NetStack Core Sync API 連接失敗',
        lastUpdate: new Date().toISOString()
      }
    }
  }
  
  // 獲取衛星數據
  async getSatelliteData(): Promise<DataState<SatelliteData>> {
    if (this.isCacheValid(this.satelliteData) && this.satelliteData.data) {
      console.log('✅ Using cached Satellite data')
      return {
        data: this.satelliteData.data,
        status: 'real',
        lastUpdate: new Date(this.satelliteData.lastUpdate).toISOString()
      }
    }
    
    if (this.satelliteData.isLoading) {
      console.log('⏳ Satellite data request already in progress')
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!this.satelliteData.isLoading) {
            clearInterval(checkInterval)
            resolve({
              data: this.satelliteData.data || {},
              status: this.satelliteData.error ? 'fallback' : 'real',
              error: this.satelliteData.error,
              lastUpdate: new Date(this.satelliteData.lastUpdate).toISOString()
            })
          }
        }, 100)
      })
    }
    
    this.satelliteData.isLoading = true
    
    try {
      console.log('🔄 Fetching fresh Satellite data')
      let positions = null
      if (typeof satelliteCache.getSatellitePositions === 'function') {
        positions = await satelliteCache.getSatellitePositions()
      }
      
      if (positions?.starlink && positions?.kuiper) {
        const satelliteInfo = {
          starlink: {
            delay: positions.starlink.delay || 2.7,
            period: positions.starlink.period || 95.5,
            altitude: positions.starlink.altitude || 550
          },
          kuiper: {
            delay: positions.kuiper.delay || 3.2,
            period: positions.kuiper.period || 98.2,
            altitude: positions.kuiper.altitude || 630
          }
        }
        
        this.satelliteData = {
          data: satelliteInfo,
          lastUpdate: Date.now(),
          isLoading: false
        }
        
        console.log('✅ Satellite data fetched and cached')
        return {
          data: satelliteInfo,
          status: 'real',
          lastUpdate: new Date().toISOString()
        }
      } else {
        throw new Error('Incomplete satellite data')
      }
    } catch (error) {
      console.warn('❌ Failed to fetch Satellite data:', error)
      
      const fallbackData = {
        starlink: { delay: 2.7, period: 95.5, altitude: 550 },
        kuiper: { delay: 3.2, period: 98.2, altitude: 630 }
      }
      
      this.satelliteData = {
        data: fallbackData,
        lastUpdate: Date.now(),
        isLoading: false,
        error: '衛星數據 API 無法連接，使用預設參數'
      }
      
      return {
        data: fallbackData,
        status: 'fallback',
        error: '衛星數據 API 無法連接，使用預設參數',
        lastUpdate: new Date().toISOString()
      }
    }
  }
  
  // 獲取健康狀態數據
  async getHealthStatus(): Promise<DataState<HealthStatusData | null>> {
    if (this.isCacheValid(this.healthStatus) && this.healthStatus.data) {
      console.log('✅ Using cached Health Status data')
      return {
        data: this.healthStatus.data,
        status: 'real',
        lastUpdate: new Date(this.healthStatus.lastUpdate).toISOString()
      }
    }
    
    if (this.healthStatus.isLoading) {
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!this.healthStatus.isLoading) {
            clearInterval(checkInterval)
            resolve({
              data: this.healthStatus.data,
              status: this.healthStatus.error ? 'error' : 'real',
              error: this.healthStatus.error,
              lastUpdate: new Date(this.healthStatus.lastUpdate).toISOString()
            })
          }
        }, 100)
      })
    }
    
    this.healthStatus.isLoading = true
    
    try {
      console.log('🔄 Fetching fresh Health Status data')
      const healthData = await unifiedNetStackApi.getHealthStatus()
      
      this.healthStatus = {
        data: healthData,
        lastUpdate: Date.now(),
        isLoading: false
      }
      
      console.log('✅ Health Status data fetched and cached')
      return {
        data: healthData,
        status: 'real',
        lastUpdate: new Date().toISOString()
      }
    } catch (error) {
      console.warn('❌ Failed to fetch Health Status data:', error)
      this.healthStatus = {
        data: null,
        lastUpdate: Date.now(),
        isLoading: false,
        error: 'NetStack Health Status API 連接失敗'
      }
      
      return {
        data: null,
        status: 'error',
        error: 'NetStack Health Status API 連接失敗',
        lastUpdate: new Date().toISOString()
      }
    }
  }
  
  // 獲取換手延遲數據
  async getHandoverLatencyMetrics(): Promise<DataState<HandoverLatencyData | null>> {
    if (this.isCacheValid(this.handoverLatency) && this.handoverLatency.data) {
      console.log('✅ Using cached Handover Latency data')
      return {
        data: this.handoverLatency.data,
        status: 'real',
        lastUpdate: new Date(this.handoverLatency.lastUpdate).toISOString()
      }
    }
    
    if (this.handoverLatency.isLoading) {
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!this.handoverLatency.isLoading) {
            clearInterval(checkInterval)
            resolve({
              data: this.handoverLatency.data,
              status: this.handoverLatency.error ? 'error' : 'real',
              error: this.handoverLatency.error,
              lastUpdate: new Date(this.handoverLatency.lastUpdate).toISOString()
            })
          }
        }, 100)
      })
    }
    
    this.handoverLatency.isLoading = true
    
    try {
      console.log('🔄 Fetching fresh Handover Latency data')
      const latencyData = await unifiedNetStackApi.getHandoverLatencyMetrics()
      
      this.handoverLatency = {
        data: latencyData,
        lastUpdate: Date.now(),
        isLoading: false
      }
      
      console.log('✅ Handover Latency data fetched and cached')
      return {
        data: latencyData,
        status: 'real',
        lastUpdate: new Date().toISOString()
      }
    } catch (error) {
      console.warn('❌ Failed to fetch Handover Latency data:', error)
      this.handoverLatency = {
        data: null,
        lastUpdate: Date.now(),
        isLoading: false,
        error: 'NetStack Handover Latency API 連接失敗'
      }
      
      return {
        data: null,
        status: 'error',
        error: 'NetStack Handover Latency API 連接失敗',
        lastUpdate: new Date().toISOString()
      }
    }
  }
  
  // 強制刷新所有快取
  invalidateAllCache(): void {
    console.log('🔄 Invalidating all cache')
    this.coreSync.lastUpdate = 0
    this.satelliteData.lastUpdate = 0
    this.healthStatus.lastUpdate = 0
    this.handoverLatency.lastUpdate = 0
  }
  
  // 獲取快取狀態
  getCacheStatus() {
    return {
      coreSync: {
        isValid: this.isCacheValid(this.coreSync),
        lastUpdate: this.coreSync.lastUpdate,
        hasData: !!this.coreSync.data
      },
      satelliteData: {
        isValid: this.isCacheValid(this.satelliteData),
        lastUpdate: this.satelliteData.lastUpdate,
        hasData: !!this.satelliteData.data
      },
      healthStatus: {
        isValid: this.isCacheValid(this.healthStatus),
        lastUpdate: this.healthStatus.lastUpdate,
        hasData: !!this.healthStatus.data
      },
      handoverLatency: {
        isValid: this.isCacheValid(this.handoverLatency),
        lastUpdate: this.handoverLatency.lastUpdate,
        hasData: !!this.handoverLatency.data
      }
    }
  }
}

// 導出單例實例
export const unifiedDataService = UnifiedDataService.getInstance()