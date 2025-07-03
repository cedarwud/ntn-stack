/**
 * Event D2 Chart Component
 * 移動參考位置距離事件圖表包裝器，用於基本展示
 * 基於 EventD1Chart.tsx 修改以支援移動參考位置
 */

import React from 'react'
import PureD2Chart from './PureD2Chart'

interface EventD2ChartProps {
    thresh1?: number // 距離門檻1（移動參考位置）
    thresh2?: number // 距離門檻2（固定參考位置）
    hysteresis?: number // 位置遲滯參數（米）
    showThresholdLines?: boolean
    isDarkTheme?: boolean
}

export const EventD2Chart: React.FC<EventD2ChartProps> = React.memo(
    ({
        thresh1 = 550000,
        thresh2 = 6000,
        hysteresis = 20,
        showThresholdLines = true,
        isDarkTheme = true,
    }) => {
        return (
            <div
                style={{
                    width: '100%',
                    height: '100%',
                    padding: '20px',
                    backgroundColor: isDarkTheme ? '#1a1a1a' : '#ffffff',
                    borderRadius: '8px',
                    border: isDarkTheme ? '1px solid #333' : '1px solid #ddd',
                }}
            >
                <PureD2Chart
                    thresh1={thresh1}
                    thresh2={thresh2}
                    hysteresis={hysteresis}
                    showThresholdLines={showThresholdLines}
                    isDarkTheme={isDarkTheme}
                />
            </div>
        )
    }
)

EventD2Chart.displayName = 'EventD2Chart'

export default EventD2Chart
