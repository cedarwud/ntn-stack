"""
環境註冊模組

將自定義環境註冊到 Gymnasium 中，使其可以通過 gym.make() 創建
"""

import logging
from gymnasium.envs.registration import register
from .leo_satellite_environment import LEOSatelliteEnvironment

logger = logging.getLogger(__name__)


def register_custom_environments():
    """
    註冊所有自定義環境到 Gymnasium
    """
    try:
        # 註冊 LEO 衛星換手環境
        register(
            id='LEOSatelliteHandoverEnv-v1',
            entry_point='netstack_api.services.rl_training.environments.leo_satellite_environment:LEOSatelliteEnvironment',
            max_episode_steps=500,
            kwargs={
                'simworld_url': 'http://localhost:8888',
                'max_satellites': 6,
                'scenario': 'urban',
                'min_elevation': 10.0,
                'fallback_enabled': True
            }
        )
        
        logger.info("成功註冊 LEOSatelliteHandoverEnv-v1")
        
        # 可以在這裡註冊更多環境
        # register(
        #     id='SatelliteConstellationEnv-v1',
        #     entry_point='...',
        #     ...
        # )
        
        return True
        
    except Exception as e:
        logger.error(f"環境註冊失敗: {e}")
        return False


def get_available_environments():
    """
    獲取可用的自定義環境列表
    
    Returns:
        Dict: 環境資訊字典
    """
    return {
        'LEOSatelliteHandoverEnv-v1': {
            'description': 'LEO 衛星換手決策環境',
            'algorithm_support': ['DQN', 'PPO', 'SAC'],
            'observation_space': 'Box(36,)',  # 6 satellites * 6 features
            'action_space': 'Discrete(6)',    # 選擇 6 個候選衛星之一
            'max_episode_steps': 500,
            'features': [
                '真實 TLE 軌道數據',
                '信號傳播模型',
                'SimWorld API 整合',
                'Fallback 機制'
            ]
        }
    }