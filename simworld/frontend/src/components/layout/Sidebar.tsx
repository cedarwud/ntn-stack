import React, { useState, useEffect, useRef } from 'react'
import ConstellationSelectorCompact from '../domains/satellite/ConstellationSelectorCompact'
import '../../styles/Sidebar.scss'
import { UAVManualDirection } from './types/sidebar.types'
import { Device } from '../../types/device'
import SidebarStarfield from '../shared/ui/effects/SidebarStarfield'
// import DeviceItem from '../domains/device/management/DeviceItem'
import { useReceiverSelection } from '../../hooks/useReceiverSelection'
import { useDeviceManagement } from './hooks/useDeviceManagement'
import { VisibleSatelliteInfo } from '../../types/satellite'

import { FeatureToggle } from './types/sidebar.types'
// import { SatellitePosition } from '../../services/simworld-api'
// import { ApiRoutes } from '../../../../config/apiRoutes'
// import { generateDeviceName as utilGenerateDeviceName } from '../../utils/deviceName'
import { SATELLITE_CONFIG } from '../../config/satellite.config'
import { simWorldApi } from '../../services/simworld-api'
import { SatelliteDebugger } from '../../utils/satelliteDebugger'
// import { netstackFetch } from '../../config/api-config'
import {
    useSatelliteState,
    useHandoverState,
} from '../../contexts/appStateHooks'

// 引入重構後的設備列表模組
import DeviceListPanel from './sidebar/DeviceListPanel'
// 引入重構後的UAV選擇模組
import UAVSelectionPanel from './sidebar/UAVSelectionPanel'
// 引入重構後的手動控制模組
import ManualControlPanel from './sidebar/ManualControlPanel'
// 引入重構後的功能開關模組
import FeatureToggleManager from './sidebar/FeatureToggleManager'
// 引入重構後的類別導航模組
import CategoryNavigation from './sidebar/CategoryNavigation'
// 移除重複的 Phase 2 組件，使用原有的衛星控制邏輯
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

    aiRanVisualizationEnabled?: boolean
    onAiRanVisualizationChange?: (enabled: boolean) => void
    manualControlEnabled?: boolean
    onManualControlEnabledChange?: (enabled: boolean) => void
    // 新增的擴展功能

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

    // 衛星動畫控制（動畫永遠開啟）
    satelliteSpeedMultiplier?: number
    onSatelliteSpeedChange?: (speed: number) => void

    // 星座切換控制 (根據開發計畫)
    selectedConstellation?: 'starlink' | 'oneweb'
    onConstellationChange?: (constellation: 'starlink' | 'oneweb') => void
}

// 核心功能開關配置 - 根據 paper.md 計畫書精簡

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

//     'meshNetworkTopology', 'failoverMechanism', 'aiRanVisualization'
// ]

// Helper function to fetch visible satellites from multiple constellations using the simWorldApi client
async function _fetchVisibleSatellites(
    count: number,
    minElevation: number,
    constellation: 'starlink' | 'oneweb' = 'starlink'
): Promise<VisibleSatelliteInfo[]> {
    try {
        // 🔍 快速健康檢查，減少詳細調試輸出
        const isHealthy = await SatelliteDebugger.quickHealthCheck()
        if (!isHealthy) {
            console.warn(`⚠️ EnhancedSidebar: 衛星API健康檢查失敗，將嘗試繼續`)
        }

        // 台灣觀測者位置：24°56'39"N 121°22'17"E (根據 CLAUDE.md 要求使用真實地理位置)
        const TAIWAN_OBSERVER = {
            lat: 24.94417, // 24°56'39"N = 24 + 56/60 + 39/3600
            lon: 121.37139, // 121°22'17"E = 121 + 22/60 + 17/3600
            alt: 100, // 台灣平均海拔約100公尺
        }

        // 使用台灣觀測點的新API方式，支援星座篩選
        const satellites = await simWorldApi.getVisibleSatellites(
            Math.max(minElevation, 5), // 使用最低可接受仰角門檻 (5°) 符合FCC規範
            Math.max(count, 50), // 確保請求足夠的衛星數量以支援651+301配置
            TAIWAN_OBSERVER.lat, // 台灣觀測點緯度
            TAIWAN_OBSERVER.lon, // 台灣觀測點經度
            constellation // 傳遞星座篩選參數
        )

        // simWorldApi.getVisibleSatellites 直接返回 SatellitePosition[] 數組
        if (!satellites) {
            console.warn(`🛰️ EnhancedSidebar: API 未返回數據`)
            return []
        }

        if (!Array.isArray(satellites)) {
            console.warn(
                `🛰️ EnhancedSidebar: satellites 不是數組，類型: ${typeof satellites}`
            )
            return []
        }

        // Reduced logging: Only log when significant changes occur (moved to component level)

        // 轉換衛星數據格式 (從 SatellitePosition 到 VisibleSatelliteInfo)
        const _convertedSatellites = satellites.map(
            (sat: Record<string, unknown>) => {
                const noradId = String(sat.norad_id || sat.id || '0')
                const position = (sat.position as Record<string, unknown>) || {}
                const signalQuality =
                    (sat.signal_quality as Record<string, unknown>) || {}

                return {
                    norad_id: parseInt(noradId),
                    name: String(sat.name || 'Unknown'),
                    elevation_deg: Number(
                        position.elevation || signalQuality.elevation_deg || 0
                    ),
                    azimuth_deg: Number(position.azimuth || 0),
                    distance_km: Number(
                        position.range || signalQuality.range_km || 0
                    ),
                    line1: `1 ${noradId}U 20001001.00000000  .00000000  00000-0  00000-0 0  9999`,
                    line2: `2 ${noradId}  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000`,
                    constellation: 'MIXED', // 使用新API時不區分星座
                }
            }
        )

        // 按仰角排序，仰角高的衛星優先
        const sortedSatellites = [...satellites]
        sortedSatellites.sort((a, b) => b.elevation_deg - a.elevation_deg)

        return sortedSatellites
    } catch (error) {
        console.error(`❌ EnhancedSidebar: 獲取台灣觀測點衛星數據失敗:`, error)

        // 嘗試健康檢查
        try {
            const healthStatus = await SatelliteDebugger.quickHealthCheck()
            console.log(`🔍 健康檢查結果: ${healthStatus ? '正常' : '異常'}`)
        } catch (healthError) {
            console.error(`❌ 健康檢查也失敗:`, healthError)
        }

        // 不再使用模擬數據，返回空數組以便調試
        return []
    }
}

