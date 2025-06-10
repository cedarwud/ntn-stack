import React, { useState, useEffect, useCallback } from 'react';
import './AnomalyAlertSystem.scss';

interface AnomalyAlertSystemProps {
  enabled: boolean;
  devices: any[];
}

interface HandoverAnomaly {
  id: string;
  type: 'timeout' | 'signal_degradation' | 'target_unavailable' | 'interference_detected' | 'network_congestion' | 'prediction_failure';
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: number;
  ue_id: string;
  handover_id: string;
  description: string;
  affected_satellites: string[];
  signal_metrics: Record<string, number>;
  recovery_suggestions: string[];
  fallback_action?: FallbackAction;
  status: 'active' | 'resolved' | 'escalated';
}

interface FallbackAction {
  action_id: string;
  strategy: string;
  target_satellite?: string;
  estimated_recovery_time: number;
  confidence: number;
  description: string;
  priority: number;
  status: 'pending' | 'executing' | 'completed' | 'failed';
}

interface AlertMetrics {
  total_anomalies: number;
  active_anomalies: number;
  resolved_anomalies: number;
  critical_anomalies: number;
  average_resolution_time: number;
  success_rate: number;
  successful_decisions: number;
  total_decisions: number;
}

const AnomalyAlertSystem: React.FC<AnomalyAlertSystemProps> = ({
  enabled,
  devices
}) => {
  const [anomalies, setAnomalies] = useState<HandoverAnomaly[]>([]);
  const [activeAlerts, setActiveAlerts] = useState<HandoverAnomaly[]>([]);
  const [fallbackActions, setFallbackActions] = useState<FallbackAction[]>([]);
  const [metrics, setMetrics] = useState<AlertMetrics>({
    total_anomalies: 0,
    active_anomalies: 0,
    resolved_anomalies: 0,
    critical_anomalies: 0,
    average_resolution_time: 0,
    success_rate: 0,
    successful_decisions: 0,
    total_decisions: 0
  });
  
  const [filter, setFilter] = useState<'all' | 'active' | 'critical' | 'resolved'>('all');
  const [isMinimized, setIsMinimized] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // 生成隨機異常
  const generateRandomAnomaly = useCallback(() => {
    const types: HandoverAnomaly['type'][] = ['timeout', 'signal_degradation', 'target_unavailable', 'interference_detected', 'network_congestion'];
    const severities: HandoverAnomaly['severity'][] = ['low', 'medium', 'high', 'critical'];
    const ueIds = ['UE_001', 'UE_002', 'UE_003', 'UAV_001', 'UAV_002'];
    const satellites = ['SAT_A1', 'SAT_B2', 'SAT_C3', 'SAT_D4', 'SAT_E5'];

    const type = types[Math.floor(Math.random() * types.length)];
    const severity = severities[Math.floor(Math.random() * severities.length)];
    const ueId = ueIds[Math.floor(Math.random() * ueIds.length)];
    
    const descriptions = {
      'timeout': '換手超時，未在預期時間內完成',
      'signal_degradation': '目標衛星信號品質嚴重劣化',
      'target_unavailable': '目標衛星突然不可用或失聯',
      'interference_detected': '檢測到強烈干擾信號',
      'network_congestion': '網路擁塞導致換手延遲',
      'prediction_failure': '換手預測算法失效'
    };

    const recoveryMap = {
      'timeout': ['回滾到源衛星', '重新計算換手路徑', '增加重試次數'],
      'signal_degradation': ['等待信號改善', '調整天線指向', '選擇信號更強的衛星'],
      'target_unavailable': ['選擇替代衛星', '重新計算最優路徑', '延遲換手等待恢復'],
      'interference_detected': ['頻率跳躍', '增加發射功率', '選擇低干擾頻段'],
      'network_congestion': ['負載均衡', '選擇較少擁塞的衛星', '調整服務質量等級'],
      'prediction_failure': ['切換到傳統換手', '重新校準預測模型', '使用備用預測算法']
    };

    const anomaly: HandoverAnomaly = {
      id: `anomaly_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      severity,
      timestamp: Date.now(),
      ue_id: ueId,
      handover_id: `HO_${Date.now()}`,
      description: descriptions[type],
      affected_satellites: [satellites[Math.floor(Math.random() * satellites.length)]],
      signal_metrics: {
        rsrp: -70 - Math.random() * 40,
        rsrq: -10 - Math.random() * 15,
        sinr: Math.random() * 20 - 5
      },
      recovery_suggestions: recoveryMap[type],
      status: 'active'
    };

    return anomaly;
  }, []);

  // 生成隨機回退動作
  const generateFallbackAction = useCallback((anomaly: HandoverAnomaly): FallbackAction => {
    const strategies = ['ROLLBACK_TO_SOURCE', 'SELECT_ALTERNATIVE_SATELLITE', 'DELAY_HANDOVER', 'ADJUST_POWER_PARAMETERS', 'FREQUENCY_HOPPING'];
    const strategy = strategies[Math.floor(Math.random() * strategies.length)];
    
    const strategyDescriptions = {
      'ROLLBACK_TO_SOURCE': '回滾到源衛星',
      'SELECT_ALTERNATIVE_SATELLITE': '選擇替代衛星',
      'DELAY_HANDOVER': '延遲換手執行',
      'ADJUST_POWER_PARAMETERS': '調整功率參數',
      'FREQUENCY_HOPPING': '執行頻率跳躍'
    };

    return {
      action_id: `action_${Date.now()}_${anomaly.id}`,
      strategy,
      target_satellite: anomaly.affected_satellites[0],
      estimated_recovery_time: 1 + Math.random() * 8,
      confidence: 0.6 + Math.random() * 0.3,
      description: strategyDescriptions[strategy as keyof typeof strategyDescriptions],
      priority: anomaly.severity === 'critical' ? 10 : anomaly.severity === 'high' ? 8 : 5,
      status: 'pending'
    };
  }, []);

  // 模擬數據更新
  useEffect(() => {
    if (!enabled) return;

    const updateData = () => {
      // 30% 機率生成新異常
      if (Math.random() < 0.3) {
        const newAnomaly = generateRandomAnomaly();
        const fallbackAction = generateFallbackAction(newAnomaly);
        
        setAnomalies(prev => [newAnomaly, ...prev.slice(0, 49)]);
        setFallbackActions(prev => [fallbackAction, ...prev.slice(0, 19)]);
        
        // 播放警告音效（如果啟用）
        if (soundEnabled && (newAnomaly.severity === 'high' || newAnomaly.severity === 'critical')) {
          // 在實際應用中會播放音效
          console.log(`🔔 新的${newAnomaly.severity}級別異常: ${newAnomaly.description}`);
        }
      }

      // 更新活躍異常
      setActiveAlerts(prev => {
        const updated = prev.map(alert => {
          // 20% 機率解決異常
          if (Math.random() < 0.2 && alert.status === 'active') {
            return { ...alert, status: 'resolved' as const };
          }
          return alert;
        }).filter(alert => alert.status === 'active');

        // 添加新的活躍異常
        const newActiveAnomalies = anomalies
          .filter(a => a.status === 'active')
          .filter(a => !updated.find(u => u.id === a.id))
          .slice(0, 5 - updated.length);

        return [...updated, ...newActiveAnomalies];
      });

      // 更新回退動作狀態
      setFallbackActions(prev => prev.map(action => {
        if (action.status === 'pending' && Math.random() < 0.3) {
          return { ...action, status: 'executing' };
        }
        if (action.status === 'executing' && Math.random() < 0.4) {
          return { ...action, status: Math.random() < 0.8 ? 'completed' : 'failed' };
        }
        return action;
      }));

      // 更新指標
      const totalAnomalies = anomalies.length;
      const activeAnomalies = anomalies.filter(a => a.status === 'active').length;
      const resolvedAnomalies = anomalies.filter(a => a.status === 'resolved').length;
      const criticalAnomalies = anomalies.filter(a => a.severity === 'critical').length;

      const successfulDecisions = Math.floor(resolvedAnomalies * 0.8) + Math.floor(Math.random() * 5);
      const totalDecisions = Math.floor(totalAnomalies * 1.2) + Math.floor(Math.random() * 10);
      
      setMetrics({
        total_anomalies: totalAnomalies,
        active_anomalies: activeAnomalies,
        resolved_anomalies: resolvedAnomalies,
        critical_anomalies: criticalAnomalies,
        average_resolution_time: 3.2 + Math.random() * 2,
        success_rate: totalAnomalies > 0 ? (resolvedAnomalies / totalAnomalies) * 100 : 0,
        successful_decisions: successfulDecisions,
        total_decisions: totalDecisions
      });
    };

    const interval = setInterval(updateData, 4000 + Math.random() * 3000);
    return () => clearInterval(interval);
  }, [enabled, anomalies, generateRandomAnomaly, generateFallbackAction, soundEnabled]);

  // 獲取過濾後的異常
  const getFilteredAnomalies = () => {
    switch (filter) {
      case 'active':
        return anomalies.filter(a => a.status === 'active');
      case 'critical':
        return anomalies.filter(a => a.severity === 'critical');
      case 'resolved':
        return anomalies.filter(a => a.status === 'resolved');
      default:
        return anomalies;
    }
  };

  // 獲取嚴重程度顏色
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#ff4757';
      case 'high': return '#ff6b35';
      case 'medium': return '#f39c12';
      case 'low': return '#2ed573';
      default: return '#74b9ff';
    }
  };

  // 獲取異常類型圖示
  const getAnomalyIcon = (type: string) => {
    const icons = {
      'timeout': '⏰',
      'signal_degradation': '📶',
      'target_unavailable': '🛑',
      'interference_detected': '📡',
      'network_congestion': '🚦',
      'prediction_failure': '🎯'
    };
    return icons[type as keyof typeof icons] || '⚠️';
  };

  // 獲取狀態圖示
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return '🔴';
      case 'resolved': return '✅';
      case 'escalated': return '🔺';
      default: return '⚪';
    }
  };

  // 手動解決異常
  const resolveAnomaly = (anomalyId: string) => {
    setAnomalies(prev => prev.map(a => 
      a.id === anomalyId ? { ...a, status: 'resolved' as const } : a
    ));
    setActiveAlerts(prev => prev.filter(a => a.id !== anomalyId));
  };

  // 格式化時間
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('zh-TW');
  };

  if (!enabled) return null;

  return (
    <div className={`anomaly-alert-system ${isMinimized ? 'minimized' : ''}`}>
      <div className="alert-header">
        <div className="header-info">
          <h2>🚨 異常監控系統</h2>
          <div className="header-metrics">
            <span className="metric">
              活躍: <strong style={{color: '#ff4757'}}>{metrics.active_anomalies}</strong>
            </span>
            <span className="metric">
              總計: <strong>{metrics.total_anomalies}</strong>
            </span>
            <span className="metric">
              成功率: <strong style={{color: '#2ed573'}}>{metrics.success_rate.toFixed(1)}%</strong>
            </span>
          </div>
        </div>
        
        <div className="header-controls">
          <button
            className={`control-btn ${soundEnabled ? 'active' : ''}`}
            onClick={() => setSoundEnabled(!soundEnabled)}
            title="切換音效"
          >
            {soundEnabled ? '🔊' : '🔇'}
          </button>
          <button
            className="control-btn"
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? '展開' : '最小化'}
          >
            {isMinimized ? '📖' : '📕'}
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* 緊急警報橫幅 */}
          {activeAlerts.length > 0 && (
            <div className="emergency-banner">
              <div className="banner-content">
                <span className="banner-icon">🚨</span>
                <span className="banner-text">
                  檢測到 {activeAlerts.length} 個活躍異常
                </span>
                <div className="banner-actions">
                  {activeAlerts.slice(0, 2).map(alert => (
                    <button
                      key={alert.id}
                      className="quick-resolve-btn"
                      onClick={() => resolveAnomaly(alert.id)}
                    >
                      解決 {alert.ue_id}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 指標卡片 */}
          <div className="metrics-grid">
            <div className="metric-card critical">
              <div className="metric-header">
                <span className="metric-icon">🔥</span>
                <span className="metric-title">嚴重異常</span>
              </div>
              <div className="metric-value">{metrics.critical_anomalies}</div>
              <div className="metric-unit">個</div>
              <div className="metric-change">需立即處理</div>
            </div>
            
            <div className="metric-card success">
              <div className="metric-header">
                <span className="metric-icon">✅</span>
                <span className="metric-title">成功率</span>
              </div>
              <div className="metric-value">{metrics.success_rate.toFixed(1)}</div>
              <div className="metric-unit">%</div>
              <div className="metric-change">{metrics.successful_decisions}/{metrics.total_decisions}</div>
            </div>
            
            <div className="metric-card info">
              <div className="metric-header">
                <span className="metric-icon">⚡</span>
                <span className="metric-title">活躍 / 總計</span>
              </div>
              <div className="metric-value">{metrics.active_anomalies} / {metrics.total_anomalies}</div>
              <div className="metric-unit">異常</div>
              <div className="metric-change">已解決: {metrics.resolved_anomalies}</div>
            </div>
            
            <div className="metric-card warning">
              <div className="metric-header">
                <span className="metric-icon">⏱️</span>
                <span className="metric-title">平均解決時間</span>
              </div>
              <div className="metric-value">{metrics.average_resolution_time.toFixed(1)}</div>
              <div className="metric-unit">秒</div>
              <div className="metric-change">回退策略執行中</div>
            </div>
          </div>

          {/* 篩選器 */}
          <div className="filter-tabs">
            {(['all', 'active', 'critical', 'resolved'] as const).map(filterType => (
              <button
                key={filterType}
                className={`filter-tab ${filter === filterType ? 'active' : ''}`}
                onClick={() => setFilter(filterType)}
              >
                {filterType === 'all' && '全部'}
                {filterType === 'active' && '活躍'}
                {filterType === 'critical' && '嚴重'}
                {filterType === 'resolved' && '已解決'}
              </button>
            ))}
          </div>

          {/* 異常列表 */}
          <div className="anomaly-list">
            <div className="list-header">
              <h3>📋 異常事件列表</h3>
              <span className="count-badge">{getFilteredAnomalies().length}</span>
            </div>
            
            <div className="anomaly-items">
              {getFilteredAnomalies().slice(0, 8).map(anomaly => (
                <div key={anomaly.id} className={`anomaly-item ${anomaly.severity} ${anomaly.status}`}>
                  <div className="anomaly-header">
                    <div className="anomaly-basic-info">
                      <span className="anomaly-icon">{getAnomalyIcon(anomaly.type)}</span>
                      <div className="anomaly-id-time">
                        <span className="anomaly-ue">{anomaly.ue_id}</span>
                        <span className="anomaly-time">{formatTime(anomaly.timestamp)}</span>
                      </div>
                    </div>
                    
                    <div className="anomaly-status-info">
                      <span 
                        className="severity-badge"
                        style={{backgroundColor: getSeverityColor(anomaly.severity)}}
                      >
                        {anomaly.severity.toUpperCase()}
                      </span>
                      <span className="status-icon">{getStatusIcon(anomaly.status)}</span>
                    </div>
                  </div>
                  
                  <div className="anomaly-description">
                    {anomaly.description}
                  </div>
                  
                  <div className="anomaly-details">
                    <div className="signal-metrics">
                      <span className="metric">RSRP: {anomaly.signal_metrics.rsrp?.toFixed(1)}dBm</span>
                      <span className="metric">SINR: {anomaly.signal_metrics.sinr?.toFixed(1)}dB</span>
                    </div>
                    
                    <div className="affected-satellites">
                      影響衛星: {anomaly.affected_satellites.join(', ')}
                    </div>
                  </div>
                  
                  {anomaly.status === 'active' && (
                    <div className="anomaly-actions">
                      <button
                        className="resolve-btn"
                        onClick={() => resolveAnomaly(anomaly.id)}
                      >
                        🔧 手動解決
                      </button>
                      <button className="escalate-btn">
                        🔺 提升等級
                      </button>
                    </div>
                  )}
                  
                  {anomaly.fallback_action && (
                    <div className="fallback-action">
                      <span className="action-icon">🔄</span>
                      <span className="action-text">
                        回退策略: {anomaly.fallback_action.description}
                      </span>
                      <span className="action-confidence">
                        信心度: {(anomaly.fallback_action.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 回退動作狀態 */}
          <div className="fallback-actions">
            <h3>🔄 回退動作狀態</h3>
            <div className="action-items">
              {fallbackActions.slice(0, 5).map(action => (
                <div key={action.action_id} className={`action-item ${action.status}`}>
                  <div className="action-info">
                    <span className="action-strategy">{action.description}</span>
                    <span className="action-time">{formatTime(Date.now())}</span>
                  </div>
                  <div className="action-status">
                    <span className={`status-badge ${action.status}`}>
                      {action.status === 'pending' && '⏳ 待執行'}
                      {action.status === 'executing' && '⚡ 執行中'}
                      {action.status === 'completed' && '✅ 完成'}
                      {action.status === 'failed' && '❌ 失敗'}
                    </span>
                    <span className="confidence">
                      {(action.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AnomalyAlertSystem;