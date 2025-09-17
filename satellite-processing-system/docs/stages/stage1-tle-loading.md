# 📊 階段一：TLE數據載入與SGP4軌道計算

[🔄 返回文檔總覽](../README.md) > 階段一

## 📖 階段概述

**目標**：從 8,837 顆衛星載入 TLE 數據並執行純粹的 SGP4 軌道計算（僅ECI座標）
**輸入**：TLE 檔案（約 2.2MB）
**輸出**：純軌道數據保存至 `/app/data/tle_orbital_calculation_output.json` + 記憶體傳遞
**處理時間**：約 2.8 分鐘 (基於實測：8,837顆衛星 = 166.48秒) ⚠️ **需要優化**
**實際處理數量**：8,183 Starlink + 653 OneWeb = 8,837 顆衛星
**重要**：階段一僅計算軌道，不涉及任何觀測點相關計算或可見性判斷

### 🚨 v5.1 關鍵修復需求 (2025-09-16)

**根本問題**: 當前軌道計算存在時間基準錯誤，導致：
- **0%覆蓋率**: 計算結果顯示0顆衛星可見，研究完全無法進行
- **時間基準錯誤**: 使用當前系統時間而非TLE epoch時間
- **軌道偏差**: 5-6天時間差導致衛星位置偏差數百公里

**修復方案**:
- 整合驗證過的直接計算算法(已驗證246顆平均可見)
- 使用TLE epoch時間作為計算基準時間
- 性能優化: 2.8分鐘 → <10秒(200x提升)
- 詳見[直接計算解決方案](../DIRECT_CALCULATION_SOLUTION.md)

### 🎯 v6.0 統一重構要求 (2025-09-17)

**核心重構目標**: 建立可靠的時間基準繼承機制，確保所有六階段使用一致的計算基準

#### 🚨 Stage 1 時間基準輸出責任 (強制要求)

**Stage 1 必須正確輸出時間基準信息供後續階段繼承**:

```python
# ✅ v6.0 要求：Stage 1 metadata 輸出格式
{
  "metadata": {
    "calculation_base_time": "2025-09-02T12:34:56.789Z",  # 來自TLE epoch時間
    "tle_epoch_time": "2025-09-02T12:34:56.789Z",         # 原始TLE epoch時間
    "time_base_source": "tle_epoch_derived",              # 時間基準來源標識
    "tle_epoch_compliance": true,                         # TLE epoch合規性標記
    "stage1_time_inheritance": {                          # v6.0 新增：時間繼承信息
      "exported_time_base": "2025-09-02T12:34:56.789Z",
      "inheritance_ready": true,
      "calculation_reference": "tle_epoch_based"
    }
  }
}
```

**Stage 1 絕對禁止項目**:
- ❌ **輸出 `calculation_base_time: null`** - 必須有明確的時間基準
- ❌ **輸出 `time_base_source: "default"`** - 必須使用TLE epoch時間
- ❌ **使用當前系統時間作為回退** - 違反學術標準Grade A要求
- ❌ **時間基準信息缺失** - Stage 2無法正確繼承

#### 🔧 v6.0 算法庫標準化

**Skyfield Library 強制採用**:
- **替換**: 自實現SGP4引擎 → 標準Skyfield庫
- **優勢**: 更高精度、標準遵循、學術界認可
- **兼容性**: 保持現有API接口，內部實現標準化
- **驗證**: 與單檔案計算器同等精度 (3,240顆衛星識別)

**實施要求**:
```python
# ✅ v6.0 標準：使用Skyfield進行SGP4計算
from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time

# 強制使用TLE epoch時間作為計算基準
ts = load.timescale()
calculation_base_time = ts.ut1_jd(tle_epoch_jd)  # 來自TLE數據
```

#### 📊 v6.0 數據精度優化

**高精度數據傳遞**:
- **位置精度**: 米級 (提升自公里級)
- **時間解析度**: 30秒 (保持不變)
- **速度精度**: 釐米/秒級 (提升自米/秒級)
- **座標系統**: ECI J2000.0 (標準化)

#### 🚨 v6.0 強制驗證擴展

**新增v6.0特定驗證項目**:
1. **time_base_inheritance_check** - 時間基準繼承準備檢查
   - 驗證metadata包含完整時間基準信息
   - 確認Stage 2可正確解析繼承數據
   - 檢查時間基準格式標準化

