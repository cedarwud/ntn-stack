import React from 'react'
import { Doughnut, Bar } from 'react-chartjs-2'

interface SystemTabProps {
    systemMetrics: any
    systemArchitectureData: any
    onChartClick?: (event: any, elements: any[], chart: any) => void
}

const SystemTab: React.FC<SystemTabProps> = ({
    systemMetrics,
    systemArchitectureData,
    onChartClick,
}) => {
    return (
        <div className="charts-grid two-column-grid">
            <div className="chart-container system-metrics">
                <h3>🖥️ LEO 衛星系統實時監控中心</h3>
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-header">
                            <h4>CPU 使用率</h4>
                            <span className="metric-value">
                                {systemMetrics.cpu}%
                            </span>
                        </div>
                        <div className="metric-bar">
                            <div
                                className="metric-fill"
                                style={{ width: `${systemMetrics.cpu}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="metric-card">
                        <div className="metric-header">
                            <h4>記憶體使用率</h4>
                            <span className="metric-value">
                                {systemMetrics.memory}%
                            </span>
                        </div>
                        <div className="metric-bar">
                            <div
                                className="metric-fill"
                                style={{ width: `${systemMetrics.memory}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="metric-card">
                        <div className="metric-header">
                            <h4>GPU 使用率</h4>
                            <span className="metric-value">
                                {systemMetrics.gpu}%
                            </span>
                        </div>
                        <div className="metric-bar">
                            <div
                                className="metric-fill"
                                style={{ width: `${systemMetrics.gpu}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="metric-card">
                        <div className="metric-header">
                            <h4>網路延遲</h4>
                            <span className="metric-value">
                                {systemMetrics.networkLatency}ms
                            </span>
                        </div>
                        <div className="metric-bar">
                            <div
                                className="metric-fill"
                                style={{
                                    width: `${Math.min(
                                        100,
                                        (systemMetrics.networkLatency / 100) *
                                            100
                                    )}%`,
                                }}
                            ></div>
                        </div>
                    </div>
                </div>
                <div className="chart-insight">
                    <strong>系統健康：</strong>
                    所有組件運行穩定，CPU 和記憶體使用率保持在合理範圍內，
                    網路延遲控制在 50ms 以下，確保實時數據傳輸品質。
                </div>
            </div>

            <div className="chart-container">
                <h3>🏗️ 系統架構組件資源分配</h3>
                <Doughnut
                    data={systemArchitectureData}
                    options={{
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right' as const,
                                labels: {
                                    color: 'white',
                                    font: {
                                        size: 14,
                                        weight: 'bold' as 'bold',
                                    },
                                    padding: 20,
                                },
                            },
                            title: {
                                display: true,
                                text: '移動衛星網絡系統資源佔比分析',
                                color: 'white',
                                font: {
                                    size: 18,
                                    weight: 'bold' as 'bold',
                                },
                            },
                        },
                        onClick: (event, elements, chart) =>
                            onChartClick?.(event, elements, chart),
                    }}
                />
                <div className="chart-insight">
                    <strong>架構優化：</strong>
                    Open5GS 核心網佔用資源最多 (32%)，UERANSIM gNB 模擬其次
                    (22%)， 同步算法僅佔
                    10%，體現了算法的高效性和系統的良好可擴展性。
                </div>
            </div>
        </div>
    )
}

export default SystemTab
