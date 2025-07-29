#!/usr/bin/env python3
"""
遷移配置服務 - Phase 1 Skyfield 到 NetStack 遷移管理

提供配置開關來控制遷移過程，支援逐步遷移和回退機制。
"""

import os
import json
import structlog
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = structlog.get_logger(__name__)


@dataclass
class MigrationConfig:
    """遷移配置數據類"""
    
    # === 總開關 ===
    migration_enabled: bool = True
    force_netstack: bool = False  # 強制使用 NetStack，無降級
    
    # === 服務級別開關 ===
    orbit_service_migration: bool = True
    satellite_position_migration: bool = True
    visibility_calculation_migration: bool = True
    tle_processing_migration: bool = False  # TLE 處理保持 skyfield
    
    # === API 端點遷移 ===
    satellite_routes_migration: bool = True
    tle_routes_migration: bool = False
    coordinate_routes_migration: bool = True
    
    # === NetStack 客戶端配置 ===
    netstack_base_url: str = "http://netstack-api:8000"
    netstack_timeout_seconds: int = 30
    netstack_retry_attempts: int = 3
    
    # === 降級策略 ===
    enable_skyfield_fallback: bool = True
    enable_simulation_fallback: bool = True
    fallback_timeout_seconds: int = 5
    
    # === 性能優化 ===
    enable_caching: bool = True
    cache_duration_minutes: int = 10
    batch_size_limit: int = 100
    
    # === 監控和日誌 ===
    enable_migration_logging: bool = True
    log_performance_metrics: bool = True
    alert_on_fallback: bool = True
    
    # === 實驗性功能 ===
    use_precomputed_data: bool = True
    use_optimal_timewindows: bool = True
    use_display_optimization: bool = True


