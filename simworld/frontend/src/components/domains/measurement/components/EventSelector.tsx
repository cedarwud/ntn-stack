/**
 * EventSelector - 統一的事件選擇器組件
 * 支援所有測量事件的選擇和切換，可在多個地方重用
 */

import React, { useState, useCallback, useMemo } from 'react'
import { EVENT_CONFIGS, EVENT_CATEGORIES, getAvailableEvents, getEventsByCategory } from '../config/eventConfig'
import type { EventType, EventConfig, EventCategory } from '../config/eventConfig'
import './EventSelector.scss'

interface EventSelectorProps {
    selectedEvent: EventType
    onEventChange: (eventType: EventType) => void
    mode?: 'compact' | 'detailed' | 'card'
    showCategories?: boolean
    showDescription?: boolean
    showStatus?: boolean
    className?: string
    style?: React.CSSProperties
}

export const EventSelector: React.FC<EventSelectorProps> = React.memo(({
    selectedEvent,
    onEventChange,
    mode = 'detailed',
    showCategories = true,
    showDescription = true,
    showStatus = true,
    className = '',
    style
}) => {
    const [activeCategory, setActiveCategory] = useState<EventCategory | 'all'>('all')
    
    const availableEvents = useMemo(() => getAvailableEvents(), [])
    
    const filteredEvents = useMemo(() => {
        if (activeCategory === 'all') return availableEvents
        return getEventsByCategory(activeCategory)
    }, [activeCategory, availableEvents])
    
    const handleEventClick = useCallback((eventType: EventType) => {
        const config = EVENT_CONFIGS[eventType]
        if (config.status === 'available') {
            onEventChange(eventType)
        }
    }, [onEventChange])
    
    const handleCategoryClick = useCallback((category: EventCategory | 'all') => {
        setActiveCategory(category)
    }, [])
    
    // 緊湊模式 - 用於 Modal 標題或小空間
    if (mode === 'compact') {
        return (
            <div className={`event-selector event-selector--compact ${className}`} style={style}>
                <div className="event-buttons">
                    {availableEvents.map((config) => (
                        <button
                            key={config.id}
                            className={`event-btn ${selectedEvent === config.id ? 'active' : ''} ${
                                config.status !== 'available' ? 'disabled' : ''
                            }`}
                            onClick={() => handleEventClick(config.id)}
                            disabled={config.status !== 'available'}
                            title={config.description}
                            style={{
                                borderColor: selectedEvent === config.id ? config.color.primary : 'transparent',
                                backgroundColor: selectedEvent === config.id ? config.color.background : 'transparent'
                            }}
                        >
                            <span className="event-icon">{config.icon}</span>
                            <span className="event-name">{config.shortName}</span>
                        </button>
                    ))}
                </div>
                {showDescription && (
                    <div className="event-description">
                        {EVENT_CONFIGS[selectedEvent].description}
                    </div>
                )}
            </div>
        )
    }
    
    // 卡片模式 - 用於主要選擇界面
    if (mode === 'card') {
        return (
            <div className={`event-selector event-selector--card ${className}`} style={style}>
                {showCategories && (
                    <div className="category-filter">
                        <button
                            className={`category-btn ${activeCategory === 'all' ? 'active' : ''}`}
                            onClick={() => handleCategoryClick('all')}
                        >
                            <span>🎯</span>
                            <span>全部事件</span>
                        </button>
                        {Object.entries(EVENT_CATEGORIES).map(([key, category]) => (
                            <button
                                key={key}
                                className={`category-btn ${activeCategory === key ? 'active' : ''}`}
                                onClick={() => handleCategoryClick(key as EventCategory)}
                            >
                                <span>{category.icon}</span>
                                <span>{category.label}</span>
                            </button>
                        ))}
                    </div>
                )}
                
                <div className="event-cards">
                    {filteredEvents.map((config) => (
                        <div
                            key={config.id}
                            className={`event-card ${selectedEvent === config.id ? 'selected' : ''} ${
                                config.status !== 'available' ? 'disabled' : ''
                            }`}
                            onClick={() => handleEventClick(config.id)}
                            style={{
                                borderColor: selectedEvent === config.id ? config.color.primary : '#444',
                                backgroundColor: selectedEvent === config.id ? config.color.background : 'transparent'
                            }}
                        >
                            <div className="card-header">
                                <span className="card-icon" style={{ color: config.color.primary }}>
                                    {config.icon}
                                </span>
                                <div className="card-title">
                                    <h4>{config.name}</h4>
                                    {showStatus && config.status !== 'available' && (
                                        <span className={`status-badge status-${config.status}`}>
                                            {config.status === 'beta' ? 'Beta' : '即將推出'}
                                        </span>
                                    )}
                                </div>
                            </div>
                            
                            {showDescription && (
                                <div className="card-content">
                                    <p className="card-description">{config.description}</p>
                                    <div className="card-details">
                                        <div className="detail-item">
                                            <span className="detail-label">標準:</span>
                                            <span className="detail-value">{config.standard}</span>
                                        </div>
                                        <div className="detail-item">
                                            <span className="detail-label">類別:</span>
                                            <span className="detail-value">
                                                {EVENT_CATEGORIES[config.category].label}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            <div className="card-footer">
                                <div className="condition-preview">
                                    <div className="condition-item">
                                        <span className="condition-label">進入:</span>
                                        <code className="condition-formula">{config.conditions.enter}</code>
                                    </div>
                                    <div className="condition-item">
                                        <span className="condition-label">離開:</span>
                                        <code className="condition-formula">{config.conditions.leave}</code>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )
    }
    
    // 詳細模式 - 預設模式，用於大多數情況
    return (
        <div className={`event-selector event-selector--detailed ${className}`} style={style}>
            {showCategories && (
                <div className="category-tabs">
                    <button
                        className={`category-tab ${activeCategory === 'all' ? 'active' : ''}`}
                        onClick={() => handleCategoryClick('all')}
                    >
                        全部 ({availableEvents.length})
                    </button>
                    {Object.entries(EVENT_CATEGORIES).map(([key, category]) => {
                        const count = getEventsByCategory(key as EventCategory).length
                        return (
                            <button
                                key={key}
                                className={`category-tab ${activeCategory === key ? 'active' : ''}`}
                                onClick={() => handleCategoryClick(key as EventCategory)}
                                title={category.description}
                            >
                                {category.icon} {category.label} ({count})
                            </button>
                        )
                    })}
                </div>
            )}
            
            <div className="event-list">
                {filteredEvents.map((config) => (
                    <div
                        key={config.id}
                        className={`event-item ${selectedEvent === config.id ? 'selected' : ''} ${
                            config.status !== 'available' ? 'disabled' : ''
                        }`}
                        onClick={() => handleEventClick(config.id)}
                        style={{
                            borderLeftColor: config.color.primary,
                            backgroundColor: selectedEvent === config.id ? config.color.background : 'transparent'
                        }}
                    >
                        <div className="item-header">
                            <span className="item-icon" style={{ color: config.color.primary }}>
                                {config.icon}
                            </span>
                            <div className="item-info">
                                <h4 className="item-title">{config.name}</h4>
                                <p className="item-standard">{config.standard}</p>
                            </div>
                            {showStatus && config.status !== 'available' && (
                                <span className={`status-badge status-${config.status}`}>
                                    {config.status === 'beta' ? 'Beta' : '即將推出'}
                                </span>
                            )}
                        </div>
                        
                        {showDescription && (
                            <div className="item-content">
                                <p className="item-description">{config.description}</p>
                                <div className="item-conditions">
                                    <div className="condition-row">
                                        <span className="condition-type enter">進入:</span>
                                        <code>{config.conditions.enter}</code>
                                    </div>
                                    <div className="condition-row">
                                        <span className="condition-type leave">離開:</span>
                                        <code>{config.conditions.leave}</code>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
})

EventSelector.displayName = 'EventSelector'

export default EventSelector