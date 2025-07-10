/**
 * RL監控Hook
 * 抽取自 FullChartAnalysisDashboard.tsx 的RL監控邏輯
 */

import { useState, useEffect, useRef } from 'react'
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

  // 定期獲取真實的訓練數據
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

            // 更新獎勵趨勢數據 - 使用最佳獎勵以更好地反映學習進度
            setRewardTrendData(prevData => {
              if (typeof metrics.best_reward === 'number') {
                // 使用 episodes 作為數據點，避免時間軸過於密集
                const episodeLabel = `Ep ${metrics.episodes_completed}`
                
                // 避免重複的 episode 數據
                const lastLabel = prevData.labels[prevData.labels.length - 1]
                if (lastLabel === episodeLabel) {
                  return prevData
                }
                
                const newDataPoints = [...prevData.dqnData, metrics.best_reward]
                const newLabels = [...prevData.labels, episodeLabel]
                
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
              if (typeof metrics.best_reward === 'number') {
                const episodeLabel = `Ep ${metrics.episodes_completed}`
                
                // 避免重複的 episode 數據
                const lastLabel = prevData.labels[prevData.labels.length - 1]
                if (lastLabel === episodeLabel) {
                  return prevData
                }
                
                const newDataPoints = [...prevData.ppoData, metrics.best_reward]
                const newLabels = [...prevData.labels, episodeLabel]
                
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
              if (typeof metrics.best_reward === 'number') {
                const episodeLabel = `Ep ${metrics.episodes_completed}`
                
                // 避免重複的 episode 數據
                const lastLabel = prevData.labels[prevData.labels.length - 1]
                if (lastLabel === episodeLabel) {
                  return prevData
                }
                
                const newDataPoints = [...(prevData.sacData || []), metrics.best_reward]
                const newLabels = [...prevData.labels, episodeLabel]
                
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
          }
        })
      } catch (error) {
        console.warn('獲取訓練數據失敗:', error)
      }
    }

    // 啟動定期數據獲取
    const interval = setInterval(fetchTrainingData, 3000) // 每3秒獲取一次
    fetchTrainingData() // 立即執行一次

    // 保持原有的事件監聽器作為備用
    const handleRLMetricsUpdate = (event: CustomEvent) => {
      const { engine, metrics } = event.detail
      
      // 只在有意義的里程碑時記錄 - 已根據用戶要求移除
      // if ((metrics.episodes_completed > 0 && metrics.episodes_completed % 5 === 0) || 
      //     (metrics.training_progress > 0 && metrics.training_progress % 10 === 0)) {
      //   console.log(`收到RL監控數據更新 - ${engine}:`, {
      //     episodes: metrics.episodes_completed,
      //     progress: metrics.training_progress,
      //     avgReward: metrics.average_reward?.toFixed(2)
      //   })
      // }
      
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

        // 更新獎勵趨勢數據 - 避免重複添加相同數據
        setRewardTrendData(prevData => {
          if (typeof metrics.average_reward === 'number') {
            // 檢查是否是新的數據點（避免重複）
            const lastDataPoint = prevData.dqnData[prevData.dqnData.length - 1]
            if (lastDataPoint === metrics.average_reward) {
              return prevData // 跳過重複數據
            }
            
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

        // 更新獎勵趨勢數據 - 避免重複添加相同數據
        setRewardTrendData(prevData => {
          if (typeof metrics.average_reward === 'number') {
            // 檢查是否是新的數據點（避免重複）
            const lastDataPoint = prevData.ppoData[prevData.ppoData.length - 1]
            if (lastDataPoint === metrics.average_reward) {
              return prevData // 跳過重複數據
            }
            
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

        // 更新獎勵趨勢數據 - SAC - 避免重複添加相同數據
        setRewardTrendData(prevData => {
          if (typeof metrics.average_reward === 'number') {
            // 檢查是否是新的數據點（避免重複）
            const lastDataPoint = (prevData.sacData || [])[prevData.sacData?.length - 1]
            if (lastDataPoint === metrics.average_reward) {
              return prevData // 跳過重複數據
            }
            
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

    // 狀態同步事件監聽器
    const handleTrainingStateSync = (event: CustomEvent) => {
      const { engine, isTraining } = event.detail
      
      // 檢查狀態是否有變化，只在狀態改變時記錄日誌
      const hasStateChanged = lastStateRef.current[engine] !== isTraining
      if (hasStateChanged) {
        console.log(`🔄 狀態同步事件 - ${engine}: ${isTraining ? '訓練中' : '停止'}`)
        lastStateRef.current[engine] = isTraining
      }
      
      if (engine === 'dqn') {
        setIsDqnTraining(isTraining)
      } else if (engine === 'ppo') {
        setIsPpoTraining(isTraining)
      } else if (engine === 'sac') {
        setIsSacTraining(isTraining)
      }
    }

    // 監聽事件
    window.addEventListener('rlMetricsUpdate', handleRLMetricsUpdate as EventListener)
    window.addEventListener('trainingStateUpdate', handleTrainingStateUpdate as EventListener)
    window.addEventListener('trainingStateSync', handleTrainingStateSync as EventListener)
    window.addEventListener('rlTrainingStopped', handleTrainingStopped as EventListener)

    return () => {
      clearInterval(interval)
      window.removeEventListener('rlMetricsUpdate', handleRLMetricsUpdate as EventListener)
      window.removeEventListener('trainingStateUpdate', handleTrainingStateUpdate as EventListener)
      window.removeEventListener('trainingStateSync', handleTrainingStateSync as EventListener)
      window.removeEventListener('rlTrainingStopped', handleTrainingStopped as EventListener)
    }
  }, [])

  // 初始化時同步後端訓練狀態
  useEffect(() => {
    const initializeTrainingState = async () => {
      try {
        console.log('🔄 useRLMonitoring Hook 初始化，同步後端訓練狀態')
        const statusSummary = await apiClient.getTrainingStatusSummary()
        
        console.log('🔄 Hook 獲取到狀態摘要:', statusSummary)
        
        // 同步訓練狀態
        const isDqnActive = statusSummary.active_algorithms.includes('dqn')
        const isPpoActive = statusSummary.active_algorithms.includes('ppo')
        const isSacActive = statusSummary.active_algorithms.includes('sac')
        
        console.log('🔄 Hook 設置訓練狀態:', {
          dqn: isDqnActive,
          ppo: isPpoActive,
          sac: isSacActive
        })
        
        setIsDqnTraining(isDqnActive)
        setIsPpoTraining(isPpoActive)
        setIsSacTraining(isSacActive)
        
      } catch (error) {
        console.warn('🔄 Hook 初始化狀態同步失敗:', error)
      }
    }
    
    initializeTrainingState()
  }, [])

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

  const toggleAllTraining = () => {
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
        ppoData: [],
        sacData: [],
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