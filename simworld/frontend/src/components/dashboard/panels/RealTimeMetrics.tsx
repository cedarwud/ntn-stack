import React, { useState, useEffect } from 'react'
import './PanelCommon.scss'

interface RealTimeMetricsProps {
    wsData: any
    connected: boolean
    style?: React.CSSProperties
    isFullscreen?: boolean
    onFullscreen?: () => void
    currentScene: string
}

interface MetricItem {
    label: string
    value: string | number
    unit?: string
    trend?: 'up' | 'down' | 'stable'
    color?: string
}

const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({
    wsData,
    connected,
    style,
    isFullscreen,
    onFullscreen,
    currentScene,
}) => {
    const [metrics, setMetrics] = useState<MetricItem[]>([])
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

    useEffect(() => {
        if (wsData) {
            const newMetrics: MetricItem[] = [
                {
                    label: 'CPU 使用率',
                    value: wsData.system_metrics?.cpu_usage_percent || 0,
                    unit: '%',
                    trend: 'stable',
                    color: '#4CAF50',
                },
                {
                    label: '記憶體使用',
                    value: wsData.system_metrics?.memory_usage_mb || 0,
                    unit: 'MB',
                    trend: 'up',
                    color: '#2196F3',
                },
                {
                    label: '網路吞吐量',
                    value: wsData.network_metrics?.throughput_mbps || 0,
                    unit: 'Mbps',
                    trend: 'stable',
                    color: '#FF9800',
                },
                {
                    label: '延遲',
                    value: wsData.network_metrics?.latency_ms || 0,
                    unit: 'ms',
                    trend: 'down',
                    color: '#9C27B0',
                },
                {
                    label: '活躍連接',
                    value: wsData.connection_metrics?.active_connections || 0,
                    unit: '',
                    trend: 'stable',
                    color: '#607D8B',
                },
                {
                    label: '錯誤率',
                    value: wsData.system_metrics?.error_rate_percent || 0,
                    unit: '%',
                    trend: 'down',
                    color: '#F44336',
                },
            ]

            setMetrics(newMetrics)
            setLastUpdate(new Date())
        }
    }, [wsData])

    const getTrendIcon = (trend?: string) => {
        switch (trend) {
            case 'up':
                return '📈'
            case 'down':
                return '📉'
            case 'stable':
                return '➡️'
            default:
                return '➡️'
        }
    }

    const formatValue = (value: string | number, unit?: string) => {
        const numValue =
            typeof value === 'number' ? value : parseFloat(value.toString())
        if (isNaN(numValue)) return 'N/A'

        const formatted = numValue.toFixed(1)
        return unit ? `${formatted} ${unit}` : formatted
    }

    return (
        <div
            className={`panel real-time-metrics ${
                isFullscreen ? 'fullscreen' : ''
            }`}
            style={style}
        >
            <div className="panel-header">
                <h3>實時指標</h3>
                <div className="panel-controls">
                    <div
                        className={`connection-status ${
                            connected ? 'connected' : 'disconnected'
                        }`}
                    >
                        <span className="status-dot"></span>
                        {connected ? '即時連線' : '連線中斷'}
                    </div>
                    <button className="fullscreen-btn" onClick={onFullscreen}>
                        {isFullscreen ? '🗗' : '🗖'}
                    </button>
                </div>
            </div>

            <div className="panel-content">
                {!connected && (
                    <div className="error-state">
                        <p>⚠️ WebSocket 連線中斷</p>
                        <small>正在嘗試重新連線...</small>
                    </div>
                )}

                {connected && (
                    <div className="metrics-container">
                        <div className="metrics-grid">
                            {metrics.map((metric, index) => (
                                <div
                                    key={index}
                                    className="metric-card real-time"
                                    style={{ borderLeftColor: metric.color }}
                                >
                                    <div className="metric-header">
                                        <span className="metric-label">
                                            {metric.label}
                                        </span>
                                        <span className="trend-icon">
                                            {getTrendIcon(metric.trend)}
                                        </span>
                                    </div>
                                    <div className="metric-value">
                                        {formatValue(metric.value, metric.unit)}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {lastUpdate && (
                            <div className="last-update">
                                最後更新: {lastUpdate.toLocaleTimeString()}
                            </div>
                        )}

                        {/* 即時統計摘要 */}
                        <div className="summary-section">
                            <h4>系統摘要</h4>
                            <div className="summary-grid">
                                <div className="summary-item">
                                    <span className="summary-label">
                                        連線狀態
                                    </span>
                                    <span
                                        className={`summary-value ${
                                            connected ? 'good' : 'bad'
                                        }`}
                                    >
                                        {connected ? '正常' : '異常'}
                                    </span>
                                </div>
                                <div className="summary-item">
                                    <span className="summary-label">
                                        數據新鮮度
                                    </span>
                                    <span className="summary-value good">
                                        實時
                                    </span>
                                </div>
                                <div className="summary-item">
                                    <span className="summary-label">
                                        系統負載
                                    </span>
                                    <span className="summary-value good">
                                        正常
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default RealTimeMetrics
