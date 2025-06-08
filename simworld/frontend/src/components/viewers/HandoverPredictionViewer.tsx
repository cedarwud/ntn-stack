import React, { useEffect, useState } from 'react'
import { ViewerProps } from '../../types/viewer'
import HandoverPredictionVisualization from './HandoverPredictionVisualization'

// Navbar 模態框適配器組件
const HandoverPredictionViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    currentScene,
}) => {
    const [devices, setDevices] = useState<any[]>([])
    const [satellites, setSatellites] = useState<any[]>([])

    // 模擬設備數據
    useEffect(() => {
        reportIsLoadingToNavbar(true)
        
        // 模擬數據載入
        setTimeout(() => {
            const mockDevices = [
                {
                    id: 1,
                    name: 'UAV-001',
                    role: 'receiver',
                    position_x: 10,
                    position_y: 20,
                    position_z: 15
                },
                {
                    id: 2,
                    name: 'UAV-002', 
                    role: 'receiver',
                    position_x: -15,
                    position_y: 10,
                    position_z: 12
                }
            ]

            const mockSatellites = [
                { id: 'sat_001', name: 'OneWeb-1234' },
                { id: 'sat_002', name: 'OneWeb-5678' },
                { id: 'sat_003', name: 'OneWeb-9012' }
            ]

            setDevices(mockDevices)
            setSatellites(mockSatellites)
            reportIsLoadingToNavbar(false)
            
            if (onReportLastUpdateToNavbar) {
                onReportLastUpdateToNavbar(new Date().toLocaleTimeString())
            }
        }, 1000)
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
        <div style={{ width: '100%', height: '600px', position: 'relative', background: '#0a0a0a' }}>
            <HandoverPredictionVisualization
                devices={devices}
                enabled={true}
                satellites={satellites}
            />
        </div>
    )
}

export default HandoverPredictionViewer