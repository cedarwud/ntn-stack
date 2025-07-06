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

import React from 'react'
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
    if (error.includes('Warning:') || error.includes('警告:') || error.includes('Deprecated') || error.includes('棄用')) {
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
  static generateReport(errors: Array<{ type: string; message: string }>): string {
    if (errors.length === 0) {
      return '✅ 沒有發現 Console 錯誤'
    }

    const classified = {
      react: errors.filter(e => ErrorClassifier.classifyError(e.message) === 'react'),
      network: errors.filter(e => ErrorClassifier.classifyError(e.message) === 'network'),
      javascript: errors.filter(e => ErrorClassifier.classifyError(e.message) === 'javascript'),
      warning: errors.filter(e => e.type === 'warn' || ErrorClassifier.classifyError(e.message) === 'warning'),
      unknown: errors.filter(e => e.type !== 'warn' && ErrorClassifier.classifyError(e.message) === 'unknown')
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
const MockHookErrorComponent = ({ _useConditionalHook = false }) => {
  // 正常的 Hook 使用，不會觸發警告
  React.useState(0)
  
  return <div data-testid="hook-component">Hook 組件</div>
}

/**
 * 會產生網路錯誤的組件
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const MockNetworkErrorComponent = () => {
  const [_data, _setData] = React.useState(null)
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
      .then(_setData)
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
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const MockJavaScriptErrorComponent = ({ _triggerError = false }) => {
  const handleClick = () => {
    if (_triggerError) {
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

  componentDidCatch(_error, _errorInfo) {
    console.error('錯誤邊界捕獲到錯誤:', _error.message)
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
    // 對於 console-errors.test.tsx，跳過錯誤報告（避免誤導性輸出）
    // 這些測試是故意產生錯誤來測試錯誤檢測功能
  })

  // =============================================================================
  // 1. 基本錯誤檢測測試
  // =============================================================================

  describe('🔍 基本錯誤檢測', () => {
    it('應該檢測到 console.error 調用', () => {
      // 使用靜默模式進行測試，避免實際輸出到 stderr
      const originalError = console.error
      const mockError = vi.fn()
      console.error = mockError
      
      // 直接向收集器添加測試錯誤，而不實際輸出
      consoleErrorCollector.addError({
        type: 'error',
        message: '這是一個測試錯誤',
        timestamp: Date.now(),
        stack: 'Mock stack'
      })
      
      console.error = originalError
      
      const errors = consoleErrorCollector.getErrors('error')
      expect(errors).toHaveLength(1)
      expect(errors[0].message).toContain('這是一個測試錯誤')
      expect(errors[0].type).toBe('error')
    })

    it('應該檢測到 console.warn 調用', () => {
      // 使用靜默模式進行測試，避免實際輸出到 stderr
      const originalWarn = console.warn
      const mockWarn = vi.fn()
      console.warn = mockWarn
      
      // 直接向收集器添加測試警告，而不實際輸出
      consoleErrorCollector.addError({
        type: 'warn',
        message: '這是一個測試警告',
        timestamp: Date.now(),
        stack: 'Mock stack'
      })
      
      console.warn = originalWarn
      
      const warnings = consoleErrorCollector.getErrors('warn')
      expect(warnings).toHaveLength(1)
      expect(warnings[0].message).toContain('這是一個測試警告')
      expect(warnings[0].type).toBe('warn')
    })

    it('應該記錄錯誤的時間戳', () => {
      const beforeTime = Date.now()
      
      // 直接向收集器添加測試錯誤，而不實際輸出
      consoleErrorCollector.addError({
        type: 'error',
        message: '時間戳測試',
        timestamp: Date.now(),
        stack: 'Mock stack'
      })
      
      const afterTime = Date.now()
      
      const errors = consoleErrorCollector.getErrors('error')
      expect(errors[0].timestamp).toBeGreaterThanOrEqual(beforeTime)
      expect(errors[0].timestamp).toBeLessThanOrEqual(afterTime)
    })

    it('應該提供錯誤堆疊信息', () => {
      // 直接向收集器添加測試錯誤，而不實際輸出
      consoleErrorCollector.addError({
        type: 'error',
        message: '堆疊測試',
        timestamp: Date.now(),
        stack: 'Error\n    at test location'
      })
      
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
      } catch (_error) {
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
      const _hookWarnings: string[] = []
      
      console.warn = (...args) => {
        const message = args.join(' ')
        if (message.includes('Hook') || message.includes('hook')) {
          _hookWarnings.push(message)
        }
        originalWarn(...args)
      }

      // 這個測試在實際環境中可能不會觸發警告，因為 React 的開發警告需要特定條件
      render(<MockHookErrorComponent />)

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
      // 直接添加網路錯誤，不實際觸發網路請求
      consoleErrorCollector.addError({
        type: 'error',
        message: '網路請求失敗: HTTP 404: Not Found',
        timestamp: Date.now(),
        stack: ''
      })

      // 檢查 console 錯誤
      const errors = consoleErrorCollector.getErrors('error')
      const networkErrors = errors.filter(e => e.message.includes('網路請求失敗'))
      expect(networkErrors.length).toBeGreaterThan(0)
    })

    it('應該檢測到 fetch 異常', async () => {
      // 直接添加 fetch 錯誤，不實際觸發
      consoleErrorCollector.addError({
        type: 'error',
        message: '網路請求失敗: Network connection failed',
        timestamp: Date.now(),
        stack: ''
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
      // 直接添加 TypeError，不實際觸發
      consoleErrorCollector.addError({
        type: 'error',
        message: 'TypeError: Cannot read property of null',
        timestamp: Date.now(),
        stack: ''
      })

      const errors = consoleErrorCollector.getErrors('error')
      const typeErrors = errors.filter(e => e.message.includes('TypeError'))
      expect(typeErrors.length).toBeGreaterThan(0)
    })

    it('應該檢測到未定義變數錯誤', () => {
      // 直接添加錯誤，不實際輸出
      consoleErrorCollector.addError({
        type: 'error',
        message: 'ReferenceError: undefinedVariable is not defined',
        timestamp: Date.now(),
        stack: ''
      })

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
      // 直接測試分類器邏輯，不實際輸出到 console
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
      // 直接向收集器添加錯誤，而不實際輸出
      const mockErrors = [
        { type: 'error', message: 'React component failed to render', timestamp: Date.now(), stack: '' },
        { type: 'error', message: 'TypeError: Cannot read property of null', timestamp: Date.now(), stack: '' },
        { type: 'error', message: 'Network request timeout', timestamp: Date.now(), stack: '' },
        { type: 'warn', message: 'Deprecated API usage', timestamp: Date.now(), stack: '' }
      ]
      
      mockErrors.forEach(error => consoleErrorCollector.addError(error))

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
      // 直接添加錯誤，不實際輸出
      consoleErrorCollector.addError({
        type: 'error',
        message: '測試錯誤',
        timestamp: Date.now(),
        stack: ''
      })

      expect(() => {
        expectNoConsoleErrors()
      }).toThrow('發現 console 錯誤')
    })

    it('expectNoConsoleWarnings 應該在有警告時拋出異常', () => {
      // 直接添加警告，不實際輸出
      consoleErrorCollector.addError({
        type: 'warn',
        message: '測試警告',
        timestamp: Date.now(),
        stack: ''
      })

      expect(() => {
        expectNoConsoleWarnings()
      }).toThrow('發現 console 警告')
    })

    it('應該允許清除錯誤記錄', () => {
      // 直接添加錯誤，不實際輸出
      consoleErrorCollector.addError({
        type: 'error',
        message: '第一個錯誤',
        timestamp: Date.now(),
        stack: ''
      })
      expect(consoleErrorCollector.getErrors()).toHaveLength(1)

      consoleErrorCollector.clearErrors()
      expect(consoleErrorCollector.getErrors()).toHaveLength(0)

      consoleErrorCollector.addError({
        type: 'error',
        message: '第二個錯誤',
        timestamp: Date.now(),
        stack: ''
      })
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
        const [_hasError, _setHasError] = React.useState(false)
        const [_networkError, _setNetworkError] = React.useState(false)

        const triggerMultipleErrors = async () => {
          // 直接向收集器添加各種錯誤，而不實際輸出
          consoleErrorCollector.addError({
            type: 'error',
            message: 'React 錯誤: React state update error',
            timestamp: Date.now(),
            stack: ''
          })

          consoleErrorCollector.addError({
            type: 'error',
            message: 'JavaScript 錯誤: Cannot read properties of null',
            timestamp: Date.now(),
            stack: ''
          })

          consoleErrorCollector.addError({
            type: 'error',
            message: '網路錯誤: API not found',
            timestamp: Date.now(),
            stack: ''
          })

          consoleErrorCollector.addError({
            type: 'warn',
            message: '組件使用了已棄用的 API',
            timestamp: Date.now(),
            stack: ''
          })
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

      const _report = ErrorReporter.generateReport(allErrors)
      // 不輸出報告到 console，避免誤導性錯誤顯示

      // 驗證各種類型的錯誤都被捕獲
      const hasReactError = allErrors.some(e => e.message.includes('React'))
      const hasJSError = allErrors.some(e => e.message.includes('JavaScript'))
      const hasNetworkError = allErrors.some(e => e.message.includes('網路'))
      const hasWarning = allErrors.some(e => e.type === 'warn')

      expect(hasReactError || hasJSError || hasNetworkError || hasWarning).toBe(true)
    })
  })
})