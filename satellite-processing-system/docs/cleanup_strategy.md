# 六階段處理器清理策略文檔

## 📋 概述

satellite-processing-system 採用統一的智能清理系統，確保各階段輸出檔案的正確清理，避免時間戳不一致和數據混亂問題。

## 🏗️ 清理架構

### 核心清理系統
- **文件位置**: `src/shared/cleanup_manager.py`
- **主要類別**: `UnifiedCleanupManager`
- **設計模式**: 單例模式，提供全域一致的清理行為

### 三種清理模式

1. **🔄 完整管道清理** (`cleanup_full_pipeline`)
   - 清理所有六個階段的輸出和驗證快照
   - 適用於完整管道執行前的環境重置

2. **🎯 單一階段清理** (`cleanup_single_stage`)
   - 只清理指定階段的輸出和驗證快照
   - 適用於單一階段測試和開發

3. **🧠 智能自動清理** (`auto_cleanup`)
   - 根據執行環境自動選擇清理策略
   - 支持執行模式檢測和智能決策

## 📁 清理範圍

### 每個階段清理的內容

| 階段 | 清理目錄 | 驗證快照 |
|------|----------|----------|
| Stage 1 | `data/outputs/stage1/` | `data/validation_snapshots/stage1_validation.json` |
| Stage 2 | `data/outputs/stage2/` | `data/validation_snapshots/stage2_validation.json` |
| Stage 3 | `data/outputs/stage3/` | `data/validation_snapshots/stage3_validation.json` |
| Stage 4 | `data/outputs/stage4/` | `data/validation_snapshots/stage4_validation.json` |
| Stage 5 | `data/outputs/stage5/` | `data/validation_snapshots/stage5_validation.json` |
| Stage 6 | `data/outputs/stage6/` | `data/validation_snapshots/stage6_validation.json` |

### ✅ 清理項目
- **輸出目錄**: 各階段的 `data/outputs/stage{N}/` 完整目錄
- **驗證快照**: `data/validation_snapshots/stage{N}_validation.json` 檔案

### ❌ 不清理項目
- **TLE源數據**: `data/tle_data/` 目錄（作為系統輸入）
- **配置文件**: `config/` 目錄
- **日誌文件**: `logs/` 目錄
- **Docker相關**: 未映射到主機的容器內部文件

## 🔧 智能目錄清理邏輯

### 清理流程
```python
for dir_path in target.directories:
    if self._remove_directory(dir_path):          # 1. 優先直接刪除
        cleaned_dirs += 1
    else:
        # 2. 備用策略：逐步清理
        cleaned_count = self._cleanup_directory_contents(dir_path)
        cleaned_files += cleaned_count
        # 3. 移除空目錄
        if self._remove_empty_directory(dir_path):
            cleaned_dirs += 1
```

### 清理策略優勢

1. **高效率**: 優先使用 `shutil.rmtree()` 直接刪除整個目錄
2. **容錯性**: 權限問題時使用逐個文件清理的備用方案
3. **完整性**: 遞迴處理嵌套目錄，確保所有檔案都被清理
4. **智能化**: 自動移除空的子目錄，保持目錄結構整潔

### 三步驟清理過程

#### 步驟 1: 直接目錄刪除
```python
def _remove_directory(self, dir_path: str) -> bool:
    """嘗試直接刪除整個目錄"""
    try:
        shutil.rmtree(path)
        return True
    except Exception:
        return False  # 進入備用模式
```

#### 步驟 2: 文件逐一清理
```python
def _cleanup_directory_contents(self, dir_path: str) -> int:
    """清理目錄內的所有檔案"""
    for file_path in path.rglob("*"):
        if file_path.is_file():
            file_path.unlink()
```

#### 步驟 3: 空目錄遞迴移除
```python
def _remove_empty_directory(self, dir_path: str) -> bool:
    """遞迴移除空目錄"""
    # 先處理所有子目錄（深度優先）
    for subdir in sorted(path.rglob('*'), reverse=True):
        if subdir.is_dir() and not any(subdir.iterdir()):
            subdir.rmdir()

    # 最後處理主目錄
    if not any(path.iterdir()):
        path.rmdir()
        return True
```

## 🎯 執行模式檢測

### 智能模式檢測
```python
def detect_execution_mode(self) -> Literal["full_pipeline", "single_stage"]:
    # 1. 檢查環境變數
    if os.getenv('PIPELINE_MODE') == 'full':
        return "full_pipeline"

    # 2. 檢查調用堆棧
    if 'run_six_stages' in caller_filename:
        return "full_pipeline"

    # 3. 預設為單一階段
    return "single_stage"
```

