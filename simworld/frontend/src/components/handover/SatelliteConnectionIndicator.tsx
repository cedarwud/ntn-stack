import React, { useState, useEffect } from 'react';
import { SatelliteConnection } from '../../types/handover';
import './SatelliteConnectionIndicator.scss';

interface SatelliteConnectionIndicatorProps {
  currentConnection: SatelliteConnection | null;
  predictedConnection: SatelliteConnection | null;
  isTransitioning: boolean;
  transitionProgress: number; // 0-1
  onConnectionSelect?: (satelliteId: string) => void;
}

const SatelliteConnectionIndicator: React.FC<SatelliteConnectionIndicatorProps> = ({
  currentConnection,
  predictedConnection,
  isTransitioning,
  transitionProgress,
  onConnectionSelect
}) => {
  const [animationPhase, setAnimationPhase] = useState<'idle' | 'fadeOut' | 'switch' | 'fadeIn'>('idle');

  useEffect(() => {
    if (isTransitioning) {
      // 換手動畫序列
      if (transitionProgress < 0.25) {
        setAnimationPhase('fadeOut');
      } else if (transitionProgress < 0.75) {
        setAnimationPhase('switch');
      } else {
        setAnimationPhase('fadeIn');
      }
    } else {
      setAnimationPhase('idle');
    }
  }, [isTransitioning, transitionProgress]);

  const formatSignalStrength = (strength: number) => {
    return `${strength.toFixed(1)} dBm`;
  };

  const getSignalBars = (strength: number) => {
    // 將信號強度轉換為 1-5 格信號條
    const normalizedStrength = Math.max(0, Math.min(100, (strength + 100) * 2)); // -100dBm to 0dBm -> 0 to 100
    return Math.ceil(normalizedStrength / 20);
  };

  const renderSatelliteCard = (
    connection: SatelliteConnection,
    type: 'current' | 'predicted',
    isActive: boolean
  ) => {
    const signalBars = getSignalBars(connection.signalStrength);
    
    return (
      <div 
        className={`satellite-card ${type} ${isActive ? 'active' : ''} ${animationPhase}`}
        onClick={() => onConnectionSelect?.(connection.satelliteId)}
        title={`點擊選擇 ${connection.satelliteName}`}
      >
        <div className="card-header">
          <div className="satellite-icon">
            🛰️
          </div>
          <div className="satellite-info">
            <div className="satellite-name">{connection.satelliteName}</div>
            <div className="satellite-id">ID: {connection.satelliteId}</div>
          </div>
          <div className="connection-status">
            {connection.isConnected && <div className="status-dot connected"></div>}
            {connection.isPredicted && <div className="status-dot predicted"></div>}
          </div>
        </div>

        <div className="satellite-metrics">
          <div className="metric-item">
            <span className="metric-label">仰角</span>
            <span className="metric-value">{connection.elevation.toFixed(1)}°</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">方位角</span>
            <span className="metric-value">{connection.azimuth.toFixed(1)}°</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">距離</span>
            <span className="metric-value">{connection.distance.toFixed(0)} km</span>
          </div>
        </div>

        <div className="signal-info">
          <div className="signal-strength">
            <span className="signal-label">信號強度</span>
            <span className="signal-value">{formatSignalStrength(connection.signalStrength)}</span>
          </div>
          <div className="signal-bars">
            {Array.from({ length: 5 }, (_, i) => (
              <div
                key={i}
                className={`signal-bar ${i < signalBars ? 'active' : ''}`}
              ></div>
            ))}
          </div>
        </div>

        <div className="card-type-label">
          {type === 'current' ? 'AT' : 'AT+Δt'}
        </div>
      </div>
    );
  };

  const renderTransitionAnimation = () => {
    if (!isTransitioning) return null;

    return (
      <div className="transition-animation">
        <div className="transition-arrow">
          <div className="arrow-body" style={{ width: `${transitionProgress * 100}%` }}></div>
          <div className="arrow-head" style={{ left: `${transitionProgress * 100}%` }}>
            ➤
          </div>
        </div>
        <div className="transition-label">
          換手進行中... {(transitionProgress * 100).toFixed(0)}%
        </div>
      </div>
    );
  };

  return (
    <div className="satellite-connection-indicator">
      <div className="indicator-header">
        <h3>🔗 衛星接入狀態</h3>
        <div className="connection-mode">
          {isTransitioning ? (
            <span className="mode-transitioning">🔄 換手中</span>
          ) : (
            <span className="mode-stable">✅ 穩定連接</span>
          )}
        </div>
      </div>

      <div className="satellite-connections">
        {/* 當前連接衛星 */}
        <div className="connection-section current-section">
          <div className="section-label">
            <span className="label-text">當前衛星 (AT)</span>
            <span className="time-label">T</span>
          </div>
          {currentConnection ? (
            renderSatelliteCard(currentConnection, 'current', !isTransitioning)
          ) : (
            <div className="no-connection">
              <div className="no-connection-icon">❌</div>
              <div className="no-connection-text">無連接</div>
            </div>
          )}
        </div>

        {/* 轉換動畫 */}
        {renderTransitionAnimation()}

        {/* 預測連接衛星 */}
        <div className="connection-section predicted-section">
          <div className="section-label">
            <span className="label-text">預測衛星 (AT+Δt)</span>
            <span className="time-label">T+Δt</span>
          </div>
          {predictedConnection ? (
            renderSatelliteCard(predictedConnection, 'predicted', false)
          ) : (
            <div className="no-prediction">
              <div className="no-prediction-icon">🔮</div>
              <div className="no-prediction-text">預測中...</div>
            </div>
          )}
        </div>
      </div>

      {/* 連接品質指標 */}
      {currentConnection && (
        <div className="quality-indicators">
          <div className="quality-item">
            <span className="quality-label">連接品質</span>
            <div className="quality-meter">
              <div 
                className="quality-fill"
                style={{ 
                  width: `${Math.max(0, (currentConnection.signalStrength + 100) * 2)}%` 
                }}
              ></div>
            </div>
          </div>
          <div className="quality-item">
            <span className="quality-label">仰角品質</span>
            <div className="quality-meter">
              <div 
                className="quality-fill"
                style={{ 
                  width: `${Math.min(100, currentConnection.elevation * 2)}%` 
                }}
              ></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SatelliteConnectionIndicator;