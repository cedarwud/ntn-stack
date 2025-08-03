/**
 * 實時事件推送系統
 * 負責處理 WebSocket 事件推送和數據同步
 */

export interface RealtimeEvent {
  type: 'rl_update' | 'handover_trigger' | 'candidate_update' | 'decision_made' | 'performance_update'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any
  timestamp: number
  source: string
}

export interface EventSubscription {
  id: string
  eventType: string
  callback: (event: RealtimeEvent) => void
  filter?: (event: RealtimeEvent) => boolean
}

export interface EventMetrics {
  totalEvents: number
  eventsPerSecond: number
  lastEventTime: number
  eventTypes: Record<string, number>
}

export class RealtimeEventStreamer {
  private subscriptions: Map<string, EventSubscription> = new Map()
  private eventBuffer: RealtimeEvent[] = []
  private maxBufferSize = 1000
  private metrics: EventMetrics = {
    totalEvents: 0,
    eventsPerSecond: 0,
    lastEventTime: 0,
    eventTypes: {}
  }

  private metricsUpdateInterval: NodeJS.Timeout | null = null
  private eventProcessingInterval: NodeJS.Timeout | null = null

  constructor() {
    this.startMetricsTracking()
    this.startEventProcessing()
  }

  /**
   * 啟動指標追蹤
   */
  private startMetricsTracking() {
    this.metricsUpdateInterval = setInterval(() => {
      this.updateMetrics()
    }, 1000)
  }

  /**
   * 啟動事件處理
   */
  private startEventProcessing() {
    this.eventProcessingInterval = setInterval(() => {
      this.processEventBuffer()
    }, 100) // 每 100ms 處理一次事件
  }

  /**
   * 訂閱事件
   */
  public subscribe(
    eventType: string,
    callback: (event: RealtimeEvent) => void,
    filter?: (event: RealtimeEvent) => boolean
  ): string {
    const id = this.generateSubscriptionId()
    const subscription: EventSubscription = {
      id,
      eventType,
      callback,
      filter
    }

    this.subscriptions.set(id, subscription)
    return id
  }

  /**
   * 取消訂閱
   */
  public unsubscribe(subscriptionId: string): boolean {
    return this.subscriptions.delete(subscriptionId)
  }

  /**
   * 處理實時數據
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public processRealtimeData(data: any) {
    try {
      const event = this.parseWebSocketData(data)
      if (event) {
        this.addEvent(event)
      }
    } catch (error) {
      console.error('❌ 處理實時數據時發生錯誤:', error)
    }
  }

  /**
   * 解析 WebSocket 數據
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private parseWebSocketData(data: any): RealtimeEvent | null {
    if (!data || typeof data !== 'object') {
      return null
    }

    // 根據數據格式判斷事件類型
    if (data.type === 'handover_monitoring') {
      return {
        type: 'handover_update',
        data: data.payload,
        timestamp: Date.now(),
        source: 'handover_monitor'
      }
    }

    if (data.type === 'handover_event') {
      return {
        type: 'handover_trigger',
        data: data.payload,
        timestamp: Date.now(),
        source: 'handover_system'
      }
    }

    if (data.type === 'candidate_selection') {
      return {
        type: 'candidate_update',
        data: data.payload,
        timestamp: Date.now(),
        source: 'candidate_service'
      }
    }

    if (data.type === 'decision_result') {
      return {
        type: 'decision_made',
        data: data.payload,
        timestamp: Date.now(),
        source: 'decision_engine'
      }
    }

    if (data.type === 'performance_metrics') {
      return {
        type: 'performance_update',
        data: data.payload,
        timestamp: Date.now(),
        source: 'performance_monitor'
      }
    }

    // 通用事件格式
    if (data.event_type && data.payload) {
      return {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        type: data.event_type as any,
        data: data.payload,
        timestamp: data.timestamp || Date.now(),
        source: data.source || 'unknown'
      }
    }

    return null
  }

  /**
   * 添加事件到緩衝區
   */
  private addEvent(event: RealtimeEvent) {
    this.eventBuffer.push(event)
    
    // 限制緩衝區大小
    if (this.eventBuffer.length > this.maxBufferSize) {
      this.eventBuffer.shift()
    }

    // 更新指標
    this.metrics.totalEvents++
    this.metrics.lastEventTime = event.timestamp
    this.metrics.eventTypes[event.type] = (this.metrics.eventTypes[event.type] || 0) + 1
  }

  /**
   * 處理事件緩衝區
   */
  private processEventBuffer() {
    if (this.eventBuffer.length === 0) return

    const eventsToProcess = [...this.eventBuffer]
    this.eventBuffer = []

    eventsToProcess.forEach(event => {
      this.distributeEvent(event)
    })
  }

