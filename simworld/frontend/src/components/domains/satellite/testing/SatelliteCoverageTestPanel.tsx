import React, { useState, useRef, useEffect } from 'react'
import { Card } from '../../../ui/card'
import { Button } from '../../../ui/button'
import { Badge } from '../../../ui/badge'
import { 
  satelliteCoverageValidator, 
  type OrbitPeriodTest, 
  type SatelliteCoverageMetrics 
} from '../../../../utils/satellite-coverage-validator'

interface SatelliteCoverageTestPanelProps {
  // 從DynamicSatelliteRenderer獲取的當前可見衛星位置
  visibleSatellitePositions?: Map<string, [number, number, number]>
  // 是否啟用測試面板
  enabled: boolean
}

const SatelliteCoverageTestPanel: React.FC<SatelliteCoverageTestPanelProps> = ({
  visibleSatellitePositions,
  enabled
}) => {
  const [isRecording, setIsRecording] = useState(false)
  const [recordCount, setRecordCount] = useState(0)
  const [testResult, setTestResult] = useState<OrbitPeriodTest | null>(null)
  const [currentMetrics, setCurrentMetrics] = useState<SatelliteCoverageMetrics | null>(null)
  const [testInProgress, setTestInProgress] = useState(false)

  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // 監聽可見衛星位置變化，自動記錄數據
  useEffect(() => {
    if (enabled && isRecording && visibleSatellitePositions) {
      satelliteCoverageValidator.recordCoverageSnapshot(visibleSatellitePositions)
      
      // 更新當前指標（模擬）
      const starlinkCount = Array.from(visibleSatellitePositions.keys())
        .filter(id => id.toLowerCase().includes('starlink') || id.includes('sat_')).length
      const onewebCount = Array.from(visibleSatellitePositions.keys())
        .filter(id => id.toLowerCase().includes('oneweb')).length

      setCurrentMetrics({
        timestamp: Date.now(),
        visibleSatellites: {
          starlink: starlinkCount,
          oneweb: onewebCount,
          total: starlinkCount + onewebCount
        },
        targetRanges: {
          starlink: [10, 15],
          oneweb: [3, 6]
        },
        compliance: {
          starlink: starlinkCount >= 10 && starlinkCount <= 15,
          oneweb: onewebCount >= 3 && onewebCount <= 6,
          overall: (starlinkCount >= 10 && starlinkCount <= 15) && (onewebCount >= 3 && onewebCount <= 6)
        },
        details: {
          starlinkSatellites: Array.from(visibleSatellitePositions.keys())
            .filter(id => id.toLowerCase().includes('starlink') || id.includes('sat_')),
          onewebSatellites: Array.from(visibleSatellitePositions.keys())
            .filter(id => id.toLowerCase().includes('oneweb'))
        }
      })
    }
  }, [enabled, isRecording, visibleSatellitePositions])

  // 更新記錄計數
  useEffect(() => {
    if (isRecording) {
      intervalRef.current = setInterval(() => {
        const status = satelliteCoverageValidator.getRecordingStatus()
        setRecordCount(status.recordCount)
      }, 1000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isRecording])

  const handleStartRecording = () => {
    satelliteCoverageValidator.startRecording()
    setIsRecording(true)
    setTestResult(null)
    setCurrentMetrics(null)
    console.log('🎬 開始記錄衛星覆蓋數據')
  }

  const handleStopRecording = () => {
    satelliteCoverageValidator.stopRecording()
    setIsRecording(false)
    console.log('⏹️ 停止記錄衛星覆蓋數據')
  }

  const handleRunFullTest = async () => {
    setTestInProgress(true)
    setTestResult(null)
    
    try {
      console.log('🧪 開始執行完整軌道週期測試...')
      
      // 執行200分鐘測試（覆蓋兩個完整的Starlink軌道週期）
      const result = await satelliteCoverageValidator.runOrbitPeriodTest(200, 30)
      
      setTestResult(result)
      
      // 生成並輸出報告
      const report = satelliteCoverageValidator.generateTestReport(result)
      console.log(report)
      
      // 可以考慮下載報告文件
      if (typeof window !== 'undefined') {
        const blob = new Blob([report], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `satellite-coverage-test-${new Date().toISOString().slice(0, 19)}.txt`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
      
    } catch (error) {
      console.error('❌ 測試執行失敗:', error)
    } finally {
      setTestInProgress(false)
    }
  }

  const handleClearData = () => {
    satelliteCoverageValidator.clearHistory()
    setRecordCount(0)
    setCurrentMetrics(null)
    setTestResult(null)
    console.log('🗑️ 清理測試數據')
  }

  const handleExportData = () => {
    const data = satelliteCoverageValidator.exportData()
    const jsonString = JSON.stringify(data, null, 2)
    
    if (typeof window !== 'undefined') {
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `satellite-coverage-data-${new Date().toISOString().slice(0, 19)}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  if (!enabled) {
    return null
  }

  return (
    <Card className="p-4 space-y-4 bg-gray-900/90 text-white border-gray-700">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          🛰️ 衛星覆蓋驗證測試
        </h3>
        <Badge variant={isRecording ? "default" : "secondary"}>
          {isRecording ? '🔴 記錄中' : '⏹️ 未記錄'}
        </Badge>
      </div>

      {/* 當前狀態顯示 */}
      {currentMetrics && (
        <div className="grid grid-cols-2 gap-4 p-3 bg-gray-800/50 rounded">
          <div>
            <div className="text-sm text-gray-300">Starlink 當前可見</div>
            <div className="text-xl font-bold flex items-center gap-2">
              {currentMetrics.visibleSatellites.starlink}
              <Badge variant={currentMetrics.compliance.starlink ? "default" : "destructive"}>
                目標: 10-15
              </Badge>
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-300">OneWeb 當前可見</div>
            <div className="text-xl font-bold flex items-center gap-2">
              {currentMetrics.visibleSatellites.oneweb}
              <Badge variant={currentMetrics.compliance.oneweb ? "default" : "destructive"}>
                目標: 3-6
              </Badge>
            </div>
          </div>
          <div className="col-span-2">
            <Badge 
              variant={currentMetrics.compliance.overall ? "default" : "destructive"}
              className="w-full justify-center"
            >
              {currentMetrics.compliance.overall ? '✅ 符合覆蓋目標' : '❌ 未達覆蓋目標'}
            </Badge>
          </div>
        </div>
      )}

      {/* 控制按鈕 */}
      <div className="flex flex-wrap gap-2">
        {!isRecording ? (
          <Button onClick={handleStartRecording} size="sm">
            🎬 開始記錄
          </Button>
        ) : (
          <Button onClick={handleStopRecording} variant="destructive" size="sm">
            ⏹️ 停止記錄
          </Button>
        )}
        
        <Button 
          onClick={handleRunFullTest} 
          disabled={testInProgress}
          size="sm"
          variant="outline"
        >
          {testInProgress ? '🔄 測試中...' : '🧪 完整軌道測試'}
        </Button>
        
        {recordCount > 0 && (
          <>
            <Button onClick={handleExportData} size="sm" variant="outline">
              💾 導出數據 ({recordCount})
            </Button>
            <Button onClick={handleClearData} size="sm" variant="outline">
              🗑️ 清理
            </Button>
          </>
        )}
      </div>

      {/* 測試結果顯示 */}
      {testResult && (
        <div className="space-y-2">
          <h4 className="font-semibold">📊 測試結果</h4>
          <div className="p-3 bg-gray-800/50 rounded text-sm space-y-1">
            <div>📅 測試時長: {((testResult.endTime - testResult.startTime) / 60000).toFixed(1)}分鐘</div>
            <div>📈 平均可見: Starlink {testResult.averageVisible.starlink}, OneWeb {testResult.averageVisible.oneweb}</div>
            <div>✅ 合規率: {testResult.complianceRate}% ({testResult.passedSamples}/{testResult.totalSamples})</div>
            <Badge 
              variant={
                testResult.complianceRate >= 95 ? "default" :
                testResult.complianceRate >= 85 ? "secondary" : "destructive"
              }
              className="w-full justify-center mt-2"
            >
              {testResult.complianceRate >= 95 ? '🌟 優秀' :
               testResult.complianceRate >= 85 ? '✅ 良好' :
               testResult.complianceRate >= 70 ? '⚠️ 需改進' : '❌ 不合格'}
            </Badge>
          </div>
        </div>
      )}

      {/* 使用說明 */}
      <div className="text-xs text-gray-400 pt-2 border-t border-gray-700">
        💡 此工具驗證3D場景中的衛星數量是否符合Stage 6動態池策略：任何時刻保持Starlink 10-15顆、OneWeb 3-6顆可見
      </div>
    </Card>
  )
}

export default SatelliteCoverageTestPanel