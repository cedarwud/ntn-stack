/**
 * useEventD2Logic Hook
 * D2 事件特定的狀態管理和業務邏輯
 * 基於 3GPP TS 38.331 規範的 Event D2 實現
 * Event D2: 服務基站距離變化事件
 */

import { useState, useCallback, useMemo } from 'react'
import type { EventD2Params, UseEventLogicResult } from '../types'
import { useAnimationControl } from './useAnimationControl'

const DEFAULT_D2_PARAMS: EventD2Params = {
  Thresh1: 1500, // distanceThreshFromReference1 in meters
  Thresh2: 800,  // distanceThreshFromReference2 in meters
  Hys: 50,       // Hysteresis in meters
  timeToTrigger: 320, // TTT in milliseconds
  reportInterval: 1000, // Report interval in milliseconds
  reportAmount: 4, // Number of reports
  reportOnLeave: true, // Report when leaving condition
  referenceLocation1: { lat: 25.0478, lon: 121.5170 }, // 台北車站
  referenceLocation2: { lat: 25.0418, lon: 121.5448 }  // 松山機場
}

interface EventD2Status {
  condition1: boolean // 距離條件 1
  condition2: boolean // 距離條件 2  
  eventTriggered: boolean // 事件是否已觸發
  currentLocation: { lat: number; lon: number } // 當前位置
  distanceToRef1: number // 到參考點1的距離
  distanceToRef2: number // 到參考點2的距離
  deltaDistance: number // 距離變化量
  movementDirection: 'approaching' | 'departing' | 'stable' // 移動趨勢
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

export const useEventD2Logic = (): UseEventLogicResult<EventD2Params> & {
  eventStatus: EventD2Status
  getCurrentLocation: (time: number) => { lat: number; lon: number }
  createNarrationContent: (time: number) => {
    phaseTitle: string
    timeProgress: string
    mainDescription: string
    technicalDetails?: string
  }
} => {
  // D2 參數狀態
  const [params, setParams] = useState<EventD2Params>(DEFAULT_D2_PARAMS)

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
    duration: 100, // D2 事件動畫持續 100 秒
    stepSize: 0.1,
    updateInterval: 100,
    autoReset: true
  })

  // 重置參數
  const resetParams = useCallback(() => {
    setParams({ ...DEFAULT_D2_PARAMS })
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
    // 模擬在台北市區的移動軌跡 - 更複雜的運動模式
    const startLat = 25.0478 // 台北車站
    const startLon = 121.5170
    
    // 創建一個複雜的移動軌跡：先接近再遠離
    const progress = currentTime / 100
    const phase1 = Math.min(progress * 2, 1) // 前50%時間
    const phase2 = Math.max((progress - 0.5) * 2, 0) // 後50%時間
    
    let latOffset: number
    let lonOffset: number
    
    if (progress < 0.5) {
      // 前半段：接近參考點
      latOffset = 0.008 * (1 - phase1) // 開始遠離，逐漸接近
      lonOffset = 0.012 * (1 - phase1)
    } else {
      // 後半段：遠離參考點
      latOffset = 0.008 * phase2 // 逐漸遠離
      lonOffset = 0.012 * phase2
    }
    
    // 添加一些隨機變化模擬真實移動
    const noise = 0.001 * Math.sin(currentTime * 0.5)
    
    return {
      lat: startLat + latOffset + noise,
      lon: startLon + lonOffset + noise * 0.7
    }
  }, [])

  // 計算 D2 事件狀態
  const eventStatus = useMemo((): EventD2Status => {
    const currentLocation = getCurrentLocation(animationControl.currentTime)
    const prevLocation = getCurrentLocation(Math.max(0, animationControl.currentTime - 1))
    
    const distanceToRef1 = calculateDistance(
      currentLocation.lat, currentLocation.lon,
      params.referenceLocation1.lat, params.referenceLocation1.lon
    )
    
    const distanceToRef2 = calculateDistance(
      currentLocation.lat, currentLocation.lon,
      params.referenceLocation2.lat, params.referenceLocation2.lon
    )

    const prevDistanceToRef1 = calculateDistance(
      prevLocation.lat, prevLocation.lon,
      params.referenceLocation1.lat, params.referenceLocation1.lon
    )

    // 計算距離變化
    const deltaDistance = distanceToRef1 - prevDistanceToRef1
    
    // 判斷移動趨勢
    let movementDirection: 'approaching' | 'departing' | 'stable'
    if (Math.abs(deltaDistance) < 5) {
      movementDirection = 'stable'
    } else if (deltaDistance < 0) {
      movementDirection = 'approaching'
    } else {
      movementDirection = 'departing'
    }

    // D2 條件: 距離變化超過門檻
    const condition1 = Math.abs(deltaDistance) > params.Thresh1 / 100 // 調整靈敏度
    const condition2 = distanceToRef2 < params.Thresh2

    // D2 觸發邏輯：顯著的距離變化或接近第二參考點
    const eventTriggered = condition1 && condition2

    return {
      condition1,
      condition2,
      eventTriggered,
      currentLocation,
      distanceToRef1,
      distanceToRef2,
      deltaDistance,
      movementDirection
    }
  }, [getCurrentLocation, animationControl.currentTime, params])

  // 創建解說內容
  const createNarrationContent = useCallback((time: number) => {
    const status = eventStatus
    const progress = ((time / 100) * 100).toFixed(1)

    let phaseTitle = ''
    let mainDescription = ''
    let technicalDetails = ''

    if (time < 10) {
      phaseTitle = '🛰️ 服務基站監測初始化'
      mainDescription = `
        <div class="phase-description">
          Event D2 監測服務基站距離變化，用於檢測 UE 的移動性和切換需求。
          此事件基於距離變化率和參考位置來觸發。
        </div>
        <p><strong>初始狀態：</strong></p>
        <ul>
          <li>當前位置：${status.currentLocation.lat.toFixed(6)}°, ${status.currentLocation.lon.toFixed(6)}°</li>
          <li>到基站1距離：${status.distanceToRef1} m</li>
          <li>到基站2距離：${status.distanceToRef2} m</li>
          <li>移動趨勢：${status.movementDirection === 'approaching' ? '接近' : status.movementDirection === 'departing' ? '遠離' : '穩定'}</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>🔧 D2 配置：</h4>
          <p>參考基站1：${params.referenceLocation1.lat.toFixed(6)}°, ${params.referenceLocation1.lon.toFixed(6)}°</p>
          <p>參考基站2：${params.referenceLocation2.lat.toFixed(6)}°, ${params.referenceLocation2.lon.toFixed(6)}°</p>
          <p>距離變化門檻：${params.Thresh1} m/s</p>
          <p>接近門檻：${params.Thresh2} m</p>
          <p>遲滯：${params.Hys} m</p>
        </div>
      `
    } else if (status.eventTriggered) {
      phaseTitle = '🚨 距離變化事件觸發'
      mainDescription = `
        <div class="phase-description">
          D2 事件已觸發！檢測到顯著的距離變化，表明 UE 正在快速移動，
          可能需要進行基站切換或調整服務品質。
        </div>
        <p><strong>觸發詳情：</strong></p>
        <ul>
          <li>距離變化：${status.deltaDistance.toFixed(1)} m/s</li>
          <li>移動狀態：${status.movementDirection === 'approaching' ? '快速接近基站' : status.movementDirection === 'departing' ? '快速遠離基站' : '穩定移動'}</li>
          <li>當前距離1：${status.distanceToRef1} m</li>
          <li>當前距離2：${status.distanceToRef2} m</li>
          <li>觸發條件：${status.condition1 ? 'D2-1 ✓' : 'D2-1 ✗'} ${status.condition2 ? 'D2-2 ✓' : 'D2-2 ✗'}</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>📊 變化分析：</h4>
          <p>距離變化率：${Math.abs(status.deltaDistance).toFixed(2)} m/s ${Math.abs(status.deltaDistance) > params.Thresh1/100 ? '✓' : '✗'}</p>
          <p>接近條件：${status.distanceToRef2} ${status.condition2 ? '<' : '≥'} ${params.Thresh2} m ${status.condition2 ? '✓' : '✗'}</p>
          <p>移動速度：${Math.abs(status.deltaDistance * 3.6).toFixed(1)} km/h</p>
          <p>建議動作：${status.eventTriggered ? '準備切換' : '維持連接'}</p>
        </div>
      `
    } else {
      phaseTitle = '📡 持續移動性監測'
      mainDescription = `
        <div class="phase-description">
          系統持續監測 UE 的移動狀態和距離變化。當檢測到快速移動或接近特定區域時，
          將觸發 D2 事件以優化網路服務。
        </div>
        <p><strong>監測狀態：</strong></p>
        <ul>
          <li>距離變化：${status.deltaDistance >= 0 ? '+' : ''}${status.deltaDistance.toFixed(1)} m/s</li>
          <li>移動趨勢：${status.movementDirection === 'approaching' ? '接近中' : status.movementDirection === 'departing' ? '遠離中' : '穩定移動'}</li>
          <li>到基站1：${status.distanceToRef1} m</li>
          <li>到基站2：${status.distanceToRef2} m (門檻：${params.Thresh2} m)</li>
        </ul>
      `
      technicalDetails = `
        <div class="technical-details">
          <h4>🎯 監測參數：</h4>
          <p>當前座標：(${status.currentLocation.lat.toFixed(6)}, ${status.currentLocation.lon.toFixed(6)})</p>
          <p>變化率檢查：${Math.abs(status.deltaDistance).toFixed(2)} m/s (需要 > ${(params.Thresh1/100).toFixed(2)} m/s)</p>
          <p>接近檢查：${status.distanceToRef2} m (需要 < ${params.Thresh2} m)</p>
          <p>移動速度：${Math.abs(status.deltaDistance * 3.6).toFixed(1)} km/h</p>
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