const Sidebar: React.FC<SidebarProps> = ({
    devices = [],
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

    manualControlEnabled = false,
    onManualControlEnabledChange,
    satelliteUavConnectionEnabled = false,
    onSatelliteUavConnectionChange,
    // 衛星動畫控制 props（動畫永遠開啟）
    satelliteSpeedMultiplier: _satelliteSpeedMultiplier = 5,
    onSatelliteSpeedChange: _onSatelliteSpeedChange,

    // 星座切換 props
    selectedConstellation = 'starlink',
    onConstellationChange,
}) => {
    // 標記未使用的props為已消費（避免TypeScript警告）
    void _satelliteSpeedMultiplier
    void _onSatelliteSpeedChange

    // 🎯 使用換手狀態
    const {
        satelliteMovementSpeed,
        setSatelliteMovementSpeed,
    } = useHandoverState()


    // 使用設備管理 Hook
    const {
        orientationInputs,
        tempDevices,
        receiverDevices,
        desiredDevices,
        jammerDevices,
        handleOrientationInputChange,
        handleDeviceRoleChange,
    } = useDeviceManagement({ devices, onDeviceChange })

    const { selectedReceiverIds, handleBadgeClick } = useReceiverSelection({
        devices,
        onSelectedReceiversChange,
    })

    // 擴展的UI狀態 - 衛星控制為默認分頁
    const [activeCategory, setActiveCategory] = useState<string>('satellite')

    // 使用 NetStack 預計算衛星數據，支援星座切換
    const satelliteState = useSatelliteState()
    const { setSkyfieldSatellites } = satelliteState
    const skyfieldSatellites = satelliteState.skyfieldSatellites || []
    const [loadingSatellites, setLoadingSatellites] = useState<boolean>(false)
    const satelliteRefreshIntervalRef = useRef<ReturnType<
        typeof setInterval
    > | null>(null)
    const onSatelliteDataUpdateRef = useRef(onSatelliteDataUpdate)
    
    // Update ref when prop changes
    useEffect(() => {
        onSatelliteDataUpdateRef.current = onSatelliteDataUpdate
    }, [onSatelliteDataUpdate])

    // 處理衛星星座顯示開關，連帶控制換手動畫顯示
    const handleSatelliteEnabledToggle = (enabled: boolean) => {
        // 調用原始的衛星顯示開關處理函數
        if (onSatelliteEnabledChange) {
            onSatelliteEnabledChange(enabled)
        }

        // 如果關閉衛星顯示，同時關閉換手動畫顯示
        if (!enabled && satelliteUavConnectionEnabled) {
            if (onSatelliteUavConnectionChange) {
                onSatelliteUavConnectionChange(false)
            }
        }
    }

    // 處理換手動畫顯示開關，連動開啟衛星顯示
    const handleSatelliteUavConnectionToggle = (enabled: boolean) => {
        if (enabled && !satelliteEnabled) {
            // 如果開啟換手動畫顯示但衛星顯示未開啟，則自動開啟衛星顯示
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
            label: '衛星星座',
            category: 'satellite',
            enabled: satelliteEnabled,
            onToggle: handleSatelliteEnabledToggle,
            icon: '🛰️',
            description: 'LEO 衛星星座顯示',
        },
        {
            id: 'satelliteUAVConnection',
            label: '換手動畫',
            category: 'satellite',
            enabled: satelliteUavConnectionEnabled && satelliteEnabled, // 只有衛星顯示開啟時才能啟用
            onToggle: handleSatelliteUavConnectionToggle,
            icon: '🔗',
            description: '衛星與 UAV 連接狀態監控（需先開啟衛星顯示）',
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

    // 精簡的類別配置 - 2 個分頁，衛星控制為首位
    const categories = [
        { id: 'satellite', label: '衛星控制', icon: '🛰️' },
        { id: 'uav', label: 'UAV 控制', icon: '🚁' },
    ]

    // 靜態衛星數據管理：完全避免重新載入和重新渲染
    const satelliteDataInitialized = useRef(false)
    const lastConstellationRef = useRef<string>(selectedConstellation)

    useEffect(() => {
        // 只在首次啟用衛星時載入一次，之後完全依賴內在軌道運動
        const initializeSatellitesOnce = async () => {
            if (!satelliteEnabled) {
                setSkyfieldSatellites([])
                if (onSatelliteDataUpdateRef.current) {
                    onSatelliteDataUpdateRef.current([])
                }
                satelliteDataInitialized.current = false
                setLoadingSatellites(false)
                return
            }

            // 檢查星座是否變化，如果變化則需要重新載入
            if (lastConstellationRef.current !== selectedConstellation) {
                console.log(`🔄 星座切換: ${lastConstellationRef.current} -> ${selectedConstellation}，重新載入衛星數據`)
                satelliteDataInitialized.current = false
                lastConstellationRef.current = selectedConstellation
            }

            // 如果已經初始化過且星座沒有變化，就不再重新載入
            if (satelliteDataInitialized.current && lastConstellationRef.current === selectedConstellation) {
                // console.log(
                //     '🛰️ 衛星數據已初始化，使用內在軌道運動，避免重新載入'
                // )
                return
            }

            // console.log(`🛰️ 初始化 ${selectedConstellation} 星座衛星數據...`)
            setLoadingSatellites(true)

            // 直接調用 API 獲取當前星座的衛星數據
            try {
                // 根據新的651+301完整軌道週期配置，請求足夠的衛星數量
                // Starlink: 651顆衛星池, OneWeb: 301顆衛星池
                const requestCount = selectedConstellation === 'starlink' ? 100 : 50  // 實用顯示數量
                // 使用標準服務仰角門檻 (10°) - 符合3GPP NTN標準和ITU-R建議
                const newSatellites = await _fetchVisibleSatellites(requestCount, 10, selectedConstellation)
                
                // Final result: Show data source type only
                console.log(`🛰️ 衛星數據來源: 真實軌道計算 (NetStack API) - ${newSatellites.length} 顆衛星`)
                
                if (onSatelliteDataUpdateRef.current) {
                    onSatelliteDataUpdateRef.current(newSatellites)
                    // console.log(`🛰️ EnhancedSidebar: 成功載入 ${selectedConstellation} 星座 ${newSatellites.length} 顆衛星`)
                }

                satelliteDataInitialized.current = true
                setLoadingSatellites(false)
            } catch (error) {
                console.error(`❌ 載入 ${selectedConstellation} 星座衛星數據失敗:`, error)
                setLoadingSatellites(false)
            }
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
        selectedConstellation, // 當星座選擇變化時重新載入衛星數據
        setSkyfieldSatellites, // 包含 setSkyfieldSatellites 依賴
        // 移除 onSatelliteDataUpdate 和 skyfieldSatellites 避免無限循環
    ])

    // 處理衛星顯示數量變更

    return (
        <div className="enhanced-sidebar-container">
            <SidebarStarfield />

            {activeComponent !== '2DRT' && (
                <>
                    {/* 功能控制面板 */}
                    <div className="control-panel">
                        {/* LEO 衛星換手機制控制 - 直接顯示五個分頁 */}
                        <div className="leo-handover-control-section">
                            {/* 類別選擇 - 使用獨立模組 */}
                            <CategoryNavigation
                                categories={categories}
                                activeCategory={activeCategory}
                                onCategoryChange={setActiveCategory}
                            />

                            {/* 功能開關 - 使用獨立模組 */}
                            <FeatureToggleManager
                                activeCategory={activeCategory}
                                featureToggles={featureToggles}
                            />

                            {/* Phase 2: 衛星控制分頁 - 當衛星控制分頁啟用且衛星啟用時顯示 */}
                            {activeCategory === 'satellite' &&
                                satelliteEnabled && (
                                    <div className="satellite-animation-controls">
                                        {/* 星座選擇器 */}
                                        <div className="control-section-title">
                                            🛰️ 星座系統選擇
                                        </div>
                                        <div className="control-item">
                                            <div className="constellation-selector">
                                                <ConstellationSelectorCompact
                                                    value={selectedConstellation}
                                                    onChange={onConstellationChange || (() => {})}
                                                    disabled={!satelliteEnabled}
                                                />
                                            </div>
                                        </div>

                                        {/* 衛星移動速度控制 */}
                                        <div className="control-item">
                                            <div className="control-label">
                                                衛星移動速度:{' '}
                                                {satelliteMovementSpeed}倍
                                            </div>
                                            <input
                                                type="range"
                                                min="1"
                                                max="60"
                                                step="1"
                                                value={
                                                    satelliteMovementSpeed ||
                                                    SATELLITE_CONFIG.SATELLITE_MOVEMENT_SPEED
                                                }
                                                onChange={(e) =>
                                                    setSatelliteMovementSpeed &&
                                                    setSatelliteMovementSpeed(
                                                        Number(e.target.value)
                                                    )
                                                }
                                                className="speed-slider"
                                            />
                                            <div className="speed-labels">
                                                <span>1倍</span>
                                                <span>衛星3D移動速度</span>
                                                <span>60倍</span>
                                            </div>
                                        </div>

                                        {/* 衛星移動速度快速設定 */}
                                        <div className="control-item">
                                            <div className="control-label">
                                                衛星移動快速設定:
                                            </div>
                                            <div className="speed-preset-buttons">
                                                {[1, 5, 10, 20, 30, 60].map(
                                                    (speed) => (
                                                        <button
                                                            key={speed}
                                                            className={`speed-preset-btn ${
                                                                satelliteMovementSpeed ===
                                                                speed
                                                                    ? 'active'
                                                                    : ''
                                                            }`}
                                                            onClick={() =>
                                                                setSatelliteMovementSpeed &&
                                                                setSatelliteMovementSpeed(
                                                                    speed
                                                                )
                                                            }
                                                        >
                                                            {speed}倍
                                                        </button>
                                                    )
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}

                            {/* 手動控制面板 - 使用獨立模組 */}
                            <ManualControlPanel
                                isVisible={activeCategory === 'uav'}
                                auto={auto}
                                manualControlEnabled={manualControlEnabled}
                                onManualControl={onManualControl}
                            />
                        </div>
                    </div>

                    {/* UAV 選擇面板 - 使用獨立模組 */}
                    <UAVSelectionPanel
                        devices={devices}
                        selectedReceiverIds={selectedReceiverIds}
                        isVisible={activeCategory === 'uav'}
                        onSelectionChange={onSelectedReceiversChange}
                        onBadgeClick={handleBadgeClick}
                    />
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

                    {/* UAV 設備列表 - 使用獨立模組（不包含衛星） */}
                    <DeviceListPanel
                        devices={devices}
                        tempDevices={tempDevices}
                        receiverDevices={receiverDevices}
                        desiredDevices={desiredDevices}
                        jammerDevices={jammerDevices}
                        skyfieldSatellites={[]} // UAV 分頁不顯示衛星
                        satelliteEnabled={false} // UAV 分頁不顯示衛星
                        loadingSatellites={false}
                        orientationInputs={orientationInputs}
                        onDeviceChange={onDeviceChange}
                        onDeleteDevice={onDeleteDevice}
                        onOrientationInputChange={handleOrientationInputChange}
                        onDeviceRoleChange={handleDeviceRoleChange}
                    />
                </>
            )}

            {/* 衛星 gNB 列表 - 移動到衛星控制分頁 */}
            {activeCategory === 'satellite' && satelliteEnabled && (
                <div className="satellite-gnb-section">
                    <DeviceListPanel
                        devices={[]} // 衛星分頁不顯示 UAV 設備
                        tempDevices={[]}
                        receiverDevices={[]}
                        desiredDevices={[]}
                        jammerDevices={[]}
                        skyfieldSatellites={skyfieldSatellites}
                        satelliteEnabled={satelliteEnabled}
                        loadingSatellites={loadingSatellites}
                        orientationInputs={orientationInputs}
                        onDeviceChange={() => {}} // 衛星分頁不需要設備操作功能
                        onDeleteDevice={() => {}}
                        onOrientationInputChange={() => {}}
                        onDeviceRoleChange={() => {}}
                    />
                </div>
            )}
        </div>
    )
}

export default Sidebar
