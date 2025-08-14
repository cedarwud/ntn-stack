# 🔄 數據處理流程 - 完整導航

> **回到總覽**：[README.md](./README.md)

## 📖 閱讀順序指南

### 第一次閱讀（理解概念）
1. [數據處理流程概述](./overviews/data-processing-flow.md#整體架構) - 10分鐘
2. [六階段處理架構](./overviews/data-processing-flow.md#處理階段概述) - 15分鐘

### 深入了解（技術細節）
1. [階段一：TLE載入](./stages/stage1-tle-loading.md) - 20分鐘
2. [階段二：智能篩選](./stages/stage2-filtering.md) - 25分鐘
3. [階段三：信號分析](./stages/stage3-signal.md) - 30分鐘
4. [階段四：時間序列](./stages/stage4-timeseries.md) - 20分鐘
5. [階段五：數據整合](./stages/stage5-integration.md) - 25分鐘
6. [階段六：動態池規劃](./stages/stage6-dynamic-pool.md) - 25分鐘 🆕

### 實作參考（程式碼位置）
- 主控制器：`/netstack/docker/satellite_orbit_preprocessor.py`
- 階段處理器：`/netstack/src/stages/`
- 配置檔案：`/netstack/config/satellite_config.py`

## 🎯 依場景查找

### 「我要了解記憶體傳遞模式」
→ [v3.0記憶體傳遞策略](./stages/stage1-tle-loading.md#記憶體傳遞實現)

### 「我要了解Pure Cron機制」
→ [Pure Cron驅動架構](./overviews/data-processing-flow.md#pure-cron驅動架構)

### 「我要查看性能指標」
→ [系統性能指標](./overviews/data-processing-flow.md#系統性能指標)

### 「我要了解動態衛星池規劃」
→ [階段六：動態衛星池規劃](./stages/stage6-dynamic-pool.md) 🆕

### 「我要排除故障」
→ [維護與故障排除](./stages/stage5-integration.md#維護與故障排除)

## ⚠️ 重要提醒

- **階段六數字僅為估計**：Starlink 45顆、OneWeb 20顆為初步估算，實際數字需開發驗證
- **記憶體傳遞模式**：階段一、二採用記憶體傳遞避免大檔案問題
- **文檔版本**：v2.2.0，支援六階段架構

---
*最後更新：2025-08-14*
