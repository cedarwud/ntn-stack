# UAV 作為 UE 的模擬實現

## 概述

本文檔描述了「UAV 作為 UE 的模擬實現」功能的完整實現，該功能是 NTN Stack 專案中的重要組件，實現了無人機（UAV）作為 5G 用戶設備（UE）在非地面網路（NTN）環境中的模擬。

## 功能特性

### 核心功能

-   ✅ **軌跡管理**：支持 UAV 飛行軌跡的創建、編輯、查詢和刪除
-   ✅ **UAV 生命週期管理**：UAV 的創建、配置、狀態追蹤和刪除
-   ✅ **任務執行控制**：支持任務的開始、停止、暫停和進度監控
-   ✅ **實時位置追蹤**：動態更新 UAV 位置並同步到 SimWorld
-   ✅ **信號質量監測**：實時監測 RSRP、RSRQ、SINR 等無線指標
-   ✅ **UERANSIM 配置生成**：自動生成適用於 NTN 環境的 UE 配置文件
-   ✅ **網路自動切換**：基於信號質量的智能網路切換機制

### 技術特性

-   🔄 **異步任務管理**：支持多個 UAV 同時執行不同任務
-   📊 **實時狀態同步**：與 SimWorld 的 Sionna 信道模型整合
-   🛠️ **RESTful API**：完整的 HTTP API 接口
-   🧪 **完整測試覆蓋**：包含單元測試和整合測試
-   📈 **性能監控**：Prometheus 指標收集和健康檢查

## 系統架構

### 整體架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NetStack      │    │   SimWorld      │    │   UERANSIM      │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ UAV UE      │ │◄──►│ │ UAV Position│ │    │ │ UE Config   │ │
│ │ Service     │ │    │ │ Tracking    │ │    │ │ Files       │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │                 │
│ │ Trajectory  │ │    │ │ Sionna      │ │    │                 │
│ │ Management  │ │    │ │ Channel     │ │    │                 │
│ └─────────────┘ │    │ │ Model       │ │    │                 │
│ ┌─────────────┐ │    │ └─────────────┘ │    │                 │
│ │ Signal      │ │    │                 │    │                 │
│ │ Quality     │ │    │                 │    │                 │
│ └─────────────┘ │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 資料流程

1. **軌跡創建** → NetStack 儲存軌跡定義
2. **UAV 創建** → 生成 UERANSIM 配置文件
3. **任務開始** → 啟動異步位置更新任務
4. **位置更新** → NetStack → SimWorld → Sionna 信道模型更新
5. **信號監測** → 根據信號質量觸發網路切換

## API 接口

### 軌跡管理 API

#### 創建軌跡

```http
POST /api/v1/uav/trajectory
Content-Type: application/json

{
  "name": "偵察任務_001",
  "description": "海岸線偵察任務軌跡",
  "mission_type": "reconnaissance",
  "points": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "latitude": 24.7881,
      "longitude": 120.9971,
      "altitude": 100,
      "speed": 20.0,
      "heading": 45.0
    }
  ]
}
```

#### 查詢軌跡

```http
GET /api/v1/uav/trajectory/{trajectory_id}
```

#### 更新軌跡

```http
PUT /api/v1/uav/trajectory/{trajectory_id}
Content-Type: application/json

{
  "description": "更新後的描述"
}
```

#### 刪除軌跡

```http
DELETE /api/v1/uav/trajectory/{trajectory_id}
```

#### 列出所有軌跡

```http
GET /api/v1/uav/trajectory?limit=100&offset=0
```

### UAV 管理 API

#### 創建 UAV

```http
POST /api/v1/uav
Content-Type: application/json

{
  "name": "偵察UAV_001",
  "ue_config": {
    "imsi": "999700000000001",
    "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
    "opc": "E8ED289DEBA952E4283B54E88E6183CA",
    "plmn": "99970",
    "apn": "internet",
    "slice_nssai": {"sst": 1, "sd": "000001"},
    "gnb_ip": "172.20.0.40",
    "gnb_port": 38412,
    "power_dbm": 23.0,
    "frequency_mhz": 2150.0,
    "bandwidth_mhz": 20.0
  },
  "initial_position": {
    "latitude": 24.7881,
    "longitude": 120.9971,
    "altitude": 100,
    "speed": 0.0,
    "heading": 0.0
  }
}
```

