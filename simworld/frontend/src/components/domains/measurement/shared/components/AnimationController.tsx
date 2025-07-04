/**
 * AnimationController 組件
 * 抽取自各事件 Viewer 的動畫控制邏輯
 * 提供統一的動畫播放、暫停、重置、速度控制功能
 */

import React, { useCallback, useEffect, useMemo } from 'react'
import type { AnimationControllerProps } from '../types'

const AnimationController: React.FC<AnimationControllerProps> = ({
  isPlaying,
  currentTime,
  duration,
  speed,
  onPlayPause,
  onReset,
  onSpeedChange,
  onTimeChange,
  className = ''
}) => {
  // 格式化時間顯示
  const formatTime = useCallback((time: number): string => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    const milliseconds = Math.floor((time % 1) * 100)
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(2, '0')}`
  }, [])

  // 計算進度百分比
  const progressPercentage = useMemo(() => {
    return duration > 0 ? (currentTime / duration) * 100 : 0
  }, [currentTime, duration])

  // 速度選項
  const speedOptions = useMemo(() => [
    { value: 0.25, label: '0.25x' },
    { value: 0.5, label: '0.5x' },
    { value: 1, label: '1x' },
    { value: 1.5, label: '1.5x' },
    { value: 2, label: '2x' },
    { value: 4, label: '4x' }
  ], [])

  // 處理時間軸拖拽
  const handleTimeSliderChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(event.target.value)
    onTimeChange(newTime)
  }, [onTimeChange])

  // 處理速度變更
  const handleSpeedChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const newSpeed = parseFloat(event.target.value)
    onSpeedChange(newSpeed)
  }, [onSpeedChange])

  // 鍵盤快捷鍵支持
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      // 只在沒有聚焦到輸入元素時響應快捷鍵
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLSelectElement) {
        return
      }

      switch (event.code) {
        case 'Space':
          event.preventDefault()
          onPlayPause()
          break
        case 'KeyR':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault()
            onReset()
          }
          break
        case 'ArrowLeft':
          event.preventDefault()
          onTimeChange(Math.max(0, currentTime - 1))
          break
        case 'ArrowRight':
          event.preventDefault()
          onTimeChange(Math.min(duration, currentTime + 1))
          break
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [currentTime, duration, onPlayPause, onReset, onTimeChange])

  return (
    <div className={`animation-controller ${className}`}>
      {/* 主控制區域 */}
      <div className="animation-controller__main">
        <div className="animation-controller__buttons">
          {/* 播放/暫停按鈕 */}
          <button
            className={`animation-btn animation-btn--play ${isPlaying ? 'playing' : 'paused'}`}
            onClick={onPlayPause}
            title={isPlaying ? '暫停 (Space)' : '播放 (Space)'}
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>

          {/* 重置按鈕 */}
          <button
            className="animation-btn animation-btn--reset"
            onClick={onReset}
            title="重置動畫 (Ctrl+R)"
          >
            ⏹️
          </button>
        </div>

        {/* 時間顯示 */}
        <div className="animation-controller__time">
          <span className="time-current">{formatTime(currentTime)}</span>
          <span className="time-separator">/</span>
          <span className="time-total">{formatTime(duration)}</span>
        </div>

        {/* 速度控制 */}
        <div className="animation-controller__speed">
          <label className="speed-label">速度:</label>
          <select
            className="speed-select"
            value={speed}
            onChange={handleSpeedChange}
            title="調整播放速度"
          >
            {speedOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 時間軸控制 */}
      <div className="animation-controller__timeline">
        <div className="timeline-container">
          <input
            type="range"
            className="timeline-slider"
            min={0}
            max={duration}
            step={0.1}
            value={currentTime}
            onChange={handleTimeSliderChange}
            title="拖拽調整時間"
          />
          <div 
            className="timeline-progress"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* 快捷鍵提示 */}
      <div className="animation-controller__shortcuts">
        <small>
          快捷鍵: Space(播放/暫停) | ←→(前進/後退) | Ctrl+R(重置)
        </small>
      </div>
    </div>
  )
}

export default AnimationController