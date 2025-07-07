import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
    useUIState,
    useSatelliteState,
    useFeatureState,
    useHandoverState,
} from '../../contexts/appStateHooks'
import { useDeviceContext } from '../../contexts/DeviceContext'
import '../../styles/Sidebar.scss'
import { UAVManualDirection } from '../domains/device/visualization/UAVFlight'
import { Device } from '../../types/device'
import SidebarStarfield from '../shared/ui/effects/SidebarStarfield'
import DeviceItem from '../domains/device/management/DeviceItem'
import { useReceiverSelection } from '../../hooks/useReceiverSelection'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { useStrategy } from '../../hooks/useStrategy'
import { SATELLITE_CONFIG } from '../../config/satellite.config'
import { simWorldApi } from '../../services/simworld-api'
import { SatelliteDebugger } from '../../utils/satelliteDebugger'
// 使用懶加載的 HandoverManager 來優化 bundle size
const HandoverManager = React.lazy(
    () => import('../domains/handover/execution/HandoverManager')
)

interface SidebarProps {
    activeComponent: string
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

// Helper function to fetch visible satellites from multiple constellations using the simWorldApi client
async function fetchVisibleSatellites(
    count: number,
    minElevation: number
): Promise<VisibleSatelliteInfo[]> {
    try {
        console.log(
            `🛰️ EnhancedSidebar: 開始獲取多星座衛星數據 - count: ${count}, minElevation: ${minElevation}`
        )

        const isHealthy = await SatelliteDebugger.quickHealthCheck()
        if (!isHealthy) {
            console.warn(`⚠️ EnhancedSidebar: 衛星API健康檢查失敗，將嘗試繼續`)
        }

        const allSatellites: VisibleSatelliteInfo[] = []
        const constellations = ['starlink', 'oneweb', 'kuiper']

        const fetchPromises = constellations.map(async (constellation) => {
            try {
                const apiUrl = `/api/v1/satellite-ops/visible_satellites?count=${Math.floor(
                    Math.max(count, 50) / constellations.length
                )}&min_elevation_deg=${Math.max(
                    minElevation,
                    0
                )}&constellation=${constellation}`

                const response = await fetch(apiUrl)
                if (!response.ok) {
                    console.warn(
                        `⚠️ EnhancedSidebar: 獲取 ${constellation} 衛星失敗: ${response.status}`
                    )
                    return []
                }

                const data = await response.json()

                if (data?.results?.satellites) {
                    const satellites = data.results.satellites.map(
                        (sat: Record<string, unknown>) => {
                            const noradId = String(
                                sat.norad_id || sat.id || '0'
                            )
                            const position =
                                (sat.position as Record<string, unknown>) || {}
                            const signalQuality =
                                (sat.signal_quality as Record<
                                    string,
                                    unknown
                                >) || {}

                            return {
                                norad_id: parseInt(noradId),
                                name: String(sat.name || 'Unknown'),
                                elevation_deg: Number(
                                    position.elevation ||
                                        signalQuality.elevation_deg ||
                                        0
                                ),
                                azimuth_deg: Number(position.azimuth || 0),
                                distance_km: Number(
                                    position.range ||
                                        signalQuality.range_km ||
                                        0
                                ),
                                line1: `1 ${noradId}U 20001001.00000000  .00000000  00000-0  00000-0 0  9999`,
                                line2: `2 ${noradId}  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000`,
                                constellation: constellation.toUpperCase(),
                            }
                        }
                    )
                    return satellites
                }
                return []
            } catch (error) {
                console.warn(
                    `⚠️ EnhancedSidebar: 獲取 ${constellation} 衛星失敗:`,
                    error
                )
                return []
            }
        })

        const constellationResults = await Promise.all(fetchPromises)
        constellationResults.forEach((satellites) => {
            allSatellites.push(...satellites)
        })

        if (allSatellites.length > 0) {
            return allSatellites
        }

        const data = await simWorldApi.getVisibleSatellites(
            Math.max(minElevation, 0),
            Math.max(count, 50)
        )

        if (!data?.results?.satellites) {
            return []
        }

        const satellites: VisibleSatelliteInfo[] = data.results.satellites.map(
            (sat: any) => {
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
                    line1: sat.tle?.line1 || '',
                    line2: sat.tle?.line2 || '',
                    constellation: sat.constellation || 'UNKNOWN',
                }
            }
        )
        return satellites
    } catch (error) {
        console.error('獲取可見衛星時出錯:', error)
        return []
    }
}

