/**
 * UE分析標籤頁內容組件
 * 用戶設備分析和統計
 */

import React from 'react'
import { Line, Doughnut } from 'react-chartjs-2'

const AnalysisTabContent: React.FC = () => {
  // UE 連接統計數據
  const ueConnectionData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
    datasets: [
      {
        label: '活躍 UE 數量',
        data: [1200, 800, 1500, 2200, 2800, 2400, 1800],
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.4,
        fill: true,
      },
      {
        label: '新接入 UE',
        data: [200, 100, 400, 600, 500, 300, 250],
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.4,
        fill: true,
      },
    ],
  }

  // UE 分佈數據
  const ueDistributionData = {
    labels: ['Starlink', 'Kuiper', 'OneWeb', 'Telesat', '其他'],
    datasets: [
      {
        data: [45, 25, 15, 10, 5],
        backgroundColor: [
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 99, 132, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
        ],
        borderWidth: 2,
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

  const doughnutOptions = {
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
      {/* UE 連接趨勢 */}
      <div className="chart-container">
        <h3>UE 連接趨勢分析</h3>
        <Line data={ueConnectionData} options={{
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            title: { ...chartOptions.plugins.title, text: '24小時 UE 連接活動統計' }
          }
        }} />
        <div className="chart-insight">
          <strong>連接模式：</strong>高峰期集中在12:00-20:00，活躍UE數量達到2800個。
          新接入UE在工作時間顯著增加，顯示商務需求驅動的連接模式。
        </div>
      </div>

      {/* UE 星座分佈 */}
      <div className="chart-container">
        <h3>UE 星座分佈統計</h3>
        <Doughnut data={ueDistributionData} options={{
          ...doughnutOptions,
          plugins: {
            ...doughnutOptions.plugins,
            title: { ...doughnutOptions.plugins.title, text: 'UE 在不同衛星星座的分佈比例' }
          }
        }} />
        <div className="chart-insight">
          <strong>分佈特徵：</strong>Starlink 佔主導地位（45%），
          Kuiper 次之（25%）。多星座接入策略提供更好的服務可靠性和覆蓋範圍。
        </div>
      </div>

      {/* UE 性能指標 */}
      <div className="chart-container extra-large">
        <h3>UE 性能關鍵指標監控</h3>
        <div className="metrics-grid" style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '20px',
          padding: '20px' 
        }}>
          {[
            { label: '平均延遲', value: '23.5ms', status: 'good' },
            { label: '成功率', value: '99.2%', status: 'excellent' },
            { label: '吞吐量', value: '1.2Gbps', status: 'good' },
            { label: '掉線率', value: '0.3%', status: 'excellent' },
            { label: '重連時間', value: '1.8s', status: 'good' },
            { label: '信號品質', value: '94.5%', status: 'excellent' },
          ].map((metric, index) => (
            <div key={index} className="metric-card" style={{
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '10px',
              padding: '15px',
              textAlign: 'center',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
              <div style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>
                {metric.label}
              </div>
              <div style={{ 
                color: metric.status === 'excellent' ? '#22c55e' : '#3b82f6', 
                fontSize: '24px', 
                fontWeight: 'bold' 
              }}>
                {metric.value}
              </div>
            </div>
          ))}
        </div>
        <div className="chart-insight">
          <strong>性能總結：</strong>整體UE性能表現優異，平均延遲控制在25ms以下，
          成功率維持在99%以上。信號品質和服務穩定性達到商用標準。
        </div>
      </div>
    </div>
  )
}

export default AnalysisTabContent