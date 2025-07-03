/**
 * Event D1 Chart Component
 * 簡化的 D1 圖表包裝器，用於基本展示
 */

import React from 'react'
import PureD1Chart from './PureD1Chart'

interface EventD1ChartProps {
    width?: number
    height?: number
    thresh1?: number
    thresh2?: number
    hysteresis?: number
    showThresholdLines?: boolean
    isDarkTheme?: boolean
}

export const EventD1Chart: React.FC<EventD1ChartProps> = React.memo(
    ({
        width = 800,
        height = 400,
        thresh1 = 400,
        thresh2 = 250,
        hysteresis = 20,
        showThresholdLines = true,
        isDarkTheme = true,
    }) => {
        return (
            <div
                style={{
                    width: width,
                    height: height,
                    padding: '20px',
                    backgroundColor: isDarkTheme ? '#1a1a1a' : '#ffffff',
                    borderRadius: '8px',
                    border: isDarkTheme ? '1px solid #333' : '1px solid #ddd',
                }}
            >
                <PureD1Chart
                    width={width}
                    height={height}
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

EventD1Chart.displayName = 'EventD1Chart'

export default EventD1Chart