/**
 * 自適應學習系統可視化組件
 * 
 * 階段八：進階 AI 智慧決策與自動化調優
 * 提供機器學習模型的自適應學習、在線訓練和持續優化功能
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
import { Line, Bar, Radar, Doughnut } from 'react-chartjs-2'
import './AdaptiveLearningSystemViewer.scss'

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

interface LearningModel {
  model_id: string
  model_name: string
  model_type: 'neural_network' | 'random_forest' | 'svm' | 'lstm' | 'transformer'
  domain: 'interference_prediction' | 'handover_optimization' | 'resource_allocation' | 'fault_detection'
  current_accuracy: number
  baseline_accuracy: number
  learning_rate: number
  adaptation_speed: 'fast' | 'medium' | 'slow'
  training_status: 'idle' | 'training' | 'evaluating' | 'updating'
  last_adaptation_time: string
  training_iterations: number
  convergence_status: 'converging' | 'converged' | 'diverging'
  performance_trend: {
    timestamp: string
    accuracy: number
    loss: number
    validation_score: number
  }[]
}

interface DataDrift {
  feature_name: string
  drift_score: number
  drift_status: 'stable' | 'moderate_drift' | 'significant_drift'
  historical_values: number[]
  current_distribution: number[]
  reference_distribution: number[]
  mitigation_strategy: string
}

interface OnlineLearningMetrics {
  total_data_points_processed: number
  learning_sessions_today: number
  average_adaptation_time: number
  model_improvements: number
  accuracy_gain_today: number
  concept_drift_events: number
  automated_retraining_count: number
  human_intervention_required: number
}

interface AdaptationEvent {
  event_id: string
  timestamp: string
  model_name: string
  event_type: 'concept_drift_detected' | 'performance_degradation' | 'new_data_pattern' | 'scheduled_update'
  trigger_reason: string
  adaptation_action: 'retrain_model' | 'update_parameters' | 'feature_engineering' | 'architecture_change'
  before_performance: number
  after_performance: number
  adaptation_time: number
  success: boolean
}

interface AdaptiveLearningSystemViewerProps {
  devices: any[]
  enabled: boolean
}

const AdaptiveLearningSystemViewer: React.FC<AdaptiveLearningSystemViewerProps> = ({
  devices,
  enabled
}) => {
  const [learningModels, setLearningModels] = useState<LearningModel[]>([])
  const [dataDrifts, setDataDrifts] = useState<DataDrift[]>([])
  const [onlineLearningMetrics, setOnlineLearningMetrics] = useState<OnlineLearningMetrics | null>(null)
  const [adaptationEvents, setAdaptationEvents] = useState<AdaptationEvent[]>([])
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [autoMode, setAutoMode] = useState(true)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  // 模擬生成學習模型數據
  const generateLearningModels = useCallback((): LearningModel[] => {
    const modelTypes: LearningModel['model_type'][] = ['neural_network', 'random_forest', 'svm', 'lstm', 'transformer']
    const domains: LearningModel['domain'][] = ['interference_prediction', 'handover_optimization', 'resource_allocation', 'fault_detection']
    const adaptationSpeeds: LearningModel['adaptation_speed'][] = ['fast', 'medium', 'slow']
    const trainingStatuses: LearningModel['training_status'][] = ['idle', 'training', 'evaluating', 'updating']
    const convergenceStatuses: LearningModel['convergence_status'][] = ['converging', 'converged', 'diverging']

    return Array.from({ length: 6 }, (_, index) => {
      const baselineAccuracy = Math.random() * 0.2 + 0.7 // 70-90%
      const currentAccuracy = baselineAccuracy + (Math.random() - 0.5) * 0.1 // ±5%

      return {
        model_id: `model_${index + 1}`,
        model_name: `自適應模型 ${index + 1}`,
        model_type: modelTypes[index % modelTypes.length],
        domain: domains[index % domains.length],
        current_accuracy: Math.max(0.5, Math.min(0.99, currentAccuracy)),
        baseline_accuracy: baselineAccuracy,
        learning_rate: Math.random() * 0.01 + 0.001, // 0.001-0.011
        adaptation_speed: adaptationSpeeds[index % adaptationSpeeds.length],
        training_status: trainingStatuses[index % trainingStatuses.length],
        last_adaptation_time: new Date(Date.now() - Math.random() * 3600000).toISOString(), // Within last hour
        training_iterations: Math.floor(Math.random() * 10000 + 1000),
        convergence_status: convergenceStatuses[index % convergenceStatuses.length],
        performance_trend: Array.from({ length: 24 }, (_, i) => ({
          timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
          accuracy: Math.max(0.5, Math.min(0.99, baselineAccuracy + Math.sin(i * 0.3) * 0.05 + (Math.random() - 0.5) * 0.02)),
          loss: Math.max(0.01, Math.min(0.5, 0.3 - Math.sin(i * 0.3) * 0.05 + (Math.random() - 0.5) * 0.02)),
          validation_score: Math.max(0.5, Math.min(0.99, baselineAccuracy + Math.sin(i * 0.3) * 0.03 + (Math.random() - 0.5) * 0.01))
        }))
      }
    })
  }, [])

  // 模擬生成數據漂移數據
  const generateDataDrifts = useCallback((): DataDrift[] => {
    const features = [
      'CPU 使用率',
      '記憶體消耗',
      '網路延遲',
      '吞吐量',
      '錯誤率',
      '溫度',
      '功耗',
      '信號強度'
    ]

    return features.map((feature, index) => {
      const driftScore = Math.random()
      let driftStatus: DataDrift['drift_status']
      if (driftScore < 0.3) driftStatus = 'stable'
      else if (driftScore < 0.7) driftStatus = 'moderate_drift'
      else driftStatus = 'significant_drift'

      return {
        feature_name: feature,
        drift_score: driftScore,
        drift_status: driftStatus,
        historical_values: Array.from({ length: 50 }, () => Math.random() * 100),
        current_distribution: Array.from({ length: 20 }, () => Math.random() * 100),
        reference_distribution: Array.from({ length: 20 }, () => Math.random() * 100),
        mitigation_strategy: driftStatus === 'significant_drift' ? '立即重新訓練模型' :
                            driftStatus === 'moderate_drift' ? '調整學習率' : '持續監控'
      }
    })
  }, [])

  // 模擬生成在線學習指標
  const generateOnlineLearningMetrics = useCallback((): OnlineLearningMetrics => {
    return {
      total_data_points_processed: Math.floor(Math.random() * 100000 + 500000),
      learning_sessions_today: Math.floor(Math.random() * 50 + 20),
      average_adaptation_time: Math.random() * 30 + 5, // 5-35 minutes
      model_improvements: Math.floor(Math.random() * 15 + 5),
      accuracy_gain_today: Math.random() * 5 + 0.5, // 0.5-5.5%
      concept_drift_events: Math.floor(Math.random() * 8 + 2),
      automated_retraining_count: Math.floor(Math.random() * 12 + 3),
      human_intervention_required: Math.floor(Math.random() * 3)
    }
  }, [])

  // 模擬生成適應事件
  const generateAdaptationEvents = useCallback((): AdaptationEvent[] => {
    const eventTypes: AdaptationEvent['event_type'][] = ['concept_drift_detected', 'performance_degradation', 'new_data_pattern', 'scheduled_update']
    const actionTypes: AdaptationEvent['adaptation_action'][] = ['retrain_model', 'update_parameters', 'feature_engineering', 'architecture_change']

    return Array.from({ length: 10 }, (_, index) => {
      const beforePerformance = Math.random() * 0.3 + 0.6 // 60-90%
      const afterPerformance = beforePerformance + (Math.random() - 0.3) * 0.1 // Usually improvement

      return {
        event_id: `event_${index + 1}`,
        timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString(), // Within last day
        model_name: `自適應模型 ${Math.floor(Math.random() * 6) + 1}`,
        event_type: eventTypes[index % eventTypes.length],
        trigger_reason: '檢測到數據分佈變化',
        adaptation_action: actionTypes[index % actionTypes.length],
        before_performance: beforePerformance,
        after_performance: Math.max(beforePerformance, afterPerformance),
        adaptation_time: Math.random() * 25 + 5, // 5-30 minutes
        success: Math.random() > 0.1 // 90% success rate
      }
    })
  }, [])

  // 初始化數據
  useEffect(() => {
    if (enabled) {
      setLoading(true)
      setTimeout(() => {
        setLearningModels(generateLearningModels())
        setDataDrifts(generateDataDrifts())
        setOnlineLearningMetrics(generateOnlineLearningMetrics())
        setAdaptationEvents(generateAdaptationEvents())
        setLastUpdate(new Date().toLocaleTimeString())
        setLoading(false)
      }, 1200)
    }
  }, [enabled, generateLearningModels, generateDataDrifts, generateOnlineLearningMetrics, generateAdaptationEvents])

  // 自動更新數據
  useEffect(() => {
    if (!enabled || !autoMode) return

    const interval = setInterval(() => {
      setLearningModels(generateLearningModels())
      setDataDrifts(generateDataDrifts())
      setOnlineLearningMetrics(generateOnlineLearningMetrics())
      setLastUpdate(new Date().toLocaleTimeString())
    }, 15000) // 15秒更新

    return () => clearInterval(interval)
  }, [enabled, autoMode, generateLearningModels, generateDataDrifts, generateOnlineLearningMetrics])

  // 準備圖表數據
  const modelPerformanceChartData = {
    labels: learningModels.map(m => m.model_name),
    datasets: [
      {
        label: '當前準確率',
        data: learningModels.map(m => m.current_accuracy * 100),
        backgroundColor: 'rgba(0, 212, 255, 0.6)',
        borderColor: 'rgba(0, 212, 255, 1)',
        borderWidth: 1
      },
      {
        label: '基準準確率',
        data: learningModels.map(m => m.baseline_accuracy * 100),
        backgroundColor: 'rgba(255, 193, 7, 0.6)',
        borderColor: 'rgba(255, 193, 7, 1)',
        borderWidth: 1
      }
    ]
  }

  const driftScoreChartData = {
    labels: dataDrifts.map(d => d.feature_name),
    datasets: [
      {
        label: '漂移分數',
        data: dataDrifts.map(d => d.drift_score),
        backgroundColor: dataDrifts.map(d => 
          d.drift_status === 'stable' ? 'rgba(76, 175, 80, 0.6)' :
          d.drift_status === 'moderate_drift' ? 'rgba(255, 152, 0, 0.6)' : 'rgba(244, 67, 54, 0.6)'
        ),
        borderColor: dataDrifts.map(d => 
          d.drift_status === 'stable' ? 'rgba(76, 175, 80, 1)' :
          d.drift_status === 'moderate_drift' ? 'rgba(255, 152, 0, 1)' : 'rgba(244, 67, 54, 1)'
        ),
        borderWidth: 1
      }
    ]
  }

  const selectedModelTrendData = selectedModel ? (() => {
    const model = learningModels.find(m => m.model_id === selectedModel)
    if (!model) return null

    return {
      labels: model.performance_trend.map(p => new Date(p.timestamp).toLocaleTimeString()),
      datasets: [
        {
          label: '準確率',
          data: model.performance_trend.map(p => p.accuracy * 100),
          borderColor: 'rgba(0, 212, 255, 1)',
          backgroundColor: 'rgba(0, 212, 255, 0.1)',
          tension: 0.4
        },
        {
          label: '驗證分數',
          data: model.performance_trend.map(p => p.validation_score * 100),
          borderColor: 'rgba(76, 175, 80, 1)',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          tension: 0.4
        }
      ]
    }
  })() : null

  const getModelTypeIcon = (type: string): string => {
    switch (type) {
      case 'neural_network': return '🧠'
      case 'random_forest': return '🌳'
      case 'svm': return '📊'
      case 'lstm': return '🔄'
      case 'transformer': return '⚡'
      default: return '🤖'
    }
  }

  const getDomainIcon = (domain: string): string => {
    switch (domain) {
      case 'interference_prediction': return '📡'
      case 'handover_optimization': return '🔄'
      case 'resource_allocation': return '⚖️'
      case 'fault_detection': return '🔍'
      default: return '🎯'
    }
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'training': return '#FF9800'
      case 'evaluating': return '#2196F3'
      case 'updating': return '#9C27B0'
      case 'idle': return '#4CAF50'
      default: return '#9E9E9E'
    }
  }

  const getDriftStatusColor = (status: string): string => {
    switch (status) {
      case 'stable': return '#4CAF50'
      case 'moderate_drift': return '#FF9800'
      case 'significant_drift': return '#F44336'
      default: return '#9E9E9E'
    }
  }

  if (!enabled) return null

  return (
    <div className="adaptive-learning-viewer">
      <div className="viewer-header">
        <h2>🧠 自適應學習系統</h2>
        <div className="header-controls">
          <label className="auto-mode-toggle">
            <input 
              type="checkbox" 
              checked={autoMode} 
              onChange={(e) => setAutoMode(e.target.checked)}
            />
            自動模式
          </label>
          <span className="last-update">最後更新: {lastUpdate}</span>
        </div>
      </div>

      {loading ? (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>正在加載自適應學習數據...</p>
        </div>
      ) : (
        <div className="viewer-content">
          {/* 整體指標概覽 */}
          {onlineLearningMetrics && (
            <div className="section metrics-overview">
              <h3>📈 學習指標概覽</h3>
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-icon">📊</div>
                  <div className="metric-content">
                    <div className="metric-value">{onlineLearningMetrics.total_data_points_processed.toLocaleString()}</div>
                    <div className="metric-label">已處理數據點</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">🎯</div>
                  <div className="metric-content">
                    <div className="metric-value">{onlineLearningMetrics.learning_sessions_today}</div>
                    <div className="metric-label">今日學習會話</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">⏱️</div>
                  <div className="metric-content">
                    <div className="metric-value">{onlineLearningMetrics.average_adaptation_time.toFixed(1)}分</div>
                    <div className="metric-label">平均適應時間</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">📈</div>
                  <div className="metric-content">
                    <div className="metric-value">+{onlineLearningMetrics.accuracy_gain_today.toFixed(1)}%</div>
                    <div className="metric-label">今日準確率提升</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">🔄</div>
                  <div className="metric-content">
                    <div className="metric-value">{onlineLearningMetrics.automated_retraining_count}</div>
                    <div className="metric-label">自動重訓次數</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-icon">⚠️</div>
                  <div className="metric-content">
                    <div className="metric-value">{onlineLearningMetrics.concept_drift_events}</div>
                    <div className="metric-label">概念漂移事件</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 模型性能比較 */}
          <div className="section model-performance">
            <h3>🤖 模型性能比較</h3>
            <div className="charts-container">
              <div className="chart-card">
                <h4>準確率對比</h4>
                <Bar 
                  data={modelPerformanceChartData}
                  options={{
                    responsive: true,
                    scales: {
                      y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                          display: true,
                          text: '準確率 (%)'
                        }
                      }
                    }
                  }}
                />
              </div>
              {selectedModelTrendData && (
                <div className="chart-card">
                  <h4>模型性能趨勢</h4>
                  <Line 
                    data={selectedModelTrendData}
                    options={{
                      responsive: true,
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 100,
                          title: {
                            display: true,
                            text: '性能指標 (%)'
                          }
                        }
                      }
                    }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* 學習模型列表 */}
          <div className="section model-list">
            <h3>📋 學習模型狀態</h3>
            <div className="model-cards">
              {learningModels.map((model) => (
                <div 
                  key={model.model_id} 
                  className={`model-card ${selectedModel === model.model_id ? 'selected' : ''}`}
                  onClick={() => setSelectedModel(model.model_id)}
                >
                  <div className="model-header">
                    <div className="model-title">
                      <span className="model-icon">{getModelTypeIcon(model.model_type)}</span>
                      <span className="model-name">{model.model_name}</span>
                    </div>
                    <div className="model-domain">
                      <span className="domain-icon">{getDomainIcon(model.domain)}</span>
                    </div>
                  </div>
                  <div className="model-metrics">
                    <div className="metric-row">
                      <span className="label">當前準確率:</span>
                      <span className="value">{(model.current_accuracy * 100).toFixed(1)}%</span>
                    </div>
                    <div className="metric-row">
                      <span className="label">基準提升:</span>
                      <span className={`value ${model.current_accuracy > model.baseline_accuracy ? 'positive' : 'negative'}`}>
                        {((model.current_accuracy - model.baseline_accuracy) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="metric-row">
                      <span className="label">訓練狀態:</span>
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(model.training_status) }}
                      >
                        {model.training_status === 'training' ? '訓練中' :
                         model.training_status === 'evaluating' ? '評估中' :
                         model.training_status === 'updating' ? '更新中' : '空閒'}
                      </span>
                    </div>
                    <div className="metric-row">
                      <span className="label">收斂狀態:</span>
                      <span className="value">
                        {model.convergence_status === 'converging' ? '收斂中' :
                         model.convergence_status === 'converged' ? '已收斂' : '發散'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 數據漂移監控 */}
          <div className="section data-drift">
            <h3>📊 數據漂移監控</h3>
            <div className="charts-container">
              <div className="chart-card">
                <h4>特徵漂移分數</h4>
                <Bar 
                  data={driftScoreChartData}
                  options={{
                    responsive: true,
                    scales: {
                      y: {
                        beginAtZero: true,
                        max: 1,
                        title: {
                          display: true,
                          text: '漂移分數'
                        }
                      }
                    }
                  }}
                />
              </div>
              <div className="drift-status-list">
                <h4>漂移狀態詳情</h4>
                {dataDrifts.map((drift, index) => (
                  <div key={index} className="drift-item">
                    <div className="drift-header">
                      <span className="feature-name">{drift.feature_name}</span>
                      <span 
                        className="drift-status"
                        style={{ color: getDriftStatusColor(drift.drift_status) }}
                      >
                        {drift.drift_status === 'stable' ? '穩定' :
                         drift.drift_status === 'moderate_drift' ? '中度漂移' : '顯著漂移'}
                      </span>
                    </div>
                    <div className="drift-details">
                      <span className="drift-score">分數: {drift.drift_score.toFixed(3)}</span>
                      <span className="mitigation">策略: {drift.mitigation_strategy}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 適應事件歷史 */}
          <div className="section adaptation-events">
            <h3>🔄 適應事件歷史</h3>
            <div className="events-table">
              <table>
                <thead>
                  <tr>
                    <th>時間</th>
                    <th>模型</th>
                    <th>事件類型</th>
                    <th>適應動作</th>
                    <th>性能變化</th>
                    <th>適應時間</th>
                    <th>狀態</th>
                  </tr>
                </thead>
                <tbody>
                  {adaptationEvents.slice(0, 8).map((event) => (
                    <tr key={event.event_id}>
                      <td>{new Date(event.timestamp).toLocaleString()}</td>
                      <td>{event.model_name}</td>
                      <td>{event.event_type}</td>
                      <td>{event.adaptation_action}</td>
                      <td>
                        <span className={`performance-change ${event.after_performance > event.before_performance ? 'positive' : 'negative'}`}>
                          {((event.after_performance - event.before_performance) * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td>{event.adaptation_time.toFixed(1)}分</td>
                      <td>
                        <span className={`status-badge ${event.success ? 'success' : 'failure'}`}>
                          {event.success ? '成功' : '失敗'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdaptiveLearningSystemViewer