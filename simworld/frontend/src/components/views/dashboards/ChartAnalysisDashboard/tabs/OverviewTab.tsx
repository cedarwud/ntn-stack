/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react'
import { Bar } from 'react-chartjs-2'
import { createInteractiveChartOptions } from '../utils/chartConfig'

interface OverviewTabProps {
    handoverLatencyData: any
    constellationComparisonData: any
    sixScenarioChartData: any
    onChartClick: (elements: any[], chart: any) => void
}

const OverviewTab: React.FC<OverviewTabProps> = ({
    handoverLatencyData,
    constellationComparisonData,
    sixScenarioChartData,
    onChartClick,
}) => {
    return (
        <div className="charts-grid">
            <div className="chart-container">
                <h3>📊 圖3: Handover 延遲分解分析</h3>
                <Bar
                    data={handoverLatencyData}
                    options={createInteractiveChartOptions(
                        '四種換手方案延遲對比 (ms)',
                        '延遲 (ms)',
                        '換手階段'
                    )}
                />
                <div className="chart-insight">
                    <strong>核心突破：</strong>本論文提出的同步算法 + Xn
                    加速換手方案， 實現了從標準 NTN 的 ~250ms 到 ~21ms
                    的革命性延遲降低，減少 91.6%。 超越 NTN-GS (153ms) 和
                    NTN-SMN (158ms) 方案，真正實現近零延遲換手。
                    <br />
                    <br />
                    <strong>📊 統計驗證：</strong>
                    改進效果 p &lt; 0.001 (***), 效應大小 Large (Cohen's d =
                    2.8), 信賴度 99.9%
                </div>
            </div>

            <div className="chart-container">
                <h3>🛰️ 圖8: 雙星座六維性能全景對比</h3>
                <Bar
                    data={constellationComparisonData}
                    options={{
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top' as const,
                                labels: {
                                    color: 'white',
                                    font: {
                                        size: 16,
                                        weight: 'bold' as const,
                                    },
                                },
                            },
                            title: {
                                display: true,
                                text: 'Starlink vs Kuiper 技術指標綜合評估',
                                color: 'white',
                                font: {
                                    size: 20,
                                    weight: 'bold' as const,
                                },
                            },
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: '技術指標維度',
                                    color: 'white',
                                    font: {
                                        size: 16,
                                        weight: 'bold' as const,
                                    },
                                },
                                ticks: {
                                    color: 'white',
                                    font: {
                                        size: 14,
                                        weight: 'bold' as const,
                                    },
                                },
                            },
                            y: {
                                ticks: {
                                    color: 'white',
                                    font: {
                                        size: 14,
                                        weight: 'bold' as const,
                                    },
                                },
                                grid: {
                                    color: 'rgba(255, 255, 255, 0.2)',
                                },
                            },
                        },
                    }}
                />
                <div className="chart-insight">
                    <strong>星座特性：</strong>Starlink (550km)
                    憑藉較低軌道在延遲和覆蓋率方面領先， Kuiper (630km)
                    則在換手頻率控制上表現更佳。兩者在 QoE 指標上相近，
                    為不同應用場景提供最適選擇。
                </div>
            </div>

            <div className="chart-container extra-large">
                <h3>🎆 圖8(a)-(f): 六場景換手延遲全面對比分析</h3>
                <Bar
                    data={sixScenarioChartData}
                    options={{
                        ...createInteractiveChartOptions(
                            '八種場景下四種換手方案的延遲對比 (ms)',
                            '延遲 (ms)',
                            '場景編號'
                        ),
                        onClick: onChartClick,
                        plugins: {
                            ...createInteractiveChartOptions('', '', '')
                                .plugins,
                            legend: {
                                position: 'top' as const,
                                labels: {
                                    color: 'white',
                                    font: {
                                        size: 18,
                                        weight: 'bold' as const,
                                    },
                                    padding: 20,
                                    usePointStyle: true,
                                    pointStyle: 'rectRounded',
                                },
                            },
                        },
                        scales: {
                            ...createInteractiveChartOptions('', '', '').scales,
                            x: {
                                title: {
                                    display: true,
                                    text: '應用場景',
                                    color: 'white',
                                    font: {
                                        size: 16,
                                        weight: 'bold' as const,
                                    },
                                },
                                ticks: {
                                    color: 'white',
                                    font: {
                                        size: 16,
                                        weight: 'bold' as const,
                                    },
                                    maxRotation: 45,
                                    minRotation: 45,
                                },
                            },
                        },
                    }}
                />
                <div className="chart-insight">
                    <span
                        style={{
                            background:
                                'linear-gradient(45deg, #ff6b6b, #4ecdc4)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            fontWeight: 'bold',
                            fontSize: '1.1rem',
                        }}
                    >
                        🎯 關鍵發現：
                    </span>{' '}
                    本研究提出的 <strong>Proposed</strong> 方案在所有 8
                    種場景下都顯著優於傳統方案。在最複雜的
                    KP-F-全方向場景中，延遲僅為 22.9ms，相比 NTN 的 270.2ms
                    降低了 <strong>91.5%</strong>
                    。這證明了我們的同步算法和 Xn 加速技術在各種星座配置下的
                    <strong>普適性和穩健性</strong>。
                </div>
            </div>
        </div>
    )
}

export default OverviewTab
