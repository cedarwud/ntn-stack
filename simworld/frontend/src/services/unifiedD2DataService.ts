/**
 * 統一 D2 數據服務 - 新架構版本
 * 使用預載緩存的衛星軌道數據，支援多星座選擇
 * 與 RL 系統共享數據，避免重複存儲
 */

import { netstackFetch } from '../config/api-config'

// === 基本類型定義 ===

export interface UEPosition {
    latitude: number
    longitude: number
    altitude: number
}

export interface FixedRefPosition {
    latitude: number
    longitude: number
    altitude: number
}

export interface SatellitePosition {
    latitude: number
    longitude: number
    altitude: number
}

export interface D2Parameters {
    thresh1: number
    thresh2: number
    hysteresis: number
}

export interface ConstellationInfo {
    name: string
    satellite_count: number
    active_satellites: number
    last_updated?: string
}

export interface SatelliteInfo {
    satellite_id: string
    norad_id: number
    satellite_name: string
    constellation: string
    is_active: boolean
    orbital_period: number
    last_updated: string
}

// === D2 測量數據類型 ===

export interface D2MeasurementPoint {
    timestamp: string
    satellite_id: string
    constellation: string
    satellite_distance: number  // 米
    ground_distance: number     // 米
    satellite_position: SatellitePosition
    trigger_condition_met: boolean
    event_type: 'entering' | 'leaving' | 'none'
}

export interface D2ScenarioConfig {
    scenario_name: string
    constellation: string
    ue_position: UEPosition
    fixed_ref_position: FixedRefPosition
    thresh1: number
    thresh2: number
    hysteresis: number
    duration_minutes: number
    sample_interval_seconds: number
}

export interface D2PrecomputeRequest {
    scenario_name: string
    constellation: string
    ue_position: UEPosition
    fixed_ref_position: FixedRefPosition
    thresh1: number
    thresh2: number
    hysteresis: number
    duration_minutes: number
    sample_interval_seconds: number
}

export interface D2PrecomputeResponse {
    scenario_name: string
    scenario_hash: string
    measurements_generated: number
    satellites_processed: number
    duration_seconds: number
    errors: string[]
}

export interface TLEUpdateRequest {
    constellation: string
    force_update: boolean
}

export interface TLEUpdateResponse {
    constellation: string
    satellites_updated: number
    satellites_added: number
    satellites_failed: number
    duration_seconds: number
    errors: string[]
}

// === 統一 D2 數據服務類 ===

class UnifiedD2DataService {
    private baseUrl = '/api/satellite-data'
    private cache = new Map<string, D2MeasurementPoint[]>()
    private cacheExpiry = new Map<string, number>()
    private readonly CACHE_TTL = 5 * 60 * 1000 // 5分鐘緩存

