/**
 * BaseChart 組件
 * 統一的圖表基礎組件，抽取各事件 Chart 的共同邏輯
 * 使用原生 Chart.js，避免 react-chartjs-2 的複雜性
 */

import React, { useEffect, useRef, useCallback, useMemo } from 'react'
import { Chart, ChartConfiguration, ChartType } from 'chart.js/auto'
import type { BaseChartProps, DataPoint, ChartAnnotation, MeasurementEventParams } from '../types'

// 圖表主題配置
const getThemeColors = (isDarkTheme: boolean) => ({
  background: isDarkTheme ? '#2d3748' : '#ffffff',
  text: isDarkTheme ? '#e2e8f0' : '#2d3748',
  grid: isDarkTheme ? '#4a5568' : '#e2e8f0',
  border: isDarkTheme ? '#718096' : '#cbd5e0',
  primary: '#3b82f6',
  secondary: '#10b981',
  accent: '#f59e0b',
  danger: '#ef4444'
})

interface BaseChartConfig {
  title: string
  xAxisLabel: string
  yAxisLabel: string
  xAxisUnit: string
  yAxisUnit: string
  yAxisRange: { min: number; max: number }
  datasets: {
    label: string
    data: DataPoint[]
    color: string
    type?: 'line' | 'scatter'
    fill?: boolean
    borderWidth?: number
    pointRadius?: number
  }[]
  annotations?: ChartAnnotation[]
}

interface BaseChartInternalProps<T extends MeasurementEventParams> extends BaseChartProps<T> {
  config: BaseChartConfig
  onDataPointClick?: (point: DataPoint, datasetIndex: number) => void
}

