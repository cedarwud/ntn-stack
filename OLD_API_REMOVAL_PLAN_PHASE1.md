# 🧹 舊API清除計畫 - 階段1：安全移除

## ✅ 立即可移除的檔案和代碼 (低風險)

### 1. 配置檔案中的SimWorld URL
- **檔案**: `algorithm_ecosystem_config.yml` (2個位置)
- **內容**: `simworld_api_url: "http://simworld_backend:8000"`
- **風險**: 🟢 低 - 僅配置參數
- **動作**: 移除或註解掉

### 2. Docker Compose 環境變數  
- **檔案**: `compose/core.yaml`, `compose/core-simple.yaml`
- **內容**: `SIMWORLD_API_URL=http://simworld_backend:8000`
- **風險**: 🟢 低 - 未被使用的環境變數
- **動作**: 可安全移除

### 3. 路由器中的過時導入和函數
- **檔案**: `satellite_ops_router.py`
- **內容**: 已被清除的`_call_simworld_satellites_api`函數
- **風險**: 🟢 低 - 已被替換
- **動作**: 完成清理殘留依賴



## ⚠️ 需要評估的服務 (中風險)

### 核心服務分析：

#### 1. **SimWorldTLEBridgeService** 🚨 **關鍵決策點**
- **檔案**: `services/simworld_tle_bridge_service.py` (1014行)
- **被依賴**: 8個服務檔案
- **功能**: TLE數據橋接、軌道預測快取
- **評估**: 
  - ❓ **問題**: 是否還有其他系統在使用？
  - ❓ **替代**: Phase0預處理是否完全替代？
  - 🎯 **建議**: 需要確認無其他依賴後才能移除

#### 2. **受影響的8個服務檔案**：

##### 2.1 `satellite_gnb_mapping_service.py`
- **依賴度**: 🔴 高 - 核心功能依賴
- **風險**: 移除可能影響衛星-gNB映射功能
- **建議**: 需要確認是否有替代實現

##### 2.2 `paper_synchronized_algorithm.py`  
- **依賴度**: 🟡 中 - 論文算法實現
- **風險**: 可能影響研究功能
- **建議**: 確認論文算法是否仍在使用

##### 2.3 `fast_access_prediction_service.py`
- **依賴度**: 🟡 中 - 快速訪問預測
- **風險**: 可能影響預測功能  
- **建議**: 檢查是否有新的預測實現

##### 2.4 `algorithm_integration_bridge.py`
- **依賴度**: 🟡 中 - 算法整合橋接
- **風險**: 可能影響算法生態系統
- **建議**: 確認算法整合是否仍需要

##### 2.5 **Sionna相關服務** (3個檔案)
- `sionna_integration_service.py`
- `sionna_ueransim_integration_service.py`  
- `oneweb_satellite_gnb_service.py`
- **依賴度**: 🟢 低 - 可能未在目前系統中使用
- **建議**: 確認Sionna整合是否為活躍功能

##### 2.6 `unified_metrics_collector.py`
- **依賴度**: 🟡 中 - 監控功能
- **風險**: 影響系統監控
- **建議**: 需要為SimWorld監控提供替代方案


## 🔍 安全性檢查命令

### 檢查哪些API端點目前正在被調用：
```bash
# 檢查最近的API調用日誌
docker logs netstack-api | grep -E '(SimWorld|simworld|tle_bridge)' | tail -10

# 檢查是否有活躍的外部連接
netstat -an | grep :8000 || echo 'No external connections to SimWorld'

# 檢查Redis中是否有SimWorld相關的快取
docker exec netstack-redis redis-cli --scan --pattern '*simworld*' | head -5
```

### 檢查服務依賴：
```bash
# 檢查哪些API端點實際被前端調用
curl -s http://localhost:8080/docs | grep -A5 -B5 satellite
```
