/**
 * 後台健康監控服務
 * 定期執行系統檢測，異常時使用 toast 警告
 */

import { runSystemTests, SystemTestResults } from '../test/test-utils'

// Toast 通知函數類型
type ToastFunction = (message: string, type: 'success' | 'error' | 'warning' | 'info') => void

class BackgroundHealthMonitor {
  private intervalId: NodeJS.Timeout | null = null
  private lastResults: SystemTestResults | null = null
  private toastFn: ToastFunction | null = null
  private isRunning = false
  
  /**
   * 設置 toast 通知函數
   */
  setToastFunction(toastFn: ToastFunction) {
    this.toastFn = toastFn
  }
  
  /**
   * 啟動單次健康檢查（網頁載入時）
   */
  async startInitialCheck() {
    if (this.isRunning) {
      return
    }
    
    this.isRunning = true
    console.log('🔍 執行網頁載入時的系統健康檢查...')
    
    // 只執行一次檢測
    await this.runHealthCheck()
    
    // 檢測完成後停止運行狀態
    this.isRunning = false
    console.log('✅ 網頁載入時的健康檢查完成')
  }
  
  /**
   * 停止後台監控（清理資源）
   */
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
    this.isRunning = false
    console.log('🛑 後台健康監控已停止')
  }
  
  /**
   * 執行健康檢查
   */
  private async runHealthCheck() {
    try {
      console.log('🔍 執行系統健康檢查...')
      const results = await runSystemTests(false) // 快速檢查，不包含性能測試
      
      this.analyzeResults(results)
      this.lastResults = results
      
      console.log('✅ 系統健康檢查完成')
      
    } catch (error) {
      console.error('❌ 系統健康檢查失敗:', error)
      this.showToast('系統健康檢查執行失敗', 'error')
    }
  }
  
  /**
   * 分析檢測結果，如有異常發送 toast 通知
   */
  private analyzeResults(results: SystemTestResults) {
    const issues: string[] = []
    
    // 檢查關鍵系統狀態
    if (!results.netstack_core_sync?.success) {
      issues.push('NetStack 核心服務異常')
    }
    
     
    if (!results.simworld_satellites?.success) {
      issues.push('SimWorld 衛星數據異常')
    }
    
    if (!results.real_connections?.success) {
      issues.push('API 整合異常')
    }
    
    if (!results.ieee_algorithm?.success) {
      issues.push('IEEE 算法異常')
    }
    
    // 如果有問題，發送警告通知
    if (issues.length > 0) {
      const message = `檢測到 ${issues.length} 個問題: ${issues.join(', ')}`
      this.showToast(message, 'warning')
      console.warn('🚨 系統健康檢查發現問題:', issues)
    } else if (this.lastResults && this.hasNewIssues(results)) {
      // 如果之前有問題，現在恢復正常
      this.showToast('系統健康狀態已恢復正常', 'success')
      console.log('✅ 系統健康狀態已恢復正常')
    }
  }
  
  /**
   * 檢查是否有新的問題
   */
  private hasNewIssues(current: SystemTestResults): boolean {
    if (!this.lastResults) return false
    
    // 簡單比較主要系統狀態
    return (
      this.lastResults.netstack_core_sync?.success !== current.netstack_core_sync?.success ||
       
      this.lastResults.simworld_satellites?.success !== current.simworld_satellites?.success ||
      this.lastResults.real_connections?.success !== current.real_connections?.success
    )
  }
  
  /**
   * 顯示 toast 通知
   */
  private showToast(message: string, type: 'success' | 'error' | 'warning' | 'info') {
    if (this.toastFn) {
      this.toastFn(message, type)
    } else {
      // 回退到 console 輸出
      const prefix = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'
      console.log(`${prefix} ${message}`)
    }
  }
  
  /**
   * 獲取當前運行狀態
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      lastResults: this.lastResults,
      lastCheckTime: this.lastResults ? new Date().toISOString() : null
    }
  }
  
  /**
   * 手動觸發檢查
   */
  async triggerCheck() {
    if (!this.isRunning) {
      console.warn('後台監控未啟動，無法手動觸發檢查')
      return
    }
    
    await this.runHealthCheck()
  }
}

// 創建全局實例
export const backgroundHealthMonitor = new BackgroundHealthMonitor()

export default backgroundHealthMonitor