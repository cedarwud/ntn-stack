/**
 * 智慧推薦系統
 *
 * 階段八：進階 AI 智慧決策與自動化調優
 * 向操作員提供智能化的最佳化建議和決策支援
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    RadialLinearScale,
} from 'chart.js'
import { Radar, Bar, Doughnut } from 'react-chartjs-2'
import './IntelligentRecommendationSystem.scss'

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    RadialLinearScale,
    Title,
    Tooltip,
    Legend
)

interface RecommendationAction {
    action_id: string
    action_type:
        | 'parameter_adjustment'
        | 'system_optimization'
        | 'maintenance'
        | 'resource_allocation'
    title: string
    description: string
    priority: 'critical' | 'high' | 'medium' | 'low'
    confidence_score: number
    estimated_impact: {
        performance_improvement: number
        cost_saving: number
        risk_reduction: number
        implementation_effort: number
    }
    implementation_steps: string[]
    prerequisites: string[]
    estimated_time_minutes: number
    category: string
    tags: string[]
}

interface RecommendationContext {
    current_performance: {
        latency_ms: number
        throughput_mbps: number
        coverage_percentage: number
        power_efficiency: number
        user_satisfaction: number
    }
    system_status: {
        cpu_utilization: number
        memory_utilization: number
        network_utilization: number
        error_rate: number
        uptime_percentage: number
    }
    recent_issues: string[]
    optimization_goals: string[]
    constraints: {
        budget_limit: number
        downtime_tolerance_minutes: number
        performance_requirements: Record<string, number>
    }
}

interface RecommendationAnalysis {
    total_recommendations: number
    recommendations_by_priority: Record<string, number>
    recommendations_by_category: Record<string, number>
    potential_improvement: number
    implementation_complexity_score: number
    estimated_roi: number
}

interface IntelligentRecommendationSystemProps {
    refreshInterval?: number
    enableRealTime?: boolean
    maxRecommendations?: number
}

const IntelligentRecommendationSystem: React.FC<
    IntelligentRecommendationSystemProps
> = ({
    refreshInterval = 60000,
    enableRealTime = true,
    // maxRecommendations = 10
}) => {
    const [recommendations, setRecommendations] = useState<
        RecommendationAction[]
    >([])
    const [context, setContext] = useState<RecommendationContext | null>(null)
    const [analysis, setAnalysis] = useState<RecommendationAnalysis | null>(
        null
    )
    const [selectedRecommendation, setSelectedRecommendation] =
        useState<RecommendationAction | null>(null)
    const [activeTab, setActiveTab] = useState<
        'overview' | 'details' | 'implementation' | 'analysis'
    >('overview')
    const [filterPriority, setFilterPriority] = useState<string>('all')
    const [filterCategory, setFilterCategory] = useState<string>('all')
    const [isLoading, setIsLoading] = useState(false)
    const [implementedActions, setImplementedActions] = useState<Set<string>>(
        new Set()
    )

    // 獲取智慧推薦
    const fetchRecommendations = useCallback(async () => {
        try {
            setIsLoading(true)

            // 獲取系統健康分析
            const healthResponse = await fetch(
                '/api/v1/ai-decision/health-analysis?include_predictions=true'
            )
            await healthResponse.json() // 暫時不使用健康數據

            // 獲取優化狀態
            const optimizationResponse = await fetch(
                '/api/v1/ai-decision/optimization/status'
            )
            await optimizationResponse.json() // 暫時不使用優化數據

            // 生成模擬推薦
            const mockRecommendations = generateIntelligentRecommendations()
            const mockContext = generateRecommendationContext()
            const mockAnalysis =
                generateRecommendationAnalysis(mockRecommendations)

            setRecommendations(mockRecommendations)
            setContext(mockContext)
            setAnalysis(mockAnalysis)

            if (!selectedRecommendation && mockRecommendations.length > 0) {
                setSelectedRecommendation(mockRecommendations[0])
            }
        } catch (error) {
            console.error('獲取智慧推薦失敗:', error)
        } finally {
            setIsLoading(false)
        }
    }, [selectedRecommendation])

    // 實施推薦
    const implementRecommendation = async (
        recommendation: RecommendationAction
    ) => {
        try {
            if (recommendation.action_type === 'parameter_adjustment') {
                // 觸發自動優化
                const response = await fetch(
                    '/api/v1/ai-decision/optimization/manual',
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            target_objectives: recommendation.estimated_impact,
                        }),
                    }
                )

                if (response.ok) {
                    setImplementedActions(
                        (prev) => new Set([...prev, recommendation.action_id])
                    )
                    alert(`推薦行動 "${recommendation.title}" 已成功實施`)
                }
            } else {
                // 其他類型的推薦
                setTimeout(() => {
                    setImplementedActions(
                        (prev) => new Set([...prev, recommendation.action_id])
                    )
                    alert(`推薦行動 "${recommendation.title}" 已標記為實施`)
                }, 1000)
            }
        } catch (error) {
            console.error('實施推薦失敗:', error)
            alert('實施推薦失敗')
        }
    }

    useEffect(() => {
        fetchRecommendations()

        if (enableRealTime) {
            const interval = setInterval(fetchRecommendations, refreshInterval)
            return () => clearInterval(interval)
        }
    }, [fetchRecommendations, enableRealTime, refreshInterval])

    // 過濾推薦
    const filteredRecommendations = recommendations.filter((rec) => {
        const priorityMatch =
            filterPriority === 'all' || rec.priority === filterPriority
        const categoryMatch =
            filterCategory === 'all' || rec.category === filterCategory
        return priorityMatch && categoryMatch
    })

    // 優先級分布圖表
    const priorityDistributionData = {
        labels: ['關鍵', '高', '中', '低'],
        datasets: [
            {
                data: analysis
                    ? [
                          analysis.recommendations_by_priority.critical || 0,
                          analysis.recommendations_by_priority.high || 0,
                          analysis.recommendations_by_priority.medium || 0,
                          analysis.recommendations_by_priority.low || 0,
                      ]
                    : [0, 0, 0, 0],
                backgroundColor: [
                    'rgba(231, 76, 60, 0.8)',
                    'rgba(255, 152, 0, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(76, 175, 80, 0.8)',
                ],
                borderColor: [
                    'rgba(231, 76, 60, 1)',
                    'rgba(255, 152, 0, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(76, 175, 80, 1)',
                ],
                borderWidth: 2,
            },
        ],
    }

    // 影響分析雷達圖
    const impactAnalysisData = {
        labels: ['性能改善', '成本節省', '風險降低', '實施難度', '用戶滿意度'],
        datasets: [
            {
                label: '預期影響',
                data: selectedRecommendation
                    ? [
                          selectedRecommendation.estimated_impact
                              .performance_improvement * 100,
                          selectedRecommendation.estimated_impact.cost_saving *
                              100,
                          selectedRecommendation.estimated_impact
                              .risk_reduction * 100,
                          100 -
                              selectedRecommendation.estimated_impact
                                  .implementation_effort *
                                  100, // 反轉實施難度
                          selectedRecommendation.confidence_score * 80 + 20, // 轉換為用戶滿意度
                      ]
                    : [0, 0, 0, 0, 0],
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                borderColor: 'rgba(52, 152, 219, 1)',
                pointBackgroundColor: 'rgba(52, 152, 219, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(52, 152, 219, 1)',
            },
        ],
    }

    // 推薦分類統計
    const categoryStatsData = {
        labels: Object.keys(analysis?.recommendations_by_category || Record<string, never>),
        datasets: [
            {
                data: Object.values(
                    analysis?.recommendations_by_category || Record<string, never>
                ),
                backgroundColor: [
                    'rgba(155, 89, 182, 0.8)',
                    'rgba(52, 152, 219, 0.8)',
                    'rgba(46, 204, 113, 0.8)',
                    'rgba(241, 196, 15, 0.8)',
                    'rgba(230, 126, 34, 0.8)',
                ],
                borderWidth: 1,
            },
        ],
    }

    const renderOverviewTab = () => (
        <div className="recommendation-overview">
            <div className="context-summary">
                <h4>系統狀態概覽</h4>
                {context && (
                    <div className="context-grid">
                        <div className="context-section">
                            <h5>性能指標</h5>
                            <div className="metrics">
                                <div className="metric">
                                    <label>延遲:</label>
                                    <span>
                                        {context.current_performance.latency_ms}
                                        ms
                                    </span>
                                </div>
                                <div className="metric">
                                    <label>吞吐量:</label>
                                    <span>
                                        {
                                            context.current_performance
                                                .throughput_mbps
                                        }
                                        Mbps
                                    </span>
                                </div>
                                <div className="metric">
                                    <label>覆蓋率:</label>
                                    <span>
                                        {
                                            context.current_performance
                                                .coverage_percentage
                                        }
                                        %
                                    </span>
                                </div>
                                <div className="metric">
                                    <label>功耗效率:</label>
                                    <span>
                                        {
                                            context.current_performance
                                                .power_efficiency
                                        }
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="context-section">
                            <h5>系統狀態</h5>
                            <div className="metrics">
                                <div className="metric">
                                    <label>CPU使用率:</label>
                                    <span>
                                        {context.system_status.cpu_utilization}%
                                    </span>
                                </div>
                                <div className="metric">
                                    <label>記憶體使用率:</label>
                                    <span>
                                        {
                                            context.system_status
                                                .memory_utilization
                                        }
                                        %
                                    </span>
                                </div>
                                <div className="metric">
                                    <label>錯誤率:</label>
                                    <span>
                                        {(
                                            context.system_status.error_rate *
                                            100
                                        ).toFixed(2)}
                                        %
                                    </span>
                                </div>
                                <div className="metric">
                                    <label>運行時間:</label>
                                    <span>
                                        {
                                            context.system_status
                                                .uptime_percentage
                                        }
                                        %
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="recommendations-summary">
                <h4>推薦統計</h4>
                {analysis && (
                    <div className="summary-stats">
                        <div className="stat-card">
                            <h5>總推薦數</h5>
                            <span className="value">
                                {analysis.total_recommendations}
                            </span>
                        </div>
                        <div className="stat-card">
                            <h5>潛在改善</h5>
                            <span className="value positive">
                                +
                                {(analysis.potential_improvement * 100).toFixed(
                                    1
                                )}
                                %
                            </span>
                        </div>
                        <div className="stat-card">
                            <h5>預期ROI</h5>
                            <span className="value">
                                {(analysis.estimated_roi * 100).toFixed(0)}%
                            </span>
                        </div>
                        <div className="stat-card">
                            <h5>實施複雜度</h5>
                            <span
                                className={`value ${
                                    analysis.implementation_complexity_score >
                                    0.7
                                        ? 'high'
                                        : analysis.implementation_complexity_score >
                                          0.4
                                        ? 'medium'
                                        : 'low'
                                }`}
                            >
                                {analysis.implementation_complexity_score > 0.7
                                    ? '高'
                                    : analysis.implementation_complexity_score >
                                      0.4
                                    ? '中'
                                    : '低'}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            <div className="charts-section">
                <div className="chart-container">
                    <h5>優先級分布</h5>
                    <Doughnut
                        data={priorityDistributionData}
                        options={{
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                },
                            },
                        }}
                    />
                </div>

                <div className="chart-container">
                    <h5>推薦分類</h5>
                    <Bar
                        data={categoryStatsData}
                        options={{
                            responsive: true,
                            plugins: {
                                legend: {
                                    display: false,
                                },
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                },
                            },
                        }}
                    />
                </div>
            </div>

            <div className="recent-issues">
                <h4>最近問題</h4>
                {context && (
                    <div className="issues-list">
                        {context.recent_issues.map((issue, index) => (
                            <div key={index} className="issue-item">
                                <span className="issue-icon">⚠️</span>
                                <span className="issue-text">{issue}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )

    const renderDetailsTab = () => (
        <div className="recommendation-details">
            <div className="filters">
                <div className="filter-group">
                    <label>優先級:</label>
                    <select
                        value={filterPriority}
                        onChange={(e) => setFilterPriority(e.target.value)}
                    >
                        <option value="all">全部</option>
                        <option value="critical">關鍵</option>
                        <option value="high">高</option>
                        <option value="medium">中</option>
                        <option value="low">低</option>
                    </select>
                </div>

                <div className="filter-group">
                    <label>分類:</label>
                    <select
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                    >
                        <option value="all">全部</option>
                        <option value="performance">性能</option>
                        <option value="reliability">可靠性</option>
                        <option value="security">安全性</option>
                        <option value="efficiency">效率</option>
                        <option value="maintenance">維護</option>
                    </select>
                </div>
            </div>

            <div className="recommendations-list">
                {filteredRecommendations.map((recommendation) => (
                    <div
                        key={recommendation.action_id}
                        className={`recommendation-card ${
                            selectedRecommendation?.action_id ===
                            recommendation.action_id
                                ? 'selected'
                                : ''
                        } ${
                            implementedActions.has(recommendation.action_id)
                                ? 'implemented'
                                : ''
                        }`}
                        onClick={() =>
                            setSelectedRecommendation(recommendation)
                        }
                    >
                        <div className="recommendation-header">
                            <div className="title-section">
                                <h5>{recommendation.title}</h5>
                                <div className="tags">
                                    {recommendation.tags.map((tag, index) => (
                                        <span key={index} className="tag">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div className="priority-section">
                                <span
                                    className={`priority ${recommendation.priority}`}
                                >
                                    {recommendation.priority === 'critical'
                                        ? '關鍵'
                                        : recommendation.priority === 'high'
                                        ? '高'
                                        : recommendation.priority === 'medium'
                                        ? '中'
                                        : '低'}
                                </span>
                                <span className="confidence">
                                    信心度:{' '}
                                    {(
                                        recommendation.confidence_score * 100
                                    ).toFixed(0)}
                                    %
                                </span>
                            </div>
                        </div>

                        <div className="recommendation-description">
                            <p>{recommendation.description}</p>
                        </div>

                        <div className="recommendation-impact">
                            <div className="impact-metrics">
                                <div className="impact-item">
                                    <label>性能改善:</label>
                                    <span className="positive">
                                        +
                                        {(
                                            recommendation.estimated_impact
                                                .performance_improvement * 100
                                        ).toFixed(1)}
                                        %
                                    </span>
                                </div>
                                <div className="impact-item">
                                    <label>成本節省:</label>
                                    <span className="positive">
                                        +
                                        {(
                                            recommendation.estimated_impact
                                                .cost_saving * 100
                                        ).toFixed(1)}
                                        %
                                    </span>
                                </div>
                                <div className="impact-item">
                                    <label>實施時間:</label>
                                    <span>
                                        {recommendation.estimated_time_minutes}
                                        分鐘
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="recommendation-actions">
                            <button
                                className={`implement-button ${
                                    implementedActions.has(
                                        recommendation.action_id
                                    )
                                        ? 'implemented'
                                        : ''
                                }`}
                                onClick={(e) => {
                                    e.stopPropagation()
                                    implementRecommendation(recommendation)
                                }}
                                disabled={implementedActions.has(
                                    recommendation.action_id
                                )}
                            >
                                {implementedActions.has(
                                    recommendation.action_id
                                )
                                    ? '已實施'
                                    : '實施'}
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )

    const renderImplementationTab = () => (
        <div className="recommendation-implementation">
            {selectedRecommendation && (
                <>
                    <div className="implementation-header">
                        <h4>{selectedRecommendation.title}</h4>
                        <span
                            className={`status ${
                                implementedActions.has(
                                    selectedRecommendation.action_id
                                )
                                    ? 'implemented'
                                    : 'pending'
                            }`}
                        >
                            {implementedActions.has(
                                selectedRecommendation.action_id
                            )
                                ? '已實施'
                                : '待實施'}
                        </span>
                    </div>

                    <div className="implementation-details">
                        <div className="prerequisites-section">
                            <h5>前置條件</h5>
                            <div className="prerequisites-list">
                                {selectedRecommendation.prerequisites.map(
                                    (prerequisite, index) => (
                                        <div
                                            key={index}
                                            className="prerequisite-item"
                                        >
                                            <span className="prerequisite-icon">
                                                📋
                                            </span>
                                            <span className="prerequisite-text">
                                                {prerequisite}
                                            </span>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>

                        <div className="steps-section">
                            <h5>實施步驟</h5>
                            <div className="steps-list">
                                {selectedRecommendation.implementation_steps.map(
                                    (step, index) => (
                                        <div key={index} className="step-item">
                                            <span className="step-number">
                                                {index + 1}
                                            </span>
                                            <span className="step-text">
                                                {step}
                                            </span>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>

                        <div className="impact-visualization">
                            <h5>預期影響分析</h5>
                            <Radar
                                data={impactAnalysisData}
                                options={{
                                    responsive: true,
                                    scales: {
                                        r: {
                                            beginAtZero: true,
                                            max: 100,
                                            ticks: {
                                                callback: function (value) {
                                                    return value + '%'
                                                },
                                            },
                                        },
                                    },
                                }}
                            />
                        </div>
                    </div>

                    <div className="implementation-footer">
                        <div className="time-estimate">
                            <label>預計實施時間:</label>
                            <span>
                                {selectedRecommendation.estimated_time_minutes}
                                分鐘
                            </span>
                        </div>

                        <div className="risk-assessment">
                            <label>實施風險:</label>
                            <span
                                className={`risk ${
                                    selectedRecommendation.estimated_impact
                                        .implementation_effort > 0.7
                                        ? 'high'
                                        : selectedRecommendation
                                              .estimated_impact
                                              .implementation_effort > 0.4
                                        ? 'medium'
                                        : 'low'
                                }`}
                            >
                                {selectedRecommendation.estimated_impact
                                    .implementation_effort > 0.7
                                    ? '高風險'
                                    : selectedRecommendation.estimated_impact
                                          .implementation_effort > 0.4
                                    ? '中風險'
                                    : '低風險'}
                            </span>
                        </div>

                        <button
                            className={`implement-main-button ${
                                implementedActions.has(
                                    selectedRecommendation.action_id
                                )
                                    ? 'implemented'
                                    : ''
                            }`}
                            onClick={() =>
                                implementRecommendation(selectedRecommendation)
                            }
                            disabled={implementedActions.has(
                                selectedRecommendation.action_id
                            )}
                        >
                            {implementedActions.has(
                                selectedRecommendation.action_id
                            )
                                ? '✓ 已實施'
                                : '🚀 立即實施'}
                        </button>
                    </div>
                </>
            )}
        </div>
    )

    const renderAnalysisTab = () => (
        <div className="recommendation-analysis">
            {analysis && (
                <>
                    <div className="analysis-summary">
                        <h4>分析摘要</h4>
                        <div className="analysis-grid">
                            <div className="analysis-item">
                                <label>總體改善潛力:</label>
                                <span className="value positive">
                                    +
                                    {(
                                        analysis.potential_improvement * 100
                                    ).toFixed(1)}
                                    %
                                </span>
                            </div>
                            <div className="analysis-item">
                                <label>實施複雜度:</label>
                                <span
                                    className={`value ${
                                        analysis.implementation_complexity_score >
                                        0.7
                                            ? 'high'
                                            : analysis.implementation_complexity_score >
                                              0.4
                                            ? 'medium'
                                            : 'low'
                                    }`}
                                >
                                    {(
                                        analysis.implementation_complexity_score *
                                        100
                                    ).toFixed(0)}
                                    %
                                </span>
                            </div>
                            <div className="analysis-item">
                                <label>投資回報率:</label>
                                <span className="value">
                                    {(analysis.estimated_roi * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="priority-breakdown">
                        <h4>優先級分解</h4>
                        <div className="priority-items">
                            {Object.entries(
                                analysis.recommendations_by_priority
                            ).map(([priority, count]) => (
                                <div key={priority} className="priority-item">
                                    <span
                                        className={`priority-label ${priority}`}
                                    >
                                        {priority === 'critical'
                                            ? '關鍵'
                                            : priority === 'high'
                                            ? '高'
                                            : priority === 'medium'
                                            ? '中'
                                            : '低'}
                                    </span>
                                    <span className="priority-count">
                                        {count}項
                                    </span>
                                    <div className="priority-bar">
                                        <div
                                            className="priority-fill"
                                            style={{
                                                width: `${
                                                    (count /
                                                        analysis.total_recommendations) *
                                                    100
                                                }%`,
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="category-analysis">
                        <h4>分類分析</h4>
                        <div className="category-chart">
                            <Doughnut
                                data={categoryStatsData}
                                options={{
                                    responsive: true,
                                    plugins: {
                                        legend: {
                                            position: 'right',
                                        },
                                    },
                                }}
                            />
                        </div>
                    </div>

                    <div className="implementation-roadmap">
                        <h4>實施路線圖</h4>
                        <div className="roadmap-steps">
                            <div className="roadmap-step">
                                <div className="step-header">
                                    <span className="step-phase">
                                        第一階段 (立即)
                                    </span>
                                    <span className="step-duration">
                                        0-1小時
                                    </span>
                                </div>
                                <div className="step-actions">
                                    {filteredRecommendations
                                        .filter(
                                            (r) => r.priority === 'critical'
                                        )
                                        .slice(0, 3)
                                        .map((r) => (
                                            <span
                                                key={r.action_id}
                                                className="action-item critical"
                                            >
                                                {r.title}
                                            </span>
                                        ))}
                                </div>
                            </div>

                            <div className="roadmap-step">
                                <div className="step-header">
                                    <span className="step-phase">
                                        第二階段 (短期)
                                    </span>
                                    <span className="step-duration">
                                        1-24小時
                                    </span>
                                </div>
                                <div className="step-actions">
                                    {filteredRecommendations
                                        .filter((r) => r.priority === 'high')
                                        .slice(0, 3)
                                        .map((r) => (
                                            <span
                                                key={r.action_id}
                                                className="action-item high"
                                            >
                                                {r.title}
                                            </span>
                                        ))}
                                </div>
                            </div>

                            <div className="roadmap-step">
                                <div className="step-header">
                                    <span className="step-phase">
                                        第三階段 (中期)
                                    </span>
                                    <span className="step-duration">1-7天</span>
                                </div>
                                <div className="step-actions">
                                    {filteredRecommendations
                                        .filter((r) => r.priority === 'medium')
                                        .slice(0, 3)
                                        .map((r) => (
                                            <span
                                                key={r.action_id}
                                                className="action-item medium"
                                            >
                                                {r.title}
                                            </span>
                                        ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    )

    return (
        <div className="intelligent-recommendation-system">
            <div className="system-header">
                <h3>智慧推薦系統</h3>
                <div className="header-controls">
                    <div className="status-indicator">
                        {enableRealTime && (
                            <span
                                className={`indicator ${
                                    isLoading ? 'loading' : 'active'
                                }`}
                            >
                                智能分析中
                            </span>
                        )}
                    </div>
                    <button
                        onClick={fetchRecommendations}
                        disabled={isLoading}
                        className="refresh-button"
                    >
                        🔄 刷新推薦
                    </button>
                </div>
            </div>

            <div className="system-tabs">
                <button
                    className={`tab ${
                        activeTab === 'overview' ? 'active' : ''
                    }`}
                    onClick={() => setActiveTab('overview')}
                >
                    系統總覽
                </button>
                <button
                    className={`tab ${activeTab === 'details' ? 'active' : ''}`}
                    onClick={() => setActiveTab('details')}
                >
                    推薦詳情
                </button>
                <button
                    className={`tab ${
                        activeTab === 'implementation' ? 'active' : ''
                    }`}
                    onClick={() => setActiveTab('implementation')}
                >
                    實施指南
                </button>
                <button
                    className={`tab ${
                        activeTab === 'analysis' ? 'active' : ''
                    }`}
                    onClick={() => setActiveTab('analysis')}
                >
                    分析報告
                </button>
            </div>

            <div className="system-content">
                {activeTab === 'overview' && renderOverviewTab()}
                {activeTab === 'details' && renderDetailsTab()}
                {activeTab === 'implementation' && renderImplementationTab()}
                {activeTab === 'analysis' && renderAnalysisTab()}
            </div>
        </div>
    )
}

// 輔助函數
function generateIntelligentRecommendations(): RecommendationAction[] {
    const recommendations: RecommendationAction[] = [
        {
            action_id: 'opt_gnb_power_001',
            action_type: 'parameter_adjustment',
            title: '優化 gNodeB 發射功率',
            description:
                '根據當前干擾情況和覆蓋需求，建議調整 gNodeB 發射功率以提升能效比。',
            priority: 'high',
            confidence_score: 0.89,
            estimated_impact: {
                performance_improvement: 0.15,
                cost_saving: 0.12,
                risk_reduction: 0.08,
                implementation_effort: 0.3,
            },
            implementation_steps: [
                '分析當前功率使用模式',
                '計算最優功率配置',
                '執行功率調整',
                '監控性能變化',
                '根據結果微調',
            ],
            prerequisites: ['確保無活躍用戶連接', '備份當前配置'],
            estimated_time_minutes: 15,
            category: 'performance',
            tags: ['功率優化', '能效', '自動調整'],
        },
        {
            action_id: 'maint_predict_001',
            action_type: 'maintenance',
            title: '預防性維護檢查',
            description:
                'AI 預測模型顯示部分組件有潛在故障風險，建議進行預防性檢查。',
            priority: 'medium',
            confidence_score: 0.76,
            estimated_impact: {
                performance_improvement: 0.08,
                cost_saving: 0.25,
                risk_reduction: 0.35,
                implementation_effort: 0.4,
            },
            implementation_steps: [
                '檢查硬體組件狀態',
                '更新軟體版本',
                '清理系統日誌',
                '驗證系統完整性',
                '制定維護計劃',
            ],
            prerequisites: ['安排維護窗口', '準備備用設備'],
            estimated_time_minutes: 45,
            category: 'maintenance',
            tags: ['預防性維護', '故障預測', '系統健康'],
        },
        {
            action_id: 'sec_update_001',
            action_type: 'system_optimization',
            title: '安全性配置更新',
            description:
                '檢測到部分安全配置可以進一步優化，建議更新以提升系統安全性。',
            priority: 'high',
            confidence_score: 0.92,
            estimated_impact: {
                performance_improvement: 0.05,
                cost_saving: 0.03,
                risk_reduction: 0.45,
                implementation_effort: 0.25,
            },
            implementation_steps: [
                '審查當前安全策略',
                '更新防火牆規則',
                '強化認證機制',
                '啟用監控告警',
                '驗證安全性改善',
            ],
            prerequisites: ['備份安全配置', '通知相關人員'],
            estimated_time_minutes: 30,
            category: 'security',
            tags: ['安全性', '配置優化', '風險降低'],
        },
        {
            action_id: 'res_alloc_001',
            action_type: 'resource_allocation',
            title: '動態資源分配優化',
            description:
                '基於使用模式分析，建議重新分配計算和網路資源以提升整體效率。',
            priority: 'medium',
            confidence_score: 0.81,
            estimated_impact: {
                performance_improvement: 0.18,
                cost_saving: 0.15,
                risk_reduction: 0.1,
                implementation_effort: 0.35,
            },
            implementation_steps: [
                '分析資源使用模式',
                '計算最優分配方案',
                '逐步調整資源分配',
                '監控性能指標',
                '優化分配策略',
            ],
            prerequisites: ['確保資源監控正常', '制定回滾計劃'],
            estimated_time_minutes: 25,
            category: 'efficiency',
            tags: ['資源優化', '動態分配', '效率提升'],
        },
        {
            action_id: 'ai_model_001',
            action_type: 'system_optimization',
            title: 'AI 模型參數調優',
            description:
                '根據最新學習數據，建議重新訓練和調優 AI 決策模型以提升準確性。',
            priority: 'low',
            confidence_score: 0.73,
            estimated_impact: {
                performance_improvement: 0.12,
                cost_saving: 0.08,
                risk_reduction: 0.06,
                implementation_effort: 0.6,
            },
            implementation_steps: [
                '準備訓練數據集',
                '配置訓練參數',
                '執行模型訓練',
                '驗證模型性能',
                '部署更新模型',
            ],
            prerequisites: ['確保足夠計算資源', '備份現有模型'],
            estimated_time_minutes: 60,
            category: 'reliability',
            tags: ['AI模型', '機器學習', '準確性提升'],
        },
    ]

    return recommendations
}

function generateRecommendationContext(): RecommendationContext {
    return {
        current_performance: {
            latency_ms: 42,
            throughput_mbps: 78,
            coverage_percentage: 85,
            power_efficiency: 0.75,
            user_satisfaction: 8.2,
        },
        system_status: {
            cpu_utilization: 68,
            memory_utilization: 72,
            network_utilization: 45,
            error_rate: 0.015,
            uptime_percentage: 99.7,
        },
        recent_issues: [
            'CPU 使用率偶爾超過 80%',
            '部分區域覆蓋率略低於預期',
            '網路延遲在高峰時段增加',
            '記憶體使用量持續增長',
        ],
        optimization_goals: [
            '提升系統穩定性',
            '降低運營成本',
            '改善用戶體驗',
            '增強安全性',
        ],
        constraints: {
            budget_limit: 10000,
            downtime_tolerance_minutes: 5,
            performance_requirements: {
                min_throughput: 50,
                max_latency: 50,
                min_coverage: 80,
            },
        },
    }
}

function generateRecommendationAnalysis(
    recommendations: RecommendationAction[]
): RecommendationAnalysis {
    const priorityCounts = recommendations.reduce((acc, rec) => {
        acc[rec.priority] = (acc[rec.priority] || 0) + 1
        return acc
    }, Record<string, never> as Record<string, number>)

    const categoryCounts = recommendations.reduce((acc, rec) => {
        acc[rec.category] = (acc[rec.category] || 0) + 1
        return acc
    }, Record<string, never> as Record<string, number>)

    const avgImprovement =
        recommendations.reduce(
            (sum, rec) => sum + rec.estimated_impact.performance_improvement,
            0
        ) / recommendations.length

    const avgComplexity =
        recommendations.reduce(
            (sum, rec) => sum + rec.estimated_impact.implementation_effort,
            0
        ) / recommendations.length

    return {
        total_recommendations: recommendations.length,
        recommendations_by_priority: priorityCounts,
        recommendations_by_category: categoryCounts,
        potential_improvement: avgImprovement,
        implementation_complexity_score: avgComplexity,
        estimated_roi: 2.3,
    }
}

export default IntelligentRecommendationSystem
