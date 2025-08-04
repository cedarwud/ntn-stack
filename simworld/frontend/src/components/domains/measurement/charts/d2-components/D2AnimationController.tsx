/**
 * D2AnimationController - 動畫播放控制組件
 * 整合從 PureD2Chart 提取的動畫播放控制功能
 */

import React, { useState, useCallback, useEffect, useRef } from 'react'

export interface AnimationState {
    isPlaying: boolean
    currentTime: number
    speed: number
    duration: number
    loop: boolean
}

export interface AnimationControllerProps {
    initialTime?: number
    maxTime?: number
    speed?: number
    autoPlay?: boolean
    loop?: boolean
    onTimeChange?: (time: number) => void
    onPlayStateChange?: (isPlaying: boolean) => void
    isDarkTheme?: boolean
}

export const D2AnimationController: React.FC<AnimationControllerProps> = ({
    initialTime = 0,
    maxTime = 120,
    speed = 1,
    autoPlay = false,
    loop = true,
    onTimeChange,
    onPlayStateChange,
    isDarkTheme = true,
}) => {
    const [animationState, setAnimationState] = useState<AnimationState>({
        isPlaying: autoPlay,
        currentTime: initialTime,
        speed: speed,
        duration: maxTime,
        loop: loop,
    })

    const animationFrameRef = useRef<number | null>(null)
    const lastUpdateRef = useRef<number>(Date.now())

    // 動畫更新循環
    const updateAnimation = useCallback(() => {
        if (!animationState.isPlaying) return

        const now = Date.now()
        const deltaTime = (now - lastUpdateRef.current) / 1000 // 轉換為秒
        lastUpdateRef.current = now

        setAnimationState(prev => {
            let newTime = prev.currentTime + deltaTime * prev.speed

            // 處理循環邏輯
            if (newTime >= prev.duration) {
                if (prev.loop) {
                    newTime = newTime % prev.duration
                } else {
                    newTime = prev.duration
                    // 停止播放
                    return {
                        ...prev,
                        currentTime: newTime,
                        isPlaying: false,
                    }
                }
            } else if (newTime < 0) {
                if (prev.loop) {
                    newTime = prev.duration + (newTime % prev.duration)
                } else {
                    newTime = 0
                    return {
                        ...prev,
                        currentTime: newTime,
                        isPlaying: false,
                    }
                }
            }

            // 通知時間變化
            onTimeChange?.(newTime)

            return {
                ...prev,
                currentTime: newTime,
            }
        })

        animationFrameRef.current = requestAnimationFrame(updateAnimation)
    }, [animationState.isPlaying, onTimeChange])

    // 啟動/停止動畫
    useEffect(() => {
        if (animationState.isPlaying) {
            lastUpdateRef.current = Date.now()
            animationFrameRef.current = requestAnimationFrame(updateAnimation)
        } else {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current)
                animationFrameRef.current = null
            }
        }

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current)
            }
        }
    }, [animationState.isPlaying, updateAnimation])

    // 播放/暫停控制
    const togglePlayPause = useCallback(() => {
        setAnimationState(prev => {
            const newIsPlaying = !prev.isPlaying
            onPlayStateChange?.(newIsPlaying)
            return {
                ...prev,
                isPlaying: newIsPlaying,
            }
        })
    }, [onPlayStateChange])

    // 停止並重置
    const stop = useCallback(() => {
        setAnimationState(prev => ({
            ...prev,
            isPlaying: false,
            currentTime: 0,
        }))
        onPlayStateChange?.(false)
        onTimeChange?.(0)
    }, [onTimeChange, onPlayStateChange])

    // 跳轉到指定時間
    const seekTo = useCallback((time: number) => {
        const clampedTime = Math.max(0, Math.min(time, animationState.duration))
        setAnimationState(prev => ({
            ...prev,
            currentTime: clampedTime,
        }))
        onTimeChange?.(clampedTime)
    }, [animationState.duration, onTimeChange])

    // 設置播放速度
    const setSpeed = useCallback((newSpeed: number) => {
        setAnimationState(prev => ({
            ...prev,
            speed: Math.max(0.1, Math.min(10, newSpeed)), // 限制速度範圍
        }))
    }, [])

    // 設置循環模式
    const setLoop = useCallback((loop: boolean) => {
        setAnimationState(prev => ({
            ...prev,
            loop,
        }))
    }, [])

    // 格式化時間顯示
    const formatTime = useCallback((seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }, [])

    const themeClass = isDarkTheme ? 'dark-theme' : 'light-theme'

    return (
        <div className={`d2-animation-controller ${themeClass}`}>
            {/* 播放控制按鈕 */}
            <div className="animation-controls">
                <button
                    className="control-btn play-pause-btn"
                    onClick={togglePlayPause}
                    title={animationState.isPlaying ? '暫停' : '播放'}
                >
                    {animationState.isPlaying ? '⏸️' : '▶️'}
                </button>
                
                <button
                    className="control-btn stop-btn"
                    onClick={stop}
                    title="停止"
                >
                    ⏹️
                </button>

                {/* 時間顯示 */}
                <div className="time-display">
                    {formatTime(animationState.currentTime)} / {formatTime(animationState.duration)}
                </div>
            </div>

            {/* 進度條 */}
            <div className="progress-container">
                <input
                    type="range"
                    min="0"
                    max={animationState.duration}
                    step="0.1"
                    value={animationState.currentTime}
                    onChange={(e) => seekTo(parseFloat(e.target.value))}
                    className="progress-slider"
                />
            </div>

            {/* 速度控制 */}
            <div className="speed-controls">
                <label className="speed-label">速度:</label>
                <button
                    className="speed-btn"
                    onClick={() => setSpeed(0.5)}
                    disabled={animationState.speed === 0.5}
                >
                    0.5x
                </button>
                <button
                    className="speed-btn"
                    onClick={() => setSpeed(1)}
                    disabled={animationState.speed === 1}
                >
                    1x
                </button>
                <button
                    className="speed-btn"
                    onClick={() => setSpeed(2)}
                    disabled={animationState.speed === 2}
                >
                    2x
                </button>
                <button
                    className="speed-btn"
                    onClick={() => setSpeed(5)}
                    disabled={animationState.speed === 5}
                >
                    5x
                </button>

                {/* 循環控制 */}
                <label className="loop-control">
                    <input
                        type="checkbox"
                        checked={animationState.loop}
                        onChange={(e) => setLoop(e.target.checked)}
                    />
                    🔄 循環
                </label>
            </div>

            <style jsx>{`
                .d2-animation-controller {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    padding: 16px;
                    border-radius: 8px;
                    border: 1px solid;
                    margin: 16px 0;
                }

                .d2-animation-controller.dark-theme {
                    background: rgba(0, 0, 0, 0.8);
                    border-color: rgba(255, 255, 255, 0.2);
                    color: white;
                }

                .d2-animation-controller.light-theme {
                    background: rgba(255, 255, 255, 0.9);
                    border-color: rgba(0, 0, 0, 0.2);
                    color: black;
                }

                .animation-controls {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .control-btn {
                    background: none;
                    border: 1px solid currentColor;
                    border-radius: 4px;
                    padding: 8px 12px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: all 0.2s ease;
                }

                .control-btn:hover {
                    background: currentColor;
                    color: var(--bg-color);
                }

                .time-display {
                    font-family: monospace;
                    font-size: 14px;
                    margin-left: auto;
                }

                .progress-container {
                    width: 100%;
                }

                .progress-slider {
                    width: 100%;
                    height: 6px;
                    border-radius: 3px;
                    outline: none;
                    -webkit-appearance: none;
                }

                .progress-slider::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: currentColor;
                    cursor: pointer;
                }

                .speed-controls {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex-wrap: wrap;
                }

                .speed-label {
                    font-size: 14px;
                    margin-right: 8px;
                }

                .speed-btn {
                    background: none;
                    border: 1px solid currentColor;
                    border-radius: 4px;
                    padding: 4px 8px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: all 0.2s ease;
                }

                .speed-btn:hover:not(:disabled) {
                    background: currentColor;
                    color: var(--bg-color);
                }

                .speed-btn:disabled {
                    background: currentColor;
                    color: var(--bg-color);
                    opacity: 0.7;
                }

                .loop-control {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    font-size: 14px;
                    margin-left: auto;
                    cursor: pointer;
                }

                .loop-control input {
                    margin: 0;
                }
            `}</style>
        </div>
    )
}

export default D2AnimationController