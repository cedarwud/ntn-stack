# 🗄️ NTN Stack 數據庫架構重構計劃

## 🎯 **重構目標**

本文檔詳細記錄從 SimWorld PostgreSQL/PostGIS 遷移到 NetStack 統一數據庫管理的完整流程：

1. **SimWorld PostgreSQL → NetStack MongoDB** (統一文檔型數據管理)
2. **NetStack 新建 PostgreSQL** (專用於 RL 研究級數據)
3. **完整清理 SimWorld PostgreSQL 資源** (容器、映像檔、Volume、Network、程式邏輯)
4. **更新所有配置文件** (Docker、Makefile、requirements.txt)

### 📊 **最終架構目標**
```
🏗️ NetStack 統一數據管理中心:
├── 📊 MongoDB (Port 27017)
│   ├── open5gs/          # 5G 核心網數據
│   └── simworld/         # 3D 場景數據 ✨ 新遷移
│
├── 🐘 PostgreSQL (Port 5433)  
│   └── rl_research/      # RL 研究數據 ✨ 新建立
│
└── 📡 Redis (Port 6379)
    └── cache/            # 緩存和即時數據

SimWorld Container (輕量化):
├── 🎮 Backend → 連接 NetStack MongoDB
├── 🖥️ Frontend
└── ❌ 移除所有 PostgreSQL 資源
```

---

## 📋 **執行階段概覽**

 < /dev/null |  階段 | 任務 | 預估時間 | 驗證標準 |
|-----|------|---------|---------|
| Phase 1 | SimWorld 數據遷移至 NetStack MongoDB | 2-3 小時 | SimWorld 正常連接 MongoDB |
| Phase 2 | 清理 SimWorld PostgreSQL 資源 | 1-2 小時 | 所有 PostgreSQL 資源完全移除 |
| Phase 3 | NetStack 建立 RL PostgreSQL | 1-2 小時 | RL 系統可連接 PostgreSQL |
| Phase 4 | 更新 Makefile 和驗證 | 1 小時 | 所有指令正常運作 |

**總計：5-8 小時**

---

## 🚀 **Phase 1: SimWorld 數據遷移 (2-3 小時)**

### 🔍 **1.1 預遷移準備**

#### **檢查現有數據結構**
```bash
# 1. 檢查 SimWorld 現有數據
docker exec -it simworld_postgis psql -U sat -d ntn_stack -c "\dt"

# 2. 備份重要數據
docker exec simworld_postgis pg_dump -U sat -d ntn_stack > simworld_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. 檢查 NetStack MongoDB 狀態
docker exec -it netstack-mongo mongosh --eval "db.adminCommand('listDatabases')"
```

### 📊 **1.2 創建數據遷移腳本**

#### **創建遷移腳本目錄**
```bash
# 創建遷移腳本目錄
mkdir -p scripts/migration
```

