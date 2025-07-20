/**
 * D1 事件專屬圖表組件
 * 
 * 基於統一 SIB19 平台的 D1 事件特定視覺化
 * 功能特點：
 * - 固定參考位置距離計算展示
 * - 智能服務衛星選擇視覺化
 * - 全球化地理座標支援
 * - 雙重距離門檻監控
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  Scatter,
  ScatterChart,
  Cell
} from 'recharts'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Alert,
  AlertDescription,
  Progress
} from '@/components/ui'
import {
  MapPin,
  Satellite,
  Target,
  TrendingUp,
  Globe,
  Navigation,
  Signal
} from 'lucide-react'

interface D1EventSpecificChartProps {
  referenceLatitude: number
  referenceLongitude: number
  referenceAltitude: number
  thresh1: number
  thresh2: number
  hysteresis: number
  onDistanceThresholdCrossed?: (crossed: boolean, distance: number) => void
  onSatelliteSelectionChange?: (satellites: string[]) => void
  className?: string
}

interface DistanceDataPoint {
  timestamp: string
  distance1: number
  distance2: number
  threshold1: number
  threshold2: number
  triggered: boolean
  uePosition: {
    latitude: number
    longitude: number
    altitude: number
  }
}

interface SatelliteInfo {
  id: string
  elevation: number
  azimuth: number
  distance: number
  signalStrength: number
  selected: boolean
  quality: 'excellent' | 'good' | 'fair' | 'poor'
}

export const D1EventSpecificChart: React.FC<D1EventSpecificChartProps> = ({
  referenceLatitude,
  referenceLongitude,
  referenceAltitude,
  thresh1,
  thresh2,
  hysteresis,
  onDistanceThresholdCrossed,
  onSatelliteSelectionChange,
  className = ''
}) => {
  // 狀態管理
  const [distanceData, setDistanceData] = useState<DistanceDataPoint[]>([])
  const [satellites, setSatellites] = useState<SatelliteInfo[]>([])
  const [currentDistance, setCurrentDistance] = useState(0)
  const [isThresholdCrossed, setIsThresholdCrossed] = useState(false)
  const [selectedSatellites, setSelectedSatellites] = useState<string[]>([])

  // 計算大圓距離
  const calculateGreatCircleDistance = useCallback((
    lat1: number, lon1: number, alt1: number,
    lat2: number, lon2: number, alt2: number
  ): number => {
    const R = 6371.0 // 地球半徑 (km)
    
    const lat1Rad = lat1 * Math.PI / 180
    const lon1Rad = lon1 * Math.PI / 180
    const lat2Rad = lat2 * Math.PI / 180
    const lon2Rad = lon2 * Math.PI / 180
    
    const dlat = lat2Rad - lat1Rad
    const dlon = lon2Rad - lon1Rad
    
    const a = Math.sin(dlat/2) * Math.sin(dlat/2) +
              Math.cos(lat1Rad) * Math.cos(lat2Rad) *
              Math.sin(dlon/2) * Math.sin(dlon/2)
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
    const distance = R * c
    
    // 考慮高度差
    const altDiff = Math.abs(alt2 - alt1)
    return Math.sqrt(distance * distance + altDiff * altDiff)
  }, [])

  // 模擬 UE 位置變化
  const simulateUEMovement = useCallback(() => {
    const time = Date.now()
    const timeInSeconds = time / 1000
    
    // 模擬 UE 在參考位置周圍移動
    const radius = 0.5 + 0.3 * Math.sin(timeInSeconds / 100) // 0.2-0.8 度範圍
    const angle = timeInSeconds / 50 // 緩慢旋轉
    
    const ueLatitude = referenceLatitude + radius * Math.cos(angle)
    const ueLongitude = referenceLongitude + radius * Math.sin(angle)
    const ueAltitude = referenceAltitude + 0.05 * Math.sin(timeInSeconds / 30)
    
    // 計算距離
    const distance1 = calculateGreatCircleDistance(
      referenceLatitude, referenceLongitude, referenceAltitude,
      ueLatitude, ueLongitude, ueAltitude
    )
    
    const distance2 = distance1 * (1 + 0.1 * Math.sin(timeInSeconds / 80)) // 第二距離略有變化
    
    // 檢查門檻觸發
    const triggered = distance1 > thresh1 || distance2 > thresh2
    
    const newDataPoint: DistanceDataPoint = {
      timestamp: new Date(time).toISOString(),
      distance1,
      distance2,
      threshold1: thresh1,
      threshold2: thresh2,
      triggered,
      uePosition: {
        latitude: ueLatitude,
        longitude: ueLongitude,
        altitude: ueAltitude
      }
    }
    
    setDistanceData(prev => {
      const newData = [...prev, newDataPoint].slice(-100) // 保留最近 100 個點
      return newData
    })
    
    setCurrentDistance(distance1)
    
    // 觸發回調
    if (triggered !== isThresholdCrossed) {
      setIsThresholdCrossed(triggered)
      onDistanceThresholdCrossed?.(triggered, distance1)
    }
  }, [
    referenceLatitude, referenceLongitude, referenceAltitude,
    thresh1, thresh2, calculateGreatCircleDistance,
    isThresholdCrossed, onDistanceThresholdCrossed
  ])

  // 模擬衛星選擇
  const simulateSatelliteSelection = useCallback(() => {
    const satellitePool = [
      'SAT_001', 'SAT_002', 'SAT_003', 'SAT_004', 'SAT_005',
      'SAT_006', 'SAT_007', 'SAT_008', 'SAT_009', 'SAT_010'
    ]
    
    const newSatellites: SatelliteInfo[] = satellitePool.map(id => {
      const elevation = 15 + Math.random() * 75 // 15-90 度
      const azimuth = Math.random() * 360
      const distance = 500 + Math.random() * 1500 // 500-2000 km
      const signalStrength = -120 + Math.random() * 40 // -120 to -80 dBm
      
      // 衛星品質評估
      let quality: SatelliteInfo['quality'] = 'poor'
      if (elevation > 60 && signalStrength > -90) quality = 'excellent'
      else if (elevation > 45 && signalStrength > -100) quality = 'good'
      else if (elevation > 30 && signalStrength > -110) quality = 'fair'
      
      return {
        id,
        elevation,
        azimuth,
        distance,
        signalStrength,
        selected: false,
        quality
      }
    })
    
    // 智能衛星選擇算法
    // 基於仰角 (50%) + 信號強度 (30%) + 軌道穩定性 (20%)
    const scoredSatellites = newSatellites.map(sat => ({
      ...sat,
      score: (
        (sat.elevation / 90) * 0.5 +
        ((sat.signalStrength + 130) / 50) * 0.3 +
        (Math.random() * 0.2) // 模擬軌道穩定性
      )
    }))
    
    // 選擇前 6 顆最佳衛星
    scoredSatellites.sort((a, b) => b.score - a.score)
    const selected = scoredSatellites.slice(0, 6)
    selected.forEach(sat => sat.selected = true)
    
    setSatellites(scoredSatellites)
    
    const selectedIds = selected.map(sat => sat.id)
    setSelectedSatellites(selectedIds)
    onSatelliteSelectionChange?.(selectedIds)
  }, [onSatelliteSelectionChange])

  // 定期更新數據
  useEffect(() => {
    const interval = setInterval(() => {
      simulateUEMovement()
      if (Math.random() < 0.1) { // 10% 機率更新衛星選擇
        simulateSatelliteSelection()
      }
    }, 1000)
    
    // 初始化
    simulateSatelliteSelection()
    
    return () => clearInterval(interval)
  }, [simulateUEMovement, simulateSatelliteSelection])

  // 圖表數據處理
  const chartData = useMemo(() => {
    return distanceData.map((point, index) => ({
      ...point,
      time: index,
      timeLabel: new Date(point.timestamp).toLocaleTimeString()
    }))
  }, [distanceData])

  // 衛星散點圖數據
  const satelliteChartData = useMemo(() => {
    return satellites.map(sat => ({
      elevation: sat.elevation,
      signalStrength: sat.signalStrength,
      id: sat.id,
      selected: sat.selected,
      quality: sat.quality
    }))
  }, [satellites])

  // 自定義 Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border rounded-lg shadow-lg">
          <p className="font-medium">{`時間: ${data.timeLabel}`}</p>
          <p className="text-blue-600">{`距離1: ${data.distance1.toFixed(2)} km`}</p>
          <p className="text-green-600">{`距離2: ${data.distance2.toFixed(2)} km`}</p>
          <p className="text-red-500">{`門檻1: ${data.threshold1} km`}</p>
          <p className="text-orange-500">{`門檻2: ${data.threshold2} km`}</p>
          {data.triggered && <p className="text-red-600 font-bold">⚠️ 已觸發</p>}
        </div>
      )
    }
    return null
  }

  // 衛星品質顏色
  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return '#10B981'
      case 'good': return '#3B82F6'
      case 'fair': return '#F59E0B'
      case 'poor': return '#EF4444'
      default: return '#6B7280'
    }
  }

  return (
    <div className={`d1-event-specific-chart ${className}`}>
      {/* 頂部狀態卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">參考位置</span>
            </div>
            <div className="text-lg font-bold">
              {referenceLatitude.toFixed(3)}°, {referenceLongitude.toFixed(3)}°
            </div>
            <div className="text-xs text-muted-foreground">
              全球化支援
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-green-500" />
              <span className="text-sm font-medium">當前距離</span>
            </div>
            <div className="text-lg font-bold">
              {currentDistance.toFixed(2)} km
            </div>
            <div className="text-xs text-muted-foreground">
              實時計算
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Satellite className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium">選中衛星</span>
            </div>
            <div className="text-lg font-bold">
              {selectedSatellites.length} 顆
            </div>
            <div className="text-xs text-muted-foreground">
              智能選擇
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-orange-500" />
              <span className="text-sm font-medium">觸發狀態</span>
            </div>
            <div className="text-lg font-bold">
              <Badge variant={isThresholdCrossed ? 'destructive' : 'default'}>
                {isThresholdCrossed ? '已觸發' : '正常'}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground">
              雙重門檻
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 全球化支援提示 */}
      <Alert className="mb-4">
        <Globe className="h-4 w-4" />
        <AlertDescription>
          D1 事件已支援全球化：當前參考位置設定為 {referenceLatitude.toFixed(3)}°N, {referenceLongitude.toFixed(3)}°E，
          可設定任意全球地理位置作為參考點。
        </AlertDescription>
      </Alert>

      {/* 主要圖表區域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 距離變化圖表 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Navigation className="h-4 w-4" />
              雙重距離測量
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="time" 
                  tickFormatter={(value) => `${value}s`}
                />
                <YAxis 
                  label={{ value: '距離 (km)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {/* 門檻線 */}
                <ReferenceLine 
                  y={thresh1} 
                  stroke="#ef4444" 
                  strokeDasharray="5 5"
                  label="門檻1"
                />
                <ReferenceLine 
                  y={thresh2} 
                  stroke="#f97316" 
                  strokeDasharray="5 5"
                  label="門檻2"
                />
                
                {/* 距離線 */}
                <Line
                  type="monotone"
                  dataKey="distance1"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="距離1"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="distance2"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="距離2"
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 衛星選擇圖表 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Signal className="h-4 w-4" />
              智能衛星選擇
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart data={satelliteChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="elevation"
                  label={{ value: '仰角 (度)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  dataKey="signalStrength"
                  label={{ value: '信號強度 (dBm)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value, name, props) => [
                    `${value}${name === 'elevation' ? '°' : ' dBm'}`,
                    name === 'elevation' ? '仰角' : '信號強度'
                  ]}
                  labelFormatter={(label, payload) => {
                    if (payload && payload[0]) {
                      const data = payload[0].payload
                      return `${data.id} (${data.selected ? '已選中' : '未選中'})`
                    }
                    return label
                  }}
                />
                <Scatter dataKey="signalStrength">
                  {satelliteChartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.selected ? getQualityColor(entry.quality) : '#d1d5db'}
                      stroke={entry.selected ? '#000' : 'none'}
                      strokeWidth={entry.selected ? 2 : 0}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
            
            {/* 圖例 */}
            <div className="mt-4 flex flex-wrap gap-2">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="text-xs">優秀</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-xs">良好</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <span className="text-xs">一般</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span className="text-xs">較差</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-gray-300"></div>
                <span className="text-xs">未選中</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 底部統計資訊 */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm font-medium mb-2">距離統計</div>
            <div className="space-y-1 text-xs">
              <div>平均距離: {chartData.length > 0 ? (chartData.reduce((sum, d) => sum + d.distance1, 0) / chartData.length).toFixed(2) : '0.00'} km</div>
              <div>最大距離: {chartData.length > 0 ? Math.max(...chartData.map(d => d.distance1)).toFixed(2) : '0.00'} km</div>
              <div>最小距離: {chartData.length > 0 ? Math.min(...chartData.map(d => d.distance1)).toFixed(2) : '0.00'} km</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="text-sm font-medium mb-2">觸發統計</div>
            <div className="space-y-1 text-xs">
              <div>觸發次數: {chartData.filter(d => d.triggered).length}</div>
              <div>觸發率: {chartData.length > 0 ? ((chartData.filter(d => d.triggered).length / chartData.length) * 100).toFixed(1) : '0.0'}%</div>
              <div>當前狀態: {isThresholdCrossed ? '已觸發' : '正常'}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="text-sm font-medium mb-2">衛星統計</div>
            <div className="space-y-1 text-xs">
              <div>可用衛星: {satellites.length} 顆</div>
              <div>選中衛星: {selectedSatellites.length} 顆</div>
              <div>平均仰角: {satellites.length > 0 ? (satellites.reduce((sum, s) => sum + s.elevation, 0) / satellites.length).toFixed(1) : '0.0'}°</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default D1EventSpecificChart
