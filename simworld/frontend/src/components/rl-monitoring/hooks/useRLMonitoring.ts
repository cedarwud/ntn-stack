/**
 * 增強版 RL 監控 Hook
 * 整合現有功能並添加 Phase 3 視覺化支援
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { apiClient } from '../../../services/api-client';
import { 
  RLMonitoringData, 
  RLMonitoringOptions, 
  TrainingStartEvent,
  AlgorithmSwitchEvent,
  DataUpdateEvent,
  ErrorEvent
} from '../types/rl-monitoring.types';

// 創建簡單的 EventEmitter
class SimpleEventEmitter<T> {
  private listeners: ((data: T) => void)[] = [];

  on(listener: (data: T) => void) {
    this.listeners.push(listener);
  }

  off(listener: (data: T) => void) {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  emit(data: T) {
    this.listeners.forEach(listener => listener(data));
  }
}

// 創建全局事件發射器
export const rlMonitoringEvents = {
  onTrainingStart: new SimpleEventEmitter<TrainingStartEvent>(),
  onAlgorithmSwitch: new SimpleEventEmitter<AlgorithmSwitchEvent>(),
  onDataUpdate: new SimpleEventEmitter<DataUpdateEvent>(),
  onError: new SimpleEventEmitter<ErrorEvent>()
};

/**
 * 增強版 RL 監控 Hook
 */
