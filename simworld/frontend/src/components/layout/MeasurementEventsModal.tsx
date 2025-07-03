/**
 * Measurement Events Modal
 * 直接顯示測量事件圖表，內建事件類型選擇器
 * 優化版本：避免不必要的重新渲染
 */

import React, { useState, useCallback, useMemo } from 'react'
import EventA4Viewer from '../domains/measurement/charts/EventA4Viewer'
import EventD1Viewer from '../domains/measurement/charts/EventD1Viewer'
import './MeasurementEventsModal.scss'

interface MeasurementEventsModalProps {
    isOpen: boolean
    onClose: () => void
}

type EventType = 'A4' | 'D1' | 'D2' | 'T1'

interface EventConfig {
    id: EventType
    name: string
    description: string
    status: 'available' | 'coming-soon'
    ViewerComponent?: React.FC<any>
}

// 穩定的事件配置 - 移到組件外部避免重新創建
const eventConfigs: EventConfig[] = [
    {
        id: 'A4',
        name: 'Event A4',
        description: 'Neighbour becomes better than threshold',
        status: 'available',
        ViewerComponent: EventA4Viewer,
    },
    {
        id: 'D1',
        name: 'Event D1',
        description: 'Distance between UE and reference locations',
        status: 'available',
        ViewerComponent: EventD1Viewer,
    },
    {
        id: 'D2',
        name: 'Event D2',
        description: 'Distance between UE and moving reference locations',
        status: 'coming-soon',
    },
    {
        id: 'T1',
        name: 'CondEvent T1',
        description: 'Time measured at UE within duration from threshold',
        status: 'coming-soon',
    },
]

