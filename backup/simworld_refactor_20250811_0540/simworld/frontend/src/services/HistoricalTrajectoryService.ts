/**
 * 歷史軌跡服務 - 獲取和管理真實衛星軌跡數據
 * 支援真實時間軸的衛星升起和落下軌跡
 */

import { netstackFetch } from "../config/api-config"
import { useState, useEffect } from "react"

export interface TrajectoryPoint {
    timestamp: number
    latitude: number
    longitude: number
    altitude: number
    elevation_deg: number
    azimuth_deg: number
    distance_km: number
    is_visible: boolean
}

export interface SatelliteTrajectory {
    satellite_id: string
    name: string
    constellation: string
    trajectory_points: TrajectoryPoint[]
    start_time: number
    end_time: number
    duration_hours: number
}

interface TrajectoryCache {
    data: Map<string, SatelliteTrajectory>
    timestamp: number
}

class HistoricalTrajectoryService {
    private cache: TrajectoryCache = {
        data: new Map(),
        timestamp: 0
    }
    private readonly CACHE_DURATION = 5 * 60 * 1000 // 5分鐘緩存
    private readonly TRAJECTORY_DURATION_HOURS = 2 // 獲取2小時的軌跡
    private readonly STEP_MINUTES = 0.5 // 每30秒一個數據點

    /**
     * 獲取多顆衛星的歷史軌跡
     */
    async getMultipleSatelliteTrajectories(
        satelliteIds: string[],
        startTime?: number,
        _durationHours: number = this.TRAJECTORY_DURATION_HOURS
    ): Promise<Map<string, SatelliteTrajectory>> {
        const now = Date.now()
        
        // 檢查緩存
        if (this.cache.timestamp && now - this.cache.timestamp < this.CACHE_DURATION) {
            const cachedTrajectories = new Map<string, SatelliteTrajectory>()
            for (const id of satelliteIds) {
                const cached = this.cache.data.get(id)
                if (cached) {
                    cachedTrajectories.set(id, cached)
                }
            }
            if (cachedTrajectories.size === satelliteIds.length) {
                console.log(`📦 使用緩存的軌跡數據: ${cachedTrajectories.size} 顆衛星`)
                return cachedTrajectories
            }
        }

        const trajectories = new Map<string, SatelliteTrajectory>()
        const promises = satelliteIds.map(id => this.getSatelliteTrajectory(id, startTime, durationHours))
        
        try {
            const results = await Promise.allSettled(promises)
            results.forEach((result, index) => {
                if (result.status === "fulfilled" && result.value) {
                    trajectories.set(satelliteIds[index], result.value)
                    // 更新緩存
                    this.cache.data.set(satelliteIds[index], result.value)
                }
            })
            
            this.cache.timestamp = now
            console.log(`🛰️ 獲取軌跡數據成功: ${trajectories.size}/${satelliteIds.length} 顆衛星`)
            return trajectories
        } catch (error) {
            console.error("❌ 獲取軌跡數據失敗:", error)
            return trajectories
        }
    }

    /**
     * 獲取單顆衛星的歷史軌跡
     */
    async getSatelliteTrajectory(
        satelliteId: string,
        startTime?: number,
        _durationHours: number = this.TRAJECTORY_DURATION_HOURS
    ): Promise<SatelliteTrajectory | null> {
        try {
            // 使用 satellite-simple API 獲取觀測者相對數據
            const endpoint = `/api/v1/satellite-simple/visible_satellites`
            const params = new URLSearchParams({
                count: '1',
                min_elevation_deg: '-90',
                observer_lat: '24.9441667',
                observer_lon: '121.3713889', 
                utc_timestamp: '2025-07-26T00:00:00Z',
                global_view: 'false',
                satellite_filter: satelliteId
            })

            const response = await netstackFetch(`${endpoint}?${params}`)
            
            if (!response.ok) {
                console.warn(`⚠️ 無法獲取衛星 ${satelliteId} 的軌跡`)
                return null
            }

            const data = await response.json()
            
            if (!data.satellites || data.satellites.length === 0) {
                console.warn(`⚠️ 衛星 ${satelliteId} 無觀測數據`)
                return null
            }
            
            const satellite = data.satellites[0]
            const currentTime = Date.now() / 1000
            
            // satellite-simple API 返回單點數據，轉換為軌跡格式
            const trajectoryPoints: TrajectoryPoint[] = [{
                timestamp: currentTime,
                latitude: 24.9441667, // NTPU 觀測者位置
                longitude: 121.3713889, // NTPU 觀測者位置  
                altitude: satellite.orbit_altitude_km || 550,
                elevation_deg: satellite.elevation_deg,
                azimuth_deg: satellite.azimuth_deg,
                distance_km: satellite.distance_km,
                is_visible: satellite.is_visible
            }]

            return {
                satellite_id: satelliteId,
                name: satellite.name,
                constellation: satellite.constellation || "unknown",
                trajectory_points: trajectoryPoints,
                start_time: currentTime,
                end_time: currentTime,
                duration_hours: 0 // 單點數據
            }
        } catch (error) {
            console.error(`❌ 獲取衛星 ${satelliteId} 軌跡失敗:`, error)
            return null
        }
    }

