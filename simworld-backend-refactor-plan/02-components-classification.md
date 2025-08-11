# SimWorld Backend 組件分類指南

## 🎯 分類標準

### 優先級分類
- **P0 核心**: 與 LEO satellite handover 研究直接相關，必須保留
- **P1 重要**: 支援核心功能或未來研究需要，建議保留  
- **P2 輔助**: 開發支援工具，可選擇性保留
- **P3 移除**: 與研究目標無關，建議移除

### 功能分類
- **🛰️ 衛星相關**: 軌道計算、可見性、切換決策
- **🔬 物理層模擬**: Sionna 相關功能
- **🎨 3D 渲染**: 前端動畫支援
- **⚙️ 系統工具**: 開發和監控工具
- **📱 設備管理**: 地面設備和UAV管理

## 📊 完整組件分類表

### P0 核心組件 (必須保留)

| 檔案路徑 | 功能描述 | 分類 | 保留原因 |
|---------|---------|------|----------|
| `domains/satellite/api/satellite_api.py` | 衛星 API 端點 | 🛰️ 衛星相關 | 核心研究功能 |
| `domains/satellite/api/real_satellite_api.py` | 真實衛星數據 API | 🛰️ 衛星相關 | 真實數據支援 |
| `domains/satellite/services/orbit_service.py` | 軌道計算服務 | 🛰️ 衛星相關 | 軌道傳播算法 |
| `domains/satellite/services/batch_orbit_service.py` | 批量軌道計算 | 🛰️ 衛星相關 | 效能優化 |
| `domains/satellite/services/enhanced_orbit_prediction_service.py` | 增強軌道預測 | 🛰️ 衛星相關 | 預測精度提升 |
| `domains/satellite/services/satellite_cache_service.py` | 衛星數據快取 | 🛰️ 衛星相關 | 效能優化 |
| `domains/satellite/services/real_constellation_service.py` | 真實星座服務 | 🛰️ 衛星相關 | 真實場景模擬 |
| `domains/coordinates/api/coordinate_api.py` | 座標轉換 API | 🛰️ 衛星相關 | 位置計算必需 |
| `domains/coordinates/services/coordinate_service.py` | 座標計算服務 | 🛰️ 衛星相關 | 座標系統轉換 |
| `api/routes/satellite_redis.py` | 衛星 Redis 快取 | 🛰️ 衛星相關 | 數據快取管理 |
| `api/routes/historical_orbits.py` | 歷史軌道數據 | 🛰️ 衛星相關 | 歷史數據支援 |
| `api/routes/unified_timeseries.py` | 統一時間序列 | 🛰️ 衛星相關 | 時間序列分析 |
| `services/distance_calculator.py` | 距離計算服務 | 🛰️ 衛星相關 | 衛星距離計算 |
| `services/sgp4_calculator.py` | SGP4 軌道算法 | 🛰️ 衛星相關 | 標準軌道傳播 |
| `services/historical_orbit_generator.py` | 歷史軌道生成 | 🛰️ 衛星相關 | 歷史數據生成 |
| `services/local_volume_data_service.py` | 本地數據服務 | 🛰️ 衛星相關 | 數據管理 |

### P1 重要組件 (建議保留)

| 檔案路徑 | 功能描述 | 分類 | 保留原因 |
|---------|---------|------|----------|
| `domains/device/api/device_api.py` | 設備管理 API | 📱 設備管理 | 基本的地面設備管理 |
| `domains/device/services/device_service.py` | 設備服務邏輯 | 📱 設備管理 | 基本設備業務邏輯 |
| `domains/simulation/api/simulation_api.py` | 模擬場景 API | 🎨 3D 渲染 | 場景載入，衛星動畫支援 |
| `domains/simulation/services/rendering/rendering_service.py` | 3D 渲染服務 | 🎨 3D 渲染 | 衛星移動渲染 |
| `domains/simulation/services/scene/scene_management_service.py` | 場景管理服務 | 🎨 3D 渲染 | 場景切換管理 |
| `domains/simulation/services/sionna_service.py` | Sionna 整合服務 | 🎨 3D 渲染 | 場景渲染（移除圖表功能） |
| `api/routes/core.py` | 核心路由端點 | 🎨 3D 渲染 | 模型檔案服務 |
| `api/routes/devices_mongodb.py` | 設備 MongoDB API | 📱 設備管理 | 設備數據持久化 |
| `static/models/` | 3D 模型資源 | 🎨 3D 渲染 | 所有 3D 模型（sat.glb, tower.glb, uav.glb, jam.glb） |
| `static/scenes/` | 3D 場景資源 | 🎨 3D 渲染 | 場景模型檔案 |

### P2 輔助組件 (可選保留)

