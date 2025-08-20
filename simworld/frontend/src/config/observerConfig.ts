/**
 * 統一觀測配置服務 - 前端版本
 * 消除前端硬編碼座標重複，與後端 observer_config_service.py 對應
 */

export interface ObserverConfiguration {
    latitude: number
    longitude: number
    altitude_m: number
    location_name: string
    country: string
}

export interface ObserverCoordinates {
    lat: number
    lon: number
    alt: number
}

/**
 * 統一觀測配置服務類
 * 消除前端系統中的硬編碼座標重複
 */
class ObserverConfigService {
    private static instance: ObserverConfigService | null = null
    private config: ObserverConfiguration | null = null

    private constructor() {
        // 私有構造函數，確保單例模式
    }

    /**
     * 獲取服務單例
     */
    public static getInstance(): ObserverConfigService {
        if (!ObserverConfigService.instance) {
            ObserverConfigService.instance = new ObserverConfigService()
        }
        return ObserverConfigService.instance
    }

    /**
     * 獲取觀測點配置 - 統一接口
     */
    public getObserverConfig(): ObserverConfiguration {
        if (this.config === null) {
            this.config = this.loadObserverConfig()
            console.log(`✅ 前端觀測配置載入: ${this.config.location_name} (${this.config.latitude}°, ${this.config.longitude}°)`)
        }
        
        return this.config
    }

    /**
     * 載入觀測配置 - 優先環境變量，降級到標準NTPU位置
     */
    private loadObserverConfig(): ObserverConfiguration {
        // 瀏覽器環境安全檢查 - Vite 會在構建時替換 import.meta.env
        try {
            // 嘗試從環境變量載入（Vite 環境變量）
            const envLat = import.meta.env?.VITE_OBSERVER_LAT
            const envLon = import.meta.env?.VITE_OBSERVER_LON
            const envAlt = import.meta.env?.VITE_OBSERVER_ALT

            if (envLat && envLon) {
                console.log('🔧 使用環境變量觀測配置')
                return {
                    latitude: parseFloat(envLat),
                    longitude: parseFloat(envLon),
                    altitude_m: envAlt ? parseFloat(envAlt) : 50.0,
                    location_name: import.meta.env?.VITE_LOCATION_NAME || "Custom Location",
                    country: import.meta.env?.VITE_COUNTRY || "Taiwan"
                }
            }
        } catch (error) {
            // 環境變量訪問失敗，使用默認配置
            console.warn('⚠️ 無法訪問環境變量，使用默認NTPU配置')
        }

        // 標準NTPU觀測點配置 (消除硬編碼重複的唯一來源)
        return {
            latitude: 24.9441667,    // NTPU標準緯度
            longitude: 121.3713889,  // NTPU標準經度  
            altitude_m: 50.0,        // 標準海拔高度
            location_name: "NTPU",
            country: "Taiwan"
        }
    }

    /**
     * 返回座標對象格式 - 兼容現有代碼
     */
    public getCoordinates(): ObserverCoordinates {
        const config = this.getObserverConfig()
        return {
            lat: config.latitude,
            lon: config.longitude,
            alt: config.altitude_m
        }
    }

    /**
     * 返回 [緯度, 經度] 元組 - 兼容現有代碼
     */
    public getLatLonArray(): [number, number] {
        const config = this.getObserverConfig()
        return [config.latitude, config.longitude]
    }

    /**
     * 返回 [緯度, 經度, 高度] 元組 - 兼容現有代碼
     */
    public getLatLonAltArray(): [number, number, number] {
        const config = this.getObserverConfig()
        return [config.latitude, config.longitude, config.altitude_m]
    }

    /**
     * 獲取配置字典 - 兼容現有代碼
     */
    public getConfigDict(): { [key: string]: number | string } {
        const config = this.getObserverConfig()
        return {
            observerLat: config.latitude,
            observerLon: config.longitude,
            observerAlt: config.altitude_m,
            locationName: config.location_name,
            country: config.country
        }
    }

    /**
     * 重載配置（用於測試或動態配置）
     */
    public reloadConfig(): void {
        this.config = null
        console.log('🔄 觀測配置已重載')
    }
}

// 全局訪問函數
export const getObserverConfigService = (): ObserverConfigService => {
    return ObserverConfigService.getInstance()
}

/**
 * 快速獲取NTPU座標 - 消除硬編碼的統一接口
 */
export const getNTPUCoordinates = (): ObserverCoordinates => {
    return getObserverConfigService().getCoordinates()
}

/**
 * 快速獲取觀測配置 - 統一接口
 */
export const getObserverConfig = (): ObserverConfiguration => {
    return getObserverConfigService().getObserverConfig()
}

/**
 * 獲取觀測配置字典 - 兼容衛星服務配置
 */
export const getObserverConfigDict = (): { [key: string]: number | string } => {
    return getObserverConfigService().getConfigDict()
}

export default ObserverConfigService