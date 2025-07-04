/**
 * 重構後的 Event T1 Viewer 組件
 * 基於新的共享架構，大幅簡化代碼結構
 * Event T1: 時間相關測量事件
 */

import React from 'react'
import { ViewerProps } from '../../../../types/viewer'
import { BaseEventViewer } from '../shared'
import { useEventT1Logic } from '../shared/hooks/useEventT1Logic'
import PureT1ChartRefactored from './PureT1ChartRefactored'

// 擴展 ViewerProps 以支援事件選擇
interface EventT1ViewerRefactoredProps extends ViewerProps {
    selectedEvent?: string
    onEventChange?: (event: string) => void
    isDarkTheme?: boolean
}

const EventT1ViewerRefactored: React.FC<EventT1ViewerRefactoredProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    selectedEvent = 'T1',
    onEventChange,
    isDarkTheme: externalIsDarkTheme,
}) => {
    // 使用事件特定的邏輯 Hook
    const eventLogic = useEventT1Logic()

    // 解說內容生成器
    const narrationGenerator = (params: typeof eventLogic.params, animationState: typeof eventLogic.animationState) => {
        return eventLogic.createNarrationContent(animationState.currentTime)
    }

    return (
        <BaseEventViewer
            eventType="T1"
            params={eventLogic.params}
            onParamsChange={eventLogic.setParams}
            chartComponent={PureT1ChartRefactored}
            narrationGenerator={narrationGenerator}
            className="event-t1-viewer-refactored"
            
            // ViewerProps 相容性
            onReportLastUpdateToNavbar={onReportLastUpdateToNavbar}
            reportRefreshHandlerToNavbar={reportRefreshHandlerToNavbar}
            reportIsLoadingToNavbar={reportIsLoadingToNavbar}
            
            // 事件選擇器支持
            selectedEvent={selectedEvent}
            onEventChange={onEventChange}
            showEventSelector={!!onEventChange}
            availableEvents={['A4', 'D1', 'D2', 'T1']}
            
            // 主題支持
            isDarkTheme={externalIsDarkTheme ?? eventLogic.themeState.isDarkTheme}
        />
    )
}

export default EventT1ViewerRefactored