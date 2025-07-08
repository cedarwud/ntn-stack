/**
 * 跨組件數據同步上下文
 * 建立 NetStack ↔ SimWorld ↔ Frontend 三層數據流
 */

import React, {
    createContext,
    useContext,
    useReducer,
    useEffect,
    useCallback,
    useRef,
} from 'react'
import { netStackApi, CoreSyncStatus } from '../services/netstack-api'
import {
    simWorldApi,
    SatellitePosition,
    useVisibleSatellites,
} from '../services/simworld-api'

// 全局數據狀態接口
export interface GlobalDataState {
    // NetStack 狀態
    netstack: {
        coreSync: CoreSyncStatus | null
        isConnected: boolean
        lastUpdate: number
        error: string | null
    }

    // SimWorld 狀態
    simworld: {
        satellites: SatellitePosition[]
        isConnected: boolean
        lastUpdate: number
        error: string | null
    }

    // 同步狀態
    sync: {
        isActive: boolean
        lastSyncTime: number
        syncErrors: string[]
        dataConsistency: 'synced' | 'partial' | 'out_of_sync'
    }

    // UI 狀態
    ui: {
        dataSource: 'real' | 'simulated' | 'mixed'
        showDataSourceIndicators: boolean
        realTimeUpdates: boolean
    }
}

// 操作類型
type DataSyncAction =
    | {
          type: 'UPDATE_NETSTACK_STATUS'
          payload: { status?: CoreSyncStatus; error?: string }
      }
    | {
          type: 'UPDATE_SIMWORLD_SATELLITES'
          payload: { satellites?: SatellitePosition[]; error?: string }
      }
    | {
          type: 'SET_CONNECTION_STATUS'
          service: 'netstack' | 'simworld'
          connected: boolean
      }
    | {
          type: 'SET_SYNC_STATUS'
          payload: {
              isActive: boolean
              consistency?: GlobalDataState['sync']['dataConsistency']
          }
      }
    | { type: 'ADD_SYNC_ERROR'; error: string }
    | { type: 'CLEAR_SYNC_ERRORS' }
    | { type: 'UPDATE_UI_STATE'; payload: Partial<GlobalDataState['ui']> }
    | { type: 'FORCE_SYNC' }

// 初始狀態
const initialState: GlobalDataState = {
    netstack: {
        coreSync: null,
        isConnected: false,
        lastUpdate: 0,
        error: null,
    },
    simworld: {
        satellites: [],
        isConnected: false,
        lastUpdate: 0,
        error: null,
    },
    sync: {
        isActive: false,
        lastSyncTime: 0,
        syncErrors: [],
        dataConsistency: 'out_of_sync',
    },
    ui: {
        dataSource: 'real',
        showDataSourceIndicators: true,
        realTimeUpdates: true,
    },
}

// Reducer
function dataSyncReducer(
    state: GlobalDataState,
    action: DataSyncAction
): GlobalDataState {
    switch (action.type) {
        case 'UPDATE_NETSTACK_STATUS':
            return {
                ...state,
                netstack: {
                    ...state.netstack,
                    coreSync: action.payload.status || state.netstack.coreSync,
                    error: action.payload.error || null,
                    lastUpdate: Date.now(),
                    isConnected: !action.payload.error,
                },
            }

        case 'UPDATE_SIMWORLD_SATELLITES':
            return {
                ...state,
                simworld: {
                    ...state.simworld,
                    satellites:
                        action.payload.satellites || state.simworld.satellites,
                    error: action.payload.error || null,
                    lastUpdate: Date.now(),
                    isConnected: !action.payload.error,
                },
            }

        case 'SET_CONNECTION_STATUS':
            return {
                ...state,
                [action.service]: {
                    ...state[action.service],
                    isConnected: action.connected,
                    error: action.connected
                        ? null
                        : `${action.service} connection failed`,
                },
            }

        case 'SET_SYNC_STATUS':
            return {
                ...state,
                sync: {
                    ...state.sync,
                    isActive: action.payload.isActive,
                    lastSyncTime: action.payload.isActive
                        ? Date.now()
                        : state.sync.lastSyncTime,
                    dataConsistency:
                        action.payload.consistency ||
                        state.sync.dataConsistency,
                },
            }

        case 'ADD_SYNC_ERROR':
            return {
                ...state,
                sync: {
                    ...state.sync,
                    syncErrors: [
                        ...state.sync.syncErrors.slice(-9),
                        action.error,
                    ], // 最多保留10個錯誤
                },
            }

        case 'CLEAR_SYNC_ERRORS':
            return {
                ...state,
                sync: {
                    ...state.sync,
                    syncErrors: [],
                },
            }

        case 'UPDATE_UI_STATE':
            return {
                ...state,
                ui: {
                    ...state.ui,
                    ...action.payload,
                },
            }

        case 'FORCE_SYNC':
            return {
                ...state,
                sync: {
                    ...state.sync,
                    isActive: true,
                    lastSyncTime: Date.now(),
                },
            }

        default:
            return state
    }
}

