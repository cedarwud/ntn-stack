/**
 * 圖表插件註冊系統
 * 提供動態圖表載入和管理功能
 */

import { Chart, ChartConfiguration, ChartType } from 'chart.js/auto'

// 圖表插件接口
export interface ChartPlugin {
    id: string
    name: string
    description: string
    version: string
    chartType: ChartType
    configFactory: (props: any) => ChartConfiguration
    defaultProps?: Record<string, any>
    isEnabled?: boolean
    dependencies?: string[]
}

// 圖表插件管理器
class ChartRegistryManager {
    private plugins: Map<string, ChartPlugin> = new Map()
    private loadedPlugins: Set<string> = new Set()
    
    constructor() {
        // console.log('🔧 [ChartRegistry] 初始化圖表插件註冊系統')
    }

    /**
     * 註冊圖表插件
     */
    register(plugin: ChartPlugin): void {
        if (this.plugins.has(plugin.id)) {
            console.warn(`⚠️ [ChartRegistry] 插件 ${plugin.id} 已存在，將被覆蓋`)
        }

        // 驗證依賴
        if (plugin.dependencies) {
            const missingDeps = plugin.dependencies.filter(dep => !this.plugins.has(dep))
            if (missingDeps.length > 0) {
                throw new Error(`插件 ${plugin.id} 缺少依賴: ${missingDeps.join(', ')}`)
            }
        }

        this.plugins.set(plugin.id, plugin)
        // console.log(`✅ [ChartRegistry] 已註冊插件: ${plugin.name} (${plugin.id})`)
    }

    /**
     * 獲取圖表插件
     */
    getPlugin(pluginId: string): ChartPlugin | undefined {
        return this.plugins.get(pluginId)
    }

    /**
     * 獲取所有已註冊插件
     */
    getAllPlugins(): ChartPlugin[] {
        return Array.from(this.plugins.values())
    }

    /**
     * 獲取已啟用插件
     */
    getEnabledPlugins(): ChartPlugin[] {
        return this.getAllPlugins().filter(plugin => plugin.isEnabled !== false)
    }

    /**
     * 按類型獲取插件
     */
    getPluginsByType(chartType: ChartType): ChartPlugin[] {
        return this.getAllPlugins().filter(plugin => plugin.chartType === chartType)
    }

    /**
     * 創建圖表配置
     */
    createChartConfig(pluginId: string, props: any = {}): ChartConfiguration {
        const plugin = this.getPlugin(pluginId)
        if (!plugin) {
            throw new Error(`未找到插件: ${pluginId}`)
        }

        if (plugin.isEnabled === false) {
            throw new Error(`插件已禁用: ${pluginId}`)
        }

        // 合併默認屬性
        const mergedProps = { ...plugin.defaultProps, ...props }
        
        try {
            const config = plugin.configFactory(mergedProps)
            // console.log(`🎯 [ChartRegistry] 已創建圖表配置: ${plugin.name}`)
            return config
        } catch (error) {
            console.error(`❌ [ChartRegistry] 創建圖表配置失敗: ${plugin.name}`, error)
            throw error
        }
    }

    /**
     * 動態載入插件
     */
    async loadPlugin(pluginId: string): Promise<void> {
        if (this.loadedPlugins.has(pluginId)) {
            // console.log(`⏭️ [ChartRegistry] 插件 ${pluginId} 已載入，跳過`)
            return
        }

        try {
            // 動態導入插件
            const pluginModule = await import(`./plugins/${pluginId}`)
            const plugin = pluginModule.default || pluginModule[pluginId]
            
            if (!plugin) {
                throw new Error(`插件模組缺少導出: ${pluginId}`)
            }

            this.register(plugin)
            this.loadedPlugins.add(pluginId)
            // console.log(`🔄 [ChartRegistry] 動態載入插件: ${pluginId}`)
        } catch (error) {
            console.error(`❌ [ChartRegistry] 載入插件失敗: ${pluginId}`, error)
            throw error
        }
    }

    /**
     * 批量載入插件
     */
    async loadPlugins(pluginIds: string[]): Promise<void> {
        const loadPromises = pluginIds.map(id => this.loadPlugin(id))
        await Promise.all(loadPromises)
        // console.log(`✅ [ChartRegistry] 批量載入完成: ${pluginIds.length} 個插件`)
    }

    /**
     * 啟用/禁用插件
     */
    setPluginEnabled(pluginId: string, enabled: boolean): void {
        const plugin = this.getPlugin(pluginId)
        if (!plugin) {
            throw new Error(`未找到插件: ${pluginId}`)
        }

        plugin.isEnabled = enabled
        // console.log(`🔄 [ChartRegistry] 插件 ${pluginId} ${enabled ? '已啟用' : '已禁用'}`)
    }

    /**
     * 移除插件
     */
    unregister(pluginId: string): boolean {
        const removed = this.plugins.delete(pluginId)
        if (removed) {
            this.loadedPlugins.delete(pluginId)
            // console.log(`🗑️ [ChartRegistry] 已移除插件: ${pluginId}`)
        }
        return removed
    }

    /**
     * 清空所有插件
     */
    clear(): void {
        this.plugins.clear()
        this.loadedPlugins.clear()
        // console.log('🧹 [ChartRegistry] 已清空所有插件')
    }

    /**
     * 獲取插件統計信息
     */
    getStats() {
        const all = this.getAllPlugins()
        const enabled = this.getEnabledPlugins()
        const byType = all.reduce((acc, plugin) => {
            acc[plugin.chartType] = (acc[plugin.chartType] || 0) + 1
            return acc
        }, {} as Record<string, number>)

        return {
            total: all.length,
            enabled: enabled.length,
            disabled: all.length - enabled.length,
            loaded: this.loadedPlugins.size,
            byType
        }
    }
}

// 單例模式，全局唯一實例
export const ChartRegistry = new ChartRegistryManager()

// 默認導出
export default ChartRegistry