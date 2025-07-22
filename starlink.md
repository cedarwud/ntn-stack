# NTN Stack Starlink 真實衛星數據整合開發計畫

## 🎯 項目目標

實現在 navbar > 立體圖中使用真實 Starlink 衛星數據進行衛星渲染，並透過 d2 events 展示真實的換手動畫，確保：

1. **真實衛星數據渲染**：使用基於台北座標 (24°56'39"N, 121°22'17"E) 的真實 Starlink 衛星可見性數據
2. **數據一致性**：sidebar 衛星 gNB 數據與立體圖渲染完全同步
3. **真實距離計算**：使用物理準確的 UE-衛星距離計算，並以適當比例呈現
4. **換手動畫同步**：d2 events 距離/時間曲線與立體圖換手動畫實時同步

## 📊 現狀分析總結

### ✅ 系統優勢
- **完整的真實數據架構**：TLE 數據獲取、SGP4 軌道計算、座標轉換系統
- **符合 3GPP 標準**：D2 events 完全按照 TS 38.331 標準實現
- **成熟的動畫系統**：UAV-衛星換手動畫、3D 渲染、多模式控制
- **論文級數據品質**：85-90% 真實數據，符合一般期刊發表要求

### ⚠️ 識別問題
- **SGP4 計算精度**：與標準軟體存在數百公里偏差，需要精度提升
- **數據同步不一致**：sidebar 使用模擬數據，3D 場景使用混合數據
- **缺失 API 端點**：單個衛星位置查詢 API 不存在導致回退到模擬數據
- **視覺縮放比例**：需要優化 3D 場景的距離呈現比例

## 🚀 開發步驟流程

### Phase 1: 修復核心數據計算 (1-2週)

**目標**：確保 SGP4 軌道計算和衛星可見性預測的基本準確性

#### 1.1 修復 SGP4 計算精度問題
```python
# 文件：simworld/backend/app/services/sgp4_calculator.py
# 修復項目：
1. 分析與 Skyfield 標準實現的 700km+ 偏差原因
2. 完善攝動項實現（J4、大氣阻力、太陽輻射壓力）
3. 優化數值穩定性和計算精度
4. 建立與多個標準軟體的驗證測試
```

#### 1.2 實現台北地區衛星可見性 API
```python
# 新增端點：GET /api/v1/satellites/{satellite_id}/position?observer_lat={lat}&observer_lon={lon}
# 返回數據：
{
  "satellite_id": "44713",
  "name": "STARLINK-1007", 
  "position": {
    "elevation": 45.2,    # 仰角 (度)
    "azimuth": 180.5,     # 方位角 (度)
    "range": 650.3,       # 距離 (km)
    "signal_quality": 85   # 信號品質 (0-100)
  },
  "observer": {
    "latitude": 24.9441,
    "longitude": 121.3717
  },
  "timestamp": "2025-01-22T10:30:00Z"
}
```

#### 1.3 建立真實 UE-衛星距離計算模組
```python
# 新建：simworld/backend/app/services/ue_satellite_distance.py
class UESatelliteDistanceCalculator:
    def calculate_slant_range(self, observer_lat, observer_lon, sat_position):
        """計算 UE 到衛星的直線距離"""
        # 使用球面三角學精確計算
        # 距離範圍：550km (90°) 到 8554km (10°)
        
    def calculate_path_loss(self, distance_km, frequency_mhz=14000):
        """計算自由空間路徑損耗"""
        # PL(dB) = 32.44 + 20*log10(f_MHz) + 20*log10(d_km)
```

**Phase 1 驗收標準：**
- [ ] SGP4 計算偏差 < 50km （目前 700km+）
- [ ] 台北地區衛星可見性 API 正常回傳真實數據
- [ ] UE-衛星距離計算精度 < 5km
- [ ] `docker exec simworld_backend python3 test_sgp4_accuracy.py` 通過率 > 95%

### Phase 2: 實現數據源統一 (1-2週)

**目標**：確保 sidebar、3D 場景、d2 events 使用相同的真實數據源

#### 2.1 統一衛星數據管理器
```typescript
// 新建：simworld/frontend/src/services/unifiedSatelliteDataManager.ts
export class UnifiedSatelliteDataManager {
  private observerPosition = { lat: 24.9441, lon: 121.3717 }; // 台北
  private updateInterval = 10000; // 10秒更新
  
  async getVisibleSatellites(minElevation: number = 10): Promise<SatelliteData[]> {
    // 統一的真實衛星數據獲取
    // 同時供應 sidebar、3D 場景、d2 events 使用
  }
  
  async getRealTimeDistances(satelliteIds: string[]): Promise<DistanceData[]> {
    // 即時距離計算，供 d2 events 使用
  }
}
```

#### 2.2 修改 sidebar 衛星 gNB 數據來源
```typescript
// 修改：simworld/frontend/src/components/layout/EnhancedSidebar/hooks/useSatelliteData.ts
// 替換模擬數據為統一數據管理器
const unifiedManager = new UnifiedSatelliteDataManager();
const realSatellites = await unifiedManager.getVisibleSatellites(10);
setSkyfieldSatellites(realSatellites);
```

#### 2.3 整合 3D 場景真實數據
```typescript
// 修改：simworld/frontend/src/services/realSatelliteService.ts
// 使用統一數據源，確保與 sidebar 一致
export class RealSatelliteDataManager {
  constructor(private unifiedManager: UnifiedSatelliteDataManager) {}
  
  async updateSatellitePositions(): Promise<SatellitePosition[]> {
    const realData = await this.unifiedManager.getVisibleSatellites();
    return this.mapToSatellitePositions(realData);
  }
}
```

**Phase 2 驗收標準：**
- [ ] Sidebar 衛星 gNB 數量與 3D 場景渲染衛星數量一致
- [ ] 兩處顯示的衛星名稱、仰角、信號品質數據完全相同
- [ ] 數據更新時兩個組件同步更新（10秒週期）
- [ ] 控制面板開關能同時影響兩處的衛星顯示

### Phase 3: 真實 3D 距離渲染 (1週)

**目標**：在 3D 立體圖中以物理準確且視覺合理的比例呈現真實距離

#### 3.1 優化 3D 場景縮放比例
```typescript
// 修改：simworld/frontend/src/components/domains/satellite/visualization/DynamicSatelliteRenderer.tsx
const SCENE_CONFIG = {
  earthRadius: 10.0,        // 場景地球半徑
  scaleRatio: 1/637,        // 1:637 縮放比例
  satelliteHeight: 0.86,    // 550km → 0.86 場景單位
  
  // 距離映射：550km (90°) → 0.86 單位, 8554km (10°) → 13.4 單位
  distanceMapping: {
    min: 0.86,    // 550km
    max: 13.4     // 8554km
  }
};
```

#### 3.2 連接線視覺化增強
```typescript
// 基於真實距離的視覺回饋
const getConnectionVisual = (distance: number) => {
  const normalizedDistance = (distance - 550) / (8554 - 550); // 0-1
  
  return {
    color: distance < 1200 ? 'green' : distance < 3000 ? 'yellow' : 'red',
    opacity: 1.0 - (normalizedDistance * 0.6), // 遠距離更透明
    radius: 0.02 * (1.0 - normalizedDistance * 0.5), // 遠距離更細
    pulseSpeed: 1.0 + normalizedDistance * 2.0 // 遠距離脈衝更快
  };
};
```

#### 3.3 動態視角控制
```typescript
// 智能相機控制，確保重要衛星始終可見
const CameraController = {
  autoFocus: (activeSatellites: SatelliteData[]) => {
    // 自動調整視角包含所有活躍連接
    const bounds = calculateBounds(activeSatellites);
    camera.position.set(...optimalViewpoint(bounds));
  },
  
  followHandover: (sourceSat: string, targetSat: string) => {
    // 換手時跟隨目標衛星
  }
};
```

**Phase 3 驗收標準：**
- [ ] 90° 衛星距離顯示為 0.86 場景單位 (對應真實 550km)
- [ ] 10° 衛星距離顯示為 13.4 場景單位 (對應真實 8554km)  
- [ ] 連接線顏色正確反映距離範圍 (綠/黃/紅)
- [ ] 視角控制能自動包含所有可見的高品質衛星

### Phase 4: D2 Events 真實數據整合 (1-2週)

**目標**：D2 events 使用真實衛星軌道和距離數據，與 3D 動畫完全同步

#### 4.1 整合真實軌道數據到 D2 Chart
```typescript
// 修改：simworld/frontend/src/services/realD2DataService.ts
export class RealD2DataService {
  constructor(private unifiedManager: UnifiedSatelliteDataManager) {}
  
  async generateRealD2Data(duration: number): Promise<D2DataPoint[]> {
    const timePoints = this.generateTimeSequence(duration);
    const dataPoints: D2DataPoint[] = [];
    
    for (const timestamp of timePoints) {
      // 獲取該時刻的真實衛星位置
      const satellites = await this.unifiedManager.getSatellitesAtTime(timestamp);
      
      // 計算真實距離
      const distances = satellites.map(sat => 
        this.calculateSlantRange(sat.position, observerPosition)
      );
      
      dataPoints.push({
        timestamp,
        satellite1Distance: distances[0],
        satellite2Distance: distances[1],
        // ... 其他數據點
      });
    }
    
    return dataPoints;
  }
}
```

#### 4.2 實現 D2 Events 與 3D 動畫同步
```typescript
// 新建：simworld/frontend/src/hooks/useD2Animation Sync.ts
export const useD2AnimationSync = () => {
  const [currentTimeIndex, setCurrentTimeIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // 同步控制 D2 Chart 和 3D 場景的時間軸
  const syncTimeUpdate = (timeIndex: number) => {
    setCurrentTimeIndex(timeIndex);
    
    // 通知 D2 Chart 更新游標位置
    d2ChartRef.current?.updateCursor(timeIndex);
    
    // 通知 3D 場景更新衛星位置和連接狀態
    handoverAnimationRef.current?.updateAtTime(timeIndex);
  };
  
  return { currentTimeIndex, isPlaying, syncTimeUpdate };
};
```

#### 4.3 真實 D2 事件觸發邏輯
```typescript
// 基於真實距離變化的 D2 事件檢測
const detectD2Events = (dataPoints: D2DataPoint[], thresholds: D2Thresholds) => {
  const events: D2Event[] = [];
  
  for (let i = 1; i < dataPoints.length; i++) {
    const prev = dataPoints[i-1];
    const curr = dataPoints[i];
    
    // 基於真實路徑損耗計算信號變化
    const pathLoss1 = calculatePathLoss(curr.satellite1Distance);
    const pathLoss2 = calculatePathLoss(curr.satellite2Distance);
    
    // 3GPP TS 38.331 事件觸發條件
    if (pathLoss1 - prev.pathLoss1 > thresholds.hysteresis && 
        pathLoss2 + prev.pathLoss2 < thresholds.threshold2) {
      events.push({
        type: 'D2_ENTER',
        timestamp: curr.timestamp,
        triggerSatellite: 'satellite2',
        distance: curr.satellite2Distance
      });
    }
  }
  
  return events;
};
```

**Phase 4 驗收標準：**
- [ ] D2 Chart 顯示基於真實軌道計算的衛星距離曲線
- [ ] 距離範圍符合物理實際 (550km - 8554km)
- [ ] D2 事件觸發基於真實信號品質變化 (路徑損耗計算)
- [ ] 動畫播放時 Chart 游標與 3D 換手動畫完全同步

### Phase 5: 用戶控制整合與優化 (1週)

**目標**：確保 sidebar 控制參數能正確影響所有組件，提供流暢的用戶體驗

#### 5.1 統一控制參數響應
```typescript
// 修改：simworld/frontend/src/components/layout/EnhancedSidebar/SatelliteControls.tsx
const SatelliteControlsIntegration = {
  onConstellationChange: (constellation: string) => {
    // 同時影響：sidebar 顯示、3D 渲染、d2 events 數據源
    unifiedManager.setConstellation(constellation);
    d2DataService.refreshData();
    handoverAnimation.updateSatelliteList();
  },
  
  onSpeedMultiplierChange: (speed: number) => {
    // 同時調整：軌道動畫速度、換手動畫速度、d2 播放速度
    satelliteRenderer.setSpeedMultiplier(speed);
    handoverAnimation.setSpeedMultiplier(speed);
    d2Chart.setPlaybackSpeed(speed);
  },
  
  onHandoverSettingsChange: (settings: HandoverSettings) => {
    // 影響：換手時機、穩定期、d2 事件閾值
    handoverAnimation.updateSettings(settings);
    d2EventDetector.updateThresholds(settings.thresholds);
  }
};
```

#### 5.2 性能優化和緩存策略
```typescript
// 智能數據更新策略
const DataUpdateStrategy = {
  // 根據控制面板狀態調整更新頻率
  getUpdateInterval: (isAnimating: boolean, speedMultiplier: number) => {
    if (!isAnimating) return 30000; // 靜態時 30 秒更新
    if (speedMultiplier > 10) return 1000; // 高速時 1 秒更新  
    return 5000; // 正常動畫 5 秒更新
  },
  
  // 緩存管理
  cacheStrategy: {
    satellitePositions: '10 minutes',
    d2DataPoints: '1 hour', 
    tleMasterData: '24 hours'
  }
};
```

#### 5.3 用戶體驗增強
```typescript
// 數據來源透明度
const DataSourceIndicator = () => (
  <div className="data-source-panel">
    <Badge color={dataSource.isReal ? 'green' : 'orange'}>
      {dataSource.isReal ? '真實 TLE 數據' : '模擬數據'}
    </Badge>
    <Tooltip content={`
      數據來源: ${dataSource.source}
      更新時間: ${dataSource.lastUpdate}
      計算精度: ±${dataSource.accuracy}km
    `}>
      <InfoIcon />
    </Tooltip>
  </div>
);
```

**Phase 5 驗收標準：**
- [ ] 衛星星座控制能同時影響 sidebar、3D 場景、d2 events
- [ ] 衛星移動速度控制同步調整所有動畫組件
- [ ] 換手參數調整即時反映在動畫和事件檢測中
- [ ] UI 明確標示數據來源和精度資訊
- [ ] 系統響應時間 < 500ms，動畫流暢無卡頓

## 🔧 技術實施細節

### 關鍵常數和配置

#### 物理參數
```python
# 衛星軌道參數
STARLINK_ALTITUDE = 550  # km
EARTH_RADIUS = 6371      # km  
ORBIT_PERIOD = 90 * 60   # 90 分鐘，秒為單位

# 觀察者位置（台北）
OBSERVER_POSITION = {
    'latitude': 24.9441,   # 24°56'39"N
    'longitude': 121.3717, # 121°22'17"E  
    'altitude': 0.050      # 50m 海拔
}
```

#### 通訊參數
```python
# 頻率和信號計算
KU_BAND_FREQUENCY = 14.0e9  # 14 GHz
FREE_SPACE_CONSTANT = 32.44  # dB

# D2 事件閾值 (基於論文研究優化)
D2_THRESHOLDS = {
    'hysteresis': 3.0,      # 3 dB，平衡性能
    'threshold1': -100.0,   # dBm，服務閾值
    'threshold2': -110.0,   # dBm，換手閾值
    'time_to_trigger': 320  # ms，符合 3GPP
}
```

#### 視覺渲染參數
```typescript
// 3D 場景配置
const SCENE_CONSTANTS = {
  EARTH_RADIUS: 10.0,           // 場景單位
  SCALE_RATIO: 10.0 / 6371,     // 真實km到場景單位
  SATELLITE_HEIGHT: 550 * SCALE_RATIO, // 0.86 場景單位
  
  // 距離顏色映射
  DISTANCE_COLORS: {
    EXCELLENT: '#00ff00',  // < 1200km，綠色
    GOOD: '#ffff00',       // 1200-3000km，黃色  
    MARGINAL: '#ff0000'    // > 3000km，紅色
  }
};
```

### 資料流架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Celestrak     │    │   NetStack API   │    │  Unified Data   │
│   TLE Data      │───▶│   SGP4 Service   │───▶│   Manager       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────────┐
                              ▼                          ▼                          ▼
                    ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
                    │   Sidebar       │        │   3D Renderer   │        │   D2 Events     │
                    │   Satellite gNB │        │   Satellite     │        │   Chart         │
                    └─────────────────┘        └─────────────────┘        └─────────────────┘
```

### 錯誤處理策略

```typescript
// 數據降級策略
const DataFallbackStrategy = {
  primary: 'Real TLE + SGP4',
  secondary: 'Cached real data',  
  tertiary: 'High-quality simulation',
  emergency: 'Basic simulation',
  
  switchConditions: {
    'SGP4 calculation timeout': 'secondary',
    'Network unavailable': 'secondary', 
    'Cache expired + network error': 'tertiary',
    'All systems failure': 'emergency'
  }
};
```

## 📋 驗收測試清單

### 功能驗收測試

#### 基本功能
- [ ] 系統啟動後顯示台北地區可見的真實 Starlink 衛星 (8-12 顆)
- [ ] Sidebar 衛星 gNB 數量與 3D 場景完全一致
- [ ] 衛星名稱、仰角、信號品質數據同步更新
- [ ] 衛星移動速度控制正常工作 (1x-10x)

#### 距離計算驗證
- [ ] 90° 衛星距離 = 550km (垂直上方)
- [ ] 25° 衛星距離約 7157km (地平線附近)
- [ ] 3D 場景距離比例正確 (1:637 縮放)
- [ ] 連接線顏色正確反映距離 (綠/黃/紅)

#### D2 Events 同步
- [ ] D2 Chart 顯示真實軌道計算的距離曲線
- [ ] 事件觸發符合 3GPP TS 38.331 標準
- [ ] Chart 游標與 3D 換手動畫時間軸同步
- [ ] 動畫速度調整同時影響 Chart 和 3D 場景

### 性能測試
- [ ] 衛星數據更新響應時間 < 500ms
- [ ] 3D 動畫幀率 > 30fps (60fps 目標)
- [ ] 記憶體使用 < 2GB
- [ ] 長時間運行穩定 (> 4 小時無崩潰)

### 準確性測試
- [ ] SGP4 計算偏差 < 50km (相比 Skyfield)
- [ ] 台北可見衛星數量符合理論預期 (8-12 顆 @ 10°)
- [ ] 路徑損耗計算符合 ITU-R 公式
- [ ] 換手時機決策合理 (無頻繁 ping-pong)

## 🚨 風險控制與備案

### 風險識別
1. **SGP4 精度問題**：可能需要整合第三方軌道計算庫
2. **性能瓶頸**：大量衛星即時計算可能影響動畫流暢度  
3. **API 依賴**：Celestrak/NetStack API 服務不穩定
4. **視覺複雜度**：3D 場景可能過於複雜影響用戶體驗

### 備案計畫
1. **精度備案**：若 SGP4 精度無法提升，使用 Skyfield Python 庫包裝
2. **性能備案**：實施數據預計算和智能緩存
3. **服務備案**：建立本地 TLE 數據備份和離線模式
4. **體驗備案**：提供簡化模式和進階模式切換

## 📈 成功指標

### 技術指標
- **數據真實性**: 90%+ 真實數據，符合頂級期刊要求
- **計算精度**: < 1% 誤差，與標準軟體一致  
- **系統性能**: < 100ms 響應時間，60fps 動畫
- **穩定性**: > 99% 正常運行時間

### 用戶體驗指標  
- **直觀性**: 用戶能直觀理解衛星位置和換手過程
- **一致性**: 所有組件顯示數據完全一致
- **控制性**: 所有控制參數立即生效且影響明確
- **教育性**: 系統能有效展示 LEO 衛星通訊原理

### 學術價值指標
- **論文支撐**: 數據品質支援 IEEE 期刊級論文發表
- **創新性**: 真實數據與 3D 動畫的創新整合
- **可重現性**: 研究結果可被其他研究者驗證
- **實用性**: 系統可應用於教學和產業演示

---

**計畫制定時間**: 2025年1月22日  
**預計完成時間**: 2025年3月15日 (8週)  
**責任人**: NTN Stack 開發團隊  
**優先級**: 高 (論文研究核心需求)

---

*此計畫基於 NTN Stack 系統深度分析結果制定，確保所有改進都建立在現有架構基礎上，最大化開發效率並最小化系統風險。*

## 🎨 D2 Events 立體圖整合呈現方案

### 📋 當前 UI 架構分析
- **立體圖**：主頁面內容區（activeComponent === '3DRT'）
- **D2 Events**：Modal 覆蓋層（MeasurementEventsModal）
- **問題**：無法同時查看，需要在兩者間切換

### 🎯 整合呈現方案設計

## **方案一：智能懸浮面板 (推薦)** ⭐⭐⭐⭐⭐

```typescript
// 特色：可拖拽、半透明、智能定位
interface FloatingD2Panel {
  position: 'top-right' | 'bottom-left' | 'custom';
  opacity: 0.9;          // 半透明不遮擋 3D 場景
  isDraggable: true;     // 用戶可自由定位
  isCollapsible: true;   // 可收縮為小圖示
  syncMode: 'realtime';  // 與 3D 動畫實時同步
}
```

**優勢**：
- ✅ 不遮擋主要 3D 場景視野
- ✅ 用戶可自定義最佳觀看位置
- ✅ 實現技術成熟，風險低
- ✅ 適合學術演示和論文展示

## **方案二：3D 場景 HUD 整合** ⭐⭐⭐⭐

```typescript
// 直接嵌入 3D 場景的 HUD 系統
interface Scene3DHUD {
  chartPosition: 'bottom-overlay';   // 場景底部
  chartSize: '30%';                  // 佔用場景 30% 高度
  backgroundBlur: true;              // 背景模糊效果
  autoHide: 'on-interaction';        // 交互時自動隱藏
}
```

**優勢**：
- ✅ 完全整合的使用體驗
- ✅ Chart 與 3D 動畫在同一視窗內
- ✅ 現代感的 HUD 設計
- ⚠️ 實現複雜度較高

## **方案三：響應式分屏模式** ⭐⭐⭐

```typescript
// 智能分屏布局
interface SplitScreenLayout {
  mode: 'horizontal' | 'vertical' | 'adaptive';
  ratio: '70:30' | '60:40';          // 3D:Chart 比例
  responsiveBreakpoint: 1200;        // 小螢幕自動切換
  transitionDuration: '300ms';       // 平滑過渡動畫
}
```

**優勢**：
- ✅ 充分利用螢幕空間
- ✅ 兩個視圖同等重要性
- ⚠️ 螢幕空間縮減可能影響細節觀察

## **方案四：側邊欄深度整合** ⭐⭐⭐

```typescript
// 擴展現有 sidebar 功能
interface SidebarIntegratedChart {
  expandedMode: true;                // 側邊欄可擴展模式
  chartSection: 'dedicated';         // 專用圖表區域
  collapsible: true;                 // 可收縮節省空間
  miniPreview: true;                 // 收縮時顯示小預覽
}
```

**優勢**：
- ✅ 充分利用現有 sidebar 架構
- ✅ 與衛星控制面板邏輯一致
- ⚠️ 可能需要較寬的 sidebar

### 🏆 最終推薦：組合式解決方案

```typescript
// 多模式切換的彈性設計
interface FlexibleD2Integration {
  defaultMode: 'floating';           // 預設懸浮面板
  availableModes: [
    'floating',     // 可拖拽懸浮面板  
    'hud',          // 3D HUD 整合
    'sidebar',      // 側邊欄整合
    'split',        // 分屏模式
    'modal'         // 傳統模態框（保留）
  ];
  userPreference: 'persistent';      // 記住用戶偏好
  quickToggle: 'F2_key';            // 快速切換模式
}
```

### 🎮 用戶操作流程設計

1. **進入立體圖**：點擊 navbar "立體圖"
2. **啟動同步模式**：sidebar > 衛星控制 > "D2 事件同步"開關
3. **選擇呈現模式**：右上角模式切換器
4. **自定義布局**：拖拽調整 D2 面板位置
5. **同步控制**：sidebar 速度控制同時影響 3D 和 Chart

### 📊 實現優先級

#### **Phase 4.4: D2 Events 視覺整合** (新增階段，1-2週)

**目標**：實現 D2 Events 與立體圖的同步視覺呈現

##### 4.4.1 基礎懸浮面板實現
```typescript
// 新建：simworld/frontend/src/components/shared/ui/FloatingD2Panel.tsx
export const FloatingD2Panel: React.FC<FloatingD2PanelProps> = ({
  isVisible,
  position,
  onPositionChange,
  children
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [panelPosition, setPanelPosition] = useState(position);
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  return (
    <div 
      className={`floating-d2-panel ${isCollapsed ? 'collapsed' : ''}`}
      style={{
        position: 'fixed',
        top: panelPosition.y,
        left: panelPosition.x,
        opacity: 0.95,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(8px)',
        borderRadius: '8px',
        zIndex: 1000
      }}
      onMouseDown={handleDragStart}
    >
      <div className="panel-header">
        <span>D2 Events</span>
        <button onClick={() => setIsCollapsed(!isCollapsed)}>
          {isCollapsed ? '📈' : '📉'}
        </button>
      </div>
      {!isCollapsed && (
        <div className="panel-content">
          {children}
        </div>
      )}
    </div>
  );
};
```

##### 4.4.2 立體圖組件整合
```typescript
// 修改：simworld/frontend/src/components/scenes/MainScene.tsx 
// (或對應的立體圖主組件)
const MainScene3D: React.FC = () => {
  const [showD2Panel, setShowD2Panel] = useState(false);
  const [d2PanelMode, setD2PanelMode] = useState<'floating' | 'hud' | 'sidebar'>('floating');
  
  // 監聽 sidebar 的 D2 事件同步開關
  useEffect(() => {
    const handleD2SyncToggle = (enabled: boolean) => {
      setShowD2Panel(enabled);
    };
    
    eventBus.on('d2-sync-toggle', handleD2SyncToggle);
    return () => eventBus.off('d2-sync-toggle', handleD2SyncToggle);
  }, []);
  
  return (
    <div className="scene-3d-container">
      {/* 主要 3D 場景 */}
      <Canvas>
        <HandoverAnimation3D />
        <DynamicSatelliteRenderer />
      </Canvas>
      
      {/* D2 Events 整合面板 */}
      {showD2Panel && d2PanelMode === 'floating' && (
        <FloatingD2Panel
          position={{ x: window.innerWidth * 0.7, y: 50 }}
          isVisible={showD2Panel}
        >
          <PureD2Chart 
            syncWithAnimation={true}
            compactMode={true}
          />
        </FloatingD2Panel>
      )}
      
      {/* HUD 模式整合 */}
      {showD2Panel && d2PanelMode === 'hud' && (
        <div className="scene-hud-overlay">
          <div className="hud-d2-chart">
            <PureD2Chart syncWithAnimation={true} />
          </div>
        </div>
      )}
    </div>
  );
};
```

##### 4.4.3 Sidebar 控制整合
```typescript
// 修改：simworld/frontend/src/components/layout/EnhancedSidebar/components/SatelliteControls.tsx
const SatelliteControlsSection: React.FC = () => {
  const [d2SyncEnabled, setD2SyncEnabled] = useState(false);
  const [d2DisplayMode, setD2DisplayMode] = useState<DisplayMode>('floating');
  
  const handleD2SyncToggle = (enabled: boolean) => {
    setD2SyncEnabled(enabled);
    // 通知立體圖組件
    eventBus.emit('d2-sync-toggle', enabled);
  };
  
  return (
    <div className="satellite-controls-section">
      {/* 現有的衛星控制 */}
      
      {/* 新增：D2 事件同步控制 */}
      <div className="control-group">
        <h4>📊 D2 事件同步</h4>
        
        <div className="control-item">
          <label>
            <input
              type="checkbox"
              checked={d2SyncEnabled}
              onChange={(e) => handleD2SyncToggle(e.target.checked)}
            />
            啟用 D2 事件同步顯示
          </label>
        </div>
        
        {d2SyncEnabled && (
          <div className="control-item">
            <label>顯示模式：</label>
            <select 
              value={d2DisplayMode}
              onChange={(e) => setD2DisplayMode(e.target.value as DisplayMode)}
            >
              <option value="floating">懸浮面板</option>
              <option value="hud">HUD 整合</option>
              <option value="sidebar">側邊欄</option>
              <option value="split">分屏模式</option>
            </select>
          </div>
        )}
        
        {d2SyncEnabled && (
          <div className="d2-sync-status">
            <small>
              🔄 與立體圖實時同步
              <br />
              📍 基於台北座標真實計算
            </small>
          </div>
        )}
      </div>
    </div>
  );
};
```

##### 4.4.4 同步動畫控制
```typescript
// 新建：simworld/frontend/src/hooks/useD2SyncController.ts
export const useD2SyncController = () => {
  const [syncTimeIndex, setSyncTimeIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  
  // 統一的時間軸控制
  const updateTimeIndex = useCallback((newIndex: number) => {
    setSyncTimeIndex(newIndex);
    
    // 同步 D2 Chart 游標
    eventBus.emit('d2-chart-cursor-update', newIndex);
    
    // 同步 3D 動畫時間
    eventBus.emit('3d-animation-time-update', newIndex);
    
    // 同步換手動畫狀態
    eventBus.emit('handover-animation-sync', {
      timeIndex: newIndex,
      isPlaying
    });
  }, [isPlaying]);
  
  // 播放控制
  const play = useCallback(() => {
    setIsPlaying(true);
    eventBus.emit('sync-play', { speed: playbackSpeed });
  }, [playbackSpeed]);
  
  const pause = useCallback(() => {
    setIsPlaying(false);
    eventBus.emit('sync-pause');
  }, []);
  
  // 速度控制
  const setSpeed = useCallback((speed: number) => {
    setPlaybackSpeed(speed);
    eventBus.emit('sync-speed-change', speed);
  }, []);
  
  return {
    syncTimeIndex,
    isPlaying,
    playbackSpeed,
    updateTimeIndex,
    play,
    pause,
    setSpeed
  };
};
```

**Phase 4.4 驗收標準：**
- [ ] 立體圖中能顯示可拖拽的 D2 Events 懸浮面板
- [ ] Sidebar 的"D2 事件同步"開關能控制面板顯示/隱藏
- [ ] D2 Chart 游標移動時，3D 場景中對應衛星連接線高亮
- [ ] 3D 換手動畫觸發時，D2 Chart 對應時間點標記
- [ ] 播放速度控制同時影響 Chart 和 3D 動畫
- [ ] 面板位置和模式選擇能持久化保存

### 🎯 預期視覺效果

**默認布局**：
- 3D 立體圖佔據主要視野（約 70% 螢幕空間）
- D2 Chart 懸浮面板位於右上角（約 25% 空間）
- 半透明背景確保不干擾 3D 場景觀察
- 面板可拖拽到用戶偏好位置

**同步動畫效果**：
- Chart 播放時，游標在距離曲線上移動
- 對應時刻的 3D 衛星連接線同步高亮和脈衝
- 換手事件觸發時，兩個視圖同時標記關鍵時間點
- 衛星移動速度調整同時影響軌道動畫和圖表播放速度

**學術演示價值**：
- 清晰展示真實 Starlink 衛星軌道數據
- 直觀呈現 UE-衛星距離變化和換手決策過程  
- 符合 3GPP 標準的 D2 事件觸發邏輯
- 專業的視覺呈現適合會議報告和論文配圖

這種整合設計不僅提供了靈活的用戶體驗選擇，還確保了學術研究和演示的專業性要求。
