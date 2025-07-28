# 🛰️ NTN Stack 衛星架構重構開發計畫 (Sky Project)

## 🎯 專案概述

### 📋 核心目標
本計畫旨在解決 NTN Stack 中 SimWorld 和 NetStack 之間的衛星計算功能重複問題，並整合獨立的 Starlink 衛星篩選工具。

### 🚨 問題分析
- **架構重複**: SimWorld backend 和 NetStack 都有 skyfield 依賴
- **職責混亂**: 衛星軌道計算應集中在 NetStack，SimWorld 應專注於 3D 仿真
- **依賴衝突**: 不同版本的 skyfield 可能導致計算結果不一致
- **維護困難**: 相同功能分散在多個服務中難以維護

### 🏗️ 目標架構
```
🌐 SimWorld Frontend
    ↓ (API 調用)
🎮 SimWorld Backend (純3D仿真)
    ↓ (衛星數據請求)
🛰️ NetStack API (衛星計算中心)
    ↓ (本地TLE數據讀取)
📂 45天收集TLE數據 (/tle_data/)
    ├── starlink/ (45個每日文件)
    └── oneweb/ (45個每日文件)
```

## 🚀 開發步驟流程

### Phase 0: 本地 TLE 數據收集與換手篩選工具 (45天收集 + 1天分析) ⚡ **可立即開始**

#### 0.1 45天本地 TLE 數據收集基礎設施
**目標**: 建立每日 TLE 數據收集系統，支援 45 天 RL 研究數據需求

**數據收集架構**:
```bash
# 實際的數據收集結構 (基於實際日期命名)
/home/sat/ntn-stack/tle_data/
├── starlink/                         # Starlink 數據目錄
│   ├── tle/                         # TLE 格式數據
│   │   ├── starlink_20250727.tle   # 基於數據實際日期
│   │   ├── starlink_20250728.tle   # 智能日期命名
│   │   └── ...                      # 收集期間的所有日期
│   └── json/                        # JSON 格式數據
│       ├── starlink_20250727.json  # 與 TLE 使用相同日期
│       ├── starlink_20250728.json
│       └── ...
└── oneweb/                           # OneWeb 數據目錄
    ├── tle/
    │   ├── oneweb_20250727.tle     # 基於數據實際日期
    │   └── ...
    └── json/
        ├── oneweb_20250727.json    # 與 TLE 使用相同日期
        └── ...
```

**核心功能**:
- [x] **數據目錄結構建立** - 支援 TLE + JSON 雙格式
- [x] **智能檔案命名** - 基於數據實際日期而非下載日期
- [x] **自動化收集工具** - 增強版下載腳本支援智能更新檢查
- [ ] **本地TLE數據加載器** - 從收集的文件讀取歷史數據
- [ ] **數據完整性檢查** - 驗證每日數據品質和連續性
- [ ] **建置時數據預處理** - Docker建置階段處理所有45天數據

#### 0.2 本地數據加載與驗證系統
**目標**: 處理用戶手動收集的真實 TLE 歷史數據

