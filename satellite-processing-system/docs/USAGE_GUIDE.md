# 📋 衛星處理系統 - 完整使用指南

**版本**: v1.1 (智能清理系統)  
**更新日期**: 2025-09-11  
**適用系統**: satellite-processing-system 獨立容器化版本

## 🚀 快速開始

### 🎯 最常用的執行方式

```bash
# 1. 啟動容器
docker compose up -d

# 2. 執行完整六階段處理 (推薦)
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py
```

⚡ **3分鐘完成**: 從 TLE 數據到動態池規劃的完整處理流程

## 📊 執行模式詳解

### 🔄 1. 完整六階段處理 (預設模式)

**自動執行所有階段**: Stage 1 → 2 → 3 → 4 → 5 → 6

```bash
# 使用預設 STANDARD 驗證
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py

# 使用 FAST 驗證 (開發推薦，速度快 60-70%)
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --validation-level=FAST

# 使用 COMPREHENSIVE 驗證 (學術發布用)
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --validation-level=COMPREHENSIVE
```

**✅ 特性**:
- 🗑️ **智能清理**: 階段1執行時清理所有舊輸出文件
- 📊 階段間自動數據傳遞
- ✅ 每階段完成後立即驗證
- 🛑 任意階段失敗時自動停止
- 📈 完整執行統計報告

### 🎯 2. 單階段執行

**只執行指定的單一階段**:

```bash
# 只執行階段 1 (TLE 軌道計算)
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=1

# 只執行階段 2 (可見性篩選)
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=2

# 只執行階段 6 (動態池規劃)
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=6

# 結合驗證級別
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=1 --validation-level=FAST
```

**🧠 智能清理策略** (v1.1 新功能):
- **完整管道模式**: 只在階段1清理所有舊檔案，其他階段保護數據流
- **單階段模式**: 智能清理目標階段及後續階段，**保留前面階段輸出作為輸入依賴**

**✅ 單階段執行優勢**:
- 🚀 基於真實前階段輸出進行開發測試
- 🛡️ 自動保護所需的輸入依賴檔案  
- 🗑️ 只清理當前階段及後續階段的舊輸出
- 📊 減少重複計算，提高開發效率

## ⚙️ 參數選項詳解

### 🎚️ `--stage` (階段選擇)

| 階段 | 功能 | 輸入 | 輸出 |
|------|------|------|------|
| `--stage=1` | TLE軌道計算 | TLE數據文件 | 8,837顆衛星軌道 |
| `--stage=2` | 可見性篩選 | Stage 1 輸出 | 可見衛星篩選結果 |
| `--stage=3` | 信號分析 | Stage 2 輸出 | 信號品質分析 |
| `--stage=4` | 時間序列預處理 | Stage 3 輸出 | 時間序列數據 |
| `--stage=5` | 數據整合 | Stage 4 輸出 | 整合數據集 |
| `--stage=6` | 動態池規劃 | Stage 5 輸出 | 最終優化方案 |

### 🛡️ `--validation-level` (驗證級別)

| 級別 | 執行時間 | 檢查項目 | 適用場景 |
|------|----------|----------|----------|
| `FAST` | **減少 60-70%** | 4-6 項關鍵檢查 | 開發測試、CI/CD |
| `STANDARD` | 正常 | 10-13 項檢查 | 正常生產使用 ⭐ **預設** |
| `COMPREHENSIVE` | 增加 5-10% | 14-16 項完整檢查 | 學術發布、重要驗證 |

## 🧠 智能清理機制詳解

### 📋 清理策略概覽

系統採用**智能雙模式清理策略**，根據執行模式自動選擇最適合的清理方案：

#### 🔄 完整管道模式 (`run_six_stages_with_validation.py`)
```bash
# 觸發條件：執行完整六階段處理
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py

# 清理行為：
# Stage 1 → 清理所有階段 1-6 的舊輸出和驗證快照
# Stage 2-6 → 跳過清理，保護數據流連續性
```

#### 🎯 單階段模式 (`--stage=N`)
```bash  
# 觸發條件：執行單一階段
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=3

# 清理行為：
# 智能清理階段 3-6 的輸出，保留階段 1-2 作為輸入依賴
```

### 🛡️ 清理保護策略

| 執行階段 | 清理範圍 | 保留範圍 | 用途說明 |
|----------|----------|----------|----------|
| `--stage=1` | 清理 1-6 | 無 | 全新開始 |
| `--stage=2` | 清理 2-6 | 保留 1 | 基於階段1真實輸出 |
| `--stage=3` | 清理 3-6 | 保留 1-2 | 基於階段1-2真實輸出 |
| `--stage=4` | 清理 4-6 | 保留 1-3 | 基於階段1-3真實輸出 |
| `--stage=5` | 清理 5-6 | 保留 1-4 | 基於階段1-4真實輸出 |
| `--stage=6` | 清理 6 | 保留 1-5 | 基於階段1-5真實輸出 |

### 📊 清理範圍詳細說明

**每階段清理內容包含**:
- ✅ **輸出檔案**: `data/*_output.json` 等處理結果
- ✅ **驗證快照**: `data/validation_snapshots/stageN_validation.json`  
- ✅ **輸出目錄**: 專用輸出目錄及其內容
- ✅ **臨時檔案**: 處理過程中的臨時檔案

**永不清理的內容**:
- 🛡️ **TLE 數據**: `data/tle_data/` (原始輸入數據)
- 🛡️ **系統配置**: 配置檔案和腳本
- 🛡️ **依賴輸入**: 前階段輸出 (單階段模式)

### 💡 開發工作流程優化

