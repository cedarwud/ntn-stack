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
    // 可選的時間進度顯示（用於靜態標記）
    highlightTime?: number
    // 觸發區間顯示選項
    showTriggerIndicator?: 'none' | 'top-bar' | 'bottom-bar'
    // 數據採樣間隔（秒）
    sampleIntervalSeconds?: number
}

export const RealD2Chart: React.FC<RealD2ChartProps> = ({
    data,
    thresh1,
    thresh2,
    hysteresis,
    showThresholdLines = true,
    isDarkTheme = true,
    width,
    height,
    className = '',
    onDataPointClick,
    onChartReady,
    highlightTime,
    showTriggerIndicator = 'none',
    sampleIntervalSeconds = 10, // 預設10秒間隔
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

    // 計算觸發區間（僅在需要顯示時計算）
    const triggerIntervals = useMemo(() => {
        if (!data || data.length === 0 || showTriggerIndicator === 'none')
            return []

        const intervals: Array<{ startTime: number; endTime: number }> = []
        let currentInterval: { startTime: number } | null = null

        data.forEach((point, index) => {
            const time = index * sampleIntervalSeconds // 使用動態採樣間隔

            if (point.triggerConditionMet && !currentInterval) {
                currentInterval = { startTime: time }
            } else if (!point.triggerConditionMet && currentInterval) {
                intervals.push({
                    startTime: currentInterval.startTime,
                    endTime: (index - 1) * 10,
                })
                currentInterval = null
            }
        })

        // 如果數據結束時仍在觸發狀態
        if (currentInterval) {
            intervals.push({
                startTime: currentInterval.startTime,
                endTime: (data.length - 1) * 10,
            })
        }

        return intervals
    }, [data, showTriggerIndicator])

    // 處理圖表數據
    const chartData: ChartData<'line'> = useMemo(() => {
        if (!data || data.length === 0) {
            return {
                labels: [],
                datasets: [],
            }
        }

        // 生成時間標籤（相對時間，秒）
        const labels = data.map((_, index) => index * sampleIntervalSeconds) // 使用動態採樣間隔

        // 衛星距離數據集
        const satelliteDistanceData = data.map(
            (point) => point.satelliteDistance / 1000
        ) // 轉換為 km

        // 地面距離數據集
        const groundDistanceData = data.map(
            (point) => point.groundDistance / 1000
        ) // 轉換為 km

        return {
            labels,
            datasets: [
                {
                    label: '衛星距離 (UE ↔ 衛星)',
                    data: satelliteDistanceData,
                    borderColor: theme.satelliteLine,
                    backgroundColor: `${theme.satelliteLine}10`,
                    borderWidth: 2.5, // 增加線條粗細
                    pointRadius: 1, // 顯示小點以保持數據真實性
                    pointHoverRadius: 5,
                    fill: false,
                    tension: 0.2, // 降低平滑度以保持真實數據特徵
                    yAxisID: 'y-left',
                },
                {
                    label: '地面距離 (UE ↔ 固定參考位置)',
                    data: groundDistanceData,
                    borderColor: theme.groundLine,
                    backgroundColor: `${theme.groundLine}10`,
                    borderWidth: 2.5, // 增加線條粗細
                    pointRadius: 1, // 顯示小點
                    pointHoverRadius: 5,
                    fill: false,
                    tension: 0.3, // 地面距離可以更平滑（因為是人工生成的）
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
            resizeDelay: 0,
            interaction: {
                mode: 'index' as const,
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Event D2: 移動參考位置距離事件 (3GPP TS 38.331) - 真實數據動態縮放',
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
                                    dataPoint?.satelliteInfo?.name || dataPoint?.referenceSatellite || 'Unknown'
                                }`,
                                `NORAD ID: ${
                                    dataPoint?.satelliteInfo?.noradId || 'N/A'
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
                            if (dataPoint?.satelliteInfo?.latitude != null) {
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
                                  scaleID: 'y-left',
                                  value: thresh1 / 1000, // 轉換為 km
                                  borderColor: '#DC3545', // 紅色門檻線1
                                  borderWidth: 3,
                                  borderDash: [8, 4],
                                  label: {
                                      content: `Thresh1: ${(
                                          thresh1 / 1000
                                      ).toFixed(0)}km (衛星)`,
                                      enabled: true,
                                      position: 'start' as const,
                                      backgroundColor: '#DC3545',
                                      color: 'white',
                                      font: { size: 11, weight: 'bold' },
                                  },
                              },
                              thresh2Line: {
                                  type: 'line' as const,
                                  scaleID: 'y-right',
                                  value: thresh2 / 1000, // 轉換為 km
                                  borderColor: '#007BFF', // 藍色門檻線2
                                  borderWidth: 3,
                                  borderDash: [8, 4],
                                  label: {
                                      content: `Thresh2: ${(
                                          thresh2 / 1000
                                      ).toFixed(1)}km (地面)`,
                                      enabled: true,
                                      position: 'end' as const,
                                      backgroundColor: '#007BFF',
                                      color: 'white',
                                      font: { size: 11, weight: 'bold' },
                                  },
                              },
                              // 遲滯線段 - 衛星距離
                              hystThresh1Upper: {
                                  type: 'line' as const,
                                  scaleID: 'y-left',
                                  value: (thresh1 + hysteresis) / 1000,
                                  borderColor: '#DC3545',
                                  borderWidth: 1,
                                  borderDash: [3, 3],
                                  label: {
                                      content: `+Hys: ${(
                                          (thresh1 + hysteresis) /
                                          1000
                                      ).toFixed(0)}km`,
                                      enabled: true,
                                      position: 'start' as const,
                                      backgroundColor: 'rgba(220, 53, 69, 0.7)',
                                      color: 'white',
                                      font: { size: 9 },
                                  },
                              },
                              hystThresh1Lower: {
                                  type: 'line' as const,
                                  scaleID: 'y-left',
                                  value: (thresh1 - hysteresis) / 1000,
                                  borderColor: '#DC3545',
                                  borderWidth: 1,
                                  borderDash: [3, 3],
                                  label: {
                                      content: `-Hys: ${(
                                          (thresh1 - hysteresis) /
                                          1000
                                      ).toFixed(0)}km`,
                                      enabled: true,
                                      position: 'start' as const,
                                      backgroundColor: 'rgba(220, 53, 69, 0.7)',
                                      color: 'white',
                                      font: { size: 9 },
                                  },
                              },
                              // 遲滯線段 - 地面距離
                              hystThresh2Upper: {
                                  type: 'line' as const,
                                  scaleID: 'y-right',
                                  value: (thresh2 + hysteresis) / 1000,
                                  borderColor: '#007BFF',
                                  borderWidth: 1,
                                  borderDash: [3, 3],
                                  label: {
                                      content: `+Hys: ${(
                                          (thresh2 + hysteresis) /
                                          1000
                                      ).toFixed(2)}km`,
                                      enabled: true,
                                      position: 'end' as const,
                                      backgroundColor: 'rgba(0, 123, 255, 0.7)',
                                      color: 'white',
                                      font: { size: 9 },
                                  },
                              },
                              hystThresh2Lower: {
                                  type: 'line' as const,
                                  scaleID: 'y-right',
                                  value: (thresh2 - hysteresis) / 1000,
                                  borderColor: '#007BFF',
                                  borderWidth: 1,
                                  borderDash: [3, 3],
                                  label: {
                                      content: `-Hys: ${(
                                          (thresh2 - hysteresis) /
                                          1000
                                      ).toFixed(2)}km`,
                                      enabled: true,
                                      position: 'end' as const,
                                      backgroundColor: 'rgba(0, 123, 255, 0.7)',
                                      color: 'white',
                                      font: { size: 9 },
                                  },
                              },
                              // 可選的時間高亮線
                              ...(highlightTime !== undefined && {
                                  highlightTimeLine: {
                                      type: 'line' as const,
                                      scaleID: 'x',
                                      value: highlightTime,
                                      borderColor: '#ff6b35',
                                      borderWidth: 2,
                                      borderDash: [5, 5],
                                      label: {
                                          content: `${highlightTime.toFixed(
                                              1
                                          )}s`,
                                          enabled: true,
                                          position: 'top' as const,
                                          backgroundColor:
                                              'rgba(255, 107, 53, 0.8)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                              }),
                              // 可選的觸發區間指示器
                              ...(showTriggerIndicator !== 'none' &&
                                  Object.fromEntries(
                                      triggerIntervals.map(
                                          (interval, index) => {
                                              const yPosition =
                                                  showTriggerIndicator ===
                                                  'top-bar'
                                                      ? {
                                                            yMin:
                                                                yAxisRanges
                                                                    .satelliteRange
                                                                    .max * 0.92,
                                                            yMax:
                                                                yAxisRanges
                                                                    .satelliteRange
                                                                    .max * 0.98,
                                                        }
                                                      : {
                                                            yMin:
                                                                yAxisRanges
                                                                    .satelliteRange
                                                                    .min * 1.02,
                                                            yMax:
                                                                yAxisRanges
                                                                    .satelliteRange
                                                                    .min * 1.08,
                                                        }

                                              return [
                                                  `triggerBar_${index}`,
                                                  {
                                                      type: 'box' as const,
                                                      xMin: interval.startTime,
                                                      xMax: interval.endTime,
                                                      xScaleID: 'x',
                                                      yScaleID: 'y-left',
                                                      ...yPosition,
                                                      backgroundColor:
                                                          'rgba(40, 167, 69, 0.4)',
                                                      borderColor:
                                                          'rgba(40, 167, 69, 0.8)',
                                                      borderWidth: 1,
                                                      label: {
                                                          content: `D2 Active`,
                                                          enabled: true,
                                                          position:
                                                              'center' as const,
                                                          backgroundColor:
                                                              'rgba(40, 167, 69, 0.9)',
                                                          color: 'white',
                                                          font: {
                                                              size: 9,
                                                              weight: 'bold',
                                                          },
                                                      },
                                                  },
                                              ]
                                          }
                                      )
                                  )),
                          },
                      }
                    : {},
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
            showTriggerIndicator,
            thresh1,
            thresh2,
            hysteresis,
            yAxisRanges,
            triggerIntervals,
            highlightTime,
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
                    width: width ? `${width}px` : '100%',
                    height: height ? `${height}px` : '100%',
                    minHeight: '400px', // 確保空狀態也有足夠高度
                    backgroundColor: theme.background,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: theme.text,
                    fontSize: '16px',
                    boxSizing: 'border-box',
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
                width: width ? `${width}px` : '100%',
                height: height ? `${height}px` : '100%',
                minHeight: '400px', // 確保空圖表也有最小高度
                backgroundColor: theme.background,
                padding: '10px',
                borderRadius: '8px',
                boxSizing: 'border-box',
                position: 'relative',
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
