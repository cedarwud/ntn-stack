/**
 * Pure D2 Chart Component
 * 基於 3GPP TS 38.331 Section 5.5.4.15a 實現
 * Event D2: 移動參考位置距離事件
 * 進入條件: Ml1 – Hys > Thresh1 AND Ml2 + Hys < Thresh2
 * 離開條件: Ml1 + Hys < Thresh1 OR Ml2 – Hys > Thresh2
 *
 * 與 D1 的差異:
 * - Ml1: UE 到 movingReferenceLocation 的距離（移動參考位置 - 衛星）
 * - Ml2: UE 到 referenceLocation 的距離（固定參考位置）
 */

import React, { useEffect, useRef, useMemo } from 'react'
import { Chart, registerables } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'

// 註冊 Chart.js 組件
Chart.register(...registerables, annotationPlugin)

// 增強的衛星軌道模擬 - 基於真實 LEO 衛星軌道參數
function _calculateAdvancedSatellitePosition(timeSeconds: number): {
    lat: number
    lon: number
    altitude: number
    velocity: number
} {
    const centerLat = 25.0478 // 台北101 緯度
    const centerLon = 121.5319 // 台北101 經度
    const orbitRadius = 0.5 // 軌道半徑（度）- 更真實的軌道範圍
    const orbitPeriod = 5400 // 軌道週期（90分鐘 = 5400秒）✅ 修正
    const orbitAltitude = 550000 // 軌道高度（公尺）- 典型 LEO 衛星

    // 計算角度位置（考慮地球自轉）
    const orbitalAngle = (timeSeconds / orbitPeriod) * 2 * Math.PI
    const earthRotationAngle = (timeSeconds / 86400) * 2 * Math.PI // 地球自轉

    // 計算衛星位置
    const satLat = centerLat + orbitRadius * Math.cos(orbitalAngle)
    const satLon =
        centerLon +
        orbitRadius * Math.sin(orbitalAngle) -
        (earthRotationAngle * 180) / Math.PI

    // 計算軌道速度 (km/s)
    const orbitalVelocity = (2 * Math.PI * (6371 + 550)) / (orbitPeriod / 60) // 約 7.5 km/s

    return {
        lat: satLat,
        lon: satLon,
        altitude: orbitAltitude,
        velocity: orbitalVelocity,
    }
}

// 計算兩點間距離（公尺）
function calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number {
    const R = 6371000 // 地球半徑（公尺）
    const dLat = ((lat2 - lat1) * Math.PI) / 180
    const dLon = ((lon2 - lon1) * Math.PI) / 180
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
            Math.cos((lat2 * Math.PI) / 180) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return R * c
}

// 計算考慮高度的 3D 距離
function _calculate3DDistance(
    lat1: number,
    lon1: number,
    alt1: number,
    lat2: number,
    lon2: number,
    alt2: number
): number {
    // 先計算表面距離
    const surfaceDistance = calculateDistance(lat1, lon1, lat2, lon2)

    // 計算高度差
    const altitudeDiff = Math.abs(alt1 - alt2)

    // 計算 3D 距離
    return Math.sqrt(
        surfaceDistance * surfaceDistance + altitudeDiff * altitudeDiff
    )
}

// UE 移動軌跡（全球化支援 - 可配置）
const _ueTrajectory = [
    { time: 0, lat: 0.0, lon: 0.0 },
    { time: 10, lat: 0.002, lon: 0.002 },
    { time: 20, lat: 0.004, lon: 0.004 },
    { time: 30, lat: 0.006, lon: 0.006 },
    { time: 40, lat: 0.008, lon: 0.008 },
    { time: 50, lat: 0.01, lon: 0.01 },
    { time: 60, lat: 0.008, lon: 0.012 },
    { time: 70, lat: 0.006, lon: 0.014 },
    { time: 80, lat: 0.004, lon: 0.016 },
    { time: 90, lat: 0.002, lon: 0.018 },
]

// 固定參考位置（全球化支援 - 可配置）
const _fixedReferenceLocation = { lat: 0.0, lon: 0.0 }