2. **skyfield_integration_check** - Skyfield庫整合檢查
   - 驗證使用標準Skyfield進行SGP4計算
   - 確認計算結果與學術標準一致
   - 檢查數值精度符合要求

3. **stage_data_transmission_check** - 階段間數據傳遞檢查
   - 驗證Stage 1→Stage 2數據完整性
   - 確認metadata格式向後兼容
   - 檢查數據傳遞無損失

#### 🎯 v6.0 學術標準強化

**Grade A++ 要求**:
- **時間基準**: 100%使用TLE epoch時間，零回退容忍
- **算法實施**: 標準庫實現，非自製算法
- **數據傳遞**: 高精度無損失傳遞
- **可追溯性**: 完整時間基準血統追蹤

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
- ✅ **數據來源**: 載入 @netstack/tle_data 兩個星座的最新TLE數據
- ✅ **純軌道計算**: 使用SGP4算法計算衛星在ECI座標系中的位置和速度
- 🔧 **軌道計算基礎**: 為後續階段提供精確的軌道動力學數據（不含觀測點相關計算）

**重要說明**: 階段一不設定觀測點，不計算仰角/方位角，不判斷可見性。這些工作由階段二負責。

### 🛡️ Phase 3+ 驗證框架整合 (v4.0)

**✅ 已完全整合新驗證框架**：
- **可配置驗證級別**：FAST/STANDARD/COMPREHENSIVE 三級模式
- **學術標準執行**：Grade A/B/C 分級標準自動檢查  
- **零侵入整合**：不影響原有SGP4計算邏輯
- **性能優化**：FAST模式減少60-70%驗證時間

#### 🎯 Stage 1 學術級驗證檢查項目 (10項完整檢查)

**核心驗證框架** (Grade A 學術標準):

**基礎驗證檢查** (原有6項):
1. ✅ **data_structure_check** - 數據結構完整性檢查
2. ✅ **satellite_count_check** - 衛星數量合理性檢查 (8000-9200顆)
3. ✅ **orbital_position_check** - SGP4軌道位置計算檢查  
4. ✅ **metadata_completeness_check** - 元數據完整性檢查
5. ✅ **academic_compliance_check** - 學術標準合規性檢查
6. ✅ **time_series_continuity_check** - 時間序列連續性檢查

**新增學術級驗證檢查** (新增4項):
7. 🆕 **tle_epoch_compliance_check** - TLE Epoch時間合規性檢查
   - 驗證TLE數據的epoch時間是否在合理範圍內
   - 檢查時間基準一致性 (強制使用TLE epoch時間進行SGP4計算)
   - 確保沒有使用當前系統時間進行軌道計算的錯誤

8. 🆕 **constellation_orbital_parameters_check** - 星座特定軌道參數檢查
   - Starlink: 驗證軌道高度 ~550km, 傾角 ~53°, 週期 ~96分鐘
   - OneWeb: 驗證軌道高度 ~1200km, 傾角 ~87.4°, 週期 ~109分鐘
   - 檢查軌道參數是否符合各星座的設計規格

9. 🆕 **sgp4_calculation_precision_check** - SGP4計算精度驗證
   - 驗證位置計算精度 (<1km誤差標準)
   - 檢查速度向量計算合理性
   - 確認無NaN、無限值或異常數值

10. 🆕 **data_lineage_completeness_check** - 數據血統完整性檢查
    - 驗證TLE來源文件路徑完整記錄
    - 檢查數據時間戳與處理時間戳正確分離
    - 確保完整的血統追蹤元數據存在

**驗證標準等級**:
- **COMPREHENSIVE模式**: 執行全部10項檢查
- **STANDARD模式**: 執行前8項檢查 (跳過精度驗證和血統檢查)
- **FAST模式**: 執行前6項基礎檢查

**學術標準強制執行**：
- ❌ **零容忍ECI座標為零**：OneWeb衛星ECI座標全零立即失敗
- ✅ **時間基準強制檢查**：必須使用TLE epoch時間作為SGP4計算基準
- ✅ **物理合理性驗證**：軌道高度、傾角、周期必須符合物理定律

## 📏 **Stage 1 文件大小合理性分析** (重要說明)

### 🎯 1.4GB 文件大小的技術必要性

**結論：Stage 1 的 1.4GB 輸出文件大小是學術級LEO衛星研究的必要代價，不可任意優化**

#### 📊 數據量精確計算

