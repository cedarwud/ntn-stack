import React, { memo, useState, useCallback } from 'react'
import { netstackFetch } from '../../../config/api-config'
import './TrainingStatusSection.scss'

interface TrainingStatusSectionProps {
    data?: {
        training: {
            status: string
            progress: number
            algorithms: Array<{
                algorithm: string
                status: string
                progress: number
                training_active: boolean
                metrics: unknown
                session_id?: string
            }>
        }
    }
    onRefresh?: () => void
}

const TrainingStatusSection: React.FC<TrainingStatusSectionProps> = ({
    data,
    onRefresh,
}) => {
    const algorithms = data?.training?.algorithms || []
    const [isControlling, setIsControlling] = useState<{
        [key: string]: boolean
    }>({})
    const [showStartModal, setShowStartModal] = useState(false)
    const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('dqn')

    // 檢查是否有任何算法正在訓練（互斥控制）
    const hasActiveTraining = algorithms.some(
        (algo) => algo.training_active || algo.status === 'running'
    )

    // 簡化的狀態檢查 - 只需要檢查是否有活動訓練

    // 訓練控制函數
    const handleStartTraining = useCallback(
        async (algorithm: string) => {
            const controlKey = `start_${algorithm}`
            setIsControlling((prev) => ({ ...prev, [controlKey]: true }))

            console.log(`🚀 [前端] 開始啟動 ${algorithm.toUpperCase()} 訓練...`)

            try {
                const requestBody = {
                    experiment_name: `${algorithm}_training_${new Date()
                        .toISOString()
                        .slice(0, 19)}`,
                    total_episodes: 1000,
                    scenario_type: 'interference_mitigation',
                    hyperparameters: {
                        learning_rate:
                            algorithm === 'dqn'
                                ? 0.001
                                : algorithm === 'ppo'
                                ? 0.0003
                                : 0.0001,
                        batch_size:
                            algorithm === 'dqn'
                                ? 32
                                : algorithm === 'ppo'
                                ? 64
                                : 128,
                        gamma: 0.99,
                    },
                }

                console.log(
                    `📤 [前端] 發送訓練請求到: /api/v1/rl/training/start/${algorithm}`
                )
                console.log(`📤 [前端] 請求內容:`, requestBody)

                const response = await netstackFetch(
                    `/api/v1/rl/training/start/${algorithm}`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestBody),
                    }
                )

                console.log(
                    `📥 [前端] 收到響應狀態: ${response.status} ${response.statusText}`
                )

                if (response.ok) {
                    const responseData = await response.json()
                    console.log(
                        `✅ [前端] ${algorithm.toUpperCase()} 訓練啟動成功`,
                        responseData
                    )
                    console.log(`🔄 [前端] 調用 onRefresh 刷新數據...`)
                    onRefresh?.()

                    // 延遲檢查訓練狀態
                    setTimeout(async () => {
                        try {
                            console.log(
                                `🔍 [前端] 3秒後檢查 ${algorithm} 訓練狀態...`
                            )
                            const statusResponse = await netstackFetch(
                                `/api/v1/rl/training/status/${algorithm}`
                            )
                            const statusData = await statusResponse.json()
                            console.log(
                                `📊 [前端] ${algorithm} 當前狀態:`,
                                statusData
                            )
                        } catch (statusError) {
                            console.error(
                                `❌ [前端] 檢查 ${algorithm} 狀態失敗:`,
                                statusError
                            )
                        }
                    }, 3000)
                } else {
                    const errorText = await response.text()
                    console.error(
                        `❌ [前端] 啟動 ${algorithm.toUpperCase()} 訓練失敗:`,
                        errorText
                    )
                }
            } catch (error) {
                console.error(
                    `💥 [前端] 啟動 ${algorithm.toUpperCase()} 訓練發生異常:`,
                    error
                )
            } finally {
                setIsControlling((prev) => ({ ...prev, [controlKey]: false }))
            }
        },
        [onRefresh]
    )

    // 暫停功能已移除

    // 恢復功能已移除

    const handleStopTraining = useCallback(
        async (algorithm: string, _sessionId?: string) => {
            const controlKey = `stop_${algorithm}`

            // 防止重複點擊
            if (isControlling[controlKey]) {
                console.log(`${algorithm} 停止操作正在進行中，忽略重複點擊`)
                return
            }

            setIsControlling((prev) => ({ ...prev, [controlKey]: true }))

            try {
                console.log(
                    `⏹️ [前端] 開始停止 ${algorithm.toUpperCase()} 訓練...`
                )

                // 使用新的特定算法停止端點
                const response = await netstackFetch(
                    `/api/v1/rl/training/stop-algorithm/${algorithm}`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                    }
                )

                if (response.ok) {
                    const result = await response.json()
                    console.log(
                        `✅ ${algorithm.toUpperCase()} 訓練已停止:`,
                        result
                    )

                    // 等待一小段時間讓後端狀態更新
                    await new Promise((resolve) => setTimeout(resolve, 500))
                    onRefresh?.()
                } else {
                    const errorText = await response.text()
                    console.error(
                        `❌ 停止 ${algorithm.toUpperCase()} 訓練失敗:`,
                        errorText
                    )
                }
            } catch (error) {
                console.error(
                    `💥 停止 ${algorithm.toUpperCase()} 訓練發生異常:`,
                    error
                )
            } finally {
                // 延遲重置控制狀態，避免立即允許重複點擊
                setTimeout(() => {
                    setIsControlling((prev) => ({
                        ...prev,
                        [controlKey]: false,
                    }))
                }, 1000)
            }
        },
        [onRefresh, isControlling]
    )

    return (
        <div className="training-status-section">
            <div className="section-header">
                <h2 className="section-title">🎯 Training Status</h2>
                <div className="training-controls">
                    <button
                        className="btn btn-primary start-training-btn"
                        onClick={() => setShowStartModal(true)}
                        disabled={data?.training?.status === 'running'}
                    >
                        <span className="btn-icon">🚀</span>
                        <span className="btn-text">開始訓練</span>
                    </button>
                </div>
            </div>

            <div className="training-overview">
                <div className="status-card">
                    <div className="status-indicator">
                        <span
                            className={`status-dot ${
                                data?.training?.status || 'idle'
                            }`}
                        ></span>
                        <span className="status-text">
                            {data?.training?.status === 'running'
                                ? 'Training Active'
                                : 'System Ready'}
                        </span>
                    </div>
                    <div className="progress-info">
                        <div className="progress-bar">
                            <div
                                className="progress-fill"
                                style={{
                                    width: `${
                                        (data?.training?.progress || 0) * 100
                                    }%`,
                                }}
                            ></div>
                        </div>
                        <span className="progress-text">
                            {((data?.training?.progress || 0) * 100).toFixed(1)}
                            %
                        </span>
                    </div>
                </div>
            </div>

            <div className="algorithms-grid">
                {algorithms.length === 0 ? (
                    <div className="no-algorithms-message">
                        <div className="message-icon">🤖</div>
                        <div className="message-text">
                            No algorithms available
                        </div>
                        <div className="message-subtext">
                            Algorithms will appear here when training data is
                            loaded
                        </div>
                    </div>
                ) : (
                    algorithms.map((algo, index) => (
                        <div key={index} className="algorithm-card">
                            <div className="algorithm-header">
                                <h3 className="algorithm-name">
                                    {algo.algorithm.toUpperCase()}
                                </h3>
                                <span
                                    className={`algorithm-status ${algo.status}`}
                                >
                                    {algo.training_active
                                        ? '🔄 Training'
                                        : '⏸️ Idle'}
                                </span>
                            </div>
                            <div className="algorithm-metrics">
                                <div className="metric">
                                    <span className="metric-label">
                                        Progress:
                                    </span>
                                    <span className="metric-value">
                                        {(algo.progress * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="metric">
                                    <span className="metric-label">
                                        當前回合:
                                    </span>
                                    <span className="metric-value">
                                        {algo.training_progress
                                            ?.current_episode || 0}{' '}
                                        /{' '}
                                        {algo.training_progress
                                            ?.total_episodes || 1000}
                                        <span
                                            className="episode-status"
                                            title="訓練狀態"
                                        >
                                            {algo.training_active ? '🔄' : '⏸️'}
                                        </span>
                                    </span>
                                </div>
                                <div className="metric">
                                    <span className="metric-label">
                                        平均獎勵:
                                    </span>
                                    <span className="metric-value">
                                        {algo.metrics?.average_reward
                                            ? algo.metrics.average_reward.toFixed(
                                                  2
                                              )
                                            : '0.00'}
                                        {algo.metrics?.performance_trend && (
                                            <span
                                                className="trend-indicator"
                                                title={`學習趨勢: ${algo.metrics.performance_trend}`}
                                            >
                                                {algo.metrics
                                                    .performance_trend ===
                                                'improving'
                                                    ? '📈'
                                                    : algo.metrics
                                                          .performance_trend ===
                                                      'stable'
                                                    ? '➡️'
                                                    : algo.metrics
                                                          .performance_trend ===
                                                      'declining'
                                                    ? '📉'
                                                    : '❓'}
                                            </span>
                                        )}
                                    </span>
                                </div>
                                {algo.metrics?.learning_efficiency !==
                                    undefined && (
                                    <div className="metric">
                                        <span className="metric-label">
                                            Learning Efficiency:
                                        </span>
                                        <span className="metric-value">
                                            {(
                                                (algo.metrics
                                                    .learning_efficiency || 0) *
                                                100
                                            ).toFixed(1)}
                                            %
                                        </span>
                                    </div>
                                )}
                            </div>
                            <div
                                className="algorithm-controls"
                                style={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    gap: '8px',
                                }}
                            >
                                {!algo.training_active ? (
                                    // 顯示開始按鈕（當沒有訓練活動）
                                    <button
                                        className="btn btn-sm btn-success"
                                        onClick={() =>
                                            handleStartTraining(algo.algorithm)
                                        }
                                        disabled={
                                            isControlling[
                                                `start_${algo.algorithm}`
                                            ] || hasActiveTraining
                                        }
                                        title={
                                            hasActiveTraining
                                                ? '其他算法正在訓練中，請先停止後再開始'
                                                : '開始訓練'
                                        }
                                    >
                                        {isControlling[
                                            `start_${algo.algorithm}`
                                        ]
                                            ? '🔄'
                                            : '▶️'}{' '}
                                        開始
                                    </button>
                                ) : (
                                    // 顯示停止按鈕（當有活動訓練）
                                    <button
                                        className="btn btn-sm btn-danger"
                                        onClick={() =>
                                            handleStopTraining(
                                                algo.algorithm,
                                                algo.session_id
                                            )
                                        }
                                        disabled={
                                            isControlling[
                                                `stop_${algo.algorithm}`
                                            ]
                                        }
                                        title="停止訓練"
                                    >
                                        {isControlling[`stop_${algo.algorithm}`]
                                            ? '🔄'
                                            : '⏹️'}{' '}
                                        停止
                                    </button>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* 開始訓練彈窗 */}
            {showStartModal && (
                <div
                    className="modal-overlay"
                    onClick={() => setShowStartModal(false)}
                >
                    <div
                        className="modal-content"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3>🚀 開始 RL 訓練</h3>
                            <button
                                className="modal-close"
                                onClick={() => setShowStartModal(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label htmlFor="algorithm-select">
                                    選擇算法:
                                </label>
                                <select
                                    id="algorithm-select"
                                    value={selectedAlgorithm}
                                    onChange={(e) =>
                                        setSelectedAlgorithm(e.target.value)
                                    }
                                    className="form-select"
                                >
                                    <option value="dqn">
                                        DQN - Deep Q-Network
                                    </option>
                                    <option value="ppo">
                                        PPO - Proximal Policy Optimization
                                    </option>
                                    <option value="sac">
                                        SAC - Soft Actor-Critic
                                    </option>
                                </select>
                            </div>
                            <div className="algorithm-info">
                                {selectedAlgorithm === 'dqn' && (
                                    <div className="info-card">
                                        <h4>🧠 DQN 特性</h4>
                                        <ul>
                                            <li>經典深度強化學習算法</li>
                                            <li>適合離散動作空間</li>
                                            <li>學習率: 0.001, Batch: 32</li>
                                        </ul>
                                    </div>
                                )}
                                {selectedAlgorithm === 'ppo' && (
                                    <div className="info-card">
                                        <h4>🎯 PPO 特性</h4>
                                        <ul>
                                            <li>策略梯度算法，穩定性高</li>
                                            <li>適合連續控制問題</li>
                                            <li>學習率: 0.0003, Batch: 64</li>
                                        </ul>
                                    </div>
                                )}
                                {selectedAlgorithm === 'sac' && (
                                    <div className="info-card">
                                        <h4>⚡ SAC 特性</h4>
                                        <ul>
                                            <li>基於最大熵的Actor-Critic</li>
                                            <li>高效樣本利用率</li>
                                            <li>學習率: 0.0001, Batch: 128</li>
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button
                                className="btn btn-secondary"
                                onClick={() => setShowStartModal(false)}
                            >
                                取消
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => {
                                    handleStartTraining(selectedAlgorithm)
                                    setShowStartModal(false)
                                }}
                                disabled={
                                    isControlling[`start_${selectedAlgorithm}`]
                                }
                            >
                                {isControlling[`start_${selectedAlgorithm}`]
                                    ? '🔄 啟動中...'
                                    : '🚀 開始訓練'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default memo(TrainingStatusSection)
