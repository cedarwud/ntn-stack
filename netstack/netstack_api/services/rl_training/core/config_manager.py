"""
🧠 配置驅動的算法管理器

基於配置文件的算法管理，支援：
- YAML/JSON 配置驅動
- 動態算法加載
- 熱重載配置
- 環境隔離
"""

import os
import logging
import yaml
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import asyncio
import hashlib

from ..interfaces.rl_algorithm import IRLAlgorithm, ScenarioType
from .algorithm_factory import get_algorithm
from .di_container import DIContainer

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmConfig:
    """算法配置"""
    name: str
    algorithm_type: str
    enabled: bool = True
    scenarios: List[str] = None
    hyperparameters: Dict[str, Any] = None
    training_config: Dict[str, Any] = None
    deployment_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.scenarios is None:
            self.scenarios = ["urban"]
        if self.hyperparameters is None:
            self.hyperparameters = {}
        if self.training_config is None:
            self.training_config = {}
        if self.deployment_config is None:
            self.deployment_config = {}


@dataclass
class SystemConfig:
    """系統配置"""
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = ""
    redis_url: str = ""
    model_storage_path: str = "./models"
    enable_monitoring: bool = True
    enable_web_ui: bool = True
    api_rate_limit: int = 1000
    max_concurrent_training: int = 3


