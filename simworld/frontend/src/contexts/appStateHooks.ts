/**
 * 專門化的 App State Hooks
 * 從 AppStateContext 中分離出來以避免 fast refresh 警告
 */
import { useContext, useMemo } from 'react'
import { AppStateContext, type AppStateContextType } from './AppStateContext'

export const useAppState = (): AppStateContextType => {
  const context = useContext(AppStateContext)
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppStateProvider')
  }
  return context
}

export const useUIState = () => {
  const { uiState, setActiveComponent, setAuto, setManualDirection, setUavAnimation, setSelectedReceiverIds } = useAppState()
  return useMemo(() => ({
    ...uiState,
    setActiveComponent,
    setAuto,
    setManualDirection,
    setUavAnimation,
    setSelectedReceiverIds,
  }), [uiState, setActiveComponent, setAuto, setManualDirection, setUavAnimation, setSelectedReceiverIds])
}

export const useFeatureState = () => {
  const { featureState, updateFeatureState } = useAppState()
  return useMemo(() => ({
    ...featureState,
    updateFeatureState,
  }), [featureState, updateFeatureState])
}

export const useSatelliteState = () => {
  const {
    satelliteState,
    setSkyfieldSatellites,
    setSatelliteEnabled,
    setSelectedConstellation
  } = useAppState()
  return useMemo(() => ({
    ...satelliteState,
    setSkyfieldSatellites,
    setSatelliteEnabled,
    setSelectedConstellation,
  }), [
    satelliteState,
    setSkyfieldSatellites,
    setSatelliteEnabled,
    setSelectedConstellation
  ])
}

export const useHandoverState = () => {
  const { 
    handoverState, 
    setHandoverStableDuration, 
    setHandoverMode, 
    setAlgorithmResults,
    setHandoverState,
    setCurrentConnection,
    setPredictedConnection,
    setIsTransitioning,
    setTransitionProgress,
    setSatelliteMovementSpeed,
    setHandoverTimingSpeed
  } = useAppState()
  
  // 直接返回對象，讓 React 處理優化
  return {
    ...handoverState,
    setHandoverStableDuration,
    setHandoverMode,
    setAlgorithmResults,
    setHandoverState,
    setCurrentConnection,
    setPredictedConnection,
    setIsTransitioning,
    setTransitionProgress,
    setSatelliteMovementSpeed,
    setHandoverTimingSpeed
  }
}

export const useDataState = () => {
  const { dataState } = useAppState()
  return dataState
}