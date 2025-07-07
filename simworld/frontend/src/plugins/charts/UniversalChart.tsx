/**
 * 通用圖表組件
 * 使用插件系統動態渲染圖表
 */

import React, { useEffect, useRef, useMemo, useCallback } from 'react'
import { Chart } from 'chart.js/auto'
import { ChartRegistry, ChartPlugin } from './ChartRegistry'

interface UniversalChartProps {
    pluginId: string
    props?: Record<string, any>
    width?: number
    height?: number
    className?: string
    style?: React.CSSProperties
    onChartReady?: (chart: Chart) => void
    onError?: (error: Error) => void
}

export const UniversalChart: React.FC<UniversalChartProps> = React.memo(({
    pluginId,
    props = {},
    width,
    height,
    className,
    style,
    onChartReady,
    onError
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const chartRef = useRef<Chart | null>(null)
    const pluginRef = useRef<ChartPlugin | null>(null)
    const isInitialized = useRef(false)

    // 獲取插件
    const plugin = useMemo(() => {
        try {
            const p = ChartRegistry.getPlugin(pluginId)
            if (!p) {
                throw new Error(`未找到插件: ${pluginId}`)
            }
            return p
        } catch (error) {
            console.error('❌ [UniversalChart] 獲取插件失敗:', error)
            onError?.(error as Error)
            return null
        }
    }, [pluginId, onError])

    // 創建圖表配置
    const chartConfig = useMemo(() => {
        if (!plugin) return null
        
        try {
            return ChartRegistry.createChartConfig(pluginId, props)
        } catch (error) {
            console.error('❌ [UniversalChart] 創建圖表配置失敗:', error)
            onError?.(error as Error)
            return null
        }
    }, [plugin, pluginId, props, onError])

    // 初始化圖表
    const initializeChart = useCallback(() => {
        if (!canvasRef.current || !chartConfig || isInitialized.current) {
            return
        }

        const ctx = canvasRef.current.getContext('2d')
        if (!ctx) {
            const error = new Error('無法獲取Canvas 2D上下文')
            console.error('❌ [UniversalChart] Canvas錯誤:', error)
            onError?.(error)
            return
        }

        try {
            console.log(`🎯 [UniversalChart] 初始化圖表: ${plugin?.name}`)
            
            chartRef.current = new Chart(ctx, chartConfig)
            pluginRef.current = plugin
            isInitialized.current = true
            
            console.log(`✅ [UniversalChart] 圖表創建成功: ${plugin?.name}`)
            onChartReady?.(chartRef.current)
            
        } catch (error) {
            console.error('❌ [UniversalChart] 圖表創建失敗:', error)
            onError?.(error as Error)
        }
    }, [chartConfig, plugin, onChartReady, onError])

    // 更新圖表
    const updateChart = useCallback(() => {
        if (!chartRef.current || !isInitialized.current || !chartConfig) {
            return
        }

        try {
            console.log(`🔄 [UniversalChart] 更新圖表: ${plugin?.name}`)
            
            // 更新數據和配置
            chartRef.current.data = chartConfig.data
            chartRef.current.options = chartConfig.options || {}
            
            // 更新圖表
            chartRef.current.update('none')
            
        } catch (error) {
            console.error('❌ [UniversalChart] 圖表更新失敗:', error)
            onError?.(error as Error)
            
            // 嘗試重新初始化
            destroyChart()
            initializeChart()
        }
    }, [chartConfig, plugin?.name, onError, initializeChart])

    // 銷毀圖表
    const destroyChart = useCallback(() => {
        if (chartRef.current) {
            try {
                chartRef.current.destroy()
                console.log(`🗑️ [UniversalChart] 圖表已銷毀: ${pluginRef.current?.name}`)
            } catch (error) {
                console.warn('⚠️ [UniversalChart] 圖表銷毀時發生錯誤:', error)
            }
            
            chartRef.current = null
            pluginRef.current = null
            isInitialized.current = false
        }
    }, [])

    // 初始化效果
    useEffect(() => {
        initializeChart()
        return destroyChart
    }, [initializeChart, destroyChart])

    // 更新效果
    useEffect(() => {
        if (isInitialized.current) {
            updateChart()
        }
    }, [updateChart])

    // 容器樣式
    const containerStyle: React.CSSProperties = {
        width: width || '100%',
        height: height || '100%',
        minHeight: '300px',
        position: 'relative',
        backgroundColor: 'transparent',
        borderRadius: '8px',
        ...style
    }

    // 錯誤狀態渲染
    if (!plugin || !chartConfig) {
        return (
            <div style={containerStyle} className={className}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: '#dc3545',
                    fontSize: '16px',
                    textAlign: 'center',
                    padding: '20px'
                }}>
                    {!plugin ? `插件未找到: ${pluginId}` : '圖表配置錯誤'}
                </div>
            </div>
        )
    }

    return (
        <div style={containerStyle} className={className}>
            <canvas
                ref={canvasRef}
                style={{ width: '100%', height: '100%' }}
            />
        </div>
    )
})

UniversalChart.displayName = 'UniversalChart'

export default UniversalChart

// 便利函數：快速創建特定類型的圖表
export const createA4Chart = (props?: Record<string, any>) => (
    <UniversalChart pluginId="a4-event-chart" props={props} />
)

export const createD1Chart = (props?: Record<string, any>) => (
    <UniversalChart pluginId="d1-event-chart" props={props} />
)