import React, { useState, useEffect } from 'react'
import './TrainingAnalysisSection.scss'

interface TrainingAnalysisProps {
    data: any
    onRefresh?: () => void
}

interface ParameterConfig {
    name: string
    value: number
    min: number
    max: number
    step: number
    description: string
    impact: string
}

const TrainingAnalysisSection: React.FC<TrainingAnalysisProps> = ({
    data,
    onRefresh
}) => {
    const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('dqn')
    const [showParameterConfig, setShowParameterConfig] = useState(false)
    const [parameters, setParameters] = useState<ParameterConfig[]>([
        {
            name: 'learning_rate',
            value: 0.001,
            min: 0.0001,
            max: 0.01,
            step: 0.0001,
            description: '學習率',
            impact: '控制模型學習速度。太高可能不穩定，太低學習緩慢。'
        },
        {
            name: 'batch_size',
            value: 32,
            min: 8,
            max: 256,
            step: 8,
            description: '批次大小',
            impact: '影響訓練穩定性和記憶體使用。大批次更穩定但需要更多記憶體。'
        },
        {
            name: 'gamma',
            value: 0.99,
            min: 0.9,
            max: 0.999,
            step: 0.001,
            description: '折扣因子',
            impact: '控制對未來獎勵的重視程度。接近1重視長期，接近0重視短期。'
        },
        {
            name: 'epsilon',
            value: 0.1,
            min: 0.01,
            max: 1.0,
            step: 0.01,
            description: '探索率',
            impact: '控制探索vs利用平衡。高值多探索，低值多利用已知策略。'
        }
    ])

    const algorithmInfo = {
        dqn: {
            name: 'Deep Q-Network',
            description: '基於深度神經網路的Q學習算法',
            strengths: ['適合離散動作空間', '學習穩定', '理論基礎扎實'],
            weaknesses: ['可能過估計Q值', '需要經驗回放', '對超參數敏感'],
            useCase: '適用於衛星選擇等離散決策問題'
        },
        ppo: {
            name: 'Proximal Policy Optimization',
            description: '策略梯度算法，具有良好的穩定性',
            strengths: ['訓練穩定', '樣本效率高', '適合連續控制'],
            weaknesses: ['調參複雜', '計算開銷大', '收斂可能較慢'],
            useCase: '適用於複雜的換手策略優化'
        },
        sac: {
            name: 'Soft Actor-Critic',
            description: '基於最大熵的Actor-Critic算法',
            strengths: ['樣本效率極高', '探索能力強', '適合連續動作'],
            weaknesses: ['實現複雜', '超參數多', '理論理解困難'],
            useCase: '適用於高維連續控制問題'
        }
    }

    const trainingMetrics = {
        handover_success_rate: '換手成功率',
        signal_quality_improvement: '信號品質提升',
        latency_reduction: '延遲降低',
        load_balancing_efficiency: '負載均衡效率',
        qos_maintenance: 'QoS維持率',
        energy_efficiency: '能耗效率'
    }

    const handleParameterChange = (index: number, value: number) => {
        const newParameters = [...parameters]
        newParameters[index].value = value
        setParameters(newParameters)
    }

    const applyParameterChanges = () => {
        // TODO: 實際應用參數變更到後端
        console.log('應用參數變更:', parameters)
        setShowParameterConfig(false)
    }

    return (
        <div className="training-analysis-section">
            <div className="section-header">
                <h2>🧠 訓練分析與配置</h2>
                <div className="header-controls">
                    <select
                        value={selectedAlgorithm}
                        onChange={(e) => setSelectedAlgorithm(e.target.value)}
                        className="algorithm-selector"
                    >
                        <option value="dqn">DQN</option>
                        <option value="ppo">PPO</option>
                        <option value="sac">SAC</option>
                    </select>
                    <button
                        className="btn btn-primary"
                        onClick={() => setShowParameterConfig(true)}
                    >
                        ⚙️ 參數配置
                    </button>
                </div>
            </div>

            {/* 算法資訊 */}
            <div className="algorithm-info-card">
                <h3>📚 {algorithmInfo[selectedAlgorithm as keyof typeof algorithmInfo].name}</h3>
                <p>{algorithmInfo[selectedAlgorithm as keyof typeof algorithmInfo].description}</p>
                
                <div className="info-grid">
                    <div className="info-column">
                        <h4>✅ 優勢</h4>
                        <ul>
                            {algorithmInfo[selectedAlgorithm as keyof typeof algorithmInfo].strengths.map((strength, index) => (
                                <li key={index}>{strength}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="info-column">
                        <h4>⚠️ 限制</h4>
                        <ul>
                            {algorithmInfo[selectedAlgorithm as keyof typeof algorithmInfo].weaknesses.map((weakness, index) => (
                                <li key={index}>{weakness}</li>
                            ))}
                        </ul>
                    </div>
                </div>
                
                <div className="use-case">
                    <h4>🎯 應用場景</h4>
                    <p>{algorithmInfo[selectedAlgorithm as keyof typeof algorithmInfo].useCase}</p>
                </div>
            </div>

            {/* 訓練目標說明 */}
            <div className="training-objectives">
                <h3>🎯 訓練目標與指標</h3>
                <div className="objectives-grid">
                    {Object.entries(trainingMetrics).map(([key, label]) => (
                        <div key={key} className="objective-card">
                            <h4>{label}</h4>
                            <div className="metric-explanation">
                                {key === 'handover_success_rate' && (
                                    <p>衡量算法選擇的換手決策成功率，基於信號品質改善和連接穩定性。</p>
                                )}
                                {key === 'signal_quality_improvement' && (
                                    <p>換手後RSRP/RSRQ/SINR等信號指標的改善程度。</p>
                                )}
                                {key === 'latency_reduction' && (
                                    <p>換手過程中的延遲降低，包括決策時間和執行時間。</p>
                                )}
                                {key === 'load_balancing_efficiency' && (
                                    <p>在多顆衛星間均勻分配負載的效率。</p>
                                )}
                                {key === 'qos_maintenance' && (
                                    <p>換手過程中維持服務品質的能力。</p>
                                )}
                                {key === 'energy_efficiency' && (
                                    <p>換手決策對終端設備能耗的影響。</p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 真實數據說明 */}
            <div className="data-source-info">
                <h3>🛰️ 訓練數據來源</h3>
                <div className="data-grid">
                    <div className="data-card">
                        <h4>📡 衛星軌道數據</h4>
                        <ul>
                            <li>真實TLE (Two-Line Element) 數據</li>
                            <li>實時軌道位置計算</li>
                            <li>可見性預測</li>
                        </ul>
                    </div>
                    <div className="data-card">
                        <h4>📶 信號傳播模型</h4>
                        <ul>
                            <li>自由空間路徑損耗</li>
                            <li>大氣衰減模型</li>
                            <li>陰影衰落效應</li>
                        </ul>
                    </div>
                    <div className="data-card">
                        <h4>🌍 環境場景</h4>
                        <ul>
                            <li>都市、郊區、鄉村環境</li>
                            <li>不同移動速度</li>
                            <li>負載變化模式</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* 參數配置彈窗 */}
            {showParameterConfig && (
                <div className="modal-overlay" onClick={() => setShowParameterConfig(false)}>
                    <div className="modal-content parameter-config-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>⚙️ 訓練參數配置</h3>
                            <button
                                className="modal-close"
                                onClick={() => setShowParameterConfig(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="modal-body">
                            {parameters.map((param, index) => (
                                <div key={param.name} className="parameter-item">
                                    <div className="parameter-header">
                                        <label>{param.description}</label>
                                        <span className="parameter-value">{param.value}</span>
                                    </div>
                                    <input
                                        type="range"
                                        min={param.min}
                                        max={param.max}
                                        step={param.step}
                                        value={param.value}
                                        onChange={(e) => handleParameterChange(index, parseFloat(e.target.value))}
                                        className="parameter-slider"
                                    />
                                    <div className="parameter-range">
                                        <span>{param.min}</span>
                                        <span>{param.max}</span>
                                    </div>
                                    <p className="parameter-impact">{param.impact}</p>
                                </div>
                            ))}
                        </div>
                        <div className="modal-footer">
                            <button
                                className="btn btn-secondary"
                                onClick={() => setShowParameterConfig(false)}
                            >
                                取消
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={applyParameterChanges}
                            >
                                應用變更
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default TrainingAnalysisSection
