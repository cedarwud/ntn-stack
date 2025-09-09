# 🔄 NTN Stack 數據處理流程

**版本**: 5.0.0 (統一資料格式架構版)  
**更新日期**: 2025-09-09  
**專案狀態**: ✅ 生產就緒 + 統一資料格式 + 即時驗證架構 + 高效處理優化  
**適用於**: LEO 衛星切換研究 - 統一資料格式 + 六階段即時驗證 + 本地數據架構

## 🎯 v5.0 重大更新
- **統一資料格式**: 消除雙重存儲架構，文件大小減少80% (6.2GB→1.2GB)
- **SimplifiedVisibilityPreFilter修復**: 解決8837顆衛星→0顆可見的數據格式適配問題  
- **高效處理**: 移除批次處理需求，直接記憶體處理1.2GB數據
- **成功結果**: 階段2現在正常輸出3200顆可見衛星 (Starlink 3033 + OneWeb 167)

## 📋 概述

本文檔詳細說明 **本地數據驅動架構** 的完整數據預處理流程：系統使用本地TLE數據，通過混合執行模式（建構時預處理 + 運行時按需更新），實現高性能的研究數據準備。

**重要澄清**：
- ✅ **本地TLE數據** - 系統使用預下載的本地TLE文件，無依賴外部API  
- ✅ **混合執行模式** - 映像檔建立時預處理 + TLE更新時增量處理 + 手動觸發支援
- ✅ **記憶體優先** - 階段間主要使用記憶體傳遞，文件存儲作為備份
- ✅ **完整SGP4算法** - 絕不使用簡化或模擬數據，保證學術研究準確性

**重要澄清**：系統使用完整的 SGP4 算法，絕不使用簡化或模擬數據。所有標記為 "simplified_for_build" 的文件僅為建構時的快速啟動數據，運行時使用 "runtime_precision" 模式。

**📋 相關文檔**：
- **系統架構**：[系統架構總覽](./system_architecture.md) - Docker 配置和組件分工
- **統一架構**：[Shared Core 統一架構](./shared_core_architecture.md) - 統一管理器和性能優化
- **技術實現**：[技術實施指南](./technical_guide.md) - 部署和開發指南
- **算法細節**：[算法實現手冊](./algorithms_implementation.md) - SGP4 和換手算法
- **階段詳解**：[stages/](./stages/) - 各階段技術實現細節

## 🚀 本地數據驅動架構 (v4.0)

### 核心理念
**本地TLE數據 + 按需處理 + 記憶體傳遞，確保研究數據的準確性和可重現性**

```
🏗️ 本地TLE準備       🚀 六階段處理          💾 數據輸出           🧠 API服務
      ↓                     ↓                    ↓                   ↓
   歷史TLE數據          手動/按需執行        結構化輸出         快速查詢服務
      ↓                     ↓                    ↓                   ↓
  /app/tle_data       記憶體+文件儲存       /app/data          PostgreSQL整合
```

### 架構優勢 (v4.0 真實實現)
- **🎯 學術研究導向** - 使用真實歷史TLE數據，確保論文數據可信度
- **⚡ 高性能處理** - 記憶體傳遞避免大文件I/O，Stage間直接數據流
- **🔄 按需執行** - 手動觸發處理，完全控制數據生成時機  
- **📁 統一數據管理** - 所有輸出集中於 `/app/data`，便於管理
- **🧹 智能清理** - 可配置文件保留策略，避免數據累積
- **🔧 統一服務架構** - shared_core 保證跨階段一致性

## 🧹 數據清理機制 (v4.1 新增)

### 清理時機與策略
系統在以下時機會自動清理舊的六階段預處理檔案：

1. **建構時清理** (`build-time-entrypoint.sh`)
   - 在 Docker 映像檔建構時，執行六階段處理前先清理所有舊檔案
   - 確保每次建構都從乾淨狀態開始

