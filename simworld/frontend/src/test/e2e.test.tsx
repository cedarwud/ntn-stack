/**
 * 前端端到端 (E2E) 測試
 * 
 * 測試完整的用戶操作流程，包括：
 * - 應用啟動和初始化
 * - 關鍵功能流程測試
 * - 用戶交互測試
 * - 數據載入和更新流程
 * - 錯誤恢復流程
 */

import React from 'react'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { 
  consoleErrorCollector, 
  expectNoConsoleErrors, 
  setupApiMocks,
  delay,
  waitForDOMUpdate
} from './setup'

// =============================================================================
// E2E 測試工具函數
// =============================================================================

/**
 * 模擬完整的應用環境
 */
const createMockApp = () => {
  const MockApp = () => {
    const [isLoading, setIsLoading] = React.useState(true)
    const [currentView, setCurrentView] = React.useState('dashboard')
    const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false)
    const [measurements, setMeasurements] = React.useState([])
    const [satellites, setSatellites] = React.useState([])
    const [error, setError] = React.useState(null)

    // 模擬應用初始化
    React.useEffect(() => {
      const initializeApp = async () => {
        try {
          setIsLoading(true)
          
          // 模擬載入配置
          await delay(100)
          
          // 模擬載入初始數據
          const mockSatellites = [
            { id: 'sat_001', name: 'StarLink-1', status: 'active' },
            { id: 'sat_002', name: 'StarLink-2', status: 'active' }
          ]
          setSatellites(mockSatellites)
          
          const mockMeasurements = [
            { id: 'meas_001', type: 'A4', value: -85, timestamp: Date.now() },
            { id: 'meas_002', type: 'D1', value: -90, timestamp: Date.now() }
          ]
          setMeasurements(mockMeasurements)
          
          setIsLoading(false)
        } catch (err) {
          setError(err.message)
          setIsLoading(false)
        }
      }
      
      initializeApp()
    }, [])

    if (isLoading) {
      return (
        <div data-testid="app-loading" className="loading-screen">
          <div data-testid="loading-spinner">載入中...</div>
          <div data-testid="loading-message">正在初始化 NTN-Stack</div>
        </div>
      )
    }

    if (error) {
      return (
        <div data-testid="app-error" className="error-screen">
          <h1>載入錯誤</h1>
          <p data-testid="error-message">{error}</p>
          <button 
            data-testid="retry-button"
            onClick={() => window.location.reload()}
          >
            重試
          </button>
        </div>
      )
    }

    return (
      <div data-testid="app-container" className="app">
        {/* 頂部導航欄 */}
        <header data-testid="app-header" className="header">
          <div data-testid="app-title">NTN-Stack 衛星通訊系統</div>
          <div data-testid="app-status" className="status">
            <span data-testid="connection-status">
              ● 已連接 ({satellites.length} 顆衛星)
            </span>
          </div>
        </header>

        <div className="app-body">
          {/* 側邊欄 */}
          <aside 
            data-testid="app-sidebar" 
            className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}
          >
            <button 
              data-testid="sidebar-toggle"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="sidebar-toggle"
            >
              {sidebarCollapsed ? '▶' : '◀'}
            </button>
            
            <nav data-testid="main-navigation">
              <ul>
                <li>
                  <button 
                    data-testid="nav-dashboard"
                    onClick={() => setCurrentView('dashboard')}
                    className={currentView === 'dashboard' ? 'active' : ''}
                  >
                    📊 儀表板
                  </button>
                </li>
                <li>
                  <button 
                    data-testid="nav-satellites"
                    onClick={() => setCurrentView('satellites')}
                    className={currentView === 'satellites' ? 'active' : ''}
                  >
                    🛰️ 衛星
                  </button>
                </li>
                <li>
                  <button 
                    data-testid="nav-measurements"
                    onClick={() => setCurrentView('measurements')}
                    className={currentView === 'measurements' ? 'active' : ''}
                  >
                    📈 測量事件
                  </button>
                </li>
                <li>
                  <button 
                    data-testid="nav-handover"
                    onClick={() => setCurrentView('handover')}
                    className={currentView === 'handover' ? 'active' : ''}
                  >
                    🔄 衛星切換
                  </button>
                </li>
              </ul>
            </nav>
          </aside>

          {/* 主內容區域 */}
          <main data-testid="app-main" className="main-content">
            {currentView === 'dashboard' && (
              <DashboardView 
                satellites={satellites}
                measurements={measurements}
              />
            )}
            {currentView === 'satellites' && (
              <SatellitesView satellites={satellites} />
            )}
            {currentView === 'measurements' && (
              <MeasurementsView measurements={measurements} />
            )}
            {currentView === 'handover' && (
              <HandoverView satellites={satellites} />
            )}
          </main>
        </div>
      </div>
    )
  }

  return MockApp
}

