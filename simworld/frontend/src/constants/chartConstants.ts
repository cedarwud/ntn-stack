/**
 * 圖表相關常數
 * 
 * 定義圖表中使用的顏色、標籤、API 端點等常數
 * 確保整個應用程式的一致性
 */

/**
 * 圖表顏色配置
 */
export const CHART_COLORS = {
    // 主要顏色
    PRIMARY: 'rgba(75, 192, 192, 0.8)',
    PRIMARY_BORDER: 'rgba(75, 192, 192, 1)',
    
    // 次要顏色
    SECONDARY: 'rgba(255, 99, 132, 0.8)',
    SECONDARY_BORDER: 'rgba(255, 99, 132, 1)',
    
    // 成功/警告/錯誤
    SUCCESS: 'rgba(34, 197, 94, 0.8)',
    SUCCESS_BORDER: 'rgba(34, 197, 94, 1)',
    WARNING: 'rgba(251, 191, 36, 0.8)',
    WARNING_BORDER: 'rgba(251, 191, 36, 1)',
    DANGER: 'rgba(239, 68, 68, 0.8)',
    DANGER_BORDER: 'rgba(239, 68, 68, 1)',
    
    // 系統指標顏色
    CPU: 'rgba(59, 130, 246, 0.8)',
    CPU_BORDER: 'rgba(59, 130, 246, 1)',
    MEMORY: 'rgba(168, 85, 247, 0.8)',
    MEMORY_BORDER: 'rgba(168, 85, 247, 1)',
    NETWORK: 'rgba(34, 197, 94, 0.8)',
    NETWORK_BORDER: 'rgba(34, 197, 94, 1)',
    GPU: 'rgba(249, 115, 22, 0.8)',
    GPU_BORDER: 'rgba(249, 115, 22, 1)',
    
    // 通信品質顏色
    EXCELLENT: 'rgba(34, 197, 94, 0.8)',
    GOOD: 'rgba(59, 130, 246, 0.8)',
    FAIR: 'rgba(251, 191, 36, 0.8)',
    POOR: 'rgba(239, 68, 68, 0.8)',
    
    // 透明度變化
    TRANSPARENT: 'rgba(255, 255, 255, 0.1)',
    SEMI_TRANSPARENT: 'rgba(255, 255, 255, 0.5)',
    OPAQUE: 'rgba(255, 255, 255, 0.9)',
    
    // 漸層顏色集合
    GRADIENT_SET: [
        'rgba(255, 99, 132, 0.8)',
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 205, 86, 0.8)',
        'rgba(75, 192, 192, 0.8)',
        'rgba(153, 102, 255, 0.8)',
        'rgba(255, 159, 64, 0.8)',
        'rgba(199, 199, 199, 0.8)',
        'rgba(83, 102, 255, 0.8)',
    ],
    
    GRADIENT_SET_BORDERS: [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 205, 86, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)',
        'rgba(255, 159, 64, 1)',
        'rgba(199, 199, 199, 1)',
        'rgba(83, 102, 255, 1)',
    ],
} as const

/**
 * 圖表標籤
 */
export const CHART_LABELS = {
    // 系統指標
    CPU_USAGE: 'CPU 使用率 (%)',
    MEMORY_USAGE: '記憶體使用率 (%)',
    GPU_USAGE: 'GPU 使用率 (%)',
    NETWORK_LATENCY: '網路延遲 (ms)',
    
    // 換手指標
    HANDOVER_DELAY: '換手延遲 (ms)',
    HANDOVER_SUCCESS_RATE: '換手成功率 (%)',
    HANDOVER_FAILURE_RATE: '換手失敗率 (%)',
    HANDOVER_COUNT: '換手次數',
    
    // 通信品質
    SIGNAL_STRENGTH: '信號強度 (dBm)',
    SINR: 'SINR (dB)',
    THROUGHPUT: '吞吐量 (Mbps)',
    PACKET_LOSS: '封包丟失率 (%)',
    
    // 訓練指標
    TRAINING_LOSS: '訓練損失',
    VALIDATION_ACCURACY: '驗證準確率 (%)',
    REWARD: '獎勵值',
    EPISODES: '訓練回合',
    
    // 時間軸
    TIME_SECONDS: '時間 (秒)',
    TIME_MINUTES: '時間 (分鐘)',
    TIME_HOURS: '時間 (小時)',
    TIMESTAMP: '時間戳記',
    
    // 其他
    COUNT: '數量',
    PERCENTAGE: '百分比 (%)',
    VALUE: '數值',
    FREQUENCY: '頻率',
} as const

/**
 * API 端點
 */
export const API_ENDPOINTS = {
    // 系統指標
    SYSTEM_METRICS: '/api/v1/system/metrics',
    SYSTEM_HEALTH: '/api/v1/system/health',
    
    // 換手相關
    HANDOVER_TEST: '/api/v1/handover/test',
    HANDOVER_METRICS: '/api/v1/handover/metrics',
    HANDOVER_PERFORMANCE: '/api/v1/handover/performance',
    
    // 訓練資料
    TRAINING_METRICS: '/api/v1/training/metrics',
    RL_METRICS: '/api/v1/rl/metrics',
    
    // 策略資料
    STRATEGY_METRICS: '/api/v1/strategy/metrics',
    ALGORITHM_PERFORMANCE: '/api/v1/algorithm/performance',
    
    // 衛星資料
    SATELLITE_DATA: '/api/v1/satellite/data',
    SATELLITE_VISIBILITY: '/api/v1/satellite/visibility',
    
    // 通信品質
    QOE_METRICS: '/api/v1/qoe/metrics',
    INTERFERENCE_DATA: '/api/v1/interference/data',
    
    // 複雜性分析
    COMPLEXITY_ANALYSIS: '/api/v1/analysis/complexity',
    PERFORMANCE_ANALYSIS: '/api/v1/analysis/performance',
} as const

/**
 * 圖表更新間隔 (毫秒)
 */
export const UPDATE_INTERVALS = {
    REAL_TIME: 1000,      // 1 秒
    FAST: 2000,           // 2 秒
    NORMAL: 5000,         // 5 秒
    SLOW: 15000,          // 15 秒
    VERY_SLOW: 30000,     // 30 秒
} as const

/**
 * 圖表設定
 */
export const CHART_SETTINGS = {
    ANIMATION_DURATION: 750,
    RESPONSIVE: true,
    MAINTAIN_ASPECT_RATIO: false,
    
    // 預設圖表尺寸
    DEFAULT_HEIGHT: 400,
    DEFAULT_WIDTH: 600,
    
    // 圖表元素大小
    POINT_RADIUS: 4,
    POINT_HOVER_RADIUS: 6,
    LINE_TENSION: 0.3,
    BORDER_WIDTH: 2,
    
    // 字體大小
    TITLE_FONT_SIZE: 20,
    LEGEND_FONT_SIZE: 16,
    TICK_FONT_SIZE: 14,
    TOOLTIP_FONT_SIZE: 15,
} as const

/**
 * 資料點限制
 */
export const DATA_LIMITS = {
    MAX_TIME_SERIES_POINTS: 100,
    MAX_REALTIME_POINTS: 50,
    MAX_HISTORY_POINTS: 1000,
} as const