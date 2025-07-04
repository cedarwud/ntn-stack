/**
 * useEventA4Logic Hook
 * A4 事件特定的狀態管理和業務邏輯
 * 基於 3GPP TS 38.331 規範的 Event A4 實現
 */

import { useState, useCallback, useMemo } from 'react'
import type { EventA4Params, UseEventLogicResult } from '../types'
import { useAnimationControl } from './useAnimationControl'

const DEFAULT_A4_PARAMS: EventA4Params = {
  Thresh: -70, // a4-Threshold in dBm
  Hys: 3, // Hysteresis in dB
  Ofn: 0, // Measurement object specific offset in dB
  Ocn: 0, // Cell specific offset in dB
  timeToTrigger: 160, // TTT in milliseconds
  reportInterval: 1000, // Report interval in milliseconds
  reportAmount: 8, // Number of reports
  reportOnLeave: true // Report when leaving condition
}

interface EventA4Status {
  condition1: boolean // 進入條件: Mn + Ofn + Ocn - Hys > a4-Thresh
  condition2: boolean // 離開條件: Mn + Ofn + Ocn + Hys < a4-Thresh
  eventTriggered: boolean // 事件是否已觸發
  currentRSRP: number // 當前 RSRP 值
  effectiveRSRP: number // 經過偏移計算後的有效 RSRP
}

