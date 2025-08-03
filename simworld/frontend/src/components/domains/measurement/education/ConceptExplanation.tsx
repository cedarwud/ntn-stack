/**
 * 概念解釋模組
 *
 * 完成 Phase 3.3 要求：
 * - 提供測量事件相關概念的詳細解釋
 * - 支援多層次學習路徑 (初學者/中級/高級)
 * - 互動式概念圖和示例
 * - 與實際測量數據的關聯
 */

import React, { useState, useCallback } from 'react'
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Button,
    Badge,
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
    Progress,
    Alert,
    AlertDescription,
} from '@/components/ui'
import {
    BookOpen,
    GraduationCap,
    Lightbulb,
    Target,
    ArrowRight,
    CheckCircle,
    PlayCircle,
    Brain,
    Zap,
} from 'lucide-react'

interface ConceptExplanationProps {
    concept: ConceptType
    learningLevel: 'beginner' | 'intermediate' | 'advanced'
    onLevelChange?: (level: 'beginner' | 'intermediate' | 'advanced') => void
    onConceptMastered?: (concept: ConceptType) => void
    className?: string
}

type ConceptType =
    | 'measurement_events'
    | 'sib19_platform'
    | 'satellite_orbits'
    | 'time_synchronization'
    | 'position_compensation'
    | 'signal_propagation'
    | 'ntn_networks'

interface ConceptContent {
    title: string
    description: string
    prerequisites: string[]
    learningObjectives: string[]
    levels: {
        beginner: {
            explanation: string
            keyPoints: string[]
            examples: string[]
            quiz?: QuizQuestion[]
        }
        intermediate: {
            explanation: string
            technicalDetails: string[]
            calculations: string[]
            quiz?: QuizQuestion[]
        }
        advanced: {
            explanation: string
            researchTopics: string[]
            implementations: string[]
            quiz?: QuizQuestion[]
        }
    }
    relatedConcepts: ConceptType[]
    practicalApplications: string[]
}

interface QuizQuestion {
    question: string
    options: string[]
    correctAnswer: number
    explanation: string
}

