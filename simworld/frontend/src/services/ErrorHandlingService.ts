/**
 * 統一錯誤處理服務
 * 提供標準化的錯誤處理、記錄和回復機制
 * 替換專案中27處重複的錯誤處理邏輯
 */

export interface ErrorContext {
  component?: string
  operation?: string
  endpoint?: string
  method?: string
  timestamp?: string
  severity?: 'low' | 'medium' | 'high' | 'critical'
  retryCount?: number
}

export interface ErrorHandlingOptions {
  shouldThrow?: boolean
  shouldRetry?: boolean
  maxRetries?: number
  fallbackData?: unknown
  onError?: (error: Error, context: ErrorContext) => void
}

export class ErrorHandlingService {
  private static readonly DEFAULT_OPTIONS: ErrorHandlingOptions = {
    shouldThrow: false,
    shouldRetry: false,
    maxRetries: 3,
    fallbackData: null,
  }

  /**
   * API 調用錯誤處理
   * 統一處理 API 調用失敗的情況
   */
  static handleApiError(
    error: unknown,
    context: ErrorContext,
    options: ErrorHandlingOptions = {}
  ): never | unknown {
    const mergedOptions = { ...this.DEFAULT_OPTIONS, ...options }
    const errorMessage = this.extractErrorMessage(error)
    
    const fullContext: ErrorContext = {
      ...context,
      timestamp: new Date().toISOString(),
      severity: this.determineSeverity(error, context),
    }

    // 記錄錯誤
    this.logError(errorMessage, fullContext)

    // 調用自定義錯誤處理函數
    if (mergedOptions.onError) {
      mergedOptions.onError(error as Error, fullContext)
    }

    // 決定是否拋出錯誤
    if (mergedOptions.shouldThrow) {
      throw new Error(`${context.operation || 'API調用'} 失敗: ${errorMessage}`)
    }

    // 返回 fallback 數據
    return mergedOptions.fallbackData
  }

  /**
   * 網路連接錯誤處理
   * 專門處理網路連接問題
   */
  static handleNetworkError(
    error: unknown,
    context: ErrorContext,
    options: ErrorHandlingOptions = {}
  ): unknown {
    const enhancedContext = {
      ...context,
      severity: 'high' as const,
      operation: context.operation || '網路連接',
    }

    console.error('🌐 網路連接錯誤:', {
      endpoint: context.endpoint,
      error: this.extractErrorMessage(error),
      timestamp: new Date().toISOString(),
    })

    return this.handleApiError(error, enhancedContext, {
      ...options,
      shouldRetry: options.shouldRetry ?? true,
    })
  }

  /**
   * 數據載入錯誤處理
   * 處理數據載入失敗並提供回退數據
   */
  static handleDataLoadError<T>(
    error: unknown,
    context: ErrorContext,
    fallbackData: T,
    options: ErrorHandlingOptions = {}
  ): T {
    const enhancedContext = {
      ...context,
      severity: 'medium' as const,
      operation: context.operation || '數據載入',
    }

    console.warn('📊 數據載入失敗，使用回退數據:', {
      component: context.component,
      operation: context.operation,
      error: this.extractErrorMessage(error),
      timestamp: new Date().toISOString(),
    })

    this.handleApiError(error, enhancedContext, {
      ...options,
      shouldThrow: false,
    })

    return fallbackData
  }

  /**
   * Hook 錯誤處理
   * 專門處理 React Hook 中的錯誤
   */
  static handleHookError(
    error: unknown,
    context: ErrorContext,
    options: ErrorHandlingOptions = {}
  ): void {
    const enhancedContext = {
      ...context,
      severity: 'medium' as const,
      component: context.component || 'Unknown Hook',
    }

    console.warn('⚛️ Hook 執行錯誤:', {
      hook: context.component,
      operation: context.operation,
      error: this.extractErrorMessage(error),
      timestamp: new Date().toISOString(),
    })

    this.handleApiError(error, enhancedContext, {
      ...options,
      shouldThrow: false,
    })
  }

  /**
   * 組件錯誤處理
   * 處理 React 組件中的錯誤
   */
  static handleComponentError(
    error: unknown,
    context: ErrorContext,
    options: ErrorHandlingOptions = {}
  ): void {
    const enhancedContext = {
      ...context,
      severity: 'high' as const,
      component: context.component || 'Unknown Component',
    }

    console.error('🔧 組件錯誤:', {
      component: context.component,
      operation: context.operation,
      error: this.extractErrorMessage(error),
      timestamp: new Date().toISOString(),
    })

    this.handleApiError(error, enhancedContext, options)
  }

