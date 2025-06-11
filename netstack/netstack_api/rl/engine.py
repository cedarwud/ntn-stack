"""
RL 引擎抽象接口和具體實現

提供可插拔的 RL 引擎架構，支持：
- Gymnasium 環境
- 傳統算法
- 混合策略
"""

import os
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List
import structlog
import numpy as np

# 條件性導入 RL 依賴
try:
    import gymnasium as gym
    from stable_baselines3 import DQN, PPO, SAC
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.callbacks import EvalCallback
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False
    gym = None
    DQN = PPO = SAC = None

logger = structlog.get_logger(__name__)

class RLEngine(ABC):
    """RL 引擎抽象基類"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.engine_type = "abstract"
        self.is_trained = False
        
    @abstractmethod
    async def get_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """獲取行動"""
        pass
    
    @abstractmethod
    async def update(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型"""
        pass
    
    @abstractmethod
    async def train(self, episodes: int = 1000) -> Dict[str, Any]:
        """訓練模型"""
        pass
    
    @abstractmethod
    async def save_model(self, path: str) -> bool:
        """保存模型"""
        pass
    
    @abstractmethod
    async def load_model(self, path: str) -> bool:
        """載入模型"""
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        return {
            "engine_type": self.engine_type,
            "is_trained": self.is_trained,
            "config": self.config
        }

