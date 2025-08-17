# 📋 Phase 1B: 檔案清點和重命名計劃

**風險等級**: 🟡 中風險  
**預估時間**: 45分鐘  
**必要性**: ✅ 必要 - 符合CLAUDE.md檔案命名規範，建立清理基礎

## 🎯 目標

全面清點所有違反CLAUDE.md命名規範的檔案，建立功能導向的重命名計劃，為後續恢復六階段系統奠定基礎。

## 🚫 禁止的命名模式 (CLAUDE.md規範)

### 絕對禁止使用的命名
- **stage + 數字**: `stage1_`, `stage2_`, `stage3_`等
- **phase + 數字**: `phase1_`, `phase2_`, `phase3_`等  
- **抽象序號**: `step1_`, `part2_`, `F1_`, `F2_`, `F3_`, `A1_`等
- **臨時標記**: `phase1_core_system`, `stage*_processor`等

## 📋 檔案清點清單

### 1. 四階段系統檔案掃描
**目標目錄**: `/netstack/src/leo_core/`

預期發現的問題檔案：
```bash
leo_core/core_system/
├── tle_data_loader/           # ✅ 功能導向命名，無需修改
├── satellite_filter_engine/   # ✅ 功能導向命名，無需修改  
├── signal_analyzer/           # ✅ 功能導向命名，無需修改
├── dynamic_pool_planner/      # ✅ 功能導向命名，無需修改
└── main_pipeline.py          # ⚠️ 可能包含引用問題命名的程式碼
```

### 2. 全系統檔案命名掃描
**掃描範圍**: 整個 `/home/sat/ntn-stack/` 專案

**掃描指令**:
```bash
# 掃描所有違反命名規範的檔案
find /home/sat/ntn-stack -type f \( -name "*stage*" -o -name "*phase*" -o -name "*F1*" -o -name "*F2*" -o -name "*F3*" -o -name "*A1*" \) > naming_violations.txt

# 掃描目錄命名問題
find /home/sat/ntn-stack -type d \( -name "*stage*" -o -name "*phase*" -o -name "*F1*" -o -name "*F2*" -o -name "*F3*" -o -name "*A1*" \) >> naming_violations.txt
```

### 3. 引用關係掃描
**檢查程式碼中的import和路徑引用**:
```bash
# 掃描程式碼中的問題引用
grep -r "stage[0-9]" /home/sat/ntn-stack/netstack/src/ > code_references.txt
grep -r "phase[0-9]" /home/sat/ntn-stack/netstack/src/ >> code_references.txt
grep -r "F[1-3]" /home/sat/ntn-stack/netstack/src/ >> code_references.txt
grep -r "A1" /home/sat/ntn-stack/netstack/src/ >> code_references.txt

# 前端引用檢查
grep -r "stage\|phase\|F[1-3]\|A1" /home/sat/ntn-stack/simworld/frontend/src/ >> code_references.txt

# 後端引用檢查  
grep -r "stage\|phase\|F[1-3]\|A1" /home/sat/ntn-stack/simworld/backend/app/ >> code_references.txt
```

## 🔄 重命名對應表

### 四階段→功能導向命名
基於功能的重命名策略：

| 原始名稱 | 功能導向名稱 | 說明 |
|----------|-------------|------|
| `F1_*` | `tle_loader_*` | TLE數據載入相關 |
| `F2_*` | `satellite_filter_*` | 衛星篩選相關 |
| `F3_*` | `signal_analyzer_*` | 信號分析相關 |
| `A1_*` | `dynamic_pool_optimizer_*` | 動態池優化相關 |
| `stage1_*` | `tle_processing_*` | 階段一功能 |
| `stage2_*` | `intelligent_filtering_*` | 階段二功能 |
| `stage3_*` | `signal_quality_analysis_*` | 階段三功能 |
| `stage4_*` | `timeseries_preprocessing_*` | 階段四功能 |
| `stage5_*` | `data_integration_*` | 階段五功能 |
| `stage6_*` | `dynamic_pool_planning_*` | 階段六功能 |
| `phase1_core_system` | `leo_satellite_core_system` | 核心系統 |

