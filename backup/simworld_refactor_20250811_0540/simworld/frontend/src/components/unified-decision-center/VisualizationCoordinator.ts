/**
 * 視覺化協調器
 * 負責協調 3D 動畫與決策流程的精確同步
 */

export interface DecisionPhase {
  id: string
  name: string
  description: string
  duration: number
  status: 'pending' | 'active' | 'completed' | 'skipped'
}

export interface CandidateInfo {
  id: string
  name: string
  position: [number, number, number]
  score: number
  signalStrength: number
  load: number
  elevation: number
  distance: number
  rank: number
}

export interface HandoverState {
  isHandover: boolean
  progress: number
  phase: string
  currentSatellite?: string
  targetSatellite?: string
}

export interface AnimationEvent {
  type: 'phase_change' | 'candidate_highlight' | 'decision_made' | 'handover_execute'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any
  timestamp: number
}

export class VisualizationCoordinator {
  private phases: DecisionPhase[] = [
    {
      id: 'monitoring',
      name: '監控階段',
      description: '監控當前連接狀態',
      duration: 1000,
      status: 'active'
    },
    {
      id: 'trigger_detection',
      name: '觸發檢測',
      description: '檢測到換手觸發條件',
      duration: 500,
      status: 'pending'
    },
    {
      id: 'candidate_selection',
      name: '候選篩選',
      description: '選擇候選衛星並評分',
      duration: 800,
      status: 'pending'
    },
    {
      id: 'rl_decision',
      name: 'RL 決策',
      description: '強化學習算法決策',
      duration: 200,
      status: 'pending'
    },
    {
      id: 'handover_preparation',
      name: '換手準備',
      description: '準備換手執行',
      duration: 600,
      status: 'pending'
    },
    {
      id: 'handover_execution',
      name: '換手執行',
      description: '執行換手操作',
      duration: 1200,
      status: 'pending'
    },
    {
      id: 'monitoring_resume',
      name: '監控恢復',
      description: '恢復正常監控狀態',
      duration: 400,
      status: 'pending'
    }
  ]

  private currentPhaseIndex = 0
  private animationQueue: AnimationEvent[] = []
  // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
  private eventListeners: Map<string, Function[]> = new Map()
  private handoverState: HandoverState = {
    isHandover: false,
    progress: 0,
    phase: 'monitoring'
  }

  private candidateInfo: CandidateInfo[] = []
  private currentAlgorithm = 'DQN'

  constructor() {
    this.initializeEventListeners()
  }

  private initializeEventListeners() {
    // 初始化事件監聽器
    this.eventListeners.set('phase_change', [])
    this.eventListeners.set('candidate_update', [])
    this.eventListeners.set('algorithm_switch', [])
    this.eventListeners.set('handover_state_change', [])
  }

