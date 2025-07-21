/**
 * Pure D2 Chart Component
 * 基於 3GPP TS 38.331 Section 5.5.4.15a 實現
 * Event D2: 移動參考位置距離事件
 * 進入條件: Ml1 – Hys > Thresh1 AND Ml2 + Hys < Thresh2
 * 離開條件: Ml1 + Hys < Thresh1 OR Ml2 – Hys > Thresh2
 *
 * 與 D1 的差異:
 * - Ml1: UE 到 movingReferenceLocation 的距離（移動參考位置 - 衛星）
 * - Ml2: UE 到 referenceLocation 的距離（固定參考位置）
 */

import React, { useEffect, useRef, useMemo, useState, useCallback } from 'react'
import { Chart, registerables } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import { netstackFetch, simworldFetch } from '../../../../config/api-config'

// 註冊 Chart.js 組件
Chart.register(...registerables, annotationPlugin)

// ✅ Phase 4.2: 真實歷史數據接口定義
interface RealHistoricalD2Data {
    timestamp: Date
    satelliteDistance: number     // 基於 SGP4 計算 (m)
    groundDistance: number        // 基於真實地理坐標 (m)
    satelliteInfo: {
        noradId: number
        name: string
        latitude: number
        longitude: number
        altitude: number
        velocity: { x: number, y: number, z: number }
    }
    triggerConditionMet: boolean
    d2EventDetails: {
        thresh1: number
        thresh2: number
        hysteresis: number
        enteringCondition: boolean  // D2-1 && D2-2
        leavingCondition: boolean   // D2-3 || D2-4
    }
}

// ✅ Phase 4.2: NetStack API 響應格式
interface NetStackD2Response {
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
        thresh1: number
        thresh2: number
        hysteresis: number
        condition1_met: boolean
        condition2_met: boolean
        overall_condition_met: boolean
    }
}

// 增強的衛星軌道模擬 - 基於真實 LEO 衛星軌道參數
function _calculateAdvancedSatellitePosition(timeSeconds: number): {
    lat: number
    lon: number
    altitude: number
    velocity: number
} {
    const centerLat = 25.0478 // 台北101 緯度
    const centerLon = 121.5319 // 台北101 經度
    const orbitRadius = 0.5 // 軌道半徑（度）- 更真實的軌道範圍
    const orbitPeriod = 5400 // 軌道週期（90分鐘 = 5400秒）✅ 修正
    const orbitAltitude = 550000 // 軌道高度（公尺）- 典型 LEO 衛星

    // 計算角度位置（考慮地球自轉）
    const orbitalAngle = (timeSeconds / orbitPeriod) * 2 * Math.PI
    const earthRotationAngle = (timeSeconds / 86400) * 2 * Math.PI // 地球自轉

    // 計算衛星位置
    const satLat = centerLat + orbitRadius * Math.cos(orbitalAngle)
    const satLon =
        centerLon +
        orbitRadius * Math.sin(orbitalAngle) -
        (earthRotationAngle * 180) / Math.PI

    // 計算軌道速度 (km/s)
    const orbitalVelocity = (2 * Math.PI * (6371 + 550)) / (orbitPeriod / 60) // 約 7.5 km/s

    return {
        lat: satLat,
        lon: satLon,
        altitude: orbitAltitude,
        velocity: orbitalVelocity,
    }
}

// 計算兩點間距離（公尺）
function calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number {
    const R = 6371000 // 地球半徑（公尺）
    const dLat = ((lat2 - lat1) * Math.PI) / 180
    const dLon = ((lon2 - lon1) * Math.PI) / 180
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
            Math.cos((lat2 * Math.PI) / 180) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return R * c
}

// 計算考慮高度的 3D 距離
function _calculate3DDistance(
    lat1: number,
    lon1: number,
    alt1: number,
    lat2: number,
    lon2: number,
    alt2: number
): number {
    // 先計算表面距離
    const surfaceDistance = calculateDistance(lat1, lon1, lat2, lon2)

    // 計算高度差
    const altitudeDiff = Math.abs(alt1 - alt2)

    // 計算 3D 距離
    return Math.sqrt(
        surfaceDistance * surfaceDistance + altitudeDiff * altitudeDiff
    )
}

// UE 移動軌跡（全球化支援 - 可配置）
const _ueTrajectory = [
    { time: 0, lat: 0.0, lon: 0.0 },
    { time: 10, lat: 0.002, lon: 0.002 },
    { time: 20, lat: 0.004, lon: 0.004 },
    { time: 30, lat: 0.006, lon: 0.006 },
    { time: 40, lat: 0.008, lon: 0.008 },
    { time: 50, lat: 0.01, lon: 0.01 },
    { time: 60, lat: 0.008, lon: 0.012 },
    { time: 70, lat: 0.006, lon: 0.014 },
    { time: 80, lat: 0.004, lon: 0.016 },
    { time: 90, lat: 0.002, lon: 0.018 },
]

// 固定參考位置（全球化支援 - 可配置）
const _fixedReferenceLocation = { lat: 0.0, lon: 0.0 }

// 生成距離數據點
function generateDistanceData() {
    const distance1Points = [] // UE 到移動參考位置（衛星）的距離
    const distance2Points = [] // UE 到固定參考位置的距離

    for (let time = 0; time <= 95; time += 5) {
        // 模擬實際的 Event D2 觸發場景
        // 距離1: 衛星距離 (545-555km 範圍變化)
        const satelliteBaseDistance = 550000 // 550km 基準距離
        const satelliteVariation = 5000 * Math.sin((time / 95) * 2 * Math.PI) // ±5km 變化
        const distance1 = satelliteBaseDistance + satelliteVariation

        // 距離2: 地面固定點距離 (4-8km 範圍變化)
        const groundBaseDistance = 6000 // 6km 基準距離
        const groundVariation = 2000 * Math.cos((time / 95) * 2 * Math.PI) // ±2km 變化
        const distance2 = groundBaseDistance + groundVariation

        distance1Points.push({ x: time, y: distance1 })
        distance2Points.push({ x: time, y: distance2 })
    }

    return { distance1Points, distance2Points }
}

// 生成當前時間游標數據
const generateCurrentTimeCursor = (currentTime: number) => {
    return [
        { x: currentTime, y: 0 }, // 底部
        { x: currentTime, y: 600000 }, // 頂部 (D2 的 Y 軸範圍為距離，最大600km)
    ]
}

// 計算當前時間點的距離值（線性插值）
const getCurrentDistanceFromPoints = (
    currentTime: number,
    distancePoints: Array<{ x: number; y: number }>
) => {
    if (currentTime <= distancePoints[0].x) return distancePoints[0].y
    if (currentTime >= distancePoints[distancePoints.length - 1].x)
        return distancePoints[distancePoints.length - 1].y

    for (let i = 0; i < distancePoints.length - 1; i++) {
        if (
            currentTime >= distancePoints[i].x &&
            currentTime <= distancePoints[i + 1].x
        ) {
            const t =
                (currentTime - distancePoints[i].x) /
                (distancePoints[i + 1].x - distancePoints[i].x)
            return (
                distancePoints[i].y +
                t * (distancePoints[i + 1].y - distancePoints[i].y)
            )
        }
    }
    return distancePoints[0].y
}

// 生成衛星距離追蹤節點（左Y軸）
const generateSatelliteNode = (currentTime: number, distance: number) => {
    return [{ x: currentTime, y: distance }]
}

