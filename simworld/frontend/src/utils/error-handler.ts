/**
 * 全局錯誤處理和回退機制
 * 提供統一的錯誤處理、重試邏輯和用戶友好的錯誤顯示
 */

export interface ErrorDetails {
  message: string
  code?: string | number
  timestamp: string
  component?: string
  action?: string
  metadata?: Record<string, unknown>
}

export interface RetryConfig {
  maxAttempts: number
  initialDelay: number
  maxDelay: number
  backoffFactor: number
  retryCondition?: (error: Error) => boolean
}

export interface FallbackConfig<T> {
  fallbackValue?: T
  fallbackFunction?: () => T | Promise<T>
  showFallbackMessage?: boolean
  logError?: boolean
}

/**
 * 錯誤分類
 */
export enum ErrorCategory {
  NETWORK = 'network',
  API = 'api',
  VALIDATION = 'validation',
  AUTHENTICATION = 'authentication',
  PERMISSION = 'permission',
  COMPONENT = 'component',
  UNKNOWN = 'unknown'
}

/**
 * 錯誤嚴重程度
 */
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

/**
 * 錯誤處理器類
 */
export class ErrorHandler {
  private errorLog: ErrorDetails[] = []
  private maxLogSize = 100
  private errorListeners: Array<(error: ErrorDetails) => void> = []

  /**
   * 處理錯誤並記錄
   */
  handleError(
    error: Error | string,
    context?: {
      component?: string
      action?: string
      metadata?: Record<string, unknown>
      severity?: ErrorSeverity
      category?: ErrorCategory
    }
  ): ErrorDetails {
    const errorDetails: ErrorDetails = {
      message: typeof error === 'string' ? error : error.message,
      code: typeof error === 'object' && 'code' in error ? 
        (typeof error.code === 'string' || typeof error.code === 'number' ? error.code : undefined) : 
        undefined,
      timestamp: new Date().toISOString(),
      component: context?.component,
      action: context?.action,
      metadata: {
        ...context?.metadata,
        severity: context?.severity || ErrorSeverity.MEDIUM,
        category: context?.category || this.categorizeError(error),
        stack: typeof error === 'object' ? error.stack : undefined
      }
    }

    // 添加到錯誤日誌
    this.addToLog(errorDetails)

    // 通知監聽器
    this.notifyListeners(errorDetails)

    // 基於嚴重程度決定是否需要特殊處理
    if (context?.severity === ErrorSeverity.CRITICAL) {
      this.handleCriticalError(errorDetails)
    }

    return errorDetails
  }

  /**
   * 自動分類錯誤
   */
  private categorizeError(error: Error | string): ErrorCategory {
    const message = typeof error === 'string' ? error : error.message.toLowerCase()

    if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
      return ErrorCategory.NETWORK
    }
    if (message.includes('api') || message.includes('endpoint') || message.includes('status')) {
      return ErrorCategory.API
    }
    if (message.includes('unauthorized') || message.includes('authentication')) {
      return ErrorCategory.AUTHENTICATION
    }
    if (message.includes('permission') || message.includes('forbidden')) {
      return ErrorCategory.PERMISSION
    }
    if (message.includes('validation') || message.includes('invalid')) {
      return ErrorCategory.VALIDATION
    }

