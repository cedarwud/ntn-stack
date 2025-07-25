# 00 - 驗收標準與驗證機制

> **回到總覽**：[README.md](./README.md)

## 🎯 驗收標準總覽

### 📋 Phase 驗證機制與完成確認

#### ✅ Phase 1: PostgreSQL 數據架構 - 驗證機制

**1.1 後端數據庫驗證**
```bash
# 檢查 PostgreSQL 表結構
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT table_name, column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'satellite_orbital_cache'
ORDER BY ordinal_position;"

# 檢查索引創建
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'satellite_orbital_cache'
ORDER BY tablename;"
```

**1.2 完成確認檢查清單**
- [ ] **數據庫表創建**: 表結構正確，索引創建成功
- [ ] **PostgreSQL 健康檢查**: 連接成功且響應時間 < 100ms
- [ ] **API 響應**: `/health` 端點返回 200 狀態

#### ✅ Phase 2: 數據預計算引擎 - 驗證機制

**2.1 TLE 數據下載驗證**
```bash
# 測試 TLE 數據獲取功能
curl -X POST "http://localhost:8080/api/v1/satellites/tle/download" \
  -H "Content-Type: application/json" \
  -d '{
    "constellations": ["starlink"],
    "force_update": false
  }'  < /dev/null |  jq
```

**2.2 完成確認檢查清單**
- [ ] **TLE 下載**: 成功獲取多星座 TLE 數據 (< 5 秒)
- [ ] **數據解析**: SGP4 軌道計算正確無誤差
- [ ] **批量存儲**: 插入效能 > 1000 條/秒
- [ ] **預計算完整性**: 6 小時數據覆蓋無遺漏時間點

#### ✅ Phase 3: API 端點實現 - 驗證機制

**3.1 衛星位置查詢驗證**
```bash
# 查詢特定時間點的衛星位置
curl -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" \
  -d "min_elevation=10" | jq
```

**3.2 完成確認檢查清單**
- [ ] **位置查詢**: 響應時間 < 100ms，數據準確
- [ ] **時間軸端點**: 正確返回數據範圍和統計
- [ ] **軌跡查詢**: 支援任意時間區間查詢
- [ ] **錯誤處理**: 無效參數返回適當錯誤訊息

#### ✅ Phase 4: 前端時間軸控制 - 驗證機制

**4.1 功能交互驗證**
```javascript
// 在瀏覽器 Console 中執行
console.log("=== 功能交互驗證 ===");

// 檢查星座選擇器
const constellationSelect = document.querySelector('.constellation-selector');
console.log("星座選擇器存在:", \!\!constellationSelect);

// 檢查時間軸控制器
const timelineControl = document.querySelector('.timeline-control');
console.log("時間軸控制器存在:", \!\!timelineControl);
```

**4.2 完成確認檢查清單**
- [ ] **星座選擇器**: 正確顯示多星座選項，有圖示和統計資訊
- [ ] **API 整合**: 選擇星座時正確調用端點
- [ ] **時間軸控制**: 播放/暫停/倍速功能正常運作
- [ ] **數據同步**: 時間變更時正確觸發回調函數
- [ ] **響應式設計**: 在不同螢幕尺寸下正常顯示

#### ✅ Phase 5: 容器啟動順序和智能更新 - 驗證機制

**5.1 容器啟動順序驗證**
```bash
# 檢查容器啟動順序和依賴關係
docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}"

# 檢查健康檢查狀態
docker inspect netstack-rl-postgres --format '{{.State.Health.Status}}'
docker inspect netstack-api --format '{{.State.Health.Status}}'
```

**5.2 完成確認檢查清單**
- [ ] **容器啟動順序**: PostgreSQL → NetStack API → SimWorld，依賴關係正確
- [ ] **啟動時間**: 完整系統啟動 < 120 秒 (包含數據載入)
- [ ] **數據持久性**: 容器重啟後數據完整保留
- [ ] **立即可用性**: 服務啟動後 10 秒內 API 可用且有數據
- [ ] **健康監控**: 所有服務健康檢查通過，資源使用合理

## 🚀 整體系統驗證流程

### **完整驗證腳本**
```bash
#\!/bin/bash
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

## 🔧 快速驗證命令

```bash
# 一鍵完整驗證
./comprehensive_verification.sh

# 單項快速檢查
curl -s http://localhost:8080/health | jq .status  # API 健康
docker-compose ps | grep healthy | wc -l          # 健康容器數
```

每個 Phase 都有明確的成功標準和具體的驗證步驟，確保開發完成後能夠快速確認系統功能正常運作。

