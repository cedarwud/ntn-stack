/**
 * 視圖模式管理器 Hook
 * 
 * 功能：
 * 1. 統一管理測量事件的視圖模式
 * 2. 支援簡易版和完整版模式切換
 * 3. 提供模式特定的配置和行為
 * 4. 處理模式切換的狀態管理
 */

import { useState, useCallback, useEffect, useMemo } from 'react'
import { ViewMode, ViewModeConfig, EventType } from '../../../../../types/measurement-view-modes'

// 預設視圖模式配置
const DEFAULT_VIEW_MODE_CONFIGS: Record<ViewMode, ViewModeConfig> = {
  simple: {
    mode: 'simple',
    displayName: '簡易版',
    description: '簡化的測量事件視圖，適合快速查看',
    features: {
      showAdvancedParameters: false,
      showPhysicalModels: false,
      showEducationalContent: false,
      showDetailedCharts: false,
      showRealTimeData: true,
      showBasicControls: true
    },
    chartConfig: {
      showLegend: true,
      showTooltips: true,
      showGrid: false,
      animationDuration: 500,
      maxDataPoints: 50
    },
    uiConfig: {
      compactLayout: true,
      showSidebar: false,
      showToolbar: true,
      theme: 'light'
    }
  },
  full: {
    mode: 'full',
    displayName: '完整版',
    description: '完整的測量事件視圖，包含所有功能和詳細資訊',
    features: {
      showAdvancedParameters: true,
      showPhysicalModels: true,
      showEducationalContent: true,
      showDetailedCharts: true,
      showRealTimeData: true,
      showBasicControls: true
    },
    chartConfig: {
      showLegend: true,
      showTooltips: true,
      showGrid: true,
      animationDuration: 750,
      maxDataPoints: 200
    },
    uiConfig: {
      compactLayout: false,
      showSidebar: true,
      showToolbar: true,
      theme: 'dark'
    }
  }
}

// 事件特定的視圖模式配置
const EVENT_SPECIFIC_CONFIGS: Record<EventType, Partial<ViewModeConfig>> = {
  A4: {
    features: {
      showSignalStrengthChart: true,
      showNeighborCellInfo: true,
      showHandoverPrediction: true
    }
  },
  D1: {
    features: {
      showDistanceChart: true,
      showSatelliteTrajectory: true,
      showGeographicView: true
    }
  },
  D2: {
    features: {
      showReferenceLocationChart: true,
      showOrbitPrediction: true,
      showSIB19Integration: true
    }
  },
  T1: {
    features: {
      showTimeSyncChart: true,
      showGNSSIntegration: true,
      showTimeFrameAnalysis: true
    }
  }
}

// Hook 返回類型
interface UseViewModeManagerReturn {
  // 當前狀態
  currentMode: ViewMode
  currentConfig: ViewModeConfig
  isTransitioning: boolean
  
  // 操作方法
  switchToMode: (mode: ViewMode) => void
  toggleMode: () => void
  resetToDefault: () => void
  
  // 配置方法
  updateConfig: (updates: Partial<ViewModeConfig>) => void
  getEventSpecificConfig: (eventType: EventType) => ViewModeConfig
  
  // 工具方法
  isFeatureEnabled: (feature: keyof ViewModeConfig['features']) => boolean
  getChartConfig: () => ViewModeConfig['chartConfig']
  getUIConfig: () => ViewModeConfig['uiConfig']
}

