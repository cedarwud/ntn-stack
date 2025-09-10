# 六階段處理器重構總計劃

## 🎯 重構目標

### 核心問題
- **文件過大**: Stage 5 (3,400行)、Stage 6 (2,662行)、Stage 1-4 (1,600-1,900行)
- **架構混亂**: 所有階段平鋪在 `/stages/` 目錄下
- **維護困難**: 單一大文件，調試和測試複雜
- **職責不清**: 處理邏輯、驗證、輸出混雜
- **代碼重複**: 各階段都有相似的驗證和輸出邏輯

### 重構目標
1. **模組化**: 將每個階段拆分為可管理的小模組
2. **標準化**: 建立統一的階段處理器接口
3. **可維護性**: 單一職責、清晰的依賴關係
4. **可擴展性**: 方便新增階段和功能
5. **可測試性**: 每個模組都可獨立測試

## 📁 新架構設計

### 目標目錄結構
```
netstack/src/pipeline/
├── README.md                          # 架構說明
├── __init__.py
├── 
├── 📁 shared/                          # 共用組件
│   ├── __init__.py
│   ├── base_processor.py              # 抽象基類
│   ├── stage_interface.py             # 標準接口定義
│   ├── validation_framework.py        # 統一驗證框架
│   ├── output_handler.py              # 統一輸出處理
│   ├── metrics_collector.py           # 指標收集
│   ├── data_lineage_tracker.py        # 數據血統追蹤
│   └── pipeline_coordinator.py        # 流程協調器
├── 
├── 📁 stages/                          # 六個階段處理器
│   ├── __init__.py
│   ├── 
│   ├── 📁 stage1_orbital_calculation/  # 階段一：軌道計算
│   │   ├── __init__.py
│   │   ├── processor.py               # 主處理器 (~200行)
│   │   ├── tle_data_loader.py         # TLE數據載入 (~300行)
│   │   ├── orbital_calculator.py      # SGP4軌道計算 (~400行)
│   │   ├── validator.py               # 驗證邏輯 (~300行)
│   │   ├── output_handler.py          # 輸出處理 (~100行)
│   │   └── config.py                  # 配置參數
│   ├── 
│   ├── 📁 stage2_visibility_filter/   # 階段二：可見性過濾
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   ├── elevation_filter.py
│   │   ├── visibility_calculator.py
│   │   ├── validator.py
│   │   └── config.py
│   ├── 
│   ├── 📁 stage3_timeseries_preprocessing/ # 階段三：時間序列預處理
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   ├── timeseries_cleaner.py
│   │   ├── feature_extractor.py
│   │   ├── validator.py
│   │   └── config.py
│   ├── 
│   ├── 📁 stage4_signal_analysis/     # 階段四：信號分析
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   ├── rsrp_calculator.py
│   │   ├── signal_quality_analyzer.py
│   │   ├── validator.py
│   │   └── config.py
│   ├── 
│   ├── 📁 stage5_data_integration/    # 階段五：數據整合
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   ├── data_merger.py
│   │   ├── consistency_checker.py
│   │   ├── validator.py
│   │   └── config.py
│   └── 
│   └── 📁 stage6_dynamic_planning/    # 階段六：動態規劃
│       ├── __init__.py
│       ├── processor.py
│       ├── pool_optimizer.py
│       ├── handover_planner.py
│       ├── validator.py
│       └── config.py
├── 
├── 📁 utils/                          # 工具函數
│   ├── __init__.py
│   ├── file_helpers.py
│   ├── time_helpers.py
│   ├── math_helpers.py
│   └── logging_helpers.py
├── 
├── 📁 tests/                          # 測試
│   ├── __init__.py
│   ├── test_shared/
│   ├── test_stages/
│   │   ├── test_stage1/
│   │   ├── test_stage2/
│   │   └── ...
│   └── integration/
└── 
└── 📁 scripts/                        # 執行腳本
    ├── __init__.py
    ├── run_pipeline.py                # 主執行腳本
    ├── run_single_stage.py           # 單階段執行
    ├── validate_pipeline.py          # 管道驗證
    └── migration_tools.py            # 遷移工具
```

### 舊架構 vs 新架構對比
```
舊架構 (問題多):
/netstack/src/stages/
├── orbital_calculation_processor.py     (1,833行)
├── satellite_visibility_filter_processor.py (1,731行)
├── timeseries_preprocessing_processor.py    (1,646行)
├── signal_analysis_processor.py             (1,862行)
├── data_integration_processor.py            (3,400行) ❌
└── dynamic_pool_planner.py                  (2,662行) ❌

新架構 (清晰模組化):
/netstack/src/pipeline/stages/stage1_orbital_calculation/
├── processor.py                        (~200行)
├── tle_data_loader.py                  (~300行)
├── orbital_calculator.py               (~400行)
├── validator.py                        (~300行)
└── output_handler.py                   (~100行)
```

## ⏱️ 實施時間線

### Phase 1: 基礎架構 (1-2週)
1. 創建新目錄結構
2. 實施 shared 模組 (base_processor, stage_interface)
3. 建立測試框架
4. 編寫遷移工具

### Phase 2: Stage 1 重構 (1週) - 作為範本
1. 拆分 `orbital_calculation_processor.py`
2. 實施新接口
3. 單元測試
4. 集成測試

### Phase 3: 其他階段重構 (3-4週)
1. Stage 5 (最高優先級，3,400行)
2. Stage 6 (高優先級，2,662行)
3. Stage 4 (1,862行)
4. Stage 2-3 (1,600-1,700行)

### Phase 4: 整合優化 (1週)
1. 性能測試
2. 文檔完善
3. 舊代碼清理

**總計時間: 6-8週**

## 🚨 風險評估

### 高風險
- **系統中斷**: 重構期間可能影響生產環境
- **功能回歸**: 重構可能引入新bug
- **依賴破壞**: 其他模組依賴舊接口

### 風險緩解策略
1. **分階段實施**: 一次只重構一個階段
2. **向後兼容**: 保持舊接口可用，逐步遷移
3. **完整測試**: 每個階段都有單元測試和集成測試
4. **回退計劃**: 每個階段都可快速回退到舊版本

## 📋 實施檢查清單

### 準備階段 ✅
- [ ] 創建重構文檔
- [ ] 設計新架構
- [ ] 建立測試環境
- [ ] 備份現有代碼

### Phase 1: 基礎架構 
- [ ] 創建目錄結構
- [ ] 實施基礎類和接口
- [ ] 建立測試框架
- [ ] 驗證架構可行性

### Phase 2: Stage 1 重構
- [ ] 分析現有 Stage 1 功能
- [ ] 拆分為小模組
- [ ] 實施新接口
- [ ] 編寫單元測試
- [ ] 集成測試通過

### Phase 3-6: 其他階段
- [ ] Stage 5 重構
- [ ] Stage 6 重構  
- [ ] Stage 4 重構
- [ ] Stage 2-3 重構

### 完成階段
- [ ] 性能驗證
- [ ] 文檔更新
- [ ] 舊代碼清理
- [ ] 部署到生產環境

## 📚 相關文檔

- [架構設計詳細說明](./architecture_design.md)
- [統一接口規範](./interface_specification.md) 
- [實施詳細步驟](./implementation_steps.md)
- [測試策略](./testing_strategy.md)
- [風險管理計劃](./risk_management.md)

---

**重要提醒**: 這是一個大型重構項目，需要仔細規劃和執行。建議在開始前與團隊充分討論，確保所有人理解變更影響。