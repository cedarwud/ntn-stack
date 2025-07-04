/**
 * useEventT1Logic Hook
 * T1 事件特定的狀態管理和業務邏輯
 * 基於 3GPP TS 38.331 規範的 Event T1 實現
 * Event T1: 時間相關測量事件
 */

import { useState, useCallback, useMemo } from 'react'
import type { EventT1Params, UseEventLogicResult } from '../types'
import { useAnimationControl } from './useAnimationControl'

const DEFAULT_T1_PARAMS: EventT1Params = {
  t1Threshold: 30, // t1-Threshold in seconds (3GPP Thresh1)
  duration: 20, // Duration in seconds (3GPP Duration) - 時間窗口持續時間
  timeToTrigger: 0, // TTT 通常為 0 (T1 有內建時間邏輯)
  reportInterval: 2000, // Report interval in milliseconds  
  reportAmount: 2, // Number of reports (用於條件事件 CondEvent)
  reportOnLeave: false, // Report when leaving condition (用於條件事件)
}

interface EventT1Status {
  condition1: boolean // 時間條件
  eventTriggered: boolean // 事件是否已觸發
  currentMeasurementTime: number // 當前測量時間
  timeRemaining: number // 剩餘時間
  measurementPhase: 'starting' | 'measuring' | 'completed' | 'timeout' // 測量階段
  reportCount: number // 報告次數
  isActive: boolean // 測量是否活躍
}

