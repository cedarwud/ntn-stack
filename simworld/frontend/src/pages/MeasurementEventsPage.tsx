/**
 * Measurement Events Page
 * 3GPP TS 38.331 Measurement Events Visualization Dashboard
 */

import React, { useState } from 'react'
import { EventA4Chart } from '../components/domains/measurement'
import {
    EventType,
    EventA4Params,
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

    const handleA4ParamChange = (
        param: keyof EventA4Params,
        value: number | boolean
    ) => {
        setA4Params((prev) => ({
            ...prev,
            [param]: value,
        }))
    }

    // 移除舊的狀態變數和處理函數

    const renderEventTypeSelector = () => (
        <div className="event-type-selector">
            <h3>3GPP TS 38.331 Measurement Events</h3>
            <div className="event-buttons">
                {(['A4', 'D2'] as EventType[]).map((eventType) => (
                    <button
                        key={eventType}
                        className={`event-btn ${
                            selectedEvent === eventType ? 'active' : ''
                        } ${!['A4'].includes(eventType) ? 'disabled' : ''}`}
                        onClick={() =>
                            ['A4'].includes(eventType) &&
                            setSelectedEvent(eventType)
                        }
                        disabled={!['A4'].includes(eventType)}
                    >
                        Event {eventType}
                        {!['A4'].includes(eventType) && (
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
                </div>
            </div>
        </div>
    )
}

export default MeasurementEventsPage
