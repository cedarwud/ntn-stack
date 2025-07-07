"""
Gymnasium 橋接模組 - 從 environment_manager.py 中提取的橋接邏輯
保持環境創建和管理邏輯，分離環境類型處理
"""

import logging
from typing import Dict, Any, Optional, Union, Tuple
import numpy as np

from .data_converters import EnvironmentDataConverter
from ..interfaces import HandoverContext, HandoverDecision

logger = logging.getLogger(__name__)

# 嘗試導入 Gymnasium，處理可選依賴
GYMNASIUM_AVAILABLE = False
try:
    import gymnasium as gym
    import gymnasium.spaces as spaces
    GYMNASIUM_AVAILABLE = True
    logger.info("Gymnasium 可用")
except ImportError:
    logger.warning("Gymnasium 不可用，部分功能受限")


class GymnasiumEnvironmentBridge:
    """Gymnasium 環境橋接器
    
    提供與 Gymnasium 環境的橋接，處理環境創建、觀察轉換和動作映射
    """
    
    def __init__(self, env_name: str, config: Dict[str, Any]):
        """初始化橋接器
        
        Args:
            env_name: 環境名稱
            config: 環境配置
        """
        self.env_name = env_name
        self.config = config
        self.env = None
        self._current_obs = None
        self._current_info = None
        self._episode_count = 0
        self._total_steps = 0
        
        # 初始化數據轉換器
        self.data_converter = EnvironmentDataConverter(config)
    
    async def create_env(self) -> bool:
        """創建 Gymnasium 環境
        
        Returns:
            bool: 是否創建成功
        """
        if not GYMNASIUM_AVAILABLE:
            logger.error("Gymnasium 不可用，無法創建環境")
            return False
        
        try:
            # 使用 gymnasium.make 創建環境
            self.env = gym.make(self.env_name, **self.config)
            logger.info(f"成功創建 Gymnasium 環境: {self.env_name}")
            return True
        except Exception as e:
            logger.error(f"創建 Gymnasium 環境失敗: {e}")
            return False
    
    def obs_to_context(self, obs: np.ndarray, info: Dict[str, Any]) -> HandoverContext:
        """將環境觀察轉換為 HandoverContext
        
        委派給數據轉換器處理
        """
        return self.data_converter.obs_to_context(obs, info)
    
    def decision_to_action(self, decision: HandoverDecision) -> Union[int, np.ndarray]:
        """將 HandoverDecision 轉換為環境動作
        
        委派給數據轉換器處理
        """
        action_space = getattr(self.env, 'action_space', None) if self.env else None
        return self.data_converter.decision_to_action(decision, action_space)
    
    async def reset(self) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """重置環境
        
        Returns:
            Tuple: (觀察, 信息)
        """
        if not self.env:
            logger.error("環境未創建，無法重置")
            return None, {}
        
        try:
            obs, info = self.env.reset()
            self._current_obs = obs
            self._current_info = info
            self._episode_count += 1
            return obs, info
        except Exception as e:
            logger.error(f"環境重置失敗: {e}")
            return None, {}
    
    async def step(self, action) -> Tuple[Optional[np.ndarray], float, bool, bool, Dict[str, Any]]:
        """執行一步
        
        Args:
            action: 動作
            
        Returns:
            Tuple: (觀察, 獎勵, 終止, 截斷, 信息)
        """
        if not self.env:
            logger.error("環境未創建，無法執行步驟")
            return None, 0.0, True, True, {}
        
        try:
            obs, reward, terminated, truncated, info = self.env.step(action)
            self._current_obs = obs
            self._current_info = info
            self._total_steps += 1
            return obs, reward, terminated, truncated, info
        except Exception as e:
            logger.error(f"環境步驟執行失敗: {e}")
            return None, 0.0, True, True, {}
    
    def get_observation_space(self):
        """獲取觀察空間"""
        return getattr(self.env, 'observation_space', None) if self.env else None
    
    def get_action_space(self):
        """獲取動作空間"""
        return getattr(self.env, 'action_space', None) if self.env else None
    
    def close(self):
        """關閉環境"""
        if self.env:
            try:
                self.env.close()
            except Exception as e:
                logger.error(f"關閉環境失敗: {e}")
            finally:
                self.env = None
    
    # === 環境信息獲取方法 ===
    
    def get_current_observation(self) -> Optional[np.ndarray]:
        """獲取當前觀察"""
        return self._current_obs
    
    def get_current_info(self) -> Dict[str, Any]:
        """獲取當前信息"""
        return self._current_info or {}
    
    def get_episode_count(self) -> int:
        """獲取回合數"""
        return self._episode_count
    
    def get_total_steps(self) -> int:
        """獲取總步數"""
        return self._total_steps
    
    def is_available(self) -> bool:
        """檢查環境是否可用"""
        return self.env is not None
    
    def get_env_info(self) -> Dict[str, Any]:
        """獲取環境信息"""
        if not self.env:
            return {"available": False}
        
        info = {
            "available": True,
            "env_name": self.env_name,
            "episode_count": self._episode_count,
            "total_steps": self._total_steps,
            "config": self.config
        }
        
        # 添加空間信息
        obs_space = self.get_observation_space()
        action_space = self.get_action_space()
        
        if obs_space:
            info["observation_space"] = str(obs_space)
        if action_space:
            info["action_space"] = str(action_space)
        
        return info
    
    # === 環境驗證方法 ===
    
    def validate_environment(self) -> Dict[str, Any]:
        """驗證環境配置和狀態
        
        Returns:
            Dict: 驗證結果
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 檢查 Gymnasium 可用性
        if not GYMNASIUM_AVAILABLE:
            validation_result["valid"] = False
            validation_result["errors"].append("Gymnasium 未安裝或不可用")
        
        # 檢查環境是否創建
        if not self.env:
            validation_result["valid"] = False
            validation_result["errors"].append("環境未創建")
        
        # 檢查配置
        if not self.config:
            validation_result["warnings"].append("環境配置為空")
        
        # 檢查環境名稱
        if not self.env_name:
            validation_result["valid"] = False
            validation_result["errors"].append("環境名稱未指定")
        
        return validation_result