/**
 * Types for 3GPP TS 38.331 Measurement Events
 */

// 重新導出 eventConfig 中的類型
export type { EventType, EventCategory, EventConfig } from '../config/eventConfig';

export interface DataPoint {
  x: number;
  y: number;
}

export interface MeasurementEventParams {
  // Common parameters
  Hys: number; // Hysteresis parameter (dB for A4, meters for D2)
  timeToTrigger: number; // TTT in milliseconds
  reportAmount: number; // Number of reports to send
  reportInterval: number; // Interval between reports in milliseconds
  reportOnLeave: boolean; // Whether to report when leaving condition
}

export interface EventA4Params extends MeasurementEventParams {
  Thresh: number; // a4-Threshold in dBm
  Ofn: number; // Measurement object specific offset (dB)
  Ocn: number; // Cell specific offset (dB)
}

export interface EventD2Params extends MeasurementEventParams {
  Thresh1: number; // Distance threshold 1 in meters
  Thresh2: number; // Distance threshold 2 in meters
  movingReferenceLocation: { lat: number; lon: number }; // Satellite position
  referenceLocation: { lat: number; lon: number }; // Fixed reference
}

export interface EventCondition {
  type: 'enter' | 'leave';
  timePoint: number;
  triggered: boolean;
  description: string;
}

export interface AnimationState {
  isPlaying: boolean;
  currentTime: number;
  speed: number; // Animation speed multiplier
  nodePosition: DataPoint | null;
  eventConditions: EventCondition[];
  activeEvents: string[];
}

export interface ChartAnnotation {
  id: string;
  type: 'line' | 'box' | 'label' | 'arrow';
  value?: number;
  valueRange?: [number, number];
  position: {
    x?: number | string;
    y?: number | string;
  };
  label: string;
  color: string;
  borderDash?: number[];
}

export interface EventChartConfig {
  eventType: EventType;
  title: string;
  xAxisLabel: string;
  yAxisLabel: string;
  yAxisUnit: string;
  xAxisUnit: string;
  datasets: ChartDataset[];
  annotations: ChartAnnotation[];
  yAxisRange: { min: number; max: number };
  params: MeasurementEventParams;
}

export interface ChartDataset {
  label: string;
  data: DataPoint[];
  borderColor: string;
  backgroundColor: string;
  borderWidth: number;
  fill: boolean;
  pointRadius: number;
  pointHoverRadius: number;
  tension: number; // For curve smoothing
}

// 事件選擇器相關類型
export interface EventSelectorState {
  selectedEvent: EventType;
  availableEvents: EventType[];
  isLoading: boolean;
  error?: string;
}

export interface EventNavigationProps {
  currentEvent: EventType;
  onEventChange: (eventType: EventType) => void;
  showDescription?: boolean;
  compact?: boolean;
}