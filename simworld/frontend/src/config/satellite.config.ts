/**
 * 衛星顯示和移動模擬配置
 * 支援 Starlink + Kuiper 衛星星座的通用參數設定
 */

export const SATELLITE_CONFIG = {
  // === 基本顯示參數 ===
  VISIBLE_COUNT: 50,                // 🌍 大幅增加可見衛星數量以獲得全球範圍數據
  MIN_ELEVATION: 0,                 // 🌍 使用標準仰角（地平線以上）以包含全球範圍衛星
  
  // === 移動模擬參數 ===
  REAL_TIME_MULTIPLIER: 1,          // 實時速度倍數（1 = 真實速度）
  HANDOVER_DEMO_MULTIPLIER: 1,     // 換手演示速度倍數（1倍真實速度，便於演示）
  ANIMATION_SPEED: 10,              // 動畫速度倍數（可調整）
  
  // === 分離的速度控制 ===
  SATELLITE_MOVEMENT_SPEED: 2,      // 衛星3D移動速度倍數（獨立控制）
  HANDOVER_TIMING_SPEED: 2,        // 換手時機和演示速度倍數（獨立控制）
  INTERPOLATION_SMOOTHNESS: 10,     // 插值平滑度（每秒幀數）
  
  // === 軌跡更新參數 ===
  POSITION_UPDATE_INTERVAL: 1000,   // 位置更新間隔（毫秒）
  TRAJECTORY_PREDICTION_TIME: 6000, // 軌跡預測時間（秒，100分鐘，涵蓋完整軌道週期）
  ORBIT_CALCULATION_STEP: 30,       // 軌道計算步長（秒，提高精度）
  ANIMATION_FRAME_RATE: 60,         // 動畫幀率（FPS）
  
  // === 視覺化參數 ===
  SAT_SCALE: 3,                     // 衛星模型縮放比例
  ORBIT_LINE_SEGMENTS: 32,          // 軌道線段數
  SHOW_ORBIT_TRAILS: true,          // 顯示軌道軌跡
  TRAIL_LENGTH: 10,                 // 軌跡長度（分鐘）
  
  // === 衛星星座軌道參數 ===
  STARLINK_ALTITUDE_KM: 550,        // Starlink 衛星軌道高度
  STARLINK_INCLINATION_DEG: 53.0,   // Starlink 軌道傾角
  KUIPER_ALTITUDE_KM: 590,          // Kuiper 衛星軌道高度 
  KUIPER_INCLINATION_DEG: 51.9,     // Kuiper 軌道傾角
  ORBITAL_PERIOD_MIN: 96,           // LEO 軌道週期（分鐘）
  
  // === 換手相關參數 ===
  HANDOVER_ELEVATION_THRESHOLD: 25, // 換手觸發仰角閾值（度）
  HANDOVER_HYSTERESIS: 2,           // 換手滯後角度（度）
  SIGNAL_FADE_MARGIN: 3,            // 信號衰落裕度（dB）
  
  // === 邊界設定 ===  
  VISIBILITY_BOUNDARY: {
    MIN_ELEVATION_DEG: 0,           // 🌍 標準仰角（地平線以上）以支持全球視野
    MAX_ELEVATION_DEG: 90,          // 衛星消失的最高仰角（度）
    AZIMUTH_RANGE_DEG: 360,         // 方位角範圍（度）
    MAX_DISTANCE_KM: 3000,          // 🌍 增加最大可見距離以包含更多衛星
  },
  
} as const;

/**
 * 運行時模式配置
 */
export const SIMULATION_MODE = {
  // 模擬模式
  REAL_TIME: 'real_time',           // 真實時間模式
  DEMO: 'demo',                     // 演示模式（加速）
  ANALYSIS: 'analysis',             // 分析模式（可暫停）
} as const;

export type SimulationMode = typeof SIMULATION_MODE[keyof typeof SIMULATION_MODE];

/**
 * 獲取當前模式的時間倍數
 */
export function getTimeMultiplier(mode: SimulationMode): number {
  switch (mode) {
    case SIMULATION_MODE.REAL_TIME:
      return SATELLITE_CONFIG.REAL_TIME_MULTIPLIER;
    case SIMULATION_MODE.DEMO:
      return SATELLITE_CONFIG.HANDOVER_DEMO_MULTIPLIER;
    case SIMULATION_MODE.ANALYSIS:
      return 0; // 可暫停
    default:
      return SATELLITE_CONFIG.REAL_TIME_MULTIPLIER;
  }
}

/**
 * 衛星星座標識符配置
 * 用於識別和追蹤特定的 Starlink 和 Kuiper 衛星
 */
export const CONSTELLATION_SATELLITES = {
  // Starlink 衛星 NORAD ID 範圍
  STARLINK_START: 44713,
  STARLINK_END: 70000,
  
  // Kuiper 衛星 NORAD ID 範圍
  KUIPER_START: 63724,
  KUIPER_END: 63750,
  
  // 支援的星座類型
  SUPPORTED_CONSTELLATIONS: ['STARLINK', 'KUIPER'] as const,
} as const;

/**
 * 真實軌跡調整參數
 * 用於在不偏離真實軌跡太遠的情況下，優化換手演示效果
 */
export const TRAJECTORY_ADJUSTMENT = {
  // 是否啟用軌跡調整
  ENABLE_ADJUSTMENT: true,
  
  // 最大位置偏移（公里）
  MAX_POSITION_OFFSET_KM: 50,
  
  // 最大時間偏移（秒）
  MAX_TIME_OFFSET_SEC: 30,
  
  // 換手場景優化
  OPTIMIZE_FOR_HANDOVER: true,
  
  // 確保最小換手間隔（秒）- 修正：基於真實 LEO 軌道週期調整
  MIN_HANDOVER_INTERVAL_SEC: 300, // 5分鐘，考慮真實 90分鐘軌道週期
} as const;