const MeasurementEventsModal: React.FC<MeasurementEventsModalProps> =
    React.memo(({ isOpen, onClose }) => {
        const [isDarkTheme, setIsDarkTheme] = useState(true)
        const [selectedEvent, setSelectedEvent] = useState<EventType>('A4')

        const toggleTheme = useCallback(() => {
            setIsDarkTheme(!isDarkTheme)
        }, [isDarkTheme])

        const handleEventChange = useCallback((eventType: EventType) => {
            const eventConfig = eventConfigs.find(
                (config) => config.id === eventType
            )
            if (eventConfig?.status === 'available') {
                setSelectedEvent(eventType)
            }
        }, [])

        const selectedEventConfig = useMemo(
            () => eventConfigs.find((config) => config.id === selectedEvent),
            [selectedEvent]
        )

        // 穩定的模態框標題配置 - 用事件選擇器替代標題
        const modalTitleConfig = useMemo(
            () => ({
                base: '', // 空標題，我們將用自定義的事件選擇器
                loading: '正在載入測量事件數據...',
                hoverRefresh: '',
            }),
            []
        )

        // 穩定的回調函數，避免每次渲染都重新創建
        const stableOnReportLastUpdate = useCallback(() => {}, [])
        const stableReportRefreshHandler = useCallback(() => {}, [])
        const stableReportIsLoading = useCallback(() => {}, [])

        // 空的刷新函數
        const handleRefresh = useCallback(() => {
            // 測量事件模態框目前不需要刷新功能
        }, [])

        // 當前事件的 Viewer 組件
        const CurrentViewer = selectedEventConfig?.ViewerComponent

        // 準備穩定的傳遞給 CurrentViewer 的 props
        const currentViewerProps = useMemo(
            () => ({
                onReportLastUpdateToNavbar: stableOnReportLastUpdate,
                reportRefreshHandlerToNavbar: stableReportRefreshHandler,
                reportIsLoadingToNavbar: stableReportIsLoading,
                currentScene: 'default',
                isDarkTheme: isDarkTheme,
            }),
            [
                stableOnReportLastUpdate,
                stableReportRefreshHandler,
                stableReportIsLoading,
                isDarkTheme,
            ]
        )

        // 即將推出的占位符組件
        const comingSoonPlaceholder = useMemo(
            () => (
                <div className="coming-soon-placeholder">
                    <h3>{selectedEventConfig?.name}</h3>
                    <p>此事件類型即將推出</p>
                    <div className="formula-preview">
                        {selectedEvent === 'D2' && (
                            <p>
                                <strong>移動參考:</strong>{' '}
                                基於衛星星曆的動態位置
                            </p>
                        )}
                        {selectedEvent === 'T1' && (
                            <p>
                                <strong>時間條件:</strong> Mt &gt; Thresh1
                                (持續時間)
                            </p>
                        )}
                    </div>
                </div>
            ),
            [selectedEvent, selectedEventConfig?.name]
        )

        // 直接渲染圖表組件
        const viewerComponent = (
            <div className="measurement-events-viewer">
                <div className="event-chart-container">
                    {CurrentViewer ? (
                        <CurrentViewer
                            {...currentViewerProps}
                            key={`viewer-${selectedEvent}`}
                        />
                    ) : (
                        comingSoonPlaceholder
                    )}
                </div>
            </div>
        )

        // 如果 modal 未打開，不渲染任何內容
        if (!isOpen) {
            return null
        }

        return (
            <div className="modal-backdrop" onClick={onClose}>
                <div
                    className={`constellation-modal measurement-events-modal`}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div
                        className="modal-header"
                        style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '15px 20px',
                        }}
                    >
                        <div style={{ flex: 1 }}></div>
                        {/* 事件選擇器作為標題 */}
                        <div
                            className="event-selector-title"
                            style={{ flex: 1, textAlign: 'center' }}
                        >
                            <div className="event-buttons-title">
                                {eventConfigs.map((config) => (
                                    <button
                                        key={config.id}
                                        className={`event-btn-title ${
                                            selectedEvent === config.id
                                                ? 'active'
                                                : ''
                                        } ${
                                            config.status === 'coming-soon'
                                                ? 'disabled'
                                                : ''
                                        }`}
                                        onClick={() =>
                                            handleEventChange(config.id)
                                        }
                                        disabled={
                                            config.status === 'coming-soon'
                                        }
                                        title={config.description}
                                    >
                                        {config.name}
                                    </button>
                                ))}
                            </div>
                            <div className="event-description">
                                {selectedEventConfig?.description}
                            </div>
                        </div>
                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px',
                                flex: 1,
                                justifyContent: 'flex-end',
                            }}
                        >
                            {/* 主題切換按鈕 */}
                            <div
                                onClick={toggleTheme}
                                style={{
                                    width: '40px',
                                    height: '20px',
                                    backgroundColor: '#444',
                                    borderRadius: '10px',
                                    position: 'relative',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    padding: '2px',
                                    transition: 'background-color 0.3s ease',
                                }}
                            >
                                <div
                                    style={{
                                        width: '16px',
                                        height: '16px',
                                        backgroundColor: '#666',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '10px',
                                        transition: 'transform 0.3s ease',
                                        transform: isDarkTheme
                                            ? 'translateX(0)'
                                            : 'translateX(18px)',
                                    }}
                                >
                                    {isDarkTheme ? '🌙' : '☀️'}
                                </div>
                            </div>
                            {/* 關閉按鈕 */}
                            <button
                                onClick={onClose}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'white',
                                    fontSize: '1.5rem',
                                    cursor: 'pointer',
                                    padding: '0 5px',
                                    lineHeight: 1,
                                    opacity: 0.7,
                                    transition: 'opacity 0.3s',
                                    marginLeft: '15px',
                                }}
                                onMouseEnter={(e) =>
                                    ((
                                        e.target as HTMLButtonElement
                                    ).style.opacity = '1')
                                }
                                onMouseLeave={(e) =>
                                    ((
                                        e.target as HTMLButtonElement
                                    ).style.opacity = '0.7')
                                }
                            >
                                ×
                            </button>
                        </div>
                    </div>
                    <div className="modal-content">{viewerComponent}</div>
                </div>
            </div>
        )
    })

MeasurementEventsModal.displayName = 'MeasurementEventsModal'

export default MeasurementEventsModal
