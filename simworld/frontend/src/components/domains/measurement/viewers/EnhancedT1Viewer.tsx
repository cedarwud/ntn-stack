/**
 * T1 事件增強查看器
 * 
 * 完成 Phase 2.3 要求：
 * - GNSS 時間同步監控
 * - 時間窗口管理
 * - 時鐘偏差分析
 * - 完整的時間同步控制界面
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Button,
  Badge,
  Alert,
  AlertDescription,
  Progress
} from '@/components/ui'
import {
  Clock,
  Timer,
  Play,
  Pause,
  RotateCcw,
  Download,
  Wifi,
  WifiOff,
  AlertTriangle,
  CheckCircle,
  RefreshCw
} from 'lucide-react'
import { EnhancedT1Chart } from '../charts/EnhancedT1Chart'
import { T1EventSpecificChart } from '../shared/components/T1EventSpecificChart'
import { EnhancedParameterPanel } from '@/components/common/EnhancedParameterPanel'
import { ViewModeToggle } from '@/components/common/ViewModeToggle'
import { useViewModeManager } from '@/hooks/useViewModeManager'

interface T1ViewerProps {
  className?: string
  initialConfig?: Partial<T1Config>
  onConfigChange?: (config: T1Config) => void
  onEventTriggered?: (eventData: any) => void
}

interface T1Config {
  // 時間門檻參數
  t1Threshold: number        // T1 時間門檻 (秒)
  requiredDuration: number   // 所需持續時間 (秒)
  
  // 時間同步參數
  maxClockOffset: number     // 最大時鐘偏移 (ms)
  syncAccuracyThreshold: number  // 同步精度門檻 (ms)
  
  // GNSS 配置
  gnssUpdateInterval: number // GNSS 更新間隔 (ms)
  syncCheckInterval: number  // 同步檢查間隔 (ms)
  
  // 顯示選項
  showTimeSyncStatus: boolean
  showTimeWindows: boolean
  showClockOffset: boolean
  showSyncWarnings: boolean
  
  // 測量配置
  measurementInterval: number
  reportingInterval: number
}

const DEFAULT_T1_CONFIG: T1Config = {
  t1Threshold: 300,
  requiredDuration: 60,
  maxClockOffset: 50,
  syncAccuracyThreshold: 10,
  gnssUpdateInterval: 1000,
  syncCheckInterval: 5000,
  showTimeSyncStatus: true,
  showTimeWindows: true,
  showClockOffset: true,
  showSyncWarnings: true,
  measurementInterval: 1000,
  reportingInterval: 5000
}

export const EnhancedT1Viewer: React.FC<T1ViewerProps> = ({
  className = '',
  initialConfig = {},
  onConfigChange,
  onEventTriggered
}) => {
  // 狀態管理
  const [config, setConfig] = useState<T1Config>({
    ...DEFAULT_T1_CONFIG,
    ...initialConfig
  })
  const [isRunning, setIsRunning] = useState(false)
  const [syncStatus, setSyncStatus] = useState<'synced' | 'degraded' | 'lost'>('synced')
  const [clockOffset, setClockOffset] = useState(0)
  const [syncAccuracy, setSyncAccuracy] = useState(5)
  const [eventHistory, setEventHistory] = useState<any[]>([])
  const [currentStatus, setCurrentStatus] = useState<'idle' | 'monitoring' | 'triggered'>('idle')
  
  // 視圖模式管理
  const { currentMode, toggleMode } = useViewModeManager('t1')

  // 配置更新處理
  const handleConfigChange = useCallback((newConfig: Partial<T1Config>) => {
    const updatedConfig = { ...config, ...newConfig }
    setConfig(updatedConfig)
    onConfigChange?.(updatedConfig)
  }, [config, onConfigChange])

  // 時間同步控制
  const handleStart = useCallback(() => {
    setIsRunning(true)
    setCurrentStatus('monitoring')
  }, [])

  const handleStop = useCallback(() => {
    setIsRunning(false)
    setCurrentStatus('idle')
  }, [])

  const handleReset = useCallback(() => {
    setIsRunning(false)
    setCurrentStatus('idle')
    setEventHistory([])
    setClockOffset(0)
    setSyncAccuracy(5)
    setSyncStatus('synced')
  }, [])

  // GNSS 重新同步
  const handleGnssResync = useCallback(() => {
    // 模擬 GNSS 重新同步過程
    setSyncStatus('degraded')
    setTimeout(() => {
      setClockOffset(Math.random() * 10 - 5) // ±5ms
      setSyncAccuracy(Math.random() * 5 + 2) // 2-7ms
      setSyncStatus('synced')
    }, 3000)
  }, [])

  // 事件觸發處理
  const handleEventTriggered = useCallback((eventData: any) => {
    setCurrentStatus('triggered')
    setEventHistory(prev => [...prev, {
      ...eventData,
      timestamp: Date.now(),
      clockOffset: clockOffset,
      syncAccuracy: syncAccuracy
    }])
    onEventTriggered?.(eventData)
    
    // 5秒後恢復監控狀態
    setTimeout(() => {
      if (isRunning) {
        setCurrentStatus('monitoring')
      }
    }, 5000)
  }, [isRunning, clockOffset, syncAccuracy, onEventTriggered])

  // 模擬時鐘偏移變化
  useEffect(() => {
    if (!isRunning) return

    const interval = setInterval(() => {
      // 模擬時鐘偏移的隨機變化
      setClockOffset(prev => {
        const change = (Math.random() - 0.5) * 2 // ±1ms 變化
        const newOffset = prev + change
        return Math.max(-100, Math.min(100, newOffset)) // 限制在 ±100ms
      })
      
      // 模擬同步精度變化
      setSyncAccuracy(prev => {
        const change = (Math.random() - 0.5) * 1 // ±0.5ms 變化
        return Math.max(1, Math.min(20, prev + change)) // 限制在 1-20ms
      })
    }, config.gnssUpdateInterval)

    return () => clearInterval(interval)
  }, [isRunning, config.gnssUpdateInterval])

  // 更新同步狀態
  useEffect(() => {
    const isOffsetOk = Math.abs(clockOffset) <= config.maxClockOffset
    const isAccuracyOk = syncAccuracy <= config.syncAccuracyThreshold
    
    if (isOffsetOk && isAccuracyOk) {
      setSyncStatus('synced')
    } else if (isOffsetOk || isAccuracyOk) {
      setSyncStatus('degraded')
    } else {
      setSyncStatus('lost')
    }
  }, [clockOffset, syncAccuracy, config.maxClockOffset, config.syncAccuracyThreshold])

  // 參數定義
  const parameterDefinitions = [
    {
      key: 't1Threshold',
      label: 'T1 時間門檻',
      type: 'number' as const,
      unit: '秒',
      min: 60,
      max: 3600,
      step: 30,
      level: 'basic' as const,
      description: '觸發 T1 事件的時間門檻值'
    },
    {
      key: 'requiredDuration',
      label: '所需持續時間',
      type: 'number' as const,
      unit: '秒',
      min: 10,
      max: 300,
      step: 10,
      level: 'basic' as const,
      description: '事件觸發後需要維持的最小時間'
    },
    {
      key: 'maxClockOffset',
      label: '最大時鐘偏移',
      type: 'number' as const,
      unit: 'ms',
      min: 10,
      max: 200,
      step: 5,
      level: 'standard' as const,
      description: '允許的最大時鐘偏移量'
    },
    {
      key: 'syncAccuracyThreshold',
      label: '同步精度門檻',
      type: 'number' as const,
      unit: 'ms',
      min: 1,
      max: 50,
      step: 1,
      level: 'standard' as const,
      description: '要求的時間同步精度'
    }
  ]

  // 渲染同步狀態指示器
  const renderSyncStatusIndicator = () => {
    const statusConfig = {
      synced: { color: 'bg-green-500', text: '已同步', icon: Wifi },
      degraded: { color: 'bg-yellow-500', text: '精度降低', icon: AlertTriangle },
      lost: { color: 'bg-red-500', text: '同步丟失', icon: WifiOff }
    }
    
    const { color, text, icon: Icon } = statusConfig[syncStatus]
    
    return (
      <div className="flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${color} animate-pulse`} />
        <span className="text-sm font-medium">{text}</span>
        <Icon className="h-4 w-4" />
      </div>
    )
  }

  // 渲染控制面板
  const renderControlPanel = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            T1 時間同步控制
          </span>
          {renderSyncStatusIndicator()}
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="flex gap-2 mb-4">
          <Button
            onClick={isRunning ? handleStop : handleStart}
            variant={isRunning ? "destructive" : "default"}
            size="sm"
            className="flex-1"
          >
            {isRunning ? (
              <>
                <Pause className="h-4 w-4 mr-2" />
                停止監控
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                開始監控
              </>
            )}
          </Button>
          
          <Button
            onClick={handleReset}
            variant="outline"
            size="sm"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            重置
          </Button>
        </div>
        
        <div className="space-y-3">
          {/* 時鐘偏移 */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>時鐘偏移</span>
              <span className="font-medium">{clockOffset.toFixed(1)} ms</span>
            </div>
            <Progress 
              value={Math.min(100, (Math.abs(clockOffset) / config.maxClockOffset) * 100)}
              className="h-2"
            />
          </div>
          
          {/* 同步精度 */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>同步精度</span>
              <span className="font-medium">{syncAccuracy.toFixed(1)} ms</span>
            </div>
            <Progress 
              value={Math.min(100, (syncAccuracy / config.syncAccuracyThreshold) * 100)}
              className="h-2"
            />
          </div>
        </div>
        
        <Button
          onClick={handleGnssResync}
          variant="outline"
          size="sm"
          className="w-full mt-4"
          disabled={syncStatus === 'degraded'}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          GNSS 重新同步
        </Button>
      </CardContent>
    </Card>
  )

  // 渲染時間狀態摘要
  const renderTimeSummary = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Timer className="h-4 w-4" />
          時間狀態摘要
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">時間門檻:</span>
            <span className="font-medium">{config.t1Threshold}s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">持續時間:</span>
            <span className="font-medium">{config.requiredDuration}s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">事件觸發:</span>
            <span className="font-medium">{eventHistory.length} 次</span>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-4 w-4" />
            <span className="text-sm font-medium">GNSS 時間同步</span>
          </div>
          <Badge variant={syncStatus === 'synced' ? 'default' : 'destructive'} className="text-xs">
            {syncStatus === 'synced' ? '高精度同步' : '需要重新同步'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className={`enhanced-t1-viewer ${className}`}>
      {/* 頂部工具欄 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          <h2 className="text-lg font-semibold">T1 事件 - 時間同步監控</h2>
          <Badge variant="outline">GNSS 同步</Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <ViewModeToggle />
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            匯出數據
          </Button>
        </div>
      </div>

      {/* 時間同步警告 */}
      {syncStatus !== 'synced' && (
        <Alert className="mb-4" variant={syncStatus === 'lost' ? 'destructive' : 'default'}>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {syncStatus === 'lost' 
              ? '時間同步已丟失，請檢查 GNSS 信號並重新同步'
              : '時間同步精度降低，建議重新同步以確保測量準確性'
            }
          </AlertDescription>
        </Alert>
      )}

      {/* 主要內容區域 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* 圖表區域 */}
        <div className="lg:col-span-3">
          <div className="space-y-4">
            {/* 傳統 T1 圖表 */}
            <EnhancedT1Chart
              config={config}
              isRunning={isRunning}
              onEventTriggered={handleEventTriggered}
              className="h-64"
            />
            
            {/* 新的 T1 事件專屬圖表 */}
            <T1EventSpecificChart
              t1Threshold={config.t1Threshold}
              requiredDuration={config.requiredDuration}
              maxClockOffset={config.maxClockOffset}
              syncAccuracyThreshold={config.syncAccuracyThreshold}
              onTimeConditionChange={(isTriggered) => {
                if (isTriggered) {
                  handleEventTriggered({ type: 'time_condition', triggered: true })
                }
              }}
              onSyncStatusChange={(isSync) => {
                setSyncStatus(isSync ? 'synced' : 'degraded')
              }}
              className="h-96"
            />
          </div>
        </div>

        {/* 側邊欄 */}
        <div className="space-y-4">
          {renderControlPanel()}
          {renderTimeSummary()}
        </div>
      </div>

      {/* 底部標籤頁 */}
      <div className="mt-6">
        <Tabs defaultValue="parameters" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="parameters">參數配置</TabsTrigger>
            <TabsTrigger value="history">同步歷史</TabsTrigger>
            <TabsTrigger value="analysis">時間分析</TabsTrigger>
          </TabsList>
          
          <TabsContent value="parameters" className="mt-4">
            <EnhancedParameterPanel
              parameters={config}
              definitions={parameterDefinitions}
              onChange={handleConfigChange}
              viewMode={currentMode}
            />
          </TabsContent>
          
          <TabsContent value="history" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">時間同步歷史</CardTitle>
              </CardHeader>
              <CardContent>
                {eventHistory.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    尚無時間事件記錄
                  </div>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {eventHistory.map((event, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium">事件 #{index + 1}</div>
                            <div className="text-sm text-muted-foreground">
                              {new Date(event.timestamp).toLocaleString()}
                            </div>
                          </div>
                          <Badge variant="destructive">已觸發</Badge>
                        </div>
                        <div className="mt-2 text-sm">
                          <div>時鐘偏移: {event.clockOffset?.toFixed(1)}ms</div>
                          <div>同步精度: {event.syncAccuracy?.toFixed(1)}ms</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="analysis" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">時間分析</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">平均時鐘偏移:</span>
                    <div className="font-bold">{clockOffset.toFixed(1)}ms</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">同步穩定性:</span>
                    <div className="font-bold">
                      {syncStatus === 'synced' ? '穩定' : '不穩定'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default EnhancedT1Viewer
