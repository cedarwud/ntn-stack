/**
 * Enhanced Viewer Adapter
 *
 * 適配 Modal 傳遞的 props 與 Enhanced 組件期望的介面
 * 確保 Enhanced 組件能在現有的 Modal 系統中正常工作
 * 
 * 注意：D2 事件已移除，統一由 EventD2Viewer 通過 📊 D2 事件監控 按鈕訪問
 */

import React from 'react'
// 只需要 A4 事件組件用於 MeasurementEventsModal
import EventA4Viewer from '../charts/EventA4Viewer'

// Modal 傳遞的 props 介面
interface ModalProps {
    onReportLastUpdateToNavbar?: () => void
    reportRefreshHandlerToNavbar?: () => void
    reportIsLoadingToNavbar?: () => void
    currentScene?: string
    isDarkTheme?: boolean
}

// A4 事件適配器 - 用於 MeasurementEventsModal 中的 A4 信號切換事件
export const AdaptedEnhancedA4Viewer: React.FC<ModalProps> = (props) => {
    return (
        <EventA4Viewer
            onReportLastUpdateToNavbar={props.onReportLastUpdateToNavbar}
            reportRefreshHandlerToNavbar={props.reportRefreshHandlerToNavbar}
            reportIsLoadingToNavbar={props.reportIsLoadingToNavbar}
            isDarkTheme={props.isDarkTheme}
        />
    )
}

// 移除 AdaptedEnhancedD2Viewer - D2 事件統一由 EventD2Viewer 處理
