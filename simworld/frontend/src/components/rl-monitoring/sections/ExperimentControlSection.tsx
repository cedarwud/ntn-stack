/**
 * 實驗控制台 - 統一參數管理和實驗執行
 * 整合原訓練控制中心和參數調優功能
 * 根據 @tr.md 設計的5個參數分組：
 * A. 實驗基本配置
 * B. LEO環境參數
 * C. 切換決策參數
 * D. RL超參數
 * E. 訓練控制
 */

import React, { useState, useEffect, useCallback } from 'react'
import { netstackFetch } from '../../../config/api-config'
import './ExperimentControlSection.scss'

interface ExperimentControlProps {
    data: unknown
    onRefresh?: () => void
}

interface ExperimentConfig {
    // A. 實驗基本配置
    experiment_name: string
    experiment_description: string
    algorithm: string
    total_episodes: number
    experiment_tags: string[]
    
    // B. LEO環境參數
    satellite_constellation: string
    scenario_type: string
    user_mobility: string
    data_source: string
    
    // C. 切換決策參數
    signal_quality_weights: {
        rsrp_weight: number
        rsrq_weight: number
        sinr_weight: number
    }
    geometry_weights: {
        elevation_weight: number
        distance_weight: number
    }
    load_balancing_weights: {
        current_load_weight: number
        predicted_load_weight: number
    }
    handover_history_weight: number
    
    // D. RL超參數
    learning_rate: number
    batch_size: number
    memory_size: number
    epsilon_start: number
    epsilon_end: number
    epsilon_decay: number
    gamma: number
    target_update_frequency: number
    
    // E. 訓練控制
    training_speed: string
    save_interval: number
    evaluation_frequency: number
    early_stopping_patience: number
    convergence_threshold: number
}

interface TrainingStatus {
    is_training: boolean
    current_episode: number
    total_episodes: number
    current_reward: number
    average_reward: number
    epsilon: number
    learning_rate: number
    loss: number
    training_time: number
    estimated_completion: string
}

