import React, { useState, useEffect } from 'react'
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

const HandoverPerformanceDashboard: React.FC<HandoverPerformanceDashboardProps> = ({ enabled }) => {
    const [metrics, setMetrics] = useState<HandoverMetrics>({
        totalHandovers: 0,
        successfulHandovers: 0,
        failedHandovers: 0,
        averageHandoverTime: 0,
        predictionAccuracy: 0,
        currentActiveHandovers: 0,
        handoverSuccessRate: 0,
        averagePredictionTime: 0,
        networkDowntime: 0,
        qosImpact: 0
    })

    const [recentEvents, setRecentEvents] = useState<HandoverEvent[]>([])
    const [accuracyHistory, setAccuracyHistory] = useState<PredictionAccuracyData[]>([])
    const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h')

    // 模擬數據更新
    useEffect(() => {
        if (!enabled) return

        const updateMetrics = () => {
            const newEvent: HandoverEvent = {
                id: `event_${Date.now()}`,
                timestamp: Date.now(),
                uavId: `UAV_${Math.floor(Math.random() * 10) + 1}`,
                fromSatellite: `SAT_${Math.floor(Math.random() * 5) + 1}`,
                toSatellite: `SAT_${Math.floor(Math.random() * 5) + 6}`,
                duration: 1500 + Math.random() * 3000,
                status: Math.random() > 0.15 ? 'success' : 'failed',
                reason: getRandomReason(),
                predictionTime: 50 + Math.random() * 200,
                executionTime: 1000 + Math.random() * 2000
            }

            setRecentEvents(prev => [newEvent, ...prev.slice(0, 19)])

            setMetrics(prev => {
                const totalHandovers = prev.totalHandovers + 1
                const successfulHandovers = prev.successfulHandovers + (newEvent.status === 'success' ? 1 : 0)
                const failedHandovers = prev.failedHandovers + (newEvent.status === 'failed' ? 1 : 0)
                
                return {
                    ...prev,
                    totalHandovers,
                    successfulHandovers,
                    failedHandovers,
                    averageHandoverTime: (prev.averageHandoverTime * (totalHandovers - 1) + newEvent.duration) / totalHandovers,
                    predictionAccuracy: 85 + Math.random() * 12,
                    currentActiveHandovers: Math.floor(Math.random() * 5),
                    handoverSuccessRate: (successfulHandovers / totalHandovers) * 100,
                    averagePredictionTime: (prev.averagePredictionTime * (totalHandovers - 1) + newEvent.predictionTime) / totalHandovers,
                    networkDowntime: prev.networkDowntime + (newEvent.status === 'failed' ? newEvent.duration : 0),
                    qosImpact: Math.max(0, 100 - (successfulHandovers / totalHandovers) * 100)
                }
            })

            // 更新準確率歷史
            if (Math.random() < 0.3) {
                const newAccuracyData: PredictionAccuracyData = {
                    timeWindow: new Date().toLocaleTimeString(),
                    accuracy: 85 + Math.random() * 12,
                    totalPredictions: Math.floor(Math.random() * 20) + 10,
                    correctPredictions: 0
                }
                newAccuracyData.correctPredictions = Math.floor(newAccuracyData.totalPredictions * newAccuracyData.accuracy / 100)

                setAccuracyHistory(prev => [newAccuracyData, ...prev.slice(0, 49)])
            }
        }

        updateMetrics()
        const interval = setInterval(updateMetrics, 3000 + Math.random() * 4000)

        return () => clearInterval(interval)
    }, [enabled])

    const getRandomReason = (): string => {
        const reasons = [
            '信號品質下降',
            '衛星仰角過低', 
            '負載平衡',
            '軌道轉換',
            '干擾避免',
            '維護需求'
        ]
        return reasons[Math.floor(Math.random() * reasons.length)]
    }

    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'success': return '#52c41a'
            case 'failed': return '#ff4d4f'
            case 'in_progress': return '#1890ff'
            default: return '#d9d9d9'
        }
    }

    // 移除未使用的函數

    if (!enabled) return null

    return (
        <div className="handover-performance-dashboard">
            <div className="dashboard-header">
                <h2>🔄 衛星換手性能監控</h2>
                <div className="time-range-selector">
                    {(['1h', '6h', '24h', '7d'] as const).map(range => (
                        <button
                            key={range}
                            className={`time-range-btn ${timeRange === range ? 'active' : ''}`}
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
                        <span>+{Math.floor(Math.random() * 10) + 1}% vs 上小時</span>
                    </div>
                </div>

                <div className="metric-card success">
                    <div className="metric-header">
                        <span className="metric-icon">✅</span>
                        <h3>成功率</h3>
                    </div>
                    <div className="metric-value">{metrics.handoverSuccessRate.toFixed(1)}%</div>
                    <div className="metric-trend stable">
                        <span className="trend-icon">→</span>
                        <span>穩定</span>
                    </div>
                </div>

                <div className="metric-card info">
                    <div className="metric-header">
                        <span className="metric-icon">⏱️</span>
                        <h3>平均時間</h3>
                    </div>
                    <div className="metric-value">{(metrics.averageHandoverTime / 1000).toFixed(1)}s</div>
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
                    <div className="metric-value">{metrics.predictionAccuracy.toFixed(1)}%</div>
                    <div className="metric-trend up">
                        <span className="trend-icon">↗</span>
                        <span>+2.3% 準確率提升</span>
                    </div>
                </div>

                <div className="metric-card active">
                    <div className="metric-header">
                        <span className="metric-icon">🔄</span>
                        <h3>進行中</h3>
                    </div>
                    <div className="metric-value">{metrics.currentActiveHandovers}</div>
                    <div className="metric-description">當前換手中</div>
                </div>

                <div className="metric-card error">
                    <div className="metric-header">
                        <span className="metric-icon">❌</span>
                        <h3>失敗次數</h3>
                    </div>
                    <div className="metric-value">{metrics.failedHandovers}</div>
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
                                        backgroundColor: '#52c41a'
                                    }}
                                />
                            ))}
                        </div>
                        <div className="chart-info">
                            <span>目標: 95%</span>
                            <span>當前: {metrics.handoverSuccessRate.toFixed(1)}%</span>
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
                                        backgroundColor: `hsl(${200 + i * 10}, 70%, 50%)`
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

            {/* 最近事件列表 */}
            <div className="events-section">
                <h3>📋 最近換手事件</h3>
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
                                    {new Date(event.timestamp).toLocaleTimeString()}
                                </span>
                                <span className="event-uav">{event.uavId}</span>
                                <span className="event-from">{event.fromSatellite}</span>
                                <span className="event-to">{event.toSatellite}</span>
                                <span className="event-duration">
                                    {(event.duration / 1000).toFixed(1)}s
                                </span>
                                <span
                                    className="event-status"
                                    style={{ color: getStatusColor(event.status) }}
                                >
                                    {event.status === 'success' ? '✅' : event.status === 'failed' ? '❌' : '🔄'}
                                    {event.status}
                                </span>
                                <span className="event-reason">{event.reason}</span>
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
                            <span className="accuracy-value">{metrics.predictionAccuracy.toFixed(1)}%</span>
                        </div>
                        <div className="accuracy-metric">
                            <span className="accuracy-label">平均預測時間</span>
                            <span className="accuracy-value">{metrics.averagePredictionTime.toFixed(0)}ms</span>
                        </div>
                        <div className="accuracy-metric">
                            <span className="accuracy-label">QoS 影響</span>
                            <span className="accuracy-value">{metrics.qosImpact.toFixed(1)}%</span>
                        </div>
                    </div>
                    
                    <div className="accuracy-history">
                        {accuracyHistory.slice(0, 5).map((data, index) => (
                            <div key={index} className="accuracy-item">
                                <span className="accuracy-time">{data.timeWindow}</span>
                                <div className="accuracy-bar">
                                    <div
                                        className="accuracy-fill"
                                        style={{
                                            width: `${data.accuracy}%`,
                                            backgroundColor: `hsl(${data.accuracy * 1.2}, 70%, 50%)`
                                        }}
                                    />
                                </div>
                                <span className="accuracy-percent">{data.accuracy.toFixed(0)}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 性能建議 */}
            <div className="recommendations-section">
                <h3>💡 性能優化建議</h3>
                <div className="recommendations-list">
                    <div className="recommendation-item high">
                        <span className="recommendation-priority">高</span>
                        <span className="recommendation-text">
                            檢測到換手失敗率略高，建議調整信號閾值參數
                        </span>
                    </div>
                    <div className="recommendation-item medium">
                        <span className="recommendation-priority">中</span>
                        <span className="recommendation-text">
                            預測算法可進一步優化，考慮增加環境因子權重
                        </span>
                    </div>
                    <div className="recommendation-item low">
                        <span className="recommendation-priority">低</span>
                        <span className="recommendation-text">
                            建議增加更多候選衛星以提高換手成功率
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default HandoverPerformanceDashboard