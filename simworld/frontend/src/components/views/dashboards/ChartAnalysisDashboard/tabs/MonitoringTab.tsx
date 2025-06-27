/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect } from 'react'
import { Line, Doughnut, Bar } from 'react-chartjs-2'
import { createInteractiveChartOptions } from '../utils/chartConfig'

interface MonitoringTabProps {
    systemMetrics: any
    onChartClick: (event: any, elements: any[], chart: any) => void
}

const MonitoringTab: React.FC<MonitoringTabProps> = ({
    systemMetrics,
    onChartClick,
}) => {
    // 即時監控狀態
    const [realTimeMetrics, setRealTimeMetrics] = useState({
        latency: 23.5,
        throughput: 945,
        packetLoss: 0.02,
        jitter: 1.8,
        cpuUsage: 45,
        memoryUsage: 62,
        networkIO: 78,
        diskIO: 34,
    })

    const [alertLevel, setAlertLevel] = useState<
        'normal' | 'warning' | 'critical'
    >('normal')
    const [isMonitoring, setIsMonitoring] = useState(true)

    // 即時更新模擬
    useEffect(() => {
        if (!isMonitoring) return

        const interval = setInterval(() => {
            setRealTimeMetrics((prev) => {
                const newMetrics = {
                    latency: Math.max(
                        15,
                        prev.latency + (Math.random() - 0.5) * 2
                    ),
                    throughput: Math.max(
                        800,
                        prev.throughput + (Math.random() - 0.5) * 50
                    ),
                    packetLoss: Math.max(
                        0,
                        Math.min(
                            1,
                            prev.packetLoss + (Math.random() - 0.5) * 0.01
                        )
                    ),
                    jitter: Math.max(
                        0.5,
                        prev.jitter + (Math.random() - 0.5) * 0.3
                    ),
                    cpuUsage: Math.max(
                        20,
                        Math.min(90, prev.cpuUsage + (Math.random() - 0.5) * 5)
                    ),
                    memoryUsage: Math.max(
                        30,
                        Math.min(
                            85,
                            prev.memoryUsage + (Math.random() - 0.5) * 3
                        )
                    ),
                    networkIO: Math.max(
                        40,
                        Math.min(95, prev.networkIO + (Math.random() - 0.5) * 8)
                    ),
                    diskIO: Math.max(
                        10,
                        Math.min(70, prev.diskIO + (Math.random() - 0.5) * 4)
                    ),
                }

                // 在同一個函數中更新警報級別，避免依賴問題
                const newAlertLevel =
                    newMetrics.latency > 40 || newMetrics.cpuUsage > 80
                        ? 'critical'
                        : newMetrics.latency > 30 ||
                          newMetrics.packetLoss > 0.05
                        ? 'warning'
                        : 'normal'
                setAlertLevel(newAlertLevel)

                return newMetrics
            })
        }, 2000)

        return () => clearInterval(interval)
    }, [isMonitoring]) // 移除所有realTimeMetrics相關的依賴

    // 生成歷史趨勢數據 - 使用固定種子避免無限渲染
    const [trendData, setTrendData] = useState(() => ({
        labels: Array.from({ length: 20 }, (_, i) => `T-${19 - i}min`),
        latencyHistory: [
            23, 25, 22, 26, 24, 23, 25, 24, 22, 26, 25, 23, 24, 22, 25, 23, 26,
            24, 23, 25,
        ],
        throughputHistory: [
            920, 945, 910, 960, 935, 920, 950, 940, 915, 965, 945, 920, 940,
            915, 950, 920, 965, 940, 920, 945,
        ],
        errorRateHistory: [
            0.02, 0.01, 0.03, 0.02, 0.01, 0.02, 0.01, 0.02, 0.03, 0.01, 0.02,
            0.01, 0.02, 0.03, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02,
        ],
    }))

    // 更新趨勢數據
    useEffect(() => {
        if (!isMonitoring) return

        const interval = setInterval(() => {
            setTrendData((prev) => ({
                labels: [...prev.labels.slice(1), `T-0min`],
                latencyHistory: [
                    ...prev.latencyHistory.slice(1),
                    realTimeMetrics.latency,
                ],
                throughputHistory: [
                    ...prev.throughputHistory.slice(1),
                    realTimeMetrics.throughput,
                ],
                errorRateHistory: [
                    ...prev.errorRateHistory.slice(1),
                    realTimeMetrics.packetLoss,
                ],
            }))
        }, 5000)

        return () => clearInterval(interval)
    }, [isMonitoring, realTimeMetrics])

    // 即時性能趨勢圖
    const performanceTrendData = {
        labels: trendData.labels,
        datasets: [
            {
                label: '延遲 (ms)',
                data: trendData.latencyHistory,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                borderWidth: 2,
                fill: true,
                yAxisID: 'y',
            },
            {
                label: '吞吐量 (Mbps)',
                data: trendData.throughputHistory,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                borderWidth: 2,
                fill: true,
                yAxisID: 'y1',
            },
        ],
    }

    // 系統資源使用圓餅圖
    const resourceUsageData = {
        labels: ['CPU', '記憶體', '網路I/O', '磁碟I/O'],
        datasets: [
            {
                data: [
                    realTimeMetrics.cpuUsage,
                    realTimeMetrics.memoryUsage,
                    realTimeMetrics.networkIO,
                    realTimeMetrics.diskIO,
                ],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                ],
                borderWidth: 2,
            },
        ],
    }

    // 錯誤率監控
    const errorMonitoringData = {
        labels: trendData.labels.slice(-10),
        datasets: [
            {
                label: '封包遺失率 (%)',
                data: trendData.errorRateHistory
                    .slice(-10)
                    .map((val) => val * 100),
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
            },
        ],
    }

    const getAlertColor = () => {
        switch (alertLevel) {
            case 'critical':
                return '#F44336'
            case 'warning':
                return '#FF9800'
            default:
                return '#4CAF50'
        }
    }

    const getAlertText = () => {
        switch (alertLevel) {
            case 'critical':
                return '🚨 嚴重警報'
            case 'warning':
                return '⚠️ 警告狀態'
            default:
                return '✅ 系統正常'
        }
    }

    return (
        <div className="charts-grid">
            {/* 即時狀態儀表板 */}
            <div className="chart-container">
                <div className="monitoring-header">
                    <h3>📊 即時系統狀態</h3>
                    <div className="monitoring-controls">
                        <button
                            className={`monitor-toggle ${
                                isMonitoring ? 'active' : ''
                            }`}
                            onClick={() => setIsMonitoring(!isMonitoring)}
                        >
                            {isMonitoring ? '⏸️ 暫停' : '▶️ 開始'}
                        </button>
                        <div
                            className="alert-indicator"
                            style={{ color: getAlertColor() }}
                        >
                            {getAlertText()}
                        </div>
                    </div>
                </div>
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div
                            className="metric-value"
                            style={{
                                color:
                                    realTimeMetrics.latency > 30
                                        ? '#FF9800'
                                        : '#4CAF50',
                            }}
                        >
                            {realTimeMetrics.latency.toFixed(1)}ms
                        </div>
                        <div className="metric-label">延遲</div>
                    </div>
                    <div className="metric-card">
                        <div
                            className="metric-value"
                            style={{
                                color:
                                    realTimeMetrics.throughput < 900
                                        ? '#FF9800'
                                        : '#4CAF50',
                            }}
                        >
                            {Math.round(realTimeMetrics.throughput)}
                        </div>
                        <div className="metric-label">吞吐量 (Mbps)</div>
                    </div>
                    <div className="metric-card">
                        <div
                            className="metric-value"
                            style={{
                                color:
                                    realTimeMetrics.packetLoss > 0.05
                                        ? '#F44336'
                                        : '#4CAF50',
                            }}
                        >
                            {(realTimeMetrics.packetLoss * 100).toFixed(3)}%
                        </div>
                        <div className="metric-label">封包遺失</div>
                    </div>
                    <div className="metric-card">
                        <div
                            className="metric-value"
                            style={{
                                color:
                                    realTimeMetrics.jitter > 2
                                        ? '#FF9800'
                                        : '#4CAF50',
                            }}
                        >
                            {realTimeMetrics.jitter.toFixed(1)}ms
                        </div>
                        <div className="metric-label">抖動</div>
                    </div>
                </div>
            </div>

            {/* 性能趨勢圖 */}
            <div className="chart-container">
                <h3>📈 即時性能趨勢</h3>
                <Line
                    data={performanceTrendData}
                    options={{
                        responsive: true,
                        animation: false,
                        plugins: {
                            title: {
                                display: true,
                                text: '近20分鐘性能趨勢',
                                color: 'white',
                            },
                            legend: {
                                labels: { color: 'white' },
                            },
                        },
                        scales: {
                            x: {
                                ticks: { color: 'white' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            },
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {
                                    display: true,
                                    text: '延遲 (ms)',
                                    color: 'white',
                                },
                                ticks: { color: 'white' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: {
                                    display: true,
                                    text: '吞吐量 (Mbps)',
                                    color: 'white',
                                },
                                ticks: { color: 'white' },
                                grid: { drawOnChartArea: false },
                            },
                        },
                        onClick: onChartClick,
                    }}
                />
                <div className="chart-insight">
                    <strong>趨勢分析：</strong>
                    {realTimeMetrics.latency > 30
                        ? '⚠️ 延遲偏高，建議檢查網路狀況'
                        : '✅ 延遲表現良好，系統運行穩定'}
                </div>
            </div>

            {/* 系統資源監控 */}
            <div className="chart-container">
                <h3>💻 系統資源使用</h3>
                <Doughnut
                    data={resourceUsageData}
                    options={{
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: '資源使用率 (%)',
                                color: 'white',
                            },
                            legend: {
                                labels: { color: 'white' },
                                position: 'bottom',
                            },
                        },
                        onClick: onChartClick,
                    }}
                />
                <div className="chart-insight">
                    <strong>資源狀態：</strong>
                    {realTimeMetrics.cpuUsage > 70
                        ? '🔥 CPU使用率偏高，建議優化'
                        : '✅ 系統資源使用正常'}
                </div>
            </div>

            {/* 錯誤率監控 */}
            <div className="chart-container">
                <h3>🚨 錯誤率監控</h3>
                <Bar
                    data={errorMonitoringData}
                    options={{
                        ...createInteractiveChartOptions(
                            '近10分鐘封包遺失率',
                            '遺失率 (%)',
                            '時間'
                        ),
                        onClick: onChartClick,
                    }}
                />
                <div className="chart-insight">
                    <strong>品質評估：</strong>
                    {realTimeMetrics.packetLoss > 0.05
                        ? '🔴 封包遺失率過高，需要關注'
                        : '🟢 網路品質良好，遺失率在正常範圍'}
                </div>
            </div>

            {/* 自動測試結果 */}
            <div className="chart-container">
                <h3>🔧 自動測試結果</h3>
                <div className="test-results">
                    <div className="test-item">
                        <span className="test-name">連線測試</span>
                        <span className="test-status success">✅ 通過</span>
                        <span className="test-time">2秒前</span>
                    </div>
                    <div className="test-item">
                        <span className="test-name">延遲測試</span>
                        <span className="test-status success">✅ 通過</span>
                        <span className="test-time">1分鐘前</span>
                    </div>
                    <div className="test-item">
                        <span className="test-name">吞吐量測試</span>
                        <span
                            className={`test-status ${
                                realTimeMetrics.throughput < 900
                                    ? 'warning'
                                    : 'success'
                            }`}
                        >
                            {realTimeMetrics.throughput < 900
                                ? '⚠️ 警告'
                                : '✅ 通過'}
                        </span>
                        <span className="test-time">3分鐘前</span>
                    </div>
                    <div className="test-item">
                        <span className="test-name">負載測試</span>
                        <span className="test-status success">✅ 通過</span>
                        <span className="test-time">5分鐘前</span>
                    </div>
                </div>
                <div className="chart-insight">
                    <strong>測試摘要：</strong>所有關鍵功能測試通過。
                    系統健康度評分：
                    {Math.round(
                        100 -
                            realTimeMetrics.latency -
                            realTimeMetrics.packetLoss * 100
                    )}
                    /100
                </div>
            </div>
        </div>
    )
}

export default MonitoringTab
