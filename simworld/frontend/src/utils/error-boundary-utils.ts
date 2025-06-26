/**
 * Error Boundary 工具函數
 * 分離出來以避免 Fast Refresh 警告
 */
import React from 'react'

/**
 * Error Boundary 相關類型定義
 */
export interface ErrorBoundaryProps {
    fallback?: React.ComponentType<{ error: Error; retry?: () => void }>
    onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

/**
 * Hook: 在函數組件中手動觸發錯誤邊界
 */
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

    return { captureError }
}
