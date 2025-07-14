import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { 
  CheckCircle, 
  Circle, 
  Clock, 
  AlertCircle, 
  Play, 
  Pause, 
  SkipForward,
  RotateCcw
} from 'lucide-react'

interface DecisionPhase {
  id: string
  name: string
  description: string
  duration: number
  status: 'pending' | 'active' | 'completed' | 'skipped'
  icon?: string
  color?: string
}

interface DecisionFlowTrackerProps {
  currentPhase: string
  progress: number
  onPhaseChange: (phase: string, progress: number) => void
}

const DEFAULT_PHASES: DecisionPhase[] = [
  {
    id: 'monitoring',
    name: '監控階段',
    description: '監控當前連接狀態和信號品質',
    duration: 1000,
    status: 'active',
    icon: '👁️',
    color: 'bg-blue-500'
  },
  {
    id: 'trigger_detection',
    name: '觸發檢測',
    description: '檢測到換手觸發條件（信號劣化、負載等）',
    duration: 500,
    status: 'pending',
    icon: '⚡',
    color: 'bg-yellow-500'
  },
  {
    id: 'candidate_selection',
    name: '候選篩選',
    description: '識別並評分候選衛星',
    duration: 800,
    status: 'pending',
    icon: '🛰️',
    color: 'bg-green-500'
  },
  {
    id: 'rl_decision',
    name: 'RL 決策',
    description: '強化學習算法進行決策分析',
    duration: 200,
    status: 'pending',
    icon: '🧠',
    color: 'bg-purple-500'
  },
  {
    id: 'handover_preparation',
    name: '換手準備',
    description: '準備換手執行所需的資源',
    duration: 600,
    status: 'pending',
    icon: '⚙️',
    color: 'bg-orange-500'
  },
  {
    id: 'handover_execution',
    name: '換手執行',
    description: '執行換手操作並切換連接',
    duration: 1200,
    status: 'pending',
    icon: '🔄',
    color: 'bg-red-500'
  },
  {
    id: 'monitoring_resume',
    name: '監控恢復',
    description: '恢復正常監控狀態',
    duration: 400,
    status: 'pending',
    icon: '✅',
    color: 'bg-green-600'
  }
]