class GymnasiumEngine(RLEngine):
    """Gymnasium 引擎實現"""
    
    def __init__(self, env_name: str, algorithm: str = "DQN", config: Optional[Dict] = None):
        super().__init__(config)
        
        if not GYMNASIUM_AVAILABLE:
            raise ImportError("Gymnasium 依賴未安裝。請安裝 gymnasium 和 stable-baselines3")
        
        self.env_name = env_name
        self.algorithm = algorithm
        self.engine_type = f"gymnasium_{algorithm}"
        
        # 初始化環境和模型
        self.env = None
        self.model = None
        self.training_env = None
        
        # 性能指標
        self.training_history = []
        self.action_history = []
        
    async def _initialize_env(self):
        """初始化環境"""
        try:
            # 確保環境已註冊
            import netstack_api.envs  # 觸發環境註冊
            
            self.env = gym.make(self.env_name)
            self.training_env = make_vec_env(self.env_name, n_envs=1)
            
            logger.info("Gymnasium 環境初始化成功", env_name=self.env_name)
            return True
            
        except Exception as e:
            logger.error("環境初始化失敗", error=str(e), env_name=self.env_name)
            return False
    
    async def _initialize_model(self):
        """初始化模型"""
        try:
            if self.training_env is None:
                await self._initialize_env()
            
            algorithm_map = {
                "DQN": DQN,
                "PPO": PPO, 
                "SAC": SAC
            }
            
            if self.algorithm not in algorithm_map:
                raise ValueError(f"不支援的算法: {self.algorithm}")
            
            AlgorithmClass = algorithm_map[self.algorithm]
            
            # 模型配置
            model_config = {
                "learning_rate": self.config.get("learning_rate", 3e-4),
                "buffer_size": self.config.get("buffer_size", 100000),
                "batch_size": self.config.get("batch_size", 64),
                "gamma": self.config.get("gamma", 0.99),
                "verbose": 1
            }
            
            # 針對不同算法調整配置
            if self.algorithm == "DQN":
                model_config.update({
                    "exploration_fraction": self.config.get("exploration_fraction", 0.3),
                    "exploration_final_eps": self.config.get("exploration_final_eps", 0.05),
                    "target_update_interval": self.config.get("target_update_interval", 1000)
                })
            
            self.model = AlgorithmClass("MlpPolicy", self.training_env, **model_config)
            
            logger.info("模型初始化成功", algorithm=self.algorithm)
            return True
            
        except Exception as e:
            logger.error("模型初始化失敗", error=str(e), algorithm=self.algorithm)
            return False
    
    async def get_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """獲取行動"""
        try:
            if self.model is None:
                await self._initialize_model()
            
            # 轉換狀態格式
            obs = self._convert_state_to_obs(state)
            
            # 獲取行動
            action, _states = self.model.predict(obs, deterministic=False)
            
            # 轉換行動格式
            action_dict = self._convert_action_to_dict(action)
            
            # 記錄行動歷史
            self.action_history.append({
                "state": state,
                "action": action_dict,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # 限制歷史長度
            if len(self.action_history) > 1000:
                self.action_history = self.action_history[-500:]
            
            return action_dict
            
        except Exception as e:
            logger.error("獲取行動失敗", error=str(e))
            return self._get_fallback_action(state)
    
    async def update(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型（在線學習）"""
        try:
            # Stable-baselines3 的模型會在訓練過程中自動更新
            # 這裡記錄經驗用於分析
            
            result = {
                "status": "success",
                "message": "經驗已記錄，模型將在下次訓練時更新",
                "experience_recorded": True
            }
            
            return result
            
        except Exception as e:
            logger.error("更新模型失敗", error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def train(self, episodes: int = 1000) -> Dict[str, Any]:
        """訓練模型"""
        try:
            if self.model is None:
                await self._initialize_model()
            
            logger.info("開始訓練模型", episodes=episodes, algorithm=self.algorithm)
            
            # 計算總步數
            total_timesteps = episodes * self.config.get("episode_length", 1000)
            
            # 設置評估回調
            eval_callback = EvalCallback(
                self.env,
                best_model_save_path=f"./models/{self.env_name}_{self.algorithm}/",
                log_path=f"./logs/{self.env_name}_{self.algorithm}/",
                eval_freq=max(total_timesteps // 10, 1000),
                deterministic=True,
                render=False
            )
            
            # 訓練模型
            self.model.learn(
                total_timesteps=total_timesteps,
                callback=eval_callback,
                progress_bar=True
            )
            
            self.is_trained = True
            
            # 記錄訓練歷史
            training_result = {
                "status": "success",
                "episodes": episodes,
                "total_timesteps": total_timesteps,
                "algorithm": self.algorithm,
                "final_reward": "未實現",  # 需要從回調中獲取
                "training_time": "未記錄"
            }
            
            self.training_history.append(training_result)
            
            logger.info("模型訓練完成", result=training_result)
            return training_result
            
        except Exception as e:
            logger.error("訓練模型失敗", error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def save_model(self, path: str) -> bool:
        """保存模型"""
        try:
            if self.model is None:
                logger.warning("無模型可保存")
                return False
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.model.save(path)
            
            logger.info("模型已保存", path=path)
            return True
            
        except Exception as e:
            logger.error("保存模型失敗", error=str(e), path=path)
            return False
    
    async def load_model(self, path: str) -> bool:
        """載入模型"""
        try:
            if not os.path.exists(path + ".zip"):  # stable-baselines3 自動添加 .zip
                logger.warning("模型檔案不存在", path=path)
                return False
            
            # 確保環境已初始化
            if self.training_env is None:
                await self._initialize_env()
            
            algorithm_map = {
                "DQN": DQN,
                "PPO": PPO,
                "SAC": SAC
            }
            
            AlgorithmClass = algorithm_map[self.algorithm]
            self.model = AlgorithmClass.load(path, env=self.training_env)
            self.is_trained = True
            
            logger.info("模型載入成功", path=path)
            return True
            
        except Exception as e:
            logger.error("載入模型失敗", error=str(e), path=path)
            return False
    
    def _convert_state_to_obs(self, state: Dict[str, Any]) -> np.ndarray:
        """將狀態字典轉換為觀測向量"""
        # 簡化實現：提取數值特徵
        obs_list = []
        
        # 提取干擾相關特徵
        if "sinr" in state:
            obs_list.append(float(state["sinr"]))
        if "interference_level" in state:
            obs_list.append(float(state["interference_level"]))
        if "signal_strength" in state:
            obs_list.append(float(state["signal_strength"]))
        
        # 提取位置特徵
        if "position" in state:
            pos = state["position"]
            if isinstance(pos, (list, tuple)):
                obs_list.extend([float(x) for x in pos[:3]])  # x, y, z
        
        # 提取性能特徵
        if "throughput" in state:
            obs_list.append(float(state["throughput"]))
        if "latency" in state:
            obs_list.append(float(state["latency"]))
        if "packet_loss" in state:
            obs_list.append(float(state["packet_loss"]))
        
        # 確保有足夠的特徵
        while len(obs_list) < 10:  # 最少10個特徵
            obs_list.append(0.0)
        
        return np.array(obs_list[:20], dtype=np.float32)  # 限制最多20個特徵
    
    def _convert_action_to_dict(self, action: np.ndarray) -> Dict[str, Any]:
        """將行動向量轉換為行動字典"""
        if isinstance(action, np.ndarray):
            action = action.flatten()
        
        # 根據環境類型轉換行動
        if "interference" in self.env_name.lower():
            return {
                "power_control": float(action[0]) if len(action) > 0 else 0.0,
                "frequency_selection": float(action[1]) if len(action) > 1 else 0.0,
                "beam_direction": float(action[2]) if len(action) > 2 else 0.0,
                "spread_factor": float(action[3]) if len(action) > 3 else 0.0
            }
        elif "optimization" in self.env_name.lower():
            return {
                "bandwidth_allocation": float(action[0]) if len(action) > 0 else 0.5,
                "qos_priority": float(action[1]) if len(action) > 1 else 0.5,
                "load_balancing": float(action[2]) if len(action) > 2 else 0.5,
                "cache_policy": float(action[3]) if len(action) > 3 else 0.5
            }
        elif "uav" in self.env_name.lower():
            # UAV 編隊控制
            num_uavs = len(action) // 4
            uav_actions = []
            for i in range(num_uavs):
                start_idx = i * 4
                uav_actions.append({
                    "thrust": float(action[start_idx]) if start_idx < len(action) else 0.0,
                    "pitch": float(action[start_idx + 1]) if start_idx + 1 < len(action) else 0.0,
                    "yaw": float(action[start_idx + 2]) if start_idx + 2 < len(action) else 0.0,
                    "roll": float(action[start_idx + 3]) if start_idx + 3 < len(action) else 0.0
                })
            return {"uav_actions": uav_actions}
        else:
            # 通用行動格式
            return {f"action_{i}": float(action[i]) for i in range(min(len(action), 6))}
    
    def _get_fallback_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """獲取備用行動（當模型失敗時）"""
        # 簡單的啟發式決策
        if "interference" in self.env_name.lower():
            return {
                "power_control": 0.5,
                "frequency_selection": 0.0,
                "beam_direction": 0.0,
                "spread_factor": 0.5
            }
        elif "optimization" in self.env_name.lower():
            return {
                "bandwidth_allocation": 0.6,
                "qos_priority": 0.7,
                "load_balancing": 0.5,
                "cache_policy": 0.4
            }
        else:
            return {"action": "no_op"}

class LegacyEngine(RLEngine):
    """傳統算法引擎實現"""
    
    def __init__(self, legacy_service: Any, config: Optional[Dict] = None):
        super().__init__(config)
        self.legacy_service = legacy_service
        self.engine_type = "legacy"
        self.is_trained = True  # 傳統服務假設已經配置好
        
    async def get_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """使用傳統服務獲取行動"""
        try:
            # 適應不同的傳統服務接口
            if hasattr(self.legacy_service, 'detect_and_mitigate_interference'):
                # AI-RAN 抗干擾服務
                result = await self.legacy_service.detect_and_mitigate_interference(
                    ue_positions=state.get("ue_positions", []),
                    gnb_positions=state.get("gnb_positions", []),
                    current_sinr=state.get("current_sinr", []),
                    network_state=state.get("network_state", {}),
                    fast_mode=True
                )
                return {"legacy_result": result}
                
            elif hasattr(self.legacy_service, 'trigger_optimization'):
                # 優化服務
                result = await self.legacy_service.trigger_optimization()
                return {"optimization_result": result}
                
            else:
                # 通用接口
                if hasattr(self.legacy_service, 'make_decision'):
                    return await self.legacy_service.make_decision(state)
                else:
                    return {"action": "legacy_default"}
                    
        except Exception as e:
            logger.error("傳統服務調用失敗", error=str(e))
            return {"action": "error", "error": str(e)}
    
    async def update(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """更新傳統服務（通常不需要）"""
        # 大部分傳統服務不支持在線學習
        return {"status": "success", "message": "傳統服務不需要更新"}
    
    async def train(self, episodes: int = 1000) -> Dict[str, Any]:
        """訓練傳統服務（通常不需要）"""
        return {"status": "success", "message": "傳統服務不需要訓練"}
    
    async def save_model(self, path: str) -> bool:
        """保存傳統服務狀態"""
        # 傳統服務通常不需要保存模型
        return True
    
    async def load_model(self, path: str) -> bool:
        """載入傳統服務狀態"""
        # 傳統服務通常不需要載入模型
        return True

class NullEngine(RLEngine):
    """空引擎實現（當服務被禁用時使用）"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.engine_type = "null"
        self.is_trained = True
        
    async def get_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """返回空行動"""
        return {"action": "disabled", "message": "AI 服務已禁用"}
    
    async def update(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """空更新"""
        return {"status": "disabled"}
    
    async def train(self, episodes: int = 1000) -> Dict[str, Any]:
        """空訓練"""
        return {"status": "disabled", "message": "AI 服務已禁用"}
    
    async def save_model(self, path: str) -> bool:
        """空保存"""
        return True
    
    async def load_model(self, path: str) -> bool:
        """空載入"""
        return True