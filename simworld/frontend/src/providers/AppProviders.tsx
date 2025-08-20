/**
 * App級別的Providers整合
 * 將所有Context Providers統一管理
 * 🚀 修復：移除 SatelliteDataBridge，避免循環依賴
 */

import React from 'react'
import { SatelliteDataProvider } from '../contexts/SatelliteDataContext'

interface AppProvidersProps {
    children: React.ReactNode
}

const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
    return (
        <SatelliteDataProvider
            initialConfig={{
                minElevation: 5,  // 會根據星座動態調整 (Starlink 5°, OneWeb 10°)
                maxCount: 15,     // Starlink: 10-15顆, OneWeb: 3-6顆
                observerLat: 24.9441667, // NTPU觀測點
                observerLon: 121.3713889,
                constellation: 'starlink',
                updateInterval: 5000 // 5秒更新間隔
            }}
        >
            {children}
        </SatelliteDataProvider>
    )
}

export default AppProviders