/**
 * API性能監控工具
 * 用於監控和優化API調用性能
 */

interface APICallMetrics {
  endpoint: string
  duration: number
  timestamp: number
  success: boolean
  cached?: boolean
}

class APIPerformanceMonitor {
  private metrics: APICallMetrics[] = []
  private readonly MAX_METRICS = 100 // 最多保存100個指標
  private readonly SLOW_THRESHOLD = 2000 // 慢查詢閾值：2秒

  /**
   * 記錄API調用
   */
  recordCall(endpoint: string, duration: number, success: boolean, cached: boolean = false) {
    const metric: APICallMetrics = {
      endpoint,
      duration,
      timestamp: Date.now(),
      success,
      cached
    }

    this.metrics.push(metric)

    // 限制記錄數量
    if (this.metrics.length > this.MAX_METRICS) {
      this.metrics.shift()
    }

    // 慢查詢警告
    if (duration > this.SLOW_THRESHOLD && !cached) {
      console.warn(`🐌 慢查詢警告: ${endpoint} 耗時 ${duration.toFixed(1)}ms`)
      
      // 提供優化建議
      this.provideTuningAdvice(endpoint, duration)
    }

    // 快取命中記錄
    if (cached) {
      console.log(`⚡ 快取命中: ${endpoint} (${duration.toFixed(1)}ms)`)
    }
  }

  /**
   * 提供調優建議
   */
  private provideTuningAdvice(endpoint: string, _duration: number) {
     
    if (endpoint.includes('visible_satellites')) {
      console.log(`💡 建議: 
        1. 減少請求的衛星數量 (當前可能過多)
        2. 增加快取時間 (衛星位置變化緩慢)
        3. 考慮分頁或延遲加載
        4. 使用更精確的篩選條件`)
    } else if (endpoint.includes('handover')) {
      console.log(`💡 建議:
        1. 使用批次處理
        2. 優化查詢參數
        3. 考慮背景預取`)
    } else {
      console.log(`💡 建議: 考慮添加快取、減少數據量或優化查詢`)
    }
  }

  /**
   * 獲取性能統計
   */
  getStats() {
    const now = Date.now()
     
     
    const recentMetrics = this.metrics.filter(m => now - m.timestamp < 300000) // 最近5分鐘

    if (recentMetrics.length === 0) {
      return null
    }

    const total = recentMetrics.length
    const successful = recentMetrics.filter(m => m.success).length
    const cached = recentMetrics.filter(m => m.cached).length
    const slow = recentMetrics.filter(m => m.duration > this.SLOW_THRESHOLD).length
    
    const durations = recentMetrics.map(m => m.duration)
    const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length
    const maxDuration = Math.max(...durations)
    const minDuration = Math.min(...durations)

    return {
      total,
      successRate: (successful / total) * 100,
      cacheHitRate: (cached / total) * 100,
      slowCallRate: (slow / total) * 100,
      avgDuration: Math.round(avgDuration),
      maxDuration: Math.round(maxDuration),
      minDuration: Math.round(minDuration),
      timeWindow: '5分鐘'
    }
  }

  /**
   * 獲取端點性能排名
   */
  getEndpointRanking() {
    const endpointStats = new Map<string, { total: number, avgDuration: number, slowCount: number }>()

    this.metrics.forEach(metric => {
      const current = endpointStats.get(metric.endpoint) || { total: 0, avgDuration: 0, slowCount: 0 }
      current.total++
      current.avgDuration = ((current.avgDuration * (current.total - 1)) + metric.duration) / current.total
      if (metric.duration > this.SLOW_THRESHOLD) {
        current.slowCount++
      }
      endpointStats.set(metric.endpoint, current)
    })

    return Array.from(endpointStats.entries())
      .map(([endpoint, stats]) => ({
        endpoint,
        ...stats,
        avgDuration: Math.round(stats.avgDuration),
        slowRate: (stats.slowCount / stats.total) * 100
      }))
      .sort((a, b) => b.avgDuration - a.avgDuration) // 按平均耗時排序
  }

  /**
   * 清理舊指標
   */
  cleanup() {
    const cutoff = Date.now() - 3600000 // 保留1小時內的數據
    this.metrics = this.metrics.filter(m => m.timestamp > cutoff)
  }

  /**
   * 包裝API調用以自動監控
   */
  async monitor<T>(
    endpoint: string,
    apiCall: () => Promise<T>,
    cached: boolean = false
  ): Promise<T> {
    const startTime = Date.now()
    
    try {
      const result = await apiCall()
      const duration = Date.now() - startTime
      this.recordCall(endpoint, duration, true, cached)
      return result
    } catch (error) {
      const duration = Date.now() - startTime
      this.recordCall(endpoint, duration, false, cached)
      throw error
    }
  }

  /**
   * 列印性能報告
   */
  printReport() {
    const stats = this.getStats()
    if (!stats) {
      console.log('📊 暫無API調用數據')
      return
    }

    console.log(`📊 API性能報告 (${stats.timeWindow}):`)
    console.log(`   總調用: ${stats.total}`)
    console.log(`   成功率: ${stats.successRate.toFixed(1)}%`)
    console.log(`   快取命中率: ${stats.cacheHitRate.toFixed(1)}%`)
    console.log(`   慢查詢率: ${stats.slowCallRate.toFixed(1)}%`)
    console.log(`   平均耗時: ${stats.avgDuration}ms`)
    console.log(`   最長耗時: ${stats.maxDuration}ms`)
    console.log(`   最短耗時: ${stats.minDuration}ms`)

    const ranking = this.getEndpointRanking()
    if (ranking.length > 0) {
      console.log('\n🏆 端點性能排名 (按平均耗時):')
      ranking.slice(0, 5).forEach((item, index) => {
        console.log(`   ${index + 1}. ${item.endpoint}: ${item.avgDuration}ms (慢查詢率: ${item.slowRate.toFixed(1)}%)`)
      })
    }
  }
}

// 創建全域監控實例
export const apiMonitor = new APIPerformanceMonitor()

// 定期清理和報告（每10分鐘）
setInterval(() => {
  apiMonitor.cleanup()
  if (process.env.NODE_ENV === 'development') {
    apiMonitor.printReport()
  }
}, 10 * 60 * 1000)

export { APIPerformanceMonitor }