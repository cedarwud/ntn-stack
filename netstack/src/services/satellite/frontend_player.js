/**
 * 時間序列播放器 - 前端JavaScript實現
 * 
 * 基於文檔: 02-timeseries-planning.md
 * 功能:
 * 1. 24小時無縫循環播放
 * 2. 多倍速控制 (1x-60x)
 * 3. 記憶體優化管理
 * 4. 分段載入策略
 */

class TimeSeriesPlayer {
    constructor(timeseriesData, options = {}) {
        this.data = timeseriesData
        this.currentIndex = 0
        this.loopPoint = timeseriesData.metadata?.loop_point || timeseriesData.frames?.length || 0
        this.isPlaying = false
        this.playbackSpeed = 1
        this.frameRate = options.frameRate || 30 // FPS
        
        // 記憶體管理
        this.memoryManager = new MemoryManager(options.maxMemoryMB || 200)
        this.segmentLoader = new SegmentLoader(this.data, options.segmentMinutes || 60)
        
        // 事件回調
        this.onFrameUpdate = options.onFrameUpdate || (() => {})
        this.onLoopComplete = options.onLoopComplete || (() => {})
        this.onPlayStateChange = options.onPlayStateChange || (() => {})
        this.onSpeedChange = options.onSpeedChange || (() => {})
        
        // 性能監控
        this.performanceMonitor = new PerformanceMonitor()
        
        console.log('🎬 時間序列播放器初始化完成')
        console.log(`📊 總幀數: ${this.data.frames?.length || 0}, 循環點: ${this.loopPoint}`)
    }
    
    /**
     * 開始播放
     */
    play() {
        if (this.isPlaying) return
        
        this.isPlaying = true
        this.onPlayStateChange(true)
        console.log('▶️ 開始播放')
        
        this.animationLoop()
    }
    
    /**
     * 暫停播放
     */
    pause() {
        this.isPlaying = false
        this.onPlayStateChange(false)
        console.log('⏸️ 暫停播放')
    }
    
    /**
     * 停止播放
     */
    stop() {
        this.isPlaying = false
        this.currentIndex = 0
        this.onPlayStateChange(false)
        console.log('⏹️ 停止播放')
    }
    
    /**
     * 設置播放速度
     */
    setPlaybackSpeed(speed) {
        const oldSpeed = this.playbackSpeed
        this.playbackSpeed = Math.max(0.1, Math.min(speed, 60))
        this.onSpeedChange(this.playbackSpeed, oldSpeed)
        console.log(`⚡ 播放速度: ${this.playbackSpeed}x`)
    }
    
    /**
     * 跳轉到指定時間
     */
    seekToTime(timestamp) {
        const frameIndex = this.findFrameIndexByTimestamp(timestamp)
        if (frameIndex >= 0) {
            this.currentIndex = frameIndex
            this.updateFrame(this.currentIndex)
            console.log(`⏭️ 跳轉到: ${timestamp}`)
        }
    }
    
    /**
     * 跳轉到指定幀
     */
    seekToFrame(frameIndex) {
        if (frameIndex >= 0 && frameIndex < this.data.frames.length) {
            this.currentIndex = frameIndex
            this.updateFrame(this.currentIndex)
        }
    }
    
    /**
     * 主動畫循環
     */
    animationLoop() {
        if (!this.isPlaying) return
        
        const startTime = performance.now()
        
        // 更新當前幀
        this.updateFrame(this.currentIndex)
        
        // 計算下一幀
        const frameStep = this.calculateFrameStep()
        this.currentIndex += frameStep
        
        // 檢查循環點
        if (this.currentIndex >= this.loopPoint) {
            this.currentIndex = 0  // 無縫循環
            this.onLoopComplete()
            console.log('🔄 完成一次循環')
        }
        
        // 記憶體管理
        this.memoryManager.cleanup()
        
        // 性能監控
        const frameTime = performance.now() - startTime
        this.performanceMonitor.recordFrameTime(frameTime)
        
        // 計算下一幀延遲
        const targetFrameTime = 1000 / this.frameRate
        const delay = Math.max(0, targetFrameTime - frameTime)
        
        // 繼續動畫
        setTimeout(() => {
            if (this.isPlaying) {
                requestAnimationFrame(() => this.animationLoop())
            }
        }, delay)
    }
    
    /**
     * 更新當前幀
     */
    updateFrame(index) {
        const frameData = this.data.frames[index]
        if (!frameData) {
            console.warn(`⚠️ 幀數據不存在: ${index}`)
            return
        }
        
        try {
            // 更新衛星位置
            this.updateSatellitePositions(frameData.satellites || [])
            
            // 檢查換手事件
            this.checkHandoverEvents(frameData.timestamp)
            
            // 更新時間顯示
            this.updateTimeDisplay(frameData.timestamp)
            
            // 更新統計信息
            this.updateStatistics(frameData)
            
            // 觸發回調
            this.onFrameUpdate(frameData, index)
            
        } catch (error) {
            console.error('❌ 更新幀時發生錯誤:', error)
        }
    }
    
