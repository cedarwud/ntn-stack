/**
 * App級別的Providers整合
 * 將所有Context Providers統一管理
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
                minElevation: 10, // 使用標準服務門檻
                maxCount: 40,     // 支援更多衛星顯示
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