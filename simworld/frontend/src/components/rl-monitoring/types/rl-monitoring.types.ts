/**
 * RL 監控系統的 TypeScript 類型定義
 */

// 算法狀態類型
export interface AlgorithmStatus {
  algorithm: 'dqn' | 'ppo' | 'sac';
  status: 'idle' | 'running' | 'completed' | 'error';
  progress: number;
  current_episode: number;
  total_episodes: number;
  average_reward: number;
  training_active: boolean;
  session_id?: string;
  start_time?: string;
  metrics?: {
    episodes_completed: number;
    total_episodes: number;
    average_reward: number;
    progress: number;
    handover_delay?: number;
    success_rate?: number;
    signal_drop_time?: number;
    energy_efficiency?: number;
    loss?: number;
    training_loss?: number;
  };
}

// 算法比較數據
export interface AlgorithmComparison {
  algorithms: AlgorithmStatus[];
  performance_metrics: {
    reward_comparison: Record<string, number>;
    convergence_analysis: Record<string, number[]>;
    statistical_significance: Record<string, boolean>;
  };
  baseline_comparison?: {
    ieee_standard: Record<string, number>;
    gpp_standard: Record<string, number>;
  };
}

// 性能指標
export interface PerformanceMetrics {
  latency: number;
  success_rate: number;
  throughput: number;
  error_rate: number;
  response_time: number;
  resource_utilization: {
    cpu: number;
    memory: number;
    gpu?: number;
  };
}

// 算法排名
export interface AlgorithmRanking {
  algorithm: string;
  rank: number;
  score: number;
  metrics: {
    reward: number;
    convergence_speed: number;
    stability: number;
    efficiency: number;
  };
}

// 視覺化數據
export interface VisualizationData {
  type: 'feature_importance' | 'decision_tree' | 'convergence' | 'comparison';
  format: 'plotly' | 'matplotlib' | 'json';
  data: any;
  metadata?: {
    algorithm?: string;
    timestamp?: string;
    confidence?: number;
  };
}

// 決策數據
export interface DecisionData {
  decision_id: string;
  algorithm: string;
  input_features: Record<string, number>;
  output_action: any;
  confidence: number;
  reasoning: {
    feature_importance: Record<string, number>;
    decision_path: any[];
    q_values?: Record<string, number>;
    policy_output?: any;
  };
  timestamp: string;
}

// 比較數據
export interface ComparisonData {
  algorithms: string[];
  metrics: Record<string, Record<string, number>>;
  radar_chart_data?: any;
  convergence_data?: Record<string, number[]>;
  statistical_tests?: Record<string, any>;
}

// 實時指標
export interface RealTimeMetrics {
  timestamp: string;
  system_status: 'healthy' | 'warning' | 'error';
  active_algorithms: string[];
  resource_usage: {
    cpu_percent: number;
    memory_percent: number;
    gpu_percent?: number;
  };
  performance_indicators: {
    avg_response_time: number;
    success_rate: number;
    error_count: number;
  };
}

// 換手事件
export interface HandoverEvent {
  event_id: string;
  event_type: 'A4' | 'D1' | 'D2' | 'T1' | 'custom';
  timestamp: string;
  source_satellite: string;
  target_satellite: string;
  algorithm_decision: string;
  success: boolean;
  metrics: {
    latency_ms: number;
    signal_strength: number;
    handover_delay: number;
  };
}

// 系統狀態
export interface SystemStatus {
  overall_health: 'healthy' | 'degraded' | 'critical';
  services: Record<string, 'up' | 'down' | 'maintenance'>;
  last_updated: string;
  uptime: number;
  error_logs: Array<{
    timestamp: string;
    level: 'info' | 'warning' | 'error';
    message: string;
    component: string;
  }>;
}

// 訓練會話
export interface ExperimentSession {
  session_id: string;
  experiment_name: string;
  algorithm_type: string;
  scenario_type: string;
  status: 'running' | 'completed' | 'failed';
  start_time: string;
  end_time?: string;
  hyperparameters: Record<string, any>;
  results?: {
    final_reward: number;
    episodes_completed: number;
    convergence_episode: number;
    success_rate: number;
  };
  research_notes?: string;
}

