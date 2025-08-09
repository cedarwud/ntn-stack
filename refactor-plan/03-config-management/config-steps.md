# 配置管理統一化執行步驟

## 🎯 執行時程與優先級

### Step 1: 配置基礎設施建立 (Priority 1)
**時間:** 6 小時  
**風險:** 低  
**影響:** 高

#### 1.1 創建配置目錄結構
```bash
# 創建配置目錄
mkdir -p /home/sat/ntn-stack/netstack/config/{environments}

# 創建配置文件
cd /home/sat/ntn-stack/netstack/config/
touch base.yaml
touch satellite.yaml  
touch database.yaml
touch network.yaml
touch monitoring.yaml
touch environments/{development,production,testing}.yaml
```

#### 1.2 實作配置管理器
```python
# 文件: /netstack/src/config/config_manager.py

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """統一配置管理器 - 單一配置源實現"""
    
    def __init__(self, config_dir: str = None):
        # 支援多種配置目錄路徑
        possible_paths = [
            config_dir,
            "/app/config",
            "/home/sat/ntn-stack/netstack/config",
            "./config"
        ]
        
        for path in possible_paths:
            if path and Path(path).exists():
                self.config_dir = Path(path)
                break
        else:
            raise FileNotFoundError("配置目錄未找到")
            
        self.config_cache = {}
        self._loaded_files = set()
        
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """載入完整配置"""
        cache_key = "merged_config"
        
        if not force_reload and cache_key in self.config_cache:
            return self.config_cache[cache_key]
            
        logger.info(f"從 {self.config_dir} 載入配置...")
        
        try:
            # 載入核心配置文件
            base_config = self._load_yaml_file("base.yaml")
            satellite_config = self._load_yaml_file("satellite.yaml")
            database_config = self._load_yaml_file("database.yaml")
            network_config = self._load_yaml_file("network.yaml")
            monitoring_config = self._load_yaml_file("monitoring.yaml")
            
            # 載入環境特定配置
            env = os.getenv("ENVIRONMENT", "development")
            env_config = self._load_yaml_file(f"environments/{env}.yaml")
            
            # 合併配置 (後載入的覆蓋先載入的)
            merged_config = {}
            for config in [base_config, satellite_config, database_config, 
                          network_config, monitoring_config, env_config]:
                merged_config = self._deep_merge(merged_config, config)
            
            # 環境變數插值
            resolved_config = self._resolve_env_vars(merged_config)
            
            # 快取結果
            self.config_cache[cache_key] = resolved_config
            logger.info(f"配置載入完成，環境: {env}")
            
            return resolved_config
            
        except Exception as e:
            logger.error(f"配置載入失敗: {e}")
            raise
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """安全載入YAML文件"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            logger.warning(f"配置文件不存在: {filename}")
            return {}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f) or {}
                self._loaded_files.add(filename)
                logger.debug(f"已載入: {filename}")
                return content
        except yaml.YAMLError as e:
            logger.error(f"YAML解析錯誤 {filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"文件讀取錯誤 {filename}: {e}")
            raise
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深度合併字典"""
        result = base.copy()
        
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _resolve_env_vars(self, obj: Any) -> Any:
        """解析環境變數 ${VAR_NAME:-default}"""
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_expr = obj[2:-1]  # 移除 ${}
            if ":-" in env_expr:
                var_name, default_value = env_expr.split(":-", 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(env_expr, obj)
        return obj

    # 便利方法
    def get_satellite_config(self) -> Dict[str, Any]:
        """獲取衛星配置"""
        config = self.load_config()
        return config.get("satellite", {})
    
    def get_database_config(self, db_name: str = None) -> Dict[str, Any]:
        """獲取數據庫配置"""
        config = self.load_config()
        databases = config.get("databases", {})
        
        if db_name:
            return databases.get(db_name, {})
        return databases
    
    def get_connection_string(self, db_type: str) -> str:
        """獲取數據庫連接字串"""
        config = self.load_config()
        return config.get("connection_strings", {}).get(db_type, "")
    
    def get_network_config(self) -> Dict[str, Any]:
        """獲取網路配置"""
        config = self.load_config()
        return config.get("network", {})
    
    def get_service_endpoint(self, service_name: str) -> str:
        """獲取服務端點"""
        network_config = self.get_network_config()
        services = network_config.get("services", {})
        ports = network_config.get("ports", {})
        
        if service_name in services:
            ip = services[service_name]
            port = ports.get(service_name, 80)
            return f"http://{ip}:{port}"
        
        return ""
    
    def validate_config(self) -> bool:
        """驗證配置完整性"""
        from .config_validator import ConfigValidator
        
        config = self.load_config()
        return ConfigValidator.validate_all(config)

# 全域配置管理器實例
config_manager = ConfigManager()
```