const BaseChart = <T extends MeasurementEventParams>({
  _eventType,
  _params,
  animationState,
  isDarkTheme,
  showThresholdLines,
  config,
  onDataPointClick,
  className = ''
}: BaseChartInternalProps<T>) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart | null>(null)
  const themeColors = useMemo(() => getThemeColors(isDarkTheme), [isDarkTheme])

  // 生成動畫游標數據
  const generateAnimationCursor = useCallback((currentTime: number) => {
    if (!showThresholdLines) return []
    
    return [
      { x: currentTime, y: config.yAxisRange.min },
      { x: currentTime, y: config.yAxisRange.max }
    ]
  }, [showThresholdLines, config.yAxisRange])

  // 生成門檻線數據
  const generateThresholdLines = useCallback(() => {
    if (!showThresholdLines || !config.annotations) return []
    
    return config.annotations.filter(annotation => 
      annotation.type === 'line' && annotation.value !== undefined
    ).map(annotation => ({
      label: annotation.label,
      data: [
        { x: 0, y: annotation.value! },
        { x: config.yAxisRange.max, y: annotation.value! }
      ],
      borderColor: annotation.color,
      backgroundColor: 'transparent',
      borderDash: annotation.borderDash || [5, 5],
      borderWidth: 2,
      pointRadius: 0,
      fill: false
    }))
  }, [showThresholdLines, config.annotations, config.yAxisRange.max])

  // 創建圖表配置
  const createChartConfig = useCallback((): ChartConfiguration => {
    const datasets = [
      // 主要數據集
      ...config.datasets.map(dataset => ({
        label: dataset.label,
        data: dataset.data,
        borderColor: dataset.color,
        backgroundColor: dataset.fill ? `${dataset.color}20` : 'transparent',
        borderWidth: dataset.borderWidth || 2,
        fill: dataset.fill || false,
        pointRadius: dataset.pointRadius || 3,
        pointHoverRadius: dataset.pointRadius ? dataset.pointRadius + 2 : 5,
        tension: 0.3,
        type: dataset.type || 'line' as ChartType
      })),
      
      // 門檻線
      ...generateThresholdLines(),
      
      // 動畫游標
      ...(animationState.currentTime > 0 ? [{
        label: '當前時間',
        data: generateAnimationCursor(animationState.currentTime),
        borderColor: themeColors.accent,
        backgroundColor: 'transparent',
        borderWidth: 3,
        pointRadius: 0,
        fill: false,
        tension: 0
      }] : [])
    ]

    return {
      type: 'line',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 300
        },
        interaction: {
          intersect: false,
          mode: 'index'
        },
        plugins: {
          title: {
            display: true,
            text: config.title,
            color: themeColors.text,
            font: {
              size: 16,
              weight: 'bold'
            },
            padding: 20
          },
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: themeColors.text,
              font: {
                size: 12
              },
              filter: (item) => !item.text?.includes('當前時間') // 隱藏游標圖例
            }
          },
          tooltip: {
            backgroundColor: isDarkTheme ? '#1a202c' : '#ffffff',
            titleColor: themeColors.text,
            bodyColor: themeColors.text,
            borderColor: themeColors.border,
            borderWidth: 1,
            cornerRadius: 8,
            displayColors: true,
            callbacks: {
              title: (context) => {
                const point = context[0]
                return `時間: ${point.parsed.x.toFixed(1)}${config.xAxisUnit}`
              },
              label: (context) => {
                const value = context.parsed.y.toFixed(2)
                return `${context.dataset.label}: ${value}${config.yAxisUnit}`
              }
            }
          }
        },
        scales: {
          x: {
            type: 'linear',
            position: 'bottom',
            title: {
              display: true,
              text: `${config.xAxisLabel} (${config.xAxisUnit})`,
              color: themeColors.text,
              font: {
                size: 14,
                weight: 'bold'
              }
            },
            ticks: {
              color: themeColors.text,
              font: {
                size: 12
              }
            },
            grid: {
              color: themeColors.grid,
              lineWidth: 1
            },
            border: {
              color: themeColors.border
            }
          },
          y: {
            type: 'linear',
            min: config.yAxisRange.min,
            max: config.yAxisRange.max,
            title: {
              display: true,
              text: `${config.yAxisLabel} (${config.yAxisUnit})`,
              color: themeColors.text,
              font: {
                size: 14,
                weight: 'bold'
              }
            },
            ticks: {
              color: themeColors.text,
              font: {
                size: 12
              }
            },
            grid: {
              color: themeColors.grid,
              lineWidth: 1
            },
            border: {
              color: themeColors.border
            }
          }
        },
        onClick: (event, elements) => {
          if (elements.length > 0 && onDataPointClick) {
            const element = elements[0]
            const datasetIndex = element.datasetIndex
            const dataIndex = element.index
            const dataset = config.datasets[datasetIndex]
            if (dataset && dataset.data[dataIndex]) {
              onDataPointClick(dataset.data[dataIndex], datasetIndex)
            }
          }
        }
      }
    }
  }, [
    config,
    animationState.currentTime,
    isDarkTheme,
    showThresholdLines,
    themeColors,
    generateAnimationCursor,
    generateThresholdLines,
    onDataPointClick
  ])

  // 初始化和更新圖表
  useEffect(() => {
    if (!canvasRef.current) return

    // 銷毀現有圖表
    if (chartRef.current) {
      chartRef.current.destroy()
    }

    // 創建新圖表
    const ctx = canvasRef.current.getContext('2d')
    if (ctx) {
      chartRef.current = new Chart(ctx, createChartConfig())
    }

    // 清理函數
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy()
        chartRef.current = null
      }
    }
  }, [createChartConfig])

  // 組件卸載時清理圖表
  useEffect(() => {
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy()
      }
    }
  }, [])

  return (
    <div className={`base-chart ${isDarkTheme ? 'dark-theme' : 'light-theme'} ${className}`}>
      <canvas
        ref={canvasRef}
        style={{
          backgroundColor: themeColors.background,
          borderRadius: '8px'
        }}
      />
    </div>
  )
}

export default BaseChart