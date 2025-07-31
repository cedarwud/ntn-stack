# NTN Stack 統一可視化平台架構計畫

## 🎯 最終願景：統一同步的 NTN 可視化體驗

**核心目標**：打造一個以立體圖為中心的統一 NTN 系統可視化平台，實現：

- **🌍 立體圖中心化**：立體圖作為主控制台，展示衛星實時位置和軌跡
- **📊 多維度同步顯示**：側邊欄、Events 圖表、換手動畫在同一頁面完美同步
- **⏱️ 時間軸統一控制**：用戶在任一組件調整時間，所有組件同步響應
- **🔄 換手事件協同**：立體圖換手動畫與 Events 圖表狀態完全同步
- **🛰️ 衛星軌跡關聯**：UE-衛星距離、RSRP 變化直接對應立體圖中的衛星移動

---

## 🏗️ 統一時間序列數據架構

### 預處理數據結構設計

**120分鐘統一時間序列格式** (基於現有本地數據架構)：
```json
{
  "metadata": {
    "computation_time": "2025-07-31T00:00:00Z",
    "constellation": "starlink",  // 只支援 starlink, oneweb
    "time_span_minutes": 120,
    "time_interval_seconds": 10,
    "total_time_points": 720,
    "data_source": "local_docker_volume",  // 100% 本地數據
    "tle_data_date": "2025-07-30",  // 手動收集數據的日期
    "reference_location": {
      "latitude": 24.9441,
      "longitude": 121.3714,
      "altitude": 0.0
    }
  },
  "satellites": [
    {
      "norad_id": 52369,
      "name": "STARLINK-52369",
      "constellation": "starlink",
      "time_series": [
        {
          "time_offset_seconds": 0,
          "timestamp": "2025-07-31T00:00:00Z",
          "position": {
            "latitude": 25.123,
            "longitude": 121.456,
            "altitude": 550000.0,
            "velocity": {"x": 7.8, "y": 0.0, "z": 0.0}
          },
          "observation": {
            "elevation_deg": 15.2,
            "azimuth_deg": 45.6,
            "range_km": 1200.5,
            "is_visible": true,
            "rsrp_dbm": -85.3,
            "rsrq_db": -12.1,
            "sinr_db": 18.5
          },
          "handover_metrics": {
            "signal_strength": 0.75,
            "handover_score": 0.82,
            "is_handover_candidate": true,
            "predicted_service_time_seconds": 450
          },
          "measurement_events": {
            "d1_distance_m": 85000.0,
            "d2_satellite_distance_m": 1200500.0,
            "d2_ground_distance_m": 21922.0,
            "a4_trigger_condition": false,
            "t1_time_condition": true
          }
        }
        // ... 719 more time points
      ]
    }
  ],
  "ue_trajectory": [
    {
      "time_offset_seconds": 0,
      "position": {"latitude": 24.9441, "longitude": 121.3714, "altitude": 0.0},
      "serving_satellite": "STARLINK-52369",
      "handover_state": "stable"
    }
    // ... 720 time points
  ],
  "handover_events": [
    {
      "time_offset_seconds": 120,
      "event_type": "handover_triggered",
      "source_satellite": "STARLINK-52369",
      "target_satellite": "STARLINK-47882",
      "trigger_conditions": ["a4_threshold_met", "d2_distance_optimal"],
      "handover_duration_ms": 150
    }
  ]
}
```

---

## 🎮 統一時間控制機制

### 全局時間狀態管理

