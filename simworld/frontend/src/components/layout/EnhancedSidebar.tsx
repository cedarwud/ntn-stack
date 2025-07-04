import React, { useState, useEffect, useRef } from 'react'
import '../../styles/Sidebar.scss'
import { UAVManualDirection } from '../domains/device/visualization/UAVFlight'
import { Device } from '../../types/device'
import SidebarStarfield from '../shared/ui/effects/SidebarStarfield'
import DeviceItem from '../domains/device/management/DeviceItem'
import { useReceiverSelection } from '../../hooks/useReceiverSelection'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { HandoverState, SatelliteConnection } from '../../types/handover'
import { SatellitePosition } from '../../services/simworld-api'
// import { ApiRoutes } from '../../../../config/apiRoutes'
import { generateDeviceName as utilGenerateDeviceName } from '../../utils/deviceName'
import { useStrategy } from '../../hooks/useStrategy'
import { SATELLITE_CONFIG } from '../../config/satellite.config'
import { simWorldApi } from '../../services/simworld-api'
import { SatelliteDebugger } from '../../utils/satelliteDebugger'
// 使用懶加載的 HandoverManager 來優化 bundle size
const HandoverManager = React.lazy(
    () => import('../domains/handover/execution/HandoverManager')
)
// RL 監控已移動到 Chart Analysis Dashboard

interface SidebarProps {
    devices: Device[]
    loading: boolean
    apiStatus: 'disconnected' | 'connected' | 'error'
    onDeviceChange: (id: number, field: keyof Device, value: unknown) => void
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

    // 階段六功能開關 - 已刪除換手相關功能
    predictionPath3DEnabled?: boolean
    onPredictionPath3DChange?: (enabled: boolean) => void
    _predictionAccuracyDashboardEnabled?: boolean
    _onChartAnalysisDashboardChange?: (enabled: boolean) => void
    _coreNetworkSyncEnabled?: boolean
    _onCoreNetworkSyncChange?: (enabled: boolean) => void

    // Stage 3 功能開關
    _realtimePerformanceMonitorEnabled?: boolean
    _onRealtimePerformanceMonitorChange?: (enabled: boolean) => void
    _scenarioTestEnvironmentEnabled?: boolean
    _onScenarioTestEnvironmentChange?: (enabled: boolean) => void

    // 階段七功能開關
    _e2ePerformanceMonitoringEnabled?: boolean
    _onE2EPerformanceMonitoringChange?: (enabled: boolean) => void
    _testResultsVisualizationEnabled?: boolean
    _onTestResultsVisualizationChange?: (enabled: boolean) => void
    _performanceTrendAnalysisEnabled?: boolean
    _onPerformanceTrendAnalysisChange?: (enabled: boolean) => void
    _automatedReportGenerationEnabled?: boolean
    _onAutomatedReportGenerationChange?: (enabled: boolean) => void

    // 階段八功能開關
    _predictiveMaintenanceEnabled?: boolean
    _onPredictiveMaintenanceChange?: (enabled: boolean) => void
    _intelligentRecommendationEnabled?: boolean
    _onIntelligentRecommendationChange?: (enabled: boolean) => void

    // 衛星動畫控制（動畫永遠開啟）
    satelliteSpeedMultiplier?: number
    onSatelliteSpeedChange?: (speed: number) => void

    // 換手模式控制
    handoverMode?: 'demo' | 'real'
    onHandoverModeChange?: (mode: 'demo' | 'real') => void