2. **運行時緊急清理** (`runtime-entrypoint.sh`)
   - 當需要緊急重新生成數據時，先清理所有舊檔案
   - 避免新舊數據混淆或衝突

3. **統一執行程式** (`run_six_stages_with_validation.py`)
   - 支援完整六階段執行和單獨階段執行
   - 內建自動清理功能，用於開發測試或問題排查
   - 使用方式: `python run_six_stages_with_validation.py [--stage N]`

### 清理目標
以下目錄和檔案會被清理：
- `/app/data/tle_calculation_outputs/`
- `/app/data/orbital_calculation_outputs/`
- `/app/data/intelligent_filtering_outputs/`
- `/app/data/signal_analysis_outputs/`
- `/app/data/timeseries_preprocessing_outputs/`
- `/app/data/data_integration_outputs/`
- `/app/data/enhanced_dynamic_pools_output.json`
- `/app/data/signal_cache/`
- `/app/data/data_integration_output.json`
- `/app/data/leo_optimization_final_report.json`

### 注意事項
- ⚠️ **Volume 持久化**：使用 bind mount 的數據會在容器重建後保留
- ⚠️ **時效性檢查**：系統應檢查檔案時間戳，避免使用過時數據
- ✅ **完整清理**：確保所有階段的輸出都被清理，避免版本不一致

## 🚨 時間基準關鍵提醒

**衛星渲染與移動計算必須使用TLE數據日期作為時間基準**

```yaml
⚠️ 極其重要 - 時間基準原則：
正確做法：
  ✅ 使用 TLE 文件日期 (如: starlink_20250816.tle → 基準時間: 2025-08-16)
  ✅ 使用 TLE Epoch 時間作為軌道計算起點
  ✅ 前端動畫基於 TLE 數據的時間戳

錯誤做法：
  ❌ 使用執行程式的當下時間 (new Date())
  ❌ 使用預計算處理的時間戳 (processing_timestamp)
  ❌ 使用前端系統的當前時間 (Date.now())

影響範圍：
  - 衛星位置計算 (可能偏差數百公里)
  - 可見性判斷 (錯誤的覆蓋評估)
  - 覆蓋率分析 (不準確的統計)
  - 換手決策 (錯誤的切換時機)

實作要點：
  - 前端必須從數據中讀取 tle_source_date 欄位
  - 動畫時間軸以 TLE 日期為起點
  - SGP4 計算使用 TLE Epoch 作為參考時間
```

### 前端實作指引
```javascript
// satellite_data 中應包含 TLE 時間信息
const satelliteData = {
  tle_source_date: "20250816",     // TLE文件日期
  tle_epoch_time: "2025-08-16T12:00:00Z", // TLE Epoch時間
  processing_time: "2025-08-21T10:30:00Z", // 僅供參考，勿用於渲染
  position_timeseries: [...]        // 基於TLE時間的軌道數據
};

// ✅ 正確：使用 TLE 數據日期
const animationStartTime = new Date(satelliteData.tle_epoch_time);

// ❌ 錯誤：使用當前時間
const wrongTime = new Date(); // 絕對不要這樣做！
```

## 🔄 六階段數據處理流程 (v4.1 即時驗證架構)

### 🚨 v5.0 統一資料格式架構重大更新

**架構革命性改進**：統一所有階段的資料格式，消除雙重存儲和冗余結構

### 🎯 v5.0 統一資料格式重大更新

**核心問題解決**：
- **發現問題**：階段1輸出雙重存儲架構 (`satellites[]` + `constellations.*`)，導致文件大小從預期1-2GB激增至6.2GB
- **根本原因**：階段2-6實際都需要 `constellations` 結構，不需要 `satellites[]` 陣列格式
- **解決方案**：統一使用 `UNIFIED_CONSTELLATION_FORMAT`，消除重複存儲

