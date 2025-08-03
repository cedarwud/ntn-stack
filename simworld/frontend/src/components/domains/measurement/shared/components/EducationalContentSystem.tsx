/**
 * 教育內容系統
 *
 * 功能：
 * 1. 互動式教學指南
 * 2. 逐步操作說明
 * 3. 概念解釋和背景知識
 * 4. 實際應用案例
 * 5. 常見問題解答
 */

import React, { useState } from 'react'
import { EventType } from './UnifiedChartExplanation'
import './EducationalContentSystem.scss'

// 教育內容類型
export type EducationContentType =
    | 'tutorial' // 教學指南
    | 'concept' // 概念解釋
    | 'case-study' // 案例研究
    | 'faq' // 常見問題
    | 'reference' // 參考資料

// 教育內容難度等級
export type DifficultyLevel =
    | 'beginner'
    | 'intermediate'
    | 'advanced'
    | 'expert'

// 教育內容接口
interface EducationalContent {
    id: string
    title: string
    type: EducationContentType
    difficulty: DifficultyLevel
    duration: number // 預估學習時間 (分鐘)
    description: string
    content: EducationalSection[]
    prerequisites?: string[]
    relatedTopics?: string[]
    tags: string[]
}

// 教育內容章節
interface EducationalSection {
    id: string
    title: string
    type: 'text' | 'image' | 'video' | 'interactive' | 'quiz'
    content: string
    media?: {
        url: string
        alt?: string
        caption?: string
    }
    interactive?: {
        type: 'simulation' | 'calculator' | 'diagram'
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        config: any
    }
    quiz?: {
        question: string
        options: string[]
        correctAnswer: number
        explanation: string
    }
}

