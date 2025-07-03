/**
 * 圖表分析儀表板圖表配置選項
 * 抽取自 FullChartAnalysisDashboard.tsx 的圖表配置
 */

/**
 * 創建交互式圖表選項
 */
export const createInteractiveChartOptions = (title: string, yLabel: string, xLabel?: string) => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: 'white',
        font: {
          size: 14,
          weight: 'bold' as const,
        },
      },
    },
    title: {
      display: true,
      text: title,
      color: 'white',
      font: {
        size: 18,
        weight: 'bold' as const,
      },
    },
  },
  scales: {
    x: {
      title: {
        display: !!xLabel,
        text: xLabel || '',
        color: 'white',
        font: {
          size: 14,
          weight: 'bold' as const,
        },
      },
      ticks: {
        color: 'white',
        font: {
          size: 12,
          weight: 'bold' as const,
        },
      },
    },
    y: {
      title: {
        display: true,
        text: yLabel,
        color: 'white',
        font: {
          size: 14,
          weight: 'bold' as const,
        },
      },
      ticks: {
        color: 'white',
        font: {
          size: 12,
          weight: 'bold' as const,
        },
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.2)',
      },
    },
  },
})

/**
 * RL監控專用圖表配置
 */
export const createRLChartOptions = (title: string, yLabel: string = '獎勵值') => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        color: 'white',
        font: {
          size: 12,
          weight: 'bold' as const,
        },
      },
    },
    title: {
      display: true,
      text: title,
      color: 'white',
      font: {
        size: 16,
        weight: 'bold' as const,
      },
    },
  },
  scales: {
    x: {
      title: {
        display: true,
        text: '時間步',
        color: 'white',
        font: {
          size: 12,
          weight: 'bold' as const,
        },
      },
      ticks: {
        color: 'white',
        font: {
          size: 10,
        },
      },
    },
    y: {
      title: {
        display: true,
        text: yLabel,
        color: 'white',
        font: {
          size: 12,
          weight: 'bold' as const,
        },
      },
      ticks: {
        color: 'white',
        font: {
          size: 10,
        },
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)',
      },
    },
  },
})

/**
 * 預設的圖表主題顏色
 */
export const chartColors = {
  primary: 'rgba(75, 192, 192, 0.7)',
  primaryBorder: 'rgba(75, 192, 192, 1)',
  secondary: 'rgba(54, 162, 235, 0.7)',
  secondaryBorder: 'rgba(54, 162, 235, 1)',
  success: 'rgba(75, 192, 192, 0.7)',
  successBorder: 'rgba(75, 192, 192, 1)',
  warning: 'rgba(255, 206, 86, 0.7)',
  warningBorder: 'rgba(255, 206, 86, 1)',
  danger: 'rgba(255, 99, 132, 0.7)',
  dangerBorder: 'rgba(255, 99, 132, 1)',
  info: 'rgba(153, 102, 255, 0.7)',
  infoBorder: 'rgba(153, 102, 255, 1)',
}

/**
 * 通用圖表樣式配置 - 完全對照 chart.html
 */
export const commonChartConfig = {
  borderWidth: 2,
  pointRadius: 0,
  pointHoverRadius: 6,
  tension: 0.3, // 完全對照 chart.html
  fill: false,
}