/**
 * 統一預計算數據服務
 * 整合 NetStack API 預計算數據和本地數據載入功能
 */
import type {
  OrbitData,
  OptimalTimeWindow,
  DisplayData
} from '../types/satellite'
import type { RealD2DataPoint } from '../components/domains/measurement/charts/RealD2Chart'
import { unifiedNetStackApi } from './unified-netstack-api'

// ================== 服務配置 ==================

export interface PrecomputedOrbitConfig {
  location: string
  constellation: 'starlink' | 'oneweb'
  elevationThreshold?: number
  environment: 'open_area' | 'urban' | 'mountainous'
  useLayeredThresholds: boolean
}

export interface AnimationConfig {
  acceleration: number      // 動畫加速倍數 (預設 60)
  distanceScale: number     // 距離縮放比例 (預設 0.1) 
  fps: number              // 動畫幀率 (預設 30)
  smoothing: boolean       // 軌跡平滑化
}

// NetStack 預計算數據格式
export interface NetStackOrbitData {
  satellites: Array<{
    norad_id: string
    name: string
    positions: Array<{
      timestamp: string
      latitude: number
      longitude: number
      altitude: number
      elevation: number
      azimuth: number
      distance: number
      is_visible: boolean
    }>
  }>
  metadata: {
    generated_at: string
    observer_location: Record<string, unknown>
    duration_minutes: number
    time_step_seconds: number
  }
}

// 本地預計算數據格式
interface LocalPrecomputedData {
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
          }
        }
        time_series: Array<{
          timestamp: string
          visible_satellites: Array<{
            norad_id: string
            name: string
            position: {
              latitude: number
              longitude: number
              altitude: number
            }
            visibility: {
              elevation: number
              azimuth: number
              distance: number
              is_visible: boolean
            }
          }>
        }>
      }
    }
  }
}

// ================== 統一預計算服務 ==================

export class UnifiedPrecomputedService {
  private config: PrecomputedOrbitConfig
  private animationConfig: AnimationConfig
  private cachedData: Map<string, unknown> = new Map()
  
  constructor() {
    this.config = {
      location: 'NTPU',
      constellation: 'starlink',
      elevationThreshold: 10,
      environment: 'urban',
      useLayeredThresholds: true
    }
    
    this.animationConfig = {
      acceleration: 60,
      distanceScale: 0.1,
      fps: 30,
      smoothing: true
    }
  }
  
  // ========== 配置管理 ==========
  
  updateConfig(newConfig: Partial<PrecomputedOrbitConfig>): void {
    this.config = { ...this.config, ...newConfig }
    this.cachedData.clear() // 清除緩存
  }
  
  updateAnimationConfig(newConfig: Partial<AnimationConfig>): void {
    this.animationConfig = { ...this.animationConfig, ...newConfig }
  }
  
  getConfig(): PrecomputedOrbitConfig {
    return { ...this.config }
  }
  
  getAnimationConfig(): AnimationConfig {
    return { ...this.animationConfig }
  }
  
  // ========== NetStack API 數據獲取 ==========
  
  async getNetStackOrbitData(
    constellation: 'starlink' | 'oneweb',
    startTime: string,
    durationMinutes: number,
    observerLocation: { lat: number; lon: number; elevation_m?: number }
  ): Promise<NetStackOrbitData> {
    const cacheKey = `netstack_${constellation}_${startTime}_${durationMinutes}`
    
    if (this.cachedData.has(cacheKey)) {
      return this.cachedData.get(cacheKey)
    }
    
    try {
      const data = await unifiedNetStackApi.getPrecomputedOrbitData({
        constellation,
        start_time: startTime,
        duration_minutes: durationMinutes,
        observer_location: observerLocation,
        elevation_threshold_deg: this.config.elevationThreshold
      })
      
      this.cachedData.set(cacheKey, data)
      return data
    } catch (error) {
      console.error('獲取 NetStack 預計算數據失敗:', error)
      throw error
    }
  }
  
  // ========== 本地數據載入 ==========
  
  async loadLocalPrecomputedData(): Promise<LocalPrecomputedData> {
    const cacheKey = 'local_precomputed'
    
    if (this.cachedData.has(cacheKey)) {
      return this.cachedData.get(cacheKey)
    }
    
    try {
      // 從本地文件載入預計算數據
      const response = await fetch('/data/precomputed_orbit_data.json')
      if (!response.ok) {
        throw new Error(`載入本地數據失敗: ${response.status}`)
      }
      
      const data = await response.json()
      this.cachedData.set(cacheKey, data)
      return data
    } catch (error) {
      console.error('載入本地預計算數據失敗:', error)
      throw error
    }
  }
  
  // ========== 數據轉換與處理 ==========
  
  convertNetStackToOrbitData(netStackData: NetStackOrbitData): OrbitData[] {
    return netStackData.satellites.map(satellite => ({
      noradId: satellite.norad_id,
      name: satellite.name,
      positions: satellite.positions.map(pos => ({
        timestamp: new Date(pos.timestamp),
        latitude: pos.latitude,
        longitude: pos.longitude,
        altitude: pos.altitude,
        elevation: pos.elevation,
        azimuth: pos.azimuth,
        distance: pos.distance,
        isVisible: pos.is_visible
      }))
    }))
  }
  
