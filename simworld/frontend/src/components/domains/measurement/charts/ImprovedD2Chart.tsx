/**
 * ImprovedD2Chart - 改進版 D2 事件圖表
 *
 * 改進重點：
 * 1. 數據平滑化處理，突出換手觸發模式
 * 2. 清晰的觸發時機標示
 * 3. 更好的視覺分離和色彩設計
 * 4. 支援與立體圖的時間同步
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

// 改進的 D2 數據點接口
export interface ImprovedD2DataPoint {
    timestamp: string
    satelliteDistance: number // 米
    groundDistance: number // 米
    smoothedSatelliteDistance: number // 平滑後的衛星距離
    smoothedGroundDistance: number // 平滑後的地面距離
    triggerConditionMet: boolean
    d2EventDetails: {
        thresh1: number
        thresh2: number
        hysteresis: number
        enteringCondition: boolean
        leavingCondition: boolean
        triggerProbability: number // 0-1, 觸發可能性
    }
    satelliteInfo: {
        noradId: number
        name: string
        latitude: number
        longitude: number
        altitude: number
    }
}

// 數據平滑化工具
export class DataSmoothingService {
    /**
     * 移動平均平滑化 - 適用於消除SGP4高頻振蕩
     */
    static movingAverage(data: number[], windowSize: number = 5): number[] {
        if (data.length < windowSize) return data

        const smoothed = []
        for (let i = 0; i < data.length; i++) {
            const start = Math.max(0, i - Math.floor(windowSize / 2))
            const end = Math.min(data.length, start + windowSize)
            const window = data.slice(start, end)
            const average =
                window.reduce((sum, val) => sum + val, 0) / window.length
            smoothed.push(average)
        }
        return smoothed
    }

    /**
     * 指數平滑 - 保留趨勢，減少噪聲
     */
    static exponentialSmoothing(data: number[], alpha: number = 0.3): number[] {
        if (data.length === 0) return data

        const smoothed = [data[0]]
        for (let i = 1; i < data.length; i++) {
            const smoothedValue =
                alpha * data[i] + (1 - alpha) * smoothed[i - 1]
            smoothed.push(smoothedValue)
        }
        return smoothed
    }

    /**
     * 觸發區間識別 - 基於平滑數據識別清晰的觸發模式
     */
    static identifyTriggerPatterns(
        smoothedSatDist: number[],
        smoothedGroundDist: number[],
        thresh1: number,
        thresh2: number,
        hysteresis: number,
        sampleInterval: number = 10
    ): Array<{
        startTime: number
        endTime: number
        triggerStrength: number // 0-1, 觸發強度
        handoverLikelihood: 'high' | 'medium' | 'low'
    }> {
        const patterns = []
        let currentPattern: any = null

        for (let i = 0; i < smoothedSatDist.length; i++) {
            const satDist = smoothedSatDist[i]
            const groundDist = smoothedGroundDist[i]
            const time = i * sampleInterval

            // D2 觸發條件:
            // Condition 1: Ml1 - Hys > Thresh1 (服務衛星距離 > 閾值1)
            // Condition 2: Ml2 + Hys < Thresh2 (目標衛星距離 < 閾值2)
            const condition1 = satDist - hysteresis > thresh1
            const condition2 = groundDist + hysteresis < thresh2
            const isTriggered = condition1 && condition2

            // 計算觸發強度 (距離閾值越遠，觸發越強)
            const cond1Strength = condition1
                ? Math.min(1, (satDist - thresh1) / (thresh1 * 0.1))
                : 0
            const cond2Strength = condition2
                ? Math.min(1, (thresh2 - groundDist) / (thresh2 * 0.1))
                : 0
            const triggerStrength = Math.min(cond1Strength, cond2Strength)

            if (isTriggered && !currentPattern) {
                // 開始新的觸發模式
                currentPattern = {
                    startTime: time,
                    endTime: time,
                    triggerStrength: triggerStrength,
                    peakStrength: triggerStrength,
                }
            } else if (isTriggered && currentPattern) {
                // 延續觸發模式
                currentPattern.endTime = time
                currentPattern.peakStrength = Math.max(
                    currentPattern.peakStrength,
                    triggerStrength
                )
            } else if (!isTriggered && currentPattern) {
                // 結束觸發模式
                const duration =
                    currentPattern.endTime - currentPattern.startTime
                currentPattern.handoverLikelihood =
                    currentPattern.peakStrength > 0.8 && duration > 30
                        ? 'high'
                        : currentPattern.peakStrength > 0.5 && duration > 15
                        ? 'medium'
                        : 'low'

                patterns.push(currentPattern)
                currentPattern = null
            }
        }

        // 處理最後的觸發模式
        if (currentPattern) {
            const duration = currentPattern.endTime - currentPattern.startTime
            currentPattern.handoverLikelihood =
                currentPattern.peakStrength > 0.8 && duration > 30
                    ? 'high'
                    : currentPattern.peakStrength > 0.5 && duration > 15
                    ? 'medium'
                    : 'low'
            patterns.push(currentPattern)
        }

        return patterns
    }
}

