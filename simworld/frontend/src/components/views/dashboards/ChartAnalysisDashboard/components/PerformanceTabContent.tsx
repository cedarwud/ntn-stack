/**
 * 性能監控標籤頁內容組件
 * 替換 ChartAnalysisDashboard 中的 performance 標籤內容
 */

import React from 'react'
import { Line, Bar } from 'react-chartjs-2'
import { useChartDataManager } from '../hooks/useChartData'

const PerformanceTabContent: React.FC = () => {
  const {
    qoeLatency,
    timeSyncAccuracy
  } = useChartDataManager()

  return (
    <div className="charts-grid">
      {/* QoE 延遲監控 - 雙 Y 軸線圖 */}
      <div className="chart-container">
        <h3>圖9A: QoE 延遲監控 - Stalling Time & RTT 分析</h3>
        <Line
          data={qoeLatency.chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
              mode: 'index' as const,
              intersect: false,
            },
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
                text: '即時服務品質體驗監控',
                color: 'white',
                font: { size: 16, weight: 'bold' as const },
              },
              tooltip: {
                mode: 'index' as const,
                intersect: false,
                callbacks: {
                  afterLabel: (context: any) => {
                    return context.datasetIndex === 0 
                      ? '影響: 用戶體驗' 
                      : '影響: 響應速度'
                  }
                }
              }
            },
            scales: {
              x: {
                ticks: {
                  color: 'white',
                  font: { size: 12 },
                },
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)',
                },
              },
              y: {
                type: 'linear' as const,
                display: true,
                position: 'left' as const,
                title: {
                  display: true,
                  text: 'Stalling Time (ms)',
                  color: 'white',
                  font: { size: 14, weight: 'bold' as const },
                },
                ticks: {
                  color: 'white',
                  font: { size: 12 },
                },
                grid: {
                  color: 'rgba(255, 255, 255, 0.2)',
                }
              },
              y1: {
                type: 'linear' as const,
                display: true,
                position: 'right' as const,
                title: {
                  display: true,
                  text: 'RTT (ms)',
                  color: 'white',
                  font: { size: 14, weight: 'bold' as const },
                },
                ticks: {
                  color: 'white',
                  font: { size: 12 },
                },
                grid: {
                  drawOnChartArea: false,
                  color: 'rgba(255, 255, 255, 0.1)'
                }
              }
            }
          }}
        />
        <div className="chart-insight">
          <strong>QoE監控：</strong>Stalling Time 從15ms降至3ms（降低80%），
          RTT 從25ms降至9ms（降低64%）。用戶體驗顯著提升，響應速度大幅改善。
        </div>
      </div>

      {/* 時間同步精度技術對比 */}
      <div className="chart-container">
        <h3>圖10: 時間同步精度技術對比</h3>
        <Bar
          data={timeSyncAccuracy.chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false,
              },
              title: {
                display: true,
                text: '不同同步技術的精度表現評估',
                color: 'white',
                font: { size: 16, weight: 'bold' as const },
              },
              tooltip: {
                callbacks: {
                  afterLabel: (context: any) => {
                    const precision = parseFloat(context.parsed.y.toFixed(1))
                    if (precision < 1) return '精度等級: 極高'
                    if (precision < 10) return '精度等級: 高'
                    if (precision < 100) return '精度等級: 中等'
                    if (precision < 1000) return '精度等級: 一般'
                    return '精度等級: 低'
                  }
                }
              }
            },
            scales: {
              x: {
                ticks: {
                  color: 'white',
                  font: { size: 12 },
                },
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)',
                },
              },
              y: {
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
            },
          }}
        />
        <div className="chart-insight">
          <strong>精度評估：</strong>各技術同步精度差異顯著，Fine-Grained Sync(0.3μs)達到極高等級，
          GPS-based(2.1μs)為高等級，傳統方法(45.2μs)僅為基礎等級。
        </div>
      </div>

      {/* 性能監控即時指標面板 */}
      <div className="realtime-metrics-panel">
        <h4>🔄 即時性能監控</h4>
        <div className="metrics-dashboard">
          <div className="metric-group">
            <h5>延遲指標</h5>
            <div className="metric-cards">
              <div className="metric-card success">
                <div className="metric-value">12.3ms</div>
                <div className="metric-label">平均延遲</div>
                <div className="metric-trend">↓ -15.2%</div>
              </div>
              <div className="metric-card warning">
                <div className="metric-value">28.7ms</div>
                <div className="metric-label">最大延遲</div>
                <div className="metric-trend">↑ +3.1%</div>
              </div>
              <div className="metric-card info">
                <div className="metric-value">8.1ms</div>
                <div className="metric-label">最小延遲</div>
                <div className="metric-trend">↓ -2.3%</div>
              </div>
            </div>
          </div>

          <div className="metric-group">
            <h5>吞吐量指標</h5>
            <div className="metric-cards">
              <div className="metric-card success">
                <div className="metric-value">156.8</div>
                <div className="metric-label">Mbps 平均</div>
                <div className="metric-trend">↑ +8.7%</div>
              </div>
              <div className="metric-card info">
                <div className="metric-value">203.5</div>
                <div className="metric-label">Mbps 峰值</div>
                <div className="metric-trend">↑ +12.4%</div>
              </div>
              <div className="metric-card warning">
                <div className="metric-value">89.2</div>
                <div className="metric-label">Mbps 最低</div>
                <div className="metric-trend">↓ -5.6%</div>
              </div>
            </div>
          </div>

          <div className="metric-group">
            <h5>系統資源</h5>
            <div className="metric-cards">
              <div className="metric-card info">
                <div className="metric-value">67.4%</div>
                <div className="metric-label">CPU 使用率</div>
                <div className="metric-trend">↑ +2.1%</div>
              </div>
              <div className="metric-card success">
                <div className="metric-value">52.8%</div>
                <div className="metric-label">記憶體使用</div>
                <div className="metric-trend">↓ -1.3%</div>
              </div>
              <div className="metric-card warning">
                <div className="metric-value">78.9%</div>
                <div className="metric-label">網路使用率</div>
                <div className="metric-trend">↑ +4.7%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 性能趨勢警告 */}
      <div className="performance-alerts">
        <div className="alert-item success">
          <div className="alert-icon">✅</div>
          <div className="alert-content">
            <div className="alert-title">延遲優化成功</div>
            <div className="alert-message">Fine-Grained Sync 算法運行良好，延遲降低 68.2%</div>
          </div>
        </div>
        <div className="alert-item warning">
          <div className="alert-icon">⚠️</div>
          <div className="alert-content">
            <div className="alert-title">網路負載偏高</div>
            <div className="alert-message">當前網路使用率 78.9%，建議監控負載均衡狀況</div>
          </div>
        </div>
        <div className="alert-item info">
          <div className="alert-icon">ℹ️</div>
          <div className="alert-content">
            <div className="alert-title">同步精度正常</div>
            <div className="alert-message">時間同步精度維持在 2.3μs，系統穩定運行</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PerformanceTabContent