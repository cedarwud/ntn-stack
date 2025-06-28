/**
 * 性能優化工具
 * 提供組件渲染性能監控和優化建議
 */
import React from 'react'

export interface PerformanceMetrics {
  componentName: string
  renderTime: number
  rerenderCount: number
  memoryUsage?: number
  lastRenderTimestamp: number
}

export interface APICallMetrics {
  endpoint: string
  responseTime: number
  callCount: number
  errorCount: number
  lastCallTimestamp: number
}

class PerformanceOptimizer {
  private componentMetrics = new Map<string, PerformanceMetrics>()
  private apiMetrics = new Map<string, APICallMetrics>()
  private renderObserver?: PerformanceObserver
  
  constructor() {
    this.initializePerformanceMonitoring()
  }

  /**
   * 初始化性能監控
   */
  private initializePerformanceMonitoring() {
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      try {
        this.renderObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'measure') {
              this.recordRenderTime(entry.name, entry.duration)
            }
          }
        })
        this.renderObserver.observe({ entryTypes: ['measure'] })
      } catch (error) {
        console.warn('Performance monitoring not supported:', error)
      }
    }
  }

  /**
   * 記錄組件渲染時間
   */
  recordRenderTime(componentName: string, renderTime: number) {
    const existing = this.componentMetrics.get(componentName)
    
    if (existing) {
      existing.renderTime = renderTime
      existing.rerenderCount++
      existing.lastRenderTimestamp = Date.now()
    } else {
      this.componentMetrics.set(componentName, {
        componentName,
        renderTime,
        rerenderCount: 1,
        lastRenderTimestamp: Date.now()
      })
    }

    // 警告慢渲染
    if (renderTime > 16) { // 超過一個動畫幀
      console.warn(`🐌 Slow render detected: ${componentName} took ${renderTime.toFixed(2)}ms`)
    }
  }

  /**
   * 記錄API調用性能
   */
  recordAPICall(endpoint: string, responseTime: number, isError = false) {
    const existing = this.apiMetrics.get(endpoint)
    
    if (existing) {
      existing.responseTime = responseTime
      existing.callCount++
      if (isError) existing.errorCount++
      existing.lastCallTimestamp = Date.now()
    } else {
      this.apiMetrics.set(endpoint, {
        endpoint,
        responseTime,
        callCount: 1,
        errorCount: isError ? 1 : 0,
        lastCallTimestamp: Date.now()
      })
    }

    // 警告慢API調用（提高閾值減少噪音）
    if (responseTime > 3000) {
      console.warn(`🐌 Slow API call: ${endpoint} took ${responseTime}ms`)
    }
  }

  /**
   * 開始渲染測量
   */
  startRenderMeasure(componentName: string) {
    if (typeof performance !== 'undefined') {
      performance.mark(`${componentName}-render-start`)
    }
  }

  /**
   * 結束渲染測量
   */
  endRenderMeasure(componentName: string) {
    if (typeof performance !== 'undefined') {
      try {
        performance.mark(`${componentName}-render-end`)
        performance.measure(
          componentName,
          `${componentName}-render-start`,
          `${componentName}-render-end`
        )
      } catch {
        // 忽略測量錯誤
      }
    }
  }

  /**
   * 開始API調用測量
   */
  startAPICall(endpoint: string): () => void {
    const startTime = performance.now()
    
    return (isError = false) => {
      const endTime = performance.now()
      this.recordAPICall(endpoint, endTime - startTime, isError)
    }
  }

  /**
   * 獲取性能報告
   */
  getPerformanceReport() {
    const slowComponents = Array.from(this.componentMetrics.values())
      .filter(metric => metric.renderTime > 16)
      .sort((a, b) => b.renderTime - a.renderTime)

    const slowAPIs = Array.from(this.apiMetrics.values())
      .filter(metric => metric.responseTime > 500)
      .sort((a, b) => b.responseTime - a.responseTime)

    const highRerenderComponents = Array.from(this.componentMetrics.values())
      .filter(metric => metric.rerenderCount > 10)
      .sort((a, b) => b.rerenderCount - a.rerenderCount)

    return {
      slowComponents,
      slowAPIs,
      highRerenderComponents,
      totalComponents: this.componentMetrics.size,
      totalAPIs: this.apiMetrics.size,
      summary: this.generatePerformanceSummary()
    }
  }

  /**
   * 生成性能摘要
   */
  private generatePerformanceSummary() {
    const avgRenderTime = Array.from(this.componentMetrics.values())
      .reduce((sum, metric) => sum + metric.renderTime, 0) / this.componentMetrics.size || 0

    const avgAPITime = Array.from(this.apiMetrics.values())
      .reduce((sum, metric) => sum + metric.responseTime, 0) / this.apiMetrics.size || 0

    const totalRerenders = Array.from(this.componentMetrics.values())
      .reduce((sum, metric) => sum + metric.rerenderCount, 0)

    const apiErrorRate = Array.from(this.apiMetrics.values())
      .reduce((sum, metric) => sum + metric.errorCount, 0) / 
      Array.from(this.apiMetrics.values())
        .reduce((sum, metric) => sum + metric.callCount, 0) || 0

    return {
      avgRenderTime: Math.round(avgRenderTime * 100) / 100,
      avgAPITime: Math.round(avgAPITime),
      totalRerenders,
      apiErrorRate: Math.round(apiErrorRate * 10000) / 100 // 百分比
    }
  }

  /**
   * 清除性能數據
   */
  clearMetrics() {
    this.componentMetrics.clear()
    this.apiMetrics.clear()
  }

  /**
   * 銷毀性能監控
   */
  destroy() {
    if (this.renderObserver) {
      this.renderObserver.disconnect()
    }
  }
}

