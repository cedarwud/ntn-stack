/**
 * 統一應用狀態Context
 * 用於減少App.tsx中的Props傳遞地獄問題
 * 將不同領域的狀態分組管理
 */

import React, { createContext, useState, useCallback, useMemo, ReactNode } from 'react'
import { VisibleSatelliteInfo } from '../types/satellite'

// ==================== 狀態類型定義 ====================

interface UIState {
  activeComponent: string
  auto: boolean
  manualDirection: string | null
  uavAnimation: boolean
  selectedReceiverIds: number[]
}

interface SatelliteState {
  skyfieldSatellites: VisibleSatelliteInfo[]
  satelliteEnabled: boolean
}

interface HandoverState {
  handoverStableDuration: number
  handoverMode: 'demo' | 'real'
  algorithmResults: {
    currentSatelliteId?: string
    predictedSatelliteId?: string
    handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
    binarySearchActive?: boolean
    predictionConfidence?: number
  }
  handoverState: unknown
  currentConnection: unknown
  predictedConnection: unknown
  isTransitioning: boolean
  transitionProgress: number
}

interface FeatureState {
  // 階段四功能
  interferenceVisualizationEnabled: boolean
  sinrHeatmapEnabled: boolean
  aiRanVisualizationEnabled: boolean
  manualControlEnabled: boolean
  sionna3DVisualizationEnabled: boolean
  realTimeMetricsEnabled: boolean
  interferenceAnalyticsEnabled: boolean
  
  // 階段五功能
  uavSwarmCoordinationEnabled: boolean
  meshNetworkTopologyEnabled: boolean
  satelliteUavConnectionEnabled: boolean
  failoverMechanismEnabled: boolean
  
  // 階段六功能
  predictionPath3DEnabled: boolean
  predictionAccuracyDashboardEnabled: boolean
  coreNetworkSyncEnabled: boolean
  
  // Stage 3 功能
  realtimePerformanceMonitorEnabled: boolean
  scenarioTestEnvironmentEnabled: boolean
  
  // 3D 換手動畫
  handover3DAnimationEnabled: boolean
  
  // 階段七功能
  e2ePerformanceMonitoringEnabled: boolean
  testResultsVisualizationEnabled: boolean
  performanceTrendAnalysisEnabled: boolean
  automatedReportGenerationEnabled: boolean
  
  // 階段八功能
  predictiveMaintenanceEnabled: boolean
  intelligentRecommendationEnabled: boolean
}

// ==================== Context介面定義 ====================

export interface AppStateContextType {
  // 狀態
  uiState: UIState
  satelliteState: SatelliteState
  handoverState: HandoverState
  featureState: FeatureState
  
  // UI狀態更新函數
  setActiveComponent: (component: string) => void
  setAuto: (auto: boolean) => void
  setManualDirection: (direction: string | null) => void
  setUavAnimation: (enabled: boolean) => void
  setSelectedReceiverIds: (ids: number[]) => void
  
  // 衛星狀態更新函數
  setSkyfieldSatellites: (satellites: VisibleSatelliteInfo[]) => void
  setSatelliteEnabled: (enabled: boolean) => void
  
  // 換手狀態更新函數
  setHandoverStableDuration: (duration: number) => void
  setHandoverMode: (mode: 'demo' | 'real') => void
  setAlgorithmResults: (results: HandoverState['algorithmResults']) => void
  setHandoverState: (state: unknown) => void
  setCurrentConnection: (connection: unknown) => void
  setPredictedConnection: (connection: unknown) => void
  setIsTransitioning: (transitioning: boolean) => void
  setTransitionProgress: (progress: number) => void
  
  // 功能開關更新函數
  updateFeatureState: (updates: Partial<FeatureState>) => void
}

// ==================== Context創建 ====================

// eslint-disable-next-line react-refresh/only-export-components
export const AppStateContext = createContext<AppStateContextType | undefined>(undefined)

// ==================== Provider組件 ====================

interface AppStateProviderProps {
  children: ReactNode
  initialActiveComponent?: string
}

