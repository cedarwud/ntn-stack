import { ApiRoutes } from '../../config/apiRoutes'

// 衛星渲染和轉換設定
export const GLB_SCENE_SIZE = 600 // 模型場景大小
export const MIN_SAT_HEIGHT = 10 // 最小衛星高度 (Y值)
export const MAX_SAT_HEIGHT = 150 // 最大衛星高度 (Y值)
export const MAX_VISIBLE_SATELLITES = 8 // 最多顯示衛星數量，優化效能
export const PASS_DURATION_MIN = 60 // 最短通過時間(秒)
export const PASS_DURATION_MAX = 180 // 最長通過時間(秒)
export const SAT_SCALE = 3 // 衛星模型縮放比例
export const SAT_MODEL_URL = ApiRoutes.simulations.getModel('sat') // 衛星模型 URL 