# 05 - Phase 4: 前端時間軸控制

> **上一階段**：[Phase 3 - API 端點](./04-phase3-api-endpoints.md) | **下一階段**：[Phase 5 - 容器啟動](./06-phase5-container-startup.md)

## 🎯 Phase 4 目標
**目標**：實現前端星座切換控制器和時間軸控制器組件，支援多星座分析和時間軸播放
**預估時間**: 2-3 天

## 📋 開發任務

### 4.1 增強型星座選擇器（多星座支援）

#### **完整的星座選擇器實現**
```typescript
// ConstellationSelector.tsx (增強版)
import React, { useState, useEffect } from 'react';
import { Select, Badge, Alert, Card, Statistic, Row, Col } from 'antd';
import { SatelliteOutlined, GlobalOutlined } from '@ant-design/icons';

interface ConstellationInfo {
  name: string;
  displayName: string;
  color: string;
  icon: React.ReactNode;
  satelliteCount: number;
  coverage: string;
  orbitAltitude: string;
  latency: string;
  dataAvailability: {
    start: string;
    end: string;
    totalDays: number;
  };
}

const CONSTELLATION_CONFIGS: Record<string, ConstellationInfo> = {
  starlink: {
    name: 'starlink',
    displayName: 'Starlink',
    color: '#1890ff',
    icon: <SatelliteOutlined />,
    satelliteCount: 0,
    coverage: '全球覆蓋 (±70°)',
    orbitAltitude: '550km',
    latency: '20-40ms',
    dataAvailability: { start: '', end: '', totalDays: 0 }
  },
  oneweb: {
    name: 'oneweb',
    displayName: 'OneWeb', 
    color: '#52c41a',
    icon: <GlobalOutlined />,
    satelliteCount: 0,
    coverage: '極地覆蓋 (±88°)',
    orbitAltitude: '1200km',
    latency: '32-50ms',
    dataAvailability: { start: '', end: '', totalDays: 0 }
  }
};

interface Props {
  value: string;
  onChange: (constellation: string) => void;
  disabled?: boolean;
  showComparison?: boolean;
}

export const ConstellationSelector: React.FC<Props> = ({ 
  value, 
  onChange, 
  disabled = false,
  showComparison = true
}) => {
  const [constellations, setConstellations] = useState(CONSTELLATION_CONFIGS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchConstellationData = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/satellites/constellations/info');
        const data = await response.json();
        
        const updated = { ...constellations };
        data.forEach((item: any) => {
          if (updated[item.constellation]) {
            updated[item.constellation].satelliteCount = item.satellite_count;
            updated[item.constellation].dataAvailability = {
              start: item.data_start,
              end: item.data_end,
              totalDays: item.total_days
            };
          }
        });
        setConstellations(updated);
      } catch (error) {
        console.error('Failed to fetch constellation data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchConstellationData();
  }, []);

  const handleChange = (newValue: string) => {
    if (!disabled) {
      onChange(newValue);
    }
  };

  const selectedConstellation = constellations[value];

  return (
    <div className="constellation-selector">
      <div className="selector-header mb-3">
        <span className="text-base font-semibold text-gray-800">
          🛰️ LEO 衛星星座系統
        </span>
        {loading && <span className="ml-2 text-sm text-blue-500">載入中...</span>}
      </div>
      
      <Select
        value={value}
        onChange={handleChange}
        disabled={disabled || loading}
        className="w-full"
        placeholder="選擇星座系統"
        size="large"
        optionLabelProp="label"
      >
        {Object.entries(constellations).map(([key, info]) => (
          <Select.Option 
            key={key} 
            value={key}
            label={
              <div className="flex items-center">
                <span style={{ color: info.color, fontSize: '16px' }}>
                  {info.icon}
                </span>
                <span className="ml-2 font-medium">{info.displayName}</span>
                {info.satelliteCount > 0 && (
                  <Badge 
                    count={info.satelliteCount} 
                    size="small" 
                    className="ml-2"
                    style={{ backgroundColor: info.color }}
                  />
                )}
              </div>
            }
          >
            <div className="constellation-option py-2">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span style={{ color: info.color, fontSize: '18px' }}>
                    {info.icon}
                  </span>
                  <span className="ml-2 font-semibold text-gray-800">
                    {info.displayName}
                  </span>
                </div>
                {info.satelliteCount > 0 && (
                  <Badge 
                    count={info.satelliteCount} 
                    size="small"
                    style={{ backgroundColor: info.color }}
                  />
                )}
              </div>
              
              <div className="text-sm text-gray-600 space-y-1">
                <div>📍 覆蓋: {info.coverage}</div>
                <div>🚀 高度: {info.orbitAltitude}</div>
                <div>⚡ 延遲: {info.latency}</div>
                {info.dataAvailability.totalDays > 0 && (
                  <div>📊 數據: {info.dataAvailability.totalDays} 天</div>
                )}
              </div>
            </div>
          </Select.Option>
        ))}
      </Select>
      
      {selectedConstellation && (
        <Card className="mt-4" size="small">
          <Row gutter={16}>
            <Col span={18}>
              <div className="flex items-center mb-3">
                <span style={{ color: selectedConstellation.color, fontSize: '20px' }}>
                  {selectedConstellation.icon}
                </span>
                <span className="ml-3 text-lg font-semibold">
                  {selectedConstellation.displayName}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">覆蓋範圍:</span>
                  <span className="ml-1 font-medium">{selectedConstellation.coverage}</span>
                </div>
                <div>
                  <span className="text-gray-500">軌道高度:</span>
                  <span className="ml-1 font-medium">{selectedConstellation.orbitAltitude}</span>
                </div>
                <div>
                  <span className="text-gray-500">預期延遲:</span>
                  <span className="ml-1 font-medium">{selectedConstellation.latency}</span>
                </div>
                <div>
                  <span className="text-gray-500">數據覆蓋:</span>
                  <span className="ml-1 font-medium">
                    {selectedConstellation.dataAvailability.totalDays} 天
                  </span>
                </div>
              </div>
            </Col>
            <Col span={6}>
              <Statistic
                title="可見衛星"
                value={selectedConstellation.satelliteCount}
                suffix="顆"
                valueStyle={{ color: selectedConstellation.color }}
              />
            </Col>
          </Row>
          
          {selectedConstellation.dataAvailability.start && (
            <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-gray-600">
              💡 數據期間: {selectedConstellation.dataAvailability.start} ~ {selectedConstellation.dataAvailability.end}
              <br />
              🎯 適用於論文級 LEO 衛星 Handover 研究和 RL 訓練
            </div>
          )}
          
          <Alert
            message="星座隔離原則"
            description="不同衛星星座間無法進行 Handover，請分別進行分析。每個星座的軌道參數、覆蓋模式和服務特性均不相同。"
            type="info"
            showIcon
            className="mt-3"
            size="small"
          />
        </Card>
      )}
    </div>
  );
};
```

