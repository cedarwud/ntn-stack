/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useMemo, memo } from 'react'
import { Bar } from 'react-chartjs-2'

interface OverviewTabProps {
    handoverLatencyData: any
    constellationComparisonData: any
    sixScenarioChartData: any
    onChartClick: (event: any, elements: any[], chart: any) => void
}

const OverviewTab: React.FC<OverviewTabProps> = ({
    handoverLatencyData,
    constellationComparisonData,
    sixScenarioChartData,
    onChartClick,
}) => {
    // 使用 useMemo 緩存 options 對象，避免每次渲染都創建新對象
    const chartOptions = useMemo(
        () => ({
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '四種換手方案延遲對比 (ms)',
                    color: 'white',
                },
                legend: {
                    labels: {
                        color: 'white',
                    },
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '換手階段',
                        color: 'white',
                    },
                    ticks: {
                        color: 'white',
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: '延遲 (ms)',
                        color: 'white',
                    },
                    ticks: {
                        color: 'white',
                    },
                },
            },
        }),
        []
    ) // 空依賴數組，只創建一次

    return (
        <div className="charts-grid">
            {/* 🎉 最終測試：完整功能恢復 */}
            {handoverLatencyData && (
                <div className="chart-container">
                    <h3>📊 換手延遲對比分析</h3>
                    <div style={{ height: '400px' }}>
                        <Bar
                            data={handoverLatencyData}
                            options={{
                                ...chartOptions,
                                onClick: onChartClick,
                            }}
                        />
                    </div>
                    <div className="chart-insight">
                        <p>
                            <strong>延遲對比分析</strong>
                            ：本圖表展示了四種不同換手方案在各個階段的延遲表現。
                        </p>
                        <p>
                            分析結果顯示，<strong>Proposed</strong>{' '}
                            方案在所有階段都展現出最低的延遲， 相比傳統 NTN
                            方案有顯著改善，特別是在準備階段和同步階段的延遲降低超過90%。
                        </p>
                        <p>
                            <strong>關鍵發現</strong>：NTN-GS 和 NTN-SMN
                            方案的性能接近， 而 Proposed
                            方案通過創新的預測性換手機制實現了延遲的大幅降低。
                        </p>
                    </div>
                </div>
            )}

            {/* 雙星座比較圖表 */}
            {constellationComparisonData &&
                constellationComparisonData.labels && (
                    <div className="chart-container">
                        <h3>📊 雙星座比較</h3>
                        <div style={{ height: '300px' }}>
                            <Bar
                                data={constellationComparisonData}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: {
                                        title: {
                                            display: true,
                                            text: '不同星座配置效能比較',
                                            color: 'white',
                                        },
                                        legend: {
                                            labels: { color: 'white' },
                                        },
                                    },
                                    scales: {
                                        x: { ticks: { color: 'white' } },
                                        y: { ticks: { color: 'white' } },
                                    },
                                }}
                            />
                        </div>
                        <div className="chart-insight">
                            <p>
                                <strong>星座配置分析</strong>
                                ：比較不同衛星星座配置下的系統性能表現，
                                包括覆蓋率、延遲、多普勒效應等關鍵指標。
                            </p>
                        </div>
                    </div>
                )}

            {/* 六場景分析圖表 */}
            {sixScenarioChartData && sixScenarioChartData.labels && (
                <div className="chart-container">
                    <h3>📊 六場景分析</h3>
                    <div style={{ height: '300px' }}>
                        <Bar
                            data={sixScenarioChartData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    title: {
                                        display: true,
                                        text: '六種場景效能分析',
                                        color: 'white',
                                    },
                                    legend: {
                                        labels: { color: 'white' },
                                    },
                                },
                                scales: {
                                    x: { ticks: { color: 'white' } },
                                    y: { ticks: { color: 'white' } },
                                },
                            }}
                        />
                    </div>
                    <div className="chart-insight">
                        <p>
                            <strong>場景效能分析</strong>
                            ：在六種不同部署場景下的系統效能評估，
                            包括密集城市、都市、鄉村等不同環境條件下的表現對比。
                        </p>
                        <p>
                            分析顯示在高密度環境下，系統需要更多的資源配置來維持服務品質，
                            而在鄉村環境下則可以達到較佳的能源效率比。
                        </p>
                    </div>
                </div>
            )}
        </div>
    )
}

export default memo(OverviewTab, (prevProps, nextProps) => {
    // 簡化比較邏輯，只比較關鍵的 props
    const handoverDataSame =
        prevProps.handoverLatencyData === nextProps.handoverLatencyData
    const constellationDataSame =
        prevProps.constellationComparisonData ===
        nextProps.constellationComparisonData
    const sixScenarioDataSame =
        prevProps.sixScenarioChartData === nextProps.sixScenarioChartData
    const onClickSame = prevProps.onChartClick === nextProps.onChartClick

    return (
        handoverDataSame &&
        constellationDataSame &&
        sixScenarioDataSame &&
        onClickSame
    )
})
