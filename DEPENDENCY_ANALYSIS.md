# NetStack 依賴分析報告

## 📊 分析摘要

**分析時間**: 2025-01-10  
**分析範圍**: `/home/sat/ntn-stack/netstack/`  
**總 Python 檔案**: 174 個檔案  

## 🚨 主要發現

### 1. 大量未使用代碼 (Vulture 分析)
- **未使用變數**: 300+ 個
- **未使用函數**: 50+ 個 
- **未使用類別**: 20+ 個大型類別
- **未使用導入**: 100+ 個導入語句

### 2. 過度分散的目錄結構
```
❌ 單檔案目錄問題:
src/algorithms/access/          → 1 個檔案 (fast_access_decision.py, 1062 行)
src/algorithms/handover/        → 1 個檔案 (fine_grained_decision.py, 718 行)  
src/algorithms/prediction/      → 1 個檔案 (orbit_prediction.py, 1188 行)
src/services/handover/          → 1 個檔案 (handover_event_trigger_service.py, 417 行)
src/services/research/          → 1 個檔案 (threegpp_event_generator.py, 609 行)

✅ 合理組織目錄:
src/algorithms/sync/            → 2 個檔案 (state_synchronization.py + distributed_sync.py)
src/algorithms/ml/              → 2 個檔案 (prediction_models.py + __init__.py)
src/services/satellite/         → 22 個檔案 (良好組織)
```

### 3. 雙重架構問題
- **netstack_api/** (86 檔案): 傳統 FastAPI 架構
- **src/** (49 檔案): 學術研究架構  
- **交叉引用極少**: 僅 1 處 netstack_api 引用 src 代碼

## 🔍 詳細分析

### A. 超大檔案分析 (>1000 行)
| 檔案路徑 | 行數 | 狀態 | 建議 |
|----------|------|------|------|
| `netstack_api/services/measurement_event_service.py` | 1470 | 活躍使用 | 保留，考慮分拆 |
| `netstack_api/services/unified_metrics_collector.py` | 1397 | **未使用** | 🗑️ 建議移除 |
| `src/algorithms/prediction/orbit_prediction.py` | 1188 | 核心算法 | 保留，重構 |
| `src/algorithms/ml/prediction_models.py` | 1117 | 核心算法 | 保留，重構 |
| `netstack_api/services/orbit_calculation_engine.py` | 1090 | 活躍使用 | 保留 |
| `netstack_api/services/handover_measurement_service.py` | 1080 | **部分未使用** | 需審查 |
| `src/algorithms/access/fast_access_decision.py` | 1062 | 核心算法 | 保留，重構 |

### B. 大型未使用類別 (Vulture 60%+ 信心度)
| 類別名稱 | 檔案位置 | 行數 | 建議 |
|----------|----------|------|------|
| `EnhancedSynchronizedAlgorithm` | `enhanced_synchronized_algorithm.py` | 886 行 | 🗑️ 移除 |
| `FineGrainedSyncService` | `fine_grained_sync_service.py` | 785 行 | 🗑️ 移除 |
| `SatelliteGnbMappingService` | `satellite_gnb_mapping_service.py` | 716 行 | 🗑️ 移除 |
| `SionnaUERANSIMIntegrationService` | `sionna_ueransim_integration_service.py` | 531 行 | 🗑️ 移除 |
| `AlgorithmEcosystemManager` | `ecosystem_manager.py` | 514 行 | 🗑️ 移除 |
| `UnifiedMetricsCollector` | `unified_metrics_collector.py` | 297 行 | 🗑️ 移除 |

### C. 過度分散問題統計
| 目錄 | 檔案數 | 總行數 | 問題 | 建議操作 |
|------|--------|--------|------|----------|
| `src/algorithms/access/` | 1 | 1062 | 過度分散 | 🔄 合併到 `src/algorithms/` |
| `src/algorithms/handover/` | 1 | 718 | 過度分散 | 🔄 合併到 `src/algorithms/` |
| `src/algorithms/prediction/` | 1 | 1188 | 過度分散 | 🔄 合併到 `src/algorithms/` |
| `src/services/handover/` | 1 | 417 | 過度分散 | 🔄 合併到 `src/services/` |
| `src/services/research/` | 1 | 609 | 過度分散 | 🔄 合併到 `src/services/` |

## 🎯 核心模組識別

### ✅ 高價值保留模組
**演算法核心** (src/algorithms/):
- `fast_access_decision.py` (1062 行) - Fast Access Prediction 算法
- `fine_grained_decision.py` (718 行) - Fine-Grained Handover 算法  
- `orbit_prediction.py` (1188 行) - SGP4 軌道預測
- `prediction_models.py` (1117 行) - 機器學習預測模型

**服務核心** (src/services/satellite/):
- 22 個檔案，組織良好，核心衛星功能

**API 核心** (netstack_api/):
- `measurement_event_service.py` (1470 行) - 測量事件服務
- `orbit_calculation_engine.py` (1090 行) - 軌道計算引擎

### 🗑️ 建議移除模組
**大型未使用服務**:
- `unified_metrics_collector.py` (1397 行) - 完全未使用
- `enhanced_synchronized_algorithm.py` (1029 行) - 實驗性代碼，未使用
- `fine_grained_sync_service.py` (890 行) - 重複功能
- `satellite_gnb_mapping_service.py` (大型類別未使用)

## 📈 預期改善效果

### 代碼減量估計
- **移除檔案數**: ~15-20 個檔案
- **減少代碼行數**: ~8,000-10,000 行 (約 13-16%)
- **減少目錄層級**: 5 個過度分散目錄 → 合併

### 結構改善
- **單檔案目錄**: 5 個 → 0 個  
- **核心算法集中**: 分散在 5 個目錄 → 集中在 1 個目錄
- **依賴關係簡化**: 雙重架構 → 統一架構

## 🚨 風險評估

### 低風險移除
- Vulture 90%+ 信心度的未使用代碼
- 零引用的大型類別
- 明顯的實驗性代碼

### 中風險移除  
- Vulture 60-89% 信心度的代碼
- 部分使用的大型服務
- 複雜的依賴關係

### 需要確認
- 配置相關的未使用變數
- API 端點的實際使用情況
- 測試代碼的依賴關係

---

**下一步**: 基於此分析生成具體的清理提案，等待用戶確認後執行重構操作。