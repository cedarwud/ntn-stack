# ⚙️ 配置管理指南

**版本**: 1.0.0  
**建立日期**: 2025-08-04  
**適用於**: LEO 衛星切換研究系統  

## 📋 概述

本文檔說明系統的統一配置管理機制、關鍵配置參數和自定義方法，確保系統配置的一致性和可維護性。

## 🔧 統一配置系統

### 核心配置類
**位置**: `/netstack/src/core/config/satellite_config.py`

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass  
class SatelliteConfig:
    """衛星系統統一配置類"""
    
    # SIB19 合規配置
    MAX_CANDIDATE_SATELLITES: int = 8
    
    # 預處理優化配置
    PREPROCESS_SATELLITES: Dict[str, int] = None
    
    # 智能篩選配置
    INTELLIGENT_SELECTION: Dict[str, Any] = None
    
    # 觀測位置配置
    OBSERVER_LOCATION: Dict[str, float] = None
    
    # 仰角門檻配置  
    ELEVATION_THRESHOLDS: Dict[str, float] = None
    
    def __post_init__(self):
        """初始化預設值"""
        self.PREPROCESS_SATELLITES = self.PREPROCESS_SATELLITES or {
            "starlink": 40,
            "oneweb": 30
        }
        
        self.INTELLIGENT_SELECTION = self.INTELLIGENT_SELECTION or {
            "enabled": True,
            "geographic_filter": True,
            "handover_suitability": True,
            "target_location": {"lat": 24.9441667, "lon": 121.3713889}
        }
        
        self.OBSERVER_LOCATION = self.OBSERVER_LOCATION or {
            "latitude": 24.9441667,   # 台北科技大學
            "longitude": 121.3713889,
            "altitude": 50.0          # 米
        }
        
        self.ELEVATION_THRESHOLDS = self.ELEVATION_THRESHOLDS or {
            "minimum": 5.0,    # 最小可見仰角
            "handover": 10.0,  # 切換觸發仰角  
            "optimal": 15.0    # 最佳服務仰角
        }
```

### 配置載入機制
```python
# 全域配置實例
_global_config: Optional[SatelliteConfig] = None

def get_satellite_config() -> SatelliteConfig:
    """獲取全域配置實例"""
    global _global_config
    if _global_config is None:
        _global_config = SatelliteConfig()
    return _global_config

def reload_config(config_data: Dict[str, Any] = None) -> SatelliteConfig:
    """重新載入配置"""
    global _global_config
    if config_data:
        _global_config = SatelliteConfig(**config_data)
    else:
        _global_config = SatelliteConfig()
    return _global_config
