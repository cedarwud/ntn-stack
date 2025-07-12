"""
🧠 算法工廠模式實現

基於工廠模式的算法創建和管理，支援：
- 動態算法註冊
- 插件化架構
- 配置驅動實例化
- 生命週期管理
"""

import logging
from typing import Dict, Type, Any
from ..interfaces.rl_algorithm import IRLAlgorithm
from ..algorithms.dqn_algorithm import DQNAlgorithm
from ..algorithms.ppo_algorithm import PPOAlgorithm
from ..algorithms.sac_algorithm import SACAlgorithm

# 演算法外掛程式註冊表
# 將演算法名稱映射到其對應的類別
algorithm_plugin: Dict[str, Type[IRLAlgorithm]] = {
    "dqn": DQNAlgorithm,
    "ppo": PPOAlgorithm,
    "sac": SACAlgorithm,
}


def get_algorithm(name: str, env_name: str, config: Dict[str, Any]) -> IRLAlgorithm:
    """
    演算法工廠函數。根據名稱獲取並初始化一個演算法實例。
    """
    algorithm_class = algorithm_plugin.get(name)
    if not algorithm_class:
        raise ValueError(f"未知的演算法: {name}")
    return algorithm_class(env_name=env_name, config=config)
