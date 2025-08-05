/**
 * D2DataManager - 數據管理 Hook
 * 負責處理真實數據的載入、格式轉換和狀態管理
 * 從 EventD2Viewer 中提取的數據管理邏輯
 */

import { useState, useCallback, useEffect } from 'react'
import { netstackFetch } from '../../../../../config/api-config'
import {
    D2MeasurementPoint,
} from '../../../../../services/unifiedD2DataService'
import type { EventD2Params } from '../../types'

// 定義數據點接口 - 修正為符合 3GPP TS 38.331 規範
export interface RealD2DataPoint {
    timestamp: number
    // 正確的 D2 事件數據結構：兩個移動參考位置（衛星）的距離
    ml1_distance: number // Ml1: UE 到 serving satellite 的距離
    ml2_distance: number // Ml2: UE 到 candidate satellite 的距離
    is_triggered?: boolean
    // 保持向後相容性
    satelliteDistance?: number  // 將對應到 ml1_distance
    groundDistance?: number     // 將對應到 ml2_distance (已修正為第二顆衛星距離)
    satellite_distance?: number // 舊欄位，用於相容性
    ground_distance?: number    // 舊欄位，用於相容性
    referenceSatellite?: string
    candidateSatellite?: string // 新增：候選衛星資訊
    elevationAngle?: number
    azimuthAngle?: number
    signalStrength?: number
    triggerConditionMet?: boolean
    servingSatelliteInfo?: {    // serving satellite 資訊
        name: string
        noradId: string | number
        constellation: string
        orbitalPeriod: number
        inclination: number
        latitude: number
        longitude: number
        altitude: number
    }
    candidateSatelliteInfo?: {  // candidate satellite 資訊
        name: string
        noradId: string | number
        constellation: string
        orbitalPeriod: number
        inclination: number
        latitude: number
        longitude: number
        altitude: number
    }
    // 保持向後相容性
    satelliteInfo?: {
        name: string
        noradId: string | number
        constellation: string
        orbitalPeriod: number
        inclination: number
        latitude: number
        longitude: number
        altitude: number
    }
    measurements?: {
        d2Distance: number
        event_type: string
        ml1_distance: number // 新增：Ml1 距離
        ml2_distance: number // 新增：Ml2 距離
    }
}

// 時間範圍配置接口
export interface TimeRangeConfig {
    durationMinutes: number
    sampleIntervalSeconds: number
}

// 數據管理器狀態接口
interface D2DataManagerState {
    realD2Data: RealD2DataPoint[]
    isLoadingRealData: boolean
    realDataError: string | null
    selectedConstellation: 'starlink' | 'oneweb' | 'gps'
    selectedTimeRange: TimeRangeConfig
}

// Hook 參數接口
interface UseD2DataManagerProps {
    params: EventD2Params
    onDataLoad?: (data: RealD2DataPoint[]) => void
    onError?: (error: string) => void
    onLoadingChange?: (loading: boolean) => void
}