```

## 📊 關鍵配置參數

### 1. 衛星候選配置
```python
satellite_selection = {
    # 3GPP NTN 標準合規
    "MAX_CANDIDATE_SATELLITES": 8,    # SIB19 最大候選數
    
    # 預處理階段優化  
    "PREPROCESS_SATELLITES": {
        "starlink": 40,               # Starlink 智能篩選數量
        "oneweb": 30                  # OneWeb 智能篩選數量
    },
    
    # 運行時動態調整
    "RUNTIME_CANDIDATES": 8           # API 返回候選數量
}
```

### 2. 智能篩選配置
```python
intelligent_selection = {
    "enabled": True,                  # 啟用智能篩選
    "geographic_filter": True,        # 地理相關性篩選
    "handover_suitability": True,     # 切換適用性評分
    
    # 地理篩選參數
    "target_location": {
        "lat": 24.9441667,            # 目標緯度 (台北科技大學)
        "lon": 121.3713889            # 目標經度
    },
    
    # 評分權重配置
    "scoring_weights": {
        "inclination_score": 0.25,    # 軌道傾角權重
        "altitude_score": 0.20,       # 高度適用性權重
        "orbital_shape": 0.15,        # 軌道形狀權重  
        "pass_frequency": 0.20,       # 經過頻率權重
        "constellation_bonus": 0.20   # 星座類型權重
    }
}
```

### 3. 軌道計算配置
```python
orbit_calculation = {
    # SGP4 計算模式
    "sgp4_mode": "production",        # production | simplified | debug
    
    # 精度配置
    "position_accuracy_m": 100,       # 目標位置精度 (米)
    "time_resolution_s": 10,          # 時間解析度 (秒)
    
    # 預測範圍
    "prediction_horizon_h": 24,       # 預測時間範圍 (小時)
    "update_interval_h": 1,           # 軌道更新間隔 (小時)
    
    # 攝動模型
    "atmospheric_drag": True,         # 大氣阻力
    "j2_perturbation": True,          # J2 重力場攝動
    "solar_radiation": False          # 太陽輻射壓 (LEO 影響小)
}
```

### 4. 仰角門檻配置
```python  
elevation_thresholds = {
    # 基礎門檻 (度)
    "minimum": 5.0,                   # 最小可見仰角
    "handover": 10.0,                 # 切換觸發仰角
    "optimal": 15.0,                  # 最佳服務仰角
    
    # 環境調整係數
    "environment_factors": {
        "urban": 1.1,                 # 城市環境
        "suburban": 1.0,              # 郊區環境
        "rural": 0.9,                 # 鄉村環境
        "mountain": 1.3,              # 山區環境
        "coastal": 1.0                # 海岸環境
    },
    
    # 天氣調整係數
    "weather_factors": {
        "clear": 1.0,                 # 晴天
        "light_rain": 1.1,            # 小雨
        "heavy_rain": 1.4,            # 大雨
        "snow": 1.2,                  # 下雪
        "fog": 1.15                   # 霧
    }
}
```

### 5. 算法參數配置
```python
algorithm_parameters = {
    # 切換決策配置
    "handover_decision": {
        "decision_timeout_ms": 100,    # 決策超時時間
        "hysteresis_margin_db": 3.0,   # 滯後邊界
        "min_service_time_s": 30,      # 最小服務時間
        "max_handover_rate": 6         # 每分鐘最大切換次數
    },
    
    # ML 預測配置  
    "ml_prediction": {
        "lstm_sequence_length": 60,    # LSTM 序列長度
        "prediction_horizon_s": 600,   # 預測時間範圍 (秒)
        "confidence_threshold": 0.8,   # 置信度門檻
        "model_update_interval_h": 24  # 模型更新間隔 (小時)
    },
    
    # 狀態同步配置
    "state_sync": {
        "consistency_level": "eventual", # 一致性級別
        "sync_timeout_ms": 5000,       # 同步超時時間
        "max_retry_attempts": 3,       # 最大重試次數
        "heartbeat_interval_s": 30     # 心跳間隔
    }
}
```

## 🌍 環境特定配置

### 開發環境配置
```python
development_config = {
    "debug_mode": True,
    "log_level": "DEBUG", 
    "enable_profiling": True,
    "mock_external_apis": True,
    
    # 寬鬆的超時設定
    "api_timeout_s": 30,
    "database_timeout_s": 10,
    
    # 測試數據配置
    "use_test_data": True,
    "data_refresh_interval_s": 300
}
```

### 生產環境配置
```python
production_config = {
    "debug_mode": False,
    "log_level": "INFO",
    "enable_profiling": False,
    "mock_external_apis": False,
    
    # 嚴格的超時設定
    "api_timeout_s": 10,
    "database_timeout_s": 5,
    
    # 生產數據配置
    "use_test_data": False,
    "data_refresh_interval_s": 3600
}
```

### Docker 容器配置
```yaml
# docker-compose.yml 環境變數
environment:
  - SATELLITE_CONFIG_MODE=production
  - MAX_CANDIDATE_SATELLITES=8
  - OBSERVER_LAT=24.9441667
  - OBSERVER_LON=121.3713889
  - ELEVATION_THRESHOLD=10.0
  - SGP4_MODE=production
  - LOG_LEVEL=INFO
