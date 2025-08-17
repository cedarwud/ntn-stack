# 🔄 LEO衛星系統六階段升級計劃

**版本**: v1.0  
**創建日期**: 2025-08-17  
**目標**: 強化六階段系統，整合四階段(leo_restructure)技術資產，清理四階段檔案

## 🎯 升級目標

### 核心理念
- **保留六階段功能完整性**：維持原系統8,735→563顆的93.6%篩選效率
- **整合leo_restructure技術棧**：標準化數據模型、智能更新、開發工具鏈
- **用模擬退火取代階段六**：動態池規劃演算法升級
- **全面技術債務清理**：檔案命名、跨平台兼容、數據源統一

### 預期效果
- ✅ 六階段 + leo_restructure 技術基礎設施
- ✅ 完整功能保持 + 60倍開發效率提升
- ✅ 跨平台兼容性 (Linux/macOS/Windows)
- ✅ 100% 本地TLE數據，零網路依賴

## 📋 執行計劃概覽

### 執行順序 (嚴格按照編號順序執行)

```
Phase 0: 準備階段 → Phase 1: 分析階段 → Phase 2: 恢復階段 → Phase 3: 整合階段 → Phase 4: 優化階段 → Phase 5: 清理階段
```

| 階段 | 檔案 | 功能 | 風險等級 | 預估時間 |
|------|------|------|----------|----------|
| **Phase 0** | `00_pre_execution_backup.md` | 完整系統備份 | 🟢 低風險 | 10分鐘 |
| **Phase 1** | `01_current_system_analysis.md` | 分析四階段系統現狀 | 🟢 低風險 | 30分鐘 |
| **Phase 1** | `02_file_inventory_and_naming.md` | 檔案清點和重命名計劃 | 🟡 中風險 | 45分鐘 |
| **Phase 2** | `03_six_stage_restoration.md` | 恢復六階段架構 | 🔴 高風險 | 2小時 |
| **Phase 3** | `04_leo_restructure_integration.md` | 整合技術資產 | 🟡 中風險 | 1.5小時 |
| **Phase 4** | `05_cross_platform_fixes.md` | 跨平台路徑修復 | 🟡 中風險 | 1小時 |
| **Phase 4** | `06_data_source_validation.md` | 本地TLE數據源驗證 | 🟡 中風險 | 45分鐘 |
| **Phase 5** | `07_cleanup_plan.md` | 四階段檔案清理 | 🟢 低風險 | 30分鐘 |

**總預估時間**: 6.5小時

## 🚨 重要安全原則

### 執行前必讀
1. **🛡️ 備份優先**：Phase 0 必須完整執行，確保可回滾
2. **🔄 增量驗證**：每完成一個檔案就測試驗證
3. **🌿 分支開發**：在 git 分支中進行所有修改
4. **⚠️ 高風險控制**：Phase 2 (六階段恢復) 風險最高，需特別謹慎

### 中斷處理
- 如任何階段失敗，立即停止後續執行
- 參考對應檔案的「🚨 故障恢復」章節
- 必要時使用 Phase 0 備份完全回滾

## 🔧 快速開始

### 一鍵執行 (推薦)
```bash
cd /home/sat/ntn-stack/leo_six_stage_upgrade_plan
./execution_scripts/run_upgrade.sh
```

### 手動步驟執行
```bash
# Phase 0: 系統備份
bash execution_scripts/00_backup_system.sh

# Phase 1: 系統分析
bash execution_scripts/01_analyze_system.sh
bash execution_scripts/02_inventory_files.sh

# Phase 2: 六階段恢復 ⚠️ 高風險階段
bash execution_scripts/03_restore_six_stages.sh

# Phase 3: 資產整合
bash execution_scripts/04_integrate_assets.sh

# Phase 4: 技術優化
bash execution_scripts/05_fix_cross_platform.sh
bash execution_scripts/06_validate_data_sources.sh

# Phase 5: 系統清理
bash execution_scripts/07_cleanup_old_files.sh
```

### 驗證成功
```bash
# 完整系統測試
make down && make build && make up

# API響應驗證
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/satellites/positions

# 前端立體圖驗證
# 瀏覽器訪問: http://localhost:5173
```

## 📊 技術資產整合摘要

### leo_restructure 核心價值
1. **🧮 完整數據模型系統** - 統一所有階段的數據結構
2. **🔄 智能增量更新** - 避免不必要的重複計算
3. **⚡ 高效開發工具鏈** - leo-dev/test/full 60倍效率提升
4. **📚 演算法庫標準化** - SGP4/RSRP/事件檢測統一
5. **🛡️ 自動清理保護** - 智能保護RL訓練數據

### 六階段功能保持
1. **階段一**: TLE載入 (8,735顆→軌道計算)
2. **階段二**: 智能篩選 (93.6%篩選率→563顆)
3. **階段三**: 信號分析 (3GPP A4/A5/D2事件)
4. **階段四**: 時間序列 (前端動畫數據)
5. **階段五**: 數據整合 (PostgreSQL+Volume混合)
6. **階段六**: **模擬退火動態池** ← leo_restructure升級

## 📋 待清理檔案清單預覽

### 四階段開發檔案 (升級完成後刪除)
- `/netstack/src/leo_core/` - 整個四階段系統目錄
- 兩個備份目錄: `leo_core.backup.20250816_*`
- 所有包含 `phase1_core_system/` 的路徑
- 所有包含 `F1/F2/F3/A1` 命名的檔案

**總清理數量**: 預估 60+ 檔案 (詳見 `07_cleanup_plan.md`)

## 🎯 成功標準

### 功能驗證
- ✅ 六階段處理流程完整運行
- ✅ API響應時間 < 100ms
- ✅ 前端立體圖正常渲染
- ✅ 衛星篩選效率維持 93.6%

### 技術升級
- ✅ 跨平台兼容 (Linux/macOS/Windows)
- ✅ 100% 本地TLE數據源
- ✅ 零模擬數據，完整SGP4算法
- ✅ 標準化檔案命名 (無stage/phase)

### 開發效率
- ✅ leo-dev 30秒快速開發模式
- ✅ 智能增量更新機制
- ✅ 自動化開發工具鏈

---

**⚠️ 重要提醒**: 執行前請詳細閱讀每個階段的具體計劃檔案，確保理解所有操作步驟和風險點。

**🚀 開始執行**: 從 `00_pre_execution_backup.md` 開始，嚴格按照編號順序執行。
