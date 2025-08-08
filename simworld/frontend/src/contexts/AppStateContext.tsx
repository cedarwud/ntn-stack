/**
 * 統一應用狀態Context
 * 用於減少App.tsx中的Props傳遞地獄問題
 * 將不同領域的狀態分組管理
 */

import React, {
    createContext,
    useState,
    useCallback,
    useMemo,
    ReactNode,
} from 'react'
import { VisibleSatelliteInfo } from '../types/satellite'
// import { SATELLITE_CONFIG } from '../config/satellite.config'

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
    // 星座選擇狀態
    selectedConstellation: 'starlink' | 'oneweb'
}

interface HandoverState {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    handoverState: any
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    currentConnection: any
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    predictedConnection: any
    isTransitioning: boolean
    transitionProgress: number
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    algorithmResults: any
    satelliteMovementSpeed: number
}

interface DataState {
    // 可以根據需要添加數據相關的狀態
    isLoading: boolean
    lastUpdated: Date | null
}

interface FeatureState {
    // 階段四功能
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
    featureState: FeatureState
    handoverState: HandoverState
    dataState: DataState

    // UI狀態更新函數
    setActiveComponent: (component: string) => void
    setAuto: (auto: boolean) => void
    setManualDirection: (direction: string | null) => void
    setUavAnimation: (enabled: boolean) => void
    setSelectedReceiverIds: (ids: number[]) => void

    // 衛星狀態更新函數
    setSkyfieldSatellites: (satellites: VisibleSatelliteInfo[]) => void
    setSatelliteEnabled: (enabled: boolean) => void
    // 星座選擇狀態更新函數
    setSelectedConstellation: (constellation: 'starlink' | 'oneweb') => void

    // 功能開關更新函數
    updateFeatureState: (updates: Partial<FeatureState>) => void

    // Handover狀態更新函數
    updateHandoverState: (updates: Partial<HandoverState>) => void

    // Data狀態更新函數
    updateDataState: (updates: Partial<DataState>) => void
}

// ==================== Context創建 ====================

// eslint-disable-next-line react-refresh/only-export-components
export const AppStateContext = createContext<AppStateContextType | undefined>(
    undefined
)

// ==================== Provider組件 ====================

interface AppStateProviderProps {
    children: ReactNode
    initialActiveComponent?: string
}

export const AppStateProvider: React.FC<AppStateProviderProps> = ({
    children,
    initialActiveComponent = '3DRT',
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
        // 星座選擇初始狀態
        selectedConstellation: 'starlink', // 預設為 Starlink
    })

    // 功能狀態
    const [featureState, setFeatureState] = useState<FeatureState>({
        // 階段四功能 - 預設關閉
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

    // Handover狀態
    const [handoverState, setHandoverState] = useState<HandoverState>({
        handoverState: null,
        currentConnection: null,
        predictedConnection: null,
        isTransitioning: false,
        transitionProgress: 0,
        algorithmResults: null,
        satelliteMovementSpeed: 1,
    })

    // Data狀態
    const [dataState, setDataState] = useState<DataState>({
        isLoading: false,
        lastUpdated: null,
    })

    // ==================== 更新函數 ====================

    // UI狀態更新
    const setActiveComponent = useCallback((component: string) => {
        setUiState((prev) => ({ ...prev, activeComponent: component }))
    }, [])

    const setAuto = useCallback((auto: boolean) => {
        setUiState((prev) => ({ ...prev, auto }))
    }, [])

    const setManualDirection = useCallback((direction: string | null) => {
        setUiState((prev) => ({ ...prev, manualDirection: direction }))
    }, [])

    const setUavAnimation = useCallback((enabled: boolean) => {
        setUiState((prev) => ({ ...prev, uavAnimation: enabled }))
    }, [])

    const setSelectedReceiverIds = useCallback((ids: number[]) => {
        setUiState((prev) => ({ ...prev, selectedReceiverIds: ids }))
    }, [])

    // 衛星狀態更新
    const setSkyfieldSatellites = useCallback(
        (satellites: VisibleSatelliteInfo[]) => {
            // console.log(`🔧 AppState: setSkyfieldSatellites 收到:`, satellites.length, '顆衛星')
            setSatelliteState((prev) => ({
                ...prev,
                skyfieldSatellites: satellites,
            }))
        },
        []
    )

    const setSatelliteEnabled = useCallback((enabled: boolean) => {
        setSatelliteState((prev) => ({ ...prev, satelliteEnabled: enabled }))
    }, [])

    // 星座選擇狀態更新函數
    const setSelectedConstellation = useCallback(
        (constellation: 'starlink' | 'oneweb') => {
            setSatelliteState((prev) => ({
                ...prev,
                selectedConstellation: constellation,
            }))
        },
        []
    )

    // 功能狀態批量更新
    const updateFeatureState = useCallback((updates: Partial<FeatureState>) => {
        setFeatureState((prev) => ({ ...prev, ...updates }))
    }, [])

    // Handover狀態批量更新
    const updateHandoverState = useCallback(
        (updates: Partial<HandoverState>) => {
            setHandoverState((prev) => ({ ...prev, ...updates }))
        },
        []
    )

    // Data狀態批量更新
    const updateDataState = useCallback((updates: Partial<DataState>) => {
        setDataState((prev) => ({ ...prev, ...updates }))
    }, [])

    // ==================== Context值 ====================

    // 使用 useMemo 來穩定 contextValue 避免不必要的重新渲染
    const contextValue: AppStateContextType = useMemo(
        () => ({
            // 狀態
            uiState,
            satelliteState,
            featureState,
            handoverState,
            dataState,

            // UI狀態更新函數
            setActiveComponent,
            setAuto,
            setManualDirection,
            setUavAnimation,
            setSelectedReceiverIds,

            // 衛星狀態更新函數
            setSkyfieldSatellites,
            setSatelliteEnabled,
            // 星座選擇狀態更新函數
            setSelectedConstellation,

            // 功能開關更新函數
            updateFeatureState,
            // Handover狀態更新函數
            updateHandoverState,
            // Data狀態更新函數
            updateDataState,
        }),
        [
            uiState,
            satelliteState,
            featureState,
            handoverState,
            dataState,
            setActiveComponent,
            setAuto,
            setManualDirection,
            setUavAnimation,
            setSelectedReceiverIds,
            setSkyfieldSatellites,
            setSatelliteEnabled,
            setSelectedConstellation,
            updateFeatureState,
            updateHandoverState,
            updateDataState,
        ]
    )

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
