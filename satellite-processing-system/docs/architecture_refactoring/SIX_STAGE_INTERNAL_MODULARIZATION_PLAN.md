# 📋 六階段內部模組化重構計劃

**版本**: 1.0.0
**建立日期**: 2025-09-18
**狀態**: 待執行
**目標**: 解決超大檔案問題，清理跨階段功能混雜，保持六階段架構

---

## 🎯 重構背景與目標

### 重構必要性
基於對當前系統的分析，發現了以下關鍵問題：
- **14個檔案超過1000行**，嚴重違反模組化原則
- **跨階段功能混雜嚴重**，Stage 6包含87個違規方法
- **重複功能普遍存在**，7-8個檔案包含相同計算功能
- **架構複雜度過高**，不利於維護和擴展

### 重構原則
1. **保持六階段架構** - 為未來強化學習和GLB渲染準備
2. **內部模組化** - 將超大檔案拆分為合理模組
3. **功能去重** - 建立統一的共享核心模組
4. **學術標準** - 確保Grade A學術合規性

## 📊 當前問題詳細分析

### 超大檔案問題
| Stage | 檔案名 | 行數 | 嚴重性 |
|-------|--------|------|---------|
| Stage 6 | temporal_spatial_analysis_engine.py | 5,821 | 🚨 極嚴重 |
| Stage 4 | timeseries_preprocessing_processor.py | 2,503 | 🚨 嚴重 |
| Stage 5 | stage5_processor.py | 2,477 | 🚨 嚴重 |
| Stage 3 | stage3_signal_analysis_processor.py | 2,484 | 🚨 嚴重 |
| Stage 1 | tle_orbital_calculation_processor.py | 1,969 | ⚠️ 中等 |

### 跨階段功能混雜
- **Stage 6最嚴重**: 包含179個軌道計算 + 130個可見性計算功能
- **Stage 4**: 包含93個軌道計算 + 115個信號分析功能
- **Stage 3**: 包含10個軌道計算 + 66個可見性計算功能
- **各Stage普遍越界**: 功能邊界模糊

### 重複功能統計
- **軌道計算重複**: 7個檔案包含 `_calculate_orbital` 功能
- **信號計算重複**: 8個檔案包含 `_calculate_signal` 功能
- **可見性計算重複**: 6個檔案包含 `_calculate_elevation` 功能

## 🗓️ 三階段重構計劃

### **Phase 1: 共享核心模組建立** (2-3天)

#### 目標
解決重複功能問題，建立統一的核心計算模組

#### 具體行動

**1.1 建立共享目錄結構**
```
src/shared/core_modules/
├── __init__.py
├── orbital_calculations_core.py      # 統一軌道計算 (整合7個重複功能)
├── visibility_calculations_core.py   # 統一可見性計算 (整合6個重複功能)
├── signal_calculations_core.py       # 統一信號計算 (整合8個重複功能)
├── physics_constants.py              # 統一物理常數定義
├── time_standards.py                 # 統一時間基準處理 (TLE epoch)
└── math_utilities.py                 # 統一數學工具函數
```

**1.2 核心模組設計原則**
- **學術Grade A標準**: 使用TLE epoch時間基準
- **標準庫優先**: 使用Skyfield等標準庫確保精度
- **無假設值**: 禁止任何預設值回退機制
- **單一職責**: 每個模組專注單一計算領域

**1.3 重複功能整合計劃**
- 從7個檔案提取軌道計算功能 → `orbital_calculations_core.py`
- 從8個檔案提取信號計算功能 → `signal_calculations_core.py`
- 從6個檔案提取可見性計算功能 → `visibility_calculations_core.py`

### **Phase 2: 超大檔案內部拆分** (3-4天)

#### 2.1 Stage 6緊急拆分 (最高優先級)
**問題檔案**: `temporal_spatial_analysis_engine.py` (5,821行, 145個方法)

**拆分策略**:
```
Step 1: 移除跨階段違規功能 (~87個方法)
├── 55個軌道計算方法 → 使用 shared/orbital_calculations_core.py
├── 32個可見性分析方法 → 使用 shared/visibility_calculations_core.py
└── 預估減少 ~3,000行

Step 2: 保留功能模組化拆分 (~58個方法, ~2,800行)
├── stage6_core_processor.py              # 主處理器 (<800行)
├── dynamic_pool_strategy_engine.py       # 動態池策略 (<700行)
├── coverage_optimization_engine.py       # 覆蓋優化 (<700行)
├── backup_satellite_manager.py           # 備份管理 (<600行)
└── pool_planning_utilities.py            # 工具函數 (<500行)
```

