/**
 * RL監控Hook
 * 抽取自 FullChartAnalysisDashboard.tsx 的RL監控邏輯
 */

import { useState, useEffect } from 'react'
import { createInitialRLData, createInitialPolicyLossData, createInitialTrainingMetrics } from '../../../../../utils/mockDataGenerator'

/**
 * RL訓練狀態和數據管理Hook
 */
export const useRLMonitoring = () => {
  // RL監控相關狀態
  const [isDqnTraining, setIsDqnTraining] = useState(false)
  const [isPpoTraining, setIsPpoTraining] = useState(false)
  const [isSacTraining, setIsSacTraining] = useState(false)
  const [trainingMetrics, setTrainingMetrics] = useState(createInitialTrainingMetrics())

  const [rewardTrendData, setRewardTrendData] = useState(createInitialRLData())
  const [policyLossData, setPolicyLossData] = useState(createInitialPolicyLossData())

  // 監聽來自GymnasiumRLMonitor的真實數據
  useEffect(() => {
    const handleRLMetricsUpdate = (event: CustomEvent) => {
      const { engine, metrics } = event.detail
      
      // 只在有意義的里程碑時記錄
      if ((metrics.episodes_completed > 0 && metrics.episodes_completed % 5 === 0) || 
          (metrics.training_progress > 0 && metrics.training_progress % 10 === 0)) {
        console.log(`收到RL監控數據更新 - ${engine}:`, {
          episodes: metrics.episodes_completed,
          progress: metrics.training_progress,
          avgReward: metrics.average_reward?.toFixed(2)
        })
      }
      
      if (engine === 'dqn') {
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

        // 更新獎勵趨勢數據
        setRewardTrendData(prevData => {
          if (typeof metrics.average_reward === 'number') {
            const currentTime = new Date()
            const timeLabel = currentTime.toLocaleTimeString('zh-TW', { 
              hour12: false, 
              minute: '2-digit', 
              second: '2-digit' 
            })
            
            // 保持數據持續增長，橫軸隨時間前進
            const newDataPoints = [...prevData.dqnData, metrics.average_reward]
            const newLabels = [...prevData.labels, timeLabel]
            
            // 如果數據點太多，限制在最多100個點以保持性能
            const maxPoints = 100
            const finalDataPoints = newDataPoints.length > maxPoints 
              ? newDataPoints.slice(-maxPoints) 
              : newDataPoints
            const finalLabels = newLabels.length > maxPoints 
              ? newLabels.slice(-maxPoints) 
              : newLabels
            
            return {
              ...prevData,
              dqnData: finalDataPoints,
              labels: finalLabels
            }
          }
          return prevData
        })

        // 更新策略損失數據 (使用模擬值，因為GymnasiumRLMonitor沒有提供policy_loss)
        setPolicyLossData(prevData => {
          const currentTime = new Date()
          const timeLabel = currentTime.toLocaleTimeString('zh-TW', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
          })
          const mockLoss = Math.random() * 0.5 + 0.1 // 模擬損失值
          
          const newLossPoints = [...(prevData.dqnLoss || []), mockLoss]
          const newLabels = [...prevData.labels, timeLabel]
          
          // 如果數據點太多，限制在最多100個點以保持性能
          const maxPoints = 100
          const finalLossPoints = newLossPoints.length > maxPoints 
            ? newLossPoints.slice(-maxPoints) 
            : newLossPoints
          const finalLabels = newLabels.length > maxPoints 
            ? newLabels.slice(-maxPoints) 
            : newLabels
          
          return {
            ...prevData,
            dqnLoss: finalLossPoints,
            labels: finalLabels
          }
        })
      } else if (engine === 'ppo') {
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

        // 更新獎勵趨勢數據
        setRewardTrendData(prevData => {
          if (typeof metrics.average_reward === 'number') {
            const currentTime = new Date()
            const timeLabel = currentTime.toLocaleTimeString('zh-TW', { 
              hour12: false, 
              minute: '2-digit', 
              second: '2-digit' 
            })
            
            // 保持數據持續增長，橫軸隨時間前進
            const newDataPoints = [...prevData.ppoData, metrics.average_reward]
            const newLabels = [...prevData.labels, timeLabel]
            
            // 如果數據點太多，限制在最多100個點以保持性能
            const maxPoints = 100
            const finalDataPoints = newDataPoints.length > maxPoints 
              ? newDataPoints.slice(-maxPoints) 
              : newDataPoints
            const finalLabels = newLabels.length > maxPoints 
              ? newLabels.slice(-maxPoints) 
              : newLabels
            
            return {
              ...prevData,
              ppoData: finalDataPoints,
              labels: finalLabels
            }
          }
          return prevData
        })

        // 更新策略損失數據 (使用模擬值，因為GymnasiumRLMonitor沒有提供policy_loss)
        setPolicyLossData(prevData => {
          const currentTime = new Date()
          const timeLabel = currentTime.toLocaleTimeString('zh-TW', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
          })
          const mockLoss = Math.random() * 0.3 + 0.05 // PPO通常損失較小
          
          const newLossPoints = [...(prevData.ppoLoss || []), mockLoss]
          const newLabels = [...prevData.labels, timeLabel]
          
          // 如果數據點太多，限制在最多100個點以保持性能
          const maxPoints = 100
          const finalLossPoints = newLossPoints.length > maxPoints 
            ? newLossPoints.slice(-maxPoints) 
            : newLossPoints
          const finalLabels = newLabels.length > maxPoints 
            ? newLabels.slice(-maxPoints) 
            : newLabels
          
          return {
            ...prevData,
            ppoLoss: finalLossPoints,
            labels: finalLabels
          }
        })
      } else if (engine === 'sac') {
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

        // 更新獎勵趨勢數據 - SAC
        setRewardTrendData(prevData => {
          if (typeof metrics.average_reward === 'number') {
            const currentTime = new Date()
            const timeLabel = currentTime.toLocaleTimeString('zh-TW', { 
              hour12: false, 
              minute: '2-digit', 
              second: '2-digit' 
            })
            
            // 保持數據持續增長，橫軸隨時間前進
            const newDataPoints = [...(prevData.sacData || []), metrics.average_reward]
            const newLabels = [...prevData.labels, timeLabel]
            
            // 如果數據點太多，限制在最多100個點以保持性能
            const maxPoints = 100
            const finalDataPoints = newDataPoints.length > maxPoints 
              ? newDataPoints.slice(-maxPoints) 
              : newDataPoints
            const finalLabels = newLabels.length > maxPoints 
              ? newLabels.slice(-maxPoints) 
              : newLabels
            
            return {
              ...prevData,
              sacData: finalDataPoints,
              labels: finalLabels
            }
          }
          return prevData
        })

        // 更新策略損失數據 - SAC
        setPolicyLossData(prevData => {
          const currentTime = new Date()
          const timeLabel = currentTime.toLocaleTimeString('zh-TW', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
          })
          const mockLoss = Math.random() * 0.4 + 0.08 // SAC損失值
          
          const newLossPoints = [...(prevData.sacLoss || []), mockLoss]
          const newLabels = [...prevData.labels, timeLabel]
          
          // 如果數據點太多，限制在最多100個點以保持性能
          const maxPoints = 100
          const finalLossPoints = newLossPoints.length > maxPoints 
            ? newLossPoints.slice(-maxPoints) 
            : newLossPoints
          const finalLabels = newLabels.length > maxPoints 
            ? newLabels.slice(-maxPoints) 
            : newLabels
          
          return {
            ...prevData,
            sacLoss: finalLossPoints,
            labels: finalLabels
          }
        })
      }
    }

    const handleTrainingStateUpdate = (event: CustomEvent) => {
      const { engine, isTraining } = event.detail
      
      console.log(`訓練狀態更新 - ${engine}: ${isTraining ? '開始' : '停止'}`)
      
      if (engine === 'dqn') {
        setIsDqnTraining(isTraining)
      } else if (engine === 'ppo') {
        setIsPpoTraining(isTraining)
      } else if (engine === 'sac') {
        setIsSacTraining(isTraining)
      }
    }

    const handleTrainingStopped = (event: CustomEvent) => {
      const { engine } = event.detail
      console.log(`收到訓練停止事件 - ${engine}`)
      
      if (engine === 'dqn') {
        setIsDqnTraining(false)
      } else if (engine === 'ppo') {
        setIsPpoTraining(false)
      } else if (engine === 'sac') {
        setIsSacTraining(false)
      }
    }

    // 監聽事件
    window.addEventListener('rlMetricsUpdate', handleRLMetricsUpdate as EventListener)
    window.addEventListener('rlTrainingStateUpdate', handleTrainingStateUpdate as EventListener)
    window.addEventListener('rlTrainingStopped', handleTrainingStopped as EventListener)

    return () => {
      window.removeEventListener('rlMetricsUpdate', handleRLMetricsUpdate as EventListener)
      window.removeEventListener('rlTrainingStateUpdate', handleTrainingStateUpdate as EventListener)
      window.removeEventListener('rlTrainingStopped', handleTrainingStopped as EventListener)
    }
  }, [])

  // 控制函數
  const toggleDqnTraining = () => {
    const newState = !isDqnTraining
    setIsDqnTraining(newState)
    window.dispatchEvent(
      new CustomEvent('dqnTrainingToggle', {
        detail: { isTraining: newState }
      })
    )
  }

  const togglePpoTraining = () => {
    const newState = !isPpoTraining
    setIsPpoTraining(newState)
    window.dispatchEvent(
      new CustomEvent('ppoTrainingToggle', {
        detail: { isTraining: newState }
      })
    )
  }

  const toggleSacTraining = () => {
    const newState = !isSacTraining
    setIsSacTraining(newState)
    window.dispatchEvent(
      new CustomEvent('sacTrainingToggle', {
        detail: { isTraining: newState }
      })
    )
  }

  const toggleAllTraining = () => {
    const anyTraining = isDqnTraining || isPpoTraining || isSacTraining
    const newState = !anyTraining
    setIsDqnTraining(newState)
    setIsPpoTraining(newState)
    setIsSacTraining(newState)
    window.dispatchEvent(
      new CustomEvent('allTrainingToggle', {
        detail: { 
          dqnTraining: newState, 
          ppoTraining: newState,
          sacTraining: newState
        }
      })
    )
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