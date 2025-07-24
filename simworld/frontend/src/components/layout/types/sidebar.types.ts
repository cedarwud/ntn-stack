import { Device } from '../../../types/device'
import { VisibleSatelliteInfo } from '../../../types/satellite'
import { HandoverState, SatelliteConnection } from '../../../types/handover'
import { UAVManualDirection } from '../../domains/device/visualization/UAVFlight'

// 功能開關介面
export interface FeatureToggle {
    id: string
    label: string
    category: 'uav' | 'satellite' | 'handover_mgr' | 'quality'
    enabled: boolean
    onToggle: (enabled: boolean) => void
    icon?: string
    description?: string
    hidden?: boolean
}

// 類別定義
export interface SidebarCategory {
    id: string
    label: string
    icon: string
}

// 設備選擇相關
export interface DeviceSelectionProps {
    devices: Device[]
    selectedIds: number[]
    onSelectionChange: (ids: number[]) => void
}

// 設備管理相關類型
export interface DeviceOrientationInputs {
    [key: string]: { x: string; y: string; z: string }
}

// UAV 選擇面板 Props
export interface UAVSelectionPanelProps {
    devices: Device[]
    selectedReceiverIds: number[]
    isVisible: boolean
    onSelectionChange?: (ids: number[]) => void
    onBadgeClick: (id: number) => void
}

// 設備列表面板 Props
export interface DeviceListPanelProps {
    devices: Device[]
    tempDevices: Device[]
    receiverDevices: Device[]
    desiredDevices: Device[]
    jammerDevices: Device[]
    skyfieldSatellites: VisibleSatelliteInfo[]
    satelliteEnabled: boolean
    loadingSatellites: boolean
    orientationInputs: DeviceOrientationInputs
    onDeviceChange: (id: number, field: keyof Device, value: unknown) => void
    onDeleteDevice: (id: number) => void
    onOrientationInputChange: (deviceId: number, axis: 'x' | 'y' | 'z', value: string) => void
    onDeviceRoleChange: (deviceId: number, newRole: string) => void
}

// 手動控制面板 Props
export interface ManualControlPanelProps {
    isVisible: boolean
    auto: boolean
    manualControlEnabled: boolean
    onManualControl: (direction: UAVManualDirection) => void
}

// 功能開關管理器 Props
export interface FeatureToggleManagerProps {
    activeCategory: string
    featureToggles: FeatureToggle[]
}

// 類別導航 Props
export interface CategoryNavigationProps {
    categories: SidebarCategory[]
    activeCategory: string
    onCategoryChange: (categoryId: string) => void
}

// 換手管理分頁 Props
export interface HandoverManagementTabProps {
    satellites: VisibleSatelliteInfo[]
    selectedUEId: number
    isVisible: boolean
    handoverMode: 'demo' | 'real'
    satelliteSpeedMultiplier: number
    currentStrategy: string
    // 所有換手相關的回調函數
    onHandoverStateChange?: (state: HandoverState) => void
    onCurrentConnectionChange?: (connection: SatelliteConnection) => void
    onPredictedConnectionChange?: (connection: SatelliteConnection) => void
    onTransitionChange?: (isTransitioning: boolean, progress: number) => void
    onAlgorithmResults?: (results: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }) => void
}

// 衛星數據管理相關
export interface UseSatelliteDataReturn {
    satellites: VisibleSatelliteInfo[]
    loadingSatellites: boolean
    initializeSatellites: () => Promise<void>
    clearSatellites: () => void
}

// 設備管理 Hook 返回值
export interface UseDeviceManagementReturn {
    orientationInputs: DeviceOrientationInputs
    tempDevices: Device[]
    receiverDevices: Device[]
    desiredDevices: Device[]
    jammerDevices: Device[]
    handleOrientationInputChange: (deviceId: number, axis: 'x' | 'y' | 'z', value: string) => void
    handleDeviceRoleChange: (deviceId: number, newRole: string) => void
}