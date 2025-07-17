import React, { useState, useEffect } from 'react'
import { netstackFetch } from '../../../config/api-config'
import './ParameterTuningSection.scss'

interface ParameterTuningProps {
    data: unknown
    onRefresh?: () => void
}

interface AlgorithmHyperparameters {
    dqn: {
        learning_rate: number
        epsilon: number
        epsilon_decay: number
        epsilon_min: number
        batch_size: number
        memory_size: number
        target_update_freq: number
        gamma: number
    }
    ppo: {
        learning_rate: number
        clip_range: number
        value_function_coef: number
        entropy_coef: number
        gae_lambda: number
        max_grad_norm: number
        batch_size: number
        gamma: number
    }
    sac: {
        learning_rate: number
        alpha: number
        target_entropy: number
        tau: number
        batch_size: number
        buffer_size: number
        gamma: number
    }
}

interface EnvironmentParameters {
    satellite_visibility_threshold: number
    signal_quality_weight: number
    load_balancing_weight: number
    handover_penalty: number
    stability_bonus: number
    ping_pong_penalty: number
    reward_scaling: number
}

interface RewardFunction {
    successful_handover_bonus: number
    stable_connection_bonus: number
    poor_handover_penalty: number
    connection_loss_penalty: number
    frequent_handover_penalty: number
    signal_quality_factor: number
    load_balancing_factor: number
}

