import React, { useState, useEffect } from 'react'
import './CoreNetworkSyncViewer.scss'

interface CoreNetworkSyncViewerProps {
    enabled: boolean
    devices: unknown[]
}

interface CoreSyncMetrics {
    totalSyncOperations: number
    successfulSyncs: number
    failedSyncs: number
    overallAccuracyMs: number
    maxAchieverAccuracyMs: number
    successRate: number
    averageSyncTime: number
    signallingFreeOperations: number
    binarySearchOptimizations: number
    activeComponents: number
    uptimePercentage: number
}

interface ComponentSyncStatus {
    name: string
    state: 'synchronized' | 'partial_sync' | 'desynchronized' | 'initializing'
    accuracyMs: number
    lastSync: number
    availability: number
    latencyMs: number
    jitterMs: number
}

interface SyncEvent {
    id: string
    timestamp: number
    type: string
    component: string
    accuracy: number
    status: 'success' | 'failed'
    message?: string
}

interface IEEEFeatures {
    fineGrainedSync: boolean
    twoPointPrediction: boolean
    signallingFreeCoordination: boolean
    binarySearchRefinement: number
}

const CoreNetworkSyncViewer: React.FC<CoreNetworkSyncViewerProps> = ({
    enabled,
    devices, // Currently not used but may be needed for future features
}) => {
    // TODO: Use devices for enhanced visualization
    console.log('Devices available for sync visualization:', devices.length)
    const [metrics, setMetrics] = useState<CoreSyncMetrics>({
        totalSyncOperations: 0,
        successfulSyncs: 0,
        failedSyncs: 0,
        overallAccuracyMs: 0,
        maxAchieverAccuracyMs: 0,
        successRate: 0,
        averageSyncTime: 0,
        signallingFreeOperations: 0,
        binarySearchOptimizations: 0,
        activeComponents: 0,
        uptimePercentage: 0,
    })

    const [components, setComponents] = useState<ComponentSyncStatus[]>([])
    const [recentEvents, setRecentEvents] = useState<SyncEvent[]>([])
    const [ieeeFeatures, setIeeeFeatures] = useState<IEEEFeatures>({
        fineGrainedSync: true,
        twoPointPrediction: true,
        signallingFreeCoordination: true,
        binarySearchRefinement: 0,
    })

    const [isServiceRunning, setIsServiceRunning] = useState(false)
    const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h')

    // 生成隨機組件名稱

    const getRandomComponent = () => {
        const components = [
            'Access Network',
            'Core Network',
            'Satellite Network',
            'UAV Network',
            'Ground Station',
        ]
        return components[Math.floor(Math.random() * components.length)]
    }

    // 生成隨機事件類型

    const getRandomEventType = () => {
        const types = [
            'Fine-Grained Sync',
            'Binary Search Refinement',
            'Emergency Resync',
            'Component Sync',
            'Signalling-Free Coordination',
        ]
        return types[Math.floor(Math.random() * types.length)]
    }

    // 模擬數據更新
    useEffect(() => {
        if (!enabled) return

        // 初始化組件狀態
        setComponents([
            {
                name: 'Access Network',
                state: 'synchronized',
                accuracyMs: 3.2,
                lastSync: Date.now() - Math.random() * 60000,
                availability: 0.98,
                latencyMs: 15.2,
                jitterMs: 2.1,
            },
            {
                name: 'Core Network',
                state: 'synchronized',
                accuracyMs: 2.8,
                lastSync: Date.now() - Math.random() * 60000,
                availability: 0.99,
                latencyMs: 12.5,
                jitterMs: 1.8,
            },
            {
                name: 'Satellite Network',
                state: 'partial_sync',
                accuracyMs: 8.5,
                lastSync: Date.now() - Math.random() * 60000,
                availability: 0.95,
                latencyMs: 45.3,
                jitterMs: 12.2,
            },
            {
                name: 'UAV Network',
                state: 'synchronized',
                accuracyMs: 5.1,
                lastSync: Date.now() - Math.random() * 60000,
                availability: 0.96,
                latencyMs: 28.7,
                jitterMs: 6.5,
            },
            {
                name: 'Ground Station',
                state: 'synchronized',
                accuracyMs: 1.9,
                lastSync: Date.now() - Math.random() * 60000,
                availability: 0.99,
                latencyMs: 8.4,
                jitterMs: 1.2,
            },
        ])

        const updateData = () => {
            // 新增同步事件
            const newEvent: SyncEvent = {
                id: `event_${Date.now()}`,
                timestamp: Date.now(),
                type: getRandomEventType(),
                component: getRandomComponent(),
                accuracy: 1 + Math.random() * 10,
                status: Math.random() > 0.1 ? 'success' : 'failed',
                message: Math.random() > 0.8 ? '網路延遲過高' : undefined,
            }

            setRecentEvents((prev) => [newEvent, ...prev.slice(0, 14)])

            // 更新指標
            setMetrics((prev) => {
                const totalOps = prev.totalSyncOperations + 1
                const successfulOps =
                    prev.successfulSyncs +
                    (newEvent.status === 'success' ? 1 : 0)
                const failedOps =
                    prev.failedSyncs + (newEvent.status === 'failed' ? 1 : 0)

                return {
                    ...prev,
                    totalSyncOperations: totalOps,
                    successfulSyncs: successfulOps,
                    failedSyncs: failedOps,
                    overallAccuracyMs: 2.5 + Math.random() * 3,
                    maxAchieverAccuracyMs: 0.8 + Math.random() * 1.5,
                    successRate: (successfulOps / totalOps) * 100,
                    averageSyncTime: 150 + Math.random() * 100,
                    signallingFreeOperations: Math.floor(successfulOps * 0.85),
                    binarySearchOptimizations: Math.floor(totalOps * 0.6),
                    activeComponents: 5,
                    uptimePercentage: 95 + Math.random() * 4,
                }
            })

            // 更新 IEEE 特性
            setIeeeFeatures((prev) => ({
                ...prev,
                binarySearchRefinement:
                    prev.binarySearchRefinement + (Math.random() > 0.7 ? 1 : 0),
            }))

            // 更新組件狀態
            setComponents((prev) =>
                prev.map((comp) => ({
                    ...comp,
                    accuracyMs: comp.accuracyMs + (Math.random() - 0.5) * 2,
                    lastSync: Date.now() - Math.random() * 30000,
                    latencyMs: comp.latencyMs + (Math.random() - 0.5) * 10,
                    jitterMs: Math.max(
                        0.1,
                        comp.jitterMs + (Math.random() - 0.5) * 2
                    ),
                }))
            )
        }

        setIsServiceRunning(true)
        const interval = setInterval(updateData, 3000 + Math.random() * 4000)

        return () => clearInterval(interval)
    }, [enabled])

    // 啟動/停止服務
    const toggleService = () => {
        setIsServiceRunning(!isServiceRunning)
    }

    // 格式化時間
    const formatTime = (timestamp: number) => {
        return new Date(timestamp).toLocaleTimeString('zh-TW')
    }

    // 獲取狀態顏色

    const getStateColor = (state: string) => {
        switch (state) {
            case 'synchronized':
                return '#10b981'
            case 'partial_sync':
                return '#f59e0b'
            case 'desynchronized':
                return '#ef4444'
            case 'initializing':
                return '#6366f1'
            default:
                return '#6b7280'
        }
    }

    if (!enabled) return null

    return (
        <div className="core-sync-dashboard">
            <div className="dashboard-header">
                <h2>📡 核心網路同步機制</h2>
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

            <div className="dashboard-subtitle">
                IEEE INFOCOM 2024 Signaling-free Synchronization
            </div>

            {/* 服務控制 */}
            <div className="service-control">
                <button
                    className={`service-btn ${
                        isServiceRunning ? 'running' : 'stopped'
                    }`}
                    onClick={toggleService}
                >
                    {isServiceRunning ? '⏸️ 停止服務' : '▶️ 啟動服務'}
                </button>
                <div className="service-status">
                    <span
                        className={`status-indicator ${
                            isServiceRunning ? 'running' : 'stopped'
                        }`}
                    ></span>
                    {isServiceRunning ? '服務運行中' : '服務已停止'}
                </div>
            </div>

            {/* 核心指標卡片 */}
            <div className="metrics-grid">
                <div className="metric-card primary">
                    <div className="metric-header">
                        <span className="metric-icon">🎯</span>
                        <span className="metric-title">同步精度</span>
                    </div>
                    <div className="metric-value">
                        {metrics.overallAccuracyMs.toFixed(1)}
                    </div>
                    <div className="metric-unit">ms</div>
                    <div className="metric-change">
                        最佳: {metrics.maxAchieverAccuracyMs.toFixed(1)}ms
                    </div>
                </div>

                <div className="metric-card success">
                    <div className="metric-header">
                        <span className="metric-icon">✅</span>
                        <span className="metric-title">成功率</span>
                    </div>
                    <div className="metric-value">
                        {metrics.successRate.toFixed(1)}
                    </div>
                    <div className="metric-unit">%</div>
                    <div className="metric-change">
                        {metrics.successfulSyncs}/{metrics.totalSyncOperations}
                    </div>
                </div>

                <div className="metric-card info">
                    <div className="metric-header">
                        <span className="metric-icon">⚡</span>
                        <span className="metric-title">無信令操作</span>
                    </div>
                    <div className="metric-value">
                        {metrics.signallingFreeOperations}
                    </div>
                    <div className="metric-unit">次</div>
                    <div className="metric-change">
                        總共 {metrics.totalSyncOperations} 次
                    </div>
                </div>

                <div className="metric-card warning">
                    <div className="metric-header">
                        <span className="metric-icon">🔍</span>
                        <span className="metric-title">Binary Search</span>
                    </div>
                    <div className="metric-value">
                        {ieeeFeatures.binarySearchRefinement}
                    </div>
                    <div className="metric-unit">優化</div>
                    <div className="metric-change">
                        {metrics.binarySearchOptimizations} 次操作
                    </div>
                </div>
            </div>

            {/* IEEE INFOCOM 2024 特性 */}
            <div className="ieee-features">
                <h3>🏆 IEEE INFOCOM 2024 特性</h3>
                <div className="features-list">
                    <div
                        className={`feature-item ${
                            ieeeFeatures.fineGrainedSync ? 'active' : 'inactive'
                        }`}
                    >
                        <span className="feature-status">
                            {ieeeFeatures.fineGrainedSync ? '🟢' : '🔴'}
                        </span>
                        <span className="feature-name">Fine-Grained 同步</span>
                    </div>
                    <div
                        className={`feature-item ${
                            ieeeFeatures.twoPointPrediction
                                ? 'active'
                                : 'inactive'
                        }`}
                    >
                        <span className="feature-status">
                            {ieeeFeatures.twoPointPrediction ? '🟢' : '🔴'}
                        </span>
                        <span className="feature-name">Two-Point 預測</span>
                    </div>
                    <div
                        className={`feature-item ${
                            ieeeFeatures.signallingFreeCoordination
                                ? 'active'
                                : 'inactive'
                        }`}
                    >
                        <span className="feature-status">
                            {ieeeFeatures.signallingFreeCoordination
                                ? '🟢'
                                : '🔴'}
                        </span>
                        <span className="feature-name">無信令協調</span>
                    </div>
                </div>
            </div>

            {/* 組件狀態 */}
            <div className="components-status">
                <h3>🔗 組件同步狀態</h3>
                <div className="components-list">
                    {components.map((comp) => (
                        <div key={comp.name} className="component-item">
                            <div className="component-info">
                                <span className="component-name">
                                    {comp.name}
                                </span>
                                <span
                                    className="component-state"
                                    style={{ color: getStateColor(comp.state) }}
                                >
                                    {comp.state.toUpperCase()}
                                </span>
                            </div>
                            <div className="component-metrics">
                                <span className="metric">
                                    精度: {comp.accuracyMs.toFixed(1)}ms
                                </span>
                                <span className="metric">
                                    可用性:{' '}
                                    {(comp.availability * 100).toFixed(1)}%
                                </span>
                                <span className="metric">
                                    延遲: {comp.latencyMs.toFixed(1)}ms
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 最近事件 */}
            <div className="recent-events">
                <h3>📋 最近同步事件</h3>
                <div className="events-list">
                    {recentEvents.slice(0, 6).map((event) => (
                        <div
                            key={event.id}
                            className={`event-item ${event.status}`}
                        >
                            <div className="event-info">
                                <span className="event-type">{event.type}</span>
                                <span className="event-time">
                                    {formatTime(event.timestamp)}
                                </span>
                            </div>
                            <div className="event-details">
                                <span className="event-component">
                                    {event.component}
                                </span>
                                <span className="event-accuracy">
                                    {event.accuracy.toFixed(1)}ms
                                </span>
                                <span
                                    className={`event-status ${event.status}`}
                                >
                                    {event.status === 'success' ? '✅' : '❌'}
                                </span>
                            </div>
                            {event.message && (
                                <div className="event-message">
                                    {event.message}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default CoreNetworkSyncViewer