// 基準比較
export interface BaselineComparison {
  baseline_algorithms: string[];
  comparison_metrics: Record<string, Record<string, number>>;
  statistical_tests: Record<string, {
    p_value: number;
    significant: boolean;
    test_type: string;
  }>;
  improvement_percentage: Record<string, number>;
}

// 統計分析
export interface StatisticalAnalysis {
  descriptive_stats: Record<string, {
    mean: number;
    std: number;
    min: number;
    max: number;
    median: number;
  }>;
  correlation_matrix: Record<string, Record<string, number>>;
  confidence_intervals: Record<string, {
    lower: number;
    upper: number;
    confidence_level: number;
  }>;
  trend_analysis: Record<string, {
    slope: number;
    r_squared: number;
    trend: 'increasing' | 'decreasing' | 'stable';
  }>;
}

// 主要數據接口
export interface RLMonitoringData {
  training: {
    status: string;
    progress: number;
    currentEpisode: number;
    totalEpisodes: number;
    algorithms: AlgorithmStatus[];
  };
  algorithms: {
    comparison: AlgorithmComparison;
    performance: PerformanceMetrics;
    ranking: AlgorithmRanking[];
  };
  visualization: {
    featureImportance: VisualizationData;
    decisionExplanation: DecisionData;
    algorithmComparison: ComparisonData;
  };
  realtime: {
    metrics: RealTimeMetrics;
    events: HandoverEvent[];
    status: SystemStatus;
  };
  research: {
    experiments: ExperimentSession[];
    baseline: BaselineComparison;
    statistics: StatisticalAnalysis;
  };
}

// 組件 Props 接口
export interface RLMonitoringPanelProps {
  mode?: 'standalone' | 'embedded';
  height?: string;
  refreshInterval?: number;
  onDataUpdate?: (data: RLMonitoringData) => void;
  onError?: (error: Error) => void;
}

// Hook 選項
export interface RLMonitoringOptions {
  refreshInterval: number;
  enabled?: boolean;
  autoStart?: boolean;
  algorithms?: ('dqn' | 'ppo' | 'sac')[];
}

// 事件類型
export interface TrainingStartEvent {
  algorithm: string;
  config: {
    episodes: number;
    batch_size?: number;
    learning_rate?: number;
  };
  timestamp: string;
}

export interface AlgorithmSwitchEvent {
  from_algorithm: string;
  to_algorithm: string;
  reason: string;
  timestamp: string;
}

export interface DataUpdateEvent {
  type: 'training' | 'performance' | 'visualization' | 'realtime' | 'research';
  data: any;
  timestamp: string;
}

export interface ErrorEvent {
  error_type: string;
  message: string;
  component: string;
  timestamp: string;
  stack?: string;
}

// 工具函數接口
export interface RLMonitoringUtils {
  exportData: (format: 'json' | 'csv' | 'excel') => Promise<Blob>;
  resetMonitoring: () => Promise<void>;
  switchAlgorithm: (algorithm: string) => Promise<void>;
  pauseTraining: (algorithm: string) => Promise<void>;
  resumeTraining: (algorithm: string) => Promise<void>;
  getHistoricalData: (timeRange: string) => Promise<any>;
}

// 標準整合接口 (為 @todo.md 使用)
export interface RLMonitoringInterface {
  component: React.ComponentType<RLMonitoringPanelProps>;
  hooks: {
    useRLStatus: () => RLMonitoringData['training'];
    useAlgorithmMetrics: () => RLMonitoringData['algorithms'];
    useVisualization: () => RLMonitoringData['visualization'];
    useRealTimeData: () => RLMonitoringData['realtime'];
  };
  events: {
    onTrainingStart: EventEmitter<TrainingStartEvent>;
    onAlgorithmSwitch: EventEmitter<AlgorithmSwitchEvent>;
    onDataUpdate: EventEmitter<DataUpdateEvent>;
    onError: EventEmitter<ErrorEvent>;
  };
  utils: RLMonitoringUtils;
}

// EventEmitter 簡單實現類型
export interface EventEmitter<T> {
  on: (listener: (data: T) => void) => void;
  off: (listener: (data: T) => void) => void;
  emit: (data: T) => void;
}