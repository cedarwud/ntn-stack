/**
 * 統一監控中心 - Phase 2
 * 整合 SimWorld 和 NetStack 的所有監控功能
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs'
import { Badge } from '../ui/badge'
import { Alert, AlertDescription } from '../ui/alert'
import {
    Activity,
    BarChart3,
    Zap,
    Target,
    Settings,
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    XCircle,
} from 'lucide-react'

// 導入現有監控組件
import { RLMonitoringPanel } from '../rl-monitoring'
import { SystemHealthViewer, AlertsViewer } from '../monitoring'

// 導入服務和Hook
import { useRLMonitoring } from '../rl-monitoring/hooks/useRLMonitoring'
import { useWebSocket } from '../../hooks/useWebSocket'
import { useCrossSystemMonitoring } from './hooks/useCrossSystemMonitoring'

// 類型定義
interface UnifiedMonitoringCenterProps {
    className?: string
    mode?: 'standalone' | 'embedded'
    height?: string
    onSystemAlert?: (alert: SystemAlert) => void
    onPerformanceChange?: (metrics: PerformanceMetrics) => void
}

interface SystemAlert {
    id: string
    level: 'info' | 'warning' | 'error' | 'critical'
    message: string
    source: 'simworld' | 'netstack' | 'integration'
    timestamp: Date
}

interface PerformanceMetrics {
    overall_health: number
    simworld_status: 'healthy' | 'warning' | 'error'
    netstack_status: 'healthy' | 'warning' | 'error'
    integration_status: 'healthy' | 'warning' | 'error'
    active_algorithms: string[]
    training_progress: number
    api_response_time: number
}

export const UnifiedMonitoringCenter: React.FC<
    UnifiedMonitoringCenterProps
> = ({
    className = '',
    mode = 'standalone',
    height = '100vh',
    onSystemAlert,
    onPerformanceChange,
}) => {
    // 狀態管理
    const [activeTab, setActiveTab] = useState('overview')
    const [systemAlerts, setSystemAlerts] = useState<SystemAlert[]>([])
    const [isCollapsed, setIsCollapsed] = useState(false)

    // 監控數據 Hook
    const {
        data: rlData,
        isLoading: rlLoading,
        error: rlError,
    } = useRLMonitoring({
        refreshInterval: 2000,
        enabled: true,
    })

    // 跨系統監控
    const {
        performanceMetrics,
        systemStatus,
        integrationHealth,
        crossSystemAlerts,
        refreshAll,
    } = useCrossSystemMonitoring()

    // WebSocket 實時連接
    const {
        data: wsData,
        isConnected: wsConnected,
        error: wsError,
    } = useWebSocket('/ws/unified-monitoring')

    // 系統健康狀態計算
    const overallHealth = useMemo(() => {
        const weights = {
            simworld: 0.3,
            netstack: 0.4,
            integration: 0.3,
        }

        const scores = {
            simworld:
                systemStatus.simworld === 'healthy'
                    ? 100
                    : systemStatus.simworld === 'warning'
                    ? 70
                    : 30,
            netstack:
                systemStatus.netstack === 'healthy'
                    ? 100
                    : systemStatus.netstack === 'warning'
                    ? 70
                    : 30,
            integration:
                integrationHealth.status === 'healthy'
                    ? 100
                    : integrationHealth.status === 'warning'
                    ? 70
                    : 30,
        }

        return Math.round(
            weights.simworld * scores.simworld +
                weights.netstack * scores.netstack +
                weights.integration * scores.integration
        )
    }, [systemStatus, integrationHealth])

    // 告警處理
    const handleNewAlert = useCallback(
        (alert: SystemAlert) => {
            setSystemAlerts((prev) => [alert, ...prev.slice(0, 9)]) // 保留最新 10 條
            if (onSystemAlert) {
                onSystemAlert(alert)
            }
        },
        [onSystemAlert]
    )

    // 監聽跨系統告警
    useEffect(() => {
        crossSystemAlerts.forEach((alert) => {
            handleNewAlert({
                id: `cross_${Date.now()}`,
                level: alert.level,
                message: alert.message,
                source: 'integration',
                timestamp: new Date(),
            })
        })
    }, [crossSystemAlerts, handleNewAlert])

    // 監聽 RL 錯誤
    useEffect(() => {
        if (rlError) {
            handleNewAlert({
                id: `rl_${Date.now()}`,
                level: 'error',
                message: `RL 系統錯誤: ${rlError.message}`,
                source: 'netstack',
                timestamp: new Date(),
            })
        }
    }, [rlError, handleNewAlert])

    // 監聽 WebSocket 錯誤
    useEffect(() => {
        if (wsError) {
            handleNewAlert({
                id: `ws_${Date.now()}`,
                level: 'warning',
                message: `WebSocket 連接問題: ${wsError.message}`,
                source: 'integration',
                timestamp: new Date(),
            })
        }
    }, [wsError, handleNewAlert])

    // 性能指標變化通知
    useEffect(() => {
        if (performanceMetrics && onPerformanceChange) {
            onPerformanceChange(performanceMetrics)
        }
    }, [performanceMetrics, onPerformanceChange])

    // 獲取狀態圖標
    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'healthy':
                return <CheckCircle className="w-4 h-4 text-green-500" />
            case 'warning':
                return <AlertTriangle className="w-4 h-4 text-yellow-500" />
            case 'error':
                return <XCircle className="w-4 h-4 text-red-500" />
            default:
                return <Activity className="w-4 h-4 text-gray-500" />
        }
    }

    // 標籤頁配置
    const tabs = useMemo(
        () => [
            {
                id: 'overview',
                label: '🎯 總覽',
                icon: <BarChart3 className="w-4 h-4" />,
                description: '系統整體狀況',
            },
            {
                id: 'rl-monitoring',
                label: '🧠 RL 監控',
                icon: <Zap className="w-4 h-4" />,
                description: 'NetStack RL 系統',
            },
            {
                id: 'system-health',
                label: '💚 系統健康',
                icon: <Activity className="w-4 h-4" />,
                description: 'SimWorld 系統狀態',
            },
            {
                id: 'integration',
                label: '🔗 整合狀態',
                icon: <Target className="w-4 h-4" />,
                description: 'API 橋接狀況',
            },
            {
                id: 'alerts',
                label: '🚨 告警中心',
                icon: <AlertTriangle className="w-4 h-4" />,
                description: '系統告警管理',
            },
        ],
        []
    )

    return (
        <div
            className={`unified-monitoring-center ${className}`}
            style={{ height: mode === 'standalone' ? height : 'auto' }}
        >
            {/* 頭部狀態欄 */}
            <div className="monitoring-header">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <h2 className="text-xl font-semibold">
                            🎛️ 統一監控中心 (Phase 2)
                        </h2>
                        <Badge
                            variant={
                                overallHealth >= 80 ? 'default' : 'destructive'
                            }
                        >
                            系統健康度: {overallHealth}%
                        </Badge>
                    </div>

                    <div className="flex items-center space-x-2">
                        {/* 快速狀態指示器 */}
                        <div className="flex items-center space-x-1">
                            <span className="text-sm">SimWorld:</span>
                            {getStatusIcon(systemStatus.simworld)}
                        </div>

                        <div className="flex items-center space-x-1">
                            <span className="text-sm">NetStack:</span>
                            {getStatusIcon(systemStatus.netstack)}
                        </div>

                        <div className="flex items-center space-x-1">
                            <span className="text-sm">整合:</span>
                            {getStatusIcon(integrationHealth.status)}
                        </div>

                        <div className="flex items-center space-x-1">
                            <span className="text-sm">WebSocket:</span>
                            {wsConnected ? (
                                <CheckCircle className="w-4 h-4 text-green-500" />
                            ) : (
                                <XCircle className="w-4 h-4 text-red-500" />
                            )}
                        </div>

                        <button
                            onClick={refreshAll}
                            className="p-2 rounded hover:bg-gray-100"
                            title="刷新所有數據"
                        >
                            <TrendingUp className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* 活動統計 */}
                <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                    <span>
                        活躍算法:{' '}
                        {performanceMetrics?.active_algorithms?.length || 0}
                    </span>
                    <span>
                        API 延遲: {performanceMetrics?.api_response_time || 0}ms
                    </span>
                    <span>告警數量: {systemAlerts.length}</span>
                    <span>最後更新: {new Date().toLocaleTimeString()}</span>
                </div>
            </div>

            {/* 主要內容區域 */}
            <div className="monitoring-content">
                <Tabs
                    value={activeTab}
                    onValueChange={setActiveTab}
                    className="w-full"
                >
                    <TabsList className="grid w-full grid-cols-5">
                        {tabs.map((tab) => (
                            <TabsTrigger
                                key={tab.id}
                                value={tab.id}
                                className="flex items-center"
                            >
                                {tab.icon}
                                <span className="ml-1 hidden sm:inline">
                                    {tab.label}
                                </span>
                            </TabsTrigger>
                        ))}
                    </TabsList>

                    {/* 總覽頁面 */}
                    <TabsContent value="overview" className="mt-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {/* 系統狀態卡片 */}
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-sm">
                                        系統狀態
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2">
                                        <div className="flex justify-between items-center">
                                            <span>SimWorld</span>
                                            <div className="flex items-center">
                                                {getStatusIcon(
                                                    systemStatus.simworld
                                                )}
                                                <span className="ml-1 capitalize">
                                                    {systemStatus.simworld}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>NetStack RL</span>
                                            <div className="flex items-center">
                                                {getStatusIcon(
                                                    systemStatus.netstack
                                                )}
                                                <span className="ml-1 capitalize">
                                                    {systemStatus.netstack}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>API 整合</span>
                                            <div className="flex items-center">
                                                {getStatusIcon(
                                                    integrationHealth.status
                                                )}
                                                <span className="ml-1 capitalize">
                                                    {integrationHealth.status}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* 性能指標卡片 */}
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-sm">
                                        性能指標
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span>整體健康度</span>
                                            <span className="font-medium">
                                                {overallHealth}%
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>訓練進度</span>
                                            <span className="font-medium">
                                                {performanceMetrics?.training_progress ||
                                                    0}
                                                %
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>活躍算法</span>
                                            <span className="font-medium">
                                                {performanceMetrics
                                                    ?.active_algorithms
                                                    ?.length || 0}
                                            </span>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* 最新告警 */}
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-sm">
                                        最新告警
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-1">
                                        {systemAlerts
                                            .slice(0, 3)
                                            .map((alert) => (
                                                <div
                                                    key={alert.id}
                                                    className="flex items-start space-x-2 text-sm"
                                                >
                                                    <Badge
                                                        variant={
                                                            alert.level ===
                                                            'error'
                                                                ? 'destructive'
                                                                : 'secondary'
                                                        }
                                                        className="text-xs"
                                                    >
                                                        {alert.level}
                                                    </Badge>
                                                    <span className="flex-1 truncate">
                                                        {alert.message}
                                                    </span>
                                                </div>
                                            ))}
                                        {systemAlerts.length === 0 && (
                                            <div className="text-sm text-gray-500">
                                                無告警信息
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>

                    {/* RL 監控頁面 */}
                    <TabsContent value="rl-monitoring" className="mt-4">
                        <Card>
                            <CardContent className="p-0">
                                <RLMonitoringPanel
                                    mode="embedded"
                                    height="600px"
                                    refreshInterval={2000}
                                    onError={(error) => {
                                        handleNewAlert({
                                            id: `rl_panel_${Date.now()}`,
                                            level: 'error',
                                            message: `RL 監控面板錯誤: ${error.message}`,
                                            source: 'netstack',
                                            timestamp: new Date(),
                                        })
                                    }}
                                />
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* 系統健康頁面 */}
                    <TabsContent value="system-health" className="mt-4">
                        <Card>
                            <CardContent className="p-0">
                                <SystemHealthViewer
                                    className="embedded"
                                    autoRefresh={true}
                                    refreshInterval={3000}
                                    showCharts={true}
                                />
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* 整合狀態頁面 */}
                    <TabsContent value="integration" className="mt-4">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <Card>
                                <CardHeader>
                                    <CardTitle>API 橋接狀態</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3">
                                        <div className="flex justify-between items-center">
                                            <span>NetStack RL 客戶端</span>
                                            <Badge
                                                variant={
                                                    integrationHealth.netstackClient
                                                        ? 'default'
                                                        : 'destructive'
                                                }
                                            >
                                                {integrationHealth.netstackClient
                                                    ? '已連接'
                                                    : '未連接'}
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>AI-RAN 服務整合</span>
                                            <Badge
                                                variant={
                                                    integrationHealth.aiRanIntegration
                                                        ? 'default'
                                                        : 'destructive'
                                                }
                                            >
                                                {integrationHealth.aiRanIntegration
                                                    ? '已整合'
                                                    : '未整合'}
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>會話管理</span>
                                            <Badge
                                                variant={
                                                    integrationHealth.sessionManagement
                                                        ? 'default'
                                                        : 'destructive'
                                                }
                                            >
                                                {integrationHealth.sessionManagement
                                                    ? '正常'
                                                    : '異常'}
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>自動降級機制</span>
                                            <Badge
                                                variant={
                                                    integrationHealth.fallbackMechanism
                                                        ? 'default'
                                                        : 'destructive'
                                                }
                                            >
                                                {integrationHealth.fallbackMechanism
                                                    ? '已啟用'
                                                    : '未啟用'}
                                            </Badge>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>整合統計</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3">
                                        <div className="flex justify-between">
                                            <span>API 調用次數</span>
                                            <span className="font-medium">
                                                {integrationHealth.apiCalls ||
                                                    0}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>成功率</span>
                                            <span className="font-medium">
                                                {integrationHealth.successRate ||
                                                    0}
                                                %
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>平均響應時間</span>
                                            <span className="font-medium">
                                                {integrationHealth.avgResponseTime ||
                                                    0}
                                                ms
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>降級次數</span>
                                            <span className="font-medium">
                                                {integrationHealth.fallbackCount ||
                                                    0}
                                            </span>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>

                    {/* 告警中心頁面 */}
                    <TabsContent value="alerts" className="mt-4">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <Card>
                                <CardHeader>
                                    <CardTitle>系統告警</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2 max-h-96 overflow-y-auto">
                                        {systemAlerts.map((alert) => (
                                            <Alert
                                                key={alert.id}
                                                variant={
                                                    alert.level === 'error'
                                                        ? 'destructive'
                                                        : 'default'
                                                }
                                            >
                                                <AlertTriangle className="h-4 w-4" />
                                                <AlertDescription>
                                                    <div className="flex justify-between items-start">
                                                        <div>
                                                            <div className="font-medium">
                                                                {alert.message}
                                                            </div>
                                                            <div className="text-xs text-gray-500">
                                                                來源:{' '}
                                                                {alert.source} |{' '}
                                                                {alert.timestamp.toLocaleString()}
                                                            </div>
                                                        </div>
                                                        <Badge
                                                            variant="outline"
                                                            className="text-xs"
                                                        >
                                                            {alert.level}
                                                        </Badge>
                                                    </div>
                                                </AlertDescription>
                                            </Alert>
                                        ))}
                                        {systemAlerts.length === 0 && (
                                            <div className="text-center text-gray-500 py-8">
                                                暫無告警信息
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>詳細告警記錄</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <AlertsViewer
                                        className="embedded"
                                        autoRefresh={true}
                                        refreshInterval={5000}
                                    />
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    )
}

export default UnifiedMonitoringCenter
