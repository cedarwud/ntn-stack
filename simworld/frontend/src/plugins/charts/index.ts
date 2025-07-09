/**
 * 圖表插件系統入口
 * 自動註冊所有可用插件
 */

import { ChartRegistry } from './ChartRegistry'
import A4EventChartPlugin from './plugins/A4EventChart'
import D1EventChartPlugin from './plugins/D1EventChart'

// 插件列表
const CHART_PLUGINS = [
    A4EventChartPlugin,
    D1EventChartPlugin,
    // 可以在此添加更多插件
]

// 初始化插件系統
export const initializeChartPlugins = (): void => {
    // console.log('🚀 [ChartPlugins] 開始初始化圖表插件系統')
    
    try {
        // 註冊所有插件
        CHART_PLUGINS.forEach(plugin => {
            ChartRegistry.register(plugin)
        })
        
        // 輸出統計信息
        const stats = ChartRegistry.getStats()
        // console.log('📊 [ChartPlugins] 插件系統初始化完成:', stats)
        
    } catch (error) {
        console.error('❌ [ChartPlugins] 插件系統初始化失敗:', error)
        throw error
    }
}

// 重新導出核心組件和服務
export { ChartRegistry } from './ChartRegistry'
export { UniversalChart, createA4Chart, createD1Chart } from './UniversalChart'
export type { ChartPlugin } from './ChartRegistry'

// 默認導出初始化函數
export default initializeChartPlugins