export const DecisionFlowTracker: React.FC<DecisionFlowTrackerProps> = ({
  currentPhase,
  progress,
  onPhaseChange
}) => {
  const [phases, setPhases] = useState<DecisionPhase[]>(DEFAULT_PHASES)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0)
  const [phaseProgress, setPhaseProgress] = useState(0)

  // 更新階段狀態
  useEffect(() => {
    const phaseIndex = phases.findIndex(p => p.id === currentPhase)
    if (phaseIndex !== -1) {
      setCurrentPhaseIndex(phaseIndex)
      setPhaseProgress(progress)
      
      // 更新階段狀態
      setPhases(prev => prev.map((phase, index) => ({
        ...phase,
        status: index < phaseIndex ? 'completed' : 
               index === phaseIndex ? 'active' : 'pending'
      })))
    }
  }, [currentPhase, progress, phases])

  // 階段圖標渲染
  const getPhaseIcon = (phase: DecisionPhase) => {
    switch (phase.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'active':
        return <Clock className="w-5 h-5 text-blue-500 animate-pulse" />
      case 'pending':
        return <Circle className="w-5 h-5 text-gray-400" />
      case 'skipped':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
      default:
        return <Circle className="w-5 h-5 text-gray-400" />
    }
  }

  // 階段狀態顏色
  const getPhaseStatusColor = (phase: DecisionPhase) => {
    switch (phase.status) {
      case 'completed':
        return 'text-green-600 bg-green-50'
      case 'active':
        return 'text-blue-600 bg-blue-50'
      case 'pending':
        return 'text-gray-600 bg-gray-50'
      case 'skipped':
        return 'text-yellow-600 bg-yellow-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  // 開始新的決策流程
  const startNewFlow = useCallback(() => {
    setPhases(prev => prev.map((phase, index) => ({
      ...phase,
      status: index === 0 ? 'active' : 'pending'
    })))
    setCurrentPhaseIndex(0)
    setPhaseProgress(0)
    setIsPlaying(true)
    onPhaseChange('monitoring', 0)
  }, [onPhaseChange])

  // 跳到下一階段
  const goToNextPhase = useCallback(() => {
    if (currentPhaseIndex < phases.length - 1) {
      const nextPhase = phases[currentPhaseIndex + 1]
      onPhaseChange(nextPhase.id, 0)
    }
  }, [currentPhaseIndex, phases, onPhaseChange])

  // 重置流程
  const resetFlow = useCallback(() => {
    setPhases(DEFAULT_PHASES)
    setCurrentPhaseIndex(0)
    setPhaseProgress(0)
    setIsPlaying(false)
    onPhaseChange('monitoring', 0)
  }, [onPhaseChange])

  // 計算總進度
  const totalProgress = ((currentPhaseIndex + (phaseProgress / 100)) / phases.length) * 100

  return (
    <div className="decision-flow-tracker space-y-4">
      {/* 控制按鈕 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={startNewFlow}
            disabled={isPlaying}
          >
            <Play className="w-4 h-4 mr-1" />
            開始流程
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={goToNextPhase}
            disabled={currentPhaseIndex >= phases.length - 1}
          >
            <SkipForward className="w-4 h-4 mr-1" />
            下一階段
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={resetFlow}
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            重置
          </Button>
        </div>

        <Badge variant="outline">
          {currentPhaseIndex + 1} / {phases.length}
        </Badge>
      </div>

      {/* 總進度條 */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-600">
          <span>整體進度</span>
          <span>{Math.round(totalProgress)}%</span>
        </div>
        <Progress value={totalProgress} className="h-2" />
      </div>

      {/* 階段列表 */}
      <div className="space-y-3">
        {phases.map((phase, index) => (
          <Card 
            key={phase.id}
            className={`transition-all duration-300 ${
              phase.status === 'active' ? 'ring-2 ring-blue-500 shadow-md' : ''
            }`}
          >
            <CardContent className="p-3">
              <div className="flex items-start gap-3">
                {/* 階段圖標 */}
                <div className="flex-shrink-0 mt-1">
                  {getPhaseIcon(phase)}
                </div>

                {/* 階段內容 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-sm">{phase.name}</h4>
                    <Badge 
                      variant="secondary" 
                      className={`text-xs ${getPhaseStatusColor(phase)}`}
                    >
                      {phase.status === 'completed' && '已完成'}
                      {phase.status === 'active' && '進行中'}
                      {phase.status === 'pending' && '等待中'}
                      {phase.status === 'skipped' && '已跳過'}
                    </Badge>
                  </div>

                  <p className="text-xs text-gray-600 mb-2">
                    {phase.description}
                  </p>

                  {/* 階段進度條 */}
                  {phase.status === 'active' && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>階段進度</span>
                        <span>{Math.round(phaseProgress)}%</span>
                      </div>
                      <Progress value={phaseProgress} className="h-1" />
                    </div>
                  )}

                  {/* 階段時間信息 */}
                  <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                    <span>預計時間: {phase.duration}ms</span>
                    {phase.status === 'active' && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        執行中...
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 統計信息 */}
      <Card className="bg-gray-50">
        <CardContent className="p-3">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-600">已完成階段</div>
              <div className="font-semibold">
                {phases.filter(p => p.status === 'completed').length}
              </div>
            </div>
            <div>
              <div className="text-gray-600">當前階段</div>
              <div className="font-semibold">
                {phases[currentPhaseIndex]?.name || '未開始'}
              </div>
            </div>
            <div>
              <div className="text-gray-600">預計總時間</div>
              <div className="font-semibold">
                {phases.reduce((sum, p) => sum + p.duration, 0)}ms
              </div>
            </div>
            <div>
              <div className="text-gray-600">剩餘時間</div>
              <div className="font-semibold">
                {phases.slice(currentPhaseIndex + 1).reduce((sum, p) => sum + p.duration, 0)}ms
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default DecisionFlowTracker