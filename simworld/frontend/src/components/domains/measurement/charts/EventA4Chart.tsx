/**
 * Event A4 Chart Component
 * Implements 3GPP TS 38.331 Event A4: Neighbour becomes better than threshold
 */

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import annotationPlugin from 'chartjs-plugin-annotation';
import { loadCSVData, DataPoint, interpolateRSRP } from '../../../../utils/csvDataParser';
import { EventA4Params, AnimationState, EventCondition } from '../types';
import './EventA4Chart.scss';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  annotationPlugin
);

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
  params = {},
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

  // Merge default params with provided params
  const eventParams = useMemo(() => ({
    ...DEFAULT_PARAMS,
    ...params
  }), [params]);

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
    const effectiveValue = rsrpValue + eventParams.Ofn + eventParams.Ocn;
    
    // A4-1 (Entering condition): Mn + Ofn + Ocn – Hys > Thresh
    const enterCondition = effectiveValue - eventParams.Hys > eventParams.Thresh;
    
    // A4-2 (Leaving condition): Mn + Ofn + Ocn + Hys < Thresh
    const leaveCondition = effectiveValue + eventParams.Hys < eventParams.Thresh;
    
    return { enter: enterCondition, leave: leaveCondition };
  }, [eventParams]);

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

  // Chart configuration
  const chartData: ChartData<'line'> = useMemo(() => ({
    datasets: [
      {
        label: 'Neighbor Cell RSRP',
        data: rsrpData,
        borderColor: '#2196F3', // Blue color matching the reference image
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        borderWidth: 2,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.1, // Smooth curve
      },
      // Moving node dataset
      ...(animationState.nodePosition ? [{
        label: 'Current Position',
        data: [animationState.nodePosition],
        borderColor: '#FF5722',
        backgroundColor: '#FF5722',
        borderWidth: 0,
        pointRadius: 8,
        pointHoverRadius: 10,
        showLine: false,
      }] : [])
    ]
  }), [rsrpData, animationState.nodePosition]);

  const chartOptions: ChartOptions<'line'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: 'linear',
        position: 'bottom',
        title: {
          display: true,
          text: 'Time (s)',
          font: { size: 14, weight: 'bold' }
        },
        grid: { display: true, color: 'rgba(0,0,0,0.1)' }
      },
      y: {
        title: {
          display: true,
          text: 'RSRP (dBm)',
          font: { size: 14, weight: 'bold' }
        },
        min: -110,
        max: -40,
        grid: { display: true, color: 'rgba(0,0,0,0.1)' }
      }
    },
    plugins: {
      legend: {
        display: true,
        position: 'top'
      },
      title: {
        display: true,
        text: 'Event A4: Neighbour becomes better than threshold',
        font: { size: 16, weight: 'bold' },
        color: '#D32F2F' // Red color matching the reference
      },
      annotation: {
        annotations: {
          // A4 Threshold line
          thresholdLine: {
            type: 'line',
            yMin: eventParams.Thresh,
            yMax: eventParams.Thresh,
            borderColor: '#D32F2F',
            borderWidth: 2,
            borderDash: [5, 5],
            label: {
              content: 'a4-Threshold',
              enabled: true,
              position: 'end',
              backgroundColor: 'rgba(211, 47, 47, 0.8)',
              color: 'white',
              padding: 4
            }
          },
          // Hysteresis indication
          hystUpper: {
            type: 'line',
            yMin: eventParams.Thresh + eventParams.Hys,
            yMax: eventParams.Thresh + eventParams.Hys,
            borderColor: 'rgba(211, 47, 47, 0.5)',
            borderWidth: 1,
            borderDash: [2, 2],
            label: {
              content: `+Hys (${eventParams.Hys}dB)`,
              enabled: true,
              position: 'start',
              backgroundColor: 'rgba(211, 47, 47, 0.6)',
              color: 'white',
              padding: 2
            }
          },
          hystLower: {
            type: 'line',
            yMin: eventParams.Thresh - eventParams.Hys,
            yMax: eventParams.Thresh - eventParams.Hys,
            borderColor: 'rgba(211, 47, 47, 0.5)',
            borderWidth: 1,
            borderDash: [2, 2],
            label: {
              content: `-Hys (${eventParams.Hys}dB)`,
              enabled: true,
              position: 'start',
              backgroundColor: 'rgba(211, 47, 47, 0.6)',
              color: 'white',
              padding: 2
            }
          }
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index'
    }
  }), [eventParams]);

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
        <Line data={chartData} options={chartOptions} />
      </div>
      
      <div className="event-info">
        <div className="event-params">
          <h4>Event A4 Parameters</h4>
          <div className="param-grid">
            <span>Threshold: {eventParams.Thresh} dBm</span>
            <span>Hysteresis: {eventParams.Hys} dB</span>
            <span>TTT: {eventParams.timeToTrigger} ms</span>
            <span>Report Amount: {eventParams.reportAmount}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventA4Chart;