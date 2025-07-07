/**
 * 插件系統主入口
 * 統一管理所有插件的初始化和配置
 */

import { ConfigManager } from '../config/ConfigManager'
import { initializeChartPlugins } from './charts'
import { ChartLoader } from './charts/ChartLoader'

// 插件系統狀態
interface PluginSystemStatus {
    isInitialized: boolean
    chartPluginsLoaded: number
    errors: string[]
    initTime: number
}

// 插件系統管理器
class PluginSystemManager {
    private status: PluginSystemStatus = {
        isInitialized: false,
        chartPluginsLoaded: 0,
        errors: [],
        initTime: 0
    }

    /**
     * 初始化整個插件系統
     */
    async initialize(): Promise<void> {
        if (this.status.isInitialized) {
            console.log('⏭️ [PluginSystem] 插件系統已初始化，跳過')
            return
        }

        const startTime = Date.now()
        console.log('🚀 [PluginSystem] 開始初始化插件系統')

        try {
            // 1. 載入配置
            await this.initializeConfig()

            // 2. 初始化圖表插件
            await this.initializeChartPlugins()

            // 3. 預載入配置中指定的插件
            await this.preloadConfiguredPlugins()

            this.status.isInitialized = true
            this.status.initTime = Date.now() - startTime

            console.log(`✅ [PluginSystem] 插件系統初始化完成 (${this.status.initTime}ms)`)
            this.logSystemStatus()

        } catch (error) {
            const errorMessage = `插件系統初始化失敗: ${error}`
            this.status.errors.push(errorMessage)
            console.error(`❌ [PluginSystem] ${errorMessage}`, error)
            throw error
        }
    }

    /**
     * 初始化配置
     */
    private async initializeConfig(): Promise<void> {
        console.log('⚙️ [PluginSystem] 載入配置...')
        
        // 從環境變量載入配置
        ConfigManager.loadFromEnvironment()
        
        // 驗證配置
        const validation = ConfigManager.validate()
        if (!validation.isValid) {
            throw new Error(`配置驗證失敗: ${validation.errors.join(', ')}`)
        }

        console.log('✅ [PluginSystem] 配置載入完成')
    }

    /**
     * 初始化圖表插件
     */
    private async initializeChartPlugins(): Promise<void> {
        if (!ConfigManager.get('feature.enablePlugins')) {
            console.log('⏭️ [PluginSystem] 插件功能已禁用，跳過圖表插件初始化')
            return
        }

        console.log('📊 [PluginSystem] 初始化圖表插件...')
        
        try {
            initializeChartPlugins()
            
            const stats = ChartLoader.getStats()
            this.status.chartPluginsLoaded = stats.total
            
            console.log('✅ [PluginSystem] 圖表插件初始化完成')
        } catch (error) {
            const errorMessage = `圖表插件初始化失敗: ${error}`
            this.status.errors.push(errorMessage)
            throw new Error(errorMessage)
        }
    }

    /**
     * 預載入配置中指定的插件
     */
    private async preloadConfiguredPlugins(): Promise<void> {
        const pluginsToPreload = ConfigManager.get<string[]>('chart.plugins') || []
        
        if (pluginsToPreload.length === 0) {
            console.log('⏭️ [PluginSystem] 沒有需要預載入的插件')
            return
        }

        console.log(`🔄 [PluginSystem] 預載入插件: ${pluginsToPreload.join(', ')}`)
        
        try {
            await ChartLoader.preloadPlugins(pluginsToPreload)
            console.log('✅ [PluginSystem] 插件預載入完成')
        } catch (error) {
            const errorMessage = `插件預載入失敗: ${error}`
            this.status.errors.push(errorMessage)
            console.warn(`⚠️ [PluginSystem] ${errorMessage}`)
            // 預載入失敗不應該阻止系統啟動
        }
    }

    /**
     * 獲取系統狀態
     */
    getStatus(): PluginSystemStatus {
        return { ...this.status }
    }

    /**
     * 檢查插件是否可用
     */
    isPluginAvailable(pluginId: string): boolean {
        const result = ChartLoader.getLoadResult(pluginId)
        return result?.status === 'loaded'
    }

    /**
     * 動態載入插件
     */
    async loadPlugin(pluginId: string): Promise<boolean> {
        try {
            const result = await ChartLoader.loadPlugin(pluginId)
            return result.status === 'loaded'
        } catch (error) {
            console.error(`❌ [PluginSystem] 動態載入插件失敗: ${pluginId}`, error)
            return false
        }
    }

    /**
     * 重載插件
     */
    async reloadPlugin(pluginId: string): Promise<boolean> {
        try {
            const result = await ChartLoader.reloadPlugin(pluginId)
            return result.status === 'loaded'
        } catch (error) {
            console.error(`❌ [PluginSystem] 重載插件失敗: ${pluginId}`, error)
            return false
        }
    }

    /**
     * 記錄系統狀態
     */
    private logSystemStatus(): void {
        console.log('📋 [PluginSystem] 系統狀態摘要:')
        console.log('  - 初始化狀態:', this.status.isInitialized ? '✅' : '❌')
        console.log('  - 圖表插件數量:', this.status.chartPluginsLoaded)
        console.log('  - 初始化耗時:', `${this.status.initTime}ms`)
        
        if (this.status.errors.length > 0) {
            console.log('  - 錯誤數量:', this.status.errors.length)
            this.status.errors.forEach(error => {
                console.log(`    - ${error}`)
            })
        }
    }

    /**
     * 清理插件系統
     */
    cleanup(): void {
        console.log('🧹 [PluginSystem] 清理插件系統...')
        
        ChartLoader.clearResults()
        
        this.status = {
            isInitialized: false,
            chartPluginsLoaded: 0,
            errors: [],
            initTime: 0
        }
        
        console.log('✅ [PluginSystem] 插件系統清理完成')
    }
}

// 單例模式，全局唯一實例
export const PluginSystem = new PluginSystemManager()

// 便利函數
export const initializePluginSystem = () => PluginSystem.initialize()
export const isPluginAvailable = (pluginId: string) => PluginSystem.isPluginAvailable(pluginId)
export const loadPlugin = (pluginId: string) => PluginSystem.loadPlugin(pluginId)

// 重新導出插件相關模組
export { ChartRegistry, UniversalChart, createA4Chart, createD1Chart } from './charts'
export { ConfigManager, getConfig, setConfig } from '../config/ConfigManager'
export { ChartLoader } from './charts/ChartLoader'

// 默認導出
export default PluginSystem