**統一格式架構**：
```json
{
  "metadata": {...},
  "constellations": {
    "starlink": {
      "metadata": {...},
      "satellites": [...]  // 統一使用列表格式
    },
    "oneweb": {
      "metadata": {...}, 
      "satellites": [...]  // 統一使用列表格式
    }
  }
}
```

**預期效果**：
- **文件大小減少**: 6.2GB → 預期1.8GB (70%減少)
- **處理速度提升**: 消除格式轉換開銷
- **維護性改善**: 單一數據格式，無新舊兼容問題

### 🚨 v4.1 即時驗證架構重大更新

**架構革命性改進**：實現每階段執行後立即驗證，防止無意義計算

- **問題識別**：之前的架構在所有階段完成後才驗證，導致失敗的中間階段會產生無意義的後續計算
- **解決方案**：每個階段執行完成後立即驗證，驗證失敗則停止所有後續處理
- **核心價值**：防止基於錯誤數據的計算資源浪費，提供快速失敗檢測
- **實現文件**：`/netstack/scripts/run_six_stages_with_validation.py` (即時驗證管道)

**即時驗證流程圖**：
```
Stage 1 執行 → [即時驗證1] → ✅ 繼續 / ❌ 停止
                    ↓
Stage 2 執行 → [即時驗證2] → ✅ 繼續 / ❌ 停止  
                    ↓
Stage 3 執行 → [即時驗證3] → ✅ 繼續 / ❌ 停止
                    ↓
             ... (以此類推)
                    ↓
🎯 關鍵優勢：任何階段失敗 = 立即停止 = 防止無意義計算
```

**實際驗證範例**：
```bash
# 即時驗證範例日誌
🔍 階段1立即驗證檢查...
✅ 階段1驗證通過
✅ 階段1品質驗證通過  
✅ 階段一完成並驗證通過: 8791 顆衛星

🎯 階段二：地理可見性篩選
❌ 階段二驗證失敗: 路徑配置錯誤
🚫 停止後續階段處理，避免基於錯誤數據的無意義計算
```

### 🎯 v3.1 數據血統追蹤更新

**重要修復**：解決數據血統追蹤問題，確保數據時間戳的準確性

- **問題**：之前系統記錄處理執行時間而非實際TLE數據時間
- **修復**：明確分離TLE數據日期與處理時間戳  
- **影響**：Stage 1 輸出現在包含完整的數據血統信息
- **標準**：符合數據治理和血統管理最佳實踐

**修復內容**：
```python
# 修復前（問題）
processing_timestamp: "2025-08-21T10:30:00Z"  # 處理執行時間

# 修復後（正確）
data_lineage: {
    "tle_dates": {"starlink": "20250820", "oneweb": "20250820"},    # 實際數據日期
    "processing_execution_time": "2025-08-21T10:30:00Z",           # 處理執行時間
    "calculation_base_time": "2025-08-20T12:00:00Z"                # SGP4計算基準時間
}
```

### 實際執行模式
**手動執行**：
```bash
# 在容器內執行完整六階段
docker exec netstack-api python /app/scripts/run_six_stages.py

# 或使用Docker建構時執行
RUN python /app/scripts/run_six_stages.py
```

### 完整數據流向圖
```
📁 本地TLE數據源：
/app/tle_data/starlink/tle/*.tle → Stage 1 TLE載入與SGP4計算
/app/tle_data/oneweb/tle/*.tle   → 完整軌道數據生成

📊 六階段記憶體處理鏈：
Stage 1 (TLE+SGP4) → Stage 2 (智能篩選) → Stage 3 (信號分析) 
     ↓                    ↓                     ↓
Stage 4 (時序預處理) → Stage 5 (數據整合) → Stage 6 (動態池規劃)

💾 統一根目錄輸出存儲 (v4.1+ 架構)：
/app/data/tle_orbital_calculation_output.json     ← Stage 1 SGP4軌道計算
/app/data/satellite_visibility_filtered_output.json ← Stage 2 地理可見性篩選結果  
/app/data/signal_event_analysis_output.json       ← Stage 3 信號品質分析
/app/data/enhanced_timeseries_output.json         ← Stage 4 時間序列預處理
/app/data/data_integration_output.json            ← Stage 5 數據整合
/app/data/enhanced_dynamic_pools_output.json      ← Stage 6 動態池規劃

🔧 架構更新: 統一使用 /app/data 根目錄，取代子目錄結構
```

