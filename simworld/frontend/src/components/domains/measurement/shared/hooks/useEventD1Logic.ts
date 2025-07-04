/**
 * useEventD1Logic Hook
 * D1 事件特定的狀態管理和業務邏輯
 * 基於 3GPP TS 38.331 規範的 Event D1 實現
 */

import { useState, useCallback, useMemo } from 'react'
import type { EventD1Params, UseEventLogicResult } from '../types'
import { useAnimationControl } from './useAnimationControl'

const DEFAULT_D1_PARAMS: EventD1Params = {
  Thresh1: 1000, // distanceThreshFromReference1 in meters
  Thresh2: 2000, // distanceThreshFromReference2 in meters
  Hys: 100, // Hysteresis in meters
  timeToTrigger: 160, // TTT in milliseconds
  reportInterval: 1000, // Report interval in milliseconds
  reportAmount: 8, // Number of reports
  reportOnLeave: true, // Report when leaving condition
  referenceLocation1: { lat: 25.0330, lon: 121.5654 }, // 台北 101
  referenceLocation2: { lat: 25.0478, lon: 121.5170 }  // 台北車站
}

interface EventD1Status {
  condition1: boolean // 距離條件 1
  condition2: boolean // 距離條件 2
  eventTriggered: boolean // 事件是否已觸發
  currentLocation: { lat: number; lon: number } // 當前位置
  distanceToRef1: number // 到參考點1的距離
  distanceToRef2: number // 到參考點2的距離
}

// 計算兩點間距離（米）
const calculateDistance = (
  lat1: number, 
  lon1: number, 
  lat2: number, 
  lon2: number
): number => {
  const R = 6371000 // 地球半徑（米）
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return Math.round(R * c)
}

