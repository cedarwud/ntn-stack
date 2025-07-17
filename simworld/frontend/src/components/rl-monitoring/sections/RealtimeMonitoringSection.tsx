/**
 * 實時監控 - LEO衛星切換性能實時追蹤
 * 根據 @ch.md 設計的4個監控內容：
 * A. 核心切換指標
 * B. 信號品質趨勢
 * C. 決策過程可視化
 * D. 訓練狀態監控
 */

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { netstackFetch, simworldFetch } from '../../../config/api-config'
import './RealtimeMonitoringSection.scss'

interface RealtimeMonitoringProps {
    data: unknown
    onRefresh?: () => void
}

interface HandoverMetrics {
    success_rate: number
    average_delay: number
    call_drop_rate: number
    pingpong_rate: number
    total_handovers: number
    successful_handovers: number
}

interface SignalQuality {
    rsrp: number
    rsrq: number
    sinr: number
    timestamp: number
}

interface CandidateSatellite {
    id: string
    name: string
    elevation: number
    azimuth: number
    rsrp: number
    rsrq: number
    sinr: number
    load_factor: number
    q_value: number
    selection_probability: number
}

interface DecisionProcess {
    current_satellite: string
    candidate_satellites: CandidateSatellite[]
    selected_satellite: string
    decision_reason: string
    q_values: Record<string, number>
    action_values: number[]
    confidence_score: number
}

interface TrainingMetrics {
    current_episode: number
    total_episodes: number
    current_reward: number
    average_reward: number
    epsilon: number
    loss: number
    learning_rate: number
    exploration_ratio: number
}

interface RealtimeData {
    handover_metrics: HandoverMetrics
    signal_quality: SignalQuality[]
    decision_process: DecisionProcess
    training_metrics: TrainingMetrics
    timestamp: number
}

