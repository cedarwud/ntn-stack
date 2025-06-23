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
        
        # 創建新的 Box 動作空間
        total_dim = sum(space.shape[0] if hasattr(space, 'shape') and space.shape else 1 
                       for space in self.original_action_space.spaces.values())
        
        self.action_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(total_dim,),
            dtype=np.float32
        )
        
        logger.info(f"Wrapped action space: {self.original_action_space} -> {self.action_space}")
    
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
                dim = space.shape[0] if space.shape else 1
                mapping[key] = {
                    'type': 'box',
                    'indices': list(range(current_idx, current_idx + dim)),
                    'low': space.low,
                    'high': space.high,
                    'shape': space.shape
                }
                current_idx += dim
            else:
                raise ValueError(f"Unsupported action space type: {type(space)}")
        
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
                
                if isinstance(low, np.ndarray) and isinstance(high, np.ndarray):
                    scaled_values = low + raw_values * (high - low)
                else:
                    scaled_values = low + raw_values * (high - low)
                
                if mapping['shape']:
                    dict_action[key] = scaled_values.reshape(mapping['shape'])
                else:
                    dict_action[key] = scaled_values[0]
        
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


class CompatibleLEOHandoverEnv(gym.Wrapper):
    """
    LEO 切換環境兼容性包裝器
    
    提供與所有 RL 算法兼容的統一接口
    """
    
    def __init__(self, env, force_box_action=True):
        """
        初始化兼容性包裝器
        
        Args:
            env: 原始環境
            force_box_action: 是否強制使用 Box 動作空間
        """
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
        else:
            self._use_dict_mapping = False
    
    def step(self, action):
        """執行動作步驟"""
        if self._use_dict_mapping:
            # 將 Box 動作轉換為 Dict 動作
            action = self._box_to_dict_action(action)
        
        return self.env.step(action)
    
    def _box_to_dict_action(self, box_action):
        """將 Box 動作轉換為 Dict 動作"""
        if not isinstance(box_action, np.ndarray):
            box_action = np.array(box_action, dtype=np.float32)
        
        # 確保動作在 [0, 1] 範圍內
        box_action = np.clip(box_action, 0.0, 1.0)
        
        # 獲取最大衛星數量（處理嵌套包裝器）
        max_satellites = self._get_max_satellites()
        
        # 映射到原始動作空間
        dict_action = {
            "handover_decision": int(box_action[0] * 3),  # 0, 1, 2
            "target_satellite": int(box_action[1] * max_satellites),
            "timing": np.array([box_action[2] * 10.0], dtype=np.float32),  # 0-10 秒
            "power_control": np.array([box_action[3]], dtype=np.float32),  # 0-1
            "priority": np.array([box_action[4]], dtype=np.float32)  # 0-1
        }
        
        # 確保值在有效範圍內
        dict_action["handover_decision"] = np.clip(dict_action["handover_decision"], 0, 2)
        dict_action["target_satellite"] = np.clip(dict_action["target_satellite"], 0, max_satellites - 1)
        
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