// 生成距離數據點
function generateDistanceData() {
    const distance1Points = [] // UE 到移動參考位置（衛星）的距離
    const distance2Points = [] // UE 到固定參考位置的距離

    for (let time = 0; time <= 95; time += 5) {
        // 模擬實際的 Event D2 觸發場景
        // 距離1: 衛星距離 (545-555km 範圍變化)
        const satelliteBaseDistance = 550000 // 550km 基準距離
        const satelliteVariation = 5000 * Math.sin((time / 95) * 2 * Math.PI) // ±5km 變化
        const distance1 = satelliteBaseDistance + satelliteVariation

        // 距離2: 地面固定點距離 (4-8km 範圍變化)
        const groundBaseDistance = 6000 // 6km 基準距離
        const groundVariation = 2000 * Math.cos((time / 95) * 2 * Math.PI) // ±2km 變化
        const distance2 = groundBaseDistance + groundVariation

        distance1Points.push({ x: time, y: distance1 })
        distance2Points.push({ x: time, y: distance2 })
    }

    return { distance1Points, distance2Points }
}

// 生成當前時間游標數據
const generateCurrentTimeCursor = (currentTime: number) => {
    return [
        { x: currentTime, y: 0 }, // 底部
        { x: currentTime, y: 600000 }, // 頂部 (D2 的 Y 軸範圍為距離，最大600km)
    ]
}

// 計算當前時間點的距離值（線性插值）
const getCurrentDistanceFromPoints = (
    currentTime: number,
    distancePoints: Array<{ x: number; y: number }>
) => {
    if (currentTime <= distancePoints[0].x) return distancePoints[0].y
    if (currentTime >= distancePoints[distancePoints.length - 1].x)
        return distancePoints[distancePoints.length - 1].y

    for (let i = 0; i < distancePoints.length - 1; i++) {
        if (
            currentTime >= distancePoints[i].x &&
            currentTime <= distancePoints[i + 1].x
        ) {
            const t =
                (currentTime - distancePoints[i].x) /
                (distancePoints[i + 1].x - distancePoints[i].x)
            return (
                distancePoints[i].y +
                t * (distancePoints[i + 1].y - distancePoints[i].y)
            )
        }
    }
    return distancePoints[0].y
}

// 生成衛星距離追蹤節點（左Y軸）
const generateSatelliteNode = (currentTime: number, distance: number) => {
    return [{ x: currentTime, y: distance }]
}

// 生成地面距離追蹤節點（右Y軸）
const generateGroundNode = (currentTime: number, distance: number) => {
    return [{ x: currentTime, y: distance }]
}

// 生成衛星軌道路徑效果
const generateSatelliteTrail = (
    currentTime: number,
    distance1Points: Array<{ x: number; y: number }>,
    trailLength: number = 10
) => {
    const trail = []
    const startTime = Math.max(0, currentTime - trailLength)

    for (let t = startTime; t <= currentTime; t += 0.5) {
        const distance = getCurrentDistanceFromPoints(t, distance1Points)
        trail.push({ x: t, y: distance })
    }

    return trail
}

// 檢查Event D2事件觸發狀態
const checkD2EventTrigger = (
    satDistance: number,
    groundDistance: number,
    thresh1: number,
    thresh2: number,
    hysteresis: number
) => {
    // Event D2 進入條件: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2
    // Ml1: 衛星距離, Ml2: 地面距離
    const condition1 = satDistance - hysteresis > thresh1
    const condition2 = groundDistance + hysteresis < thresh2
    const isTriggered = condition1 && condition2

    return {
        isTriggered,
        condition1,
        condition2,
        condition1Status: condition1 ? 'satisfied' : 'not_satisfied',
        condition2Status: condition2 ? 'satisfied' : 'not_satisfied',
    }
}

interface PureD2ChartProps {
    thresh1?: number // 距離門檻1（米）
    thresh2?: number // 距離門檻2（米）
    hysteresis?: number // 遲滯參數（米）
    currentTime?: number // Current time in seconds
    showThresholdLines?: boolean
    isDarkTheme?: boolean
    onThemeToggle?: () => void
}

