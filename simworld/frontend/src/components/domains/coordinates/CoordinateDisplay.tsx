import React from 'react'

interface CoordinateDisplayProps {
    position: {
        x: number
        y: number
        clientX: number
        clientY: number
        sceneX?: number
        sceneY?: number
    } | null
}

// 使用 React.memo 優化，只有 props 變化時才重新渲染
const CoordinateDisplay: React.FC<CoordinateDisplayProps> = React.memo(
    ({ position }) => {
        if (!position) {
            return null
        }

        // 如果已經有計算好的場景座標，則直接使用
        const sceneX = position.sceneX !== undefined ? position.sceneX : null
        const sceneY = position.sceneY !== undefined ? position.sceneY : null

        return (
            <div
                style={{
                    position: 'fixed', // 使用 fixed 定位相對於視窗
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    color: 'white',
                    padding: '2px 6px',
                    borderRadius: '3px',
                    fontSize: '12px',
                    pointerEvents: 'none', // 確保不會阻擋底層元素的事件
                    zIndex: 1000,
                    left: `${position.clientX}px`,
                    top: `${position.clientY - 35}px`, // 在滑鼠上方顯示
                    transform: 'translateX(-50%)', // 水平居中
                    whiteSpace: 'nowrap', // 防止換行
                }}
            >
                X: {sceneX}, Y: {sceneY}
            </div>
        )
    }
)

export default CoordinateDisplay
