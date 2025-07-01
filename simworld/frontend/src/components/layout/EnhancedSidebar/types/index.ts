/**
 * Enhanced Sidebar 類型定義
 */

import { UAVManualDirection } from '../../../domains/device/visualization/UAVFlight'
import { Device } from '../../../../types/device'
import { VisibleSatelliteInfo } from '../../../../types/satellite'

// 基礎 Sidebar Props
export interface EnhancedSidebarProps {
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
  
  // 衛星控制
  satelliteEnabled?: boolean
  onSatelliteEnabledChange?: (enabled: boolean) => void
  
  // 階段四功能開關
  interferenceVisualizationEnabled?: boolean
  onInterferenceVisualizationChange?: (enabled: boolean) => void
  sinrHeatmapEnabled?: boolean
  onSinrHeatmapChange?: (enabled: boolean) => void
  aiRanVisualizationEnabled?: boolean
  onAiRanVisualizationChange?: (enabled: boolean) => void
  manualControlEnabled?: boolean
  onManualControlEnabledChange?: (enabled: boolean) => void
  
  // 擴展功能
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
}

// 功能切換開關配置
export interface FeatureToggle {
  id: string
  label: string
  category: string
  enabled?: boolean
  onToggle: (enabled: boolean) => void
  icon: string
  description: string
  dependency?: string // 依賴的其他功能
}

// 類別配置
export interface Category {
  id: string
  label: string
  icon: string
}

// 方向輸入
export interface OrientationInput {
  x: string
  y: string
  z: string
}

// 衛星數據狀態
export interface SatelliteDataState {
  satellites: VisibleSatelliteInfo[]
  isLoading: boolean
  isInitialized: boolean
  error: string | null
}

// 手動控制狀態
export interface ManualControlState {
  enabled: boolean
  activeDirection: UAVManualDirection | null
}

// 設備管理狀態
export interface DeviceManagementState {
  orientationInputs: Record<number, OrientationInput>
  selectedReceivers: number[]
  tempDevices: Device[]
}

// Sidebar 狀態
export interface SidebarState {
  activeCategory: string
  isCollapsed: boolean
  searchQuery: string
}

// 操作類型
export type DeviceOperation = 'add' | 'delete' | 'update' | 'apply' | 'cancel'

// 事件處理器
export interface SidebarEventHandlers {
  onDeviceOperation: (operation: DeviceOperation, deviceId?: number, field?: keyof Device, value?: unknown) => void
  onFeatureToggle: (featureId: string, enabled: boolean) => void
  onCategoryChange: (categoryId: string) => void
  onManualControl: (direction: UAVManualDirection) => void
  onSatelliteUpdate: (satellites: VisibleSatelliteInfo[]) => void
}