/**
 * 圖表數據管理 Hook
 * 專為 ChartAnalysisDashboard 組件提供數據
 */

import { useMemo } from 'react'
import { ChartData } from 'chart.js'

// UE 接入策略雷達圖數據
export const useChartDataManager = () => {
  const accessStrategyRadar = useMemo(() => ({
    chartData: {
      labels: ['延遲性能', '能耗效率', '精度穩定', '計算複雜度', '可靠性', '擴展性'],
      datasets: [
        {
          label: 'Fine-Grained Sync',
          data: [9.2, 8.8, 9.5, 7.5, 9.7, 8.9],
          backgroundColor: 'rgba(34, 197, 94, 0.2)',
          borderColor: 'rgba(34, 197, 94, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(34, 197, 94, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(34, 197, 94, 1)',
        },
        {
          label: 'Binary Search',
          data: [7.8, 7.2, 8.1, 8.0, 8.4, 7.6],
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(59, 130, 246, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(59, 130, 246, 1)',
        },
        {
          label: 'Traditional',
          data: [6.1, 5.8, 6.5, 5.2, 6.9, 6.0],
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(239, 68, 68, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(239, 68, 68, 1)',
        },
      ],
    } as ChartData<'radar'>
  }), [])

  // 時間同步精度數據
  const timeSyncAccuracy = useMemo(() => ({
    chartData: {
      labels: ['Fine-Grained Sync', 'GPS-based', 'NTP Standard', 'Binary Search', 'Traditional'],
      datasets: [
        {
          label: '同步精度 (μs)',
          data: [0.3, 2.1, 12.5, 8.7, 45.2],
          backgroundColor: [
            'rgba(34, 197, 94, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(251, 191, 36, 0.8)',
            'rgba(168, 85, 247, 0.8)',
            'rgba(239, 68, 68, 0.8)',
          ],
          borderColor: [
            'rgba(34, 197, 94, 1)',
            'rgba(59, 130, 246, 1)',
            'rgba(251, 191, 36, 1)',
            'rgba(168, 85, 247, 1)',
            'rgba(239, 68, 68, 1)',
          ],
          borderWidth: 2,
        },
      ],
    } as ChartData<'bar'>
  }), [])

  // QoE 延遲監控數據
  const qoeLatency = useMemo(() => ({
    chartData: {
      labels: ['0s', '30s', '60s', '90s', '120s', '150s', '180s', '210s', '240s', '270s', '300s'],
      datasets: [
        {
          label: 'Stalling Time (ms)',
          data: [15, 12, 8, 6, 4, 3, 5, 7, 6, 4, 3],
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.4,
          fill: true,
          yAxisID: 'y',
        },
        {
          label: 'RTT (ms)',
          data: [25, 22, 18, 15, 12, 10, 13, 16, 14, 11, 9],
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          tension: 0.4,
          fill: true,
          yAxisID: 'y1',
        },
      ],
    } as ChartData<'line'>
  }), [])

  return {
    accessStrategyRadar,
    timeSyncAccuracy,
    qoeLatency,
  }
}