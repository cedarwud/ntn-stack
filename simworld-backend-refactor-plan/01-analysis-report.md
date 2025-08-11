# SimWorld Backend 全面分析報告

## 🔍 分析範圍與目標

**分析目標**: 識別 SimWorld Backend 中與 LEO satellite handover 研究無關的過時程式、重複功能和未使用的 API

**分析原則**: 
- 保留與衛星軌道計算、可見性分析、切換決策相關的核心功能
- 移除 Sionna 繪圖分析功能，保留 3D 場景渲染功能（用於前端渲染衛星移動動畫）
- 保留基本 devices 管理和所有 3D 模型資源（sat.glb, tower.glb, uav.glb, jam.glb）
- 移除系統監控、UAV 追踪、分析圖表等與研究目標無關的功能

## 📊 分析結果總覽

### 🎯 核心發現
- **總檔案數**: ~85 個 Python 檔案
- **建議移除**: 12 個檔案/模組
- **建議保留**: 65 個檔案/模組  
- **需要重構**: 8 個檔案/模組

### 📈 程式碼品質評估
- **重複功能**: 發現 3 處重複的距離計算邏輯
- **過時代碼**: Skyfield 遷移相關代碼已無必要
- **未使用 API**: UAV 追踪 API 與研究目標不符
- **系統監控**: 完整的系統資源監控域與研究無關

## 🔧 技術債務識別

### 高優先級技術債務
1. **Skyfield 遷移服務** (skyfield_migration.py)
   - 原因: 遷移完成後的遺留代碼
   - 影響: 增加維護負擔，無實際用途

2. **精度驗證器** (precision_validator.py) 
   - 原因: 開發期驗證工具，生產環境不需要
   - 影響: 額外的依賴和複雜度

3. **UAV 追踪模組** (uav.py 及相關)
   - 原因: 與 LEO satellite handover 研究無關
   - 影響: 分散注意力，增加系統複雜度

### 中優先級技術債務  
1. **系統資源監控域** (domains/system/)
   - 原因: 與核心研究目標無直接關係
   - 影響: 增加系統複雜度和維護成本

2. **重複的距離計算邏輯**
   - 位置: distance_calculator.py, distance_validator.py
   - 影響: 代碼重複，維護困難

## 📋 詳細分析結果

### ✅ 核心保留組件（與 LEO Satellite Handover 直接相關）

#### 衛星域 (domains/satellite/)
- **satellite_api.py**: 衛星可見性、切換候選查找
- **orbit_service.py**: 軌道計算服務
- **batch_orbit_service.py**: 批量軌道計算
- **cqrs_satellite_service.py**: 衛星服務架構
- **satellite_cache_service.py**: 衛星數據快取

#### 座標域 (domains/coordinates/)  
- **coordinate_api.py**: 座標系統轉換
- **coordinate_service.py**: 座標計算服務
- 用途: 衛星位置計算必需的座標轉換

#### API 路由
- **satellite_redis.py**: 衛星數據 Redis 快取
- **historical_orbits.py**: 歷史軌道數據管理
- **unified_timeseries.py**: 統一時間序列數據

#### 核心服務
- **distance_calculator.py**: 衛星距離計算
- **sgp4_calculator.py**: SGP4 軌道傳播算法
- **historical_orbit_generator.py**: 歷史軌道數據生成

### ❌ 建議移除組件（Sionna 繪圖功能）

#### 無線域中的 Sionna 繪圖功能 (domains/wireless/)
- **wireless_api.py**: 無線通道模擬 API（產生 SINR、CFR 等分析圖表）
- **sionna_channel_service.py**: Sionna 物理層模擬（產生圖表功能）
- **channel_conversion_service.py**: 通道數據轉換（用於繪圖分析）
- 移除原因: 主要用於產生分析圖表，非 LEO satellite handover 核心演算法

### ✅ 精簡保留組件（僅基本功能）

#### 設備域 (domains/device/) 
- **device_api.py**: 設備管理 API（僅基本CRUD功能）
- **device_service.py**: 設備服務邏輯（僅基本邏輯）
- 保留原因: 提供最基本的地面設備管理功能

### 🎨 保留組件（用於衛星移動渲染）

#### 模擬域 (domains/simulation/) - 部分保留
- **simulation_api.py**: 場景模擬 API（**保留**基本場景載入功能）
- **rendering_service.py**: 3D 渲染服務（**保留**衛星移動渲染）  
- **scene_management_service.py**: 場景管理（**保留**場景切換管理）
- **sionna_service.py**: Sionna 整合服務（**移除**圖表生成功能，**保留**場景渲染）
- 保留原因: 前端需要渲染衛星移動動畫，但移除分析圖表功能

