/**
 * 統一衛星數據服務
 * 整合所有衛星相關的API調用和數據處理邏輯
 */

import { netstackFetchWithRetry } from '../config/api-config'
import { getNTPUCoordinates } from '../config/observerConfig'

// 導入時間序列接口
export interface PositionTimePoint {
    time: string
    time_offset_seconds: number
    elevation_deg: number
    azimuth_deg: number
    range_km: number
    is_visible: boolean
}

// 統一的衛星數據接口
export interface UnifiedSatelliteInfo {
    id: string
    norad_id: string
    name: string
    elevation_deg: number
    azimuth_deg: number
    distance_km: number
    signal_strength: number
    is_visible: boolean
    constellation: 'starlink' | 'oneweb' | 'mixed'
    last_updated: string
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
    signal_quality: {
        rsrp: number
        rsrq: number
        sinr: number
        estimated_signal_strength: number
    }
    // 🎯 真實SGP4軌道時間序列數據用於精確軌道運動
    position_timeseries?: PositionTimePoint[]
}

export interface SatelliteDataServiceConfig {
    minElevation: number
    maxCount: number
    observerLat: number
    observerLon: number
    constellation: 'starlink' | 'oneweb'
    updateInterval: number
}

export class SatelliteDataService {
    private static instance: SatelliteDataService | null = null
    private config: SatelliteDataServiceConfig
    private cache: Map<string, { data: UnifiedSatelliteInfo[], timestamp: number }> = new Map()
    private readonly CACHE_DURATION = 30000 // 30秒緩存

    private constructor(config: SatelliteDataServiceConfig) {
        this.config = config
    }

    public static getInstance(config?: SatelliteDataServiceConfig): SatelliteDataService {
        if (!SatelliteDataService.instance) {
            // 🎯 使用統一觀測配置服務，消除硬編碼座標
            const coordinates = getNTPUCoordinates()
            const defaultConfig: SatelliteDataServiceConfig = {
                minElevation: 10,
                maxCount: 12, // 默認值，會根據星座動態調整
                observerLat: coordinates.lat, // 統一配置服務
                observerLon: coordinates.lon, // 統一配置服務
                constellation: 'starlink',
                updateInterval: 5000 // 5秒更新
            }
            SatelliteDataService.instance = new SatelliteDataService(config || defaultConfig)
        }
        return SatelliteDataService.instance
    }

    /**
     * 根據星座獲取配置參數
     */
    private getConstellationConfig(constellation: 'starlink' | 'oneweb'): { maxCount: number, minElevation: number } {
        switch (constellation) {
            case 'starlink':
                return {
                    maxCount: 15,        // 顯示10-15顆可見衛星
                    minElevation: 5      // Starlink 5° 仰角門檻（低軌道，信號較強）
                }
            case 'oneweb':
                return {
                    maxCount: 6,         // 顯示3-6顆可見衛星  
                    minElevation: 10     // OneWeb 10° 仰角門檻（稍高軌道）
                }
            default:
                return {
                    maxCount: 12,
                    minElevation: 10
                }
        }
    }

    /**
     * 更新服務配置
     */
    public updateConfig(newConfig: Partial<SatelliteDataServiceConfig>): void {
        this.config = { ...this.config, ...newConfig }
        // 清除緩存以強制更新數據
        this.cache.clear()
    }

    /**
     * 獲取可見衛星數據 - 統一API調用
     */
    public async getVisibleSatellites(forceRefresh: boolean = false): Promise<UnifiedSatelliteInfo[]> {
        // 🎯 根據星座動態調整參數（仰角門檻和衛星數量）
        const constellationConfig = this.getConstellationConfig(this.config.constellation)
        const actualMinElevation = constellationConfig.minElevation
        const actualMaxCount = constellationConfig.maxCount
        
        const cacheKey = `${this.config.constellation}_${actualMinElevation}_${actualMaxCount}`
        
        // 檢查緩存
        if (!forceRefresh) {
            const cached = this.cache.get(cacheKey)
            if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
                return cached.data
            }
        }

