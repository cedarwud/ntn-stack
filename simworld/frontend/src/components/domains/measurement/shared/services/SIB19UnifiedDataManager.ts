/**
 * SIB19 統一數據管理器
 * 
 * 實現統一改進主準則 v3.0 的核心理念：
 * - 資訊統一：單一 SIB19 數據源為所有事件圖表提供統一資訊
 * - 應用分化：根據事件類型選擇性萃取和使用 SIB19 資訊子集
 * 
 * 解決當前架構問題：
 * 1. 消除資訊孤島 - 統一的數據源和更新機制
 * 2. 避免重複配置 - 單次配置，多處使用
 * 3. 提供統一基準 - 一致的時間、位置、精度標準
 * 4. 提升可擴展性 - 標準化的數據接口和組件規範
 */

import { EventEmitter } from 'events'

// 基礎數據類型定義
export interface Position {
  latitude: number
  longitude: number
  altitude: number
  x?: number
  y?: number
  z?: number
}

export interface SatellitePosition extends Position {
  satellite_id: string
  timestamp: number
  elevation: number
  azimuth: number
  distance: number
  velocity: {
    x: number
    y: number
    z: number
  }
}

export interface NeighborCellConfig {
  cell_id: string
  satellite_id: string
  carrier_freq: number
  phys_cell_id: number
  signal_strength: number
  is_active: boolean
}

export interface SMTCWindow {
  start_time: string
  end_time: string
  satellite_id: string
  measurement_type: string
  priority: number
}

export interface SIB19Data {
  broadcast_id: string
  broadcast_time: string
  validity_time: number
  time_to_expiry_hours: number
  satellites_count: number
  satellite_ephemeris: Record<string, any>
  reference_location: {
    type: string
    latitude: number
    longitude: number
    altitude: number
  }
  moving_reference_location?: {
    type: string
    satellite_id: string
    trajectory: Position[]
  }
  time_correction: {
    gnss_time_offset: number
    delta_gnss_time: number
    current_accuracy_ms: number
    sync_accuracy_ms: number
  }
  neighbor_cells: NeighborCellConfig[]
  smtc_windows: SMTCWindow[]
  status: 'valid' | 'expiring' | 'expired' | 'not_initialized'
}

// 事件特定數據類型
export interface A4VisualizationData {
  position_compensation: {
    delta_s: number
    effective_delta_s: number
    geometric_compensation_km: number
  }
  signal_strength: {
    serving_satellite: string
    target_satellite: string
    rsrp_dbm: number
    threshold: number
  }
  trigger_conditions: {
    is_triggered: boolean
    hysteresis: number
    time_to_trigger: number
  }
}

export interface D2VisualizationData {
  moving_reference: {
    current_position: Position
    trajectory: Position[]
    satellite_id: string
  }
  relative_distances: {
    satellite_distance: number
    ground_distance: number
    threshold1: number
    threshold2: number
  }
  movement_vector: {
    velocity_kmh: number
    direction_deg: number
  }
}

/**
 * SIB19 統一數據管理器
 * 
 * 核心職責：
 * 1. 統一數據源管理 - 單一 SIB19 數據源
 * 2. 事件特定數據萃取 - 根據事件類型提供專屬數據
 * 3. 自動更新機制 - 定期更新和失效管理
 * 4. 事件通知 - 數據變更時通知所有訂閱者
 */
export class SIB19UnifiedDataManager extends EventEmitter {
  private sib19Data: SIB19Data | null = null
  private satellitePositions: Map<string, SatellitePosition> = new Map()
  private lastUpdateTime: number = 0
  private updateInterval: number = 5000 // 5 秒更新間隔
  private autoUpdateTimer: NodeJS.Timeout | null = null
  private isUpdating: boolean = false

  constructor(updateInterval: number = 5000) {
    super()
    this.updateInterval = updateInterval
    this.startAutoUpdate()
  }

