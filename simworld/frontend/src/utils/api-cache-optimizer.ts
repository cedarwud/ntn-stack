/**
 * API 緩存優化器
 * 專為 LEO 衛星換手研究提供智能緩存策略
 */

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
  accessCount: number
  lastAccessed: number
}

interface CacheConfig {
  maxSize: number
  defaultTTL: number
  enableCompression: boolean
}

export class ApiCacheOptimizer {
  private cache = new Map<string, CacheEntry<any>>()
  private config: CacheConfig
  
  constructor(config: Partial<CacheConfig> = {}) {
    this.config = {
      maxSize: 100, // 最大緩存條目數
      defaultTTL: 30000, // 預設 TTL 30秒
      enableCompression: false, // 簡化實現，不啟用壓縮
      ...config
    }
  }

  /**
   * 智能 TTL 策略 - 根據數據類型設置不同緩存時間
   */
  private getTTLForEndpoint(endpoint: string): number {
    // 衛星軌道數據 - 較長緩存（軌道變化慢）
    if (endpoint.includes('/satellite') || endpoint.includes('/orbit')) {
      return 60000 // 1分鐘
    }
    
    // 設備狀態 - 中等緩存
    if (endpoint.includes('/device') || endpoint.includes('/status')) {
      return 30000 // 30秒
    }
    
    // 換手決策 - 短緩存（需要即時性）
    if (endpoint.includes('/handover') || endpoint.includes('/decision')) {
      return 10000 // 10秒
    }
    
    // 健康檢查 - 很短緩存
    if (endpoint.includes('/health')) {
      return 5000 // 5秒
    }
    
    return this.config.defaultTTL
  }

  /**
   * 生成緩存鍵 - 包含參數信息
   */
  private generateCacheKey(endpoint: string, params?: Record<string, any>): string {
    const paramString = params ? JSON.stringify(params) : ''
    return `${endpoint}:${paramString}`
  }

  /**
   * 檢查緩存是否有效
   */
  private isValidCache<T>(entry: CacheEntry<T>): boolean {
    const now = Date.now()
    return (now - entry.timestamp) < entry.ttl
  }

  /**
   * LRU 清理策略
   */
  private evictLRU(): void {
    if (this.cache.size <= this.config.maxSize) return
    
    // 找到最久未訪問的條目
    let oldestKey = ''
    let oldestTime = Date.now()
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < oldestTime) {
        oldestTime = entry.lastAccessed
        oldestKey = key
      }
    }
    
    if (oldestKey) {
      this.cache.delete(oldestKey)
    }
  }

  /**
   * 設置緩存
   */
  set<T>(endpoint: string, data: T, params?: Record<string, any>, customTTL?: number): void {
    const key = this.generateCacheKey(endpoint, params)
    const ttl = customTTL || this.getTTLForEndpoint(endpoint)
    const now = Date.now()
    
    this.cache.set(key, {
      data,
      timestamp: now,
      ttl,
      accessCount: 0,
      lastAccessed: now
    })
    
    this.evictLRU()
  }

  /**
   * 獲取緩存
   */
  get<T>(endpoint: string, params?: Record<string, any>): T | null {
    const key = this.generateCacheKey(endpoint, params)
    const entry = this.cache.get(key) as CacheEntry<T> | undefined
    
    if (!entry || !this.isValidCache(entry)) {
      if (entry) this.cache.delete(key)
      return null
    }
    
    // 更新訪問統計
    entry.accessCount++
    entry.lastAccessed = Date.now()
    
    return entry.data
  }

  /**
   * 檢查是否有緩存
   */
  has(endpoint: string, params?: Record<string, any>): boolean {
    const key = this.generateCacheKey(endpoint, params)
    const entry = this.cache.get(key)
    return entry ? this.isValidCache(entry) : false
  }

  /**
   * 清除特定前綴的緩存
   */
  clearByPrefix(prefix: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * 清除過期緩存
   */
  clearExpired(): void {
    for (const [key, entry] of this.cache.entries()) {
      if (!this.isValidCache(entry)) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * 清除所有緩存
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * 預熱緩存 - 批量載入常用數據
   */
  async preloadCache(
    preloadRequests: Array<{
      endpoint: string
      params?: Record<string, any>
      fetcher: () => Promise<any>
    }>
  ): Promise<void> {
    const promises = preloadRequests.map(async ({ endpoint, params, fetcher }) => {
      try {
        const data = await fetcher()
        this.set(endpoint, data, params)
      } catch (error) {
        console.warn(`緩存預熱失敗: ${endpoint}`, error)
      }
    })
    
    await Promise.allSettled(promises)
  }

  /**
   * 獲取緩存統計
   */
  getStats(): {
    totalEntries: number
    hitRate: number
    memoryUsage: number
    topEndpoints: Array<{ endpoint: string; accessCount: number }>
  } {
    const entries = Array.from(this.cache.entries())
    const totalAccess = entries.reduce((sum, [, entry]) => sum + entry.accessCount, 0)
    
    // 計算熱門端點
    const endpointStats = new Map<string, number>()
    for (const [key, entry] of entries) {
      const endpoint = key.split(':')[0]
      endpointStats.set(endpoint, (endpointStats.get(endpoint) || 0) + entry.accessCount)
    }
    
    const topEndpoints = Array.from(endpointStats.entries())
      .map(([endpoint, accessCount]) => ({ endpoint, accessCount }))
      .sort((a, b) => b.accessCount - a.accessCount)
      .slice(0, 5)
    
    return {
      totalEntries: this.cache.size,
      hitRate: totalAccess > 0 ? entries.length / totalAccess : 0,
      memoryUsage: JSON.stringify([...this.cache.entries()]).length, // 粗略估算
      topEndpoints
    }
  }
}

/**
 * 增強的 API 緩存裝飾器
 */
export function withCache<T>(
  cacheOptimizer: ApiCacheOptimizer,
  endpoint: string,
  customTTL?: number
) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value
    
    descriptor.value = async function (...args: any[]) {
      const params = args[0]
      
      // 先檢查緩存
      const cached = cacheOptimizer.get<T>(endpoint, params)
      if (cached !== null) {
        return cached
      }
      
      // 執行原方法
      const result = await originalMethod.apply(this, args)
      
      // 存入緩存
      cacheOptimizer.set(endpoint, result, params, customTTL)
      
      return result
    }
    
    return descriptor
  }
}

// 全局緩存實例
export const apiCacheOptimizer = new ApiCacheOptimizer({
  maxSize: 200, // 增加緩存大小以支持更多衛星數據
  defaultTTL: 30000,
  enableCompression: false
})

// 衛星數據專用緩存實例
export const satelliteCacheOptimizer = new ApiCacheOptimizer({
  maxSize: 50, // 衛星數據相對穩定，不需要太多條目
  defaultTTL: 60000, // 較長的 TTL
  enableCompression: false
})