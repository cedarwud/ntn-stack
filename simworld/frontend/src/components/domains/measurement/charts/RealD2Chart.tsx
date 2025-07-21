/**
 * RealD2Chart - 純真實數據 D2 圖表組件
 *
 * 職責：
 * - 專門渲染基於真實 TLE 數據的 D2 測量事件圖表
 * - 使用 Chart.js 進行高性能圖表渲染
 * - 支援動態座標軸調整以適應真實數據範圍
 * - 符合 IEEE 論文研究等級的數據真實性要求
 *
 * 不負責：
 * - 數據獲取（由父組件處理）
 * - 參數控制（由父組件處理）
 * - 模式切換（由父組件處理）
 */

import React, { useRef, useEffect, useMemo, useCallback } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ChartOptions,
    ChartData,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import annotationPlugin from 'chartjs-plugin-annotation'

// 註冊 Chart.js 組件
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    annotationPlugin
)

// 真實 D2 數據點接口
export interface RealD2DataPoint {
    timestamp: string
    satelliteDistance: number // 米
    groundDistance: number // 米
    satelliteInfo: {
        noradId: number
        name: string
        latitude: number
        longitude: number
        altitude: number
    }
    triggerConditionMet: boolean
    d2EventDetails: {
        thresh1: number
        thresh2: number
        hysteresis: number
        enteringCondition: boolean
        leavingCondition: boolean
    }
}

// 組件 Props 接口
export interface RealD2ChartProps {
    data: RealD2DataPoint[]
    thresh1: number
    thresh2: number
    hysteresis: number
    showThresholdLines?: boolean
    isDarkTheme?: boolean
    width?: number
    height?: number
    className?: string
    onDataPointClick?: (dataPoint: RealD2DataPoint, index: number) => void
    onChartReady?: (chart: ChartJS) => void
}