```python
# 本地數據加載器增強 (支援實際日期命名和雙格式)
def load_collected_tle_data(constellation='starlink', start_date=None, end_date=None):
    """
    載入手動收集的TLE歷史數據
    - 自動掃描可用的日期檔案 (YYYYMMDD 格式)
    - 支援 TLE 和 JSON 雙格式讀取
    - 驗證格式完整性和數據品質
    - 支援 Starlink 和 OneWeb 雙星座
    - 可指定日期範圍或自動檢測
    """
    tle_dir = f"/app/tle_data/{constellation}/tle/"
    json_dir = f"/app/tle_data/{constellation}/json/"
    collected_data = []
    available_dates = []
    
    # 掃描可用的 TLE 檔案日期
    import glob
    import re
    
    tle_pattern = f"{tle_dir}{constellation}_*.tle"
    tle_files = glob.glob(tle_pattern)
    
    for tle_file in tle_files:
        # 提取日期 (YYYYMMDD)
        match = re.search(r'(\d{8})\.tle$', tle_file)
        if match:
            date_str = match.group(1)
            
            # 檢查日期範圍過濾
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
                
            if file_exists_and_valid(tle_file):
                # 檢查對應的 JSON 檔案
                json_file = f"{json_dir}{constellation}_{date_str}.json"
                has_json = file_exists_and_valid(json_file)
                
                # 解析 TLE 數據
                daily_tle_data = parse_tle_file(tle_file)
                daily_json_data = parse_json_file(json_file) if has_json else None
                
                collected_data.append({
                    'date': date_str,
                    'tle_file': tle_file,
                    'json_file': json_file if has_json else None,
                    'satellite_count': len(daily_tle_data),
                    'tle_data': daily_tle_data,
                    'json_data': daily_json_data,
                    'has_dual_format': has_json
                })
                available_dates.append(date_str)
    
    # 按日期排序
    collected_data.sort(key=lambda x: x['date'])
    available_dates.sort()
    
    return {
        'constellation': constellation,
        'total_days_collected': len(collected_data),
        'date_range': {
            'start': available_dates[0] if available_dates else None,
            'end': available_dates[-1] if available_dates else None,
            'available_dates': available_dates
        },
        'dual_format_coverage': sum(1 for d in collected_data if d['has_dual_format']),
        'coverage_percentage': len(collected_data) / len(available_dates) * 100 if available_dates else 0,
        'daily_data': collected_data
    }
```

**驗證標準**:
- [x] **格式正確性** - 所有TLE行符合標準格式(69字符) ✅ 已實現
- [ ] **時間連續性** - 檢查45天數據的時間跨度 (目前只有1天數據)
- [x] **星座完整性** - Starlink(7,996顆) + OneWeb(651顆) ✅ 已驗證
- [x] **軌道參數合理性** - 高度、傾角、週期在合理範圍 ✅ Phase 0.2 已完成

#### 0.3 Docker建置時預計算整合
**目標**: 在容器建置階段處理手動收集的歷史數據，實現RL研究需求

```dockerfile
# 修改後的Dockerfile預計算整合
# 位置: /netstack/docker/Dockerfile

# 複製手動收集的TLE數據到容器 (支援TLE+JSON雙格式)
COPY ../tle_data/ /app/tle_data/

# 建置時預計算基於實際收集數據的軌道計算
RUN python3 generate_precomputed_satellite_data.py \
    --tle_source local_collection \
    --input_dir /app/tle_data \
    --output /app/data/rl_research_collected_data.sql \
    --observer_lat 24.94417 --observer_lon 121.37139 \
    --time_step_seconds 30 \
    --constellations starlink,oneweb \
    --auto_detect_date_range \
    --support_dual_format
```

**建置階段增強功能**:
```python
# 建置時數據處理邏輯 (generate_precomputed_satellite_data.py)
def process_collected_data():
    """
    處理手動收集的數據，支援實際日期命名
    """
    # 1. 自動掃描可用的數據檔案
    starlink_data = load_collected_tle_data('starlink')
    oneweb_data = load_collected_tle_data('oneweb')
    
    # 2. 檢查數據覆蓋率和品質
    total_days = len(set(starlink_data['date_range']['available_dates'] + 
                        oneweb_data['date_range']['available_dates']))
    
    print(f"📊 建置時數據統計:")
    print(f"  - Starlink: {starlink_data['total_days_collected']} 天數據")
    print(f"  - OneWeb: {oneweb_data['total_days_collected']} 天數據") 
    print(f"  - 總覆蓋期間: {total_days} 天")
    print(f"  - 雙格式支援: {starlink_data['dual_format_coverage']}/Starlink + {oneweb_data['dual_format_coverage']}/OneWeb")
    
    # 3. 預計算軌道數據
    return precompute_orbital_data(starlink_data, oneweb_data)
```

