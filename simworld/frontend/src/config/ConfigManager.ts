/**
 * 統一配置管理系統
 * 提供中央化的配置管理和動態更新功能
 */

// 配置類型定義
export interface AppConfig {
    api: ApiConfig
    chart: ChartConfig
    theme: ThemeConfig
    feature: FeatureConfig
    performance: PerformanceConfig
}

export interface ApiConfig {
    baseUrl: string
    timeout: number
    retryAttempts: number
    endpoints: Record<string, string>
}

export interface ChartConfig {
    defaultWidth: number
    defaultHeight: number
    animationDuration: number
    refreshInterval: number
    plugins: string[]
}

export interface ThemeConfig {
    default: 'dark' | 'light'
    colors: {
        dark: Record<string, string>
        light: Record<string, string>
    }
}

export interface FeatureConfig {
    enablePlugins: boolean
    enableCaching: boolean
    enableAnalytics: boolean
    enableRealTime: boolean
}

export interface PerformanceConfig {
    maxCacheSize: number
    debounceDelay: number
    throttleDelay: number
    lazyLoadThreshold: number
}

// 配置變更監聽器類型
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ConfigChangeListener = (key: string, newValue: any, oldValue: any) => void

// 默認配置
const DEFAULT_CONFIG: AppConfig = {
    api: {
        baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000',
        timeout: 30000,
        retryAttempts: 3,
        endpoints: {
            handover: '/api/v1/handover',
            devices: '/api/v1/devices',
            satellite: '/api/v1/satellite',
            simulation: '/api/v1/simulation',
            coordination: '/api/v1/coordination'
        }
    },
    chart: {
        defaultWidth: 800,
        defaultHeight: 400,
        animationDuration: 300,
        refreshInterval: 1000,
        plugins: ['tooltip', 'legend', 'zoom']
    },
    theme: {
        default: 'dark',
        colors: {
            dark: {
                primary: '#007bff',
                secondary: '#6c757d',
                success: '#28a745',
                danger: '#dc3545',
                warning: '#ffc107',
                info: '#17a2b8',
                background: '#121212',
                surface: '#1e1e1e',
                text: '#ffffff',
                textSecondary: '#aaaaaa'
            },
            light: {
                primary: '#0066cc',
                secondary: '#6c757d',
                success: '#198754',
                danger: '#dc3545',
                warning: '#ffca2c',
                info: '#0dcaf0',
                background: '#ffffff',
                surface: '#f8f9fa',
                text: '#212529',
                textSecondary: '#6c757d'
            }
        }
    },
    feature: {
        enablePlugins: true,
        enableCaching: true,
        enableAnalytics: false,
        enableRealTime: true
    },
    performance: {
        maxCacheSize: 100,
        debounceDelay: 300,
        throttleDelay: 100,
        lazyLoadThreshold: 0.1
    }
}

// 配置管理器類
class ConfigurationManager {
    private config: AppConfig
    private listeners: Map<string, ConfigChangeListener[]> = new Map()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    private cache: Map<string, any> = new Map()

    constructor(initialConfig: Partial<AppConfig> = {}) {
        this.config = this.mergeConfig(DEFAULT_CONFIG, initialConfig)
        // console.log('⚙️ [ConfigManager] 配置管理器已初始化')
        this.logConfigSummary()
    }

    /**
     * 深度合併配置
     */
    private mergeConfig(target: AppConfig, source: Partial<AppConfig>): AppConfig {
        const result = { ...target }
        
        for (const key in source) {
            const sourceValue = source[key as keyof AppConfig]
            if (sourceValue !== undefined) {
                if (typeof sourceValue === 'object' && !Array.isArray(sourceValue)) {
                    result[key as keyof AppConfig] = {
                        ...target[key as keyof AppConfig],
                        ...sourceValue
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    } as any
                } else {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    result[key as keyof AppConfig] = sourceValue as any
                }
            }
        }
        
        return result
    }

    /**
     * 獲取配置值
     */
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    get<T = any>(path: string): T {
        // 檢查緩存
        if (this.cache.has(path)) {
            return this.cache.get(path)
        }

        const keys = path.split('.')
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let value: any = this.config

        for (const key of keys) {
            if (value && typeof value === 'object' && key in value) {
                value = value[key]
            } else {
                console.warn(`⚠️ [ConfigManager] 配置路徑不存在: ${path}`)
                return undefined as T
            }
        }

        // 緩存結果
        this.cache.set(path, value)
        return value
    }

    /**
     * 設置配置值
     */
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set(path: string, value: any): void {
        const keys = path.split('.')
        const lastKey = keys.pop()!
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let target: any = this.config

        // 導航到目標對象
        for (const key of keys) {
            if (!target[key] || typeof target[key] !== 'object') {
                target[key] = {}
            }
            target = target[key]
        }

        const oldValue = target[lastKey]
        target[lastKey] = value

        // 清除相關緩存
        this.clearCacheByPrefix(path)

        // 通知監聽器
        this.notifyListeners(path, value, oldValue)

        // console.log(`🔄 [ConfigManager] 配置已更新: ${path} =`, value)
    }

    /**
     * 批量更新配置
     */
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    update(updates: Record<string, any>): void {
        // console.log('🔄 [ConfigManager] 批量更新配置:', updates)
        
        for (const [path, value] of Object.entries(updates)) {
            this.set(path, value)
        }
    }