### 4.2 增強型時間軸控制器

#### **完整的時間軸控制器實現**
```typescript
// TimelineControl.tsx (增強版)
import React, { useState, useEffect, useCallback } from 'react';
import { Slider, DatePicker, Button, Space, Card, Statistic, Progress, Switch } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  FastForwardOutlined,
  StepForwardOutlined,
  StepBackwardOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import moment from 'moment';

interface TimelineData {
  start: string;
  end: string;
  totalDurationHours: number;
  dataPoints: number;
  resolution: string;
}

interface Props {
  constellation: string;
  onTimeChange: (timestamp: number) => void;
  onPlaybackSpeedChange?: (speed: number) => void;
  disabled?: boolean;
  showStatistics?: boolean;
}

export const TimelineControl: React.FC<Props> = ({ 
  constellation,
  onTimeChange,
  onPlaybackSpeedChange,
  disabled = false,
  showStatistics = true
}) => {
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [realTimeMode, setRealTimeMode] = useState(false);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const fetchTimelineData = async () => {
      if (!constellation) return;
      
      setLoading(true);
      try {
        const response = await fetch(`/api/satellites/timeline/${constellation}`);
        const data = await response.json();
        
        setTimelineData({
          start: data.start_time,
          end: data.end_time,
          totalDurationHours: data.duration_hours,
          dataPoints: data.total_points,
          resolution: data.resolution
        });
        
        const startTime = new Date(data.start_time).getTime();
        setCurrentTime(startTime);
        onTimeChange(startTime);
        
      } catch (error) {
        console.error('Failed to fetch timeline data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTimelineData();
    setIsPlaying(false);
  }, [constellation, onTimeChange]);

  useEffect(() => {
    if (!isPlaying || !timelineData) return;
    
    const interval = setInterval(() => {
      setCurrentTime(prevTime => {
        const timeStep = realTimeMode ? 1000 : (60 * 1000 * playbackSpeed);
        const nextTime = prevTime + timeStep;
        const endTime = new Date(timelineData.end).getTime();
        
        if (nextTime > endTime) {
          setIsPlaying(false);
          return endTime;
        }
        
        onTimeChange(nextTime);
        return nextTime;
      });
    }, realTimeMode ? 1000 : 500);

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, realTimeMode, timelineData, onTimeChange]);

  const handleSliderChange = useCallback((value: number) => {
    if (!timelineData) return;
    
    const startTime = new Date(timelineData.start).getTime();
    const endTime = new Date(timelineData.end).getTime();
    const targetTime = startTime + (endTime - startTime) * (value / 100);
    
    setCurrentTime(targetTime);
    onTimeChange(targetTime);
  }, [timelineData, onTimeChange]);

  const togglePlayback = () => setIsPlaying(!isPlaying);

  const cycleSpeed = () => {
    const speeds = [0.5, 1, 2, 5, 10];
    const currentIndex = speeds.indexOf(playbackSpeed);
    const nextIndex = (currentIndex + 1) % speeds.length;
    setPlaybackSpeed(speeds[nextIndex]);
  };

  if (loading || !timelineData) {
    return (
      <Card className="timeline-control" loading={loading}>
        <div className="text-center py-4 text-gray-500">
          載入 {constellation} 星座時間軸數據...
        </div>
      </Card>
    );
  }

  const progress = ((currentTime - new Date(timelineData.start).getTime()) / 
                   (new Date(timelineData.end).getTime() - new Date(timelineData.start).getTime())) * 100;

  return (
    <Card className="timeline-control" title="⏰ 歷史數據時間軸控制">
      {showStatistics && (
        <div className="grid grid-cols-4 gap-4 mb-4">
          <Statistic
            title="數據覆蓋"
            value={timelineData.totalDurationHours}
            suffix="小時"
            precision={1}
          />
          <Statistic
            title="數據點數"
            value={timelineData.dataPoints}
            formatter={(value) => `${(value as number / 1000).toFixed(1)}K`}
          />
          <Statistic
            title="解析度"
            value={timelineData.resolution}
          />
          <Statistic
            title="進度"
            value={progress}
            suffix="%"
            precision={1}
          />
        </div>
      )}

      <div className="mb-4">
        <Progress 
          percent={progress} 
          showInfo={false} 
          strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
        />
      </div>
      
      <div className="mb-4">
        <Slider
          min={0}
          max={100}
          value={progress}
          onChange={handleSliderChange}
          disabled={disabled || isPlaying}
          tooltip={{
            formatter: (value) => {
              if (!value || !timelineData) return '';
              const startTime = new Date(timelineData.start).getTime();
              const endTime = new Date(timelineData.end).getTime();
              const targetTime = startTime + (endTime - startTime) * (value / 100);
              return moment(targetTime).format('MM/DD HH:mm');
            }
          }}
        />
        
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{moment(timelineData.start).format('MM/DD HH:mm')}</span>
          <span className="font-semibold text-blue-600">
            {moment(currentTime).format('MM-DD HH:mm:ss')}
          </span>
          <span>{moment(timelineData.end).format('MM/DD HH:mm')}</span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <Space size="small">
          <Button
            type="primary"
            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={togglePlayback}
            disabled={disabled || currentTime >= new Date(timelineData.end).getTime()}
          >
            {isPlaying ? '暫停' : '播放'}
          </Button>
          
          {!realTimeMode && (
            <Button
              icon={<FastForwardOutlined />}
              onClick={cycleSpeed}
              disabled={disabled}
              size="small"
            >
              {playbackSpeed}x
            </Button>
          )}
        </Space>

        <Space size="middle">
          <div className="flex items-center">
            <span className="text-xs text-gray-500 mr-2">實時模式</span>
            <Switch
              size="small"
              checked={realTimeMode}
              onChange={setRealTimeMode}
              disabled={disabled}
            />
          </div>
          
          <DatePicker
            showTime
            value={moment(currentTime)}
            onChange={(date) => {
              if (date) {
                const newTime = date.valueOf();
                const startTime = new Date(timelineData.start).getTime();
                const endTime = new Date(timelineData.end).getTime();
                
                if (newTime >= startTime && newTime <= endTime) {
                  setCurrentTime(newTime);
                  onTimeChange(newTime);
                }
              }
            }}
            disabled={disabled || isPlaying}
            size="small"
            format="MM/DD HH:mm"
          />
        </Space>
      </div>
      
      <div className="mt-3 text-xs text-gray-500 bg-gray-50 p-2 rounded">
        💡 提示: 滑桿快速跳轉，播放控制動畫，實時模式按真實時間播放，加速模式可調整倍速
      </div>
    </Card>
  );
};
```

