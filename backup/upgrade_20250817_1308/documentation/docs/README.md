# 📚 NTN Stack 技術文檔中心

## 🚀 快速開始
- **想了解數據流程？** → [數據處理流程總覽](./data-flow-index.md)
- **想查看API？** → [API參考](./api_reference.md)
- **想了解架構？** → [系統架構](./system_architecture.md)

## 📊 數據處理流程文檔

### 從這裡開始閱讀數據流：
1. **總體導航** → [data-flow-index.md](./data-flow-index.md)
   - 完整閱讀指南
   - 場景快速查找
   - 階段概覽

2. **架構概述** → [overviews/data-processing-flow.md](./overviews/data-processing-flow.md) 
   - 六階段架構總覽
   - Pure Cron驅動機制
   - 性能指標

3. **階段實現** → [stages/](./stages/)
   - [階段一：TLE載入](./stages/stage1-tle-loading.md)
   - [階段二：智能篩選](./stages/stage2-filtering.md)
   - [階段三：信號分析](./stages/stage3-signal.md)
   - [階段四：時間序列](./stages/stage4-timeseries.md)
   - [階段五：數據整合](./stages/stage5-integration.md)
   - [階段六：動態池規劃](./stages/stage6-dynamic-pool.md) 🆕

## 🏗️ 系統架構文檔
- [系統架構](./system_architecture.md) - Docker容器配置
- [標準實現](./standards_implementation.md) - 3GPP/ITU-R標準
- [演算法實現](./algorithms_implementation.md) - SGP4/換手演算法

## 🛰️ 衛星專業文檔
- [衛星星座分析](./satellite_constellation_analysis.md)
- [衛星換手標準](./satellite_handover_standards.md) ⭐ 重要

## 📖 技術指南
- [技術指南](./technical_guide.md) - 開發指引
- [API參考](./api_reference.md) - 端點說明

---
*最後更新：2025-08-14 | v2.2.0*