// 上下文
const DataSyncContext = createContext<{
    state: GlobalDataState
    dispatch: React.Dispatch<DataSyncAction>
    // 便利方法
    forceSync: () => void
    getDataSourceStatus: () => {
        netstack: boolean
        simworld: boolean
        overall: string
    }
    isDataConsistent: () => boolean
} | null>(null)

// Provider 組件
export const DataSyncProvider: React.FC<{ children: React.ReactNode }> = ({
    children,
}) => {
    const [state, dispatch] = useReducer(dataSyncReducer, initialState)

    // 使用真實衛星數據 hook - 減少更新頻率
    const {
        satellites: realSatellites,
        error: satellitesError,
    } = useVisibleSatellites(5, 15, 60000) // 5度仰角，最多15顆，60秒更新

    // 強制同步方法
    const forceSync = useCallback(async () => {
        dispatch({ type: 'SET_SYNC_STATUS', payload: { isActive: true } })

        try {
            // 並行獲取 NetStack 和 SimWorld 數據
            const [netstackData, simworldData] = await Promise.allSettled([
                netStackApi.getCoreSync(),
                simWorldApi.getVisibleSatellites(5, 30),
            ])

            // 處理 NetStack 結果
            if (netstackData.status === 'fulfilled') {
                dispatch({
                    type: 'UPDATE_NETSTACK_STATUS',
                    payload: { status: netstackData.value },
                })
            } else {
                dispatch({
                    type: 'UPDATE_NETSTACK_STATUS',
                    payload: {
                        error:
                            netstackData.reason?.message ||
                            'NetStack connection failed',
                    },
                })
                dispatch({
                    type: 'ADD_SYNC_ERROR',
                    error: `NetStack: ${netstackData.reason?.message}`,
                })
            }

            // 處理 SimWorld 結果
            if (simworldData.status === 'fulfilled') {
                dispatch({
                    type: 'UPDATE_SIMWORLD_SATELLITES',
                    payload: {
                        satellites: simworldData.value.visible_satellites,
                    },
                })
            } else {
                dispatch({
                    type: 'UPDATE_SIMWORLD_SATELLITES',
                    payload: {
                        error:
                            simworldData.reason?.message ||
                            'SimWorld connection failed',
                    },
                })
                dispatch({
                    type: 'ADD_SYNC_ERROR',
                    error: `SimWorld: ${simworldData.reason?.message}`,
                })
            }

            // 計算數據一致性
            const netstackOk = netstackData.status === 'fulfilled'
            const simworldOk = simworldData.status === 'fulfilled'

            let consistency: GlobalDataState['sync']['dataConsistency'] =
                'out_of_sync'
            if (netstackOk && simworldOk) {
                consistency = 'synced'
            } else if (netstackOk || simworldOk) {
                consistency = 'partial'
            }

            dispatch({
                type: 'SET_SYNC_STATUS',
                payload: { isActive: false, consistency },
            })
        } catch (error) {
            dispatch({ type: 'ADD_SYNC_ERROR', error: `Sync failed: ${error}` })
            dispatch({
                type: 'SET_SYNC_STATUS',
                payload: { isActive: false, consistency: 'out_of_sync' },
            })
        }
    }, [])

    // 獲取數據源狀態
    const getDataSourceStatus = useCallback(() => {
        const netstack = state.netstack.isConnected
        const simworld = state.simworld.isConnected

        let overall = 'disconnected'
        if (netstack && simworld) {
            overall = 'fully_connected'
        } else if (netstack || simworld) {
            overall = 'partially_connected'
        }

        return { netstack, simworld, overall }
    }, [state.netstack.isConnected, state.simworld.isConnected])

    // 檢查數據一致性
    const isDataConsistent = useCallback(() => {
        return state.sync.dataConsistency === 'synced'
    }, [state.sync.dataConsistency])

    // 自動處理 SimWorld 衛星數據更新
    useEffect(() => {
        if (realSatellites && realSatellites.length > 0) {
            dispatch({
                type: 'UPDATE_SIMWORLD_SATELLITES',
                payload: { satellites: realSatellites },
            })
        }

        if (satellitesError) {
            dispatch({
                type: 'UPDATE_SIMWORLD_SATELLITES',
                payload: { error: satellitesError },
            })
        }
    }, [realSatellites, satellitesError])

    // 定期自動同步
    useEffect(() => {
        if (!state.ui.realTimeUpdates) return

        // 每120秒自動同步（減少頻率）
        const interval = setInterval(forceSync, 120000)

        return () => clearInterval(interval)
    }, [forceSync, state.ui.realTimeUpdates]) // 移除 state.sync.syncErrors 避免頻繁重啟

    // 自動更新 UI 數據源狀態 - 修復無限循環問題
    useEffect(() => {
        const netstack = state.netstack.isConnected
        const simworld = state.simworld.isConnected

        let dataSource: GlobalDataState['ui']['dataSource'] = 'simulated'
        if (netstack && simworld) {
            dataSource = 'real'
        } else if (netstack || simworld) {
            dataSource = 'mixed'
        }

        if (dataSource !== state.ui.dataSource) {
            dispatch({ type: 'UPDATE_UI_STATE', payload: { dataSource } })
        }
    }, [
        state.netstack.isConnected,
        state.simworld.isConnected,
        state.ui.dataSource,
    ])

    // 監控同步狀態並記錄日誌（減少日誌頻率）
    const lastLogTimeRef = useRef(0)
    useEffect(() => {
        const now = Date.now()
        const timeSinceLastLog = now - lastLogTimeRef.current

        // 只在有錯誤時或每10秒記錄一次
        if (state.sync.syncErrors.length > 0 || timeSinceLastLog > 10000) {
            if (state.sync.isActive) {
                // 移除重複的同步開始日誌
            } else {
                // 只在狀態變化或有錯誤時記錄
                if (state.sync.syncErrors.length > 0) {
                    console.warn(
                        '⚠️ 同步錯誤:',
                        state.sync.syncErrors.slice(-3)
                    )
                }
                lastLogTimeRef.current = now
            }
        }
    }, [
        state.sync.isActive,
        state.sync.dataConsistency,
        state.sync.syncErrors.length,
        state.sync.syncErrors,
    ])

    return (
        <DataSyncContext.Provider
            value={{
                state,
                dispatch,
                forceSync,
                getDataSourceStatus,
                isDataConsistent,
            }}
        >
            {children}
        </DataSyncContext.Provider>
    )
}

