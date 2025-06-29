/**
 * 系統架構標籤頁內容組件
 * 系統架構圖和組件分析
 */

import React from 'react'
import { Bar, Pie, Line } from 'react-chartjs-2'

const SystemTabContent: React.FC = () => {
  // 系統資源使用情況
  const systemResourceData = {
    labels: ['CPU', 'Memory', 'Storage', 'Network', 'GPU'],
    datasets: [
      {
        label: '當前使用率 (%)',
        data: [72, 85, 45, 68, 33],
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
        ],
        borderWidth: 2,
      },
    ],
  }

  // 模組性能分析
  const modulePerformanceData = {
    labels: ['信號處理', '同步控制', '換手管理', '資源分配', '干擾消除', '路由選擇'],
    datasets: [
      {
        label: '處理延遲 (ms)',
        data: [3.2, 5.8, 12.5, 8.1, 15.3, 6.7],
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 2,
      },
      {
        label: '吞吐量 (Mbps)',
        data: [850, 720, 450, 680, 320, 590],
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        yAxisID: 'y1',
      },
    ],
  }

  // 系統穩定性趨勢
  const stabilityTrendData = {
    labels: ['第1天', '第2天', '第3天', '第4天', '第5天', '第6天', '第7天'],
    datasets: [
      {
        label: '可用性 (%)',
        data: [99.2, 99.5, 99.3, 99.7, 99.8, 99.6, 99.9],
        borderColor: 'rgba(34, 197, 94, 1)',
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        tension: 0.4,
        fill: true,
      },
      {
        label: '錯誤率 (%)',
        data: [0.8, 0.5, 0.7, 0.3, 0.2, 0.4, 0.1],
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.4,
        fill: true,
      },
    ],
  }

  const chartOptions = {
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
        color: 'white',
        font: { size: 16, weight: 'bold' as const },
      },
    },
    scales: {
      x: {
        ticks: { color: 'white', font: { size: 12 } },
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
      },
      y: {
        ticks: { color: 'white', font: { size: 12 } },
        grid: { color: 'rgba(255, 255, 255, 0.2)' },
      },
    },
  }

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: 'white',
          font: { size: 14, weight: 'bold' as const },
        },
      },
      title: {
        display: true,
        color: 'white',
        font: { size: 16, weight: 'bold' as const },
      },
    },
  }

  return (
    <div className="charts-grid">
      {/* 系統架構圖 */}
      <div className="chart-container extra-large">
        <h3>NTN 系統架構總覽</h3>
        
        {/* 系統架構示意圖 */}
        <div style={{ 
          background: 'rgba(0, 0, 0, 0.3)', 
          borderRadius: '10px', 
          padding: '30px', 
          margin: '20px 0',
          position: 'relative',
          height: '300px'
        }}>
          {/* 衛星層 */}
          <div style={{
            position: 'absolute', top: '20px', left: '50%', transform: 'translateX(-50%)',
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            borderRadius: '10px', padding: '10px 20px', color: 'white', fontWeight: 'bold'
          }}>
            🛰️ 衛星星座層
          </div>
          
          {/* ISL 連接線 */}
          <div style={{
            position: 'absolute', top: '70px', left: '30%', right: '30%', height: '2px',
            background: 'linear-gradient(90deg, #40e0ff, #667eea)', borderRadius: '1px'
          }}></div>
          
          {/* NTN 網關 */}
          <div style={{
            position: 'absolute', top: '100px', left: '20%',
            background: 'linear-gradient(135deg, #4ade80, #22c55e)',
            borderRadius: '8px', padding: '8px 15px', color: 'white', fontSize: '14px'
          }}>
            NTN 網關
          </div>
          
          <div style={{
            position: 'absolute', top: '100px', right: '20%',
            background: 'linear-gradient(135deg, #4ade80, #22c55e)',
            borderRadius: '8px', padding: '8px 15px', color: 'white', fontSize: '14px'
          }}>
            NTN 網關
          </div>
          
          {/* 核心網路 */}
          <div style={{
            position: 'absolute', top: '150px', left: '50%', transform: 'translateX(-50%)',
            background: 'linear-gradient(135deg, #f59e0b, #d97706)',
            borderRadius: '10px', padding: '12px 25px', color: 'white', fontWeight: 'bold'
          }}>
            🌐 5G 核心網路
          </div>
          
          {/* UE 設備 */}
          <div style={{
            position: 'absolute', bottom: '20px', left: '25%',
            background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
            borderRadius: '8px', padding: '8px 15px', color: 'white', fontSize: '14px'
          }}>
            📱 UE 設備
          </div>
          
          <div style={{
            position: 'absolute', bottom: '20px', right: '25%',
            background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
            borderRadius: '8px', padding: '8px 15px', color: 'white', fontSize: '14px'
          }}>
            📱 UE 設備
          </div>
          
          {/* 連接線 */}
          <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
            <defs>
              <linearGradient id="connectionGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{stopColor:"#40e0ff", stopOpacity:0.8}} />
                <stop offset="100%" style={{stopColor:"#667eea", stopOpacity:0.8}} />
              </linearGradient>
            </defs>
            <line x1="50%" y1="60" x2="30%" y2="120" stroke="url(#connectionGradient)" strokeWidth="2" strokeDasharray="5,5" />
            <line x1="50%" y1="60" x2="70%" y2="120" stroke="url(#connectionGradient)" strokeWidth="2" strokeDasharray="5,5" />
            <line x1="30%" y1="140" x2="50%" y2="170" stroke="url(#connectionGradient)" strokeWidth="2" />
            <line x1="70%" y1="140" x2="50%" y2="170" stroke="url(#connectionGradient)" strokeWidth="2" />
            <line x1="50%" y1="200" x2="35%" y2="240" stroke="url(#connectionGradient)" strokeWidth="2" strokeDasharray="3,3" />
            <line x1="50%" y1="200" x2="65%" y2="240" stroke="url(#connectionGradient)" strokeWidth="2" strokeDasharray="3,3" />
          </svg>
        </div>

        <div className="chart-insight">
          <strong>架構特色：</strong>採用分層設計，衛星星座層提供全球覆蓋，
          NTN網關負責協議轉換，5G核心網確保服務品質。
          系統支援多衛星同時接入，實現高可靠性和低延遲通信。
        </div>
      </div>

      {/* 系統資源使用 */}
      <div className="chart-container">
        <h3>系統資源使用狀況</h3>
        <Pie data={systemResourceData} options={{
          ...pieOptions,
          plugins: {
            ...pieOptions.plugins,
            title: { ...pieOptions.plugins.title, text: '各項資源當前使用率分佈' }
          }
        }} />
        <div className="chart-insight">
          <strong>資源狀態：</strong>記憶體使用率最高（85%），需要關注。
          CPU 使用率穩定（72%），GPU 資源充足（33%）。
          整體系統運行健康，有進一步優化空間。
        </div>
      </div>

      {/* 模組性能分析 */}
      <div className="chart-container">
        <h3>核心模組性能分析</h3>
        <Bar data={modulePerformanceData} options={{
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            title: { ...chartOptions.plugins.title, text: '各功能模組處理效能統計' }
          },
          scales: {
            x: {
              ...chartOptions.scales.x,
            },
            y: {
              type: 'linear' as const,
              display: true,
              position: 'left' as const,
              title: {
                display: true,
                text: '處理延遲 (ms)',
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
              },
              ticks: { color: 'white', font: { size: 12 } },
              grid: { color: 'rgba(255, 255, 255, 0.2)' },
            },
            y1: {
              type: 'linear' as const,
              display: true,
              position: 'right' as const,
              title: {
                display: true,
                text: '吞吐量 (Mbps)',
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
              },
              ticks: { color: 'white', font: { size: 12 } },
              grid: {
                drawOnChartArea: false,
              },
            },
          },
        }} />
        <div className="chart-insight">
          <strong>模組效能：</strong>信號處理模組延遲最低（3.2ms），吞吐量最高（850Mbps）。
          干擾消除模組處理複雜度較高但效果顯著。各模組均達到設計要求。
        </div>
      </div>

      {/* 系統穩定性趨勢 */}
      <div className="chart-container extra-large">
        <h3>系統穩定性週趨勢</h3>
        <Line data={stabilityTrendData} options={{
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            title: { ...chartOptions.plugins.title, text: '7天系統可用性與錯誤率變化' }
          },
          scales: {
            ...chartOptions.scales,
            y: {
              ...chartOptions.scales.y,
              title: {
                display: true,
                text: '百分比 (%)',
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
              },
              min: 0,
              max: 100,
            },
          },
        }} />

        {/* 系統關鍵指標 */}
        <div style={{ marginTop: '20px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '10px', padding: '20px' }}>
          <h4 style={{ color: 'white', textAlign: 'center', marginBottom: '15px' }}>🎯 系統關鍵指標</h4>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '15px' 
          }}>
            {[
              { metric: '平均可用性', value: '99.6%', status: 'excellent' },
              { metric: '平均錯誤率', value: '0.4%', status: 'good' },
              { metric: '系統吞吐量', value: '2.8Gbps', status: 'excellent' },
              { metric: '響應時間', value: '18ms', status: 'excellent' },
              { metric: '並發用戶', value: '15K', status: 'good' },
              { metric: '資源利用率', value: '68%', status: 'good' },
            ].map((item, index) => (
              <div key={index} style={{
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '8px',
                padding: '12px',
                textAlign: 'center',
                border: '1px solid rgba(255, 255, 255, 0.2)'
              }}>
                <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}>
                  {item.metric}
                </div>
                <div style={{ 
                  color: item.status === 'excellent' ? '#22c55e' : '#3b82f6', 
                  fontSize: '18px', 
                  fontWeight: 'bold' 
                }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-insight">
          <strong>穩定性總結：</strong>系統7天平均可用性達到99.6%，錯誤率維持在0.4%以下。
          週末期間性能最佳，工作日負載較高但仍保持穩定。
          系統架構設計合理，具備良好的擴展性和容錯能力。
        </div>
      </div>
    </div>
  )
}

export default SystemTabContent