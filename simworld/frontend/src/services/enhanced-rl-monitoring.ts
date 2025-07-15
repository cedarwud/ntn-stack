/**
 * 增強版 RL 監控服務 - Phase 2
 * 整合 NetStack RL 客戶端和統一監控功能
 */

import { netStackApi } from './netstack-api';

// 擴展的數據類型
export interface EnhancedRLStatus {
  // 基礎狀態
  overall_status: 'healthy' | 'warning' | 'error' | 'offline';
  last_updated: string;
  
  // 算法狀態
  algorithms: {
    dqn: AlgorithmStatus;
    ppo: AlgorithmStatus;
    sac: AlgorithmStatus;
  };
  
  // NetStack 整合狀態  
  netstack_integration: {
    connected: boolean;
    client_status: 'active' | 'inactive' | 'error';
    api_bridge_health: 'healthy' | 'degraded' | 'failed';
    session_management: boolean;
    fallback_active: boolean;
  };
  
  // 訓練會話
  active_sessions: TrainingSession[];
  completed_sessions: number;
  
  // 性能指標
  performance_metrics: {
    avg_decision_time: number;
    success_rate: number;
    api_response_time: number;
    memory_usage: number;
    cpu_usage: number;
  };
  
  // 實時決策數據
  realtime_decisions: RealtimeDecision[];
  
  // 系統事件
  recent_events: SystemEvent[];
}

export interface AlgorithmStatus {
  name: string;
  status: 'training' | 'idle' | 'error' | 'paused';
  progress: number;
  current_episode: number;
  total_episodes: number;
  current_reward: number;
  best_reward: number;
  convergence_rate: number;
  model_version: string;
  last_updated: string;
  hardware_usage: {
    gpu: number;
    memory: number;
  };
}

export interface TrainingSession {
  session_id: string;
  algorithm: string;
  status: 'running' | 'paused' | 'completed' | 'error';
  start_time: string;
  end_time?: string;
  progress: number;
  episodes_completed: number;
  episodes_target: number;
  current_reward: number;
  metrics: {
    avg_reward: number;
    best_reward: number;
    convergence_metrics: Record<string, number>;
  };
}

export interface RealtimeDecision {
  decision_id: string;
  timestamp: string;
  algorithm: string;
  input_state: Record<string, any>;
  output_action: any;
  confidence: number;
  execution_time_ms: number;
  result: 'success' | 'failure' | 'pending';
}

export interface SystemEvent {
  event_id: string;
  timestamp: string;
  type: 'info' | 'warning' | 'error' | 'critical';
  source: 'netstack' | 'simworld' | 'integration';
  message: string;
  details?: Record<string, any>;
}

export interface AlgorithmControlRequest {
  algorithm: 'dqn' | 'ppo' | 'sac';
  action: 'start' | 'pause' | 'resume' | 'stop' | 'restart';
  parameters?: Record<string, any>;
}

export interface AlgorithmSwitchRequest {
  from_algorithm: string;
  to_algorithm: string;
  preserve_session: boolean;
  transfer_learning: boolean;
}

export class EnhancedRLMonitoringService {
  private baseUrl: string;
  private refreshInterval: number;
  private eventListeners: Map<string, Function[]> = new Map();
  private wsConnection: WebSocket | null = null;
  private isConnected: boolean = false;

  constructor(baseUrl: string = '', refreshInterval: number = 2000) {
    this.baseUrl = baseUrl;
    this.refreshInterval = refreshInterval;
    this.initializeEventHandlers();
  }

  private initializeEventHandlers() {
    // 初始化事件監聽器
    this.eventListeners.set('statusUpdate', []);
    this.eventListeners.set('algorithmChange', []);
    this.eventListeners.set('sessionUpdate', []);
    this.eventListeners.set('decisionMade', []);
    this.eventListeners.set('error', []);
    this.eventListeners.set('connectionChange', []);
  }

