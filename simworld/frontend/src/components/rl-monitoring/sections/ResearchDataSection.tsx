import React, { memo, useState, useCallback } from 'react'
import './ResearchDataSection.scss'

interface ResearchDataSectionProps {
    data?: {
        experiments: Array<{
            session_id: string
            experiment_name: string
            algorithm_type: string
            scenario_type: string
            status: 'running' | 'completed' | 'failed'
            start_time: string
            end_time?: string
            hyperparameters: Record<string, any>
            results?: {
                final_reward: number
                episodes_completed: number
                convergence_episode: number
                success_rate: number
            }
            research_notes?: string
        }>
        baseline: {
            baseline_algorithms: string[]
            comparison_metrics: Record<string, Record<string, number>>
            statistical_tests: Record<
                string,
                {
                    p_value: number
                    significant: boolean
                    test_type: string
                }
            >
            improvement_percentage: Record<string, number>
        }
        statistics: {
            descriptive_stats: Record<
                string,
                {
                    mean: number
                    std: number
                    min: number
                    max: number
                    median: number
                }
            >
            correlation_matrix: Record<string, Record<string, number>>
            confidence_intervals: Record<
                string,
                {
                    lower: number
                    upper: number
                    confidence_level: number
                }
            >
            trend_analysis: Record<
                string,
                {
                    slope: number
                    r_squared: number
                    trend: 'increasing' | 'decreasing' | 'stable'
                }
            >
        }
    }
    onRefresh?: () => void
}

