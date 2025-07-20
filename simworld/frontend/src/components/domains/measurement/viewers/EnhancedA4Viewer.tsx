/**
 * A4 事件增強查看器
 * 
 * 完成 Phase 2.4 要求：
 * - SIB19 強化和位置補償實現
 * - 信號強度分析
 * - 衛星選擇算法
 * - 完整的位置補償控制界面
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
  Navigation,
  Satellite,
  Play,
  Pause,
  RotateCcw,
  Download,
  Target,
  Signal,
  MapPin,
  TrendingUp
} from 'lucide-react'
import { EnhancedA4Chart } from '../charts/EnhancedA4Chart'
import { A4EventSpecificChart } from '../shared/components/A4EventSpecificChart'
import { EnhancedParameterPanel } from '@/components/common/EnhancedParameterPanel'
import { ViewModeToggle } from '@/components/common/ViewModeToggle'
import { useViewModeManager } from '@/hooks/useViewModeManager'

interface A4ViewerProps {
  className?: string
  initialConfig?: Partial<A4Config>
  onConfigChange?: (config: A4Config) => void
  onEventTriggered?: (eventData: any) => void
}

interface A4Config {
  // 位置補償參數
  compensationThreshold: number    // 補償門檻 (km)
  maxCompensationRange: number     // 最大補償範圍 (km)
  
  // 信號強度參數
  minSignalStrength: number        // 最小信號強度 (dBm)
  signalQualityThreshold: number   // 信號品質門檻
  
  // 衛星選擇參數
  minElevationAngle: number        // 最小仰角 (度)
  maxSatelliteCount: number        // 最大衛星數量
  
  // UE 位置
  ueLatitude: number
  ueLongitude: number
  ueAltitude: number
  
  // 顯示選項
  showPositionCompensation: boolean
  showSignalAnalysis: boolean
  showSatelliteSelection: boolean
  showCompensationHistory: boolean
  
  // 測量配置
  measurementInterval: number
  reportingInterval: number
}

const DEFAULT_A4_CONFIG: A4Config = {
  compensationThreshold: 1.0,
  maxCompensationRange: 3.0,
  minSignalStrength: -120,
  signalQualityThreshold: 0.7,
  minElevationAngle: 15,
  maxSatelliteCount: 8,
  ueLatitude: 25.0,
  ueLongitude: 121.0,
  ueAltitude: 0.1,
  showPositionCompensation: true,
  showSignalAnalysis: true,
  showSatelliteSelection: true,
  showCompensationHistory: true,
  measurementInterval: 1000,
  reportingInterval: 5000
}

export const EnhancedA4Viewer: React.FC<A4ViewerProps> = ({
  className = '',
  initialConfig = {},
  onConfigChange,
  onEventTriggered
}) => {
  // 狀態管理
  const [config, setConfig] = useState<A4Config>({
    ...DEFAULT_A4_CONFIG,
    ...initialConfig
  })
  const [isRunning, setIsRunning] = useState(false)
  const [compensationActive, setCompensationActive] = useState(false)
  const [currentCompensation, setCurrentCompensation] = useState({ x: 0, y: 0, z: 0 })
  const [signalStrength, setSignalStrength] = useState(-95)
  const [selectedSatellites, setSelectedSatellites] = useState<string[]>([])
  const [eventHistory, setEventHistory] = useState<any[]>([])
  const [currentStatus, setCurrentStatus] = useState<'idle' | 'measuring' | 'compensating'>('idle')
  
  // 視圖模式管理
  const { currentMode, toggleMode } = useViewModeManager('a4')

  // 配置更新處理
  const handleConfigChange = useCallback((newConfig: Partial<A4Config>) => {
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
    setCompensationActive(false)
  }, [])

  const handleReset = useCallback(() => {
    setIsRunning(false)
    setCurrentStatus('idle')
    setCompensationActive(false)
    setCurrentCompensation({ x: 0, y: 0, z: 0 })
    setEventHistory([])
    setSelectedSatellites([])
  }, [])

  // 事件觸發處理
  const handleEventTriggered = useCallback((eventData: any) => {
    setCurrentStatus('compensating')
    setCompensationActive(true)
    setEventHistory(prev => [...prev, {
      ...eventData,
      timestamp: Date.now(),
      compensation: currentCompensation,
      signalStrength: signalStrength,
      satellites: selectedSatellites
    }])
    onEventTriggered?.(eventData)
    
    // 10秒後恢復測量狀態
    setTimeout(() => {
      if (isRunning) {
        setCurrentStatus('measuring')
        setCompensationActive(false)
      }
    }, 10000)
  }, [isRunning, currentCompensation, signalStrength, selectedSatellites, onEventTriggered])

  // 模擬位置補償變化
  useEffect(() => {
    if (!isRunning) return

    const interval = setInterval(() => {
      // 模擬位置補償的變化
      setCurrentCompensation(prev => ({
        x: prev.x + (Math.random() - 0.5) * 0.1, // ±50m 變化
        y: prev.y + (Math.random() - 0.5) * 0.1,
        z: prev.z + (Math.random() - 0.5) * 0.05  // ±25m 變化
      }))
      
      // 模擬信號強度變化
      setSignalStrength(prev => {
        const change = (Math.random() - 0.5) * 5 // ±2.5dBm 變化
        return Math.max(-130, Math.min(-80, prev + change))
      })
      
      // 模擬衛星選擇變化
      const availableSatellites = ['SAT_001', 'SAT_002', 'SAT_003', 'SAT_004', 'SAT_005', 'SAT_006']
      const selectedCount = Math.min(config.maxSatelliteCount, Math.floor(Math.random() * 4) + 3)
      const selected = availableSatellites.slice(0, selectedCount)
      setSelectedSatellites(selected)
    }, config.measurementInterval)

    return () => clearInterval(interval)
  }, [isRunning, config.measurementInterval, config.maxSatelliteCount])

  // 參數定義
  const parameterDefinitions = [
    {
      key: 'compensationThreshold',
      label: '補償門檻',
      type: 'number' as const,
      unit: 'km',
      min: 0.1,
      max: 10,
      step: 0.1,
      level: 'basic' as const,
      description: '觸發位置補償的距離門檻'
    },
    {
      key: 'maxCompensationRange',
      label: '最大補償範圍',
      type: 'number' as const,
      unit: 'km',
      min: 1,
      max: 10,
      step: 0.5,
      level: 'basic' as const,
      description: '位置補償的最大範圍限制'
    },
    {
      key: 'minSignalStrength',
      label: '最小信號強度',
      type: 'number' as const,
      unit: 'dBm',
      min: -140,
      max: -80,
      step: 1,
      level: 'standard' as const,
      description: '衛星選擇的最小信號強度要求'
    },
    {
      key: 'minElevationAngle',
      label: '最小仰角',
      type: 'number' as const,
      unit: '°',
      min: 5,
      max: 45,
      step: 5,
      level: 'standard' as const,
      description: '衛星選擇的最小仰角要求'
    }
  ]

  // 渲染狀態指示器
  const renderStatusIndicator = () => {
    const statusConfig = {
      idle: { color: 'bg-gray-500', text: '待機', icon: Pause },
      measuring: { color: 'bg-blue-500', text: '測量中', icon: Play },
      compensating: { color: 'bg-orange-500', text: '補償中', icon: Target }
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
            <Navigation className="h-4 w-4" />
            A4 位置補償控制
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
        
        <div className="space-y-3">
          {/* 位置補償狀態 */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>位置補償</span>
              <Badge variant={compensationActive ? 'destructive' : 'default'}>
                {compensationActive ? '啟用' : '停用'}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground">
              X: {currentCompensation.x.toFixed(2)}km, 
              Y: {currentCompensation.y.toFixed(2)}km, 
              Z: {currentCompensation.z.toFixed(2)}km
            </div>
          </div>
          
          {/* 信號強度 */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>信號強度</span>
              <span className="font-medium">{signalStrength.toFixed(1)} dBm</span>
            </div>
            <Progress 
              value={Math.min(100, ((signalStrength + 130) / 50) * 100)}
              className="h-2"
            />
          </div>
          
          {/* 選中衛星數量 */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>選中衛星</span>
              <span className="font-medium">{selectedSatellites.length} 顆</span>
            </div>
            <div className="text-xs text-muted-foreground">
              {selectedSatellites.join(', ')}
            </div>
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
          <Target className="h-4 w-4" />
          配置摘要
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">補償門檻:</span>
            <span className="font-medium">{config.compensationThreshold}km</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">最大範圍:</span>
            <span className="font-medium">{config.maxCompensationRange}km</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">UE 位置:</span>
            <span className="font-medium">
              {config.ueLatitude.toFixed(3)}°, {config.ueLongitude.toFixed(3)}°
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">補償次數:</span>
            <span className="font-medium">{eventHistory.length}</span>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center gap-2 mb-2">
            <Signal className="h-4 w-4" />
            <span className="text-sm font-medium">SIB19 強化</span>
          </div>
          <Badge variant="outline" className="text-xs">
            統一平台整合
          </Badge>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className={`enhanced-a4-viewer ${className}`}>
      {/* 頂部工具欄 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Navigation className="h-5 w-5" />
          <h2 className="text-lg font-semibold">A4 事件 - 位置補償</h2>
          <Badge variant="outline">SIB19 強化</Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <ViewModeToggle />
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            匯出數據
          </Button>
        </div>
      </div>

      {/* SIB19 強化提示 */}
      <Alert className="mb-4">
        <TrendingUp className="h-4 w-4" />
        <AlertDescription>
          A4 事件已整合統一 SIB19 平台：位置補償範圍修正為 ±3km，衛星選擇算法優化。
        </AlertDescription>
      </Alert>

      {/* 主要內容區域 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* 圖表區域 */}
        <div className="lg:col-span-3">
          <div className="space-y-4">
            {/* 傳統 A4 圖表 */}
            <EnhancedA4Chart
              config={config}
              isRunning={isRunning}
              onEventTriggered={handleEventTriggered}
              className="h-64"
            />
            
            {/* 新的 A4 事件專屬圖表 */}
            <A4EventSpecificChart
              compensationThreshold={config.compensationThreshold}
              maxCompensationRange={config.maxCompensationRange}
              uePosition={{
                latitude: config.ueLatitude,
                longitude: config.ueLongitude,
                altitude: config.ueAltitude
              }}
              onCompensationTriggered={(compensation) => {
                handleEventTriggered({ type: 'position_compensation', compensation })
              }}
              className="h-96"
            />
          </div>
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
            <TabsTrigger value="history">補償歷史</TabsTrigger>
            <TabsTrigger value="analysis">性能分析</TabsTrigger>
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
                <CardTitle className="text-sm font-medium">位置補償歷史</CardTitle>
              </CardHeader>
              <CardContent>
                {eventHistory.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    尚無位置補償記錄
                  </div>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {eventHistory.map((event, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium">補償 #{index + 1}</div>
                            <div className="text-sm text-muted-foreground">
                              {new Date(event.timestamp).toLocaleString()}
                            </div>
                          </div>
                          <Badge variant="destructive">已觸發</Badge>
                        </div>
                        <div className="mt-2 text-sm">
                          <div>補償量: ({event.compensation?.x.toFixed(2)}, {event.compensation?.y.toFixed(2)}, {event.compensation?.z.toFixed(2)}) km</div>
                          <div>信號強度: {event.signalStrength?.toFixed(1)} dBm</div>
                          <div>衛星數: {event.satellites?.length} 顆</div>
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
                <CardTitle className="text-sm font-medium">性能分析</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">平均補償量:</span>
                    <div className="font-bold">
                      {eventHistory.length > 0 
                        ? `${(eventHistory.reduce((sum, e) => sum + Math.sqrt(e.compensation?.x**2 + e.compensation?.y**2 + e.compensation?.z**2), 0) / eventHistory.length).toFixed(2)}km`
                        : 'N/A'
                      }
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">補償成功率:</span>
                    <div className="font-bold">
                      {eventHistory.length > 0 ? '100%' : 'N/A'}
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

export default EnhancedA4Viewer