### 4.3 衛星動畫渲染組件

#### **完整的動畫渲染器實現**
```typescript
// SatelliteAnimationViewer.tsx
import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Space, Statistic } from 'antd';
import { netstackFetch } from '../config/api-config';

interface SatellitePosition {
  satellite_id: string;
  constellation: string;
  position: {
    latitude: number;
    longitude: number;
    altitude: number;
  };
  observation: {
    elevation_angle: number;
    azimuth_angle: number;
    range_km: number;
  };
  signal_quality: {
    signal_strength: number;
    path_loss_db: number;
  };
}

interface HandoverEvent {
  satellite_id: string;
  event_type: 'serving' | 'handover_candidate' | 'monitoring' | 'approaching';
  trigger_condition: string;
  event_priority: 'high' | 'medium' | 'low' | 'info';
  action: string;
}

interface Props {
  currentTime: Date;
  constellation: string;
  playbackSpeed: number;
}

export const SatelliteAnimationViewer: React.FC<Props> = ({
  currentTime,
  constellation,
  playbackSpeed
}) => {
  const [satellites, setSatellites] = useState<SatellitePosition[]>([]);
  const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 獲取當前時間點的衛星位置
  useEffect(() => {
    const fetchSatellitesAtTime = async () => {
      if (!currentTime || !constellation) return;
      
      setLoading(true);
      try {
        const response = await netstackFetch(
          `/api/v1/satellites/history/at_time?target_time=${currentTime.toISOString()}&constellation=${constellation}&count=20`
        );
        const data = await response.json();
        
        if (data.success) {
          setSatellites(data.satellites);
        }
      } catch (error) {
        console.error('Failed to fetch satellites:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSatellitesAtTime();
  }, [currentTime, constellation]);
  
  // 計算並顯示 handover 事件
  useEffect(() => {
    const fetchHandoverEvents = async () => {
      if (!currentTime || !constellation || satellites.length === 0) return;
      
      try {
        const response = await netstackFetch(
          `/api/v1/satellites/d2/events?timestamp=${currentTime.toISOString()}&constellation=${constellation}`
        );
        const data = await response.json();
        
        if (data.success) {
          setHandoverEvents(data.handover_events);
        }
      } catch (error) {
        console.error('Failed to fetch handover events:', error);
      }
    };
    
    fetchHandoverEvents();
  }, [satellites, currentTime, constellation]);

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'serving': return 'green';
      case 'handover_candidate': return 'blue';
      case 'monitoring': return 'orange';
      case 'approaching': return 'gray';
      default: return 'default';
    }
  };

  const getEventTypeText = (eventType: string) => {
    switch (eventType) {
      case 'serving': return '服務中';
      case 'handover_candidate': return 'Handover候選';
      case 'monitoring': return '監測中';
      case 'approaching': return '即將可見';
      default: return eventType;
    }
  };

  const satelliteColumns = [
    {
      title: '衛星ID',
      dataIndex: 'satellite_id',
      key: 'satellite_id',
      width: 120,
    },
    {
      title: '仰角',
      dataIndex: ['observation', 'elevation_angle'],
      key: 'elevation',
      width: 80,
      render: (value: number) => `${value.toFixed(1)}°`,
      sorter: (a: SatellitePosition, b: SatellitePosition) => 
        b.observation.elevation_angle - a.observation.elevation_angle,
    },
    {
      title: '方位角',
      dataIndex: ['observation', 'azimuth_angle'],
      key: 'azimuth',
      width: 80,
      render: (value: number) => `${value.toFixed(1)}°`,
    },
    {
      title: '距離',
      dataIndex: ['observation', 'range_km'],
      key: 'range',
      width: 80,
      render: (value: number) => `${value.toFixed(0)}km`,
    },
    {
      title: '信號強度',
      dataIndex: ['signal_quality', 'signal_strength'],
      key: 'signal',
      width: 90,
      render: (value: number) => (
        <span style={{ color: value > 70 ? 'green' : value > 50 ? 'orange' : 'red' }}>
          {value.toFixed(1)}dBm
        </span>
      ),
    },
    {
      title: '狀態',
      key: 'status',
      width: 100,
      render: (_: any, record: SatellitePosition) => {
        const event = handoverEvents.find(e => e.satellite_id === record.satellite_id);
        return event ? (
          <Tag color={getEventTypeColor(event.event_type)}>
            {getEventTypeText(event.event_type)}
          </Tag>
        ) : (
          <Tag color="default">未分類</Tag>
        );
      },
    },
  ];

  const eventColumns = [
    {
      title: '衛星ID',
      dataIndex: 'satellite_id',
      key: 'satellite_id',
      width: 120,
    },
    {
      title: '事件類型',
      dataIndex: 'event_type',
      key: 'event_type',
      width: 120,
      render: (value: string) => (
        <Tag color={getEventTypeColor(value)}>
          {getEventTypeText(value)}
        </Tag>
      ),
    },
    {
      title: '觸發條件',
      dataIndex: 'trigger_condition',
      key: 'trigger_condition',
      ellipsis: true,
    },
    {
      title: '優先級',
      dataIndex: 'event_priority',
      key: 'priority',
      width: 80,
      render: (value: string) => (
        <Tag color={value === 'high' ? 'red' : value === 'medium' ? 'orange' : 'blue'}>
          {value}
        </Tag>
      ),
    },
    {
      title: '動作',
      dataIndex: 'action',
      key: 'action',
      ellipsis: true,
    },
  ];

  return (
    <div className="satellite-animation-viewer">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <Statistic
          title="可見衛星"
          value={satellites.length}
          suffix="顆"
          valueStyle={{ color: '#3f8600' }}
        />
        <Statistic
          title="Handover事件"
          value={handoverEvents.length}
          suffix="個"
          valueStyle={{ color: '#cf1322' }}
        />
        <Statistic
          title="播放速度"
          value={playbackSpeed}
          suffix="x"
          valueStyle={{ color: '#1890ff' }}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* 衛星位置表 */}
        <Card title="🛰️ 當前可見衛星" size="small">
          <Table
            columns={satelliteColumns}
            dataSource={satellites}
            rowKey="satellite_id"
            size="small"
            pagination={{ pageSize: 8, size: 'small' }}
            loading={loading}
            scroll={{ y: 300 }}
          />
        </Card>

        {/* Handover 事件表 */}
        <Card title="📡 Handover 事件" size="small">
          <Table
            columns={eventColumns}
            dataSource={handoverEvents}
            rowKey={(record) => `${record.satellite_id}-${record.event_type}`}
            size="small"
            pagination={{ pageSize: 8, size: 'small' }}
            scroll={{ y: 300 }}
          />
        </Card>
      </div>

      {/* 3GPP NTN 符合性指標 */}
      <Card title="📋 3GPP NTN 符合性檢查" size="small" className="mt-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {handoverEvents.filter(e => e.event_type === 'handover_candidate').length}
            </div>
            <div className="text-sm text-gray-500">Handover 候選</div>
            <div className="text-xs text-gray-400">標準: ≤ 5 顆</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {handoverEvents.filter(e => e.event_type === 'monitoring').length}
            </div>
            <div className="text-sm text-gray-500">監測衛星</div>
            <div className="text-xs text-gray-400">標準: ≤ 8 顆</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {satellites.filter(s => s.observation.elevation_angle >= 10).length}
            </div>
            <div className="text-sm text-gray-500">可測量</div>
            <div className="text-xs text-gray-400">仰角 ≥ 10°</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {handoverEvents.filter(e => e.event_type === 'serving').length}
            </div>
            <div className="text-sm text-gray-500">服務中</div>
            <div className="text-xs text-gray-400">主要連接</div>
          </div>
        </div>
      </Card>
    </div>
  );
};
```

