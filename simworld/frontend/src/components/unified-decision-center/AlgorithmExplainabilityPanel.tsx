import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
    Brain,
    TrendingUp,
    Target,
    BarChart3,
    Zap,
    Eye,
    Activity,
    // ArrowRight,
    // AlertCircle,
    CheckCircle,
} from 'lucide-react'

interface AlgorithmMetrics {
    confidence: number
    actionValue: number
    policyGradient: number
    explorationRate: number
    learningRate: number
    rewardPrediction: number
}

interface DecisionReasoning {
    factor: string
    weight: number
    value: number
    impact: number
    description: string
}

interface AlgorithmExplainabilityPanelProps {
    algorithm: string
    onAlgorithmSwitch: (algorithm: string) => void
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    metrics: any
}

const ALGORITHMS = [
    {
        id: 'DQN',
        name: 'Deep Q-Network',
        description: '基於價值函數的深度強化學習',
        color: 'bg-blue-500',
    },
    {
        id: 'PPO',
        name: 'Proximal Policy Optimization',
        description: '近端策略優化算法',
        color: 'bg-green-500',
    },
    {
        id: 'SAC',
        name: 'Soft Actor-Critic',
        description: '軟演員評論家算法',
        color: 'bg-purple-500',
    },
]

export const AlgorithmExplainabilityPanel: React.FC<
    AlgorithmExplainabilityPanelProps
