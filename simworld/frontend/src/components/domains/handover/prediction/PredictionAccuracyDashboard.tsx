import React, { useState, useEffect, useCallback } from 'react'
import {
    HandoverAPIService,
    AccuracyMetrics,
} from '../../../../services/handoverApi'
import './PredictionAccuracyDashboard.scss'

interface PredictionAccuracyDashboardProps {
    isEnabled: boolean
    refreshInterval?: number // 刷新間隔（毫秒）
}

interface AccuracyTrendData {
    timestamp: number
    accuracy: number
}

interface OptimizationRecommendation {
    id: string
    priority: 'high' | 'medium' | 'low'
    recommendation: string
    impact: string
}

const PredictionAccuracyDashboard: React.FC<
    PredictionAccuracyDashboardProps
> = ({ isEnabled, refreshInterval = 5000 }) => {
    // 準確率指標狀態
    const [accuracyMetrics, setAccuracyMetrics] =
        useState<AccuracyMetrics | null>(null)
    const [accuracyTrend, setAccuracyTrend] = useState<AccuracyTrendData[]>([])
    const [recommendations, setRecommendations] = useState<
        OptimizationRecommendation[]
    >([])
    const [loading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // 設定狀態
    const [accuracyOptimizationEnabled, setAccuracyOptimizationEnabled] =
        useState(true)
    const [weatherAdjustmentEnabled, setWeatherAdjustmentEnabled] =
        useState(true)

    // 生成模擬準確率數據
    const generateMockMetrics = useCallback((): AccuracyMetrics => {
        // 60% 機率達到95%以上，40% 機率低於95%
        const baseAccuracy =
            Math.random() > 0.4
                ? 0.95 + Math.random() * 0.04 // 95-99%
                : 0.89 + Math.random() * 0.06 // 89-95%

        const rollingAccuracy = baseAccuracy + (Math.random() - 0.5) * 0.02

        const _metrics = {
            current_accuracy: baseAccuracy,
            rolling_accuracy: Math.max(0.85, Math.min(0.99, rollingAccuracy)),
            accuracy_trend:
                Math.random() > 0.6
                    ? 'improving'
                    : Math.random() > 0.3
                    ? 'stable'
                    : 'declining',
            predictions_evaluated: Math.floor(Math.random() * 1000) + 500,
            target_achievement: baseAccuracy >= 0.95,
            confidence_interval: [
                Math.max(0.85, baseAccuracy - 0.03),
                Math.min(0.99, baseAccuracy + 0.03),
            ] as [number, number],
            accuracy_by_context: {
                weather_clear: 0.96 + Math.random() * 0.03,
                weather_cloudy: 0.91 + Math.random() * 0.04,
                satellites_high: 0.95 + Math.random() * 0.03,
                satellites_low: 0.88 + Math.random() * 0.05,
            },
        }

        console.log(
            '生成模擬數據:',
            _metrics,
            '目標達成:',
            _metrics.target_achievement
        )
        return _metrics
    }, [])

    // 移除未使用的 fetchAccuracyMetrics 函數

    // 生成模擬建議數據
    const generateMockRecommendations =
        useCallback((): OptimizationRecommendation[] => {
            const mockRecs = [
                {
                    priority: 'high' as const,
                    rec: '當前預測準確率為 94.2%，建議調整 delta_t 參數以提升精度',
                    impact: '高影響',
                },
                {
                    priority: 'medium' as const,
                    rec: '天氣條件良好，可啟用高精度預測模式',
                    impact: '正面影響',
                },
                {
                    priority: 'low' as const,
                    rec: '機器學習模型性能穩定，建議維持當前配置',
                    impact: '中等影響',
                },
                {
                    priority: 'medium' as const,
                    rec: '衛星密度較高，可提升預測窗口至 15 秒',
                    impact: '正面影響',
                },
            ]

            // 隨機返回 2-3 個建議
            const shuffled = mockRecs.sort(() => 0.5 - Math.random())
            return shuffled
                .slice(0, 2 + Math.floor(Math.random() * 2))
                .map((item, index) => ({
                    id: `rec_${index}`,
                    priority: item.priority,
                    recommendation: item.rec,
                    impact: item.impact,
                }))
        }, [])

    // 移除未使用的 fetchRecommendations 函數

    // 換手準確率優化
    const toggleAccuracyOptimization = useCallback(async () => {
        try {
            const newState = !accuracyOptimizationEnabled
            // 暫時使用本地狀態，直到後端實現 API
            setAccuracyOptimizationEnabled(newState)
            console.log(`準確率優化已${newState ? '啟用' : '停用'}`)

            // 嘗試調用 API（如果存在）
            try {
                await HandoverAPIService.toggleAccuracyOptimization(newState)
            } catch {
                console.warn('準確率優化 API 暫未實現，使用本地狀態')
            }
        } catch (err) {
            setError('換手準確率優化失敗')
            console.error('換手準確率優化錯誤:', err)
        }
    }, [accuracyOptimizationEnabled])

    // 換手天氣調整
    const toggleWeatherAdjustment = useCallback(async () => {
        try {
            const newState = !weatherAdjustmentEnabled
            setWeatherAdjustmentEnabled(newState)
            console.log(`天氣調整已${newState ? '啟用' : '停用'}`)

            // 調用天氣調整 API
            try {
                await HandoverAPIService.toggleWeatherAdjustment(newState)
            } catch (apiErr) {
                console.warn('天氣調整 API 調用失敗:', apiErr)
            }
        } catch (err) {
            setError('換手天氣調整失敗')
            console.error('換手天氣調整錯誤:', err)
        }
    }, [weatherAdjustmentEnabled])

    // 初始化數據 - 只執行一次
    useEffect(() => {
        if (!isEnabled) {
            console.log('預測精度儀表板未啟用')
            return
        }

        console.log('初始化預測精度儀表板數據')

        // 立即設置初始數據
        const initialData = generateMockMetrics()
        setAccuracyMetrics(initialData)

        // 設置初始建議
        const initialRecs = generateMockRecommendations()
        setRecommendations(initialRecs)
    }, [isEnabled, generateMockMetrics, generateMockRecommendations]) // 只依賴 isEnabled

    // 定期更新數據 - 獨立的 useEffect
    useEffect(() => {
        if (!isEnabled || !accuracyMetrics) return

        console.log('啟動定期數據更新')

        // 設定定期刷新
        const interval = setInterval(() => {
            console.log('定期更新數據')

            // 更新準確率數據
            const newMetrics = generateMockMetrics()
            setAccuracyMetrics(newMetrics)

            // 更新趨勢數據
            setAccuracyTrend((prev) => {
                const newTrend = [
                    ...prev,
                    {
                        timestamp: Date.now(),
                        accuracy: newMetrics.current_accuracy,
                    },
                ]
                return newTrend.slice(-50)
            })

            // 偶爾更新建議
            if (Math.random() < 0.2) {
                // 20% 概率更新建議
                const newRecs = generateMockRecommendations()
                setRecommendations(newRecs)
            }
        }, refreshInterval)

        return () => {
            console.log('清理定期更新定時器')
            clearInterval(interval)
        }
    }, [
        isEnabled,
        accuracyMetrics,
        refreshInterval,
        generateMockMetrics,
        generateMockRecommendations,
    ])

    // 格式化百分比
    const formatPercentage = (value: number | undefined | null): string => {
        if (value === undefined || value === null || isNaN(value)) {
            return '--'
        }
        return `${(value * 100).toFixed(1)}%`
    }

    // 獲取準確率等級

    const getAccuracyLevel = (
        accuracy: number | undefined | null
    ): { level: string; color: string } => {
        if (!accuracy || isNaN(accuracy))
            return { level: '--', color: '#64748b' }
        if (accuracy >= 0.95) return { level: '優秀', color: '#10b981' }
        if (accuracy >= 0.9) return { level: '良好', color: '#3b82f6' }
        if (accuracy >= 0.8) return { level: '中等', color: '#f59e0b' }
        if (accuracy >= 0.7) return { level: '較差', color: '#f97316' }
        return { level: '需改善', color: '#ef4444' }
    }

    // 獲取趨勢圖表數據

    const getTrendChartPath = (): string => {
        if (accuracyTrend.length < 2) return ''

        const width = 200
        const height = 60
        const points = accuracyTrend.slice(-20) // 最近20個數據點

        if (points.length < 2) return ''

        const xStep = width / (points.length - 1)
        const yMin = Math.min(...points.map((p) => p.accuracy))
        const yMax = Math.max(...points.map((p) => p.accuracy))
        const yRange = yMax - yMin || 0.1 // 避免除零

        const pathData = points
            .map((point, index) => {
                const x = index * xStep
                const y = height - ((point.accuracy - yMin) / yRange) * height
                return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
            })
            .join(' ')

        return pathData
    }

    if (!isEnabled) {
        return (
            <div className="prediction-accuracy-dashboard disabled">
                <div className="disabled-message">
                    <h3>📊 預測精度儀表板已停用</h3>
                    <p>請啟用換手功能來查看預測精度分析</p>
                </div>
            </div>
        )
    }

    if (loading && !accuracyMetrics) {
        return (
            <div className="prediction-accuracy-dashboard loading">
                <div className="loading-indicator">
                    <div className="spinner"></div>
                    <p>載入預測精度數據...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="prediction-accuracy-dashboard">
            <div className="dashboard-header">
                <h2>📊 預測精度分析儀表板</h2>
                <div className="header-controls">
                    <div className="control-group">
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={accuracyOptimizationEnabled}
                                onChange={toggleAccuracyOptimization}
                            />
                            <span className="toggle-slider"></span>
                            <span className="toggle-label">準確率優化</span>
                        </label>
                    </div>
                    <div className="control-group">
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={weatherAdjustmentEnabled}
                                onChange={toggleWeatherAdjustment}
                            />
                            <span className="toggle-slider"></span>
                            <span className="toggle-label">天氣調整</span>
                        </label>
                    </div>
                </div>
            </div>

            {error && (
                <div className="error-message">
                    <span className="error-icon">⚠️</span>
                    <span>{error}</span>
                </div>
            )}

            <div className="dashboard-content">
                {/* 主要指標卡片 */}
                <div className="metrics-grid">
                    <div className="metric-card primary">
                        <div className="metric-header">
                            <h3>當前準確率</h3>
                            <span className="metric-icon">🎯</span>
                        </div>
                        <div className="metric-value">
                            {accuracyMetrics
                                ? formatPercentage(
                                      accuracyMetrics.current_accuracy
                                  )
                                : '--'}
                        </div>
                        <div className="metric-detail">
                            {accuracyMetrics && (
                                <span
                                    className="accuracy-level"
                                    style={{
                                        color: getAccuracyLevel(
                                            accuracyMetrics.current_accuracy
                                        ).color,
                                    }}
                                >
                                    {
                                        getAccuracyLevel(
                                            accuracyMetrics.current_accuracy
                                        ).level
                                    }
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="metric-card">
                        <div className="metric-header">
                            <h3>滾動準確率</h3>
                            <span className="metric-icon">📈</span>
                        </div>
                        <div className="metric-value">
                            {accuracyMetrics
                                ? formatPercentage(
                                      accuracyMetrics.rolling_accuracy
                                  )
                                : '--'}
                        </div>
                        <div className="metric-detail">
                            <span
                                className={`trend-indicator ${
                                    accuracyMetrics?.accuracy_trend || ''
                                }`}
                            >
                                {accuracyMetrics?.accuracy_trend ===
                                    'improving' && '📈 上升中'}
                                {accuracyMetrics?.accuracy_trend ===
                                    'declining' && '📉 下降中'}
                                {accuracyMetrics?.accuracy_trend === 'stable' &&
                                    '➡️ 穩定'}
                            </span>
                        </div>
                    </div>

                    <div className="metric-card">
                        <div className="metric-header">
                            <h3>目標達成</h3>
                            <span className="metric-icon">🏆</span>
                        </div>
                        <div className="metric-value">
                            {accuracyMetrics?.target_achievement ? '✅' : '❌'}
                        </div>
                        <div className="metric-detail">
                            <span>目標: 95%</span>
                        </div>
                    </div>

                    <div className="metric-card">
                        <div className="metric-header">
                            <h3>評估次數</h3>
                            <span className="metric-icon">🔢</span>
                        </div>
                        <div className="metric-value">
                            {accuracyMetrics?.predictions_evaluated || 0}
                        </div>
                        <div className="metric-detail">
                            <span>總預測評估</span>
                        </div>
                    </div>
                </div>

                {/* 準確率趨勢圖 */}
                <div className="trend-chart-container">
                    <h3>準確率趨勢</h3>
                    <div className="trend-chart">
                        {accuracyTrend.length >= 2 ? (
                            <svg width="100%" height="80" viewBox="0 0 200 60">
                                <defs>
                                    <linearGradient
                                        id="trendGradient"
                                        x1="0%"
                                        y1="0%"
                                        x2="0%"
                                        y2="100%"
                                    >
                                        <stop
                                            offset="0%"
                                            stopColor="#3b82f6"
                                            stopOpacity="0.8"
                                        />
                                        <stop
                                            offset="100%"
                                            stopColor="#3b82f6"
                                            stopOpacity="0.1"
                                        />
                                    </linearGradient>
                                </defs>
                                <path
                                    d={getTrendChartPath()}
                                    fill="none"
                                    stroke="#3b82f6"
                                    strokeWidth="2"
                                />
                                <path
                                    d={`${getTrendChartPath()} L 200 60 L 0 60 Z`}
                                    fill="url(#trendGradient)"
                                />
                            </svg>
                        ) : (
                            <div className="no-data">
                                <span>📊 累積數據中...</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* 置信區間 */}
                {accuracyMetrics?.confidence_interval && (
                    <div className="confidence-interval">
                        <h3>95% 置信區間</h3>
                        <div className="interval-bar">
                            <div className="interval-range">
                                <span className="range-start">
                                    {formatPercentage(
                                        accuracyMetrics.confidence_interval[0]
                                    )}
                                </span>
                                <div className="range-bar">
                                    <div
                                        className="range-fill"
                                        style={{
                                            left: `${
                                                accuracyMetrics
                                                    .confidence_interval[0] *
                                                100
                                            }%`,
                                            width: `${
                                                (accuracyMetrics
                                                    .confidence_interval[1] -
                                                    accuracyMetrics
                                                        .confidence_interval[0]) *
                                                100
                                            }%`,
                                        }}
                                    ></div>
                                </div>
                                <span className="range-end">
                                    {formatPercentage(
                                        accuracyMetrics.confidence_interval[1]
                                    )}
                                </span>
                            </div>
                        </div>
                    </div>
                )}

                {/* 上下文準確率分析 */}
                {accuracyMetrics?.accuracy_by_context &&
                    Object.keys(accuracyMetrics.accuracy_by_context).length >
                        0 && (
                        <div className="context-analysis">
                            <h3>上下文準確率分析</h3>
                            <div className="context-grid">
                                {Object.entries(
                                    accuracyMetrics.accuracy_by_context
                                ).map(([context, accuracy]) => (
                                    <div key={context} className="context-item">
                                        <div className="context-label">
                                            {context
                                                .replace('weather_', '天氣: ')
                                                .replace(
                                                    'satellites_',
                                                    '衛星數量: '
                                                )}
                                        </div>
                                        <div className="context-value">
                                            {formatPercentage(accuracy)}
                                        </div>
                                        <div className="context-bar">
                                            <div
                                                className="context-fill"
                                                style={{
                                                    width: `${accuracy * 100}%`,
                                                    backgroundColor:
                                                        getAccuracyLevel(
                                                            accuracy
                                                        ).color,
                                                }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                {/* 優化建議 */}
                {recommendations.length > 0 && (
                    <div className="recommendations">
                        <h3>🔧 優化建議</h3>
                        <div className="recommendations-list">
                            {recommendations.map((rec) => (
                                <div
                                    key={rec.id}
                                    className={`recommendation-item ${rec.priority}`}
                                >
                                    <div className="recommendation-header">
                                        <span
                                            className={`priority-badge ${rec.priority}`}
                                        >
                                            {rec.priority === 'high' && '🔴 高'}
                                            {rec.priority === 'medium' &&
                                                '🟡 中'}
                                            {rec.priority === 'low' && '🟢 低'}
                                        </span>
                                        <span className="impact-badge">
                                            {rec.impact}
                                        </span>
                                    </div>
                                    <div className="recommendation-text">
                                        {rec.recommendation}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {loading && !accuracyMetrics && (
                <div className="refresh-indicator">
                    <div className="refresh-spinner"></div>
                    <span>更新中...</span>
                </div>
            )}
        </div>
    )
}

export default PredictionAccuracyDashboard