```

## 🔄 配置載入優先級

### 配置來源優先級 (高到低)
1. **環境變數**: `SATELLITE_*` 環境變數
2. **命令列參數**: `--config` 參數指定的檔案
3. **配置檔案**: `config/satellite_config.json`
4. **預設值**: 程式碼中的預設配置

### 配置載入流程
```python
def load_configuration() -> SatelliteConfig:
    """載入配置的完整流程"""
    config_data = {}
    
    # 1. 載入預設配置
    config_data.update(DEFAULT_CONFIG)
    
    # 2. 載入檔案配置
    config_file = os.getenv('SATELLITE_CONFIG_FILE', 'config/satellite_config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            file_config = json.load(f)
            config_data.update(file_config)
    
    # 3. 載入環境變數
    env_config = {}
    for key, value in os.environ.items():
        if key.startswith('SATELLITE_'):
            config_key = key[10:]  # 移除 'SATELLITE_' 前綴
            env_config[config_key] = parse_env_value(value)
    config_data.update(env_config)
    
    # 4. 建立配置實例
    return SatelliteConfig(**config_data)
```

## 📁 配置檔案範例

### 基礎配置檔案
**位置**: `/config/satellite_config.json`
```json
{
  "MAX_CANDIDATE_SATELLITES": 8,
  "PREPROCESS_SATELLITES": {
    "starlink": 40,
    "oneweb": 30
  },
  "OBSERVER_LOCATION": {
    "latitude": 24.9441667,
    "longitude": 121.3713889,
    "altitude": 50.0
  },
  "ELEVATION_THRESHOLDS": {
    "minimum": 5.0,
    "handover": 10.0,
    "optimal": 15.0
  },
  "INTELLIGENT_SELECTION": {
    "enabled": true,
    "geographic_filter": true,
    "handover_suitability": true,
    "scoring_weights": {
      "inclination_score": 0.25,
      "altitude_score": 0.20,
      "orbital_shape": 0.15,
      "pass_frequency": 0.20,
      "constellation_bonus": 0.20
    }
  }
}
```

### 實驗特定配置
**位置**: `/config/experiment_config.json`
```json
{
  "experiment_name": "handover_algorithm_comparison",
  "algorithms": ["fine_grained", "traditional", "ml_driven"],
  "scenarios": {
    "urban": {
      "observer_location": {"lat": 25.0330, "lon": 121.5654}, 
      "environment_factor": 1.1,
      "satellite_density": "high"
    },
    "rural": {
      "observer_location": {"lat": 24.1469, "lon": 120.6839},
      "environment_factor": 0.9, 
      "satellite_density": "medium"
    }
  },
  "performance_metrics": [
    "handover_latency",
    "success_rate", 
    "prediction_accuracy"
  ]
}
```

## 🛠️ 配置驗證機制

### 配置完整性檢查
```python
class ConfigValidator:
    """配置驗證器"""
    
    @staticmethod
    def validate_satellite_config(config: SatelliteConfig) -> List[str]:
        """驗證衛星配置的完整性"""
        errors = []
        
        # 檢查候選衛星數量
        if config.MAX_CANDIDATE_SATELLITES < 1 or config.MAX_CANDIDATE_SATELLITES > 16:
            errors.append("MAX_CANDIDATE_SATELLITES 必須在 1-16 之間")
        
        # 檢查觀測位置
        lat = config.OBSERVER_LOCATION["latitude"]
        lon = config.OBSERVER_LOCATION["longitude"] 
        if not (-90 <= lat <= 90):
            errors.append("觀測緯度必須在 -90 到 90 度之間")
        if not (-180 <= lon <= 180):
            errors.append("觀測經度必須在 -180 到 180 度之間")
            
        # 檢查仰角門檻
        if config.ELEVATION_THRESHOLDS["minimum"] < 0:
            errors.append("最小仰角不能小於 0 度")
        if config.ELEVATION_THRESHOLDS["handover"] <= config.ELEVATION_THRESHOLDS["minimum"]:
            errors.append("切換仰角必須大於最小仰角")
            
        return errors
    
    @staticmethod
    def validate_and_load() -> SatelliteConfig:
        """驗證並載入配置"""
        config = load_configuration()
        errors = ConfigValidator.validate_satellite_config(config)
        
        if errors:
            raise ValueError(f"配置驗證失敗: {'; '.join(errors)}")
            
        return config
```

### 配置健康檢查
```python
def health_check_config() -> Dict[str, Any]:
    """配置健康檢查"""
    config = get_satellite_config()
    
    return {
        "config_loaded": True,
        "max_candidates": config.MAX_CANDIDATE_SATELLITES,
        "observer_location": config.OBSERVER_LOCATION,
        "intelligent_selection": config.INTELLIGENT_SELECTION["enabled"],
        "validation_status": "passed",
        "last_updated": datetime.now().isoformat()
    }
```

## 🔧 實際使用範例

### 在算法中使用配置
```python
from src.core.config.satellite_config import get_satellite_config

def handover_decision_algorithm(candidates):
    """切換決策算法使用配置"""
    config = get_satellite_config()
    
    # 使用配置的候選數量限制
    max_candidates = config.MAX_CANDIDATE_SATELLITES
    candidates = candidates[:max_candidates]
    
    # 使用配置的仰角門檻
    min_elevation = config.ELEVATION_THRESHOLDS["handover"]
    valid_candidates = [
        c for c in candidates 
        if c["elevation_deg"] >= min_elevation
    ]
    
    # 使用智能篩選配置
    if config.INTELLIGENT_SELECTION["enabled"]:
        return intelligent_selection_algorithm(valid_candidates, config)
    else:
        return traditional_selection_algorithm(valid_candidates)
```

### 在 API 中使用配置
```python  
from fastapi import APIRouter
from src.core.config.satellite_config import get_satellite_config

router = APIRouter()

@router.get("/satellites/candidates")
async def get_satellite_candidates():
    """獲取衛星候選清單"""
    config = get_satellite_config()
    
    # 使用配置限制返回數量
    max_count = config.MAX_CANDIDATE_SATELLITES
    
    # 使用配置的觀測位置
    observer_lat = config.OBSERVER_LOCATION["latitude"]
    observer_lon = config.OBSERVER_LOCATION["longitude"]
    
    candidates = calculate_visible_satellites(
        observer_lat, observer_lon, max_count
    )
    
    return {"candidates": candidates, "config_max": max_count}
```

### 配置動態更新
```python
@router.put("/config/update")
async def update_configuration(new_config: dict):
    """動態更新配置"""
    try:
        # 驗證新配置
        updated_config = SatelliteConfig(**new_config)
        errors = ConfigValidator.validate_satellite_config(updated_config)
        
        if errors:
            return {"success": False, "errors": errors}
        
        # 應用新配置
        reload_config(new_config)
        
        return {"success": True, "message": "配置更新成功"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## ⚠️ 配置管理注意事項

### 1. 配置一致性
- **所有組件** 必須使用 `get_satellite_config()` 獲取配置
- **禁止硬編碼** 配置參數在程式碼中
- **配置變更** 後必須重啟相關服務

### 2. 性能考量  
- 配置載入時進行一次性驗證
- 頻繁訪問的配置值可以快取
- 避免在性能關鍵路徑中重複載入配置

### 3. 安全性
- 敏感配置使用環境變數而非配置檔案
- 配置檔案權限控制 (600 或 640)
- 生產環境禁用配置動態更新 API

### 4. 向後兼容性
- 新增配置參數必須提供預設值
- 移除配置參數前先標記為廢棄 (deprecated)
- 配置結構變更需要提供遷移機制

---

**本文檔建立了完整的配置管理體系，確保系統配置的統一性、可維護性和可擴展性。**