const ParameterTuningSection: React.FC<ParameterTuningProps> = ({ data, onRefresh }) => {
    const [selectedAlgorithm, setSelectedAlgorithm] = useState<keyof AlgorithmHyperparameters>('dqn')
    const [hyperparameters, setHyperparameters] = useState<AlgorithmHyperparameters>({
        dqn: {
            learning_rate: 0.001,
            epsilon: 1.0,
            epsilon_decay: 0.995,
            epsilon_min: 0.01,
            batch_size: 32,
            memory_size: 10000,
            target_update_freq: 100,
            gamma: 0.99,
        },
        ppo: {
            learning_rate: 0.0003,
            clip_range: 0.2,
            value_function_coef: 0.5,
            entropy_coef: 0.01,
            gae_lambda: 0.95,
            max_grad_norm: 0.5,
            batch_size: 64,
            gamma: 0.99,
        },
        sac: {
            learning_rate: 0.0001,
            alpha: 0.2,
            target_entropy: -2.0,
            tau: 0.005,
            batch_size: 128,
            buffer_size: 50000,
            gamma: 0.99,
        },
    })

    const [environmentParams, setEnvironmentParams] = useState<EnvironmentParameters>({
        satellite_visibility_threshold: 10.0,
        signal_quality_weight: 0.4,
        load_balancing_weight: 0.3,
        handover_penalty: -5.0,
        stability_bonus: 10.0,
        ping_pong_penalty: -15.0,
        reward_scaling: 1.0,
    })

    const [rewardFunction, setRewardFunction] = useState<RewardFunction>({
        successful_handover_bonus: 100,
        stable_connection_bonus: 50,
        poor_handover_penalty: -50,
        connection_loss_penalty: -100,
        frequent_handover_penalty: -25,
        signal_quality_factor: 0.3,
        load_balancing_factor: 0.2,
    })

    const [activeTab, setActiveTab] = useState<'hyperparameters' | 'environment' | 'reward' | 'optimization'>('hyperparameters')
    const [isApplying, setIsApplying] = useState(false)
    const [lastApplied, setLastApplied] = useState<Date | null>(null)
    const [isOptimizing, setIsOptimizing] = useState(false)
    const [optimizationProgress, setOptimizationProgress] = useState(0)
    const [optimizationResults, setOptimizationResults] = useState<Record<string, unknown> | null>(null)

    // 加載當前參數
    useEffect(() => {
        loadCurrentParameters()
    }, [selectedAlgorithm])

    const loadCurrentParameters = async () => {
        try {
            const response = await netstackFetch(`/api/v1/rl/parameters/${selectedAlgorithm}`)
            if (response.ok) {
                const params = await response.json()
                if (params.hyperparameters) {
                    setHyperparameters(prev => ({
                        ...prev,
                        [selectedAlgorithm]: params.hyperparameters
                    }))
                }
                if (params.environment) {
                    setEnvironmentParams(params.environment)
                }
                if (params.reward) {
                    setRewardFunction(params.reward)
                }
            }
        } catch (error) {
            console.error('加載參數失敗:', error)
        }
    }

    const applyParameters = async () => {
        setIsApplying(true)
        try {
            const response = await netstackFetch(`/api/v1/rl/parameters/${selectedAlgorithm}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    hyperparameters: hyperparameters[selectedAlgorithm],
                    environment: environmentParams,
                    reward: rewardFunction,
                })
            })

            if (response.ok) {
                setLastApplied(new Date())
                console.log('✅ 參數應用成功')
                onRefresh?.()
            } else {
                console.error('❌ 參數應用失敗')
            }
        } catch (error) {
            console.error('參數應用異常:', error)
        } finally {
            setIsApplying(false)
        }
    }

    const resetToDefaults = () => {
        setHyperparameters({
            dqn: {
                learning_rate: 0.001,
                epsilon: 1.0,
                epsilon_decay: 0.995,
                epsilon_min: 0.01,
                batch_size: 32,
                memory_size: 10000,
                target_update_freq: 100,
                gamma: 0.99,
            },
            ppo: {
                learning_rate: 0.0003,
                clip_range: 0.2,
                value_function_coef: 0.5,
                entropy_coef: 0.01,
                gae_lambda: 0.95,
                max_grad_norm: 0.5,
                batch_size: 64,
                gamma: 0.99,
            },
            sac: {
                learning_rate: 0.0001,
                alpha: 0.2,
                target_entropy: -2.0,
                tau: 0.005,
                batch_size: 128,
                buffer_size: 50000,
                gamma: 0.99,
            },
        })
        setEnvironmentParams({
            satellite_visibility_threshold: 10.0,
            signal_quality_weight: 0.4,
            load_balancing_weight: 0.3,
            handover_penalty: -5.0,
            stability_bonus: 10.0,
            ping_pong_penalty: -15.0,
            reward_scaling: 1.0,
        })
        setRewardFunction({
            successful_handover_bonus: 100,
            stable_connection_bonus: 50,
            poor_handover_penalty: -50,
            connection_loss_penalty: -100,
            frequent_handover_penalty: -25,
            signal_quality_factor: 0.3,
            load_balancing_factor: 0.2,
        })
    }

    // 一鍵參數優化
    const optimizeParameters = async () => {
        setIsOptimizing(true)
        setOptimizationProgress(0)
        setOptimizationResults(null)

        try {
            // 開始優化
            const response = await netstackFetch(`/api/v1/rl/optimization/${selectedAlgorithm}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    optimization_type: 'bayesian',
                    max_iterations: 50,
                    target_metric: 'average_reward',
                    constraints: {
                        max_training_time: 3600, // 1 小時
                        min_episodes: 100,
                        convergence_threshold: 0.01
                    }
                })
            })

            if (!response.ok) {
                throw new Error('優化啟動失敗')
            }

            const { optimization_id } = await response.json()

            // 輪詢優化進度
            const pollInterval = setInterval(async () => {
                try {
                    const statusResponse = await netstackFetch(`/api/v1/rl/optimization/${optimization_id}/status`)
                    if (statusResponse.ok) {
                        const status = await statusResponse.json()
                        setOptimizationProgress(status.progress || 0)

                        if (status.status === 'completed') {
                            clearInterval(pollInterval)
                            setIsOptimizing(false)
                            setOptimizationResults(status.results)
                            
                            // 應用優化結果
                            if (status.results.best_parameters) {
                                setHyperparameters(prev => ({
                                    ...prev,
                                    [selectedAlgorithm]: status.results.best_parameters.hyperparameters
                                }))
                                setEnvironmentParams(status.results.best_parameters.environment)
                                setRewardFunction(status.results.best_parameters.reward)
                            }
                        } else if (status.status === 'failed') {
                            clearInterval(pollInterval)
                            setIsOptimizing(false)
                            console.error('優化失敗:', status.error)
                        }
                    }
                } catch (error) {
                    console.error('獲取優化狀態失敗:', error)
                }
            }, 2000)

            // 5分鐘後超時
            setTimeout(() => {
                clearInterval(pollInterval)
                if (isOptimizing) {
                    setIsOptimizing(false)
                    console.warn('優化超時')
                }
            }, 300000)

        } catch (error) {
            console.error('參數優化失敗:', error)
            setIsOptimizing(false)
        }
    }

    // 應用優化結果
    const applyOptimizationResults = async () => {
        if (!optimizationResults || !optimizationResults.best_parameters) return

        setIsApplying(true)
        try {
            const response = await netstackFetch(`/api/v1/rl/parameters/${selectedAlgorithm}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(optimizationResults.best_parameters)
            })

            if (response.ok) {
                setLastApplied(new Date())
                console.log('✅ 優化參數應用成功')
                onRefresh?.()
            } else {
                console.error('❌ 優化參數應用失敗')
            }
        } catch (error) {
            console.error('優化參數應用異常:', error)
        } finally {
            setIsApplying(false)
        }
    }

    const updateHyperparameter = (key: string, value: number) => {
        setHyperparameters(prev => ({
            ...prev,
            [selectedAlgorithm]: {
                ...prev[selectedAlgorithm],
                [key]: value
            }
        }))
    }

    const updateEnvironmentParam = (key: keyof EnvironmentParameters, value: number) => {
        setEnvironmentParams(prev => ({
            ...prev,
            [key]: value
        }))
    }

    const updateRewardParam = (key: keyof RewardFunction, value: number) => {
        setRewardFunction(prev => ({
            ...prev,
            [key]: value
        }))
    }

    const getParameterDescription = (param: string) => {
        const descriptions: Record<string, string> = {
            learning_rate: '學習率 - 控制網絡權重更新的步長',
            epsilon: '探索率 - 隨機動作的概率',
            epsilon_decay: '探索率衰減 - 每次更新後epsilon的衰減係數',
            epsilon_min: '最小探索率 - epsilon的最小值',
            batch_size: '批次大小 - 每次訓練使用的樣本數量',
            memory_size: '記憶體大小 - 經驗回放緩衝區的容量',
            target_update_freq: '目標網絡更新頻率 - 每多少步更新一次目標網絡',
            gamma: '折扣因子 - 未來獎勵的重要性',
            clip_range: '裁剪範圍 - PPO算法的裁剪參數',
            value_function_coef: '價值函數係數 - 價值損失的權重',
            entropy_coef: '熵係數 - 探索的權重',
            gae_lambda: 'GAE λ - 廣義優勢估計的衰減參數',
            max_grad_norm: '最大梯度範數 - 梯度裁剪的閾值',
            alpha: '溫度參數 - SAC算法的熵正則化係數',
            target_entropy: '目標熵 - 期望的策略熵值',
            tau: '軟更新係數 - 目標網絡軟更新的速率',
            buffer_size: '緩衝區大小 - 經驗回放緩衝區的容量',
        }
        return descriptions[param] || '參數描述'
    }

    const renderParameterControl = (key: string, value: number, min: number, max: number, step: number) => (
        <div key={key} className="parameter-control">
            <div className="parameter-header">
                <label>{key}</label>
                <span className="parameter-value">{value}</span>
            </div>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e) => updateHyperparameter(key, parseFloat(e.target.value))}
                className="parameter-slider"
            />
            <div className="parameter-description">
                {getParameterDescription(key)}
            </div>
        </div>
    )

    return (
        <div className="parameter-tuning-section">
            <div className="section-header">
                <h2>⚙️ 參數調優中心</h2>
                <div className="header-controls">
                    <select
                        value={selectedAlgorithm}
                        onChange={(e) => setSelectedAlgorithm(e.target.value as keyof AlgorithmHyperparameters)}
                        className="algorithm-selector"
                    >
                        <option value="dqn">DQN</option>
                        <option value="ppo">PPO</option>
                        <option value="sac">SAC</option>
                    </select>
                    <button className="btn btn-secondary" onClick={resetToDefaults}>
                        🔄 重置默認值
                    </button>
                </div>
            </div>

            <div className="parameter-tabs">
                <div className="tab-nav">
                    <button
                        className={`tab-btn ${activeTab === 'hyperparameters' ? 'active' : ''}`}
                        onClick={() => setActiveTab('hyperparameters')}
                    >
                        🧠 算法超參數
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'environment' ? 'active' : ''}`}
                        onClick={() => setActiveTab('environment')}
                    >
                        🌐 環境參數
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'reward' ? 'active' : ''}`}
                        onClick={() => setActiveTab('reward')}
                    >
                        🎯 獎勵函數
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'optimization' ? 'active' : ''}`}
                        onClick={() => setActiveTab('optimization')}
                    >
                        🚀 一鍵優化
                    </button>
                </div>

                <div className="tab-content">
                    {activeTab === 'hyperparameters' && (
                        <div className="hyperparameters-panel">
                            <h3>{selectedAlgorithm.toUpperCase()} 超參數</h3>
                            <div className="parameters-grid">
                                {selectedAlgorithm === 'dqn' && (
                                    <>
                                        {renderParameterControl('learning_rate', hyperparameters.dqn.learning_rate, 0.0001, 0.01, 0.0001)}
                                        {renderParameterControl('epsilon', hyperparameters.dqn.epsilon, 0.01, 1.0, 0.01)}
                                        {renderParameterControl('epsilon_decay', hyperparameters.dqn.epsilon_decay, 0.9, 0.999, 0.001)}
                                        {renderParameterControl('epsilon_min', hyperparameters.dqn.epsilon_min, 0.001, 0.1, 0.001)}
                                        <div className="parameter-control">
                                            <div className="parameter-header">
                                                <label>batch_size</label>
                                                <span className="parameter-value">{hyperparameters.dqn.batch_size}</span>
                                            </div>
                                            <input
                                                type="range"
                                                min={16}
                                                max={128}
                                                step={16}
                                                value={hyperparameters.dqn.batch_size}
                                                onChange={(e) => updateHyperparameter('batch_size', parseInt(e.target.value))}
                                                className="parameter-slider"
                                            />
                                            <div className="parameter-description">批次大小 - 每次訓練使用的樣本數量</div>
                                        </div>
                                        <div className="parameter-control">
                                            <div className="parameter-header">
                                                <label>memory_size</label>
                                                <span className="parameter-value">{hyperparameters.dqn.memory_size}</span>
                                            </div>
                                            <input
                                                type="range"
                                                min={5000}
                                                max={50000}
                                                step={5000}
                                                value={hyperparameters.dqn.memory_size}
                                                onChange={(e) => updateHyperparameter('memory_size', parseInt(e.target.value))}
                                                className="parameter-slider"
                                            />
                                            <div className="parameter-description">記憶體大小 - 經驗回放緩衝區的容量</div>
                                        </div>
                                        <div className="parameter-control">
                                            <div className="parameter-header">
                                                <label>target_update_freq</label>
                                                <span className="parameter-value">{hyperparameters.dqn.target_update_freq}</span>
                                            </div>
                                            <input
                                                type="range"
                                                min={10}
                                                max={1000}
                                                step={10}
                                                value={hyperparameters.dqn.target_update_freq}
                                                onChange={(e) => updateHyperparameter('target_update_freq', parseInt(e.target.value))}
                                                className="parameter-slider"
                                            />
                                            <div className="parameter-description">目標網絡更新頻率 - 每多少步更新一次目標網絡</div>
                                        </div>
                                        {renderParameterControl('gamma', hyperparameters.dqn.gamma, 0.9, 0.999, 0.001)}
                                    </>
                                )}
                                
                                {selectedAlgorithm === 'ppo' && (
                                    <>
                                        {renderParameterControl('learning_rate', hyperparameters.ppo.learning_rate, 0.0001, 0.01, 0.0001)}
                                        {renderParameterControl('clip_range', hyperparameters.ppo.clip_range, 0.1, 0.5, 0.01)}
                                        {renderParameterControl('value_function_coef', hyperparameters.ppo.value_function_coef, 0.1, 1.0, 0.1)}
                                        {renderParameterControl('entropy_coef', hyperparameters.ppo.entropy_coef, 0.001, 0.1, 0.001)}
                                        {renderParameterControl('gae_lambda', hyperparameters.ppo.gae_lambda, 0.8, 0.99, 0.01)}
                                        {renderParameterControl('max_grad_norm', hyperparameters.ppo.max_grad_norm, 0.1, 2.0, 0.1)}
                                        <div className="parameter-control">
                                            <div className="parameter-header">
                                                <label>batch_size</label>
                                                <span className="parameter-value">{hyperparameters.ppo.batch_size}</span>
                                            </div>
                                            <input
                                                type="range"
                                                min={32}
                                                max={256}
                                                step={32}
                                                value={hyperparameters.ppo.batch_size}
                                                onChange={(e) => updateHyperparameter('batch_size', parseInt(e.target.value))}
                                                className="parameter-slider"
                                            />
                                            <div className="parameter-description">批次大小 - 每次訓練使用的樣本數量</div>
                                        </div>
                                        {renderParameterControl('gamma', hyperparameters.ppo.gamma, 0.9, 0.999, 0.001)}
                                    </>
                                )}
                                
                                {selectedAlgorithm === 'sac' && (
                                    <>
                                        {renderParameterControl('learning_rate', hyperparameters.sac.learning_rate, 0.0001, 0.01, 0.0001)}
                                        {renderParameterControl('alpha', hyperparameters.sac.alpha, 0.01, 1.0, 0.01)}
                                        {renderParameterControl('target_entropy', hyperparameters.sac.target_entropy, -10.0, 0.0, 0.1)}
                                        {renderParameterControl('tau', hyperparameters.sac.tau, 0.001, 0.1, 0.001)}
                                        <div className="parameter-control">
                                            <div className="parameter-header">
                                                <label>batch_size</label>
                                                <span className="parameter-value">{hyperparameters.sac.batch_size}</span>
                                            </div>
                                            <input
                                                type="range"
                                                min={64}
                                                max={512}
                                                step={64}
                                                value={hyperparameters.sac.batch_size}
                                                onChange={(e) => updateHyperparameter('batch_size', parseInt(e.target.value))}
                                                className="parameter-slider"
                                            />
                                            <div className="parameter-description">批次大小 - 每次訓練使用的樣本數量</div>
                                        </div>
                                        <div className="parameter-control">
                                            <div className="parameter-header">
                                                <label>buffer_size</label>
                                                <span className="parameter-value">{hyperparameters.sac.buffer_size}</span>
                                            </div>
                                            <input
                                                type="range"
                                                min={10000}
                                                max={100000}
                                                step={10000}
                                                value={hyperparameters.sac.buffer_size}
                                                onChange={(e) => updateHyperparameter('buffer_size', parseInt(e.target.value))}
                                                className="parameter-slider"
                                            />
                                            <div className="parameter-description">緩衝區大小 - 經驗回放緩衝區的容量</div>
                                        </div>
                                        {renderParameterControl('gamma', hyperparameters.sac.gamma, 0.9, 0.999, 0.001)}
                                    </>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'environment' && (
                        <div className="environment-panel">
                            <h3>🌐 環境參數</h3>
                            <div className="parameters-grid">
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>satellite_visibility_threshold</label>
                                        <span className="parameter-value">{environmentParams.satellite_visibility_threshold}°</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={5}
                                        max={30}
                                        step={1}
                                        value={environmentParams.satellite_visibility_threshold}
                                        onChange={(e) => updateEnvironmentParam('satellite_visibility_threshold', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">衛星可見性閾值 - 衛星仰角低於此值時不可見</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>signal_quality_weight</label>
                                        <span className="parameter-value">{environmentParams.signal_quality_weight}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0.1}
                                        max={1.0}
                                        step={0.1}
                                        value={environmentParams.signal_quality_weight}
                                        onChange={(e) => updateEnvironmentParam('signal_quality_weight', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">信號質量權重 - 信號質量在決策中的重要性</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>load_balancing_weight</label>
                                        <span className="parameter-value">{environmentParams.load_balancing_weight}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0.1}
                                        max={1.0}
                                        step={0.1}
                                        value={environmentParams.load_balancing_weight}
                                        onChange={(e) => updateEnvironmentParam('load_balancing_weight', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">負載均衡權重 - 負載均衡在決策中的重要性</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>handover_penalty</label>
                                        <span className="parameter-value">{environmentParams.handover_penalty}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={-20}
                                        max={0}
                                        step={1}
                                        value={environmentParams.handover_penalty}
                                        onChange={(e) => updateEnvironmentParam('handover_penalty', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">換手懲罰 - 每次換手的基礎懲罰</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>stability_bonus</label>
                                        <span className="parameter-value">{environmentParams.stability_bonus}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0}
                                        max={50}
                                        step={5}
                                        value={environmentParams.stability_bonus}
                                        onChange={(e) => updateEnvironmentParam('stability_bonus', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">穩定性獎勵 - 維持穩定連接的獎勵</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>ping_pong_penalty</label>
                                        <span className="parameter-value">{environmentParams.ping_pong_penalty}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={-50}
                                        max={0}
                                        step={5}
                                        value={environmentParams.ping_pong_penalty}
                                        onChange={(e) => updateEnvironmentParam('ping_pong_penalty', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">乒乓效應懲罰 - 頻繁往返換手的懲罰</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>reward_scaling</label>
                                        <span className="parameter-value">{environmentParams.reward_scaling}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0.1}
                                        max={5.0}
                                        step={0.1}
                                        value={environmentParams.reward_scaling}
                                        onChange={(e) => updateEnvironmentParam('reward_scaling', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">獎勵縮放 - 所有獎勵的縮放因子</div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'reward' && (
                        <div className="reward-panel">
                            <h3>🎯 獎勵函數</h3>
                            <div className="parameters-grid">
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>successful_handover_bonus</label>
                                        <span className="parameter-value">{rewardFunction.successful_handover_bonus}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0}
                                        max={200}
                                        step={10}
                                        value={rewardFunction.successful_handover_bonus}
                                        onChange={(e) => updateRewardParam('successful_handover_bonus', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">成功換手獎勵 - 成功換手到更好衛星的獎勵</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>stable_connection_bonus</label>
                                        <span className="parameter-value">{rewardFunction.stable_connection_bonus}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0}
                                        max={100}
                                        step={5}
                                        value={rewardFunction.stable_connection_bonus}
                                        onChange={(e) => updateRewardParam('stable_connection_bonus', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">穩定連接獎勵 - 維持穩定連接的獎勵</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>poor_handover_penalty</label>
                                        <span className="parameter-value">{rewardFunction.poor_handover_penalty}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={-100}
                                        max={0}
                                        step={5}
                                        value={rewardFunction.poor_handover_penalty}
                                        onChange={(e) => updateRewardParam('poor_handover_penalty', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">糟糕換手懲罰 - 換手到更差衛星的懲罰</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>connection_loss_penalty</label>
                                        <span className="parameter-value">{rewardFunction.connection_loss_penalty}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={-200}
                                        max={0}
                                        step={10}
                                        value={rewardFunction.connection_loss_penalty}
                                        onChange={(e) => updateRewardParam('connection_loss_penalty', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">連接中斷懲罰 - 連接中斷的嚴重懲罰</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>frequent_handover_penalty</label>
                                        <span className="parameter-value">{rewardFunction.frequent_handover_penalty}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={-50}
                                        max={0}
                                        step={5}
                                        value={rewardFunction.frequent_handover_penalty}
                                        onChange={(e) => updateRewardParam('frequent_handover_penalty', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">頻繁換手懲罰 - 頻繁換手的懲罰</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>signal_quality_factor</label>
                                        <span className="parameter-value">{rewardFunction.signal_quality_factor}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0.1}
                                        max={1.0}
                                        step={0.1}
                                        value={rewardFunction.signal_quality_factor}
                                        onChange={(e) => updateRewardParam('signal_quality_factor', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">信號質量因子 - 信號質量對獎勵的影響係數</div>
                                </div>
                                <div className="parameter-control">
                                    <div className="parameter-header">
                                        <label>load_balancing_factor</label>
                                        <span className="parameter-value">{rewardFunction.load_balancing_factor}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={0.1}
                                        max={1.0}
                                        step={0.1}
                                        value={rewardFunction.load_balancing_factor}
                                        onChange={(e) => updateRewardParam('load_balancing_factor', parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-description">負載均衡因子 - 負載均衡對獎勵的影響係數</div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'optimization' && (
                        <div className="optimization-panel">
                            <h3>🚀 一鍵參數優化</h3>
                            <div className="optimization-description">
                                <p>
                                    使用貝葉斯優化算法自動尋找最佳參數組合，基於歷史訓練數據和性能指標進行智能調優。
                                </p>
                                <div className="optimization-features">
                                    <div className="feature-item">
                                        <span className="feature-icon">🎯</span>
                                        <span>自動超參數調優</span>
                                    </div>
                                    <div className="feature-item">
                                        <span className="feature-icon">📊</span>
                                        <span>性能指標優化</span>
                                    </div>
                                    <div className="feature-item">
                                        <span className="feature-icon">🔄</span>
                                        <span>迭代式改進</span>
                                    </div>
                                    <div className="feature-item">
                                        <span className="feature-icon">📈</span>
                                        <span>收斂性分析</span>
                                    </div>
                                </div>
                            </div>

                            {!isOptimizing && !optimizationResults && (
                                <div className="optimization-start">
                                    <div className="optimization-settings">
                                        <h4>優化設置</h4>
                                        <div className="settings-grid">
                                            <div className="setting-item">
                                                <label>目標算法:</label>
                                                <span className="setting-value">{selectedAlgorithm.toUpperCase()}</span>
                                            </div>
                                            <div className="setting-item">
                                                <label>優化目標:</label>
                                                <span className="setting-value">平均獎勵最大化</span>
                                            </div>
                                            <div className="setting-item">
                                                <label>最大迭代:</label>
                                                <span className="setting-value">50 次</span>
                                            </div>
                                            <div className="setting-item">
                                                <label>時間限制:</label>
                                                <span className="setting-value">1 小時</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <button
                                        className="btn btn-primary btn-large optimization-start-btn"
                                        onClick={optimizeParameters}
                                        disabled={isOptimizing}
                                    >
                                        🚀 開始優化
                                    </button>
                                </div>
                            )}

                            {isOptimizing && (
                                <div className="optimization-progress">
                                    <h4>🔄 優化進行中...</h4>
                                    <div className="progress-bar">
                                        <div 
                                            className="progress-fill"
                                            style={{ width: `${optimizationProgress}%` }}
                                        />
                                    </div>
                                    <div className="progress-text">
                                        進度: {optimizationProgress.toFixed(1)}%
                                    </div>
                                    <div className="optimization-status">
                                        <div className="status-item">
                                            <span className="status-icon">🎯</span>
                                            <span>正在尋找最佳參數組合...</span>
                                        </div>
                                        <div className="status-item">
                                            <span className="status-icon">📊</span>
                                            <span>評估性能指標...</span>
                                        </div>
                                        <div className="status-item">
                                            <span className="status-icon">🔄</span>
                                            <span>迭代優化中...</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {optimizationResults && (
                                <div className="optimization-results">
                                    <h4>✅ 優化完成</h4>
                                    <div className="results-summary">
                                        <div className="summary-item">
                                            <span className="summary-label">最佳性能:</span>
                                            <span className="summary-value">
                                                {(optimizationResults.best_score as number)?.toFixed(2) || 'N/A'}
                                            </span>
                                        </div>
                                        <div className="summary-item">
                                            <span className="summary-label">改進幅度:</span>
                                            <span className="summary-value">
                                                +{(((optimizationResults.improvement as number) || 0) * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                        <div className="summary-item">
                                            <span className="summary-label">優化迭代:</span>
                                            <span className="summary-value">
                                                {optimizationResults.iterations as number || 0} 次
                                            </span>
                                        </div>
                                        <div className="summary-item">
                                            <span className="summary-label">收斂時間:</span>
                                            <span className="summary-value">
                                                {((optimizationResults.convergence_time as number) || 0).toFixed(1)} 分鐘
                                            </span>
                                        </div>
                                    </div>

                                    <div className="optimized-parameters">
                                        <h5>🎯 優化後的參數</h5>
                                        <div className="parameter-comparison">
                                            <div className="comparison-section">
                                                <h6>超參數</h6>
                                                {Object.entries((optimizationResults.best_parameters as Record<string, unknown>)?.hyperparameters as Record<string, unknown> || {}).map(([key, value]) => (
                                                    <div key={key} className="parameter-item">
                                                        <span className="param-name">{key}:</span>
                                                        <span className="param-value">{String(value)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="comparison-section">
                                                <h6>環境參數</h6>
                                                {Object.entries((optimizationResults.best_parameters as Record<string, unknown>)?.environment as Record<string, unknown> || {}).map(([key, value]) => (
                                                    <div key={key} className="parameter-item">
                                                        <span className="param-name">{key}:</span>
                                                        <span className="param-value">{String(value)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="results-actions">
                                        <button
                                            className="btn btn-success btn-large"
                                            onClick={applyOptimizationResults}
                                            disabled={isApplying}
                                        >
                                            {isApplying ? '🔄 應用中...' : '✅ 應用優化結果'}
                                        </button>
                                        <button
                                            className="btn btn-secondary"
                                            onClick={() => setOptimizationResults(null)}
                                        >
                                            🔄 重新優化
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            <div className="apply-section">
                <div className="apply-info">
                    {lastApplied && (
                        <div className="last-applied">
                            ✅ 最後應用時間: {lastApplied.toLocaleTimeString()}
                        </div>
                    )}
                    <div className="apply-note">
                        ⚠️ 參數變更將在下次訓練開始時生效
                    </div>
                </div>
                <button
                    className="btn btn-primary btn-large apply-btn"
                    onClick={applyParameters}
                    disabled={isApplying}
                >
                    {isApplying ? '🔄 應用中...' : '✅ 應用參數'}
                </button>
            </div>
        </div>
    )
}

export default ParameterTuningSection