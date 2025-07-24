# LEO 衛星系統開發計畫文檔

## 📚 文檔結構

本項目的開發計畫已按功能模組拆分為多個專門文檔，便於閱讀和維護：

### 🎯 核心規劃文檔
- **[overview.md](./overview.md)** - 方案概述、技術參數、多星座支援設計
- **[architecture.md](./architecture.md)** - 系統架構、數據流設計、PostgreSQL 架構

### 🚀 開發實施文檔  
- **[phase1-database.md](./phase1-database.md)** - Phase 1: PostgreSQL 數據架構設計
- **[phase2-precompute.md](./phase2-precompute.md)** - Phase 2: 數據預計算引擎
- **[phase3-api.md](./phase3-api.md)** - Phase 3: API 端點實現
- **[phase4-frontend.md](./phase4-frontend.md)** - Phase 4: 前端時間軸控制
- **[phase5-deployment.md](./phase5-deployment.md)** - Phase 5: 容器啟動順序和智能更新

### 🧪 測試驗證文檔
- **[verification.md](./verification.md)** - 各 Phase 驗證機制和完成確認方法
- **[testing-scripts.md](./testing-scripts.md)** - 測試腳本和自動化驗證工具

### 📊 技術細節文檔
- **[api-specification.md](./api-specification.md)** - 完整 API 規格文檔
- **[database-schema.md](./database-schema.md)** - 數據庫 Schema 設計詳情
- **[frontend-components.md](./frontend-components.md)** - 前端組件設計規格

## 🔄 文檔使用流程

### 👨‍💻 開發者閱讀順序
1. **開始前** → `overview.md` 了解整體方案
2. **架構設計** → `architecture.md` 理解系統結構
3. **分階段開發** → `phase1-5` 文檔按順序實施
4. **測試驗證** → `verification.md` 確保每階段完成

### 🛠️ 維護更新流程
- **功能變更** → 更新對應 phase 文檔
- **架構調整** → 更新 `architecture.md`
- **測試改進** → 更新 `verification.md`
- **API 變更** → 更新 `api-specification.md`

## 🎯 快速導航

### 我想了解...
- **整體方案** → [overview.md](./overview.md)
- **系統架構** → [architecture.md](./architecture.md)  
- **如何開發** → [phase1-database.md](./phase1-database.md) (按順序讀)
- **如何測試** → [verification.md](./verification.md)
- **API 規格** → [api-specification.md](./api-specification.md)

### 我想實施...
- **數據庫設計** → [phase1-database.md](./phase1-database.md)
- **預計算引擎** → [phase2-precompute.md](./phase2-precompute.md)
- **前端組件** → [phase4-frontend.md](./phase4-frontend.md)
- **部署配置** → [phase5-deployment.md](./phase5-deployment.md)

## 📝 文檔維護

- **主要維護者**: 開發團隊
- **更新頻率**: 隨開發進度同步更新
- **版本控制**: 與代碼庫同步版本管理
- **協作方式**: Pull Request 方式提交文檔變更

---
*文檔拆分時間: 2025-01-23*  
*原始文檔: new.md (已拆分為多個專門文檔)*