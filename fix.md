# LEO 衛星系統開發前重構修復計劃

## ✅ 階段3完成狀態 (2025-07-24)

**🎉 Phase 3 清理優化完成 - 測試結構更加清晰，配置更加精簡**

### 完成項目
- ✅ **3.1 NetStack 測試文件整理** - 按功能分組，統一測試結構
  - 單元測試：`/tests/unit/` (按服務分類)
  - 整合測試：`/tests/integration/` (Phase 2.3, Phase 3)
  - 端到端測試：`/tests/e2e/` (完整流程測試)
- ✅ **3.2 前端配置參數簡化** - satellite.config.ts 精簡為核心參數
  - 統一時間控制參數
  - 基於 3GPP NTN 標準的切換參數
  - 支援動態配置調整

### 測試結構改進
```
netstack/tests/
├── unit/                    # 單元測試
│   ├── ai_decision_integration/
│   └── rl_training/
├── integration/             # 整合測試  
│   ├── phase_2_3_integration_test.py
│   └── phase_3_integration_test.py
└── e2e/                     # 端到端測試
    └── test_rl_integration_e2e.py
```

### 配置簡化成果
- 參數數量減少 60% (從 30+ 個減少到 12 個核心參數)
- 統一時間控制機制
- 移除冗餘的調整參數
- 支援運行時動態調整

### 驗證結果
- ✅ **系統狀態**: 所有服務健康運行 (NetStack + SimWorld)
- ✅ **API 測試**: NetStack `/health`, SimWorld `/health` 正常
- ✅ **前端載入**: 頁面正常顯示
- ✅ **測試結構**: 文件組織清晰，便於維護

---

## ✅ 階段1完成狀態 (2025-01-24)

**🎉 關鍵修復已完成 - 系統可正常進行 Phase 1-5 開發**

### 完成項目
- ✅ **1.1 清理重複 Satellite Redis 路由文件** - 移除重複文件，簡化路由
- ✅ **1.2 統一數據庫策略** - SimWorld 完全遷移到 PostgreSQL，使用 NetStack PostgreSQL
- ✅ **1.3 簡化依賴注入系統** - 移除複雜 DI 容器，改為直接實例化

### 額外修復 (發現並解決)
- ✅ **Pydantic v2 兼容性** - 修復 `regex` → `pattern` 參數更名
- ✅ **PostgreSQL 連接配置** - 正確配置 NetStack PostgreSQL 憑證
- ✅ **MongoDB 依賴清理** - 移除 SimWorld 中殘留的 MongoDB 引用

### 驗證結果
- ✅ **系統狀態**: 所有服務健康運行 (NetStack + SimWorld)
- ✅ **API 測試**: NetStack `/health`, SimWorld `/api/v1/devices/` 正常
- ✅ **數據庫**: PostgreSQL 正常工作，設備數據完整載入
- ✅ **啟動速度**: 依賴注入簡化，提升啟動效率

---

## 🚨 緊急重構需求分析

在進行 **LEO 衛星系統 Phase 1-5 開發** 之前，發現現有架構存在嚴重問題，**必須先進行重構修復**，否則將嚴重影響開發效率和系統穩定性。

## 📊 問題嚴重程度評估

### 🔴 CRITICAL - 必須在 Phase 1 前修復
- **數據層混亂**: PostgreSQL + MongoDB + Redis 混用，造成數據不一致風險
- **重複路由文件**: 3個satellite_redis文件導致維護混亂
- **依賴注入過度複雜**: 影響服務啟動和調試

### 🟠 HIGH - Phase 1-2 期間修復
- **Domain架構過度工程化**: 過多領域分離增加複雜度
- **前端代理配置混亂**: 影響API整合
- **配置文件分散**: 環境變數管理困難

### 🟡 MEDIUM - Phase 3-4 期間修復
- **測試文件冗餘**: NetStack中過多phase測試文件
- **前端配置參數過多**: 維護成本高
- **構建配置過度優化**: 不必要的複雜性

---

## 🏗️ 具體重構計劃

### 🔴 階段1: 緊急修復 (Phase 1 開發前)

