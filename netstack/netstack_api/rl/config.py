"""
RL 配置管理

提供靈活的配置管理，支持：
- 環境變量配置
- 檔案配置
- 動態配置更新
- 服務特定配置
"""

import os
import yaml
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)

class RLConfig:
    """RL 配置類"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = self._load_config(config)
        self._validate_config()
        
    def _load_config(self, custom_config: Optional[Dict] = None) -> Dict[str, Any]:
        """載入配置"""
        
        # 默認配置
        default_config = {
            "global": {
                "engine_type": "gymnasium",  # gymnasium, legacy, disabled
                "fallback_enabled": True,
                "health_check_interval": 60,
                "max_response_time": 10.0,
                "max_error_rate": 0.3
            },
            "services": {
                "interference": {
                    "enabled": True,
                    "engine_type": "gymnasium",
                    "algorithm": "DQN",
                    "env_name": "netstack/InterferenceMitigation-v0",
                    "config": {
                        "learning_rate": 3e-4,
                        "buffer_size": 100000,
                        "batch_size": 64,
                        "gamma": 0.99,
                        "exploration_fraction": 0.3,
                        "exploration_final_eps": 0.05,
                        "target_update_interval": 1000
                    }
                },
                "optimization": {
                    "enabled": True,
                    "engine_type": "gymnasium", 
                    "algorithm": "PPO",
                    "env_name": "netstack/NetworkOptimization-v0",
                    "config": {
                        "learning_rate": 3e-4,
                        "n_steps": 2048,
                        "batch_size": 64,
                        "n_epochs": 10,
                        "gamma": 0.99,
                        "gae_lambda": 0.95
                    }
                },
                "uav": {
                    "enabled": False,  # 默認禁用 UAV 服務
                    "engine_type": "gymnasium",
                    "algorithm": "SAC",
                    "env_name": "netstack/UAVFormation-v0",
                    "config": {
                        "learning_rate": 3e-4,
                        "buffer_size": 1000000,
                        "batch_size": 256,
                        "gamma": 0.99,
                        "tau": 0.005,
                        "learning_starts": 100
                    }
                },
                "decision": {
                    "enabled": True,
                    "engine_type": "legacy",  # 使用現有的決策引擎
                    "algorithm": "hybrid",
                    "config": {}
                }
            },
            "training": {
                "auto_train": False,
                "train_interval_hours": 24,
                "episodes_per_training": 1000,
                "save_models": True,
                "model_save_path": "./models/rl/",
                "tensorboard_log": "./logs/tensorboard/"
            },
            "monitoring": {
                "metrics_enabled": True,
                "detailed_logging": False,
                "performance_tracking": True,
                "alert_thresholds": {
                    "error_rate": 0.5,
                    "response_time": 5.0
                }
            }
        }
        
        # 從環境變量載入
        env_config = self._load_from_env()
        
        # 從配置檔案載入
        file_config = self._load_from_file()
        
        # 合併配置（優先級：custom > env > file > default）
        merged_config = default_config
        if file_config:
            merged_config = self._deep_merge(merged_config, file_config)
        if env_config:
            merged_config = self._deep_merge(merged_config, env_config)
        if custom_config:
            merged_config = self._deep_merge(merged_config, custom_config)
        
        logger.info("配置載入完成", 
                   sources=["default", "file" if file_config else None, 
                           "env" if env_config else None, 
                           "custom" if custom_config else None])
        
        return merged_config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """從環境變量載入配置"""
        env_config = {}
        
        # 全局配置
        if os.getenv("RL_ENGINE_TYPE"):
            env_config["global"] = {"engine_type": os.getenv("RL_ENGINE_TYPE")}
        
        # 服務特定配置
        services_config = {}
        
        # 干擾緩解服務
        if os.getenv("RL_INTERFERENCE_ENABLED"):
            services_config["interference"] = {
                "enabled": os.getenv("RL_INTERFERENCE_ENABLED").lower() == "true"
            }
        if os.getenv("RL_INTERFERENCE_ENGINE"):
            if "interference" not in services_config:
                services_config["interference"] = {}
            services_config["interference"]["engine_type"] = os.getenv("RL_INTERFERENCE_ENGINE")
        
        # 優化服務
        if os.getenv("RL_OPTIMIZATION_ENABLED"):
            services_config["optimization"] = {
                "enabled": os.getenv("RL_OPTIMIZATION_ENABLED").lower() == "true"
            }
        if os.getenv("RL_OPTIMIZATION_ENGINE"):
            if "optimization" not in services_config:
                services_config["optimization"] = {}
            services_config["optimization"]["engine_type"] = os.getenv("RL_OPTIMIZATION_ENGINE")
        
        # UAV 服務
        if os.getenv("RL_UAV_ENABLED"):
            services_config["uav"] = {
                "enabled": os.getenv("RL_UAV_ENABLED").lower() == "true"
            }
        
        if services_config:
            env_config["services"] = services_config
        
        return env_config
    
    def _load_from_file(self) -> Optional[Dict[str, Any]]:
        """從配置檔案載入"""
        config_paths = [
            os.getenv("RL_CONFIG_PATH"),
            "./config/rl_config.yaml",
            "./rl_config.yaml",
            "/etc/netstack/rl_config.yaml"
        ]
        
        for path in config_paths:
            if path and os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    logger.info("從檔案載入配置", path=path)
                    return config
                except Exception as e:
                    logger.warning("載入配置檔案失敗", path=path, error=str(e))
        
        return None
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合併字典"""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self):
        """驗證配置"""
        required_sections = ["global", "services"]
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"缺少必需的配置段落: {section}")
        
        # 驗證引擎類型
        valid_engines = ["gymnasium", "legacy", "disabled"]
        global_engine = self.config["global"].get("engine_type")
        if global_engine not in valid_engines:
            logger.warning("無效的全局引擎類型", engine_type=global_engine)
        
        # 驗證服務配置
        for service_name, service_config in self.config["services"].items():
            if "engine_type" in service_config:
                engine_type = service_config["engine_type"]
                if engine_type not in valid_engines:
                    logger.warning("無效的服務引擎類型", 
                                 service=service_name, 
                                 engine_type=engine_type)
    
    def get_engine_type(self, service_name: str) -> str:
        """獲取服務的引擎類型"""
        service_config = self.config["services"].get(service_name, {})
        
        # 檢查服務是否啟用
        if not service_config.get("enabled", True):
            return "disabled"
        
        # 返回服務特定的引擎類型，或全局類型
        return service_config.get("engine_type", self.config["global"]["engine_type"])
    
    def get_algorithm(self, service_name: str) -> str:
        """獲取服務的算法"""
        service_config = self.config["services"].get(service_name, {})
        return service_config.get("algorithm", "DQN")
    
    def get_env_name(self, service_name: str) -> str:
        """獲取服務的環境名稱"""
        service_config = self.config["services"].get(service_name, {})
        return service_config.get("env_name", f"netstack/{service_name}-v0")
    
    def get_engine_config(self, service_name: str) -> Dict[str, Any]:
        """獲取服務的引擎配置"""
        service_config = self.config["services"].get(service_name, {})
        return service_config.get("config", {})
    
    def is_service_enabled(self, service_name: str) -> bool:
        """檢查服務是否啟用"""
        service_config = self.config["services"].get(service_name, {})
        return service_config.get("enabled", True)
    
    def get_training_config(self) -> Dict[str, Any]:
        """獲取訓練配置"""
        return self.config.get("training", {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """獲取監控配置"""
        return self.config.get("monitoring", {})
    
    def update_service_config(self, service_name: str, new_config: Dict[str, Any]):
        """更新服務配置"""
        if "services" not in self.config:
            self.config["services"] = {}
        
        if service_name not in self.config["services"]:
            self.config["services"][service_name] = {}
        
        self.config["services"][service_name] = self._deep_merge(
            self.config["services"][service_name], 
            new_config
        )
        
        logger.info("服務配置已更新", service_name=service_name)
    
    def save_to_file(self, path: str) -> bool:
        """保存配置到檔案"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info("配置已保存", path=path)
            return True
            
        except Exception as e:
            logger.error("保存配置失敗", path=path, error=str(e))
            return False
    
    def get_full_config(self) -> Dict[str, Any]:
        """獲取完整配置"""
        return self.config.copy()
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"RLConfig(services={list(self.config.get('services', {}).keys())})"