  /**
   * 註冊事件監聽器
   */
  // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
  public addEventListener(event: string, listener: Function) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event)!.push(listener)
  }

  /**
   * 移除事件監聽器
   */
  // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
  public removeEventListener(event: string, listener: Function) {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  /**
   * 觸發事件
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private emit(event: string, data?: any) {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      listeners.forEach(listener => listener(data))
    }
  }

  /**
   * 階段變更通知
   */
  public notifyPhaseChange(phase: string, progress: number) {
    const phaseIndex = this.phases.findIndex(p => p.id === phase)
    if (phaseIndex !== -1) {
      this.currentPhaseIndex = phaseIndex
      this.phases[phaseIndex].status = 'active'
      
      // 更新換手狀態
      this.handoverState.phase = phase
      this.handoverState.progress = progress
      this.handoverState.isHandover = phase !== 'monitoring' && phase !== 'monitoring_resume'

      // 創建動畫事件
      const animationEvent: AnimationEvent = {
        type: 'phase_change',
        data: {
          phase,
          progress,
          phaseInfo: this.phases[phaseIndex]
        },
        timestamp: Date.now()
      }

      this.addAnimationEvent(animationEvent)
      this.emit('phase_change', { phase, progress, phaseInfo: this.phases[phaseIndex] })
      this.emit('handover_state_change', this.handoverState)
    }
  }

  /**
   * 候選衛星更新
   */
  public updateCandidates(candidates: CandidateInfo[]) {
    this.candidateInfo = candidates.map((candidate, index) => ({
      ...candidate,
      rank: index + 1
    }))

    const animationEvent: AnimationEvent = {
      type: 'candidate_highlight',
      data: {
        candidates: this.candidateInfo,
        highlightDuration: 2000
      },
      timestamp: Date.now()
    }

    this.addAnimationEvent(animationEvent)
    this.emit('candidate_update', this.candidateInfo)
  }

  /**
   * 算法切換
   */
  public switchAlgorithm(algorithm: string) {
    const previousAlgorithm = this.currentAlgorithm
    this.currentAlgorithm = algorithm

    const animationEvent: AnimationEvent = {
      type: 'decision_made',
      data: {
        algorithm,
        previousAlgorithm,
        switchTime: Date.now()
      },
      timestamp: Date.now()
    }

    this.addAnimationEvent(animationEvent)
    this.emit('algorithm_switch', { algorithm, previousAlgorithm })
  }

  /**
   * 換手狀態更新
   */
  public updateHandoverState(state: Partial<HandoverState>) {
    this.handoverState = { ...this.handoverState, ...state }
    this.emit('handover_state_change', this.handoverState)
  }

  /**
   * 添加動畫事件到隊列
   */
  private addAnimationEvent(event: AnimationEvent) {
    this.animationQueue.push(event)
    this.processAnimationQueue()
  }

  /**
   * 處理動畫隊列
   */
  private processAnimationQueue() {
    if (this.animationQueue.length === 0) return

    const event = this.animationQueue.shift()!
    this.executeAnimation(event)
  }

  /**
   * 執行動畫
   */
  private executeAnimation(event: AnimationEvent) {
    console.log('📽️ 執行動畫事件:', event.type, event.data)
    
    switch (event.type) {
      case 'phase_change':
        this.executePhaseChangeAnimation(event.data)
        break
      case 'candidate_highlight':
        this.executeCandidateHighlightAnimation(event.data)
        break
      case 'decision_made':
        this.executeDecisionMadeAnimation(event.data)
        break
      case 'handover_execute':
        this.executeHandoverAnimation(event.data)
        break
    }
  }

  /**
   * 執行階段變更動畫
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private executePhaseChangeAnimation(data: any) {
    // 這裡會與 3D 場景協調，更新視覺效果
    console.log('🎭 階段變更動畫:', data.phase, data.progress)
  }

  /**
   * 執行候選衛星高亮動畫
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private executeCandidateHighlightAnimation(data: any) {
    // 這裡會在 3D 場景中高亮候選衛星
    console.log('🎯 候選衛星高亮動畫:', data.candidates.length, '個候選')
  }

  /**
   * 執行決策動畫
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private executeDecisionMadeAnimation(data: any) {
    // 這裡會顯示決策過程動畫
    console.log('🧠 決策動畫:', data.algorithm)
  }

  /**
   * 執行換手動畫
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private executeHandoverAnimation(data: any) {
    // 這裡會執行完整的換手動畫序列
    console.log('🔄 換手動畫:', data)
  }

  /**
   * 獲取當前階段信息
   */
  public getCurrentPhase(): DecisionPhase {
    return this.phases[this.currentPhaseIndex]
  }

  /**
   * 獲取所有階段信息
   */
  public getAllPhases(): DecisionPhase[] {
    return [...this.phases]
  }

  /**
   * 獲取當前換手狀態
   */
  public getHandoverState(): HandoverState {
    return { ...this.handoverState }
  }

  /**
   * 獲取候選衛星信息
   */
  public getCandidateInfo(): CandidateInfo[] {
    return [...this.candidateInfo]
  }

  /**
   * 獲取當前算法
   */
  public getCurrentAlgorithm(): string {
    return this.currentAlgorithm
  }

  /**
   * 重置協調器狀態
   */
  public reset() {
    this.currentPhaseIndex = 0
    this.phases.forEach((phase, index) => {
      phase.status = index === 0 ? 'active' : 'pending'
    })
    this.animationQueue = []
    this.handoverState = {
      isHandover: false,
      progress: 0,
      phase: 'monitoring'
    }
    this.candidateInfo = []
  }

  /**
   * 開始新的決策流程
   */
  public startNewDecisionFlow() {
    this.reset()
    this.notifyPhaseChange('trigger_detection', 0)
  }

  /**
   * 銷毀協調器
   */
  public destroy() {
    this.eventListeners.clear()
    this.animationQueue = []
  }
}

export default VisualizationCoordinator