### 六階段詳細處理流程

#### **Stage 1: TLE 數據載入與 SGP4 軌道計算** ✅ v5.0 統一格式版
**數據源**: 本地TLE文件 (`/app/tle_data/`)  
**處理對象**: 8,837 顆衛星 (8,186 Starlink + 651 OneWeb)  
**處理時間**: 約 2-3 分鐘  
**輸出模式**: 統一 UNIFIED_CONSTELLATION_FORMAT
**🔧 v5.0 重大改進**: 消除雙重存儲架構，統一資料格式，預期減少70%文件大小

**實際實現位置**: `/netstack/src/stages/tle_orbital_calculation_processor.py`
```python
class Stage1TLEProcessor:
    def __init__(self, tle_data_dir="/app/tle_data", output_dir="/app/data"):
        self.tle_data_dir = Path(tle_data_dir)    # 本地TLE數據源
        self.output_dir = Path(output_dir)        # 統一輸出目錄
```

**核心處理流程**:
```python
def process_tle_orbital_calculation(self):
    # 1. 掃描本地TLE文件
    scan_result = self.scan_tle_data() 
    
    # 2. 載入原始衛星數據 
    raw_satellite_data = self.load_raw_satellite_data(scan_result)
    
    # 3. 執行完整SGP4軌道計算
    tle_data = self.calculate_all_orbits(raw_satellite_data)
    
    # 4. 返回記憶體數據給Stage 2
    return tle_data
```

**技術特色**:
- **完整 SGP4 軌道計算** - 使用官方 SGP4 演算法，非簡化版本
- **時間解析度**: 30 秒間隔，計算 96 分鐘軌道窗口，生成 192 個軌道點
- **完整數據結構** - 每顆衛星包含軌道要素、時間序列、可見性分析、數據血統追蹤
- **即時驗證** - ValidationSnapshotBase 框架自動檢查數據完整性和質量

**實際輸出數據結構** (經驗證確認):
```json
{
  "satellites": [
    {
      "satellite_id": "STARLINK-1008", 
      "norad_id": 44713,
      "orbital_elements": {
        "epoch_year": 25, "epoch_days": 245.21338756,
        "inclination_deg": 53.055, "raan_deg": 312.7245,
        "eccentricity": 0.0001497, "mean_motion_revs_per_day": 15.06406813
      },
      "position_timeseries": [
        {
          "time_index": 0, "utc_time": "2025-09-06T06:45:55.529510+00:00",
          "eci_position_km": [2115.75, 4376.90, 4922.43],
          "geodetic": {"latitude_deg": 45.60, "longitude_deg": -22.44, "altitude_km": 551.12},
          "relative_to_observer": {"elevation_deg": -49.21, "azimuth_deg": 334.96, "is_visible": false}
        }
        // ... 共192個時間點
      ],
      "visibility_analysis": {
        "total_points": 192, "visible_points": 45, "visibility_percentage": 23.44,
        "visibility_windows": [...], "orbital_phase_metrics": {...}
      },
      "tle_data": {
        "source_file": "/app/tle_data/starlink/tle/starlink_20250902.tle",
        "constellation": "starlink", "data_lineage": {...}
      }
    }
  ],
  "metadata": {
    "total_satellites": 8791, "processing_timestamp": "2025-09-06T06:49:40.346292+00:00"
  }
}
```

