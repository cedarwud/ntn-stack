/**
 * 統一的換手決策引擎
 * 用於消除組件間的邏輯重複和矛盾
 */

import { VisibleSatelliteInfo } from '../../../types/satellite'
import { HANDOVER_CONFIG } from '../config/handoverConfig'

export interface HandoverDecision {
  needsHandover: boolean
  targetSatellite: VisibleSatelliteInfo | null
  reason: string
  confidence: number
}

export interface SatelliteQuality {
  elevation: number
  signalStrength: number
  quality: 'excellent' | 'good' | 'fair' | 'poor'
  score: number
}

/**
 * 統一的換手決策引擎
 */
export class HandoverDecisionEngine {
  /**
   * 主要換手決策函數
   */
  static shouldHandover(
    currentSatellite: VisibleSatelliteInfo,
    availableSatellites: VisibleSatelliteInfo[],
    currentTime: number = Date.now(),
    handoverHistory: Array<{ from: string; to: string; timestamp: number }> = [],
    cooldownPeriod: number = HANDOVER_CONFIG.HANDOVER_HISTORY.DEMO_COOLDOWN_MS
  ): HandoverDecision {
    
    const currentQuality = this.calculateSatelliteQuality(currentSatellite)
    
    // 檢查是否需要換手
    const handoverReasons = this.analyzeHandoverNeeds(currentSatellite, currentTime)
    
    if (handoverReasons.length === 0) {
      return {
        needsHandover: false,
        targetSatellite: currentSatellite,
        reason: '當前衛星服務品質良好',
        confidence: 0.95
      }
    }
    
    // 需要換手，選擇最佳候選衛星
    const candidates = this.filterCandidateSatellites(
      currentSatellite, 
      availableSatellites, 
      handoverHistory, 
      currentTime, 
      cooldownPeriod
    )
    
    if (candidates.length === 0) {
      return {
        needsHandover: false,
        targetSatellite: currentSatellite,
        reason: '無可用的換手候選衛星',
        confidence: 0.8
      }
    }
    
    // 選擇最佳候選衛星
    const bestCandidate = this.selectBestCandidate(candidates, currentQuality)
    
    return {
      needsHandover: true,
      targetSatellite: bestCandidate,
      reason: handoverReasons.join(', '),
      confidence: 0.9
    }
  }

  /**
   * 分析換手需求
   */
  private static analyzeHandoverNeeds(
    satellite: VisibleSatelliteInfo, 
    currentTime: number
  ): string[] {
    const reasons: string[] = []
    const quality = this.calculateSatelliteQuality(satellite)
    
    // 條件1：仰角過低
    if (quality.elevation < HANDOVER_CONFIG.HANDOVER_THRESHOLDS.MIN_ELEVATION_DEGREES) {
      reasons.push(`仰角過低(${quality.elevation.toFixed(1)}°)`)
    }
    
    // 條件2：信號強度基於時間的變化
    const timeBasedSignalDrop = Math.sin(
      currentTime / HANDOVER_CONFIG.HANDOVER_THRESHOLDS.TIME_BASED_CYCLE_MS
    ) < HANDOVER_CONFIG.HANDOVER_THRESHOLDS.SIGNAL_DROP_THRESHOLD
    
    if (timeBasedSignalDrop) {
      reasons.push('信號強度週期性下降')
    }
    
    // 條件3：軌道位置判斷
    const orbitalPosition = (currentTime / 1000) % 360
    const { ORBITAL_POSITION_THRESHOLD } = HANDOVER_CONFIG.HANDOVER_THRESHOLDS
    const isLeavingView = (
      orbitalPosition > ORBITAL_POSITION_THRESHOLD.LEAVE_START || 
      orbitalPosition < ORBITAL_POSITION_THRESHOLD.LEAVE_END
    ) && quality.elevation < ORBITAL_POSITION_THRESHOLD.MIN_ELEVATION_FOR_ORBITAL
    
    if (isLeavingView) {
      reasons.push(`即將離開視野(軌道位置${orbitalPosition.toFixed(1)}°)`)
    }
    
    return reasons
  }

  /**
   * 計算衛星服務品質
   */
  static calculateSatelliteQuality(satellite: VisibleSatelliteInfo): SatelliteQuality {
    const elevation = satellite.elevation_deg || 0
    
    // 基於仰角估算信號強度
    const signalStrength = this.estimateSignalStrength(elevation)
    
    // 計算綜合品質等級
    const quality = this.getQualityLevel(signalStrength)
    
    // 計算綜合分數 (0-100)
    const score = this.calculateQualityScore(elevation, signalStrength)
    
    return {
      elevation,
      signalStrength,
      quality,
      score
    }
  }

  /**
   * 基於仰角估算信號強度
   */
  private static estimateSignalStrength(elevation: number): number {
    // 仰角越高，信號越強
    const { SIGNAL_RANGE } = HANDOVER_CONFIG.SIGNAL_QUALITY
    const normalizedElevation = Math.max(0, Math.min(90, elevation)) / 90
    
    // 使用平方根函數模擬真實的信號強度變化
    const signalFactor = Math.sqrt(normalizedElevation)
    return SIGNAL_RANGE.MIN + signalFactor * (SIGNAL_RANGE.MAX - SIGNAL_RANGE.MIN)
  }