export const RealD2Chart: React.FC<RealD2ChartProps> = ({
    data,
    thresh1,
    thresh2,
    hysteresis,
    showThresholdLines = true,
    isDarkTheme = true,
    width = 1000,
    height = 600,
    className = '',
    onDataPointClick,
    onChartReady,
}) => {
    const chartRef = useRef<ChartJS | null>(null)

    // 主題配置
    const theme = useMemo(
        () => ({
            background: isDarkTheme ? '#1a1a1a' : '#ffffff',
            text: isDarkTheme ? '#ffffff' : '#333333',
            grid: isDarkTheme ? '#374151' : '#e5e7eb',
            satelliteLine: '#28a745', // 綠色 - 衛星距離
            groundLine: '#fd7e14', // 橙色 - 地面距離
            thresh1Line: '#dc3545', // 紅色 - 閾值1
            thresh2Line: '#ffc107', // 黃色 - 閾值2
            triggerPoint: '#ff0000', // 紅色 - 觸發點
        }),
        [isDarkTheme]
    )

    // 處理圖表數據
    const chartData: ChartData<'line'> = useMemo(() => {
        if (!data || data.length === 0) {
            return {
                labels: [],
                datasets: [],
            }
        }

        // 生成時間標籤（相對時間，秒）
        const labels = data.map((_, index) => index * 10) // 假設每10秒一個數據點

        // 衛星距離數據集
        const satelliteDistanceData = data.map(
            (point) => point.satelliteDistance / 1000
        ) // 轉換為 km

        // 地面距離數據集
        const groundDistanceData = data.map(
            (point) => point.groundDistance / 1000
        ) // 轉換為 km

        // 觸發點標記 - 分別顯示在兩條線上
        const satelliteTriggerPoints = data.map((point, index) => {
            if (point.triggerConditionMet) {
                return point.satelliteDistance / 1000 // 顯示在衛星距離線上
            }
            return null
        })

        const groundTriggerPoints = data.map((point, index) => {
            if (point.triggerConditionMet) {
                return point.groundDistance / 1000 // 顯示在地面距離線上
            }
            return null
        })

        return {
            labels,
            datasets: [
                {
                    label: '衛星距離 (UE ↔ 移動參考位置) ⚡',
                    data: satelliteDistanceData,
                    borderColor: theme.satelliteLine,
                    backgroundColor: `${theme.satelliteLine}20`,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: false,
                    tension: 0.1,
                    yAxisID: 'y-left',
                },
                {
                    label: '地面距離 (UE ↔ 固定參考位置) ⚡',
                    data: groundDistanceData,
                    borderColor: theme.groundLine,
                    backgroundColor: `${theme.groundLine}20`,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: false,
                    tension: 0.1,
                    yAxisID: 'y-right',
                },
                {
                    label: 'D2 事件觸發點 (衛星)',
                    data: satelliteTriggerPoints,
                    borderColor: theme.triggerPoint,
                    backgroundColor: theme.triggerPoint,
                    borderWidth: 0,
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    showLine: false,
                    yAxisID: 'y-left',
                },
                {
                    label: 'D2 事件觸發點 (地面)',
                    data: groundTriggerPoints,
                    borderColor: theme.triggerPoint,
                    backgroundColor: `${theme.triggerPoint}80`, // 半透明
                    borderWidth: 0,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    showLine: false,
                    yAxisID: 'y-right',
                },
            ],
        }
    }, [data, theme])

    // 計算動態 Y 軸範圍
    const yAxisRanges = useMemo(() => {
        if (!data || data.length === 0) {
            return {
                satelliteRange: { min: 400, max: 800 },
                groundRange: { min: 0, max: 100 },
            }
        }

        const satelliteDistances = data.map((d) => d.satelliteDistance / 1000)
        const groundDistances = data.map((d) => d.groundDistance / 1000)

        const satelliteMin = Math.min(...satelliteDistances)
        const satelliteMax = Math.max(...satelliteDistances)
        const groundMin = Math.min(...groundDistances)
        const groundMax = Math.max(...groundDistances)

        // 添加緩衝區
        const satelliteBuffer = (satelliteMax - satelliteMin) * 0.1
        let groundBuffer = (groundMax - groundMin) * 0.1

        // 如果地面距離範圍太小（所有值相同），使用固定緩衝區
        if (groundBuffer < 1) {
            // 小於 1 公里
            groundBuffer = Math.max(1, groundMax * 0.1) // 至少 1 公里或 10% 的緩衝區
        }

        const result = {
            satelliteRange: {
                min: Math.max(0, satelliteMin - satelliteBuffer),
                max: satelliteMax + satelliteBuffer,
            },
            groundRange: {
                min: Math.max(0, groundMin - groundBuffer),
                max: groundMax + groundBuffer,
            },
        }

        // 調試完成，移除日誌以提高性能

        return result
    }, [data])

    // 圖表配置 - 移到條件渲染之前
    const chartOptions: ChartOptions<'line'> = useMemo(
        () => ({
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index' as const,
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Event D2: 移動參考位置距離事件 (真實 TLE 數據)',
                    font: {
                        size: 16,
                        weight: 'bold',
                    },
                    color: theme.text,
                },
                legend: {
                    display: true,
                    position: 'top' as const,
                    labels: {
                        color: theme.text,
                        usePointStyle: true,
                        padding: 20,
                    },
                },
                tooltip: {
                    backgroundColor: isDarkTheme
                        ? 'rgba(33, 37, 41, 0.95)'
                        : 'rgba(255, 255, 255, 0.95)',
                    titleColor: theme.text,
                    bodyColor: theme.text,
                    borderColor: theme.grid,
                    borderWidth: 1,
                    callbacks: {
                        title: (context) => {
                            const dataIndex = context[0].dataIndex
                            const dataPoint = data[dataIndex]
                            return [
                                `時間: ${context[0].label}s`,
                                `衛星: ${
                                    dataPoint?.satelliteInfo.name || 'Unknown'
                                }`,
                                `NORAD ID: ${
                                    dataPoint?.satelliteInfo.noradId || 'N/A'
                                }`,
                            ]
                        },
                        label: (context) => {
                            const dataIndex = context.dataIndex
                            const dataPoint = data[dataIndex]
                            const dataset = context.dataset.label || ''
                            const value = context.parsed.y

                            if (dataset.includes('觸發點')) {
                                return `${dataset}: D2 事件已觸發`
                            }

                            return [
                                `${dataset}: ${value.toFixed(1)} km`,
                                `觸發狀態: ${
                                    dataPoint?.triggerConditionMet
                                        ? '已觸發'
                                        : '未觸發'
                                }`,
                            ]
                        },
                        footer: (context) => {
                            const dataIndex = context[0].dataIndex
                            const dataPoint = data[dataIndex]
                            if (dataPoint) {
                                return [
                                    '--- 衛星位置 ---',
                                    `緯度: ${dataPoint.satelliteInfo.latitude.toFixed(
                                        4
                                    )}°`,
                                    `經度: ${dataPoint.satelliteInfo.longitude.toFixed(
                                        4
                                    )}°`,
                                    `高度: ${(
                                        dataPoint.satelliteInfo.altitude / 1000
                                    ).toFixed(1)} km`,
                                ]
                            }
                            return []
                        },
                    },
                },
                annotation: showThresholdLines
                    ? {
                          annotations: {
                              thresh1Line: {
                                  type: 'line' as const,
                                  yMin: thresh1 / 1000,
                                  yMax: thresh1 / 1000,
                                  borderColor: theme.thresh1Line,
                                  borderWidth: 2,
                                  borderDash: [5, 5],
                                  label: {
                                      display: true,
                                      content: `閾值1: ${(
                                          thresh1 / 1000
                                      ).toFixed(0)} km`,
                                      position: 'end' as const,
                                      backgroundColor: theme.thresh1Line,
                                      color: 'white',
                                  },
                                  scaleID: 'y-left',
                              },
                              thresh2Line: {
                                  type: 'line' as const,
                                  yMin: thresh2 / 1000,
                                  yMax: thresh2 / 1000,
                                  borderColor: theme.thresh2Line,
                                  borderWidth: 2,
                                  borderDash: [5, 5],
                                  label: {
                                      display: true,
                                      content: `閾值2: ${(
                                          thresh2 / 1000
                                      ).toFixed(0)} km`,
                                      position: 'end' as const,
                                      backgroundColor: theme.thresh2Line,
                                      color: 'black',
                                  },
                                  scaleID: 'y-right',
                              },
                          },
                      }
                    : undefined,
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '時間 (秒)',
                        color: theme.text,
                        font: {
                            size: 14,
                            weight: 'bold',
                        },
                    },
                    grid: {
                        color: theme.grid,
                        lineWidth: 1,
                    },
                    ticks: {
                        color: theme.text,
                        stepSize: 30, // 每30秒一個刻度
                    },
                },
                'y-left': {
                    type: 'linear' as const,
                    position: 'left' as const,
                    title: {
                        display: true,
                        text: '衛星距離 (km) - 真實數據',
                        color: theme.satelliteLine,
                        font: {
                            size: 14,
                            weight: 'bold',
                        },
                    },
                    grid: {
                        color: theme.grid,
                        lineWidth: 1,
                    },
                    ticks: {
                        color: theme.satelliteLine,
                        callback: (value) => `${Number(value).toFixed(0)}`,
                    },
                    min: yAxisRanges.satelliteRange.min,
                    max: yAxisRanges.satelliteRange.max,
                },
                'y-right': {
                    type: 'linear' as const,
                    position: 'right' as const,
                    title: {
                        display: true,
                        text: '地面距離 (km) - 真實數據',
                        color: theme.groundLine,
                        font: {
                            size: 14,
                            weight: 'bold',
                        },
                    },
                    grid: {
                        display: false, // 避免網格線重疊
                    },
                    ticks: {
                        color: theme.groundLine,
                        callback: (value) => `${Number(value).toFixed(1)}`,
                    },
                    min: yAxisRanges.groundRange.min,
                    max: yAxisRanges.groundRange.max,
                },
            },
            onClick: (event, elements) => {
                if (elements.length > 0 && onDataPointClick) {
                    const element = elements[0]
                    const dataIndex = element.index
                    const dataPoint = data[dataIndex]
                    if (dataPoint) {
                        onDataPointClick(dataPoint, dataIndex)
                    }
                }
            },
        }),
        [
            theme,
            isDarkTheme,
            showThresholdLines,
            thresh1,
            thresh2,
            yAxisRanges,
            data,
            onDataPointClick,
        ]
    )

    // 圖表準備回調
    const handleChartReady = useCallback(
        (chart: ChartJS) => {
            chartRef.current = chart
            if (onChartReady) {
                onChartReady(chart)
            }
        },
        [onChartReady]
    )

    // 如果沒有數據，顯示載入狀態
    if (!data || data.length === 0) {
        return (
            <div
                className={`real-d2-chart ${className}`}
                style={{
                    width,
                    height,
                    backgroundColor: theme.background,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: theme.text,
                    fontSize: '16px',
                }}
            >
                正在載入真實衛星數據...
            </div>
        )
    }

    return (
        <div
            className={`real-d2-chart ${className}`}
            style={{
                width,
                height,
                backgroundColor: theme.background,
                padding: '10px',
                borderRadius: '8px',
            }}
        >
            <Line
                ref={handleChartReady}
                data={chartData}
                options={chartOptions}
            />
        </div>
    )
}

export default RealD2Chart
