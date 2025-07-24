import React from 'react'
import { HandoverManagementTabProps } from '../types/sidebar.types'
import { SATELLITE_CONFIG } from '../../../config/satellite.config'

// 使用懶加載的 HandoverManager 來優化 bundle size
const HandoverManager = React.lazy(
    () => import('../../domains/handover/execution/HandoverManager')
)

const HandoverManagementTab: React.FC<HandoverManagementTabProps> = ({
    satellites,
    selectedUEId,
    isVisible,
    handoverMode = 'demo',
    satelliteSpeedMultiplier = 5,
    currentStrategy,
    onHandoverStateChange,
    onCurrentConnectionChange,
    onPredictedConnectionChange,
    onTransitionChange,
    onAlgorithmResults,
}) => {
    if (!isVisible) {
        return null
    }

    return (
        <div className="handover-management-tab">
            {/* 🚀 LEO 衛星換手管理系統 */}
            <React.Suspense
                fallback={
                    <div className="handover-loading">
                        🔄 載入換手管理器...
                    </div>
                }
            >
                <HandoverManager
                    satellites={satellites}
                    selectedUEId={selectedUEId}
                    isEnabled={true}
                    mockMode={false}
                    speedMultiplier={satelliteSpeedMultiplier}
                    handoverMode={handoverMode}
                    handoverStrategy={currentStrategy}
                    onHandoverStateChange={onHandoverStateChange}
                    onCurrentConnectionChange={onCurrentConnectionChange}
                    onPredictedConnectionChange={onPredictedConnectionChange}
                    onTransitionChange={onTransitionChange}
                    onAlgorithmResults={onAlgorithmResults}
                    // UI 在這個獨立模組中始終顯示
                    hideUI={false}
                />
            </React.Suspense>
        </div>
    )
}

export default HandoverManagementTab