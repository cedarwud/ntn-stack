/**
 * 重構後的 Event A4 Viewer 組件
 * 基於新的共享架構，大幅簡化代碼結構
 * 作為其他事件遷移的範本
 */

import React from 'react'
import { ViewerProps } from '../../../../types/viewer'
import { BaseEventViewer } from '../shared'
import { useEventA4Logic } from '../shared/hooks/useEventA4Logic'
import PureA4ChartRefactored from './PureA4ChartRefactored'

// 擴展 ViewerProps 以支援事件選擇
interface EventA4ViewerRefactoredProps extends ViewerProps {
    selectedEvent?: string
    onEventChange?: (event: string) => void
    isDarkTheme?: boolean
}

const EventA4ViewerRefactored: React.FC<EventA4ViewerRefactoredProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    selectedEvent = 'A4',
    onEventChange,
    isDarkTheme: externalIsDarkTheme,
}) => {
    // 使用事件特定的邏輯 Hook
    const eventLogic = useEventA4Logic()

    // 解說內容生成器
    const narrationGenerator = (params: typeof eventLogic.params, animationState: typeof eventLogic.animationState) => {
        return eventLogic.createNarrationContent(animationState.currentTime)
    }

    return (
        <BaseEventViewer
            eventType="A4"
            params={eventLogic.params}
            onParamsChange={eventLogic.setParams}
            chartComponent={PureA4ChartRefactored}
            narrationGenerator={narrationGenerator}
            className="event-a4-viewer-refactored"
            
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

export default EventA4ViewerRefactored