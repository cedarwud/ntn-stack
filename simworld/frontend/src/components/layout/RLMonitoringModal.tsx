/**
 * 獨立的 RL 監控模態框組件
 * 從 FullChartAnalysisDashboard 中提取出來，作為 navbar 的獨立功能
 */

import React, { useState } from 'react'
import { Line } from 'react-chartjs-2'
import GymnasiumRLMonitor from '../dashboard/GymnasiumRLMonitor'
import { createRLChartOptions } from '../../config/dashboardChartOptions'
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
    // 使用 RL 監控 Hook
    const {
        isDqnTraining,
        isPpoTraining,
        isSacTraining,
        trainingMetrics,
        rewardTrendData,
        policyLossData,
        toggleDqnTraining,
        togglePpoTraining,
        toggleSacTraining
    } = useRLMonitoring(isOpen); // 只在模態框打開時啟用監控

    const [isChartView, setIsChartView] = useState(false);

    if (!isOpen) return null;

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div 
                className="constellation-modal rl-monitoring-standalone"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="modal-header">
                    <div className="modal-title-section">
                        <h1 className="modal-title">
                            🧠 強化學習 (RL) 監控中心
                        </h1>
                        <p className="modal-subtitle">
                            實時監控 DQN、PPO、SAC 演算法訓練狀態與性能指標
                        </p>
                    </div>
                    <div className="modal-controls">
                        <button 
                            className={`view-toggle-btn ${!isChartView ? 'active' : ''}`}
                            onClick={() => setIsChartView(false)}
                        >
                            📊 控制面板
                        </button>
                        <button 
                            className={`view-toggle-btn ${isChartView ? 'active' : ''}`}
                            onClick={() => setIsChartView(true)}
                        >
                            📈 圖表分析
                        </button>
                        <button 
                            className="modal-close-btn"
                            onClick={onClose}
                            aria-label="關閉 RL 監控"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                <div className="modal-body">
                    {!isChartView ? (
                        // 控制面板視圖
                        <GymnasiumRLMonitor />
                    ) : (
                        // 圖表分析視圖
                        <div className="chart-analysis-container">
                            <div className="charts-grid">
                                <div className="chart-container">
                                    <h3>獎勵趨勢</h3>
                                    <Line 
                                        data={{
                                            labels: rewardTrendData.labels,
                                            datasets: [
                                                {
                                                    label: 'DQN',
                                                    data: rewardTrendData.dqnData,
                                                    borderColor: 'rgb(75, 192, 192)',
                                                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                                },
                                                {
                                                    label: 'PPO',
                                                    data: rewardTrendData.ppoData,
                                                    borderColor: 'rgb(255, 99, 132)',
                                                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                                },
                                                {
                                                    label: 'SAC',
                                                    data: rewardTrendData.sacData,
                                                    borderColor: 'rgb(54, 162, 235)',
                                                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                                }
                                            ]
                                        }}
                                        options={createRLChartOptions('獎勵趨勢')}
                                    />
                                </div>
                                <div className="chart-container">
                                    <h3>策略損失</h3>
                                    <Line 
                                        data={{
                                            labels: policyLossData.labels,
                                            datasets: [
                                                {
                                                    label: 'DQN Loss',
                                                    data: policyLossData.dqnData,
                                                    borderColor: 'rgb(75, 192, 192)',
                                                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                                },
                                                {
                                                    label: 'PPO Loss',
                                                    data: policyLossData.ppoData,
                                                    borderColor: 'rgb(255, 99, 132)',
                                                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                                },
                                                {
                                                    label: 'SAC Loss',
                                                    data: policyLossData.sacData,
                                                    borderColor: 'rgb(54, 162, 235)',
                                                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                                }
                                            ]
                                        }}
                                        options={createRLChartOptions('策略損失')}
                                    />
                                </div>
                            </div>
                            
                            {/* 訓練指標概覽 */}
                            <div className="metrics-overview">
                                <h3>訓練指標概覽</h3>
                                <div className="metrics-grid">
                                    <div className="metric-card">
                                        <h4>DQN</h4>
                                        <div className="metric-value">
                                            Episode: {trainingMetrics.dqn.episodes}
                                        </div>
                                        <div className="metric-value">
                                            Reward: {trainingMetrics.dqn.avgReward.toFixed(2)}
                                        </div>
                                        <div className="metric-value">
                                            Progress: {trainingMetrics.dqn.progress.toFixed(1)}%
                                        </div>
                                        <button 
                                            className={`training-btn ${isDqnTraining ? 'stop' : 'start'}`}
                                            onClick={toggleDqnTraining}
                                        >
                                            {isDqnTraining ? '停止訓練' : '開始訓練'}
                                        </button>
                                    </div>
                                    
                                    <div className="metric-card">
                                        <h4>PPO</h4>
                                        <div className="metric-value">
                                            Episode: {trainingMetrics.ppo.episodes}
                                        </div>
                                        <div className="metric-value">
                                            Reward: {trainingMetrics.ppo.avgReward.toFixed(2)}
                                        </div>
                                        <div className="metric-value">
                                            Progress: {trainingMetrics.ppo.progress.toFixed(1)}%
                                        </div>
                                        <button 
                                            className={`training-btn ${isPpoTraining ? 'stop' : 'start'}`}
                                            onClick={togglePpoTraining}
                                        >
                                            {isPpoTraining ? '停止訓練' : '開始訓練'}
                                        </button>
                                    </div>
                                    
                                    <div className="metric-card">
                                        <h4>SAC</h4>
                                        <div className="metric-value">
                                            Episode: {trainingMetrics.sac.episodes}
                                        </div>
                                        <div className="metric-value">
                                            Reward: {trainingMetrics.sac.avgReward.toFixed(2)}
                                        </div>
                                        <div className="metric-value">
                                            Progress: {trainingMetrics.sac.progress.toFixed(1)}%
                                        </div>
                                        <button 
                                            className={`training-btn ${isSacTraining ? 'stop' : 'start'}`}
                                            onClick={toggleSacTraining}
                                        >
                                            {isSacTraining ? '停止訓練' : '開始訓練'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default RLMonitoringModal;
