/**
 * SimWorld API Service
 * Provides unified interface for satellite data and position tracking
 */

import { useState, useEffect } from 'react'
import { netstackFetch } from '../config/api-config'

/**
 * 計算衛星相對於觀測者的仰角和方位角
 * 基於球面三角學公式
 */
function _calculateElevationAzimuth(
    satLat: number, satLon: number, satAlt: number,
    obsLat: number, obsLon: number, obsAlt: number = 0.024  // NTPU高度24米
): { elevation: number, azimuth: number, range: number } {
    // 地球參數
    const earthRadius = 6371.0  // km
    
    // 轉換為弧度
    const satLatRad = (satLat * Math.PI) / 180
    const satLonRad = (satLon * Math.PI) / 180
    const obsLatRad = (obsLat * Math.PI) / 180
    const obsLonRad = (obsLon * Math.PI) / 180
    
    // 將地理坐標轉換為ECEF坐標系 (Earth-Centered, Earth-Fixed)
    const toECEF = (latRad: number, lonRad: number, alt: number) => {
        const x = (earthRadius + alt) * Math.cos(latRad) * Math.cos(lonRad)
        const y = (earthRadius + alt) * Math.cos(latRad) * Math.sin(lonRad)
        const z = (earthRadius + alt) * Math.sin(latRad)
        return { x, y, z }
    }
    
    // 衛星和觀測者的ECEF坐標
    const satECEF = toECEF(satLatRad, satLonRad, satAlt)
    const obsECEF = toECEF(obsLatRad, obsLonRad, obsAlt)
    
    // 計算衛星相對於觀測者的向量
    const dx = satECEF.x - obsECEF.x
    const dy = satECEF.y - obsECEF.y
    const dz = satECEF.z - obsECEF.z
    
    // 3D直線距離
    const range = Math.sqrt(dx * dx + dy * dy + dz * dz)
    
    // 計算本地坐標系 (ENU: East-North-Up)
    const sinLat = Math.sin(obsLatRad)
    const cosLat = Math.cos(obsLatRad)
    const sinLon = Math.sin(obsLonRad)
    const cosLon = Math.cos(obsLonRad)
    
    // 轉換到ENU坐標系
    const east = -sinLon * dx + cosLon * dy
    const north = -sinLat * cosLon * dx - sinLat * sinLon * dy + cosLat * dz
    const up = cosLat * cosLon * dx + cosLat * sinLon * dy + sinLat * dz
    
    // 計算仰角 (elevation)
    const horizDistance = Math.sqrt(east * east + north * north)
    const elevation = Math.atan2(up, horizDistance) * (180 / Math.PI)
    
    // 計算方位角 (azimuth) - 從北方順時針測量
    let azimuth = Math.atan2(east, north) * (180 / Math.PI)
    if (azimuth < 0) azimuth += 360
    
    return {
        elevation: elevation,  // 可以為負值（地平線以下）
        azimuth: azimuth,
        range: range
    }
}

// 時間序列位置點接口
export interface PositionTimePoint {
    time: string
    time_offset_seconds: number
    elevation_deg: number
    azimuth_deg: number
    range_km: number
    is_visible: boolean
}

// Standard satellite position interface used across the application
export interface SatellitePosition {
    id: number
    name: string
    norad_id: string
    position: {
        latitude: number
        longitude: number
        altitude: number
        elevation: number
        azimuth: number
        range: number
        velocity: number
        doppler_shift: number
    }
    signal_strength: number
    is_visible: boolean
    last_updated: string
    // 真實SGP4軌道時間序列數據
    position_timeseries?: PositionTimePoint[]
    // Additional optional fields for compatibility
    elevation_deg?: number
    azimuth_deg?: number
    distance_km?: number
    range_km?: number
    elevation?: number
    azimuth?: number
    visible?: boolean
}

/**
 * Hook to get visible satellites using NetStack real-time API
 * This replaces the old simworld satellite calculation with NetStack's optimized backend
 */
// 添加緩存減少重複API調用
const satelliteCache = new Map<string, { data: SatellitePosition[], timestamp: number }>()
const CACHE_DURATION = 30000 // 30秒緩存

