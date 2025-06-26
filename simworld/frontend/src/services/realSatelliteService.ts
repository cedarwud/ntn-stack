/**
 * 真實衛星數據服務
 * 為立體圖提供真實衛星數據疊加功能
 */
import { ApiRoutes } from '../config/apiRoutes'
import { SATELLITE_CONFIG as _SATELLITE_CONFIG } from '../config/satellite.config'

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
    observerLat: number = 0.0,      // 預設赤道位置，全球視野
    observerLon: number = 0.0,      // 預設本初子午線
    observerAlt: number = 0.0,      // 預設海平面
    minElevation: number = -10.0,   // 預設-10度，包含地平線以下
    maxResults: number = 100,       // 預設獲取100顆衛星
    globalView: boolean = true      // 預設啟用全球視野
): Promise<RealSatelliteData | null> {
    try {
        // 構建API URL，包含觀察者位置參數
        const params = new URLSearchParams({
            count: maxResults.toString(),
            min_elevation_deg: minElevation.toString(),
            observer_lat: observerLat.toString(),
            observer_lon: observerLon.toString(),
            observer_alt: observerAlt.toString(),
            global_view: globalView.toString()
        })
        
        const apiUrl = `${ApiRoutes.satelliteOps.getVisibleSatellites}?${params.toString()}`
        
        // 減少重複日誌 - 只在首次請求時記錄
    // console.log(`🛰️ 請求衛星數據: 觀察者位置(${observerLat}, ${observerLon}, ${observerAlt}m), 全球視野: ${globalView}`)
        
        const response = await fetch(apiUrl)
        
        if (!response.ok) {
            console.error(`Error fetching real satellite data: ${response.status} ${response.statusText}`)
            return null
        }
        
        const apiData = await response.json()
        
        // 檢查 API 回傳的實際格式
        if (!apiData.satellites || !Array.isArray(apiData.satellites)) {
            console.error('API returned unexpected format:', apiData)
            return null
        }
        
        // 轉換 API 格式為前端期望的格式
         
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const satellites: RealSatelliteInfo[] = apiData.satellites.map((sat: any) => ({
            id: parseInt(sat.norad_id) || 0,
            name: (sat.name || '').replace(' [DTC]', '').replace('[DTC]', ''), // 移除DTC標記
            norad_id: sat.norad_id,
            position: {
                latitude: 0, // API 沒有提供，使用預設值
                longitude: 0, // API 沒有提供，使用預設值
                altitude: sat.orbit_altitude_km || 0,
                elevation: sat.elevation_deg || 0,
                azimuth: sat.azimuth_deg || 0,
                range: sat.distance_km || 0,
                velocity: sat.velocity_km_s || 0,
                doppler_shift: 0 // API 沒有提供，使用預設值
            },
            signal_quality: {
                elevation_deg: sat.elevation_deg || 0,
                range_km: sat.distance_km || 0,
                estimated_signal_strength: Math.min(100, (sat.elevation_deg || 0) * 2), // 基於仰角估算信號強度
                path_loss_db: 20 * Math.log10(Math.max(1, sat.distance_km || 1)) + 92.45 + 20 * Math.log10(2.15) // 2.15 GHz
            },
            timestamp: new Date().toISOString()
        }))
        
        const data: RealSatelliteData = {
            success: true,
            observer: {
                latitude: observerLat,
                longitude: observerLon,
                altitude: observerAlt
            },
            results: {
                total_visible: satellites.length,
                satellites: satellites
            },
            timestamp: new Date().toISOString()
        }
        
        // 減少重複日誌 - 只在數據量顯著變化時記錄
        // console.log(`🛰️ 獲取 ${data.results.total_visible} 顆真實可見衛星 (全球視野: ${globalView})`)
        // console.log(`📊 處理統計: 處理=${apiData.processed}, 可見=${apiData.visible}`)
        
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
    
    const status = []
    
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
    private updateInterval: number = 30000 // 恢復為30秒更新一次，減少日誌
    private observerLat: number = 0.0
    private observerLon: number = 0.0
    private observerAlt: number = 0.0
    private globalView: boolean = true
    private lastLoggedSatelliteCount: number = 0
    private lastLoggedGlobalView: boolean = false
    
    constructor(
        observerLat: number = 0.0,      // 預設赤道位置
        observerLon: number = 0.0,      // 預設本初子午線  
        observerAlt: number = 0.0,      // 預設海平面
        globalView: boolean = true      // 預設啟用全球視野
    ) {
        this.observerLat = observerLat
        this.observerLon = observerLon
        this.observerAlt = observerAlt
        this.globalView = globalView
        // 立即更新一次數據
        this.updateData().then(() => {
            console.log('🚀 初始衛星數據已載入')
        })
        this.startPeriodicUpdate()
    }
    
    async updateData(): Promise<boolean> {
        const newData = await fetchRealSatelliteData(
            this.observerLat,
            this.observerLon,
            this.observerAlt,
            this.globalView ? -10.0 : 5.0,  // 全球視野使用-10度仰角
            this.globalView ? 150 : 50,     // 全球視野獲取更多衛星
            this.globalView
        )
        
        if (newData) {
            this.data = newData
            this.mapping = mapRealSatellitesToSimulated(
                newData.results.satellites,
                this.globalView ? 30 : 18  // 全球視野映射更多衛星
            )
            this.lastUpdateTime = Date.now()
            
            // 只有當衛星數量或全球視野狀態發生變化時才記錄日誌
            const satelliteCountChanged = this.lastLoggedSatelliteCount !== newData.results.total_visible
            const globalViewChanged = this.lastLoggedGlobalView !== this.globalView
            
            if (satelliteCountChanged || globalViewChanged) {
                // console.log(`🔄 衛星數據更新完成: ${newData.results.total_visible} 顆衛星 (全球視野: ${this.globalView})`) // 減少重複日誌
                this.lastLoggedSatelliteCount = newData.results.total_visible
                this.lastLoggedGlobalView = this.globalView
            }
            
            return true
        }
        
        return false
    }
    
    // 設置觀察者位置
    setObserverPosition(lat: number, lon: number, alt: number = 100.0): void {
        if (this.observerLat !== lat || this.observerLon !== lon || this.observerAlt !== alt) {
            // 只在顯著位置變化時記錄日誌（避免微小變化產生大量日誌）
            const significantChange = Math.abs(lat - this.observerLat) > 0.1 || Math.abs(lon - this.observerLon) > 0.1 || Math.abs(alt - this.observerAlt) > 10
            if (significantChange) {
                console.log(`📍 觀察者位置已更新: (${lat}, ${lon}, ${alt}m)`)
            }
            
            this.observerLat = lat
            this.observerLon = lon
            this.observerAlt = alt
            // 立即更新數據
            this.updateData()
        }
    }
    
    // 切換全球視野模式
    setGlobalView(enabled: boolean): void {
        if (this.globalView !== enabled) {
            this.globalView = enabled
            console.log(`🌍 全球視野模式: ${enabled ? '開啟' : '關閉'}`)
            // 立即更新數據
            this.updateData()
        }
    }
    
    getObserverPosition(): { lat: number, lon: number, alt: number } {
        return {
            lat: this.observerLat,
            lon: this.observerLon,
            alt: this.observerAlt
        }
    }
    
    isGlobalViewEnabled(): boolean {
        return this.globalView
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

// 全球衛星數據管理器實例 - 預設全球視野模式獲取所有Starlink和Kuiper衛星
export const realSatelliteDataManager = new RealSatelliteDataManager(
    0.0,     // 赤道位置
    0.0,     // 本初子午線
    0.0,     // 海平面
    true     // 全球視野模式 - 獲取全球所有通信衛星
)