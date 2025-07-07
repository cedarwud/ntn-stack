/**
 * 圖表動態載入器
 * 提供圖表的動態載入和熱替換功能
 */

import { ChartRegistry, ChartPlugin } from './ChartRegistry'

// 載入狀態
export enum LoadStatus {
    PENDING = 'pending',
    LOADING = 'loading',
    LOADED = 'loaded',
    ERROR = 'error'
}

// 載入結果
export interface LoadResult {
    pluginId: string
    status: LoadStatus
    plugin?: ChartPlugin
    error?: Error
    loadTime?: number
}

// 載入進度回調
export type LoadProgressCallback = (result: LoadResult) => void

// 圖表載入器類
class ChartLoaderManager {
    private loadingPlugins: Set<string> = new Set()
    private loadResults: Map<string, LoadResult> = new Map()
    
    constructor() {
        console.log('🔄 [ChartLoader] 圖表載入器已初始化')
    }

    /**
     * 動態載入單個插件
     */
    async loadPlugin(
        pluginId: string,
        onProgress?: LoadProgressCallback
    ): Promise<LoadResult> {
        // 如果已經在載入，等待結果
        if (this.loadingPlugins.has(pluginId)) {
            return this.waitForLoad(pluginId)
        }

        // 如果已經載入，直接返回結果
        const existingResult = this.loadResults.get(pluginId)
        if (existingResult && existingResult.status === LoadStatus.LOADED) {
            return existingResult
        }

        const startTime = Date.now()
        this.loadingPlugins.add(pluginId)

        const result: LoadResult = {
            pluginId,
            status: LoadStatus.LOADING
        }

        onProgress?.(result)

        try {
            console.log(`🔄 [ChartLoader] 開始載入插件: ${pluginId}`)

            // 檢查是否已經註冊
            const existingPlugin = ChartRegistry.getPlugin(pluginId)
            if (existingPlugin) {
                console.log(`⏭️ [ChartLoader] 插件已註冊: ${pluginId}`)
                
                result.status = LoadStatus.LOADED
                result.plugin = existingPlugin
                result.loadTime = Date.now() - startTime
                
                this.loadResults.set(pluginId, result)
                this.loadingPlugins.delete(pluginId)
                onProgress?.(result)
                
                return result
            }

            // 動態導入插件模組
            let pluginModule: any
            
            try {
                // 嘗試從預定義路徑載入
                pluginModule = await import(`./plugins/${this.getPluginFileName(pluginId)}`)
            } catch (importError) {
                // 嘗試直接路徑
                try {
                    pluginModule = await import(`./plugins/${pluginId}`)
                } catch (directImportError) {
                    throw new Error(`無法載入插件模組: ${pluginId}`)
                }
            }

            // 提取插件定義
            const plugin = pluginModule.default || pluginModule[pluginId] || pluginModule
            
            if (!plugin || !this.validatePlugin(plugin)) {
                throw new Error(`插件格式無效: ${pluginId}`)
            }

            // 註冊插件
            ChartRegistry.register(plugin)

            result.status = LoadStatus.LOADED
            result.plugin = plugin
            result.loadTime = Date.now() - startTime

            console.log(`✅ [ChartLoader] 插件載入成功: ${pluginId} (${result.loadTime}ms)`)

        } catch (error) {
            console.error(`❌ [ChartLoader] 插件載入失敗: ${pluginId}`, error)
            
            result.status = LoadStatus.ERROR
            result.error = error as Error
            result.loadTime = Date.now() - startTime
        } finally {
            this.loadResults.set(pluginId, result)
            this.loadingPlugins.delete(pluginId)
            onProgress?.(result)
        }

        return result
    }

    /**
     * 批量載入插件
     */
    async loadPlugins(
        pluginIds: string[],
        onProgress?: LoadProgressCallback
    ): Promise<LoadResult[]> {
        console.log(`🔄 [ChartLoader] 開始批量載入插件: ${pluginIds.length} 個`)

        const loadPromises = pluginIds.map(id => this.loadPlugin(id, onProgress))
        const results = await Promise.all(loadPromises)

        const successful = results.filter(r => r.status === LoadStatus.LOADED).length
        console.log(`✅ [ChartLoader] 批量載入完成: ${successful}/${pluginIds.length} 成功`)

        return results
    }

    /**
     * 預載入指定插件
     */
    async preloadPlugins(pluginIds: string[]): Promise<void> {
        console.log(`🚀 [ChartLoader] 開始預載入插件: ${pluginIds.join(', ')}`)
        
        const results = await this.loadPlugins(pluginIds)
        const failed = results.filter(r => r.status === LoadStatus.ERROR)
        
        if (failed.length > 0) {
            console.warn(`⚠️ [ChartLoader] 預載入失敗的插件:`, failed.map(r => r.pluginId))
        }
    }

    /**
     * 熱重載插件
     */
    async reloadPlugin(pluginId: string): Promise<LoadResult> {
        console.log(`🔥 [ChartLoader] 熱重載插件: ${pluginId}`)
        
        // 先移除現有插件
        ChartRegistry.unregister(pluginId)
        this.loadResults.delete(pluginId)
        
        // 重新載入
        return this.loadPlugin(pluginId)
    }

    /**
     * 獲取載入結果
     */
    getLoadResult(pluginId: string): LoadResult | undefined {
        return this.loadResults.get(pluginId)
    }

    /**
     * 獲取所有載入結果
     */
    getAllLoadResults(): LoadResult[] {
        return Array.from(this.loadResults.values())
    }

    /**
     * 清除載入結果
     */
    clearResults(): void {
        this.loadResults.clear()
        console.log('🧹 [ChartLoader] 已清除所有載入結果')
    }

    /**
     * 獲取載入統計
     */
    getStats() {
        const results = this.getAllLoadResults()
        const byStatus = results.reduce((acc, result) => {
            acc[result.status] = (acc[result.status] || 0) + 1
            return acc
        }, {} as Record<LoadStatus, number>)

        const totalLoadTime = results
            .filter(r => r.loadTime !== undefined)
            .reduce((sum, r) => sum + (r.loadTime || 0), 0)

        return {
            total: results.length,
            loading: this.loadingPlugins.size,
            byStatus,
            averageLoadTime: results.length > 0 ? totalLoadTime / results.length : 0,
            totalLoadTime
        }
    }

    /**
     * 等待插件載入完成
     */
    private async waitForLoad(pluginId: string): Promise<LoadResult> {
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (!this.loadingPlugins.has(pluginId)) {
                    clearInterval(checkInterval)
                    const result = this.loadResults.get(pluginId)
                    if (result) {
                        resolve(result)
                    }
                }
            }, 50)
        })
    }

    /**
     * 根據插件ID獲取文件名
     */
    private getPluginFileName(pluginId: string): string {
        // 轉換插件ID到文件名的映射規則
        const fileNameMap: Record<string, string> = {
            'a4-event-chart': 'A4EventChart',
            'd1-event-chart': 'D1EventChart',
            'd2-event-chart': 'D2EventChart',
            't1-event-chart': 'T1EventChart'
        }

        return fileNameMap[pluginId] || pluginId
    }

    /**
     * 驗證插件格式
     */
    private validatePlugin(plugin: any): plugin is ChartPlugin {
        return (
            plugin &&
            typeof plugin === 'object' &&
            typeof plugin.id === 'string' &&
            typeof plugin.name === 'string' &&
            typeof plugin.chartType === 'string' &&
            typeof plugin.configFactory === 'function'
        )
    }
}

// 單例模式，全局唯一實例
export const ChartLoader = new ChartLoaderManager()

// 默認導出
export default ChartLoader