// src/App.tsx - Phase 4 優化版本 
// 實現懶載入和性能優化

import { useMemo, useEffect, useCallback, lazy, Suspense } from 'react'
import { useParams } from 'react-router-dom'
import { useToast } from './hooks/useToast'

// 懶載入 3D 場景組件
const SceneViewer = lazy(() => import('./components/scenes/FloorView'))
const SceneView = lazy(() => import('./components/scenes/StereogramView'))
import Layout from './components/layout/Layout'
import ErrorBoundary from './components/shared/ui/feedback/ErrorBoundary'
import Navbar from './components/layout/Navbar'
// 🚀 使用重構後的統一數據源版本
import Sidebar from './components/layout/Sidebar.refactored'
import ToastNotification from './components/shared/ui/feedback/ToastNotification'
import { backgroundHealthMonitor } from './services/healthMonitor'
import { countActiveDevices } from './utils/deviceUtils'
import { DataSyncProvider } from './contexts/DataSyncContext'
import { StrategyProvider } from './contexts/StrategyContext'
import { AppStateProvider } from './contexts/AppStateContext'
import { DeviceProvider, useDeviceContext } from './contexts/DeviceContext'
// 🚀 引入重構後的統一Providers
import AppProviders from './providers/AppProviders'
import SatelliteDataBridge from './providers/SatelliteDataBridge'
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
        loading,
        apiStatus,
        updateDeviceField,
        deleteDeviceById,
        addNewDevice,
        applyDeviceChanges,
        cancelDeviceChanges,
        hasTempDevices,
    } = useDeviceContext()

    // Toast通知系統
    const { showToast } = useToast()

    // 網頁載入時執行健康檢查
    useEffect(() => {
        // console.log('🏗️ AppContent 組件掛載，場景:', currentScene)
        backgroundHealthMonitor.setToastFunction(showToast)
        const timer = setTimeout(() => {
            backgroundHealthMonitor.startInitialCheck()
        }, 3000)

        // console.log('🔍 網頁載入時將執行系統健康檢查')
        return () => {
            console.log('🔄 AppContent 組件卸載，場景:', currentScene)
            clearTimeout(timer)
        }
    }, [showToast, currentScene])

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

    // 載入指示器組件
    const LoadingComponent = () => (
        <div className="loading-container" style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            backgroundColor: '#1a1a1a',
            color: '#ffffff'
        }}>
            <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', marginBottom: '10px' }}>🛰️ 載入衛星可視化系統中...</div>
                <div style={{ fontSize: '14px', opacity: 0.7 }}>正在初始化 3D 渲染引擎</div>
            </div>
        </div>
    )

    // 渲染活躍組件 - 使用 Suspense 懶載入
    const renderActiveComponent = () => {
        if (uiState.activeComponent === '3DRT') {
            return (
                <Suspense fallback={<LoadingComponent />}>
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
                </Suspense>
            )
        } else if (uiState.activeComponent === '2DRT') {
            return (
                <Suspense fallback={<LoadingComponent />}>
                    <SceneViewer
                        devices={tempDevices}
                        refreshDeviceData={refreshDeviceData}
                        sceneName={currentScene}
                    />
                </Suspense>
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
                        activeComponent={uiState.activeComponent}
                        sidebar={
                            <ErrorBoundary fallback={<div>側邊欄發生錯誤</div>}>
                                <Sidebar
                                    devices={tempDevices}
                                    loading={loading}
                                    apiStatus={apiStatus}
                                    onDeviceChange={updateDeviceField}
                                    onDeleteDevice={deleteDeviceById}
                                    onAddDevice={addNewDevice}
                                    onApply={applyDeviceChanges}
                                    onCancel={cancelDeviceChanges}
                                    hasTempDevices={hasTempDevices}
                                    auto={uiState.auto}
                                    onAutoChange={uiState.setAuto}
                                    onManualControl={uiState.setManualDirection}
                                    activeComponent={uiState.activeComponent}
                                    uavAnimation={uiState.uavAnimation}
                                    onUavAnimationChange={
                                        uiState.setUavAnimation
                                    }
                                    onSelectedReceiversChange={
                                        uiState.setSelectedReceiverIds
                                    }
                                    onSatelliteDataUpdate={
                                        satelliteState.setSkyfieldSatellites
                                    }
                                    satelliteEnabled={
                                        satelliteState.satelliteEnabled
                                    }
                                    onSatelliteEnabledChange={
                                        satelliteState.setSatelliteEnabled
                                    }

                                    satelliteUavConnectionEnabled={
                                        featureState.satelliteUavConnectionEnabled
                                    }
                                    onSatelliteUavConnectionChange={(enabled) =>
                                        featureState.updateFeatureState({
                                            satelliteUavConnectionEnabled:
                                                enabled,
                                        })
                                    }
                                    satelliteSpeedMultiplier={
                                        handoverState.handoverStableDuration
                                    }
                                    onSatelliteSpeedChange={
                                        handoverState.setHandoverStableDuration
                                    }
                                    onHandoverStateChange={
                                        handoverState.setHandoverState
                                    }
                                    onCurrentConnectionChange={
                                        handoverState.setCurrentConnection
                                    }
                                    onPredictedConnectionChange={
                                        handoverState.setPredictedConnection
                                    }
                                    onTransitionChange={(
                                        isTransitioning,
                                        progress
                                    ) => {
                                        handoverState.setIsTransitioning(
                                            isTransitioning
                                        )
                                        handoverState.setTransitionProgress(
                                            progress
                                        )
                                    }}
                                    onAlgorithmResults={
                                        handoverState.setAlgorithmResults
                                    }
                                    satelliteMovementSpeed={
                                        handoverState.satelliteMovementSpeed
                                    }
                                    onSatelliteMovementSpeedChange={
                                        handoverState.setSatelliteMovementSpeed
                                    }
                                    handoverTimingSpeed={
                                        handoverState.handoverTimingSpeed
                                    }
                                    onHandoverTimingSpeedChange={
                                        handoverState.setHandoverTimingSpeed
                                    }
                                    handoverStableDuration={
                                        handoverState.handoverStableDuration
                                    }
                                    onHandoverStableDurationChange={
                                        handoverState.setHandoverStableDuration
                                    }
                                    // 星座切換控制
                                    selectedConstellation={
                                        satelliteState.selectedConstellation
                                    }
                                    onConstellationChange={
                                        satelliteState.setSelectedConstellation
                                    }
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

const App: React.FC<AppProps> = ({
    activeView: _activeView = 'stereogram',
}) => {
    const { scenes: sceneName } = useParams<{ scenes: string }>()
    const currentScene = sceneName || 'default_scene'

    return (
        <ErrorBoundary fallback={<div>應用程式發生嚴重錯誤</div>}>
            <StrategyProvider>
                <DeviceProvider>
                    {/* 🚀 修復：正確的Provider嵌套順序 */}
                    <AppProviders>
                        <AppStateProvider>
                            {/* 🌉 SatelliteDataBridge：現在可以同時訪問兩個Context */}
                            <SatelliteDataBridge>
                                <DataSyncProvider>
                                    <AppContent
                                        key={currentScene}
                                        currentScene={currentScene}
                                    />
                                </DataSyncProvider>
                            </SatelliteDataBridge>
                        </AppStateProvider>
                    </AppProviders>
                </DeviceProvider>
            </StrategyProvider>
        </ErrorBoundary>
    )
}

export default App
