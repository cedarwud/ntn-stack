/**
 * SimWorld API Service
 * Provides unified interface for satellite data and position tracking
 */

import { useState, useEffect } from 'react'
import { netstackFetch } from '../config/api-config'

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
export function useVisibleSatellites(
    minElevation: number = 5,
    maxCount: number = 10,
    observerLat: number = 24.9441667,
    observerLon: number = 121.3713889,
    constellation: 'starlink' | 'oneweb' = 'starlink'
) {
    const [satellites, setSatellites] = useState<SatellitePosition[]>([])
    const [loading, setLoading] = useState<boolean>(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let isMounted = true
        // 不再需要 timeoutId，因為沒有定期更新

        const fetchVisibleSatellites = async () => {
            if (!isMounted) return

            setLoading(true)
            setError(null)

            try {
                // 減少日誌輸出頻率 - 只在初次載入或錯誤恢復時顯示
                const isInitialLoad = satellites.length === 0
                if (isInitialLoad || error) {
                    console.log(`🛰️ SimWorld API: 載入可見衛星 (${constellation}, 仰角≥${minElevation}°)`)
                }

                // Use NetStack's real-time visible satellites endpoint
                const endpoint = `/api/v1/satellite-ops/visible_satellites?` + 
                    `count=${maxCount}&` +
                    `min_elevation_deg=${minElevation}&` +
                    `observer_lat=${observerLat}&` +
                    `observer_lon=${observerLon}&` +
                    `utc_timestamp=${new Date().toISOString()}&` +
                    `global_view=false&` +
                    `constellation=${constellation}`

                const response = await netstackFetch(endpoint)
                
                if (!response.ok) {
                    throw new Error(`NetStack API 錯誤: ${response.status} ${response.statusText}`)
                }

                const data = await response.json()
                
                if (!isMounted) return

                // Convert NetStack format to SimWorld format
                const convertedSatellites: SatellitePosition[] = (data.satellites || []).map((sat: any, index: number) => ({
                    id: index + 1,
                    name: sat.name || `${constellation.toUpperCase()}-${sat.norad_id}`,
                    norad_id: sat.norad_id?.toString() || '0',
                    position: {
                        latitude: sat.latitude || 0,
                        longitude: sat.longitude || 0,
                        altitude: sat.altitude_km || sat.altitude || 550, // Default LEO altitude
                        elevation: sat.elevation_deg || sat.elevation || 0,
                        azimuth: sat.azimuth_deg || sat.azimuth || 0,
                        range: sat.distance_km || sat.range_km || sat.range || 1000,
                        velocity: 7.5, // Typical LEO satellite velocity km/s
                        doppler_shift: 0 // Simplified for now
                    },
                    signal_strength: Math.max(0.1, 1.0 - ((sat.distance_km || sat.range_km || 1000) / 2000)),
                    is_visible: sat.is_visible !== false,
                    last_updated: new Date().toISOString(),
                    // Compatibility fields
                    elevation_deg: sat.elevation_deg || sat.elevation || 0,
                    azimuth_deg: sat.azimuth_deg || sat.azimuth || 0,
                    distance_km: sat.distance_km || sat.range_km || sat.range || 1000,
                    range_km: sat.distance_km || sat.range_km || sat.range || 1000,
                    elevation: sat.elevation_deg || sat.elevation || 0,
                    azimuth: sat.azimuth_deg || sat.azimuth || 0,
                    visible: sat.is_visible !== false
                }))

                setSatellites(convertedSatellites)
                
                // 只在初次載入或錯誤恢復時顯示成功日誌
                const isFirstLoad = satellites.length === 0
                if (isFirstLoad || error) {
                    console.log(`✅ SimWorld API: 成功載入 ${convertedSatellites.length} 顆可見衛星`)
                }

            } catch (err) {
                if (!isMounted) return
                
                const errorMessage = err instanceof Error ? err.message : '載入衛星數據失敗'
                setError(errorMessage)
                setSatellites([])
                
                console.error('❌ SimWorld API: 可見衛星載入失敗:', errorMessage)
            } finally {
                if (isMounted) {
                    setLoading(false)
                }
            }
        }

        // Initial fetch - 只載入一次，之後依靠軌道計算
        fetchVisibleSatellites()

        // 不再設置定期更新 - 衛星軌道由 3D 引擎基於 TLE 數據計算
        // 這避免了不必要的 API 調用和日誌輸出

        return () => {
            isMounted = false
            // 清理已不需要，因為沒有定時器
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
export async function getSatelliteHealth(): Promise<any> {
    const endpoint = '/api/v1/satellite-ops/health'
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
    } catch (error) {
        console.warn('⚠️ Failed to get constellations from API, using defaults')
        return ['starlink', 'oneweb']
    }
}

/**
 * Legacy API object for backward compatibility
 */
export const simWorldApi = {
    async getVisibleSatellites(
        minElevation: number = 5,
        maxCount: number = 10,
        observerLat: number = 24.9441667,
        observerLon: number = 121.3713889,
        constellation: string = 'starlink'
    ): Promise<SatellitePosition[]> {
        try {
            const endpoint = `/api/v1/satellite-ops/visible_satellites?` + 
                `count=${maxCount}&` +
                `min_elevation_deg=${minElevation}&` +
                `observer_lat=${observerLat}&` +
                `observer_lon=${observerLon}&` +
                `utc_timestamp=${new Date().toISOString()}&` +
                `global_view=false&` +
                `constellation=${constellation}`

            const response = await netstackFetch(endpoint)
            
            if (!response.ok) {
                throw new Error(`NetStack API 錯誤: ${response.status} ${response.statusText}`)
            }

            const data = await response.json()
            
            // Convert NetStack format to SimWorld format
            const convertedSatellites: SatellitePosition[] = (data.satellites || []).map((sat: any, index: number) => ({
                id: index + 1,
                name: sat.name || `${constellation.toUpperCase()}-${sat.norad_id}`,
                norad_id: sat.norad_id?.toString() || '0',
                position: {
                    latitude: sat.latitude || 0,
                    longitude: sat.longitude || 0,
                    altitude: sat.altitude_km || sat.altitude || 550,
                    elevation: sat.elevation_deg || sat.elevation || 0,
                    azimuth: sat.azimuth_deg || sat.azimuth || 0,
                    range: sat.distance_km || sat.range_km || sat.range || 1000,
                    velocity: 7.5,
                    doppler_shift: 0
                },
                signal_strength: Math.max(0.1, 1.0 - ((sat.distance_km || sat.range_km || 1000) / 2000)),
                is_visible: sat.is_visible !== false,
                last_updated: new Date().toISOString(),
                // Compatibility fields
                elevation_deg: sat.elevation_deg || sat.elevation || 0,
                azimuth_deg: sat.azimuth_deg || sat.azimuth || 0,
                distance_km: sat.distance_km || sat.range_km || sat.range || 1000,
                range_km: sat.distance_km || sat.range_km || sat.range || 1000,
                elevation: sat.elevation_deg || sat.elevation || 0,
                azimuth: sat.azimuth_deg || sat.azimuth || 0,
                visible: sat.is_visible !== false
            }))

            return convertedSatellites
        } catch (error) {
            console.error('❌ SimWorld API: getVisibleSatellites failed:', error)
            return []
        }
    }
}