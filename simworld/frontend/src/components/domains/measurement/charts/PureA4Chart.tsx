/**
 * Pure A4 Chart Component
 * 完全對照 chart.html 的實現方式
 * 使用原生 Chart.js，拋棄 react-chartjs-2
 * 優化版本：避免不必要的重新渲染
 */

import React, { useEffect, useRef, useMemo } from 'react'
import { Chart } from 'chart.js/auto'

// 完全對照 chart.html 的數據點
const dataPoints = [
    { x: 1.48, y: -51.66 },
    { x: 3.65, y: -51.93 },
    { x: 5.82, y: -52.45 },
    { x: 7.99, y: -53.18 },
    { x: 10.17, y: -54.13 },
    { x: 12.34, y: -55.38 },
    { x: 14.51, y: -56.9 },
    { x: 16.68, y: -58.82 },
    { x: 18.66, y: -61.08 },
    { x: 20.24, y: -63.51 },
    { x: 21.32, y: -66.04 },
    { x: 22.02, y: -68.77 },
    { x: 22.21, y: -71.47 },
    { x: 22.81, y: -74.17 },
    { x: 23.79, y: -76.41 },
    { x: 25.4, y: -78.89 },
    { x: 27.35, y: -81.11 },
    { x: 29.72, y: -83.25 },
    { x: 31.4, y: -84.45 },
    { x: 35.25, y: -86.75 },
    { x: 37.42, y: -87.36 },
    { x: 39.59, y: -87.94 },
    { x: 41.76, y: -88.32 },
    { x: 43.94, y: -88.58 },
    { x: 46.11, y: -88.42 },
    { x: 48.28, y: -88.26 },
    { x: 50.45, y: -88.02 },
    { x: 52.63, y: -87.73 },
    { x: 54.8, y: -87.32 },
    { x: 56.97, y: -86.84 },
    { x: 58.65, y: -86.46 },
    { x: 61.51, y: -85.47 },
    { x: 63.69, y: -84.75 },
    { x: 65.86, y: -83.84 },
    { x: 67.83, y: -82.9 },
    { x: 70.2, y: -81.45 },
    { x: 72.37, y: -79.85 },
    { x: 74.38, y: -77.7 },
    { x: 75.53, y: -75.79 },
    { x: 76.13, y: -71.29 },
    { x: 77.31, y: -68.42 },
    { x: 78.99, y: -65.89 },
    { x: 81.06, y: -63.81 },
    { x: 83.24, y: -62.15 },
    { x: 85.41, y: -60.98 },
    { x: 87.58, y: -60.17 },
    { x: 89.75, y: -59.67 },
    { x: 91.23, y: -59.54 },
]

// 生成當前時間游標數據
const generateCurrentTimeCursor = (currentTime: number) => {
    return [
        { x: currentTime, y: -95 }, // 底部
        { x: currentTime, y: -40 }, // 頂部
    ]
}

// 計算當前時間點的RSRP值（線性插值）
const getCurrentRSRP = (currentTime: number): number => {
    if (currentTime <= dataPoints[0].x) return dataPoints[0].y
    if (currentTime >= dataPoints[dataPoints.length - 1].x)
        return dataPoints[dataPoints.length - 1].y

    // 找到當前時間點前後的數據點
    for (let i = 0; i < dataPoints.length - 1; i++) {
        if (
            currentTime >= dataPoints[i].x &&
            currentTime <= dataPoints[i + 1].x
        ) {
            // 線性插值
            const t =
                (currentTime - dataPoints[i].x) /
                (dataPoints[i + 1].x - dataPoints[i].x)
            return dataPoints[i].y + t * (dataPoints[i + 1].y - dataPoints[i].y)
        }
    }
    return dataPoints[0].y
}

// 生成信號強度追蹤節點
const generateSignalNode = (currentTime: number, rsrp: number) => {
    return [{ x: currentTime, y: rsrp }]
}

