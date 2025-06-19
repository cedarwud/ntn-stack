import React, { useEffect } from 'react'
import { ViewerProps } from '../../types/viewer'
import FourWayHandoverComparisonDashboard from '../dashboard/FourWayHandoverComparisonDashboard'

// Navbar 模態框適配器組件 - 四種換手方案對比
const FourWayHandoverComparisonViewer: React.FC<ViewerProps> = ({
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
        }, 1200) // 稍長的載入時間，因為需要獲取真實數據
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
            }, 800)
        }

        reportRefreshHandlerToNavbar(refreshHandler)
    }, [onReportLastUpdateToNavbar, reportRefreshHandlerToNavbar, reportIsLoadingToNavbar])

    return (
        <div style={{ 
            width: '100%', 
            height: '700px', 
            position: 'relative', 
            overflow: 'auto',
            padding: '0',
            background: 'radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%)'
        }}>
            <FourWayHandoverComparisonDashboard enabled={true} />
        </div>
    )
}

export default FourWayHandoverComparisonViewer