"""
🤖 強化學習算法模組

實現各種強化學習換手算法，包括 DQN、PPO、SAC 等。
"""

from .base_rl_algorithm import BaseRLHandoverAlgorithm

# 嘗試導入具體的 RL 算法，允許優雅降級
try:
    from .dqn_agent import DQNHandoverAgent
    DQN_AVAILABLE = True
except ImportError as e:
    DQN_AVAILABLE = False
    print(f"警告：DQN 算法導入失敗: {e}")

try:
    from .ppo_agent import PPOHandoverAgent
    PPO_AVAILABLE = True
except ImportError as e:
    PPO_AVAILABLE = False
    print(f"警告：PPO 算法導入失敗: {e}")

try:
    from .sac_agent import SACHandoverAgent
    SAC_AVAILABLE = True
except ImportError as e:
    SAC_AVAILABLE = False
    print(f"警告：SAC 算法導入失敗: {e}")

# 動態構建 __all__ 列表
__all__ = ["BaseRLHandoverAlgorithm"]

if DQN_AVAILABLE:
    __all__.append("DQNHandoverAgent")
if PPO_AVAILABLE:
    __all__.append("PPOHandoverAgent")
if SAC_AVAILABLE:
    __all__.append("SACHandoverAgent")