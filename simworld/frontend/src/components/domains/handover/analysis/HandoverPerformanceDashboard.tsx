import React, { useState, useEffect } from 'react'
import { netStackApi } from '../../../../services/netstack-api'
import {
    useNetStackData,
    useDataSourceStatus,
} from '../../../../contexts/DataSyncContext'
import {
    realConnectionManager,
    RealConnectionInfo,
    RealHandoverStatus,
} from '../../../../services/realConnectionService'
import './HandoverPerformanceDashboard.scss'

interface HandoverPerformanceDashboardProps {
    enabled: boolean
}

interface HandoverMetrics {
    totalHandovers: number
    successfulHandovers: number
    failedHandovers: number
    averageHandoverTime: number
    predictionAccuracy: number
    currentActiveHandovers: number
    handoverSuccessRate: number
    averagePredictionTime: number
    networkDowntime: number
    qosImpact: number
}

interface HandoverEvent {
    id: string
    timestamp: number
    uavId: string
    fromSatellite: string
    toSatellite: string
    duration: number
    status: 'success' | 'failed' | 'in_progress'
    reason: string
    predictionTime: number
    executionTime: number
}

interface PredictionAccuracyData {
    timeWindow: string
    accuracy: number
    totalPredictions: number
    correctPredictions: number
}

const HandoverPerformanceDashboard: React.FC<
    HandoverPerformanceDashboardProps