#### **數據遷移腳本: scripts/migration/migrate_simworld_to_mongo.py**
```python
#\!/usr/bin/env python3
"""
SimWorld PostgreSQL to NetStack MongoDB Migration Script
遷移 SimWorld 的場景配置數據到 NetStack MongoDB
"""

import asyncio
import asyncpg
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimWorldDataMigrator:
    def __init__(self):
        # PostgreSQL 連接配置
        self.pg_url = "postgresql://sat:123@localhost:5432/ntn_stack"
        # MongoDB 連接配置  
        self.mongo_url = "mongodb://localhost:27017"
        self.mongo_db_name = "simworld"
        
    async def connect_databases(self):
        """建立數據庫連接"""
        try:
            # 連接 PostgreSQL
            self.pg_conn = await asyncpg.connect(self.pg_url)
            logger.info("✅ PostgreSQL 連接成功")
            
            # 連接 MongoDB
            self.mongo_client = AsyncIOMotorClient(self.mongo_url)
            self.simworld_db = self.mongo_client[self.mongo_db_name]
            logger.info("✅ MongoDB 連接成功")
            
        except Exception as e:
            logger.error(f"❌ 數據庫連接失敗: {e}")
            raise

    async def migrate_scene_configs(self):
        """遷移場景配置數據"""
        try:
            # 檢查是否有場景配置表
            tables = await self.pg_conn.fetch(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            table_names = [table['table_name'] for table in tables]
            logger.info(f"📋 發現的表: {table_names}")
            
            # 如果有場景相關的表，進行遷移
            if any('scene' in table.lower() for table in table_names):
                scenes = await self.pg_conn.fetch("SELECT * FROM scenes")
                for scene in scenes:
                    scene_doc = {
                        "scene_id": scene.get("id") or scene.get("scene_id"),
                        "name": scene.get("name"),
                        "config": scene.get("config"),
                        "created_at": scene.get("created_at") or datetime.now(),
                        "migrated_at": datetime.now()
                    }
                    await self.simworld_db.scenes.insert_one(scene_doc)
                logger.info(f"✅ 遷移了 {len(scenes)} 個場景配置")
            
            # 創建基本集合結構
            collections = ["scenes", "render_configs", "user_preferences", "performance_metrics"]
            for collection in collections:
                await self.simworld_db.create_collection(collection)
                logger.info(f"✅ 創建集合: {collection}")
                
        except Exception as e:
            logger.warning(f"⚠️ 場景數據遷移警告: {e}")

    async def create_default_data(self):
        """創建預設數據"""
        try:
            # 創建預設場景配置
            default_scenes = [
                {
                    "scene_id": "nycu_campus",
                    "name": "NYCU Campus",
                    "config": {
                        "model_path": "/app/static/scenes/NYCU/NYCU.glb",
                        "xml_path": "/app/static/scenes/NYCU/NYCU.xml",
                        "render_settings": {
                            "quality": "high",
                            "lighting": "dynamic",
                            "effects": True
                        }
                    },
                    "created_at": datetime.now()
                },
                {
                    "scene_id": "default_scene",
                    "name": "Default Scene",
                    "config": {
                        "model_path": "/app/static/models/default.glb",
                        "render_settings": {
                            "quality": "medium",
                            "lighting": "static",
                            "effects": False
                        }
                    },
                    "created_at": datetime.now()
                }
            ]
            
            for scene in default_scenes:
                await self.simworld_db.scenes.replace_one(
                    {"scene_id": scene["scene_id"]},
                    scene,
                    upsert=True
                )
            
            logger.info("✅ 創建了預設場景配置")
            
        except Exception as e:
            logger.error(f"❌ 創建預設數據失敗: {e}")

    async def verify_migration(self):
        """驗證遷移結果"""
        try:
            # 檢查 MongoDB 數據
            scene_count = await self.simworld_db.scenes.count_documents({})
            collections = await self.simworld_db.list_collection_names()
            
            logger.info(f"✅ 遷移驗證通過:")
            logger.info(f"   - 場景數量: {scene_count}")
            logger.info(f"   - 集合列表: {collections}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 遷移驗證失敗: {e}")
            return False

    async def close_connections(self):
        """關閉數據庫連接"""
        if hasattr(self, 'pg_conn'):
            await self.pg_conn.close()
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()

    async def run_migration(self):
        """執行完整遷移流程"""
        try:
            logger.info("🚀 開始 SimWorld 數據遷移...")
            
            await self.connect_databases()
            await self.migrate_scene_configs()
            await self.create_default_data()
            
            if await self.verify_migration():
                logger.info("✅ SimWorld 數據遷移完成！")
                return True
            else:
                logger.error("❌ 遷移驗證失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 遷移過程中發生錯誤: {e}")
            return False
        finally:
            await self.close_connections()

if __name__ == "__main__":
    migrator = SimWorldDataMigrator()
    result = asyncio.run(migrator.run_migration())
    exit(0 if result else 1)
```

### 🔄 **1.3 執行數據遷移**

```bash
# 1. 確保服務運行
make status

# 2. 安裝遷移腳本依賴
pip install asyncpg motor

# 3. 執行數據遷移
cd /home/sat/ntn-stack
python scripts/migration/migrate_simworld_to_mongo.py

# 4. 驗證遷移結果
docker exec -it netstack-mongo mongosh simworld --eval "db.scenes.find().pretty()"
```

### 📝 **1.4 更新 SimWorld 配置連接 MongoDB**

#### **更新 simworld/backend/app/core/config.py**
```python
# 更新數據庫 URL 配置
DATABASE_URL = "mongodb://netstack-mongo:27017/simworld"

# 移除 PostgreSQL 相關配置
# 註釋或刪除所有 postgresql+asyncpg 相關代碼
```

#### **更新 simworld/backend/requirements.txt**
```txt
# 移除 PostgreSQL 相關依賴
# asyncpg>=0.29.0
# psycopg2-binary>=2.9.9

# 新增 MongoDB 依賴
motor>=3.3.0
pymongo>=4.6.0
```

#### **更新 simworld/backend/app/database.py (如果存在)**
```python
# 替換為 MongoDB 連接邏輯
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import DATABASE_URL

class Database:
    client: AsyncIOMotorClient = None
    database = None

    async def connect_to_mongo(self):
        self.client = AsyncIOMotorClient(DATABASE_URL)
        self.database = self.client.simworld

    async def close_mongo_connection(self):
        if self.client:
            self.client.close()

db = Database()
```

### ✅ **1.5 測試 SimWorld MongoDB 連接**

```bash
# 1. 重建 SimWorld 容器
cd simworld
docker compose build backend

# 2. 重啟 SimWorld
make simworld-restart

# 3. 檢查連接狀態
curl http://localhost:8888/health

# 4. 查看日誌確認無 PostgreSQL 錯誤
docker logs simworld_backend
```

---

## 🧹 **Phase 2: 清理 SimWorld PostgreSQL 資源 (1-2 小時)**

### 🚫 **2.1 停止並移除 PostgreSQL 容器**

