// src/App.tsx
import { useState, useCallback, useMemo, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { VisibleSatelliteInfo } from './types/satellite'
import { Device } from './types/device'
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
import './styles/App.scss'

interface AppProps {
    activeView?: string
}

const App: React.FC<AppProps> = ({ activeView = 'stereogram' }) => {
    const { scenes } = useParams<{ scenes: string }>()

    // 確保有預設場景
    const currentScene = scenes || 'nycu'

    // 根據 activeView 設定初始組件
    const initialComponent = activeView === 'stereogram' ? '3DRT' : '2DRT'

    const {
        tempDevices,
        loading,
        apiStatus,
        hasTempDevices,
        fetchDevices: refreshDeviceData,
        setTempDevices,
        setHasTempDevices,
        applyDeviceChanges,
        deleteDeviceById,
        addNewDevice,
        updateDeviceField,
        cancelDeviceChanges,
        updateDevicePositionFromUAV,
    } = useDevices()

    const [skyfieldSatellites, setSkyfieldSatellites] = useState<
        VisibleSatelliteInfo[]
    >([])
    const [satelliteEnabled, setSatelliteEnabled] = useState<boolean>(true) // 預設開啟衛星顯示

    // 衛星動畫控制狀態（動畫永遠開啟，只保留軌跡線控制）
    const [handoverStableDuration, setHandoverStableDuration] =
        useState<number>(5) // 預設5秒穩定期
    const [handoverMode, setHandoverMode] = useState<'demo' | 'real'>('demo') // 換手模式控制
    

    // 🚀 演算法與視覺化對接狀態
    const [algorithmResults, setAlgorithmResults] = useState<{
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }>({})

    const [activeComponent, setActiveComponent] =
        useState<string>(initialComponent)
    const [auto, setAuto] = useState(false)
    const [manualDirection, setManualDirection] = useState<
        | 'up'
        | 'down'
        | 'left'
        | 'right'
        | 'ascend'
        | 'descend'
        | 'left-up'
        | 'right-up'
        | 'left-down'
        | 'right-down'
        | 'rotate-left'
        | 'rotate-right'
        | null
    >(null)
    const [uavAnimation, setUavAnimation] = useState(false)
    const [selectedReceiverIds, setSelectedReceiverIds] = useState<number[]>([])

    // 新增階段四功能狀態 - 預設關閉，專注於換手機制
    const [
        interferenceVisualizationEnabled,
        setInterferenceVisualizationEnabled,
    ] = useState(false)
    const [sinrHeatmapEnabled, setSinrHeatmapEnabled] = useState(false)
    const [aiRanVisualizationEnabled, setAiRanVisualizationEnabled] =
        useState(false)
    const [manualControlEnabled, setManualControlEnabled] = useState(false) // 預設關閉手動控制

    // 新增的階段四擴展功能
    const [sionna3DVisualizationEnabled, setSionna3DVisualizationEnabled] =
        useState(false)
    const [realTimeMetricsEnabled, setRealTimeMetricsEnabled] = useState(false)
    const [interferenceAnalyticsEnabled, setInterferenceAnalyticsEnabled] =
        useState(false)

    // 階段五功能狀態 - 衛星連接功能預設啟用
    const [uavSwarmCoordinationEnabled, setUavSwarmCoordinationEnabled] =
        useState(false)
    const [meshNetworkTopologyEnabled, setMeshNetworkTopologyEnabled] =
        useState(false)
    const [satelliteUavConnectionEnabled, setSatelliteUavConnectionEnabled] =
        useState(false)
    const [failoverMechanismEnabled, setFailoverMechanismEnabled] =
        useState(false)

    // 階段六功能狀態 - 換手核心功能預設關閉，由新組件控制
    const [predictionPath3DEnabled, setPredictionPath3DEnabled] =
        useState(false)
    const [
        predictionAccuracyDashboardEnabled,
        setPredictionAccuracyDashboardEnabled,
    ] = useState(false)
    const [coreNetworkSyncEnabled, setCoreNetworkSyncEnabled] = useState(false)

    // Stage 3 功能狀態
    const [
        realtimePerformanceMonitorEnabled,
        setRealtimePerformanceMonitorEnabled,
    ] = useState(false)
    const [scenarioTestEnvironmentEnabled, setScenarioTestEnvironmentEnabled] =
        useState(false)

    // Toast 通知系統
    const { showToast } = useToast()

    // 網頁載入時執行一次健康檢查
    useEffect(() => {
        // 設置 toast 通知函數
        backgroundHealthMonitor.setToastFunction(showToast)

        // 延遲3秒後執行檢查，讓其他組件先載入完成
        const timer = setTimeout(() => {
            backgroundHealthMonitor.startInitialCheck()
        }, 3000)

        console.log('🔍 網頁載入時將執行系統健康檢查')

        // 清理定時器
        return () => {
            clearTimeout(timer)
        }
    }, [showToast])

    // 3D 換手動畫狀態
    const [handover3DAnimationEnabled] = useState(true) // 預設啟用
    const [handoverState, setHandoverState] = useState(null)
    const [currentConnection, setCurrentConnection] = useState(null)
    const [predictedConnection, setPredictedConnection] = useState(null)
    const [isTransitioning, setIsTransitioning] = useState(false)
    const [transitionProgress, setTransitionProgress] = useState(0)

    // 階段七功能狀態
    const [
        e2ePerformanceMonitoringEnabled,
        setE2EPerformanceMonitoringEnabled,
    ] = useState(false)
    const [
        testResultsVisualizationEnabled,
        setTestResultsVisualizationEnabled,
    ] = useState(false)
    const [
        performanceTrendAnalysisEnabled,
        setPerformanceTrendAnalysisEnabled,
    ] = useState(false)
    const [
        automatedReportGenerationEnabled,
        setAutomatedReportGenerationEnabled,
    ] = useState(false)

    // 階段八功能狀態
    const [predictiveMaintenanceEnabled, setPredictiveMaintenanceEnabled] =
        useState(false)
    const [
        intelligentRecommendationEnabled,
        setIntelligentRecommendationEnabled,
    ] = useState(false)

    const sortedDevicesForSidebar = useMemo(() => {
        return [...tempDevices].sort((a, b) => {
            const roleOrder: { [key: string]: number } = {
                receiver: 1,
                desired: 2,
                jammer: 3,
            }
            const roleA = roleOrder[a.role] || 99
            const roleB = roleOrder[b.role] || 99

            if (roleA !== roleB) {
                return roleA - roleB
            }

            return a.name.localeCompare(b.name)
        })
    }, [tempDevices])

    const handleApply = async () => {
        const { activeTx: currentActiveTx, activeRx: currentActiveRx } =
            countActiveDevices(tempDevices)

        if (currentActiveTx < 1 || currentActiveRx < 1) {
            alert(
                '套用失敗：操作後必須至少保留一個啟用的發射器 (desired) 和一個啟用的接收器 (receiver)。請檢查設備的啟用狀態。'
            )
            return
        }

        await applyDeviceChanges()
    }

    const handleCancel = () => {
        cancelDeviceChanges()
    }

    const handleDeleteDevice = async (id: number) => {
        if (id < 0) {
            setTempDevices((prev) => prev.filter((device) => device.id !== id))
            setHasTempDevices(true)
            console.log(`已從前端移除臨時設備 ID: ${id}`)
            return
        }

        const devicesAfterDelete = tempDevices.filter(
            (device) => device.id !== id
        )
        const { activeTx: futureActiveTx, activeRx: futureActiveRx } =
            countActiveDevices(devicesAfterDelete)

        if (futureActiveTx < 1 || futureActiveRx < 1) {
            alert(
                '刪除失敗：操作後必須至少保留一個啟用的發射器 (desired) 和一個啟用的接收器 (receiver)。'
            )
            return
        }

        if (!window.confirm('確定要刪除這個設備嗎？此操作將立即生效。')) {
            return
        }

        await deleteDeviceById(id)
    }

    const handleAddDevice = () => {
        addNewDevice()
    }

    const handleDeviceChange = (
        id: number,
        field: string | number | symbol,
        value: unknown
    ) => {
        updateDeviceField(id, field as keyof Device, value)
    }

    const handleMenuClick = (component: string) => {
        setActiveComponent(component)
    }

    const handleSelectedReceiversChange = useCallback((ids: number[]) => {
        // console.log('選中的 receiver IDs:', ids) // 註解掉飛行時的 log
        setSelectedReceiverIds(ids)
    }, [])

    const handleSatelliteDataUpdate = useCallback(
        (satellites: VisibleSatelliteInfo[]) => {
            setSkyfieldSatellites(satellites)
        },
        []
    )

    const handleManualControl = useCallback(
        (
            direction:
                | 'up'
                | 'down'
                | 'left'
                | 'right'
                | 'ascend'
                | 'descend'
                | 'left-up'
                | 'right-up'
                | 'left-down'
                | 'right-down'
                | 'rotate-left'
                | 'rotate-right'
                | null
        ) => {
            if (selectedReceiverIds.length === 0) {
                console.log('沒有選中的 receiver，無法控制 UAV')
                return
            }

            setManualDirection(direction)
        },
        [selectedReceiverIds, setManualDirection]
    )

    const handleUAVPositionUpdate = useCallback(
        (pos: [number, number, number], deviceId?: number) => {
            if (
                deviceId === undefined ||
                !selectedReceiverIds.includes(deviceId)
            ) {
                return
            }
            updateDevicePositionFromUAV(deviceId, pos)
        },
        [selectedReceiverIds, updateDevicePositionFromUAV]
    )

    const handleAutoChange = useCallback(
        (newAuto: boolean) => {
            setAuto(newAuto)
            // 當自動飛行開啟時，自動關閉手動控制
            if (newAuto && manualControlEnabled) {
                setManualControlEnabled(false)
            }
        },
        [manualControlEnabled]
    )

    const renderActiveComponent = useCallback(() => {
        switch (activeComponent) {
            case '2DRT':
                return (
                    <SceneViewer
                        devices={tempDevices}
                        refreshDeviceData={refreshDeviceData}
                        sceneName={currentScene}
                    />
                )
            case '3DRT':
                return (
                    <SceneView
                        devices={tempDevices}
                        auto={auto}
                        manualDirection={manualDirection}
                        onManualControl={handleManualControl}
                        onUAVPositionUpdate={handleUAVPositionUpdate}
                        uavAnimation={uavAnimation}
                        selectedReceiverIds={selectedReceiverIds}
                        satellites={satelliteEnabled ? skyfieldSatellites : []}
                        sceneName={currentScene}
                        // 階段四功能狀態
                        interferenceVisualizationEnabled={
                            interferenceVisualizationEnabled
                        }
                        sinrHeatmapEnabled={sinrHeatmapEnabled}
                        aiRanVisualizationEnabled={aiRanVisualizationEnabled}
                        sionna3DVisualizationEnabled={
                            sionna3DVisualizationEnabled
                        }
                        realTimeMetricsEnabled={realTimeMetricsEnabled}
                        interferenceAnalyticsEnabled={
                            interferenceAnalyticsEnabled
                        }
                        // 階段五功能狀態
                        uavSwarmCoordinationEnabled={
                            uavSwarmCoordinationEnabled
                        }
                        meshNetworkTopologyEnabled={meshNetworkTopologyEnabled}
                        satelliteUavConnectionEnabled={
                            satelliteUavConnectionEnabled
                        }
                        failoverMechanismEnabled={failoverMechanismEnabled}
                        // 階段六功能狀態
                        predictionPath3DEnabled={predictionPath3DEnabled}
                        predictionAccuracyDashboardEnabled={
                            predictionAccuracyDashboardEnabled
                        }
                        coreNetworkSyncEnabled={coreNetworkSyncEnabled}
                        // Stage 3 功能
                        realtimePerformanceMonitorEnabled={
                            realtimePerformanceMonitorEnabled
                        }
                        scenarioTestEnvironmentEnabled={
                            scenarioTestEnvironmentEnabled
                        }
                        // 3D 換手動畫
                        handover3DAnimationEnabled={handover3DAnimationEnabled}
                        handoverState={handoverState}
                        currentConnection={currentConnection}
                        predictedConnection={predictedConnection}
                        isTransitioning={isTransitioning}
                        transitionProgress={transitionProgress}
                        onHandoverEvent={(event: Record<string, unknown>) => {
                            console.log('換手事件:', event)
                            // 可以在這裡處理換手事件
                        }}
                        // 階段七功能狀態
                        e2ePerformanceMonitoringEnabled={
                            e2ePerformanceMonitoringEnabled
                        }
                        testResultsVisualizationEnabled={
                            testResultsVisualizationEnabled
                        }
                        performanceTrendAnalysisEnabled={
                            performanceTrendAnalysisEnabled
                        }
                        automatedReportGenerationEnabled={
                            automatedReportGenerationEnabled
                        }
                        // 階段八功能狀態
                        predictiveMaintenanceEnabled={
                            predictiveMaintenanceEnabled
                        }
                        intelligentRecommendationEnabled={
                            intelligentRecommendationEnabled
                        }
                        // 衛星功能狀態
                        satelliteEnabled={satelliteEnabled}
                        satelliteSpeedMultiplier={1} // 固定為1x
                        handoverStableDuration={handoverStableDuration}
                        handoverMode={handoverMode}
                        // 🚀 演算法結果對接
                        algorithmResults={algorithmResults}
                    />
                )
            default:
                return (
                    <SceneViewer
                        devices={tempDevices}
                        refreshDeviceData={refreshDeviceData}
                        sceneName={currentScene}
                    />
                )
        }
    }, [
        activeComponent,
        tempDevices,
        auto,
        manualDirection,
        handleManualControl,
        handleUAVPositionUpdate,
        uavAnimation,
        selectedReceiverIds,
        refreshDeviceData,
        skyfieldSatellites,
        satelliteEnabled,
        algorithmResults,
        handoverMode,
        realtimePerformanceMonitorEnabled,
        scenarioTestEnvironmentEnabled,
        currentScene,
        interferenceVisualizationEnabled,
        sinrHeatmapEnabled,
        aiRanVisualizationEnabled,
        sionna3DVisualizationEnabled,
        realTimeMetricsEnabled,
        interferenceAnalyticsEnabled,
        uavSwarmCoordinationEnabled,
        meshNetworkTopologyEnabled,
        satelliteUavConnectionEnabled,
        failoverMechanismEnabled,
        predictionPath3DEnabled,
        predictionAccuracyDashboardEnabled,
        coreNetworkSyncEnabled,
        handover3DAnimationEnabled,
        handoverState,
        currentConnection,
        predictedConnection,
        isTransitioning,
        transitionProgress,
        e2ePerformanceMonitoringEnabled,
        testResultsVisualizationEnabled,
        performanceTrendAnalysisEnabled,
        automatedReportGenerationEnabled,
        predictiveMaintenanceEnabled,
        intelligentRecommendationEnabled,
        handoverStableDuration,
    ])

    if (loading) {
        return <div className="loading">載入中...</div>
    }

    return (
        <StrategyProvider>
            <DataSyncProvider>
                <ErrorBoundary>
                    <div className="app-container">
                        <Navbar
                            onMenuClick={handleMenuClick}
                            activeComponent={activeComponent}
                            currentScene={currentScene}
                        />
                        <div className="content-wrapper">
                            {/* 全局數據源狀態指示器已移除 - 簡化 UI */}
                            {/* Stage3QuickCheck 已移至後台運行，異常時將使用 Toast 通知 */}

                            <Layout
                                sidebar={
                                    <ErrorBoundary
                                        fallback={<div>側邊欄發生錯誤</div>}
                                    >
                                        <EnhancedSidebar
                                            devices={sortedDevicesForSidebar}
                                            onDeviceChange={handleDeviceChange}
                                            onDeleteDevice={handleDeleteDevice}
                                            onAddDevice={handleAddDevice}
                                            onApply={handleApply}
                                            onCancel={handleCancel}
                                            loading={loading}
                                            apiStatus={apiStatus}
                                            hasTempDevices={hasTempDevices}
                                            auto={auto}
                                            onAutoChange={handleAutoChange}
                                            onManualControl={
                                                handleManualControl
                                            }
                                            activeComponent={activeComponent}
                                            uavAnimation={uavAnimation}
                                            onUavAnimationChange={
                                                setUavAnimation
                                            }
                                            onSelectedReceiversChange={
                                                handleSelectedReceiversChange
                                            }
                                            onSatelliteDataUpdate={
                                                handleSatelliteDataUpdate
                                            }
                                            satelliteEnabled={satelliteEnabled}
                                            onSatelliteEnabledChange={
                                                setSatelliteEnabled
                                            }
                                            // 新增階段四功能開關
                                            interferenceVisualizationEnabled={
                                                interferenceVisualizationEnabled
                                            }
                                            onInterferenceVisualizationChange={
                                                setInterferenceVisualizationEnabled
                                            }
                                            sinrHeatmapEnabled={
                                                sinrHeatmapEnabled
                                            }
                                            onSinrHeatmapChange={
                                                setSinrHeatmapEnabled
                                            }
                                            aiRanVisualizationEnabled={
                                                aiRanVisualizationEnabled
                                            }
                                            onAiRanVisualizationChange={
                                                setAiRanVisualizationEnabled
                                            }
                                            manualControlEnabled={
                                                manualControlEnabled
                                            }
                                            onManualControlEnabledChange={
                                                setManualControlEnabled
                                            }
                                            // 新增的擴展功能
                                            sionna3DVisualizationEnabled={
                                                sionna3DVisualizationEnabled
                                            }
                                            onSionna3DVisualizationChange={
                                                setSionna3DVisualizationEnabled
                                            }
                                            realTimeMetricsEnabled={
                                                realTimeMetricsEnabled
                                            }
                                            onRealTimeMetricsChange={
                                                setRealTimeMetricsEnabled
                                            }
                                            interferenceAnalyticsEnabled={
                                                interferenceAnalyticsEnabled
                                            }
                                            onInterferenceAnalyticsChange={
                                                setInterferenceAnalyticsEnabled
                                            }
                                            // 階段五功能開關
                                            uavSwarmCoordinationEnabled={
                                                uavSwarmCoordinationEnabled
                                            }
                                            onUavSwarmCoordinationChange={
                                                setUavSwarmCoordinationEnabled
                                            }
                                            meshNetworkTopologyEnabled={
                                                meshNetworkTopologyEnabled
                                            }
                                            onMeshNetworkTopologyChange={
                                                setMeshNetworkTopologyEnabled
                                            }
                                            satelliteUavConnectionEnabled={
                                                satelliteUavConnectionEnabled
                                            }
                                            onSatelliteUavConnectionChange={
                                                setSatelliteUavConnectionEnabled
                                            }
                                            failoverMechanismEnabled={
                                                failoverMechanismEnabled
                                            }
                                            onFailoverMechanismChange={
                                                setFailoverMechanismEnabled
                                            }
                                            // 階段六功能狀態
                                            predictionPath3DEnabled={
                                                predictionPath3DEnabled
                                            }
                                            onPredictionPath3DChange={
                                                setPredictionPath3DEnabled
                                            }
                                            _predictionAccuracyDashboardEnabled={
                                                predictionAccuracyDashboardEnabled
                                            }
                                            _onChartAnalysisDashboardChange={
                                                setPredictionAccuracyDashboardEnabled
                                            }
                                            _coreNetworkSyncEnabled={
                                                coreNetworkSyncEnabled
                                            }
                                            _onCoreNetworkSyncChange={
                                                setCoreNetworkSyncEnabled
                                            }
                                            // Stage 3 功能
                                            _realtimePerformanceMonitorEnabled={
                                                realtimePerformanceMonitorEnabled
                                            }
                                            _onRealtimePerformanceMonitorChange={
                                                setRealtimePerformanceMonitorEnabled
                                            }
                                            _scenarioTestEnvironmentEnabled={
                                                scenarioTestEnvironmentEnabled
                                            }
                                            _onScenarioTestEnvironmentChange={
                                                setScenarioTestEnvironmentEnabled
                                            }
                                            // 階段七功能狀態
                                            _e2ePerformanceMonitoringEnabled={
                                                e2ePerformanceMonitoringEnabled
                                            }
                                            _onE2EPerformanceMonitoringChange={
                                                setE2EPerformanceMonitoringEnabled
                                            }
                                            _testResultsVisualizationEnabled={
                                                testResultsVisualizationEnabled
                                            }
                                            _onTestResultsVisualizationChange={
                                                setTestResultsVisualizationEnabled
                                            }
                                            _performanceTrendAnalysisEnabled={
                                                performanceTrendAnalysisEnabled
                                            }
                                            _onPerformanceTrendAnalysisChange={
                                                setPerformanceTrendAnalysisEnabled
                                            }
                                            _automatedReportGenerationEnabled={
                                                automatedReportGenerationEnabled
                                            }
                                            _onAutomatedReportGenerationChange={
                                                setAutomatedReportGenerationEnabled
                                            }
                                            // 階段八功能狀態
                                            _predictiveMaintenanceEnabled={
                                                predictiveMaintenanceEnabled
                                            }
                                            _onPredictiveMaintenanceChange={
                                                setPredictiveMaintenanceEnabled
                                            }
                                            _intelligentRecommendationEnabled={
                                                intelligentRecommendationEnabled
                                            }
                                            _onIntelligentRecommendationChange={
                                                setIntelligentRecommendationEnabled
                                            }
                                            // 3D 動畫狀態更新回調
                                            onHandoverStateChange={
                                                setHandoverState
                                            }
                                            onCurrentConnectionChange={
                                                setCurrentConnection
                                            }
                                            onPredictedConnectionChange={
                                                setPredictedConnection
                                            }
                                            onTransitionChange={(
                                                isTransitioning,
                                                progress
                                            ) => {
                                                setIsTransitioning(
                                                    isTransitioning
                                                )
                                                setTransitionProgress(progress)
                                            }}
                                            // 🚀 演算法結果回調 - 連接後端演算法與前端視覺化
                                            onAlgorithmResults={
                                                setAlgorithmResults
                                            }
                                            // 衛星動畫控制 props（動畫永遠開啟）
                                            satelliteSpeedMultiplier={
                                                handoverStableDuration
                                            }
                                            onSatelliteSpeedChange={
                                                setHandoverStableDuration
                                            }
                                            handoverMode={handoverMode}
                                            onHandoverModeChange={
                                                setHandoverMode
                                            }
                                        />
                                    </ErrorBoundary>
                                }
                                content={
                                    <ErrorBoundary
                                        fallback={<div>主視圖發生錯誤</div>}
                                    >
                                        {renderActiveComponent()}
                                    </ErrorBoundary>
                                }
                                activeComponent={activeComponent}
                            />
                        </div>
                    </div>
                    {/* Toast 通知系統 */}
                    <ToastNotification />
                </ErrorBoundary>
            </DataSyncProvider>
        </StrategyProvider>
    )
}

export default App
