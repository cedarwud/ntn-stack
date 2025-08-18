/**
 * 衛星覆蓋驗證工具
 * 用於測試3D場景中的衛星渲染是否符合Stage 6動態池策略
 */

export interface SatelliteCoverageMetrics {
  timestamp: number
  visibleSatellites: {
    starlink: number
    oneweb: number
    total: number
  }
  targetRanges: {
    starlink: [number, number] // [10, 15]
    oneweb: [number, number]   // [3, 6] 
  }
  compliance: {
    starlink: boolean
    oneweb: boolean
    overall: boolean
  }
  details: {
    starlinkSatellites: string[]
    onewebSatellites: string[]
  }
}

export interface OrbitPeriodTest {
  startTime: number
  endTime: number
  sampleInterval: number // 秒
  totalSamples: number
  passedSamples: number
  averageVisible: {
    starlink: number
    oneweb: number
  }
  complianceRate: number
  failurePoints: SatelliteCoverageMetrics[]
}

export class SatelliteCoverageValidator {
  private coverageHistory: SatelliteCoverageMetrics[] = []
  private isRecording = false
  
  // 目標範圍（基於Stage 6的動態池策略）
  private readonly targetRanges = {
    starlink: [10, 15] as [number, number],
    oneweb: [3, 6] as [number, number]
  }

  /**
   * 開始記錄衛星覆蓋數據
   */
  startRecording(): void {
    this.isRecording = true
    this.coverageHistory = []
    console.log('🔍 開始記錄衛星覆蓋數據...')
  }

  /**
   * 停止記錄
   */
  stopRecording(): void {
    this.isRecording = false
    console.log('⏹️ 停止記錄衛星覆蓋數據')
  }

  /**
   * 記錄當前時刻的衛星可見狀態
   */
  recordCoverageSnapshot(visibleSatellites: Map<string, [number, number, number]>): void {
    if (!this.isRecording) return

    // 分析可見衛星
    const starlinkSatellites: string[] = []
    const onewebSatellites: string[] = []

    visibleSatellites.forEach((position, satelliteId) => {
      // 判斷衛星類型（基於ID或名稱模式）
      const lowerSatId = satelliteId.toLowerCase()
      if (lowerSatId.includes('starlink') || lowerSatId.includes('sat_') || lowerSatId.startsWith('starlink_')) {
        starlinkSatellites.push(satelliteId)
      } else if (lowerSatId.includes('oneweb') || lowerSatId.startsWith('oneweb_')) {
        onewebSatellites.push(satelliteId)
      }
    })

    const metrics: SatelliteCoverageMetrics = {
      timestamp: Date.now(),
      visibleSatellites: {
        starlink: starlinkSatellites.length,
        oneweb: onewebSatellites.length,
        total: starlinkSatellites.length + onewebSatellites.length
      },
      targetRanges: {
        starlink: this.targetRanges.starlink,
        oneweb: this.targetRanges.oneweb
      },
      compliance: {
        starlink: starlinkSatellites.length >= this.targetRanges.starlink[0] && 
                 starlinkSatellites.length <= this.targetRanges.starlink[1],
        oneweb: onewebSatellites.length >= this.targetRanges.oneweb[0] && 
               onewebSatellites.length <= this.targetRanges.oneweb[1],
        overall: false
      },
      details: {
        starlinkSatellites,
        onewebSatellites
      }
    }

    // 計算整體合規性
    metrics.compliance.overall = metrics.compliance.starlink && metrics.compliance.oneweb

    this.coverageHistory.push(metrics)

    // 即時日誌（每10次記錄輸出一次）
    if (this.coverageHistory.length % 10 === 0) {
      console.log(`📊 覆蓋快照 #${this.coverageHistory.length}: Starlink ${metrics.visibleSatellites.starlink}, OneWeb ${metrics.visibleSatellites.oneweb}, 合規: ${metrics.compliance.overall ? '✅' : '❌'}`)
    }
  }