```typescript
// /simworld/frontend/src/contexts/UnifiedTimeContext.tsx
interface UnifiedTimeState {
  // 時間控制
  currentTimePoint: number        // 0-719 (當前時間點索引)
  isPlaying: boolean             // 時間軸播放狀態
  playbackSpeed: number          // 播放速度倍數 (0.1x - 10x)
  
  // 數據狀態
  timeseriesData: TimeseriesData | null
  constellation: 'starlink' | 'oneweb'
  
  // 同步狀態
  connectedComponents: Set<string>  // 已連接的組件ID
  lastUpdateTime: number
}

interface UnifiedTimeActions {
  // 時間控制
  setTimePoint: (timePoint: number) => void
  playPause: () => void
  setPlaybackSpeed: (speed: number) => void
  
  // 組件註冊
  registerComponent: (componentId: string) => void
  unregisterComponent: (componentId: string) => void
  
  // 數據控制  
  switchConstellation: (constellation: 'starlink' | 'oneweb') => void
  refreshData: () => Promise<void>
}

// 統一時間Hook
const useUnifiedTime = (componentId: string) => {
  const context = useContext(UnifiedTimeContext)
  
  useEffect(() => {
    context.registerComponent(componentId)
    return () => context.unregisterComponent(componentId)
  }, [])
  
  return context
}
```

---

## 🌍 立體圖中心化架構

### 立體圖作為主控制台

```typescript
// /simworld/frontend/src/components/scenes/UnifiedStereogramView.tsx
const UnifiedStereogramView = () => {
  const { 
    currentTimePoint, 
    timeseriesData, 
    constellation,
    setTimePoint,
    playPause,
    isPlaying 
  } = useUnifiedTime('stereogram')
  
  // 當前時間點的衛星位置
  const currentSatellites = useMemo(() => {
    if (!timeseriesData) return []
    
    return timeseriesData.satellites.map(sat => ({
      ...sat.time_series[currentTimePoint],
      name: sat.name,
      norad_id: sat.norad_id,
      // 換手狀態視覺化
      isHandoverCandidate: sat.time_series[currentTimePoint].handover_metrics.is_handover_candidate,
      handoverScore: sat.time_series[currentTimePoint].handover_metrics.handover_score
    }))
  }, [timeseriesData, currentTimePoint])
  
  // UE 當前位置和服務狀態
  const currentUE = useMemo(() => {
    if (!timeseriesData) return null
    return timeseriesData.ue_trajectory[currentTimePoint]
  }, [timeseriesData, currentTimePoint])
  
  // 換手事件動畫
  const activeHandoverEvent = useMemo(() => {
    if (!timeseriesData) return null
    return timeseriesData.handover_events.find(event => 
      Math.abs(event.time_offset_seconds - (currentTimePoint * 10)) <= 5
    )
  }, [timeseriesData, currentTimePoint])
  
  return (
    <div className="unified-stereogram-container">
      {/* 3D 立體圖主視圖 */}
      <Canvas className="main-3d-view">
        <StereogramScene 
          satellites={currentSatellites}
          ue={currentUE}
          handoverEvent={activeHandoverEvent}
          onTimePointChange={setTimePoint}
        />
        
        {/* 換手動畫層 */}
        <HandoverAnimationLayer 
          event={activeHandoverEvent}
          satellites={currentSatellites}
        />
      </Canvas>
      
      {/* 時間控制條 */}
      <UnifiedTimeController 
        currentTimePoint={currentTimePoint}
        totalTimePoints={720}
        isPlaying={isPlaying}
        onTimeChange={setTimePoint}
        onPlayPause={playPause}
      />
      
      {/* 同步側邊欄 */}
      <SynchronizedSidebar 
        satellites={currentSatellites}
        ue={currentUE}
        timePoint={currentTimePoint}
      />
      
      {/* 同步 Events 圖表面板 */}
      <SynchronizedEventsPanel 
        timeseriesData={timeseriesData}
        currentTimePoint={currentTimePoint}
        activeHandoverEvent={activeHandoverEvent}
      />
    </div>
  )
}
```

---

## 📊 Events 圖表完全同步機制

### 多事件圖表統一顯示

