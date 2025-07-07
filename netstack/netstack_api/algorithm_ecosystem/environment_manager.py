"""
🌍 環境管理器

統一管理 Gymnasium 環境和算法執行環境，為強化學習和傳統算法提供標準化的執行環境。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False

from .interfaces import (
    HandoverContext,
    HandoverDecision,
    GeoCoordinate,
    SignalMetrics,
    SatelliteInfo,
    HandoverDecisionType
)

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """環境類型"""
    GYMNASIUM = "gymnasium"
    SIMULATION = "simulation"
    REAL_WORLD = "real_world"
    MOCK = "mock"


class EnvironmentStatus(Enum):
    """環境狀態"""
    UNINITIALIZED = "uninitialized"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class EnvironmentConfig:
    """環境配置"""
    env_type: EnvironmentType
    env_name: str
    parameters: Dict[str, Any]
    max_episode_steps: int = 1000
    reward_config: Optional[Dict[str, Any]] = None
    observation_config: Optional[Dict[str, Any]] = None
    action_config: Optional[Dict[str, Any]] = None


@dataclass
class EnvironmentInfo:
    """環境信息"""
    env_id: str
    env_type: EnvironmentType
    env_name: str
    status: EnvironmentStatus
    observation_space: Optional[Any] = None
    action_space: Optional[Any] = None
    current_episode: int = 0
    total_steps: int = 0
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None


class GymnasiumEnvironmentBridge:
    """Gymnasium 環境橋接器
    
    為現有的 LEOSatelliteHandoverEnv 提供標準化接口。
    """
    
    def __init__(self, env_name: str, config: Dict[str, Any]):
        """初始化橋接器
        
        Args:
            env_name: 環境名稱
            config: 環境配置
        """
        self.env_name = env_name
        self.config = config
        self.env: Optional['gym.Env'] = None
        self._current_obs = None
        self._current_info = None
        self._episode_count = 0
        self._total_steps = 0
        
        if not GYMNASIUM_AVAILABLE:
            raise ImportError("Gymnasium not available")
    
    async def create_env(self) -> 'gym.Env':
        """創建 Gymnasium 環境"""
        try:
            if self.env_name == "LEOSatelliteHandoverEnv-v1":
                # 導入現有的環境
                from ..envs.handover_env_fixed import LEOSatelliteHandoverEnv
                self.env = LEOSatelliteHandoverEnv(
                    scenario=self.config.get('scenario', 'urban'),
                    max_ues=self.config.get('max_ues', 100),
                    max_satellites=self.config.get('max_satellites', 10),
                    episode_length=self.config.get('episode_length', 1000),
                    netstack_api_url=self.config.get('netstack_api_url', 'http://localhost:8080'),
                    simworld_api_url=self.config.get('simworld_api_url', 'http://localhost:8888')
                )
            else:
                # 使用 gym.make 創建標準環境
                self.env = gym.make(self.env_name, **self.config)
            
            logger.info(f"Gymnasium 環境 '{self.env_name}' 創建成功")
            return self.env
            
        except Exception as e:
            logger.error(f"創建 Gymnasium 環境失敗: {e}")
            raise
    
    def obs_to_context(self, obs: np.ndarray, info: Dict[str, Any]) -> HandoverContext:
        """將環境觀察轉換為 HandoverContext
        
        Args:
            obs: 環境觀察
            info: 環境信息
            
        Returns:
            HandoverContext: 換手上下文
        """
        try:
            # 解析觀察向量 (基於 LEOSatelliteHandoverEnv 的觀察空間)
            # 觀察向量格式: [ue_features(4), current_satellite_features(6), candidate_satellites_features(6*max_satellites), network_features(4)]
            
            ue_features = obs[:4]  # UE 位置和速度
            current_sat_features = obs[4:10]  # 當前衛星特徵
            
            # 解析 UE 信息
            ue_location = GeoCoordinate(
                latitude=float(ue_features[0]),
                longitude=float(ue_features[1]),
                altitude=0.0
            )
            
            ue_velocity = GeoCoordinate(
                latitude=float(ue_features[2]),
                longitude=float(ue_features[3]),
                altitude=0.0
            )
            
            # 解析當前衛星信息
            current_satellite = None
            current_signal_metrics = None
            if current_sat_features[0] > 0:  # 有當前衛星
                current_satellite = f"sat_{int(current_sat_features[0])}"
                current_signal_metrics = SignalMetrics(
                    rsrp=float(current_sat_features[1]),
                    rsrq=float(current_sat_features[2]),
                    sinr=float(current_sat_features[3]),
                    throughput=float(current_sat_features[4]),
                    latency=float(current_sat_features[5])
                )
            
            # 解析候選衛星信息
            candidate_satellites = []
            max_satellites = self.config.get('max_satellites', 10)
            for i in range(max_satellites):
                start_idx = 10 + i * 6
                sat_features = obs[start_idx:start_idx + 6]
                
                if sat_features[0] > 0:  # 衛星存在
                    satellite_info = SatelliteInfo(
                        satellite_id=f"sat_{int(sat_features[0])}",
                        position=GeoCoordinate(
                            latitude=float(sat_features[1]),
                            longitude=float(sat_features[2]),
                            altitude=600000.0  # LEO 軌道高度
                        ),
                        signal_metrics=SignalMetrics(
                            rsrp=float(sat_features[3]),
                            rsrq=float(sat_features[4]),
                            sinr=float(sat_features[5]),
                            throughput=0.0,
                            latency=0.0
                        )
                    )
                    candidate_satellites.append(satellite_info)
            
            # 構建網路狀態
            network_start_idx = 10 + max_satellites * 6
            network_features = obs[network_start_idx:network_start_idx + 4]
            network_state = {
                'total_ues': int(network_features[0]),
                'active_satellites': int(network_features[1]),
                'network_load': float(network_features[2]),
                'interference_level': float(network_features[3])
            }
            
            # 創建 HandoverContext
            context = HandoverContext(
                ue_id=info.get('ue_id', 'ue_001'),
                current_satellite=current_satellite,
                ue_location=ue_location,
                ue_velocity=ue_velocity,
                current_signal_metrics=current_signal_metrics,
                candidate_satellites=candidate_satellites,
                network_state=network_state,
                timestamp=datetime.now(),
                scenario_info=info.get('scenario_info'),
                weather_conditions=info.get('weather_conditions'),
                traffic_load=info.get('traffic_load')
            )
            
            return context
            
        except Exception as e:
            logger.error(f"觀察轉換失敗: {e}")
            # 返回最小化的上下文
            return HandoverContext(
                ue_id=info.get('ue_id', 'ue_001'),
                current_satellite=None,
                ue_location=GeoCoordinate(latitude=0.0, longitude=0.0),
                ue_velocity=None,
                current_signal_metrics=None,
                candidate_satellites=[],
                network_state={},
                timestamp=datetime.now()
            )
    
    def decision_to_action(self, decision: HandoverDecision) -> Union[int, np.ndarray]:
        """將 HandoverDecision 轉換為環境動作
        
        Args:
            decision: 換手決策
            
        Returns:
            環境動作
        """
        try:
            if hasattr(self.env, 'action_space'):
                if isinstance(self.env.action_space, spaces.Discrete):
                    # 離散動作空間
                    if decision.handover_decision == HandoverDecisionType.NO_HANDOVER:
                        return 0
                    elif decision.handover_decision == HandoverDecisionType.IMMEDIATE_HANDOVER:
                        # 如果有目標衛星，返回對應的動作索引
                        if decision.target_satellite:
                            try:
                                sat_id = int(decision.target_satellite.split('_')[-1])
                                return min(sat_id, self.env.action_space.n - 1)
                            except (ValueError, IndexError):
                                return 1  # 默認換手動作
                        return 1
                    elif decision.handover_decision == HandoverDecisionType.PREPARE_HANDOVER:
                        return 2
                    else:
                        return 0
                
                elif isinstance(self.env.action_space, spaces.Box):
                    # 連續動作空間
                    action = np.zeros(self.env.action_space.shape)
                    action[0] = float(decision.handover_decision.value)
                    if decision.target_satellite:
                        try:
                            sat_id = int(decision.target_satellite.split('_')[-1])
                            action[1] = min(float(sat_id), self.env.action_space.high[1])
                        except (ValueError, IndexError):
                            action[1] = 0.0
                    action[2] = decision.confidence
                    return action
                
                else:
                    # 其他動作空間類型
                    return decision.handover_decision.value
            
            else:
                # 沒有定義動作空間，返回決策值
                return decision.handover_decision.value
                
        except Exception as e:
            logger.error(f"決策轉換失敗: {e}")
            return 0  # 默認無換手動作
    
    async def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """重置環境"""
        if not self.env:
            await self.create_env()
        
        obs, info = self.env.reset()
        self._current_obs = obs
        self._current_info = info
        self._episode_count += 1
        
        return obs, info
    
    async def step(self, action: Any) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """執行環境步驟"""
        if not self.env:
            raise RuntimeError("環境未初始化")
        
        obs, reward, terminated, truncated, info = self.env.step(action)
        self._current_obs = obs
        self._current_info = info
        self._total_steps += 1
        
        return obs, reward, terminated, truncated, info
    
    def get_observation_space(self) -> Any:
        """獲取觀察空間"""
        return self.env.observation_space if self.env else None
    
    def get_action_space(self) -> Any:
        """獲取動作空間"""
        return self.env.action_space if self.env else None
    
    def close(self) -> None:
        """關閉環境"""
        if self.env:
            self.env.close()
            self.env = None


class EnvironmentManager:
    """環境管理器
    
    統一管理所有類型的執行環境，為算法提供標準化的環境接口。
    """
    
    def __init__(self):
        """初始化環境管理器"""
        self._environments: Dict[str, GymnasiumEnvironmentBridge] = {}
        self._environment_configs: Dict[str, EnvironmentConfig] = {}
        self._environment_info: Dict[str, EnvironmentInfo] = {}
        self._default_env_id: Optional[str] = None
        self._initialized = False
        
        logger.info("環境管理器初始化")
    
    async def initialize(self, default_config: Optional[Dict[str, Any]] = None) -> None:
        """初始化環境管理器
        
        Args:
            default_config: 默認環境配置
        """
        if self._initialized:
            return
        
        logger.info("開始初始化環境管理器...")
        
        # 創建默認環境
        if default_config:
            await self.create_environment("default", default_config)
            self._default_env_id = "default"
        
        self._initialized = True
        logger.info("環境管理器初始化完成")
    
    async def create_environment(
        self, 
        env_id: str, 
        config: Dict[str, Any],
        auto_create: bool = True
    ) -> bool:
        """創建環境
        
        Args:
            env_id: 環境ID
            config: 環境配置
            auto_create: 是否自動創建環境實例
            
        Returns:
            bool: 是否成功
        """
        try:
            # 解析配置
            env_config = EnvironmentConfig(
                env_type=EnvironmentType(config.get('env_type', 'gymnasium')),
                env_name=config.get('env_name', 'LEOSatelliteHandoverEnv-v1'),
                parameters=config.get('parameters', {}),
                max_episode_steps=config.get('max_episode_steps', 1000),
                reward_config=config.get('reward_config'),
                observation_config=config.get('observation_config'),
                action_config=config.get('action_config')
            )
            
            # 創建環境橋接器
            if env_config.env_type == EnvironmentType.GYMNASIUM:
                env_bridge = GymnasiumEnvironmentBridge(env_config.env_name, env_config.parameters)
                
                if auto_create:
                    await env_bridge.create_env()
                
                self._environments[env_id] = env_bridge
                self._environment_configs[env_id] = env_config
                
                # 記錄環境信息
                self._environment_info[env_id] = EnvironmentInfo(
                    env_id=env_id,
                    env_type=env_config.env_type,
                    env_name=env_config.env_name,
                    status=EnvironmentStatus.READY,
                    observation_space=env_bridge.get_observation_space(),
                    action_space=env_bridge.get_action_space(),
                    created_at=datetime.now()
                )
                
                logger.info(f"環境 '{env_id}' 創建成功")
                return True
            
            else:
                logger.error(f"不支持的環境類型: {env_config.env_type}")
                return False
                
        except Exception as e:
            logger.error(f"創建環境 '{env_id}' 失敗: {e}")
            return False
    
    def get_environment(self, env_id: Optional[str] = None) -> Optional[GymnasiumEnvironmentBridge]:
        """獲取環境
        
        Args:
            env_id: 環境ID，如果為 None 則返回默認環境
            
        Returns:
            GymnasiumEnvironmentBridge: 環境橋接器
        """
        if env_id is None:
            env_id = self._default_env_id
        
        if env_id is None:
            logger.error("沒有可用的環境")
            return None
        
        if env_id not in self._environments:
            logger.error(f"環境 '{env_id}' 不存在")
            return None
        
        # 更新使用時間
        if env_id in self._environment_info:
            self._environment_info[env_id].last_used = datetime.now()
        
        return self._environments[env_id]
    
    def list_environments(self) -> List[EnvironmentInfo]:
        """列出所有環境
        
        Returns:
            List[EnvironmentInfo]: 環境信息列表
        """
        return list(self._environment_info.values())
    
    async def remove_environment(self, env_id: str) -> bool:
        """移除環境
        
        Args:
            env_id: 環境ID
            
        Returns:
            bool: 是否成功
        """
        if env_id not in self._environments:
            logger.warning(f"環境 '{env_id}' 不存在")
            return False
        
        try:
            # 關閉環境
            self._environments[env_id].close()
            
            # 清理記錄
            del self._environments[env_id]
            del self._environment_configs[env_id]
            del self._environment_info[env_id]
            
            # 更新默認環境
            if self._default_env_id == env_id:
                self._default_env_id = None
                if self._environments:
                    self._default_env_id = next(iter(self._environments.keys()))
            
            logger.info(f"環境 '{env_id}' 移除成功")
            return True
            
        except Exception as e:
            logger.error(f"移除環境 '{env_id}' 失敗: {e}")
            return False
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """獲取環境管理器統計信息
        
        Returns:
            Dict[str, Any]: 統計信息
        """
        total_environments = len(self._environments)
        
        env_types = {}
        env_statuses = {}
        for info in self._environment_info.values():
            env_type = info.env_type.value
            env_status = info.status.value
            env_types[env_type] = env_types.get(env_type, 0) + 1
            env_statuses[env_status] = env_statuses.get(env_status, 0) + 1
        
        return {
            'total_environments': total_environments,
            'default_environment': self._default_env_id,
            'environment_types': env_types,
            'environment_statuses': env_statuses,
            'gymnasium_available': GYMNASIUM_AVAILABLE,
            'initialized': self._initialized
        }
    
    async def cleanup(self) -> None:
        """清理資源"""
        logger.info("開始清理環境管理器...")
        
        for env_id in list(self._environments.keys()):
            await self.remove_environment(env_id)
        
        self._initialized = False
        logger.info("環境管理器清理完成")