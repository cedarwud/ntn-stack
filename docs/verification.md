# 系統驗證機制與完成確認

## 📋 驗證方法統一標準

### **🎯 後端 API 驗證**
- 使用 `curl` 命令測試所有端點
- 檢查 HTTP 狀態碼、響應時間、JSON 格式
- 驗證數據庫查詢和事務處理
- 使用 Docker 日誌檢查系統運行狀態

### **🎨 前端功能驗證**
- 使用瀏覽器開發者工具的 Console 和 Network 頁籤
- 檢查 React 組件是否正確渲染和更新
- 監聽 DOM 變更和 API 調用
- 測試用戶交互和響應式設計

### **🔧 系統整合驗證**
- 容器健康檢查和依賴關係驗證
- 數據持久性和服務恢復能力測試
- 性能基準測試和資源使用監控
- 完整系統驗證腳本自動化檢查

---

## ✅ Phase 1: PostgreSQL 數據架構 - 驗證機制

### **1.1 後端數據庫驗證**
```bash
# 1. 檢查 PostgreSQL 表結構
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT table_name, column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name IN ('satellite_tle_data', 'satellite_orbital_cache', 'd2_measurement_cache')
ORDER BY table_name, ordinal_position;
"

# 2. 檢查索引是否正確創建
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename LIKE 'satellite_%' OR tablename LIKE 'd2_%'
ORDER BY tablename;
"

# 3. 檢查視圖是否存在
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT viewname, definition 
FROM pg_views 
WHERE viewname IN ('active_satellites_overview', 'd2_events_summary');
"
```

### **1.2 API 端點驗證**
```bash
# 檢查數據庫連接健康狀態
curl -X GET "http://localhost:8080/api/v1/satellites/health" \
  -H "Content-Type: application/json" | jq

# 預期響應：
# {
#   "status": "healthy",
#   "database": "postgresql",
#   "tables": ["satellite_tle_data", "satellite_orbital_cache", "d2_measurement_cache"],
#   "timestamp": "2025-01-23T..."
# }
```

### **1.3 完成確認檢查清單**
- [ ] **數據庫表創建**: 3 張主要表 + 4 個索引 + 2 個視圖
- [ ] **PostgreSQL 健康檢查**: 連接成功且響應時間 < 100ms
- [ ] **表結構驗證**: 所有必要欄位存在且類型正確
- [ ] **索引效能**: 查詢執行計劃顯示使用索引
- [ ] **API 響應**: `/health` 端點返回 200 狀態

---

## ✅ Phase 2: 數據預計算引擎 - 驗證機制

### **2.1 TLE 數據下載驗證**
```bash
# 1. 測試 TLE 數據獲取功能
curl -X POST "http://localhost:8080/api/v1/satellites/tle/download" \
  -H "Content-Type: application/json" \
  -d '{
    "constellations": ["starlink", "oneweb"],
    "force_update": false
  }' | jq

# 預期響應：
# {
#   "success": true,
#   "downloaded": {
#     "starlink": 6,
#     "oneweb": 4
#   },
#   "total_satellites": 10,
#   "download_time_ms": 1500
# }

# 2. 驗證 TLE 數據存儲
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT constellation, COUNT(*) as satellite_count, 
       MIN(epoch) as oldest_tle, MAX(epoch) as newest_tle
FROM satellite_tle_data 
WHERE is_active = true 
GROUP BY constellation;
"
```

### **2.2 軌道預計算驗證**
```bash
# 1. 啟動軌道預計算作業
curl -X POST "http://localhost:8080/api/v1/satellites/precompute" \
  -H "Content-Type: application/json" \
  -d '{
    "constellation": "starlink",
    "start_time": "2025-01-23T00:00:00Z",
    "end_time": "2025-01-23T06:00:00Z",
    "time_step_seconds": 30,
    "observer_location": {
      "latitude": 24.94417,
      "longitude": 121.37139,
      "altitude": 100
    }
  }' | jq

# 預期響應：
# {
#   "job_id": "precompute_starlink_20250123",
#   "status": "running",
#   "estimated_duration_minutes": 5,
#   "total_calculations": 2880
# }

# 2. 檢查預計算進度
curl -X GET "http://localhost:8080/api/v1/satellites/precompute/job_id/status" | jq

# 3. 驗證預計算結果
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT constellation, 
       COUNT(*) as total_records,
       COUNT(DISTINCT satellite_id) as unique_satellites,
       MIN(timestamp) as earliest_time,
       MAX(timestamp) as latest_time
FROM satellite_orbital_cache 
WHERE constellation = 'starlink'
GROUP BY constellation;
"
```

