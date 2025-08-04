/**
 * 統一的測量事件配置管理
 * 支援所有 3GPP TS 38.331 測量事件 (A4, D1, D2, T1)
 */

import React from 'react'

// 基本類型定義
export type EventType = 'A4' // 移除 D2，只保留 A4 事件用於 MeasurementEventsModal
export type EventCategory = 'signal' | 'distance' | 'time'

// 動態導入適配後的 Enhanced 事件組件以優化性能
const AdaptedEnhancedA4Viewer = React.lazy(() => import('../adapters/EnhancedViewerAdapter').then(module => ({ default: module.AdaptedEnhancedA4Viewer })))
// 移除 D2 組件導入，D2 功能統一到 EventD2Viewer

export interface EventConfig {
    id: EventType
    name: string
    description: string
    shortName: string
    status: 'available' | 'coming-soon' | 'beta'
    category: 'signal' | 'distance' | 'time'
    standard: string
    ViewerComponent: React.ComponentType<unknown>
    icon: string
    color: {
        primary: string
        secondary: string
        background: string
    }
    parameters: {
        primary: string[]
        secondary: string[]
        units: Record<string, string>
    }
    conditions: {
        enter: string
        leave: string
    }
}

// 統一的事件配置庫 - 只保留 A4 事件用於 MeasurementEventsModal
export const EVENT_CONFIGS: Record<EventType, EventConfig> = {
    A4: {
        id: 'A4',
        name: 'Event A4',
        description: 'Neighbour becomes better than threshold',
        shortName: 'A4',
        status: 'available',
        category: 'signal',
        standard: '3GPP TS 38.331 Section 5.5.4.5',
        ViewerComponent: AdaptedEnhancedA4Viewer,
        icon: '📡',
        color: {
            primary: '#4A90E2',
            secondary: '#357ABD',
            background: 'rgba(74, 144, 226, 0.1)'
        },
        parameters: {
            primary: ['a4-Threshold', 'Hysteresis'],
            secondary: ['Offset Freq', 'Offset Cell', 'TimeToTrigger'],
            units: {
                'a4-Threshold': 'dBm',
                'Hysteresis': 'dB',
                'Offset Freq': 'dB',
                'Offset Cell': 'dB',
                'TimeToTrigger': 'ms'
            }
        },
        conditions: {
            enter: 'Mn + Ofn + Ocn - Hys > Thresh',
            leave: 'Mn + Ofn + Ocn + Hys < Thresh'
        }
    }
    // 移除 D2 配置 - D2 事件統一由 EventD2Viewer 通過 📊 D2 事件監控 按鈕訪問
}

// 獲取所有可用事件
export const getAvailableEvents = (): EventConfig[] => {
    return Object.values(EVENT_CONFIGS).filter(config => config.status === 'available')
}

// 根據類別獲取事件
export const getEventsByCategory = (category: EventConfig['category']): EventConfig[] => {
    return Object.values(EVENT_CONFIGS).filter(config => config.category === category)
}

// 獲取事件配置
export const getEventConfig = (eventType: EventType): EventConfig => {
    return EVENT_CONFIGS[eventType]
}

// 獲取事件顏色主題
export const getEventTheme = (eventType: EventType) => {
    return EVENT_CONFIGS[eventType].color
}

// 事件類別標籤
export const EVENT_CATEGORIES = {
    signal: { label: '信號測量', icon: '📶', description: '基於無線信號強度的測量事件' },
    distance: { label: '距離測量', icon: '📏', description: '基於地理位置距離的測量事件' },
    time: { label: '時間條件', icon: '⏰', description: '基於時間窗口的條件事件' }
} as const

export type EventCategory = keyof typeof EVENT_CATEGORIES