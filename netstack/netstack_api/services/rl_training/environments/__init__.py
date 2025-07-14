"""
RL Training Environments

提供用於 RL 訓練的各種環境實現
"""

from .leo_satellite_environment import LEOSatelliteEnvironment
from .registry import register_custom_environments, get_available_environments

# 自動註冊環境
register_custom_environments()

__all__ = [
    "LEOSatelliteEnvironment", 
    "register_custom_environments", 
    "get_available_environments"
]