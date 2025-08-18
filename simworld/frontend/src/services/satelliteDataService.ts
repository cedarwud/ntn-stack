/**
 * 統一衛星數據服務
 * 整合所有衛星相關的API調用和數據處理邏輯
 */

import { netstackFetch } from '../config/api-config'

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
            const defaultConfig: SatelliteDataServiceConfig = {
                minElevation: 10,
                maxCount: 40,
                observerLat: 24.9441667, // NTPU
                observerLon: 121.3713889,
                constellation: 'starlink',
                updateInterval: 5000 // 5秒更新
            }
            SatelliteDataService.instance = new SatelliteDataService(config || defaultConfig)
        }
        return SatelliteDataService.instance
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
        const cacheKey = `${this.config.constellation}_${this.config.minElevation}_${this.config.maxCount}`
        
        // 檢查緩存
        if (!forceRefresh) {
            const cached = this.cache.get(cacheKey)
            if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
                console.log(`⚡ SatelliteDataService: 使用緩存數據 (${cached.data.length} 顆衛星)`)
                return cached.data
            }
        }

        try {
            const currentTime = new Date().toISOString()
            const endpoint = `/api/v1/leo-frontend/visible_satellites?count=${this.config.maxCount}&min_elevation_deg=${this.config.minElevation}&observer_lat=${this.config.observerLat}&observer_lon=${this.config.observerLon}&constellation=${this.config.constellation}&utc_timestamp=${currentTime}&global_view=false`
            
            const response = await netstackFetch(endpoint)
            
            if (!response.ok) {
                throw new Error(`NetStack API 錯誤: ${response.status} ${response.statusText}`)
            }

            const data = await response.json()
            const satellites = data.satellites || []

            // 轉換為統一格式
            const unifiedSatellites: UnifiedSatelliteInfo[] = satellites.map((sat: Record<string, unknown>, index: number) => {
                const satelliteId = String(sat.norad_id || sat.id || index)
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
                    }
                }
            })

            // 更新緩存
            this.cache.set(cacheKey, {
                data: unifiedSatellites,
                timestamp: Date.now()
            })

            console.log(`✅ SatelliteDataService: 成功獲取 ${unifiedSatellites.length} 顆 ${this.config.constellation} 衛星`)
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
            const response = await netstackFetch(endpoint)
            
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
            const response = await netstackFetch(endpoint)
            
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