export const AppStateProvider: React.FC<AppStateProviderProps> = ({ 
  children, 
  initialActiveComponent = '3DRT' 
}) => {
  // UI狀態
  const [uiState, setUiState] = useState<UIState>({
    activeComponent: initialActiveComponent,
    auto: false,
    manualDirection: null,
    uavAnimation: false,
    selectedReceiverIds: [],
  })

  // 衛星狀態
  const [satelliteState, setSatelliteState] = useState<SatelliteState>({
    skyfieldSatellites: [],
    satelliteEnabled: true,
  })

  // 換手狀態
  const [handoverState, setHandoverState] = useState<HandoverState>({
    handoverStableDuration: 5,
    handoverMode: 'demo',
    algorithmResults: {},
    handoverState: null,
    currentConnection: null,
    predictedConnection: null,
    isTransitioning: false,
    transitionProgress: 0,
  })

  // 功能狀態
  const [featureState, setFeatureState] = useState<FeatureState>({
    // 階段四功能 - 預設關閉
    interferenceVisualizationEnabled: false,
    sinrHeatmapEnabled: false,
    aiRanVisualizationEnabled: false,
    manualControlEnabled: false,
    sionna3DVisualizationEnabled: false,
    realTimeMetricsEnabled: false,
    interferenceAnalyticsEnabled: false,
    
    // 階段五功能 - 預設關閉
    uavSwarmCoordinationEnabled: false,
    meshNetworkTopologyEnabled: false,
    satelliteUavConnectionEnabled: false,
    failoverMechanismEnabled: false,
    
    // 階段六功能 - 預設關閉
    predictionPath3DEnabled: false,
    predictionAccuracyDashboardEnabled: false,
    coreNetworkSyncEnabled: false,
    
    // Stage 3 功能 - 預設關閉
    realtimePerformanceMonitorEnabled: false,
    scenarioTestEnvironmentEnabled: false,
    
    // 3D 換手動畫 - 預設啟用
    handover3DAnimationEnabled: true,
    
    // 階段七功能 - 預設關閉
    e2ePerformanceMonitoringEnabled: false,
    testResultsVisualizationEnabled: false,
    performanceTrendAnalysisEnabled: false,
    automatedReportGenerationEnabled: false,
    
    // 階段八功能 - 預設關閉
    predictiveMaintenanceEnabled: false,
    intelligentRecommendationEnabled: false,
  })

  // ==================== 更新函數 ====================

  // UI狀態更新
  const setActiveComponent = useCallback((component: string) => {
    setUiState(prev => ({ ...prev, activeComponent: component }))
  }, [])

  const setAuto = useCallback((auto: boolean) => {
    setUiState(prev => ({ ...prev, auto }))
  }, [])

  const setManualDirection = useCallback((direction: string | null) => {
    setUiState(prev => ({ ...prev, manualDirection: direction }))
  }, [])

  const setUavAnimation = useCallback((enabled: boolean) => {
    setUiState(prev => ({ ...prev, uavAnimation: enabled }))
  }, [])

  const setSelectedReceiverIds = useCallback((ids: number[]) => {
    setUiState(prev => ({ ...prev, selectedReceiverIds: ids }))
  }, [])

  // 衛星狀態更新
  const setSkyfieldSatellites = useCallback((satellites: VisibleSatelliteInfo[]) => {
    setSatelliteState(prev => ({ ...prev, skyfieldSatellites: satellites }))
  }, [])

  const setSatelliteEnabled = useCallback((enabled: boolean) => {
    setSatelliteState(prev => ({ ...prev, satelliteEnabled: enabled }))
  }, [])

  // 換手狀態更新
  const setHandoverStableDuration = useCallback((duration: number) => {
    setHandoverState(prev => ({ ...prev, handoverStableDuration: duration }))
  }, [])

  const setHandoverMode = useCallback((mode: 'demo' | 'real') => {
    setHandoverState(prev => ({ ...prev, handoverMode: mode }))
  }, [])

  const setAlgorithmResults = useCallback((results: HandoverState['algorithmResults']) => {
    setHandoverState(prev => ({ ...prev, algorithmResults: results }))
  }, [])

  const setHandoverStateInternal = useCallback((state: unknown) => {
    setHandoverState(prev => ({ ...prev, handoverState: state }))
  }, [])

  const setCurrentConnection = useCallback((connection: unknown) => {
    setHandoverState(prev => ({ ...prev, currentConnection: connection }))
  }, [])

  const setPredictedConnection = useCallback((connection: unknown) => {
    setHandoverState(prev => ({ ...prev, predictedConnection: connection }))
  }, [])

  const setIsTransitioning = useCallback((transitioning: boolean) => {
    setHandoverState(prev => ({ ...prev, isTransitioning: transitioning }))
  }, [])

  const setTransitionProgress = useCallback((progress: number) => {
    setHandoverState(prev => ({ ...prev, transitionProgress: progress }))
  }, [])

  // 功能狀態批量更新
  const updateFeatureState = useCallback((updates: Partial<FeatureState>) => {
    setFeatureState(prev => ({ ...prev, ...updates }))
  }, [])

  // ==================== Context值 ====================

  // 使用 useMemo 來穩定 contextValue 避免不必要的重新渲染
  const contextValue: AppStateContextType = useMemo(() => ({
        // 狀態
        uiState,
        satelliteState,
        handoverState,
        featureState,
        
        // UI狀態更新函數
        setActiveComponent,
        setAuto,
        setManualDirection,
        setUavAnimation,
        setSelectedReceiverIds,
        
        // 衛星狀態更新函數
        setSkyfieldSatellites,
        setSatelliteEnabled,
        
        // 換手狀態更新函數
        setHandoverStableDuration,
        setHandoverMode,
        setAlgorithmResults,
        setHandoverState: setHandoverStateInternal,
        setCurrentConnection,
        setPredictedConnection,
        setIsTransitioning,
        setTransitionProgress,
        
        // 功能開關更新函數
        updateFeatureState,
    }), [
        uiState,
        satelliteState, 
        handoverState,
        featureState,
        setActiveComponent,
        setAuto,
        setManualDirection,
        setUavAnimation,
        setSelectedReceiverIds,
        setSkyfieldSatellites,
        setSatelliteEnabled,
        setHandoverStableDuration,
        setHandoverMode,
        setAlgorithmResults,
        setHandoverStateInternal,
        setCurrentConnection,
        setPredictedConnection,
        setIsTransitioning,
        setTransitionProgress,
        updateFeatureState
    ])

  return (
    <AppStateContext.Provider value={contextValue}>
      {children}
    </AppStateContext.Provider>
  )
}

// ==================== Hook ====================

// useAppState hook moved to ./appStateHooks.ts

// ==================== 專門化Hooks ====================

// useUIState hook moved to ./appStateHooks.ts

// useSatelliteState hook moved to ./appStateHooks.ts

// useHandoverState hook moved to ./appStateHooks.ts

// useFeatureState hook moved to ./appStateHooks.ts