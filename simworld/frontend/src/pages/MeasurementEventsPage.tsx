/**
 * Measurement Events Page
 * 3GPP TS 38.331 Measurement Events Visualization Dashboard
 */

import React, { useState } from 'react';
import { EventA4Chart } from '../components/domains/measurement';
import { EventType, EventA4Params } from '../components/domains/measurement/types';
import './MeasurementEventsPage.scss';

export const MeasurementEventsPage: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState<EventType>('A4');
  const [eventParams, setEventParams] = useState<Partial<EventA4Params>>({
    Thresh: -65,
    Hys: 3,
    Ofn: 0,
    Ocn: 0,
    timeToTrigger: 320,
    reportAmount: 3,
    reportInterval: 1000,
    reportOnLeave: true
  });

  const handleParamChange = (param: keyof EventA4Params, value: number | boolean) => {
    setEventParams(prev => ({
      ...prev,
      [param]: value
    }));
  };

  const renderEventTypeSelector = () => (
    <div className="event-type-selector">
      <h3>3GPP TS 38.331 Measurement Events</h3>
      <div className="event-buttons">
        {(['A4', 'D1', 'D2', 'T1'] as EventType[]).map(eventType => (
          <button
            key={eventType}
            className={`event-btn ${selectedEvent === eventType ? 'active' : ''} ${eventType !== 'A4' ? 'disabled' : ''}`}
            onClick={() => eventType === 'A4' && setSelectedEvent(eventType)}
            disabled={eventType !== 'A4'}
          >
            Event {eventType}
            {eventType !== 'A4' && <span className="coming-soon">Coming Soon</span>}
          </button>
        ))}
      </div>
    </div>
  );

  const renderParameterControls = () => (
    <div className="parameter-controls">
      <h4>Event Parameters</h4>
      <div className="controls-grid">
        <div className="control-group">
          <label htmlFor="thresh">a4-Threshold (dBm)</label>
          <input
            id="thresh"
            type="number"
            value={eventParams.Thresh || -65}
            onChange={(e) => handleParamChange('Thresh', parseFloat(e.target.value))}
            min={-100}
            max={-30}
            step={1}
          />
        </div>

        <div className="control-group">
          <label htmlFor="hys">Hysteresis (dB)</label>
          <input
            id="hys"
            type="number"
            value={eventParams.Hys || 3}
            onChange={(e) => handleParamChange('Hys', parseFloat(e.target.value))}
            min={0}
            max={30}
            step={0.5}
          />
        </div>

        <div className="control-group">
          <label htmlFor="ofn">Offset Ofn (dB)</label>
          <input
            id="ofn"
            type="number"
            value={eventParams.Ofn || 0}
            onChange={(e) => handleParamChange('Ofn', parseFloat(e.target.value))}
            min={-24}
            max={24}
            step={0.5}
          />
        </div>

        <div className="control-group">
          <label htmlFor="ocn">Offset Ocn (dB)</label>
          <input
            id="ocn"
            type="number"
            value={eventParams.Ocn || 0}
            onChange={(e) => handleParamChange('Ocn', parseFloat(e.target.value))}
            min={-24}
            max={24}
            step={0.5}
          />
        </div>

        <div className="control-group">
          <label htmlFor="ttt">TimeToTrigger (ms)</label>
          <select
            id="ttt"
            value={eventParams.timeToTrigger || 320}
            onChange={(e) => handleParamChange('timeToTrigger', parseInt(e.target.value))}
          >
            <option value={0}>0</option>
            <option value={40}>40</option>
            <option value={64}>64</option>
            <option value={80}>80</option>
            <option value={100}>100</option>
            <option value={128}>128</option>
            <option value={160}>160</option>
            <option value={256}>256</option>
            <option value={320}>320</option>
            <option value={480}>480</option>
            <option value={512}>512</option>
            <option value={640}>640</option>
            <option value={1024}>1024</option>
            <option value={1280}>1280</option>
            <option value={2560}>2560</option>
            <option value={5120}>5120</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="reportAmount">Report Amount</label>
          <select
            id="reportAmount"
            value={eventParams.reportAmount || 3}
            onChange={(e) => handleParamChange('reportAmount', parseInt(e.target.value))}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={4}>4</option>
            <option value={8}>8</option>
            <option value={16}>16</option>
            <option value={32}>32</option>
            <option value={64}>64</option>
            <option value={-1}>Infinity</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="reportInterval">Report Interval (ms)</label>
          <select
            id="reportInterval"
            value={eventParams.reportInterval || 1000}
            onChange={(e) => handleParamChange('reportInterval', parseInt(e.target.value))}
          >
            <option value={120}>120</option>
            <option value={240}>240</option>
            <option value={480}>480</option>
            <option value={640}>640</option>
            <option value={1024}>1024</option>
            <option value={2048}>2048</option>
            <option value={5120}>5120</option>
            <option value={10240}>10240</option>
            <option value={60000}>60000</option>
            <option value={360000}>360000</option>
            <option value={720000}>720000</option>
            <option value={1800000}>1800000</option>
            <option value={3600000}>3600000</option>
          </select>
        </div>

        <div className="control-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={eventParams.reportOnLeave || false}
              onChange={(e) => handleParamChange('reportOnLeave', e.target.checked)}
            />
            Report on Leave
          </label>
        </div>
      </div>
    </div>
  );

  const renderEventDescription = () => (
    <div className="event-description">
      <h4>Event A4: Neighbour becomes better than threshold</h4>
      <div className="description-content">
        <p>
          Event A4 is triggered when a neighbouring cell's signal strength becomes better than a configured threshold.
          This is commonly used for handover decisions in cellular networks.
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

        <div className="variables">
          <h5>Variables:</h5>
          <ul>
            <li><strong>Mn:</strong> Measurement result of the neighbouring cell (RSRP in dBm)</li>
            <li><strong>Ofn:</strong> Measurement object specific offset (dB)</li>
            <li><strong>Ocn:</strong> Cell specific offset (dB)</li>
            <li><strong>Hys:</strong> Hysteresis parameter for this event (dB)</li>
            <li><strong>Thresh:</strong> a4-Threshold parameter (dBm)</li>
          </ul>
        </div>
      </div>
    </div>
  );

  return (
    <div className="measurement-events-page">
      <div className="page-header">
        <h1>3GPP TS 38.331 Measurement Events</h1>
        <p>Interactive visualization of 5G NR measurement events for handover and radio resource management</p>
      </div>

      <div className="page-content">
        <div className="left-panel">
          {renderEventTypeSelector()}
          {renderParameterControls()}
          {renderEventDescription()}
        </div>

        <div className="main-chart-area">
          {selectedEvent === 'A4' && (
            <EventA4Chart
              width={1000}
              height={700}
              params={eventParams}
              onEventTriggered={(condition) => {
                console.log('Event triggered:', condition);
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default MeasurementEventsPage;