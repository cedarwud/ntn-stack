/**
 * 性能監控面板
 * 顯示實時性能指標和優化建議
 */
import React, { useState, useEffect, useRef } from 'react'
import { performanceOptimizer } from '../../utils/performance-optimizer'
import { bundleAnalyzer } from '../../utils/bundle-optimizer'

interface PerformanceDashboardProps {
  isVisible?: boolean
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
  autoHide?: boolean
}

const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  isVisible = false,
  position = 'bottom-right'
}) => {
  const [isOpen, setIsOpen] = useState(isVisible)
  const [activeTab, setActiveTab] = useState<'components' | 'api' | 'bundle'>('components')
  const [performanceReport, setPerformanceReport] = useState<any>(null)
  const [bundleAnalysis, setBundleAnalysis] = useState<any>(null)
  const intervalRef = useRef<NodeJS.Timeout | undefined>(undefined)

  // 更新性能數據
  const updatePerformanceData = () => {
    const report = performanceOptimizer.getPerformanceReport()
    const analysis = bundleAnalyzer.analyzeCurrentPage()
    
    setPerformanceReport(report)
    setBundleAnalysis(analysis)
  }

  // 設置定期更新
  useEffect(() => {
    if (isOpen) {
      updatePerformanceData()
      intervalRef.current = setInterval(updatePerformanceData, 5000) // 每5秒更新
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isOpen])

  // 鍵盤快捷鍵
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'P') {
        setIsOpen(!isOpen)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed ${getPositionClasses(position)} z-50 bg-blue-600 text-white p-2 rounded-full shadow-lg hover:bg-blue-700 transition-colors`}
        title="性能監控 (Ctrl+Shift+P)"
      >
        📊
      </button>
    )
  }

  return (
    <div className={`fixed ${getPositionClasses(position)} z-50 bg-white shadow-xl rounded-lg border max-w-md w-96 max-h-96 overflow-hidden`}>
      {/* 標題欄 */}
      <div className="flex items-center justify-between p-3 bg-gray-100 border-b">
        <h3 className="font-bold text-sm">性能監控</h3>
        <div className="flex gap-1">
          <button
            onClick={updatePerformanceData}
            className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
            title="刷新數據"
          >
            🔄
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600"
          >
            ✕
          </button>
        </div>
      </div>

      {/* 標籤頁 */}
      <div className="flex border-b">
        {[
          { key: 'components', label: '組件' },
          { key: 'api', label: 'API' },
          { key: 'bundle', label: 'Bundle' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex-1 px-3 py-2 text-xs ${
              activeTab === tab.key 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-50 hover:bg-gray-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 內容區域 */}
      <div className="p-3 overflow-y-auto max-h-80">
        {activeTab === 'components' && (
          <ComponentsTab report={performanceReport} />
        )}
        
        {activeTab === 'api' && (
          <APITab report={performanceReport} />
        )}
        
        {activeTab === 'bundle' && (
          <BundleTab analysis={bundleAnalysis} />
        )}
      </div>

      {/* 性能摘要 */}
      {performanceReport?.summary && (
        <div className="p-2 bg-gray-50 border-t text-xs">
          <div className="grid grid-cols-2 gap-2">
            <div>平均渲染: {performanceReport.summary.avgRenderTime}ms</div>
            <div>平均API: {performanceReport.summary.avgAPITime}ms</div>
            <div>重渲染: {performanceReport.summary.totalRerenders}</div>
            <div>錯誤率: {performanceReport.summary.apiErrorRate}%</div>
          </div>
        </div>
      )}
    </div>
  )
}

// 組件性能標籤頁
const ComponentsTab: React.FC<{ report: any }> = ({ report }) => {
  if (!report) return <div className="text-xs text-gray-500">載入中...</div>

  return (
    <div className="space-y-2">
      <h4 className="font-bold text-xs">慢組件 (&gt;16ms)</h4>
      {report.slowComponents?.length > 0 ? (
        <div className="space-y-1">
          {report.slowComponents.slice(0, 5).map((component: any, index: number) => (
            <div key={index} className="text-xs p-2 bg-red-50 rounded">
              <div className="font-medium">{component.componentName}</div>
              <div className="text-gray-600">
                {component.renderTime.toFixed(1)}ms (重渲染: {component.rerenderCount})
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-green-600">✅ 所有組件性能良好</div>
      )}

      <h4 className="font-bold text-xs mt-3">高重渲染組件 (&gt;10次)</h4>
      {report.highRerenderComponents?.length > 0 ? (
        <div className="space-y-1">
          {report.highRerenderComponents.slice(0, 3).map((component: any, index: number) => (
            <div key={index} className="text-xs p-2 bg-yellow-50 rounded">
              <div className="font-medium">{component.componentName}</div>
              <div className="text-gray-600">重渲染: {component.rerenderCount}次</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-green-600">✅ 重渲染次數正常</div>
      )}
    </div>
  )
}

// API 性能標籤頁
const APITab: React.FC<{ report: any }> = ({ report }) => {
  if (!report) return <div className="text-xs text-gray-500">載入中...</div>

  return (
    <div className="space-y-2">
      <h4 className="font-bold text-xs">慢API (&gt;500ms)</h4>
      {report.slowAPIs?.length > 0 ? (
        <div className="space-y-1">
          {report.slowAPIs.slice(0, 5).map((api: any, index: number) => (
            <div key={index} className="text-xs p-2 bg-red-50 rounded">
              <div className="font-medium truncate">{api.endpoint}</div>
              <div className="text-gray-600">
                {api.responseTime.toFixed(0)}ms (調用: {api.callCount}, 錯誤: {api.errorCount})
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-green-600">✅ 所有API響應良好</div>
      )}

      <div className="mt-3 text-xs">
        <div>總API數: {report.totalAPIs}</div>
      </div>
    </div>
  )
}

// Bundle 分析標籤頁
const BundleTab: React.FC<{ analysis: any }> = ({ analysis }) => {
  const [suggestions, setSuggestions] = useState<string[]>([])

  useEffect(() => {
    const optimizationSuggestions = bundleAnalyzer.getOptimizationSuggestions()
    setSuggestions(optimizationSuggestions)
  }, [])

  if (!analysis) return <div className="text-xs text-gray-500">載入中...</div>

  return (
    <div className="space-y-2">
      <h4 className="font-bold text-xs">Bundle 分析</h4>
      <div className="text-xs space-y-1">
        <div>模塊數量: {analysis.totalModules}</div>
        <div>估算大小: {analysis.estimatedSize}KB</div>
      </div>

      <h4 className="font-bold text-xs mt-3">優化建議</h4>
      {suggestions.length > 0 ? (
        <div className="space-y-1">
          {suggestions.map((suggestion, index) => (
            <div key={index} className="text-xs p-2 bg-blue-50 rounded">
              💡 {suggestion}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-green-600">✅ Bundle 配置良好</div>
      )}

      <h4 className="font-bold text-xs mt-3">已載入模塊</h4>
      <div className="max-h-24 overflow-y-auto">
        {analysis.modules?.slice(0, 5).map((module: string, index: number) => (
          <div key={index} className="text-xs text-gray-600 truncate">
            {module.split('/').pop()}
          </div>
        ))}
      </div>
    </div>
  )
}

// 計算位置類名
function getPositionClasses(position: string): string {
  switch (position) {
    case 'top-left': return 'top-4 left-4'
    case 'top-right': return 'top-4 right-4'
    case 'bottom-left': return 'bottom-4 left-4'
    case 'bottom-right': return 'bottom-4 right-4'
    default: return 'bottom-4 right-4'
  }
}

export default PerformanceDashboard