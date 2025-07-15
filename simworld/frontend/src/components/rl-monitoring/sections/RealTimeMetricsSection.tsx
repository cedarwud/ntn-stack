import React, { memo, useState, useEffect } from 'react'
import './RealTimeMetricsSection.scss'

interface RealTimeMetricsSectionProps {
    data?: {
        metrics: {
            timestamp: string
            system_status: 'healthy' | 'warning' | 'error'
            active_algorithms: string[]
            resource_usage: {
                cpu_percent: number
                memory_percent: number
                gpu_percent?: number
            }
            performance_indicators: {
                avg_response_time: number
                success_rate: number
                error_count: number
            }
        }
        events: Array<{
            event_id: string
            event_type: 'A4' | 'D1' | 'D2' | 'T1' | 'custom'
            timestamp: string
            source_satellite: string
            target_satellite: string
            algorithm_decision: string
            success: boolean
            metrics: {
                latency_ms: number
                signal_strength: number
                handover_delay: number
            }
        }>
        status: {
            overall_health: 'healthy' | 'degraded' | 'critical'
            services: Record<string, 'up' | 'down' | 'maintenance'>
            last_updated: string
            uptime: number
            error_logs: Array<{
                timestamp: string
                level: 'info' | 'warning' | 'error'
                message: string
                component: string
            }>
        }
    }
    onRefresh?: () => void
}