#### 1.1 清理重複的 Satellite Redis 路由文件
**問題**: 存在3個重複文件造成維護混亂
```bash
# 需要清理的文件:
simworld/backend/app/api/routes/satellite_redis.py     # 保留
simworld/backend/app/api/routes/satellite_redis_old.py  # 刪除
simworld/backend/app/api/routes/satellite_redis_fixed.py # 刪除
```

**修復步驟**:
1. 比較三個文件的差異，整合最佳功能到主文件
2. 刪除舊版本和臨時修復版本
3. 更新router.py中的import引用
4. 測試API端點正常工作

#### 1.2 統一數據庫策略
**問題**: SimWorld 同時使用 PostgreSQL + MongoDB 造成數據分散

**修復策略** (基於系統分析):
- **SimWorld → PostgreSQL** (時間序列數據、空間查詢優化)
- **NetStack → 保持 MongoDB** (Open5GS 標準依賴，不可修改)
- **Redis 僅用於緩存** (衛星位置數據等高頻查詢)

**SimWorld 遷移範圍**:
- 設備管理 (`devices_mongodb.py`)
- 模擬結果存儲 (CFR、SINR、Doppler 圖表)
- MongoDeviceManager → PostgreSQL DeviceManager

**實施策略** (基於 lifespan.py 分析):
- ✅ **修改初始化腳本** - `lifespan.py` 中的種子數據初始化
- ✅ **創建 PostgreSQL Schema** - 設備表、地面站表
- ✅ **更新 API 路由** - 從 MongoDB 改為 PostgreSQL
- ❌ **不需要數據遷移** - 都是可重建的種子數據

**具體步驟**:
1. 創建 PostgreSQL 設備和地面站表結構
2. 修改 lifespan.py 初始化函數使用 PostgreSQL  
3. 更新 devices_mongodb.py → devices_postgresql.py
4. 更新模擬 API 使用 PostgreSQL 依賴
5. 保留 NetStack MongoDB 完全不動

#### ✅ 1.3 簡化依賴注入系統
**問題**: app/core/dependency_injection.py 過度複雜，影響服務啟動

**修復原則** (遵循CLAUDE.md規範):
- **簡化優於複雜** - 移除不必要的抽象層
- **直接依賴注入** - 使用FastAPI內建的Depends系統
- **避免循環依賴** - 清理複雜的服務依賴關係

**✅ 實施完成**:
1. ✅ 分析DI使用情況 - 僅在performance服務初始化中使用
2. ✅ 改為直接實例化 - 更新service_registry.py
3. ✅ 移除DI容器依賴 - 標記dependency_injection.py為deprecated
4. ✅ 簡化啟動邏輯 - 減少啟動時間和複雜度

### 🟠 階段2: 架構優化 (Phase 1-2 期間)

#### 2.1 簡化 Domain 架構
**問題**: 過多領域分離導致維護複雜度增加

**當前架構問題**:
```
app/domains/
├── satellite/     # 衛星領域
├── simulation/    # 模擬領域
├── device/        # 設備領域
├── coordinates/   # 坐標領域
├── handover/      # 切換領域
├── interference/  # 干擾領域
├── wireless/      # 無線領域
├── system/        # 系統領域
└── performance/   # 性能領域
```

**簡化策略**:
1. **合併相關領域** - wireless + interference → rf_simulation
2. **移除過度抽象** - 將simple的CRUD操作直接實現
3. **專注核心領域** - satellite, simulation, handover為主

#### 2.2 修復前端代理配置
**問題**: vite.config.ts 中代理配置過於複雜

**當前問題**:
- 複雜的路徑重寫邏輯
- 硬編碼的容器名稱
- 重複的代理規則

**修復計劃**:
1. **簡化代理規則** - 統一API路徑管理
2. **環境變數化** - 移除硬編碼容器名稱
3. **API統一前綴** - /api/simworld, /api/netstack
4. **測試代理配置** - 確保開發和生產環境一致

#### 2.3 整合配置文件
**問題**: 配置分散在多個文件中

**目標**:
- **app/core/config.py** - 後端配置統一管理
- **前端環境變數** - 統一API端點配置
- **Docker環境** - 一致的容器間通訊配置

#### 2.4 修復衛星數據載入和 Fallback 機制
**問題**: TLE 數據下載失敗導致前端衛星API返回空數組

**根本原因**:
- 外部 TLE 數據源 (CelesTrak) 下載失敗
- NetStack 缺乏有效的 fallback 初始化機制
- 數據格式和存儲位置不匹配

