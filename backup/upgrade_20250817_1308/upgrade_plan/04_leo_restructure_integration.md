# 🔗 Phase 3: leo_restructure 技術資產整合計劃

**風險等級**: 🟡 中風險  
**預估時間**: 1.5小時  
**必要性**: ✅ 重要 - 整合優秀技術資產，提升系統架構

## 🎯 目標

將 leo_restructure 目錄中的技術資產整合到恢復的六階段系統中，包括：
- 完整數據模型系統
- 智能增量更新機制  
- 高效開發工具鏈
- 模擬退火優化器取代階段六

## 📋 leo_restructure 核心資產清單

### 1. 數據模型系統 (shared_core/data_models.py)
- SatelliteState: 衛星狀態標準化
- HandoverEventData: 換手事件數據
- VisibilityMetrics: 可見性指標
- PoolSolution: 衛星池解決方案

### 2. 智能增量更新 (shared_core/incremental_update_manager.py)  
- TLE數據變更檢測
- 代碼變更檢測
- 智能更新策略建議

### 3. 高效開發工具鏈
- leo-dev: 30秒快速開發模式
- leo-test: 3分鐘功能測試
- leo-full: 10分鐘完整驗證

### 4. 模擬退火優化器 (algorithms/simulated_annealing.py)
- 動態池規劃演算法
- 多目標優化能力

## 🔧 整合執行計劃

### Step 1: 整合數據模型系統
```bash
# 複製數據模型到六階段系統
cp /home/sat/ntn-stack/leo_restructure/shared_core/data_models.py \
   /home/sat/ntn-stack/netstack/src/shared/leo_data_models.py

# 更新各階段處理器使用統一數據模型
# TODO: 修改stage1-6處理器的輸入輸出格式
```

### Step 2: 整合智能增量更新
```bash
# 複製增量更新管理器
cp /home/sat/ntn-stack/leo_restructure/shared_core/incremental_update_manager.py \
   /home/sat/ntn-stack/netstack/src/core/intelligent_update_manager.py
```

### Step 3: 模擬退火優化器取代階段六
```bash
# 用模擬退火取代原始階段六
cp /home/sat/ntn-stack/leo_restructure/algorithms/simulated_annealing.py \
   /home/sat/ntn-stack/netstack/src/stages/simulated_annealing_stage6.py
```

### Step 4: 整合開發工具鏈
```bash
# 複製開發工具腳本
cp -r /home/sat/ntn-stack/leo_restructure/tools/ \
      /home/sat/ntn-stack/tools/leo_dev_tools/
```

## ✅ 整合驗證檢查清單

- [ ] 數據模型系統已整合並測試
- [ ] 智能增量更新機制運作正常
- [ ] 模擬退火優化器替換階段六成功
- [ ] 開發工具鏈功能正常
- [ ] 所有階段處理器使用統一數據格式

---
**下一步**: 繼續執行 `05_cross_platform_fixes.md`
