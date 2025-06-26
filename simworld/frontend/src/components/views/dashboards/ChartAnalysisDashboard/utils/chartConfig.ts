/* eslint-disable @typescript-eslint/no-explicit-any */
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    LogarithmicScale,
    BarElement,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    Filler,
    RadialLinearScale,
} from 'chart.js'

// 註冊 Chart.js 組件
export const registerChartComponents = () => {
    ChartJS.register(
        CategoryScale,
        LinearScale,
        LogarithmicScale,
        BarElement,
        LineElement,
        PointElement,
        Title,
        Tooltip,
        Legend,
        ArcElement,
        Filler,
        RadialLinearScale
    )
}

// 配置全域 Chart.js 預設值
export const configureChartDefaults = () => {
    ChartJS.defaults.color = 'white'
    ChartJS.defaults.font.size = 16
    ChartJS.defaults.plugins.legend.labels.color = 'white'
    ChartJS.defaults.plugins.legend.labels.font = { size: 16 }
    ChartJS.defaults.plugins.title.color = 'white'
    ChartJS.defaults.plugins.title.font = { size: 20, weight: 'bold' as const }
    ChartJS.defaults.plugins.tooltip.titleColor = 'white'
    ChartJS.defaults.plugins.tooltip.bodyColor = 'white'
    ChartJS.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.9)'
    ChartJS.defaults.plugins.tooltip.titleFont = { size: 16 }
    ChartJS.defaults.plugins.tooltip.bodyFont = { size: 15 }
    ChartJS.defaults.scale.ticks.color = 'white'
    ChartJS.defaults.scale.ticks.font = { size: 14 }
    ChartJS.defaults.locale = 'en-US'

    // 配置元素樣式
    ;(ChartJS.defaults as any).elements = {
        ...((ChartJS.defaults as any).elements || {}),
        arc: {
            ...((ChartJS.defaults as any).elements?.arc || {}),
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
        bar: {
            ...((ChartJS.defaults as any).elements?.bar || {}),
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
        line: {
            ...((ChartJS.defaults as any).elements?.line || {}),
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
    }

    // 配置坐標軸
    try {
        ;(ChartJS.defaults.scale as any).title = {
            color: 'white',
            font: { size: 16, weight: 'bold' as const },
        }
    } catch (e) {
        console.warn('Could not set scale title defaults:', e)
    }
    ChartJS.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.2)'
}

// 創建互動式圖表配置
export const createInteractiveChartOptions = (
    title: string,
    yAxisLabel: string = '',
    xAxisLabel: string = ''
) => ({
    responsive: true,
    maintainAspectRatio: false,
    onClick: (event: any, elements: any[]) => {
        if (elements.length > 0) {
            const dataIndex = elements[0].index
            const datasetIndex = elements[0].datasetIndex
            
            // 觸發自定義事件
            const customEvent = new CustomEvent('chartElementClick', {
                detail: { dataIndex, datasetIndex, title }
            })
            window.dispatchEvent(customEvent)
        }
    },
    plugins: {
        title: {
            display: !!title,
            text: title,
            color: 'white',
            font: { size: 20, weight: 'bold' as const },
        },
        legend: {
            position: 'top' as const,
            labels: {
                color: 'white',
                font: { size: 16, weight: 'bold' as const },
            },
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            titleColor: 'white',
            bodyColor: 'white',
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
        },
    },
    scales: {
        x: {
            title: {
                display: !!xAxisLabel,
                text: xAxisLabel,
                color: 'white',
                font: { size: 16, weight: 'bold' as const },
            },
            ticks: {
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
            },
            grid: { color: 'rgba(255, 255, 255, 0.2)' },
        },
        y: {
            title: {
                display: !!yAxisLabel,
                text: yAxisLabel,
                color: 'white',
                font: { size: 16, weight: 'bold' as const },
            },
            ticks: {
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
            },
            grid: { color: 'rgba(255, 255, 255, 0.2)' },
        },
    },
})

// 雷達圖專用配置
export const createRadarChartOptions = (title: string) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        title: {
            display: !!title,
            text: title,
            color: 'white',
            font: { size: 20, weight: 'bold' as const },
        },
        legend: {
            position: 'top' as const,
            labels: {
                color: 'white',
                font: { size: 16 },
            },
        },
    },
    scales: {
        r: {
            angleLines: { color: 'rgba(255, 255, 255, 0.2)' },
            grid: { color: 'rgba(255, 255, 255, 0.2)' },
            pointLabels: {
                color: 'white',
                font: { size: 14, weight: 'bold' as const },
            },
            ticks: {
                color: 'white',
                font: { size: 12 },
                stepSize: 1,
                backdropColor: 'transparent',
            },
        },
    },
})

// 圓餅圖專用配置
export const createPieChartOptions = (title: string) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        title: {
            display: !!title,
            text: title,
            color: 'white',
            font: { size: 20, weight: 'bold' as const },
        },
        legend: {
            position: 'bottom' as const,
            labels: {
                color: 'white',
                font: { size: 14 },
                padding: 20,
            },
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            titleColor: 'white',
            bodyColor: 'white',
            callbacks: {
                label: (context: any) => {
                    const label = context.label || ''
                    const value = context.parsed || 0
                    const percentage = ((value / context.dataset.data.reduce((a: number, b: number) => a + b, 0)) * 100).toFixed(1)
                    return `${label}: ${value} (${percentage}%)`
                }
            }
        },
    },
})

// 對數軸配置
export const createLogScaleOptions = (title: string, yAxisLabel: string) => ({
    ...createInteractiveChartOptions(title, yAxisLabel),
    scales: {
        ...createInteractiveChartOptions(title, yAxisLabel).scales,
        y: {
            ...createInteractiveChartOptions(title, yAxisLabel).scales.y,
            type: 'logarithmic' as const,
            min: 1,
            max: 10000,
        },
    },
})

// 預設顏色調色盤
export const COLOR_PALETTE = {
    primary: ['rgba(255, 99, 132, 0.8)', 'rgba(54, 162, 235, 0.8)', 'rgba(255, 206, 86, 0.8)', 'rgba(75, 192, 192, 0.8)'],
    border: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)', 'rgba(75, 192, 192, 1)'],
    extended: [
        'rgba(153, 102, 255, 0.8)',
        'rgba(255, 159, 64, 0.8)',
        'rgba(199, 199, 199, 0.8)',
        'rgba(83, 102, 255, 0.8)',
        'rgba(255, 99, 255, 0.8)',
        'rgba(54, 255, 162, 0.8)',
    ],
} 