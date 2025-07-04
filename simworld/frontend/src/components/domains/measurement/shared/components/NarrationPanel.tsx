/**
 * NarrationPanel 組件
 * 抽取自各事件 Viewer 的解說面板邏輯
 * 提供統一的拖拽、透明度控制、最小化等功能
 */

import React, { useRef, useCallback, useEffect, useState } from 'react'
import type { NarrationPanelProps } from '../types'

const NarrationPanel: React.FC<NarrationPanelProps> = ({
  isVisible,
  isMinimized,
  showTechnicalDetails,
  content,
  position,
  opacity,
  onToggleVisibility,
  onToggleMinimized,
  onToggleTechnicalDetails,
  onPositionChange,
  onOpacityChange,
  className = ''
}) => {
  // 拖拽狀態和引用
  const [isDragging, setIsDragging] = useState(false)
  const narrationPanelRef = useRef<HTMLDivElement>(null)
  const dragState = useRef({
    isDragging: false,
    offsetX: 0,
    offsetY: 0,
    currentX: position.x,
    currentY: position.y,
  })
  const animationFrameId = useRef<number | null>(null)
  const latestMouseEvent = useRef({ x: 0, y: 0 })

  // 初始化拖拽狀態位置
  useEffect(() => {
    dragState.current.currentX = position.x
    dragState.current.currentY = position.y
  }, [position.x, position.y])

  // 核心拖拽更新函數，使用 requestAnimationFrame 確保流暢
  const updatePosition = useCallback(() => {
    if (!dragState.current.isDragging) {
      animationFrameId.current = null
      return
    }

    const { x, y } = latestMouseEvent.current
    const newX = x - dragState.current.offsetX
    const newY = y - dragState.current.offsetY

    // 限制在螢幕範圍內
    const panelWidth = narrationPanelRef.current?.offsetWidth || 420
    const panelHeight = narrationPanelRef.current?.offsetHeight || 400
    const maxX = Math.max(0, window.innerWidth - panelWidth)
    const maxY = Math.max(0, window.innerHeight - panelHeight)

    const finalX = Math.max(0, Math.min(newX, maxX))
    const finalY = Math.max(0, Math.min(newY, maxY))

    dragState.current.currentX = finalX
    dragState.current.currentY = finalY

    // 直接更新 DOM 避免 React 重新渲染延遲
    if (narrationPanelRef.current) {
      narrationPanelRef.current.style.transform = `translate(${finalX}px, ${finalY}px)`
    }

    // 繼續動畫幀
    animationFrameId.current = requestAnimationFrame(updatePosition)
  }, [])

  // 鼠標移動處理
  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      latestMouseEvent.current = { x: e.clientX, y: e.clientY }
      
      if (!animationFrameId.current) {
        animationFrameId.current = requestAnimationFrame(updatePosition)
      }
    },
    [updatePosition]
  )

  // 鼠標釋放處理
  const handleMouseUp = useCallback(() => {
    dragState.current.isDragging = false
    setIsDragging(false)

    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)

    // 取消任何等待中的動畫幀
    if (animationFrameId.current) {
      cancelAnimationFrame(animationFrameId.current)
      animationFrameId.current = null
    }

    // 最終同步到父組件狀態
    onPositionChange({
      x: dragState.current.currentX,
      y: dragState.current.currentY,
    })
  }, [handleMouseMove, onPositionChange])

  // 拖拽開始處理
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // 忽略控制按鈕區域的點擊
      if (
        e.target instanceof HTMLElement &&
        (e.target.closest('.narration-controls') ||
          e.target.closest('.opacity-control') ||
          e.target.closest('button') ||
          e.target.closest('input') ||
          e.target.closest('.narration-close-btn'))
      ) {
        return
      }

      e.preventDefault()
      e.stopPropagation()

      dragState.current.isDragging = true
      dragState.current.offsetX = e.clientX - dragState.current.currentX
      dragState.current.offsetY = e.clientY - dragState.current.currentY
      setIsDragging(true)

      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    },
    [handleMouseMove, handleMouseUp]
  )

  // 透明度變更處理
  const handleOpacityChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newOpacity = parseFloat(e.target.value)
    onOpacityChange(newOpacity)
  }, [onOpacityChange])

  // 組件卸載時清理
  useEffect(() => {
    return () => {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current)
      }
    }
  }, [])

  // 如果不可見，不渲染
  if (!isVisible) {
    return null
  }

  return (
    <div
      ref={narrationPanelRef}
      className={`narration-panel floating ${isMinimized ? 'minimized' : ''} ${className}`}
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
        transform: `translate(${position.x}px, ${position.y}px)`,
        opacity: opacity,
        zIndex: 9999,
        cursor: isDragging ? 'grabbing' : 'grab',
      }}
      onMouseDown={handleMouseDown}
    >
      {/* 面板標題區 */}
      <div className="narration-header">
        <h3 className="narration-title">
          {typeof content === 'string' ? '解說' : content}
        </h3>
        
        <div className="narration-controls">
          {/* 透明度控制 */}
          <div className="opacity-control">
            <input
              type="range"
              min="0.3"
              max="1"
              step="0.1"
              value={opacity}
              onChange={handleOpacityChange}
              className="opacity-slider"
              title="調整透明度"
            />
          </div>

          {/* 技術細節切換按鈕 */}
          <button
            className={`narration-technical-toggle ${showTechnicalDetails ? 'active' : ''}`}
            onClick={onToggleTechnicalDetails}
            title={showTechnicalDetails ? '隱藏技術細節' : '顯示技術細節'}
          >
            🔧
          </button>

          {/* 最小化/展開按鈕 */}
          <button
            className="narration-minimize-btn"
            onClick={onToggleMinimized}
            title={isMinimized ? '展開' : '最小化'}
          >
            {isMinimized ? '📖' : '📘'}
          </button>

          {/* 關閉按鈕 */}
          <button
            className="narration-close-btn"
            onClick={onToggleVisibility}
            title="關閉解說面板"
          >
            ✕
          </button>
        </div>
      </div>

      {/* 面板內容區 */}
      {!isMinimized && (
        <div className="narration-content">
          {typeof content === 'string' ? (
            <div 
              className="narration-text"
              dangerouslySetInnerHTML={{ __html: content }}
            />
          ) : (
            <div className="narration-text">{content}</div>
          )}
        </div>
      )}

      {/* 拖拽提示 */}
      {!isMinimized && (
        <div className="narration-footer">
          <small className="drag-hint">
            💡 拖拽面板移動位置 | 💻 技術細節切換 | 🎚️ 透明度調整
          </small>
        </div>
      )}
    </div>
  )
}

export default NarrationPanel