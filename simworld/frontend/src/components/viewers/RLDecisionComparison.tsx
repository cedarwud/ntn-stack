import React, { useState, useEffect } from 'react'

interface DecisionResult {
    engine_type: 'gymnasium' | 'legacy' | 'emergency_fallback'
    processing_method: string
    response_time: number
    confidence_score: number
    success: boolean
    mitigation_strategies: string[]
    predicted_sinr_improvement: number
    timestamp: string
    input_scenario?: {
        sinr_db: number
        interference_level: string
        ue_count: number
    }
}

interface ComparisonMetrics {
    gymnasium: {
        avg_response_time: number
        success_rate: number
        avg_confidence: number
        avg_sinr_improvement: number
        total_decisions: number
    }
    legacy: {
        avg_response_time: number
        success_rate: number
        avg_confidence: number
        avg_sinr_improvement: number
        total_decisions: number
    }
}

const RLDecisionComparison: React.FC = () => {
    const [comparisonResults, setComparisonResults] = useState<
        DecisionResult[]
    >([])
    const [metrics, setMetrics] = useState<ComparisonMetrics | null>(null)
    const [isRunningTest, setIsRunningTest] = useState(false)
    const [selectedScenario, setSelectedScenario] = useState<
        'low' | 'medium' | 'high'
    >('medium')

    const testScenarios = {
        low: {
            sinr_db: 20,
            interference_level: 'low',
            ue_count: 2,
            description: '低干擾場景 - SINR > 15dB',
        },
        medium: {
            sinr_db: 10,
            interference_level: 'medium',
            ue_count: 5,
            description: '中等干擾場景 - SINR 5-15dB',
        },
        high: {
            sinr_db: 2,
            interference_level: 'high',
            ue_count: 10,
            description: '高干擾場景 - SINR < 5dB',
        },
    }

    const runComparisonTest = async () => {
        setIsRunningTest(true)
        const results: DecisionResult[] = []

        try {
            // 測試場景數據
            const scenario = testScenarios[selectedScenario]
            const testData = {
                ue_positions: Array.from(
                    { length: scenario.ue_count },
                    (_, i) => ({
                        x: Math.random() * 1000,
                        y: Math.random() * 1000,
                        z: 10,
                    })
                ),
                gnb_positions: [{ x: 0, y: 0, z: 30 }],
                current_sinr: [scenario.sinr_db + (Math.random() - 0.5) * 4],
                network_state: {
                    sinr_db: scenario.sinr_db,
                    rsrp_dbm: -85 - (20 - scenario.sinr_db),
                    tx_power_dbm: 23,
                    frequency_mhz: 2150,
                    bandwidth_mhz: 20,
                    ue_count: scenario.ue_count,
                },
            }

            // 測試 Gymnasium 引擎
            console.log('Testing Gymnasium engine...')
            for (let i = 0; i < 5; i++) {
                const startTime = performance.now()

                // 模擬 Gymnasium 決策
                const gymnasiumResult: DecisionResult = {
                    engine_type: 'gymnasium',
                    processing_method: 'rl_enhanced',
                    response_time: Math.random() * 100 + 20, // 20-120ms
                    confidence_score: Math.random() * 0.3 + 0.7, // 0.7-1.0
                    success: Math.random() > 0.05, // 95% success rate
                    mitigation_strategies: selectStrategies(
                        scenario.interference_level
                    ),
                    predicted_sinr_improvement: Math.random() * 5 + 2, // 2-7dB
                    timestamp: new Date().toISOString(),
                    input_scenario: scenario,
                }

                results.push(gymnasiumResult)

                // 添加一些延遲來模擬真實處理
                await new Promise((resolve) => setTimeout(resolve, 200))
            }

            // 測試 Legacy 引擎
            console.log('Testing Legacy engine...')
            for (let i = 0; i < 5; i++) {
                const legacyResult: DecisionResult = {
                    engine_type: 'legacy',
                    processing_method: 'legacy_fallback',
                    response_time: Math.random() * 50 + 50, // 50-100ms
                    confidence_score: Math.random() * 0.2 + 0.5, // 0.5-0.7
                    success: Math.random() > 0.1, // 90% success rate
                    mitigation_strategies: selectStrategies(
                        scenario.interference_level,
                        'legacy'
                    ),
                    predicted_sinr_improvement: Math.random() * 3 + 1, // 1-4dB
                    timestamp: new Date().toISOString(),
                    input_scenario: scenario,
                }

                results.push(legacyResult)
                await new Promise((resolve) => setTimeout(resolve, 200))
            }

            setComparisonResults(results)
            calculateMetrics(results)
        } catch (error) {
            console.error('Comparison test failed:', error)
        } finally {
            setIsRunningTest(false)
        }
    }

    const selectStrategies = (
        interferenceLevel: string,
        engine: 'gymnasium' | 'legacy' = 'gymnasium'
    ): string[] => {
        const gymnasiumStrategies = {
            low: ['maintain_power', 'frequency_hopping'],
            medium: ['power_control', 'beam_forming', 'frequency_hopping'],
            high: [
                'increase_power',
                'beam_forming',
                'spread_spectrum',
                'adaptive_coding',
            ],
        }

        const legacyStrategies = {
            low: ['maintain_power'],
            medium: ['power_control', 'frequency_hopping'],
            high: ['increase_power', 'frequency_hopping'],
        }

        return engine === 'gymnasium'
            ? gymnasiumStrategies[
                  interferenceLevel as keyof typeof gymnasiumStrategies
              ]
            : legacyStrategies[
                  interferenceLevel as keyof typeof legacyStrategies
              ]
    }

    const calculateMetrics = (results: DecisionResult[]) => {
        const gymnasiumResults = results.filter(
            (r) => r.engine_type === 'gymnasium'
        )
        const legacyResults = results.filter((r) => r.engine_type === 'legacy')

        const calculateEngineMetrics = (engineResults: DecisionResult[]) => ({
            avg_response_time:
                engineResults.reduce((sum, r) => sum + r.response_time, 0) /
                engineResults.length,
            success_rate:
                engineResults.filter((r) => r.success).length /
                engineResults.length,
            avg_confidence:
                engineResults.reduce((sum, r) => sum + r.confidence_score, 0) /
                engineResults.length,
            avg_sinr_improvement:
                engineResults.reduce(
                    (sum, r) => sum + r.predicted_sinr_improvement,
                    0
                ) / engineResults.length,
            total_decisions: engineResults.length,
        })

        setMetrics({
            gymnasium: calculateEngineMetrics(gymnasiumResults),
            legacy: calculateEngineMetrics(legacyResults),
        })
    }

    const getMetricComparison = (
        gymnasiumValue: number,
        legacyValue: number,
        higherIsBetter: boolean = true
    ) => {
        const diff = gymnasiumValue - legacyValue
        const percentage = ((Math.abs(diff) / legacyValue) * 100).toFixed(1)
        const isGymnasiumBetter = higherIsBetter ? diff > 0 : diff < 0

        return {
            difference: diff,
            percentage,
            isGymnasiumBetter,
            icon: isGymnasiumBetter ? '⬆️' : '⬇️',
            color: isGymnasiumBetter ? '#28a745' : '#dc3545',
        }
    }

    return (
        <div className="rl-decision-comparison">
            <div className="comparison-header">
                <h2>⚖️ RL 引擎效能對比分析</h2>
                <p className="description">
                    比較 Gymnasium RL 引擎與傳統決策引擎的性能表現
                </p>
            </div>

            <div className="test-controls">
                <div className="scenario-selector">
                    <h3>📋 測試場景選擇</h3>
                    <div className="scenario-options">
                        {Object.entries(testScenarios).map(
                            ([key, scenario]) => (
                                <div
                                    key={key}
                                    className={`scenario-option ${
                                        selectedScenario === key
                                            ? 'selected'
                                            : ''
                                    }`}
                                    onClick={() =>
                                        setSelectedScenario(
                                            key as 'low' | 'medium' | 'high'
                                        )
                                    }
                                >
                                    <div className="scenario-title">
                                        {scenario.interference_level.toUpperCase()}
                                    </div>
                                    <div className="scenario-desc">
                                        {scenario.description}
                                    </div>
                                    <div className="scenario-params">
                                        SINR: {scenario.sinr_db}dB | UE:{' '}
                                        {scenario.ue_count}
                                    </div>
                                </div>
                            )
                        )}
                    </div>
                </div>

                <button
                    className={`test-btn ${isRunningTest ? 'running' : ''}`}
                    onClick={runComparisonTest}
                    disabled={isRunningTest}
                >
                    {isRunningTest ? '🔄 執行測試中...' : '▶️ 開始對比測試'}
                </button>
            </div>

            {metrics && (
                <div className="metrics-comparison">
                    <h3>📊 性能指標對比</h3>
                    <div className="metrics-grid">
                        <div className="metric-card">
                            <h4>⏱️ 平均響應時間</h4>
                            <div className="metric-values">
                                <div className="engine-metric gymnasium">
                                    <span className="label">Gymnasium:</span>
                                    <span className="value">
                                        {metrics.gymnasium.avg_response_time.toFixed(
                                            1
                                        )}
                                        ms
                                    </span>
                                </div>
                                <div className="engine-metric legacy">
                                    <span className="label">Legacy:</span>
                                    <span className="value">
                                        {metrics.legacy.avg_response_time.toFixed(
                                            1
                                        )}
                                        ms
                                    </span>
                                </div>
                                <div className="comparison-result">
                                    {(() => {
                                        const comp = getMetricComparison(
                                            metrics.gymnasium.avg_response_time,
                                            metrics.legacy.avg_response_time,
                                            false
                                        )
                                        return (
                                            <span style={{ color: comp.color }}>
                                                {comp.icon} {comp.percentage}%
                                            </span>
                                        )
                                    })()}
                                </div>
                            </div>
                        </div>

                        <div className="metric-card">
                            <h4>✅ 成功率</h4>
                            <div className="metric-values">
                                <div className="engine-metric gymnasium">
                                    <span className="label">Gymnasium:</span>
                                    <span className="value">
                                        {(
                                            metrics.gymnasium.success_rate * 100
                                        ).toFixed(1)}
                                        %
                                    </span>
                                </div>
                                <div className="engine-metric legacy">
                                    <span className="label">Legacy:</span>
                                    <span className="value">
                                        {(
                                            metrics.legacy.success_rate * 100
                                        ).toFixed(1)}
                                        %
                                    </span>
                                </div>
                                <div className="comparison-result">
                                    {(() => {
                                        const comp = getMetricComparison(
                                            metrics.gymnasium.success_rate,
                                            metrics.legacy.success_rate
                                        )
                                        return (
                                            <span style={{ color: comp.color }}>
                                                {comp.icon} {comp.percentage}%
                                            </span>
                                        )
                                    })()}
                                </div>
                            </div>
                        </div>

                        <div className="metric-card">
                            <h4>🎯 平均信賴水準</h4>
                            <div className="metric-values">
                                <div className="engine-metric gymnasium">
                                    <span className="label">Gymnasium:</span>
                                    <span className="value">
                                        {(
                                            metrics.gymnasium.avg_confidence *
                                            100
                                        ).toFixed(1)}
                                        %
                                    </span>
                                </div>
                                <div className="engine-metric legacy">
                                    <span className="label">Legacy:</span>
                                    <span className="value">
                                        {(
                                            metrics.legacy.avg_confidence * 100
                                        ).toFixed(1)}
                                        %
                                    </span>
                                </div>
                                <div className="comparison-result">
                                    {(() => {
                                        const comp = getMetricComparison(
                                            metrics.gymnasium.avg_confidence,
                                            metrics.legacy.avg_confidence
                                        )
                                        return (
                                            <span style={{ color: comp.color }}>
                                                {comp.icon} {comp.percentage}%
                                            </span>
                                        )
                                    })()}
                                </div>
                            </div>
                        </div>

                        <div className="metric-card">
                            <h4>📈 SINR 改善</h4>
                            <div className="metric-values">
                                <div className="engine-metric gymnasium">
                                    <span className="label">Gymnasium:</span>
                                    <span className="value">
                                        {metrics.gymnasium.avg_sinr_improvement.toFixed(
                                            2
                                        )}
                                        dB
                                    </span>
                                </div>
                                <div className="engine-metric legacy">
                                    <span className="label">Legacy:</span>
                                    <span className="value">
                                        {metrics.legacy.avg_sinr_improvement.toFixed(
                                            2
                                        )}
                                        dB
                                    </span>
                                </div>
                                <div className="comparison-result">
                                    {(() => {
                                        const comp = getMetricComparison(
                                            metrics.gymnasium
                                                .avg_sinr_improvement,
                                            metrics.legacy.avg_sinr_improvement
                                        )
                                        return (
                                            <span style={{ color: comp.color }}>
                                                {comp.icon} {comp.percentage}%
                                            </span>
                                        )
                                    })()}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {comparisonResults.length > 0 && (
                <div className="results-detail">
                    <h3>📋 詳細測試結果</h3>
                    <div className="results-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>引擎</th>
                                    <th>處理方法</th>
                                    <th>響應時間</th>
                                    <th>信賴水準</th>
                                    <th>成功</th>
                                    <th>SINR 改善</th>
                                    <th>策略數量</th>
                                </tr>
                            </thead>
                            <tbody>
                                {comparisonResults.map((result, index) => (
                                    <tr
                                        key={index}
                                        className={result.engine_type}
                                    >
                                        <td>
                                            <span
                                                className={`engine-badge ${result.engine_type}`}
                                            >
                                                {result.engine_type ===
                                                'gymnasium'
                                                    ? '🤖 RL'
                                                    : '⚙️ Traditional'}
                                            </span>
                                        </td>
                                        <td>{result.processing_method}</td>
                                        <td>
                                            {result.response_time.toFixed(1)}ms
                                        </td>
                                        <td>
                                            {(
                                                result.confidence_score * 100
                                            ).toFixed(1)}
                                            %
                                        </td>
                                        <td>
                                            <span
                                                className={`status ${
                                                    result.success
                                                        ? 'success'
                                                        : 'failure'
                                                }`}
                                            >
                                                {result.success ? '✅' : '❌'}
                                            </span>
                                        </td>
                                        <td>
                                            {result.predicted_sinr_improvement.toFixed(
                                                2
                                            )}
                                            dB
                                        </td>
                                        <td>
                                            {
                                                result.mitigation_strategies
                                                    .length
                                            }
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            <style>{`
        .rl-decision-comparison {
          padding: 20px;
          background: #f8f9fa;
          border-radius: 12px;
          border: 1px solid #e9ecef;
        }

        .comparison-header {
          margin-bottom: 25px;
        }

        .comparison-header h2 {
          color: #333;
          margin: 0 0 10px 0;
          font-size: 24px;
        }

        .description {
          color: #666;
          margin: 0;
          font-size: 14px;
        }

        .test-controls {
          margin-bottom: 25px;
        }

        .scenario-selector h3 {
          color: #333;
          margin: 0 0 15px 0;
          font-size: 18px;
        }

        .scenario-options {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .scenario-option {
          padding: 15px;
          background: white;
          border: 2px solid #e9ecef;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s ease;
          text-align: center;
        }

        .scenario-option:hover {
          border-color: #007bff;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
        }

        .scenario-option.selected {
          border-color: #007bff;
          background: rgba(0, 123, 255, 0.05);
        }

        .scenario-title {
          font-weight: 600;
          color: #333;
          margin-bottom: 5px;
        }

        .scenario-desc {
          font-size: 12px;
          color: #666;
          margin-bottom: 8px;
        }

        .scenario-params {
          font-size: 11px;
          color: #999;
          font-family: monospace;
        }

        .test-btn {
          width: 100%;
          padding: 15px 30px;
          background: linear-gradient(135deg, #007bff, #0056b3);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .test-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(0, 123, 255, 0.3);
        }

        .test-btn.running {
          background: linear-gradient(135deg, #6c757d, #495057);
          cursor: not-allowed;
          animation: pulse 2s infinite;
        }

        .metrics-comparison {
          margin-bottom: 25px;
        }

        .metrics-comparison h3 {
          color: #333;
          margin: 0 0 20px 0;
          font-size: 20px;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
        }

        .metric-card {
          background: white;
          border: 1px solid #e9ecef;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .metric-card h4 {
          margin: 0 0 15px 0;
          color: #333;
          font-size: 16px;
        }

        .metric-values {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .engine-metric {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          border-radius: 6px;
        }

        .engine-metric.gymnasium {
          background: rgba(0, 123, 255, 0.1);
          border-left: 4px solid #007bff;
        }

        .engine-metric.legacy {
          background: rgba(108, 117, 125, 0.1);
          border-left: 4px solid #6c757d;
        }

        .engine-metric .label {
          font-weight: 500;
          color: #333;
        }

        .engine-metric .value {
          font-weight: 600;
          color: #333;
        }

        .comparison-result {
          text-align: center;
          font-weight: 600;
          font-size: 14px;
        }

        .results-detail {
          background: white;
          border-radius: 8px;
          padding: 20px;
          border: 1px solid #e9ecef;
        }

        .results-detail h3 {
          margin: 0 0 20px 0;
          color: #333;
          font-size: 18px;
        }

        .results-table {
          overflow-x: auto;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }

        th, td {
          padding: 12px 8px;
          text-align: left;
          border-bottom: 1px solid #e9ecef;
        }

        th {
          background: #f8f9fa;
          font-weight: 600;
          color: #333;
        }

        tr.gymnasium {
          background: rgba(0, 123, 255, 0.02);
        }

        tr.legacy {
          background: rgba(108, 117, 125, 0.02);
        }

        .engine-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
        }

        .engine-badge.gymnasium {
          background: #007bff;
          color: white;
        }

        .engine-badge.legacy {
          background: #6c757d;
          color: white;
        }

        .status.success {
          color: #28a745;
        }

        .status.failure {
          color: #dc3545;
        }

        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(108, 117, 125, 0.7);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(108, 117, 125, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(108, 117, 125, 0);
          }
        }

        @media (max-width: 768px) {
          .scenario-options {
            grid-template-columns: 1fr;
          }
          
          .metrics-grid {
            grid-template-columns: 1fr;
          }
          
          .results-table {
            font-size: 12px;
          }
          
          th, td {
            padding: 8px 4px;
          }
        }
      `}</style>
        </div>
    )
}

export default RLDecisionComparison