  /**
   * 獲取信號品質等級
   */
  private static getQualityLevel(signalStrength: number): 'excellent' | 'good' | 'fair' | 'poor' {
    const { SIGNAL_QUALITY } = HANDOVER_CONFIG
    
    if (signalStrength >= SIGNAL_QUALITY.EXCELLENT_THRESHOLD_DBM) return 'excellent'
    if (signalStrength >= SIGNAL_QUALITY.GOOD_THRESHOLD_DBM) return 'good'
    if (signalStrength >= SIGNAL_QUALITY.FAIR_THRESHOLD_DBM) return 'fair'
    return 'poor'
  }

  /**
   * 計算綜合品質分數
   */
  private static calculateQualityScore(elevation: number, signalStrength: number): number {
    const elevationScore = Math.max(0, Math.min(100, elevation * 100 / 90))
    const { SIGNAL_RANGE } = HANDOVER_CONFIG.SIGNAL_QUALITY
    const signalScore = Math.max(0, Math.min(100, 
      (signalStrength - SIGNAL_RANGE.MIN) / (SIGNAL_RANGE.MAX - SIGNAL_RANGE.MIN) * 100
    ))
    
    // 加權平均：仰角佔60%，信號強度佔40%
    return elevationScore * 0.6 + signalScore * 0.4
  }

  /**
   * 過濾候選衛星
   */
  private static filterCandidateSatellites(
    currentSatellite: VisibleSatelliteInfo,
    availableSatellites: VisibleSatelliteInfo[],
    handoverHistory: Array<{ from: string; to: string; timestamp: number }>,
    currentTime: number,
    cooldownPeriod: number
  ): VisibleSatelliteInfo[] {
    
    // 排除當前衛星
    let candidates = availableSatellites.filter(
      sat => sat.norad_id !== currentSatellite.norad_id
    )
    
    // 排除最近有換手記錄的衛星
    const recentPartners = new Set<string>()
    const currentSatId = currentSatellite.norad_id.toString()
    
    handoverHistory
      .filter(record => currentTime - record.timestamp < cooldownPeriod)
      .forEach(record => {
        if (record.from === currentSatId) {
          recentPartners.add(record.to)
        } else if (record.to === currentSatId) {
          recentPartners.add(record.from)
        }
      })
    
    // 優先選擇沒有最近換手記錄的衛星
    const preferredCandidates = candidates.filter(
      sat => !recentPartners.has(sat.norad_id.toString())
    )
    
    return preferredCandidates.length > 0 ? preferredCandidates : candidates
  }

  /**
   * 選擇最佳候選衛星
   */
  private static selectBestCandidate(
    candidates: VisibleSatelliteInfo[],
    _currentQuality: SatelliteQuality
  ): VisibleSatelliteInfo {
    
    // 計算所有候選衛星的品質
    const candidateQualities = candidates.map(sat => ({
      satellite: sat,
      quality: this.calculateSatelliteQuality(sat)
    }))
    
    // 按品質分數排序，選擇最佳的
    candidateQualities.sort((a, b) => b.quality.score - a.quality.score)
    
    // 額外考慮相鄰衛星的偏好（符合軌道換手邏輯）
    const adjacentBonus = this.calculateAdjacencyBonus(candidateQualities)
    
    // 結合品質分數和相鄰偏好
    const finalScores = candidateQualities.map((item, index) => ({
      ...item,
      finalScore: item.quality.score + adjacentBonus[index]
    }))
    
    finalScores.sort((a, b) => b.finalScore - a.finalScore)
    
    return finalScores[0].satellite
  }

  /**
   * 計算相鄰性偏好加分
   */
  private static calculateAdjacencyBonus(
    candidateQualities: Array<{ satellite: VisibleSatelliteInfo; quality: SatelliteQuality }>
  ): number[] {
    // 簡化的相鄰性計算：基於 NORAD ID 的接近程度
    return candidateQualities.map((_, index) => {
      // 如果是前幾個候選衛星，給予額外分數
      if (index < 3) {
        return 5 * (3 - index) // 前3個分別給15, 10, 5分
      }
      return 0
    })
  }

  /**
   * 生成動態衛星名稱（用於Binary Search迭代）
   */
  static generateDynamicSatelliteName(timestamp: number, iterationCount: number): string {
    const timeHash = Math.floor(timestamp / 10000) % 1000
    const satelliteBase = HANDOVER_CONFIG.SATELLITE_SELECTION.SATELLITE_ID_RANGE.BASE + 
                         (timeHash + iterationCount) % HANDOVER_CONFIG.SATELLITE_SELECTION.SATELLITE_ID_RANGE.RANGE
    return `STARLINK-${satelliteBase.toString().padStart(4, '0')}`
  }

  /**
   * 格式化衛星信息用於顯示
   */
  static formatSatelliteInfo(satellite: VisibleSatelliteInfo) {
    return {
      id: satellite.norad_id.toString(),
      name: satellite.name.replace(' [DTC]', '').replace('[DTC]', ''),
      elevation: satellite.elevation_deg || 0,
      quality: this.calculateSatelliteQuality(satellite)
    }
  }
}