/**
 * D1 事件增強查看器
 * 
 * 完成 Phase 2.2 要求：
 * - 全球化地理座標支援
 * - 統一 SIB19 平台整合
 * - 雙重距離測量視覺化
 * - 完整的參數配置界面
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
  AlertDescription
} from '@/components/ui'
import {
  Settings,
  Play,
  Pause,
  RotateCcw,
  Download,
  Info,
  MapPin,
  Satellite,
  Target
} from 'lucide-react'
import { EnhancedD1Chart } from '../charts/EnhancedD1Chart'
import { EnhancedParameterPanel } from '@/components/common/EnhancedParameterPanel'
import { ViewModeToggle } from '@/components/common/ViewModeToggle'
import { useViewModeManager } from '@/hooks/useViewModeManager'

interface D1ViewerProps {
  className?: string
  initialConfig?: Partial<D1Config>
  onConfigChange?: (config: D1Config) => void
  onEventTriggered?: (eventData: any) => void
}

interface D1Config {
  // 基本參數
  thresh1: number      // 第一距離門檻 (km)
  thresh2: number      // 第二距離門檻 (km)
  hysteresis: number   // 遲滯值 (m)
  
  // 參考位置 (全球化支援)
  referenceLatitude: number
  referenceLongitude: number
  referenceAltitude: number
  
  // 測量配置
  measurementInterval: number  // 測量間隔 (ms)
  reportingInterval: number    // 報告間隔 (ms)
  
  // 顯示選項
  showSatelliteTrajectory: boolean
  showDistanceCalculation: boolean
  showTriggerHistory: boolean
  showGeographicMap: boolean
}

const DEFAULT_D1_CONFIG: D1Config = {
  thresh1: 50.0,
  thresh2: 100.0,
  hysteresis: 0.5,
  referenceLatitude: 25.0,
  referenceLongitude: 121.0,
  referenceAltitude: 0.1,
  measurementInterval: 1000,
  reportingInterval: 5000,
  showSatelliteTrajectory: true,
  showDistanceCalculation: true,
  showTriggerHistory: true,
  showGeographicMap: false
}

export const EnhancedD1Viewer: React.FC<D1ViewerProps> = ({
  className = '',
  initialConfig = {},
  onConfigChange,
  onEventTriggered
}) => {
  // 狀態管理
  const [config, setConfig] = useState<D1Config>({
    ...DEFAULT_D1_CONFIG,
    ...initialConfig
  })
  const [isRunning, setIsRunning] = useState(false)
  const [eventHistory, setEventHistory] = useState<any[]>([])
  const [currentStatus, setCurrentStatus] = useState<'idle' | 'measuring' | 'triggered'>('idle')
  
  // 視圖模式管理
  const { currentMode, toggleMode } = useViewModeManager('d1')

  // 配置更新處理
  const handleConfigChange = useCallback((newConfig: Partial<D1Config>) => {
    const updatedConfig = { ...config, ...newConfig }
    setConfig(updatedConfig)
    onConfigChange?.(updatedConfig)
  }, [config, onConfigChange])

  // 測量控制
  const handleStart = useCallback(() => {
    setIsRunning(true)
    setCurrentStatus('measuring')
  }, [])

  const handleStop = useCallback(() => {
    setIsRunning(false)
    setCurrentStatus('idle')
  }, [])

  const handleReset = useCallback(() => {
    setIsRunning(false)
    setCurrentStatus('idle')
    setEventHistory([])
  }, [])

  // 事件觸發處理
  const handleEventTriggered = useCallback((eventData: any) => {
    setCurrentStatus('triggered')
    setEventHistory(prev => [...prev, {
      ...eventData,
      timestamp: Date.now()
    }])
    onEventTriggered?.(eventData)
    
    // 3秒後恢復測量狀態
    setTimeout(() => {
      if (isRunning) {
        setCurrentStatus('measuring')
      }
    }, 3000)
  }, [isRunning, onEventTriggered])

  // 參數定義 (用於 EnhancedParameterPanel)
  const parameterDefinitions = [
    {
      key: 'thresh1',
      label: '第一距離門檻',
      type: 'number' as const,
      unit: 'km',
      min: 1,
      max: 200,
      step: 1,
      level: 'basic' as const,
      description: '觸發 D1 事件的第一個距離門檻值'
    },
    {
      key: 'thresh2',
      label: '第二距離門檻',
      type: 'number' as const,
      unit: 'km',
      min: 1,
      max: 200,
      step: 1,
      level: 'basic' as const,
      description: '觸發 D1 事件的第二個距離門檻值'
    },
    {
      key: 'hysteresis',
      label: '遲滯值',
      type: 'number' as const,
      unit: 'm',
      min: 0.1,
      max: 10,
      step: 0.1,
      level: 'standard' as const,
      description: '防止頻繁觸發的遲滯值'
    },
    {
      key: 'referenceLatitude',
      label: '參考緯度',
      type: 'number' as const,
      unit: '°',
      min: -90,
      max: 90,
      step: 0.001,
      level: 'standard' as const,
      description: '參考位置的緯度座標 (全球化支援)'
    },
    {
      key: 'referenceLongitude',
      label: '參考經度',
      type: 'number' as const,
      unit: '°',
      min: -180,
      max: 180,
      step: 0.001,
      level: 'standard' as const,
      description: '參考位置的經度座標 (全球化支援)'
    },
    {
      key: 'referenceAltitude',
      label: '參考高度',
      type: 'number' as const,
      unit: 'km',
      min: 0,
      max: 10,
      step: 0.001,
      level: 'expert' as const,
      description: '參考位置的海拔高度'
    }
  ]

  // 渲染狀態指示器
  const renderStatusIndicator = () => {
    const statusConfig = {
      idle: { color: 'bg-gray-500', text: '待機', icon: Pause },
      measuring: { color: 'bg-blue-500', text: '測量中', icon: Play },
      triggered: { color: 'bg-red-500', text: '已觸發', icon: Target }
    }
    
    const { color, text, icon: Icon } = statusConfig[currentStatus]
    
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
            <Settings className="h-4 w-4" />
            D1 事件控制
          </span>
          {renderStatusIndicator()}
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
                停止測量
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                開始測量
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
        
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">事件觸發次數:</span>
            <div className="font-bold">{eventHistory.length}</div>
          </div>
          <div>
            <span className="text-muted-foreground">測量間隔:</span>
            <div className="font-bold">{config.measurementInterval}ms</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  // 渲染配置摘要
  const renderConfigSummary = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Info className="h-4 w-4" />
          配置摘要
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">距離門檻:</span>
            <span className="font-medium">{config.thresh1}km / {config.thresh2}km</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">參考位置:</span>
            <span className="font-medium">
              {config.referenceLatitude.toFixed(3)}°, {config.referenceLongitude.toFixed(3)}°
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">遲滯值:</span>
            <span className="font-medium">{config.hysteresis}m</span>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="h-4 w-4" />
            <span className="text-sm font-medium">全球化支援</span>
          </div>
          <Badge variant="outline" className="text-xs">
            支援全球任意參考位置
          </Badge>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className={`enhanced-d1-viewer ${className}`}>
      {/* 頂部工具欄 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Satellite className="h-5 w-5" />
          <h2 className="text-lg font-semibold">D1 事件 - 雙重距離測量</h2>
          <Badge variant="outline">全球化支援</Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <ViewModeToggle />
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            匯出數據
          </Button>
        </div>
      </div>

      {/* 全球化支援提示 */}
      <Alert className="mb-4">
        <MapPin className="h-4 w-4" />
        <AlertDescription>
          D1 事件已支援全球化：可設定任意地理位置作為參考點，不再限制於台灣地區。
        </AlertDescription>
      </Alert>

      {/* 主要內容區域 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* 圖表區域 */}
        <div className="lg:col-span-3">
          <EnhancedD1Chart
            config={config}
            isRunning={isRunning}
            onEventTriggered={handleEventTriggered}
            className="h-96"
          />
        </div>

        {/* 側邊欄 */}
        <div className="space-y-4">
          {renderControlPanel()}
          {renderConfigSummary()}
        </div>
      </div>

      {/* 底部標籤頁 */}
      <div className="mt-6">
        <Tabs defaultValue="parameters" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="parameters">參數配置</TabsTrigger>
            <TabsTrigger value="history">事件歷史</TabsTrigger>
            <TabsTrigger value="analysis">數據分析</TabsTrigger>
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
                <CardTitle className="text-sm font-medium">事件觸發歷史</CardTitle>
              </CardHeader>
              <CardContent>
                {eventHistory.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    尚無事件觸發記錄
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
                          <div>距離1: {event.distance1?.toFixed(2)}km</div>
                          <div>距離2: {event.distance2?.toFixed(2)}km</div>
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
                <CardTitle className="text-sm font-medium">數據分析</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">平均觸發間隔:</span>
                    <div className="font-bold">
                      {eventHistory.length > 1 
                        ? `${((eventHistory[eventHistory.length - 1].timestamp - eventHistory[0].timestamp) / (eventHistory.length - 1) / 1000).toFixed(1)}s`
                        : 'N/A'
                      }
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">觸發成功率:</span>
                    <div className="font-bold">
                      {isRunning ? '計算中...' : 'N/A'}
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

export default EnhancedD1Viewer