**預計算增強功能**:
- [x] **智能日期掃描** - 自動檢測可用數據的日期範圍，無需固定45天 ✅ 已實現
- [x] **雙格式支援** - 同時處理 TLE 和 JSON 格式數據 ✅ 已實現
- [x] **多星座支援** - 同時處理Starlink和OneWeb歷史數據 ✅ 已實現
- [ ] **真正的軌道預計算** - 當前只是統計，需實現 SGP4 軌道計算
- [ ] **時間軸重建** - 基於實際收集日期重現歷史軌道演化 
- [ ] **數據品質評估** - 建置時檢查數據完整性和覆蓋率
- [ ] **RL訓練數據格式** - 產出適合強化學習的標準化數據集

**⚠️ Phase 0.3 關鍵未完成項目**:
1. **真正的軌道預計算** - 目前 build_with_phase0_data.py 只做統計，未進行 SGP4 計算
2. **預計算檔案輸出** - 需要生成實際的軌道位置數據，而非僅 metadata
3. **容器內軌道數據** - Docker 映像應包含預計算的軌道軌跡，非僅原始 TLE

#### 0.4 座標特定軌道預計算引擎與換手分析
**目標**: 實現可配置座標的軌道預計算引擎，支援即時展示和研究需求

**核心功能設計**:
```python
class CoordinateSpecificOrbitEngine:
    """座標特定軌道預計算引擎 - 支援任意觀測點"""
    
    def __init__(self, observer_lat: float, observer_lon: float, 
                 observer_alt: float = 0.0, min_elevation: float = 5.0):
        """
        初始化引擎
        Args:
            observer_lat: 觀測點緯度 (度)
            observer_lon: 觀測點經度 (度) 
            observer_alt: 觀測點海拔 (米)
            min_elevation: 最小仰角閾值 (度)
        """
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.observer_alt = observer_alt
        self.min_elevation = min_elevation
    
    def compute_96min_orbital_cycle(self, satellite_tle_data):
        """
        計算96分鐘完整軌道週期的可見性
        - 基於真實 TLE 數據進行 SGP4 軌道計算
        - 生成30秒間隔的位置序列
        - 計算仰角、方位角、距離
        - 識別可見性窗口 (仰角 ≥ min_elevation)
        """
        pass
    
    def filter_visible_satellites(self, all_satellites):
        """
        衛星可見性篩選器
        - 篩選掉永遠無法到達最小仰角的衛星
        - 大幅減少後續計算量 (預期可減少60-80%衛星)
        - 返回篩選後的「可換手衛星清單」
        """
        pass
    
    def find_optimal_timewindow(self, filtered_satellites, window_hours=6):
        """
        最佳時間窗口識別
        - 在24小時內找出指定時長的最佳窗口
        - 以可見衛星數量、換手機會為評估標準
        - 考慮前端展示需求 (動畫加速、距離縮放)
        """
        pass
    
    def generate_display_optimized_data(self, optimal_window_data):
        """
        前端展示優化數據生成
        - 考慮60倍加速動畫的時間壓縮
        - 距離大幅縮減的視覺效果調整
        - 平滑的衛星軌跡插值
        - 換手事件的動畫時序優化
        """
        pass

# 預設座標配置 (可擴展到其他觀測點)
NTPU_COORDINATES = {
    'lat': 24.94417,    # 24°56'39"N
    'lon': 121.37139,   # 121°22'17"E
    'alt': 50.0,        # 海拔50米
    'name': 'NTPU'
}

OBSERVER_LOCATIONS = {
    'ntpu': NTPU_COORDINATES,
    # 未來可添加其他觀測點
    # 'nctu': {...},
    # 'ntu': {...}
}
```

**Docker 建置時預計算整合**:
```dockerfile
# 在建置階段完成軌道預計算，避免運行時延遲
RUN python3 precompute_coordinate_orbits.py \
    --tle-data-dir /app/tle_data \
    --output-dir /app/data/precomputed \
    --observer-lat 24.94417 --observer-lon 121.37139 \
    --min-elevation 5.0 \
    --orbital-cycle-minutes 96 \
    --optimal-window-hours 6 \
    --time-step-seconds 30 \
    --display-acceleration 60 \
    --distance-scale 0.1
```

