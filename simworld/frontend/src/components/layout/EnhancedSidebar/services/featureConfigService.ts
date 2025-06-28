/**
 * 功能配置服務
 * 管理所有功能切換開關的配置
 */

import { FeatureToggle, Category, EnhancedSidebarProps } from '../types'

export class FeatureConfigService {
  /**
   * 獲取所有功能切換開關配置
   */
  static getFeatureToggles(props: EnhancedSidebarProps): FeatureToggle[] {
    const {
      auto,
      uavAnimation,
      onUavAnimationChange,
      satelliteEnabled,
      satelliteUavConnectionEnabled,
      sinrHeatmapEnabled,
      onSinrHeatmapChange,
      interferenceVisualizationEnabled,
      onInterferenceVisualizationChange,
      manualControlEnabled,
      onManualControlEnabledChange,
    } = props

    const featureToggles: FeatureToggle[] = [
      // UAV 控制 (3個基礎)
      {
        id: 'autoFlight',
        label: '自動飛行模式',
        category: 'uav',
        enabled: auto,
        onToggle: props.onAutoChange,
        icon: '✈️',
        description: 'UAV 自動飛行路徑模式',
      },
      {
        id: 'uavAnimation',
        label: 'UAV 動畫效果',
        category: 'uav',
        enabled: uavAnimation,
        onToggle: onUavAnimationChange,
        icon: '🎬',
        description: 'UAV 飛行動畫效果',
      },

      // 衛星控制
      {
        id: 'satelliteEnabled',
        label: '衛星星座顯示',
        category: 'satellite',
        enabled: satelliteEnabled,
        onToggle: this.createSafeToggle(props.onSatelliteEnabledChange),
        icon: '🛰️',
        description: 'LEO 衛星星座顯示',
      },
      {
        id: 'satelliteUAVConnection',
        label: '衛星-UAV 連接',
        category: 'satellite',
        enabled: satelliteUavConnectionEnabled && satelliteEnabled,
        onToggle: this.createSafeToggle(props.onSatelliteUavConnectionChange),
        icon: '🔗',
        description: '衛星與 UAV 連接狀態監控（需先開啟衛星顯示）',
        dependency: 'satelliteEnabled',
      },

      // 通信品質
      {
        id: 'sinrHeatmap',
        label: 'SINR 熱力圖',
        category: 'quality',
        enabled: sinrHeatmapEnabled,
        onToggle: this.createSafeToggle(onSinrHeatmapChange),
        icon: '🔥',
        description: '地面 SINR 信號強度熱力圖',
      },
      {
        id: 'interferenceVisualization',
        label: '干擾源可視化',
        category: 'quality',
        enabled: interferenceVisualizationEnabled,
        onToggle: this.createSafeToggle(onInterferenceVisualizationChange),
        icon: '📡',
        description: '3D 干擾源範圍和影響可視化',
      },
    ]

    // 動態添加手動控制開關（當自動飛行關閉時）
    if (!auto) {
      featureToggles.splice(2, 0, {
        id: 'manualControl',
        label: '手動控制面板',
        category: 'uav',
        enabled: manualControlEnabled,
        onToggle: this.createSafeToggle(onManualControlEnabledChange),
        icon: '🕹️',
        description: '顯示 UAV 手動控制面板',
      })
    }

    return featureToggles
  }

  /**
   * 獲取類別配置
   */
  static getCategories(): Category[] {
    return [
      { id: 'uav', label: 'UAV 控制', icon: '🚁' },
      { id: 'satellite', label: '衛星控制', icon: '🛰️' },
      { id: 'handover_mgr', label: '換手管理', icon: '🔄' },
      { id: 'quality', label: '通信品質', icon: '📶' },
    ]
  }

  /**
   * 根據類別過濾功能
   */
  static getFeaturesByCategory(features: FeatureToggle[], categoryId: string): FeatureToggle[] {
    return features.filter(feature => feature.category === categoryId)
  }

  /**
   * 檢查功能依賴關係
   */
  static checkDependency(feature: FeatureToggle, allFeatures: FeatureToggle[]): boolean {
    if (!feature.dependency) {
      return true
    }

    const dependentFeature = allFeatures.find(f => f.id === feature.dependency)
    return dependentFeature ? !!dependentFeature.enabled : false
  }

  /**
   * 創建安全的切換函數
   */
  private static createSafeToggle(handler?: (enabled: boolean) => void): (enabled: boolean) => void {
    return handler || (() => {})
  }

  /**
   * 獲取功能統計
   */
  static getFeatureStats(features: FeatureToggle[]): {
    total: number
    enabled: number
    byCategory: Record<string, { total: number; enabled: number }>
  } {
    const byCategory: Record<string, { total: number; enabled: number }> = {}
    let totalEnabled = 0

    features.forEach(feature => {
      if (!byCategory[feature.category]) {
        byCategory[feature.category] = { total: 0, enabled: 0 }
      }
      
      byCategory[feature.category].total++
      
      if (feature.enabled) {
        totalEnabled++
        byCategory[feature.category].enabled++
      }
    })

    return {
      total: features.length,
      enabled: totalEnabled,
      byCategory,
    }
  }

  /**
   * 搜尋功能
   */
  static searchFeatures(features: FeatureToggle[], query: string): FeatureToggle[] {
    if (!query.trim()) {
      return features
    }

    const lowerQuery = query.toLowerCase()
    return features.filter(feature => 
      feature.label.toLowerCase().includes(lowerQuery) ||
      feature.description.toLowerCase().includes(lowerQuery) ||
      feature.id.toLowerCase().includes(lowerQuery)
    )
  }
}