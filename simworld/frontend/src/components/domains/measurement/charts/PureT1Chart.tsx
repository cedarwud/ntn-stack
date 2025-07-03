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

// T1 事件模擬數據 - 時間窗口狀態變化
const generateT1TimeData = (threshold: number, duration: number) => {
    const dataPoints = []
    const totalTime = 120000 // 120 seconds
    const step = 1000 // 1 second steps
    
    for (let t = 0; t <= totalTime; t += step) {
        // 模擬時間測量值 Mt (毫秒)
        let mt = 0
        
        // 創建幾個時間窗口模式
        if (t >= 20000 && t <= 35000) {
            // 第一個時間窗口：20-35秒，測量值超過閾值
            mt = threshold + 500 + Math.sin((t - 20000) / 2000) * 200
        } else if (t >= 50000 && t <= 80000) {
            // 第二個時間窗口：50-80秒，測量值接近閾值
            mt = threshold + Math.cos((t - 50000) / 3000) * 400
        } else if (t >= 90000 && t <= 110000) {
            // 第三個時間窗口：90-110秒，測量值遠超閾值
            mt = threshold + 800 + Math.random() * 200
        } else {
            // 基準時間測量值，低於閾值
            mt = threshold * 0.3 + Math.random() * threshold * 0.2
        }
        
        dataPoints.push({ x: t / 1000, y: mt }) // Convert to seconds for display
    }
    
    return dataPoints
}

// T1 條件狀態數據生成
const generateT1ConditionData = (timeData: any[], threshold: number, duration: number) => {
    const conditionData = []
    let conditionState = 0 // 0 = not triggered, 1 = triggered
    let triggerStartTime = 0
    
    for (const point of timeData) {
        const currentTime = point.x * 1000 // Convert back to ms
        const mt = point.y
        
        if (mt > threshold) {
            if (conditionState === 0) {
                // Start of potential trigger
                triggerStartTime = currentTime
                conditionState = 0.5 // Pending state
            } else if (conditionState === 0.5) {
                // Check if duration requirement is met
                if (currentTime - triggerStartTime >= duration) {
                    conditionState = 1 // Fully triggered
                }
            }
        } else {
            // Below threshold - reset condition
            conditionState = 0
            triggerStartTime = 0
        }
        
        conditionData.push({ x: point.x, y: conditionState })
    }
    
    return conditionData
}

