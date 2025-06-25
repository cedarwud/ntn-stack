/**
 * LEO衛星換手管理系統配置常量
 */

export const HANDOVER_CONFIG = {
  // 時間相關配置
  TIMING: {
    DEFAULT_DELTA_T_SECONDS: 5,        // 預設時間間隔（秒）
    MIN_DELTA_T_SECONDS: 3,            // 最小時間間隔（秒）
    MAX_DELTA_T_SECONDS: 30,           // 最大時間間隔（秒）
    UPDATE_INTERVAL_MS: 100,           // UI更新間隔（毫秒）
    ALGORITHM_CHECK_INTERVAL_MS: 1000, // 演算法檢查間隔（毫秒）
  },

  // 換手決策閾值
  HANDOVER_THRESHOLDS: {
    MIN_ELEVATION_DEGREES: 20,         // 最低仰角閾值（度）
    SIGNAL_DROP_THRESHOLD: -0.8,       // 信號下降閾值
    ORBITAL_POSITION_THRESHOLD: {      // 軌道位置閾值
      LEAVE_START: 340,                // 離開視野開始角度
      LEAVE_END: 20,                   // 離開視野結束角度
      MIN_ELEVATION_FOR_ORBITAL: 25,   // 軌道判斷最低仰角
    },
    TIME_BASED_CYCLE_MS: 45000,        // 時間基礎信號週期（毫秒）
  },

  // 防重複換手配置
  HANDOVER_HISTORY: {
    DEMO_COOLDOWN_MS: 90000,           // 演示模式冷卻期（毫秒）
    REAL_COOLDOWN_MS: 120000,          // 真實模式冷卻期（毫秒）
    MAX_HISTORY_RECORDS: 100,          // 最大歷史記錄數
  },

  // Binary Search 配置
  BINARY_SEARCH: {
    MIN_PRECISION_MS: 10,              // 最小精度（毫秒）
    MAX_ITERATIONS: 10,                // 最大迭代次數
    PRECISION_LEVELS: [0.01, 0.05, 0.1, 0.2, 0.4], // 精度等級（秒）
    TIME_VARIATION_INTERVAL_MS: 12000, // 時間變化間隔（毫秒）
  },

  // 信號品質計算
  SIGNAL_QUALITY: {
    EXCELLENT_THRESHOLD_DBM: -70,      // 優秀信號閾值
    GOOD_THRESHOLD_DBM: -85,           // 良好信號閾值
    FAIR_THRESHOLD_DBM: -100,          // 一般信號閾值
    SIGNAL_RANGE: {                    // 信號強度範圍
      MIN: -120,                       // 最低可用信號
      MAX: -60,                        // 最強信號
    },
  },

  // 動畫和視覺效果
  ANIMATION: {
    HANDOVER_DURATION_MS: {            // 換手動畫時長範圍
      MIN: 3500,
      MAX: 6500,
    },
    SUCCESS_RATE: 0.9,                 // 換手成功率
    PROGRESS_UPDATE_INTERVAL_MS: 100,  // 進度更新間隔
    STATUS_RESET_DELAY_MS: 2000,       // 狀態重置延遲
  },

  // API 配置
  API: {
    REQUEST_TIMEOUT_MS: 5000,          // API請求超時時間
    RETRY_ATTEMPTS: 3,                 // 重試次數
    RETRY_DELAY_MS: 1000,              // 重試延遲
    FALLBACK_SATELLITES_COUNT: 18,     // 後備衛星數量
  },

  // 衛星選擇策略
  SATELLITE_SELECTION: {
    MAX_FRONT_SATELLITES: 6,           // 前置衛星最大數量
    ADJACENT_SELECTION_PROBABILITY: 0.6, // 相鄰衛星選擇機率
    SATELLITE_ID_RANGE: {              // 衛星ID範圍
      BASE: 1000,
      RANGE: 500,
    },
  },

  // 精度和準確度
  ACCURACY: {
    DEFAULT_CONFIDENCE: 0.95,          // 預設置信度
    MIN_CONFIDENCE: 0.85,              // 最低置信度
    MAX_CONFIDENCE: 0.99,              // 最高置信度
    CONFIDENCE_VARIANCE: 0.04,         // 置信度變異範圍
  }
} as const

/**
 * 獲取換手冷卻期配置
 */
export const getHandoverCooldownPeriod = (mode: 'demo' | 'real'): number => {
  return mode === 'demo' 
    ? HANDOVER_CONFIG.HANDOVER_HISTORY.DEMO_COOLDOWN_MS
    : HANDOVER_CONFIG.HANDOVER_HISTORY.REAL_COOLDOWN_MS
}

/**
 * 獲取信號品質等級
 */
export const getSignalQualityLevel = (signalStrength: number): 'excellent' | 'good' | 'fair' | 'poor' => {
  const { SIGNAL_QUALITY } = HANDOVER_CONFIG
  
  if (signalStrength >= SIGNAL_QUALITY.EXCELLENT_THRESHOLD_DBM) return 'excellent'
  if (signalStrength >= SIGNAL_QUALITY.GOOD_THRESHOLD_DBM) return 'good'
  if (signalStrength >= SIGNAL_QUALITY.FAIR_THRESHOLD_DBM) return 'fair'
  return 'poor'
}

/**
 * 獲取信號品質百分比
 */
export const getSignalQualityPercentage = (signalStrength: number): number => {
  const { SIGNAL_QUALITY } = HANDOVER_CONFIG
  const { MIN, MAX } = SIGNAL_QUALITY.SIGNAL_RANGE
  
  return Math.max(0, Math.min(100, ((signalStrength - MIN) / (MAX - MIN)) * 100))
}

/**
 * 獲取Binary Search精度等級
 */
export const getBinarySearchPrecision = (timeStamp: number): number => {
  const { BINARY_SEARCH } = HANDOVER_CONFIG
  const timeVariation = Math.floor(timeStamp / BINARY_SEARCH.TIME_VARIATION_INTERVAL_MS) % BINARY_SEARCH.PRECISION_LEVELS.length
  return BINARY_SEARCH.PRECISION_LEVELS[timeVariation]
}