**情境1 - 開發階段4時間序列預處理**:
```bash
# 執行階段4 → 自動保留階段1-3輸出，清理階段4-6
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=4

# 優勢：
# ✅ 無需重新計算階段1-3 (節省數分鐘)  
# ✅ 基於真實數據測試階段4邏輯
# ✅ 自動清理階段4舊輸出確保結果正確
```

**情境2 - 完整系統測試**:
```bash
# 執行完整管道 → 階段1清理全部，確保數據一致性
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py

# 優勢：
# ✅ 從頭開始確保完整性
# ✅ 階段2-6不清理，保護數據流
# ✅ 完整驗證所有階段協同工作
```

## 🔧 Make 快捷命令

為了方便使用，系統提供了多個 Make 快捷命令：

### 🎯 完整處理命令
```bash
make run-stages          # 標準模式完整處理
make run-fast            # 快速模式完整處理  
make run-comprehensive   # 完整驗證模式處理
```

### 🧪 單階段命令
```bash
make run-stage1          # 只執行階段1
make run-stage6          # 只執行階段6
```

### 🛠️ 開發環境命令
```bash
make dev-run-stages      # 開發環境完整處理 (FAST模式)
make dev-run-stage STAGE=3  # 開發環境執行指定階段
```

### 📋 系統管理命令
```bash
make up                  # 啟動所有服務
make down                # 停止所有服務  
make status              # 查看服務狀態
make logs                # 查看即時日誌
```

## 🐳 容器環境說明

### 📦 主要容器

| 容器名 | 用途 | 狀態 |
|--------|------|------|
| `satellite-dev` | **主處理容器** | 🟢 開發/生產通用 |
| `satellite-postgres-dev` | 數據庫 | 🟢 支援服務 |
| `satellite-dev-monitor` | 監控服務 | 🟢 可選 |

**⚠️ 重要**: 所有執行命令都使用 `satellite-dev` 容器。

### 🔗 進入容器進行互動操作
```bash
# 進入主容器
docker exec -it satellite-dev bash

# 在容器內直接執行
python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=1
```

## 📁 數據目錄結構

### 📥 輸入數據 (自動提供)
```
data/
├── tle_data/
│   ├── starlink/        # Starlink TLE 數據
│   └── oneweb/          # OneWeb TLE 數據
```

### 📤 輸出數據 (自動生成)
```
data/
├── outputs/
│   ├── stage1/          # 階段1輸出：軌道計算結果
│   ├── stage2/          # 階段2輸出：可見性篩選
│   └── ...
├── validation_snapshots/
│   ├── stage1_validation.json
│   └── ...
```

## 🎯 使用場景指南

### 🧪 **開發和調試**
```bash
# 快速測試單個階段
make dev-run-stage STAGE=1

# 快速測試完整流程  
make dev-run-stages
```

### 🏭 **生產部署**
```bash
# 標準生產處理
make run-stages

# 高品質驗證處理
make run-comprehensive
```

### 📊 **學術研究**
```bash
# 最高品質驗證，適合論文發表
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --validation-level=COMPREHENSIVE
```

### 🐛 **故障排除**
```bash
# 檢查單個階段問題
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=2 --validation-level=COMPREHENSIVE

# 查看詳細日誌
make logs
```

## ⚡ 性能參考

### 📊 執行時間 (參考)
- **Stage 1 (軌道計算)**: ~3分鐘 (8,837顆衛星)
- **Stage 2-6**: 各約 30-60秒  
- **完整六階段**: ~5-8分鐘
- **FAST 驗證**: 節省 60-70% 驗證時間

### 💾 資源需求
- **RAM**: 8GB+ 推薦
- **磁碟**: 20GB+ 可用空間
- **輸出文件大小**: 1-3GB 總計

## 🚨 故障排除

### ❌ 常見問題

#### **1. 容器未啟動**
```bash
# 檢查容器狀態
make status

# 重新啟動
make down && make up
```

#### **2. 權限錯誤**
```bash
# 修正數據目錄權限
sudo chown -R $USER:$USER data/
```

#### **3. 磁碟空間不足**
```bash
# 清理舊輸出 (自動執行，但可手動清理)
docker exec satellite-dev rm -rf /satellite-processing/data/outputs/*
```

#### **4. 階段執行失敗**
- ✅ **自動清理**: 每次執行前會自動清理舊輸出
- ✅ **立即停止**: 任何階段失敗會自動停止後續處理
- ✅ **詳細日誌**: 查看具體錯誤信息

### 🔍 調試技巧

```bash
# 1. 檢查系統健康狀態  
docker exec satellite-dev python /satellite-processing/scripts/health_check.py

# 2. 使用 FAST 模式快速測試
docker exec satellite-dev python /satellite-processing/scripts/run_six_stages_with_validation.py --stage=1 --validation-level=FAST

# 3. 查看驗證快照
ls -la data/validation_snapshots/
```

## 🔗 相關文檔

- **📊 技術文檔索引**: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
- **🛡️ 驗證框架**: [validation_framework_overview.md](validation_framework_overview.md)  
- **📈 數據處理流程**: [data_processing_flow.md](data_processing_flow.md)
- **⚙️ 階段詳細說明**: [stages/STAGES_OVERVIEW.md](stages/STAGES_OVERVIEW.md)

## 📞 技術支援

如有問題，請查看：
1. **本使用指南** - 涵蓋 90% 常見使用場景
2. **故障排除區段** - 解決常見問題
3. **相關技術文檔** - 深入理解系統架構

---

**⚡ 核心理念**: 簡單易用 > 功能完整 > 高性能優化  
**🎯 設計目標**: 3分鐘上手、5分鐘完整處理、零配置使用

*最後更新: 2025-09-11 - v1.0*