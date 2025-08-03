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
  const { handoverState, updateHandoverState } = useAppState()
  return useMemo(() => ({
    ...handoverState,
    updateHandoverState,
    // 提供方便的單個狀態更新方法
    setHandoverMode: (mode: 'demo' | 'real') => updateHandoverState({ handoverMode: mode }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    setHandoverState: (state: any) => updateHandoverState({ handoverState: state }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    setCurrentConnection: (connection: any) => updateHandoverState({ currentConnection: connection }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    setPredictedConnection: (connection: any) => updateHandoverState({ predictedConnection: connection }),
    setIsTransitioning: (isTransitioning: boolean) => updateHandoverState({ isTransitioning }),
    setTransitionProgress: (progress: number) => updateHandoverState({ transitionProgress: progress }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    setAlgorithmResults: (results: any) => updateHandoverState({ algorithmResults: results }),
    setSatelliteMovementSpeed: (speed: number) => updateHandoverState({ satelliteMovementSpeed: speed }),
    setHandoverTimingSpeed: (speed: number) => updateHandoverState({ handoverTimingSpeed: speed }),
    setHandoverStableDuration: (duration: number) => updateHandoverState({ handoverStableDuration: duration }),
  }), [handoverState, updateHandoverState])
}

export const useDataState = () => {
  const { dataState } = useAppState()
  return dataState
}