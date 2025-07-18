import { useState, useEffect, useCallback, useRef } from 'react'

// 星空星點動畫元件
const STAR_COUNT = 60
interface Star {
    left: number
    top: number
    size: number
    baseOpacity: number
    phase: number
    speed: number
    animOpacity: number
}
function createStars(): Star[] {
    return Array.from({ length: STAR_COUNT }, () => {
        const baseOpacity = Math.random() * 0.7 + 0.3
        return {
            left: Math.random() * 100,
            top: Math.random() * 100,
            size: Math.random() * 1.5 + 0.5,
            baseOpacity,
            phase: Math.random() * Math.PI * 2,
            speed: Math.random() * 1.0 + 1.0,
            animOpacity: baseOpacity,
        }
    })
}
const SidebarStarfield: React.FC = () => {
    const [starAnim, setStarAnim] = useState<Star[]>(() => createStars())
    const frameRef = useRef(0)
    const mountedRef = useRef(true)

    const updateStars = useCallback(() => {
        if (!mountedRef.current) return
        
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
    }, [])

    useEffect(() => {
        mountedRef.current = true
        
        // 恢復動畫，降低更新頻率到 100ms
        const interval = setInterval(updateStars, 100)
        
        return () => {
            mountedRef.current = false
            clearInterval(interval)
        }
    }, [updateStars])
    return (
        <div className="sidebar-starfield-container">
            {starAnim.map((star, i) => (
                <div
                    key={i}
                    className="sidebar-star"
                    style={{
                        left: `${star.left}%`,
                        top: `${star.top}%`,
                        width: `${star.size}px`,
                        height: `${star.size}px`,
                        opacity: star.animOpacity,
                    }}
                />
            ))}
        </div>
    )
}

export default SidebarStarfield
