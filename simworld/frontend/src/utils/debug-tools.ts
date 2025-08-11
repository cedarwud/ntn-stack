/**
 * 開發調試工具集
 * 為 LEO 衛星換手研究提供專用調試功能
 */

import { apiCacheOptimizer, satelliteCacheOptimizer } from './api-cache-optimizer'
import { threePerformanceOptimizer } from './3d-performance-optimizer'

export interface DebugPanel {
  show: () => void
  hide: () => void
  toggle: () => void
  update: () => void
}

/**
 * 性能監控面板
 */
export class PerformanceDebugPanel implements DebugPanel {
  private panel: HTMLElement | null = null
  private isVisible = false
  private updateInterval: NodeJS.Timeout | null = null

  show(): void {
    if (this.isVisible) return
    
    this.createPanel()
    this.isVisible = true
    this.startUpdating()
  }

  hide(): void {
    if (!this.isVisible) return
    
    if (this.panel) {
      document.body.removeChild(this.panel)
      this.panel = null
    }
    this.isVisible = false
    this.stopUpdating()
  }

  toggle(): void {
    if (this.isVisible) {
      this.hide()
    } else {
      this.show()
    }
  }

  update(): void {
    if (!this.panel || !this.isVisible) return

    const stats = apiCacheOptimizer.getStats()
    const satelliteStats = satelliteCacheOptimizer.getStats()
    
    const content = `
      <div style="padding: 16px; font-family: monospace; font-size: 12px;">
        <h3 style="margin: 0 0 12px 0; color: #00ff00;">🛰️ LEO 衛星系統性能監控</h3>
        
        <div style="margin-bottom: 16px;">
          <h4 style="margin: 0 0 8px 0; color: #ffa500;">📊 API 緩存統計</h4>
          <div>緩存條目: ${stats.totalEntries}</div>
          <div>命中率: ${(stats.hitRate * 100).toFixed(1)}%</div>
          <div>內存使用: ${(stats.memoryUsage / 1024).toFixed(1)} KB</div>
          <div>熱門端點:</div>
          <ul style="margin: 4px 0; padding-left: 16px;">
            ${stats.topEndpoints.slice(0, 3).map(ep => 
              `<li>${ep.endpoint}: ${ep.accessCount}次</li>`
            ).join('')}
          </ul>
        </div>

        <div style="margin-bottom: 16px;">
          <h4 style="margin: 0 0 8px 0; color: #ffa500;">🛰️ 衛星緩存統計</h4>
          <div>衛星數據條目: ${satelliteStats.totalEntries}</div>
          <div>命中率: ${(satelliteStats.hitRate * 100).toFixed(1)}%</div>
          <div>內存使用: ${(satelliteStats.memoryUsage / 1024).toFixed(1)} KB</div>
        </div>

        <div style="margin-bottom: 16px;">
          <h4 style="margin: 0 0 8px 0; color: #ffa500;">⚡ 系統性能</h4>
          <div>內存使用: ${this.getMemoryUsage()} MB</div>
          <div>FPS: ${this.getFPS()}</div>
          <div>更新時間: ${new Date().toLocaleTimeString()}</div>
        </div>

        <div>
          <button onclick="window.debugTools.clearAllCache()" 
                  style="padding: 4px 8px; margin-right: 8px; background: #ff4444; color: white; border: none; border-radius: 3px; cursor: pointer;">
            清空緩存
          </button>
          <button onclick="window.debugTools.exportStats()" 
                  style="padding: 4px 8px; margin-right: 8px; background: #4444ff; color: white; border: none; border-radius: 3px; cursor: pointer;">
            導出統計
          </button>
          <button onclick="window.debugTools.togglePanel()" 
                  style="padding: 4px 8px; background: #44ff44; color: black; border: none; border-radius: 3px; cursor: pointer;">
            隱藏面板
          </button>
        </div>
      </div>
    `

    this.panel!.innerHTML = content
  }

