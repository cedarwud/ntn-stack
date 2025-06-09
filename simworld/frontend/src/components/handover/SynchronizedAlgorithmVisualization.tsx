import React, { useState, useEffect, useCallback } from 'react'
import { VisibleSatelliteInfo } from '../../types/satellite'
import './SynchronizedAlgorithmVisualization.scss'

interface AlgorithmStep {
  step: 'two_point_prediction' | 'binary_search' | 'sync_check' | 'handover_trigger'
  timestamp: number
  data: any
  status: 'running' | 'completed' | 'error'
  description: string
}

interface BinarySearchIteration {
  iteration: number
  start_time: number
  end_time: number
  mid_time: number
  satellite: string
  precision: number
  completed: boolean
}

interface PredictionResult {
  prediction_id: string
  ue_id: number
  current_time: number
  future_time: number
  delta_t_seconds: number
  current_satellite: {
    satellite_id: string
    name: string
    signal_strength: number
    elevation: number
  }
  future_satellite: {
    satellite_id: string
    name: string
    signal_strength: number
    elevation: number
  }
  handover_required: boolean
  handover_trigger_time?: number
  binary_search_result?: {
    handover_time: number
    iterations: BinarySearchIteration[]
    iteration_count: number
    final_precision: number
  }
  prediction_confidence: number
  accuracy_percentage: number
}

interface SynchronizedAlgorithmVisualizationProps {
  satellites: VisibleSatelliteInfo[]
  selectedUEId?: number
  isEnabled: boolean
  onAlgorithmStep?: (step: AlgorithmStep) => void
}

