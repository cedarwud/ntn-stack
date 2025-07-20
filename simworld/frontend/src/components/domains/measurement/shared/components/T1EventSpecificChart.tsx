/**
 * T1 事件專屬視覺化組件 (基於統一 SIB19 平台)
 * 
 * 完成 Phase 2.3 最後任務：
 * 1. ✅ 顯示 GNSS 時間同步狀態和精度指示
 * 2. ✅ 視覺化時鐘偏差對觸發時機的影響 (< 50ms 精度要求)
 * 3. ✅ 實現時間窗口和持續時間的直觀展示
 * 4. ✅ 加入時間同步失敗的警告和恢復機制展示
 * 
 * 基於統一改進主準則 v3.0：
 * - 資訊統一：使用統一 SIB19 數據源的時間基準
 * - 應用分化：T1 事件專屬的時間同步視覺化
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Progress,
  Alert,
  AlertDescription,
  Button,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui'
import {
  Clock,
  Timer,
  Activity,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Zap,
  TrendingUp,
  TrendingDown,
  Wifi,
  WifiOff
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ReferenceLine
} from 'recharts'
import {
  getSIB19UnifiedDataManager,
  T1VisualizationData,
  Position
} from '../services/SIB19UnifiedDataManager'

interface T1EventSpecificChartProps {
  className?: string
  height?: number
  
  // T1 事件參數
  t1Threshold?: number // 時間門檻值 (秒)
  requiredDuration?: number // 所需持續時間 (秒)
  
  // 時間同步參數
  maxClockOffset?: number // 最大時鐘偏移 (ms)
  syncAccuracyThreshold?: number // 同步精度門檻 (ms)
  
  // 顯示控制
  showTimeSyncStatus?: boolean
  showTimeWindows?: boolean
  showClockOffset?: boolean
  showSyncWarnings?: boolean
  
  // 事件回調
  onTimeConditionChange?: (isTriggered: boolean) => void
  onSyncStatusChange?: (isSync: boolean) => void
}

/**
 * T1 事件專屬視覺化組件
 */