```typescript
// /simworld/frontend/src/components/domains/measurement/UnifiedEventsPanel.tsx
const SynchronizedEventsPanel = ({ 
  timeseriesData, 
  currentTimePoint, 
  activeHandoverEvent 
}) => {
  // D2 距離事件數據
  const d2EventData = useMemo(() => {
    if (!timeseriesData) return []
    
    return timeseriesData.satellites.flatMap(sat =>
      sat.time_series.map((timePoint, index) => ({
        timeOffset: index,
        timestamp: timePoint.timestamp,
        satelliteDistance: timePoint.measurement_events.d2_satellite_distance_m,
        groundDistance: timePoint.measurement_events.d2_ground_distance_m,
        satelliteInfo: {
          name: sat.name,
          position: timePoint.position,
          observation: timePoint.observation
        },
        isCurrentTimePoint: index === currentTimePoint
      }))
    )
  }, [timeseriesData, currentTimePoint])
  
  // A4 RSRP 事件數據
  const a4EventData = useMemo(() => {
    return timeseriesData?.satellites.map(sat => ({
      name: sat.name,
      rsrpSeries: sat.time_series.map((tp, index) => ({
        timeOffset: index,
        rsrp: tp.observation.rsrp_dbm,
        isCurrentTimePoint: index === currentTimePoint,
        triggerCondition: tp.measurement_events.a4_trigger_condition
      }))
    })) || []
  }, [timeseriesData, currentTimePoint])
  
  return (
    <div className="synchronized-events-panel">
      {/* D2 距離事件圖表 */}
      <SynchronizedD2Chart 
        data={d2EventData}
        currentTimePoint={currentTimePoint}
        onTimePointHover={(timePoint) => {
          // 立體圖預覽該時間點
          previewTimePoint(timePoint)
        }}
      />
      
      {/* A4 RSRP 事件圖表 */}
      <SynchronizedA4Chart 
        data={a4EventData}
        currentTimePoint={currentTimePoint}
        handoverEvent={activeHandoverEvent}
      />
      
      {/* 換手事件時間線 */}
      <HandoverTimeline 
        events={timeseriesData?.handover_events || []}
        currentTimePoint={currentTimePoint}
        onEventClick={(event) => {
          // 跳轉到換手事件時間點
          setTimePoint(event.time_offset_seconds / 10)
        }}
      />
    </div>
  )
}
```

---

## 🔄 換手事件協同動畫

### 立體圖與圖表換手狀態同步

```typescript
// /simworld/frontend/src/components/domains/handover/SynchronizedHandoverSystem.tsx
const SynchronizedHandoverSystem = ({ 
  activeHandoverEvent, 
  satellites, 
  currentTimePoint 
}) => {
  // 換手動畫狀態
  const handoverAnimation = useMemo(() => {
    if (!activeHandoverEvent) return null
    
    const sourceSat = satellites.find(s => s.name === activeHandoverEvent.source_satellite)
    const targetSat = satellites.find(s => s.name === activeHandoverEvent.target_satellite)
    
    return {
      source: sourceSat,
      target: targetSat,
      progress: calculateHandoverProgress(activeHandoverEvent, currentTimePoint),
      phase: determineHandoverPhase(activeHandoverEvent, currentTimePoint)
    }
  }, [activeHandoverEvent, satellites, currentTimePoint])
  
  return (
    <>
      {/* 立體圖中的換手動畫 */}
      <HandoverBeamAnimation 
        source={handoverAnimation?.source}
        target={handoverAnimation?.target}
        progress={handoverAnimation?.progress}
        phase={handoverAnimation?.phase}
      />
      
      {/* 圖表中的換手指示器 */}
      <HandoverIndicatorOverlay 
        event={activeHandoverEvent}
        currentTimePoint={currentTimePoint}
      />
      
      {/* 側邊欄換手狀態 */}
      <HandoverStatusDisplay 
        animation={handoverAnimation}
        event={activeHandoverEvent}
      />
    </>
  )
}
```

---

## 🛠️ 預處理階段實施方案

### NetStack 預處理引擎擴展

