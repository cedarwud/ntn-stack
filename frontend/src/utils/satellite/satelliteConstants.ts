// 衛星渲染和轉換設定
export const GLB_SCENE_SIZE = 1500 // GLB 場景大小
export const MIN_SAT_HEIGHT = 0 // 衛星最小高度
export const MAX_SAT_HEIGHT = 300 // GLB 場景中衛星最大高度
export const MAX_VISIBLE_SATELLITES = 100 // 最大可見衛星數量，用於性能優化
export const PASS_DURATION_MIN = 60 // 衛星通過所需最短時間(秒)
export const PASS_DURATION_MAX = 300 // 衛星通過所需最長時間(秒)
export const SAT_SCALE = 3 // 衛星模型縮放比例
export const SAT_MODEL_URL = '/api/v1/sionna/models/sat' // 衛星模型 URL 