import React, { memo, useState, useCallback } from 'react'
import './VisualizationSection.scss'

interface VisualizationSectionProps {
    data?: {
        featureImportance: {
            type: string
            format: string
            data: any
            metadata?: {
                algorithm?: string
                timestamp?: string
                confidence?: number
            }
        }
        decisionExplanation: {
            decision_id: string
            algorithm: string
            input_features: Record<string, number>
            output_action: any
            confidence: number
            reasoning: {
                feature_importance: Record<string, number>
                decision_path: any[]
                q_values?: Record<string, number>
                policy_output?: any
            }
            timestamp: string
        }
        algorithmComparison: {
            algorithms: string[]
            metrics: Record<string, Record<string, number>>
            radar_chart_data?: any
            convergence_data?: Record<string, number[]>
            statistical_tests?: Record<string, any>
        }
    }
    onRefresh?: () => void
}

const VisualizationSection: React.FC<VisualizationSectionProps> = ({
    data,
    onRefresh,
}) => {
    const [activeVisualization, setActiveVisualization] =
        useState<string>('features')
    const [isGenerating, setIsGenerating] = useState(false)

    // 特徵重要性數據處理
    const featureImportanceData = data?.featureImportance?.data || {}
    const hasFeatureData = Object.keys(featureImportanceData).length > 0

    // 決策解釋數據處理
    const decisionData = data?.decisionExplanation
    const hasDecisionData = decisionData && decisionData.decision_id

    // 算法比較數據處理
    const comparisonData = data?.algorithmComparison
    const hasComparisonData =
        comparisonData && comparisonData.algorithms?.length > 0

    // 生成新的視覺化
    const handleGenerateVisualization = useCallback(
        async (type: string) => {
            setIsGenerating(true)
            try {
                console.log(`正在生成 ${type} 視覺化...`)

                // 調用 Phase 3 視覺化 API
                const response = await fetch(
                    '/api/v1/rl/phase-3/visualizations/generate',
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            chart_type: type,
                            data_source: 'current_training',
                            format: 'plotly',
                            algorithm: 'all',
                        }),
                    }
                )

                if (response.ok) {
                    const result = await response.json()
                    console.log('視覺化生成成功:', result)
                    if (onRefresh) {
                        onRefresh()
                    }
                } else {
                    console.warn('視覺化生成失敗:', response.status)
                }
            } catch (error) {
                console.error('視覺化生成錯誤:', error)
            } finally {
                setIsGenerating(false)
            }
        },
        [onRefresh]
    )

    // 渲染特徵重要性圖表
    const renderFeatureImportance = () => {
        if (!hasFeatureData) {
            return (
                <div className="placeholder-visualization">
                    <div className="placeholder-content">
                        <div className="placeholder-icon">📊</div>
                        <div className="placeholder-title">特徵重要性分析</div>
                        <div className="placeholder-text">
                            此視覺化將顯示每個輸入特徵對算法決策的影響程度
                        </div>
                        <button
                            className="generate-btn"
                            onClick={() =>
                                handleGenerateVisualization(
                                    'feature_importance'
                                )
                            }
                            disabled={isGenerating}
                        >
                            {isGenerating ? '生成中...' : '生成特徵重要性圖表'}
                        </button>
                    </div>
                </div>
            )
        }

        // 模擬特徵重要性數據
        const features = [
            {
                name: '衛星距離',
                importance: 0.85,
                description: '目標衛星與用戶的距離',
            },
            {
                name: '信號強度',
                importance: 0.72,
                description: '當前信號接收強度',
            },
            {
                name: '載荷狀況',
                importance: 0.68,
                description: '衛星當前載荷負載情況',
            },
            {
                name: '天氣條件',
                importance: 0.45,
                description: '環境天氣對信號的影響',
            },
            {
                name: '電池電量',
                importance: 0.38,
                description: '衛星電池剩餘電量',
            },
            {
                name: '軌道角度',
                importance: 0.32,
                description: '衛星相對地面的角度',
            },
        ]

        return (
            <div className="feature-importance-chart">
                <div className="chart-header">
                    <h4 className="chart-title">特徵重要性分析</h4>
                    <div className="chart-info">
                        <span className="algorithm-badge">
                            {data?.featureImportance?.metadata?.algorithm?.toUpperCase() ||
                                'ALL'}
                        </span>
                        <span className="confidence-badge">
                            置信度:{' '}
                            {(
                                (data?.featureImportance?.metadata
                                    ?.confidence || 0.85) * 100
                            ).toFixed(1)}
                            %
                        </span>
                    </div>
                </div>

                <div className="features-list">
                    {features.map((feature, index) => (
                        <div key={index} className="feature-item">
                            <div className="feature-info">
                                <div className="feature-name">
                                    {feature.name}
                                </div>
                                <div className="feature-description">
                                    {feature.description}
                                </div>
                            </div>
                            <div className="importance-bar">
                                <div
                                    className="importance-fill"
                                    style={{
                                        width: `${feature.importance * 100}%`,
                                        backgroundColor: `hsl(${
                                            120 * feature.importance
                                        }, 70%, 50%)`,
                                    }}
                                ></div>
                                <span className="importance-value">
                                    {(feature.importance * 100).toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    // 渲染決策解釋
    const renderDecisionExplanation = () => {
        if (!hasDecisionData) {
            return (
                <div className="placeholder-visualization">
                    <div className="placeholder-content">
                        <div className="placeholder-icon">🧠</div>
                        <div className="placeholder-title">決策解釋分析</div>
                        <div className="placeholder-text">
                            此視覺化將展示算法的決策過程和推理邏輯
                        </div>
                        <button
                            className="generate-btn"
                            onClick={() =>
                                handleGenerateVisualization(
                                    'decision_explanation'
                                )
                            }
                            disabled={isGenerating}
                        >
                            {isGenerating ? '生成中...' : '生成決策解釋'}
                        </button>
                    </div>
                </div>
            )
        }

        // 模擬決策數據
        const mockDecision = {
            current_state: {
                用戶位置: [120.15, 24.16],
                當前衛星ID: 'SAT_001',
                信號質量: 0.72,
                載荷狀況: 0.68,
            },
            decision_process: [
                {
                    step: 1,
                    action: '掃描可用衛星',
                    result: '發現3個候選衛星',
                    confidence: 0.95,
                },
                {
                    step: 2,
                    action: '評估信號品質',
                    result: 'SAT_003 信號最強',
                    confidence: 0.87,
                },
                {
                    step: 3,
                    action: '檢查載荷狀況',
                    result: 'SAT_003 載荷適中',
                    confidence: 0.79,
                },
                {
                    step: 4,
                    action: '計算切換成本',
                    result: '切換成本可接受',
                    confidence: 0.82,
                },
                {
                    step: 5,
                    action: '最終決策',
                    result: '切換至 SAT_003',
                    confidence: 0.89,
                },
            ],
            q_values: {
                keep_current: 0.45,
                switch_to_sat003: 0.89,
                switch_to_sat005: 0.62,
            },
        }

        return (
            <div className="decision-explanation">
                <div className="explanation-header">
                    <h4 className="explanation-title">決策過程解釋</h4>
                    <div className="decision-info">
                        <span className="algorithm-badge">
                            {decisionData?.algorithm?.toUpperCase() || 'DQN'}
                        </span>
                        <span className="confidence-badge">
                            總體置信度:{' '}
                            {((decisionData?.confidence || 0.89) * 100).toFixed(
                                1
                            )}
                            %
                        </span>
                    </div>
                </div>

                <div className="current-state">
                    <h5 className="state-title">📍 當前狀態</h5>
                    <div className="state-grid">
                        {Object.entries(mockDecision.current_state).map(
                            ([key, value], index) => (
                                <div key={index} className="state-item">
                                    <span className="state-label">{key}:</span>
                                    <span className="state-value">
                                        {Array.isArray(value)
                                            ? `[${value.join(', ')}]`
                                            : value}
                                    </span>
                                </div>
                            )
                        )}
                    </div>
                </div>

                <div className="decision-steps">
                    <h5 className="steps-title">🔄 決策步驟</h5>
                    <div className="steps-timeline">
                        {mockDecision.decision_process.map((step, index) => (
                            <div key={index} className="step-item">
                                <div className="step-number">{step.step}</div>
                                <div className="step-content">
                                    <div className="step-action">
                                        {step.action}
                                    </div>
                                    <div className="step-result">
                                        {step.result}
                                    </div>
                                    <div className="step-confidence">
                                        置信度:{' '}
                                        {(step.confidence * 100).toFixed(1)}%
                                    </div>
                                </div>
                                <div
                                    className="confidence-indicator"
                                    style={{
                                        backgroundColor: `hsl(${
                                            120 * step.confidence
                                        }, 70%, 50%)`,
                                    }}
                                ></div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="q-values">
                    <h5 className="qvalues-title">📊 行動價值 (Q-Values)</h5>
                    <div className="qvalues-bars">
                        {Object.entries(mockDecision.q_values).map(
                            ([action, value], index) => (
                                <div key={index} className="qvalue-item">
                                    <div className="action-name">
                                        {action.replace(/_/g, ' ')}
                                    </div>
                                    <div className="qvalue-bar">
                                        <div
                                            className="qvalue-fill"
                                            style={{
                                                width: `${
                                                    (value as number) * 100
                                                }%`,
                                                backgroundColor:
                                                    value ===
                                                    Math.max(
                                                        ...Object.values(
                                                            mockDecision.q_values
                                                        )
                                                    )
                                                        ? '#10b981'
                                                        : '#6b7280',
                                            }}
                                        ></div>
                                        <span className="qvalue-text">
                                            {(value as number).toFixed(3)}
                                        </span>
                                    </div>
                                </div>
                            )
                        )}
                    </div>
                </div>
            </div>
        )
    }

    // 渲染算法比較雷達圖
    const renderAlgorithmComparison = () => {
        if (!hasComparisonData) {
            return (
                <div className="placeholder-visualization">
                    <div className="placeholder-content">
                        <div className="placeholder-icon">📈</div>
                        <div className="placeholder-title">算法比較分析</div>
                        <div className="placeholder-text">
                            此視覺化將顯示不同算法在各個維度的性能對比
                        </div>
                        <button
                            className="generate-btn"
                            onClick={() =>
                                handleGenerateVisualization(
                                    'algorithm_comparison'
                                )
                            }
                            disabled={isGenerating}
                        >
                            {isGenerating ? '生成中...' : '生成算法比較圖表'}
                        </button>
                    </div>
                </div>
            )
        }

        // 模擬雷達圖數據
        const radarData = {
            metrics: ['準確率', '收斂速度', '穩定性', '效率', '魯棒性'],
            algorithms: [
                {
                    name: 'DQN',
                    values: [0.85, 0.7, 0.9, 0.75, 0.8],
                    color: '#3b82f6',
                },
                {
                    name: 'PPO',
                    values: [0.78, 0.85, 0.75, 0.85, 0.75],
                    color: '#10b981',
                },
                {
                    name: 'SAC',
                    values: [0.82, 0.8, 0.7, 0.8, 0.85],
                    color: '#f59e0b',
                },
            ],
        }

        return (
            <div className="algorithm-comparison-radar">
                <div className="radar-header">
                    <h4 className="radar-title">算法性能雷達圖</h4>
                    <div className="algorithms-legend">
                        {radarData.algorithms.map((algo, index) => (
                            <div key={index} className="legend-item">
                                <div
                                    className="legend-color"
                                    style={{ backgroundColor: algo.color }}
                                ></div>
                                <span className="legend-name">{algo.name}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="radar-container">
                    {/* 這裡會是實際的雷達圖，目前顯示表格形式 */}
                    <div className="metrics-comparison-table">
                        <div className="table-header">
                            <div className="metric-col">指標</div>
                            {radarData.algorithms.map((algo, index) => (
                                <div
                                    key={index}
                                    className="algo-col"
                                    style={{ color: algo.color }}
                                >
                                    {algo.name}
                                </div>
                            ))}
                        </div>
                        {radarData.metrics.map((metric, metricIndex) => (
                            <div key={metricIndex} className="table-row">
                                <div className="metric-col">{metric}</div>
                                {radarData.algorithms.map((algo, algoIndex) => (
                                    <div key={algoIndex} className="algo-col">
                                        <div className="performance-cell">
                                            <div
                                                className="performance-bar"
                                                style={{
                                                    width: `${
                                                        algo.values[
                                                            metricIndex
                                                        ] * 100
                                                    }%`,
                                                    backgroundColor: algo.color,
                                                }}
                                            ></div>
                                            <span className="performance-value">
                                                {(
                                                    algo.values[metricIndex] *
                                                    100
                                                ).toFixed(0)}
                                                %
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )
    }

    const visualizationTabs = [
        {
            id: 'features',
            label: '特徵重要性',
            icon: '📊',
            component: renderFeatureImportance,
        },
        {
            id: 'decision',
            label: '決策解釋',
            icon: '🧠',
            component: renderDecisionExplanation,
        },
        {
            id: 'comparison',
            label: '算法比較',
            icon: '📈',
            component: renderAlgorithmComparison,
        },
    ]

    return (
        <div className="visualization-section">
            <div className="section-header">
                <h2 className="section-title">👁️ 決策透明化視覺分析</h2>
                <div className="section-controls">
                    <button
                        className="refresh-btn"
                        onClick={onRefresh}
                        title="刷新數據"
                    >
                        🔄
                    </button>
                </div>
            </div>

            <div className="phase3-badge">
                <span className="badge-icon">🎯</span>
                <span className="badge-text">Phase 3 決策透明化引擎</span>
                <span className="badge-status">已整合</span>
            </div>

            {/* 視覺化選項卡 */}
            <div className="visualization-tabs">
                <div className="tabs-nav">
                    {visualizationTabs.map((tab) => (
                        <button
                            key={tab.id}
                            className={`vis-tab ${
                                activeVisualization === tab.id
                                    ? 'vis-tab--active'
                                    : ''
                            }`}
                            onClick={() => setActiveVisualization(tab.id)}
                        >
                            <span className="tab-icon">{tab.icon}</span>
                            <span className="tab-label">{tab.label}</span>
                        </button>
                    ))}
                </div>

                <div className="tab-content">
                    {visualizationTabs
                        .find((tab) => tab.id === activeVisualization)
                        ?.component()}
                </div>
            </div>

            {/* 說明文字 */}
            <div className="visualization-info">
                <div className="info-card">
                    <h4 className="info-title">💡 視覺化說明</h4>
                    <div className="info-content">
                        <p>
                            <strong>特徵重要性</strong>
                            ：顯示每個輸入特徵對算法決策的影響程度，
                            幫助理解哪些因素最重要。
                        </p>
                        <p>
                            <strong>決策解釋</strong>
                            ：展示算法的完整決策過程，包括每個步驟的
                            推理邏輯和置信度。
                        </p>
                        <p>
                            <strong>算法比較</strong>
                            ：通過雷達圖和統計分析對比不同算法在各個
                            性能維度的表現。
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default memo(VisualizationSection)
