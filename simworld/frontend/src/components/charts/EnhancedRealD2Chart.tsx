/**
 * EnhancedRealD2Chart - 增強版真實D2圖表
 * 
 * 核心特性：
 * 1. 整合智能數據處理，解決SGP4高頻振蕩問題
 * 2. 對比顯示原始vs處理後的數據效果
 * 3. 實時處理品質評估和建議
 * 4. 清晰的D2觸發時機標示
 */

import React, { useState, useMemo, useCallback, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ChartOptions,
    ChartData,
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import { 
    intelligentDataProcessor, 
    DEFAULT_PROCESSING_CONFIG,
    ProcessingConfig,
    ProcessingResult
} from '../../services/intelligentDataProcessor'

// 註冊 Chart.js 組件
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    annotationPlugin
)

// 原始數據接口
export interface RawD2DataPoint {
    timestamp: string
    satelliteDistance: number
    groundDistance: number
    satellite_distance?: number // 兼容性
    ground_distance?: number // 兼容性
    satelliteInfo?: {
        name: string
        noradId: number
        latitude: number
        longitude: number
        altitude: number
    }
}

// 組件Props
export interface EnhancedRealD2ChartProps {
    // 數據
    rawData: RawD2DataPoint[]
    
    // D2觸發配置
    thresh1?: number // 衛星距離閾值
    thresh2?: number // 地面距離閾值
    hysteresis?: number // 遲滯值
    
    // 處理配置
    processingConfig?: Partial<ProcessingConfig>
    
    // 顯示選項
    showOriginalData?: boolean // 是否顯示原始數據
    showProcessedData?: boolean // 是否顯示處理後數據
    showProcessingMetrics?: boolean // 是否顯示處理指標
    showTriggerIndicators?: boolean // 是否顯示觸發指標
    
    // 圖表配置
    height?: number
    isDarkTheme?: boolean
    
    // 回調函數
    onProcessingComplete?: (result: ProcessingResult) => void
    onTriggerDetected?: (triggers: Array<{
        startTime: number
        endTime: number
        duration: number
        likelihood: 'high' | 'medium' | 'low'
        maxIntensity: number
    }>) => void
}