const EnhancedSidebar: React.FC<SidebarProps> = ({ activeComponent }) => {
    const {
        auto,
        setAuto,
        uavAnimation,
        setUavAnimation,
        setManualDirection,
        setSelectedReceiverIds,
        selectedReceiverIds,
    } = useUIState()
    const { satelliteEnabled, setSatelliteEnabled, setSkyfieldSatellites } =
        useSatelliteState()
    const {
        handoverMode,
        setHandoverMode,
        setHandoverState,
        setCurrentConnection,
        setPredictedConnection,
        setIsTransitioning,
        setTransitionProgress,
        setAlgorithmResults,
    } = useHandoverState()
    const {
        interferenceVisualizationEnabled,
        sinrHeatmapEnabled,
        manualControlEnabled,
        satelliteUavConnectionEnabled,
        updateFeatureState,
    } = useFeatureState()
    const {
        tempDevices: devices,
        loading,
        apiStatus,
        hasTempDevices,
        applyDeviceChanges,
        deleteDeviceById,
        addNewDevice,
        updateDeviceField,
        cancelDeviceChanges,
    } = useDeviceContext()

    const { currentStrategy } = useStrategy()

    const [activeCategory, setActiveCategory] = useState<
        'uav' | 'satellite' | 'handover_mgr' | 'quality'
    >('uav')
    const [loadingSatellites, setLoadingSatellites] = useState(false)
    const [orientationInputs, setOrientationInputs] = useState<{
        [key: string]: { x: string; y: string; z: string }
    }>({})
    const manualIntervalRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const satelliteRefreshIntervalRef = useRef<NodeJS.Timeout | null>(null)

    const { handleBadgeClick } = useReceiverSelection({
        devices,
        onSelectedReceiversChange: setSelectedReceiverIds,
    })

    const handleSatelliteEnabledToggle = useCallback(
        (enabled: boolean) => {
            setSatelliteEnabled(enabled)
            if (!enabled && satelliteUavConnectionEnabled) {
                updateFeatureState({ satelliteUavConnectionEnabled: false })
            }
        },
        [satelliteUavConnectionEnabled, setSatelliteEnabled, updateFeatureState]
    )

    const handleSatelliteUavConnectionToggle = useCallback(
        (enabled: boolean) => {
            if (enabled && !satelliteEnabled) {
                setSatelliteEnabled(true)
            }
            updateFeatureState({ satelliteUavConnectionEnabled: enabled })
        },
        [satelliteEnabled, setSatelliteEnabled, updateFeatureState]
    )

    const featureToggles: FeatureToggle[] = [
        {
            id: 'auto',
            label: '自動飛行模式',
            category: 'uav',
            enabled: auto,
            onToggle: setAuto,
            icon: '🤖',
        },
        {
            id: 'uavAnimation',
            label: 'UAV 飛行動畫',
            category: 'uav',
            enabled: uavAnimation,
            onToggle: setUavAnimation,
            icon: '🎬',
        },
        {
            id: 'satelliteEnabled',
            label: '衛星星座顯示',
            category: 'satellite',
            enabled: satelliteEnabled,
            onToggle: handleSatelliteEnabledToggle,
            icon: '🛰️',
        },
        {
            id: 'satelliteUAVConnection',
            label: '衛星-UAV 連接',
            category: 'satellite',
            enabled: satelliteUavConnectionEnabled && satelliteEnabled,
            onToggle: handleSatelliteUavConnectionToggle,
            icon: '🔗',
        },
        {
            id: 'sinrHeatmap',
            label: 'SINR 熱力圖',
            category: 'quality',
            enabled: sinrHeatmapEnabled,
            onToggle: (enabled) =>
                updateFeatureState({ sinrHeatmapEnabled: enabled }),
            icon: '🔥',
        },
        {
            id: 'interferenceVisualization',
            label: '干擾源可視化',
            category: 'quality',
            enabled: interferenceVisualizationEnabled,
            onToggle: (enabled) =>
                updateFeatureState({
                    interferenceVisualizationEnabled: enabled,
                }),
            icon: '📡',
        },
    ]

    if (!auto) {
        featureToggles.splice(2, 0, {
            id: 'manualControl',
            label: '手動控制面板',
            category: 'uav',
            enabled: manualControlEnabled,
            onToggle: (enabled) =>
                updateFeatureState({ manualControlEnabled: enabled }),
            icon: '🕹️',
        })
    }

    const categories = [
        { id: 'uav', label: 'UAV 控制', icon: '🚁' },
        { id: 'satellite', label: '衛星控制', icon: '🛰️' },
        { id: 'handover_mgr', label: '換手管理', icon: '🔄' },
        { id: 'quality', label: '通信品質', icon: '📶' },
    ]

    const satelliteDataInitialized = useRef(false)

    useEffect(() => {
        const initializeSatellitesOnce = async () => {
            if (!satelliteEnabled) {
                setSkyfieldSatellites([])
                satelliteDataInitialized.current = false
                setLoadingSatellites(false)
                return
            }

            if (satelliteDataInitialized.current) {
                return
            }

            setLoadingSatellites(true)
            const satellites = await fetchVisibleSatellites(
                SATELLITE_CONFIG.VISIBLE_COUNT,
                SATELLITE_CONFIG.MIN_ELEVATION
            )
            const sortedSatellites = [...satellites].sort(
                (a, b) => b.elevation_deg - a.elevation_deg
            )
            setSkyfieldSatellites(sortedSatellites)
            satelliteDataInitialized.current = true
            setLoadingSatellites(false)
        }

        if (satelliteRefreshIntervalRef.current) {
            clearInterval(satelliteRefreshIntervalRef.current)
            satelliteRefreshIntervalRef.current = null
        }
        initializeSatellitesOnce()

        return () => {
            if (satelliteRefreshIntervalRef.current) {
                clearInterval(satelliteRefreshIntervalRef.current)
                satelliteRefreshIntervalRef.current = null
            }
        }
    }, [satelliteEnabled, setSkyfieldSatellites])

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
                if (
                    JSON.stringify(existingInput) !== JSON.stringify(newInput)
                ) {
                    hasChanges = true
                }
            } else {
                newInputs[device.id] = { x: backendX, y: backendY, z: backendZ }
                hasChanges = true
            }
        })
        if (hasChanges) {
            setOrientationInputs(newInputs)
        }
    }, [devices, orientationInputs])

    const generateDeviceName = (id: number) => `UAV-${id}`

    const handleDeviceOrientationInputChange = (
        deviceId: number,
        axis: 'x' | 'y' | 'z',
        value: string
    ) => {
        setOrientationInputs((prev) => ({
            ...prev,
            [deviceId]: { ...prev[deviceId], [axis]: value },
        }))
    }

    const handleApplyOrientation = (deviceId: number) => {
        const input = orientationInputs[deviceId]
        updateDeviceField(deviceId, 'orientation_x', parseFloat(input.x))
        updateDeviceField(deviceId, 'orientation_y', parseFloat(input.y))
        updateDeviceField(deviceId, 'orientation_z', parseFloat(input.z))
    }

    const handleManualDown = (direction: UAVManualDirection) => {
        setManualDirection(direction)
        if (manualIntervalRef.current) clearInterval(manualIntervalRef.current)
        manualIntervalRef.current = setInterval(() => {
            setManualDirection(direction)
        }, 60)
    }

    const handleManualUp = () => {
        if (manualIntervalRef.current) {
            clearInterval(manualIntervalRef.current)
            manualIntervalRef.current = null
        }
        setManualDirection(null)
    }

    const handleDeviceRoleChange = (deviceId: number, newRole: string) => {
        updateDeviceField(deviceId, 'role', newRole)
    }

    const renderFeatureToggles = () => {
        const currentToggles = featureToggles.filter(
            (toggle) => toggle.category === activeCategory && !toggle.hidden
        )
        return (
            <div className="feature-toggles">
                {currentToggles.map((toggle) => (
                    <div key={toggle.id} className="feature-toggle-item">
                        <label htmlFor={toggle.id}>{toggle.label}</label>
                        <input
                            type="checkbox"
                            id={toggle.id}
                            checked={toggle.enabled}
                            onChange={(e) => toggle.onToggle(e.target.checked)}
                        />
                    </div>
                ))}
            </div>
        )
    }

    if (activeComponent !== '3DRT') {
        return null
    }

    return (
        <div className="sidebar">
            <SidebarStarfield />
            <div className="sidebar-content">
                <div className="sidebar-header">
                    <h2>控制面板</h2>
                    <span
                        className={`api-status ${
                            apiStatus === 'connected'
                                ? 'connected'
                                : 'disconnected'
                        }`}
                    >
                        {apiStatus === 'connected' ? '已連接' : '未連接'}
                    </span>
                </div>

                <div className="sidebar-section">
                    <div className="device-list-header">
                        <h3>設備列表</h3>
                        <div className="header-actions">
                            <button
                                onClick={() => addNewDevice()}
                                disabled={loading}
                                className="action-btn"
                            >
                                + 添加
                            </button>
                            <button
                                onClick={() => applyDeviceChanges()}
                                disabled={!hasTempDevices || loading}
                                className="action-btn apply"
                            >
                                應用
                            </button>
                            <button
                                onClick={() => cancelDeviceChanges()}
                                disabled={!hasTempDevices || loading}
                                className="action-btn cancel"
                            >
                                取消
                            </button>
                        </div>
                    </div>
                    {loading && <p>加載中...</p>}
                    <div className="device-items-container">
                        {devices.map((device) => (
                            <DeviceItem
                                key={device.id}
                                device={device}
                                onDeviceChange={updateDeviceField}
                                onDeleteDevice={deleteDeviceById}
                                generateDeviceName={generateDeviceName}
                                onOrientationChange={
                                    handleDeviceOrientationInputChange
                                }
                                onApplyOrientation={handleApplyOrientation}
                                onRoleChange={handleDeviceRoleChange}
                                onManualDown={handleManualDown}
                                onManualUp={handleManualUp}
                                selected={selectedReceiverIds.includes(
                                    device.id as number
                                )}
                                onSelect={() =>
                                    handleBadgeClick(device.id as number)
                                }
                            />
                        ))}
                    </div>
                </div>

                <div className="sidebar-section">
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
                                    setActiveCategory(category.id as any)
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
                    <div className="category-content">
                        {renderFeatureToggles()}
                    </div>
                </div>

                {activeCategory === 'handover_mgr' && (
                    <React.Suspense fallback={<div>加載換手管理器...</div>}>
                        <HandoverManager
                            mode={handoverMode}
                            onModeChange={setHandoverMode}
                            onStateChange={setHandoverState}
                            onCurrentConnectionChange={setCurrentConnection}
                            onPredictedConnectionChange={setPredictedConnection}
                            onTransitionChange={(isTransitioning, progress) => {
                                setIsTransitioning(isTransitioning)
                                setTransitionProgress(progress)
                            }}
                            onAlgorithmResults={setAlgorithmResults}
                        />
                    </React.Suspense>
                )}
            </div>
        </div>
    )
}

export default EnhancedSidebar
