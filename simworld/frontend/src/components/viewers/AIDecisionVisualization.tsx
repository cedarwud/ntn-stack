import React, { useEffect, useState, useCallback } from 'react'
import { ViewerProps } from '../../types/viewer'

interface AIDecisionNode {
  node_id: string
  decision_type: string
  confidence_score: number
  recommended_action: string
  execution_status: string
  execution_priority: string
  input_features: {
    sinr_db: number
    interference_level: number
    channel_quality: number
    traffic_load: number
  }
  reasoning: string[]
  timestamp: string
}

interface AIDecisionData {
  timestamp: string
  scene_id: string
  active_decisions: AIDecisionNode[]
  system_performance: {
    overall_improvement: number
    decisions_made: number
    success_rate: number
    avg_response_time: number
  }
}

const AIDecisionVisualization: React.FC<ViewerProps> = ({
  currentScene,
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar
}) => {
  const [aiDecisionData, setAIDecisionData] = useState<AIDecisionData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedDecisionType, setSelectedDecisionType] = useState<string>('all')

  const generateMockData = (): AIDecisionData => {
    const decisionTypes = [
      'frequency_selection',
      'power_control', 
      'handover',
      'interference_mitigation',
      'resource_allocation'
    ]
    
    const active_decisions: AIDecisionNode[] = decisionTypes.map((type, index) => ({
      node_id: `decision_${index + 1}`,
      decision_type: type,
      confidence_score: 0.7 + Math.random() * 0.3,
      recommended_action: `執行${type.replace(/_/g, ' ')}優化`,
      execution_status: ['pending', 'executing', 'completed', 'failed'][Math.floor(Math.random() * 4)],
      execution_priority: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)],
      input_features: {
        sinr_db: Math.random() * 30 - 10,
        interference_level: Math.random(),
        channel_quality: Math.random(),
        traffic_load: Math.random()
      },
      reasoning: [
        `檢測到${type}需要優化`,
        `分析當前性能指標`,
        `計算最佳調整參數`,
        `評估執行風險和收益`
      ],
      timestamp: new Date().toISOString()
    }))

    return {
      timestamp: new Date().toISOString(),
      scene_id: currentScene || 'default',
      active_decisions,
      system_performance: {
        overall_improvement: 0.23,
        decisions_made: 1247,
        success_rate: 0.87,
        avg_response_time: 45.2
      }
    }
  }

  const refreshData = useCallback(() => {
    console.log('AIDecisionVisualization: Starting refresh...')
    setIsLoading(true)
    reportIsLoadingToNavbar(true)
    
    setTimeout(() => {
      console.log('AIDecisionVisualization: Generating data...')
      const newData = generateMockData()
      setAIDecisionData(newData)
      setIsLoading(false)
      reportIsLoadingToNavbar(false)
      
      if (onReportLastUpdateToNavbar) {
        onReportLastUpdateToNavbar(new Date().toISOString())
      }
      console.log('AIDecisionVisualization: Data loaded successfully')
    }, 1000)
  }, [onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

  useEffect(() => {
    console.log('AIDecisionVisualization: Component mounted, starting initial load...')
    refreshData()
    reportRefreshHandlerToNavbar(refreshData)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#00ff00'
      case 'executing': return '#ffaa00'
      case 'pending': return '#0088ff'
      case 'failed': return '#ff0000'
      default: return '#888888'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#ff4444'
      case 'medium': return '#ffaa44'
      case 'low': return '#44ff44'
      default: return '#888888'
    }
  }

  if (isLoading || !aiDecisionData) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#1a1a1a',
        color: 'white',
        flexDirection: 'column'
      }}>
        <div style={{ fontSize: '18px', marginBottom: '16px' }}>載入中...</div>
        <div style={{ fontSize: '14px', opacity: 0.7 }}>正在分析 AI 決策過程</div>
      </div>
    )
  }

  const filteredDecisions = selectedDecisionType === 'all' 
    ? aiDecisionData.active_decisions
    : aiDecisionData.active_decisions.filter(d => d.decision_type === selectedDecisionType)

  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      background: '#1a1a1a', 
      color: 'white',
      overflow: 'auto',
      padding: '20px'
    }}>
      {/* 頂部統計面板 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        <div style={{
          background: 'rgba(0,255,0,0.2)',
          border: '1px solid rgba(0,255,0,0.5)',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>🎯 整體改善</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {(aiDecisionData.system_performance.overall_improvement * 100).toFixed(1)}%
          </div>
        </div>
        
        <div style={{
          background: 'rgba(0,150,255,0.2)',
          border: '1px solid rgba(0,150,255,0.5)',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>⚡ 已執行決策</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {aiDecisionData.system_performance.decisions_made.toLocaleString()}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,150,0,0.2)',
          border: '1px solid rgba(255,150,0,0.5)',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>✅ 成功率</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {(aiDecisionData.system_performance.success_rate * 100).toFixed(1)}%
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,0,150,0.2)',
          border: '1px solid rgba(255,0,150,0.5)',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>⏱️ 平均響應</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {aiDecisionData.system_performance.avg_response_time.toFixed(1)}ms
          </div>
        </div>
      </div>

      {/* 決策類型過濾器 */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ marginRight: '12px', fontSize: '16px' }}>決策類型篩選:</label>
        <select 
          value={selectedDecisionType}
          onChange={(e) => setSelectedDecisionType(e.target.value)}
          style={{
            background: '#333',
            color: 'white',
            border: '1px solid #555',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '14px'
          }}
        >
          <option value="all">全部類型</option>
          <option value="frequency_selection">頻率選擇</option>
          <option value="power_control">功率控制</option>
          <option value="handover">換手決策</option>
          <option value="interference_mitigation">干擾緩解</option>
          <option value="resource_allocation">資源分配</option>
        </select>
      </div>

      {/* 決策節點 */}
      <div>
        <h3 style={{ marginBottom: '16px' }}>🤖 活躍 AI 決策節點</h3>
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '16px'
        }}>
          {filteredDecisions.map((decision) => (
            <div key={decision.node_id} style={{
              background: 'rgba(255,255,255,0.1)',
              border: `2px solid ${getStatusColor(decision.execution_status)}`,
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '12px'
              }}>
                <h4 style={{ margin: 0, fontSize: '16px' }}>
                  {decision.decision_type.replace(/_/g, ' ').toUpperCase()}
                </h4>
                <span style={{ 
                  background: getPriorityColor(decision.execution_priority),
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}>
                  {decision.execution_priority.toUpperCase()}
                </span>
              </div>

              <div style={{ fontSize: '14px', marginBottom: '12px' }}>
                <div style={{ marginBottom: '4px' }}>
                  <strong>建議動作:</strong> {decision.recommended_action}
                </div>
                <div style={{ marginBottom: '4px' }}>
                  <strong>信心度:</strong> {(decision.confidence_score * 100).toFixed(1)}%
                </div>
                <div>
                  <strong>狀態:</strong> 
                  <span style={{ color: getStatusColor(decision.execution_status), marginLeft: '8px' }}>
                    {decision.execution_status.toUpperCase()}
                  </span>
                </div>
              </div>

              <div style={{ fontSize: '13px', marginBottom: '12px' }}>
                <div style={{ marginBottom: '8px' }}><strong>輸入特徵:</strong></div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                  <div>SINR: {decision.input_features.sinr_db.toFixed(1)}dB</div>
                  <div>干擾: {(decision.input_features.interference_level * 100).toFixed(0)}%</div>
                  <div>通道品質: {(decision.input_features.channel_quality * 100).toFixed(0)}%</div>
                  <div>流量負載: {(decision.input_features.traffic_load * 100).toFixed(0)}%</div>
                </div>
              </div>

              <div style={{ fontSize: '12px', marginBottom: '12px' }}>
                <div style={{ marginBottom: '4px' }}><strong>推理過程:</strong></div>
                {decision.reasoning.map((reason, index) => (
                  <div key={index} style={{ marginLeft: '12px', marginBottom: '2px' }}>
                    {index + 1}. {reason}
                  </div>
                ))}
              </div>

              <div style={{ 
                fontSize: '11px', 
                padding: '8px',
                background: `${getStatusColor(decision.execution_status)}20`,
                borderRadius: '4px',
                textAlign: 'center'
              }}>
                更新時間: {new Date(decision.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 底部時間戳 */}
      <div style={{ 
        marginTop: '30px', 
        textAlign: 'center', 
        fontSize: '12px', 
        opacity: 0.7 
      }}>
        場景: {aiDecisionData.scene_id} | 最後更新: {new Date(aiDecisionData.timestamp).toLocaleString()}
      </div>
    </div>
  )
}

export default AIDecisionVisualization