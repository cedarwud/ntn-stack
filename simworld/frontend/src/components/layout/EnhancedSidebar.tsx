import { useState, useEffect, useRef } from 'react'
import '../../styles/Sidebar.scss'
import { UAVManualDirection } from '../scenes/UAVFlight'
import { Device } from '../../types/device'
import SidebarStarfield from '../ui/SidebarStarfield'
import DeviceItem from '../devices/DeviceItem'
import { useReceiverSelection } from '../../hooks/useReceiverSelection'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { ApiRoutes } from '../../config/apiRoutes'
import { generateDeviceName as utilGenerateDeviceName } from '../../utils/deviceName'
import HandoverManager from '../handover/HandoverManager'
import { SATELLITE_CONFIG } from '../../config/satellite.config'

interface SidebarProps {
    devices: Device[]
    loading: boolean
    apiStatus: 'disconnected' | 'connected' | 'error'
    onDeviceChange: (id: number, field: keyof Device, value: any) => void
    onDeleteDevice: (id: number) => void
    onAddDevice: () => void
    onApply: () => void
    onCancel: () => void
    hasTempDevices: boolean
    auto: boolean
    onAutoChange: (auto: boolean) => void
    onManualControl: (direction: UAVManualDirection) => void
    activeComponent: string
    uavAnimation: boolean
    onUavAnimationChange: (val: boolean) => void
    onSelectedReceiversChange?: (selectedIds: number[]) => void
    onSatelliteDataUpdate?: (satellites: VisibleSatelliteInfo[]) => void
    satelliteEnabled?: boolean
    onSatelliteEnabledChange?: (enabled: boolean) => void
    // 新增的階段四功能開關
    interferenceVisualizationEnabled?: boolean
    onInterferenceVisualizationChange?: (enabled: boolean) => void
    sinrHeatmapEnabled?: boolean
    onSinrHeatmapChange?: (enabled: boolean) => void
    aiRanVisualizationEnabled?: boolean
    onAiRanVisualizationChange?: (enabled: boolean) => void
    manualControlEnabled?: boolean
    onManualControlEnabledChange?: (enabled: boolean) => void
    // 新增的擴展功能
    sionna3DVisualizationEnabled?: boolean
    onSionna3DVisualizationChange?: (enabled: boolean) => void
    realTimeMetricsEnabled?: boolean
    onRealTimeMetricsChange?: (enabled: boolean) => void
    interferenceAnalyticsEnabled?: boolean
    onInterferenceAnalyticsChange?: (enabled: boolean) => void
    // 階段五功能開關
    uavSwarmCoordinationEnabled?: boolean
    onUavSwarmCoordinationChange?: (enabled: boolean) => void
    meshNetworkTopologyEnabled?: boolean
    onMeshNetworkTopologyChange?: (enabled: boolean) => void
    satelliteUavConnectionEnabled?: boolean
    onSatelliteUavConnectionChange?: (enabled: boolean) => void
    failoverMechanismEnabled?: boolean
    onFailoverMechanismChange?: (enabled: boolean) => void

    // 階段六功能開關
    handoverPredictionEnabled?: boolean
    onHandoverPredictionChange?: (enabled: boolean) => void
    handoverDecisionVisualizationEnabled?: boolean
    onHandoverDecisionVisualizationChange?: (enabled: boolean) => void
    predictionPath3DEnabled?: boolean
    onPredictionPath3DChange?: (enabled: boolean) => void
    handoverPerformanceDashboardEnabled?: boolean
    onHandoverPerformanceDashboardChange?: (enabled: boolean) => void
    predictionAccuracyDashboardEnabled?: boolean
    onPredictionAccuracyDashboardChange?: (enabled: boolean) => void
    coreNetworkSyncEnabled?: boolean
    onCoreNetworkSyncChange?: (enabled: boolean) => void
    
    // Stage 3 功能開關
    realtimePerformanceMonitorEnabled?: boolean
    onRealtimePerformanceMonitorChange?: (enabled: boolean) => void
    scenarioTestEnvironmentEnabled?: boolean
    onScenarioTestEnvironmentChange?: (enabled: boolean) => void
    
    // 階段七功能開關
    e2ePerformanceMonitoringEnabled?: boolean
    onE2EPerformanceMonitoringChange?: (enabled: boolean) => void
    testResultsVisualizationEnabled?: boolean
    onTestResultsVisualizationChange?: (enabled: boolean) => void
    performanceTrendAnalysisEnabled?: boolean
    onPerformanceTrendAnalysisChange?: (enabled: boolean) => void
    automatedReportGenerationEnabled?: boolean
    onAutomatedReportGenerationChange?: (enabled: boolean) => void
    
    // 階段八功能開關
    predictiveMaintenanceEnabled?: boolean
    onPredictiveMaintenanceChange?: (enabled: boolean) => void
    intelligentRecommendationEnabled?: boolean
    onIntelligentRecommendationChange?: (enabled: boolean) => void
    
    // 衛星動畫控制（動畫永遠開啟）
    satelliteSpeedMultiplier?: number
    onSatelliteSpeedChange?: (speed: number) => void
    
