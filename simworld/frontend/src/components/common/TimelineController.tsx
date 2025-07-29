/**
 * Phase 2: 時間軸控制器
 * 
 * 提供播放/暫停/快進/時間跳轉功能
 * 支援 60 倍加速和自定義速度控制
 */

import React, { useState, useCallback } from 'react'
import { Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

export interface TimelineControllerProps {
  isPlaying: boolean
  currentTime: number
  totalDuration: number
  speed: number
  onPlay: () => void
  onPause: () => void
  onSeek: (time: number) => void
  onSpeedChange: (speed: number) => void
  onReset?: () => void
  className?: string
}

const SPEED_OPTIONS = [
  { value: 1, label: '1x' },
  { value: 10, label: '10x' },
  { value: 30, label: '30x' },
  { value: 60, label: '60x' },
  { value: 120, label: '120x' },
  { value: 300, label: '300x' }
]

export const TimelineController: React.FC<TimelineControllerProps> = ({
  isPlaying,
  currentTime,
  totalDuration,
  speed,
  onPlay,
  onPause,
  onSeek,
  onSpeedChange,
  onReset,
  className = ''
}) => {
  const [isDragging, setIsDragging] = useState(false)

  // 格式化時間顯示
  const formatTime = useCallback((seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }, [])

  // 處理進度條拖拽
  const handleProgressChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = (parseFloat(event.target.value) / 100) * totalDuration
    onSeek(newTime)
  }, [totalDuration, onSeek])

  const handleProgressMouseDown = useCallback(() => {
    setIsDragging(true)
  }, [])

  const handleProgressMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // 快進/快退
  const handleSkipForward = useCallback(() => {
    const newTime = Math.min(currentTime + 60, totalDuration) // 快進 1 分鐘
    onSeek(newTime)
  }, [currentTime, totalDuration, onSeek])

  const handleSkipBack = useCallback(() => {
    const newTime = Math.max(currentTime - 60, 0) // 快退 1 分鐘
    onSeek(newTime)
  }, [currentTime, onSeek])

  // 計算進度百分比
  const progressPercentage = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0

  return (
    <Card className={`p-4 bg-gray-900/90 backdrop-blur-sm border-gray-700 ${className}`}>
      <div className="space-y-4">
        {/* 時間顯示 */}
        <div className="flex justify-between items-center text-sm text-gray-300">
          <span>{formatTime(currentTime)}</span>
          <span className="text-blue-400 font-mono">
            {speed}x 加速
          </span>
          <span>{formatTime(totalDuration)}</span>
        </div>

        {/* 進度條 */}
        <div className="relative">
          <input
            type="range"
            min="0"
            max="100"
            value={progressPercentage}
            onChange={handleProgressChange}
            onMouseDown={handleProgressMouseDown}
            onMouseUp={handleProgressMouseUp}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${progressPercentage}%, #374151 ${progressPercentage}%, #374151 100%)`
            }}
          />
          
          {/* 進度指示器 */}
          <div 
            className="absolute top-0 w-3 h-2 bg-blue-500 rounded-full transform -translate-x-1/2 pointer-events-none"
            style={{ left: `${progressPercentage}%` }}
          />
        </div>

        {/* 控制按鈕 */}
        <div className="flex items-center justify-center space-x-2">
          {/* 重置按鈕 */}
          {onReset && (
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              className="bg-gray-800 border-gray-600 hover:bg-gray-700"
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
          )}

          {/* 快退按鈕 */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleSkipBack}
            className="bg-gray-800 border-gray-600 hover:bg-gray-700"
          >
            <SkipBack className="w-4 h-4" />
          </Button>

          {/* 播放/暫停按鈕 */}
          <Button
            variant="outline"
            size="sm"
            onClick={isPlaying ? onPause : onPlay}
            className="bg-blue-600 border-blue-500 hover:bg-blue-700 text-white"
          >
            {isPlaying ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </Button>

          {/* 快進按鈕 */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleSkipForward}
            className="bg-gray-800 border-gray-600 hover:bg-gray-700"
          >
            <SkipForward className="w-4 h-4" />
          </Button>
        </div>

        {/* 速度控制 */}
        <div className="flex items-center justify-center space-x-2">
          <span className="text-sm text-gray-400">速度:</span>
          <div className="flex space-x-1">
            {SPEED_OPTIONS.map((option) => (
              <Button
                key={option.value}
                variant={speed === option.value ? "default" : "outline"}
                size="sm"
                onClick={() => onSpeedChange(option.value)}
                className={`text-xs px-2 py-1 ${
                  speed === option.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-600 hover:bg-gray-700 text-gray-300'
                }`}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>

        {/* 狀態指示器 */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isPlaying ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>{isPlaying ? '播放中' : '已暫停'}</span>
          </div>
          
          {isDragging && (
            <span className="text-blue-400">拖拽中...</span>
          )}
          
          <div className="text-right">
            <div>剩餘: {formatTime(totalDuration - currentTime)}</div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: 2px solid #1e293b;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .slider::-webkit-slider-thumb:hover {
          background: #2563eb;
          transform: scale(1.1);
        }

        .slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: 2px solid #1e293b;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .slider::-moz-range-thumb:hover {
          background: #2563eb;
          transform: scale(1.1);
        }
      `}</style>
    </Card>
  )
}

export default TimelineController
