import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import NetworkTopologyChart from './charts/NetworkTopologyChart'
import PerformanceMetricsPanel from './panels/PerformanceMetricsPanel'
import SatelliteOrbitView from './views/SatelliteOrbitView'
import UAVFlightTracker from './views/UAVFlightTracker'
import RealTimeMetrics from './panels/RealTimeMetrics'
import AlertsPanel from './panels/AlertsPanel'
import ControlPanel from './panels/ControlPanel'
import SystemOverview from './panels/SystemOverview'
import { useWebSocket } from '../../hooks/useWebSocket'
import { useApiData } from '../../hooks/useApiData'
import './Dashboard.scss'

interface DashboardProps {
    currentScene: string
}

interface DashboardLayout {
    id: string
    name: string
    components: {
        [key: string]: {
            x: number
            y: number
            w: number
            h: number
        }
    }
}

const Dashboard: React.FC<DashboardProps> = ({ currentScene }) => {
    const navigate = useNavigate()
    const { scenes } = useParams<{ scenes: string }>()

    // 狀態管理
    const [selectedLayout, setSelectedLayout] = useState<string>('overview')
    const [isFullscreen, setIsFullscreen] = useState<string | null>(null)
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
    const [autoRefresh, setAutoRefresh] = useState(true)
    const [refreshInterval, setRefreshInterval] = useState(5000) // 5秒

    // WebSocket 連接狀態
    const {
        data: wsData,
        connected: wsConnected,
        connect: wsConnect,
        disconnect: wsDisconnect,
    } = useWebSocket(`ws://localhost:8080/api/v1/ws/network-status`)

    // API 數據管理
    const {
        data: systemData,
        loading: systemLoading,
        error: systemError,
        refetch: refetchSystem,
    } = useApiData('/api/v1/system/status')

    const {
        data: networkTopology,
        loading: topologyLoading,
        refetch: refetchTopology,
    } = useApiData('/api/v1/mesh/topology')

    const {
        data: performanceMetrics,
        loading: metricsLoading,
        refetch: refetchMetrics,
    } = useApiData('/api/v1/system/metrics')

    // 定義儀表板佈局
    const dashboardLayouts: DashboardLayout[] = [
        {
            id: 'overview',
            name: '系統總覽',
            components: {
                systemOverview: { x: 0, y: 0, w: 6, h: 2 },
                networkTopology: { x: 6, y: 0, w: 6, h: 6 },
                realTimeMetrics: { x: 0, y: 2, w: 6, h: 4 },
                alertsPanel: { x: 0, y: 6, w: 12, h: 2 },
            },
        },
        {
            id: 'network',
            name: '網絡監控',
            components: {
                networkTopology: { x: 0, y: 0, w: 8, h: 6 },
                performanceMetrics: { x: 8, y: 0, w: 4, h: 6 },
                realTimeMetrics: { x: 0, y: 6, w: 12, h: 2 },
            },
        },
        {
            id: 'uav',
            name: 'UAV 追蹤',
            components: {
                uavTracker: { x: 0, y: 0, w: 8, h: 6 },
                satelliteView: { x: 8, y: 0, w: 4, h: 6 },
                controlPanel: { x: 0, y: 6, w: 12, h: 2 },
            },
        },
    ]

    // 自動刷新邏輯
    useEffect(() => {
        if (!autoRefresh) return

        const interval = setInterval(() => {
            refetchSystem()
            refetchTopology()
            refetchMetrics()
        }, refreshInterval)

        return () => clearInterval(interval)
    }, [
        autoRefresh,
        refreshInterval,
        refetchSystem,
        refetchTopology,
        refetchMetrics,
    ])

    // WebSocket 連接管理
    useEffect(() => {
        if (autoRefresh) {
            wsConnect()
        } else {
            wsDisconnect()
        }

        return () => wsDisconnect()
    }, [autoRefresh, wsConnect, wsDisconnect])

    // 佈局管理
    const currentLayout =
        dashboardLayouts.find((layout) => layout.id === selectedLayout) ||
        dashboardLayouts[0]

    // 組件渲染映射
    const renderComponent = (componentId: string, layout: any) => {
        const commonProps = {
            style: {
                gridColumn: `${layout.x + 1} / span ${layout.w}`,
                gridRow: `${layout.y + 1} / span ${layout.h}`,
            },
            isFullscreen: isFullscreen === componentId,
            onFullscreen: () =>
                setIsFullscreen(
                    isFullscreen === componentId ? null : componentId
                ),
            currentScene,
        }

        switch (componentId) {
            case 'systemOverview':
                return (
                    <SystemOverview
                        key={componentId}
                        {...commonProps}
                        data={systemData}
                        loading={systemLoading}
                        error={systemError}
                    />
                )

            case 'networkTopology':
                return (
                    <NetworkTopologyChart
                        key={componentId}
                        {...commonProps}
                        data={networkTopology}
                        loading={topologyLoading}
                        onNodeClick={(nodeId: string) => {
                            console.log('Node clicked:', nodeId)
                        }}
                    />
                )

            case 'performanceMetrics':
                return (
                    <PerformanceMetricsPanel
                        key={componentId}
                        {...commonProps}
                        data={performanceMetrics}
                        loading={metricsLoading}
                    />
                )

            case 'realTimeMetrics':
                return (
                    <RealTimeMetrics
                        key={componentId}
                        {...commonProps}
                        wsData={wsData}
                        connected={wsConnected}
                    />
                )

            case 'satelliteView':
                return (
                    <SatelliteOrbitView
                        key={componentId}
                        {...commonProps}
                        currentScene={currentScene}
                    />
                )

            case 'uavTracker':
                return (
                    <UAVFlightTracker
                        key={componentId}
                        {...commonProps}
                        currentScene={currentScene}
                    />
                )

            case 'alertsPanel':
                return (
                    <AlertsPanel
                        key={componentId}
                        {...commonProps}
                        alerts={[]} // TODO: 實現告警數據
                    />
                )

            case 'controlPanel':
                return (
                    <ControlPanel
                        key={componentId}
                        {...commonProps}
                        onCommand={(command: string, params: any) => {
                            console.log('Command:', command, params)
                        }}
                    />
                )

            default:
                return (
                    <div
                        key={componentId}
                        {...commonProps}
                        className="dashboard-placeholder"
                    >
                        <p>組件 {componentId} 開發中...</p>
                    </div>
                )
        }
    }

    return (
        <div className={`dashboard ${isFullscreen ? 'fullscreen' : ''}`}>
            {/* 控制欄 */}
            <div className="dashboard-controls">
                <div className="layout-selector">
                    {dashboardLayouts.map((layout) => (
                        <button
                            key={layout.id}
                            className={`layout-btn ${
                                selectedLayout === layout.id ? 'active' : ''
                            }`}
                            onClick={() => setSelectedLayout(layout.id)}
                        >
                            {layout.name}
                        </button>
                    ))}
                </div>

                <div className="dashboard-settings">
                    <div className="refresh-controls">
                        <label className="auto-refresh">
                            <input
                                type="checkbox"
                                checked={autoRefresh}
                                onChange={(e) =>
                                    setAutoRefresh(e.target.checked)
                                }
                            />
                            自動刷新
                        </label>
                        <select
                            value={refreshInterval}
                            onChange={(e) =>
                                setRefreshInterval(Number(e.target.value))
                            }
                            disabled={!autoRefresh}
                        >
                            <option value={1000}>1秒</option>
                            <option value={5000}>5秒</option>
                            <option value={10000}>10秒</option>
                            <option value={30000}>30秒</option>
                        </select>
                    </div>

                    <div className="connection-status">
                        <span
                            className={`status-indicator ${
                                wsConnected ? 'connected' : 'disconnected'
                            }`}
                        >
                            {wsConnected ? '已連線' : '已斷線'}
                        </span>
                    </div>

                    <button
                        className="fullscreen-exit"
                        onClick={() => setIsFullscreen(null)}
                        style={{ display: isFullscreen ? 'block' : 'none' }}
                    >
                        退出全螢幕
                    </button>
                </div>
            </div>

            {/* 儀表板格線 */}
            <div
                className="dashboard-grid"
                style={{
                    gridTemplateColumns: 'repeat(12, 1fr)',
                    gridTemplateRows: 'repeat(8, 1fr)',
                }}
            >
                {Object.entries(currentLayout.components).map(
                    ([componentId, layout]) =>
                        renderComponent(componentId, layout)
                )}
            </div>

            {/* 全螢幕遮罩 */}
            {isFullscreen && (
                <div className="fullscreen-overlay">
                    <div className="fullscreen-content">
                        {Object.entries(currentLayout.components)
                            .filter(
                                ([componentId]) => componentId === isFullscreen
                            )
                            .map(([componentId, layout]) =>
                                renderComponent(componentId, {
                                    ...layout,
                                    x: 0,
                                    y: 0,
                                    w: 12,
                                    h: 8,
                                })
                            )}
                    </div>
                </div>
            )}
        </div>
    )
}

export default Dashboard
