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
    onSatelliteCountChange?: (count: number) => void
    satelliteDisplayCount?: number
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
    handoverPerformanceDashboardEnabled?: boolean
    onHandoverPerformanceDashboardChange?: (enabled: boolean) => void
}

// 功能開關配置
interface FeatureToggle {
    id: string
    label: string
    category: 'basic' | 'phase4' | 'phase5' | 'phase6' | 'phase7' | 'phase8'
    enabled: boolean
    onToggle: (enabled: boolean) => void
    icon?: string
    description?: string
    hidden?: boolean // 新增 hidden 屬性
}

// Helper function to fetch visible satellites
async function fetchVisibleSatellites(
    count: number,
    minElevation: number = 0
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
    onSatelliteCountChange,
    satelliteDisplayCount: propSatelliteDisplayCount = 10,
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
    handoverPerformanceDashboardEnabled = false,
    onHandoverPerformanceDashboardChange,
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
    const [activeCategory, setActiveCategory] = useState<string>('basic')
    const [showTempDevices, setShowTempDevices] = useState(true)
    const [showReceiverDevices, setShowReceiverDevices] = useState(false)
    const [showDesiredDevices, setShowDesiredDevices] = useState(false)
    const [showJammerDevices, setShowJammerDevices] = useState(false)

    // 衛星相關狀態
    const [satelliteDisplayCount, setSatelliteDisplayCount] = useState<number>(
        propSatelliteDisplayCount
    )
    const [skyfieldSatellites, setSkyfieldSatellites] = useState<
        VisibleSatelliteInfo[]
    >([])
    const [showSkyfieldSection, setShowSkyfieldSection] = useState<boolean>(false)
    const [loadingSatellites, setLoadingSatellites] = useState<boolean>(false)
    const [minElevation, setMinElevation] = useState<number>(0)
    const satelliteRefreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

    // 功能開關配置
    const featureToggles: FeatureToggle[] = [
        // 基礎功能
        {
            id: 'auto',
            label: '自動飛行',
            category: 'basic',
            enabled: auto,
            onToggle: onAutoChange,
            icon: '🤖',
            description: 'UAV 自動飛行模式'
        },
        {
            id: 'animation',
            label: 'UAV 動畫',
            category: 'basic',
            enabled: uavAnimation,
            onToggle: onUavAnimationChange,
            icon: '🎬',
            description: 'UAV 飛行動畫效果'
        },
        {
            id: 'manualControl',
            label: '手動控制',
            category: 'basic',
            enabled: manualControlEnabled,
            onToggle: onManualControlEnabledChange || (() => {}),
            icon: '🕹️',
            description: '顯示 UAV 手動控制面板',
            hidden: auto // 自動飛行開啟時隱藏此開關
        },
        {
            id: 'satellite',
            label: '衛星顯示',
            category: 'basic',
            enabled: satelliteEnabled,
            onToggle: onSatelliteEnabledChange || (() => {}),
            icon: '🛰️',
            description: 'OneWeb 衛星星座顯示'
        },
        
        // 階段四功能
        {
            id: 'interferenceVisualization',
            label: '干擾源可視化',
            category: 'phase4',
            enabled: interferenceVisualizationEnabled,
            onToggle: onInterferenceVisualizationChange || (() => {}),
            icon: '📡',
            description: '3D 干擾源範圍和影響可視化'
        },
        {
            id: 'sinrHeatmap',
            label: 'SINR 熱力圖',
            category: 'phase4',
            enabled: sinrHeatmapEnabled,
            onToggle: onSinrHeatmapChange || (() => {}),
            icon: '🔥',
            description: '地面 SINR 信號強度熱力圖'
        },
        {
            id: 'aiRanVisualization',
            label: 'AI-RAN 決策',
            category: 'phase4',
            enabled: aiRanVisualizationEnabled,
            onToggle: onAiRanVisualizationChange || (() => {}),
            icon: '🧠',
            description: 'AI-RAN 抗干擾決策過程可視化'
        },
        {
            id: 'sionna3DVisualization',
            label: 'Sionna 3D 模擬',
            category: 'phase4',
            enabled: sionna3DVisualizationEnabled,
            onToggle: onSionna3DVisualizationChange || (() => {}),
            icon: '📊',
            description: 'Sionna 3D 無線環境模擬與可視化'
        },
        {
            id: 'realTimeMetrics',
            label: '即時性能指標',
            category: 'phase4',
            enabled: realTimeMetricsEnabled,
            onToggle: onRealTimeMetricsChange || (() => {}),
            icon: '⚡',
            description: '即時網路性能指標監控'
        },
        {
            id: 'interferenceAnalytics',
            label: '干擾分析引擎',
            category: 'phase4',
            enabled: interferenceAnalyticsEnabled,
            onToggle: onInterferenceAnalyticsChange || (() => {}),
            icon: '🔍',
            description: '智能干擾模式分析與預測'
        },
        
        // 階段五功能
        {
            id: 'uavSwarmCoordination',
            label: 'UAV 群集協調',
            category: 'phase5',
            enabled: uavSwarmCoordinationEnabled,
            onToggle: onUavSwarmCoordinationChange || (() => {}),
            icon: '🚁',
            description: '多 UAV 編隊飛行與群集協調'
        },
        {
            id: 'meshNetworkTopology',
            label: '網狀網路拓撲',
            category: 'phase5',
            enabled: meshNetworkTopologyEnabled,
            onToggle: onMeshNetworkTopologyChange || (() => {}),
            icon: '🕸️',
            description: '網狀網路拓撲結構可視化'
        },
        {
            id: 'satelliteUavConnection',
            label: '衛星-UAV 連接',
            category: 'phase5',
            enabled: satelliteUavConnectionEnabled,
            onToggle: onSatelliteUavConnectionChange || (() => {}),
            icon: '🛰️',
            description: '衛星與 UAV 連接狀態監控'
        },
        {
            id: 'failoverMechanism',
            label: '故障轉移機制',
            category: 'phase5',
            enabled: failoverMechanismEnabled,
            onToggle: onFailoverMechanismChange || (() => {}),
            icon: '🔄',
            description: '智能網路故障轉移機制'
        },
        // 階段六功能
        {
            id: 'handoverPrediction',
            label: '換手預測分析',
            category: 'phase6',
            enabled: handoverPredictionEnabled,
            onToggle: onHandoverPredictionChange || (() => {}),
            icon: '🔮',
            description: '智能衛星換手預測與時間軸分析'
        },
        {
            id: 'handoverDecisionVisualization',
            label: '換手決策可視化',
            category: 'phase6',
            enabled: handoverDecisionVisualizationEnabled,
            onToggle: onHandoverDecisionVisualizationChange || (() => {}),
            icon: '🧠',
            description: '衛星換手決策過程 3D 可視化'
        },
        {
            id: 'handoverPerformanceDashboard',
            label: '換手性能監控',
            category: 'phase6',
            enabled: handoverPerformanceDashboardEnabled,
            onToggle: onHandoverPerformanceDashboardChange || (() => {}),
            icon: '📊',
            description: '換手性能統計與分析儀表板'
        }
    ]

    // 類別配置
    const categories = [
        { id: 'basic', label: '基礎功能', icon: '⚙️' },
        { id: 'phase4', label: '階段四', icon: '🔬' },
        { id: 'phase5', label: '階段五', icon: '🚁', disabled: false },
        { id: 'phase6', label: '階段六', icon: '🔄', disabled: false },
        { id: 'phase7', label: '階段七', icon: '📊', disabled: true },
        { id: 'phase8', label: '階段八', icon: '🤖', disabled: true },
    ]

    // 衛星數據獲取效果
    useEffect(() => {
        setSatelliteDisplayCount(propSatelliteDisplayCount)
    }, [propSatelliteDisplayCount])

    useEffect(() => {
        const loadSatellites = async () => {
            if (!satelliteEnabled) {
                setSkyfieldSatellites([])
                if (onSatelliteDataUpdate) {
                    onSatelliteDataUpdate([])
                }
                setLoadingSatellites(false)
                return
            }

            setLoadingSatellites(true)
            const satellites = await fetchVisibleSatellites(
                satelliteDisplayCount,
                minElevation
            )

            let sortedSatellites = [...satellites]
            sortedSatellites.sort((a, b) => b.elevation_deg - a.elevation_deg)

            setSkyfieldSatellites(sortedSatellites)

            if (onSatelliteDataUpdate) {
                onSatelliteDataUpdate(sortedSatellites)
            }

            setLoadingSatellites(false)
        }

        if (satelliteRefreshIntervalRef.current) {
            clearInterval(satelliteRefreshIntervalRef.current)
            satelliteRefreshIntervalRef.current = null
        }

        if (satelliteEnabled) {
            loadSatellites()
            satelliteRefreshIntervalRef.current = setInterval(() => {
                console.log('自動刷新衛星數據...')
                loadSatellites()
            }, 60000)
        } else {
            loadSatellites()
        }

        return () => {
            if (satelliteRefreshIntervalRef.current) {
                clearInterval(satelliteRefreshIntervalRef.current)
                satelliteRefreshIntervalRef.current = null
            }
        }
    }, [
        satelliteDisplayCount,
        minElevation,
        onSatelliteDataUpdate,
        satelliteEnabled,
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
    const handleSatelliteCountChange = (count: number) => {
        setSatelliteDisplayCount(count)
        if (onSatelliteCountChange) {
            onSatelliteCountChange(count)
        }
    }

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
                                🎛️ 功能控制面板
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
                                            } ${category.disabled ? 'disabled' : ''}`}
                                            onClick={() => !category.disabled && setActiveCategory(category.id)}
                                            disabled={category.disabled}
                                            title={category.disabled ? '即將推出' : category.label}
                                        >
                                            <span className="tab-icon">{category.icon}</span>
                                            <span className="tab-label">{category.label}</span>
                                        </button>
                                    ))}
                                </div>

                                {/* 功能開關 */}
                                {renderFeatureToggles()}

                                {/* 階段四專用控制面板 */}
                                {activeCategory === 'phase4' && (
                                    <div className="phase4-control-panel">
                                        <div className="phase4-header">
                                            <h4>🔬 階段四：AI-RAN 抗干擾系統</h4>
                                        </div>
                                        
                                        <div className="phase4-status-grid">
                                            <div className="status-item">
                                                <span className="status-label">Sionna 引擎</span>
                                                <span className={`status-indicator ${true ? 'active' : 'inactive'}`}>
                                                    {true ? '🟢 運行中' : '🔴 離線'}
                                                </span>
                                            </div>
                                            
                                            <div className="status-item">
                                                <span className="status-label">AI 決策模型</span>
                                                <span className={`status-indicator ${aiRanVisualizationEnabled ? 'active' : 'inactive'}`}>
                                                    {aiRanVisualizationEnabled ? '🟢 啟用' : '⚪ 待啟用'}
                                                </span>
                                            </div>
                                            
                                            <div className="status-item">
                                                <span className="status-label">干擾檢測</span>
                                                <span className={`status-indicator ${interferenceVisualizationEnabled ? 'active' : 'inactive'}`}>
                                                    {interferenceVisualizationEnabled ? '🟡 監控中' : '⚪ 停用'}
                                                </span>
                                            </div>
                                            
                                            <div className="status-item">
                                                <span className="status-label">SINR 分析</span>
                                                <span className={`status-indicator ${sinrHeatmapEnabled ? 'active' : 'inactive'}`}>
                                                    {sinrHeatmapEnabled ? '🟢 分析中' : '⚪ 停用'}
                                                </span>
                                            </div>
                                        </div>
                                        
                                        <div className="phase4-metrics">
                                            <div className="metric-row">
                                                <span className="metric-label">干擾源數量:</span>
                                                <span className="metric-value">{jammerDevices.length}</span>
                                            </div>
                                            <div className="metric-row">
                                                <span className="metric-label">UAV 連接數:</span>
                                                <span className="metric-value">{receiverDevices.length}</span>
                                            </div>
                                            <div className="metric-row">
                                                <span className="metric-label">平均 SINR:</span>
                                                <span className="metric-value">-85 dBm</span>
                                            </div>
                                        </div>
                                        
                                        <div className="phase4-actions">
                                            <button 
                                                className="phase4-btn optimize-btn"
                                                onClick={() => {
                                                    // 開啟所有階段四功能
                                                    onInterferenceVisualizationChange && onInterferenceVisualizationChange(true)
                                                    onSinrHeatmapChange && onSinrHeatmapChange(true)
                                                    onAiRanVisualizationChange && onAiRanVisualizationChange(true)
                                                    console.log('AI 優化系統已啟動：干擾檢測、SINR分析、智能決策')
                                                }}
                                            >
                                                🧠 啟動 AI 優化
                                            </button>
                                            <button 
                                                className="phase4-btn analyze-btn"
                                                onClick={() => {
                                                    // 只開啟干擾分析
                                                    onInterferenceVisualizationChange && onInterferenceVisualizationChange(true)
                                                    onSinrHeatmapChange && onSinrHeatmapChange(true)
                                                    console.log('執行干擾分析：顯示干擾源和 SINR 熱力圖')
                                                }}
                                            >
                                                🔍 執行干擾分析
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* 衛星設置 */}
                                {satelliteEnabled && (
                                    <div className="satellite-settings">
                                        <div className="setting-row">
                                            <label>衛星數量:</label>
                                            <input
                                                type="number"
                                                value={satelliteDisplayCount}
                                                onChange={(e) => {
                                                    const value = parseInt(e.target.value, 10)
                                                    if (!isNaN(value) && value > 0 && value <= 100) {
                                                        handleSatelliteCountChange(value)
                                                    }
                                                }}
                                                min="1"
                                                max="100"
                                                className="setting-input"
                                            />
                                        </div>
                                        <div className="setting-row">
                                            <label>最低仰角:</label>
                                            <input
                                                type="number"
                                                value={minElevation}
                                                onChange={(e) => {
                                                    const value = parseInt(e.target.value, 10)
                                                    if (!isNaN(value) && value >= 0 && value <= 90) {
                                                        setMinElevation(value)
                                                    }
                                                }}
                                                min="0"
                                                max="90"
                                                className="setting-input"
                                            />
                                        </div>
                                    </div>
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

                    {/* UAV 選擇徽章 */}
                    <div className="uav-selection-container">
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
                                return (
                                    <span
                                        key={device.id}
                                        className={`uav-badge ${
                                            isSelected ? 'selected' : ''
                                        }`}
                                        onClick={() =>
                                            handleBadgeClick(device.id as number)
                                        }
                                    >
                                        {device.name}
                                    </span>
                                )
                            })}
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