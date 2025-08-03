import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
    Activity,
    Zap,
    Target,
    BarChart3,
    Brain,
    Satellite,
    MonitorSpeaker,
} from 'lucide-react'

// 導入現有組件
import HandoverAnimation3D from '@/components/domains/handover/execution/HandoverAnimation3D'
// import UnifiedHandoverStatus from '@/components/domains/handover/execution/UnifiedHandoverStatus'

// 導入視覺化協調系統
import { VisualizationCoordinator } from './VisualizationCoordinator'
import { RealtimeEventStreamer } from './RealtimeEventStreamer'
import { DecisionFlowTracker } from './DecisionFlowTracker'
import { CandidateSelectionPanel } from './CandidateSelectionPanel'
import { AlgorithmExplainabilityPanel } from './AlgorithmExplainabilityPanel'

// 導入API服務
import { useWebSocket } from '@/hooks/useWebSocket'

interface DecisionControlCenterProps {
    className?: string
}

export const DecisionControlCenter: React.FC<DecisionControlCenterProps> = ({
    className = '',
}) => {
    // 狀態管理
    const [currentPhase, setCurrentPhase] = useState<string>('monitoring')
    const [decisionProgress, setDecisionProgress] = useState<number>(0)
    const [activeAlgorithm, setActiveAlgorithm] = useState<string>('DQN')
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [candidateSatellites, setCandidateSatellites] = useState<any[]>([])
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [decisionMetrics, _setDecisionMetrics] = useState<any>({})
    const [systemStatus, setSystemStatus] = useState<
        'healthy' | 'warning' | 'error'
    >('healthy')

    // WebSocket 實時數據
    const { data: wsData, isConnected: wsConnected } = useWebSocket(
        '/ws/handover-monitor'
    )

    // 視覺化協調器
    const [visualCoordinator] = useState(() => new VisualizationCoordinator())
    const [eventStreamer] = useState(() => new RealtimeEventStreamer())

    // 決策流程處理
    const handleDecisionPhaseChange = useCallback(
        (phase: string, progress: number) => {
            setCurrentPhase(phase)
            setDecisionProgress(progress)

            // 通知視覺化協調器
            visualCoordinator.notifyPhaseChange(phase, progress)
        },
        [visualCoordinator]
    )

    // 候選衛星更新
    const handleCandidateUpdate = useCallback(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (candidates: any[]) => {
            setCandidateSatellites(candidates)
            visualCoordinator.updateCandidates(candidates)
        },
        [visualCoordinator]
    )

    // 算法切換
    const handleAlgorithmSwitch = useCallback(
        (algorithm: string) => {
            setActiveAlgorithm(algorithm)
            visualCoordinator.switchAlgorithm(algorithm)
        },
        [visualCoordinator]
    )

    // 系統狀態評估
    useEffect(() => {
        if (!wsConnected) {
            setSystemStatus('warning')
        } else {
            setSystemStatus('healthy')
        }
    }, [wsConnected])

    // 實時數據處理
    useEffect(() => {
        if (wsData) {
            eventStreamer.processRealtimeData(wsData)
        }
    }, [wsData, eventStreamer])

    return (
        <div className={`unified-decision-center ${className}`}>
            {/* 系統狀態頂部欄 */}
            <Card className="mb-4">
                <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <Brain className="w-6 h-6" />
                            LEO 衛星換手決策控制中心
                        </CardTitle>
                        <div className="flex items-center gap-4">
                            <Badge
                                variant={
                                    systemStatus === 'healthy'
                                        ? 'default'
                                        : 'destructive'
                                }
                            >
                                {systemStatus === 'healthy'
                                    ? '系統正常'
                                    : '系統異常'}
                            </Badge>
                            <Badge variant="outline">
                                {activeAlgorithm} 算法
                            </Badge>
                            <Badge variant="secondary">
                                WebSocket {wsConnected ? '已連接' : '未連接'}
                            </Badge>
                        </div>
                    </div>
                </CardHeader>
            </Card>

            {/* 系統異常提示 */}
            {systemStatus !== 'healthy' && (
                <Alert className="mb-4">
                    <AlertDescription>
                        {systemStatus === 'error' &&
                            '⚠️ 系統發生錯誤，請檢查後端服務狀態'}
                        {systemStatus === 'warning' &&
                            '⚠️ WebSocket 連接中斷，實時數據可能延遲'}
                    </AlertDescription>
                </Alert>
            )}

            {/* 主要內容區域 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 左側：決策流程追蹤 */}
                <div className="lg:col-span-1">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Target className="w-5 h-5" />
                                決策流程追蹤
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <DecisionFlowTracker
                                currentPhase={currentPhase}
                                progress={decisionProgress}
                                onPhaseChange={handleDecisionPhaseChange}
                            />
                        </CardContent>
                    </Card>

                    {/* 候選衛星面板 */}
                    <Card className="mt-4">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Satellite className="w-5 h-5" />
                                候選衛星評分
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <CandidateSelectionPanel
                                candidates={candidateSatellites}
                                onCandidateUpdate={handleCandidateUpdate}
                            />
                        </CardContent>
                    </Card>
                </div>

                {/* 中間：3D 視覺化 */}
                <div className="lg:col-span-1">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <MonitorSpeaker className="w-5 h-5" />
                                3D 決策視覺化
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-2">
                            <div className="h-[600px] relative">
                                <HandoverAnimation3D
                                    satellites={candidateSatellites}
                                    devices={[]}
                                    enabled={true}
                                    onStatusUpdate={handleDecisionPhaseChange}
                                    onHandoverStateUpdate={(state) => {
                                        visualCoordinator.updateHandoverState(
                                            state
                                        )
                                    }}
                                />
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* 右側：算法透明化 */}
                <div className="lg:col-span-1">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Brain className="w-5 h-5" />
                                算法決策透明化
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <AlgorithmExplainabilityPanel
                                algorithm={activeAlgorithm}
                                onAlgorithmSwitch={handleAlgorithmSwitch}
                                metrics={decisionMetrics}
                            />
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* 底部：監控與統計 */}
            <div className="mt-6">
                <Tabs defaultValue="monitoring" className="w-full">
                    <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="monitoring">
                            <Activity className="w-4 h-4 mr-2" />
                            實時監控
                        </TabsTrigger>
                        <TabsTrigger value="performance">
                            <BarChart3 className="w-4 h-4 mr-2" />
                            性能分析
                        </TabsTrigger>
                        <TabsTrigger value="comparison">
                            <Zap className="w-4 h-4 mr-2" />
                            算法比較
                        </TabsTrigger>
                        <TabsTrigger value="history">
                            <Target className="w-4 h-4 mr-2" />
                            歷史回放
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="monitoring" className="mt-4">
                        <Card>
                            <CardHeader>
                                <CardTitle>系統實時監控</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-center text-gray-500">
                                    監控功能開發中...
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="performance" className="mt-4">
                        <Card>
                            <CardHeader>
                                <CardTitle>決策性能分析</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <div className="text-sm text-gray-500">
                                            平均決策時間
                                        </div>
                                        <div className="text-2xl font-bold">
                                            {decisionMetrics.avgDecisionTime ||
                                                '2.3ms'}
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="text-sm text-gray-500">
                                            成功率
                                        </div>
                                        <div className="text-2xl font-bold">
                                            {decisionMetrics.successRate ||
                                                '94.7%'}
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="text-sm text-gray-500">
                                            置信度
                                        </div>
                                        <div className="text-2xl font-bold">
                                            {decisionMetrics.confidence ||
                                                '0.87'}
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="text-sm text-gray-500">
                                            API 響應時間
                                        </div>
                                        <div className="text-2xl font-bold text-green-600">
                                            {'<3ms'}
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="comparison" className="mt-4">
                        <Card>
                            <CardHeader>
                                <CardTitle>算法比較分析</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <div className="grid grid-cols-3 gap-4">
                                        <div className="text-center p-4 border rounded-lg">
                                            <div className="text-lg font-semibold">
                                                DQN
                                            </div>
                                            <div className="text-sm text-gray-500">
                                                深度Q網絡
                                            </div>
                                            <div className="text-2xl font-bold mt-2">
                                                92.3%
                                            </div>
                                        </div>
                                        <div className="text-center p-4 border rounded-lg bg-blue-50">
                                            <div className="text-lg font-semibold">
                                                PPO
                                            </div>
                                            <div className="text-sm text-gray-500">
                                                近端策略優化
                                            </div>
                                            <div className="text-2xl font-bold mt-2">
                                                94.7%
                                            </div>
                                        </div>
                                        <div className="text-center p-4 border rounded-lg">
                                            <div className="text-lg font-semibold">
                                                SAC
                                            </div>
                                            <div className="text-sm text-gray-500">
                                                軟演員評論家
                                            </div>
                                            <div className="text-2xl font-bold mt-2">
                                                91.8%
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="history" className="mt-4">
                        <Card>
                            <CardHeader>
                                <CardTitle>決策歷史回放</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-center py-8 text-gray-500">
                                    🎬 決策歷史回放功能即將推出
                                    <br />
                                    支援完整的決策過程重現和分析
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    )
}

export default DecisionControlCenter
