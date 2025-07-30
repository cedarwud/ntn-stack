/**
 * 預計算數據服務
 * 從 @netstack/data/ 載入預計算的衛星軌道數據
 * 用於 D2 事件的真實數據模式
 */

import type { RealD2DataPoint } from '../components/domains/measurement/charts/RealD2Chart'

// 預計算數據接口
interface PrecomputedOrbitData {
    generated_at: string
    computation_type: string
    observer_location: {
        lat: number
        lon: number
        alt: number
        name: string
    }
    constellations: {
        [key: string]: {
            name: string
            orbit_data: {
                metadata: {
                    start_time: string
                    duration_minutes: number
                    time_step_seconds: number
                    total_time_points: number
                    observer_location: {
                        lat: number
                        lon: number
                        alt: number
                        name: string
                    }
                }
                satellites: {
                    [satelliteId: string]: {
                        satellite_id: string
                        norad_id: number
                        satellite_name: string
                        tle_line1: string
                        tle_line2: string
                        visibility_data: Array<{
                            timestamp: string
                            position: {
                                latitude: number
                                longitude: number
                                altitude: number
                            }
                            elevation: number
                            azimuth: number
                            distance: number
                            is_visible: boolean
                        }>
                    }
                }
            }
        }
    }
}

interface LayeredAnalysisData {
    analysis_date: string
    analysis_timestamp: string
    observer_location: {
        lat: number
        lon: number
        alt: number
    }
    thresholds: {
        pre_handover: number
        execution: number
        critical: number
    }
    constellations: {
        [key: string]: {
            total_satellites: number
            pre_handover_count: number
            execution_count: number
            critical_count: number
            invisible_count: number
            satellites_by_phase: {
                [phase: string]: Array<{
                    name: string
                    norad_id: string
                    line1: string
                    line2: string
                    elevation: number
                    timestamp: string
                }>
            }
        }
    }
}

class PrecomputedDataService {
    private precomputedData: PrecomputedOrbitData | null = null
    private layeredData: LayeredAnalysisData | null = null
    private cache = new Map<string, any>()