const PureD2Chart: React.FC<PureD2ChartProps> = ({
    thresh1 = 550000,
    thresh2 = 6000,
    hysteresis = 20,
    currentTime = 0,
    showThresholdLines = true,
    isDarkTheme = true,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const chartRef = useRef<Chart | null>(null)
    const _isInitialized = useRef(false)

    // 使用 useMemo 穩定主題配色方案 - 與 A4/D1 一致
    const colors = useMemo(
        () => ({
            dark: {
                distance1Line: '#28A745', // 綠色：距離1（移動參考位置）
                distance2Line: '#FD7E14', // 橙色：距離2（固定參考位置）
                thresh1Line: '#DC3545', // 紅色：門檻1
                thresh2Line: '#007BFF', // 藍色：門檻2
                currentTimeLine: '#ff6b35', // 動畫游標線顏色
                title: 'white',
                text: 'white',
                grid: 'rgba(255, 255, 255, 0.1)',
                background: 'transparent',
            },
            light: {
                distance1Line: '#198754',
                distance2Line: '#FD6C00',
                thresh1Line: '#DC3545',
                thresh2Line: '#0D6EFD',
                currentTimeLine: '#ff6b35', // 動畫游標線顏色
                title: 'black',
                text: '#333333',
                grid: 'rgba(0, 0, 0, 0.1)',
                background: 'white',
            },
        }),
        []
    )

    const currentTheme = useMemo(
        () => (isDarkTheme ? colors.dark : colors.light),
        [isDarkTheme, colors]
    )

    // 計算距離數據
    const { distance1Points, distance2Points } = useMemo(
        () => generateDistanceData(),
        []
    )

    // 創建圖表配置
    const chartConfig = useMemo(() => {
        return {
            type: 'line' as const,
            data: {
                datasets: [
                    {
                        label: '距離1 (UE ← → 移動參考位置/衛星)',
                        data: distance1Points,
                        borderColor: currentTheme.distance1Line,
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y-left', // 使用左側Y軸
                    },
                    {
                        label: '距離2 (UE ← → 固定參考位置)',
                        data: distance2Points,
                        borderColor: currentTheme.distance2Line,
                        backgroundColor: 'rgba(253, 126, 20, 0.1)',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y-right', // 使用右側Y軸
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart' as const,
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Event D2: 移動參考位置距離事件 (3GPP TS 38.331)',
                        font: {
                            size: 16,
                            weight: 'bold' as const,
                        },
                        color: currentTheme.text,
                        padding: 20,
                    },
                    legend: {
                        display: true,
                        position: 'top' as const,
                        labels: {
                            color: currentTheme.text,
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 12,
                            },
                        },
                    },
                    tooltip: {
                        mode: 'index' as const,
                        intersect: false,
                        callbacks: {
                            title: (context) => `時間: ${context[0].parsed.x}s`,
                            label: (context) => {
                                const dataset = context.dataset.label || ''
                                const value = context.parsed.y.toFixed(1)
                                return `${dataset}: ${value}m`
                            },
                        },
                    },
                    annotation: {
                        annotations: showThresholdLines
                            ? {
                                  thresh1Line: {
                                      type: 'line' as const,
                                      scaleID: 'y-left',
                                      value: thresh1,
                                      borderColor: currentTheme.thresh1Line,
                                      borderWidth: 3,
                                      borderDash: [8, 4],
                                      label: {
                                          content: `Thresh1: ${(
                                              thresh1 / 1000
                                          ).toFixed(0)}km (衛星)`,
                                          enabled: true,
                                          position: 'start' as const,
                                          backgroundColor:
                                              currentTheme.thresh1Line,
                                          color: 'white',
                                          font: { size: 11, weight: 'bold' },
                                      },
                                  },
                                  thresh2Line: {
                                      type: 'line' as const,
                                      scaleID: 'y-right',
                                      value: thresh2,
                                      borderColor: currentTheme.thresh2Line,
                                      borderWidth: 3,
                                      borderDash: [8, 4],
                                      label: {
                                          content: `Thresh2: ${(
                                              thresh2 / 1000
                                          ).toFixed(1)}km (地面)`,
                                          enabled: true,
                                          position: 'end' as const,
                                          backgroundColor:
                                              currentTheme.thresh2Line,
                                          color: 'white',
                                          font: { size: 11, weight: 'bold' },
                                      },
                                  },
                                  // 添加遲滯區間標註 - 衛星距離 (左Y軸)
                                  hystThresh1Upper: {
                                      type: 'line' as const,
                                      scaleID: 'y-left',
                                      value: thresh1 + hysteresis,
                                      borderColor: currentTheme.thresh1Line,
                                      borderWidth: 1,
                                      borderDash: [3, 3],
                                      label: {
                                          content: `+Hys: ${(
                                              (thresh1 + hysteresis) /
                                              1000
                                          ).toFixed(0)}km`,
                                          enabled: true,
                                          position: 'start' as const,
                                          backgroundColor:
                                              'rgba(220, 53, 69, 0.7)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                                  hystThresh1Lower: {
                                      type: 'line' as const,
                                      scaleID: 'y-left',
                                      value: thresh1 - hysteresis,
                                      borderColor: currentTheme.thresh1Line,
                                      borderWidth: 1,
                                      borderDash: [3, 3],
                                      label: {
                                          content: `-Hys: ${(
                                              (thresh1 - hysteresis) /
                                              1000
                                          ).toFixed(0)}km`,
                                          enabled: true,
                                          position: 'start' as const,
                                          backgroundColor:
                                              'rgba(220, 53, 69, 0.7)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                                  // 遲滯區間標註 - 地面距離 (右Y軸)
                                  hystThresh2Upper: {
                                      type: 'line' as const,
                                      scaleID: 'y-right',
                                      value: thresh2 + hysteresis,
                                      borderColor: currentTheme.thresh2Line,
                                      borderWidth: 1,
                                      borderDash: [3, 3],
                                      label: {
                                          content: `+Hys: ${(
                                              (thresh2 + hysteresis) /
                                              1000
                                          ).toFixed(2)}km`,
                                          enabled: true,
                                          position: 'end' as const,
                                          backgroundColor:
                                              'rgba(0, 123, 255, 0.7)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                                  hystThresh2Lower: {
                                      type: 'line' as const,
                                      scaleID: 'y-right',
                                      value: thresh2 - hysteresis,
                                      borderColor: currentTheme.thresh2Line,
                                      borderWidth: 1,
                                      borderDash: [3, 3],
                                      label: {
                                          content: `-Hys: ${(
                                              (thresh2 - hysteresis) /
                                              1000
                                          ).toFixed(2)}km`,
                                          enabled: true,
                                          position: 'end' as const,
                                          backgroundColor:
                                              'rgba(0, 123, 255, 0.7)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                                  // Event D2 觸發條件標註 - X軸時間區間
                                  triggerCondition: {
                                      type: 'box' as const,
                                      xMin: 20,
                                      xMax: 80,
                                      xScaleID: 'x',
                                      yScaleID: 'y-left',
                                      yMin: 545000,
                                      yMax: 547000,
                                      backgroundColor:
                                          'rgba(40, 167, 69, 0.15)',
                                      borderColor: 'rgba(40, 167, 69, 0.6)',
                                      borderWidth: 2,
                                      label: {
                                          content:
                                              'Event D2 觸發區間 (20-80s)\n條件: Ml1-Hys>Thresh1 AND Ml2+Hys<Thresh2',
                                          enabled: true,
                                          position: 'center' as const,
                                          backgroundColor:
                                              'rgba(40, 167, 69, 0.9)',
                                          color: 'white',
                                          font: { size: 10, weight: 'bold' },
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
                            text: '時間 (秒)',
                            color: currentTheme.text,
                            font: {
                                size: 14,
                                weight: 'bold' as const,
                            },
                        },
                        grid: {
                            color: currentTheme.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentTheme.text,
                            stepSize: 10,
                        },
                        min: 0,
                        max: 95,
                    },
                    'y-left': {
                        type: 'linear' as const,
                        position: 'left' as const,
                        title: {
                            display: true,
                            text: '衛星距離 (km)',
                            color: currentTheme.distance1Line,
                            font: {
                                size: 14,
                                weight: 'bold' as const,
                            },
                        },
                        grid: {
                            color: currentTheme.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentTheme.distance1Line,
                            callback: (value) => `${(value / 1000).toFixed(0)}`,
                        },
                        min: 545000, // 545km
                        max: 560000, // 560km
                    },
                    'y-right': {
                        type: 'linear' as const,
                        position: 'right' as const,
                        title: {
                            display: true,
                            text: '地面距離 (km)',
                            color: currentTheme.distance2Line,
                            font: {
                                size: 14,
                                weight: 'bold' as const,
                            },
                        },
                        grid: {
                            display: false, // 避免網格線重疊
                        },
                        ticks: {
                            color: currentTheme.distance2Line,
                            callback: (value) => `${(value / 1000).toFixed(1)}`,
                        },
                        min: 3000, // 3km
                        max: 9000, // 9km
                    },
                },
                interaction: {
                    mode: 'index' as const,
                    intersect: false,
                },
                hover: {
                    mode: 'index' as const,
                    intersect: false,
                },
            },
        }
    }, [
        distance1Points,
        distance2Points,
        thresh1,
        thresh2,
        hysteresis,
        showThresholdLines,
        currentTheme,
    ])

    // 創建和更新圖表
    useEffect(() => {
        if (!canvasRef.current) return

        const ctx = canvasRef.current.getContext('2d')
        if (!ctx) return

        // 銷毀舊圖表
        if (chartRef.current) {
            chartRef.current.destroy()
        }

        // 創建新圖表
        chartRef.current = new Chart(ctx, chartConfig)

        return () => {
            if (chartRef.current) {
                chartRef.current.destroy()
                chartRef.current = null
            }
        }
    }, [chartConfig])

    // 更新游標和動態節點 - 不重新創建圖表
    useEffect(() => {
        if (!chartRef.current) return
        const chart = chartRef.current

        // 處理游標和動態節點數據集
        const expectedCursorIndex = 2
        const expectedSatNodeIndex = 3
        const expectedGroundNodeIndex = 4
        const expectedTrailIndex = 5
        const expectedEventNodeIndex = 6

        if (currentTime > 0) {
            const cursorData = generateCurrentTimeCursor(currentTime)
            const currentSatDistance = getCurrentDistanceFromPoints(
                currentTime,
                distance1Points
            )
            const currentGroundDistance = getCurrentDistanceFromPoints(
                currentTime,
                distance2Points
            )
            const eventStatus = checkD2EventTrigger(
                currentSatDistance,
                currentGroundDistance,
                thresh1,
                thresh2,
                hysteresis
            )
            const satelliteTrail = generateSatelliteTrail(
                currentTime,
                distance1Points
            )

            // 更新游標
            if (chart.data.datasets[expectedCursorIndex]) {
                chart.data.datasets[expectedCursorIndex].data = cursorData
                chart.data.datasets[
                    expectedCursorIndex
                ].label = `Current Time: ${currentTime.toFixed(1)}s`
            } else {
                chart.data.datasets.push({
                    label: `Current Time: ${currentTime.toFixed(1)}s`,
                    data: cursorData,
                    borderColor: currentTheme.currentTimeLine,
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    tension: 0,
                    borderDash: [5, 5],
                    yAxisID: 'y-left',
                } as Record<string, unknown>)
            }

            // 更新衛星節點（左Y軸）
            const satNodeData = generateSatelliteNode(
                currentTime,
                currentSatDistance
            )
            const satNodeColor = eventStatus.condition1 ? '#28A745' : '#FFC107'
            const satNodeSize = eventStatus.condition1 ? 14 : 10

            if (chart.data.datasets[expectedSatNodeIndex]) {
                chart.data.datasets[expectedSatNodeIndex].data = satNodeData
                chart.data.datasets[
                    expectedSatNodeIndex
                ].label = `Satellite (${(currentSatDistance / 1000).toFixed(
                    0
                )}km)`
                chart.data.datasets[expectedSatNodeIndex].borderColor =
                    satNodeColor
                chart.data.datasets[expectedSatNodeIndex].backgroundColor =
                    satNodeColor
                chart.data.datasets[expectedSatNodeIndex].pointRadius =
                    satNodeSize
            } else {
                chart.data.datasets.push({
                    label: `Satellite (${(currentSatDistance / 1000).toFixed(
                        0
                    )}km)`,
                    data: satNodeData,
                    borderColor: satNodeColor,
                    backgroundColor: satNodeColor,
                    borderWidth: 3,
                    fill: false,
                    pointRadius: satNodeSize,
                    pointHoverRadius: satNodeSize + 4,
                    pointStyle: 'circle',
                    showLine: false,
                    yAxisID: 'y-left',
                    tension: 0,
                } as Record<string, unknown>)
            }

            // 更新地面節點（右Y軸）
            const groundNodeData = generateGroundNode(
                currentTime,
                currentGroundDistance
            )
            const groundNodeColor = eventStatus.condition2
                ? '#007BFF'
                : '#DC3545'
            const groundNodeSize = eventStatus.condition2 ? 14 : 10

            if (chart.data.datasets[expectedGroundNodeIndex]) {
                chart.data.datasets[expectedGroundNodeIndex].data =
                    groundNodeData
                chart.data.datasets[
                    expectedGroundNodeIndex
                ].label = `Ground (${(currentGroundDistance / 1000).toFixed(
                    1
                )}km)`
                chart.data.datasets[expectedGroundNodeIndex].borderColor =
                    groundNodeColor
                chart.data.datasets[expectedGroundNodeIndex].backgroundColor =
                    groundNodeColor
                chart.data.datasets[expectedGroundNodeIndex].pointRadius =
                    groundNodeSize
            } else {
                chart.data.datasets.push({
                    label: `Ground (${(currentGroundDistance / 1000).toFixed(
                        1
                    )}km)`,
                    data: groundNodeData,
                    borderColor: groundNodeColor,
                    backgroundColor: groundNodeColor,
                    borderWidth: 3,
                    fill: false,
                    pointRadius: groundNodeSize,
                    pointHoverRadius: groundNodeSize + 4,
                    pointStyle: 'rect',
                    showLine: false,
                    yAxisID: 'y-right',
                    tension: 0,
                } as Record<string, unknown>)
            }

            // 更新衛星軌道路徑（動態追蹤效果）
            if (chart.data.datasets[expectedTrailIndex]) {
                chart.data.datasets[expectedTrailIndex].data = satelliteTrail
            } else {
                chart.data.datasets.push({
                    label: 'Satellite Orbit Trail',
                    data: satelliteTrail,
                    borderColor: 'rgba(40, 167, 69, 0.5)',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 2,
                    pointHoverRadius: 0,
                    tension: 0.3,
                    yAxisID: 'y-left',
                    borderDash: [3, 3],
                } as Record<string, unknown>)
            }

            // 更新Event D2狀態節點
            if (eventStatus.isTriggered) {
                const eventNodeData = [
                    { x: currentTime, y: currentSatDistance },
                ]
                if (chart.data.datasets[expectedEventNodeIndex]) {
                    chart.data.datasets[expectedEventNodeIndex].data =
                        eventNodeData
                } else {
                    chart.data.datasets.push({
                        label: 'Event D2 TRIGGERED!',
                        data: eventNodeData,
                        borderColor: '#FF6B35',
                        backgroundColor: '#FF6B35',
                        borderWidth: 4,
                        fill: false,
                        pointRadius: 20,
                        pointHoverRadius: 24,
                        pointStyle: 'star',
                        showLine: false,
                        yAxisID: 'y-left',
                        tension: 0,
                    } as Record<string, unknown>)
                }
            } else {
                // 移除Event節點
                if (
                    chart.data.datasets[expectedEventNodeIndex] &&
                    chart.data.datasets[expectedEventNodeIndex].label?.includes(
                        'TRIGGERED'
                    )
                ) {
                    chart.data.datasets.splice(expectedEventNodeIndex, 1)
                }
            }
        } else {
            // 移除所有動態節點
            while (chart.data.datasets.length > expectedCursorIndex) {
                chart.data.datasets.pop()
            }
        }

        // 更新圖表 - 使用 'none' 避免動畫
        try {
            chart.update('none')
        } catch (error) {
            console.error('❌ [PureD2Chart] 圖表更新失敗:', error)
            // 嘗試重新初始化圖表
            chart.destroy()
            chartRef.current = null
        }
    }, [
        currentTime,
        currentTheme,
        distance1Points,
        distance2Points,
        thresh1,
        thresh2,
        hysteresis,
    ])

    return (
        <div
            style={{
                width: '100%',
                height: '100%',
                minHeight: '400px',
                maxHeight: '70vh',
                position: 'relative',
                backgroundColor: currentTheme.background,
                borderRadius: '8px',
            }}
        >
            <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
        </div>
    )
}

export default PureD2Chart
