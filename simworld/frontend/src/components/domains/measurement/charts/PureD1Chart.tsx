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
// 距離1: UE 到 referenceLocation1 的距離 (公尺)
const distance1Points = [
    { x: 0, y: 800 },
    { x: 5, y: 750 },
    { x: 10, y: 700 },
    { x: 15, y: 650 },
    { x: 20, y: 600 },
    { x: 25, y: 550 },
    { x: 30, y: 500 },
    { x: 35, y: 450 },
    { x: 40, y: 400 },
    { x: 45, y: 350 },
    { x: 50, y: 320 },
    { x: 55, y: 300 },
    { x: 60, y: 290 },
    { x: 65, y: 300 },
    { x: 70, y: 320 },
    { x: 75, y: 350 },
    { x: 80, y: 400 },
    { x: 85, y: 450 },
    { x: 90, y: 500 },
    { x: 95, y: 550 },
]

// 距離2: UE 到 referenceLocation2 的距離 (公尺)  
const distance2Points = [
    { x: 0, y: 100 },
    { x: 5, y: 120 },
    { x: 10, y: 140 },
    { x: 15, y: 160 },
    { x: 20, y: 180 },
    { x: 25, y: 200 },
    { x: 30, y: 220 },
    { x: 35, y: 240 },
    { x: 40, y: 260 },
    { x: 45, y: 280 },
    { x: 50, y: 300 },
    { x: 55, y: 320 },
    { x: 60, y: 300 },
    { x: 65, y: 280 },
    { x: 70, y: 260 },
    { x: 75, y: 240 },
    { x: 80, y: 220 },
    { x: 85, y: 200 },
    { x: 90, y: 180 },
    { x: 95, y: 160 },
]

interface PureD1ChartProps {
    width?: number
    height?: number
    thresh1?: number // distanceThreshFromReference1 (meters)
    thresh2?: number // distanceThreshFromReference2 (meters) 
    hysteresis?: number // hysteresisLocation (meters)
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
                    distance1Line: '#28A745', // 綠色：距離1
                    distance2Line: '#FD7E14', // 橙色：距離2  
                    thresh1Line: '#DC3545', // 紅色：門檻1
                    thresh2Line: '#007BFF', // 藍色：門檻2
                    hysteresisLine: 'rgba(108, 117, 125, 0.6)', // 灰色：遲滯線
                    title: '#E74C3C',
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
                    title: '#D32F2F',
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

            console.log('🎯 [PureD1Chart] 初始化 useEffect 觸發')

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
                const timePoints = distance1Points.map(point => point.x)
                
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