**預計算數據輸出格式**:
```json
{
  "metadata": {
    "observer_location": {"lat": 24.94417, "lon": 121.37139, "alt": 50.0},
    "computation_date": "2025-01-28T12:00:00Z",
    "orbital_cycle_minutes": 96,
    "time_step_seconds": 30,
    "total_satellites_input": 8647,
    "filtered_satellites": 2156,
    "filtering_efficiency": "75.1%"
  },
  "optimal_timewindow": {
    "start_time": "2025-01-28T14:30:00Z",
    "end_time": "2025-01-28T20:30:00Z",
    "duration_hours": 6,
    "avg_visible_satellites": 8.2,
    "max_visible_satellites": 12,
    "handover_opportunities": 34
  },
  "satellite_trajectories": [
    {
      "norad_id": 44714,
      "name": "STARLINK-1008",
      "visibility_windows": [...],
      "display_trajectory": [...],
      "handover_events": [...]
    }
  ],
  "display_optimization": {
    "animation_fps": 30,
    "acceleration_factor": 60,
    "distance_scale": 0.1,
    "trajectory_smoothing": true
  }
}
```

**Phase 0 驗收標準 (更新至實際狀態)：**

**✅ 已完成功能**:
- [x] **數據收集基礎設施** - TLE+JSON 雙格式目錄結構完全建立
- [x] **智能下載工具** - 增強版腳本支援實際日期命名和智能更新檢查
- [x] **本地數據加載器** - LocalTLELoader 支援實際日期命名的歷史數據讀取
- [x] **數據完整性檢查系統** - TLE 格式驗證、軌道參數合理性檢查 (Phase 0.2)
- [x] **Docker建置時統計預處理** - 數據掃描、配置生成、RL metadata
- [x] **換手分析框架** - Phase0HandoverAnalyzer 基礎架構 (運行時計算)
- [x] **雙星座支援** - Starlink (7,996顆) 和 OneWeb (651顆) 數據驗證
- [x] **完整測試驗證** - 100% 測試通過率，綜合驗證報告

**🚧 Phase 0.1-0.3 未完成功能 (需優先開發)**:
- [ ] **Phase 0.1 - 時間連續性檢查** - 45天數據連續性驗證 (目前只有1天)
- [ ] **Phase 0.3 - 真正的軌道預計算** - SGP4軌道計算取代統計預處理
- [ ] **Phase 0.3 - 軌道數據檔案輸出** - 生成實際軌道位置數據
- [ ] **Phase 0.3 - 容器內軌道數據嵌入** - Docker映像包含預計算軌跡

**🚧 Phase 0.4 新功能 (核心目標)**:
- [ ] **座標特定軌道預計算引擎** - CoordinateSpecificOrbitEngine 實現
- [ ] **96分鐘軌道週期可見性計算** - 完整軌道週期 SGP4 計算
- [ ] **衛星可見性篩選器** - 5度仰角閾值過濾，減少60-80%計算量
- [ ] **最佳6小時時間窗口識別** - 基於可見衛星數量的最佳時段
- [ ] **前端展示優化數據生成** - 60倍加速、距離縮放的動畫優化
- [ ] **Docker建置時軌道預計算整合** - precompute_coordinate_orbits.py
- [ ] **預計算數據檔案輸出** - JSON格式的軌道軌跡和換手事件

**📊 數據收集狀況**:
- [ ] **45天歷史數據收集** - 當前僅1天數據 (20250727)，可並行進行

**📊 數據現狀 (基於1天數據)**:
- **總衛星數**: 8,647 顆 (Starlink: 7,996 + OneWeb: 651)
- **數據品質**: 100% TLE 格式正確，軌道參數全部在合理範圍
- **覆蓋日期**: 2025-07-27 (1天基線數據)
- **雙格式支援**: 100% (TLE + JSON 對應文件)

**⚡ 開發優先級建議**:

**🔥 緊急優先 (Phase 0.3 修復)**:
1. **實現真正的 SGP4 軌道預計算** - 修復 build_with_phase0_data.py
2. **生成軌道數據檔案** - 輸出實際軌道位置，非僅統計
3. **Docker建置時軌道嵌入** - 容器包含預計算數據

