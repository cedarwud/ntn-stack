/**
 * Enhanced T1 Event Chart
 * 增強版 T1 時間條件測量事件圖表
 * 
 * 主要功能：
 * 1. 實時 T1 時間條件監測
 * 2. 服務時間軸視覺化
 * 3. 觸發條件分析
 * 4. GNSS 時間同步狀態
 * 5. 服務持續時間預測
 * 6. 時間門檻調整即時回饋
 */

import React, { useState, useEffect, useCallback, useRef } from 'react'
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
    Filler,
    TimeScale,
    ChartOptions,
    TooltipItem,
    ScatterDataPoint
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import annotationPlugin from 'chartjs-plugin-annotation'
import 'chartjs-adapter-date-fns'
import { netstackFetch } from '../../../../config/api-config'

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    TimeScale,
    annotationPlugin
)

interface UEPosition {
    latitude: number
    longitude: number
    altitude: number
}

interface RealTimeT1Data {
    timestamp: string
    trigger_state: string
    trigger_condition_met: boolean
    measurement_values: {
        elapsed_time: number
        service_start_time: string
        total_service_duration: number
        remaining_service_time: number
        current_time: string
        epoch_time: string
        gnss_time_offset_ms: number
        sync_accuracy_ms: number
    }
    trigger_details: {
        elapsed_time: number
        t1_threshold: number
        required_duration: number
        remaining_service_time: number
        threshold_condition_met: boolean
        duration_condition_met: boolean
        overall_condition_met: boolean
        gnss_time_offset_ms: number
        sync_accuracy_ms: number
    }
    sib19_data: {
        time_frame_type: string
        epoch_time: string
        service_duration: number
        sync_accuracy_requirement_ms: number
    }
}

interface EnhancedT1ChartProps {
    t1Threshold: number // 時間門檻 (秒)
    requiredDuration: number // 要求持續時間 (秒)
    timeToTrigger: number // 觸發時間 (ms)
    uePosition: UEPosition
    showThresholdLines?: boolean
    isDarkTheme?: boolean
    useRealData?: boolean
    autoUpdate?: boolean
    updateInterval?: number
    onThemeToggle?: () => void
    onDataModeToggle?: () => void
    onTriggerEvent?: (eventData: any) => void
}

interface DataPoint {
    x: string | number
    y: number
    elapsed_time?: number
    threshold_met?: boolean
    duration_met?: boolean
    overall_met?: boolean
    sync_accuracy?: number
}

