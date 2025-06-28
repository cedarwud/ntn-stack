/**
 * 圖表數據處理 Hook
 * 統一管理 ChartAnalysisDashboard 的數據邏輯
 */

import { useState, useMemo, useCallback } from 'react'
import { ChartData } from 'chart.js'

// 數據類型定義
export interface ChartDataPoint {
  x?: number | string
  y: number
  label?: string
}

export interface MetricsData {
  handoverLatency: number[]
  performanceMetrics: number[]
  accuracyData: number[]
  systemMetrics: {
    cpu: number
    memory: number
    network: number
    storage: number
  }
}

// Handover 延遲數據 Hook
export const useHandoverLatencyData = () => {
  const [isLoading, setIsLoading] = useState(true)
  const [error] = useState<string | null>(null)

  const chartData = useMemo((): ChartData<'bar'> => ({
    labels: [
      '候選星座計算', 
      '位置預測', 
      '信號品質評估', 
      '決策執行', 
      '確認握手'
    ],
    datasets: [{
      label: 'Fine-Grained Sync',
      data: [1.2, 0.8, 1.5, 0.6, 0.4],
      backgroundColor: 'rgba(76, 175, 80, 0.8)',
      borderColor: 'rgba(76, 175, 80, 1)',
      borderWidth: 1
    }, {
      label: 'Traditional Method',
      data: [3.5, 2.8, 4.2, 2.1, 1.8],
      backgroundColor: 'rgba(244, 67, 54, 0.8)',
      borderColor: 'rgba(244, 67, 54, 1)',
      borderWidth: 1
    }]
  }), [])

  return {
    chartData,
    isLoading,
    error,
    refresh: useCallback(() => {
      setIsLoading(true)
      // 模擬數據刷新
      setTimeout(() => {
        setIsLoading(false)
      }, 500)
    }, [])
  }
}

// 性能對比數據 Hook
export const usePerformanceComparisonData = () => {
  const chartData = useMemo((): ChartData<'bar'> => ({
    labels: [
      '延遲 (ms)', '吞吐量 (Mbps)', '成功率 (%)', 
      '能耗 (W)', 'CPU 使用率 (%)', '記憶體使用率 (%)'
    ],
    datasets: [{
      label: 'Starlink',
      data: [12.5, 85.2, 98.7, 45.3, 65.8, 72.1],
      backgroundColor: 'rgba(33, 150, 243, 0.8)',
      borderColor: 'rgba(33, 150, 243, 1)',
      borderWidth: 1
    }, {
      label: 'OneWeb',
      data: [15.8, 78.9, 96.2, 52.7, 71.3, 68.9],
      backgroundColor: 'rgba(255, 152, 0, 0.8)',
      borderColor: 'rgba(255, 152, 0, 1)',
      borderWidth: 1
    }]
  }), [])

  return { chartData }
}

// QoE 延遲監控數據 Hook
export const useQoELatencyData = () => {
  const chartData = useMemo((): ChartData<'line'> => {
    const timeLabels = Array.from({ length: 50 }, (_, i) => `${i * 2}s`)
    
    // 生成穩定的模擬數據（不使用 Math.random()）
    const stallingTimeData = Array.from({ length: 50 }, (_, i) => 50 + (i % 10) * 5 + Math.sin(i * 0.1) * 20)
    const rttData = Array.from({ length: 50 }, (_, i) => 20 + (i % 8) * 3 + Math.cos(i * 0.15) * 10)
    
    return {
      labels: timeLabels,
      datasets: [{
        label: 'Stalling Time (ms)',
        data: stallingTimeData,
        borderColor: 'rgba(76, 175, 80, 1)',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        tension: 0.4,
        fill: true,
        yAxisID: 'y'
      }, {
        label: 'RTT (ms)',
        data: rttData,
        borderColor: 'rgba(33, 150, 243, 1)',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        tension: 0.4,
        fill: true,
        yAxisID: 'y1'
      }]
    }
  }, [])

  return { chartData }
}

// UE 接入策略雷達數據 Hook
export const useAccessStrategyRadarData = () => {
  const chartData = useMemo((): ChartData<'radar'> => ({
    labels: [
      '延遲優化', '吞吐量', '能效比', 
      '可靠性', '覆蓋範圍', '負載均衡'
    ],
    datasets: [{
      label: 'Fine-Grained Sync',
      data: [9.2, 8.7, 9.5, 9.1, 8.9, 9.3],
      borderColor: 'rgba(76, 175, 80, 1)',
      backgroundColor: 'rgba(76, 175, 80, 0.2)',
      pointBackgroundColor: 'rgba(76, 175, 80, 1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(76, 175, 80, 1)'
    }, {
      label: 'Traditional Method',
      data: [6.8, 7.2, 6.5, 7.0, 7.5, 6.9],
      borderColor: 'rgba(244, 67, 54, 1)',
      backgroundColor: 'rgba(244, 67, 54, 0.2)',
      pointBackgroundColor: 'rgba(244, 67, 54, 1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(244, 67, 54, 1)'
    }]
  }), [])

  return { chartData }
}

