"""
驗證框架統一配置管理器
提供配置載入、驗證、更新等功能
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationConfig:
    """驗證配置基礎類"""
    
    def __init__(self, config_data: Dict[str, Any] = None):
        """
        初始化驗證配置
        
        Args:
            config_data: 配置數據
        """
        self.config_data = config_data or {}
        self.last_updated = datetime.utcnow()
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        獲取配置值，支持點號分隔的嵌套鍵
        
        Args:
            key: 配置鍵（支持 "parent.child.key" 格式）
            default: 默認值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config_data
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any):
        """
        設置配置值，支持點號分隔的嵌套鍵
        
        Args:
            key: 配置鍵
            value: 配置值
        """
        keys = key.split(".")
        config = self.config_data
        
        # 創建嵌套結構
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        # 設置最終值
        config[keys[-1]] = value
        self.last_updated = datetime.utcnow()
        
    def update(self, other_config: Union[Dict[str, Any], "ValidationConfig"]):
        """
        更新配置
        
        Args:
            other_config: 其他配置數據或配置對象
        """
        if isinstance(other_config, ValidationConfig):
            other_data = other_config.config_data
        else:
            other_data = other_config
            
        self._deep_update(self.config_data, other_data)
        self.last_updated = datetime.utcnow()
        
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "config_data": self.config_data,
            "last_updated": self.last_updated.isoformat()
        }
        
    def validate(self) -> bool:
        """驗證配置完整性"""
        # 基礎類默認返回True，子類可以覆蓋
        return True


class ConfigManager:
    """配置管理器主類"""
    
    def __init__(self, config_dir: str = "/app/config/validation"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目錄路徑
        """
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, ValidationConfig] = {}
        self.config_files: Dict[str, str] = {}
        self.logger = logging.getLogger("validation.config_manager")
        
        # 創建配置目錄
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 載入默認配置
        self._load_default_configs()
        
    def _load_default_configs(self):
        """載入默認配置"""
        default_configs = {
            "engine": {
                "parallel_execution": True,
                "max_workers": 4,
                "stop_on_critical": True,
                "timeout_seconds": 300
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_enabled": True,
                "console_enabled": True
            },
            "academic_standards": {
                "grade_a_requirements": {
                    "zero_tolerance_threshold": 0.01,
                    "eci_coordinate_range": [-42000, 42000],
                    "mandatory_tle_epoch": True,
                    "sgp4_calculation_required": True
                }
            },
            "data_quality": {
                "statistical_analysis": {
                    "enabled": True,
                    "outlier_detection_threshold": 3.0,
                    "distribution_tests": ["normality", "consistency"]
                },
                "completeness_checks": {
                    "required_fields_coverage": 0.95,
                    "missing_data_threshold": 0.05
                }
            }
        }
        
        for config_name, config_data in default_configs.items():
            self.configs[config_name] = ValidationConfig(config_data)
            
        self.logger.info(f"Loaded {len(default_configs)} default configurations")
        
    def load_config_file(self, file_path: str, config_name: str = None) -> bool:
        """
        從文件載入配置
        
        Args:
            file_path: 配置文件路徑
            config_name: 配置名稱，如果不提供則使用文件名
            
        Returns:
            是否載入成功
        """
        file_path = Path(file_path)
        if not file_path.exists():
            self.logger.error(f"Config file not found: {file_path}")
            return False
            
        if config_name is None:
            config_name = file_path.stem
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() in [".yml", ".yaml"]:
                    config_data = yaml.safe_load(f)
                elif file_path.suffix.lower() == ".json":
                    config_data = json.load(f)
                else:
                    self.logger.error(f"Unsupported config file format: {file_path.suffix}")
                    return False
                    
            # 創建或更新配置
            if config_name in self.configs:
                self.configs[config_name].update(config_data)
                self.logger.info(f"Updated configuration: {config_name}")
            else:
                self.configs[config_name] = ValidationConfig(config_data)
                self.logger.info(f"Loaded new configuration: {config_name}")
                
            self.config_files[config_name] = str(file_path)
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to load config file {file_path}: {e}")
            return False
            
    def save_config_file(self, config_name: str, file_path: str = None, format: str = "yaml") -> bool:
        """
        保存配置到文件
        
        Args:
            config_name: 配置名稱
            file_path: 保存路徑，如果不提供則使用默認路徑
            format: 文件格式（yaml/json）
            
        Returns:
            是否保存成功
        """
        if config_name not in self.configs:
            self.logger.error(f"Configuration {config_name} not found")
            return False
            
        if file_path is None:
            file_ext = "yml" if format.lower() == "yaml" else "json"
            file_path = self.config_dir / f"{config_name}.{file_ext}"
        else:
            file_path = Path(file_path)
            
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = self.configs[config_name].config_data
            
            with open(file_path, "w", encoding="utf-8") as f:
                if format.lower() == "yaml":
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                    
            self.config_files[config_name] = str(file_path)
            self.logger.info(f"Saved configuration {config_name} to {file_path}")
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to save config file {file_path}: {e}")
            return False
            
    def get_config(self, config_name: str) -> Optional[ValidationConfig]:
        """
        獲取配置對象
        
        Args:
            config_name: 配置名稱
            
        Returns:
            配置對象，如果不存在則返回None
        """
        return self.configs.get(config_name)
        
    def get_config_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        獲取配置值
        
        Args:
            config_name: 配置名稱
            key: 配置鍵
            default: 默認值
            
        Returns:
            配置值
        """
        config = self.get_config(config_name)
        if config:
            return config.get(key, default)
        return default
        
    def set_config_value(self, config_name: str, key: str, value: Any):
        """
        設置配置值
        
        Args:
            config_name: 配置名稱
            key: 配置鍵
            value: 配置值
        """
        if config_name not in self.configs:
            self.configs[config_name] = ValidationConfig()
            
        self.configs[config_name].set(key, value)
        
    def reload_config(self, config_name: str) -> bool:
        """
        重新載入配置
        
        Args:
            config_name: 配置名稱
            
        Returns:
            是否重新載入成功
        """
        if config_name in self.config_files:
            file_path = self.config_files[config_name]
            return self.load_config_file(file_path, config_name)
        else:
            self.logger.warning(f"No file path recorded for config: {config_name}")
            return False
            
    def validate_all_configs(self) -> Dict[str, bool]:
        """
        驗證所有配置
        
        Returns:
            配置驗證結果字典
        """
        results = {}
        for config_name, config in self.configs.items():
            try:
                results[config_name] = config.validate()
            except Exception as e:
                self.logger.exception(f"Config validation error for {config_name}: {e}")
                results[config_name] = False
                
        return results
        
    def get_all_config_names(self) -> List[str]:
        """獲取所有配置名稱"""
        return list(self.configs.keys())
        
    def export_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        導出所有配置
        
        Returns:
            包含所有配置的字典
        """
        return {
            name: config.config_data 
            for name, config in self.configs.items()
        }
        
    def import_configs(self, configs_data: Dict[str, Dict[str, Any]]):
        """
        導入配置數據
        
        Args:
            configs_data: 配置數據字典
        """
        for config_name, config_data in configs_data.items():
            if config_name in self.configs:
                self.configs[config_name].update(config_data)
            else:
                self.configs[config_name] = ValidationConfig(config_data)
                
        self.logger.info(f"Imported {len(configs_data)} configurations")
        
    def __str__(self) -> str:
        return f"ConfigManager(configs={len(self.configs)}, dir={self.config_dir})"


# 全局配置管理器實例
_global_config_manager: Optional[ConfigManager] = None


def get_global_config_manager() -> ConfigManager:
    """獲取全局配置管理器實例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def get_config_value(config_name: str, key: str, default: Any = None) -> Any:
    """獲取配置值的便捷函數"""
    return get_global_config_manager().get_config_value(config_name, key, default)


def set_config_value(config_name: str, key: str, value: Any):
    """設置配置值的便捷函數"""
    get_global_config_manager().set_config_value(config_name, key, value)
