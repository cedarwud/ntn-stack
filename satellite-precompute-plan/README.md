# 真實衛星歷史數據預計算方案

## 📋 開發計畫概述

**核心理念**：使用真實 TLE 歷史數據 + 預計算存儲 + 時間軸播放，解決即時計算性能問題，同時保持數據真實性。

### ✅ 方案優勢
- **真實性保證**：使用真實 Starlink TLE 數據，非模擬數據
- **性能優化**：預計算避免即時 SGP4 運算瓶頸
- **展示友好**：支援時間軸控制、加速播放、handover 動畫
- **研究價值**：可用於 3GPP events 計算和論文分析
- **穩定性**：不依賴網路即時連接

## 📚 檔案結構與開發順序

### 🎯 開發階段文檔（按順序執行）

 < /dev/null |  階段 | 檔案名稱 | 說明 | 預估時間 |
|------|----------|------|----------|
| **方案總覽** | [`01-project-overview.md`](./01-project-overview.md) | 技術參數建議、多星座支援設計 | 參考 |
| **Phase 1** | [`02-phase1-database-setup.md`](./02-phase1-database-setup.md) | PostgreSQL 歷史數據表設計、容器內預載數據機制 | 1-2 天 |
| **Phase 2** | [`03-phase2-precompute-engine.md`](./03-phase2-precompute-engine.md) | 歷史數據預計算器、批次處理和存儲 | 2-3 天 |  
| **Phase 3** | [`04-phase3-api-endpoints.md`](./04-phase3-api-endpoints.md) | 時間軸查詢 API、時間控制 API | 1-2 天 |
| **Phase 4** | [`05-phase4-frontend-timeline.md`](./05-phase4-frontend-timeline.md) | 星座切換控制器、時間軸控制器組件 | 2-3 天 |
| **Phase 5** | [`06-phase5-container-startup.md`](./06-phase5-container-startup.md) | Docker Compose 啟動順序、智能啟動腳本 | 1 天 |

### 📊 支援與規範文檔

| 分類 | 檔案名稱 | 說明 |
|------|----------|------|
| **驗收標準** | [`00-verification-standards.md`](./00-verification-standards.md) | 各階段驗證機制與完成確認 |
| **性能指標** | [`00-performance-metrics.md`](./00-performance-metrics.md) | 效能指標、資源使用預估、未來擴展 |

## 🚀 快速開始

### 📋 開發前置檢查

```bash
# 1. 確認 Docker 環境運行正常
make status

# 2. 確認 PostgreSQL RL 數據庫可用
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "\dt"

# 3. 檢查當前 Git 狀態
git status
```

### 🎯 開發執行流程

```bash
# 1. 從 Phase 1 開始開發
cd satellite-precompute-plan
less 02-phase1-database-setup.md

# 2. 按順序完成各階段
# Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

# 3. 每個階段完成後執行驗證
# 參考對應的驗證標準文檔
```

### ⚠️ 重要注意事項

1. **編碼規範**：創建中文檔案時使用 `echo` 命令，避免亂碼
2. **錯誤處理**：發現錯誤立即修復，絕不接受錯誤狀態
3. **API 配置**：禁止硬編碼 URL，使用統一配置系統
4. **真實數據**：對論文研究影響的數據必須使用真實數據
5. **重構驗證**：每次重構後必須執行完整系統驗證

## 🎯 核心技術要求

### 💾 數據真實性分級
- **CRITICAL**：軌道動力學、衛星位置、切換決策邏輯
- **HIGH**：信號強度模型、都卜勒頻移、路徑損耗
- **MEDIUM**：大氣衰減、干擾場景、網路負載
- **LOW**：用戶行為、背景流量、非關鍵參數

### 📊 技術規格
- **時間解析度**：30 秒間隔
- **可見衛星數**：6-8 顆（符合 3GPP NTN 標準）
- **觀測位置**：台灣（24.94°N, 121.37°E）
- **支援星座**：Starlink (主要) + OneWeb (對比)
- **數據存儲**：NetStack RL PostgreSQL (172.20.0.51:5432/rl_research)

## 📖 相關資源

### 🔗 外部參考
- [Celestrak TLE 數據](https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle)
- [3GPP TS 38.331 NTN 標準](https://www.3gpp.org/specifications)
- [Skyfield 天體計算庫](https://rhodesmill.org/skyfield/)

### 📂 專案結構
```
ntn-stack/
├── satellite-precompute-plan/    # 本開發計畫目錄
├── netstack/                     # 5G 核心網後端
├── simworld/                     # 3D 仿真引擎
└── CLAUDE.md                     # 專案開發規範
```

---

**🎯 下一步動作**：開始 [`02-phase1-database-setup.md`](./02-phase1-database-setup.md) 的開發工作！

