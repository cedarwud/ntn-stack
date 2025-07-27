# SimWorld Backend TypeScript → Python 遷移計劃書

## 🎯 遷移目標
將 `simworld/backend/src/` 中的 TypeScript 衛星服務安全遷移到 Python (`app/`)，統一技術棧，消除重複實現，並整合數據緩存系統。

## 🔍 現況分析

### 📁 當前架構問題
```
simworld/backend/
├── app/          # Python FastAPI 主服務 (已有完整衛星功能)
│   ├── services/ # ✅ tle_data_service.py, historical_data_cache.py
│   └── domains/  # ✅ 完整的衛星計算域
├── src/          # ❌ Node.js TypeScript 重複服務
│   ├── services/ # 🔄 TLEDataService.ts, HistoricalDataCache.ts (重複)
│   ├── routes/   # 🔄 tle.ts (重複 API)
│   └── utils/    # 🔄 logger.ts
└── data/         # 🔄 外部數據緩存 (需整合)
    ├── tle_cache/      # TLE 緩存文件
    ├── tle_historical/ # 歷史數據
    └── batch_cache/    # 批次緩存
```

### ⚠️ 核心問題識別

#### 1. **技術債務嚴重**
- **雙重實現**: TLE 服務同時有 Python 和 TypeScript 版本
- **維護負擔**: 需要同時維護兩套相同功能的代碼
- **數據不一致風險**: 兩套緩存系統可能產生不同步

#### 2. **架構不清晰**
- **職責混亂**: 衛星計算功能分散在兩種語言中
- **部署複雜**: 需要 Python + Node.js 雙運行環境
- **調試困難**: 跨語言問題定位複雜

#### 3. **科學計算不適配**
- **生態系統**: TypeScript 缺乏成熟的衛星計算庫
- **精度問題**: JavaScript 數值計算精度不如 Python
- **學術標準**: 衛星研究領域主要使用 Python

### 🎯 遷移理由

#### **Python 在衛星計算的優勢**
- **成熟庫支援**: `skyfield`, `sgp4`, `numpy`, `scipy`
- **學術標準**: 符合衛星研究領域慣例
- **精度保證**: 高精度數值計算能力
- **算法移植**: 學術論文算法易於實現

#### **技術統一的好處**
- **簡化部署**: 單一運行環境 (Python)
- **代碼品質**: 消除重複實現
- **團隊效率**: 統一技術棧，減少學習成本
- **維護成本**: 單一代碼路徑

## 🛠️ 遷移策略

### 📋 總體原則
1. **安全第一**: 每步都有驗證和回滾機制
2. **漸進式**: 一個服務一個服務地遷移
3. **零停機**: 遷移過程中系統保持運行
4. **功能對等**: 確保遷移後功能完全一致
5. **數據保護**: 所有數據完整性得到保證

### Phase 1: 準備和備份階段 (安全基礎)
**目標**: 建立安全的遷移基礎，確保可以隨時回滾

#### 1.1 系統狀態檢查
```bash
# 檢查當前系統健康狀態
make status
docker logs simworld_backend 2>&1 | tail -20

# 確認 Python 服務正常運行
curl -s http://localhost:8888/health | jq

# 檢查 TypeScript 服務是否被實際使用
docker exec simworld_backend netstat -tlnp | grep 3000 || echo "TypeScript 服務未啟動"
```

#### 1.2 完整備份
```bash
# 備份整個 backend 目錄
cp -r simworld/backend simworld/backend_backup_$(date +%Y%m%d_%H%M%S)

# 備份數據緩存
cp -r simworld/backend/data simworld/backend/data_backup_$(date +%Y%m%d_%H%M%S)

# 備份當前 git 狀態
git stash push -m "遷移前狀態備份_$(date +%Y%m%d_%H%M%S)"
```

#### 1.3 功能基線建立
```bash
# 記錄當前 Python 服務的功能基線
curl -s http://localhost:8888/api/tle/constellations | jq > baseline_constellations.json
curl -s http://localhost:8888/api/tle/cache-stats | jq > baseline_cache_stats.json

# 測試關鍵 API 端點
echo "=== Python 服務功能基線 ===" > baseline_test.txt
curl -s http://localhost:8888/api/satellite-data/constellations/starlink/positions | jq '.satellites | length' >> baseline_test.txt
```

**Phase 1 驗收標準:**
- [ ] 系統完整備份完成
- [ ] 當前功能基線記錄完整
- [ ] 回滾機制驗證成功
- [ ] Python 服務運行正常

