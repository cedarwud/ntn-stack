/**
 * 統一衛星數據Context
 * 使用React Context + Reducer管理所有衛星相關狀態
 */

import React, { createContext, useContext, useReducer, useEffect, useCallback, useRef } from 'react'
import { getSatelliteDataService, UnifiedSatelliteInfo, SatelliteDataServiceConfig } from '../services/satelliteDataService'
import { getNTPUCoordinates } from '../config/observerConfig'
import { dynamicPoolService, DynamicPoolData } from '../services/DynamicPoolService'

// 衛星數據狀態類型定義
export interface SatelliteDataState {
    satellites: UnifiedSatelliteInfo[]
    loading: boolean
    error: string | null
    lastUpdated: string | null
    config: SatelliteDataServiceConfig
    selectedConstellation: 'starlink' | 'oneweb'
    systemHealth: { status: string, details: Record<string, unknown> } | null
    // 動態池相關狀態
    dynamicPool: {
        data: DynamicPoolData | null
        loading: boolean
        enabled: boolean
        error: string | null
    }
}

// Action類型定義
export type SatelliteDataAction =
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_SATELLITES'; payload: UnifiedSatelliteInfo[] }
    | { type: 'SET_ERROR'; payload: string | null }
    | { type: 'UPDATE_CONFIG'; payload: Partial<SatelliteDataServiceConfig> }
    | { type: 'SET_CONSTELLATION'; payload: 'starlink' | 'oneweb' }
    | { type: 'SET_SYSTEM_HEALTH'; payload: { status: string, details: Record<string, unknown> } }
    | { type: 'CLEAR_DATA' }
    // 動態池相關Actions
    | { type: 'SET_POOL_LOADING'; payload: boolean }
    | { type: 'SET_POOL_DATA'; payload: DynamicPoolData | null }
    | { type: 'SET_POOL_ERROR'; payload: string | null }
    | { type: 'TOGGLE_POOL_MODE'; payload: boolean }

// 初始狀態
const getInitialState = (): SatelliteDataState => {
    const coordinates = getNTPUCoordinates()
    return {
        satellites: [],
        loading: false,
        error: null,
        lastUpdated: null,
        config: {
            minElevation: 5,  // 會根據星座動態調整 (Starlink 5°, OneWeb 10°)
            maxCount: 15,     // Starlink: 10-15顆, OneWeb: 3-6顆
            observerLat: coordinates.lat, // 統一配置服務
            observerLon: coordinates.lon, // 統一配置服務
            constellation: 'starlink',
            updateInterval: 5000
        },
        selectedConstellation: 'starlink',
        systemHealth: null,
        // 動態池初始狀態
        dynamicPool: {
            data: null,
            loading: false,
            enabled: false, // 暫時禁用優化池，顯示所有可見衛星
            error: null
        }
    }
}

// Reducer函數
function satelliteDataReducer(state: SatelliteDataState, action: SatelliteDataAction): SatelliteDataState {
    switch (action.type) {
        case 'SET_LOADING':
            return {
                ...state,
                loading: action.payload
            }
        
        case 'SET_SATELLITES':
            return {
                ...state,
                satellites: action.payload,
                loading: false,
                error: null,
                lastUpdated: new Date().toISOString()
            }
        
        case 'SET_ERROR':
            return {
                ...state,
                error: action.payload,
                loading: false
            }
        
        case 'UPDATE_CONFIG':
            return {
                ...state,
                config: { ...state.config, ...action.payload }
            }
        
        case 'SET_CONSTELLATION':
            return {
                ...state,
                selectedConstellation: action.payload,
                config: { ...state.config, constellation: action.payload }
            }
        
        case 'SET_SYSTEM_HEALTH':
            return {
                ...state,
                systemHealth: action.payload
            }
        
        case 'CLEAR_DATA':
            return {
                ...state,
                satellites: [],
                error: null,
                lastUpdated: null
            }
        
        // 動態池相關cases
        case 'SET_POOL_LOADING':
            return {
                ...state,
                dynamicPool: { ...state.dynamicPool, loading: action.payload }
            }
        
        case 'SET_POOL_DATA':
            return {
                ...state,
                dynamicPool: {
                    ...state.dynamicPool,
                    data: action.payload,
                    loading: false,
                    error: null
                }
            }
        
        case 'SET_POOL_ERROR':
            return {
                ...state,
                dynamicPool: {
                    ...state.dynamicPool,
                    error: action.payload,
                    loading: false
                }
            }
        
        case 'TOGGLE_POOL_MODE':
            return {
                ...state,
                dynamicPool: { ...state.dynamicPool, enabled: action.payload }
            }
        
        default:
            return state
    }
}

// Context類型定義
interface SatelliteDataContextType {
    state: SatelliteDataState
    dispatch: React.Dispatch<SatelliteDataAction>
    refreshSatellites: (forceRefresh?: boolean) => Promise<void>
    updateConfig: (newConfig: Partial<SatelliteDataServiceConfig>) => void
    setConstellation: (constellation: 'starlink' | 'oneweb') => void
    checkSystemHealth: () => Promise<void>
    // 動態池相關方法
    loadDynamicPool: () => Promise<void>
    togglePoolMode: (enabled: boolean) => void
    getPoolStatistics: () => { mode: string, total: number, starlink: number, oneweb: number }
}

// 創建Context
const SatelliteDataContext = createContext<SatelliteDataContextType | undefined>(undefined)

// Provider組件
interface SatelliteDataProviderProps {
    children: React.ReactNode
    initialConfig?: Partial<SatelliteDataServiceConfig>
}