const ExperimentControlSection: React.FC<ExperimentControlProps> = ({ 
    data: _data, 
    onRefresh 
}) => {
    // 實驗配置狀態
    const [experimentConfig, setExperimentConfig] = useState<ExperimentConfig>({
        // A. 實驗基本配置
        experiment_name: `leo_handover_${Date.now()}`,
        experiment_description: 'LEO衛星切換決策學習實驗',
        algorithm: 'dqn',
        total_episodes: 1000,
        experiment_tags: ['leo', 'handover', 'rl'],
        
        // B. LEO環境參數
        satellite_constellation: 'mixed',
        scenario_type: 'urban',
        user_mobility: 'static',
        data_source: 'real_tle',
        
        // C. 切換決策參數
        signal_quality_weights: {
            rsrp_weight: 0.25,
            rsrq_weight: 0.20,
            sinr_weight: 0.15
        },
        geometry_weights: {
            elevation_weight: 0.30,
            distance_weight: 0.10
        },
        load_balancing_weights: {
            current_load_weight: 0.10,
            predicted_load_weight: 0.05
        },
        handover_history_weight: 0.15,
        
        // D. RL超參數
        learning_rate: 0.001,
        batch_size: 32,
        memory_size: 10000,
        epsilon_start: 1.0,
        epsilon_end: 0.01,
        epsilon_decay: 0.995,
        gamma: 0.99,
        target_update_frequency: 100,
        
        // E. 訓練控制
        training_speed: 'normal',
        save_interval: 100,
        evaluation_frequency: 50,
        early_stopping_patience: 200,
        convergence_threshold: 0.001
    })
    
    // 訓練狀態
    const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null)
    const [isTraining, setIsTraining] = useState(false)
    const [isControlling, setIsControlling] = useState(false)
    
    // 參數分組展開狀態
    const [expandedSections, setExpandedSections] = useState<Set<string>>(
        new Set(['basic', 'environment', 'decision', 'hyperparams', 'control'])
    )
    
    // 獲取訓練狀態
    const fetchTrainingStatus = useCallback(async () => {
        try {
            const response = await netstackFetch(`/api/v1/rl/training/status/${experimentConfig.algorithm}`)
            if (response.ok) {
                const status = await response.json()
                setTrainingStatus(status)
                setIsTraining(status.is_training || false)
            }
        } catch (error) {
            console.error('獲取訓練狀態失敗:', error)
        }
    }, [experimentConfig.algorithm])
    
    // 開始實驗
    const handleStartExperiment = useCallback(async () => {
        if (isControlling) return
        setIsControlling(true)
        
        try {
            const response = await netstackFetch(
                `/api/v1/rl/training/start/${experimentConfig.algorithm}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(experimentConfig)
                }
            )
            
            if (response.ok) {
                console.log('✅ 實驗啟動成功')
                setIsTraining(true)
                onRefresh?.()
            } else {
                console.error('❌ 實驗啟動失敗')
            }
        } catch (error) {
            console.error('實驗啟動異常:', error)
        } finally {
            setIsControlling(false)
        }
    }, [experimentConfig, isControlling, onRefresh])
    
    // 停止實驗
    const handleStopExperiment = useCallback(async () => {
        if (isControlling) return
        setIsControlling(true)
        
        try {
            const response = await netstackFetch(
                `/api/v1/rl/training/stop/${experimentConfig.algorithm}`,
                { method: 'POST' }
            )
            
            if (response.ok) {
                console.log('✅ 實驗停止成功')
                setIsTraining(false)
                setTrainingStatus(null)
                onRefresh?.()
            } else {
                console.error('❌ 實驗停止失敗')
            }
        } catch (error) {
            console.error('實驗停止異常:', error)
        } finally {
            setIsControlling(false)
        }
    }, [experimentConfig.algorithm, isControlling, onRefresh])
    
    // 參數分組切換
    const toggleSection = (sectionId: string) => {
        const newExpanded = new Set(expandedSections)
        if (newExpanded.has(sectionId)) {
            newExpanded.delete(sectionId)
        } else {
            newExpanded.add(sectionId)
        }
        setExpandedSections(newExpanded)
    }
    
    // 更新配置
    const updateConfig = (path: string, value: any) => {
        setExperimentConfig(prev => {
            const newConfig = { ...prev }
            const keys = path.split('.')
            let current = newConfig as any
            
            for (let i = 0; i < keys.length - 1; i++) {
                current = current[keys[i]]
            }
            current[keys[keys.length - 1]] = value
            
            return newConfig
        })
    }
    
    // 定期更新狀態
    useEffect(() => {
        fetchTrainingStatus()
        const interval = setInterval(fetchTrainingStatus, 2000)
        return () => clearInterval(interval)
    }, [fetchTrainingStatus])
    
    return (
        <div className="experiment-control-section">
            <div className="section-header">
                <h2>🚀 實驗控制台</h2>
                <div className="header-subtitle">
                    統一參數管理和實驗執行 - 專為LEO衛星切換研究設計
                </div>
            </div>
            
            <div className="experiment-layout">
                {/* 左側：參數配置 */}
                <div className="config-panel">
                    <div className="config-header">
                        <h3>🎛️ 實驗配置</h3>
                        <div className="config-actions">
                            <button 
                                className="btn btn-secondary btn-sm"
                                onClick={() => setExpandedSections(new Set(['basic', 'environment', 'decision', 'hyperparams', 'control']))}
                            >
                                全部展開
                            </button>
                            <button 
                                className="btn btn-secondary btn-sm"
                                onClick={() => setExpandedSections(new Set())}
                            >
                                全部收起
                            </button>
                        </div>
                    </div>
                    
                    {/* A. 實驗基本配置 */}
                    <div className="config-section">
                        <div 
                            className="config-section-header"
                            onClick={() => toggleSection('basic')}
                        >
                            <span className="section-icon">📋</span>
                            <span className="section-title">A. 實驗基本配置</span>
                            <span className="section-toggle">
                                {expandedSections.has('basic') ? '▼' : '▶'}
                            </span>
                        </div>
                        
                        {expandedSections.has('basic') && (
                            <div className="config-content">
                                <div className="config-grid">
                                    <div className="config-item">
                                        <label>
                                            實驗名稱
                                            <span className="tooltip" title="用於識別和管理實驗">ⓘ</span>
                                        </label>
                                        <input
                                            type="text"
                                            value={experimentConfig.experiment_name}
                                            onChange={(e) => updateConfig('experiment_name', e.target.value)}
                                            disabled={isTraining}
                                        />
                                    </div>
                                    
                                    <div className="config-item">
                                        <label>
                                            算法選擇
                                            <span className="tooltip" title="選擇強化學習算法">ⓘ</span>
                                        </label>
                                        <select
                                            value={experimentConfig.algorithm}
                                            onChange={(e) => updateConfig('algorithm', e.target.value)}
                                            disabled={isTraining}
                                        >
                                            <option value="dqn">DQN - Deep Q-Network</option>
                                            <option value="ppo">PPO - Proximal Policy Optimization</option>
                                            <option value="sac">SAC - Soft Actor-Critic</option>
                                        </select>
                                    </div>
                                    
                                    <div className="config-item">
                                        <label>
                                            總回合數
                                            <span className="tooltip" title="訓練的總回合數">ⓘ</span>
                                        </label>
                                        <input
                                            type="number"
                                            min="100"
                                            max="10000"
                                            step="100"
                                            value={experimentConfig.total_episodes}
                                            onChange={(e) => updateConfig('total_episodes', parseInt(e.target.value))}
                                            disabled={isTraining}
                                        />
                                    </div>
                                    
                                    <div className="config-item full-width">
                                        <label>
                                            實驗描述
                                            <span className="tooltip" title="詳細描述實驗目的和設定">ⓘ</span>
                                        </label>
                                        <textarea
                                            value={experimentConfig.experiment_description}
                                            onChange={(e) => updateConfig('experiment_description', e.target.value)}
                                            disabled={isTraining}
                                            rows={2}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                    
                    {/* B. LEO環境參數 */}
                    <div className="config-section">
                        <div 
                            className="config-section-header"
                            onClick={() => toggleSection('environment')}
                        >
                            <span className="section-icon">🌍</span>
                            <span className="section-title">B. LEO環境參數</span>
                            <span className="section-toggle">
                                {expandedSections.has('environment') ? '▼' : '▶'}
                            </span>
                        </div>
                        
                        {expandedSections.has('environment') && (
                            <div className="config-content">
                                <div className="config-grid">
                                    <div className="config-item">
                                        <label>
                                            衛星星座
                                            <span className="tooltip" title="選擇LEO衛星星座類型">ⓘ</span>
                                        </label>
                                        <select
                                            value={experimentConfig.satellite_constellation}
                                            onChange={(e) => updateConfig('satellite_constellation', e.target.value)}
                                            disabled={isTraining}
                                        >
                                            <option value="starlink">Starlink</option>
                                            <option value="oneweb">OneWeb</option>
                                            <option value="kuiper">Kuiper</option>
                                            <option value="mixed">混合星座</option>
                                        </select>
                                    </div>
                                    
                                    <div className="config-item">
                                        <label>
                                            場景類型
                                            <span className="tooltip" title="影響信號傳播和干擾模型">ⓘ</span>
                                        </label>
                                        <select
                                            value={experimentConfig.scenario_type}
                                            onChange={(e) => updateConfig('scenario_type', e.target.value)}
                                            disabled={isTraining}
                                        >
                                            <option value="urban">都市環境</option>
                                            <option value="suburban">郊區環境</option>
                                            <option value="rural">鄉村環境</option>
                                            <option value="maritime">海洋環境</option>
                                            <option value="mixed">混合環境</option>
                                        </select>
                                    </div>
                                    
                                    <div className="config-item">
                                        <label>
                                            用戶移動性
                                            <span className="tooltip" title="影響切換頻率和決策複雜度">ⓘ</span>
                                        </label>
                                        <select
                                            value={experimentConfig.user_mobility}
                                            onChange={(e) => updateConfig('user_mobility', e.target.value)}
                                            disabled={isTraining}
                                        >
                                            <option value="static">靜態</option>
                                            <option value="pedestrian">步行 (3 km/h)</option>
                                            <option value="uav">UAV (30 km/h)</option>
                                            <option value="vehicle">車輛 (60 km/h)</option>
                                            <option value="highspeed">高速 (300 km/h)</option>
                                        </select>
                                    </div>
                                    
                                    <div className="config-item">
                                        <label>
                                            數據來源
                                            <span className="tooltip" title="影響仿真真實度">ⓘ</span>
                                        </label>
                                        <select
                                            value={experimentConfig.data_source}
                                            onChange={(e) => updateConfig('data_source', e.target.value)}
                                            disabled={isTraining}
                                        >
                                            <option value="real_tle">真實 TLE 數據</option>
                                            <option value="historical">歷史數據</option>
                                            <option value="simulated">模擬數據</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                    
                    {/* C. 切換決策參數 */}
                    <div className="config-section">
                        <div 
                            className="config-section-header"
                            onClick={() => toggleSection('decision')}
                        >
                            <span className="section-icon">🎯</span>
                            <span className="section-title">C. 切換決策參數</span>
                            <span className="section-toggle">
                                {expandedSections.has('decision') ? '▼' : '▶'}
                            </span>
                        </div>
                        
                        {expandedSections.has('decision') && (
                            <div className="config-content">
                                <div className="decision-weights">
                                    <h4>信號品質權重</h4>
                                    <div className="weight-group">
                                        <div className="weight-item">
                                            <label>RSRP權重</label>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.05"
                                                value={experimentConfig.signal_quality_weights.rsrp_weight}
                                                onChange={(e) => updateConfig('signal_quality_weights.rsrp_weight', parseFloat(e.target.value))}
                                                disabled={isTraining}
                                            />
                                            <span>{(experimentConfig.signal_quality_weights.rsrp_weight * 100).toFixed(0)}%</span>
                                        </div>
                                        
                                        <div className="weight-item">
                                            <label>RSRQ權重</label>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.05"
                                                value={experimentConfig.signal_quality_weights.rsrq_weight}
                                                onChange={(e) => updateConfig('signal_quality_weights.rsrq_weight', parseFloat(e.target.value))}
                                                disabled={isTraining}
                                            />
                                            <span>{(experimentConfig.signal_quality_weights.rsrq_weight * 100).toFixed(0)}%</span>
                                        </div>
                                    </div>
                                    
                                    <h4>幾何參數權重</h4>
                                    <div className="weight-group">
                                        <div className="weight-item">
                                            <label>仰角權重</label>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.05"
                                                value={experimentConfig.geometry_weights.elevation_weight}
                                                onChange={(e) => updateConfig('geometry_weights.elevation_weight', parseFloat(e.target.value))}
                                                disabled={isTraining}
                                            />
                                            <span>{(experimentConfig.geometry_weights.elevation_weight * 100).toFixed(0)}%</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                
                {/* 右側：訓練控制 */}
                <div className="control-panel">
                    <div className="control-header">
                        <h3>🎮 訓練控制</h3>
                        <div className="training-status">
                            {isTraining ? (
                                <span className="status-indicator status-active">🟢 訓練中</span>
                            ) : (
                                <span className="status-indicator status-idle">⏸️ 待機</span>
                            )}
                        </div>
                    </div>
                    
                    {!isTraining ? (
                        <div className="control-idle">
                            <div className="experiment-summary">
                                <h4>實驗摘要</h4>
                                <div className="summary-item">
                                    <strong>算法:</strong> {experimentConfig.algorithm.toUpperCase()}
                                </div>
                                <div className="summary-item">
                                    <strong>回合數:</strong> {experimentConfig.total_episodes}
                                </div>
                                <div className="summary-item">
                                    <strong>環境:</strong> {experimentConfig.scenario_type} / {experimentConfig.satellite_constellation}
                                </div>
                                <div className="summary-item">
                                    <strong>數據源:</strong> {experimentConfig.data_source}
                                </div>
                            </div>
                            
                            <button
                                className="btn btn-primary btn-large start-experiment-btn"
                                onClick={handleStartExperiment}
                                disabled={isControlling}
                            >
                                {isControlling ? '🔄 啟動中...' : '▶️ 開始實驗'}
                            </button>
                        </div>
                    ) : (
                        <div className="control-active">
                            <div className="training-progress">
                                <h4>訓練進度</h4>
                                {trainingStatus && (
                                    <div className="progress-info">
                                        <div className="progress-bar">
                                            <div 
                                                className="progress-fill"
                                                style={{ 
                                                    width: `${(trainingStatus.current_episode / trainingStatus.total_episodes) * 100}%` 
                                                }}
                                            />
                                        </div>
                                        <div className="progress-text">
                                            {trainingStatus.current_episode} / {trainingStatus.total_episodes} 回合
                                        </div>
                                        
                                        <div className="metrics-grid">
                                            <div className="metric-item">
                                                <span className="metric-label">當前獎勵</span>
                                                <span className="metric-value">{trainingStatus.current_reward.toFixed(2)}</span>
                                            </div>
                                            <div className="metric-item">
                                                <span className="metric-label">平均獎勵</span>
                                                <span className="metric-value">{trainingStatus.average_reward.toFixed(2)}</span>
                                            </div>
                                            <div className="metric-item">
                                                <span className="metric-label">探索率</span>
                                                <span className="metric-value">{(trainingStatus.epsilon * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="metric-item">
                                                <span className="metric-label">損失</span>
                                                <span className="metric-value">{trainingStatus.loss.toFixed(4)}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                            
                            <button
                                className="btn btn-danger btn-large stop-experiment-btn"
                                onClick={handleStopExperiment}
                                disabled={isControlling}
                            >
                                {isControlling ? '🔄 停止中...' : '⏹️ 停止實驗'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default ExperimentControlSection