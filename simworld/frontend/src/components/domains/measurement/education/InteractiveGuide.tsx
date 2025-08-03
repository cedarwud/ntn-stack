/**
 * 互動式指南組件
 *
 * 完成 Phase 3.3 要求：
 * - 提供步驟式的互動學習體驗
 * - 實時指導用戶操作測量事件系統
 * - 結合實際操作和理論學習
 * - 支援個人化學習路徑
 */

import React, { useState, useCallback } from 'react'
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Button,
    Badge,
    Progress,
    Alert,
    AlertDescription,
    Separator,
} from '@/components/ui'
import {
    Play,
    Pause,
    SkipForward,
    RotateCcw,
    CheckCircle,
    ArrowRight,
    Lightbulb,
    Target,
    Eye,
    Hand,
    BookOpen,
    Award,
} from 'lucide-react'

interface InteractiveGuideProps {
    guideType: GuideType
    onStepComplete?: (step: number) => void
    onGuideComplete?: () => void
    className?: string
}

type GuideType =
    | 'getting_started'
    | 'a4_measurement'
    | 'd1_measurement'
    | 'd2_measurement'
    | 't1_measurement'
    | 'advanced_analysis'

interface GuideStep {
    id: number
    title: string
    description: string
    instruction: string
    actionType: 'observe' | 'click' | 'configure' | 'analyze'
    targetElement?: string
    expectedResult?: string
    hints?: string[]
    theory?: string
    nextStepCondition?: 'manual' | 'automatic' | 'event'
}

interface GuideDefinition {
    title: string
    description: string
    estimatedTime: number // 分鐘
    difficulty: 'beginner' | 'intermediate' | 'advanced'
    prerequisites: string[]
    learningObjectives: string[]
    steps: GuideStep[]
}

const GUIDE_LIBRARY: Record<GuideType, GuideDefinition> = {
    getting_started: {
        title: '系統入門指南',
        description: '學習如何使用 NTN 測量事件系統的基本功能',
        estimatedTime: 15,
        difficulty: 'beginner',
        prerequisites: [],
        learningObjectives: [
            '了解系統界面佈局',
            '學會基本操作流程',
            '掌握參數配置方法',
            '理解測量結果解讀',
        ],
        steps: [
            {
                id: 1,
                title: '系統界面導覽',
                description: '熟悉系統的主要界面元素和功能區域',
                instruction:
                    '觀察系統界面，識別主要功能區域：圖表區、控制面板、參數配置區',
                actionType: 'observe',
                expectedResult: '能夠識別界面的主要組成部分',
                theory: '良好的界面設計有助於提高工作效率和減少操作錯誤',
                nextStepCondition: 'manual',
            },
            {
                id: 2,
                title: '選擇測量事件',
                description: '學習如何選擇和切換不同的測量事件',
                instruction:
                    '點擊頂部的事件標籤，嘗試切換到不同的測量事件 (A4, D1, D2, T1)',
                actionType: 'click',
                targetElement: '.measurement-event-tabs',
                expectedResult: '成功切換到不同的測量事件界面',
                hints: ['標籤通常位於界面頂部', '每個事件都有不同的圖表和參數'],
                nextStepCondition: 'manual',
            },
            {
                id: 3,
                title: '啟動測量',
                description: '學習如何開始和停止測量過程',
                instruction: '找到「開始測量」按鈕並點擊，觀察系統狀態的變化',
                actionType: 'click',
                targetElement: '.start-measurement-button',
                expectedResult:
                    '系統開始收集測量數據，狀態指示器顯示「測量中」',
                theory: '測量過程會持續收集數據直到手動停止或達到預設條件',
                nextStepCondition: 'automatic',
            },
            {
                id: 4,
                title: '觀察實時數據',
                description: '學習如何解讀實時測量數據和圖表',
                instruction: '觀察圖表中的數據變化，注意數值的更新和趨勢',
                actionType: 'observe',
                expectedResult: '能夠理解圖表顯示的測量數據含義',
                hints: ['注意數值的單位和範圍', '觀察數據的變化趨勢'],
                theory: '實時數據反映了系統的當前狀態，有助於及時發現問題',
                nextStepCondition: 'manual',
            },
            {
                id: 5,
                title: '配置基本參數',
                description: '學習如何調整測量參數以適應不同需求',
                instruction: '在參數面板中調整門檻值，觀察對測量結果的影響',
                actionType: 'configure',
                targetElement: '.parameter-panel',
                expectedResult: '參數變更後，測量行為發生相應變化',
                theory: '適當的參數配置是獲得準確測量結果的關鍵',
                nextStepCondition: 'manual',
            },
        ],
    },
    a4_measurement: {
        title: 'A4 位置補償測量',
        description: '深入學習 A4 事件的位置補償機制和應用',
        estimatedTime: 25,
        difficulty: 'intermediate',
        prerequisites: ['系統入門指南'],
        learningObjectives: [
            '理解位置補償的原理',
            '掌握 A4 事件的配置方法',
            '學會分析位置補償效果',
            '了解衛星選擇算法',
        ],
        steps: [
            {
                id: 1,
                title: '理解位置補償概念',
                description: '學習什麼是位置補償以及為什麼需要它',
                instruction:
                    '閱讀 A4 事件的說明，理解位置補償在衛星通信中的重要性',
                actionType: 'observe',
                theory: '位置補償用於修正 GNSS 定位誤差，提高定位精度',
                nextStepCondition: 'manual',
            },
            {
                id: 2,
                title: '配置補償參數',
                description: '學習如何設定位置補償的門檻值和範圍',
                instruction: '調整補償門檻值 (1-10km) 和最大補償範圍 (1-10km)',
                actionType: 'configure',
                expectedResult: '參數設定完成，系統接受新的配置',
                hints: ['門檻值決定何時觸發補償', '範圍限制補償的最大幅度'],
                nextStepCondition: 'manual',
            },
            {
                id: 3,
                title: '觀察補償過程',
                description: '啟動測量並觀察位置補償的觸發和執行',
                instruction: '開始測量，等待位置補償事件的觸發',
                actionType: 'observe',
                expectedResult: '當位置偏差超過門檻時，系統觸發補償',
                theory: '補償過程包括偏差檢測、補償計算和位置修正',
                nextStepCondition: 'event',
            },
            {
                id: 4,
                title: '分析補償效果',
                description: '學習如何評估位置補償的效果和精度',
                instruction: '查看補償歷史和性能分析，評估補償效果',
                actionType: 'analyze',
                expectedResult: '能夠理解補償前後的位置精度改善',
                nextStepCondition: 'manual',
            },
        ],
    },
    // 其他指南定義...
}