export const SatelliteDataProvider: React.FC<SatelliteDataProviderProps> = ({ 
    children, 
    initialConfig 
}) => {
    const initialState = getInitialState()
    const [state, dispatch] = useReducer(satelliteDataReducer, {
        ...initialState,
        config: { ...initialState.config, ...initialConfig }
    })
    
    const serviceRef = useRef(getSatelliteDataService(state.config))
    const updateIntervalRef = useRef<NodeJS.Timeout | null>(null)

    // 載入動態池數據
    const loadDynamicPool = useCallback(async () => {
        dispatch({ type: 'SET_POOL_LOADING', payload: true })
        
        try {
            await dynamicPoolService.loadDynamicPool()
            const poolStats = dynamicPoolService.getPoolStatistics()
            dispatch({ type: 'SET_POOL_DATA', payload: poolStats.total > 0 ? {
                starlink_satellites: [], // 實際數據在service中
                oneweb_satellites: [],
                total_selected: poolStats.total
            } : null })
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '未知錯誤'
            console.error('❌ SatelliteDataProvider: 動態池載入失敗:', error)
            dispatch({ type: 'SET_POOL_ERROR', payload: errorMessage })
        }
    }, [])

    // 刷新衛星數據
    const refreshSatellites = useCallback(async (forceRefresh: boolean = false) => {
        dispatch({ type: 'SET_LOADING', payload: true })
        
        try {
            const rawSatellites = await serviceRef.current.getVisibleSatellites(forceRefresh)
            
            // 🎯 關鍵改變：通過動態池過濾衛星數據
            const filteredSatellites = state.dynamicPool.enabled ? 
                dynamicPoolService.filterSatellitesByPool(rawSatellites) : 
                rawSatellites
            
            dispatch({ type: 'SET_SATELLITES', payload: filteredSatellites })
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '未知錯誤'
            console.error('❌ SatelliteDataProvider: 刷新衛星數據失敗:', error)
            dispatch({ type: 'SET_ERROR', payload: errorMessage })
        }
    }, [state.dynamicPool.enabled])

    // 更新配置
    const updateConfig = useCallback((newConfig: Partial<SatelliteDataServiceConfig>) => {
        dispatch({ type: 'UPDATE_CONFIG', payload: newConfig })
        serviceRef.current.updateConfig(newConfig)
        // 配置變更後立即刷新數據
        refreshSatellites(true)
    }, [refreshSatellites])

    // 設置星座
    const setConstellation = useCallback((constellation: 'starlink' | 'oneweb') => {
        dispatch({ type: 'SET_CONSTELLATION', payload: constellation })
        serviceRef.current.updateConfig({ constellation })
        // 星座變更後立即刷新數據
        refreshSatellites(true)
    }, [refreshSatellites])

    // 檢查系統健康狀態
    const checkSystemHealth = useCallback(async () => {
        try {
            const health = await serviceRef.current.getSystemHealth()
            dispatch({ type: 'SET_SYSTEM_HEALTH', payload: health })
        } catch (error) {
            console.error('❌ SatelliteDataProvider: 健康檢查失敗:', error)
        }
    }, [])

    // 切換池模式
    const togglePoolMode = useCallback((enabled: boolean) => {
        dispatch({ type: 'TOGGLE_POOL_MODE', payload: enabled })
        dynamicPoolService.togglePoolMode(enabled)
        // 切換後立即刷新數據
        refreshSatellites(true)
    }, [refreshSatellites])

    // 獲取池統計信息
    const getPoolStatistics = useCallback(() => {
        return dynamicPoolService.getPoolStatistics()
    }, [])

    // 初始化動態池
    useEffect(() => {
        loadDynamicPool()
    }, [loadDynamicPool])

    // 自動更新機制
    useEffect(() => {
        // 清除現有的定時器
        if (updateIntervalRef.current) {
            clearInterval(updateIntervalRef.current)
        }

        // 立即獲取一次數據
        refreshSatellites()

        // 設置定期更新
        updateIntervalRef.current = setInterval(() => {
            refreshSatellites()
        }, state.config.updateInterval)

        return () => {
            if (updateIntervalRef.current) {
                clearInterval(updateIntervalRef.current)
            }
        }
    }, [state.config.updateInterval, refreshSatellites])

    // 當服務配置變更時更新服務實例
    useEffect(() => {
        serviceRef.current.updateConfig(state.config)
    }, [state.config])

    const contextValue: SatelliteDataContextType = {
        state,
        dispatch,
        refreshSatellites,
        updateConfig,
        setConstellation,
        checkSystemHealth,
        // 動態池相關方法
        loadDynamicPool,
        togglePoolMode,
        getPoolStatistics
    }

    return (
        <SatelliteDataContext.Provider value={contextValue}>
            {children}
        </SatelliteDataContext.Provider>
    )
}

// 自定義Hook
export const useSatelliteData = (): SatelliteDataContextType => {
    const context = useContext(SatelliteDataContext)
    if (context === undefined) {
        throw new Error('useSatelliteData must be used within a SatelliteDataProvider')
    }
    return context
}

// 便利Hook - 只獲取衛星數據
export const useSatellites = () => {
    const { state } = useSatelliteData()
    return {
        satellites: state.satellites,
        loading: state.loading,
        error: state.error,
        lastUpdated: state.lastUpdated
    }
}

// 便利Hook - 只獲取配置相關
export const useSatelliteConfig = () => {
    const { state, updateConfig, setConstellation } = useSatelliteData()
    return {
        config: state.config,
        selectedConstellation: state.selectedConstellation,
        updateConfig,
        setConstellation
    }
}