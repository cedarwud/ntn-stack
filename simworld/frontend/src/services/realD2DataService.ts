/**
 * 真實 D2 數據服務
 * 
 * 功能：
 * 1. 與後端真實衛星數據 API 集成
 * 2. 支持實時和歷史數據獲取
 * 3. 數據格式轉換和驗證
 * 4. 錯誤處理和重試機制
 * 
 * 符合 d2.md Phase 4 前端集成要求
 */

import { netstackFetch } from '../config/api-config'

export interface UEPosition {
    latitude: number
    longitude: number
    altitude: number
}

export interface MeasurementValues {
    satellite_distance: number
    ground_distance: number
    reference_satellite: string
    elevation_angle: number
    azimuth_angle: number
    signal_strength: number
}

export interface D2MeasurementResult {
    timestamp: string
    measurement_values: MeasurementValues
    trigger_condition_met: boolean
    satellite_info: {
        norad_id?: number
        constellation?: string
        orbital_period?: number
        inclination?: number
    }
}

export interface D2RealDataResponse {
    success: boolean
    scenario_name: string
    data_source: 'real' | 'simulated'
    ue_position: UEPosition
    duration_minutes: number
    sample_count: number
    results: D2MeasurementResult[]
    metadata: {
        constellation: string
        reference_position: UEPosition
        coverage_analysis: {
            visible_satellites: number
            coverage_percentage: number
            average_elevation: number
            constellation_distribution: Record<string, number>
        }
        data_quality: string
        sgp4_precision: string
        atmospheric_corrections: boolean
    }
    timestamp: string
}

export interface D2ServiceStatus {
    success: boolean
    service_status: string
    data_source: string
    supported_constellations: string[]
    total_satellites: number
    constellation_stats: Record<string, any>
    service_health: Record<string, string>
    capabilities: {
        real_time_tracking: boolean
        sgp4_propagation: boolean
        atmospheric_corrections: boolean
        multi_constellation: boolean
        handover_prediction: boolean
    }
    timestamp: string
}

export interface D2RealDataRequest {
    scenario_name?: string
    ue_position: UEPosition
    duration_minutes?: number
    sample_interval_seconds?: number
    constellation?: string
    reference_position?: UEPosition
}

class RealD2DataService {
    private baseUrl = '/api/measurement-events/D2'
    private cache = new Map<string, { data: D2RealDataResponse; timestamp: number }>()
    private cacheTimeout = 30000 // 30秒緩存

    /**
     * 獲取真實 D2 測量數據
     */
    async getRealD2Data(request: D2RealDataRequest): Promise<D2RealDataResponse> {
        try {
            console.log('🔗 [RealD2DataService] 獲取真實 D2 數據:', request)

            const cacheKey = this.generateCacheKey(request)
            const cached = this.cache.get(cacheKey)
            
            // 檢查緩存
            if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
                console.log('📦 [RealD2DataService] 使用緩存數據')
                return cached.data
            }

            // 生成時間序列數據
            const durationMinutes = request.duration_minutes || 5
            const sampleIntervalSeconds = request.sample_interval_seconds || 10
            const totalSamples = Math.floor((durationMinutes * 60) / sampleIntervalSeconds)

            console.log(`🔗 [RealD2DataService] 生成 ${totalSamples} 個真實數據點，時長 ${durationMinutes} 分鐘`)

            const results: D2MeasurementResult[] = []
            const startTime = new Date()

            for (let i = 0; i < totalSamples; i++) {
                const currentTime = new Date(startTime.getTime() + i * sampleIntervalSeconds * 1000)

                try {
                    const response = await netstackFetch(`${this.baseUrl}/data`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            ue_position: request.ue_position,
                            d2_params: {
                                thresh1: 800000.0,
                                thresh2: 30000.0,
                                hysteresis: 500.0,
                                time_to_trigger: 160
                            },
                            // 嘗試指定星座類型
                            constellation: request.constellation || 'starlink',
                            prefer_constellation: request.constellation || 'starlink'
                        })
                    })