// 檢查事件觸發狀態
const checkEventTrigger = (
    rsrp: number,
    threshold: number,
    hysteresis: number
) => {
    const enterThreshold = threshold + hysteresis // 進入門檻
    const exitThreshold = threshold - hysteresis // 離開門檻

    return {
        isAboveEnterThreshold: rsrp > enterThreshold,
        isBelowExitThreshold: rsrp < exitThreshold,
        isInHysteresisZone: rsrp >= exitThreshold && rsrp <= enterThreshold,
    }
}

interface PureA4ChartProps {
    width?: number
    height?: number
    threshold?: number
    hysteresis?: number
    currentTime?: number // Current time in seconds
    showThresholdLines?: boolean
    isDarkTheme?: boolean
    onThemeToggle?: () => void
}

export const PureA4Chart: React.FC<PureA4ChartProps> = React.memo(
    ({
        width: _width = 800,
        height: _height = 400,
        threshold = -70,
        hysteresis = 3,
        currentTime = 0,
        showThresholdLines = true,
        isDarkTheme = true,
        _onThemeToggle,
    }) => {
        const canvasRef = useRef<HTMLCanvasElement>(null)
        const chartRef = useRef<Chart | null>(null)
        const isInitialized = useRef(false)

        // 使用 useMemo 穩定主題配色方案
        const colors = useMemo(
            () => ({
                dark: {
                    rsrpLine: '#007bff',
                    thresholdLine: '#E74C3C',
                    hysteresisLine: 'rgba(231, 76, 60, 0.6)',
                    currentTimeLine: '#ff6b35', // 動畫游標線顏色
                    title: 'white',
                    text: 'white',
                    grid: 'rgba(255, 255, 255, 0.1)',
                    background: 'transparent',
                },
                light: {
                    rsrpLine: '#0066CC',
                    thresholdLine: '#D32F2F',
                    hysteresisLine: '#D32F2F',
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

        // 初始化圖表 - 只執行一次
        useEffect(() => {
            if (!canvasRef.current || isInitialized.current) return
            const ctx = canvasRef.current.getContext('2d')
            if (!ctx) return

            // 準備初始數據集 - 使用正確的主題顏色
            const datasets: any[] = [
                {
                    label: 'Neighbor Cell RSRP',
                    data: dataPoints,
                    borderColor: currentTheme.rsrpLine,
                    backgroundColor: 'transparent',
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                },
            ]

            // 如果需要顯示閾值線，添加閾值線數據集
            if (showThresholdLines) {
                const thresholdData = dataPoints.map((point) => ({
                    x: point.x,
                    y: threshold,
                }))
                const upperThresholdData = dataPoints.map((point) => ({
                    x: point.x,
                    y: threshold + hysteresis,
                }))
                const lowerThresholdData = dataPoints.map((point) => ({
                    x: point.x,
                    y: threshold - hysteresis,
                }))

                datasets.push(
                    {
                        label: 'a4-Threshold',
                        data: thresholdData,
                        borderColor: currentTheme.thresholdLine,
                        backgroundColor: 'transparent',
                        borderDash: [10, 5],
                        borderWidth: 2,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                    },
                    {
                        label: 'Threshold + Hys',
                        data: upperThresholdData,
                        borderColor: currentTheme.hysteresisLine,
                        backgroundColor: 'transparent',
                        borderDash: [5, 3],
                        borderWidth: 3,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                    },
                    {
                        label: 'Threshold - Hys',
                        data: lowerThresholdData,
                        borderColor: currentTheme.hysteresisLine,
                        backgroundColor: 'transparent',
                        borderDash: [5, 3],
                        borderWidth: 3,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                    }
                )
            }

            // 添加當前時間游標
            if (currentTime > 0) {
                const cursorData = generateCurrentTimeCursor(currentTime)
                datasets.push({
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
                })

                // 添加信號強度追蹤節點
                const currentRSRP = getCurrentRSRP(currentTime)
                const signalNode = generateSignalNode(currentTime, currentRSRP)
                const eventStatus = checkEventTrigger(
                    currentRSRP,
                    threshold,
                    hysteresis
                )

                // 根據事件狀態決定節點顏色和大小
                let nodeColor = '#FFD93D' // 預設黃色
                let nodeSize = 8
                let nodeLabel = 'Signal Tracking'

                if (eventStatus.isAboveEnterThreshold) {
                    nodeColor = '#28A745' // 綠色：事件激活
                    nodeSize = 12
                    nodeLabel = 'Event A4 ACTIVE'
                } else if (eventStatus.isBelowExitThreshold) {
                    nodeColor = '#DC3545' // 紅色：信號過弱
                    nodeSize = 8
                    nodeLabel = 'Signal Too Weak'
                } else if (eventStatus.isInHysteresisZone) {
                    nodeColor = '#FFC107' // 橙色：遲滯區間
                    nodeSize = 10
                    nodeLabel = 'Hysteresis Zone'
                }

                datasets.push({
                    label: `${nodeLabel} (RSRP: ${currentRSRP.toFixed(1)} dBm)`,
                    data: signalNode,
                    borderColor: nodeColor,
                    backgroundColor: nodeColor,
                    borderWidth: 3,
                    fill: false,
                    pointRadius: nodeSize,
                    pointHoverRadius: nodeSize + 4,
                    pointStyle: 'circle',
                    showLine: false, // 只顯示點，不顯示線
                    tension: 0,
                })
            }

            try {
                chartRef.current = new Chart(ctx, {
                    type: 'line',
                    data: { datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: showThresholdLines,
                                position: 'bottom',
                                labels: {
                                    color: currentTheme.text,
                                    font: { size: 12 },
                                },
                            },
                            title: {
                                display: true,
                                text: 'Event A4: 鄰近基站優於門檻事件 (3GPP TS 38.331)',
                                font: {
                                    size: 16,
                                    weight: 'bold',
                                },
                                color: currentTheme.title,
                                padding: 20,
                            },
                        },
                        scales: {
                            x: {
                                type: 'linear',
                                title: {
                                    display: true,
                                    text: 'Time (s)',
                                    color: currentTheme.text,
                                    font: { size: 14 },
                                },
                                ticks: { color: currentTheme.text },
                                grid: { color: currentTheme.grid },
                                min: 0,
                                max: 95,
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'RSRP (dBm)',
                                    color: currentTheme.text,
                                    font: { size: 14 },
                                },
                                ticks: { color: currentTheme.text },
                                grid: { color: currentTheme.grid },
                                min: -100,
                                max: -50,
                                reverse: true,
                            },
                        },
                    },
                })

                isInitialized.current = true
            } catch (error) {
                console.error('❌ [PureA4Chart] 圖表創建失敗:', error)
            }

            // 清理函數
            return () => {
                if (chartRef.current) {
                    chartRef.current.destroy()
                    chartRef.current = null
                    isInitialized.current = false
                }
            }
        }, [currentTheme]) // 響應主題變化重新初始化

        // 更新參數和主題 - 不重新創建圖表
        useEffect(() => {
            if (!chartRef.current || !isInitialized.current) {
                return
            }
            const chart = chartRef.current

            // 處理 showThresholdLines 變化
            if (showThresholdLines) {
                // 確保有閾值線數據集
                const thresholdData = dataPoints.map((point) => ({
                    x: point.x,
                    y: threshold,
                }))
                const upperThresholdData = dataPoints.map((point) => ({
                    x: point.x,
                    y: threshold + hysteresis,
                }))
                const lowerThresholdData = dataPoints.map((point) => ({
                    x: point.x,
                    y: threshold - hysteresis,
                }))

                // 如果沒有閾值線數據集，添加它們
                if (chart.data.datasets.length === 1) {
                    chart.data.datasets.push(
                        {
                            label: 'a4-Threshold',
                            data: thresholdData,
                            borderColor: currentTheme.thresholdLine,
                            backgroundColor: 'transparent',
                            borderDash: [10, 5],
                            borderWidth: 2,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>,
                        {
                            label: 'Threshold + Hys',
                            data: upperThresholdData,
                            borderColor: currentTheme.hysteresisLine,
                            backgroundColor: 'transparent',
                            borderDash: [5, 3],
                            borderWidth: 3,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>,
                        {
                            label: 'Threshold - Hys',
                            data: lowerThresholdData,
                            borderColor: currentTheme.hysteresisLine,
                            backgroundColor: 'transparent',
                            borderDash: [5, 3],
                            borderWidth: 3,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>
                    )
                } else {
                    // 更新現有閾值線數據
                    if (chart.data.datasets[1]) {
                        chart.data.datasets[1].data = thresholdData
                    }
                    if (chart.data.datasets[2]) {
                        chart.data.datasets[2].data = upperThresholdData
                    }
                    if (chart.data.datasets[3]) {
                        chart.data.datasets[3].data = lowerThresholdData
                    }
                }
            } else {
                // 隱藏閾值線，但保留數據集結構
                if (chart.data.datasets.length > 1) {
                    chart.data.datasets = [chart.data.datasets[0]]
                }
            }

            // 處理游標數據集
            const expectedCursorIndex = showThresholdLines ? 4 : 1
            const expectedNodeIndex = expectedCursorIndex + 1

            if (currentTime > 0) {
                const cursorData = generateCurrentTimeCursor(currentTime)
                const currentRSRP = getCurrentRSRP(currentTime)
                const signalNode = generateSignalNode(currentTime, currentRSRP)
                const eventStatus = checkEventTrigger(
                    currentRSRP,
                    threshold,
                    hysteresis
                )

                // 根據事件狀態決定節點顏色和大小
                let nodeColor = '#FFD93D' // 預設黃色
                let nodeSize = 8
                let nodeLabel = 'Signal Tracking'

                if (eventStatus.isAboveEnterThreshold) {
                    nodeColor = '#28A745' // 綠色：事件激活
                    nodeSize = 12
                    nodeLabel = 'Event A4 ACTIVE'
                } else if (eventStatus.isBelowExitThreshold) {
                    nodeColor = '#DC3545' // 紅色：信號過弱
                    nodeSize = 8
                    nodeLabel = 'Signal Too Weak'
                } else if (eventStatus.isInHysteresisZone) {
                    nodeColor = '#FFC107' // 橙色：遲滯區間
                    nodeSize = 10
                    nodeLabel = 'Hysteresis Zone'
                }

                // 更新游標數據集
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
                    } as Record<string, unknown>)
                }

                // 更新信號節點數據集
                if (chart.data.datasets[expectedNodeIndex]) {
                    chart.data.datasets[expectedNodeIndex].data = signalNode
                    chart.data.datasets[
                        expectedNodeIndex
                    ].label = `${nodeLabel} (RSRP: ${currentRSRP.toFixed(
                        1
                    )} dBm)`
                    chart.data.datasets[expectedNodeIndex].borderColor =
                        nodeColor
                    chart.data.datasets[expectedNodeIndex].backgroundColor =
                        nodeColor
                    chart.data.datasets[expectedNodeIndex].pointRadius =
                        nodeSize
                    chart.data.datasets[expectedNodeIndex].pointHoverRadius =
                        nodeSize + 4
                } else {
                    chart.data.datasets.push({
                        label: `${nodeLabel} (RSRP: ${currentRSRP.toFixed(
                            1
                        )} dBm)`,
                        data: signalNode,
                        borderColor: nodeColor,
                        backgroundColor: nodeColor,
                        borderWidth: 3,
                        fill: false,
                        pointRadius: nodeSize,
                        pointHoverRadius: nodeSize + 4,
                        pointStyle: 'circle',
                        showLine: false,
                        tension: 0,
                    } as Record<string, unknown>)
                }
            } else {
                // 移除游標和節點數據集
                if (
                    chart.data.datasets[expectedNodeIndex] &&
                    chart.data.datasets[expectedNodeIndex].label?.includes(
                        'RSRP:'
                    )
                ) {
                    chart.data.datasets.splice(expectedNodeIndex, 1)
                }
                if (
                    chart.data.datasets[expectedCursorIndex] &&
                    chart.data.datasets[expectedCursorIndex].label?.includes(
                        'Current Time'
                    )
                ) {
                    chart.data.datasets.splice(expectedCursorIndex, 1)
                }
            }

            // 更新顏色主題
            chart.data.datasets[0].borderColor = currentTheme.rsrpLine
            if (chart.data.datasets[1]) {
                chart.data.datasets[1].borderColor = currentTheme.thresholdLine
            }
            if (chart.data.datasets[2]) {
                chart.data.datasets[2].borderColor = currentTheme.hysteresisLine
            }
            if (chart.data.datasets[3]) {
                chart.data.datasets[3].borderColor = currentTheme.hysteresisLine
            }
            // 更新游標顏色
            if (
                chart.data.datasets[expectedCursorIndex] &&
                chart.data.datasets[expectedCursorIndex].label?.includes(
                    'Current Time'
                )
            ) {
                chart.data.datasets[expectedCursorIndex].borderColor =
                    currentTheme.currentTimeLine
            }
            // 信號節點的顏色根據狀態動態決定，無需在此更新

            // 更新圖表選項的顏色 - 安全訪問
            try {
                if (chart.options?.plugins?.title) {
                    chart.options.plugins.title.color = currentTheme.title
                }
                if (chart.options?.plugins?.legend?.labels) {
                    chart.options.plugins.legend.labels.color =
                        currentTheme.text
                }
                if (chart.options?.plugins?.legend) {
                    chart.options.plugins.legend.display = showThresholdLines
                }

                // 確保 scales 存在
                if (!chart.options.scales) {
                    chart.options.scales = {}
                }

                const xScale = chart.options.scales.x as Record<string, any>
                if (xScale?.title) {
                    xScale.title.color = currentTheme.text
                }
                if (xScale?.ticks) {
                    xScale.ticks.color = currentTheme.text
                }
                if (xScale?.grid) {
                    xScale.grid.color = currentTheme.grid
                }

                const yScale = chart.options.scales.y as Record<string, any>
                if (yScale?.title) {
                    yScale.title.color = currentTheme.text
                }
                if (yScale?.ticks) {
                    yScale.ticks.color = currentTheme.text
                }
                if (yScale?.grid) {
                    yScale.grid.color = currentTheme.grid
                }
            } catch (error) {
                console.warn('⚠️ [PureA4Chart] 更新圖表選項時發生錯誤:', error)
            }

            // 更新圖表 - 使用 'none' 避免動畫
            try {
                chart.update('none')
            } catch (error) {
                console.error('❌ [PureA4Chart] 圖表更新失敗:', error)
                // 嘗試重新初始化圖表
                chart.destroy()
                chartRef.current = null
                isInitialized.current = false
            }
        }, [
            threshold,
            hysteresis,
            currentTheme,
            showThresholdLines,
            currentTime,
        ])

        return (
            <div
                style={{
                    width: '100%',
                    height: '100%',
                    minHeight: '300px',
                    maxHeight: '70vh',
                    position: 'relative',
                    backgroundColor: currentTheme.background,
                    borderRadius: '8px',
                }}
            >
                <canvas
                    ref={canvasRef}
                    style={{ width: '100%', height: '100%' }}
                />
            </div>
        )
    }
)

PureA4Chart.displayName = 'PureA4Chart'

export default PureA4Chart
