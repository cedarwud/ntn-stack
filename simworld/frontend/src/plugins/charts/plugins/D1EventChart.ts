/**
 * D1事件圖表插件
 * 基於現有PureD1Chart的插件化版本
 */

import { ChartPlugin } from '../ChartRegistry'
import { ChartConfiguration } from 'chart.js/auto'

// D1圖表的數據點（從PureD1Chart移植）
const dataPoints = [
    { x: 1.48, y: -46.23 },
    { x: 3.65, y: -46.87 },
    { x: 5.82, y: -47.94 },
    { x: 7.99, y: -49.32 },
    { x: 10.17, y: -50.89 },
    { x: 12.34, y: -52.71 },
    { x: 14.51, y: -54.85 },
    { x: 16.68, y: -57.42 },
    { x: 18.66, y: -60.58 },
    { x: 20.24, y: -64.25 },
    { x: 21.32, y: -68.12 },
    { x: 22.02, y: -72.31 },
    { x: 22.21, y: -76.58 },
    { x: 22.81, y: -80.84 },
    { x: 23.79, y: -84.91 },
    { x: 25.4, y: -88.73 },
    { x: 27.35, y: -92.25 },
    { x: 29.72, y: -95.42 },
    { x: 31.4, y: -97.15 },
    { x: 35.25, y: -101.23 },
    { x: 37.42, y: -102.87 },
    { x: 39.59, y: -104.12 },
    { x: 41.76, y: -104.89 },
    { x: 43.94, y: -105.34 },
    { x: 46.11, y: -105.18 },
    { x: 48.28, y: -104.95 },
    { x: 50.45, y: -104.58 },
    { x: 52.63, y: -104.12 },
    { x: 54.8, y: -103.51 },
    { x: 56.97, y: -102.84 },
    { x: 58.65, y: -102.31 },
    { x: 61.51, y: -101.02 },
    { x: 63.69, y: -100.08 },
    { x: 65.86, y: -98.89 },
    { x: 67.83, y: -97.58 },
    { x: 70.2, y: -95.72 },
    { x: 72.37, y: -93.68 },
    { x: 74.38, y: -91.12 },
    { x: 75.53, y: -88.74 },
    { x: 76.13, y: -83.21 },
    { x: 77.31, y: -79.45 },
    { x: 78.99, y: -76.12 },
    { x: 81.06, y: -73.58 },
    { x: 83.24, y: -71.42 },
    { x: 85.41, y: -69.89 },
    { x: 87.58, y: -68.74 },
    { x: 89.75, y: -67.89 },
    { x: 91.23, y: -67.54 },
]

// D1圖表配置工廠函數
const createD1ChartConfig = (props: {
    threshold?: number
    hysteresis?: number
    currentTime?: number
    showThresholdLines?: boolean
    isDarkTheme?: boolean
}): ChartConfiguration => {
    const {
        threshold = -85,
        hysteresis = 2,
        currentTime = 0,
        showThresholdLines = true,
        isDarkTheme = true
    } = props

    // 主題配色
    const colors = {
        dark: {
            rsrpLine: '#28a745',
            thresholdLine: '#ffc107',
            hysteresisLine: 'rgba(255, 193, 7, 0.6)',
            currentTimeLine: '#ff6b35',
            title: 'white',
            text: 'white',
            grid: 'rgba(255, 255, 255, 0.1)',
        },
        light: {
            rsrpLine: '#198754',
            thresholdLine: '#ffca2c',
            hysteresisLine: '#ffca2c',
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
            label: 'Serving Cell RSRP',
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
                label: 'D1-Threshold',
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
            { x: currentTime, y: -110 },
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
                    text: 'Event D1: 服務基站低於門檻事件 (3GPP TS 38.331)',
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
                    min: -115,
                    max: -40,
                    reverse: true,
                },
            },
        },
    }
}

// D1圖表插件定義
const D1EventChartPlugin: ChartPlugin = {
    id: 'd1-event-chart',
    name: 'D1事件圖表',
    description: 'LTE/5G D1測量事件可視化圖表',
    version: '1.0.0',
    chartType: 'line',
    configFactory: createD1ChartConfig,
    defaultProps: {
        threshold: -85,
        hysteresis: 2,
        currentTime: 0,
        showThresholdLines: true,
        isDarkTheme: true
    },
    isEnabled: true,
    dependencies: []
}

export default D1EventChartPlugin