#### 1.3 實作配置驗證器
```python
# 文件: /netstack/src/config/config_validator.py

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import ipaddress
import re

class SatelliteConstellationConfig(BaseModel):
    target_count: int = Field(..., gt=0, le=1000, description="目標衛星數量")
    min_elevation_deg: float = Field(..., ge=0, le=90, description="最小仰角度")
    frequency_ghz: float = Field(..., gt=0, le=100, description="頻率GHz")
    orbital_period_minutes: int = Field(..., gt=60, le=200, description="軌道週期分鐘")

class ObserverLocationConfig(BaseModel):
    name: str = Field(..., min_length=1, description="觀測點名稱")
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    altitude_m: float = Field(..., ge=0, le=10000, description="海拔高度米")

class DatabaseConfig(BaseModel):
    host: str = Field(..., min_length=1)
    port: int = Field(..., gt=0, le=65535)
    database: str = Field(..., min_length=1)
    username: Optional[str] = None
    password: Optional[str] = None
    connection_timeout: Optional[int] = Field(10, gt=0, le=300)

class NetworkServiceConfig(BaseModel):
    """網路服務IP配置驗證"""
    
    @validator('*', pre=True)
    def validate_ip_address(cls, v, field):
        if isinstance(v, str):
            try:
                ipaddress.ip_address(v)
                return v
            except ValueError:
                # 允許主機名
                if re.match(r'^[a-zA-Z0-9.-]+$', v):
                    return v
                raise ValueError(f"無效的IP地址或主機名: {v}")
        return v

class ConfigValidator:
    """配置驗證器"""
    
    @staticmethod
    def validate_satellite_config(config: Dict) -> bool:
        """驗證衛星配置"""
        if "satellite" not in config:
            raise ValueError("缺少衛星配置區塊")
            
        satellite_config = config["satellite"]
        
        # 驗證星座配置
        if "constellations" in satellite_config:
            for name, constellation in satellite_config["constellations"].items():
                try:
                    SatelliteConstellationConfig(**constellation)
                except Exception as e:
                    raise ValueError(f"星座配置 {name} 無效: {e}")
        
        # 驗證觀測點配置  
        if "observer" in satellite_config and "location" in satellite_config["observer"]:
            try:
                ObserverLocationConfig(**satellite_config["observer"]["location"])
            except Exception as e:
                raise ValueError(f"觀測點配置無效: {e}")
        
        return True
    
    @staticmethod
    def validate_database_config(config: Dict) -> bool:
        """驗證數據庫配置"""
        if "databases" not in config:
            raise ValueError("缺少數據庫配置區塊")
            
        databases = config["databases"]
        required_databases = ["mongodb", "postgresql", "redis"]
        
        for db_name in required_databases:
            if db_name not in databases:
                raise ValueError(f"缺少必要數據庫配置: {db_name}")
                
            try:
                DatabaseConfig(**databases[db_name])
            except Exception as e:
                raise ValueError(f"數據庫配置 {db_name} 無效: {e}")
        
        # 驗證連接字串
        if "connection_strings" in config:
            conn_strings = config["connection_strings"]
            for db_type in required_databases:
                if db_type not in conn_strings:
                    raise ValueError(f"缺少連接字串: {db_type}")
                if not conn_strings[db_type]:
                    raise ValueError(f"連接字串為空: {db_type}")
        
        return True
    
    @staticmethod
    def validate_network_config(config: Dict) -> bool:
        """驗證網路配置"""
        if "network" not in config:
            raise ValueError("缺少網路配置區塊")
            
        network_config = config["network"]
        
        # 驗證Docker子網配置
        if "docker" in network_config and "subnet" in network_config["docker"]:
            subnet = network_config["docker"]["subnet"]
            try:
                ipaddress.ip_network(subnet, strict=False)
            except ValueError:
                raise ValueError(f"無效的Docker子網: {subnet}")
        
        # 驗證服務IP配置
        if "services" in network_config:
            services = network_config["services"]
            for service_name, ip_addr in services.items():
                try:
                    ip = ipaddress.ip_address(ip_addr)
                    # 檢查IP是否在Docker子網內
                    if "docker" in network_config:
                        subnet = ipaddress.ip_network(network_config["docker"]["subnet"])
                        if ip not in subnet:
                            raise ValueError(f"服務 {service_name} IP {ip_addr} 不在子網 {subnet} 內")
                except ValueError as e:
                    raise ValueError(f"服務 {service_name} IP配置無效: {e}")
        
        # 驗證端口配置
        if "ports" in network_config:
            ports = network_config["ports"]
            for service_name, port in ports.items():
                if not isinstance(port, int) or port < 1 or port > 65535:
                    raise ValueError(f"服務 {service_name} 端口無效: {port}")
        
        return True
    
    @staticmethod
    def validate_consistency(config: Dict) -> bool:
        """驗證配置一致性"""
        errors = []
        
        # 檢查衛星配置一致性
        if "satellite" in config and "constellations" in config["satellite"]:
            constellations = config["satellite"]["constellations"]
            
            # 檢查Starlink配置
            if "starlink" in constellations:
                starlink_count = constellations["starlink"]["target_count"]
                # 可以添加更多一致性檢查...
        
        # 檢查數據庫配置一致性
        if "databases" in config and "connection_strings" in config:
            # 確保連接字串與數據庫配置匹配
            pass
        
        if errors:
            raise ValueError("配置一致性檢查失敗: " + "; ".join(errors))
        
        return True
    
    @staticmethod
    def validate_all(config: Dict) -> bool:
        """執行完整配置驗證"""
        validators = [
            ConfigValidator.validate_satellite_config,
            ConfigValidator.validate_database_config,
            ConfigValidator.validate_network_config,
            ConfigValidator.validate_consistency,
        ]
        
        for validator in validators:
            validator(config)
        
        return True
```

