# 🏷️ Phase 0 文件功能分析與重命名計劃

## 📋 Phase 0 文件功能分析結果

### 1. 核心處理器文件

#### `build_with_phase0_data_refactored.py` 
- **實際功能**: Phase 1 的主要處理器 (含完整 SGP4 軌道計算)
- **重命名為**: `build_with_phase1_data.py`
- **理由**: 文件內包含 `_execute_phase1_orbit_calculation()` 方法，是真正的 Phase 1 實現

#### `phase0_integration.py`
- **實際功能**: 獨立的 Starlink 數據下載與預篩選工具
- **重命名為**: `starlink_analysis_toolkit.py` 
- **理由**: 這是專門的 Starlink 分析工具，不是主要處理流程的一部分

#### `generate_layered_phase0_data.py`
- **實際功能**: 分層仰角門檻數據生成器
- **重命名為**: `generate_layered_elevation_data.py`
- **理由**: 按功能命名更清晰，避免與 Phase 概念混淆

### 2. 數據文件

#### `phase0_precomputed_orbits.json`
- **實際功能**: Phase 1 的預計算軌道數據
- **重命名為**: `phase1_precomputed_orbits.json`
- **理由**: 這是 Phase 1 處理的結果數據

#### `phase0_data_summary.json`
- **實際功能**: Phase 1 處理結果的摘要
- **重命名為**: `phase1_data_summary.json`
- **理由**: 摘要對應的是 Phase 1 的處理統計

#### `phase0_build_config.json`
- **實際功能**: Phase 1 建構配置
- **重命名為**: `phase1_build_config.json`
- **理由**: 配置對應的是 Phase 1 建構過程

#### `layered_phase0/`
- **實際功能**: 分層仰角數據目錄
- **重命名為**: `layered_elevation_data/`
- **理由**: 按功能命名，避免 Phase 混淆

### 3. 環境配置

#### `phase0.env`
- **實際功能**: Phase 1 環境配置變數
- **重命名為**: `phase1.env`
- **理由**: 配置對應的是 Phase 1 的環境設定

## 🗂️ 代碼引用更新

### API 路由器更新

#### `coordinate_orbit_endpoints.py`
```python
# 舊的引用
phase0_loader = Phase0DataLoader()
/app/data/phase0_precomputed_orbits.json

# 新的引用  
phase1_loader = Phase1DataLoader()
/app/data/phase1_precomputed_orbits.json
```

#### `simple_satellite_router.py`
```python
# 舊的函數名
def get_phase0_satellite_data(constellation: str, count: int = 200)

# 新的函數名
def get_phase1_satellite_data(constellation: str, count: int = 200)
```

### 配置管理更新

#### `config_manager.py`
```python
# 舊的配置鍵
"phase0_data_dir": self._resolve_data_path(...)

# 新的配置鍵
"phase1_data_dir": self._resolve_data_path(...)
```

## 📁 phase1_refactor/ 文件移動規劃

### ❌ 需要清理的文件 (不應該在重構計劃資料夾)
```
phase1_refactor/01_data_source/tle_loader.py         → 移動到 netstack/src/services/satellite/
phase1_refactor/01_data_source/satellite_catalog.py  → 移動到 netstack/src/services/satellite/
phase1_refactor/01_data_source/data_validation.py    → 移動到 netstack/src/services/satellite/
phase1_refactor/02_orbit_calculation/sgp4_engine.py  → 移動到 netstack/src/services/satellite/
phase1_refactor/02_orbit_calculation/orbit_propagator.py → 移動到 netstack/src/services/satellite/
phase1_refactor/03_processing_pipeline/phase1_coordinator.py → 移動到 netstack/docker/
phase1_refactor/04_output_interface/phase1_api.py    → 移動到 netstack/netstack_api/routers/
```

### ✅ 應該保留的文件 (重構計劃文檔)
```
phase1_refactor/README.md                            → 更新為重構計劃說明
phase1_refactor/PHASE0_TO_PHASE1_UNIFICATION_PLAN.md → 保留
phase1_refactor/FILE_RENAMING_PLAN.md               → 本文件
phase1_refactor/MIGRATION_ROADMAP.md                → 新建遷移路線圖
```

## 🚀 具體實施步驟

### Step 1: 備份當前系統
```bash
git branch backup-before-phase0-renaming
git add -A
git commit -m "Backup before Phase 0 → Phase 1 renaming"
```

### Step 2: 核心文件重命名
```bash
# 主要處理器
mv netstack/docker/build_with_phase0_data_refactored.py \
   netstack/docker/build_with_phase1_data.py

# 獨立工具重命名
mv netstack/src/services/satellite/phase0_integration.py \
   netstack/src/services/satellite/starlink_analysis_toolkit.py

# 分層數據生成器
mv netstack/generate_layered_phase0_data.py \
   netstack/generate_layered_elevation_data.py
```

### Step 3: 數據文件重命名
```bash
# 在容器內部，這些文件路徑會在運行時重新生成
# 需要更新所有引用這些文件的代碼
```

### Step 4: 代碼引用批量更新
```bash
# 批量替換 Python 文件中的引用
find netstack/ -name "*.py" -exec sed -i 's/phase0_/phase1_/g' {} +
find netstack/ -name "*.py" -exec sed -i 's/Phase0/Phase1/g' {} +
```

### Step 5: 配置檔案更新
```bash
# 更新 Docker compose 配置
# 更新環境變數檔案
# 更新 API 路由配置
```

## ⚠️ 風險評估

### 高風險變更
1. **build_with_phase0_data_refactored.py** → 系統核心處理器
2. **API 端點路徑變更** → 可能影響現有 API 調用
3. **數據文件路徑變更** → 需要確保所有引用同步更新

### 低風險變更  
1. **phase0_integration.py** → 獨立工具，影響範圍小
2. **generate_layered_phase0_data.py** → 公用程式，較少依賴

## 📋 驗證清單

完成重命名後需要驗證：

- [ ] 所有 phase0 引用已更新為對應的正確命名
- [ ] API 端點正常響應
- [ ] 數據處理流程正常運作
- [ ] Docker 容器正常啟動
- [ ] 單元測試全部通過
- [ ] phase1_refactor/ 只包含計劃文檔，無實際代碼

---

**此計劃將為每個文件提供功能性的正確命名，消除 phase0 造成的混淆。**