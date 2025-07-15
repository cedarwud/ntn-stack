/**
 * Phase 2 統一監控系統演示頁面
 * 展示所有 Phase 2 開發的監控功能
 */

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
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
    RefreshCw,
    Download,
    Play,
    Pause,
    Stop,
} from 'lucide-react'

// 導入 Phase 2 組件
import { UnifiedMonitoringCenter } from '../components/unified-monitoring'
import { useCrossSystemMonitoring } from '../components/unified-monitoring/hooks/useCrossSystemMonitoring'
import { enhancedRLMonitoringService } from '../services/enhanced-rl-monitoring'

// 類型定義
interface DemoStats {
    totalComponents: number
    activeMonitors: number
    systemHealth: number
    lastUpdated: string
}

interface Phase2Achievement {
    title: string
    description: string
    status: 'completed' | 'in-progress' | 'planned'
    features: string[]
}

export const Phase2MonitoringDemo: React.FC = () => {
    // 狀態管理
    const [activeDemo, setActiveDemo] = useState('overview')
    const [demoStats, setDemoStats] = useState<DemoStats>({
        totalComponents: 5,
        activeMonitors: 3,
        systemHealth: 85,
        lastUpdated: new Date().toISOString(),
    })
    const [isTestRunning, setIsTestRunning] = useState(false)
    const [testResults, setTestResults] = useState<any>(null)

    // 使用 Phase 2 Hook
    const {
        performanceMetrics,
        systemStatus,
        integrationHealth,
        crossSystemAlerts,
        isLoading,
        error,
        refreshAll,
    } = useCrossSystemMonitoring()

    // Phase 2 成就列表
    const phase2Achievements: Phase2Achievement[] = [
        {
            title: '統一監控中心',
            description: '整合 SimWorld 和 NetStack 的統一監控介面',
            status: 'completed',
            features: [
                '多系統狀態聚合',
                '實時健康度監控',
                '跨系統告警管理',
                '響應式儀表板設計',
            ],
        },
        {
            title: '跨系統監控聚合器',
            description: '智能的跨系統數據聚合和狀態分析',
            status: 'completed',
            features: [
                '並行系統檢查',
                '智能降級檢測',
                'API 橋接監控',
                '性能指標聚合',
            ],
        },
        {
            title: '增強版 RL 監控服務',
            description: '完整的 RL 系統監控和控制服務',
            status: 'completed',
            features: [
                'WebSocket 實時推送',
                '算法控制介面',
                '會話管理',
                '決策透明化',
            ],
        },
        {
            title: 'API 橋接整合監控',
            description: 'Phase 1 API 橋接的完整監控支援',
            status: 'completed',
            features: [
                'NetStack 客戶端狀態',
                '整合健康檢查',
                '會話同步監控',
                '降級機制監控',
            ],
        },
        {
            title: '測試與驗證框架',
            description: '全面的系統整合測試和驗證',
            status: 'completed',
            features: [
                '自動化整合測試',
                '性能基準測試',
                '穩定性驗證',
                '錯誤場景測試',
            ],
        },
    ]

    // 組件掛載時的初始化
    useEffect(() => {
        // 連接增強版 RL 監控服務
        enhancedRLMonitoringService.connectWebSocket()

        // 設置事件監聽
        enhancedRLMonitoringService.on('statusUpdate', (data) => {
            console.log('RL 監控狀態更新:', data)
        })

        enhancedRLMonitoringService.on('error', (error) => {
            console.error('RL 監控錯誤:', error)
        })

        // 清理函數
        return () => {
            enhancedRLMonitoringService.disconnect()
        }
    }, [])

    // 更新演示統計
    useEffect(() => {
        if (performanceMetrics) {
            setDemoStats((prev) => ({
                ...prev,
                systemHealth: performanceMetrics.overall_health,
                lastUpdated: new Date().toISOString(),
            }))
        }
    }, [performanceMetrics])

    // 運行整合測試
    const runIntegrationTest = async () => {
        setIsTestRunning(true)
        try {
            // 模擬測試運行
            await new Promise((resolve) => setTimeout(resolve, 3000))

            // 模擬測試結果
            const mockResults = {
                total_tests: 25,
                passed_tests: 23,
                failed_tests: 2,
                success_rate: 92,
                duration_seconds: 45.2,
                test_categories: {
                    基礎連接: { passed: 5, total: 5 },
                    'API 橋接': { passed: 4, total: 5 },
                    監控聚合: { passed: 5, total: 5 },
                    WebSocket: { passed: 4, total: 5 },
                    性能測試: { passed: 5, total: 5 },
                },
            }

            setTestResults(mockResults)
        } catch (error) {
            console.error('測試運行失敗:', error)
        } finally {
            setIsTestRunning(false)
        }
    }

    // 導出監控報告
    const exportReport = async () => {
        try {
            const data = {
                timestamp: new Date().toISOString(),
                phase: 'Phase 2 - 統一監控系統',
                system_status: systemStatus,
                performance_metrics: performanceMetrics,
                integration_health: integrationHealth,
                cross_system_alerts: crossSystemAlerts,
                demo_stats: demoStats,
            }

            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json',
            })

            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `phase2_monitoring_report_${Date.now()}.json`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
        } catch (error) {
            console.error('導出報告失敗:', error)
        }
    }

    // 獲取狀態圖標
    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'healthy':
            case 'completed':
                return <CheckCircle className="w-4 h-4 text-green-500" />
            case 'warning':
            case 'in-progress':
                return <AlertTriangle className="w-4 h-4 text-yellow-500" />
            case 'error':
                return <XCircle className="w-4 h-4 text-red-500" />
            default:
                return <Activity className="w-4 h-4 text-gray-500" />
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
            <div className="max-w-7xl mx-auto">
                {/* 頁面標題 */}
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 mb-2">
                                🎛️ Phase 2 統一監控系統演示
                            </h1>
                            <p className="text-gray-600">
                                展示 SimWorld 與 NetStack RL
                                系統的完整監控整合方案
                            </p>
                        </div>

                        <div className="flex items-center space-x-3">
                            <Badge variant="default" className="text-sm">
                                Phase 2 完成
                            </Badge>
                            <Button
                                onClick={refreshAll}
                                disabled={isLoading}
                                variant="outline"
                                size="sm"
                            >
                                {isLoading ? (
                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                ) : (
                                    <RefreshCw className="w-4 h-4" />
                                )}
                                刷新
                            </Button>
                            <Button
                                onClick={exportReport}
                                variant="outline"
                                size="sm"
                            >
                                <Download className="w-4 h-4 mr-1" />
                                導出報告
                            </Button>
                        </div>
                    </div>

                    {/* 快速統計 */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-gray-600">
                                            組件總數
                                        </p>
                                        <p className="text-2xl font-bold">
                                            {demoStats.totalComponents}
                                        </p>
                                    </div>
                                    <BarChart3 className="w-8 h-8 text-blue-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-gray-600">
                                            活躍監控
                                        </p>
                                        <p className="text-2xl font-bold">
                                            {demoStats.activeMonitors}
                                        </p>
                                    </div>
                                    <Activity className="w-8 h-8 text-green-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-gray-600">
                                            系統健康度
                                        </p>
                                        <p className="text-2xl font-bold">
                                            {demoStats.systemHealth}%
                                        </p>
                                    </div>
                                    <TrendingUp className="w-8 h-8 text-indigo-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-gray-600">
                                            告警數量
                                        </p>
                                        <p className="text-2xl font-bold">
                                            {crossSystemAlerts?.length || 0}
                                        </p>
                                    </div>
                                    <AlertTriangle className="w-8 h-8 text-orange-500" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>

                {/* 主要內容標籤 */}
                <Tabs
                    value={activeDemo}
                    onValueChange={setActiveDemo}
                    className="w-full"
                >
                    <TabsList className="grid w-full grid-cols-5">
                        <TabsTrigger value="overview">📋 總覽</TabsTrigger>
                        <TabsTrigger value="monitoring">
                            🎛️ 統一監控
                        </TabsTrigger>
                        <TabsTrigger value="achievements">🏆 成就</TabsTrigger>
                        <TabsTrigger value="testing">🧪 測試</TabsTrigger>
                        <TabsTrigger value="integration">
                            🔗 整合狀態
                        </TabsTrigger>
                    </TabsList>

                    {/* 總覽頁面 */}
                    <TabsContent value="overview" className="mt-6">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center">
                                        <Target className="w-5 h-5 mr-2" />
                                        Phase 2 目標達成
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <span>統一監控系統整合</span>
                                            <Badge variant="default">
                                                ✅ 完成
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>跨系統監控聚合</span>
                                            <Badge variant="default">
                                                ✅ 完成
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>增強版 RL 監控</span>
                                            <Badge variant="default">
                                                ✅ 完成
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>測試與驗證框架</span>
                                            <Badge variant="default">
                                                ✅ 完成
                                            </Badge>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center">
                                        <Activity className="w-5 h-5 mr-2" />
                                        系統狀態概覽
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3">
                                        <div className="flex justify-between items-center">
                                            <span>SimWorld 系統</span>
                                            <div className="flex items-center">
                                                {getStatusIcon(
                                                    systemStatus?.simworld
                                                )}
                                                <span className="ml-1 capitalize">
                                                    {systemStatus?.simworld ||
                                                        'unknown'}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>NetStack RL 系統</span>
                                            <div className="flex items-center">
                                                {getStatusIcon(
                                                    systemStatus?.netstack
                                                )}
                                                <span className="ml-1 capitalize">
                                                    {systemStatus?.netstack ||
                                                        'unknown'}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>API 橋接整合</span>
                                            <div className="flex items-center">
                                                {getStatusIcon(
                                                    integrationHealth?.status
                                                )}
                                                <span className="ml-1 capitalize">
                                                    {integrationHealth?.status ||
                                                        'unknown'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Phase 2 架構圖 */}
                        <Card className="mt-6">
                            <CardHeader>
                                <CardTitle>Phase 2 架構概覽</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-center p-8 bg-gray-50 rounded-lg">
                                    <div className="max-w-4xl mx-auto">
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                            <div className="bg-blue-100 p-4 rounded-lg">
                                                <h3 className="font-semibold text-blue-800 mb-2">
                                                    SimWorld 系統
                                                </h3>
                                                <p className="text-sm text-blue-600">
                                                    干擾服務 + UI 前端
                                                </p>
                                            </div>
                                            <div className="bg-green-100 p-4 rounded-lg">
                                                <h3 className="font-semibold text-green-800 mb-2">
                                                    統一監控中心
                                                </h3>
                                                <p className="text-sm text-green-600">
                                                    Phase 2 核心組件
                                                </p>
                                            </div>
                                            <div className="bg-purple-100 p-4 rounded-lg">
                                                <h3 className="font-semibold text-purple-800 mb-2">
                                                    NetStack RL
                                                </h3>
                                                <p className="text-sm text-purple-600">
                                                    訓練引擎 + API
                                                </p>
                                            </div>
                                        </div>
                                        <div className="mt-4 text-sm text-gray-600">
                                            ← API 橋接整合 (Phase 1) →
                                            統一監控聚合 (Phase 2) →
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* 統一監控頁面 */}
                    <TabsContent value="monitoring" className="mt-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>統一監控中心 - 實時演示</CardTitle>
                                <p className="text-sm text-gray-600">
                                    這是 Phase 2
                                    開發的核心組件，整合了所有監控功能
                                </p>
                            </CardHeader>
                            <CardContent className="p-0">
                                <div style={{ height: '700px' }}>
                                    <UnifiedMonitoringCenter
                                        mode="embedded"
                                        height="100%"
                                        onSystemAlert={(alert) => {
                                            console.log('系統告警:', alert)
                                        }}
                                        onPerformanceChange={(metrics) => {
                                            console.log('性能變化:', metrics)
                                        }}
                                    />
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* 成就頁面 */}
                    <TabsContent value="achievements" className="mt-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {phase2Achievements.map((achievement, index) => (
                                <Card key={index}>
                                    <CardHeader>
                                        <CardTitle className="flex items-center justify-between">
                                            <span>{achievement.title}</span>
                                            {getStatusIcon(achievement.status)}
                                        </CardTitle>
                                        <p className="text-sm text-gray-600">
                                            {achievement.description}
                                        </p>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-2">
                                            {achievement.features.map(
                                                (feature, idx) => (
                                                    <div
                                                        key={idx}
                                                        className="flex items-center"
                                                    >
                                                        <CheckCircle className="w-3 h-3 text-green-500 mr-2" />
                                                        <span className="text-sm">
                                                            {feature}
                                                        </span>
                                                    </div>
                                                )
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </TabsContent>

                    {/* 測試頁面 */}
                    <TabsContent value="testing" className="mt-6">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center justify-between">
                                    <span>整合測試與驗證</span>
                                    <Button
                                        onClick={runIntegrationTest}
                                        disabled={isTestRunning}
                                        variant="default"
                                    >
                                        {isTestRunning ? (
                                            <>
                                                <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                                                執行中...
                                            </>
                                        ) : (
                                            <>
                                                <Play className="w-4 h-4 mr-1" />
                                                運行測試
                                            </>
                                        )}
                                    </Button>
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                {testResults ? (
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                            <div className="bg-blue-50 p-3 rounded">
                                                <p className="text-sm text-blue-600">
                                                    總測試數
                                                </p>
                                                <p className="text-xl font-bold text-blue-800">
                                                    {testResults.total_tests}
                                                </p>
                                            </div>
                                            <div className="bg-green-50 p-3 rounded">
                                                <p className="text-sm text-green-600">
                                                    通過測試
                                                </p>
                                                <p className="text-xl font-bold text-green-800">
                                                    {testResults.passed_tests}
                                                </p>
                                            </div>
                                            <div className="bg-red-50 p-3 rounded">
                                                <p className="text-sm text-red-600">
                                                    失敗測試
                                                </p>
                                                <p className="text-xl font-bold text-red-800">
                                                    {testResults.failed_tests}
                                                </p>
                                            </div>
                                            <div className="bg-purple-50 p-3 rounded">
                                                <p className="text-sm text-purple-600">
                                                    成功率
                                                </p>
                                                <p className="text-xl font-bold text-purple-800">
                                                    {testResults.success_rate}%
                                                </p>
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            {Object.entries(
                                                testResults.test_categories
                                            ).map(
                                                ([category, results]: [
                                                    string,
                                                    any
                                                ]) => (
                                                    <div
                                                        key={category}
                                                        className="flex justify-between items-center p-2 bg-gray-50 rounded"
                                                    >
                                                        <span>{category}</span>
                                                        <Badge
                                                            variant={
                                                                results.passed ===
                                                                results.total
                                                                    ? 'default'
                                                                    : 'destructive'
                                                            }
                                                        >
                                                            {results.passed}/
                                                            {results.total}
                                                        </Badge>
                                                    </div>
                                                )
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-gray-500">
                                        點擊「運行測試」按鈕開始整合測試
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* 整合狀態頁面 */}
                    <TabsContent value="integration" className="mt-6">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                                                    integrationHealth?.netstackClient
                                                        ? 'default'
                                                        : 'destructive'
                                                }
                                            >
                                                {integrationHealth?.netstackClient
                                                    ? '已連接'
                                                    : '未連接'}
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>AI-RAN 服務整合</span>
                                            <Badge
                                                variant={
                                                    integrationHealth?.aiRanIntegration
                                                        ? 'default'
                                                        : 'destructive'
                                                }
                                            >
                                                {integrationHealth?.aiRanIntegration
                                                    ? '已整合'
                                                    : '未整合'}
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>會話管理</span>
                                            <Badge
                                                variant={
                                                    integrationHealth?.sessionManagement
                                                        ? 'default'
                                                        : 'destructive'
                                                }
                                            >
                                                {integrationHealth?.sessionManagement
                                                    ? '正常'
                                                    : '異常'}
                                            </Badge>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span>降級機制</span>
                                            <Badge
                                                variant={
                                                    integrationHealth?.fallbackMechanism
                                                        ? 'default'
                                                        : 'destructive'
                                                }
                                            >
                                                {integrationHealth?.fallbackMechanism
                                                    ? '已啟用'
                                                    : '未啟用'}
                                            </Badge>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>性能指標</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3">
                                        <div className="flex justify-between">
                                            <span>整體健康度</span>
                                            <span className="font-medium">
                                                {performanceMetrics?.overall_health ||
                                                    0}
                                                %
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>API 響應時間</span>
                                            <span className="font-medium">
                                                {performanceMetrics?.api_response_time ||
                                                    0}
                                                ms
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
                                        <div className="flex justify-between">
                                            <span>訓練進度</span>
                                            <span className="font-medium">
                                                {performanceMetrics?.training_progress ||
                                                    0}
                                                %
                                            </span>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    )
}

export default Phase2MonitoringDemo