#### 查詢 UAV 狀態

```http
GET /api/v1/uav/{uav_id}
```

#### 開始任務

```http
POST /api/v1/uav/{uav_id}/mission/start
Content-Type: application/json

{
  "trajectory_id": "trajectory_uuid",
  "speed_factor": 1.0,
  "start_time": "2024-01-01T10:00:00Z"
}
```

#### 停止任務

```http
POST /api/v1/uav/{uav_id}/mission/stop
```

#### 更新位置

```http
PUT /api/v1/uav/{uav_id}/position
Content-Type: application/json

{
  "position": {
    "latitude": 24.8000,
    "longitude": 121.0000,
    "altitude": 120,
    "speed": 15.0,
    "heading": 45.0
  },
  "signal_quality": {
    "rsrp_dbm": -80.0,
    "rsrq_db": -10.0,
    "sinr_db": 15.0,
    "cqi": 12,
    "throughput_mbps": 50.0,
    "latency_ms": 35.0,
    "packet_loss_rate": 0.01
  }
}
```

### 快速演示 API

#### 執行快速演示

```http
POST /api/v1/uav/demo/quick-test
```

## 使用指南

### 環境準備

1. **啟動服務**

```bash
# 啟動所有服務
make up

# 或者分別啟動
make netstack-start
make simworld-start
```

2. **檢查服務狀態**

```bash
make status
```

### 快速開始

#### 方法一：使用快速演示

```bash
# 執行完整的演示流程
make test-uav-ue-demo

# 或直接調用 API
curl -X POST http://localhost:8080/api/v1/uav/demo/quick-test
```

#### 方法二：手動創建軌跡和 UAV

1. **創建軌跡**

```bash
curl -X POST http://localhost:8080/api/v1/uav/trajectory \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試軌跡",
    "description": "手動創建的測試軌跡",
    "mission_type": "test",
    "points": [
      {
        "timestamp": "2024-01-01T10:00:00Z",
        "latitude": 24.7881,
        "longitude": 120.9971,
        "altitude": 100,
        "speed": 20.0,
        "heading": 0.0
      },
      {
        "timestamp": "2024-01-01T10:05:00Z",
        "latitude": 24.8000,
        "longitude": 121.0000,
        "altitude": 150,
        "speed": 25.0,
        "heading": 45.0
      }
    ]
  }'
```

2. **創建 UAV**

```bash
curl -X POST http://localhost:8080/api/v1/uav \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試UAV",
    "ue_config": {
      "imsi": "999700000000002",
      "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
      "opc": "E8ED289DEBA952E4283B54E88E6183CA"
    },
    "initial_position": {
      "latitude": 24.7881,
      "longitude": 120.9971,
      "altitude": 100
    }
  }'
```

3. **開始任務**

```bash
curl -X POST http://localhost:8080/api/v1/uav/{uav_id}/mission/start \
  -H "Content-Type: application/json" \
  -d '{
    "trajectory_id": "{trajectory_id}",
    "speed_factor": 1.0
  }'
```

### 監控和調試

#### 查看 UAV 狀態

```bash
# 查看特定 UAV
curl http://localhost:8080/api/v1/uav/{uav_id}

# 查看所有 UAV
curl http://localhost:8080/api/v1/uav
```

#### 查看軌跡資訊

```bash
# 查看特定軌跡
curl http://localhost:8080/api/v1/uav/trajectory/{trajectory_id}

# 查看所有軌跡
curl http://localhost:8080/api/v1/uav/trajectory
```

#### 查看 SimWorld 中的 UAV 位置

```bash
# 查看所有 UAV 位置
curl http://localhost:8888/api/v1/uav/positions

# 查看特定 UAV 位置
curl http://localhost:8888/api/v1/uav/{uav_id}/position
```

## 測試

### 測試類型

#### 1. 快速測試

```bash
make test-uav-ue-quick
```

檢查基本的 API 端點是否正常運作。

#### 2. 完整整合測試

```bash
make test-uav-ue
```

執行完整的功能測試，包括：

-   服務健康檢查
-   軌跡管理功能
-   UAV 管理功能
-   任務執行流程
-   SimWorld 整合
-   快速演示功能

#### 3. 手動測試