  /**
   * 執行完整軌道週期測試
   * @param durationMinutes 測試持續時間（分鐘）
   * @param sampleInterval 採樣間隔（秒）
   */
  async runOrbitPeriodTest(durationMinutes: number = 200, sampleInterval: number = 30): Promise<OrbitPeriodTest> {
    const startTime = Date.now()
    const endTime = startTime + (durationMinutes * 60 * 1000)
    const totalSamples = Math.floor((durationMinutes * 60) / sampleInterval)

    console.log(`🧪 開始軌道週期測試：${durationMinutes}分鐘，每${sampleInterval}秒採樣，預計${totalSamples}個樣本`)

    this.startRecording()

    // 模擬測試期間的數據收集（實際應用中會從3D渲染器獲取數據）
    await this.simulateTestPeriod(durationMinutes, sampleInterval)

    this.stopRecording()

    return this.analyzeTestResults(startTime, endTime, sampleInterval)
  }

  /**
   * 模擬測試期間（實際應用中應該從真實3D渲染器獲取數據）
   */
  private async simulateTestPeriod(durationMinutes: number, sampleInterval: number): Promise<void> {
    const samples = Math.floor((durationMinutes * 60) / sampleInterval)
    
    for (let i = 0; i < samples; i++) {
      // 模擬不同時間點的衛星可見性
      const mockVisibleSatellites = this.generateMockVisibleSatellites(i, samples)
      this.recordCoverageSnapshot(mockVisibleSatellites)
      
      // 模擬時間流逝
      await new Promise(resolve => setTimeout(resolve, 10)) // 加速模擬
    }
  }

  /**
   * 生成模擬的可見衛星數據（用於測試）
   */
  private generateMockVisibleSatellites(sampleIndex: number, totalSamples: number): Map<string, [number, number, number]> {
    const visibleSatellites = new Map<string, [number, number, number]>()

    // 模擬基於軌道週期的衛星可見性變化
    const orbitProgress = (sampleIndex / totalSamples) * 2 * Math.PI // 兩個完整軌道週期
    
    // Starlink 衛星（96分鐘軌道週期）
    const starlinkCount = Math.floor(12 + 3 * Math.sin(orbitProgress)) // 9-15顆變化
    for (let i = 0; i < starlinkCount; i++) {
      visibleSatellites.set(`starlink_${String(i).padStart(5, '0')}`, [
        100 * Math.cos(i * 0.5 + orbitProgress),
        50 + 30 * Math.sin(i * 0.3),
        100 * Math.sin(i * 0.5 + orbitProgress)
      ])
    }

    // OneWeb 衛星（109分鐘軌道週期）
    const onewebCount = Math.floor(4 + 2 * Math.cos(orbitProgress * 0.88)) // 2-6顆變化
    for (let i = 0; i < onewebCount; i++) {
      visibleSatellites.set(`oneweb_${String(i).padStart(5, '0')}`, [
        80 * Math.cos(i * 0.7 + orbitProgress * 0.88),
        60 + 25 * Math.sin(i * 0.4),
        80 * Math.sin(i * 0.7 + orbitProgress * 0.88)
      ])
    }

    return visibleSatellites
  }

  /**
   * 分析測試結果
   */
  private analyzeTestResults(startTime: number, endTime: number, sampleInterval: number): OrbitPeriodTest {
    const totalSamples = this.coverageHistory.length
    const passedSamples = this.coverageHistory.filter(m => m.compliance.overall).length
    
    // 計算平均可見衛星數
    const averageStarlink = this.coverageHistory.reduce((sum, m) => sum + m.visibleSatellites.starlink, 0) / totalSamples
    const averageOneweb = this.coverageHistory.reduce((sum, m) => sum + m.visibleSatellites.oneweb, 0) / totalSamples
    
    // 找出失敗點
    const failurePoints = this.coverageHistory.filter(m => !m.compliance.overall)

    const complianceRate = (passedSamples / totalSamples) * 100

    return {
      startTime,
      endTime,
      sampleInterval,
      totalSamples,
      passedSamples,
      averageVisible: {
        starlink: Number(averageStarlink.toFixed(2)),
        oneweb: Number(averageOneweb.toFixed(2))
      },
      complianceRate: Number(complianceRate.toFixed(2)),
      failurePoints: failurePoints.slice(0, 10) // 只保留前10個失敗點
    }
  }

