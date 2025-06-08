import React, { useEffect, useState, useCallback } from 'react'
import { ViewerProps } from '../../types/viewer'

interface RANDecision {
  decision_id: string
  decision_type: 'beam_optimization' | 'frequency_allocation' | 'power_control' | 'interference_mitigation' | 'handover_trigger'
  affected_cells: string[]
  confidence_level: number
  predicted_improvement: number
  execution_status: 'pending' | 'executing' | 'completed' | 'failed'
  decision_rationale: string[]
  metrics_before: {
    sinr_avg: number
    throughput_mbps: number
    interference_level: number
    user_satisfaction: number
  }
  metrics_after?: {
    sinr_avg: number
    throughput_mbps: number
    interference_level: number
    user_satisfaction: number
  }
  timestamp: string
}

interface AIRANSystemStatus {
  is_active: boolean
  learning_mode: boolean
  model_accuracy: number
  decisions_per_minute: number
  total_optimizations: number
  success_rate: number
  energy_savings_percent: number
  spectral_efficiency_gain: number
}

interface AIRANDecisionData {
  timestamp: string
  scene_id: string
  active_decisions: RANDecision[]
  system_status: AIRANSystemStatus
  network_overview: {
    total_cells: number
    active_optimizations: number
    interference_incidents: number
    coverage_efficiency: number
  }
}

