import React from 'react'
import { Line, Radar } from 'react-chartjs-2'

interface AlgorithmsTabProps {
    timeSyncPrecisionData: any
    performanceRadarData: any
    onChartClick?: (event: any, elements: any[], chart: any) => void
}

const AlgorithmsTab: React.FC<AlgorithmsTabProps> = ({
    timeSyncPrecisionData,
    performanceRadarData,
    onChartClick,
}) => {
    return (
        <div className="charts-grid two-column-grid">
            <div className="chart-container">
                <h3>⏰ 時間同步精度技術對比</h3>
                <Line
                    data={timeSyncPrecisionData}
                    options={{
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top' as const,
                                labels: {
                                    color: 'white',
                                    font: {
                                        size: 14,
                                        weight: 'bold' as 'bold',
                                    },
                                },
                            },
                            title: {
                                display: true,
                                text: '不同網路條件下時間同步精度對比',
                                color: 'white',
                                font: {
                                    size: 18,
                                    weight: 'bold' as 'bold',
                                },
                            },
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: '衛星數量',
                                    color: 'white',
                                    font: {
                                        size: 14,
                                        weight: 'bold' as 'bold',
                                    },
                                },
                                ticks: {
                                    color: 'white',
                                    font: {
                                        size: 12,
                                        weight: 'bold' as 'bold',
                                    },
                                },
                                grid: {
                                    color: 'rgba(255, 255, 255, 0.3)',
                                },
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: '同步精度 (μs)',
                                    color: 'white',
                                    font: {
                                        size: 14,
                                        weight: 'bold' as 'bold',
                                    },
                                },
                                ticks: {
                                    color: 'white',
                                    font: {
                                        size: 12,
                                        weight: 'bold' as 'bold',
                                    },
                                    callback: function (value: any) {
                                        return (
                                            Math.round(Number(value) * 10) / 10
                                        )
                                    },
                                },
                                grid: {
                                    color: 'rgba(255, 255, 255, 0.3)',
                                },
                            },
                        },
                        onClick: (event, elements, chart) =>
                            onChartClick?.(event, elements, chart),
                    }}
                />
                <div className="chart-insight">
                    <strong>同步精度：</strong>
                    Fast-prediction 算法在所有場景下都達到了優秀的時間同步精度，
                    特別是在多衛星環境下，精度可達到 2.5μs 以內，滿足 5G NTN
                    嚴格要求。
                </div>
            </div>

            <div className="chart-container">
                <h3>🎯 UE 接入策略六維效能雷達</h3>
                <Radar
                    data={performanceRadarData}
                    options={{
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top' as const,
                                labels: {
                                    color: 'white',
                                    font: {
                                        size: 14,
                                        weight: 'bold' as 'bold',
                                    },
                                },
                            },
                            title: {
                                display: true,
                                text: '策略綜合性能評估雷達圖',
                                color: 'white',
                                font: {
                                    size: 18,
                                    weight: 'bold' as 'bold',
                                },
                            },
                        },
                        scales: {
                            r: {
                                angleLines: {
                                    display: true,
                                    color: 'rgba(255, 255, 255, 0.3)',
                                },
                                grid: {
                                    color: 'rgba(255, 255, 255, 0.3)',
                                },
                                pointLabels: {
                                    color: 'white',
                                    font: {
                                        size: 12,
                                        weight: 'bold' as 'bold',
                                    },
                                },
                                ticks: {
                                    color: 'white',
                                    backdropColor: 'transparent',
                                    font: {
                                        size: 10,
                                    },
                                },
                                suggestedMin: 0,
                                suggestedMax: 100,
                            },
                        },
                        onClick: (event, elements, chart) =>
                            onChartClick?.(event, elements, chart),
                    }}
                />
                <div className="chart-insight">
                    <strong>策略優化：</strong>
                    Flexible 策略在靈活性和能耗效率方面表現突出， Consistent
                    策略在穩定性和成功率方面領先，
                    可根據應用場景動態選擇最適策略。
                </div>
            </div>
        </div>
    )
}

export default AlgorithmsTab
