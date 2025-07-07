/**
 * A4事件圖表插件
 * 基於現有PureA4Chart的插件化版本
 */

import { ChartPlugin } from '../ChartRegistry'
import { ChartConfiguration } from 'chart.js/auto'

// A4圖表的數據點（從PureA4Chart移植）
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

// A4圖表配置工廠函數
const createA4ChartConfig = (props: {
    threshold?: number
    hysteresis?: number
    currentTime?: number
    showThresholdLines?: boolean
    isDarkTheme?: boolean
}): ChartConfiguration => {
    const {
        threshold = -70,
        hysteresis = 3,
        currentTime = 0,
        showThresholdLines = true,
        isDarkTheme = true
    } = props

    // 主題配色
    const colors = {
        dark: {
            rsrpLine: '#007bff',
            thresholdLine: '#E74C3C',
            hysteresisLine: 'rgba(231, 76, 60, 0.6)',
            currentTimeLine: '#ff6b35',
            title: 'white',
            text: 'white',
            grid: 'rgba(255, 255, 255, 0.1)',
        },
        light: {
            rsrpLine: '#0066CC',
            thresholdLine: '#D32F2F',
            hysteresisLine: '#D32F2F',
            currentTimeLine: '#ff6b35',
            title: 'black',
            text: '#333333',
            grid: 'rgba(0, 0, 0, 0.1)',
        }
    }

    const currentTheme = isDarkTheme ? colors.dark : colors.light

    // 基礎數據集
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

    // 添加閾值線
    if (showThresholdLines) {
        const thresholdData = dataPoints.map(point => ({ x: point.x, y: threshold }))
        const upperThresholdData = dataPoints.map(point => ({ x: point.x, y: threshold + hysteresis }))
        const lowerThresholdData = dataPoints.map(point => ({ x: point.x, y: threshold - hysteresis }))

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
        const cursorData = [
            { x: currentTime, y: -95 },
            { x: currentTime, y: -40 },
        ]

        datasets.push({
            label: `Current Time: ${currentTime.toFixed(1)}s`,
            data: cursorData,
            borderColor: currentTheme.currentTimeLine,
            backgroundColor: 'transparent',
            borderWidth: 3,
            fill: false,
            pointRadius: 0,
            tension: 0,
            borderDash: [5, 5],
        })
    }

    return {
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
    }
}

// A4圖表插件定義
const A4EventChartPlugin: ChartPlugin = {
    id: 'a4-event-chart',
    name: 'A4事件圖表',
    description: 'LTE/5G A4測量事件可視化圖表',
    version: '1.0.0',
    chartType: 'line',
    configFactory: createA4ChartConfig,
    defaultProps: {
        threshold: -70,
        hysteresis: 3,
        currentTime: 0,
        showThresholdLines: true,
        isDarkTheme: true
    },
    isEnabled: true,
    dependencies: []
}

export default A4EventChartPlugin