```python
# /netstack/src/services/satellite/unified_timeseries_generator.py
class UnifiedTimeseriesGenerator:
    """統一時間序列數據生成器 - 支援完整 NTN 可視化需求"""
    
    def __init__(self):
        self.time_span_minutes = 120
        self.time_interval_seconds = 10
        self.total_time_points = 720
        
    async def generate_unified_timeseries(
        self,
        constellation: str,
        reference_location: Position,
        start_time: datetime
    ) -> UnifiedTimeseriesData:
        """生成統一時間序列數據"""
        
        # 1. 從本地 Docker Volume 獲取 TLE 數據 (無 API 調用)
        satellites_tle = await self.load_local_tle_data(constellation)
        
        # 2. 計算所有時間點的衛星位置
        satellite_timeseries = []
        for sat_tle in satellites_tle:
            time_series = await self.calculate_satellite_timeseries(
                sat_tle, start_time, reference_location
            )
            satellite_timeseries.append({
                "norad_id": sat_tle.catalog_number,
                "name": sat_tle.satellite_name,
                "constellation": constellation,
                "time_series": time_series
            })
        
        # 3. 計算 UE 軌跡（如果 UE 移動）
        ue_trajectory = await self.calculate_ue_trajectory(
            reference_location, start_time
        )
        
        # 4. 識別和標記換手事件
        handover_events = await self.identify_handover_events(
            satellite_timeseries, ue_trajectory
        )
        
        return UnifiedTimeseriesData(
            metadata=self.generate_metadata(),
            satellites=satellite_timeseries,
            ue_trajectory=ue_trajectory,
            handover_events=handover_events
        )
    
    async def calculate_satellite_timeseries(
        self, 
        tle: TLEData, 
        start_time: datetime,
        reference_location: Position
    ) -> List[TimeseriesPoint]:
        """計算單顆衛星的完整時間序列"""
        
        time_series = []
        current_time = start_time
        
        for i in range(self.total_time_points):
            # SGP4 軌道計算
            orbit_position = self.sgp4_calculator.propagate_orbit(tle, current_time)
            
            # 觀測角度和可見性
            observation = self.calculate_observation_metrics(
                orbit_position, reference_location, current_time
            )
            
            # 換手相關指標
            handover_metrics = self.calculate_handover_metrics(
                orbit_position, observation, current_time
            )
            
            # 測量事件計算
            measurement_events = self.calculate_measurement_events(
                orbit_position, reference_location, observation
            )
            
            time_series.append(TimeseriesPoint(
                time_offset_seconds=i * self.time_interval_seconds,
                timestamp=current_time.isoformat(),
                position=orbit_position,
                observation=observation,
                handover_metrics=handover_metrics,
                measurement_events=measurement_events
            ))
            
            current_time += timedelta(seconds=self.time_interval_seconds)
        
        return time_series
```

### API 端點設計 (基於本地數據架構)

```python
# /netstack/src/api/routes/unified_satellites.py
@router.get("/unified/timeseries")
async def get_unified_timeseries_data(
    constellation: str = "starlink",  # 只支援 starlink, oneweb
    reference_lat: float = 24.9441,
    reference_lon: float = 121.3714,
    reference_alt: float = 0.0,
    start_time: Optional[str] = None
):
    """獲取統一時間序列數據 - 基於 Docker Volume 本地數據"""
    
    # 驗證星座支援
    if constellation not in ["starlink", "oneweb"]:
        raise HTTPException(
            status_code=400, 
            detail=f"不支援的星座: {constellation}。僅支援 starlink, oneweb"
        )
    
    if start_time is None:
        start_time = datetime.now(timezone.utc)
    else:
        start_time = datetime.fromisoformat(start_time)
    
    reference_location = Position(
        latitude=reference_lat,
        longitude=reference_lon, 
        altitude=reference_alt
    )
    
    # 使用本地數據生成器 (無網路 API 調用)
    generator = UnifiedTimeseriesGenerator()
    unified_data = await generator.generate_unified_timeseries(
        constellation, reference_location, start_time
    )
    
    # 標記數據來源
    unified_data.metadata["data_source"] = "local_docker_volume"
    unified_data.metadata["network_dependency"] = False
    
    return unified_data.to_dict()
```

---

## ⚡ 性能優化策略

### 分層數據載入