### Phase 2: 功能差異分析和增強階段
**目標**: 確保 Python 服務包含 TypeScript 服務的所有功能

#### 2.1 功能對比分析
```bash
# 分析 TypeScript 服務的獨特功能
echo "=== TypeScript 服務功能分析 ===" > ts_features.txt

# 檢查 TLEDataService.ts 的獨特方法
grep -n "export.*function\|async.*(" simworld/backend/src/services/TLEDataService.ts >> ts_features.txt

# 檢查 HistoricalDataCache.ts 的獨特功能
grep -n "export.*function\|async.*(" simworld/backend/src/services/HistoricalDataCache.ts >> ts_features.txt

# 分析路由差異
diff <(grep -r "router\." simworld/backend/src/routes/) <(grep -r "router\." simworld/backend/app/api/routes/) > route_diff.txt || true
```

#### 2.2 Python 服務功能增強
```python
# 如果發現 TypeScript 服務有 Python 服務缺失的功能，進行增強
# 例如：特殊的 TLE 解析邏輯、錯誤處理機制等

# 位置：app/services/tle_data_service.py
# 增加任何 TypeScript 版本獨有的功能
```

#### 2.3 API 端點對齊
```bash
# 確保 Python 服務提供所有 TypeScript 路由
# 檢查是否需要新增 API 端點

# 比較 API 路由
echo "TypeScript 路由:" > api_comparison.txt
grep -r "router\.\(get\|post\|put\|delete\)" simworld/backend/src/routes/ >> api_comparison.txt
echo -e "\nPython 路由:" >> api_comparison.txt  
grep -r "@router\.\(get\|post\|put\|delete\)" simworld/backend/app/api/routes/ >> api_comparison.txt
```

**Phase 2 驗收標準:**
- [ ] 功能差異分析完成
- [ ] Python 服務包含所有 TypeScript 功能
- [ ] API 端點完全對齊
- [ ] 功能測試全部通過

### Phase 3: 數據整合階段 (低風險)
**目標**: 將外部數據緩存整合到 Python 應用內

#### 3.1 數據目錄重組
```bash
# 在 app 內建立統一數據結構
mkdir -p simworld/backend/app/data/cache
mkdir -p simworld/backend/app/data/historical  
mkdir -p simworld/backend/app/data/batch

# 複製 (不是移動) 數據到新位置
cp -r simworld/backend/data/tle_cache/* simworld/backend/app/data/cache/
cp -r simworld/backend/data/tle_historical/* simworld/backend/app/data/historical/
cp -r simworld/backend/data/batch_cache/* simworld/backend/app/data/batch/
```

#### 3.2 Python 服務路徑更新
```python
# 更新 app/services/tle_data_service.py
# 從:
cache_dir = Path("./data/tle_cache")
# 改為:
cache_dir = Path("./app/data/cache")

# 更新 app/services/historical_data_cache.py  
# 從:
historical_dir = Path("./data/tle_historical")
# 改為:
historical_dir = Path("./app/data/historical")
```

#### 3.3 數據一致性驗證
```bash
# 重啟 Python 服務測試新數據路徑
make simworld-restart

# 驗證數據訪問正常
curl -s http://localhost:8888/api/tle/cache-stats | jq
curl -s http://localhost:8888/api/tle/constellations | jq

# 比較數據一致性
diff baseline_cache_stats.json <(curl -s http://localhost:8888/api/tle/cache-stats) || echo "數據路徑更新檢查"
```

**Phase 3 驗收標準:**
- [ ] 數據目錄成功整合到 app/data/
- [ ] Python 服務正常讀取新路徑數據
- [ ] 數據一致性驗證通過
- [ ] API 響應時間無明顯變化

### Phase 4: TypeScript 服務漸進移除階段 (高風險)
**目標**: 安全移除 TypeScript 服務，確保無影響

#### 4.1 TypeScript 服務使用檢查
```bash
# 檢查 TypeScript 服務是否真的在使用
ss -tlnp | grep :3000 || echo "✅ TypeScript 服務未監聽 3000 端口"

# 檢查進程
ps aux | grep -E "(node|ts-node)" | grep -v grep || echo "✅ 無 TypeScript 進程運行"

# 檢查容器內是否有 Node.js 服務
docker exec simworld_backend ps aux | grep -E "(node|ts-node)" || echo "✅ 容器內無 TypeScript 服務"
```