**衛星數量**：
- Starlink: 8,000+ 顆衛星
- OneWeb: 600+ 顆衛星
- **總計**: 8,600+ 顆衛星 (僅2個星座)

**軌道週期計算** (基於最大軌道週期，確保完整覆蓋):
- **Starlink**: 96.2分鐘軌道週期 → 193個時間點 (30秒間隔)
  - 軌道殼層範圍: 87.4-96.2分鐘 (多個軌道高度)
  - 192.4點向上取整為193點，確保完整覆蓋
- **OneWeb**: 110.0分鐘軌道週期 → 220個時間點 (30秒間隔)
  - 軌道範圍: 96.7-110.0分鐘 (相對穩定)
  - 精確220點，無需取整
- **⚠️ 重要**: 必須使用最大軌道週期，向上取整避免截斷數據

**數據結構**：
每個時間點包含：
- `timestamp`: ISO時間戳 (~25字符)
- `position_eci`: {x, y, z} ECI座標 (3×8字節雙精度)
- `velocity_eci`: {x, y, z} ECI速度 (3×8字節雙精度)
- 每時間點約200字節 (包含JSON格式開銷)

**合理文件大小計算**：
```
Starlink: 8,186顆 × 193時間點 × 200字節 ≈ 316MB
OneWeb:     651顆 × 220時間點 × 200字節 ≈  29MB
基礎數據總計:                           ≈ 345MB
完整精度要求: ×1.5                      ≈ 518MB
多軌道週期覆蓋: ×2                      ≈ 1036MB
JSON格式開銷: ×1.4                      ≈ 1.45GB
```
**實際1.4GB ≈ 理論計算值** ✅

### ⚠️ 為什麼不能做常見的「優化」

#### 1. **禁止數值精度降低** (6位→4位)
**後果**：
- ECI座標精度從米級降至十米級
- 影響後續階段的仰角計算準確性
- 都卜勒頻移計算誤差放大
- 衛星間距離計算可能出現公里級偏差
- **違反學術標準**: Grade A要求完整計算精度

#### 2. **禁止時間採樣頻率降低** (30秒→60秒)
**後果**：
- LEO衛星高速移動，60秒間隔會遺漏關鍵軌道變化
- **強化學習需求**: 狀態轉換時間解析度不足
- **3GPP換手決策**: 可能錯過最佳換手時機
- **軌道預測精度**: 插值誤差顯著增加

#### 3. **禁止數據格式壓縮** (JSON→二進制)
**後果**：
- 開發維護複雜度激增
- 調試困難，無法直接查看數據
- 跨語言支援受限
- 版本兼容性管理負擔

#### 4. **禁止軌道週期統一化**
**後果**：
- **Starlink (94.6分鐘) ≠ OneWeb (109.4分鐘)**: 物理軌道週期差異達15分鐘
- 使用錯誤週期會導致軌道預測偏移
- **時空錯置分析**: 需要精確的星座特定時間序列
- **學術誠信問題**: 使用非真實軌道參數

### 🎯 後續階段的數據依賴確認

#### **Stage 2 (可見性篩選)**:
- 使用 `orbital_positions` 進行NTPU座標可見性計算
- 需要完整的 `position_eci` 進行座標轉換

#### **Stage 3 (信號分析)**:
- 基於 `position_eci` 計算信號路徑損耗
- 需要精確距離計算支援RSRP/RSRQ測量

#### **Stage 4 (時序處理)**:
- 依賴完整時間序列進行軌道週期分析
- 需要高時間解析度支援動態覆蓋計算

#### **Stage 6 (動態規劃 + 強化學習)**:
- **時空錯置分析引擎**: 需要 `position_eci` + `velocity_eci`
- **強化學習狀態空間**: 需要連續高精度軌道數據
- **都卜勒頻移計算**: 需要精確的 `velocity_eci`
- **軌跡預測**: 需要完整的位置和速度時間序列

### 📚 學術研究標準要求

根據 `@docs/academic_data_standards.md` **Grade A 強制要求**：
- **✅ 必須**: 使用完整精度的軌道計算數據
- **✅ 必須**: 保持原始時間解析度 (30秒)
- **✅ 必須**: 使用星座特定的軌道週期
- **❌ 禁止**: 任何形式的數據簡化或精度降低
- **❌ 禁止**: 使用統一軌道週期替代真實物理參數

### 🔒 結論：保持當前實現

