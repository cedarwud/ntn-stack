"""
算法整合器 - 統一管理 RL 算法

提供統一的 RL 算法接口，包括：
- 算法實例化和管理
- 算法切換和配置
- 算法性能監控
- 算法適配器管理
"""

import logging
from typing import Dict, Optional, Any, List
from abc import ABC, abstractmethod

# 導入真實算法實現
try:
    from ..algorithms.real_rl_algorithms import (
        IRLAlgorithm as RealIRLAlgorithm,
        RealDQNAlgorithm,
        RealPPOAlgorithm,
        RealSACAlgorithm,
        create_real_algorithm,
    )

    REAL_ALGORITHMS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"真實算法模組導入失敗，將使用模擬算法: {e}")
    REAL_ALGORITHMS_AVAILABLE = False

logger = logging.getLogger(__name__)


class IRLAlgorithm(ABC):
    """RL 算法統一接口"""

    @abstractmethod
    async def predict(self, state: Any) -> Any:
        """預測動作"""
        pass

    @abstractmethod
    async def learn(
        self, state: Any, action: Any, reward: float, next_state: Any, done: bool
    ):
        """學習經驗"""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """獲取算法指標"""
        pass


class DQNAlgorithm(IRLAlgorithm):
    """DQN 算法實現 - 使用真實或模擬算法"""

    def __init__(self, state_size: int = 10, action_size: int = 4):
        self.name = "DQN"

        if REAL_ALGORITHMS_AVAILABLE:
            # 使用真實 DQN 算法
            self.real_algorithm = RealDQNAlgorithm(state_size, action_size)
            self.is_real = True
            logger.info("🧠 [DQN] 使用真實 DQN 算法初始化完成")
        else:
            # 使用模擬算法
            self.metrics = {
                "total_steps": 0,
                "learning_rate": 0.001,
                "epsilon": 0.1,
                "loss": 0.0,
            }
            self.is_real = False
            logger.info("🎲 [DQN] 使用模擬 DQN 算法初始化完成")

    async def predict(self, state: Any) -> Any:
        """DQN 動作預測"""
        if self.is_real:
            # 使用真實算法預測
            action = await self.real_algorithm.predict(state)
            logger.debug(f"🧠 [DQN] 真實預測動作: {action}")
            return action
        else:
            # 模擬 DQN 預測
            import random

            action = random.choice([0, 1, 2, 3])  # 4 個動作
            logger.debug(f"🎲 [DQN] 模擬預測動作: {action}")
            return action

    async def learn(
        self, state: Any, action: Any, reward: float, next_state: Any, done: bool
    ):
        """DQN 學習"""
        if self.is_real:
            # 使用真實算法學習
            await self.real_algorithm.learn(state, action, reward, next_state, done)
            logger.debug(f"🧠 [DQN] 真實學習更新: 獎勵={reward}")
        else:
            # 模擬學習過程
            self.metrics["total_steps"] += 1
            self.metrics["loss"] = abs(reward - 0.5) * 0.1
            logger.debug(f"🎲 [DQN] 模擬學習更新: 獎勵={reward}")

    def get_metrics(self) -> Dict[str, Any]:
        if self.is_real:
            return self.real_algorithm.get_metrics()
        else:
            return self.metrics.copy()


class PPOAlgorithm(IRLAlgorithm):
    """PPO 算法實現 - 使用真實或模擬算法"""

    def __init__(self, state_size: int = 10, action_size: int = 4):
        self.name = "PPO"

        if REAL_ALGORITHMS_AVAILABLE:
            # 使用真實 PPO 算法
            self.real_algorithm = RealPPOAlgorithm(state_size, action_size)
            self.is_real = True
            logger.info("🎯 [PPO] 使用真實 PPO 算法初始化完成")
        else:
            # 使用模擬算法
            self.metrics = {
                "total_steps": 0,
                "policy_loss": 0.0,
                "value_loss": 0.0,
                "entropy": 0.01,
            }
            self.is_real = False
            logger.info("🎲 [PPO] 使用模擬 PPO 算法初始化完成")

    async def predict(self, state: Any) -> Any:
        """PPO 動作預測"""
        if self.is_real:
            action = await self.real_algorithm.predict(state)
            logger.debug(f"🎯 [PPO] 真實預測動作: {action}")
            return action
        else:
            import random

            action = random.choice([0, 1, 2, 3])
            logger.debug(f"🎲 [PPO] 模擬預測動作: {action}")
            return action

    async def learn(
        self, state: Any, action: Any, reward: float, next_state: Any, done: bool
    ):
        """PPO 學習"""
        if self.is_real:
            await self.real_algorithm.learn(state, action, reward, next_state, done)
            logger.debug(f"🎯 [PPO] 真實學習更新: 獎勵={reward}")
        else:
            self.metrics["total_steps"] += 1
            self.metrics["policy_loss"] = abs(reward - 0.8) * 0.1
            self.metrics["value_loss"] = abs(reward - 0.8) * 0.05
            logger.debug(f"🎲 [PPO] 模擬學習更新: 獎勵={reward}")

    def get_metrics(self) -> Dict[str, Any]:
        if self.is_real:
            return self.real_algorithm.get_metrics()
        else:
            return self.metrics.copy()