    /**
     * 獲取完整配置
     */
    getAll(): AppConfig {
        return { ...this.config }
    }

    /**
     * 重置配置到默認值
     */
    reset(): void {
        const oldConfig = this.config
        this.config = { ...DEFAULT_CONFIG }
        this.cache.clear()
        
        // console.log('🔄 [ConfigManager] 配置已重置到默認值')
        this.notifyListeners('*', this.config, oldConfig)
    }

    /**
     * 註冊配置變更監聽器
     */
    onConfigChange(path: string, listener: ConfigChangeListener): () => void {
        if (!this.listeners.has(path)) {
            this.listeners.set(path, [])
        }
        
        this.listeners.get(path)!.push(listener)
        
        // 返回取消註冊函數
        return () => {
            const listeners = this.listeners.get(path)
            if (listeners) {
                const index = listeners.indexOf(listener)
                if (index > -1) {
                    listeners.splice(index, 1)
                }
            }
        }
    }

    /**
     * 通知監聽器
     */
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    private notifyListeners(path: string, newValue: any, oldValue: any): void {
        // 通知具體路徑的監聽器
        const listeners = this.listeners.get(path) || []
        listeners.forEach(listener => {
            try {
                listener(path, newValue, oldValue)
            } catch (error) {
                console.error(`❌ [ConfigManager] 監聽器執行失敗:`, error)
            }
        })

        // 通知通配符監聽器
        const wildcardListeners = this.listeners.get('*') || []
        wildcardListeners.forEach(listener => {
            try {
                listener(path, newValue, oldValue)
            } catch (error) {
                console.error(`❌ [ConfigManager] 通配符監聽器執行失敗:`, error)
            }
        })
    }

    /**
     * 清除指定前綴的緩存
     */
    private clearCacheByPrefix(prefix: string): void {
        const keysToDelete: string[] = []
        
        for (const key of this.cache.keys()) {
            if (key.startsWith(prefix)) {
                keysToDelete.push(key)
            }
        }
        
        keysToDelete.forEach(key => this.cache.delete(key))
    }

    /**
     * 從環境變量載入配置
     */
    loadFromEnvironment(): void {
        const envConfig: Partial<AppConfig> = {}

        // API配置
        if (import.meta.env.VITE_API_BASE_URL) {
            envConfig.api = {
                ...this.config.api,
                baseUrl: import.meta.env.VITE_API_BASE_URL
            }
        }

        // 功能配置
        if (import.meta.env.VITE_ENABLE_ANALYTICS !== undefined) {
            envConfig.feature = {
                ...this.config.feature,
                enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true'
            }
        }

        // 主題配置
        if (import.meta.env.VITE_DEFAULT_THEME) {
            envConfig.theme = {
                ...this.config.theme,
                default: import.meta.env.VITE_DEFAULT_THEME as 'dark' | 'light'
            }
        }

        this.config = this.mergeConfig(this.config, envConfig)
        this.cache.clear()
        
        // console.log('🔄 [ConfigManager] 已從環境變量載入配置')
    }

    /**
     * 輸出配置摘要 - 已禁用減少日誌噪音
     */
    private logConfigSummary(): void {
        // 已禁用詳細配置日誌，只在需要調試時啟用
        // console.log('📋 [ConfigManager] 配置摘要:')
        // console.log('  - API Base URL:', this.get('api.baseUrl'))
        // console.log('  - 默認主題:', this.get('theme.default'))
        // console.log('  - 插件啟用:', this.get('feature.enablePlugins'))
        // console.log('  - 緩存啟用:', this.get('feature.enableCaching'))
        // console.log('  - 圖表插件:', this.get('chart.plugins'))
    }

    /**
     * 驗證配置
     */
    validate(): { isValid: boolean; errors: string[] } {
        const errors: string[] = []

        // 驗證API配置
        if (!this.get('api.baseUrl')) {
            errors.push('API baseUrl 不能為空')
        }

        // 驗證主題配置
        const defaultTheme = this.get('theme.default')
        if (!['dark', 'light'].includes(defaultTheme)) {
            errors.push('默認主題必須是 dark 或 light')
        }

        // 驗證數值配置
        const timeout = this.get('api.timeout')
        if (typeof timeout !== 'number' || timeout <= 0) {
            errors.push('API timeout 必須是正數')
        }

        return {
            isValid: errors.length === 0,
            errors
        }
    }

    /**
     * 導出配置到JSON
     */
    exportToJSON(): string {
        return JSON.stringify(this.config, null, 2)
    }

    /**
     * 從JSON導入配置
     */
    importFromJSON(jsonString: string): void {
        try {
            const importedConfig = JSON.parse(jsonString)
            this.config = this.mergeConfig(DEFAULT_CONFIG, importedConfig)
            this.cache.clear()
            
            // console.log('📥 [ConfigManager] 已從JSON導入配置')
            this.notifyListeners('*', this.config, null)
        } catch (error) {
            console.error('❌ [ConfigManager] JSON配置導入失敗:', error)
            throw new Error('無效的JSON配置格式')
        }
    }
}

// 單例模式，全局唯一實例
export const ConfigManager = new ConfigurationManager()

// 便利函數
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const getConfig = <T = any>(path: string): T => ConfigManager.get<T>(path)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const setConfig = (path: string, value: any): void => ConfigManager.set(path, value)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const updateConfig = (updates: Record<string, any>): void => ConfigManager.update(updates)

// 默認導出
export default ConfigManager