#### **Stage 2: 地理可見性篩選** ✅ v2.0 增強驗證版
**處理對象**: 從 8,791 顆篩選至 ~3,075 顆候選  
**篩選率**: ~35.0% 保留率 (基於真實地理可見性條件)  
**處理時間**: 約 1-2 分鐘 (統一格式高效處理)
**🔧 v2.0 更新**: 修正驗證標準，基於物理條件的自然篩選，非硬性數量限制

**實際實現位置**: `/netstack/src/stages/satellite_visibility_filter_processor.py`
```python
class SatelliteVisibilityFilterProcessor:
    def process_intelligent_filtering(self, stage1_data):
        # 接收Stage 1的記憶體數據
        # 執行自然地理可見性篩選 - 無數量限制，純粹基於條件篩選
        # 返回篩選後的候選衛星給Stage 3
```

**自然篩選管線** (v2.0):
1. **星座分離篩選** (8,791 → 8,791) - 分離 Starlink 和 OneWeb
2. **地理可見性篩選** (8,791 → ~3,075) - 基於 NTPU 觀測點和物理條件
3. **物理條件驗證** (~3,075 → ~3,075) - 驗證仰角門檻和可見時間

**實際篩選結果** (v2.0 基於物理條件):
- **篩選條件**:
  - Starlink: 仰角 ≥5°, 可見時間 ≥1.0分鐘
  - OneWeb: 仰角 ≥10°, 可見時間 ≥0.5分鐘
- **實際結果**:
  - Starlink: ~2,852 顆 (基於5°門檻自然篩選)
  - OneWeb: ~223 顆 (基於10°門檻自然篩選)
  - 總計: ~3,075 顆衛星 (35.0% 保留率)

**🎯 重要說明**: 數量由物理條件決定，不是硬性限制。不同TLE數據日期和觀測條件會產生不同結果。

#### **Stage 3: 信號品質分析**
**處理對象**: 1,113 顆候選衛星的信號分析  
**處理時間**: 約 1-2 分鐘  
**核心技術**: 3GPP NTN 標準 A4/A5/D2 事件實現

**3GPP 事件分析**:
- **Event A4**: 鄰近衛星信號優於門檻 (RSRP > -100 dBm)
- **Event A5**: 服務衛星劣化且鄰近衛星良好
- **Event D2**: 基於距離的換手觸發

**RSRP 計算實現**:
```python
def calculate_rsrp_simple(sat):
    # 自由空間路徑損耗 (Ku頻段 12 GHz)
    fspl_db = 20 * math.log10(sat.distance_km) + 20 * math.log10(12.0) + 32.45
    elevation_gain = min(sat.elevation_deg / 90.0, 1.0) * 15  # 最大15dB增益
    tx_power = 43.0  # 43dBm發射功率
    return tx_power - fspl_db + elevation_gain
```

#### **Stage 4: 時間序列預處理**
**處理對象**: 1,113 顆衛星的時間序列最佳化  
**輸入**: 階段三信號品質數據 (~200MB)  
**輸出**: 前端時間序列數據 (~60-75MB)

**前端動畫需求**:
- **時間軸控制**: 支援 1x-60x 倍速播放
- **衛星軌跡**: 平滑的軌道動畫路徑
- **信號變化**: 即時信號強度視覺化
- **換手事件**: 動態換手決策展示

**最佳化策略**:
- **檔案大小**: 壓縮至前端可接受範圍
- **載入速度**: 支援快速初始化
- **動畫流暢**: 60 FPS 渲染需求
- **記憶體效率**: 瀏覽器記憶體友善

#### **Stage 5: 數據整合處理** ✅ 已修復
**處理對象**: 跨系統數據格式統一與分層增強  
**處理時間**: 約 30-60 秒  

**整合功能**:
- **分層仰角濾波**: 5°/10°/15° 三層仰角門檻數據生成
  - elevation_5deg: 399顆衛星 (100%保留)
  - elevation_10deg: 351顆衛星 (87.9%保留) 
  - elevation_15deg: 277顆衛星 (69.4%保留)