    // 3D 動畫狀態更新回調
    onHandoverStateChange?: (state: HandoverState) => void
    onCurrentConnectionChange?: (connection: SatelliteConnection) => void
    onPredictedConnectionChange?: (connection: SatelliteConnection) => void
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
    category: 'uav' | 'satellite' | 'handover_mgr' | 'quality'
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

// Helper function to fetch visible satellites from multiple constellations using the simWorldApi client
async function fetchVisibleSatellites(
    count: number,
    minElevation: number
): Promise<VisibleSatelliteInfo[]> {
    try {
        console.log(
            `🛰️ EnhancedSidebar: 開始獲取多星座衛星數據 - count: ${count}, minElevation: ${minElevation}`
        )

        // 🔍 快速健康檢查，減少詳細調試輸出
        const isHealthy = await SatelliteDebugger.quickHealthCheck()
        if (!isHealthy) {
            console.warn(`⚠️ EnhancedSidebar: 衛星API健康檢查失敗，將嘗試繼續`)
        }

        const allSatellites: VisibleSatelliteInfo[] = []
        const constellations = ['starlink', 'oneweb', 'kuiper'] // 支援的星座列表（根據後端數據庫實際擁有的星座）
        
        // 並行獲取多個星座的衛星數據 (使用後端 API 直接調用)
        const fetchPromises = constellations.map(async (constellation) => {
            try {
                // 直接使用後端 API，因為 simWorldApi 暫不支援星座過濾
                const apiUrl = `/api/v1/satellite-ops/visible_satellites?count=${Math.floor(Math.max(count, 50) / constellations.length)}&min_elevation_deg=${Math.max(minElevation, 0)}&constellation=${constellation}`
                
                const response = await fetch(apiUrl)
                if (!response.ok) {
                    console.warn(`⚠️ EnhancedSidebar: 獲取 ${constellation} 衛星失敗: ${response.status}`)
                    return []
                }
                
                const data = await response.json()
                
                if (data?.results?.satellites) {
                    // 標記衛星所屬星座
                    const satellites = data.results.satellites.map((sat: Record<string, unknown>) => {
                        const noradId = String(sat.norad_id || sat.id || '0')
                        const position = sat.position as Record<string, unknown> || {}
                        const signalQuality = sat.signal_quality as Record<string, unknown> || {}
                        
                        return {
                            norad_id: parseInt(noradId),
                            name: String(sat.name || 'Unknown'),
                            elevation_deg: Number(position.elevation || signalQuality.elevation_deg || 0),
                            azimuth_deg: Number(position.azimuth || 0),
                            distance_km: Number(position.range || signalQuality.range_km || 0),
                            line1: `1 ${noradId}U 20001001.00000000  .00000000  00000-0  00000-0 0  9999`,
                            line2: `2 ${noradId}  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000`,
                            constellation: constellation.toUpperCase() // 添加星座標記
                        }
                    })
                    
                    console.log(`🛰️ EnhancedSidebar: 獲取到 ${satellites.length} 顆 ${constellation.toUpperCase()} 衛星`)
                    return satellites
                }
                return []
            } catch (error) {
                console.warn(`⚠️ EnhancedSidebar: 獲取 ${constellation} 衛星失敗:`, error)
                return []
            }
        })
        
        // 等待所有星座數據獲取完成
        const constellationResults = await Promise.all(fetchPromises)
        
        // 合併所有星座的衛星數據
        constellationResults.forEach(satellites => {
            allSatellites.push(...satellites)
        })

        console.log(`🌍 EnhancedSidebar: 總共獲取到 ${allSatellites.length} 顆可見衛星`)

        // 如果獲取到多星座數據，直接返回
        if (allSatellites.length > 0) {
            return allSatellites
        }

        // 如果沒有獲取到多星座數據，嘗試使用原始 API（向後兼容）
        console.log(`🛰️ EnhancedSidebar: 多星座獲取失敗，回退到原始API`)
        const data = await simWorldApi.getVisibleSatellites(
            Math.max(minElevation, 0), // 🌍 使用標準仰角（地平線以上）
            Math.max(count, 50) // 🌍 請求更多衛星，至少50顆
        )

        console.log(
            `🛰️ EnhancedSidebar: API 響應數據結構正常，獲得 ${
                data?.results?.satellites?.length || 0
            } 顆衛星`
        )

        // 詳細檢查 API 響應格式
        if (!data) {
            console.warn(`🛰️ EnhancedSidebar: API 未返回數據`)
            return []
        }

        if (!data.results) {
            console.warn(`🛰️ EnhancedSidebar: API 響應缺少 results 字段`)
            return []
        }

        if (!data.results.satellites) {
            console.warn(
                `🛰️ EnhancedSidebar: API 響應 results 中缺少 satellites 字段`
            )
            return []
        }

        if (!Array.isArray(data.results.satellites)) {
            console.warn(
                `🛰️ EnhancedSidebar: satellites 不是數組，類型: ${typeof data
                    .results.satellites}`
            )
            return []
        }

        if (data.results.satellites.length === 0) {
            console.warn(`🛰️ EnhancedSidebar: API 返回空的衛星數組`)
            return []
        }

        const satellites: VisibleSatelliteInfo[] = data.results.satellites.map(
            (sat: SatellitePosition, _index: number) => {
                return {
                    norad_id: parseInt(sat.norad_id),
                    name: sat.name || 'Unknown',
                    elevation_deg:
                        sat.position?.elevation ||
                        sat.signal_quality?.elevation_deg ||
                        0,
                    azimuth_deg: sat.position?.azimuth || 0,
                    distance_km:
                        sat.position?.range ||
                        sat.signal_quality?.range_km ||
                        0,
                    line1: `1 ${sat.norad_id}U 20001001.00000000  .00000000  00000-0  00000-0 0  9999`,
                    line2: `2 ${sat.norad_id}  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000`,
                }
            }
        )

        console.log(`🛰️ EnhancedSidebar: 成功載入 ${satellites.length} 顆衛星`)

        if (satellites.length < 1) {
            console.warn(
                `⚠️ EnhancedSidebar: 沒有可用衛星 (${satellites.length} 顆)`
            )
            console.warn(`⚠️ 可能原因: 後端TLE數據缺失或API配置問題`)
        } else if (satellites.length === 1) {
            console.warn(
                `⚠️ EnhancedSidebar: 衛星數量極少 (${satellites.length} 顆)`
            )
            console.warn(
                `⚠️ 可能原因: 當前時間點可見衛星較少，或後端數據不完整`
            )
        }

        // 不再使用模擬數據補充，直接返回真實數據
        return satellites
    } catch (error) {
        console.error('❌ EnhancedSidebar: Error fetching satellites:', error)
        console.error('❌ 錯誤詳細信息:', {
            errorName: error?.name,
            errorMessage: error?.message,
            errorStack: error?.stack,
        })

        // 嘗試執行健康檢查以進一步診斷問題
        try {
            const isHealthy = await SatelliteDebugger.quickHealthCheck()
            console.error(`❌ API健康檢查結果: ${isHealthy ? '正常' : '異常'}`)
            if (!isHealthy) {
                console.error(
                    `❌ 建議檢查: 後端服務狀態、網路連接、API路由配置`
                )
            }
        } catch (healthError) {
            console.error(`❌ 健康檢查也失敗:`, healthError)
        }

        // 不再使用模擬數據，返回空數組以便調試
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
    manualControlEnabled = false,
    onManualControlEnabledChange,
    satelliteUavConnectionEnabled = false,
    onSatelliteUavConnectionChange,
    _predictionAccuracyDashboardEnabled = false,
    _onChartAnalysisDashboardChange,
    _coreNetworkSyncEnabled = false,
    _onCoreNetworkSyncChange,
    // Stage 3 功能 props (未使用但保留用於未來功能)
    _realtimePerformanceMonitorEnabled = false,
    _onRealtimePerformanceMonitorChange,
    _scenarioTestEnvironmentEnabled = false,
    _onScenarioTestEnvironmentChange,
    // 階段七功能 props (未使用但保留用於未來功能)
    _e2ePerformanceMonitoringEnabled = false,
    _onE2EPerformanceMonitoringChange,
    _testResultsVisualizationEnabled = false,
    _onTestResultsVisualizationChange,
    _performanceTrendAnalysisEnabled = false,
    _onPerformanceTrendAnalysisChange,
    _automatedReportGenerationEnabled = false,
    _onAutomatedReportGenerationChange,
    // 階段八功能 props (未使用但保留用於未來功能)
    _predictiveMaintenanceEnabled = false,
    _onPredictiveMaintenanceChange,
    _intelligentRecommendationEnabled = false,
    _onIntelligentRecommendationChange,
    // 3D 動畫狀態更新回調
    onHandoverStateChange,
    onCurrentConnectionChange,
    onPredictedConnectionChange,
    onTransitionChange,
    onAlgorithmResults,
    // 衛星動畫控制 props（動畫永遠開啟）
    satelliteSpeedMultiplier = 5,
    onSatelliteSpeedChange,
    // 換手模式控制 props
    handoverMode = 'demo',
    onHandoverModeChange,
}) => {
    // 🎯 使用全域策略狀態
    const { currentStrategy } = useStrategy()

    // 標記未使用但保留的props為已消費（避免TypeScript警告）
    void _predictionAccuracyDashboardEnabled
    void _onChartAnalysisDashboardChange
    void _coreNetworkSyncEnabled
    void _onCoreNetworkSyncChange
    void _realtimePerformanceMonitorEnabled
    void _onRealtimePerformanceMonitorChange
    void _scenarioTestEnvironmentEnabled
    void _onScenarioTestEnvironmentChange
    void _e2ePerformanceMonitoringEnabled
    void _onE2EPerformanceMonitoringChange
    void _testResultsVisualizationEnabled
    void _onTestResultsVisualizationChange
    void _performanceTrendAnalysisEnabled
    void _onPerformanceTrendAnalysisChange
    void _automatedReportGenerationEnabled
    void _onAutomatedReportGenerationChange
    void _predictiveMaintenanceEnabled
    void _onPredictiveMaintenanceChange
    void _intelligentRecommendationEnabled
    void _onIntelligentRecommendationChange

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
    const [activeCategory, setActiveCategory] = useState<string>('uav')
    const [showTempDevices, setShowTempDevices] = useState(true)
    const [showReceiverDevices, setShowReceiverDevices] = useState(false)
    const [showDesiredDevices, setShowDesiredDevices] = useState(false)
    const [showJammerDevices, setShowJammerDevices] = useState(false)
    const [showUavSelection, setShowUavSelection] = useState(false)

    // 衛星相關狀態已移除，使用固定配置
    const [skyfieldSatellites, setSkyfieldSatellites] = useState<
        VisibleSatelliteInfo[]
    >([])
    const [showSkyfieldSection, setShowSkyfieldSection] =
        useState<boolean>(false)
    const [loadingSatellites, setLoadingSatellites] = useState<boolean>(false)
    const satelliteRefreshIntervalRef = useRef<ReturnType<
        typeof setInterval
    > | null>(null)

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

    // 精簡的核心功能開關配置
    const featureToggles: FeatureToggle[] = [
        // UAV 控制 (4個)
        {
            id: 'auto',
            label: '自動飛行模式',
            category: 'uav',
            enabled: auto,
            onToggle: onAutoChange,
            icon: '🤖',
            description: 'UAV 自動飛行模式',
        },
        {
            id: 'uavAnimation',
            label: 'UAV 飛行動畫',
            category: 'uav',
            enabled: uavAnimation,
            onToggle: onUavAnimationChange,
            icon: '🎬',
            description: 'UAV 飛行動畫效果',
        },

        // 衛星控制 (7個 - 包含移動過來的3個換手開關)
        {
            id: 'satelliteEnabled',
            label: '衛星星座顯示',
            category: 'satellite',
            enabled: satelliteEnabled,
            onToggle: handleSatelliteEnabledToggle,
            icon: '🛰️',
            description: 'LEO 衛星星座顯示',
        },
        {
            id: 'satelliteUAVConnection',
            label: '衛星-UAV 連接',
            category: 'satellite',
            enabled: satelliteUavConnectionEnabled && satelliteEnabled, // 只有衛星顯示開啟時才能啟用
            onToggle: handleSatelliteUavConnectionToggle,
            icon: '🔗',
            description: '衛星與 UAV 連接狀態監控（需先開啟衛星顯示）',
        },

        // 通信品質 (2個)
        {
            id: 'sinrHeatmap',
            label: 'SINR 熱力圖',
            category: 'quality',
            enabled: sinrHeatmapEnabled,
            onToggle: onSinrHeatmapChange || (() => {}),
            icon: '🔥',
            description: '地面 SINR 信號強度熱力圖',
        },
        {
            id: 'interferenceVisualization',
            label: '干擾源可視化',
            category: 'quality',
            enabled: interferenceVisualizationEnabled,
            onToggle: onInterferenceVisualizationChange || (() => {}),
            icon: '📡',
            description: '3D 干擾源範圍和影響可視化',
        },

        // 手動控制面板會根據自動飛行狀態動態顯示
        // 隱藏的非核心功能：predictionAccuracyDashboard, predictionPath3D, coreNetworkSync 等 17 個功能
    ]

    // 動態添加手動控制開關（當自動飛行關閉時）
    if (!auto) {
        featureToggles.splice(2, 0, {
            id: 'manualControl',
            label: '手動控制面板',
            category: 'uav',
            enabled: manualControlEnabled,
            onToggle: onManualControlEnabledChange || (() => {}),
            icon: '🕹️',
            description: '顯示 UAV 手動控制面板',
        })
    }

    // 精簡的類別配置 - 4 個分頁
    const categories = [
        { id: 'uav', label: 'UAV 控制', icon: '🚁' },
        { id: 'satellite', label: '衛星控制', icon: '🛰️' },
        { id: 'handover_mgr', label: '換手管理', icon: '🔄' },
        { id: 'quality', label: '通信品質', icon: '📶' },
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
                console.log(
                    '🛰️ 衛星數據已初始化，使用內在軌道運動，避免重新載入'
                )
                return
            }

            console.log('🛰️ 首次初始化衛星數據...')
            setLoadingSatellites(true)

            const satellites = await fetchVisibleSatellites(
                SATELLITE_CONFIG.VISIBLE_COUNT,
                SATELLITE_CONFIG.MIN_ELEVATION
            )

            const sortedSatellites = [...satellites]
            sortedSatellites.sort((a, b) => b.elevation_deg - a.elevation_deg)

            setSkyfieldSatellites(sortedSatellites)

            if (onSatelliteDataUpdate) {
                onSatelliteDataUpdate(sortedSatellites)
            }

            satelliteDataInitialized.current = true
            setLoadingSatellites(false)
            // 衛星數據初始化完成
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
        onSatelliteDataUpdate,
        // 移除其他依賴，避免重新載入
    ])

    // 設備方向輸入處理 - 修復無限循環問題
    useEffect(() => {
        const newInputs: {
            [key: string]: { x: string; y: string; z: string }
        } = {}
        let hasChanges = false

        devices.forEach((device) => {
            const existingInput = orientationInputs[device.id]
            const backendX = device.orientation_x?.toString() || '0'
            const backendY = device.orientation_y?.toString() || '0'
            const backendZ = device.orientation_z?.toString() || '0'

            if (existingInput) {
                const newInput = {
                    x:
                        existingInput.x !== '0' && existingInput.x !== backendX
                            ? existingInput.x
                            : backendX,
                    y:
                        existingInput.y !== '0' && existingInput.y !== backendY
                            ? existingInput.y
                            : backendY,
                    z:
                        existingInput.z !== '0' && existingInput.z !== backendZ
                            ? existingInput.z
                            : backendZ,
                }
                newInputs[device.id] = newInput

                // 檢查是否有實際變化
                if (
                    JSON.stringify(existingInput) !== JSON.stringify(newInput)
                ) {
                    hasChanges = true
                }
            } else {
                newInputs[device.id] = {
                    x: backendX,
                    y: backendY,
                    z: backendZ,
                }
                hasChanges = true
            }
        })

        // 只有在有實際變化時才更新狀態
        if (hasChanges) {
            setOrientationInputs(newInputs)
        }
    }, [devices, orientationInputs])

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
            } else {
                const numValue = parseFloat(value)
                if (!isNaN(numValue)) {
                    const orientationKey = `orientation_${axis}` as keyof Device
                    onDeviceChange(deviceId, orientationKey, numValue)
                }
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
            (toggle) => toggle.category === activeCategory && !toggle.hidden
        )

        return (
            <div className="feature-toggles-container">
                {currentToggles.map((toggle) => (
                    <div
                        key={toggle.id}
                        className={`feature-toggle ${
                            toggle.enabled ? 'enabled' : 'disabled'
                        }`}
                        onClick={() => toggle.onToggle(!toggle.enabled)}
                        title={toggle.description}
                    >
                        <div className="toggle-content">
                            <span className="toggle-icon">{toggle.icon}</span>
                            <span className="toggle-label">{toggle.label}</span>
                        </div>
                        <div
                            className={`toggle-switch ${
                                toggle.enabled ? 'on' : 'off'
                            }`}
                        >
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
                        {/* LEO 衛星換手機制控制 - 直接顯示五個分頁 */}
                        <div className="leo-handover-control-section">
                            {/* 類別選擇 */}
                            <div className="category-tabs">
                                {categories.map((category) => (
                                    <button
                                        key={category.id}
                                        className={`category-tab ${
                                            activeCategory === category.id
                                                ? 'active'
                                                : ''
                                        }`}
                                        onClick={() =>
                                            setActiveCategory(category.id)
                                        }
                                        title={category.label}
                                    >
                                        <span className="tab-icon">
                                            {category.icon}
                                        </span>
                                        <span className="tab-label">
                                            {category.label}
                                        </span>
                                    </button>
                                ))}
                            </div>

                            {/* 功能開關 */}
                            {renderFeatureToggles()}

                            {/* 衛星動畫速度控制 - 當衛星啟用時顯示 */}
                            {activeCategory === 'satellite' &&
                                satelliteEnabled && (
                                    <div className="satellite-animation-controls">
                                        <div className="control-section-title">
                                            🔄 換手控制
                                        </div>

                                        {/* 換手模式切換 */}
                                        <div className="control-item">
                                            <div className="handover-mode-switch">
                                                <button
                                                    className={`mode-btn ${
                                                        handoverMode === 'demo'
                                                            ? 'active'
                                                            : ''
                                                    }`}
                                                    onClick={() =>
                                                        onHandoverModeChange &&
                                                        onHandoverModeChange(
                                                            'demo'
                                                        )
                                                    }
                                                >
                                                    🎭 演示模式
                                                </button>
                                                <button
                                                    className={`mode-btn ${
                                                        handoverMode === 'real'
                                                            ? 'active'
                                                            : ''
                                                    }`}
                                                    onClick={() =>
                                                        onHandoverModeChange &&
                                                        onHandoverModeChange(
                                                            'real'
                                                        )
                                                    }
                                                >
                                                    🔗 真實模式
                                                </button>
                                            </div>
                                            <div className="mode-description">
                                                {handoverMode === 'demo'
                                                    ? '20秒演示週期，適合展示和理解'
                                                    : '快速換手週期，對接後端真實數據'}
                                            </div>
                                        </div>

                                        {/* 換手穩定期時間控制 - 根據模式調整範圍 */}
                                        <div className="control-item">
                                            <div className="control-label">
                                                換手穩定期:{' '}
                                                {satelliteSpeedMultiplier}秒
                                                {handoverMode === 'real' &&
                                                    ' (真實模式)'}
                                            </div>
                                            <input
                                                type="range"
                                                min="1"
                                                max="30"
                                                step="1"
                                                value={satelliteSpeedMultiplier}
                                                onChange={(e) =>
                                                    onSatelliteSpeedChange &&
                                                    onSatelliteSpeedChange(
                                                        Number(e.target.value)
                                                    )
                                                }
                                                className="speed-slider"
                                            />
                                            <div className="speed-labels">
                                                <span>1秒</span>
                                                <span>穩定期持續時間</span>
                                                <span>30秒</span>
                                            </div>
                                        </div>

                                        {/* 穩定期預設時間按鈕 - 根據模式調整選項 */}
                                        <div className="control-item">
                                            <div className="control-label">
                                                快速設定:
                                            </div>
                                            <div className="speed-preset-buttons">
                                                {[1, 3, 5, 10, 15, 20, 30].map(
                                                    (duration) => (
                                                        <button
                                                            key={duration}
                                                            className={`speed-preset-btn ${
                                                                satelliteSpeedMultiplier ===
                                                                duration
                                                                    ? 'active'
                                                                    : ''
                                                            }`}
                                                            onClick={() =>
                                                                onSatelliteSpeedChange &&
                                                                onSatelliteSpeedChange(
                                                                    duration
                                                                )
                                                            }
                                                        >
                                                            {duration}秒
                                                        </button>
                                                    )
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}

                            {/* 🚀 換手管理器 - 始終顯示，不需要依賴其他開關 */}
                            <React.Suspense
                                fallback={
                                    <div className="handover-loading">
                                        🔄 載入換手管理器...
                                    </div>
                                }
                            >
                                <HandoverManager
                                    satellites={skyfieldSatellites}
                                    selectedUEId={selectedReceiverIds[0]}
                                    isEnabled={true}
                                    mockMode={false}
                                    speedMultiplier={satelliteSpeedMultiplier}
                                    handoverMode={handoverMode}
                                    handoverStrategy={currentStrategy}
                                    onHandoverStateChange={
                                        onHandoverStateChange
                                    }
                                    onCurrentConnectionChange={
                                        onCurrentConnectionChange
                                    }
                                    onPredictedConnectionChange={
                                        onPredictedConnectionChange
                                    }
                                    onTransitionChange={onTransitionChange}
                                    onAlgorithmResults={onAlgorithmResults}
                                    // 只在換手類別中顯示 UI，但邏輯始終運行
                                    hideUI={activeCategory !== 'handover_mgr'}
                                />
                            </React.Suspense>

                            {/* 手動控制面板 - 當自動飛行開啟時隱藏，且需要手動控制開關啟用 */}
                            {!auto && manualControlEnabled && (
                                <div className="manual-control-panel">
                                    <div className="manual-control-title">
                                        🕹️ UAV 手動控制
                                    </div>
                                    <div className="manual-control-grid">
                                        {/* 第一排：↖ ↑ ↗ */}
                                        <div className="manual-row">
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown('left-up')
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ↖
                                            </button>
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown('descend')
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ↑
                                            </button>
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown('right-up')
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ↗
                                            </button>
                                        </div>
                                        {/* 第二排：← ⟲ ⟳ → */}
                                        <div className="manual-row">
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown('left')
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ←
                                            </button>
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown(
                                                        'rotate-left'
                                                    )
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ⟲
                                            </button>
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown(
                                                        'rotate-right'
                                                    )
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ⟳
                                            </button>
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown('right')
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                →
                                            </button>
                                        </div>
                                        {/* 第三排：↙ ↓ ↘ */}
                                        <div className="manual-row">
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown(
                                                        'left-down'
                                                    )
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ↙
                                            </button>
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown('ascend')
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ↓
                                            </button>
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown(
                                                        'right-down'
                                                    )
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                ↘
                                            </button>
                                        </div>
                                        {/* 升降排 */}
                                        <div className="manual-row">
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown('up')
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                升
                                            </button>
                                            <button
                                                onMouseDown={() =>
                                                    handleManualDown('down')
                                                }
                                                onMouseUp={handleManualUp}
                                                onMouseLeave={handleManualUp}
                                            >
                                                降
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* UAV 選擇徽章 - 優化版 - 只在UAV控制分頁顯示 */}
                    {activeCategory === 'uav' && (
                        <div className="uav-selection-container">
                            <div
                                className={`uav-selection-header ${
                                    showUavSelection ? 'expanded' : ''
                                }`}
                                onClick={() =>
                                    setShowUavSelection(!showUavSelection)
                                }
                            >
                                <span className="selection-title">
                                    🚁 UAV 接收器選擇
                                </span>
                                <span className="selection-count">
                                    {selectedReceiverIds.length} /{' '}
                                    {
                                        devices.filter(
                                            (d) =>
                                                d.role === 'receiver' &&
                                                d.id !== null
                                        ).length
                                    }
                                </span>
                                <span
                                    className={`header-arrow ${
                                        showUavSelection ? 'expanded' : ''
                                    }`}
                                >
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
                                                    device.role ===
                                                        'receiver' &&
                                                    device.id !== null
                                            )
                                            .map((device) => {
                                                const isSelected =
                                                    selectedReceiverIds.includes(
                                                        device.id as number
                                                    )
                                                // 設備狀態數據
                                                const connectionStatus =
                                                    device.active
                                                        ? 'connected'
                                                        : 'disconnected'
                                                // 基於設備ID生成穩定的模擬數據
                                                const deviceIdNum =
                                                    typeof device.id ===
                                                    'number'
                                                        ? device.id
                                                        : 0
                                                const signalStrength =
                                                    (deviceIdNum % 4) + 1 // 1-4 bars，基於ID固定
                                                const batteryLevel = Math.max(
                                                    20,
                                                    100 -
                                                        ((deviceIdNum * 7) % 80)
                                                ) // 20-100%，基於ID固定

                                                return (
                                                    <div
                                                        key={device.id}
                                                        className={`enhanced-uav-badge ${
                                                            isSelected
                                                                ? 'selected'
                                                                : ''
                                                        } ${connectionStatus}`}
                                                        onClick={() =>
                                                            handleBadgeClick(
                                                                device.id as number
                                                            )
                                                        }
                                                        title={`點擊${
                                                            isSelected
                                                                ? '取消選擇'
                                                                : '選擇'
                                                        } ${device.name}`}
                                                    >
                                                        <div className="badge-header">
                                                            <span className="device-name">
                                                                {device.name}
                                                            </span>
                                                            <div className="status-indicators">
                                                                <span
                                                                    className={`connection-dot ${connectionStatus}`}
                                                                ></span>
                                                                <span className="signal-bars">
                                                                    {Array.from(
                                                                        {
                                                                            length: 4,
                                                                        },
                                                                        (
                                                                            _,
                                                                            i
                                                                        ) => (
                                                                            <span
                                                                                key={
                                                                                    i
                                                                                }
                                                                                className={`signal-bar ${
                                                                                    i <
                                                                                    signalStrength
                                                                                        ? 'active'
                                                                                        : ''
                                                                                }`}
                                                                            ></span>
                                                                        )
                                                                    )}
                                                                </span>
                                                            </div>
                                                        </div>
                                                        <div className="badge-info">
                                                            <div className="info-item">
                                                                <span className="info-label">
                                                                    位置:
                                                                </span>
                                                                <span className="info-value">
                                                                    (
                                                                    {device.position_x !==
                                                                    undefined
                                                                        ? device.position_x.toFixed(
                                                                              1
                                                                          )
                                                                        : '0.0'}
                                                                    ,{' '}
                                                                    {device.position_y !==
                                                                    undefined
                                                                        ? device.position_y.toFixed(
                                                                              1
                                                                          )
                                                                        : '0.0'}
                                                                    ,{' '}
                                                                    {device.position_z !==
                                                                    undefined
                                                                        ? device.position_z.toFixed(
                                                                              1
                                                                          )
                                                                        : '0.0'}
                                                                    )
                                                                </span>
                                                            </div>
                                                            <div className="info-item">
                                                                <span className="info-label">
                                                                    功率:
                                                                </span>
                                                                <span className="info-value">
                                                                    {device.power_dbm?.toFixed(
                                                                        1
                                                                    ) ??
                                                                        'N/A'}{' '}
                                                                    dBm
                                                                </span>
                                                            </div>
                                                            <div className="info-item">
                                                                <span className="info-label">
                                                                    電量:
                                                                </span>
                                                                <span
                                                                    className={`battery-level ${
                                                                        batteryLevel >
                                                                        60
                                                                            ? 'high'
                                                                            : batteryLevel >
                                                                              30
                                                                            ? 'medium'
                                                                            : 'low'
                                                                    }`}
                                                                >
                                                                    {
                                                                        batteryLevel
                                                                    }
                                                                    %
                                                                </span>
                                                            </div>
                                                        </div>
                                                        {isSelected && (
                                                            <div className="selection-indicator">
                                                                <span className="checkmark">
                                                                    ✓
                                                                </span>
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
                                                onClick={() =>
                                                    onSelectedReceiversChange &&
                                                    onSelectedReceiversChange(
                                                        []
                                                    )
                                                }
                                            >
                                                清除選擇
                                            </button>
                                            <button
                                                className="action-btn select-all"
                                                onClick={() => {
                                                    const allIds = devices
                                                        .filter(
                                                            (d) =>
                                                                d.role ===
                                                                    'receiver' &&
                                                                d.id !== null
                                                        )
                                                        .map(
                                                            (d) =>
                                                                d.id as number
                                                        )
                                                    if (
                                                        onSelectedReceiversChange
                                                    ) {
                                                        onSelectedReceiversChange(
                                                            allIds
                                                        )
                                                    }
                                                }}
                                            >
                                                全部選擇
                                            </button>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* RL 監控已移動到 Chart Analysis Dashboard */}

            {/* 設備操作按鈕 - 只在UAV控制分頁顯示 */}
            {activeCategory === 'uav' && (
                <>
                    <div className="device-actions">
                        <button
                            onClick={onAddDevice}
                            className="action-btn add-btn"
                        >
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
                                    className={`section-header ${
                                        showTempDevices ? 'expanded' : ''
                                    }`}
                                    onClick={() =>
                                        setShowTempDevices(!showTempDevices)
                                    }
                                >
                                    <span className="header-icon">➕</span>
                                    <span className="header-title">
                                        新增設備
                                    </span>
                                    <span className="header-count">
                                        ({tempDevices.length})
                                    </span>
                                </h3>
                                {showTempDevices &&
                                    tempDevices.map((device) => (
                                        <DeviceItem
                                            key={device.id}
                                            device={device}
                                            orientationInput={
                                                orientationInputs[
                                                    device.id
                                                ] || {
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
                                            onDeviceRoleChange={
                                                handleDeviceRoleChange
                                            }
                                        />
                                    ))}
                            </>
                        )}

                        {/* 衛星資料區塊 */}
                        {satelliteEnabled && (
                            <>
                                <h3
                                    className={`section-header ${
                                        showSkyfieldSection ? 'expanded' : ''
                                    }`}
                                    onClick={() =>
                                        setShowSkyfieldSection(
                                            !showSkyfieldSection
                                        )
                                    }
                                >
                                    <span className="header-icon">🛰️</span>
                                    <span className="header-title">
                                        衛星 gNB
                                    </span>
                                    <span className="header-count">
                                        (
                                        {loadingSatellites
                                            ? '...'
                                            : skyfieldSatellites.length}
                                        )
                                    </span>
                                </h3>
                                {showSkyfieldSection && (
                                    <div className="satellite-list">
                                        {loadingSatellites ? (
                                            <div className="loading-text">
                                                正在載入衛星資料...
                                            </div>
                                        ) : skyfieldSatellites.length > 0 ? (
                                            skyfieldSatellites.map((sat) => (
                                                <div
                                                    key={sat.norad_id}
                                                    className="satellite-item"
                                                >
                                                    <div className="satellite-name">
                                                        {sat.name} (NORAD:{' '}
                                                        {sat.norad_id})
                                                    </div>
                                                    <div className="satellite-details">
                                                        仰角:{' '}
                                                        <span
                                                            style={{
                                                                color:
                                                                    sat.elevation_deg >
                                                                    45
                                                                        ? '#ff3300'
                                                                        : '#0088ff',
                                                            }}
                                                        >
                                                            {sat.elevation_deg.toFixed(
                                                                2
                                                            )}
                                                            °
                                                        </span>
                                                        {' | '}方位角:{' '}
                                                        {sat.azimuth_deg.toFixed(
                                                            2
                                                        )}
                                                        °{' | '}距離:{' '}
                                                        {sat.distance_km.toFixed(
                                                            2
                                                        )}{' '}
                                                        km
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
                                    className={`section-header ${
                                        showReceiverDevices ? 'expanded' : ''
                                    }`}
                                    onClick={() =>
                                        setShowReceiverDevices(
                                            !showReceiverDevices
                                        )
                                    }
                                >
                                    <span className="header-icon">📱</span>
                                    <span className="header-title">
                                        接收器 Rx
                                    </span>
                                    <span className="header-count">
                                        ({receiverDevices.length})
                                    </span>
                                </h3>
                                {showReceiverDevices &&
                                    receiverDevices.map((device) => (
                                        <DeviceItem
                                            key={device.id}
                                            device={device}
                                            orientationInput={
                                                orientationInputs[
                                                    device.id
                                                ] || {
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
                                            onDeviceRoleChange={
                                                handleDeviceRoleChange
                                            }
                                        />
                                    ))}
                            </>
                        )}

                        {/* 發射器 */}
                        {desiredDevices.length > 0 && (
                            <>
                                <h3
                                    className={`section-header ${
                                        showDesiredDevices ? 'expanded' : ''
                                    }`}
                                    onClick={() =>
                                        setShowDesiredDevices(
                                            !showDesiredDevices
                                        )
                                    }
                                >
                                    <span className="header-icon">📡</span>
                                    <span className="header-title">
                                        發射器 Tx
                                    </span>
                                    <span className="header-count">
                                        ({desiredDevices.length})
                                    </span>
                                </h3>
                                {showDesiredDevices &&
                                    desiredDevices.map((device) => (
                                        <DeviceItem
                                            key={device.id}
                                            device={device}
                                            orientationInput={
                                                orientationInputs[
                                                    device.id
                                                ] || {
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
                                            onDeviceRoleChange={
                                                handleDeviceRoleChange
                                            }
                                        />
                                    ))}
                            </>
                        )}

                        {/* 干擾源 */}
                        {jammerDevices.length > 0 && (
                            <>
                                <h3
                                    className={`section-header ${
                                        showJammerDevices ? 'expanded' : ''
                                    }`}
                                    onClick={() =>
                                        setShowJammerDevices(!showJammerDevices)
                                    }
                                >
                                    <span className="header-icon">⚡</span>
                                    <span className="header-title">
                                        干擾源 Jam
                                    </span>
                                    <span className="header-count">
                                        ({jammerDevices.length})
                                    </span>
                                </h3>
                                {showJammerDevices &&
                                    jammerDevices.map((device) => (
                                        <DeviceItem
                                            key={device.id}
                                            device={device}
                                            orientationInput={
                                                orientationInputs[
                                                    device.id
                                                ] || {
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
                                            onDeviceRoleChange={
                                                handleDeviceRoleChange
                                            }
                                        />
                                    ))}
                            </>
                        )}
                    </div>
                </>
            )}
        </div>
    )
}

export default EnhancedSidebar