```bash
# 1. 停止 SimWorld 服務
make simworld-stop

# 2. 完全移除 SimWorld PostgreSQL 容器和資源
cd simworld
docker compose down -v --remove-orphans

# 3. 手動清理 PostgreSQL 相關資源
docker container rm simworld_postgis || true
docker volume rm simworld_postgres_data || true
docker image rm postgis/postgis:16-3.4 || true

# 4. 清理網路
docker network rm simworld_sionna-net || true
docker network prune -f
```

### 📄 **2.2 更新 SimWorld Docker Compose**

#### **完全重寫 simworld/docker-compose.yml**
```yaml
# SimWorld Docker Compose - MongoDB 版本
services:
    backend:
        build:
            context: ./backend
            dockerfile: Dockerfile
        container_name: simworld_backend
        ports:
            - '8888:8000'
        volumes:
            - ./backend:/app
        env_file:
            - ./backend/.env
        environment:
            # === 渲染和計算模式設定 ===
            CUDA_VISIBLE_DEVICES: '-1'
            PYOPENGL_PLATFORM: 'egl'
            PYRENDER_BACKEND: 'pyglet'
            PYTHONUNBUFFERED: '1'
            
            # === 數據庫連接 ===
            DATABASE_URL: mongodb://netstack-mongo:27017/simworld
            
            # === Redis 連接 ===
            REDIS_URL: redis://netstack-redis:6379/0
            
            # === 外部 IP 設定 ===
            EXTERNAL_IP: ${EXTERNAL_IP:-127.0.0.1}

        networks:
            - sionna-net
            - netstack-core
        
        healthcheck:
            test:
                [
                    'CMD-SHELL',
                    'python -c "import socket; s = socket.create_connection((\"localhost\", 8000), timeout=5)" || exit 1',
                ]
            interval: 10s
            timeout: 5s
            retries: 5
            start_period: 30s

    frontend:
        build:
            context: ./frontend
            dockerfile: Dockerfile
        container_name: simworld_frontend
        ports:
            - '5173:5173'
        volumes:
            - ./frontend:/app
            - node_modules:/app/node_modules
        environment:
            VITE_ENV_MODE: docker
            VITE_NETSTACK_URL: /netstack
            VITE_SIMWORLD_URL: /api
            VITE_NETSTACK_PROXY_TARGET: http://netstack-api:8080
            VITE_SIMWORLD_PROXY_TARGET: http://simworld_backend:8000
            VITE_PORT: 5173
            VITE_DEBUG: true
        networks:
            - sionna-net
            - netstack-core
        depends_on:
            backend:
                condition: service_healthy

networks:
    sionna-net:
        driver: bridge
    netstack-core:
        external: true
        name: compose_netstack-core

volumes:
    node_modules:
```

### 🗑️ **2.3 清理 SimWorld 程式邏輯中的 PostgreSQL 程式碼**

#### **移除 PostgreSQL 相關程式碼**
```bash
# 1. 搜尋並記錄所有 PostgreSQL 相關檔案
cd simworld/backend
find . -name "*.py" -exec grep -l "postgresql\|asyncpg\|psycopg2\|PostGIS" {} \;

# 2. 手動編輯每個檔案，移除 PostgreSQL 相關程式碼
# 主要檔案可能包括：
# - app/core/config.py
# - app/database.py  
# - app/models/
# - app/api/
```

#### **更新 Dockerfile (移除 PostgreSQL 依賴)**
```dockerfile
# simworld/backend/Dockerfile
# 移除所有 PostgreSQL 相關的系統依賴
# 例如：libpq-dev, postgresql-client 等

FROM python:3.11-slim

# 只保留必要的系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### ✅ **2.4 驗證清理完成**

```bash
# 1. 檢查沒有 PostgreSQL 容器
docker ps -a | grep postgres

# 2. 檢查沒有 PostgreSQL 映像檔
docker images | grep postgres

# 3. 檢查沒有 PostgreSQL Volume
docker volume ls | grep postgres

# 4. 重新啟動 SimWorld 驗證
make simworld-restart

# 5. 確認服務正常
curl http://localhost:8888/health
```

---

## 🐘 **Phase 3: NetStack 建立 RL PostgreSQL (1-2 小時)**

### 📊 **3.1 更新 NetStack Docker Compose**

#### **編輯 netstack/compose/core.yaml - 新增 PostgreSQL 服務**
```yaml
# 在現有服務後新增 RL PostgreSQL
services:
  # ... 現有服務 (mongo, redis, 5G 核心網服務)

  # RL 研究級 PostgreSQL 數據庫
  postgres-rl:
    image: postgres:16
    container_name: netstack-postgres-rl
    hostname: postgres-rl
    environment:
      POSTGRES_DB: rl_research
      POSTGRES_USER: rl_user
      POSTGRES_PASSWORD: rl_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    ports:
      - "5432:5432"  # SimWorld PostgreSQL 已移除，直接使用標準端口
    volumes:
      - postgres_rl_data:/var/lib/postgresql/data
      - ../rl_system/sql/init.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ../rl_system/sql/research_schema.sql:/docker-entrypoint-initdb.d/02-research_schema.sql
    networks:
      netstack-core:
        ipv4_address: 172.20.0.70
        aliases:
          - postgres-rl
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rl_user -d rl_research"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

