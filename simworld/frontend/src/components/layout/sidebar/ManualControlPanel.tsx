import React, { useRef } from 'react'
import { ManualControlPanelProps } from '../types/sidebar.types'
import { UAVManualDirection } from '../../domains/device/visualization/UAVFlight'

const ManualControlPanel: React.FC<ManualControlPanelProps> = ({
    isVisible,
    auto,
    manualControlEnabled,
    onManualControl,
}) => {
    const manualIntervalRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    // 只在非自動模式且手動控制開啟時顯示
    if (!isVisible || auto || !manualControlEnabled) {
        return null
    }

    // 手動控制處理
    const handleManualDown = (
        direction:
            | 'up'
            | 'down' 
            | 'left'
            | 'right'
            | 'ascend'
            | 'descend'
            | 'left-up'
            | 'right-up'
            | 'left-down'
            | 'right-down'
            | 'rotate-left'
            | 'rotate-right'
    ) => {
        onManualControl(direction)
        if (manualIntervalRef.current) clearInterval(manualIntervalRef.current)
        manualIntervalRef.current = setInterval(() => {
            onManualControl(direction)
        }, 60)
    }

    const handleManualUp = () => {
        if (manualIntervalRef.current) {
            clearInterval(manualIntervalRef.current)
            manualIntervalRef.current = null
        }
        onManualControl(null)
    }

    return (
        <div className="manual-control-panel">
            <div className="manual-control-title">
                🕹️ UAV 手動控制
            </div>
            <div className="manual-control-grid">
                {/* 第一排：↖ ↑ ↗ */}
                <div className="manual-row">
                    <button
                        onMouseDown={() => handleManualDown('left-up')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ↖
                    </button>
                    <button
                        onMouseDown={() => handleManualDown('descend')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ↑
                    </button>
                    <button
                        onMouseDown={() => handleManualDown('right-up')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ↗
                    </button>
                </div>
                {/* 第二排：← ⟲ ⟳ → */}
                <div className="manual-row">
                    <button
                        onMouseDown={() => handleManualDown('left')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ←
                    </button>
                    <button
                        onMouseDown={() => handleManualDown('rotate-left')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ⟲
                    </button>
                    <button
                        onMouseDown={() => handleManualDown('rotate-right')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ⟳
                    </button>
                    <button
                        onMouseDown={() => handleManualDown('right')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        →
                    </button>
                </div>
                {/* 第三排：↙ ↓ ↘ */}
                <div className="manual-row">
                    <button
                        onMouseDown={() => handleManualDown('left-down')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ↙
                    </button>
                    <button
                        onMouseDown={() => handleManualDown('ascend')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ↓
                    </button>
                    <button
                        onMouseDown={() => handleManualDown('right-down')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        ↘
                    </button>
                </div>
                {/* 升降排 */}
                <div className="manual-row">
                    <button
                        onMouseDown={() => handleManualDown('up')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        升
                    </button>
                    <button
                        onMouseDown={() => handleManualDown('down')}
                        onMouseUp={handleManualUp}
                        onMouseLeave={handleManualUp}
                    >
                        降
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ManualControlPanel