export const useEventD1Logic = (): UseEventLogicResult<EventD1Params> & {
  eventStatus: EventD1Status
  getCurrentLocation: (time: number) => { lat: number; lon: number }
  createNarrationContent: (time: number) => {
    phaseTitle: string
    timeProgress: string
    mainDescription: string
    technicalDetails?: string
  }
} => {
  // D1 參數狀態
  const [params, setParams] = useState<EventD1Params>(DEFAULT_D1_PARAMS)

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
    duration: 120, // D1 事件動畫持續 120 秒
    stepSize: 0.1,
    updateInterval: 100,
    autoReset: true
  })

  // 重置參數
  const resetParams = useCallback(() => {
    setParams({ ...DEFAULT_D1_PARAMS })
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

  // 獲取當前時間點的位置（模擬移動軌跡）
  const getCurrentLocation = useCallback((currentTime: number): { lat: number; lon: number } => {
    // 模擬在台北市區的移動軌跡
    const startLat = 25.0330
    const startLon = 121.5654
    
    // 創建一個橢圓軌跡
    const progress = (currentTime / 120) * 2 * Math.PI
    const latOffset = 0.01 * Math.sin(progress) // 約 1.1 km 範圍
    const lonOffset = 0.015 * Math.cos(progress) // 約 1.5 km 範圍
    
    return {
      lat: startLat + latOffset,
      lon: startLon + lonOffset
    }
  }, [])

  // 計算 D1 事件狀態
  const eventStatus = useMemo((): EventD1Status => {
    const currentLocation = getCurrentLocation(animationControl.currentTime)
    
    const distanceToRef1 = calculateDistance(
      currentLocation.lat, currentLocation.lon,
      params.referenceLocation1.lat, params.referenceLocation1.lon
    )
    
    const distanceToRef2 = calculateDistance(
      currentLocation.lat, currentLocation.lon,
      params.referenceLocation2.lat, params.referenceLocation2.lon
    )

    // D1-1 條件: 距離參考點1小於門檻1
    const condition1 = distanceToRef1 < params.Thresh1

    // D1-2 條件: 距離參考點2小於門檻2
    const condition2 = distanceToRef2 < params.Thresh2

    // 簡化的觸發邏輯
    const eventTriggered = condition1 || condition2

    return {
      condition1,
      condition2,
      eventTriggered,
      currentLocation,
      distanceToRef1,
      distanceToRef2
    }
  }, [getCurrentLocation, animationControl.currentTime, params])

  // 創建解說內容
  const createNarrationContent = useCallback((time: number) => {
    const status = eventStatus
    const progress = ((time / 120) * 100).toFixed(1)

    let phaseTitle = ''
    let mainDescription = ''
    let technicalDetails = ''

    if (time < 15) {
      phaseTitle = '🚀 位置服務初始化'
      mainDescription = `
        <div class="phase-description">
          Event D1 基於地理位置的測量事件正在初始化。此事件監測 UE 與特定參考位置的距離，
          用於位置相關的服務觸發。
        </div>
        <p><strong>當前狀態：</strong></p>
        <ul>
          <li>當前位置：${status.currentLocation.lat.toFixed(6)}°, ${status.currentLocation.lon.toFixed(6)}°</li>
          <li>到參考點1距離：${status.distanceToRef1} m</li>
          <li>到參考點2距離：${status.distanceToRef2} m</li>
          <li>事件狀態：${status.eventTriggered ? '<span class="status-indicator triggered">已觸發</span>' : '<span class="status-indicator inactive">等待中</span>'}</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>🔧 參考點配置：</h4>
          <p>參考點1：${params.referenceLocation1.lat.toFixed(6)}°, ${params.referenceLocation1.lon.toFixed(6)}°</p>
          <p>參考點2：${params.referenceLocation2.lat.toFixed(6)}°, ${params.referenceLocation2.lon.toFixed(6)}°</p>
          <p>門檻1：${params.Thresh1} m</p>
          <p>門檻2：${params.Thresh2} m</p>
          <p>遲滯：${params.Hys} m</p>
        </div>
      `
    } else if (status.eventTriggered) {
      phaseTitle = '📍 位置觸發階段'
      mainDescription = `
        <div class="phase-description">
          D1 事件已觸發！UE 已進入指定的地理區域範圍內。
          ${status.condition1 ? '接近參考點1' : ''}${status.condition1 && status.condition2 ? ' 和 ' : ''}${status.condition2 ? '接近參考點2' : ''}。
        </div>
        <p><strong>觸發詳情：</strong></p>
        <ul>
          <li>觸發條件：${status.condition1 ? 'D1-1 ✓' : 'D1-1 ✗'} ${status.condition2 ? 'D1-2 ✓' : 'D1-2 ✗'}</li>
          <li>當前距離1：${status.distanceToRef1} m (門檻：${params.Thresh1} m)</li>
          <li>當前距離2：${status.distanceToRef2} m (門檻：${params.Thresh2} m)</li>
          <li>報告間隔：${params.reportInterval} ms</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>🎯 觸發分析：</h4>
          <p>條件1檢查：${status.distanceToRef1} ${status.condition1 ? '<' : '≥'} ${params.Thresh1} m ${status.condition1 ? '✓' : '✗'}</p>
          <p>條件2檢查：${status.distanceToRef2} ${status.condition2 ? '<' : '≥'} ${params.Thresh2} m ${status.condition2 ? '✓' : '✗'}</p>
          <p>觸發邏輯：OR (任一條件滿足即觸發)</p>
          <p>報告週期：每 ${params.reportInterval} ms 發送位置報告</p>
        </div>
      `
    } else {
      phaseTitle = '🚶 移動監測階段'
      mainDescription = `
        <div class="phase-description">
          UE 正在移動中，系統持續監測與參考位置的距離。當進入設定範圍時將觸發 D1 事件。
        </div>
        <p><strong>距離狀態：</strong></p>
        <ul>
          <li>距參考點1：${status.distanceToRef1} m (需要 < ${params.Thresh1} m)</li>
          <li>距參考點2：${status.distanceToRef2} m (需要 < ${params.Thresh2} m)</li>
          <li>最近目標：${status.distanceToRef1 < status.distanceToRef2 ? '參考點1' : '參考點2'}</li>
          <li>最短距離：${Math.min(status.distanceToRef1, status.distanceToRef2)} m</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>📊 距離計算：</h4>
          <p>使用 Haversine 公式計算大圓距離</p>
          <p>當前座標：(${status.currentLocation.lat.toFixed(6)}, ${status.currentLocation.lon.toFixed(6)})</p>
          <p>到點1距離：${status.distanceToRef1} m (差距：${status.distanceToRef1 - params.Thresh1} m)</p>
          <p>到點2距離：${status.distanceToRef2} m (差距：${status.distanceToRef2 - params.Thresh2} m)</p>
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
    getCurrentLocation,
    createNarrationContent
  }
}