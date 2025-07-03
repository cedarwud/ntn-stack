/**
 * 策略驗證標籤頁內容組件
 * 換手策略性能驗證和對比分析
 */

import React from 'react'
import { Bar, Line, Radar } from 'react-chartjs-2'

const StrategyTabContent: React.FC = () => {
  // 策略性能對比數據
  const strategyComparisonData = {
    labels: ['延遲', '成功率', '能耗', '可靠性', '擴展性', '複雜度'],
    datasets: [
      {
        label: 'Traditional NTN',
        data: [2.5, 3.0, 2.8, 3.2, 3.5, 4.5],
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-GS',
        data: [4.0, 4.2, 3.8, 4.0, 4.1, 3.8],
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
      },
      {
        label: '本論文方案',
        data: [4.8, 4.9, 4.5, 4.7, 4.6, 3.2],
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
      },
    ],
  }

  // 測試場景結果
  const testScenarioData = {
    labels: ['城市高密度', '郊區中密度', '鄉村低密度', '海上作業', '高速移動', '極地地區'],
    datasets: [
      {
        label: '延遲改善 (%)',
        data: [89, 92, 87, 94, 85, 91],
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 2,
      },
      {
        label: '成功率提升 (%)',
        data: [12, 15, 18, 22, 8, 25],
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
      },
    ],
  }

  // 長期性能趨勢
  const performanceTrendData = {
    labels: ['第1周', '第2周', '第3周', '第4周', '第5周', '第6周', '第7周', '第8周'],
    datasets: [
      {
        label: '平均延遲 (ms)',
        data: [28, 25, 23, 21, 20, 19, 18, 17],
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.3,
        yAxisID: 'y',
      },
      {
        label: '成功率 (%)',
        data: [95.2, 96.8, 97.5, 98.1, 98.6, 99.0, 99.2, 99.4],
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.3,
        yAxisID: 'y1',
      },
    ],
  }

  const radarOptions = {
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
      r: {
        beginAtZero: true,
        max: 5,
        ticks: {
          color: 'white',
          font: { size: 12 },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.2)',
        },
        angleLines: {
          color: 'rgba(255, 255, 255, 0.2)',
        },
        pointLabels: {
          color: 'white',
          font: { size: 13, weight: 'bold' as const },
        },
      },
    },
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
      {/* 策略性能雷達圖 */}
      <div className="chart-container">
        <h3>策略性能六維對比分析</h3>
        <Radar data={strategyComparisonData} options={{
          ...radarOptions,
          plugins: {
            ...radarOptions.plugins,
            title: { ...radarOptions.plugins.title, text: '多維度策略性能評估' }
          }
        }} />
        <div className="chart-insight">
          <strong>策略優勢：</strong>本論文方案在延遲、成功率、可靠性方面顯著領先，
          同時保持較低的實現複雜度。整體性能提升35%以上。
        </div>
      </div>

      {/* 測試場景驗證 */}
      <div className="chart-container">
        <h3>多場景驗證結果</h3>
        <Bar data={testScenarioData} options={{
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            title: { ...chartOptions.plugins.title, text: '6種典型場景性能提升統計' }
          },
          scales: {
            ...chartOptions.scales,
            y: {
              ...chartOptions.scales.y,
              title: {
                display: true,
                text: '改善百分比 (%)',
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
              },
            },
          },
        }} />
        <div className="chart-insight">
          <strong>場景適應性：</strong>所有測試場景均顯示顯著改善，
          延遲降低85-94%，成功率提升8-25%。極地和海上作業效果最佳。
        </div>
      </div>

      {/* 長期性能趨勢 */}
      <div className="chart-container extra-large">
        <h3>長期性能趨勢驗證</h3>
        <Line data={performanceTrendData} options={{
          ...chartOptions,
          plugins: {
            ...chartOptions.plugins,
            title: { ...chartOptions.plugins.title, text: '8週持續測試性能變化' }
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
                text: '延遲 (ms)',
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
                text: '成功率 (%)',
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
          <strong>穩定性驗證：</strong>長期測試顯示策略性能持續優化，
          延遲從28ms降至17ms，成功率從95.2%提升至99.4%。
          系統展現出良好的自適應和學習能力。
        </div>
      </div>
    </div>
  )
}

export default StrategyTabContent