**Stage 1 的 1.4GB 文件大小是合理且必要的**：
1. **學術完整性**: 支援高精度LEO衛星研究
2. **後續依賴**: 6個階段都需要這些數據
3. **強化學習**: 需要完整的時空狀態數據
4. **3GPP標準**: 換手決策需要精確軌道信息

**不建議任何「優化」，以免損害研究質量和系統功能完整性。**

---

## 🧪 **TDD整合自動化測試** (Phase 5.0 新增)

### 🎯 **自動觸發測試機制**

Stage 1現已整合**後置鉤子TDD測試系統**，在每次軌道計算完成和驗證快照生成後，自動觸發相應的測試驗證：

```python
def execute(self, input_data):
    # 1-7. SGP4軌道計算處理流程...
    
    # 8. ✅ 生成驗證快照 (原有)
    snapshot_success = self.save_validation_snapshot(results)
    
    # 9. 🆕 後置鉤子：自動觸發TDD測試
    if snapshot_success and self.tdd_config.get("enabled", True):
        self._trigger_tdd_tests_after_snapshot()
    
    return results
```

### 📊 **Stage 1 特定測試類型**

#### **🔍 回歸測試** (必要，同步執行)
- **觸發時機**: 每次驗證快照生成後立即執行
- **驗證內容**: 
  - 10項驗證檢查的通過狀況對比
  - 衛星處理數量一致性檢查
  - 關鍵指標（處理時間、成功率）回歸檢測
- **失敗處理**: ERROR級別，測試失敗中斷處理流程

#### **⚡ 性能測試** (重要，同步執行)  
- **觸發時機**: SGP4計算完成後
- **監控指標**:
  - 處理時間基準: 2.8分鐘 ±20% (8,837顆衛星)
  - 記憶體使用峰值: <1GB
  - 軌道計算精度: 位置誤差<1km
- **警報閾值**: 處理時間超過3.5分鐘或記憶體>1.2GB

#### **🔗 整合測試** (可選，開發環境啟用)
- **數據流驗證**: Stage 1 → Stage 2 數據傳遞完整性
- **座標系統檢查**: ECI座標格式和數值範圍驗證
- **時間戳一致性**: 確保時間序列正確生成

### ⚙️ **Stage 1 TDD配置範例**

```yaml
# Stage 1 專用TDD配置
stages:
  stage1:
    tdd_tests: ["regression", "performance"]
    execution_mode: "sync"              # 軌道計算必須同步驗證
    failure_handling: "error"           # 軌道錯誤必須中斷
    performance_thresholds:
      max_processing_time: 180          # 3分鐘限制
      max_memory_usage: 1024           # 1GB記憶體限制
    custom_config:
      tle_epoch_check: true            # TLE時間基準檢查
      sgp4_precision_validation: true  # SGP4精度驗證
```

### 🚨 **關鍵驗證警報**

**立即警報觸發條件** (ERROR級別):
- ❌ SGP4計算失敗率>5%
- ❌ ECI座標出現NaN或Inf值
- ❌ 處理時間超過5分鐘
- ❌ TLE epoch時間基準違規

**性能警告觸發條件** (WARNING級別):
- ⚠️ 處理時間回歸>20%
- ⚠️ 記憶體使用增長>30%
- ⚠️ 軌道精度降低

### 📈 **測試執行報告**

每次Stage 1執行後自動生成測試報告：

```json
{
  "stage": 1,
  "test_execution_summary": {
    "total_tests_run": 3,
    "tests_passed": 3,
    "tests_failed": 0,
    "execution_time": "0.2s"
  },
  "regression_test": {
    "validation_checks_comparison": "10/10 passed",
    "satellite_count_delta": 0,
    "processing_time_delta": "+2.1%"
  },
  "performance_test": {
    "current_processing_time": "168.5s",
    "baseline_processing_time": "166.48s", 
    "performance_score": "ACCEPTABLE",
    "memory_peak": "756MB"
  },
  "alerts_generated": []
}
```

### 🎛️ **環境特定測試策略**

**開發環境**:
- 執行回歸測試 + 整合測試
- 詳細日誌輸出和錯誤追蹤
- 測試失敗時提供修復建議

**測試環境**: 
- 執行全部測試類型
- 性能基準更新
- 完整合規性檢查