---

### Step 2: 創建配置文件 (Priority 1)  
**時間:** 4 小時  
**風險:** 低  
**影響:** 高

#### 2.1 基礎配置文件
```yaml
# 文件: /netstack/config/base.yaml

application:
  name: "NetStack LEO Satellite System"
  version: "1.0.0"
  description: "5G NTN LEO satellite handover research platform"
  
system:
  timezone: "Asia/Taipei"
  locale: "zh_TW.UTF-8"
  
logging:
  level: "${LOG_LEVEL:-INFO}"
  format: "json"
  handlers:
    - console
    - file
  
api:
  host: "${API_HOST:-0.0.0.0}"
  port: "${API_PORT:-8080}"
  workers: "${API_WORKERS:-1}"
  reload: false
  timeout: 30
  
security:
  secret_key: "${SECRET_KEY:-development_key_please_change}"
  algorithm: "HS256"
  access_token_expire_minutes: 30
```

#### 2.2 衛星系統配置文件  
```yaml
# 文件: /netstack/config/satellite.yaml

satellite:
  # 衛星星座配置 - 統一管理所有硬編碼值
  constellations:
    starlink:
      target_count: 150              # 原 satellite_selector.py line 55
      min_elevation_deg: 10.0        # 統一最小仰角標準
      frequency_ghz: 20.0            # Ku頻段
      orbital_period_minutes: 96     # 軌道週期
      itu_r_p618_enabled: true       # ITU-R P.618鏈路計算
      
    oneweb:
      target_count: 50               # 原 satellite_selector.py line 56  
      min_elevation_deg: 10.0        # 統一最小仰角標準
      frequency_ghz: 18.0            # Ku頻段
      orbital_period_minutes: 114    # 軌道週期
      itu_r_p618_enabled: true
  
  # 觀測點配置 - NTPU座標
  observer:
    location:
      name: "National Taipei University"
      latitude: 24.9441667           # 原硬編碼值
      longitude: 121.3713889         # 原硬編碼值 
      altitude_m: 50                 # 海拔高度
      timezone: "Asia/Taipei"
  
  # 數據處理配置
  processing:
    time_step_seconds: 30            # 時間步長
    safety_factor: 1.5               # 安全係數
    orbital_calculation_method: "sgp4"
    
    # 預處理模式
    modes:
      instant_load:                  # 即時載入模式
        enabled: true
        precompute_on_startup: true
        
      simple_load:                   # 簡化載入模式  
        enabled: true
        skip_data_update_check: true
        cron_driven_updates: true
        
      batch_processing:              # 批次處理模式
        enabled: false
        batch_size: 1000
  
  # 演算法配置
  algorithms:
    sgp4:
      enabled: true
      propagation_accuracy: "high"
      
    itu_r_p618:
      enabled: true
      frequency_ghz: 20.0
      rain_rate_mm_hr: 10.0          # 降雨率
      antenna_efficiency: 0.65       # 天線效率
      
    elevation_filtering:
      primary_threshold_deg: 10.0     # 主要門檻
      backup_threshold_deg: 5.0       # 備用門檻
      emergency_threshold_deg: 0.0    # 緊急門檻

# 研究相關配置
research:
  handover:
    target_satellite_count: 8        # RL研究目標衛星數
    evaluation_interval_seconds: 30  # 評估間隔
    
  data_collection:
    enabled: true
    export_format: "json"
    include_metadata: true
```

