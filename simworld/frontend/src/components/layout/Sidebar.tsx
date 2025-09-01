import React, { useState, useEffect } from 'react'
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
// 🎯 移除未使用的imports（simWorldApi, SatelliteDebugger）
// import { netstackFetch } from '../../config/api-config'
import {
    useSatelliteState,
    useHandoverState,
} from '../../contexts/appStateHooks'
// 🎯 移除重复数据源导入 - 统一使用 satelliteState
// import { useSatelliteData } from '../../contexts/SatelliteDataContext'

// 引入重構後的設備列表模組
import DeviceListPanel from './sidebar/DeviceListPanel'
// 引入重構後的UAV選擇模組
import UAVSelectionPanel from './sidebar/UAVSelectionPanel'

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
//     basic: ['auto', 'satelliteEnabled'],
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

// 🎯 移除直接API調用，改用SatelliteDataContext
// 這確保Sidebar使用Stage 6優化的156衛星池數據而非全量391衛星數據

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
    onManualControl: _onManualControl,
    activeComponent,
    uavAnimation: _uavAnimation,
    onUavAnimationChange,
    onSelectedReceiversChange,
    onSatelliteDataUpdate: _onSatelliteDataUpdate,
    satelliteEnabled = false,
    onSatelliteEnabledChange,

    satelliteUavConnectionEnabled = false,
    onSatelliteUavConnectionChange,
    // 衛星動畫控制 props（動畫永遠開啟）
    satelliteSpeedMultiplier: _satelliteSpeedMultiplier = 5,
    onSatelliteSpeedChange: _onSatelliteSpeedChange,

    // 星座切換 props
    selectedConstellation = 'starlink',
    onConstellationChange: _onConstellationChange,
}) => {
    // 標記未使用的props為已消費（避免TypeScript警告）
    void _satelliteSpeedMultiplier
    void _onSatelliteSpeedChange
    void _onManualControl
    void _uavAnimation
    void _onConstellationChange
    void _onSatelliteDataUpdate

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
    const skyfieldSatellites = satelliteState.skyfieldSatellites || []
    
    // 🎯 移除重复数据源，统一使用 satelliteState
    // const { state: satelliteContextState } = useSatelliteData()
    // const contextSatellites = satelliteContextState.satellites || []
    const [loadingSatellites, setLoadingSatellites] = useState<boolean>(false)

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
        // UAV 控制 (1個)
        {
            id: 'auto',
            label: '自動飛行模式',
            category: 'uav',
            enabled: auto,
            onToggle: (enabled: boolean) => {
                onAutoChange(enabled)
                // 自動飛行模式開啟時同時開啟 UAV 飛行動畫
                onUavAnimationChange(enabled)
            },
            icon: '🤖',
            description: 'UAV 自動飛行模式（包含飛行動畫效果）',
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

        // 隱藏的非核心功能：predictionAccuracyDashboard, predictionPath3D, coreNetworkSync 等 17 個功能
    ]



    // 精簡的類別配置 - 2 個分頁，衛星控制為首位
    const categories = [
        { id: 'satellite', label: '衛星控制', icon: '🛰️' },
        { id: 'uav', label: 'UAV 控制', icon: '🚁' },
    ]

    // 🎯 简化数据管理：完全依赖统一的 SatelliteDataContext，移除重复初始化逻辑
    useEffect(() => {
        // 只处理显示状态，数据由 SatelliteDataContext 统一管理
        if (!satelliteEnabled) {
            setLoadingSatellites(false)
        }
    }, [satelliteEnabled])

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
                                                    onChange={(constellation) => {
                                                        // 處理星座切換
                                                        if (_onConstellationChange) {
                                                            _onConstellationChange(constellation)
                                                        }
                                                    }}
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
