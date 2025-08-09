/**
 * 衛星數據快取工具
 * 用於緩解慢速衛星API調用的性能問題
 */

import { netstackFetch } from '../config/api-config';

interface CachedData<T> {
  data: T
  timestamp: number
  expiry: number
}

class SatelliteCacheManager {
  private cache: Map<string, CachedData<unknown>> = new Map()
  private readonly DEFAULT_CACHE_TIME = 60 * 1000 // 60秒

  /**
   * 獲取快取數據
   */
  get<T>(key: string): T | null {
    const cached = this.cache.get(key)
    
    if (!cached) {
      return null
    }
    
    // 檢查是否過期
    if (Date.now() > cached.expiry) {
      this.cache.delete(key)
      return null
    }
    
    console.log(`📦 使用快取數據: ${key}`)
    return cached.data as T
  }

  /**
   * 設置快取數據
   */
  set<T>(key: string, data: T, cacheTimeMs: number = this.DEFAULT_CACHE_TIME): void {
    const expiry = Date.now() + cacheTimeMs
    
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expiry
    })
    
    console.log(`💾 快取數據: ${key}，過期時間: ${new Date(expiry).toLocaleTimeString()}`)
  }

  /**
   * 清除特定快取
   */
  delete(key: string): void {
    this.cache.delete(key)
  }

  /**
   * 清除所有快取
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * 清除過期快取
   */
  cleanup(): void {
    const now = Date.now()
    const keysToDelete: string[] = []
    
    this.cache.forEach((cached, key) => {
      if (now > cached.expiry) {
        keysToDelete.push(key)
      }
    })
    
    keysToDelete.forEach(key => this.cache.delete(key))
    
    if (keysToDelete.length > 0) {
      console.log(`🧹 清理了 ${keysToDelete.length} 個過期快取`)
    }
  }

  /**
   * 獲取快取統計信息
   */
  getStats() {
    const now = Date.now()
    let validEntries = 0
    let expiredEntries = 0
    
    this.cache.forEach(cached => {
      if (now > cached.expiry) {
        expiredEntries++
      } else {
        validEntries++
      }
    })
    
    return {
      total: this.cache.size,
      valid: validEntries,
      expired: expiredEntries
    }
  }

  /**
   * 創建帶快取的API調用包裝器
   */
  async withCache<T>(
    key: string,
    apiCall: () => Promise<T>,
    cacheTimeMs: number = this.DEFAULT_CACHE_TIME
  ): Promise<T> {
    // 先檢查快取
    const cached = this.get<T>(key)
    if (cached !== null) {
      return cached
    }

    // 執行API調用
    console.log(`🌐 執行API調用: ${key}`)
    const startTime = Date.now()
    
    try {
      const data = await apiCall()
      const duration = Date.now() - startTime
      
      // 儲存到快取
      this.set(key, data, cacheTimeMs)
      
      console.log(`✅ API調用完成: ${key} (${duration}ms)`)
      return data
    } catch (error) {
      const duration = Date.now() - startTime
      console.error(`❌ API調用失敗: ${key} (${duration}ms)`, error)
      throw error
    }
  }

  /**
   * 獲取衛星位置信息（包含 Starlink 和 Kuiper 數據）
   */
  async getSatellitePositions(): Promise<{
    starlink: { delay: number; period: number; altitude: number }
    kuiper: { delay: number; period: number; altitude: number }
  }> {
    const cacheKey = 'satellite_positions'
    
    return this.withCache(cacheKey, async () => {
      try {
        // 獲取 Starlink 衛星數據
        const starlinkResponse = await netstackFetch('/api/v1/satellite-simple/visible_satellites?constellation=starlink&count=10&global_view=true')
        const starlinkData = await starlinkResponse.json()
        
        // 獲取 Kuiper 衛星數據（如果沒有 Kuiper 數據，使用預設值）
        let kuiperData = { satellites: [] }
        try {
          const kuiperResponse = await netstackFetch('/api/v1/satellite-simple/visible_satellites?constellation=kuiper&count=10&global_view=true')
          kuiperData = await kuiperResponse.json()
        } catch (_error) {
          console.warn('Kuiper 衛星數據不可用，使用預設值')
        }

        // 計算 Starlink 平均數據
        const starlinkSatellites = starlinkData.satellites || []
        const starlinkAvgAltitude = starlinkSatellites.length > 0 
          ? starlinkSatellites.reduce((sum: number, sat: { orbit_altitude_km?: number }) => sum + (sat.orbit_altitude_km || 550), 0) / starlinkSatellites.length
          : 550

        // 計算延遲（基於高度，高度越高延遲越大）
        const starlinkDelay = Math.round((starlinkAvgAltitude / 550) * 2.7 * 10) / 10
        const starlinkPeriod = Math.round((Math.sqrt(Math.pow(starlinkAvgAltitude + 6371, 3) / 398600.4418) * 2 * Math.PI / 60) * 10) / 10

        // Kuiper 數據（如果有真實數據則使用，否則使用預設值）
        const kuiperSatellites = kuiperData.satellites || []
        const kuiperAvgAltitude = kuiperSatellites.length > 0
          ? kuiperSatellites.reduce((sum: number, sat: { orbit_altitude_km?: number }) => sum + (sat.orbit_altitude_km || 630), 0) / kuiperSatellites.length
          : 630

        const kuiperDelay = Math.round((kuiperAvgAltitude / 630) * 3.2 * 10) / 10
        const kuiperPeriod = Math.round((Math.sqrt(Math.pow(kuiperAvgAltitude + 6371, 3) / 398600.4418) * 2 * Math.PI / 60) * 10) / 10

        return {
          starlink: {
            delay: starlinkDelay,
            period: starlinkPeriod,
            altitude: Math.round(starlinkAvgAltitude)
          },
          kuiper: {
            delay: kuiperDelay,
            period: kuiperPeriod,
            altitude: Math.round(kuiperAvgAltitude)
          }
        }
      } catch (error) {
        console.error('Failed to fetch satellite positions:', error)
        // 回退到預設值
        return {
          starlink: { delay: 2.7, period: 95.5, altitude: 550 },
          kuiper: { delay: 3.2, period: 98.2, altitude: 630 }
        }
      }
    }, 5 * 60 * 1000) // 快取 5 分鐘
  }
}

// 創建全域快取實例
export const satelliteCache = new SatelliteCacheManager()

// 自動清理過期快取（每5分鐘）
setInterval(() => {
  satelliteCache.cleanup()
}, 5 * 60 * 1000)

// 導出類型
export type { CachedData }
export { SatelliteCacheManager }