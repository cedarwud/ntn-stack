/**
 * NetStack 預計算 API 服務
 * Phase 1: 統一使用 NetStack 預計算數據，取代 SimWorld 的舊衛星計算
 */

import { useState, useEffect } from 'react'
import { netstackFetch } from '../config/api-config'
import type { SatellitePosition } from './simworld-api'

// NetStack 預計算數據接口
export interface PrecomputedSatellite {
    norad_id: number
    name: string
    latitude: number
    longitude: number
    altitude: number
    elevation: number
    azimuth: number
    range_km: number
    is_visible: boolean
}

export interface PrecomputedOrbitData {
    location: {
        id: string
        name: string
        latitude: number
        longitude: number
        altitude: number
        environment: string
    }
    computation_metadata: {
        constellation: string
        elevation_threshold: number
        use_layered: boolean
        environment_factor: string
        computation_date: string
        total_satellites_input: number
        filtered_satellites_count: number
        filtering_efficiency: string
    }
    filtered_satellites: PrecomputedSatellite[]
    total_processing_time_ms: number
}

/**
 * NetStack 預計算衛星數據 Hook
 * 取代舊的 useVisibleSatellites，統一使用 Phase 0 預計算數據
 * 支援星座切換功能
 */
export function useNetstackPrecomputedSatellites(
    location: string = 'ntpu',
    constellation: 'starlink' | 'oneweb' = 'starlink'
) {
    const [satellites, setSatellites] = useState<SatellitePosition[]>([])
    const [loading, setLoading] = useState<boolean>(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let isMounted = true

        const fetchPrecomputedSatellites = async () => {
            if (!location) return

            setLoading(true)
            setError(null)

            try {
                console.log(`🛰️ NetStack: 載入 ${location} ${constellation} 預計算衛星數據`)

                // 調用 NetStack 預計算端點，支援星座切換 (修正路徑)
                const endpoint = `/api/v1/satellites/precomputed/${location}?constellation=${constellation}&elevation_threshold=10&use_layered=true`
                
                const response = await netstackFetch(endpoint)
                
                if (!response.ok) {
                    throw new Error(`NetStack API 錯誤: ${response.status} ${response.statusText}`)
                }

                const data: PrecomputedOrbitData = await response.json()
                
                if (!isMounted) return

                // 轉換 NetStack 格式到 SimWorld 格式
                const convertedSatellites: SatellitePosition[] = data.filtered_satellites.map((sat, index) => ({
                    id: index + 1,
                    name: sat.name,
                    norad_id: sat.norad_id.toString(),
                    position: {
                        latitude: sat.latitude,
                        longitude: sat.longitude,
                        altitude: sat.altitude,
                        elevation: sat.elevation,
                        azimuth: sat.azimuth,
                        range: sat.range_km,
                        velocity: 7.5, // 典型 LEO 衛星速度 km/s
                        doppler_shift: 0 // 簡化處理
                    },
                    signal_strength: Math.max(0.1, 1.0 - (sat.range_km / 2000)), // 基於距離的信號強度
                    is_visible: sat.is_visible,
                    last_updated: new Date().toISOString()
                }))

                setSatellites(convertedSatellites)
                
                console.log(`✅ NetStack: 成功載入 ${convertedSatellites.length} 顆預計算衛星`)
                console.log(`📊 NetStack: 篩選效率 ${data.computation_metadata.filtering_efficiency}`)
                console.log(`⚡ NetStack: 處理時間 ${data.total_processing_time_ms}ms`)

            } catch (err) {
                if (!isMounted) return
                
                const errorMessage = err instanceof Error ? err.message : '未知錯誤'
                setError(errorMessage)
                setSatellites([])
                
                console.error('❌ NetStack: 預計算衛星數據載入失敗:', errorMessage)
            } finally {
                if (isMounted) {
                    setLoading(false)
                }
            }
        }

        fetchPrecomputedSatellites()

        return () => {
            isMounted = false
        }
    }, [location, constellation])

    return {
        satellites,
        loading,
        error
    }
}

/**
 * NetStack 最佳時間窗口 API
 */
export async function getOptimalTimeWindow(
    location: string = 'ntpu',
    constellation: string = 'starlink',
    windowHours: number = 6
): Promise<any> {
    const endpoint = `/optimal-window/${location}?constellation=${constellation}&window_hours=${windowHours}`
    
    const response = await netstackFetch(endpoint)
    
    if (!response.ok) {
        throw new Error(`NetStack API 錯誤: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
}

/**
 * NetStack 展示優化數據 API
 */
export async function getDisplayOptimizedData(
    location: string = 'ntpu',
    acceleration: number = 60,
    distanceScale: number = 0.1
): Promise<any> {
    const endpoint = `/display-data/${location}?acceleration=${acceleration}&distance_scale=${distanceScale}`
    
    const response = await netstackFetch(endpoint)
    
    if (!response.ok) {
        throw new Error(`NetStack API 錯誤: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
}

/**
 * NetStack 健康檢查
 */
export async function checkNetstackHealth(): Promise<any> {
    const endpoint = '/health/precomputed'
    
    const response = await netstackFetch(endpoint)
    
    if (!response.ok) {
        throw new Error(`NetStack 健康檢查失敗: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
}
