/**
 * 衛星分析標籤頁內容組件
 * 衛星運行狀態和軌道分析
 */

import React from 'react'
import { Line, Scatter, Bar } from 'react-chartjs-2'

const MonitoringTabContent: React.FC = () => {
  // 衛星位置追蹤數據
  const satelliteTrackingData = {
    labels: ['0min', '15min', '30min', '45min', '60min', '75min', '90min'],
    datasets: [
      {
        label: 'Starlink-1547',
        data: [550, 552, 548, 551, 549, 553, 550],
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.3,
      },
      {
        label: 'Kuiper-892',
        data: [630, 628, 632, 629, 631, 627, 630],
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.3,
      },
    ],
  }

  // 覆蓋區域分析
  const coverageData = {
    datasets: [{
      label: '衛星覆蓋區域',
      data: [
        { x: -180, y: 85 }, { x: -120, y: 75 }, { x: -60, y: 80 },
        { x: 0, y: 82 }, { x: 60, y: 78 }, { x: 120, y: 76 }, { x: 180, y: 85 }
      ],
      backgroundColor: 'rgba(75, 192, 192, 0.6)',
      borderColor: 'rgba(75, 192, 192, 1)',
      pointRadius: 8,
    }]
  }

  // 星座健康狀況
  const healthStatusData = {
    labels: ['Starlink', 'Kuiper', 'OneWeb', 'Telesat'],
    datasets: [
      {
        label: '正常運行',
        data: [4200, 1800, 650, 298],
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
      },
      {
        label: '維護中',
        data: [50, 20, 15, 8],
        backgroundColor: 'rgba(251, 191, 36, 0.8)',
      },
      {
        label: '故障',
        data: [25, 8, 5, 2],
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
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

  return (
    <div className="charts-grid">
      {/* 衛星軌道追蹤 */}
      <div className="chart-container">
        <h3>衛星軌道高度實時追蹤</h3>
        <Line data={satelliteTrackingData} options={{
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            title: { ...chartOptions.plugins.title, text: '90分鐘軌道周期衛星高度變化' }
          },
          scales: {
            ...chartOptions.scales,
            y: {
              ...chartOptions.scales.y,
              title: {
                display: true,
                text: '高度 (km)',
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
              },
            },
          },
        }} />
        <div className="chart-insight">
          <strong>軌道特性：</strong>Starlink 運行在550km LEO軌道，
          Kuiper 在630km軌道。軌道高度穩定，變化幅度在±3km範圍內。
        </div>
      </div>

      {/* 全球覆蓋分析 */}
      <div className="chart-container">
        <h3>全球覆蓋區域分析</h3>
        <Scatter data={coverageData} options={{
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            title: { ...chartOptions.plugins.title, text: '衛星覆蓋強度熱點分佈' }
          },
          scales: {
            x: {
              ...chartOptions.scales.x,
              title: {
                display: true,
                text: '經度 (°)',
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
              },
              min: -180,
              max: 180,
            },
            y: {
              ...chartOptions.scales.y,
              title: {
                display: true,
                text: '緯度 (°)',
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
              },
              min: -90,
              max: 90,
            },
          },
        }} />
        <div className="chart-insight">
          <strong>覆蓋模式：</strong>極地地區覆蓋密度最高，
          赤道附近覆蓋相對較少。總體覆蓋率達到94.2%。
        </div>
      </div>

      {/* 星座健康監控 */}
      <div className="chart-container extra-large">
        <h3>星座健康狀況監控</h3>
        <Bar data={healthStatusData} options={{
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            title: { ...chartOptions.plugins.title, text: '各星座衛星運行狀態統計' }
          },
          scales: {
            ...chartOptions.scales,
            y: {
              ...chartOptions.scales.y,
              title: {
                display: true,
                text: '衛星數量',
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
              },
            },
          },
        }} />
        <div className="chart-insight">
          <strong>健康狀況：</strong>各星座整體運行良好，正常率均超過98%。
          Starlink 擁有最大的衛星數量，故障率控制在0.6%以下。
          定期維護確保系統穩定性。
        </div>
      </div>
    </div>
  )
}

export default MonitoringTabContent