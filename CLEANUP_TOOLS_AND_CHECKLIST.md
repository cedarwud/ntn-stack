# 代碼清理工具與檢查清單

## 🔍 未使用功能檢測工具

### 1. 自動化分析工具
```bash
# 安裝分析工具
pip install vulture pydeps importchecker pyflakes

# 檢測未使用的代碼
vulture netstack/ --min-confidence 80

# 生成依賴關係圖
pydeps netstack/src --show-deps --max-bacon 3 --show-dot > deps.dot

# 檢查導入問題
importchecker netstack/src

# 檢查語法和未使用變數
pyflakes netstack/
```

### 2. 手動檢查腳本
```bash
#!/bin/bash
# 檢查每個 Python 文件的使用情況

echo "=== 檢查未被導入的模組 ==="
for file in $(find netstack/src -name "*.py"); do
    basename=$(basename "$file" .py)
    if [ "$basename" != "__init__" ]; then
        count=$(grep -r "from.*$basename\|import.*$basename" netstack/ | wc -l)
        if [ "$count" -eq 0 ]; then
            echo "❓ 可能未使用: $file (導入次數: $count)"
        fi
    fi
done

echo -e "\n=== 檢查大型檔案 (>1000行) ==="
find netstack/ -name "*.py" -exec wc -l {} + | awk '$1 > 1000' | sort -nr

echo -e "\n=== 檢查空檔案或僅有註釋的檔案 ==="
find netstack/ -name "*.py" -exec sh -c 'lines=$(grep -v "^#\|^$\|^[[:space:]]*#" "$1" | wc -l); if [ $lines -le 3 ]; then echo "❓ 內容極少: $1 (有效行數: $lines)"; fi' _ {} \;
```

## 📋 模組評估檢查清單

### 對每個 Python 檔案/模組的評估標準

#### 🎯 保留標準 (必須滿足至少 2 項)
- [ ] **被主要功能使用**: 被核心 API 或主要算法引用
- [ ] **有測試覆蓋**: 存在對應的測試文件
- [ ] **核心業務邏輯**: 實現主要的衛星/算法功能
- [ ] **外部接口**: 提供對外的 API 端點
- [ ] **配置或數據**: 重要的配置文件或數據文件
- [ ] **近期有更新**: 最近 3 個月內有修改

#### ❌ 移除標準 (滿足任一項可考慮移除)
- [ ] **零引用**: 沒有任何其他文件導入或使用
- [ ] **過時實驗**: 明顯是實驗性或概念驗證代碼
- [ ] **重複功能**: 與其他文件提供相同功能
- [ ] **空文件**: 只有導入語句或註釋，無實際邏輯
- [ ] **錯誤代碼**: 包含明顯錯誤或無法運行的代碼
- [ ] **過時依賴**: 依賴已移除的外部庫或服務

#### 🔄 重構標準 (需要改進但保留)
- [ ] **結構不佳**: 代碼結構混亂但功能重要
- [ ] **依賴複雜**: 硬編碼依賴多，不利測試
- [ ] **職責不明**: 一個文件包含多種不相關功能
- [ ] **命名不當**: 文件名或函數名不清晰

## 🗂️ 具體檢查清單 - 按目錄分析

### src/algorithms/ 目錄
```bash
src/algorithms/access/fast_access_decision.py      # 44KB
src/algorithms/handover/fine_grained_decision.py   # 28KB  
src/algorithms/prediction/orbit_prediction.py      # 47KB
src/algorithms/sync/state_synchronization.py       # 37KB
src/algorithms/sync/distributed_sync.py            # 31KB
src/algorithms/ml/prediction_models.py             # ?KB
```

**評估問題**:
- [ ] 每個目錄只有 1-2 個文件，過度分散？
- [ ] 這些算法是否都在實際使用？
- [ ] 是否有重複的算法實現？

### src/services/ 目錄
```bash
src/services/handover/handover_event_trigger_service.py  # 1個文件
src/services/research/threegpp_event_generator.py        # 1個文件
src/services/satellite/                                  # 22個文件 (合理)
```

**評估問題**:
- [ ] handover/ 和 research/ 是否需要獨立目錄？
- [ ] 這些服務是否與 netstack_api/services/ 重複？

### netstack_api/ vs src/ 重複分析
```bash
# 需要檢查的潛在重複功能
netstack_api/services/ (28文件) vs src/services/ (24文件)
netstack_api/models/ vs src/domain/
netstack_api/routers/ vs src/api/
```

**重複檢查清單**:
- [ ] 相同名稱的服務是否提供相同功能？
- [ ] 數據模型是否重複定義？
- [ ] API 端點是否有重複的路由？

## 🛠️ 重構決策矩陣

### 高優先級清理 (建議立即處理)
| 文件類型 | 標準 | 操作 |
|---------|------|------|
| 空檔案 | < 5 行有效代碼 | 刪除 |
| 零引用檔案 | 無任何導入引用 | 刪除 |
| 明顯重複 | 相同功能，不同實現 | 合併 |
| 過時實驗 | 包含 "test", "demo", "experiment" | 歸檔或刪除 |

### 中優先級清理 (重構時處理)
| 文件類型 | 標準 | 操作 |
|---------|------|------|
| 過度分散 | 單檔案目錄 | 合併到父目錄 |
| 功能重複 | 相似但不完全相同 | 重構統一 |
| 結構不良 | 混合多種職責 | 拆分重組 |

### 低優先級清理 (重構後優化)
| 文件類型 | 標準 | 操作 |
|---------|------|------|
| 命名不當 | 名稱不清晰 | 重命名 |
| 代碼品質 | 複雜度高但功能重要 | 逐步改善 |

## 📊 清理進度追蹤模板

### 清理記錄表格
```markdown
| 檔案路徑 | 大小 | 引用次數 | 最後修改 | 決策 | 原因 | 狀態 |
|---------|------|---------|----------|------|------|------|
| src/algorithms/access/fast_access_decision.py | 44KB | 3 | 2024-08-04 | 保留+重構 | 核心算法 | ⏳ |
| src/algorithms/handover/fine_grained_decision.py | 28KB | 2 | 2024-08-03 | 保留+重構 | 核心算法 | ⏳ |
| ... | | | | | | |
```

### 統計摘要模板
```markdown
## 清理統計
- **總檔案數**: 174
- **已檢查**: 0 / 174
- **保留**: 0
- **重構**: 0  
- **移除**: 0
- **歸檔**: 0

## 空間節省
- **移除檔案數**: 0
- **節省代碼行數**: 0
- **減少目錄數**: 0
```

## 🚀 建議執行流程

### Step 1: 快速篩選 (1小時)
```bash
# 執行自動化工具，生成初步報告
./run_analysis_tools.sh > analysis_report.txt

# 識別明顯的清理目標
# - 空檔案
# - 零引用檔案  
# - 超大檔案
```

### Step 2: 手動審核 (2-3小時)
```bash
# 對每個標記的檔案進行手動檢查
# 使用上述檢查清單進行評估
# 記錄決策和原因
```

### Step 3: 分批執行 (重構過程中)
```bash
# 按模組分批進行重構和清理
# 每完成一個模組，更新進度記錄
# 運行測試確保功能無損
```

---

**這份檢查清單和工具建議可以幫助您在重構過程中系統性地識別和處理未使用的功能，確保重構的效率和安全性。**