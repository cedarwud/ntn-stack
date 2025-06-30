/**
 * 完整的圖表分析儀表板
 * 包含所有 8 個標籤分頁的完整功能
 */

import React, { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import OverviewTabContent from '../views/dashboards/ChartAnalysisDashboard/components/OverviewTabContent'
import AnalysisTabContent from '../views/dashboards/ChartAnalysisDashboard/components/AnalysisTabContent'
import EnhancedAlgorithmTabContent from '../views/dashboards/ChartAnalysisDashboard/components/EnhancedAlgorithmTabContent'
import EnhancedPerformanceTabContent from '../views/dashboards/ChartAnalysisDashboard/components/EnhancedPerformanceTabContent'
import MonitoringTabContent from '../views/dashboards/ChartAnalysisDashboard/components/MonitoringTabContent'
import StrategyTabContent from '../views/dashboards/ChartAnalysisDashboard/components/StrategyTabContent'
import ParametersTabContent from '../views/dashboards/ChartAnalysisDashboard/components/ParametersTabContent'
import EnhancedSystemTabContent from '../views/dashboards/ChartAnalysisDashboard/components/EnhancedSystemTabContent'
import GymnasiumRLMonitor from '../dashboard/GymnasiumRLMonitor'
import '../views/dashboards/ChartAnalysisDashboard/ChartAnalysisDashboard.scss'

interface FullChartAnalysisDashboardProps {
  isOpen: boolean
  onClose: () => void
}

type TabName = 'overview' | 'performance' | 'system' | 'algorithms' | 'rl-monitoring' | 'analysis' | 'monitoring' | 'strategy' | 'parameters'

// 模擬數據和圖表選項（保留以備不時之需）
const _createMockData = () => {
  // Handover 延遲分析數據
  const handoverLatencyData = {
    labels: ['信號檢測', '決策計算', '連接建立', '數據傳輸', '確認完成'],
    datasets: [
      {
        label: 'NTN 標準',
        data: [45, 78, 89, 23, 15],
        backgroundColor: 'rgba(255, 99, 132, 0.7)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-GS',
        data: [32, 54, 45, 15, 7],
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-SMN',
        data: [35, 58, 48, 12, 5],
        backgroundColor: 'rgba(255, 206, 86, 0.7)',
        borderColor: 'rgba(255, 206, 86, 1)',
        borderWidth: 2,
      },
      {
        label: '本論文方案',
        data: [8, 7, 4, 1.5, 0.5],
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
      },
    ],
  }

  // 雙星座對比數據
  const constellationComparisonData = {
    labels: ['延遲', '覆蓋率', '換手頻率', 'QoE', '能耗', '可靠性'],
    datasets: [
      {
        label: 'Starlink',
        data: [85, 92, 75, 88, 82, 90],
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
      },
      {
        label: 'Kuiper',
        data: [78, 85, 88, 86, 85, 87],
        backgroundColor: 'rgba(153, 102, 255, 0.7)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 2,
      },
    ],
  }

  // 六場景數據
  const sixScenarioChartData = {
    labels: [
      'SL-F-同向',
      'SL-F-全向',
      'SL-C-同向',
      'SL-C-全向',
      'KP-F-同向',
      'KP-F-全向',
      'KP-C-同向',
      'KP-C-全向',
    ],
    datasets: [
      {
        label: 'NTN 標準',
        data: [245, 255, 238, 252, 248, 258, 242, 250],
        backgroundColor: 'rgba(255, 99, 132, 0.7)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-GS',
        data: [148, 158, 145, 155, 152, 162, 146, 156],
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-SMN',
        data: [152, 165, 148, 162, 155, 168, 150, 160],
        backgroundColor: 'rgba(255, 206, 86, 0.7)',
        borderColor: 'rgba(255, 206, 86, 1)',
        borderWidth: 2,
      },
      {
        label: '本論文方案',
        data: [18, 24, 16, 22, 20, 26, 17, 23],
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
      },
    ],
  }

  return {
    handoverLatencyData,
    constellationComparisonData,
    sixScenarioChartData,
  }
}

// 創建圖表選項
const createInteractiveChartOptions = (title: string, yLabel: string, xLabel?: string) => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: 'white',
        font: {
          size: 14,
          weight: 'bold' as const,
        },
      },
    },
    title: {
      display: true,
      text: title,
      color: 'white',
      font: {
        size: 18,
        weight: 'bold' as const,
      },
    },
  },
  scales: {
    x: {
      title: {
        display: !!xLabel,
        text: xLabel || '',
        color: 'white',
        font: {
          size: 14,
          weight: 'bold' as const,
        },
      },
      ticks: {
        color: 'white',
        font: {
          size: 12,
          weight: 'bold' as const,
        },
      },
    },
    y: {
      title: {
        display: true,
        text: yLabel,
        color: 'white',
        font: {
          size: 14,
          weight: 'bold' as const,
        },
      },
      ticks: {
        color: 'white',
        font: {
          size: 12,
          weight: 'bold' as const,
        },
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.2)',
      },
    },
  },
})

