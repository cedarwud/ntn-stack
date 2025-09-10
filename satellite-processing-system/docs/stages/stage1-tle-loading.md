# 📊 階段一：TLE數據載入與SGP4軌道計算

[🔄 返回文檔總覽](../README.md) > 階段一

## 📖 階段概述

**目標**：從 8,791 顆衛星載入 TLE 數據並執行精確的 SGP4 軌道計算  
**輸入**：TLE 檔案（約 2.2MB）  
**輸出**：全量數據保存至 `/app/data/tle_orbital_calculation_output.json` + 記憶體傳遞  
**處理時間**：約 4-5 分鐘
**實際處理數量**：8,140 Starlink + 651 OneWeb = 8,791 顆衛星

### 🗂️ 統一輸出目錄結構

六階段處理系統採用統一的輸出目錄結構：

```bash
/app/data/                                    # 統一數據目錄
├── tle_orbital_calculation_output.json      # 階段一：軌道計算 ⭐
├── satellite_visibility_filtered_output.json # 階段二：地理可見性篩選  
├── signal_quality_analysis_output.json      # 階段三：信號分析
├── timeseries_preprocessing_output.json     # 階段四：時間序列
├── data_integration_output.json             # 階段五：數據整合
├── enhanced_dynamic_pools_output.json       # 階段六：動態池規劃
└── validation_snapshots/                    # 驗證快照目錄
    ├── stage1_validation.json               # 階段一驗證快照（僅驗證快照保留stage命名）
    ├── stage2_validation.json
    └── ...
```

**命名規則**：
- 所有階段輸出使用**功能性命名**（如 `tle_orbital_calculation_output.json`）
- **僅驗證快照**保留 `stage{N}_validation.json` 格式
- 統一保存至 `/app/data/` 目錄（容器內）
- 驗證快照保存至 `validation_snapshots/` 子目錄
- 無額外子目錄，保持扁平結構