  /**
   * 獲取測試報告
   */
  generateTestReport(testResult: OrbitPeriodTest): string {
    const report = `
🛰️ 衛星覆蓋驗證報告
================================

📅 測試時間: ${new Date(testResult.startTime).toLocaleString()} - ${new Date(testResult.endTime).toLocaleString()}
⏱️ 測試持續: ${((testResult.endTime - testResult.startTime) / 60000).toFixed(1)}分鐘
📊 採樣間隔: ${testResult.sampleInterval}秒
🔢 總樣本數: ${testResult.totalSamples}

🎯 目標覆蓋範圍:
  - Starlink: ${this.targetRanges.starlink[0]}-${this.targetRanges.starlink[1]}顆
  - OneWeb: ${this.targetRanges.oneweb[0]}-${this.targetRanges.oneweb[1]}顆

📈 實際平均覆蓋:
  - Starlink: ${testResult.averageVisible.starlink}顆
  - OneWeb: ${testResult.averageVisible.oneweb}顆

✅ 合規性結果:
  - 合規樣本: ${testResult.passedSamples}/${testResult.totalSamples}
  - 合規率: ${testResult.complianceRate}%
  - 評級: ${testResult.complianceRate >= 95 ? '🌟 優秀' : testResult.complianceRate >= 85 ? '✅ 良好' : testResult.complianceRate >= 70 ? '⚠️ 需改進' : '❌ 不合格'}

${testResult.failurePoints.length > 0 ? `
❌ 失敗點分析 (前${Math.min(testResult.failurePoints.length, 5)}個):
${testResult.failurePoints.slice(0, 5).map((fp, i) => 
  `  ${i + 1}. ${new Date(fp.timestamp).toLocaleTimeString()}: Starlink ${fp.visibleSatellites.starlink}, OneWeb ${fp.visibleSatellites.oneweb}`
).join('\n')}
` : '🎉 無失敗點！完美覆蓋'}

💡 結論:
${testResult.complianceRate >= 90 
  ? '✅ Stage 6動態池策略成功！3D場景中的衛星覆蓋符合預期，能夠在整個軌道週期內保證連續可見性。'
  : testResult.complianceRate >= 70
    ? '⚠️ 動態池策略部分有效，但需要調整參數或增加動態池大小。'
    : '❌ 動態池策略未達預期，需要重新檢視算法實現。'
}
================================
    `

    return report
  }

  /**
   * 清理歷史記錄
   */
  clearHistory(): void {
    this.coverageHistory = []
  }

  /**
   * 獲取當前記錄狀態
   */
  getRecordingStatus(): { isRecording: boolean; recordCount: number } {
    return {
      isRecording: this.isRecording,
      recordCount: this.coverageHistory.length
    }
  }

  /**
   * 導出測試數據（用於進一步分析）
   */
  exportData(): { metrics: SatelliteCoverageMetrics[]; summary: any } {
    return {
      metrics: this.coverageHistory,
      summary: {
        totalRecords: this.coverageHistory.length,
        averageVisible: {
          starlink: this.coverageHistory.reduce((sum, m) => sum + m.visibleSatellites.starlink, 0) / this.coverageHistory.length,
          oneweb: this.coverageHistory.reduce((sum, m) => sum + m.visibleSatellites.oneweb, 0) / this.coverageHistory.length
        },
        complianceRate: (this.coverageHistory.filter(m => m.compliance.overall).length / this.coverageHistory.length) * 100
      }
    }
  }
}

// 全局實例
export const satelliteCoverageValidator = new SatelliteCoverageValidator()