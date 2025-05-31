/**
 * 圖表相關類型定義
 */

// UAV 數據類型
export interface UAVPosition {
  latitude: number;
  longitude: number;
  altitude: number;
  timestamp: string;
  speed: number;
  heading: number;
}

export interface UAVSignalQuality {
  rsrp_dbm: number;
  rsrq_db: number;
  sinr_db: number;
  cqi: number;
  throughput_mbps: number;
  latency_ms: number;
  packet_loss_rate: number;
  jitter_ms: number;
  link_budget_margin_db: number;
  doppler_shift_hz: number;
  beam_alignment_score: number;
  interference_level_db: number;
  timestamp: string;
  measurement_confidence: number;
}

export interface UAVData {
  uav_id: string;
  name: string;
  flight_status: 'idle' | 'flying' | 'landing' | 'takeoff' | 'error';
  ue_connection_status: 'connected' | 'disconnected' | 'connecting';
  current_position: UAVPosition;
  target_position?: UAVPosition;
  signal_quality: UAVSignalQuality;
  last_update: string;
}

// 系統狀態數據類型
export interface ComponentMetrics {
  cpu_usage?: number;
  memory_usage?: number;
  active_connections?: number;
}

export interface SystemComponent {
  name: string;
  healthy: boolean;
  status: string;
  version: string;
  last_health_check: string;
  metrics?: ComponentMetrics;
  error?: string | null;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'error';
  timestamp: string;
  components: Record<string, SystemComponent>;
  summary: {
    total_services: number;
    healthy_services: number;
    degraded_services: number;
    last_updated: string;
  };
}

// 網路拓撲數據類型
export interface NetworkNode {
  id: string;
  name: string;
  type: 'satellite' | 'gnb' | 'uav' | 'ue' | 'core';
  position: {
    x: number;
    y: number;
    z?: number;
  };
  status: 'active' | 'inactive' | 'error';
  metrics?: ComponentMetrics;
}

export interface NetworkLink {
  id: string;
  source: string;
  target: string;
  type: 'cellular' | 'satellite' | 'mesh' | 'backhaul';
  quality: {
    rssi?: number;
    snr?: number;
    latency?: number;
    throughput?: number;
  };
  status: 'active' | 'inactive' | 'degraded';
}

export interface NetworkTopology {
  nodes: NetworkNode[];
  links: NetworkLink[];
  timestamp: string;
}

// 性能數據類型
export interface PerformanceMetrics {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  network_throughput: number;
  active_connections: number;
  response_time: number;
}

export interface TimeSeriesData {
  label: string;
  data: {
    x: string | number;
    y: number;
  }[];
  borderColor?: string;
  backgroundColor?: string;
}

// 圖表配置類型
export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'scatter' | 'radar' | 'heatmap';
  title: string;
  data: any;
  options?: any;
  realtime?: boolean;
  refreshInterval?: number;
}

// WebSocket 事件類型
export interface WebSocketEvent {
  type: 'uav_update' | 'system_status' | 'performance_metrics' | 'topology_change';
  data: any;
  timestamp: string;
}

// 圖表組件屬性類型
export interface ChartComponentProps {
  config: ChartConfig;
  className?: string;
  height?: number;
  onDataUpdate?: (data: any) => void;
  onError?: (error: Error) => void;
}

// 儀表盤配置類型
export interface DashboardConfig {
  layout: 'grid' | 'tabs' | 'sidebar';
  charts: ChartConfig[];
  autoRefresh: boolean;
  refreshInterval: number;
  realtime: boolean;
}

// 數據更新事件類型
export interface DataUpdateEvent {
  type: string;
  data: any;
  timestamp: string;
  source: 'api' | 'websocket' | 'cache';
} 