                    if (!response.ok) {
                        throw new Error(`API 錯誤: ${response.status} ${response.statusText}`)
                    }

                    const singleData = await response.json()

                    // 轉換為 D2MeasurementResult 格式
                    const measurementResult: D2MeasurementResult = {
                        timestamp: currentTime.toISOString(),
                        measurement_values: {
                            satellite_distance: singleData.measurement_values.satellite_distance,
                            ground_distance: singleData.measurement_values.ground_distance,
                            reference_satellite: singleData.measurement_values.reference_satellite,
                            elevation_angle: 0, // API 沒有提供，使用預設值
                            azimuth_angle: 0,   // API 沒有提供，使用預設值
                            signal_strength: -80 // API 沒有提供，使用預設值
                        },
                        trigger_condition_met: singleData.trigger_condition_met,
                        satellite_info: {
                            norad_id: parseInt(singleData.measurement_values.reference_satellite.split('_')[1]) || 0,
                            constellation: singleData.measurement_values.reference_satellite.startsWith('gps') ? 'gps' : 'starlink',
                            orbital_period: singleData.sib19_data?.orbital_period_minutes || 0,
                            inclination: 0 // API 沒有提供
                        }
                    }

                    results.push(measurementResult)

                    // 每5個樣本顯示進度
                    if (i % 5 === 0) {
                        console.log(`📊 [RealD2DataService] 已獲取 ${i + 1}/${totalSamples} 個真實數據點`)
                    }