    // 3D 動畫狀態更新回調
    onHandoverStateChange?: (state: any) => void
    onCurrentConnectionChange?: (connection: any) => void
    onPredictedConnectionChange?: (connection: any) => void
    onTransitionChange?: (isTransitioning: boolean, progress: number) => void
    // 🚀 演算法結果回調 - 用於對接視覺化
    onAlgorithmResults?: (results: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }) => void
}

// 核心功能開關配置 - 根據 paper.md 計畫書精簡
interface FeatureToggle {
    id: string
    label: string
    category: 'basic' | 'handover' | 'quality'
    enabled: boolean
    onToggle: (enabled: boolean) => void
    icon?: string
    description?: string
    hidden?: boolean
}

// 定義核心功能和隱藏功能 - 未來擴展用
// const CORE_HANDOVER_FEATURES = {
//     basic: ['auto', 'uavAnimation', 'satelliteEnabled'],
//     handover: ['handoverPrediction', 'handoverDecision', 'handoverPerformance'],
//     quality: ['sinrHeatmap', 'interferenceVisualization'],
//     network: ['satelliteUAVConnection']
// }

// const HIDDEN_FEATURES = [
//     'adaptiveLearning', 'predictiveMaintenance', 'testVisualization',
//     'intelligentRecommendation', 'automatedReporting', 'mlModelMonitoring',
//     'e2ePerformanceMonitoring', 'performanceTrendAnalysis', 'realTimeMetrics',
//     'interferenceAnalytics', 'sionna3DVisualization', 'uavSwarmCoordination',
//     'meshNetworkTopology', 'failoverMechanism', 'aiRanVisualization'
// ]

// Helper function to fetch visible satellites
async function fetchVisibleSatellites(
    count: number,
    minElevation: number
): Promise<VisibleSatelliteInfo[]> {
    const apiUrl = `${ApiRoutes.satelliteOps.getVisibleSatellites}?count=${count}&min_elevation_deg=${minElevation}`
    try {
        const response = await fetch(apiUrl)
        if (!response.ok) {
            console.error(
                `Error fetching satellites: ${response.status} ${response.statusText}`
            )
            return []
        }
        const data = await response.json()
        return data.satellites || []
    } catch (error) {
        console.error(
            'Network error or JSON parsing error fetching satellites:',
            error
        )
        return []
    }
}

