"""
🎯 環境管理器 - 重構後的簡化版本

算法環境管理的核心組件，專注於環境生命週期管理。
重構後職責專注於管理，具體轉換功能委派給專門模組。
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .interfaces import HandoverContext, HandoverDecision
from .environment import GymnasiumEnvironmentBridge, EnvironmentDataConverter

logger = logging.getLogger(__name__)

# 檢查 Gymnasium 可用性
GYMNASIUM_AVAILABLE = False
try:
    import gymnasium as gym
    GYMNASIUM_AVAILABLE = True
    logger.info("Gymnasium 可用")
except ImportError:
    logger.warning("Gymnasium 不可用，部分功能受限")


class EnvironmentType(Enum):
    """環境類型"""
    LEO_SATELLITE_HANDOVER = "LEOSatelliteHandoverEnv"
    SATELLITE_CONSTELLATION = "SatelliteConstellationEnv"
    MULTI_UE_HANDOVER = "MultiUEHandoverEnv"
    CUSTOM = "custom"


class EnvironmentStatus(Enum):
    """環境狀態"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class EnvironmentConfig:
    """環境配置"""
    env_type: EnvironmentType
    config: Dict[str, Any]
    enable_gymnasium: bool = True
    auto_reset: bool = True
    max_episodes: int = 1000
    max_steps_per_episode: int = 500


@dataclass
class EnvironmentInfo:
    """環境信息"""
    env_id: str
    env_type: EnvironmentType
    status: EnvironmentStatus
    config: EnvironmentConfig
    created_at: datetime
    total_episodes: int = 0
    total_steps: int = 0
    current_episode_steps: int = 0
    last_reward: float = 0.0
    metadata: Dict[str, Any] = None


