import React, { useState, useEffect, useCallback } from 'react'
import { netstackFetch, simworldFetch } from '../../../config/api-config'
import './TrainingControlCenterSection.scss'

interface TrainingControlCenterProps {
    data: unknown
    onRefresh?: () => void
}

interface SatelliteData {
    id: string
    name: string
    elevation: number
    azimuth: number
    range: number
    rsrp: number
    rsrq: number
    sinr: number
    load_factor: number
    data_quality: 'real' | 'historical' | 'simulated'
}

interface TrainingProgress {
    current_episode: number
    total_episodes: number
    current_reward: number
    average_reward: number
    selected_satellite: string
    decision_reason: string
    algorithm: string
    training_active: boolean
    // 新增：訓練狀態字段
    epsilon: number
    learning_rate: number
    loss: number
    q_value: number
    success_rate: number
}

interface DecisionFactors {
    elevation_weight: number
    rsrp_weight: number
    rsrq_weight: number
    load_weight: number
    stability_weight: number
}

const TrainingControlCenterSection: React.FC<TrainingControlCenterProps> = ({
    data: _data,
    onRefresh,
}) => {
    const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('dqn')
    const [isTraining, setIsTraining] = useState(false)
    const [trainingProgress, setTrainingProgress] = useState<TrainingProgress | null>(null)
    const [visibleSatellites, setVisibleSatellites] = useState<SatelliteData[]>([])
    const [isControlling, setIsControlling] = useState(false)
    
    // 新增：訓練參數配置
    const [trainingEpisodes, setTrainingEpisodes] = useState<number>(1000)
    const [maxStepsPerEpisode, setMaxStepsPerEpisode] = useState<number>(200)
    const [trainingSpeed, setTrainingSpeed] = useState<string>('normal')
    const [saveInterval, setSaveInterval] = useState<number>(100)
    
    // 新增：環境配置
    const [scenarioType, setScenarioType] = useState<string>('urban')
    const [constellationType, setConstellationType] = useState<string>('mixed')
    const [dataSource, setDataSource] = useState<string>('real_tle')
    const [mobilitySpeed, setMobilitySpeed] = useState<string>('static')
    const [totalSatellites, setTotalSatellites] = useState<number>(0)
    
    const [decisionFactors, setDecisionFactors] = useState<DecisionFactors>({
        elevation_weight: 0.30,
        rsrp_weight: 0.25,
        rsrq_weight: 0.20,
        load_weight: 0.15,
        stability_weight: 0.10,
    })

    // 數據品質分級函數
    const getDataQuality = (satellite: Record<string, unknown>): 'real' | 'historical' | 'simulated' => {
        if (satellite.tle_data && satellite.real_time_position) {
            return 'real'
        } else if (satellite.historical_data) {
            return 'historical'
        } else {
            return 'simulated'
        }
    }

    // 獲取可見衛星數據（含品質分級）
    const fetchVisibleSatellites = useCallback(async () => {
        try {
            const response = await simworldFetch(
                '/v1/satellites/visible_satellites?count=10&global_view=true'
            )
            if (response.ok) {
                const data = await response.json()
                const satellitesList = data.satellites || []

                if (satellitesList.length > 0) {
                    const satellites = satellitesList.map((sat: Record<string, unknown>) => {
                        const signalQuality = sat.signal_quality as Record<string, unknown> || {}
                        const position = sat.position as Record<string, unknown> || {}
                        const signalStrength = (signalQuality.estimated_signal_strength as number) || 80
                        const pathLoss = (signalQuality.path_loss_db as number) || 120
                        const rsrp = signalStrength - pathLoss
                        const elevation = (position.elevation as number) || 0
                        const rsrq = -20 + (elevation / 90) * 10
                        const sinr = 5 + (elevation / 90) * 15
                        const range = (position.range as number) || 800
                        const loadFactor = Math.min(0.9, 0.2 + (range - 500) / 1000)
                        const dataQuality = getDataQuality(sat)

                        return {
                            id: (sat.id as string)?.toString() || (sat.norad_id as string) || 'unknown',
                            name: (sat.name as string) || `Satellite-${sat.id}`,
                            elevation: elevation,
                            azimuth: (position.azimuth as number) || 0,
                            range: range,
                            rsrp: rsrp,
                            rsrq: rsrq,
                            sinr: sinr,
                            load_factor: loadFactor,
                            data_quality: dataQuality,
                        }
                    })
                    setVisibleSatellites(satellites)
                    setTotalSatellites(satellites.length * 50) // 假設這是可見衛星的1/50
                    return
                }
            }
        } catch (error) {
            console.warn('真實衛星數據不可用，使用模擬數據:', error)
        }

        // 模擬數據（帶品質標記）
        const mockSatellites = [
            {
                id: 'starlink-1234',
                name: 'Starlink-1234',
                elevation: 45.2,
                azimuth: 120.5,
                range: 550,
                rsrp: -85,
                rsrq: -12,
                sinr: 15,
                load_factor: 0.3,
                data_quality: 'simulated' as const,
            },
            {
                id: 'starlink-5678',
                name: 'Starlink-5678',
                elevation: 38.7,
                azimuth: 210.3,
                range: 580,
                rsrp: -90,
                rsrq: -14,
                sinr: 12,
                load_factor: 0.5,
                data_quality: 'simulated' as const,
            },
            {
                id: 'kuiper-1001',
                name: 'Kuiper-1001',
                elevation: 52.1,
                azimuth: 85.7,
                range: 520,
                rsrp: -82,
                rsrq: -10,
                sinr: 18,
                load_factor: 0.7,
                data_quality: 'simulated' as const,
            },
        ]

        const dynamicSatellites = mockSatellites.map((sat) => ({
            ...sat,
            rsrp: sat.rsrp + (Math.random() - 0.5) * 4,
            load_factor: Math.max(0.1, Math.min(0.9, sat.load_factor + (Math.random() - 0.5) * 0.2)),
        }))

        setVisibleSatellites(dynamicSatellites)
        setTotalSatellites(dynamicSatellites.length * 100) // 模擬總衛星數
    }, [])

    // 獲取訓練狀態
    const fetchTrainingStatus = useCallback(async () => {
        try {
            const response = await netstackFetch(`/api/v1/rl/training/status/${selectedAlgorithm}`)
            if (response.ok) {
                const status = await response.json()
                setIsTraining(status.training_active || false)

                if (status.training_progress) {
                    setTrainingProgress({
                        current_episode: status.training_progress.current_episode || 0,
                        total_episodes: status.training_progress.total_episodes || trainingEpisodes,
                        current_reward: status.metrics?.last_reward || 0,
                        average_reward: status.metrics?.average_reward || 0,
                        selected_satellite: status.decision_data?.selected_satellite || 'N/A',
                        decision_reason: status.decision_data?.reason || '等待決策...',
                        algorithm: selectedAlgorithm,
                        training_active: status.training_active || false,
                        // 新增：訓練狀態字段
                        epsilon: status.training_progress.epsilon || 0.1,
                        learning_rate: status.training_progress.learning_rate || 0.001,
                        loss: status.training_progress.loss || 0,
                        q_value: status.training_progress.q_value || 0,
                        success_rate: status.training_progress.success_rate || 0,
                    })
                }
            }
        } catch (error) {
            console.error('獲取訓練狀態失敗:', error)
        }
    }, [selectedAlgorithm, trainingEpisodes])

    // 開始訓練
    const handleStartTraining = useCallback(async () => {
        if (isControlling) return
        setIsControlling(true)

        try {
            const response = await netstackFetch(
                `/api/v1/rl/training/start/${selectedAlgorithm}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        experiment_name: `leo_handover_${selectedAlgorithm}_${Date.now()}`,
                        total_episodes: trainingEpisodes,
                        max_steps_per_episode: maxStepsPerEpisode,
                        scenario_type: scenarioType,
                        constellation_type: constellationType,
                        data_source: dataSource,
                        mobility_speed: mobilitySpeed,
                        training_speed: trainingSpeed,
                        save_interval: saveInterval,
                        hyperparameters: {
                            learning_rate: 0.001,
                            batch_size: 32,
                            gamma: 0.99,
                        },
                        decision_factors: decisionFactors,
                    }),
                }
            )

            if (response.ok) {
                console.log('✅ 訓練啟動成功')
                setIsTraining(true)
                onRefresh?.()
            } else {
                console.error('❌ 訓練啟動失敗')
            }
        } catch (error) {
            console.error('訓練啟動異常:', error)
        } finally {
            setIsControlling(false)
        }
    }, [selectedAlgorithm, decisionFactors, isControlling, onRefresh, trainingEpisodes, maxStepsPerEpisode, scenarioType, constellationType, dataSource, mobilitySpeed, trainingSpeed, saveInterval])

    // 停止訓練
    const handleStopTraining = useCallback(async () => {
        if (isControlling) return
        setIsControlling(true)

        try {
            const response = await netstackFetch(
                `/api/v1/rl/training/stop-algorithm/${selectedAlgorithm}`,
                {
                    method: 'POST',
                }
            )

            if (response.ok) {
                console.log('✅ 訓練停止成功')
                setIsTraining(false)
                setTrainingProgress(null)
                onRefresh?.()
            } else {
                console.error('❌ 訓練停止失敗')
            }
        } catch (error) {
            console.error('訓練停止異常:', error)
        } finally {
            setIsControlling(false)
        }
    }, [selectedAlgorithm, isControlling, onRefresh])

    // 定期更新數據
    useEffect(() => {
        fetchVisibleSatellites()
        fetchTrainingStatus()

        const interval = setInterval(() => {
            fetchVisibleSatellites()
            fetchTrainingStatus()
        }, 2000)

        return () => clearInterval(interval)
    }, [selectedAlgorithm, fetchTrainingStatus, fetchVisibleSatellites])

    const _getSignalQuality = (rsrp: number) => {
        if (rsrp > -80) return { level: '優秀', color: '#00ff00' }
        if (rsrp > -90) return { level: '良好', color: '#ffff00' }
        if (rsrp > -100) return { level: '一般', color: '#ff8800' }
        return { level: '差', color: '#ff0000' }
    }

    const _getDataQualityIcon = (quality: 'real' | 'historical' | 'simulated') => {
        switch (quality) {
            case 'real':
                return { icon: '🟢', label: '真實數據' }
            case 'historical':
                return { icon: '🟡', label: '歷史數據' }
            case 'simulated':
                return { icon: '🔴', label: '模擬數據' }
            default:
                return { icon: '⚪', label: '未知' }
        }
    }

    return (
        <div className="training-control-center">
            <div className="section-header">
                <h2>🎯 LEO 衛星換手訓練控制中心</h2>
                <div className="algorithm-selector">
                    <select
                        value={selectedAlgorithm}
                        onChange={(e) => setSelectedAlgorithm(e.target.value)}
                        disabled={isTraining}
                    >
                        <option value="dqn">DQN - Deep Q-Network</option>
                        <option value="ppo">PPO - Proximal Policy Optimization</option>
                        <option value="sac">SAC - Soft Actor-Critic</option>
                    </select>
                </div>
            </div>

            <div className="main-dashboard">
                {/* 左側：訓練環境配置 */}
                <div className="environment-panel">
                    <h3>🌐 訓練環境配置</h3>
                    
                    {/* 訓練參數設定 */}
                    <div className="training-config">
                        <h4>🔧 訓練參數</h4>
                        <div className="config-grid">
                            <div className="config-item">
                                <label>總回合數:</label>
                                <input
                                    type="number"
                                    min="100"
                                    max="10000"
                                    step="100"
                                    value={trainingEpisodes}
                                    onChange={(e) => setTrainingEpisodes(parseInt(e.target.value))}
                                    disabled={isTraining}
                                />
                            </div>
                            <div className="config-item">
                                <label>每回合步數:</label>
                                <input
                                    type="number"
                                    min="50"
                                    max="500"
                                    step="10"
                                    value={maxStepsPerEpisode}
                                    onChange={(e) => setMaxStepsPerEpisode(parseInt(e.target.value))}
                                    disabled={isTraining}
                                />
                            </div>
                            <div className="config-item">
                                <label>訓練速度:</label>
                                <select
                                    value={trainingSpeed}
                                    onChange={(e) => setTrainingSpeed(e.target.value)}
                                    disabled={isTraining}
                                >
                                    <option value="slow">慢速 (詳細觀察)</option>
                                    <option value="normal">正常 (平衡)</option>
                                    <option value="fast">快速 (批量訓練)</option>
                                </select>
                            </div>
                            <div className="config-item">
                                <label>保存間隔:</label>
                                <input
                                    type="number"
                                    min="10"
                                    max="1000"
                                    step="10"
                                    value={saveInterval}
                                    onChange={(e) => setSaveInterval(parseInt(e.target.value))}
                                    disabled={isTraining}
                                />
                                <span>回合</span>
                            </div>
                        </div>
                    </div>

                    {/* 訓練環境設定 */}
                    <div className="environment-config">
                        <h4>🌍 環境設定</h4>
                        <div className="env-grid">
                            <div className="env-item">
                                <label>場景類型:</label>
                                <select
                                    value={scenarioType}
                                    onChange={(e) => setScenarioType(e.target.value)}
                                    disabled={isTraining}
                                >
                                    <option value="urban">都市環境</option>
                                    <option value="suburban">郊區環境</option>
                                    <option value="rural">鄉村環境</option>
                                    <option value="maritime">海洋環境</option>
                                    <option value="mixed">混合環境</option>
                                </select>
                            </div>
                            <div className="env-item">
                                <label>衛星星座:</label>
                                <select
                                    value={constellationType}
                                    onChange={(e) => setConstellationType(e.target.value)}
                                    disabled={isTraining}
                                >
                                    <option value="starlink">Starlink</option>
                                    <option value="oneweb">OneWeb</option>
                                    <option value="kuiper">Kuiper</option>
                                    <option value="mixed">混合星座</option>
                                </select>
                            </div>
                            <div className="env-item">
                                <label>數據來源:</label>
                                <select
                                    value={dataSource}
                                    onChange={(e) => setDataSource(e.target.value)}
                                    disabled={isTraining}
                                >
                                    <option value="real_tle">真實 TLE 數據</option>
                                    <option value="historical">歷史數據</option>
                                    <option value="simulated">模擬數據</option>
                                </select>
                            </div>
                            <div className="env-item">
                                <label>移動速度:</label>
                                <select
                                    value={mobilitySpeed}
                                    onChange={(e) => setMobilitySpeed(e.target.value)}
                                    disabled={isTraining}
                                >
                                    <option value="static">靜態</option>
                                    <option value="pedestrian">步行 (3 km/h)</option>
                                    <option value="uav">UAV (30 km/h)</option>
                                    <option value="vehicle">車輛 (60 km/h)</option>
                                    <option value="highspeed">高速 (300 km/h)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* 數據來源狀態 */}
                    <div className="data-source-status">
                        <h4>📊 數據來源狀態</h4>
                        <div className="source-indicators">
                            <div className="source-item">
                                <span className="source-label">總衛星數:</span>
                                <span className="source-value">{totalSatellites}</span>
                            </div>
                            <div className="source-item">
                                <span className="source-label">可用衛星:</span>
                                <span className="source-value">{visibleSatellites.length}</span>
                            </div>
                            <div className="source-item">
                                <span className="source-label">數據品質:</span>
                                <span className={`source-value quality-${dataSource}`}>
                                    {dataSource === 'real_tle' ? '🟢 真實' : 
                                     dataSource === 'historical' ? '🟡 歷史' : '🔴 模擬'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 右側：訓練控制 */}
                <div className="training-control-panel">
                    <h3>🧠 {selectedAlgorithm.toUpperCase()} 訓練控制</h3>

                    {!isTraining ? (
                        <div className="training-idle">
                            <div className="idle-status">
                                <span className="status-icon">⏸️</span>
                                <span>準備開始 LEO 衛星換手決策訓練</span>
                            </div>
                            
                            <div className="decision-factors">
                                <h4>🎯 決策因素權重</h4>
                                <div className="factors-grid">
                                    <div className="factor-item">
                                        <label>仰角 (30%)</label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="1"
                                            step="0.05"
                                            value={decisionFactors.elevation_weight}
                                            onChange={(e) =>
                                                setDecisionFactors({
                                                    ...decisionFactors,
                                                    elevation_weight: parseFloat(e.target.value),
                                                })
                                            }
                                        />
                                        <span>{(decisionFactors.elevation_weight * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="factor-item">
                                        <label>RSRP (25%)</label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="1"
                                            step="0.05"
                                            value={decisionFactors.rsrp_weight}
                                            onChange={(e) =>
                                                setDecisionFactors({
                                                    ...decisionFactors,
                                                    rsrp_weight: parseFloat(e.target.value),
                                                })
                                            }
                                        />
                                        <span>{(decisionFactors.rsrp_weight * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="factor-item">
                                        <label>RSRQ (20%)</label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="1"
                                            step="0.05"
                                            value={decisionFactors.rsrq_weight}
                                            onChange={(e) =>
                                                setDecisionFactors({
                                                    ...decisionFactors,
                                                    rsrq_weight: parseFloat(e.target.value),
                                                })
                                            }
                                        />
                                        <span>{(decisionFactors.rsrq_weight * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="factor-item">
                                        <label>負載 (15%)</label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="1"
                                            step="0.05"
                                            value={decisionFactors.load_weight}
                                            onChange={(e) =>
                                                setDecisionFactors({
                                                    ...decisionFactors,
                                                    load_weight: parseFloat(e.target.value),
                                                })
                                            }
                                        />
                                        <span>{(decisionFactors.load_weight * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="factor-item">
                                        <label>穩定性 (10%)</label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="1"
                                            step="0.05"
                                            value={decisionFactors.stability_weight}
                                            onChange={(e) =>
                                                setDecisionFactors({
                                                    ...decisionFactors,
                                                    stability_weight: parseFloat(e.target.value),
                                                })
                                            }
                                        />
                                        <span>{(decisionFactors.stability_weight * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                            </div>

                            <button
                                className="btn btn-primary btn-large start-training-btn"
                                onClick={handleStartTraining}
                                disabled={isControlling}
                            >
                                {isControlling ? '🔄 啟動中...' : '▶️ 開始訓練'}
                            </button>
                        </div>
                    ) : (
                        <div className="training-active">
                            <div className="training-status">
                                <span className="status-icon">🔄</span>
                                <span>訓練進行中...</span>
                                <button
                                    className="btn btn-danger btn-sm"
                                    onClick={handleStopTraining}
                                    disabled={isControlling}
                                >
                                    {isControlling ? '🔄' : '⏹️'} 停止
                                </button>
                            </div>

                            {trainingProgress && (
                                <>
                                    <div className="progress-section">
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill"
                                                style={{
                                                    width: `${
                                                        (trainingProgress.current_episode /
                                                            trainingProgress.total_episodes) *
                                                        100
                                                    }%`,
                                                }}
                                            />
                                        </div>
                                        <div className="progress-text">
                                            回合 {trainingProgress.current_episode} /{' '}
                                            {trainingProgress.total_episodes} (
                                            {(
                                                (trainingProgress.current_episode /
                                                    trainingProgress.total_episodes) *
                                                100
                                            ).toFixed(1)}
                                            %)
                                        </div>
                                    </div>

                                    <div className="metrics-grid">
                                        <div className="metric-card">
                                            <span className="metric-label">當前獎勵</span>
                                            <span className="metric-value">
                                                {trainingProgress.current_reward.toFixed(2)}
                                            </span>
                                        </div>
                                        <div className="metric-card">
                                            <span className="metric-label">平均獎勵</span>
                                            <span className="metric-value">
                                                {trainingProgress.average_reward.toFixed(2)}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="training-state-section">
                                        <h4>🧠 訓練狀態</h4>
                                        <div className="training-state-info">
                                            <div className="state-item">
                                                <span className="state-label">當前回合:</span>
                                                <span className="state-value">{trainingProgress.current_episode}</span>
                                            </div>
                                            <div className="state-item">
                                                <span className="state-label">探索率:</span>
                                                <span className="state-value">{(trainingProgress.epsilon * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="state-item">
                                                <span className="state-label">學習率:</span>
                                                <span className="state-value">{trainingProgress.learning_rate.toFixed(4)}</span>
                                            </div>
                                            <div className="state-item">
                                                <span className="state-label">損失函數:</span>
                                                <span className="state-value">{trainingProgress.loss.toFixed(4)}</span>
                                            </div>
                                            <div className="state-item">
                                                <span className="state-label">Q值:</span>
                                                <span className="state-value">{trainingProgress.q_value.toFixed(2)}</span>
                                            </div>
                                            <div className="state-item">
                                                <span className="state-label">成功率:</span>
                                                <span className="state-value">{(trainingProgress.success_rate * 100).toFixed(1)}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>

        </div>
    )
}

export default TrainingControlCenterSection