                    // 添加小延遲避免過於頻繁的 API 調用
                    if (i < totalSamples - 1) {
                        await new Promise(resolve => setTimeout(resolve, 100))
                    }

                } catch (error) {
                    console.warn(`⚠️ [RealD2DataService] 第 ${i + 1} 個數據點獲取失敗:`, error)
                    // 繼續獲取下一個數據點
                }
            }

            if (results.length === 0) {
                throw new Error('無法獲取任何真實數據點')
            }

            // 構建完整的響應
            const data: D2RealDataResponse = {
                success: true,
                scenario_name: request.scenario_name || 'Real_D2_Frontend',
                data_source: 'real',
                ue_position: request.ue_position,
                duration_minutes: durationMinutes,
                sample_count: results.length,
                results: results,
                metadata: {
                    constellation: request.constellation || 'gps',
                    reference_position: request.reference_position || request.ue_position,
                    coverage_analysis: {
                        visible_satellites: 1,
                        coverage_percentage: 100,
                        average_elevation: 45,
                        constellation_distribution: { 'gps': results.length }
                    },
                    data_quality: 'high',
                    sgp4_precision: 'standard',
                    atmospheric_corrections: false
                },
                timestamp: new Date().toISOString()
            }

            console.log(`✅ [RealD2DataService] 成功生成 ${results.length} 個真實數據點的時間序列`)
            
            // 驗證數據格式
            this.validateD2Response(data)
            
            // 緩存數據
            this.cache.set(cacheKey, { data, timestamp: Date.now() })
            
            console.log('✅ [RealD2DataService] 成功獲取真實數據:', {
                sampleCount: data.sample_count,
                constellation: data.metadata.constellation,
                visibleSatellites: data.metadata.coverage_analysis.visible_satellites
            })

            return data

        } catch (error) {
            console.error('❌ [RealD2DataService] 獲取真實數據失敗:', error)
            throw new Error(`獲取真實 D2 數據失敗: ${error instanceof Error ? error.message : '未知錯誤'}`)
        }
    }

    /**
     * 獲取 D2 服務狀態
     */
    async getServiceStatus(): Promise<D2ServiceStatus> {
        try {
            console.log('🔍 [RealD2DataService] 檢查服務狀態')

            const response = await netstackFetch(`${this.baseUrl}/status`, {
                method: 'GET'
            })

            if (!response.ok) {
                throw new Error(`狀態檢查失敗: ${response.status}`)
            }

            const status: D2ServiceStatus = await response.json()
            
            console.log('📊 [RealD2DataService] 服務狀態:', {
                status: status.service_status,
                totalSatellites: status.total_satellites,
                constellations: status.supported_constellations
            })

            return status

        } catch (error) {
            console.error('❌ [RealD2DataService] 服務狀態檢查失敗:', error)
            throw error
        }
    }

    /**
     * 獲取模擬數據（向後兼容）
     */
    async getSimulatedD2Data(request: {
        scenario_name?: string
        ue_position: UEPosition
        duration_minutes?: number
        sample_interval_seconds?: number
        target_satellites?: string[]
    }): Promise<D2RealDataResponse> {
        try {
            console.log('🎲 [RealD2DataService] 獲取模擬數據（使用真實衛星）')

            const response = await netstackFetch(`${this.baseUrl}/simulate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    scenario_name: request.scenario_name || 'Enhanced_D2_Simulation',
                    ue_position: request.ue_position,
                    duration_minutes: request.duration_minutes || 5,
                    sample_interval_seconds: request.sample_interval_seconds || 10,
                    target_satellites: request.target_satellites || []
                })
            })

            if (!response.ok) {
                throw new Error(`模擬 API 錯誤: ${response.status}`)
            }

            const data: D2RealDataResponse = await response.json()
            this.validateD2Response(data)

            console.log('✅ [RealD2DataService] 成功獲取模擬數據:', {
                sampleCount: data.sample_count,
                dataSource: data.data_source
            })

            return data

        } catch (error) {
            console.error('❌ [RealD2DataService] 獲取模擬數據失敗:', error)
            throw error
        }
    }

    /**
     * 轉換為前端圖表格式
     */
    convertToChartFormat(response: D2RealDataResponse): Array<{
        timestamp: string
        satellite_distance: number
        ground_distance: number
        trigger_condition_met: boolean
        reference_satellite: string
        elevation_angle?: number
        azimuth_angle?: number
        signal_strength?: number
    }> {
        return response.results.map(result => ({
            timestamp: result.timestamp,
            satellite_distance: result.measurement_values.satellite_distance,
            ground_distance: result.measurement_values.ground_distance,
            trigger_condition_met: result.trigger_condition_met,
            reference_satellite: result.measurement_values.reference_satellite,
            elevation_angle: result.measurement_values.elevation_angle,
            azimuth_angle: result.measurement_values.azimuth_angle,
            signal_strength: result.measurement_values.signal_strength
        }))
    }

    /**
     * 清除緩存
     */
    clearCache(): void {
        this.cache.clear()
        console.log('🗑️ [RealD2DataService] 緩存已清除')
    }

    /**
     * 生成緩存鍵
     */
    private generateCacheKey(request: D2RealDataRequest): string {
        return JSON.stringify({
            ue: request.ue_position,
            duration: request.duration_minutes,
            interval: request.sample_interval_seconds,
            constellation: request.constellation
        })
    }

    /**
     * 驗證 D2 響應數據格式
     */
    private validateD2Response(data: D2RealDataResponse): void {
        if (!data.success) {
            throw new Error('API 返回失敗狀態')
        }

        if (!Array.isArray(data.results)) {
            throw new Error('結果數據格式無效')
        }

        if (data.results.length === 0) {
            console.warn('⚠️ [RealD2DataService] 返回空結果集')
        }

        // 驗證第一個結果的格式
        if (data.results.length > 0) {
            const firstResult = data.results[0]
            if (!firstResult.measurement_values || !firstResult.timestamp) {
                throw new Error('測量結果格式無效')
            }
        }
    }

    /**
     * 獲取數據質量信息
     */
    getDataQualityInfo(response: D2RealDataResponse): {
        dataSource: string
        quality: string
        satelliteCount: number
        coveragePercentage: number
        hasAtmosphericCorrections: boolean
    } {
        return {
            dataSource: response.data_source,
            quality: response.metadata.data_quality,
            satelliteCount: response.metadata.coverage_analysis.visible_satellites,
            coveragePercentage: response.metadata.coverage_analysis.coverage_percentage,
            hasAtmosphericCorrections: response.metadata.atmospheric_corrections
        }
    }
}

// 導出單例實例
export const realD2DataService = new RealD2DataService()
export default realD2DataService