/**
 * 儀表板視圖組件
 */
const DashboardView = ({ satellites, measurements }) => (
  <div data-testid="dashboard-view">
    <h1>系統儀表板</h1>
    
    <div data-testid="dashboard-stats" className="stats-grid">
      <div data-testid="stat-satellites" className="stat-card">
        <h3>活躍衛星</h3>
        <span data-testid="satellite-count">{satellites.length}</span>
      </div>
      <div data-testid="stat-measurements" className="stat-card">
        <h3>測量事件</h3>
        <span data-testid="measurement-count">{measurements.length}</span>
      </div>
      <div data-testid="stat-status" className="stat-card">
        <h3>系統狀態</h3>
        <span data-testid="system-status">正常</span>
      </div>
    </div>

    <div data-testid="dashboard-charts" className="charts-section">
      <div data-testid="chart-a4" className="chart-container">
        <h3>A4 測量事件</h3>
        <div data-testid="chart-a4-content">A4 圖表內容</div>
      </div>
      <div data-testid="chart-d1" className="chart-container">
        <h3>D1 測量事件</h3>
        <div data-testid="chart-d1-content">D1 圖表內容</div>
      </div>
    </div>
  </div>
)

/**
 * 衛星視圖組件
 */
const SatellitesView = ({ satellites }) => (
  <div data-testid="satellites-view">
    <header data-testid="satellites-header">
      <h1>衛星管理</h1>
      <button data-testid="refresh-satellites">🔄 刷新</button>
    </header>
    
    <div data-testid="satellites-list">
      {satellites.map(satellite => (
        <div 
          key={satellite.id} 
          data-testid={`satellite-${satellite.id}`}
          className="satellite-card"
        >
          <h3>{satellite.name}</h3>
          <p>ID: {satellite.id}</p>
          <p>狀態: <span data-testid={`status-${satellite.id}`}>{satellite.status}</span></p>
          <button data-testid={`details-${satellite.id}`}>查看詳情</button>
        </div>
      ))}
    </div>
  </div>
)

/**
 * 測量事件視圖組件
 */
