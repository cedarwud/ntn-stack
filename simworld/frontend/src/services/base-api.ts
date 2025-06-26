/**
 * 基礎 API 客戶端類
 * 提供統一的 HTTP 請求處理和錯誤管理
 */
import { performanceOptimizer } from '../utils/performance-optimizer'
import { withRetry, NetworkErrorHandler, globalErrorHandler, ErrorCategory } from '../utils/error-handler'

export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
  timestamp?: string
}

export class BaseApiClient {
  protected baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  /**
   * 統一的 GET 請求方法 - 包含重試和錯誤處理
   */
  protected async get<T>(endpoint: string, params?: Record<string, string | number | boolean>): Promise<T> {
    return withRetry(async () => {
      const endAPICall = performanceOptimizer.startAPICall(endpoint)
      
      try {
        // Handle relative URLs for Vite proxy
        let url: URL
        if (this.baseUrl.startsWith('http')) {
          // Absolute URL
          url = new URL(endpoint, this.baseUrl)
        } else {
          // Relative URL (proxy path like /netstack)
          const fullPath = this.baseUrl + endpoint
          url = new URL(fullPath, window.location.origin)
        }
        
        if (params) {
          Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
              url.searchParams.append(key, String(value))
            }
          })
        }

        const response = await fetch(url.toString(), {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: AbortSignal.timeout(10000) // 10秒超時
        })

        if (!response.ok) {
          endAPICall(true)
          // 只記錄非 404 錯誤，404 可能是正常的 fallback 邏輯
          if (response.status !== 404) {
            console.error(`❌ API Error: ${endpoint} - ${response.status} ${response.statusText}`)
          }
          const error = new Error(`API request failed: ${response.status} ${response.statusText}`) as Error & { status: number }
          error.status = response.status
          throw error
        }

        const result = await response.json()
        endAPICall(false)
        return result
      } catch (error) {
        endAPICall(true)
        
        // 記錄錯誤到全局錯誤處理器
        globalErrorHandler.handleError(error as Error, {
          component: 'BaseApiClient',
          action: 'GET',
          metadata: { endpoint, params },
          category: ErrorCategory.API
        })
        
        throw error
      }
    }, {
      maxAttempts: 3,
      initialDelay: 1000,
      maxDelay: 5000,
      backoffFactor: 2,
      retryCondition: (error) => NetworkErrorHandler.shouldRetry(error as Error & { status?: number })
    })
  }

  /**
   * 統一的 POST 請求方法 - 包含重試和錯誤處理
   */
  protected async post<T>(endpoint: string, data?: Record<string, unknown> | FormData | string): Promise<T> {
    return withRetry(async () => {
      const endAPICall = performanceOptimizer.startAPICall(endpoint)
      
      try {
        // Handle relative URLs for Vite proxy
        let url: URL
        if (this.baseUrl.startsWith('http')) {
          // Absolute URL
          url = new URL(endpoint, this.baseUrl)
        } else {
          // Relative URL (proxy path like /netstack)
          const fullPath = this.baseUrl + endpoint
          url = new URL(fullPath, window.location.origin)
        }

        const response = await fetch(url.toString(), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: data ? JSON.stringify(data) : undefined,
          signal: AbortSignal.timeout(10000) // 10秒超時
        })

        if (!response.ok) {
          endAPICall(true)
          // 只記錄非 404 錯誤，404 可能是正常的 fallback 邏輯
          if (response.status !== 404) {
            console.error(`❌ API Error: ${endpoint} - ${response.status} ${response.statusText}`)
          }
          const error = new Error(`API request failed: ${response.status} ${response.statusText}`) as Error & { status: number }
          error.status = response.status
          throw error
        }

        const result = await response.json()
        endAPICall(false)
        return result
      } catch (error) {
        endAPICall(true)
        
        // 記錄錯誤到全局錯誤處理器
        globalErrorHandler.handleError(error as Error, {
          component: 'BaseApiClient',
          action: 'POST',
          metadata: { endpoint, data },
          category: ErrorCategory.API
        })
        
        throw error
      }
    }, {
      maxAttempts: 3,
      initialDelay: 1000,
      maxDelay: 5000,
      backoffFactor: 2,
      retryCondition: (error) => NetworkErrorHandler.shouldRetry(error as Error & { status?: number })
    })
  }

  /**
   * 統一的 PUT 請求方法 - 包含重試和錯誤處理
   */
  protected async put<T>(endpoint: string, data?: Record<string, unknown> | FormData | string): Promise<T> {
    return withRetry(async () => {
      const endAPICall = performanceOptimizer.startAPICall(endpoint)
      
      try {
        // Handle relative URLs for Vite proxy
        let url: URL
        if (this.baseUrl.startsWith('http')) {
          // Absolute URL
          url = new URL(endpoint, this.baseUrl)
        } else {
          // Relative URL (proxy path like /netstack)
          const fullPath = this.baseUrl + endpoint
          url = new URL(fullPath, window.location.origin)
        }

        const response = await fetch(url.toString(), {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: data ? JSON.stringify(data) : undefined,
          signal: AbortSignal.timeout(10000) // 10秒超時
        })

        if (!response.ok) {
          endAPICall(true)
          // 只記錄非 404 錯誤，404 可能是正常的 fallback 邏輯
          if (response.status !== 404) {
            console.error(`❌ API Error: ${endpoint} - ${response.status} ${response.statusText}`)
          }
          const error = new Error(`API request failed: ${response.status} ${response.statusText}`) as Error & { status: number }
          error.status = response.status
          throw error
        }

        const result = await response.json()
        endAPICall(false)
        return result
      } catch (error) {
        endAPICall(true)
        
        // 記錄錯誤到全局錯誤處理器
        globalErrorHandler.handleError(error as Error, {
          component: 'BaseApiClient',
          action: 'PUT',
          metadata: { endpoint, data },
          category: ErrorCategory.API
        })
        
        throw error
      }
    }, {
      maxAttempts: 3,
      initialDelay: 1000,
      maxDelay: 5000,
      backoffFactor: 2,
      retryCondition: (error) => NetworkErrorHandler.shouldRetry(error as Error & { status?: number })
    })
  }

  /**
   * 統一的 DELETE 請求方法 - 包含重試和錯誤處理
   */
  protected async delete<T>(endpoint: string): Promise<T> {
    return withRetry(async () => {
      const endAPICall = performanceOptimizer.startAPICall(endpoint)
      
      try {
        // Handle relative URLs for Vite proxy
        let url: URL
        if (this.baseUrl.startsWith('http')) {
          // Absolute URL
          url = new URL(endpoint, this.baseUrl)
        } else {
          // Relative URL (proxy path like /netstack)
          const fullPath = this.baseUrl + endpoint
          url = new URL(fullPath, window.location.origin)
        }

        const response = await fetch(url.toString(), {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: AbortSignal.timeout(10000) // 10秒超時
        })

        if (!response.ok) {
          endAPICall(true)
          // 只記錄非 404 錯誤，404 可能是正常的 fallback 邏輯
          if (response.status !== 404) {
            console.error(`❌ API Error: ${endpoint} - ${response.status} ${response.statusText}`)
          }
          const error = new Error(`API request failed: ${response.status} ${response.statusText}`) as Error & { status: number }
          error.status = response.status
          throw error
        }

        const result = await response.json()
        endAPICall(false)
        return result
      } catch (error) {
        endAPICall(true)
        
        // 記錄錯誤到全局錯誤處理器
        globalErrorHandler.handleError(error as Error, {
          component: 'BaseApiClient',
          action: 'DELETE',
          metadata: { endpoint },
          category: ErrorCategory.API
        })
        
        throw error
      }
    }, {
      maxAttempts: 3,
      initialDelay: 1000,
      maxDelay: 5000,
      backoffFactor: 2,
      retryCondition: (error) => NetworkErrorHandler.shouldRetry(error as Error & { status?: number })
    })
  }

  /**
   * 健康檢查方法 - 所有API都需要
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await this.get<{ status: string }>('/health')
      return {
        status: response.status || 'ok',
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        status: 'error',
        timestamp: new Date().toISOString()
      }
    }
  }

  /**
   * 批量請求處理 - 減少重複的批量操作代碼
   */
  protected async batchRequest<T>(
    requests: Array<() => Promise<T>>
  ): Promise<Array<T | null>> {
    const results = await Promise.allSettled(requests.map(req => req()))
    
    return results.map(result => 
      result.status === 'fulfilled' ? result.value : null
    )
  }

  /**
   * 重試邏輯 - 統一的重試機制
   */
  protected async withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: Error

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error as Error
        
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, delay * attempt))
        }
      }
    }

    throw lastError!
  }

  /**
   * 緩存機制 - 統一的響應緩存
   */
  private cache = new Map<string, { data: unknown; timestamp: number }>()
  
  protected async getCached<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttlMs: number = 30000
  ): Promise<T> {
    const cached = this.cache.get(key)
    const now = Date.now()
    
    if (cached && (now - cached.timestamp) < ttlMs) {
      return cached.data as T
    }
    
    const data = await fetcher()
    this.cache.set(key, { data, timestamp: now })
    
    return data
  }

  /**
   * 清理緩存
   */
  protected clearCache(pattern?: string): void {
    if (!pattern) {
      this.cache.clear()
      return
    }
    
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key)
      }
    }
  }
}