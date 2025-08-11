# SimWorld Backend 重構計劃總覽

## 🎯 專案目標

本重構計劃旨在全面檢視和優化 SimWorld Backend，專注於 **LEO satellite handover** 研究核心需求，移除無關功能，提升系統維護效率和研究專注度。

### 核心理念
> **正確性 > 可靠性 > 效能 > 可維護性**  
> 確保核心研究功能完整保留，同時為 Sionna 物理層模擬和 3D 場景渲染提供支援

## 📚 文檔架構

### 📖 重構計劃文檔

| 文檔 | 描述 | 狀態 |
|------|------|------|
| [01-analysis-report.md](./01-analysis-report.md) | **全面分析報告** - 詳細分析現有架構，識別問題和改善機會 | ✅ 完成 |
| [02-components-classification.md](./02-components-classification.md) | **組件分類指南** - 按優先級和功能分類所有組件 | ✅ 完成 |
| [03-refactor-roadmap.md](./03-refactor-roadmap.md) | **重構路線圖** - 5階段分步驟執行計劃 | ✅ 完成 |
| [04-implementation-plan.md](./04-implementation-plan.md) | **實施計劃** - 詳細執行步驟和驗證方法 | ✅ 完成 |
| [05-risk-assessment.md](./05-risk-assessment.md) | **風險評估** - 風險分析、緩解策略和應急方案 | ✅ 完成 |

### 📊 快速參考

#### 🎯 重構範圍概覽
- **總檔案數**: ~85 個 Python 檔案
- **建議移除**: 15+ 個檔案/功能 (-20%) + 分析圖表資源
- **核心保留**: 16 個檔案 (衛星相關)
- **重要保留**: 10 個檔案 (設備管理 + 3D 衛星渲染)

#### 🚀 預期效益  
- **程式碼簡化**: 減少 ~3,000+ 行程式碼 (-25%)
- **維護效率**: 降低技術債務 30%
- **系統效能**: 記憶體使用減少 20%
- **開發專注**: 聚焦於核心演算法 + 衛星動畫支援

## 🔄 執行流程

### Phase 1: 環境準備 (Week 1)
```bash
# 建立重構分支和備份
git checkout -b refactor/simworld-backend-cleanup
git tag v-before-refactor
```
**目標**: 建立安全的重構環境  
**交付**: 完整備份、依賴分析、測試基準

### Phase 2: 低風險移除 (Week 2)  
```bash
# 移除 UAV 追踪、開發工具、過時代碼
rm app/api/routes/uav.py
rm app/services/precision_validator.py
rm app/services/skyfield_migration.py
```
**目標**: 移除完全獨立的組件  
**交付**: UAV、開發工具、遷移代碼移除

### Phase 3: 精確功能移除 (Week 3)
```bash
# 移除系統監控功能域
rm -rf app/domains/system/

# 移除 Sionna 繪圖分析功能
# 在 domains/wireless/ 中移除圖表生成相關功能
# 在 domains/simulation/services/sionna_service.py 中移除圖表方法

# 移除分析圖表資源（保留所有 3D 模型）
rm -rf app/static/images/
```
**目標**: 精確移除繪圖分析功能，保留衛星渲染  
**交付**: 系統監控、Sionna 繪圖功能移除，保留 3D 場景和所有模型

### Phase 4: 程式碼重構 (Week 4)
**目標**: 重構重複程式碼，優化架構  
**交付**: 統一距離計算、優化座標轉換、重組 API

### Phase 5: 測試完善 (Week 5)
**目標**: 完善測試，更新文檔  
**交付**: 80% 測試覆蓋率、完整文檔

## 🎨 架構保留策略

### ✅ 核心保留 (P0 - 必須)
**LEO Satellite Handover 直接相關**

🛰️ **衛星域** (domains/satellite/)
- 軌道計算、可見性分析、切換決策
- SGP4 算法、距離計算、歷史數據

🌐 **座標域** (domains/coordinates/)  
- 座標系統轉換、位置計算
- ECEF、ENU、地理座標轉換

### ✅ 重要保留 (P1 - 衛星動畫支援)
**衛星移動渲染和基本功能**

📱 **設備域** (domains/device/)
- 基本設備 CRUD 管理（核心功能）
- 設備數據持久化（基本操作）

🎨 **3D 渲染域** (domains/simulation/)
- 場景管理服務（衛星動畫場景）
- 3D 渲染服務（衛星移動渲染）
- 場景模擬 API（場景載入）

📦 **3D 資源** (static/)
- 所有 3D 模型（sat.glb, tower.glb, uav.glb, jam.glb）
- 場景模型檔案（NTPU、NYCU 等場景）

### ❌ 移除組件 (P3)  
**繪圖分析和非研究相關功能**

