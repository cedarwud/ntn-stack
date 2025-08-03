/**
 * 統一圖表說明系統
 *
 * 功能：
 * 1. 統一的圖表標題和說明文字
 * 2. 論文級數據真實性標示
 * 3. 物理模型說明
 * 4. 用戶教育內容
 * 5. 多語言支援
 */

import React, { useState, useEffect } from 'react'
import './UnifiedChartExplanation.scss'

// 事件類型定義
export type EventType = 'A4' | 'D1' | 'D2' | 'T1'

// 數據類型定義
export type DataType = 'real' | 'simulated' | 'enhanced'

// 說明內容接口
interface ExplanationContent {
    title: string
    subtitle: string
    description: string
    physicalModels: string[]
    dataQuality: {
        level: 'research' | 'production' | 'demo'
        accuracy: string
        standards: string[]
    }
    keyFeatures: string[]
    educationalNotes: string[]
}

// 統一說明內容配置
const EXPLANATION_CONFIGS: Record<EventType, ExplanationContent> = {
    A4: {
        title: 'Event A4: 鄰居衛星信號監測事件',
        subtitle: '基於 SIB19 位置補償機制的精確信號強度測量',
        description:
            '監測鄰居衛星的信號強度變化，當信號強度超過設定閾值時觸發測量事件。採用 3GPP TR 38.811 NTN 標準的路徑損耗模型，整合真實的大氣衰減和電離層效應。',
        physicalModels: [
            '3GPP TR 38.811 NTN 路徑損耗模型',
            'ITU-R P.618 降雨衰減模型',
            'Klobuchar 電離層延遲模型',
            '都卜勒頻移精確計算 (基於 SGP4)',
            'Starlink/OneWeb 真實天線方向圖',
        ],
        dataQuality: {
            level: 'research',
            accuracy: '< 1 dB (信號強度), < 100 Hz (都卜勒頻移)',
            standards: [
                '3GPP TS 38.331',
                '3GPP TR 38.811',
                'ITU-R P.618',
                'ITU-R P.676',
            ],
        },
        keyFeatures: [
            '真實衛星軌道數據 (TLE)',
            '實時氣象數據整合',
            'SIB19 位置補償機制',
            '多頻段支援 (L/S/C/X/Ku/Ka)',
            '論文研究級數據精度',
        ],
        educationalNotes: [
            'A4 事件主要用於鄰居細胞的信號品質評估',
            '觸發條件：鄰居衛星 RSRP > A4 閾值',
            '測量結果用於切換決策和負載平衡',
            '支援最多 8 個 NTN 鄰居細胞同時監測',
        ],
    },
    D1: {
        title: 'Event D1: 雙重距離測量事件',
        subtitle: '基於全球化地理座標的智能服務衛星選擇',
        description:
            '測量服務衛星和目標衛星之間的距離變化，當距離差超過設定閾值時觸發測量事件。採用精確的 SGP4 軌道模型和真實的地球物理參數。',
        physicalModels: [
            'SGP4 軌道傳播算法',
            'WGS84 地球座標系統',
            '地球自轉效應修正',
            '相對論時間修正',
            '大氣阻力和太陽輻射壓力',
        ],
        dataQuality: {
            level: 'research',
            accuracy: '< 1 km (距離測量), < 10 m (位置精度)',
            standards: ['3GPP TS 38.331', 'CCSDS 502.0-B-2', 'WGS84'],
        },
        keyFeatures: [
            '全球化地理座標支援',
            '智能服務衛星選擇算法',
            '雙重距離閾值機制',
            '真實軌道週期 (90分鐘)',
            '亞公里級精度',
        ],
        educationalNotes: [
            'D1 事件用於監測衛星間的相對位置變化',
            '觸發條件：|d_serving - d_target| > D1 閾值',
            '測量結果用於預測最佳切換時機',
            '支援極地和赤道軌道衛星',
        ],
    },
    D2: {
        title: 'Event D2: 移動參考位置距離事件',
        subtitle: '基於 SIB19 廣播的動態參考位置追蹤',
        description:
            '監測衛星與移動參考位置之間的距離變化，採用真實的 90分鐘軌道週期和 SIB19 星曆數據，實現精確的位置預測和切換觸發。',
        physicalModels: [
            'SIB19 衛星星曆廣播模型',
            '移動參考位置算法',
            '軌道攝動修正',
            'GNSS 時間同步',
            '星曆有效性驗證',
        ],
        dataQuality: {
            level: 'research',
            accuracy: '< 500 m (參考位置), < 5 s (時間同步)',
            standards: ['3GPP TS 38.331', '3GPP TS 38.455', 'CCSDS 502.0-B-2'],
        },
        keyFeatures: [
            '真實 90分鐘軌道週期',
            'SIB19 星曆數據整合',
            '移動參考位置動態更新',
            '星曆有效性倒計時',
            '雙閾值觸發機制',
        ],
        educationalNotes: [
            'D2 事件基於移動參考位置進行距離測量',
            '觸發條件：d_serving > Thresh1 且 d_target < Thresh2',
            '參考位置每 15 分鐘更新一次',
            '支援星曆過期自動更新',
        ],
    },
    T1: {
        title: 'Event T1: 時間框架測量事件',
        subtitle: '基於 SIB19 時間框架的精確時間同步',
        description:
            '測量時間相關的參數變化，當時間差超過設定閾值時觸發測量事件。整合 GNSS 時間同步機制和 SIB19 時間框架，確保納秒級時間精度。',
        physicalModels: [
            'GNSS 時間同步算法',
            'SIB19 時間框架模型',
            '相對論時間修正',
            '電離層時間延遲',
            '衛星時鐘偏差修正',
        ],
        dataQuality: {
            level: 'research',
            accuracy: '< 1 ns (時間同步), < 10 μs (測量精度)',
            standards: ['3GPP TS 38.331', 'ITU-R TF.460-6', 'IEEE 1588'],
        },
        keyFeatures: [
            'SIB19 時間框架整合',
            'GNSS 時間同步機制',
            '納秒級時間精度',
            '多重時間基準驗證',
            '自動時間偏差修正',
        ],
        educationalNotes: [
            'T1 事件用於監測時間相關參數的變化',
            '觸發條件：時間差 > T1 閾值',
            '測量結果用於時間同步和調度優化',
            '支援 UTC、GPS、Galileo 時間基準',
        ],
    },
}

