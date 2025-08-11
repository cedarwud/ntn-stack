/**
 * React 錯誤邊界組件
 * 捕獲組件樹中的 JavaScript 錯誤並顯示用戶友好的錯誤界面
 */
import React, { Component, ReactNode } from 'react'
import { globalErrorHandler, ErrorSeverity, ErrorCategory, getUserFriendlyMessage } from '../../../../utils/error-handler'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: unknown) => void
  level?: 'page' | 'section' | 'component'
}

interface State {
  hasError: boolean
  error?: Error
  errorId?: string
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    }
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    // 記錄錯誤到全局錯誤處理器
    globalErrorHandler.handleError(error, {
      component: 'ErrorBoundary',
      action: 'componentDidCatch',
      metadata: {
        errorInfo,
        level: this.props.level || 'component',
        componentStack: errorInfo.componentStack
      },
      severity: this.props.level === 'page' ? ErrorSeverity.CRITICAL : ErrorSeverity.HIGH,
      category: ErrorCategory.COMPONENT
    })

    // 調用自定義錯誤處理器
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorId: undefined })
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      // 如果有自定義回退UI，使用它
      if (this.props.fallback) {
        return this.props.fallback
      }

      // 根據錯誤級別返回不同的錯誤UI
      return this.renderErrorUI()
    }

    return this.props.children
  }

  private renderErrorUI() {
    const { error, errorId } = this.state
    const { level = 'component' } = this.props
    const friendlyMessage = error ? getUserFriendlyMessage(error) : '發生未知錯誤'

    if (level === 'page') {
      return this.renderPageErrorUI(friendlyMessage, errorId)
    }

    if (level === 'section') {
      return this.renderSectionErrorUI(friendlyMessage, errorId)
    }

    return this.renderComponentErrorUI(friendlyMessage, errorId)
  }

  private renderPageErrorUI(message: string, errorId?: string) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
        <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8 text-center">
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">頁面發生錯誤</h1>
            <p className="text-gray-600">{message}</p>
          </div>

          <div className="space-y-3">
            <button
              onClick={this.handleReload}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              重新載入頁面
            </button>
            <button
              onClick={this.handleRetry}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-md transition-colors"
            >
              重試
            </button>
          </div>

          {errorId && (
            <p className="mt-4 text-xs text-gray-500">
              錯誤ID: {errorId}
            </p>
          )}
        </div>
      </div>
    )
  }

  private renderSectionErrorUI(message: string, errorId?: string) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 m-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-red-800">
              區塊載入失敗
            </h3>
            <p className="mt-1 text-sm text-red-700">{message}</p>
            <div className="mt-4 flex space-x-3">
              <button
                onClick={this.handleRetry}
                className="bg-red-100 hover:bg-red-200 text-red-800 text-sm font-medium py-1 px-3 rounded transition-colors"
              >
                重試
              </button>
            </div>
            {errorId && (
              <p className="mt-2 text-xs text-red-600">錯誤ID: {errorId}</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  private renderComponentErrorUI(message: string, errorId?: string) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded p-4 m-2">
        <div className="flex items-center">
          <svg className="h-4 w-4 text-yellow-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm text-yellow-800">{message}</p>
            {errorId && (
              <p className="text-xs text-yellow-600 mt-1">ID: {errorId}</p>
            )}
          </div>
          <button
            onClick={this.handleRetry}
            className="text-yellow-800 hover:text-yellow-900 text-sm font-medium ml-2"
          >
            重試
          </button>
        </div>
      </div>
    )
  }
}

/**
 * HOC: 為組件添加錯誤邊界
 */
// eslint-disable-next-line react-refresh/only-export-components
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  )

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

/**
 * Hook: 在函數組件中手動觸發錯誤邊界
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null)

  const captureError = React.useCallback((error: Error | string) => {
    const errorObj = typeof error === 'string' ? new Error(error) : error
    setError(errorObj)
  }, [])

  React.useEffect(() => {
    if (error) {
      throw error
    }
  }, [error])

  return captureError
}

export default ErrorBoundary