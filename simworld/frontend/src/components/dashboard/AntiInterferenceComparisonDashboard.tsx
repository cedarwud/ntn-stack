import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useWebSocket } from '../../hooks/useWebSocket'

interface MetricComparison {
  metric: string
  beforeValue: number
  afterValue: number
  improvement: number
  improvementPercent: number
  unit: string
  category: 'performance' | 'interference' | 'quality'
}

interface AIRANDecision {
  timestamp: number
  decisionType: 'frequency_hop' | 'power_control' | 'beamforming' | 'channel_switch'
  triggerCondition: string
  executionTime: number
  effectiveness: number
  affectedUEs: string[]
}

interface InterferenceEvent {
  id: string
  timestamp: number
  sourceType: string
  targetUE: string
  detectedSINR: number
  mitigatedSINR: number
  mitigationMethod: string
  responseTime: number
}

interface DashboardData {
  metricComparisons: MetricComparison[]
  airanDecisions: AIRANDecision[]
  interferenceEvents: InterferenceEvent[]
  summaryStats: {
    totalInterferenceEvents: number
    averageResponseTime: number
    averageImprovement: number
    systemEfficiency: number
  }
}

const AntiInterferenceComparisonDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    metricComparisons: [],
    airanDecisions: [],
    interferenceEvents: [],
    summaryStats: {
      totalInterferenceEvents: 0,
      averageResponseTime: 0,
      averageImprovement: 0,
      systemEfficiency: 0
    }
  })
  
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h')
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'performance' | 'interference' | 'quality'>('all')
  const [realTimeEnabled, setRealTimeEnabled] = useState(true)
  const [showDetails, setShowDetails] = useState(false)

  const { isConnected, sendMessage } = useWebSocket({
    url: 'ws://localhost:8080/ws/anti-interference-metrics',
    enableReconnect: realTimeEnabled,
    onMessage: handleWebSocketMessage,
  })

  function handleWebSocketMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data)
      
      switch (data.type) {
        case 'metric_comparison_update':
          setDashboardData(prev => ({
            ...prev,
            metricComparisons: data.comparisons
          }))
          break
          
        case 'airan_decision':
          setDashboardData(prev => ({
            ...prev,
            airanDecisions: [data.decision, ...prev.airanDecisions.slice(0, 99)]
          }))
          break
          
        case 'interference_event':
          setDashboardData(prev => ({
            ...prev,
            interferenceEvents: [data.event, ...prev.interferenceEvents.slice(0, 99)]
          }))
          break
          
        case 'summary_stats':
          setDashboardData(prev => ({
            ...prev,
            summaryStats: data.stats
          }))
          break
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }

  const filteredMetrics = useMemo(() => {
    if (selectedCategory === 'all') {
      return dashboardData.metricComparisons
    }
    return dashboardData.metricComparisons.filter(metric => metric.category === selectedCategory)
  }, [dashboardData.metricComparisons, selectedCategory])

  const fetchComparisonData = useCallback(async () => {
    try {
      const response = await fetch(`/api/anti-interference/comparison?timeRange=${selectedTimeRange}`)
      const data = await response.json()
      setDashboardData(data)
    } catch (error) {
      console.error('Error fetching comparison data:', error)
    }
  }, [selectedTimeRange])

  useEffect(() => {
    fetchComparisonData()
    
    if (realTimeEnabled && isConnected) {
      sendMessage(JSON.stringify({
        type: 'subscribe_comparison_metrics',
        timeRange: selectedTimeRange
      }))
    }
  }, [selectedTimeRange, realTimeEnabled, isConnected, fetchComparisonData, sendMessage])

  const getImprovementColor = (improvement: number) => {
    if (improvement > 20) return '#4CAF50'
    if (improvement > 10) return '#8BC34A'
    if (improvement > 0) return '#CDDC39'
    if (improvement > -10) return '#FF9800'
    return '#F44336'
  }

  const getDecisionTypeIcon = (type: string) => {
    switch (type) {
      case 'frequency_hop': return '🎯'
      case 'power_control': return '⚡'
      case 'beamforming': return '📡'
      case 'channel_switch': return '🔄'
      default: return '🤖'
    }
  }

  const formatValue = (value: number, unit: string) => {
    if (unit === '%') return `${value.toFixed(1)}%`
    if (unit === 'dB') return `${value.toFixed(2)} dB`
    if (unit === 'ms') return `${value.toFixed(1)} ms`
    if (unit === 'Mbps') return `${value.toFixed(1)} Mbps`
    return `${value.toFixed(2)} ${unit}`
  }

  return (
    <div className="anti-interference-dashboard">
      <div className="dashboard-header">
        <h2>AI-RAN Anti-Interference Effects Comparison Dashboard</h2>
        <div className="dashboard-controls">
          <div className="time-range-selector">
            <label>Time Range:</label>
            <select 
              value={selectedTimeRange} 
              onChange={(e) => setSelectedTimeRange(e.target.value as any)}
            >
              <option value="1h">Last 1 Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </select>
          </div>
          
          <div className="category-filter">
            <label>Category:</label>
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value as any)}
            >
              <option value="all">All Metrics</option>
              <option value="performance">Performance</option>
              <option value="interference">Interference</option>
              <option value="quality">Quality</option>
            </select>
          </div>
          
          <button
            className={`real-time-toggle ${realTimeEnabled ? 'active' : ''}`}
            onClick={() => setRealTimeEnabled(!realTimeEnabled)}
          >
            {realTimeEnabled ? '🔴 Live' : '⏸️ Paused'}
          </button>
          
          <button
            className={`details-toggle ${showDetails ? 'active' : ''}`}
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
      </div>

      <div className="summary-stats">
        <div className="stat-card">
          <h3>Total Interference Events</h3>
          <div className="stat-value">{dashboardData.summaryStats.totalInterferenceEvents}</div>
        </div>
        <div className="stat-card">
          <h3>Avg Response Time</h3>
          <div className="stat-value">{dashboardData.summaryStats.averageResponseTime.toFixed(1)} ms</div>
        </div>
        <div className="stat-card">
          <h3>Avg Improvement</h3>
          <div className="stat-value" style={{ color: getImprovementColor(dashboardData.summaryStats.averageImprovement) }}>
            +{dashboardData.summaryStats.averageImprovement.toFixed(1)}%
          </div>
        </div>
        <div className="stat-card">
          <h3>System Efficiency</h3>
          <div className="stat-value">{dashboardData.summaryStats.systemEfficiency.toFixed(1)}%</div>
        </div>
      </div>

      <div className="metrics-comparison-grid">
        <div className="metrics-section">
          <h3>Performance Metrics Comparison</h3>
          <div className="metrics-table">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Before AI-RAN</th>
                  <th>After AI-RAN</th>
                  <th>Improvement</th>
                  <th>Impact</th>
                </tr>
              </thead>
              <tbody>
                {filteredMetrics.map((metric, index) => (
                  <tr key={index} className={`metric-row ${metric.category}`}>
                    <td className="metric-name">{metric.metric}</td>
                    <td className="before-value">{formatValue(metric.beforeValue, metric.unit)}</td>
                    <td className="after-value">{formatValue(metric.afterValue, metric.unit)}</td>
                    <td className="improvement" style={{ color: getImprovementColor(metric.improvementPercent) }}>
                      {metric.improvement > 0 ? '+' : ''}{formatValue(metric.improvement, metric.unit)}
                    </td>
                    <td className="improvement-percent" style={{ color: getImprovementColor(metric.improvementPercent) }}>
                      {metric.improvementPercent > 0 ? '+' : ''}{metric.improvementPercent.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {showDetails && (
          <>
            <div className="airan-decisions-section">
              <h3>Recent AI-RAN Decisions</h3>
              <div className="decisions-list">
                {dashboardData.airanDecisions.slice(0, 10).map((decision, index) => (
                  <div key={index} className="decision-item">
                    <div className="decision-header">
                      <span className="decision-icon">{getDecisionTypeIcon(decision.decisionType)}</span>
                      <span className="decision-type">{decision.decisionType.replace('_', ' ').toUpperCase()}</span>
                      <span className="decision-time">{new Date(decision.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="decision-details">
                      <div className="decision-trigger">Trigger: {decision.triggerCondition}</div>
                      <div className="decision-metrics">
                        <span>Execution: {decision.executionTime}ms</span>
                        <span>Effectiveness: {(decision.effectiveness * 100).toFixed(1)}%</span>
                        <span>Affected UEs: {decision.affectedUEs.length}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="interference-events-section">
              <h3>Interference Events & Mitigation</h3>
              <div className="events-list">
                {dashboardData.interferenceEvents.slice(0, 10).map((event, index) => (
                  <div key={event.id} className="event-item">
                    <div className="event-header">
                      <span className="event-id">#{event.id}</span>
                      <span className="event-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
                      <span className="event-source">{event.sourceType}</span>
                    </div>
                    <div className="event-details">
                      <div className="event-target">Target UE: {event.targetUE}</div>
                      <div className="sinr-comparison">
                        <span className="before-sinr">Before: {event.detectedSINR.toFixed(1)} dB</span>
                        <span className="after-sinr">After: {event.mitigatedSINR.toFixed(1)} dB</span>
                        <span className="sinr-improvement" style={{ color: getImprovementColor((event.mitigatedSINR - event.detectedSINR) / event.detectedSINR * 100) }}>
                          +{(event.mitigatedSINR - event.detectedSINR).toFixed(1)} dB
                        </span>
                      </div>
                      <div className="mitigation-info">
                        <span>Method: {event.mitigationMethod}</span>
                        <span>Response: {event.responseTime}ms</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      <div className="dashboard-footer">
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
          <span className="last-update">
            Last updated: {new Date().toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  )
}

export default AntiInterferenceComparisonDashboard