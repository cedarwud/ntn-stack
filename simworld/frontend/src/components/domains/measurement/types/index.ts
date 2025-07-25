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
  Hys: number; // Hysteresis parameter (dB for A4, meters for D1/D2)
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

export interface EventD1Params extends MeasurementEventParams {
  Thresh1: number; // distanceThreshFromReference1 in meters
  Thresh2: number; // distanceThreshFromReference2 in meters
  referenceLocation1: { lat: number; lon: number };
  referenceLocation2: { lat: number; lon: number };
}

export interface EventD2Params extends MeasurementEventParams {
  Thresh1: number; // Distance threshold 1 in meters
  Thresh2: number; // Distance threshold 2 in meters
  movingReferenceLocation: { lat: number; lon: number }; // Satellite position
  referenceLocation: { lat: number; lon: number }; // Fixed reference
}

// T1 事件：測量時間超過門檻事件
// 基於 3GPP TS 38.331 Section 5.5.4.16 - Event T1
export interface EventT1Params {
  t1Threshold: number; // t1-Threshold in seconds - 測量時間門檻 (3GPP Thresh1)
  duration: number; // Duration in seconds - 時間窗口持續時間 (3GPP Duration)
  timeToTrigger: number; // TTT in seconds (通常為 0 因為 T1 有內建時間邏輯)
  reportAmount: number; // 報告次數 (條件事件用途)
  reportInterval: number; // 報告間隔 (秒) (條件事件用途)
  reportOnLeave: boolean; // 離開時報告 (條件事件用途)
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