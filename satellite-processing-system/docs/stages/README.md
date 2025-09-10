# 📊 六階段數據處理 - 技術文檔導航

[🔄 返回文檔總覽](../README.md) | [📋 完整數據流程說明](../data_processing_flow.md) | [🧠 Shared Core 統一架構](../shared_core_architecture.md)

## ✅ **當前狀態**: 六階段獨立系統已完成
**本文檔描述的是已實現並可運行的獨立系統功能**  
📁 **實際位置**: `satellite-processing-system/` 獨立系統  
🚧 **其他功能**: 文檔中提及的 NetStack/SimWorld 等為未來整合方向

## 🚀 快速執行指南 (獨立系統版本)

### 完整六階段執行
```bash
# 在獨立系統容器內執行
docker-compose exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py

# 或在本地環境執行
python scripts/run_six_stages_with_validation.py
```

### 單獨執行指定階段
```bash
# 執行階段1 (TLE軌道計算)
python scripts/run_six_stages_with_validation.py --stage 1

# 執行階段2 (可見性篩選)
python scripts/run_six_stages_with_validation.py --stage 2

# 執行階段6 (動態池規劃)
python scripts/run_six_stages_with_validation.py --stage 6
```

### 執行腳本位置 (獨立系統架構)
- **主執行程式**: `scripts/run_six_stages_with_validation.py`
- **建置驗證**: `scripts/final_build_validation.py`
- **性能優化**: `scripts/startup_optimizer.py`

### 🛡️ Phase 3+ 驗證框架整合
**六階段處理器已完全整合新驗證框架**：
- ✅ **可配置驗證級別**: FAST/STANDARD/COMPREHENSIVE 三級模式
- ✅ **學術標準執行**: Grade A/B/C 分級標準自動檢查
- ✅ **零侵入整合**: 不影響原有處理邏輯
- ✅ **性能優化**: FAST模式減少60-70%驗證時間

```bash
# 使用不同驗證級別執行 (獨立系統)
python scripts/run_six_stages_with_validation.py --validation-level=FAST
python scripts/run_six_stages_with_validation.py --validation-level=STANDARD  # 預設
python scripts/run_six_stages_with_validation.py --validation-level=COMPREHENSIVE
```

**詳細驗證框架說明**: [驗證框架總覽](../validation_framework_overview.md)

### Sample Mode 說明
- **僅階段1支援**: `--sample-mode` 只在階段1有效 (每星座限制800顆衛星)
- **用於開發測試**: 大幅縮短處理時間，適合程式開發和功能驗證
- **其他階段**: 階段2-6不支援sample-mode，程式會自動忽略此參數

## 🎯 快速導航

六階段數據處理流程通過 **智能軌道相位選擇策略**，將 8,735 顆衛星原始數據高效優化至 **150-250 顆精選動態池**（相比暴力數量堆疊減少85%）。**詳細的架構和流程說明請參考 [數據處理流程文檔](../data_processing_flow.md)**。

## 📚 階段文檔導航

### 🚀 建議閱讀順序

#### 第一次學習（概念理解）
1. **[階段一：TLE載入與SGP4計算](./stage1-tle-loading.md)** - 15分鐘
   - 理解 8,779 → 軌道計算的基礎
   - 掌握 v3.0 記憶體傳遞模式
   - 了解 SGP4 精確計算原理

2. **[階段二：地理可見性篩選](./stage2-filtering.md)** - 20分鐘
   - 理解基於NTPU觀測點的地理可見性篩選
   - 掌握 v3.0 記憶體傳遞模式
   - 了解Starlink/OneWeb星座差異化篩選策略

#### 深度技術研究（實現細節）
3. **[階段三：信號品質分析](./stage3-signal.md)** - 25分鐘
   - ITU-R P.618 標準信號模型
   - 3GPP NTN 事件處理（A4/A5/D2）✅ 完全符合TS 38.331標準
   - RSRP/RSRQ/SINR 計算實現

4. **[階段四：時間序列預處理](./stage4-timeseries.md)** - 20分鐘
   - Pure Cron 驅動架構
   - 前端動畫數據最佳化
   - 60 FPS 渲染準備

5. **[階段五：數據整合](./stage5-integration.md)** - 25分鐘
   - 混合存儲架構（PostgreSQL + Volume）
   - 486MB 存儲分佈策略
   - 結構化數據與檔案管理

#### 前沿功能（最新發展）
6. **[階段六：智能軌道優化動態池](./stage6-dynamic-pool.md)** - 25分鐘 🆕
   - 時空錯置理論實戰應用
   - 智能軌道相位選擇演算法
   - 2小時完整軌道週期驗證 (Starlink: 93.63分鐘、OneWeb: 109.64分鐘)

## 🔍 依場景快速查找