  convertLocalToOrbitData(localData: LocalPrecomputedData, constellation: string): OrbitData[] {
    const constData = localData.constellations[constellation]
    if (!constData) return []
    
    // 提取所有衛星的位置數據
    const satelliteMap = new Map<string, OrbitData>()
    
    constData.orbit_data.time_series.forEach(timePoint => {
      timePoint.visible_satellites.forEach(sat => {
        if (!satelliteMap.has(sat.norad_id)) {
          satelliteMap.set(sat.norad_id, {
            noradId: sat.norad_id,
            name: sat.name,
            positions: []
          })
        }
        
        satelliteMap.get(sat.norad_id).positions.push({
          timestamp: new Date(timePoint.timestamp),
          latitude: sat.position.latitude,
          longitude: sat.position.longitude,
          altitude: sat.position.altitude,
          elevation: sat.visibility.elevation,
          azimuth: sat.visibility.azimuth,
          distance: sat.visibility.distance,
          isVisible: sat.visibility.is_visible
        })
      })
    })
    
    return Array.from(satelliteMap.values())
  }
  
  // ========== 數據分析與優化 ==========
  
  findOptimalTimeWindows(orbitData: OrbitData[]): OptimalTimeWindow[] {
    const _timeWindows: OptimalTimeWindow[] = []
    
    // 分析每個時間段的可見衛星數量
    const timePoints = new Map<number, { time: Date; visibleCount: number; satellites: string[] }>()
    
    orbitData.forEach(satellite => {
      satellite.positions.forEach(pos => {
        if (pos.isVisible) {
          const timeKey = pos.timestamp.getTime()
          if (!timePoints.has(timeKey)) {
            timePoints.set(timeKey, {
              time: pos.timestamp,
              visibleCount: 0,
              satellites: []
            })
          }
          timePoints.get(timeKey)!.visibleCount++
          timePoints.get(timeKey)!.satellites.push(satellite.name)
        }
      })
    })
    
    // 找出高可見性時間段
    const sortedTimes = Array.from(timePoints.values())
      .sort((a, b) => b.visibleCount - a.visibleCount)
      .slice(0, 10) // 取前 10 個最佳時間段
    
    return sortedTimes.map((point, index) => ({
      startTime: point.time,
      endTime: new Date(point.time.getTime() + 5 * 60 * 1000), // 5分鐘窗口
      visibleSatellites: point.visibleCount,
      quality: Math.max(0.5, Math.min(1.0, point.visibleCount / 8)), // 8顆衛星為最佳
      description: `時間段 ${index + 1}: ${point.visibleCount} 顆可見衛星`,
      satellites: point.satellites
    }))
  }
  
  generateDisplayData(orbitData: OrbitData[], timeRange: { start: Date; end: Date }): DisplayData {
    // 過濾時間範圍內的數據
    const filteredData = orbitData.map(satellite => ({
      ...satellite,
      positions: satellite.positions.filter(pos => 
        pos.timestamp >= timeRange.start && pos.timestamp <= timeRange.end
      )
    })).filter(satellite => satellite.positions.length > 0)
    
    // 生成顯示統計
    let totalVisibleCount = 0
    let maxSimultaneous = 0
    const coverageMap = new Map<number, number>()
    
    filteredData.forEach(satellite => {
      satellite.positions.forEach(pos => {
        if (pos.isVisible) {
          totalVisibleCount++
          const timeKey = Math.floor(pos.timestamp.getTime() / (5 * 60 * 1000)) // 5分鐘槽
          coverageMap.set(timeKey, (coverageMap.get(timeKey) || 0) + 1)
        }
      })
    })
    
    maxSimultaneous = Math.max(...Array.from(coverageMap.values()), 0)
    
    return {
      satellites: filteredData,
      metadata: {
        timeRange,
        totalSatellites: filteredData.length,
        totalVisiblePositions: totalVisibleCount,
        maxSimultaneousVisible: maxSimultaneous,
        averageVisible: totalVisibleCount / Math.max(1, coverageMap.size),
        coverage: (coverageMap.size * 5) / 60, // 小時數
        animationConfig: this.animationConfig
      }
    }
  }
  
  // ========== D2 測量數據支援 ==========
  
  async generateD2MeasurementData(
    constellation: string,
    timeRange: { start: Date; end: Date }
  ): Promise<RealD2DataPoint[]> {
    try {
      const localData = await this.loadLocalPrecomputedData()
      const orbitData = this.convertLocalToOrbitData(localData, constellation)
      
      const d2Points: RealD2DataPoint[] = []
      
      // 生成 D2 測量數據點
      orbitData.forEach(satellite => {
        satellite.positions.forEach(pos => {
          if (pos.isVisible && pos.timestamp >= timeRange.start && pos.timestamp <= timeRange.end) {
            d2Points.push({
              timestamp: pos.timestamp,
              satelliteName: satellite.name,
              d2Distance: pos.distance,
              elevation: pos.elevation,
              azimuth: pos.azimuth,
              signalStrength: this.calculateSignalStrength(pos.distance, pos.elevation),
              isHandoverCandidate: pos.elevation >= (this.config.elevationThreshold || 10)
            })
          }
        })
      })
      
      return d2Points.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
    } catch (error) {
      console.error('生成 D2 測量數據失敗:', error)
      return []
    }
  }
  
  // ========== 私有輔助方法 ==========
  
  private calculateSignalStrength(distance: number, elevation: number): number {
    // 簡化的信號強度計算（基於距離和仰角）
    const pathLoss = 20 * Math.log10(distance) + 20 * Math.log10(28e9) - 147.55 // 自由空間路徑損耗
    const elevationGain = Math.max(0, Math.sin(elevation * Math.PI / 180) * 3) // 仰角增益
    return Math.max(-120, -pathLoss + elevationGain) // 限制最小值
  }
  
  // ========== 緩存管理 ==========
  
  clearCache(): void {
    this.cachedData.clear()
  }
  
  getCacheSize(): number {
    return this.cachedData.size
  }
}

// 單例導出
export const unifiedPrecomputedService = new UnifiedPrecomputedService()

// 向後兼容的導出
export default unifiedPrecomputedService