  /**
   * 關鍵功能錯誤處理
   * 處理系統關鍵功能的錯誤
   */
  static handleCriticalError(
    error: unknown,
    context: ErrorContext,
    options: ErrorHandlingOptions = {}
  ): never {
    const enhancedContext = {
      ...context,
      severity: 'critical' as const,
    }

    console.error('🚨 關鍵錯誤:', {
      component: context.component,
      operation: context.operation,
      endpoint: context.endpoint,
      error: this.extractErrorMessage(error),
      timestamp: new Date().toISOString(),
    })

    this.handleApiError(error, enhancedContext, {
      ...options,
      shouldThrow: true,
    })

    // TypeScript 需要這個，雖然上面已經拋出錯誤
    throw new Error('Critical error occurred')
  }

  /**
   * 帶重試的 API 調用
   * 自動重試失敗的 API 調用
   */
  static async withRetry<T>(
    operation: () => Promise<T>,
    context: ErrorContext,
    options: ErrorHandlingOptions = {}
  ): Promise<T> {
    const maxRetries = options.maxRetries ?? 3
    let lastError: unknown

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error
        
        if (attempt === maxRetries) {
          // 最後一次嘗試失敗
          const enhancedContext = {
            ...context,
            retryCount: attempt,
            operation: `${context.operation} (重試 ${attempt}/${maxRetries})`,
          }
          
          return this.handleApiError(error, enhancedContext, options) as T
        }

        // 重試前等待
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000) // 指數退避，最大5秒
        await new Promise(resolve => setTimeout(resolve, delay))
        
        console.warn(`🔄 重試 ${attempt}/${maxRetries}:`, {
          operation: context.operation,
          error: this.extractErrorMessage(error),
        })
      }
    }

    // 不應該到達這裡，但為了 TypeScript
    throw lastError
  }

  /**
   * 提取錯誤訊息
   */
  private static extractErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message
    }
    if (typeof error === 'string') {
      return error
    }
    if (error && typeof error === 'object' && 'message' in error) {
      return String((error as { message: unknown }).message)
    }
    return '未知錯誤'
  }

  /**
   * 決定錯誤嚴重程度
   */
  private static determineSeverity(error: unknown, context: ErrorContext): ErrorContext['severity'] {
    // 如果已經指定嚴重程度，直接使用
    if (context.severity) {
      return context.severity
    }

    const errorMessage = this.extractErrorMessage(error).toLowerCase()

    // 關鍵錯誤模式
    if (errorMessage.includes('network') || 
        errorMessage.includes('connection') ||
        errorMessage.includes('timeout')) {
      return 'high'
    }

    // 中等錯誤模式
    if (errorMessage.includes('not found') || 
        errorMessage.includes('404') ||
        errorMessage.includes('data')) {
      return 'medium'
    }

    // 預設為低級錯誤
    return 'low'
  }

  /**
   * 記錄錯誤
   */
  private static logError(message: string, context: ErrorContext): void {
    const logEntry = {
      message,
      component: context.component,
      operation: context.operation,
      endpoint: context.endpoint,
      method: context.method,
      severity: context.severity,
      timestamp: context.timestamp,
      retryCount: context.retryCount,
    }

    switch (context.severity) {
      case 'critical':
        console.error('🚨 CRITICAL:', logEntry)
        break
      case 'high':
        console.error('❗ HIGH:', logEntry)
        break
      case 'medium':
        console.warn('⚠️ MEDIUM:', logEntry)
        break
      case 'low':
      default:
        console.warn('ℹ️ LOW:', logEntry)
        break
    }
  }

  /**
   * 常用的錯誤處理預設值
   */
  static readonly PATTERNS = {
    /**
     * API 端點不存在的處理
     */
    ENDPOINT_NOT_EXISTS: (endpoint: string, fallbackData: unknown) => ({
      shouldThrow: false,
      fallbackData,
      onError: (_error: Error, _context: ErrorContext) => {
        console.error(`🚨 API 錯誤 - ${endpoint} 端點不存在，使用模擬數據`)
      }
    }),

    /**
     * 數據載入失敗的處理
     */
    DATA_LOAD_FAILED: (componentName: string, fallbackData: unknown) => ({
      shouldThrow: false,
      fallbackData,
      onError: (error: Error, _context: ErrorContext) => {
        console.warn(`📊 ${componentName} 數據載入失敗，使用回退數據:`, error.message)
      }
    }),

    /**
     * 網路連接問題的處理
     */
    NETWORK_ERROR: {
      shouldRetry: true,
      maxRetries: 3,
      shouldThrow: false,
      onError: (error: Error, context: ErrorContext) => {
        console.error('🌐 網路連接問題:', {
          endpoint: context.endpoint,
          error: error.message,
          timestamp: new Date().toISOString()
        })
      }
    },
  }
}