### 具體檔案重命名計劃

#### NetStack核心檔案
```bash
# 可能需要重命名的檔案 (基於掃描結果)
/netstack/src/leo_core/phase1_core_system/ → /netstack/src/leo_core/satellite_core_system/
/netstack/src/stages/stage1_processor.py → /netstack/src/stages/tle_processing_engine.py
/netstack/src/stages/stage2_processor.py → /netstack/src/stages/intelligent_filtering_engine.py
/netstack/src/stages/stage3_processor.py → /netstack/src/stages/signal_analysis_engine.py
/netstack/src/stages/stage4_processor.py → /netstack/src/stages/timeseries_processing_engine.py  
/netstack/src/stages/stage5_processor.py → /netstack/src/stages/data_integration_engine.py
/netstack/src/stages/stage6_processor.py → /netstack/src/stages/dynamic_pool_planning_engine.py
```

#### 前端檔案
```bash
# 檢查前端服務是否有命名問題
/simworld/frontend/src/services/*stage* → 重命名為功能導向
/simworld/frontend/src/config/*stage* → 重命名為功能導向
```

#### 後端檔案
```bash
# 檢查後端路由是否有命名問題
/simworld/backend/app/api/routes/*stage* → 重命名為功能導向
/simworld/backend/app/services/*stage* → 重命名為功能導向
```

## 🔧 執行步驟

### Step 1: 檔案命名違規掃描
```bash
cd /home/sat/ntn-stack/leo_six_stage_upgrade_plan

# 創建掃描報告目錄
mkdir -p reports

# 掃描所有命名違規檔案
echo "=== 檔案命名違規掃描 ===" > reports/naming_violations_report.txt
echo "掃描時間: $(date)" >> reports/naming_violations_report.txt
echo "" >> reports/naming_violations_report.txt

# 檔案命名掃描
echo "## 檔案命名違規" >> reports/naming_violations_report.txt
find /home/sat/ntn-stack -type f \( -name "*stage*" -o -name "*phase*" -o -name "*F1*" -o -name "*F2*" -o -name "*F3*" -o -name "*A1*" \) >> reports/naming_violations_report.txt

echo "" >> reports/naming_violations_report.txt
echo "## 目錄命名違規" >> reports/naming_violations_report.txt
find /home/sat/ntn-stack -type d \( -name "*stage*" -o -name "*phase*" -o -name "*F1*" -o -name "*F2*" -o -name "*F3*" -o -name "*A1*" \) >> reports/naming_violations_report.txt

echo "" >> reports/naming_violations_report.txt
echo "總檔案數: $(find /home/sat/ntn-stack -type f \( -name "*stage*" -o -name "*phase*" -o -name "*F1*" -o -name "*F2*" -o -name "*F3*" -o -name "*A1*" \) | wc -l)" >> reports/naming_violations_report.txt
echo "總目錄數: $(find /home/sat/ntn-stack -type d \( -name "*stage*" -o -name "*phase*" -o -name "*F1*" -o -name "*F2*" -o -name "*F3*" -o -name "*A1*" \) | wc -l)" >> reports/naming_violations_report.txt
```

### Step 2: 程式碼引用關係分析
```bash
# 掃描程式碼中的引用關係
echo "" >> reports/naming_violations_report.txt
echo "=== 程式碼引用關係分析 ===" >> reports/naming_violations_report.txt

# NetStack引用掃描
echo "## NetStack引用" >> reports/naming_violations_report.txt
grep -r "stage[0-9]\|phase[0-9]\|F[1-3]\|A1" /home/sat/ntn-stack/netstack/src/ --include="*.py" | head -20 >> reports/naming_violations_report.txt

# 前端引用掃描
echo "" >> reports/naming_violations_report.txt
echo "## 前端引用" >> reports/naming_violations_report.txt
grep -r "stage\|phase\|F[1-3]\|A1" /home/sat/ntn-stack/simworld/frontend/src/ --include="*.ts" --include="*.js" | head -20 >> reports/naming_violations_report.txt

# 後端引用掃描
echo "" >> reports/naming_violations_report.txt
echo "## 後端引用" >> reports/naming_violations_report.txt
grep -r "stage\|phase\|F[1-3]\|A1" /home/sat/ntn-stack/simworld/backend/app/ --include="*.py" | head -20 >> reports/naming_violations_report.txt
```

