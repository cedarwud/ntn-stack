// 性能監控工具
class PerformanceMonitor {
    private static instance: PerformanceMonitor
    private performanceObserver: PerformanceObserver | null = null
    private isMonitoring = false
    private longTaskCount = 0
    private lastLongTaskReport = 0
    private memoryCheckInterval: number | null = null

    static getInstance(): PerformanceMonitor {
        if (!PerformanceMonitor.instance) {
            PerformanceMonitor.instance = new PerformanceMonitor()
        }
        return PerformanceMonitor.instance
    }

    startMonitoring(): void {
        if (this.isMonitoring || typeof window === 'undefined') return

        try {
            // 監控長任務（但降低報告頻率）
            this.performanceObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'longtask') {
                        this.handleLongTask(entry)
                    }
                }
            })

            this.performanceObserver.observe({ entryTypes: ['longtask'] })

            // 監控記憶體使用（如果可用）
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            if ('memory' in performance && (performance as any).memory) {
                this.monitorMemory()
            }

            // 監控錯誤（更嚴格的過濾）
            window.addEventListener('error', this.handleError)
            window.addEventListener('unhandledrejection', this.handleUnhandledRejection)

            this.isMonitoring = true
            console.log('性能監控已啟動（智能模式）')
        } catch (error) {
            console.warn('無法啟動性能監控:', error)
        }
    }

    stopMonitoring(): void {
        if (!this.isMonitoring) return

        if (this.performanceObserver) {
            this.performanceObserver.disconnect()
            this.performanceObserver = null
        }

        if (this.memoryCheckInterval) {
            clearInterval(this.memoryCheckInterval)
            this.memoryCheckInterval = null
        }

        window.removeEventListener('error', this.handleError)
        window.removeEventListener('unhandledrejection', this.handleUnhandledRejection)

        this.isMonitoring = false
        console.log('性能監控已停止')
    }

    private handleLongTask(entry: PerformanceEntry): void {
        this.longTaskCount++
        const now = performance.now()

        // 智能長任務報告策略
        // 1. 忽略短時間的長任務（< 100ms）
        if (entry.duration < 100) return

        // 2. 限制報告頻率：每10秒最多報告一次
        if (now - this.lastLongTaskReport < 10000) return

        // 3. 檢查是否在3D渲染環境中
        if (this.isIn3DEnvironment()) {
            // 在3D環境中，只報告極長的任務（> 500ms）
            if (entry.duration < 500) return
        }

        console.warn('檢測到顯著長任務:', {
            duration: `${Math.round(entry.duration)}ms`,
            totalCount: this.longTaskCount,
            environment: this.isIn3DEnvironment() ? '3D渲染' : '一般'
        })

        this.lastLongTaskReport = now
    }

    private isIn3DEnvironment(): boolean {
        // 檢查頁面中是否有Three.js相關元素
        return !!(
            document.querySelector('canvas') ||
            window.location.pathname.includes('stereogram') ||
            document.querySelector('[class*="scene"]')
        )
    }

    private monitorMemory(): void {
        const checkMemory = () => {
            if ('memory' in performance) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const memory = (performance as any).memory
                const usedMB = Math.round(memory.usedJSHeapSize / 1024 / 1024)
                const totalMB = Math.round(memory.totalJSHeapSize / 1024 / 1024)
                const limitMB = Math.round(memory.jsHeapSizeLimit / 1024 / 1024)

                // 記憶體使用超過 90% 才發出警告
                if (usedMB / limitMB > 0.9) {
                    console.warn('記憶體使用率極高:', {
                        used: `${usedMB}MB`,
                        total: `${totalMB}MB`,
                        limit: `${limitMB}MB`,
                        usage: `${Math.round((usedMB / limitMB) * 100)}%`
                    })
                }
            }
        }

        // 每 60 秒檢查一次記憶體（降低頻率）
        this.memoryCheckInterval = window.setInterval(checkMemory, 60000)
    }

    private handleError = (event: ErrorEvent): void => {
        // 更嚴格地過濾瀏覽器擴展錯誤
        if (this.isExtensionError(event)) {
            return
        }

        // 過濾已知的無害錯誤
        if (this.isKnownHarmlessError(event)) {
            return
        }

        console.error('應用錯誤:', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            error: event.error
        })
    }

    private isExtensionError(event: ErrorEvent): boolean {
        const extensionIndicators = [
            'chrome-extension://',
            'moz-extension://',
            'extension',
            'CacheStore.js',
            'GenAIWebpageEligibilityService',
            'ActionableCoachmark',
            'ShowOneChild',
            'ch-content-script',
            'content-script-utils',
            'jquery-3.1.1.min.js'
        ]

        return extensionIndicators.some(indicator => 
            event.filename?.includes(indicator) ||
            event.message?.includes(indicator) ||
            event.error?.stack?.includes(indicator)
        )
    }

    private isKnownHarmlessError(event: ErrorEvent): boolean {
        const harmlessPatterns = [
            'Cache get failed',
            'Cache set failed',
            'caches is not defined',
            'ResizeObserver loop limit exceeded'
        ]

        return harmlessPatterns.some(pattern =>
            event.message?.includes(pattern)
        )
    }

    private handleUnhandledRejection = (event: PromiseRejectionEvent): void => {
        // 過濾擴展相關的 Promise 拒絕
        const reason = event.reason?.toString() || ''
        if (this.isExtensionRelated(reason)) {
            return
        }

        console.error('未處理的 Promise 拒絕:', event.reason)
    }

    private isExtensionRelated(text: string): boolean {
        const extensionKeywords = [
            'extension',
            'Cache',
            'GenAI',
            'Coachmark'
        ]

        return extensionKeywords.some(keyword => text.includes(keyword))
    }

    // 輔助函數：檢查 WebGL 上下文
    checkWebGLContext(): boolean {
        try {
            const canvas = document.createElement('canvas')
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
            if (!gl) {
                console.warn('WebGL 不可用')
                return false
            }
            return true
        } catch (error) {
            console.error('WebGL 檢查失敗:', error)
            return false
        }
    }

    // 輔助函數：獲取性能指標
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    getPerformanceMetrics(): any {
        if (typeof window === 'undefined' || !window.performance) {
            return null
        }

        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
        
        return {
            // 頁面載入時間
            domContentLoaded: navigation?.domContentLoadedEventEnd - navigation?.domContentLoadedEventStart,
            pageLoad: navigation?.loadEventEnd - navigation?.loadEventStart,
            
            // 記憶體使用（如果可用）
            memory: 'memory' in performance ? {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                used: Math.round(((performance as any).memory.usedJSHeapSize) / 1024 / 1024),
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                total: Math.round(((performance as any).memory.totalJSHeapSize) / 1024 / 1024),
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                limit: Math.round(((performance as any).memory.jsHeapSizeLimit) / 1024 / 1024)
            } : null,
            
            // WebGL 支援
            webglSupported: this.checkWebGLContext(),
            
            // 長任務統計
            longTaskCount: this.longTaskCount,
            environment: this.isIn3DEnvironment() ? '3D渲染環境' : '一般網頁環境'
        }
    }

    // 新增：手動報告性能總結
    reportPerformanceSummary(): void {
         
         
         
        const _metrics = this.getPerformanceMetrics()
        if (metrics) {
            console.group('📊 性能監控總結')
            console.log('環境類型:', metrics.environment)
            console.log('長任務總數:', metrics.longTaskCount)
            if (metrics.memory) {
                console.log('記憶體使用:', `${metrics.memory.used}MB / ${metrics.memory.limit}MB`)
            }
            console.log('WebGL 支援:', metrics.webglSupported ? '✅' : '❌')
            console.groupEnd()
        }
    }
}

export default PerformanceMonitor

// 自動啟動監控（僅在開發環境）
if (import.meta.env.DEV) {
    const monitor = PerformanceMonitor.getInstance()
    monitor.startMonitoring()
    
    // 每5分鐘報告一次性能總結
    setInterval(() => {
        monitor.reportPerformanceSummary()
    }, 5 * 60 * 1000)
} 