// 教育內容配置
const EDUCATIONAL_CONTENTS: Record<EventType, EducationalContent[]> = {
    A4: [
        {
            id: 'a4-basics',
            title: 'A4 事件基礎概念',
            type: 'concept',
            difficulty: 'beginner',
            duration: 15,
            description: '了解 A4 事件的基本原理和觸發條件',
            tags: ['基礎', '信號測量', 'RSRP'],
            content: [
                {
                    id: 'a4-intro',
                    title: '什麼是 A4 事件？',
                    type: 'text',
                    content:
                        'A4 事件是 3GPP 標準中定義的測量事件，用於監測鄰居衛星的信號強度。當鄰居衛星的 RSRP (Reference Signal Received Power) 超過設定的閾值時，會觸發 A4 測量報告。',
                },
                {
                    id: 'a4-trigger',
                    title: '觸發條件',
                    type: 'text',
                    content:
                        'A4 事件的觸發條件是：鄰居衛星 RSRP > A4 閾值 + 滯後值。這個機制可以避免因信號波動造成的頻繁觸發。',
                },
                {
                    id: 'a4-applications',
                    title: '實際應用',
                    type: 'text',
                    content:
                        'A4 事件主要用於：\n• 鄰居細胞發現\n• 負載平衡決策\n• 切換準備\n• 信號品質監測',
                },
            ],
        },
        {
            id: 'a4-advanced',
            title: 'A4 事件進階分析',
            type: 'tutorial',
            difficulty: 'advanced',
            duration: 30,
            description: '深入了解 A4 事件的物理模型和數據真實性',
            tags: ['進階', '物理模型', '數據分析'],
            prerequisites: ['a4-basics'],
            content: [
                {
                    id: 'a4-physics',
                    title: '物理模型解析',
                    type: 'text',
                    content:
                        '本系統採用的 A4 事件物理模型包括：\n• 3GPP TR 38.811 NTN 路徑損耗模型\n• ITU-R P.618 降雨衰減模型\n• Klobuchar 電離層延遲模型\n• 真實衛星天線方向圖',
                },
                {
                    id: 'a4-accuracy',
                    title: '數據精度分析',
                    type: 'text',
                    content:
                        '系統達到論文研究級精度：\n• 信號強度測量精度：< 1 dB\n• 都卜勒頻移精度：< 100 Hz\n• 位置精度：< 10 m\n• 時間同步精度：< 1 ns',
                },
            ],
        },
    ],
    D1: [
        {
            id: 'd1-basics',
            title: 'D1 事件基礎概念',
            type: 'concept',
            difficulty: 'beginner',
            duration: 20,
            description: '了解 D1 事件的雙重距離測量原理',
            tags: ['基礎', '距離測量', '軌道計算'],
            content: [
                {
                    id: 'd1-intro',
                    title: 'D1 事件原理',
                    type: 'text',
                    content:
                        'D1 事件監測服務衛星和目標衛星之間的距離變化。當兩個衛星與用戶的距離差超過設定閾值時觸發測量。',
                },
                {
                    id: 'd1-calculation',
                    title: '距離計算方法',
                    type: 'text',
                    content:
                        '系統使用 SGP4 軌道模型計算精確的衛星位置，然後基於 WGS84 座標系統計算與用戶的距離。',
                },
            ],
        },
    ],
    D2: [
        {
            id: 'd2-basics',
            title: 'D2 事件基礎概念',
            type: 'concept',
            difficulty: 'intermediate',
            duration: 25,
            description: '了解 D2 事件的移動參考位置機制',
            tags: ['基礎', '參考位置', 'SIB19'],
            content: [
                {
                    id: 'd2-intro',
                    title: 'D2 事件特點',
                    type: 'text',
                    content:
                        'D2 事件基於移動參考位置進行距離測量，參考位置會根據 SIB19 廣播的星曆數據動態更新。',
                },
                {
                    id: 'd2-orbit',
                    title: '真實軌道參數',
                    type: 'text',
                    content:
                        '系統採用真實的 90分鐘軌道週期，相比簡化模型的 120秒，大幅提升了預測精度。',
                },
            ],
        },
    ],
    T1: [
        {
            id: 't1-basics',
            title: 'T1 事件基礎概念',
            type: 'concept',
            difficulty: 'intermediate',
            duration: 18,
            description: '了解 T1 事件的時間同步機制',
            tags: ['基礎', '時間同步', 'GNSS'],
            content: [
                {
                    id: 't1-intro',
                    title: 'T1 事件功能',
                    type: 'text',
                    content:
                        'T1 事件監測時間相關參數的變化，確保系統的時間同步精度滿足 NTN 網路的嚴格要求。',
                },
                {
                    id: 't1-sync',
                    title: '時間同步技術',
                    type: 'text',
                    content:
                        '系統整合 GNSS 時間同步和 SIB19 時間框架，實現納秒級的時間精度。',
                },
            ],
        },
    ],
}

// 組件屬性
interface EducationalContentSystemProps {
    eventType?: EventType
    contentType?: EducationContentType
    difficulty?: DifficultyLevel
    isOpen?: boolean
    onClose?: () => void
    className?: string
}

export const EducationalContentSystem: React.FC<
    EducationalContentSystemProps