        try {
            // 🎯 使用預計算數據的可見性時間窗口 (基於Stage 6真實分析結果)
            // 衛星僅在特定時間窗口可見：09:42-09:47 (5分鐘) 和 11:13-11:17 (4分鐘)
            const visibilityWindows = [
                {
                    start: new Date('2025-08-18T09:42:02Z'),
                    end: new Date('2025-08-18T09:47:02Z'),
                    duration: 5 * 60 // 5分鐘，以秒為單位
                },
                {
                    start: new Date('2025-08-18T11:13:02Z'), 
                    end: new Date('2025-08-18T11:17:32Z'),
                    duration: 4 * 60 + 30 // 4分30秒，以秒為單位
                }
            ]
            
            const totalVisibilityDuration = visibilityWindows.reduce((sum, window) => sum + window.duration, 0)
            
            // 🚀 關鍵修復：只在可見時間窗口內循環，確保每次查詢都能找到衛星
            const currentCycle = Math.floor(Date.now() / 1000) % totalVisibilityDuration
            let targetTime: Date
            
            if (currentCycle < visibilityWindows[0].duration) {
                // 在第一個可見窗口內 (09:42-09:47)
                const offsetInWindow = currentCycle
                targetTime = new Date(visibilityWindows[0].start.getTime() + offsetInWindow * 1000)
            } else {
                // 在第二個可見窗口內 (11:13-11:17)
                const offsetInWindow = currentCycle - visibilityWindows[0].duration
                targetTime = new Date(visibilityWindows[1].start.getTime() + offsetInWindow * 1000)
            }
            
            let endpoint = `/api/v1/satellite-simple/visible_satellites?count=${actualMaxCount}&min_elevation_deg=${actualMinElevation}&observer_lat=${this.config.observerLat}&observer_lon=${this.config.observerLon}&constellation=${this.config.constellation}&utc_timestamp=${targetTime.toISOString()}&global_view=false`
            
            let response = await netstackFetchWithRetry(endpoint)
            
            // 如果主要端點失敗，嘗試使用備用端點
            if (!response.ok) {
                console.warn(`⚠️ 主要API端點失敗 (${response.status})，嘗試備用端點...`)
                endpoint = `/api/v1/leo-frontend/satellites`
                response = await netstackFetchWithRetry(endpoint)
                
                if (!response.ok) {
                    throw new Error(`NetStack API 錯誤: ${response.status} ${response.statusText}`)
                }
            }

            const data = await response.json()
            const satellites = data.satellites || []

            // 轉換為統一格式，保留position_timeseries數據
            const unifiedSatellites: UnifiedSatelliteInfo[] = satellites.map((sat: Record<string, unknown>, index: number) => {
                const satelliteId = String(sat.norad_id || sat.id || index)
                
                // 🚀 關鍵修復：保留position_timeseries數據
                const positionTimeseries = Array.isArray(sat.position_timeseries) 
                    ? sat.position_timeseries.map((point: any) => ({
                        time: String(point.time || ''),
                        time_offset_seconds: Number(point.time_offset_seconds || 0),
                        elevation_deg: Number(point.elevation_deg || 0),
                        azimuth_deg: Number(point.azimuth_deg || 0),
                        range_km: Number(point.range_km || 0),
                        is_visible: Boolean(point.is_visible)
                    })) 
                    : undefined;
                
                return {
                    id: satelliteId,
                    norad_id: String(sat.norad_id || ''),
                    name: String(sat.name || 'Unknown'),
                    elevation_deg: Number(sat.elevation_deg || 0),
                    azimuth_deg: Number(sat.azimuth_deg || 0),
                    distance_km: Number(sat.distance_km || 0),
                    signal_strength: Number(sat.signal_strength || 0),
                    is_visible: Boolean(sat.is_visible),
                    constellation: this.config.constellation,
                    last_updated: new Date().toISOString(),
                    position: {
                        latitude: this.config.observerLat,
                        longitude: this.config.observerLon,
                        altitude: Number(sat.orbit_altitude_km || 550),
                        elevation: Number(sat.elevation_deg || 0),
                        azimuth: Number(sat.azimuth_deg || 0),
                        range: Number(sat.distance_km || 0),
                        velocity: Number(sat.velocity || 7.5),
                        doppler_shift: Number(sat.doppler_shift || 0)
                    },
                    signal_quality: {
                        rsrp: Number(sat.rsrp || -100),
                        rsrq: Number(sat.rsrq || -10),
                        sinr: Number(sat.sinr || 10),
                        estimated_signal_strength: Number(sat.signal_strength || Math.max(0.3, 1.0 - (Number(sat.distance_km || 1000) / 2000)))
                    },
                    // 🌟 保留真實SGP4軌道數據
                    position_timeseries: positionTimeseries
                }
            })

            // 更新緩存
            this.cache.set(cacheKey, {
                data: unifiedSatellites,
                timestamp: Date.now()
            })

            return unifiedSatellites

        } catch (error) {
            console.error('❌ SatelliteDataService: API調用失敗:', error)
            throw error
        }
    }

    /**
     * 獲取系統健康狀態
     */
    public async getSystemHealth(): Promise<{ status: string, details: Record<string, unknown> }> {
        try {
            const endpoint = '/api/v1/leo-frontend/health'
            const response = await netstackFetchWithRetry(endpoint)
            
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`)
            }
            
            return await response.json()
        } catch (error) {
            console.error('❌ SatelliteDataService: 健康檢查失敗:', error)
            throw error
        }
    }

    /**
     * 獲取可用星座列表
     */
    public async getAvailableConstellations(): Promise<string[]> {
        try {
            const endpoint = '/api/v1/satellites/constellations/info'
            const response = await netstackFetchWithRetry(endpoint)
            
            if (!response.ok) {
                throw new Error(`Failed to get constellations: ${response.status}`)
            }
            
            const data = await response.json()
            return data.available_constellations || ['starlink', 'oneweb']
        } catch (_error) {
            console.warn('⚠️ SatelliteDataService: 獲取星座列表失敗，使用默認值')
            return ['starlink', 'oneweb']
        }
    }

    /**
     * 清除緩存
     */
    public clearCache(): void {
        this.cache.clear()
        console.log('🗑️ SatelliteDataService: 緩存已清除')
    }

    /**
     * 獲取當前配置
     */
    public getConfig(): SatelliteDataServiceConfig {
        return { ...this.config }
    }
}

// 導出單例實例獲取函數
export const getSatelliteDataService = (config?: SatelliteDataServiceConfig) => {
    return SatelliteDataService.getInstance(config)
}