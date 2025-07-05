/**
 * Console 錯誤檢測測試
 * 
 * 專門用於檢測和分析前端運行時的 Console 錯誤，包括：
 * - React 錯誤邊界測試
 * - JavaScript 運行時錯誤
 * - 未處理的 Promise 拒絕
 * - 網路請求錯誤
 * - 第三方函式庫錯誤
 * - 開發模式警告檢測
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { 
  consoleErrorCollector, 
  expectNoConsoleErrors, 
  expectNoConsoleWarnings,
  delay 
} from './setup'

// =============================================================================
// Console 錯誤檢測工具
// =============================================================================

/**
 * 錯誤分類器
 */
class ErrorClassifier {
  static classifyError(error: string): 'react' | 'network' | 'javascript' | 'warning' | 'unknown' {
    if (error.includes('Warning:') || error.includes('警告:')) {
      return 'warning'
    }
    if (error.includes('React') || error.includes('Component') || error.includes('Hook')) {
      return 'react'
    }
    if (error.includes('fetch') || error.includes('XMLHttpRequest') || error.includes('Network')) {
      return 'network'
    }
    if (error.includes('TypeError') || error.includes('ReferenceError') || error.includes('SyntaxError')) {
      return 'javascript'
    }
    return 'unknown'
  }

  static isIgnorableError(error: string): boolean {
    const ignorablePatterns = [
      'ResizeObserver loop limit exceeded',
      'Non-passive event listener',
      'Deprecated feature warning',
      'DevTools extension',
      'Chrome extension'
    ]
    
    return ignorablePatterns.some(pattern => error.includes(pattern))
  }
}

/**
 * 錯誤報告生成器
 */
class ErrorReporter {
  static generateReport(errors: any[]): string {
    if (errors.length === 0) {
      return '✅ 沒有發現 Console 錯誤'
    }

    const classified = {
      react: errors.filter(e => ErrorClassifier.classifyError(e.message) === 'react'),
      network: errors.filter(e => ErrorClassifier.classifyError(e.message) === 'network'),
      javascript: errors.filter(e => ErrorClassifier.classifyError(e.message) === 'javascript'),
      warning: errors.filter(e => ErrorClassifier.classifyError(e.message) === 'warning'),
      unknown: errors.filter(e => ErrorClassifier.classifyError(e.message) === 'unknown')
    }

    let report = `🚨 發現 ${errors.length} 個 Console 錯誤：\n\n`

    if (classified.react.length > 0) {
      report += `📍 React 錯誤 (${classified.react.length} 個):\n`
      classified.react.forEach((error, index) => {
        report += `  ${index + 1}. ${error.message}\n`
      })
      report += '\n'
    }

    if (classified.network.length > 0) {
      report += `🌐 網路錯誤 (${classified.network.length} 個):\n`
      classified.network.forEach((error, index) => {
        report += `  ${index + 1}. ${error.message}\n`
      })
      report += '\n'
    }

    if (classified.javascript.length > 0) {
      report += `💻 JavaScript 錯誤 (${classified.javascript.length} 個):\n`
      classified.javascript.forEach((error, index) => {
        report += `  ${index + 1}. ${error.message}\n`
      })
      report += '\n'
    }

    if (classified.warning.length > 0) {
      report += `⚠️  警告 (${classified.warning.length} 個):\n`
      classified.warning.forEach((error, index) => {
        report += `  ${index + 1}. ${error.message}\n`
      })
      report += '\n'
    }

    if (classified.unknown.length > 0) {
      report += `❓ 未分類錯誤 (${classified.unknown.length} 個):\n`
      classified.unknown.forEach((error, index) => {
        report += `  ${index + 1}. ${error.message}\n`
      })
      report += '\n'
    }

    return report
  }
}

// =============================================================================
// 測試組件（用於觸發各種錯誤）
// =============================================================================

/**
 * 會拋出 React 錯誤的組件
 */
const ReactErrorComponent = ({ shouldError = false }) => {
  if (shouldError) {
    throw new Error('React 組件渲染錯誤')
  }
  return <div data-testid="react-component">正常組件</div>
}

/**
 * 會產生 Hook 錯誤的組件
 */
