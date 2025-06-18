/**
 * 真實衛星數據服務
 * 為立體圖提供真實衛星數據疊加功能
 */
import { ApiRoutes } from '../config/apiRoutes'
import { SATELLITE_CONFIG } from '../config/satellite.config'

export interface RealSatelliteInfo {
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
    signal_quality: {
        elevation_deg: number
        range_km: number
        estimated_signal_strength: number
        path_loss_db: number
    }
    timestamp: string
}

export interface RealSatelliteData {
    success: boolean
    observer: {
        latitude: number
        longitude: number
        altitude: number
    }
    results: {
        total_visible: number
        satellites: RealSatelliteInfo[]
    }
    timestamp: string
}

/**
 * 獲取可見衛星的真實數據
 */
export async function fetchRealSatelliteData(
    observerLat: number = 25.0,
    observerLon: number = 121.0,
    observerAlt: number = 100.0,
    minElevation: number = 5.0,
    maxResults: number = 50
): Promise<RealSatelliteData | null> {
    try {
        const apiUrl = `${ApiRoutes.satelliteOps.getVisibleSatellites}?observer_lat=${observerLat}&observer_lon=${observerLon}&observer_alt=${observerAlt}&min_elevation=${minElevation}&max_results=${maxResults}`
        
        const response = await fetch(apiUrl)
        
        if (!response.ok) {
            console.error(`Error fetching real satellite data: ${response.status} ${response.statusText}`)
            return null
        }
        
        const data: RealSatelliteData = await response.json()
        
        if (!data.success) {
            console.error('API returned unsuccessful response')
            return null
        }
        
        console.log(`🛰️ 獲取 ${data.results.total_visible} 顆真實可見衛星`)
        return data
        
    } catch (error) {
        console.error('Error fetching real satellite data:', error)
        return null
    }
}

/**
 * 將真實衛星數據映射到模擬衛星上
 * @param realSatellites 真實衛星數據
 * @param simulatedCount 模擬衛星數量 (預設18顆)
 */
export function mapRealSatellitesToSimulated(
    realSatellites: RealSatelliteInfo[],
    simulatedCount: number = 18
): Map<string, RealSatelliteInfo> {
    const mapping = new Map<string, RealSatelliteInfo>()
    
    // 取前 simulatedCount 顆衛星，或所有可用的衛星
    const availableSatellites = realSatellites.slice(0, simulatedCount)
    
    // 映射到模擬衛星 ID 上
    availableSatellites.forEach((realSat, index) => {
        const simulatedId = `sat_${index}`
        mapping.set(simulatedId, realSat)
    })
    
    // 如果真實衛星數量不足，用現有的衛星循環填充
    if (realSatellites.length > 0 && simulatedCount > realSatellites.length) {
        for (let i = realSatellites.length; i < simulatedCount; i++) {
            const simulatedId = `sat_${i}`
            const realSatIndex = i % realSatellites.length
            mapping.set(simulatedId, realSatellites[realSatIndex])
        }
    }
    
    return mapping
}

/**
 * 獲取衛星信號強度對應的顏色
 */
export function getSignalStrengthColor(signalStrength: number): string {
    if (signalStrength > 30) return '#00ff00' // 綠色 - 極佳信號
    if (signalStrength > 20) return '#80ff00' // 黃綠色 - 良好信號
    if (signalStrength > 10) return '#ffff00' // 黃色 - 可用信號
    if (signalStrength > 0) return '#ff8000' // 橙色 - 弱信號
    return '#ff0000' // 紅色 - 很弱信號
}

/**
 * 獲取衛星狀態描述
 */
export function getSatelliteStatusDescription(satellite: RealSatelliteInfo): string {
    const elevation = satellite.position.elevation
    const signalStrength = satellite.signal_quality.estimated_signal_strength
    
    let status = []
    
    if (elevation > 60) status.push('高仰角')
    else if (elevation > 30) status.push('中仰角')
    else status.push('低仰角')
    
    if (signalStrength > 20) status.push('強信號')
    else if (signalStrength > 10) status.push('中信號')
    else status.push('弱信號')
    
    return status.join(' · ')
}

/**
 * 真實衛星數據管理類
 */
export class RealSatelliteDataManager {
    private data: RealSatelliteData | null = null
    private mapping: Map<string, RealSatelliteInfo> = new Map()
    private lastUpdateTime: number = 0
    private updateInterval: number = 30000 // 30秒更新一次
    
    constructor() {
        this.startPeriodicUpdate()
    }
    
    async updateData(): Promise<boolean> {
        const newData = await fetchRealSatelliteData()
        
        if (newData) {
            this.data = newData
            this.mapping = mapRealSatellitesToSimulated(newData.results.satellites)
            this.lastUpdateTime = Date.now()
            return true
        }
        
        return false
    }
    
    getRealSatelliteInfo(simulatedId: string): RealSatelliteInfo | null {
        return this.mapping.get(simulatedId) || null
    }
    
    getAllMappings(): Map<string, RealSatelliteInfo> {
        return this.mapping
    }
    
    getLastUpdateTime(): number {
        return this.lastUpdateTime
    }
    
    isDataFresh(): boolean {
        return (Date.now() - this.lastUpdateTime) < this.updateInterval * 2
    }
    
    private startPeriodicUpdate(): void {
        // 立即更新一次
        this.updateData()
        
        // 設置定期更新
        setInterval(() => {
            this.updateData()
        }, this.updateInterval)
    }
    
    destroy(): void {
        // 清理資源
        this.data = null
        this.mapping.clear()
    }
}

// 單例實例
export const realSatelliteDataManager = new RealSatelliteDataManager()