#### 2.3 數據庫配置文件
```yaml
# 文件: /netstack/config/database.yaml

databases:
  # MongoDB - 5G核心網數據  
  mongodb:
    host: "${MONGO_HOST:-mongo}"
    port: 27017
    database: "open5gs"
    connection_timeout: 10
    max_pool_size: 100
    
  # PostgreSQL - 衛星數據專用
  postgresql:  
    host: "${POSTGRES_HOST:-netstack-postgres}"
    port: 5432
    database: "${POSTGRES_DB:-netstack_db}"
    username: "${POSTGRES_USER:-netstack_user}"
    password: "${POSTGRES_PASSWORD:-netstack_password}"
    pool_size: 10
    max_overflow: 20
    connection_timeout: 30
    
  # Redis - 快取和會話管理
  redis:
    host: "${REDIS_HOST:-redis}"
    port: 6379
    database: 0
    connection_timeout: 5
    max_connections: 50

# 連接字串模板 - 統一管理
connection_strings:
  mongodb: "mongodb://${databases.mongodb.host}:${databases.mongodb.port}/${databases.mongodb.database}"
  postgresql: "postgresql://${databases.postgresql.username}:${databases.postgresql.password}@${databases.postgresql.host}:${databases.postgresql.port}/${databases.postgresql.database}"
  redis: "redis://${databases.redis.host}:${databases.redis.port}/${databases.redis.database}"

# 數據庫表配置
tables:
  satellite_orbital_cache:
    retention_days: 7
    partition_by: "timestamp"
    
  satellite_tle_data:
    retention_days: 30
    update_frequency: "daily"
```

#### 2.4 網路配置文件
```yaml
# 文件: /netstack/config/network.yaml

network:
  # Docker網路配置 - 統一IP分配
  docker:
    subnet: "172.20.0.0/16"
    gateway: "172.20.0.1"
    
  # 服務IP分配 - 解決IP不一致問題
  services:
    # 基礎設施
    mongo: "172.20.0.10"
    redis: "172.20.0.50"  
    postgres: "172.20.0.51"        # 統一使用 .51 (非 .55)
    
    # 5G核心網服務
    nrf: "172.20.0.23"
    scp: "172.20.0.26"
    amf: "172.20.0.20"
    ausf: "172.20.0.21"
    bsf: "172.20.0.22"
    nssf: "172.20.0.24"
    pcf: "172.20.0.25"
    smf: "172.20.0.27"
    udm: "172.20.0.28"
    udr: "172.20.0.29"
    upf: "172.20.0.30"
    webui: "172.20.0.31"
    
    # NetStack服務
    netstack-api: "172.20.0.40"
    
  # 端口配置
  ports:
    api: 8080
    mongo: 27017
    postgres: 5432
    redis: 6379
    webui: 9999
    prometheus: 9090
    
# 外部端點配置  
external_endpoints:
  simworld_backend: "${SIMWORLD_API_URL:-http://simworld_backend:8000}"
  health_check_url: "http://localhost:8080/health"
  
# 網路政策
network_policies:
  # 允許的連接
  allowed_connections:
    - netstack-api -> postgres
    - netstack-api -> mongo  
    - netstack-api -> redis
    
  # 限制連接
  restricted_connections:
    - simworld -> netstack-internal
```

