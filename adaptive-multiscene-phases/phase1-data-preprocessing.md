# Phase 1: 資料預處理架構與流程

## 目標
建立完整的衛星資料預處理架構，在 Docker 映像檔建構階段完成 NTPU 場景的資料計算，為 D2/A4/A5 事件檢測和 3D 視覺化提供基礎。

## 現有預處理架構

### 1.1 兩階段預處理流程

#### 第一階段：基礎軌道計算 (build_with_phase0_data.py)
在 Docker build 時執行，計算內容：
- **SGP4 軌道預測**：每 30 秒計算一次位置
  - 目前設定：96 分鐘（適合 Starlink 完整週期）
  - 問題：OneWeb 需要 ~110 分鐘才能完成一個軌道週期
  - 建議：延長至 110 分鐘以涵蓋兩個星座
- **可見性判定**：計算每顆衛星對 NTPU 的仰角，篩選 > 10° 的可見衛星
- **可見性窗口**：記錄每段可見期間的開始/結束時間、最大仰角
- **衛星數量**：Starlink 約 7996 顆、OneWeb 約 651 顆

輸出檔案：
```json
// phase0_precomputed_orbits.json 結構
{
  "generated_at": "2025-01-01T00:00:00Z",
  "observer_location": {
    "lat": 24.94417,
    "lon": 121.37139,
    "alt": 50.0,
    "name": "NTPU"
  },
  "constellations": {
    "starlink": {
      "orbit_data": {
        "satellites": {
          "48273": {  // NORAD ID
            "name": "STARLINK-1234",
            "positions": [
              {
                "time": "2025-01-01T00:00:00Z",
                "lat": 25.123,
                "lon": 121.456,
                "alt_km": 550.0,
                "elevation_deg": 45.6,
                "azimuth_deg": 123.4,
                "is_visible": true
              }
              // ... 每 30 秒一筆
              // Starlink: ~192 筆 (96分鐘)
              // OneWeb: ~220 筆 (110分鐘)
            ],
            "visibility_windows": [
              {
                "start_time": "2025-01-01T00:05:30Z",
                "end_time": "2025-01-01T00:12:30Z",
                "max_elevation": 67.8,
                "duration_seconds": 420
              }
            ]
          }
        }
      }
    }
  }
}
```

#### 第二階段：分層門檻處理 (generate_layered_phase0_data.py)
基於第一階段數據，應用三層仰角門檻：
- **預備觸發門檻**：13.5° - 開始準備換手
- **執行門檻**：11.25° - 執行換手決策
- **臨界門檻**：5.0° - 緊急換手保障

### 1.2 儲存架構
```
/netstack/data/
├── phase0_precomputed_orbits.json    # 基礎軌道數據 (~150MB)
├── phase0_data_summary.json           # 數據摘要
├── phase0_build_config.json           # 建構配置
├── layered_phase0/                    # 分層處理結果
│   ├── layered_analysis_20250727.json
│   └── layered_phase0_summary.json
└── scenes.csv                         # 場景參數表（預留多場景）
```

### 1.3 Volume 掛載策略
- **建構時**：數據生成在映像檔內的 `/app/data`
- **運行時**：透過 Docker volume 掛載，避免重複計算
- **更新機制**：當 TLE 數據更新時，重新執行建構流程

## 實施狀態更新 (2025-01-01)

### 已完成
- ✅ 刪除舊的 96 分鐘週期資料
- ✅ 保留 scenes.csv 場景參數表

### 待實現
- ⏳ 更新 build_with_phase0_data.py 為 120 分鐘週期
- ⏳ 加入 D2/A4/A5 事件檢測
- ⏳ 重新執行 Docker build

## 待實現：D2/A4/A5 事件預處理

### 1.4 軌道週期調整建議

```python
class Phase0DataPreprocessor:
    def __init__(self):
        # 針對不同星座設定不同的計算週期
        self.constellation_periods = {
            'starlink': 96,   # 分鐘
            'oneweb': 110     # 分鐘
        }
        
        # 或使用統一的較長週期
        self.unified_period_minutes = 110  # 涵蓋所有星座
```

### 1.5 事件篩選邏輯整合
需要在 `build_with_phase0_data.py` 中加入：

```python
def detect_handover_events(self, visibility_windows, elevation_thresholds):
    """檢測 D2/A4/A5 換手事件"""
    events = {
        'd2_events': [],  # 服務衛星即將消失
        'a4_events': [],  # 鄰近衛星變好
        'a5_events': []   # 服務變差且鄰近變好
    }
    
    # D2 事件：當前服務衛星仰角接近臨界門檻
    for window in visibility_windows:
        if window['min_elevation'] <= elevation_thresholds['critical'] + 2.0:
            events['d2_events'].append({
                'satellite_id': window['satellite_id'],
                'trigger_time': window['critical_approach_time'],
                'elevation_at_trigger': window['elevation_at_trigger']
            })
    
    return events
```

### 1.6 分離儲存架構
建議將資料分為兩類：
1. **軌道資料** (for 3D 視覺化)：衛星位置、速度、軌跡
2. **事件資料** (for 圖表分析)：D2/A4/A5 事件時間序列、換手統計

```
/netstack/data/
├── orbits/                           # 3D 視覺化用
│   └── ntpu_orbit_data.json         
├── events/                           # 事件分析用  
│   └── ntpu_handover_events.json
└── statistics/                       # 統計摘要
    └── ntpu_analysis_summary.json
```

## 資料量估算

基於現有數據：
- **原始 TLE**：~5MB/天 (兩個星座)
- **預計算軌道**：
  - 目前：~150MB (96分鐘週期)
  - 建議：~170MB (110分鐘週期，涵蓋 OneWeb 完整軌道)
- **可見衛星數**：同時約 20-30 顆
- **換手事件**：每小時約 10-15 次

## 效能優化建議

1. **增量更新**：只計算新增的 TLE 數據
2. **壓縮儲存**：使用 gzip 壓縮 JSON
3. **快取機制**：熱門查詢結果快取
4. **平行處理**：多核心同時計算不同衛星