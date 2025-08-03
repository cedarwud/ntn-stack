/**
 * Enhanced Viewer Adapter
 *
 * 適配 Modal 傳遞的 props 與 Enhanced 組件期望的介面
 * 確保 Enhanced 組件能在現有的 Modal 系統中正常工作
 */

import React from 'react'
// 🔧 臨時切換到舊版工作正常的實現
import EventA4Viewer from '../charts/EventA4Viewer'
import EventD2Viewer from '../charts/EventD2Viewer'

// Modal 傳遞的 props 介面
interface ModalProps {
    onReportLastUpdateToNavbar?: () => void
    reportRefreshHandlerToNavbar?: () => void
    reportIsLoadingToNavbar?: () => void
    currentScene?: string
    isDarkTheme?: boolean
}

// 🔧 切換到舊版工作正常的組件
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

export const AdaptedEnhancedD2Viewer: React.FC<ModalProps> = (props) => {
    return (
        <EventD2Viewer
            onReportLastUpdateToNavbar={props.onReportLastUpdateToNavbar}
            reportRefreshHandlerToNavbar={props.reportRefreshHandlerToNavbar}
            reportIsLoadingToNavbar={props.reportIsLoadingToNavbar}
            isDarkTheme={props.isDarkTheme}
        />
    )
}