- **PostgreSQL整合**: 衛星元數據、信號統計、換手事件
- **格式標準化**: 統一 `position_timeseries` 數據結構
- **換手場景生成**: A4/A5/D2 事件時間軸

#### **Stage 6: 動態池規劃 (時間序列保留版)**
**處理對象**: 從 1,113 顆候選中選出 156 顆衛星池 (120 Starlink + 36 OneWeb)  
**處理時間**: 約 0.5 秒 (快速選擇 + 時間序列數據保留)

**核心功能**:
- **時間序列保留**: 確保每顆衛星包含完整的 192 點軌跡數據
- **數據完整性**: 30 秒間隔的連續 SGP4 計算結果
- **前端支持**: 解決軌跡跳躍問題，支持平滑 3D 動畫

**關鍵實現**:
```python
# 實際實現位置: /netstack/src/stages/enhanced_dynamic_pool_planner.py
@dataclass 
class EnhancedSatelliteCandidate:
    position_timeseries: List[Dict[str, Any]] = None  # 🎯 完整時間序列

def convert_to_enhanced_candidates(satellite_data):
    # 保留完整的時間序列數據
    position_timeseries = sat_data.get('position_timeseries', [])
    # 確保 192 點×30 秒間隔軌跡數據完整性
```

## 🗃️ 數據存儲架構

### 本地TLE數據源
**數據來源**: 預下載的歷史TLE數據  
**更新方式**: 手動更新本地TLE文件  
**星座覆蓋**:

```
📁 /app/tle_data/ (容器內路徑)
├── starlink/
│   ├── tle/starlink_20250805.tle    # 歷史TLE數據 (8,128顆)
│   └── json/starlink.json           # 結構化數據
└── oneweb/
    ├── tle/oneweb_20250805.tle      # 歷史TLE數據 (651顆)  
    └── json/oneweb.json
```

### 六階段輸出數據結構
```
📁 /app/data/ (統一數據輸出目錄)
├── tle_calculation_outputs/         # Stage 1: SGP4軌道計算結果
│   └── tle_orbital_calculation_output.json  # 完整軌道數據 (可達2.3GB)
├── intelligent_filtering_outputs/   # Stage 2: 1,113顆篩選候選
│   └── satellite_visibility_filtered_output.json
├── signal_analysis_outputs/         # Stage 3: 3GPP事件分析
│   └── signal_event_analysis_output.json  
├── timeseries_preprocessing_outputs/ # Stage 4: 前端動畫數據 (~60MB)
│   ├── starlink_enhanced.json      # Starlink時序數據
│   └── oneweb_enhanced.json         # OneWeb時序數據
├── data_integration_outputs/        # Stage 5: PostgreSQL整合狀態
│   └── integrated_data_output.json
└── enhanced_dynamic_pools_output.json  # Stage 6: 最終動態池
```

### Docker Volume 映射
```yaml
# docker-compose.yml 中的實際映射
volumes:
  - /home/sat/ntn-stack/data:/app/data              # 主要輸出目錄
  - /home/sat/ntn-stack/netstack/tle_data:/app/tle_data  # TLE數據源
```

### PostgreSQL 數據庫整合
```sql
-- RL 研究數據庫 (172.20.0.51:5432/rl_research)
satellite_orbital_cache:    -- 軌道計算緩存 (~3MB/週)
├── satellite_id           -- 衛星識別碼
├── timestamp              -- 時間戳 (30秒間隔)  
├── latitude, longitude    -- 地理座標
├── altitude, elevation    -- 高度和仰角
└── distance_km           -- 3D距離

satellite_tle_data:        -- TLE原始數據存儲
├── satellite_id          -- 衛星識別碼
├── constellation         -- 星座名稱
├── tle_line1, tle_line2  -- TLE數據行
└── epoch_time           -- 軌道元素時間
```

