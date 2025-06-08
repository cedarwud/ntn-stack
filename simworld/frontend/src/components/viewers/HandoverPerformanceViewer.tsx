import React, { useEffect } from 'react'
import { ViewerProps } from '../../types/viewer'
import HandoverPerformanceDashboard from '../dashboard/HandoverPerformanceDashboard'

// Navbar 模態框適配器組件
const HandoverPerformanceViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    currentScene,
}) => {
    // 初始化
    useEffect(() => {
        reportIsLoadingToNavbar(true)
        
        // 模擬數據載入
        setTimeout(() => {
            reportIsLoadingToNavbar(false)
            
            if (onReportLastUpdateToNavbar) {
                onReportLastUpdateToNavbar(new Date().toLocaleTimeString())
            }
        }, 800)
    }, [currentScene, onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

    // 設置刷新處理器
    useEffect(() => {
        const refreshHandler = () => {
            reportIsLoadingToNavbar(true)
            setTimeout(() => {
                reportIsLoadingToNavbar(false)
                if (onReportLastUpdateToNavbar) {
                    onReportLastUpdateToNavbar(new Date().toLocaleTimeString())
                }
            }, 600)
        }

        reportRefreshHandlerToNavbar(refreshHandler)
    }, [onReportLastUpdateToNavbar, reportRefreshHandlerToNavbar, reportIsLoadingToNavbar])

    return (
        <div style={{ width: '100%', height: '600px', position: 'relative', overflow: 'auto' }}>
            <HandoverPerformanceDashboard enabled={true} />
        </div>
    )
}

export default HandoverPerformanceViewer