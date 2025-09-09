# 📚 NTN Stack 技術文檔中心

**版本**: 4.3.0 (Phase 3+ 驗證框架整合版)  
**更新日期**: 2025-09-09  
**專案狀態**: ✅ 生產就緒 + Phase 3+ 驗證框架 + 學術標準執行 + 可配置驗證級別

## 🚀 快速開始

### 🚨 極重要提醒：TLE數據時間基準
**衛星渲染必須使用TLE文件日期作為時間基準**
- ✅ **正確**：使用 TLE 文件日期 (如: `starlink_20250816.tle` → 時間基準: 2025-08-16)
- ❌ **錯誤**：使用當前系統時間、處理時間戳或前端即時時間
- ⚠️ **影響**：錯誤的時間基準會造成數百公里的位置偏差，影響所有衛星相關計算

### 🎯 新用戶導航
- **想了解系統架構？** → [系統架構總覽](./system_architecture.md)
- **想了解數據處理流程？** → [數據處理流程](./data_processing_flow.md)
- **需要技術實現細節？** → [技術實施指南](./technical_guide.md)
- **查看API文檔？** → [API參考手冊](./api_reference.md)

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
| [驗證框架總覽](./validation_framework_overview.md) | 🛡️ **NEW**: 六階段驗證框架、學術標準執行 | 數據工程師、研究人員 |
| [驗證框架快速指南](./validation_quick_guide.md) | ⚡ **NEW**: 5分鐘上手驗證框架 | 所有開發者 |
| [管道自動驗證架構](./PIPELINE_AUTO_VALIDATION_ARCHITECTURE.md) | ⭐ **NEW**: Fail-Fast自動驗證、階段品質控制 | 數據工程師、系統架構師 |
| [即時驗證架構](./IMMEDIATE_VALIDATION_ARCHITECTURE.md) | 階段即時驗證、防無意義計算 | 數據工程師、系統架構師 |
| [建構驗證指南](./BUILD_VALIDATION_GUIDE.md) | 建構時自動狀態檢查、三格式報告 | DevOps、系統維護 |
| [統一日誌管理指南](./UNIFIED_LOG_MANAGEMENT_GUIDE.md) | ⭐ **NEW**: 統一日誌輸出、自動清理、TLE來源追蹤 | 所有用戶、運維人員 |
| [Shared Core 統一架構](./shared_core_architecture.md) | 統一管理器、性能優化、避免重複 | 後端工程師、架構師 |
| [數據處理流程](./data_processing_flow.md) | 六階段處理流程、Pure Cron架構 + 自動驗證 | 數據工程師、研究人員 |
| [UltraThink 系統狀態](./ultrathink_system_status.md) | 當前專案狀況、修復成果、開發指導 | 所有開發者、維護人員 |

### 🔧 技術實現文檔  
| 文檔 | 用途 | 讀者對象 |
|------|------|----------|
| [算法實現手冊](./algorithms_implementation.md) | 3GPP標準、SGP4算法、換手邏輯 | 算法工程師、研究人員 |
| [技術實施指南](./technical_guide.md) | 部署配置、開發環境、故障排除 | 後端開發者、運維 |

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
3. [技術實施指南](./technical_guide.md) - 開發環境配置  
4. [API參考手冊](./api_reference.md) - 熟悉接口設計

### 🔬 **研究人員** (3-5天)  
1. [衛星換手標準](./satellite_handover_standards.md) - 3GPP標準理解
2. [算法實現手冊](./algorithms_implementation.md) - 算法細節
3. [數據處理流程](./data_processing_flow.md) - 數據來源和處理
4. [Stage 3 信號分析](./stages/stage3-signal.md) - A4/A5/D2事件實現

### 🏗️ **系統運維** (1-2天)
1. [系統架構總覽](./system_architecture.md) - Docker配置理解
2. [技術實施指南](./technical_guide.md) - 部署和維護
3. [API參考手冊](./api_reference.md) - 監控端點

---

**🚀 開始探索 NTN Stack！** 選擇適合你角色的文檔開始學習，或直接查看 [系統架構總覽](./system_architecture.md) 獲得全局理解。

*最後更新：2025-08-20 | UltraThink 全面修復版本 3.3.0*