  /**
   * 啟動自動更新機制
   */
  private startAutoUpdate(): void {
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer)
    }

    this.autoUpdateTimer = setInterval(async () => {
      if (!this.isUpdating) {
        await this.updateSIB19Data()
      }
    }, this.updateInterval)
  }

  /**
   * 停止自動更新
   */
  public stopAutoUpdate(): void {
    if (this.autoUpdateTimer) {
      clearInterval(this.autoUpdateTimer)
      this.autoUpdateTimer = null
    }
  }

  /**
   * 更新 SIB19 數據
   * 統一的數據更新入口，確保所有圖表使用相同的數據源
   */
  public async updateSIB19Data(): Promise<boolean> {
    if (this.isUpdating) {
      return false
    }

    this.isUpdating = true

    try {
      // 調用統一的 SIB19 狀態 API
      const response = await fetch('/api/measurement-events/sib19-status')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const newData: SIB19Data = await response.json()
      
      // 更新衛星位置數據
      await this.updateSatellitePositions(newData)
      
      // 檢查數據是否有變化
      const hasChanged = this.hasDataChanged(newData)
      
      this.sib19Data = newData
      this.lastUpdateTime = Date.now()

      if (hasChanged) {
        // 通知所有訂閱者數據已更新
        this.emit('dataUpdated', this.sib19Data)
        
        // 發送事件特定的數據更新通知
        this.emit('a4DataUpdated', this.getA4SpecificData())
        this.emit('d2DataUpdated', this.getD2SpecificData())
      }

      return true

    } catch (error) {
      console.error('SIB19 數據更新失敗:', error)
      this.emit('updateError', error)
      return false
    } finally {
      this.isUpdating = false
    }
  }

  /**
   * 更新衛星位置數據
   */
  private async updateSatellitePositions(sib19Data: SIB19Data): Promise<void> {
    try {
      // 獲取所有衛星的當前位置
      const satelliteIds = Object.keys(sib19Data.satellite_ephemeris)
      
      for (const satelliteId of satelliteIds) {
        const response = await fetch(`/api/orbit/satellite/${satelliteId}/position`)
        if (response.ok) {
          const positionData = await response.json()
          
          const satellitePosition: SatellitePosition = {
            satellite_id: satelliteId,
            timestamp: positionData.timestamp,
            latitude: positionData.position.latitude,
            longitude: positionData.position.longitude,
            altitude: positionData.position.altitude,
            x: positionData.position.x,
            y: positionData.position.y,
            z: positionData.position.z,
            elevation: positionData.position.elevation || 0,
            azimuth: positionData.position.azimuth || 0,
            distance: positionData.position.distance || 0,
            velocity: positionData.position.velocity || { x: 0, y: 0, z: 0 }
          }
          
          this.satellitePositions.set(satelliteId, satellitePosition)
        }
      }
    } catch (error) {
      console.error('衛星位置更新失敗:', error)
    }
  }

  /**
   * 檢查數據是否有變化
   */
  private hasDataChanged(newData: SIB19Data): boolean {
    if (!this.sib19Data) return true
    
    return (
      this.sib19Data.broadcast_id !== newData.broadcast_id ||
      this.sib19Data.broadcast_time !== newData.broadcast_time ||
      this.sib19Data.status !== newData.status ||
      this.sib19Data.satellites_count !== newData.satellites_count
    )
  }

  /**
   * 獲取當前 SIB19 數據
   */
  public getSIB19Data(): SIB19Data | null {
    return this.sib19Data
  }

  /**
   * 獲取衛星位置數據
   */
  public getSatellitePositions(): Map<string, SatellitePosition> {
    return new Map(this.satellitePositions)
  }

  /**
   * 獲取特定衛星的位置
   */
  public getSatellitePosition(satelliteId: string): SatellitePosition | null {
    return this.satellitePositions.get(satelliteId) || null
  }

  /**
   * A4 事件特定數據萃取
   * 提取位置補償、信號強度、觸發條件等 A4 專屬資訊
   */
  public getA4SpecificData(): A4VisualizationData | null {
    if (!this.sib19Data) return null

    // 模擬 A4 事件特定數據 - 實際應從 API 獲取
    return {
      position_compensation: {
        delta_s: 0.0,
        effective_delta_s: 0.0,
        geometric_compensation_km: 0.0
      },
      signal_strength: {
        serving_satellite: Object.keys(this.sib19Data.satellite_ephemeris)[0] || '',
        target_satellite: Object.keys(this.sib19Data.satellite_ephemeris)[1] || '',
        rsrp_dbm: -80.0,
        threshold: -85.0
      },
      trigger_conditions: {
        is_triggered: false,
        hysteresis: 3.0,
        time_to_trigger: 160
      }
    }
  }

  /**
   * D2 事件特定數據萃取
   * 提取動態參考位置、相對距離等 D2 專屬資訊
   * 修正 Phase 2.1: 基於真實 LEO 衛星軌道計算 (90分鐘週期)
   */
  public getD2SpecificData(): D2VisualizationData | null {
    if (!this.sib19Data) return null

    const movingRef = this.sib19Data.moving_reference_location
    const currentTime = Date.now()

    // 基於真實 LEO 衛星軌道計算動態參考位置
    // 軌道週期: 90 分鐘 = 5400 秒
    const orbitalPeriod = 5400 // 秒
    const timeInOrbit = (currentTime / 1000) % orbitalPeriod
    const orbitalPhase = (timeInOrbit / orbitalPeriod) * 2 * Math.PI

    // LEO 衛星典型參數
    const _orbitalRadius = 6371 + 550 // 地球半徑 + 550km 高度
    const orbitalInclination = 53.0 * Math.PI / 180 // 53度傾角

    // 計算當前衛星位置 (簡化的軌道模型)
    const satellitePosition = {
      latitude: Math.asin(Math.sin(orbitalInclination) * Math.sin(orbitalPhase)) * 180 / Math.PI,
      longitude: (orbitalPhase * 180 / Math.PI - (currentTime / 1000) * 0.25) % 360, // 考慮地球自轉
      altitude: 550.0 // km
    }

    // 生成軌道軌跡 (未來 90 分鐘)
    const trajectory: Position[] = []
    for (let i = 0; i < 90; i += 5) { // 每 5 分鐘一個點
      const futureTime = timeInOrbit + i * 60
      const futurePhase = (futureTime / orbitalPeriod) * 2 * Math.PI
      trajectory.push({
        latitude: Math.asin(Math.sin(orbitalInclination) * Math.sin(futurePhase)) * 180 / Math.PI,
        longitude: (futurePhase * 180 / Math.PI - ((currentTime / 1000 + i * 60) * 0.25)) % 360,
        altitude: 550.0
      })
    }

    // 計算相對距離 (基於真實地理計算)
    const referenceLocation = this.sib19Data.reference_location

    // 衛星到地面參考點的距離 (3D 距離)
    const satelliteDistance = this.calculateDistance3D(
      satellitePosition,
      referenceLocation
    )

    // 地面距離 (2D 距離)
    const groundDistance = this.calculateDistance2D(
      satellitePosition,
      referenceLocation
    )

    // 計算移動向量
    const velocity_kmh = 27000.0 // 典型 LEO 衛星速度
    const direction_deg = (orbitalPhase * 180 / Math.PI + 90) % 360 // 軌道方向

    return {
      moving_reference: {
        current_position: satellitePosition,
        trajectory: trajectory,
        satellite_id: movingRef?.satellite_id || 'LEO_SAT_001'
      },
      relative_distances: {
        satellite_distance: satelliteDistance * 1000, // 轉換為米
        ground_distance: groundDistance * 1000, // 轉換為米
        threshold1: 800000.0, // 800 km
        threshold2: 30000.0   // 30 km
      },
      movement_vector: {
        velocity_kmh: velocity_kmh,
        direction_deg: direction_deg
      }
    }
  }

  /**
   * 計算 3D 距離 (考慮高度)
   */
  private calculateDistance3D(pos1: Position, pos2: Position): number {
    const R = 6371 // 地球半徑 (km)

    const lat1 = pos1.latitude * Math.PI / 180
    const lat2 = pos2.latitude * Math.PI / 180
    const deltaLat = (pos2.latitude - pos1.latitude) * Math.PI / 180
    const deltaLon = (pos2.longitude - pos1.longitude) * Math.PI / 180

    const a = Math.sin(deltaLat/2) * Math.sin(deltaLat/2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(deltaLon/2) * Math.sin(deltaLon/2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))

    const groundDistance = R * c
    const heightDiff = (pos1.altitude || 0) - (pos2.altitude || 0)

    return Math.sqrt(groundDistance * groundDistance + heightDiff * heightDiff)
  }

  /**
   * 計算 2D 距離 (不考慮高度)
   */
  private calculateDistance2D(pos1: Position, pos2: Position): number {
    const R = 6371 // 地球半徑 (km)

    const lat1 = pos1.latitude * Math.PI / 180
    const lat2 = pos2.latitude * Math.PI / 180
    const deltaLat = (pos2.latitude - pos1.latitude) * Math.PI / 180
    const deltaLon = (pos2.longitude - pos1.longitude) * Math.PI / 180

    const a = Math.sin(deltaLat/2) * Math.sin(deltaLat/2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(deltaLon/2) * Math.sin(deltaLon/2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))

    return R * c
  }

  /**
   * 獲取數據更新狀態
   */
  public getUpdateStatus(): {
    lastUpdateTime: number
    isUpdating: boolean
    autoUpdateEnabled: boolean
  } {
    return {
      lastUpdateTime: this.lastUpdateTime,
      isUpdating: this.isUpdating,
      autoUpdateEnabled: this.autoUpdateTimer !== null
    }
  }

  /**
   * 手動觸發數據更新
   */
  public async forceUpdate(): Promise<boolean> {
    return await this.updateSIB19Data()
  }

  /**
   * 清理資源
   */
  public destroy(): void {
    this.stopAutoUpdate()
    this.removeAllListeners()
    this.sib19Data = null
    this.satellitePositions.clear()
  }
}

// 單例模式 - 確保全局只有一個數據管理器實例
let globalDataManager: SIB19UnifiedDataManager | null = null

export function getSIB19UnifiedDataManager(): SIB19UnifiedDataManager {
  if (!globalDataManager) {
    globalDataManager = new SIB19UnifiedDataManager()
  }
  return globalDataManager
}

export function destroySIB19UnifiedDataManager(): void {
  if (globalDataManager) {
    globalDataManager.destroy()
    globalDataManager = null
  }
}