## ⚡ 性能指標與優化

### 預期性能提升
- **API 響應時間**: 從 500-2000ms → 50-100ms
- **衛星數據量**: 從 6 顆模擬 → 6-8 顆真實可見衛星 (符合 3GPP NTN 標準)
- **換手候選**: 3-5 顆 (符合真實場景)
- **時間範圍**: 支援 6 小時完整歷史數據
- **動畫流暢度**: 支援 1x-60x 倍速播放

### 記憶體傳遞優勢
- **避免大文件I/O**: Stage間直接記憶體數據流，無需寫入2.3GB中間文件
- **處理速度提升**: 六階段總處理時間從10-15分鐘優化至5-8分鐘
- **儲存空間節省**: 僅在需要時才生成文件備份，節省磁碟空間

### 資源使用優化  
- **記憶體峰值**: ~4-6GB (處理8,779顆衛星時)
- **CPU 使用**: Stage 1 最高 (~80%)，其他階段 <30%
- **磁碟空間**: 完整輸出約200-300MB (不含大型備份文件)
- **處理時間**: 完整六階段 5-8分鐘

### 性能基準
```
🚀 數據載入時間: < 30 秒
⚡ API 查詢響應: < 100ms
🎨 前端組件載入: < 2 秒
🎬 動畫流暢度: 60 FPS
💾 記憶體使用: < 200MB
🔧 CPU 使用率: < 50%
```

## 🔧 執行和管理

### 手動執行六階段

#### ⭐ 推薦：即時驗證模式 (v4.1)
```bash
# 方法 1: 容器內執行即時驗證版本 (推薦)
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py

# 方法 2: 進入容器執行
docker exec -it netstack-api bash
python /app/scripts/run_six_stages_with_validation.py

# 方法 3: 建構時執行 (在Dockerfile中)  
RUN python /app/scripts/run_six_stages_with_validation.py
```

#### 傳統模式：完整處理後驗證
```bash
# 傳統方式：執行所有階段後才驗證
docker exec netstack-api python /app/scripts/run_six_stages.py

# 後續驗證 (已整合到主程式中，無需額外步驟)
# 驗證功能已內建於 run_six_stages_with_validation.py
```

#### 執行模式比較
| 特性 | 即時驗證模式 | 傳統模式 |
|------|-------------|----------|
| **驗證時機** | 每階段執行後立即驗證 | 所有階段完成後驗證 |
| **失敗處理** | 立即停止，節省資源 | 繼續執行，可能浪費計算 |
| **錯誤檢測** | 快速檢測 (<5分鐘) | 延遲檢測 (20-30分鐘) |
| **資源效率** | 高效，避免無意義計算 | 低效，可能重複計算 |
| **推薦度** | ✅ **強烈推薦** | ⚠️ 僅供相容性 |

### 輸出驗證
```bash
# 檢查輸出檔案完整性
docker exec netstack-api python /app/scripts/run_six_stages.py --verify-only

# 查看處理統計
ls -lah /home/sat/ntn-stack/data/*/
```

### 清理策略
```bash
# 清理所有輸出 (重新開始)
rm -rf /home/sat/ntn-stack/data/*/

# 清理大型備份檔案但保留小文件  
find /home/sat/ntn-stack/data/ -name "*.json" -size +100M -delete
```

## 🔍 數據品質保證

### TLE 數據格式驗證
```
STARLINK-1008           
1 44714U 19074B   25217.02554568  .00001428  00000+0  11473-3 0  9994
2 44714  53.0544  88.2424 0001286  82.9322 277.1813 15.06399309315962
```

**驗證項目**:
- **格式完整性**: TLE 標準 69 字元行格式
- **校驗和驗證**: modulo-10 校驗和正確性
- **數值範圍檢查**: 軌道參數合理性驗證
- **時間一致性**: epoch 時間與當前時間差異檢查

