/**
 * Enhanced Viewer Adapter
 * 
 * 適配 Modal 傳遞的 props 與 Enhanced 組件期望的介面
 * 確保 Enhanced 組件能在現有的 Modal 系統中正常工作
 */

import React from 'react'
import EnhancedA4Viewer from '../charts/EnhancedA4Viewer'
import EnhancedD1Viewer from '../charts/EnhancedD1Viewer'
import EnhancedT1Viewer from '../charts/EnhancedT1Viewer'
import EnhancedD2Viewer from '../charts/EnhancedD2Viewer'

// Modal 傳遞的 props 介面
interface ModalProps {
    onReportLastUpdateToNavbar?: () => void
    reportRefreshHandlerToNavbar?: () => void
    reportIsLoadingToNavbar?: () => void
    currentScene?: string
    isDarkTheme?: boolean
}

// 簡化的適配器組件
export const AdaptedEnhancedA4Viewer: React.FC<ModalProps> = (props) => {
    return <EnhancedA4Viewer className={props.isDarkTheme ? 'dark-theme' : 'light-theme'} />
}

export const AdaptedEnhancedD1Viewer: React.FC<ModalProps> = (props) => {
    return <EnhancedD1Viewer className={props.isDarkTheme ? 'dark-theme' : 'light-theme'} />
}

export const AdaptedEnhancedD2Viewer: React.FC<ModalProps> = (props) => {
    return <EnhancedD2Viewer className={props.isDarkTheme ? 'dark-theme' : 'light-theme'} />
}

export const AdaptedEnhancedT1Viewer: React.FC<ModalProps> = (props) => {
    return <EnhancedT1Viewer className={props.isDarkTheme ? 'dark-theme' : 'light-theme'} />
}