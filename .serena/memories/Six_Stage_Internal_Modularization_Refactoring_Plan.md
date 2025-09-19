# 六階段內部模組化重構計劃

## 📊 重構需求分析

### 🎯 重構目標
- **主要目標**: 解決超過1000行的檔案問題
- **次要目標**: 清理跨階段功能混雜
- **最終目標**: 整合重複功能，建立乾淨的六階段架構

### 🚨 當前問題評估
**超大檔案問題**:
- Stage 6: temporal_spatial_analysis_engine.py (5,821行) - 最嚴重
- Stage 4: timeseries_preprocessing_processor.py (2,503行) - 嚴重
- Stage 5: stage5_processor.py (2,477行) - 嚴重
- Stage 3: stage3_signal_analysis_processor.py (2,484行) - 嚴重
- Stage 1: tle_orbital_calculation_processor.py (1,969行) - 中等

**跨階段功能混雜**:
- Stage 6包含179個Stage 1功能 (軌道計算)
- Stage 6包含130個Stage 2功能 (可見性計算)
- Stage 4包含93個Stage 1功能 + 115個Stage 3功能
- 各階段都有不同程度的功能越界

**重複功能問題**:
- 7個檔案包含重複的軌道計算功能
- 8個檔案包含重複的信號計算功能  
- 6個檔案包含重複的可見性計算功能

## 📋 三階段重構計劃

### **Phase 1: 共享核心模組建立** (2-3天)

#### 目標: 解決重複功能問題
創建統一的共享核心模組，避免功能重複

#### 具體行動:
1. **建立共享目錄結構**:
   ```
   src/shared/core_modules/
   ├── orbital_calculations_core.py      # 統一軌道計算模組
   ├── visibility_calculations_core.py   # 統一可見性計算模組
   ├── signal_calculations_core.py       # 統一信號計算模組  
   ├── physics_constants.py              # 統一物理常數
   ├── time_standards.py                 # 統一時間基準處理
   └── math_utilities.py                 # 統一數學工具函數
   ```

2. **提取重複功能**:
   - 從7個檔案提取軌道計算功能到orbital_calculations_core.py
   - 從8個檔案提取信號計算功能到signal_calculations_core.py
   - 從6個檔案提取可見性計算功能到visibility_calculations_core.py

3. **確保學術標準**:
   - 所有時間基準統一使用TLE epoch時間
   - 使用標準庫(Skyfield)確保計算精度
   - 無假設值回退機制

### **Phase 2: 超大檔案內部拆分** (3-4天)

#### 目標: 將所有主處理器檔案控制在1000行以內

#### 2.1 Stage 6拆分 (最優先 - 5,821行)
**檔案**: temporal_spatial_analysis_engine.py

**拆分策略**:
1. **移除跨階段違規功能** (~3,000行):
   - 55個軌道計算方法 → 移至shared/orbital_calculations_core.py
   - 32個可見性分析方法 → 移至shared/visibility_calculations_core.py

2. **保留功能模組化拆分** (~2,800行):
   ```
   ├── stage6_core_processor.py              # 主處理器 (<800行)
   ├── dynamic_pool_strategy_engine.py       # 動態池策略引擎 (<700行)
   ├── coverage_optimization_engine.py       # 覆蓋優化引擎 (<700行)
   ├── backup_satellite_manager.py           # 備份衛星管理 (<600行)
   └── pool_planning_utilities.py            # 規劃工具函數 (<500行)
   ```

#### 2.2 Stage 4拆分 (次優先 - 2,503行)
**檔案**: timeseries_preprocessing_processor.py

**拆分策略**:
1. **移除跨階段違規功能** (~1,000行):
   - 93個軌道計算功能 → 使用shared/orbital_calculations_core.py
   - 115個信號分析功能 → 使用shared/signal_calculations_core.py

2. **保留功能模組化拆分** (~1,500行):
   ```
   ├── stage4_core_processor.py              # 主處理器 (<800行)
   ├── animation_data_builder.py             # 動畫數據建構器 (<500行)  
   ├── timeseries_formatter.py               # 時間序列格式化 (<400行)
   └── preprocessing_utilities.py            # 預處理工具函數 (<300行)
   ```

#### 2.3 其他Stage拆分
**Stage 5**: stage5_processor.py (2,477行)
**Stage 3**: stage3_signal_analysis_processor.py (2,484行)
**Stage 1**: tle_orbital_calculation_processor.py (1,969行)

類似策略進行拆分，確保主處理器 < 1000行

### **Phase 3: 架構驗證與最佳化** (1-2天)

#### 目標: 確保重構後系統正常運作

#### 具體行動:
1. **功能驗證**:
   - 測試所有Stage獨立執行
   - 驗證Stage間數據傳遞
   - 確認無功能遺失

2. **性能驗證**:
   - 執行完整六階段流程
   - 比較重構前後處理時間
   - 確保無性能回歸

3. **學術標準驗證**:
   - 確認時間基準一致性
   - 驗證計算結果精度
   - 檢查無假設值使用

## 🎯 成功標準

### 量化指標:
- ✅ **檔案大小**: 所有主處理器 < 1000行
- ✅ **功能純度**: 0%跨階段功能違規  
- ✅ **程式碼重複**: 0%重複功能實現
- ✅ **六階段完整**: 保持完整的數據處理流程

### 質量標準:
- ✅ **學術合規**: Grade A標準，TLE epoch時間基準
- ✅ **架構清晰**: 每個檔案職責單一明確
- ✅ **可維護性**: 模組化設計易於維護擴展
- ✅ **可測試性**: 每個模組可獨立測試

## 📅 執行時間表

**總預估時間**: 6-9天

- **Phase 1** (2-3天): 共享核心模組建立
- **Phase 2** (3-4天): 超大檔案拆分
- **Phase 3** (1-2天): 驗證與最佳化

## ⚠️ 風險控制

### 技術風險:
- **數據流中斷**: 確保模組拆分不影響Stage間數據傳遞
- **功能遺失**: 詳細記錄移動的功能，確保無遺漏
- **性能影響**: 監控模組化後的性能變化

### 緩解措施:
- **備份策略**: 重構前完整備份所有檔案
- **漸進驗證**: 每個Phase完成後立即驗證
- **回退計劃**: 如有問題可快速回退到重構前狀態

## 📝 預期成果

重構完成後將實現:

1. **乾淨的六階段架構**: 每個Stage職責清晰，無功能越界
2. **可維護的程式碼**: 所有檔案 < 1000行，易於理解和維護  
3. **高品質的共享模組**: 統一的核心功能，避免重複開發
4. **符合學術標準**: Grade A合規，適合論文發表
5. **擴展準備**: 為未來強化學習和GLB渲染做好架構準備

這個重構將為後續的強化學習開發和前端渲染提供穩固的基礎架構。