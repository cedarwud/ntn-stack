/**
 * Measurement Events Modal
 * 直接顯示測量事件圖表，內建事件類型選擇器
 * 優化版本：避免不必要的重新渲染
 */

import React, { useState, useCallback, useMemo, useRef } from 'react'
import ViewerModal from '../shared/ui/layout/ViewerModal'
import EventA4Viewer from '../domains/measurement/charts/EventA4Viewer'
import { ViewerProps } from '../../types/viewer'
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
        status: 'coming-soon',
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

// 創建一個包含事件選擇器的 Viewer 組件
interface MeasurementEventsViewerProps extends ViewerProps {
    isDarkTheme?: boolean
}

const MeasurementEventsViewer: React.FC<MeasurementEventsViewerProps> =
    React.memo((viewerProps) => {
        const [selectedEvent, setSelectedEvent] = useState<EventType>('A4')

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

        // 穩定的 ViewerComponent 渲染
        const CurrentViewer = selectedEventConfig?.ViewerComponent

        // 使用 useRef 來穩定回調函數
        const stableOnReportLastUpdate = useRef(
            viewerProps.onReportLastUpdateToNavbar || (() => {})
        )
        const stableReportRefreshHandler = useRef(
            viewerProps.reportRefreshHandlerToNavbar || (() => {})
        )
        const stableReportIsLoading = useRef(
            viewerProps.reportIsLoadingToNavbar || (() => {})
        )

        // 準備穩定的傳遞給 CurrentViewer 的 props
        const currentViewerProps = useMemo(
            () => ({
                onReportLastUpdateToNavbar: stableOnReportLastUpdate.current,
                reportRefreshHandlerToNavbar:
                    stableReportRefreshHandler.current,
                reportIsLoadingToNavbar: stableReportIsLoading.current,
                currentScene: viewerProps.currentScene || 'default',
                selectedEvent: selectedEvent,
                onEventChange: handleEventChange,
                isDarkTheme: viewerProps.isDarkTheme,
            }),
            [
                viewerProps.currentScene,
                selectedEvent,
                handleEventChange,
                viewerProps.isDarkTheme, // 只保留真正會變化的
            ]
        )

        // 即將推出的占位符組件 - 使用 useMemo 穩定化
        const comingSoonPlaceholder = useMemo(
            () => (
                <div className="coming-soon-placeholder">
                    <h3>{selectedEventConfig?.name}</h3>
                    <p>此事件類型即將推出</p>
                    <div className="formula-preview">
                        {selectedEvent === 'D1' && (
                            <p>
                                <strong>距離條件:</strong> Ml1 &gt; Thresh1 AND
                                Ml2 &lt; Thresh2
                            </p>
                        )}
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

        return (
            <div className="measurement-events-viewer">
                {/* 圖表顯示區域 */}
                <div className="event-chart-container">
                    {CurrentViewer ? (
                        <CurrentViewer
                            {...currentViewerProps}
                            key={`viewer-${selectedEvent}`} // 添加穩定的 key
                        />
                    ) : (
                        comingSoonPlaceholder
                    )}
                </div>
            </div>
        )
    })

MeasurementEventsViewer.displayName = 'MeasurementEventsViewer'

const MeasurementEventsModal: React.FC<MeasurementEventsModalProps> =
    React.memo(({ isOpen, onClose }) => {
        const [isDarkTheme, setIsDarkTheme] = useState(true)

        const toggleTheme = useCallback(() => {
            setIsDarkTheme(!isDarkTheme)
        }, [isDarkTheme])

        // 穩定的模態框標題配置
        const modalTitleConfig = useMemo(
            () => ({
                base: '3GPP TS 38.331 測量事件',
                loading: '正在載入測量事件數據...',
                hoverRefresh: '重新載入測量事件',
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

        // 直接渲染組件，使用穩定的 key 和回調函數
        const viewerComponent = (
            <MeasurementEventsViewer
                key="measurement-events-viewer-stable" // 穩定的 key
                onReportLastUpdateToNavbar={stableOnReportLastUpdate}
                reportRefreshHandlerToNavbar={stableReportRefreshHandler}
                reportIsLoadingToNavbar={stableReportIsLoading}
                currentScene="default"
                isDarkTheme={isDarkTheme}
            />
        )

        return (
            <ViewerModal
                isOpen={isOpen}
                onClose={onClose}
                modalTitleConfig={modalTitleConfig}
                lastUpdateTimestamp=""
                isLoading={false}
                onRefresh={handleRefresh}
                viewerComponent={viewerComponent}
                className="measurement-events-modal"
                isDarkTheme={isDarkTheme}
                onThemeToggle={toggleTheme}
            />
        )
    })

MeasurementEventsModal.displayName = 'MeasurementEventsModal'

export default MeasurementEventsModal