#### 4.2 逐步移除 (分階段)
```bash
# Stage 1: 移除測試文件 (最低風險)
rm -rf simworld/backend/src/test/
echo "✅ 移除測試文件完成"

# 重啟並驗證系統正常
make simworld-restart
curl -s http://localhost:8888/health | jq '.status' | grep -q "healthy" && echo "✅ 系統狀態正常"

# Stage 2: 移除工具類 (中等風險)  
rm -rf simworld/backend/src/utils/
echo "✅ 移除工具類完成"

# 重啟並驗證
make simworld-restart
curl -s http://localhost:8888/health | jq '.status' | grep -q "healthy" && echo "✅ 系統狀態正常"

# Stage 3: 移除路由 (較高風險)
rm -rf simworld/backend/src/routes/
echo "✅ 移除路由完成"

# 重啟並驗證
make simworld-restart
curl -s http://localhost:8888/health | jq '.status' | grep -q "healthy" && echo "✅ 系統狀態正常"

# Stage 4: 移除服務類 (最高風險)
rm -rf simworld/backend/src/services/
echo "✅ 移除服務類完成"

# 最終驗證
make simworld-restart
curl -s http://localhost:8888/health | jq '.status' | grep -q "healthy" && echo "✅ 系統狀態正常"
```

#### 4.3 每階段驗證
```bash
# 每移除一個目錄後都要執行的驗證
function verify_system() {
    echo "=== 系統驗證 $(date) ==="
    
    # 1. 容器狀態檢查
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep simworld
    
    # 2. 健康檢查
    curl -s http://localhost:8888/health | jq
    
    # 3. 關鍵 API 測試
    curl -s http://localhost:8888/api/tle/constellations | jq '.[] | .name' | head -3
    
    # 4. 錯誤日誌檢查
    docker logs simworld_backend 2>&1 | tail -5 | grep -i error && echo "❌ 發現錯誤" || echo "✅ 無錯誤"
    
    echo "=== 驗證完成 ==="
}
```

**Phase 4 驗收標準:**
- [ ] TypeScript 服務確認未被使用
- [ ] 逐步移除每階段驗證通過
- [ ] 系統功能完全正常
- [ ] 無任何錯誤日誌

### Phase 5: 清理和優化階段 (收尾)
**目標**: 清理殘餘文件，優化目錄結構

#### 5.1 目錄結構清理
```bash
# 移除空的 src 目錄
rmdir simworld/backend/src 2>/dev/null || rm -rf simworld/backend/src

# 移除舊的 data 目錄 (確保新路徑正常後)
if curl -s http://localhost:8888/api/tle/cache-stats | jq -e '.total_files > 0' >/dev/null; then
    echo "✅ 新數據路徑正常，移除舊 data 目錄"
    rm -rf simworld/backend/data
else
    echo "❌ 新數據路徑異常，保留舊 data 目錄"
fi
```

#### 5.2 文檔更新
```bash
# 更新 d2.md 中的路徑引用
sed -i 's|simworld/backend/src/|simworld/backend/app/|g' d2.md

# 更新項目文檔
echo "## 架構簡化完成
- ✅ 統一使用 Python 技術棧  
- ✅ 消除 TypeScript 重複實現
- ✅ 整合數據緩存到 app/data/
- ✅ 簡化部署和維護" >> simworld/backend/README.md
```

#### 5.3 最終系統驗證
```bash
# 完整系統測試
make down && make up
sleep 60
make status

# 功能完整性測試
echo "=== 最終功能驗證 ===" > final_verification.txt
curl -s http://localhost:8888/health | jq >> final_verification.txt
curl -s http://localhost:8888/api/tle/constellations | jq >> final_verification.txt
curl -s http://localhost:8888/api/satellite-data/constellations/starlink/positions | jq '.satellites | length' >> final_verification.txt

# 與基線對比
echo "=== 基線對比 ===" >> final_verification.txt
diff baseline_test.txt <(curl -s http://localhost:8888/api/satellite-data/constellations/starlink/positions | jq '.satellites | length') >> final_verification.txt || echo "功能對比完成" >> final_verification.txt
```

**Phase 5 驗收標準:**
- [ ] 所有 TypeScript 相關目錄已移除
- [ ] 數據路徑完全遷移到 app/data/
- [ ] 文檔引用已更新
- [ ] 最終功能測試與基線一致

## 🚨 風險控制措施

