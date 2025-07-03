/**
 * Pure D1 Test Component
 * 用於測試 Event D1 圖表的基本功能
 */

import React, { useState } from 'react'
import PureD1Chart from './PureD1Chart'
import './EventA4Chart.scss'

export const PureD1Test: React.FC = () => {
    const [thresh1, setThresh1] = useState(400)
    const [thresh2, setThresh2] = useState(250)
    const [hysteresis, setHysteresis] = useState(20)
    const [showThresholdLines, setShowThresholdLines] = useState(true)
    const [isDarkTheme, setIsDarkTheme] = useState(true)

    return (
        <div className="event-chart-test">
            <h2>Event D1 測試</h2>
            
            <div className="test-controls">
                <div className="control-group">
                    <label>
                        Thresh1 (參考點1門檻): {thresh1}m
                        <input
                            type="range"
                            min="200"
                            max="800"
                            step="10"
                            value={thresh1}
                            onChange={(e) => setThresh1(Number(e.target.value))}
                        />
                    </label>
                </div>
                
                <div className="control-group">
                    <label>
                        Thresh2 (參考點2門檻): {thresh2}m
                        <input
                            type="range"
                            min="100"
                            max="400"
                            step="10"
                            value={thresh2}
                            onChange={(e) => setThresh2(Number(e.target.value))}
                        />
                    </label>
                </div>
                
                <div className="control-group">
                    <label>
                        Hysteresis (遲滯): {hysteresis}m
                        <input
                            type="range"
                            min="5"
                            max="50"
                            step="5"
                            value={hysteresis}
                            onChange={(e) => setHysteresis(Number(e.target.value))}
                        />
                    </label>
                </div>
                
                <div className="control-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={showThresholdLines}
                            onChange={(e) => setShowThresholdLines(e.target.checked)}
                        />
                        顯示門檻線
                    </label>
                </div>
                
                <div className="control-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={isDarkTheme}
                            onChange={(e) => setIsDarkTheme(e.target.checked)}
                        />
                        暗色主題
                    </label>
                </div>
            </div>
            
            <div className="chart-container">
                <PureD1Chart
                    thresh1={thresh1}
                    thresh2={thresh2}
                    hysteresis={hysteresis}
                    showThresholdLines={showThresholdLines}
                    isDarkTheme={isDarkTheme}
                />
            </div>
        </div>
    )
}

export default PureD1Test