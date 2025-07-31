/**
 * Enhanced D2 Chart Component
 * 增強版 D2 移動參考位置距離事件圖表
 *
 * 新功能：
 * 1. 整合真實 NetStack API 數據
 * 2. 多因子衛星選擇算法視覺化
 * 3. 動態參考位置支援
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
    Chart as ChartJS,
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import { netstackFetch } from '../../../../config/api-config'
import { useViewModeManager } from '../../../../hooks/useViewModeManager'
import ViewModeToggle from '../../../common/ViewModeToggle'

// 註冊 Chart.js 組件
Chart.register(...registerables, annotationPlugin)

interface EnhancedD2ChartProps {
    // 基本參數
    thresh1?: number // 衛星距離門檻值 (m)
    thresh2?: number // 地面距離門檻值 (m)
    hysteresis?: number // 遲滯值 (m)
    currentTime?: number // 當前時間 (s)

    // UE 位置
    uePosition?: {
        latitude: number
        longitude: number
        altitude: number
    }

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

interface RealTimeD2Data {
    timestamp: string
    trigger_state: string
    trigger_condition_met: boolean
    measurement_values: {
        reference_satellite: string
        satellite_distance: number
        ground_distance: number
        reference_satellite_lat: number
        reference_satellite_lon: number
        reference_satellite_alt: number
    }
    trigger_details: {
        satellite_distance: number
        ground_distance: number
        thresh1: number
        thresh2: number
        hysteresis: number
        condition1_met: boolean
        condition2_met: boolean
        overall_condition_met: boolean
        reference_satellite: string
    }
    satellite_positions: Record<string, any>
}

interface SimulationD2Data {
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

const EnhancedD2Chart: React.FC<EnhancedD2ChartProps> = ({
    thresh1 = 800000, // 800km 預設衛星距離門檻
    thresh2 = 30000, // 30km 預設地面距離門檻
    hysteresis = 500, // 500m 預設遲滯
    currentTime = 0,
    uePosition = {
        latitude: 25.0478,
        longitude: 121.5319,
        altitude: 100,
    },
    showThresholdLines = true,
    isDarkTheme = true,
    useRealData = false, // 🔧 暫時禁用真實數據，使用靜態測試數據
    autoUpdate = false, // 🔧 暫時禁用自動更新，專注於靜態測試
    updateInterval = 1000, // 更頻繁更新
    onThemeToggle,
    onDataModeToggle,
    onTriggerEvent,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const chartRef = useRef<ChartJS | null>(null)
    const intervalRef = useRef<NodeJS.Timeout | null>(null)

    // ✅ 添加視圖模式管理
    const viewModeManager = useViewModeManager({
        eventType: 'D2',
        defaultMode: 'simple',
        enableLocalStorage: true,
        onModeChange: (mode) => {
            console.log(`D2圖表切換到${mode}模式`)
        },
    })

    // ✅ 根據視圖模式調整行為
    const { currentMode, config } = viewModeManager

    // 數據狀態
    const [realTimeData, setRealTimeData] = useState<RealTimeD2Data | null>(
        null
    )
    const [simulationData, setSimulationData] =
        useState<SimulationD2Data | null>(null)
    const [dataHistory, setDataHistory] = useState<
        Array<{ time: number; data: RealTimeD2Data }>
    >([])
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [connectionStatus, setConnectionStatus] = useState<
        'connected' | 'disconnected' | 'connecting'
    >('disconnected')

    // 主題配色方案
    const colors = useMemo(
        () => ({
            dark: {
                satelliteDistance: '#28A745', // 綠色：衛星距離
                groundDistance: '#FD7E14', // 橙色：地面距離
                thresh1Line: '#DC3545', // 紅色：衛星門檻
                thresh2Line: '#007BFF', // 藍色：地面門檻
                currentTimeLine: '#FF6B35', // 動畫游標線
                referenceNode: '#17A2B8', // 青色：參考衛星節點
                triggerEvent: '#FF1744', // 亮紅色：觸發事件
                title: 'white',
                text: 'white',
                grid: 'rgba(255, 255, 255, 0.1)',
                background: 'transparent',
            },
            light: {
                satelliteDistance: '#198754',
                groundDistance: '#FD6C00',
                thresh1Line: '#DC3545',
                thresh2Line: '#0D6EFD',
                currentTimeLine: '#FF6B35',
                referenceNode: '#0DCAF0',
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
            const response = await netstackFetch(
                '/api/measurement-events/D2/data',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ue_position: uePosition,
                        d2_params: {
                            thresh1,
                            thresh2,
                            hysteresis,
                            time_to_trigger: 160,
                        },
                    }),
                }
            )

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`)
            }

            const data: RealTimeD2Data = await response.json()
            setRealTimeData(data)
            setConnectionStatus('connected')
            setError(null)

            // 添加到歷史數據
            const currentTimeStamp = Date.now() / 1000
            setDataHistory((prev) => {
                const newHistory = [...prev, { time: currentTimeStamp, data }]
                return newHistory.slice(-1800) // 保留最近1800個數據點 (30分鐘)
            })

            // 觸發事件回調
            if (data.trigger_condition_met && onTriggerEvent) {
                onTriggerEvent(data)
            }
        } catch (err) {
            console.error('❌ [EnhancedD2Chart] 真實數據獲取失敗:', err)
            setError(err instanceof Error ? err.message : '數據獲取失敗')
            setConnectionStatus('disconnected')
        } finally {
            setIsLoading(false)
        }
    }, [useRealData, uePosition, thresh1, thresh2, hysteresis, onTriggerEvent])

    // 獲取模擬數據
    const fetchSimulationData = useCallback(async () => {
        if (useRealData) return

        setIsLoading(true)

        try {
            const response = await netstackFetch(
                '/api/measurement-events/D2/simulate',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        scenario_name: 'Enhanced_D2_Simulation',
                        ue_position: uePosition,
                        duration_minutes: 5,
                        sample_interval_seconds: 10,
                        target_satellites: [],
                    }),
                }
            )

            if (!response.ok) {
                throw new Error(`Simulation API Error: ${response.status}`)
            }

            const data: SimulationD2Data = await response.json()
            setSimulationData(data)
            setError(null)
        } catch (err) {
            console.error('❌ [EnhancedD2Chart] 模擬數據獲取失敗:', err)
            setError(err instanceof Error ? err.message : '模擬數據獲取失敗')
        } finally {
            setIsLoading(false)
        }
    }, [useRealData, uePosition])

    // 預繪製軌跡數據狀態
    const [preloadedTrajectory, setPreloadedTrajectory] = useState<
        Array<{
            timestamp: string
            satellite_distance: number
            ground_distance: number
            trigger_condition_met: boolean
            reference_satellite: string
        }>
    >([])
    const [currentTrajectoryIndex, setCurrentTrajectoryIndex] = useState(0)
    const [usePreloadedData, setUsePreloadedData] = useState(true) // 預設啟用軌跡動畫

    // 生成靜態測試數據（確保交叉變化模式正確顯示）
    const generatePreloadedTrajectory = useCallback(() => {
        // 簡單的靜態測試數據，直接手工編寫確保正確
        const trajectoryPoints = [
            // 第1段：綠色上升，橙色下降
            {
                timestamp: '2023-01-01T00:00:00Z',
                satellite_distance: 550,
                ground_distance: 8.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24876',
            },
            {
                timestamp: '2023-01-01T00:00:02Z',
                satellite_distance: 551,
                ground_distance: 7.5,
                trigger_condition_met: false,
                reference_satellite: 'gps_24877',
            },
            {
                timestamp: '2023-01-01T00:00:04Z',
                satellite_distance: 552,
                ground_distance: 7.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24878',
            },
            {
                timestamp: '2023-01-01T00:00:06Z',
                satellite_distance: 553,
                ground_distance: 6.5,
                trigger_condition_met: false,
                reference_satellite: 'gps_24879',
            },
            {
                timestamp: '2023-01-01T00:00:08Z',
                satellite_distance: 554,
                ground_distance: 6.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24880',
            },

            // 第2段：兩線接近交叉點
            {
                timestamp: '2023-01-01T00:00:10Z',
                satellite_distance: 555,
                ground_distance: 5.5,
                trigger_condition_met: true,
                reference_satellite: 'gps_24881',
            },
            {
                timestamp: '2023-01-01T00:00:12Z',
                satellite_distance: 555,
                ground_distance: 5.0,
                trigger_condition_met: true,
                reference_satellite: 'gps_24882',
            },
            {
                timestamp: '2023-01-01T00:00:14Z',
                satellite_distance: 554,
                ground_distance: 4.5,
                trigger_condition_met: true,
                reference_satellite: 'gps_24883',
            },
            {
                timestamp: '2023-01-01T00:00:16Z',
                satellite_distance: 553,
                ground_distance: 4.0,
                trigger_condition_met: true,
                reference_satellite: 'gps_24884',
            },
            {
                timestamp: '2023-01-01T00:00:18Z',
                satellite_distance: 552,
                ground_distance: 3.8,
                trigger_condition_met: true,
                reference_satellite: 'gps_24885',
            },

            // 第3段：交叉後分離
            {
                timestamp: '2023-01-01T00:00:20Z',
                satellite_distance: 551,
                ground_distance: 4.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24886',
            },
            {
                timestamp: '2023-01-01T00:00:22Z',
                satellite_distance: 550,
                ground_distance: 4.5,
                trigger_condition_met: false,
                reference_satellite: 'gps_24887',
            },
            {
                timestamp: '2023-01-01T00:00:24Z',
                satellite_distance: 549,
                ground_distance: 5.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24888',
            },
            {
                timestamp: '2023-01-01T00:00:26Z',
                satellite_distance: 548,
                ground_distance: 5.5,
                trigger_condition_met: false,
                reference_satellite: 'gps_24889',
            },
            {
                timestamp: '2023-01-01T00:00:28Z',
                satellite_distance: 547,
                ground_distance: 6.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24890',
            },

            // 第4段：繼續分離
            {
                timestamp: '2023-01-01T00:00:30Z',
                satellite_distance: 546,
                ground_distance: 6.5,
                trigger_condition_met: false,
                reference_satellite: 'gps_24891',
            },
            {
                timestamp: '2023-01-01T00:00:32Z',
                satellite_distance: 545,
                ground_distance: 7.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24892',
            },
            {
                timestamp: '2023-01-01T00:00:34Z',
                satellite_distance: 545,
                ground_distance: 7.5,
                trigger_condition_met: false,
                reference_satellite: 'gps_24893',
            },
            {
                timestamp: '2023-01-01T00:00:36Z',
                satellite_distance: 546,
                ground_distance: 8.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24894',
            },
            {
                timestamp: '2023-01-01T00:00:38Z',
                satellite_distance: 547,
                ground_distance: 8.0,
                trigger_condition_met: false,
                reference_satellite: 'gps_24895',
            },
        ]

        setPreloadedTrajectory(trajectoryPoints)
        console.log(
            '🎯 [D2] 靜態測試數據已生成，交叉變化模式:',
            trajectoryPoints.length,
            '個數據點'
        )
        console.log(
            '綠色曲線範圍:',
            Math.min(...trajectoryPoints.map((p) => p.satellite_distance)),
            '-',
            Math.max(...trajectoryPoints.map((p) => p.satellite_distance)),
            'km'
        )
        console.log(
            '橙色曲線範圍:',
            Math.min(...trajectoryPoints.map((p) => p.ground_distance)),
            '-',
            Math.max(...trajectoryPoints.map((p) => p.ground_distance)),
            'km'
        )
    }, [])

    // 生成圖表數據
    const chartData = useMemo(() => {
        // 優先使用預繪製軌跡數據
        let dataSource = []
        if (usePreloadedData && preloadedTrajectory.length > 0) {
            // 顯示所有靜態測試數據（暫時禁用動畫）
            dataSource = preloadedTrajectory
        } else if (useRealData && dataHistory.length > 0) {
            // 真實數據模式
            dataSource = dataHistory.map((entry) => ({
                timestamp: entry.data.timestamp,
                satellite_distance:
                    entry.data.measurement_values.satellite_distance,
                ground_distance: entry.data.measurement_values.ground_distance,
                trigger_condition_met: entry.data.trigger_condition_met,
                reference_satellite:
                    entry.data.measurement_values.reference_satellite,
            }))
        } else if (!useRealData && simulationData) {
            // 模擬數據模式：使用模擬結果
            const results = simulationData.results || []
            dataSource = results.map((result) => ({
                timestamp: result.timestamp,
                satellite_distance:
                    result.measurement_values?.satellite_distance || 0,
                ground_distance:
                    result.measurement_values?.ground_distance || 0,
                trigger_condition_met: result.trigger_condition_met,
                reference_satellite:
                    result.measurement_values?.reference_satellite || 'unknown',
            }))
        }

        // 減少console噪音，只在數據變化時記錄
        if (
            dataSource.length !== preloadedTrajectory.length ||
            dataSource.length === 0
        ) {
            console.log('📊 [D2] chartData 更新:', {
                usePreloadedData,
                trajectoryLength: preloadedTrajectory.length,
                dataSourceLength: dataSource.length,
            })
        }

        if (dataSource.length === 0) {
            console.log('❌ [D2] 沒有數據源，返回空圖表')
            // 如果沒有數據，生成預設軌跡
            if (!usePreloadedData) {
                generatePreloadedTrajectory()
            }
            return {
                satelliteDistancePoints: [],
                groundDistancePoints: [],
                timeLabels: [],
                maxTime: 0,
                triggerZones: [],
            }
        }

        const satelliteDistancePoints = dataSource.map((entry, index) => ({
            x: index,
            y: usePreloadedData
                ? entry.satellite_distance  // 預載數據已經是km
                : entry.satellite_distance / 1000, // 真實數據是米，轉換為km
        }))

        const groundDistancePoints = dataSource.map((entry, index) => ({
            x: index,
            y: usePreloadedData
                ? entry.ground_distance  // 預載數據已經是km
                : entry.ground_distance / 1000, // 真實數據是米，轉換為km
        }))

        // 減少重複log，只在數據長度變化時記錄
        const currentPointsCount = satelliteDistancePoints.length
        if (
            currentPointsCount > 0 &&
            currentPointsCount !== preloadedTrajectory.length
        ) {
            console.log('✅ [D2] 數據點生成完成:', currentPointsCount, '點')
        }

        return {
            satelliteDistancePoints,
            groundDistancePoints,
            timeLabels: dataSource.map((_, index) => (index * 2).toString()),
            maxTime: dataSource.length - 1,
            triggerZones: dataSource.map((entry, index) => ({
                x: index,
                triggered: entry.trigger_condition_met,
            })),
        }
    }, [
        usePreloadedData,
        preloadedTrajectory,
        currentTrajectoryIndex,
        useRealData,
        dataHistory,
        simulationData,
    ])

    // 圖表配置
    const chartConfig: ChartConfiguration = useMemo(
        () => ({
            type: 'line',
            data: {
                datasets: [
                    {
                        label: '衛星距離 (UE ↔ 移動參考位置)',
                        data: chartData.satelliteDistancePoints,
                        borderColor: currentTheme.satelliteDistance,
                        backgroundColor: `${currentTheme.satelliteDistance}20`,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y-left',
                    },
                    {
                        label: '地面距離 (UE ↔ 固定參考位置)',
                        data: chartData.groundDistancePoints,
                        borderColor: currentTheme.groundDistance,
                        backgroundColor: `${currentTheme.groundDistance}20`,
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
                // ✅ 根據視圖模式調整動畫速度
                animation: {
                    duration:
                        config.chart.animationSpeed === 'fast'
                            ? 500
                            : config.chart.animationSpeed === 'slow'
                            ? 1500
                            : 750,
                    easing: 'easeInOutQuart',
                },
                plugins: {
                    title: {
                        display: true,
                        text: `增強版 Event D2: 移動參考位置距離事件 ${
                            currentMode === 'simple' ? '(簡易版)' : '(完整版)'
                        }`,
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
                                // 數據已經轉換為km，直接顯示
                                if (label.includes('衛星')) {
                                    return `${label}: ${value.toFixed(1)} km`
                                } else {
                                    return `${label}: ${value.toFixed(2)} km`
                                }
                            },
                        },
                    },
                    // ✅ 根據視圖模式控制技術細節顯示
                    annotation: {
                        annotations:
                            config.chart.showThresholdLines &&
                            showThresholdLines
                                ? {
                                      // ✅ 簡易版：只顯示主要門檻線，標籤簡化
                                      ...(currentMode === 'simple'
                                          ? {
                                                thresh1Line: {
                                                    type: 'line',
                                                    scaleID: 'y-left',
                                                    value: useRealData ? 1300 : 550, // 真實數據使用1300km門檻
                                                    borderColor:
                                                        currentTheme.thresh1Line,
                                                    borderWidth: 3, // 簡易版線條更粗
                                                    borderDash: [5, 5], // 簡化虛線樣式
                                                    label: {
                                                        content: useRealData ? '衛星門檻: 1300km' : '衛星門檻',
                                                        enabled: true,
                                                        position: 'start',
                                                        backgroundColor:
                                                            currentTheme.thresh1Line,
                                                        color: 'white',
                                                        font: {
                                                            size: 12,
                                                            weight: 'bold',
                                                        },
                                                    },
                                                },
                                            }
                                          : {
                                                // ✅ 完整版：顯示詳細門檻線配置
                                                thresh1Line: {
                                                    type: 'line',
                                                    scaleID: 'y-left',
                                                    value: useRealData ? 1300 : 550, // 真實數據使用1300km門檻
                                                    borderColor:
                                                        currentTheme.thresh1Line,
                                                    borderWidth: 2,
                                                    borderDash: [8, 4],
                                                    label: {
                                                        content: useRealData 
                                                            ? '衛星門檻: 1300km'
                                                            : '衛星門檻: 550km',
                                                        enabled: true,
                                                        position: 'start',
                                                        backgroundColor:
                                                            currentTheme.thresh1Line,
                                                        color: 'white',
                                                        font: {
                                                            size: 11,
                                                            weight: 'bold',
                                                        },
                                                    },
                                                },
                                                thresh2Line: {
                                                    type: 'line',
                                                    scaleID: 'y-right',
                                                    value: useRealData ? 1300 : 6, // 真實數據地面距離門檻也約1300km
                                                    borderColor:
                                                        currentTheme.thresh2Line,
                                                    borderWidth: 2,
                                                    borderDash: [8, 4],
                                                    label: {
                                                        content: useRealData
                                                            ? '地面門檻: 1300km'
                                                            : '地面門檻: 6.0km',
                                                        enabled: true,
                                                        position: 'end',
                                                        backgroundColor:
                                                            currentTheme.thresh2Line,
                                                        color: 'white',
                                                        font: {
                                                            size: 11,
                                                            weight: 'bold',
                                                        },
                                                    },
                                                },
                                            }),

                                      // ✅ 技術細節只在完整版顯示
                                      ...(config.chart.showTechnicalDetails
                                          ? {
                                                triggerZone: {
                                                    type: 'box',
                                                    xMin: 7,
                                                    xMax: 22,
                                                    yMin: 545,
                                                    yMax: 555,
                                                    xScaleID: 'x',
                                                    yScaleID: 'y-left',
                                                    backgroundColor:
                                                        'rgba(40, 167, 69, 0.2)',
                                                    borderColor:
                                                        'rgba(40, 167, 69, 0.5)',
                                                    borderWidth: 1,
                                                },
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
                                            }
                                          : {}),
                                  }
                                : {},
                    },
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text:
                                currentMode === 'simple'
                                    ? '時間'
                                    : useRealData
                                    ? '數據點序列'
                                    : '時間 (秒)',
                            color: currentTheme.text,
                            font: { size: 14, weight: 'bold' },
                        },
                        grid: {
                            color: currentTheme.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentTheme.text,
                            stepSize: useRealData ? 5 : 2, // 每2秒顯示一個刻度
                            callback: function (value) {
                                // 靜態模式：顯示秒數，真實模式：顯示數據點序列
                                return useRealData
                                    ? value
                                    : `${Number(value) * 2}s`
                            },
                        },
                        min: 0,
                        max: chartData.maxTime,
                    },
                    'y-left': {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: '衛星距離 (km)',
                            color: currentTheme.satelliteDistance,
                            font: { size: 14, weight: 'bold' },
                        },
                        grid: {
                            color: currentTheme.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentTheme.satelliteDistance,
                            callback: (value) => `${Number(value).toFixed(0)}`,
                        },
                        min: useRealData ? 1100 : 540, // 真實數據範圍 ~1100-1500km，預載數據 540-565km
                        max: useRealData ? 1500 : 565,
                    },
                    'y-right': {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: '地面距離 (km)',
                            color: currentTheme.groundDistance,
                            font: { size: 14, weight: 'bold' },
                        },
                        grid: { display: false },
                        ticks: {
                            color: currentTheme.groundDistance,
                            callback: (value) => `${Number(value).toFixed(1)}`,
                        },
                        min: useRealData ? 1100 : 3, // 真實數據地面距離也約1100-1500km，預載數據 3-9km
                        max: useRealData ? 1500 : 9,
                    },
                },
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
            },
        }),
        [
            chartData,
            thresh1,
            thresh2,
            hysteresis,
            showThresholdLines,
            currentTheme,
            useRealData,
            // ✅ 依賴包含config和currentMode
            config,
            currentMode,
        ]
    )

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

    // 初始化和數據更新（靜態測試模式 - 完全禁用API調用）
    useEffect(() => {
        console.log('🔧 [D2] useEffect觸發:', {
            usePreloadedData,
            useRealData,
            autoUpdate,
            trajectoryLength: preloadedTrajectory.length,
        })

        // 只在軌跡數據為空時生成，避免無限循環
        if (usePreloadedData && preloadedTrajectory.length === 0) {
            console.log('🚀 [D2] 初始化，生成預載軌跡')
            generatePreloadedTrajectory()
            return // 生成軌跡後立即返回，避免任何API調用
        }

        // 在靜態測試期間，完全禁用所有API調用
        if (usePreloadedData) {
            console.log('📊 [D2] 使用預載模式，跳過所有API調用')
            return
        }

        if (autoUpdate && useRealData) {
            console.log('📡 [D2] 啟動真實數據模式')
            fetchRealTimeData() // 立即獲取一次

            intervalRef.current = setInterval(() => {
                fetchRealTimeData()
            }, updateInterval)

            return () => {
                if (intervalRef.current) {
                    clearInterval(intervalRef.current)
                }
            }
        } else if (!useRealData && !usePreloadedData) {
            console.log('🎲 [D2] 啟動模擬數據模式')
            fetchSimulationData() // 獲取模擬數據
        }
    }, [
        autoUpdate,
        useRealData,
        updateInterval,
        fetchRealTimeData,
        fetchSimulationData,
        usePreloadedData,
        preloadedTrajectory.length,
    ])

    // 軌跡動畫進度控制（完全禁用，專注於靜態測試）
    // useEffect暫時移除避免干擾

    // 控制面板
    const ControlPanel = () => (
        <div
            style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                backgroundColor: isDarkTheme
                    ? 'rgba(33, 37, 41, 0.9)'
                    : 'rgba(255, 255, 255, 0.9)',
                border: `1px solid ${isDarkTheme ? '#495057' : '#dee2e6'}`,
                borderRadius: '8px',
                padding: '12px',
                fontSize: '12px',
                color: currentTheme.text,
                minWidth: '200px',
                zIndex: 10,
            }}
        >
            {/* ✅ 添加視圖模式標題 */}
            <div
                style={{
                    marginBottom: '8px',
                    fontWeight: 'bold',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                }}
            >
                🛰️ D2 移動參考位置距離
                <ViewModeToggle
                    viewModeManager={viewModeManager}
                    size="small"
                    showLabel={true}
                    position="top-right"
                />
            </div>

            {/* ✅ 基礎級參數 - 簡易版和完整版都顯示 */}
            <div style={{ marginBottom: '8px' }}>
                <label
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                    }}
                >
                    <input
                        type="checkbox"
                        checked={isDarkTheme}
                        onChange={onThemeToggle}
                    />
                    深色主題
                </label>
            </div>

            {/* ✅ 標準級參數 - 完整版才顯示 */}
            {config.parameters.level !== 'basic' && (
                <div style={{ marginBottom: '8px' }}>
                    <label
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                        }}
                    >
                        <input
                            type="checkbox"
                            checked={usePreloadedData}
                            onChange={() =>
                                setUsePreloadedData(!usePreloadedData)
                            }
                        />
                        軌跡動畫模式
                    </label>
                </div>
            )}

            {/* ✅ 專家級參數 - 只有專家模式顯示 */}
            {config.parameters.showExpertParameters && (
                <div style={{ marginBottom: '8px' }}>
                    <label
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                        }}
                    >
                        <input
                            type="checkbox"
                            checked={useRealData}
                            onChange={onDataModeToggle}
                        />
                        使用真實數據
                    </label>
                </div>
            )}

            {useRealData && (
                <div style={{ marginBottom: '8px' }}>
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            fontSize: '11px',
                        }}
                    >
                        <div
                            style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                backgroundColor:
                                    connectionStatus === 'connected'
                                        ? '#28a745'
                                        : connectionStatus === 'connecting'
                                        ? '#ffc107'
                                        : '#dc3545',
                            }}
                        />
                        {connectionStatus === 'connected'
                            ? '已連線'
                            : connectionStatus === 'connecting'
                            ? '連線中'
                            : '已斷線'}
                    </div>

                    {realTimeData && (
                        <div style={{ marginTop: '4px', fontSize: '10px' }}>
                            <div>
                                參考衛星:{' '}
                                {
                                    realTimeData.measurement_values
                                        .reference_satellite
                                }
                            </div>
                            <div>
                                觸發狀態:{' '}
                                {realTimeData.trigger_condition_met
                                    ? '✅ 已觸發'
                                    : '⏸️ 監測中'}
                            </div>
                        </div>
                    )}

                    {usePreloadedData && (
                        <div style={{ marginTop: '4px', fontSize: '10px' }}>
                            <div>
                                動畫進度: {currentTrajectoryIndex + 1}/
                                {preloadedTrajectory.length}
                            </div>
                            <div>軌跡模式: 交叉變化</div>
                        </div>
                    )}
                </div>
            )}

            {/* ✅ 教育模式說明 - 簡易版顯示 */}
            {config.education.showConceptExplanations && (
                <div
                    style={{
                        marginTop: '12px',
                        fontSize: '11px',
                        color: 'rgba(255,255,255,0.8)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        padding: '8px',
                        borderRadius: '4px',
                    }}
                >
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                        💡 什麼是D2事件？
                    </div>
                    <div>
                        D2事件監測UE與移動參考位置（衛星）的距離變化，當距離滿足特定條件時觸發切換決策。
                    </div>
                </div>
            )}

            {error && (
                <div
                    style={{
                        color: '#dc3545',
                        fontSize: '10px',
                        marginTop: '8px',
                        maxWidth: '180px',
                        wordWrap: 'break-word',
                    }}
                >
                    ❌ {error}
                </div>
            )}
        </div>
    )

    return (
        <div
            style={{
                width: '100%',
                height: '100%',
                minHeight: '500px',
                position: 'relative',
                backgroundColor: currentTheme.background,
                borderRadius: '8px',
                border: `1px solid ${isDarkTheme ? '#495057' : '#dee2e6'}`,
                padding: '20px',
            }}
        >
            <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
            <ControlPanel />

            {isLoading && (
                <div
                    style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        color: currentTheme.text,
                        backgroundColor: isDarkTheme
                            ? 'rgba(33, 37, 41, 0.8)'
                            : 'rgba(255, 255, 255, 0.8)',
                        padding: '20px',
                        borderRadius: '8px',
                        textAlign: 'center',
                    }}
                >
                    🔄 數據載入中...
                </div>
            )}
        </div>
    )
}

export default EnhancedD2Chart
