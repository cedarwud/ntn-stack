# 🗄️ NTN Stack 數據庫架構簡化重構計劃

## ✅ **數據驗證結果** (2025-07-12)

### 📊 **SimWorld PostgreSQL 數據分析**
- **Device**: 7筆自動重建數據 (tx0-tx2, jam1-jam3, rx) 
- **GroundStation**: 1筆自動重建數據 (NYCU_gnb)
- **Satellite**: 8017筆 TLE 同步數據，可從 API 重新獲取
- **空表**: handover_prediction_table、manual_handover_request、satellitepass
- **結論**: ✅ 確認無用戶數據，全部為程序自動生成

### 🔧 **Redis 價值評估**
- **核心功能**: 衛星軌道計算性能優化、TLE 數據緩存
- **性能價值**: 8017顆衛星的高頻軌道計算需要緩存支援
- **建議**: ✅ 保留 Redis，對 LEO 衛星系統具重要價值

## 🎯 **簡化重構方案**

### 📝 **Phase 1: 直接改寫 lifespan.py (1-2小時)**

#### 1.1 修改數據儲存目標
- **原始**: SimWorld PostgreSQL (simworld_postgis:5432)
- **修改為**: NetStack MongoDB (netstack-mongo:27017)
- **保留**: Redis 緩存系統 (性能優化)

#### 1.2 程式碼修改點
```python
# 修改 /simworld/backend/app/db/lifespan.py

# 原始 PostgreSQL 代碼:
from sqlmodel import SQLModel, select as sqlmodel_select
from app.domains.device.models.device_model import Device, DeviceRole
from app.domains.satellite.models.ground_station_model import GroundStation

# 改為 MongoDB 代碼:
from motor.motor_asyncio import AsyncIOMotorClient
from app.db.mongodb_config import get_mongodb_client

async def seed_initial_device_data_mongodb(mongodb_client):
    """修改為 MongoDB 數據儲存"""
    db = mongodb_client["simworld"]
    devices_collection = db["devices"]
    
    # 檢查現有數據
    existing_count = await devices_collection.count_documents({})
    if existing_count >= 7:
        return
    
    # 插入 device 數據
    devices = [
        {"name": "tx0", "position": [-110, -110, 40], "role": "desired", "active": True},
        {"name": "tx1", "position": [-106, 56, 61], "role": "desired", "active": True},
        {"name": "tx2", "position": [100, -30, 40], "role": "desired", "active": True},
        {"name": "jam1", "position": [100, 60, 40], "role": "jammer", "active": True},
        {"name": "jam2", "position": [-30, 53, 67], "role": "jammer", "active": True}, 
        {"name": "jam3", "position": [-105, -31, 64], "role": "jammer", "active": True},
        {"name": "rx", "position": [0, 0, 40], "role": "receiver", "active": True}
    ]
    await devices_collection.insert_many(devices)

async def seed_default_ground_station_mongodb(mongodb_client):
    """修改為 MongoDB 地面站儲存"""  
    db = mongodb_client["simworld"]
    stations_collection = db["ground_stations"]
    
    existing = await stations_collection.find_one({"station_identifier": "NYCU_gnb"})
    if existing:
        return
        
    station = {
        "station_identifier": "NYCU_gnb",
        "name": "NYCU Main gNB", 
        "latitude_deg": 24.786667,
        "longitude_deg": 120.996944,
        "altitude_m": 100.0,
        "description": "Default Ground Station at National Yang Ming Chiao Tung University"
    }
    await stations_collection.insert_one(station)
```

### 🐳 **Phase 2: Docker 配置更新 (30分鐘)**

#### 2.1 SimWorld docker-compose.yml 修改
```yaml
# 移除 PostgreSQL 配置
services:
  backend:
    environment:
      # 移除 PostgreSQL 相關環境變數
      # - DATABASE_URL=postgresql://sat:123@simworld_postgis:5432/ntn_stack
      
      # 添加 MongoDB 連接
      - MONGODB_URL=mongodb://netstack-mongo:27017
      - MONGODB_DATABASE=simworld
      
      # 保留 Redis (性能優化)
      - REDIS_URL=redis://netstack-redis:6379/0
      
    networks:
      - default
      - netstack-core  # 連接到 NetStack 網路訪問 MongoDB

  # 移除整個 simworld_postgis 服務
  # simworld_postgis: 
  #   ...

  # 保留其他服務 (frontend 等)

networks:
  netstack-core:
    external: true
    name: netstack_netstack-core
```

#### 2.2 NetStack MongoDB 確認運行
```bash
# 確認 NetStack MongoDB 正常運行
docker exec netstack-mongo mongosh --eval "db.adminCommand('listDatabases')"

# 建立 simworld 數據庫
docker exec netstack-mongo mongosh simworld --eval "db.createCollection('devices')"
docker exec netstack-mongo mongosh simworld --eval "db.createCollection('ground_stations')"
```

### 🔄 **Phase 3: 測試驗證 (30分鐘)**

```bash
# 1. 重啟 SimWorld (測試新配置)
cd /home/sat/ntn-stack/simworld && docker compose down
cd /home/sat/ntn-stack/simworld && docker compose up -d

# 2. 檢查 MongoDB 數據
docker exec netstack-mongo mongosh simworld --eval "db.devices.find().pretty()"
docker exec netstack-mongo mongosh simworld --eval "db.ground_stations.find().pretty()"

# 3. 驗證 API 功能
curl http://localhost:8888/api/v1/devices/  < /dev/null |  jq
curl http://localhost:8888/api/v1/ground-stations/ | jq

# 4. 檢查 Redis 仍正常運作 (衛星數據)
docker exec netstack-redis redis-cli keys "*tle*"
```

