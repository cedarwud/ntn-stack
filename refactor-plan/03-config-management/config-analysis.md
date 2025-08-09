# 配置管理統一化分析報告

## 🎯 配置管理現狀問題

### 嚴重問題: 配置分散化
**影響級別:** 🔴 嚴重 - 導致系統不一致和維護困難

#### 問題具體表現
1. **衛星配置多處定義**
   - `satellite_selector.py` line 55-56: `starlink_target=150, oneweb_target=50`
   - `build_with_phase0_data.py` line 232-233: `max_display_starlink=150, max_display_oneweb=50`
   - `constellation_separated_selection.json`: 實際運行數據
   - 各文件配置可能不同步

2. **Docker配置複雜化**
   - `core.yaml` vs `core-simple.yaml` 重複定義
   - IP地址分配不一致 (172.20.0.51 vs 172.20.0.55)
   - 環境變數分散在多個compose文件

3. **硬編碼配置普遍**
   - 數據庫連接字串硬編碼
   - 服務端點URL硬編碼
   - 演算法參數硬編碼

## 📊 配置分散性詳細分析

### 1. 衛星系統配置源

**配置來源映射:**
```yaml
satellite_selector.py:
  starlink_target: 150
  oneweb_target: 50
  min_elevation_deg: 10.0
  
build_with_phase0_data.py:
  max_display_starlink: 150  # 應與上方一致
  max_display_oneweb: 50     # 應與上方一致
  
constellation_separated_selection.json:
  # 實際運行時數據，可能與配置不符
  
compose/core.yaml:
  SATELLITE_DATA_MODE: instant_load
  POSTGRES_WAIT_TIMEOUT: 30
  PRECOMPUTE_ON_STARTUP: true
  
compose/core-simple.yaml:
  SATELLITE_DATA_MODE: simple_load  # 不同設定
  SKIP_DATA_UPDATE_CHECK: true
  CRON_DRIVEN_UPDATES: true
```

**風險分析:**
- 修改配置需要更新多個文件
- 容易出現不同環境間配置不一致
- 調試困難，無法確定實際使用的配置值

### 2. 數據庫配置分散

**當前分散狀況:**
```yaml
# Docker Compose 中
core.yaml:
  POSTGRES_DB: netstack_db
  POSTGRES_USER: netstack_user  
  POSTGRES_PASSWORD: netstack_password
  ipv4_address: 172.20.0.55

core-simple.yaml:
  POSTGRES_DB: netstack_db
  POSTGRES_USER: netstack_user
  POSTGRES_PASSWORD: netstack_password  
  ipv4_address: 172.20.0.51  # 不同IP!

# Python代碼中
CONNECTION_STRING = "postgresql://netstack_user:netstack_password@netstack-postgres:5432/netstack_db"
```

**問題:**
- IP地址不一致導致連接失敗
- 認證資訊重複定義
- 無統一的連接配置管理

### 3. 服務端點配置混亂

**端點定義分散:**
```yaml
# API服務
NetStack API: http://localhost:8080
SimWorld Backend: http://localhost:8888
SimWorld Frontend: http://localhost:5173

# Docker內部網路
netstack-api: 172.20.0.40
simworld_backend: 172.21.0.4  # 不同子網！
```

**問題:**
- 不同compose文件使用不同IP範圍
- 服務發現困難
- 跨服務通信配置複雜

## 🛠️ 統一配置管理解決方案

### 方案概述
創建分層配置管理系統，實現單一配置源 (Single Source of Truth)

```
📁 /netstack/config/
├── 🔧 base.yaml              # 基礎配置
├── 🐳 docker.yaml            # Docker特定配置  
├── 🛰️ satellite.yaml         # 衛星系統配置
├── 💾 database.yaml          # 數據庫配置
├── 🌐 network.yaml           # 網路配置
├── 📊 monitoring.yaml        # 監控配置
└── 📝 environments/          # 環境特定配置
    ├── development.yaml
    ├── production.yaml
    └── testing.yaml
```

### 1. 核心配置結構設計

#### base.yaml - 基礎配置
```yaml
# /netstack/config/base.yaml
application:
  name: "NetStack LEO Satellite System"
  version: "1.0.0"
  description: "5G NTN LEO satellite network stack"

system:
  timezone: "Asia/Taipei"
  locale: "zh_TW.UTF-8"
  log_level: "INFO"
  
api:
  host: "0.0.0.0"
  port: 8080
  workers: 1
  reload: false
  
security:
  secret_key: "${SECRET_KEY:-default_dev_key}"
  algorithm: "HS256"
  access_token_expire_minutes: 30
```

