
# 🧹 完整舊API清除清單

## 🔴 **階段1：修復當前路由器邏輯 (緊急)**

### satellite_ops_router.py - 需要完全重寫
- ❌ **當前狀況**：我的修改未生效，仍調用`_call_simworld_satellites_api`
- ✅ **修復動作**：確保API端點真正使用Phase0或新預處理系統
- 🎯 **檔案位置**：`netstack_api/routers/satellite_ops_router.py`

## 🟡 **階段2：服務層清理 (需評估)**

### 核心服務檔案 (8個)：
1. `services/simworld_tle_bridge_service.py` - 1014行主要橋接服務
2. `services/satellite_gnb_mapping_service.py` - 衛星gNB映射 (🔴高風險)
3. `services/paper_synchronized_algorithm.py` - 論文算法
4. `services/fast_access_prediction_service.py` - 快速訪問預測
5. `services/algorithm_integration_bridge.py` - 算法整合橋接  
6. `services/sionna_integration_service.py` - Sionna整合
7. `services/sionna_ueransim_integration_service.py` - Sionna-UERANSIM
8. `services/oneweb_satellite_gnb_service.py` - OneWeb服務

### 監控服務：
9. `services/unified_metrics_collector.py` - 包含SimWorld監控

## 🟢 **階段3：配置清理 (安全)**

### 配置檔案 (4個)：
1. `algorithm_ecosystem_config.yml` (2個位置)
2. `compose/core.yaml` - SIMWORLD_API_URL環境變數
3. `compose/core-simple.yaml` - SIMWORLD_API_URL環境變數

## ⚡ **建議執行順序**：

### 步驟1：立即修復路由器 (緊急)
- 確保`visible_satellites`端點使用Phase0數據
- 移除`_call_simworld_satellites_api`調用

### 步驟2：評估服務依賴 (1-2天)
- 逐一檢查8個服務是否仍在使用
- 為核心功能提供替代實現

### 步驟3：安全清理配置 (最後)
- 移除配置檔案中的SimWorld URL
- 清理環境變數

## 🚨 **風險提醒**：

1. **不要同時移除多個服務** - 可能導致系統崩潰
2. **先確認Phase0完全替代** - 確保無功能遺失  
3. **保留備份** - 每次清理前備份檔案
4. **分階段測試** - 每步驟後驗證系統正常