export const EnhancedRealD2Chart: React.FC<EnhancedRealD2ChartProps> = ({
    rawData,
    thresh1 = 600000, // 600km
    thresh2 = 80000,  // 80km
    hysteresis = 5000, // 5km
    processingConfig,
    showOriginalData = false,
    showProcessedData = true,
    showProcessingMetrics = true,
    showTriggerIndicators = true,
    height = 500,
    isDarkTheme = true,
    onProcessingComplete,
    onTriggerDetected,
}) => {
    // 狀態管理
    const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null)
    const [isProcessing, setIsProcessing] = useState(false)
    const [processingStrategy, setProcessingStrategy] = useState<'conservative' | 'balanced' | 'aggressive' | 'adaptive'>('adaptive')
    const [triggerEvents, setTriggerEvents] = useState<Array<{
        startTime: number
        endTime: number
        duration: number
        likelihood: 'high' | 'medium' | 'low'
        maxIntensity: number
    }>>([])

    // 合併處理配置
    const fullProcessingConfig = useMemo(() => ({
        ...DEFAULT_PROCESSING_CONFIG,
        noisReductionStrategy: processingStrategy,
        ...processingConfig,
    }), [processingConfig, processingStrategy])

    // 主題配置
    const theme = useMemo(() => ({
        background: isDarkTheme ? '#1a1a1a' : '#ffffff',
        text: isDarkTheme ? '#ffffff' : '#333333',
        grid: isDarkTheme ? '#374151' : '#e5e7eb',
        
        // 原始數據 - 半透明，顯示噪聲
        originalSatLine: '#dc354540',
        originalGroundLine: '#ffc10740',
        
        // 處理後數據 - 清晰，主要展示
        processedSatLine: '#00D2FF',
        processedGroundLine: '#FF6B35',
        
        // 閾值線
        thresh1Line: '#dc3545',
        thresh2Line: '#28a745',
        
        // 觸發指標
        triggerZone: '#28a74540',
        triggerBorder: '#28a745',
    }), [isDarkTheme])

    // 檢測觸發事件函數 - 需要在useEffect之前定義
    const detectTriggerEvents = useCallback((data: Array<{satelliteDistance: number, groundDistance: number}>, t1: number, t2: number, hys: number) => {
        const events: Array<{
            startTime: number
            endTime: number
            duration: number
            likelihood: 'high' | 'medium' | 'low'
            maxIntensity: number
        }> = []
        let currentEvent: {
            startTime: number
            startIndex: number
            maxIntensity: number
        } | null = null

        data.forEach((point, index) => {
            const time = index * 10 // 假設10秒間隔
            
            // D2觸發條件
            const condition1 = (point.satelliteDistance - hys) > t1
            const condition2 = (point.groundDistance + hys) < t2
            const triggered = condition1 && condition2

            if (triggered && !currentEvent) {
                // 開始新事件
                currentEvent = {
                    startTime: time,
                    startIndex: index,
                    maxIntensity: 0,
                }
            } else if (triggered && currentEvent) {
                // 更新事件強度
                const intensity = Math.min(
                    (point.satelliteDistance - t1) / (t1 * 0.1),
                    (t2 - point.groundDistance) / (t2 * 0.1)
                )
                currentEvent.maxIntensity = Math.max(currentEvent.maxIntensity, intensity)
            } else if (!triggered && currentEvent) {
                // 結束事件
                const duration = time - currentEvent.startTime
                events.push({
                    ...currentEvent,
                    endTime: time,
                    endIndex: index - 1,
                    duration,
                    likelihood: currentEvent.maxIntensity > 0.8 ? 'high' :
                               currentEvent.maxIntensity > 0.5 ? 'medium' : 'low'
                })
                currentEvent = null
            }
        })

        // 處理結尾的事件
        if (currentEvent) {
            const duration = (data.length - 1) * 10 - currentEvent.startTime
            events.push({
                ...currentEvent,
                endTime: (data.length - 1) * 10,
                endIndex: data.length - 1,
                duration,
                likelihood: currentEvent.maxIntensity > 0.8 ? 'high' :
                           currentEvent.maxIntensity > 0.5 ? 'medium' : 'low'
            })
        }

        return events
    }, [])

    // 數據處理
    useEffect(() => {
        if (!rawData || rawData.length === 0) return

        const processData = async () => {
            setIsProcessing(true)
            
            try {
                // console.log('🔄 開始智能數據處理...', {
                //     dataPoints: rawData.length,
                //     strategy: processingStrategy
                // })

                // 格式化數據為處理器期望的格式
                const formattedData = rawData.map(point => ({
                    satelliteDistance: point.satelliteDistance || point.satellite_distance || 0,
                    groundDistance: point.groundDistance || point.ground_distance || 0,
                    timestamp: point.timestamp,
                    satelliteInfo: point.satelliteInfo,
                }))

                // 應用智能處理
                const result = intelligentDataProcessor.processRealSatelliteData(
                    formattedData,
                    fullProcessingConfig
                )

                setProcessingResult(result)
                
                // 檢測觸發事件
                const triggers = detectTriggerEvents(result.processedData, thresh1, thresh2, hysteresis)
                setTriggerEvents(triggers)
                
                // console.log('✅ 數據處理完成', {
                //     noiseReduction: `${(result.processingMetrics.noiseReductionRate * 100).toFixed(1)}%`,
                //     visualClarity: `${(result.processingMetrics.visualClarityScore * 100).toFixed(1)}%`,
                //     triggers: triggers.length,
                //     recommendations: result.recommendations.length
                // })

                // 觸發回調
                if (onProcessingComplete) {
                    onProcessingComplete(result)
                }

                if (onTriggerDetected) {
                    onTriggerDetected(triggers)
                }

            } catch (error) {
                console.error('❌ 數據處理失敗:', error)
            } finally {
                setIsProcessing(false)
            }
        }

        processData()
    }, [rawData, fullProcessingConfig, thresh1, thresh2, hysteresis, onProcessingComplete, onTriggerDetected])

    // 構建圖表數據
    const chartData: ChartData<'line'> = useMemo(() => {
        if (!processingResult) {
            return { labels: [], datasets: [] }
        }

        const labels = processingResult.processedData.map((_, index) => index * 10)
        const datasets = []

        // 原始數據（可選顯示）
        if (showOriginalData) {
            datasets.push({
                label: '原始衛星距離 (含噪聲)',
                data: processingResult.originalData.map(d => d.satelliteDistance / 1000),
                borderColor: theme.originalSatLine,
                backgroundColor: 'transparent',
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
                tension: 0,
                yAxisID: 'y-satellite',
            })

            datasets.push({
                label: '原始地面距離 (含噪聲)',
                data: processingResult.originalData.map(d => d.groundDistance / 1000),
                borderColor: theme.originalGroundLine,
                backgroundColor: 'transparent',
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
                tension: 0,
                yAxisID: 'y-ground',
            })
        }

        // 處理後數據（主要顯示）
        if (showProcessedData) {
            datasets.push({
                label: '智能處理後 - 衛星距離',
                data: processingResult.processedData.map(d => d.satelliteDistance / 1000),
                borderColor: theme.processedSatLine,
                backgroundColor: `${theme.processedSatLine}20`,
                borderWidth: 3,
                pointRadius: 0,
                pointHoverRadius: 6,
                fill: false,
                tension: 0.3,
                yAxisID: 'y-satellite',
            })

            datasets.push({
                label: '智能處理後 - 地面距離',
                data: processingResult.processedData.map(d => d.groundDistance / 1000),
                borderColor: theme.processedGroundLine,
                backgroundColor: `${theme.processedGroundLine}20`,
                borderWidth: 3,
                pointRadius: 0,
                pointHoverRadius: 6,
                fill: false,
                tension: 0.3,
                yAxisID: 'y-ground',
            })
        }

        return { labels, datasets }
    }, [processingResult, showOriginalData, showProcessedData, theme])

    // 圖表配置
    const chartOptions: ChartOptions<'line'> = useMemo(() => ({
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index' as const,
            intersect: false,
        },
        plugins: {
            title: {
                display: true,
                text: `增強版 D2 事件分析 - ${processingStrategy}處理策略`,
                font: { size: 16, weight: 'bold' },
                color: theme.text,
            },
            legend: {
                display: true,
                position: 'top' as const,
                labels: {
                    color: theme.text,
                    usePointStyle: true,
                    padding: 15,
                },
            },
            tooltip: {
                backgroundColor: isDarkTheme ? 'rgba(33, 37, 41, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                titleColor: theme.text,
                bodyColor: theme.text,
                borderColor: theme.grid,
                borderWidth: 1,
                callbacks: {
                    title: (context) => [
                        `時間: ${context[0].label}s`,
                        `數據處理策略: ${processingStrategy}`,
                    ],
                    label: (context) => {
                        const dataset = context.dataset.label || ''
                        const value = context.parsed.y
                        return `${dataset}: ${value.toFixed(1)} km`
                    },
                    footer: (_context) => {
                        if (processingResult) {
                            const metrics = processingResult.processingMetrics
                            return [
                                '--- 處理品質 ---',
                                `降噪率: ${(metrics.noiseReductionRate * 100).toFixed(1)}%`,
                                `視覺清晰度: ${(metrics.visualClarityScore * 100).toFixed(1)}%`,
                                `物理準確度: ${(metrics.physicalAccuracyScore * 100).toFixed(1)}%`,
                            ]
                        }
                        return []
                    },
                },
            },
            annotation: showTriggerIndicators && processingResult ? {
                annotations: {
                    // 閾值線
                    thresh1Line: {
                        type: 'line' as const,
                        scaleID: 'y-satellite',
                        value: thresh1 / 1000,
                        borderColor: theme.thresh1Line,
                        borderWidth: 2,
                        borderDash: [8, 4],
                        label: {
                            content: `閾值1: ${(thresh1 / 1000).toFixed(0)}km`,
                            enabled: true,
                            position: 'start' as const,
                            backgroundColor: theme.thresh1Line,
                            color: 'white',
                            font: { size: 11, weight: 'bold' },
                        },
                    },
                    thresh2Line: {
                        type: 'line' as const,
                        scaleID: 'y-ground',
                        value: thresh2 / 1000,
                        borderColor: theme.thresh2Line,
                        borderWidth: 2,
                        borderDash: [8, 4],
                        label: {
                            content: `閾值2: ${(thresh2 / 1000).toFixed(1)}km`,
                            enabled: true,
                            position: 'end' as const,
                            backgroundColor: theme.thresh2Line,
                            color: 'white',
                            font: { size: 11, weight: 'bold' },
                        },
                    },
                    // 觸發區間
                    ...Object.fromEntries(
                        triggerEvents.map((event, index) => [
                            `trigger_${index}`,
                            {
                                type: 'box' as const,
                                xMin: event.startTime,
                                xMax: event.endTime,
                                xScaleID: 'x',
                                yScaleID: 'y-satellite',
                                yMin: Math.max(400, (thresh1 / 1000) - 50),
                                yMax: Math.max(450, (thresh1 / 1000) - 30),
                                backgroundColor: theme.triggerZone,
                                borderColor: theme.triggerBorder,
                                borderWidth: 2,
                                label: {
                                    content: `D2觸發 (${event.likelihood})`,
                                    enabled: true,
                                    position: 'center' as const,
                                    backgroundColor: theme.triggerBorder,
                                    color: 'white',
                                    font: { size: 9, weight: 'bold' },
                                },
                            },
                        ])
                    ),
                },
            } : {},
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: '時間 (秒)',
                    color: theme.text,
                    font: { size: 14, weight: 'bold' },
                },
                grid: { color: theme.grid },
                ticks: { 
                    color: theme.text,
                    stepSize: 30,
                },
            },
            'y-satellite': {
                type: 'linear' as const,
                position: 'left' as const,
                title: {
                    display: true,
                    text: '衛星距離 (km)',
                    color: theme.processedSatLine,
                    font: { size: 14, weight: 'bold' },
                },
                grid: { color: theme.grid },
                ticks: { 
                    color: theme.processedSatLine,
                    callback: (value) => `${Number(value).toFixed(0)}`,
                },
            },
            'y-ground': {
                type: 'linear' as const,
                position: 'right' as const,
                title: {
                    display: true,
                    text: '地面距離 (km)',
                    color: theme.processedGroundLine,
                    font: { size: 14, weight: 'bold' },
                },
                grid: { display: false },
                ticks: { 
                    color: theme.processedGroundLine,
                    callback: (value) => `${Number(value).toFixed(1)}`,
                },
            },
        },
    }), [theme, isDarkTheme, showTriggerIndicators, processingResult, triggerEvents, thresh1, thresh2, processingStrategy])

    // 載入狀態
    if (isProcessing) {
        return (
            <div style={{
                height: `${height}px`,
                backgroundColor: theme.background,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '12px',
                border: `2px solid ${theme.grid}`,
            }}>
                <div style={{ textAlign: 'center', color: theme.text }}>
                    <div style={{ fontSize: '24px', marginBottom: '16px' }}>🔄</div>
                    <div>正在應用智能數據處理...</div>
                    <div style={{ fontSize: '14px', opacity: 0.7, marginTop: '8px' }}>
                        策略: {processingStrategy} | 去除SGP4高頻振盪
                    </div>
                </div>
            </div>
        )
    }

    if (!processingResult) {
        return (
            <div style={{
                height: `${height}px`,
                backgroundColor: theme.background,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '12px',
                border: `2px solid ${theme.grid}`,
                color: theme.text,
            }}>
                等待數據載入...
            </div>
        )
    }

    return (
        <div style={{
            backgroundColor: theme.background,
            borderRadius: '12px',
            border: `2px solid ${theme.grid}`,
            padding: '16px',
            position: 'relative',
        }}>
            {/* 控制面板 */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '16px',
                flexWrap: 'wrap',
                gap: '16px',
            }}>
                {/* 處理策略選擇 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <label style={{ color: theme.text, fontSize: '14px', fontWeight: 'bold' }}>
                        處理策略:
                    </label>
                    <select
                        value={processingStrategy}
                        onChange={(e) => setProcessingStrategy(e.target.value as 'conservative' | 'balanced' | 'aggressive' | 'adaptive')}
                        style={{
                            padding: '6px 12px',
                            backgroundColor: isDarkTheme ? '#374151' : '#f3f4f6',
                            color: theme.text,
                            border: `1px solid ${theme.grid}`,
                            borderRadius: '6px',
                            fontSize: '14px',
                        }}
                    >
                        <option value="conservative">保守 (輕度處理)</option>
                        <option value="balanced">平衡 (中度處理)</option>
                        <option value="aggressive">激進 (強力處理)</option>
                        <option value="adaptive">自適應 (智能處理)</option>
                    </select>
                </div>

                {/* 顯示選項 */}
                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: theme.text, fontSize: '14px' }}>
                        <input
                            type="checkbox"
                            checked={showOriginalData}
                            onChange={(e) => setShowOriginalData(e.target.checked)}
                        />
                        顯示原始數據
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: theme.text, fontSize: '14px' }}>
                        <input
                            type="checkbox"
                            checked={showProcessedData}
                            onChange={(e) => setShowProcessedData(e.target.checked)}
                        />
                        顯示處理後數據
                    </label>
                </div>

                {/* 處理指標概覽 */}
                {showProcessingMetrics && (
                    <div style={{
                        display: 'flex',
                        gap: '16px',
                        fontSize: '12px',
                        color: theme.text,
                    }}>
                        <div>
                            🔇 降噪: {(processingResult.processingMetrics.noiseReductionRate * 100).toFixed(1)}%
                        </div>
                        <div>
                            👁️ 清晰度: {(processingResult.processingMetrics.visualClarityScore * 100).toFixed(1)}%
                        </div>
                        <div>
                            🎯 觸發: {triggerEvents.length}個
                        </div>
                    </div>
                )}
            </div>

            {/* 主圖表 */}
            <div style={{ height: `${height}px` }}>
                <Line data={chartData} options={chartOptions} />
            </div>

            {/* 處理建議 */}
            {processingResult.recommendations.length > 0 && (
                <div style={{
                    marginTop: '16px',
                    padding: '12px',
                    backgroundColor: isDarkTheme ? '#2d3748' : '#f7fafc',
                    borderRadius: '8px',
                    borderLeft: `4px solid ${theme.processedSatLine}`,
                }}>
                    <h4 style={{ color: theme.text, fontSize: '14px', marginBottom: '8px', margin: 0 }}>
                        💡 處理建議
                    </h4>
                    <ul style={{ 
                        margin: 0, 
                        paddingLeft: '20px', 
                        color: theme.text, 
                        fontSize: '13px',
                        lineHeight: '1.4',
                    }}>
                        {processingResult.recommendations.map((rec, index) => (
                            <li key={index}>{rec}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}

export default EnhancedRealD2Chart