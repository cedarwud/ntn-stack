/**
 * Pure D1 Chart Component
 * 基於 3GPP TS 38.331 Section 5.5.4.15 實現
 * Event D1: 距離雙門檻事件
 * 進入條件: Ml1 – Hys > Thresh1 AND Ml2 + Hys < Thresh2
 * 離開條件: Ml1 + Hys < Thresh1 OR Ml2 – Hys > Thresh2
 */

import React, { useEffect, useRef, useMemo } from 'react'
import { Chart } from 'chart.js/auto'

// 模擬距離數據：UE 到兩個參考位置的距離隨時間變化
// 調整數據以正確展示 Event D1 觸發邏輯：
// - 在 30-70s 時間段，距離1 > Thresh1 (400m) AND 距離2 < Thresh2 (250m)
// 距離1: UE 到 referenceLocation1 的距離 (公尺)
const distance1Points = [
    { x: 0, y: 200 }, // 開始時距離較近，不觸發
    { x: 5, y: 250 },
    { x: 10, y: 300 },
    { x: 15, y: 350 },
    { x: 20, y: 380 },
    { x: 25, y: 400 }, // 接近門檻
    { x: 30, y: 450 }, // 超過 Thresh1 (400m) - 觸發區間開始
    { x: 35, y: 500 }, // 遠離 referenceLocation1
    { x: 40, y: 520 },
    { x: 45, y: 530 }, // 最遠點
    { x: 50, y: 520 },
    { x: 55, y: 500 },
    { x: 60, y: 480 },
    { x: 65, y: 450 },
    { x: 70, y: 420 }, // 仍超過 Thresh1
    { x: 75, y: 380 }, // 觸發區間結束 - 低於 Thresh1
    { x: 80, y: 350 },
    { x: 85, y: 320 },
    { x: 90, y: 280 },
    { x: 95, y: 250 }, // 回到較近距離
]

// 距離2: UE 到 referenceLocation2 的距離 (公尺)
const distance2Points = [
    { x: 0, y: 400 }, // 開始時距離較遠，不觸發
    { x: 5, y: 380 },
    { x: 10, y: 350 },
    { x: 15, y: 320 },
    { x: 20, y: 290 },
    { x: 25, y: 270 }, // 接近門檻
    { x: 30, y: 240 }, // 低於 Thresh2 (250m) - 觸發區間開始
    { x: 35, y: 200 }, // 接近 referenceLocation2
    { x: 40, y: 180 },
    { x: 45, y: 160 }, // 最近點
    { x: 50, y: 170 },
    { x: 55, y: 190 },
    { x: 60, y: 210 },
    { x: 65, y: 220 },
    { x: 70, y: 240 }, // 仍低於 Thresh2
    { x: 75, y: 260 }, // 觸發區間結束 - 超過 Thresh2
    { x: 80, y: 290 },
    { x: 85, y: 320 },
    { x: 90, y: 350 },
    { x: 95, y: 380 }, // 回到較遠距離
]

// 生成當前時間游標數據
const generateCurrentTimeCursor = (currentTime: number) => {
    return [
        { x: currentTime, y: 100 }, // 底部
        { x: currentTime, y: 600 }  // 頂部 (D1 的 Y 軸範圍為距離)
    ]
}

// 計算當前時間點的距離值（線性插值）
const getCurrentDistance = (currentTime: number, distancePoints: Array<{x: number, y: number}>) => {
    if (currentTime <= distancePoints[0].x) return distancePoints[0].y
    if (currentTime >= distancePoints[distancePoints.length - 1].x) return distancePoints[distancePoints.length - 1].y
    
    for (let i = 0; i < distancePoints.length - 1; i++) {
        if (currentTime >= distancePoints[i].x && currentTime <= distancePoints[i + 1].x) {
            const t = (currentTime - distancePoints[i].x) / (distancePoints[i + 1].x - distancePoints[i].x)
            return distancePoints[i].y + t * (distancePoints[i + 1].y - distancePoints[i].y)
        }
    }
    return distancePoints[0].y
}

// 生成距離追蹤節點
const generateDistanceNode = (currentTime: number, distance: number) => {
    return [{ x: currentTime, y: distance }]
}

