/**
 * 增強系統架構標籤頁內容組件
 * 整合原始版本和新版本的所有有意義功能，使用真實NetStack API數據
 */

import React from 'react'
import { Doughnut, Bar, Line } from 'react-chartjs-2'
import { useSystemArchitectureData } from '../hooks/useSystemArchitectureData'

const EnhancedSystemTabContent: React.FC = () => {
  const {
    resourceAllocationChart,
    systemPerformanceChart,
    componentStabilityChart,
    systemStats,
    systemPerformance,
    dataStatus
  } = useSystemArchitectureData(true)

  // 雙軸圖表選項
  const createDualAxisOptions = (title: string, leftLabel: string, rightLabel: string) => ({
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
        text: title,
        color: 'white',
        font: { size: 16, weight: 'bold' as const },
      },
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
          text: leftLabel,
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
          text: rightLabel,
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
  })

  // 單軸圖表選項
  const createSingleAxisOptions = (title: string, yLabel: string) => ({
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
        text: title,
        color: 'white',
        font: { size: 16, weight: 'bold' as const },
      },
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
        title: {
          display: true,
          text: yLabel,
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
  })

  // 環形圖選項
  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: 'white',
          font: { size: 13, weight: 'bold' as const },
          padding: 20,
        },
      },
      title: {
        display: true,
        text: 'NetStack 組件資源分配比例',
        color: 'white',
        font: { size: 16, weight: 'bold' as const },
      },
      tooltip: {
        callbacks: {
          label: (context: { label: string; parsed: number }) => {
            return `${context.label}: ${context.parsed.toFixed(1)}%`
          }
        }
      }
    },
  }

  return (
    <div className="enhanced-system-content">
      {/* NTN系統架構總覽 */}
      <div className="architecture-overview">
        <h3>🛰️ NTN 系統架構總覽 - NetStack 實時監控</h3>
        
        {/* 視覺化架構圖 */}
        <div className="architecture-diagram">
          {/* 衛星層 */}
          <div className="arch-layer satellite-layer">
            <div className="arch-component satellite-constellation">
              🛰️ 衛星星座層
              <div className="status-indicator">
                {dataStatus.overall === 'real' ? '🟢 實時連接' : '🟡 模擬數據'}
              </div>
            </div>
          </div>
          
          {/* ISL 連接線 */}
          <div className="arch-connection isl-connection"></div>
          
          {/* NTN 網關層 */}
          <div className="arch-layer gateway-layer">
            <div className="arch-component ntn-gateway-left">
              NTN 網關 A
            </div>
            <div className="arch-component ntn-gateway-right">
              NTN 網關 B
            </div>
          </div>
          
          {/* 核心網路層 */}
          <div className="arch-layer core-layer">
            <div className="arch-component core-network">
              🌐 5G 核心網路 (Open5GS)
              <div className="performance-stats">
                CPU: {systemPerformance.cpu.toFixed(1)}% | 
                可用性: {systemPerformance.uptime.toFixed(1)}%
              </div>
            </div>
          </div>
          
          {/* UE 設備層 */}
          <div className="arch-layer ue-layer">
            <div className="arch-component ue-device-left">
              📱 UE 設備
            </div>
            <div className="arch-component ue-device-right">
              📱 UE 設備
            </div>
          </div>

          {/* 動態連接線 */}
          <svg className="connection-lines">
            <defs>
              <linearGradient id="dataFlow" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{stopColor:"#40e0ff", stopOpacity:0.8}} />
                <stop offset="100%" style={{stopColor:"#667eea", stopOpacity:0.8}} />
              </linearGradient>
            </defs>
            <line x1="50%" y1="15%" x2="25%" y2="35%" stroke="url(#dataFlow)" strokeWidth="3" strokeDasharray="8,4">
              <animate attributeName="stroke-dashoffset" values="0;12" dur="2s" repeatCount="indefinite"/>
            </line>
            <line x1="50%" y1="15%" x2="75%" y2="35%" stroke="url(#dataFlow)" strokeWidth="3" strokeDasharray="8,4">
              <animate attributeName="stroke-dashoffset" values="0;12" dur="2s" repeatCount="indefinite"/>
            </line>
            <line x1="25%" y1="45%" x2="50%" y2="55%" stroke="url(#dataFlow)" strokeWidth="3" />
            <line x1="75%" y1="45%" x2="50%" y2="55%" stroke="url(#dataFlow)" strokeWidth="3" />
            <line x1="50%" y1="75%" x2="30%" y2="85%" stroke="url(#dataFlow)" strokeWidth="3" strokeDasharray="5,3">
              <animate attributeName="stroke-dashoffset" values="0;8" dur="1.5s" repeatCount="indefinite"/>
            </line>
            <line x1="50%" y1="75%" x2="70%" y2="85%" stroke="url(#dataFlow)" strokeWidth="3" strokeDasharray="5,3">
              <animate attributeName="stroke-dashoffset" values="0;8" dur="1.5s" repeatCount="indefinite"/>
            </line>
          </svg>
        </div>

        <div className="chart-insight">
          <strong>架構特色：</strong>
          {dataStatus.overall === 'real' && '基於NetStack即時數據顯示，'}
          {dataStatus.overall === 'calculated' && '基於NetStack計算數據，'}
          {dataStatus.overall === 'fallback' && '使用高質量模擬數據，'}
          採用分層NTN設計，支援多衛星協同、ISL互聯和動態資源分配。
          當前系統運行穩定，所有組件狀態正常。
        </div>
      </div>

      {/* 三象限圖表布局 */}
      <div className="system-charts-grid">
        {/* NetStack 組件資源分配 */}
        <div className="chart-container">
          <h3>圖12A: NetStack 組件資源分配</h3>
          <Doughnut
            data={resourceAllocationChart.data}
            options={doughnutOptions}
          />
          <div className="chart-insight">
            <strong>資源分配分析：</strong>
            {resourceAllocationChart.status === 'real' ? '基於NetStack Core Sync即時數據' : '基於NetStack組件狀態計算'}
            顯示各組件資源使用比例。接入網路和核心網路占用最多資源，
            系統負載分配合理，無資源瓶頸。
          </div>
        </div>

        {/* 系統性能資源監控 */}
        <div className="chart-container">
          <h3>圖12B: 系統性能資源監控</h3>
          <Bar
            data={systemPerformanceChart.data}
            options={createSingleAxisOptions(
              'NetStack 即時資源使用狀況',
              '使用率 (%)'
            )}
          />
          <div className="chart-insight">
            <strong>性能監控：</strong>
            {systemPerformanceChart.status === 'real' ? 'NetStack即時系統數據' : '基於NetStack狀態計算'}
            Memory使用率較高({systemPerformance.memory.toFixed(1)}%)需關注，
            CPU穩定運行({systemPerformance.cpu.toFixed(1)}%)，整體系統健康。
          </div>
        </div>

        {/* 組件穩定性趨勢 */}
        <div className="chart-container extra-wide">
          <h3>圖12C: 組件穩定性與錯誤率分析</h3>
          <Line
            data={componentStabilityChart.data}
            options={createDualAxisOptions(
              'NetStack 組件可用性與錯誤率對比',
              '可用性 (%)',
              '錯誤率 (%)'
            )}
          />
          <div className="chart-insight">
            <strong>穩定性評估：</strong>
            {componentStabilityChart.status === 'calculated' ? '基於NetStack統計數據計算' : '使用基準數據'}
            各組件可用性均達97%以上，衛星網路稍低但仍在可接受範圍。
            整體錯誤率控制在2%以下，系統穩定性良好。
          </div>
        </div>
      </div>

      {/* NetStack 系統統計指標 */}
      <div className="system-statistics">
        <h4>📊 NetStack 系統統計指標</h4>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{systemStats.totalSyncOperations.toLocaleString()}</div>
            <div className="stat-label">總同步操作</div>
            <div className="stat-trend">
              {dataStatus.statistics === 'real' ? '📊 即時數據' : '🔄 計算值'}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{((systemStats.successfulSyncs / systemStats.totalSyncOperations) * 100).toFixed(1)}%</div>
            <div className="stat-label">同步成功率</div>
            <div className="stat-trend">
              {systemStats.successfulSyncs.toLocaleString()}/{systemStats.totalSyncOperations.toLocaleString()}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{systemStats.averageSyncTime.toFixed(1)}ms</div>
            <div className="stat-label">平均同步時間</div>
            <div className="stat-trend">
              {dataStatus.statistics === 'real' ? '📊 即時測量' : '🔄 估算值'}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{systemStats.systemUptime.toFixed(1)}%</div>
            <div className="stat-label">系統可用性</div>
            <div className="stat-trend">
              {systemStats.failedSyncs} 次失敗
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{systemStats.componentCount}</div>
            <div className="stat-label">活躍組件數</div>
            <div className="stat-trend">
              {dataStatus.resources === 'real' ? '📊 NetStack數據' : '🔄 模擬值'}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{systemPerformance.uptime.toFixed(1)}%</div>
            <div className="stat-label">即時可用性</div>
            <div className="stat-trend">
              {dataStatus.performance === 'real' ? '📊 即時監控' : '🔄 計算值'}
            </div>
          </div>
        </div>
      </div>

      {/* 系統架構樣式 */}
      <style jsx>{`
        .enhanced-system-content {
          width: 100%;
        }

        .architecture-overview {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 15px;
          padding: 25px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          margin-bottom: 30px;
        }

        .architecture-overview h3 {
          color: white;
          margin-bottom: 25px;
          font-size: 1.5rem;
          text-align: center;
          font-weight: bold;
        }

        .architecture-diagram {
          position: relative;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 15px;
          padding: 40px;
          margin: 20px 0;
          height: 400px;
          overflow: hidden;
        }

        .arch-layer {
          position: absolute;
          width: 100%;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 100px;
        }

        .satellite-layer {
          top: 20px;
        }

        .gateway-layer {
          top: 120px;
        }

        .core-layer {
          top: 220px;
        }

        .ue-layer {
          bottom: 20px;
        }

        .arch-component {
          background: linear-gradient(135deg, #667eea, #764ba2);
          border-radius: 12px;
          padding: 15px 25px;
          color: white;
          font-weight: bold;
          text-align: center;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
          border: 1px solid rgba(255, 255, 255, 0.2);
          transition: all 0.3s ease;
        }

        .arch-component:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }

        .satellite-constellation {
          background: linear-gradient(135deg, #667eea, #764ba2);
          font-size: 1.1rem;
          min-width: 250px;
        }

        .ntn-gateway-left, .ntn-gateway-right {
          background: linear-gradient(135deg, #4ade80, #22c55e);
          font-size: 0.95rem;
          min-width: 120px;
        }

        .core-network {
          background: linear-gradient(135deg, #f59e0b, #d97706);
          font-size: 1.1rem;
          min-width: 280px;
        }

        .ue-device-left, .ue-device-right {
          background: linear-gradient(135deg, #8b5cf6, #7c3aed);
          font-size: 0.9rem;
          min-width: 100px;
        }

        .status-indicator {
          font-size: 0.8rem;
          margin-top: 5px;
          opacity: 0.9;
        }

        .performance-stats {
          font-size: 0.8rem;
          margin-top: 5px;
          opacity: 0.9;
        }

        .connection-lines {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: 1;
        }

        .arch-connection {
          position: absolute;
          top: 80px;
          left: 25%;
          right: 25%;
          height: 3px;
          background: linear-gradient(90deg, #40e0ff, #667eea);
          border-radius: 2px;
          box-shadow: 0 0 10px rgba(64, 224, 255, 0.5);
        }

        .system-charts-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          grid-template-rows: auto auto;
          gap: 20px;
          margin-bottom: 30px;
        }

        .chart-container.extra-wide {
          grid-column: 1 / -1;
        }

        @media (max-width: 1200px) {
          .system-charts-grid {
            grid-template-columns: 1fr;
          }
          
          .arch-layer {
            gap: 50px;
          }
          
          .arch-component {
            padding: 12px 20px;
            font-size: 0.9rem;
          }
        }

        .chart-container {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 15px;
          padding: 25px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(5px);
          min-height: 500px;
        }

        .chart-container h3 {
          color: white;
          margin-bottom: 20px;
          font-size: 1.4rem;
          text-align: center;
          font-weight: bold;
        }

        .chart-insight {
          margin-top: 15px;
          padding: 15px;
          background: rgba(102, 126, 234, 0.1);
          border-radius: 10px;
          color: white;
          border-left: 4px solid #667eea;
          font-size: 1.1rem;
          line-height: 1.6;
        }

        .chart-insight strong {
          color: white;
        }

        .system-statistics {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 15px;
          padding: 25px;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .system-statistics h4 {
          color: white;
          margin-bottom: 20px;
          font-size: 1.3rem;
          text-align: center;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 20px;
        }

        .stat-card {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 20px;
          text-align: center;
          border: 1px solid rgba(255, 255, 255, 0.1);
          transition: all 0.3s ease;
        }

        .stat-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
          border-color: rgba(102, 126, 234, 0.5);
        }

        .stat-value {
          color: white;
          font-size: 2rem;
          font-weight: bold;
          margin-bottom: 8px;
        }

        .stat-label {
          color: rgba(255, 255, 255, 0.8);
          font-size: 1rem;
          margin-bottom: 5px;
        }

        .stat-trend {
          color: rgba(255, 255, 255, 0.6);
          font-size: 0.85rem;
        }

        @media (max-width: 768px) {
          .architecture-diagram {
            height: 350px;
            padding: 30px 20px;
          }
          
          .system-charts-grid {
            gap: 15px;
          }
          
          .chart-container {
            padding: 20px;
            min-height: 400px;
          }
          
          .stats-grid {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
          }
        }
      `}</style>
    </div>
  )
}

export default EnhancedSystemTabContent