### 4.4 主頁面整合示例

#### **完整的多星座分析頁面**
```typescript
// SatelliteAnalysis.tsx (多星座分析頁面)
import React, { useState, useCallback } from 'react';
import { Row, Col, Card, Spin } from 'antd';
import { ConstellationSelector } from '../components/ConstellationSelector';
import { TimelineControl } from '../components/TimelineControl';
import { SatelliteAnimationViewer } from '../components/SatelliteAnimationViewer';

export const SatelliteAnalysis: React.FC = () => {
  const [selectedConstellation, setSelectedConstellation] = useState('starlink');
  const [currentTimestamp, setCurrentTimestamp] = useState(Date.now());
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [loading, setLoading] = useState(false);

  const handleConstellationChange = useCallback((constellation: string) => {
    setLoading(true);
    setSelectedConstellation(constellation);
    setTimeout(() => setLoading(false), 500);
  }, []);

  const handleTimeChange = useCallback((timestamp: number) => {
    setCurrentTimestamp(timestamp);
  }, []);

  const handlePlaybackSpeedChange = useCallback((speed: number) => {
    setPlaybackSpeed(speed);
  }, []);

  return (
    <div className="satellite-analysis-page p-6">
      <Spin spinning={loading} tip="切換星座中...">
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="🛰️ LEO 衛星星座分析控制台" className="mb-4">
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <ConstellationSelector
                    value={selectedConstellation}
                    onChange={handleConstellationChange}
                    disabled={loading}
                    showComparison={true}
                  />
                </Col>
                <Col span={16}>
                  <TimelineControl
                    constellation={selectedConstellation}
                    onTimeChange={handleTimeChange}
                    onPlaybackSpeedChange={handlePlaybackSpeedChange}
                    disabled={loading}
                    showStatistics={true}
                  />
                </Col>
              </Row>
            </Card>
          </Col>

          <Col span={24}>
            <SatelliteAnimationViewer
              currentTime={new Date(currentTimestamp)}
              constellation={selectedConstellation}
              playbackSpeed={playbackSpeed}
            />
          </Col>
        </Row>
      </Spin>
    </div>
  );
};
```

