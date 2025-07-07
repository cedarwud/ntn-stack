/**
 * 插件系統使用示例
 * 展示如何使用新的插件化架構
 */

import React, { useState, useEffect } from 'react'
import { UniversalChart, ChartRegistry, ChartLoader } from '../plugins/charts'
import { ConfigManager } from '../config/ConfigManager'

export const PluginSystemDemo: React.FC = () => {
    const [selectedPlugin, setSelectedPlugin] = useState('a4-event-chart')
    const [chartProps, setChartProps] = useState({
        threshold: -70,
        hysteresis: 3,
        currentTime: 30,
        showThresholdLines: true,
        isDarkTheme: true
    })
    const [availablePlugins, setAvailablePlugins] = useState<string[]>([])

    useEffect(() => {
        // 獲取可用插件列表
        const plugins = ChartRegistry.getEnabledPlugins()
        setAvailablePlugins(plugins.map(p => p.id))
        console.log('📊 可用插件:', plugins.map(p => `${p.name} (${p.id})`))
    }, [])

    const handlePluginChange = (pluginId: string) => {
        setSelectedPlugin(pluginId)
        const plugin = ChartRegistry.getPlugin(pluginId)
        if (plugin?.defaultProps) {
            setChartProps({ ...chartProps, ...plugin.defaultProps })
        }
    }

    const handleThresholdChange = (value: number) => {
        setChartProps({ ...chartProps, threshold: value })
    }

    const handleTimeChange = (value: number) => {
        setChartProps({ ...chartProps, currentTime: value })
    }

    const toggleTheme = () => {
        setChartProps({ ...chartProps, isDarkTheme: !chartProps.isDarkTheme })
    }

    const exportConfig = () => {
        const config = ConfigManager.exportToJSON()
        const blob = new Blob([config], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'chart-config.json'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    const showStats = () => {
        const registryStats = ChartRegistry.getStats()
        const loaderStats = ChartLoader.getStats()
        
        console.log('📊 插件註冊統計:', registryStats)
        console.log('🔄 插件載入統計:', loaderStats)
        
        alert(`插件系統統計:\n註冊插件: ${registryStats.total}\n已載入: ${loaderStats.total}\n平均載入時間: ${loaderStats.averageLoadTime.toFixed(2)}ms`)
    }

    return (
        <div style={{ padding: '20px', backgroundColor: '#1e1e1e', color: 'white', minHeight: '100vh' }}>
            <h1>🚀 插件化圖表系統示例</h1>
            
            {/* 控制面板 */}
            <div style={{ marginBottom: '20px', display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                <div>
                    <label>選擇插件:</label>
                    <select 
                        value={selectedPlugin} 
                        onChange={(e) => handlePluginChange(e.target.value)}
                        style={{ marginLeft: '10px', padding: '5px' }}
                    >
                        {availablePlugins.map(id => {
                            const plugin = ChartRegistry.getPlugin(id)
                            return (
                                <option key={id} value={id}>
                                    {plugin?.name || id}
                                </option>
                            )
                        })}
                    </select>
                </div>

                <div>
                    <label>門檻值:</label>
                    <input
                        type="range"
                        min="-100"
                        max="-50"
                        value={chartProps.threshold}
                        onChange={(e) => handleThresholdChange(Number(e.target.value))}
                        style={{ marginLeft: '10px' }}
                    />
                    <span style={{ marginLeft: '10px' }}>{chartProps.threshold} dBm</span>
                </div>

                <div>
                    <label>當前時間:</label>
                    <input
                        type="range"
                        min="0"
                        max="95"
                        value={chartProps.currentTime}
                        onChange={(e) => handleTimeChange(Number(e.target.value))}
                        style={{ marginLeft: '10px' }}
                    />
                    <span style={{ marginLeft: '10px' }}>{chartProps.currentTime}s</span>
                </div>

                <button onClick={toggleTheme} style={{ padding: '8px 16px' }}>
                    切換主題 ({chartProps.isDarkTheme ? '深色' : '淺色'})
                </button>

                <button onClick={showStats} style={{ padding: '8px 16px' }}>
                    顯示統計
                </button>

                <button onClick={exportConfig} style={{ padding: '8px 16px' }}>
                    導出配置
                </button>
            </div>

            {/* 圖表展示區 */}
            <div style={{ 
                backgroundColor: chartProps.isDarkTheme ? '#2d2d2d' : '#ffffff', 
                padding: '20px', 
                borderRadius: '8px',
                height: '500px'
            }}>
                <UniversalChart
                    pluginId={selectedPlugin}
                    props={chartProps}
                    onChartReady={(chart) => {
                        console.log('✅ 圖表已就緒:', chart)
                    }}
                    onError={(error) => {
                        console.error('❌ 圖表錯誤:', error)
                    }}
                />
            </div>

            {/* 說明文字 */}
            <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#2d2d2d', borderRadius: '8px' }}>
                <h3>🎯 插件系統特點</h3>
                <ul>
                    <li>✅ <strong>動態載入</strong>: 圖表插件可以動態載入和卸載</li>
                    <li>✅ <strong>統一介面</strong>: 所有圖表使用相同的UniversalChart組件</li>
                    <li>✅ <strong>配置管理</strong>: 統一的配置管理系統</li>
                    <li>✅ <strong>類型安全</strong>: 完整的TypeScript支持</li>
                    <li>✅ <strong>錯誤處理</strong>: 優雅的錯誤處理和回饋</li>
                    <li>✅ <strong>性能優化</strong>: 延遲載入和緩存機制</li>
                </ul>

                <h3>🔧 添加新圖表的步驟</h3>
                <ol>
                    <li>在 <code>plugins/charts/plugins/</code> 創建新插件文件</li>
                    <li>實現 <code>ChartPlugin</code> 介面</li>
                    <li>在 <code>plugins/charts/index.ts</code> 註冊插件</li>
                    <li>完成！新圖表自動可用</li>
                </ol>
            </div>
        </div>
    )
}

export default PluginSystemDemo