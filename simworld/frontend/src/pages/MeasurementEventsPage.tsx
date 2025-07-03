/**
 * Measurement Events Page
 * 3GPP TS 38.331 Measurement Events Visualization Dashboard
 */

import React, { useState } from 'react'
import { EventA4Chart } from '../components/domains/measurement'
import { EventD1Chart } from '../components/domains/measurement/charts/EventD1Chart'
import {
    EventType,
    EventA4Params,
    EventD1Params,
} from '../components/domains/measurement/types'
import './MeasurementEventsPage.scss'

export const MeasurementEventsPage: React.FC = () => {
    const [selectedEvent, setSelectedEvent] = useState<EventType>('A4')

    // A4 事件參數
    const [a4Params, setA4Params] = useState<Partial<EventA4Params>>({
        Thresh: -65,
        Hys: 3,
        Ofn: 0,
        Ocn: 0,
        timeToTrigger: 320,
        reportAmount: 3,
        reportInterval: 1000,
        reportOnLeave: true,
    })

    // D1 事件參數
    const [d1Params, setD1Params] = useState<Partial<EventD1Params>>({
        Thresh1: 400,
        Thresh2: 250,
        Hys: 20,
        timeToTrigger: 320,
        reportAmount: 3,
        reportInterval: 1000,
        reportOnLeave: true,
        referenceLocation1: { lat: 25.0478, lon: 121.5319 }, // 台北101
        referenceLocation2: { lat: 25.0173, lon: 121.4695 }, // 中正紀念堂
    })

    const handleA4ParamChange = (
        param: keyof EventA4Params,
        value: number | boolean
    ) => {
        setA4Params((prev) => ({
            ...prev,
            [param]: value,
        }))
    }

    const handleD1ParamChange = (
        param: keyof EventD1Params,
        value: number | boolean | { lat: number; lon: number }
    ) => {
        setD1Params((prev) => ({
            ...prev,
            [param]: value,
        }))
    }

    // 根據當前選擇的事件類型獲取參數和處理函數
    const currentParams =
        selectedEvent === 'A4'
            ? a4Params
            : selectedEvent === 'D1'
            ? d1Params
            : a4Params

    const currentParamHandler =
        selectedEvent === 'A4'
            ? handleA4ParamChange
            : selectedEvent === 'D1'
            ? handleD1ParamChange
            : handleA4ParamChange

    // 移除舊的狀態變數和處理函數

    const renderEventTypeSelector = () => (
        <div className="event-type-selector">
            <h3>3GPP TS 38.331 Measurement Events</h3>
            <div className="event-buttons">
                {(['A4', 'D1', 'T1'] as EventType[]).map((eventType) => (
                    <button
                        key={eventType}
                        className={`event-btn ${
                            selectedEvent === eventType ? 'active' : ''
                        } ${
                            !['A4', 'D1'].includes(eventType) ? 'disabled' : ''
                        }`}
                        onClick={() =>
                            ['A4', 'D1'].includes(eventType) &&
                            setSelectedEvent(eventType)
                        }
                        disabled={!['A4', 'D1'].includes(eventType)}
                    >
                        Event {eventType}
                        {!['A4', 'D1'].includes(eventType) && (
                            <span className="coming-soon">Coming Soon</span>
                        )}
                    </button>
                ))}
            </div>
        </div>
    ) // 移除舊的複雜參數控制函數

    // 簡化的參數控制渲染函數
    const renderSimpleParameterControls = () => (
        <div className="parameter-controls">
            <h4>Event Parameters</h4>
            <div className="controls-grid">
                {selectedEvent === 'A4' && (
                    <>
                        <div className="control-group">
                            <label htmlFor="thresh">a4-Threshold (dBm)</label>
                            <input
                                id="thresh"
                                type="number"
                                value={a4Params.Thresh || -65}
                                onChange={(e) =>
                                    handleA4ParamChange(
                                        'Thresh',
                                        parseFloat(e.target.value)
                                    )
                                }
                                min={-100}
                                max={-40}
                                step={1}
                            />
                        </div>
                        <div className="control-group">
                            <label htmlFor="hys">Hysteresis (dB)</label>
                            <input
                                id="hys"
                                type="number"
                                value={a4Params.Hys || 3}
                                onChange={(e) =>
                                    handleA4ParamChange(
                                        'Hys',
                                        parseFloat(e.target.value)
                                    )
                                }
                                min={0}
                                max={10}
                                step={0.5}
                            />
                        </div>
                    </>
                )}

                {selectedEvent === 'D1' && (
                    <>
                        <div className="control-group">
                            <label htmlFor="thresh1">
                                Distance Threshold 1 (m)
                            </label>
                            <input
                                id="thresh1"
                                type="number"
                                value={d1Params.Thresh1 || 400}
                                onChange={(e) =>
                                    handleD1ParamChange(
                                        'Thresh1',
                                        parseFloat(e.target.value)
                                    )
                                }
                                min={100}
                                max={1000}
                                step={10}
                            />
                        </div>
                        <div className="control-group">
                            <label htmlFor="thresh2">
                                Distance Threshold 2 (m)
                            </label>
                            <input
                                id="thresh2"
                                type="number"
                                value={d1Params.Thresh2 || 250}
                                onChange={(e) =>
                                    handleD1ParamChange(
                                        'Thresh2',
                                        parseFloat(e.target.value)
                                    )
                                }
                                min={100}
                                max={1000}
                                step={10}
                            />
                        </div>
                    </>
                )}
            </div>
        </div>
    )

    const renderEventDescription = () => (
        <div className="event-description">
            {selectedEvent === 'A4' && (
                <>
                    <h4>Event A4: Neighbour becomes better than threshold</h4>
                    <div className="description-content">
                        <p>
                            Event A4 is triggered when a neighbouring cell's
                            signal strength becomes better than a configured
                            threshold. This is commonly used for handover
                            decisions in cellular networks.
                        </p>

                        <div className="conditions">
                            <div className="condition">
                                <strong>Entering condition (A4-1):</strong>
                                <code>Mn + Ofn + Ocn – Hys &gt; Thresh</code>
                            </div>
                            <div className="condition">
                                <strong>Leaving condition (A4-2):</strong>
                                <code>Mn + Ofn + Ocn + Hys &lt; Thresh</code>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {selectedEvent === 'D1' && (
                <>
                    <h4>
                        Event D1: Distance between UE and reference locations
                    </h4>
                    <div className="description-content">
                        <p>
                            Event D1 is triggered when the distance between UE
                            and reference locations meets both threshold
                            conditions simultaneously. This is useful for
                            location-based handover decisions.
                        </p>

                        <div className="conditions">
                            <div className="condition">
                                <strong>Entering condition (D1-1):</strong>
                                <code>
                                    Ml1 – Hys &gt; Thresh1 AND Ml2 + Hys &lt;
                                    Thresh2
                                </code>
                            </div>
                            <div className="condition">
                                <strong>Leaving condition (D1-2):</strong>
                                <code>
                                    Ml1 + Hys &lt; Thresh1 OR Ml2 – Hys &gt;
                                    Thresh2
                                </code>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    )

    return (
        <div className="measurement-events-page">
            <div className="page-header">
                <h1>3GPP TS 38.331 Measurement Events</h1>
                <p>
                    Interactive visualization of 5G NR measurement events for
                    handover and radio resource management
                </p>
            </div>

            <div className="page-content">
                <div className="left-panel">
                    {renderEventTypeSelector()}
                    {renderSimpleParameterControls()}
                    {renderEventDescription()}
                </div>

                <div className="main-chart-area">
                    {selectedEvent === 'A4' && (
                        <EventA4Chart
                            width={1000}
                            height={700}
                            params={a4Params}
                            onEventTriggered={(condition) => {
                                console.log('Event triggered:', condition)
                            }}
                        />
                    )}
                    {selectedEvent === 'D1' && (
                        <EventD1Chart
                            width={1000}
                            height={700}
                            thresh1={d1Params.Thresh1}
                            thresh2={d1Params.Thresh2}
                            hysteresis={d1Params.Hys}
                            showThresholdLines={true}
                            isDarkTheme={true}
                        />
                    )}
                </div>
            </div>
        </div>
    )
}

export default MeasurementEventsPage
