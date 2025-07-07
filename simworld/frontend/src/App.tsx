// src/App.tsx - 階段四重構版本
// 繼續減少Props傳遞，由組件直接使用Context

import { useMemo, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useToast } from './hooks/useToast'
import SceneViewer from './components/scenes/FloorView'
import SceneView from './components/scenes/StereogramView'
import Layout from './components/layout/Layout'
import ErrorBoundary from './components/shared/ui/feedback/ErrorBoundary'
import Navbar from './components/layout/Navbar'
import EnhancedSidebar from './components/layout/EnhancedSidebar'
import ToastNotification from './components/shared/ui/feedback/ToastNotification'
import { backgroundHealthMonitor } from './services/healthMonitor'
import { countActiveDevices } from './utils/deviceUtils'
import { DataSyncProvider } from './contexts/DataSyncContext'
import { StrategyProvider } from './contexts/StrategyContext'
import { AppStateProvider } from './contexts/AppStateContext'
import { DeviceProvider, useDeviceContext } from './contexts/DeviceContext'
import {
    useUIState,
    useSatelliteState,
    useHandoverState,
    useFeatureState,
} from './contexts/appStateHooks'
import './styles/App.scss'

interface AppProps {
    activeView?: string
}

// ==================== 主要應用邏輯組件 ====================
const AppContent: React.FC<{ currentScene: string }> = ({ currentScene }) => {
    // 使用專門化的狀態Hooks，減少Context耦合
    const uiState = useUIState()
    const satelliteState = useSatelliteState()
    const handoverState = useHandoverState()
    const featureState = useFeatureState()
    const {
        tempDevices,
        updateDevicePositionFromUAV,
        fetchDevices: refreshDeviceData,
    } = useDeviceContext()

    // Toast通知系統
    const { showToast } = useToast()

    // 網頁載入時執行健康檢查
    useEffect(() => {
        backgroundHealthMonitor.setToastFunction(showToast)
        const timer = setTimeout(() => {
            backgroundHealthMonitor.startInitialCheck()
        }, 3000)

        console.log('🔍 網頁載入時將執行系統健康檢查')
        return () => clearTimeout(timer)
    }, [showToast])

    // 活躍設備計數 (保留以備後用)
    const _activeDevices = useMemo(() => {
        return countActiveDevices(tempDevices)
    }, [tempDevices])

    const handleUAVPositionUpdate = useCallback(
        (pos: [number, number, number], deviceId?: number) => {
            if (
                deviceId === undefined ||
                !uiState.selectedReceiverIds.includes(deviceId)
            ) {
                return
            }
            updateDevicePositionFromUAV(deviceId, pos)
        },
        [uiState.selectedReceiverIds, updateDevicePositionFromUAV]
    )

    const handleSceneViewManualControl = useCallback(
        (direction: string | null) => {
            if (uiState.selectedReceiverIds.length === 0) {
                return
            }
            uiState.setManualDirection(direction)
        },
        [uiState]
    )

    const handleHandoverEvent = useCallback(
        (event: Record<string, unknown>) => {
            console.log('換手事件:', event)
        },
        []
    )

    // 渲染活躍組件
    const renderActiveComponent = () => {
        if (uiState.activeComponent === '3DRT') {
            return (
                <SceneView
                    devices={tempDevices}
                    uiState={uiState}
                    featureState={featureState}
                    handoverState={handoverState}
                    satelliteState={satelliteState}
                    sceneName={currentScene}
                    onUAVPositionUpdate={handleUAVPositionUpdate}
                    onManualControl={handleSceneViewManualControl}
                    onHandoverEvent={handleHandoverEvent}
                />
            )
        } else if (uiState.activeComponent === '2DRT') {
            return (
                <SceneViewer
                    devices={tempDevices}
                    refreshDeviceData={refreshDeviceData}
                    sceneName={currentScene}
                />
            )
        }
        return <div>未知組件</div>
    }

    return (
        <div className="App">
            <div
                style={{
                    height: '100vh',
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                <ErrorBoundary fallback={<div>導航欄發生錯誤</div>}>
                    <Navbar
                        onMenuClick={uiState.setActiveComponent}
                        activeComponent={uiState.activeComponent}
                        currentScene={currentScene}
                    />
                </ErrorBoundary>
                <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                    <Layout
                        sidebar={
                            <ErrorBoundary fallback={<div>側邊欄發生錯誤</div>}>
                                <EnhancedSidebar
                                    activeComponent={uiState.activeComponent}
                                />
                            </ErrorBoundary>
                        }
                    >
                        <ToastNotification />
                        {renderActiveComponent()}
                    </Layout>
                </div>
            </div>
        </div>
    )
}

const App: React.FC<AppProps> = ({ activeView = 'stereogram' }) => {
    const { sceneName } = useParams<{ sceneName: string }>()
    const currentScene = sceneName || 'default_scene'

    return (
        <ErrorBoundary fallback={<div>應用程式發生嚴重錯誤</div>}>
            <StrategyProvider>
                <AppStateProvider>
                    <DeviceProvider>
                        <DataSyncProvider>
                            <AppContent
                                key={currentScene}
                                currentScene={currentScene}
                            />
                        </DataSyncProvider>
                    </DeviceProvider>
                </AppStateProvider>
            </StrategyProvider>
        </ErrorBoundary>
    )
}

export default App
