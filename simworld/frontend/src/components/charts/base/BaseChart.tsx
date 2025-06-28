/**
 * 基礎圖表組件
 * 
 * 提供所有圖表的共用功能和介面
 */
import React from 'react'
import { ChartOptions, ChartData, ChartEvent, ActiveElement } from 'chart.js'

export interface BaseChartProps {
    title?: string
    data: ChartData
    options?: ChartOptions
    width?: number
    height?: number
    className?: string
    isLoading?: boolean
    error?: string | null
    onChartClick?: (event: ChartEvent, elements: ActiveElement[]) => void
    onChartHover?: (event: ChartEvent, elements: ActiveElement[]) => void
}

export interface ChartWrapperProps extends BaseChartProps {
    children: React.ReactNode
}

/**
 * 圖表包裝器組件
 * 提供載入狀態、錯誤處理和統一樣式
 */
export const ChartWrapper: React.FC<ChartWrapperProps> = ({
    title,
    className = '',
    isLoading = false,
    error = null,
    children,
    width,
    height,
}) => {
    const containerStyle: React.CSSProperties = {
        width: width || '100%',
        height: height || 400,
        position: 'relative',
        backgroundColor: 'rgba(0, 0, 0, 0.1)',
        borderRadius: '8px',
        padding: '16px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
    }

    if (isLoading) {
        return (
            <div className={`chart-container ${className}`} style={containerStyle}>
                {title && (
                    <div className="chart-title" style={{ 
                        color: 'white', 
                        fontSize: '18px', 
                        fontWeight: 'bold', 
                        marginBottom: '16px',
                        textAlign: 'center'
                    }}>
                        {title}
                    </div>
                )}
                <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100%',
                    color: 'white',
                    fontSize: '16px'
                }}>
                    🔄 載入中...
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className={`chart-container ${className}`} style={containerStyle}>
                {title && (
                    <div className="chart-title" style={{ 
                        color: 'white', 
                        fontSize: '18px', 
                        fontWeight: 'bold', 
                        marginBottom: '16px',
                        textAlign: 'center'
                    }}>
                        {title}
                    </div>
                )}
                <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100%',
                    color: '#ef4444',
                    fontSize: '16px',
                    textAlign: 'center'
                }}>
                    ❌ {error}
                </div>
            </div>
        )
    }

    return (
        <div className={`chart-container ${className}`} style={containerStyle}>
            {title && (
                <div className="chart-title" style={{ 
                    color: 'white', 
                    fontSize: '18px', 
                    fontWeight: 'bold', 
                    marginBottom: '16px',
                    textAlign: 'center'
                }}>
                    {title}
                </div>
            )}
            <div style={{ height: title ? 'calc(100% - 50px)' : '100%' }}>
                {children}
            </div>
        </div>
    )
}

/**
 * 圖表資料驗證函數
 */
// eslint-disable-next-line react-refresh/only-export-components
export const validateChartData = (data: ChartData): boolean => {
    if (!data || !data.datasets || !Array.isArray(data.datasets)) {
        return false
    }
    
    if (data.datasets.length === 0) {
        return false
    }

    // 檢查每個數據集是否有效
    return data.datasets.every(dataset => 
        dataset && 
        Array.isArray(dataset.data) && 
        dataset.data.length > 0
    )
}

/**
 * 生成預設圖表選項
 */
// eslint-disable-next-line react-refresh/only-export-components
export const getDefaultChartOptions = (overrides: Partial<ChartOptions> = {}): ChartOptions => {
    const defaultOptions: ChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
            },
            tooltip: {
                enabled: true,
                intersect: false,
                mode: 'index',
            },
        },
        scales: {
            x: {
                display: true,
                grid: {
                    display: true,
                },
            },
            y: {
                display: true,
                beginAtZero: true,
                grid: {
                    display: true,
                },
            },
        },
        animation: {
            duration: 750,
        },
    }

    // 深度合併選項
    return mergeChartOptions(defaultOptions, overrides)
}

/**
 * 深度合併圖表選項
 */
const mergeChartOptions = (target: Record<string, unknown>, source: Record<string, unknown>): Record<string, unknown> => {
    const result = { ...target }
    
    for (const key in source) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
            if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
                result[key] = mergeChartOptions(target[key] as Record<string, unknown> || {}, source[key] as Record<string, unknown>)
            } else {
                result[key] = source[key]
            }
        }
    }
    
    return result
}