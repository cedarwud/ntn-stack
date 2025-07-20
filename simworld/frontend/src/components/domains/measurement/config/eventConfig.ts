/**
 * 統一的測量事件配置管理
 * 支援所有 3GPP TS 38.331 測量事件 (A4, D1, D2, T1)
 */

import React from 'react'

// 基本類型定義
export type EventType = 'A4' | 'D1' | 'D2' | 'T1'
export type EventCategory = 'signal' | 'distance' | 'time'

// 動態導入適配後的 Enhanced 事件組件以優化性能
const AdaptedEnhancedA4Viewer = React.lazy(() => import('../adapters/EnhancedViewerAdapter').then(module => ({ default: module.AdaptedEnhancedA4Viewer })))
const AdaptedEnhancedD1Viewer = React.lazy(() => import('../adapters/EnhancedViewerAdapter').then(module => ({ default: module.AdaptedEnhancedD1Viewer }))) 
const AdaptedEnhancedD2Viewer = React.lazy(() => import('../adapters/EnhancedViewerAdapter').then(module => ({ default: module.AdaptedEnhancedD2Viewer })))
const AdaptedEnhancedT1Viewer = React.lazy(() => import('../adapters/EnhancedViewerAdapter').then(module => ({ default: module.AdaptedEnhancedT1Viewer })))

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

// 統一的事件配置庫
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
    },
    D1: {
        id: 'D1',
        name: 'Event D1',
        description: 'Distance between UE and reference locations',
        shortName: 'D1',
        status: 'available',
        category: 'distance',
        standard: '3GPP TS 38.331 Section 5.5.4.15',
        ViewerComponent: AdaptedEnhancedD1Viewer,
        icon: '📍',
        color: {
            primary: '#50C878',
            secondary: '#45B06A',
            background: 'rgba(80, 200, 120, 0.1)'
        },
        parameters: {
            primary: ['distanceThreshFromReference1', 'distanceThreshFromReference2'],
            secondary: ['hysteresisLocation', 'TimeToTrigger'],
            units: {
                'distanceThreshFromReference1': 'm',
                'distanceThreshFromReference2': 'm',
                'hysteresisLocation': 'm',
                'TimeToTrigger': 'ms'
            }
        },
        conditions: {
            enter: 'Ml1 - Hys > Thresh1 且 Ml2 + Hys < Thresh2',
            leave: 'Ml1 + Hys < Thresh1 或 Ml2 - Hys > Thresh2'
        }
    },
    D2: {
        id: 'D2',
        name: 'Event D2',
        description: 'Distance between UE and moving reference locations',
        shortName: 'D2',
        status: 'available',
        category: 'distance',
        standard: '3GPP TS 38.331 Section 5.5.4.15a',
        ViewerComponent: AdaptedEnhancedD2Viewer,
        icon: '🛰️',
        color: {
            primary: '#FF6B35',
            secondary: '#E55A2E',
            background: 'rgba(255, 107, 53, 0.1)'
        },
        parameters: {
            primary: ['distanceThreshFromReference1', 'distanceThreshFromReference2'],
            secondary: ['hysteresisLocation', 'movingReferenceLocation', 'TimeToTrigger'],
            units: {
                'distanceThreshFromReference1': 'm',
                'distanceThreshFromReference2': 'm',
                'hysteresisLocation': 'm',
                'TimeToTrigger': 'ms'
            }
        },
        conditions: {
            enter: 'Ml1 - Hys > Thresh1 且 Ml2 + Hys < Thresh2',
            leave: 'Ml1 + Hys < Thresh1 或 Ml2 - Hys > Thresh2'
        }
    },
    T1: {
        id: 'T1',
        name: 'CondEvent T1',
        description: 'Time measured at UE within duration from threshold',
        shortName: 'T1',
        status: 'available',
        category: 'time',
        standard: '3GPP TS 38.331 Section 5.5.4.16',
        ViewerComponent: AdaptedEnhancedT1Viewer,
        icon: '⏱️',
        color: {
            primary: '#9B59B6',
            secondary: '#8E44AD',
            background: 'rgba(155, 89, 182, 0.1)'
        },
        parameters: {
            primary: ['t1-Threshold', 'Duration'],
            secondary: ['當前時間 Mt'],
            units: {
                't1-Threshold': 'ms',
                'Duration': 'ms',
                '當前時間 Mt': 'ms'
            }
        },
        conditions: {
            enter: 'Mt > Thresh1',
            leave: 'Mt > Thresh1 + Duration'
        }
    }
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