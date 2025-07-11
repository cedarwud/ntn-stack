import gymnasium as gym
from typing import Dict, Any
import random
import time

from ..interfaces.rl_algorithm import IRLAlgorithm


class DQNAlgorithm(IRLAlgorithm):
    """
    一個DQN演算法的簡單模擬實作。
    它並不進行真正的神經網路訓練，而是模擬一個訓練過程，
    以便我們可以專注於打通整個系統的前後端和 API 流程。
    """

    def __init__(self, env_name: str, config: Dict[str, Any]):
        """
        初始化DQN演算法模擬器

        Args:
            env_name (str): 要使用的gymnasium環境名稱。
            config (Dict[str, Any]): 演算法的超參數。
        """
        self.env_name = env_name
        self.config = config
        self.is_training = False
        self._current_episode = 0
        self._total_episodes = config.get("total_episodes", 100)
        self._last_reward = 0.0
        self._average_reward = 0.0
        self._loss = 1.0  # Initial loss

        # 嘗試初始化環境以確保其存在
        try:
            self.env = gym.make(env_name)
        except Exception as e:
            # 在實際應用中，這裡應該有更健壯的錯誤處理
            print(f"無法建立環境 '{env_name}': {e}")
            raise

    def train(self) -> None:
        """
        模擬一個訓練循環。
        在真實的實現中，這裡會是與環境互動、更新網路權重等複雜邏輯。
        """
        if not self.is_training:
            self.is_training = True
            self._current_episode = 0

        if self._current_episode < self._total_episodes:
            # 模擬一個 step 的耗時
            time.sleep(self.config.get("step_time", 0.5))

            self._current_episode += 1
            # 模擬獎勵和損失的變化
            self._last_reward = random.uniform(-10, 10)
            self._average_reward = (
                self._average_reward * (self._current_episode - 1) + self._last_reward
            ) / self._current_episode
            self._loss *= 0.95  # 模擬損失下降
        else:
            self.is_training = False

    def get_status(self) -> Dict[str, Any]:
        """
        獲取目前訓練狀態
        """
        return {
            "is_training": self.is_training,
            "algorithm": "DQN",
            "environment": self.env_name,
            "episode": self._current_episode,
            "total_episodes": self._total_episodes,
            "last_reward": self._last_reward,
            "average_reward": self._average_reward,
            "loss": self._loss,
            "progress": (
                (self._current_episode / self._total_episodes) * 100
                if self._total_episodes > 0
                else 0
            ),
        }

    def stop_training(self) -> None:
        """
        停止訓練過程
        """
        self.is_training = False