| 檔案路徑 | 功能描述 | 分類 | 考量因素 |
|---------|---------|------|----------|
| `api/routes/health.py` | 健康檢查端點 | ⚙️ 系統工具 | 系統監控需要 |
| `core/lifecycle_manager.py` | 生命週期管理 | ⚙️ 系統工具 | 系統啟動管理 |
| `core/service_registry.py` | 服務註冊中心 | ⚙️ 系統工具 | 服務發現機制 |
| `db/lifespan.py` | 數據庫生命週期 | ⚙️ 系統工具 | 數據庫連接管理 |
| `db/mongodb_config.py` | MongoDB 配置 | ⚙️ 系統工具 | 數據庫配置 |
| `db/redis_client.py` | Redis 客戶端 | ⚙️ 系統工具 | 快取連接管理 |

### P3 移除組件 (建議移除)

| 檔案路徑 | 功能描述 | 分類 | 移除原因 |
|---------|---------|------|----------|
| `api/routes/uav.py` | UAV 追踪 API | 📱 設備管理 | 與研究目標無關 |
| `domains/system/` (完整目錄) | 系統資源監控 | ⚙️ 系統工具 | 與研究目標無關 |
| `domains/wireless/` 中的繪圖功能 | 無線繪圖分析 | 🔬 物理層模擬 | SINR、CFR 等圖表生成功能，非核心演算法 |
| `domains/simulation/services/sionna_service.py` 中的圖表方法 | Sionna 繪圖功能 | 🔬 物理層模擬 | generate_doppler_plots, generate_cfr_plot 等方法 |
| `static/images/` | 分析圖表檔案 | 🔬 物理層模擬 | CFR、SINR、都卜勒等預生成圖表，非 3D 渲染 |
| `services/precision_validator.py` | 精度驗證工具 | ⚙️ 系統工具 | 開發期工具 |
| `services/distance_validator.py` | 距離驗證工具 | ⚙️ 系統工具 | 開發期工具 |
| `services/skyfield_migration.py` | Skyfield 遷移 | ⚙️ 系統工具 | 過時的遷移代碼 |
| `api/v1/distance_validation.py` | 距離驗證 API | ⚙️ 系統工具 | 開發期 API |

## 📋 詳細分析

### 🛰️ 衛星相關組件 (核心保留)

**總計**: 16 個檔案
**狀態**: 全部保留
**重要性**: P0 核心

這些組件構成了 LEO satellite handover 研究的核心基礎設施：

1. **軌道計算**: SGP4 算法、軌道傳播、位置預測
2. **可見性分析**: 衛星可見性判斷、仰角計算
3. **切換決策**: 切換候選選擇、決策邏輯
4. **數據管理**: TLE 數據、歷史軌道、時間序列

### 🔬 物理層模擬組件 (部分移除)

**總計**: 5 個檔案  
**狀態**: 移除繪圖分析功能
**重要性**: P3 移除

Sionna 繪圖分析功能主要用於圖表生成，非核心演算法：

1. **通道模擬圖表**: 移除 SINR、CFR 圖表生成
2. **信號分析圖表**: 移除都卜勒、通道響應圖表
3. **統計圖表**: 移除各種統計分析圖表

### 🎨 3D 渲染組件 (保留衛星動畫)

**總計**: 8 個檔案/目錄 + 靜態資源
**狀態**: 保留衛星移動渲染功能  
**重要性**: P1 重要

3D 渲染功能專注於衛星移動動畫：

1. **場景管理**: 保留 3D 場景載入與管理（衛星動畫需要）
2. **模型服務**: 保留衛星、基站 3D 模型檔案提供
3. **渲染支援**: 保留衛星移動渲染參數和配置
4. **靜態資源**: 保留所有 3D 模型檔案（包含 UAV、干擾設備），移除分析圖表

### 📱 設備管理組件 (部分保留)

**總計**: 3 個檔案
**保留**: 2 個檔案 (設備相關)
**移除**: 1 個檔案 (UAV 相關)
**重要性**: P1 重要 / P3 移除

地面設備管理保留，UAV 追踪移除：

1. **保留**: 地面基站、用戶設備管理
2. **移除**: UAV 位置追踪和軌跡管理

### ⚙️ 系統工具組件 (選擇性保留)

**總計**: 12 個檔案/目錄
**保留**: 6 個檔案 (基礎工具)
**移除**: 6 個檔案/目錄 (非必要工具)
**重要性**: P2 輔助 / P3 移除

基礎系統工具保留，開發期工具和系統監控移除：

1. **保留**: 健康檢查、生命週期管理、數據庫配置
2. **移除**: 系統資源監控、精度驗證、過時遷移代碼

## 🎯 重構優先級建議

### Phase 1: 高風險移除 (P3 組件)
1. 移除 UAV 追踪模組
2. 移除系統資源監控域
3. 移除開發期驗證工具

### Phase 2: 代碼重構
1. 合併重複的距離計算邏輯
2. 優化座標轉換服務
3. 整合軌道計算服務

### Phase 3: 架構優化
1. 重新組織 API 路由結構
2. 優化服務依賴關係
3. 改進錯誤處理機制

---

**總結**: 通過大幅移除物理層模擬、3D 渲染等視覺化功能，SimWorld Backend 將專注於 LEO satellite handover 核心演算法，保留衛星軌道計算、可見性分析、切換決策和最基本的設備管理功能，達到最大程度的簡化。
EOF < /dev/null