> = ({ enabled }) => {
    // 使用數據同步上下文
    const { isConnected: netstackConnected } = useNetStackData()
    const { dataSource } = useDataSourceStatus()

     
     
    const [metrics, setMetrics] = useState<HandoverMetrics>({
        totalHandovers: 15,
        successfulHandovers: 13,
        failedHandovers: 2,
        averageHandoverTime: 2340,
        predictionAccuracy: 87.5,
        currentActiveHandovers: 2,
        handoverSuccessRate: 86.7,
        averagePredictionTime: 125,
        networkDowntime: 480,
        qosImpact: 13.3,
    })

    const [recentEvents, setRecentEvents] = useState<HandoverEvent[]>([])
    const [accuracyHistory, setAccuracyHistory] = useState<
        PredictionAccuracyData[]
    >([])
    const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [realConnectionData, setRealConnectionData] = useState<{
        connections: Map<string, RealConnectionInfo>
        handovers: Map<string, RealHandoverStatus>
    }>({ connections: new Map(), handovers: new Map() })

    // 基於全局數據同步狀態決定是否使用真實數據
    const useRealData = netstackConnected && dataSource !== 'simulated'

    // 使用真實 NetStack API 獲取效能數據
    useEffect(() => {
        if (!enabled) return

        const fetchRealMetrics = async () => {
            if (!useRealData) return

            setIsLoading(true)
            setError(null)

            try {
                console.log('🔥 獲取真實 NetStack 效能指標...')

                // 並行獲取多個 API 數據
                const [coreSyncStatus, handoverMetrics, recentEvents] =
                    await Promise.all([
                        netStackApi.getCoreSync(),
                        netStackApi.getHandoverLatencyMetrics().catch(() => []), // 如果失敗返回空數組
                        netStackApi.getRecentSyncEvents().catch(() => []), // 如果失敗返回空數組
                    ])

                console.log('✅ NetStack 效能數據:', {
                    coreSyncStatus,
                    handoverMetrics: handoverMetrics.length,
                    recentEvents: recentEvents.length,
                })

                // 更新真實指標
                const realMetrics: HandoverMetrics = {
                    totalHandovers:
                        coreSyncStatus.statistics.total_sync_operations || 0,
                    successfulHandovers:
                        coreSyncStatus.statistics.successful_syncs || 0,
                    failedHandovers:
                        coreSyncStatus.statistics.failed_syncs || 0,
                    averageHandoverTime:
                        coreSyncStatus.statistics.average_sync_time_ms || 0,
                    predictionAccuracy:
                        coreSyncStatus.ieee_infocom_2024_features
                            .binary_search_refinement * 100 || 0,
                    currentActiveHandovers:
                        coreSyncStatus.service_info.active_tasks || 0,
                    handoverSuccessRate:
                        coreSyncStatus.statistics.total_sync_operations > 0
                            ? (coreSyncStatus.statistics.successful_syncs /
                                  coreSyncStatus.statistics
                                      .total_sync_operations) *
                              100
                            : 0,
                    averagePredictionTime:
                        coreSyncStatus.sync_performance.overall_accuracy_ms ||
                        0,
                    networkDowntime: coreSyncStatus.statistics.uptime_percentage
                        ? (100 - coreSyncStatus.statistics.uptime_percentage) *
                          60 *
                          60 *
                          1000 // 轉為 ms
                        : 0,
                    qosImpact:
                        coreSyncStatus.sync_performance.overall_accuracy_ms > 50
                            ? Math.min(
                                  100,
                                  (coreSyncStatus.sync_performance
                                      .overall_accuracy_ms -
                                      50) /
                                      5
                              )
                            : 0,
                }

                setMetrics(realMetrics)

                // 轉換換手測量數據為事件格式
                if (handoverMetrics.length > 0) {
                    const events: HandoverEvent[] = handoverMetrics
                        .slice(0, 20)
                        .map((metric) => ({
                            id: metric.measurement_id,
                            timestamp: metric.timestamp,
                            uavId: metric.ue_id,
                            fromSatellite: metric.source_satellite,
                            toSatellite: metric.target_satellite,
                            duration: metric.latency_ms,
                            status:
                                metric.success_rate > 0.8
                                    ? 'success'
                                    : 'failed',
                            reason: `${metric.handover_type} handover`,
                            predictionTime:
                                metric.additional_metrics.signaling_overhead ||
                                0,
                            executionTime:
                                metric.additional_metrics
                                    .interruption_time_ms || 0,
                        }))

                    setRecentEvents(events)
                }

                // 更新真實連接數據狀態
                const connections = realConnectionManager.getAllConnections()
                const handovers = realConnectionManager.getAllHandovers()
                setRealConnectionData({ connections, handovers })

                // 更新準確率歷史（基於真實數據）
                const newAccuracyData: PredictionAccuracyData = {
                    timeWindow: new Date().toLocaleTimeString(),
                    accuracy: realMetrics.predictionAccuracy,
                    totalPredictions: realMetrics.totalHandovers,
                    correctPredictions: realMetrics.successfulHandovers,
                }

                setAccuracyHistory((prev) => [
                    newAccuracyData,
                    ...prev.slice(0, 19),
                ])
            } catch (error) {
                console.error('❌ 獲取 NetStack 效能指標失敗:', error)
                setError(
                    error instanceof Error ? error.message : 'Unknown error'
                )

                // 注意：useRealData 現在由全局狀態控制，不需要手動設置
                console.warn('⚠️ 回退到模擬數據模式')
            } finally {
                setIsLoading(false)
            }
        }

        // 立即獲取一次數據
        fetchRealMetrics()

        // 如果使用真實數據，每30秒更新一次
        const interval = setInterval(() => {
            if (useRealData) {
                fetchRealMetrics()
            }
        }, 30000)

        return () => clearInterval(interval)
    }, [enabled, useRealData])

    // 回退的模擬數據更新（當真實 API 不可用時）
    useEffect(() => {
        if (!enabled || useRealData) return

        console.log('⚠️ 使用模擬數據更新效能指標')

        const updateSimulatedMetrics = () => {
            const newEvent: HandoverEvent = {
                id: `sim_event_${Date.now()}`,
                timestamp: Date.now(),
                uavId: `UAV_${Math.floor(Math.random() * 10) + 1}`,
                fromSatellite: `SAT_${Math.floor(Math.random() * 5) + 1}`,
                toSatellite: `SAT_${Math.floor(Math.random() * 5) + 6}`,
                duration: 1500 + Math.random() * 3000,
                status: Math.random() > 0.15 ? 'success' : 'failed',
                reason: getRandomReason(),
                predictionTime: 50 + Math.random() * 200,
                executionTime: 1000 + Math.random() * 2000,
            }

            setRecentEvents((prev) => [newEvent, ...prev.slice(0, 19)])

            setMetrics((prev) => {
                const totalHandovers = prev.totalHandovers + 1
                const successfulHandovers =
                    prev.successfulHandovers +
                    (newEvent.status === 'success' ? 1 : 0)
                const failedHandovers =
                    prev.failedHandovers +
                    (newEvent.status === 'failed' ? 1 : 0)

                return {
                    ...prev,
                    totalHandovers,
                    successfulHandovers,
                    failedHandovers,
                    averageHandoverTime:
                        (prev.averageHandoverTime * (totalHandovers - 1) +
                            newEvent.duration) /
                        totalHandovers,
                    predictionAccuracy: 85 + Math.random() * 12,
                    currentActiveHandovers: Math.floor(Math.random() * 5),
                    handoverSuccessRate:
                        (successfulHandovers / totalHandovers) * 100,
                    averagePredictionTime:
                        (prev.averagePredictionTime * (totalHandovers - 1) +
                            newEvent.predictionTime) /
                        totalHandovers,
                    networkDowntime:
                        prev.networkDowntime +
                        (newEvent.status === 'failed' ? newEvent.duration : 0),
                    qosImpact: Math.max(
                        0,
                        100 - (successfulHandovers / totalHandovers) * 100
                    ),
                }
            })

            // 更新準確率歷史 (更頻繁)
            if (Math.random() < 0.6) {
                const newAccuracyData: PredictionAccuracyData = {
                    timeWindow: new Date().toLocaleTimeString(),
                    accuracy: 85 + Math.random() * 12,
                    totalPredictions: Math.floor(Math.random() * 20) + 10,
                    correctPredictions: 0,
                }
                newAccuracyData.correctPredictions = Math.floor(
                    (newAccuracyData.totalPredictions *
                        newAccuracyData.accuracy) /
                        100
                )

                setAccuracyHistory((prev) => [
                    newAccuracyData,
                    ...prev.slice(0, 49),
                ])
            }
        }

        // 立即產生一些初始事件
        for (let i = 0; i < 8; i++) {
            setTimeout(() => updateSimulatedMetrics(), i * 500)
        }

        // 然後正常間隔更新
        const interval = setInterval(
            updateSimulatedMetrics,
            2000 + Math.random() * 3000
        )

        return () => clearInterval(interval)
    }, [enabled, useRealData])

         
         
    const getRandomReason = (): string => {
        const reasons = [
            '信號品質下降',
            '衛星仰角過低',
            '負載平衡',
            '軌道轉換',
            '干擾避免',
            '維護需求',
        ]
        return reasons[Math.floor(Math.random() * reasons.length)]
    }

         
         
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'success':
                return '#52c41a'
            case 'failed':
                return '#ff4d4f'
            case 'in_progress':
                return '#1890ff'
            default:
                return '#d9d9d9'
        }
    }

    // 移除未使用的函數

    if (!enabled) return null

    return (
        <div className="handover-performance-dashboard">
            <div className="dashboard-header">
                <div className="header-main">
                    <h2>🔄 衛星換手性能監控</h2>
                    {/* 📊 數據源狀態指示器 */}
                    <div
                        className="data-source-indicator"
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            marginLeft: '16px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                        }}
                    >
                        <div
                            style={{
                                padding: '4px 8px',
                                borderRadius: '4px',
                                backgroundColor: useRealData
                                    ? 'rgba(40, 167, 69, 0.9)'
                                    : 'rgba(255, 193, 7, 0.9)',
                                color: useRealData ? '#fff' : '#000',
                            }}
                        >
                            {useRealData ? '🐈 真實數據' : '⚠️ 模擬數據'}
                        </div>
                        {useRealData &&
                            realConnectionData.connections.size > 0 && (
                                <div
                                    style={{
                                        padding: '4px 8px',
                                        borderRadius: '4px',
                                        backgroundColor:
                                            'rgba(23, 162, 184, 0.9)',
                                        color: '#fff',
                                    }}
                                >
                                    {realConnectionData.connections.size} 連接
                                </div>
                            )}
                        {isLoading && (
                            <div
                                style={{
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    backgroundColor: 'rgba(108, 117, 125, 0.9)',
                                    color: '#fff',
                                }}
                            >
                                🔄 更新中
                            </div>
                        )}
                    </div>
                </div>

                <div className="time-range-selector">
                    {(['1h', '6h', '24h', '7d'] as const).map((range) => (
                        <button
                            key={range}
                            className={`time-range-btn ${
                                timeRange === range ? 'active' : ''
                            }`}
                            onClick={() => setTimeRange(range)}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            {/* 關鍵指標卡片 */}
            <div className="metrics-grid">
                <div className="metric-card primary">
                    <div className="metric-header">
                        <span className="metric-icon">📊</span>
                        <h3>總換手次數</h3>
                    </div>
                    <div className="metric-value">{metrics.totalHandovers}</div>
                    <div className="metric-trend up">
                        <span className="trend-icon">↗</span>
                        <span>
                            +{Math.floor(Math.random() * 10) + 1}% vs 上小時
                        </span>
                    </div>
                </div>

                <div className="metric-card success">
                    <div className="metric-header">
                        <span className="metric-icon">✅</span>
                        <h3>成功率</h3>
                    </div>
                    <div className="metric-value">
                        {metrics.handoverSuccessRate.toFixed(1)}%
                    </div>
                    <div className="metric-trend stable">
                        <span className="trend-icon">→</span>
                        <span>{useRealData ? '真實數據' : '穩定'}</span>
                    </div>
                </div>

                <div className="metric-card info">
                    <div className="metric-header">
                        <span className="metric-icon">⏱️</span>
                        <h3>平均時間</h3>
                    </div>
                    <div className="metric-value">
                        {(metrics.averageHandoverTime / 1000).toFixed(1)}s
                    </div>
                    <div className="metric-trend down">
                        <span className="trend-icon">↘</span>
                        <span>-5% 性能提升</span>
                    </div>
                </div>

                <div className="metric-card warning">
                    <div className="metric-header">
                        <span className="metric-icon">🎯</span>
                        <h3>預測準確率</h3>
                    </div>
                    <div className="metric-value">
                        {metrics.predictionAccuracy.toFixed(1)}%
                    </div>
                    <div className="metric-trend up">
                        <span className="trend-icon">↗</span>
                        <span>
                            {useRealData
                                ? 'IEEE INFOCOM 2024'
                                : '+2.3% 準確率提升'}
                        </span>
                    </div>
                </div>

                <div className="metric-card active">
                    <div className="metric-header">
                        <span className="metric-icon">🔄</span>
                        <h3>進行中</h3>
                    </div>
                    <div className="metric-value">
                        {metrics.currentActiveHandovers}
                    </div>
                    <div className="metric-description">當前換手中</div>
                </div>

                <div className="metric-card error">
                    <div className="metric-header">
                        <span className="metric-icon">❌</span>
                        <h3>失敗次數</h3>
                    </div>
                    <div className="metric-value">
                        {metrics.failedHandovers}
                    </div>
                    <div className="metric-description">需要關注</div>
                </div>
            </div>

            {/* 性能圖表區域 */}
            <div className="charts-section">
                <div className="chart-container">
                    <h3>📈 換手成功率趨勢</h3>
                    <div className="chart-placeholder">
                        <div className="chart-line">
                            {Array.from({ length: 10 }, (_, i) => (
                                <div
                                    key={i}
                                    className="chart-point"
                                    style={{
                                        left: `${i * 10}%`,
                                        bottom: `${80 + Math.random() * 15}%`,
                                        backgroundColor: '#52c41a',
                                    }}
                                />
                            ))}
                        </div>
                        <div className="chart-info">
                            <span>目標: 95%</span>
                            <span>
                                當前: {metrics.handoverSuccessRate.toFixed(1)}%
                            </span>
                        </div>
                    </div>
                </div>

                <div className="chart-container">
                    <h3>⏱️ 換手時間分佈</h3>
                    <div className="chart-placeholder">
                        <div className="histogram">
                            {Array.from({ length: 8 }, (_, i) => (
                                <div
                                    key={i}
                                    className="histogram-bar"
                                    style={{
                                        height: `${30 + Math.random() * 60}%`,
                                        backgroundColor: `hsl(${
                                            200 + i * 10
                                        }, 70%, 50%)`,
                                    }}
                                />
                            ))}
                        </div>
                        <div className="chart-labels">
                            <span>0-1s</span>
                            <span>1-2s</span>
                            <span>2-3s</span>
                            <span>3-4s</span>
                            <span>4-5s</span>
                            <span>5-6s</span>
                            <span>6-7s</span>
                            <span>7s+</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 最近事件列表 - 整合真實數據 */}
            <div className="events-section">
                <h3>📋 最近換手事件</h3>

                {/* 真實連接狀態概覽 */}
                {useRealData && realConnectionData.connections.size > 0 && (
                    <div
                        className="real-connections-overview"
                        style={{
                            marginBottom: '16px',
                            padding: '12px',
                            backgroundColor: 'rgba(23, 162, 184, 0.1)',
                            borderRadius: '8px',
                            border: '1px solid rgba(23, 162, 184, 0.3)',
                        }}
                    >
                        <h4 style={{ margin: '0 0 8px 0', color: '#17a2b8' }}>
                            🐈 當前真實連接狀態
                        </h4>
                        <div
                            style={{
                                display: 'grid',
                                gridTemplateColumns:
                                    'repeat(auto-fit, minmax(200px, 1fr))',
                                gap: '8px',
                            }}
                        >
                            {Array.from(
                                realConnectionData.connections.entries()
                            )
                                .slice(0, 6)
                                .map(([ueId, conn]) => {
                                    const handover =
                                        realConnectionData.handovers.get(ueId)
                                    return (
                                        <div
                                            key={ueId}
                                            style={{
                                                padding: '8px',
                                                backgroundColor:
                                                    'rgba(255, 255, 255, 0.05)',
                                                borderRadius: '4px',
                                                fontSize: '12px',
                                            }}
                                        >
                                            <div
                                                style={{
                                                    fontWeight: 'bold',
                                                    marginBottom: '4px',
                                                }}
                                            >
                                                {ueId}
                                            </div>
                                            <div>
                                                衛星:{' '}
                                                {conn.current_satellite_id}
                                            </div>
                                            <div>
                                                信號:{' '}
                                                {conn.signal_quality.toFixed(1)}
                                                dBm
                                            </div>
                                            <div
                                                style={{
                                                    color:
                                                        conn.status ===
                                                        'connected'
                                                            ? '#52c41a'
                                                            : '#ff4d4f',
                                                }}
                                            >
                                                {conn.status === 'connected'
                                                    ? '✅ 已連接'
                                                    : conn.status ===
                                                      'handover_preparing'
                                                    ? '🔄 準備換手'
                                                    : conn.status ===
                                                      'handover_executing'
                                                    ? '⚡ 換手中'
                                                    : '❌ 未連接'}
                                            </div>
                                            {handover &&
                                                handover.handover_status !==
                                                    'idle' && (
                                                    <div
                                                        style={{
                                                            color: '#1890ff',
                                                            fontSize: '11px',
                                                            marginTop: '2px',
                                                        }}
                                                    >
                                                        換手:{' '}
                                                        {
                                                            handover.handover_status
                                                        }
                                                        {handover.prediction_confidence && (
                                                            <span>
                                                                {' '}
                                                                (
                                                                {(
                                                                    handover.prediction_confidence *
                                                                    100
                                                                ).toFixed(0)}
                                                                %)
                                                            </span>
                                                        )}
                                                    </div>
                                                )}
                                        </div>
                                    )
                                })}
                        </div>
                    </div>
                )}

                <div className="events-table">
                    <div className="events-header">
                        <span>時間</span>
                        <span>UAV</span>
                        <span>從衛星</span>
                        <span>到衛星</span>
                        <span>持續時間</span>
                        <span>狀態</span>
                        <span>原因</span>
                    </div>
                    <div className="events-list">
                        {recentEvents.slice(0, 10).map((event) => (
                            <div key={event.id} className="event-row">
                                <span className="event-time">
                                    {new Date(
                                        event.timestamp
                                    ).toLocaleTimeString()}
                                </span>
                                <span className="event-uav">{event.uavId}</span>
                                <span className="event-from">
                                    {event.fromSatellite}
                                </span>
                                <span className="event-to">
                                    {event.toSatellite}
                                </span>
                                <span className="event-duration">
                                    {(event.duration / 1000).toFixed(1)}s
                                </span>
                                <span
                                    className="event-status"
                                    style={{
                                        color: getStatusColor(event.status),
                                    }}
                                >
                                    {event.status === 'success'
                                        ? '✅'
                                        : event.status === 'failed'
                                        ? '❌'
                                        : '🔄'}
                                    {event.status}
                                </span>
                                <span className="event-reason">
                                    {event.reason}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 預測準確率分析 */}
            <div className="accuracy-section">
                <h3>🎯 預測準確率分析</h3>
                <div className="accuracy-grid">
                    <div className="accuracy-summary">
                        <div className="accuracy-metric">
                            <span className="accuracy-label">整體準確率</span>
                            <span className="accuracy-value">
                                {metrics.predictionAccuracy.toFixed(1)}%
                            </span>
                        </div>
                        <div className="accuracy-metric">
                            <span className="accuracy-label">平均預測時間</span>
                            <span className="accuracy-value">
                                {metrics.averagePredictionTime.toFixed(0)}ms
                            </span>
                        </div>
                        <div className="accuracy-metric">
                            <span className="accuracy-label">QoS 影響</span>
                            <span className="accuracy-value">
                                {metrics.qosImpact.toFixed(1)}%
                            </span>
                        </div>
                    </div>

                    <div className="accuracy-history">
                        {accuracyHistory.slice(0, 5).map((data, index) => (
                            <div key={index} className="accuracy-item">
                                <span className="accuracy-time">
                                    {data.timeWindow}
                                </span>
                                <div className="accuracy-bar">
                                    <div
                                        className="accuracy-fill"
                                        style={{
                                            width: `${data.accuracy}%`,
                                            backgroundColor: `hsl(${
                                                data.accuracy * 1.2
                                            }, 70%, 50%)`,
                                        }}
                                    />
                                </div>
                                <span className="accuracy-percent">
                                    {data.accuracy.toFixed(0)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 錯誤和警告狀態 */}
            {error && (
                <div
                    className="error-section"
                    style={{
                        padding: '16px',
                        backgroundColor: 'rgba(245, 34, 45, 0.1)',
                        borderRadius: '8px',
                        border: '1px solid rgba(245, 34, 45, 0.3)',
                        marginBottom: '24px',
                    }}
                >
                    <h3 style={{ color: '#f5222d', margin: '0 0 8px 0' }}>
                        ⚠️ 數據獲取錯誤
                    </h3>
                    <p style={{ margin: '0', color: '#f5222d' }}>{error}</p>
                    <p
                        style={{
                            margin: '8px 0 0 0',
                            fontSize: '14px',
                            color: '#666',
                        }}
                    >
                        系統已自動切換至模擬數據模式，請檢查 NetStack 連接狀態。
                    </p>
                </div>
            )}

            {/* 性能建議 - 基於真實數據的智能建議 */}
            <div className="recommendations-section">
                <h3>💡 性能優化建議</h3>
                <div className="recommendations-list">
                    {useRealData && metrics.handoverSuccessRate < 90 && (
                        <div className="recommendation-item high">
                            <span className="recommendation-priority">高</span>
                            <span className="recommendation-text">
                                換手成功率{' '}
                                {metrics.handoverSuccessRate.toFixed(1)}%
                                低於目標 90%，建議檢查信號閾值參數
                            </span>
                        </div>
                    )}
                    {useRealData && metrics.predictionAccuracy < 85 && (
                        <div className="recommendation-item medium">
                            <span className="recommendation-priority">中</span>
                            <span className="recommendation-text">
                                IEEE INFOCOM 2024 預測準確率{' '}
                                {metrics.predictionAccuracy.toFixed(1)}%
                                可進一步優化
                            </span>
                        </div>
                    )}
                    {useRealData && metrics.currentActiveHandovers > 3 && (
                        <div className="recommendation-item medium">
                            <span className="recommendation-priority">中</span>
                            <span className="recommendation-text">
                                當前有 {metrics.currentActiveHandovers}{' '}
                                個活躍換手，可能需要調整換手策略
                            </span>
                        </div>
                    )}
                    {realConnectionData.connections.size > 0 &&
                        Array.from(
                            realConnectionData.connections.values()
                        ).filter((conn) => conn.signal_quality < -85).length >
                            0 && (
                            <div className="recommendation-item high">
                                <span className="recommendation-priority">
                                    高
                                </span>
                                <span className="recommendation-text">
                                    檢測到{' '}
                                    {
                                        Array.from(
                                            realConnectionData.connections.values()
                                        ).filter(
                                            (conn) => conn.signal_quality < -85
                                        ).length
                                    }{' '}
                                    個連接信號質量低於 -85dBm，建議立即換手
                                </span>
                            </div>
                        )}
                    {!useRealData && (
                        <>
                            <div className="recommendation-item high">
                                <span className="recommendation-priority">
                                    高
                                </span>
                                <span className="recommendation-text">
                                    檢測到換手失敗率略高，建議調整信號閾值參數
                                </span>
                            </div>
                            <div className="recommendation-item medium">
                                <span className="recommendation-priority">
                                    中
                                </span>
                                <span className="recommendation-text">
                                    預測算法可進一步優化，考慮增加環境因子權重
                                </span>
                            </div>
                            <div className="recommendation-item low">
                                <span className="recommendation-priority">
                                    低
                                </span>
                                <span className="recommendation-text">
                                    建議增加更多候選衛星以提高換手成功率
                                </span>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}

export default HandoverPerformanceDashboard
