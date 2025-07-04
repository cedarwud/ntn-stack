// src/App.tsx - 階段三重構版本
// 大幅減少Props傳遞，使用Context管理狀態

import { useMemo, useEffect, useCallback } from 'react'
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

    // 活躍設備計數 (保留以備後用)
    const _activeDevices = useMemo(() => {
        return countActiveDevices(tempDevices)
    }, [tempDevices])

    // 優化的回調函數
    const handleAutoChange = useCallback((newAuto: boolean) => {
        uiState.setAuto(newAuto)
        // 當自動飛行開啟時，自動關閉手動控制
        if (newAuto && featureState.manualControlEnabled) {
            featureState.updateFeatureState({ manualControlEnabled: false })
        }
    }, [uiState.setAuto, featureState.manualControlEnabled, featureState.updateFeatureState])

    const handleManualControl = useCallback((direction: string | null) => {
        // 檢查是否有選中的接收器
        if (uiState.selectedReceiverIds.length === 0) {
            console.log('沒有選中的 receiver，無法控制 UAV')
            return
        }
        uiState.setManualDirection(direction)
    }, [uiState.selectedReceiverIds, uiState.setManualDirection])

    const handleUAVPositionUpdate = useCallback((pos: [number, number, number], deviceId?: number) => {
        // 檢查設備ID是否在選中的接收器列表中
        if (deviceId === undefined || !uiState.selectedReceiverIds.includes(deviceId)) {
            return
        }
        updateDevicePositionFromUAV(deviceId, pos)
    }, [uiState.selectedReceiverIds, updateDevicePositionFromUAV])

    const handleSceneViewManualControl = useCallback((direction: string | null) => {
        // 檢查是否有選中的接收器
        if (uiState.selectedReceiverIds.length === 0) {
            console.log('沒有選中的 receiver，無法控制 UAV')
            return
        }
        uiState.setManualDirection(direction)
    }, [uiState.selectedReceiverIds, uiState.setManualDirection])

    const handleHandoverEvent = useCallback((event: Record<string, unknown>) => {
        console.log('換手事件:', event)
    }, [])

    const handleTransitionChange = useCallback((isTransitioning: boolean, progress: number) => {
        handoverState.setIsTransitioning(isTransitioning)
        handoverState.setTransitionProgress(progress)
    }, [handoverState.setIsTransitioning, handoverState.setTransitionProgress])

    // 渲染活躍組件
    const renderActiveComponent = () => {
        if (uiState.activeComponent === '3DRT') {
            return (
                <SceneView
                    devices={tempDevices}
                    auto={uiState.auto}
                    manualDirection={uiState.manualDirection}
                    onManualControl={handleSceneViewManualControl}
                    onUAVPositionUpdate={handleUAVPositionUpdate}
                    uavAnimation={uiState.uavAnimation}
                    selectedReceiverIds={uiState.selectedReceiverIds}
                    satellites={satelliteState.satelliteEnabled ? satelliteState.skyfieldSatellites : []}
                    sceneName={currentScene}
                    
                    // 階段四功能狀態
                    interferenceVisualizationEnabled={featureState.interferenceVisualizationEnabled}
                    sinrHeatmapEnabled={featureState.sinrHeatmapEnabled}
                    aiRanVisualizationEnabled={featureState.aiRanVisualizationEnabled}
                    sionna3DVisualizationEnabled={featureState.sionna3DVisualizationEnabled}
                    realTimeMetricsEnabled={featureState.realTimeMetricsEnabled}
                    interferenceAnalyticsEnabled={featureState.interferenceAnalyticsEnabled}
                    
                    // 階段五功能狀態
                    uavSwarmCoordinationEnabled={featureState.uavSwarmCoordinationEnabled}
                    meshNetworkTopologyEnabled={featureState.meshNetworkTopologyEnabled}
                    satelliteUavConnectionEnabled={featureState.satelliteUavConnectionEnabled}
                    failoverMechanismEnabled={featureState.failoverMechanismEnabled}
                    
                    // 階段六功能狀態
                    predictionPath3DEnabled={featureState.predictionPath3DEnabled}
                    predictionAccuracyDashboardEnabled={featureState.predictionAccuracyDashboardEnabled}
                    coreNetworkSyncEnabled={featureState.coreNetworkSyncEnabled}
                    
                    // Stage 3 功能
                    realtimePerformanceMonitorEnabled={featureState.realtimePerformanceMonitorEnabled}
                    scenarioTestEnvironmentEnabled={featureState.scenarioTestEnvironmentEnabled}
                    
                    // 3D 換手動畫
                    handover3DAnimationEnabled={true}
                    handoverState={handoverState.handoverState}
                    currentConnection={handoverState.currentConnection}
                    predictedConnection={handoverState.predictedConnection}
                    isTransitioning={handoverState.isTransitioning}
                    transitionProgress={handoverState.transitionProgress}
                    onHandoverEvent={handleHandoverEvent}
                    
                    // 階段七功能狀態
                    e2ePerformanceMonitoringEnabled={featureState.e2ePerformanceMonitoringEnabled}
                    testResultsVisualizationEnabled={featureState.testResultsVisualizationEnabled}
                    performanceTrendAnalysisEnabled={featureState.performanceTrendAnalysisEnabled}
                    automatedReportGenerationEnabled={featureState.automatedReportGenerationEnabled}
                    
                    // 階段八功能狀態
                    predictiveMaintenanceEnabled={featureState.predictiveMaintenanceEnabled}
                    intelligentRecommendationEnabled={featureState.intelligentRecommendationEnabled}
                    
                    // 衛星功能狀態
                    satelliteEnabled={satelliteState.satelliteEnabled}
                    satelliteSpeedMultiplier={1}
                    handoverStableDuration={handoverState.handoverStableDuration}
                    handoverMode={handoverState.handoverMode}
                    
                    // 演算法結果對接
                    algorithmResults={handoverState.algorithmResults}
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
            <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
                {/* 導航欄 */}
                <ErrorBoundary fallback={<div>導航欄發生錯誤</div>}>
                    <Navbar 
                        onMenuClick={uiState.setActiveComponent}
                        activeComponent={uiState.activeComponent}
                        currentScene={currentScene}
                    />
                </ErrorBoundary>

                {/* 主要內容區域 */}
                <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                    <Layout
                        sidebar={
                            <ErrorBoundary fallback={<div>側邊欄發生錯誤</div>}>
                                <EnhancedSidebar
                                    // 設備相關
                                    devices={sortedDevicesForSidebar}
                                    loading={loading}
                                    apiStatus={apiStatus}
                                    hasTempDevices={hasTempDevices}
                                    onApply={applyDeviceChanges}
                                    onCancel={cancelDeviceChanges}
                                    onDeleteDevice={deleteDeviceById}
                                    onAddDevice={addNewDevice}
                                    onDeviceChange={updateDeviceField}
                                    
                                    // UI控制
                                    activeComponent={uiState.activeComponent}
                                    auto={uiState.auto}
                                    onAutoChange={handleAutoChange}
                                    onManualControl={handleManualControl}
                                    uavAnimation={uiState.uavAnimation}
                                    onUavAnimationChange={uiState.setUavAnimation}
                                    onSelectedReceiversChange={uiState.setSelectedReceiverIds}
                                    
                                    // 衛星控制
                                    satelliteEnabled={satelliteState.satelliteEnabled}
                                    onSatelliteEnabledChange={satelliteState.setSatelliteEnabled}
                                    onSatelliteDataUpdate={satelliteState.setSkyfieldSatellites}
                                    
                                    // 階段四功能開關 - 使用 featureState
                                    interferenceVisualizationEnabled={featureState.interferenceVisualizationEnabled}
                                    onInterferenceVisualizationChange={(enabled) => featureState.updateFeatureState({ interferenceVisualizationEnabled: enabled })}
                                    sinrHeatmapEnabled={featureState.sinrHeatmapEnabled}
                                    onSinrHeatmapChange={(enabled) => featureState.updateFeatureState({ sinrHeatmapEnabled: enabled })}
                                    aiRanVisualizationEnabled={featureState.aiRanVisualizationEnabled}
                                    onAiRanVisualizationChange={(enabled) => featureState.updateFeatureState({ aiRanVisualizationEnabled: enabled })}
                                    manualControlEnabled={featureState.manualControlEnabled}
                                    onManualControlEnabledChange={(enabled) => featureState.updateFeatureState({ manualControlEnabled: enabled })}
                                    
                                    // 擴展功能
                                    sionna3DVisualizationEnabled={featureState.sionna3DVisualizationEnabled}
                                    onSionna3DVisualizationChange={(enabled) => featureState.updateFeatureState({ sionna3DVisualizationEnabled: enabled })}
                                    realTimeMetricsEnabled={featureState.realTimeMetricsEnabled}
                                    onRealTimeMetricsChange={(enabled) => featureState.updateFeatureState({ realTimeMetricsEnabled: enabled })}
                                    interferenceAnalyticsEnabled={featureState.interferenceAnalyticsEnabled}
                                    onInterferenceAnalyticsChange={(enabled) => featureState.updateFeatureState({ interferenceAnalyticsEnabled: enabled })}
                                    
                                    // 階段五功能開關
                                    uavSwarmCoordinationEnabled={featureState.uavSwarmCoordinationEnabled}
                                    onUavSwarmCoordinationChange={(enabled) => featureState.updateFeatureState({ uavSwarmCoordinationEnabled: enabled })}
                                    meshNetworkTopologyEnabled={featureState.meshNetworkTopologyEnabled}
                                    onMeshNetworkTopologyChange={(enabled) => featureState.updateFeatureState({ meshNetworkTopologyEnabled: enabled })}
                                    satelliteUavConnectionEnabled={featureState.satelliteUavConnectionEnabled}
                                    onSatelliteUavConnectionChange={(enabled) => featureState.updateFeatureState({ satelliteUavConnectionEnabled: enabled })}
                                    failoverMechanismEnabled={featureState.failoverMechanismEnabled}
                                    onFailoverMechanismChange={(enabled) => featureState.updateFeatureState({ failoverMechanismEnabled: enabled })}
                                    
                                    // 階段六功能開關
                                    predictionPath3DEnabled={featureState.predictionPath3DEnabled}
                                    onPredictionPath3DChange={(enabled) => featureState.updateFeatureState({ predictionPath3DEnabled: enabled })}
                                    _predictionAccuracyDashboardEnabled={featureState.predictionAccuracyDashboardEnabled}
                                    _onChartAnalysisDashboardChange={(enabled) => featureState.updateFeatureState({ predictionAccuracyDashboardEnabled: enabled })}
                                    _coreNetworkSyncEnabled={featureState.coreNetworkSyncEnabled}
                                    _onCoreNetworkSyncChange={(enabled) => featureState.updateFeatureState({ coreNetworkSyncEnabled: enabled })}
                                    
                                    // Stage 3 功能
                                    _realtimePerformanceMonitorEnabled={featureState.realtimePerformanceMonitorEnabled}
                                    _onRealtimePerformanceMonitorChange={(enabled) => featureState.updateFeatureState({ realtimePerformanceMonitorEnabled: enabled })}
                                    _scenarioTestEnvironmentEnabled={featureState.scenarioTestEnvironmentEnabled}
                                    _onScenarioTestEnvironmentChange={(enabled) => featureState.updateFeatureState({ scenarioTestEnvironmentEnabled: enabled })}
                                    
                                    // 階段七功能開關
                                    _e2ePerformanceMonitoringEnabled={featureState.e2ePerformanceMonitoringEnabled}
                                    _onE2EPerformanceMonitoringChange={(enabled) => featureState.updateFeatureState({ e2ePerformanceMonitoringEnabled: enabled })}
                                    _testResultsVisualizationEnabled={featureState.testResultsVisualizationEnabled}
                                    _onTestResultsVisualizationChange={(enabled) => featureState.updateFeatureState({ testResultsVisualizationEnabled: enabled })}
                                    _performanceTrendAnalysisEnabled={featureState.performanceTrendAnalysisEnabled}
                                    _onPerformanceTrendAnalysisChange={(enabled) => featureState.updateFeatureState({ performanceTrendAnalysisEnabled: enabled })}
                                    _automatedReportGenerationEnabled={featureState.automatedReportGenerationEnabled}
                                    _onAutomatedReportGenerationChange={(enabled) => featureState.updateFeatureState({ automatedReportGenerationEnabled: enabled })}
                                    
                                    // 階段八功能開關
                                    _predictiveMaintenanceEnabled={featureState.predictiveMaintenanceEnabled}
                                    _onPredictiveMaintenanceChange={(enabled) => featureState.updateFeatureState({ predictiveMaintenanceEnabled: enabled })}
                                    _intelligentRecommendationEnabled={featureState.intelligentRecommendationEnabled}
                                    _onIntelligentRecommendationChange={(enabled) => featureState.updateFeatureState({ intelligentRecommendationEnabled: enabled })}
                                    
                                    // 換手動畫狀態回調
                                    onHandoverStateChange={handoverState.setHandoverState}
                                    onCurrentConnectionChange={handoverState.setCurrentConnection}
                                    onPredictedConnectionChange={handoverState.setPredictedConnection}
                                    onTransitionChange={handleTransitionChange}
                                    onAlgorithmResults={handoverState.setAlgorithmResults}
                                    
                                    // 衛星動畫控制
                                    satelliteSpeedMultiplier={handoverState.handoverStableDuration}
                                    onSatelliteSpeedChange={handoverState.setHandoverStableDuration}
                                    handoverMode={handoverState.handoverMode}
                                    onHandoverModeChange={handoverState.setHandoverMode}
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