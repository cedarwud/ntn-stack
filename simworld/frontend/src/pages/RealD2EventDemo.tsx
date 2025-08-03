/**
 * RealD2EventDemo - Demo page for real satellite D2 event visualization
 */

import React, { useState } from 'react'
// import D2EventChart from '../components/handover/D2EventChart'; // 暫時註釋，檔案缺失
import './RealD2EventDemo.scss'

const RealD2EventDemo: React.FC = () => {
    const [constellation, setConstellation] = useState<'starlink' | 'oneweb'>(
        'starlink'
    )
    const [currentTime, setCurrentTime] = useState<Date | undefined>(undefined)
    const [thresholds, setThresholds] = useState({
        thresh1: 600,
        thresh2: 400,
        hysteresis: 20,
    })

    const handleConstellationChange = (
        newConstellation: 'starlink' | 'oneweb'
    ) => {
        setConstellation(newConstellation)
    }

    const handleTimeSelect = (time: Date) => {
        setCurrentTime(time)
        console.log('Selected time:', time)
    }

    const handleThresholdChange = (field: string, value: number) => {
        setThresholds((prev) => ({
            ...prev,
            [field]: value,
        }))
    }

    return (
        <div className="real-d2-event-demo">
            <div className="demo-container">
                <h1 className="demo-title">真實 D2 事件可視化</h1>
                <p className="demo-subtitle">
                    使用真實衛星數據和 Moving Reference Location (MRL)
                    計算來可視化 3GPP D2 換手事件
                </p>

                {/* Controls */}
                <div className="controls-panel">
                    <div className="control-group">
                        <label className="control-label">衛星星座</label>
                        <div className="toggle-buttons">
                            <button
                                className={`toggle-button ${
                                    constellation === 'starlink' ? 'active' : ''
                                }`}
                                onClick={() =>
                                    handleConstellationChange('starlink')
                                }
                            >
                                Starlink
                            </button>
                            <button
                                className={`toggle-button ${
                                    constellation === 'oneweb' ? 'active' : ''
                                }`}
                                onClick={() =>
                                    handleConstellationChange('oneweb')
                                }
                            >
                                OneWeb
                            </button>
                        </div>
                    </div>

                    <div className="control-group">
                        <label className="control-label">
                            閾值 1 (服務衛星): {thresholds.thresh1} km
                        </label>
                        <input
                            type="range"
                            className="slider"
                            value={thresholds.thresh1}
                            onChange={(e) =>
                                handleThresholdChange(
                                    'thresh1',
                                    Number(e.target.value)
                                )
                            }
                            min={300}
                            max={800}
                            step={25}
                        />
                    </div>

                    <div className="control-group">
                        <label className="control-label">
                            閾值 2 (目標衛星): {thresholds.thresh2} km
                        </label>
                        <input
                            type="range"
                            className="slider"
                            value={thresholds.thresh2}
                            onChange={(e) =>
                                handleThresholdChange(
                                    'thresh2',
                                    Number(e.target.value)
                                )
                            }
                            min={200}
                            max={600}
                            step={25}
                        />
                    </div>

                    <div className="control-group">
                        <label className="control-label">
                            滯後效應: {thresholds.hysteresis} km
                        </label>
                        <input
                            type="range"
                            className="slider"
                            value={thresholds.hysteresis}
                            onChange={(e) =>
                                handleThresholdChange(
                                    'hysteresis',
                                    Number(e.target.value)
                                )
                            }
                            min={5}
                            max={50}
                            step={5}
                        />
                    </div>
                </div>

                {/* D2 Event Chart */}
                {/* 暫時註釋，D2EventChart 組件缺失
                <D2EventChart
                    constellation={constellation}
                    currentTime={currentTime}
                    onTimeSelect={handleTimeSelect}
                    thresholds={thresholds}
                    height={500}
                />
                */}
                <div
                    style={{
                        height: '500px',
                        background: '#f0f0f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#666',
                        fontSize: '16px',
                    }}
                >
                    D2EventChart 組件暫時不可用
                </div>

                {/* Info Panels */}
                <div className="info-panels">
                    <div className="info-panel">
                        <h3>D2 事件觸發條件</h3>
                        <p>D2 換手在以下條件觸發：</p>
                        <ul>
                            <li>
                                Ml1 (服務衛星 MRL 距離) &gt; 閾值1 + 滯後效應
                            </li>
                            <li>
                                Ml2 (目標衛星 MRL 距離) &lt; 閾值2 - 滯後效應
                            </li>
                        </ul>
                        <p className="note">
                            MRL (Moving Reference Location) 是衛星的星下點 -
                            即衛星在地球表面正下方的投影點。
                        </p>
                    </div>

                    <div className="info-panel">
                        <h3>當前狀態</h3>
                        {currentTime ? (
                            <>
                                <p>
                                    <strong>選定時間:</strong>{' '}
                                    {currentTime.toLocaleTimeString()}
                                </p>
                                <p className="note">點擊圖表選擇不同的時間點</p>
                            </>
                        ) : (
                            <p className="note">點擊圖表選擇時間點</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default RealD2EventDemo
