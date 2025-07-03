/**
 * Event A4 Chart Component
 * Implements 3GPP TS 38.331 Event A4: Neighbour becomes better than threshold
 */

import React, { useEffect, useState, useCallback } from 'react';
import { loadCSVData, DataPoint, interpolateRSRP } from '../../../../utils/csvDataParser';
import { EventA4Params, AnimationState, EventCondition } from '../types';
import PureA4Chart from './PureA4Chart';
import './EventA4Chart.scss';


interface EventA4ChartProps {
  width?: number;
  height?: number;
  params?: Partial<EventA4Params>;
  onEventTriggered?: (condition: EventCondition) => void;
}

const DEFAULT_PARAMS: EventA4Params = {
  Thresh: -65, // a4-Threshold in dBm
  Ofn: 0, // Measurement object specific offset (dB)
  Ocn: 0, // Cell specific offset (dB)
  Hys: 3, // Hysteresis parameter (dB)
  timeToTrigger: 320, // TTT in milliseconds
  reportAmount: 3, // Number of reports to send
  reportInterval: 1000, // Interval between reports in milliseconds
  reportOnLeave: true, // Whether to report when leaving condition
};

export const EventA4Chart: React.FC<EventA4ChartProps> = ({
  width = 800,
  height = 600,
  params: _params = {},
  _onEventTriggered
}) => {
  const [rsrpData, setRsrpData] = useState<DataPoint[]>([]);
  const [animationState, setAnimationState] = useState<AnimationState>({
    isPlaying: false,
    currentTime: 0,
    speed: 1,
    nodePosition: null,
    eventConditions: [],
    activeEvents: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load RSRP data from CSV
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const csvData = await loadCSVData();
        setRsrpData(csvData.points);
      } catch (err) {
        console.error('Error loading RSRP data:', err);
        setError('Failed to load RSRP data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Check A4 conditions: Mn + Ofn + Ocn ± Hys compared to Thresh
  const checkA4Conditions = useCallback((rsrpValue: number): { enter: boolean; leave: boolean } => {
    const effectiveValue = rsrpValue + DEFAULT_PARAMS.Ofn + DEFAULT_PARAMS.Ocn;
    
    // A4-1 (Entering condition): Mn + Ofn + Ocn – Hys > Thresh
    const enterCondition = effectiveValue - DEFAULT_PARAMS.Hys > DEFAULT_PARAMS.Thresh;
    
    // A4-2 (Leaving condition): Mn + Ofn + Ocn + Hys < Thresh
    const leaveCondition = effectiveValue + DEFAULT_PARAMS.Hys < DEFAULT_PARAMS.Thresh;
    
    return { enter: enterCondition, leave: leaveCondition };
  }, []);

  // Animation control functions
  const startAnimation = useCallback(() => {
    setAnimationState(prev => ({ ...prev, isPlaying: true }));
  }, []);

  const stopAnimation = useCallback(() => {
    setAnimationState(prev => ({ ...prev, isPlaying: false }));
  }, []);

  const resetAnimation = useCallback(() => {
    setAnimationState(prev => ({
      ...prev,
      isPlaying: false,
      currentTime: 0,
      nodePosition: null,
      eventConditions: [],
      activeEvents: []
    }));
  }, []);

  // Animation loop
  useEffect(() => {
    let animationFrame: number;

    if (animationState.isPlaying && rsrpData.length > 0) {
      const animate = () => {
        setAnimationState(prev => {
          const timeStep = 0.1 * prev.speed; // 100ms step
          const newTime = prev.currentTime + timeStep;
          const maxTime = rsrpData[rsrpData.length - 1]?.x || 0;

          if (newTime >= maxTime) {
            return { ...prev, isPlaying: false, currentTime: maxTime };
          }

          // Get current RSRP value
          const currentRsrp = interpolateRSRP(rsrpData, newTime);
          const nodePosition = { x: newTime, y: currentRsrp };

          // Check A4 conditions
          const _conditions = checkA4Conditions(currentRsrp);
          
          // Handle event triggering logic here
          // This would include TimeToTrigger logic, report scheduling, etc.

          return {
            ...prev,
            currentTime: newTime,
            nodePosition
          };
        });

        animationFrame = requestAnimationFrame(animate);
      };

      animationFrame = requestAnimationFrame(animate);
    }

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [animationState.isPlaying, animationState.speed, rsrpData, checkA4Conditions]);


  if (loading) {
    return (
      <div className="event-a4-chart loading">
        <div className="loading-spinner">Loading RSRP data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="event-a4-chart error">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="event-a4-chart" style={{ width, height }}>
      <div className="chart-controls">
        <div className="animation-controls">
          <button 
            onClick={startAnimation} 
            disabled={animationState.isPlaying}
            className="btn btn-primary"
          >
            ▶ Play
          </button>
          <button 
            onClick={stopAnimation} 
            disabled={!animationState.isPlaying}
            className="btn btn-secondary"
          >
            ⏸ Pause
          </button>
          <button 
            onClick={resetAnimation}
            className="btn btn-secondary"
          >
            ⏹ Reset
          </button>
        </div>
        <div className="time-display">
          Time: {animationState.currentTime.toFixed(1)}s
        </div>
      </div>
      
      <div className="chart-container" style={{ height: height - 80 }}>
        <PureA4Chart 
          width={width} 
          height={height - 80}
          threshold={DEFAULT_PARAMS.Thresh}
          hysteresis={DEFAULT_PARAMS.Hys}
          showThresholdLines={true}
        />
      </div>
      
      <div className="event-info">
        <div className="event-params">
          <h4>Event A4 Parameters</h4>
          <div className="param-grid">
            <span>Threshold: {DEFAULT_PARAMS.Thresh} dBm</span>
            <span>Hysteresis: {DEFAULT_PARAMS.Hys} dB</span>
            <span>TTT: {DEFAULT_PARAMS.timeToTrigger} ms</span>
            <span>Report Amount: {DEFAULT_PARAMS.reportAmount}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventA4Chart;