// 系統架構資源分配數據 Hook
export const useSystemArchitectureData = () => {
  const chartData = useMemo((): ChartData<'doughnut'> => ({
    labels: [
      '衛星追蹤模組', '預測演算法', '決策引擎', 
      '通訊協定', '監控系統', '其他'
    ],
    datasets: [{
      data: [25.5, 22.3, 18.9, 15.2, 12.1, 6.0],
      backgroundColor: [
        'rgba(76, 175, 80, 0.8)',
        'rgba(33, 150, 243, 0.8)',
        'rgba(255, 152, 0, 0.8)',
        'rgba(156, 39, 176, 0.8)',
        'rgba(244, 67, 54, 0.8)',
        'rgba(96, 125, 139, 0.8)'
      ],
      borderColor: [
        'rgba(76, 175, 80, 1)',
        'rgba(33, 150, 243, 1)',
        'rgba(255, 152, 0, 1)',
        'rgba(156, 39, 176, 1)',
        'rgba(244, 67, 54, 1)',
        'rgba(96, 125, 139, 1)'
      ],
      borderWidth: 2
    }]
  }), [])

  return { chartData }
}

// 六場景換手延遲數據 Hook
export const useSixScenarioLatencyData = () => {
  const chartData = useMemo((): ChartData<'bar'> => ({
    labels: [
      '城市密集', '郊區住宅', '高速公路', 
      '山區覆蓋', '海上通訊', '極地環境'
    ],
    datasets: [{
      label: 'Fine-Grained Sync (ms)',
      data: [8.2, 9.1, 7.8, 12.5, 15.2, 18.7],
      backgroundColor: 'rgba(76, 175, 80, 0.8)',
      borderColor: 'rgba(76, 175, 80, 1)',
      borderWidth: 1
    }, {
      label: 'Binary Search (ms)',
      data: [12.8, 14.2, 11.9, 18.3, 22.1, 25.8],
      backgroundColor: 'rgba(33, 150, 243, 0.8)',
      borderColor: 'rgba(33, 150, 243, 1)',
      borderWidth: 1
    }, {
      label: 'Traditional (ms)',
      data: [25.3, 28.7, 23.1, 35.2, 42.8, 48.9],
      backgroundColor: 'rgba(244, 67, 54, 0.8)',
      borderColor: 'rgba(244, 67, 54, 1)',
      borderWidth: 1
    }]
  }), [])

  return { chartData }
}

// 計算複雜度數據 Hook
export const useComputationalComplexityData = () => {
  const chartData = useMemo((): ChartData<'bar'> => ({
    labels: [
      '10 衛星', '50 衛星', '100 衛星', 
      '200 衛星', '500 衛星', '1000 衛星'
    ],
    datasets: [{
      label: 'Fine-Grained Sync (ms)',
      data: [2.1, 8.7, 15.2, 28.9, 65.3, 125.7],
      backgroundColor: 'rgba(76, 175, 80, 0.8)',
      borderColor: 'rgba(76, 175, 80, 1)',
      borderWidth: 1
    }, {
      label: 'Traditional O(n²) (ms)',
      data: [5.8, 142.3, 580.9, 2341.7, 14625.8, 58503.2],
      backgroundColor: 'rgba(244, 67, 54, 0.8)',
      borderColor: 'rgba(244, 67, 54, 1)',
      borderWidth: 1
    }]
  }), [])

  return { chartData }
}

// 時間同步精度數據 Hook
export const useTimeSyncAccuracyData = () => {
  const chartData = useMemo((): ChartData<'bar'> => ({
    labels: [
      'GPS同步', 'NTP協議', '本地時鐘', 
      'Fine-Grained', '混合同步', '量子同步'
    ],
    datasets: [{
      label: '同步精度 (μs)',
      data: [12.5, 850.2, 15000.7, 2.3, 8.9, 0.8],
      backgroundColor: [
        'rgba(76, 175, 80, 0.8)',
        'rgba(255, 152, 0, 0.8)',
        'rgba(244, 67, 54, 0.8)',
        'rgba(33, 150, 243, 0.8)',
        'rgba(156, 39, 176, 0.8)',
        'rgba(0, 188, 212, 0.8)'
      ],
      borderColor: [
        'rgba(76, 175, 80, 1)',
        'rgba(255, 152, 0, 1)',
        'rgba(244, 67, 54, 1)',
        'rgba(33, 150, 243, 1)',
        'rgba(156, 39, 176, 1)',
        'rgba(0, 188, 212, 1)'
      ],
      borderWidth: 1
    }]
  }), [])

  return { chartData }
}

// 統一數據管理 Hook
export const useChartDataManager = () => {
  const handoverLatency = useHandoverLatencyData()
  const performanceComparison = usePerformanceComparisonData()
  const qoeLatency = useQoELatencyData()
  const accessStrategyRadar = useAccessStrategyRadarData()
  const systemArchitecture = useSystemArchitectureData()
  const sixScenarioLatency = useSixScenarioLatencyData()
  const computationalComplexity = useComputationalComplexityData()
  const timeSyncAccuracy = useTimeSyncAccuracyData()

  return {
    handoverLatency,
    performanceComparison,
    qoeLatency,
    accessStrategyRadar,
    systemArchitecture,
    sixScenarioLatency,
    computationalComplexity,
    timeSyncAccuracy
  }
}