# 📚 衛星處理系統 - 技術文檔導航中心

**版本**: 6.1.0 (Phase 3部分完成 + 發現重大架構問題)
**更新日期**: 2025-09-18
**專案狀態**: 🚨 **緊急重構需求** - 發現14個超大檔案需拆分 + 71%功能邊界違規 + Phase 4-6緊急重構計劃

## 📋 系統開發狀態說明

### 🚨 **重大發現 - 系統性過度開發問題 (v6.1現況)**
**當前真實狀況評估**:
- **⚠️ 重構僅5%完成**: 之前聲稱的「重構完成」不正確
- **🚨 14個超大檔案**: >1000行，嚴重違反模組化原則
- **📊 Stage 6最嚴重**: 5,821行，71%功能違規 (104/145方法)
- **🔄 跨階段功能混雜**: 數百個方法放錯Stage
- **📚 文檔與實際脫節**: 文檔描述與代碼實現嚴重不符

### ✅ **僅完成的微量工作 (Phase 1-3)**
**實際已完成功能**:
- **📡 Stage 1**: 移除6個觀測者計算方法 (202行)
- **📶 Stage 3**: 觀測者座標動態載入修復
- **🧹 清理工作**: 部分重複檔案移除
- **🐳 容器環境**: 獨立容器部署可用
- **🔧 執行腳本**: `scripts/run_six_stages_with_validation.py` 可用

### 🚨 **緊急重構計劃 - Phase 4-6 (必須立即執行)**
**解決系統性過度開發問題**:
- **📋 完整重構計劃**: [Phase 4-6緊急重構計劃](./architecture_refactoring/PHASE4_6_EMERGENCY_REFACTORING_PLAN.md) ⚡ **必讀**
- **🎯 Phase 4**: 超大檔案拆分 (2-3天) - 處理14個>1000行檔案
- **🔄 Phase 5**: 跨階段功能重新分配 (2-3天) - 修復數百個功能違規
- **📚 Phase 6**: 文檔同步更新 (1-2天) - 讓文檔反映實際架構
- **⏰ 預估總時程**: 5-8天完成真正的全面重構

### 🚧 **未來開發方向 - 完整NTN系統**
**重構完成後的未來功能**:
- **🌐 NetStack API服務**: `http://localhost:8080` (未來功能)
- **🎮 SimWorld 3D渲染**: 前端可視化系統 (未來功能)
- **📡 完整NTN網路**: 與外部系統整合 (未來功能)
- **🔄 即時服務**: 持續運行的API服務 (未來功能)

## 🚀 快速開始

### 🚨 極重要提醒：TLE數據時間基準
**衛星渲染必須使用TLE文件日期作為時間基準**
- ✅ **正確**：使用 TLE 文件日期 (如: `starlink_20250816.tle` → 時間基準: 2025-08-16)
- ❌ **錯誤**：使用當前系統時間、處理時間戳或前端即時時間
- ⚠️ **影響**：錯誤的時間基準會造成數百公里的位置偏差，影響所有衛星相關計算

### 🎯 新用戶導航
- **🚀 想快速開始使用？** → [📋 完整使用指南](./USAGE_GUIDE.md) ⭐ **推薦**
- **🏗️ 想了解系統架構？** → [🔄 數據處理流程](./data_processing_flow.md)
- **📊 想了解階段詳情？** → [📊 階段技術概覽](./stages/STAGES_OVERVIEW.md)
- **🛡️ 想了解驗證框架？** → [🛡️ 驗證框架總覽](./validation_framework_overview.md)

### ⚡ 開發者快速查詢
```bash
# 服務控制
make up/down/status/logs              # 啟動/停止/狀態/日誌
make simworld-restart                 # 重啟 SimWorld (30秒)
make netstack-restart                 # 重啟 NetStack (1-2分鐘)

# 服務地址
NetStack API    → http://localhost:8080
SimWorld UI     → http://localhost:5173
SimWorld API    → http://localhost:8888

# 健康檢查
curl http://localhost:8080/health     # NetStack 健康檢查

# 📊 統一日誌查看 (NEW!)
# 執行六階段處理
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py

# 查看最新執行結果
ls -la logs/summary/*.txt | tail -1 | awk '{print $9}' | xargs cat
```