export const InteractiveGuide: React.FC<InteractiveGuideProps> = ({
    guideType,
    onStepComplete,
    onGuideComplete,
    className = '',
}) => {
    const [currentStep, setCurrentStep] = useState(0)
    const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())
    const [isActive, setIsActive] = useState(false)
    const [showHints, setShowHints] = useState(false)
    const [_stepStartTime, setStepStartTime] = useState<number>(0)

    const guide = GUIDE_LIBRARY[guideType]
    const currentStepData = guide.steps[currentStep]
    const progress = (completedSteps.size / guide.steps.length) * 100

    // 開始指南
    const startGuide = useCallback(() => {
        setIsActive(true)
        setCurrentStep(0)
        setCompletedSteps(new Set())
        setStepStartTime(Date.now())
    }, [])

    // 暫停指南
    const pauseGuide = useCallback(() => {
        setIsActive(false)
    }, [])

    // 重置指南
    const resetGuide = useCallback(() => {
        setIsActive(false)
        setCurrentStep(0)
        setCompletedSteps(new Set())
        setShowHints(false)
    }, [])

    // 完成當前步驟
    const completeCurrentStep = useCallback(() => {
        const newCompletedSteps = new Set(completedSteps)
        newCompletedSteps.add(currentStep)
        setCompletedSteps(newCompletedSteps)

        onStepComplete?.(currentStep)

        // 移動到下一步或完成指南
        if (currentStep < guide.steps.length - 1) {
            setCurrentStep(currentStep + 1)
            setStepStartTime(Date.now())
            setShowHints(false)
        } else {
            setIsActive(false)
            onGuideComplete?.()
        }
    }, [
        currentStep,
        completedSteps,
        guide.steps.length,
        onStepComplete,
        onGuideComplete,
    ])

    // 跳到下一步
    const skipToNextStep = useCallback(() => {
        if (currentStep < guide.steps.length - 1) {
            setCurrentStep(currentStep + 1)
            setStepStartTime(Date.now())
            setShowHints(false)
        }
    }, [currentStep, guide.steps.length])

    // 渲染動作圖標
    const renderActionIcon = (actionType: string) => {
        switch (actionType) {
            case 'observe':
                return <Eye className="h-4 w-4" />
            case 'click':
                return <Hand className="h-4 w-4" />
            case 'configure':
                return <Target className="h-4 w-4" />
            case 'analyze':
                return <BookOpen className="h-4 w-4" />
            default:
                return <ArrowRight className="h-4 w-4" />
        }
    }

    // 渲染步驟列表
    const renderStepList = () => (
        <div className="space-y-2">
            {guide.steps.map((step, index) => (
                <div
                    key={step.id}
                    className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                        index === currentStep
                            ? 'bg-primary/10 border border-primary/20'
                            : completedSteps.has(index)
                            ? 'bg-green-50 border border-green-200'
                            : 'bg-muted'
                    }`}
                >
                    <div className="flex-shrink-0">
                        {completedSteps.has(index) ? (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : index === currentStep ? (
                            renderActionIcon(step.actionType)
                        ) : (
                            <div className="w-5 h-5 rounded-full border-2 border-muted-foreground" />
                        )}
                    </div>
                    <div className="flex-1">
                        <div className="font-medium text-sm">{step.title}</div>
                        <div className="text-xs text-muted-foreground">
                            {step.description}
                        </div>
                    </div>
                    <Badge variant="outline" className="text-xs">
                        {step.actionType}
                    </Badge>
                </div>
            ))}
        </div>
    )

    return (
        <div className={`interactive-guide ${className}`}>
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <BookOpen className="h-5 w-5" />
                            {guide.title}
                        </CardTitle>
                        <div className="flex items-center gap-2">
                            <Badge variant="outline">{guide.difficulty}</Badge>
                            <Badge variant="outline">
                                {guide.estimatedTime} 分鐘
                            </Badge>
                        </div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        {guide.description}
                    </p>
                </CardHeader>

                <CardContent>
                    {/* 進度條 */}
                    <div className="mb-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">
                                學習進度
                            </span>
                            <span className="text-sm text-muted-foreground">
                                {completedSteps.size}/{guide.steps.length}{' '}
                                步驟完成
                            </span>
                        </div>
                        <Progress value={progress} className="h-2" />
                    </div>

                    {/* 控制按鈕 */}
                    <div className="flex gap-2 mb-6">
                        {!isActive ? (
                            <Button onClick={startGuide} className="flex-1">
                                <Play className="h-4 w-4 mr-2" />
                                開始指南
                            </Button>
                        ) : (
                            <Button
                                onClick={pauseGuide}
                                variant="outline"
                                className="flex-1"
                            >
                                <Pause className="h-4 w-4 mr-2" />
                                暫停指南
                            </Button>
                        )}
                        <Button onClick={resetGuide} variant="outline">
                            <RotateCcw className="h-4 w-4 mr-2" />
                            重置
                        </Button>
                    </div>

                    {/* 當前步驟 */}
                    {isActive && currentStepData && (
                        <Card className="mb-6 border-primary/20">
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center gap-2">
                                    {renderActionIcon(
                                        currentStepData.actionType
                                    )}
                                    步驟 {currentStep + 1}:{' '}
                                    {currentStepData.title}
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="mb-4">
                                    {currentStepData.instruction}
                                </p>

                                {currentStepData.theory && (
                                    <Alert className="mb-4">
                                        <Lightbulb className="h-4 w-4" />
                                        <AlertDescription>
                                            <strong>理論背景：</strong>{' '}
                                            {currentStepData.theory}
                                        </AlertDescription>
                                    </Alert>
                                )}

                                {currentStepData.expectedResult && (
                                    <div className="mb-4 p-3 bg-muted rounded-lg">
                                        <div className="font-medium text-sm mb-1">
                                            預期結果：
                                        </div>
                                        <div className="text-sm">
                                            {currentStepData.expectedResult}
                                        </div>
                                    </div>
                                )}

                                {currentStepData.hints && (
                                    <div className="mb-4">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() =>
                                                setShowHints(!showHints)
                                            }
                                        >
                                            {showHints
                                                ? '隱藏提示'
                                                : '顯示提示'}
                                        </Button>
                                        {showHints && (
                                            <div className="mt-2 space-y-1">
                                                {currentStepData.hints.map(
                                                    (hint, index) => (
                                                        <div
                                                            key={index}
                                                            className="text-sm text-muted-foreground flex items-start gap-2"
                                                        >
                                                            <Lightbulb className="h-3 w-3 mt-0.5 flex-shrink-0" />
                                                            {hint}
                                                        </div>
                                                    )
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}

                                <div className="flex gap-2">
                                    <Button onClick={completeCurrentStep}>
                                        <CheckCircle className="h-4 w-4 mr-2" />
                                        完成此步驟
                                    </Button>
                                    <Button
                                        variant="outline"
                                        onClick={skipToNextStep}
                                    >
                                        <SkipForward className="h-4 w-4 mr-2" />
                                        跳過
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* 步驟列表 */}
                    <div>
                        <h4 className="font-semibold mb-4">指南步驟</h4>
                        {renderStepList()}
                    </div>

                    {/* 學習目標 */}
                    <Separator className="my-6" />
                    <div>
                        <h4 className="font-semibold mb-4 flex items-center gap-2">
                            <Target className="h-4 w-4" />
                            學習目標
                        </h4>
                        <ul className="space-y-2">
                            {guide.learningObjectives.map(
                                (objective, index) => (
                                    <li
                                        key={index}
                                        className="flex items-start gap-2 text-sm"
                                    >
                                        <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                                        {objective}
                                    </li>
                                )
                            )}
                        </ul>
                    </div>

                    {/* 完成獎勵 */}
                    {progress === 100 && (
                        <Alert className="mt-6">
                            <Award className="h-4 w-4" />
                            <AlertDescription>
                                🎉 恭喜！您已完成「{guide.title}
                                」指南。您現在已掌握了相關的操作技能和理論知識。
                            </AlertDescription>
                        </Alert>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}

export default InteractiveGuide