export const useRLMonitoring = (options: RLMonitoringOptions) => {
  const { refreshInterval = 2000, enabled = true, autoStart = false } = options;

  // 基礎狀態
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // 訓練狀態
  const [isDqnTraining, setIsDqnTraining] = useState(false);
  const [isPpoTraining, setIsPpoTraining] = useState(false);
  const [isSacTraining, setIsSacTraining] = useState(false);

  // 數據狀態
  const [rlData, setRlData] = useState<RLMonitoringData>({
    training: {
      status: 'idle',
      progress: 0,
      currentEpisode: 0,
      totalEpisodes: 30,
      algorithms: []
    },
    algorithms: {
      comparison: {
        algorithms: [],
        performance_metrics: {
          reward_comparison: {},
          convergence_analysis: {},
          statistical_significance: {}
        }
      },
      performance: {
        latency: 0,
        success_rate: 0,
        throughput: 0,
        error_rate: 0,
        response_time: 0,
        resource_utilization: {
          cpu: 0,
          memory: 0
        }
      },
      ranking: []
    },
    visualization: {
      featureImportance: {
        type: 'feature_importance',
        format: 'json',
        data: {}
      },
      decisionExplanation: {
        decision_id: '',
        algorithm: '',
        input_features: {},
        output_action: null,
        confidence: 0,
        reasoning: {
          feature_importance: {},
          decision_path: []
        },
        timestamp: ''
      },
      algorithmComparison: {
        algorithms: [],
        metrics: {}
      }
    },
    realtime: {
      metrics: {
        timestamp: '',
        system_status: 'healthy',
        active_algorithms: [],
        resource_usage: {
          cpu_percent: 0,
          memory_percent: 0
        },
        performance_indicators: {
          avg_response_time: 0,
          success_rate: 0,
          error_count: 0
        }
      },
      events: [],
      status: {
        overall_health: 'healthy',
        services: {},
        last_updated: '',
        uptime: 0,
        error_logs: []
      }
    },
    research: {
      experiments: [],
      baseline: {
        baseline_algorithms: [],
        comparison_metrics: {},
        statistical_tests: {},
        improvement_percentage: {}
      },
      statistics: {
        descriptive_stats: {},
        correlation_matrix: {},
        confidence_intervals: {},
        trend_analysis: {}
      }
    }
  });

  // 追蹤狀態
  const lastStateRef = useRef<Record<string, boolean>>({
    dqn: false,
    ppo: false,
    sac: false
  });
  
  // 追蹤進度變化
  const lastProgressRef = useRef({ 
    dqn: { progress: 0, episodes: 0 }, 
    ppo: { progress: 0, episodes: 0 }, 
    sac: { progress: 0, episodes: 0 } 
  });

  const recentlyStartedRef = useRef<Map<string, number>>(new Map());

  // API 調用函數
  const startTraining = useCallback(async (
    algorithm: string, 
    config: { episodes: number; batch_size?: number; learning_rate?: number }
  ) => {
    try {
      console.log(`🚀 Starting training for ${algorithm}...`);
      
      const response = await apiClient.controlTraining('start', algorithm.toLowerCase());
      console.log(`✅ Successfully started training for ${algorithm}`, response);
      
      // 記錄啟動時間
      recentlyStartedRef.current.set(algorithm.toLowerCase(), Date.now());
      
      // 發射事件
      rlMonitoringEvents.onTrainingStart.emit({
        algorithm,
        config,
        timestamp: new Date().toISOString()
      });
      
      return response;
    } catch (error) {
      console.error(`❌ Failed to start training for ${algorithm}:`, error);
      rlMonitoringEvents.onError.emit({
        error_type: 'training_start_failed',
        message: `Failed to start training for ${algorithm}`,
        component: 'useRLMonitoring',
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }, []);

  const stopTraining = useCallback(async (algorithm: string) => {
    try {
      console.log(`🛑 Stopping training for ${algorithm}...`);
      
      const response = await apiClient.controlTraining('stop', algorithm.toLowerCase());
      console.log(`✅ Successfully stopped training for ${algorithm}`, response);
      
      // 移除啟動標記
      recentlyStartedRef.current.delete(algorithm.toLowerCase());
      
      return response;
    } catch (error) {
      console.error(`❌ Failed to stop training for ${algorithm}:`, error);
      rlMonitoringEvents.onError.emit({
        error_type: 'training_stop_failed',
        message: `Failed to stop training for ${algorithm}`,
        component: 'useRLMonitoring',
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }, []);

  // 數據獲取函數
  const fetchTrainingData = useCallback(async () => {
    if (!enabled) return;
    
    // 只在有狀態變化時記錄日誌，避免無限日誌
    const shouldLog = Math.random() < 0.05; // 只記錄 5% 的請求
    if (shouldLog) {
        console.log(`🔄 [前端監控] 開始獲取訓練數據...`);
    }
    
    try {
      // 避免短暫的 loading 狀態導致抖動
      // setIsLoading(true);
      setError(null);

      if (shouldLog) {
          console.log(`📡 [前端監控] 並行調用多個 API 端點...`);
      }
      // 並行調用多個 API 端點
      const [
        statusSummary,
        trainingSessions,
        performanceReport,
        healthCheck
      ] = await Promise.allSettled([
        apiClient.getTrainingStatusSummary(),
        apiClient.getRLTrainingSessions(),
        apiClient.getTrainingPerformanceMetrics(),
        apiClient.getAIDecisionEngineHealth()
      ]);

      if (shouldLog) {
          console.log(`📊 [前端監控] API 調用結果:`, {
            statusSummary: statusSummary.status,
            trainingSessions: trainingSessions.status,
            performanceReport: performanceReport.status,
            healthCheck: healthCheck.status
          });
      }

      // 處理 Phase 3 視覺化數據
      let visualizationData = null;
      let decisionExplanation = null;
      
      try {
        const [vizGenerate, vizExplain] = await Promise.allSettled([
          fetch('/netstack/api/v1/rl/phase-3/visualizations/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              chart_type: 'feature_importance',
              data_source: 'current_training',
              format: 'plotly'
            })
          }),
          fetch('/netstack/api/v1/rl/phase-3/explain/decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              state: [0.1, 0.2, 0.3, 0.4, 0.5],
              action: 1,
              q_values: [0.8, 0.9, 0.7],
              algorithm: 'dqn',
              episode: 1,
              step: 1,
              include_reasoning: true
            })
          })
        ]);

        if (vizGenerate.status === 'fulfilled' && vizGenerate.value.ok) {
          visualizationData = await vizGenerate.value.json();
        }
        
        if (vizExplain.status === 'fulfilled' && vizExplain.value.ok) {
          decisionExplanation = await vizExplain.value.json();
        }
      } catch (vizError) {
        // 只在 10% 的情況下記錄錯誤，避免日誌過多
        if (Math.random() < 0.1) {
          console.warn('Phase 3 visualization APIs not available:', vizError);
        }
      }

      // 處理算法狀態 - 修復數據映射邏輯
      const processAlgorithmStatus = (algorithm: string) => {
        const sessionData = trainingSessions.status === 'fulfilled' ? trainingSessions.value : null;
        const statusData = statusSummary.status === 'fulfilled' ? statusSummary.value : null;
        
        const activeSession = sessionData?.active_sessions?.find(
          (session: { algorithm?: string; status?: string }) => session.algorithm?.toLowerCase() === algorithm.toLowerCase() && session.status === 'running'
        );
        
        const algorithmData = statusData?.algorithms?.[algorithm] || statusData?.[algorithm] || null;
        
        // 從 algorithmData 提取訓練進度數據
        const trainingProgress = algorithmData?.training_progress || {};
        const metricsData = algorithmData?.metrics || {};
        
        // 修復數據映射邏輯，使用正確的字段名
        return {
          is_training: !!activeSession || (algorithmData?.status === 'running') || (algorithmData?.is_training === true),
          status: activeSession?.status || algorithmData?.status || 'idle',
          progress: (trainingProgress.progress_percentage || 0) / 100, // 將百分比轉換為小數
          metrics: {
            episodes_completed: trainingProgress.current_episode || metricsData.episodes_completed || 0,
            total_episodes: trainingProgress.total_episodes || metricsData.episodes_target || 30,
            average_reward: trainingProgress.current_reward || metricsData.current_reward || 0,
            current_reward: trainingProgress.current_reward || metricsData.current_reward || 0,
            best_reward: trainingProgress.best_reward || metricsData.best_reward || 0,
            success_rate: 0.85, // 模擬數據
            convergence_speed: 0.7, // 模擬數據
            stability: 0.9, // 模擬數據
            ...activeSession?.metrics,
            ...metricsData
          }
        };
      };

      const dqnStatus = processAlgorithmStatus('dqn');
      const ppoStatus = processAlgorithmStatus('ppo');
      const sacStatus = processAlgorithmStatus('sac');

      if (shouldLog) {
          console.log(`🧮 [前端監控] 算法狀態處理結果:`, {
            dqn: { is_training: dqnStatus.is_training, status: dqnStatus.status, progress: dqnStatus.progress },
            ppo: { is_training: ppoStatus.is_training, status: ppoStatus.status, progress: ppoStatus.progress },
            sac: { is_training: sacStatus.is_training, status: sacStatus.status, progress: sacStatus.progress }
          });
      }

      // 更新狀態
      const newDqnState = dqnStatus.is_training;
      const newPpoState = ppoStatus.is_training;
      const newSacState = sacStatus.is_training;

      // 檢查狀態變化和進度變化
      const currentState = { dqn: newDqnState, ppo: newPpoState, sac: newSacState };
      const hasStateChanged = 
        currentState.dqn !== lastStateRef.current.dqn ||
        currentState.ppo !== lastStateRef.current.ppo ||
        currentState.sac !== lastStateRef.current.sac;

      // 檢查進度數據變化
      const currentProgress = {
        dqn: { progress: dqnStatus.progress, episodes: dqnStatus.metrics.episodes_completed },
        ppo: { progress: ppoStatus.progress, episodes: ppoStatus.metrics.episodes_completed },
        sac: { progress: sacStatus.progress, episodes: sacStatus.metrics.episodes_completed }
      };

      const hasProgressChanged = 
        JSON.stringify(currentProgress) !== JSON.stringify(lastProgressRef.current);

      if (hasStateChanged || hasProgressChanged || shouldLog) {
          console.log(`📈 [前端監控] 狀態比較:`, {
            previous: lastStateRef.current,
            current: currentState,
            hasChanged: hasStateChanged
          });
          console.log(`📊 [前端監控] 進度比較:`, {
            previous: lastProgressRef.current,
            current: currentProgress,
            hasProgressChanged: hasProgressChanged
          });
      }

      if (hasStateChanged || hasProgressChanged) {
        console.log('🔄 [前端監控] Training state changed:', currentState);
        console.log('📊 [前端監控] Training progress changed:', currentProgress);
        
        // 發射狀態變化事件
        rlMonitoringEvents.onDataUpdate.emit({
          type: 'training',
          data: { state: currentState, progress: currentProgress },
          timestamp: new Date().toISOString()
        });
      }

      lastStateRef.current = currentState;
      lastProgressRef.current = currentProgress;

      // 更新組件狀態
      if (hasStateChanged || shouldLog) {
          console.log(`🔧 [前端監控] 更新組件狀態:`, { dqn: newDqnState, ppo: newPpoState, sac: newSacState });
      }
      setIsDqnTraining(newDqnState);
      setIsPpoTraining(newPpoState);
      setIsSacTraining(newSacState);

      // 構建完整的 RL 監控數據
      const algorithmsArray = [
        {
          algorithm: 'dqn',
          status: dqnStatus.status,
          progress: dqnStatus.progress || 0,
          current_episode: dqnStatus.metrics.episodes_completed || 0,
          total_episodes: dqnStatus.metrics.total_episodes || 30,
          average_reward: dqnStatus.metrics.average_reward || 0,
          training_active: newDqnState,
          metrics: {
            ...dqnStatus.metrics,
            success_rate: 0.85,
            convergence_speed: 0.7,
            stability: 0.9
          }
        },
        {
          algorithm: 'ppo',
          status: ppoStatus.status,
          progress: ppoStatus.progress || 0,
          current_episode: ppoStatus.metrics.episodes_completed || 0,
          total_episodes: ppoStatus.metrics.total_episodes || 30,
          average_reward: ppoStatus.metrics.average_reward || 0,
          training_active: newPpoState,
          metrics: {
            ...ppoStatus.metrics,
            success_rate: 0.78,
            convergence_speed: 0.6,
            stability: 0.8
          }
        },
        {
          algorithm: 'sac',
          status: sacStatus.status,
          progress: sacStatus.progress || 0,
          current_episode: sacStatus.metrics.episodes_completed || 0,
          total_episodes: sacStatus.metrics.total_episodes || 30,
          average_reward: sacStatus.metrics.average_reward || 0,
          training_active: newSacState,
          metrics: {
            ...sacStatus.metrics,
            success_rate: 0.82,
            convergence_speed: 0.8,
            stability: 0.75
          }
        }
      ];
      
      // Algorithms array construction complete
      
      const newRlData: RLMonitoringData = {
        training: {
          status: newDqnState || newPpoState || newSacState ? 'running' : 'idle',
          progress: Math.max(
            dqnStatus.progress || 0,
            ppoStatus.progress || 0,
            sacStatus.progress || 0
          ),
          currentEpisode: Math.max(
            dqnStatus.metrics.episodes_completed || 0,
            ppoStatus.metrics.episodes_completed || 0,
            sacStatus.metrics.episodes_completed || 0
          ),
          totalEpisodes: 30,
          algorithms: algorithmsArray
        },
        algorithms: {
          comparison: {
            algorithms: [dqnStatus, ppoStatus, sacStatus].map((status, index) => ({
              algorithm: (['dqn', 'ppo', 'sac'][index]) as 'dqn' | 'ppo' | 'sac',
              status: status.status,
              progress: status.progress || 0,
              current_episode: status.metrics.episodes_completed || 0,
              total_episodes: status.metrics.total_episodes || 30,
              average_reward: status.metrics.average_reward || 0,
              training_active: status.is_training,
              metrics: status.metrics
            })),
            performance_metrics: {
              reward_comparison: {
                dqn: dqnStatus.metrics.average_reward || 0,
                ppo: ppoStatus.metrics.average_reward || 0,
                sac: sacStatus.metrics.average_reward || 0
              },
              convergence_analysis: {},
              statistical_significance: {}
            }
          },
          performance: performanceReport.status === 'fulfilled' ? performanceReport.value : rlData.algorithms.performance,
          ranking: [
            { algorithm: 'dqn', rank: 1, score: dqnStatus.metrics.average_reward || 0, metrics: { reward: dqnStatus.metrics.average_reward || 0, convergence_speed: 0, stability: 0, efficiency: 0 }},
            { algorithm: 'ppo', rank: 2, score: ppoStatus.metrics.average_reward || 0, metrics: { reward: ppoStatus.metrics.average_reward || 0, convergence_speed: 0, stability: 0, efficiency: 0 }},
            { algorithm: 'sac', rank: 3, score: sacStatus.metrics.average_reward || 0, metrics: { reward: sacStatus.metrics.average_reward || 0, convergence_speed: 0, stability: 0, efficiency: 0 }}
          ].sort((a, b) => b.score - a.score).map((item, index) => ({ ...item, rank: index + 1 }))
        },
        visualization: {
          featureImportance: visualizationData || rlData.visualization.featureImportance,
          decisionExplanation: decisionExplanation || rlData.visualization.decisionExplanation,
          algorithmComparison: {
            algorithms: ['dqn', 'ppo', 'sac'],
            metrics: {
              dqn: { reward: dqnStatus.metrics.average_reward || 0, episodes: dqnStatus.metrics.episodes_completed || 0 },
              ppo: { reward: ppoStatus.metrics.average_reward || 0, episodes: ppoStatus.metrics.episodes_completed || 0 },
              sac: { reward: sacStatus.metrics.average_reward || 0, episodes: sacStatus.metrics.episodes_completed || 0 }
            }
          }
        },
        realtime: {
          metrics: {
            timestamp: new Date().toISOString(),
            system_status: healthCheck.status === 'fulfilled' ? 'healthy' : 'warning',
            active_algorithms: [
              ...(newDqnState ? ['dqn'] : []),
              ...(newPpoState ? ['ppo'] : []),
              ...(newSacState ? ['sac'] : [])
            ],
            resource_usage: {
              cpu_percent: 0,
              memory_percent: 0
            },
            performance_indicators: {
              avg_response_time: 0,
              success_rate: 0,
              error_count: 0
            }
          },
          events: [],
          status: {
            overall_health: 'healthy',
            services: {},
            last_updated: new Date().toISOString(),
            uptime: 0,
            error_logs: []
          }
        },
        research: rlData.research // 保持現有的研究數據
      };

      setRlData(newRlData);
      setLastUpdated(new Date());

      // 發射數據更新事件
      rlMonitoringEvents.onDataUpdate.emit({
        type: 'realtime',
        data: newRlData,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('Failed to fetch RL monitoring data:', error);
      setError(error as Error);
      
      rlMonitoringEvents.onError.emit({
        error_type: 'data_fetch_failed',
        message: (error as Error).message,
        component: 'useRLMonitoring',
        timestamp: new Date().toISOString()
      });
    } finally {
      // setIsLoading(false);
    }
  }, [enabled]);

  // 控制函數
  const toggleDqnTraining = useCallback(async () => {
    try {
      if (!isDqnTraining) {
        await startTraining('dqn', { episodes: 30, batch_size: 32, learning_rate: 0.001 });
      } else {
        await stopTraining('dqn');
      }
      setTimeout(fetchTrainingData, 1000);
    } catch (error) {
      console.error('Toggle DQN training failed:', error);
    }
  }, [isDqnTraining, startTraining, stopTraining, fetchTrainingData]);

  const togglePpoTraining = useCallback(async () => {
    try {
      if (!isPpoTraining) {
        await startTraining('ppo', { episodes: 30, batch_size: 32, learning_rate: 0.001 });
      } else {
        await stopTraining('ppo');
      }
      setTimeout(fetchTrainingData, 1000);
    } catch (error) {
      console.error('Toggle PPO training failed:', error);
    }
  }, [isPpoTraining, startTraining, stopTraining, fetchTrainingData]);

  const toggleSacTraining = useCallback(async () => {
    try {
      if (!isSacTraining) {
        await startTraining('sac', { episodes: 30, batch_size: 32, learning_rate: 0.001 });
      } else {
        await stopTraining('sac');
      }
      setTimeout(fetchTrainingData, 1000);
    } catch (error) {
      console.error('Toggle SAC training failed:', error);
    }
  }, [isSacTraining, startTraining, stopTraining, fetchTrainingData]);

  // 工具函數
  const utils = useMemo(() => ({
    exportData: async (_format: 'json' | 'csv' | 'excel') => {
      const dataStr = JSON.stringify(rlData, null, 2);
      return new Blob([dataStr], { type: 'application/json' });
    },
    resetMonitoring: async () => {
      setRlData({
        training: { status: 'idle', progress: 0, currentEpisode: 0, totalEpisodes: 30, algorithms: [] },
        algorithms: { comparison: { algorithms: [], performance_metrics: { reward_comparison: {}, convergence_analysis: {}, statistical_significance: {} }}, performance: { latency: 0, success_rate: 0, throughput: 0, error_rate: 0, response_time: 0, resource_utilization: { cpu: 0, memory: 0 }}, ranking: [] },
        visualization: { featureImportance: { type: 'feature_importance' as const, format: 'json' as const, data: {} }, decisionExplanation: { decision_id: '', algorithm: '', input_features: {}, output_action: null, confidence: 0, reasoning: { feature_importance: {}, decision_path: [] }, timestamp: '' }, algorithmComparison: { algorithms: [], metrics: {} }},
        realtime: { metrics: { timestamp: '', system_status: 'healthy' as const, active_algorithms: [], resource_usage: { cpu_percent: 0, memory_percent: 0 }, performance_indicators: { avg_response_time: 0, success_rate: 0, error_count: 0 }}, events: [], status: { overall_health: 'healthy' as const, services: {}, last_updated: '', uptime: 0, error_logs: [] }},
        research: { experiments: [], baseline: { baseline_algorithms: [], comparison_metrics: {}, statistical_tests: {}, improvement_percentage: {} }, statistics: { descriptive_stats: {}, correlation_matrix: {}, confidence_intervals: {}, trend_analysis: {} }}
      });
    },
    switchAlgorithm: async (algorithm: string) => {
      // 實現算法切換邏輯
      console.log(`Switching to algorithm: ${algorithm}`);
    }
  }), [rlData]);

  // 定期數據獲取
  useEffect(() => {
    if (!enabled) return;

    fetchTrainingData(); // 立即執行一次
    const interval = setInterval(fetchTrainingData, refreshInterval);

    return () => clearInterval(interval);
  }, [enabled, refreshInterval, fetchTrainingData]);

  // 自動啟動
  useEffect(() => {
    if (autoStart && enabled) {
      // 自動啟動邏輯
    }
  }, [autoStart, enabled]);

  return {
    // 狀態
    isLoading,
    error,
    lastUpdated,
    
    // 舊版兼容性
    isDqnTraining,
    isPpoTraining,
    isSacTraining,
    
    // 新版數據
    data: rlData,
    
    // 控制函數
    toggleDqnTraining,
    togglePpoTraining,
    toggleSacTraining,
    startTraining,
    stopTraining,
    
    // 工具函數
    utils,
    
    // 數據刷新
    refresh: fetchTrainingData,
    
    // 事件系統
    events: rlMonitoringEvents,
    
    // 分解數據訪問器（為了向後兼容）
    training: rlData.training,
    algorithms: rlData.algorithms,
    visualization: rlData.visualization,
    realtime: rlData.realtime,
    research: rlData.research
  };
};