  /**
   * 分發事件給訂閱者
   */
  private distributeEvent(event: RealtimeEvent) {
    this.subscriptions.forEach(subscription => {
      if (subscription.eventType === event.type || subscription.eventType === '*') {
        // 應用過濾器
        if (subscription.filter && !subscription.filter(event)) {
          return
        }

        try {
          subscription.callback(event)
        } catch (error) {
          console.error('❌ 事件回調函數執行失敗:', error)
        }
      }
    })
  }

  /**
   * 更新指標
   */
  private updateMetrics() {
    const now = Date.now()
    const timeSinceLastUpdate = now - (this.metrics.lastEventTime || now)
    
    // 計算每秒事件數
    if (timeSinceLastUpdate < 5000) { // 最近 5 秒內有事件
      this.metrics.eventsPerSecond = this.metrics.totalEvents / ((now - this.metrics.lastEventTime) / 1000)
    } else {
      this.metrics.eventsPerSecond = 0
    }
  }

  /**
   * 生成訂閱 ID
   */
  private generateSubscriptionId(): string {
    return `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 獲取事件指標
   */
  public getMetrics(): EventMetrics {
    return { ...this.metrics }
  }

  /**
   * 獲取最近的事件
   */
  public getRecentEvents(count: number = 10): RealtimeEvent[] {
    return this.eventBuffer.slice(-count)
  }

  /**
   * 獲取特定類型的事件
   */
  public getEventsByType(eventType: string, count: number = 10): RealtimeEvent[] {
    return this.eventBuffer
      .filter(event => event.type === eventType)
      .slice(-count)
  }

  /**
   * 清理事件緩衝區
   */
  public clearEventBuffer() {
    this.eventBuffer = []
  }

  /**
   * 重置指標
   */
  public resetMetrics() {
    this.metrics = {
      totalEvents: 0,
      eventsPerSecond: 0,
      lastEventTime: 0,
      eventTypes: {}
    }
  }

  /**
   * 模擬事件（用於測試）
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public simulateEvent(type: RealtimeEvent['type'], data: any) {
    const event: RealtimeEvent = {
      type,
      data,
      timestamp: Date.now(),
      source: 'simulator'
    }

    this.addEvent(event)
  }

  /**
   * 模擬 RL 更新事件
   */
  public simulateRLUpdate() {
    this.simulateEvent('rl_update', {
      algorithm: 'DQN',
      episode: 1234,
      reward: 0.87,
      loss: 0.023,
      epsilon: 0.1,
      timestamp: Date.now()
    })
  }

  /**
   * 模擬換手觸發事件
   */
  public simulateHandoverTrigger() {
    this.simulateEvent('handover_trigger', {
      trigger_type: 'signal_degradation',
      current_satellite: 'sat_001',
      signal_strength: 0.3,
      candidates: ['sat_002', 'sat_003', 'sat_004'],
      timestamp: Date.now()
    })
  }

  /**
   * 模擬候選更新事件
   */
  public simulateCandidateUpdate() {
    this.simulateEvent('candidate_update', {
      candidates: [
        { id: 'sat_002', score: 0.92, signal: 0.85, load: 0.4 },
        { id: 'sat_003', score: 0.88, signal: 0.79, load: 0.6 },
        { id: 'sat_004', score: 0.84, signal: 0.82, load: 0.3 }
      ],
      best_candidate: 'sat_002',
      timestamp: Date.now()
    })
  }

  /**
   * 模擬決策事件
   */
  public simulateDecisionMade() {
    this.simulateEvent('decision_made', {
      algorithm: 'PPO',
      selected_satellite: 'sat_002',
      confidence: 0.89,
      reasoning: {
        signal_score: 0.85,
        load_score: 0.93,
        distance_score: 0.91
      },
      timestamp: Date.now()
    })
  }

  /**
   * 獲取活躍訂閱數
   */
  public getActiveSubscriptions(): number {
    return this.subscriptions.size
  }

  /**
   * 獲取事件緩衝區大小
   */
  public getBufferSize(): number {
    return this.eventBuffer.length
  }

  /**
   * 銷毀事件推送器
   */
  public destroy() {
    if (this.metricsUpdateInterval) {
      clearInterval(this.metricsUpdateInterval)
    }
    if (this.eventProcessingInterval) {
      clearInterval(this.eventProcessingInterval)
    }
    
    this.subscriptions.clear()
    this.eventBuffer = []
  }
}

export default RealtimeEventStreamer