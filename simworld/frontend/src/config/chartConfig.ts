/**
 * Chart.js 全域配置模組
 * 
 * 從 ChartAnalysisDashboard 中抽離的 Chart.js 配置
 * 提供統一的圖表組件註冊和全域預設值設定
 */
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

/**
 * 註冊所有需要的 Chart.js 組件
 */
export const registerChartComponents = (): void => {
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

/**
 * 設定 Chart.js 全域預設值
 * 主要針對深色主題優化
 */
export const setChartDefaults = (): void => {
    // 基本顏色和字體設定
    ChartJS.defaults.color = 'white'
    ChartJS.defaults.font.size = 16
    ChartJS.defaults.locale = 'en-US'

    // 圖例設定
    ChartJS.defaults.plugins.legend.labels.color = 'white'
    ChartJS.defaults.plugins.legend.labels.font = { size: 16 }

    // 標題設定
    ChartJS.defaults.plugins.title.color = 'white'
    ChartJS.defaults.plugins.title.font = { size: 20, weight: 'bold' as const }

    // Tooltip 設定
    ChartJS.defaults.plugins.tooltip.titleColor = 'white'
    ChartJS.defaults.plugins.tooltip.bodyColor = 'white'
    ChartJS.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.9)'
    ChartJS.defaults.plugins.tooltip.titleFont = { size: 16 }
    ChartJS.defaults.plugins.tooltip.bodyFont = { size: 15 }

    // 軸標籤設定
    ChartJS.defaults.scale.ticks.color = 'white'
    ChartJS.defaults.scale.ticks.font = { size: 14 }
    ChartJS.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.2)'

    // 元素預設樣式
    ;(ChartJS.defaults as Record<string, unknown>).elements = {
        ...((ChartJS.defaults as Record<string, unknown>).elements || {}),
        arc: {
            ...((ChartJS.defaults as Record<string, unknown>).elements as Record<string, unknown>)?.arc || {},
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
        bar: {
            ...((ChartJS.defaults as Record<string, unknown>).elements as Record<string, unknown>)?.bar || {},
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
        line: {
            ...((ChartJS.defaults as Record<string, unknown>).elements as Record<string, unknown>)?.line || {},
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
    }

    // 軸標題設定（需要安全處理）
    try {
        ;(ChartJS.defaults.scale as Record<string, unknown>).title = {
            color: 'white',
            font: { size: 16, weight: 'bold' as const },
        }
    } catch (e) {
        console.warn('Could not set scale title defaults:', e)
    }
}

/**
 * 初始化 Chart.js 配置
 * 應在應用程式啟動時調用一次
 */
export const initializeChartJS = (): void => {
    registerChartComponents()
    setChartDefaults()
}