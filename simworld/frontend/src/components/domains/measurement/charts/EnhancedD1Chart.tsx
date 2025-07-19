/**
 * Enhanced D1 Chart Component
 * 增強版 D1 雙重距離測量事件圖表
 * 
 * 新功能：
 * 1. 整合真實 NetStack API 數據
 * 2. 智能服務衛星選擇算法視覺化
 * 3. 多重參考位置支援
 * 4. 實時數據流和模擬數據切換
 * 5. 3GPP TS 38.331 完整合規
 * 
 * 符合 LEO 衛星切換論文研究數據真實性原則
 */

import React, { useEffect, useRef, useMemo, useState, useCallback } from 'react'
import {
    Chart,
    registerables,
    ChartConfiguration,
    Chart as ChartJS
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import { netstackFetch } from '../../../../config/api-config'

// 註冊 Chart.js 組件
Chart.register(...registerables, annotationPlugin)

interface EnhancedD1ChartProps {
    // 基本參數
    thresh1?: number // 服務衛星距離門檻值 (m)
    thresh2?: number // 固定參考位置距離門檻值 (m) 
    hysteresis?: number // 遲滯值 (m)
    currentTime?: number // 當前時間 (s)
    
    // UE 位置
    uePosition?: {
        latitude: number
        longitude: number
        altitude: number
    }
    
    // D1 專屬配置
    minElevationAngle?: number // 最小仰角 (度)
    servingSatelliteId?: string // 指定服務衛星
    referenceLocationId?: string // 參考位置 ID
    timeWindowMs?: number // 時間窗口過濾 (ms)
    
    // 顯示控制
    showThresholdLines?: boolean
    isDarkTheme?: boolean
    useRealData?: boolean // 使用真實數據還是模擬數據
    autoUpdate?: boolean // 自動更新真實數據
    updateInterval?: number // 更新間隔 (ms)
    
    // 回調函數
    onThemeToggle?: () => void
    onDataModeToggle?: () => void
    onTriggerEvent?: (eventData: any) => void
}

interface RealTimeD1Data {
    timestamp: string
    trigger_state: string
    trigger_condition_met: boolean
    measurement_values: {
        serving_satellite: string
        serving_satellite_distance: number
        reference_position_distance: number
        serving_satellite_lat: number
        serving_satellite_lon: number
        serving_satellite_alt: number
        serving_satellite_elevation: number
        reference_position: {
            latitude: number
            longitude: number
            altitude: number
        }
    }
    trigger_details: {
        serving_satellite_distance: number
        reference_position_distance: number
        thresh1: number
        thresh2: number
        hysteresis: number
        condition1_met: boolean
        condition2_met: boolean
        overall_condition_met: boolean
        serving_satellite: string
        elevation_angle: number
        satellite_score: number
    }
    satellite_positions: Record<string, any>
}

interface SimulationD1Data {
    scenario: string
    summary: {
        total_samples: number
        trigger_events: number
        trigger_rate: number
    }
    results: Array<{
        timestamp: string
        trigger_state: string
        trigger_condition_met: boolean
        measurement_values: any
        trigger_details: any
    }>
    statistics: any
}

const EnhancedD1Chart: React.FC<EnhancedD1ChartProps> = ({
    thresh1 = 10000, // 10km 預設服務衛星距離門檻
    thresh2 = 5000,  // 5km 預設固定參考位置距離門檻
    hysteresis = 500, // 500m 預設遲滯
    currentTime = 0,
    uePosition = {
        latitude: 25.0478,
        longitude: 121.5319,
        altitude: 100
    },
    minElevationAngle = 5.0,
    servingSatelliteId = '',
    referenceLocationId = 'default',
    timeWindowMs = 1000,
    showThresholdLines = true,
    isDarkTheme = true,
    useRealData = true,
    autoUpdate = true,
    updateInterval = 2000,
    onThemeToggle,
    onDataModeToggle,
    onTriggerEvent
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const chartRef = useRef<ChartJS | null>(null)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)
    
    // 數據狀態
    const [realTimeData, setRealTimeData] = useState<RealTimeD1Data | null>(null)
    const [simulationData, setSimulationData] = useState<SimulationD1Data | null>(null)
    const [dataHistory, setDataHistory] = useState<Array<{ time: number, data: RealTimeD1Data }>>([]
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected')

    // 主題配色方案
    const colors = useMemo(
        () => ({
            dark: {
                servingSatelliteDistance: '#28A745', // 綠色：服務衛星距離
                referencePositionDistance: '#FF6347', // 橙紅色：固定參考位置距離
                thresh1Line: '#DC3545',              // 紅色：服務衛星門檻
                thresh2Line: '#007BFF',              // 藍色：固定參考位置門檻
                currentTimeLine: '#FF6B35',          // 動畫游標線
                servingSatelliteNode: '#17A2B8',     // 青色：服務衛星節點
                triggerEvent: '#FF1744',             // 亮紅色：觸發事件
                title: 'white',
                text: 'white',
                grid: 'rgba(255, 255, 255, 0.1)',
                background: 'transparent',
            },
            light: {
                servingSatelliteDistance: '#198754',
                referencePositionDistance: '#FF4500',
                thresh1Line: '#DC3545',
                thresh2Line: '#0D6EFD',
                currentTimeLine: '#FF6B35',
                servingSatelliteNode: '#0DCAF0',
                triggerEvent: '#FF1744',
                title: 'black',
                text: '#333333',
                grid: 'rgba(0, 0, 0, 0.1)',
                background: 'white',
            },
        }),
        []
    )

    const currentTheme = useMemo(
        () => (isDarkTheme ? colors.dark : colors.light),
        [isDarkTheme, colors]
    )

    // 獲取真實時間數據
    const fetchRealTimeData = useCallback(async () => {
        if (!useRealData) return
        
        setIsLoading(true)
        setConnectionStatus('connecting')
        
        try {
            const response = await netstackFetch('/api/measurement-events/D1/data', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ue_position: uePosition,
                    d1_params: {
                        thresh1,
                        thresh2,
                        hysteresis,
                        time_to_trigger: 160,
                        min_elevation_angle: minElevationAngle,
                        serving_satellite_id: servingSatelliteId,
                        reference_location_id: referenceLocationId,
                        time_window_ms: timeWindowMs
                    }
                })
            })

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`)
            }

            const data: RealTimeD1Data = await response.json()
            setRealTimeData(data)
            setConnectionStatus('connected')
            setError(null)

            // 添加到歷史數據
            const currentTimeStamp = Date.now() / 1000
            setDataHistory(prev => {
                const newHistory = [...prev, { time: currentTimeStamp, data }]
                return newHistory.slice(-60) // 保留最近60個數據點
            })

            // 觸發事件回調
            if (data.trigger_condition_met && onTriggerEvent) {
                onTriggerEvent(data)
            }

        } catch (err) {
            console.error('❌ [EnhancedD1Chart] 真實數據獲取失敗:', err)
            setError(err instanceof Error ? err.message : '數據獲取失敗')
            setConnectionStatus('disconnected')
        } finally {
            setIsLoading(false)
        }
    }, [useRealData, uePosition, thresh1, thresh2, hysteresis, minElevationAngle, servingSatelliteId, referenceLocationId, timeWindowMs, onTriggerEvent])

    // 獲取模擬數據
    const fetchSimulationData = useCallback(async () => {
        if (useRealData) return
        
        setIsLoading(true)
        
        try {
            const response = await netstackFetch('/api/measurement-events/D1/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scenario_name: 'Enhanced_D1_Simulation',
                    ue_position: uePosition,
                    duration_minutes: 5,
                    sample_interval_seconds: 10,
                    target_satellites: []
                })
            })

            if (!response.ok) {
                throw new Error(`Simulation API Error: ${response.status}`)
            }

            const data: SimulationD1Data = await response.json()
            setSimulationData(data)
            setError(null)

        } catch (err) {
            console.error('❌ [EnhancedD1Chart] 模擬數據獲取失敗:', err)
            setError(err instanceof Error ? err.message : '模擬數據獲取失敗')
        } finally {
            setIsLoading(false)
        }
    }, [useRealData, uePosition])

    // 生成圖表數據
    const chartData = useMemo(() => {
        if (useRealData && dataHistory.length > 0) {
            // 真實數據模式：使用歷史數據點
            const servingSatelliteDistancePoints = dataHistory.map((entry, index) => ({
                x: index,
                y: entry.data.measurement_values.serving_satellite_distance
            }))
            
            const referencePositionDistancePoints = dataHistory.map((entry, index) => ({
                x: index,
                y: entry.data.measurement_values.reference_position_distance
            }))

            return {
                servingSatelliteDistancePoints,
                referencePositionDistancePoints,
                timeLabels: dataHistory.map((entry, index) => index.toString()),
                maxTime: dataHistory.length - 1
            }
        } else if (!useRealData && simulationData) {
            // 模擬數據模式：使用模擬結果
            const results = simulationData.results || []
            const servingSatelliteDistancePoints = results.map((result, index) => ({
                x: index,
                y: result.measurement_values?.serving_satellite_distance || 0
            }))
            
            const referencePositionDistancePoints = results.map((result, index) => ({
                x: index,
                y: result.measurement_values?.reference_position_distance || 0
            }))

            return {
                servingSatelliteDistancePoints,
                referencePositionDistancePoints,
                timeLabels: results.map((_, index) => (index * 10).toString()),
                maxTime: results.length - 1
            }
        } else {
            // 預設模擬數據
            const defaultData = Array.from({ length: 30 }, (_, i) => {
                const time = i * 2
                const servingSatDistance = 10000 + 2000 * Math.sin(time / 10)
                const refPosDistance = 5000 + 1500 * Math.cos(time / 8)
                return {
                    servingSatelliteDistance: { x: i, y: servingSatDistance },
                    referencePositionDistance: { x: i, y: refPosDistance }
                }
            })

            return {
                servingSatelliteDistancePoints: defaultData.map(d => d.servingSatelliteDistance),
                referencePositionDistancePoints: defaultData.map(d => d.referencePositionDistance),
                timeLabels: defaultData.map((_, i) => (i * 2).toString()),
                maxTime: 29
            }
        }
    }, [useRealData, dataHistory, simulationData])

    // 圖表配置
    const chartConfig: ChartConfiguration = useMemo(() => ({
        type: 'line',
        data: {
            datasets: [
                {
                    label: '服務衛星距離 (UE ↔ 智能選擇衛星)',
                    data: chartData.servingSatelliteDistancePoints,
                    borderColor: currentTheme.servingSatelliteDistance,
                    backgroundColor: `${currentTheme.servingSatelliteDistance}20`,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: false,
                    tension: 0.1,
                    yAxisID: 'y-left',
                },
                {
                    label: '固定參考位置距離 (UE ↔ 固定參考點)',
                    data: chartData.referencePositionDistancePoints,
                    borderColor: currentTheme.referencePositionDistance,
                    backgroundColor: `${currentTheme.referencePositionDistance}20`,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: false,
                    tension: 0.1,
                    yAxisID: 'y-right',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 750,
                easing: 'easeInOutQuart',
            },
            plugins: {
                title: {
                    display: true,
                    text: `增強版 Event D1: 雙重距離測量事件 ${useRealData ? '(真實數據)' : '(模擬數據)'}`,
                    font: {
                        size: 16,
                        weight: 'bold',
                    },
                    color: currentTheme.text,
                    padding: 20,
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: currentTheme.text,
                        usePointStyle: true,
                        padding: 20,
                        font: { size: 12 },
                    },
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: (context) => {
                            const index = context[0].dataIndex
                            return useRealData 
                                ? `數據點: ${index + 1}`
                                : `時間: ${chartData.timeLabels[index]}s`
                        },
                        label: (context) => {
                            const value = context.parsed.y
                            const label = context.dataset.label || ''
                            return `${label}: ${(value / 1000).toFixed(2)} km`
                        },
                    },
                },
                annotation: {
                    annotations: showThresholdLines ? {
                        // 服務衛星距離門檻線
                        thresh1Line: {
                            type: 'line',
                            scaleID: 'y-left',
                            value: thresh1,
                            borderColor: currentTheme.thresh1Line,
                            borderWidth: 3,
                            borderDash: [8, 4],
                            label: {
                                content: `服務衛星門檻: ${(thresh1 / 1000).toFixed(1)}km`,
                                enabled: true,
                                position: 'start',
                                backgroundColor: currentTheme.thresh1Line,
                                color: 'white',
                                font: { size: 11, weight: 'bold' },
                            },
                        },
                        // 固定參考位置距離門檻線
                        thresh2Line: {
                            type: 'line',
                            scaleID: 'y-right',
                            value: thresh2,
                            borderColor: currentTheme.thresh2Line,
                            borderWidth: 3,
                            borderDash: [8, 4],
                            label: {
                                content: `參考位置門檻: ${(thresh2 / 1000).toFixed(1)}km`,
                                enabled: true,
                                position: 'end',
                                backgroundColor: currentTheme.thresh2Line,
                                color: 'white',
                                font: { size: 11, weight: 'bold' },
                            },
                        },
                        // 遲滯區間
                        hystZone1: {
                            type: 'box',
                            xMin: 0,
                            xMax: chartData.maxTime,
                            yMin: thresh1 - hysteresis,
                            yMax: thresh1 + hysteresis,
                            xScaleID: 'x',
                            yScaleID: 'y-left',
                            backgroundColor: `${currentTheme.thresh1Line}15`,
                            borderColor: `${currentTheme.thresh1Line}50`,
                            borderWidth: 1,
                        },
                        hystZone2: {
                            type: 'box',
                            xMin: 0,
                            xMax: chartData.maxTime,
                            yMin: thresh2 - hysteresis,
                            yMax: thresh2 + hysteresis,
                            xScaleID: 'x',
                            yScaleID: 'y-right',
                            backgroundColor: `${currentTheme.thresh2Line}15`,
                            borderColor: `${currentTheme.thresh2Line}50`,
                            borderWidth: 1,
                        },
                    } : {},
                },
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: useRealData ? '數據點序列' : '時間 (秒)',
                        color: currentTheme.text,
                        font: { size: 14, weight: 'bold' },
                    },
                    grid: {
                        color: currentTheme.grid,
                        lineWidth: 1,
                    },
                    ticks: {
                        color: currentTheme.text,
                        stepSize: useRealData ? 5 : 10,
                    },
                    min: 0,
                    max: chartData.maxTime,
                },
                'y-left': {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: '服務衛星距離 (km)',
                        color: currentTheme.servingSatelliteDistance,
                        font: { size: 14, weight: 'bold' },
                    },
                    grid: {
                        color: currentTheme.grid,
                        lineWidth: 1,
                    },
                    ticks: {
                        color: currentTheme.servingSatelliteDistance,
                        callback: (value) => `${(Number(value) / 1000).toFixed(1)}`,
                    },
                },
                'y-right': {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: '參考位置距離 (km)',
                        color: currentTheme.referencePositionDistance,
                        font: { size: 14, weight: 'bold' },
                    },
                    grid: { display: false },
                    ticks: {
                        color: currentTheme.referencePositionDistance,
                        callback: (value) => `${(Number(value) / 1000).toFixed(2)}`,
                    },
                },
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
        },
    }), [
        chartData,
        thresh1,
        thresh2,
        hysteresis,
        showThresholdLines,
        currentTheme,
        useRealData
    ])

    // 創建圖表
    useEffect(() => {
        if (!canvasRef.current) return

        const ctx = canvasRef.current.getContext('2d')
        if (!ctx) return

        // 銷毀舊圖表
        if (chartRef.current) {
            chartRef.current.destroy()
        }

        // 創建新圖表
        chartRef.current = new Chart(ctx, chartConfig)

        return () => {
            if (chartRef.current) {
                chartRef.current.destroy()
                chartRef.current = null
            }
        }
    }, [chartConfig])

    // 自動更新真實數據
    useEffect(() => {
        if (autoUpdate && useRealData) {
            fetchRealTimeData() // 立即獲取一次
            
            intervalRef.current = setInterval(() => {
                fetchRealTimeData()
            }, updateInterval)

            return () => {
                if (intervalRef.current) {
                    clearInterval(intervalRef.current)
                }
            }
        } else if (!useRealData) {
            fetchSimulationData() // 獲取模擬數據
        }
    }, [autoUpdate, useRealData, updateInterval, fetchRealTimeData, fetchSimulationData])

    // 控制面板
    const ControlPanel = () => (
        <div style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            backgroundColor: isDarkTheme ? 'rgba(33, 37, 41, 0.9)' : 'rgba(255, 255, 255, 0.9)',
            border: `1px solid ${isDarkTheme ? '#495057' : '#dee2e6'}`,
            borderRadius: '8px',
            padding: '12px',
            fontSize: '12px',
            color: currentTheme.text,
            minWidth: '200px',
            zIndex: 10
        }}>
            <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>
                🎯 增強版 D1 控制面板
            </div>
            
            <div style={{ marginBottom: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <input
                        type="checkbox"
                        checked={useRealData}
                        onChange={onDataModeToggle}
                    />
                    使用真實數據
                </label>
            </div>

            <div style={{ marginBottom: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <input
                        type="checkbox"
                        checked={isDarkTheme}
                        onChange={onThemeToggle}
                    />
                    深色主題
                </label>
            </div>

            {useRealData && (
                <div style={{ marginBottom: '8px' }}>
                    <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '6px',
                        fontSize: '11px' 
                    }}>
                        <div style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            backgroundColor: connectionStatus === 'connected' ? '#28a745' : 
                                           connectionStatus === 'connecting' ? '#ffc107' : '#dc3545'
                        }} />
                        {connectionStatus === 'connected' ? '已連線' : 
                         connectionStatus === 'connecting' ? '連線中' : '已斷線'}
                    </div>
                    
                    {realTimeData && (
                        <div style={{ marginTop: '4px', fontSize: '10px' }}>
                            <div>服務衛星: {realTimeData.measurement_values.serving_satellite}</div>
                            <div>仰角: {realTimeData.measurement_values.serving_satellite_elevation?.toFixed(1)}°</div>
                            <div>觸發狀態: {realTimeData.trigger_condition_met ? '✅ 已觸發' : '⏸️ 監測中'}</div>
                        </div>
                    )}
                </div>
            )}

            {error && (
                <div style={{ 
                    color: '#dc3545', 
                    fontSize: '10px', 
                    marginTop: '8px',
                    maxWidth: '180px',
                    wordWrap: 'break-word'
                }}>
                    ❌ {error}
                </div>
            )}
        </div>
    )

    return (
        <div style={{
            width: '100%',
            height: '100%',
            minHeight: '500px',
            position: 'relative',
            backgroundColor: currentTheme.background,
            borderRadius: '8px',
            border: `1px solid ${isDarkTheme ? '#495057' : '#dee2e6'}`,
            padding: '20px'
        }}>
            <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
            <ControlPanel />
            
            {isLoading && (
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    color: currentTheme.text,
                    backgroundColor: isDarkTheme ? 'rgba(33, 37, 41, 0.8)' : 'rgba(255, 255, 255, 0.8)',
                    padding: '20px',
                    borderRadius: '8px',
                    textAlign: 'center'
                }}>
                    🔄 數據載入中...
                </div>
            )}
        </div>
    )
}

export default EnhancedD1Chart