/**
 * Pure T1 Chart Component
 * 3GPP TS 38.331 Section 5.5.4.16 Event T1 Implementation
 * Time window condition event visualization
 * Time measured at UE within duration from threshold
 */

import React, { useEffect, useRef, useMemo } from 'react'
import { Chart } from 'chart.js/auto'
import annotationPlugin from 'chartjs-plugin-annotation'

// 註冊 annotation 插件
Chart.register(annotationPlugin)

// CondEvent T1 正確的狀態數據生成
// 基於 3GPP TS 38.331: Mt > Thresh1 (進入), Mt > Thresh1 + Duration (離開)
const generateT1StateData = (threshold: number, duration: number) => {
    const statePoints = []
    const totalTime = 25000 // 25 seconds for clear visualization
    const step = 100 // 100ms steps
    
    for (let mt = 0; mt <= totalTime; mt += step) {
        let state = 0 // Default: not triggered
        
        // CondEvent T1 邏輯：
        // 進入條件 T1-1: Mt > Thresh1
        // 離開條件 T1-2: Mt > Thresh1 + Duration
        if (mt > threshold && mt <= threshold + duration) {
            state = 1 // Event is active/triggered
        }
        
        statePoints.push({ x: mt / 1000, y: state }) // Convert to seconds
    }
    
    return statePoints
}

// 生成當前時間游標數據
const generateCurrentTimeCursor = (currentTime: number) => {
    return [
        { x: currentTime / 1000, y: 0 },
        { x: currentTime / 1000, y: 1 }
    ]
}

interface PureT1ChartProps {
    width?: number
    height?: number
    threshold?: number // t1-Threshold in milliseconds
    duration?: number // Duration parameter in milliseconds
    currentTime?: number // Current time Mt in milliseconds
    showThresholdLines?: boolean
    isDarkTheme?: boolean
    onThemeToggle?: () => void
}

