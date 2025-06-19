/**
 * 安全組件包裝器
 * 為任何組件添加錯誤處理、加載狀態和回退機制
 */
import React, { Suspense, useState, useEffect, useCallback } from 'react'
import ErrorBoundary from './ErrorBoundary'
import { withFallback, globalErrorHandler, ErrorCategory } from '../../utils/error-handler'

export interface SafeComponentProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  loadingFallback?: React.ReactNode
  errorFallback?: React.ReactNode
  level?: 'page' | 'section' | 'component'
  retryable?: boolean
  maxRetries?: number
  onError?: (error: Error) => void
  onRetry?: () => void
}

export interface AsyncComponentProps<T> {
  asyncOperation: () => Promise<T>
  children: (data: T) => React.ReactNode
  fallback?: React.ReactNode
  errorFallback?: (error: Error, retry: () => void) => React.ReactNode
  loadingFallback?: React.ReactNode
  deps?: any[]
  retryable?: boolean
  maxRetries?: number
}

/**
 * 安全組件包裝器 - 提供錯誤邊界和加載狀態
 */
export function SafeComponent({
  children,
  loadingFallback,
  errorFallback,
  level = 'component',
  onError
}: SafeComponentProps) {
  return (
    <ErrorBoundary
      level={level}
      fallback={errorFallback}
      onError={onError}
    >
      <Suspense fallback={loadingFallback || <DefaultLoadingFallback />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  )
}

/**
 * 異步組件 - 處理異步數據加載
 */
export function AsyncComponent<T>({
  asyncOperation,
  children,
  fallback,
  errorFallback,
  loadingFallback,
  deps = [],
  retryable = true,
  maxRetries = 3
}: AsyncComponentProps<T>) {
  const [state, setState] = useState<{
    data?: T
    loading: boolean
    error?: Error
    retryCount: number
  }>({
    loading: true,
    retryCount: 0
  })

  const executeOperation = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: undefined }))
    
    try {
      const result = await withFallback(
        asyncOperation,
        {
          logError: true,
          showFallbackMessage: false
        }
      )
      
      setState({
        data: result,
        loading: false,
        error: undefined,
        retryCount: 0
      })
    } catch (error) {
      globalErrorHandler.handleError(error as Error, {
        component: 'AsyncComponent',
        action: 'executeOperation',
        category: ErrorCategory.COMPONENT
      })
      
      setState(prev => ({
        ...prev,
        loading: false,
        error: error as Error,
        retryCount: prev.retryCount + 1
      }))
    }
  }, [asyncOperation, ...deps])

  const handleRetry = useCallback(() => {
    if (state.retryCount < maxRetries) {
      executeOperation()
    }
  }, [executeOperation, state.retryCount, maxRetries])

  useEffect(() => {
    executeOperation()
  }, [executeOperation])

  if (state.loading) {
    return loadingFallback ? <>{loadingFallback}</> : <DefaultLoadingFallback />
  }

  if (state.error) {
    if (errorFallback) {
      return <>{errorFallback(state.error, handleRetry)}</>
    }
    return (
      <DefaultErrorFallback 
        error={state.error} 
        onRetry={retryable && state.retryCount < maxRetries ? handleRetry : undefined}
        retryCount={state.retryCount}
        maxRetries={maxRetries}
      />
    )
  }

  if (state.data === undefined) {
    return fallback ? <>{fallback}</> : <DefaultEmptyFallback />
  }

  return <>{children(state.data)}</>
}

/**
 * 默認加載回退組件
 */
function DefaultLoadingFallback() {
  return (
    <div className="flex items-center justify-center p-4">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
      <span className="ml-2 text-gray-600">載入中...</span>
    </div>
  )
}

/**
 * 默認錯誤回退組件
 */
function DefaultErrorFallback({ 
  error, 
  onRetry, 
  retryCount, 
  maxRetries 
}: { 
  error: Error
  onRetry?: () => void
  retryCount: number
  maxRetries: number
}) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-2">
      <div className="flex items-start">
        <svg className="h-5 w-5 text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            載入失敗
          </h3>
          <p className="mt-1 text-sm text-red-700">
            {error.message || '發生未知錯誤'}
          </p>
          {onRetry && (
            <div className="mt-3">
              <button
                onClick={onRetry}
                className="bg-red-100 hover:bg-red-200 text-red-800 text-sm font-medium py-1 px-3 rounded transition-colors"
              >
                重試 ({retryCount}/{maxRetries})
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * 默認空狀態回退組件
 */
function DefaultEmptyFallback() {
  return (
    <div className="flex items-center justify-center p-4 text-gray-500">
      <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v1m-4 0V4a1 1 0 00-1-1H6a1 1 0 00-1 1v1m0 0h4v4H6V5z" />
      </svg>
      暫無資料
    </div>
  )
}

/**
 * HOC: 為組件添加安全包裝
 */
export function withSafeWrapper<P extends object>(
  Component: React.ComponentType<P>,
  safeProps?: Omit<SafeComponentProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <SafeComponent {...safeProps}>
      <Component {...props} />
    </SafeComponent>
  )

  WrappedComponent.displayName = `withSafeWrapper(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

/**
 * Hook: 安全的異步操作
 */
export function useSafeAsync<T>(
  asyncFn: () => Promise<T>,
  deps: any[] = []
) {
  const [state, setState] = useState<{
    data?: T
    loading: boolean
    error?: Error
  }>({ loading: true })

  const execute = useCallback(async () => {
    setState({ loading: true })
    
    try {
      const result = await asyncFn()
      setState({ data: result, loading: false })
    } catch (error) {
      globalErrorHandler.handleError(error as Error, {
        component: 'useSafeAsync',
        action: 'execute'
      })
      setState({ error: error as Error, loading: false })
    }
  }, deps)

  useEffect(() => {
    execute()
  }, [execute])

  return {
    ...state,
    refetch: execute
  }
}

export default SafeComponent