> = ({
    eventType,
    contentType: _contentType,
    difficulty: _difficulty,
    isOpen = false,
    onClose,
    className = '',
}) => {
    const [selectedContent, setSelectedContent] =
        useState<EducationalContent | null>(null)
    const [currentSection, setCurrentSection] = useState(0)
    const [completedSections, setCompletedSections] = useState<Set<string>>(
        new Set()
    )
    const [searchQuery, setSearchQuery] = useState('')
    const [filterType, setFilterType] = useState<EducationContentType | 'all'>(
        'all'
    )
    const [filterDifficulty, setFilterDifficulty] = useState<
        DifficultyLevel | 'all'
    >('all')

    // 獲取所有教育內容
    const getAllContents = (): EducationalContent[] => {
        if (eventType) {
            return EDUCATIONAL_CONTENTS[eventType] || []
        }
        return Object.values(EDUCATIONAL_CONTENTS).flat()
    }

    // 過濾內容
    const filteredContents = getAllContents().filter((content) => {
        const matchesSearch =
            content.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            content.description
                .toLowerCase()
                .includes(searchQuery.toLowerCase()) ||
            content.tags.some((tag) =>
                tag.toLowerCase().includes(searchQuery.toLowerCase())
            )

        const matchesType = filterType === 'all' || content.type === filterType
        const matchesDifficulty =
            filterDifficulty === 'all' ||
            content.difficulty === filterDifficulty

        return matchesSearch && matchesType && matchesDifficulty
    })

    // 標記章節完成
    const markSectionCompleted = (sectionId: string) => {
        setCompletedSections((prev) => new Set([...prev, sectionId]))
    }

    // 獲取難度標籤
    const getDifficultyLabel = (difficulty: DifficultyLevel) => {
        const labels = {
            beginner: { text: '初學者', color: '#10b981', icon: '🌱' },
            intermediate: { text: '中級', color: '#f59e0b', icon: '🌿' },
            advanced: { text: '進階', color: '#ef4444', icon: '🌳' },
            expert: { text: '專家', color: '#8b5cf6', icon: '🏆' },
        }
        return labels[difficulty]
    }

    // 獲取內容類型標籤
    const getContentTypeLabel = (type: EducationContentType) => {
        const labels = {
            tutorial: { text: '教學指南', icon: '📚' },
            concept: { text: '概念解釋', icon: '💡' },
            'case-study': { text: '案例研究', icon: '📊' },
            faq: { text: '常見問題', icon: '❓' },
            reference: { text: '參考資料', icon: '📖' },
        }
        return labels[type]
    }

    if (!isOpen) return null

    return (
        <div className={`educational-content-system ${className}`}>
            <div className="education-overlay" onClick={onClose} />

            <div className="education-modal">
                {/* 標題欄 */}
                <div className="education-header">
                    <div className="header-title">
                        <h2>📚 教育內容系統</h2>
                        <p>互動式學習指南和概念解釋</p>
                    </div>
                    <button className="close-button" onClick={onClose}>
                        ✕
                    </button>
                </div>

                {/* 主要內容 */}
                <div className="education-body">
                    {!selectedContent ? (
                        // 內容列表視圖
                        <div className="content-browser">
                            {/* 搜索和過濾 */}
                            <div className="browser-controls">
                                <div className="search-box">
                                    <input
                                        type="text"
                                        placeholder="搜索教育內容..."
                                        value={searchQuery}
                                        onChange={(e) =>
                                            setSearchQuery(e.target.value)
                                        }
                                    />
                                    <span className="search-icon">🔍</span>
                                </div>

                                <div className="filter-controls">
                                    <select
                                        value={filterType}
                                        onChange={(e) =>
                                            setFilterType(
                                                e.target.value as
                                                    | EducationContentType
                                                    | 'all'
                                            )
                                        }
                                    >
                                        <option value="all">所有類型</option>
                                        <option value="tutorial">
                                            教學指南
                                        </option>
                                        <option value="concept">
                                            概念解釋
                                        </option>
                                        <option value="case-study">
                                            案例研究
                                        </option>
                                        <option value="faq">常見問題</option>
                                        <option value="reference">
                                            參考資料
                                        </option>
                                    </select>

                                    <select
                                        value={filterDifficulty}
                                        onChange={(e) =>
                                            setFilterDifficulty(
                                                e.target.value as
                                                    | DifficultyLevel
                                                    | 'all'
                                            )
                                        }
                                    >
                                        <option value="all">所有難度</option>
                                        <option value="beginner">初學者</option>
                                        <option value="intermediate">
                                            中級
                                        </option>
                                        <option value="advanced">進階</option>
                                        <option value="expert">專家</option>
                                    </select>
                                </div>
                            </div>

                            {/* 內容卡片 */}
                            <div className="content-grid">
                                {filteredContents.map((content) => {
                                    const difficultyInfo = getDifficultyLabel(
                                        content.difficulty
                                    )
                                    const typeInfo = getContentTypeLabel(
                                        content.type
                                    )

                                    return (
                                        <div
                                            key={content.id}
                                            className="content-card"
                                            onClick={() =>
                                                setSelectedContent(content)
                                            }
                                        >
                                            <div className="card-header">
                                                <div className="content-type">
                                                    <span className="type-icon">
                                                        {typeInfo.icon}
                                                    </span>
                                                    <span className="type-text">
                                                        {typeInfo.text}
                                                    </span>
                                                </div>
                                                <div
                                                    className="difficulty-badge"
                                                    style={{
                                                        color: difficultyInfo.color,
                                                    }}
                                                >
                                                    <span className="difficulty-icon">
                                                        {difficultyInfo.icon}
                                                    </span>
                                                    <span className="difficulty-text">
                                                        {difficultyInfo.text}
                                                    </span>
                                                </div>
                                            </div>

                                            <div className="card-body">
                                                <h3 className="content-title">
                                                    {content.title}
                                                </h3>
                                                <p className="content-description">
                                                    {content.description}
                                                </p>

                                                <div className="content-meta">
                                                    <span className="duration">
                                                        ⏱️ {content.duration}{' '}
                                                        分鐘
                                                    </span>
                                                    <span className="sections">
                                                        📄{' '}
                                                        {content.content.length}{' '}
                                                        章節
                                                    </span>
                                                </div>

                                                <div className="content-tags">
                                                    {content.tags.map((tag) => (
                                                        <span
                                                            key={tag}
                                                            className="tag"
                                                        >
                                                            {tag}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>

                            {filteredContents.length === 0 && (
                                <div className="no-results">
                                    <p>沒有找到符合條件的教育內容</p>
                                    <button
                                        onClick={() => {
                                            setSearchQuery('')
                                            setFilterType('all')
                                            setFilterDifficulty('all')
                                        }}
                                    >
                                        清除篩選條件
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        // 內容詳細視圖
                        <div className="content-viewer">
                            {/* 內容導航 */}
                            <div className="content-navigation">
                                <button
                                    className="back-button"
                                    onClick={() => setSelectedContent(null)}
                                >
                                    ← 返回列表
                                </button>

                                <div className="progress-info">
                                    <span>
                                        進度: {currentSection + 1} /{' '}
                                        {selectedContent.content.length}
                                    </span>
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{
                                                width: `${
                                                    ((currentSection + 1) /
                                                        selectedContent.content
                                                            .length) *
                                                    100
                                                }%`,
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* 內容標題 */}
                            <div className="content-header">
                                <h2>{selectedContent.title}</h2>
                                <p>{selectedContent.description}</p>
                            </div>

                            {/* 章節內容 */}
                            <div className="section-content">
                                {selectedContent.content[currentSection] && (
                                    <ContentSection
                                        section={
                                            selectedContent.content[
                                                currentSection
                                            ]
                                        }
                                        isCompleted={completedSections.has(
                                            selectedContent.content[
                                                currentSection
                                            ].id
                                        )}
                                        onComplete={() =>
                                            markSectionCompleted(
                                                selectedContent.content[
                                                    currentSection
                                                ].id
                                            )
                                        }
                                    />
                                )}
                            </div>

                            {/* 導航按鈕 */}
                            <div className="section-navigation">
                                <button
                                    className="nav-button prev"
                                    disabled={currentSection === 0}
                                    onClick={() =>
                                        setCurrentSection(
                                            Math.max(0, currentSection - 1)
                                        )
                                    }
                                >
                                    上一章節
                                </button>

                                <span className="section-indicator">
                                    {selectedContent.content.map((_, index) => (
                                        <button
                                            key={index}
                                            className={`indicator ${
                                                index === currentSection
                                                    ? 'active'
                                                    : ''
                                            } ${
                                                completedSections.has(
                                                    selectedContent.content[
                                                        index
                                                    ].id
                                                )
                                                    ? 'completed'
                                                    : ''
                                            }`}
                                            onClick={() =>
                                                setCurrentSection(index)
                                            }
                                        />
                                    ))}
                                </span>

                                <button
                                    className="nav-button next"
                                    disabled={
                                        currentSection ===
                                        selectedContent.content.length - 1
                                    }
                                    onClick={() =>
                                        setCurrentSection(
                                            Math.min(
                                                selectedContent.content.length -
                                                    1,
                                                currentSection + 1
                                            )
                                        )
                                    }
                                >
                                    下一章節
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

// 章節內容組件
interface ContentSectionProps {
    section: EducationalSection
    isCompleted: boolean
    onComplete: () => void
}

const ContentSection: React.FC<ContentSectionProps> = ({
    section,
    isCompleted,
    onComplete,
}) => {
    const [quizAnswer, setQuizAnswer] = useState<number | null>(null)
    const [showQuizResult, setShowQuizResult] = useState(false)

    const handleQuizSubmit = () => {
        if (quizAnswer !== null && section.quiz) {
            setShowQuizResult(true)
            if (quizAnswer === section.quiz.correctAnswer) {
                onComplete()
            }
        }
    }

    return (
        <div className="content-section">
            <h3 className="section-title">{section.title}</h3>

            <div className="section-body">
                {section.type === 'text' && (
                    <div className="text-content">
                        {section.content.split('\n').map((paragraph, index) => (
                            <p key={index}>{paragraph}</p>
                        ))}
                    </div>
                )}

                {section.type === 'image' && section.media && (
                    <div className="image-content">
                        <img src={section.media.url} alt={section.media.alt} />
                        {section.media.caption && (
                            <p className="caption">{section.media.caption}</p>
                        )}
                    </div>
                )}

                {section.type === 'quiz' && section.quiz && (
                    <div className="quiz-content">
                        <h4 className="quiz-question">
                            {section.quiz.question}
                        </h4>
                        <div className="quiz-options">
                            {section.quiz.options.map((option, index) => (
                                <label key={index} className="quiz-option">
                                    <input
                                        type="radio"
                                        name="quiz-answer"
                                        value={index}
                                        checked={quizAnswer === index}
                                        onChange={() => setQuizAnswer(index)}
                                    />
                                    <span>{option}</span>
                                </label>
                            ))}
                        </div>

                        {!showQuizResult && (
                            <button
                                className="quiz-submit"
                                onClick={handleQuizSubmit}
                                disabled={quizAnswer === null}
                            >
                                提交答案
                            </button>
                        )}

                        {showQuizResult && (
                            <div
                                className={`quiz-result ${
                                    quizAnswer === section.quiz.correctAnswer
                                        ? 'correct'
                                        : 'incorrect'
                                }`}
                            >
                                <p className="result-text">
                                    {quizAnswer === section.quiz.correctAnswer
                                        ? '✅ 答對了！'
                                        : '❌ 答錯了'}
                                </p>
                                <p className="explanation">
                                    {section.quiz.explanation}
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {!isCompleted && section.type !== 'quiz' && (
                <button className="complete-section" onClick={onComplete}>
                    標記為已完成
                </button>
            )}

            {isCompleted && <div className="completion-badge">✅ 已完成</div>}
        </div>
    )
}

// 教育內容快速啟動器
export const EducationQuickLauncher: React.FC<{
    eventType: EventType
    onLaunch: () => void
    className?: string
}> = ({ eventType, onLaunch, className = '' }) => {
    const contents = EDUCATIONAL_CONTENTS[eventType] || []
    const beginnerContents = contents.filter((c) => c.difficulty === 'beginner')

    return (
        <div className={`education-quick-launcher ${className}`}>
            <button className="launcher-button" onClick={onLaunch}>
                <span className="launcher-icon">🎓</span>
                <div className="launcher-text">
                    <span className="launcher-title">
                        學習 {eventType} 事件
                    </span>
                    <span className="launcher-subtitle">
                        {beginnerContents.length} 個教學內容
                    </span>
                </div>
                <span className="launcher-arrow">→</span>
            </button>
        </div>
    )
}

export default EducationalContentSystem
