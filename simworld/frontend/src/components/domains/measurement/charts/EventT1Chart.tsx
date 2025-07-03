/**
 * Event T1 Chart Component
 * 主要的 Event T1 圖表組件，包含動畫控制和參數調整
 * 基於 3GPP TS 38.331 Section 5.5.4.16 規範
 */

import React, { useState, useCallback, useMemo } from 'react';
import PureT1Chart from './PureT1Chart';
import type { EventT1Params } from '../types';
import './EventT1Chart.scss'; // Import the new SCSS file

interface EventT1ChartProps {
    isDarkTheme?: boolean;
    onThemeToggle?: () => void;
    initialParams?: Partial<EventT1Params>;
    showControls?: boolean;
    width?: number;
    height?: number;
}

export const EventT1Chart: React.FC<EventT1ChartProps> = React.memo(
    ({
        isDarkTheme = true,
        onThemeToggle,
        initialParams = {},
        showControls = true,
        width = 800,
        height = 600,
    }) => {
        // Event T1 參數狀態
        const [params, setParams] = useState<EventT1Params>(() => ({
            Thresh1: initialParams.Thresh1 ?? 5000, // 5 seconds default
            Duration: initialParams.Duration ?? 10000, // 10 seconds default
            Hys: initialParams.Hys ?? 0, // Not applicable for T1
            timeToTrigger: initialParams.timeToTrigger ?? 0, // T1 has built-in time logic
            reportAmount: initialParams.reportAmount ?? 1,
            reportInterval: initialParams.reportInterval ?? 1000,
            reportOnLeave: initialParams.reportOnLeave ?? true,
        }));

        const [showThresholdLines, setShowThresholdLines] = useState(true);

        // 穩定的參數更新回調
        const updateParam = useCallback(
            (key: keyof EventT1Params, value: unknown) => {
                setParams((prev) => ({
                    ...prev,
                    [key]: value,
                }));
            },
            []
        );

        // 穩定的圖表 props
        const chartProps = useMemo(
            () => ({
                threshold: params.Thresh1,
                duration: params.Duration,
                showThresholdLines,
                isDarkTheme,
                onThemeToggle,
            }),
            [params.Thresh1, params.Duration, showThresholdLines, isDarkTheme, onThemeToggle]
        );

        return (
            <div className="event-t1-chart" style={{ width, height }}>
                <div className="chart-container" style={{ height: height - 80 }}>
                    <PureT1Chart {...chartProps} width={width} height={height - 80} />
                </div>

                <div className="event-info">
                    <div className="event-params">
                        <h4>Event T1 Parameters</h4>
                        <div className="param-grid">
                            <span>Threshold: {params.Thresh1} ms</span>
                            <span>Duration: {params.Duration} ms</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
);

EventT1Chart.displayName = 'EventT1Chart'

export default EventT1Chart