volumes:
  # ... 現有 volumes
  postgres_rl_data:
    driver: local
```

### 📝 **3.2 創建 RL PostgreSQL 初始化腳本**

#### **創建目錄結構**
```bash
mkdir -p netstack/rl_system/sql
```

#### **netstack/rl_system/sql/init.sql**
```sql
-- RL PostgreSQL 初始化腳本
-- 基礎數據庫和用戶配置

-- 確保數據庫存在
SELECT 'CREATE DATABASE rl_research' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'rl_research')\gexec

-- 設置基本配置
ALTER DATABASE rl_research SET timezone = 'UTC';
ALTER DATABASE rl_research SET client_encoding = 'UTF8';
ALTER DATABASE rl_research SET default_transaction_isolation = 'read committed';

-- 創建擴展 (如果需要)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 記錄初始化完成
INSERT INTO pg_database (datname) VALUES ('rl_research') ON CONFLICT DO NOTHING;
```

#### **netstack/rl_system/sql/research_schema.sql**
```sql
-- RL 研究級數據表設計
-- 基於 @rl.md 的學術研究需求

-- 研究實驗會話表（支援 todo.md 實驗追蹤）
CREATE TABLE IF NOT EXISTS rl_experiment_sessions (
    id BIGSERIAL PRIMARY KEY,
    experiment_name VARCHAR(100) NOT NULL,
    algorithm_type VARCHAR(20) NOT NULL CHECK (algorithm_type IN ('DQN', 'PPO', 'SAC', 'A3C')),
    scenario_type VARCHAR(50), -- urban, suburban, low_latency, maritime
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_episodes INTEGER DEFAULT 0,
    session_status VARCHAR(20) DEFAULT 'running' CHECK (session_status IN ('running', 'completed', 'failed', 'paused')),
    hyperparameters JSONB, -- 完整的超參數記錄
    research_notes TEXT, -- 支援學術研究記錄
    baseline_comparison JSONB, -- IEEE/3GPP baseline 比較數據
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 詳細訓練 episode 數據（支援決策透明化）
CREATE TABLE IF NOT EXISTS rl_training_episodes (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES rl_experiment_sessions(id) ON DELETE CASCADE,
    episode_number INTEGER NOT NULL,
    total_reward FLOAT,
    success_rate FLOAT,
    handover_latency_ms FLOAT, -- 支援 todo.md 性能分析
    decision_confidence FLOAT, -- 支援 Algorithm Explainability
    candidate_satellites JSONB, -- 支援候選篩選視覺化
    decision_reasoning JSONB, -- 支援決策透明化
    q_values JSONB, -- DQN Q值分布
    policy_gradients JSONB, -- PPO/SAC policy gradient 數據
    exploration_rate FLOAT, -- ε-greedy 探索率
    network_loss FLOAT, -- 神經網路損失函數值
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 決策分析數據（支援 todo.md 視覺化）
CREATE TABLE IF NOT EXISTS rl_decision_analysis (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES rl_experiment_sessions(id) ON DELETE CASCADE,
    episode_number INTEGER,
    candidate_satellites JSONB, -- 所有候選衛星信息
    scoring_details JSONB, -- 每個候選的評分細節
    selected_satellite_id VARCHAR(50),
    decision_factors JSONB, -- 決策因子權重 (信號強度、負載、仰角)
    confidence_level FLOAT,
    reasoning_path JSONB, -- Algorithm Explainability 數據
    statistical_significance JSONB, -- 統計顯著性數據
    baseline_comparison JSONB, -- 與 baseline 算法比較
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 算法性能比較表（支援學術研究）
CREATE TABLE IF NOT EXISTS rl_algorithm_performance (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES rl_experiment_sessions(id) ON DELETE CASCADE,
    algorithm_type VARCHAR(20) NOT NULL,
    convergence_rate FLOAT, -- 收斂速度
    stability_metric FLOAT, -- 穩定性指標
    robustness_score FLOAT, -- 魯棒性評分
    baseline_improvement FLOAT, -- 相對於 baseline 的改善百分比
    statistical_p_value FLOAT, -- 統計顯著性 p 值
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 實驗配置版本控制表
CREATE TABLE IF NOT EXISTS rl_experiment_configs (
    id BIGSERIAL PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL,
    config_version VARCHAR(20) NOT NULL,
    config_data JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(config_name, config_version)
);

-- 創建索引提升查詢性能
CREATE INDEX IF NOT EXISTS idx_experiment_sessions_algorithm_scenario 
ON rl_experiment_sessions(algorithm_type, scenario_type);

CREATE INDEX IF NOT EXISTS idx_training_episodes_session_episode 
ON rl_training_episodes(session_id, episode_number);

CREATE INDEX IF NOT EXISTS idx_decision_analysis_session_episode 
ON rl_decision_analysis(session_id, episode_number);

CREATE INDEX IF NOT EXISTS idx_algorithm_performance_session_algorithm 
ON rl_algorithm_performance(session_id, algorithm_type);

-- 創建視圖支援複雜查詢
CREATE OR REPLACE VIEW rl_experiment_summary AS
SELECT 
    s.id,
    s.experiment_name,
    s.algorithm_type,
    s.scenario_type,
    s.total_episodes,
    s.session_status,
    s.start_time,
    s.end_time,
    AVG(e.total_reward) as avg_reward,
    AVG(e.success_rate) as avg_success_rate,
    AVG(e.handover_latency_ms) as avg_latency,
    COUNT(e.id) as completed_episodes
FROM rl_experiment_sessions s
LEFT JOIN rl_training_episodes e ON s.id = e.session_id
GROUP BY s.id, s.experiment_name, s.algorithm_type, s.scenario_type, 
         s.total_episodes, s.session_status, s.start_time, s.end_time;

-- 插入示例配置數據
INSERT INTO rl_experiment_configs (config_name, config_version, config_data, description) VALUES
('dqn_default', 'v1.0', '{"learning_rate": 0.001, "epsilon": 0.1, "batch_size": 32, "memory_size": 10000}', 'DQN 預設配置'),
('ppo_default', 'v1.0', '{"learning_rate": 0.0003, "clip_ratio": 0.2, "batch_size": 64, "epochs": 10}', 'PPO 預設配置'),
('sac_default', 'v1.0', '{"learning_rate": 0.0003, "tau": 0.005, "alpha": 0.2, "batch_size": 256}', 'SAC 預設配置')
ON CONFLICT (config_name, config_version) DO NOTHING;

-- 記錄架構初始化完成
CREATE TABLE IF NOT EXISTS rl_schema_version (
    version VARCHAR(10) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO rl_schema_version (version) VALUES ('1.0.0') ON CONFLICT DO NOTHING;
```

### 🔗 **3.3 更新 NetStack API RL 連接配置**

#### **編輯 netstack/compose/core.yaml - 更新 netstack-api 環境變數**
```yaml
netstack-api:
  # ... 現有配置
  environment:
    # ... 現有環境變數
    - RL_DATABASE_URL=postgresql://rl_user:rl_password@postgres-rl:5432/rl_research
  depends_on:
    # ... 現有依賴
    postgres-rl:
      condition: service_healthy
```

#### **更新 netstack/requirements.txt**
```txt
# ... 現有依賴

# RL PostgreSQL 支援
asyncpg>=0.29.0
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.23
alembic>=1.12.1
```

### ✅ **3.4 測試 NetStack PostgreSQL 連接**

```bash
# 1. 啟動 NetStack (包含新的 PostgreSQL)
make netstack-restart

# 2. 等待 PostgreSQL 啟動
sleep 30

# 3. 檢查 PostgreSQL 健康狀態
docker exec netstack-postgres-rl pg_isready -U rl_user -d rl_research

# 4. 驗證數據表創建
docker exec netstack-postgres-rl psql -U rl_user -d rl_research -c "\dt"

# 5. 檢查 NetStack API 連接
curl http://localhost:8080/api/v1/rl/status

# 6. 查看日誌確認無錯誤
docker logs netstack-postgres-rl
docker logs netstack-api
```

---

## 🛠️ **Phase 4: 更新 Makefile 和最終驗證 (1 小時)**

### 📝 **4.1 更新根目錄 Makefile**

#### **編輯 /home/sat/ntn-stack/Makefile - 移除不必要的 PostgreSQL 引用**
```makefile
# 更新狀態檢查 - 移除獨立的 RL System PostgreSQL 檢查
status: ## 檢查所有服務狀態
\t@echo "$(CYAN)📊 檢查 NTN Stack 服務狀態...$(RESET)"
\t@echo ""
\t@echo "$(YELLOW)NetStack 服務狀態:$(RESET)"
\t@cd $(NETSTACK_DIR) && docker compose -f compose/core.yaml ps || echo "$(RED)❌ NetStack 核心網服務未運行$(RESET)"
\t@echo ""
\t@echo "$(YELLOW)SimWorld 服務狀態:$(RESET)"
\t@cd $(SIMWORLD_DIR) && docker compose ps || echo "$(RED)❌ SimWorld 服務未運行$(RESET)"
\t@echo ""
\t@echo "$(YELLOW)服務健康檢查:$(RESET)"
\t@curl -s $(NETSTACK_URL)/health > /dev/null && echo "$(GREEN)✅ NetStack 健康檢查通過$(RESET)" || echo "$(RED)❌ NetStack 健康檢查失敗$(RESET)"
\t@curl -s http://localhost:8080/api/v1/rl/status > /dev/null && echo "$(GREEN)✅ RL System 健康檢查通過$(RESET)" || echo "$(RED)❌ RL System 健康檢查失敗$(RESET)"
\t@curl -s $(SIMWORLD_URL)/ > /dev/null && echo "$(GREEN)✅ SimWorld 健康檢查通過$(RESET)" || echo "$(RED)❌ SimWorld 健康檢查失敗$(RESET)"

# 更新網路驗證 - 移除舊的 PostgreSQL 連接檢查
verify-network-connection: ## 🔗 驗證容器間網路連接
\t@echo "$(CYAN)🔗 驗證容器間網路連接...$(RESET)"
\t@echo "$(YELLOW)檢查網路配置:$(RESET)"
\t@docker network ls | grep -E "(netstack-core|sionna-net)" || echo "$(RED)❌ 網路不存在$(RESET)"
\t@echo "$(YELLOW)檢查數據庫連接:$(RESET)"
\t@docker exec netstack-api python -c "import asyncpg; print('PostgreSQL 模組可用')" && echo "$(GREEN)✅ RL PostgreSQL 連接模組正常$(RESET)" || echo "$(RED)❌ RL PostgreSQL 連接模組異常$(RESET)"
\t@docker exec simworld_backend python -c "import motor; print('MongoDB 模組可用')" && echo "$(GREEN)✅ SimWorld MongoDB 連接模組正常$(RESET)" || echo "$(RED)❌ SimWorld MongoDB 連接模組異常$(RESET)"
\t@echo "$(YELLOW)測試跨服務 API 連接:$(RESET)"
\t@timeout 10s bash -c 'until docker exec simworld_backend curl -s http://172.20.0.40:8080/health > /dev/null 2>&1; do sleep 1; done' && echo "$(GREEN)✅ SimWorld -> NetStack 連接正常$(RESET)" || echo "$(RED)❌ SimWorld -> NetStack 連接失敗$(RESET)"
```

### 🔧 **4.2 創建數據庫管理腳本**

#### **scripts/db-management.sh**
```bash
#\!/bin/bash
# NTN Stack 數據庫管理腳本

set -e

# 顏色定義
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
RESET='\033[0m'

# 函數：數據庫狀態檢查
check_databases() {
    echo -e "${BLUE}📊 檢查數據庫狀態...${RESET}"
    
    # NetStack MongoDB
    if docker exec netstack-mongo mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ NetStack MongoDB 正常${RESET}"
    else
        echo -e "${RED}❌ NetStack MongoDB 異常${RESET}"
    fi
    
    # NetStack PostgreSQL (RL)
    if docker exec netstack-postgres-rl pg_isready -U rl_user -d rl_research >/dev/null 2>&1; then
        echo -e "${GREEN}✅ NetStack PostgreSQL (RL) 正常${RESET}"
    else
        echo -e "${RED}❌ NetStack PostgreSQL (RL) 異常${RESET}"
    fi
}

# 函數：備份數據庫
backup_databases() {
    echo -e "${BLUE}💾 備份數據庫...${RESET}"
    
    BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 備份 MongoDB
    docker exec netstack-mongo mongodump --db simworld --out /tmp/backup
    docker cp netstack-mongo:/tmp/backup "$BACKUP_DIR/mongodb"
    
    # 備份 PostgreSQL
    docker exec netstack-postgres-rl pg_dump -U rl_user rl_research > "$BACKUP_DIR/postgresql_rl.sql"
    
    echo -e "${GREEN}✅ 備份完成: $BACKUP_DIR${RESET}"
}

# 函數：重置 RL 數據庫
reset_rl_database() {
    echo -e "${YELLOW}⚠️  重置 RL 數據庫...${RESET}"
    read -p "確定要重置 RL 數據庫嗎? (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        docker exec netstack-postgres-rl psql -U rl_user -d rl_research -c "
        TRUNCATE TABLE rl_training_episodes, rl_decision_analysis, rl_algorithm_performance CASCADE;
        DELETE FROM rl_experiment_sessions WHERE session_status \!= 'running';
        "
        echo -e "${GREEN}✅ RL 數據庫已重置${RESET}"
    fi
}

# 函數：查看數據庫統計
show_database_stats() {
    echo -e "${BLUE}📈 數據庫統計...${RESET}"
    
    # MongoDB 統計
    echo -e "${YELLOW}SimWorld MongoDB:${RESET}"
    docker exec netstack-mongo mongosh simworld --eval "
    print('場景配置數量:', db.scenes.countDocuments({}));
    print('渲染配置數量:', db.render_configs.countDocuments({}));
    "
    
    # PostgreSQL 統計
    echo -e "${YELLOW}RL PostgreSQL:${RESET}"
    docker exec netstack-postgres-rl psql -U rl_user -d rl_research -c "
    SELECT 
        '實驗會話' as table_name, COUNT(*) as count 
    FROM rl_experiment_sessions
    UNION ALL
    SELECT 
        '訓練 Episodes' as table_name, COUNT(*) as count 
    FROM rl_training_episodes
    UNION ALL
    SELECT 
        '決策分析' as table_name, COUNT(*) as count 
    FROM rl_decision_analysis;
    "
}

# 主菜單
main_menu() {
    echo -e "${BLUE}🗄️  NTN Stack 數據庫管理工具${RESET}"
    echo ""
    echo "1. 檢查數據庫狀態"
    echo "2. 備份所有數據庫"
    echo "3. 重置 RL 數據庫"
    echo "4. 查看數據庫統計"
    echo "5. 退出"
    echo ""
    read -p "請選擇操作 (1-5): " choice
    
    case $choice in
        1) check_databases ;;
        2) backup_databases ;;
        3) reset_rl_database ;;
        4) show_database_stats ;;
        5) echo "再見！" && exit 0 ;;
        *) echo "無效選擇" ;;
    esac
}

