import React, { memo } from 'react'
import './TrainingStatusSection.scss'

interface TrainingStatusSectionProps {
    data?: {
        training: {
            status: string;
            progress: number;
            algorithms: Array<{
                algorithm: string;
                status: string;
                progress: number;
                training_active: boolean;
                metrics: any;
            }>;
        };
    };
}

const TrainingStatusSection: React.FC<TrainingStatusSectionProps> = ({ data }) => {
    const algorithms = data?.training?.algorithms || [];
    
    // Algorithms array processing
    
    return (
        <div className="training-status-section">
            <h2 className="section-title">🎯 Training Status</h2>
            
            <div className="training-overview">
                <div className="status-card">
                    <div className="status-indicator">
                        <span className={`status-dot ${data?.training?.status || 'idle'}`}></span>
                        <span className="status-text">
                            {data?.training?.status === 'running' ? 'Training Active' : 'System Ready'}
                        </span>
                    </div>
                    <div className="progress-info">
                        <div className="progress-bar">
                            <div 
                                className="progress-fill" 
                                style={{ width: `${(data?.training?.progress || 0) * 100}%` }}
                            ></div>
                        </div>
                        <span className="progress-text">
                            {((data?.training?.progress || 0) * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>

            <div className="algorithms-grid">
                {algorithms.length === 0 ? (
                    <div className="no-algorithms-message">
                        <div className="message-icon">🤖</div>
                        <div className="message-text">No algorithms available</div>
                        <div className="message-subtext">Algorithms will appear here when training data is loaded</div>
                    </div>
                ) : (
                    algorithms.map((algo, index) => (
                        <div key={index} className="algorithm-card">
                            <div className="algorithm-header">
                                <h3 className="algorithm-name">{algo.algorithm.toUpperCase()}</h3>
                                <span className={`algorithm-status ${algo.status}`}>
                                    {algo.training_active ? '🔄 Training' : '⏸️ Idle'}
                                </span>
                            </div>
                            <div className="algorithm-metrics">
                                <div className="metric">
                                    <span className="metric-label">Progress:</span>
                                    <span className="metric-value">{(algo.progress * 100).toFixed(1)}%</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-label">Success Rate:</span>
                                    <span className="metric-value">{((algo.metrics?.success_rate || 0) * 100).toFixed(1)}%</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-label">Stability:</span>
                                    <span className="metric-value">{((algo.metrics?.stability || 0) * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}

export default memo(TrainingStatusSection)
