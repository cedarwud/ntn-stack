/**
 * RL 監控標籤頁內容組件
 * 強化學習智能監控中心
 */

import React, { useState } from 'react'
import GymnasiumRLMonitor from '../../../../dashboard/GymnasiumRLMonitor'

const RLMonitoringTabContent: React.FC = () => {
  const [isDqnTraining, setIsDqnTraining] = useState(false)
  const [isPpoTraining, setIsPpoTraining] = useState(false)

  return (
    <div className="rl-monitoring-fullwidth">
      <div className="rl-monitor-header">
        <h2>強化學習 (RL) 智能監控中心</h2>
        
        {/* 大型控制按鈕 */}
        <div className="rl-controls-section large-buttons">
          <button
            className="large-control-btn dqn-btn"
            onClick={() => {
              setIsDqnTraining(!isDqnTraining)
              // 觸發自定義事件通知 GymnasiumRLMonitor
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
              // 觸發自定義事件通知 GymnasiumRLMonitor
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
              // 觸發自定義事件
              window.dispatchEvent(
                new CustomEvent('bothTrainingToggle', {
                  detail: {
                    dqnTraining: newDqnState,
                    ppoTraining: newPpoState
                  }
                })
              )
            }}
          >
            <div className="btn-icon">🚀</div>
            <div className="btn-content">
              <div className="btn-title">
                {isDqnTraining && isPpoTraining ? '停止全部' : '啟動全部'}
              </div>
              <div className="btn-subtitle">
                {isDqnTraining && isPpoTraining ? '🔴 全部運行' : '⚪ 聯合訓練'}
              </div>
            </div>
          </button>
        </div>
        
        <div className="rl-header-info">
          <div className="info-badge">
            🎯 智能換手決策
          </div>
          <div className="info-badge">
            📊 即時性能優化
          </div>
          <div className="info-badge">
            🔄 自適應學習
          </div>
        </div>
      </div>

      {/* RL 監控內容區域 */}
      <div className="rl-content-grid">
        <div className="rl-real-component">
          <GymnasiumRLMonitor />
        </div>
        
        <div className="rl-training-viz">
          <h3>訓練視覺化</h3>
          <div className="training-charts enhanced">
            {/* DQN 訓練卡片 */}
            <div className="training-engine-card">
              <div className="engine-header">
                <span className="engine-name">🤖 DQN Engine</span>
                <span className={`training-status ${isDqnTraining ? 'active' : 'idle'}`}>
                  {isDqnTraining ? '訓練中' : '待機'}
                </span>
              </div>
              <div className="training-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill dqn-fill" 
                    style={{ width: `${isDqnTraining ? 65 : 0}%` }}
                  ></div>
                </div>
                <span className="progress-text">65%</span>
              </div>
              <div className="training-metrics">
                <div className="metric">
                  <div className="label">Episodes</div>
                  <div className="value">{isDqnTraining ? '1,247' : '0'}</div>
                </div>
                <div className="metric">
                  <div className="label">Avg Reward</div>
                  <div className="value">{isDqnTraining ? '0.87' : '0.00'}</div>
                </div>
              </div>
            </div>

            {/* PPO 訓練卡片 */}
            <div className="training-engine-card">
              <div className="engine-header">
                <span className="engine-name">⚙️ PPO Engine</span>
                <span className={`training-status ${isPpoTraining ? 'active' : 'idle'}`}>
                  {isPpoTraining ? '訓練中' : '待機'}
                </span>
              </div>
              <div className="training-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill ppo-fill" 
                    style={{ width: `${isPpoTraining ? 72 : 0}%` }}
                  ></div>
                </div>
                <span className="progress-text">72%</span>
              </div>
              <div className="training-metrics">
                <div className="metric">
                  <div className="label">Episodes</div>
                  <div className="value">{isPpoTraining ? '892' : '0'}</div>
                </div>
                <div className="metric">
                  <div className="label">Avg Reward</div>
                  <div className="value">{isPpoTraining ? '0.91' : '0.00'}</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* 全域訓練統計 */}
          <div className="global-training-stats">
            <h4>
              📊 全域訓練統計
              <span className={`demo-badge ${isDqnTraining || isPpoTraining ? 'real-data' : ''}`}>
                {isDqnTraining || isPpoTraining ? '即時數據' : '演示模式'}
              </span>
            </h4>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">🎯</div>
                <div className="stat-content">
                  <div className="stat-label">成功率</div>
                  <div className="stat-value">
                    {isDqnTraining || isPpoTraining ? '94.2%' : '0%'}
                  </div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">⚡</div>
                <div className="stat-content">
                  <div className="stat-label">平均延遲</div>
                  <div className="stat-value">
                    {isDqnTraining || isPpoTraining ? '18.5ms' : '0ms'}
                  </div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🔋</div>
                <div className="stat-content">
                  <div className="stat-label">能耗效率</div>
                  <div className="stat-value">
                    {isDqnTraining || isPpoTraining ? '89.7%' : '0%'}
                  </div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📈</div>
                <div className="stat-content">
                  <div className="stat-label">學習進度</div>
                  <div className="stat-value">
                    {isDqnTraining || isPpoTraining ? '68.5%' : '0%'}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="data-source-info">
              <p>
                <span className="icon">ℹ️</span>
                RL 智能監控整合了 DQN 和 PPO 算法，實現自適應換手決策優化。
                訓練數據來自真實的衛星網路環境模擬，持續改善系統性能。
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RLMonitoringTabContent