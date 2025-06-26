import { ApiRoutes } from '../../config/apiRoutes'

// === 衛星渲染和轉換設定 ===
export const GLB_SCENE_SIZE = 1200 // 模型場景大小
export const MIN_SAT_HEIGHT = 0 // 最小衛星高度 (Y值)
export const MAX_SAT_HEIGHT = 600 // 最大衛星高度 (Y值)
export const MAX_VISIBLE_SATELLITES = 100 // 最多顯示衛星數量，優化效能
export const PASS_DURATION_MIN = 120 // 最短通過時間(秒)
export const PASS_DURATION_MAX = 180 // 最長通過時間(秒)
export const SAT_SCALE = 3 // 衛星模型縮放比例
export const SAT_MODEL_URL = ApiRoutes.simulations.getModel('sat') // 衛星模型 URL 

// === 3D場景邊界設定 ===
export const SCENE_BOUNDARY = {
  // 衛星位置範圍
  MAX_RENDER_DISTANCE: 900,         // 最大渲染距離（增加以適應更多衛星）
  MIN_RENDER_DISTANCE: 150,         // 最小渲染距離
  HEIGHT_SCALE_FACTOR: 1.8,         // 高度縮放因子（增加高度變化）
  
  // 可見性邊界
  VISIBILITY_THRESHOLD: {
    MIN_ELEVATION: 3,               // 最低仰角閾值（度）- 降低以顯示更多衛星
    MAX_ELEVATION: 90,              // 最高仰角閾值（度）
    HORIZON_BUFFER: 2,              // 地平線緩衝區（度）
  },
  
  // 場景邊界
  SCENE_LIMITS: {
    X_MAX: 1200,                    // X軸最大值（擴大場景）
    X_MIN: -1200,                   // X軸最小值
    Y_MAX: 700,                     // Y軸最大值（高度）
    Y_MIN: -80,                     // Y軸最小值（地平線以下）
    Z_MAX: 1200,                    // Z軸最大值
    Z_MIN: -1200,                   // Z軸最小值
  }
} as const 