#### satellite.yaml - 衛星系統統一配置
```yaml
# /netstack/config/satellite.yaml
satellite:
  constellations:
    starlink:
      target_count: 150
      min_elevation_deg: 10.0
      frequency_ghz: 20.0
      orbital_period_minutes: 96
      
    oneweb:
      target_count: 50
      min_elevation_deg: 10.0
      frequency_ghz: 18.0
      orbital_period_minutes: 114
  
  observer:
    location:
      name: "NTPU Taiwan"
      latitude: 24.9441667
      longitude: 121.3713889
      altitude_m: 50
  
  processing:
    time_step_seconds: 30
    safety_factor: 1.5
    preprocessing_modes:
      - "instant_load"
      - "simple_load"
      - "cron_driven"
  
  algorithms:
    itu_r_p618:
      enabled: true
      frequency_ghz: 20.0
      elevation_threshold_deg: 5.0
    
    sgp4:
      enabled: true
      propagation_method: "sgp4"
```

#### database.yaml - 數據庫統一配置
```yaml
# /netstack/config/database.yaml
databases:
  mongodb:
    host: "mongo"
    port: 27017
    database: "open5gs"
    connection_timeout: 10
    
  postgresql:
    host: "netstack-postgres"
    port: 5432
    database: "netstack_db"
    username: "netstack_user"
    password: "${POSTGRES_PASSWORD:-netstack_password}"
    pool_size: 10
    max_overflow: 20
    
  redis:
    host: "redis"
    port: 6379
    database: 0
    connection_timeout: 5
    
connection_strings:
  mongodb: "mongodb://${databases.mongodb.host}:${databases.mongodb.port}/${databases.mongodb.database}"
  postgresql: "postgresql://${databases.postgresql.username}:${databases.postgresql.password}@${databases.postgresql.host}:${databases.postgresql.port}/${databases.postgresql.database}"
  redis: "redis://${databases.redis.host}:${databases.redis.port}/${databases.redis.database}"
```

#### network.yaml - 網路統一配置
```yaml
# /netstack/config/network.yaml
network:
  docker:
    subnet: "172.20.0.0/16"
    gateway: "172.20.0.1"
    
  services:
    # 核心服務IP分配
    mongo: "172.20.0.10"
    nrf: "172.20.0.23"
    scp: "172.20.0.26"
    amf: "172.20.0.20"
    redis: "172.20.0.50"
    postgres: "172.20.0.51"  # 統一使用.51
    netstack-api: "172.20.0.40"
    
  ports:
    api: 8080
    mongo: 27017
    postgres: 5432
    redis: 6379
    prometheus: 9090
    
external_endpoints:
  simworld_backend: "http://simworld_backend:8000"
  webui: "http://localhost:9999"
```

### 2. 配置管理代碼架構

#### 配置載入器
```python
# /netstack/src/config/config_manager.py

import yaml
import os
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    """統一配置管理器"""
    
    def __init__(self, config_dir: str = "/app/config"):
        self.config_dir = Path(config_dir)
        self.config_cache = {}
        
    def load_config(self, config_name: str = None) -> Dict[str, Any]:
        """載入配置文件"""
        if config_name in self.config_cache:
            return self.config_cache[config_name]
            
        # 載入基礎配置
        base_config = self._load_yaml_file("base.yaml")
        
        # 載入專門配置
        satellite_config = self._load_yaml_file("satellite.yaml")
        database_config = self._load_yaml_file("database.yaml")
        network_config = self._load_yaml_file("network.yaml")
        
        # 載入環境特定配置
        env = os.getenv("ENVIRONMENT", "development")
        env_config = self._load_yaml_file(f"environments/{env}.yaml")
        
        # 合併配置
        merged_config = {
            **base_config,
            **satellite_config,
            **database_config,
            **network_config,
            **env_config
        }
        
        # 環境變數替換
        resolved_config = self._resolve_env_vars(merged_config)
        
        # 快取結果
        self.config_cache[config_name or "default"] = resolved_config
        return resolved_config
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """載入YAML配置文件"""
        file_path = self.config_dir / filename
        if not file_path.exists():
            return {}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """解析環境變數"""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            # 解析 ${VAR_NAME:-default_value} 格式
            env_expr = config[2:-1]  # 移除 ${ }
            if ":-" in env_expr:
                var_name, default_value = env_expr.split(":-", 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(env_expr, config)
        return config

    def get_database_url(self, db_type: str) -> str:
        """獲取數據庫連接字串"""
        config = self.load_config()
        return config["connection_strings"][db_type]
    
    def get_satellite_config(self) -> Dict[str, Any]:
        """獲取衛星系統配置"""
        config = self.load_config()
        return config["satellite"]
    
    def get_network_config(self) -> Dict[str, Any]:
        """獲取網路配置"""
        config = self.load_config()
        return config["network"]

# 全域配置實例
config_manager = ConfigManager()
```

