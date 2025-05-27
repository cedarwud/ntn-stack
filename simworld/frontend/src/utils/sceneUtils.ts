/**
 * 場景相關的工具函數
 */

// 場景名稱映射：前端路由參數 -> 後端場景目錄名稱
export const SCENE_MAPPING = {
    nycu: 'NYCU',
    lotus: 'Lotus',
    ntpu: 'NTPU',
    nanliao: 'Nanliao',
} as const

// 場景顯示名稱映射
export const SCENE_DISPLAY_NAMES = {
    nycu: '陽明交通大學',
    lotus: '荷花池',
    ntpu: '臺北大學',
    nanliao: '南寮漁港',
} as const

// 場景座標轉換參數映射
export const SCENE_COORDINATE_TRANSFORMS = {
    nycu: {
        offsetX: 865,
        offsetY: 640,
        scale: 1.0,
    },
    lotus: {
        offsetX: 1200,
        offsetY: 900,
        scale: 1.0,
    },
    ntpu: {
        offsetX: 900,
        offsetY: 620,
        scale: 1.0,
    },
    nanliao: {
        offsetX: 920,
        offsetY: 600,
        scale: 1.0,
    },
} as const

/**
 * 將前端路由參數轉換為後端場景名稱
 * @param sceneParam 前端路由參數 (如 'nycu', 'lotus')
 * @returns 後端場景目錄名稱 (如 'NYCU', 'Lotus')
 */
export function getBackendSceneName(sceneParam: string): string {
    const normalizedParam = sceneParam.toLowerCase()
    return SCENE_MAPPING[normalizedParam as keyof typeof SCENE_MAPPING] || SCENE_MAPPING.nycu
}

/**
 * 獲取場景的顯示名稱
 * @param sceneParam 前端路由參數 (如 'nycu', 'lotus')
 * @returns 場景顯示名稱 (如 '陽明交通大學', '荷花池')
 */
export function getSceneDisplayName(sceneParam: string): string {
    const normalizedParam = sceneParam.toLowerCase()
    return SCENE_DISPLAY_NAMES[normalizedParam as keyof typeof SCENE_DISPLAY_NAMES] || SCENE_DISPLAY_NAMES.nycu
}

/**
 * 獲取場景的紋理檔案名稱
 * @param sceneParam 前端路由參數
 * @returns 紋理檔案名稱
 */
export function getSceneTextureName(sceneParam: string): string {
    const backendName = getBackendSceneName(sceneParam)
    
    // 根據不同場景返回對應的紋理檔案名稱
    switch (backendName) {
        case 'NYCU':
            return 'EXPORT_GOOGLE_SAT_WM.png'
        case 'Lotus':
            return 'EXPORT_GOOGLE_SAT_WM.png'  // 假設 Lotus 也使用相同的紋理檔案
        case 'NTPU':
            return 'EXPORT_GOOGLE_SAT_WM.png'  // 臺北大學使用相同的紋理檔案
        case 'Nanliao':
            return 'EXPORT_GOOGLE_SAT_WM.png'  // 南寮漁港使用相同的紋理檔案
        default:
            return 'EXPORT_GOOGLE_SAT_WM.png'
    }
}

/**
 * 獲取場景的座標轉換參數
 * @param sceneParam 前端路由參數
 * @returns 座標轉換參數
 */
export function getSceneCoordinateTransform(sceneParam: string): { offsetX: number; offsetY: number; scale: number } {
    const normalizedParam = sceneParam.toLowerCase()
    return SCENE_COORDINATE_TRANSFORMS[normalizedParam as keyof typeof SCENE_COORDINATE_TRANSFORMS] || SCENE_COORDINATE_TRANSFORMS.nycu
}

/**
 * 檢查場景參數是否有效
 * @param sceneParam 前端路由參數
 * @returns 是否為有效的場景參數
 */
export function isValidScene(sceneParam: string): boolean {
    const normalizedParam = sceneParam.toLowerCase()
    return normalizedParam in SCENE_MAPPING
} 