**⭐ 高優先級 (Phase 0.4 核心)**:
4. **座標特定軌道引擎** - CoordinateSpecificOrbitEngine 實現  
5. **NTPU 座標可見性篩選** - 5度仰角閾值過濾
6. **6小時最佳時段識別** - 基於真實軌道計算

**📈 中優先級 (功能完善)**:
7. **前端展示數據優化** - 60倍加速、距離縮放
8. **45天數據收集** - 可並行進行，不阻塞開發

**🎯 Phase 0 最終完成標準**:
- [ ] Phase 0.3 軌道預計算修復：Docker建置時生成真實軌道數據
- [ ] Phase 0.4 NTPU 座標預計算：8,647 → ~2,000 顆可見衛星篩選  
- [ ] 6小時最佳時間窗口：平均8-12顆可見衛星的最佳時段
- [ ] 容器啟動時軌道數據立即可用：< 30秒啟動時間
- [ ] 預計算數據檔案：< 50MB，包含軌跡和換手事件

---

### Phase 1: NetStack 衛星 API 整合與架構優化 (2-3天)

**前置條件**: Phase 0 座標特定軌道預計算引擎已完成

#### 1.1 NetStack 衛星 API 增強
**目標**: 整合 Phase 0 預計算數據，提供統一的衛星 API 接口

```python
# /netstack/src/api/satellite/coordinate_orbit_endpoints.py
@router.get("/satellites/precomputed/{location}")
async def get_precomputed_orbit_data(
    location: str,  # 'ntpu', 'nctu' 等預定義座標
    constellation: str = "starlink",
    time_range: Optional[str] = None
):
    """
    獲取預計算的軌道數據
    - 使用 Phase 0 預計算結果
    - 支援多座標位置
    - 無需即時軌道計算
    """

@router.get("/satellites/optimal-window/{location}")
async def get_optimal_timewindow(
    location: str,
    constellation: str = "starlink",
    window_hours: int = 6
):
    """
    獲取最佳觀測時間窗口
    - 基於 Phase 0 預計算結果
    - 直接返回最佳6小時時段
    - 包含可見衛星清單和換手事件
    """

@router.get("/satellites/display-data/{location}")
async def get_display_optimized_data(
    location: str,
    acceleration: int = 60,
    distance_scale: float = 0.1
):
    """
    獲取前端展示優化數據
    - 60倍加速動畫數據
    - 距離縮放優化
    - 平滑軌跡插值
    """
```

#### 1.2 SimWorld Backend 衛星功能移除
**目標**: 移除 SimWorld 中重複的衛星計算邏輯，改用 NetStack API

```bash
# 1. 識別 SimWorld 中的衛星計算代碼
cd /home/sat/ntn-stack/simworld/backend
grep -r "skyfield\|SGP4\|EarthSatellite" . --include="*.py"

# 2. 替換為 NetStack API 調用
# 將軌道計算改為 HTTP 請求到 NetStack
```

**重構項目**:
- [ ] 移除 SimWorld requirements.txt 中的 skyfield 依賴
- [ ] 重構衛星位置計算為 NetStack API 調用
- [ ] 更新 3D 渲染邏輯使用預計算數據
- [ ] 建立 SimWorld ↔ NetStack 通信機制

#### 1.3 容器啟動順序優化
**目標**: 確保 NetStack 預計算數據在 SimWorld 啟動前準備就緒

```yaml
# docker-compose.yml 啟動順序調整
services:
  netstack-api:
    # 優先啟動，載入 Phase 0 預計算數據
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/satellites/health"]
    
  simworld-backend:
    depends_on:
      netstack-api:
        condition: service_healthy  # 等待 NetStack 健康檢查通過
```

**Phase 1 驗收標準：**
- [ ] NetStack API 完整支援預計算數據查詢
- [ ] SimWorld 不再包含 skyfield 等軌道計算依賴
- [ ] 容器啟動時間顯著減少 (目標 < 30秒)
- [ ] SimWorld 3D 渲染正常使用 NetStack 預計算數據
- [ ] 所有軌道計算統一在 NetStack 執行

### Phase 2: 前端視覺化與展示增強 (2-3天)

**前置條件**: Phase 1 NetStack API 整合完成