export function useVisibleSatellites(
    minElevation: number = 5,   // 會根據星座動態調整 (Starlink 5°, OneWeb 10°)
    maxCount: number = 15,      // 實時可見衛星數 (10-15顆)
    observerLat: number = 24.9441667,
    observerLon: number = 121.3713889,
    constellation: 'starlink' | 'oneweb' = 'starlink'
) {
    const [satellites, setSatellites] = useState<SatellitePosition[]>([])
    const [loading, setLoading] = useState<boolean>(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let isMounted = true

        const fetchVisibleSatellites = async () => {
            if (!isMounted) return

            // 檢查緩存，減少API延遲
            const cacheKey = `${constellation}_${minElevation}_${maxCount}`
            const cached = satelliteCache.get(cacheKey)
            if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
                setSatellites(cached.data)
                setLoading(false)
                // 調試已移除：使用緩存數據
                return
            }

            setLoading(true)
            setError(null)

            try {
                // 🎯 根據星座設置特定參數
                const constellationConfig = constellation === 'starlink' 
                    ? { maxCount: 15, minElevation: 5 }   // Starlink: 5° 仰角，10-15顆可見
                    : { maxCount: 6, minElevation: 10 }   // OneWeb: 10° 仰角，3-6顆可見
                
                // 🎯 使用預計算數據的時間範圍 (2025-08-18 09:42:02 to 11:17:32)
                const dataStartTime = new Date('2025-08-18T09:42:02Z')
                const dataEndTime = new Date('2025-08-18T11:17:32Z')
                const dataDuration = dataEndTime.getTime() - dataStartTime.getTime()
                
                // 基於當前秒數在數據範圍內循環，實現動態衛星位置
                const currentSeconds = Math.floor(Date.now() / 1000) % Math.floor(dataDuration / 1000)
                const targetTime = new Date(dataStartTime.getTime() + currentSeconds * 1000)
                
                const endpoint = `/api/v1/satellite-simple/visible_satellites?count=${constellationConfig.maxCount}&min_elevation_deg=${constellationConfig.minElevation}&observer_lat=${observerLat}&observer_lon=${observerLon}&constellation=${constellation}&utc_timestamp=${targetTime.toISOString()}&global_view=false`
                
                const response = await netstackFetch(endpoint)
                
                if (!response.ok) {
                    throw new Error(`NetStack satellite-simple API 錯誤: ${response.status} ${response.statusText}`)
                }

                const data = await response.json()
                
                if (!isMounted) return

                // 轉換 leo-frontend API 數據到前端格式，保留SGP4時間序列數據
                const convertedSatellites: SatellitePosition[] = data.satellites.map((sat: Record<string, unknown>, index: number) => ({
                    id: index + 1,
                    name: sat.name,
                    norad_id: sat.norad_id,
                    position: {
                        latitude: observerLat, // 觀測者位置
                        longitude: observerLon, // 觀測者位置  
                        altitude: sat.orbit_altitude_km || 550,
                        elevation: sat.elevation_deg,
                        azimuth: sat.azimuth_deg,
                        range: sat.distance_km,
                        velocity: 7.5,
                        doppler_shift: 0
                    },
                    signal_strength: sat.signal_strength || Math.max(0.3, 1.0 - (sat.distance_km / 2000)),
                    is_visible: sat.is_visible,
                    last_updated: new Date().toISOString(),
                    // 🎯 保留真實SGP4時間序列數據用於前端軌道運動
                    position_timeseries: sat.position_timeseries as PositionTimePoint[] || undefined,
                    // Compatibility fields
                    elevation_deg: sat.elevation_deg,
                    azimuth_deg: sat.azimuth_deg,
                    distance_km: sat.distance_km,
                    range_km: sat.distance_km,
                    elevation: sat.elevation_deg,
                    azimuth: sat.azimuth_deg,
                    visible: sat.is_visible
                }))

                setSatellites(convertedSatellites)
                
                // 更新緩存
                satelliteCache.set(cacheKey, {
                    data: convertedSatellites,
                    timestamp: Date.now()
                })
                
                // console.log(`✅ NetStack leo-frontend API: 載入 ${convertedSatellites.length} 顆衛星 (observer-relative calculations)`)

            } catch (err) {
                if (!isMounted) return
                
                const errorMessage = err instanceof Error ? err.message : '載入NetStack衛星數據失敗'
                setError(errorMessage)
                setSatellites([])
                
                console.error('❌ NetStack leo-frontend API 失敗:', errorMessage)
            } finally {
                if (isMounted) {
                    setLoading(false)
                }
            }
        }

        // Initial fetch - 只載入一次，之後依靠軌道計算
        fetchVisibleSatellites()

        return () => {
            isMounted = false
        }
    }, [minElevation, maxCount, observerLat, observerLon, constellation])

    return {
        satellites,
        loading,
        error
    }
}

