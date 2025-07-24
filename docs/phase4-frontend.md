# Phase 4: 前端時間軸控制 (3-4 天)

## 🎯 Phase 4 目標
實現多星座支援的前端時間軸控制系統，包含星座選擇器、時間軸控制器和 3D 動畫展示功能。

## 📋 主要任務

### 4.1 星座切換控制器
### 4.2 時間軸控制器組件  
### 4.3 增強型星座選擇器 (多星座支援)
### 4.4 增強型時間軸控制器
### 4.5 主頁面整合示例

---

## 4.1 基礎星座選擇器

```typescript
// ConstellationSelector.tsx
interface ConstellationSelectorProps {
  selectedConstellation: 'starlink' | 'oneweb';
  onConstellationChange: (constellation: 'starlink' | 'oneweb') => void;
  availableConstellations: ConstellationInfo[];
}

interface ConstellationInfo {
  id: 'starlink' | 'oneweb';
  name: string;
  description: string;
  satelliteCount: number;
  orbitAltitude: number;
  inclination: number;
  coverage: string;
}

export const ConstellationSelector: React.FC<ConstellationSelectorProps> = ({
  selectedConstellation,
  onConstellationChange,
  availableConstellations
}) => {
  return (
    <div className="constellation-selector">
      <h3>星座選擇</h3>
      <div className="constellation-tabs">
        {availableConstellations.map(constellation => (
          <div
            key={constellation.id}
            className={`constellation-tab ${selectedConstellation === constellation.id ? 'active' : ''}`}
            onClick={() => onConstellationChange(constellation.id)}
          >
            <div className="constellation-name">{constellation.name}</div>
            <div className="constellation-info">
              <span>衛星數: {constellation.satelliteCount}</span>
              <span>高度: {constellation.orbitAltitude}km</span>
              <span>傾角: {constellation.inclination}°</span>
            </div>
            <div className="constellation-coverage">{constellation.coverage}</div>
          </div>
        ))}
      </div>
      
      {/* 切換警告 */}
      <div className="constellation-warning">
        ⚠️ 注意：不同星座無法進行跨星座 handover，請分別分析
      </div>
    </div>
  );
};
```

## 4.2 基礎時間軸控制器

```typescript
// TimelineController.tsx
interface TimelineControllerProps {
  availableTimeRange: {
    start: string;
    end: string;
    totalDurationHours: number;
  };
  onTimeChange: (timestamp: Date) => void;
  onPlaybackSpeedChange: (speed: number) => void;
}

export const TimelineController: React.FC<TimelineControllerProps> = ({
  availableTimeRange,
  onTimeChange, 
  onPlaybackSpeedChange
}) => {
  const [currentTime, setCurrentTime] = useState(new Date(availableTimeRange.start));
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  
  // 時間軸滑桿
  const handleTimeSliderChange = (value: number) => {
    const startTime = new Date(availableTimeRange.start).getTime();
    const endTime = new Date(availableTimeRange.end).getTime();
    const targetTime = new Date(startTime + (endTime - startTime) * value / 100);
    
    setCurrentTime(targetTime);
    onTimeChange(targetTime);
  };
  
  // 播放控制
  useEffect(() => {
    if (!isPlaying) return;
    
    const interval = setInterval(() => {
      setCurrentTime(prev => {
        const next = new Date(prev.getTime() + 30000 * playbackSpeed); // 30秒步進 × 加速倍數
        
        if (next.getTime() > new Date(availableTimeRange.end).getTime()) {
          setIsPlaying(false);
          return prev;
        }
        
        onTimeChange(next);
        return next;
      });
    }, 1000); // 每秒更新
    
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, availableTimeRange, onTimeChange]);
  
  return (
    <div className="timeline-controller">
      <div className="time-display">
        <h3>當前時間: {currentTime.toLocaleString()}</h3>
        <p>數據範圍: {availableTimeRange.start} ~ {availableTimeRange.end}</p>
      </div>
      
      {/* 時間軸滑桿 */}
      <div className="timeline-slider">
        <input
          type="range"
          min="0"
          max="100"
          onChange={e => handleTimeSliderChange(parseInt(e.target.value))}
          className="timeline-range"
        />
      </div>
      
      {/* 播放控制 */}
      <div className="playback-controls">
        <button onClick={() => setIsPlaying(!isPlaying)}>
          {isPlaying ? '暫停' : '播放'}
        </button>
        
        <div className="speed-controls">
          <label>播放速度:</label>
          {[0.5, 1, 2, 5, 10].map(speed => (
            <button
              key={speed}
              className={playbackSpeed === speed ? 'active' : ''}
              onClick={() => {
                setPlaybackSpeed(speed);
                onPlaybackSpeedChange(speed);
              }}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
      
      {/* 跳轉控制 */}
      <div className="jump-controls">
        <button onClick={() => {
          const newTime = new Date(currentTime.getTime() - 10 * 60 * 1000); // 往前10分鐘
          setCurrentTime(newTime);
          onTimeChange(newTime);
        }}>
          ⏪ -10分鐘
        </button>
        
        <button onClick={() => {
          const newTime = new Date(currentTime.getTime() + 10 * 60 * 1000); // 往後10分鐘
          setCurrentTime(newTime);
          onTimeChange(newTime);
        }}>
          ⏩ +10分鐘
        </button>
      </div>
    </div>
  );
};
```

## 4.3 增強型星座選擇器 (多星座支援)

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

## 4.4 增強型時間軸控制器

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

## 4.5 主頁面整合示例

```typescript
// SatelliteAnalysis.tsx (多星座分析頁面)
import React, { useState, useCallback } from 'react';
import { Row, Col, Card } from 'antd';
import { ConstellationSelector } from '../components/ConstellationSelector';
import { TimelineControl } from '../components/TimelineControl';

export const SatelliteAnalysis: React.FC = () => {
  const [selectedConstellation, setSelectedConstellation] = useState('starlink');
  const [currentTimestamp, setCurrentTimestamp] = useState(Date.now());
  const [loading, setLoading] = useState(false);

  const handleConstellationChange = useCallback((constellation: string) => {
    setLoading(true);
    setSelectedConstellation(constellation);
    setTimeout(() => setLoading(false), 500);
  }, []);

  const handleTimeChange = useCallback((timestamp: number) => {
    setCurrentTimestamp(timestamp);
  }, []);

  return (
    <div className="satellite-analysis-page p-6">
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
                  disabled={loading}
                  showStatistics={true}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
```

---

## 📋 Phase 4 交付物

### **前端組件**
- [x] 基礎星座選擇器
- [x] 基礎時間軸控制器  
- [x] 增強型多星座選擇器
- [x] 增強型時間軸控制器
- [x] 主頁面整合示例

### **功能特色**
- **多星座支援**: Starlink + OneWeb 切換
- **豐富控制**: 播放/暫停/倍速/跳轉
- **統計顯示**: 數據覆蓋、點數、解析度、進度
- **響應式設計**: 適配不同螢幕尺寸
- **錯誤處理**: 網路異常的優雅處理

### **技術實現**
- **React Hook**: useState, useEffect, useCallback
- **Ant Design**: 豐富的 UI 組件庫
- **TypeScript**: 完整的類型安全
- **Moment.js**: 時間處理和格式化

---

**下一步**: 查看 [phase5-deployment.md](./phase5-deployment.md) 了解容器部署配置