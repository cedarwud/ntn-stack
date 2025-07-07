/**
 * 獨立的 RL 監控模態框組件
 * 從 FullChartAnalysisDashboard 中提取出來，作為 navbar 的獨立功能
 */

import React from 'react'
import { Line } from 'react-chartjs-2'
import GymnasiumRLMonitor from '../dashboard/GymnasiumRLMonitor'
import { createInteractiveChartOptions } from '../../config/dashboardChartOptions'
import { useRLMonitoring } from '../views/dashboards/ChartAnalysisDashboard/hooks/useRLMonitoring'
import '../views/dashboards/ChartAnalysisDashboard/ChartAnalysisDashboard.scss'

interface RLMonitoringModalProps {
    isOpen: boolean
    onClose: () => void
}

const RLMonitoringModal: React.FC<RLMonitoringModalProps> = ({
    isOpen,
    onClose,
}) => {
    // RL監控相關狀態和邏輯 - 使用專用Hook
    const {
        isDqnTraining,
        isPpoTraining,
        isSacTraining,
        toggleDqnTraining,
        togglePpoTraining,
        toggleSacTraining,
        toggleAllTraining,
        trainingMetrics,
        rewardTrendData,
    } = useRLMonitoring()

    // 安全訪問 trainingMetrics
    const safeTrainingMetrics = {
        dqn: {
            episodes: trainingMetrics?.dqn?.episodes || 0,
            avgReward: trainingMetrics?.dqn?.avgReward || 0,
            progress: trainingMetrics?.dqn?.progress || 0,
        },
        ppo: {
            episodes: trainingMetrics?.ppo?.episodes || 0,
            avgReward: trainingMetrics?.ppo?.avgReward || 0,
            progress: trainingMetrics?.ppo?.progress || 0,
        },
        sac: {
            episodes: trainingMetrics?.sac?.episodes || 0,
            avgReward: trainingMetrics?.sac?.avgReward || 0,
            progress: trainingMetrics?.sac?.progress || 0,
        },
    }

    if (!isOpen) return null

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div 
                className="modal-content chart-analysis-modal rl-monitoring-standalone"
                onClick={(e) => e.stopPropagation()}
            >
                {/* 模態框標題欄 */}
                <div className="modal-header">
                    <div className="modal-title-section">
                        <h1 className="modal-title">
                            🧠 強化學習 (RL) 監控中心
                        </h1>
                        <p className="modal-subtitle">
                            實時監控 DQN、PPO、SAC 演算法訓練狀態與性能指標
                        </p>
                    </div>
                    <button 
                        className="modal-close-btn"
                        onClick={onClose}
                        aria-label="關閉 RL 監控"
                    >
                        ✕
                    </button>
                </div>

                {/* RL 監控內容 */}
                <div className="modal-body">
                    <div className="rl-monitoring-fullwidth">
                        <div className="rl-monitor-header">
                            {/* 大型控制按鈕 */}
                            <div className="rl-controls-section large-buttons">
                                <button
                                    className="large-control-btn dqn-btn"
                                    onClick={toggleDqnTraining}
                                >
                                    <div className="btn-icon">🤖</div>
                                    <div className="btn-content">
                                        <div className="btn-title">
                                            {isDqnTraining
                                                ? '停止 DQN'
                                                : '啟動 DQN'}
                                        </div>
                                        <div className="btn-subtitle">
                                            {isDqnTraining
                                                ? '🔴 訓練中'
                                                : '⚪ 待機'}
                                        </div>
                                    </div>
                                </button>

                                <button
                                    className="large-control-btn ppo-btn"
                                    onClick={togglePpoTraining}
                                >
                                    <div className="btn-icon">⚙️</div>
                                    <div className="btn-content">
                                        <div className="btn-title">
                                            {isPpoTraining
                                                ? '停止 PPO'
                                                : '啟動 PPO'}
                                        </div>
                                        <div className="btn-subtitle">
                                            {isPpoTraining
                                                ? '🔴 訓練中'
                                                : '⚪ 待機'}
                                        </div>
                                    </div>
                                </button>

                                <button
                                    className="large-control-btn sac-btn"
                                    onClick={toggleSacTraining}
                                >
                                    <div className="btn-icon">🎯</div>
                                    <div className="btn-content">
                                        <div className="btn-title">
                                            {isSacTraining
                                                ? '停止 SAC'
                                                : '啟動 SAC'}
                                        </div>
                                        <div className="btn-subtitle">
                                            {isSacTraining
                                                ? '🔴 訓練中'
                                                : '⚪ 待機'}
                                        </div>
                                    </div>
                                </button>

                                <button
                                    className="large-control-btn all-btn"
                                    onClick={toggleAllTraining}
                                >
                                    <div className="btn-icon">🚀</div>
                                    <div className="btn-content">
                                        <div className="btn-title">
                                            {isDqnTraining || isPpoTraining || isSacTraining
                                                ? '停止全部'
                                                : '同時啟動'}
                                        </div>
                                        <div className="btn-subtitle">
                                            {isDqnTraining || isPpoTraining || isSacTraining
                                                ? '🔴 全部停止'
                                                : '⚪ 一鍵啟動'}
                                        </div>
                                    </div>
                                </button>
                            </div>
                        </div>

                        {/* RL 監控面板 */}
                        <div className="rl-monitor-panels">
                            {/* DQN 監控面板 */}
                            <div className="rl-algorithm-panel dqn-panel">
                                <div className="panel-header">
                                    <div className="algorithm-info">
                                        <span className="algorithm-name">
                                            DQN Engine
                                        </span>
                                        <span
                                            className={`training-status ${
                                                isDqnTraining
                                                    ? 'active'
                                                    : 'idle'
                                            }`}
                                        >
                                            {isDqnTraining
                                                ? '🔴 訓練中'
                                                : '⚪ 待機'}
                                        </span>
                                    </div>
                                    <div className="training-progress">
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill dqn-fill"
                                                style={{
                                                    width: `${safeTrainingMetrics.dqn.progress}%`,
                                                }}
                                            ></div>
                                        </div>
                                        <span className="progress-text">
                                            {safeTrainingMetrics.dqn.progress.toFixed(
                                                1
                                            )}
                                            %
                                        </span>
                                    </div>
                                    <div className="training-metrics">
                                        <div className="metric">
                                            <span className="label">
                                                Episodes:
                                            </span>
                                            <span className="value">
                                                {safeTrainingMetrics.dqn.episodes}
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="label">
                                                Avg Reward:
                                            </span>
                                            <span className="value">
                                                {safeTrainingMetrics.dqn.avgReward.toFixed(
                                                    2
                                                )}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="charts-mini-grid">
                                        <div className="mini-chart">
                                            <div className="chart-title">
                                                獎勵趨勢
                                            </div>
                                            <div className="chart-area">
                                                {rewardTrendData.dqnData
                                                    .length > 0 ? (
                                                    <Line
                                                        data={{
                                                            labels: rewardTrendData.labels.slice(
                                                                0,
                                                                rewardTrendData
                                                                    .dqnData
                                                                    .length
                                                            ),
                                                            datasets: [
                                                                {
                                                                    label: 'DQN獎勵',
                                                                    data: rewardTrendData.dqnData,
                                                                    borderColor:
                                                                        '#22c55e',
                                                                    backgroundColor:
                                                                        'rgba(34, 197, 94, 0.1)',
                                                                    borderWidth: 2,
                                                                    fill: true,
                                                                    tension: 0.3,
                                                                    pointRadius: 0,
                                                                },
                                                            ],
                                                        }}
                                                        options={createInteractiveChartOptions(
                                                            'DQN 獎勵趨勢',
                                                            'Episode',
                                                            'Reward'
                                                        )}
                                                    />
                                                ) : (
                                                    <div className="no-data">
                                                        等待訓練數據...
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* PPO 監控面板 */}
                            <div className="rl-algorithm-panel ppo-panel">
                                <div className="panel-header">
                                    <div className="algorithm-info">
                                        <span className="algorithm-name">
                                            PPO Engine
                                        </span>
                                        <span
                                            className={`training-status ${
                                                isPpoTraining
                                                    ? 'active'
                                                    : 'idle'
                                            }`}
                                        >
                                            {isPpoTraining
                                                ? '🔴 訓練中'
                                                : '⚪ 待機'}
                                        </span>
                                    </div>
                                    <div className="training-progress">
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill ppo-fill"
                                                style={{
                                                    width: `${safeTrainingMetrics.ppo.progress}%`,
                                                }}
                                            ></div>
                                        </div>
                                        <span className="progress-text">
                                            {safeTrainingMetrics.ppo.progress.toFixed(
                                                1
                                            )}
                                            %
                                        </span>
                                    </div>
                                    <div className="training-metrics">
                                        <div className="metric">
                                            <span className="label">
                                                Episodes:
                                            </span>
                                            <span className="value">
                                                {
                                                    safeTrainingMetrics.ppo
                                                        .episodes
                                                }
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="label">
                                                Avg Reward:
                                            </span>
                                            <span className="value">
                                                {safeTrainingMetrics.ppo.avgReward.toFixed(
                                                    2
                                                )}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="charts-mini-grid">
                                        <div className="mini-chart">
                                            <div className="chart-title">
                                                獎勵趨勢
                                            </div>
                                            <div className="chart-area">
                                                {rewardTrendData.ppoData
                                                    .length > 0 ? (
                                                    <Line
                                                        data={{
                                                            labels: rewardTrendData.labels.slice(
                                                                0,
                                                                rewardTrendData
                                                                    .ppoData
                                                                    .length
                                                            ),
                                                            datasets: [
                                                                {
                                                                    label: 'PPO獎勵',
                                                                    data: rewardTrendData.ppoData,
                                                                    borderColor:
                                                                        '#3b82f6',
                                                                    backgroundColor:
                                                                        'rgba(59, 130, 246, 0.1)',
                                                                    borderWidth: 2,
                                                                    fill: true,
                                                                    tension: 0.3,
                                                                    pointRadius: 0,
                                                                },
                                                            ],
                                                        }}
                                                        options={createInteractiveChartOptions(
                                                            'PPO 獎勵趨勢',
                                                            'Episode',
                                                            'Reward'
                                                        )}
                                                    />
                                                ) : (
                                                    <div className="no-data">
                                                        等待訓練數據...
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* SAC 監控面板 */}
                            <div className="rl-algorithm-panel sac-panel">
                                <div className="panel-header">
                                    <div className="algorithm-info">
                                        <span className="algorithm-name">
                                            SAC Engine
                                        </span>
                                        <span
                                            className={`training-status ${
                                                isSacTraining
                                                    ? 'active'
                                                    : 'idle'
                                            }`}
                                        >
                                            {isSacTraining
                                                ? '🔴 訓練中'
                                                : '⚪ 待機'}
                                        </span>
                                    </div>
                                    <div className="training-progress">
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill sac-fill"
                                                style={{
                                                    width: `${safeTrainingMetrics.sac.progress}%`,
                                                }}
                                            ></div>
                                        </div>
                                        <span className="progress-text">
                                            {safeTrainingMetrics.sac.progress.toFixed(
                                                1
                                            )}
                                            %
                                        </span>
                                    </div>
                                    <div className="training-metrics">
                                        <div className="metric">
                                            <span className="label">
                                                Episodes:
                                            </span>
                                            <span className="value">
                                                {
                                                    safeTrainingMetrics.sac
                                                        .episodes
                                                }
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="label">
                                                Avg Reward:
                                            </span>
                                            <span className="value">
                                                {safeTrainingMetrics.sac.avgReward.toFixed(
                                                    2
                                                )}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="charts-mini-grid">
                                        <div className="mini-chart">
                                            <div className="chart-title">
                                                獎勵趨勢
                                            </div>
                                            <div className="chart-area">
                                                {rewardTrendData.sacData
                                                    .length > 0 ? (
                                                    <Line
                                                        data={{
                                                            labels: rewardTrendData.labels.slice(
                                                                0,
                                                                rewardTrendData
                                                                    .sacData
                                                                    .length
                                                            ),
                                                            datasets: [
                                                                {
                                                                    label: 'SAC獎勵',
                                                                    data: rewardTrendData.sacData,
                                                                    borderColor:
                                                                        '#f59e0b',
                                                                    backgroundColor:
                                                                        'rgba(245, 158, 11, 0.1)',
                                                                    borderWidth: 2,
                                                                    fill: true,
                                                                    tension: 0.3,
                                                                    pointRadius: 0,
                                                                },
                                                            ],
                                                        }}
                                                        options={createInteractiveChartOptions(
                                                            'SAC 獎勵趨勢',
                                                            'Episode',
                                                            'Reward'
                                                        )}
                                                    />
                                                ) : (
                                                    <div className="no-data">
                                                        等待訓練數據...
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 嵌入真實的 RL 監控組件 */}
                        <div className="rl-monitor-component">
                            <GymnasiumRLMonitor />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default RLMonitoringModal