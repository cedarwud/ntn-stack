import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useWebSocket } from '../../hooks/useWebSocket'
import { WebSocketEvent } from '../../types/charts'

// AI-RAN 決策數據類型
interface AIDecision {
  decision_id: string
  timestamp: string
  scenario_id: string
  input_state: {
    sinr_db: number
    rsrp_dbm: number
    interference_level_db: number
    frequency_mhz: number
    ue_count: number
    network_load: number
  }
  ai_analysis: {
    strategy: string
    confidence: number
    expected_improvement: number
    reasoning: string
    alternative_strategies: string[]
    risk_assessment: number
  }
  execution_result: {
    success: boolean
    actual_improvement: number
    execution_time_ms: number
    side_effects: string[]
  }
  learning_feedback: {
    reward: number
    state_quality: number
    action_effectiveness: number
  }
}

interface DecisionNode {
  id: string
  type: 'input' | 'analysis' | 'decision' | 'execution' | 'feedback'
  position: { x: number; y: number }
  data: any
  status: 'pending' | 'processing' | 'completed' | 'failed'
  timestamp: string
}

interface AIRANDecisionVisualizationProps {
  height?: number
  realTimeEnabled?: boolean
  showConfidenceMetrics?: boolean
  showLearningProgress?: boolean
  onDecisionClick?: (decision: AIDecision) => void
}

