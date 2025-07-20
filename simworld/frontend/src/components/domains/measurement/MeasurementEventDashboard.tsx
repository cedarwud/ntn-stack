/**
 * 測量事件統一儀表板
 * 實現簡易版/完整版模式的統一管理界面
 * 
 * 功能：
 * - 多事件類型切換 (A4, D1, D2, T1)
 * - 統一的視圖模式管理
 * - 全局配置和狀態管理
 * - 教育模式和說明系統
 */

import React, { useState, useCallback, useMemo } from 'react'
import { useViewModeManager } from '../../../hooks/useViewModeManager'
import ViewModeToggle from '../../common/ViewModeToggle'
import EnhancedA4ViewerWithModes from './charts/EnhancedA4ViewerWithModes'

// 事件類型定義
type EventType = 'A4' | 'D1' | 'D2' | 'T1'

interface EventInfo {
    id: EventType
    name: string
    description: string
    icon: string
    color: string
    complexity: 'basic' | 'intermediate' | 'advanced'
    standardRef: string
}

interface MeasurementEventDashboardProps {
    defaultEventType?: EventType
    enableGlobalViewMode?: boolean
    showEducationPanel?: boolean
    className?: string
}

const MeasurementEventDashboard: React.FC<MeasurementEventDashboardProps> = ({
    defaultEventType = 'A4',
    enableGlobalViewMode = true,
    showEducationPanel = true,
    className = ''
}) => {
    // 事件資訊配置
    const eventInfos: EventInfo[] = useMemo(() => [
        {
            id: 'A4',
            name: 'A4 信號強度事件',
            description: '鄰居細胞信號強度超過服務細胞時觸發的測量事件',
            icon: '📶',
            color: 'blue',
            complexity: 'intermediate',
            standardRef: '3GPP TS 38.331 Section 5.5.4.5'
        },
        {
            id: 'D1',
            name: 'D1 距離測量事件',
            description: 'UE 到兩個參考位置距離的雙重門檻事件',
            icon: '📏',
            color: 'green',
            complexity: 'basic',
            standardRef: '3GPP TS 38.331 Section 5.5.4.15'
        },
        {
            id: 'D2',
            name: 'D2 移動參考位置事件',
            description: 'UE 到移動參考位置（衛星）距離的測量事件',
            icon: '🛰️',
            color: 'purple',
            complexity: 'advanced',
            standardRef: '3GPP TS 38.331 Section 5.5.4.15a'
        },
        {
            id: 'T1',
            name: 'T1 時間條件事件',
            description: '基於時間窗口的條件觸發測量事件',
            icon: '⏱️',
            color: 'orange',
            complexity: 'intermediate',
            standardRef: '3GPP TS 38.331 Section 5.5.4.16'
        }
    ], [])

    // 當前選中的事件類型
    const [currentEventType, setCurrentEventType] = useState<EventType>(defaultEventType)
    const [showEducation, setShowEducation] = useState(showEducationPanel)

    // 視圖模式管理器 (全局)
    const globalViewModeManager = useViewModeManager({
        eventType: currentEventType,
        defaultMode: 'simple',
        enableLocalStorage: true,
        onModeChange: (mode) => {
            console.log(`全局視圖模式切換到: ${mode}`)
        }
    })

    // 當前事件資訊
    const currentEventInfo = useMemo(() => {
        return eventInfos.find(event => event.id === currentEventType)!
    }, [eventInfos, currentEventType])

    // 處理事件類型切換
    const handleEventTypeChange = useCallback((eventType: EventType) => {
        setCurrentEventType(eventType)
        
        // 如果啟用全局視圖模式，重新初始化管理器
        // 這裡應該通過 context 或狀態管理來處理
        console.log(`切換到事件類型: ${eventType}`)
    }, [])

    // 複雜度標識顏色
    const getComplexityColor = (complexity: string) => {
        switch (complexity) {
            case 'basic': return 'bg-green-100 text-green-800'
            case 'intermediate': return 'bg-yellow-100 text-yellow-800'
            case 'advanced': return 'bg-red-100 text-red-800'
            default: return 'bg-gray-100 text-gray-800'
        }
    }

    // 事件類型標籤顏色
    const getEventColor = (color: string) => {
        const colors = {
            blue: 'bg-blue-500 hover:bg-blue-600',
            green: 'bg-green-500 hover:bg-green-600',
            purple: 'bg-purple-500 hover:bg-purple-600',
            orange: 'bg-orange-500 hover:bg-orange-600'
        }
        return colors[color as keyof typeof colors] || colors.blue
    }

    // 渲染事件選擇器
    const renderEventSelector = () => (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {eventInfos.map((event) => (
                <button
                    key={event.id}
                    onClick={() => handleEventTypeChange(event.id)}
                    className={`
                        p-4 rounded-lg border-2 transition-all duration-200
                        ${currentEventType === event.id
                            ? `${getEventColor(event.color)} text-white border-transparent shadow-lg`
                            : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300 hover:shadow-md'
                        }
                    `}
                >
                    <div className="text-center">
                        <div className="text-2xl mb-2">{event.icon}</div>
                        <div className="font-semibold text-sm mb-1">{event.name}</div>
                        <div className={`
                            inline-block px-2 py-1 rounded-full text-xs font-medium
                            ${currentEventType === event.id
                                ? 'bg-white bg-opacity-20 text-white'
                                : getComplexityColor(event.complexity)
                            }
                        `}>
                            {event.complexity}
                        </div>
                    </div>
                </button>
            ))}
        </div>
    )

    // 渲染教育面板
    const renderEducationPanel = () => (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
                <div className="text-2xl">{currentEventInfo.icon}</div>
                <div className="flex-1">
                    <h3 className="font-semibold text-blue-900 mb-2">
                        {currentEventInfo.name}
                    </h3>
                    <p className="text-sm text-blue-800 mb-3">
                        {currentEventInfo.description}
                    </p>
                    
                    <div className="flex items-center space-x-4 text-xs text-blue-700">
                        <span className="flex items-center space-x-1">
                            <span>📋</span>
                            <span>{currentEventInfo.standardRef}</span>
                        </span>
                        <span className={`
                            px-2 py-1 rounded-full font-medium
                            ${getComplexityColor(currentEventInfo.complexity)}
                        `}>
                            {currentEventInfo.complexity} 級別
                        </span>
                    </div>

                    {/* 簡易模式說明 */}
                    {globalViewModeManager.currentMode === 'simple' && (
                        <div className="mt-3 p-3 bg-white rounded border border-blue-200">
                            <h4 className="text-sm font-medium text-blue-900 mb-1">
                                💡 簡易模式說明
                            </h4>
                            <p className="text-xs text-blue-700">
                                當前為簡易模式，只顯示核心參數和基本功能。
                                如需完整功能，請切換到完整版模式。
                            </p>
                        </div>
                    )}
                </div>
                
                <button
                    onClick={() => setShowEducation(false)}
                    className="text-blue-500 hover:text-blue-700 text-sm"
                >
                    ✕
                </button>
            </div>
        </div>
    )

    // 渲染事件組件
    const renderEventComponent = () => {
        switch (currentEventType) {
            case 'A4':
                return (
                    <EnhancedA4ViewerWithModes
                        onParameterChange={(params) => {
                            console.log('A4 參數變更:', params)
                        }}
                        onTriggerEvent={(eventData) => {
                            console.log('A4 事件觸發:', eventData)
                        }}
                    />
                )
            case 'D1':
                return (
                    <div className="h-full flex items-center justify-center bg-gray-100 rounded-lg">
                        <div className="text-center">
                            <div className="text-4xl mb-4">📏</div>
                            <h3 className="text-lg font-medium text-gray-700 mb-2">D1 距離測量事件</h3>
                            <p className="text-sm text-gray-500">增強版 D1 組件開發中...</p>
                        </div>
                    </div>
                )
            case 'D2':
                return (
                    <div className="h-full flex items-center justify-center bg-gray-100 rounded-lg">
                        <div className="text-center">
                            <div className="text-4xl mb-4">🛰️</div>
                            <h3 className="text-lg font-medium text-gray-700 mb-2">D2 移動參考位置事件</h3>
                            <p className="text-sm text-gray-500">增強版 D2 組件開發中...</p>
                        </div>
                    </div>
                )
            case 'T1':
                return (
                    <div className="h-full flex items-center justify-center bg-gray-100 rounded-lg">
                        <div className="text-center">
                            <div className="text-4xl mb-4">⏱️</div>
                            <h3 className="text-lg font-medium text-gray-700 mb-2">T1 時間條件事件</h3>
                            <p className="text-sm text-gray-500">增強版 T1 組件開發中...</p>
                        </div>
                    </div>
                )
            default:
                return null
        }
    }

    return (
        <div className={`h-full flex flex-col bg-gray-50 ${className}`}>
            {/* 頂部工具列 */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <h1 className="text-xl font-bold text-gray-900">
                            NTN 測量事件系統
                        </h1>
                        <span className="text-sm text-gray-500">
                            3GPP TS 38.331 標準實現
                        </span>
                    </div>

                    <div className="flex items-center space-x-4">
                        {/* 教育模式切換 */}
                        <button
                            onClick={() => setShowEducation(!showEducation)}
                            className={`
                                px-3 py-1 rounded text-sm font-medium transition-colors
                                ${showEducation
                                    ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }
                            `}
                        >
                            💡 說明
                        </button>

                        {/* 全局視圖模式切換 */}
                        {enableGlobalViewMode && (
                            <ViewModeToggle
                                viewModeManager={globalViewModeManager}
                                size="small"
                                showLabel={true}
                                showDescription={false}
                                enableKeyboardShortcut={true}
                                position="top-right"
                                style={{ position: 'relative', top: 'auto', right: 'auto' }}
                            />
                        )}
                    </div>
                </div>
            </div>

            {/* 事件選擇器 */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
                {renderEventSelector()}
            </div>

            {/* 教育面板 */}
            {showEducation && (
                <div className="px-6 py-4">
                    {renderEducationPanel()}
                </div>
            )}

            {/* 主要內容區 */}
            <div className="flex-1 overflow-hidden">
                {renderEventComponent()}
            </div>

            {/* 底部狀態欄 */}
            <div className="bg-white border-t border-gray-200 px-6 py-2">
                <div className="flex items-center justify-between text-xs text-gray-600">
                    <span>
                        當前事件: {currentEventInfo.name} | 
                        視圖模式: {globalViewModeManager.currentMode === 'simple' ? '簡易版' : '完整版'} |
                        參數級別: {globalViewModeManager.config.parameters.level}
                    </span>
                    <span>
                        更新間隔: {globalViewModeManager.config.performance.updateInterval}ms |
                        最大數據點: {globalViewModeManager.config.performance.maxDataPoints}
                    </span>
                </div>
            </div>
        </div>
    )
}

export default MeasurementEventDashboard