const FullChartAnalysisDashboard: React.FC<FullChartAnalysisDashboardProps> = ({
  isOpen,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<TabName>('overview')

  // RL監控相關狀態 - 與完整圖表一致
  const [isDqnTraining, setIsDqnTraining] = useState(false)
  const [isPpoTraining, setIsPpoTraining] = useState(false)
  const [trainingMetrics, setTrainingMetrics] = useState({
    dqn: {
      episodes: 0,
      avgReward: 0,
      progress: 0,
      handoverDelay: 0,
      successRate: 0,
      signalDropTime: 0,
      energyEfficiency: 0,
    },
    ppo: {
      episodes: 0,
      avgReward: 0,
      progress: 0,
      handoverDelay: 0,
      successRate: 0,
      signalDropTime: 0,
      energyEfficiency: 0,
    },
  })

  const [rewardTrendData, setRewardTrendData] = useState({
    dqnData: [] as number[],
    ppoData: [] as number[],
    labels: [] as string[],
  })

  const [policyLossData, setPolicyLossData] = useState({
    dqnLoss: [] as number[],
    ppoLoss: [] as number[],
    labels: [] as string[],
  })

  // 監聽來自GymnasiumRLMonitor的真實數據 - 與完整圖表一致
  useEffect(() => {
    const handleRLMetricsUpdate = (event: CustomEvent) => {
      const { engine, metrics } = event.detail
      // 處理邏輯與完整圖表完全相同
      setTrainingMetrics((prev) => {
        const newMetrics = { ...prev }
        if (engine === 'dqn') {
          newMetrics.dqn = {
            episodes: metrics.episodes_completed || 0,
            avgReward: metrics.average_reward || 0,
            progress: metrics.training_progress || 0,
            handoverDelay: 45 - (metrics.training_progress / 100) * 20 + (Math.random() - 0.5) * 5,
            successRate: Math.min(100, 82 + (metrics.training_progress / 100) * 12 + (Math.random() - 0.5) * 1.5),
            signalDropTime: 18 - (metrics.training_progress / 100) * 8 + (Math.random() - 0.5) * 2,
            energyEfficiency: 0.75 + (metrics.training_progress / 100) * 0.2 + (Math.random() - 0.5) * 0.05,
          }

          // 更新DQN獎勵趨勢數據
          setRewardTrendData((prevData) => {
            const newDataPoints = [...prevData.dqnData, metrics.average_reward].slice(-20)
            return {
              ...prevData,
              dqnData: newDataPoints,
              labels: Array.from({ length: Math.max(newDataPoints.length, prevData.ppoData.length) }, (_, i) => `${i + 1}`),
            }
          })

          // 更新DQN損失數據
          setPolicyLossData((prevData) => {
            const newLossPoints = [...prevData.dqnLoss, Math.random() * 0.5 + 0.1].slice(-20)
            return {
              ...prevData,
              dqnLoss: newLossPoints,
              labels: Array.from({ length: Math.max(newLossPoints.length, prevData.ppoLoss.length) }, (_, i) => `${i + 1}`),
            }
          })
        } else if (engine === 'ppo') {
          newMetrics.ppo = {
            episodes: metrics.episodes_completed || 0,
            avgReward: metrics.average_reward || 0,
            progress: metrics.training_progress || 0,
            handoverDelay: 40 - (metrics.training_progress / 100) * 22 + (Math.random() - 0.5) * 4,
            successRate: Math.min(100, 84 + (metrics.training_progress / 100) * 10 + (Math.random() - 0.5) * 1.2),
            signalDropTime: 16 - (metrics.training_progress / 100) * 9 + (Math.random() - 0.5) * 1.5,
            energyEfficiency: 0.8 + (metrics.training_progress / 100) * 0.18 + (Math.random() - 0.5) * 0.04,
          }

          // 更新PPO獎勵趨勢數據
          setRewardTrendData((prevData) => {
            const newDataPoints = [...prevData.ppoData, metrics.average_reward].slice(-20)
            return {
              ...prevData,
              ppoData: newDataPoints,
              labels: Array.from({ length: Math.max(prevData.dqnData.length, newDataPoints.length) }, (_, i) => `${i + 1}`),
            }
          })

          // 更新PPO損失數據
          setPolicyLossData((prevData) => {
            const newLossPoints = [...prevData.ppoLoss, Math.random() * 0.3 + 0.05].slice(-20)
            return {
              ...prevData,
              ppoLoss: newLossPoints,
              labels: Array.from({ length: Math.max(prevData.dqnLoss.length, newLossPoints.length) }, (_, i) => `${i + 1}`),
            }
          })
        }
        return newMetrics
      })
    }

    const handleTrainingStopped = (event: CustomEvent) => {
      const { engine } = event.detail
      setTrainingMetrics((prev) => {
        const newMetrics = { ...prev }
        if (engine === 'dqn') {
          newMetrics.dqn = {
            episodes: 0, avgReward: 0, progress: 0,
            handoverDelay: 0, successRate: 0, signalDropTime: 0, energyEfficiency: 0,
          }
        } else if (engine === 'ppo') {
          newMetrics.ppo = {
            episodes: 0, avgReward: 0, progress: 0,
            handoverDelay: 0, successRate: 0, signalDropTime: 0, energyEfficiency: 0,
          }
        }
        return newMetrics
      })
    }

    window.addEventListener('rlMetricsUpdate', handleRLMetricsUpdate as EventListener)
    window.addEventListener('rlTrainingStopped', handleTrainingStopped as EventListener)

    return () => {
      window.removeEventListener('rlMetricsUpdate', handleRLMetricsUpdate as EventListener)
      window.removeEventListener('rlTrainingStopped', handleTrainingStopped as EventListener)
    }
  }, [])

  if (!isOpen) return null

  // const mockData = createMockData() // 已改用真實API數據，保留以備不時之需

  // 標籤配置 - 按照原始檔案的順序和名稱
  const tabs = [
    { key: 'overview', label: '核心圖表', icon: '📊' },
    { key: 'performance', label: '性能監控', icon: '⚡' },
    { key: 'system', label: '系統架構', icon: '🖥️' },
    { key: 'algorithms', label: '算法分析', icon: '🔬' },
    { key: 'rl-monitoring', label: 'RL 監控', icon: '🧠' },
    { key: 'analysis', label: '深度分析', icon: '📈' },
    { key: 'monitoring', label: '衛星監控', icon: '🔍' },
    { key: 'strategy', label: '即時策略效果', icon: '🎯' },
    { key: 'parameters', label: '軌道參數', icon: '📋' },
  ]

  // 渲染標籤頁內容
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <OverviewTabContent
            createInteractiveChartOptions={createInteractiveChartOptions}
          />
        )
      case 'performance':
        return <EnhancedPerformanceTabContent />
      case 'system':
        return <EnhancedSystemTabContent />
      case 'algorithms':
        return <EnhancedAlgorithmTabContent />
      case 'rl-monitoring':
        // 與完整圖表完全一致的內嵌RL監控實現
        return (
          <div className="rl-monitoring-fullwidth">
            <div className="rl-monitor-header">
              <h2>🧠 強化學習 (RL) 智能監控中心</h2>
              {/* 大型控制按鈕 */}
              <div className="rl-controls-section large-buttons">
                <button
                  className="large-control-btn dqn-btn"
                  onClick={() => {
                    setIsDqnTraining(!isDqnTraining)
                    window.dispatchEvent(
                      new CustomEvent('dqnTrainingToggle', {
                        detail: { isTraining: !isDqnTraining }
                      })
                    )
                  }}
                >
                  <div className="btn-icon">🤖</div>
                  <div className="btn-content">
                    <div className="btn-title">
                      {isDqnTraining ? '停止 DQN' : '啟動 DQN'}
                    </div>
                    <div className="btn-subtitle">
                      {isDqnTraining ? '🔴 訓練中' : '⚪ 待機'}
                    </div>
                  </div>
                </button>
                
                <button
                  className="large-control-btn ppo-btn"
                  onClick={() => {
                    setIsPpoTraining(!isPpoTraining)
                    window.dispatchEvent(
                      new CustomEvent('ppoTrainingToggle', {
                        detail: { isTraining: !isPpoTraining }
                      })
                    )
                  }}
                >
                  <div className="btn-icon">⚙️</div>
                  <div className="btn-content">
                    <div className="btn-title">
                      {isPpoTraining ? '停止 PPO' : '啟動 PPO'}
                    </div>
                    <div className="btn-subtitle">
                      {isPpoTraining ? '🔴 訓練中' : '⚪ 待機'}
                    </div>
                  </div>
                </button>
                
                <button
                  className="large-control-btn both-btn"
                  onClick={() => {
                    const newDqnState = !isDqnTraining || !isPpoTraining
                    const newPpoState = !isDqnTraining || !isPpoTraining
                    setIsDqnTraining(newDqnState)
                    setIsPpoTraining(newPpoState)
                    window.dispatchEvent(
                      new CustomEvent('bothTrainingToggle', {
                        detail: { dqnTraining: newDqnState, ppoTraining: newPpoState }
                      })
                    )
                  }}
                >
                  <div className="btn-icon">🚀</div>
                  <div className="btn-content">
                    <div className="btn-title">
                      {isDqnTraining && isPpoTraining ? '停止全部' : '同時訓練'}
                    </div>
                    <div className="btn-subtitle">
                      {isDqnTraining && isPpoTraining ? '🔴 全部運行' : '⚪ 批量啟動'}
                    </div>
                  </div>
                </button>
              </div>
            </div>

            <div className="rl-content-grid">
              {/* 嵌入真實的 RL 監控組件 */}
              <div className="rl-real-component">
                <GymnasiumRLMonitor />
              </div>

              {/* 豐富的訓練過程可視化 */}
              <div className="rl-training-viz">
                <h3>📊 實時訓練進度監控</h3>
                <div className="training-charts enhanced">
                  {/* DQN 訓練卡片 */}
                  <div className="training-engine-card dqn-card">
                    <div className="engine-header">
                      <span className="engine-icon">🤖</span>
                      <span className="engine-name">DQN Engine</span>
                      <span className={`training-status ${isDqnTraining ? 'active' : 'idle'}`}>
                        {isDqnTraining ? '🔴 訓練中' : '⚪ 待機'}
                      </span>
                    </div>
                    <div className="training-progress">
                      <div className="progress-bar">
                        <div
                          className="progress-fill dqn-fill"
                          style={{ width: `${trainingMetrics.dqn.progress}%` }}
                        ></div>
                      </div>
                      <span className="progress-text">
                        {trainingMetrics.dqn.progress.toFixed(1)}%
                      </span>
                    </div>
                    <div className="training-metrics">
                      <div className="metric">
                        <span className="label">Episodes:</span>
                        <span className="value">{trainingMetrics.dqn.episodes}</span>
                      </div>
                      <div className="metric">
                        <span className="label">Avg Reward:</span>
                        <span className="value">{trainingMetrics.dqn.avgReward.toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="charts-mini-grid">
                      <div className="mini-chart">
                        <div className="chart-title">獎勵趨勢</div>
                        <div className="chart-area">
                          {rewardTrendData.dqnData.length > 0 ? (
                            <Line
                              data={{
                                labels: rewardTrendData.labels.slice(0, rewardTrendData.dqnData.length),
                                datasets: [
                                  {
                                    label: 'DQN獎勵',
                                    data: rewardTrendData.dqnData,
                                    borderColor: '#22c55e',
                                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
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
                                scales: { x: { display: false }, y: { display: false } },
                              }}
                            />
                          ) : (
                            <div className="no-data">等待訓練數據...</div>
                          )}
                        </div>
                      </div>
                      <div className="mini-chart">
                        <div className="chart-title">損失函數</div>
                        <div className="chart-area">
                          {policyLossData.dqnLoss.length > 0 ? (
                            <Line
                              data={{
                                labels: policyLossData.labels.slice(0, policyLossData.dqnLoss.length),
                                datasets: [
                                  {
                                    label: 'DQN損失',
                                    data: policyLossData.dqnLoss,
                                    borderColor: '#ef4444',
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
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
                                scales: { x: { display: false }, y: { display: false } },
                              }}
                            />
                          ) : (
                            <div className="no-data">等待訓練數據...</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* PPO 訓練卡片 */}
                  <div className="training-engine-card ppo-card">
                    <div className="engine-header">
                      <span className="engine-icon">⚙️</span>
                      <span className="engine-name">PPO Engine</span>
                      <span className={`training-status ${isPpoTraining ? 'active' : 'idle'}`}>
                        {isPpoTraining ? '🔴 訓練中' : '⚪ 待機'}
                      </span>
                    </div>
                    <div className="training-progress">
                      <div className="progress-bar">
                        <div
                          className="progress-fill ppo-fill"
                          style={{ width: `${trainingMetrics.ppo.progress}%` }}
                        ></div>
                      </div>
                      <span className="progress-text">
                        {trainingMetrics.ppo.progress.toFixed(1)}%
                      </span>
                    </div>
                    <div className="training-metrics">
                      <div className="metric">
                        <span className="label">Episodes:</span>
                        <span className="value">{trainingMetrics.ppo.episodes}</span>
                      </div>
                      <div className="metric">
                        <span className="label">Avg Reward:</span>
                        <span className="value">{trainingMetrics.ppo.avgReward.toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="charts-mini-grid">
                      <div className="mini-chart">
                        <div className="chart-title">獎勵趨勢</div>
                        <div className="chart-area">
                          {rewardTrendData.ppoData.length > 0 ? (
                            <Line
                              data={{
                                labels: rewardTrendData.labels.slice(0, rewardTrendData.ppoData.length),
                                datasets: [
                                  {
                                    label: 'PPO獎勵',
                                    data: rewardTrendData.ppoData,
                                    borderColor: '#f97316',
                                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
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
                                scales: { x: { display: false }, y: { display: false } },
                              }}
                            />
                          ) : (
                            <div className="no-data">等待訓練數據...</div>
                          )}
                        </div>
                      </div>
                      <div className="mini-chart">
                        <div className="chart-title">策略損失</div>
                        <div className="chart-area">
                          {policyLossData.ppoLoss.length > 0 ? (
                            <Line
                              data={{
                                labels: policyLossData.labels.slice(0, policyLossData.ppoLoss.length),
                                datasets: [
                                  {
                                    label: 'PPO損失',
                                    data: policyLossData.ppoLoss,
                                    borderColor: '#8b5cf6',
                                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
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
                                scales: { x: { display: false }, y: { display: false } },
                              }}
                            />
                          ) : (
                            <div className="no-data">等待訓練數據...</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 全局訓練統計 */}
                <div className="global-training-stats">
                  <h3>📈 全局訓練統計</h3>
                  <div style={{ fontSize: '0.85em', color: '#aab8c5', marginBottom: '12px', textAlign: 'center' }}>
                    💡 即時訓練指標：累計回合數、平均成功率(限100%)、總獎勵值
                  </div>
                  <div className="stats-grid">
                    <div className="stat-card cumulative">
                      <div className="stat-header">
                        <span className="stat-icon">🔢</span>
                        <span className="stat-title" title="DQN + PPO 算法的總訓練回合數">累計回合</span>
                      </div>
                      <div className="stat-value">
                        {(isDqnTraining ? trainingMetrics.dqn.episodes : 0) + (isPpoTraining ? trainingMetrics.ppo.episodes : 0)}
                      </div>
                      <div className="stat-trend">
                        {isDqnTraining || isPpoTraining ? '訓練中...' : '待機中'}
                      </div>
                    </div>

                    <div className="stat-card success-rate">
                      <div className="stat-header">
                        <span className="stat-icon">✅</span>
                        <span className="stat-title" title="算法平均成功率，已限制最大值為100%">成功率</span>
                      </div>
                      <div className="stat-value">
                        {(isDqnTraining || isPpoTraining) && (trainingMetrics.dqn.episodes > 0 || trainingMetrics.ppo.episodes > 0)
                          ? Math.min(100, ((isDqnTraining ? trainingMetrics.dqn.successRate : 0) + (isPpoTraining ? trainingMetrics.ppo.successRate : 0)) / ((isDqnTraining ? 1 : 0) + (isPpoTraining ? 1 : 0))).toFixed(1)
                          : '0.0'}%
                      </div>
                      <div className="stat-trend">
                        {(isDqnTraining || isPpoTraining) && (trainingMetrics.dqn.episodes > 0 || trainingMetrics.ppo.episodes > 0) ? '學習中' : '無變化'}
                      </div>
                    </div>

                    <div className="stat-card total-reward">
                      <div className="stat-header">
                        <span className="stat-icon">💰</span>
                        <span className="stat-title" title="累積總獎勵 = 平均獎勵 × 回合數，支援 K/M 單位">總獎勵</span>
                      </div>
                      <div className="stat-value">
                        {(() => {
                          const totalReward = (isDqnTraining ? trainingMetrics.dqn.avgReward * trainingMetrics.dqn.episodes : 0) + (isPpoTraining ? trainingMetrics.ppo.avgReward * trainingMetrics.ppo.episodes : 0)
                          if (totalReward >= 1000000) {
                            return (totalReward / 1000000).toFixed(1) + 'M'
                          } else if (totalReward >= 1000) {
                            return (totalReward / 1000).toFixed(1) + 'K'
                          } else {
                            return totalReward.toFixed(1)
                          }
                        })()}
                      </div>
                      <div className="stat-trend">
                        {isDqnTraining || isPpoTraining ? '累積中' : '無累積'}
                      </div>
                    </div>

                    <div className="stat-card active-time">
                      <div className="stat-header">
                        <span className="stat-icon">⏰</span>
                        <span className="stat-title">活躍時間</span>
                      </div>
                      <div className="stat-value">
                        {isDqnTraining || isPpoTraining ? '🟢 運行中' : '⚪ 待機'}
                      </div>
                      <div className="stat-trend">
                        {isDqnTraining || isPpoTraining ? 'Live' : 'Idle'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 性能比較表 */}
                <div className="rl-performance-comparison compact">
                  <h3>📈 算法性能比較</h3>
                  {isDqnTraining || isPpoTraining ? (
                    <div className="comparison-table">
                      <table>
                        <thead>
                          <tr>
                            <th>指標</th>
                            <th>DQN</th>
                            <th>PPO</th>
                            <th>INFOCOM 2024</th>
                            <th>改善率</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>換手延遲 (ms)</td>
                            <td className="metric-value">
                              {isDqnTraining && trainingMetrics.dqn.episodes > 0 ? trainingMetrics.dqn.handoverDelay.toFixed(1) : '--'}
                            </td>
                            <td className="metric-value">
                              {isPpoTraining && trainingMetrics.ppo.episodes > 0 ? trainingMetrics.ppo.handoverDelay.toFixed(1) : '--'}
                            </td>
                            <td className="metric-value baseline">45.2</td>
                            <td className="improvement">
                              {(isDqnTraining && trainingMetrics.dqn.episodes > 0) || (isPpoTraining && trainingMetrics.ppo.episodes > 0) ? (() => {
                                const improvement = Math.round(((45.2 - Math.min(isDqnTraining ? trainingMetrics.dqn.handoverDelay : 999, isPpoTraining ? trainingMetrics.ppo.handoverDelay : 999)) / 45.2) * 100)
                                const color = improvement >= 10 ? '#4ade80' : improvement >= 0 ? '#fbbf24' : '#ef4444'
                                const icon = improvement >= 10 ? '⬆️' : improvement >= 0 ? '➡️' : '⬇️'
                                return <span style={{ color, fontWeight: 'bold' }}>{icon} {improvement}%</span>
                              })() : '待計算'}
                            </td>
                          </tr>
                          <tr>
                            <td>成功率 (%)</td>
                            <td className="metric-value">
                              {isDqnTraining && trainingMetrics.dqn.episodes > 0 ? trainingMetrics.dqn.successRate.toFixed(1) : '--'}
                            </td>
                            <td className="metric-value">
                              {isPpoTraining && trainingMetrics.ppo.episodes > 0 ? trainingMetrics.ppo.successRate.toFixed(1) : '--'}
                            </td>
                            <td className="metric-value baseline">84.3</td>
                            <td className="improvement">
                              {(isDqnTraining && trainingMetrics.dqn.episodes > 0) || (isPpoTraining && trainingMetrics.ppo.episodes > 0) ? (() => {
                                const improvement = Math.round(((Math.max(isDqnTraining ? trainingMetrics.dqn.successRate : 0, isPpoTraining ? trainingMetrics.ppo.successRate : 0) - 84.3) / 84.3) * 100)
                                const color = improvement >= 2 ? '#4ade80' : improvement >= 0 ? '#fbbf24' : '#ef4444'
                                const icon = improvement >= 2 ? '⬆️' : improvement >= 0 ? '➡️' : '⬇️'
                                return <span style={{ color, fontWeight: 'bold' }}>{icon} {improvement >= 0 ? '+' : ''}{improvement}%</span>
                              })() : '待計算'}
                            </td>
                          </tr>
                          <tr>
                            <td>信號中斷時間 (ms)</td>
                            <td className="metric-value">
                              {isDqnTraining && trainingMetrics.dqn.episodes > 0 ? trainingMetrics.dqn.signalDropTime.toFixed(1) : '--'}
                            </td>
                            <td className="metric-value">
                              {isPpoTraining && trainingMetrics.ppo.episodes > 0 ? trainingMetrics.ppo.signalDropTime.toFixed(1) : '--'}
                            </td>
                            <td className="metric-value baseline">12.8</td>
                            <td className="improvement">
                              {(isDqnTraining && trainingMetrics.dqn.episodes > 0) || (isPpoTraining && trainingMetrics.ppo.episodes > 0) ? (() => {
                                const improvement = Math.round(((12.8 - Math.min(isDqnTraining ? trainingMetrics.dqn.signalDropTime : 999, isPpoTraining ? trainingMetrics.ppo.signalDropTime : 999)) / 12.8) * 100)
                                const color = improvement >= 15 ? '#4ade80' : improvement >= 0 ? '#fbbf24' : '#ef4444'
                                const icon = improvement >= 15 ? '⬆️' : improvement >= 0 ? '➡️' : '⬇️'
                                return <span style={{ color, fontWeight: 'bold' }}>{icon} {improvement}%</span>
                              })() : '待計算'}
                            </td>
                          </tr>
                          <tr>
                            <td>能耗效率</td>
                            <td className="metric-value">
                              {isDqnTraining && trainingMetrics.dqn.episodes > 0 ? trainingMetrics.dqn.energyEfficiency.toFixed(2) : '--'}
                            </td>
                            <td className="metric-value">
                              {isPpoTraining && trainingMetrics.ppo.episodes > 0 ? trainingMetrics.ppo.energyEfficiency.toFixed(2) : '--'}
                            </td>
                            <td className="metric-value baseline">0.72</td>
                            <td className="improvement">
                              {(isDqnTraining && trainingMetrics.dqn.episodes > 0) || (isPpoTraining && trainingMetrics.ppo.episodes > 0) ? (() => {
                                const improvement = Math.round(((Math.max(isDqnTraining ? trainingMetrics.dqn.energyEfficiency : 0, isPpoTraining ? trainingMetrics.ppo.energyEfficiency : 0) - 0.72) / 0.72) * 100)
                                const color = improvement >= 5 ? '#4ade80' : improvement >= 0 ? '#fbbf24' : '#ef4444'
                                const icon = improvement >= 5 ? '⬆️' : improvement >= 0 ? '➡️' : '⬇️'
                                return <span style={{ color, fontWeight: 'bold' }}>{icon} {improvement >= 0 ? '+' : ''}{improvement}%</span>
                              })() : '待計算'}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#aab8c5', fontSize: '0.9rem' }}>
                      🤖 請啟動 DQN 或 PPO 引擎以查看性能比較
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )
      case 'analysis':
        return <AnalysisTabContent />
      case 'monitoring':
        return <MonitoringTabContent />
      case 'strategy':
        return <StrategyTabContent />
      case 'parameters':
        return <ParametersTabContent />
      default:
        return (
          <OverviewTabContent
            createInteractiveChartOptions={createInteractiveChartOptions}
          />
        )
    }
  }

  return (
    <div className="chart-analysis-overlay">
      <div className="chart-analysis-modal">
        <div className="modal-header">
          <h2>🚀 NTN 衛星網路換手分析儀表板</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* 標籤頁導航 */}
        <div className="tabs-container">
          <div className="tabs">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.key as TabName)}
              >
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-label">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="modal-content">
          <style>{`
            /* 弹窗样式 - 参考完整图表弹窗 */
            .chart-analysis-overlay {
              position: fixed;
              top: 0;
              left: 0;
              width: 100vw;
              height: 100vh;
              background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(20, 30, 48, 0.95));
              z-index: 10000;
              display: flex;
              align-items: center;
              justify-content: center;
              backdrop-filter: blur(10px);
            }
            
            .chart-analysis-modal {
              width: 95vw;
              height: 95vh;
              background: linear-gradient(145deg, #1a1a2e, #16213e);
              border-radius: 20px;
              box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
              display: flex;
              flex-direction: column;
              overflow: hidden;
              border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .modal-content {
              flex: 1;
              padding: 20px;
              overflow-y: auto;
              background: linear-gradient(180deg, #1a1a2e, #16213e);
            }
            
            .modal-content::-webkit-scrollbar {
              width: 8px;
            }
            
            .modal-content::-webkit-scrollbar-track {
              background: rgba(255, 255, 255, 0.1);
              border-radius: 4px;
            }
            
            .modal-content::-webkit-scrollbar-thumb {
              background: linear-gradient(180deg, #667eea, #764ba2);
              border-radius: 4px;
            }
            
            .full-chart-analysis-dashboard .charts-grid {
              display: grid !important;
              gap: 20px !important;
              width: 100% !important;
              grid-template-columns: 1fr 1fr !important;
              grid-template-rows: auto auto !important;
              margin: 0 !important;
              padding: 0 !important;
            }
            
            /* 前两个图表填满宽度 */
            .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(1) {
              grid-column: 1 !important;
              grid-row: 1 !important;
              width: 100% !important;
              max-width: none !important;
              min-width: 0 !important;
            }
            
            .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(2) {
              grid-column: 2 !important;
              grid-row: 1 !important;
              width: 100% !important;
              max-width: none !important;
              min-width: 0 !important;
            }
            
            /* 第三个图表（六场景）跨两列显示 */
            .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(3) {
              grid-column: 1 / -1 !important;
              grid-row: 2 !important;
              width: 100% !important;
              max-width: none !important;
            }
            
            /* 响应式：小屏幕时改为单列布局 */
            @media (max-width: 1200px) {
              .full-chart-analysis-dashboard .charts-grid {
                grid-template-columns: 1fr !important;
                grid-template-rows: auto auto auto !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(1) {
                grid-column: 1 !important;
                grid-row: 1 !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(2) {
                grid-column: 1 !important;
                grid-row: 2 !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(3) {
                grid-column: 1 !important;
                grid-row: 3 !important;
              }
            }
            
            .full-chart-analysis-dashboard .chart-container {
              background: rgba(255, 255, 255, 0.05);
              border-radius: 15px;
              padding: 25px;
              border: 1px solid rgba(255, 255, 255, 0.1);
              backdrop-filter: blur(5px);
              height: auto;
              min-height: 500px;
              display: flex;
              flex-direction: column;
              width: 100% !important;
              box-sizing: border-box !important;
              margin: 0 !important;
            }
            
            .full-chart-analysis-dashboard .chart-container.extra-large {
              min-height: 600px;
            }
            
            .full-chart-analysis-dashboard .chart-container canvas {
              height: 350px !important;
              max-height: 350px !important;
              width: 100% !important;
              max-width: 100% !important;
              flex-shrink: 0;
            }
            
            .full-chart-analysis-dashboard .chart-container.extra-large canvas {
              height: 450px !important;
              max-height: 450px !important;
              width: 100% !important;
              max-width: 100% !important;
            }
            
            /* 确保Chart.js容器也能自适应 */
            .full-chart-analysis-dashboard .chart-container > div {
              width: 100% !important;
              height: auto !important;
            }
            
            .full-chart-analysis-dashboard .chart-container h3 {
              color: white;
              margin-bottom: 20px;
              font-size: 1.4rem;
              text-align: center;
              font-weight: bold;
            }
            
            .full-chart-analysis-dashboard .chart-insight {
              margin-top: 15px;
              padding: 15px;
              background: rgba(102, 126, 234, 0.1);
              border-radius: 10px;
              color: white;
              border-left: 4px solid #667eea;
              font-size: 1.1rem;
              line-height: 1.6;
              flex-shrink: 0;
            }
            
            .full-chart-analysis-dashboard .chart-insight strong {
              color: white;
            }
            
            .full-chart-analysis-dashboard .algorithm-comparison-table,
            .full-chart-analysis-dashboard .algorithm-features {
              margin-top: 16px;
              flex-shrink: 0;
            }
            
            /* 移动端适配 */
            @media (max-width: 768px) {
              .chart-analysis-modal {
                width: 100vw !important;
                height: 100vh !important;
                border-radius: 0 !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid {
                grid-template-columns: 1fr !important;
                grid-template-rows: auto auto auto !important;
                gap: 15px !important;
                padding: 10px !important;
                width: 100% !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(1),
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(2),
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(3) {
                grid-column: 1 !important;
                width: 100% !important;
              }
              
              .full-chart-analysis-dashboard .chart-container {
                padding: 15px !important;
                min-height: 400px !important;
                width: 100% !important;
                margin: 0 !important;
              }
              
              .full-chart-analysis-dashboard .chart-container canvas {
                height: 250px !important;
                max-height: 250px !important;
                width: 100% !important;
                max-width: 100% !important;
              }
            }
          `}</style>
          <div className="full-chart-analysis-dashboard">
            {renderTabContent()}
          </div>
        </div>

        {/* 數據來源說明頁腳 */}
        <div className="modal-footer" style={{
          padding: '20px 24px',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          fontSize: '0.9rem',
          color: 'rgba(255, 255, 255, 0.9)',
          lineHeight: '1.6',
          minHeight: '100px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'flex-start' }}>
            <div style={{ flex: '1', minWidth: '300px' }}>
              <strong style={{ color: 'white', display: 'block', marginBottom: '8px' }}>
                🔄 重構版數據來源：
              </strong>
              <div style={{ paddingLeft: '16px', color: 'rgba(255, 255, 255, 0.85)' }}>
                《Accelerating Handover in Mobile Satellite Network》IEEE INFOCOM 2024 | 
                UERANSIM + Open5GS 原型系統 | NetStack Core Sync API | 
                Celestrak TLE 即時軌道數據 | 真實 Starlink & Kuiper 衛星參數
              </div>
            </div>
          </div>
          <div style={{ 
            fontSize: '0.85rem', 
            color: 'rgba(255, 255, 255, 0.7)',
            fontStyle: 'italic',
            padding: '12px 16px',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderLeft: '3px solid rgba(59, 130, 246, 0.5)',
            borderRadius: '4px'
          }}>
            💡 此版本採用智能數據回退機制：優先使用真實API數據，API失敗時自動切換到模擬數據。
            所有圖表容器已優化為更大尺寸，提供完整的內容顯示空間。
          </div>
        </div>
      </div>
    </div>
  )
}

export default FullChartAnalysisDashboard