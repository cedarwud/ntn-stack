import { useState, useEffect, useCallback, useRef } from 'react'

export interface Star {
    left: number
    top: number
    size: number
    baseOpacity: number
    phase: number
    speed: number
    animOpacity: number
}

export interface StarfieldProps {
    starCount?: number
    style?: React.CSSProperties
    starStyle?: React.CSSProperties
}

function createStars(starCount: number): Star[] {
    return Array.from({ length: starCount }, () => {
        const baseOpacity = Math.random() * 0.7 + 0.3
        return {
            left: Math.random() * 100,
            top: Math.random() * 100,
            size: Math.random() * 2 + 1,
            baseOpacity,
            phase: Math.random() * Math.PI * 2,
            speed: Math.random() * 1.0 + 1.0,
            animOpacity: baseOpacity,
        }
    })
}

const Starfield: React.FC<StarfieldProps> = ({
    starCount = 180,
    style = {},
    starStyle = {},
}) => {
    const [starAnim, setStarAnim] = useState<Star[]>(() =>
        createStars(starCount)
    )

    const frameRef = useRef(0)
    const mountedRef = useRef(true)

    useEffect(() => {
        mountedRef.current = true

        const updateStars = () => {
            frameRef.current++
            setStarAnim((prev) =>
                prev.map((star) => {
                    const t = frameRef.current / 30
                    const flicker = Math.sin(t * star.speed + star.phase) * 0.5
                    let opacity = star.baseOpacity + flicker
                    opacity = Math.max(0.15, Math.min(1, opacity))
                    return { ...star, animOpacity: opacity }
                })
            )
        }

        // 重新啟用動畫，降低更新頻率到 120ms
        const interval = setInterval(updateStars, 120)

        return () => {
            mountedRef.current = false
            clearInterval(interval)
        }
    }, [])

    // 處理 starCount 變化
    useEffect(() => {
        setStarAnim(createStars(starCount))
    }, [starCount])
    return (
        <div
            style={{
                position: 'absolute',
                inset: 0,
                zIndex: 0,
                pointerEvents: 'none',
                ...style,
            }}
        >
            {starAnim.map((star, i) => (
                <div
                    key={i}
                    style={{
                        position: 'absolute',
                        left: `${star.left}%`,
                        top: `${star.top}%`,
                        width: `${star.size}px`,
                        height: `${star.size}px`,
                        borderRadius: '50%',
                        background: 'white',
                        opacity: star.animOpacity,
                        filter: 'blur(0.5px)',
                        transition: 'opacity 0.2s linear',
                        ...starStyle,
                    }}
                />
            ))}
        </div>
    )
}

export default Starfield