    /**
     * 計算幀步長
     */
    calculateFrameStep() {
        // 基於播放速度計算幀步長
        // 1x = 1幀, 10x = 10幀, 等等
        return Math.max(1, Math.round(this.playbackSpeed))
    }
    
    /**
     * 更新衛星位置
     */
    updateSatellitePositions(satellites) {
        satellites.forEach(sat => {
            this.updateSingleSatellite(sat)
        })
    }
    
    /**
     * 更新單顆衛星
     */
    updateSingleSatellite(sat) {
        // 這裡應該調用3D場景更新函數
        // 暫時輸出到控制台作為示例
        if (this.performanceMonitor.shouldLogDetails()) {
            console.log(`🛰️ ${sat.name}: ${sat.relative?.elevation?.toFixed(1)}° elevation`)
        }
    }
    
    /**
     * 檢查換手事件
     */
    checkHandoverEvents(timestamp) {
        // 檢查當前時間點是否有換手事件
        const events = this.findEventsAtTime(timestamp)
        if (events.length > 0) {
            console.log(`📡 檢測到 ${events.length} 個換手事件`)
            events.forEach(event => this.handleEvent(event))
        }
    }
    
    /**
     * 更新時間顯示
     */
    updateTimeDisplay(timestamp) {
        // 更新前端時間顯示
        const timeElement = document.getElementById('simulation-time')
        if (timeElement) {
            const date = new Date(timestamp)
            timeElement.textContent = date.toISOString().substring(0, 19).replace('T', ' ')
        }
    }
    
    /**
     * 更新統計信息
     */
    updateStatistics(frameData) {
        const stats = {
            visibleSatellites: frameData.satellites?.length || 0,
            activeEvents: frameData.active_events?.length || 0,
            handoverCandidates: frameData.handover_candidates?.length || 0
        }
        
        // 更新統計顯示
        this.displayStatistics(stats)
    }
    
    /**
     * 顯示統計信息
     */
    displayStatistics(stats) {
        const elements = {
            visible: document.getElementById('visible-count'),
            events: document.getElementById('event-count'),
            candidates: document.getElementById('candidate-count')
        }
        
        if (elements.visible) elements.visible.textContent = stats.visibleSatellites
        if (elements.events) elements.events.textContent = stats.activeEvents
        if (elements.candidates) elements.candidates.textContent = stats.handoverCandidates
    }
    
    /**
     * 根據時間戳找到幀索引
     */
    findFrameIndexByTimestamp(timestamp) {
        return this.data.frames.findIndex(frame => frame.timestamp === timestamp)
    }
    
    /**
     * 找到指定時間的事件
     */
    findEventsAtTime(timestamp) {
        // 從數據中查找事件
        return this.data.frames.find(frame => frame.timestamp === timestamp)?.active_events || []
    }
    
    /**
     * 處理事件
     */
    handleEvent(event) {
        console.log(`🔔 處理事件: ${event.type}`)
        // 這裡可以觸發視覺效果、聲音提示等
    }
    
    /**
     * 獲取當前狀態
     */
    getState() {
        return {
            isPlaying: this.isPlaying,
            currentIndex: this.currentIndex,
            currentTime: this.data.frames[this.currentIndex]?.timestamp,
            playbackSpeed: this.playbackSpeed,
            progress: this.currentIndex / (this.loopPoint || 1),
            performance: this.performanceMonitor.getStats()
        }
    }
}

/**
 * 記憶體管理器
 */
class MemoryManager {
    constructor(maxMemoryMB = 200) {
        this.maxMemoryBytes = maxMemoryMB * 1024 * 1024
        this.cache = new Map()
        this.lastCleanup = Date.now()
        this.cleanupInterval = 60000 // 60秒
    }
    
    cleanup() {
        const now = Date.now()
        if (now - this.lastCleanup > this.cleanupInterval) {
            this.performCleanup()
            this.lastCleanup = now
        }
    }
    
    performCleanup() {
        // 估算記憶體使用量
        const usage = this.estimateMemoryUsage()
        
        if (usage > this.maxMemoryBytes * 0.8) {
            console.log('🧹 執行記憶體清理')
            
            // 清理舊的快取項目
            const entries = Array.from(this.cache.entries())
            entries.sort((a, b) => a[1].lastAccess - b[1].lastAccess)
            
            // 刪除最舊的25%
            const toDelete = Math.floor(entries.length * 0.25)
            for (let i = 0; i < toDelete; i++) {
                this.cache.delete(entries[i][0])
            }
            
            // 強制垃圾回收（如果支持）
            if (window.gc) {
                window.gc()
            }
        }
    }
    
