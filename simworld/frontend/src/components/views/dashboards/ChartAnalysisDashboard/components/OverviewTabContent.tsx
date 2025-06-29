/**
 * 核心圖表標籤頁內容組件
 * 替換 ChartAnalysisDashboard 中的 overview 標籤內容
 */

import React from 'react'
import { Bar } from 'react-chartjs-2'

interface OverviewTabContentProps {
  handoverLatencyData: any
  constellationComparisonData: any
  sixScenarioChartData: any
  createInteractiveChartOptions: (title: string, yLabel: string, xLabel?: string) => any
}

const OverviewTabContent: React.FC<OverviewTabContentProps> = ({
  handoverLatencyData,
  constellationComparisonData,
  sixScenarioChartData,
  createInteractiveChartOptions
}) => {
  return (
    <div className="charts-grid">
      {/* Handover 延遲分解分析 */}
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
          <strong>核心突破：</strong>本論文提出的同步算法
          + Xn 加速換手方案， 實現了從標準 NTN 的 ~250ms
          到 ~21ms 的革命性延遲降低，減少 91.6%。 超越
          NTN-GS (153ms) 和 NTN-SMN (158ms)
          方案，真正實現近零延遲換手。
          <br />
          <br />
          <strong>📊 統計驗證：</strong>
          改進效果 p &lt; 0.001 (***), 效應大小 Large
          (Cohen's d = 2.8), 信賴度 99.9%
        </div>
      </div>

      {/* 雙星座性能對比 */}
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
          憑藉較低軌道在延遲和覆蓋率方面領先， Kuiper
          (630km) 則在換手頻率控制上表現更佳。兩者在 QoE
          指標上相近， 為不同應用場景提供最適選擇。
        </div>
      </div>

      {/* 六場景換手延遲分析 */}
      <div className="chart-container extra-large">
        <h3>🎆 圖8(a)-(f): 六場景換手延遲全面對比分析</h3>
        <Bar
          data={sixScenarioChartData}
          options={{
            ...createInteractiveChartOptions(
              '四種方案在八種場景下的換手延遲對比',
              '延遲 (ms)'
            ),
            scales: {
              ...createInteractiveChartOptions('', '')
                .scales,
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
              marginLeft: '0.5rem',
              fontSize: '1.1rem',
            }}
          >
            SL：Starlink、KP：Kuiper、F：Flexible、C：Consistent
            <br />
            同：同向、全：全方向
          </span>
          <br />
          <br />
          <strong>多場景對比：</strong>
          本方案在八種應用場景下均實現領先性能，相較 NTN
          標準方案減少 90% 以上延遲。Flexible
          策略在動態場景下表現較佳，Consistent
          策略在穩定環境下更適用。雙星座部署（Starlink +
          Kuiper）可提供互補的服務覆蓋，實現最佳化的網路效能和可靠性。
        </div>
      </div>
    </div>
  )
}

export default OverviewTabContent