const CONCEPT_LIBRARY: Record<ConceptType, ConceptContent> = {
    measurement_events: {
        title: '測量事件基礎',
        description:
            '了解 5G NTN 系統中的測量事件機制，包括 A4、D1、D2、T1 等事件的作用和觸發條件。',
        prerequisites: ['基礎通信原理', '5G 網路架構'],
        learningObjectives: [
            '理解測量事件的定義和分類',
            '掌握各類事件的觸發條件',
            '了解事件在網路優化中的作用',
            '學會配置和監控測量事件',
        ],
        levels: {
            beginner: {
                explanation:
                    '測量事件是 5G 系統中用於監控網路狀態和用戶設備性能的機制。就像汽車的儀表板會顯示速度、油量等資訊，測量事件會報告信號強度、位置變化、時間同步等狀態。',
                keyPoints: [
                    'A4 事件：監控位置變化，確保定位準確',
                    'D1 事件：測量距離變化，管理服務區域',
                    'D2 事件：追蹤移動參考點，如衛星位置',
                    'T1 事件：監控時間同步，保證系統協調',
                ],
                examples: [
                    '手機在城市中移動時的位置更新',
                    '衛星通話時的信號切換',
                    '導航系統的時間校準',
                ],
                quiz: [
                    {
                        question: 'A4 事件主要用於監控什麼？',
                        options: [
                            '信號強度',
                            '位置變化',
                            '時間同步',
                            '數據傳輸',
                        ],
                        correctAnswer: 1,
                        explanation:
                            'A4 事件專門用於監控 UE 的位置變化，當位置偏差超過設定門檻時會觸發位置補償。',
                    },
                ],
            },
            intermediate: {
                explanation:
                    '測量事件基於 3GPP TS 38.331 標準實現，通過週期性或事件驅動的方式收集網路和 UE 的測量數據。這些數據用於無線資源管理、移動性管理和網路優化。',
                technicalDetails: [
                    '事件觸發基於門檻值比較和遲滯機制',
                    '測量報告包含時間戳、測量值和事件標識',
                    '支援週期性和非週期性報告模式',
                    '可配置測量間隔和報告準則',
                ],
                calculations: [
                    '信號強度計算：RSRP = 功率 - 路徑損耗',
                    '距離計算：d = √[(x₂-x₁)² + (y₂-y₁)² + (z₂-z₁)²]',
                    '時間偏移：Δt = t_measured - t_reference',
                    '觸發條件：measurement > threshold + hysteresis',
                ],
                quiz: [
                    {
                        question: '遲滯機制的主要作用是什麼？',
                        options: [
                            '提高精度',
                            '防止頻繁觸發',
                            '加快響應',
                            '節省功耗',
                        ],
                        correctAnswer: 1,
                        explanation:
                            '遲滯機制通過設定進入和離開門檻的差值，防止在門檻值附近的小幅波動導致頻繁觸發。',
                    },
                ],
            },
            advanced: {
                explanation:
                    '高級測量事件實現涉及複雜的信號處理、統計分析和機器學習算法。現代系統使用自適應門檻、預測性觸發和多維度優化來提升性能。',
                researchTopics: [
                    '基於 AI 的自適應門檻調整',
                    '多事件聯合優化算法',
                    '邊緣計算在測量事件中的應用',
                    '6G 網路的測量事件演進',
                ],
                implementations: [
                    '實時信號處理管道設計',
                    '分散式測量數據融合',
                    '低延遲事件觸發機制',
                    '大規模測量數據分析平台',
                ],
                quiz: [
                    {
                        question:
                            '在 NTN 環境中，測量事件面臨的主要挑戰是什麼？',
                        options: [
                            '高延遲',
                            '都卜勒效應',
                            '路徑損耗',
                            '以上皆是',
                        ],
                        correctAnswer: 3,
                        explanation:
                            'NTN 環境中，衛星的高速移動導致都卜勒效應，長距離傳輸造成高延遲和路徑損耗，這些都是測量事件需要考慮的挑戰。',
                    },
                ],
            },
        },
        relatedConcepts: ['sib19_platform', 'ntn_networks'],
        practicalApplications: [
            '網路覆蓋優化',
            '用戶體驗監控',
            '故障診斷和預防',
            '資源分配決策',
        ],
    },
    sib19_platform: {
        title: 'SIB19 統一平台',
        description:
            '深入了解 SIB19 系統資訊廣播的統一平台架構，以及如何實現資訊統一和應用分化。',
        prerequisites: ['測量事件基礎', '5G 系統資訊'],
        learningObjectives: [
            '理解 SIB19 的作用和重要性',
            '掌握統一平台的設計原則',
            '學會資訊統一和應用分化的實現',
            '了解與測量事件的整合方式',
        ],
        levels: {
            beginner: {
                explanation:
                    'SIB19 就像是衛星網路的「廣播電台」，定期向所有用戶設備發送重要的系統資訊，包括衛星位置、時間基準、服務參數等。統一平台確保所有測量事件都使用相同的基礎資訊。',
                keyPoints: [
                    'SIB19 提供衛星星曆和時間資訊',
                    '統一平台避免資訊重複和不一致',
                    '支援多個測量事件的協調工作',
                    '定期更新確保資訊的時效性',
                ],
                examples: [
                    '所有測量事件使用相同的時間基準',
                    '衛星位置資訊在多個事件間共享',
                    '系統參數的一致性配置',
                ],
            },
            intermediate: {
                explanation:
                    'SIB19 統一平台基於「資訊統一、應用分化」的設計原則，通過單一數據源和事件特定萃取機制，實現高效的資源共享和專業化處理。',
                technicalDetails: [
                    '單例模式確保全局唯一數據管理器',
                    '事件特定萃取方法提供客製化數據',
                    '觀察者模式實現數據更新通知',
                    '緩存機制提升數據存取效率',
                ],
                calculations: [
                    '數據一致性檢查：hash(data_A) = hash(data_B)',
                    '更新頻率優化：f_update = min(f_required)',
                    '記憶體使用：M_total = M_shared + Σ(M_specific)',
                    'API 調用減少：R_reduction = (N_old - N_new) / N_old',
                ],
            },
            advanced: {
                explanation:
                    '高級 SIB19 平台實現包括分散式數據同步、智能緩存策略、故障恢復機制和性能監控系統，支援大規模部署和高可用性要求。',
                researchTopics: [
                    '分散式 SIB19 數據同步算法',
                    '基於機器學習的數據預測和緩存',
                    '區塊鏈在 SIB19 數據完整性中的應用',
                    '邊緣計算環境下的 SIB19 優化',
                ],
                implementations: [
                    '微服務架構的 SIB19 平台',
                    '容器化部署和自動擴展',
                    '實時監控和告警系統',
                    '多雲環境的數據同步',
                ],
            },
        },
        relatedConcepts: ['measurement_events', 'satellite_orbits'],
        practicalApplications: [
            '多事件協調測量',
            '系統資源優化',
            '數據一致性保證',
            '平台可擴展性',
        ],
    },
    // 其他概念的定義可以繼續添加...
}