### Step 3: 建立重命名執行計劃
```bash
# 基於掃描結果建立具體的重命名指令
echo "" >> reports/naming_violations_report.txt
echo "=== 重命名執行計劃 ===" >> reports/naming_violations_report.txt

# 建立重命名腳本模板
cat > reports/rename_execution_plan.sh << 'EOF'
#!/bin/bash
# 檔案重命名執行計劃
# 基於掃描結果自動生成

# 設定備份目錄
backup_dir="/home/sat/ntn-stack/backup/renaming_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

echo "開始檔案重命名..."
echo "備份目錄: $backup_dir"

# TODO: 根據實際掃描結果填入具體的重命名指令
# 格式: mv "原始路徑" "新路徑"
# 每次移動前先備份

# 範例:
# cp "/原始路徑" "$backup_dir/"
# mv "/原始路徑" "/新路徑"

echo "檔案重命名完成"
EOF

chmod +x reports/rename_execution_plan.sh
```

### Step 4: 引用關係修復計劃
```bash
# 建立引用修復計劃
cat > reports/reference_fix_plan.txt << 'EOF'
# 引用關係修復計劃
# 基於掃描結果需要修復的程式碼引用

## Python Import修復
# 格式: 檔案路徑 → 需要修改的import語句

## TypeScript/JavaScript引用修復  
# 格式: 檔案路徑 → 需要修改的引用

## 配置檔案修復
# 格式: 檔案路徑 → 需要修改的配置項目

## API端點修復
# 格式: 檔案路徑 → 需要修改的端點路徑
EOF
```

## ⚠️ 重命名風險控制

### 重命名前安全檢查
1. **完整備份**: 每個檔案重命名前先備份
2. **依賴檢查**: 確認檔案的所有引用關係
3. **測試驗證**: 重命名後測試關鍵功能
4. **回滾機制**: 準備快速回滾方案

### 高風險檔案識別
- **主要配置檔案**: `docker-compose.yml`, `package.json`等
- **API路由檔案**: 可能影響前端調用
- **核心業務邏輯**: 主要演算法檔案
- **資料庫模型**: 可能影響數據存取

## 📊 重命名統計表

執行掃描後填寫：

### 掃描結果統計
- 違規檔案總數: `_______`
- 違規目錄總數: `_______`
- 程式碼引用總數: `_______`

### 風險分類
- 🟢 低風險 (配置檔案): `_______`
- 🟡 中風險 (業務邏輯): `_______`
- 🔴 高風險 (核心系統): `_______`

### 重命名範圍
- NetStack檔案: `_______`
- SimWorld檔案: `_______`
- 配置檔案: `_______`
- 文檔檔案: `_______`

## ✅ 驗證檢查清單

### 掃描完成驗證
- [ ] 檔案命名違規掃描完成
- [ ] 程式碼引用關係分析完成
- [ ] 重命名執行計劃已建立
- [ ] 引用修復計劃已建立
- [ ] 風險評估已完成

### 報告輸出驗證
- [ ] `naming_violations_report.txt` 已生成
- [ ] `rename_execution_plan.sh` 已建立
- [ ] `reference_fix_plan.txt` 已建立
- [ ] 統計數據已完整記錄

## 🔗 輸出檔案

### 主要報告
1. **`reports/naming_violations_report.txt`** - 完整違規掃描報告
2. **`reports/rename_execution_plan.sh`** - 重命名執行腳本
3. **`reports/reference_fix_plan.txt`** - 引用修復計劃

### 下一步行動
掃描和計劃完成後，繼續執行：
→ `03_six_stage_restoration.md`

---
**📝 重要提醒**: 此階段是準備性工作，實際的重命名執行將在六階段恢復過程中進行，確保與系統架構恢復同步。