const RealtimeMonitoringSection: React.FC<RealtimeMonitoringProps> = ({ 
    data: _data, 
    onRefresh: _onRefresh 
}) => {
    const [realtimeData, setRealtimeData] = useState<RealtimeData | null>(null)
    const [isConnected, setIsConnected] = useState(false)
    const [activeView, setActiveView] = useState<string>('handover')
    const [signalHistory, setSignalHistory] = useState<SignalQuality[]>([])
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const wsRef = useRef<WebSocket | null>(null)
    
    // WebSocket 連接管理
    const connectWebSocket = useCallback(() => {
        try {
            const ws = new WebSocket('ws://localhost:8080/ws/rl-monitoring')
            wsRef.current = ws
            
            ws.onopen = () => {
                console.log('✅ WebSocket 連接成功')
                setIsConnected(true)
            }
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data) as RealtimeData
                    setRealtimeData(data)
                    
                    // 更新信號歷史
                    if (data.signal_quality) {
                        setSignalHistory(prev => {
                            const updated = [...prev, ...data.signal_quality]
                            return updated.slice(-100) // 保留最近100個數據點
                        })
                    }
                } catch (error) {
                    console.error('解析 WebSocket 數據失敗:', error)
                }
            }
            
            ws.onclose = () => {
                console.log('❌ WebSocket 連接關閉')
                setIsConnected(false)
                // 5秒後重新連接
                setTimeout(connectWebSocket, 5000)
            }
            
            ws.onerror = (error) => {
                console.error('WebSocket 連接錯誤:', error)
                setIsConnected(false)
            }
        } catch (error) {
            console.error('建立 WebSocket 連接失敗:', error)
            setIsConnected(false)
        }
    }, [])
    
    // 獲取模擬數據
    const fetchMockData = useCallback(async () => {
        try {
            const mockData: RealtimeData = {
                handover_metrics: {
                    success_rate: 0.95 + Math.random() * 0.04,
                    average_delay: 80 + Math.random() * 40,
                    call_drop_rate: 0.01 + Math.random() * 0.02,
                    pingpong_rate: 0.05 + Math.random() * 0.03,
                    total_handovers: 1250 + Math.floor(Math.random() * 50),
                    successful_handovers: 1180 + Math.floor(Math.random() * 50)
                },
                signal_quality: [{
                    rsrp: -85 + Math.random() * 20,
                    rsrq: -12 + Math.random() * 8,
                    sinr: 15 + Math.random() * 10,
                    timestamp: Date.now()
                }],
                decision_process: {
                    current_satellite: 'starlink-1234',
                    candidate_satellites: [
                        {
                            id: 'starlink-1234',
                            name: 'Starlink-1234',
                            elevation: 45.2,
                            azimuth: 120.5,
                            rsrp: -82,
                            rsrq: -10,
                            sinr: 18,
                            load_factor: 0.3,
                            q_value: 0.85,
                            selection_probability: 0.65
                        },
                        {
                            id: 'starlink-5678',
                            name: 'Starlink-5678',
                            elevation: 38.7,
                            azimuth: 210.3,
                            rsrp: -90,
                            rsrq: -14,
                            sinr: 12,
                            load_factor: 0.5,
                            q_value: 0.72,
                            selection_probability: 0.25
                        }
                    ],
                    selected_satellite: 'starlink-1234',
                    decision_reason: '最高 Q 值且信號品質優良',
                    q_values: {
                        'starlink-1234': 0.85,
                        'starlink-5678': 0.72
                    },
                    action_values: [0.85, 0.72, 0.65, 0.58],
                    confidence_score: 0.92
                },
                training_metrics: {
                    current_episode: 450 + Math.floor(Math.random() * 10),
                    total_episodes: 1000,
                    current_reward: 45.6 + Math.random() * 20,
                    average_reward: 42.8 + Math.random() * 5,
                    epsilon: 0.1 + Math.random() * 0.1,
                    loss: 0.05 + Math.random() * 0.03,
                    learning_rate: 0.001,
                    exploration_ratio: 0.15 + Math.random() * 0.1
                },
                timestamp: Date.now()
            }
            
            setRealtimeData(mockData)
            setSignalHistory(prev => {
                const updated = [...prev, ...mockData.signal_quality]
                return updated.slice(-100)
            })
        } catch (error) {
            console.error('獲取模擬數據失敗:', error)
        }
    }, [])
    
    // 繪製信號品質趨勢圖
    const drawSignalChart = useCallback(() => {
        const canvas = canvasRef.current
        if (!canvas || signalHistory.length === 0) return
        
        const ctx = canvas.getContext('2d')
        if (!ctx) return
        
        canvas.width = 600
        canvas.height = 200
        
        // 清空畫布
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        
        // 繪製背景
        ctx.fillStyle = '#1a1a2e'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        
        const margin = 40
        const chartWidth = canvas.width - 2 * margin
        const chartHeight = canvas.height - 2 * margin
        
        // 繪製座標軸
        ctx.strokeStyle = '#333'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(margin, margin)
        ctx.lineTo(margin, canvas.height - margin)
        ctx.lineTo(canvas.width - margin, canvas.height - margin)
        ctx.stroke()
        
        // 繪製網格
        ctx.strokeStyle = '#2a2a3e'
        ctx.lineWidth = 1
        for (let i = 0; i <= 5; i++) {
            const y = margin + (i / 5) * chartHeight
            ctx.beginPath()
            ctx.moveTo(margin, y)
            ctx.lineTo(canvas.width - margin, y)
            ctx.stroke()
        }
        
        // 繪製RSRP曲線
        if (signalHistory.length > 1) {
            const rsrpValues = signalHistory.map(s => s.rsrp)
            const minRsrp = Math.min(...rsrpValues)
            const maxRsrp = Math.max(...rsrpValues)
            const rsrpRange = maxRsrp - minRsrp || 1
            
            ctx.strokeStyle = '#4fc3f7'
            ctx.lineWidth = 2
            ctx.beginPath()
            
            signalHistory.forEach((signal, index) => {
                const x = margin + (index / (signalHistory.length - 1)) * chartWidth
                const y = canvas.height - margin - ((signal.rsrp - minRsrp) / rsrpRange) * chartHeight
                
                if (index === 0) {
                    ctx.moveTo(x, y)
                } else {
                    ctx.lineTo(x, y)
                }
            })
            
            ctx.stroke()
        }
        
        // 繪製標籤
        ctx.fillStyle = '#fff'
        ctx.font = '12px Arial'
        ctx.fillText('RSRP (dBm)', margin, margin - 10)
        
    }, [signalHistory])
    
    // 初始化連接
    useEffect(() => {
        connectWebSocket()
        
        // 如果WebSocket連接失敗，使用模擬數據
        const mockDataInterval = setInterval(() => {
            if (!isConnected) {
                fetchMockData()
            }
        }, 2000)
        
        return () => {
            if (wsRef.current) {
                wsRef.current.close()
            }
            clearInterval(mockDataInterval)
        }
    }, [connectWebSocket, fetchMockData, isConnected])
    
    // 繪製圖表
    useEffect(() => {
        if (activeView === 'signal') {
            drawSignalChart()
        }
    }, [activeView, drawSignalChart])
    
    if (!realtimeData) {
        return (
            <div className="realtime-monitoring-loading">
                <div className="loading-spinner">📡</div>
                <div>正在連接實時監控...</div>
            </div>
        )
    }
    
    return (
        <div className="realtime-monitoring-section">
            <div className="section-header">
                <h2>📊 實時監控</h2>
                <div className="connection-status">
                    <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
                    <span>{isConnected ? 'WebSocket 已連接' : '使用模擬數據'}</span>
                </div>
            </div>
            
            <div className="monitoring-tabs">
                <div className="tab-nav">
                    <button 
                        className={`tab-btn ${activeView === 'handover' ? 'active' : ''}`}
                        onClick={() => setActiveView('handover')}
                    >
                        🔄 切換指標
                    </button>
                    <button 
                        className={`tab-btn ${activeView === 'signal' ? 'active' : ''}`}
                        onClick={() => setActiveView('signal')}
                    >
                        📶 信號品質
                    </button>
                    <button 
                        className={`tab-btn ${activeView === 'decision' ? 'active' : ''}`}
                        onClick={() => setActiveView('decision')}
                    >
                        🎯 決策過程
                    </button>
                    <button 
                        className={`tab-btn ${activeView === 'training' ? 'active' : ''}`}
                        onClick={() => setActiveView('training')}
                    >
                        🧠 訓練狀態
                    </button>
                </div>
                
                <div className="tab-content">
                    {activeView === 'handover' && (
                        <div className="handover-metrics">
                            <h3>🔄 核心切換指標</h3>
                            <div className="metrics-grid">
                                <div className="metric-card">
                                    <div className="metric-header">
                                        <span className="metric-icon">✅</span>
                                        <span className="metric-label">切換成功率</span>
                                    </div>
                                    <div className="metric-value">
                                        {(realtimeData.handover_metrics.success_rate * 100).toFixed(1)}%
                                    </div>
                                    <div className="metric-trend">
                                        <span className="trend-indicator trend-up">↗️</span>
                                        <span>+0.2% vs 上次</span>
                                    </div>
                                </div>
                                
                                <div className="metric-card">
                                    <div className="metric-header">
                                        <span className="metric-icon">⏱️</span>
                                        <span className="metric-label">平均延遲</span>
                                    </div>
                                    <div className="metric-value">
                                        {realtimeData.handover_metrics.average_delay.toFixed(0)}ms
                                    </div>
                                    <div className="metric-trend">
                                        <span className="trend-indicator trend-down">↘️</span>
                                        <span>-5ms vs 上次</span>
                                    </div>
                                </div>
                                
                                <div className="metric-card">
                                    <div className="metric-header">
                                        <span className="metric-icon">📞</span>
                                        <span className="metric-label">掉話率</span>
                                    </div>
                                    <div className="metric-value">
                                        {(realtimeData.handover_metrics.call_drop_rate * 100).toFixed(2)}%
                                    </div>
                                    <div className="metric-trend">
                                        <span className="trend-indicator trend-stable">➡️</span>
                                        <span>穩定</span>
                                    </div>
                                </div>
                                
                                <div className="metric-card">
                                    <div className="metric-header">
                                        <span className="metric-icon">🏓</span>
                                        <span className="metric-label">乒乓切換率</span>
                                    </div>
                                    <div className="metric-value">
                                        {(realtimeData.handover_metrics.pingpong_rate * 100).toFixed(1)}%
                                    </div>
                                    <div className="metric-trend">
                                        <span className="trend-indicator trend-down">↘️</span>
                                        <span>-0.5% vs 上次</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="handover-summary">
                                <div className="summary-item">
                                    <span className="summary-label">總切換次數:</span>
                                    <span className="summary-value">{realtimeData.handover_metrics.total_handovers}</span>
                                </div>
                                <div className="summary-item">
                                    <span className="summary-label">成功切換:</span>
                                    <span className="summary-value">{realtimeData.handover_metrics.successful_handovers}</span>
                                </div>
                            </div>
                        </div>
                    )}
                    
                    {activeView === 'signal' && (
                        <div className="signal-quality">
                            <h3>📶 信號品質趨勢</h3>
                            <div className="signal-chart">
                                <canvas ref={canvasRef} className="chart-canvas" />
                            </div>
                            <div className="current-signal">
                                <h4>當前信號品質</h4>
                                <div className="signal-metrics">
                                    <div className="signal-item">
                                        <span className="signal-label">RSRP:</span>
                                        <span className="signal-value">{realtimeData.signal_quality[0]?.rsrp.toFixed(1)} dBm</span>
                                    </div>
                                    <div className="signal-item">
                                        <span className="signal-label">RSRQ:</span>
                                        <span className="signal-value">{realtimeData.signal_quality[0]?.rsrq.toFixed(1)} dB</span>
                                    </div>
                                    <div className="signal-item">
                                        <span className="signal-label">SINR:</span>
                                        <span className="signal-value">{realtimeData.signal_quality[0]?.sinr.toFixed(1)} dB</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    
                    {activeView === 'decision' && (
                        <div className="decision-process">
                            <h3>🎯 決策過程可視化</h3>
                            <div className="current-decision">
                                <div className="decision-header">
                                    <span className="selected-satellite">選擇衛星: {realtimeData.decision_process.selected_satellite}</span>
                                    <span className="confidence-score">置信度: {(realtimeData.decision_process.confidence_score * 100).toFixed(1)}%</span>
                                </div>
                                <div className="decision-reason">
                                    <strong>決策理由:</strong> {realtimeData.decision_process.decision_reason}
                                </div>
                            </div>
                            
                            <div className="candidate-satellites">
                                <h4>候選衛星</h4>
                                <div className="satellites-list">
                                    {realtimeData.decision_process.candidate_satellites.map((satellite) => (
                                        <div key={satellite.id} className={`satellite-item ${satellite.id === realtimeData.decision_process.selected_satellite ? 'selected' : ''}`}>
                                            <div className="satellite-header">
                                                <span className="satellite-name">{satellite.name}</span>
                                                <span className="satellite-probability">{(satellite.selection_probability * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="satellite-metrics">
                                                <div className="metric-pair">
                                                    <span>仰角: {satellite.elevation.toFixed(1)}°</span>
                                                    <span>RSRP: {satellite.rsrp.toFixed(1)} dBm</span>
                                                </div>
                                                <div className="metric-pair">
                                                    <span>負載: {(satellite.load_factor * 100).toFixed(0)}%</span>
                                                    <span>Q值: {satellite.q_value.toFixed(2)}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                    
                    {activeView === 'training' && (
                        <div className="training-status">
                            <h3>🧠 訓練狀態監控</h3>
                            <div className="training-progress">
                                <div className="progress-bar">
                                    <div 
                                        className="progress-fill"
                                        style={{ 
                                            width: `${(realtimeData.training_metrics.current_episode / realtimeData.training_metrics.total_episodes) * 100}%` 
                                        }}
                                    />
                                </div>
                                <div className="progress-text">
                                    回合 {realtimeData.training_metrics.current_episode} / {realtimeData.training_metrics.total_episodes}
                                </div>
                            </div>
                            
                            <div className="training-metrics">
                                <div className="metric-row">
                                    <div className="metric-item">
                                        <span className="metric-label">當前獎勵:</span>
                                        <span className="metric-value">{realtimeData.training_metrics.current_reward.toFixed(2)}</span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">平均獎勵:</span>
                                        <span className="metric-value">{realtimeData.training_metrics.average_reward.toFixed(2)}</span>
                                    </div>
                                </div>
                                <div className="metric-row">
                                    <div className="metric-item">
                                        <span className="metric-label">探索率:</span>
                                        <span className="metric-value">{(realtimeData.training_metrics.epsilon * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">損失:</span>
                                        <span className="metric-value">{realtimeData.training_metrics.loss.toFixed(4)}</span>
                                    </div>
                                </div>
                                <div className="metric-row">
                                    <div className="metric-item">
                                        <span className="metric-label">學習率:</span>
                                        <span className="metric-value">{realtimeData.training_metrics.learning_rate.toFixed(4)}</span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">探索比例:</span>
                                        <span className="metric-value">{(realtimeData.training_metrics.exploration_ratio * 100).toFixed(1)}%</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default RealtimeMonitoringSection