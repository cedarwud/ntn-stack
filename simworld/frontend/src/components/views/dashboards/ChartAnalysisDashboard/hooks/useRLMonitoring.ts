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
export const useRLMonitoring = () => {
  // RL監控相關狀態
  const [isDqnTraining, setIsDqnTraining] = useState(false)
  const [isPpoTraining, setIsPpoTraining] = useState(false)
  const [isSacTraining, setIsSacTraining] = useState(false)
  
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
      // 注意：後端路由是 /api/v1/rl/training/start/{algorithm_name}
      const response = await apiClient.post(`/api/v1/rl/training/start/${algorithm}`, config);
      console.log(`Successfully started training for ${algorithm}`, response);
      // 可以在這裡觸發一個日誌或通知
    } catch (error) {
      console.error(`Failed to start training for ${algorithm}:`, error);
      // 可以在這裡顯示一個錯誤通知
      throw error; // 向上拋出錯誤，讓調用者可以處理
    }
  };

  const stopTraining = async (algorithm: string) => {
    // 停止訓練的邏輯尚未在後端實現，暫時保留
    console.warn(`Stop training functionality for ${algorithm} is not yet implemented on the backend.`);
    // try {
    //   await apiClient.post(`/api/v1/rl/training/stop/${algorithm}`);
    // } catch (error) {
    //   console.error(`Failed to stop training for ${algorithm}:`, error);
    // }
  };


  // 統一的數據獲取 - 移除重複的事件監聽機制
  useEffect(() => {
    const fetchTrainingData = async () => {
      try {
        // apiClient.getRLTrainingSessions() 邏輯需要與新的後端 /status API 對應
        const allAlgorithms = ['dqn', 'ppo', 'sac']
        const statusPromises = allAlgorithms.map(algo => 
          apiClient.get<StatusResponse>(`/api/v1/rl/training/status/${algo}`) // 指定返回類型
            .then(res => ({ algorithm: algo, data: res }))
            .catch(() => ({ algorithm: algo, data: { status: 'not_found' }} as { algorithm: string, data: StatusResponse })) // 確保錯誤情況下的類型匹配
        );
        
        const results = await Promise.all(statusPromises);

        const activeAlgorithms = new Set<string>();
        results.forEach(result => {
          // 現在 result.data 是強型別的
          if (result.data && result.data.status === 'running') {
            activeAlgorithms.add(result.algorithm);
          }
        });
        
        // 更新訓練狀態
        setIsDqnTraining(activeAlgorithms.has('dqn'))
        setIsPpoTraining(activeAlgorithms.has('ppo'))
        setIsSacTraining(activeAlgorithms.has('sac'))
        
        // 此處可以添加更新訓練指標和圖表的邏輯，
        // 但需要後端 /status API 提供更豐富的數據
        
      } catch (error) {
        console.warn('獲取訓練數據失敗:', error)
      }
    }

    // 啟動定期數據獲取
    const interval = setInterval(fetchTrainingData, 2000);
    fetchTrainingData(); // 立即執行一次

    return () => {
      clearInterval(interval)
    }
  }, [])


  // 控制函數
  const toggleDqnTraining = () => {
    if (!isDqnTraining) {
      console.log('Calling startTraining for dqn');
      startTraining('dqn', { episodes: 100, batch_size: 32, learning_rate: 0.001 });
    } else {
      console.log('Calling stopTraining for dqn');
      stopTraining('dqn');
    }
    // 手動切換狀態以立即更新UI，後續由API輪詢來同步真實狀態
    setIsDqnTraining(!isDqnTraining);
  }

  const togglePpoTraining = () => {
    if (!isPpoTraining) {
      console.log('Calling startTraining for ppo');
      startTraining('ppo', { episodes: 100, batch_size: 32, learning_rate: 0.001 });
    } else {
      console.log('Calling stopTraining for ppo');
      stopTraining('ppo');
    }
    setIsPpoTraining(!isPpoTraining);
  }

  const toggleSacTraining = () => {
    if (!isSacTraining) {
      console.log('Calling startTraining for sac');
      startTraining('sac', { episodes: 100, batch_size: 32, learning_rate: 0.001 });
    } else {
      console.log('Calling stopTraining for sac');
      stopTraining('sac');
    }
    setIsSacTraining(!isSacTraining);
  }

  const toggleAllTraining = useCallback(() => {
    const anyTraining = isDqnTraining || isPpoTraining || isSacTraining
    const newState = !anyTraining;
    
    const algorithmsToToggle = ['dqn', 'ppo', 'sac'];
    algorithmsToToggle.forEach(algo => {
      const isTraining = algo === 'dqn' ? isDqnTraining : algo === 'ppo' ? isPpoTraining : isSacTraining;
      if (newState && !isTraining) {
        startTraining(algo, { episodes: 100 });
      } else if (!newState && isTraining) {
        stopTraining(algo);
      }
    });

    setIsDqnTraining(newState);
    setIsPpoTraining(newState);
    setIsSacTraining(newState);
    
    // 如果是開始訓練，統一初始化所有圖表
    if (newState) {
      console.log('🎯 統一初始化所有算法圖表從 Ep 0 開始')
      setRewardTrendData(prevData => ({
        ...prevData,
        dqnData: [0], // 起始獎勵點
        dqnLabels: ['Ep 0'],
        ppoData: [0], // 起始獎勵點
        ppoLabels: ['Ep 0'],
        sacData: [0], // 起始獎勵點
        sacLabels: ['Ep 0'],
      }))
    }
    
    // 更新所有引擎的 trainingMetrics
    if (newState) {
      // 開始訓練時，等待真實數據從 GymnasiumRLMonitor 推送
      console.log('啟動所有引擎，等待真實數據更新')
      // 訓練指標和圖表數據將由 handleRLMetricsUpdate 事件處理器進行更新
      // 不再生成模擬數據，完全依賴真實 API 數據
    } else {
      // 停止訓練時，重置數據
      console.log('停止所有引擎，重置訓練指標')
      setTrainingMetrics(prevMetrics => ({
        ...prevMetrics,
        dqn: {
          episodes: 0,
          avgReward: 0,
          progress: 0,
          handoverDelay: 45,
          successRate: 82,
          signalDropTime: 18,
          energyEfficiency: 0.75,
        },
        ppo: {
          episodes: 0,
          avgReward: 0,
          progress: 0,
          handoverDelay: 40,
          successRate: 84,
          signalDropTime: 16,
          energyEfficiency: 0.8,
        },
        sac: {
          episodes: 0,
          avgReward: 0,
          progress: 0,
          handoverDelay: 42,
          successRate: 85,
          signalDropTime: 16,
          energyEfficiency: 0.78,
        }
      }))
      
      // 重置圖表數據
      console.log('重置圖表數據')
      setRewardTrendData(prevData => ({
        ...prevData,
        dqnData: [],
        dqnLabels: [],
        ppoData: [],
        ppoLabels: [],
        sacData: [],
        sacLabels: [],
        labels: []
      }))
      
      setPolicyLossData(prevData => ({
        ...prevData,
        dqnData: [],
        ppoData: [],
        sacData: [],
        labels: []
      }))
    }
    
    // 移除舊的前端事件派發
    // console.log('發送 allToggle 事件:', { isTraining: newState })
    // window.dispatchEvent(
    //   new CustomEvent('allToggle', {
    //     detail: { 
    //       isTraining: newState
    //     }
    //   })
    // )
  }, [isDqnTraining, isPpoTraining, isSacTraining]) // 添加依賴避免閉包問題

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
    toggleAllTraining,
    
    // 設置函數（如果需要外部控制）
    setIsDqnTraining,
    setIsPpoTraining,
    setIsSacTraining,
    setTrainingMetrics,
    setRewardTrendData,
    setPolicyLossData
  }
}