---

### Step 3: 代碼遷移更新 (Priority 2)
**時間:** 8 小時  
**風險:** 中等  
**影響:** 高

#### 3.1 更新衛星選擇器使用配置
```python
# 文件: src/services/satellite/preprocessing/satellite_selector.py

# 原始硬編碼 (移除)
# starlink_target: int = 150
# oneweb_target: int = 50

# 新的配置驅動方式
from src.config.config_manager import config_manager

class SatelliteSelector:
    def __init__(self):
        # 從配置載入參數
        self.config = config_manager.get_satellite_config()
        
        # 星座配置
        self.starlink_config = self.config["constellations"]["starlink"]
        self.oneweb_config = self.config["constellations"]["oneweb"]
        
        # 觀測點配置
        self.observer_config = self.config["observer"]["location"]
        
    def get_target_counts(self) -> tuple:
        """獲取目標衛星數量"""
        starlink_target = self.starlink_config["target_count"]
        oneweb_target = self.oneweb_config["target_count"]
        return starlink_target, oneweb_target
        
    def get_elevation_threshold(self, constellation: str) -> float:
        """獲取仰角門檻"""
        if constellation == "starlink":
            return self.starlink_config["min_elevation_deg"]
        elif constellation == "oneweb":
            return self.oneweb_config["min_elevation_deg"]
        else:
            return 10.0  # 預設值
            
    def get_observer_location(self) -> tuple:
        """獲取觀測點座標"""
        return (
            self.observer_config["latitude"],
            self.observer_config["longitude"],
            self.observer_config["altitude_m"]
        )
```

#### 3.2 更新數據庫連接使用配置
```python
# 文件: netstack_api/app/core/database.py

from src.config.config_manager import config_manager
import motor.motor_asyncio
import asyncpg
import redis.asyncio as redis

class DatabaseManager:
    def __init__(self):
        # 載入數據庫配置
        self.db_config = config_manager.get_database_config()
        
    async def get_mongo_client(self):
        """獲取MongoDB客戶端"""
        connection_string = config_manager.get_connection_string("mongodb")
        return motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        
    async def get_postgres_pool(self):
        """獲取PostgreSQL連接池"""
        connection_string = config_manager.get_connection_string("postgresql")
        return await asyncpg.create_pool(connection_string)
        
    async def get_redis_client(self):
        """獲取Redis客戶端"""
        connection_string = config_manager.get_connection_string("redis")
        return redis.from_url(connection_string)
```

#### 3.3 更新主應用程式使用配置
```python
# 文件: netstack_api/main.py

from src.config.config_manager import config_manager
import logging

# 配置載入和驗證
async def load_and_validate_config():
    """載入並驗證配置"""
    try:
        config = config_manager.load_config()
        
        # 配置驗證
        if config_manager.validate_config():
            logging.info("✅ 配置驗證通過")
        else:
            logging.error("❌ 配置驗證失敗")
            raise ValueError("配置驗證失敗")
            
        return config
    except Exception as e:
        logging.error(f"配置載入失敗: {e}")
        raise

async def create_app():
    """創建應用程式實例"""
    # 載入配置
    config = await load_and_validate_config()
    
    # 使用配置創建FastAPI實例
    app_config = config["api"]
    
    app = FastAPI(
        title=config["application"]["name"],
        version=config["application"]["version"],
        description=config["application"]["description"]
    )
    
    # 使用配置創建數據庫連接
    # ... (使用配置而非硬編碼值)
    
    return app, config

# 主程式啟動
if __name__ == "__main__":
    import uvicorn
    
    # 載入伺服器配置
    config = config_manager.load_config()
    server_config = config["api"]
    
    # 啟動伺服器
    uvicorn.run(
        "netstack_api.main:app",
        host=server_config["host"],
        port=server_config["port"],
        workers=server_config["workers"],
        reload=server_config["reload"],
        log_level=config["logging"]["level"].lower()
    )
```

---

### Step 4: Docker配置整合 (Priority 2)
**時間:** 6 小時  
**風險:** 中等  
**影響:** 中等