## 📋 實施檢查清單

### **組件實現檢查**
- [ ] 實現增強型星座選擇器（多星座支援、統計資訊）
- [ ] 實現增強型時間軸控制器（進度條、倍速、實時模式）
- [ ] 實現衛星動畫渲染組件（表格視圖、handover 事件）
- [ ] 實現主頁面整合（響應式布局、狀態管理）

### **功能特性檢查**
- [ ] 星座切換功能（API 調用、數據更新）
- [ ] 時間軸播放控制（播放、暫停、倍速、跳轉）
- [ ] 實時數據更新（衛星位置、handover 事件）
- [ ] 3GPP NTN 符合性顯示（衛星數量、事件統計）

### **UI/UX 檢查**
- [ ] 響應式設計（桌面、平板、手機適配）
- [ ] 載入狀態處理（Spin、Skeleton、Progress）
- [ ] 錯誤狀態處理（網路錯誤、數據缺失）
- [ ] 用戶交互回饋（按鈕狀態、Toast 提示）

## 🧪 詳細驗證步驟

### **4.1 星座選擇器驗證**
```javascript
// 在瀏覽器開發者工具 Console 中執行
console.log("=== 星座選擇器驗證開始 ===");

// 檢查組件是否載入
const constellationSelector = document.querySelector('.constellation-selector');
console.log("星座選擇器存在:", !!constellationSelector);

// 檢查選項數量
const options = document.querySelectorAll('.constellation-option');
console.log("星座選項數量:", options.length, "（預期: ≥ 2）");

// 檢查 API 調用
const originalFetch = window.fetch;
let apiCallCount = 0;
window.fetch = function(...args) {
    if (args[0].includes('/api/satellites/constellations/info')) {
        apiCallCount++;
        console.log("星座資訊 API 調用次數:", apiCallCount);
    }
    return originalFetch.apply(this, args);
};

// 模擬星座切換
if (constellationSelector) {
    const selectElement = constellationSelector.querySelector('.ant-select-selector');
    if (selectElement) {
        selectElement.click();
        setTimeout(() => {
            const optionElements = document.querySelectorAll('.ant-select-item-option');
            console.log("下拉選項數量:", optionElements.length);
        }, 500);
    }
}
```

