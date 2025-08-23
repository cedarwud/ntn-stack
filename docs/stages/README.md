# 📊 六階段數據處理 - 技術文檔導航

[🔄 返回文檔總覽](../README.md) | [📋 完整數據流程說明](../data_processing_flow.md) | [🧠 Shared Core 統一架構](../shared_core_architecture.md)

## 🎯 快速導航

六階段數據處理流程將 8,735 顆衛星原始數據逐步優化至研究可用的動態衛星池。**詳細的架構和流程說明請參考 [數據處理流程文檔](../data_processing_flow.md)**。

## 📚 階段文檔導航

### 🚀 建議閱讀順序

#### 第一次學習（概念理解）
1. **[階段一：TLE載入與SGP4計算](./stage1-tle-loading.md)** - 15分鐘
   - 理解 8,735 → 軌道計算的基礎
   - 掌握 v3.0 記憶體傳遞模式
   - 了解 SGP4 精確計算原理

2. **[階段二：智能衛星篩選](./stage2-filtering.md)** - 20分鐘
   - 理解 8,735 → 563 的 93.6% 篩選率
   - 掌握六階段篩選管線
   - 了解星座負載平衡策略

#### 深度技術研究（實現細節）
3. **[階段三：信號品質分析](./stage3-signal.md)** - 25分鐘
   - ITU-R P.618 標準信號模型
   - 3GPP NTN 事件處理（A4/A5/D2）
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
6. **[階段六：動態池規劃](./stage6-dynamic-pool.md)** - 25分鐘 🆕
   - 動態衛星池規劃演算法
   - 時空分散策略設計
   - 立體圖整軌道週期覆蓋

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

## 📈 性能概要

六階段處理實現 8,735 → 390+ 顆衛星的智能篩選，總處理時間 10-15 分鐘。

**詳細性能指標和存儲分佈請參考**：[數據處理流程 - 性能指標](../data_processing_flow.md#性能指標與優化)

## ⚙️ 開發與維護指引

### 程式碼組織
```bash
/netstack/src/stages/
├── tle_orbital_calculation_processor.py     # TLE載入與SGP4計算
├── intelligent_satellite_filter_processor.py  # 智能衛星篩選
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
/netstack/src/shared_core/
├── data_lineage_manager.py          # 數據族系追蹤管理器 🆕
├── auto_cleanup_manager.py          # 自動清理管理器
├── elevation_threshold_manager.py   # 仰角門檻管理器
├── observer_config_service.py       # 觀察者配置服務
├── signal_quality_cache.py          # 信號品質緩存系統
└── utils.py                         # 共用工具函數
```

### 監控與診斷
每個階段都提供完整的診斷指令和故障排除指南，詳見各階段文檔的「🚨 故障排除」章節。

## 🔄 版本歷程

- **v1.0** (2025-07-XX): 基礎五階段架構
- **v2.0** (2025-08-XX): 記憶體傳遞優化（v3.0處理模式）
- **v2.1** (2025-08-13): 混合存儲架構優化
- **v2.2** (2025-08-14): 新增階段六動態池規劃 🆕
- **v3.1** (2025-08-20): 數據族系追蹤修復 🆕
- **v3.2** (2025-08-22): 文檔與實現完全同步 🆕

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