#### 2.2 Stage 4拆分 (次高優先級)
**問題檔案**: `timeseries_preprocessing_processor.py` (2,503行)

**拆分策略**:
```
Step 1: 移除跨階段違規功能
├── 93個軌道計算功能 → 使用 shared/orbital_calculations_core.py
├── 115個信號分析功能 → 使用 shared/signal_calculations_core.py
└── 預估減少 ~1,000行

Step 2: 保留功能模組化拆分 (~1,500行)
├── stage4_core_processor.py              # 主處理器 (<800行)
├── animation_data_builder.py             # 動畫數據建構 (<500行)
├── timeseries_formatter.py               # 時序格式化 (<400行)
└── preprocessing_utilities.py            # 預處理工具 (<300行)
```

#### 2.3 其他Stage類似拆分
- **Stage 5**: `stage5_processor.py` (2,477行) → 拆分為4個模組
- **Stage 3**: `stage3_signal_analysis_processor.py` (2,484行) → 拆分為4個模組
- **Stage 1**: `tle_orbital_calculation_processor.py` (1,969行) → 拆分為3個模組

### **Phase 3: 架構驗證與最佳化** (1-2天)

#### 3.1 功能完整性驗證
- 測試所有Stage獨立執行能力
- 驗證六階段數據傳遞流程
- 確認無功能遺失或邏輯錯誤

#### 3.2 性能驗證
- 執行完整六階段處理流程
- 比較重構前後執行時間
- 確保無性能回歸問題

#### 3.3 學術標準驗證
- 確認所有時間基準使用TLE epoch時間
- 驗證計算結果精度符合Grade A標準
- 檢查無假設值回退機制

## 🎯 重構成功標準

### 量化指標
- ✅ **檔案大小控制**: 所有主處理器 < 1000行
- ✅ **功能邊界清晰**: 0%跨階段功能違規
- ✅ **程式碼去重**: 0%重複功能實現
- ✅ **架構完整**: 保持完整六階段數據流

### 質量標準
- ✅ **學術合規**: 100% Grade A標準合規
- ✅ **代碼品質**: 單一職責，高內聚低耦合
- ✅ **可維護性**: 模組化設計，易於維護
- ✅ **可測試性**: 每個模組可獨立測試
- ✅ **擴展準備**: 為強化學習和GLB渲染做好準備

## 📅 詳細執行時程

### Phase 1: 共享核心模組建立 (2-3天)
- **Day 1**: 建立目錄結構，設計核心模組介面
- **Day 2**: 實作orbital_calculations_core.py和visibility_calculations_core.py
- **Day 3**: 實作signal_calculations_core.py和其他工具模組

### Phase 2: 超大檔案拆分 (3-4天)
- **Day 4**: Stage 6 temporal_spatial_analysis_engine.py 拆分
- **Day 5**: Stage 4 timeseries_preprocessing_processor.py 拆分
- **Day 6**: Stage 5 和 Stage 3 拆分
- **Day 7**: Stage 1 拆分和調整

### Phase 3: 驗證與最佳化 (1-2天)
- **Day 8**: 功能和性能驗證
- **Day 9**: 學術標準驗證和文檔更新

**總預估時間**: 6-9天

## ⚠️ 風險管理

### 識別的風險
1. **資料流中斷風險**: 模組拆分可能影響Stage間資料傳遞
2. **功能遺失風險**: 複雜的功能移動可能遺漏部分邏輯
3. **性能回歸風險**: 模組化後可能影響執行效率
4. **整合複雜風險**: 新舊模組整合可能出現相容性問題

### 風險緩解措施
1. **完整備份策略**: 重構前備份所有原始檔案
2. **漸進式驗證**: 每個Phase完成後立即功能驗證
3. **詳細記錄**: 記錄所有功能移動和修改
4. **快速回退計劃**: 如有重大問題可立即回退

## 📝 預期成果與價值

### 技術成果
1. **乾淨的六階段架構**: 職責邊界清晰，無功能越界
2. **高品質程式碼**: 所有檔案 < 1000行，易於維護
3. **統一核心模組**: 避免功能重複，提高代碼品質
4. **學術標準合規**: Grade A標準，適合論文發表

### 業務價值
1. **開發效率提升**: 模組化架構提高開發和除錯效率
2. **系統可維護性**: 清晰架構降低維護成本
3. **擴展能力**: 為強化學習和GLB渲染提供良好基礎
4. **學術研究支援**: 高品質代碼支援論文發表

---

**下一步**: 等待批准後開始執行Phase 1共享核心模組建立工作。

**責任人**: Claude Code Assistant
**審查**: 待用戶確認
**狀態**: 📋 計劃制定完成，等待執行批准