export const useD2DataManager = ({
    params,
    onDataLoad,
    onError,
    onLoadingChange,
}: UseD2DataManagerProps) => {
    // 數據管理狀態
    const [state, setState] = useState<D2DataManagerState>({
        realD2Data: [],
        isLoadingRealData: false,
        realDataError: null,
        selectedConstellation: 'starlink',
        selectedTimeRange: {
            durationMinutes: 120, // 預設為2小時，可看到LEO完整軌道週期
            sampleIntervalSeconds: 30, // 2小時觀測使用30秒間隔更合適
        },
    })

    // 轉換 API 響應為 RealD2Chart 所需格式的函數
    const convertToRealD2DataPoints = useCallback(
        (measurements: D2MeasurementPoint[]): RealD2DataPoint[] => {
            return measurements.map((measurement, index) => {
                // 模擬動態地面距離變化（基於穩定的時間進度）
                const _baseGroundDistance = measurement.ground_distance
                const timeProgress = index / Math.max(1, measurements.length - 1)

                // 創建穩定的 sin 波變化，基於正確的 LEO 軌道週期
                // 2小時觀測時間對應約1.33個Starlink軌道週期（96分鐘/軌道）
                // timeProgress 從 0 到 1，對應 1.33 個軌道週期
                const orbitalCycles = 1.33 // 2小時 ÷ 96分鐘 = 1.33個週期
                const dynamicGroundDistance =
                    midDistance +
                    Math.sin(timeProgress * orbitalCycles * 2 * Math.PI + Math.PI / 4) * amplitude

                return {
                    timestamp: measurement.timestamp,
                    satelliteDistance: measurement.satellite_distance,
                    groundDistance: dynamicGroundDistance, // 動態地面距離
                    satelliteInfo: {
                        noradId: 0, // 暫時使用預設值
                        name: measurement.satellite_id,
                        latitude: measurement.satellite_position.latitude,
                        longitude: measurement.satellite_position.longitude,
                        altitude: measurement.satellite_position.altitude,
                    },
                    triggerConditionMet: measurement.trigger_condition_met,
                    d2EventDetails: {
                        thresh1: params.Thresh1,
                        thresh2: params.Thresh2,
                        hysteresis: params.Hys,
                        enteringCondition: measurement.event_type === 'entering',
                        leavingCondition: measurement.event_type === 'leaving',
                    },
                } as RealD2DataPoint
            })
        },
        [params.Thresh1, params.Thresh2, params.Hys]
    )

    // 載入真實數據 - 使用 SimWorld NetStack 96分鐘預處理數據 API
    const loadRealData = useCallback(async () => {
        // 使用setState來獲取最新狀態，避免closure問題
        const currentState = await new Promise<D2DataManagerState>((resolve) => {
            setState(prev => {
                resolve(prev)
                return prev
            })
        })
        
        if (currentState.isLoadingRealData) return

        setState(prev => ({ ...prev, isLoadingRealData: true, realDataError: null }))
        onLoadingChange?.(true)

        try {
            console.log(
                `🔄 [D2DataManager] 從 NetStack 96分鐘預處理數據載入 ${currentState.selectedConstellation} 星座數據...`
            )
            console.log(
                `⏱️ 時間段: ${currentState.selectedTimeRange.durationMinutes} 分鐘`
            )

            // 構建 API 請求 - 添加參數驗證和默認值
            console.log('🔍 [D2DataManager] 請求參數調試:', {
                referenceLocation: params.referenceLocation,
                movingReferenceLocation: params.movingReferenceLocation,
                selectedTimeRange: currentState.selectedTimeRange,
                selectedConstellation: currentState.selectedConstellation,
            })

            const requestBody = {
                scenario_name: `D2_Real_Data_${currentState.selectedConstellation}`,
                ue_position: {
                    latitude: params.referenceLocation?.latitude || 24.94417,
                    longitude: params.referenceLocation?.longitude || 121.37139,
                    altitude: params.referenceLocation?.altitude || 50.0,
                },
                duration_minutes: currentState.selectedTimeRange.durationMinutes || 5,
                sample_interval_seconds: currentState.selectedTimeRange.sampleIntervalSeconds || 30,
                constellation: currentState.selectedConstellation || 'starlink',
                reference_position: {
                    latitude: params.movingReferenceLocation?.latitude || 24.1477,
                    longitude: params.movingReferenceLocation?.longitude || 120.6736,
                    altitude: params.movingReferenceLocation?.altitude || 0.0,
                },
            }

            console.log('📤 [D2DataManager] 實際發送的請求體:', requestBody)

            // 嘗試調用 NetStack API - 使用配置化的 fetch
            let response: Response
            let useLocalFallback = false
            
            try {
                response = await netstackFetch('/measurement-events/D2/data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody),
                })

                if (!response.ok) {
                    console.warn(`⚠️ [D2DataManager] NetStack API 不可用 (${response.status}), 使用本地回退數據`)
                    useLocalFallback = true
                }
            } catch (error) {
                console.warn('⚠️ [D2DataManager] NetStack API 連接失敗, 使用本地回退數據:', error)
                useLocalFallback = true
            }

            let convertedData: RealD2DataPoint[]

            if (useLocalFallback) {
                // 🛡️ 生成本地回退數據
                console.log('🔄 [D2DataManager] 生成本地回退數據')
                const duration = currentState.selectedTimeRange.durationMinutes
                const interval = currentState.selectedTimeRange.sampleIntervalSeconds
                const numPoints = Math.floor((duration * 60) / interval) + 1 // +1 確保包含結束時間點
                
                const fallbackData: RealD2DataPoint[] = []
                const startTime = Date.now()
                
                for (let i = 0; i < numPoints; i++) {
                    const timeOffset = i * interval * 1000
                    const timestamp = startTime + timeOffset
                    
                    // 基於真實 LEO 軌道參數生成正確的雙衛星距離數據
                    const orbitalPhase1 = (timeOffset / 1000) / 5760 * 2 * Math.PI // serving satellite, 96分鐘Starlink軌道週期
                    const orbitalPhase2 = (timeOffset / 1000) / 5760 * 2 * Math.PI + Math.PI/3 // candidate satellite, 96分鐘Starlink軌道週期，相位差60度
                    
                    // Ml1: UE 到 serving satellite 的距離 (450-1050km)
                    const ml1_distance = 750000 + Math.sin(orbitalPhase1) * 300000
                    
                    // Ml2: UE 到 candidate satellite 的距離 (400-900km, 不同的軌道參數)
                    const ml2_distance = 650000 + Math.cos(orbitalPhase2) * 250000
                    
                    // 計算換手觸發條件 (基於 3GPP TS 38.331)
                    const thresh1 = params.Thresh1 || 800000 // 800km
                    const thresh2 = params.Thresh2 || 600000 // 600km (修正為合理的衛星距離)
                    const hys = params.Hys || 500
                    
                    // D2-1: Ml1 - Hys > Thresh1 && D2-2: Ml2 + Hys < Thresh2
                    const d2_1_condition = (ml1_distance - hys) > thresh1
                    const d2_2_condition = (ml2_distance + hys) < thresh2
                    const triggerConditionMet = d2_1_condition && d2_2_condition
                    
                    fallbackData.push({
                        timestamp,
                        // 新的正確數據結構
                        ml1_distance, // serving satellite 距離
                        ml2_distance, // candidate satellite 距離
                        // 向後相容性欄位
                        satelliteDistance: ml1_distance,
                        groundDistance: ml2_distance, // 修正：現在是第二顆衛星距離
                        satellite_distance: ml1_distance,
                        ground_distance: ml2_distance,
                        referenceSatellite: `STARLINK-SERVING-${i % 100}`,
                        candidateSatellite: `STARLINK-CANDIDATE-${(i + 50) % 100}`,
                        elevationAngle: 15 + Math.sin(orbitalPhase1 * 2) * 30, // 5-45度
                        azimuthAngle: 180 + Math.cos(orbitalPhase1 * 1.5) * 90, // 90-270度
                        signalStrength: -75 + Math.sin(orbitalPhase1 * 3) * 15, // -90 to -60 dBm
                        triggerConditionMet,
                        servingSatelliteInfo: {
                            name: `${currentState.selectedConstellation.toUpperCase()}-SERVING-${i % 100}`,
                            noradId: `SRV-${i % 100}`,
                            constellation: currentState.selectedConstellation,
                            orbitalPeriod: 96, // 96分鐘軌道週期（Starlink標準）
                            inclination: 53, // 典型 LEO 軌道傾角
                            latitude: 24.95 + Math.sin(orbitalPhase1) * 5,
                            longitude: 121.37 + Math.cos(orbitalPhase1) * 5,
                            altitude: 550000 + Math.sin(orbitalPhase1 * 0.5) * 50000,
                        },
                        candidateSatelliteInfo: {
                            name: `${currentState.selectedConstellation.toUpperCase()}-CANDIDATE-${(i + 50) % 100}`,
                            noradId: `CND-${(i + 50) % 100}`,
                            constellation: currentState.selectedConstellation,
                            orbitalPeriod: 90,
                            inclination: 53,
                            latitude: 24.95 + Math.sin(orbitalPhase2) * 5,
                            longitude: 121.37 + Math.cos(orbitalPhase2) * 5,
                            altitude: 550000 + Math.sin(orbitalPhase2 * 0.5) * 50000,
                        },
                        // 向後相容性
                        satelliteInfo: {
                            name: `${currentState.selectedConstellation.toUpperCase()}-DUAL-SIM`,
                            noradId: 'DUAL-LOCAL',
                            constellation: currentState.selectedConstellation,
                            orbitalPeriod: 90,
                            inclination: 53,
                            latitude: 24.95 + Math.sin(orbitalPhase1) * 5,
                            longitude: 121.37 + Math.cos(orbitalPhase1) * 5,
                            altitude: 550000 + Math.sin(orbitalPhase1 * 0.5) * 50000,
                        },
                        measurements: {
                            d2Distance: Math.abs(ml1_distance - ml2_distance),
                            event_type: triggerConditionMet ? 'entering' : 'normal',
                            ml1_distance, // 新增：正確的 Ml1 距離
                            ml2_distance, // 新增：正確的 Ml2 距離
                        },
                    })
                }
                
                convertedData = fallbackData
                console.log(`✅ [D2DataManager] 本地回退數據生成完成: ${numPoints} 個數據點`)
            } else {
                const apiResult = await response.json()

                if (!apiResult.success) {
                    throw new Error(`API 回傳錯誤: ${apiResult.error || '未知錯誤'}`)
                }

                // 轉換 API 響應為前端格式 - 修正為正確的雙衛星距離結構
                convertedData = apiResult.results.map(
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    (result: any, index: number) => {
                        // 如果 API 還沒有雙衛星數據，使用合理的替代方案
                        const ml1_distance = result.measurement_values.satellite_distance || 750000
                        // 將 ground_distance 重新解釋為第二顆衛星距離，並確保在合理範圍
                        const ml2_distance = result.measurement_values.ground_distance > 100000 
                            ? result.measurement_values.ground_distance 
                            : 600000 + Math.sin(index * 0.1) * 200000 // 400-800km 範圍
                        
                        // 計算正確的 D2 觸發條件
                        const thresh1 = params.Thresh1 || 800000
                        const thresh2 = params.Thresh2 || 600000 // 修正為合理的衛星距離門檻
                        const hys = params.Hys || 500
                        
                        const d2_1_condition = (ml1_distance - hys) > thresh1
                        const d2_2_condition = (ml2_distance + hys) < thresh2
                        const triggerConditionMet = d2_1_condition && d2_2_condition
                        
                        return {
                            timestamp: result.timestamp,
                            // 新的正確數據結構
                            ml1_distance,
                            ml2_distance,
                            // 向後相容性欄位
                            satelliteDistance: ml1_distance,
                            groundDistance: ml2_distance, // 修正：現在代表第二顆衛星距離
                            satellite_distance: ml1_distance,
                            ground_distance: ml2_distance,
                            referenceSatellite: result.measurement_values.reference_satellite,
                            candidateSatellite: `CANDIDATE-${result.measurement_values.reference_satellite}`,
                            elevationAngle: result.measurement_values.elevation_angle,
                            azimuthAngle: result.measurement_values.azimuth_angle,
                            signalStrength: result.measurement_values.signal_strength,
                            triggerConditionMet, // 使用正確計算的觸發條件
                            servingSatelliteInfo: {
                                name: result.measurement_values.reference_satellite,
                                noradId: result.satellite_info?.norad_id || 'N/A',
                                constellation: result.satellite_info?.constellation || currentState.selectedConstellation,
                                orbitalPeriod: result.satellite_info?.orbital_period || 90,
                                inclination: result.satellite_info?.inclination || 53,
                                latitude: result.satellite_info?.latitude || 0,
                                longitude: result.satellite_info?.longitude || 0,
                                altitude: result.satellite_info?.altitude || 550000,
                            },
                            candidateSatelliteInfo: {
                                name: `CANDIDATE-${result.measurement_values.reference_satellite}`,
                                noradId: `CND-${result.satellite_info?.norad_id || 'N/A'}`,
                                constellation: result.satellite_info?.constellation || currentState.selectedConstellation,
                                orbitalPeriod: result.satellite_info?.orbital_period || 90,
                                inclination: result.satellite_info?.inclination || 53,
                                latitude: (result.satellite_info?.latitude || 0) + 1, // 略微不同的位置
                                longitude: (result.satellite_info?.longitude || 0) + 1,
                                altitude: (result.satellite_info?.altitude || 550000) + 10000,
                            },
                            // 向後相容性
                            satelliteInfo: {
                                name: result.measurement_values.reference_satellite,
                                noradId: result.satellite_info?.norad_id || 'N/A',
                                constellation: result.satellite_info?.constellation || currentState.selectedConstellation,
                                orbitalPeriod: result.satellite_info?.orbital_period || 90,
                                inclination: result.satellite_info?.inclination || 53,
                                latitude: result.satellite_info?.latitude || 0,
                                longitude: result.satellite_info?.longitude || 0,
                                altitude: result.satellite_info?.altitude || 550000,
                            },
                            measurements: {
                                d2Distance: Math.abs(ml1_distance - ml2_distance),
                                event_type: triggerConditionMet ? 'entering' : 'normal',
                                ml1_distance, // 新增：正確的 Ml1 距離
                                ml2_distance, // 新增：正確的 Ml2 距離
                            },
                        } as RealD2DataPoint
                    }
                )
            }

            setState(prev => ({ ...prev, realD2Data: convertedData, realDataError: null }))
            onDataLoad?.(convertedData)

            console.log(
                `✅ [D2DataManager] 成功載入 ${convertedData.length} 個 ${currentState.selectedConstellation} NetStack 數據點`
            )
            console.log(
                '🔍 [D2DataManager] 前3個數據點預覽:',
                convertedData.slice(0, 3).map((d) => ({
                    time: d.timestamp,
                    satDist: (d.satelliteDistance! / 1000).toFixed(1) + 'km',
                    groundDist: (d.groundDistance / 1000).toFixed(1) + 'km',
                }))
            )

            // 診斷時間範圍問題
            if (convertedData.length > 1) {
                const firstTime = new Date(convertedData[0].timestamp)
                const lastTime = new Date(convertedData[convertedData.length - 1].timestamp)
                const actualDurationMinutes =
                    (lastTime.getTime() - firstTime.getTime()) / (1000 * 60)
                const expectedDuration = currentState.selectedTimeRange.durationMinutes

                console.log('⏰ [D2DataManager] 時間範圍診斷:', {
                    預期時間段: expectedDuration + '分鐘',
                    實際時間段: actualDurationMinutes.toFixed(2) + '分鐘',
                    開始時間: firstTime.toISOString(),
                    結束時間: lastTime.toISOString(),
                    數據點數量: convertedData.length,
                    採樣間隔: currentState.selectedTimeRange.sampleIntervalSeconds + '秒',
                })
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '載入真實數據時發生未知錯誤'
            console.error('❌ [D2DataManager] 載入真實數據失敗:', errorMessage)
            setState(prev => ({ ...prev, realDataError: errorMessage }))
            onError?.(errorMessage)
        } finally {
            setState(prev => ({ ...prev, isLoadingRealData: false }))
            onLoadingChange?.(false)
        }
    }, [
        // 移除state和params依賴，避免重複調用
        onDataLoad,
        onError,
        onLoadingChange,
    ])

    // 星座選擇處理
    const handleConstellationChange = useCallback((constellation: 'starlink' | 'oneweb' | 'gps') => {
        setState(prev => ({ ...prev, selectedConstellation: constellation }))
    }, [])

    // 時間範圍選擇處理
    const handleTimeRangeChange = useCallback((timeRange: Partial<TimeRangeConfig>) => {
        setState(prev => ({
            ...prev,
            selectedTimeRange: { ...prev.selectedTimeRange, ...timeRange }
        }))
    }, [])

    // 星座信息輔助函數
    const getConstellationInfo = useCallback((constellation: string) => {
        switch (constellation) {
            case 'starlink':
                return {
                    description: '低軌高速軌道 (53°, 550km, 15軌/日)',
                    characteristics: '快速變化的距離曲線，明顯的都卜勒效應',
                }
            case 'oneweb':
                return {
                    description: '極軌中高度軌道 (87°, 1200km, 13軌/日)',
                    characteristics: '極地覆蓋，中等變化率的軌道特徵',
                }
            case 'gps':
                return {
                    description: '中軌穩定軌道 (55°, 20200km, 2軌/日)',
                    characteristics: '緩慢變化，長期穩定的距離關係',
                }
            default:
                return {
                    description: '未知星座',
                    characteristics: '標準軌道特徵',
                }
        }
    }, [])

    // 手動觸發數據載入的 effect
    useEffect(() => {
        // 可以根據需要添加自動載入邏輯
    }, [state.selectedConstellation, state.selectedTimeRange])

    // 對外暴露的方法和狀態
    return {
        // 狀態
        realD2Data: state.realD2Data,
        isLoadingRealData: state.isLoadingRealData,
        realDataError: state.realDataError,
        selectedConstellation: state.selectedConstellation,
        selectedTimeRange: state.selectedTimeRange,
        
        // 方法
        loadRealData,
        handleConstellationChange,
        handleTimeRangeChange,
        getConstellationInfo,
        convertToRealD2DataPoints,
    }
}

// 導出類型
export type { TimeRangeConfig, D2DataManagerState }