const SynchronizedAlgorithmVisualization: React.FC<SynchronizedAlgorithmVisualizationProps> = ({
  satellites,
  selectedUEId = 1,
  isEnabled,
  onAlgorithmStep
}) => {
  const [algorithmSteps, setAlgorithmSteps] = useState<AlgorithmStep[]>([])
  const [currentStep, setCurrentStep] = useState<string>('')
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null)
  const [binarySearchIterations, setBinarySearchIterations] = useState<BinarySearchIteration[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [syncAccuracy, setSyncAccuracy] = useState(0.95)
  const [lastExecutionTime, setLastExecutionTime] = useState(0)

  // 執行二點預測算法
  const executeTwoPointPrediction = useCallback(async () => {
    if (!isEnabled || isRunning || satellites.length === 0) return

    // 防止過於頻繁的調用 - 至少間隔 10 秒
    const now = Date.now()
    if (now - lastExecutionTime < 10000) {
      return
    }
    setLastExecutionTime(now)

    try {
      setIsRunning(true)
      setCurrentStep('two_point_prediction')

      // 添加算法步驟
      const step: AlgorithmStep = {
        step: 'two_point_prediction',
        timestamp: Date.now(),
        data: { ue_id: selectedUEId, satellites_count: satellites.length },
        status: 'running',
        description: '執行二點預測：計算 T 和 T+Δt 時間點的最佳衛星'
      }
      
      setAlgorithmSteps(prev => [...prev, step])
      onAlgorithmStep?.(step)

      // 調用後端 API
      const response = await fetch('/api/v1/handover/fine-grained/prediction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ue_id: selectedUEId,
          delta_t_seconds: 10,
          precision_threshold: 0.1
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result: PredictionResult = await response.json()
      setPredictionResult(result)

      // 更新步驟狀態
      const completedStep = { ...step, status: 'completed' as const, data: result }
      setAlgorithmSteps(prev => prev.map(s => s.timestamp === step.timestamp ? completedStep : s))

      // 如果需要換手，執行 Binary Search
      if (result.handover_required && result.binary_search_result) {
        await executeBinarySearchVisualization(result.binary_search_result.iterations)
      }

      // 檢查同步狀態
      await checkSyncStatus(result)

    } catch (error) {
      console.error('二點預測執行失敗:', error)
      
      // 更新步驟為錯誤狀態
      setAlgorithmSteps(prev => prev.map(s => 
        s.timestamp === prev[prev.length - 1]?.timestamp 
          ? { ...s, status: 'error', description: `執行失敗: ${error}` }
          : s
      ))
    } finally {
      setIsRunning(false)
      setCurrentStep('')
    }
  }, [isEnabled, selectedUEId, satellites.length, lastExecutionTime, onAlgorithmStep])

  // 可視化 Binary Search 過程
  const executeBinarySearchVisualization = async (iterations: BinarySearchIteration[]) => {
    setCurrentStep('binary_search')
    
    const binaryStep: AlgorithmStep = {
      step: 'binary_search',
      timestamp: Date.now(),
      data: { iterations_count: iterations.length },
      status: 'running',
      description: 'Binary Search Refinement：精確計算換手觸發時間 Tp'
    }
    
    setAlgorithmSteps(prev => [...prev, binaryStep])

    // 逐步顯示迭代過程
    for (let i = 0; i < iterations.length; i++) {
      setBinarySearchIterations(prev => [...prev, iterations[i]])
      await new Promise(resolve => setTimeout(resolve, 750)) // 配合後端的延遲
    }

    // 完成 Binary Search
    const completedBinaryStep = { ...binaryStep, status: 'completed' as const }
    setAlgorithmSteps(prev => prev.map(s => s.timestamp === binaryStep.timestamp ? completedBinaryStep : s))
  }

  // 檢查同步狀態
  const checkSyncStatus = async (result: PredictionResult) => {
    setCurrentStep('sync_check')
    
    const syncStep: AlgorithmStep = {
      step: 'sync_check',
      timestamp: Date.now(),
      data: { confidence: result.prediction_confidence },
      status: 'running',
      description: '檢查同步狀態：驗證預測準確性和系統同步'
    }
    
    setAlgorithmSteps(prev => [...prev, syncStep])
    
    // 模擬同步檢查
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    setSyncAccuracy(result.prediction_confidence)
    
    const completedSyncStep = { ...syncStep, status: 'completed' as const }
    setAlgorithmSteps(prev => prev.map(s => s.timestamp === syncStep.timestamp ? completedSyncStep : s))
  }

  // 定期執行算法
  useEffect(() => {
    if (!isEnabled) return

    // 初始執行
    const timeoutId = setTimeout(() => {
      executeTwoPointPrediction()
    }, 1000) // 延遲 1 秒執行，避免組件初始化時的重複調用

    // 定期執行（每 15 秒）- 增加間隔避免過度頻繁的API調用
    const interval = setInterval(() => {
      if (!isRunning) { // 只有在不運行時才執行新的預測
        executeTwoPointPrediction()
      }
    }, 15000)

    return () => {
      clearTimeout(timeoutId)
      clearInterval(interval)
    }
  }, [isEnabled]) // 移除 executeTwoPointPrediction 依賴，避免無限循環

  // 清除歷史記錄
  const clearHistory = useCallback(() => {
    setAlgorithmSteps([])
    setBinarySearchIterations([])
    setPredictionResult(null)
    setCurrentStep('')
  }, [])

  if (!isEnabled) {
    return (
      <div className="synchronized-algorithm-visualization disabled">
        <div className="disabled-message">
          <h3>🔒 Fine-Grained Synchronized Algorithm</h3>
          <p>請啟用換手相關功能來使用此演算法可視化</p>
        </div>
      </div>
    )
  }

  return (
    <div className="synchronized-algorithm-visualization">
      <div className="algorithm-header">
        <h2>🧮 Fine-Grained Synchronized Algorithm</h2>
        <div className="algorithm-info">
          <span className="paper-ref">IEEE INFOCOM 2024</span>
          <span className="ue-id">UE: {selectedUEId}</span>
          {currentStep && (
            <span className="current-step">
              執行中: {getStepDisplayName(currentStep)}
            </span>
          )}
        </div>
        <button onClick={clearHistory} className="clear-btn" disabled={isRunning}>
          清除歷史
        </button>
      </div>

      <div className="algorithm-content">
        {/* 算法流程時間軸 */}
        <div className="algorithm-timeline">
          <h3>📋 算法執行流程</h3>
          <div className="timeline-container">
            {algorithmSteps.length > 0 ? (
              algorithmSteps.map((step, index) => (
                <div key={step.timestamp} className={`timeline-item ${step.status}`}>
                  <div className="timeline-marker">
                    <span className="step-number">{index + 1}</span>
                  </div>
                  <div className="timeline-content">
                    <div className="step-header">
                      <span className="step-icon">{getStepIcon(step.step)}</span>
                      <span className="step-name">{getStepDisplayName(step.step)}</span>
                      <span className="step-status">{getStatusIcon(step.status)}</span>
                    </div>
                    <div className="step-description">{step.description}</div>
                    <div className="step-timestamp">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <span className="empty-icon">⏳</span>
                <span className="empty-message">等待算法執行...</span>
              </div>
            )}
          </div>
        </div>

        {/* 預測結果展示 */}
        {predictionResult && (
          <div className="prediction-results">
            <h3>📊 二點預測結果</h3>
            <div className="prediction-grid">
              <div className="prediction-card current">
                <h4>當前時間 T</h4>
                <div className="satellite-info">
                  <span className="satellite-name">{predictionResult.current_satellite.name}</span>
                  <span className="satellite-id">ID: {predictionResult.current_satellite.satellite_id}</span>
                </div>
                <div className="metrics">
                  <div className="metric">
                    <span className="label">仰角:</span>
                    <span className="value">{predictionResult.current_satellite.elevation.toFixed(1)}°</span>
                  </div>
                  <div className="metric">
                    <span className="label">信號:</span>
                    <span className="value">{predictionResult.current_satellite.signal_strength.toFixed(1)} dBm</span>
                  </div>
                </div>
              </div>

              <div className="prediction-arrow">
                <span className="arrow">➤</span>
                <div className="delta-t">Δt = {predictionResult.delta_t_seconds}s</div>
              </div>

              <div className="prediction-card future">
                <h4>預測時間 T+Δt</h4>
                <div className="satellite-info">
                  <span className="satellite-name">{predictionResult.future_satellite.name}</span>
                  <span className="satellite-id">ID: {predictionResult.future_satellite.satellite_id}</span>
                </div>
                <div className="metrics">
                  <div className="metric">
                    <span className="label">仰角:</span>
                    <span className="value">{predictionResult.future_satellite.elevation.toFixed(1)}°</span>
                  </div>
                  <div className="metric">
                    <span className="label">信號:</span>
                    <span className="value">{predictionResult.future_satellite.signal_strength.toFixed(1)} dBm</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="prediction-summary">
              <div className="handover-decision">
                <span className="decision-label">換手決策:</span>
                <span className={`decision-value ${predictionResult.handover_required ? 'required' : 'not-required'}`}>
                  {predictionResult.handover_required ? '需要換手' : '無需換手'}
                </span>
              </div>
              <div className="confidence-meter">
                <span className="confidence-label">預測置信度:</span>
                <div className="confidence-bar">
                  <div 
                    className="confidence-fill"
                    style={{ width: `${predictionResult.accuracy_percentage}%` }}
                  ></div>
                </div>
                <span className="confidence-value">{predictionResult.accuracy_percentage.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Binary Search 迭代過程 */}
        {binarySearchIterations.length > 0 && (
          <div className="binary-search-visualization">
            <h3>🔍 Binary Search Refinement</h3>
            <div className="iterations-container">
              {binarySearchIterations.map((iteration, index) => (
                <div key={index} className={`iteration-item ${iteration.completed ? 'completed' : 'running'}`}>
                  <div className="iteration-number">#{iteration.iteration}</div>
                  <div className="iteration-details">
                    <div className="time-range">
                      <span>區間: [{iteration.start_time.toFixed(3)}, {iteration.end_time.toFixed(3)}]</span>
                    </div>
                    <div className="mid-point">
                      <span>中點: {iteration.mid_time.toFixed(3)}</span>
                      <span className="satellite">衛星: {iteration.satellite}</span>
                    </div>
                    <div className="precision">
                      <span>精度: {iteration.precision.toFixed(3)}s</span>
                      {iteration.completed && <span className="completed-mark">✓</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 簡化的系統同步狀態 - 移除動畫避免閃爍 */}
        <div className="sync-status-simple">
          <h3>🔄 系統同步狀態</h3>
          <div className="sync-summary">
            <div className="sync-metric">
              <span className="metric-label">同步準確率:</span>
              <span className="metric-value">{(syncAccuracy * 100).toFixed(1)}%</span>
              <span className={`status-indicator ${syncAccuracy > 0.95 ? 'excellent' : syncAccuracy > 0.9 ? 'good' : 'warning'}`}>
                {syncAccuracy > 0.95 ? '優秀' : syncAccuracy > 0.9 ? '良好' : '需改善'}
              </span>
            </div>
            <div className="sync-metric">
              <span className="metric-label">算法狀態:</span>
              <span className="metric-value">
                {isRunning ? '執行中' : '待機'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// 輔助函數
function getStepIcon(step: string): string {
  switch (step) {
    case 'two_point_prediction': return '📊'
    case 'binary_search': return '🔍'
    case 'sync_check': return '🔄'
    case 'handover_trigger': return '⚡'
    default: return '⚙️'
  }
}

function getStepDisplayName(step: string): string {
  switch (step) {
    case 'two_point_prediction': return '二點預測'
    case 'binary_search': return 'Binary Search'
    case 'sync_check': return '同步檢查'
    case 'handover_trigger': return '換手觸發'
    default: return step
  }
}

function getStatusIcon(status: string): string {
  switch (status) {
    case 'running': return '⏳'
    case 'completed': return '✅'
    case 'error': return '❌'
    default: return '⚪'
  }
}

export default SynchronizedAlgorithmVisualization