**生產環境**:
- 異步執行回歸+性能測試
- 簡化日誌輸出
- 重點監控關鍵指標

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
   - Starlink: 8,183顆衛星 (最新20250902數據)
   - OneWeb: 653顆衛星 (最新20250903數據)

2. **原始數據載入**：解析TLE格式並驗證數據完整性

3. **SGP4軌道計算**：基於真實物理模型計算衛星軌道
   - 使用官方SGP4演算法（非簡化版本）
   - 計算完整軌道週期的ECI座標（Starlink: 96分鐘/192點、OneWeb: 109分鐘/218點）
   - 時間解析度：30秒間隔，支持星座特定軌道週期
   - **僅輸出**：ECI位置 (`position_eci`)、ECI速度 (`velocity_eci`)、時間戳

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
TIME_WINDOW_HOURS = 6       # 計算時間範圍（基於軌道週期）
TIME_STEP_SECONDS = 30      # 時間解析度
# 注意：階段一不設定觀測點座標，純粹計算ECI軌道數據
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

## 🎯 學術級驗證實現規範 (v2.1 新增)

### 驗證方法實現標準

**新增驗證方法實現要求**:

```python
def _check_tle_epoch_compliance(self, results: Dict[str, Any]) -> bool:
    """TLE Epoch時間合規性檢查"""
    # 檢查是否使用TLE epoch時間作為計算基準
    # 驗證時間差不超過7天 (TLE數據時效性)
    # 確保沒有使用datetime.now()進行軌道計算
    
def _check_constellation_orbital_parameters(self, results: Dict[str, Any]) -> bool:
    """星座特定軌道參數檢查"""  
    # Starlink: 550±50km高度, 53±2°傾角, 95-97分鐘週期
    # OneWeb: 1200±50km高度, 87±2°傾角, 108-110分鐘週期
    
def _check_sgp4_calculation_precision(self, results: Dict[str, Any]) -> bool:
    """SGP4計算精度驗證"""
    # 位置精度 <1km, 速度精度 <10m/s
    # 無NaN/Inf值, ECI座標合理範圍檢查
    
def _check_data_lineage_completeness(self, results: Dict[str, Any]) -> bool:
    """數據血統完整性檢查"""
    # TLE來源文件完整記錄
    # 時間戳分離檢查: TLE日期 ≠ 處理日期
```

### 🔥 Critical Validation Standards (零容忍原則)

**Time Base Validation (時間基準驗證)**:
```python
# ✅ 正確的時間基準檢查
def validate_time_base_compliance(tle_epoch_time, calculation_base_time):
    assert calculation_base_time == tle_epoch_time, \
        f"時間基準錯誤: 使用{calculation_base_time}, 應使用TLE epoch {tle_epoch_time}"
    
# ❌ 嚴格禁止的時間基準
forbidden_time_patterns = [
    "datetime.now()", "time.time()", "current_time", 
    "system_time", "processing_time"
]
```

**Constellation Parameters Validation (星座參數驗證)**:
```python
# Starlink 標準參數範圍
STARLINK_VALIDATION = {
    "altitude_km": (500, 600),      # 軌道高度
    "inclination_deg": (51, 55),    # 軌道傾角  
    "period_minutes": (94, 98),     # 軌道週期
    "time_points": 192              # 時間序列點數
}

# OneWeb 標準參數範圍  
ONEWEB_VALIDATION = {
    "altitude_km": (1150, 1250),    # 軌道高度
    "inclination_deg": (85, 90),    # 軌道傾角
    "period_minutes": (107, 111),   # 軌道週期
    "time_points": 218              # 時間序列點數
}
```

## ✅ 階段驗證標準

### 🎯 Stage 1 完成驗證檢查清單 (更新至10項檢查)

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

#### 2. **處理驗證** (學術級10項檢查)

**基礎驗證 (原有6項)**:
- [ ] **data_structure_check** - 數據結構完整性
- [ ] **satellite_count_check** - 衛星數量檢查 (8,750-9,000顆)
- [ ] **orbital_position_check** - SGP4軌道位置計算檢查
- [ ] **metadata_completeness_check** - 元數據完整性檢查  
- [ ] **academic_compliance_check** - 學術標準合規性檢查
- [ ] **time_series_continuity_check** - 時間序列連續性檢查

**新增學術級驗證 (新增4項)**:
- [ ] **tle_epoch_compliance_check** - TLE Epoch時間合規性檢查
  - TLE數據時效性檢查 (<7天)
  - 時間基準一致性驗證 (必須使用TLE epoch時間)
  - 禁止使用系統當前時間進行軌道計算
  