    return ErrorCategory.UNKNOWN
  }

  /**
   * 處理嚴重錯誤
   */
  private handleCriticalError(errorDetails: ErrorDetails) {
    console.error('🚨 Critical Error:', errorDetails)
    
    // 可以在這裡添加：
    // - 發送錯誤報告到監控服務
    // - 顯示全局錯誤彈窗
    // - 觸發回退模式
  }

  /**
   * 添加到錯誤日誌
   */
  private addToLog(error: ErrorDetails) {
    this.errorLog.unshift(error)
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize)
    }
  }

  /**
   * 通知監聽器
   */
  private notifyListeners(error: ErrorDetails) {
    this.errorListeners.forEach(listener => {
      try {
        listener(error)
      } catch (err) {
        console.warn('Error in error listener:', err)
      }
    })
  }

  /**
   * 添加錯誤監聽器
   */
  addErrorListener(listener: (error: ErrorDetails) => void) {
    this.errorListeners.push(listener)
    
    return () => {
      const index = this.errorListeners.indexOf(listener)
      if (index > -1) {
        this.errorListeners.splice(index, 1)
      }
    }
  }

  /**
   * 獲取錯誤日誌
   */
  getErrorLog(): ErrorDetails[] {
    return [...this.errorLog]
  }

  /**
   * 清除錯誤日誌
   */
  clearErrorLog() {
    this.errorLog = []
  }

  /**
   * 獲取錯誤統計
   */
  getErrorStats() {
    const categories = this.errorLog.reduce((acc, error) => {
      const category = (error.metadata?.category as string) || ErrorCategory.UNKNOWN
      acc[category] = (acc[category] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const severities = this.errorLog.reduce((acc, error) => {
      const severity = (error.metadata?.severity as string) || ErrorSeverity.MEDIUM
      acc[severity] = (acc[severity] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return {
      total: this.errorLog.length,
      categories,
      severities,
      recent: this.errorLog.slice(0, 5)
    }
  }
}

/**
 * 重試工具函數
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
    retryCondition = () => true
  } = config

  let lastError: Error
  let delay = initialDelay

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error as Error
      
      // 檢查是否應該重試
      if (attempt === maxAttempts || !retryCondition(lastError)) {
        throw lastError
      }

      // 等待後重試
      await new Promise(resolve => setTimeout(resolve, delay))
      delay = Math.min(delay * backoffFactor, maxDelay)
    }
  }

  throw lastError!
}

/**
 * 回退機制工具函數
 */
export async function withFallback<T>(
  operation: () => Promise<T>,
  config: FallbackConfig<T>
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    if (config.logError !== false) {
      globalErrorHandler.handleError(error as Error, {
        component: 'FallbackHandler',
        action: 'withFallback'
      })
    }

    if (config.showFallbackMessage) {
      console.warn('Operation failed, using fallback:', error)
    }

    if (config.fallbackFunction) {
      return await config.fallbackFunction()
    }

    if (config.fallbackValue !== undefined) {
      return config.fallbackValue
    }

    throw error
  }
}

/**
 * 安全執行函數 - 確保不會拋出未處理的錯誤
 */
export function safeExecute<T>(
  operation: () => T,
  fallbackValue?: T,
  errorHandler?: (error: Error) => void
): T | undefined {
  try {
    return operation()
  } catch (error) {
    if (errorHandler) {
      errorHandler(error as Error)
    } else {
      globalErrorHandler.handleError(error as Error, {
        component: 'SafeExecute',
        action: 'safeExecute'
      })
    }
    return fallbackValue
  }
}

/**
 * 網路錯誤處理 - 專門處理API調用錯誤
 */
export class NetworkErrorHandler {
  static isNetworkError(error: Error): boolean {
    return error.message.includes('fetch') || 
           error.message.includes('network') || 
           error.message.includes('connection') ||
           error.name === 'TypeError'
  }

  static isTimeout(error: Error): boolean {
    return error.message.includes('timeout') || 
           error.name === 'TimeoutError'
  }

  static isServerError(error: Error & { status?: number }): boolean {
    return error.status ? error.status >= 500 : false
  }

  static shouldRetry(error: Error & { status?: number }): boolean {
    // 重試條件：網路錯誤、超時、5xx 服務器錯誤
    return this.isNetworkError(error) || 
           this.isTimeout(error) || 
           this.isServerError(error)
  }

  static getRetryConfig(error: Error): Partial<RetryConfig> {
    if (this.isTimeout(error)) {
      return {
        maxAttempts: 2,
        initialDelay: 500,
        maxDelay: 2000
      }
    }

    if (this.isNetworkError(error)) {
      return {
        maxAttempts: 3,
        initialDelay: 1000,
        maxDelay: 5000
      }
    }

    return {
      maxAttempts: 2,
      initialDelay: 1000,
      maxDelay: 3000
    }
  }
}

/**
 * React 錯誤邊界工具
 */
export interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: React.ErrorInfo
}

export function createErrorBoundaryProps() {
  return {
    onError: (error: Error, errorInfo: React.ErrorInfo) => {
      globalErrorHandler.handleError(error, {
        component: 'ErrorBoundary',
        action: 'componentDidCatch',
        metadata: { errorInfo },
        severity: ErrorSeverity.HIGH,
        category: ErrorCategory.COMPONENT
      })
    }
  }
}

/**
 * 用戶友好的錯誤消息
 */
export function getUserFriendlyMessage(error: Error | ErrorDetails): string {
  const message = typeof error === 'object' && 'message' in error ? error.message : String(error)
  const category = typeof error === 'object' && 'metadata' in error ? 
    error.metadata?.category : undefined

  switch (category) {
    case ErrorCategory.NETWORK:
      return '網路連接問題，請檢查您的網路連接後重試'
    case ErrorCategory.API:
      return '服務暫時無法使用，請稍後重試'
    case ErrorCategory.AUTHENTICATION:
      return '登入已過期，請重新登入'
    case ErrorCategory.PERMISSION:
      return '您沒有執行此操作的權限'
    case ErrorCategory.VALIDATION:
      return '輸入資料有誤，請檢查後重新提交'
    default:
      // 回退到原始錯誤消息，但移除技術細節
      return message.includes('Error:') ? 
        message.split('Error:')[1]?.trim() || '發生未知錯誤' : 
        message || '發生未知錯誤'
  }
}

// 全局錯誤處理器實例
export const globalErrorHandler = new ErrorHandler()

// 設置全局錯誤監聽
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    globalErrorHandler.handleError(event.error || event.message, {
      component: 'Global',
      action: 'unhandledError',
      severity: ErrorSeverity.HIGH
    })
  })

  window.addEventListener('unhandledrejection', (event) => {
    globalErrorHandler.handleError(event.reason, {
      component: 'Global',
      action: 'unhandledPromiseRejection',
      severity: ErrorSeverity.HIGH
    })
  })
}