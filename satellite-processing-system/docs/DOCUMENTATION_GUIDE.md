# 📚 衛星處理系統文檔導航

這個目錄包含了衛星處理系統的完整技術文檔，涵蓋架構設計、實現細節和使用指南。

## 🚀 快速開始

### 新用戶推薦閱讀順序
1. **[系統總覽](README.md)** - 了解整個系統架構和基本概念
2. **[數據處理流程](data_processing_flow.md)** - 理解六階段處理管道
3. **[學術數據標準](academic_data_standards.md)** - 理解數據質量要求 ⚠️ **強制遵循**
4. **[TLE時間基準](TLE_TIME_REFERENCE.md)** - 理解軌道計算時間規範 ⚠️ **極其重要**

### 開發者深度學習
5. **[驗證框架總覽](validation_framework_overview.md)** - 理解三級驗證體系
6. **[共享核心架構](shared_core_architecture.md)** - 理解模組化設計
7. **[衛星換手標準](satellite_handover_standards.md)** - 理解ITU-R和3GPP標準實現

## 📋 文檔分類

### 🏗️ 系統架構文檔
- **[README.md](README.md)** - 系統總覽、快速部署指南
- **[data_processing_flow.md](data_processing_flow.md)** - 完整的數據流程說明
- **[shared_core_architecture.md](shared_core_architecture.md)** - 模組化設計詳解
- **[validation_framework_overview.md](validation_framework_overview.md)** - Phase 3+ 驗證框架

### 📏 標準和規範文檔
- **[academic_data_standards.md](academic_data_standards.md)** 🚨 **強制遵循**
  - Grade A/B/C 分級標準
  - 禁止使用模擬數據
  - 學術級質量要求

- **[TLE_TIME_REFERENCE.md](TLE_TIME_REFERENCE.md)** 🚨 **極其重要**
  - SGP4軌道計算時間基準
  - 防止使用錯誤時間導致8000→0顆衛星問題
  - 強制使用TLE epoch時間

- **[satellite_handover_standards.md](satellite_handover_standards.md)**
  - ITU-R P.618 信號模型
  - 3GPP NTN 標準實現
  - 分層仰角門檻設計

## 📊 六階段處理文檔

### 🎯 階段文檔總導航
**[stages/README.md](stages/README.md)** - 六階段處理完整導航和快速執行指南

### 各階段詳細文檔
1. **[階段一：TLE載入與SGP4計算](stages/stage1-tle-loading.md)**
   - 8,779顆衛星軌道計算
   - v3.0記憶體傳遞模式
   - SGP4精確計算引擎

2. **[階段二：地理可見性篩選](stages/stage2-filtering.md)**
   - 基於NTPU觀測點篩選
   - 星座差異化策略
   - 智能篩選演算法

3. **[階段三：信號品質分析](stages/stage3-signal.md)**
   - ITU-R P.618標準模型
   - 3GPP NTN事件處理（A4/A5/D2）
   - RSRP/RSRQ/SINR計算

4. **[階段四：時間序列預處理](stages/stage4-timeseries.md)**
   - Pure Cron驅動架構
   - 60 FPS渲染準備
   - 前端動畫數據優化

5. **[階段五：數據整合](stages/stage5-integration.md)**
   - 混合存儲架構（PostgreSQL + Volume）
   - 486MB存儲分佈策略
   - 結構化數據管理

6. **[階段六：智能軌道優化動態池](stages/stage6-dynamic-pool.md)** 🆕
   - 時空錯置理論實戰
   - 8,735→150-250顆智能優化
   - 2小時完整軌道週期驗證

## 🔍 按使用場景查找文檔

### 「我要部署系統」
→ [README.md](README.md) + [data_processing_flow.md](data_processing_flow.md)

### 「我要理解數據品質要求」
→ [academic_data_standards.md](academic_data_standards.md) 🚨 **必讀**

### 「我遇到軌道計算問題」
→ [TLE_TIME_REFERENCE.md](TLE_TIME_REFERENCE.md) 🚨 **必讀**

### 「我要了解驗證框架」
→ [validation_framework_overview.md](validation_framework_overview.md)

### 「我要了解六階段處理細節」
→ [stages/README.md](stages/README.md) → 各階段文檔

### 「我要理解3GPP標準實現」
→ [stages/stage3-signal.md](stages/stage3-signal.md#3gpp-ntn-事件處理)

### 「我要了解動態衛星池」
→ [stages/stage6-dynamic-pool.md](stages/stage6-dynamic-pool.md) 🆕

## ⚠️ 關鍵提醒

### 🚨 強制遵循原則
1. **數據真實性原則**: 絕對禁止使用模擬數據、假設值、簡化算法
2. **時間基準原則**: SGP4計算必須使用TLE epoch時間，不得使用當前時間
3. **學術標準原則**: 所有實現必須達到Grade A標準，可通過同行評審

### 🛡️ 質量保證
- 所有算法基於官方標準（ITU-R、3GPP、IEEE）
- 使用真實數據源（Space-Track.org、官方API）
- 完整驗證框架確保學術級質量

### 📈 性能指標
- **六階段處理時間**: <10秒（相比原15分鐘提升100倍）
- **衛星優化效率**: 8,735→150-250顆（減少85%）
- **覆蓋保證**: 95%+時間滿足10-15/3-6顆可見要求
- **時空錯置驗證**: 基於2小時完整軌道週期

## 📝 文檔維護

### 版本同步
- 所有文檔與實現完全同步
- 版本更新時同時更新文檔
- 確保文檔的準確性和時效性

### 更新頻率
- 核心架構文檔: 跟隨系統版本更新
- 階段文檔: 跟隨實現變更即時更新
- 標準文檔: 保持與最新標準同步

---
**📋 快速參考**: [系統README](README.md) | [數據流程](data_processing_flow.md) | [學術標準](academic_data_standards.md) | [TLE時間](TLE_TIME_REFERENCE.md)

*最後更新：2025-09-10 | v4.3+ - 完整模組化架構*