/**
 * Enhanced A4 Event Chart
 * 增強版 A4 信號強度測量事件圖表
 * 
 * 主要功能：
 * 1. 實時 A4 信號強度監測 (RSRP)
 * 2. 位置補償效果視覺化
 * 3. 服務衛星 vs 鄰居衛星信號比較
 * 4. A4 門檻和遲滯帶顯示
 * 5. 觸發條件狀態追蹤
 * 6. 位置補償參數即時調整
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
    TooltipItem
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

interface A4Parameters {
    a4_threshold: number
    hysteresis: number
    time_to_trigger: number
}

interface A4MeasurementData {
    timestamp: string
    trigger_state: string
    trigger_condition_met: boolean
    measurement_values: {
        serving_rsrp: number
        serving_distance: number
        best_neighbor_rsrp: number
        best_neighbor_distance: number
        best_neighbor_id: string
        position_compensation: number
        time_compensation: number
        distance_diff_limited_km: number
        signal_compensation_db: number
        compensated_neighbor_rsrp: number
    }
    trigger_details: {
        serving_rsrp: number
        original_neighbor_rsrp: number
        compensated_neighbor_rsrp: number
        best_neighbor_id: string
        threshold: number
        hysteresis: number
        position_compensation_m: number
        time_compensation_ms: number
        distance_diff_limited_km: number
        signal_compensation_db: number
        condition_met: boolean
    }
    satellite_positions: Record<string, unknown>
}

interface RealTimeA4Data {
    timestamp: string
    serving_rsrp: number
    original_neighbor_rsrp: number
    compensated_neighbor_rsrp: number
    threshold: number
    position_compensation_m: number
    signal_compensation_db: number
    trigger_condition_met: boolean
    best_neighbor_id: string
}

interface EnhancedA4ChartProps {
    uePosition: UEPosition
    a4Parameters: A4Parameters
    isActive: boolean
    updateInterval?: number
    maxDataPoints?: number
    onTriggerEvent?: (data: RealTimeA4Data) => void
    onError?: (error: string) => void
    theme?: 'light' | 'dark'
}

const EnhancedA4Chart: React.FC<EnhancedA4ChartProps> = ({
    uePosition,
    a4Parameters,
    isActive,
    updateInterval = 2000,
    maxDataPoints = 100,
    onTriggerEvent,
    onError,
    theme = 'light'
}) => {
    const [chartData, setChartData] = useState<unknown>(null)
    const [realTimeData, setRealTimeData] = useState<RealTimeA4Data[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [statistics, setStatistics] = useState({
        totalMeasurements: 0,
        triggerEvents: 0,
        avgSignalCompensation: 0,
        avgPositionCompensation: 0,
        currentNeighborId: 'N/A'
    })

    const intervalRef = useRef<NodeJS.Timeout | null>(null)
    const isComponentMounted = useRef(true)

    // API 調用函數
    const fetchA4Data = useCallback(async (): Promise<A4MeasurementData | null> => {
        try {
            setIsLoading(true)
            
            const response = await netstackFetch('/api/measurement-events/A4/data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ue_position: uePosition,
                    a4_params: a4Parameters
                })
            })

            if (!response.ok) {
                throw new Error(`A4 API 錯誤: ${response.status} ${response.statusText}`)
            }

            const data: A4MeasurementData = await response.json()
            return data

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'A4 數據獲取失敗'
            setError(errorMessage)
            onError?.(errorMessage)
            return null
        } finally {
            setIsLoading(false)
        }
    }, [uePosition, a4Parameters, onError])

    // 處理實時數據
    const processRealTimeData = useCallback((data: A4MeasurementData) => {
        if (!data?.trigger_details) return

        const newDataPoint: RealTimeA4Data = {
            timestamp: data.timestamp,
            serving_rsrp: data.trigger_details.serving_rsrp,
            original_neighbor_rsrp: data.trigger_details.original_neighbor_rsrp,
            compensated_neighbor_rsrp: data.trigger_details.compensated_neighbor_rsrp,
            threshold: data.trigger_details.threshold,
            position_compensation_m: data.trigger_details.position_compensation_m,
            signal_compensation_db: data.trigger_details.signal_compensation_db,
            trigger_condition_met: data.trigger_details.condition_met,
            best_neighbor_id: data.trigger_details.best_neighbor_id
        }

        setRealTimeData(prevData => {
            const newData = [...prevData, newDataPoint]
            
            // 限制數據點數量
            if (newData.length > maxDataPoints) {
                newData.splice(0, newData.length - maxDataPoints)
            }
            
            return newData
        })

        // 更新統計信息
        setStatistics(prevStats => ({
            totalMeasurements: prevStats.totalMeasurements + 1,
            triggerEvents: prevStats.triggerEvents + (newDataPoint.trigger_condition_met ? 1 : 0),
            avgSignalCompensation: (prevStats.avgSignalCompensation * prevStats.totalMeasurements + newDataPoint.signal_compensation_db) / (prevStats.totalMeasurements + 1),
            avgPositionCompensation: (prevStats.avgPositionCompensation * prevStats.totalMeasurements + Math.abs(newDataPoint.position_compensation_m)) / (prevStats.totalMeasurements + 1),
            currentNeighborId: newDataPoint.best_neighbor_id
        }))

        // 觸發事件回調
        if (newDataPoint.trigger_condition_met && onTriggerEvent) {
            onTriggerEvent(newDataPoint)
        }

    }, [maxDataPoints, onTriggerEvent])

    // 數據輪詢
    const startDataPolling = useCallback(() => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
        }

        intervalRef.current = setInterval(async () => {
            if (!isComponentMounted.current || !isActive) return

            const data = await fetchA4Data()
            if (data && isComponentMounted.current) {
                processRealTimeData(data)
            }
        }, updateInterval)
    }, [fetchA4Data, processRealTimeData, updateInterval, isActive])

    // 生成圖表數據
    const generateChartData = useCallback(() => {
        if (realTimeData.length === 0) return null

        const timestamps = realTimeData.map(d => new Date(d.timestamp))
        
        return {
            labels: timestamps,
            datasets: [
                {
                    label: '服務衛星 RSRP',
                    data: realTimeData.map(d => d.serving_rsrp),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.2,
                    fill: false
                },
                {
                    label: '原始鄰居衛星 RSRP',
                    data: realTimeData.map(d => d.original_neighbor_rsrp),
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.2,
                    fill: false,
                    borderDash: [5, 5]
                },
                {
                    label: '補償後鄰居衛星 RSRP',
                    data: realTimeData.map(d => d.compensated_neighbor_rsrp),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.2,
                    fill: false
                },
                {
                    label: 'A4 門檻',
                    data: realTimeData.map(d => d.threshold),
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0,
                    fill: false,
                    borderDash: [10, 5]
                }
            ]
        }
    }, [realTimeData, theme])

    // 圖表配置
    const chartOptions: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    displayFormats: {
                        second: 'HH:mm:ss',
                        minute: 'HH:mm',
                        hour: 'HH:mm'
                    }
                },
                grid: {
                    color: theme === 'dark' ? '#374151' : '#e5e7eb'
                },
                ticks: {
                    color: theme === 'dark' ? '#ffffff' : '#374151',
                    maxTicksLimit: 10
                },
                title: {
                    display: true,
                    text: '時間',
                    color: theme === 'dark' ? '#ffffff' : '#374151'
                }
            },
            y: {
                grid: {
                    color: theme === 'dark' ? '#374151' : '#e5e7eb'
                },
                ticks: {
                    color: theme === 'dark' ? '#ffffff' : '#374151'
                },
                title: {
                    display: true,
                    text: 'RSRP (dBm)',
                    color: theme === 'dark' ? '#ffffff' : '#374151'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'A4 信號強度測量事件 - 位置補償效果',
                color: theme === 'dark' ? '#ffffff' : '#374151',
                font: {
                    size: 16,
                    weight: 'bold'
                }
            },
            legend: {
                position: 'top',
                labels: {
                    color: theme === 'dark' ? '#ffffff' : '#374151',
                    usePointStyle: true,
                    padding: 20
                }
            },
            tooltip: {
                backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
                titleColor: theme === 'dark' ? '#ffffff' : '#374151',
                bodyColor: theme === 'dark' ? '#ffffff' : '#374151',
                borderColor: theme === 'dark' ? '#374151' : '#e5e7eb',
                borderWidth: 1,
                callbacks: {
                    label: (context: TooltipItem<'line'>) => {
                        const value = context.parsed.y
                        const dataIndex = context.dataIndex
                        const data = realTimeData[dataIndex]
                        
                        if (context.datasetIndex === 0) {
                            return `服務衛星 RSRP: ${value.toFixed(1)} dBm`
                        } else if (context.datasetIndex === 1) {
                            return `原始鄰居 RSRP: ${value.toFixed(1)} dBm`
                        } else if (context.datasetIndex === 2) {
                            const compensation = data?.signal_compensation_db || 0
                            return `補償後 RSRP: ${value.toFixed(1)} dBm (補償: ${compensation.toFixed(1)} dB)`
                        } else if (context.datasetIndex === 3) {
                            return `A4 門檻: ${value.toFixed(1)} dBm`
                        }
                        return `${value.toFixed(1)} dBm`
                    },
                    afterBody: (tooltipItems: TooltipItem<'line'>[]) => {
                        if (tooltipItems.length === 0) return []
                        
                        const dataIndex = tooltipItems[0].dataIndex
                        const data = realTimeData[dataIndex]
                        
                        if (!data) return []
                        
                        return [
                            ``,
                            `鄰居衛星: ${data.best_neighbor_id}`,
                            `位置補償: ${(data.position_compensation_m / 1000).toFixed(2)} km`,
                            `信號補償: ${data.signal_compensation_db.toFixed(1)} dB`,
                            `觸發狀態: ${data.trigger_condition_met ? '已觸發' : '未觸發'}`
                        ]
                    }
                }
            },
            annotation: {
                annotations: realTimeData.reduce((acc, data, index) => {
                    if (data.trigger_condition_met) {
                        acc[`trigger-${index}`] = {
                            type: 'point',
                            xValue: new Date(data.timestamp),
                            yValue: data.compensated_neighbor_rsrp,
                            backgroundColor: '#dc2626',
                            borderColor: '#ffffff',
                            borderWidth: 2,
                            radius: 8,
                            display: true
                        }
                    }
                    return acc
                }, {} as Record<string, unknown>)
            }
        }
    }

    // 組件生命週期
    useEffect(() => {
        isComponentMounted.current = true
        return () => {
            isComponentMounted.current = false
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [])

    useEffect(() => {
        if (isActive) {
            startDataPolling()
        } else {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [isActive, startDataPolling])

    useEffect(() => {
        const newChartData = generateChartData()
        setChartData(newChartData)
    }, [generateChartData])

    // 清理數據
    const clearData = useCallback(() => {
        setRealTimeData([])
        setStatistics({
            totalMeasurements: 0,
            triggerEvents: 0,
            avgSignalCompensation: 0,
            avgPositionCompensation: 0,
            currentNeighborId: 'N/A'
        })
        setError(null)
    }, [])

    if (error) {
        return (
            <div className={`p-4 rounded-lg border ${
                theme === 'dark' 
                    ? 'bg-red-900/20 border-red-700 text-red-200' 
                    : 'bg-red-50 border-red-200 text-red-700'
            }`}>
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">⚠️</span>
                    <span className="font-semibold">A4 圖表錯誤</span>
                </div>
                <p className="text-sm">{error}</p>
                <button 
                    onClick={clearData}
                    className={`mt-2 px-3 py-1 rounded text-sm ${
                        theme === 'dark'
                            ? 'bg-red-700 hover:bg-red-600 text-white'
                            : 'bg-red-100 hover:bg-red-200 text-red-700'
                    }`}
                >
                    重試
                </button>
            </div>
        )
    }

    return (
        <div className="w-full h-full space-y-4">
            {/* 統計信息面板 */}
            <div className={`grid grid-cols-2 md:grid-cols-5 gap-4 p-4 rounded-lg ${
                theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'
            }`}>
                <div className="text-center">
                    <div className={`text-2xl font-bold ${
                        theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                    }`}>
                        {statistics.totalMeasurements}
                    </div>
                    <div className={`text-xs ${
                        theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                        總測量次數
                    </div>
                </div>
                
                <div className="text-center">
                    <div className={`text-2xl font-bold ${
                        statistics.triggerEvents > 0
                            ? (theme === 'dark' ? 'text-red-400' : 'text-red-600')
                            : (theme === 'dark' ? 'text-green-400' : 'text-green-600')
                    }`}>
                        {statistics.triggerEvents}
                    </div>
                    <div className={`text-xs ${
                        theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                        觸發事件
                    </div>
                </div>
                
                <div className="text-center">
                    <div className={`text-2xl font-bold ${
                        theme === 'dark' ? 'text-yellow-400' : 'text-yellow-600'
                    }`}>
                        {statistics.avgSignalCompensation.toFixed(1)}
                    </div>
                    <div className={`text-xs ${
                        theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                        平均信號補償 (dB)
                    </div>
                </div>
                
                <div className="text-center">
                    <div className={`text-2xl font-bold ${
                        theme === 'dark' ? 'text-purple-400' : 'text-purple-600'
                    }`}>
                        {(statistics.avgPositionCompensation / 1000).toFixed(2)}
                    </div>
                    <div className={`text-xs ${
                        theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                        平均位置補償 (km)
                    </div>
                </div>
                
                <div className="text-center">
                    <div className={`text-sm font-bold ${
                        theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                        {statistics.currentNeighborId}
                    </div>
                    <div className={`text-xs ${
                        theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                        當前鄰居衛星
                    </div>
                </div>
            </div>

            {/* 圖表區域 */}
            <div className="h-96 w-full">
                {chartData ? (
                    <Line data={chartData} options={chartOptions} />
                ) : (
                    <div className={`flex items-center justify-center h-full ${
                        theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                        {isLoading ? (
                            <div className="flex items-center gap-2">
                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-current"></div>
                                <span>載入 A4 測量數據...</span>
                            </div>
                        ) : (
                            <div className="text-center">
                                <div className="text-4xl mb-2">📡</div>
                                <div>等待 A4 測量數據</div>
                                <div className="text-sm mt-1">
                                    確保 UE 位置和 A4 參數已配置
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* 控制按鈕 */}
            <div className="flex justify-center gap-2">
                <button
                    onClick={clearData}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        theme === 'dark'
                            ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                            : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                    }`}
                >
                    清除數據
                </button>
                
                <div className={`px-3 py-2 rounded-lg text-sm ${
                    isActive
                        ? (theme === 'dark' ? 'bg-green-900/30 text-green-400' : 'bg-green-100 text-green-700')
                        : (theme === 'dark' ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-600')
                }`}>
                    {isActive ? '🟢 實時監測中' : '⏸️ 已暫停'}
                </div>
                
                {isLoading && (
                    <div className={`px-3 py-2 rounded-lg text-sm ${
                        theme === 'dark' ? 'bg-blue-900/30 text-blue-400' : 'bg-blue-100 text-blue-700'
                    }`}>
                        🔄 更新中...
                    </div>
                )}
            </div>
        </div>
    )
}

export default EnhancedA4Chart