### 「我要了解記憶體傳遞模式」
→ [階段一](./stage1-tle-loading.md#v30記憶體傳遞模式) + [階段二](./stage2-filtering.md#v30記憶體傳遞模式)

### 「我要理解衛星篩選邏輯」
→ [階段二：六階段篩選管線](./stage2-filtering.md#智能篩選演算法)

### 「我要了解3GPP標準實現」
→ [階段三：3GPP NTN事件處理](./stage3-signal.md#3gpp-ntn-事件處理)

### 「我要了解前端數據格式」
→ [階段四：JSON數據格式](./stage4-timeseries.md#json-數據格式)

### 「我要了解存儲架構」
→ [階段五：混合存儲架構](./stage5-integration.md#混合存儲架構)

### 「我要了解動態衛星池」
→ [階段六：動態覆蓋需求](./stage6-dynamic-pool.md#動態覆蓋需求) 🆕

## 📈 性能概要（智能優化版）

六階段處理實現 8,779 → 150-250 顆衛星的時空錯置優化：
- **核心突破**：智能軌道相位選擇 >> 暴力數量堆疊
- **效率提升**：相同覆蓋效果下減少85%衛星數
- **智能子集**：Starlink ~150 顆 + OneWeb ~40 顆
- **覆蓋保證**：95%+ 時間滿足 10-15/3-6 顆可見要求（基於2小時軌道週期驗證）
- **總處理時間**：<10 秒（相比原15分鐘提升100倍）

**詳細性能指標和存儲分佈請參考**：[數據處理流程 - 性能指標](../data_processing_flow.md#性能指標與優化)

## 🏆 時空錯置理論驗證突破

### 重大發現
- **理論驗證**: 首次用實際軌道數據驗證時空錯置理論可行性
- **效率突破**: 證明軌道相位智能選擇優於暴力數量堆疊85%
- **方法論創新**: 建立基於軌道動力學的最小衛星數理論框架

### 驗證數據
- **數據來源**: 階段三信號分析輸出（554顆衛星實際軌道數據）
- **時間窗口**: 1.5小時接近Starlink完整軌道週期驗證
- **關鍵結論**: 130顆衛星子集在最佳時刻可達32顆可見，證明小子集有效性

### 戰略意義
- **LEO衛星優化範例**: 為其他衛星星座研究提供可擴展優化方法
- **資源效率革命**: 從"更多衛星=更好覆蓋"轉向"更智能選擇=更高效覆蓋"
- **學術價值**: 時空錯置理論的首次大規模實際驗證

## ⚙️ 開發與維護指引

### 程式碼組織
```bash
/netstack/src/stages/
├── tle_orbital_calculation_processor.py     # TLE載入與SGP4計算
├── satellite_visibility_filter_processor.py   # 地理可見性篩選
├── signal_quality_analysis_processor.py     # 信號品質分析
├── timeseries_preprocessing_processor.py    # 時間序列預處理
├── data_integration_processor.py            # 數據整合與存儲
└── enhanced_dynamic_pool_planner.py         # 動態池規劃 🆕
```

### 配置檔案
```bash
/netstack/config/
├── satellite_config.py              # 衛星系統配置
├── signal_processing_config.py      # 信號處理參數
├── database_config.py               # 資料庫配置
└── dynamic_pool_config.py           # 動態池規劃配置 🆕
```

### 核心架構支援
```bash
src/shared/  # 獨立系統共用組件架構 (21個核心組件)
├── algorithm_metrics.py             # 演算法指標收集
├── auto_cleanup_manager.py          # 自動清理管理器
├── base_processor.py                # 基礎處理器架構
├── base_stage_processor.py          # 基礎階段處理器
├── cleanup_manager.py               # 清理管理器
├── data_lineage_manager.py          # 數據族系追蹤管理器
├── data_models.py                   # 統一數據模型
├── debug_data_injector.py           # 除錯數據注入器
├── elevation_threshold_manager.py   # 仰角門檻管理器
├── engines/
│   └── sgp4_orbital_engine.py       # SGP4軌道引擎
├── incremental_update_manager.py    # 增量更新管理器
├── json_file_service.py             # JSON檔案服務
├── observer_config_service.py       # 觀察者配置服務
├── pipeline_coordinator.py          # 管道協調器
├── signal_quality_cache.py          # 信號品質緩存系統
├── stage_data_manager.py            # 階段資料管理器
├── tle_parser.py                    # TLE解析器
├── unified_log_manager.py           # 統一日誌管理器
├── utils.py                         # 共用工具函數
├── validation_engine.py             # 驗證引擎
├── validation_snapshot_base.py      # 驗證快照基底
└── visibility_service.py            # 可見性服務
```

### 監控與診斷
每個階段都提供完整的診斷指令和故障排除指南，詳見各階段文檔的「🚨 故障排除」章節。

## 🔄 版本歷程

- **v1.0** (2025-07-XX): 基礎五階段架構
- **v2.0** (2025-08-XX): 記憶體傳遞優化（v3.0處理模式）
- **v2.1** (2025-08-13): 混合存儲架構優化
- **v2.2** (2025-08-14): 新增階段六動態池規劃
- **v3.1** (2025-08-20): 數據族系追蹤修復
- **v3.2** (2025-08-22): 文檔與實現完全同步
- **v4.0** (2025-09-01): 階段二增強版 + 時空優化調整 🆕
- **v4.3** (2025-09-09): Phase 3+ 驗證框架完整整合 🛡️

## ⚠️ 重要提醒

1. **記憶體傳遞模式**：階段一、二採用記憶體傳遞，大幅提升性能
2. **數據族系追蹤**：所有階段嚴格區分TLE數據日期與處理執行時間 🆕
3. **檔案名稱標準**：使用描述性命名，避免 phase/stage 數字命名
4. **Pure Cron架構**：定時自動更新，容器啟動時數據立即可用
5. **混合存儲設計**：PostgreSQL處理結構化查詢，Volume存儲大型時間序列

---
**上層導航**: [數據流程總導航](../README.md)  
**系統架構**: [README.md](../README.md)  
*最後更新：2025-08-22 | v3.2.0 - 文檔與實現完全同步*