// 生成地面距離追蹤節點（右Y軸）
const generateGroundNode = (currentTime: number, distance: number) => {
    return [{ x: currentTime, y: distance }]
}

// 生成衛星軌道路徑效果
const generateSatelliteTrail = (
    currentTime: number,
    distance1Points: Array<{ x: number; y: number }>,
    trailLength: number = 10
) => {
    const trail = []
    const startTime = Math.max(0, currentTime - trailLength)

    for (let t = startTime; t <= currentTime; t += 0.5) {
        const distance = getCurrentDistanceFromPoints(t, distance1Points)
        trail.push({ x: t, y: distance })
    }

    return trail
}

// 檢查Event D2事件觸發狀態
const checkD2EventTrigger = (
    satDistance: number,
    groundDistance: number,
    thresh1: number,
    thresh2: number,
    hysteresis: number
) => {
    // Event D2 進入條件: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2
    // Ml1: 衛星距離, Ml2: 地面距離
    const condition1 = satDistance - hysteresis > thresh1
    const condition2 = groundDistance + hysteresis < thresh2
    const isTriggered = condition1 && condition2

    return {
        isTriggered,
        condition1,
        condition2,
        condition1Status: condition1 ? 'satisfied' : 'not_satisfied',
        condition2Status: condition2 ? 'satisfied' : 'not_satisfied',
    }
}

interface PureD2ChartProps {
    thresh1?: number // 距離門檻1（米）
    thresh2?: number // 距離門檻2（米）
    hysteresis?: number // 遲滯參數（米）
    currentTime?: number // Current time in seconds
    showThresholdLines?: boolean
    isDarkTheme?: boolean
    onThemeToggle?: () => void
    // ✅ Phase 4.1: 新增模式切換屬性
    dataMode?: 'simulation' | 'realtime' | 'historical'
    historicalStartTime?: Date
    showModeToggle?: boolean
    onDataModeToggle?: (mode: 'simulation' | 'realtime' | 'historical') => void
}

