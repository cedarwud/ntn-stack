/**
 * 功能切換區塊組件
 * 顯示按類別分組的功能開關
 */

import React, { useState } from 'react'
import { FeatureToggle, Category } from '../types'

interface FeatureToggleSectionProps {
  features: FeatureToggle[]
  categories: Category[]
  activeCategory: string
  onCategoryChange: (categoryId: string) => void
  searchQuery?: string
  onSearchChange?: (query: string) => void
}

const FeatureToggleSection: React.FC<FeatureToggleSectionProps> = ({
  features,
  categories,
  activeCategory,
  onCategoryChange,
  searchQuery = '',
  onSearchChange,
}) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set([activeCategory])
  )

  // 過濾功能（根據搜尋查詢）
  const filteredFeatures = features.filter(feature => {
    if (!searchQuery.trim()) return true
    
    const query = searchQuery.toLowerCase()
    return (
      feature.label.toLowerCase().includes(query) ||
      feature.description.toLowerCase().includes(query) ||
      feature.id.toLowerCase().includes(query)
    )
  })

  // 按類別分組功能
  const featuresByCategory = categories.reduce((acc, category) => {
    acc[category.id] = filteredFeatures.filter(feature => feature.category === category.id)
    return acc
  }, {} as Record<string, FeatureToggle[]>)

  // 切換類別展開狀態
  const toggleCategoryExpansion = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId)
    } else {
      newExpanded.add(categoryId)
    }
    setExpandedCategories(newExpanded)
  }

  // 渲染功能開關
  const renderFeatureToggle = (feature: FeatureToggle) => {
    const isDisabled = feature.dependency && !features.find(f => 
      f.id === feature.dependency && f.enabled
    )

    return (
      <div
        key={feature.id}
        className={`feature-toggle-item ${feature.enabled ? 'enabled' : 'disabled'} ${
          isDisabled ? 'dependency-disabled' : ''
        }`}
      >
        <div className="feature-toggle-header">
          <div className="feature-info">
            <span className="feature-icon">{feature.icon}</span>
            <div className="feature-text">
              <span className="feature-label">{feature.label}</span>
              <span className="feature-description">{feature.description}</span>
            </div>
          </div>
          
          <label className="feature-switch">
            <input
              type="checkbox"
              checked={feature.enabled || false}
              disabled={isDisabled}
              onChange={(e) => feature.onToggle(e.target.checked)}
            />
            <span className="switch-slider"></span>
          </label>
        </div>

        {feature.dependency && (
          <div className="feature-dependency">
            <span className="dependency-text">
              需要先啟用: {features.find(f => f.id === feature.dependency)?.label}
            </span>
          </div>
        )}
      </div>
    )
  }

  // 渲染類別區塊
  const renderCategory = (category: Category) => {
    const categoryFeatures = featuresByCategory[category.id]
    const isExpanded = expandedCategories.has(category.id)
    const enabledCount = categoryFeatures.filter(f => f.enabled).length
    const totalCount = categoryFeatures.length

    if (categoryFeatures.length === 0 && searchQuery) {
      return null // 搜尋時隱藏空類別
    }

    return (
      <div key={category.id} className="feature-category">
        <div
          className={`category-header ${isExpanded ? 'expanded' : 'collapsed'}`}
          onClick={() => toggleCategoryExpansion(category.id)}
        >
          <div className="category-info">
            <span className="category-icon">{category.icon}</span>
            <span className="category-label">{category.label}</span>
            <span className="category-count">
              {enabledCount}/{totalCount}
            </span>
          </div>
          <span className="expand-icon">
            {isExpanded ? '▼' : '▶'}
          </span>
        </div>

        {isExpanded && (
          <div className="category-content">
            {categoryFeatures.length > 0 ? (
              categoryFeatures.map(renderFeatureToggle)
            ) : (
              <div className="no-features">
                此類別暫無功能
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="feature-toggle-section">
      {/* 搜尋框 */}
      {onSearchChange && (
        <div className="search-box">
          <input
            type="text"
            placeholder="搜尋功能..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="search-input"
          />
          <span className="search-icon">🔍</span>
        </div>
      )}

      {/* 統計信息 */}
      <div className="features-stats">
        <span className="stats-text">
          已啟用: {filteredFeatures.filter(f => f.enabled).length}/{filteredFeatures.length}
        </span>
      </div>

      {/* 類別列表 */}
      <div className="categories-list">
        {categories.map(renderCategory)}
      </div>

      {/* 搜尋無結果 */}
      {searchQuery && filteredFeatures.length === 0 && (
        <div className="no-search-results">
          <span className="no-results-icon">🔍</span>
          <span className="no-results-text">找不到符合條件的功能</span>
        </div>
      )}
    </div>
  )
}

export default FeatureToggleSection