/**
 * Get satellite health status
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function getSatelliteHealth(): Promise<any> {
    const endpoint = '/api/v1/leo-frontend/health'
    const response = await netstackFetch(endpoint)
    
    if (!response.ok) {
        throw new Error(`Health check failed: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
}

/**
 * Get available constellations
 */
export async function getAvailableConstellations(): Promise<string[]> {
    try {
        const endpoint = '/api/v1/satellites/constellations/info'
        const response = await netstackFetch(endpoint)
        
        if (!response.ok) {
            throw new Error(`Failed to get constellations: ${response.status}`)
        }
        
        const data = await response.json()
        return data.available_constellations || ['starlink', 'oneweb']
    } catch (_error) {
        console.warn('⚠️ Failed to get constellations from API, using defaults')
        return ['starlink', 'oneweb']
    }
}

/**
 * Legacy API object for backward compatibility
 */
export const simWorldApi = {
    async getVisibleSatellites(
        minElevation: number = 10,  // 使用標準服務門檻 (10°)
        maxCount: number = 50,  // 允許顯示更多衛星，會根據星座動態調整
        observerLat: number = 24.9441667,
        observerLon: number = 121.3713889,
        constellation: string = 'starlink'
    ): Promise<SatellitePosition[]> {
        try {
            // 🎯 根據星座設置特定參數
            const constellationConfig = constellation === 'starlink' 
                ? { maxCount: 15, minElevation: 5 }   // Starlink: 5° 仰角，10-15顆可見
                : { maxCount: 6, minElevation: 10 }   // OneWeb: 10° 仰角，3-6顆可見
            
            // 🎯 使用預計算數據的時間範圍 (2025-08-18 09:42:02 to 11:17:32)
            const dataStartTime = new Date('2025-08-18T09:42:02Z')
            const dataEndTime = new Date('2025-08-18T11:17:32Z')
            const dataDuration = dataEndTime.getTime() - dataStartTime.getTime()
            
            // 基於當前秒數在數據範圍內循環，實現動態衛星位置
            const currentSeconds = Math.floor(Date.now() / 1000) % Math.floor(dataDuration / 1000)
            const targetTime = new Date(dataStartTime.getTime() + currentSeconds * 1000)
            
            const endpoint = `/api/v1/satellite-simple/visible_satellites?count=${constellationConfig.maxCount}&min_elevation_deg=${constellationConfig.minElevation}&observer_lat=${observerLat}&observer_lon=${observerLon}&constellation=${constellation}&utc_timestamp=${targetTime.toISOString()}&global_view=false`
            const response = await netstackFetch(endpoint)
            
            if (!response.ok) {
                throw new Error(`NetStack satellite-simple API 錯誤: ${response.status} ${response.statusText}`)
            }

            const data = await response.json()
            const satellites = data.satellites || []
            
            // 轉換為前端格式，保留SGP4時間序列數據
            const convertedSatellites: SatellitePosition[] = satellites.map((sat: Record<string, unknown>, index: number) => ({
                id: index + 1,
                name: sat.name,
                norad_id: sat.norad_id,
                position: {
                    latitude: observerLat,
                    longitude: observerLon,
                    altitude: sat.orbit_altitude_km || 550,
                    elevation: sat.elevation_deg,
                    azimuth: sat.azimuth_deg,
                    range: sat.distance_km,
                    velocity: 7.5,
                    doppler_shift: 0
                },
                signal_strength: sat.signal_strength || 0.8,
                is_visible: sat.is_visible,
                last_updated: new Date().toISOString(),
                // 🎯 保留真實SGP4時間序列數據用於前端軌道運動
                position_timeseries: sat.position_timeseries as PositionTimePoint[] || undefined,
                // Compatibility fields
                elevation_deg: sat.elevation_deg,
                azimuth_deg: sat.azimuth_deg,
                distance_km: sat.distance_km,
                range_km: sat.distance_km,
                elevation: sat.elevation_deg,
                azimuth: sat.azimuth_deg,
                visible: sat.is_visible
            }))

            // console.log(`✅ NetStack leo-frontend API: 載入 ${convertedSatellites.length} 顆衛星`)
            return convertedSatellites
        } catch (error) {
            console.error('❌ NetStack leo-frontend API failed:', error)
            return []
        }
    }
}