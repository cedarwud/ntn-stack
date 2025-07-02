// src/App.tsx - 階段三重構版本
// 大幅減少Props傳遞，使用Context管理狀態

import { useMemo, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useDevices } from './hooks/useDevices'
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
import { AppStateProvider, useUIState, useSatelliteState, useHandoverState, useFeatureState } from './contexts/AppStateContext'
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

    // 設備管理Hook（保持原有邏輯）
    const {
        tempDevices,
        loading,
        apiStatus,
        hasTempDevices,
        fetchDevices: refreshDeviceData,
        setTempDevices: _setTempDevices,
        setHasTempDevices: _setHasTempDevices,
        applyDeviceChanges,
        deleteDeviceById,
        addNewDevice,
        updateDeviceField,
        cancelDeviceChanges,
        updateDevicePositionFromUAV,
    } = useDevices()

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

    // 排序設備數據
    const sortedDevicesForSidebar = useMemo(() => {
        return [...tempDevices].sort((a, b) => {
            const roleOrder: { [key: string]: number } = {
                receiver: 1,
                desired: 2,
                jammer: 3,
            }
            const roleA = roleOrder[a.role] || 99
            const roleB = roleOrder[b.role] || 99
            return roleA - roleB || a.id - b.id
        })
    }, [tempDevices])

    // 活躍設備計數
    const activeDevices = useMemo(() => {
        return countActiveDevices(tempDevices)
    }, [tempDevices])

    // 渲染活躍組件
    const renderActiveComponent = () => {
        if (uiState.activeComponent === '3DRT') {
            return (
                <SceneView
                    scene={currentScene}
                    skyfieldSatellites={satelliteState.skyfieldSatellites}
                    devices={tempDevices}
                    loading={loading}
                    satelliteEnabled={satelliteState.satelliteEnabled}
                    auto={uiState.auto}
                    manualDirection={uiState.manualDirection}
                    uavAnimation={uiState.uavAnimation}
                    selectedReceiverIds={uiState.selectedReceiverIds}
                    // 功能開關 - 直接傳遞feature state
                    {...featureState}
                    // 換手相關狀態
                    handoverState={handoverState.handoverState}
                    currentConnection={handoverState.currentConnection}
                    predictedConnection={handoverState.predictedConnection}
                    isTransitioning={handoverState.isTransitioning}
                    transitionProgress={handoverState.transitionProgress}
                    // 設備操作回調
                    onDeviceUpdate={updateDeviceField}
                    onSatelliteUpdate={satelliteState.setSkyfieldSatellites}
                    onAlgorithmResults={handoverState.setAlgorithmResults}
                    onCurrentConnectionChange={handoverState.setCurrentConnection}
                    onPredictedConnectionChange={handoverState.setPredictedConnection}
                    onTransitionChange={(isTransitioning, progress) => {
                        handoverState.setIsTransitioning(isTransitioning)
                        handoverState.setTransitionProgress(progress)
                    }}
                    // 衛星動畫控制
                    satelliteSpeedMultiplier={handoverState.handoverStableDuration}
                    onSatelliteSpeedChange={handoverState.setHandoverStableDuration}
                    handoverMode={handoverState.handoverMode}
                    onHandoverModeChange={handoverState.setHandoverMode}
                />
            )
        } else if (uiState.activeComponent === '2DRT') {
            return (
                <SceneViewer
                    scene={currentScene}
                    skyfieldSatellites={satelliteState.skyfieldSatellites}
                    devices={tempDevices}
                    loading={loading}
                    satelliteEnabled={satelliteState.satelliteEnabled}
                    onDeviceUpdate={updateDeviceField}
                    onSatelliteUpdate={satelliteState.setSkyfieldSatellites}
                    selectedReceiverIds={uiState.selectedReceiverIds}
                />
            )
        }
        return <div>未知組件</div>
    }

    return (
        <div className="App">
            <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
                {/* 導航欄 */}
                <ErrorBoundary fallback={<div>導航欄發生錯誤</div>}>
                    <Navbar 
                        activeDevicesCount={activeDevices}
                        apiStatus={apiStatus}
                    />
                </ErrorBoundary>

                {/* 主要內容區域 */}
                <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                    <Layout
                        sidebar={
                            <ErrorBoundary fallback={<div>側邊欄發生錯誤</div>}>
                                <EnhancedSidebar
                                    // 設備相關
                                    tempDevices={sortedDevicesForSidebar}
                                    loading={loading}
                                    hasTempDevices={hasTempDevices}
                                    onApplyChanges={applyDeviceChanges}
                                    onDeleteDevice={deleteDeviceById}
                                    onAddDevice={addNewDevice}
                                    onCancelChanges={cancelDeviceChanges}
                                    onDeviceUpdate={updateDeviceField}
                                    refreshDeviceData={refreshDeviceData}
                                    updateDevicePositionFromUAV={updateDevicePositionFromUAV}
                                    
                                    // UI控制 - 通過回調傳遞
                                    activeComponent={uiState.activeComponent}
                                    onActiveComponentChange={uiState.setActiveComponent}
                                    auto={uiState.auto}
                                    onAutoChange={uiState.setAuto}
                                    manualDirection={uiState.manualDirection}
                                    onManualDirectionChange={uiState.setManualDirection}
                                    uavAnimation={uiState.uavAnimation}
                                    onUavAnimationChange={uiState.setUavAnimation}
                                    selectedReceiverIds={uiState.selectedReceiverIds}
                                    onSelectedReceiverIdsChange={uiState.setSelectedReceiverIds}
                                    
                                    // 衛星控制
                                    satelliteEnabled={satelliteState.satelliteEnabled}
                                    onSatelliteEnabledChange={satelliteState.setSatelliteEnabled}
                                    
                                    // 功能開關 - 使用批量更新
                                    featureState={featureState}
                                    onFeatureStateChange={featureState.updateFeatureState}
                                />
                            </ErrorBoundary>
                        }
                        content={
                            <ErrorBoundary fallback={<div>主視圖發生錯誤</div>}>
                                {renderActiveComponent()}
                            </ErrorBoundary>
                        }
                        activeComponent={uiState.activeComponent}
                    />
                </div>
            </div>
            
            {/* Toast 通知系統 */}
            <ToastNotification />
        </div>
    )
}

// ==================== 主要App組件 ====================
const App: React.FC<AppProps> = ({ activeView = 'stereogram' }) => {
    const { scenes } = useParams<{ scenes: string }>()
    const currentScene = scenes || 'nycu'
    const initialComponent = activeView === 'stereogram' ? '3DRT' : '2DRT'

    return (
        <ErrorBoundary fallback={<div>應用程式發生嚴重錯誤</div>}>
            <StrategyProvider>
                <DataSyncProvider>
                    <AppStateProvider initialActiveComponent={initialComponent}>
                        <AppContent currentScene={currentScene} />
                    </AppStateProvider>
                </DataSyncProvider>
            </StrategyProvider>
        </ErrorBoundary>
    )
}

export default App