  // 事件系統
  public on(event: string, callback: Function) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(callback);
  }

  public off(event: string, callback: Function) {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any) {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  // WebSocket 連接管理
  public async connectWebSocket(): Promise<boolean> {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/rl-enhanced-monitoring`;
      
      this.wsConnection = new WebSocket(wsUrl);
      
      this.wsConnection.onopen = () => {
        this.isConnected = true;
        this.emit('connectionChange', { connected: true });
        console.log('Enhanced RL monitoring WebSocket connected');
      };
      
      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      this.wsConnection.onclose = () => {
        this.isConnected = false;
        this.emit('connectionChange', { connected: false });
        console.log('Enhanced RL monitoring WebSocket disconnected');
        
        // 自動重連
        setTimeout(() => {
          if (!this.isConnected) {
            this.connectWebSocket();
          }
        }, 5000);
      };
      
      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', { source: 'websocket', error });
      };
      
      return true;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.emit('error', { source: 'websocket', error });
      return false;
    }
  }

  private handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'status_update':
        this.emit('statusUpdate', data.payload);
        break;
      case 'algorithm_change':
        this.emit('algorithmChange', data.payload);
        break;
      case 'session_update':
        this.emit('sessionUpdate', data.payload);
        break;
      case 'decision_made':
        this.emit('decisionMade', data.payload);
        break;
      case 'system_event':
        this.emit('systemEvent', data.payload);
        break;
      default:
        console.warn('Unknown WebSocket message type:', data.type);
    }
  }

  // 核心 API 方法
  public async getEnhancedStatus(): Promise<EnhancedRLStatus> {
    try {
      // 並行獲取多個數據源
      const [
        basicStatus,
        netstackStatus,
        sessionsData,
        performanceData,
        realtimeData,
        eventsData
      ] = await Promise.all([
        this.getBasicRLStatus(),
        this.getNetStackIntegrationStatus(), 
        this.getActiveSessions(),
        this.getPerformanceMetrics(),
        this.getRealtimeDecisions(),
        this.getRecentEvents()
      ]);

      // 整合數據
      const enhancedStatus: EnhancedRLStatus = {
        overall_status: this.calculateOverallStatus(basicStatus, netstackStatus),
        last_updated: new Date().toISOString(),
        algorithms: basicStatus.algorithms,
        netstack_integration: netstackStatus,
        active_sessions: sessionsData,
        completed_sessions: sessionsData.filter(s => s.status === 'completed').length,
        performance_metrics: performanceData,
        realtime_decisions: realtimeData,
        recent_events: eventsData
      };

      this.emit('statusUpdate', enhancedStatus);
      return enhancedStatus;
    } catch (error) {
      console.error('Failed to get enhanced RL status:', error);
      this.emit('error', { source: 'api', method: 'getEnhancedStatus', error });
      throw error;
    }
  }

  private async getBasicRLStatus(): Promise<any> {
    try {
      const response = await fetch('/api/v1/rl/status');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get basic RL status:', error);
      // 返回默認狀態
      return {
        algorithms: {
          dqn: this.createDefaultAlgorithmStatus('DQN'),
          ppo: this.createDefaultAlgorithmStatus('PPO'),  
          sac: this.createDefaultAlgorithmStatus('SAC')
        }
      };
    }
  }

  private async getNetStackIntegrationStatus(): Promise<any> {
    try {
      const response = await fetch('/interference/ai-ran/netstack/status');
      const isConnected = response.ok;
      
      if (isConnected) {
        const data = await response.json();
        return {
          connected: true,
          client_status: 'active',
          api_bridge_health: 'healthy',
          session_management: data.session_management !== false,
          fallback_active: data.fallback_active === true
        };
      } else {
        return {
          connected: false,
          client_status: 'inactive',
          api_bridge_health: 'failed',
          session_management: false,
          fallback_active: true
        };
      }
    } catch (error) {
      console.error('Failed to get NetStack integration status:', error);
      return {
        connected: false,
        client_status: 'error',
        api_bridge_health: 'failed',
        session_management: false,
        fallback_active: true
      };
    }
  }

  private async getActiveSessions(): Promise<TrainingSession[]> {
    try {
      const response = await fetch('/api/v1/rl/training/sessions');
      if (response.ok) {
        const data = await response.json();
        return Array.isArray(data) ? data : data.sessions || [];
      }
      return [];
    } catch (error) {
      console.error('Failed to get active sessions:', error);
      return [];
    }
  }

  private async getPerformanceMetrics(): Promise<any> {
    try {
      const response = await fetch('/api/v1/rl/performance/metrics');
      if (response.ok) {
        return await response.json();
      }
      
      // 默認性能指標
      return {
        avg_decision_time: 150,
        success_rate: 95.5,
        api_response_time: 85,
        memory_usage: 45.2,
        cpu_usage: 32.8
      };
    } catch (error) {
      return {
        avg_decision_time: 0,
        success_rate: 0,
        api_response_time: 0,
        memory_usage: 0,
        cpu_usage: 0
      };
    }
  }

  private async getRealtimeDecisions(): Promise<RealtimeDecision[]> {
    try {
      const response = await fetch('/api/v1/rl/decisions/recent?limit=10');
      if (response.ok) {
        const data = await response.json();
        return Array.isArray(data) ? data : data.decisions || [];
      }
      return [];
    } catch (error) {
      return [];
    }
  }

  private async getRecentEvents(): Promise<SystemEvent[]> {
    try {
      const response = await fetch('/api/v1/rl/events/recent?limit=20');
      if (response.ok) {
        const data = await response.json();
        return Array.isArray(data) ? data : data.events || [];
      }
      return [];
    } catch (error) {
      return [];
    }
  }

  // 算法控制方法
  public async controlAlgorithm(request: AlgorithmControlRequest): Promise<boolean> {
    try {
      const response = await fetch('/api/v1/rl/algorithms/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });
      
      if (response.ok) {
        this.emit('algorithmChange', request);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to control algorithm:', error);
      this.emit('error', { source: 'api', method: 'controlAlgorithm', error });
      return false;
    }
  }

  public async switchAlgorithm(request: AlgorithmSwitchRequest): Promise<boolean> {
    try {
      const response = await fetch('/api/v1/rl/algorithms/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });
      
      if (response.ok) {
        this.emit('algorithmChange', request);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to switch algorithm:', error);
      this.emit('error', { source: 'api', method: 'switchAlgorithm', error });
      return false;
    }
  }

  // 工具方法
  private calculateOverallStatus(basicStatus: any, netstackStatus: any): 'healthy' | 'warning' | 'error' | 'offline' {
    if (!netstackStatus.connected && !netstackStatus.fallback_active) {
      return 'offline';
    }
    
    if (!netstackStatus.connected && netstackStatus.fallback_active) {
      return 'warning';
    }
    
    if (netstackStatus.api_bridge_health === 'failed') {
      return 'error';
    }
    
    if (netstackStatus.api_bridge_health === 'degraded') {
      return 'warning';
    }
    
    return 'healthy';
  }

  private createDefaultAlgorithmStatus(name: string): AlgorithmStatus {
    return {
      name,
      status: 'idle',
      progress: 0,
      current_episode: 0,
      total_episodes: 100,
      current_reward: 0,
      best_reward: 0,
      convergence_rate: 0,
      model_version: 'v1.0.0',
      last_updated: new Date().toISOString(),
      hardware_usage: {
        gpu: 0,
        memory: 0
      }
    };
  }

  // 清理方法
  public disconnect() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
    this.isConnected = false;
    this.eventListeners.clear();
  }
}

// 創建全局實例
export const enhancedRLMonitoringService = new EnhancedRLMonitoringService();

// 默認導出
export default EnhancedRLMonitoringService; 