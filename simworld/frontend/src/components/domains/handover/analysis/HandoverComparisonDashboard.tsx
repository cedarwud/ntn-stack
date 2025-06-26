import React, { useState, useEffect, useMemo } from 'react'
import './HandoverComparisonDashboard.scss'

interface HandoverComparisonDashboardProps {
    enabled: boolean
}

interface HandoverMetrics {
    method_id: string
    latency: number
    success_rate: number
    packet_loss: number
    throughput: number
    power_consumption: number
    prediction_accuracy: number
    handover_frequency: number
    signal_quality: number
    network_overhead: number
    user_satisfaction: number
}

interface ComparisonResult {
    traditional_metrics: HandoverMetrics
    accelerated_metrics: HandoverMetrics
    improvement_percentage: {
        latency: number
        success_rate: number
        packet_loss: number
        throughput: number
        power_consumption: number
        prediction_accuracy: number
    }
    timestamp: number
}

interface TestScenario {
    id: string
    name: string
    description: string
    mobility_pattern: string
    satellite_count: number
    ue_count: number
    duration: number
    status: 'pending' | 'running' | 'completed' | 'failed'
}

const HandoverComparisonDashboard: React.FC<
    HandoverComparisonDashboardProps
> = ({ enabled }) => {
    const [comparisonResults, setComparisonResults] = useState<
        ComparisonResult[]
    >([])
    const [currentTest, setCurrentTest] = useState<TestScenario | null>(null)
    const [selectedScenario, setSelectedScenario] =
        useState<string>('urban_mobility')
    const [isRunningTest, setIsRunningTest] = useState(false)
    const [testProgress, setTestProgress] = useState(0)
    const [selectedMetric, setSelectedMetric] = useState<string>('latency')

    // 測試場景定義
    const testScenarios: TestScenario[] = useMemo(
        () => [
            {
                id: 'urban_mobility',
                name: '城市移動場景',
                description: '高密度建築物，頻繁遮蔽',
                mobility_pattern: 'urban_random_walk',
                satellite_count: 12,
                ue_count: 8,
                duration: 300,
                status: 'pending',
            },
            {
                id: 'highway_mobility',
                name: '高速公路場景',
                description: '高速線性移動',
                mobility_pattern: 'linear_high_speed',
                satellite_count: 8,
                ue_count: 4,
                duration: 180,
                status: 'pending',
            },
            {
                id: 'rural_coverage',
                name: '偏遠地區場景',
                description: '低衛星密度覆蓋',
                mobility_pattern: 'stationary_sparse',
                satellite_count: 4,
                ue_count: 2,
                duration: 240,
                status: 'pending',
            },
            {
                id: 'emergency_response',
                name: '緊急救援場景',
                description: 'UAV密集作業環境',
                mobility_pattern: 'swarm_coordination',
                satellite_count: 16,
                ue_count: 12,
                duration: 360,
                status: 'pending',
            },
        ],
        []
    )

    // 生成模擬對比數據
    const generateComparisonData = (scenario: string): ComparisonResult => {
        const baseLatency =
            scenario === 'highway_mobility'
                ? 80
                : scenario === 'urban_mobility'
                ? 120
                : scenario === 'rural_coverage'
                ? 100
                : 140

        const traditional: HandoverMetrics = {
            method_id: 'traditional',
            latency: baseLatency + Math.random() * 40,
            success_rate: 85 + Math.random() * 10,
            packet_loss: 2 + Math.random() * 3,
            throughput: 180 + Math.random() * 40,
            power_consumption: 850 + Math.random() * 150,
            prediction_accuracy: 60 + Math.random() * 15,
            handover_frequency: 8 + Math.random() * 4,
            signal_quality: 70 + Math.random() * 15,
            network_overhead: 15 + Math.random() * 5,
            user_satisfaction: 3.2 + Math.random() * 0.8,
        }

        const accelerated: HandoverMetrics = {
            method_id: 'ml_prediction',
            latency: traditional.latency * 0.35, // 65% 延遲減少
            success_rate: Math.min(99, traditional.success_rate * 1.12), // 12% 成功率提升
            packet_loss: traditional.packet_loss * 0.4, // 60% 封包遺失減少
            throughput: traditional.throughput * 1.25, // 25% 吞吐量提升
            power_consumption: traditional.power_consumption * 0.78, // 22% 功耗減少
            prediction_accuracy: Math.min(
                98,
                traditional.prediction_accuracy * 1.45
            ), // 45% 預測精度提升
            handover_frequency: traditional.handover_frequency * 0.7, // 30% 換手頻率減少
            signal_quality: Math.min(95, traditional.signal_quality * 1.18), // 18% 信號品質提升
            network_overhead: traditional.network_overhead * 0.6, // 40% 網路開銷減少
            user_satisfaction: Math.min(
                5.0,
                traditional.user_satisfaction * 1.35
            ), // 35% 用戶滿意度提升
        }

        const improvement = {
            latency:
                ((traditional.latency - accelerated.latency) /
                    traditional.latency) *
                100,
            success_rate:
                ((accelerated.success_rate - traditional.success_rate) /
                    traditional.success_rate) *
                100,
            packet_loss:
                ((traditional.packet_loss - accelerated.packet_loss) /
                    traditional.packet_loss) *
                100,
            throughput:
                ((accelerated.throughput - traditional.throughput) /
                    traditional.throughput) *
                100,
            power_consumption:
                ((traditional.power_consumption -
                    accelerated.power_consumption) /
                    traditional.power_consumption) *
                100,
            prediction_accuracy:
                ((accelerated.prediction_accuracy -
                    traditional.prediction_accuracy) /
                    traditional.prediction_accuracy) *
                100,
        }

        return {
            traditional_metrics: traditional,
            accelerated_metrics: accelerated,
            improvement_percentage: improvement,
            timestamp: Date.now(),
        }
    }

    // 運行對比測試
    const runComparisonTest = async (scenarioId: string) => {
        const scenario = testScenarios.find((s) => s.id === scenarioId)
        if (!scenario) return

        setCurrentTest({ ...scenario, status: 'running' })
        setIsRunningTest(true)
        setTestProgress(0)

        // 模擬測試進度
        const testInterval = setInterval(() => {
            setTestProgress((prev) => {
                const newProgress = prev + 2
                if (newProgress >= 100) {
                    clearInterval(testInterval)

                    // 生成對比結果
                    const result = generateComparisonData(scenarioId)
                    setComparisonResults((prev) => [
                        result,
                        ...prev.slice(0, 9),
                    ])

                    setCurrentTest((prev) =>
                        prev ? { ...prev, status: 'completed' } : null
                    )
                    setIsRunningTest(false)
                    setTestProgress(100)

                    setTimeout(() => {
                        setCurrentTest(null)
                        setTestProgress(0)
                    }, 2000)

                    return 100
                }
                return newProgress
            })
        }, 100)
    }

    // 獲取最新對比結果
         
         
    const getLatestResult = (): ComparisonResult | null => {
        return comparisonResults.length > 0 ? comparisonResults[0] : null
    }

    // 獲取指標單位
         
         
    const getMetricUnit = (metric: string) => {
        const units = {
            latency: 'ms',
            success_rate: '%',
            packet_loss: '%',
            throughput: 'Mbps',
            power_consumption: 'mW',
            prediction_accuracy: '%',
            handover_frequency: '次/分',
            signal_quality: 'dB',
            network_overhead: '%',
            user_satisfaction: '/5',
        }
        return units[metric as keyof typeof units] || ''
    }

    // 獲取指標中文名稱
         
         
    const getMetricDisplayName = (metric: string) => {
        const names = {
            latency: '換手延遲',
            success_rate: '成功率',
            packet_loss: '封包遺失率',
            throughput: '吞吐量',
            power_consumption: '功耗',
            prediction_accuracy: '預測精度',
            handover_frequency: '換手頻率',
            signal_quality: '信號品質',
            network_overhead: '網路開銷',
            user_satisfaction: '用戶滿意度',
        }
        return names[metric as keyof typeof names] || metric
    }

    // 初始化模擬數據
    useEffect(() => {
        if (!enabled) return

        // 生成初始對比數據
        const initialResults = [
            generateComparisonData('urban_mobility'),
            generateComparisonData('highway_mobility'),
            generateComparisonData('rural_coverage'),
        ]
        setComparisonResults(initialResults)

        // 定期更新數據
        const updateInterval = setInterval(() => {
            if (!isRunningTest) {
                const randomScenario =
                    testScenarios[
                        Math.floor(Math.random() * testScenarios.length)
                    ]
                const newResult = generateComparisonData(randomScenario.id)
                setComparisonResults((prev) => [newResult, ...prev.slice(0, 9)])
            }
        }, 8000)

        return () => clearInterval(updateInterval)
    }, [enabled, isRunningTest, testScenarios])

    if (!enabled) return null

    const latestResult = getLatestResult()

    return (
        <div className="handover-comparison-dashboard">
            <div className="dashboard-header">
                <div className="header-info">
                    <h2>🏆 換手方法對比測試</h2>
                    <p>IEEE INFOCOM 2024 vs 傳統換手性能對比</p>
                </div>

                <div className="test-controls">
                    <select
                        value={selectedScenario}
                        onChange={(e) => setSelectedScenario(e.target.value)}
                        disabled={isRunningTest}
                    >
                        {testScenarios.map((scenario) => (
                            <option key={scenario.id} value={scenario.id}>
                                {scenario.name}
                            </option>
                        ))}
                    </select>

                    <button
                        className="run-test-btn"
                        onClick={() => runComparisonTest(selectedScenario)}
                        disabled={isRunningTest}
                    >
                        {isRunningTest ? '🔄 測試中...' : '▶️ 運行測試'}
                    </button>
                </div>
            </div>

            {currentTest && (
                <div className="current-test-status">
                    <div className="test-info">
                        <h3>🔬 {currentTest.name}</h3>
                        <p>{currentTest.description}</p>
                        <div className="test-params">
                            <span>衛星數: {currentTest.satellite_count}</span>
                            <span>UE數: {currentTest.ue_count}</span>
                            <span>時長: {currentTest.duration}s</span>
                        </div>
                    </div>

                    <div className="progress-container">
                        <div className="progress-bar">
                            <div
                                className="progress-fill"
                                style={{ width: `${testProgress}%` }}
                            ></div>
                        </div>
                        <span className="progress-text">
                            {testProgress.toFixed(0)}%
                        </span>
                    </div>
                </div>
            )}

            {latestResult && (
                <>
                    {/* 性能對比卡片 */}
                    <div className="comparison-overview">
                        <div className="method-card traditional">
                            <div className="method-header">
                                <h3>📶 傳統換手</h3>
                                <span className="method-type">
                                    基於RSRP/RSRQ測量
                                </span>
                            </div>
                            <div className="key-metrics">
                                <div className="metric">
                                    <span className="label">延遲</span>
                                    <span className="value">
                                        {latestResult.traditional_metrics.latency.toFixed(
                                            1
                                        )}
                                        ms
                                    </span>
                                </div>
                                <div className="metric">
                                    <span className="label">成功率</span>
                                    <span className="value">
                                        {latestResult.traditional_metrics.success_rate.toFixed(
                                            1
                                        )}
                                        %
                                    </span>
                                </div>
                                <div className="metric">
                                    <span className="label">封包遺失</span>
                                    <span className="value">
                                        {latestResult.traditional_metrics.packet_loss.toFixed(
                                            1
                                        )}
                                        %
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="vs-indicator">
                            <div className="vs-circle">VS</div>
                            <div className="improvement-summary">
                                <span className="improvement-text">
                                    延遲減少
                                </span>
                                <span className="improvement-value">
                                    {latestResult.improvement_percentage.latency.toFixed(
                                        0
                                    )}
                                    %
                                </span>
                            </div>
                        </div>

                        <div className="method-card accelerated">
                            <div className="method-header">
                                <h3>🚀 IEEE INFOCOM 2024 加速換手</h3>
                                <span className="method-type">ML預測驅動</span>
                            </div>
                            <div className="key-metrics">
                                <div className="metric">
                                    <span className="label">延遲</span>
                                    <span className="value">
                                        {latestResult.accelerated_metrics.latency.toFixed(
                                            1
                                        )}
                                        ms
                                    </span>
                                </div>
                                <div className="metric">
                                    <span className="label">成功率</span>
                                    <span className="value">
                                        {latestResult.accelerated_metrics.success_rate.toFixed(
                                            1
                                        )}
                                        %
                                    </span>
                                </div>
                                <div className="metric">
                                    <span className="label">封包遺失</span>
                                    <span className="value">
                                        {latestResult.accelerated_metrics.packet_loss.toFixed(
                                            1
                                        )}
                                        %
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 詳細指標對比 */}
                    <div className="detailed-comparison">
                        <div className="comparison-header">
                            <h3>📊 詳細性能指標對比</h3>
                            <div className="metric-selector">
                                <select
                                    value={selectedMetric}
                                    onChange={(e) =>
                                        setSelectedMetric(e.target.value)
                                    }
                                >
                                    <option value="latency">換手延遲</option>
                                    <option value="success_rate">成功率</option>
                                    <option value="packet_loss">
                                        封包遺失率
                                    </option>
                                    <option value="throughput">吞吐量</option>
                                    <option value="power_consumption">
                                        功耗
                                    </option>
                                    <option value="prediction_accuracy">
                                        預測精度
                                    </option>
                                </select>
                            </div>
                        </div>

                        <div className="metrics-grid">
                            {Object.entries(
                                latestResult.improvement_percentage
                            ).map(([metric, improvement]) => {
                                const traditionalValue = latestResult
                                    .traditional_metrics[
                                    metric as keyof HandoverMetrics
                                ] as number
                                const acceleratedValue = latestResult
                                    .accelerated_metrics[
                                    metric as keyof HandoverMetrics
                                ] as number

                                return (
                                    <div
                                        key={metric}
                                        className="metric-comparison-card"
                                    >
                                        <div className="metric-header">
                                            <h4>
                                                {getMetricDisplayName(metric)}
                                            </h4>
                                            <span
                                                className={`improvement ${
                                                    improvement > 0
                                                        ? 'positive'
                                                        : 'negative'
                                                }`}
                                            >
                                                {improvement > 0 ? '+' : ''}
                                                {improvement.toFixed(1)}%
                                            </span>
                                        </div>

                                        <div className="metric-bars">
                                            <div className="metric-bar traditional">
                                                <span className="label">
                                                    傳統
                                                </span>
                                                <div className="bar-container">
                                                    <div
                                                        className="bar-fill"
                                                        style={{
                                                            width: '100%',
                                                        }}
                                                    ></div>
                                                    <span className="value">
                                                        {traditionalValue.toFixed(
                                                            1
                                                        )}
                                                        {getMetricUnit(metric)}
                                                    </span>
                                                </div>
                                            </div>

                                            <div className="metric-bar accelerated">
                                                <span className="label">
                                                    加速
                                                </span>
                                                <div className="bar-container">
                                                    <div
                                                        className="bar-fill"
                                                        style={{
                                                            width: `${
                                                                (acceleratedValue /
                                                                    traditionalValue) *
                                                                100
                                                            }%`,
                                                        }}
                                                    ></div>
                                                    <span className="value">
                                                        {acceleratedValue.toFixed(
                                                            1
                                                        )}
                                                        {getMetricUnit(metric)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>

                    {/* 測試歷史記錄 */}
                    <div className="test-history">
                        <h3>📈 測試歷史記錄</h3>
                        <div className="history-list">
                            {comparisonResults
                                .slice(0, 5)
                                .map((result, index) => (
                                    <div key={index} className="history-item">
                                        <div className="history-time">
                                            {new Date(
                                                result.timestamp
                                            ).toLocaleTimeString('zh-TW')}
                                        </div>
                                        <div className="history-improvements">
                                            <span className="improvement-item">
                                                延遲: -
                                                {result.improvement_percentage.latency.toFixed(
                                                    0
                                                )}
                                                %
                                            </span>
                                            <span className="improvement-item">
                                                成功率: +
                                                {result.improvement_percentage.success_rate.toFixed(
                                                    0
                                                )}
                                                %
                                            </span>
                                            <span className="improvement-item">
                                                吞吐量: +
                                                {result.improvement_percentage.throughput.toFixed(
                                                    0
                                                )}
                                                %
                                            </span>
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default HandoverComparisonDashboard
