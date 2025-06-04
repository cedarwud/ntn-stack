/**
 * NTN Stack 統一儀表板
 * 整合所有系統監控和可視化功能
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from 'recharts'
import useWebSocket from '../../hooks/useWebSocket'
import { Card, Alert, Spin, Progress, Tag, Badge, Statistic } from './ui'
import UAVMetricsChart from './charts/UAVMetricsChart'
import NetworkTopologyChart from './charts/NetworkTopologyChart'

interface NTNStackDashboardProps {
    className?: string
}

interface MetricData {
    timestamp: string
    value: number
    labels: Record<string, string>
    source: string
}

interface SystemHealthData {
    status: 'healthy' | 'warning' | 'critical'
    services: {
        netstack: boolean
        simworld: boolean
        open5gs: boolean
        ueransim: boolean
    }
    uptime: number
    version: string
}

interface UAVMetrics {
    uav_id: string
    latency_ms: number
    sinr_db: number
    rsrp_dbm: number
    throughput_mbps: number
    connection_type: string
    cell_id: string
    position: [number, number, number]
    battery_percent: number
    status: 'connected' | 'disconnected' | 'error'
}

interface AIRANMetrics {
    decision_accuracy: number
    interference_events: number
    mitigation_success_rate: number
    model_training_status: 'idle' | 'training' | 'converged'
    last_decision_time: string
    active_strategies: string[]
}

interface SionnaMetrics {
    gpu_utilization: number[]
    memory_usage_mb: number[]
    simulation_fps: number
    active_scenarios: number
    computation_queue_size: number
    last_simulation_time: number
}

const NTNStackDashboard: React.FC<NTNStackDashboardProps> = ({
    className = '',
}) => {
    // 狀態管理
    const [activeTab, setActiveTab] = useState<
        'overview' | 'uav' | 'network' | 'ai' | 'performance'
    >('overview')
    const [isRealtime, setIsRealtime] = useState(true)
    const [refreshInterval, setRefreshInterval] = useState(5000)
    const [timeRange, setTimeRange] = useState('1h')

    // 數據狀態
    const [systemHealth, setSystemHealth] = useState<SystemHealthData | null>(
        null
    )
    const [uavMetrics, setUAVMetrics] = useState<UAVMetrics[]>([])
    const [airanMetrics, setAIRANMetrics] = useState<AIRANMetrics | null>(null)
    const [sionnaMetrics, setSionnaMetrics] = useState<SionnaMetrics | null>(
        null
    )
    const [metricsHistory, setMetricsHistory] = useState<MetricData[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // WebSocket 連接
    const { isConnected, connectionStatus } = useWebSocket({
        url: '/api/ws/metrics',
        enableReconnect: isRealtime,
        maxReconnectAttempts: 5,
        reconnectInterval: 3000,
        onMessage: handleRealtimeUpdate,
        onConnect: () => {
            console.log('儀表板實時連接已建立')
        },
        onDisconnect: () => {
            console.log('儀表板實時連接已斷開')
        },
    })

    // 實時數據更新處理
    function handleRealtimeUpdate(event: any) {
        try {
            const data = JSON.parse(event.data)

            switch (data.type) {
                case 'system_health':
                    setSystemHealth(data.payload)
                    break
                case 'uav_metrics':
                    setUAVMetrics(data.payload)
                    break
                case 'ai_ran_metrics':
                    setAIRANMetrics(data.payload)
                    break
                case 'sionna_metrics':
                    setSionnaMetrics(data.payload)
                    break
                case 'metrics_batch':
                    updateMetricsHistory(data.payload)
                    break
                default:
                    break
            }
        } catch (err) {
            console.error('處理實時數據失敗:', err)
        }
    }

    // 更新歷史指標
    const updateMetricsHistory = useCallback(
        (newMetrics: MetricData[]) => {
            setMetricsHistory((prev) => {
                const updated = [...prev, ...newMetrics]
                const cutoff = Date.now() - getTimeRangeMs(timeRange)
                return updated.filter(
                    (m) => new Date(m.timestamp).getTime() > cutoff
                )
            })
        },
        [timeRange]
    )

    // 獲取時間範圍毫秒數
    const getTimeRangeMs = (range: string): number => {
        const multipliers = {
            '1h': 3600000,
            '6h': 21600000,
            '24h': 86400000,
            '7d': 604800000,
        }
        return multipliers[range as keyof typeof multipliers] || 3600000
    }

    // 數據加載
    const loadDashboardData = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)

            const [healthRes, uavRes, aiRes, sionnaRes, metricsRes] =
                await Promise.all([
                    fetch('/api/v1/system/health'),
                    fetch('/api/v1/uav/metrics'),
                    fetch('/api/v1/ai-ran/metrics'),
                    fetch('/api/v1/sionna/metrics'),
                    fetch(`/api/v1/metrics/history?range=${timeRange}`),
                ])

            if (healthRes.ok) {
                setSystemHealth(await healthRes.json())
            }

            if (uavRes.ok) {
                const uavData = await uavRes.json()
                setUAVMetrics(uavData.uav_metrics || [])
            }

            if (aiRes.ok) {
                setAIRANMetrics(await aiRes.json())
            }

            if (sionnaRes.ok) {
                setSionnaMetrics(await sionnaRes.json())
            }

            if (metricsRes.ok) {
                const metricsData = await metricsRes.json()
                setMetricsHistory(metricsData.metrics || [])
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : '載入數據失敗')
        } finally {
            setLoading(false)
        }
    }, [timeRange])

    // 初始化和定時刷新
    useEffect(() => {
        loadDashboardData()

        if (!isRealtime) {
            const interval = setInterval(loadDashboardData, refreshInterval)
            return () => clearInterval(interval)
        }
    }, [loadDashboardData, isRealtime, refreshInterval])

    // 計算關鍵指標
    const keyMetrics = useMemo(() => {
        const connectedUAVs = uavMetrics.filter(
            (uav) => uav.status === 'connected'
        ).length
        const avgLatency =
            uavMetrics.reduce((sum, uav) => sum + uav.latency_ms, 0) /
                uavMetrics.length || 0
        const avgSINR =
            uavMetrics.reduce((sum, uav) => sum + uav.sinr_db, 0) /
                uavMetrics.length || 0
        const totalThroughput = uavMetrics.reduce(
            (sum, uav) => sum + uav.throughput_mbps,
            0
        )
        const systemUptime = systemHealth?.uptime || 0

        return {
            connectedUAVs,
            totalUAVs: uavMetrics.length,
            avgLatency: Math.round(avgLatency * 10) / 10,
            avgSINR: Math.round(avgSINR * 10) / 10,
            totalThroughput: Math.round(totalThroughput * 10) / 10,
            systemUptime: Math.round((systemUptime / 3600) * 10) / 10, // 小時
            connectionSuccessRate:
                (connectedUAVs / uavMetrics.length) * 100 || 0,
            aiDecisionAccuracy: airanMetrics?.decision_accuracy || 0,
            gpuUtilization: sionnaMetrics?.gpu_utilization?.[0] || 0,
        }
    }, [uavMetrics, systemHealth, airanMetrics, sionnaMetrics])

    // 標籤配置
    const tabs = [
        { id: 'overview', label: '總覽', icon: '📊' },
        { id: 'uav', label: 'UAV 監控', icon: '🚁' },
        { id: 'network', label: '網路拓撲', icon: '🌐' },
        { id: 'ai', label: 'AI-RAN', icon: '🤖' },
        { id: 'performance', label: '性能分析', icon: '📈' },
    ] as const

    // 系統狀態顏色
    const getStatusColor = (status: string) => {
        const colors = {
            healthy: '#52c41a',
            warning: '#faad14',
            critical: '#ff4d4f',
            connected: '#52c41a',
            disconnected: '#ff4d4f',
            error: '#ff4d4f',
        }
        return colors[status as keyof typeof colors] || '#d9d9d9'
    }

    // 渲染總覽標籤
    const renderOverviewTab = () => (
        <div className="overview-container">
            {/* 關鍵指標卡片 */}
            <div className="metrics-grid">
                <Card title="系統狀態" className="status-card">
                    <div className="status-indicator">
                        <Badge
                            status={
                                systemHealth?.status === 'healthy'
                                    ? 'success'
                                    : 'error'
                            }
                            text={
                                systemHealth?.status?.toUpperCase() || 'UNKNOWN'
                            }
                        />
                        <div className="uptime-info">
                            運行時間: {keyMetrics.systemUptime}h
                        </div>
                    </div>
                </Card>

                <Card title="UAV 連接" className="uav-card">
                    <Statistic
                        title="連接成功率"
                        value={keyMetrics.connectionSuccessRate}
                        suffix="%"
                        precision={1}
                        valueStyle={{
                            color:
                                keyMetrics.connectionSuccessRate > 95
                                    ? '#3f8600'
                                    : '#cf1322',
                        }}
                    />
                    <div className="connection-count">
                        {keyMetrics.connectedUAVs} / {keyMetrics.totalUAVs}{' '}
                        已連接
                    </div>
                </Card>

                <Card title="端到端延遲" className="latency-card">
                    <Statistic
                        title="平均延遲"
                        value={keyMetrics.avgLatency}
                        suffix="ms"
                        precision={1}
                        valueStyle={{
                            color:
                                keyMetrics.avgLatency < 50
                                    ? '#3f8600'
                                    : '#cf1322',
                        }}
                    />
                    <Progress
                        percent={Math.min(
                            (keyMetrics.avgLatency / 100) * 100,
                            100
                        )}
                        status={
                            keyMetrics.avgLatency < 50 ? 'success' : 'exception'
                        }
                        size="small"
                    />
                </Card>

                <Card title="信號品質" className="signal-card">
                    <Statistic
                        title="平均 SINR"
                        value={keyMetrics.avgSINR}
                        suffix="dB"
                        precision={1}
                        valueStyle={{
                            color:
                                keyMetrics.avgSINR > 15 ? '#3f8600' : '#cf1322',
                        }}
                    />
                </Card>

                <Card title="AI 決策" className="ai-card">
                    <Statistic
                        title="決策準確性"
                        value={keyMetrics.aiDecisionAccuracy}
                        suffix="%"
                        precision={1}
                        valueStyle={{
                            color:
                                keyMetrics.aiDecisionAccuracy > 90
                                    ? '#3f8600'
                                    : '#cf1322',
                        }}
                    />
                    <div className="ai-status">
                        狀態: {airanMetrics?.model_training_status || 'Unknown'}
                    </div>
                </Card>

                <Card title="GPU 使用率" className="gpu-card">
                    <Statistic
                        title="GPU 0"
                        value={keyMetrics.gpuUtilization}
                        suffix="%"
                        precision={1}
                        valueStyle={{
                            color:
                                keyMetrics.gpuUtilization < 80
                                    ? '#3f8600'
                                    : '#cf1322',
                        }}
                    />
                    <Progress
                        percent={keyMetrics.gpuUtilization}
                        status={
                            keyMetrics.gpuUtilization < 80
                                ? 'active'
                                : 'exception'
                        }
                        size="small"
                    />
                </Card>
            </div>

            {/* 實時圖表 */}
            <div className="charts-grid">
                <Card title="UAV 延遲趨勢" className="chart-card">
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart
                            data={metricsHistory.filter(
                                (m) => m.source === 'uav'
                            )}
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="timestamp" />
                            <YAxis />
                            <Tooltip />
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke="#1890ff"
                                strokeWidth={2}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </Card>

                <Card title="系統資源使用" className="chart-card">
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart
                            data={metricsHistory.filter(
                                (m) => m.source === 'system'
                            )}
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="timestamp" />
                            <YAxis />
                            <Tooltip />
                            <Area
                                type="monotone"
                                dataKey="value"
                                stackId="1"
                                stroke="#52c41a"
                                fill="#52c41a"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </Card>
            </div>

            {/* 服務狀態表格 */}
            <Card title="服務狀態" className="services-card">
                <div className="services-grid">
                    {systemHealth &&
                        Object.entries(systemHealth.services).map(
                            ([service, status]) => (
                                <div key={service} className="service-item">
                                    <Badge
                                        status={status ? 'success' : 'error'}
                                        text={service.toUpperCase()}
                                    />
                                </div>
                            )
                        )}
                </div>
            </Card>
        </div>
    )

    // 渲染 UAV 監控標籤
    const renderUAVTab = () => (
        <div className="uav-container">
            <div className="uav-overview">
                <Card title="UAV 總覽" className="overview-card">
                    <div className="uav-stats">
                        <Statistic title="總數" value={keyMetrics.totalUAVs} />
                        <Statistic
                            title="在線"
                            value={keyMetrics.connectedUAVs}
                        />
                        <Statistic
                            title="平均延遲"
                            value={keyMetrics.avgLatency}
                            suffix="ms"
                        />
                        <Statistic
                            title="總吞吐量"
                            value={keyMetrics.totalThroughput}
                            suffix="Mbps"
                        />
                    </div>
                </Card>
            </div>

            <div className="uav-details">
                <UAVMetricsChart
                    refreshInterval={isRealtime ? 5000 : 0}
                    className="uav-chart"
                />

                <Card title="UAV 詳細列表" className="uav-list-card">
                    <div className="uav-list">
                        {uavMetrics.map((uav) => (
                            <div key={uav.uav_id} className="uav-item">
                                <div className="uav-header">
                                    <span className="uav-id">{uav.uav_id}</span>
                                    <Tag color={getStatusColor(uav.status)}>
                                        {uav.status}
                                    </Tag>
                                </div>
                                <div className="uav-metrics">
                                    <span>延遲: {uav.latency_ms}ms</span>
                                    <span>SINR: {uav.sinr_db}dB</span>
                                    <span>RSRP: {uav.rsrp_dbm}dBm</span>
                                    <span>電池: {uav.battery_percent}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </Card>
            </div>
        </div>
    )

    // 渲染 AI-RAN 標籤
    const renderAITab = () => (
        <div className="ai-container">
            <div className="ai-overview">
                <Card title="AI-RAN 狀態" className="ai-status-card">
                    <div className="ai-metrics">
                        <Statistic
                            title="決策準確性"
                            value={airanMetrics?.decision_accuracy || 0}
                            suffix="%"
                        />
                        <Statistic
                            title="干擾事件"
                            value={airanMetrics?.interference_events || 0}
                        />
                        <Statistic
                            title="緩解成功率"
                            value={airanMetrics?.mitigation_success_rate || 0}
                            suffix="%"
                        />
                    </div>
                    <div className="training-status">
                        <Tag
                            color={
                                airanMetrics?.model_training_status ===
                                'converged'
                                    ? 'green'
                                    : 'orange'
                            }
                        >
                            {airanMetrics?.model_training_status || 'Unknown'}
                        </Tag>
                    </div>
                </Card>
            </div>

            <div className="ai-charts">
                <Card title="決策準確性趨勢" className="chart-card">
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart
                            data={metricsHistory.filter(
                                (m) => m.source === 'ai-ran'
                            )}
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="timestamp" />
                            <YAxis />
                            <Tooltip />
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke="#722ed1"
                                strokeWidth={2}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </Card>

                <Card title="活躍策略" className="strategies-card">
                    <div className="strategies-list">
                        {airanMetrics?.active_strategies?.map((strategy) => (
                            <Tag key={strategy} color="blue">
                                {strategy}
                            </Tag>
                        )) || <span>無活躍策略</span>}
                    </div>
                </Card>
            </div>
        </div>
    )

    // 渲染性能分析標籤
    const renderPerformanceTab = () => (
        <div className="performance-container">
            <div className="performance-overview">
                <Card title="Sionna GPU 性能" className="gpu-performance-card">
                    <div className="gpu-metrics">
                        {sionnaMetrics?.gpu_utilization?.map((util, index) => (
                            <div key={index} className="gpu-item">
                                <span>GPU {index}</span>
                                <Progress percent={util} />
                                <span>
                                    {sionnaMetrics.memory_usage_mb[index]}MB
                                </span>
                            </div>
                        ))}
                    </div>
                </Card>
            </div>

            <div className="performance-charts">
                <Card title="GPU 使用率趨勢" className="chart-card">
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart
                            data={metricsHistory.filter(
                                (m) => m.source === 'sionna'
                            )}
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="timestamp" />
                            <YAxis />
                            <Tooltip />
                            <Area
                                type="monotone"
                                dataKey="value"
                                stroke="#fa8c16"
                                fill="#fa8c16"
                                fillOpacity={0.6}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </Card>

                <Card title="系統性能指標" className="system-performance-card">
                    <div className="performance-stats">
                        <Statistic
                            title="模擬 FPS"
                            value={sionnaMetrics?.simulation_fps || 0}
                        />
                        <Statistic
                            title="活躍場景"
                            value={sionnaMetrics?.active_scenarios || 0}
                        />
                        <Statistic
                            title="計算隊列"
                            value={sionnaMetrics?.computation_queue_size || 0}
                        />
                    </div>
                </Card>
            </div>
        </div>
    )

    // 渲染網路拓撲標籤
    const renderNetworkTab = () => (
        <div className="network-container">
            <NetworkTopologyChart
                width={1200}
                height={800}
                refreshInterval={isRealtime ? 10000 : 0}
                className="network-topology"
            />
        </div>
    )

    // 渲染標籤內容
    const renderTabContent = () => {
        switch (activeTab) {
            case 'overview':
                return renderOverviewTab()
            case 'uav':
                return renderUAVTab()
            case 'network':
                return renderNetworkTab()
            case 'ai':
                return renderAITab()
            case 'performance':
                return renderPerformanceTab()
            default:
                return renderOverviewTab()
        }
    }

    if (loading) {
        return (
            <div className="dashboard-loading">
                <Spin size="large" />
                <p>載入儀表板數據...</p>
            </div>
        )
    }

    return (
        <div className={`ntn-stack-dashboard ${className}`}>
            {/* 儀表板標題欄 */}
            <div className="dashboard-header">
                <div className="header-left">
                    <h1>NTN Stack 統一儀表板</h1>
                    <div className="connection-status">
                        <Badge
                            status={isConnected ? 'success' : 'error'}
                            text={isConnected ? '實時連接' : '離線模式'}
                        />
                    </div>
                </div>

                <div className="header-controls">
                    <div className="control-group">
                        <label>時間範圍:</label>
                        <select
                            value={timeRange}
                            onChange={(e) => setTimeRange(e.target.value)}
                        >
                            <option value="1h">1小時</option>
                            <option value="6h">6小時</option>
                            <option value="24h">24小時</option>
                            <option value="7d">7天</option>
                        </select>
                    </div>

                    <div className="control-group">
                        <label>
                            <input
                                type="checkbox"
                                checked={isRealtime}
                                onChange={(e) =>
                                    setIsRealtime(e.target.checked)
                                }
                            />
                            實時更新
                        </label>
                    </div>

                    <button
                        onClick={loadDashboardData}
                        className="refresh-button"
                    >
                        🔄 刷新
                    </button>
                </div>
            </div>

            {/* 錯誤提示 */}
            {error && (
                <Alert
                    message="數據載入失敗"
                    description={error}
                    type="error"
                    closable
                    onClose={() => setError(null)}
                />
            )}

            {/* 標籤導航 */}
            <div className="dashboard-tabs">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        className={`tab-button ${
                            activeTab === tab.id ? 'active' : ''
                        }`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        <span className="tab-icon">{tab.icon}</span>
                        <span className="tab-label">{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* 內容區域 */}
            <div className="dashboard-content">{renderTabContent()}</div>
        </div>
    )
}

export default NTNStackDashboard
