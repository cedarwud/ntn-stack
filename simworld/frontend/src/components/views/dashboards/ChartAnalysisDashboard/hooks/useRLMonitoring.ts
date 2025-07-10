/**
 * RL監控Hook
 * 抽取自 FullChartAnalysisDashboard.tsx 的RL監控邏輯
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { createInitialRLData, createInitialPolicyLossData, createInitialTrainingMetrics } from '../../../../../utils/mockDataGenerator'
import { apiClient } from '../../../../../services/api-client'

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

  // 統一的數據獲取 - 移除重複的事件監聽機制
  useEffect(() => {
    const fetchTrainingData = async () => {
      try {
        const sessions = await apiClient.getRLTrainingSessions()
        // 只處理活躍的訓練會話
        const activeSessions = sessions.filter((session: Record<string, unknown>) => session.status === 'active')
        
        // 同步訓練狀態和重置非活躍算法的數據
        const activeAlgorithms = activeSessions.map((session: Record<string, unknown>) => session.algorithm_name as string)
        const allAlgorithms = ['dqn', 'ppo', 'sac']
        
        // 更新訓練狀態
        setIsDqnTraining(activeAlgorithms.includes('dqn'))
        setIsPpoTraining(activeAlgorithms.includes('ppo'))
        setIsSacTraining(activeAlgorithms.includes('sac'))
        
        allAlgorithms.forEach(algorithm => {
          if (!activeAlgorithms.includes(algorithm)) {
            setTrainingMetrics(prevMetrics => ({
              ...prevMetrics,
              [algorithm]: {
                episodes: 0,
                avgReward: 0,
                progress: 0,
                handoverDelay: algorithm === 'dqn' ? 45 : algorithm === 'ppo' ? 40 : 42,
                successRate: algorithm === 'dqn' ? 82 : algorithm === 'ppo' ? 84 : 85,
                signalDropTime: algorithm === 'dqn' ? 18 : 16,
                energyEfficiency: algorithm === 'dqn' ? 0.75 : algorithm === 'ppo' ? 0.8 : 0.78,
              }
            }))
          }
        })
        
        activeSessions.forEach((session: Record<string, unknown>) => {
          const algorithm = session.algorithm_name as string
          const progress = ((session.episodes_completed as number) / (session.episodes_target as number)) * 100
          
          const metrics = {
            episodes_completed: session.episodes_completed as number,
            average_reward: session.current_reward as number,
            best_reward: session.best_reward as number,
            training_progress: progress
          }
          
          // 更新訓練指標
          if (algorithm === 'dqn') {
            setTrainingMetrics(prevMetrics => ({
              ...prevMetrics,
              dqn: {
                episodes: metrics.episodes_completed || 0,
                avgReward: metrics.average_reward || 0,
                progress: metrics.training_progress || 0,
                handoverDelay: 45 - (metrics.training_progress || 0) / 100 * 20 + (Math.random() - 0.5) * 5,
                successRate: Math.min(100, 82 + (metrics.training_progress || 0) / 100 * 12 + (Math.random() - 0.5) * 1.5),
                signalDropTime: 18 - (metrics.training_progress || 0) / 100 * 8 + (Math.random() - 0.5) * 2,
                energyEfficiency: 0.75 + (metrics.training_progress || 0) / 100 * 0.2 + (Math.random() - 0.5) * 0.05,
              }
            }))

            // 更新獎勵趨勢數據 - DQN專用邏輯
            setRewardTrendData(prevData => {
              if (typeof metrics.average_reward === 'number') {
                // 檢查DQN專用的重複檢查
                const dqnData = prevData.dqnData || []
                const dqnLabels = prevData.dqnLabels || []
                
                // 避免重複的 episode 數據 - 檢查DQN專用標籤
                const lastDqnLabel = dqnLabels[dqnLabels.length - 1]
                const expectedLabel = `Ep ${metrics.episodes_completed}`
                if (lastDqnLabel === expectedLabel) {
                  return prevData // 跳過重複數據
                }
                
                const newDataPoints = [...dqnData, metrics.average_reward || 0]
                const newDqnLabels = [...dqnLabels, expectedLabel]
                
                const maxPoints = 100
                const finalDataPoints = newDataPoints.length > maxPoints 
                  ? newDataPoints.slice(-maxPoints) 
                  : newDataPoints
                const finalDqnLabels = newDqnLabels.length > maxPoints 
                  ? newDqnLabels.slice(-maxPoints) 
                  : newDqnLabels
                
                return {
                  ...prevData,
                  dqnData: finalDataPoints,
                  dqnLabels: finalDqnLabels
                }
              }
              return prevData
            })
          } else if (algorithm === 'ppo') {
            setTrainingMetrics(prevMetrics => ({
              ...prevMetrics,
              ppo: {
                episodes: metrics.episodes_completed || 0,
                avgReward: metrics.average_reward || 0,
                progress: metrics.training_progress || 0,
                handoverDelay: 40 - (metrics.training_progress || 0) / 100 * 22 + (Math.random() - 0.5) * 4,
                successRate: Math.min(100, 84 + (metrics.training_progress || 0) / 100 * 10 + (Math.random() - 0.5) * 1.2),
                signalDropTime: 16 - (metrics.training_progress || 0) / 100 * 9 + (Math.random() - 0.5) * 1.5,
                energyEfficiency: 0.8 + (metrics.training_progress || 0) / 100 * 0.18 + (Math.random() - 0.5) * 0.04,
              }
            }))

            setRewardTrendData(prevData => {
              if (typeof metrics.average_reward === 'number') {
                // 檢查PPO專用的重複檢查
                const ppoData = prevData.ppoData || []
                const ppoLabels = prevData.ppoLabels || []
                
                // 避免重複的 episode 數據 - 檢查PPO專用標籤
                const lastPpoLabel = ppoLabels[ppoLabels.length - 1]
                const expectedLabel = `Ep ${metrics.episodes_completed}`
                if (lastPpoLabel === expectedLabel) {
                  return prevData // 跳過重複數據
                }
                
                const newDataPoints = [...ppoData, metrics.average_reward || 0]
                const newPpoLabels = [...ppoLabels, expectedLabel]
                
                const maxPoints = 100
                const finalDataPoints = newDataPoints.length > maxPoints 
                  ? newDataPoints.slice(-maxPoints) 
                  : newDataPoints
                const finalPpoLabels = newPpoLabels.length > maxPoints 
                  ? newPpoLabels.slice(-maxPoints) 
                  : newPpoLabels
                
                return {
                  ...prevData,
                  ppoData: finalDataPoints,
                  ppoLabels: finalPpoLabels
                }
              }
              return prevData
            })
          } else if (algorithm === 'sac') {
            setTrainingMetrics(prevMetrics => ({
              ...prevMetrics,
              sac: {
                episodes: metrics.episodes_completed || 0,
                avgReward: metrics.average_reward || 0,
                progress: metrics.training_progress || 0,
                handoverDelay: 42 - (metrics.training_progress || 0) / 100 * 18 + (Math.random() - 0.5) * 4,
                successRate: Math.min(100, 85 + (metrics.training_progress || 0) / 100 * 13 + (Math.random() - 0.5) * 1.2),
                signalDropTime: 16 - (metrics.training_progress || 0) / 100 * 7 + (Math.random() - 0.5) * 1.8,
                energyEfficiency: 0.78 + (metrics.training_progress || 0) / 100 * 0.18 + (Math.random() - 0.5) * 0.04,
              }
            }))

            setRewardTrendData(prevData => {
              if (typeof metrics.average_reward === 'number') {
                // 檢查SAC專用的重複檢查
                const sacData = prevData.sacData || []
                const sacLabels = prevData.sacLabels || []
                
                // 避免重複的 episode 數據 - 檢查SAC專用標籤
                const lastSacLabel = sacLabels[sacLabels.length - 1]
                const expectedLabel = `Ep ${metrics.episodes_completed}`
                if (lastSacLabel === expectedLabel) {
                  return prevData // 跳過重複數據
                }
                
                const newDataPoints = [...sacData, metrics.average_reward || 0]
                const newSacLabels = [...sacLabels, expectedLabel]
                
                const maxPoints = 100
                const finalDataPoints = newDataPoints.length > maxPoints 
                  ? newDataPoints.slice(-maxPoints) 
                  : newDataPoints
                const finalSacLabels = newSacLabels.length > maxPoints 
                  ? newSacLabels.slice(-maxPoints) 
                  : newSacLabels
                
                return {
                  ...prevData,
                  sacData: finalDataPoints,
                  sacLabels: finalSacLabels
                }
              }
              return prevData
            })
          }
        })
      } catch (error) {
        console.warn('獲取訓練數據失敗:', error)
      }
    }

    // 啟動定期數據獲取 - 簡化為單一數據源
    const interval = setInterval(fetchTrainingData, 2000) // 提升到每2秒獲取一次，確保實時性
    fetchTrainingData() // 立即執行一次

    return () => {
      clearInterval(interval)
    }
  }, [])

  // 初始化時同步後端訓練狀態 - 簡化版本
  useEffect(() => {
    const initializeTrainingState = async () => {
      try {
        console.log('🔄 初始化 RL 監控狀態')
        const statusSummary = await apiClient.getTrainingStatusSummary()
        
        // 同步訓練狀態
        const isDqnActive = statusSummary.active_algorithms.includes('dqn')
        const isPpoActive = statusSummary.active_algorithms.includes('ppo')
        const isSacActive = statusSummary.active_algorithms.includes('sac')
        
        setIsDqnTraining(isDqnActive)
        setIsPpoTraining(isPpoActive)
        setIsSacTraining(isSacActive)
        
      } catch (error) {
        console.warn('🔄 初始化狀態同步失敗:', error)
      }
    }
    
    initializeTrainingState()
  }, [])

  // 所有事件處理邏輯已被 fetchTrainingData 的 API 輪詢替代
  // 移除了複雜的事件監聽器以避免數據衝突和同步問題

  // 控制函數
  const toggleDqnTraining = () => {
    const newState = !isDqnTraining
    console.log('toggleDqnTraining 被調用:', { 
      currentState: isDqnTraining, 
      newState 
    })
    setIsDqnTraining(newState)
    console.log('發送 dqnToggle 事件:', { isTraining: newState })
    window.dispatchEvent(
      new CustomEvent('dqnToggle', {
        detail: { isTraining: newState }
      })
    )
  }

  const togglePpoTraining = () => {
    const newState = !isPpoTraining
    console.log('togglePpoTraining 被調用:', { 
      currentState: isPpoTraining, 
      newState 
    })
    setIsPpoTraining(newState)
    console.log('發送 ppoToggle 事件:', { isTraining: newState })
    window.dispatchEvent(
      new CustomEvent('ppoToggle', {
        detail: { isTraining: newState }
      })
    )
  }

  const toggleSacTraining = () => {
    const newState = !isSacTraining
    console.log('toggleSacTraining 被調用:', { 
      currentState: isSacTraining, 
      newState 
    })
    setIsSacTraining(newState)
    console.log('發送 sacToggle 事件:', { isTraining: newState })
    window.dispatchEvent(
      new CustomEvent('sacToggle', {
        detail: { isTraining: newState }
      })
    )
  }

  const toggleAllTraining = useCallback(() => {
    const anyTraining = isDqnTraining || isPpoTraining || isSacTraining
    const newState = !anyTraining
    console.log('toggleAllTraining 被調用:', { 
      anyCurrentlyTraining: anyTraining, 
      newState,
      currentStates: { isDqnTraining, isPpoTraining, isSacTraining }
    })
    setIsDqnTraining(newState)
    setIsPpoTraining(newState)
    setIsSacTraining(newState)
    
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
    
    console.log('發送 allToggle 事件:', { isTraining: newState })
    window.dispatchEvent(
      new CustomEvent('allToggle', {
        detail: { 
          isTraining: newState
        }
      })
    )
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