/**
 * 預計算軌道服務 - Phase 1 NetStack 整合
 * 
 * 整合 NetStack API 的預計算軌道數據，替代前端的即時計算。
 * 支援 60 倍加速動畫和距離縮放優化。
 */

import type {
  OrbitData,
  OptimalTimeWindow,
  DisplayData,
  SatelliteTrajectory,
  HandoverEvent,
  ObserverLocation
} from '../types/satellite';
import { netstackFetch } from '../config/api-config';

export interface PrecomputedOrbitConfig {
  location: string;
  constellation: 'starlink' | 'oneweb';
  elevationThreshold?: number;
  environment: 'open_area' | 'urban' | 'mountainous';
  useLayeredThresholds: boolean;
}

export interface AnimationConfig {
  acceleration: number;      // 動畫加速倍數 (預設 60)
  distanceScale: number;     // 距離縮放比例 (預設 0.1)
  fps: number;              // 動畫幀率 (預設 30)
  smoothing: boolean;       // 軌跡平滑化
}

export class PrecomputedOrbitService {
  private cache: Map<string, any> = new Map();
  private cacheTTL: number = 10 * 60 * 1000; // 10 分鐘快取

  /**
   * 載入預計算軌道數據
   */
  async loadPrecomputedOrbitData(config: PrecomputedOrbitConfig): Promise<OrbitData> {
    const cacheKey = `orbit_${JSON.stringify(config)}`;
    
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTTL) {
        console.log('🚀 使用快取的軌道數據');
        return cached.data;
      }
    }

    try {
      const params = new URLSearchParams({
        constellation: config.constellation,
        environment: config.environment,
        use_layered_thresholds: config.useLayeredThresholds.toString()
      });

      if (config.elevationThreshold) {
        params.append('elevation_threshold', config.elevationThreshold.toString());
      }

      const response = await netstackFetch(
        `/api/v1/satellites/precomputed/${config.location}?${params}`
      );

      if (!response.ok) {
        throw new Error(`NetStack API 錯誤: ${response.status}`);
      }

      const data = await response.json();
      
      // 快取結果
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      console.log(`✅ 成功載入 ${config.location} 預計算軌道數據:`, {
        satelliteCount: data.computation_metadata?.filtered_satellites_count || 0,
        processingTime: data.total_processing_time_ms || 0
      });

      return data;

    } catch (error) {
      console.error('❌ 載入預計算軌道數據失敗:', error);
      throw new Error(`無法載入預計算軌道數據: ${error}`);
    }
  }

  /**
   * 獲取最佳時間窗口
   */
  async loadOptimalTimeWindow(
    location: string = 'ntpu',
    constellation: string = 'starlink',
    windowHours: number = 6
  ): Promise<OptimalTimeWindow> {
    const cacheKey = `window_${location}_${constellation}_${windowHours}`;
    
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTTL) {
        return cached.data;
      }
    }

    try {
      const response = await netstackFetch(
        `/optimal-window/${location}?constellation=${constellation}&window_hours=${windowHours}`
      );

      if (!response.ok) {
        throw new Error(`NetStack API 錯誤: ${response.status}`);
      }

      const data = await response.json();
      
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      console.log(`✅ 成功載入最佳時間窗口 (${windowHours}小時):`, {
        qualityScore: data.quality_score || 0,
        trajectoryCount: data.satellite_trajectories?.length || 0
      });

      return data;

    } catch (error) {
      console.error('❌ 載入最佳時間窗口失敗:', error);
      throw new Error(`無法載入最佳時間窗口: ${error}`);
    }
  }

  /**
   * 獲取展示優化數據 (支援 60 倍加速動畫)
   */
  async getDisplayOptimizedData(
    location: string = 'ntpu',
    animationConfig: Partial<AnimationConfig> = {}
  ): Promise<DisplayData> {
    const config: AnimationConfig = {
      acceleration: 60,
      distanceScale: 0.1,
      fps: 30,
      smoothing: true,
      ...animationConfig
    };

    const cacheKey = `display_${location}_${JSON.stringify(config)}`;
    
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTTL) {
        return cached.data;
      }
    }

    try {
      const response = await netstackFetch(
        `/display-data/${location}?acceleration=${config.acceleration}&distance_scale=${config.distanceScale}`
      );

      if (!response.ok) {
        throw new Error(`NetStack API 錯誤: ${response.status}`);
      }

      const data = await response.json();
      
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      console.log(`✅ 成功載入展示優化數據:`, {
        acceleration: config.acceleration,
        keyframes: data.animation_keyframes?.length || 0,
        trajectories: data.trajectory_data?.length || 0
      });

      return data;

    } catch (error) {
      console.error('❌ 載入展示優化數據失敗:', error);
      throw new Error(`無法載入展示優化數據: ${error}`);
    }
  }

  /**
   * 獲取支援的觀測位置列表
   */
  async getSupportedLocations(): Promise<ObserverLocation[]> {
    const cacheKey = 'supported_locations';
    
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTTL) {
        return cached.data.locations;
      }
    }

    try {
      const response = await netstackFetch(`/locations`);

      if (!response.ok) {
        throw new Error(`NetStack API 錯誤: ${response.status}`);
      }

      const data = await response.json();
      
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      console.log(`✅ 成功載入支援位置列表: ${data.total_locations} 個位置`);

      return data.locations;

    } catch (error) {
      console.error('❌ 載入支援位置失敗:', error);
      throw new Error(`無法載入支援位置: ${error}`);
    }
  }

  /**
   * 檢查 NetStack 預計算數據健康狀態
   */
  async checkPrecomputedHealth(): Promise<boolean> {
    try {
      const response = await netstackFetch(`/health/precomputed`);
      
      if (!response.ok) {
        console.warn('⚠️ NetStack 預計算健康檢查失敗');
        return false;
      }

      const health = await response.json();
      const isHealthy = health.overall_status === 'healthy';
      
      console.log(`${isHealthy ? '✅' : '❌'} NetStack 預計算狀態: ${health.overall_status}`);
      
      return isHealthy;

    } catch (error) {
      console.error('❌ 預計算健康檢查異常:', error);
      return false;
    }
  }

  /**
   * 清除快取
   */
  clearCache(): void {
    this.cache.clear();
    console.log('🗑️ 預計算軌道服務快取已清除');
  }

  /**
   * 設定快取 TTL
   */
  setCacheTTL(ttlMs: number): void {
    this.cacheTTL = ttlMs;
    console.log(`⏰ 快取 TTL 設定為 ${ttlMs / 1000} 秒`);
  }
}

// 創建全域單例
export const precomputedOrbitService = new PrecomputedOrbitService();

// 便利函數
export async function loadNTPUSatelliteData(
  constellation: 'starlink' | 'oneweb' = 'starlink'
): Promise<OrbitData> {
  return precomputedOrbitService.loadPrecomputedOrbitData({
    location: 'ntpu',
    constellation,
    environment: 'urban',
    useLayeredThresholds: true
  });
}

export async function loadOptimal6HourWindow(): Promise<OptimalTimeWindow> {
  return precomputedOrbitService.loadOptimalTimeWindow('ntpu', 'starlink', 6);
}

export async function loadDisplayAnimationData(
  acceleration: number = 60
): Promise<DisplayData> {
  return precomputedOrbitService.getDisplayOptimizedData('ntpu', {
    acceleration,
    distanceScale: 0.1
  });
}