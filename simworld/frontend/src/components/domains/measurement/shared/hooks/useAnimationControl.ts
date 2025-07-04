/**
 * useAnimationControl Hook
 * 抽取自各事件 Viewer 的動畫狀態管理邏輯
 * 提供統一的動畫狀態管理、自動播放、時間更新等功能
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import type { AnimationState } from '../types'

interface UseAnimationControlOptions {
  duration: number // 動畫總時長（秒）
  stepSize?: number // 時間步長（秒），默認 0.1
  updateInterval?: number // 更新間隔（毫秒），默認 100
  autoReset?: boolean // 動畫結束時是否自動重置，默認 true
}

interface UseAnimationControlResult {
  animationState: AnimationState
  isPlaying: boolean
  currentTime: number
  speed: number
  duration: number
  
  // 控制函數
  play: () => void
  pause: () => void
  togglePlayPause: () => void
  reset: () => void
  setTime: (time: number) => void
  setSpeed: (speed: number) => void
  
  // 狀態更新函數
  updateAnimationState: (updates: Partial<AnimationState>) => void
}

export const useAnimationControl = ({
  duration,
  stepSize = 0.1,
  updateInterval = 100,
  autoReset = true
}: UseAnimationControlOptions): UseAnimationControlResult => {
  
  // 動畫狀態
  const [animationState, setAnimationState] = useState<AnimationState>({
    isPlaying: false,
    currentTime: 0,
    speed: 1,
    nodePosition: null,
    eventConditions: [],
    activeEvents: []
  })

  // 用於存儲 interval ID 的 ref
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // 清理 interval 的函數
  const clearAnimationInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  // 播放函數
  const play = useCallback(() => {
    setAnimationState(prev => ({
      ...prev,
      isPlaying: true
    }))
  }, [])

  // 暫停函數
  const pause = useCallback(() => {
    setAnimationState(prev => ({
      ...prev,
      isPlaying: false
    }))
    clearAnimationInterval()
  }, [clearAnimationInterval])

  // 播放/暫停切換
  const togglePlayPause = useCallback(() => {
    setAnimationState(prev => ({
      ...prev,
      isPlaying: !prev.isPlaying
    }))
  }, [])

  // 重置函數
  const reset = useCallback(() => {
    setAnimationState(prev => ({
      ...prev,
      isPlaying: false,
      currentTime: 0,
      nodePosition: null,
      eventConditions: [],
      activeEvents: []
    }))
    clearAnimationInterval()
  }, [clearAnimationInterval])

  // 設置時間
  const setTime = useCallback((time: number) => {
    const clampedTime = Math.max(0, Math.min(duration, time))
    setAnimationState(prev => ({
      ...prev,
      currentTime: clampedTime
    }))
  }, [duration])

  // 設置速度
  const setSpeed = useCallback((speed: number) => {
    setAnimationState(prev => ({
      ...prev,
      speed: Math.max(0.1, Math.min(10, speed)) // 限制速度範圍 0.1x - 10x
    }))
  }, [])

  // 更新動畫狀態
  const updateAnimationState = useCallback((updates: Partial<AnimationState>) => {
    setAnimationState(prev => ({
      ...prev,
      ...updates
    }))
  }, [])

  // 動畫循環邏輯
  useEffect(() => {
    if (!animationState.isPlaying) {
      clearAnimationInterval()
      return
    }

    intervalRef.current = setInterval(() => {
      setAnimationState(prev => {
        const newTime = prev.currentTime + stepSize * prev.speed
        
        // 檢查是否達到最大時間
        if (newTime >= duration) {
          // 動畫結束處理
          if (autoReset) {
            return {
              ...prev,
              isPlaying: false,
              currentTime: 0
            }
          } else {
            return {
              ...prev,
              isPlaying: false,
              currentTime: duration
            }
          }
        }
        
        return {
          ...prev,
          currentTime: newTime
        }
      })
    }, updateInterval)

    return clearAnimationInterval
  }, [animationState.isPlaying, animationState.speed, stepSize, duration, updateInterval, autoReset, clearAnimationInterval])

  // 組件卸載時清理 interval
  useEffect(() => {
    return clearAnimationInterval
  }, [clearAnimationInterval])

  return {
    animationState,
    isPlaying: animationState.isPlaying,
    currentTime: animationState.currentTime,
    speed: animationState.speed,
    duration,
    
    play,
    pause,
    togglePlayPause,
    reset,
    setTime,
    setSpeed,
    updateAnimationState
  }
}