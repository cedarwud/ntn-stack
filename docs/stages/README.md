# 📊 數據處理階段 - 技術實現文檔

[🔄 返回數據流程導航](../README.md)

## 🎯 六階段處理架構總覽

NTN Stack 採用精密設計的六階段數據處理流程，從 8,735 顆衛星原始數據逐步優化至立體圖可用的動態衛星池。

### 📊 處理流程概要
```
階段一      階段二      階段三      階段四      階段五      階段六
TLE載入 →  智能篩選 →  信號分析 →  時間序列 →  數據整合 →  動態池規劃
8,735顆    563顆      563顆      563顆      混合存儲    衛星池規劃

記憶體傳遞  記憶體傳遞  檔案輸出    檔案最佳化  PostgreSQL   立體圖用池
(避免2.2GB) (避免2.4GB) (~295MB)   (~100MB)    + Volume    (45+20顆*)
```
*數字為估算值，待實際開發驗證

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

## 📈 關鍵技術指標總覽

### 處理性能
- **總處理時間**：10-15 分鐘（六個階段）
- **數據縮減率**：8,735 → 563 顆（93.6% 篩選）
- **存儲最佳化**：原始 2.2GB → 最終 486MB（78% 壓縮）
- **記憶體效率**：階段一、二記憶體傳遞，避免大檔案 I/O

### 數據品質
- **SGP4精度**：位置誤差 < 1km（LEO軌道）
- **信號計算**：ITU-R P.618 標準模型
- **事件檢測**：3GPP NTN A4/A5/D2 完整實現
- **動畫流暢度**：60 FPS，360點最佳化軌跡

### 存儲分佈
```
PostgreSQL (86MB):
├── satellite_metadata: 2MB (563顆基本資訊)
├── signal_statistics: 35MB (信號統計數據)
├── handover_events: 25MB (~2,600個事件)
├── indexes_overhead: 12MB (索引優化)
└── system_metadata: 12MB (系統開銷)

Docker Volume (400MB):
├── enhanced_timeseries: 100MB (前端動畫)
├── layered_phase0: 120MB (分層處理結果)
├── handover_scenarios: 80MB (換手場景)
├── signal_analysis: 90MB (信號分析)
└── cache_files: 10MB (緩存數據)
```

## ⚙️ 開發與維護指引

### 程式碼組織
```bash
/netstack/src/stages/
├── stage1_tle_processor.py           # TLE載入與SGP4計算
├── stage2_filtering_processor.py     # 智能衛星篩選
├── stage3_signal_processor.py        # 信號品質分析
├── stage4_timeseries_processor.py    # 時間序列預處理
├── stage5_integration_processor.py   # 數據整合與存儲
└── stage6_dynamic_pool_planner.py    # 動態池規劃 🆕
```

### 配置檔案
```bash
/netstack/config/
├── satellite_config.py              # 衛星系統配置
├── signal_processing_config.py      # 信號處理參數
├── database_config.py               # 資料庫配置
└── dynamic_pool_config.py           # 動態池規劃配置 🆕
```

### 監控與診斷
每個階段都提供完整的診斷指令和故障排除指南，詳見各階段文檔的「🚨 故障排除」章節。

## 🔄 版本歷程

- **v1.0** (2025-07-XX): 基礎五階段架構
- **v2.0** (2025-08-XX): 記憶體傳遞優化（v3.0處理模式）
- **v2.1** (2025-08-13): 混合存儲架構優化
- **v2.2** (2025-08-14): 新增階段六動態池規劃 🆕

## ⚠️ 重要提醒

1. **記憶體傳遞模式**：階段一、二採用記憶體傳遞，大幅提升性能
2. **數字估算說明**：階段六的衛星池大小（45+20顆）為估算值，需實際開發驗證
3. **Pure Cron架構**：定時自動更新，容器啟動時數據立即可用
4. **混合存儲設計**：PostgreSQL處理結構化查詢，Volume存儲大型時間序列

---
**上層導航**: [數據流程總導航](../README.md)  
**系統架構**: [README.md](../README.md)  
*最後更新：2025-08-14 | v2.2.0*