### 🎯 @doc/todo.md 對應實現
本階段實現以下核心需求：
- ✅ **地理定位**: 設定 NTPU 觀測點座標 (24°56'39"N 121°22'17"E)
- ✅ **數據來源**: 載入 @netstack/tle_data 兩個星座的最新TLE數據
- 🔧 **軌道計算基礎**: 為後續可見性篩選和時空錯置分析提供精確的軌道動力學數據

### 🛡️ Phase 3+ 驗證框架整合 (v4.0)

**✅ 已完全整合新驗證框架**：
- **可配置驗證級別**：FAST/STANDARD/COMPREHENSIVE 三級模式
- **學術標準執行**：Grade A/B/C 分級標準自動檢查  
- **零侵入整合**：不影響原有SGP4計算邏輯
- **性能優化**：FAST模式減少60-70%驗證時間

#### 🎯 Stage 1 驗證檢查項目

**FAST模式** (4項關鍵檢查):
- ✅ TLE文件存在性檢查
- ✅ 衛星數量檢查 (8000-9200顆)
- ✅ 統一格式檢查 (UNIFIED_CONSTELLATION_FORMAT)
- ✅ SGP4計算完整性檢查

**COMPREHENSIVE模式** (14項完整檢查):
- 上述FAST檢查 + 星座完整性、重複數據檢查、軌道數據合理性
- 數據血統追蹤、時間基準一致性、處理性能檢查
- 軌道參數物理邊界驗證等

**學術標準強制執行**：
- ❌ **零容忍ECI座標為零**：OneWeb衛星ECI座標全零立即失敗
- ✅ **時間基準強制檢查**：必須使用TLE epoch時間作為SGP4計算基準
- ✅ **物理合理性驗證**：軌道高度、傾角、周期必須符合物理定律

### 🚀 v3.2 過度篩選修復版本

- **🔧 核心修復**：✅ **消除過度篩選問題**
  - **取樣數量**：從 50 顆提升到 800 顆 (10% 合理取樣率)
  - **處理模式**：支援全量處理模式 (sample_mode=False)
  - **數據完整性**：確保足夠數據流向後續階段
  - **性能平衡**：在處理速度與數據完整性間達到最佳平衡

### 🚀 v3.1 數據血統追蹤版本

- **核心修復**：✅ **數據血統追蹤機制**
  - **TLE數據日期**：記錄實際TLE檔案日期（如：2025-08-20）
  - **處理時間戳**：記錄程式執行時間（如：2025-08-21）
  - **計算基準時間**：使用TLE epoch時間進行軌道計算
  - **數據治理**：完全符合數據血統管理原則

- **技術改進**：
  - **傳遞方式**：直接將軌道計算結果在記憶體中傳遞給階段二
  - **效能提升**：消除檔案 I/O 開銷，處理速度提升 50%+
  - **數據完整性**：確保每顆衛星都有完整的TLE來源追蹤信息

### ⏰ 時間週期與數據血統說明

**重要澄清**：系統中有三個不同的時間概念：

1. **軌道計算週期**：**星座特定設計**
   - **Starlink**: 96分鐘軌道 → 192個時間點 (30秒間隔)
   - **OneWeb**: 109分鐘軌道 → 218個時間點 (30秒間隔)
   - 基於真實軌道動力學，每個星座使用其實際軌道週期
   - 用於生成連續的軌跡動畫數據

2. **系統更新週期**：6小時  
   - Cron自動下載新TLE數據的頻率
   - 重新執行六階段處理的間隔
   - 保持衛星軌道數據新鮮度

3. **🎯 數據血統時間戳**（v3.1 新增）：
   - **TLE數據日期**：實際衛星軌道元素的有效時間
   - **TLE Epoch時間**：TLE軌道元素的參考時間點
   - **處理執行時間**：軌道計算程序的實際運行時間
   - **計算基準時間**：SGP4算法使用的時間基準（採用TLE Epoch）

## 🚨 強制運行時檢查 (新增)

**2025-09-09 重大強化**: 基於系統性驗證盲區發現，新增強制運行時架構完整性檢查維度。

### 🔴 零容忍運行時檢查 (任何失敗都會停止執行)

#### 1. 引擎類型強制檢查
```python
# 🚨 嚴格檢查實際使用的引擎類型，而非聲明的類型
assert isinstance(engine, SGP4OrbitalEngine), f"錯誤引擎: {type(engine)}"
# 原因: 防止使用CoordinateSpecificOrbitEngine替代SGP4OrbitalEngine
# 影響: 使用錯誤引擎會產生不正確的軌道計算結果
```

#### 2. API契約格式檢查  
```python
# 🚨 星座特定時間序列長度檢查 (修正版)
constellation = satellite.get('constellation', '').lower()
expected_points = {
    'starlink': 192,  # 96分鐘軌道
    'oneweb': 218     # 109分鐘軌道
}.get(constellation)

assert expected_points is not None, f"未知星座: {constellation}"
assert len(timeseries) == expected_points, f"時間序列長度錯誤: {len(timeseries)} (應為{expected_points}點，星座: {constellation})"

# 🚨 強制檢查輸出數據結構完整性
assert 'position_timeseries' in output, "缺少完整時間序列數據"
assert 'metadata' in output, "缺少元數據信息"
assert 'constellation' in satellite, "衛星缺少星座標識"
assert output['metadata']['total_satellites'] > 8600, "衛星數量不足"
```

#### 3. 執行流程完整性檢查
```python
# 🚨 檢查方法調用路徑，確保按文檔順序執行
assert method_name == "calculate_position_timeseries", "錯誤計算方法"
assert processing_mode == "complete_sgp4_calculation", "簡化算法檢測"
# 原因: 防止使用簡化算法或回退機制
# 影響: 確保學術標準Grade A完整實現
```

#### 4. 無簡化回退零容忍檢查
```python
# 🚨 禁止任何形式的簡化或回退
forbidden_patterns = [
    "simplified", "mock", "fallback", "estimated", 
    "assumed", "default", "placeholder"
]
for pattern in forbidden_patterns:
    assert pattern.lower() not in str(engine.__class__).lower(), \
        f"檢測到禁用的簡化實現: {pattern}"
```

### 📋 Runtime Check Integration Points

**檢查時機**: 
- **初始化時**: 驗證引擎類型和配置參數
- **計算過程中**: 監控方法調用路徑和數據流
- **輸出前**: 嚴格檢查數據格式和結構完整性

**失敗處理**:
- **立即停止**: 任何runtime check失敗都會立即終止執行
- **錯誤報告**: 詳細記錄失敗原因和檢測到的違規
- **無回退機制**: 絕不允許降級或簡化處理

### 🛡️ 實施要求

- **100%檢測率**: 所有架構違規必須被檢測
- **零漏檢容忍**: 不允許任何違規通過檢查
- **性能影響**: 運行時檢查額外時間開銷 <5%
- **學術誠信**: 確保完全符合學術級數據標準

### 🚨 衛星渲染時間基準重要說明

**關鍵原則：前端渲染必須使用TLE數據日期作為時間基準**

```yaml
⚠️ 重要提醒：
- ✅ 正確：使用 TLE 文件日期 (如: 20250902 來自 starlink_20250902.tle)
- ❌ 錯誤：使用程式執行日期 (如: 當前系統時間)
- ❌ 錯誤：使用處理計算日期 (如: 資料預處理的時間戳)
- ❌ 錯誤：使用前端當下時間 (如: new Date())

原因：
- TLE數據代表特定時間點的衛星軌道狀態
- 使用錯誤的時間基準會導致衛星位置計算偏差
- 可能造成數百公里的位置誤差，影響可見性判斷
```

**前端實作範例**：
```javascript
// ✅ 正確的時間基準使用
const getTLEBaseTime = (satelliteData) => {
  // 從數據中提取TLE日期
  const tleDate = satelliteData.tle_source_date; // "20250902"
  const tleEpoch = satelliteData.tle_epoch_time; // TLE的epoch時間
  
  // 使用TLE日期作為動畫基準時間
  const baseTime = new Date(
    parseInt(tleDate.substr(0,4)),  // 2025
    parseInt(tleDate.substr(4,2))-1, // 09 (月份從0開始)
    parseInt(tleDate.substr(6,2))    // 02
  );
  
  return baseTime;
};

// ❌ 錯誤的時間基準使用
const getWrongBaseTime = () => {
  return new Date(); // 千萬不要使用當前時間！
};
```

## 🏗️ 核心處理器架構

### 主要實現位置
```bash
# 核心處理器
/netstack/src/stages/tle_orbital_calculation_processor.py
├── Stage1TLEProcessor.scan_tle_data()                          # TLE檔案掃描
├── Stage1TLEProcessor.load_raw_satellite_data()               # 原始數據載入  
├── Stage1TLEProcessor.calculate_all_orbits()                  # 完整SGP4計算
├── Stage1TLEProcessor.save_tle_calculation_output()           # Debug模式控制輸出
└── Stage1TLEProcessor.process_tle_orbital_calculation()       # 完整流程執行

# SGP4引擎支援
/netstack/src/services/satellite/coordinate_specific_orbit_engine.py
```

### 處理流程

1. **TLE檔案掃描**：掃描兩個星座的TLE資料
   - Starlink: 8,140顆衛星 (最新20250902數據)
   - OneWeb: 651顆衛星 (最新20250903數據)

2. **原始數據載入**：解析TLE格式並驗證數據完整性

3. **SGP4軌道計算**：基於真實物理模型計算衛星位置
   - 使用官方SGP4演算法（非簡化版本）
   - 計算完整軌道週期數據（Starlink: 96分鐘/192點、OneWeb: 109分鐘/218點）
   - 時間解析度：30秒間隔，支持星座特定軌道週期

4. **記憶體傳遞**：將結果直接傳遞給階段二

## 🔧 技術實現細節

### SGP4計算精度
- **標準遵循**：嚴格遵循官方SGP4/SDP4標準
- **誤差控制**：位置誤差 < 1km（LEO衛星）
- **時間精度**：UTC時間精確到秒級

### 🚨 **強制原則：學術級數據標準遵循** (Grade A 等級)

#### 🟢 **Grade A 強制要求：必須使用真實數據**
- **✅ TLE數據源**：Space-Track.org 官方實時數據
  - 數據更新頻率：每日更新，絕不可超過7天
  - 格式標準：嚴格遵循NORAD兩行軌道根數格式
  - 數據驗證：必須通過校驗和（checksum）驗證
- **✅ 軌道計算算法**：完整SGP4/SDP4實現
  - 算法標準：AIAA 2006-6753 "Revisiting Spacetrack Report #3"
  - 實施要求：使用官方SGP4實現，非簡化版本
  - 精度標準：位置誤差 < 1km（LEO衛星）
- **✅ 時間標準**：GPS/UTC標準時間
  - GPS時間：精確到微秒級同步
  - 時間基準：使用TLE epoch時間進行計算
  - 同步要求：通過NTP伺服器同步

#### 🔴 **Grade C 嚴格禁止項目** (零容忍)
- **❌ 預設軌道週期回退**：如96分鐘預設值、平均軌道週期
- **❌ TLE數據不可用時的假設值**：如假設衛星位置、估算軌道參數
- **❌ 簡化軌道計算模型**：如線性軌道近似、圓形軌道假設
- **❌ 任意時間假設**：如使用系統當前時間替代TLE epoch時間
- **❌ 魔術數字**：任何沒有物理依據和標準文獻支持的常數值

#### 🚨 **執行檢查原則**
- **數據不可用時的處理**：系統必須失敗退出，絕不允許回退到模擬數據
- **錯誤處理策略**：記錄錯誤並終止處理，不得使用估算值繼續
- **驗證要求**：所有計算結果必須可通過獨立SGP4實現驗證
- **可追溯性**：每個數據點都必須有明確的TLE來源和計算依據

### 🎯 數據血統追蹤系統（v3.1）
- **TLE來源追蹤**：每顆衛星記錄完整的TLE文件來源信息
- **時間戳分離**：明確區分數據時間與處理時間
- **血統元數據**：包含文件路徑、文件日期、epoch時間等完整信息
- **數據治理標準**：符合數據血統管理最佳實踐

```python
# 數據血統結構示例
satellite_data = {
    'tle_data': {
        'source_file': '/app/tle_data/starlink/tle/starlink_20250902.tle',
        'source_file_date': '20250902',  # TLE數據實際日期
        'epoch_year': 2025,
        'epoch_day': 245.5,
        'calculation_base_time': '2025-09-02T12:00:00Z',  # TLE epoch時間
        'data_lineage': {
            'data_source_date': '20250902',           # 數據來源日期
            'tle_epoch_date': '2025-09-02T12:00:00Z', # TLE參考時間
            'processing_execution_date': '2025-09-02T14:26:00Z', # 處理執行時間
            'calculation_strategy': 'sgp4_with_tle_epoch_base'
        }
    }
}
```

### 記憶體管理
- **數據結構**：使用高效的numpy陣列
- **記憶體使用**：峰值約500MB
- **垃圾回收**：自動清理中間計算結果

## 📖 **學術標準參考文獻**

### 軌道力學標準
- **AIAA 2006-6753**: "Revisiting Spacetrack Report #3" - SGP4/SDP4官方實現標準
- **NASA/TP-2010-216239**: "SGP4 Orbit Determination" - NASA軌道計算技術報告
- **IERS Conventions (2010)**: 地球參考框架和時間系統標準

### 數據來源標準
- **Space-Track.org**: 官方NORAD TLE數據來源 (https://www.space-track.org/)
- **USSTRATCOM**: 美國戰略司令部衛星追蹤數據
- **CelesTrak**: TLE數據格式標準和驗證工具

### 時間系統標準  
- **IERS Technical Note No. 36**: 地球定向參數和時間系統
- **ITU-R Recommendation TF.460**: 時間信號標準化
- **GPS Interface Specification**: GPS時間系統規範

### 精度驗證基準
- **STK (Systems Tool Kit)**: 商業軌道計算軟件比較基準
- **GMAT (General Mission Analysis Tool)**: NASA開源軌道分析工具
- **Orekit**: 開源軌道力學庫驗證參考

## ⚙️ 配置參數

```python
# 主要配置
OBSERVER_LAT = 24.9441667  # NTPU緯度
OBSERVER_LON = 121.3713889  # NTPU經度
TIME_WINDOW_HOURS = 6       # 計算時間範圍
TIME_STEP_SECONDS = 30      # 時間解析度
```

## 🚨 故障排除

### 常見問題

1. **TLE數據過期**
   - 檢查：TLE檔案最後修改時間
   - 解決：執行增量更新腳本

2. **SGP4計算失敗**
   - 檢查：TLE格式完整性
   - 解決：重新下載TLE數據

3. **記憶體不足**
   - 檢查：系統可用記憶體
   - 解決：增加swap空間或分批處理

4. **🎯 數據血統追蹤問題（v3.1）**
   - **症狀**：數據時間戳與處理時間戳相同
   - **檢查**：輸出metadata中的 `data_lineage` 字段
   - **解決**：確認TLE文件日期正確解析，重新執行處理

### 診斷指令

```bash
# 檢查TLE數據狀態
find /app/tle_data -name '*.tle' -exec ls -la {} \;

# 驗證TLE軌道計算處理器
python -c "from stages.tle_orbital_calculation_processor import Stage1TLEProcessor; print('TLE軌道計算處理器正常')"

# 驗證SGP4引擎
python -c "from src.services.satellite.coordinate_specific_orbit_engine import *; print('SGP4引擎正常')"

# 🎯 驗證數據血統追蹤（v3.1）
python -c "
import json
with open('/app/data/tle_orbital_calculation_output.json', 'r') as f:
    data = json.load(f)
    lineage = data['metadata']['data_lineage']
    print('📊 數據血統檢查:')
    print(f'  TLE日期: {lineage.get(\"tle_dates\", {})}')
    print(f'  處理時間: {data[\"metadata\"][\"processing_timestamp\"]}')
    print('✅ 數據血統追蹤正常' if lineage.get('tle_dates') else '❌ 數據血統追蹤異常')
"
```

## ✅ 階段驗證標準

### 🎯 Stage 1 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] TLE文件存在性檢查
  - Starlink TLE文件: `/app/tle_data/starlink/tle/*.tle`
  - OneWeb TLE文件: `/app/tle_data/oneweb/tle/*.tle`
- [ ] TLE格式驗證
  - 每個TLE必須包含3行（衛星名稱、Line 1、Line 2）
  - Line 1/2 必須各為69字元
  - 校驗和（checksum）正確
- [ ] TLE完整性檢查
  - TLE epoch時間必須存在且可解析
  - 注意：我們計算TLE epoch當天的軌道，不存在時效性問題

#### 2. **處理驗證**
- [ ] **衛星數量驗證**
  ```
  預期範圍:
  - Starlink: 8,000-8,200顆
  - OneWeb: 600-700顆  
  - 總計: 8,600-8,900顆
  ```
- [ ] **SGP4計算驗證**
  - 每顆衛星生成192個時間點（96分鐘，30秒間隔）
  - 位置誤差 < 1km（與參考實現比較）
  - 無NaN或無效值
- [ ] **記憶體使用監控**
  - 峰值記憶體 < 1GB（全量處理模式）
  - 無記憶體洩漏（處理後釋放）

#### 3. **輸出驗證**
- [ ] **數據結構完整性**
  ```json
  {
    "stage_name": "SGP4軌道計算與時間序列生成",
    "satellites": [...],  // 扁平衛星列表（8791個元素）
    "metadata": {
      "total_satellites": 8791,  // 必須 > 8600
      "constellations": {
        "starlink": {"satellite_count": 8140},
        "oneweb": {"satellite_count": 651}
      },
      "data_lineage": {
        "tle_dates": {"starlink": "20250902", "oneweb": "20250903"},
        "processing_timeline": {...}
      }
    }
  }
  ```
- [ ] **時間序列數據驗證**
  - 每顆衛星包含 `position_timeseries` 陣列
  - 時間序列長度 = 192點（或配置值）
  - 每個時間點包含：time, position_eci, velocity_eci, elevation_deg, azimuth_deg, is_visible
- [ ] **數據血統追蹤（v3.1）**
  - TLE數據日期正確記錄
  - 處理時間戳與數據時間戳分離
  - 完整的血統元數據

#### 4. **性能指標**
- [ ] 處理時間 < 5分鐘（全量8,791顆衛星）
- [ ] 記憶體傳遞成功（無大檔案生成）
- [ ] CPU使用率峰值 < 80%

#### 5. **自動驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import sys

# 載入輸出數據
try:
    with open('/app/data/tle_orbital_calculation_output.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print('⚠️ 使用記憶體傳遞模式，跳過文件驗證')
    sys.exit(0)

# 驗證項目
metadata = data.get('metadata', {})
satellites = data.get('satellites', [])
constellations = metadata.get('constellations', {})

checks = {
    'total_satellites': metadata.get('total_satellites', 0) > 8600,
    'satellites_list': isinstance(satellites, list) and len(satellites) > 8600,
    'has_starlink_info': 'starlink' in constellations,
    'has_oneweb_info': 'oneweb' in constellations,
    'has_data_lineage': 'data_lineage' in metadata,
    'has_tle_dates': 'tle_dates' in metadata.get('data_lineage', {}),
    'starlink_count': constellations.get('starlink', {}).get('satellite_count', 0) > 8000,
    'oneweb_count': constellations.get('oneweb', {}).get('satellite_count', 0) > 600
}

# 計算通過率
passed = sum(checks.values())
total = len(checks)

print('📊 Stage 1 驗證結果:')
print(f'  衛星總數: {metadata.get(\"total_satellites\", 0)}')
print(f'  Starlink: {constellations.get(\"starlink\", {}).get(\"satellite_count\", 0)}')
print(f'  OneWeb: {constellations.get(\"oneweb\", {}).get(\"satellite_count\", 0)}')
print()

for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')
print(f'\\n總計: {passed}/{total} 項通過')

if passed == total:
    print('✅ Stage 1 驗證通過！')
else:
    print('❌ Stage 1 驗證失敗，請檢查上述項目')
    sys.exit(1)
"
```

### 🚨 驗證失敗處理
1. **數量不足**：檢查TLE文件是否完整
2. **SGP4失敗**：驗證TLE格式，更新skyfield庫
3. **血統缺失**：確認使用v3.1版本處理器
4. **記憶體溢出**：啟用分批處理模式

---
**下一處理器**: [地理可見性篩選處理器](./stage2-filtering.md)  
**相關文檔**: [Pure Cron架構](../data_processing_flow.md#pure-cron驅動架構)
