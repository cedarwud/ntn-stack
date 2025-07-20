/**
 * 測量事件圖表統一視圖模式定義
 * 實現簡易版/完整版模式切換的統一標準
 * 
 * 基於 Phase 3.1 UI/UX 統一改進計劃
 */

// 基本視圖模式類型
export type ViewMode = 'simple' | 'advanced'

// 參數顯示級別
export type ParameterLevel = 'basic' | 'standard' | 'expert'

// 技術細節顯示級別  
export type TechnicalDetailLevel = 'none' | 'minimal' | 'standard' | 'full'

// 統一視圖模式配置介面
export interface ViewModeConfig {
    mode: ViewMode
    
    // 參數面板配置
    parameters: {
        level: ParameterLevel
        showAdvancedParameters: boolean
        showExpertParameters: boolean
        showDebuggingInfo: boolean
        showStandardReferences: boolean
    }
    
    // 圖表配置
    chart: {
        showTechnicalDetails: boolean
        showThresholdLines: boolean
        showAnimations: boolean
        animationSpeed: 'slow' | 'normal' | 'fast'
        showDataTooltips: boolean
        showLegend: boolean
    }
    
    // 控制面板配置
    controls: {
        showAdvancedControls: boolean
        showSimulationControls: boolean
        showDataModeToggle: boolean
        showExportOptions: boolean
        enableTLEImport: boolean
    }
    
    // 教育和說明配置
    education: {
        showConceptExplanations: boolean
        showParameterDescriptions: boolean
        showPhysicalMeaning: boolean
        showApplicationScenarios: boolean
        interactiveGuidance: boolean
    }
    
    // 效能配置
    performance: {
        updateInterval: number // ms
        maxDataPoints: number
        enableRealTimeUpdates: boolean
        cachingEnabled: boolean
    }
}

// 預設的簡易版配置
export const SIMPLE_MODE_CONFIG: ViewModeConfig = {
    mode: 'simple',
    
    parameters: {
        level: 'basic',
        showAdvancedParameters: false,
        showExpertParameters: false,
        showDebuggingInfo: false,
        showStandardReferences: false
    },
    
    chart: {
        showTechnicalDetails: false,
        showThresholdLines: true,
        showAnimations: true,
        animationSpeed: 'normal',
        showDataTooltips: true,
        showLegend: true
    },
    
    controls: {
        showAdvancedControls: false,
        showSimulationControls: false,
        showDataModeToggle: false,
        showExportOptions: false,
        enableTLEImport: false
    },
    
    education: {
        showConceptExplanations: true,
        showParameterDescriptions: true,
        showPhysicalMeaning: true,
        showApplicationScenarios: true,
        interactiveGuidance: true
    },
    
    performance: {
        updateInterval: 3000, // 較慢的更新，減少複雜度
        maxDataPoints: 50,
        enableRealTimeUpdates: true,
        cachingEnabled: true
    }
}

// 預設的完整版配置
export const ADVANCED_MODE_CONFIG: ViewModeConfig = {
    mode: 'advanced',
    
    parameters: {
        level: 'expert',
        showAdvancedParameters: true,
        showExpertParameters: true,
        showDebuggingInfo: true,
        showStandardReferences: true
    },
    
    chart: {
        showTechnicalDetails: true,
        showThresholdLines: true,
        showAnimations: true,
        animationSpeed: 'fast',
        showDataTooltips: true,
        showLegend: true
    },
    
    controls: {
        showAdvancedControls: true,
        showSimulationControls: true,
        showDataModeToggle: true,
        showExportOptions: true,
        enableTLEImport: true
    },
    
    education: {
        showConceptExplanations: false, // 專家模式不需要基礎解釋
        showParameterDescriptions: true,
        showPhysicalMeaning: true,
        showApplicationScenarios: false,
        interactiveGuidance: false
    },
    
    performance: {
        updateInterval: 1000, // 更快的更新，專業用途
        maxDataPoints: 200,
        enableRealTimeUpdates: true,
        cachingEnabled: true
    }
}

// 事件特定的參數映射
export interface EventParameterMapping {
    [eventType: string]: {
        basic: string[]        // 簡易版顯示的參數
        standard: string[]     // 標準版顯示的參數
        expert: string[]       // 專家版顯示的參數
    }
}

// A4 事件參數映射
export const A4_PARAMETER_MAPPING: EventParameterMapping['A4'] = {
    basic: [
        'a4Threshold',           // A4門檻值
        'hysteresis',           // 遲滯值
        'currentTime'           // 當前時間
    ],
    standard: [
        'a4Threshold',
        'hysteresis', 
        'currentTime',
        'useRealData',          // 數據模式
        'uePosition',           // UE位置
        'neighbour_satellite_id' // 鄰居衛星
    ],
    expert: [
        'a4Threshold',
        'hysteresis',
        'currentTime',
        'useRealData',
        'uePosition',
        'neighbour_satellite_id',
        'time_to_trigger',      // 觸發時間
        'report_config_id',     // 報告配置
        'cell_individual_offset', // 細胞偏移
        'position_compensation', // 位置補償
        'signal_compensation_db', // 信號補償
        'updateInterval',       // 更新間隔
        'maxDataHistory'        // 最大數據歷史
    ]
}