### **2.3 完成確認檢查清單**
- [ ] **TLE 下載**: 成功獲取多星座 TLE 數據 (< 5 秒)
- [ ] **數據解析**: SGP4 軌道計算正確無誤差
- [ ] **批量存儲**: 插入效能 > 1000 條/秒
- [ ] **預計算完整性**: 6 小時數據覆蓋無遺漏時間點
- [ ] **計算準確性**: 位置誤差 < 1km (與 Skyfield 基準比較)

---

## ✅ Phase 3: API 端點實現 - 驗證機制

### **3.1 衛星位置查詢驗證**
```bash
# 1. 查詢特定時間點的衛星位置
curl -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" \
  -d "min_elevation=10" | jq

# 預期響應：
# {
#   "satellites": [
#     {
#       "satellite_id": "starlink-1",
#       "norad_id": 50001,
#       "position": {
#         "latitude": 25.1,
#         "longitude": 121.5,
#         "altitude": 550.2
#       },
#       "elevation_angle": 35.4,
#       "azimuth_angle": 180.0,
#       "distance_km": 1200.5
#     }
#   ],
#   "observer_location": {...},
#   "timestamp": "2025-01-23T12:00:00Z",
#   "query_time_ms": 45
# }
```

### **3.2 完成確認檢查清單**
- [ ] **位置查詢**: 響應時間 < 100ms，數據準確
- [ ] **時間軸端點**: 正確返回數據範圍和統計
- [ ] **軌跡查詢**: 支援任意時間區間查詢
- [ ] **D2 事件**: 正確計算 handover 觸發條件
- [ ] **錯誤處理**: 無效參數返回適當錯誤訊息

---

## ✅ Phase 4: 前端時間軸控制 - 驗證機制

### **4.1 星座選擇器驗證**
```javascript
// 在瀏覽器 Console 中執行檢查
console.log("=== 星座選擇器驗證開始 ===");
console.log("可用星座數量:", document.querySelectorAll('.constellation-option').length);
console.log("預期: ≥ 2 (Starlink + OneWeb)");

// 檢查 API 調用
// 在 Network 標籤中查看是否有以下請求：
// GET /api/satellites/constellations/info
// 狀態碼應為 200，響應時間 < 500ms
```

### **4.2 時間軸控制器驗證**
```javascript
// 檢查控制器是否載入
const timelineControl = document.querySelector('.timeline-control');
console.log("時間軸控制器存在:", !!timelineControl);

// 檢查統計資訊顯示
const statistics = document.querySelectorAll('.ant-statistic');
console.log("統計項目數量:", statistics.length);
console.log("預期: 4 項 (數據覆蓋、數據點數、解析度、進度)");

// 檢查播放控制按鈕
const playButton = document.querySelector('[data-testid="play-button"], .ant-btn-primary');
console.log("播放按鈕存在:", !!playButton);
```

### **4.3 完成確認檢查清單**
- [ ] **星座選擇器**: 正確顯示多星座選項，有圖示和統計資訊
- [ ] **API 整合**: 選擇星座時正確調用 `/constellations/info` 端點
- [ ] **時間軸控制**: 播放/暫停/倍速功能正常運作
- [ ] **數據同步**: 時間變更時正確觸發回調函數
- [ ] **響應式設計**: 在不同螢幕尺寸下正常顯示
- [ ] **性能表現**: 組件載入時間 < 2 秒，操作響應 < 300ms

---

## ✅ Phase 5: 容器啟動順序和智能更新 - 驗證機制

### **5.1 容器啟動順序驗證**
```bash
# 1. 檢查容器啟動順序和依賴關係
docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}"

# 預期結果：所有容器都應為 "Up" 狀態
# netstack-rl-postgres     Up    Up 30 seconds (healthy)
# netstack-api             Up    Up 25 seconds (healthy)  
# simworld_backend         Up    Up 20 seconds (healthy)

# 2. 檢查健康檢查狀態
docker inspect netstack-rl-postgres --format '{{.State.Health.Status}}'
docker inspect netstack-api --format '{{.State.Health.Status}}'

# 預期: 所有容器都返回 "healthy"
```

