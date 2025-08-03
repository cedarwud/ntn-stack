# SimWorld Backend 清理報告

## 🎯 執行摘要

經過全面分析 SimWorld 後端程式碼，識別出多個過時和未使用的檔案及程式邏輯。本報告提供詳細的清理計畫，確保系統的可維護性和效能。

## 🗂️ 可安全刪除的檔案清單

### 🚨 第一階段：高優先級 - 完全未使用的檔案

#### PostgreSQL 遺留檔案 (已移除，改用 MongoDB)
```bash
simworld/backend/app/api/routes/devices_postgresql.py
simworld/backend/app/db/postgresql_config.py  
simworld/backend/app/db/postgresql_seeds.py
simworld/backend/app/db/postgresql_schema.sql
```

#### 過時系統檔案
```bash
simworld/backend/app/core/dependency_injection_deprecated.py
simworld/backend/app/api/routes/satellite_redis.py.backup
simworld/backend/app/db/lifespan_mongodb_backup.py
```

#### 未引用的根目錄處理腳本
```bash
simworld/backend/integrated_phase1_phase2_filter.py
simworld/backend/orbital_diversity_filter.py
simworld/backend/preprocess_120min_timeseries.py
simworld/backend/preprocess_120min_timeseries_sgp4.py
```

### 📊 第二階段：中優先級 - 註釋掉但存在的檔案

#### 需要評估的路由檔案
```bash
simworld/backend/app/api/routes/satellite.py          # PostgreSQL 版本
simworld/backend/app/api/routes/measurement_events.py # 依賴已刪除的 constellation_manager
simworld/backend/app/api/v1/satellite_admin_api.py   # 依賴 satellite 模組
```

### 🔍 第三階段：需要進一步確認的檔案

#### 空目錄
```bash
simworld/backend/netstack/data/     # 空目錄
simworld/backend/netstack/tle_data/ # 空目錄
```

#### 重複的資料檔案 (可能可以精簡)
```bash
simworld/backend/data/oneweb_120min_d2_demo.json
simworld/backend/data/oneweb_120min_d2_smoothed.json  
simworld/backend/data/starlink_120min_d2_demo.json
simworld/backend/data/starlink_120min_d2_smoothed.json
```

## 🧹 詳細執行步驟

### 步驟 1：備份重要資料
```bash
# 創建備份目錄
mkdir -p /home/sat/ntn-stack/backup/$(date +%Y%m%d_%H%M)_backend_cleanup

# 備份整個 backend 目錄 (可選)
cp -r simworld/backend /home/sat/ntn-stack/backup/$(date +%Y%m%d_%H%M)_backend_cleanup/
```

### 步驟 2：執行第一階段清理
```bash
# 刪除 PostgreSQL 相關檔案
rm simworld/backend/app/api/routes/devices_postgresql.py
rm simworld/backend/app/db/postgresql_config.py
rm simworld/backend/app/db/postgresql_seeds.py
rm simworld/backend/app/db/postgresql_schema.sql

# 刪除過時系統檔案
rm simworld/backend/app/core/dependency_injection_deprecated.py
rm simworld/backend/app/api/routes/satellite_redis.py.backup
rm simworld/backend/app/db/lifespan_mongodb_backup.py

# 刪除根目錄未使用腳本
rm simworld/backend/integrated_phase1_phase2_filter.py
rm simworld/backend/orbital_diversity_filter.py
rm simworld/backend/preprocess_120min_timeseries.py
rm simworld/backend/preprocess_120min_timeseries_sgp4.py

# 刪除空目錄
rmdir simworld/backend/netstack/data simworld/backend/netstack/tle_data simworld/backend/netstack 2>/dev/null || true
```

### 步驟 3：清理註釋程式碼
```bash
# 編輯 app/api/v1/router.py，移除所有被註釋的 import 和 router 註冊行
# 需要手動編輯以下檔案：
# - simworld/backend/app/api/v1/router.py
# - simworld/backend/app/api/dependencies.py  
# - simworld/backend/app/db/lifespan.py
# - simworld/backend/app/core/config.py
```

### 步驟 4：系統驗證
```bash
# 重啟服務
cd /home/sat/ntn-stack
make simworld-restart

# 等待服務啟動 (30-60 秒)
sleep 60

# 檢查服務狀態
make status | grep simworld

# 檢查 API 健康狀態
curl -s http://localhost:8888/health | jq
curl -s http://localhost:8888/ping | jq

# 檢查日誌無錯誤
docker logs simworld_backend 2>&1 | tail -20
```

### 步驟 5：驗證清理效果
```bash
# 檢查已刪除的檔案
ls -la simworld/backend/app/api/routes/devices_postgresql.py 2>/dev/null || echo "✅ PostgreSQL 路由已刪除"
ls -la simworld/backend/app/core/dependency_injection_deprecated.py 2>/dev/null || echo "✅ 過時依賴注入已刪除"

# 檢查目錄大小變化
du -sh simworld/backend/
```

## 📋 清理後檢查清單

### ✅ 第一階段完成確認
- [ ] PostgreSQL 相關檔案已刪除 (4 個檔案)
- [ ] 過時系統檔案已刪除 (3 個檔案)  
- [ ] 根目錄處理腳本已刪除 (4 個檔案)
- [ ] 空目錄已清理
- [ ] 服務重啟成功
- [ ] API 健康檢查通過
- [ ] 無錯誤日誌

### ✅ 第二階段完成確認 (選用)
- [ ] 註釋掉的路由檔案已評估
- [ ] router.py 中的註釋行已清理
- [ ] dependencies.py 中的註釋行已清理
- [ ] lifespan.py 中的註釋行已清理

### ✅ 第三階段完成確認 (選用)
- [ ] 重複資料檔案已評估
- [ ] 確認保留必要的 enhanced 版本檔案
- [ ] 刪除不必要的 demo 和 smoothed 版本

## 🎯 預期效果

### 檔案系統優化
- **減少檔案數量**: 約 15+ 個無用檔案
- **清理程式碼**: 移除數百行註釋程式碼
- **目錄結構**: 更清晰的檔案組織

### 程式碼品質提升
- **可讀性**: 移除混淆的註釋程式碼
- **維護性**: 減少過時依賴和檔案
- **安全性**: 移除未使用的 API 端點

### 系統效能
- **啟動時間**: 減少不必要的檔案掃描
- **記憶體使用**: 減少未使用模組載入
- **部署大小**: 減少 Docker 映像大小

## ⚠️ 風險評估

### 低風險操作
- ✅ 刪除明確標示為 deprecated 的檔案
- ✅ 刪除 .backup 檔案
- ✅ 刪除未被引用的根目錄腳本

### 中風險操作  
- ⚠️ 刪除註釋掉的路由檔案 (建議先保留)
- ⚠️ 刪除資料檔案 (建議先確認使用情況)

### 建議執行順序
1. **第一階段**: 低風險檔案清理 + 系統驗證
2. **第二階段**: 註釋程式碼清理 + 系統驗證  
3. **第三階段**: 資料檔案評估 + 選擇性清理

## 🚀 執行建議

1. **分階段執行**: 不要一次刪除所有檔案
2. **充分測試**: 每階段完成後都要驗證系統正常
3. **保留備份**: 至少保留一週的備份
4. **文檔更新**: 更新相關技術文檔和註釋

---

**建議執行時間**: 30-60 分鐘  
**建議執行者**: 熟悉 SimWorld 架構的開發者  
**前置條件**: 確保開發環境可以正常重啟和測試
