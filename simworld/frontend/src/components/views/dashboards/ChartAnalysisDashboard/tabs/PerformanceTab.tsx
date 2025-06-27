import React from 'react'
import { Line, Bar } from 'react-chartjs-2'

interface PerformanceTabProps {
    qoeTimeSeriesData: any
    complexityData: any
    onChartClick?: (event: any, elements: any[], chart: any) => void
}

const PerformanceTab: React.FC<PerformanceTabProps> = ({
    qoeTimeSeriesData,
    complexityData,
    onChartClick,
}) => {
    return (
        <div className="charts-grid two-column-grid">
            <div className="chart-container">
                <h3>📊 QoE 實時監控 - Stalling Time & RTT 分析</h3>
                <Line
                    data={qoeTimeSeriesData}
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
                                text: '不同場景下的 QoE 表現分析',
                                color: 'white',
                                font: {
                                    size: 18,
                                    weight: 'bold' as 'bold',
                                },
                            },
                        },
                        scales: {
                            x: {
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
                                max: 1,
                                title: {
                                    display: true,
                                    text: 'QoE 分數',
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
                        },
                        onClick: (event, elements, chart) =>
                            onChartClick?.(event, elements, chart),
                    }}
                />
                <div className="chart-insight">
                    <strong>品質保證：</strong>
                    Ultra-Dense Urban 場景下 QoE 維持在 0.85 以上， Remote
                    地區也能達到 0.75，確保全域用戶體驗一致性。
                </div>
            </div>

            <div className="chart-container">
                <h3>⚡ 圖7: 算法複雜度可擴展性分析</h3>
                <Bar
                    data={complexityData}
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
                                text: 'Fast-prediction vs 標準算法性能對比',
                                color: 'white',
                                font: {
                                    size: 18,
                                    weight: 'bold' as 'bold',
                                },
                            },
                        },
                        scales: {
                            x: {
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
                                    text: '處理時間 (ms)',
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
                        },
                        onClick: (event, elements, chart) =>
                            onChartClick?.(event, elements, chart),
                    }}
                />
                <div className="chart-insight">
                    <strong>效能突破：</strong>
                    Fast-prediction 算法在 1000 節點規模下僅需 67.5ms，
                    相比標準演算法的 142ms 提升 52%， 達到
                    67.5Mbps，提供穩定高速的衛星網路服務。
                </div>
            </div>
        </div>
    )
}

export default PerformanceTab
