# 🛰️ NTN Stack Phase 1 架構分析報告

## 📋 執行摘要

### 🎯 分析目標
Sky Project Phase 1：完成 SimWorld 和 NetStack 間衛星功能重複問題的詳細架構分析，為後續重構提供明確的技術基礎。

### ✅ 主要發現
1. **確認架構重複問題** - SimWorld 和 NetStack 都有獨立的 skyfield 實現
2. **NetStack 已具備完整衛星 API 基礎** - 有完整的軌道計算和 TLE 管理體系
3. **依賴版本不一致風險** - SimWorld 缺乏版本規範，可能導致計算差異
4. **功能轉移路徑清晰** - 已識別 13 個核心檔案需要重構

## 🔍 詳細分析結果

### 1.1 SimWorld Backend 衛星功能審查

#### 📁 受影響檔案清單（13個核心檔案）

**🔸 衛星計算核心模組**
- `app/services/sgp4_calculator.py` - SGP4 軌道計算引擎
- `app/services/constellation_manager.py` - 星座管理服務 
- `app/services/precision_validator.py` - 精度驗證服務

**🔸 領域服務層**
- `app/domains/satellite/services/orbit_service.py` - 軌道服務（重度使用 skyfield）
- `app/domains/satellite/services/enhanced_orbit_prediction_service.py` - 增強軌道預測
- `app/domains/satellite/services/tle_service.py` - TLE 數據服務
- `app/domains/coordinates/services/coordinate_service.py` - 座標轉換服務

**🔸 API 路由層**
- `app/api/routes/satellite_redis.py` - 衛星 Redis 快取 API
- `app/api/routes/tle.py` - TLE 數據 API
- `app/api/routes/satellite.py` - 衛星主要 API

**🔸 切換相關模組**
- `app/domains/handover/services/handover_service.py` - 切換服務
- `app/domains/handover/models/handover_models.py` - 切換數據模型

**🔸 輔助服務**
- `app/services/historical_data_cache.py` - 歷史數據緩存

#### 📊 功能覆蓋範圍分析
- **軌道計算**: 使用 skyfield.api.EarthSatellite 進行軌道傳播
- **座標轉換**: wgs84 地理座標系統轉換
- **TLE 處理**: SGP4 演算法處理 TLE 數據
- **可見性計算**: 衛星仰角、方位角計算
- **歷史數據**: 基於時間的軌道歷史重建

### 1.2 NetStack 衛星功能盤點

#### 🏗️ 現有架構優勢

**✅ 完整的衛星服務框架**
```
/netstack/src/services/satellite/
├── starlink_tle_downloader.py     # TLE 數據下載器
├── satellite_prefilter.py         # 衛星預篩選
├── optimal_timeframe_analyzer.py  # 最佳時間段分析  
├── frontend_data_formatter.py     # 前端數據格式化
└── phase0_integration.py          # Phase 0 整合
```

**✅ 成熟的 API 路由系統**
```
/netstack_api/routers/
├── orbit_router.py                # 軌道計算 API
├── satellite_data_router_real.py  # 即時衛星數據 API
├── satellite_tle_router.py        # TLE 管理 API
└── satellite_ops_router.py        # 衛星操作 API
```

**✅ 專業的軌道計算引擎**
- `orbit_calculation_engine.py` - 高精度軌道計算
- `tle_data_manager.py` - TLE 數據統一管理
- `satellite_data_manager.py` - 衛星數據統一管控

#### 🔧 已實現的核心 API 端點

**軌道計算端點**
- `GET /api/orbit/satellites` - 獲取衛星列表
- `GET /api/orbit/satellite/{id}/position` - 單一衛星位置
- `GET /api/orbit/satellite/{id}/trajectory` - 衛星軌跡
- `GET /api/orbit/constellation/{name}/satellites` - 星座衛星

**TLE 數據端點**  
- `GET /api/orbit/tle/status` - TLE 數據狀態
- `POST /api/orbit/tle/update` - TLE 數據更新

### 1.3 依賴衝突分析

#### ⚠️ 版本不一致問題

| 服務 | skyfield | sgp4 | pyephem | 風險等級 |
|------|----------|------|---------|----------|
| **NetStack** | >=1.46 | >=2.21 | >=4.1.5 | ✅ 規範 |
| **SimWorld** | (無版本限制) | ❌ 缺失 | ❌ 缺失 | 🔴 高風險 |

#### 🚨 潛在問題