  private createPanel(): void {
    this.panel = document.createElement('div')
    this.panel.id = 'debug-performance-panel'
    this.panel.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      width: 350px;
      background: rgba(0, 0, 0, 0.9);
      color: #ffffff;
      border: 1px solid #333;
      border-radius: 8px;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    `
    
    document.body.appendChild(this.panel)
    this.update()
  }

  private startUpdating(): void {
    this.updateInterval = setInterval(() => this.update(), 1000)
  }

  private stopUpdating(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval)
      this.updateInterval = null
    }
  }

  private getMemoryUsage(): string {
    if ('memory' in performance) {
      return ((performance as any).memory.usedJSHeapSize / 1024 / 1024).toFixed(1)
    }
    return 'N/A'
  }

  private getFPS(): string {
    // 簡化的 FPS 計算
    if (typeof window.frameStartTime === 'undefined') {
      window.frameStartTime = performance.now()
      window.frameCount = 0
    }
    
    window.frameCount++
    const now = performance.now()
    const elapsed = now - window.frameStartTime
    
    if (elapsed >= 1000) {
      const fps = Math.round((window.frameCount * 1000) / elapsed)
      window.frameStartTime = now
      window.frameCount = 0
      return fps.toString()
    }
    
    return 'Measuring...'
  }
}

/**
 * 衛星調試工具
 */
export class SatelliteDebugTools {
  /**
   * 日誌衛星換手事件
   */
  static logHandoverEvent(event: {
    fromSatellite?: string
    toSatellite?: string
    reason?: string
    timestamp?: number
    metadata?: Record<string, any>
  }): void {
    const logEntry = {
      timestamp: event.timestamp || Date.now(),
      type: 'HANDOVER_EVENT',
      from: event.fromSatellite || 'unknown',
      to: event.toSatellite || 'unknown',
      reason: event.reason || 'unspecified',
      metadata: event.metadata || {},
      time: new Date().toISOString()
    }

    console.group('🛰️ 衛星換手事件')
    console.log('從衛星:', logEntry.from)
    console.log('到衛星:', logEntry.to)
    console.log('觸發原因:', logEntry.reason)
    console.log('時間戳:', logEntry.time)
    if (Object.keys(logEntry.metadata).length > 0) {
      console.log('附加信息:', logEntry.metadata)
    }
    console.groupEnd()

    // 存儲到本地用於調試
    this.storeDebugLog('handover', logEntry)
  }

  /**
   * 日誌衛星可見性變化
   */
  static logVisibilityChange(satelliteId: string, isVisible: boolean, elevation: number): void {
    const logEntry = {
      timestamp: Date.now(),
      type: 'VISIBILITY_CHANGE',
      satelliteId,
      isVisible,
      elevation,
      time: new Date().toISOString()
    }

    console.log(`🛰️ ${satelliteId} ${isVisible ? '進入' : '離開'}視野 (仰角: ${elevation.toFixed(1)}°)`)
    this.storeDebugLog('visibility', logEntry)
  }

  /**
   * 存儲調試日誌
   */
  private static storeDebugLog(category: string, entry: any): void {
    const key = `debug_${category}_logs`
    const logs = JSON.parse(localStorage.getItem(key) || '[]')
    
    logs.push(entry)
    
    // 只保留最近100條記錄
    if (logs.length > 100) {
      logs.splice(0, logs.length - 100)
    }
    
    localStorage.setItem(key, JSON.stringify(logs))
  }

  /**
   * 獲取調試日誌
   */
  static getDebugLogs(category: string): any[] {
    const key = `debug_${category}_logs`
    return JSON.parse(localStorage.getItem(key) || '[]')
  }

  /**
   * 清空調試日誌
   */
  static clearDebugLogs(category?: string): void {
    if (category) {
      localStorage.removeItem(`debug_${category}_logs`)
    } else {
      // 清空所有調試日誌
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('debug_') && key.endsWith('_logs')) {
          localStorage.removeItem(key)
        }
      })
    }
  }
}

/**
 * 全局調試工具
 */
export class GlobalDebugTools {
  private performancePanel: PerformanceDebugPanel

  constructor() {
    this.performancePanel = new PerformanceDebugPanel()
    this.setupGlobalMethods()
    this.setupKeyboardShortcuts()
  }

  private setupGlobalMethods(): void {
    // 將工具方法添加到全局對象
    (window as any).debugTools = {
      showPanel: () => this.performancePanel.show(),
      hidePanel: () => this.performancePanel.hide(),
      togglePanel: () => this.performancePanel.toggle(),
      
      clearAllCache: () => {
        apiCacheOptimizer.clear()
        satelliteCacheOptimizer.clear()
        threePerformanceOptimizer.clearCache()
        console.log('🧹 所有緩存已清空')
      },

      exportStats: () => {
        const stats = {
          apiCache: apiCacheOptimizer.getStats(),
          satelliteCache: satelliteCacheOptimizer.getStats(),
          handoverLogs: SatelliteDebugTools.getDebugLogs('handover'),
          visibilityLogs: SatelliteDebugTools.getDebugLogs('visibility'),
          timestamp: new Date().toISOString()
        }
        
        const blob = new Blob([JSON.stringify(stats, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `leo-satellite-stats-${Date.now()}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        
        console.log('📊 統計數據已導出')
      },

      logHandover: SatelliteDebugTools.logHandoverEvent,
      logVisibility: SatelliteDebugTools.logVisibilityChange,
      getHandoverLogs: () => SatelliteDebugTools.getDebugLogs('handover'),
      getVisibilityLogs: () => SatelliteDebugTools.getDebugLogs('visibility'),
      clearLogs: SatelliteDebugTools.clearDebugLogs
    }
  }

  private setupKeyboardShortcuts(): void {
    document.addEventListener('keydown', (e) => {
      // Ctrl+Shift+D 顯示/隱藏調試面板
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault()
        this.performancePanel.toggle()
      }
      
      // Ctrl+Shift+C 清空緩存
      if (e.ctrlKey && e.shiftKey && e.key === 'C') {
        e.preventDefault()
        ;(window as any).debugTools.clearAllCache()
      }
      
      // Ctrl+Shift+E 導出統計
      if (e.ctrlKey && e.shiftKey && e.key === 'E') {
        e.preventDefault()
        ;(window as any).debugTools.exportStats()
      }
    })
  }

  /**
   * 在開發模式下自動啟動
   */
  static autoStart(): void {
    if (process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost') {
      new GlobalDebugTools()
      console.log('🔧 調試工具已啟動')
      console.log('快捷鍵:')
      console.log('  Ctrl+Shift+D: 顯示/隱藏性能面板')
      console.log('  Ctrl+Shift+C: 清空所有緩存')
      console.log('  Ctrl+Shift+E: 導出統計數據')
    }
  }
}

// 擴展全局類型
declare global {
  interface Window {
    debugTools: {
      showPanel: () => void
      hidePanel: () => void
      togglePanel: () => void
      clearAllCache: () => void
      exportStats: () => void
      logHandover: (event: any) => void
      logVisibility: (satelliteId: string, isVisible: boolean, elevation: number) => void
      getHandoverLogs: () => any[]
      getVisibilityLogs: () => any[]
      clearLogs: (category?: string) => void
    }
    frameStartTime: number
    frameCount: number
  }
}

export { SatelliteDebugTools, GlobalDebugTools }