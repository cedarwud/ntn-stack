/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from 'react'
import { Line } from 'react-chartjs-2'
import GymnasiumRLMonitor from '../../../../dashboard/GymnasiumRLMonitor'

interface RLMonitoringTabProps {
    isDqnTraining: boolean
    isPpoTraining: boolean
    trainingMetrics: any
    rewardTrendData: any
    policyLossData: any
    infocomMetrics: any
    onDqnToggle: () => void
    onPpoToggle: () => void
}

const RLMonitoringTab: React.FC<RLMonitoringTabProps> = ({
    isDqnTraining,
    isPpoTraining,
    trainingMetrics,
    rewardTrendData,
    policyLossData,
    infocomMetrics,
    onDqnToggle,
    onPpoToggle,
}) => {
    return (
        <div className="rl-monitoring-fullwidth">
            <div className="rl-monitor-header">
                <h2>🧠 強化學習 (RL) 智能監控中心</h2>

                {/* 大型控制按鈕 */}
                <div className="rl-controls-section large-buttons">
                    <button
                        className="large-control-btn dqn-btn"
                        onClick={onDqnToggle}
                        style={{
                            backgroundColor: isDqnTraining
                                ? '#ef4444'
                                : '#6b7280',
                            border: isDqnTraining
                                ? '2px solid #dc2626'
                                : '2px solid #4b5563',
                            boxShadow: isDqnTraining
                                ? '0 0 20px rgba(239, 68, 68, 0.5)'
                                : 'none',
                        }}
                    >
                        <span className="btn-icon">🎯</span>
                        <span className="btn-text">
                            DQN 訓練
                            {isDqnTraining ? ' (運行中)' : ' (待機)'}
                        </span>
                        <span className="btn-status">
                            {isDqnTraining ? '🔴' : '⚪'}
                        </span>
                    </button>

                    <button
                        className="large-control-btn ppo-btn"
                        onClick={onPpoToggle}
                        style={{
                            backgroundColor: isPpoTraining
                                ? '#f97316'
                                : '#6b7280',
                            border: isPpoTraining
                                ? '2px solid #ea580c'
                                : '2px solid #4b5563',
                            boxShadow: isPpoTraining
                                ? '0 0 20px rgba(249, 115, 22, 0.5)'
                                : 'none',
                        }}
                    >
                        <span className="btn-icon">🚀</span>
                        <span className="btn-text">
                            PPO 訓練
                            {isPpoTraining ? ' (運行中)' : ' (待機)'}
                        </span>
                        <span className="btn-status">
                            {isPpoTraining ? '🔴' : '⚪'}
                        </span>
                    </button>
                </div>

                <p className="rl-description">
                    🎮 使用 Gymnasium 環境進行 NTN 換手優化訓練。DQN
                    專注於離散動作空間的快速決策， PPO
                    則在連續策略空間中尋找最優解。兩個算法並行運作，實現更全面的學習策略。
                </p>
            </div>

            {/* 演算法監控區域 */}
            <div className="rl-algorithms-grid">
                {/* DQN 監控卡片 */}
                <div className="algorithm-monitor-card dqn-card">
                    <div className="card-header">
                        <h3>🎯 DQN (Deep Q-Network)</h3>
                        <span className="training-status">
                            {isDqnTraining ? '🔴 訓練中' : '⚪ 待機'}
                        </span>
                    </div>

                    <div className="training-progress">
                        <div className="progress-bar">
                            <div
                                className="progress-fill dqn-fill"
                                style={{
                                    width: `${trainingMetrics.dqn.progress}%`,
                                }}
                            ></div>
                        </div>
                        <span className="progress-text">
                            {trainingMetrics.dqn.progress.toFixed(1)}%
                        </span>
                    </div>

                    <div className="training-metrics">
                        <div className="metric">
                            <span className="label">Episodes:</span>
                            <span className="value">
                                {trainingMetrics.dqn.episodes}
                            </span>
                        </div>
                        <div className="metric">
                            <span className="label">平均獎勵:</span>
                            <span className="value">
                                {trainingMetrics.dqn.avgReward.toFixed(2)}
                            </span>
                        </div>
                        <div className="metric">
                            <span className="label">換手延遲:</span>
                            <span className="value">
                                {trainingMetrics.dqn.handoverDelay.toFixed(1)}ms
                            </span>
                        </div>
                        <div className="metric">
                            <span className="label">成功率:</span>
                            <span className="value">
                                {trainingMetrics.dqn.successRate.toFixed(1)}%
                            </span>
                        </div>
                    </div>

                    {/* DQN 即時圖表 */}
                    <div className="realtime-charts">
                        <div className="mini-chart reward-chart">
                            <h4>獎勵趨勢</h4>
                            <Line
                                data={{
                                    labels: rewardTrendData.labels.slice(
                                        0,
                                        rewardTrendData.dqnData.length
                                    ),
                                    datasets: [
                                        {
                                            label: 'DQN獎勵',
                                            data: rewardTrendData.dqnData,
                                            borderColor: '#ef4444',
                                            backgroundColor:
                                                'rgba(239, 68, 68, 0.1)',
                                            borderWidth: 2,
                                            fill: true,
                                            tension: 0.4,
                                        },
                                    ],
                                }}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: { legend: { display: false } },
                                    scales: {
                                        x: { display: false },
                                        y: { display: false },
                                    },
                                }}
                            />
                        </div>

                        <div className="mini-chart loss-chart">
                            <h4>損失函數</h4>
                            <Line
                                data={{
                                    labels: policyLossData.labels.slice(
                                        0,
                                        policyLossData.dqnLoss.length
                                    ),
                                    datasets: [
                                        {
                                            label: 'DQN損失',
                                            data: policyLossData.dqnLoss,
                                            borderColor: '#ef4444',
                                            backgroundColor:
                                                'rgba(239, 68, 68, 0.1)',
                                            borderWidth: 2,
                                            fill: true,
                                        },
                                    ],
                                }}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: { legend: { display: false } },
                                    scales: {
                                        x: { display: false },
                                        y: { display: false },
                                    },
                                }}
                            />
                        </div>
                    </div>
                </div>

                {/* PPO 監控卡片 */}
                <div className="algorithm-monitor-card ppo-card">
                    <div className="card-header">
                        <h3>🚀 PPO (Proximal Policy Optimization)</h3>
                        <span className="training-status">
                            {isPpoTraining ? '🔴 訓練中' : '⚪ 待機'}
                        </span>
                    </div>

                    <div className="training-progress">
                        <div className="progress-bar">
                            <div
                                className="progress-fill ppo-fill"
                                style={{
                                    width: `${trainingMetrics.ppo.progress}%`,
                                }}
                            ></div>
                        </div>
                        <span className="progress-text">
                            {trainingMetrics.ppo.progress.toFixed(1)}%
                        </span>
                    </div>

                    <div className="training-metrics">
                        <div className="metric">
                            <span className="label">Episodes:</span>
                            <span className="value">
                                {trainingMetrics.ppo.episodes}
                            </span>
                        </div>
                        <div className="metric">
                            <span className="label">平均獎勵:</span>
                            <span className="value">
                                {trainingMetrics.ppo.avgReward.toFixed(2)}
                            </span>
                        </div>
                        <div className="metric">
                            <span className="label">換手延遲:</span>
                            <span className="value">
                                {trainingMetrics.ppo.handoverDelay.toFixed(1)}ms
                            </span>
                        </div>
                        <div className="metric">
                            <span className="label">成功率:</span>
                            <span className="value">
                                {trainingMetrics.ppo.successRate.toFixed(1)}%
                            </span>
                        </div>
                    </div>

                    {/* PPO 即時圖表 */}
                    <div className="realtime-charts">
                        <div className="mini-chart reward-chart">
                            <h4>獎勵趨勢</h4>
                            <Line
                                data={{
                                    labels: rewardTrendData.labels.slice(
                                        0,
                                        rewardTrendData.ppoData.length
                                    ),
                                    datasets: [
                                        {
                                            label: 'PPO獎勵',
                                            data: rewardTrendData.ppoData,
                                            borderColor: '#f97316',
                                            backgroundColor:
                                                'rgba(249, 115, 22, 0.1)',
                                            borderWidth: 2,
                                            fill: true,
                                            tension: 0.4,
                                        },
                                    ],
                                }}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: { legend: { display: false } },
                                    scales: {
                                        x: { display: false },
                                        y: { display: false },
                                    },
                                }}
                            />
                        </div>

                        <div className="mini-chart loss-chart">
                            <h4>損失函數</h4>
                            <Line
                                data={{
                                    labels: policyLossData.labels.slice(
                                        0,
                                        policyLossData.ppoLoss.length
                                    ),
                                    datasets: [
                                        {
                                            label: 'PPO損失',
                                            data: policyLossData.ppoLoss,
                                            borderColor: '#8b5cf6',
                                            backgroundColor:
                                                'rgba(139, 92, 246, 0.1)',
                                            borderWidth: 2,
                                            fill: true,
                                        },
                                    ],
                                }}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: { legend: { display: false } },
                                    scales: {
                                        x: { display: false },
                                        y: { display: false },
                                    },
                                }}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* 集成GymnasiumRLMonitor組件 */}
            <div className="gymnasium-integration">
                <GymnasiumRLMonitor />
            </div>
        </div>
    )
}

export default RLMonitoringTab