// 生成事件觸發節點
const generateEventNode = (currentTime: number, distance: number) => {
    return [{ x: currentTime, y: distance }]
}

// 檢查Event D1事件觸發狀態
const checkD1EventTrigger = (distance1: number, distance2: number, thresh1: number, thresh2: number, hysteresis: number) => {
    // Event D1 進入條件: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2
    const condition1 = (distance1 - hysteresis) > thresh1
    const condition2 = (distance2 + hysteresis) < thresh2
    const isTriggered = condition1 && condition2
    
    return {
        isTriggered,
        condition1,
        condition2,
        condition1Status: condition1 ? 'satisfied' : 'not_satisfied',
        condition2Status: condition2 ? 'satisfied' : 'not_satisfied'
    }
}

interface PureD1ChartProps {
    width?: number
    height?: number
    thresh1?: number // distanceThreshFromReference1 (meters)
    thresh2?: number // distanceThreshFromReference2 (meters)
    hysteresis?: number // hysteresisLocation (meters)
    currentTime?: number // Current time in seconds
    showThresholdLines?: boolean
    isDarkTheme?: boolean
    onThemeToggle?: () => void
}

export const PureD1Chart: React.FC<PureD1ChartProps> = React.memo(
    ({
        width: _width = 800,
        height: _height = 400,
        thresh1 = 400, // Thresh1: 400m
        thresh2 = 250, // Thresh2: 250m
        hysteresis = 20, // 20m hysteresis
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
                    distance1Line: '#28A745', // 綠色：距離1
                    distance2Line: '#FD7E14', // 橙色：距離2
                    thresh1Line: '#DC3545', // 紅色：門檻1
                    thresh2Line: '#007BFF', // 藍色：門檻2
                    hysteresisLine: 'rgba(108, 117, 125, 0.6)', // 灰色：遲滯線
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
                    hysteresisLine: 'rgba(108, 117, 125, 0.8)',
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
            [isDarkTheme] // 移除 colors 依賴，因為 colors 已經是穩定的
        )

        // 初始化圖表 - 只執行一次
        useEffect(() => {
            if (!canvasRef.current || isInitialized.current) return
            const ctx = canvasRef.current.getContext('2d')
            if (!ctx) return


            // 準備初始數據集
            const datasets: any[] = [
                {
                    label: 'Distance 1 (UE ↔ Ref1)',
                    data: distance1Points,
                    borderColor: '#28A745', // 預設綠色
                    backgroundColor: 'transparent',
                    fill: false,
                    tension: 0.3,
                    pointRadius: 2,
                    pointHoverRadius: 4,
                    borderWidth: 3,
                },
                {
                    label: 'Distance 2 (UE ↔ Ref2)',
                    data: distance2Points,
                    borderColor: '#FD7E14', // 預設橙色
                    backgroundColor: 'transparent',
                    fill: false,
                    tension: 0.3,
                    pointRadius: 2,
                    pointHoverRadius: 4,
                    borderWidth: 3,
                },
            ]

            // 如果需要顯示門檻線，添加門檻線數據集
            if (showThresholdLines) {
                const timePoints = distance1Points.map((point) => point.x)

                // Thresh1 門檻線數據
                const thresh1Data = timePoints.map((time) => ({
                    x: time,
                    y: thresh1,
                }))

                // Thresh2 門檻線數據
                const thresh2Data = timePoints.map((time) => ({
                    x: time,
                    y: thresh2,
                }))

                // Thresh1 遲滯線
                const thresh1HysUpperData = timePoints.map((time) => ({
                    x: time,
                    y: thresh1 + hysteresis,
                }))
                const thresh1HysLowerData = timePoints.map((time) => ({
                    x: time,
                    y: thresh1 - hysteresis,
                }))

                // Thresh2 遲滯線
                const thresh2HysUpperData = timePoints.map((time) => ({
                    x: time,
                    y: thresh2 + hysteresis,
                }))
                const thresh2HysLowerData = timePoints.map((time) => ({
                    x: time,
                    y: thresh2 - hysteresis,
                }))

                datasets.push(
                    {
                        label: 'Thresh1 (Ref1 Threshold)',
                        data: thresh1Data,
                        borderColor: '#DC3545', // 紅色
                        backgroundColor: 'transparent',
                        borderDash: [10, 5],
                        borderWidth: 2,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                    },
                    {
                        label: 'Thresh2 (Ref2 Threshold)',
                        data: thresh2Data,
                        borderColor: '#007BFF', // 藍色
                        backgroundColor: 'transparent',
                        borderDash: [10, 5],
                        borderWidth: 2,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                    },
                    {
                        label: 'Thresh1 + Hys',
                        data: thresh1HysUpperData,
                        borderColor: 'rgba(220, 53, 69, 0.4)',
                        backgroundColor: 'transparent',
                        borderDash: [5, 3],
                        borderWidth: 1,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                    },
                    {
                        label: 'Thresh1 - Hys',
                        data: thresh1HysLowerData,
                        borderColor: 'rgba(220, 53, 69, 0.4)',
                        backgroundColor: 'transparent',
                        borderDash: [5, 3],
                        borderWidth: 1,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                    },
                    {
                        label: 'Thresh2 + Hys',
                        data: thresh2HysUpperData,
                        borderColor: 'rgba(0, 123, 255, 0.4)',
                        backgroundColor: 'transparent',
                        borderDash: [5, 3],
                        borderWidth: 1,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                    },
                    {
                        label: 'Thresh2 - Hys',
                        data: thresh2HysLowerData,
                        borderColor: 'rgba(0, 123, 255, 0.4)',
                        backgroundColor: 'transparent',
                        borderDash: [5, 3],
                        borderWidth: 1,
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
                
                // 添加距離追蹤節點
                const currentDistance1 = getCurrentDistance(currentTime, distance1Points)
                const currentDistance2 = getCurrentDistance(currentTime, distance2Points)
                const eventStatus = checkD1EventTrigger(currentDistance1, currentDistance2, thresh1, thresh2, hysteresis)
                
                // 節點1（距離到Ref1）
                const node1Data = generateDistanceNode(currentTime, currentDistance1)
                let node1Color = '#28A745' // 預設綠色
                let node1Size = 10
                
                if (eventStatus.condition1) {
                    node1Color = '#28A745' // 綠色：條件滿足
                    node1Size = 12
                } else {
                    node1Color = '#FFC107' // 橙色：條件不滿足
                    node1Size = 8
                }
                
                datasets.push({
                    label: `Distance 1 Node (${currentDistance1.toFixed(0)}m)`,
                    data: node1Data,
                    borderColor: node1Color,
                    backgroundColor: node1Color,
                    borderWidth: 3,
                    fill: false,
                    pointRadius: node1Size,
                    pointHoverRadius: node1Size + 4,
                    pointStyle: 'triangle',
                    showLine: false,
                    tension: 0,
                })
                
                // 節點2（距離到Ref2）
                const node2Data = generateDistanceNode(currentTime, currentDistance2)
                let node2Color = '#FD7E14' // 預設橙色
                let node2Size = 10
                
                if (eventStatus.condition2) {
                    node2Color = '#007BFF' // 藍色：條件滿足
                    node2Size = 12
                } else {
                    node2Color = '#DC3545' // 紅色：條件不滿足
                    node2Size = 8
                }
                
                datasets.push({
                    label: `Distance 2 Node (${currentDistance2.toFixed(0)}m)`,
                    data: node2Data,
                    borderColor: node2Color,
                    backgroundColor: node2Color,
                    borderWidth: 3,
                    fill: false,
                    pointRadius: node2Size,
                    pointHoverRadius: node2Size + 4,
                    pointStyle: 'rect',
                    showLine: false,
                    tension: 0,
                })
                
                // Event D1 狀態節點（中間位置）
                if (eventStatus.isTriggered) {
                    const eventNodeData = [{ x: currentTime, y: (currentDistance1 + currentDistance2) / 2 }]
                    datasets.push({
                        label: 'Event D1 TRIGGERED',
                        data: eventNodeData,
                        borderColor: '#FF6B35',
                        backgroundColor: '#FF6B35',
                        borderWidth: 4,
                        fill: false,
                        pointRadius: 16,
                        pointHoverRadius: 20,
                        pointStyle: 'star',
                        showLine: false,
                        tension: 0,
                    })
                }
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
                                    color: 'white', // 預設顏色
                                    font: { size: 12 },
                                    filter: function (legendItem, chartData) {
                                        // 隱藏遲滯線圖例，避免過於複雜
                                        const label = legendItem.text || ''
                                        return !label.includes('Hys')
                                    },
                                },
                            },
                            title: {
                                display: true,
                                text: 'Event D1: 距離雙門檻事件 (3GPP TS 38.331)',
                                font: {
                                    size: 16,
                                    weight: 'bold',
                                },
                                color: 'white',
                                padding: 20,
                            },
                        },
                        scales: {
                            x: {
                                type: 'linear',
                                title: {
                                    display: true,
                                    text: 'Time (s)',
                                    color: 'white', // 預設顏色
                                    font: { size: 14 },
                                },
                                ticks: { color: 'white' }, // 預設顏色
                                grid: { color: 'rgba(255, 255, 255, 0.1)' }, // 預設顏色
                                min: 0,
                                max: 100,
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Distance (m)',
                                    color: 'white', // 預設顏色
                                    font: { size: 14 },
                                },
                                ticks: { color: 'white' }, // 預設顏色
                                grid: { color: 'rgba(255, 255, 255, 0.1)' }, // 預設顏色
                                min: 0,
                                max: 900,
                            },
                        },
                    },
                })

                isInitialized.current = true
            } catch (error) {
                console.error('❌ [PureD1Chart] 圖表創建失敗:', error)
            }

            // 清理函數
            return () => {
                if (chartRef.current) {
                    chartRef.current.destroy()
                    chartRef.current = null
                    isInitialized.current = false
                    }
            }
        }, []) // 只在掛載時執行

        // 更新參數和主題 - 不重新創建圖表
        useEffect(() => {
            if (!chartRef.current || !isInitialized.current) {
                return
            }
            const chart = chartRef.current


            // 處理 showThresholdLines 變化和參數更新
            if (showThresholdLines) {
                const timePoints = distance1Points.map((point) => point.x)

                // 重新計算門檻線數據
                const thresh1Data = timePoints.map((time) => ({
                    x: time,
                    y: thresh1,
                }))
                const thresh2Data = timePoints.map((time) => ({
                    x: time,
                    y: thresh2,
                }))
                const thresh1HysUpperData = timePoints.map((time) => ({
                    x: time,
                    y: thresh1 + hysteresis,
                }))
                const thresh1HysLowerData = timePoints.map((time) => ({
                    x: time,
                    y: thresh1 - hysteresis,
                }))
                const thresh2HysUpperData = timePoints.map((time) => ({
                    x: time,
                    y: thresh2 + hysteresis,
                }))
                const thresh2HysLowerData = timePoints.map((time) => ({
                    x: time,
                    y: thresh2 - hysteresis,
                }))

                // 確保有足夠的數據集
                if (chart.data.datasets.length === 2) {
                    // 添加門檻線數據集
                    chart.data.datasets.push(
                        {
                            label: 'Thresh1 (Ref1 Threshold)',
                            data: thresh1Data,
                            borderColor: currentTheme.thresh1Line,
                            backgroundColor: 'transparent',
                            borderDash: [10, 5],
                            borderWidth: 2,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>,
                        {
                            label: 'Thresh2 (Ref2 Threshold)',
                            data: thresh2Data,
                            borderColor: currentTheme.thresh2Line,
                            backgroundColor: 'transparent',
                            borderDash: [10, 5],
                            borderWidth: 2,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>,
                        {
                            label: 'Thresh1 + Hys',
                            data: thresh1HysUpperData,
                            borderColor: currentTheme.hysteresisLine,
                            backgroundColor: 'transparent',
                            borderDash: [5, 3],
                            borderWidth: 1,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>,
                        {
                            label: 'Thresh1 - Hys',
                            data: thresh1HysLowerData,
                            borderColor: currentTheme.hysteresisLine,
                            backgroundColor: 'transparent',
                            borderDash: [5, 3],
                            borderWidth: 1,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>,
                        {
                            label: 'Thresh2 + Hys',
                            data: thresh2HysUpperData,
                            borderColor: currentTheme.hysteresisLine,
                            backgroundColor: 'transparent',
                            borderDash: [5, 3],
                            borderWidth: 1,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>,
                        {
                            label: 'Thresh2 - Hys',
                            data: thresh2HysLowerData,
                            borderColor: currentTheme.hysteresisLine,
                            backgroundColor: 'transparent',
                            borderDash: [5, 3],
                            borderWidth: 1,
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                        } as Record<string, unknown>
                    )
                } else {
                    // 更新現有門檻線數據
                    if (chart.data.datasets[2])
                        chart.data.datasets[2].data = thresh1Data
                    if (chart.data.datasets[3])
                        chart.data.datasets[3].data = thresh2Data
                    if (chart.data.datasets[4])
                        chart.data.datasets[4].data = thresh1HysUpperData
                    if (chart.data.datasets[5])
                        chart.data.datasets[5].data = thresh1HysLowerData
                    if (chart.data.datasets[6])
                        chart.data.datasets[6].data = thresh2HysUpperData
                    if (chart.data.datasets[7])
                        chart.data.datasets[7].data = thresh2HysLowerData
                }
            } else {
                // 隱藏門檻線，只保留距離曲線
                if (chart.data.datasets.length > 2) {
                    chart.data.datasets = chart.data.datasets.slice(0, 2)
                }
            }

            // 更新顏色主題
            chart.data.datasets[0].borderColor = currentTheme.distance1Line
            chart.data.datasets[1].borderColor = currentTheme.distance2Line
            if (chart.data.datasets[2])
                chart.data.datasets[2].borderColor = currentTheme.thresh1Line
            if (chart.data.datasets[3])
                chart.data.datasets[3].borderColor = currentTheme.thresh2Line
            if (chart.data.datasets[4])
                chart.data.datasets[4].borderColor = currentTheme.hysteresisLine
            if (chart.data.datasets[5])
                chart.data.datasets[5].borderColor = currentTheme.hysteresisLine
            if (chart.data.datasets[6])
                chart.data.datasets[6].borderColor = currentTheme.hysteresisLine
            if (chart.data.datasets[7])
                chart.data.datasets[7].borderColor = currentTheme.hysteresisLine

            // 更新圖表選項的顏色 - 安全訪問
            try {
                if (chart.options?.plugins?.legend?.labels) {
                    chart.options.plugins.legend.labels.color = currentTheme.text
                }
                if (chart.options?.plugins?.legend) {
                    chart.options.plugins.legend.display = showThresholdLines
                }
                if (chart.options?.plugins?.title) {
                    chart.options.plugins.title.color = currentTheme.title
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
                console.warn('⚠️ [PureD1Chart] 更新圖表選項時發生錯誤:', error)
            }

            // 更新圖表 - 使用 'none' 避免動畫
            try {
                chart.update('none')
                } catch (error) {
                console.error('❌ [PureD1Chart] 圖表更新失敗:', error)
                // 嘗試重新初始化圖表
                console.log('🔄 [PureD1Chart] 嘗試重新初始化圖表')
                chart.destroy()
                chartRef.current = null
                isInitialized.current = false
            }
        }, [thresh1, thresh2, hysteresis, isDarkTheme, showThresholdLines]) // 移除 currentTime，避免動畫時頻繁觸發

        // 單獨處理 currentTime 變化 - 只更新動畫相關元素，避免重複計算
        useEffect(() => {
            if (!chartRef.current || !isInitialized.current || currentTime === 0) {
                return
            }
            
            const chart = chartRef.current
            
            try {
                // 確保圖表實例存在且已初始化
                if (!chart.data || !chart.data.datasets) {
                    console.warn('⚠️ [PureD1Chart] 圖表數據未初始化，跳過動畫更新')
                    return
                }
                
                // 只更新動畫相關的數據集（游標和節點）
                const expectedCursorIndex = showThresholdLines ? 8 : 2
                const expectedNode1Index = expectedCursorIndex + 1
                const expectedNode2Index = expectedCursorIndex + 2
                const expectedEventNodeIndex = expectedCursorIndex + 3
                
                const cursorData = generateCurrentTimeCursor(currentTime)
                const currentDistance1 = getCurrentDistance(currentTime, distance1Points)
                const currentDistance2 = getCurrentDistance(currentTime, distance2Points)
                const eventStatus = checkD1EventTrigger(currentDistance1, currentDistance2, thresh1, thresh2, hysteresis)
                
                // 添加游標數據集（如果不存在）
                if (!chart.data.datasets[expectedCursorIndex]) {
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
                    } as any)
                } else {
                    // 更新游標
                    chart.data.datasets[expectedCursorIndex].data = cursorData
                    chart.data.datasets[expectedCursorIndex].label = `Current Time: ${currentTime.toFixed(1)}s`
                }
                
                // 添加/更新節點1
                if (!chart.data.datasets[expectedNode1Index]) {
                    const node1Color = eventStatus.condition1 ? '#28A745' : '#FFC107'
                    const node1Size = eventStatus.condition1 ? 12 : 8
                    chart.data.datasets.push({
                        label: `Distance 1 Node (${currentDistance1.toFixed(0)}m)`,
                        data: generateDistanceNode(currentTime, currentDistance1),
                        borderColor: node1Color,
                        backgroundColor: node1Color,
                        borderWidth: 3,
                        fill: false,
                        pointRadius: node1Size,
                        pointHoverRadius: node1Size + 4,
                        pointStyle: 'triangle',
                        showLine: false,
                        tension: 0,
                    } as any)
                } else {
                    chart.data.datasets[expectedNode1Index].data = generateDistanceNode(currentTime, currentDistance1)
                }
                
                // 添加/更新節點2
                if (!chart.data.datasets[expectedNode2Index]) {
                    const node2Color = eventStatus.condition2 ? '#007BFF' : '#DC3545'
                    const node2Size = eventStatus.condition2 ? 12 : 8
                    chart.data.datasets.push({
                        label: `Distance 2 Node (${currentDistance2.toFixed(0)}m)`,
                        data: generateDistanceNode(currentTime, currentDistance2),
                        borderColor: node2Color,
                        backgroundColor: node2Color,
                        borderWidth: 3,
                        fill: false,
                        pointRadius: node2Size,
                        pointHoverRadius: node2Size + 4,
                        pointStyle: 'rect',
                        showLine: false,
                        tension: 0,
                    } as any)
                } else {
                    chart.data.datasets[expectedNode2Index].data = generateDistanceNode(currentTime, currentDistance2)
                }
                
                // 添加/更新事件節點
                if (eventStatus.isTriggered) {
                    const eventNodeData = generateEventNode(currentTime, Math.min(currentDistance1, currentDistance2))
                    if (!chart.data.datasets[expectedEventNodeIndex]) {
                        chart.data.datasets.push({
                            label: 'Event D1 TRIGGERED',
                            data: eventNodeData,
                            borderColor: '#FF6B35',
                            backgroundColor: '#FF6B35',
                            borderWidth: 4,
                            fill: false,
                            pointRadius: 16,
                            pointHoverRadius: 20,
                            pointStyle: 'star',
                            showLine: false,
                            tension: 0,
                        } as any)
                    } else {
                        chart.data.datasets[expectedEventNodeIndex].data = eventNodeData
                    }
                } else {
                    // 如果事件未觸發，清空事件節點數據
                    if (chart.data.datasets[expectedEventNodeIndex]) {
                        chart.data.datasets[expectedEventNodeIndex].data = []
                    }
                }
                
                // 安全的圖表更新
                if (chart.update && typeof chart.update === 'function') {
                    chart.update('none')
                } else {
                    console.warn('⚠️ [PureD1Chart] chart.update 方法不可用')
                }
            } catch (error) {
                console.warn('⚠️ [PureD1Chart] 動畫更新時發生錯誤:', error)
                // 如果更新失敗，不影響主要功能
            }
        }, [currentTime, showThresholdLines, currentTheme]) // 添加必要依賴

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
                <canvas
                    ref={canvasRef}
                    style={{ width: '100%', height: '100%' }}
                />
            </div>
        )
    }
)

PureD1Chart.displayName = 'PureD1Chart'

export default PureD1Chart