### **4.2 時間軸控制器驗證**
```javascript
console.log("=== 時間軸控制器驗證 ===");

// 檢查控制器是否載入
const timelineControl = document.querySelector('.timeline-control');
console.log("時間軸控制器存在:", !!timelineControl);

// 檢查統計資訊顯示
const statistics = document.querySelectorAll('.ant-statistic');
console.log("統計項目數量:", statistics.length, "（預期: 4 項）");

// 檢查播放控制按鈕
const playButton = document.querySelector('[aria-label*="播放"], [title*="播放"]');
console.log("播放按鈕存在:", !!playButton);

// 檢查滑桿控制
const slider = document.querySelector('.ant-slider');
console.log("時間滑桿存在:", !!slider);

// 檢查進度條
const progress = document.querySelector('.ant-progress');
console.log("進度條存在:", !!progress);

// 模擬播放控制測試
if (playButton) {
    console.log("開始播放控制測試...");
    playButton.click();
    
    setTimeout(() => {
        const pauseButton = document.querySelector('[aria-label*="暫停"], [title*="暫停"]');
        console.log("播放狀態切換成功:", !!pauseButton);
        
        if (pauseButton) {
            pauseButton.click();
        }
    }, 1000);
}
```

### **4.3 數據流驗證**
```javascript
console.log("=== 數據流驗證 ===");

// 監聽時間變更事件
let timeChangeCount = 0;
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.target.textContent && 
            mutation.target.textContent.match(/\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)) {
            timeChangeCount++;
            console.log("時間顯示更新次數:", timeChangeCount);
        }
    });
});

// 監聽時間顯示元素
const timeDisplays = document.querySelectorAll('[class*="time"], [class*="timestamp"]');
timeDisplays.forEach(element => {
    observer.observe(element, { 
        childList: true, 
        subtree: true, 
        characterData: true 
    });
});

// 檢查衛星數據更新
let satelliteUpdateCount = 0;
const satelliteObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.target.closest('.ant-table-tbody')) {
            satelliteUpdateCount++;
            console.log("衛星數據更新次數:", satelliteUpdateCount);
        }
    });
});

const satelliteTable = document.querySelector('.ant-table-tbody');
if (satelliteTable) {
    satelliteObserver.observe(satelliteTable, {
        childList: true,
        subtree: true
    });
}

// 5 秒後檢查結果
setTimeout(() => {
    console.log("=== 數據流驗證結果 ===");
    console.log("- 時間顯示更新次數:", timeChangeCount);
    console.log("- 衛星數據更新次數:", satelliteUpdateCount);
    console.log("- 預期: 播放模式下 > 0 次更新");
    
    observer.disconnect();
    satelliteObserver.disconnect();
}, 5000);
```

