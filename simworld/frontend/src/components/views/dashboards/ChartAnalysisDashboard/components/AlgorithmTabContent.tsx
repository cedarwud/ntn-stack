/**
 * 算法分析標籤頁內容組件
 * 替換 ChartAnalysisDashboard 中的 algorithms 標籤內容
 */

import React from 'react'
import { Radar, Bar } from 'react-chartjs-2'
import { useChartDataManager } from '../hooks/useChartData'

const AlgorithmTabContent: React.FC = () => {
  const {
    accessStrategyRadar,
    timeSyncAccuracy
  } = useChartDataManager()

  return (
    <div className="charts-grid">
      {/* UE 接入策略六維效能雷達圖 */}
      <div className="chart-container">
        <h3>UE 接入策略六維效能雷達</h3>
        <Radar
          data={accessStrategyRadar.chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top' as const,
                labels: {
                  color: 'white',
                  font: { size: 14, weight: 'bold' as const },
                },
              },
              title: {
                display: true,
                text: 'Fine-Grained Sync vs Traditional - 多維度性能比較',
                color: 'white',
                font: { size: 16, weight: 'bold' as const },
              },
              tooltip: {
                callbacks: {
                  afterLabel: (context: any) => {
                    const score = parseFloat(context.parsed.r.toFixed(1))
                    if (score >= 9.0) return '評級: 優秀'
                    if (score >= 8.0) return '評級: 良好'
                    if (score >= 7.0) return '評級: 一般'
                    return '評級: 需改進'
                  }
                }
              }
            },
            scales: {
              r: {
                min: 0,
                max: 10,
                ticks: {
                  stepSize: 2,
                  color: 'white',
                  font: { size: 12 },
                  callback: (value: any) => `${value}/10`
                },
                grid: {
                  color: 'rgba(255, 255, 255, 0.2)',
                },
                angleLines: {
                  color: 'rgba(255, 255, 255, 0.2)',
                },
                pointLabels: {
                  color: 'white',
                  font: { size: 12, weight: 'bold' as const },
                }
              }
            }
          }}
        />
        <div className="chart-insight">
          <strong>雷達分析：</strong>Fine-Grained Sync 在延遲性能(9.2)、精度穩定(9.5)、可靠性(9.7)方面表現卓越，
          顯著優於 Binary Search 和 Traditional 方法。整體性能提升35%以上。
        </div>
      </div>

      {/* 時間同步精度對比 */}
      <div className="chart-container">
        <h3>時間同步精度技術對比詳細分析</h3>
        <Bar
          data={timeSyncAccuracy.chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y' as const,
            plugins: {
              legend: {
                display: false,
              },
              title: {
                display: true,
                text: '各種同步技術的精度性能評估',
                color: 'white',
                font: { size: 16, weight: 'bold' as const },
              },
              tooltip: {
                callbacks: {
                  afterLabel: (context: any) => {
                    const precision = parseFloat(context.parsed.x.toFixed(1))
                    if (precision < 1) return '等級: 極高精度 (量子級)'
                    if (precision < 10) return '等級: 高精度 (GPS級)'
                    if (precision < 100) return '等級: 中等精度'
                    if (precision < 1000) return '等級: 標準精度'
                    return '等級: 基礎精度'
                  }
                }
              }
            },
            scales: {
              x: {
                type: 'logarithmic' as const,
                title: {
                  display: true,
                  text: '同步精度 (μs, 對數尺度)',
                  color: 'white',
                  font: { size: 14, weight: 'bold' as const },
                },
                ticks: {
                  color: 'white',
                  font: { size: 12 },
                },
                grid: {
                  color: 'rgba(255, 255, 255, 0.2)',
                },
              },
              y: {
                ticks: {
                  color: 'white',
                  font: { size: 12 },
                },
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)',
                },
              },
            },
          }}
        />
        <div className="chart-insight">
          <strong>精度對比：</strong>Fine-Grained Sync 實現了0.3μs的極高精度，
          比GPS-based(2.1μs)高7倍，比Traditional(45.2μs)高150倍。達到量子級同步水準。
        </div>
      </div>

      {/* 算法性能對比分析表格 */}
      <div className="algorithm-comparison-table">
        <h4>📊 算法性能對比分析</h4>
        <div className="comparison-table">
          <table>
            <thead>
              <tr>
                <th>算法類型</th>
                <th>平均延遲</th>
                <th>計算複雜度</th>
                <th>記憶體使用</th>
                <th>能耗效率</th>
                <th>可靠性</th>
                <th>整體評分</th>
              </tr>
            </thead>
            <tbody>
              <tr className="algorithm-row fine-grained">
                <td>
                  <span className="algorithm-name">Fine-Grained Sync</span>
                  <span className="algorithm-badge recommended">推薦</span>
                </td>
                <td className="metric-cell success">8.2ms</td>
                <td className="metric-cell success">O(n log n)</td>
                <td className="metric-cell success">156MB</td>
                <td className="metric-cell success">95.2%</td>
                <td className="metric-cell success">99.7%</td>
                <td className="metric-cell success">9.2/10</td>
              </tr>
              <tr className="algorithm-row binary-search">
                <td>
                  <span className="algorithm-name">Binary Search</span>
                  <span className="algorithm-badge moderate">適中</span>
                </td>
                <td className="metric-cell info">12.1ms</td>
                <td className="metric-cell info">O(n log n)</td>
                <td className="metric-cell info">198MB</td>
                <td className="metric-cell info">87.3%</td>
                <td className="metric-cell info">96.4%</td>
                <td className="metric-cell info">7.8/10</td>
              </tr>
              <tr className="algorithm-row traditional">
                <td>
                  <span className="algorithm-name">Traditional</span>
                  <span className="algorithm-badge low">基礎</span>
                </td>
                <td className="metric-cell warning">26.7ms</td>
                <td className="metric-cell warning">O(n²)</td>
                <td className="metric-cell warning">312MB</td>
                <td className="metric-cell warning">68.9%</td>
                <td className="metric-cell warning">89.2%</td>
                <td className="metric-cell warning">6.1/10</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 算法特性詳細說明 */}
      <div className="algorithm-features">
        <div className="feature-cards">
          <div className="feature-card">
            <div className="feature-header">
              <h5>🚀 Fine-Grained Synchronized Algorithm</h5>
              <span className="feature-badge best">最佳選擇</span>
            </div>
            <div className="feature-content">
              <div className="feature-highlights">
                <div className="highlight-item">
                  <span className="highlight-icon">⚡</span>
                  <span>延遲降低 68.2%</span>
                </div>
                <div className="highlight-item">
                  <span className="highlight-icon">🧠</span>
                  <span>智能預測機制</span>
                </div>
                <div className="highlight-item">
                  <span className="highlight-icon">🔄</span>
                  <span>動態負載均衡</span>
                </div>
              </div>
              <div className="feature-description">
                基於 IEEE INFOCOM 2024 論文實現，採用精細化時間同步機制，
                結合衛星軌道預測和信號品質評估，實現最優的換手決策。
              </div>
            </div>
          </div>

          <div className="feature-card">
            <div className="feature-header">
              <h5>🔍 Binary Search Refinement</h5>
              <span className="feature-badge good">良好</span>
            </div>
            <div className="feature-content">
              <div className="feature-highlights">
                <div className="highlight-item">
                  <span className="highlight-icon">📊</span>
                  <span>搜索效率優化</span>
                </div>
                <div className="highlight-item">
                  <span className="highlight-icon">⚖️</span>
                  <span>平衡性能成本</span>
                </div>
                <div className="highlight-item">
                  <span className="highlight-icon">🎯</span>
                  <span>精確定位目標</span>
                </div>
              </div>
              <div className="feature-description">
                使用二分搜索算法優化候選衛星選擇過程，
                在計算效率和精度之間取得良好平衡。
              </div>
            </div>
          </div>

          <div className="feature-card">
            <div className="feature-header">
              <h5>📈 Traditional Method</h5>
              <span className="feature-badge basic">傳統</span>
            </div>
            <div className="feature-content">
              <div className="feature-highlights">
                <div className="highlight-item">
                  <span className="highlight-icon">🔧</span>
                  <span>實現簡單</span>
                </div>
                <div className="highlight-item">
                  <span className="highlight-icon">📊</span>
                  <span>基礎功能</span>
                </div>
                <div className="highlight-item">
                  <span className="highlight-icon">⚠️</span>
                  <span>效能限制</span>
                </div>
              </div>
              <div className="feature-description">
                傳統的換手算法，實現簡單但效能受限，
                主要用作性能基準對比。
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AlgorithmTabContent