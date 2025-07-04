/**
 * 圖表配置工廠
 * 根據事件類型和參數生成對應的圖表配置
 */

import type { EventType, MeasurementEventParams, EventA4Params, EventD1Params, EventD2Params, EventT1Params, DataPoint, ChartAnnotation } from '../types'

// A4 事件的 RSRP 數據點（來自實際測量）
const A4_DATA_POINTS: DataPoint[] = [
  { x: 1.48, y: -51.66 }, { x: 3.65, y: -51.93 }, { x: 5.82, y: -52.45 },
  { x: 7.99, y: -53.18 }, { x: 10.17, y: -54.13 }, { x: 12.34, y: -55.38 },
  { x: 14.51, y: -56.9 }, { x: 16.68, y: -58.82 }, { x: 18.66, y: -61.08 },
  { x: 20.24, y: -63.51 }, { x: 21.32, y: -66.04 }, { x: 22.02, y: -68.77 },
  { x: 22.21, y: -71.47 }, { x: 22.81, y: -74.17 }, { x: 23.79, y: -76.41 },
  { x: 25.4, y: -78.89 }, { x: 27.35, y: -81.11 }, { x: 29.72, y: -83.25 },
  { x: 31.4, y: -84.45 }, { x: 35.25, y: -86.75 }, { x: 37.42, y: -87.36 },
  { x: 39.59, y: -87.94 }, { x: 41.76, y: -88.32 }, { x: 43.94, y: -88.58 },
  { x: 46.11, y: -88.42 }, { x: 48.28, y: -88.26 }, { x: 50.45, y: -88.02 },
  { x: 52.63, y: -87.73 }, { x: 54.8, y: -87.32 }, { x: 56.97, y: -86.84 },
  { x: 58.65, y: -86.46 }, { x: 61.51, y: -85.47 }, { x: 63.69, y: -84.75 },
  { x: 65.86, y: -83.84 }, { x: 67.83, y: -82.9 }, { x: 70.2, y: -81.45 },
  { x: 72.37, y: -79.85 }, { x: 74.38, y: -77.7 }, { x: 75.53, y: -75.79 },
  { x: 76.13, y: -71.29 }, { x: 77.31, y: -68.42 }, { x: 78.99, y: -65.89 },
  { x: 81.06, y: -63.81 }, { x: 83.24, y: -62.15 }, { x: 85.41, y: -60.98 },
  { x: 87.58, y: -60.17 }, { x: 89.75, y: -59.67 }, { x: 91.23, y: -59.54 }
]

// 生成 D1 事件的距離數據（模擬）
const generateD1DistanceData = (_params: EventD1Params): DataPoint[] => {
  const points: DataPoint[] = []
  const duration = 120 // 120 秒
  
  for (let t = 0; t <= duration; t += 1) {
    // 模擬橢圓軌跡移動
    const progress = (t / duration) * 2 * Math.PI
    const baseDistance = 1500
    const variation1 = 800 * Math.sin(progress)
    const variation2 = 600 * Math.cos(progress * 1.5)
    
    const distance = Math.abs(baseDistance + variation1 + variation2)
    points.push({ x: t, y: distance })
  }
  
  return points
}

// 生成 D2 事件的距離數據（模擬）
const generateD2DistanceData = (_params: EventD2Params): DataPoint[] => {
  const points: DataPoint[] = []
  const duration = 100
  
  for (let t = 0; t <= duration; t += 1) {
    // 模擬衛星移動導致的距離變化
    const progress = (t / duration) * Math.PI
    const baseDistance = 2000
    const satelliteMovement = 1000 * Math.sin(progress)
    const ueMovement = 300 * Math.cos(progress * 2)
    
    const distance = Math.max(100, baseDistance - satelliteMovement + ueMovement)
    points.push({ x: t, y: distance })
  }
  
  return points
}

// 生成 T1 事件的時間數據（模擬）
const generateT1TimeData = (params: EventT1Params): DataPoint[] => {
  const points: DataPoint[] = []
  const duration = 80
  
  for (let t = 0; t <= duration; t += 1) {
    // 模擬測量時間的累積
    const measurementTime = Math.min(t, params.t1Threshold + params.duration + 10)
    points.push({ x: t, y: measurementTime })
  }
  
  return points
}

// 創建 A4 事件圖表配置
const createA4ChartConfig = (params: EventA4Params, isDarkTheme: boolean) => {
  const thresholdColor = isDarkTheme ? '#ef4444' : '#dc2626'
  const enterThresholdColor = isDarkTheme ? '#10b981' : '#059669'
  const leaveThresholdColor = isDarkTheme ? '#f59e0b' : '#d97706'

  const annotations: ChartAnnotation[] = [
    {
      id: 'a4-threshold',
      type: 'line',
      value: params.Thresh,
      position: { y: params.Thresh },
      label: `A4 門檻 (${params.Thresh} dBm)`,
      color: thresholdColor,
      borderDash: [10, 5]
    },
    {
      id: 'a4-enter-threshold',
      type: 'line',
      value: params.Thresh + params.Hys,
      position: { y: params.Thresh + params.Hys },
      label: `進入門檻 (${params.Thresh + params.Hys} dBm)`,
      color: enterThresholdColor,
      borderDash: [5, 10]
    },
    {
      id: 'a4-leave-threshold',
      type: 'line',
      value: params.Thresh - params.Hys,
      position: { y: params.Thresh - params.Hys },
      label: `離開門檻 (${params.Thresh - params.Hys} dBm)`,
      color: leaveThresholdColor,
      borderDash: [15, 5]
    }
  ]

  return {
    title: `Event A4 - 鄰近基站 RSRP 測量`,
    xAxisLabel: '時間',
    yAxisLabel: 'RSRP',
    xAxisUnit: '秒',
    yAxisUnit: 'dBm',
    yAxisRange: { min: -95, max: -40 },
    datasets: [
      {
        label: '鄰近基站 RSRP',
        data: A4_DATA_POINTS,
        color: isDarkTheme ? '#3b82f6' : '#2563eb',
        type: 'line' as const,
        fill: false,
        borderWidth: 3,
        pointRadius: 4
      }
    ],
    annotations
  }
}

// 創建 D1 事件圖表配置
const createD1ChartConfig = (params: EventD1Params, isDarkTheme: boolean) => {
  const threshold1Color = isDarkTheme ? '#ef4444' : '#dc2626'
  const threshold2Color = isDarkTheme ? '#f59e0b' : '#d97706'

  const annotations: ChartAnnotation[] = [
    {
      id: 'd1-threshold1',
      type: 'line',
      value: params.Thresh1,
      position: { y: params.Thresh1 },
      label: `距離門檻1 (${params.Thresh1} m)`,
      color: threshold1Color,
      borderDash: [10, 5]
    },
    {
      id: 'd1-threshold2',
      type: 'line',
      value: params.Thresh2,
      position: { y: params.Thresh2 },
      label: `距離門檻2 (${params.Thresh2} m)`,
      color: threshold2Color,
      borderDash: [5, 10]
    }
  ]

  return {
    title: `Event D1 - 距離參考點測量`,
    xAxisLabel: '時間',
    yAxisLabel: '距離',
    xAxisUnit: '秒',
    yAxisUnit: 'm',
    yAxisRange: { min: 0, max: 3000 },
    datasets: [
      {
        label: '到參考點1距離',
        data: generateD1DistanceData(params),
        color: isDarkTheme ? '#3b82f6' : '#2563eb',
        type: 'line' as const,
        fill: false,
        borderWidth: 3,
        pointRadius: 3
      }
    ],
    annotations
  }
}

// 創建 D2 事件圖表配置
const createD2ChartConfig = (params: EventD2Params, isDarkTheme: boolean) => {
  const threshold1Color = isDarkTheme ? '#ef4444' : '#dc2626'
  const threshold2Color = isDarkTheme ? '#f59e0b' : '#d97706'

  const annotations: ChartAnnotation[] = [
    {
      id: 'd2-threshold1',
      type: 'line',
      value: params.Thresh1,
      position: { y: params.Thresh1 },
      label: `距離門檻1 (${params.Thresh1} m)`,
      color: threshold1Color,
      borderDash: [10, 5]
    },
    {
      id: 'd2-threshold2',
      type: 'line',
      value: params.Thresh2,
      position: { y: params.Thresh2 },
      label: `距離門檻2 (${params.Thresh2} m)`,
      color: threshold2Color,
      borderDash: [5, 10]
    }
  ]

  return {
    title: `Event D2 - 衛星距離變化測量`,
    xAxisLabel: '時間',
    yAxisLabel: '距離',
    xAxisUnit: '秒',
    yAxisUnit: 'm',
    yAxisRange: { min: 0, max: 4000 },
    datasets: [
      {
        label: '到移動參考點距離',
        data: generateD2DistanceData(params),
        color: isDarkTheme ? '#10b981' : '#059669',
        type: 'line' as const,
        fill: false,
        borderWidth: 3,
        pointRadius: 3
      }
    ],
    annotations
  }
}

// 創建 T1 事件圖表配置
const createT1ChartConfig = (params: EventT1Params, isDarkTheme: boolean) => {
  const thresholdColor = isDarkTheme ? '#ef4444' : '#dc2626'
  const durationColor = isDarkTheme ? '#f59e0b' : '#d97706'

  const annotations: ChartAnnotation[] = [
    {
      id: 't1-threshold',
      type: 'line',
      value: params.t1Threshold,
      position: { y: params.t1Threshold },
      label: `t1-Threshold: ${params.t1Threshold}s (進入條件: Mt > Thresh1)`,
      color: thresholdColor,
      borderDash: [10, 5]
    },
    {
      id: 't1-threshold-duration',
      type: 'line',
      value: params.t1Threshold + params.duration,
      position: { y: params.t1Threshold + params.duration },
      label: `Thresh1+Duration: ${params.t1Threshold + params.duration}s (離開條件: Mt > Thresh1+Duration)`,
      color: durationColor,
      borderDash: [5, 10]
    }
  ]

  return {
    title: `CondEvent T1 - 時間窗口條件事件 (3GPP TS 38.331)`,
    xAxisLabel: '實際時間',
    yAxisLabel: '測量時間 Mt',
    xAxisUnit: '秒',
    yAxisUnit: '秒', 
    yAxisRange: { min: 0, max: Math.max(params.t1Threshold + params.duration + 20, 60) },
    datasets: [
      {
        label: '累積測量時間 Mt (條件事件用)',
        data: generateT1TimeData(params),
        color: isDarkTheme ? '#8b5cf6' : '#7c3aed',
        type: 'line' as const,
        fill: true,
        borderWidth: 3,
        pointRadius: 3
      }
    ],
    annotations
  }
}

// 主要的圖表配置工廠函數
export const createChartConfig = <T extends MeasurementEventParams>(
  eventType: EventType,
  params: T,
  isDarkTheme: boolean
) => {
  switch (eventType) {
    case 'A4':
      return createA4ChartConfig(params as EventA4Params, isDarkTheme)
    case 'D1':
      return createD1ChartConfig(params as EventD1Params, isDarkTheme)
    case 'D2':
      return createD2ChartConfig(params as EventD2Params, isDarkTheme)
    case 'T1':
      return createT1ChartConfig(params as EventT1Params, isDarkTheme)
    default:
      throw new Error(`Unsupported event type: ${eventType}`)
  }
}

// 導出輔助函數
export {
  A4_DATA_POINTS,
  generateD1DistanceData,
  generateD2DistanceData,
  generateT1TimeData
}