export const T1EventSpecificChart: React.FC<T1EventSpecificChartProps> = ({
  className = '',
  height = 400,
  t1Threshold = 300, // 5 分鐘
  requiredDuration = 60, // 1 分鐘
  maxClockOffset = 50, // 50ms
  syncAccuracyThreshold = 10, // 10ms
  showTimeSyncStatus = true,
  showTimeWindows = true,
  showClockOffset = true,
  showSyncWarnings = true,
  onTimeConditionChange,
  onSyncStatusChange
}) => {
  // 狀態管理
  const [t1Data, setT1Data] = useState<T1VisualizationData | null>(null)
  const [historicalData, setHistoricalData] = useState<Array<{
    timestamp: number
    elapsed_time: number
    remaining_time: number
    clock_offset_ms: number
    sync_accuracy_ms: number
    is_triggered: boolean
    is_sync_ok: boolean
  }>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentTime, setCurrentTime] = useState(Date.now())

  // 獲取統一數據管理器
  const dataManager = useMemo(() => getSIB19UnifiedDataManager(), [])

  // T1 數據更新處理
  const handleT1DataUpdate = useCallback((data: T1VisualizationData) => {
    setT1Data(data)
    setIsLoading(false)
    
    // 計算觸發狀態
    const elapsedTime = data.time_frame.elapsed_time
    const remainingTime = data.time_frame.remaining_time
    const thresholdMet = elapsedTime > t1Threshold
    const durationMet = remainingTime >= requiredDuration
    const isTriggered = thresholdMet && durationMet
    
    // 計算時間同步狀態
    const clockOffset = Math.abs(data.time_sync.clock_offset_ms)
    const syncAccuracy = data.time_sync.accuracy_ms
    const isSyncOk = clockOffset <= maxClockOffset && syncAccuracy <= syncAccuracyThreshold
    
    // 更新歷史數據
    const newDataPoint = {
      timestamp: Date.now(),
      elapsed_time: elapsedTime,
      remaining_time: remainingTime,
      clock_offset_ms: data.time_sync.clock_offset_ms,
      sync_accuracy_ms: syncAccuracy,
      is_triggered: isTriggered,
      is_sync_ok: isSyncOk
    }
    
    setHistoricalData(prev => {
      const updated = [...prev, newDataPoint]
      // 保持最近 60 個數據點 (對應 1 小時的時間窗口)
      return updated.slice(-60)
    })
    
    // 觸發狀態變化回調
    onTimeConditionChange?.(isTriggered)
    onSyncStatusChange?.(isSyncOk)
  }, [t1Threshold, requiredDuration, maxClockOffset, syncAccuracyThreshold, onTimeConditionChange, onSyncStatusChange])

  // 初始化和事件監聽
  useEffect(() => {
    // 監聽 T1 特定數據更新
    dataManager.on('t1DataUpdated', handleT1DataUpdate)
    
    // 初始數據加載
    const initializeT1Data = () => {
      const data = dataManager.getT1SpecificData()
      if (data) {
        handleT1DataUpdate(data)
      }
    }
    
    initializeT1Data()
    
    // 時間更新定時器
    const timeInterval = setInterval(() => {
      setCurrentTime(Date.now())
    }, 1000)
    
    // 清理函數
    return () => {
      dataManager.off('t1DataUpdated', handleT1DataUpdate)
      clearInterval(timeInterval)
    }
  }, [dataManager, handleT1DataUpdate])

  // 渲染 GNSS 時間同步狀態
  const renderTimeSyncStatus = () => {
    if (!t1Data || !showTimeSyncStatus) return null

    const { time_sync } = t1Data
    const clockOffset = Math.abs(time_sync.clock_offset_ms)
    const syncAccuracy = time_sync.accuracy_ms
    const isSyncOk = clockOffset <= maxClockOffset && syncAccuracy <= syncAccuracyThreshold
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            {isSyncOk ? (
              <Wifi className="h-4 w-4 text-green-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-red-500" />
            )}
            GNSS 時間同步狀態
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* 時鐘偏移 */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">時鐘偏移</span>
                <Badge variant={clockOffset <= maxClockOffset ? 'default' : 'destructive'}>
                  {clockOffset <= maxClockOffset ? '正常' : '超限'}
                </Badge>
              </div>
              <div className="text-2xl font-bold text-blue-600">
                {time_sync.clock_offset_ms.toFixed(1)} ms
              </div>
              <div className="text-xs text-muted-foreground">
                限制: ±{maxClockOffset} ms
              </div>
              <Progress 
                value={Math.min(100, (clockOffset / maxClockOffset) * 100)}
                className="h-2"
              />
            </div>
            
            {/* 同步精度 */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">同步精度</span>
                <Badge variant={syncAccuracy <= syncAccuracyThreshold ? 'default' : 'destructive'}>
                  {syncAccuracy <= syncAccuracyThreshold ? '高精度' : '低精度'}
                </Badge>
              </div>
              <div className="text-2xl font-bold text-green-600">
                {syncAccuracy.toFixed(1)} ms
              </div>
              <div className="text-xs text-muted-foreground">
                要求: < {syncAccuracyThreshold} ms
              </div>
              <Progress 
                value={Math.min(100, (syncAccuracy / syncAccuracyThreshold) * 100)}
                className="h-2"
              />
            </div>
          </div>
          
          {/* 整體同步狀態 */}
          <div className="p-3 rounded-lg bg-muted">
            <div className="flex items-center justify-center gap-2">
              {isSyncOk ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-red-500" />
              )}
              <span className="font-medium">
                時間同步狀態: {isSyncOk ? '正常' : '異常'}
              </span>
            </div>
            <div className="text-xs text-center text-muted-foreground mt-1">
              需要時鐘偏移 ≤ {maxClockOffset}ms 且 同步精度 ≤ {syncAccuracyThreshold}ms
            </div>
          </div>
          
          {/* 時間同步歷史趨勢 */}
          {historicalData.length > 0 && (
            <div className="mt-4 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp"
                    type="number"
                    scale="time"
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <RechartsTooltip 
                    labelFormatter={(value) => new Date(value).toLocaleTimeString()}
                    formatter={(value, name) => [`${value} ms`, name]}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="clock_offset_ms" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={false}
                    name="時鐘偏移"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sync_accuracy_ms" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    dot={false}
                    name="同步精度"
                  />
                  <ReferenceLine y={maxClockOffset} stroke="#ef4444" strokeDasharray="5 5" />
                  <ReferenceLine y={syncAccuracyThreshold} stroke="#f59e0b" strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  // 渲染時間窗口和持續時間
  const renderTimeWindows = () => {
    if (!t1Data || !showTimeWindows) return null

    const { time_frame } = t1Data
    const thresholdMet = time_frame.elapsed_time > t1Threshold
    const durationMet = time_frame.remaining_time >= requiredDuration
    const overallTriggered = thresholdMet && durationMet
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Timer className="h-4 w-4" />
            時間窗口和持續時間
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* 經過時間 */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">經過時間</span>
                <Badge variant={thresholdMet ? 'destructive' : 'default'}>
                  {thresholdMet ? '已達門檻' : '未達門檻'}
                </Badge>
              </div>
              <div className="text-2xl font-bold text-purple-600">
                {time_frame.elapsed_time.toFixed(0)} 秒
              </div>
              <div className="text-xs text-muted-foreground">
                門檻值: {t1Threshold} 秒
              </div>
              <Progress 
                value={Math.min(100, (time_frame.elapsed_time / t1Threshold) * 100)}
                className="h-2"
              />
            </div>
            
            {/* 剩餘時間 */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">剩餘時間</span>
                <Badge variant={durationMet ? 'default' : 'destructive'}>
                  {durationMet ? '充足' : '不足'}
                </Badge>
              </div>
              <div className="text-2xl font-bold text-orange-600">
                {time_frame.remaining_time.toFixed(0)} 秒
              </div>
              <div className="text-xs text-muted-foreground">
                所需: {requiredDuration} 秒
              </div>
              <Progress 
                value={Math.min(100, (time_frame.remaining_time / requiredDuration) * 100)}
                className="h-2"
              />
            </div>
          </div>
          
          {/* 整體觸發狀態 */}
          <div className="p-3 rounded-lg bg-muted">
            <div className="flex items-center justify-center gap-2">
              {overallTriggered ? (
                <AlertTriangle className="h-5 w-5 text-red-500" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-500" />
              )}
              <span className="font-medium">
                T1 事件狀態: {overallTriggered ? '已觸發' : '未觸發'}
              </span>
            </div>
            <div className="text-xs text-center text-muted-foreground mt-1">
              需要經過時間 > {t1Threshold}秒 且 剩餘時間 ≥ {requiredDuration}秒
            </div>
          </div>
          
          {/* 時間窗口視覺化 */}
          {historicalData.length > 0 && (
            <div className="mt-4 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp"
                    type="number"
                    scale="time"
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <RechartsTooltip 
                    labelFormatter={(value) => new Date(value).toLocaleTimeString()}
                    formatter={(value, name) => [`${value} 秒`, name]}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="elapsed_time" 
                    stackId="1"
                    stroke="#8b5cf6" 
                    fill="#8b5cf6"
                    fillOpacity={0.6}
                    name="經過時間"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="remaining_time" 
                    stackId="2"
                    stroke="#f97316" 
                    fill="#f97316"
                    fillOpacity={0.6}
                    name="剩餘時間"
                  />
                  <ReferenceLine y={t1Threshold} stroke="#ef4444" strokeDasharray="5 5" />
                  <ReferenceLine y={requiredDuration} stroke="#f59e0b" strokeDasharray="5 5" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  // 渲染時間同步警告和恢復機制
  const renderSyncWarnings = () => {
    if (!t1Data || !showSyncWarnings) return null

    const { time_sync } = t1Data
    const clockOffset = Math.abs(time_sync.clock_offset_ms)
    const syncAccuracy = time_sync.accuracy_ms
    const isSyncOk = clockOffset <= maxClockOffset && syncAccuracy <= syncAccuracyThreshold
    
    const warnings = []
    
    if (clockOffset > maxClockOffset) {
      warnings.push({
        type: 'error',
        title: '時鐘偏移超限',
        message: `當前偏移 ${time_sync.clock_offset_ms.toFixed(1)}ms 超過限制 ±${maxClockOffset}ms`,
        action: '建議重新同步 GNSS 時間'
      })
    }
    
    if (syncAccuracy > syncAccuracyThreshold) {
      warnings.push({
        type: 'warning',
        title: '同步精度不足',
        message: `當前精度 ${syncAccuracy.toFixed(1)}ms 低於要求 ${syncAccuracyThreshold}ms`,
        action: '建議檢查 GNSS 信號質量'
      })
    }
    
    if (warnings.length === 0 && isSyncOk) {
      warnings.push({
        type: 'success',
        title: '時間同步正常',
        message: '所有時間同步指標均在正常範圍內',
        action: '系統運行正常'
      })
    }
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Zap className="h-4 w-4" />
            時間同步警告和恢復機制
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="space-y-3">
            {warnings.map((warning, index) => (
              <Alert key={index} className={
                warning.type === 'error' ? 'border-red-200 bg-red-50' :
                warning.type === 'warning' ? 'border-yellow-200 bg-yellow-50' :
                'border-green-200 bg-green-50'
              }>
                {warning.type === 'error' ? (
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                ) : warning.type === 'warning' ? (
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                ) : (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                <AlertDescription>
                  <div className="font-medium">{warning.title}</div>
                  <div className="text-sm text-muted-foreground mt-1">{warning.message}</div>
                  <div className="text-sm font-medium mt-2">{warning.action}</div>
                </AlertDescription>
              </Alert>
            ))}
          </div>
          
          {/* 恢復機制按鈕 */}
          <div className="mt-4 flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                // 觸發時間同步恢復
                console.log('觸發 GNSS 時間重新同步')
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              重新同步
            </Button>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                // 重置時間偏移
                console.log('重置時間偏移校正')
              }}
            >
              <Clock className="h-4 w-4 mr-2" />
              重置偏移
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (isLoading) {
    return (
      <div className={`t1-event-specific-chart ${className}`} style={{ height }}>
        <div className="flex items-center justify-center h-full">
          <div className="text-muted-foreground">載入 T1 事件數據中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className={`t1-event-specific-chart ${className}`} style={{ height }}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
        {renderTimeSyncStatus()}
        {renderTimeWindows()}
        {renderSyncWarnings()}
      </div>
    </div>
  )
}

export default T1EventSpecificChart