            try {
                console.log('🔧 [PureD1Chart] 開始創建圖表')
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
                                    filter: function(legendItem, chartData) {
                                        // 隱藏遲滯線圖例，避免過於複雜
                                        const label = legendItem.text || '';
                                        return !label.includes('Hys');
                                    }
                                },
                            },
                            title: { 
                                display: true,
                                text: 'Event D1: 距離雙門檻事件',
                                color: 'white',
                                font: { size: 16 }
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
                console.log('✅ [PureD1Chart] 圖表創建成功')
            } catch (error) {
                console.error('❌ [PureD1Chart] 圖表創建失敗:', error)
            }

            // 清理函數
            return () => {
                console.log('🗑️ [PureD1Chart] 清理函數執行')
                if (chartRef.current) {
                    chartRef.current.destroy()
                    chartRef.current = null
                    isInitialized.current = false
                    console.log('🗑️ [PureD1Chart] 圖表已銷毀')
                }
            }
        }, []) // 只在掛載時執行

        // 更新參數和主題 - 不重新創建圖表
        useEffect(() => {
            if (!chartRef.current || !isInitialized.current) {
                return
            }
            const chart = chartRef.current

            console.log('🔄 [PureD1Chart] 更新圖表參數')

            // 處理 showThresholdLines 變化和參數更新
            if (showThresholdLines) {
                const timePoints = distance1Points.map(point => point.x)
                
                // 重新計算門檻線數據
                const thresh1Data = timePoints.map((time) => ({ x: time, y: thresh1 }))
                const thresh2Data = timePoints.map((time) => ({ x: time, y: thresh2 }))
                const thresh1HysUpperData = timePoints.map((time) => ({ x: time, y: thresh1 + hysteresis }))
                const thresh1HysLowerData = timePoints.map((time) => ({ x: time, y: thresh1 - hysteresis }))
                const thresh2HysUpperData = timePoints.map((time) => ({ x: time, y: thresh2 + hysteresis }))
                const thresh2HysLowerData = timePoints.map((time) => ({ x: time, y: thresh2 - hysteresis }))

                // 確保有足夠的數據集
                if (chart.data.datasets.length === 2) {
                    // 添加門檻線數據集
                    chart.data.datasets.push(
                        { label: 'Thresh1 (Ref1 Threshold)', data: thresh1Data, borderColor: currentTheme.thresh1Line, backgroundColor: 'transparent', borderDash: [10, 5], borderWidth: 2, fill: false, tension: 0, pointRadius: 0 } as any,
                        { label: 'Thresh2 (Ref2 Threshold)', data: thresh2Data, borderColor: currentTheme.thresh2Line, backgroundColor: 'transparent', borderDash: [10, 5], borderWidth: 2, fill: false, tension: 0, pointRadius: 0 } as any,
                        { label: 'Thresh1 + Hys', data: thresh1HysUpperData, borderColor: currentTheme.hysteresisLine, backgroundColor: 'transparent', borderDash: [5, 3], borderWidth: 1, fill: false, tension: 0, pointRadius: 0 } as any,
                        { label: 'Thresh1 - Hys', data: thresh1HysLowerData, borderColor: currentTheme.hysteresisLine, backgroundColor: 'transparent', borderDash: [5, 3], borderWidth: 1, fill: false, tension: 0, pointRadius: 0 } as any,
                        { label: 'Thresh2 + Hys', data: thresh2HysUpperData, borderColor: currentTheme.hysteresisLine, backgroundColor: 'transparent', borderDash: [5, 3], borderWidth: 1, fill: false, tension: 0, pointRadius: 0 } as any,
                        { label: 'Thresh2 - Hys', data: thresh2HysLowerData, borderColor: currentTheme.hysteresisLine, backgroundColor: 'transparent', borderDash: [5, 3], borderWidth: 1, fill: false, tension: 0, pointRadius: 0 } as any
                    )
                } else {
                    // 更新現有門檻線數據
                    if (chart.data.datasets[2]) chart.data.datasets[2].data = thresh1Data
                    if (chart.data.datasets[3]) chart.data.datasets[3].data = thresh2Data
                    if (chart.data.datasets[4]) chart.data.datasets[4].data = thresh1HysUpperData
                    if (chart.data.datasets[5]) chart.data.datasets[5].data = thresh1HysLowerData
                    if (chart.data.datasets[6]) chart.data.datasets[6].data = thresh2HysUpperData
                    if (chart.data.datasets[7]) chart.data.datasets[7].data = thresh2HysLowerData
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
            if (chart.data.datasets[2]) chart.data.datasets[2].borderColor = currentTheme.thresh1Line
            if (chart.data.datasets[3]) chart.data.datasets[3].borderColor = currentTheme.thresh2Line
            if (chart.data.datasets[4]) chart.data.datasets[4].borderColor = currentTheme.hysteresisLine
            if (chart.data.datasets[5]) chart.data.datasets[5].borderColor = currentTheme.hysteresisLine
            if (chart.data.datasets[6]) chart.data.datasets[6].borderColor = currentTheme.hysteresisLine
            if (chart.data.datasets[7]) chart.data.datasets[7].borderColor = currentTheme.hysteresisLine

            // 更新圖表選項的顏色
            if (chart.options.plugins?.legend?.labels) {
                chart.options.plugins.legend.labels.color = currentTheme.text
            }
            if (chart.options.plugins?.legend) {
                chart.options.plugins.legend.display = showThresholdLines
            }
            if (chart.options.plugins?.title) {
                chart.options.plugins.title.color = currentTheme.title
            }
            if ((chart.options.scales?.x as any)?.title) {
                ;(chart.options.scales.x as any).title.color = currentTheme.text
            }
            if ((chart.options.scales?.x as any)?.ticks) {
                ;(chart.options.scales.x as any).ticks.color = currentTheme.text
            }
            if ((chart.options.scales?.x as any)?.grid) {
                ;(chart.options.scales.x as any).grid.color = currentTheme.grid
            }
            if ((chart.options.scales?.y as any)?.title) {
                ;(chart.options.scales.y as any).title.color = currentTheme.text
            }
            if ((chart.options.scales?.y as any)?.ticks) {
                ;(chart.options.scales.y as any).ticks.color = currentTheme.text
            }
            if ((chart.options.scales?.y as any)?.grid) {
                ;(chart.options.scales.y as any).grid.color = currentTheme.grid
            }

            // 更新圖表 - 使用 'none' 避免動畫
            chart.update('none')
            console.log('✅ [PureD1Chart] 圖表更新完成')
        }, [thresh1, thresh2, hysteresis, currentTheme, showThresholdLines])

        return (
            <div
                style={{
                    width: '100%',
                    height: '100%',
                    minHeight: '400px',
                    maxHeight: '80vh',
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