class EnvironmentManager:
    """環境管理器 - 重構後的簡化版本
    
    主要職責：
    1. 環境生命週期管理
    2. 環境配置管理
    3. 協調橋接器和轉換器
    """
    
    def __init__(self):
        self._environments: Dict[str, GymnasiumEnvironmentBridge] = {}
        self._environment_configs: Dict[str, EnvironmentConfig] = {}
        self._environment_info: Dict[str, EnvironmentInfo] = {}
        self._default_env_id: Optional[str] = None
        self._initialized = False

    async def initialize(self, default_config: Optional[EnvironmentConfig] = None) -> None:
        """初始化環境管理器"""
        try:
            # 設置默認配置
            if default_config is None:
                default_config = EnvironmentConfig(
                    env_type=EnvironmentType.LEO_SATELLITE_HANDOVER,
                    config={
                        'max_satellites': 10,
                        'ue_count': 1,
                        'scenario': 'urban'
                    }
                )
            
            # 創建默認環境
            if GYMNASIUM_AVAILABLE:
                default_env_id = await self.create_environment(
                    env_type=default_config.env_type,
                    config=default_config.config,
                    auto_create=True
                )
                if default_env_id:
                    self._default_env_id = default_env_id
            
            self._initialized = True
            logger.info("EnvironmentManager 初始化完成")
            
        except Exception as e:
            logger.error(f"EnvironmentManager 初始化失敗: {e}")
            raise

    async def create_environment(self, env_type: EnvironmentType, 
                               config: Dict[str, Any], 
                               auto_create: bool = True) -> Optional[str]:
        """創建環境
        
        Args:
            env_type: 環境類型
            config: 環境配置
            auto_create: 是否自動創建
            
        Returns:
            str: 環境ID，失敗返回None
        """
        try:
            env_id = str(uuid.uuid4())
            
            # 創建環境配置
            env_config = EnvironmentConfig(
                env_type=env_type,
                config=config,
                enable_gymnasium=GYMNASIUM_AVAILABLE,
                auto_reset=config.get('auto_reset', True),
                max_episodes=config.get('max_episodes', 1000),
                max_steps_per_episode=config.get('max_steps_per_episode', 500)
            )
            
            # 創建環境信息
            env_info = EnvironmentInfo(
                env_id=env_id,
                env_type=env_type,
                status=EnvironmentStatus.CREATED,
                config=env_config,
                created_at=datetime.now(),
                metadata=config.get('metadata', {})
            )
            
            if auto_create and GYMNASIUM_AVAILABLE:
                # 創建 Gymnasium 橋接器
                try:
                    env_bridge = GymnasiumEnvironmentBridge(env_type.value, config)
                    
                    # 嘗試創建環境
                    if await env_bridge.create_env():
                        self._environments[env_id] = env_bridge
                        env_info.status = EnvironmentStatus.RUNNING
                        logger.info(f"成功創建環境: {env_id}")
                    else:
                        logger.warning(f"環境創建失敗，但繼續註冊: {env_id}")
                        env_info.status = EnvironmentStatus.ERROR
                        
                except Exception as e:
                    logger.error(f"創建環境橋接器失敗: {e}")
                    env_info.status = EnvironmentStatus.ERROR
            
            # 保存配置和信息
            self._environment_configs[env_id] = env_config
            self._environment_info[env_id] = env_info
            
            return env_id
            
        except Exception as e:
            logger.error(f"創建環境失敗: {e}")
            return None

    def get_environment(self, env_id: Optional[str] = None) -> Optional[GymnasiumEnvironmentBridge]:
        """獲取環境實例
        
        Args:
            env_id: 環境ID，None時返回默認環境
            
        Returns:
            GymnasiumEnvironmentBridge: 環境實例
        """
        if env_id is None:
            env_id = self._default_env_id
        
        if env_id is None:
            logger.warning("沒有可用的環境")
            return None
        
        if env_id not in self._environments:
            logger.warning(f"環境不存在: {env_id}")
            return None
        
        return self._environments[env_id]

    def list_environments(self) -> List[EnvironmentInfo]:
        """列出所有環境"""
        return list(self._environment_info.values())

    async def remove_environment(self, env_id: str) -> bool:
        """移除環境
        
        Args:
            env_id: 環境ID
            
        Returns:
            bool: 是否成功移除
        """
        try:
            if env_id in self._environments:
                # 關閉環境
                self._environments[env_id].close()
                del self._environments[env_id]
            
            if env_id in self._environment_configs:
                del self._environment_configs[env_id]
            
            if env_id in self._environment_info:
                del self._environment_info[env_id]
            
            # 如果移除的是默認環境，清除默認設置
            if self._default_env_id == env_id:
                self._default_env_id = None
                # 如果還有其他環境，設置第一個為默認
                if self._environments:
                    self._default_env_id = next(iter(self._environments.keys()))
            
            logger.info(f"成功移除環境: {env_id}")
            return True
            
        except Exception as e:
            logger.error(f"移除環境失敗: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """獲取管理器統計信息"""
        try:
            total_environments = len(self._environment_info)
            
            # 統計環境類型和狀態
            env_types = {}
            env_statuses = {}
            for info in self._environment_info.values():
                env_type = info.env_type.value
                env_status = info.status.value
                env_types[env_type] = env_types.get(env_type, 0) + 1
                env_statuses[env_status] = env_statuses.get(env_status, 0) + 1
            
            return {
                'total_environments': total_environments,
                'default_env_id': self._default_env_id,
                'environment_types': env_types,
                'environment_statuses': env_statuses,
                'gymnasium_available': GYMNASIUM_AVAILABLE,
                'initialized': self._initialized
            }
            
        except Exception as e:
            logger.error(f"獲取統計信息失敗: {e}")
            return {'error': str(e)}

    async def cleanup(self) -> None:
        """清理資源"""
        try:
            # 關閉所有環境
            for env_id in list(self._environments.keys()):
                await self.remove_environment(env_id)
            
            # 清理所有數據
            self._environments.clear()
            self._environment_configs.clear()
            self._environment_info.clear()
            self._default_env_id = None
            self._initialized = False
            
            logger.info("EnvironmentManager 資源清理完成")
            
        except Exception as e:
            logger.error(f"資源清理失敗: {e}")
    
    # === 便捷方法 ===
    
    def get_default_environment(self) -> Optional[GymnasiumEnvironmentBridge]:
        """獲取默認環境"""
        return self.get_environment()
    
    def get_environment_info(self, env_id: Optional[str] = None) -> Optional[EnvironmentInfo]:
        """獲取環境信息"""
        if env_id is None:
            env_id = self._default_env_id
        
        if env_id is None:
            return None
        
        return self._environment_info.get(env_id)
    
    def is_initialized(self) -> bool:
        """檢查是否已初始化"""
        return self._initialized
    
    def has_environments(self) -> bool:
        """檢查是否有環境"""
        return len(self._environments) > 0