class SACAlgorithm(IRLAlgorithm):
    """SAC 算法實現 - 使用真實或模擬算法"""

    def __init__(self, state_size: int = 10, action_size: int = 4):
        self.name = "SAC"

        if REAL_ALGORITHMS_AVAILABLE:
            # 使用真實 SAC 算法
            self.real_algorithm = RealSACAlgorithm(state_size, action_size)
            self.is_real = True
            logger.info("⚡ [SAC] 使用真實 SAC 算法初始化完成")
        else:
            # 使用模擬算法
            self.metrics = {
                "total_steps": 0,
                "actor_loss": 0.0,
                "critic_loss": 0.0,
                "temperature": 0.2,
            }
            self.is_real = False
            logger.info("🎲 [SAC] 使用模擬 SAC 算法初始化完成")

    async def predict(self, state: Any) -> Any:
        """SAC 動作預測"""
        if self.is_real:
            action = await self.real_algorithm.predict(state)
            logger.debug(f"⚡ [SAC] 真實預測動作: {action}")
            return action
        else:
            import random

            action = random.choice([0, 1, 2, 3])
            logger.debug(f"🎲 [SAC] 模擬預測動作: {action}")
            return action

    async def learn(
        self, state: Any, action: Any, reward: float, next_state: Any, done: bool
    ):
        """SAC 學習"""
        if self.is_real:
            await self.real_algorithm.learn(state, action, reward, next_state, done)
            logger.debug(f"⚡ [SAC] 真實學習更新: 獎勵={reward}")
        else:
            self.metrics["total_steps"] += 1
            self.metrics["actor_loss"] = abs(reward - 0.75) * 0.1
            self.metrics["critic_loss"] = abs(reward - 0.75) * 0.08
            logger.debug(f"🎲 [SAC] 模擬學習更新: 獎勵={reward}")

    def get_metrics(self) -> Dict[str, Any]:
        if self.is_real:
            return self.real_algorithm.get_metrics()
        else:
            return self.metrics.copy()


class RLAlgorithmIntegrator:
    """RL 算法整合器"""

    def __init__(self):
        self.algorithms: Dict[str, IRLAlgorithm] = {}
        self.active_algorithm: Optional[str] = None
        self._initialize_algorithms()

    def _initialize_algorithms(self):
        """初始化所有可用算法"""
        try:
            self.algorithms["dqn"] = DQNAlgorithm()
            self.algorithms["ppo"] = PPOAlgorithm()
            self.algorithms["sac"] = SACAlgorithm()

            logger.info(
                f"算法整合器初始化完成，可用算法: {list(self.algorithms.keys())}"
            )
        except Exception as e:
            logger.error(f"算法初始化失敗: {e}")

    async def get_algorithm(self, algorithm_name: str) -> Optional[IRLAlgorithm]:
        """獲取算法實例"""
        try:
            # 支持大小寫不敏感的算法名稱
            algorithm_key = algorithm_name.lower()
            if algorithm_key in self.algorithms:
                logger.info(f"✅ 獲取算法實例: {algorithm_name} -> {algorithm_key}")
                return self.algorithms[algorithm_key]
            else:
                logger.warning(f"算法 {algorithm_name} (key: {algorithm_key}) 不存在，可用算法: {list(self.algorithms.keys())}")
                return None
        except Exception as e:
            logger.error(f"獲取算法實例失敗: {e}")
            return None

    def get_available_algorithms(self) -> List[str]:
        """獲取可用算法列表"""
        return list(self.algorithms.keys())

    def set_active_algorithm(self, algorithm_name: str) -> bool:
        """設置活躍算法"""
        try:
            if algorithm_name in self.algorithms:
                self.active_algorithm = algorithm_name
                logger.info(f"切換到算法: {algorithm_name}")
                return True
            else:
                logger.warning(f"無法切換到不存在的算法: {algorithm_name}")
                return False
        except Exception as e:
            logger.error(f"切換算法失敗: {e}")
            return False

    def get_active_algorithm(self) -> Optional[IRLAlgorithm]:
        """獲取當前活躍算法"""
        if self.active_algorithm:
            return self.algorithms.get(self.active_algorithm)
        return None

    def get_algorithm_metrics(self, algorithm_name: str) -> Optional[Dict[str, Any]]:
        """獲取算法指標"""
        try:
            if algorithm_name in self.algorithms:
                return self.algorithms[algorithm_name].get_metrics()
            return None
        except Exception as e:
            logger.error(f"獲取算法指標失敗: {e}")
            return None

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有算法指標"""
        try:
            all_metrics = {}
            for name, algorithm in self.algorithms.items():
                all_metrics[name] = algorithm.get_metrics()
            return all_metrics
        except Exception as e:
            logger.error(f"獲取所有算法指標失敗: {e}")
            return {}

    async def compare_algorithms(self, test_states: List[Any]) -> Dict[str, Any]:
        """比較算法性能"""
        try:
            comparison_results = {}

            for algorithm_name, algorithm in self.algorithms.items():
                results = []
                for state in test_states:
                    action = await algorithm.predict(state)
                    results.append(action)

                comparison_results[algorithm_name] = {
                    "predictions": results,
                    "metrics": algorithm.get_metrics(),
                    "average_prediction": sum(results) / len(results) if results else 0,
                }

            return comparison_results

        except Exception as e:
            logger.error(f"算法比較失敗: {e}")
            return {}

    def get_integration_status(self) -> Dict[str, Any]:
        """獲取整合器狀態"""
        return {
            "total_algorithms": len(self.algorithms),
            "available_algorithms": list(self.algorithms.keys()),
            "active_algorithm": self.active_algorithm,
            "status": "operational",
        }
