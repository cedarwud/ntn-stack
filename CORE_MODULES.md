# NetStack 核心模組清單

## 🎯 核心模組分類

基於依賴分析和功能審計，以下是建議保留和重構的核心模組：

## 📚 **Tier 1: 絕對核心** (必須保留)

### 🔬 算法核心
| 模組 | 當前位置 | 行數 | 重構後位置 | 重要性 |
|------|----------|------|------------|---------|
| Fast Access Decision | `src/algorithms/access/fast_access_decision.py` | 1062 | `src/algorithms/fast_access_decision.py` | ⭐⭐⭐ 論文核心算法 |
| Fine-Grained Handover | `src/algorithms/handover/fine_grained_decision.py` | 718 | `src/algorithms/fine_grained_decision.py` | ⭐⭐⭐ 論文核心算法 |
| Orbit Prediction | `src/algorithms/prediction/orbit_prediction.py` | 1188 | `src/algorithms/orbit_prediction.py` | ⭐⭐⭐ SGP4 軌道預測 |
| ML Prediction Models | `src/algorithms/ml/prediction_models.py` | 1117 | `src/algorithms/ml_prediction_models.py` | ⭐⭐⭐ 機器學習模型 |
| State Synchronization | `src/algorithms/sync/state_synchronization.py` | 1016 | `src/algorithms/state_synchronization.py` | ⭐⭐ 狀態同步算法 |
| Distributed Sync | `src/algorithms/sync/distributed_sync.py` | 781 | `src/algorithms/distributed_sync.py` | ⭐⭐ 分散式同步 |

### 🛰️ 衛星服務核心
| 模組 | 當前位置 | 行數 | 重構後位置 | 重要性 |
|------|----------|------|------------|---------|
| Satellite Services | `src/services/satellite/` (22 files) | ~8000+ | `src/satellite/` | ⭐⭐⭐ 衛星核心功能集 |
| TLE Data Management | `src/services/satellite/local_tle_loader.py` | 468 | `src/satellite/tle_management.py` | ⭐⭐⭐ TLE 數據管理 |
| Orbit Calculation | `src/services/satellite/coordinate_specific_orbit_engine.py` | 850 | `src/satellite/orbit_engine.py` | ⭐⭐⭐ 軌道計算引擎 |

### 🌐 API 核心
| 模組 | 當前位置 | 行數 | 重構後位置 | 重要性 |
|------|----------|------|------------|---------|
| Measurement Event Service | `netstack_api/services/measurement_event_service.py` | 1470 | `src/api/measurement_service.py` | ⭐⭐⭐ 測量事件核心 |
| Orbit Calculation Engine | `netstack_api/services/orbit_calculation_engine.py` | 1090 | `src/api/orbit_service.py` | ⭐⭐⭐ 軌道計算服務 |
| Health Service | `netstack_api/services/health_service.py` | 200 | `src/api/health_service.py` | ⭐⭐ 健康檢查 |

## 📊 **Tier 2: 重要支援** (保留但需重構)

### 🔧 工具和配置
| 模組 | 當前位置 | 重構後位置 | 操作 |
|------|----------|------------|------|
| Satellite Config | `config/satellite_config.py` | `src/config/satellite_config.py` | 清理未使用變數 |
| Database Connection | `netstack_api/services/database_connection_manager.py` | `src/infrastructure/database.py` | 重構為依賴注入 |
| Event Bus Service | `netstack_api/services/event_bus_service.py` | `src/infrastructure/event_bus.py` | 簡化並重構 |

### 📡 協議和通信
| 模組 | 當前位置 | 重構後位置 | 操作 |
|------|----------|------------|------|
| SIB19 Broadcast | `src/protocols/sib/sib19_broadcast.py` | `src/protocols/sib19_broadcast.py` | 保留，移除嵌套目錄 |
| NTN RRC Procedures | `src/protocols/rrc/ntn_procedures.py` | `src/protocols/ntn_rrc_procedures.py` | 保留，移除嵌套目錄 |
| Time Frequency Sync | `src/protocols/sync/time_frequency_sync.py` | `src/protocols/time_frequency_sync.py` | 保留，移除嵌套目錄 |

## 🔄 **Tier 3: 條件保留** (需要用戶確認)