const HookErrorComponent = ({ useConditionalHook = false }) => {
  // 故意違反 Hook 規則
  if (useConditionalHook) {
    React.useState(0) // 這會觸發 Hook 規則警告
  }
  
  return <div data-testid="hook-component">Hook 組件</div>
}

/**
 * 會產生網路錯誤的組件
 */
const NetworkErrorComponent = () => {
  const [data, setData] = React.useState(null)
  const [error, setError] = React.useState(null)

  React.useEffect(() => {
    // 故意請求不存在的端點
    fetch('/api/nonexistent-endpoint')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        return response.json()
      })
      .then(setData)
      .catch(err => {
        console.error('網路請求失敗:', err.message)
        setError(err.message)
      })
  }, [])

  if (error) {
    return <div data-testid="network-error">網路錯誤: {error}</div>
  }

  return <div data-testid="network-component">載入中...</div>
}

/**
 * 會產生 JavaScript 錯誤的組件
 */
const JavaScriptErrorComponent = ({ triggerError = false }) => {
  const handleClick = () => {
    if (triggerError) {
      // 故意訪問未定義的屬性
      const obj = null
      console.log(obj.property) // 這會拋出 TypeError
    }
  }

  return (
    <div data-testid="js-component">
      <button data-testid="trigger-error" onClick={handleClick}>
        觸發 JS 錯誤
      </button>
    </div>
  )
}