const RealTimeMetricsSection: React.FC<RealTimeMetricsSectionProps> = ({
    data,
    onRefresh,
}) => {
    const [connectionStatus, setConnectionStatus] = useState<
        'connected' | 'disconnected' | 'connecting'
    >('connecting')
    const [realtimeData, setRealtimeData] = useState(data)
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

    // 模擬 WebSocket 連接
    useEffect(() => {
        const simulateConnection = () => {
            setConnectionStatus('connected')

            // 模擬實時數據更新
            const interval = setInterval(() => {
                setLastUpdate(new Date())

                // 模擬數據變化
                if (Math.random() < 0.3) {
                    // 30% 機率更新數據
                    setRealtimeData(
                        (prevData) =>
                            ({
                                ...prevData,
                                metrics: {
                                    ...prevData?.metrics,
                                    timestamp: new Date().toISOString(),
                                    resource_usage: {
                                        cpu_percent: Math.random() * 100,
                                        memory_percent: Math.random() * 100,
                                        gpu_percent: Math.random() * 100,
                                    },
                                    performance_indicators: {
                                        avg_response_time:
                                            50 + Math.random() * 100,
                                        success_rate:
                                            0.85 + Math.random() * 0.15,
                                        error_count: Math.floor(
                                            Math.random() * 5
                                        ),
                                    },
                                },
                            } as any)
                    )
                }
            }, 2000)

            return () => clearInterval(interval)
        }

        const cleanup = simulateConnection()
        return cleanup
    }, [])

    const currentData = realtimeData || data
    const metrics = currentData?.metrics
    const events = currentData?.events || []
    const systemStatus = currentData?.status

    // 獲取狀態顏色
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'healthy':
                return '#10b981'
            case 'warning':
                return '#f59e0b'
            case 'error':
            case 'critical':
                return '#ef4444'
            case 'degraded':
                return '#f97316'
            default:
                return '#6b7280'
        }
    }

    // 獲取資源使用等級
    const getResourceLevel = (percentage: number) => {
        if (percentage >= 90) return { level: 'critical', color: '#ef4444' }
        if (percentage >= 75) return { level: 'warning', color: '#f59e0b' }
        if (percentage >= 50) return { level: 'normal', color: '#10b981' }
        return { level: 'low', color: '#3b82f6' }
    }

    return (
        <div className="realtime-metrics-section">
            <div className="section-header">
                <h2 className="section-title">⚡ 實時系統監控</h2>
                <div className="connection-status">
                    <div
                        className={`status-indicator status-indicator--${connectionStatus}`}
                    >
                        <div className="status-dot"></div>
                        <span className="status-text">
                            {connectionStatus === 'connected' &&
                                'WebSocket 已連接'}
                            {connectionStatus === 'disconnected' &&
                                'WebSocket 已斷線'}
                            {connectionStatus === 'connecting' &&
                                'WebSocket 連接中...'}
                        </span>
                        <span className="last-update">
                            最後更新: {lastUpdate.toLocaleTimeString()}
                        </span>
                    </div>
                </div>
            </div>

            {/* 系統健康狀態 */}
            <div className="system-health-overview">
                <div className="health-card">
                    <div className="health-header">
                        <h3 className="health-title">🏥 系統健康狀態</h3>
                        <div
                            className="health-status-badge"
                            style={{
                                backgroundColor: getStatusColor(
                                    systemStatus?.overall_health || 'healthy'
                                ),
                                color: 'white',
                            }}
                        >
                            {systemStatus?.overall_health || 'healthy'}
                        </div>
                    </div>

                    <div className="health-metrics">
                        <div className="health-metric">
                            <div className="metric-icon">⏱️</div>
                            <div className="metric-info">
                                <div className="metric-label">系統運行時間</div>
                                <div className="metric-value">
                                    {Math.floor(
                                        (systemStatus?.uptime || 0) / 3600
                                    )}
                                    h{' '}
                                    {Math.floor(
                                        ((systemStatus?.uptime || 0) % 3600) /
                                            60
                                    )}
                                    m
                                </div>
                            </div>
                        </div>

                        <div className="health-metric">
                            <div className="metric-icon">🎯</div>
                            <div className="metric-info">
                                <div className="metric-label">活躍算法</div>
                                <div className="metric-value">
                                    {metrics?.active_algorithms?.length || 0} /
                                    3
                                </div>
                            </div>
                        </div>

                        <div className="health-metric">
                            <div className="metric-icon">📊</div>
                            <div className="metric-info">
                                <div className="metric-label">成功率</div>
                                <div className="metric-value">
                                    {(
                                        (metrics?.performance_indicators
                                            ?.success_rate || 0) * 100
                                    ).toFixed(1)}
                                    %
                                </div>
                            </div>
                        </div>

                        <div className="health-metric">
                            <div className="metric-icon">⚡</div>
                            <div className="metric-info">
                                <div className="metric-label">平均響應時間</div>
                                <div className="metric-value">
                                    {(
                                        metrics?.performance_indicators
                                            ?.avg_response_time || 0
                                    ).toFixed(1)}
                                    ms
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 資源使用監控 */}
            <div className="resource-monitoring">
                <h3 className="subsection-title">💻 資源使用情況</h3>
                <div className="resource-grid">
                    <div className="resource-card">
                        <div className="resource-header">
                            <span className="resource-icon">🖥️</span>
                            <span className="resource-name">CPU 使用率</span>
                        </div>
                        <div className="resource-content">
                            <div className="resource-percentage">
                                {(
                                    metrics?.resource_usage?.cpu_percent || 0
                                ).toFixed(1)}
                                %
                            </div>
                            <div className="resource-bar">
                                <div
                                    className="resource-fill"
                                    style={{
                                        width: `${
                                            metrics?.resource_usage
                                                ?.cpu_percent || 0
                                        }%`,
                                        backgroundColor: getResourceLevel(
                                            metrics?.resource_usage
                                                ?.cpu_percent || 0
                                        ).color,
                                    }}
                                ></div>
                            </div>
                            <div className="resource-status">
                                {
                                    getResourceLevel(
                                        metrics?.resource_usage?.cpu_percent ||
                                            0
                                    ).level
                                }
                            </div>
                        </div>
                    </div>

                    <div className="resource-card">
                        <div className="resource-header">
                            <span className="resource-icon">🧠</span>
                            <span className="resource-name">記憶體使用率</span>
                        </div>
                        <div className="resource-content">
                            <div className="resource-percentage">
                                {(
                                    metrics?.resource_usage?.memory_percent || 0
                                ).toFixed(1)}
                                %
                            </div>
                            <div className="resource-bar">
                                <div
                                    className="resource-fill"
                                    style={{
                                        width: `${
                                            metrics?.resource_usage
                                                ?.memory_percent || 0
                                        }%`,
                                        backgroundColor: getResourceLevel(
                                            metrics?.resource_usage
                                                ?.memory_percent || 0
                                        ).color,
                                    }}
                                ></div>
                            </div>
                            <div className="resource-status">
                                {
                                    getResourceLevel(
                                        metrics?.resource_usage
                                            ?.memory_percent || 0
                                    ).level
                                }
                            </div>
                        </div>
                    </div>

                    <div className="resource-card">
                        <div className="resource-header">
                            <span className="resource-icon">🎮</span>
                            <span className="resource-name">GPU 使用率</span>
                        </div>
                        <div className="resource-content">
                            <div className="resource-percentage">
                                {(
                                    metrics?.resource_usage?.gpu_percent || 0
                                ).toFixed(1)}
                                %
                            </div>
                            <div className="resource-bar">
                                <div
                                    className="resource-fill"
                                    style={{
                                        width: `${
                                            metrics?.resource_usage
                                                ?.gpu_percent || 0
                                        }%`,
                                        backgroundColor: getResourceLevel(
                                            metrics?.resource_usage
                                                ?.gpu_percent || 0
                                        ).color,
                                    }}
                                ></div>
                            </div>
                            <div className="resource-status">
                                {
                                    getResourceLevel(
                                        metrics?.resource_usage?.gpu_percent ||
                                            0
                                    ).level
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 活躍算法狀態 */}
            <div className="active-algorithms">
                <h3 className="subsection-title">🎯 活躍算法狀態</h3>
                <div className="algorithms-status">
                    {['DQN', 'PPO', 'SAC'].map((algorithm) => {
                        const isActive = metrics?.active_algorithms?.includes(
                            algorithm.toLowerCase()
                        )
                        return (
                            <div
                                key={algorithm}
                                className={`algorithm-status-card ${
                                    isActive ? 'active' : 'inactive'
                                }`}
                            >
                                <div className="algorithm-status-header">
                                    <span className="algorithm-name">
                                        {algorithm}
                                    </span>
                                    <div
                                        className={`status-dot ${
                                            isActive ? 'active' : 'inactive'
                                        }`}
                                    ></div>
                                </div>
                                <div className="algorithm-status-body">
                                    <div className="status-text">
                                        {isActive ? '🔄 訓練中' : '⏸️ 閒置'}
                                    </div>
                                    {isActive && (
                                        <div className="training-info">
                                            <div className="training-metric">
                                                <span>獎勵: </span>
                                                <span>
                                                    {(
                                                        Math.random() * 0.5 +
                                                        0.4
                                                    ).toFixed(3)}
                                                </span>
                                            </div>
                                            <div className="training-metric">
                                                <span>輪次: </span>
                                                <span>
                                                    {Math.floor(
                                                        Math.random() * 30
                                                    )}
                                                    /30
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* 實時事件流 */}
            <div className="realtime-events">
                <h3 className="subsection-title">📡 實時事件流</h3>
                <div className="events-container">
                    {events.length === 0 ? (
                        <div className="no-events-message">
                            <div className="no-events-icon">📡</div>
                            <div className="no-events-text">暫無實時事件</div>
                            <div className="no-events-subtext">
                                換手事件將在此處即時顯示
                            </div>
                        </div>
                    ) : (
                        <div className="events-list">
                            {events.slice(0, 5).map((event, index) => (
                                <div
                                    key={event.event_id || index}
                                    className={`event-item ${
                                        event.success ? 'success' : 'failure'
                                    }`}
                                >
                                    <div className="event-header">
                                        <div className="event-type-badge">
                                            {event.event_type}
                                        </div>
                                        <div className="event-timestamp">
                                            {new Date(
                                                event.timestamp
                                            ).toLocaleTimeString()}
                                        </div>
                                        <div
                                            className={`event-status ${
                                                event.success
                                                    ? 'success'
                                                    : 'failure'
                                            }`}
                                        >
                                            {event.success ? '✅' : '❌'}
                                        </div>
                                    </div>
                                    <div className="event-details">
                                        <div className="handover-info">
                                            {event.source_satellite} →{' '}
                                            {event.target_satellite}
                                        </div>
                                        <div className="algorithm-decision">
                                            算法: {event.algorithm_decision}
                                        </div>
                                        <div className="event-metrics">
                                            <span>
                                                延遲: {event.metrics.latency_ms}
                                                ms
                                            </span>
                                            <span>
                                                信號:{' '}
                                                {event.metrics.signal_strength.toFixed(
                                                    2
                                                )}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default memo(RealTimeMetricsSection)
