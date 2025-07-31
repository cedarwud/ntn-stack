/**
 * D2DataProcessingDemo - LEO 衛星換手研究頁面
 * 
 * 整合版本：專注於 LEO satellite handover 研究
 * - 基於真實的 3GPP TS 38.331 標準
 * - D2 和 A3 事件監控
 * - 為與立體圖整合做準備
 */

import React from 'react'
import LEOSatelliteHandoverMonitor from '../components/handover/LEOSatelliteHandoverMonitor'

const D2DataProcessingDemo: React.FC = () => {
    return (
        <div style={{
            height: '100vh',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
        }}>
            <div style={{
                flex: 1,
                overflow: 'auto',
                padding: 0
            }}>
                <LEOSatelliteHandoverMonitor />
            </div>
        </div>
    )
}

export default D2DataProcessingDemo