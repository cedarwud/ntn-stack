import { Device } from '../../../types/device'
import { VisibleSatelliteInfo } from '../../../types/satellite'

// UAV 手動控制方向定義 - 移動到此處避免循環依賴
export type UAVManualDirection =
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

// 功能開關介面
export interface FeatureToggle {
    id: string
    label: string
    category: 'uav' | 'satellite'
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