// D1 事件參數映射
export const D1_PARAMETER_MAPPING: EventParameterMapping['D1'] = {
    basic: [
        'thresh1',              // 距離門檻1
        'thresh2',              // 距離門檻2  
        'hysteresis',           // 遲滯值
        'currentTime'           // 當前時間
    ],
    standard: [
        'thresh1',
        'thresh2',
        'hysteresis',
        'currentTime',
        'uePosition',           // UE位置
        'servingSatelliteId',   // 服務衛星
        'referenceLocationId'   // 參考位置
    ],
    expert: [
        'thresh1',
        'thresh2', 
        'hysteresis',
        'currentTime',
        'uePosition',
        'servingSatelliteId',
        'referenceLocationId',
        'minElevationAngle',    // 最小仰角
        'timeWindowMs',         // 時間窗口
        'useRealData',          // 數據模式
        'autoUpdate',           // 自動更新
        'updateInterval'        // 更新間隔
    ]
}

// D2 事件參數映射
export const D2_PARAMETER_MAPPING: EventParameterMapping['D2'] = {
    basic: [
        'thresh1',              // 衛星距離門檻
        'thresh2',              // 地面距離門檻
        'hysteresis',           // 遲滯值
        'currentTime'           // 當前時間
    ],
    standard: [
        'thresh1',
        'thresh2',
        'hysteresis', 
        'currentTime',
        'uePosition',           // UE位置
        'movingReferenceLocation', // 移動參考位置
        'showThresholdLines'    // 顯示門檻線
    ],
    expert: [
        'thresh1',
        'thresh2',
        'hysteresis',
        'currentTime', 
        'uePosition',
        'movingReferenceLocation',
        'showThresholdLines',
        'isDarkTheme',          // 主題模式
        'useRealData',          // 數據模式
        'autoUpdate',           // 自動更新
        'updateInterval',       // 更新間隔
        'orbitPeriod',          // 軌道週期
        'satelliteAltitude'     // 衛星高度
    ]
}

// T1 事件參數映射
export const T1_PARAMETER_MAPPING: EventParameterMapping['T1'] = {
    basic: [
        't1Threshold',          // T1門檻值
        'duration',             // 持續時間
        'currentTime'           // 當前時間
    ],
    standard: [
        't1Threshold',
        'duration',
        'currentTime',
        'serviceStartTime',     // 服務開始時間
        'serviceEndTime',       // 服務結束時間
        'showThresholdLines'    // 顯示門檻線
    ],
    expert: [
        't1Threshold', 
        'duration',
        'currentTime',
        'serviceStartTime',
        'serviceEndTime',
        'showThresholdLines',
        'sessionScenario',      // 會話場景
        'timeSync',             // 時間同步
        'syncAccuracy',         // 同步精度
        'useRealData',          // 數據模式
        'autoUpdate',           // 自動更新
        'updateInterval'        // 更新間隔
    ]
}

// 統一參數映射
export const EVENT_PARAMETER_MAPPINGS: EventParameterMapping = {
    A4: A4_PARAMETER_MAPPING,
    D1: D1_PARAMETER_MAPPING,
    D2: D2_PARAMETER_MAPPING,
    T1: T1_PARAMETER_MAPPING
}

// 視圖模式管理 Hook 介面
export interface ViewModeManager {
    currentMode: ViewMode
    config: ViewModeConfig
    toggleMode: () => void
    setMode: (mode: ViewMode) => void
    updateConfig: (updates: Partial<ViewModeConfig>) => void
    getParametersForLevel: (eventType: string, level: ParameterLevel) => string[]
    isParameterVisible: (eventType: string, parameterName: string) => boolean
}

// 教育模式內容配置
export interface EducationConfig {
    concepts: {
        [conceptId: string]: {
            title: string
            description: string
            physicalMeaning: string
            applicationScenarios: string[]
            relatedParameters: string[]
        }
    }
    
    guidelines: {
        [eventType: string]: {
            quickStart: string
            commonPitfalls: string[]
            bestPractices: string[]
            troubleshooting: string[]
        }
    }
}

// A4 事件教育內容
export const A4_EDUCATION_CONFIG: EducationConfig['concepts'] = {
    'a4-threshold': {
        title: 'A4 門檻值 (A4 Threshold)',
        description: '鄰居細胞信號強度必須超過服務細胞信號強度的門檻值，才會觸發 A4 事件',
        physicalMeaning: '表示切換的敏感度，值越小越容易觸發切換',
        applicationScenarios: [
            '密集城市環境：較小的門檻值(1-3dB)確保及時切換',
            '郊區環境：較大的門檻值(3-6dB)避免頻繁切換',
            '高速移動場景：中等門檻值(2-4dB)平衡切換效率和穩定性'
        ],
        relatedParameters: ['hysteresis', 'time_to_trigger', 'position_compensation']
    },
    
    'position-compensation': {
        title: '位置補償 (Position Compensation)',
        description: '基於 UE 和衛星的相對位置動態調整信號強度測量值',
        physicalMeaning: '補償因衛星移動和 UE 位置變化導致的信號強度偏差',
        applicationScenarios: [
            'LEO 衛星通訊：補償快速軌道運動造成的信號變化',
            '高速移動用戶：補償都卜勒效應和路徑變化',
            '山區通訊：補償地形遮蔽和反射效應'
        ],
        relatedParameters: ['ue_position', 'satellite_position', 'signal_compensation_db']
    }
}

// 視圖模式本地存儲管理
export const VIEW_MODE_STORAGE_KEY = 'ntn-stack-view-mode'
export const VIEW_MODE_CONFIG_STORAGE_KEY = 'ntn-stack-view-mode-config'

// 用戶偏好存儲介面
export interface UserPreferences {
    defaultViewMode: ViewMode
    customConfigs: {
        [configName: string]: Partial<ViewModeConfig>
    }
    lastUsedEventType: string
    favoriteParameters: {
        [eventType: string]: string[]
    }
}