#### 2.1 SimWorld Frontend 軌道展示優化
**目標**: 整合 Phase 0 預計算數據，實現流暢的衛星軌跡動畫

```typescript
// /simworld/frontend/src/services/PrecomputedOrbitService.ts
class PrecomputedOrbitService {
    private netstackApiUrl: string;
    
    async loadOptimalTimeWindow(location: string = 'ntpu'): Promise<OrbitData> {
        // 從 NetStack 獲取 Phase 0 預計算的最佳6小時窗口
        const response = await fetch(
            `${this.netstackApiUrl}/satellites/optimal-window/${location}`
        );
        return response.json();
    }
    
    async getDisplayOptimizedData(
        acceleration: number = 60, 
        distanceScale: number = 0.1
    ): Promise<DisplayData> {
        // 獲取前端展示優化數據
        const response = await fetch(
            `${this.netstackApiUrl}/satellites/display-data/ntpu?acceleration=${acceleration}&distance_scale=${distanceScale}`
        );
        return response.json();
    }
}
```

#### 2.2 立體圖(navbar > 立體圖)動畫增強
**目標**: 實現基於預計算數據的平滑衛星動畫

```typescript
// 衛星軌跡動畫控制器
class SatelliteAnimationController {
    private animationSpeed: number = 60; // 60倍加速
    private distanceScale: number = 0.1;  // 距離縮放
    
    initializeAnimation(precomputedData: OrbitData) {
        // 使用 Phase 0 預計算的軌跡數據
        // 避免即時計算，確保動畫流暢
    }
    
    updateSatellitePositions(timestamp: number) {
        // 基於預計算數據插值更新位置
        // 支援時間軸控制 (播放/暫停/快進)
    }
    
    renderHandoverEvents(handoverData: HandoverEvent[]) {
        // 視覺化換手事件
        // 顯示衛星間的切換動畫
    }
}
```

#### 2.3 座標選擇與多觀測點支援
**目標**: 支援切換不同觀測座標的軌道視圖

```typescript
// 觀測點選擇組件
interface ObserverLocation {
    id: string;
    name: string;
    lat: number;
    lon: number;
    alt: number;
}

const SUPPORTED_LOCATIONS: ObserverLocation[] = [
    { id: 'ntpu', name: 'NTPU 國立台北大學', lat: 24.94417, lon: 121.37139, alt: 50 },
    // 未來可擴展其他觀測點
    // { id: 'nctu', name: 'NCTU 國立陽明交通大學', lat: 24.7881, lon: 120.9971, alt: 30 },
];

class LocationSelectorComponent {
    onLocationChange(locationId: string) {
        // 切換觀測點時重新載入對應的預計算數據
        this.orbitService.loadOptimalTimeWindow(locationId);
    }
}
```

**Phase 2 驗收標準：**
- [ ] SimWorld 前端完整整合 NetStack 預計算數據
- [ ] 立體圖動畫流暢，支援60倍加速和距離縮放
- [ ] 時間軸控制功能 (播放/暫停/快進/時間跳轉)
- [ ] 換手事件視覺化 (衛星間切換動畫)
- [ ] 支援 NTPU 座標觀測點選擇
- [ ] 容器啟動後立即可用，無需等待軌道計算

---

### Phase 3: 研究數據與 RL 整合 (2-3天)

**前置條件**: Phase 0-2 完成，具備完整的預計算軌道數據

#### 3.1 45天歷史數據收集自動化
**目標**: 建立每日自動化 TLE 數據收集機制

```python
# /netstack/scripts/daily_tle_collector.py
class DailyTLECollector:
    def __init__(self, target_days: int = 45):
        self.target_days = target_days
        self.base_dir = Path("/app/tle_data")
    
    async def collect_daily_data(self):
        """
        每日自動收集 TLE 數據
        - 智能檢查現有數據，避免重複下載
        - 支援 Starlink 和 OneWeb 雙星座
        - 自動驗證數據完整性
        - 觸發增量預計算更新
        """
        pass
    
    def validate_45day_completeness(self):
        """
        驗證45天數據集完整性
        - 檢查連續日期覆蓋
        - 驗證數據品質
        - 生成收集進度報告
        """
        pass
```

