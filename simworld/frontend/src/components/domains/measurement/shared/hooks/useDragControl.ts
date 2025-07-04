/**
 * useDragControl Hook
 * 提供統一的拖拽功能，適用於解說面板和其他可拖拽組件
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import type { DragState, DragHandlers } from '../types'

interface UseDragControlOptions {
  initialPosition: { x: number; y: number }
  boundaryConstraint?: boolean // 是否限制在視窗範圍內
  onPositionChange?: (position: { x: number; y: number }) => void
  elementRef?: React.RefObject<HTMLElement> // 用於計算邊界的元素引用
}

interface UseDragControlResult {
  position: { x: number; y: number }
  isDragging: boolean
  dragHandlers: DragHandlers
  setPosition: (position: { x: number; y: number }) => void
}

export const useDragControl = ({
  initialPosition,
  boundaryConstraint = true,
  onPositionChange,
  elementRef
}: UseDragControlOptions): UseDragControlResult => {
  
  // 位置狀態
  const [position, setPositionState] = useState(initialPosition)
  const [isDragging, setIsDragging] = useState(false)

  // 拖拽狀態引用
  const dragState = useRef<DragState>({
    isDragging: false,
    dragOffset: { x: 0, y: 0 },
    lastPosition: initialPosition
  })

  // 動畫幀引用
  const animationFrameId = useRef<number | null>(null)
  const latestMouseEvent = useRef({ x: 0, y: 0 })

  // 更新位置
  const setPosition = useCallback((newPosition: { x: number; y: number }) => {
    setPositionState(newPosition)
    dragState.current.lastPosition = newPosition
    onPositionChange?.(newPosition)
  }, [onPositionChange])

  // 計算約束後的位置
  const constrainPosition = useCallback((x: number, y: number) => {
    if (!boundaryConstraint) {
      return { x, y }
    }

    // 獲取元素尺寸
    const elementWidth = elementRef?.current?.offsetWidth || 300
    const elementHeight = elementRef?.current?.offsetHeight || 200

    // 計算邊界
    const maxX = Math.max(0, window.innerWidth - elementWidth)
    const maxY = Math.max(0, window.innerHeight - elementHeight)

    return {
      x: Math.max(0, Math.min(x, maxX)),
      y: Math.max(0, Math.min(y, maxY))
    }
  }, [boundaryConstraint, elementRef])

  // 核心位置更新函數
  const updatePosition = useCallback(() => {
    if (!dragState.current.isDragging) {
      animationFrameId.current = null
      return
    }

    const { x, y } = latestMouseEvent.current
    const newX = x - dragState.current.dragOffset.x
    const newY = y - dragState.current.dragOffset.y

    const constrainedPosition = constrainPosition(newX, newY)
    dragState.current.lastPosition = constrainedPosition

    // 如果有元素引用，直接更新 DOM 以獲得更流暢的拖拽體驗
    if (elementRef?.current) {
      elementRef.current.style.transform = 
        `translate(${constrainedPosition.x}px, ${constrainedPosition.y}px)`
    }

    // 繼續動畫幀
    animationFrameId.current = requestAnimationFrame(updatePosition)
  }, [constrainPosition, elementRef])

  // 拖拽開始處理
  const onDragStart = useCallback((event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()

    const rect = event.currentTarget.getBoundingClientRect()
    
    dragState.current = {
      isDragging: true,
      dragOffset: {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
      },
      lastPosition: position
    }

    setIsDragging(true)
  }, [position])

  // 拖拽移動處理
  const onDragMove = useCallback((event: MouseEvent) => {
    latestMouseEvent.current = { x: event.clientX, y: event.clientY }
    
    if (!animationFrameId.current && dragState.current.isDragging) {
      animationFrameId.current = requestAnimationFrame(updatePosition)
    }
  }, [updatePosition])

  // 拖拽結束處理
  const onDragEnd = useCallback(() => {
    dragState.current.isDragging = false
    setIsDragging(false)

    // 取消動畫幀
    if (animationFrameId.current) {
      cancelAnimationFrame(animationFrameId.current)
      animationFrameId.current = null
    }

    // 同步最終位置到狀態
    setPosition(dragState.current.lastPosition)

    // 移除事件監聽器
    document.removeEventListener('mousemove', onDragMove)
    document.removeEventListener('mouseup', onDragEnd)
  }, [onDragMove, setPosition])

  // 設置拖拽事件監聽器
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', onDragMove)
      document.addEventListener('mouseup', onDragEnd)
    }

    return () => {
      document.removeEventListener('mousemove', onDragMove)
      document.removeEventListener('mouseup', onDragEnd)
    }
  }, [isDragging, onDragMove, onDragEnd])

  // 清理動畫幀
  useEffect(() => {
    return () => {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current)
      }
    }
  }, [])

  // 響應初始位置變化
  useEffect(() => {
    if (!isDragging) {
      setPositionState(initialPosition)
      dragState.current.lastPosition = initialPosition
    }
  }, [initialPosition, isDragging])

  return {
    position,
    isDragging,
    dragHandlers: {
      onDragStart,
      onDragMove,
      onDragEnd
    },
    setPosition
  }
}