class ConfigDrivenAlgorithmManager:
    """配置驅動的算法管理器
    
    負責根據配置文件自動化管理算法的加載、配置和生命週期。
    支援多環境配置和熱重載功能。
    """
    
    def __init__(self, config_path: Union[str, Path], container: Optional[DIContainer] = None):
        self.config_path = Path(config_path)
        self.container = container or DIContainer()
        self.config: Dict[str, Any] = {}
        self.algorithms: Dict[str, IRLAlgorithm] = {}
        self.system_config: Optional[SystemConfig] = None
        self.algorithm_configs: Dict[str, AlgorithmConfig] = {}
        self._config_hash: Optional[str] = None
        self._file_watchers: List[asyncio.Task] = []
        self._initialized = False
        
        logger.info(f"配置驅動算法管理器初始化，配置文件: {config_path}")
    
    async def initialize(self) -> None:
        """初始化算法管理器"""
        if self._initialized:
            logger.warning("算法管理器已初始化")
            return
        
        try:
            # 加載配置
            await self._load_config()
            
            # 解析配置
            await self._parse_config()
            
            # 動態加載算法插件
            await self._load_algorithm_plugins()
            
            # 設置文件監控（如果啟用）
            if self.system_config and self.system_config.environment != "production":
                await self._setup_file_watcher()
            
            self._initialized = True
            logger.info("配置驅動算法管理器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化算法管理器失敗: {e}")
            raise
    
    async def _load_config(self) -> None:
        """加載配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            config_content = self.config_path.read_text(encoding='utf-8')
            
            # 計算配置文件哈希值
            current_hash = hashlib.md5(config_content.encode()).hexdigest()
            
            # 如果配置沒有變化，跳過重載
            if self._config_hash == current_hash:
                logger.debug("配置文件未變化，跳過重載")
                return
            
            # 根據文件擴展名解析配置
            if self.config_path.suffix.lower() in ['.yml', '.yaml']:
                self.config = yaml.safe_load(config_content)
            elif self.config_path.suffix.lower() == '.json':
                self.config = json.loads(config_content)
            else:
                raise ValueError(f"不支援的配置文件格式: {self.config_path.suffix}")
            
            self._config_hash = current_hash
            logger.info(f"成功加載配置文件: {self.config_path}")
            
        except Exception as e:
            logger.error(f"加載配置文件失敗: {e}")
            raise
    
    async def _parse_config(self) -> None:
        """解析配置內容"""
        try:
            # 解析系統配置
            system_config_data = self.config.get('system', {})
            self.system_config = SystemConfig(
                environment=system_config_data.get('environment', 'development'),
                log_level=system_config_data.get('log_level', 'INFO'),
                database_url=system_config_data.get('database_url', ''),
                redis_url=system_config_data.get('redis_url', ''),
                model_storage_path=system_config_data.get('model_storage_path', './models'),
                enable_monitoring=system_config_data.get('enable_monitoring', True),
                enable_web_ui=system_config_data.get('enable_web_ui', True),
                api_rate_limit=system_config_data.get('api_rate_limit', 1000),
                max_concurrent_training=system_config_data.get('max_concurrent_training', 3)
            )
            
            # 解析算法配置
            rl_algorithms = self.config.get('handover_algorithms', {}).get('reinforcement_learning', {})
            self.algorithm_configs.clear()
            
            for algo_name, algo_config in rl_algorithms.items():
                config_obj = AlgorithmConfig(
                    name=algo_name,
                    algorithm_type=algo_config.get('algorithm_type', algo_name.upper()),
                    enabled=algo_config.get('enabled', True),
                    scenarios=algo_config.get('scenarios', ['urban']),
                    hyperparameters=algo_config.get('hyperparameters', {}),
                    training_config=algo_config.get('training', {}),
                    deployment_config=algo_config.get('deployment', {})
                )
                self.algorithm_configs[algo_name] = config_obj
            
            logger.info(f"解析到 {len(self.algorithm_configs)} 個算法配置")
            
        except Exception as e:
            logger.error(f"解析配置失敗: {e}")
            raise
    
    async def _load_algorithm_plugins(self) -> None:
        """動態加載算法插件"""
        try:
            loaded_count = 0
            
            for algo_name, algo_config in self.algorithm_configs.items():
                if not algo_config.enabled:
                    logger.info(f"算法 {algo_name} 已禁用，跳過加載")
                    continue
                
                try:
                    # 嘗試創建算法實例
                    scenario_types = [ScenarioType(s) for s in algo_config.scenarios]
                    
                    # 為每個場景創建算法實例
                    for scenario_type in scenario_types:
                        algorithm = get_algorithm(
                            name=algo_config.algorithm_type.lower(),
                            env_name="CartPole-v1",  # 使用標準 Gymnasium 環境
                            config=algo_config.hyperparameters,
                            scenario_type=scenario_type,
                            use_singleton=True
                        )
                        
                        instance_key = f"{algo_name}_{scenario_type.value}"
                        self.algorithms[instance_key] = algorithm
                        
                        logger.info(f"成功加載算法: {algo_name} (類型: {algo_config.algorithm_type}, 場景: {scenario_type.value})")
                    
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"加載算法 {algo_name} 失敗: {e}")
            
            logger.info(f"成功加載 {loaded_count} 個算法")
            
        except Exception as e:
            logger.error(f"加載算法插件失敗: {e}")
            raise
    
    async def _setup_file_watcher(self) -> None:
        """設置配置文件監控"""
        async def watch_config_file():
            """監控配置文件變化"""
            last_modified = None
            
            while True:
                try:
                    current_modified = self.config_path.stat().st_mtime
                    
                    if last_modified is None:
                        last_modified = current_modified
                    elif current_modified != last_modified:
                        logger.info("檢測到配置文件變化，重新加載...")
                        await self._reload_config()
                        last_modified = current_modified
                    
                    await asyncio.sleep(5)  # 每5秒檢查一次
                    
                except Exception as e:
                    logger.error(f"監控配置文件失敗: {e}")
                    await asyncio.sleep(10)  # 出錯時等待更長時間
        
        # 啟動監控任務
        task = asyncio.create_task(watch_config_file())
        self._file_watchers.append(task)
        logger.info("已啟動配置文件監控")
    
    async def _reload_config(self) -> None:
        """重新加載配置"""
        try:
            # 重新加載配置文件
            await self._load_config()
            await self._parse_config()
            
            # 重新加載算法
            old_algorithms = self.algorithms.copy()
            self.algorithms.clear()
            await self._load_algorithm_plugins()
            
            # 清理舊的算法實例
            for old_algorithm in old_algorithms.values():
                try:
                    # 如果算法有清理方法，調用它
                    if hasattr(old_algorithm, 'cleanup'):
                        await old_algorithm.cleanup()
                except Exception as e:
                    logger.warning(f"清理舊算法實例失敗: {e}")
            
            logger.info("配置重新加載完成")
            
        except Exception as e:
            logger.error(f"重新加載配置失敗: {e}")
    
    async def get_algorithm(self, name: str, scenario_type: ScenarioType = ScenarioType.URBAN) -> IRLAlgorithm:
        """獲取算法實例
        
        Args:
            name: 算法名稱
            scenario_type: 場景類型
            
        Returns:
            IRLAlgorithm: 算法實例
            
        Raises:
            ValueError: 算法不存在或未啟用
        """
        if not self._initialized:
            await self.initialize()
        
        instance_key = f"{name}_{scenario_type.value}"
        
        if instance_key not in self.algorithms:
            raise ValueError(f"算法 {name} (場景: {scenario_type.value}) 不存在或未啟用")
        
        return self.algorithms[instance_key]
    
    def get_available_algorithms(self) -> List[str]:
        """獲取可用算法列表
        
        Returns:
            List[str]: 算法名稱列表
        """
        return [
            config.name 
            for config in self.algorithm_configs.values() 
            if config.enabled
        ]
    
    def get_algorithm_config(self, name: str) -> Optional[AlgorithmConfig]:
        """獲取算法配置
        
        Args:
            name: 算法名稱
            
        Returns:
            Optional[AlgorithmConfig]: 算法配置
        """
        return self.algorithm_configs.get(name)
    
    def get_system_config(self) -> SystemConfig:
        """獲取系統配置
        
        Returns:
            SystemConfig: 系統配置
        """
        return self.system_config
    
    async def update_algorithm_config(self, name: str, updates: Dict[str, Any]) -> bool:
        """更新算法配置
        
        Args:
            name: 算法名稱
            updates: 更新內容
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if name not in self.algorithm_configs:
                logger.error(f"算法 {name} 不存在")
                return False
            
            # 更新內存中的配置
            config = self.algorithm_configs[name]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # 更新配置文件（可選）
            # 這裡可以實現配置文件的自動更新
            
            logger.info(f"成功更新算法 {name} 的配置")
            return True
            
        except Exception as e:
            logger.error(f"更新算法配置失敗: {e}")
            return False
    
    async def enable_algorithm(self, name: str) -> bool:
        """啟用算法
        
        Args:
            name: 算法名稱
            
        Returns:
            bool: 是否啟用成功
        """
        return await self.update_algorithm_config(name, {"enabled": True})
    
    async def disable_algorithm(self, name: str) -> bool:
        """禁用算法
        
        Args:
            name: 算法名稱
            
        Returns:
            bool: 是否禁用成功
        """
        return await self.update_algorithm_config(name, {"enabled": False})
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """獲取管理器統計資訊
        
        Returns:
            Dict[str, Any]: 統計資訊
        """
        enabled_algorithms = sum(1 for config in self.algorithm_configs.values() if config.enabled)
        
        return {
            "initialized": self._initialized,
            "config_path": str(self.config_path),
            "config_hash": self._config_hash,
            "total_algorithms": len(self.algorithm_configs),
            "enabled_algorithms": enabled_algorithms,
            "loaded_instances": len(self.algorithms),
            "system_config": {
                "environment": self.system_config.environment if self.system_config else "unknown",
                "monitoring_enabled": self.system_config.enable_monitoring if self.system_config else False
            },
            "file_watchers_active": len(self._file_watchers)
        }
    
    async def shutdown(self) -> None:
        """關閉管理器"""
        try:
            # 停止文件監控
            for task in self._file_watchers:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # 清理算法實例
            for algorithm in self.algorithms.values():
                try:
                    if hasattr(algorithm, 'cleanup'):
                        await algorithm.cleanup()
                except Exception as e:
                    logger.warning(f"清理算法實例失敗: {e}")
            
            self.algorithms.clear()
            self._initialized = False
            
            logger.info("配置驅動算法管理器已關閉")
            
        except Exception as e:
            logger.error(f"關閉算法管理器失敗: {e}")