// React Hook for component performance monitoring
export function usePerformanceMonitoring(componentName: string) {
  const startRender = () => {
    performanceOptimizer.startRenderMeasure(componentName)
  }

  const endRender = () => {
    performanceOptimizer.endRenderMeasure(componentName)
  }

  return { startRender, endRender }
}

// React Hook for API call performance monitoring
export function useAPIPerformanceMonitoring() {
  const trackAPICall = (endpoint: string) => {
    return performanceOptimizer.startAPICall(endpoint)
  }

  return { trackAPICall }
}

// 全局性能優化器實例
export const performanceOptimizer = new PerformanceOptimizer()

// 在開發環境中暴露到 window 對象
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  ;(window as unknown as Window & { performanceOptimizer: PerformanceOptimizer }).performanceOptimizer = performanceOptimizer
}

/**
 * 組件性能優化裝飾器 HOC
 */
export function withPerformanceMonitoring<T extends object>(
  Component: React.ComponentType<T>,
  componentName?: string
) {
  const displayName = componentName || Component.displayName || Component.name || 'Anonymous'
  
  const WrappedComponent = (props: T) => {
    const { startRender, endRender } = usePerformanceMonitoring(displayName)
    
    React.useEffect(() => {
      startRender()
      
      return () => {
        endRender()
      }
    })

    return React.createElement(Component, props)
  }

  WrappedComponent.displayName = `withPerformanceMonitoring(${displayName})`
  
  return WrappedComponent
}

/**
 * 批量API調用優化器
 */
export class BatchAPIOptimizer {
  private batchRequests = new Map<string, {
    requests: Array<{ params: unknown; resolve: (value: unknown | PromiseLike<unknown>) => void; reject: (reason: unknown) => void }>
    timeout: NodeJS.Timeout
  }>()

  /**
   * 批量處理API請求
   */
  batchRequest<T>(
    endpoint: string,
    params: unknown,
    batchTime = 100
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      if (!this.batchRequests.has(endpoint)) {
        this.batchRequests.set(endpoint, {
          requests: [],
          timeout: setTimeout(() => {
            this.executeBatch(endpoint)
          }, batchTime)
        })
      }

      const batch = this.batchRequests.get(endpoint)!
      batch.requests.push({ params, resolve, reject })
    })
  }

  /**
   * 執行批量請求
   */
  private async executeBatch(endpoint: string) {
    const batch = this.batchRequests.get(endpoint)
    if (!batch) return

    this.batchRequests.delete(endpoint)
    clearTimeout(batch.timeout)

    try {
      // 這裡需要根據具體API實現批量調用邏輯
      // 示例：將多個請求合併為一個批量請求
      const allParams = batch.requests.map(req => req.params)
      
      // 假設API支持批量查詢
      const response = await fetch(`${endpoint}/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requests: allParams })
      })

      const results = await response.json()
      
      // 將結果分發給各個請求
      batch.requests.forEach((req, index) => {
        req.resolve(results[index])
      })
    } catch (error) {
      // 如果批量請求失敗，逐個重試
      batch.requests.forEach(req => {
        req.reject(error)
      })
    }
  }
}

export const batchAPIOptimizer = new BatchAPIOptimizer()