#### 配置驗證器
```python
# /netstack/src/config/config_validator.py

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional

class SatelliteConstellationConfig(BaseModel):
    target_count: int = Field(..., gt=0, description="目標衛星數量")
    min_elevation_deg: float = Field(..., ge=0, le=90, description="最小仰角")
    frequency_ghz: float = Field(..., gt=0, description="頻率")
    orbital_period_minutes: int = Field(..., gt=0, description="軌道週期")

class ObserverLocationConfig(BaseModel):
    name: str = Field(..., description="觀測點名稱")
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    altitude_m: float = Field(..., ge=0, description="海拔高度")

class SatelliteConfig(BaseModel):
    constellations: Dict[str, SatelliteConstellationConfig]
    observer: Dict[str, ObserverLocationConfig]
    processing: Dict[str, Any]

class DatabaseConfig(BaseModel):
    host: str
    port: int = Field(..., gt=0, le=65535)
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    
class NetworkConfig(BaseModel):
    subnet: str = Field(..., regex=r'^\d+\.\d+\.\d+\.\d+/\d+$')
    services: Dict[str, str]
    ports: Dict[str, int]

class ConfigValidator:
    """配置驗證器"""
    
    @staticmethod
    def validate_satellite_config(config: Dict) -> bool:
        """驗證衛星配置"""
        try:
            SatelliteConfig(**config["satellite"])
            return True
        except Exception as e:
            raise ValueError(f"衛星配置驗證失敗: {e}")
    
    @staticmethod  
    def validate_database_config(config: Dict) -> bool:
        """驗證數據庫配置"""
        try:
            databases = config["databases"]
            for db_name, db_config in databases.items():
                DatabaseConfig(**db_config)
            return True
        except Exception as e:
            raise ValueError(f"數據庫配置驗證失敗: {e}")
    
    @staticmethod
    def validate_network_config(config: Dict) -> bool:
        """驗證網路配置"""
        try:
            NetworkConfig(**config["network"])
            return True
        except Exception as e:
            raise ValueError(f"網路配置驗證失敗: {e}")
    
    @staticmethod
    def validate_all(config: Dict) -> bool:
        """驗證所有配置"""
        validators = [
            ConfigValidator.validate_satellite_config,
            ConfigValidator.validate_database_config,
            ConfigValidator.validate_network_config,
        ]
        
        for validator in validators:
            validator(config)
        
        return True
```

## 📋 配置遷移執行計劃

### Phase 1: 建立配置基礎設施
1. 創建 `/netstack/config/` 目錄結構
2. 實作 `ConfigManager` 和 `ConfigValidator`
3. 創建基礎配置文件

### Phase 2: 遷移現有配置
1. 將 `satellite_selector.py` 硬編碼配置遷移到 `satellite.yaml`
2. 將數據庫連接配置統一到 `database.yaml`
3. 將網路配置統一到 `network.yaml`

### Phase 3: 更新使用者代碼
1. 修改所有使用硬編碼配置的模塊
2. 替換為 `config_manager.get_*()` 調用
3. 添加配置驗證到啟動流程

### Phase 4: Docker配置整合
1. 簡化 compose 文件，移除重複配置
2. 使用環境變數從配置文件讀取
3. 統一IP地址分配方案

## 🎯 預期效果

### 立即效益
- ✅ 單一配置源，消除配置不一致
- ✅ 環境間配置差異明確可控
- ✅ 配置變更影響範圍明確

### 長期效益  
- ✅ 新功能配置集中管理
- ✅ 配置驗證自動化
- ✅ 運營維護成本降低

---

*配置管理統一化計劃*  
*版本: v1.0*  
*制定時間: 2025-08-09*