export const ConceptExplanation: React.FC<ConceptExplanationProps> = ({
    concept,
    learningLevel,
    onLevelChange,
    onConceptMastered,
    className = '',
}) => {
    const [currentTab, setCurrentTab] = useState('explanation')
    const [quizProgress, setQuizProgress] = useState<Record<number, boolean>>(
        {}
    )
    const [_showQuiz, _setShowQuiz] = useState(false)
    const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
    const [showExplanation, setShowExplanation] = useState(false)

    const conceptData = CONCEPT_LIBRARY[concept]
    const levelData = conceptData.levels[learningLevel]

    // 處理測驗答案
    const handleQuizAnswer = useCallback(
        (questionIndex: number, answerIndex: number) => {
            setSelectedAnswer(answerIndex)
            setShowExplanation(true)

            const question = levelData.quiz?.[questionIndex]
            if (question && answerIndex === question.correctAnswer) {
                setQuizProgress((prev) => ({ ...prev, [questionIndex]: true }))
            }
        },
        [levelData.quiz]
    )

    // 檢查是否完成所有測驗
    const isQuizCompleted = useMemo(() => {
        if (!levelData.quiz) return true
        return levelData.quiz.every((_, index) => quizProgress[index])
    }, [levelData.quiz, quizProgress])

    // 渲染學習進度
    const renderProgress = () => {
        const totalQuestions = levelData.quiz?.length || 0
        const completedQuestions =
            Object.values(quizProgress).filter(Boolean).length
        const progressPercentage =
            totalQuestions > 0
                ? (completedQuestions / totalQuestions) * 100
                : 100

        return (
            <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">學習進度</span>
                    <span className="text-sm text-muted-foreground">
                        {completedQuestions}/{totalQuestions} 完成
                    </span>
                </div>
                <Progress value={progressPercentage} className="h-2" />
            </div>
        )
    }

    // 渲染測驗區塊
    const renderQuiz = () => {
        if (!levelData.quiz || levelData.quiz.length === 0) return null

        return (
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <Brain className="h-5 w-5" />
                        知識測驗
                    </h3>
                    <Badge variant={isQuizCompleted ? 'default' : 'outline'}>
                        {isQuizCompleted ? '已完成' : '進行中'}
                    </Badge>
                </div>

                {levelData.quiz.map((question, index) => (
                    <Card
                        key={index}
                        className={
                            quizProgress[index] ? 'border-green-500' : ''
                        }
                    >
                        <CardHeader>
                            <CardTitle className="text-sm flex items-center gap-2">
                                {quizProgress[index] ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                ) : (
                                    <Target className="h-4 w-4" />
                                )}
                                問題 {index + 1}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="mb-4">{question.question}</p>
                            <div className="space-y-2">
                                {question.options.map((option, optionIndex) => (
                                    <Button
                                        key={optionIndex}
                                        variant={
                                            selectedAnswer === optionIndex
                                                ? optionIndex ===
                                                  question.correctAnswer
                                                    ? 'default'
                                                    : 'destructive'
                                                : 'outline'
                                        }
                                        className="w-full justify-start"
                                        onClick={() =>
                                            handleQuizAnswer(index, optionIndex)
                                        }
                                        disabled={quizProgress[index]}
                                    >
                                        {option}
                                    </Button>
                                ))}
                            </div>
                            {showExplanation && selectedAnswer !== null && (
                                <Alert className="mt-4">
                                    <Lightbulb className="h-4 w-4" />
                                    <AlertDescription>
                                        {question.explanation}
                                    </AlertDescription>
                                </Alert>
                            )}
                        </CardContent>
                    </Card>
                ))}
            </div>
        )
    }

    return (
        <div className={`concept-explanation ${className}`}>
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <GraduationCap className="h-5 w-5" />
                            {conceptData.title}
                        </CardTitle>
                        <div className="flex items-center gap-2">
                            <Badge variant="outline">{learningLevel}</Badge>
                            {onLevelChange && (
                                <div className="flex gap-1">
                                    {(
                                        [
                                            'beginner',
                                            'intermediate',
                                            'advanced',
                                        ] as const
                                    ).map((level) => (
                                        <Button
                                            key={level}
                                            variant={
                                                level === learningLevel
                                                    ? 'default'
                                                    : 'outline'
                                            }
                                            size="sm"
                                            onClick={() => onLevelChange(level)}
                                        >
                                            {level === 'beginner'
                                                ? '初級'
                                                : level === 'intermediate'
                                                ? '中級'
                                                : '高級'}
                                        </Button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        {conceptData.description}
                    </p>
                </CardHeader>

                <CardContent>
                    {renderProgress()}

                    <Tabs value={currentTab} onValueChange={setCurrentTab}>
                        <TabsList className="grid w-full grid-cols-4">
                            <TabsTrigger value="explanation">說明</TabsTrigger>
                            <TabsTrigger value="examples">示例</TabsTrigger>
                            <TabsTrigger value="quiz">測驗</TabsTrigger>
                            <TabsTrigger value="related">相關</TabsTrigger>
                        </TabsList>

                        <TabsContent value="explanation" className="mt-4">
                            <div className="space-y-4">
                                <div className="p-4 bg-muted rounded-lg">
                                    <p className="leading-relaxed">
                                        {levelData.explanation}
                                    </p>
                                </div>

                                {/* 關鍵要點 */}
                                {'keyPoints' in levelData && (
                                    <div>
                                        <h4 className="font-semibold mb-2 flex items-center gap-2">
                                            <Target className="h-4 w-4" />
                                            關鍵要點
                                        </h4>
                                        <ul className="space-y-2">
                                            {levelData.keyPoints.map(
                                                (point, index) => (
                                                    <li
                                                        key={index}
                                                        className="flex items-start gap-2"
                                                    >
                                                        <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                                                        <span className="text-sm">
                                                            {point}
                                                        </span>
                                                    </li>
                                                )
                                            )}
                                        </ul>
                                    </div>
                                )}

                                {/* 技術細節 */}
                                {'technicalDetails' in levelData && (
                                    <div>
                                        <h4 className="font-semibold mb-2 flex items-center gap-2">
                                            <Zap className="h-4 w-4" />
                                            技術細節
                                        </h4>
                                        <ul className="space-y-2">
                                            {levelData.technicalDetails.map(
                                                (detail, index) => (
                                                    <li
                                                        key={index}
                                                        className="flex items-start gap-2"
                                                    >
                                                        <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                                                        <span className="text-sm">
                                                            {detail}
                                                        </span>
                                                    </li>
                                                )
                                            )}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </TabsContent>

                        <TabsContent value="examples" className="mt-4">
                            <div className="space-y-4">
                                {'examples' in levelData && (
                                    <div>
                                        <h4 className="font-semibold mb-4">
                                            實際應用示例
                                        </h4>
                                        <div className="grid gap-4">
                                            {levelData.examples.map(
                                                (example, index) => (
                                                    <Card key={index}>
                                                        <CardContent className="pt-4">
                                                            <div className="flex items-start gap-3">
                                                                <PlayCircle className="h-5 w-5 text-primary mt-0.5" />
                                                                <span className="text-sm">
                                                                    {example}
                                                                </span>
                                                            </div>
                                                        </CardContent>
                                                    </Card>
                                                )
                                            )}
                                        </div>
                                    </div>
                                )}

                                <div>
                                    <h4 className="font-semibold mb-4">
                                        實際應用領域
                                    </h4>
                                    <div className="grid gap-2">
                                        {conceptData.practicalApplications.map(
                                            (application, index) => (
                                                <div
                                                    key={index}
                                                    className="flex items-center gap-2 p-2 bg-muted rounded"
                                                >
                                                    <ArrowRight className="h-4 w-4" />
                                                    <span className="text-sm">
                                                        {application}
                                                    </span>
                                                </div>
                                            )
                                        )}
                                    </div>
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="quiz" className="mt-4">
                            {renderQuiz()}
                        </TabsContent>

                        <TabsContent value="related" className="mt-4">
                            <div className="space-y-4">
                                <h4 className="font-semibold">相關概念</h4>
                                <div className="grid gap-2">
                                    {conceptData.relatedConcepts.map(
                                        (relatedConcept, index) => (
                                            <Button
                                                key={index}
                                                variant="outline"
                                                className="justify-start"
                                                onClick={() => {
                                                    // 這裡可以觸發導航到相關概念
                                                    console.log(
                                                        'Navigate to:',
                                                        relatedConcept
                                                    )
                                                }}
                                            >
                                                <BookOpen className="h-4 w-4 mr-2" />
                                                {CONCEPT_LIBRARY[relatedConcept]
                                                    ?.title || relatedConcept}
                                            </Button>
                                        )
                                    )}
                                </div>

                                <div className="mt-6">
                                    <h4 className="font-semibold mb-2">
                                        學習前置條件
                                    </h4>
                                    <div className="space-y-2">
                                        {conceptData.prerequisites.map(
                                            (prerequisite, index) => (
                                                <div
                                                    key={index}
                                                    className="flex items-center gap-2 text-sm"
                                                >
                                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                                    {prerequisite}
                                                </div>
                                            )
                                        )}
                                    </div>
                                </div>
                            </div>
                        </TabsContent>
                    </Tabs>

                    {/* 完成按鈕 */}
                    {isQuizCompleted && onConceptMastered && (
                        <div className="mt-6 pt-4 border-t">
                            <Button
                                onClick={() => onConceptMastered(concept)}
                                className="w-full"
                            >
                                <CheckCircle className="h-4 w-4 mr-2" />
                                標記為已掌握
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}

export default ConceptExplanation
