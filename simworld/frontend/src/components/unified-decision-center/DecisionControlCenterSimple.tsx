import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { netstackFetch } from '../../config/api-config'

interface DecisionControlCenterSimpleProps {
  className?: string
}

export const DecisionControlCenterSimple: React.FC<DecisionControlCenterSimpleProps> = ({ 
  className = '' 
}) => {
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'warning' | 'error'>('healthy')
  const [activeAlgorithm, setActiveAlgorithm] = useState<string>('DQN')
  const [apiResponseTime, setApiResponseTime] = useState<number>(2.3)
  const [isConnected, setIsConnected] = useState<boolean>(true)

  // 模擬系統狀態更新
  useEffect(() => {
    const interval = setInterval(() => {
      setApiResponseTime(prev => Math.max(1, prev + (Math.random() - 0.5) * 0.5))
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  // 算法切換
  const handleAlgorithmSwitch = (algorithm: string) => {
    setActiveAlgorithm(algorithm)
    // 模擬算法切換過程
    setSystemStatus('warning')
    setTimeout(() => setSystemStatus('healthy'), 2000)
  }

  // 系統健康檢查
  const performHealthCheck = async () => {
    try {
      const response = await netstackFetch('/api/v1/rl/health')
      const data = await response.json()
      
      if (data.status === 'healthy') {
        setSystemStatus('healthy')
        setIsConnected(true)
      } else {
        setSystemStatus('warning')
      }
    } catch (error) {
      setSystemStatus('error')
      setIsConnected(false)
    }
  }

  // 頁面加載時執行健康檢查
  useEffect(() => {
    performHealthCheck()
  }, [])

  return (
    <div className={`min-h-screen bg-gray-50 p-6 ${className}`}>
      <div className="max-w-7xl mx-auto">
        {/* 頁面標題 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🧠 LEO 衛星換手決策控制中心
          </h1>
          <p className="text-gray-600">
            Phase 4: 統一決策控制中心 - 實現完整的端到端決策流程整合
          </p>
        </div>

        {/* 系統狀態頂部欄 */}
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">系統狀態總覽</CardTitle>
              <div className="flex items-center gap-4">
                <Badge variant={systemStatus === 'healthy' ? 'default' : 'destructive'}>
                  {systemStatus === 'healthy' ? '✅ 系統正常' : '⚠️ 系統異常'}
                </Badge>
                <Badge variant="outline">
                  {activeAlgorithm} 算法
                </Badge>
                <Badge variant="secondary">
                  API 響應: {apiResponseTime.toFixed(1)}ms
                </Badge>
                <Badge variant={isConnected ? 'default' : 'destructive'}>
                  {isConnected ? '🔗 已連接' : '❌ 未連接'}
                </Badge>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* 系統異常提示 */}
        {systemStatus !== 'healthy' && (
          <Alert className="mb-6">
            <AlertDescription>
              {systemStatus === 'error' && '⚠️ 系統發生錯誤，正在嘗試自動修復...'}
              {systemStatus === 'warning' && '⚠️ 系統正在進行算法切換，請稍候...'}
            </AlertDescription>
          </Alert>
        )}

        {/* 主要功能區域 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 算法管理 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">🤖 算法管理</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-sm text-gray-600 mb-4">
                  當前活躍算法：<span className="font-semibold">{activeAlgorithm}</span>
                </div>
                
                <div className="space-y-2">
                  {['DQN', 'PPO', 'SAC'].map((alg) => (
                    <Button
                      key={alg}
                      variant={activeAlgorithm === alg ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handleAlgorithmSwitch(alg)}
                      className="w-full"
                    >
                      {alg === 'DQN' && '🧠 Deep Q-Network'}
                      {alg === 'PPO' && '🎯 Proximal Policy Optimization'}
                      {alg === 'SAC' && '🎭 Soft Actor-Critic'}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 性能監控 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">📊 性能監控</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>API 響應時間</span>
                    <span className="font-semibold text-green-600">
                      {apiResponseTime.toFixed(1)}ms
                    </span>
                  </div>
                  <Progress value={Math.min(apiResponseTime / 50 * 100, 100)} className="h-2" />
                  <div className="text-xs text-gray-500 mt-1">
                    目標: &lt; 50ms
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>決策成功率</span>
                    <span className="font-semibold text-green-600">94.7%</span>
                  </div>
                  <Progress value={94.7} className="h-2" />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>系統負載</span>
                    <span className="font-semibold text-blue-600">35%</span>
                  </div>
                  <Progress value={35} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 決策統計 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">📈 決策統計</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">1,234</div>
                    <div className="text-sm text-gray-600">總決策數</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">1,169</div>
                    <div className="text-sm text-gray-600">成功決策</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">2.3ms</div>
                    <div className="text-sm text-gray-600">平均延遲</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">0.87</div>
                    <div className="text-sm text-gray-600">平均置信度</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Phase 4 開發進度 */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">🚀 Phase 4 開發進度</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-lg font-semibold text-green-600">✅ 已完成</div>
                  <div className="text-sm text-gray-600">高性能 API 優化</div>
                  <div className="text-2xl font-bold mt-2">100%</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-lg font-semibold text-blue-600">🔄 進行中</div>
                  <div className="text-sm text-gray-600">端到端整合驗證</div>
                  <div className="text-2xl font-bold mt-2">60%</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-lg font-semibold text-yellow-600">⏳ 待開始</div>
                  <div className="text-sm text-gray-600">Algorithm Explainability</div>
                  <div className="text-2xl font-bold mt-2">0%</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-lg font-semibold text-gray-600">📋 計劃中</div>
                  <div className="text-sm text-gray-600">完整決策流程測試</div>
                  <div className="text-2xl font-bold mt-2">0%</div>
                </div>
              </div>
              
              <div className="mt-6">
                <div className="flex justify-between text-sm mb-2">
                  <span>Phase 4 總體進度</span>
                  <span className="font-semibold">40%</span>
                </div>
                <Progress value={40} className="h-3" />
                <div className="text-xs text-gray-500 mt-2">
                  預計完成時間：3-4 週
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 快速操作 */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">⚡ 快速操作</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <Button onClick={performHealthCheck} variant="outline" size="sm">
                🔄 系統健康檢查
              </Button>
              <Button variant="outline" size="sm">
                📊 查看詳細監控
              </Button>
              <Button variant="outline" size="sm">
                🔧 算法參數調整
              </Button>
              <Button variant="outline" size="sm">
                📈 性能分析報告
              </Button>
              <Button variant="outline" size="sm">
                🎯 決策歷史回放
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default DecisionControlCenterSimple