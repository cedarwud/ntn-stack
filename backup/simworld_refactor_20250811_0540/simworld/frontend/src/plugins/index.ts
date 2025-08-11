/**
 * 插件系統主入口 - 簡化版
 * 移除插件化架構，保持配置管理功能
 */

import { ConfigManager } from '../config/ConfigManager'

/**
 * 初始化配置系統
 */
export const initializeConfigSystem = async (): Promise<void> => {
    try {
        // 從環境變量載入配置
        ConfigManager.loadFromEnvironment()
        
        // 驗證配置
        const validation = ConfigManager.validate()
        if (!validation.isValid) {
            console.warn('⚠️ [ConfigSystem] 配置驗證警告:', validation.errors)
        }
        
        // console.log('✅ [ConfigSystem] 配置系統初始化完成')
    } catch (error) {
        console.error('❌ [ConfigSystem] 配置系統初始化失敗:', error)
        throw error
    }
}

// 重新導出配置管理
export { ConfigManager, getConfig, setConfig } from '../config/ConfigManager'

// 默認導出初始化函數
export default initializeConfigSystem