# Phase 4-6 全面重構計劃

## 🚨 重構現況評估
**當前完成度**: ~5% (只完成Stage 1/3的部分清理)
**剩餘工作量**: ~95% (14個大型檔案需拆分，數百個跨階段違規需修復)

## Phase 4: 超大檔案緊急拆分 (2-3天)

### 🥇 緊急優先級：Stage 6 temporal_spatial_analysis_engine.py
**問題**: 5,821行，71%違規功能 (104/145方法)
**行動**:
1. 提取55個軌道計算方法 → 移至Stage 1或創建共享模組
2. 提取32個可見性方法 → 移至Stage 2或創建共享模組  
3. 提取17個時間序列方法 → 移至Stage 4
4. 保留41個合法的動態池規劃方法
5. 目標：縮減至<800行

### 🥈 高優先級：Stage 4 timeseries_preprocessing_processor.py  
**問題**: 2,503行，包含178個違規功能
**行動**:
1. 移除93個軌道計算功能 → Stage 1
2. 移除85個信號分析功能 → Stage 3
3. 保留純時間序列預處理功能
4. 目標：縮減至<1000行

### 🥉 中優先級：其他大型檔案
**行動**:
- Stage 5 processor (2,477行) → <1000行
- Stage 3 processor (2,484行) → <1000行  
- Stage 1 processor (1,969行) → <1000行

## Phase 5: 跨階段功能重新分配 (2-3天)

### 功能歸屬重新定義
1. **軌道計算模組集中化** (Stage 1)
   - 統一SGP4計算
   - 統一TLE處理
   - 統一軌道元素計算

2. **可見性分析模組集中化** (Stage 2)
   - 統一仰角/方位角計算
   - 統一覆蓋視窗分析
   - 統一觀測者幾何計算

3. **信號分析模組集中化** (Stage 3)
   - 統一信號品質計算
   - 統一換手決策邏輯
   - 統一3GPP事件處理

### 共享模組創建
**創建**: `src/shared/cross_stage_modules/`
- `orbital_calculations.py` - 跨Stage軌道計算工具
- `visibility_calculations.py` - 跨Stage可見性計算工具
- `signal_calculations.py` - 跨Stage信號計算工具

## Phase 6: 文檔同步更新 (1-2天)

### 文檔更新範圍
1. **Stage文檔更新**
   - `/docs/stages/stage1-tle-loading.md` - 反映實際軌道計算範圍
   - `/docs/stages/stage2-filtering.md` - 反映實際可見性分析範圍
   - `/docs/stages/stage3-signal.md` - 反映實際信號分析範圍
   - `/docs/stages/stage4-timeseries.md` - 反映實際時間序列範圍
   - `/docs/stages/stage5-integration.md` - 反映實際整合範圍
   - `/docs/stages/stage6-dynamic-pool.md` - 反映實際動態池範圍

2. **架構文檔更新**
   - `MODULAR_ARCHITECTURE_GUIDE.md` - 更新模組化架構指南
   - `data_processing_flow.md` - 更新數據處理流程
   - `system_architecture.md` - 更新系統架構圖

3. **新增文檔**
   - `PHASE4_6_REFACTORING_COMPLETION_REPORT.md` - 全面重構完成報告
   - `LARGE_FILE_BREAKDOWN_ANALYSIS.md` - 大型檔案拆分分析
   - `CROSS_STAGE_VIOLATION_RESOLUTION.md` - 跨階段違規解決方案

## 🎯 成功標準
1. **檔案大小**: 所有Stage處理器 < 1000行
2. **功能邊界**: 0%跨階段違規
3. **測試通過**: 所有Stage獨立執行成功
4. **文檔同步**: 文檔100%反映實際實現

## ⚠️ 風險評估
- **高風險**: Stage 6檔案拆分可能影響動態池邏輯
- **中風險**: 跨Stage功能移動可能破壞數據流  
- **低風險**: 文檔更新工作量大但技術風險低

## 📅 預估時程
- Phase 4: 2-3天 (超大檔案拆分)
- Phase 5: 2-3天 (功能重新分配)  
- Phase 6: 1-2天 (文檔更新)
- **總計**: 5-8天完成全面重構