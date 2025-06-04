/**
 * 數據可視化儀表盤
 * 整合系統狀態、UAV 指標、網路拓撲等圖表
 */
import { useState, useMemo } from 'react'
import SystemStatusChart from './charts/SystemStatusChart'
import UAVMetricsChart from './charts/UAVMetricsChart'
import NetworkTopologyChart from './charts/NetworkTopologyChart'
import useWebSocket from '../../hooks/useWebSocket'
import { WebSocketEvent } from '../../types/charts'

interface DataVisualizationDashboardProps {
    className?: string
}

const DataVisualizationDashboard: React.FC<DataVisualizationDashboardProps> = ({
    className = '',
}) => {
    const [activeTab, setActiveTab] = useState<
        'overview' | 'system' | 'uav' | 'network'
    >('overview')
    const [isRealtime, setIsRealtime] = useState(false) // 預設關閉自動刷新
    const [lastUpdate, setLastUpdate] = useState<string>('')
    const [isWebSocketEnabled, setIsWebSocketEnabled] = useState(false) // 預設關閉 WebSocket

    // WebSocket 連接用於實時數據更新 - 可選
    const { isConnected, reconnectCount, connectionStatus, resetReconnection } =
        useWebSocket({
            url: '/api/ws',
            enableReconnect: isWebSocketEnabled, // 只在啟用時才連接
            maxReconnectAttempts: 2,
            reconnectInterval: 10000, // 增加重連間隔
            onMessage: handleWebSocketMessage,
            onConnect: () => {
                console.log('儀表盤 WebSocket 已連接')
            },
            onDisconnect: () => {
                console.log('儀表盤 WebSocket 已斷開')
            },
        })

    function handleWebSocketMessage(event: WebSocketEvent) {
        console.log('收到實時數據更新:', event)
        setLastUpdate(new Date().toLocaleString())

        // 根據事件類型處理不同的數據更新
        switch (event.type) {
            case 'system_status':
                // 系統狀態更新
                break
            case 'uav_update':
                // UAV 數據更新
                break
            case 'topology_change':
                // 網路拓撲變化
                break
            default:
                break
        }
    }

    const tabs = [
        { id: 'overview', label: '總覽', icon: '📊' },
        { id: 'system', label: '系統狀態', icon: '🔧' },
        { id: 'uav', label: 'UAV 監控', icon: '🚁' },
        { id: 'network', label: '網路拓撲', icon: '🌐' },
    ] as const

    // 導航欄項目
    const navItems = [
        { id: 'dashboard', label: '儀表盤', icon: '📊', active: true },
        { id: 'simulation', label: '仿真控制', icon: '🎮', active: false },
        { id: 'analysis', label: '數據分析', icon: '📈', active: false },
        { id: 'settings', label: '系統設置', icon: '⚙️', active: false },
    ]

    // 避免不必要的重新渲染，增加刷新間隔
    const chartConfigs = useMemo(
        () => ({
            system: { refreshInterval: isRealtime ? 30000 : 0 }, // 30秒
            uav: { refreshInterval: isRealtime ? 15000 : 0 }, // 15秒
            network: { refreshInterval: isRealtime ? 60000 : 0 }, // 60秒
        }),
        [isRealtime]
    )

    const renderTabContent = () => {
        switch (activeTab) {
            case 'overview':
                return (
                    <div className="overview-grid">
                        <div className="chart-container small">
                            <SystemStatusChart
                                refreshInterval={0} // 總覽頁面不自動刷新
                                className="overview-chart"
                            />
                        </div>
                        <div className="chart-container small">
                            <UAVMetricsChart
                                refreshInterval={0} // 總覽頁面不自動刷新
                                className="overview-chart"
                            />
                        </div>
                        <div className="chart-container large">
                            <NetworkTopologyChart
                                width={600}
                                height={400}
                                refreshInterval={0} // 總覽頁面不自動刷新
                                className="overview-chart"
                            />
                        </div>
                    </div>
                )
            case 'system':
                return (
                    <div className="single-chart">
                        <SystemStatusChart
                            refreshInterval={
                                chartConfigs.system.refreshInterval
                            }
                            className="full-chart"
                        />
                    </div>
                )
            case 'uav':
                return (
                    <div className="single-chart">
                        <UAVMetricsChart
                            refreshInterval={chartConfigs.uav.refreshInterval}
                            className="full-chart"
                        />
                    </div>
                )
            case 'network':
                return (
                    <div className="single-chart">
                        <NetworkTopologyChart
                            width={1000}
                            height={700}
                            refreshInterval={
                                chartConfigs.network.refreshInterval
                            }
                            className="full-chart"
                        />
                    </div>
                )
            default:
                return null
        }
    }

    return (
        <>
            {/* 導航欄移至最頂部 */}
            <nav className="dashboard-navbar">
                <div className="navbar-brand">
                    <h1>NTN Stack</h1>
                    <span className="version">v1.0.0</span>
                </div>

                <div className="navbar-nav">
                    {navItems.map((item) => (
                        <button
                            key={item.id}
                            className={`nav-item ${
                                item.active ? 'active' : 'disabled'
                            }`}
                            disabled={!item.active}
                            title={item.active ? undefined : '功能開發中'}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            <span className="nav-label">{item.label}</span>
                        </button>
                    ))}
                </div>

                <div className="navbar-actions">
                    <div className="connection-indicator">
                        <span
                            className={`status-dot ${
                                isWebSocketEnabled
                                    ? isConnected
                                        ? 'connected'
                                        : connectionStatus === 'failed'
                                        ? 'failed'
                                        : 'connecting'
                                    : 'disabled'
                            }`}
                            title={
                                !isWebSocketEnabled
                                    ? 'WebSocket 已停用'
                                    : isConnected
                                    ? '實時連接正常'
                                    : connectionStatus === 'failed'
                                    ? `連接失敗 (重試 ${reconnectCount} 次)`
                                    : '正在連接...'
                            }
                        >
                            ●
                        </span>
                        <span className="connection-text">
                            {isWebSocketEnabled
                                ? isConnected
                                    ? '已連接'
                                    : '離線'
                                : '靜態模式'}
                        </span>
                    </div>
                </div>
            </nav>

            {/* 儀表盤主體 */}
            <div className={`data-visualization-dashboard ${className}`}>
                <div className="dashboard-main">
                    {/* 儀表盤標題欄 */}
                    <div className="dashboard-header">
                        <div className="header-left">
                            <h2>數據可視化儀表盤</h2>
                            <div className="breadcrumb">
                                <span>儀表盤</span>
                                <span className="separator">/</span>
                                <span>
                                    {
                                        tabs.find((t) => t.id === activeTab)
                                            ?.label
                                    }
                                </span>
                            </div>
                        </div>

                        <div className="header-controls">
                            <div className="control-group">
                                <label className="toggle-control">
                                    <input
                                        type="checkbox"
                                        checked={isRealtime}
                                        onChange={(e) =>
                                            setIsRealtime(e.target.checked)
                                        }
                                    />
                                    <span className="toggle-slider"></span>
                                    <span className="toggle-label">
                                        自動刷新
                                    </span>
                                </label>
                            </div>

                            <div className="control-group">
                                <label className="toggle-control">
                                    <input
                                        type="checkbox"
                                        checked={isWebSocketEnabled}
                                        onChange={(e) =>
                                            setIsWebSocketEnabled(
                                                e.target.checked
                                            )
                                        }
                                    />
                                    <span className="toggle-slider"></span>
                                    <span className="toggle-label">
                                        實時連接
                                    </span>
                                </label>
                            </div>

                            {connectionStatus === 'failed' && (
                                <button
                                    className="retry-button"
                                    onClick={resetReconnection}
                                    title="重新嘗試連接"
                                >
                                    🔄 重試
                                </button>
                            )}

                            {lastUpdate && (
                                <div className="last-update">
                                    最後更新: {lastUpdate}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* 標籤導航 */}
                    <div className="dashboard-tabs">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                className={`tab-button ${
                                    activeTab === tab.id ? 'active' : ''
                                }`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <span className="tab-icon">{tab.icon}</span>
                                <span className="tab-label">{tab.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* 圖表內容區域 */}
                    <div className="dashboard-content">
                        {renderTabContent()}
                    </div>
                </div>
            </div>
        </>
    )
}

export default DataVisualizationDashboard
