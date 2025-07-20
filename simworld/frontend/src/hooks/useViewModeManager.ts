/**
 * 統一視圖模式管理 Hook
 * 實現簡易版/完整版模式的統一管理和狀態控制
 * 
 * 功能：
 * - 模式切換和狀態管理
 * - 參數顯示控制
 * - 用戶偏好存儲
 * - 事件特定配置
 */

import { useState, useCallback, useEffect, useMemo } from 'react'
import {
    ViewMode,
    ViewModeConfig,
    ViewModeManager,
    ParameterLevel,
    SIMPLE_MODE_CONFIG,
    ADVANCED_MODE_CONFIG,
    EVENT_PARAMETER_MAPPINGS,
    VIEW_MODE_STORAGE_KEY,
    VIEW_MODE_CONFIG_STORAGE_KEY,
    UserPreferences
} from '../types/measurement-view-modes'

// Hook 配置選項
interface UseViewModeManagerOptions {
    eventType: string                           // 事件類型 (A4, D1, D2, T1)
    defaultMode?: ViewMode                      // 預設模式
    enableLocalStorage?: boolean                // 是否啟用本地存儲
    customConfig?: Partial<ViewModeConfig>      // 自定義配置覆蓋
    onModeChange?: (mode: ViewMode) => void     // 模式變更回調
}

export const useViewModeManager = (options: UseViewModeManagerOptions): ViewModeManager => {
    const {
        eventType,
        defaultMode = 'simple',
        enableLocalStorage = true,
        customConfig = {},
        onModeChange
    } = options

    // 從本地存儲載入用戶偏好
    const loadUserPreferences = useCallback((): UserPreferences => {
        if (!enableLocalStorage) {
            return {
                defaultViewMode: defaultMode,
                customConfigs: {},
                lastUsedEventType: eventType,
                favoriteParameters: {}
            }
        }

        try {
            const stored = localStorage.getItem(VIEW_MODE_CONFIG_STORAGE_KEY)
            if (stored) {
                return JSON.parse(stored)
            }
        } catch (error) {
            console.warn('Failed to load user preferences:', error)
        }

        return {
            defaultViewMode: defaultMode,
            customConfigs: {},
            lastUsedEventType: eventType,
            favoriteParameters: {}
        }
    }, [defaultMode, eventType, enableLocalStorage])

    // 保存用戶偏好到本地存儲
    const saveUserPreferences = useCallback((preferences: UserPreferences) => {
        if (!enableLocalStorage) return

        try {
            localStorage.setItem(VIEW_MODE_CONFIG_STORAGE_KEY, JSON.stringify(preferences))
        } catch (error) {
            console.warn('Failed to save user preferences:', error)
        }
    }, [enableLocalStorage])

    // 載入初始模式
    const loadInitialMode = useCallback((): ViewMode => {
        if (!enableLocalStorage) return defaultMode

        try {
            const stored = localStorage.getItem(VIEW_MODE_STORAGE_KEY)
            if (stored && (stored === 'simple' || stored === 'advanced')) {
                return stored as ViewMode
            }
        } catch (error) {
            console.warn('Failed to load view mode from storage:', error)
        }

        return defaultMode
    }, [defaultMode, enableLocalStorage])

    // 狀態管理
    const [currentMode, setCurrentMode] = useState<ViewMode>(loadInitialMode)
    const [userPreferences, setUserPreferences] = useState<UserPreferences>(loadUserPreferences)

    // 基礎配置計算
    const baseConfig = useMemo((): ViewModeConfig => {
        const base = currentMode === 'simple' ? SIMPLE_MODE_CONFIG : ADVANCED_MODE_CONFIG
        
        // 合併自定義配置
        return {
            ...base,
            ...customConfig,
            parameters: {
                ...base.parameters,
                ...customConfig.parameters
            },
            chart: {
                ...base.chart,
                ...customConfig.chart
            },
            controls: {
                ...base.controls,
                ...customConfig.controls
            },
            education: {
                ...base.education,
                ...customConfig.education
            },
            performance: {
                ...base.performance,
                ...customConfig.performance
            }
        }
    }, [currentMode, customConfig])

    // 應用用戶自定義配置
    const config = useMemo((): ViewModeConfig => {
        const customConfigName = `${eventType}_${currentMode}`
        const userCustomConfig = userPreferences.customConfigs[customConfigName]
        
        if (!userCustomConfig) return baseConfig

        return {
            ...baseConfig,
            ...userCustomConfig,
            parameters: {
                ...baseConfig.parameters,
                ...userCustomConfig.parameters
            },
            chart: {
                ...baseConfig.chart,
                ...userCustomConfig.chart
            },
            controls: {
                ...baseConfig.controls,
                ...userCustomConfig.controls
            },
            education: {
                ...baseConfig.education,
                ...userCustomConfig.education
            },
            performance: {
                ...baseConfig.performance,
                ...userCustomConfig.performance
            }
        }
    }, [baseConfig, userPreferences.customConfigs, eventType, currentMode])

    // 切換模式
    const toggleMode = useCallback(() => {
        const newMode = currentMode === 'simple' ? 'advanced' : 'simple'
        setCurrentMode(newMode)
        
        // 保存到本地存儲
        if (enableLocalStorage) {
            try {
                localStorage.setItem(VIEW_MODE_STORAGE_KEY, newMode)
            } catch (error) {
                console.warn('Failed to save view mode to storage:', error)
            }
        }

        // 更新用戶偏好
        const updatedPreferences = {
            ...userPreferences,
            defaultViewMode: newMode,
            lastUsedEventType: eventType
        }
        setUserPreferences(updatedPreferences)
        saveUserPreferences(updatedPreferences)

        // 觸發回調
        if (onModeChange) {
            onModeChange(newMode)
        }
    }, [currentMode, enableLocalStorage, userPreferences, eventType, saveUserPreferences, onModeChange])

    // 設置特定模式
    const setMode = useCallback((mode: ViewMode) => {
        if (mode === currentMode) return

        setCurrentMode(mode)

        // 保存到本地存儲
        if (enableLocalStorage) {
            try {
                localStorage.setItem(VIEW_MODE_STORAGE_KEY, mode)
            } catch (error) {
                console.warn('Failed to save view mode to storage:', error)
            }
        }

        // 更新用戶偏好
        const updatedPreferences = {
            ...userPreferences,
            defaultViewMode: mode,
            lastUsedEventType: eventType
        }
        setUserPreferences(updatedPreferences)
        saveUserPreferences(updatedPreferences)

        // 觸發回調
        if (onModeChange) {
            onModeChange(mode)
        }
    }, [currentMode, enableLocalStorage, userPreferences, eventType, saveUserPreferences, onModeChange])

    // 更新配置
    const updateConfig = useCallback((updates: Partial<ViewModeConfig>) => {
        const customConfigName = `${eventType}_${currentMode}`
        const currentCustomConfig = userPreferences.customConfigs[customConfigName] || {}
        
        const newCustomConfig = {
            ...currentCustomConfig,
            ...updates
        }

        const updatedPreferences = {
            ...userPreferences,
            customConfigs: {
                ...userPreferences.customConfigs,
                [customConfigName]: newCustomConfig
            }
        }

        setUserPreferences(updatedPreferences)
        saveUserPreferences(updatedPreferences)
    }, [eventType, currentMode, userPreferences, saveUserPreferences])

    // 獲取特定級別的參數列表
    const getParametersForLevel = useCallback((eventTypeParam: string, level: ParameterLevel): string[] => {
        const mapping = EVENT_PARAMETER_MAPPINGS[eventTypeParam]
        if (!mapping) {
            console.warn(`No parameter mapping found for event type: ${eventTypeParam}`)
            return []
        }

        switch (level) {
            case 'basic':
                return mapping.basic
            case 'standard':
                return mapping.standard
            case 'expert':
                return mapping.expert
            default:
                return mapping.basic
        }
    }, [])

    // 檢查參數是否應該顯示
    const isParameterVisible = useCallback((eventTypeParam: string, parameterName: string): boolean => {
        const { parameters } = config
        const currentParameters = getParametersForLevel(eventTypeParam, parameters.level)
        
        // 基本參數總是顯示
        if (currentParameters.includes(parameterName)) {
            return true
        }

        // 檢查進階參數
        if (parameters.showAdvancedParameters) {
            const standardParameters = getParametersForLevel(eventTypeParam, 'standard')
            if (standardParameters.includes(parameterName)) {
                return true
            }
        }

        // 檢查專家參數
        if (parameters.showExpertParameters) {
            const expertParameters = getParametersForLevel(eventTypeParam, 'expert')
            if (expertParameters.includes(parameterName)) {
                return true
            }
        }

        // 檢查收藏參數
        const favoriteParams = userPreferences.favoriteParameters[eventTypeParam] || []
        if (favoriteParams.includes(parameterName)) {
            return true
        }

        return false
    }, [config, getParametersForLevel, userPreferences.favoriteParameters])

    // 監聽配置變化，自動保存
    useEffect(() => {
        if (enableLocalStorage) {
            saveUserPreferences(userPreferences)
        }
    }, [userPreferences, enableLocalStorage, saveUserPreferences])

    // 返回管理器介面
    return {
        currentMode,
        config,
        toggleMode,
        setMode,
        updateConfig,
        getParametersForLevel,
        isParameterVisible
    }
}