```bash
# 執行測試腳本
python3 tests/test_uav_ue_integration.py
```

### 測試場景

#### 場景 1：基本軌跡和 UAV 管理

-   創建軌跡
-   創建 UAV
-   查詢狀態
-   更新位置
-   清理資源

#### 場景 2：任務執行流程

-   開始任務
-   監控進度
-   位置自動更新
-   停止任務

#### 場景 3：信號質量監測

-   模擬信號衰減
-   觸發網路切換
-   恢復信號品質

#### 場景 4：多 UAV 並發

-   同時創建多個 UAV
-   並發執行不同任務
-   資源競爭處理

## 配置參數

### 環境變數

-   `UAV_UPDATE_INTERVAL`: UAV 位置更新間隔（秒），預設 5.0
-   `UERANSIM_CONFIG_DIR`: UERANSIM 配置文件目錄，預設 `/tmp/ueransim_configs`
-   `SIMWORLD_API_URL`: SimWorld API 地址，預設 `http://simworld-backend:8000`

### UERANSIM 配置

UAV UE 服務會自動生成針對 NTN 環境優化的 UERANSIM 配置：

-   **延遲容忍**: NAS 定時器調整為 NTN 環境
-   **功率控制**: 根據 UAV 高度和距離調整發射功率
-   **頻率補償**: 支持都卜勒頻移補償
-   **重連機制**: 優化的連接重建流程

## 故障排除

### 常見問題

#### 1. 服務連接失敗

```bash
# 檢查服務狀態
make status

# 查看服務日誌
make logs
```

#### 2. UAV 創建失敗

-   檢查 IMSI 格式（必須為 15 位數字）
-   確認 gNodeB IP 地址可達
-   驗證 MongoDB 連接

#### 3. 任務執行異常

-   確認軌跡存在且有效
-   檢查軌跡點時間戳順序
-   驗證 UAV 狀態

#### 4. SimWorld 整合問題

-   確認 SimWorld 服務運行
-   檢查網路連接
-   驗證 API 端點

### 日誌分析

#### NetStack 日誌

```bash
docker logs netstack-api | grep -i uav
```

#### SimWorld 日誌

```bash
docker logs simworld_backend | grep -i uav
```

#### 結構化日誌查詢

```bash
# 查找特定 UAV 的日誌
docker logs netstack-api 2>&1 | jq 'select(.uav_id == "target_uav_id")'
```

## 性能考量

### 系統資源

-   **記憶體使用**: 每個 UAV 約占用 1-2MB 記憶體
-   **CPU 負載**: 位置更新任務使用異步處理，CPU 負載低
-   **網路頻寬**: 位置更新頻率可調整，預設每 5 秒一次

### 擴展性

-   **並發 UAV 數量**: 理論上無限制，實際受硬體資源限制
-   **軌跡複雜度**: 支持任意複雜度的軌跡
-   **更新頻率**: 可根據需求調整更新間隔

### 性能優化

-   使用 Redis 快取頻繁查詢的資料
-   批次處理多個 UAV 的位置更新
-   異步處理信道模型更新

## 安全考量

### 數據保護

-   UAV IMSI 和認證密鑰加密存儲
-   API 端點支持認證和授權
-   敏感資料不在日誌中顯示

### 網路安全

-   支持 HTTPS/TLS 加密通信
-   API 速率限制
-   輸入驗證和參數檢查

## 後續發展

### 計劃功能

-   [ ] 支持真實 UAV 硬體整合
-   [ ] 進階路徑規劃算法
-   [ ] 機器學習基礎的信號預測
-   [ ] 3D 視覺化介面
-   [ ] 集群任務協調

### 技術改進

-   [ ] GraphQL API 支持
-   [ ] WebSocket 實時通信
-   [ ] 分散式部署支援
-   [ ] 效能指標更詳細收集

## 結論

UAV UE 功能的實現為 NTN Stack 專案提供了完整的無人機模擬能力，支持從軌跡規劃到任務執行的全生命週期管理。透過與 SimWorld 的整合，實現了真實的無線通道模擬，為 5G NTN 研究和開發提供了強大的工具。

該實現採用現代化的微服務架構，具有良好的擴展性和可維護性，同時提供了完整的測試覆蓋和文檔支持，確保系統的可靠性和易用性。
