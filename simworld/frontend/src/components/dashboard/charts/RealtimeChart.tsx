/**
 * 通用實時圖表組件
 * 支持多種圖表類型和實時數據更新
 */
import { useEffect, useRef, useCallback, useState } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
    Filler,
} from 'chart.js'
import { Chart } from 'react-chartjs-2'
import 'chartjs-adapter-date-fns'
import { ChartComponentProps, TimeSeriesData } from '../../../types/charts'

// 註冊 Chart.js 組件
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
    Filler
)

interface RealtimeChartProps extends ChartComponentProps {
    maxDataPoints?: number
    updateInterval?: number
    showLegend?: boolean
    showGrid?: boolean
    animated?: boolean
}

const RealtimeChart: React.FC<RealtimeChartProps> = ({
    config,
    className = '',
    height = 400,
    maxDataPoints = 50,
    updateInterval = 1000,
    showLegend = true,
    showGrid = true,
    animated = true,
    onDataUpdate,
    onError,
}) => {
    const chartRef = useRef<ChartJS | null>(null)
    const [chartData, setChartData] = useState(config.data)
    const [isLoading, setIsLoading] = useState(false)
    const intervalRef = useRef<number | null>(null)

    // 默認圖表選項
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: animated
            ? {
                  duration: 750,
                  easing: 'easeInOutQuart' as const,
              }
            : false,
        interaction: {
            mode: 'index' as const,
            intersect: false,
        },
        plugins: {
            legend: {
                display: showLegend,
                position: 'top' as const,
                labels: {
                    boxWidth: 12,
                    font: {
                        size: 12,
                    },
                },
            },
            title: {
                display: !!config.title,
                text: config.title,
                font: {
                    size: 16,
                    weight: 'bold' as const,
                },
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: '#4a7bff',
                borderWidth: 1,
                cornerRadius: 6,
                displayColors: true,
                callbacks: {
                    title: (context: any[]) => {
                        if (context[0]?.parsed?.x) {
                            return new Date(
                                context[0].parsed.x
                            ).toLocaleString()
                        }
                        return context[0]?.label || ''
                    },
                    label: (context: any) => {
                        const label = context.dataset.label || ''
                        const value =
                            typeof context.parsed.y === 'number'
                                ? context.parsed.y.toFixed(2)
                                : context.parsed.y
                        return `${label}: ${value}`
                    },
                },
            },
        },
        scales: {
            x: {
                type: config.type === 'line' ? 'time' : 'category',
                display: true,
                grid: {
                    display: showGrid,
                    color: 'rgba(255, 255, 255, 0.1)',
                },
                ticks: {
                    color: '#94a3b8',
                    font: {
                        size: 11,
                    },
                },
                ...(config.type === 'line' && {
                    time: {
                        displayFormats: {
                            minute: 'HH:mm',
                            hour: 'HH:mm',
                            day: 'MM-dd',
                        },
                    },
                }),
            },
            y: {
                display: true,
                grid: {
                    display: showGrid,
                    color: 'rgba(255, 255, 255, 0.1)',
                },
                ticks: {
                    color: '#94a3b8',
                    font: {
                        size: 11,
                    },
                },
            },
        },
    }

    // 合併用戶選項
    const chartOptions = {
        ...defaultOptions,
        ...config.options,
    }

    // 添加新數據點
    const addDataPoint = useCallback(
        (newData: TimeSeriesData) => {
            setChartData((prevData) => {
                const updatedData = { ...prevData }

                if (updatedData.datasets) {
                    updatedData.datasets.forEach(
                        (dataset: any, index: number) => {
                            if (newData.data && newData.data.length > 0) {
                                const newPoint =
                                    newData.data[newData.data.length - 1]

                                if (!dataset.data) {
                                    dataset.data = []
                                }

                                // 添加新數據點
                                dataset.data.push(newPoint)

                                // 限制數據點數量
                                if (dataset.data.length > maxDataPoints) {
                                    dataset.data = dataset.data.slice(
                                        -maxDataPoints
                                    )
                                }
                            }
                        }
                    )
                }

                return updatedData
            })

            onDataUpdate?.(newData)
        },
        [maxDataPoints, onDataUpdate]
    )

    // 更新整個數據集
    const updateChartData = useCallback(
        (newData: any) => {
            setChartData(newData)
            onDataUpdate?.(newData)
        },
        [onDataUpdate]
    )

    // 清空圖表數據
    const clearChart = useCallback(() => {
        setChartData((prevData) => {
            const clearedData = { ...prevData }
            if (clearedData.datasets) {
                clearedData.datasets.forEach((dataset: any) => {
                    dataset.data = []
                })
            }
            return clearedData
        })
    }, [])

    // 實時更新邏輯
    useEffect(() => {
        if (config.realtime && config.refreshInterval) {
            intervalRef.current = window.setInterval(() => {
                // 這裡可以添加自動刷新邏輯
                // 通常由父組件通過 props 更新數據
            }, config.refreshInterval)

            return () => {
                if (intervalRef.current) {
                    window.clearInterval(intervalRef.current)
                }
            }
        }
    }, [config.realtime, config.refreshInterval])

    // 當 config.data 變化時更新圖表
    useEffect(() => {
        setChartData(config.data)
    }, [config.data])

    // 錯誤處理
    const handleError = useCallback(
        (error: Error) => {
            console.error('圖表錯誤:', error)
            onError?.(error)
        },
        [onError]
    )

    // 獲取圖表實例的引用
    const getChartRef = useCallback(() => {
        return chartRef.current
    }, [])

    // 導出方法供父組件使用
    React.useImperativeHandle(chartRef, () => ({
        addDataPoint,
        updateChartData,
        clearChart,
        getChartRef,
    }))

    return (
        <div className={`realtime-chart ${className}`} style={{ height }}>
            {isLoading && (
                <div className="chart-loading">
                    <div className="loading-spinner"></div>
                    <span>載入中...</span>
                </div>
            )}
            <Chart
                ref={chartRef}
                type={config.type}
                data={chartData}
                options={chartOptions}
                onError={handleError}
            />
        </div>
    )
}

export default RealtimeChart
