/**
 * LEO 衛星系統配置 - 精簡版
 * 基於真實 LEO 軌道參數和 3GPP NTN 標準
 */

export const SATELLITE_CONFIG = {
  // === 核心顯示參數 ===
  VISIBLE_COUNT: 30,                // 台灣地區可見衛星數量
  MIN_ELEVATION: 10,                // 最小仰角（3GPP NTN 標準）
  
  // === 時間控制（統一管理）===
  TIME_MULTIPLIER: 1,               // 統一時間倍數（1 = 真實速度）
  UPDATE_INTERVAL: 1000,            // 位置更新間隔（毫秒）
  ANIMATION_FPS: 60,                // 動畫幀率
  
  // === LEO 軌道參數 ===
  ALTITUDE_KM: 550,                 // 標準 LEO 軌道高度
  INCLINATION_DEG: 53.0,            // 標準軌道傾角
  ORBITAL_PERIOD_MIN: 96,           // LEO 軌道週期
  
  // === 切換參數（3GPP NTN）===
  HANDOVER_ELEVATION_THRESHOLD: 25, // 切換觸發仰角
  HANDOVER_HYSTERESIS: 2,           // 切換滯後
  SIGNAL_FADE_MARGIN: 3,            // 信號衰落裕度
  
  // === 視覺化參數 ===
  SAT_SCALE: 3,                     // 衛星模型大小
  SHOW_ORBIT_TRAILS: true,          // 顯示軌道
  TRAIL_LENGTH: 10,                 // 軌跡長度（分鐘）
} as const;

/**
 * 模擬模式配置 - 簡化版
 */
export const SIMULATION_MODE = {
  REAL_TIME: 'real_time',           // 真實時間模式
  DEMO: 'demo',                     // 演示模式
  ANALYSIS: 'analysis',             // 分析模式
} as const;

export type SimulationMode = typeof SIMULATION_MODE[keyof typeof SIMULATION_MODE];

/**
 * 獲取模式時間倍數
 */
export function getTimeMultiplier(mode: SimulationMode): number {
  switch (mode) {
    case SIMULATION_MODE.REAL_TIME:
      return SATELLITE_CONFIG.TIME_MULTIPLIER;
    case SIMULATION_MODE.DEMO:
      return SATELLITE_CONFIG.TIME_MULTIPLIER * 10; // 演示模式10倍速
    case SIMULATION_MODE.ANALYSIS:
      return 0; // 暫停模式
    default:
      return SATELLITE_CONFIG.TIME_MULTIPLIER;
  }
}

/**
 * 衛星星座配置 - 精簡版
 */
export const CONSTELLATION_CONFIG = {
  // 支援的星座類型
  SUPPORTED_TYPES: ['STARLINK', 'KUIPER'] as const,
  
  // NORAD ID 範圍
  STARLINK_ID_RANGE: [44713, 70000],
  KUIPER_ID_RANGE: [63724, 63750],
} as const;

/**
 * 動態配置支援 - 運行時調整關鍵參數
 */
export const DYNAMIC_CONFIG = {
  // 可動態調整的參數
  adjustableParams: [
    'TIME_MULTIPLIER',
    'VISIBLE_COUNT', 
    'HANDOVER_ELEVATION_THRESHOLD',
    'TRAIL_LENGTH'
  ] as const,
  
  // 參數範圍限制
  paramLimits: {
    TIME_MULTIPLIER: [0.1, 100],
    VISIBLE_COUNT: [5, 100],
    HANDOVER_ELEVATION_THRESHOLD: [10, 45],
    TRAIL_LENGTH: [1, 30]
  }
} as const;