    estimateMemoryUsage() {
        // 簡化的記憶體使用量估算
        return this.cache.size * 1000 // 假設每個快取項目約1KB
    }
}

/**
 * 分段載入器
 */
class SegmentLoader {
    constructor(data, segmentMinutes = 60) {
        this.data = data
        this.segmentSize = segmentMinutes * 2 // 30秒間隔，60分鐘 = 120幀
        this.loadedSegments = new Set()
        this.loadingSegments = new Set()
    }
    
    async loadSegment(segmentIndex) {
        if (this.loadedSegments.has(segmentIndex) || this.loadingSegments.has(segmentIndex)) {
            return
        }
        
        this.loadingSegments.add(segmentIndex)
        
        try {
            console.log(`📦 載入片段 ${segmentIndex}`)
            
            // 模擬異步載入
            await new Promise(resolve => setTimeout(resolve, 100))
            
            this.loadedSegments.add(segmentIndex)
            this.loadingSegments.delete(segmentIndex)
            
        } catch (error) {
            console.error(`❌ 載入片段 ${segmentIndex} 失敗:`, error)
            this.loadingSegments.delete(segmentIndex)
        }
    }
    
    preloadNearbySegments(currentIndex) {
        const currentSegment = Math.floor(currentIndex / this.segmentSize)
        
        // 預載入當前和下一個片段
        for (let i = currentSegment; i <= currentSegment + 1; i++) {
            this.loadSegment(i)
        }
    }
}

/**
 * 性能監控器
 */
class PerformanceMonitor {
    constructor() {
        this.frameTimes = []
        this.maxSamples = 100
        this.logDetailInterval = 1000 // 1秒輸出一次詳細信息
        this.lastDetailLog = 0
    }
    
    recordFrameTime(frameTime) {
        this.frameTimes.push(frameTime)
        
        if (this.frameTimes.length > this.maxSamples) {
            this.frameTimes.shift()
        }
    }
    
    shouldLogDetails() {
        const now = Date.now()
        if (now - this.lastDetailLog > this.logDetailInterval) {
            this.lastDetailLog = now
            return true
        }
        return false
    }
    
    getStats() {
        if (this.frameTimes.length === 0) {
            return { avgFrameTime: 0, maxFrameTime: 0, fps: 0 }
        }
        
        const sum = this.frameTimes.reduce((a, b) => a + b, 0)
        const avg = sum / this.frameTimes.length
        const max = Math.max(...this.frameTimes)
        const fps = 1000 / avg
        
        return {
            avgFrameTime: avg.toFixed(2),
            maxFrameTime: max.toFixed(2),
            fps: fps.toFixed(1),
            samples: this.frameTimes.length
        }
    }
}

/**
 * 播放器控制 UI
 */
class PlayerControls {
    constructor(player) {
        this.player = player
        this.setupControls()
    }
    
    setupControls() {
        // 播放/暫停按鈕
        const playBtn = document.getElementById('play-button')
        if (playBtn) {
            playBtn.addEventListener('click', () => {
                if (this.player.isPlaying) {
                    this.player.pause()
                    playBtn.textContent = '▶️'
                } else {
                    this.player.play()
                    playBtn.textContent = '⏸️'
                }
            })
        }
        
        // 速度滑塊
        const speedSlider = document.getElementById('speed-slider')
        if (speedSlider) {
            speedSlider.addEventListener('input', (e) => {
                const speed = parseFloat(e.target.value)
                this.player.setPlaybackSpeed(speed)
                this.updateSpeedDisplay(speed)
            })
        }
        
        // 時間軸
        const timeline = document.getElementById('timeline')
        if (timeline) {
            timeline.addEventListener('click', (e) => {
                const rect = timeline.getBoundingClientRect()
                const progress = (e.clientX - rect.left) / rect.width
                const frameIndex = Math.floor(progress * this.player.loopPoint)
                this.player.seekToFrame(frameIndex)
            })
        }
    }
    
    updateSpeedDisplay(speed) {
        const display = document.getElementById('speed-display')
        if (display) {
            display.textContent = `${speed}x`
        }
    }
    
    updateProgressBar() {
        const progressBar = document.getElementById('progress-bar')
        if (progressBar) {
            const progress = this.player.currentIndex / this.player.loopPoint
            progressBar.style.width = `${progress * 100}%`
        }
    }
}

// 匯出供外部使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TimeSeriesPlayer, PlayerControls }
} else if (typeof window !== 'undefined') {
    window.TimeSeriesPlayer = TimeSeriesPlayer
    window.PlayerControls = PlayerControls
}