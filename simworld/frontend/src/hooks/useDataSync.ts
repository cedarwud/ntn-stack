/**
 * DataSync 相關的 Hook 函數
 * 分離出來以避免 Fast Refresh 警告
 */
import { useContext } from 'react'
import { DataSyncContext } from '../contexts/DataSyncContext'

// 自定義 Hook
export const useDataSync = () => {
    const context = useContext(DataSyncContext)
    if (!context) {
        throw new Error('useDataSync must be used within a DataSyncProvider')
    }
    return context
}

// 專用 Hooks
export const useNetStackData = () => {
    const { state } = useDataSync()
    return {
        coreSync: state.netstack.coreSync,
        isConnected: state.netstack.isConnected,
        error: state.netstack.error,
        lastUpdate: state.netstack.lastUpdate,
    }
}

export const useSimWorldData = () => {
    const { state } = useDataSync()
    return {
        satellites: state.simworld.satellites,
        isConnected: state.simworld.isConnected,
        error: state.simworld.error,
        lastUpdate: state.simworld.lastUpdate,
    }
}

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

export const useDataSourceStatus = () => {
    const { state, getDataSourceStatus } = useDataSync()
    return {
        ...getDataSourceStatus(),
        dataSource: state.ui.dataSource,
        showIndicators: state.ui.showDataSourceIndicators,
        autoSync: state.ui.autoSync,
    }
}
