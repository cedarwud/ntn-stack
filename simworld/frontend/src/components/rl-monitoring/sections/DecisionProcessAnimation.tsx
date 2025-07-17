import React, { useState, useEffect, useRef } from 'react'
import { netstackFetch } from '../../../config/api-config'
import './DecisionProcessAnimation.scss'

interface DecisionProcessAnimationProps {
    selectedSatellite?: string
    onSatelliteSelect?: (satelliteId: string) => void
}

interface DecisionStep {
    step: number
    title: string
    description: string
    factors: {
        elevation: number
        rsrp: number
        rsrq: number
        load: number
        stability: number
    }
    score: number
    selected: boolean
}

interface DecisionProcess {
    timestamp: string
    current_satellite: string
    candidate_satellites: string[]
    decision_steps: DecisionStep[]
    final_decision: string
    decision_reason: string
    confidence: number
    reward: number
}

interface SatelliteInfo {
    id: string
    name: string
    elevation: number
    rsrp: number
    rsrq: number
    load_factor: number
    stability_score: number
}

const DecisionProcessAnimation: React.FC<DecisionProcessAnimationProps> = ({
    selectedSatellite,
    onSatelliteSelect
}) => {
    const [decisionProcess, setDecisionProcess] = useState<DecisionProcess | null>(null)
    const [satellites, setSatellites] = useState<SatelliteInfo[]>([])
    const [isPlaying, setIsPlaying] = useState(false)
    const [currentStep, setCurrentStep] = useState(0)
    const [playbackSpeed, setPlaybackSpeed] = useState(1)
    const [isLoading, setIsLoading] = useState(false)
    const intervalRef = useRef<NodeJS.Timeout>()

    // 獲取決策過程數據
    const fetchDecisionProcess = async () => {
        setIsLoading(true)
        try {
            const response = await netstackFetch('/api/v1/rl/decision-process/latest')
            if (response.ok) {
                const data = await response.json()
                setDecisionProcess(data)
                setCurrentStep(0)
            } else {
                // 生成模擬決策過程
                generateMockDecisionProcess()
            }
        } catch (error) {
            console.error('獲取決策過程失敗:', error)
            generateMockDecisionProcess()
        } finally {
            setIsLoading(false)
        }
    }

    // 生成模擬決策過程
    const generateMockDecisionProcess = () => {
        const mockSatellites = [
            {
                id: 'starlink-1234',
                name: 'Starlink-1234',
                elevation: 45.2,
                rsrp: -85,
                rsrq: -12,
                load_factor: 0.3,
                stability_score: 0.85
            },
            {
                id: 'starlink-5678',
                name: 'Starlink-5678',
                elevation: 38.7,
                rsrp: -90,
                rsrq: -14,
                load_factor: 0.5,
                stability_score: 0.72
            },
            {
                id: 'kuiper-1001',
                name: 'Kuiper-1001',
                elevation: 52.1,
                rsrp: -82,
                rsrq: -10,
                load_factor: 0.7,
                stability_score: 0.91
            }
        ]

        setSatellites(mockSatellites)

        const decisionSteps: DecisionStep[] = mockSatellites.map((sat, index) => ({
            step: index + 1,
            title: `評估 ${sat.name}`,
            description: `分析衛星 ${sat.name} 的各項指標`,
            factors: {
                elevation: sat.elevation / 90, // 正規化到 0-1
                rsrp: (sat.rsrp + 120) / 40, // 正規化到 0-1
                rsrq: (sat.rsrq + 20) / 10, // 正規化到 0-1
                load: 1 - sat.load_factor, // 負載越低越好
                stability: sat.stability_score
            },
            score: calculateScore(sat),
            selected: sat.id === 'kuiper-1001' // 最高分的衛星
        }))

        const mockProcess: DecisionProcess = {
            timestamp: new Date().toISOString(),
            current_satellite: 'starlink-1234',
            candidate_satellites: mockSatellites.map(s => s.id),
            decision_steps: decisionSteps,
            final_decision: 'kuiper-1001',
            decision_reason: '基於仰角 (52.1°)、信號品質 (RSRP: -82 dBm) 和穩定性 (0.91) 的綜合評估',
            confidence: 0.87,
            reward: 75.5
        }

        setDecisionProcess(mockProcess)
    }

    // 計算衛星評分
    const calculateScore = (satellite: SatelliteInfo): number => {
        const weights = {
            elevation: 0.30,
            rsrp: 0.25,
            rsrq: 0.20,
            load: 0.15,
            stability: 0.10
        }

        const normalizedValues = {
            elevation: satellite.elevation / 90,
            rsrp: (satellite.rsrp + 120) / 40,
            rsrq: (satellite.rsrq + 20) / 10,
            load: 1 - satellite.load_factor,
            stability: satellite.stability_score
        }

        return Object.entries(weights).reduce((score, [key, weight]) => {
            const value = normalizedValues[key as keyof typeof normalizedValues]
            return score + (value * weight * 100)
        }, 0)
    }

    // 播放動畫
    const startAnimation = () => {
        setIsPlaying(true)
        setCurrentStep(0)
        
        intervalRef.current = setInterval(() => {
            setCurrentStep(prev => {
                if (!decisionProcess || prev >= decisionProcess.decision_steps.length - 1) {
                    setIsPlaying(false)
                    return prev
                }
                return prev + 1
            })
        }, 2000 / playbackSpeed)
    }

    // 停止動畫
    const stopAnimation = () => {
        setIsPlaying(false)
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
        }
    }

    // 重置動畫
    const resetAnimation = () => {
        stopAnimation()
        setCurrentStep(0)
    }

    // 清理定時器
    useEffect(() => {
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [])

    // 初始化
    useEffect(() => {
        fetchDecisionProcess()
        const interval = setInterval(fetchDecisionProcess, 10000)
        return () => clearInterval(interval)
    }, [])

    // 渲染決策因素條形圖
    const renderFactorBar = (label: string, value: number, weight: number) => {
        const percentage = value * 100
        const weightedScore = value * weight * 100
        
        return (
            <div key={label} className="factor-bar">
                <div className="factor-label">
                    <span>{label}</span>
                    <span className="factor-weight">({(weight * 100).toFixed(0)}%)</span>
                </div>
                <div className="factor-progress">
                    <div 
                        className="factor-fill"
                        style={{ width: `${percentage}%` }}
                    />
                    <div className="factor-value">{weightedScore.toFixed(1)}</div>
                </div>
            </div>
        )
    }

    if (isLoading) {
        return (
            <div className="decision-process-loading">
                <div className="loading-spinner">🧠</div>
                <div>正在加載決策過程...</div>
            </div>
        )
    }

    if (!decisionProcess) {
        return (
            <div className="decision-process-error">
                <div className="error-icon">❌</div>
                <div>無法加載決策過程數據</div>
                <button onClick={fetchDecisionProcess}>重新加載</button>
            </div>
        )
    }

    const currentStepData = decisionProcess.decision_steps[currentStep]

    return (
        <div className="decision-process-animation">
            <div className="animation-header">
                <h3>🎯 LEO 衛星換手決策過程</h3>
                <div className="animation-controls">
                    <button 
                        onClick={startAnimation}
                        disabled={isPlaying}
                        className="control-btn play-btn"
                    >
                        ▶️ 播放
                    </button>
                    <button 
                        onClick={stopAnimation}
                        disabled={!isPlaying}
                        className="control-btn pause-btn"
                    >
                        ⏸️ 暫停
                    </button>
                    <button 
                        onClick={resetAnimation}
                        className="control-btn reset-btn"
                    >
                        🔄 重置
                    </button>
                    <div className="speed-control">
                        <label>速度:</label>
                        <select 
                            value={playbackSpeed} 
                            onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                        >
                            <option value={0.5}>0.5x</option>
                            <option value={1}>1x</option>
                            <option value={2}>2x</option>
                            <option value={3}>3x</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="animation-content">
                <div className="decision-timeline">
                    <div className="timeline-header">
                        <h4>決策時間軸</h4>
                        <div className="timeline-info">
                            步驟 {currentStep + 1} / {decisionProcess.decision_steps.length}
                        </div>
                    </div>
                    
                    <div className="timeline-steps">
                        {decisionProcess.decision_steps.map((step, index) => (
                            <div 
                                key={index}
                                className={`timeline-step ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
                                onClick={() => setCurrentStep(index)}
                            >
                                <div className="step-number">{step.step}</div>
                                <div className="step-title">{step.title}</div>
                                <div className="step-score">{step.score.toFixed(1)}</div>
                                {step.selected && <div className="step-selected">✓</div>}
                            </div>
                        ))}
                    </div>
                </div>

                <div className="decision-details">
                    <div className="current-step-info">
                        <h4>{currentStepData.title}</h4>
                        <p>{currentStepData.description}</p>
                        <div className="step-score-display">
                            綜合評分: <span className="score-value">{currentStepData.score.toFixed(1)}</span>
                        </div>
                    </div>

                    <div className="decision-factors">
                        <h5>決策因素分析</h5>
                        <div className="factors-grid">
                            {renderFactorBar('仰角', currentStepData.factors.elevation, 0.30)}
                            {renderFactorBar('RSRP', currentStepData.factors.rsrp, 0.25)}
                            {renderFactorBar('RSRQ', currentStepData.factors.rsrq, 0.20)}
                            {renderFactorBar('負載', currentStepData.factors.load, 0.15)}
                            {renderFactorBar('穩定性', currentStepData.factors.stability, 0.10)}
                        </div>
                    </div>

                    {currentStep === decisionProcess.decision_steps.length - 1 && (
                        <div className="final-decision">
                            <h5>🎉 最終決策</h5>
                            <div className="decision-result">
                                <div className="selected-satellite">
                                    選中衛星: <strong>{decisionProcess.final_decision}</strong>
                                </div>
                                <div className="decision-reason">
                                    {decisionProcess.decision_reason}
                                </div>
                                <div className="decision-metrics">
                                    <div className="metric">
                                        <span>信心度:</span>
                                        <span className="metric-value">{(decisionProcess.confidence * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="metric">
                                        <span>獎勵:</span>
                                        <span className="metric-value">{decisionProcess.reward.toFixed(1)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="satellite-comparison">
                    <h5>衛星比較</h5>
                    <div className="satellites-grid">
                        {satellites.map((satellite) => (
                            <div 
                                key={satellite.id}
                                className={`satellite-card ${satellite.id === decisionProcess.final_decision ? 'selected' : ''}`}
                                onClick={() => onSatelliteSelect?.(satellite.id)}
                            >
                                <div className="satellite-name">{satellite.name}</div>
                                <div className="satellite-metrics">
                                    <div className="metric">
                                        <span>仰角:</span>
                                        <span>{satellite.elevation.toFixed(1)}°</span>
                                    </div>
                                    <div className="metric">
                                        <span>RSRP:</span>
                                        <span>{satellite.rsrp.toFixed(1)} dBm</span>
                                    </div>
                                    <div className="metric">
                                        <span>負載:</span>
                                        <span>{(satellite.load_factor * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="metric">
                                        <span>穩定性:</span>
                                        <span>{(satellite.stability_score * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                                <div className="satellite-score">
                                    評分: {calculateScore(satellite).toFixed(1)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default DecisionProcessAnimation