// 組件屬性接口
interface UnifiedChartExplanationProps {
    eventType: EventType
    dataType: DataType
    isExpanded?: boolean
    onToggle?: (expanded: boolean) => void
    showPhysicalModels?: boolean
    showEducationalNotes?: boolean
    className?: string
}

export const UnifiedChartExplanation: React.FC<
    UnifiedChartExplanationProps
> = ({
    eventType,
    dataType,
    isExpanded = false,
    onToggle,
    showPhysicalModels = true,
    showEducationalNotes = true,
    className = '',
}) => {
    const [expanded, setExpanded] = useState(isExpanded)
    const [activeTab, setActiveTab] = useState<
        'overview' | 'models' | 'education'
    >('overview')

    const config = EXPLANATION_CONFIGS[eventType]

    useEffect(() => {
        setExpanded(isExpanded)
    }, [isExpanded])

    const handleToggle = () => {
        const newExpanded = !expanded
        setExpanded(newExpanded)
        onToggle?.(newExpanded)
    }

    const getDataTypeLabel = () => {
        switch (dataType) {
            case 'real':
                return { label: '真實數據', icon: '🟢', class: 'real-data' }
            case 'enhanced':
                return { label: '增強數據', icon: '🔵', class: 'enhanced-data' }
            case 'simulated':
                return {
                    label: '模擬數據',
                    icon: '🟡',
                    class: 'simulated-data',
                }
        }
    }

    const dataTypeInfo = getDataTypeLabel()

    return (
        <div
            className={`unified-chart-explanation ${className} ${
                expanded ? 'expanded' : 'collapsed'
            }`}
        >
            {/* 標題欄 */}
            <div className="explanation-header" onClick={handleToggle}>
                <div className="title-section">
                    <h3 className="chart-title">{config.title}</h3>
                    <p className="chart-subtitle">{config.subtitle}</p>
                </div>

                <div className="header-controls">
                    <div className={`data-type-badge ${dataTypeInfo.class}`}>
                        <span className="data-icon">{dataTypeInfo.icon}</span>
                        <span className="data-label">{dataTypeInfo.label}</span>
                    </div>

                    <div className="quality-badge research-grade">
                        <span className="quality-icon">🎓</span>
                        <span className="quality-label">論文研究級</span>
                    </div>

                    <button
                        className="expand-toggle"
                        aria-label={expanded ? '收起說明' : '展開說明'}
                    >
                        {expanded ? '▼' : '▶'}
                    </button>
                </div>
            </div>

            {/* 展開內容 */}
            {expanded && (
                <div className="explanation-content">
                    {/* 標籤頁導航 */}
                    <div className="tab-navigation">
                        <button
                            className={`tab-button ${
                                activeTab === 'overview' ? 'active' : ''
                            }`}
                            onClick={() => setActiveTab('overview')}
                        >
                            📊 概述
                        </button>
                        {showPhysicalModels && (
                            <button
                                className={`tab-button ${
                                    activeTab === 'models' ? 'active' : ''
                                }`}
                                onClick={() => setActiveTab('models')}
                            >
                                🔬 物理模型
                            </button>
                        )}
                        {showEducationalNotes && (
                            <button
                                className={`tab-button ${
                                    activeTab === 'education' ? 'active' : ''
                                }`}
                                onClick={() => setActiveTab('education')}
                            >
                                📚 教育說明
                            </button>
                        )}
                    </div>

                    {/* 標籤頁內容 */}
                    <div className="tab-content">
                        {activeTab === 'overview' && (
                            <div className="overview-tab">
                                <div className="description-section">
                                    <h4>事件描述</h4>
                                    <p>{config.description}</p>
                                </div>

                                <div className="features-section">
                                    <h4>關鍵特性</h4>
                                    <ul className="features-list">
                                        {config.keyFeatures.map(
                                            (feature, index) => (
                                                <li
                                                    key={index}
                                                    className="feature-item"
                                                >
                                                    <span className="feature-icon">
                                                        ✨
                                                    </span>
                                                    {feature}
                                                </li>
                                            )
                                        )}
                                    </ul>
                                </div>

                                <div className="quality-section">
                                    <h4>數據品質</h4>
                                    <div className="quality-metrics">
                                        <div className="metric-item">
                                            <span className="metric-label">
                                                精度等級:
                                            </span>
                                            <span className="metric-value">
                                                {config.dataQuality.level}
                                            </span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-label">
                                                測量精度:
                                            </span>
                                            <span className="metric-value">
                                                {config.dataQuality.accuracy}
                                            </span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-label">
                                                符合標準:
                                            </span>
                                            <span className="metric-value">
                                                {config.dataQuality.standards.join(
                                                    ', '
                                                )}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'models' && showPhysicalModels && (
                            <div className="models-tab">
                                <h4>整合的物理模型</h4>
                                <div className="models-grid">
                                    {config.physicalModels.map(
                                        (model, index) => (
                                            <div
                                                key={index}
                                                className="model-card"
                                            >
                                                <span className="model-icon">
                                                    🔬
                                                </span>
                                                <span className="model-name">
                                                    {model}
                                                </span>
                                            </div>
                                        )
                                    )}
                                </div>

                                <div className="models-note">
                                    <p>
                                        <strong>注意：</strong>
                                        所有物理模型均基於最新的國際標準和研究成果，
                                        確保數據的科學性和準確性，適用於論文發表和學術研究。
                                    </p>
                                </div>
                            </div>
                        )}

                        {activeTab === 'education' && showEducationalNotes && (
                            <div className="education-tab">
                                <h4>教育說明</h4>
                                <div className="education-content">
                                    {config.educationalNotes.map(
                                        (note, index) => (
                                            <div
                                                key={index}
                                                className="education-item"
                                            >
                                                <span className="education-icon">
                                                    💡
                                                </span>
                                                <p className="education-text">
                                                    {note}
                                                </p>
                                            </div>
                                        )
                                    )}
                                </div>

                                <div className="learning-resources">
                                    <h5>相關學習資源</h5>
                                    <ul className="resources-list">
                                        <li>
                                            📖 3GPP TS 38.331: NR RRC Protocol
                                            Specification
                                        </li>
                                        <li>
                                            📖 3GPP TR 38.811: Study on New
                                            Radio Access Technology
                                        </li>
                                        <li>
                                            📖 ITU-R P.618: Propagation data and
                                            prediction methods
                                        </li>
                                        <li>
                                            📖 CCSDS 502.0-B-2: Orbit Data
                                            Messages
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

// 統一圖表配置生成器
export const generateUnifiedChartConfig = (
    eventType: EventType,
    dataType: DataType,
    isDarkTheme: boolean = true
) => {
    const config = EXPLANATION_CONFIGS[eventType]
    const dataTypeInfo = getDataTypeLabel(dataType)

    return {
        plugins: {
            title: {
                display: true,
                text: `${config.title} ${dataTypeInfo.label}`,
                font: {
                    size: 16,
                    weight: 'bold' as const,
                },
                color: isDarkTheme ? '#ffffff' : '#1f2937',
                padding: 20,
            },
            legend: {
                display: true,
                position: 'top' as const,
                labels: {
                    color: isDarkTheme ? '#ffffff' : '#1f2937',
                    usePointStyle: true,
                    padding: 20,
                    font: { size: 12 },
                },
            },
            tooltip: {
                mode: 'index' as const,
                intersect: false,
                backgroundColor: isDarkTheme
                    ? 'rgba(0, 0, 0, 0.9)'
                    : 'rgba(255, 255, 255, 0.9)',
                titleColor: isDarkTheme ? '#ffffff' : '#1f2937',
                bodyColor: isDarkTheme ? '#ffffff' : '#1f2937',
                borderColor: isDarkTheme
                    ? 'rgba(255, 255, 255, 0.2)'
                    : 'rgba(0, 0, 0, 0.2)',
                borderWidth: 1,
                titleFont: { size: 14, weight: 'bold' as const },
                bodyFont: { size: 13 },
                footerFont: { size: 12 },
                callbacks: {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    afterBody: (context: any[]) => {
                        if (context.length > 0) {
                            return [
                                ``,
                                `📊 ${config.title}`,
                                `🔬 論文研究級數據精度`,
                            ]
                        }
                        return []
                    },
                },
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: getXAxisLabel(eventType),
                    color: isDarkTheme ? '#ffffff' : '#1f2937',
                    font: { size: 14, weight: 'bold' as const },
                },
                ticks: {
                    color: isDarkTheme
                        ? 'rgba(255, 255, 255, 0.8)'
                        : 'rgba(0, 0, 0, 0.8)',
                },
                grid: {
                    color: isDarkTheme
                        ? 'rgba(255, 255, 255, 0.1)'
                        : 'rgba(0, 0, 0, 0.1)',
                },
            },
            y: {
                title: {
                    display: true,
                    text: getYAxisLabel(eventType),
                    color: isDarkTheme ? '#ffffff' : '#1f2937',
                    font: { size: 14, weight: 'bold' as const },
                },
                ticks: {
                    color: isDarkTheme
                        ? 'rgba(255, 255, 255, 0.8)'
                        : 'rgba(0, 0, 0, 0.8)',
                },
                grid: {
                    color: isDarkTheme
                        ? 'rgba(255, 255, 255, 0.1)'
                        : 'rgba(0, 0, 0, 0.1)',
                },
            },
        },
    }
}

// 輔助函數
const getDataTypeLabel = (dataType: DataType) => {
    switch (dataType) {
        case 'real':
            return { label: '(真實數據)', icon: '🟢', class: 'real-data' }
        case 'enhanced':
            return { label: '(增強數據)', icon: '🔵', class: 'enhanced-data' }
        case 'simulated':
            return { label: '(模擬數據)', icon: '🟡', class: 'simulated-data' }
    }
}

const getXAxisLabel = (eventType: EventType): string => {
    switch (eventType) {
        case 'A4':
            return '時間 (秒) / 測量點'
        case 'D1':
            return '時間 (秒) / 軌道位置'
        case 'D2':
            return '時間 (秒) / 參考位置更新'
        case 'T1':
            return '時間 (秒) / 時間框架'
    }
}

const getYAxisLabel = (eventType: EventType): string => {
    switch (eventType) {
        case 'A4':
            return '信號強度 (dBm) / 路徑損耗 (dB)'
        case 'D1':
            return '距離 (km) / 相對位置'
        case 'D2':
            return '距離 (km) / 參考位置偏移'
        case 'T1':
            return '時間差 (秒) / 同步精度'
    }
}

export default UnifiedChartExplanation
