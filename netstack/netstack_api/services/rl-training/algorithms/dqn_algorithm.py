import gymnasium as gym
from typing import Dict, Any, List
import random
import time

from ..interfaces.rl_algorithm import IRLAlgorithm, ScenarioType


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

    def get_name(self) -> str:
        """獲取算法名稱"""
        return "DQN (Deep Q-Network)"

    def get_supported_scenarios(self) -> List[ScenarioType]:
        """獲取支持的場景類型"""
        return [
            ScenarioType.URBAN,
            ScenarioType.SUBURBAN,
            ScenarioType.LOW_LATENCY,
            ScenarioType.HIGH_MOBILITY
        ]

    async def predict(self, state: Any) -> Any:
        """執行預測"""
        # 簡單的隨機預測作為演示
        return random.randint(0, 3)

    def train(self) -> None:
        """
        模擬一個訓練循環。
        在真實的實現中，這裡會是與環境互動、更新網路權重等複雜邏輯。
        """
        print(f"🔍 DEBUG [DQN]: 開始訓練步驟，當前狀態: is_training={self.is_training}, episode={self._current_episode}/{self._total_episodes}")
        
        if not self.is_training:
            print(f"🔍 DEBUG [DQN]: 初始化訓練狀態")
            self.is_training = True
            self._current_episode = 0

        if self._current_episode < self._total_episodes:
            print(f"🔍 DEBUG [DQN]: 執行訓練步驟 {self._current_episode + 1}")
            
            # 模擬一個 step 的耗時 - 使用配置的 step_time
            step_time = self.config.get("step_time", 1.0)  # 默认1秒
            print(f"⏱️ DEBUG [DQN]: 等待 {step_time} 秒...")
            time.sleep(step_time)

            self._current_episode += 1
            # 模擬獎勵和損失的變化
            self._last_reward = random.uniform(-10, 10)
            self._average_reward = (
                self._average_reward * (self._current_episode - 1) + self._last_reward
            ) / self._current_episode
            self._loss *= 0.95  # 模擬損失下降
            
            print(f"📊 DEBUG [DQN]: 訓練步驟完成 {self._current_episode}/{self._total_episodes}, 獎勵: {self._last_reward:.2f}")
        else:
            print(f"✅ DEBUG [DQN]: 訓練完成，但保持狀態讓前端顯示最終結果")
            # 不立即設置 is_training = False，讓訓練循環控制最終狀態

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

    def load_model(self, model_path: str) -> bool:
        """加載模型
        
        Args:
            model_path: 模型檔案路徑
            
        Returns:
            bool: 是否加載成功
        """
        # 模擬模型加載
        print(f"模擬加載模型: {model_path}")
        return True

    def save_model(self, model_path: str) -> bool:
        """保存模型
        
        Args:
            model_path: 保存路徑
            
        Returns:
            bool: 是否保存成功
        """
        # 模擬模型保存
        print(f"模擬保存模型: {model_path}")
        return True

    def get_hyperparameters(self) -> Dict[str, Any]:
        """獲取當前超參數"""
        return self.config.copy()

    def set_hyperparameters(self, params: Dict[str, Any]) -> bool:
        """設定超參數"""
        self.config.update(params)
        return True

    def get_training_metrics(self) -> Dict[str, Any]:
        """獲取訓練指標"""
        return {
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

    def is_trained(self) -> bool:
        """檢查模型是否已訓練"""
        return self._current_episode >= self._total_episodes

    def get_memory_usage(self) -> Dict[str, float]:
        """獲取記憶體使用量"""
        # 模擬記憶體使用量
        return {
            "total_mb": 128.0,
            "used_mb": 64.0,
            "free_mb": 64.0,
            "usage_percent": 50.0
        }

    def validate_scenario(self, scenario: ScenarioType) -> bool:
        """驗證場景是否支援"""
        # DQN支援所有場景類型
        return True
