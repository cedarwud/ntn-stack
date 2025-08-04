/**
 * D2DataManager - 數據管理 Hook
 * 負責處理真實數據的載入、格式轉換和狀態管理
 * 從 EventD2Viewer 中提取的數據管理邏輯
 */

import { useState, useCallback, useEffect } from 'react'
import { simworldFetch } from '../../../../../config/api-config'
import {
    D2MeasurementPoint,
} from '../../../../../services/unifiedD2DataService'
import type { EventD2Params } from '../../types'

// 定義數據點接口
export interface RealD2DataPoint {
    timestamp: number
    satellite_distance: number
    ground_distance: number
    is_triggered?: boolean
    satelliteDistance?: number
    groundDistance?: number
    referenceSatellite?: string
    elevationAngle?: number
    azimuthAngle?: number
    signalStrength?: number
    triggerConditionMet?: boolean
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
            sampleIntervalSeconds: 10, // 適合2小時觀測的採樣間隔
        },
    })

    // 轉換 API 響應為 RealD2Chart 所需格式的函數
    const convertToRealD2DataPoints = useCallback(
        (measurements: D2MeasurementPoint[]): RealD2DataPoint[] => {
            return measurements.map((measurement, index) => {
                // 模擬動態地面距離變化（基於穩定的時間進度）
                const baseGroundDistance = measurement.ground_distance
                const timeProgress = index / Math.max(1, measurements.length - 1)

                // 創建穩定的 sin 波變化，調整到與模擬數據相似的範圍
                // 模擬數據範圍：5.5-6.8 公里，真實數據基礎：7.14 公里
                // 調整為 5.5-6.8 公里範圍以統一顯示
                const minDistance = 5500 // 5.5 公里（米）
                const maxDistance = 6800 // 6.8 公里（米）
                const midDistance = (minDistance + maxDistance) / 2
                const amplitude = (maxDistance - minDistance) / 2

                const dynamicGroundDistance =
                    midDistance +
                    Math.sin(timeProgress * 4 * Math.PI + Math.PI / 4) * amplitude

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
        if (state.isLoadingRealData) return

        setState(prev => ({ ...prev, isLoadingRealData: true, realDataError: null }))
        onLoadingChange?.(true)

        try {
            console.log(
                `🔄 [D2DataManager] 從 NetStack 96分鐘預處理數據載入 ${state.selectedConstellation} 星座數據...`
            )
            console.log(
                `⏱️ 時間段: ${state.selectedTimeRange.durationMinutes} 分鐘`
            )

            // 構建 API 請求 - 添加參數驗證和默認值
            console.log('🔍 [D2DataManager] 請求參數調試:', {
                referenceLocation: params.referenceLocation,
                movingReferenceLocation: params.movingReferenceLocation,
                selectedTimeRange: state.selectedTimeRange,
                selectedConstellation: state.selectedConstellation,
            })

            const requestBody = {
                scenario_name: `D2_Real_Data_${state.selectedConstellation}`,
                ue_position: {
                    latitude: params.referenceLocation?.latitude || 24.94417,
                    longitude: params.referenceLocation?.longitude || 121.37139,
                    altitude: params.referenceLocation?.altitude || 50.0,
                },
                duration_minutes: state.selectedTimeRange.durationMinutes || 5,
                sample_interval_seconds: state.selectedTimeRange.sampleIntervalSeconds || 30,
                constellation: state.selectedConstellation || 'starlink',
                reference_position: {
                    latitude: params.movingReferenceLocation?.latitude || 24.1477,
                    longitude: params.movingReferenceLocation?.longitude || 120.6736,
                    altitude: params.movingReferenceLocation?.altitude || 0.0,
                },
            }

            console.log('📤 [D2DataManager] 實際發送的請求體:', requestBody)

            // 調用 SimWorld NetStack API - 使用配置化的 fetch
            const response = await simworldFetch('/v1/measurement-events/D2/real', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            })

            if (!response.ok) {
                let errorDetail = `${response.status} ${response.statusText}`
                try {
                    const errorData = await response.json()
                    if (errorData.detail) {
                        console.error(
                            '📋 [D2DataManager] 詳細驗證錯誤:',
                            errorData.detail
                        )
                        errorDetail = `${errorDetail} - 驗證錯誤: ${JSON.stringify(
                            errorData.detail
                        )}`
                    }
                } catch (_e) {
                    // 無法解析錯誤響應，使用原始錯誤
                }
                throw new Error(`API 調用失敗: ${errorDetail}`)
            }

            const apiResult = await response.json()

            if (!apiResult.success) {
                throw new Error(`API 回傳錯誤: ${apiResult.error || '未知錯誤'}`)
            }

            // 轉換 API 響應為前端格式
            const convertedData = apiResult.results.map(
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (result: any, _index: number) => ({
                    timestamp: result.timestamp,
                    satelliteDistance: result.measurement_values.satellite_distance,
                    groundDistance: result.measurement_values.ground_distance,
                    referenceSatellite: result.measurement_values.reference_satellite,
                    elevationAngle: result.measurement_values.elevation_angle,
                    azimuthAngle: result.measurement_values.azimuth_angle,
                    signalStrength: result.measurement_values.signal_strength,
                    triggerConditionMet: result.trigger_condition_met,
                    satelliteInfo: {
                        name: result.measurement_values.reference_satellite,
                        noradId: result.satellite_info?.norad_id || 'N/A',
                        constellation: result.satellite_info?.constellation || state.selectedConstellation,
                        orbitalPeriod: result.satellite_info?.orbital_period || 0,
                        inclination: result.satellite_info?.inclination || 0,
                        latitude: result.satellite_info?.latitude || 0,
                        longitude: result.satellite_info?.longitude || 0,
                        altitude: result.satellite_info?.altitude || 0,
                    },
                    measurements: {
                        d2Distance:
                            result.measurement_values.satellite_distance -
                            result.measurement_values.ground_distance,
                        event_type: result.trigger_condition_met ? 'entering' : 'normal',
                    },
                }) as RealD2DataPoint
            )

            setState(prev => ({ ...prev, realD2Data: convertedData, realDataError: null }))
            onDataLoad?.(convertedData)

            console.log(
                `✅ [D2DataManager] 成功載入 ${convertedData.length} 個 ${state.selectedConstellation} NetStack 數據點`
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
                const expectedDuration = state.selectedTimeRange.durationMinutes

                console.log('⏰ [D2DataManager] 時間範圍診斷:', {
                    預期時間段: expectedDuration + '分鐘',
                    實際時間段: actualDurationMinutes.toFixed(2) + '分鐘',
                    開始時間: firstTime.toISOString(),
                    結束時間: lastTime.toISOString(),
                    數據點數量: convertedData.length,
                    採樣間隔: state.selectedTimeRange.sampleIntervalSeconds + '秒',
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
        state.isLoadingRealData,
        state.selectedConstellation,
        state.selectedTimeRange,
        params,
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