export const PureT1Chart: React.FC<PureT1ChartProps> = React.memo(
    ({
        width: _width = 800,
        height: _height = 400,
        threshold = 5000, // 5 seconds default
        duration = 10000, // 10 seconds default
        currentTime = 2000, // 2 seconds default
        showThresholdLines = true,
        isDarkTheme = true,
        _onThemeToggle,
    }) => {
        const canvasRef = useRef<HTMLCanvasElement>(null)
        const chartRef = useRef<Chart | null>(null)
        const isInitialized = useRef(false)

        // T1 事件專用配色方案
        const colors = useMemo(
            () => ({
                dark: {
                    stateLine: '#28A745', // 綠色：T1 狀態曲線
                    currentTimeLine: '#FF6B6B', // 紅色：當前時間游標
                    thresholdLine: '#FFD93D', // 黃色：t1-Threshold
                    durationLine: '#6BCF7F', // 淺綠：Duration 標示
                    windowArea: 'rgba(40, 167, 69, 0.2)', // 半透明綠：激活窗口
                    title: 'white',
                    text: 'white',
                    grid: 'rgba(255, 255, 255, 0.1)',
                    background: 'transparent',
                },
                light: {
                    stateLine: '#198754', // 深綠
                    currentTimeLine: '#DC3545', // 深紅
                    thresholdLine: '#FF9800', // 橙色
                    durationLine: '#4CAF50', // 綠色
                    windowArea: 'rgba(25, 135, 84, 0.15)', // 半透明綠
                    title: 'black',
                    text: '#333333',
                    grid: 'rgba(0, 0, 0, 0.1)',
                    background: 'white',
                },
            }),
            []
        )

        const currentColors = isDarkTheme ? colors.dark : colors.light

        // CondEvent T1 數據生成
        const chartData = useMemo(() => {
            const stateData = generateT1StateData(threshold, duration)
            const cursorData = generateCurrentTimeCursor(currentTime)
            
            return {
                stateData,
                cursorData,
            }
        }, [threshold, duration, currentTime])

        // T1 狀態圖表配置 - 矩形脈衝設計
        const chartConfig = useMemo(() => ({
            type: 'line' as const,
            data: {
                datasets: [
                    {
                        label: 'T1 Event State (0=Inactive, 1=Active)',
                        data: chartData.stateData,
                        borderColor: currentColors.stateLine,
                        backgroundColor: currentColors.windowArea,
                        borderWidth: 4,
                        fill: 'origin',
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        tension: 0, // 直角矩形脈衝
                        stepped: 'before', // 階梯式曲線
                    },
                    {
                        label: `Current Time (Mt): ${currentTime}ms`,
                        data: chartData.cursorData,
                        borderColor: currentColors.currentTimeLine,
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        tension: 0,
                        borderDash: [5, 5],
                    },
                    {
                        label: `Event Status Node`,
                        data: chartData.statusNodeData,
                        borderColor: currentTime > threshold && currentTime <= threshold + duration ? '#28A745' : '#6C757D',
                        backgroundColor: currentTime > threshold && currentTime <= threshold + duration ? '#28A745' : '#6C757D',
                        borderWidth: 3,
                        fill: false,
                        pointRadius: currentTime > threshold && currentTime <= threshold + duration ? 12 : 8,
                        pointHoverRadius: 16,
                        pointStyle: 'rectRot',
                        showLine: false,
                        tension: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart' as const,
                },
                plugins: {
                    title: {
                        display: true,
                        text: '條件事件 T1 (CondEvent T1) - 時間窗口條件',
                        color: currentColors.title,
                        font: { size: 16, weight: 'bold' as const },
                        padding: 20,
                    },
                    legend: {
                        display: true,
                        position: 'top' as const,
                        labels: { 
                            color: currentColors.text,
                            usePointStyle: true,
                            padding: 15,
                        },
                    },
                    tooltip: {
                        mode: 'index' as const,
                        intersect: false,
                        callbacks: {
                            title: (context) => `時間 Mt: ${(context[0].parsed.x * 1000).toFixed(0)}ms`,
                            label: (context) => {
                                if (context.datasetIndex === 0) {
                                    const state = context.parsed.y
                                    const stateText = state === 1 ? '激活 (Active)' : '未激活 (Inactive)'
                                    return `T1 狀態: ${stateText}`
                                }
                                return context.dataset.label || ''
                            },
                            afterBody: () => {
                                const mt = currentTime
                                const isActive = mt > threshold && mt <= threshold + duration
                                return [
                                    `進入條件 T1-1: Mt > ${threshold}ms`,
                                    `離開條件 T1-2: Mt > ${threshold + duration}ms`,
                                    `當前狀態: ${isActive ? '事件激活中' : '事件未激活'}`
                                ]
                            }
                        }
                    },
                    annotation: {
                        annotations: showThresholdLines
                            ? {
                                  // Thresh1 垂直線
                                  thresholdLine: {
                                      type: 'line' as const,
                                      xMin: threshold / 1000,
                                      xMax: threshold / 1000,
                                      borderColor: currentColors.thresholdLine,
                                      borderWidth: 3,
                                      borderDash: [8, 4],
                                      label: {
                                          content: `進入 (Mt>${threshold}ms)`,
                                          enabled: true,
                                          position: 'start' as const,
                                          backgroundColor: currentColors.thresholdLine,
                                          color: isDarkTheme ? '#000' : '#fff',
                                          font: { size: 11, weight: 'bold' },
                                      },
                                  },
                                  // Thresh1 + Duration 垂直線
                                  endLine: {
                                      type: 'line' as const,
                                      xMin: (threshold + duration) / 1000,
                                      xMax: (threshold + duration) / 1000,
                                      borderColor: currentColors.durationLine,
                                      borderWidth: 3,
                                      borderDash: [8, 4],
                                      label: {
                                          content: `離開 (Mt>${threshold + duration}ms)`,
                                          enabled: true,
                                          position: 'end' as const,
                                          backgroundColor: currentColors.durationLine,
                                          color: isDarkTheme ? '#000' : '#fff',
                                          font: { size: 11, weight: 'bold' },
                                      },
                                  },
                                  // 激活時間窗口
                                  activeWindow: {
                                      type: 'box' as const,
                                      xMin: threshold / 1000,
                                      xMax: (threshold + duration) / 1000,
                                      yMin: 0,
                                      yMax: 1,
                                      backgroundColor: currentColors.windowArea,
                                      borderColor: currentColors.stateLine,
                                      borderWidth: 2,
                                      label: {
                                          content: `T1 激活窗口\n持續時間: ${duration}ms`,
                                          enabled: true,
                                          position: 'center' as const,
                                          backgroundColor: currentColors.stateLine,
                                          color: 'white',
                                          font: { size: 12, weight: 'bold' },
                                      },
                                  },
                              }
                            : {},
                    },
                },
                scales: {
                    x: {
                        type: 'linear' as const,
                        position: 'bottom' as const,
                        title: {
                            display: true,
                            text: '時間 Mt (秒)',
                            color: currentColors.text,
                            font: { size: 14, weight: 'bold' as const },
                        },
                        grid: {
                            color: currentColors.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentColors.text,
                            stepSize: 2,
                            callback: function (value: number | string) {
                                return `${value}s (${Number(value) * 1000}ms)`
                            },
                        },
                        min: 0,
                        max: 25,
                    },
                    y: {
                        type: 'linear' as const,
                        display: true,
                        position: 'left' as const,
                        title: {
                            display: true,
                            text: 'CondEvent T1 狀態',
                            color: currentColors.stateLine,
                            font: { size: 14, weight: 'bold' as const },
                        },
                        grid: {
                            color: currentColors.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentColors.text,
                            stepSize: 1,
                            callback: function (value: number | string) {
                                if (Number(value) === 0) return '0 (未激活)'
                                if (Number(value) === 1) return '1 (激活)'
                                return value
                            },
                        },
                        min: -0.1,
                        max: 1.2,
                    },
                },
                interaction: {
                    intersect: false,
                    mode: 'index' as const,
                },
            },
        }), [chartData, threshold, duration, currentTime, showThresholdLines, currentColors, isDarkTheme])

        // 初始化和更新圖表
        useEffect(() => {
            if (!canvasRef.current) return

            const canvas = canvasRef.current
            const ctx = canvas.getContext('2d')
            if (!ctx) return

            try {
                if (chartRef.current && isInitialized.current) {
                    // 更新現有圖表
                    chartRef.current.data = chartConfig.data
                    chartRef.current.options = chartConfig.options
                    
                    // 確保annotation插件正確初始化
                    if (!chartRef.current.options.plugins) {
                        chartRef.current.options.plugins = {}
                    }
                    if (!chartRef.current.options.plugins.annotation) {
                        chartRef.current.options.plugins.annotation = { annotations: {} }
                    }
                    
                    chartRef.current.update('none')
                } else {
                    // 創建新圖表
                    if (chartRef.current) {
                        chartRef.current.destroy()
                    }

                    chartRef.current = new Chart(ctx, chartConfig)
                    isInitialized.current = true
                }
            } catch (error) {
                console.error('T1 Chart error:', error)
            }
        }, [chartConfig])

        // 清理函數
        useEffect(() => {
            return () => {
                if (chartRef.current) {
                    chartRef.current.destroy()
                    chartRef.current = null
                }
                isInitialized.current = false
            }
        }, [])

        return (
            <div className="pure-chart-container" style={{ position: 'relative' }}>
                <canvas
                    ref={canvasRef}
                    width={_width}
                    height={_height}
                    style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        backgroundColor: currentColors.background,
                    }}
                />
            </div>
        )
    }
)

PureT1Chart.displayName = 'PureT1Chart'

export default PureT1Chart
