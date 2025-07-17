import React, { useState } from 'react'
import VisualizationSection from './VisualizationSection'
import Satellite3DVisualization from './Satellite3DVisualization'
import DecisionProcessAnimation from './DecisionProcessAnimation'
import SignalHeatMap from './SignalHeatMap'
import './EnvironmentVisualizationSection.scss'

interface EnvironmentVisualizationProps {
    data: unknown
    onRefresh?: () => void
}

const EnvironmentVisualizationSection: React.FC<EnvironmentVisualizationProps> = ({ data, onRefresh }) => {
    const [activeView, setActiveView] = useState<'3d' | '2d' | 'decision' | 'heatmap'>('3d')
    const [selectedSatellite, setSelectedSatellite] = useState<string | undefined>()

    return (
        <div className="environment-visualization-section">
            <div className="section-header">
                <h2>🌐 環境可視化</h2>
                <div className="view-selector">
                    <button 
                        className={`view-btn ${activeView === '3d' ? 'active' : ''}`}
                        onClick={() => setActiveView('3d')}
                    >
                        🌍 3D 星座
                    </button>
                    <button 
                        className={`view-btn ${activeView === '2d' ? 'active' : ''}`}
                        onClick={() => setActiveView('2d')}
                    >
                        🗺️ 2D 視圖
                    </button>
                    <button 
                        className={`view-btn ${activeView === 'decision' ? 'active' : ''}`}
                        onClick={() => setActiveView('decision')}
                    >
                        🎯 決策過程
                    </button>
                    <button 
                        className={`view-btn ${activeView === 'heatmap' ? 'active' : ''}`}
                        onClick={() => setActiveView('heatmap')}
                    >
                        🔥 信號熱力圖
                    </button>
                </div>
            </div>
            
            <div className="visualization-content">
                {activeView === '3d' && (
                    <div className="view-3d">
                        <Satellite3DVisualization 
                            selectedSatellite={selectedSatellite}
                            onSatelliteSelect={(satellite) => setSelectedSatellite(satellite.id)}
                        />
                    </div>
                )}
                
                {activeView === '2d' && (
                    <div className="view-2d">
                        <VisualizationSection 
                            data={(data as Record<string, unknown>)?.visualization} 
                            onRefresh={onRefresh} 
                        />
                    </div>
                )}
                
                {activeView === 'decision' && (
                    <div className="view-decision">
                        <DecisionProcessAnimation 
                            selectedSatellite={selectedSatellite}
                            onSatelliteSelect={setSelectedSatellite}
                        />
                    </div>
                )}
                
                {activeView === 'heatmap' && (
                    <div className="view-heatmap">
                        <SignalHeatMap 
                            selectedSatellite={selectedSatellite}
                            onSatelliteSelect={setSelectedSatellite}
                        />
                    </div>
                )}
            </div>
        </div>
    )
}

export default EnvironmentVisualizationSection