### **4.4 響應式設計驗證**
```javascript
console.log("=== 響應式設計驗證 ===");

const testViewports = [
    { width: 1920, height: 1080, name: "桌面大螢幕" },
    { width: 1366, height: 768, name: "桌面標準" },
    { width: 768, height: 1024, name: "平板" },
    { width: 375, height: 812, name: "手機" }
];

// 保存原始視窗大小
const originalWidth = window.innerWidth;
const originalHeight = window.innerHeight;

testViewports.forEach((viewport, index) => {
    setTimeout(() => {
        // 模擬視窗大小變更
        window.resizeTo(viewport.width, viewport.height);
        
        // 觸發 resize 事件
        window.dispatchEvent(new Event('resize'));
        
        setTimeout(() => {
            const controlPanel = document.querySelector('.satellite-analysis-page');
            if (controlPanel) {
                const rect = controlPanel.getBoundingClientRect();
                console.log(`${viewport.name}: 寬度 ${rect.width}px, 高度 ${rect.height}px`);
                console.log(`- 是否適應螢幕: ${rect.width <= viewport.width}`);
                
                // 檢查組件是否正常顯示
                const selector = document.querySelector('.constellation-selector');
                const timeline = document.querySelector('.timeline-control');
                const viewer = document.querySelector('.satellite-animation-viewer');
                
                console.log(`- 組件顯示狀態: 選擇器(${!!selector}) 時間軸(${!!timeline}) 檢視器(${!!viewer})`);
            }
            
            // 最後一個測試後恢復原始大小
            if (index === testViewports.length - 1) {
                setTimeout(() => {
                    window.resizeTo(originalWidth, originalHeight);
                    window.dispatchEvent(new Event('resize'));
                }, 500);
            }
        }, 200);
    }, index * 1000);
});
```