    /**
     * 獲取可用的衛星星座列表
     */
    async getAvailableConstellations(): Promise<ConstellationInfo[]> {
        try {
            console.log('🔍 [UnifiedD2] 獲取可用星座列表...')
            
            const response = await netstackFetch(`${this.baseUrl}/constellations`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const constellations: ConstellationInfo[] = await response.json()
            
            console.log('✅ [UnifiedD2] 成功獲取星座列表:', constellations.length, '個星座')
            return constellations

        } catch (error) {
            console.error('❌ [UnifiedD2] 獲取星座列表失敗:', error)
            throw error
        }
    }

    /**
     * 獲取指定星座的衛星列表
     */
    async getConstellationSatellites(constellation: string, limit = 100): Promise<SatelliteInfo[]> {
        try {
            console.log(`🔍 [UnifiedD2] 獲取 ${constellation} 衛星列表...`)
            
            const response = await netstackFetch(
                `${this.baseUrl}/constellations/${constellation}/satellites?limit=${limit}`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            )

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const satellites: SatelliteInfo[] = await response.json()
            
            console.log(`✅ [UnifiedD2] 成功獲取 ${constellation} 衛星:`, satellites.length, '顆')
            return satellites

        } catch (error) {
            console.error(`❌ [UnifiedD2] 獲取 ${constellation} 衛星列表失敗:`, error)
            throw error
        }
    }

    /**
     * 更新 TLE 數據
     */
    async updateTLEData(constellation: string, forceUpdate = false): Promise<TLEUpdateResponse> {
        try {
            console.log(`🔄 [UnifiedD2] 更新 ${constellation} TLE 數據...`)
            
            const request: TLEUpdateRequest = {
                constellation,
                force_update: forceUpdate
            }

            const response = await netstackFetch(`${this.baseUrl}/tle/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request)
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const result: TLEUpdateResponse = await response.json()
            
            console.log(`✅ [UnifiedD2] TLE 更新完成:`, result)
            return result

        } catch (error) {
            console.error(`❌ [UnifiedD2] TLE 更新失敗:`, error)
            throw error
        }
    }

    /**
     * 預計算 D2 測量數據
     */
    async precomputeD2Measurements(config: D2ScenarioConfig): Promise<D2PrecomputeResponse> {
        try {
            console.log(`🔄 [UnifiedD2] 預計算 D2 測量數據: ${config.scenario_name}`)
            
            const request: D2PrecomputeRequest = {
                scenario_name: config.scenario_name,
                constellation: config.constellation,
                ue_position: config.ue_position,
                fixed_ref_position: config.fixed_ref_position,
                thresh1: config.thresh1,
                thresh2: config.thresh2,
                hysteresis: config.hysteresis,
                duration_minutes: config.duration_minutes,
                sample_interval_seconds: config.sample_interval_seconds
            }

            const response = await netstackFetch(`${this.baseUrl}/d2/precompute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request)
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const result: D2PrecomputeResponse = await response.json()
            
            console.log(`✅ [UnifiedD2] D2 預計算完成:`, result)
            return result

        } catch (error) {
            console.error(`❌ [UnifiedD2] D2 預計算失敗:`, error)
            throw error
        }
    }

    /**
     * 獲取緩存的 D2 測量數據
     */
    async getCachedD2Measurements(scenarioHash: string, limit = 1000): Promise<D2MeasurementPoint[]> {
        try {
            // 檢查本地緩存
            const cacheKey = `d2_${scenarioHash}`
            const cached = this.cache.get(cacheKey)
            const expiry = this.cacheExpiry.get(cacheKey)
            
            if (cached && expiry && Date.now() < expiry) {
                console.log('📦 [UnifiedD2] 使用本地緩存數據:', cached.length, '個數據點')
                return cached
            }

            console.log(`🔍 [UnifiedD2] 獲取緩存的 D2 測量數據: ${scenarioHash}`)
            
            const response = await netstackFetch(
                `${this.baseUrl}/d2/measurements/${scenarioHash}?limit=${limit}`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            )

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const responseData = await response.json()
            const measurements: D2MeasurementPoint[] = responseData.measurements || []
            
            // 更新本地緩存
            this.cache.set(cacheKey, measurements)
            this.cacheExpiry.set(cacheKey, Date.now() + this.CACHE_TTL)
            
            console.log(`✅ [UnifiedD2] 成功獲取 D2 測量數據:`, measurements.length, '個數據點')
            return measurements

        } catch (error) {
            console.error(`❌ [UnifiedD2] 獲取 D2 測量數據失敗:`, error)
            throw error
        }
    }

    /**
     * 一鍵式獲取 D2 數據 (自動處理預計算和緩存)
     */
    async getD2Data(config: D2ScenarioConfig): Promise<D2MeasurementPoint[]> {
        try {
            console.log(`🚀 [UnifiedD2] 一鍵式獲取 D2 數據: ${config.scenario_name}`)

            // 1. 確保 TLE 數據是最新的
            await this.updateTLEData(config.constellation, false)

            // 2. 預計算 D2 測量數據
            const precomputeResult = await this.precomputeD2Measurements(config)

            // 3. 計算所需的數據點數量限制
            const totalSeconds = config.duration_minutes * 60
            const expectedDataPoints = Math.ceil(totalSeconds / config.sample_interval_seconds)
            const limit = Math.max(1000, expectedDataPoints + 100) // 至少1000個，或預期數量+緩衝

            console.log(`📊 [UnifiedD2] 計算數據點限制: ${config.duration_minutes}分鐘 × ${config.sample_interval_seconds}秒間隔 = ${expectedDataPoints}個數據點，設定限制為${limit}`)

            // 4. 獲取緩存的測量數據
            const measurements = await this.getCachedD2Measurements(precomputeResult.scenario_hash, limit)

            console.log(`✅ [UnifiedD2] 一鍵式獲取完成:`, measurements.length, '個數據點')
            return measurements

        } catch (error) {
            console.error(`❌ [UnifiedD2] 一鍵式獲取失敗:`, error)
            throw error
        }
    }

    /**
     * 清除本地緩存
     */
    clearCache(): void {
        this.cache.clear()
        this.cacheExpiry.clear()
        console.log('🧹 [UnifiedD2] 本地緩存已清除')
    }

    /**
     * 清除特定場景的緩存
     */
    clearScenarioCache(scenarioHash: string): void {
        const cacheKey = `d2_${scenarioHash}`
        this.cache.delete(cacheKey)
        this.cacheExpiry.delete(cacheKey)
        console.log(`🧹 [UnifiedD2] 場景緩存已清除: ${scenarioHash}`)
    }
}

// 導出單例實例
export const unifiedD2DataService = new UnifiedD2DataService()
export default unifiedD2DataService
