/**
 * D2ThemeManager - 主題管理系統
 * 整合從 EnhancedD2Chart 提取的進階配色和主題功能
 */

export interface D2ColorScheme {
    satelliteDistance: string
    groundDistance: string
    thresh1Line: string
    thresh2Line: string
    currentTimeLine: string
    referenceNode: string
    triggerEvent: string
    title: string
    text: string
    grid: string
    background: string
    // 新增：連接狀態顏色
    connected: string
    disconnected: string
    connecting: string
    // 新增：錯誤狀態顏色
    error: string
    warning: string
    success: string
}

export const D2_THEMES = {
    dark: {
        satelliteDistance: '#28A745', // 綠色：衛星距離
        groundDistance: '#FD7E14', // 橙色：地面距離
        thresh1Line: '#DC3545', // 紅色：衛星門檻
        thresh2Line: '#007BFF', // 藍色：地面門檻
        currentTimeLine: '#FF6B35', // 動畫游標線
        referenceNode: '#17A2B8', // 青色：參考衛星節點
        triggerEvent: '#FF1744', // 亮紅色：觸發事件
        title: 'white',
        text: 'white',
        grid: 'rgba(255, 255, 255, 0.1)',
        background: 'transparent',
        // 連接狀態
        connected: '#28A745',
        disconnected: '#DC3545',
        connecting: '#FFC107',
        // 狀態顏色
        error: '#FF1744',
        warning: '#FF9800',
        success: '#4CAF50',
    } as D2ColorScheme,
    light: {
        satelliteDistance: '#198754',
        groundDistance: '#FD6C00',
        thresh1Line: '#DC3545',
        thresh2Line: '#0D6EFD',
        currentTimeLine: '#FF6B35',
        referenceNode: '#0DCAF0',
        triggerEvent: '#FF1744',
        title: 'black',
        text: '#333333',
        grid: 'rgba(0, 0, 0, 0.1)',
        background: 'white',
        // 連接狀態
        connected: '#198754',
        disconnected: '#DC3545',
        connecting: '#E65100',
        // 狀態顏色
        error: '#D32F2F',
        warning: '#F57C00',
        success: '#388E3C',
    } as D2ColorScheme,
}

export class D2ThemeManager {
    private isDarkTheme: boolean
    private onThemeChange?: (theme: D2ColorScheme) => void

    constructor(isDarkTheme = true, onThemeChange?: (theme: D2ColorScheme) => void) {
        this.isDarkTheme = isDarkTheme
        this.onThemeChange = onThemeChange
    }

    getCurrentTheme(): D2ColorScheme {
        return this.isDarkTheme ? D2_THEMES.dark : D2_THEMES.light
    }

    setTheme(isDark: boolean): void {
        this.isDarkTheme = isDark
        const newTheme = this.getCurrentTheme()
        this.onThemeChange?.(newTheme)
    }

    toggleTheme(): void {
        this.setTheme(!this.isDarkTheme)
    }

    // 獲取連接狀態顏色
    getConnectionStatusColor(status: 'connected' | 'disconnected' | 'connecting'): string {
        const theme = this.getCurrentTheme()
        return theme[status]
    }

    // 獲取狀態顏色
    getStatusColor(status: 'error' | 'warning' | 'success'): string {
        const theme = this.getCurrentTheme()
        return theme[status]
    }

    // 生成 Chart.js 兼容的配色
    getChartColors() {
        const theme = this.getCurrentTheme()
        return {
            scales: {
                x: {
                    ticks: { color: theme.text },
                    grid: { color: theme.grid },
                },
                y: {
                    ticks: { color: theme.text },
                    grid: { color: theme.grid },
                },
                y1: {
                    ticks: { color: theme.text },
                    grid: { display: false },
                },
            },
            plugins: {
                legend: {
                    labels: { color: theme.text },
                },
                title: {
                    color: theme.title,
                },
            },
        }
    }

    // 生成數據集顏色配置
    getDatasetColors() {
        const theme = this.getCurrentTheme()
        return {
            satelliteDistance: {
                borderColor: theme.satelliteDistance,
                backgroundColor: theme.satelliteDistance + '20',
                pointBackgroundColor: theme.satelliteDistance,
            },
            groundDistance: {
                borderColor: theme.groundDistance,
                backgroundColor: theme.groundDistance + '20',
                pointBackgroundColor: theme.groundDistance,
            },
            thresholdLines: {
                thresh1: theme.thresh1Line,
                thresh2: theme.thresh2Line,
            },
            currentTime: theme.currentTimeLine,
            referenceNode: theme.referenceNode,
            triggerEvent: theme.triggerEvent,
        }
    }
}

// Hook 版本
export const useD2ThemeManager = (
    isDarkTheme = true,
    onThemeChange?: (theme: D2ColorScheme) => void
) => {
    const themeManager = new D2ThemeManager(isDarkTheme, onThemeChange)
    
    return {
        currentTheme: themeManager.getCurrentTheme(),
        setTheme: (isDark: boolean) => themeManager.setTheme(isDark),
        toggleTheme: () => themeManager.toggleTheme(),
        getConnectionStatusColor: (status: 'connected' | 'disconnected' | 'connecting') =>
            themeManager.getConnectionStatusColor(status),
        getStatusColor: (status: 'error' | 'warning' | 'success') =>
            themeManager.getStatusColor(status),
        getChartColors: () => themeManager.getChartColors(),
        getDatasetColors: () => themeManager.getDatasetColors(),
    }
}