### SGP4 計算精度驗證
- **位置精度**: 與官方 SGP4 參考實現比較誤差 < 1km
- **速度精度**: 軌道速度計算誤差 < 0.1 m/s
- **時間精度**: 軌道預測時間精度 < 1 秒

## 🚨 異常處理與容錯

### 常見問題排解
1. **TLE文件缺失**: 檢查 `/app/tle_data/` 目錄結構
2. **記憶體不足**: 調整Docker記憶體限制或使用sample_mode
3. **磁碟空間不足**: 清理舊輸出文件或調整保留策略
4. **處理中斷**: 從中斷的Stage繼續，利用已有的中間結果

### 數據完整性驗證
```python
# 每個Stage都包含完整性檢查
def verify_stage_output(stage_data):
    if not stage_data or 'metadata' not in stage_data:
        raise ValueError("Stage數據不完整")
    
    total_satellites = stage_data['metadata']['total_satellites'] 
    if total_satellites == 0:
        raise ValueError("未處理任何衛星數據")
```

### 容錯設計原則
1. **graceful degradation** - 部分失敗不影響整體系統
2. **automatic retry** - 自動重試機制 (指數退避)
3. **fallback mechanism** - 失敗時使用緩存數據
4. **health monitoring** - 持續健康狀態監控

## 🔮 未來擴展規劃

### 架構優化方向
1. **分散式處理**: 支援多容器並行處理不同星座  
2. **增量更新**: 智能檢測TLE變更，只重新計算變更部分
3. **快取優化**: 智能快取中間結果，避免重複計算
4. **自動化流程**: 可選的Cron調度支援，但保持手動優先

### 研究價值提升  
1. **多時間點支援**: 支援不同歷史時間點的軌道數據
2. **精度比較**: 與官方軌道數據進行精度驗證
3. **統計分析**: 大量歷史數據支援統計研究
4. **算法驗證**: 真實場景下的 handover 算法測試

## 🎯 技術規格總結

### 核心技術參數
- **數據來源**: 本地歷史TLE文件 (CelesTrak原始數據)
- **處理模式**: 手動/按需執行，記憶體優先傳遞  
- **時間解析度**: 30 秒間隔
- **觀測位置**: 台灣 NTPU (24.94°N, 121.37°E)
- **支援星座**: Starlink (8,128顆) + OneWeb (651顆)
- **數據存儲**: 統一於 `/app/data`，PostgreSQL 整合

### 數據處理統計
```
原始數據:     8,779 顆衛星 TLE (本地文件)
Stage 1:      完整 SGP4 軌道計算 (記憶體傳遞)
Stage 2:      智能篩選至 1,113 顆候選 (87.3% 減少)
Stage 3:      3GPP A4/A5/D2 事件分析
Stage 4:      前端動畫數據最佳化 (60-75MB)
Stage 5:      跨系統格式統一
Stage 6:      動態池規劃 (最終衛星池)
```

---

## 🎯 v4.1 即時驗證架構總結

### 關鍵改進
- **革命性架構升級**：從「處理後驗證」→「即時驗證」  
- **資源效率提升**：防止基於失敗數據的無意義計算
- **快速錯誤檢測**：階段失敗立即停止，節省20-30分鐘無效處理時間
- **精確失敗定位**：準確識別具體失敗階段，便於調試
- **Docker建構整合**：新的建構腳本支援即時驗證模式

### 實現檔案
- **主管道**：`/netstack/scripts/run_six_stages_with_validation.py`
- **建構腳本**：`/netstack/scripts/final_build_validation.py` (統一驗證)
- **驗證框架**：`ValidationSnapshotBase` 統一驗證系統

**這個本地數據驅動架構 + 即時驗證系統確保了學術研究的數據準確性、可重現性和處理效率，完全基於真實的歷史TLE數據和完整的SGP4計算！**

*最後更新：2025-09-06 | 數據處理流程版本 4.1.0 (即時驗證架構版)*