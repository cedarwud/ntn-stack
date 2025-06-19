/**
 * 系統健康診斷工具
 * 提供詳細的診斷信息和修復建議
 */

export interface DiagnosticResult {
  service: string
  status: 'healthy' | 'warning' | 'error'
  message: string
  details?: any
  fixSuggestions?: string[]
}

export interface SystemDiagnostics {
  overall_health: 'healthy' | 'degraded' | 'critical'
  diagnostics: DiagnosticResult[]
  summary: {
    healthy_count: number
    warning_count: number
    error_count: number
    total_checks: number
  }
}

class HealthDiagnosticsService {
  
  /**
   * 執行完整系統診斷
   */
  async runDiagnostics(): Promise<SystemDiagnostics> {
    const diagnostics: DiagnosticResult[] = []
    
    // 檢查 NetStack API
    diagnostics.push(await this.checkNetStackAPI())
    
    // 檢查 SimWorld 後端
    diagnostics.push(await this.checkSimWorldBackend())
    
    // 檢查前端服務
    diagnostics.push(await this.checkFrontendService())
    
    // 檢查數據庫連接
    diagnostics.push(await this.checkDatabaseConnection())
    
    // 檢查核心同步服務
    diagnostics.push(await this.checkCoreSyncService())
    
    return this.analyzeDiagnostics(diagnostics)
  }
  