export const useEventA4Logic = (): UseEventLogicResult<EventA4Params> & {
  eventStatus: EventA4Status
  getCurrentRSRP: (time: number) => number
  createNarrationContent: (time: number) => {
    phaseTitle: string
    timeProgress: string
    mainDescription: string
    technicalDetails?: string
  }
} => {
  // A4 參數狀態
  const [params, setParams] = useState<EventA4Params>(DEFAULT_A4_PARAMS)

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
    duration: 95, // A4 事件動畫持續 95 秒
    stepSize: 0.1,
    updateInterval: 100,
    autoReset: true
  })

  // 重置參數
  const resetParams = useCallback(() => {
    setParams({ ...DEFAULT_A4_PARAMS })
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

  // 獲取當前時間點的 RSRP 值（模擬實際變化）
  const getCurrentRSRP = useCallback((currentTime: number): number => {
    // 模擬實際的 RSRP 變化情境
    const baseRSRP = -65
    const variation = 15 * Math.sin((currentTime / 95) * 4 * Math.PI)
    return Math.round((baseRSRP + variation) * 10) / 10 // 保留一位小數
  }, [])

  // 計算 A4 事件狀態
  const eventStatus = useMemo((): EventA4Status => {
    const currentRSRP = getCurrentRSRP(animationControl.currentTime)
    const effectiveRSRP = currentRSRP + params.Ofn + params.Ocn

    // A4-1 進入條件: Mn + Ofn + Ocn - Hys > a4-Thresh
    const condition1 = effectiveRSRP - params.Hys > params.Thresh

    // A4-2 離開條件: Mn + Ofn + Ocn + Hys < a4-Thresh  
    const condition2 = effectiveRSRP + params.Hys < params.Thresh

    // 簡化的觸發邏輯（實際應考慮 TTT）
    const eventTriggered = condition1

    return {
      condition1,
      condition2,
      eventTriggered,
      currentRSRP,
      effectiveRSRP: Math.round(effectiveRSRP * 10) / 10
    }
  }, [getCurrentRSRP, animationControl.currentTime, params])

  // 創建解說內容
  const createNarrationContent = useCallback((time: number) => {
    const status = eventStatus
    const progress = ((time / 95) * 100).toFixed(1)

    // 判斷當前階段
    let phaseTitle = ''
    let mainDescription = ''
    let technicalDetails = ''

    if (time < 10) {
      phaseTitle = '🚀 初始化階段'
      mainDescription = `
        <div class="phase-description">
          系統正在初始化 Event A4 測量環境。A4 事件用於監測鄰近基站的信號強度，
          當鄰近基站信號超過設定門檻時觸發換手程序。
        </div>
        <p><strong>當前狀態：</strong></p>
        <ul>
          <li>RSRP 測量值：${status.currentRSRP} dBm</li>
          <li>有效 RSRP：${status.effectiveRSRP} dBm</li>
          <li>門檻值：${params.Thresh} dBm</li>
          <li>事件狀態：${status.eventTriggered ? '<span class="status-indicator triggered">已觸發</span>' : '<span class="status-indicator inactive">等待中</span>'}</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>🔧 技術參數：</h4>
          <div class="formula">A4-1 進入條件：Mn + Ofn + Ocn - Hys > a4-Thresh</div>
          <div class="formula">A4-2 離開條件：Mn + Ofn + Ocn + Hys < a4-Thresh</div>
          <p>當前計算：${status.currentRSRP} + ${params.Ofn} + ${params.Ocn} - ${params.Hys} = ${(status.effectiveRSRP - params.Hys).toFixed(1)} dBm</p>
          <p>門檻比較：${(status.effectiveRSRP - params.Hys).toFixed(1)} ${status.condition1 ? '>' : '≤'} ${params.Thresh}</p>
        </div>
      `
    } else if (time < 30) {
      phaseTitle = '📡 信號監測階段'
      mainDescription = `
        <div class="phase-description">
          UE 持續監測鄰近基站的 RSRP 信號強度變化。系統會評估是否滿足 A4 事件的觸發條件。
        </div>
        <p><strong>監測結果：</strong></p>
        <ul>
          <li>原始 RSRP：${status.currentRSRP} dBm</li>
          <li>頻率偏移 (Ofn)：${params.Ofn > 0 ? '+' : ''}${params.Ofn} dB</li>
          <li>小區偏移 (Ocn)：${params.Ocn > 0 ? '+' : ''}${params.Ocn} dB</li>
          <li>有效 RSRP：${status.effectiveRSRP} dBm</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>📊 測量流程：</h4>
          <p>1. 測量鄰近基站 RSRP：${status.currentRSRP} dBm</p>
          <p>2. 應用頻率偏移：${status.currentRSRP} + ${params.Ofn} = ${(status.currentRSRP + params.Ofn).toFixed(1)} dBm</p>
          <p>3. 應用小區偏移：${(status.currentRSRP + params.Ofn).toFixed(1)} + ${params.Ocn} = ${status.effectiveRSRP} dBm</p>
          <p>4. 條件判斷：${status.effectiveRSRP} - ${params.Hys} = ${(status.effectiveRSRP - params.Hys).toFixed(1)} dBm</p>
        </div>
      `
    } else if (status.eventTriggered) {
      phaseTitle = '✅ 事件觸發階段'
      mainDescription = `
        <div class="phase-description">
          A4 事件已觸發！鄰近基站信號強度超過門檻值，系統將啟動換手準備程序。
        </div>
        <p><strong>觸發詳情：</strong></p>
        <ul>
          <li>觸發條件：A4-1 ✓</li>
          <li>等待時間 (TTT)：${params.timeToTrigger} ms</li>
          <li>報告間隔：${params.reportInterval} ms</li>
          <li>報告次數：${params.reportAmount === -1 ? '無限制' : params.reportAmount} 次</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>🎯 觸發分析：</h4>
          <div class="formula">條件檢查：${(status.effectiveRSRP - params.Hys).toFixed(1)} > ${params.Thresh} ✓</div>
          <p>差值：${((status.effectiveRSRP - params.Hys) - params.Thresh).toFixed(1)} dB</p>
          <p>下一步：等待 TTT (${params.timeToTrigger} ms) 後發送測量報告</p>
          <p>報告週期：每 ${params.reportInterval} ms 發送一次</p>
        </div>
      `
    } else {
      phaseTitle = '⏳ 持續監測階段'
      mainDescription = `
        <div class="phase-description">
          信號強度未達到觸發門檻，系統持續監測中。當滿足條件時將自動觸發 A4 事件。
        </div>
        <p><strong>當前狀態：</strong></p>
        <ul>
          <li>距離門檻：${(params.Thresh - (status.effectiveRSRP - params.Hys)).toFixed(1)} dB</li>
          <li>需要提升：${status.effectiveRSRP - params.Hys < params.Thresh ? '是' : '否'}</li>
          <li>遲滯保護：${params.Hys} dB</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>📈 距離分析：</h4>
          <p>當前有效 RSRP：${status.effectiveRSRP} dB</p>
          <p>考慮遲滯後：${(status.effectiveRSRP - params.Hys).toFixed(1)} dB</p>
          <p>觸發門檻：${params.Thresh} dB</p>
          <p>差距：${((status.effectiveRSRP - params.Hys) - params.Thresh).toFixed(1)} dB ${(status.effectiveRSRP - params.Hys) < params.Thresh ? '(需提升)' : '(已超過)'}</p>
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
    getCurrentRSRP,
    createNarrationContent
  }
}