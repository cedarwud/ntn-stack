import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { dynamicPoolService } from '../../services/DynamicPoolService';
import { UnifiedSatelliteInfo, SatelliteDataService } from '../../services/satelliteDataService';
import { useDataSync } from '../../contexts/DataSyncContext';
import { useSatelliteState } from '../../contexts/appStateHooks';
import { Play, Pause, RotateCcw, Settings, BarChart3, ChevronDown, ChevronUp } from 'lucide-react';
import '../../styles/SatelliteVisibilitySimplified.scss';

interface SatelliteVisibilitySimplifiedProps {
  className?: string;
}

interface VisibilityStats {
  total: number;
  starlink: number;
  oneweb: number;
  starlinkVisible: number;
  onewebVisible: number;
  totalVisible: number;
}

interface StageStatistics {
  stage: number;
  stage_name: string;
  status: string;
  total_satellites: number;
  starlink_count: number;
  oneweb_count: number;
  processing_time?: string;
  output_file_size_mb?: number;
  last_updated?: string;
  error_message?: string;
  tle_data_date?: string;  // TLE數據來源日期
  execution_time?: string; // 實際執行時間
}

interface PipelineStatistics {
  metadata: {
    analysis_timestamp: string;
    analyzer_version: string;
  };
  stages: StageStatistics[];
  summary: {
    total_stages: number;
    successful_stages: number;
    failed_stages: number;
    no_data_stages: number;
    data_flow: Array<{
      stage: number;
      satellites: number;
      starlink: number;
      oneweb: number;
    }>;
    final_output: number;
    pipeline_health: string;
    data_retention_rate?: number;
    data_loss_rate?: number;
  };
}

