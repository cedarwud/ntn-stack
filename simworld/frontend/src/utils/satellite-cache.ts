/**
 * 衛星數據快取工具
 * 用於緩解慢速衛星API調用的性能問題
 */

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