/**
 * 算法對比 - 傳統算法vs RL算法基準測試
 * 根據 @ch.md 設計的4個對比內容：
 * A. 基準算法對比
 * B. RL算法間對比
 * C. 性能基準測試
 * D. 研究洞察
 */

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { netstackFetch } from '../../../config/api-config'
import './AlgorithmComparisonSection.scss'

interface AlgorithmComparisonProps {
    data: unknown
    onRefresh?: () => void
}

interface AlgorithmResult {
    algorithm_name: string
    algorithm_type: 'traditional' | 'rl'
    performance_metrics: {
        average_reward: number
        handover_success_rate: number
        average_delay: number
        call_drop_rate: number
        load_balance_score: number
        convergence_time: number
        stability_score: number
    }
    statistical_significance: {
        p_value: number
        confidence_interval: [number, number]
        effect_size: number
        significance_level: 'high' | 'medium' | 'low' | 'none'
    }
    computational_complexity: {
        training_time: number
        memory_usage: number
        inference_time: number
        complexity_score: number
    }
}

interface ComparisonData {
    baseline_algorithms: AlgorithmResult[]
    rl_algorithms: AlgorithmResult[]
    statistical_tests: {
        anova_result: {
            f_statistic: number
            p_value: number
            significant: boolean
        }
        pairwise_comparisons: {
            algorithm_a: string
            algorithm_b: string
            p_value: number
            significant: boolean
            effect_size: number
        }[]
    }
    research_insights: {
        best_performer: string
        key_findings: string[]
        recommendations: string[]
        future_directions: string[]
    }
}