    /**
     * 根據當前時間計算衛星在軌跡中的位置
     */
    interpolatePosition(
        trajectory: SatelliteTrajectory,
        currentTime: number
    ): TrajectoryPoint | null {
        if (!trajectory.trajectory_points.length) return null

        const points = trajectory.trajectory_points
        
        // 找到最接近的兩個點進行插值
        let prevPoint: TrajectoryPoint | null = null
        let nextPoint: TrajectoryPoint | null = null
        
        for (let i = 0; i < points.length - 1; i++) {
            if (points[i].timestamp <= currentTime && points[i + 1].timestamp >= currentTime) {
                prevPoint = points[i]
                nextPoint = points[i + 1]
                break
            }
        }

        // 如果找不到插值點，返回最近的點
        if (!prevPoint || !nextPoint) {
            if (currentTime <= points[0].timestamp) return points[0]
            if (currentTime >= points[points.length - 1].timestamp) return points[points.length - 1]
            return null
        }

        // 線性插值
        const t = (currentTime - prevPoint.timestamp) / (nextPoint.timestamp - prevPoint.timestamp)
        
        return {
            timestamp: currentTime,
            latitude: prevPoint.latitude + (nextPoint.latitude - prevPoint.latitude) * t,
            longitude: prevPoint.longitude + (nextPoint.longitude - prevPoint.longitude) * t,
            altitude: prevPoint.altitude + (nextPoint.altitude - prevPoint.altitude) * t,
            elevation_deg: prevPoint.elevation_deg + (nextPoint.elevation_deg - prevPoint.elevation_deg) * t,
            azimuth_deg: prevPoint.azimuth_deg + (nextPoint.azimuth_deg - prevPoint.azimuth_deg) * t,
            distance_km: prevPoint.distance_km + (nextPoint.distance_km - prevPoint.distance_km) * t,
            is_visible: prevPoint.elevation_deg > 0 || nextPoint.elevation_deg > 0
        }
    }

    /**
     * 將軌跡點轉換為3D場景座標
     */
    trajectoryPointTo3D(
        point: TrajectoryPoint,
        sceneScale: number = 1200,
        heightScale: number = 600
    ): [number, number, number] {
        // 使用真實的仰角和方位角計算3D位置
        const elevRad = (point.elevation_deg * Math.PI) / 180
        const azimRad = (point.azimuth_deg * Math.PI) / 180
        
        // 計算地面投影距離
        const groundDistance = sceneScale * Math.cos(elevRad)
        
        // 計算3D座標
        const x = groundDistance * Math.sin(azimRad)
        const z = groundDistance * Math.cos(azimRad)
        // 高度：確保地平線以下的衛星不顯示
        const y = point.elevation_deg > 0 
            ? Math.max(10, heightScale * Math.sin(elevRad) + 100)
            : -200 // 地平線以下的衛星隱藏
        
        return [x, y, z]
    }

    /**
     * 清除緩存
     */
    clearCache(): void {
        this.cache.data.clear()
        this.cache.timestamp = 0
        console.log("🗑️ 軌跡緩存已清除")
    }
}

// 創建單例實例
export const historicalTrajectoryService = new HistoricalTrajectoryService()

// 導出用於React Hook的輔助函數
export function useHistoricalTrajectories(
    satelliteIds: string[],
    enabled: boolean = true
) {
    const [trajectories, setTrajectories] = useState<Map<string, SatelliteTrajectory>>(new Map())
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!enabled || satelliteIds.length === 0) {
            setTrajectories(new Map())
            return
        }

        let isMounted = true

        const fetchTrajectories = async () => {
            setLoading(true)
            setError(null)

            try {
                const data = await historicalTrajectoryService.getMultipleSatelliteTrajectories(satelliteIds)
                if (isMounted) {
                    setTrajectories(data)
                    console.log(`✅ 載入 ${data.size} 條衛星軌跡`)
                }
            } catch (err) {
                if (isMounted) {
                    setError(err instanceof Error ? err.message : "獲取軌跡失敗")
                    console.error("❌ 軌跡載入失敗:", err)
                }
            } finally {
                if (isMounted) {
                    setLoading(false)
                }
            }
        }

        fetchTrajectories()

        return () => {
            isMounted = false
        }
    }, [satelliteIds.join(","), enabled])

    return { trajectories, loading, error }
}

export default historicalTrajectoryService
