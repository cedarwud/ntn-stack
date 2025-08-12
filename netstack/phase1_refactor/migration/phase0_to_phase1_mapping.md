# 📋 Phase 0 到 Phase 1 代碼映射指南

**版本**: v1.0.0  
**建立日期**: 2025-08-12  
**目的**: 指導將現有 phase0 代碼重新組織到正確的 Phase 1 結構

## 🎯 重新組織原則

### 核心理解
- **原 phase0** = 實際上就是 Phase 1 的建構時預計算
- **新 Phase 1** = 完整的全量衛星軌道計算系統
- **不需要** 獨立的 phase0，所有功能整合到 Phase 1

## 📁 文件映射表

### 🔄 主要處理文件

| 原始文件 | 新位置 | 映射說明 |
|---------|--------|---------|
| `build_with_phase0_data_refactored.py` | `03_processing_pipeline/phase1_coordinator.py` | 主要協調邏輯 |
| `build_with_phase0_data_refactored.py` | `01_data_source/tle_loader.py` | TLE 載入邏輯 |
| `build_with_phase0_data_refactored.py` | `02_orbit_calculation/sgp4_engine.py` | SGP4 計算邏輯 |

### 🛠️ SGP4 實現文件

| 原始文件 | 新位置 | 映射說明 |
|---------|--------|---------|
| `simworld/backend/app/services/sgp4_calculator.py` | `02_orbit_calculation/sgp4_engine.py` | 整合 SGP4 實現 |
| `netstack/src/algorithms/orbit_prediction.py` | `02_orbit_calculation/orbit_propagator.py` | 軌道傳播功能 |
| `netstack/netstack_api/services/orbit_calculation_engine.py` | `02_orbit_calculation/sgp4_engine.py` | 計算引擎功能 |

### 📊 API 和路由文件

| 原始文件 | 新位置 | 映射說明 |
|---------|--------|---------|
| `simple_satellite_router.py` | `04_output_interface/phase1_api.py` | Phase 1 統一 API |
| `coordinate_orbit_endpoints.py` | `04_output_interface/phase1_api.py` | 座標軌道端點整合 |
| `satellite_ops_router.py` | `04_output_interface/phase2_interface.py` | Phase 2 接口規範 |

### 📋 配置文件

| 原始文件 | 新位置 | 映射說明 |
|---------|--------|---------|
| `config/unified_satellite_config.py` | `config/phase1_config.yaml` | 統一配置轉換 |
| `config/satellite_config.py` | `config/constellation_config.yaml` | 星座特定配置 |

## 🔧 關鍵代碼片段映射

### 1. TLE 數據載入

**原始代碼** (`build_with_phase0_data_refactored.py:137-168`):
```python
logger.info("  1.2 載入原始衛星數據...")
# 收集所有原始衛星數據
all_raw_satellites = {}
for constellation in self.supported_constellations:
    constellation_data = scan_result['constellations'].get(constellation, {})
    
    if constellation_data.get('files', 0) == 0:
        logger.warning(f"      跳過 {constellation}: 無可用數據")
        continue
```

**新位置** (`01_data_source/tle_loader.py:TLELoader.load_all_tle_data()`):
```python
def load_all_tle_data(self) -> TLELoadResult:
    logger.info("開始載入所有 TLE 數據...")
    
    all_records = []
    constellation_counts = {}
    errors = []
    
    # 掃描檔案
    tle_files = self.scan_tle_files()
```

### 2. SGP4 計算

**原始代碼** (`build_with_phase0_data_refactored.py:447-580`):
```python
logger.info(f"    執行 {constellation_name} SGP4軌道計算: {len(satellite_pool)} 顆衛星")

# 執行完整 SGP4 軌道計算
constellation_orbit_data = self._execute_sgp4_orbit_calculation(
    constellation_name, satellite_pool
)
```

**新位置** (`02_orbit_calculation/sgp4_engine.py:SGP4Engine.batch_calculate()`):
```python
def batch_calculate(self, satellite_ids: List[str], 
                   timestamps: List[datetime]) -> SGP4BatchResult:
    logger.info(f"開始批量計算: {len(satellite_ids)} 顆衛星 × {len(timestamps)} 時間點")
```

### 3. API 端點

