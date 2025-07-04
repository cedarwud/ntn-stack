/**
 * 重構後的 Event D2 Viewer 組件
 * 基於新的共享架構，大幅簡化代碼結構
 * Event D2: 服務基站距離變化事件
 */

import React from 'react'
import { ViewerProps } from '../../../../types/viewer'
import { BaseEventViewer } from '../shared'
import { useEventD2Logic } from '../shared/hooks/useEventD2Logic'
import PureD2ChartRefactored from './PureD2ChartRefactored'

// 擴展 ViewerProps 以支援事件選擇
interface EventD2ViewerRefactoredProps extends ViewerProps {
    selectedEvent?: string
    onEventChange?: (event: string) => void
    isDarkTheme?: boolean
}

const EventD2ViewerRefactored: React.FC<EventD2ViewerRefactoredProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    selectedEvent = 'D2',
    onEventChange,
    isDarkTheme: externalIsDarkTheme,
}) => {
    // 使用事件特定的邏輯 Hook
    const eventLogic = useEventD2Logic()

    // 解說內容生成器
    const narrationGenerator = (params: typeof eventLogic.params, animationState: typeof eventLogic.animationState) => {
        return eventLogic.createNarrationContent(animationState.currentTime)
    }

    return (
        <BaseEventViewer
            eventType="D2"
            params={eventLogic.params}
            onParamsChange={eventLogic.setParams}
            chartComponent={PureD2ChartRefactored}
            narrationGenerator={narrationGenerator}
            className="event-d2-viewer-refactored"
            
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

export default EventD2ViewerRefactored