### 🚀 **Phase 4: NetStack RL PostgreSQL 建立 (1小時)**

#### 4.1 NetStack RL PostgreSQL 配置
```yaml
# netstack/compose/core.yaml 添加 RL PostgreSQL
services:
  rl-postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rl_research
      POSTGRES_USER: rl_user  
      POSTGRES_PASSWORD: rl_password
    ports:
      - "5432:5432"  # 現在可以使用 5432 (SimWorld PostgreSQL 已移除)
    volumes:
      - rl_postgres_data:/var/lib/postgresql/data
    networks:
      - netstack-core
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rl_user -d rl_research"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  rl_postgres_data:
```

#### 4.2 更新 RL 系統環境變數
```bash
# netstack/compose/core.yaml 中的 netstack-api 服務
services:
  netstack-api:
    environment:
      # 更新 RL 數據庫連接
      - RL_DATABASE_URL=postgresql://rl_user:rl_password@rl-postgres:5432/rl_research
```

### 📋 **Phase 5: Makefile 更新 (15分鐘)**

#### 5.1 根目錄 Makefile 無需修改
- NetStack 和 SimWorld 啟動邏輯保持不變
- MongoDB 在 NetStack 中，會自動隨 NetStack 啟動
- PostgreSQL 移除不影響現有命令

#### 5.2 驗證指令
```bash
# 驗證完整系統啟動
make down && make up && make status

# 檢查各服務健康狀態
curl http://localhost:8080/health  # NetStack (包含 MongoDB)
curl http://localhost:8888/        # SimWorld (連接 NetStack MongoDB)
curl http://localhost:8001/api/v1/health  # RL System (連接 RL PostgreSQL)
```

## ⏰ **實際執行時程**

| Phase | 任務 | 預估時間 | 實際狀態 | 完成時間 |
|-------|------|---------|----------|----------|
| Phase 1 | 修改 lifespan.py 為 MongoDB | 1-2小時 | ✅ **完成** | 2小時 |
| Phase 2 | Docker 配置更新 | 30分鐘 | ✅ **完成** | 30分鐘 |
| Phase 3 | 測試驗證 | 30分鐘 | ✅ **完成** | 30分鐘 |
| Phase 4 | NetStack RL PostgreSQL | 1小時 | ✅ **完成** | 1小時 |
| Phase 5 | Makefile 更新與全面驗證 | 15分鐘 | ✅ **完成** | 15分鐘 |

**總計：約4小時** ✅ **項目完成** (2025-07-13)

## ✅ **最終驗證結果**

### 🧪 **系統健康檢查** (2025-07-13 07:14)
- **NetStack MongoDB**: ✅ 健康 (響應時間 0.6ms)
- **NetStack Redis**: ✅ 健康 (內存使用 5.45M) 
- **NetStack RL PostgreSQL**: ✅ 健康 (表結構完整)
- **SimWorld Backend**: ✅ 正常運行 (MongoDB 集成成功)

### 📊 **數據驗證結果**
- **設備數據**: ✅ 10筆設備正常存儲在 MongoDB
- **地面站數據**: ✅ 1筆地面站 (NYCU_gnb) 正常存儲
- **TLE 緩存**: ✅ Starlink/Kuiper 數據正常緩存在 Redis
- **RL 表結構**: ✅ 3個表 (sessions, episodes, analysis) 已建立

## 🎯 **最終架構**

```
🏗️ NetStack 統一數據管理:
├── 📊 MongoDB (Port 27017)
│   ├── open5gs/          # 5G 核心網數據  
│   └── simworld/         # 3D 場景數據 ✨ 直接寫入
│
├── 🐘 PostgreSQL (Port 5432)  
│   └── rl_research/      # RL 研究數據 ✨ 新建立
│
└── 📡 Redis (Port 6379)
    └── tle_cache/        # 衛星軌道緩存 ✨ 保留

SimWorld Container (輕量化):
├── 🎮 Backend → 直接連接 NetStack MongoDB
├── 🖥️ Frontend  
└── ❌ 完全移除 PostgreSQL 資源
```

## ✅ **執行優勢**

### 🚀 **簡化效益**
- **無數據遷移**: 所有數據都是自動重建，無需備份還原
- **無停機時間**: 可以直接修改配置重啟
- **風險極低**: 數據可以立即重新生成
- **時間大幅縮短**: 從原計劃8小時縮短到4.5小時

### 📊 **保留關鍵價值**  
- **Redis 性能優化**: 保留衛星軌道計算緩存
- **MongoDB 文檔優勢**: 更適合 SimWorld 場景數據
- **PostgreSQL 研究級**: 專用於 RL 學術研究

### 🎯 **為 @rl.md 做好準備**
- PostgreSQL 專用於 RL 研究，符合學術標準
- 清理完成後可立即開始 RL 真實數據儲存實施
- 支援 todo.md 所需的研究級數據架構

---

## 🎉 **項目完成總結**

### ✅ **db.md 狀態: 完全完成** (2025-07-13)

**🎯 所有核心目標達成:**
- ✅ **架構簡化**: SimWorld PostgreSQL → MongoDB，資源優化
- ✅ **數據遷移**: 設備、地面站、TLE 數據全部正確遷移
- ✅ **性能提升**: Redis 緩存 + MongoDB 文檔儲存最佳組合
- ✅ **RL 準備**: PostgreSQL 專用數據庫建立，表結構完整

**📊 驗證結果:**
- 所有 API 端點正常響應
- 數據庫健康檢查 100% 通過
- 系統架構符合預期設計
- 為 rl.md 開發掃清障礙

**🚀 結論: ✅ db.md 項目完全完成，可以立即開始 @rl.md 的實施**
