/**
 * 數據同步測試組件
 * 用於測試 NetStack ↔ SimWorld ↔ Frontend 三層數據流
 */

import React from 'react'
import { 
  useDataSync, 
  useNetStackData, 
  useSimWorldData, 
  useSyncStatus, 
  useDataSourceStatus 
} from '../../contexts/DataSyncContext'

const DataSyncTest: React.FC = () => {
  const { forceSync } = useDataSync()
  const netStackData = useNetStackData()
  const simWorldData = useSimWorldData()
  const syncStatus = useSyncStatus()
  const dataSourceStatus = useDataSourceStatus()

  return (
    <div style={{ 
      position: 'fixed', 
      top: '100px', 
      left: '20px', 
      background: 'rgba(0, 0, 0, 0.8)', 
      color: 'white', 
      padding: '20px', 
      borderRadius: '8px',
      maxWidth: '400px',
      fontSize: '12px',
      zIndex: 9999
    }}>
      <h3>Data Sync Test Dashboard</h3>
      
      <div style={{ marginBottom: '10px' }}>
        <h4>NetStack Status:</h4>
        <div>Connected: {netStackData.isConnected ? '✅' : '❌'}</div>
        <div>Error: {netStackData.error || 'None'}</div>
        <div>Last Update: {netStackData.lastUpdate ? new Date(netStackData.lastUpdate).toLocaleTimeString() : 'Never'}</div>
      </div>

      <div style={{ marginBottom: '10px' }}>
        <h4>SimWorld Status:</h4>
        <div>Connected: {simWorldData.isConnected ? '✅' : '❌'}</div>
        <div>Satellites: {simWorldData.satellites.length}</div>
        <div>Error: {simWorldData.error || 'None'}</div>
        <div>Last Update: {simWorldData.lastUpdate ? new Date(simWorldData.lastUpdate).toLocaleTimeString() : 'Never'}</div>
      </div>

      <div style={{ marginBottom: '10px' }}>
        <h4>Sync Status:</h4>
        <div>Active: {syncStatus.isActive ? '🔄' : '⏸️'}</div>
        <div>Consistency: {syncStatus.consistency}</div>
        <div>Is Consistent: {syncStatus.isConsistent ? '✅' : '❌'}</div>
        <div>Errors: {syncStatus.errors.length}</div>
        <div>Last Sync: {syncStatus.lastSyncTime ? new Date(syncStatus.lastSyncTime).toLocaleTimeString() : 'Never'}</div>
      </div>

      <div style={{ marginBottom: '10px' }}>
        <h4>Data Source:</h4>
        <div>NetStack: {dataSourceStatus.netstack ? '✅' : '❌'}</div>
        <div>SimWorld: {dataSourceStatus.simworld ? '✅' : '❌'}</div>
        <div>Overall: {dataSourceStatus.overall}</div>
        <div>Data Source: {dataSourceStatus.dataSource}</div>
      </div>

      <button 
        onClick={forceSync}
        disabled={syncStatus.isActive}
        style={{
          background: syncStatus.isActive ? '#555' : '#007acc',
          color: 'white',
          border: 'none',
          padding: '8px 16px',
          borderRadius: '4px',
          cursor: syncStatus.isActive ? 'not-allowed' : 'pointer'
        }}
      >
        {syncStatus.isActive ? 'Syncing...' : 'Force Sync'}
      </button>

      {syncStatus.errors.length > 0 && (
        <div style={{ marginTop: '10px', background: 'rgba(255, 0, 0, 0.2)', padding: '8px', borderRadius: '4px' }}>
          <h4>Recent Errors:</h4>
          {syncStatus.errors.slice(-3).map((error, index) => (
            <div key={index} style={{ fontSize: '10px', marginBottom: '4px' }}>
              {error}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default DataSyncTest