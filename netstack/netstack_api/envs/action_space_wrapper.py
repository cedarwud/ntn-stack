"""
動作空間包裝器

將 Dict 動作空間轉換為 Box 動作空間，使其與 stable-baselines3 兼容
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import Dict, Any, Union
import logging

logger = logging.getLogger(__name__)


class DictToBoxActionWrapper(gym.ActionWrapper):
    """
    將 Dict 動作空間轉換為 Box 動作空間的包裝器
    
    將原始環境的 Dict 動作空間扁平化為連續的 Box 空間，
    在執行動作時再將其轉換回 Dict 格式
    """
    
    def __init__(self, env):
        super().__init__(env)
        
        if not isinstance(env.action_space, spaces.Dict):
            raise ValueError("This wrapper only works with Dict action spaces")
        
        self.original_action_space = env.action_space
        self.action_mapping = self._create_action_mapping()
        
        # 計算正確的總維度
        total_dim = 0
        for key, space in self.original_action_space.spaces.items():
            if isinstance(space, spaces.Discrete):
                total_dim += 1  # Discrete 空間用 1 維表示
            elif isinstance(space, spaces.Box):
                total_dim += np.prod(space.shape)  # Box 空間用所有維度
            else:
                total_dim += 1  # 其他類型默認 1 維
        
        # 創建新的 Box 動作空間
        self.action_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(total_dim,),
            dtype=np.float32
        )
        
        logger.info(f"Wrapped action space: {self.original_action_space} -> {self.action_space}")
        logger.info(f"Action mapping: {self.action_mapping}")
    
    def _create_action_mapping(self):
        """創建動作空間映射"""
        mapping = {}
        current_idx = 0
        
        for key, space in self.original_action_space.spaces.items():
            if isinstance(space, spaces.Discrete):
                mapping[key] = {
                    'type': 'discrete',
                    'indices': [current_idx],
                    'n': space.n,
                    'low': 0,
                    'high': space.n - 1
                }
                current_idx += 1
            elif isinstance(space, spaces.Box):
                dim = np.prod(space.shape) if space.shape else 1
                mapping[key] = {
                    'type': 'box',
                    'indices': list(range(current_idx, current_idx + dim)),
                    'low': space.low.flatten() if hasattr(space.low, 'flatten') else space.low,
                    'high': space.high.flatten() if hasattr(space.high, 'flatten') else space.high,
                    'shape': space.shape,
                    'original_shape': space.shape
                }
                current_idx += dim
            else:
                # 為其他類型提供默認處理
                mapping[key] = {
                    'type': 'unknown',
                    'indices': [current_idx],
                    'low': 0,
                    'high': 1
                }
                current_idx += 1
                logger.warning(f"Unknown action space type for {key}: {type(space)}")
        
        return mapping
    
    def action(self, action):
        """將 Box 動作轉換為 Dict 動作"""
        if not isinstance(action, np.ndarray):
            action = np.array(action, dtype=np.float32)
        
        # 確保動作在 [0, 1] 範圍內
        action = np.clip(action, 0.0, 1.0)
        
        dict_action = {}
        
        for key, mapping in self.action_mapping.items():
            indices = mapping['indices']
            
            if mapping['type'] == 'discrete':
                # 將 [0, 1] 映射到離散值
                raw_value = action[indices[0]]
                discrete_value = int(raw_value * mapping['n'])
                discrete_value = np.clip(discrete_value, 0, mapping['n'] - 1)
                dict_action[key] = discrete_value
                
            elif mapping['type'] == 'box':
                # 將 [0, 1] 映射到 Box 範圍
                raw_values = action[indices]
                low = mapping['low']
                high = mapping['high']
                
                # 處理標量和數組情況
                if isinstance(low, np.ndarray) and isinstance(high, np.ndarray):
                    if len(low) == len(raw_values):
                        scaled_values = low + raw_values * (high - low)
                    else:
                        # 廣播處理
                        scaled_values = low[0] + raw_values * (high[0] - low[0])
                else:
                    scaled_values = low + raw_values * (high - low)
                
                # 重塑為原始形狀
                if mapping['original_shape'] and len(mapping['original_shape']) > 0:
                    try:
                        dict_action[key] = scaled_values.reshape(mapping['original_shape']).astype(np.float32)
                    except ValueError:
                        # 如果重塑失敗，使用第一個值
                        dict_action[key] = np.array([scaled_values[0]] * np.prod(mapping['original_shape'])).reshape(mapping['original_shape']).astype(np.float32)
                else:
                    dict_action[key] = scaled_values[0] if len(scaled_values) == 1 else scaled_values.astype(np.float32)
                    
            elif mapping['type'] == 'unknown':
                # 未知類型的默認處理
                dict_action[key] = action[indices[0]]
        
        return dict_action


class BoxToBoxActionWrapper(gym.ActionWrapper):
    """
    Box 動作空間正規化包裝器
    
    確保動作值在合理範圍內，並提供更好的數值穩定性
    """
    
    def __init__(self, env):
        super().__init__(env)
        
        if not isinstance(env.action_space, spaces.Box):
            raise ValueError("This wrapper only works with Box action spaces")
    
    def action(self, action):
        """正規化動作"""
        if not isinstance(action, np.ndarray):
            action = np.array(action, dtype=np.float32)
        
        # 裁剪到動作空間範圍
        action = np.clip(action, self.action_space.low, self.action_space.high)
        
        return action


def wrap_action_space(env):
    """
    自動包裝動作空間以兼容 stable-baselines3
    
    Args:
        env: 原始環境
        
    Returns:
        包裝後的環境
    """
    if isinstance(env.action_space, spaces.Dict):
        logger.info("Wrapping Dict action space to Box")
        env = DictToBoxActionWrapper(env)
    elif isinstance(env.action_space, spaces.Box):
        logger.info("Applying Box action space normalization")
        env = BoxToBoxActionWrapper(env)
    
    return env


class ObservationNormalizationWrapper(gym.ObservationWrapper):
    """
    觀測空間正規化包裝器
    
    確保觀測向量維度一致並進行正規化
    """
    
    def __init__(self, env, target_obs_dim=72):
        super().__init__(env)
        
        self.target_obs_dim = target_obs_dim
        self.original_obs_space = env.observation_space
        
        # 創建標準化的觀測空間
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(target_obs_dim,),
            dtype=np.float32
        )
        
        logger.info(f"Normalized observation space: {self.original_obs_space} -> {self.observation_space}")
    
    def observation(self, observation):
        """正規化觀測"""
        if not isinstance(observation, np.ndarray):
            observation = np.array(observation, dtype=np.float32)
        
        # 如果觀測維度不匹配，進行調整
        if observation.shape[0] != self.target_obs_dim:
            if observation.shape[0] > self.target_obs_dim:
                # 截斷多餘的維度
                observation = observation[:self.target_obs_dim]
            else:
                # 填充不足的維度
                padding = np.zeros(self.target_obs_dim - observation.shape[0], dtype=np.float32)
                observation = np.concatenate([observation, padding])
        
        # 確保數值穩定性
        observation = np.nan_to_num(observation, nan=0.0, posinf=1.0, neginf=-1.0)
        
        return observation.astype(np.float32)


class CompatibleLEOHandoverEnv(gym.Wrapper):
    """
    LEO 切換環境兼容性包裝器
    
    提供與所有 RL 算法兼容的統一接口
    """
    
    def __init__(self, env, force_box_action=True, target_obs_dim=72):
        """
        初始化兼容性包裝器
        
        Args:
            env: 原始環境
            force_box_action: 是否強制使用 Box 動作空間
            target_obs_dim: 目標觀測維度
        """
        # 首先應用觀測空間正規化
        env = ObservationNormalizationWrapper(env, target_obs_dim)
        
        super().__init__(env)
        
        if force_box_action and isinstance(env.action_space, spaces.Dict):
            # 使用簡化的 Box 動作空間
            self.action_space = spaces.Box(
                low=0.0,
                high=1.0,
                shape=(5,),  # [handover_decision, target_satellite, timing, power, priority]
                dtype=np.float32
            )
            self._use_dict_mapping = True
            self._original_action_space = env.action_space
        else:
            self._use_dict_mapping = False
    
    def step(self, action):
        """執行動作步驟"""
        if self._use_dict_mapping:
            # 將 Box 動作轉換為 Dict 動作
            action = self._box_to_dict_action(action)
        
        return self.env.step(action)
    
    def _box_to_dict_action(self, action):
        """將 Box 動作轉換為 Dict 動作"""
        if not isinstance(action, np.ndarray):
            action = np.array(action, dtype=np.float32)
        
        # 確保動作在 [0, 1] 範圍內
        action = np.clip(action, 0.0, 1.0)
        
        # 基於原始動作空間結構創建 Dict 動作
        dict_action = {}
        
        # 獲取原始動作空間的鍵
        original_keys = list(self._original_action_space.spaces.keys())
        
        for i, key in enumerate(original_keys):
            if i < len(action):
                original_space = self._original_action_space.spaces[key]
                
                if isinstance(original_space, spaces.Discrete):
                    # 離散動作：將 [0,1] 映射到 [0, n-1]
                    discrete_value = int(action[i] * original_space.n)
                    dict_action[key] = np.clip(discrete_value, 0, original_space.n - 1)
                    
                elif isinstance(original_space, spaces.Box):
                    # 連續動作：將 [0,1] 映射到 [low, high]
                    low = original_space.low
                    high = original_space.high
                    
                    if original_space.shape == ():
                        # 標量
                        scaled_value = low + action[i] * (high - low)
                        dict_action[key] = np.array([scaled_value], dtype=np.float32)
                    else:
                        # 數組 - 使用第一個值
                        if hasattr(low, '__len__') and hasattr(high, '__len__'):
                            scaled_value = low[0] + action[i] * (high[0] - low[0])
                        else:
                            scaled_value = low + action[i] * (high - low)
                        
                        dict_action[key] = np.full(original_space.shape, scaled_value, dtype=np.float32)
                else:
                    # 其他類型，直接使用原始值
                    dict_action[key] = action[i]
            else:
                # 如果動作維度不足，使用默認值
                original_space = self._original_action_space.spaces[key]
                if isinstance(original_space, spaces.Discrete):
                    dict_action[key] = 0
                elif isinstance(original_space, spaces.Box):
                    if original_space.shape == ():
                        dict_action[key] = np.array([original_space.low], dtype=np.float32)
                    else:
                        dict_action[key] = np.full(original_space.shape, original_space.low, dtype=np.float32)
                else:
                    dict_action[key] = 0.0
        
        return dict_action
    
    def _get_max_satellites(self):
        """獲取最大衛星數量（處理嵌套包裝器）"""
        env = self.env
        while hasattr(env, 'env'):
            if hasattr(env, 'max_satellites'):
                return env.max_satellites
            env = env.env
        
        # 如果找不到，使用默認值
        if hasattr(env, 'max_satellites'):
            return env.max_satellites
        else:
            return 50  # 默認值