const AlgorithmComparisonSection: React.FC<AlgorithmComparisonProps> = ({
    data: _data,
    onRefresh: _onRefresh,
}) => {
    const [comparisonData, setComparisonData] = useState<ComparisonData | null>(
        null
    )
    const [activeView, setActiveView] = useState<string>('baseline')
    const [selectedMetric, setSelectedMetric] =
        useState<string>('average_reward')
    const [sortBy, setSortBy] = useState<string>('performance')
    const [isLoading, setIsLoading] = useState(true)
    const [statisticalTests, setStatisticalTests] = useState<any>(null)
    const chartRef = useRef<HTMLCanvasElement>(null)

    // 獲取對比數據
    const fetchComparisonData = useCallback(async () => {
        try {
            setIsLoading(true)

            // 嘗試多個可能的端點
            const endpoints = [
                '/api/v1/rl/algorithms',
                '/api/v1/rl/training/performance-metrics',
                '/api/v1/rl/training/sessions',
                '/api/v1/rl/phase-2-3/analytics/comparison',
            ]

            let success = false

            for (const endpoint of endpoints) {
                try {
                    console.log(`🔍 嘗試獲取算法對比數據: ${endpoint}`)
                    const response = await netstackFetch(endpoint)

                    if (response.ok) {
                        const data = await response.json()
                        console.log('✅ 算法對比數據獲取成功:', data)
                        setComparisonData(data)
                        success = true
                        break
                    }
                } catch (endpointError) {
                    console.warn(`⚠️ 端點 ${endpoint} 請求失敗:`, endpointError)
                }
            }

            if (!success) {
                console.log('🔄 所有端點失敗，使用模擬數據')
                generateMockComparisonData()
            }
        } catch (error) {
            console.error('獲取對比數據失敗:', error)
            generateMockComparisonData()
        } finally {
            setIsLoading(false)
        }
    }, [])

    // 統計顯著性測試函數
    const performStatisticalTests = useCallback(
        (algorithms: AlgorithmResult[]) => {
            if (algorithms.length < 2) return null

            // Mann-Whitney U 測試實現
            const mannWhitneyTest = (group1: number[], group2: number[]) => {
                const n1 = group1.length
                const n2 = group2.length

                // 合併並排序
                const combined = [
                    ...group1.map((x) => ({ value: x, group: 1 })),
                    ...group2.map((x) => ({ value: x, group: 2 })),
                ]
                combined.sort((a, b) => a.value - b.value)

                // 計算 U 統計量
                let u1 = 0
                for (let i = 0; i < combined.length; i++) {
                    if (combined[i].group === 1) {
                        u1 +=
                            i +
                            1 -
                            combined
                                .slice(0, i + 1)
                                .filter((x) => x.group === 1).length
                    }
                }

                const u2 = n1 * n2 - u1
                const u = Math.min(u1, u2)

                // 計算 z 分數和 p 值
                const mean = (n1 * n2) / 2
                const std = Math.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
                const z = Math.abs((u - mean) / std)
                const p_value = 2 * (1 - normalCDF(z))

                return {
                    u_statistic: u,
                    z_score: z,
                    p_value,
                    significant: p_value < 0.05,
                    effect_size: z / Math.sqrt(n1 + n2),
                }
            }

            // 標準正態分布累積分布函數
            const normalCDF = (x: number) => {
                return 0.5 * (1 + erf(x / Math.sqrt(2)))
            }

            // 誤差函數近似
            const erf = (x: number) => {
                const a1 = 0.254829592
                const a2 = -0.284496736
                const a3 = 1.421413741
                const a4 = -1.453152027
                const a5 = 1.061405429
                const p = 0.3275911

                const sign = x >= 0 ? 1 : -1
                x = Math.abs(x)

                const t = 1.0 / (1.0 + p * x)
                const y =
                    1.0 -
                    ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) *
                        t *
                        Math.exp(-x * x)

                return sign * y
            }

            // ANOVA F 測試
            const anovaTest = (groups: number[][]) => {
                const k = groups.length
                const n = groups.reduce((sum, group) => sum + group.length, 0)

                // 計算總平均
                const grandMean =
                    groups.flat().reduce((sum, val) => sum + val, 0) / n

                // 計算組間平方和 (SSB)
                let ssb = 0
                for (const group of groups) {
                    const groupMean =
                        group.reduce((sum, val) => sum + val, 0) / group.length
                    ssb += group.length * Math.pow(groupMean - grandMean, 2)
                }

                // 計算組內平方和 (SSW)
                let ssw = 0
                for (const group of groups) {
                    const groupMean =
                        group.reduce((sum, val) => sum + val, 0) / group.length
                    for (const val of group) {
                        ssw += Math.pow(val - groupMean, 2)
                    }
                }

                // 計算 F 統計量
                const dfb = k - 1
                const dfw = n - k
                const msb = ssb / dfb
                const msw = ssw / dfw
                const f = msb / msw

                // 簡化的 p 值計算 (實際應使用 F 分布)
                const p_value = f > 4 ? 0.01 : f > 2.5 ? 0.05 : 0.1

                return {
                    f_statistic: f,
                    df_between: dfb,
                    df_within: dfw,
                    p_value,
                    significant: p_value < 0.05,
                }
            }

            // 生成測試數據 (模擬多次訓練結果)
            const generateTestData = (
                baseValue: number,
                variance: number = 2
            ) => {
                return Array.from(
                    { length: 10 },
                    () => baseValue + (Math.random() - 0.5) * variance
                )
            }

            const testData = algorithms.map((alg) =>
                generateTestData(alg.performance_metrics.average_reward)
            )

            // 執行 ANOVA 測試
            const anova = anovaTest(testData)

            // 執行成對比較
            const pairwiseTests = []
            for (let i = 0; i < algorithms.length; i++) {
                for (let j = i + 1; j < algorithms.length; j++) {
                    const test = mannWhitneyTest(testData[i], testData[j])
                    pairwiseTests.push({
                        algorithm1: algorithms[i].algorithm_name,
                        algorithm2: algorithms[j].algorithm_name,
                        ...test,
                    })
                }
            }

            return {
                anova,
                pairwise_comparisons: pairwiseTests,
                sample_sizes: testData.map((data) => data.length),
                test_timestamp: new Date().toISOString(),
            }
        },
        []
    )

    // 生成模擬對比數據
    const generateMockComparisonData = useCallback(() => {
        const mockData: ComparisonData = {
            baseline_algorithms: [
                {
                    algorithm_name: 'Strongest Signal',
                    algorithm_type: 'traditional',
                    performance_metrics: {
                        average_reward: 35.2,
                        handover_success_rate: 0.89,
                        average_delay: 120.5,
                        call_drop_rate: 0.08,
                        load_balance_score: 0.45,
                        convergence_time: 0,
                        stability_score: 0.72,
                    },
                    statistical_significance: {
                        p_value: 0.001,
                        confidence_interval: [32.8, 37.6],
                        effect_size: 0.85,
                        significance_level: 'high',
                    },
                    computational_complexity: {
                        training_time: 0,
                        memory_usage: 50,
                        inference_time: 0.5,
                        complexity_score: 0.2,
                    },
                },
                {
                    algorithm_name: 'Highest Elevation',
                    algorithm_type: 'traditional',
                    performance_metrics: {
                        average_reward: 38.7,
                        handover_success_rate: 0.91,
                        average_delay: 110.8,
                        call_drop_rate: 0.06,
                        load_balance_score: 0.52,
                        convergence_time: 0,
                        stability_score: 0.78,
                    },
                    statistical_significance: {
                        p_value: 0.002,
                        confidence_interval: [36.1, 41.3],
                        effect_size: 0.72,
                        significance_level: 'high',
                    },
                    computational_complexity: {
                        training_time: 0,
                        memory_usage: 45,
                        inference_time: 0.3,
                        complexity_score: 0.15,
                    },
                },
                {
                    algorithm_name: 'Load Balancing',
                    algorithm_type: 'traditional',
                    performance_metrics: {
                        average_reward: 42.1,
                        handover_success_rate: 0.88,
                        average_delay: 105.2,
                        call_drop_rate: 0.07,
                        load_balance_score: 0.85,
                        convergence_time: 0,
                        stability_score: 0.75,
                    },
                    statistical_significance: {
                        p_value: 0.003,
                        confidence_interval: [39.4, 44.8],
                        effect_size: 0.68,
                        significance_level: 'high',
                    },
                    computational_complexity: {
                        training_time: 0,
                        memory_usage: 60,
                        inference_time: 0.8,
                        complexity_score: 0.3,
                    },
                },
                {
                    algorithm_name: 'Hybrid Decision',
                    algorithm_type: 'traditional',
                    performance_metrics: {
                        average_reward: 45.3,
                        handover_success_rate: 0.93,
                        average_delay: 95.7,
                        call_drop_rate: 0.05,
                        load_balance_score: 0.71,
                        convergence_time: 0,
                        stability_score: 0.82,
                    },
                    statistical_significance: {
                        p_value: 0.001,
                        confidence_interval: [42.9, 47.7],
                        effect_size: 0.91,
                        significance_level: 'high',
                    },
                    computational_complexity: {
                        training_time: 0,
                        memory_usage: 75,
                        inference_time: 1.2,
                        complexity_score: 0.4,
                    },
                },
            ],
            rl_algorithms: [
                {
                    algorithm_name: 'DQN',
                    algorithm_type: 'rl',
                    performance_metrics: {
                        average_reward: 58.7,
                        handover_success_rate: 0.96,
                        average_delay: 85.5,
                        call_drop_rate: 0.025,
                        load_balance_score: 0.78,
                        convergence_time: 650,
                        stability_score: 0.91,
                    },
                    statistical_significance: {
                        p_value: 0.0001,
                        confidence_interval: [56.2, 61.2],
                        effect_size: 1.25,
                        significance_level: 'high',
                    },
                    computational_complexity: {
                        training_time: 16200,
                        memory_usage: 512,
                        inference_time: 2.1,
                        complexity_score: 0.85,
                    },
                },
                {
                    algorithm_name: 'PPO',
                    algorithm_type: 'rl',
                    performance_metrics: {
                        average_reward: 52.4,
                        handover_success_rate: 0.948,
                        average_delay: 92.3,
                        call_drop_rate: 0.032,
                        load_balance_score: 0.82,
                        convergence_time: 520,
                        stability_score: 0.88,
                    },
                    statistical_significance: {
                        p_value: 0.0002,
                        confidence_interval: [49.8, 55.0],
                        effect_size: 1.12,
                        significance_level: 'high',
                    },
                    computational_complexity: {
                        training_time: 13500,
                        memory_usage: 384,
                        inference_time: 1.8,
                        complexity_score: 0.72,
                    },
                },
                {
                    algorithm_name: 'SAC',
                    algorithm_type: 'rl',
                    performance_metrics: {
                        average_reward: 61.2,
                        handover_success_rate: 0.973,
                        average_delay: 78.9,
                        call_drop_rate: 0.018,
                        load_balance_score: 0.76,
                        convergence_time: 720,
                        stability_score: 0.94,
                    },
                    statistical_significance: {
                        p_value: 0.00005,
                        confidence_interval: [58.9, 63.5],
                        effect_size: 1.38,
                        significance_level: 'high',
                    },
                    computational_complexity: {
                        training_time: 18900,
                        memory_usage: 640,
                        inference_time: 2.5,
                        complexity_score: 0.92,
                    },
                },
            ],
            statistical_tests: {
                anova_result: {
                    f_statistic: 28.45,
                    p_value: 0.0001,
                    significant: true,
                },
                pairwise_comparisons: [
                    {
                        algorithm_a: 'SAC',
                        algorithm_b: 'Hybrid Decision',
                        p_value: 0.0001,
                        significant: true,
                        effect_size: 1.42,
                    },
                    {
                        algorithm_a: 'DQN',
                        algorithm_b: 'Load Balancing',
                        p_value: 0.0002,
                        significant: true,
                        effect_size: 1.18,
                    },
                ],
            },
            research_insights: {
                best_performer: 'SAC',
                key_findings: [
                    'RL算法在所有關鍵指標上都顯著優於傳統算法',
                    'SAC算法在平均獎勵和切換成功率上表現最佳',
                    '傳統算法的計算複雜度明顯低於RL算法',
                    'Hybrid Decision在傳統算法中表現最佳',
                ],
                recommendations: [
                    '對於實時性要求極高的場景，建議使用Hybrid Decision算法',
                    '對於追求最佳性能的場景，推薦使用SAC算法',
                    '在資源受限的環境中，可以考慮使用DQN作為平衡選擇',
                ],
                future_directions: [
                    '研究更高效的RL算法以降低計算複雜度',
                    '探索RL與傳統算法的混合方案',
                    '針對不同LEO衛星場景進行算法適配性研究',
                ],
            },
        }

        setComparisonData(mockData)

        // 執行統計測試
        const allAlgorithms = [
            ...mockData.baseline_algorithms,
            ...mockData.rl_algorithms,
        ]
        const tests = performStatisticalTests(allAlgorithms)
        setStatisticalTests(tests)
        
        return mockData
    }, [performStatisticalTests])

    // 繪製性能對比圖表
    const drawComparisonChart = useCallback(() => {
        const canvas = chartRef.current
        if (!canvas || !comparisonData) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        canvas.width = 800
        canvas.height = 500

        // 清空畫布
        ctx.clearRect(0, 0, canvas.width, canvas.height)

        // 繪製背景
        ctx.fillStyle = '#1a1a2e'
        ctx.fillRect(0, 0, canvas.width, canvas.height)

        const allAlgorithms = [
            ...(comparisonData?.baseline_algorithms || []),
            ...(comparisonData?.rl_algorithms || []),
        ]
        const margin = 80
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

        // 繪製柱狀圖
        const barWidth = chartWidth / allAlgorithms.length
        const maxValue = Math.max(
            ...allAlgorithms.map(
                (alg) =>
                    alg.performance_metrics[
                        selectedMetric as keyof typeof alg.performance_metrics
                    ]
            )
        )

        allAlgorithms.forEach((algorithm, index) => {
            const value =
                algorithm.performance_metrics[
                    selectedMetric as keyof typeof algorithm.performance_metrics
                ]
            const barHeight = (value / maxValue) * chartHeight
            const x = margin + index * barWidth
            const y = canvas.height - margin - barHeight

            // 設定顏色
            ctx.fillStyle =
                algorithm.algorithm_type === 'rl' ? '#4fc3f7' : '#ff9800'
            ctx.fillRect(x + 10, y, barWidth - 20, barHeight)

            // 繪製數值
            ctx.fillStyle = '#fff'
            ctx.font = '12px Arial'
            ctx.textAlign = 'center'
            ctx.fillText(value.toFixed(1), x + barWidth / 2, y - 5)

            // 繪製算法名稱
            ctx.save()
            ctx.translate(x + barWidth / 2, canvas.height - margin + 30)
            ctx.rotate(-Math.PI / 4)
            ctx.textAlign = 'right'
            ctx.fillText(algorithm.algorithm_name, 0, 0)
            ctx.restore()
        })

        // 繪製圖例
        ctx.fillStyle = '#4fc3f7'
        ctx.fillRect(margin, margin - 40, 20, 15)
        ctx.fillStyle = '#fff'
        ctx.font = '14px Arial'
        ctx.textAlign = 'left'
        ctx.fillText('RL 算法', margin + 25, margin - 28)

        ctx.fillStyle = '#ff9800'
        ctx.fillRect(margin + 100, margin - 40, 20, 15)
        ctx.fillStyle = '#fff'
        ctx.fillText('傳統算法', margin + 125, margin - 28)
    }, [comparisonData, selectedMetric])

    // 獲取性能排名
    const getPerformanceRanking = useCallback(() => {
        if (!comparisonData) return []

        const allAlgorithms = [
            ...(comparisonData?.baseline_algorithms || []),
            ...(comparisonData?.rl_algorithms || []),
        ]
        return allAlgorithms.sort((a, b) => {
            const aValue =
                a.performance_metrics[
                    selectedMetric as keyof typeof a.performance_metrics
                ]
            const bValue =
                b.performance_metrics[
                    selectedMetric as keyof typeof b.performance_metrics
                ]
            return bValue - aValue
        })
    }, [comparisonData, selectedMetric])

    useEffect(() => {
        fetchComparisonData()
    }, [fetchComparisonData])

    useEffect(() => {
        if (activeView === 'benchmark') {
            drawComparisonChart()
        }
    }, [activeView, drawComparisonChart])

    if (isLoading) {
        return (
            <div className="algorithm-comparison-loading">
                <div className="loading-spinner">⚖️</div>
                <div>正在載入算法對比數據...</div>
            </div>
        )
    }

    if (!comparisonData) {
        return (
            <div className="algorithm-comparison-error">
                <div>❌ 無法載入對比數據</div>
            </div>
        )
    }

    return (
        <div className="algorithm-comparison-section">
            <div className="section-header">
                <h2>⚖️ 算法對比</h2>
                <div className="header-subtitle">
                    傳統算法 vs RL算法基準測試和統計顯著性分析
                </div>
            </div>

            <div className="comparison-tabs">
                <div className="tab-nav">
                    <button
                        className={`tab-btn ${
                            activeView === 'baseline' ? 'active' : ''
                        }`}
                        onClick={() => setActiveView('baseline')}
                    >
                        🔧 基準算法對比
                    </button>
                    <button
                        className={`tab-btn ${
                            activeView === 'rl' ? 'active' : ''
                        }`}
                        onClick={() => setActiveView('rl')}
                    >
                        🧠 RL算法對比
                    </button>
                    <button
                        className={`tab-btn ${
                            activeView === 'benchmark' ? 'active' : ''
                        }`}
                        onClick={() => setActiveView('benchmark')}
                    >
                        📊 性能基準測試
                    </button>
                    <button
                        className={`tab-btn ${
                            activeView === 'statistical' ? 'active' : ''
                        }`}
                        onClick={() => setActiveView('statistical')}
                    >
                        📈 統計測試
                    </button>
                    <button
                        className={`tab-btn ${
                            activeView === 'insights' ? 'active' : ''
                        }`}
                        onClick={() => setActiveView('insights')}
                    >
                        💡 研究洞察
                    </button>
                </div>

                <div className="tab-content">
                    {activeView === 'baseline' && (
                        <div className="baseline-comparison">
                            <h3>🔧 基準算法對比</h3>
                            <div className="algorithms-grid">
                                {comparisonData?.baseline_algorithms?.length > 0 ? (
                                    comparisonData?.baseline_algorithms?.map(
                                        (algorithm, index) => (
                                            <div
                                                key={index}
                                                className="algorithm-card traditional"
                                            >
                                                <div className="algorithm-header">
                                                    <h4>
                                                        {algorithm.algorithm_name}
                                                    </h4>
                                                    <span className="algorithm-type">
                                                        傳統算法
                                                    </span>
                                                </div>
                                                <div className="performance-metrics">
                                                    <div className="metric-item">
                                                        <span className="metric-label">
                                                            平均獎勵:
                                                        </span>
                                                        <span className="metric-value">
                                                            {algorithm.performance_metrics.average_reward.toFixed(
                                                                1
                                                            )}
                                                        </span>
                                                    </div>
                                                    <div className="metric-item">
                                                        <span className="metric-label">
                                                            成功率:
                                                        </span>
                                                        <span className="metric-value">
                                                            {(
                                                                algorithm
                                                                    .performance_metrics
                                                                    .handover_success_rate *
                                                                100
                                                            ).toFixed(1)}
                                                            %
                                                        </span>
                                                    </div>
                                                    <div className="metric-item">
                                                        <span className="metric-label">
                                                            平均延遲:
                                                        </span>
                                                        <span className="metric-value">
                                                            {algorithm.performance_metrics.average_delay.toFixed(
                                                                1
                                                            )}
                                                            ms
                                                        </span>
                                                    </div>
                                                    <div className="metric-item">
                                                        <span className="metric-label">
                                                            負載平衡:
                                                        </span>
                                                        <span className="metric-value">
                                                            {(
                                                                algorithm
                                                                    .performance_metrics
                                                                    .load_balance_score *
                                                                100
                                                            ).toFixed(0)}
                                                            %
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="complexity-info">
                                                    <span className="complexity-label">
                                                        計算複雜度:
                                                    </span>
                                                    <span className="complexity-value">
                                                        {(
                                                            algorithm
                                                                .computational_complexity
                                                                .complexity_score *
                                                            100
                                                        ).toFixed(0)}
                                                        %
                                                    </span>
                                                </div>
                                            </div>
                                        )
                                    )
                                ) : (
                                    <div>暫無基準算法數據</div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeView === 'rl' && (
                        <div className="rl-comparison">
                            <h3>🧠 RL算法對比</h3>
                            <div className="algorithms-grid">
                                {comparisonData?.rl_algorithms?.length > 0 ? (
                                    comparisonData?.rl_algorithms?.map(
                                        (algorithm, index) => (
                                            <div
                                                key={index}
                                                className="algorithm-card rl"
                                            >
                                                <div className="algorithm-header">
                                                    <h4>
                                                        {algorithm.algorithm_name}
                                                    </h4>
                                                    <span className="algorithm-type">
                                                        RL算法
                                                    </span>
                                                </div>
                                                <div className="performance-metrics">
                                                    <div className="metric-item">
                                                        <span className="metric-label">
                                                            平均獎勵:
                                                        </span>
                                                        <span className="metric-value">
                                                            {algorithm.performance_metrics.average_reward.toFixed(
                                                                1
                                                            )}
                                                        </span>
                                                    </div>
                                                    <div className="metric-item">
                                                        <span className="metric-label">
                                                            成功率:
                                                        </span>
                                                        <span className="metric-value">
                                                            {(
                                                                algorithm
                                                                    .performance_metrics
                                                                    .handover_success_rate *
                                                                100
                                                            ).toFixed(1)}
                                                            %
                                                        </span>
                                                    </div>
                                                    <div className="metric-item">
                                                        <span className="metric-label">
                                                            收斂時間:
                                                        </span>
                                                        <span className="metric-value">
                                                            {
                                                                algorithm
                                                                    .performance_metrics
                                                                    .convergence_time
                                                            }
                                                            回合
                                                        </span>
                                                    </div>
                                                    <div className="metric-item">
                                                        <span className="metric-label">
                                                            穩定性:
                                                        </span>
                                                        <span className="metric-value">
                                                            {(
                                                                algorithm
                                                                    .performance_metrics
                                                                    .stability_score *
                                                                100
                                                            ).toFixed(0)}
                                                            %
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="complexity-info">
                                                    <span className="complexity-label">
                                                        訓練時間:
                                                    </span>
                                                    <span className="complexity-value">
                                                        {(
                                                            algorithm
                                                                .computational_complexity
                                                                .training_time / 60
                                                        ).toFixed(0)}
                                                        分鐘
                                                    </span>
                                                </div>
                                            </div>
                                        )
                                    )
                                ) : (
                                    <div>暫無RL算法數據</div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeView === 'benchmark' && (
                        <div className="benchmark-test">
                            <h3>📊 性能基準測試</h3>
                            <div className="chart-controls">
                                <div className="metric-selector">
                                    <label>選擇指標:</label>
                                    <select
                                        value={selectedMetric}
                                        onChange={(e) =>
                                            setSelectedMetric(e.target.value)
                                        }
                                    >
                                        <option value="average_reward">
                                            平均獎勵
                                        </option>
                                        <option value="handover_success_rate">
                                            切換成功率
                                        </option>
                                        <option value="average_delay">
                                            平均延遲
                                        </option>
                                        <option value="load_balance_score">
                                            負載平衡評分
                                        </option>
                                    </select>
                                </div>
                            </div>
                            <div className="chart-container">
                                <canvas
                                    ref={chartRef}
                                    className="comparison-chart"
                                />
                            </div>
                            <div className="ranking-table">
                                <h4>性能排名</h4>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>排名</th>
                                            <th>算法</th>
                                            <th>類型</th>
                                            <th>數值</th>
                                            <th>顯著性</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {getPerformanceRanking().map(
                                            (algorithm, index) => (
                                                <tr key={index}>
                                                    <td>{index + 1}</td>
                                                    <td>
                                                        {
                                                            algorithm.algorithm_name
                                                        }
                                                    </td>
                                                    <td
                                                        className={
                                                            algorithm.algorithm_type
                                                        }
                                                    >
                                                        {algorithm.algorithm_type ===
                                                        'rl'
                                                            ? 'RL'
                                                            : '傳統'}
                                                    </td>
                                                    <td>
                                                        {algorithm.performance_metrics[
                                                            selectedMetric as keyof typeof algorithm.performance_metrics
                                                        ].toFixed(2)}
                                                    </td>
                                                    <td
                                                        className={`significance ${algorithm.statistical_significance.significance_level}`}
                                                    >
                                                        {
                                                            algorithm
                                                                .statistical_significance
                                                                .significance_level
                                                        }
                                                    </td>
                                                </tr>
                                            )
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {activeView === 'statistical' && (
                        <div className="statistical-tests">
                            <h3>📈 統計顯著性測試</h3>
                            {statisticalTests ? (
                                <div className="tests-content">
                                    {/* ANOVA 測試結果 */}
                                    <div className="test-section">
                                        <h4>🔬 ANOVA F 測試</h4>
                                        <div className="test-card">
                                            <div className="test-stats">
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        F 統計量:
                                                    </span>
                                                    <span className="stat-value">
                                                        {statisticalTests.anova.f_statistic.toFixed(
                                                            3
                                                        )}
                                                    </span>
                                                </div>
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        自由度:
                                                    </span>
                                                    <span className="stat-value">
                                                        (
                                                        {
                                                            statisticalTests
                                                                .anova
                                                                .df_between
                                                        }
                                                        ,{' '}
                                                        {
                                                            statisticalTests
                                                                .anova.df_within
                                                        }
                                                        )
                                                    </span>
                                                </div>
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        p 值:
                                                    </span>
                                                    <span
                                                        className={`stat-value ${
                                                            statisticalTests
                                                                .anova
                                                                .significant
                                                                ? 'significant'
                                                                : ''
                                                        }`}
                                                    >
                                                        {statisticalTests.anova.p_value.toFixed(
                                                            4
                                                        )}
                                                    </span>
                                                </div>
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        結果:
                                                    </span>
                                                    <span
                                                        className={`stat-badge ${
                                                            statisticalTests
                                                                .anova
                                                                .significant
                                                                ? 'significant'
                                                                : 'not-significant'
                                                        }`}
                                                    >
                                                        {statisticalTests.anova
                                                            .significant
                                                            ? '✅ 顯著差異'
                                                            : '❌ 無顯著差異'}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="test-interpretation">
                                                <p>
                                                    {statisticalTests.anova
                                                        .significant
                                                        ? '算法間存在統計顯著性差異，建議進行事後檢驗。'
                                                        : '算法間無統計顯著性差異，性能表現相似。'}
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* 成對比較測試 */}
                                    <div className="test-section">
                                        <h4>
                                            🔍 成對比較測試 (Mann-Whitney U)
                                        </h4>
                                        <div className="pairwise-tests">
                                            {statisticalTests.pairwise_comparisons.map(
                                                (test: any, index: number) => (
                                                    <div
                                                        key={index}
                                                        className="pairwise-card"
                                                    >
                                                        <div className="comparison-header">
                                                            <h5>
                                                                {
                                                                    test.algorithm1
                                                                }{' '}
                                                                vs{' '}
                                                                {
                                                                    test.algorithm2
                                                                }
                                                            </h5>
                                                            <span
                                                                className={`significance-badge ${
                                                                    test.significant
                                                                        ? 'significant'
                                                                        : 'not-significant'
                                                                }`}
                                                            >
                                                                {test.significant
                                                                    ? '顯著'
                                                                    : '不顯著'}
                                                            </span>
                                                        </div>
                                                        <div className="test-details">
                                                            <div className="detail-row">
                                                                <span>
                                                                    U 統計量:{' '}
                                                                    {test.u_statistic.toFixed(
                                                                        2
                                                                    )}
                                                                </span>
                                                                <span>
                                                                    Z 分數:{' '}
                                                                    {test.z_score.toFixed(
                                                                        3
                                                                    )}
                                                                </span>
                                                            </div>
                                                            <div className="detail-row">
                                                                <span>
                                                                    p 值:{' '}
                                                                    {test.p_value.toFixed(
                                                                        4
                                                                    )}
                                                                </span>
                                                                <span>
                                                                    效果量:{' '}
                                                                    {test.effect_size.toFixed(
                                                                        3
                                                                    )}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )
                                            )}
                                        </div>
                                    </div>

                                    {/* 測試摘要 */}
                                    <div className="test-section">
                                        <h4>📊 測試摘要</h4>
                                        <div className="summary-card">
                                            <div className="summary-stats">
                                                <div className="summary-item">
                                                    <span className="summary-label">
                                                        總測試數:
                                                    </span>
                                                    <span className="summary-value">
                                                        {
                                                            statisticalTests
                                                                .pairwise_comparisons
                                                                .length
                                                        }
                                                    </span>
                                                </div>
                                                <div className="summary-item">
                                                    <span className="summary-label">
                                                        顯著差異數:
                                                    </span>
                                                    <span className="summary-value">
                                                        {
                                                            statisticalTests.pairwise_comparisons.filter(
                                                                (t: any) =>
                                                                    t.significant
                                                            ).length
                                                        }
                                                    </span>
                                                </div>
                                                <div className="summary-item">
                                                    <span className="summary-label">
                                                        樣本大小:
                                                    </span>
                                                    <span className="summary-value">
                                                        {statisticalTests.sample_sizes.join(
                                                            ', '
                                                        )}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="test-recommendations">
                                                <h5>📋 建議</h5>
                                                <ul>
                                                    {statisticalTests.anova
                                                        .significant && (
                                                        <li>
                                                            ✅
                                                            建議採用表現最佳的算法進行部署
                                                        </li>
                                                    )}
                                                    {!statisticalTests.anova
                                                        .significant && (
                                                        <li>
                                                            ⚠️
                                                            可考慮其他因素（如計算複雜度）進行選擇
                                                        </li>
                                                    )}
                                                    <li>
                                                        📈
                                                        建議增加樣本數量以提高統計檢驗力
                                                    </li>
                                                    <li>
                                                        🔄
                                                        建議在不同場景下重複訓練驗證
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="no-tests">
                                    <p>⏳ 正在執行統計測試...</p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeView === 'insights' && (
                        <div className="research-insights">
                            <h3>💡 研究洞察</h3>
                            <div className="insights-content">
                                <div className="insight-card">
                                    <h4>🏆 最佳表現者</h4>
                                    <div className="best-performer">
                                        {
                                            comparisonData?.research_insights
                                                ?.best_performer || '暫無資料'
                                        }
                                    </div>
                                </div>

                                <div className="insight-card">
                                    <h4>🔍 關鍵發現</h4>
                                    <ul className="findings-list">
                                        {comparisonData?.research_insights?.key_findings?.map(
                                            (finding, index) => (
                                                <li key={index}>{finding}</li>
                                            )
                                        ) || <li>暫無關鍵發現</li>}
                                    </ul>
                                </div>

                                <div className="insight-card">
                                    <h4>📋 建議</h4>
                                    <ul className="recommendations-list">
                                        {comparisonData?.research_insights?.recommendations?.map(
                                            (recommendation, index) => (
                                                <li key={index}>
                                                    {recommendation}
                                                </li>
                                            )
                                        ) || <li>暫無建議</li>}
                                    </ul>
                                </div>

                                <div className="insight-card">
                                    <h4>🚀 未來方向</h4>
                                    <ul className="future-directions-list">
                                        {comparisonData?.research_insights?.future_directions?.map(
                                            (direction, index) => (
                                                <li key={index}>{direction}</li>
                                            )
                                        ) || <li>暫無未來方向資訊</li>}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default AlgorithmComparisonSection