# 檢查參數
if [[ $# -eq 0 ]]; then
    main_menu
else
    case $1 in
        status) check_databases ;;
        backup) backup_databases ;;
        reset) reset_rl_database ;;
        stats) show_database_stats ;;
        *) echo "用法: $0 [status|backup|reset|stats]" ;;
    esac
fi
```

```bash
# 設置腳本執行權限
chmod +x scripts/db-management.sh
```

### ✅ **4.3 完整系統驗證**

#### **系統重啟驗證腳本: scripts/full-system-verification.sh**
```bash
#\!/bin/bash
# 完整系統驗證腳本

set -e

# 顏色定義
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
RESET='\033[0m'

echo -e "${CYAN}🚀 NTN Stack 完整系統驗證開始...${RESET}"

# 1. 完全停止所有服務
echo -e "${YELLOW}📍 Step 1: 停止所有服務${RESET}"
make all-stop
sleep 5

# 2. 清理容器和網路
echo -e "${YELLOW}📍 Step 2: 清理資源${RESET}"
docker system prune -f
docker network prune -f

# 3. 啟動 NetStack
echo -e "${YELLOW}📍 Step 3: 啟動 NetStack (包含數據庫)${RESET}"
make netstack-start
sleep 30

# 4. 驗證 NetStack 數據庫
echo -e "${YELLOW}📍 Step 4: 驗證 NetStack 數據庫${RESET}"
echo "檢查 MongoDB..."
docker exec netstack-mongo mongosh --eval "db.adminCommand('ping')" && echo -e "${GREEN}✅ MongoDB 正常${RESET}"

