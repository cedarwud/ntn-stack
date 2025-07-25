# 05 - Phase 4: 前端時間軸控制

> **上一階段**：[Phase 3 - API 端點](./04-phase3-api-endpoints.md) | **下一階段**：[Phase 5 - 容器啟動](./06-phase5-container-startup.md)

## 🎯 Phase 4 目標
**目標**：實現前端星座切換控制器和時間軸控制器組件
**預估時間**: 2-3 天

## 📋 開發任務

### 4.1 星座切換控制器
```typescript
// ConstellationSelector.tsx
interface ConstellationSelectorProps {
  selectedConstellation: 'starlink' | 'oneweb';
  onConstellationChange: (constellation: 'starlink' | 'oneweb') => void;
  availableConstellations: ConstellationInfo[];
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
          </div>
        ))}
      </div>
      
      <div className="constellation-warning">
        ⚠️ 注意：不同星座無法進行跨星座 handover，請分別分析
      </div>
    </div>
  );
};
```

### 4.2 時間軸控制器組件
```typescript
// TimelineController.tsx
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
  
  return (
    <div className="timeline-controller">
      <div className="time-display">
        {currentTime.toISOString().substr(11, 8)} UTC
      </div>
      
      <input
        type="range"
        min={0}
        max={100} 
        value={(currentTime.getTime() - new Date(availableTimeRange.start).getTime()) / 
               (new Date(availableTimeRange.end).getTime() - new Date(availableTimeRange.start).getTime()) * 100}
        onChange={(e) => handleTimeSliderChange(Number(e.target.value))}
        className="time-slider"
      />
      
      <div className="playback-controls">
        <button onClick={() => setIsPlaying(\!isPlaying)}>
          {isPlaying ? '⏸️' : '▶️'}
        </button>
        
        <select value={playbackSpeed} onChange={(e) => setPlaybackSpeed(Number(e.target.value))}>
          <option value={1}>1x</option>
          <option value={2}>2x</option>
          <option value={5}>5x</option>
          <option value={10}>10x</option>
        </select>
      </div>
    </div>
  );
};
```

## 📋 實施檢查清單
- [ ] 實現星座選擇器組件
- [ ] 實現時間軸控制器組件
- [ ] 實現動畫渲染組件
- [ ] API 整合和數據同步
- [ ] 響應式設計

## 🧪 驗證步驟
```javascript
// 在瀏覽器 Console 執行
console.log("星座選擇器存在:", \!\!document.querySelector('.constellation-selector'));
console.log("時間軸控制器存在:", \!\!document.querySelector('.timeline-controller'));
```

**完成標準**：組件正常運作，API 整合成功，響應式設計