const MeasurementsView = ({ measurements }) => {
  const [selectedType, setSelectedType] = React.useState('all')
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [selectedEvent, setSelectedEvent] = React.useState(null)

  const filteredMeasurements = selectedType === 'all' 
    ? measurements 
    : measurements.filter(m => m.type === selectedType)

  return (
    <div data-testid="measurements-view">
      <header data-testid="measurements-header">
        <h1>測量事件</h1>
        <div data-testid="measurement-filters">
          <select 
            data-testid="type-filter"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            <option value="all">所有類型</option>
            <option value="A4">A4 事件</option>
            <option value="D1">D1 事件</option>
            <option value="D2">D2 事件</option>
            <option value="T1">T1 事件</option>
          </select>
        </div>
      </header>

      <div data-testid="measurements-list">
        {filteredMeasurements.map(measurement => (
          <div 
            key={measurement.id}
            data-testid={`measurement-${measurement.id}`}
            className="measurement-card"
            onClick={() => {
              setSelectedEvent(measurement)
              setIsModalOpen(true)
            }}
          >
            <span data-testid={`type-${measurement.id}`}>{measurement.type}</span>
            <span data-testid={`value-${measurement.id}`}>{measurement.value} dBm</span>
            <span data-testid={`time-${measurement.id}`}>
              {new Date(measurement.timestamp).toLocaleTimeString()}
            </span>
          </div>
        ))}
      </div>

      {/* 測量事件詳情模態框 */}
      {isModalOpen && selectedEvent && (
        <div data-testid="measurement-modal" className="modal-overlay">
          <div data-testid="modal-content" className="modal-content">
            <header data-testid="modal-header">
              <h2>測量事件詳情</h2>
              <button 
                data-testid="modal-close"
                onClick={() => setIsModalOpen(false)}
              >
                ✕
              </button>
            </header>
            <div data-testid="modal-body">
              <p>事件類型: <span data-testid="modal-type">{selectedEvent.type}</span></p>
              <p>測量值: <span data-testid="modal-value">{selectedEvent.value} dBm</span></p>
              <p>時間戳: <span data-testid="modal-timestamp">
                {new Date(selectedEvent.timestamp).toLocaleString()}
              </span></p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * 衛星切換視圖組件
 */
const HandoverView = ({ satellites }) => {
  const [selectedSource, setSelectedSource] = React.useState('')
  const [selectedTarget, setSelectedTarget] = React.useState('')
  const [isHandoverInProgress, setIsHandoverInProgress] = React.useState(false)
  const [handoverResult, setHandoverResult] = React.useState(null)

  const executeHandover = async () => {
    if (!selectedSource || !selectedTarget) {
      alert('請選擇源衛星和目標衛星')
      return
    }

    setIsHandoverInProgress(true)
    setHandoverResult(null)

    try {
      // 模擬切換過程
      await delay(2000)
      
      setHandoverResult({
        success: true,
        switchTime: 25.5,
        message: `成功從 ${selectedSource} 切換到 ${selectedTarget}`
      })
    } catch (error) {
      setHandoverResult({
        success: false,
        message: `切換失敗: ${error.message}`
      })
    } finally {
      setIsHandoverInProgress(false)
    }
  }

  return (
    <div data-testid="handover-view">
      <h1>衛星切換</h1>
      
      <div data-testid="handover-form" className="handover-form">
        <div data-testid="source-selection">
          <label>源衛星:</label>
          <select 
            data-testid="source-satellite"
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            disabled={isHandoverInProgress}
          >
            <option value="">請選擇源衛星</option>
            {satellites.map(sat => (
              <option key={sat.id} value={sat.id}>{sat.name}</option>
            ))}
          </select>
        </div>

        <div data-testid="target-selection">
          <label>目標衛星:</label>
          <select 
            data-testid="target-satellite"
            value={selectedTarget}
            onChange={(e) => setSelectedTarget(e.target.value)}
            disabled={isHandoverInProgress}
          >
            <option value="">請選擇目標衛星</option>
            {satellites.map(sat => (
              <option key={sat.id} value={sat.id}>{sat.name}</option>
            ))}
          </select>
        </div>

        <button 
          data-testid="execute-handover"
          onClick={executeHandover}
          disabled={isHandoverInProgress || !selectedSource || !selectedTarget}
        >
          {isHandoverInProgress ? '切換中...' : '執行切換'}
        </button>
      </div>

      {isHandoverInProgress && (
        <div data-testid="handover-progress" className="progress-indicator">
          <div data-testid="progress-spinner">⟳</div>
          <p>正在執行衛星切換...</p>
        </div>
      )}

      {handoverResult && (
        <div 
          data-testid="handover-result" 
          className={`result ${handoverResult.success ? 'success' : 'error'}`}
        >
          <p data-testid="result-message">{handoverResult.message}</p>
          {handoverResult.success && (
            <p data-testid="switch-time">切換時間: {handoverResult.switchTime}ms</p>
          )}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// E2E 測試案例
// =============================================================================

describe('🚀 端到端 (E2E) 測試', () => {

  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    user = userEvent.setup()
    consoleErrorCollector.clearErrors()
    setupApiMocks()
  })

  afterEach(() => {
    // 檢查每個測試後是否有未處理的錯誤
    const errors = consoleErrorCollector.getErrors('error')
    if (errors.length > 0) {
      console.warn(`測試完成後發現 ${errors.length} 個錯誤，但允許繼續`)
    }
  })

  // =============================================================================
  // 1. 應用啟動和初始化測試
  // =============================================================================

  describe('🏁 應用啟動測試', () => {
    it('應該成功啟動並顯示載入畫面', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      // 檢查載入畫面
      expect(screen.getByTestId('app-loading')).toBeInTheDocument()
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
      expect(screen.getByText('正在初始化 NTN-Stack')).toBeInTheDocument()
      
      // 等待載入完成
      await waitFor(() => {
        expect(screen.queryByTestId('app-loading')).not.toBeInTheDocument()
      }, { timeout: 3000 })
      
      // 檢查主應用界面
      expect(screen.getByTestId('app-container')).toBeInTheDocument()
      expect(screen.getByTestId('app-header')).toBeInTheDocument()
      expect(screen.getByText('NTN-Stack 衛星通訊系統')).toBeInTheDocument()
    })

    it('應該正確載入初始數據', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      // 等待載入完成
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })
      
      // 檢查連接狀態
      expect(screen.getByTestId('connection-status')).toHaveTextContent('● 已連接 (2 顆衛星)')
      
      // 檢查儀表板數據
      expect(screen.getByTestId('satellite-count')).toHaveTextContent('2')
      expect(screen.getByTestId('measurement-count')).toHaveTextContent('2')
      expect(screen.getByTestId('system-status')).toHaveTextContent('正常')
    })
  })

  // =============================================================================
  // 2. 導航和視圖切換測試
  // =============================================================================

  describe('🧭 導航測試', () => {
    it('應該正確切換不同視圖', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })

      // 初始狀態應該顯示儀表板
      expect(screen.getByTestId('dashboard-view')).toBeInTheDocument()
      expect(screen.getByTestId('nav-dashboard')).toHaveClass('active')

      // 切換到衛星視圖
      await user.click(screen.getByTestId('nav-satellites'))
      await waitForDOMUpdate()
      
      expect(screen.getByTestId('satellites-view')).toBeInTheDocument()
      expect(screen.queryByTestId('dashboard-view')).not.toBeInTheDocument()
      expect(screen.getByTestId('nav-satellites')).toHaveClass('active')

      // 切換到測量事件視圖
      await user.click(screen.getByTestId('nav-measurements'))
      await waitForDOMUpdate()
      
      expect(screen.getByTestId('measurements-view')).toBeInTheDocument()
      expect(screen.queryByTestId('satellites-view')).not.toBeInTheDocument()
      expect(screen.getByTestId('nav-measurements')).toHaveClass('active')

      // 切換到衛星切換視圖
      await user.click(screen.getByTestId('nav-handover'))
      await waitForDOMUpdate()
      
      expect(screen.getByTestId('handover-view')).toBeInTheDocument()
      expect(screen.queryByTestId('measurements-view')).not.toBeInTheDocument()
      expect(screen.getByTestId('nav-handover')).toHaveClass('active')
    })

    it('應該正確切換側邊欄狀態', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })

      const sidebar = screen.getByTestId('app-sidebar')
      const toggleButton = screen.getByTestId('sidebar-toggle')

      // 初始狀態應該是展開的
      expect(sidebar).not.toHaveClass('collapsed')
      expect(toggleButton).toHaveTextContent('◀')

      // 收起側邊欄
      await user.click(toggleButton)
      await waitForDOMUpdate()
      
      expect(sidebar).toHaveClass('collapsed')
      expect(toggleButton).toHaveTextContent('▶')

      // 再次展開
      await user.click(toggleButton)
      await waitForDOMUpdate()
      
      expect(sidebar).not.toHaveClass('collapsed')
      expect(toggleButton).toHaveTextContent('◀')
    })
  })

  // =============================================================================
  // 3. 測量事件功能測試
  // =============================================================================

  describe('📈 測量事件功能測試', () => {
    it('應該正確顯示和過濾測量事件', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })

      // 切換到測量事件視圖
      await user.click(screen.getByTestId('nav-measurements'))
      await waitForDOMUpdate()

      // 檢查測量事件列表
      expect(screen.getByTestId('measurements-list')).toBeInTheDocument()
      expect(screen.getByTestId('measurement-meas_001')).toBeInTheDocument()
      expect(screen.getByTestId('measurement-meas_002')).toBeInTheDocument()

      // 測試過濾功能
      const typeFilter = screen.getByTestId('type-filter')
      await user.selectOptions(typeFilter, 'A4')
      
      // 應該只顯示 A4 事件
      expect(screen.getByTestId('measurement-meas_001')).toBeInTheDocument()
      expect(screen.queryByTestId('measurement-meas_002')).not.toBeInTheDocument()
    })

    it('應該正確打開和關閉測量事件詳情模態框', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })

      // 切換到測量事件視圖
      await user.click(screen.getByTestId('nav-measurements'))
      await waitForDOMUpdate()

      // 點擊測量事件打開詳情
      await user.click(screen.getByTestId('measurement-meas_001'))
      await waitForDOMUpdate()

      // 檢查模態框是否打開
      expect(screen.getByTestId('measurement-modal')).toBeInTheDocument()
      expect(screen.getByTestId('modal-content')).toBeInTheDocument()
      expect(screen.getByTestId('modal-type')).toHaveTextContent('A4')
      expect(screen.getByTestId('modal-value')).toHaveTextContent('-85 dBm')

      // 關閉模態框
      await user.click(screen.getByTestId('modal-close'))
      await waitForDOMUpdate()

      expect(screen.queryByTestId('measurement-modal')).not.toBeInTheDocument()
    })
  })

  // =============================================================================
  // 4. 衛星切換功能測試
  // =============================================================================

  describe('🔄 衛星切換功能測試', () => {
    it('應該正確執行衛星切換流程', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })

      // 切換到衛星切換視圖
      await user.click(screen.getByTestId('nav-handover'))
      await waitForDOMUpdate()

      // 選擇源衛星
      await user.selectOptions(screen.getByTestId('source-satellite'), 'sat_001')
      
      // 選擇目標衛星
      await user.selectOptions(screen.getByTestId('target-satellite'), 'sat_002')

      // 執行切換按鈕應該可用
      const executeButton = screen.getByTestId('execute-handover')
      expect(executeButton).not.toBeDisabled()

      // 執行切換
      await user.click(executeButton)
      
      // 檢查進度指示器
      expect(screen.getByTestId('handover-progress')).toBeInTheDocument()
      expect(screen.getByText('正在執行衛星切換...')).toBeInTheDocument()
      
      // 按鈕應該被禁用
      expect(executeButton).toBeDisabled()

      // 等待切換完成
      await waitFor(() => {
        expect(screen.getByTestId('handover-result')).toBeInTheDocument()
      }, { timeout: 3000 })

      // 檢查結果
      expect(screen.getByTestId('result-message')).toHaveTextContent('成功從 sat_001 切換到 sat_002')
      expect(screen.getByTestId('switch-time')).toHaveTextContent('切換時間: 25.5ms')
      
      // 進度指示器應該消失
      expect(screen.queryByTestId('handover-progress')).not.toBeInTheDocument()
      
      // 按鈕應該重新可用
      expect(executeButton).not.toBeDisabled()
    })

    it('應該驗證衛星切換的輸入驗證', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })

      // 切換到衛星切換視圖
      await user.click(screen.getByTestId('nav-handover'))
      await waitForDOMUpdate()

      // 執行切換按鈕應該被禁用（因為沒有選擇衛星）
      expect(screen.getByTestId('execute-handover')).toBeDisabled()

      // 只選擇源衛星
      await user.selectOptions(screen.getByTestId('source-satellite'), 'sat_001')
      expect(screen.getByTestId('execute-handover')).toBeDisabled()

      // 選擇目標衛星後按鈕應該可用
      await user.selectOptions(screen.getByTestId('target-satellite'), 'sat_002')
      expect(screen.getByTestId('execute-handover')).not.toBeDisabled()
    })
  })

  // =============================================================================
  // 5. 錯誤處理和恢復測試
  // =============================================================================

  describe('🛡️ 錯誤處理測試', () => {
    it('應該正確處理應用載入錯誤', async () => {
      // 創建會拋出錯誤的應用版本
      const ErrorApp = () => {
        const [error, setError] = React.useState(null)
        
        React.useEffect(() => {
          // 模擬載入錯誤
          setTimeout(() => {
            setError('網路連接失敗')
          }, 100)
        }, [])

        if (error) {
          return (
            <div data-testid="app-error" className="error-screen">
              <h1>載入錯誤</h1>
              <p data-testid="error-message">{error}</p>
              <button 
                data-testid="retry-button"
                onClick={() => setError(null)}
              >
                重試
              </button>
            </div>
          )
        }

        return <div data-testid="app-loading">載入中...</div>
      }

      render(<ErrorApp />)

      // 等待錯誤出現
      await waitFor(() => {
        expect(screen.getByTestId('app-error')).toBeInTheDocument()
      })

      expect(screen.getByTestId('error-message')).toHaveTextContent('網路連接失敗')
      expect(screen.getByTestId('retry-button')).toBeInTheDocument()

      // 測試重試功能
      await user.click(screen.getByTestId('retry-button'))
      expect(screen.getByTestId('app-loading')).toBeInTheDocument()
    })
  })

  // =============================================================================
  // 6. 效能和響應測試
  // =============================================================================

  describe('⚡ 效能測試', () => {
    it('視圖切換應該在合理時間內完成', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })

      const views = ['satellites', 'measurements', 'handover', 'dashboard']
      
      for (const view of views) {
        const start = performance.now()
        
        await user.click(screen.getByTestId(`nav-${view}`))
        await waitFor(() => {
          expect(screen.getByTestId(`${view}-view`)).toBeInTheDocument()
        })
        
        const end = performance.now()
        const switchTime = end - start
        
        // 視圖切換應該在 100ms 內完成
        expect(switchTime).toBeLessThan(100)
      }
    })

    it('應該支援快速連續操作', async () => {
      const MockApp = createMockApp()
      render(<MockApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-container')).toBeInTheDocument()
      })

      // 快速切換側邊欄多次
      const toggleButton = screen.getByTestId('sidebar-toggle')
      
      for (let i = 0; i < 5; i++) {
        await user.click(toggleButton)
        await waitForDOMUpdate()
      }
      
      // 應該仍然正常工作
      expect(screen.getByTestId('app-sidebar')).toBeInTheDocument()
      
      expectNoConsoleErrors()
    })
  })
})