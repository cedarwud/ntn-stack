/**
 * 系統健康狀態查看器組件
 * 階段8：整合 Prometheus 系統監控數據
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Line } from 'react-chartjs-2'
import { prometheusApiService, PrometheusTarget } from '../../services/systemMonitoringApi'
import './SystemHealthViewer.scss'

interface SystemHealthViewerProps {
    className?: string
    autoRefresh?: boolean
    refreshInterval?: number
    showCharts?: boolean
}

interface SystemMetrics {
    cpuUsage: number
    memoryUsage: number
    diskUsage: number
    networkRx: number
    networkTx: number
}

interface ServiceHealth {
    prometheus: boolean
    grafana: boolean
    alertmanager: boolean
    netstack: boolean
    simworld: boolean
}

const SystemHealthViewer: React.FC<SystemHealthViewerProps> = ({
    className = '',
    autoRefresh = true,
    refreshInterval = 3000,
    showCharts = true
}) => {
    const [metrics, setMetrics] = useState<SystemMetrics>({
        cpuUsage: 0,
        memoryUsage: 0,
        diskUsage: 0,
        networkRx: 0,
        networkTx: 0
    })
    
    const [serviceHealth, setServiceHealth] = useState<ServiceHealth>({
        prometheus: false,
        grafana: false,
        alertmanager: false,
        netstack: false,
        simworld: false
    })
    
    const [targets, setTargets] = useState<PrometheusTarget[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
    const [historicalData, setHistoricalData] = useState<{
        labels: string[]
        cpu: number[]
        memory: number[]
        network: number[]
    }>({
        labels: [],
        cpu: [],
        memory: [],
        network: []
    })

    // 獲取系統健康數據
    const fetchSystemHealth = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)

            // 並行獲取各種監控數據
            const [systemMetrics, targetsResult, prometheusHealth, alertManagerHealth] = await Promise.all([
                prometheusApiService.getSystemHealthMetrics(),
                prometheusApiService.getTargetStatus(),
                prometheusApiService.checkHealth(),
                prometheusApiService.checkAlertManagerHealth()
            ])

            // 解析系統指標
            const parsedMetrics: SystemMetrics = {
                cpuUsage: systemMetrics.cpuUsage.data.result[0]?.value?.[1] 
                    ? parseFloat(systemMetrics.cpuUsage.data.result[0].value[1]) 
                    : 0,
                memoryUsage: systemMetrics.memoryUsage.data.result[0]?.value?.[1] 
                    ? parseFloat(systemMetrics.memoryUsage.data.result[0].value[1]) 
                    : 0,
                diskUsage: systemMetrics.diskUsage.data.result[0]?.value?.[1] 
                    ? parseFloat(systemMetrics.diskUsage.data.result[0].value[1]) 
                    : 0,
                networkRx: systemMetrics.networkRx.data.result[0]?.value?.[1] 
                    ? parseFloat(systemMetrics.networkRx.data.result[0].value[1]) 
                    : 0,
                networkTx: 0 // 可以添加網路發送監控
            }

            setMetrics(parsedMetrics)

            // 解析監控目標狀態
            if (targetsResult.status === 'success') {
                setTargets(targetsResult.data.activeTargets)
                
                // 解析服務健康狀態
                const health: ServiceHealth = {
                    prometheus: prometheusHealth,
                    grafana: targetsResult.data.activeTargets.some(t => t.labels.job === 'grafana' && t.health === 'up'),
                    alertmanager: alertManagerHealth,
                    netstack: targetsResult.data.activeTargets.some(t => t.labels.job?.includes('netstack') && t.health === 'up'),
                    simworld: targetsResult.data.activeTargets.some(t => t.labels.job?.includes('simworld') && t.health === 'up')
                }
                
                setServiceHealth(health)
            }

            // 更新歷史數據 (用於圖表)
            if (showCharts) {
                setHistoricalData(prev => {
                    const now = new Date().toLocaleTimeString('zh-TW', { 
                        hour: '2-digit', 
                        minute: '2-digit', 
                        second: '2-digit' 
                    })
                    
                    const newLabels = [...prev.labels, now].slice(-20) // 保留最近20個點
                    const newCpu = [...prev.cpu, parsedMetrics.cpuUsage].slice(-20)
                    const newMemory = [...prev.memory, parsedMetrics.memoryUsage].slice(-20)
                    const newNetwork = [...prev.network, parsedMetrics.networkRx / (1024 * 1024)].slice(-20) // 轉換為 MB/s

                    return {
                        labels: newLabels,
                        cpu: newCpu,
                        memory: newMemory,
                        network: newNetwork
                    }
                })
            }

            setLastUpdate(new Date())
        } catch (err) {
            console.error('獲取系統健康數據失敗:', err)
            setError(err instanceof Error ? err.message : '未知錯誤')
        } finally {
            setLoading(false)
        }
    }, [showCharts])

    // 自動刷新邏輯
    useEffect(() => {
        fetchSystemHealth()

        if (autoRefresh && refreshInterval > 0) {
            const interval = setInterval(fetchSystemHealth, refreshInterval)
            return () => clearInterval(interval)
        }
    }, [fetchSystemHealth, autoRefresh, refreshInterval])

    // 獲取健康狀態顏色
    const getHealthColor = (isHealthy: boolean): string => {
        return isHealthy ? '#4caf50' : '#f44336'
    }

    // 獲取指標狀態樣式
    const getMetricStatusClass = (value: number, thresholds: { warning: number; critical: number }): string => {
        if (value >= thresholds.critical) return 'critical'
        if (value >= thresholds.warning) return 'warning'
        return 'normal'
    }

    // 格式化網路流量
    const formatNetworkTraffic = (bytes: number): string => {
        if (bytes === 0) return '0 B/s'
        const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s']
        const i = Math.floor(Math.log(bytes) / Math.log(1024))
        return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`
    }

    // 圖表配置
    const chartData = {
        labels: historicalData.labels,
        datasets: [
            {
                label: 'CPU 使用率 (%)',
                data: historicalData.cpu,
                borderColor: '#2196f3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                fill: true,
                tension: 0.4
            },
            {
                label: '記憶體使用率 (%)',
                data: historicalData.memory,
                borderColor: '#ff9800',
                backgroundColor: 'rgba(255, 152, 0, 0.1)',
                fill: true,
                tension: 0.4
            },
            {
                label: '網路流量 (MB/s)',
                data: historicalData.network,
                borderColor: '#4caf50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                fill: true,
                tension: 0.4,
                yAxisID: 'y1'
            }
        ]
    }

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#e0e0e0'
                }
            }
        },
        scales: {
            x: {
                ticks: { color: '#888' },
                grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y: {
                type: 'linear' as const,
                display: true,
                position: 'left' as const,
                min: 0,
                max: 100,
                ticks: { 
                    color: '#888',
                    callback: function(value: number | string) {
                        return value + '%'
                    }
                },
                grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            y1: {
                type: 'linear' as const,
                display: true,
                position: 'right' as const,
                min: 0,
                ticks: { 
                    color: '#888',
                    callback: function(value: number | string) {
                        return value + ' MB/s'
                    }
                },
                grid: { drawOnChartArea: false }
            }
        }
    }

    return (
        <div className={`system-health-viewer ${className}`}>
            {/* 標題與狀態 */}
            <div className="health-header">
                <div className="health-title">
                    <h3>💻 系統健康狀態 (階段8)</h3>
                    {lastUpdate && (
                        <span className="last-update">
                            最後更新: {lastUpdate.toLocaleTimeString('zh-TW')}
                        </span>
                    )}
                </div>
                <button 
                    className="refresh-btn"
                    onClick={fetchSystemHealth}
                    disabled={loading}
                >
                    {loading ? '⏳' : '🔄'} 刷新
                </button>
            </div>

            {/* 錯誤狀態 */}
            {error && (
                <div className="error-state">
                    <span className="error-icon">❌</span>
                    <span className="error-message">{error}</span>
                </div>
            )}

            {/* 服務狀態 */}
            <div className="services-health">
                <h4>🔧 服務狀態</h4>
                <div className="services-grid">
                    <div className="service-item">
                        <span className="service-icon">📊</span>
                        <span className="service-name">Prometheus</span>
                        <span 
                            className="service-status"
                            style={{ color: getHealthColor(serviceHealth.prometheus) }}
                        >
                            {serviceHealth.prometheus ? '🟢 在線' : '🔴 離線'}
                        </span>
                    </div>
                    
                    <div className="service-item">
                        <span className="service-icon">📈</span>
                        <span className="service-name">Grafana</span>
                        <span 
                            className="service-status"
                            style={{ color: getHealthColor(serviceHealth.grafana) }}
                        >
                            {serviceHealth.grafana ? '🟢 在線' : '🔴 離線'}
                        </span>
                    </div>
                    
                    <div className="service-item">
                        <span className="service-icon">🚨</span>
                        <span className="service-name">AlertManager</span>
                        <span 
                            className="service-status"
                            style={{ color: getHealthColor(serviceHealth.alertmanager) }}
                        >
                            {serviceHealth.alertmanager ? '🟢 在線' : '🔴 離線'}
                        </span>
                    </div>
                    
                    <div className="service-item">
                        <span className="service-icon">🌐</span>
                        <span className="service-name">NetStack</span>
                        <span 
                            className="service-status"
                            style={{ color: getHealthColor(serviceHealth.netstack) }}
                        >
                            {serviceHealth.netstack ? '🟢 在線' : '🔴 離線'}
                        </span>
                    </div>
                    
                    <div className="service-item">
                        <span className="service-icon">🛰️</span>
                        <span className="service-name">SimWorld</span>
                        <span 
                            className="service-status"
                            style={{ color: getHealthColor(serviceHealth.simworld) }}
                        >
                            {serviceHealth.simworld ? '🟢 在線' : '🔴 離線'}
                        </span>
                    </div>
                </div>
            </div>

            {/* 系統指標 */}
            <div className="system-metrics">
                <h4>⚡ 系統指標</h4>
                <div className="metrics-grid">
                    <div className={`metric-item ${getMetricStatusClass(metrics.cpuUsage, { warning: 70, critical: 85 })}`}>
                        <div className="metric-header">
                            <span className="metric-icon">🖥️</span>
                            <span className="metric-name">CPU 使用率</span>
                        </div>
                        <div className="metric-value">
                            {metrics.cpuUsage.toFixed(1)}%
                        </div>
                        <div className="metric-bar">
                            <div 
                                className="metric-fill"
                                style={{ width: `${Math.min(metrics.cpuUsage, 100)}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className={`metric-item ${getMetricStatusClass(metrics.memoryUsage, { warning: 75, critical: 90 })}`}>
                        <div className="metric-header">
                            <span className="metric-icon">💾</span>
                            <span className="metric-name">記憶體使用率</span>
                        </div>
                        <div className="metric-value">
                            {metrics.memoryUsage.toFixed(1)}%
                        </div>
                        <div className="metric-bar">
                            <div 
                                className="metric-fill"
                                style={{ width: `${Math.min(metrics.memoryUsage, 100)}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className={`metric-item ${getMetricStatusClass(metrics.diskUsage, { warning: 80, critical: 90 })}`}>
                        <div className="metric-header">
                            <span className="metric-icon">💿</span>
                            <span className="metric-name">磁碟使用率</span>
                        </div>
                        <div className="metric-value">
                            {metrics.diskUsage.toFixed(1)}%
                        </div>
                        <div className="metric-bar">
                            <div 
                                className="metric-fill"
                                style={{ width: `${Math.min(metrics.diskUsage, 100)}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="metric-item normal">
                        <div className="metric-header">
                            <span className="metric-icon">📡</span>
                            <span className="metric-name">網路流量</span>
                        </div>
                        <div className="metric-value">
                            {formatNetworkTraffic(metrics.networkRx)}
                        </div>
                        <div className="metric-description">
                            接收流量
                        </div>
                    </div>
                </div>
            </div>

            {/* 歷史圖表 */}
            {showCharts && historicalData.labels.length > 1 && (
                <div className="system-charts">
                    <h4>📊 歷史趨勢</h4>
                    <div className="chart-container">
                        <Line data={chartData} options={chartOptions} />
                    </div>
                </div>
            )}

            {/* 監控目標狀態 */}
            {targets.length > 0 && (
                <div className="monitoring-targets">
                    <h4>🎯 監控目標 ({targets.length})</h4>
                    <div className="targets-list">
                        {targets.slice(0, 6).map((target, index) => (
                            <div key={index} className="target-item">
                                <div className="target-info">
                                    <span className="target-job">{target.labels.job || '未知'}</span>
                                    <span className="target-url">{target.scrapeUrl}</span>
                                </div>
                                <span 
                                    className={`target-health ${target.health}`}
                                >
                                    {target.health === 'up' ? '🟢' : '🔴'} {target.health}
                                </span>
                            </div>
                        ))}
                        {targets.length > 6 && (
                            <div className="targets-more">
                                +{targets.length - 6} 個更多目標
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

export default SystemHealthViewer