class MigrationConfigManager:
    """遷移配置管理器"""
    
    def __init__(self, config_file: str = "/app/config/migration_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路徑
        """
        self.config_file = Path(config_file)
        self.config: MigrationConfig = MigrationConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """載入配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新配置對象
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                logger.info(f"載入遷移配置: {self.config_file}")
            else:
                logger.info("配置文件不存在，使用默認配置")
                self._save_config()  # 創建默認配置文件
                
        except Exception as e:
            logger.error(f"載入配置失敗: {e}，使用默認配置")
    
    def _save_config(self) -> None:
        """保存配置文件"""
        try:
            # 確保目錄存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
            
            logger.info(f"保存遷移配置: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
    
    def get_config(self) -> MigrationConfig:
        """獲取當前配置"""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            updates: 配置更新字典
        """
        try:
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.info(f"更新配置: {key} = {value}")
                else:
                    logger.warning(f"未知配置項: {key}")
            
            self._save_config()
            
        except Exception as e:
            logger.error(f"更新配置失敗: {e}")
    
    def reset_to_defaults(self) -> None:
        """重置為默認配置"""
        self.config = MigrationConfig()
        self._save_config()
        logger.info("重置為默認配置")
    
    def enable_full_migration(self) -> None:
        """啟用完整遷移模式"""
        updates = {
            "migration_enabled": True,
            "force_netstack": True,
            "orbit_service_migration": True,
            "satellite_position_migration": True,
            "visibility_calculation_migration": True,
            "satellite_routes_migration": True,
            "coordinate_routes_migration": True,
            "enable_skyfield_fallback": False
        }
        self.update_config(updates)
        logger.info("啟用完整遷移模式")
    
    def enable_safe_migration(self) -> None:
        """啟用安全遷移模式 (保留降級機制)"""
        updates = {
            "migration_enabled": True,
            "force_netstack": False,
            "orbit_service_migration": True,
            "satellite_position_migration": True,
            "visibility_calculation_migration": True,
            "enable_skyfield_fallback": True,
            "enable_simulation_fallback": True
        }
        self.update_config(updates)
        logger.info("啟用安全遷移模式")
    
    def disable_migration(self) -> None:
        """禁用遷移，回退到 skyfield"""
        updates = {
            "migration_enabled": False,
            "force_netstack": False,
            "orbit_service_migration": False,
            "satellite_position_migration": False,
            "visibility_calculation_migration": False,
            "satellite_routes_migration": False
        }
        self.update_config(updates)
        logger.info("禁用遷移，回退到 skyfield")
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        獲取特定服務的配置
        
        Args:
            service_name: 服務名稱
            
        Returns:
            服務配置字典
        """
        service_configs = {
            "orbit_service": {
                "migration_enabled": self.config.orbit_service_migration,
                "netstack_url": self.config.netstack_base_url,
                "timeout": self.config.netstack_timeout_seconds,
                "enable_fallback": self.config.enable_skyfield_fallback,
                "enable_caching": self.config.enable_caching
            },
            "satellite_routes": {
                "migration_enabled": self.config.satellite_routes_migration,
                "netstack_url": self.config.netstack_base_url,
                "batch_size": self.config.batch_size_limit,
                "enable_precomputed": self.config.use_precomputed_data
            },
            "visibility_calculator": {
                "migration_enabled": self.config.visibility_calculation_migration,
                "use_optimal_windows": self.config.use_optimal_timewindows,
                "cache_duration": self.config.cache_duration_minutes
            }
        }
        
        return service_configs.get(service_name, {})
    
    def is_migration_enabled(self, component: str = "global") -> bool:
        """
        檢查特定組件是否啟用遷移
        
        Args:
            component: 組件名稱
            
        Returns:
            是否啟用遷移
        """
        if not self.config.migration_enabled:
            return False
        
        component_map = {
            "global": True,
            "orbit_service": self.config.orbit_service_migration,
            "satellite_position": self.config.satellite_position_migration,
            "visibility_calculation": self.config.visibility_calculation_migration,
            "tle_processing": self.config.tle_processing_migration,
            "satellite_routes": self.config.satellite_routes_migration,
            "tle_routes": self.config.tle_routes_migration,
            "coordinate_routes": self.config.coordinate_routes_migration
        }
        
        return component_map.get(component, False)
    
    def get_netstack_config(self) -> Dict[str, Any]:
        """獲取 NetStack 客戶端配置"""
        return {
            "base_url": self.config.netstack_base_url,
            "timeout": self.config.netstack_timeout_seconds,
            "retry_attempts": self.config.netstack_retry_attempts,
            "enable_caching": self.config.enable_caching,
            "cache_duration": self.config.cache_duration_minutes
        }
    
    def get_fallback_config(self) -> Dict[str, Any]:
        """獲取降級策略配置"""
        return {
            "enable_skyfield_fallback": self.config.enable_skyfield_fallback,
            "enable_simulation_fallback": self.config.enable_simulation_fallback,
            "fallback_timeout": self.config.fallback_timeout_seconds,
            "alert_on_fallback": self.config.alert_on_fallback
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """獲取監控配置"""
        return {
            "enable_logging": self.config.enable_migration_logging,
            "log_performance": self.config.log_performance_metrics,
            "alert_on_fallback": self.config.alert_on_fallback
        }
    
    def export_config(self) -> Dict[str, Any]:
        """導出完整配置"""
        return asdict(self.config)
    
    def import_config(self, config_dict: Dict[str, Any]) -> None:
        """
        導入配置
        
        Args:
            config_dict: 配置字典
        """
        try:
            for key, value in config_dict.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            self._save_config()
            logger.info("導入配置成功")
            
        except Exception as e:
            logger.error(f"導入配置失敗: {e}")


# === 全域配置管理器實例 ===

_config_manager: Optional[MigrationConfigManager] = None

def get_migration_config() -> MigrationConfigManager:
    """
    獲取遷移配置管理器單例
    
    Returns:
        配置管理器實例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = MigrationConfigManager()
    return _config_manager


# === 環境變量配置覆蓋 ===

def apply_env_overrides() -> None:
    """應用環境變量配置覆蓋"""
    config_manager = get_migration_config()
    config = config_manager.get_config()
    
    # 環境變量映射
    env_mappings = {
        "MIGRATION_ENABLED": "migration_enabled",
        "FORCE_NETSTACK": "force_netstack",
        "NETSTACK_BASE_URL": "netstack_base_url",
        "NETSTACK_TIMEOUT": "netstack_timeout_seconds",
        "ENABLE_SKYFIELD_FALLBACK": "enable_skyfield_fallback",
        "ENABLE_CACHING": "enable_caching"
    }
    
    updates = {}
    for env_var, config_key in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            # 類型轉換
            if config_key in ["migration_enabled", "force_netstack", "enable_skyfield_fallback", "enable_caching"]:
                updates[config_key] = env_value.lower() in ("true", "1", "yes", "on")
            elif config_key in ["netstack_timeout_seconds"]:
                updates[config_key] = int(env_value)
            else:
                updates[config_key] = env_value
    
    if updates:
        config_manager.update_config(updates)
        logger.info(f"應用環境變量覆蓋: {updates}")


# === 便利函數 ===

def is_migration_enabled(component: str = "global") -> bool:
    """檢查是否啟用遷移 (便利函數)"""
    return get_migration_config().is_migration_enabled(component)

def get_netstack_url() -> str:
    """獲取 NetStack URL (便利函數)"""
    return get_migration_config().get_config().netstack_base_url

def should_use_skyfield_fallback() -> bool:
    """是否應該使用 skyfield 降級 (便利函數)"""
    config = get_migration_config().get_config()
    return config.enable_skyfield_fallback and not config.force_netstack


# === 初始化 ===

# 應用環境變量覆蓋
apply_env_overrides()