echo "檢查 PostgreSQL..."
docker exec netstack-postgres-rl pg_isready -U rl_user -d rl_research && echo -e "${GREEN}✅ PostgreSQL 正常${RESET}"

echo "檢查 RL 數據表..."
docker exec netstack-postgres-rl psql -U rl_user -d rl_research -c "\dt" | grep rl_experiment && echo -e "${GREEN}✅ RL 數據表存在${RESET}"

# 5. 啟動 SimWorld
echo -e "${YELLOW}📍 Step 5: 啟動 SimWorld${RESET}"
make simworld-start
sleep 20

# 6. 驗證 SimWorld MongoDB 連接
echo -e "${YELLOW}📍 Step 6: 驗證 SimWorld MongoDB 連接${RESET}"
docker exec simworld_backend python -c "
import motor.motor_asyncio
import asyncio

async def test_mongo():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://netstack-mongo:27017')
    db = client.simworld
    result = await db.admin.command('ping')
    print('✅ SimWorld MongoDB 連接正常')
    client.close()

asyncio.run(test_mongo())
" && echo -e "${GREEN}✅ SimWorld MongoDB 連接測試通過${RESET}"

# 7. API 健康檢查
echo -e "${YELLOW}📍 Step 7: API 健康檢查${RESET}"
curl -s http://localhost:8080/health | jq . && echo -e "${GREEN}✅ NetStack API 正常${RESET}"
curl -s http://localhost:8888/ && echo -e "${GREEN}✅ SimWorld API 正常${RESET}"

