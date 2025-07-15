import React, { memo } from 'react'
import './AlgorithmComparisonSection.scss'

interface AlgorithmComparisonSectionProps {
    data?: {
        comparison: {
            algorithms: Array<{
                algorithm: string
                status: string
                progress: number
                current_episode: number
                total_episodes: number
                average_reward: number
                training_active: boolean
                metrics: any
            }>
            performance_metrics: {
                reward_comparison: Record<string, number>
                convergence_analysis: Record<string, number[]>
                statistical_significance: Record<string, boolean>
            }
        }
        performance: {
            latency: number
            success_rate: number
            throughput: number
            error_rate: number
            response_time: number
            resource_utilization: {
                cpu: number
                memory: number
            }
        }
        ranking: Array<{
            algorithm: string
            rank: number
            score: number
            metrics: {
                reward: number
                convergence_speed: number
                stability: number
                efficiency: number
            }
        }>
    }
    onRefresh?: () => void
}

const AlgorithmComparisonSection: React.FC<AlgorithmComparisonSectionProps> = ({
    data,
    onRefresh,
}) => {
    const algorithms = data?.comparison?.algorithms || []
    const rankings = data?.ranking || []
    const performance = data?.performance

    // 計算最佳算法
    const bestAlgorithm = rankings.length > 0 ? rankings[0] : null

    // 獲取算法顏色
    const getAlgorithmColor = (algorithm: string) => {
        const colors = {
            dqn: '#3b82f6', // 藍色
            ppo: '#10b981', // 綠色
            sac: '#f59e0b', // 橙色
        }
        return (
            colors[algorithm.toLowerCase() as keyof typeof colors] || '#6b7280'
        )
    }

    // 獲取性能等級
    const getPerformanceLevel = (score: number) => {
        if (score >= 0.8)
            return { level: 'excellent', emoji: '🟢', text: '優秀' }
        if (score >= 0.6) return { level: 'good', emoji: '🟡', text: '良好' }
        if (score >= 0.4) return { level: 'average', emoji: '🟠', text: '一般' }
        return { level: 'poor', emoji: '🔴', text: '待改進' }
    }

    return (
        <div className="algorithm-comparison-section">
            <div className="section-header">
                <h2 className="section-title">🧠 算法性能對比</h2>
                <button
                    className="refresh-btn"
                    onClick={onRefresh}
                    title="刷新數據"
                >
                    🔄
                </button>
            </div>

            {/* 總體性能概覽 */}
            {performance && (
                <div className="performance-overview">
                    <div className="overview-card">
                        <h3 className="overview-title">系統性能概覽</h3>
                        <div className="metrics-grid">
                            <div className="metric-item">
                                <div className="metric-icon">⚡</div>
                                <div className="metric-info">
                                    <div className="metric-label">響應時間</div>
                                    <div className="metric-value">
                                        {performance.response_time.toFixed(2)}ms
                                    </div>
                                </div>
                            </div>
                            <div className="metric-item">
                                <div className="metric-icon">✅</div>
                                <div className="metric-info">
                                    <div className="metric-label">成功率</div>
                                    <div className="metric-value">
                                        {(
                                            performance.success_rate * 100
                                        ).toFixed(1)}
                                        %
                                    </div>
                                </div>
                            </div>
                            <div className="metric-item">
                                <div className="metric-icon">📊</div>
                                <div className="metric-info">
                                    <div className="metric-label">吞吐量</div>
                                    <div className="metric-value">
                                        {performance.throughput.toFixed(0)}{' '}
                                        req/s
                                    </div>
                                </div>
                            </div>
                            <div className="metric-item">
                                <div className="metric-icon">❌</div>
                                <div className="metric-info">
                                    <div className="metric-label">錯誤率</div>
                                    <div className="metric-value">
                                        {(performance.error_rate * 100).toFixed(
                                            2
                                        )}
                                        %
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 算法排名 */}
            {rankings.length > 0 && (
                <div className="algorithm-ranking">
                    <h3 className="subsection-title">🏆 算法排名</h3>
                    <div className="ranking-grid">
                        {rankings.map((ranking, index) => {
                            const performanceLevel = getPerformanceLevel(
                                ranking.score
                            )
                            const isWinner = index === 0

                            return (
                                <div
                                    key={ranking.algorithm}
                                    className={`ranking-card ${
                                        isWinner ? 'ranking-card--winner' : ''
                                    }`}
                                >
                                    <div className="ranking-header">
                                        <div className="rank-badge">
                                            {index === 0 && '🥇'}
                                            {index === 1 && '🥈'}
                                            {index === 2 && '🥉'}
                                            {index > 2 && `#${ranking.rank}`}
                                        </div>
                                        <div className="algorithm-info">
                                            <div className="algorithm-name-rank">
                                                {ranking.algorithm.toUpperCase()}
                                            </div>
                                            <div className="performance-indicator">
                                                {performanceLevel.emoji}{' '}
                                                {performanceLevel.text}
                                            </div>
                                        </div>
                                        <div className="score-display">
                                            <div className="score-value">
                                                {ranking.score.toFixed(3)}
                                            </div>
                                            <div className="score-label">
                                                總分
                                            </div>
                                        </div>
                                    </div>

                                    <div className="metrics-breakdown">
                                        <div className="metric-bar">
                                            <span className="metric-name">
                                                獎勵
                                            </span>
                                            <div className="bar-container">
                                                <div
                                                    className="bar-fill"
                                                    style={{
                                                        width: `${
                                                            (ranking.metrics
                                                                .reward || 0) *
                                                            100
                                                        }%`,
                                                        backgroundColor:
                                                            getAlgorithmColor(
                                                                ranking.algorithm
                                                            ),
                                                    }}
                                                ></div>
                                            </div>
                                            <span className="metric-value-small">
                                                {(
                                                    ranking.metrics.reward || 0
                                                ).toFixed(2)}
                                            </span>
                                        </div>

                                        <div className="metric-bar">
                                            <span className="metric-name">
                                                收斂速度
                                            </span>
                                            <div className="bar-container">
                                                <div
                                                    className="bar-fill"
                                                    style={{
                                                        width: `${
                                                            (ranking.metrics
                                                                .convergence_speed ||
                                                                0) * 100
                                                        }%`,
                                                        backgroundColor:
                                                            getAlgorithmColor(
                                                                ranking.algorithm
                                                            ),
                                                    }}
                                                ></div>
                                            </div>
                                            <span className="metric-value-small">
                                                {(
                                                    ranking.metrics
                                                        .convergence_speed || 0
                                                ).toFixed(2)}
                                            </span>
                                        </div>

                                        <div className="metric-bar">
                                            <span className="metric-name">
                                                穩定性
                                            </span>
                                            <div className="bar-container">
                                                <div
                                                    className="bar-fill"
                                                    style={{
                                                        width: `${
                                                            (ranking.metrics
                                                                .stability ||
                                                                0) * 100
                                                        }%`,
                                                        backgroundColor:
                                                            getAlgorithmColor(
                                                                ranking.algorithm
                                                            ),
                                                    }}
                                                ></div>
                                            </div>
                                            <span className="metric-value-small">
                                                {(
                                                    ranking.metrics.stability ||
                                                    0
                                                ).toFixed(2)}
                                            </span>
                                        </div>

                                        <div className="metric-bar">
                                            <span className="metric-name">
                                                效率
                                            </span>
                                            <div className="bar-container">
                                                <div
                                                    className="bar-fill"
                                                    style={{
                                                        width: `${
                                                            (ranking.metrics
                                                                .efficiency ||
                                                                0) * 100
                                                        }%`,
                                                        backgroundColor:
                                                            getAlgorithmColor(
                                                                ranking.algorithm
                                                            ),
                                                    }}
                                                ></div>
                                            </div>
                                            <span className="metric-value-small">
                                                {(
                                                    ranking.metrics
                                                        .efficiency || 0
                                                ).toFixed(2)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* 詳細比較表格 */}
            {algorithms.length > 0 && (
                <div className="algorithm-comparison-table">
                    <h3 className="subsection-title">📊 詳細對比分析</h3>
                    <div className="comparison-table">
                        <div className="table-header">
                            <div className="col col-algorithm">算法</div>
                            <div className="col col-status">狀態</div>
                            <div className="col col-progress">進度</div>
                            <div className="col col-episodes">訓練輪次</div>
                            <div className="col col-reward">平均獎勵</div>
                            <div className="col col-active">訓練狀態</div>
                        </div>

                        {algorithms.map((algo, index) => (
                            <div key={index} className="table-row">
                                <div className="col col-algorithm">
                                    <div className="algorithm-cell">
                                        <div
                                            className="algorithm-color-indicator"
                                            style={{
                                                backgroundColor:
                                                    getAlgorithmColor(
                                                        algo.algorithm
                                                    ),
                                            }}
                                        ></div>
                                        <span className="algorithm-name-table">
                                            {algo.algorithm.toUpperCase()}
                                        </span>
                                    </div>
                                </div>
                                <div className="col col-status">
                                    <span
                                        className={`status-badge status-badge--${algo.status}`}
                                    >
                                        {algo.status === 'running' && '🔄'}
                                        {algo.status === 'completed' && '✅'}
                                        {algo.status === 'idle' && '⏸️'}
                                        {algo.status === 'error' && '❌'}
                                        {algo.status}
                                    </span>
                                </div>
                                <div className="col col-progress">
                                    <div className="progress-cell">
                                        <div className="progress-bar-small">
                                            <div
                                                className="progress-fill-small"
                                                style={{
                                                    width: `${
                                                        (algo.progress || 0) *
                                                        100
                                                    }%`,
                                                    backgroundColor:
                                                        getAlgorithmColor(
                                                            algo.algorithm
                                                        ),
                                                }}
                                            ></div>
                                        </div>
                                        <span className="progress-text-small">
                                            {(
                                                (algo.progress || 0) * 100
                                            ).toFixed(1)}
                                            %
                                        </span>
                                    </div>
                                </div>
                                <div className="col col-episodes">
                                    <span className="episodes-info">
                                        {algo.current_episode} /{' '}
                                        {algo.total_episodes}
                                    </span>
                                </div>
                                <div className="col col-reward">
                                    <span className="reward-value">
                                        {(algo.average_reward || 0).toFixed(3)}
                                    </span>
                                </div>
                                <div className="col col-active">
                                    <div
                                        className={`training-indicator ${
                                            algo.training_active
                                                ? 'active'
                                                : 'inactive'
                                        }`}
                                    >
                                        <div className="indicator-dot"></div>
                                        <span className="indicator-text">
                                            {algo.training_active
                                                ? '訓練中'
                                                : '閒置'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* 當前最佳推薦 */}
            {bestAlgorithm && (
                <div className="best-algorithm-recommendation">
                    <div className="recommendation-card">
                        <h3 className="recommendation-title">
                            🎯 當前最佳算法推薦
                        </h3>
                        <div className="recommendation-content">
                            <div className="winner-info">
                                <div className="winner-badge">
                                    🏆 {bestAlgorithm.algorithm.toUpperCase()}
                                </div>
                                <div className="winner-score">
                                    綜合得分: {bestAlgorithm.score.toFixed(3)}
                                </div>
                            </div>
                            <div className="recommendation-text">
                                基於當前性能指標，
                                <strong>
                                    {bestAlgorithm.algorithm.toUpperCase()}
                                </strong>{' '}
                                算法表現最佳，
                                建議在生產環境中優先使用此算法進行衛星切換決策。
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 無數據提示 */}
            {algorithms.length === 0 && rankings.length === 0 && (
                <div className="no-data-message">
                    <div className="no-data-icon">📊</div>
                    <div className="no-data-text">算法比較數據載入中...</div>
                    <div className="no-data-subtext">
                        請啟動算法訓練以查看性能對比數據
                    </div>
                </div>
            )}
        </div>
    )
}

export default memo(AlgorithmComparisonSection)