  /**
   * 檢查 NetStack API
   */
  private async checkNetStackAPI(): Promise<DiagnosticResult> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const response = await fetch('http://localhost:8080/health', {
        method: 'GET',
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        return {
          service: 'NetStack API',
          status: 'error',
          message: `NetStack API 回應異常 (HTTP ${response.status})`,
          fixSuggestions: [
            '檢查 NetStack Docker 容器是否運行: docker ps | grep netstack-api',
            '重啟 NetStack 服務: cd netstack && docker-compose -f compose/core.yaml restart netstack-api'
          ]
        }
      }
      
      const data = await response.json()
      
      if (data.overall_status === 'healthy') {
        return {
          service: 'NetStack API',
          status: 'healthy',
          message: 'NetStack API 運行正常',
          details: {
            version: data.version,
            services: Object.keys(data.services || {}).length
          }
        }
      } else {
        return {
          service: 'NetStack API',
          status: 'warning',
          message: `NetStack API 狀態: ${data.overall_status}`,
          details: data,
          fixSuggestions: [
            '檢查 MongoDB 和 Redis 連接狀態',
            '查看 NetStack API 日誌: docker logs netstack-api'
          ]
        }
      }
      
    } catch (error) {
      return {
        service: 'NetStack API',
        status: 'error',
        message: 'NetStack API 無法連接',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
        fixSuggestions: [
          '確認 NetStack 服務是否啟動: make status',
          '檢查端口 8080 是否被占用: lsof -i :8080',
          '啟動 NetStack 服務: cd netstack && make up'
        ]
      }
    }
  }
  
  /**
   * 檢查 SimWorld 後端
   */
  private async checkSimWorldBackend(): Promise<DiagnosticResult> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const response = await fetch('http://localhost:8888/', {
        method: 'GET',
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        return {
          service: 'SimWorld 後端',
          status: 'error',
          message: `SimWorld 後端回應異常 (HTTP ${response.status})`,
          fixSuggestions: [
            '檢查 SimWorld Docker 容器: docker ps | grep simworld_backend',
            '重啟 SimWorld 服務: cd simworld && docker-compose restart backend'
          ]
        }
      }
      
      return {
        service: 'SimWorld 後端',
        status: 'healthy',
        message: 'SimWorld 後端運行正常'
      }
      
    } catch (error) {
      return {
        service: 'SimWorld 後端',
        status: 'error',
        message: 'SimWorld 後端無法連接',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
        fixSuggestions: [
          '啟動 SimWorld 服務: cd simworld && docker-compose up -d',
          '檢查端口 8888 是否被占用: lsof -i :8888'
        ]
      }
    }
  }
  
  /**
   * 檢查前端服務
   */
  private async checkFrontendService(): Promise<DiagnosticResult> {
    try {
      // 檢查當前頁面是否可以訪問
      if (typeof window !== 'undefined') {
        const currentUrl = window.location.href
        return {
          service: '前端服務',
          status: 'healthy',
          message: '前端服務運行正常',
          details: { url: currentUrl }
        }
      }
      
      return {
        service: '前端服務',
        status: 'warning',
        message: '無法確定前端服務狀態',
        fixSuggestions: [
          '確認前端開發服務器是否運行: ps aux | grep vite',
          '啟動前端服務: cd simworld/frontend && npm run dev'
        ]
      }
      
    } catch (error) {
      return {
        service: '前端服務',
        status: 'error',
        message: '前端服務檢查失敗',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
        fixSuggestions: [
          '重新啟動前端開發服務器',
          '檢查前端依賴是否安裝: npm install'
        ]
      }
    }
  }
  
  /**
   * 檢查數據庫連接
   */
  private async checkDatabaseConnection(): Promise<DiagnosticResult> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const response = await fetch('http://localhost:8080/health', {
        method: 'GET',
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        return {
          service: '數據庫連接',
          status: 'error',
          message: '無法檢查數據庫狀態'
        }
      }
      
      const data = await response.json()
      const mongoStatus = data.services?.mongodb?.status
      const redisStatus = data.services?.redis?.status
      
      if (mongoStatus === 'healthy' && redisStatus === 'healthy') {
        return {
          service: '數據庫連接',
          status: 'healthy',
          message: 'MongoDB 和 Redis 連接正常',
          details: {
            mongodb: data.services.mongodb,
            redis: data.services.redis
          }
        }
      } else {
        return {
          service: '數據庫連接',
          status: 'warning',
          message: '部分數據庫服務異常',
          details: { mongoStatus, redisStatus },
          fixSuggestions: [
            '檢查數據庫容器狀態: docker ps | grep -E "(mongo|redis)"',
            '重啟數據庫服務: cd netstack && docker-compose -f compose/core.yaml restart mongo redis'
          ]
        }
      }
      
    } catch (error) {
      return {
        service: '數據庫連接',
        status: 'error',
        message: '數據庫連接檢查失敗',
        fixSuggestions: [
          '確認數據庫服務是否啟動',
          '檢查網絡連接'
        ]
      }
    }
  }
  
  /**
   * 檢查核心同步服務
   */
  private async checkCoreSyncService(): Promise<DiagnosticResult> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const response = await fetch('http://localhost:8080/api/v1/core-sync/status', {
        method: 'GET',
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        return {
          service: '核心同步服務',
          status: 'error',
          message: `核心同步服務回應異常 (HTTP ${response.status})`,
          fixSuggestions: [
            '檢查 NetStack API 服務狀態',
            '重啟核心同步服務'
          ]
        }
      }
      
      const data = await response.json()
      
      if (data.service_info?.is_running && data.service_info?.core_sync_state === 'synchronized') {
        return {
          service: '核心同步服務',
          status: 'healthy',
          message: '核心同步服務正常運行',
          details: {
            state: data.service_info.core_sync_state,
            active_tasks: data.service_info.active_tasks,
            accuracy: data.sync_performance?.overall_accuracy_ms
          }
        }
      } else {
        return {
          service: '核心同步服務',
          status: 'warning',
          message: `核心同步狀態: ${data.service_info?.core_sync_state || 'unknown'}`,
          details: data,
          fixSuggestions: [
            '檢查同步服務配置',
            '重新初始化同步服務'
          ]
        }
      }
      
    } catch (error) {
      return {
        service: '核心同步服務',
        status: 'error',
        message: '核心同步服務無法連接',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
        fixSuggestions: [
          '確認 NetStack API 服務正常',
          '檢查核心同步端點配置'
        ]
      }
    }
  }
  
  /**
   * 分析診斷結果
   */
  private analyzeDiagnostics(diagnostics: DiagnosticResult[]): SystemDiagnostics {
    const healthy_count = diagnostics.filter(d => d.status === 'healthy').length
    const warning_count = diagnostics.filter(d => d.status === 'warning').length
    const error_count = diagnostics.filter(d => d.status === 'error').length
    const total_checks = diagnostics.length
    
    let overall_health: 'healthy' | 'degraded' | 'critical'
    
    if (error_count > 0) {
      overall_health = 'critical'
    } else if (warning_count > 0) {
      overall_health = 'degraded'
    } else {
      overall_health = 'healthy'
    }
    
    return {
      overall_health,
      diagnostics,
      summary: {
        healthy_count,
        warning_count,
        error_count,
        total_checks
      }
    }
  }
  
  /**
   * 顯示診斷報告
   */
  displayDiagnosticReport(diagnostics: SystemDiagnostics): void {
    console.log('\n🔍 系統健康診斷報告')
    console.log('=' .repeat(50))
    
    console.log(`\n📊 總體狀態: ${this.getStatusIcon(diagnostics.overall_health)} ${diagnostics.overall_health.toUpperCase()}`)
    console.log(`📈 檢查結果: ${diagnostics.summary.healthy_count}✅ ${diagnostics.summary.warning_count}⚠️ ${diagnostics.summary.error_count}❌`)
    
    console.log('\n📋 詳細診斷:')
    diagnostics.diagnostics.forEach(diagnostic => {
      const icon = this.getStatusIcon(diagnostic.status)
      console.log(`${icon} ${diagnostic.service}: ${diagnostic.message}`)
      
      if (diagnostic.fixSuggestions && diagnostic.fixSuggestions.length > 0) {
        console.log(`   💡 修復建議:`)
        diagnostic.fixSuggestions.forEach(suggestion => {
          console.log(`      • ${suggestion}`)
        })
      }
    })
    
    console.log('\n' + '=' .repeat(50))
  }
  
  private getStatusIcon(status: string): string {
    switch (status) {
      case 'healthy': return '✅'
      case 'warning': case 'degraded': return '⚠️'
      case 'error': case 'critical': return '❌'
      default: return 'ℹ️'
    }
  }
}

// 創建全局實例
export const healthDiagnostics = new HealthDiagnosticsService()

export default healthDiagnostics 