const SatelliteVisibilitySimplified: React.FC<SatelliteVisibilitySimplifiedProps> = ({ 
  className = '' 
}) => {
  // 狀態管理
  const [selectedConstellation, setSelectedConstellation] = useState<'starlink' | 'oneweb' | 'both'>('both');
  const [isAnimating, setIsAnimating] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(60); // 秒/小時
  const [currentTime, setCurrentTime] = useState(new Date());
  const [visibleSatellites, setVisibleSatellites] = useState<UnifiedSatelliteInfo[]>([]);
  const [visibilityStats, setVisibilityStats] = useState<VisibilityStats>({ 
    total: 0, 
    starlink: 0, 
    oneweb: 0, 
    starlinkVisible: 0, 
    onewebVisible: 0, 
    totalVisible: 0 
  });
  const [poolInfo, setPoolInfo] = useState<any>(null);
  const [displayMode, setDisplayMode] = useState<'satellites' | 'pipeline'>('pipeline');
  const [pipelineStats, setPipelineStats] = useState<PipelineStatistics | null>(null);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [satelliteListCollapsed, setSatelliteListCollapsed] = useState(true); // 預設收合

  // 使用數據同步上下文和衛星狀態
  const { state } = useDataSync();
  const satelliteState = useSatelliteState();
  
  // 只在關鍵狀態變化時輸出調試信息
  useEffect(() => {
    if (state.error) {
      console.log('❌ DataSync 錯誤:', state.error);
    }
  }, [state.error]);

  // 自動啟用衛星數據（只執行一次）
  useEffect(() => {
    if (!satelliteState.satelliteEnabled) {
      satelliteState.setSatelliteEnabled(true);
    }
  }, [satelliteState.satelliteEnabled, satelliteState]);

  // 初始化動態池服務
  useEffect(() => {
    const initializePool = async () => {
      try {
        await dynamicPoolService.loadDynamicPool();
        const stats = dynamicPoolService.getPoolStatistics();
        setPoolInfo(stats);
      } catch (error) {
        console.error('❌ 動態池載入失敗:', error);
      }
    };
    initializePool();
  }, []);

  // 時間更新效果 - 使用歷史基準時間
  useEffect(() => {
    if (!isAnimating) return;

    const interval = setInterval(() => {
      setCurrentTime(prev => new Date(prev.getTime() + (speedMultiplier * 1000)));
    }, 1000);

    return () => clearInterval(interval);
  }, [isAnimating, speedMultiplier]);

  // 初始化為歷史時間（TLE數據的有效範圍）
  useEffect(() => {
    // 設置為2025年8月31日的歷史時間，對應實際TLE數據日期
    setCurrentTime(new Date('2025-08-31T12:00:00Z'));
  }, []);

  // 載入衛星數據服務實例
  const satelliteDataService = useMemo(() => {
    return SatelliteDataService.getInstance();
  }, []);

  // 獲取管道統計 - 移除 displayMode 依賴以避免重複載入
  const loadPipelineStatistics = useCallback(async () => {
    setPipelineLoading(true);
    try {
      const { netstackFetch } = await import('../../config/api-config');
      const response = await netstackFetch('/api/v1/pipeline/statistics');
      
      if (!response.ok) {
        throw new Error(`管道統計 API 錯誤: ${response.status}`);
      }
      
      const data: PipelineStatistics = await response.json();
      setPipelineStats(data);
      
      console.log('📊 管道統計載入成功:', data.summary.pipeline_health);
    } catch (error) {
      console.error('❌ 管道統計載入失敗:', error);
      setPipelineStats(null);
    } finally {
      setPipelineLoading(false);
    }
  }, []); // 移除所有依賴

  // 載入管道統計（當切換到管道視圖時）
  useEffect(() => {
    if (displayMode === 'pipeline') {
      console.log('📊 初次載入管道統計');
      loadPipelineStatistics();
      
      // 每5分鐘刷新一次管道統計（減少頻率）
      const interval = setInterval(() => {
        console.log('🔄 定期刷新管道統計');
        loadPipelineStatistics();
      }, 300000); // 5分鐘 = 300000ms
      return () => {
        console.log('🛑 清理管道統計刷新定時器');
        clearInterval(interval);
      };
    }
  }, [displayMode]); // 只依賴 displayMode

  // 載入階段六動態池數據 - 包含完整時間序列
  const loadSatelliteData = useCallback(async (constellation: 'starlink' | 'oneweb' | 'both', time: Date) => {
    try {
      let allSatellites: UnifiedSatelliteInfo[] = [];
      
      // 計算時間偏移秒數（從基準時間2025-08-31開始）
      const baseTime = new Date('2025-08-31T12:00:00Z');
      const timeOffsetSeconds = Math.floor((time.getTime() - baseTime.getTime()) / 1000);
      
      // 確保動態池數據已載入完成
      await dynamicPoolService.loadDynamicPool();
      
      // 優先使用動態池優化數據
      if (dynamicPoolService.shouldUseOptimizedPool()) {
        console.log(`🎯 使用階段六動態池數據 (優化方案)，時間: ${time.toISOString()}`);
        
        // 使用階段六動態池API獲取優化後的衛星數據
        const { netstackFetch } = await import('../../config/api-config');
        const response = await netstackFetch(`/api/v1/satellite/unified?constellation=${constellation}&count=20&time=${time.toISOString()}`);
        
        if (!response.ok) {
          throw new Error(`動態池API錯誤: ${response.status}`);
        }
        
        const data = await response.json();
        allSatellites = data.satellites || [];
        
        // 使用動態池過濾衛星
        allSatellites = dynamicPoolService.filterSatellitesByPool(allSatellites);
        
      } else {
        console.log(`🎯 使用全量數據API (回退方案)，時間: ${time.toISOString()}`);
        
        // 回退方案：使用全量數據API
        const { netstackFetch } = await import('../../config/api-config');
        const response = await netstackFetch(`/api/v1/satellite/unified?constellation=${constellation}&count=20&time=${time.toISOString()}`);
        
        if (!response.ok) {
          throw new Error(`全量衛星API錯誤: ${response.status}`);
        }
        
        const data = await response.json();
        allSatellites = data.satellites || [];
      }
      
      console.log(`✅ 衛星數據載入: ${allSatellites.length} 顆衛星`);
      console.log(`📊 數據源: ${dynamicPoolService.shouldUseOptimizedPool() ? '階段六動態池' : '全量數據API'}`);
    
      
      return allSatellites;
    } catch (error) {
      console.error('❌ 全量衛星數據載入失敗:', error);
      return [];
    }
  }, []);

  // 更新可見衛星列表 - 使用真實SGP4軌道計算
  useEffect(() => {
    const updateSatelliteData = async () => {
      try {
        // 載入真實的衛星軌道數據
        const satellites = await loadSatelliteData(selectedConstellation, currentTime);
        setVisibleSatellites(satellites);

        // 計算統計資訊 - 分離可見和總計
        const starlinkSats = satellites.filter(s => s.constellation === 'starlink');
        const onewebSats = satellites.filter(s => s.constellation === 'oneweb');
        
        const stats = {
          total: satellites.length,
          starlink: starlinkSats.length,
          oneweb: onewebSats.length,
          starlinkVisible: starlinkSats.filter(s => s.is_visible).length,
          onewebVisible: onewebSats.filter(s => s.is_visible).length,
          totalVisible: satellites.filter(s => s.is_visible).length
        };
        
        // 只在統計有實際變化時顯示總覽和更新狀態
        if (visibilityStats.total !== stats.total || visibilityStats.starlink !== stats.starlink || visibilityStats.oneweb !== stats.oneweb) {
          setVisibilityStats(stats);
          console.log(`📊 真實軌道計算結果: ${stats.total}顆 (Starlink: ${stats.starlink}, OneWeb: ${stats.oneweb}) - 時間: ${currentTime.toLocaleString()}`);
        }
      } catch (error) {
        console.error('❌ 衛星數據更新失敗:', error);
      }
    };

    updateSatelliteData();
  }, [selectedConstellation, currentTime, loadSatelliteData, visibilityStats]);

  // 控制函數
  const handlePlayPause = () => {
    setIsAnimating(!isAnimating);
  };

  const handleReset = () => {
    setCurrentTime(new Date());
    setIsAnimating(false);
  };

  const handleSpeedChange = (newSpeed: number) => {
    setSpeedMultiplier(newSpeed);
  };

  return (
    <div className={`satellite-visibility-simplified ${className}`}>
      {/* 控制面板 */}
      <Card className="control-panel">
        <div className="control-row">
          <div className="view-controls">
            <Button
              onClick={() => setDisplayMode('satellites')}
              variant={displayMode === 'satellites' ? "default" : "outline"}
              size="sm"
            >
              <Settings className="w-4 h-4" />
              衛星視圖
            </Button>
            <Button
              onClick={() => setDisplayMode('pipeline')}
              variant={displayMode === 'pipeline' ? "default" : "outline"}
              size="sm"
            >
              <BarChart3 className="w-4 h-4" />
              管道統計
            </Button>
          </div>

          {displayMode === 'satellites' && (
            <>
              <div className="time-controls">
                <Button onClick={handlePlayPause} variant="outline" size="sm">
                  {isAnimating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  {isAnimating ? '暫停' : '播放'}
                </Button>
                <Button onClick={handleReset} variant="outline" size="sm">
                  <RotateCcw className="w-4 h-4" />
                  重置
                </Button>
              </div>
              
              <div className="speed-controls">
                <span className="speed-label">速度:</span>
                {[1, 60, 300, 3600].map(speed => (
                  <Button
                    key={speed}
                    onClick={() => handleSpeedChange(speed)}
                    variant={speedMultiplier === speed ? "default" : "outline"}
                    size="sm"
                  >
                    {speed < 60 ? `${speed}s` : speed < 3600 ? `${speed/60}m` : `${speed/3600}h`}
                  </Button>
                ))}
              </div>

              <div className="constellation-filter">
                <span className="filter-label">星座:</span>
                {[
                  { key: 'both' as const, label: '全部' },
                  { key: 'starlink' as const, label: 'Starlink' },
                  { key: 'oneweb' as const, label: 'OneWeb' }
                ].map(option => (
                  <Button
                    key={option.key}
                    onClick={() => setSelectedConstellation(option.key)}
                    variant={selectedConstellation === option.key ? "default" : "outline"}
                    size="sm"
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
            </>
          )}
        </div>
      </Card>

      {/* 狀態面板 */}
      {displayMode === 'satellites' ? (
        <Card className="status-panel">
          <div className="status-row">
            <div className="time-display">
              <strong>當前時間:</strong> {currentTime.toLocaleString()}
            </div>
            
            <div className="visibility-stats">
              <Badge variant="outline" className="stat-badge">
                總衛星: {visibilityStats.totalVisible}/{visibilityStats.total}
              </Badge>
              <Badge variant="outline" className="stat-badge starlink">
                Starlink: {visibilityStats.starlinkVisible}/{visibilityStats.starlink}
              </Badge>
              <Badge variant="outline" className="stat-badge oneweb">
                OneWeb: {visibilityStats.onewebVisible}/{visibilityStats.oneweb}
              </Badge>
            </div>

            {poolInfo && (
              <div className="pool-info">
                <Badge variant="outline" className="pool-badge">
                  動態池: {poolInfo.mode === 'optimized' ? '已優化' : '全量'} ({poolInfo.total}顆)
                </Badge>
              </div>
            )}
          </div>
        </Card>
      ) : (
        <Card className="pipeline-summary-panel">
          <div className="pipeline-summary">
            {pipelineLoading ? (
              <div className="loading-message">🔄 載入管道統計中...</div>
            ) : pipelineStats ? (
              <>
                <div className="pipeline-header">
                  <h3>六階段數據處理管道</h3>
                  <Badge 
                    variant={
                      pipelineStats.summary.pipeline_health === 'healthy' ? 'default' : 
                      pipelineStats.summary.pipeline_health === 'degraded' ? 'secondary' : 'destructive'
                    }
                  >
                    {pipelineStats.summary.pipeline_health === 'healthy' ? '正常' :
                     pipelineStats.summary.pipeline_health === 'degraded' ? '降級' : '故障'}
                  </Badge>
                </div>
                <div className="pipeline-metrics">
                  <Badge variant="outline" className="metric-badge">
                    成功階段: {pipelineStats.summary.successful_stages}/{pipelineStats.summary.total_stages}
                  </Badge>
                  <Badge variant="outline" className="metric-badge">
                    最終輸出: {pipelineStats.summary.final_output} 顆衛星
                  </Badge>
                  {pipelineStats.summary.data_retention_rate && (
                    <Badge variant="outline" className="metric-badge">
                      數據保留率: {pipelineStats.summary.data_retention_rate}%
                    </Badge>
                  )}
                  <Badge variant="outline" className="metric-badge">
                    更新時間: {new Date(pipelineStats.metadata.analysis_timestamp).toLocaleString()}
                  </Badge>
                </div>
              </>
            ) : (
              <div className="error-message">❌ 管道統計載入失敗</div>
            )}
          </div>
        </Card>
      )}

      {/* 主要內容區域 */}
      {displayMode === 'satellites' ? (
        <Card className="satellite-list">
          <div className="list-header" onClick={() => setSatelliteListCollapsed(!satelliteListCollapsed)}>
            <div className="header-content">
              <h3>可見衛星列表</h3>
              <Badge variant="secondary">{visibleSatellites.length} 顆衛星</Badge>
            </div>
            <Button variant="ghost" size="sm" className="collapse-button">
              {satelliteListCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </Button>
          </div>
          
          {!satelliteListCollapsed && (
            <div className="satellite-grid">
              {visibleSatellites.slice(0, 20).map((sat, index) => (
                <div key={`${sat.constellation}-${sat.id || sat.norad_id}-${index}`} className="satellite-item">
                  <div className="sat-header">
                    <span className="sat-name">{sat.name}</span>
                    <Badge 
                      variant="outline" 
                      className={`constellation-badge ${sat.constellation?.toLowerCase()}`}
                    >
                      {sat.constellation?.toUpperCase() || 'UNKNOWN'}
                    </Badge>
                  </div>
                  <div className="sat-details">
                    <span>仰角: {sat.elevation_deg?.toFixed(1)}°</span>
                    <span>方位: {sat.azimuth_deg?.toFixed(1)}°</span>
                    <span>距離: {sat.distance_km?.toFixed(0)}km</span>
                    <span>信號: {sat.signal_strength?.toFixed(1)}dBm</span>
                  </div>
                </div>
              ))}
              
              {visibleSatellites.length > 20 && (
                <div className="more-satellites">
                  還有 {visibleSatellites.length - 20} 顆衛星...
                </div>
              )}
              
              {visibleSatellites.length === 0 && (
                <div className="no-satellites">
                  目前沒有可見的衛星 (使用全量數據API - 即時軌道計算)
                </div>
              )}
            </div>
          )}
        </Card>
      ) : (
        <Card className="pipeline-stages">
          <div className="stages-header">
            <h3>階段處理統計</h3>
            <Button onClick={loadPipelineStatistics} variant="outline" size="sm" disabled={pipelineLoading}>
              <RotateCcw className="w-4 h-4" />
              刷新
            </Button>
          </div>
          
          {pipelineLoading ? (
            <div className="pipeline-loading">
              <div className="loading-spinner">🔄</div>
              <span>載入管道統計中...</span>
            </div>
          ) : pipelineStats ? (
            <div className="pipeline-layout">
              {/* 第一行：所有階段 1-6 */}
              <div className="stages-single-row">
                <h4 className="row-title">六階段處理管道</h4>
                <div className="stages-single-row-content">
                  {pipelineStats.stages.map((stage) => {
                    // 修正狀態判斷：0顆衛星應該顯示為異常
                    const actualStatus = stage.total_satellites === 0 ? 'warning' : stage.status;
                    return (
                      <div 
                        key={stage.stage} 
                        className={`stage-item-compact ${actualStatus}`}
                      >
                        <div className="stage-compact-header">
                          <span className="stage-number">階段 {stage.stage}</span>
                          <Badge 
                            variant={
                              actualStatus === 'success' ? 'default' : 
                              actualStatus === 'failed' ? 'destructive' : 
                              actualStatus === 'warning' ? 'secondary' : 'secondary'
                            }
                          >
                            {actualStatus === 'success' ? '✅' :
                             actualStatus === 'failed' ? '❌' : 
                             actualStatus === 'warning' ? '⚠️' : '❓'}
                          </Badge>
                        </div>
                        <div className="stage-compact-title">{stage.stage_name}</div>
                        <div className="stage-compact-stats">
                          <div className="compact-stat">🛰️ {stage.total_satellites}</div>
                          <div className="compact-stat">⭐ {stage.starlink_count}</div>
                          <div className="compact-stat">🔵 {stage.oneweb_count}</div>
                          {stage.tle_data_date && (
                            <div className="compact-stat">📅 {stage.tle_data_date}</div>
                          )}
                          {stage.last_updated && (
                            <div className="compact-stat">⏰ {new Date(stage.last_updated).toLocaleString('zh-TW', {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'})}</div>
                          )}
                        </div>
                        {stage.error_message && (
                          <div className="stage-compact-error">❌ {stage.error_message}</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
              
              {/* 第二行：數據流向圖 */}
              {pipelineStats.summary.data_flow.length > 1 && (
                <div className="data-flow-row">
                  <h4 className="flow-title">數據流向圖</h4>
                  <div className="flow-diagram">
                    {pipelineStats.summary.data_flow.map((stage, index) => (
                      <div key={stage.stage} className="flow-stage">
                        <div className="flow-stage-number">階段 {stage.stage}</div>
                        <div className="flow-stage-count">{stage.satellites}顆</div>
                        <div className="flow-stage-details">
                          <span className="flow-starlink">Starlink: {stage.starlink}</span>
                          <span className="flow-oneweb">OneWeb: {stage.oneweb}</span>
                        </div>
                        {index < pipelineStats.summary.data_flow.length - 1 && (
                          <div className="flow-arrow">→</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="pipeline-error">
              ❌ 無法載入管道統計數據
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default SatelliteVisibilitySimplified;