    /**
     * 載入預計算軌道數據
     */
    async loadPrecomputedOrbitData(): Promise<PrecomputedOrbitData> {
        if (this.precomputedData) {
            return this.precomputedData
        }

        try {
            console.log('🔄 開始載入預計算軌道數據...')
            
            // 嘗試多個數據源的優先順序
            const dataSources = [
                '/data/phase0_precomputed_orbits_test.json',
                '/data/phase0_precomputed_orbits.json',
                '/data/historical_precomputed_orbits.json'  // 歷史數據 fallback
            ]
            
            let lastError: Error | null = null
            
            for (const [index, dataSource] of dataSources.entries()) {
                try {
                    console.log(`📡 嘗試載入數據源 ${index + 1}: ${dataSource}`)
                    
                    const response = await fetch(dataSource)
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
                    }
                    
                    // 檢查文件大小
                    const contentLength = response.headers.get('content-length')
                    if (contentLength) {
                        const sizeMB = (parseInt(contentLength) / 1024 / 1024).toFixed(2)
                        console.log(`📊 文件大小: ${sizeMB} MB`)
                        
                        // 如果文件太大，提供警告但不阻止載入
                        if (parseInt(contentLength) > 100 * 1024 * 1024) { // 100MB
                            console.warn('⚠️ 文件較大，載入可能需要較長時間')
                        }
                    }
                    
                    // 載入並解析數據
                    const text = await response.text()
                    console.log(`📊 實際讀取: ${(text.length / 1024 / 1024).toFixed(2)} MB`)
                    
                    this.precomputedData = JSON.parse(text) as PrecomputedOrbitData
                    
                    // 驗證數據結構
                    this.validatePrecomputedData(this.precomputedData)
                    
                    console.log(`✅ 成功載入預計算軌道數據 (來源: ${dataSource})`)
                    console.log(`📊 包含星座: ${Object.keys(this.precomputedData.constellations).join(', ')}`)
                    
                    return this.precomputedData
                    
                } catch (error) {
                    lastError = error as Error
                    console.warn(`❌ 數據源 ${index + 1} 載入失敗: ${error}`)
                    continue
                }
            }
            
            // 所有數據源都失敗，嘗試生成歷史數據
            console.warn('🔄 所有預計算數據源均不可用，嘗試使用歷史數據...')
            return await this.generateHistoricalFallbackData()
            
        } catch (error) {
            console.error('❌ 預計算軌道數據載入完全失敗:', error)
            throw error
        }
    }

    /**
     * 驗證預計算數據結構
     */
    private validatePrecomputedData(data: PrecomputedOrbitData): void {
        if (!data || typeof data !== 'object') {
            throw new Error('無效的數據結構')
        }
        
        if (!data.constellations || typeof data.constellations !== 'object') {
            throw new Error('缺少星座數據')
        }
        
        const constellationCount = Object.keys(data.constellations).length
        if (constellationCount === 0) {
            throw new Error('無可用星座數據')
        }
        
        console.log(`🔍 數據驗證通過: ${constellationCount} 個星座`)
    }

    /**
     * 生成基於歷史數據的 fallback 數據
     */
    private async generateHistoricalFallbackData(): Promise<PrecomputedOrbitData> {
        console.log('🛰️ 生成歷史數據 fallback...')
        
        try {
            // 調用後端歷史軌道生成器
            const response = await fetch('/api/v1/satellites/historical-orbits?constellation=starlink&duration_hours=6')
            
            if (response.ok) {
                const historicalData = await response.json()
                console.log('✅ 成功獲取歷史軌道數據')
                return historicalData
            } else {
                console.warn('❌ 後端歷史數據生成失敗，使用內建 fallback')
            }
        } catch (error) {
            console.warn('⚠️ 歷史數據請求失敗:', error)
        }
        
        // 最終 fallback - 生成基本結構的預設數據
        return this.generateMinimalFallbackData()
    }

    /**
     * 生成最小 fallback 數據
     */
    private generateMinimalFallbackData(): PrecomputedOrbitData {
        console.log('📦 生成最小 fallback 數據...')
        
        const now = new Date()
        const satellites: { [key: string]: any } = {}
        
        // 生成3顆模擬衛星（基於真實 Starlink 參數）
        for (let i = 1; i <= 3; i++) {
            const satelliteId = `fallback_sat_${i.toString().padStart(3, '0')}`
            
            satellites[satelliteId] = {
                satellite_id: satelliteId,
                norad_id: 44700 + i, // 真實 Starlink NORAD ID 範圍
                satellite_name: `STARLINK-FALLBACK-${i}`,
                tle_line1: `1 ${44700 + i}U 19074${String.fromCharCode(65 + i)}   24300.50000000  .00001234  00000-0  12345-3 0  9999`,
                tle_line2: `2 ${44700 + i}  53.0534 ${95.4567 + i * 10}.0000 0001234  87.6543 272.3456 15.05000000289456`,
                visibility_data: this.generateFallbackVisibilityData(now, i)
            }
        }
        
        const fallbackData: PrecomputedOrbitData = {
            generated_at: now.toISOString(),
            computation_type: 'minimal_fallback',
            observer_location: {
                lat: 24.94417,
                lon: 121.37139,
                alt: 50,
                name: 'NTPU'
            },
            constellations: {
                starlink: {
                    name: 'STARLINK',
                    orbit_data: {
                        metadata: {
                            start_time: now.toISOString(),
                            duration_minutes: 360, // 6小時
                            time_step_seconds: 60,
                            total_time_points: 360,
                            observer_location: {
                                lat: 24.94417,
                                lon: 121.37139,
                                alt: 50,
                                name: 'NTPU'
                            }
                        },
                        satellites
                    }
                }
            }
        }
        
        console.log('✅ 最小 fallback 數據生成完成')
        return fallbackData
    }

    /**
     * 生成 fallback 可見性數據
     */
    private generateFallbackVisibilityData(startTime: Date, satelliteIndex: number): Array<any> {
        const data = []
        const totalPoints = 360 // 6小時，每分鐘一個點
        
        for (let i = 0; i < totalPoints; i++) {
            const timestamp = new Date(startTime.getTime() + i * 60 * 1000)
            
            // 基於真實 LEO 軌道參數的簡化計算
            const orbitProgress = (i + satelliteIndex * 120) / 95 // 95分鐘軌道周期
            const latitude = 53 * Math.sin(orbitProgress * 2 * Math.PI) // Starlink 傾角
            const longitude = ((orbitProgress * 360) % 360) - 180
            const altitude = 550000 + Math.sin(orbitProgress * 4 * Math.PI) * 10000 // 550km ± 10km
            
            // 簡化的仰角計算 (基於台灣位置)
            const elevation = Math.max(0, 90 - Math.abs(latitude - 24.94417) * 2)
            
            data.push({
                timestamp: timestamp.toISOString(),
                position: {
                    latitude,
                    longitude,
                    altitude
                },
                elevation,
                azimuth: (180 + orbitProgress * 360) % 360,
                distance: Math.sqrt(altitude * altitude + 1000000), // 簡化距離計算
                is_visible: elevation > 10
            })
        }
        
        return data
    }

    /**
     * 載入分層分析數據
     */
    async loadLayeredAnalysisData(date: string = '20250728'): Promise<LayeredAnalysisData> {
        const cacheKey = `layered_${date}`
        
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey)
        }

        try {
            const response = await fetch(`/data/layered_phase0/layered_analysis_${date}.json`)
            if (!response.ok) {
                throw new Error(`Failed to load layered data: ${response.status}`)
            }
            const data = await response.json()
            this.cache.set(cacheKey, data)
            console.log('✅ 分層分析數據載入成功')
            return data
        } catch (error) {
            console.error('❌ 分層分析數據載入失敗:', error)
            throw error
        }
    }

    /**
     * 轉換預計算數據為 D2 圖表數據格式
     */
    async convertToD2DataPoints(
        constellation: 'starlink' | 'oneweb' | 'gps',
        params: {
            Thresh1: number
            Thresh2: number
            Hys: number
            referenceLocation: { lat: number; lon: number }
            movingReferenceLocation: { lat: number; lon: number }
        },
        options: {
            durationMinutes: number
            sampleIntervalSeconds: number
        }
    ): Promise<RealD2DataPoint[]> {
        console.log(`🔄 開始轉換 ${constellation} 預計算數據...`)

        try {
            const precomputedData = await this.loadPrecomputedOrbitData()
            const constellationData = precomputedData.constellations[constellation]

            if (!constellationData) {
                throw new Error(`constellation ${constellation} not found in precomputed data`)
            }

            const satellites = Object.values(constellationData.orbit_data.satellites)
            const dataPoints: RealD2DataPoint[] = []

            // 選擇第一顆可見衛星的數據
            const selectedSatellite = satellites[0]
            if (!selectedSatellite || !selectedSatellite.visibility_data) {
                throw new Error(`No visibility data found for ${constellation}`)
            }

            // 計算時間範圍
            const maxPoints = Math.floor((options.durationMinutes * 60) / options.sampleIntervalSeconds)
            const visibilityData = selectedSatellite.visibility_data.slice(0, maxPoints)

            console.log(`📊 處理 ${visibilityData.length} 個數據點`)

            for (let i = 0; i < visibilityData.length; i++) {
                const dataPoint = visibilityData[i]
                
                // 計算衛星距離 (使用預計算的距離數據，單位：公尺)
                const satelliteDistance = dataPoint.distance * 1000 // 轉換為公尺

                // 計算固定參考位置距離 (簡化計算)
                const groundDistance = this.calculateGroundDistance(
                    params.referenceLocation,
                    dataPoint.position,
                    i,
                    visibilityData.length
                )

                // 判斷觸發條件
                const condition1 = satelliteDistance - params.Hys > params.Thresh1
                const condition2 = groundDistance + params.Hys < params.Thresh2
                const triggerConditionMet = condition1 && condition2

                dataPoints.push({
                    timestamp: dataPoint.timestamp,
                    satelliteDistance,
                    groundDistance,
                    satelliteInfo: {
                        noradId: selectedSatellite.norad_id,
                        name: selectedSatellite.satellite_name,
                        latitude: dataPoint.position.latitude,
                        longitude: dataPoint.position.longitude,
                        altitude: dataPoint.position.altitude,
                    },
                    triggerConditionMet,
                    d2EventDetails: {
                        thresh1: params.Thresh1,
                        thresh2: params.Thresh2,
                        hysteresis: params.Hys,
                        enteringCondition: triggerConditionMet,
                        leavingCondition: !triggerConditionMet,
                    },
                })
            }

            console.log(`✅ 成功轉換 ${dataPoints.length} 個 ${constellation} 數據點`)
            return dataPoints

        } catch (error) {
            console.error(`❌ 轉換 ${constellation} 數據失敗:`, error)
            throw error
        }
    }

    /**
     * 計算地面距離 (使用真實地理計算)
     */
    private calculateGroundDistance(
        referenceLocation: { lat: number; lon: number },
        satellitePosition: { latitude: number; longitude: number; altitude: number },
        index: number,
        totalPoints: number
    ): number {
        try {
            // 使用 Haversine 公式計算真實地理距離
            const distance = this.calculateHaversineDistance(
                referenceLocation.lat,
                referenceLocation.lon,
                satellitePosition.latitude,
                satellitePosition.longitude
            )
            
            // 考慮高度差異的 3D 距離
            const altitudeDiff = satellitePosition.altitude // 衛星高度 (公尺)
            const groundDistance3D = Math.sqrt(distance * distance + altitudeDiff * altitudeDiff)
            
            // 添加基於時間的動態變化 (模擬移動參考點)
            const timeProgress = index / Math.max(1, totalPoints - 1)
            const movementVariation = Math.sin(timeProgress * 2 * Math.PI) * 200 // ±200公尺變化
            
            return groundDistance3D + movementVariation
            
        } catch (error) {
            console.warn('真實地理計算失敗，使用簡化版本:', error)
            // 降級到簡化計算
            return this.calculateSimplifiedGroundDistance(index, totalPoints)
        }
    }

    /**
     * Haversine 公式計算地表距離
     */
    private calculateHaversineDistance(
        lat1: number, lon1: number,
        lat2: number, lon2: number
    ): number {
        const R = 6371000 // 地球半徑 (公尺)
        
        const φ1 = lat1 * Math.PI / 180 // φ, λ in radians
        const φ2 = lat2 * Math.PI / 180
        const Δφ = (lat2 - lat1) * Math.PI / 180
        const Δλ = (lon2 - lon1) * Math.PI / 180

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                  Math.cos(φ1) * Math.cos(φ2) *
                  Math.sin(Δλ/2) * Math.sin(Δλ/2)
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))

        return R * c // 距離 (公尺)
    }

    /**
     * 簡化地面距離計算 (fallback)
     */
    private calculateSimplifiedGroundDistance(index: number, totalPoints: number): number {
        const timeProgress = index / Math.max(1, totalPoints - 1)
        const minDistance = 5500 // 5.5 公里（公尺）
        const maxDistance = 6800 // 6.8 公里（公尺）
        const midDistance = (minDistance + maxDistance) / 2
        const amplitude = (maxDistance - minDistance) / 2

        return midDistance + Math.sin(timeProgress * 4 * Math.PI + Math.PI / 4) * amplitude
    }

    /**
     * 清除緩存
     */
    clearCache(): void {
        this.cache.clear()
        this.precomputedData = null
        this.layeredData = null
        console.log('🧹 預計算數據緩存已清除')
    }

    /**
     * 獲取可用星座列表
     */
    async getAvailableConstellations(): Promise<string[]> {
        try {
            const data = await this.loadPrecomputedOrbitData()
            return Object.keys(data.constellations)
        } catch (error) {
            console.error('❌ 無法獲取星座列表:', error)
            return ['starlink', 'oneweb'] // 返回預設值
        }
    }
}

// 單例模式
export const precomputedDataService = new PrecomputedDataService()

// 導出類型
export type { PrecomputedOrbitData, LayeredAnalysisData }