// 視圖模式管理器 Hook
export const useViewModeManager = (
  initialMode: ViewMode = 'simple',
  eventType?: EventType
): UseViewModeManagerReturn => {
  // 狀態管理
  const [currentMode, setCurrentMode] = useState<ViewMode>(initialMode)
  const [customConfig, setCustomConfig] = useState<Partial<ViewModeConfig>>({})
  const [isTransitioning, setIsTransitioning] = useState(false)

  // 計算當前配置
  const currentConfig = useMemo((): ViewModeConfig => {
    const baseConfig = DEFAULT_VIEW_MODE_CONFIGS[currentMode]
    const eventSpecificConfig = eventType ? EVENT_SPECIFIC_CONFIGS[eventType] : {}
    
    return {
      ...baseConfig,
      ...eventSpecificConfig,
      ...customConfig,
      features: {
        ...baseConfig.features,
        ...eventSpecificConfig.features,
        ...customConfig.features
      },
      chartConfig: {
        ...baseConfig.chartConfig,
        ...eventSpecificConfig.chartConfig,
        ...customConfig.chartConfig
      },
      uiConfig: {
        ...baseConfig.uiConfig,
        ...eventSpecificConfig.uiConfig,
        ...customConfig.uiConfig
      }
    }
  }, [currentMode, eventType, customConfig])

  // 切換到指定模式
  const switchToMode = useCallback((mode: ViewMode) => {
    if (mode === currentMode) return
    
    setIsTransitioning(true)
    
    // 模擬切換動畫
    setTimeout(() => {
      setCurrentMode(mode)
      setIsTransitioning(false)
    }, 300)
  }, [currentMode])

  // 切換模式（簡易版 ↔ 完整版）
  const toggleMode = useCallback(() => {
    const nextMode = currentMode === 'simple' ? 'full' : 'simple'
    switchToMode(nextMode)
  }, [currentMode, switchToMode])

  // 重置到預設配置
  const resetToDefault = useCallback(() => {
    setCustomConfig({})
    setCurrentMode(initialMode)
  }, [initialMode])

  // 更新配置
  const updateConfig = useCallback((updates: Partial<ViewModeConfig>) => {
    setCustomConfig(prev => ({
      ...prev,
      ...updates,
      features: {
        ...prev.features,
        ...updates.features
      },
      chartConfig: {
        ...prev.chartConfig,
        ...updates.chartConfig
      },
      uiConfig: {
        ...prev.uiConfig,
        ...updates.uiConfig
      }
    }))
  }, [])

  // 獲取事件特定配置
  const getEventSpecificConfig = useCallback((eventType: EventType): ViewModeConfig => {
    const baseConfig = DEFAULT_VIEW_MODE_CONFIGS[currentMode]
    const eventSpecificConfig = EVENT_SPECIFIC_CONFIGS[eventType]
    
    return {
      ...baseConfig,
      ...eventSpecificConfig,
      features: {
        ...baseConfig.features,
        ...eventSpecificConfig.features
      }
    }
  }, [currentMode])

  // 檢查功能是否啟用
  const isFeatureEnabled = useCallback((feature: keyof ViewModeConfig['features']): boolean => {
    return currentConfig.features[feature] === true
  }, [currentConfig.features])

  // 獲取圖表配置
  const getChartConfig = useCallback(() => {
    return currentConfig.chartConfig
  }, [currentConfig.chartConfig])

  // 獲取 UI 配置
  const getUIConfig = useCallback(() => {
    return currentConfig.uiConfig
  }, [currentConfig.uiConfig])

  // 監聽模式變化，觸發相關副作用
  useEffect(() => {
    // 可以在這裡添加模式切換的副作用
    // 例如：記錄分析、本地存儲等
    console.log(`視圖模式切換到: ${currentMode}`)
  }, [currentMode])

  return {
    // 當前狀態
    currentMode,
    currentConfig,
    isTransitioning,
    
    // 操作方法
    switchToMode,
    toggleMode,
    resetToDefault,
    
    // 配置方法
    updateConfig,
    getEventSpecificConfig,
    
    // 工具方法
    isFeatureEnabled,
    getChartConfig,
    getUIConfig
  }
}

// 視圖模式上下文 Hook（用於跨組件共享）
export const useViewModeContext = () => {
  // 這裡可以實現 Context 邏輯
  // 暫時返回基本的 Hook
  return useViewModeManager()
}

// 預設導出
export default useViewModeManager
