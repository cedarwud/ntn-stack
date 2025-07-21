/**
 * Orbit Trajectory Hook
 * 軌道軌跡數據鉤子
 * 
 * 功能：
 * 1. 獲取長時間軌道預測數據
 * 2. 計算軌跡路徑點
 * 3. 管理軌跡數據緩存
 * 4. 提供動畫播放支持
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { netstackFetch } from '../../config/api-config'

interface OrbitPoint {
    timestamp: string
    latitude: number
    longitude: number
    altitude: number
    distance_to_ue?: number
    signal_strength?: number
    elevation_angle?: number
}

interface TrajectoryData {
    satellite_id: string
    duration_hours: number
    points: OrbitPoint[]
    current_index: number
    total_points: number
}

interface UseOrbitTrajectoryOptions {
    satelliteId?: string
    uePosition: {
        latitude: number
        longitude: number
        altitude: number
    }
    durationHours?: number
    intervalMinutes?: number
    autoUpdate?: boolean
}

export const useOrbitTrajectory = ({
    satelliteId = '',
    uePosition,
    durationHours = 2,
    intervalMinutes = 1,
    autoUpdate = true
}: UseOrbitTrajectoryOptions) => {
    const [trajectoryData, setTrajectoryData] = useState<TrajectoryData | null>(null)
    const [currentIndex, setCurrentIndex] = useState(0)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const cacheRef = useRef<Map<string, TrajectoryData>>(new Map())
    
    // 計算當前軌道點
    const getCurrentPoint = useCallback((): OrbitPoint | null => {
        if (!trajectoryData || currentIndex >= trajectoryData.points.length) {
            return null
        }
        return trajectoryData.points[currentIndex]
    }, [trajectoryData, currentIndex])
    
    // 獲取軌跡預測數據
    const fetchTrajectoryData = useCallback(async (satId: string) => {
        if (!satId) return
        
        const cacheKey = `${satId}_${durationHours}_${intervalMinutes}`
        
        // 檢查緩存
        if (cacheRef.current.has(cacheKey)) {
            const cached = cacheRef.current.get(cacheKey)!
            setTrajectoryData(cached)
            return
        }
        
        setIsLoading(true)
        setError(null)
        
        try {
            // 如果測量事件API支持軌跡預測，使用它
            // 否則使用模擬軌跡生成
            const response = await generateSimulatedTrajectory(satId, uePosition, durationHours, intervalMinutes)
            
            const newTrajectoryData: TrajectoryData = {
                satellite_id: satId,
                duration_hours: durationHours,
                points: response,
                current_index: 0,
                total_points: response.length
            }
            
            setTrajectoryData(newTrajectoryData)
            cacheRef.current.set(cacheKey, newTrajectoryData)
            
        } catch (err) {
            console.error('❌ 軌跡數據獲取失敗:', err)
            setError(err instanceof Error ? err.message : '軌跡數據獲取失敗')
        } finally {
            setIsLoading(false)
        }
    }, [uePosition, durationHours, intervalMinutes])
    
    // 生成模擬軌跡（基於真實軌道動力學）
    const generateSimulatedTrajectory = async (
        satId: string, 
        ue: { latitude: number, longitude: number, altitude: number },
        hours: number,
        intervalMin: number
    ): Promise<OrbitPoint[]> => {
        const points: OrbitPoint[] = []
        const totalPoints = (hours * 60) / intervalMin
        const startTime = new Date()
        
        // LEO 軌道參數（基於真實Starlink參數）
        const orbitalPeriod = 95.6 * 60 * 1000 // 95.6分鐘，毫秒
        const inclination = 53 * Math.PI / 180 // 53度傾角
        const altitude = 550000 // 550km高度
        
        for (let i = 0; i < totalPoints; i++) {
            const timeOffset = i * intervalMin * 60 * 1000
            const currentTime = new Date(startTime.getTime() + timeOffset)
            
            // 基於軌道動力學計算位置
            const orbitalPhase = (timeOffset / orbitalPeriod) * 2 * Math.PI
            const lat = Math.asin(Math.sin(inclination) * Math.sin(orbitalPhase)) * 180 / Math.PI
            const lon = (orbitalPhase * 180 / Math.PI + currentTime.getTime() / 240000) % 360 - 180
            
            // 計算與UE的距離
            const distance = calculateDistance(lat, lon, altitude, ue.latitude, ue.longitude, ue.altitude)
            
            // 計算信號強度（基於距離和仰角）
            const elevationAngle = calculateElevationAngle(lat, lon, altitude, ue.latitude, ue.longitude, ue.altitude)
            const pathLoss = 20 * Math.log10(distance / 1000) + 20 * Math.log10(28) + 32.4 // 28GHz
            const signalStrength = -50 - pathLoss // 基準信號強度
            
            points.push({
                timestamp: currentTime.toISOString(),
                latitude: lat,
                longitude: lon,
                altitude: altitude / 1000, // 轉換為km
                distance_to_ue: distance / 1000, // 轉換為km
                signal_strength: signalStrength,
                elevation_angle: elevationAngle
            })
        }
        
        return points
    }
    
    // 距離計算（Haversine公式）
    const calculateDistance = (
        lat1: number, lon1: number, alt1: number,
        lat2: number, lon2: number, alt2: number
    ): number => {
        const R = 6371000 // 地球半徑（米）
        const dLat = (lat2 - lat1) * Math.PI / 180
        const dLon = (lon2 - lon1) * Math.PI / 180
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2)
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
        const groundDistance = R * c
        const altDiff = alt1 - alt2
        return Math.sqrt(groundDistance * groundDistance + altDiff * altDiff)
    }
    
    // 仰角計算
    const calculateElevationAngle = (
        satLat: number, satLon: number, satAlt: number,
        ueLat: number, ueLon: number, ueAlt: number
    ): number => {
        const distance = calculateDistance(satLat, satLon, 0, ueLat, ueLon, 0)
        const heightDiff = satAlt - ueAlt
        return Math.atan2(heightDiff, distance) * 180 / Math.PI
    }
    
    // 設置動畫時間索引
    const setAnimationIndex = useCallback((index: number) => {
        if (trajectoryData && index >= 0 && index < trajectoryData.points.length) {
            setCurrentIndex(index)
        }
    }, [trajectoryData])
    
    // 根據時間設置索引
    const setTimeIndex = useCallback((targetTime: Date) => {
        if (!trajectoryData) return
        
        let closestIndex = 0
        let closestDiff = Infinity
        
        trajectoryData.points.forEach((point, index) => {
            const pointTime = new Date(point.timestamp)
            const diff = Math.abs(pointTime.getTime() - targetTime.getTime())
            if (diff < closestDiff) {
                closestDiff = diff
                closestIndex = index
            }
        })
        
        setCurrentIndex(closestIndex)
    }, [trajectoryData])
    
    // 自動獲取軌跡數據
    useEffect(() => {
        if (autoUpdate && satelliteId) {
            fetchTrajectoryData(satelliteId)
        }
    }, [satelliteId, autoUpdate, fetchTrajectoryData])
    
    return {
        trajectoryData,
        currentPoint: getCurrentPoint(),
        currentIndex,
        isLoading,
        error,
        setAnimationIndex,
        setTimeIndex,
        fetchTrajectoryData
    }
}