#### 3.2 RL 訓練數據集生成
**目標**: 基於 Phase 0 預計算結果生成標準化的 RL 訓練數據

```python
# /netstack/src/services/rl/rl_dataset_generator.py
class RLDatasetGenerator:
    def __init__(self, precomputed_orbit_data: Dict):
        self.orbit_data = precomputed_orbit_data
    
    def generate_handover_episodes(self):
        """
        生成換手決策 episode
        - 基於真實軌道軌跡
        - 包含狀態空間 (衛星位置、信號強度、仰角)
        - 動作空間 (目標衛星選擇、換手時機)
        - 獎勵函數 (換手成功率、服務連續性)
        """
        pass
    
    def export_ml_format(self, format_type: str = "pytorch"):
        """
        導出 ML 框架適用格式
        - PyTorch Dataset
        - TensorFlow tf.data
        - 標準 CSV/JSON 格式
        """
        pass
```

#### 3.3 學術研究支援功能
**目標**: 支援 3GPP NTN 標準和學術論文需求

```python
# 3GPP Events 生成器
class ThreeGPPEventGenerator:
    def generate_measurement_events(self, handover_data):
        """
        生成符合 3GPP TS 38.331 的測量事件
        - Event A3: 相鄰衛星信號強度比較
        - Event A5: 服務衛星信號低於閾值
        - 支援學術論文的標準化分析
        """
        pass
```

**Phase 3 驗收標準：**
- [ ] 45天完整 TLE 數據收集機制建立
- [ ] RL 訓練數據集自動生成 (支援 PyTorch/TensorFlow)
- [ ] 3GPP NTN 標準事件生成器
- [ ] 學術論文品質的數據驗證報告
- [ ] 支援多星座 (Starlink/OneWeb) 對比研究

---

### Phase 4: 部署優化與生產準備 (1-2天)

#### 4.1 容器啟動性能優化
**目標**: 確保整個系統快速啟動，預計算數據即時可用

```yaml
# docker-compose.production.yml
services:
  netstack-api:
    environment:
      - PRECOMPUTED_DATA_ENABLED=true
      - ORBIT_CACHE_PRELOAD=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/satellites/health/precomputed"]
      interval: 5s
      timeout: 3s
      retries: 3
      start_period: 10s
```

#### 4.2 監控與告警
**目標**: 建立預計算數據的健康監控

```python
# 預計算數據健康檢查
@router.get("/satellites/health/precomputed")
async def check_precomputed_health():
    """
    檢查預計算數據狀態
    - 數據完整性
    - 最後更新時間  
    - 可用座標位置
    - 記憶體使用量
    """
    pass
```

**Phase 4 驗收標準：**
- [ ] 容器啟動時間 < 30秒
- [ ] 預計算數據健康監控完整
- [ ] 支援多環境部署 (開發/測試/生產)
- [ ] 完整的錯誤處理和降級機制
- [ ] 系統整體穩定性驗證

---

## 📋 總結

### 🎯 **Sky Project 核心改變**

**Phase 0 重點調整**:
- **新增**: 座標特定軌道預計算引擎 (CoordinateSpecificOrbitEngine)
- **強化**: Docker 建置時完成軌道預計算，避免運行時延遲
- **優化**: 衛星篩選機制，減少60-80%計算量
- **支援**: NTPU 座標特定優化，可擴展至其他觀測點

**架構簡化**:
- **Phase 1-2**: 專注於 API 整合和前端視覺化  
- **Phase 3-4**: 專注於研究數據和生產部署
- **移除**: satellite-precompute-plan 中的重複內容，整合至主流程

### 🚀 **下一步實施**

1. **立即可開始**: Phase 0 座標軌道預計算引擎開發
2. **數據基礎**: 基於現有1天數據 (20250727) 驗證概念
3. **擴展目標**: 逐步收集45天歷史數據
4. **最終目標**: 實現秒級容器啟動，流暢的衛星動畫展示

**預期效果**: 容器啟動時軌道數據立即可用，前端動畫流暢展示真實的衛星換手場景。