// 自定義 Hook
// eslint-disable-next-line react-refresh/only-export-components
export const useDataSync = () => {
    const context = useContext(DataSyncContext)
    if (!context) {
        throw new Error('useDataSync must be used within a DataSyncProvider')
    }
    return context
}

// 專用 Hooks
// eslint-disable-next-line react-refresh/only-export-components
export const useNetStackData = () => {
    const { state } = useDataSync()
    return {
        coreSync: state.netstack.coreSync,
        isConnected: state.netstack.isConnected,
        error: state.netstack.error,
        lastUpdate: state.netstack.lastUpdate,
    }
}

// eslint-disable-next-line react-refresh/only-export-components
export const useSimWorldData = () => {
    const { state } = useDataSync()
    return {
        satellites: state.simworld.satellites,
        isConnected: state.simworld.isConnected,
        error: state.simworld.error,
        lastUpdate: state.simworld.lastUpdate,
    }
}

// eslint-disable-next-line react-refresh/only-export-components
export const useSyncStatus = () => {
    const { state, forceSync, isDataConsistent } = useDataSync()
    return {
        isActive: state.sync.isActive,
        lastSyncTime: state.sync.lastSyncTime,
        errors: state.sync.syncErrors,
        consistency: state.sync.dataConsistency,
        isConsistent: isDataConsistent(),
        forceSync,
    }
}

// eslint-disable-next-line react-refresh/only-export-components
export const useDataSourceStatus = () => {
    const { state, getDataSourceStatus } = useDataSync()
    return {
        ...getDataSourceStatus(),
        dataSource: state.ui.dataSource,
        showIndicators: state.ui.showDataSourceIndicators,
    }
}

export default DataSyncContext
