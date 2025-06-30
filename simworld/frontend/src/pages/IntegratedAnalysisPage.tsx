/**
 * 整合分析頁面 - 展示新舊圖表深度分析整合功能
 */

import React, { useState } from 'react'
import IntegratedAnalysisDashboard from '../components/views/dashboards/IntegratedAnalysisDashboard'
import './IntegratedAnalysisPage.scss'

interface AnalysisMode {
  id: string
  name: string
  description: string
  icon: string
}

const analysisModes: AnalysisMode[] = [
  {
    id: 'comprehensive',
    name: '綜合分析模式',
    description: '整合所有新舊圖表數據，提供全面的深度分析',
    icon: '🔬'
  },
  {
    id: 'performance',
    name: '性能專注模式',
    description: '專注於換手性能和延遲分析',
    icon: '⚡'
  },
  {
    id: 'comparison',
    name: '對比分析模式',
    description: '重點比較不同算法和方案的效果',
    icon: '📊'
  },
  {
    id: 'realtime',
    name: '即時監控模式',
    description: '實時追蹤系統性能和異常',
    icon: '📡'
  }
]

export const IntegratedAnalysisPage: React.FC = () => {
  const [selectedMode, setSelectedMode] = useState<string>('comprehensive')
  const [showDashboard, setShowDashboard] = useState(false)

  const handleModeSelect = (modeId: string) => {
    setSelectedMode(modeId)
    setShowDashboard(true)
  }

  const selectedModeConfig = analysisModes.find(mode => mode.id === selectedMode)

  if (showDashboard) {
    return (
      <div className="integrated-analysis-page">
        <div className="page-header">
          <button 
            className="back-button"
            onClick={() => setShowDashboard(false)}
          >
            ← 返回模式選擇
          </button>
          <div className="mode-info">
            <span className="mode-icon">{selectedModeConfig?.icon}</span>
            <span className="mode-name">{selectedModeConfig?.name}</span>
          </div>
        </div>
        
        <IntegratedAnalysisDashboard />
      </div>
    )
  }

  return (
    <div className="integrated-analysis-page welcome">
      <header className="welcome-header">
        <h1>🔬 整合深度分析系統</h1>
        <p className="subtitle">
          結合新舊圖表數據，使用真實API提供有意義的深度分析
        </p>
      </header>

      <section className="features-overview">
        <h2>🎯 核心功能特性</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>多維度性能對比</h3>
            <p>整合NTN標準、NTN-GS、NTN-SMN與本論文方案的全面對比分析</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">📈</div>
            <h3>24小時趨勢追蹤</h3>
            <p>即時監控換手成功率、平均延遲、網路利用率的時間趨勢</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>效能雷達分析</h3>
            <p>六維雷達圖展示延遲優化、能耗效率、可靠性等關鍵指標</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">💰</div>
            <h3>成本效益評估</h3>
            <p>全面分析部署成本、運營成本與性能收益的投資回報率</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🌐</div>
            <h3>真實數據整合</h3>
            <p>結合NetStack Core Sync API、Celestrak TLE軌道數據</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🔄</div>
            <h3>智能回退機制</h3>
            <p>API失效時自動切換到高質量模擬數據，確保分析連續性</p>
          </div>
        </div>
      </section>

      <section className="data-sources">
        <h2>📡 數據來源</h2>
        <div className="sources-grid">
          <div className="source-item">
            <div className="source-status real">🟢</div>
            <div className="source-info">
              <h4>NetStack Core Sync API</h4>
              <p>IEEE INFOCOM 2024論文實現的真實換手數據</p>
            </div>
          </div>
          
          <div className="source-item">
            <div className="source-status real">🟢</div>
            <div className="source-info">
              <h4>Celestrak TLE 軌道數據</h4>
              <p>Starlink、Kuiper衛星星座的即時軌道參數</p>
            </div>
          </div>
          
          <div className="source-item">
            <div className="source-status calculated">🟡</div>
            <div className="source-info">
              <h4>算法性能計算數據</h4>
              <p>基於真實系統狀態計算的性能衍生指標</p>
            </div>
          </div>
          
          <div className="source-item">
            <div className="source-status fallback">🟠</div>
            <div className="source-info">
              <h4>高質量回退數據</h4>
              <p>API不可用時的備用基準數據集</p>
            </div>
          </div>
        </div>
      </section>

      <section className="analysis-modes">
        <h2>🔧 分析模式選擇</h2>
        <div className="modes-grid">
          {analysisModes.map((mode) => (
            <div 
              key={mode.id}
              className={`mode-card ${selectedMode === mode.id ? 'selected' : ''}`}
              onClick={() => setSelectedMode(mode.id)}
            >
              <div className="mode-icon">{mode.icon}</div>
              <h3>{mode.name}</h3>
              <p>{mode.description}</p>
              <button 
                className="mode-button"
                onClick={(e) => {
                  e.stopPropagation()
                  handleModeSelect(mode.id)
                }}
              >
                啟動分析
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="technical-specs">
        <h2>⚙️ 技術規格</h2>
        <div className="specs-container">
          <div className="spec-group">
            <h4>圖表庫</h4>
            <ul>
              <li>Chart.js 4.5.0 - 主要圖表引擎</li>
              <li>React-Chartjs-2 5.3.0 - React整合</li>
              <li>支援Bar、Line、Radar、Doughnut圖表</li>
            </ul>
          </div>
          
          <div className="spec-group">
            <h4>數據處理</h4>
            <ul>
              <li>即時API數據獲取與處理</li>
              <li>智能錯誤處理與回退機制</li>
              <li>30秒定時數據更新</li>
            </ul>
          </div>
          
          <div className="spec-group">
            <h4>性能特性</h4>
            <ul>
              <li>響應式設計，支援桌面與移動端</li>
              <li>暗色主題優化</li>
              <li>載入狀態與錯誤處理</li>
            </ul>
          </div>
        </div>
      </section>

      <footer className="page-footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4>🎯 使用建議</h4>
            <p>
              建議先使用「綜合分析模式」獲得全面概覽，
              再根據具體需求切換到專門的分析模式。
            </p>
          </div>
          
          <div className="footer-section">
            <h4>📚 相關資源</h4>
            <ul>
              <li><a href="#ieee-paper">IEEE INFOCOM 2024 論文</a></li>
              <li><a href="#netstack-docs">NetStack 系統文檔</a></li>
              <li><a href="#api-reference">API 參考文檔</a></li>
            </ul>
          </div>
        </div>
        
        <div className="footer-bottom">
          <p>
            🚀 基於 <strong>NTN-Stack</strong> 5G衛星網路分析平台 |
            整合新舊圖表深度分析 | 使用真實API數據
          </p>
        </div>
      </footer>
    </div>
  )
}

export default IntegratedAnalysisPage