### 執行策略

#### 完整管道模式
- **階段 1**: 執行完整清理（清理所有 6 個階段）
- **階段 2-6**: 跳過清理，保護數據流完整性

#### 單一階段模式
- **任何階段**: 使用智能清理策略 `cleanup_from_stage(current_stage)`
- 清理當前階段及其後續階段，保留前面階段作為輸入依賴

## 🚀 使用方法

### 基本用法
```python
from shared.cleanup_manager import get_cleanup_manager

# 獲取清理管理器
cleanup_manager = get_cleanup_manager()

# 自動智能清理
result = cleanup_manager.auto_cleanup(current_stage=3)

# 完整管道清理
result = cleanup_manager.cleanup_full_pipeline()

# 單一階段清理
result = cleanup_manager.cleanup_single_stage(3)

# 從指定階段開始清理
result = cleanup_manager.cleanup_from_stage(3)  # 清理階段3-6
```

### 便捷函數
```python
from shared.cleanup_manager import auto_cleanup, cleanup_all_stages

# 便捷自動清理
auto_cleanup(current_stage=2)

# 便捷完整清理
cleanup_all_stages()
```

## 📊 清理結果

### 返回格式
```python
{
    "files": 15,      # 清理的檔案數量
    "directories": 3  # 清理的目錄數量
}
```

### 日誌輸出
```
🗑️ 執行完整管道清理（方案一）
==================================================
  ✅ 已刪除: data/validation_snapshots/stage1_validation.json (0.1 MB)
  🗂️ 已移除目錄: data/outputs/stage1 (25 個檔案)
  ✅ 已刪除: data/validation_snapshots/stage2_validation.json (0.2 MB)
  🗂️ 已移除目錄: data/outputs/stage2 (12 個檔案)
==================================================
🗑️ 完整管道清理完成: 2 檔案, 6 目錄
```

## ⚙️ 配置

### 清理目標配置
```python
self.STAGE_CLEANUP_TARGETS = {
    1: CleanupTarget(
        stage=1,
        output_files=[],  # 不清理單個檔案，統一清理整個目錄
        validation_file="data/validation_snapshots/stage1_validation.json",
        directories=["data/outputs/stage1"]
    ),
    # ... 其他階段配置
}
```

### 環境變數控制
```bash
# 強制完整管道模式
export PIPELINE_MODE=full

# 強制單一階段模式
export PIPELINE_MODE=single
```

## 🔍 故障排除

### 常見問題

1. **權限不足**
   - 現象：目錄無法直接刪除
   - 解決：自動進入逐檔案清理模式

2. **檔案被鎖定**
   - 現象：部分檔案無法刪除
   - 解決：記錄警告並繼續清理其他檔案

3. **目錄非空**
   - 現象：空目錄檢測失敗
   - 解決：遞迴檢查所有子目錄

### 調試方法
```python
# 啟用詳細日誌
import logging
logging.getLogger('cleanup_manager').setLevel(logging.DEBUG)

# 檢查清理狀態
cleanup_manager = get_cleanup_manager()
mode = cleanup_manager.detect_execution_mode()
print(f"檢測到執行模式: {mode}")
```

## 📈 性能考量

### 優化策略
- **批量操作**: 優先使用 `shutil.rmtree()` 進行批量刪除
- **失敗快速回退**: 檢測到權限問題立即切換到備用策略
- **記憶體效率**: 使用生成器遍歷大型目錄結構
- **日誌適度**: 重要操作記錄，避免過度日誌影響性能

### 典型性能
- **小型目錄** (< 100 檔案): < 1 秒
- **中型目錄** (100-1000 檔案): 1-5 秒
- **大型目錄** (> 1000 檔案): 5-30 秒

## 🔒 安全考量

### 安全措施
- **路徑驗證**: 只清理預定義的安全路徑
- **容器隔離**: 在 Docker 容器內執行，限制影響範圍
- **備份建議**: 重要數據建議在清理前備份
- **權限最小化**: 只有清理操作的最小必要權限

---

## 📝 更新日誌

### v2.0.0 (當前版本)
- ✅ 簡化清理範圍：只清理 outputs 和 validation
- ✅ 移除 TDD 相關檔案清理
- ✅ 智能目錄清理策略
- ✅ 遞迴空目錄處理
- ✅ 完整測試覆蓋

### v1.0.0 (舊版本)
- 複雜的多目錄清理
- TDD 整合文件清理
- 硬編碼清理路徑

---

*此文檔最後更新: 2025-09-15*