- 🚁 UAV 追踪模組 (api/routes/uav.py)
- 🖥️ 系統監控域 (domains/system/) - **完整移除**
- 🔬 Sionna 繪圖功能 (domains/wireless/ 中的圖表生成) - **部分移除**
- 📊 分析圖表資源 (static/images/) - **完整移除**（保留所有 3D 模型）
- 🔧 開發期工具 (precision_validator.py, distance_validator.py)
- 📦 過時遷移代碼 (skyfield_migration.py)

## 🛡️ 風險管理

### 🔴 高風險關注
1. **隱藏依賴風險**: 深度分析模組依賴關係
2. **核心功能損壞**: 完整測試衛星相關功能  
3. **資料一致性**: 備份和驗證資料庫資料

### 🟡 中風險監控
1. **API 相容性**: 保持前端 API 向後相容
2. **效能回歸**: 持續監控響應時間和資源使用
3. **測試覆蓋**: 補強關鍵功能測試

### 🟢 低風險項目
1. **文檔同步**: 更新相關文檔
2. **環境差異**: 使用 Docker 確保一致性

## ⚡ 快速開始

### 1. 閱讀重構計劃
```bash
# 先閱讀全面分析報告
cat 01-analysis-report.md

# 了解組件分類
cat 02-components-classification.md

# 查看執行路線圖  
cat 03-refactor-roadmap.md
```

### 2. 環境準備
```bash
# 建立重構分支
git checkout -b refactor/simworld-backend-cleanup

# 建立備份
cp -r simworld/backend backup/simworld-backend-$(date +%Y%m%d)

# 安裝分析工具
pip install pydeps vulture pipdeptree
```

### 3. 執行重構前檢查
```bash
# 相依性分析
pydeps simworld/backend/app --show-deps

# 建立測試基準
cd simworld/backend  
python -m pytest tests/ --cov=app --cov-report=html

# API 健康檢查
curl -s http://localhost:8888/health | jq .
```

## 📈 成功標準

### 功能完整性 ✅
- [ ] 所有衛星相關功能正常運作
- [ ] 軌道計算精度保持不變  
- [ ] 可見性分析結果正確
- [ ] 基本設備管理功能正常
- [ ] 衛星 3D 移動渲染功能正常

### 品質指標 📊  
- [ ] 測試覆蓋率 ≥ 80%
- [ ] 程式碼品質評分 ≥ 8.5/10
- [ ] API 響應時間 ≤ 100ms (90th)
- [ ] 記憶體使用減少 ≥ 20%

### 維護效率 🔧
- [ ] 移除 15+ 個無關檔案/功能 + 分析圖表資源
- [ ] 減少 3000+ 行程式碼
- [ ] 消除 3 個技術債務域 + 部分功能  
- [ ] 專注於核心演算法研究 + 衛星動畫支援

## 🔍 檢查清單

### 執行前確認
- [ ] 已閱讀所有重構計劃文檔
- [ ] 已建立完整程式碼和資料備份
- [ ] 已準備測試基準和驗證腳本  
- [ ] 已與相關開發人員溝通協調

### 執行中監控
- [ ] 每階段後執行完整測試套件
- [ ] 持續監控系統健康狀態
- [ ] 記錄詳細的變更日誌
- [ ] 驗證核心功能正確性

### 執行後驗證
- [ ] 所有測試通過，無回歸
- [ ] API 功能完整，效能良好
- [ ] 文檔更新完整，準確無誤
- [ ] 系統運行穩定，無異常

## 📞 支援與協助

### 技術支援
- **重構問題**: 參考 [04-implementation-plan.md](./04-implementation-plan.md)
- **風險處理**: 參考 [05-risk-assessment.md](./05-risk-assessment.md)  
- **組件分類**: 參考 [02-components-classification.md](./02-components-classification.md)

### 應急處理
```bash
# 緊急回滾腳本
git reset --hard v-before-refactor
make simworld-restart

# 健康檢查腳本
bash scripts/refactor_validation.sh
```

---

## 🎯 總結

此重構計劃經過詳細的分析和規劃，旨在：

1. **專注研究目標** - 精確移除 Sionna 繪圖分析功能，保留衛星動畫渲染
2. **保持功能完整** - 確保 LEO satellite handover 核心研究功能不受影響
3. **平衡簡化與支援** - 移除分析圖表功能，保留前端衛星動畫支援
4. **提升維護效率** - 減少技術債務，簡化系統架構同時保持視覺化能力

**執行原則**: 安全第一，漸進改進，確保核心研究工作順利進行。

---

**文檔版本**: v1.0  
**建立日期**: 2025-08-11  
**最後更新**: 2025-08-11  
**作者**: Claude Code AI Assistant
EOF < /dev/null
