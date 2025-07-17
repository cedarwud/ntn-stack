import React, { useState } from 'react'
import AlgorithmComparisonSection from './AlgorithmComparisonSection'
import TrainingAnalysisSection from './TrainingAnalysisSection'
import ConvergenceAnalysisSection from './ConvergenceAnalysisSection'
import './PerformanceAnalysisSection.scss'

interface PerformanceAnalysisProps {
    data: unknown
    onRefresh?: () => void
}

const PerformanceAnalysisSection: React.FC<PerformanceAnalysisProps> = ({ data, onRefresh }) => {
    const [activeTab, setActiveTab] = useState<string>('comparison')

    const tabs = [
        { id: 'comparison', label: '📊 算法比較', icon: '📊' },
        { id: 'training', label: '🧠 訓練分析', icon: '🧠' },
        { id: 'convergence', label: '📈 收斂分析', icon: '📈' }
    ]

    const renderTabContent = () => {
        switch (activeTab) {
            case 'comparison':
                return (
                    <AlgorithmComparisonSection 
                        data={(data as Record<string, unknown>)?.algorithms} 
                        onRefresh={onRefresh} 
                    />
                )
            case 'training':
                return (
                    <TrainingAnalysisSection 
                        data={(data as Record<string, unknown>)?.training} 
                        onRefresh={onRefresh} 
                    />
                )
            case 'convergence':
                return (
                    <ConvergenceAnalysisSection 
                        data={(data as Record<string, unknown>)?.convergence} 
                        onRefresh={onRefresh} 
                    />
                )
            default:
                return null
        }
    }

    return (
        <div className="performance-analysis-section">
            <div className="section-header">
                <h2>📊 性能分析</h2>
                <div className="header-subtitle">
                    深度訓練結果分析、算法比較和收斂性統計測試
                </div>
            </div>
            
            <div className="analysis-tabs">
                <div className="tab-nav">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <span className="tab-icon">{tab.icon}</span>
                            {tab.label}
                        </button>
                    ))}
                </div>
                
                <div className="tab-content">
                    {renderTabContent()}
                </div>
            </div>
        </div>
    )
}

export default PerformanceAnalysisSection