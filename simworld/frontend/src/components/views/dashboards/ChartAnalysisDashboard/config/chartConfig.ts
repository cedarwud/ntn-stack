/**
 * Chart.js 全域配置
 * 將 Chart.js 配置從主組件中分離出來
 */

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler,
  RadialLinearScale,
} from 'chart.js'

/**
 * 註冊所有需要的 Chart.js 組件
 */
export function registerChartComponents(): void {
  ChartJS.register(
    CategoryScale,
    LinearScale,
    LogarithmicScale,
    BarElement,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    Filler,
    RadialLinearScale
  )
}

/**
 * 設置 Chart.js 全域默認配置
 */
export function setupGlobalChartDefaults(): void {
  // 基本配置
  ChartJS.defaults.color = 'white'
  ChartJS.defaults.font.size = 16
  ChartJS.defaults.locale = 'en-US'

  // 圖例配置
  ChartJS.defaults.plugins.legend.labels.color = 'white'
  ChartJS.defaults.plugins.legend.labels.font = { size: 16 }

  // 標題配置
  ChartJS.defaults.plugins.title.color = 'white'
  ChartJS.defaults.plugins.title.font = { size: 20, weight: 'bold' as const }

  // 提示框配置
  ChartJS.defaults.plugins.tooltip.titleColor = 'white'
  ChartJS.defaults.plugins.tooltip.bodyColor = 'white'
  ChartJS.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.9)'
  ChartJS.defaults.plugins.tooltip.titleFont = { size: 16 }
  ChartJS.defaults.plugins.tooltip.bodyFont = { size: 15 }

  // 刻度配置
  ChartJS.defaults.scale.ticks.color = 'white'
  ChartJS.defaults.scale.ticks.font = { size: 14 }
  ChartJS.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.2)'

  // 元素默認配置
  if (ChartJS.defaults.elements) {
    if (ChartJS.defaults.elements.arc) {
      ChartJS.defaults.elements.arc.backgroundColor = 'rgba(255, 255, 255, 0.1)'
    }
    if (ChartJS.defaults.elements.bar) {
      ChartJS.defaults.elements.bar.backgroundColor = 'rgba(255, 255, 255, 0.1)'
    }
    if (ChartJS.defaults.elements.line) {
      ChartJS.defaults.elements.line.backgroundColor = 'rgba(255, 255, 255, 0.1)'
    }
  }

  // 刻度標題配置（類型安全）
  try {
    if (ChartJS.defaults.scale && 'title' in ChartJS.defaults.scale) {
      ;(ChartJS.defaults.scale as Record<string, unknown>).title = {
        color: 'white',
        font: { size: 16, weight: 'bold' as const },
      }
    }
  } catch (e) {
    console.warn('Could not set scale title defaults:', e)
  }
}

/**
 * 常用圖表配置選項
 */
export const commonChartOptions = {
  /**
   * 柱狀圖基本配置
   */
  barChart: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },

  /**
   * 線圖基本配置
   */
  lineChart: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },

  /**
   * 圓餅圖基本配置
   */
  pieChart: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
      title: {
        display: true,
      },
    },
  },

  /**
   * 雷達圖基本配置
   */
  radarChart: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
      },
    },
    scales: {
      r: {
        beginAtZero: true,
      },
    },
  },
}

/**
 * 色彩主題配置
 */
export const chartColors = {
  primary: [
    'rgba(54, 162, 235, 0.8)',
    'rgba(255, 99, 132, 0.8)',
    'rgba(255, 205, 86, 0.8)',
    'rgba(75, 192, 192, 0.8)',
    'rgba(153, 102, 255, 0.8)',
    'rgba(255, 159, 64, 0.8)',
  ],
  background: [
    'rgba(54, 162, 235, 0.2)',
    'rgba(255, 99, 132, 0.2)',
    'rgba(255, 205, 86, 0.2)',
    'rgba(75, 192, 192, 0.2)',
    'rgba(153, 102, 255, 0.2)',
    'rgba(255, 159, 64, 0.2)',
  ],
  border: [
    'rgba(54, 162, 235, 1)',
    'rgba(255, 99, 132, 1)',
    'rgba(255, 205, 86, 1)',
    'rgba(75, 192, 192, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)',
  ],
  success: 'rgba(40, 167, 69, 0.8)',
  warning: 'rgba(255, 193, 7, 0.8)',
  danger: 'rgba(220, 53, 69, 0.8)',
  info: 'rgba(23, 162, 184, 0.8)',
}

/**
 * 初始化圖表系統
 */
export function initializeChartSystem(): void {
  registerChartComponents()
  setupGlobalChartDefaults()
}