const AIRANDecisionVisualization: React.FC<AIRANDecisionVisualizationProps> = ({
  height = 600,
  realTimeEnabled = true,
  showConfidenceMetrics = true,
  showLearningProgress = true,
  onDecisionClick
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number | null>(null)
  
  // 狀態管理
  const [decisions, setDecisions] = useState<AIDecision[]>([])
  const [currentDecision, setCurrentDecision] = useState<AIDecision | null>(null)
  const [decisionNodes, setDecisionNodes] = useState<DecisionNode[]>([])
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [aiMetrics, setAiMetrics] = useState({
    total_decisions: 0,
    success_rate: 0.0,
    average_confidence: 0.0,
    learning_progress: 0.0,
    model_accuracy: 0.0
  })
  
  // 配置選項
  const [visualizationMode, setVisualizationMode] = useState<'flow' | 'timeline' | 'network'>('flow')
  const [showDetails, setShowDetails] = useState(true)
  const [animateTransitions, setAnimateTransitions] = useState(true)
  const [timeWindow, setTimeWindow] = useState(300) // 秒
  
  // 性能監控
  const [renderCount, setRenderCount] = useState(0)
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)

  // WebSocket 連接處理 AI-RAN 決策數據
  const { isConnected, sendMessage } = useWebSocket({
    url: 'ws://localhost:8080/ws/ai-ran-decisions',
    enableReconnect: realTimeEnabled,
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('AI-RAN Decision Visualization WebSocket 已連接')
      if (realTimeEnabled) {
        sendMessage({
          type: 'subscribe',
          topics: ['ai_decisions', 'learning_updates', 'model_metrics']
        })
      }
    }
  })

  // 處理 WebSocket 消息
  function handleWebSocketMessage(event: WebSocketEvent) {
    try {
      switch (event.type) {
        case 'ai_ran_decisions':
          const newDecision = event.data as AIDecision
          setDecisions(prev => {
            const updated = [newDecision, ...prev].slice(0, 50) // 保留最近 50 個決策
            return updated
          })
          setCurrentDecision(newDecision)
          createDecisionFlow(newDecision)
          setLastUpdate(event.timestamp)
          break
          
        case 'ai_learning_updates':
          setAiMetrics(prev => ({
            ...prev,
            ...event.data
          }))
          break
          
        case 'model_metrics':
          setAiMetrics(prev => ({
            ...prev,
            model_accuracy: event.data.accuracy,
            learning_progress: event.data.progress
          }))
          break
      }
    } catch (error) {
      console.error('處理 AI 決策 WebSocket 消息失敗:', error)
    }
  }

  // 創建決策流程節點
  const createDecisionFlow = useCallback((decision: AIDecision) => {
    const nodes: DecisionNode[] = [
      {
        id: `${decision.decision_id}_input`,
        type: 'input',
        position: { x: 50, y: 100 },
        data: decision.input_state,
        status: 'completed',
        timestamp: decision.timestamp
      },
      {
        id: `${decision.decision_id}_analysis`,
        type: 'analysis',
        position: { x: 200, y: 100 },
        data: decision.ai_analysis,
        status: 'completed',
        timestamp: decision.timestamp
      },
      {
        id: `${decision.decision_id}_decision`,
        type: 'decision',
        position: { x: 350, y: 100 },
        data: {
          strategy: decision.ai_analysis.strategy,
          confidence: decision.ai_analysis.confidence
        },
        status: 'completed',
        timestamp: decision.timestamp
      },
      {
        id: `${decision.decision_id}_execution`,
        type: 'execution',
        position: { x: 500, y: 100 },
        data: decision.execution_result,
        status: decision.execution_result.success ? 'completed' : 'failed',
        timestamp: decision.timestamp
      },
      {
        id: `${decision.decision_id}_feedback`,
        type: 'feedback',
        position: { x: 650, y: 100 },
        data: decision.learning_feedback,
        status: 'completed',
        timestamp: decision.timestamp
      }
    ]
    
    if (animateTransitions) {
      // 動畫顯示節點
      nodes.forEach((node, index) => {
        setTimeout(() => {
          setDecisionNodes(prev => {
            const filtered = prev.filter(n => !n.id.startsWith(decision.decision_id))
            return [...filtered, ...nodes.slice(0, index + 1)]
          })
        }, index * 300)
      })
    } else {
      setDecisionNodes(prev => {
        const filtered = prev.filter(n => !n.id.startsWith(decision.decision_id))
        return [...filtered, ...nodes]
      })
    }
  }, [animateTransitions])

  // 畫布繪製邏輯
  const drawVisualization = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清除畫布
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 設置畫布大小
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width
    canvas.height = rect.height

    // 根據可視化模式繪製
    switch (visualizationMode) {
      case 'flow':
        drawDecisionFlow(ctx)
        break
      case 'timeline':
        drawTimeline(ctx)
        break
      case 'network':
        drawNeuralNetwork(ctx)
        break
    }

    setRenderCount(prev => prev + 1)
  }, [visualizationMode, decisionNodes, decisions, selectedNode])

  // 繪製決策流程圖
  const drawDecisionFlow = (ctx: CanvasRenderingContext2D) => {
    const nodeRadius = 30
    const nodeColors = {
      input: '#2196F3',
      analysis: '#FF9800',
      decision: '#4CAF50',
      execution: '#9C27B0',
      feedback: '#607D8B'
    }
    
    const statusColors = {
      pending: '#FFC107',
      processing: '#2196F3',
      completed: '#4CAF50',
      failed: '#F44336'
    }

    // 繪製連接線
    if (decisionNodes.length > 1) {
      ctx.strokeStyle = '#666'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 5])
      
      for (let i = 0; i < decisionNodes.length - 1; i++) {
        const current = decisionNodes[i]
        const next = decisionNodes[i + 1]
        
        if (current.id.split('_')[0] === next.id.split('_')[0]) {
          ctx.beginPath()
          ctx.moveTo(current.position.x + nodeRadius, current.position.y)
          ctx.lineTo(next.position.x - nodeRadius, next.position.y)
          ctx.stroke()
        }
      }
      ctx.setLineDash([])
    }

    // 繪製節點
    decisionNodes.forEach(node => {
      const isSelected = selectedNode === node.id
      
      // 節點圓圈
      ctx.fillStyle = nodeColors[node.type]
      ctx.strokeStyle = statusColors[node.status]
      ctx.lineWidth = isSelected ? 4 : 2
      
      ctx.beginPath()
      ctx.arc(node.position.x, node.position.y, nodeRadius, 0, 2 * Math.PI)
      ctx.fill()
      ctx.stroke()
      
      // 節點標籤
      ctx.fillStyle = '#FFF'
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'
      ctx.fillText(
        node.type.toUpperCase(),
        node.position.x,
        node.position.y + 4
      )
      
      // 狀態指示器
      if (node.status === 'processing') {
        const time = Date.now() * 0.01
        const pulseRadius = nodeRadius + Math.sin(time) * 5
        ctx.strokeStyle = statusColors[node.status]
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.arc(node.position.x, node.position.y, pulseRadius, 0, 2 * Math.PI)
        ctx.stroke()
      }
      
      // 詳細信息
      if (showDetails && isSelected) {
        drawNodeDetails(ctx, node)
      }
    })
  }

  // 繪製時間軸視圖
  const drawTimeline = (ctx: CanvasRenderingContext2D) => {
    const timelineHeight = ctx.canvas.height - 100
    const timelineStart = 50
    const timelineEnd = ctx.canvas.width - 50
    const timelineY = 50
    
    // 繪製時間軸
    ctx.strokeStyle = '#666'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(timelineStart, timelineY)
    ctx.lineTo(timelineEnd, timelineY)
    ctx.stroke()
    
    // 當前時間
    const now = Date.now()
    const timeRange = timeWindow * 1000 // 轉換為毫秒
    
    // 繪製決策點
    decisions.slice(0, 20).forEach((decision, index) => {
      const decisionTime = new Date(decision.timestamp).getTime()
      const relativeTime = now - decisionTime
      
      if (relativeTime <= timeRange) {
        const x = timelineEnd - (relativeTime / timeRange) * (timelineEnd - timelineStart)
        const y = timelineY + 20 + (index % 5) * 40
        
        // 決策點
        const color = decision.execution_result.success ? '#4CAF50' : '#F44336'
        ctx.fillStyle = color
        ctx.beginPath()
        ctx.arc(x, y, 8, 0, 2 * Math.PI)
        ctx.fill()
        
        // 置信度線
        const confidenceHeight = decision.ai_analysis.confidence * 60
        ctx.strokeStyle = color
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.moveTo(x, y + 10)
        ctx.lineTo(x, y + 10 + confidenceHeight)
        ctx.stroke()
        
        // 策略標籤
        ctx.fillStyle = '#FFF'
        ctx.font = '10px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(
          decision.ai_analysis.strategy.substring(0, 8),
          x,
          y + 80
        )
      }
    })
    
    // 時間標籤
    ctx.fillStyle = '#999'
    ctx.font = '12px Arial'
    ctx.textAlign = 'left'
    ctx.fillText('現在', timelineEnd - 20, timelineY - 10)
    ctx.textAlign = 'right'
    ctx.fillText(`${timeWindow}秒前`, timelineStart + 20, timelineY - 10)
  }

  // 繪製神經網路視圖
  const drawNeuralNetwork = (ctx: CanvasRenderingContext2D) => {
    const centerX = ctx.canvas.width / 2
    const centerY = ctx.canvas.height / 2
    const layers = [
      { name: '輸入層', nodes: 6, color: '#2196F3' },
      { name: '隱藏層1', nodes: 8, color: '#FF9800' },
      { name: '隱藏層2', nodes: 6, color: '#FF9800' },
      { name: '輸出層', nodes: 4, color: '#4CAF50' }
    ]
    
    const layerSpacing = 120
    const nodeSpacing = 40
    
    layers.forEach((layer, layerIndex) => {
      const x = centerX - (layers.length * layerSpacing) / 2 + layerIndex * layerSpacing
      const startY = centerY - (layer.nodes * nodeSpacing) / 2
      
      // 繪製層標籤
      ctx.fillStyle = '#FFF'
      ctx.font = '14px Arial'
      ctx.textAlign = 'center'
      ctx.fillText(layer.name, x, startY - 30)
      
      // 繪製節點
      for (let nodeIndex = 0; nodeIndex < layer.nodes; nodeIndex++) {
        const y = startY + nodeIndex * nodeSpacing
        
        // 節點激活程度（模擬）
        const activation = Math.random()
        const alpha = 0.3 + activation * 0.7
        
        ctx.fillStyle = layer.color
        ctx.globalAlpha = alpha
        ctx.beginPath()
        ctx.arc(x, y, 8, 0, 2 * Math.PI)
        ctx.fill()
        ctx.globalAlpha = 1
        
        // 繪製連接線到下一層
        if (layerIndex < layers.length - 1) {
          const nextLayer = layers[layerIndex + 1]
          const nextX = x + layerSpacing
          const nextStartY = centerY - (nextLayer.nodes * nodeSpacing) / 2
          
          for (let nextNodeIndex = 0; nextNodeIndex < nextLayer.nodes; nextNodeIndex++) {
            const nextY = nextStartY + nextNodeIndex * nodeSpacing
            
            // 連接強度（模擬）
            const weight = Math.random()
            ctx.strokeStyle = weight > 0.5 ? '#4CAF50' : '#FF5722'
            ctx.lineWidth = weight * 2
            ctx.globalAlpha = 0.3
            
            ctx.beginPath()
            ctx.moveTo(x + 8, y)
            ctx.lineTo(nextX - 8, nextY)
            ctx.stroke()
            ctx.globalAlpha = 1
          }
        }
      }
    })
  }

  // 繪製節點詳細信息
  const drawNodeDetails = (ctx: CanvasRenderingContext2D, node: DecisionNode) => {
    const detailX = node.position.x + 50
    const detailY = node.position.y - 50
    const detailWidth = 200
    const detailHeight = 120
    
    // 背景
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
    ctx.fillRect(detailX, detailY, detailWidth, detailHeight)
    
    // 邊框
    ctx.strokeStyle = '#666'
    ctx.lineWidth = 1
    ctx.strokeRect(detailX, detailY, detailWidth, detailHeight)
    
    // 文字
    ctx.fillStyle = '#FFF'
    ctx.font = '12px Arial'
    ctx.textAlign = 'left'
    
    let textY = detailY + 20
    const lineHeight = 16
    
    ctx.fillText(`類型: ${node.type}`, detailX + 10, textY)
    textY += lineHeight
    ctx.fillText(`狀態: ${node.status}`, detailX + 10, textY)
    textY += lineHeight
    
    // 根據節點類型顯示特定信息
    switch (node.type) {
      case 'input':
        ctx.fillText(`SINR: ${node.data.sinr_db?.toFixed(1)} dB`, detailX + 10, textY)
        textY += lineHeight
        ctx.fillText(`頻率: ${node.data.frequency_mhz} MHz`, detailX + 10, textY)
        break
      case 'analysis':
        ctx.fillText(`策略: ${node.data.strategy}`, detailX + 10, textY)
        textY += lineHeight
        ctx.fillText(`置信度: ${(node.data.confidence * 100).toFixed(1)}%`, detailX + 10, textY)
        break
      case 'execution':
        ctx.fillText(`成功: ${node.data.success ? '是' : '否'}`, detailX + 10, textY)
        textY += lineHeight
        ctx.fillText(`用時: ${node.data.execution_time_ms}ms`, detailX + 10, textY)
        break
      case 'feedback':
        ctx.fillText(`獎勵: ${node.data.reward?.toFixed(2)}`, detailX + 10, textY)
        textY += lineHeight
        ctx.fillText(`效果: ${(node.data.action_effectiveness * 100).toFixed(1)}%`, detailX + 10, textY)
        break
    }
  }

  // 鼠標點擊處理
  const handleCanvasClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // 檢查點擊的節點
    for (const node of decisionNodes) {
      const dx = x - node.position.x
      const dy = y - node.position.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      
      if (distance <= 30) {
        setSelectedNode(selectedNode === node.id ? null : node.id)
        
        // 如果點擊的是完整決策，調用回調
        if (onDecisionClick && currentDecision) {
          const decisionId = node.id.split('_')[0]
          if (decisionId === currentDecision.decision_id) {
            onDecisionClick(currentDecision)
          }
        }
        break
      }
    }
  }, [decisionNodes, selectedNode, currentDecision, onDecisionClick])

  // 渲染循環
  useEffect(() => {
    const animate = () => {
      drawVisualization()
      if (animateTransitions) {
        animationFrameRef.current = requestAnimationFrame(animate)
      }
    }
    
    if (animateTransitions) {
      animate()
    } else {
      drawVisualization()
    }
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [drawVisualization, animateTransitions])

  // 模擬數據（開發測試用）
  useEffect(() => {
    if (!realTimeEnabled && decisions.length === 0) {
      const mockDecision: AIDecision = {
        decision_id: 'mock_001',
        timestamp: new Date().toISOString(),
        scenario_id: 'scenario_001',
        input_state: {
          sinr_db: -5,
          rsrp_dbm: -85,
          interference_level_db: -70,
          frequency_mhz: 2150,
          ue_count: 5,
          network_load: 0.7
        },
        ai_analysis: {
          strategy: 'frequency_hopping',
          confidence: 0.85,
          expected_improvement: 8.5,
          reasoning: '檢測到強干擾，建議進行頻率跳變',
          alternative_strategies: ['power_control', 'beam_forming'],
          risk_assessment: 0.2
        },
        execution_result: {
          success: true,
          actual_improvement: 7.8,
          execution_time_ms: 150,
          side_effects: []
        },
        learning_feedback: {
          reward: 0.78,
          state_quality: 0.82,
          action_effectiveness: 0.91
        }
      }
      
      setDecisions([mockDecision])
      setCurrentDecision(mockDecision)
      createDecisionFlow(mockDecision)
      setAiMetrics({
        total_decisions: 1,
        success_rate: 1.0,
        average_confidence: 0.85,
        learning_progress: 0.75,
        model_accuracy: 0.88
      })
    }
  }, [realTimeEnabled, decisions.length, createDecisionFlow])

  // 記憶化的指標統計
  const statisticsData = useMemo(() => {
    if (decisions.length === 0) return null
    
    const recentDecisions = decisions.slice(0, 10)
    const successCount = recentDecisions.filter(d => d.execution_result.success).length
    const avgConfidence = recentDecisions.reduce((sum, d) => sum + d.ai_analysis.confidence, 0) / recentDecisions.length
    const avgImprovement = recentDecisions.reduce((sum, d) => sum + d.execution_result.actual_improvement, 0) / recentDecisions.length
    
    return {
      success_rate: (successCount / recentDecisions.length) * 100,
      avg_confidence: avgConfidence * 100,
      avg_improvement: avgImprovement,
      total_decisions: decisions.length
    }
  }, [decisions])

  return (
    <div className="ai-ran-decision-visualization" style={{ 
      width: '100%', 
      height: `${height}px`,
      background: '#1a1a1a',
      position: 'relative',
      borderRadius: '4px',
      overflow: 'hidden'
    }}>
      {/* 控制面板 */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '10px',
        borderRadius: '4px',
        zIndex: 100,
        minWidth: '200px'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>AI-RAN 決策可視化</h4>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label>
            可視化模式:
            <select
              value={visualizationMode}
              onChange={(e) => setVisualizationMode(e.target.value as any)}
              style={{ marginLeft: '5px', padding: '2px' }}
            >
              <option value="flow">決策流程</option>
              <option value="timeline">時間軸</option>
              <option value="network">神經網路</option>
            </select>
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={realTimeEnabled}
              onChange={(e) => setRealTimeEnabled(e.target.checked)}
            />
            實時模式 {isConnected ? '🟢' : '🔴'}
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={showDetails}
              onChange={(e) => setShowDetails(e.target.checked)}
            />
            顯示詳情
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={animateTransitions}
              onChange={(e) => setAnimateTransitions(e.target.checked)}
            />
            動畫效果
          </label>
          
          {visualizationMode === 'timeline' && (
            <label>
              時間窗口:
              <select
                value={timeWindow}
                onChange={(e) => setTimeWindow(Number(e.target.value))}
                style={{ marginLeft: '5px', padding: '2px' }}
              >
                <option value={60}>1分鐘</option>
                <option value={300}>5分鐘</option>
                <option value={600}>10分鐘</option>
                <option value={1800}>30分鐘</option>
              </select>
            </label>
          )}
        </div>
      </div>
      
      {/* 統計面板 */}
      {showConfidenceMetrics && statisticsData && (
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          background: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '10px',
          borderRadius: '4px',
          zIndex: 100,
          minWidth: '200px'
        }}>
          <h4 style={{ margin: '0 0 10px 0' }}>AI 性能指標</h4>
          <div style={{ fontSize: '12px', lineHeight: '1.4' }}>
            <div>決策總數: {statisticsData.total_decisions}</div>
            <div>成功率: {statisticsData.success_rate.toFixed(1)}%</div>
            <div>平均置信度: {statisticsData.avg_confidence.toFixed(1)}%</div>
            <div>平均改善: {statisticsData.avg_improvement.toFixed(1)} dB</div>
            {showLearningProgress && (
              <>
                <div>學習進度: {(aiMetrics.learning_progress * 100).toFixed(1)}%</div>
                <div>模型準確度: {(aiMetrics.model_accuracy * 100).toFixed(1)}%</div>
              </>
            )}
          </div>
          
          {lastUpdate && (
            <div style={{ fontSize: '10px', marginTop: '10px', color: '#aaa' }}>
              最後更新: {new Date(lastUpdate).toLocaleTimeString()}
            </div>
          )}
        </div>
      )}
      
      {/* 當前決策信息 */}
      {currentDecision && showDetails && (
        <div style={{
          position: 'absolute',
          bottom: '10px',
          left: '10px',
          background: 'rgba(0, 0, 0, 0.9)',
          color: 'white',
          padding: '10px',
          borderRadius: '4px',
          zIndex: 100,
          maxWidth: '300px'
        }}>
          <h4 style={{ margin: '0 0 10px 0' }}>當前決策</h4>
          <div style={{ fontSize: '12px', lineHeight: '1.4' }}>
            <div><strong>策略:</strong> {currentDecision.ai_analysis.strategy}</div>
            <div><strong>置信度:</strong> {(currentDecision.ai_analysis.confidence * 100).toFixed(1)}%</div>
            <div><strong>預期改善:</strong> {currentDecision.ai_analysis.expected_improvement.toFixed(1)} dB</div>
            <div><strong>執行結果:</strong> {currentDecision.execution_result.success ? '成功' : '失敗'}</div>
            <div><strong>實際改善:</strong> {currentDecision.execution_result.actual_improvement.toFixed(1)} dB</div>
            <div><strong>推理:</strong> {currentDecision.ai_analysis.reasoning}</div>
          </div>
        </div>
      )}
      
      {/* 性能監控 */}
      <div style={{
        position: 'absolute',
        bottom: '10px',
        right: '10px',
        background: 'rgba(0, 0, 0, 0.6)',
        color: '#aaa',
        padding: '5px',
        borderRadius: '2px',
        fontSize: '10px',
        zIndex: 100
      }}>
        渲染: {renderCount} | 節點: {decisionNodes.length}
      </div>
      
      {/* 主畫布 */}
      <canvas
        ref={canvasRef}
        onClick={handleCanvasClick}
        style={{
          width: '100%',
          height: '100%',
          cursor: 'pointer'
        }}
      />
    </div>
  )
}

export default AIRANDecisionVisualization