interface PureT1ChartProps {
    width?: number
    height?: number
    threshold?: number // t1-Threshold in milliseconds
    duration?: number // Duration parameter in milliseconds
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
        showThresholdLines = true,
        isDarkTheme = true,
        onThemeToggle,
    }) => {
        const canvasRef = useRef<HTMLCanvasElement>(null)
        const chartRef = useRef<Chart | null>(null)
        const isInitialized = useRef(false)

        // 使用 useMemo 穩定主題配色方案
        const colors = useMemo(
            () => ({
                dark: {
                    timeLine: '#00D4AA', // Teal for time measurement
                    conditionLine: '#FF6B6B', // Red for condition state
                    thresholdLine: '#FFD93D', // Yellow for threshold
                    durationLine: '#6BCF7F', // Green for duration
                    title: '#FFD93D',
                    text: 'white',
                    grid: 'rgba(255, 255, 255, 0.1)',
                    background: 'transparent',
                },
                light: {
                    timeLine: '#009688', // Dark teal
                    conditionLine: '#F44336', // Dark red
                    thresholdLine: '#FF9800', // Orange
                    durationLine: '#4CAF50', // Green
                    title: '#FF9800',
                    text: '#333333',
                    grid: 'rgba(0, 0, 0, 0.1)',
                    background: 'white',
                },
            }),
            []
        )

        const currentColors = isDarkTheme ? colors.dark : colors.light

        // 穩定的數據生成
        const chartData = useMemo(() => {
            const timeData = generateT1TimeData(threshold, duration)
            const conditionData = generateT1ConditionData(timeData, threshold, duration)
            
            return {
                timeData,
                conditionData,
            }
        }, [threshold, duration])

        // 穩定的圖表配置
        const chartConfig = useMemo(() => ({
            type: 'line' as const,
            data: {
                datasets: [
                    {
                        label: 'Time Measurement (Mt)',
                        data: chartData.timeData,
                        borderColor: currentColors.timeLine,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        tension: 0.3,
                        yAxisID: 'y',
                    },
                    {
                        label: 'T1 Condition State',
                        data: chartData.conditionData,
                        borderColor: currentColors.conditionLine,
                        backgroundColor: currentColors.conditionLine + '20',
                        borderWidth: 3,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        tension: 0,
                        yAxisID: 'y1',
                        stepped: true,
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
                        text: '3GPP TS 38.331 Event T1: Time Window Condition',
                        color: currentColors.title,
                        font: { size: 16, weight: 'bold' as const },
                    },
                    legend: {
                        display: true,
                        position: 'top' as const,
                        labels: { color: currentColors.text },
                    },
                    annotation: {
                        annotations: showThresholdLines
                            ? {
                                  thresholdLine: {
                                      type: 'line' as const,
                                      yMin: threshold,
                                      yMax: threshold,
                                      yScaleID: 'y',
                                      borderColor: currentColors.thresholdLine,
                                      borderWidth: 2,
                                      borderDash: [8, 4],
                                      label: {
                                          display: true,
                                          content: `t1-Threshold: ${threshold}ms`,
                                          position: 'end' as const,
                                          backgroundColor: currentColors.thresholdLine,
                                          color: isDarkTheme ? '#000' : '#fff',
                                          font: { size: 11 },
                                      },
                                  },
                                  durationLine: {
                                      type: 'line' as const,
                                      yMin: threshold + duration * 0.1,
                                      yMax: threshold + duration * 0.1,
                                      yScaleID: 'y',
                                      borderColor: currentColors.durationLine,
                                      borderWidth: 1,
                                      borderDash: [4, 2],
                                      label: {
                                          display: true,
                                          content: `Duration: ${duration}ms`,
                                          position: 'start' as const,
                                          backgroundColor: currentColors.durationLine,
                                          color: isDarkTheme ? '#000' : '#fff',
                                          font: { size: 10 },
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
                            text: 'Time (seconds)',
                            color: currentColors.text,
                            font: { size: 14 },
                        },
                        grid: {
                            color: currentColors.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentColors.text,
                            callback: function (value: any) {
                                return value + 's'
                            },
                        },
                        min: 0,
                        max: 120,
                    },
                    y: {
                        type: 'linear' as const,
                        display: true,
                        position: 'left' as const,
                        title: {
                            display: true,
                            text: 'Time Measurement (Mt) [ms]',
                            color: currentColors.text,
                            font: { size: 14 },
                        },
                        grid: {
                            color: currentColors.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentColors.text,
                            callback: function (value: any) {
                                return value + 'ms'
                            },
                        },
                        min: 0,
                        max: Math.max(threshold * 2, 15000),
                    },
                    y1: {
                        type: 'linear' as const,
                        display: true,
                        position: 'right' as const,
                        title: {
                            display: true,
                            text: 'T1 State (0=Not Triggered, 1=Triggered)',
                            color: currentColors.text,
                            font: { size: 12 },
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            color: currentColors.text,
                            stepSize: 0.5,
                            callback: function (value: any) {
                                if (value === 0) return 'Not Triggered'
                                if (value === 0.5) return 'Pending'
                                if (value === 1) return 'Triggered'
                                return value
                            },
                        },
                        min: 0,
                        max: 1,
                    },
                },
                interaction: {
                    intersect: false,
                    mode: 'index' as const,
                },
            },
        }), [chartData, threshold, duration, showThresholdLines, currentColors, isDarkTheme])

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
