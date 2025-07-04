/**
 * Event Management System Test
 * 測試統一的事件導航系統和配置管理
 */

import React, { useState, useCallback } from 'react'
import { EventSelector } from '../components/domains/measurement/components/EventSelector'
import { EventConfigPanel } from '../components/domains/measurement/components/EventConfigPanel'
import type { EventType } from '../components/domains/measurement/types'

export const EventManagementTest: React.FC = () => {
    const [selectedEvent, setSelectedEvent] = useState<EventType>('A4')
    const [mode, setMode] = useState<'compact' | 'detailed' | 'card'>('detailed')
    const [showConfigPanel, setShowConfigPanel] = useState(false)
    
    const handleEventChange = useCallback((eventType: EventType) => {
        setSelectedEvent(eventType)
    }, [])
    
    const handleParamsChange = useCallback((eventType: EventType, params: Record<string, unknown>) => {
        console.log('Parameters changed for', eventType, ':', params)
    }, [])
    
    return (
        <div style={{ padding: '20px', backgroundColor: '#1a1a1a', minHeight: '100vh', color: 'white' }}>
            <h1 style={{ marginBottom: '30px', color: '#FFD93D' }}>
                🚀 Phase 4: 統一事件導航系統測試
            </h1>
            
            <div style={{ marginBottom: '30px' }}>
                <h2 style={{ color: '#4A90E2', marginBottom: '20px' }}>
                    📡 EventSelector 組件測試
                </h2>
                
                {/* 模式切換 */}
                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ color: '#ccc', marginBottom: '10px' }}>顯示模式：</h3>
                    <div style={{ display: 'flex', gap: '10px' }}>
                        {(['compact', 'detailed', 'card'] as const).map(m => (
                            <button
                                key={m}
                                onClick={() => setMode(m)}
                                style={{
                                    padding: '8px 16px',
                                    border: mode === m ? '2px solid #4A90E2' : '1px solid #444',
                                    borderRadius: '6px',
                                    background: mode === m ? 'rgba(74, 144, 226, 0.2)' : 'transparent',
                                    color: 'white',
                                    cursor: 'pointer'
                                }}
                            >
                                {m === 'compact' ? '🔸 緊湊' : 
                                 m === 'detailed' ? '📋 詳細' : 
                                 '🃏 卡片'}
                            </button>
                        ))}
                    </div>
                </div>
                
                {/* EventSelector 展示 */}
                <div style={{ 
                    border: '1px solid #333', 
                    borderRadius: '8px', 
                    padding: '20px',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)'
                }}>
                    <EventSelector
                        selectedEvent={selectedEvent}
                        onEventChange={handleEventChange}
                        mode={mode}
                        showCategories={true}
                        showDescription={true}
                        showStatus={true}
                    />
                </div>
            </div>
            
            <div style={{ marginBottom: '30px' }}>
                <h2 style={{ color: '#50C878', marginBottom: '20px' }}>
                    ⚙️ EventConfigPanel 組件測試
                </h2>
                
                <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                    <button
                        onClick={() => setShowConfigPanel(!showConfigPanel)}
                        style={{
                            padding: '10px 20px',
                            border: '1px solid #50C878',
                            borderRadius: '8px',
                            background: showConfigPanel ? 'rgba(80, 200, 120, 0.2)' : 'transparent',
                            color: '#50C878',
                            cursor: 'pointer'
                        }}
                    >
                        {showConfigPanel ? '🔽 隱藏配置面板' : '🔼 顯示配置面板'}
                    </button>
                </div>
                
                {showConfigPanel && (
                    <div style={{ 
                        border: '1px solid #333', 
                        borderRadius: '8px', 
                        padding: '20px',
                        backgroundColor: 'rgba(255, 255, 255, 0.02)'
                    }}>
                        <EventConfigPanel
                            selectedEvent={selectedEvent}
                            onEventChange={handleEventChange}
                            onParamsChange={handleParamsChange}
                            showPresets={true}
                            showExport={true}
                        />
                    </div>
                )}
            </div>
            
            <div style={{ marginBottom: '30px' }}>
                <h2 style={{ color: '#FF6B35', marginBottom: '20px' }}>
                    🎯 當前狀態
                </h2>
                
                <div style={{ 
                    border: '1px solid #333', 
                    borderRadius: '8px', 
                    padding: '20px',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    fontFamily: 'monospace'
                }}>
                    <div><strong>選擇的事件:</strong> {selectedEvent}</div>
                    <div><strong>顯示模式:</strong> {mode}</div>
                    <div><strong>配置面板:</strong> {showConfigPanel ? '已開啟' : '已關閉'}</div>
                </div>
            </div>
            
            <div>
                <h2 style={{ color: '#9B59B6', marginBottom: '20px' }}>
                    ✅ 測試重點
                </h2>
                
                <div style={{ 
                    border: '1px solid #333', 
                    borderRadius: '8px', 
                    padding: '20px',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)'
                }}>
                    <h3 style={{ color: '#ccc', marginBottom: '15px' }}>EventSelector 功能：</h3>
                    <ul style={{ color: '#aaa', lineHeight: '1.6' }}>
                        <li>✓ 三種顯示模式切換 (compact, detailed, card)</li>
                        <li>✓ 事件類型選擇和切換</li>
                        <li>✓ 分類篩選功能</li>
                        <li>✓ 3GPP 規範條件顯示</li>
                        <li>✓ 響應式設計</li>
                    </ul>
                    
                    <h3 style={{ color: '#ccc', marginBottom: '15px', marginTop: '20px' }}>EventConfigPanel 功能：</h3>
                    <ul style={{ color: '#aaa', lineHeight: '1.6' }}>
                        <li>✓ 統一的事件配置管理</li>
                        <li>✓ 預設配置選擇 (default, urban, rural 等)</li>
                        <li>✓ 參數即時編輯</li>
                        <li>✓ 配置匯入/匯出</li>
                        <li>✓ 配置預覽和驗證</li>
                    </ul>
                    
                    <h3 style={{ color: '#ccc', marginBottom: '15px', marginTop: '20px' }}>整合效果：</h3>
                    <ul style={{ color: '#aaa', lineHeight: '1.6' }}>
                        <li>✓ 統一的事件配置管理</li>
                        <li>✓ 模組化和可重用設計</li>
                        <li>✓ 類型安全的參數管理</li>
                        <li>✓ 性能優化 (React.memo, useMemo)</li>
                    </ul>
                </div>
            </div>
        </div>
    )
}

export default EventManagementTest