### ❓ 待確認模組
| 模組 | 當前位置 | 行數 | 狀態 | 建議 |
|------|----------|------|------|------|
| Handover Measurement Service | `netstack_api/services/handover_measurement_service.py` | 1080 | Vulture 報告部分未使用 | 🤔 需用戶確認 |
| Batch Processor | `netstack_api/services/batch_processor.py` | 400 | 不確定使用情況 | 🤔 需用戶確認 |
| Handover Event Trigger | `src/services/handover/handover_event_trigger_service.py` | 417 | 單檔案目錄 | 🤔 移動或刪除？ |
| ThreeGPP Event Generator | `src/services/research/threegpp_event_generator.py` | 609 | 研究代碼 | 🤔 保留或移除？ |

## 🗑️ **Tier 4: 建議移除** (高信心度)

### ❌ 大型未使用類別 (Vulture 60%+ 信心度)
| 類別 | 檔案 | 行數 | 移除原因 |
|------|------|------|----------|
| `EnhancedSynchronizedAlgorithm` | `enhanced_synchronized_algorithm.py` | 1029 | 完全未使用 |
| `UnifiedMetricsCollector` | `unified_metrics_collector.py` | 1397 | 完全未使用 |
| `FineGrainedSyncService` | `fine_grained_sync_service.py` | 890 | 功能重複 |
| `SatelliteGnbMappingService` | `satellite_gnb_mapping_service.py` | 768 | 大型類別未使用 |
| `SionnaUERANSIMIntegrationService` | `sionna_ueransim_integration_service.py` | 531 | 集成服務未使用 |
| `AlgorithmEcosystemManager` | `ecosystem_manager.py` | 514 | 生態系統管理未使用 |

### ❌ 實驗性/過時代碼
| 模組 | 移除原因 | 風險級別 |
|------|----------|----------|
| `netstack_api/algorithm_ecosystem/` (全目錄) | 實驗性功能，Vulture 報告大量未使用 | 低風險 |
| Various test/demo functions | 明顯的測試或示範代碼 | 低風險 |
| Unused configuration constants | 300+ 個未使用變數 | 低風險 |

## 📈 重構後的目標結構

### 🎯 新架構層次
```
src/
├── algorithms/                  # 核心算法 (扁平化)
│   ├── fast_access_decision.py
│   ├── fine_grained_decision.py
│   ├── orbit_prediction.py
│   ├── ml_prediction_models.py
│   ├── state_synchronization.py
│   └── distributed_sync.py
├── satellite/                   # 衛星功能 (整合 services/satellite)
│   ├── orbit_engine.py
│   ├── tle_management.py
│   ├── data_processing.py
│   └── measurement_optimizer.py
├── api/                        # API 服務 (整合 netstack_api 核心)
│   ├── measurement_service.py
│   ├── orbit_service.py
│   └── health_service.py
├── protocols/                  # 通信協議 (扁平化)
│   ├── sib19_broadcast.py
│   ├── ntn_rrc_procedures.py
│   └── time_frequency_sync.py
├── infrastructure/             # 基礎設施 (依賴注入友好)
│   ├── database.py
│   ├── event_bus.py
│   └── external_apis.py
├── domain/                     # 領域模型 (新增)
│   ├── satellite.py
│   ├── orbit.py
│   └── measurement_event.py
└── interfaces/                 # 抽象接口 (新增，支援 TDD/BDD)
    ├── repositories.py
    └── services.py
```

## 📊 效果預測

### 📉 代碼減量
- **移除檔案**: ~25 個檔案
- **減少代碼行數**: ~12,000 行 (約 15-19%)
- **簡化目錄**: 從 5 層嵌套 → 2-3 層嵌套

### 📈 品質提升
- **依賴注入**: 支援 mock 和測試
- **單一職責**: 每個模組職責明確
- **扁平化結構**: 減少導入複雜度
- **核心聚焦**: 突出研究核心算法

### 🎯 TDD/BDD 友好
- **可測試**: 依賴注入，純函數偏向
- **可 mock**: 抽象接口清晰
- **組織清晰**: 測試對應關係明確

---

**下一步**: 基於此核心模組清單，生成具體的重構操作提案，等待用戶確認。