### **4.5 API 整合驗證**
```bash
# 檢查前端 API 調用
# 在瀏覽器 Network 標籤中應該看到以下請求：

# 1. 星座資訊查詢
curl -X GET "http://localhost:8080/api/v1/satellites/constellations/info" | jq

# 2. 時間軸資訊查詢
curl -X GET "http://localhost:8080/api/v1/satellites/timeline/starlink" | jq

# 3. 衛星位置查詢
curl -X GET "http://localhost:8080/api/v1/satellites/history/at_time?target_time=2025-01-23T12:00:00Z&constellation=starlink" | jq

# 4. Handover 事件查詢
curl -X GET "http://localhost:8080/api/v1/satellites/d2/events?timestamp=2025-01-23T12:00:00Z&constellation=starlink" | jq
```

## ✅ 完成確認檢查清單

### **組件功能檢查**
- [ ] **星座選擇器**: 正確顯示多星座選項，有圖示和統計資訊
- [ ] **API 整合**: 選擇星座時正確調用 `/constellations/info` 端點
- [ ] **時間軸控制**: 播放/暫停/倍速功能正常運作
- [ ] **數據同步**: 時間變更時正確觸發回調函數並更新顯示
- [ ] **響應式設計**: 在不同螢幕尺寸下正常顯示
- [ ] **錯誤處理**: 網路錯誤時顯示適當提示訊息

### **性能檢查**
- [ ] **組件載入**: 載入時間 < 2 秒
- [ ] **操作響應**: 用戶操作響應時間 < 300ms
- [ ] **數據更新**: 星座切換時數據更新 < 1 秒
- [ ] **動畫流暢**: 時間軸播放動畫 ≥ 30 FPS

### **用戶體驗檢查**
- [ ] **直觀操作**: 用戶可以直觀理解各個控制項功能
- [ ] **狀態反饋**: 載入、錯誤、成功狀態有明確視覺反饋
- [ ] **數據可視化**: 衛星位置、handover 事件清晰易讀
- [ ] **3GPP 符合性**: 顯示符合 3GPP NTN 標準的統計資訊

---

**🎯 完成標準**：
- 所有組件正常載入和渲染
- 星座切換功能完整，API 整合成功
- 時間軸播放控制流暢，支援多種播放模式
- 響應式設計在各種設備上正常工作
- 數據流更新及時，用戶交互體驗良好
- 前端驗證腳本全部通過，無控制台錯誤

