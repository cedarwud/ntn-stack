/**
 * 核心圖表標籤頁內容組件
 * 替換 ChartAnalysisDashboard 中的 overview 標籤內容
 */

import React from 'react'
import { BaseBarChart } from '../../../../charts/base/BaseBarChart'
import { BaseDoughnutChart } from '../../../../charts/base/BasePieChart'
import { useChartDataManager } from '../../../../../hooks/useChartData'

const OverviewTabContent: React.FC = () => {
  const {
    handoverLatency,
    performanceComparison,
    systemArchitecture,
    sixScenarioLatency,
    computationalComplexity
  } = useChartDataManager()

  return (
    <div className="overview-tab-content">
      {/* 第一行：Handover 延遲分解分析 */}
      <div className="chart-row">
        <div className="chart-container">
          <BaseBarChart
            title="📊 圖3: Handover 延遲分解分析"
            subtitle="Fine-Grained Sync vs Traditional - 各階段延遲對比"
            data={handoverLatency.chartData}
            options={{
              stacked: false,
              showValues: true,
              showLegend: true,
              maintainAspectRatio: false
            }}
            height={350}
          />
        </div>
      </div>

      {/* 第二行：雙星座性能對比 */}
      <div className="chart-row">
        <div className="chart-container">
          <BaseBarChart
            title="🚀 圖4: 雙星座六維性能全景對比"
            subtitle="Starlink vs OneWeb - 多維度性能評估"
            data={performanceComparison.chartData}
            options={{
              stacked: false,
              showValues: true,
              showLegend: true,
              maintainAspectRatio: false,
              plugins: {
                tooltip: {
                  callbacks: {
                    afterLabel: (context) => {
                      const metricUnits = {
                        '延遲 (ms)': 'ms',
                        '吞吐量 (Mbps)': 'Mbps',
                        '成功率 (%)': '%',
                        '能耗 (W)': 'W',
                        'CPU 使用率 (%)': '%',
                        '記憶體使用率 (%)': '%'
                      }
                      const label = context.label as keyof typeof metricUnits
                      return `單位: ${metricUnits[label] || ''}`
                    }
                  }
                }
              }
            }}
            height={350}
          />
        </div>
      </div>

      {/* 第三行：六場景換手延遲分析 */}
      <div className="chart-row">
        <div className="chart-container">
          <BaseBarChart
            title="🌍 圖5: 六場景換手延遲全面對比分析"
            subtitle="不同環境下的算法性能表現"
            data={sixScenarioLatency.chartData}
            options={{
              stacked: false,
              showValues: true,
              showLegend: true,
              maintainAspectRatio: false,
              plugins: {
                tooltip: {
                  callbacks: {
                    afterLabel: () => '延遲越低性能越好'
                  }
                }
              }
            }}
            height={350}
          />
        </div>
      </div>

      {/* 第四行：兩個並排的圖表 */}
      <div className="chart-row chart-row-split">
        {/* 計算複雜度可擴展性驗證 */}
        <div className="chart-container chart-half">
          <BaseBarChart
            title="⚡ 圖6: 計算複雜度可擴展性驗證"
            subtitle="算法擴展性能測試"
            data={computationalComplexity.chartData}
            options={{
              stacked: false,
              showValues: false,
              showLegend: true,
              maintainAspectRatio: false,
              scales: {
                y: {
                  type: 'logarithmic',
                  title: {
                    display: true,
                    text: '計算時間 (ms, 對數尺度)'
                  }
                }
              },
              plugins: {
                tooltip: {
                  callbacks: {
                    afterLabel: () => 'O(n) vs O(n²) 複雜度對比'
                  }
                }
              }
            }}
            height={350}
          />
        </div>

        {/* 系統架構組件資源分配 */}
        <div className="chart-container chart-half">
          <BaseDoughnutChart
            title="🏗️ 圖7: 系統架構組件資源分配"
            subtitle="各模組 CPU 資源佔用分析"
            data={systemArchitecture.chartData}
            options={{
              cutout: '60%',
              showPercentages: true,
              showLegend: true,
              legendPosition: 'right',
              maintainAspectRatio: false,
              plugins: {
                tooltip: {
                  callbacks: {
                    afterLabel: (context) => `資源佔用: ${context.parsed}%`
                  }
                }
              }
            }}
            height={350}
          />
        </div>
      </div>

      {/* 性能指標總結卡片 */}
      <div className="metrics-summary-row">
        <div className="metrics-card">
          <h4>🎯 核心性能指標</h4>
          <div className="metrics-grid">
            <div className="metric-item">
              <span className="metric-label">平均延遲降低</span>
              <span className="metric-value success">-68.2%</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">計算效率提升</span>
              <span className="metric-value success">+127.5%</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">系統穩定性</span>
              <span className="metric-value success">99.7%</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">資源利用率</span>
              <span className="metric-value info">78.4%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OverviewTabContent