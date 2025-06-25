/**
 * 系統狀態圖表組件
 * 顯示各系統組件的健康狀態和指標
 */
import { useState, useEffect, useCallback } from 'react'
import { getSystemStatus } from '../../../services/netstackApi'
import { SystemStatus } from '../../../types/charts'

interface SystemStatusChartProps {
    className?: string
    refreshInterval?: number
}

const SystemStatusChart: React.FC<SystemStatusChartProps> = ({
    className = '',
    refreshInterval = 5000,
}) => {
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // 使用 useCallback 避免函數重新創建
    const loadSystemStatus = useCallback(async () => {
        try {
            setLoading(true)
            const data = await getSystemStatus()
            setSystemStatus(data)
            setError(null)
        } catch (err) {
            console.error('載入系統狀態失敗:', err)
            setError('無法載入系統狀態')
        } finally {
            setLoading(false)
        }
    }, [])

    // 組件掛載時載入數據
    useEffect(() => {
        loadSystemStatus()
    }, [loadSystemStatus])

    // 設置定時刷新
    useEffect(() => {
        if (refreshInterval > 0) {
            const interval = setInterval(loadSystemStatus, refreshInterval)
            return () => clearInterval(interval)
        }
    }, [refreshInterval, loadSystemStatus])

    // 獲取狀態顏色
    const getStatusColor = (status: string): string => {
        switch (status.toLowerCase()) {
            case 'healthy':
                return '#10b981' // green
            case 'degraded':
                return '#f59e0b' // yellow
            case 'error':
                return '#ef4444' // red
            default:
                return '#6b7280' // gray
        }
    }

    // 獲取健康狀態圖標
    const getHealthIcon = (healthy: boolean): string => {
        return healthy ? '✅' : '❌'
    }

    if (loading) {
        return (
            <div className={`system-status-chart ${className}`}>
                <div className="loading">
                    <div className="loading-spinner"></div>
                    <span>載入系統狀態中...</span>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className={`system-status-chart ${className}`}>
                <div className="error">
                    <span className="error-icon">⚠️</span>
                    <span>{error}</span>
                    <button onClick={loadSystemStatus} className="retry-button">
                        重試
                    </button>
                </div>
            </div>
        )
    }

    if (!systemStatus) {
        return (
            <div className={`system-status-chart ${className}`}>
                <div className="no-data">無系統狀態數據</div>
            </div>
        )
    }

    return (
        <div className={`system-status-chart ${className}`}>
            <div className="chart-header">
                <h3>系統狀態監控</h3>
                <div className="status-indicator">
                    <div
                        className="status-dot"
                        style={{
                            backgroundColor: getStatusColor(
                                systemStatus.status
                            ),
                        }}
                    ></div>
                    <span
                        className="status-text"
                        style={{
                            color: getStatusColor(systemStatus.status),
                        }}
                    >
                        {systemStatus.status}
                    </span>
                </div>
            </div>

            <div className="system-summary">
                <div className="summary-item">
                    <span className="label">總服務數</span>
                    <span className="value">
                        {systemStatus.summary.total_services}
                    </span>
                </div>
                <div className="summary-item">
                    <span className="label">健康服務</span>
                    <span className="value healthy">
                        {systemStatus.summary.healthy_services}
                    </span>
                </div>
                <div className="summary-item">
                    <span className="label">異常服務</span>
                    <span className="value degraded">
                        {systemStatus.summary.degraded_services}
                    </span>
                </div>
            </div>

            <div className="components-list">
                {Object.entries(systemStatus.components).map(
                    ([key, component]) => (
                        <div key={key} className="component-item">
                            <div className="component-header">
                                <span className="health-icon">
                                    {getHealthIcon(component.healthy)}
                                </span>
                                <span className="component-name">
                                    {component.name}
                                </span>
                                <span className="component-version">
                                    v{component.version}
                                </span>
                                <span
                                    className="component-status"
                                    style={{
                                        color: getStatusColor(component.status),
                                    }}
                                >
                                    {component.status}
                                </span>
                            </div>

                            {component.metrics && (
                                <div className="component-metrics">
                                    <div className="metric">
                                        <span className="metric-label">
                                            CPU 使用率:
                                        </span>
                                        <span className="metric-value">
                                            {component.metrics.cpu_usage}%
                                        </span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">
                                            記憶體使用率:
                                        </span>
                                        <span className="metric-value">
                                            {component.metrics.memory_usage}%
                                        </span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">
                                            活躍連接:
                                        </span>
                                        <span className="metric-value">
                                            {
                                                component.metrics
                                                    .active_connections
                                            }
                                        </span>
                                    </div>
                                </div>
                            )}

                            {component.error && (
                                <div className="component-error">
                                    <span className="error-text">
                                        {component.error}
                                    </span>
                                </div>
                            )}

                            <div className="component-footer">
                                最後健康檢查:{' '}
                                {new Date(
                                    component.last_health_check
                                ).toLocaleString()}
                            </div>
                        </div>
                    )
                )}
            </div>

            <div className="chart-footer">
                最後更新: {new Date(systemStatus.timestamp).toLocaleString()}
            </div>
        </div>
    )
}

export default SystemStatusChart