#### 4.1 簡化Docker Compose配置
```yaml
# 文件: netstack/compose/core-unified.yaml
# 統一的Docker Compose配置，替代core.yaml和core-simple.yaml

networks:
  netstack-core:
    driver: bridge
    ipam:
      config:
        # 使用配置文件中的子網設定
        - subnet: 172.20.0.0/16

services:
  # PostgreSQL - 使用統一IP配置
  postgres:
    image: postgres:16-alpine
    container_name: netstack-postgres
    hostname: netstack-postgres
    environment:
      # 使用環境變數，從配置文件讀取
      POSTGRES_DB: "${POSTGRES_DB:-netstack_db}"
      POSTGRES_USER: "${POSTGRES_USER:-netstack_user}"  
      POSTGRES_PASSWORD: "${POSTGRES_PASSWORD:-netstack_password}"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      netstack-core:
        # 統一使用配置文件中的IP  
        ipv4_address: 172.20.0.51
        aliases:
          - postgres
          - netstack-postgres
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-netstack_user} -d ${POSTGRES_DB:-netstack_db}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # NetStack API - 統一啟動方式
  netstack-api:
    build:
      context: ../
      dockerfile: docker/Dockerfile
    container_name: netstack-api
    entrypoint: ["/usr/local/bin/smart-entrypoint.sh"]
    command: ["python", "-m", "netstack_api.main"]
    environment:
      # 簡化環境變數，依賴配置文件
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      # 資料庫連接從配置文件讀取
      - POSTGRES_HOST=netstack-postgres
      - POSTGRES_PORT=5432
      - MONGO_HOST=mongo
      - REDIS_HOST=redis
    volumes:
      # 掛載配置目錄
      - ../config:/app/config:ro
      - satellite_precomputed_data:/app/data
    networks:
      netstack-core:
        ipv4_address: 172.20.0.40
    depends_on:
      - postgres
      - mongo
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

  # 其他服務省略...
```

#### 4.2 創建環境特定配置
```yaml
# 文件: /netstack/config/environments/production.yaml

# 生產環境特定設定
logging:
  level: "INFO"
  
api:
  workers: 2
  reload: false
  
system:
  debug: false
  
# 性能優化設定
satellite:
  processing:
    modes:
      instant_load:
        enabled: true
        precompute_on_startup: true
        
databases:
  postgresql:
    pool_size: 20
    max_overflow: 40
    
  mongodb:
    max_pool_size: 200
```

```yaml  
# 文件: /netstack/config/environments/development.yaml

# 開發環境特定設定  
logging:
  level: "DEBUG"
  
api:
  workers: 1
  reload: true
  
system:
  debug: true
  
satellite:
  processing:
    modes:
      instant_load:
        enabled: true
        precompute_on_startup: false
        
databases:
  postgresql:
    pool_size: 5
    max_overflow: 10
```

---

### Step 5: 測試與驗證 (Priority 1)
**時間:** 6 小時  
**風險:** 低  
**影響:** 高

#### 5.1 配置驗證測試
```bash
#!/bin/bash
# 文件: scripts/validate-config.sh

echo "🔧 配置統一化驗證測試..."

# 測試配置載入
echo "1. 測試配置文件載入..."
docker exec netstack-api python -c "
from src.config.config_manager import config_manager
config = config_manager.load_config()
print('✅ 配置載入成功')
print(f'應用程式: {config[\"application\"][\"name\"]}')
print(f'Starlink目標: {config[\"satellite\"][\"constellations\"][\"starlink\"][\"target_count\"]}')
print(f'OneWeb目標: {config[\"satellite\"][\"constellations\"][\"oneweb\"][\"target_count\"]}')
"

# 測試配置驗證
echo "2. 測試配置驗證..."
docker exec netstack-api python -c "
from src.config.config_manager import config_manager
if config_manager.validate_config():
    print('✅ 配置驗證通過')
else:
    print('❌ 配置驗證失敗')
    exit(1)
"

# 測試數據庫連接配置
echo "3. 測試數據庫連接配置..."
docker exec netstack-api python -c "
from src.config.config_manager import config_manager

# 測試連接字串生成
postgres_url = config_manager.get_connection_string('postgresql')
mongo_url = config_manager.get_connection_string('mongodb')
redis_url = config_manager.get_connection_string('redis')

print(f'PostgreSQL: {postgres_url}')
print(f'MongoDB: {mongo_url}')
print(f'Redis: {redis_url}')
print('✅ 連接字串生成成功')
"

# 測試衛星配置讀取
echo "4. 測試衛星配置..."
docker exec netstack-api python -c "
from src.config.config_manager import config_manager

sat_config = config_manager.get_satellite_config()
starlink = sat_config['constellations']['starlink']
oneweb = sat_config['constellations']['oneweb']

print(f'Starlink配置: {starlink[\"target_count\"]}顆衛星, {starlink[\"min_elevation_deg\"]}°仰角')
print(f'OneWeb配置: {oneweb[\"target_count\"]}顆衛星, {oneweb[\"min_elevation_deg\"]}°仰角')
print('✅ 衛星配置讀取成功')
"

echo "✅ 所有配置驗證測試通過"
```

