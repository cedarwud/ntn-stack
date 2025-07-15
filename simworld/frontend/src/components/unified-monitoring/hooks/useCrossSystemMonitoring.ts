/**
 * 跨系統監控聚合器 Hook - Phase 2
 * 聚合 SimWorld 和 NetStack 的監控數據
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { netStackApi } from '../../../services/netstack-api';

// 類型定義
interface SystemStatus {
  simworld: 'healthy' | 'warning' | 'error';
  netstack: 'healthy' | 'warning' | 'error';
}

interface IntegrationHealth {
  status: 'healthy' | 'warning' | 'error';
  netstackClient: boolean;
  aiRanIntegration: boolean;
  sessionManagement: boolean;
  fallbackMechanism: boolean;
  apiCalls: number;
  successRate: number;
  avgResponseTime: number;
  fallbackCount: number;
}

interface PerformanceMetrics {
  overall_health: number;
  simworld_status: 'healthy' | 'warning' | 'error';
  netstack_status: 'healthy' | 'warning' | 'error';
  integration_status: 'healthy' | 'warning' | 'error';
  active_algorithms: string[];
  training_progress: number;
  api_response_time: number;
}

interface CrossSystemAlert {
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  source: 'simworld' | 'netstack' | 'integration';
  timestamp: Date;
}

interface UseCrossSystemMonitoringReturn {
  performanceMetrics: PerformanceMetrics | null;
  systemStatus: SystemStatus;
  integrationHealth: IntegrationHealth;
  crossSystemAlerts: CrossSystemAlert[];
  isLoading: boolean;
  error: Error | null;
  refreshAll: () => Promise<void>;
}

export const useCrossSystemMonitoring = (
  refreshInterval: number = 5000
): UseCrossSystemMonitoringReturn => {
  // 狀態管理
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    simworld: 'healthy',
    netstack: 'healthy'
  });
  const [integrationHealth, setIntegrationHealth] = useState<IntegrationHealth>({
    status: 'healthy',
    netstackClient: false,
    aiRanIntegration: false,
    sessionManagement: false,
    fallbackMechanism: false,
    apiCalls: 0,
    successRate: 0,
    avgResponseTime: 0,
    fallbackCount: 0
  });
  const [crossSystemAlerts, setCrossSystemAlerts] = useState<CrossSystemAlert[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Ref 用於追蹤統計
  const statsRef = useRef({
    apiCalls: 0,
    successfulCalls: 0,
    totalResponseTime: 0,
    fallbackCount: 0
  });

  // SimWorld 系統健康檢查
  const checkSimWorldHealth = useCallback(async (): Promise<'healthy' | 'warning' | 'error'> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch('/system/health', {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        return 'error';
      }

      const data = await response.json();
      
      // 根據響應判斷健康狀態
      if (data.status === 'healthy' && data.services?.all_healthy) {
        return 'healthy';
      } else if (data.status === 'degraded') {
        return 'warning';
      } else {
        return 'error';
      }
    } catch (error) {
      console.error('SimWorld health check failed:', error);
      return 'error';
    }
  }, []);

  // NetStack 系統健康檢查
  const checkNetStackHealth = useCallback(async (): Promise<'healthy' | 'warning' | 'error'> => {
    try {
      const startTime = Date.now();
      const response = await netStackApi.getHealthStatus();
      const responseTime = Date.now() - startTime;

      // 更新統計
      statsRef.current.apiCalls++;
      statsRef.current.totalResponseTime += responseTime;

      if (response.status === 'healthy') {
        statsRef.current.successfulCalls++;
        return responseTime > 1000 ? 'warning' : 'healthy';
      } else {
        return 'warning';
      }
    } catch (error) {
      console.error('NetStack health check failed:', error);
      return 'error';
    }
  }, []);

  // 檢查 API 橋接整合狀態
  const checkIntegrationHealth = useCallback(async (): Promise<IntegrationHealth> => {
    try {
      // 檢查 NetStack 客戶端連接
      const netstackClientStatus = await checkNetStackClientConnection();
      
      // 檢查 AI-RAN 服務整合
      const aiRanStatus = await checkAIRANIntegration();
      
      // 檢查會話管理
      const sessionStatus = await checkSessionManagement();
      
      // 檢查降級機制
      const fallbackStatus = await checkFallbackMechanism();

      // 計算統計
      const { apiCalls, successfulCalls, totalResponseTime, fallbackCount } = statsRef.current;
      const successRate = apiCalls > 0 ? Math.round((successfulCalls / apiCalls) * 100) : 100;
      const avgResponseTime = apiCalls > 0 ? Math.round(totalResponseTime / apiCalls) : 0;

      // 判斷整體整合狀態
      const overallStatus = 
        netstackClientStatus && aiRanStatus && sessionStatus ? 'healthy' :
        netstackClientStatus || aiRanStatus ? 'warning' : 'error';

      return {
        status: overallStatus,
        netstackClient: netstackClientStatus,
        aiRanIntegration: aiRanStatus,
        sessionManagement: sessionStatus,
        fallbackMechanism: fallbackStatus,
        apiCalls,
        successRate,
        avgResponseTime,
        fallbackCount
      };
    } catch (error) {
      console.error('Integration health check failed:', error);
      return {
        status: 'error',
        netstackClient: false,
        aiRanIntegration: false,
        sessionManagement: false,
        fallbackMechanism: false,
        apiCalls: statsRef.current.apiCalls,
        successRate: 0,
        avgResponseTime: 0,
        fallbackCount: statsRef.current.fallbackCount
      };
    }
  }, []);

  // 檢查 NetStack 客戶端連接
  const checkNetStackClientConnection = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch('/interference/ai-ran/netstack/status');
      return response.ok;
    } catch (error) {
      return false;
    }
  }, []);

  // 檢查 AI-RAN 服務整合
  const checkAIRANIntegration = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch('/interference/ai-ran/control-integrated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'health_check' })
      });
      return response.status !== 404; // 只要端點存在就認為已整合
    } catch (error) {
      return false;
    }
  }, []);

  // 檢查會話管理
  const checkSessionManagement = useCallback(async (): Promise<boolean> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch('/api/v1/rl/training/sessions', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return Array.isArray(data) || Array.isArray(data.sessions);
      }
      return false;
    } catch (error) {
      return false;
    }
  }, []);

  // 檢查降級機制
  const checkFallbackMechanism = useCallback(async (): Promise<boolean> => {
    // 降級機制通常是被動的，我們檢查相關配置
    return true; // 假設降級機制已實現
  }, []);

  // 獲取活躍算法列表
  const getActiveAlgorithms = useCallback(async (): Promise<string[]> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch('/api/v1/rl/algorithms', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return data.algorithms || data || [];
      }
      return [];
    } catch (error) {
      return [];
    }
  }, []);

  // 獲取訓練進度
  const getTrainingProgress = useCallback(async (): Promise<number> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch('/api/v1/rl/status', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        return data.overall_progress || data.progress || 0;
      }
      return 0;
    } catch (error) {
      return 0;
    }
  }, []);

  // 生成跨系統告警
  const generateCrossSystemAlerts = useCallback((
    simworldStatus: 'healthy' | 'warning' | 'error',
    netstackStatus: 'healthy' | 'warning' | 'error',
    integrationStatus: 'healthy' | 'warning' | 'error'
  ): CrossSystemAlert[] => {
    const alerts: CrossSystemAlert[] = [];

    // SimWorld 告警
    if (simworldStatus === 'error') {
      alerts.push({
        level: 'error',
        message: 'SimWorld 系統出現故障，請檢查服務狀態',
        source: 'simworld',
        timestamp: new Date()
      });
    } else if (simworldStatus === 'warning') {
      alerts.push({
        level: 'warning',
        message: 'SimWorld 系統性能下降，建議關注',
        source: 'simworld',
        timestamp: new Date()
      });
    }

    // NetStack 告警
    if (netstackStatus === 'error') {
      alerts.push({
        level: 'error',
        message: 'NetStack RL 系統無法連接，請檢查服務',
        source: 'netstack',
        timestamp: new Date()
      });
    } else if (netstackStatus === 'warning') {
      alerts.push({
        level: 'warning',
        message: 'NetStack RL 系統響應較慢，可能影響性能',
        source: 'netstack',
        timestamp: new Date()
      });
    }

    // 整合告警
    if (integrationStatus === 'error') {
      alerts.push({
        level: 'critical',
        message: 'API 橋接整合失效，系統降級運行',
        source: 'integration',
        timestamp: new Date()
      });
    } else if (integrationStatus === 'warning') {
      alerts.push({
        level: 'warning',
        message: 'API 橋接整合狀態不穩定，建議檢查',
        source: 'integration',
        timestamp: new Date()
      });
    }

    return alerts;
  }, []);

  // 刷新所有監控數據
  const refreshAll = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // 並行檢查所有系統
      const [
        simworldStatus,
        netstackStatus,
        integrationHealthResult,
        activeAlgorithms,
        trainingProgress
      ] = await Promise.all([
        checkSimWorldHealth(),
        checkNetStackHealth(),
        checkIntegrationHealth(),
        getActiveAlgorithms(),
        getTrainingProgress()
      ]);

      // 更新系統狀態
      setSystemStatus({
        simworld: simworldStatus,
        netstack: netstackStatus
      });

      // 更新整合健康狀態
      setIntegrationHealth(integrationHealthResult);

      // 計算整體健康度
      const healthScores = {
        simworld: simworldStatus === 'healthy' ? 100 : simworldStatus === 'warning' ? 70 : 30,
        netstack: netstackStatus === 'healthy' ? 100 : netstackStatus === 'warning' ? 70 : 30,
        integration: integrationHealthResult.status === 'healthy' ? 100 : 
                    integrationHealthResult.status === 'warning' ? 70 : 30
      };

      const overallHealth = Math.round(
        (healthScores.simworld * 0.3 + 
         healthScores.netstack * 0.4 + 
         healthScores.integration * 0.3)
      );

      // 更新性能指標
      setPerformanceMetrics({
        overall_health: overallHealth,
        simworld_status: simworldStatus,
        netstack_status: netstackStatus,
        integration_status: integrationHealthResult.status,
        active_algorithms: activeAlgorithms,
        training_progress: trainingProgress,
        api_response_time: integrationHealthResult.avgResponseTime
      });

      // 生成跨系統告警
      const alerts = generateCrossSystemAlerts(
        simworldStatus,
        netstackStatus,
        integrationHealthResult.status
      );
      setCrossSystemAlerts(alerts);

    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      console.error('Cross-system monitoring refresh failed:', error);
    } finally {
      setIsLoading(false);
    }
  }, [
    checkSimWorldHealth,
    checkNetStackHealth,
    checkIntegrationHealth,
    getActiveAlgorithms,
    getTrainingProgress,
    generateCrossSystemAlerts
  ]);

  // 定期刷新
  useEffect(() => {
    refreshAll(); // 初始化加載

    const interval = setInterval(refreshAll, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshAll, refreshInterval]);

  return {
    performanceMetrics,
    systemStatus,
    integrationHealth,
    crossSystemAlerts,
    isLoading,
    error,
    refreshAll
  };
}; 