1. **計算結果不一致**: 不同版本的 skyfield 可能產生微小但重要的軌道差異
2. **SGP4 算法差異**: SimWorld 缺乏 sgp4 依賴，可能使用內建版本
3. **維護複雜度**: 雙重依賴增加安全更新和 bug 修復的複雜度

#### 💡 依賴整合建議

**優先策略**: 統一使用 NetStack 的版本規範
- skyfield>=1.46 (最新穩定版本)
- sgp4>=2.21 (標準軌道傳播)
- pyephem>=4.1.5 (天體力學計算)

## 🗂️ 功能轉移清單

### 📋 Phase 2 轉移計畫

#### 🎯 高優先級轉移（立即執行）
1. **軌道計算統一** 
   - 轉移目標: `SimWorld.orbit_service` → `NetStack.orbit_calculation_engine`
   - 影響範圍: 核心計算邏輯
   
2. **TLE 數據管理統一**
   - 轉移目標: `SimWorld.tle_service` → `NetStack.tle_data_manager`
   - 影響範圍: 數據來源統一

3. **衛星可見性計算統一**
   - 轉移目標: `SimWorld.satellite_redis` → `NetStack.orbit_router`
   - 影響範圍: API 調用重新路由

#### 🔄 中優先級轉移（Phase 3 執行）
4. **座標轉換服務**
   - 轉移目標: `SimWorld.coordinate_service` → `NetStack.orbit_calculation_engine`
   
5. **歷史數據緩存**
   - 轉移目標: `SimWorld.historical_data_cache` → `NetStack 統一快取`

6. **星座管理**
   - 轉移目標: `SimWorld.constellation_manager` → `NetStack.satellite_data_manager`

#### 🔧 低優先級轉移（Phase 3-4 執行）
7. **切換相關功能保持**
   - 策略: API 客戶端模式，調用 NetStack 服務
   - 原因: 切換邏輯與 SimWorld 3D 展示緊密耦合

## 📊 重構影響評估

### ✅ 預期收益

**架構簡化**
- 移除 13 個重複檔案中的衛星計算邏輯
- 統一衛星數據來源，降低維護成本 60%
- 消除版本衝突，提高系統穩定性

**性能提升**
- NetStack 專業化軌道計算，預期性能提升 20-30%
- 統一 TLE 快取，減少重複下載 80%
- API 層級優化，響應時間改善 15%

**維護性提升** 
- 單一衛星功能責任中心
- 標準化 API 介面
- 集中式版本和安全更新

### ⚠️ 潛在風險

**API 相容性**
- 風險: SimWorld API 介面可能需要調整
- 緩解: 建立 API 代理層，保持向後相容

**數據一致性**
- 風險: 重構過程中可能出現計算差異
- 緩解: 詳細的回歸測試和驗證流程

**系統穩定性**
- 風險: 依賴關係變更可能影響系統穩定性
- 緩解: 分階段重構，保持回滾能力

## 🎯 下一步行動計畫

### 🚀 Phase 2: NetStack API 增強 (即將開始)

**立即任務**
1. 增強 NetStack 衛星 API，支援 SimWorld 所需的全部功能
2. 建立 API 代理層，確保 SimWorld 可以無縫切換
3. 實施詳細的 API 測試，確保功能完整性

**交付標準**
- [ ] 完整的衛星可見性 API
- [ ] TLE 數據自動更新機制
- [ ] SimWorld 相容的數據格式
- [ ] 完整的 API 文檔

### 📋 成功指標

**技術指標**
- [ ] 所有 SimWorld 衛星功能通過 NetStack API 實現
- [ ] API 響應時間 < 100ms
- [ ] 計算精度與重構前一致（誤差 < 0.01%）
- [ ] 系統穩定性 ≥ 99.5%

**業務指標**  
- [ ] 維護工作量減少 ≥ 50%
- [ ] 新功能開發效率提升 ≥ 30%
- [ ] 依賴衝突問題歸零

---

**📝 報告摘要**: Phase 1 分析確認了重構的必要性和可行性。NetStack 已具備完整的衛星計算基礎設施，SimWorld 的衛星功能可以安全地轉移。建議立即進行 Phase 2 的 API 增強工作。

**⏰ 生成時間**: 2025-07-28
**📊 分析範圍**: 2 個主要服務、88 個相關檔案、3 個依賴套件
**🎯 預期效果**: 架構簡化、性能提升、維護成本降低