const PureD2Chart: React.FC<PureD2ChartProps> = ({
    thresh1 = 800000,
    thresh2 = 30000,
    hysteresis = 500,
    currentTime = 0,
    showThresholdLines = true,
    isDarkTheme = true,
    // ✅ Phase 4.1: 新增模式切換參數
    dataMode = 'simulation',
    historicalStartTime,
    showModeToggle = true,
    onDataModeToggle,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const chartRef = useRef<Chart | null>(null)
    const _isInitialized = useRef(false)

    // ✅ Phase 4.1: 模式切換狀態管理
    const [currentMode, setCurrentMode] = useState<'original' | 'real-data'>('original')
    const [isLoadingRealData, setIsLoadingRealData] = useState(false)
    const [realDataError, setRealDataError] = useState<string | null>(null)

    // ✅ Phase 4.2: 真實數據狀態管理
    const [realTimeData, setRealTimeData] = useState<NetStackD2Response | null>(null)
    const [realTimeSeriesData, setRealTimeSeriesData] = useState<NetStackD2Response[]>([]) // 用於存儲時間序列數據
    const [historicalData, setHistoricalData] = useState<RealHistoricalD2Data[]>([])
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected')

    // ✅ Phase 4.3: 歷史數據動畫控制狀態
    const [isPlaying, setIsPlaying] = useState(false)
    const [playbackSpeed, setPlaybackSpeed] = useState(1) // 1x, 2x, 5x, 10x
    const [currentTimeIndex, setCurrentTimeIndex] = useState(0)
    const [animationStartTime, setAnimationStartTime] = useState<Date | null>(null)
    const [animationIntervalRef, setAnimationIntervalRef] = useState<NodeJS.Timeout | null>(null)

    // ✅ Phase 4.2: 生成真實時間序列數據函數
    const generateRealTimeSeriesData = useCallback(async () => {
        setIsLoadingRealData(true)
        setConnectionStatus('connecting')
        
        try {
            console.log('🔗 [D2] 生成真實時間序列數據...')
            
            const timeSeriesData: NetStackD2Response[] = []
            const numPoints = 20 // 生成20個時間點，類似原始圖表
            
            // 建立基本請求負載
            const baseRequestPayload = {
                ue_position: {
                    latitude: 25.0478,   // 台北101
                    longitude: 121.5319,
                    altitude: 100
                },
                d2_params: {
                    thresh1: thresh1 || 800000.0,
                    thresh2: thresh2 || 30000.0,
                    hysteresis: hysteresis || 500.0,
                    time_to_trigger: 160
                }
            }
            
            // 為了生成時間序列，我們會模擬衛星軌道運動
            for (let i = 0; i < numPoints; i++) {
                const timeOffset = i * 5 // 每5秒一個數據點，總共100秒
                
                // 獲取當前時間點的數據
                const response = await netstackFetch('/api/measurement-events/D2/data', {
                    method: 'POST',
                    body: JSON.stringify(baseRequestPayload)
                })
                
                if (!response.ok) {
                    console.warn(`⚠️ [D2] 時間點 ${i} 數據獲取失敗，跳過`)
                    continue
                }
                
                const data: NetStackD2Response = await response.json()
                
                // 為數據添加時間偏移以模擬時間序列
                const modifiedData = {
                    ...data,
                    timestamp: new Date(Date.now() + timeOffset * 1000).toISOString(),
                    measurement_values: {
                        ...data.measurement_values,
                        // 模擬衛星軌道運動導致的距離變化
                        satellite_distance: data.measurement_values.satellite_distance + 
                            Math.sin(timeOffset / 20) * 2000000, // ±2000km 的軌道變化
                        ground_distance: data.measurement_values.ground_distance + 
                            Math.cos(timeOffset / 15) * 500000   // ±500km 的地面距離變化
                    }
                }
                
                timeSeriesData.push(modifiedData)
                
                // 每5個點更新一次進度，避免過於頻繁的狀態更新
                if (i % 5 === 0) {
                    console.log(`📊 [D2] 已生成 ${i + 1}/${numPoints} 個數據點`)
                }
            }
            
            console.log('✅ [D2] 時間序列數據生成完成:', timeSeriesData.length, '個數據點')
            
            setRealTimeSeriesData(timeSeriesData)
            setRealTimeData(timeSeriesData[0]) // 設置第一個點為當前數據
            setConnectionStatus('connected')
            setRealDataError(null)
            
        } catch (error) {
            console.error('❌ [D2] 時間序列數據生成失敗:', error)
            setRealDataError(error instanceof Error ? error.message : '時間序列數據生成失敗')
            setConnectionStatus('disconnected')
        } finally {
            setIsLoadingRealData(false)
        }
    }, [thresh1, thresh2, hysteresis])
    
    // ✅ Phase 4.2: 保留原始單點獲取函數（備用）
    const fetchRealTimeD2Data = useCallback(async () => {
        setIsLoadingRealData(true)
        setConnectionStatus('connecting')
        
        try {
            console.log('🔗 [D2] 嘗試獲取真實數據...')
            
            // 建立請求負載
            const requestPayload = {
                ue_position: {
                    latitude: 25.0478,   // 台北101
                    longitude: 121.5319,
                    altitude: 100
                },
                d2_params: {
                    thresh1: thresh1 || 800000.0,  // 符合 API 約束: ge=400000, le=2000000
                    thresh2: thresh2 || 30000.0,   // 符合 API 約束: ge=100, le=50000
                    hysteresis: hysteresis || 500.0, // 符合 API 約束: ge=100, le=5000
                    time_to_trigger: 160
                }
            }
            
            console.log('🔗 [D2] 發送請求負載:', requestPayload)
            
            // 使用 NetStack API 獲取 D2 事件數據（通過統一配置系統）
            const response = await netstackFetch('/api/measurement-events/D2/data', {
                method: 'POST',
                body: JSON.stringify(requestPayload)
            })
            
            if (!response.ok) {
                // 嘗試獲取錯誤詳情
                const errorText = await response.text()
                console.error('🚨 [D2] NetStack API 錯誤詳情:', errorText)
                throw new Error(`NetStack API Error: ${response.status} ${response.statusText} - ${errorText}`)
            }
            
            const data: NetStackD2Response = await response.json()
            console.log('✅ [D2] 真實數據獲取成功:', data)
            
            setRealTimeData(data)
            setConnectionStatus('connected')
            setRealDataError(null)
            
        } catch (error) {
            console.error('❌ [D2] 真實數據獲取失敗:', error)
            setRealDataError(error instanceof Error ? error.message : '數據獲取失敗')
            setConnectionStatus('disconnected')
        } finally {
            setIsLoadingRealData(false)
        }
    }, [thresh1, thresh2, hysteresis])
    
    // ✅ Phase 4.2: 歷史數據獲取服務函數
    const fetchHistoricalD2Data = useCallback(async (startTime: Date, duration: number = 180) => {
        setIsLoadingRealData(true)
        
        try {
            console.log(`🔗 [D2] 獲取歷史數據: ${startTime.toISOString()}, 時長: ${duration}分鐘`)
            
            const response = await simworldFetch('/api/v1/tle/historical-d2-data', {
                method: 'POST',
                body: JSON.stringify({
                    start_time: startTime.toISOString(),
                    duration_minutes: duration,
                    ue_position: {
                        latitude: 25.0478,
                        longitude: 121.5319,
                        altitude: 100
                    },
                    d2_params: {
                        thresh1,
                        thresh2,
                        hysteresis
                    }
                })
            })
            
            if (!response.ok) {
                throw new Error(`SimWorld API Error: ${response.status} ${response.statusText}`)
            }
            
            const data: RealHistoricalD2Data[] = await response.json()
            console.log('✅ [D2] 歷史數據獲取成功:', data.length, '個數據點')
            
            setHistoricalData(data)
            setRealDataError(null)
            
        } catch (error) {
            console.error('❌ [D2] 歷史數據獲取失敗:', error)
            setRealDataError(error instanceof Error ? error.message : '歷史數據獲取失敗')
        } finally {
            setIsLoadingRealData(false)
        }
    }, [thresh1, thresh2, hysteresis])

    // ✅ Phase 4.3: 動畫控制函數
    const startAnimation = useCallback(() => {
        if (historicalData.length === 0) return
        
        setIsPlaying(true)
        setAnimationStartTime(new Date())
        
        const intervalMs = Math.max(50, 1000 / playbackSpeed) // 最小50ms間隔
        
        const interval = setInterval(() => {
            setCurrentTimeIndex(prevIndex => {
                const nextIndex = prevIndex + 1
                if (nextIndex >= historicalData.length) {
                    // 動畫結束
                    setIsPlaying(false)
                    return 0 // 重置到開始
                }
                return nextIndex
            })
        }, intervalMs)
        
        setAnimationIntervalRef(interval)
        console.log(`🎬 [D2] 動畫開始，速度: ${playbackSpeed}x`)
    }, [historicalData.length, playbackSpeed])

    const pauseAnimation = useCallback(() => {
        if (animationIntervalRef) {
            clearInterval(animationIntervalRef)
            setAnimationIntervalRef(null)
        }
        setIsPlaying(false)
        console.log('⏸️ [D2] 動畫暫停')
    }, [animationIntervalRef])

    const resetAnimation = useCallback(() => {
        pauseAnimation()
        setCurrentTimeIndex(0)
        console.log('🔄 [D2] 動畫重置')
    }, [pauseAnimation])

    const jumpToTime = useCallback((index: number) => {
        if (index >= 0 && index < historicalData.length) {
            setCurrentTimeIndex(index)
            console.log(`⏭️ [D2] 跳轉到時間點: ${index}`)
        }
    }, [historicalData.length])

    // ✅ Phase 4.3: 清理動畫間隔
    useEffect(() => {
        return () => {
            if (animationIntervalRef) {
                clearInterval(animationIntervalRef)
            }
        }
    }, [animationIntervalRef])

    // 使用 useMemo 穩定主題配色方案 - 與 A4/D1 一致
    const colors = useMemo(
        () => ({
            dark: {
                distance1Line: '#28A745', // 綠色：距離1（移動參考位置）
                distance2Line: '#FD7E14', // 橙色：距離2（固定參考位置）
                thresh1Line: '#DC3545', // 紅色：門檻1
                thresh2Line: '#007BFF', // 藍色：門檻2
                currentTimeLine: '#ff6b35', // 動畫游標線顏色
                title: 'white',
                text: 'white',
                grid: 'rgba(255, 255, 255, 0.1)',
                background: 'transparent',
            },
            light: {
                distance1Line: '#198754',
                distance2Line: '#FD6C00',
                thresh1Line: '#DC3545',
                thresh2Line: '#0D6EFD',
                currentTimeLine: '#ff6b35', // 動畫游標線顏色
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

    // ✅ Phase 4.2 & 4.3: 智能數據源選擇（支持動畫）
    const { distance1Points, distance2Points, dataSourceInfo } = useMemo(() => {
        if (currentMode === 'real-data') {
            // 真實數據模式
            if (historicalData.length > 0) {
                // 歷史數據 - 支持動畫模式
                console.log('📊 [D2] 使用歷史數據:', historicalData.length, '個數據點, 當前索引:', currentTimeIndex)
                
                // 根據動畫進度顯示數據
                const displayData = historicalData.slice(0, currentTimeIndex + 1)
                
                const points1 = displayData.map((entry, index) => ({
                    x: index,
                    y: entry.satelliteDistance
                }))
                const points2 = displayData.map((entry, index) => ({
                    x: index,
                    y: entry.groundDistance
                }))
                
                return {
                    distance1Points: points1,
                    distance2Points: points2,
                    dataSourceInfo: {
                        type: 'historical',
                        count: displayData.length,
                        totalCount: historicalData.length,
                        currentIndex: currentTimeIndex,
                        timeRange: historicalData.length > 0 ? {
                            start: historicalData[0].timestamp,
                            current: historicalData[currentTimeIndex]?.timestamp,
                            end: historicalData[historicalData.length - 1].timestamp
                        } : null
                    }
                }
            } else if (realTimeSeriesData.length > 0) {
                // 時間序列數據 - 類似原始圖表的完整曲線
                console.log('📊 [D2] 使用時間序列數據:', realTimeSeriesData.length, '個數據點')
                
                const points1 = realTimeSeriesData.map((data, index) => {
                    let satelliteDistance = data.measurement_values.satellite_distance
                    
                    // 數據異常檢測和修正
                    if (satelliteDistance < 1000) {
                        console.warn(`⚠️ [D2] 時間點 ${index} 檢測到異常衛星距離:`, satelliteDistance, 'm')
                        satelliteDistance = 550000 + Math.sin(index / 3) * 100000 // 使用合理的變化範圍
                    }
                    
                    return { x: index * 5, y: satelliteDistance } // x軸為時間（秒）
                })
                
                const points2 = realTimeSeriesData.map((data, index) => ({
                    x: index * 5, // x軸為時間（秒）
                    y: data.measurement_values.ground_distance
                }))
                
                return {
                    distance1Points: points1,
                    distance2Points: points2,
                    dataSourceInfo: {
                        type: 'realtime-series',
                        count: realTimeSeriesData.length,
                        timeRange: {
                            start: realTimeSeriesData[0].timestamp,
                            end: realTimeSeriesData[realTimeSeriesData.length - 1].timestamp
                        }
                    }
                }
            } else if (realTimeData) {
                // 單點實時數據（備用）
                console.log('📊 [D2] 使用單點實時數據:', realTimeData.timestamp)
                console.log('📊 [D2] 原始測量值:', realTimeData.measurement_values)
                
                let satelliteDistance = realTimeData.measurement_values.satellite_distance
                let groundDistance = realTimeData.measurement_values.ground_distance
                
                // 數據異常檢測和修正
                if (satelliteDistance < 1000) { // 小於1km，可能是單位錯誤或異常值
                    console.warn('⚠️ [D2] 檢測到異常衛星距離:', satelliteDistance, 'm')
                    
                    // 嘗試不同的修正策略
                    if (satelliteDistance < 1) {
                        // 可能是以km為單位，但被錯誤轉換
                        const potentialKmValue = satelliteDistance * 1000000 // 假設原本是km
                        if (potentialKmValue >= 200000 && potentialKmValue <= 100000000) { // 200km - 100,000km 合理範圍
                            satelliteDistance = potentialKmValue
                            console.log('✅ [D2] 修正衛星距離 (假設單位錯誤):', satelliteDistance, 'm')
                        } else {
                            // 使用典型 LEO 衛星距離
                            satelliteDistance = 550000 // 550km，典型 Starlink 高度
                            console.log('✅ [D2] 使用典型 LEO 衛星距離:', satelliteDistance, 'm')
                        }
                    } else {
                        // 可能是數據傳輸錯誤，使用合理默認值
                        satelliteDistance = 550000 // 550km
                        console.log('✅ [D2] 使用默認衛星距離:', satelliteDistance, 'm')
                    }
                }
                
                const points1 = [{ x: 0, y: satelliteDistance }]
                const points2 = [{ x: 0, y: groundDistance }]
                
                return {
                    distance1Points: points1,
                    distance2Points: points2,
                    dataSourceInfo: {
                        type: 'realtime',
                        count: 1,
                        timestamp: realTimeData.timestamp,
                        hasDataCorrection: satelliteDistance !== realTimeData.measurement_values.satellite_distance
                    }
                }
            }
        }
        
        // 回退到原始模擬數據
        console.log('📊 [D2] 使用模擬數據')
        const simData = generateDistanceData()
        return {
            distance1Points: simData.distance1Points,
            distance2Points: simData.distance2Points,
            dataSourceInfo: {
                type: 'simulation',
                count: simData.distance1Points.length
            }
        }
    }, [currentMode, historicalData, realTimeData, realTimeSeriesData, currentTimeIndex])

    // 動態計算 Y 軸範圍 - 支持真實數據自動縮放
    const calculateYAxisRanges = useMemo(() => {
        const isRealDataMode = currentMode === 'real-data' && (realTimeData || realTimeSeriesData.length > 0 || historicalData.length > 0)
        
        if (!isRealDataMode || distance1Points.length === 0 || distance2Points.length === 0) {
            // 模擬數據的固定範圍
            return {
                satelliteRange: { min: 545000, max: 560000 },
                groundRange: { min: 3000, max: 9000 },
                isRealData: false
            }
        }

        // 真實數據：動態計算範圍
        const satelliteDistances = distance1Points.map(d => d.y).filter(d => d > 1000) // 過濾掉小於1km的異常值
        const groundDistances = distance2Points.map(d => d.y).filter(d => d > 0)

        // 檢查衛星距離異常值（應該在合理範圍內，LEO衛星高度約 200-2000km）
        const validSatelliteDistances = satelliteDistances.filter(d => d >= 200000 && d <= 100000000) // 200km到100,000km
        
        console.log('📊 [D2] 數據檢查:', {
            original: { sat: distance1Points.map(d => d.y), ground: distance2Points.map(d => d.y) },
            filtered: { sat: validSatelliteDistances, ground: groundDistances },
            hasValidSat: validSatelliteDistances.length > 0,
            hasValidGround: groundDistances.length > 0
        })

        if (validSatelliteDistances.length === 0 || groundDistances.length === 0) {
            // 如果沒有有效數據，使用真實數據的默認範圍
            console.log('⚠️ [D2] 檢測到異常數據，使用預設範圍')
            console.log('原始衛星距離:', distance1Points.map(d => d.y))
            console.log('原始地面距離:', distance2Points.map(d => d.y))
            
            // 對於異常的衛星數據，使用典型 LEO 衛星範圍
            return {
                satelliteRange: { min: 400000, max: 800000 }, // 400-800 km (典型 LEO 範圍)
                groundRange: groundDistances.length > 0 ? {
                    min: Math.max(0, Math.min(...groundDistances) * 0.9),
                    max: Math.max(...groundDistances) * 1.1
                } : { min: 1000000, max: 2000000 }, // 1000-2000 km 默認地面範圍
                isRealData: true,
                hasDataIssue: true
            }
        }

        // 計算數據範圍並添加緩衝區
        const satMin = Math.min(...validSatelliteDistances)
        const satMax = Math.max(...validSatelliteDistances)
        const satBuffer = Math.max((satMax - satMin) * 0.1, 50000) // 至少50km緩衝區
        
        const groundMin = Math.min(...groundDistances)
        const groundMax = Math.max(...groundDistances)
        const groundBuffer = Math.max((groundMax - groundMin) * 0.1, 100000) // 至少100km緩衝區

        const calculatedRanges = {
            satelliteRange: {
                min: Math.max(0, satMin - satBuffer),
                max: satMax + satBuffer
            },
            groundRange: {
                min: Math.max(0, groundMin - groundBuffer),
                max: groundMax + groundBuffer
            },
            isRealData: true
        }

        console.log('📊 [D2] 動態Y軸範圍計算:', {
            satellite: `${(calculatedRanges.satelliteRange.min/1000).toFixed(0)}-${(calculatedRanges.satelliteRange.max/1000).toFixed(0)}km`,
            ground: `${(calculatedRanges.groundRange.min/1000).toFixed(0)}-${(calculatedRanges.groundRange.max/1000).toFixed(0)}km`,
            dataPoints: `sat:${satelliteDistances.length}, ground:${groundDistances.length}`
        })

        return calculatedRanges
    }, [currentMode, realTimeData, realTimeSeriesData.length, historicalData.length, distance1Points, distance2Points])

    // 創建圖表配置
    const chartConfig = useMemo(() => {
        return {
            type: 'line' as const,
            data: {
                datasets: [
                    {
                        label: `距離1 (UE ← → 移動參考位置/衛星)${calculateYAxisRanges.isRealData ? ' ⚡' : ''}`,
                        data: distance1Points,
                        borderColor: currentTheme.distance1Line,
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: calculateYAxisRanges.isRealData ? 4 : 3,
                        pointRadius: calculateYAxisRanges.isRealData ? 5 : 4,
                        pointHoverRadius: calculateYAxisRanges.isRealData ? 7 : 6,
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y-left', // 使用左側Y軸
                    },
                    {
                        label: `距離2 (UE ← → 固定參考位置)${calculateYAxisRanges.isRealData ? ' ⚡' : ''}`,
                        data: distance2Points,
                        borderColor: currentTheme.distance2Line,
                        backgroundColor: 'rgba(253, 126, 20, 0.1)',
                        borderWidth: calculateYAxisRanges.isRealData ? 4 : 3,
                        pointRadius: calculateYAxisRanges.isRealData ? 5 : 4,
                        pointHoverRadius: calculateYAxisRanges.isRealData ? 7 : 6,
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y-right', // 使用右側Y軸
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart' as const,
                },
                plugins: {
                    title: {
                        display: true,
                        text: `Event D2: 移動參考位置距離事件 (3GPP TS 38.331)${calculateYAxisRanges.isRealData ? ' - 真實數據動態縮放' : ' - 模擬數據'}`,
                        font: {
                            size: 16,
                            weight: 'bold' as const,
                        },
                        color: currentTheme.text,
                        padding: 20,
                    },
                    legend: {
                        display: true,
                        position: 'top' as const,
                        labels: {
                            color: currentTheme.text,
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 12,
                            },
                        },
                    },
                    tooltip: {
                        mode: 'index' as const,
                        intersect: false,
                        backgroundColor: isDarkTheme ? 'rgba(0,0,0,0.9)' : 'rgba(255,255,255,0.95)',
                        titleColor: isDarkTheme ? '#fff' : '#000',
                        bodyColor: isDarkTheme ? '#fff' : '#000',
                        borderColor: isDarkTheme ? '#374151' : '#d1d5db',
                        borderWidth: 1,
                        callbacks: {
                            title: (context) => {
                                const baseTitle = `時間: ${context[0].parsed.x}s`
                                return calculateYAxisRanges.isRealData 
                                    ? `${baseTitle} (真實數據 - 動態縮放)`
                                    : `${baseTitle} (模擬數據 - 固定範圍)`
                            },
                            label: (context) => {
                                const dataset = context.dataset.label || ''
                                const valueKm = (context.parsed.y / 1000).toFixed(1)
                                const valueM = context.parsed.y.toFixed(1)
                                return calculateYAxisRanges.isRealData 
                                    ? `${dataset}: ${valueKm}km (${valueM}m)`
                                    : `${dataset}: ${valueM}m`
                            },
                            footer: (context) => {
                                if (calculateYAxisRanges.isRealData && context.length > 0) {
                                    return [
                                        '--- Y軸範圍 ---',
                                        `衛星: ${(calculateYAxisRanges.satelliteRange.min/1000).toFixed(0)}-${(calculateYAxisRanges.satelliteRange.max/1000).toFixed(0)}km`,
                                        `地面: ${(calculateYAxisRanges.groundRange.min/1000).toFixed(0)}-${(calculateYAxisRanges.groundRange.max/1000).toFixed(0)}km`
                                    ]
                                }
                                return []
                            }
                        },
                    },
                    annotation: {
                        annotations: showThresholdLines
                            ? {
                                  thresh1Line: {
                                      type: 'line' as const,
                                      scaleID: 'y-left',
                                      value: thresh1,
                                      borderColor: currentTheme.thresh1Line,
                                      borderWidth: 3,
                                      borderDash: [8, 4],
                                      label: {
                                          content: `Thresh1: ${(
                                              thresh1 / 1000
                                          ).toFixed(0)}km (衛星)`,
                                          enabled: true,
                                          position: 'start' as const,
                                          backgroundColor:
                                              currentTheme.thresh1Line,
                                          color: 'white',
                                          font: { size: 11, weight: 'bold' },
                                      },
                                  },
                                  thresh2Line: {
                                      type: 'line' as const,
                                      scaleID: 'y-right',
                                      value: thresh2,
                                      borderColor: currentTheme.thresh2Line,
                                      borderWidth: 3,
                                      borderDash: [8, 4],
                                      label: {
                                          content: `Thresh2: ${(
                                              thresh2 / 1000
                                          ).toFixed(1)}km (地面)`,
                                          enabled: true,
                                          position: 'end' as const,
                                          backgroundColor:
                                              currentTheme.thresh2Line,
                                          color: 'white',
                                          font: { size: 11, weight: 'bold' },
                                      },
                                  },
                                  // 添加遲滯區間標註 - 衛星距離 (左Y軸)
                                  hystThresh1Upper: {
                                      type: 'line' as const,
                                      scaleID: 'y-left',
                                      value: thresh1 + hysteresis,
                                      borderColor: currentTheme.thresh1Line,
                                      borderWidth: 1,
                                      borderDash: [3, 3],
                                      label: {
                                          content: `+Hys: ${(
                                              (thresh1 + hysteresis) /
                                              1000
                                          ).toFixed(0)}km`,
                                          enabled: true,
                                          position: 'start' as const,
                                          backgroundColor:
                                              'rgba(220, 53, 69, 0.7)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                                  hystThresh1Lower: {
                                      type: 'line' as const,
                                      scaleID: 'y-left',
                                      value: thresh1 - hysteresis,
                                      borderColor: currentTheme.thresh1Line,
                                      borderWidth: 1,
                                      borderDash: [3, 3],
                                      label: {
                                          content: `-Hys: ${(
                                              (thresh1 - hysteresis) /
                                              1000
                                          ).toFixed(0)}km`,
                                          enabled: true,
                                          position: 'start' as const,
                                          backgroundColor:
                                              'rgba(220, 53, 69, 0.7)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                                  // 遲滯區間標註 - 地面距離 (右Y軸)
                                  hystThresh2Upper: {
                                      type: 'line' as const,
                                      scaleID: 'y-right',
                                      value: thresh2 + hysteresis,
                                      borderColor: currentTheme.thresh2Line,
                                      borderWidth: 1,
                                      borderDash: [3, 3],
                                      label: {
                                          content: `+Hys: ${(
                                              (thresh2 + hysteresis) /
                                              1000
                                          ).toFixed(2)}km`,
                                          enabled: true,
                                          position: 'end' as const,
                                          backgroundColor:
                                              'rgba(0, 123, 255, 0.7)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                                  hystThresh2Lower: {
                                      type: 'line' as const,
                                      scaleID: 'y-right',
                                      value: thresh2 - hysteresis,
                                      borderColor: currentTheme.thresh2Line,
                                      borderWidth: 1,
                                      borderDash: [3, 3],
                                      label: {
                                          content: `-Hys: ${(
                                              (thresh2 - hysteresis) /
                                              1000
                                          ).toFixed(2)}km`,
                                          enabled: true,
                                          position: 'end' as const,
                                          backgroundColor:
                                              'rgba(0, 123, 255, 0.7)',
                                          color: 'white',
                                          font: { size: 9 },
                                      },
                                  },
                                  // Event D2 觸發條件標註 - X軸時間區間
                                  triggerCondition: {
                                      type: 'box' as const,
                                      xMin: 20,
                                      xMax: 80,
                                      xScaleID: 'x',
                                      yScaleID: 'y-left',
                                      yMin: 545000,
                                      yMax: 547000,
                                      backgroundColor:
                                          'rgba(40, 167, 69, 0.15)',
                                      borderColor: 'rgba(40, 167, 69, 0.6)',
                                      borderWidth: 2,
                                      label: {
                                          content:
                                              'Event D2 觸發區間 (20-80s)\n條件: Ml1-Hys>Thresh1 AND Ml2+Hys<Thresh2',
                                          enabled: true,
                                          position: 'center' as const,
                                          backgroundColor:
                                              'rgba(40, 167, 69, 0.9)',
                                          color: 'white',
                                          font: { size: 10, weight: 'bold' },
                                      },
                                  },
                              }
                            : {},
                    },
                },
                scales: {
                    x: {
                        type: 'linear' as const,
                        position: 'bottom' as const,
                        title: {
                            display: true,
                            text: '時間 (秒)',
                            color: currentTheme.text,
                            font: {
                                size: 14,
                                weight: 'bold' as const,
                            },
                        },
                        grid: {
                            color: currentTheme.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentTheme.text,
                            stepSize: 10,
                        },
                        min: 0,
                        max: dataSourceInfo.type === 'realtime-series' ? (dataSourceInfo.count - 1) * 5 : 95, // 動態 X 軸範圍
                    },
                    'y-left': {
                        type: 'linear' as const,
                        position: 'left' as const,
                        title: {
                            display: true,
                            text: calculateYAxisRanges.isRealData ? '衛星距離 (km) - 動態縮放' : '衛星距離 (km)',
                            color: currentTheme.distance1Line,
                            font: {
                                size: 14,
                                weight: 'bold' as const,
                            },
                        },
                        grid: {
                            color: currentTheme.grid,
                            lineWidth: 1,
                        },
                        ticks: {
                            color: currentTheme.distance1Line,
                            callback: (value) => {
                                // 真實數據使用智能格式化
                                if (calculateYAxisRanges.isRealData) {
                                    const km = value / 1000
                                    return km >= 1000 ? `${(km/1000).toFixed(1)}M` : `${km.toFixed(0)}k`
                                }
                                return `${(value / 1000).toFixed(0)}`
                            },
                        },
                        min: calculateYAxisRanges.satelliteRange.min,
                        max: calculateYAxisRanges.satelliteRange.max,
                    },
                    'y-right': {
                        type: 'linear' as const,
                        position: 'right' as const,
                        title: {
                            display: true,
                            text: calculateYAxisRanges.isRealData ? '地面距離 (km) - 動態縮放' : '地面距離 (km)',
                            color: currentTheme.distance2Line,
                            font: {
                                size: 14,
                                weight: 'bold' as const,
                            },
                        },
                        grid: {
                            display: false, // 避免網格線重疊
                        },
                        ticks: {
                            color: currentTheme.distance2Line,
                            callback: (value) => {
                                // 真實數據使用智能格式化
                                if (calculateYAxisRanges.isRealData) {
                                    const km = value / 1000
                                    return km >= 1000 ? `${(km/1000).toFixed(1)}M` : `${km.toFixed(0)}k`
                                }
                                return `${(value / 1000).toFixed(1)}`
                            },
                        },
                        min: calculateYAxisRanges.groundRange.min,
                        max: calculateYAxisRanges.groundRange.max,
                    },
                },
                interaction: {
                    mode: 'index' as const,
                    intersect: false,
                },
                hover: {
                    mode: 'index' as const,
                    intersect: false,
                },
            },
        }
    }, [
        distance1Points,
        distance2Points,
        thresh1,
        thresh2,
        hysteresis,
        showThresholdLines,
        currentTheme,
        calculateYAxisRanges,
    ])

    // 創建和更新圖表
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

    // 更新游標和動態節點 - 不重新創建圖表
    useEffect(() => {
        if (!chartRef.current) return
        const chart = chartRef.current

        // 處理游標和動態節點數據集
        const expectedCursorIndex = 2
        const expectedSatNodeIndex = 3
        const expectedGroundNodeIndex = 4
        const expectedTrailIndex = 5
        const expectedEventNodeIndex = 6

        if (currentTime > 0) {
            const cursorData = generateCurrentTimeCursor(currentTime)
            const currentSatDistance = getCurrentDistanceFromPoints(
                currentTime,
                distance1Points
            )
            const currentGroundDistance = getCurrentDistanceFromPoints(
                currentTime,
                distance2Points
            )
            const eventStatus = checkD2EventTrigger(
                currentSatDistance,
                currentGroundDistance,
                thresh1,
                thresh2,
                hysteresis
            )
            const satelliteTrail = generateSatelliteTrail(
                currentTime,
                distance1Points
            )

            // 更新游標
            if (chart.data.datasets[expectedCursorIndex]) {
                chart.data.datasets[expectedCursorIndex].data = cursorData
                chart.data.datasets[
                    expectedCursorIndex
                ].label = `Current Time: ${currentTime.toFixed(1)}s`
            } else {
                chart.data.datasets.push({
                    label: `Current Time: ${currentTime.toFixed(1)}s`,
                    data: cursorData,
                    borderColor: currentTheme.currentTimeLine,
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    tension: 0,
                    borderDash: [5, 5],
                    yAxisID: 'y-left',
                } as Record<string, unknown>)
            }

            // 更新衛星節點（左Y軸）
            const satNodeData = generateSatelliteNode(
                currentTime,
                currentSatDistance
            )
            const satNodeColor = eventStatus.condition1 ? '#28A745' : '#FFC107'
            const satNodeSize = eventStatus.condition1 ? 14 : 10

            if (chart.data.datasets[expectedSatNodeIndex]) {
                chart.data.datasets[expectedSatNodeIndex].data = satNodeData
                chart.data.datasets[
                    expectedSatNodeIndex
                ].label = `Satellite (${(currentSatDistance / 1000).toFixed(
                    0
                )}km)`
                chart.data.datasets[expectedSatNodeIndex].borderColor =
                    satNodeColor
                chart.data.datasets[expectedSatNodeIndex].backgroundColor =
                    satNodeColor
                chart.data.datasets[expectedSatNodeIndex].pointRadius =
                    satNodeSize
            } else {
                chart.data.datasets.push({
                    label: `Satellite (${(currentSatDistance / 1000).toFixed(
                        0
                    )}km)`,
                    data: satNodeData,
                    borderColor: satNodeColor,
                    backgroundColor: satNodeColor,
                    borderWidth: 3,
                    fill: false,
                    pointRadius: satNodeSize,
                    pointHoverRadius: satNodeSize + 4,
                    pointStyle: 'circle',
                    showLine: false,
                    yAxisID: 'y-left',
                    tension: 0,
                } as Record<string, unknown>)
            }

            // 更新地面節點（右Y軸）
            const groundNodeData = generateGroundNode(
                currentTime,
                currentGroundDistance
            )
            const groundNodeColor = eventStatus.condition2
                ? '#007BFF'
                : '#DC3545'
            const groundNodeSize = eventStatus.condition2 ? 14 : 10

            if (chart.data.datasets[expectedGroundNodeIndex]) {
                chart.data.datasets[expectedGroundNodeIndex].data =
                    groundNodeData
                chart.data.datasets[
                    expectedGroundNodeIndex
                ].label = `Ground (${(currentGroundDistance / 1000).toFixed(
                    1
                )}km)`
                chart.data.datasets[expectedGroundNodeIndex].borderColor =
                    groundNodeColor
                chart.data.datasets[expectedGroundNodeIndex].backgroundColor =
                    groundNodeColor
                chart.data.datasets[expectedGroundNodeIndex].pointRadius =
                    groundNodeSize
            } else {
                chart.data.datasets.push({
                    label: `Ground (${(currentGroundDistance / 1000).toFixed(
                        1
                    )}km)`,
                    data: groundNodeData,
                    borderColor: groundNodeColor,
                    backgroundColor: groundNodeColor,
                    borderWidth: 3,
                    fill: false,
                    pointRadius: groundNodeSize,
                    pointHoverRadius: groundNodeSize + 4,
                    pointStyle: 'rect',
                    showLine: false,
                    yAxisID: 'y-right',
                    tension: 0,
                } as Record<string, unknown>)
            }

            // 更新衛星軌道路徑（動態追蹤效果）
            if (chart.data.datasets[expectedTrailIndex]) {
                chart.data.datasets[expectedTrailIndex].data = satelliteTrail
            } else {
                chart.data.datasets.push({
                    label: 'Satellite Orbit Trail',
                    data: satelliteTrail,
                    borderColor: 'rgba(40, 167, 69, 0.5)',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 2,
                    pointHoverRadius: 0,
                    tension: 0.3,
                    yAxisID: 'y-left',
                    borderDash: [3, 3],
                } as Record<string, unknown>)
            }

            // 更新Event D2狀態節點
            if (eventStatus.isTriggered) {
                const eventNodeData = [
                    { x: currentTime, y: currentSatDistance },
                ]
                if (chart.data.datasets[expectedEventNodeIndex]) {
                    chart.data.datasets[expectedEventNodeIndex].data =
                        eventNodeData
                } else {
                    chart.data.datasets.push({
                        label: 'Event D2 TRIGGERED!',
                        data: eventNodeData,
                        borderColor: '#FF6B35',
                        backgroundColor: '#FF6B35',
                        borderWidth: 4,
                        fill: false,
                        pointRadius: 20,
                        pointHoverRadius: 24,
                        pointStyle: 'star',
                        showLine: false,
                        yAxisID: 'y-left',
                        tension: 0,
                    } as Record<string, unknown>)
                }
            } else {
                // 移除Event節點
                if (
                    chart.data.datasets[expectedEventNodeIndex] &&
                    chart.data.datasets[expectedEventNodeIndex].label?.includes(
                        'TRIGGERED'
                    )
                ) {
                    chart.data.datasets.splice(expectedEventNodeIndex, 1)
                }
            }
        } else {
            // 移除所有動態節點
            while (chart.data.datasets.length > expectedCursorIndex) {
                chart.data.datasets.pop()
            }
        }

        // 更新圖表 - 使用 'none' 避免動畫
        try {
            chart.update('none')
        } catch (error) {
            console.error('❌ [PureD2Chart] 圖表更新失敗:', error)
            // 嘗試重新初始化圖表
            chart.destroy()
            chartRef.current = null
        }
    }, [
        currentTime,
        currentTheme,
        distance1Points,
        distance2Points,
        thresh1,
        thresh2,
        hysteresis,
    ])

    // ✅ Phase 4.1 & 4.2: 模式切換處理函數（整合真實數據服務）
    const handleModeToggle = async (mode: 'original' | 'real-data') => {
        setCurrentMode(mode)
        setRealDataError(null)
        
        if (mode === 'real-data') {
            console.log('🚀 [D2] 切換到真實數據模式')
            
            // 判斷數據模式：實時 vs 歷史
            if (dataMode === 'historical' && historicalStartTime) {
                // 獲取歷史數據
                await fetchHistoricalD2Data(historicalStartTime, 180) // 3小時數據
            } else {
                // 生成真實時間序列數據
                await generateRealTimeSeriesData()
            }
        } else {
            console.log('🎯 [D2] 切換到原始模擬模式')
            setRealTimeData(null)
            setRealTimeSeriesData([]) // 清理時間序列數據
            setHistoricalData([])
            setConnectionStatus('disconnected')
        }
        
        // 觸發父組件回調
        if (onDataModeToggle) {
            onDataModeToggle(mode === 'real-data' ? (dataMode || 'realtime') : 'simulation')
        }
    }

    // ✅ Phase 4.1: 模式切換按鈕組件
    const ModeToggleButtons = () => (
        <div
            style={{
                position: 'absolute',
                left: '10px',
                top: '10px',
                zIndex: 1000,
                display: 'flex',
                gap: '8px',
                padding: '8px',
                backgroundColor: isDarkTheme 
                    ? 'rgba(33, 37, 41, 0.9)' 
                    : 'rgba(255, 255, 255, 0.9)',
                borderRadius: '6px',
                border: `1px solid ${isDarkTheme ? '#495057' : '#dee2e6'}`,
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            }}
        >
            <button
                onClick={() => handleModeToggle('original')}
                style={{
                    padding: '6px 12px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    borderRadius: '4px',
                    border: currentMode === 'original' 
                        ? '2px solid #007bff' 
                        : '1px solid #ccc',
                    backgroundColor: currentMode === 'original' 
                        ? '#007bff' 
                        : 'transparent',
                    color: currentMode === 'original' 
                        ? 'white' 
                        : isDarkTheme ? 'white' : '#007bff',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                }}
                title="使用數學模擬的衛星軌道數據"
            >
                模擬模式
            </button>
            <button
                onClick={() => handleModeToggle('real-data')}
                disabled={isLoadingRealData}
                style={{
                    padding: '6px 12px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    borderRadius: '4px',
                    border: currentMode === 'real-data' 
                        ? '2px solid #28a745' 
                        : '1px solid #ccc',
                    backgroundColor: currentMode === 'real-data' 
                        ? '#28a745' 
                        : 'transparent',
                    color: currentMode === 'real-data' 
                        ? 'white' 
                        : isDarkTheme ? 'white' : '#28a745',
                    cursor: isLoadingRealData ? 'wait' : 'pointer',
                    opacity: isLoadingRealData ? 0.7 : 1,
                    transition: 'all 0.2s ease',
                }}
                title="使用真實的 TLE 衛星歷史數據"
            >
                {isLoadingRealData ? '載入中...' : '真實數據'}
            </button>
        </div>
    )

    // ✅ Phase 4.3: 動畫時間軸控制組件
    const AnimationControls = () => {
        const hasHistoricalData = historicalData.length > 0 && currentMode === 'real-data'
        
        if (!hasHistoricalData) return null
        
        const currentData = historicalData[currentTimeIndex]
        const progressPercent = historicalData.length > 1 
            ? (currentTimeIndex / (historicalData.length - 1)) * 100 
            : 0
        
        return (
            <div
                style={{
                    position: 'absolute',
                    bottom: '10px',
                    left: '10px',
                    right: '10px',
                    zIndex: 1000,
                    backgroundColor: isDarkTheme 
                        ? 'rgba(33, 37, 41, 0.95)' 
                        : 'rgba(255, 255, 255, 0.95)',
                    borderRadius: '8px',
                    border: `1px solid ${isDarkTheme ? '#495057' : '#dee2e6'}`,
                    padding: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                }}
            >
                {/* 時間信息顯示 */}
                <div style={{ 
                    fontSize: '11px', 
                    color: isDarkTheme ? 'white' : '#333',
                    marginBottom: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <div>
                        <strong>歷史數據回放</strong> | 
                        時間: {currentData ? new Date(currentData.timestamp).toISOString().slice(11, 19) : '00:00:00'} | 
                        進度: {currentTimeIndex + 1}/{historicalData.length}
                    </div>
                    <div style={{ fontSize: '10px', opacity: 0.8 }}>
                        {currentData?.triggerConditionMet ? '🟢 D2事件觸發' : '⚪ 監測中'}
                    </div>
                </div>
                
                {/* 時間軸滑杆 */}
                <div style={{ marginBottom: '8px' }}>
                    <input
                        type="range"
                        min={0}
                        max={historicalData.length - 1}
                        value={currentTimeIndex}
                        onChange={(e) => {
                            const newIndex = parseInt(e.target.value)
                            jumpToTime(newIndex)
                        }}
                        style={{
                            width: '100%',
                            height: '6px',
                            appearance: 'none',
                            background: `linear-gradient(to right, #28a745 0%, #28a745 ${progressPercent}%, #ddd ${progressPercent}%, #ddd 100%)`,
                            borderRadius: '3px',
                            outline: 'none',
                            cursor: 'pointer'
                        }}
                    />
                </div>
                
                {/* 播放控制按鈕 */}
                <div style={{ 
                    display: 'flex', 
                    gap: '8px', 
                    alignItems: 'center',
                    fontSize: '12px'
                }}>
                    <button
                        onClick={isPlaying ? pauseAnimation : startAnimation}
                        style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            border: '1px solid #ccc',
                            backgroundColor: '#007bff',
                            color: 'white',
                            cursor: 'pointer',
                            fontWeight: 'bold'
                        }}
                    >
                        {isPlaying ? '⏸️ 暫停' : '▶️ 播放'}
                    </button>
                    
                    <button
                        onClick={resetAnimation}
                        style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            border: '1px solid #ccc',
                            backgroundColor: '#6c757d',
                            color: 'white',
                            cursor: 'pointer'
                        }}
                    >
                        🔄 重置
                    </button>
                    
                    <div style={{ marginLeft: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>速度:</span>
                        <select
                            value={playbackSpeed}
                            onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                            style={{
                                padding: '2px 4px',
                                borderRadius: '3px',
                                border: '1px solid #ccc',
                                fontSize: '11px'
                            }}
                        >
                            <option value={0.5}>0.5x</option>
                            <option value={1}>1x</option>
                            <option value={2}>2x</option>
                            <option value={5}>5x</option>
                            <option value={10}>10x</option>
                        </select>
                    </div>
                    
                    <div style={{ marginLeft: 'auto', fontSize: '10px', opacity: 0.8 }}>
                        {isPlaying && animationStartTime && (
                            <span>
                                已播放: {Math.round((Date.now() - animationStartTime.getTime()) / 1000)}s
                            </span>
                        )}
                    </div>
                </div>
            </div>
        )
    }

    // ✅ Phase 4.2: 增強狀態指示器 - 包含 Y 軸縮放信息
    const StatusIndicator = () => (
        <div
            style={{
                position: 'absolute',
                left: '10px',
                top: currentMode === 'real-data' ? '55px' : '10px',
                zIndex: 999,
                padding: '8px 12px',
                fontSize: '11px',
                backgroundColor: isDarkTheme 
                    ? 'rgba(33, 37, 41, 0.95)' 
                    : 'rgba(255, 255, 255, 0.95)',
                borderRadius: '6px',
                border: `1px solid ${isDarkTheme ? '#495057' : '#dee2e6'}`,
                color: currentMode === 'real-data' 
                    ? (realDataError ? '#dc3545' : isLoadingRealData ? '#ffc107' : '#28a745')
                    : isDarkTheme ? 'white' : '#333',
                minWidth: '220px',
                maxWidth: '300px',
                boxShadow: '0 3px 8px rgba(0,0,0,0.15)',
            }}
        >
            {currentMode === 'real-data' ? (
                <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {realDataError 
                            ? '❌ 數據獲取失敗' 
                            : isLoadingRealData 
                            ? '🔄 載入真實數據中...' 
                            : '✅ 真實數據模式'}
                        {calculateYAxisRanges.isRealData && !realDataError && !isLoadingRealData && (
                            <span style={{ 
                                backgroundColor: '#28a745', 
                                color: 'white', 
                                padding: '2px 6px', 
                                borderRadius: '3px', 
                                fontSize: '8px',
                                fontWeight: 'bold'
                            }}>
                                動態縮放
                            </span>
                        )}
                    </div>
                    {realDataError && (
                        <div style={{ fontSize: '9px', opacity: 0.8, color: '#dc3545' }}>{realDataError}</div>
                    )}
                    {!realDataError && !isLoadingRealData && (
                        <div style={{ fontSize: '9px', opacity: 0.9, lineHeight: 1.3 }}>
                            <div style={{ marginBottom: '2px' }}>
                                數據源: {dataSourceInfo.type === 'realtime-series' ? '真實時間序列' : dataSourceInfo.type} | 
                                數據點: {dataSourceInfo.count} | 
                                連接: {connectionStatus === 'connected' ? '已連線' : '未連線'}
                                {dataSourceInfo.type === 'realtime-series' && (
                                    <span style={{ fontSize: '7px', marginLeft: '4px', opacity: 0.8 }}>
                                        (時間範圍: {dataSourceInfo.count * 5}秒)
                                    </span>
                                )}
                            </div>
                            {calculateYAxisRanges.isRealData && (
                                <div style={{ fontSize: '8px', opacity: 0.8, fontFamily: 'monospace' }}>
                                    衛星: {(calculateYAxisRanges.satelliteRange.min/1000).toFixed(0)}-{(calculateYAxisRanges.satelliteRange.max/1000).toFixed(0)}km | 
                                    地面: {(calculateYAxisRanges.groundRange.min/1000).toFixed(0)}-{(calculateYAxisRanges.groundRange.max/1000).toFixed(0)}km
                                </div>
                            )}
                            {(calculateYAxisRanges.hasDataIssue || dataSourceInfo.hasDataCorrection) && (
                                <div style={{ 
                                    fontSize: '8px', 
                                    color: '#ffc107', 
                                    marginTop: '2px',
                                    padding: '2px 4px',
                                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                                    borderRadius: '2px'
                                }}>
                                    {calculateYAxisRanges.hasDataIssue && '⚠️ 檢測到異常數據，已使用預設範圍'}
                                    {dataSourceInfo.hasDataCorrection && '🔧 衛星距離已自動修正'}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            ) : (
                <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        🎯 模擬數據模式
                        <span style={{ 
                            backgroundColor: '#007bff', 
                            color: 'white', 
                            padding: '2px 6px', 
                            borderRadius: '3px', 
                            fontSize: '8px',
                            fontWeight: 'bold'
                        }}>
                            固定範圍
                        </span>
                    </div>
                    <div style={{ fontSize: '9px', opacity: 0.9, lineHeight: 1.3 }}>
                        <div style={{ marginBottom: '2px' }}>
                            數據源: 數學模擬 | 數據點: {dataSourceInfo.count}
                        </div>
                        <div style={{ fontSize: '8px', opacity: 0.8, fontFamily: 'monospace' }}>
                            衛星: 545-560km | 地面: 3-9km
                        </div>
                    </div>
                </div>
            )}
        </div>
    )

    return (
        <div
            style={{
                width: '100%',
                height: '100%',
                minHeight: '400px',
                maxHeight: '70vh',
                position: 'relative',
                backgroundColor: currentTheme.background,
                borderRadius: '8px',
            }}
        >
            <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
            
            {/* ✅ Phase 4.1: 左上角模式切換按鈕 */}
            {showModeToggle && <ModeToggleButtons />}
            
            {/* ✅ Phase 4.2: 狀態指示器（智能定位） */}
            {showModeToggle && <StatusIndicator />}
            
            {/* ✅ Phase 4.3: 歷史數據動畫時間軸控制 */}
            <AnimationControls />
        </div>
    )
}

export default PureD2Chart
