import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Satellite, 
  Signal, 
  Activity, 
  Gauge, 
  MapPin,
  Trophy,
  TrendingUp,
  AlertTriangle
} from 'lucide-react'

interface CandidateInfo {
  id: string
  name: string
  position: [number, number, number]
  score: number
  signalStrength: number
  load: number
  elevation: number
  distance: number
  rank: number
  status: 'available' | 'busy' | 'maintenance' | 'unreachable'
  lastUpdate: number
}

interface CandidateSelectionPanelProps {
  candidates: CandidateInfo[]
  onCandidateUpdate: (candidates: CandidateInfo[]) => void
}

// 模擬候選衛星數據
const MOCK_CANDIDATES: CandidateInfo[] = [
  {
    id: 'sat_001',
    name: 'Starlink-1234',
    position: [100, 200, 300],
    score: 0.92,
    signalStrength: 0.85,
    load: 0.35,
    elevation: 45,
    distance: 1200,
    rank: 1,
    status: 'available',
    lastUpdate: Date.now()
  },
  {
    id: 'sat_002',
    name: 'Starlink-1235',
    position: [150, 180, 280],
    score: 0.88,
    signalStrength: 0.79,
    load: 0.52,
    elevation: 38,
    distance: 1350,
    rank: 2,
    status: 'available',
    lastUpdate: Date.now()
  },
  {
    id: 'sat_003',
    name: 'Starlink-1236',
    position: [80, 220, 320],
    score: 0.84,
    signalStrength: 0.82,
    load: 0.28,
    elevation: 52,
    distance: 1150,
    rank: 3,
    status: 'available',
    lastUpdate: Date.now()
  },
  {
    id: 'sat_004',
    name: 'Starlink-1237',
    position: [120, 160, 290],
    score: 0.76,
    signalStrength: 0.71,
    load: 0.68,
    elevation: 31,
    distance: 1480,
    rank: 4,
    status: 'busy',
    lastUpdate: Date.now()
  }
]