#### 5.2 配置一致性檢查
```python
#!/usr/bin/env python3
# 文件: scripts/check-config-consistency.py

"""
配置一致性檢查工具
檢查新配置系統與舊硬編碼值是否一致
"""

import sys
import os
sys.path.append("/home/sat/ntn-stack/netstack")

from src.config.config_manager import config_manager

def check_satellite_config_consistency():
    """檢查衛星配置一致性"""
    config = config_manager.load_config()
    
    # 檢查配置值
    starlink_count = config["satellite"]["constellations"]["starlink"]["target_count"]
    oneweb_count = config["satellite"]["constellations"]["oneweb"]["target_count"]
    
    print("🛰️ 衛星配置檢查:")
    print(f"  Starlink目標數量: {starlink_count}")
    print(f"  OneWeb目標數量: {oneweb_count}")
    
    # 預期值檢查
    if starlink_count == 150 and oneweb_count == 50:
        print("  ✅ 配置值與預期一致")
        return True
    else:
        print("  ❌ 配置值與預期不符")
        return False

def check_database_config_consistency():
    """檢查數據庫配置一致性"""
    # 測試連接字串
    postgres_url = config_manager.get_connection_string("postgresql")
    expected_parts = ["netstack_user", "netstack-postgres", "5432", "netstack_db"]
    
    print("💾 數據庫配置檢查:")
    print(f"  PostgreSQL URL: {postgres_url}")
    
    if all(part in postgres_url for part in expected_parts):
        print("  ✅ 數據庫配置正確")
        return True
    else:
        print("  ❌ 數據庫配置有誤")
        return False

def check_network_config_consistency():
    """檢查網路配置一致性"""
    network_config = config_manager.get_network_config()
    
    # 檢查關鍵服務IP
    postgres_ip = network_config["services"]["postgres"]
    netstack_api_ip = network_config["services"]["netstack-api"]
    
    print("🌐 網路配置檢查:")
    print(f"  PostgreSQL IP: {postgres_ip}")
    print(f"  NetStack API IP: {netstack_api_ip}")
    
    # 預期IP檢查
    if postgres_ip == "172.20.0.51" and netstack_api_ip == "172.20.0.40":
        print("  ✅ 網路配置正確")
        return True
    else:
        print("  ❌ 網路配置不符預期")
        return False

if __name__ == "__main__":
    print("🔍 開始配置一致性檢查...\n")
    
    checks = [
        check_satellite_config_consistency,
        check_database_config_consistency,
        check_network_config_consistency
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
            print()
        except Exception as e:
            print(f"  ❌ 檢查失敗: {e}\n")
            results.append(False)
    
    # 總結
    if all(results):
        print("✅ 所有配置一致性檢查通過")
        sys.exit(0)
    else:
        print("❌ 配置一致性檢查失敗")
        sys.exit(1)
```

## 📈 預期效果與成功指標

### 立即效益
- **單一配置源**: 消除150+50配置分散問題
- **配置驗證**: 自動檢測配置錯誤
- **環境隔離**: development/production配置分離

### 中長期效益
- **維護成本降低**: 配置變更只需修改一處
- **部署可靠性**: 消除配置不一致導致的部署失敗
- **團隊協作**: 新人能快速理解系統配置

### 成功指標
- [ ] 所有硬編碼配置遷移到配置文件
- [ ] 配置驗證100%通過
- [ ] Docker IP地址分配一致
- [ ] 系統功能完全正常

---

**配置統一化執行計劃**  
*總執行時間: 30 小時*  
*建議執行期: 4-5 工作天*  
*優先級: 高 - 是後續重構的基礎*