const EnhancedT1Chart: React.FC<EnhancedT1ChartProps> = ({
    t1Threshold,
    requiredDuration,
    timeToTrigger,
    uePosition,
    showThresholdLines = true,
    isDarkTheme = false,
    useRealData = true,
    autoUpdate = true,
    updateInterval = 2000,
    onThemeToggle,
    onDataModeToggle,
    onTriggerEvent
}) => {
    const [data, setData] = useState<RealTimeT1Data[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null)
    const [isConnected, setIsConnected] = useState(true)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)

    // 數據處理
    const processChartData = useCallback(() => {
        if (data.length === 0) {
            return {
                labels: [],
                datasets: []
            }
        }

        const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString())
        
        // 經過時間數據
        const elapsedTimeData: DataPoint[] = data.map((d, index) => ({
            x: index,
            y: d.measurement_values.elapsed_time,
            elapsed_time: d.measurement_values.elapsed_time,
            threshold_met: d.trigger_details.threshold_condition_met,
            duration_met: d.trigger_details.duration_condition_met,
            overall_met: d.trigger_details.overall_condition_met,
            sync_accuracy: d.trigger_details.sync_accuracy_ms
        }))

        // 剩餘服務時間數據
        const remainingTimeData: DataPoint[] = data.map((d, index) => ({
            x: index,
            y: d.measurement_values.remaining_service_time,
            elapsed_time: d.measurement_values.elapsed_time,
            threshold_met: d.trigger_details.threshold_condition_met,
            duration_met: d.trigger_details.duration_condition_met,
            overall_met: d.trigger_details.overall_condition_met
        }))

        // 時間同步精度數據
        const syncAccuracyData: DataPoint[] = data.map((d, index) => ({
            x: index,
            y: d.trigger_details.sync_accuracy_ms,
            elapsed_time: d.measurement_values.elapsed_time,
            threshold_met: d.trigger_details.threshold_condition_met,
            sync_accuracy: d.trigger_details.sync_accuracy_ms
        }))

        const themeColors = isDarkTheme ? {
            primary: '#00d4ff',
            secondary: '#ff6b35',
            success: '#00ff88',
            warning: '#ffb347',
            danger: '#ff4757',
            info: '#7bed9f',
            grid: '#2c3e50',
            text: '#ecf0f1',
            background: '#34495e'
        } : {
            primary: '#007bff',
            secondary: '#fd7e14',
            success: '#28a745',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#17a2b8',
            grid: '#dee2e6',
            text: '#495057',
            background: '#ffffff'
        }

        return {
            labels,
            datasets: [
                {
                    label: '經過時間 (秒)',
                    data: elapsedTimeData,
                    borderColor: themeColors.primary,
                    backgroundColor: `${themeColors.primary}20`,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointBackgroundColor: elapsedTimeData.map(d => 
                        d.threshold_met ? themeColors.success : themeColors.warning
                    ),
                    pointBorderColor: themeColors.primary,
                    pointRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: '剩餘服務時間 (秒)',
                    data: remainingTimeData,
                    borderColor: themeColors.secondary,
                    backgroundColor: `${themeColors.secondary}20`,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointBackgroundColor: remainingTimeData.map(d => 
                        d.duration_met ? themeColors.success : themeColors.danger
                    ),
                    pointBorderColor: themeColors.secondary,
                    pointRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: '時間同步精度 (ms)',
                    data: syncAccuracyData,
                    borderColor: themeColors.info,
                    backgroundColor: `${themeColors.info}20`,
                    borderWidth: 1,
                    fill: false,
                    tension: 0.1,
                    pointBackgroundColor: syncAccuracyData.map(d => 
                        (d.sync_accuracy || 0) < 50 ? themeColors.success : themeColors.warning
                    ),
                    pointBorderColor: themeColors.info,
                    pointRadius: 3,
                    yAxisID: 'y1'
                }
            ]
        }
    }, [data, isDarkTheme, t1Threshold, requiredDuration])

    // 圖表配置
    const chartOptions: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index' as const,
            intersect: false,
        },
        plugins: {
            title: {
                display: true,
                text: `T1 時間條件測量事件 | 門檻: ${t1Threshold}s | 持續時間: ${requiredDuration}s`,
                color: isDarkTheme ? '#ecf0f1' : '#495057',
                font: {
                    size: 16,
                    weight: 'bold'
                }
            },
            legend: {
                display: true,
                position: 'top' as const,
                labels: {
                    color: isDarkTheme ? '#ecf0f1' : '#495057',
                    usePointStyle: true,
                    padding: 20
                }
            },
            tooltip: {
                enabled: true,
                backgroundColor: isDarkTheme ? '#2c3e50dd' : '#f8f9fadd',
                titleColor: isDarkTheme ? '#ecf0f1' : '#495057',
                bodyColor: isDarkTheme ? '#ecf0f1' : '#495057',
                borderColor: isDarkTheme ? '#34495e' : '#dee2e6',
                borderWidth: 1,
                callbacks: {
                    title: (context: TooltipItem<'line'>[]) => {
                        if (context.length > 0) {
                            const dataIndex = context[0].dataIndex
                            if (data[dataIndex]) {
                                return `時間: ${new Date(data[dataIndex].timestamp).toLocaleTimeString()}`
                            }
                        }
                        return ''
                    },
                    label: (context: TooltipItem<'line'>) => {
                        const dataIndex = context.dataIndex
                        const dataset = context.dataset
                        const point = dataset.data[dataIndex] as DataPoint
                        
                        let label = dataset.label || ''
                        if (label) {
                            label += ': '
                        }
                        
                        if (dataset.label === '經過時間 (秒)') {
                            label += `${point.y.toFixed(1)}s`
                            if (point.threshold_met) {
                                label += ' ✅ 門檻已達成'
                            } else {
                                label += ' ⏳ 未達門檻'
                            }
                        } else if (dataset.label === '剩餘服務時間 (秒)') {
                            label += `${point.y.toFixed(1)}s`
                            if (point.duration_met) {
                                label += ' ✅ 持續時間足夠'
                            } else {
                                label += ' ❌ 持續時間不足'
                            }
                        } else if (dataset.label === '時間同步精度 (ms)') {
                            label += `${point.y.toFixed(2)}ms`
                            if (point.y < 50) {
                                label += ' ✅ 精度良好'
                            } else {
                                label += ' ⚠️ 精度需改善'
                            }
                        }
                        
                        return label
                    },
                    afterBody: (context: TooltipItem<'line'>[]) => {
                        if (context.length > 0) {
                            const dataIndex = context[0].dataIndex
                            const point = context[0].dataset.data[dataIndex] as DataPoint
                            
                            if (point.overall_met) {
                                return ['', '🎯 T1 事件條件滿足！']
                            } else {
                                return ['', '⏱️ T1 事件條件未滿足']
                            }
                        }
                        return []
                    }
                }
            },
            annotation: showThresholdLines ? {
                annotations: {
                    thresholdLine: {
                        type: 'line' as const,
                        yMin: t1Threshold,
                        yMax: t1Threshold,
                        yScaleID: 'y',
                        borderColor: isDarkTheme ? '#e74c3c' : '#dc3545',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        label: {
                            display: true,
                            content: `T1 門檻: ${t1Threshold}s`,
                            position: 'end' as const,
                            backgroundColor: isDarkTheme ? '#e74c3c' : '#dc3545',
                            color: '#ffffff',
                            font: {
                                size: 11
                            }
                        }
                    },
                    durationLine: {
                        type: 'line' as const,
                        yMin: requiredDuration,
                        yMax: requiredDuration,
                        yScaleID: 'y',
                        borderColor: isDarkTheme ? '#f39c12' : '#ffc107',
                        borderWidth: 2,
                        borderDash: [3, 3],
                        label: {
                            display: true,
                            content: `要求持續: ${requiredDuration}s`,
                            position: 'start' as const,
                            backgroundColor: isDarkTheme ? '#f39c12' : '#ffc107',
                            color: '#ffffff',
                            font: {
                                size: 11
                            }
                        }
                    },
                    syncRequirement: {
                        type: 'line' as const,
                        yMin: 50,
                        yMax: 50,
                        yScaleID: 'y1',
                        borderColor: isDarkTheme ? '#17a2b8' : '#17a2b8',
                        borderWidth: 1,
                        borderDash: [2, 2],
                        label: {
                            display: true,
                            content: '同步要求: 50ms',
                            position: 'center' as const,
                            backgroundColor: isDarkTheme ? '#17a2b8' : '#17a2b8',
                            color: '#ffffff',
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            } : undefined
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: '時間軸',
                    color: isDarkTheme ? '#ecf0f1' : '#495057',
                    font: {
                        size: 12,
                        weight: 'bold'
                    }
                },
                grid: {
                    color: isDarkTheme ? '#34495e' : '#dee2e6',
                    lineWidth: 1
                },
                ticks: {
                    color: isDarkTheme ? '#bdc3c7' : '#6c757d',
                    maxTicksLimit: 10
                }
            },
            y: {
                type: 'linear' as const,
                display: true,
                position: 'left' as const,
                title: {
                    display: true,
                    text: '時間 (秒)',
                    color: isDarkTheme ? '#ecf0f1' : '#495057',
                    font: {
                        size: 12,
                        weight: 'bold'
                    }
                },
                grid: {
                    color: isDarkTheme ? '#34495e' : '#dee2e6',
                    lineWidth: 1
                },
                ticks: {
                    color: isDarkTheme ? '#bdc3c7' : '#6c757d'
                },
                beginAtZero: true
            },
            y1: {
                type: 'linear' as const,
                display: true,
                position: 'right' as const,
                title: {
                    display: true,
                    text: '同步精度 (ms)',
                    color: isDarkTheme ? '#ecf0f1' : '#495057',
                    font: {
                        size: 12,
                        weight: 'bold'
                    }
                },
                grid: {
                    drawOnChartArea: false,
                },
                ticks: {
                    color: isDarkTheme ? '#bdc3c7' : '#6c757d'
                },
                beginAtZero: true,
                max: 100
            }
        }
    }

    // 獲取實時數據
    const fetchRealTimeData = useCallback(async () => {
        if (!useRealData) return

        setIsLoading(true)
        setError(null)

        try {
            const response = await netstackFetch('/api/measurement-events/T1/data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ue_position: uePosition,
                    t1_params: {
                        t1_threshold: t1Threshold,
                        duration: requiredDuration,
                        time_to_trigger: timeToTrigger
                    }
                })
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const newData: RealTimeT1Data = await response.json()
            
            setData(prevData => {
                const updatedData = [...prevData, newData]
                // 保留最近 100 個數據點
                return updatedData.slice(-100)
            })

            setLastUpdateTime(new Date())
            setIsConnected(true)

            // 檢查觸發條件
            if (newData.trigger_condition_met && onTriggerEvent) {
                onTriggerEvent(newData)
            }

        } catch (error) {
            console.error('❌ T1 數據獲取失敗:', error)
            setError(error instanceof Error ? error.message : '未知錯誤')
            setIsConnected(false)
        } finally {
            setIsLoading(false)
        }
    }, [useRealData, uePosition, t1Threshold, requiredDuration, timeToTrigger, onTriggerEvent])

    // 生成模擬數據
    const generateSimulatedData = useCallback(() => {
        if (useRealData) return

        const now = new Date()
        const simulatedData: RealTimeT1Data = {
            timestamp: now.toISOString(),
            trigger_state: 'idle',
            trigger_condition_met: false,
            measurement_values: {
                elapsed_time: Math.random() * 7200, // 0-2小時
                service_start_time: new Date(now.getTime() - Math.random() * 7200000).toISOString(),
                total_service_duration: 7200,
                remaining_service_time: Math.random() * 3600, // 0-1小時
                current_time: now.toISOString(),
                epoch_time: now.toISOString(),
                gnss_time_offset_ms: (Math.random() - 0.5) * 100, // ±50ms
                sync_accuracy_ms: Math.random() * 80 + 10 // 10-90ms
            },
            trigger_details: {
                elapsed_time: 0,
                t1_threshold: t1Threshold,
                required_duration: requiredDuration,
                remaining_service_time: 0,
                threshold_condition_met: false,
                duration_condition_met: false,
                overall_condition_met: false,
                gnss_time_offset_ms: 0,
                sync_accuracy_ms: 0
            },
            sib19_data: {
                time_frame_type: "absolute",
                epoch_time: now.toISOString(),
                service_duration: 7200,
                sync_accuracy_requirement_ms: 50
            }
        }

        // 計算觸發條件
        simulatedData.trigger_details.elapsed_time = simulatedData.measurement_values.elapsed_time
        simulatedData.trigger_details.remaining_service_time = simulatedData.measurement_values.remaining_service_time
        simulatedData.trigger_details.threshold_condition_met = simulatedData.measurement_values.elapsed_time > t1Threshold
        simulatedData.trigger_details.duration_condition_met = simulatedData.measurement_values.remaining_service_time >= requiredDuration
        simulatedData.trigger_details.overall_condition_met = simulatedData.trigger_details.threshold_condition_met && simulatedData.trigger_details.duration_condition_met
        simulatedData.trigger_details.gnss_time_offset_ms = simulatedData.measurement_values.gnss_time_offset_ms
        simulatedData.trigger_details.sync_accuracy_ms = simulatedData.measurement_values.sync_accuracy_ms

        simulatedData.trigger_condition_met = simulatedData.trigger_details.overall_condition_met
        simulatedData.trigger_state = simulatedData.trigger_condition_met ? 'triggered' : 'idle'

        setData(prevData => {
            const updatedData = [...prevData, simulatedData]
            return updatedData.slice(-100)
        })

        setLastUpdateTime(new Date())
        setIsConnected(true)

        if (simulatedData.trigger_condition_met && onTriggerEvent) {
            onTriggerEvent(simulatedData)
        }
    }, [useRealData, t1Threshold, requiredDuration, onTriggerEvent])

    // 設置定時更新
    useEffect(() => {
        if (!autoUpdate) return

        const updateFunction = useRealData ? fetchRealTimeData : generateSimulatedData

        // 立即執行一次
        updateFunction()

        // 設置定時更新
        intervalRef.current = setInterval(updateFunction, updateInterval)

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [autoUpdate, fetchRealTimeData, generateSimulatedData, updateInterval, useRealData])

    const chartData = processChartData()

    return (
        <div className={`enhanced-t1-chart ${isDarkTheme ? 'dark-theme' : 'light-theme'}`}>
            {/* 圖表頭部資訊 */}
            <div className="chart-header">
                <div className="chart-info">
                    <div className="data-status">
                        <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
                            {isConnected ? '🟢' : '🔴'}
                        </span>
                        <span className="status-text">
                            {useRealData ? '真實數據' : '模擬數據'} | 
                            {isLoading ? ' 更新中...' : ` 最後更新: ${lastUpdateTime?.toLocaleTimeString() || 'N/A'}`}
                        </span>
                    </div>
                    {error && (
                        <div className="error-message">
                            ⚠️ {error}
                        </div>
                    )}
                </div>
                
                <div className="chart-controls">
                    <button
                        className="control-btn"
                        onClick={onDataModeToggle}
                        title={useRealData ? '切換到模擬數據' : '切換到真實數據'}
                    >
                        {useRealData ? '📡' : '🎲'}
                    </button>
                    <button
                        className="control-btn"
                        onClick={onThemeToggle}
                        title="切換主題"
                    >
                        {isDarkTheme ? '🌙' : '☀️'}
                    </button>
                </div>
            </div>

            {/* 關鍵指標顯示 */}
            {data.length > 0 && (
                <div className="metrics-display">
                    <div className="metric-item">
                        <span className="metric-label">經過時間:</span>
                        <span className="metric-value">
                            {data[data.length - 1].measurement_values.elapsed_time.toFixed(1)}s
                        </span>
                    </div>
                    <div className="metric-item">
                        <span className="metric-label">剩餘時間:</span>
                        <span className="metric-value">
                            {data[data.length - 1].measurement_values.remaining_service_time.toFixed(1)}s
                        </span>
                    </div>
                    <div className="metric-item">
                        <span className="metric-label">同步精度:</span>
                        <span className="metric-value">
                            {data[data.length - 1].trigger_details.sync_accuracy_ms.toFixed(2)}ms
                        </span>
                    </div>
                    <div className="metric-item">
                        <span className="metric-label">觸發狀態:</span>
                        <span className={`metric-value ${data[data.length - 1].trigger_condition_met ? 'triggered' : 'idle'}`}>
                            {data[data.length - 1].trigger_condition_met ? '🎯 已觸發' : '⏱️ 待機'}
                        </span>
                    </div>
                </div>
            )}

            {/* 圖表區域 */}
            <div className="chart-area h-96 w-full" style={{ height: '400px', minHeight: '400px' }}>
                <Line data={chartData} options={chartOptions} />
            </div>
        </div>
    )
}

export default EnhancedT1Chart