**修復策略**:
1. **改善 Fallback 機制** - 自動檢測下載失敗並載入本地數據
2. **統一數據格式** - 確保 Redis 數據格式符合 API 預期
3. **健康檢查增強** - 衛星數據載入狀態監控
4. **初始化順序優化** - 確保 TLE 數據在 API 啟動前就緒

**具體修復步驟**:
1. 分析 NetStack 衛星數據管理架構和數據流
2. 實現自動 fallback 觸發機制
3. 統一 Redis TLE 數據鍵值格式
4. 添加衛星數據健康檢查端點
5. 測試前端 API 響應正確的衛星數據

**優先級**: Phase 1-2 期間修復 (不阻礙核心功能開發)

### 🟡 階段3: 清理優化 (Phase 3-4 期間)

#### 3.1 NetStack 測試文件整理
**問題**: 過多的phase測試文件造成維護困難

**當前狀況**:
```bash
netstack/
├── test_phase0_*.py    # Phase 0 相關測試
├── test_phase1_*.py    # Phase 1 相關測試
├── test_phase2_*.py    # Phase 2 相關測試
└── 其他零散測試文件...
```

**整理策略**:
1. **按功能分組** - satellite_tests/, rl_tests/, integration_tests/
2. **合併重複測試** - 避免功能重疊的測試
3. **統一測試框架** - 使用一致的測試模式

#### 3.2 前端配置參數簡化
**問題**: satellite.config.ts 中參數過多

**簡化原則**:
- **移除非必要參數** - 減少配置複雜度
- **合理預設值** - 提供適合LEO衛星的預設配置
- **動態配置** - 支援運行時調整關鍵參數

---

## 📋 重構驗證流程

### 每個階段完成後必須執行

```bash
# 1. 完全重啟系統
make down && make up

# 2. 檢查所有服務狀態
make status

# 3. 驗證關鍵API端點
curl -s http://localhost:8080/health  < /dev/null |  jq
curl -s http://localhost:8888/health | jq
curl -s http://localhost:5173/api/health | jq

# 4. 執行重構驗證腳本
./verify-refactor.sh --after-refactor
```

## ⚠️ 重構風險控制原則

**遵循 CLAUDE.md 中的重構安全原則**:

### 🛡️ 黃金法則
1. **簡化問題，而非複雜化解決方案**
2. **功能不減少** - 重構後功能 ≥ 重構前
3. **穩定性提升** - bug 數量應該減少
4. **維護性改善** - 未來修改應該更容易

### 🚨 危險信號識別
- **引入事件系統到簡單功能** ❌
- **過度抽象化** ❌
- **為了技術炫技而重構** ❌
- **追求完美而忽略實用性** ❌

### ✅ 重構成功標準
- [ ] 所有原有功能正常工作
- [ ] 新功能按預期工作
- [ ] 系統整體穩定性沒有下降
- [ ] 代碼複雜度沒有明顯增加
- [ ] 維護成本沒有增加

---

## 🎯 總結與建議

### 📊 重構影響評估

**如果不進行重構，LEO衛星系統開發將面臨**:
- ⚠️ **Phase 1 數據整合困難** - 多數據源衝突
- ⚠️ **Phase 2-3 API開發緩慢** - 路由和配置混亂
- ⚠️ **Phase 4 前端整合問題** - 代理配置複雜
- ⚠️ **Phase 5 部署困難** - 服務依賴不清晰

**重構後的優勢**:
- ✅ **統一數據架構** - PostgreSQL為主，Redis為輔
- ✅ **清晰的API結構** - 簡化的路由和端點
- ✅ **簡化的配置管理** - 統一的環境變數
- ✅ **提高開發效率** - 減少配置和依賴複雜度

### 🚀 開始重構的建議

**優先執行階段1的緊急修復**，這些是影響Phase 1-5開發的關鍵瓶頸。

**時間估算**:
- **階段1 (緊急修復)**: 2-3天
- **階段2 (架構優化)**: 1週
- **階段3 (清理優化)**: 3-5天

**投資回報**: 重構投入的時間將在後續Phase 1-5開發中節省2-3倍的時間。

---
*重構計劃創建時間: 2025-07-24*
*符合 CLAUDE.md 中的架構設計和重構原則*