### 即時監控腳本
```bash
#!/bin/bash
# monitor_migration.sh - 遷移過程監控腳本

while true; do
    echo "=== $(date) 遷移監控 ==="
    
    # 1. 容器狀態
    docker ps --format "{{.Names}}: {{.Status}}" | grep simworld
    
    # 2. API 健康狀態
    if curl -s http://localhost:8888/health | jq -e '.status == "healthy"' >/dev/null; then
        echo "✅ API 健康"
    else
        echo "❌ API 異常 - 立即檢查！"
    fi
    
    # 3. 錯誤日誌監控
    error_count=$(docker logs simworld_backend 2>&1 | tail -10 | grep -c -i error)
    if [ $error_count -gt 0 ]; then
        echo "❌ 發現 $error_count 個錯誤"
        docker logs simworld_backend 2>&1 | tail -5
    else
        echo "✅ 無錯誤"
    fi
    
    echo ""
    sleep 30
done
```

### 緊急回滾程序
```bash
#!/bin/bash
# emergency_rollback.sh - 緊急回滾腳本

echo "🚨 執行緊急回滾..."

# 1. 停止當前服務
make simworld-stop

# 2. 恢復備份
if [ -d "simworld/backend_backup_*" ]; then
    latest_backup=$(ls -td simworld/backend_backup_* | head -1)
    echo "恢復備份: $latest_backup"
    
    rm -rf simworld/backend
    cp -r "$latest_backup" simworld/backend
    
    echo "✅ 備份恢復完成"
else
    echo "❌ 找不到備份目錄"
    exit 1
fi

# 3. 恢復 git 狀態
git stash pop

# 4. 重啟服務
make simworld-start

# 5. 驗證回滾成功
sleep 30
if curl -s http://localhost:8888/health | jq -e '.status == "healthy"' >/dev/null; then
    echo "✅ 回滾成功，系統正常"
else
    echo "❌ 回滾後系統異常，需要手動檢查"
fi
```

### 檢查點機制
```bash
# 每個 Phase 完成後建立檢查點
function create_checkpoint() {
    local phase_name=$1
    local checkpoint_dir="migration_checkpoints/phase_${phase_name}_$(date +%Y%m%d_%H%M%S)"
    
    mkdir -p "$checkpoint_dir"
    cp -r simworld/backend "$checkpoint_dir/"
    
    # 記錄系統狀態
    curl -s http://localhost:8888/health > "$checkpoint_dir/health_status.json"
    docker ps > "$checkpoint_dir/container_status.txt"
    
    echo "✅ 檢查點已建立: $checkpoint_dir"
}
```

## 📋 執行檢查清單

### 遷移前檢查
- [ ] 系統運行狀態正常
- [ ] 完整備份已建立
- [ ] 監控腳本已啟動  
- [ ] 回滾腳本已準備
- [ ] 團隊成員已通知

### 每階段檢查
- [ ] 階段目標明確理解
- [ ] 驗證腳本準備完成
- [ ] 執行步驟逐一完成
- [ ] 系統狀態持續正常
- [ ] 檢查點已建立

### 遷移後檢查
- [ ] 所有 TypeScript 代碼已移除
- [ ] Python 服務包含完整功能
- [ ] 數據緩存路徑統一
- [ ] 系統性能無退化
- [ ] 文檔已更新完成

## ⚡ 執行時程規劃

- **Phase 1**: 60 分鐘 (準備和備份)
- **Phase 2**: 90 分鐘 (功能分析和增強)  
- **Phase 3**: 45 分鐘 (數據整合)
- **Phase 4**: 60 分鐘 (服務移除)
- **Phase 5**: 30 分鐘 (清理優化)

**總估計時間**: 4.75 小時

## 🎯 成功標準

### 功能完整性
- ✅ 所有衛星相關 API 正常運作
- ✅ TLE 數據服務功能完整
- ✅ 歷史數據查詢正常
- ✅ 數據緩存機制穩定

### 架構清潔性
- ✅ 統一 Python 技術棧
- ✅ 無重複功能實現
- ✅ 清晰的代碼結構
- ✅ 簡化的部署流程

### 系統穩定性  
- ✅ 遷移後無錯誤日誌
- ✅ API 響應時間維持或改善
- ✅ 記憶體使用量優化
- ✅ 容器啟動時間改善

### 維護便利性
- ✅ 單一技術棧易於維護
- ✅ 代碼庫大小減少
- ✅ 依賴管理簡化
- ✅ 團隊學習成本降低

---

**⚠️ 重要提醒**: 此為技術棧統一的重要遷移，必須在具備完整備份和回滾能力的環境下進行。每個階段都要確保系統功能完全正常再進行下一步。

**🎯 遷移哲學**: "安全第一，功能對等，逐步漸進，可隨時回滾"