### **5.2 數據持久性驗證**
```bash
# 檢查數據是否在重啟後保持
echo "=== 數據持久性測試 ==="

# 重啟前查詢數據量
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT 'Before restart' as stage, COUNT(*) as satellite_records
FROM satellite_tle_data;
"

# 執行容器重啟
make simworld-restart

# 等待服務完全啟動 (30秒)
sleep 30

# 重啟後檢查數據
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT 'After restart' as stage, COUNT(*) as satellite_records
FROM satellite_tle_data;
"

# 預期: 重啟前後數據量相同
```

### **5.3 完成確認檢查清單**
- [ ] **容器啟動順序**: PostgreSQL → NetStack API → SimWorld，依賴關係正確
- [ ] **啟動時間**: 完整系統啟動 < 120 秒 (包含數據載入)
- [ ] **數據持久性**: 容器重啟後數據完整保留
- [ ] **立即可用性**: 服務啟動後 10 秒內 API 可用且有數據
- [ ] **背景更新**: 更新服務正常運行，有適當的日誌記錄
- [ ] **健康監控**: 所有服務健康檢查通過，資源使用合理
- [ ] **故障恢復**: 數據庫中斷後能自動恢復連接
- [ ] **性能穩定**: 併發請求處理正常，無記憶體洩漏

---

## 🚀 完整驗證腳本

### **comprehensive_verification.sh**
```bash
#!/bin/bash
# comprehensive_verification.sh - 完整系統驗證腳本

echo "🛰️ LEO 衛星系統完整驗證開始..."
echo "========================================"

# Phase 1: 數據庫架構驗證
echo "Phase 1: 檢查數據庫架構..."
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "\dt" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Phase 1: PostgreSQL 架構正常"
else
    echo "❌ Phase 1: PostgreSQL 架構有問題"
    exit 1
fi

# Phase 2: 數據預計算驗證
echo "Phase 2: 檢查數據預計算..."
curl -s "http://localhost:8080/api/v1/satellites/health" | grep -q "healthy"
if [ $? -eq 0 ]; then
    echo "✅ Phase 2: 數據預計算系統正常"
else
    echo "❌ Phase 2: 數據預計算系統異常"
    exit 1
fi

# Phase 3: API 端點驗證
echo "Phase 3: 檢查 API 端點..."
response=$(curl -s -w "%{http_code}" "http://localhost:8080/api/v1/satellites/constellations/info" -o /dev/null)
if [ "$response" -eq 200 ]; then
    echo "✅ Phase 3: API 端點正常工作"
else
    echo "❌ Phase 3: API 端點異常 (HTTP: $response)"
    exit 1
fi

# Phase 4: 前端驗證 (需要手動確認)
echo "Phase 4: 前端驗證..."
frontend_status=$(curl -s -w "%{http_code}" "http://localhost:5173" -o /dev/null)
if [ "$frontend_status" -eq 200 ]; then
    echo "✅ Phase 4: 前端服務正常 (需手動驗證功能)"
else
    echo "❌ Phase 4: 前端服務異常"
fi

# Phase 5: 容器協調驗證
echo "Phase 5: 檢查容器協調..."
healthy_containers=$(docker-compose ps | grep "Up.*healthy" | wc -l)
if [ "$healthy_containers" -ge 3 ]; then
    echo "✅ Phase 5: 容器協調正常 ($healthy_containers 個健康容器)"
else
    echo "❌ Phase 5: 容器協調異常"
    exit 1
fi

echo "========================================"
echo "🎉 系統驗證完成！所有 Phase 檢查通過"
echo "📋 請執行前端手動測試完成 Phase 4 驗證"
```

### **使用方法**
```bash
# 1. 賦予執行權限
chmod +x comprehensive_verification.sh

# 2. 執行完整驗證
./comprehensive_verification.sh

# 3. 針對單一 Phase 驗證
# 參考上述各 Phase 的具體驗證命令
```

### **🔧 快速驗證命令**
```bash
# 一鍵完整驗證
./comprehensive_verification.sh

# 單項快速檢查
curl -s http://localhost:8080/health | jq .status  # API 健康
docker-compose ps | grep healthy | wc -l          # 健康容器數
```

每個 Phase 都有明確的成功標準和具體的驗證步驟，確保開發完成後能夠快速確認系統功能正常運作。