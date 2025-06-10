import React, { useState, useEffect, useRef } from 'react';
import './RealtimePerformanceMonitor.scss';

interface RealtimePerformanceMonitorProps {
  enabled: boolean;
  devices?: any[];
}

interface PerformanceMetrics {
  timestamp: number;
  handover_latency: number;
  success_rate: number;
  prediction_accuracy: number;
  throughput: number;
  signal_strength: number;
  packet_loss: number;
  network_load: number;
  satellite_count: number;
  active_ues: number;
  ml_processing_time: number;
  interference_level: number;
}

interface SystemStatus {
  overall_health: 'excellent' | 'good' | 'warning' | 'critical';
  active_handovers: number;
  failed_handovers: number;
  system_uptime: number;
  ml_model_status: 'active' | 'degraded' | 'offline';
  network_status: 'stable' | 'congested' | 'unstable';
}

interface AlertItem {
  id: string;
  type: 'performance' | 'system' | 'prediction' | 'network';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: number;
  status: 'active' | 'acknowledged' | 'resolved';
}

const RealtimePerformanceMonitor: React.FC<RealtimePerformanceMonitorProps> = ({
  enabled,
  devices = []
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    overall_health: 'good',
    active_handovers: 0,
    failed_handovers: 0,
    system_uptime: 0,
    ml_model_status: 'active',
    network_status: 'stable'
  });
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('1h');
  const [selectedMetric, setSelectedMetric] = useState<string>('handover_latency');
  const [isExpanded, setIsExpanded] = useState(true);

  const chartRef = useRef<HTMLCanvasElement>(null);
  const metricsHistoryRef = useRef<PerformanceMetrics[]>([]);

  // 生成模擬性能數據
  const generateMetrics = (): PerformanceMetrics => {
    const now = Date.now();
    const baseLatency = 45 + Math.random() * 30;
    const networkLoad = Math.random() * 100;
    
    return {
      timestamp: now,
      handover_latency: baseLatency + (networkLoad > 80 ? Math.random() * 20 : 0),
      success_rate: Math.max(85, 99 - (networkLoad > 70 ? Math.random() * 10 : Math.random() * 3)),
      prediction_accuracy: Math.max(88, 96 - Math.random() * 8),
      throughput: Math.max(150, 250 - (networkLoad > 60 ? Math.random() * 80 : Math.random() * 30)),
      signal_strength: -70 - Math.random() * 25,
      packet_loss: Math.max(0, Math.random() * 3 + (networkLoad > 75 ? Math.random() * 2 : 0)),
      network_load: networkLoad,
      satellite_count: 8 + Math.floor(Math.random() * 8),
      active_ues: Math.floor(Math.random() * 12) + 2,
      ml_processing_time: 15 + Math.random() * 10,
      interference_level: Math.random() * 40
    };
  };

  // 生成系統狀態
  const updateSystemStatus = (latestMetrics: PerformanceMetrics) => {
    const newStatus: SystemStatus = {
      overall_health: latestMetrics.success_rate > 95 ? 'excellent' :
                     latestMetrics.success_rate > 90 ? 'good' :
                     latestMetrics.success_rate > 85 ? 'warning' : 'critical',
      active_handovers: Math.floor(Math.random() * 8) + 2,
      failed_handovers: Math.floor(Math.random() * 3),
      system_uptime: Date.now() - (Date.now() - 86400000 * 7), // 7 days
      ml_model_status: latestMetrics.prediction_accuracy > 90 ? 'active' :
                      latestMetrics.prediction_accuracy > 80 ? 'degraded' : 'offline',
      network_status: latestMetrics.network_load < 70 ? 'stable' :
                     latestMetrics.network_load < 85 ? 'congested' : 'unstable'
    };
    
    setSystemStatus(newStatus);
  };

  // 生成警報
  const checkAndGenerateAlerts = (metrics: PerformanceMetrics) => {
    const newAlerts: AlertItem[] = [];

    if (metrics.handover_latency > 80) {
      newAlerts.push({
        id: `alert_${Date.now()}_latency`,
        type: 'performance',
        severity: metrics.handover_latency > 100 ? 'critical' : 'high',
        message: `換手延遲過高: ${metrics.handover_latency.toFixed(1)}ms`,
        timestamp: Date.now(),
        status: 'active'
      });
    }

    if (metrics.success_rate < 90) {
      newAlerts.push({
        id: `alert_${Date.now()}_success`,
        type: 'system',
        severity: metrics.success_rate < 85 ? 'critical' : 'medium',
        message: `換手成功率下降: ${metrics.success_rate.toFixed(1)}%`,
        timestamp: Date.now(),
        status: 'active'
      });
    }

    if (metrics.packet_loss > 2) {
      newAlerts.push({
        id: `alert_${Date.now()}_packet`,
        type: 'network',
        severity: metrics.packet_loss > 4 ? 'high' : 'medium',
        message: `封包遺失率偏高: ${metrics.packet_loss.toFixed(1)}%`,
        timestamp: Date.now(),
        status: 'active'
      });
    }

    if (metrics.prediction_accuracy < 85) {
      newAlerts.push({
        id: `alert_${Date.now()}_prediction`,
        type: 'prediction',
        severity: metrics.prediction_accuracy < 80 ? 'high' : 'medium',
        message: `預測精度下降: ${metrics.prediction_accuracy.toFixed(1)}%`,
        timestamp: Date.now(),
        status: 'active'
      });
    }

    if (newAlerts.length > 0) {
      setAlerts(prev => [...newAlerts, ...prev.slice(0, 19)]);
    }
  };

  // 獲取指標顏色
  const getMetricColor = (value: number, metric: string) => {
    switch (metric) {
      case 'handover_latency':
        return value < 50 ? '#52c41a' : value < 80 ? '#faad14' : '#ff4d4f';
      case 'success_rate':
        return value > 95 ? '#52c41a' : value > 90 ? '#faad14' : '#ff4d4f';
      case 'prediction_accuracy':
        return value > 90 ? '#52c41a' : value > 85 ? '#faad14' : '#ff4d4f';
      case 'packet_loss':
        return value < 1 ? '#52c41a' : value < 3 ? '#faad14' : '#ff4d4f';
      default:
        return '#1890ff';
    }
  };

  // 獲取狀態指示器
  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'excellent': return { icon: '🟢', text: '優秀', color: '#52c41a' };
      case 'good': return { icon: '🔵', text: '良好', color: '#1890ff' };
      case 'warning': return { icon: '🟡', text: '警告', color: '#faad14' };
      case 'critical': return { icon: '🔴', text: '嚴重', color: '#ff4d4f' };
      case 'active': return { icon: '✅', text: '正常', color: '#52c41a' };
      case 'degraded': return { icon: '⚠️', text: '降級', color: '#faad14' };
      case 'offline': return { icon: '❌', text: '離線', color: '#ff4d4f' };
      case 'stable': return { icon: '📶', text: '穩定', color: '#52c41a' };
      case 'congested': return { icon: '🚦', text: '擁塞', color: '#faad14' };
      case 'unstable': return { icon: '📴', text: '不穩定', color: '#ff4d4f' };
      default: return { icon: '⚪', text: '未知', color: '#666' };
    }
  };

  // 格式化時間
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('zh-TW');
  };

  // 格式化運行時間
  const formatUptime = (uptime: number) => {
    const days = Math.floor(uptime / (1000 * 60 * 60 * 24));
    const hours = Math.floor((uptime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    return `${days}天 ${hours}小時`;
  };

  // 數據更新
  useEffect(() => {
    if (!enabled) return;

    const updateData = () => {
      const newMetrics = generateMetrics();
      
      setMetrics(prev => {
        const updated = [newMetrics, ...prev.slice(0, 99)];
        metricsHistoryRef.current = updated;
        return updated;
      });

      updateSystemStatus(newMetrics);
      
      // 20% 機率生成警報
      if (Math.random() < 0.2) {
        checkAndGenerateAlerts(newMetrics);
      }
    };

    // 初始數據
    updateData();

    // 定期更新
    const interval = setInterval(updateData, 2000);
    return () => clearInterval(interval);
  }, [enabled]);

  // 清除警報
  const dismissAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  if (!enabled) return null;

  const latestMetrics = metrics[0];

  return (
    <div className={`realtime-performance-monitor ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div className="monitor-header">
        <div className="header-info">
          <h2>⚡ 即時性能監控</h2>
          <div className="system-health">
            <span className="health-indicator">
              {getStatusIndicator(systemStatus.overall_health).icon}
              系統狀態: {getStatusIndicator(systemStatus.overall_health).text}
            </span>
            <span className="uptime">
              運行時間: {formatUptime(systemStatus.system_uptime)}
            </span>
          </div>
        </div>
        
        <div className="header-controls">
          <select 
            value={selectedTimeRange} 
            onChange={(e) => setSelectedTimeRange(e.target.value)}
          >
            <option value="5m">5分鐘</option>
            <option value="15m">15分鐘</option>
            <option value="1h">1小時</option>
            <option value="6h">6小時</option>
          </select>
          
          <button
            className="expand-btn"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? '📕' : '📖'}
          </button>
        </div>
      </div>

      {isExpanded && latestMetrics && (
        <>
          {/* 核心指標卡片 */}
          <div className="core-metrics">
            <div className="metric-card primary">
              <div className="metric-icon">⚡</div>
              <div className="metric-content">
                <span className="metric-label">換手延遲</span>
                <span 
                  className="metric-value"
                  style={{color: getMetricColor(latestMetrics.handover_latency, 'handover_latency')}}
                >
                  {latestMetrics.handover_latency.toFixed(1)}ms
                </span>
                <span className="metric-trend">
                  {metrics.length > 1 && latestMetrics.handover_latency < metrics[1].handover_latency ? '📈' : '📉'}
                </span>
              </div>
            </div>

            <div className="metric-card primary">
              <div className="metric-icon">✅</div>
              <div className="metric-content">
                <span className="metric-label">成功率</span>
                <span 
                  className="metric-value"
                  style={{color: getMetricColor(latestMetrics.success_rate, 'success_rate')}}
                >
                  {latestMetrics.success_rate.toFixed(1)}%
                </span>
                <span className="metric-trend">
                  {metrics.length > 1 && latestMetrics.success_rate > metrics[1].success_rate ? '📈' : '📉'}
                </span>
              </div>
            </div>

            <div className="metric-card primary">
              <div className="metric-icon">🎯</div>
              <div className="metric-content">
                <span className="metric-label">預測精度</span>
                <span 
                  className="metric-value"
                  style={{color: getMetricColor(latestMetrics.prediction_accuracy, 'prediction_accuracy')}}
                >
                  {latestMetrics.prediction_accuracy.toFixed(1)}%
                </span>
                <span className="metric-trend">
                  {metrics.length > 1 && latestMetrics.prediction_accuracy > metrics[1].prediction_accuracy ? '📈' : '📉'}
                </span>
              </div>
            </div>

            <div className="metric-card primary">
              <div className="metric-icon">📦</div>
              <div className="metric-content">
                <span className="metric-label">封包遺失</span>
                <span 
                  className="metric-value"
                  style={{color: getMetricColor(latestMetrics.packet_loss, 'packet_loss')}}
                >
                  {latestMetrics.packet_loss.toFixed(1)}%
                </span>
                <span className="metric-trend">
                  {metrics.length > 1 && latestMetrics.packet_loss < metrics[1].packet_loss ? '📈' : '📉'}
                </span>
              </div>
            </div>
          </div>

          {/* 系統狀態概覽 */}
          <div className="system-overview">
            <h3>🖥️ 系統狀態概覽</h3>
            <div className="status-grid">
              <div className="status-item">
                <span className="status-label">ML模型狀態</span>
                <span 
                  className="status-value"
                  style={{color: getStatusIndicator(systemStatus.ml_model_status).color}}
                >
                  {getStatusIndicator(systemStatus.ml_model_status).icon} 
                  {getStatusIndicator(systemStatus.ml_model_status).text}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">網路狀態</span>
                <span 
                  className="status-value"
                  style={{color: getStatusIndicator(systemStatus.network_status).color}}
                >
                  {getStatusIndicator(systemStatus.network_status).icon} 
                  {getStatusIndicator(systemStatus.network_status).text}
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">活躍換手</span>
                <span className="status-value">{systemStatus.active_handovers} 個</span>
              </div>

              <div className="status-item">
                <span className="status-label">失敗換手</span>
                <span className="status-value" style={{color: systemStatus.failed_handovers > 5 ? '#ff4d4f' : '#52c41a'}}>
                  {systemStatus.failed_handovers} 個
                </span>
              </div>

              <div className="status-item">
                <span className="status-label">衛星數量</span>
                <span className="status-value">{latestMetrics.satellite_count} 顆</span>
              </div>

              <div className="status-item">
                <span className="status-label">活躍UE</span>
                <span className="status-value">{latestMetrics.active_ues} 個</span>
              </div>
            </div>
          </div>

          {/* 性能圖表區域 */}
          <div className="performance-chart">
            <div className="chart-header">
              <h3>📊 性能趨勢圖</h3>
              <select 
                value={selectedMetric} 
                onChange={(e) => setSelectedMetric(e.target.value)}
              >
                <option value="handover_latency">換手延遲</option>
                <option value="success_rate">成功率</option>
                <option value="prediction_accuracy">預測精度</option>
                <option value="throughput">吞吐量</option>
                <option value="packet_loss">封包遺失率</option>
                <option value="network_load">網路負載</option>
              </select>
            </div>
            
            <div className="chart-container">
              <canvas ref={chartRef} width="400" height="150"></canvas>
              <div className="chart-placeholder">
                <p>📈 即時性能趨勢圖</p>
                <div className="trend-summary">
                  {metrics.slice(0, 10).map((metric, index) => (
                    <div key={index} className="trend-point" style={{
                      height: `${(metric[selectedMetric as keyof PerformanceMetrics] as number / 100) * 60}px`,
                      backgroundColor: getMetricColor(metric[selectedMetric as keyof PerformanceMetrics] as number, selectedMetric)
                    }}></div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 即時警報 */}
          <div className="realtime-alerts">
            <div className="alerts-header">
              <h3>🚨 即時警報</h3>
              <span className="alerts-count">{alerts.filter(a => a.status === 'active').length} 個活躍</span>
            </div>
            
            <div className="alerts-list">
              {alerts.slice(0, 5).map(alert => (
                <div key={alert.id} className={`alert-item ${alert.severity} ${alert.status}`}>
                  <div className="alert-content">
                    <div className="alert-header">
                      <span className="alert-type">
                        {alert.type === 'performance' && '⚡'}
                        {alert.type === 'system' && '🖥️'}
                        {alert.type === 'prediction' && '🎯'}
                        {alert.type === 'network' && '🌐'}
                      </span>
                      <span className="alert-severity">{alert.severity.toUpperCase()}</span>
                      <span className="alert-time">{formatTime(alert.timestamp)}</span>
                    </div>
                    <p className="alert-message">{alert.message}</p>
                  </div>
                  
                  <button 
                    className="dismiss-btn"
                    onClick={() => dismissAlert(alert.id)}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* 詳細指標 */}
          <div className="detailed-metrics">
            <h3>📋 詳細指標</h3>
            <div className="metrics-table">
              <div className="metric-row">
                <span className="metric-name">吞吐量</span>
                <span className="metric-val">{latestMetrics.throughput.toFixed(1)} Mbps</span>
              </div>
              <div className="metric-row">
                <span className="metric-name">信號強度</span>
                <span className="metric-val">{latestMetrics.signal_strength.toFixed(1)} dBm</span>
              </div>
              <div className="metric-row">
                <span className="metric-name">網路負載</span>
                <span className="metric-val">{latestMetrics.network_load.toFixed(1)}%</span>
              </div>
              <div className="metric-row">
                <span className="metric-name">ML處理時間</span>
                <span className="metric-val">{latestMetrics.ml_processing_time.toFixed(1)}ms</span>
              </div>
              <div className="metric-row">
                <span className="metric-name">干擾等級</span>
                <span className="metric-val">{latestMetrics.interference_level.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default RealtimePerformanceMonitor;