/**
 * 動態衛星池服務
 * 
 * 負責載入和管理階段6生成的動態衛星池數據，
 * 確保前端只使用優化後的90-110顆衛星而非391顆全量數據
 */

import { simworldFetch } from '../config/api-config'

export interface DynamicPoolData {
    starlink_satellites: string[]  // 衛星ID列表
    oneweb_satellites: string[]
    total_selected: number
    coverage_metrics?: {
        starlink_coverage_score: number
        oneweb_coverage_score: number
    }
}

export interface DynamicPoolConfig {
    useOptimizedPool: boolean  // 是否使用優化池（true）或全量數據（false）
    poolDataPath: string       // 動態池數據文件路徑
}

class DynamicPoolService {
    private static instance: DynamicPoolService
    private poolData: DynamicPoolData | null = null
    private config: DynamicPoolConfig = {
        useOptimizedPool: true,  // 默認使用優化池
        poolDataPath: '/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json'
    }
    private loadPromise: Promise<void> | null = null

    private constructor() {}

    /**
     * 獲取單例實例
     */
    public static getInstance(): DynamicPoolService {
        if (!DynamicPoolService.instance) {
            DynamicPoolService.instance = new DynamicPoolService()
        }
        return DynamicPoolService.instance
    }

    /**
     * 載入動態池數據
     */
    public async loadDynamicPool(): Promise<void> {
        // 避免重複載入
        if (this.loadPromise) {
            return this.loadPromise
        }

        this.loadPromise = this._loadPoolData()
        return this.loadPromise
    }

    private async _loadPoolData(): Promise<void> {
        try {
            // 從後端API載入動態池數據
            const response = await simworldFetch('/satellite/dynamic-pool')
            
            if (!response.ok) {
                // 如果API不存在，嘗試直接載入文件
                const fileResponse = await fetch(this.config.poolDataPath)
                if (fileResponse.ok) {
                    const data = await fileResponse.json()
                    this.poolData = data.dynamic_satellite_pool
                } else {
                    throw new Error('無法載入動態池數據')
                }
            } else {
                const data = await response.json()
                this.poolData = data.dynamic_satellite_pool
            }
            
        } catch (error) {
            console.error('❌ 載入動態池數據失敗:', error)
            // Fallback: 設置為不使用優化池
            this.config.useOptimizedPool = false
            this.poolData = null
        }
    }

    /**
     * 檢查是否應該使用優化池
     */
    public shouldUseOptimizedPool(): boolean {
        return this.config.useOptimizedPool && this.poolData !== null
    }

    /**
     * 切換池模式（優化池 vs 全量數據）
     */
    public togglePoolMode(useOptimized: boolean): void {
        this.config.useOptimizedPool = useOptimized
    }

    /**
     * 過濾衛星數據，只保留動態池中的衛星
     */
    public filterSatellitesByPool<T extends { id?: string, satellite_id?: string }>(
        satellites: T[]
    ): T[] {
        if (!this.shouldUseOptimizedPool() || !this.poolData) {
            // 不使用優化池，返回全部數據
            return satellites
        }

        // 創建池中衛星ID的Set以提高查詢效率
        const poolIds = new Set([
            ...this.poolData.starlink_satellites,
            ...this.poolData.oneweb_satellites
        ])

        // 過濾衛星列表 - 支援多種ID字段格式
        const filtered = satellites.filter(sat => {
            // 嘗試不同的ID字段：id, satellite_id, norad_id, name等
            const possibleIds = [
                sat.id,
                sat.satellite_id,
                sat.norad_id,
                // 從名稱提取衛星ID（如：STARLINK-34604 -> starlink_07937）
                sat.name?.toLowerCase().replace(/[^a-z0-9]/g, '_')
            ].filter(Boolean)
            
            // 檢查是否有任何ID在池中
            return possibleIds.some(id => poolIds.has(id))
        })

        return filtered
    }

    /**
     * 獲取池中的衛星ID列表
     */
    public getPoolSatelliteIds(): string[] {
        if (!this.poolData) {
            return []
        }
        return [
            ...this.poolData.starlink_satellites,
            ...this.poolData.oneweb_satellites
        ]
    }

    /**
     * 獲取池的覆蓋評分
     */
    public getCoverageMetrics(): { starlink: number, oneweb: number } | null {
        if (!this.poolData?.coverage_metrics) {
            return null
        }
        return {
            starlink: this.poolData.coverage_metrics.starlink_coverage_score,
            oneweb: this.poolData.coverage_metrics.oneweb_coverage_score
        }
    }

    /**
     * 檢查特定衛星是否在池中
     */
    public isSatelliteInPool(satelliteId: string): boolean {
        if (!this.poolData) {
            return true  // 如果沒有池數據，默認所有衛星都"在池中"
        }
        return this.poolData.starlink_satellites.includes(satelliteId) ||
               this.poolData.oneweb_satellites.includes(satelliteId)
    }

    /**
     * 獲取池統計信息
     */
    public getPoolStatistics() {
        if (!this.poolData) {
            return {
                mode: 'full',
                total: 0,
                starlink: 0,
                oneweb: 0,
                coverage: null
            }
        }

        return {
            mode: this.config.useOptimizedPool ? 'optimized' : 'full',
            total: this.poolData.total_selected,
            starlink: this.poolData.starlink_satellites.length,
            oneweb: this.poolData.oneweb_satellites.length,
            coverage: this.getCoverageMetrics()
        }
    }
}

// 導出單例實例
export const dynamicPoolService = DynamicPoolService.getInstance()

// 🎯 移除自動載入，改由SatelliteDataContext主動調用
// 這避免模組初始化時的無限循環和API未準備問題