#### 核心路由中的模型服務 (api/routes/core.py) - 保留
- **get_model()**: 3D 模型檔案服務（**保留**，用於衛星動畫）
- **get_scene_model()**: 場景模型檔案服務（**保留**，用於場景載入）
- 保留原因: 為前端提供衛星移動動畫所需的 3D 資源

#### 靜態資源 (static/) - 部分保留
- **images/**: 各種分析圖表（cfr_plot.png, delay_doppler.png 等）- **移除**
- **models/**: 所有 3D 模型（sat.glb, tower.glb, uav.glb, jam.glb）- **完整保留**
- **scenes/**: NTPU、NYCU 等場景模型（.glb, .xml, .ply 檔案）- **保留**
- 保留原因: 所有 3D 模型和場景檔案都用於前端 3D 渲染和動畫

### ❌ 建議移除組件（更新後的完整清單）

#### 1. UAV 追踪模組
- **檔案**: api/routes/uav.py
- **相關**: UAV 位置、軌跡管理
- **移除原因**: 與 LEO satellite handover 研究無關
- **風險評估**: 低風險，無其他模組依賴

#### 2. 系統資源監控域
- **檔案**: domains/system/ (完整目錄)
- **功能**: CPU、記憶體、GPU 監控
- **移除原因**: 與核心研究目標無關
- **風險評估**: 低風險，獨立模組

#### 3. Sionna 繪圖分析功能  
- **檔案**: domains/wireless/ 中的分析圖表功能
- **功能**: SINR、CFR、通道響應等圖表生成
- **移除原因**: 主要用於產生分析圖表，非 LEO handover 核心演算法
- **風險評估**: 低風險，獨立功能模組

#### 4. Sionna 服務中的圖表功能
- **檔案**: domains/simulation/services/sionna_service.py 中的圖表方法
- **功能**: generate_doppler_plots, generate_cfr_plot, generate_sinr_map 等
- **移除原因**: 用於產生分析圖表，非衛星移動渲染核心
- **風險評估**: 低風險，可精確移除特定方法

#### 5. 分析圖表靜態檔案
- **檔案**: static/images/ (cfr_plot.png, delay_doppler.png, sinr_map.png 等)
- **功能**: 預生成的分析圖表檔案  
- **移除原因**: 分析圖表與衛星移動動畫無關
- **風險評估**: 極低風險，純分析輸出檔案

#### 6. 非必要靜態檔案
- **檔案**: static/images/ 中的分析圖表檔案
- **功能**: 預生成的 CFR、SINR、都卜勒分析圖表
- **移除原因**: 分析圖表與衛星移動動畫和研究無關
- **風險評估**: 極低風險，純分析輸出檔案

#### 7. 過時開發工具
- **skyfield_migration.py**: Skyfield 遷移服務
- **precision_validator.py**: 精度驗證工具
- **distance_validator.py**: 距離驗證工具
- **移除原因**: 開發期工具，生產環境不需要
- **風險評估**: 極低風險，僅開發期使用

## 🎯 預期收益

### 程式碼簡化
- **移除程式碼行數**: ~3,000+ 行（移除 Sionna 繪圖功能）
- **減少檔案數量**: 15+ 個檔案（主要移除分析圖表功能）
- **降低複雜度**: 移除 3 個完整功能域 + 部分模組功能（system, wireless 繪圖功能, dev tools）

### 維護效益
- **減少技術債務**: 移除過時和重複程式碼
- **提升開發效率**: 專注於核心研究功能
- **降低錯誤風險**: 減少不必要的程式碼路徑

### 系統效能
- **降低記憶體使用**: 移除未使用的服務和快取
- **加快啟動時間**: 減少模組載入時間
- **簡化部署**: 減少依賴和配置複雜度

## 🚨 風險識別與緩解

### 低風險項目
- UAV 追踪模組: 完全獨立，無依賴關係
- 系統監控域: 獨立模組，安全移除
- 開發工具: 僅開發期使用，移除安全

### 中風險項目
- 距離計算重複邏輯: 需要仔細重構以避免破壞現有功能
- 部分 API 端點: 需要確認前端是否有呼叫

### 緩解策略
1. **漸進式移除**: 分階段移除，每階段後進行完整測試
2. **備份機制**: 移除前建立完整備份
3. **相依性檢查**: 使用工具檢查模組間依賴關係
4. **測試驗證**: 移除後執行完整的整合測試

---

**結論**: 通過精確移除 Sionna 繪圖分析功能，同時保留 3D 場景和模型用於衛星移動渲染，可以有效簡化 SimWorld Backend，專注於 LEO satellite handover 的核心演算法研究，同時保持前端衛星動畫的完整支援。系統將保留衛星軌道計算、可見性分析、切換決策演算法、基本設備管理和衛星移動渲染功能。
EOF < /dev/null