> = ({ algorithm, onAlgorithmSwitch, metrics: _metrics }) => {
    const [currentMetrics, setCurrentMetrics] = useState<AlgorithmMetrics>({
        confidence: 0.87,
        actionValue: 0.92,
        policyGradient: 0.15,
        explorationRate: 0.1,
        learningRate: 0.0003,
        rewardPrediction: 0.78,
    })

    const [decisionReasoning, _setDecisionReasoning] = useState<
        DecisionReasoning[]
    >([
        {
            factor: '信號強度',
            weight: 0.35,
            value: 0.85,
            impact: 0.3,
            description: '目標衛星信號強度良好，有利於穩定連接',
        },
        {
            factor: '負載狀況',
            weight: 0.25,
            value: 0.4,
            impact: 0.1,
            description: '目標衛星負載較低，可提供更好的服務品質',
        },
        {
            factor: '距離因子',
            weight: 0.2,
            value: 0.75,
            impact: 0.15,
            description: '衛星距離適中，傳輸延遲可接受',
        },
        {
            factor: '仰角條件',
            weight: 0.15,
            value: 0.92,
            impact: 0.14,
            description: '仰角條件優秀，信號傳播路徑良好',
        },
        {
            factor: '歷史表現',
            weight: 0.05,
            value: 0.88,
            impact: 0.04,
            description: '該衛星歷史表現良好，可靠性高',
        },
    ])

    const [isTraining, setIsTraining] = useState(false)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [decisionHistory, setDecisionHistory] = useState<any[]>([])

    // 模擬指標更新
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentMetrics((prev) => ({
                confidence: Math.max(
                    0.1,
                    Math.min(1, prev.confidence + (Math.random() - 0.5) * 0.05)
                ),
                actionValue: Math.max(
                    0.1,
                    Math.min(1, prev.actionValue + (Math.random() - 0.5) * 0.03)
                ),
                policyGradient: Math.max(
                    0,
                    Math.min(
                        1,
                        prev.policyGradient + (Math.random() - 0.5) * 0.02
                    )
                ),
                explorationRate: Math.max(
                    0,
                    Math.min(
                        1,
                        prev.explorationRate + (Math.random() - 0.5) * 0.01
                    )
                ),
                learningRate: prev.learningRate,
                rewardPrediction: Math.max(
                    0.1,
                    Math.min(
                        1,
                        prev.rewardPrediction + (Math.random() - 0.5) * 0.04
                    )
                ),
            }))
        }, 2000)

        return () => clearInterval(interval)
    }, [])

    // 獲取當前算法信息
    const currentAlgorithm = useMemo(() => {
        return ALGORITHMS.find((alg) => alg.id === algorithm) || ALGORITHMS[0]
    }, [algorithm])

    // 計算總體決策置信度
    const _totalConfidence = useMemo(() => {
        return decisionReasoning.reduce(
            (sum, reasoning) => sum + reasoning.impact,
            0
        )
    }, [decisionReasoning])

    // 獲取置信度等級
    const getConfidenceLevel = (confidence: number) => {
        if (confidence >= 0.9)
            return {
                level: '非常高',
                color: 'text-green-600',
                bgColor: 'bg-green-50',
            }
        if (confidence >= 0.7)
            return {
                level: '高',
                color: 'text-green-500',
                bgColor: 'bg-green-50',
            }
        if (confidence >= 0.5)
            return {
                level: '中等',
                color: 'text-yellow-600',
                bgColor: 'bg-yellow-50',
            }
        if (confidence >= 0.3)
            return {
                level: '低',
                color: 'text-orange-600',
                bgColor: 'bg-orange-50',
            }
        return { level: '非常低', color: 'text-red-600', bgColor: 'bg-red-50' }
    }

    // 算法切換
    const handleAlgorithmSwitch = (newAlgorithm: string) => {
        onAlgorithmSwitch(newAlgorithm)
        setIsTraining(true)
        setTimeout(() => setIsTraining(false), 3000)
    }

    // 模擬決策過程
    const simulateDecision = () => {
        const newDecision = {
            timestamp: Date.now(),
            algorithm,
            selectedSatellite: 'sat_001',
            confidence: currentMetrics.confidence,
            reasoning: decisionReasoning.map((r) => ({ ...r })),
        }
        setDecisionHistory((prev) => [newDecision, ...prev.slice(0, 4)])
    }

    const confidenceLevel = getConfidenceLevel(currentMetrics.confidence)

    return (
        <div className="algorithm-explainability-panel space-y-4">
            {/* 算法選擇 */}
            <Card>
                <CardHeader className="pb-3">
                    <CardTitle className="text-sm">算法選擇</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <div className="space-y-3">
                        {ALGORITHMS.map((alg) => (
                            <div
                                key={alg.id}
                                className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                                    algorithm === alg.id
                                        ? 'border-blue-500 bg-blue-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                }`}
                                onClick={() => handleAlgorithmSwitch(alg.id)}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div
                                            className={`w-3 h-3 rounded-full ${alg.color}`}
                                        />
                                        <span className="font-medium text-sm">
                                            {alg.name}
                                        </span>
                                    </div>
                                    {algorithm === alg.id && (
                                        <Badge
                                            variant="secondary"
                                            className="text-xs"
                                        >
                                            <CheckCircle className="w-3 h-3 mr-1" />
                                            使用中
                                        </Badge>
                                    )}
                                </div>
                                <p className="text-xs text-gray-600 mt-1">
                                    {alg.description}
                                </p>
                            </div>
                        ))}
                    </div>

                    {isTraining && (
                        <div className="mt-3 p-2 bg-blue-50 rounded-lg">
                            <div className="flex items-center gap-2 text-sm text-blue-600">
                                <Activity className="w-4 h-4 animate-pulse" />
                                算法切換中，正在重新訓練...
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* 決策透明化 */}
            <Tabs defaultValue="reasoning" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="reasoning">決策推理</TabsTrigger>
                    <TabsTrigger value="metrics">算法指標</TabsTrigger>
                    <TabsTrigger value="history">決策歷史</TabsTrigger>
                </TabsList>

                <TabsContent value="reasoning" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm flex items-center gap-2">
                                <Eye className="w-4 h-4" />
                                決策推理過程
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {/* 總體置信度 */}
                            <div
                                className={`p-3 rounded-lg ${confidenceLevel.bgColor} mb-4`}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium">
                                        總體置信度
                                    </span>
                                    <span
                                        className={`text-lg font-bold ${confidenceLevel.color}`}
                                    >
                                        {(
                                            currentMetrics.confidence * 100
                                        ).toFixed(1)}
                                        %
                                    </span>
                                </div>
                                <div className="flex items-center gap-2 text-sm">
                                    <Badge
                                        variant="outline"
                                        className={confidenceLevel.color}
                                    >
                                        {confidenceLevel.level}
                                    </Badge>
                                    <span className="text-gray-600">
                                        基於 {decisionReasoning.length}{' '}
                                        個決策因子
                                    </span>
                                </div>
                            </div>

                            {/* 決策因子分析 */}
                            <div className="space-y-3">
                                {decisionReasoning.map((reasoning, index) => (
                                    <div
                                        key={index}
                                        className="p-3 border rounded-lg"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                <Target className="w-4 h-4 text-blue-500" />
                                                <span className="font-medium text-sm">
                                                    {reasoning.factor}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Badge
                                                    variant="outline"
                                                    className="text-xs"
                                                >
                                                    權重:{' '}
                                                    {(
                                                        reasoning.weight * 100
                                                    ).toFixed(0)}
                                                    %
                                                </Badge>
                                                <span className="text-sm font-medium">
                                                    {(
                                                        reasoning.value * 100
                                                    ).toFixed(0)}
                                                    %
                                                </span>
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <Progress
                                                value={reasoning.value * 100}
                                                className="h-2"
                                            />
                                            <div className="flex items-center justify-between text-xs text-gray-600">
                                                <span>
                                                    {reasoning.description}
                                                </span>
                                                <span>
                                                    影響:{' '}
                                                    {(
                                                        reasoning.impact * 100
                                                    ).toFixed(1)}
                                                    %
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* 決策建議 */}
                            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-start gap-2">
                                    <Brain className="w-4 h-4 text-purple-500 mt-0.5" />
                                    <div className="flex-1">
                                        <div className="font-medium text-sm mb-1">
                                            算法建議
                                        </div>
                                        <div className="text-xs text-gray-600">
                                            基於當前分析，建議選擇 Starlink-1234
                                            衛星。
                                            該衛星在信號強度和仰角條件方面表現優異，
                                            綜合評分達到{' '}
                                            {(
                                                currentMetrics.confidence * 100
                                            ).toFixed(1)}
                                            %。
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="metrics" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm flex items-center gap-2">
                                <BarChart3 className="w-4 h-4" />
                                {currentAlgorithm.name} 指標
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span>決策置信度</span>
                                            <span className="font-medium">
                                                {(
                                                    currentMetrics.confidence *
                                                    100
                                                ).toFixed(1)}
                                                %
                                            </span>
                                        </div>
                                        <Progress
                                            value={
                                                currentMetrics.confidence * 100
                                            }
                                            className="h-2"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span>動作價值</span>
                                            <span className="font-medium">
                                                {(
                                                    currentMetrics.actionValue *
                                                    100
                                                ).toFixed(1)}
                                                %
                                            </span>
                                        </div>
                                        <Progress
                                            value={
                                                currentMetrics.actionValue * 100
                                            }
                                            className="h-2"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span>策略梯度</span>
                                            <span className="font-medium">
                                                {(
                                                    currentMetrics.policyGradient *
                                                    100
                                                ).toFixed(1)}
                                                %
                                            </span>
                                        </div>
                                        <Progress
                                            value={
                                                currentMetrics.policyGradient *
                                                100
                                            }
                                            className="h-2"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span>探索率</span>
                                            <span className="font-medium">
                                                {(
                                                    currentMetrics.explorationRate *
                                                    100
                                                ).toFixed(1)}
                                                %
                                            </span>
                                        </div>
                                        <Progress
                                            value={
                                                currentMetrics.explorationRate *
                                                100
                                            }
                                            className="h-2"
                                        />
                                    </div>
                                </div>

                                <div className="pt-4 border-t">
                                    <div className="grid grid-cols-1 gap-3">
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm text-gray-600">
                                                學習率
                                            </span>
                                            <span className="font-mono text-sm">
                                                {currentMetrics.learningRate}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm text-gray-600">
                                                獎勵預測
                                            </span>
                                            <span className="font-mono text-sm">
                                                {(
                                                    currentMetrics.rewardPrediction *
                                                    100
                                                ).toFixed(1)}
                                                %
                                            </span>
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
                            <CardTitle className="text-sm flex items-center gap-2">
                                <TrendingUp className="w-4 h-4" />
                                決策歷史
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {decisionHistory.length === 0 ? (
                                    <div className="text-center py-8 text-gray-500">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={simulateDecision}
                                        >
                                            模擬決策過程
                                        </Button>
                                        <p className="text-xs mt-2">
                                            點擊按鈕查看決策歷史
                                        </p>
                                    </div>
                                ) : (
                                    decisionHistory.map((decision, index) => (
                                        <div
                                            key={index}
                                            className="p-3 border rounded-lg"
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="flex items-center gap-2">
                                                    <Zap className="w-4 h-4 text-green-500" />
                                                    <span className="font-medium text-sm">
                                                        {decision.algorithm}{' '}
                                                        決策
                                                    </span>
                                                </div>
                                                <Badge
                                                    variant="secondary"
                                                    className="text-xs"
                                                >
                                                    {new Date(
                                                        decision.timestamp
                                                    ).toLocaleTimeString()}
                                                </Badge>
                                            </div>

                                            <div className="space-y-2">
                                                <div className="flex items-center justify-between text-sm">
                                                    <span>
                                                        選擇衛星:{' '}
                                                        {
                                                            decision.selectedSatellite
                                                        }
                                                    </span>
                                                    <span>
                                                        置信度:{' '}
                                                        {(
                                                            decision.confidence *
                                                            100
                                                        ).toFixed(1)}
                                                        %
                                                    </span>
                                                </div>

                                                <div className="text-xs text-gray-600">
                                                    基於{' '}
                                                    {decision.reasoning.length}{' '}
                                                    個決策因子的綜合分析
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>

                            {decisionHistory.length > 0 && (
                                <div className="mt-4 pt-3 border-t">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={simulateDecision}
                                        className="w-full"
                                    >
                                        新增決策記錄
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}

export default AlgorithmExplainabilityPanel