// 便利 Hook：取得當前應該顯示的參數列表
export const useVisibleParameters = (
    eventType: string, 
    allParameters: string[], 
    viewModeManager: ViewModeManager
): string[] => {
    return useMemo(() => {
        return allParameters.filter(param => 
            viewModeManager.isParameterVisible(eventType, param)
        )
    }, [eventType, allParameters, viewModeManager])
}

// 便利 Hook：檢查功能是否啟用
export const useFeatureEnabled = (
    feature: keyof ViewModeConfig, 
    viewModeManager: ViewModeManager
): boolean => {
    return useMemo(() => {
        const config = viewModeManager.config
        
        switch (feature) {
            case 'parameters':
                return config.parameters.showAdvancedParameters
            case 'chart':
                return config.chart.showTechnicalDetails
            case 'controls':
                return config.controls.showAdvancedControls
            case 'education':
                return config.education.showConceptExplanations
            default:
                return false
        }
    }, [feature, viewModeManager.config])
}

// 便利 Hook：取得教育模式狀態
export const useEducationMode = (viewModeManager: ViewModeManager) => {
    const { config } = viewModeManager
    
    return useMemo(() => ({
        enabled: config.education.showConceptExplanations,
        showDescriptions: config.education.showParameterDescriptions,
        showPhysicalMeaning: config.education.showPhysicalMeaning,
        showScenarios: config.education.showApplicationScenarios,
        interactiveGuidance: config.education.interactiveGuidance
    }), [config.education])
}