/**
 * 共享類型定義 - 衛星通訊事件圖表重構
 * 基於現有的 MeasurementEventParams 擴展，為重構後的組件架構提供類型支持
 */

// 重新導出現有類型
export type { 
  EventType, 
  EventCategory, 
  MeasurementEventParams,
  EventA4Params,
  EventD1Params,
  EventD2Params,
  EventT1Params,
  DataPoint,
  AnimationState,
  EventCondition,
  ChartAnnotation,
  EventChartConfig,
  ChartDataset
} from '../../types';

// 基礎事件查看器屬性
export interface BaseEventViewerProps<T extends MeasurementEventParams> {
  eventType: EventType;
  params: T;
  onParamsChange: (params: T) => void;
  chartComponent: React.ComponentType<BaseChartProps<T>>;
  narrationGenerator?: (params: T, animationState: AnimationState) => string;
  className?: string;
}

// 動畫控制器屬性
export interface AnimationControllerProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  speed: number;
  onPlayPause: () => void;
  onReset: () => void;
  onSpeedChange: (speed: number) => void;
  onTimeChange: (time: number) => void;
  className?: string;
}

// 解說面板屬性
export interface NarrationPanelProps {
  isVisible: boolean;
  isMinimized: boolean;
  showTechnicalDetails: boolean;
  content: string;
  position: { x: number; y: number };
  opacity: number;
  onToggleVisibility: () => void;
  onToggleMinimized: () => void;
  onToggleTechnicalDetails: () => void;
  onPositionChange: (position: { x: number; y: number }) => void;
  onOpacityChange: (opacity: number) => void;
  className?: string;
}

// 事件控制面板屬性
export interface EventControlPanelProps<T extends MeasurementEventParams> {
  eventType: EventType;
  params: T;
  onParamsChange: (params: T) => void;
  onReset: () => void;
  showThresholdLines: boolean;
  onToggleThresholdLines: () => void;
  isDarkTheme: boolean;
  onToggleTheme: () => void;
  className?: string;
}

// 基礎圖表屬性
export interface BaseChartProps<T extends MeasurementEventParams> {
  eventType: EventType;
  params: T;
  animationState: AnimationState;
  isDarkTheme: boolean;
  showThresholdLines: boolean;
  className?: string;
}

// 事件特定邏輯 Hook 介面
export interface UseEventLogicResult<T extends MeasurementEventParams> {
  params: T;
  setParams: (params: T) => void;
  resetParams: () => void;
  animationState: AnimationState;
  updateAnimationState: (updates: Partial<AnimationState>) => void;
  themeState: {
    isDarkTheme: boolean;
    toggleTheme: () => void;
  };
  panelState: {
    showThresholdLines: boolean;
    toggleThresholdLines: () => void;
    narrationPanel: {
      isVisible: boolean;
      isMinimized: boolean;
      showTechnicalDetails: boolean;
      position: { x: number; y: number };
      opacity: number;
    };
    updateNarrationPanel: (updates: Partial<typeof panelState.narrationPanel>) => void;
  };
}

// 解說內容生成器函數類型
export type NarrationGenerator<T extends MeasurementEventParams> = (
  params: T,
  animationState: AnimationState
) => string;

// 事件參數配置
export interface EventParameterConfig<T extends MeasurementEventParams> {
  eventType: EventType;
  defaultParams: T;
  parameterDefinitions: ParameterDefinition[];
  validationRules: ValidationRule[];
}

export interface ParameterDefinition {
  key: string;
  label: string;
  type: 'number' | 'boolean' | 'select' | 'location';
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  options?: Array<{ value: string | number | boolean; label: string }>;
  description?: string;
}

export interface ValidationRule {
  key: string;
  validator: (value: unknown, allParams: MeasurementEventParams) => boolean;
  errorMessage: string;
}

// 圖表配置工廠函數類型
export type ChartConfigFactory<T extends MeasurementEventParams> = (
  eventType: EventType,
  params: T,
  isDarkTheme: boolean
) => EventChartConfig;

// 拖拽系統介面
export interface DragState {
  isDragging: boolean;
  dragOffset: { x: number; y: number };
  lastPosition: { x: number; y: number };
}

export interface DragHandlers {
  onDragStart: (event: React.MouseEvent) => void;
  onDragMove: (event: MouseEvent) => void;
  onDragEnd: () => void;
}

// 事件特定的常數和配置
export interface EventConstants {
  ANIMATION_DURATION: number;
  DEFAULT_SPEED: number;
  SPEED_OPTIONS: number[];
  THRESHOLD_LINE_COLORS: {
    light: string;
    dark: string;
  };
  DEFAULT_NARRATION_POSITION: { x: number; y: number };
  DEFAULT_NARRATION_OPACITY: number;
}