# 8. RL 系統測試
echo -e "${YELLOW}📍 Step 8: RL 系統連接測試${RESET}"
curl -s http://localhost:8080/api/v1/rl/status | jq . && echo -e "${GREEN}✅ RL 系統正常${RESET}"

# 9. 最終狀態檢查
echo -e "${YELLOW}📍 Step 9: 最終狀態檢查${RESET}"
make status

echo -e "${CYAN}🎉 完整系統驗證完成！${RESET}"
echo -e "${GREEN}✅ 數據庫架構重構成功${RESET}"
echo ""
echo -e "${BLUE}📊 系統服務地址:${RESET}"
echo "  NetStack API:  http://localhost:8080"
echo "  SimWorld:      http://localhost:8888"
echo "  MongoDB:       localhost:27017 (內部)"
echo "  PostgreSQL RL: localhost:5433"
```

```bash
# 設置執行權限
chmod +x scripts/full-system-verification.sh
```

---

## 🎯 **執行清單 (Check List)**

### ✅ **Phase 1 完成確認**
- [ ] SimWorld 數據成功遷移到 NetStack MongoDB
- [ ] SimWorld 配置更新為 MongoDB 連接
- [ ] SimWorld 服務可正常啟動並連接 MongoDB
- [ ] 數據遷移腳本執行無錯誤

### ✅ **Phase 2 完成確認**  
- [ ] SimWorld PostgreSQL 容器完全移除
- [ ] SimWorld PostgreSQL Volume 完全清理
- [ ] SimWorld PostgreSQL 映像檔完全移除
- [ ] SimWorld docker-compose.yml 完全重寫
- [ ] SimWorld 程式碼中無 PostgreSQL 相關代碼
- [ ] SimWorld Dockerfile 無 PostgreSQL 依賴

### ✅ **Phase 3 完成確認**
- [ ] NetStack PostgreSQL 容器成功創建
- [ ] RL 數據表結構完全創建
- [ ] NetStack API 可連接 RL PostgreSQL
- [ ] RL 系統健康檢查通過
- [ ] PostgreSQL 初始化腳本執行成功

### ✅ **Phase 4 完成確認**
- [ ] 根目錄 Makefile 更新完成
- [ ] 數據庫管理腳本創建完成
- [ ] 完整系統驗證腳本創建完成
- [ ] 所有 make 指令正常運作
- [ ] 系統重啟驗證通過

---

## 🚨 **故障排除指南**

### 🔧 **常見問題及解決方案**

#### **Problem 1: SimWorld 無法連接 MongoDB**
```bash
# 檢查網路連接
docker exec simworld_backend ping netstack-mongo