const EnhancedSidebar: React.FC<SidebarProps> = ({
    devices,
    loading,
    apiStatus,
    onDeviceChange,
    onDeleteDevice,
    onAddDevice,
    onApply,
    onCancel,
    hasTempDevices,
    auto,
    onAutoChange,
    onManualControl,
    activeComponent,
    uavAnimation,
    onUavAnimationChange,
    onSelectedReceiversChange,
    onSatelliteDataUpdate,
    satelliteEnabled = false,
    onSatelliteEnabledChange,
    interferenceVisualizationEnabled = false,
    onInterferenceVisualizationChange,
    sinrHeatmapEnabled = false,
    onSinrHeatmapChange,
    aiRanVisualizationEnabled = false,
    onAiRanVisualizationChange,
    manualControlEnabled = false,
    onManualControlEnabledChange,
    sionna3DVisualizationEnabled = false,
    onSionna3DVisualizationChange,
    realTimeMetricsEnabled = false,
    onRealTimeMetricsChange,
    interferenceAnalyticsEnabled = false,
    onInterferenceAnalyticsChange,
    // 階段五功能 props
    uavSwarmCoordinationEnabled = false,
    onUavSwarmCoordinationChange,
    meshNetworkTopologyEnabled = false,
    onMeshNetworkTopologyChange,
    satelliteUavConnectionEnabled = false,
    onSatelliteUavConnectionChange,
    failoverMechanismEnabled = false,
    onFailoverMechanismChange,
    // 階段六功能 props
    handoverPredictionEnabled = false,
    onHandoverPredictionChange,
    handoverDecisionVisualizationEnabled = false,
    onHandoverDecisionVisualizationChange,
    predictionPath3DEnabled = false,
    onPredictionPath3DChange,
    handoverPerformanceDashboardEnabled = false,
    onHandoverPerformanceDashboardChange,
    predictionAccuracyDashboardEnabled = false,
    onPredictionAccuracyDashboardChange,
    coreNetworkSyncEnabled = false,
    onCoreNetworkSyncChange,
    // Stage 3 功能 props
    realtimePerformanceMonitorEnabled = false,
    onRealtimePerformanceMonitorChange,
    scenarioTestEnvironmentEnabled = false,
    onScenarioTestEnvironmentChange,
    // 階段七功能 props
    e2ePerformanceMonitoringEnabled = false,
    onE2EPerformanceMonitoringChange,
    testResultsVisualizationEnabled = false,
    onTestResultsVisualizationChange,
    performanceTrendAnalysisEnabled = false,
    onPerformanceTrendAnalysisChange,
    automatedReportGenerationEnabled = false,
    onAutomatedReportGenerationChange,
    // 階段八功能 props
    predictiveMaintenanceEnabled = false,
    onPredictiveMaintenanceChange,
    intelligentRecommendationEnabled = false,
    onIntelligentRecommendationChange,
    // 3D 動畫狀態更新回調
    onHandoverStateChange,
    onCurrentConnectionChange,
    onPredictedConnectionChange,
    onTransitionChange,
    onAlgorithmResults,
    // 衛星動畫控制 props（動畫永遠開啟）
    satelliteSpeedMultiplier = 5,
    onSatelliteSpeedChange,
}) => {
    // 現有狀態
    const [orientationInputs, setOrientationInputs] = useState<{
        [key: string]: { x: string; y: string; z: string }
    }>({})
    const manualIntervalRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const { selectedReceiverIds, handleBadgeClick } = useReceiverSelection({
        devices,
        onSelectedReceiversChange,
    })

    // 擴展的UI狀態
    const [showControlPanel, setShowControlPanel] = useState(true)
    const [activeCategory, setActiveCategory] = useState<string>('handover') // 默認顯示換手機制
    const [showTempDevices, setShowTempDevices] = useState(true)
    const [showReceiverDevices, setShowReceiverDevices] = useState(false)
    const [showDesiredDevices, setShowDesiredDevices] = useState(false)
    const [showJammerDevices, setShowJammerDevices] = useState(false)
    const [showUavSelection, setShowUavSelection] = useState(false)

    // 衛星相關狀態已移除，使用固定配置
    const [skyfieldSatellites, setSkyfieldSatellites] = useState<
        VisibleSatelliteInfo[]
    >([])
    const [showSkyfieldSection, setShowSkyfieldSection] = useState<boolean>(false)
    const [loadingSatellites, setLoadingSatellites] = useState<boolean>(false)
    const satelliteRefreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

    // 處理衛星星座顯示開關，連帶控制衛星-UAV 連接
    const handleSatelliteEnabledToggle = (enabled: boolean) => {
        // 調用原始的衛星顯示開關處理函數
        if (onSatelliteEnabledChange) {
            onSatelliteEnabledChange(enabled)
        }
        
        // 如果關閉衛星顯示，同時關閉衛星-UAV 連接
        if (!enabled && satelliteUavConnectionEnabled) {
            if (onSatelliteUavConnectionChange) {
                onSatelliteUavConnectionChange(false)
            }
        }
    }
    
    // 處理衛星-UAV 連接開關，連動開啟衛星顯示
    const handleSatelliteUavConnectionToggle = (enabled: boolean) => {
        if (enabled && !satelliteEnabled) {
            // 如果開啟衛星-UAV 連接但衛星顯示未開啟，則自動開啟衛星顯示
            if (onSatelliteEnabledChange) {
                onSatelliteEnabledChange(true)
            }
        }
        // 調用原始的開關處理函數
        if (onSatelliteUavConnectionChange) {
            onSatelliteUavConnectionChange(enabled)
        }
    }

    // 精簡的核心功能開關配置 - 根據 paper.md 優化為 8 個核心功能
    const featureToggles: FeatureToggle[] = [
        // 基礎控制 (4個)
        {
            id: 'auto',
            label: '自動飛行模式',
            category: 'basic',
            enabled: auto,
            onToggle: onAutoChange,
            icon: '🤖',
            description: 'UAV 自動飛行模式'
        },
        {
            id: 'uavAnimation',
            label: 'UAV 飛行動畫',
            category: 'basic',
            enabled: uavAnimation,
            onToggle: onUavAnimationChange,
            icon: '🎬',
            description: 'UAV 飛行動畫效果'
        },
        {
            id: 'satelliteEnabled',
            label: '衛星星座顯示',
            category: 'basic',
            enabled: satelliteEnabled,
            onToggle: handleSatelliteEnabledToggle,
            icon: '🛰️',
            description: 'LEO 衛星星座顯示'
        },
        {
            id: 'satelliteUAVConnection',
            label: '衛星-UAV 連接',
            category: 'basic',
            enabled: satelliteUavConnectionEnabled && satelliteEnabled, // 只有衛星顯示開啟時才能啟用
            onToggle: handleSatelliteUavConnectionToggle,
            icon: '🔗',
            description: '衛星與 UAV 連接狀態監控（需先開啟衛星顯示）'
        },
        
        // 換手核心功能 (3個)
        {
            id: 'handoverPrediction',
            label: '換手預測顯示',
            category: 'handover',
            enabled: handoverPredictionEnabled,
            onToggle: onHandoverPredictionChange || (() => {}),
            icon: '🔮',
            description: '衛星換手預測與時間軸分析'
        },
        {
            id: 'handoverDecision',
            label: '換手決策可視化',
            category: 'handover',
            enabled: handoverDecisionVisualizationEnabled,
            onToggle: onHandoverDecisionVisualizationChange || (() => {}),
            icon: '🎯',
            description: '換手決策過程 3D 可視化（含預測路徑）'
        },
        {
            id: 'handoverPerformance',
            label: '換手性能監控',
            category: 'handover',
            enabled: handoverPerformanceDashboardEnabled,
            onToggle: onHandoverPerformanceDashboardChange || (() => {}),
            icon: '📊',
            description: '換手性能統計與分析（含預測精度）'
        },
        
        // 通信品質 (2個)
        {
            id: 'sinrHeatmap',
            label: 'SINR 熱力圖',
            category: 'quality',
            enabled: sinrHeatmapEnabled,
            onToggle: onSinrHeatmapChange || (() => {}),
            icon: '🔥',
            description: '地面 SINR 信號強度熱力圖'
        },
        {
            id: 'interferenceVisualization',
            label: '干擾源可視化',
            category: 'quality',
            enabled: interferenceVisualizationEnabled,
            onToggle: onInterferenceVisualizationChange || (() => {}),
            icon: '📡',
            description: '3D 干擾源範圍和影響可視化'
        },
        
        
        // 手動控制面板會根據自動飛行狀態動態顯示
        // 隱藏的非核心功能：predictionAccuracyDashboard, predictionPath3D, coreNetworkSync 等 17 個功能
    ]
    
    // 動態添加手動控制開關（當自動飛行關閉時）
    if (!auto) {
        featureToggles.splice(3, 0, {
            id: 'manualControl',
            label: '手動控制面板',
            category: 'basic',
            enabled: manualControlEnabled,
            onToggle: onManualControlEnabledChange || (() => {}),
            icon: '🕹️',
            description: '顯示 UAV 手動控制面板'
        })
    }

    // 精簡的類別配置 - 只保留 3 個核心類別
    const categories = [
        { id: 'basic', label: '基礎控制', icon: '⚙️' },
        { id: 'handover', label: '換手機制', icon: '🔄' },
        { id: 'quality', label: '通信品質', icon: '📶' }
    ]

    // 靜態衛星數據管理：完全避免重新載入和重新渲染
    const satelliteDataInitialized = useRef(false)
    

    useEffect(() => {
        // 只在首次啟用衛星時載入一次，之後完全依賴內在軌道運動
        const initializeSatellitesOnce = async () => {
            if (!satelliteEnabled) {
                setSkyfieldSatellites([])
                if (onSatelliteDataUpdate) {
                    onSatelliteDataUpdate([])
                }
                satelliteDataInitialized.current = false
                setLoadingSatellites(false)
                return
            }

            // 如果已經初始化過，就不再重新載入
            if (satelliteDataInitialized.current) {
                console.log('🛰️ 衛星數據已初始化，使用內在軌道運動，避免重新載入')
                return
            }

            console.log('🛰️ 首次初始化衛星數據...')
            setLoadingSatellites(true)
            
            const satellites = await fetchVisibleSatellites(
                SATELLITE_CONFIG.VISIBLE_COUNT,
                SATELLITE_CONFIG.MIN_ELEVATION
            )

            let sortedSatellites = [...satellites]
            sortedSatellites.sort((a, b) => b.elevation_deg - a.elevation_deg)
            
            setSkyfieldSatellites(sortedSatellites)

            if (onSatelliteDataUpdate) {
                onSatelliteDataUpdate(sortedSatellites)
            }

            satelliteDataInitialized.current = true
            setLoadingSatellites(false)
            console.log('🛰️ 衛星數據初始化完成，後續使用內在運動邏輯')
        }

        // 清理任何現有的刷新間隔
        if (satelliteRefreshIntervalRef.current) {
            clearInterval(satelliteRefreshIntervalRef.current)
            satelliteRefreshIntervalRef.current = null
        }

        // 只初始化一次，不設置定期刷新
        initializeSatellitesOnce()

        return () => {
            if (satelliteRefreshIntervalRef.current) {
                clearInterval(satelliteRefreshIntervalRef.current)
                satelliteRefreshIntervalRef.current = null
            }
        }
    }, [
        satelliteEnabled, // 只依賴啟用狀態
        // 移除其他依賴，避免重新載入
    ])

    // 設備方向輸入處理
    useEffect(() => {
        const newInputs: {
            [key: string]: { x: string; y: string; z: string }
        } = {}
        devices.forEach((device) => {
            const existingInput = orientationInputs[device.id]
            const backendX = device.orientation_x?.toString() || '0'
            const backendY = device.orientation_y?.toString() || '0'
            const backendZ = device.orientation_z?.toString() || '0'

            if (existingInput) {
                newInputs[device.id] = {
                    x: existingInput.x !== '0' && existingInput.x !== backendX
                        ? existingInput.x
                        : backendX,
                    y: existingInput.y !== '0' && existingInput.y !== backendY
                        ? existingInput.y
                        : backendY,
                    z: existingInput.z !== '0' && existingInput.z !== backendZ
                        ? existingInput.z
                        : backendZ,
                }
            } else {
                newInputs[device.id] = {
                    x: backendX,
                    y: backendY,
                    z: backendZ,
                }
            }
        })
        setOrientationInputs(newInputs)
    }, [devices])

    // 處理衛星顯示數量變更

    // 方向輸入處理
    const handleDeviceOrientationInputChange = (
        deviceId: number,
        axis: 'x' | 'y' | 'z',
        value: string
    ) => {
        setOrientationInputs((prev) => ({
            ...prev,
            [deviceId]: {
                ...prev[deviceId],
                [axis]: value,
            },
        }))

        if (value.includes('/')) {
            const parts = value.split('/')
            if (parts.length === 2) {
                const numerator = parseFloat(parts[0])
                const denominator = parseFloat(parts[1])
                if (
                    !isNaN(numerator) &&
                    !isNaN(denominator) &&
                    denominator !== 0
                ) {
                    const calculatedValue = (numerator / denominator) * Math.PI
                    const orientationKey = `orientation_${axis}` as keyof Device
                    onDeviceChange(deviceId, orientationKey, calculatedValue)
                }
            }
        } else {
            const numValue = parseFloat(value)
            if (!isNaN(numValue)) {
                const orientationKey = `orientation_${axis}` as keyof Device
                onDeviceChange(deviceId, orientationKey, numValue)
            }
        }
    }

    // 手動控制處理
    const handleManualDown = (
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
    ) => {
        onManualControl(direction)
        if (manualIntervalRef.current) clearInterval(manualIntervalRef.current)
        manualIntervalRef.current = setInterval(() => {
            onManualControl(direction)
        }, 60)
    }

    const handleManualUp = () => {
        if (manualIntervalRef.current) {
            clearInterval(manualIntervalRef.current)
            manualIntervalRef.current = null
        }
        onManualControl(null)
    }

    // 設備分組
    const tempDevices = devices.filter(
        (device) => device.id == null || device.id < 0
    )
    const receiverDevices = devices.filter(
        (device) =>
            device.id != null && device.id >= 0 && device.role === 'receiver'
    )
    const desiredDevices = devices.filter(
        (device) =>
            device.id != null && device.id >= 0 && device.role === 'desired'
    )
    const jammerDevices = devices.filter(
        (device) =>
            device.id != null && device.id >= 0 && device.role === 'jammer'
    )

    const handleDeviceRoleChange = (deviceId: number, newRole: string) => {
        const newName = utilGenerateDeviceName(
            newRole,
            devices.map((d) => ({ name: d.name }))
        )
        onDeviceChange(deviceId, 'role', newRole)
        onDeviceChange(deviceId, 'name', newName)
    }

    // 渲染功能開關
    const renderFeatureToggles = () => {
        const currentToggles = featureToggles.filter(
            toggle => toggle.category === activeCategory && !toggle.hidden
        )

        return (
            <div className="feature-toggles-container">
                {currentToggles.map((toggle) => (
                    <div
                        key={toggle.id}
                        className={`feature-toggle ${toggle.enabled ? 'enabled' : 'disabled'}`}
                        onClick={() => toggle.onToggle(!toggle.enabled)}
                        title={toggle.description}
                    >
                        <div className="toggle-content">
                            <span className="toggle-icon">{toggle.icon}</span>
                            <span className="toggle-label">{toggle.label}</span>
                        </div>
                        <div className={`toggle-switch ${toggle.enabled ? 'on' : 'off'}`}>
                            <div className="toggle-slider"></div>
                        </div>
                    </div>
                ))}
            </div>
        )
    }

    return (
        <div className="enhanced-sidebar-container">
            <SidebarStarfield />
            
            {activeComponent !== '2DRT' && (
                <>
                    {/* 功能控制面板 */}
                    <div className="control-panel">
                        <div
                            className="control-panel-header"
                            onClick={() => setShowControlPanel(!showControlPanel)}
                        >
                            <span className="header-title">
                                🎛️ LEO 衛星換手機制控制
                            </span>
                            <span className={`header-arrow ${showControlPanel ? 'expanded' : ''}`}>
                                ▼
                            </span>
                        </div>

                        {showControlPanel && (
                            <>
                                {/* 類別選擇 */}
                                <div className="category-tabs">
                                    {categories.map((category) => (
                                        <button
                                            key={category.id}
                                            className={`category-tab ${
                                                activeCategory === category.id ? 'active' : ''
                                            }`}
                                            onClick={() => setActiveCategory(category.id)}
                                            title={category.label}
                                        >
                                            <span className="tab-icon">{category.icon}</span>
                                            <span className="tab-label">{category.label}</span>
                                        </button>
                                    ))}
                                </div>

                                {/* 功能開關 */}
                                {renderFeatureToggles()}

                                {/* 衛星動畫速度控制 - 當衛星啟用時顯示 */}
                                {activeCategory === 'basic' && satelliteEnabled && (
                                    <div className="satellite-animation-controls">
                                        <div className="control-section-title">🎭 衛星動畫控制</div>
                                        

                                        {/* 速度控制滑塊 */}
                                        <div className="control-item">
                                            <div className="control-label">
                                                動畫速度: {satelliteSpeedMultiplier}x
                                            </div>
                                            <input
                                                type="range"
                                                min="1"
                                                max="10"
                                                step="1"
                                                value={Math.min(satelliteSpeedMultiplier, 10)}
                                                onChange={(e) => onSatelliteSpeedChange && onSatelliteSpeedChange(Number(e.target.value))}
                                                className="speed-slider"
                                            />
                                            <div className="speed-labels">
                                                <span>1x</span>
                                                <span>真實時間比例</span>
                                                <span>10x</span>
                                            </div>
                                        </div>

                                        {/* 預設速度按鈕 */}
                                        <div className="control-item">
                                            <div className="control-label">快速設定:</div>
                                            <div className="speed-preset-buttons">
                                                {[1, 3, 5, 7, 10].map(speed => (
                                                    <button
                                                        key={speed}
                                                        className={`speed-preset-btn ${satelliteSpeedMultiplier === speed ? 'active' : ''}`}
                                                        onClick={() => onSatelliteSpeedChange && onSatelliteSpeedChange(speed)}
                                                    >
                                                        {speed}x
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* 時間換算顯示 */}
                                        <div className="control-item time-conversion">
                                            <div className="conversion-info">
                                                <span className="conversion-label">實際時間比例:</span>
                                                <span className="conversion-value">
                                                    1分鐘 = {(60 / satelliteSpeedMultiplier).toFixed(1)}秒
                                                </span>
                                            </div>
                                            <div className="conversion-info">
                                                <span className="conversion-label">軌道週期:</span>
                                                <span className="conversion-value">
                                                    {(109 * 60 / satelliteSpeedMultiplier).toFixed(0)}秒
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* 🚀 換手管理器 - 當衛星連接功能啟用時在背景運行，UI 僅在換手類別中顯示 */}
                                {satelliteEnabled && satelliteUavConnectionEnabled && (
                                    <HandoverManager
                                        satellites={skyfieldSatellites}
                                        selectedUEId={selectedReceiverIds[0]}
                                        isEnabled={true}
                                        mockMode={true}
                                        speedMultiplier={satelliteSpeedMultiplier}
                                        onHandoverStateChange={onHandoverStateChange}
                                        onCurrentConnectionChange={onCurrentConnectionChange}
                                        onPredictedConnectionChange={onPredictedConnectionChange}
                                        onTransitionChange={onTransitionChange}
                                        onAlgorithmResults={onAlgorithmResults}
                                        // 只在換手類別中顯示 UI，但邏輯始終運行
                                        hideUI={activeCategory !== 'handover'}
                                    />
                                )}


                                {/* 手動控制面板 - 當自動飛行開啟時隱藏，且需要手動控制開關啟用 */}
                                {!auto && manualControlEnabled && (
                                    <div className="manual-control-panel">
                                        <div className="manual-control-title">🕹️ UAV 手動控制</div>
                                        <div className="manual-control-grid">
                                            {/* 第一排：↖ ↑ ↗ */}
                                            <div className="manual-row">
                                                <button onMouseDown={() => handleManualDown('left-up')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>↖</button>
                                                <button onMouseDown={() => handleManualDown('descend')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>↑</button>
                                                <button onMouseDown={() => handleManualDown('right-up')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>↗</button>
                                            </div>
                                            {/* 第二排：← ⟲ ⟳ → */}
                                            <div className="manual-row">
                                                <button onMouseDown={() => handleManualDown('left')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>←</button>
                                                <button onMouseDown={() => handleManualDown('rotate-left')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>⟲</button>
                                                <button onMouseDown={() => handleManualDown('rotate-right')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>⟳</button>
                                                <button onMouseDown={() => handleManualDown('right')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>→</button>
                                            </div>
                                            {/* 第三排：↙ ↓ ↘ */}
                                            <div className="manual-row">
                                                <button onMouseDown={() => handleManualDown('left-down')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>↙</button>
                                                <button onMouseDown={() => handleManualDown('ascend')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>↓</button>
                                                <button onMouseDown={() => handleManualDown('right-down')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>↘</button>
                                            </div>
                                            {/* 升降排 */}
                                            <div className="manual-row">
                                                <button onMouseDown={() => handleManualDown('up')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>升</button>
                                                <button onMouseDown={() => handleManualDown('down')} onMouseUp={handleManualUp} onMouseLeave={handleManualUp}>降</button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>

                    {/* UAV 選擇徽章 - 優化版 */}
                    <div className="uav-selection-container">
                        <div 
                            className={`uav-selection-header ${showUavSelection ? 'expanded' : ''}`}
                            onClick={() => setShowUavSelection(!showUavSelection)}
                        >
                            <span className="selection-title">🚁 UAV 接收器選擇</span>
                            <span className="selection-count">
                                {selectedReceiverIds.length} / {devices.filter(d => d.role === 'receiver' && d.id !== null).length}
                            </span>
                            <span className={`header-arrow ${showUavSelection ? 'expanded' : ''}`}>
                                ▼
                            </span>
                        </div>
                        {showUavSelection && (
                            <>
                                <div className="uav-badges-grid">
                                    {devices
                                        .filter(
                                            (device) =>
                                                device.name &&
                                                device.role === 'receiver' &&
                                                device.id !== null
                                        )
                                        .map((device) => {
                                            const isSelected = selectedReceiverIds.includes(
                                                device.id as number
                                            )
                                            // 設備狀態數據
                                            const connectionStatus = device.active ? 'connected' : 'disconnected'
                                            // 基於設備ID生成穩定的模擬數據
                                            const deviceIdNum = typeof device.id === 'number' ? device.id : 0
                                            const signalStrength = (deviceIdNum % 4) + 1 // 1-4 bars，基於ID固定
                                            const batteryLevel = Math.max(20, 100 - (deviceIdNum * 7) % 80) // 20-100%，基於ID固定
                                            
                                            return (
                                                <div
                                                    key={device.id}
                                                    className={`enhanced-uav-badge ${
                                                        isSelected ? 'selected' : ''
                                                    } ${connectionStatus}`}
                                                    onClick={() =>
                                                        handleBadgeClick(device.id as number)
                                                    }
                                                    title={`點擊${isSelected ? '取消選擇' : '選擇'} ${device.name}`}
                                                >
                                                    <div className="badge-header">
                                                        <span className="device-name">{device.name}</span>
                                                        <div className="status-indicators">
                                                            <span className={`connection-dot ${connectionStatus}`}></span>
                                                            <span className="signal-bars">
                                                                {Array.from({ length: 4 }, (_, i) => (
                                                                    <span
                                                                        key={i}
                                                                        className={`signal-bar ${
                                                                            i < signalStrength ? 'active' : ''
                                                                        }`}
                                                                    ></span>
                                                                ))}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="badge-info">
                                                        <div className="info-item">
                                                            <span className="info-label">位置:</span>
                                                            <span className="info-value">
                                                                ({device.position_x !== undefined ? device.position_x.toFixed(1) : '0.0'}, {device.position_y !== undefined ? device.position_y.toFixed(1) : '0.0'}, {device.position_z !== undefined ? device.position_z.toFixed(1) : '0.0'})
                                                            </span>
                                                        </div>
                                                        <div className="info-item">
                                                            <span className="info-label">功率:</span>
                                                            <span className="info-value">
                                                                {device.power_dbm?.toFixed(1) ?? 'N/A'} dBm
                                                            </span>
                                                        </div>
                                                        <div className="info-item">
                                                            <span className="info-label">電量:</span>
                                                            <span className={`battery-level ${
                                                                batteryLevel > 60 ? 'high' : 
                                                                batteryLevel > 30 ? 'medium' : 'low'
                                                            }`}>
                                                                {batteryLevel}%
                                                            </span>
                                                        </div>
                                                    </div>
                                                    {isSelected && (
                                                        <div className="selection-indicator">
                                                            <span className="checkmark">✓</span>
                                                        </div>
                                                    )}
                                                </div>
                                            )
                                        })}
                                </div>
                                {selectedReceiverIds.length > 0 && (
                                    <div className="selection-actions">
                                        <button
                                            className="action-btn clear-selection"
                                            onClick={() => onSelectedReceiversChange && onSelectedReceiversChange([])}
                                        >
                                            清除選擇
                                        </button>
                                        <button
                                            className="action-btn select-all"
                                            onClick={() => {
                                                const allIds = devices
                                                    .filter(d => d.role === 'receiver' && d.id !== null)
                                                    .map(d => d.id as number)
                                                onSelectedReceiversChange && onSelectedReceiversChange(allIds)
                                            }}
                                        >
                                            全部選擇
                                        </button>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </>
            )}

            {/* 設備操作按鈕 */}
            <div className="device-actions">
                <button onClick={onAddDevice} className="action-btn add-btn">
                    ➕ 添加設備
                </button>
                <div className="action-group">
                    <button
                        onClick={onApply}
                        disabled={
                            loading ||
                            apiStatus !== 'connected' ||
                            !hasTempDevices ||
                            auto
                        }
                        className="action-btn apply-btn"
                    >
                        ✅ 套用
                    </button>
                    <button
                        onClick={onCancel}
                        disabled={loading}
                        className="action-btn cancel-btn"
                    >
                        ❌ 取消
                    </button>
                </div>
            </div>

            {/* 設備列表 */}
            <div className="devices-list">
                {/* 新增設備區塊 */}
                {tempDevices.length > 0 && (
                    <>
                        <h3
                            className={`section-header ${showTempDevices ? 'expanded' : ''}`}
                            onClick={() => setShowTempDevices(!showTempDevices)}
                        >
                            <span className="header-icon">➕</span>
                            <span className="header-title">新增設備</span>
                            <span className="header-count">({tempDevices.length})</span>
                        </h3>
                        {showTempDevices &&
                            tempDevices.map((device) => (
                                <DeviceItem
                                    key={device.id}
                                    device={device}
                                    orientationInput={
                                        orientationInputs[device.id] || {
                                            x: '0',
                                            y: '0',
                                            z: '0',
                                        }
                                    }
                                    onDeviceChange={onDeviceChange}
                                    onDeleteDevice={onDeleteDevice}
                                    onOrientationInputChange={
                                        handleDeviceOrientationInputChange
                                    }
                                    onDeviceRoleChange={handleDeviceRoleChange}
                                />
                            ))}
                    </>
                )}

                {/* 衛星資料區塊 */}
                {satelliteEnabled && (
                    <>
                        <h3
                            className={`section-header ${showSkyfieldSection ? 'expanded' : ''}`}
                            onClick={() => setShowSkyfieldSection(!showSkyfieldSection)}
                        >
                            <span className="header-icon">🛰️</span>
                            <span className="header-title">衛星 gNB</span>
                            <span className="header-count">
                                ({loadingSatellites ? '...' : skyfieldSatellites.length})
                            </span>
                        </h3>
                        {showSkyfieldSection && (
                            <div className="satellite-list">
                                {loadingSatellites ? (
                                    <div className="loading-text">正在載入衛星資料...</div>
                                ) : skyfieldSatellites.length > 0 ? (
                                    skyfieldSatellites.map((sat) => (
                                        <div key={sat.norad_id} className="satellite-item">
                                            <div className="satellite-name">
                                                {sat.name} (NORAD: {sat.norad_id})
                                            </div>
                                            <div className="satellite-details">
                                                仰角: <span style={{ color: sat.elevation_deg > 45 ? '#ff3300' : '#0088ff' }}>
                                                    {sat.elevation_deg.toFixed(2)}°
                                                </span>
                                                {' | '}方位角: {sat.azimuth_deg.toFixed(2)}°
                                                {' | '}距離: {sat.distance_km.toFixed(2)} km
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="no-data-text">
                                        無衛星資料可顯示。請調整最低仰角後重試。
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                )}

                {/* 接收器 */}
                {receiverDevices.length > 0 && (
                    <>
                        <h3
                            className={`section-header ${showReceiverDevices ? 'expanded' : ''}`}
                            onClick={() => setShowReceiverDevices(!showReceiverDevices)}
                        >
                            <span className="header-icon">📱</span>
                            <span className="header-title">接收器 Rx</span>
                            <span className="header-count">({receiverDevices.length})</span>
                        </h3>
                        {showReceiverDevices &&
                            receiverDevices.map((device) => (
                                <DeviceItem
                                    key={device.id}
                                    device={device}
                                    orientationInput={
                                        orientationInputs[device.id] || {
                                            x: '0',
                                            y: '0',
                                            z: '0',
                                        }
                                    }
                                    onDeviceChange={onDeviceChange}
                                    onDeleteDevice={onDeleteDevice}
                                    onOrientationInputChange={
                                        handleDeviceOrientationInputChange
                                    }
                                    onDeviceRoleChange={handleDeviceRoleChange}
                                />
                            ))}
                    </>
                )}

                {/* 發射器 */}
                {desiredDevices.length > 0 && (
                    <>
                        <h3
                            className={`section-header ${showDesiredDevices ? 'expanded' : ''}`}
                            onClick={() => setShowDesiredDevices(!showDesiredDevices)}
                        >
                            <span className="header-icon">📡</span>
                            <span className="header-title">發射器 Tx</span>
                            <span className="header-count">({desiredDevices.length})</span>
                        </h3>
                        {showDesiredDevices &&
                            desiredDevices.map((device) => (
                                <DeviceItem
                                    key={device.id}
                                    device={device}
                                    orientationInput={
                                        orientationInputs[device.id] || {
                                            x: '0',
                                            y: '0',
                                            z: '0',
                                        }
                                    }
                                    onDeviceChange={onDeviceChange}
                                    onDeleteDevice={onDeleteDevice}
                                    onOrientationInputChange={
                                        handleDeviceOrientationInputChange
                                    }
                                    onDeviceRoleChange={handleDeviceRoleChange}
                                />
                            ))}
                    </>
                )}

                {/* 干擾源 */}
                {jammerDevices.length > 0 && (
                    <>
                        <h3
                            className={`section-header ${showJammerDevices ? 'expanded' : ''}`}
                            onClick={() => setShowJammerDevices(!showJammerDevices)}
                        >
                            <span className="header-icon">⚡</span>
                            <span className="header-title">干擾源 Jam</span>
                            <span className="header-count">({jammerDevices.length})</span>
                        </h3>
                        {showJammerDevices &&
                            jammerDevices.map((device) => (
                                <DeviceItem
                                    key={device.id}
                                    device={device}
                                    orientationInput={
                                        orientationInputs[device.id] || {
                                            x: '0',
                                            y: '0',
                                            z: '0',
                                        }
                                    }
                                    onDeviceChange={onDeviceChange}
                                    onDeleteDevice={onDeleteDevice}
                                    onOrientationInputChange={
                                        handleDeviceOrientationInputChange
                                    }
                                    onDeviceRoleChange={handleDeviceRoleChange}
                                />
                            ))}
                    </>
                )}
            </div>
        </div>
    )
}

export default EnhancedSidebar