// 組件 Props 接口
export interface ImprovedD2ChartProps {
    data: ImprovedD2DataPoint[]
    thresh1: number
    thresh2: number
    hysteresis: number

    // 視覺選項
    showThresholdLines?: boolean
    showRawData?: boolean // 是否顯示原始高頻數據
    isDarkTheme?: boolean
    width?: number
    height?: number
    className?: string

    // 時間同步選項
    currentTime?: number // 當前時間點（秒），用於與立體圖同步
    onTimeChange?: (time: number) => void // 時間變化回調

    // 觸發分析選項
    highlightTriggerPatterns?: boolean
    showHandoverPrediction?: boolean

    // 數據處理選項
    smoothingWindowSize?: number // 平滑窗口大小
    smoothingAlpha?: number // 指數平滑參數

    // 回調函數
    onDataPointClick?: (dataPoint: ImprovedD2DataPoint, index: number) => void
    onChartReady?: (chart: ChartJS) => void
    onTriggerPatternDetected?: (patterns: any[]) => void
}

export const ImprovedD2Chart: React.FC<ImprovedD2ChartProps> = ({
    data,
    thresh1,
    thresh2,
    hysteresis,
    showThresholdLines = true,
    showRawData = false,
    isDarkTheme = true,
    width,
    height,
    className = '',
    currentTime,
    onTimeChange,
    highlightTriggerPatterns = true,
    _showHandoverPrediction = true,
    smoothingWindowSize = 5,
    smoothingAlpha = 0.3,
    onDataPointClick,
    onChartReady,
    onTriggerPatternDetected,
}) => {
    const chartRef = useRef<ChartJS | null>(null)

    // 主題配置 - 改進版色彩方案
    const theme = useMemo(
        () => ({
            background: isDarkTheme ? '#1a1a1a' : '#ffffff',
            text: isDarkTheme ? '#ffffff' : '#333333',
            grid: isDarkTheme ? '#374151' : '#e5e7eb',

            // 主要數據線 - 更清楚的色彩對比
            satelliteLine: '#00D2FF', // 亮藍色 - 衛星距離（平滑）
            groundLine: '#FF6B35', // 橙紅色 - 地面距離（平滑）

            // 原始數據線 - 透明度較低
            rawSatelliteLine: '#00D2FF40', // 半透明藍色
            rawGroundLine: '#FF6B3540', // 半透明橙色

            // 閾值線
            thresh1Line: '#DC3545', // 紅色
            thresh2Line: '#28A745', // 綠色

            // 觸發模式標示
            triggerHigh: '#FF0066', // 高可能性
            triggerMedium: '#FF9900', // 中等可能性
            triggerLow: '#FFCC00', // 低可能性

            // 時間同步標示
            currentTimeLine: '#FF6B35',
        }),
        [isDarkTheme]
    )

    // 數據平滑化處理
    const processedData = useMemo(() => {
        if (!data || data.length === 0)
            return { smoothedData: [], triggerPatterns: [] }

        // 提取原始距離數據
        const satelliteDistances = data.map((d) => d.satelliteDistance)
        const groundDistances = data.map((d) => d.groundDistance)

        // 應用平滑化算法
        const smoothedSatelliteDistances =
            DataSmoothingService.exponentialSmoothing(
                DataSmoothingService.movingAverage(
                    satelliteDistances,
                    smoothingWindowSize
                ),
                smoothingAlpha
            )
        const smoothedGroundDistances =
            DataSmoothingService.exponentialSmoothing(
                DataSmoothingService.movingAverage(
                    groundDistances,
                    smoothingWindowSize
                ),
                smoothingAlpha
            )

        // 識別觸發模式
        const triggerPatterns = DataSmoothingService.identifyTriggerPatterns(
            smoothedSatelliteDistances,
            smoothedGroundDistances,
            thresh1,
            thresh2,
            hysteresis,
            10 // 10秒採樣間隔
        )

        // 構建處理後的數據
        const smoothedData = data.map((point, index) => ({
            ...point,
            smoothedSatelliteDistance: smoothedSatelliteDistances[index],
            smoothedGroundDistance: smoothedGroundDistances[index],
        }))

        return { smoothedData, triggerPatterns }
    }, [
        data,
        smoothingWindowSize,
        smoothingAlpha,
        thresh1,
        thresh2,
        hysteresis,
    ])

    // 觸發模式變化時的回調
    useEffect(() => {
        if (
            onTriggerPatternDetected &&
            processedData.triggerPatterns.length > 0
        ) {
            onTriggerPatternDetected(processedData.triggerPatterns)
        }
    }, [processedData.triggerPatterns, onTriggerPatternDetected])

    // 圖表數據構建
    const chartData: ChartData<'line'> = useMemo(() => {
        if (
            !processedData.smoothedData ||
            processedData.smoothedData.length === 0
        ) {
            return { labels: [], datasets: [] }
        }

        const labels = processedData.smoothedData.map((_, index) => index * 10) // 10秒間隔
        const datasets = []

        // 平滑後的衛星距離（主要線條）
        datasets.push({
            label: '衛星距離 (平滑)',
            data: processedData.smoothedData.map(
                (d) => d.smoothedSatelliteDistance / 1000
            ),
            borderColor: theme.satelliteLine,
            backgroundColor: `${theme.satelliteLine}20`,
            borderWidth: 3,
            pointRadius: 0,
            pointHoverRadius: 6,
            fill: false,
            tension: 0.4,
            yAxisID: 'y-satellite',
        })

        // 平滑後的地面距離（主要線條）
        datasets.push({
            label: '地面距離 (平滑)',
            data: processedData.smoothedData.map(
                (d) => d.smoothedGroundDistance / 1000
            ),
            borderColor: theme.groundLine,
            backgroundColor: `${theme.groundLine}20`,
            borderWidth: 3,
            pointRadius: 0,
            pointHoverRadius: 6,
            fill: false,
            tension: 0.4,
            yAxisID: 'y-ground',
        })

        // 可選：顯示原始高頻數據
        if (showRawData) {
            datasets.push({
                label: '衛星距離 (原始)',
                data: processedData.smoothedData.map(
                    (d) => d.satelliteDistance / 1000
                ),
                borderColor: theme.rawSatelliteLine,
                backgroundColor: 'transparent',
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
                tension: 0,
                yAxisID: 'y-satellite',
            })

            datasets.push({
                label: '地面距離 (原始)',
                data: processedData.smoothedData.map(
                    (d) => d.groundDistance / 1000
                ),
                borderColor: theme.rawGroundLine,
                backgroundColor: 'transparent',
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
                tension: 0,
                yAxisID: 'y-ground',
            })
        }

        return { labels, datasets }
    }, [processedData, theme, showRawData])

    // 計算動態軸範圍
    const yAxisRanges = useMemo(() => {
        if (
            !processedData.smoothedData ||
            processedData.smoothedData.length === 0
        ) {
            return {
                satelliteRange: { min: 400, max: 800 },
                groundRange: { min: 0, max: 100 },
            }
        }

        const satDistances = processedData.smoothedData.map(
            (d) => d.smoothedSatelliteDistance / 1000
        )
        const groundDistances = processedData.smoothedData.map(
            (d) => d.smoothedGroundDistance / 1000
        )

        const satMin = Math.min(...satDistances)
        const satMax = Math.max(...satDistances)
        const groundMin = Math.min(...groundDistances)
        const groundMax = Math.max(...groundDistances)

        // 增加適當的緩衝區
        const satBuffer = (satMax - satMin) * 0.2 || 50
        const groundBuffer = (groundMax - groundMin) * 0.2 || 20

        return {
            satelliteRange: {
                min: Math.max(0, satMin - satBuffer),
                max: satMax + satBuffer,
            },
            groundRange: {
                min: Math.max(0, groundMin - groundBuffer),
                max: groundMax + groundBuffer,
            },
        }
    }, [processedData])

    // 圖表配置
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
                    text: 'D2事件分析 - 衛星換手觸發時機預測 (改進版)',
                    font: { size: 16, weight: 'bold' },
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
                            const dataPoint =
                                processedData.smoothedData[dataIndex]
                            return [
                                `時間: ${context[0].label}s`,
                                `衛星: ${
                                    dataPoint?.satelliteInfo?.name || 'Unknown'
                                }`,
                            ]
                        },
                        label: (context) => {
                            const dataIndex = context.dataIndex
                            const dataPoint =
                                processedData.smoothedData[dataIndex]
                            const dataset = context.dataset.label || ''
                            const value = context.parsed.y

                            return [
                                `${dataset}: ${value.toFixed(1)} km`,
                                `觸發狀態: ${
                                    dataPoint?.triggerConditionMet
                                        ? '✅ 已觸發'
                                        : '❌ 未觸發'
                                }`,
                            ]
                        },
                        afterBody: (context) => {
                            const dataIndex = context[0].dataIndex
                            const dataPoint =
                                processedData.smoothedData[dataIndex]

                            if (dataPoint?.triggerConditionMet) {
                                return [
                                    '--- D2 事件詳情 ---',
                                    `閾值1: ${(thresh1 / 1000).toFixed(0)} km`,
                                    `閾值2: ${(thresh2 / 1000).toFixed(1)} km`,
                                    `遲滯值: ${(hysteresis / 1000).toFixed(
                                        1
                                    )} km`,
                                ]
                            }
                            return []
                        },
                    },
                },
                annotation: showThresholdLines
                    ? {
                          annotations: {
                              // 閾值線
                              thresh1Line: {
                                  type: 'line' as const,
                                  scaleID: 'y-satellite',
                                  value: thresh1 / 1000,
                                  borderColor: theme.thresh1Line,
                                  borderWidth: 2,
                                  borderDash: [8, 4],
                                  label: {
                                      content: `閾值1: ${(
                                          thresh1 / 1000
                                      ).toFixed(0)}km`,
                                      enabled: true,
                                      position: 'start' as const,
                                      backgroundColor: theme.thresh1Line,
                                      color: 'white',
                                      font: { size: 11, weight: 'bold' },
                                  },
                              },
                              thresh2Line: {
                                  type: 'line' as const,
                                  scaleID: 'y-ground',
                                  value: thresh2 / 1000,
                                  borderColor: theme.thresh2Line,
                                  borderWidth: 2,
                                  borderDash: [8, 4],
                                  label: {
                                      content: `閾值2: ${(
                                          thresh2 / 1000
                                      ).toFixed(1)}km`,
                                      enabled: true,
                                      position: 'end' as const,
                                      backgroundColor: theme.thresh2Line,
                                      color: 'white',
                                      font: { size: 11, weight: 'bold' },
                                  },
                              },
                              // 當前時間線（與立體圖同步）
                              ...(currentTime !== undefined && {
                                  currentTimeLine: {
                                      type: 'line' as const,
                                      scaleID: 'x',
                                      value: currentTime,
                                      borderColor: theme.currentTimeLine,
                                      borderWidth: 3,
                                      label: {
                                          content: `當前: ${currentTime.toFixed(
                                              1
                                          )}s`,
                                          enabled: true,
                                          position: 'top' as const,
                                          backgroundColor:
                                              theme.currentTimeLine,
                                          color: 'white',
                                          font: { size: 10, weight: 'bold' },
                                      },
                                  },
                              }),
                              // 觸發模式區間標示
                              ...(highlightTriggerPatterns &&
                                  Object.fromEntries(
                                      processedData.triggerPatterns.map(
                                          (pattern, index) => [
                                              `triggerPattern_${index}`,
                                              {
                                                  type: 'box' as const,
                                                  xMin: pattern.startTime,
                                                  xMax: pattern.endTime,
                                                  xScaleID: 'x',
                                                  yScaleID: 'y-satellite',
                                                  yMin: yAxisRanges
                                                      .satelliteRange.min,
                                                  yMax:
                                                      yAxisRanges.satelliteRange
                                                          .min +
                                                      (yAxisRanges
                                                          .satelliteRange.max -
                                                          yAxisRanges
                                                              .satelliteRange
                                                              .min) *
                                                          0.1,
                                                  backgroundColor:
                                                      pattern.handoverLikelihood ===
                                                      'high'
                                                          ? `${theme.triggerHigh}40`
                                                          : pattern.handoverLikelihood ===
                                                            'medium'
                                                          ? `${theme.triggerMedium}40`
                                                          : `${theme.triggerLow}40`,
                                                  borderColor:
                                                      pattern.handoverLikelihood ===
                                                      'high'
                                                          ? theme.triggerHigh
                                                          : pattern.handoverLikelihood ===
                                                            'medium'
                                                          ? theme.triggerMedium
                                                          : theme.triggerLow,
                                                  borderWidth: 2,
                                                  label: {
                                                      content: `D2觸發 (${pattern.handoverLikelihood})`,
                                                      enabled: true,
                                                      position:
                                                          'center' as const,
                                                      backgroundColor:
                                                          pattern.handoverLikelihood ===
                                                          'high'
                                                              ? theme.triggerHigh
                                                              : pattern.handoverLikelihood ===
                                                                'medium'
                                                              ? theme.triggerMedium
                                                              : theme.triggerLow,
                                                      color: 'white',
                                                      font: {
                                                          size: 9,
                                                          weight: 'bold',
                                                      },
                                                  },
                                              },
                                          ]
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
                        text: '時間 (秒) - 與立體圖同步',
                        color: theme.text,
                        font: { size: 14, weight: 'bold' },
                    },
                    grid: { color: theme.grid },
                    ticks: {
                        color: theme.text,
                        stepSize: 30,
                    },
                },
                'y-satellite': {
                    type: 'linear' as const,
                    position: 'left' as const,
                    title: {
                        display: true,
                        text: '衛星距離 (km)',
                        color: theme.satelliteLine,
                        font: { size: 14, weight: 'bold' },
                    },
                    grid: { color: theme.grid },
                    ticks: {
                        color: theme.satelliteLine,
                        callback: (value) => `${Number(value).toFixed(0)}`,
                    },
                    min: yAxisRanges.satelliteRange.min,
                    max: yAxisRanges.satelliteRange.max,
                },
                'y-ground': {
                    type: 'linear' as const,
                    position: 'right' as const,
                    title: {
                        display: true,
                        text: '地面距離 (km)',
                        color: theme.groundLine,
                        font: { size: 14, weight: 'bold' },
                    },
                    grid: { display: false },
                    ticks: {
                        color: theme.groundLine,
                        callback: (value) => `${Number(value).toFixed(1)}`,
                    },
                    min: yAxisRanges.groundRange.min,
                    max: yAxisRanges.groundRange.max,
                },
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const element = elements[0]
                    const dataIndex = element.index
                    const clickedTime = dataIndex * 10 // 10秒間隔

                    // 觸發時間變化，實現與立體圖同步
                    if (onTimeChange) {
                        onTimeChange(clickedTime)
                    }

                    // 觸發數據點點擊事件
                    if (onDataPointClick) {
                        const dataPoint = processedData.smoothedData[dataIndex]
                        if (dataPoint) {
                            onDataPointClick(dataPoint, dataIndex)
                        }
                    }
                }
            },
        }),
        [
            theme,
            isDarkTheme,
            showThresholdLines,
            highlightTriggerPatterns,
            thresh1,
            thresh2,
            hysteresis,
            yAxisRanges,
            processedData,
            currentTime,
            onTimeChange,
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

    // 載入狀態
    if (!data || data.length === 0) {
        return (
            <div
                className={`improved-d2-chart ${className}`}
                style={{
                    width: width ? `${width}px` : '100%',
                    height: height ? `${height}px` : '100%',
                    minHeight: '400px',
                    backgroundColor: theme.background,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: theme.text,
                    fontSize: '16px',
                }}
            >
                🛰️ 正在載入改進版 D2 事件數據...
            </div>
        )
    }

    return (
        <div
            className={`improved-d2-chart ${className}`}
            style={{
                width: width ? `${width}px` : '100%',
                height: height ? `${height}px` : '100%',
                minHeight: '400px',
                backgroundColor: theme.background,
                padding: '15px',
                borderRadius: '12px',
                border: `2px solid ${theme.grid}`,
                position: 'relative',
            }}
        >
            {/* 控制面板 */}
            <div
                style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    display: 'flex',
                    gap: '10px',
                    zIndex: 10,
                }}
            >
                {/* 觸發模式統計 */}
                {processedData.triggerPatterns.length > 0 && (
                    <div
                        style={{
                            backgroundColor: isDarkTheme
                                ? '#2d3748'
                                : '#f7fafc',
                            color: theme.text,
                            padding: '8px 12px',
                            borderRadius: '6px',
                            fontSize: '12px',
                            border: `1px solid ${theme.grid}`,
                        }}
                    >
                        D2觸發次數: {processedData.triggerPatterns.length} |
                        高可能性:{' '}
                        {
                            processedData.triggerPatterns.filter(
                                (p) => p.handoverLikelihood === 'high'
                            ).length
                        }
                    </div>
                )}

                {/* 與立體圖同步指示器 */}
                {currentTime !== undefined && (
                    <div
                        style={{
                            backgroundColor: theme.currentTimeLine,
                            color: 'white',
                            padding: '6px 10px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 'bold',
                        }}
                    >
                        同步: {currentTime.toFixed(1)}s
                    </div>
                )}
            </div>

            {/* 主圖表 */}
            <Line
                ref={handleChartReady}
                data={chartData}
                options={chartOptions}
            />
        </div>
    )
}

export default ImprovedD2Chart
