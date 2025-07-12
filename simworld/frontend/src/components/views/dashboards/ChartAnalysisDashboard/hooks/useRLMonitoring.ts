/**
 * RL監控Hook
 * 抽取自 FullChartAnalysisDashboard.tsx 的RL監控邏輯
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { createInitialRLData, createInitialPolicyLossData, createInitialTrainingMetrics } from '../../../../../utils/mockDataGenerator'
import { apiClient } from '../../../../../services/api-client'

// 定義訓練配置的類型
interface TrainingConfig {
  episodes: number;
  batch_size?: number;
  learning_rate?: number;
}

// 定義後端狀態 API 的回傳類型
interface StatusResponse {
  algorithm: string;
  status: 'running' | 'completed' | 'not_found' | { status: 'completed', result: any };
}


/**
 * RL訓練狀態和數據管理Hook
 */
export const useRLMonitoring = (enabled: boolean = true) => {
  // 調試標志 - 設置為 false 來禁用調試日誌
  const DEBUG_ENABLED = false;
  
  // RL監控相關狀態
  const [isDqnTraining, setIsDqnTraining] = useState(false)
  const [isPpoTraining, setIsPpoTraining] = useState(false)
  const [isSacTraining, setIsSacTraining] = useState(false)
  
  // 跟蹤剛啟動的訓練 - 改進的解決方案
  const recentlyStartedRef = useRef<Map<string, number>>(new Map()) // 使用 Map 来跟踪启动时间
  const lastEpisodesRef = useRef<Record<string, number>>({
    dqn: 0,
    ppo: 0,
    sac: 0
  })
  
  // 跟蹤上次的狀態，避免重複日誌
  const lastStateRef = useRef<Record<string, boolean>>({
    dqn: false,
    ppo: false,
    sac: false
  })
  const [trainingMetrics, setTrainingMetrics] = useState(createInitialTrainingMetrics())

  const [rewardTrendData, setRewardTrendData] = useState(createInitialRLData())
  const [policyLossData, setPolicyLossData] = useState(createInitialPolicyLossData())

  // 後端 API 函數
  const startTraining = async (algorithm: string, config: TrainingConfig) => {
    try {
      console.log(`🚀 Starting training API call for ${algorithm}...`);
      console.log('🔍 Training request payload:', {
        action: "start",
        algorithm: algorithm.toLowerCase(),
        config: config
      });
      
      // 使用增強版RL訓練端點，這個端點真正會啟動訓練
      const response = await apiClient.post(`/api/v1/rl/enhanced/start/${algorithm.toLowerCase()}`, {
        total_episodes: config.episodes || 50, // 减少episode数量
        step_time: 1.0, // 增加到1秒每episode，让用户能看到进度
        experiment_name: `${algorithm.toLowerCase()}_training_${Date.now()}`,
        scenario_type: "handover_simulation",
        researcher_id: "frontend_user"
      });
      
      console.log(`✅ Successfully started training for ${algorithm}`, response);
      console.log('🔍 Training start response analysis:', {
        status: (response as any).status,
        algorithm: (response as any).algorithm,
        training_active: (response as any).training_active,
        message: (response as any).message,
        fullResponse: response
      });
      
      // 标记为最近启动的训练，记录启动时间
      recentlyStartedRef.current.set(algorithm.toLowerCase(), Date.now());
      console.log(`🕐 Training ${algorithm} marked as recently started at ${new Date().toISOString()}`);
      
      // 移除調試代碼，使用正常的狀態輪詢
      
    } catch (error) {
      console.error(`❌ Failed to start training for ${algorithm}:`, error);
      throw error; // 向上拋出錯誤，讓調用者可以處理
    }
  };

  const stopTraining = async (algorithm: string) => {
    try {
      console.log(`🛑 Stopping training API call for ${algorithm}...`);
      // 使用增強版RL訓練停止端點
      const response = await apiClient.post(`/api/v1/rl/enhanced/stop/${algorithm.toLowerCase()}`);
      console.log(`✅ Successfully stopped training for ${algorithm}`, response);
      console.log('🔍 Training stop response analysis:', {
        status: (response as any).status,
        algorithm: (response as any).algorithm,
        message: (response as any).message,
        fullResponse: response
      });
      
      // 移除最近启动的标记
      recentlyStartedRef.current.delete(algorithm.toLowerCase());
      console.log(`🕐 Training ${algorithm} removed from recently started list`);
      
    } catch (error) {
      console.error(`❌ Failed to stop training for ${algorithm}:`, error);
    }
  };


  // 統一的數據獲取函數
  const fetchTrainingData = async () => {
    if (!enabled) return; // 如果未啟用，直接返回
    
    try {
      // 使用增強版RL訓練狀態端點來獲取真實的訓練狀態
      // 由於我們需要檢查三種算法，並行調用三個端點
      const [dqnResponse, ppoResponse, sacResponse] = await Promise.allSettled([
        apiClient.get<any>(`/api/v1/rl/enhanced/status/dqn`),
        apiClient.get<any>(`/api/v1/rl/enhanced/status/ppo`),
        apiClient.get<any>(`/api/v1/rl/enhanced/status/sac`)
      ]);
      
      // 處理三個算法的響應
      const getStatusFromResponse = (response: any) => {
        if (response.status === 'fulfilled') {
          const data = response.value;
          return {
            is_training: data.is_training || false,
            status: data.status || 'idle',
            training_progress: data.training_progress,
            metrics: data.metrics
          };
        }
        return {
          is_training: false,
          status: 'error',
          training_progress: null,
          metrics: null
        };
      };

      const dqnStatus = getStatusFromResponse(dqnResponse);
      const ppoStatus = getStatusFromResponse(ppoResponse);
      const sacStatus = getStatusFromResponse(sacResponse);

      // 更新訓練狀態 - 直接使用API返回的真實狀態
      const newDqnState = dqnStatus.is_training;
      const newPpoState = ppoStatus.is_training;
      const newSacState = sacStatus.is_training;
      
      // 只有状态真正变化时才记录日志
      const currentState = { dqn: newDqnState, ppo: newPpoState, sac: newSacState };
      const hasStateChanged = 
        currentState.dqn !== lastStateRef.current.dqn ||
        currentState.ppo !== lastStateRef.current.ppo ||
        currentState.sac !== lastStateRef.current.sac;
      
      if (hasStateChanged) {
        console.log('🔄 Training state changed:', {
          states: currentState,
          dqnStatus: dqnStatus.status,
          ppoStatus: ppoStatus.status,
          sacStatus: sacStatus.status
        });
      }
      
      // 只在狀態變化時顯示API響應（避免無限日誌）
      if (hasStateChanged) {
        console.log('🔍 API Responses:', {
          dqn: { status: dqnStatus.status, is_training: dqnStatus.is_training, hasMetrics: !!dqnStatus.metrics },
          ppo: { status: ppoStatus.status, is_training: ppoStatus.is_training, hasMetrics: !!ppoStatus.metrics },
          sac: { status: sacStatus.status, is_training: sacStatus.is_training, hasMetrics: !!sacStatus.metrics }
        });
      }
      
      lastStateRef.current = currentState;
      
      setIsDqnTraining(newDqnState);
      setIsPpoTraining(newPpoState);
      setIsSacTraining(newSacState);
      
      // 更新訓練指標 - 處理每個算法的數據
      setTrainingMetrics(prevMetrics => {
        const newMetrics = { ...prevMetrics };
        
        // 更新DQN指標 - 使用真實後端數據
        if (dqnStatus.metrics) {
          // 確保最終狀態顯示：如果episodes等於total_episodes，顯示100%
          const episodes = dqnStatus.metrics.episodes_completed || 0;
          const totalEpisodes = dqnStatus.metrics.total_episodes || 30;
          const calculatedProgress = totalEpisodes > 0 ? (episodes / totalEpisodes) * 100 : 0;
          const displayProgress = episodes >= totalEpisodes ? 100 : (dqnStatus.training_progress?.progress || calculatedProgress);
          
          newMetrics.dqn = {
            episodes: episodes,
            avgReward: dqnStatus.metrics.average_reward || 0,
            progress: displayProgress,
            // 使用真實的訓練指標，如果後端沒有提供則使用合理的計算值
            handoverDelay: dqnStatus.metrics.handover_delay || (100 - (dqnStatus.metrics.progress || 0)) * 2, // 基於進度計算
            successRate: dqnStatus.metrics.success_rate || Math.max(0, Math.min(100, 50 + (dqnStatus.metrics.average_reward || 0) * 10)), // 基於獎勵計算
            signalDropTime: dqnStatus.metrics.signal_drop_time || Math.max(0, 50 - (dqnStatus.metrics.progress || 0) * 0.3), // 基於進度計算
            energyEfficiency: dqnStatus.metrics.energy_efficiency || Math.max(0, Math.min(100, 60 + (dqnStatus.metrics.average_reward || 0) * 5)), // 基於獎勵計算
          };
        }
        
        // 更新PPO指標 - 使用真實後端數據
        if (ppoStatus.metrics) {
          const episodes = ppoStatus.metrics.episodes_completed || 0;
          const totalEpisodes = ppoStatus.metrics.total_episodes || 30;
          const calculatedProgress = totalEpisodes > 0 ? (episodes / totalEpisodes) * 100 : 0;
          const displayProgress = episodes >= totalEpisodes ? 100 : (ppoStatus.training_progress?.progress || calculatedProgress);
          
          newMetrics.ppo = {
            episodes: episodes,
            avgReward: ppoStatus.metrics.average_reward || 0,
            progress: displayProgress,
            // 使用真實的訓練指標，如果後端沒有提供則使用合理的計算值
            handoverDelay: ppoStatus.metrics.handover_delay || (100 - (ppoStatus.metrics.progress || 0)) * 2,
            successRate: ppoStatus.metrics.success_rate || Math.max(0, Math.min(100, 50 + (ppoStatus.metrics.average_reward || 0) * 10)),
            signalDropTime: ppoStatus.metrics.signal_drop_time || Math.max(0, 50 - (ppoStatus.metrics.progress || 0) * 0.3),
            energyEfficiency: ppoStatus.metrics.energy_efficiency || Math.max(0, Math.min(100, 60 + (ppoStatus.metrics.average_reward || 0) * 5)),
          };
        }
        
        // 更新SAC指標 - 使用真實後端數據
        if (sacStatus.metrics) {
          const episodes = sacStatus.metrics.episodes_completed || 0;
          const totalEpisodes = sacStatus.metrics.total_episodes || 30;
          const calculatedProgress = totalEpisodes > 0 ? (episodes / totalEpisodes) * 100 : 0;
          const displayProgress = episodes >= totalEpisodes ? 100 : (sacStatus.training_progress?.progress || calculatedProgress);
          
          newMetrics.sac = {
            episodes: episodes,
            avgReward: sacStatus.metrics.average_reward || 0,
            progress: displayProgress,
            // 使用真實的訓練指標，如果後端沒有提供則使用合理的計算值
            handoverDelay: sacStatus.metrics.handover_delay || (100 - (sacStatus.metrics.progress || 0)) * 2,
            successRate: sacStatus.metrics.success_rate || Math.max(0, Math.min(100, 50 + (sacStatus.metrics.average_reward || 0) * 10)),
            signalDropTime: sacStatus.metrics.signal_drop_time || Math.max(0, 50 - (sacStatus.metrics.progress || 0) * 0.3),
            energyEfficiency: sacStatus.metrics.energy_efficiency || Math.max(0, Math.min(100, 60 + (sacStatus.metrics.average_reward || 0) * 5)),
          };
        }
        
        return newMetrics;
      });
      
      // 更新图表数据 - 分別處理每個正在訓練的算法，只在episodes真正增加時更新
      const updateChartData = (algorithm: string, status: any, isTraining: boolean) => {
        if (!isTraining || !status.metrics) return;
        
        const episodes = status.metrics.episodes_completed || 0;
        const avgReward = status.metrics.average_reward || 0;
        const lastEpisodes = lastEpisodesRef.current[algorithm] || 0;
        
        // 只有當episodes真正增加時才更新圖表，確保同步
        if (episodes <= lastEpisodes) {
          return; // episodes沒有增加，跳過圖表更新
        }
        
        // 更新追蹤的episode數
        lastEpisodesRef.current[algorithm] = episodes;
        
        // 更新奖励趋势数据
        setRewardTrendData(prevData => {
          const newData = { ...prevData };
          
          if (algorithm === 'dqn') {
            newData.dqnData = [...prevData.dqnData, avgReward].slice(-50);
            newData.dqnLabels = [...prevData.dqnLabels, `Episode ${episodes}`].slice(-50);
          } else if (algorithm === 'ppo') {
            newData.ppoData = [...prevData.ppoData, avgReward].slice(-50);
            newData.ppoLabels = [...prevData.ppoLabels, `Episode ${episodes}`].slice(-50);
          } else if (algorithm === 'sac') {
            newData.sacData = [...prevData.sacData, avgReward].slice(-50);
            newData.sacLabels = [...prevData.sacLabels, `Episode ${episodes}`].slice(-50);
          }
          
          // 更新统一标签
          newData.labels = [...prevData.labels, `Episode ${episodes}`].slice(-50);
          
          return newData;
        });
        
        // 更新策略损失数据 - 使用真實後端數據
        setPolicyLossData(prevData => {
          const newData = { ...prevData };
          // 使用真實的損失數據，如果沒有則基於訓練指標計算
          const realLoss = status.metrics?.loss || status.metrics?.training_loss;
          const newLoss = realLoss !== undefined ? realLoss : Math.max(0, 1.0 - (status.metrics?.progress || 0) / 100);
          
          if (algorithm === 'dqn') {
            newData.dqnData = [...prevData.dqnData, newLoss].slice(-50);
          } else if (algorithm === 'ppo') {
            newData.ppoData = [...prevData.ppoData, newLoss].slice(-50);
          } else if (algorithm === 'sac') {
            newData.sacData = [...prevData.sacData, newLoss].slice(-50);
          }
          
          // 更新统一标签
          newData.labels = [...prevData.labels, `Episode ${episodes}`].slice(-50);
          
          return newData;
        });
      };
      
      // 為每個正在訓練的算法更新圖表數據
      updateChartData('dqn', dqnStatus, newDqnState);
      updateChartData('ppo', ppoStatus, newPpoState);
      updateChartData('sac', sacStatus, newSacState);
      
    } catch (error) {
      console.warn('獲取訓練數據失敗:', error);
      // 使用模擬數據作為後備
      setIsDqnTraining(false);
      setIsPpoTraining(false);
      setIsSacTraining(false);
    }
  };

  // 統一的數據獲取 - 只在啟用時運行
  useEffect(() => {
    if (!enabled) return; // 如果未啟用，不啟動輪詢
    
    // 啟動定期數據獲取 - 使用更快的轮询频率以捕获快速训练
    const interval = setInterval(fetchTrainingData, 500); // 改为500ms轮询
    fetchTrainingData(); // 立即執行一次

    return () => {
      clearInterval(interval)
    }
  }, [enabled]) // 依賴於 enabled 參數


  // 控制函數 - 完全依賴後端狀態，不做立即狀態更新
  const toggleDqnTraining = async () => {
    try {
      if (!isDqnTraining) {
        console.log('� Starting DQN training...');
        await startTraining('dqn', { episodes: 30, batch_size: 32, learning_rate: 0.001 });
      } else {
        console.log('� Stopping DQN training...');
        await stopTraining('dqn');
      }
      // 延遲一點時間後再查詢狀態，給後端時間更新
      setTimeout(() => {
        fetchTrainingData();
      }, 1000);
    } catch (error) {
      console.error('❌ Toggle DQN training failed:', error);
    }
  }

  const togglePpoTraining = async () => {
    try {
      if (!isPpoTraining) {
        console.log('� Starting PPO training...');
        await startTraining('ppo', { episodes: 30, batch_size: 32, learning_rate: 0.001 });
      } else {
        console.log('� Stopping PPO training...');
        await stopTraining('ppo');
      }
      // 延遲一點時間後再查詢狀態，給後端時間更新
      setTimeout(() => {
        fetchTrainingData();
      }, 1000);
    } catch (error) {
      console.error('❌ Toggle PPO training failed:', error);
    }
  }

  const toggleSacTraining = async () => {
    try {
      if (!isSacTraining) {
        console.log('� Starting SAC training...');
        await startTraining('sac', { episodes: 30, batch_size: 32, learning_rate: 0.001 });
      } else {
        console.log('� Stopping SAC training...');
        await stopTraining('sac');
      }
      // 延遲一點時間後再查詢狀態，給後端時間更新
      setTimeout(() => {
        fetchTrainingData();
      }, 1000);
    } catch (error) {
      console.error('❌ Toggle SAC training failed:', error);
    }
  }

  return {
    // 狀態
    isDqnTraining,
    isPpoTraining,
    isSacTraining,
    trainingMetrics,
    rewardTrendData,
    policyLossData,
    
    // 控制函數
    toggleDqnTraining,
    togglePpoTraining,
    toggleSacTraining,
    
    // 設置函數（如果需要外部控制）
    setIsDqnTraining,
    setIsPpoTraining,
    setIsSacTraining,
    setTrainingMetrics,
    setRewardTrendData,
    setPolicyLossData
  }
}