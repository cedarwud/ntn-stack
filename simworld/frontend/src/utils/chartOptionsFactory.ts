/**
 * 圖表選項工廠
 * 
 * 提供各種圖表類型的標準化選項配置
 * 減少重複代碼，提供一致的圖表外觀
 */
import { ChartOptions } from 'chart.js'

export interface ChartConfig {
    title?: string
    responsive?: boolean
    maintainAspectRatio?: boolean
    showLegend?: boolean
    showGrid?: boolean
    backgroundColor?: string
    borderColor?: string
    tension?: number
    fill?: boolean
    scales?: {
        x?: {
            display?: boolean
            title?: { display: boolean; text: string }
        }
        y?: {
            display?: boolean
            title?: { display: boolean; text: string }
            beginAtZero?: boolean
            type?: 'linear' | 'logarithmic'
        }
    }
    plugins?: {
        tooltip?: {
            enabled?: boolean
            callbacks?: Record<string, unknown>
        }
        legend?: {
            display?: boolean
            position?: 'top' | 'bottom' | 'left' | 'right'
        }
    }
}

/**
 * 建立基礎圖表選項
 */
const createBaseOptions = (config: ChartConfig): ChartOptions => ({
    responsive: config.responsive ?? true,
    maintainAspectRatio: config.maintainAspectRatio ?? false,
    plugins: {
        title: {
            display: !!config.title,
            text: config.title || '',
        },
        legend: {
            display: config.showLegend ?? true,
            position: config.plugins?.legend?.position ?? 'top',
        },
        tooltip: {
            enabled: config.plugins?.tooltip?.enabled ?? true,
            callbacks: config.plugins?.tooltip?.callbacks,
        },
    },
    scales: {
        x: {
            display: config.scales?.x?.display ?? true,
            title: config.scales?.x?.title,
            grid: {
                display: config.showGrid ?? true,
            },
        },
        y: {
            display: config.scales?.y?.display ?? true,
            title: config.scales?.y?.title,
            beginAtZero: config.scales?.y?.beginAtZero ?? true,
            type: config.scales?.y?.type ?? 'linear',
            grid: {
                display: config.showGrid ?? true,
            },
        },
    },
})

/**
 * 建立線性圖表選項
 */
export const createLineChartOptions = (config: ChartConfig = {}): ChartOptions => {
    const baseOptions = createBaseOptions(config)
    
    return {
        ...baseOptions,
        elements: {
            line: {
                tension: config.tension ?? 0.3,
                borderColor: config.borderColor ?? 'rgba(75, 192, 192, 1)',
                backgroundColor: config.backgroundColor ?? 'rgba(75, 192, 192, 0.2)',
                fill: config.fill ?? false,
            },
            point: {
                radius: 4,
                hoverRadius: 6,
            },
        },
        interaction: {
            intersect: false,
            mode: 'index',
        },
    }
}

/**
 * 建立長條圖選項
 */
export const createBarChartOptions = (config: ChartConfig = {}): ChartOptions => {
    const baseOptions = createBaseOptions(config)
    
    return {
        ...baseOptions,
        elements: {
            bar: {
                backgroundColor: config.backgroundColor ?? 'rgba(54, 162, 235, 0.8)',
                borderColor: config.borderColor ?? 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
            },
        },
    }
}

/**
 * 建立雷達圖選項
 */
export const createRadarChartOptions = (config: ChartConfig = {}): ChartOptions => {
    return {
        responsive: config.responsive ?? true,
        maintainAspectRatio: config.maintainAspectRatio ?? false,
        plugins: {
            title: {
                display: !!config.title,
                text: config.title || '',
            },
            legend: {
                display: config.showLegend ?? true,
                position: config.plugins?.legend?.position ?? 'top',
            },
        },
        scales: {
            r: {
                beginAtZero: true,
                grid: {
                    display: config.showGrid ?? true,
                },
                pointLabels: {
                    color: 'white',
                    font: {
                        size: 12,
                    },
                },
                ticks: {
                    color: 'white',
                    font: {
                        size: 10,
                    },
                },
            },
        },
        elements: {
            line: {
                borderColor: config.borderColor ?? 'rgba(255, 99, 132, 1)',
                backgroundColor: config.backgroundColor ?? 'rgba(255, 99, 132, 0.2)',
            },
            point: {
                borderColor: config.borderColor ?? 'rgba(255, 99, 132, 1)',
                backgroundColor: config.backgroundColor ?? 'rgba(255, 99, 132, 0.2)',
            },
        },
    }
}

/**
 * 建立圓餅圖選項
 */
export const createPieChartOptions = (config: ChartConfig = {}): ChartOptions => {
    return {
        responsive: config.responsive ?? true,
        maintainAspectRatio: config.maintainAspectRatio ?? false,
        plugins: {
            title: {
                display: !!config.title,
                text: config.title || '',
            },
            legend: {
                display: config.showLegend ?? true,
                position: config.plugins?.legend?.position ?? 'bottom',
            },
            tooltip: {
                enabled: config.plugins?.tooltip?.enabled ?? true,
                callbacks: {
                    label: function(context: { label?: string; parsed?: number; dataset: { data: number[] } }) {
                        const label = context.label || ''
                        const value = context.parsed || 0
                        const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
                        const percentage = ((value / total) * 100).toFixed(1)
                        return `${label}: ${value} (${percentage}%)`
                    },
                    ...config.plugins?.tooltip?.callbacks,
                },
            },
        },
    }
}

/**
 * 建立甜甜圈圖選項
 */
export const createDoughnutChartOptions = (config: ChartConfig = {}): ChartOptions => {
    return {
        ...createPieChartOptions(config),
        cutout: '50%',
    }
}