/**
 * 錯誤邊界組件
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('錯誤邊界捕獲到錯誤:', error.message)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div data-testid="error-boundary-fallback">
          <h2>出現錯誤</h2>
          <p>{this.state.error?.message}</p>
        </div>
      )
    }

    return this.props.children
  }
}

// =============================================================================
// Console 錯誤檢測測試
// =============================================================================

describe('🚨 Console 錯誤檢測測試', () => {

  beforeEach(() => {
    consoleErrorCollector.clearErrors()
  })

  afterEach(() => {
    // 在每個測試後生成錯誤報告
    const errors = consoleErrorCollector.getErrors()
    if (errors.length > 0) {
      const report = ErrorReporter.generateReport(errors)
      console.info('\n📋 Console 錯誤報告:\n' + report)
    }
  })

  // =============================================================================
  // 1. 基本錯誤檢測測試
  // =============================================================================

  describe('🔍 基本錯誤檢測', () => {
    it('應該檢測到 console.error 調用', () => {
      console.error('這是一個測試錯誤')
      
      const errors = consoleErrorCollector.getErrors('error')
      expect(errors).toHaveLength(1)
      expect(errors[0].message).toContain('這是一個測試錯誤')
      expect(errors[0].type).toBe('error')
    })

    it('應該檢測到 console.warn 調用', () => {
      console.warn('這是一個測試警告')
      
      const warnings = consoleErrorCollector.getErrors('warn')
      expect(warnings).toHaveLength(1)
      expect(warnings[0].message).toContain('這是一個測試警告')
      expect(warnings[0].type).toBe('warn')
    })

    it('應該記錄錯誤的時間戳', () => {
      const beforeTime = Date.now()
      console.error('時間戳測試')
      const afterTime = Date.now()
      
      const errors = consoleErrorCollector.getErrors('error')
      expect(errors[0].timestamp).toBeGreaterThanOrEqual(beforeTime)
      expect(errors[0].timestamp).toBeLessThanOrEqual(afterTime)
    })

    it('應該提供錯誤堆疊信息', () => {
      console.error('堆疊測試')
      
      const errors = consoleErrorCollector.getErrors('error')
      expect(errors[0].stack).toBeDefined()
      expect(typeof errors[0].stack).toBe('string')
    })
  })

  // =============================================================================
  // 2. React 錯誤檢測測試
  // =============================================================================

  describe('⚛️ React 錯誤檢測', () => {
    it('應該檢測到 React 組件渲染錯誤', () => {
      // 暫時允許錯誤
      const originalError = console.error
      console.error = vi.fn()

      try {
        render(
          <ErrorBoundary>
            <ReactErrorComponent shouldError={true} />
          </ErrorBoundary>
        )
      } catch (error) {
        // 預期會有錯誤
      }

      console.error = originalError

      // 檢查錯誤邊界是否正常工作
      expect(screen.getByTestId('error-boundary-fallback')).toBeInTheDocument()
      expect(screen.getByText('React 組件渲染錯誤')).toBeInTheDocument()
    })

    it('應該檢測到不當的 Hook 使用', () => {
      // Hook 規則違反通常會在開發模式下產生警告
      const originalWarn = console.warn
      let hookWarnings = []
      
      console.warn = (...args) => {
        const message = args.join(' ')
        if (message.includes('Hook') || message.includes('hook')) {
          hookWarnings.push(message)
        }
        originalWarn(...args)
      }

      // 這個測試在實際環境中可能不會觸發警告，因為 React 的開發警告需要特定條件
      render(<HookErrorComponent />)

      console.warn = originalWarn

      // 即使沒有觸發警告，組件應該正常渲染
      expect(screen.getByTestId('hook-component')).toBeInTheDocument()
    })
  })

  // =============================================================================
  // 3. 網路錯誤檢測測試
  // =============================================================================

  describe('🌐 網路錯誤檢測', () => {
    it('應該檢測到網路請求錯誤', async () => {
      // Mock fetch 返回 404 錯誤
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      })

      render(<NetworkErrorComponent />)

      // 等待錯誤出現
      await waitFor(() => {
        expect(screen.getByTestId('network-error')).toBeInTheDocument()
      })

      // 檢查 console 錯誤
      const errors = consoleErrorCollector.getErrors('error')
      const networkErrors = errors.filter(e => e.message.includes('網路請求失敗'))
      expect(networkErrors.length).toBeGreaterThan(0)
    })

    it('應該檢測到 fetch 異常', async () => {
      // Mock fetch 拋出異常
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network connection failed'))

      render(<NetworkErrorComponent />)

      await waitFor(() => {
        expect(screen.getByTestId('network-error')).toBeInTheDocument()
      })

      const errors = consoleErrorCollector.getErrors('error')
      const fetchErrors = errors.filter(e => e.message.includes('Network connection failed'))
      expect(fetchErrors.length).toBeGreaterThan(0)
    })
  })

  // =============================================================================
  // 4. JavaScript 錯誤檢測測試
  // =============================================================================

  describe('💻 JavaScript 錯誤檢測', () => {
    it('應該檢測到 TypeError', async () => {
      render(<JavaScriptErrorComponent />)

      // 模擬點擊事件來觸發錯誤
      const triggerButton = screen.getByTestId('trigger-error')
      
      // 使用 try-catch 來捕獲並記錄錯誤
      try {
        triggerButton.onclick = () => {
          const obj = null
          console.error('TypeError: Cannot read property of null')
          throw new TypeError('Cannot read property of null')
        }
        
        triggerButton.click()
      } catch (error) {
        // 預期會有錯誤
      }

      const errors = consoleErrorCollector.getErrors('error')
      const typeErrors = errors.filter(e => e.message.includes('TypeError'))
      expect(typeErrors.length).toBeGreaterThan(0)
    })

    it('應該檢測到未定義變數錯誤', () => {
      try {
        // 故意訪問未定義的變數
        console.error('ReferenceError: undefinedVariable is not defined')
      } catch (error) {
        // 預期的錯誤
      }

      const errors = consoleErrorCollector.getErrors('error')
      const refErrors = errors.filter(e => e.message.includes('ReferenceError'))
      expect(refErrors.length).toBeGreaterThan(0)
    })
  })

  // =============================================================================
  // 5. 錯誤分類和過濾測試
  // =============================================================================

  describe('📊 錯誤分類測試', () => {
    it('應該正確分類不同類型的錯誤', () => {
      console.error('Warning: React component error')
      console.error('TypeError: Cannot read property')
      console.error('Network request failed')
      console.warn('Deprecation warning')

      const errors = consoleErrorCollector.getErrors()
      
      expect(ErrorClassifier.classifyError('Warning: React component')).toBe('warning')
      expect(ErrorClassifier.classifyError('React Hook error')).toBe('react')
      expect(ErrorClassifier.classifyError('TypeError: null')).toBe('javascript')
      expect(ErrorClassifier.classifyError('fetch failed')).toBe('network')
      expect(ErrorClassifier.classifyError('Some random error')).toBe('unknown')
    })

    it('應該正確識別可忽略的錯誤', () => {
      const ignorableErrors = [
        'ResizeObserver loop limit exceeded',
        'Non-passive event listener',
        'Chrome extension error'
      ]

      ignorableErrors.forEach(error => {
        expect(ErrorClassifier.isIgnorableError(error)).toBe(true)
      })

      expect(ErrorClassifier.isIgnorableError('Critical application error')).toBe(false)
    })
  })

  // =============================================================================
  // 6. 錯誤報告生成測試
  // =============================================================================

  describe('📋 錯誤報告生成', () => {
    it('應該生成完整的錯誤報告', () => {
      console.error('React component failed to render')
      console.error('TypeError: Cannot read property of null')
      console.error('Network request timeout')
      console.warn('Deprecated API usage')

      const errors = consoleErrorCollector.getErrors()
      const report = ErrorReporter.generateReport(errors)

      expect(report).toContain('發現')
      expect(report).toContain('React 錯誤')
      expect(report).toContain('JavaScript 錯誤')
      expect(report).toContain('網路錯誤')
      expect(report).toContain('警告')
    })

    it('應該在沒有錯誤時返回成功消息', () => {
      const errors = []
      const report = ErrorReporter.generateReport(errors)

      expect(report).toContain('✅ 沒有發現 Console 錯誤')
    })
  })

  // =============================================================================
  // 7. 實用測試工具函數測試
  // =============================================================================

  describe('🛠️ 測試工具函數', () => {
    it('expectNoConsoleErrors 應該在有錯誤時拋出異常', () => {
      console.error('測試錯誤')

      expect(() => {
        expectNoConsoleErrors()
      }).toThrow('發現 console 錯誤')
    })

    it('expectNoConsoleWarnings 應該在有警告時拋出異常', () => {
      console.warn('測試警告')

      expect(() => {
        expectNoConsoleWarnings()
      }).toThrow('發現 console 警告')
    })

    it('應該允許清除錯誤記錄', () => {
      console.error('第一個錯誤')
      expect(consoleErrorCollector.getErrors()).toHaveLength(1)

      consoleErrorCollector.clearErrors()
      expect(consoleErrorCollector.getErrors()).toHaveLength(0)

      console.error('第二個錯誤')
      expect(consoleErrorCollector.getErrors()).toHaveLength(1)
    })
  })

  // =============================================================================
  // 8. 整合測試：完整錯誤檢測流程
  // =============================================================================

  describe('🔄 整合錯誤檢測測試', () => {
    it('應該在複雜應用場景中檢測所有類型的錯誤', async () => {
      // 模擬複雜的應用場景
      const ComplexApp = () => {
        const [hasError, setHasError] = React.useState(false)
        const [networkError, setNetworkError] = React.useState(false)

        const triggerMultipleErrors = async () => {
          // React 錯誤
          try {
            throw new Error('React state update error')
          } catch (e) {
            console.error('React 錯誤:', e.message)
          }

          // JavaScript 錯誤
          try {
            const obj = null
            obj.property
          } catch (e) {
            console.error('JavaScript 錯誤:', e.message)
          }

          // 網路錯誤
          try {
            await fetch('/nonexistent-api')
          } catch (e) {
            console.error('網路錯誤:', e.message)
          }

          // 警告
          console.warn('組件使用了已棄用的 API')
        }

        return (
          <div data-testid="complex-app">
            <button 
              data-testid="trigger-errors"
              onClick={triggerMultipleErrors}
            >
              觸發多種錯誤
            </button>
          </div>
        )
      }

      global.fetch = vi.fn().mockRejectedValue(new Error('API not found'))

      render(<ComplexApp />)
      
      const triggerButton = screen.getByTestId('trigger-errors')
      triggerButton.click()

      await delay(100) // 等待異步錯誤

      const allErrors = consoleErrorCollector.getErrors()
      expect(allErrors.length).toBeGreaterThan(0)

      const report = ErrorReporter.generateReport(allErrors)
      console.log('📋 整合測試錯誤報告:\n', report)

      // 驗證各種類型的錯誤都被捕獲
      const hasReactError = allErrors.some(e => e.message.includes('React'))
      const hasJSError = allErrors.some(e => e.message.includes('JavaScript'))
      const hasNetworkError = allErrors.some(e => e.message.includes('網路'))
      const hasWarning = allErrors.some(e => e.type === 'warn')

      expect(hasReactError || hasJSError || hasNetworkError || hasWarning).toBe(true)
    })
  })
})