const AIRANDecisionVisualization: React.FC<ViewerProps> = ({
  currentScene,
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar
}) => {
  const [aiRanData, setAIRanData] = useState<AIRANDecisionData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedDecisionType, setSelectedDecisionType] = useState<string>('all')

  const generateMockData = (): AIRANDecisionData => {
    const decisionTypes: RANDecision['decision_type'][] = [
      'beam_optimization',
      'frequency_allocation', 
      'power_control',
      'interference_mitigation',
      'handover_trigger'
    ]
    
    const active_decisions: RANDecision[] = decisionTypes.map((type, index) => {
      const metricsBase = {
        sinr_avg: 8 + Math.random() * 10,
        throughput_mbps: 50 + Math.random() * 100,
        interference_level: 0.2 + Math.random() * 0.5,
        user_satisfaction: 0.6 + Math.random() * 0.3
      }
      
      const improvement = 0.1 + Math.random() * 0.3
      
      return {
        decision_id: `RAN_DEC_${String(index + 1).padStart(3, '0')}`,
        decision_type: type,
        affected_cells: [`CELL_${index + 1}`, `CELL_${index + 5}`],
        confidence_level: 0.75 + Math.random() * 0.25,
        predicted_improvement: improvement,
        execution_status: ['pending', 'executing', 'completed', 'failed'][Math.floor(Math.random() * 4)] as any,
        decision_rationale: [
          `分析${type}性能指標`,
          `識別優化潛力區域`,
          `計算最佳參數配置`,
          `評估系統影響和風險`,
          `生成執行建議`
        ],
        metrics_before: metricsBase,
        metrics_after: {
          sinr_avg: metricsBase.sinr_avg * (1 + improvement * 0.5),
          throughput_mbps: metricsBase.throughput_mbps * (1 + improvement),
          interference_level: metricsBase.interference_level * (1 - improvement * 0.7),
          user_satisfaction: Math.min(0.99, metricsBase.user_satisfaction * (1 + improvement * 0.8))
        },
        timestamp: new Date().toISOString()
      }
    })

    return {
      timestamp: new Date().toISOString(),
      scene_id: currentScene || 'default',
      active_decisions,
      system_status: {
        is_active: true,
        learning_mode: true,
        model_accuracy: 0.94,
        decisions_per_minute: 12.5,
        total_optimizations: 8429,
        success_rate: 0.91,
        energy_savings_percent: 23.7,
        spectral_efficiency_gain: 18.2
      },
      network_overview: {
        total_cells: 24,
        active_optimizations: active_decisions.filter(d => d.execution_status === 'executing').length,
        interference_incidents: 3,
        coverage_efficiency: 0.87
      }
    }
  }

  const refreshData = useCallback(() => {
    console.log('AIRANDecisionVisualization: Starting refresh...')
    setIsLoading(true)
    reportIsLoadingToNavbar(true)
    
    setTimeout(() => {
      console.log('AIRANDecisionVisualization: Generating data...')
      const newData = generateMockData()
      setAIRanData(newData)
      setIsLoading(false)
      reportIsLoadingToNavbar(false)
      
      if (onReportLastUpdateToNavbar) {
        onReportLastUpdateToNavbar(new Date().toISOString())
      }
      console.log('AIRANDecisionVisualization: Data loaded successfully')
    }, 1300)
  }, [onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

  useEffect(() => {
    console.log('AIRANDecisionVisualization: Component mounted, starting initial load...')
    refreshData()
    reportRefreshHandlerToNavbar(refreshData)
  }, [])

  const getDecisionTypeColor = (decisionType: string) => {
    switch (decisionType) {
      case 'beam_optimization': return '#ff6b35'
      case 'frequency_allocation': return '#4ecdc4'
      case 'power_control': return '#45b7d1'
      case 'interference_mitigation': return '#feca57'
      case 'handover_trigger': return '#96ceb4'
      default: return '#95a5a6'
    }
  }

  const getDecisionTypeIcon = (decisionType: string) => {
    switch (decisionType) {
      case 'beam_optimization': return '📡'
      case 'frequency_allocation': return '📊'
      case 'power_control': return '⚡'
      case 'interference_mitigation': return '🛡️'
      case 'handover_trigger': return '🔄'
      default: return '🤖'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#00ff00'
      case 'executing': return '#ffaa00'
      case 'pending': return '#0088ff'
      case 'failed': return '#ff0000'
      default: return '#888888'
    }
  }

  if (isLoading || !aiRanData) {
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
        <div style={{ fontSize: '14px', opacity: 0.7 }}>正在分析 AI-RAN 決策系統</div>
      </div>
    )
  }

  const filteredDecisions = selectedDecisionType === 'all' 
    ? aiRanData.active_decisions
    : aiRanData.active_decisions.filter(d => d.decision_type === selectedDecisionType)

  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      background: '#1a1a1a', 
      color: 'white',
      overflow: 'auto',
      padding: '20px'
    }}>
      {/* 頂部系統狀態 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        <div style={{
          background: 'rgba(0,255,0,0.2)',
          border: '1px solid rgba(0,255,0,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>🤖 AI-RAN 狀態</h3>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {aiRanData.system_status.is_active ? '🟢 運行中' : '🔴 停止'}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(0,150,255,0.2)',
          border: '1px solid rgba(0,150,255,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>🎯 模型準確度</h3>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {(aiRanData.system_status.model_accuracy * 100).toFixed(1)}%
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,150,0,0.2)',
          border: '1px solid rgba(255,150,0,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>⚡ 決策頻率</h3>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {aiRanData.system_status.decisions_per_minute.toFixed(1)}/min
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,0,150,0.2)',
          border: '1px solid rgba(255,0,150,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>✅ 成功率</h3>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {(aiRanData.system_status.success_rate * 100).toFixed(1)}%
          </div>
        </div>

        <div style={{
          background: 'rgba(100,255,100,0.2)',
          border: '1px solid rgba(100,255,100,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>🔋 節能效果</h3>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {aiRanData.system_status.energy_savings_percent.toFixed(1)}%
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,255,100,0.2)',
          border: '1px solid rgba(255,255,100,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>📈 頻譜效率</h3>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            +{aiRanData.system_status.spectral_efficiency_gain.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* 網路概覽 */}
      <div style={{
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 16px 0' }}>📡 網路概覽</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>總基站數</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {aiRanData.network_overview.total_cells}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>進行中優化</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {aiRanData.network_overview.active_optimizations}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>干擾事件</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {aiRanData.network_overview.interference_incidents}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>覆蓋效率</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {(aiRanData.network_overview.coverage_efficiency * 100).toFixed(1)}%
            </div>
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
          <option value="all">全部決策</option>
          <option value="beam_optimization">波束優化</option>
          <option value="frequency_allocation">頻率分配</option>
          <option value="power_control">功率控制</option>
          <option value="interference_mitigation">干擾緩解</option>
          <option value="handover_trigger">換手觸發</option>
        </select>
      </div>

      {/* 決策詳情 */}
      <div>
        <h3 style={{ marginBottom: '16px' }}>🧠 AI-RAN 決策詳情</h3>
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
          gap: '16px'
        }}>
          {filteredDecisions.map((decision) => (
            <div key={decision.decision_id} style={{
              background: 'rgba(255,255,255,0.05)',
              border: `2px solid ${getDecisionTypeColor(decision.decision_type)}`,
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
                  {getDecisionTypeIcon(decision.decision_type)} {decision.decision_id}
                </h4>
                <span style={{
                  background: `${getStatusColor(decision.execution_status)}30`,
                  color: getStatusColor(decision.execution_status),
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  textTransform: 'uppercase'
                }}>
                  {decision.execution_status}
                </span>
              </div>

              <div style={{ fontSize: '14px', marginBottom: '12px' }}>
                <div>決策類型: {decision.decision_type.replace(/_/g, ' ')}</div>
                <div>影響基站: {decision.affected_cells.join(', ')}</div>
                <div>信心度: {(decision.confidence_level * 100).toFixed(1)}%</div>
                <div>預期改善: {(decision.predicted_improvement * 100).toFixed(1)}%</div>
              </div>

              {/* 性能指標對比 */}
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>性能指標對比</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                  <div>
                    <div style={{ opacity: 0.8 }}>執行前</div>
                    <div>SINR: {decision.metrics_before.sinr_avg.toFixed(1)} dB</div>
                    <div>吞吐量: {decision.metrics_before.throughput_mbps.toFixed(0)} Mbps</div>
                    <div>干擾: {(decision.metrics_before.interference_level * 100).toFixed(0)}%</div>
                    <div>滿意度: {(decision.metrics_before.user_satisfaction * 100).toFixed(0)}%</div>
                  </div>
                  {decision.metrics_after && (
                    <div>
                      <div style={{ opacity: 0.8 }}>執行後</div>
                      <div style={{ color: '#00ff00' }}>SINR: {decision.metrics_after.sinr_avg.toFixed(1)} dB</div>
                      <div style={{ color: '#00ff00' }}>吞吐量: {decision.metrics_after.throughput_mbps.toFixed(0)} Mbps</div>
                      <div style={{ color: '#00ff00' }}>干擾: {(decision.metrics_after.interference_level * 100).toFixed(0)}%</div>
                      <div style={{ color: '#00ff00' }}>滿意度: {(decision.metrics_after.user_satisfaction * 100).toFixed(0)}%</div>
                    </div>
                  )}
                </div>
              </div>

              {/* 決策推理過程 */}
              <div style={{ fontSize: '12px', marginBottom: '12px' }}>
                <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>決策推理過程:</div>
                {decision.decision_rationale.map((reason, index) => (
                  <div key={index} style={{ marginLeft: '12px', marginBottom: '2px' }}>
                    {index + 1}. {reason}
                  </div>
                ))}
              </div>

              {/* 信心度條 */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '12px', marginBottom: '4px' }}>決策信心度</div>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  height: '6px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    background: decision.confidence_level > 0.8 ? '#00ff00' : 
                               decision.confidence_level > 0.6 ? '#ffaa00' : '#ff0000',
                    height: '100%',
                    width: `${decision.confidence_level * 100}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>

              <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>
                決策時間: {new Date(decision.timestamp).toLocaleTimeString()}
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
        場景: {aiRanData.scene_id} | 最後更新: {new Date(aiRanData.timestamp).toLocaleString()}
      </div>
    </div>
  )
}

export default AIRANDecisionVisualization