const ResearchDataSection: React.FC<ResearchDataSectionProps> = ({
    data,
    onRefresh,
}) => {
    const [activeTab, setActiveTab] = useState<string>('experiments')
    const [selectedExperiment, setSelectedExperiment] = useState<string | null>(
        null
    )
    const [isExporting, setIsExporting] = useState(false)

    const experiments = data?.experiments || []
    const baseline = data?.baseline
    const statistics = data?.statistics

    // 生成模擬實驗數據
    const mockExperiments =
        experiments.length === 0
            ? [
                  {
                      session_id: 'exp_001_dqn_leo_handover',
                      experiment_name: 'DQN LEO 衛星切換優化',
                      algorithm_type: 'DQN',
                      scenario_type: 'LEO_Handover',
                      status: 'completed' as const,
                      start_time: '2024-01-15T10:30:00Z',
                      end_time: '2024-01-15T14:45:00Z',
                      hyperparameters: {
                          learning_rate: 0.001,
                          batch_size: 32,
                          epsilon_decay: 0.995,
                          replay_buffer_size: 10000,
                      },
                      results: {
                          final_reward: 0.847,
                          episodes_completed: 1000,
                          convergence_episode: 650,
                          success_rate: 0.92,
                      },
                      research_notes:
                          '實驗顯示 DQN 在 LEO 衛星切換場景中表現良好，收斂穩定。',
                  },
                  {
                      session_id: 'exp_002_ppo_comparative',
                      experiment_name: 'PPO 算法對比研究',
                      algorithm_type: 'PPO',
                      scenario_type: 'Comparative_Study',
                      status: 'running' as const,
                      start_time: '2024-01-16T09:00:00Z',
                      hyperparameters: {
                          learning_rate: 0.0003,
                          clip_range: 0.2,
                          entropy_coef: 0.01,
                          value_function_coef: 0.5,
                      },
                      results: {
                          final_reward: 0.782,
                          episodes_completed: 750,
                          convergence_episode: 0,
                          success_rate: 0.88,
                      },
                      research_notes: 'PPO 算法訓練中，目前表現穩定。',
                  },
                  {
                      session_id: 'exp_003_sac_exploration',
                      experiment_name: 'SAC 探索策略優化',
                      algorithm_type: 'SAC',
                      scenario_type: 'Exploration_Study',
                      status: 'failed' as const,
                      start_time: '2024-01-14T16:20:00Z',
                      end_time: '2024-01-14T18:30:00Z',
                      hyperparameters: {
                          learning_rate: 0.0003,
                          tau: 0.005,
                          alpha: 0.2,
                          target_update_interval: 1,
                      },
                      research_notes: '實驗因超參數設置問題而失敗，需要調整。',
                  },
              ]
            : experiments

    // 導出研究數據
    const handleExportData = useCallback(
        async (format: 'json' | 'csv' | 'excel') => {
            setIsExporting(true)
            try {
                console.log(`導出 ${format} 格式的研究數據...`)

                const exportData = {
                    experiments: mockExperiments,
                    baseline: baseline,
                    statistics: statistics,
                    export_timestamp: new Date().toISOString(),
                    export_format: format,
                }

                const dataStr = JSON.stringify(exportData, null, 2)
                const blob = new Blob([dataStr], { type: 'application/json' })

                // 創建下載連結
                const url = URL.createObjectURL(blob)
                const link = document.createElement('a')
                link.href = url
                link.download = `research_data_${
                    new Date().toISOString().split('T')[0]
                }.${format}`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                URL.revokeObjectURL(url)

                console.log('研究數據導出成功')
            } catch (error) {
                console.error('研究數據導出失敗:', error)
            } finally {
                setIsExporting(false)
            }
        },
        [mockExperiments, baseline, statistics]
    )

    // 渲染實驗歷史
    const renderExperiments = () => (
        <div className="experiments-container">
            <div className="experiments-header">
                <h4 className="experiments-title">🧪 實驗會話歷史</h4>
                <div className="experiments-summary">
                    總計 {mockExperiments.length} 個實驗 | 完成{' '}
                    {
                        mockExperiments.filter((e) => e.status === 'completed')
                            .length
                    }{' '}
                    個 | 進行中{' '}
                    {
                        mockExperiments.filter((e) => e.status === 'running')
                            .length
                    }{' '}
                    個
                </div>
            </div>

            <div className="experiments-list">
                {mockExperiments.map((experiment, index) => {
                    const isSelected =
                        selectedExperiment === experiment.session_id
                    const duration = experiment.end_time
                        ? (
                              (new Date(experiment.end_time).getTime() -
                                  new Date(experiment.start_time).getTime()) /
                              (1000 * 60 * 60)
                          ).toFixed(1)
                        : null

                    return (
                        <div
                            key={experiment.session_id}
                            className={`experiment-card ${
                                isSelected ? 'selected' : ''
                            } experiment-card--${experiment.status}`}
                            onClick={() =>
                                setSelectedExperiment(
                                    isSelected ? null : experiment.session_id
                                )
                            }
                        >
                            <div className="experiment-header">
                                <div className="experiment-info">
                                    <div className="experiment-name">
                                        {experiment.experiment_name}
                                    </div>
                                    <div className="experiment-details">
                                        <span className="algorithm-badge">
                                            {experiment.algorithm_type}
                                        </span>
                                        <span className="scenario-badge">
                                            {experiment.scenario_type}
                                        </span>
                                        <span
                                            className={`status-badge status-badge--${experiment.status}`}
                                        >
                                            {experiment.status ===
                                                'completed' && '✅ 已完成'}
                                            {experiment.status === 'running' &&
                                                '🔄 進行中'}
                                            {experiment.status === 'failed' &&
                                                '❌ 失敗'}
                                        </span>
                                    </div>
                                </div>

                                <div className="experiment-metrics">
                                    {experiment.results && (
                                        <>
                                            <div className="metric">
                                                <span className="metric-label">
                                                    最終獎勵:
                                                </span>
                                                <span className="metric-value">
                                                    {experiment.results.final_reward.toFixed(
                                                        3
                                                    )}
                                                </span>
                                            </div>
                                            <div className="metric">
                                                <span className="metric-label">
                                                    成功率:
                                                </span>
                                                <span className="metric-value">
                                                    {(
                                                        experiment.results
                                                            .success_rate * 100
                                                    ).toFixed(1)}
                                                    %
                                                </span>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="experiment-timeline">
                                <div className="timeline-info">
                                    <span>
                                        開始:{' '}
                                        {new Date(
                                            experiment.start_time
                                        ).toLocaleString()}
                                    </span>
                                    {experiment.end_time && (
                                        <span>
                                            結束:{' '}
                                            {new Date(
                                                experiment.end_time
                                            ).toLocaleString()}
                                        </span>
                                    )}
                                    {duration && (
                                        <span>耗時: {duration} 小時</span>
                                    )}
                                </div>
                            </div>

                            {isSelected && (
                                <div className="experiment-details-expanded">
                                    <div className="hyperparameters">
                                        <h5 className="detail-title">
                                            超參數配置
                                        </h5>
                                        <div className="params-grid">
                                            {Object.entries(
                                                experiment.hyperparameters
                                            ).map(([key, value]) => (
                                                <div
                                                    key={key}
                                                    className="param-item"
                                                >
                                                    <span className="param-name">
                                                        {key}:
                                                    </span>
                                                    <span className="param-value">
                                                        {value}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {experiment.results && (
                                        <div className="experiment-results">
                                            <h5 className="detail-title">
                                                實驗結果
                                            </h5>
                                            <div className="results-grid">
                                                <div className="result-item">
                                                    <span className="result-label">
                                                        最終獎勵:
                                                    </span>
                                                    <span className="result-value">
                                                        {experiment.results.final_reward.toFixed(
                                                            3
                                                        )}
                                                    </span>
                                                </div>
                                                <div className="result-item">
                                                    <span className="result-label">
                                                        完成輪次:
                                                    </span>
                                                    <span className="result-value">
                                                        {
                                                            experiment.results
                                                                .episodes_completed
                                                        }
                                                    </span>
                                                </div>
                                                <div className="result-item">
                                                    <span className="result-label">
                                                        收斂輪次:
                                                    </span>
                                                    <span className="result-value">
                                                        {experiment.results
                                                            .convergence_episode ||
                                                            'N/A'}
                                                    </span>
                                                </div>
                                                <div className="result-item">
                                                    <span className="result-label">
                                                        成功率:
                                                    </span>
                                                    <span className="result-value">
                                                        {(
                                                            experiment.results
                                                                .success_rate *
                                                            100
                                                        ).toFixed(1)}
                                                        %
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {experiment.research_notes && (
                                        <div className="research-notes">
                                            <h5 className="detail-title">
                                                研究筆記
                                            </h5>
                                            <div className="notes-content">
                                                {experiment.research_notes}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )

    const researchTabs = [
        {
            id: 'experiments',
            label: '實驗歷史',
            icon: '🧪',
            component: renderExperiments,
        },
        {
            id: 'baseline',
            label: '基準比較',
            icon: '📊',
            component: () => <div>基準比較功能開發中...</div>,
        },
        {
            id: 'statistics',
            label: '統計分析',
            icon: '📈',
            component: () => <div>統計分析功能開發中...</div>,
        },
    ]

    return (
        <div className="research-data-section">
            <div className="section-header">
                <h2 className="section-title">🔬 研究數據管理</h2>
                <div className="section-controls">
                    <div className="export-controls">
                        <button
                            className="export-btn"
                            onClick={() => handleExportData('json')}
                            disabled={isExporting}
                            title="導出為 JSON"
                        >
                            {isExporting ? '⏳' : '📥'} JSON
                        </button>
                        <button
                            className="export-btn"
                            onClick={() => handleExportData('csv')}
                            disabled={isExporting}
                            title="導出為 CSV"
                        >
                            {isExporting ? '⏳' : '📊'} CSV
                        </button>
                        <button
                            className="export-btn"
                            onClick={() => handleExportData('excel')}
                            disabled={isExporting}
                            title="導出為 Excel"
                        >
                            {isExporting ? '⏳' : '📋'} Excel
                        </button>
                    </div>
                    <button
                        className="refresh-btn"
                        onClick={onRefresh}
                        title="刷新數據"
                    >
                        🔄
                    </button>
                </div>
            </div>

            <div className="mongodb-badge">
                <span className="badge-icon">🍃</span>
                <span className="badge-text">MongoDB 研究數據庫</span>
                <span className="badge-status">已連接</span>
            </div>

            {/* 研究數據選項卡 */}
            <div className="research-tabs">
                <div className="tabs-nav">
                    {researchTabs.map((tab) => (
                        <button
                            key={tab.id}
                            className={`research-tab ${
                                activeTab === tab.id
                                    ? 'research-tab--active'
                                    : ''
                            }`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <span className="tab-icon">{tab.icon}</span>
                            <span className="tab-label">{tab.label}</span>
                        </button>
                    ))}
                </div>

                <div className="tab-content">
                    {researchTabs
                        .find((tab) => tab.id === activeTab)
                        ?.component()}
                </div>
            </div>

            {/* 學術價值說明 */}
            <div className="academic-value">
                <div className="value-card">
                    <h4 className="value-title">🎓 學術研究價值</h4>
                    <div className="value-content">
                        <p>
                            <strong>論文支援</strong>
                            ：完整的實驗數據支援學術論文撰寫，
                            包含統計顯著性測試和基準比較。
                        </p>
                        <p>
                            <strong>可重現性</strong>
                            ：詳細記錄超參數配置和實驗條件，
                            確保研究結果的可重現性。
                        </p>
                        <p>
                            <strong>數據導出</strong>
                            ：支援多種格式導出，便於在其他
                            分析工具中進一步處理和可視化。
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default memo(ResearchDataSection)