export const useEventT1Logic = (): UseEventLogicResult<EventT1Params> & {
  eventStatus: EventT1Status
  getCurrentMeasurementTime: (time: number) => number
  createNarrationContent: (time: number) => {
    phaseTitle: string
    timeProgress: string
    mainDescription: string
    technicalDetails?: string
  }
} => {
  // T1 參數狀態
  const [params, setParams] = useState<EventT1Params>(DEFAULT_T1_PARAMS)

  // 主題狀態
  const [isDarkTheme, setIsDarkTheme] = useState(true)
  
  // 面板狀態
  const [showThresholdLines, setShowThresholdLines] = useState(true)
  const [narrationPanel, setNarrationPanel] = useState({
    isVisible: true,
    isMinimized: false,
    showTechnicalDetails: false,
    position: { x: 20, y: 20 },
    opacity: 0.95
  })

  // 動畫控制
  const animationControl = useAnimationControl({
    duration: 80, // T1 事件動畫持續 80 秒
    stepSize: 0.1,
    updateInterval: 100,
    autoReset: true
  })

  // 重置參數
  const resetParams = useCallback(() => {
    setParams({ ...DEFAULT_T1_PARAMS })
  }, [])

  // 主題切換
  const toggleTheme = useCallback(() => {
    setIsDarkTheme(prev => !prev)
  }, [])

  // 門檻線切換
  const toggleThresholdLines = useCallback(() => {
    setShowThresholdLines(prev => !prev)
  }, [])

  // 解說面板狀態更新
  const updateNarrationPanel = useCallback((updates: Partial<typeof narrationPanel>) => {
    setNarrationPanel(prev => ({ ...prev, ...updates }))
  }, [])

  // 獲取當前測量時間
  const getCurrentMeasurementTime = useCallback((currentTime: number): number => {
    // 模擬測量時間的累積
    // 在前30秒快速累積，然後趨於穩定
    if (currentTime <= 30) {
      return currentTime * 0.9 // 稍慢於實際時間
    } else if (currentTime <= 60) {
      return 27 + (currentTime - 30) * 0.3 // 慢速累積
    } else {
      return Math.min(params.t1Threshold + params.duration + 5, 27 + 9 + (currentTime - 60) * 0.1)
    }
  }, [params.t1Threshold, params.duration])

  // 計算 T1 事件狀態
  const eventStatus = useMemo((): EventT1Status => {
    const currentTime = animationControl.currentTime
    const measurementTime = getCurrentMeasurementTime(currentTime)
    
    // 3GPP T1 條件邏輯:
    // 進入條件 (T1-1): Mt > Thresh1
    const enteringCondition = measurementTime > params.t1Threshold
    // 離開條件 (T1-2): Mt > Thresh1 + Duration
    const leavingCondition = measurementTime > (params.t1Threshold + params.duration)
    
    // 確定測量階段
    let measurementPhase: 'starting' | 'measuring' | 'completed' | 'timeout'
    if (currentTime < 5) {
      measurementPhase = 'starting'
    } else if (!enteringCondition) {
      measurementPhase = 'measuring'
    } else if (enteringCondition && !leavingCondition) {
      measurementPhase = 'completed' // T1 事件活躍期間
    } else {
      measurementPhase = 'timeout' // 超過 Thresh1 + Duration
    }
    
    // 計算報告次數（基於觸發後的時間）
    const reportCount = enteringCondition ? Math.min(
      Math.floor((measurementTime - params.t1Threshold) / (params.reportInterval / 1000)) + 1,
      params.reportAmount
    ) : 0

    const eventTriggered = enteringCondition && !leavingCondition
    const timeRemaining = Math.max(0, params.t1Threshold - measurementTime)
    const isActive = measurementPhase === 'measuring' || measurementPhase === 'completed'

    return {
      condition1: enteringCondition,
      eventTriggered,
      currentMeasurementTime: measurementTime,
      timeRemaining,
      measurementPhase,
      reportCount,
      isActive
    }
  }, [getCurrentMeasurementTime, animationControl.currentTime, params])

  // 創建解說內容
  const createNarrationContent = useCallback((time: number) => {
    const status = eventStatus
    const progress = ((time / 80) * 100).toFixed(1)

    let phaseTitle = ''
    let mainDescription = ''
    let technicalDetails = ''

    if (status.measurementPhase === 'starting') {
      phaseTitle = '⏱️ 測量計時器初始化'
      mainDescription = `
        <div class="phase-description">
          Event T1 是基於時間的測量事件，用於監測某項測量活動的持續時間。
          當測量時間達到設定門檻時觸發報告。
        </div>
        <p><strong>初始狀態：</strong></p>
        <ul>
          <li>測量時間：${status.currentMeasurementTime.toFixed(1)} 秒</li>
          <li>目標門檻：${params.t1Threshold} 秒</li>
          <li>剩餘時間：${status.timeRemaining.toFixed(1)} 秒</li>
          <li>測量狀態：${status.isActive ? '活躍' : '準備中'}</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>⚙️ T1 配置 (3GPP TS 38.331)：</h4>
          <p>Thresh1 (t1-Threshold)：${params.t1Threshold} 秒</p>
          <p>Duration：${params.duration} 秒</p>
          <p>進入條件：Mt > ${params.t1Threshold}s</p>
          <p>離開條件：Mt > ${params.t1Threshold + params.duration}s</p>
          <p>觸發時間：${params.timeToTrigger} 毫秒 (T1 內建時間邏輯)</p>
          <p>報告間隔：${params.reportInterval} 毫秒 (條件事件用途)</p>
          <p>報告次數：${params.reportAmount} 次 (條件事件用途)</p>
        </div>
      `
    } else if (status.measurementPhase === 'measuring') {
      phaseTitle = '📊 測量時間累積中'
      mainDescription = `
        <div class="phase-description">
          測量計時器正在運行，記錄特定條件下的持續時間。
          系統會持續監測直到達到時間門檻。
        </div>
        <p><strong>測量進度：</strong></p>
        <ul>
          <li>已測量：${status.currentMeasurementTime.toFixed(1)} / ${params.t1Threshold} 秒</li>
          <li>完成度：${((status.currentMeasurementTime / params.t1Threshold) * 100).toFixed(1)}%</li>
          <li>剩餘時間：${status.timeRemaining.toFixed(1)} 秒</li>
          <li>測量狀態：${status.isActive ? '持續測量中' : '暫停'}</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>⏱️ 時間分析：</h4>
          <p>測量開始時間：${(time - status.currentMeasurementTime).toFixed(1)} 秒</p>
          <p>當前測量時間：${status.currentMeasurementTime.toFixed(1)} 秒</p>
          <p>預計完成時間：${(time + status.timeRemaining).toFixed(1)} 秒</p>
          <p>測量效率：${((status.currentMeasurementTime / time) * 100).toFixed(1)}%</p>
        </div>
      `
    } else if (status.measurementPhase === 'completed') {
      phaseTitle = '✅ T1 事件觸發成功'
      mainDescription = `
        <div class="phase-description">
          T1 事件已觸發！測量時間達到設定門檻，系統開始發送週期性報告。
          這表明測量條件已持續滿足足夠長的時間。
        </div>
        <p><strong>觸發詳情：</strong></p>
        <ul>
          <li>觸發時間：${status.currentMeasurementTime.toFixed(1)} 秒</li>
          <li>超過門檻：${(status.currentMeasurementTime - params.t1Threshold).toFixed(1)} 秒</li>
          <li>已發送報告：${status.reportCount} / ${params.reportAmount} 次</li>
          <li>下次報告：${(params.reportInterval / 1000).toFixed(1)} 秒後</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>📈 觸發分析：</h4>
          <p>門檻檢查：${status.currentMeasurementTime.toFixed(1)} ≥ ${params.t1Threshold} 秒 ✓</p>
          <p>觸發延遲：${params.timeToTrigger} 毫秒</p>
          <p>報告模式：每 ${params.reportInterval / 1000} 秒一次</p>
          <p>總報告次數：${status.reportCount} 次（最多 ${params.reportAmount} 次）</p>
        </div>
      `
    } else { // timeout
      phaseTitle = '⏰ 測量週期完成'
      mainDescription = `
        <div class="phase-description">
          測量週期已完成，T1 事件保持觸發狀態。系統已完成所有預定的報告發送，
          測量活動進入維持階段。
        </div>
        <p><strong>最終狀態：</strong></p>
        <ul>
          <li>總測量時間：${status.currentMeasurementTime.toFixed(1)} 秒</li>
          <li>完成所有報告：${status.reportCount} 次</li>
          <li>事件狀態：持續觸發中</li>
          <li>維持時間：${(status.currentMeasurementTime - params.t1Threshold).toFixed(1)} 秒</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>📋 完成總結：</h4>
          <p>測量週期：${status.currentMeasurementTime.toFixed(1)} 秒</p>
          <p>有效測量：${(status.currentMeasurementTime - params.t1Threshold).toFixed(1)} 秒</p>
          <p>報告效率：100% (${status.reportCount}/${params.reportAmount})</p>
          <p>事件狀態：${status.eventTriggered ? '成功觸發' : '未觸發'}</p>
        </div>
      `
    }

    return {
      phaseTitle,
      timeProgress: `${time.toFixed(1)}s (${progress}%)`,
      mainDescription,
      technicalDetails
    }
  }, [eventStatus, params])

  return {
    params,
    setParams,
    resetParams,
    animationState: animationControl.animationState,
    updateAnimationState: animationControl.updateAnimationState,
    themeState: {
      isDarkTheme,
      toggleTheme
    },
    panelState: {
      showThresholdLines,
      toggleThresholdLines,
      narrationPanel,
      updateNarrationPanel
    },
    eventStatus,
    getCurrentMeasurementTime,
    createNarrationContent
  }
}