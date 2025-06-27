/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react'
import { Bar } from 'react-chartjs-2'
import { createInteractiveChartOptions } from '../utils/chartConfig'

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
    console.log(
        '🔍 OverviewTab render - handoverLatencyData:',
        handoverLatencyData ? 'exists' : 'null'
    )

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
                    的革命性延遲降低，減少 91.6%。
                </div>
            </div>
        </div>
    )
}

export default OverviewTab