## 📖 文檔導航

### 🏗️ 系統架構與配置
| 文檔 | 用途 | 讀者對象 |
|------|------|----------|
| [系統架構總覽](./system_architecture.md) | Docker配置、服務架構、高層設計 | 系統架構師、DevOps |
| [**六階段重構完成報告**](./archives/completed_refactoring_2024/refactoring/six_stages_restructure/COMPLETION_REPORT.md) | 🎉 **歷史**: 模組化重構完成成果、22個專業組件 | 所有團隊成員 |
| [**模組化架構使用指南**](./MODULAR_ARCHITECTURE_GUIDE.md) | 🚀 **NEW**: 新架構使用指南、革命性除錯能力 | 開發者、維護人員 |
| [驗證框架總覽](./validation_framework_overview.md) | 🛡️ **NEW**: 六階段驗證框架、學術標準執行 | 數據工程師、研究人員 |
| [驗證框架快速指南](./validation_quick_guide.md) | ⚡ **NEW**: 5分鐘上手驗證框架 | 所有開發者 |
| [**TDD重構指南**](./TDD_REFACTORING_GUIDE.md) | 🧪 **v6.0**: 重構後TDD測試開發指南 | 開發者、測試工程師 |
| [Shared Core 統一架構](./shared_core_architecture.md) | 統一管理器、性能優化、避免重複 | 後端工程師、架構師 |
| [數據處理流程](./data_processing_flow.md) | 六階段處理流程、Pure Cron架構 + 自動驗證 | 數據工程師、研究人員 |

### 🔧 技術實現文檔
| 文檔 | 用途 | 讀者對象 |
|------|------|----------|
| [算法實現手冊](./algorithms_implementation.md) | 3GPP標準、SGP4算法、換手邏輯 | 算法工程師、研究人員 |
| [技術實施指南](./technical_guide.md) | 部署配置、開發環境、故障排除 | 後端開發者、運維 |
| [**直接計算解決方案**](./DIRECT_CALCULATION_SOLUTION.md) | **🚨 v5.1關鍵修復** - 時間基準錯誤修復、性能優化 | **所有開發者** ⚠️ |

### 🛰️ 專業標準文檔
| 文檔 | 用途 | 讀者對象 |
|------|------|----------|
| [衛星換手標準](./satellite_handover_standards.md) | 3GPP NTN標準、仰角門檻、A4/A5/D2事件 | 通訊工程師、學術研究 |
| [API參考手冊](./api_reference.md) | 端點說明、參數定義、返回格式 | 前端開發者、API用戶 |

### 📊 六階段處理流程詳解
| 階段 | 文檔 | 處理內容 | 技術重點 |
|------|------|----------|----------|
| **Stage 1** | [TLE載入與SGP4計算](./stages/stage1-tle-loading.md) | 8,779顆衛星軌道計算 | SGP4算法、軌道動力學 |
| **Stage 2** | [地理可見性篩選](./stages/stage2-filtering.md) | 地理篩選至1,113顆候選 | 基於NTPU觀測點、星座差異化 |
| **Stage 3** | [信號品質分析](./stages/stage3-signal.md) | 3GPP事件分析 | A4/A5/D2事件、RSRP計算 |
| **Stage 4** | [時間序列預處理](./stages/stage4-timeseries.md) | 前端動畫數據準備 | 1x-60x倍速、60FPS渲染 |
| **Stage 5** | [數據整合處理](./stages/stage5-integration.md) | 跨系統數據整合 | 格式統一、驗證機制 |
| **Stage 6** | [動態池規劃](./stages/stage6-dynamic-pool.md) | 時間序列保留 | 156顆動態池、192點連續數據 |

## 🎯 按場景查找文檔

### 🔬 學術研究場景
**目標**: 進行LEO衛星換手研究、發表論文
- **必讀**: [衛星換手標準](./satellite_handover_standards.md) - 3GPP NTN標準實現
- **參考**: [算法實現手冊](./algorithms_implementation.md) - SGP4、換手算法
- **數據**: [Stage 3 信號分析](./stages/stage3-signal.md) - A4/A5/D2事件