# 工具函數
def create_default_config(config_path: Union[str, Path]) -> None:
    """創建預設配置文件
    
    Args:
        config_path: 配置文件路徑
    """
    default_config = {
        "system": {
            "environment": "development",
            "log_level": "INFO",
            "database_url": "postgresql://postgres:password@localhost:5432/rl_system",
            "redis_url": "redis://localhost:6379/0",
            "model_storage_path": "./models",
            "enable_monitoring": True,
            "enable_web_ui": True,
            "api_rate_limit": 1000,
            "max_concurrent_training": 3
        },
        "handover_algorithms": {
            "reinforcement_learning": {
                "dqn": {
                    "algorithm_type": "DQN",
                    "enabled": True,
                    "scenarios": ["urban", "suburban"],
                    "hyperparameters": {
                        "learning_rate": 0.001,
                        "batch_size": 32,
                        "epsilon": 0.1,
                        "gamma": 0.99
                    },
                    "training": {
                        "max_episodes": 1000,
                        "max_steps_per_episode": 500
                    },
                    "deployment": {
                        "auto_deploy": False,
                        "validation_required": True
                    }
                },
                "ppo": {
                    "algorithm_type": "PPO",
                    "enabled": True,
                    "scenarios": ["urban", "low_latency"],
                    "hyperparameters": {
                        "learning_rate": 0.0003,
                        "batch_size": 64,
                        "gamma": 0.99,
                        "clip_epsilon": 0.2
                    }
                },
                "sac": {
                    "algorithm_type": "SAC",
                    "enabled": False,
                    "scenarios": ["suburban", "high_mobility"],
                    "hyperparameters": {
                        "learning_rate": 0.0001,
                        "batch_size": 128,
                        "tau": 0.005
                    }
                }
            }
        }
    }
    
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    logger.info(f"已創建預設配置文件: {config_path}")


# 異常定義
class ConfigManagerError(Exception):
    """配置管理器基礎異常"""
    pass


class ConfigFileError(ConfigManagerError):
    """配置文件異常"""
    pass


class AlgorithmLoadError(ConfigManagerError):
    """算法加載異常"""
    pass