# 檢查 MongoDB 服務狀態  
docker logs netstack-mongo

# 手動測試連接
docker exec simworld_backend python -c "
import motor.motor_asyncio
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://netstack-mongo:27017')
print(client.admin.command('ping'))
"
```

#### **Problem 2: NetStack PostgreSQL 初始化失敗**
```bash
# 檢查初始化日誌
docker logs netstack-postgres-rl

# 手動執行 SQL 腳本
docker exec -i netstack-postgres-rl psql -U rl_user -d rl_research < netstack/rl_system/sql/research_schema.sql

# 重新創建容器
docker rm -f netstack-postgres-rl
docker volume rm compose_postgres_rl_data
make netstack-restart
```

#### **Problem 3: 網路連接問題**
```bash
# 檢查網路存在
docker network ls | grep netstack-core

# 手動連接網路
docker network connect compose_netstack-core simworld_backend

# 重新創建網路
docker network rm compose_netstack-core
make netstack-restart
make simworld-restart
```

#### **Problem 4: 服務啟動順序問題**
```bash
# 按順序重啟
make all-stop
sleep 10
make netstack-start
sleep 30
make simworld-start
sleep 20
make status
```

### 📞 **緊急恢復方案**

#### **完全重置系統**
```bash
# 1. 停止所有服務
make all-stop

# 2. 清理所有資源
make all-clean-i

# 3. 移除所有網路
docker network prune -f

# 4. 重新啟動
make all-start

# 5. 執行驗證
./scripts/full-system-verification.sh
```

#### **數據恢復**
```bash
# 從備份恢復 MongoDB
docker exec -i netstack-mongo mongorestore --db simworld /tmp/backup/simworld

# 從備份恢復 PostgreSQL
cat backup_postgresql_rl.sql | docker exec -i netstack-postgres-rl psql -U rl_user -d rl_research
```

---

## 📈 **成功標準驗證**

### 🎯 **最終驗證清單**

```bash
# 執行完整驗證
./scripts/full-system-verification.sh

# 手動驗證重點項目
echo "1. 檢查 SimWorld 無 PostgreSQL 資源"
docker ps -a | grep postgres | grep -v netstack

echo "2. 檢查 NetStack 數據庫服務"
curl -s http://localhost:8080/health | jq .database

echo "3. 檢查 RL 系統連接"
curl -s http://localhost:8080/api/v1/rl/status | jq .database

echo "4. 檢查 SimWorld MongoDB 連接"
curl -s http://localhost:8888/health | jq .database

echo "5. 檢查所有服務健康狀態"
make status

echo "6. 檢查數據庫統計"
./scripts/db-management.sh stats
```

### ✅ **成功指標**
- [ ] 0 個 SimWorld PostgreSQL 容器存在
- [ ] 1 個 NetStack MongoDB 服務正常
- [ ] 1 個 NetStack PostgreSQL (RL) 服務正常  
- [ ] SimWorld 可正常訪問 http://localhost:8888
- [ ] NetStack 可正常訪問 http://localhost:8080
- [ ] RL API 可正常訪問 http://localhost:8080/api/v1/rl/status
- [ ] 所有 make 指令無錯誤執行
- [ ] 系統重啟後所有服務自動恢復

---

**🎉 恭喜！NTN Stack 數據庫架構重構完成！**

**📊 重構成果:**
- ✅ SimWorld 遷移至 NetStack MongoDB (統一管理)
- ✅ NetStack 新建 RL PostgreSQL (研究級專用)  
- ✅ 完全清理 SimWorld PostgreSQL 資源
- ✅ 統一 Makefile 管理所有數據庫服務
- ✅ 為 @rl.md 後續開發奠定穩固基礎

**🚀 下一步：開始 @rl.md Phase 1 - PostgreSQL 真實數據儲存開發！**