### 🏗️ 系統部署場景  
**目標**: 部署和維護NTN Stack系統
- **必讀**: [系統架構總覽](./system_architecture.md) - Docker配置
- **參考**: [技術實施指南](./technical_guide.md) - 部署配置
- **監控**: [API參考手冊](./api_reference.md) - 健康檢查端點

### 💻 前端開發場景
**目標**: 開發3D衛星視覺化界面
- **必讀**: [API參考手冊](./api_reference.md) - 前端API
- **參考**: [Stage 4 時間序列](./stages/stage4-timeseries.md) - 動畫數據格式
- **數據**: [數據處理流程](./data_processing_flow.md) - 數據結構

### 🔧 算法開發場景
**目標**: 優化換手決策算法、添加新功能
- **必讀**: [算法實現手冊](./algorithms_implementation.md) - 核心算法
- **參考**: [衛星換手標準](./satellite_handover_standards.md) - 標準規範
- **實現**: [Stage 6 動態池規劃](./stages/stage6-dynamic-pool.md) - 時間序列數據保留

## 🔄 系統概覽

### 📊 核心數據流程
```
TLE數據(8,779顆) → SGP4計算 → 智能篩選(1,113顆) → 信號分析 → 時間序列 → 數據整合 → 時間序列保留(156顆)
     Stage1           Stage2        Stage3       Stage4      Stage5      Stage6
```

### 🏗️ 系統架構層次
完整的系統架構設計請參考：**[系統架構總覽](./system_architecture.md)**

### 🛰️ 技術特色
- **完整SGP4軌道計算** - 非簡化算法，符合學術研究標準  
- **3GPP NTN標準合規** - A4/A5/D2事件完整實現
- **Pure Cron驅動架構** - 容器純數據載入，Cron自動更新
- **六階段智能處理** - 從8,779顆到156顆動態池，含完整時間序列數據
- **真實數據驅動** - CelesTrak官方TLE數據，6小時自動更新
- **⚡ Fail-Fast自動驗證** - 每階段完成後立即驗證，失敗時停止後續執行

## 📋 版本信息

| 組件 | 版本 | 狀態 | 說明 |
|------|------|------|------|
| **NetStack** | 3.3.0 | ✅ 穩定 | 15+ 微服務容器 |
| **SimWorld** | 2.1.0 | ✅ 穩定 | 3D視覺化引擎 |
| **文檔系統** | 3.3.0 | ✅ 整合 | 精簡文檔，反映當前專案狀況 |
| **數據處理** | 6-Stage | ✅ 生產 | UltraThink 修復版 - 100% 管線穩定性 |

## 🎓 學習路徑建議

### 👨‍💻 **後端開發者** (2-3天)
1. [系統架構總覽](./system_architecture.md) - 了解整體架構
2. [Shared Core 統一架構](./shared_core_architecture.md) - 掌握統一管理器設計
3. [智能清理策略](./cleanup_strategy.md) - 數據清理和管理機制 🆕
4. [技術實施指南](./technical_guide.md) - 開發環境配置
5. [API參考手冊](./api_reference.md) - 熟悉接口設計

### 🔬 **研究人員** (3-5天)  
1. [衛星換手標準](./satellite_handover_standards.md) - 3GPP標準理解
2. [算法實現手冊](./algorithms_implementation.md) - 算法細節
3. [數據處理流程](./data_processing_flow.md) - 數據來源和處理
4. [Stage 3 信號分析](./stages/stage3-signal.md) - A4/A5/D2事件實現

### 🏗️ **系統運維** (1-2天)
1. [系統架構總覽](./system_architecture.md) - Docker配置理解
2. [技術實施指南](./technical_guide.md) - 部署和維護
3. [智能清理策略](./cleanup_strategy.md) - 數據清理和管理 🆕
4. [API參考手冊](./api_reference.md) - 監控端點

---

**🚀 開始探索 NTN Stack！** 選擇適合你角色的文檔開始學習，或直接查看 [系統架構總覽](./system_architecture.md) 獲得全局理解。

*最後更新：2025-09-10 | 六階段模組化重構完成版本 5.0.0*