export const CandidateSelectionPanel: React.FC<CandidateSelectionPanelProps> = ({
  candidates: propCandidates,
  onCandidateUpdate
}) => {
  const [candidates, setCandidates] = useState<CandidateInfo[]>(
    propCandidates.length > 0 ? propCandidates : MOCK_CANDIDATES
  )
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'score' | 'signal' | 'load' | 'distance'>('score')
  const [showDetails, setShowDetails] = useState(false)

  // 更新候選數據
  useEffect(() => {
    if (propCandidates.length > 0) {
      setCandidates(propCandidates)
    }
  }, [propCandidates])

  // 排序候選衛星
  const sortedCandidates = useMemo(() => {
    return [...candidates].sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return b.score - a.score
        case 'signal':
          return b.signalStrength - a.signalStrength
        case 'load':
          return a.load - b.load // 負載越低越好
        case 'distance':
          return a.distance - b.distance // 距離越近越好
        default:
          return b.score - a.score
      }
    })
  }, [candidates, sortBy])

  // 獲取狀態顏色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'bg-green-500'
      case 'busy':
        return 'bg-yellow-500'
      case 'maintenance':
        return 'bg-orange-500'
      case 'unreachable':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  // 獲取狀態文字
  const getStatusText = (status: string) => {
    switch (status) {
      case 'available':
        return '可用'
      case 'busy':
        return '繁忙'
      case 'maintenance':
        return '維護中'
      case 'unreachable':
        return '不可達'
      default:
        return '未知'
    }
  }

  // 獲取評分等級
  const getScoreGrade = (score: number) => {
    if (score >= 0.9) return { grade: 'A+', color: 'text-green-600' }
    if (score >= 0.8) return { grade: 'A', color: 'text-green-500' }
    if (score >= 0.7) return { grade: 'B+', color: 'text-blue-500' }
    if (score >= 0.6) return { grade: 'B', color: 'text-blue-400' }
    if (score >= 0.5) return { grade: 'C', color: 'text-yellow-500' }
    return { grade: 'D', color: 'text-red-500' }
  }

  // 選擇候選衛星
  const selectCandidate = (candidateId: string) => {
    setSelectedCandidate(candidateId)
    const candidate = candidates.find(c => c.id === candidateId)
    if (candidate) {
      onCandidateUpdate([candidate])
    }
  }

  // 刷新候選數據
  const refreshCandidates = () => {
    const updatedCandidates = candidates.map(candidate => ({
      ...candidate,
      score: Math.max(0.1, Math.min(1, candidate.score + (Math.random() - 0.5) * 0.1)),
      signalStrength: Math.max(0.1, Math.min(1, candidate.signalStrength + (Math.random() - 0.5) * 0.1)),
      load: Math.max(0, Math.min(1, candidate.load + (Math.random() - 0.5) * 0.1)),
      lastUpdate: Date.now()
    }))
    setCandidates(updatedCandidates)
    onCandidateUpdate(updatedCandidates)
  }

  // 統計信息
  const statistics = useMemo(() => {
    const available = candidates.filter(c => c.status === 'available').length
    const avgScore = candidates.reduce((sum, c) => sum + c.score, 0) / candidates.length
    const bestCandidate = candidates.reduce((best, current) => 
      current.score > best.score ? current : best
    )
    
    return {
      total: candidates.length,
      available,
      avgScore,
      bestCandidate
    }
  }, [candidates])

  return (
    <div className="candidate-selection-panel space-y-4">
      {/* 統計摘要 */}
      <Card className="bg-blue-50">
        <CardContent className="p-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-blue-600">總候選數</div>
              <div className="text-2xl font-bold">{statistics.total}</div>
            </div>
            <div>
              <div className="text-green-600">可用候選</div>
              <div className="text-2xl font-bold">{statistics.available}</div>
            </div>
            <div>
              <div className="text-purple-600">平均評分</div>
              <div className="text-2xl font-bold">{statistics.avgScore.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-orange-600">最佳候選</div>
              <div className="text-sm font-semibold">{statistics.bestCandidate.name}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 排序控制 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">排序方式:</span>
          <Button
            variant={sortBy === 'score' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('score')}
          >
            評分
          </Button>
          <Button
            variant={sortBy === 'signal' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('signal')}
          >
            信號
          </Button>
          <Button
            variant={sortBy === 'load' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('load')}
          >
            負載
          </Button>
          <Button
            variant={sortBy === 'distance' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('distance')}
          >
            距離
          </Button>
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={refreshCandidates}
        >
          <TrendingUp className="w-4 h-4 mr-1" />
          刷新
        </Button>
      </div>

      {/* 候選列表 */}
      <div className="space-y-3">
        {sortedCandidates.map((candidate, index) => {
          const scoreGrade = getScoreGrade(candidate.score)
          const isSelected = selectedCandidate === candidate.id
          const isTop3 = index < 3
          
          return (
            <Card 
              key={candidate.id}
              className={`cursor-pointer transition-all duration-200 ${
                isSelected ? 'ring-2 ring-blue-500 shadow-md' : 'hover:shadow-sm'
              } ${isTop3 ? 'border-l-4 border-l-green-500' : ''}`}
              onClick={() => selectCandidate(candidate.id)}
            >
              <CardContent className="p-3">
                <div className="flex items-start justify-between">
                  {/* 基本信息 */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Satellite className="w-4 h-4 text-blue-500" />
                      <span className="font-medium text-sm">{candidate.name}</span>
                      
                      {/* 排名徽章 */}
                      {isTop3 && (
                        <Badge variant="secondary" className="text-xs">
                          <Trophy className="w-3 h-3 mr-1" />
                          #{index + 1}
                        </Badge>
                      )}
                      
                      {/* 狀態徽章 */}
                      <Badge 
                        variant="outline" 
                        className="text-xs"
                      >
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(candidate.status)} mr-1`} />
                        {getStatusText(candidate.status)}
                      </Badge>
                    </div>

                    {/* 評分 */}
                    <div className="mb-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-600">綜合評分</span>
                        <span className={`text-sm font-bold ${scoreGrade.color}`}>
                          {scoreGrade.grade} ({(candidate.score * 100).toFixed(1)}%)
                        </span>
                      </div>
                      <Progress value={candidate.score * 100} className="h-2" />
                    </div>

                    {/* 詳細指標 */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex items-center gap-1">
                        <Signal className="w-3 h-3 text-green-500" />
                        <span>信號: {(candidate.signalStrength * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Activity className="w-3 h-3 text-blue-500" />
                        <span>負載: {(candidate.load * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Gauge className="w-3 h-3 text-purple-500" />
                        <span>仰角: {candidate.elevation}°</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-orange-500" />
                        <span>距離: {candidate.distance}km</span>
                      </div>
                    </div>

                    {/* 警告信息 */}
                    {(candidate.status !== 'available' || candidate.signalStrength < 0.6) && (
                      <div className="mt-2 flex items-center gap-1 text-xs text-yellow-600">
                        <AlertTriangle className="w-3 h-3" />
                        {candidate.status !== 'available' 
                          ? `衛星狀態: ${getStatusText(candidate.status)}`
                          : '信號強度較低'
                        }
                      </div>
                    )}
                  </div>

                  {/* 選擇按鈕 */}
                  <div className="flex-shrink-0 ml-3">
                    <Button 
                      variant={isSelected ? 'default' : 'outline'}
                      size="sm"
                      disabled={candidate.status !== 'available'}
                    >
                      {isSelected ? '已選擇' : '選擇'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 選擇摘要 */}
      {selectedCandidate && (
        <Card className="bg-green-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">已選擇候選衛星</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {(() => {
              const selected = candidates.find(c => c.id === selectedCandidate)
              if (!selected) return null
              
              return (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{selected.name}</span>
                    <span className="text-sm text-green-600">
                      評分: {(selected.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    信號強度: {(selected.signalStrength * 100).toFixed(0)}% | 
                    負載: {(selected.load * 100).toFixed(0)}% | 
                    距離: {selected.distance}km
                  </div>
                </div>
              )
            })()}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default CandidateSelectionPanel