**原始代碼** (`simple_satellite_router.py:91-164`):
```python
def get_phase0_satellite_data(constellation: str, count: int = 200) -> List[Dict]:
    """
    從Phase0預處理系統獲取實際衛星數據
    使用150+50顆真實衛星取代舊的15顆模擬數據 (基於SGP4全量計算優化配置)
    """
```

**新位置** (`04_output_interface/phase1_api.py:get_satellite_orbits()`):
```python
def get_satellite_orbits(constellation: str, count: int = 200) -> List[Dict]:
    """
    從 Phase 1 軌道數據庫獲取衛星軌道數據
    使用完整 SGP4 計算結果，支援 8,715 顆衛星全量數據
    """
```

## 🚫 需要移除的過時概念

### 過時命名和文件
```bash
# 需要重新命名或移除的文件和概念
❌ phase0_precomputed_orbits.json -> ✅ phase1_orbit_database.json
❌ phase0_preprocessing -> ✅ phase1_sgp4_calculation
❌ 150+50 配置 -> ✅ 全量 8,715 顆衛星
❌ enhanced_satellite_data.json -> ✅ 完全移除 (假數據)
```

### 過時函數和變量名
```python
# 需要重新命名
❌ get_phase0_satellite_data() -> ✅ get_satellite_orbits()
❌ phase0_loader -> ✅ phase1_coordinator
❌ phase0_preprocessing_150_50 -> ✅ phase1_sgp4_full_calculation
❌ enable_sgp4 -> ✅ 默認啟用，不需要配置 (符合 CLAUDE.md)
```

## 📋 遷移檢查清單

### Stage 1: 代碼重新組織
- [ ] 將 TLE 載入邏輯提取到 `01_data_source/tle_loader.py`
- [ ] 將 SGP4 計算邏輯提取到 `02_orbit_calculation/sgp4_engine.py`
- [ ] 將主要協調邏輯移動到 `03_processing_pipeline/phase1_coordinator.py`
- [ ] 創建統一的 Phase 1 API 在 `04_output_interface/phase1_api.py`

### Stage 2: 命名規範統一
- [ ] 重新命名所有 `phase0_*` 變量為 `phase1_*`
- [ ] 更新 API 響應中的 `data_source` 欄位
- [ ] 統一使用 "Phase 1" 而非 "phase0" 在日誌和文檔中
- [ ] 移除所有 150+50 相關的硬編碼配置

### Stage 3: 功能驗證
- [ ] 確認 TLE 載入功能正常
- [ ] 驗證 SGP4 計算結果一致性
- [ ] 測試 Phase 1 協調器完整流程
- [ ] 驗證 Phase 2 接口兼容性

### Stage 4: 配置遷移
- [ ] 將 `unified_satellite_config.py` 轉換為 YAML 格式
- [ ] 創建 `phase1_config.yaml` 主配置文件
- [ ] 建立 `constellation_config.yaml` 星座配置
- [ ] 移除過時的配置選項

## 🔄 數據流向變更

### 原始數據流 (混亂)
```
TLE Files -> build_with_phase0_data_refactored.py -> phase0_precomputed_orbits.json
          -> simple_satellite_router.py -> API Response (phase0_preprocessing_150_50)
```

### 新數據流 (清晰)
```
TLE Files -> tle_loader.py -> sgp4_engine.py -> phase1_coordinator.py 
          -> phase1_orbit_database.json -> phase1_api.py 
          -> API Response (phase1_sgp4_full_calculation)
```

## ⚠️ 注意事項

### 1. 兼容性考慮
- Phase 2 可能依賴某些 phase0 的數據格式
- API 端點的改變需要通知前端
- Docker Volume 中的數據路徑可能需要更新

### 2. 性能影響
- 新架構應該保持相同或更好的性能
- 批量計算邏輯需要優化
- 記憶體使用模式可能有變化

### 3. 測試要求
- 所有重新組織的代碼都需要完整測試
- 確保 SGP4 計算結果數值一致性
- 驗證 Phase 1 → Phase 2 數據傳遞正確性

## 📞 遷移支援

**遷移過程中如果遇到問題**:
1. 檢查 `phase1_refactor/docs/` 中的技術文檔
2. 參考 `05_integration/integration_tests.py` 中的測試用例
3. 查看 `migration/api_changes.md` 了解 API 變更詳情

---

**目標**: 將分散、混亂的 phase0 代碼重新組織為清晰、模組化的 Phase 1 架構，為整個 NTN Stack 提供可靠的軌道數據基礎。