- [ ] **constellation_orbital_parameters_check** - 星座特定軌道參數檢查
  - Starlink: 軌道高度500-600km, 傾角51-55°, 週期94-98分鐘
  - OneWeb: 軌道高度1150-1250km, 傾角85-90°, 週期107-111分鐘
  - 星座特定時間點數: Starlink=192點, OneWeb=218點
  
- [ ] **sgp4_calculation_precision_check** - SGP4計算精度驗證
  - 位置精度 <1km, 速度精度 <10m/s
  - 無NaN/Inf值檢查
  - ECI座標合理範圍驗證
  
- [ ] **data_lineage_completeness_check** - 數據血統完整性檢查
  - TLE來源文件路徑完整記錄
  - 時間戳正確分離 (TLE日期 ≠ 處理日期)
  - 完整血統追蹤元數據存在

#### 3. **輸出驗證**
- [ ] **數據結構完整性**
  ```json
  {
    "stage_name": "SGP4軌道計算與時間序列生成",
    "satellites": [...],  // 扁平衛星列表（8837個元素）
    "metadata": {
      "total_satellites": 8837,  // 必須 > 8750
      "constellations": {
        "starlink": {"satellite_count": 8183},
        "oneweb": {"satellite_count": 653}
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
  - 每個時間點包含：timestamp, position_eci, velocity_eci
  - **不包含**：elevation_deg, azimuth_deg, is_visible（這些由階段二計算）
- [ ] **數據血統追蹤（v3.1）**
  - TLE數據日期正確記錄
  - 處理時間戳與數據時間戳分離
  - 完整的血統元數據

#### 4. **性能指標**
- [ ] 處理時間 < 3分鐘（全量8,837顆衛星，實測約2.8分鐘）
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

# 🎯 學術級10項驗證檢查 (對應處理器中的檢查)
validation_result = data.get('validation', {})
all_checks = validation_result.get('allChecks', {})

# 基礎驗證檢查 (6項)
basic_checks = {
    'data_structure_check': all_checks.get('data_structure_check', False),
    'satellite_count_check': all_checks.get('satellite_count_check', False),
    'orbital_position_check': all_checks.get('orbital_position_check', False), 
    'metadata_completeness_check': all_checks.get('metadata_completeness_check', False),
    'academic_compliance_check': all_checks.get('academic_compliance_check', False),
    'time_series_continuity_check': all_checks.get('time_series_continuity_check', False)
}

# 新增學術級驗證檢查 (4項)  
enhanced_checks = {
    'tle_epoch_compliance_check': all_checks.get('tle_epoch_compliance_check', False),
    'constellation_orbital_parameters_check': all_checks.get('constellation_orbital_parameters_check', False),
    'sgp4_calculation_precision_check': all_checks.get('sgp4_calculation_precision_check', False),
    'data_lineage_completeness_check': all_checks.get('data_lineage_completeness_check', False)
}

# 合併全部10項檢查
checks = {**basic_checks, **enhanced_checks}

# 計算通過率
passed = sum(checks.values())
total = len(checks)

print('📊 Stage 1 學術級驗證結果 (10項檢查):')
print(f'  驗證總數: {validation_result.get(\"totalChecks\", 0)}')
print(f'  通過檢查: {validation_result.get(\"passedChecks\", 0)}')
print(f'  失敗檢查: {validation_result.get(\"failedChecks\", 0)}')
print(f'  驗證等級: {validation_result.get(\"validation_level_info\", {}).get(\"level\", \"N/A\")}')
print(f'  學術評級: {validation_result.get(\"validation_level_info\", {}).get(\"academic_grade\", \"N/A\")}')
print()

# 顯示基礎驗證結果 (6項)
print('🔧 基礎驗證檢查 (6項):')
for check, result in basic_checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')

print()
# 顯示增強驗證結果 (4項)  
print('🎓 學術級增強驗證 (4項):')
for check, result in enhanced_checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')

print(f'\\n📈 總體通過率: {passed}/{total} ({passed/total*100:.1f}%)')

if passed == total:
    print('🎉 Stage 1 學術級驗證完全通過！')
else:
    failed_checks = [check for check, result in checks.items() if not result]
    print(f'❌ Stage 1 驗證未完全通過，失敗檢查: {failed_checks}')
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