```typescript
// 首次載入：載入完整120分鐘數據
const initialLoad = async (constellation: string) => {
  const response = await fetch(`/api/v1/satellites/unified/timeseries?constellation=${constellation}`)
  return response.json()
}

// 實時更新：只更新當前可見時間窗口
const updateCurrentWindow = async (timePoint: number, windowSize = 60) => {
  const startOffset = Math.max(0, timePoint - windowSize/2)
  const endOffset = Math.min(719, timePoint + windowSize/2)
  
  // 只更新當前窗口的數據
  return await fetch(`/api/v1/satellites/unified/timeseries/window?start=${startOffset}&end=${endOffset}`)
}
```

### 渲染優化

```typescript
// 組件記憶化
const MemoizedSatellite3D = React.memo(Satellite3D, (prev, next) => {
  return prev.position === next.position && 
         prev.handoverState === next.handoverState
})

// 時間點變化時的差分更新
const useDifferentialUpdate = (timeseriesData, currentTimePoint) => {
  const prevTimePointRef = useRef(currentTimePoint)
  
  return useMemo(() => {
    const prevTimePoint = prevTimePointRef.current
    const changedSatellites = new Set()
    
    // 只更新位置有變化的衛星
    timeseriesData.satellites.forEach(sat => {
      const prevPos = sat.time_series[prevTimePoint]?.position
      const currentPos = sat.time_series[currentTimePoint]?.position
      
      if (!positionsEqual(prevPos, currentPos)) {
        changedSatellites.add(sat.norad_id)
      }
    })
    
    prevTimePointRef.current = currentTimePoint
    return changedSatellites
  }, [timeseriesData, currentTimePoint])
}
```

---

## 🎯 最終成果展示

### 統一可視化平台特性

✅ **時間軸統一控制**
- 用戶拖動任一組件的時間軸，所有組件同步響應
- 播放/暫停控制影響整個系統狀態

✅ **衛星軌跡完美對應**  
- 立體圖中衛星移動直接對應 Events 圖表中的距離/RSRP 變化
- 鼠標懸停圖表數據點，立體圖中對應衛星高亮顯示

✅ **換手事件協同顯示**
- 立體圖中的換手動畫與 Events 圖表中的換手標記完全同步
- 換手決策過程在多個視圖中同時呈現

✅ **多事件類型支援**
- D1/D2 距離事件、A4 RSRP 事件、T1 時間事件統一數據源
- 支援未來擴展 A3、A5 等其他 3GPP NTN 事件

✅ **性能優化保證**
- 分層載入和差分更新確保流暢的時間軸操作
- 記憶化和虛擬化技術支援大量數據點渲染

---

## 🔧 本地數據架構整合

### 實際實施基礎

**數據來源現實**：
- ✅ **100% 本地數據**：基於 Docker Volume `/app/data/` 
- ✅ **手動 TLE 更新**：每月手動收集 Starlink, OneWeb 數據
- ✅ **零網路依賴**：IP 被封鎖後的完全本地化方案
- ❌ **Kuiper 排除**：數量太少，無換手研究價值

### 數據流程架構

```
每日 TLE 更新 → Docker Volume → 120分鐘預處理 → 統一 API → 多組件同步
     ↓              ↓                ↓              ↓           ↓
自動更新     /app/data/*.json   時間序列數據    NetStack API   立體圖+Events
```

### 建構階段預處理

```dockerfile
# NetStack Dockerfile 擴展
COPY tle_data/ /app/tle_data/            # 手動收集的 TLE 數據
RUN python generate_120min_timeseries.py \  # 預處理 120 分鐘數據
    --constellations starlink,oneweb \
    --duration 120 \
    --interval 10 \
    --output /app/data/
```

### 資料更新維護

```bash
# 每日資料更新流程 (推薦)
cd /home/sat/ntn-stack/scripts
./daily_tle_download_enhanced.sh       # 自動收集最新 TLE
docker build -t netstack:latest .      # 重建映像檔
make netstack-restart                   # 應用新數據

# 強制更新模式 (如需要)
./daily_tle_download_enhanced.sh --force
```

## 🛰️ 軌道計算精度提升建議

### 當前實施現況

**簡化圓軌道模型 vs SGP4 精確模型**:

| 特性 | 簡化圓軌道模型 | SGP4 精確模型 |
|------|----------------|----------------|
| **計算速度** | 極快 | 中等 |
| **位置精度** | 公里級 (±5-10km) | 米級 (±100-500m) |
| **時序精度** | 分鐘級誤差 | 秒級精度 |
| **物理完整性** | 基礎 | 完整 (地球扁率、大氣阻力、重力攝動) |
| **研究價值** | 教學演示 | 學術研究與實用應用 |
| **LEO 適用性** | 一般 | 優秀 |

### 對 LEO 衛星換手研究的影響

**簡化圓軌道的限制**:
- ❌ **位置誤差累積**: 長時間預測誤差快速增大
- ❌ **換手時機偏差**: 影響最佳換手點判斷
- ❌ **信號強度估算**: 基於不準確距離的信號強度計算
- ❌ **學術可信度**: 論文結果的實用性受質疑

**SGP4 模型的價值**:
- ✅ **高精度軌道預測**: 考慮真實物理效應
- ✅ **準確換手決策**: 基於精確的衛星位置和速度
- ✅ **實際部署可行**: 與真實系統行為一致
- ✅ **學術價值提升**: 研究成果具有實際應用價值
- ✅ **國際標準一致**: 與 3GPP NTN 標準使用相同計算方法

### 實施建議與階段規劃

**Phase 1 - 混合精度模式** (2-3週實施):
```python
# 關鍵換手計算使用 SGP4
if is_handover_critical_calculation:
    position = sgp4_calculator.propagate_orbit(tle, timestamp)
else:
    position = simplified_orbit_model(tle, timestamp)
```

**Phase 2 - 完整 SGP4 遷移** (4-6週實施):
```python
# 全面使用 SGP4，預計算並快取軌道數據
precomputed_orbits = sgp4_precompute_120min_timeseries()
```

**Phase 3 - 高級軌道分析** (長期目標):
- 軌道攝動補償
- 多體重力場效應
- 大氣密度變化修正

### 效能與成本評估

**計算資源影響**:
- **CPU 使用**: 增加 20-30%
- **記憶體需求**: 增加 15-25%
- **預計算時間**: 延長 2-3 倍
- **數據準確性**: 提升 10-50 倍

**開發工作量**:
- **核心 SGP4 整合**: 1-2 週
- **預計算系統更新**: 1 週
- **API 介面調整**: 3-5 天
- **測試與驗證**: 1 週

**學術與實用價值**:
- 📊 **論文引用價值**: 大幅提升
- 🎯 **實際部署可行性**: 從概念驗證升級到實用系統
- 🏆 **國際競爭力**: 與頂尖研究機構同等精度標準
- 💡 **技術創新**: 為真實 5G NTN 部署提供技術基礎

## 📅 TLE 數據管理最佳實踐

### 自動化更新機制詳解

**daily_tle_download_enhanced.sh 特性**:
- 🔄 **智能更新檢查**: 比較遠端檔案修改時間和大小
- 💾 **7天滾動備份**: 防止數據遺失，支援快速回滾
- ✅ **完整性驗證**: 自動驗證下載數據的格式和新鮮度
- 🚨 **異常處理**: 下載失敗時保持現有數據穩定運行
- 📊 **詳細報告**: 提供完整的更新狀況和統計資訊

**建議定期維護流程**:
```bash
# 每日自動執行 (crontab)
0 2 * * * cd /home/sat/ntn-stack/scripts && ./daily_tle_download_enhanced.sh

# 每週檢查備份狀況
0 3 * * 0 find /home/sat/ntn-stack/netstack/tle_data/backups -type d -mtime +7 -exec rm -rf {} \;

# 每月強制更新和系統健檢
0 4 1 * * cd /home/sat/ntn-stack/scripts && ./daily_tle_download_enhanced.sh --force && make netstack-restart
```

---

**這個架構基於真實的本地數據環境，實現統一 NTN 系統可視化平台，確保在無網路依賴的情況下提供穩定可靠的衛星軌跡和測量事件數據。建議優先考慮 SGP4 升級以顯著提升 LEO 衛星換手研究的學術價值和實用性。**