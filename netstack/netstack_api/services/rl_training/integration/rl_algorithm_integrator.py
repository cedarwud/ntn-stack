"""
Phase 2.3 統一 RL 算法整合器

統一管理 DQN、PPO、SAC 算法，提供標準化的接口：
- 算法載入和初始化
- 統一的決策接口
- 算法切換和比較
- 性能監控和指標收集
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class AlgorithmType(Enum):
    """支援的算法類型"""

    DQN = "dqn"
    PPO = "ppo"
    SAC = "sac"


class AlgorithmStatus(Enum):
    """算法狀態"""

    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    TRAINING = "training"
    INFERENCING = "inferencing"
    ERROR = "error"


@dataclass
class AlgorithmDecision:
    """算法決策結果"""

    algorithm_type: AlgorithmType
    action: Any
    confidence: float
    q_values: Optional[List[float]] = None
    policy_logits: Optional[List[float]] = None
    reasoning: Optional[Dict[str, Any]] = None
    decision_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AlgorithmMetrics:
    """算法性能指標"""

    total_decisions: int = 0
    successful_decisions: int = 0
    average_decision_time_ms: float = 0.0
    average_confidence: float = 0.0
    total_reward: float = 0.0
    episode_count: int = 0
    last_performance_update: Optional[datetime] = None


class BaseRLAlgorithmAdapter(ABC):
    """RL 算法適配器基類"""

    def __init__(self, algorithm_type: AlgorithmType, config: Dict[str, Any]):
        self.algorithm_type = algorithm_type
        self.config = config
        self.status = AlgorithmStatus.IDLE
        self.metrics = AlgorithmMetrics()
        self._last_state = None
        self._last_action = None

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化算法"""
        pass

    @abstractmethod
    async def predict(self, state: Any) -> AlgorithmDecision:
        """執行預測"""
        pass

    @abstractmethod
    async def update(
        self, state: Any, action: Any, reward: float, next_state: Any, done: bool
    ) -> bool:
        """更新算法"""
        pass

    @abstractmethod
    async def save_model(self, path: str) -> bool:
        """保存模型"""
        pass

    @abstractmethod
    async def load_model(self, path: str) -> bool:
        """載入模型"""
        pass


class DQNAlgorithmAdapter(BaseRLAlgorithmAdapter):
    """DQN 算法適配器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(AlgorithmType.DQN, config)
        self.dqn_agent = None

    async def initialize(self) -> bool:
        """初始化 DQN 算法"""
        try:
            self.status = AlgorithmStatus.LOADING

            # 嘗試導入現有的 DQN 實現
            try:
                from ...algorithm_ecosystem.rl_algorithms.dqn_agent import (
                    DQNHandoverAgent,
                )

                self.dqn_agent = DQNHandoverAgent(self.config)
                await self.dqn_agent.initialize()
                logger.info("成功載入生產級 DQN 算法")
            except ImportError:
                # 使用備用實現
                from ...algorithms.dqn_algorithm import DQNAlgorithm

                self.dqn_agent = DQNAlgorithm("LEOSatelliteHandover-v0", self.config)
                logger.warning("使用備用 DQN 實現")

            self.status = AlgorithmStatus.READY
            logger.info("DQN 算法初始化完成")
            return True

        except Exception as e:
            self.status = AlgorithmStatus.ERROR
            logger.error(f"DQN 算法初始化失敗: {e}")
            return False

    async def predict(self, state: Any) -> AlgorithmDecision:
        """DQN 預測"""
        start_time = time.time()

        try:
            self.status = AlgorithmStatus.INFERENCING

            # 執行 DQN 預測
            if hasattr(self.dqn_agent, "make_decision"):
                # 生產級接口
                action, q_values, confidence = await self.dqn_agent.make_decision(state)
                reasoning = {
                    "epsilon": getattr(self.dqn_agent, "epsilon", 0.0),
                    "exploration_mode": confidence < 0.8,
                }
            else:
                # 備用接口
                action = await self.dqn_agent.predict(state)
                q_values = None
                confidence = 0.7  # 預設置信度
                reasoning = {"backup_mode": True}

            decision_time = (time.time() - start_time) * 1000

            # 更新指標
            self.metrics.total_decisions += 1
            self.metrics.average_decision_time_ms = (
                self.metrics.average_decision_time_ms
                * (self.metrics.total_decisions - 1)
                + decision_time
            ) / self.metrics.total_decisions
            self.metrics.average_confidence = (
                self.metrics.average_confidence * (self.metrics.total_decisions - 1)
                + confidence
            ) / self.metrics.total_decisions

            self.status = AlgorithmStatus.READY

            return AlgorithmDecision(
                algorithm_type=AlgorithmType.DQN,
                action=action,
                confidence=confidence,
                q_values=q_values,
                reasoning=reasoning,
                decision_time_ms=decision_time,
                metadata={
                    "total_decisions": self.metrics.total_decisions,
                    "algorithm_status": self.status.value,
                },
            )

        except Exception as e:
            logger.error(f"DQN 預測失敗: {e}")
            self.status = AlgorithmStatus.ERROR
            return AlgorithmDecision(
                algorithm_type=AlgorithmType.DQN,
                action=0,  # 預設動作
                confidence=0.0,
                decision_time_ms=time.time() - start_time,
                metadata={"error": str(e)},
            )

    async def update(
        self, state: Any, action: Any, reward: float, next_state: Any, done: bool
    ) -> bool:
        """更新 DQN"""
        try:
            if hasattr(self.dqn_agent, "remember"):
                self.dqn_agent.remember(state, action, reward, next_state, done)

            if (
                hasattr(self.dqn_agent, "train_step")
                and self.metrics.total_decisions % 10 == 0
            ):
                await self.dqn_agent.train_step()

            self.metrics.total_reward += reward
            if reward > 0:
                self.metrics.successful_decisions += 1

            return True
        except Exception as e:
            logger.error(f"DQN 更新失敗: {e}")
            return False

    async def save_model(self, path: str) -> bool:
        """保存 DQN 模型"""
        try:
            if hasattr(self.dqn_agent, "save_model"):
                return await self.dqn_agent.save_model(path)
            return True
        except Exception as e:
            logger.error(f"DQN 模型保存失敗: {e}")
            return False

    async def load_model(self, path: str) -> bool:
        """載入 DQN 模型"""
        try:
            if hasattr(self.dqn_agent, "load_model"):
                return await self.dqn_agent.load_model(path)
            return True
        except Exception as e:
            logger.error(f"DQN 模型載入失敗: {e}")
            return False


class PPOAlgorithmAdapter(BaseRLAlgorithmAdapter):
    """PPO 算法適配器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(AlgorithmType.PPO, config)
        self.ppo_agent = None

    async def initialize(self) -> bool:
        """初始化 PPO 算法"""
        try:
            self.status = AlgorithmStatus.LOADING

            # 嘗試導入現有的 PPO 實現
            try:
                from ...algorithm_ecosystem.rl_algorithms.ppo_agent import (
                    PPOHandoverAgent,
                )

                self.ppo_agent = PPOHandoverAgent(self.config)
                await self.ppo_agent.initialize()
                logger.info("成功載入生產級 PPO 算法")
            except ImportError:
                # 使用備用實現
                from ...algorithms.ppo_algorithm import PPOAlgorithm

                self.ppo_agent = PPOAlgorithm("LEOSatelliteHandover-v0", self.config)
                logger.warning("使用備用 PPO 實現")

            self.status = AlgorithmStatus.READY
            logger.info("PPO 算法初始化完成")
            return True

        except Exception as e:
            self.status = AlgorithmStatus.ERROR
            logger.error(f"PPO 算法初始化失敗: {e}")
            return False

    async def predict(self, state: Any) -> AlgorithmDecision:
        """PPO 預測"""
        start_time = time.time()

        try:
            self.status = AlgorithmStatus.INFERENCING

            # 執行 PPO 預測
            if hasattr(self.ppo_agent, "make_decision"):
                # 生產級接口
                action, policy_logits, confidence = await self.ppo_agent.make_decision(
                    state
                )
                reasoning = {
                    "policy_entropy": np.std(policy_logits) if policy_logits else 0.0,
                    "action_distribution": policy_logits,
                }
            else:
                # 備用接口
                action = await self.ppo_agent.predict(state)
                policy_logits = None
                confidence = 0.8  # PPO 通常較穩定
                reasoning = {"backup_mode": True}

            decision_time = (time.time() - start_time) * 1000

            # 更新指標
            self.metrics.total_decisions += 1
            self.metrics.average_decision_time_ms = (
                self.metrics.average_decision_time_ms
                * (self.metrics.total_decisions - 1)
                + decision_time
            ) / self.metrics.total_decisions
            self.metrics.average_confidence = (
                self.metrics.average_confidence * (self.metrics.total_decisions - 1)
                + confidence
            ) / self.metrics.total_decisions

            self.status = AlgorithmStatus.READY

            return AlgorithmDecision(
                algorithm_type=AlgorithmType.PPO,
                action=action,
                confidence=confidence,
                policy_logits=policy_logits,
                reasoning=reasoning,
                decision_time_ms=decision_time,
                metadata={
                    "total_decisions": self.metrics.total_decisions,
                    "algorithm_status": self.status.value,
                },
            )

        except Exception as e:
            logger.error(f"PPO 預測失敗: {e}")
            self.status = AlgorithmStatus.ERROR
            return AlgorithmDecision(
                algorithm_type=AlgorithmType.PPO,
                action=0,
                confidence=0.0,
                decision_time_ms=time.time() - start_time,
                metadata={"error": str(e)},
            )

    async def update(
        self, state: Any, action: Any, reward: float, next_state: Any, done: bool
    ) -> bool:
        """更新 PPO"""
        try:
            if hasattr(self.ppo_agent, "store_transition"):
                self.ppo_agent.store_transition(state, action, reward, next_state, done)

            if (
                hasattr(self.ppo_agent, "update_policy")
                and self.metrics.total_decisions % 20 == 0
            ):
                await self.ppo_agent.update_policy()

            self.metrics.total_reward += reward
            if reward > 0:
                self.metrics.successful_decisions += 1

            return True
        except Exception as e:
            logger.error(f"PPO 更新失敗: {e}")
            return False

    async def save_model(self, path: str) -> bool:
        """保存 PPO 模型"""
        try:
            if hasattr(self.ppo_agent, "save_model"):
                return await self.ppo_agent.save_model(path)
            return True
        except Exception as e:
            logger.error(f"PPO 模型保存失敗: {e}")
            return False

    async def load_model(self, path: str) -> bool:
        """載入 PPO 模型"""
        try:
            if hasattr(self.ppo_agent, "load_model"):
                return await self.ppo_agent.load_model(path)
            return True
        except Exception as e:
            logger.error(f"PPO 模型載入失敗: {e}")
            return False


class SACAlgorithmAdapter(BaseRLAlgorithmAdapter):
    """SAC 算法適配器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(AlgorithmType.SAC, config)
        self.sac_agent = None

    async def initialize(self) -> bool:
        """初始化 SAC 算法"""
        try:
            self.status = AlgorithmStatus.LOADING

            # 嘗試導入現有的 SAC 實現
            try:
                from ...algorithm_ecosystem.rl_algorithms.sac_agent import (
                    SACHandoverAgent,
                )

                self.sac_agent = SACHandoverAgent(self.config)
                await self.sac_agent.initialize()
                logger.info("成功載入生產級 SAC 算法")
            except ImportError:
                # 使用備用實現
                from ...algorithms.sac_algorithm import SACAlgorithm

                self.sac_agent = SACAlgorithm("LEOSatelliteHandover-v0", self.config)
                logger.warning("使用備用 SAC 實現")

            self.status = AlgorithmStatus.READY
            logger.info("SAC 算法初始化完成")
            return True

        except Exception as e:
            self.status = AlgorithmStatus.ERROR
            logger.error(f"SAC 算法初始化失敗: {e}")
            return False

    async def predict(self, state: Any) -> AlgorithmDecision:
        """SAC 預測"""
        start_time = time.time()

        try:
            self.status = AlgorithmStatus.INFERENCING

            # 執行 SAC 預測
            if hasattr(self.sac_agent, "make_decision"):
                # 生產級接口
                action, q_values, confidence = await self.sac_agent.make_decision(state)
                reasoning = {
                    "entropy_regularization": getattr(self.sac_agent, "alpha", 0.2),
                    "exploration_noise": 0.1,
                    "q_value_spread": np.std(q_values) if q_values else 0.0,
                }
            else:
                # 備用接口
                action = await self.sac_agent.predict(state)
                q_values = None
                confidence = 0.85  # SAC 通常較穩定
                reasoning = {"backup_mode": True}

            decision_time = (time.time() - start_time) * 1000

            # 更新指標
            self.metrics.total_decisions += 1
            self.metrics.average_decision_time_ms = (
                self.metrics.average_decision_time_ms
                * (self.metrics.total_decisions - 1)
                + decision_time
            ) / self.metrics.total_decisions
            self.metrics.average_confidence = (
                self.metrics.average_confidence * (self.metrics.total_decisions - 1)
                + confidence
            ) / self.metrics.total_decisions

            self.status = AlgorithmStatus.READY

            return AlgorithmDecision(
                algorithm_type=AlgorithmType.SAC,
                action=action,
                confidence=confidence,
                q_values=q_values,
                reasoning=reasoning,
                decision_time_ms=decision_time,
                metadata={
                    "total_decisions": self.metrics.total_decisions,
                    "algorithm_status": self.status.value,
                },
            )

        except Exception as e:
            logger.error(f"SAC 預測失敗: {e}")
            self.status = AlgorithmStatus.ERROR
            return AlgorithmDecision(
                algorithm_type=AlgorithmType.SAC,
                action=0,
                confidence=0.0,
                decision_time_ms=time.time() - start_time,
                metadata={"error": str(e)},
            )

    async def update(
        self, state: Any, action: Any, reward: float, next_state: Any, done: bool
    ) -> bool:
        """更新 SAC"""
        try:
            if hasattr(self.sac_agent, "remember"):
                self.sac_agent.remember(state, action, reward, next_state, done)

            if (
                hasattr(self.sac_agent, "update_networks")
                and self.metrics.total_decisions % 5 == 0
            ):
                await self.sac_agent.update_networks()

            self.metrics.total_reward += reward
            if reward > 0:
                self.metrics.successful_decisions += 1

            return True
        except Exception as e:
            logger.error(f"SAC 更新失敗: {e}")
            return False

    async def save_model(self, path: str) -> bool:
        """保存 SAC 模型"""
        try:
            if hasattr(self.sac_agent, "save_model"):
                return await self.sac_agent.save_model(path)
            return True
        except Exception as e:
            logger.error(f"SAC 模型保存失敗: {e}")
            return False

    async def load_model(self, path: str) -> bool:
        """載入 SAC 模型"""
        try:
            if hasattr(self.sac_agent, "load_model"):
                return await self.sac_agent.load_model(path)
            return True
        except Exception as e:
            logger.error(f"SAC 模型載入失敗: {e}")
            return False


class RLAlgorithmIntegrator:
    """RL 算法統一整合器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 RL 算法整合器

        Args:
            config: 整合器配置
                - enabled_algorithms: 啟用的算法列表
                - default_algorithm: 預設算法
                - algorithm_configs: 各算法的具體配置
        """
        self.config = config
        self.enabled_algorithms = config.get(
            "enabled_algorithms", ["dqn", "ppo", "sac"]
        )
        self.default_algorithm = config.get("default_algorithm", "dqn")
        self.algorithm_configs = config.get("algorithm_configs", {})

        # 算法適配器實例
        self.adapters: Dict[AlgorithmType, BaseRLAlgorithmAdapter] = {}
        self.current_algorithm = None

        # 整合器狀態
        self.is_initialized = False
        self.total_decisions = 0
        self.algorithm_switch_count = 0

        logger.info(f"RL 算法整合器初始化，啟用算法: {self.enabled_algorithms}")

    async def initialize(self) -> bool:
        """初始化所有啟用的算法"""
        try:
            logger.info("開始初始化 RL 算法...")

            # 創建算法適配器
            for algorithm_name in self.enabled_algorithms:
                try:
                    algorithm_type = AlgorithmType(algorithm_name.lower())
                    algorithm_config = self.algorithm_configs.get(algorithm_name, {})

                    if algorithm_type == AlgorithmType.DQN:
                        adapter = DQNAlgorithmAdapter(algorithm_config)
                    elif algorithm_type == AlgorithmType.PPO:
                        adapter = PPOAlgorithmAdapter(algorithm_config)
                    elif algorithm_type == AlgorithmType.SAC:
                        adapter = SACAlgorithmAdapter(algorithm_config)
                    else:
                        logger.warning(f"不支援的算法類型: {algorithm_name}")
                        continue

                    # 初始化適配器
                    if await adapter.initialize():
                        self.adapters[algorithm_type] = adapter
                        logger.info(f"成功初始化 {algorithm_name.upper()} 算法")
                    else:
                        logger.error(f"初始化 {algorithm_name.upper()} 算法失敗")

                except Exception as e:
                    logger.error(f"創建 {algorithm_name} 適配器時發生錯誤: {e}")

            # 設置預設算法
            if self.adapters:
                default_type = AlgorithmType(self.default_algorithm.lower())
                if default_type in self.adapters:
                    self.current_algorithm = default_type
                else:
                    # 使用第一個可用的算法
                    self.current_algorithm = list(self.adapters.keys())[0]

                self.is_initialized = True
                logger.info(
                    f"RL 算法整合器初始化完成，當前算法: {self.current_algorithm.value}"
                )
                return True
            else:
                logger.error("沒有成功初始化任何算法")
                return False

        except Exception as e:
            logger.error(f"RL 算法整合器初始化失敗: {e}")
            return False

    async def predict(
        self, state: Any, algorithm_type: Optional[AlgorithmType] = None
    ) -> AlgorithmDecision:
        """
        執行決策預測

        Args:
            state: 環境狀態
            algorithm_type: 指定的算法類型，如果為 None 則使用當前算法

        Returns:
            AlgorithmDecision: 決策結果
        """
        if not self.is_initialized:
            raise RuntimeError("算法整合器尚未初始化")

        # 確定使用的算法
        target_algorithm = algorithm_type or self.current_algorithm

        if target_algorithm not in self.adapters:
            raise ValueError(f"算法 {target_algorithm.value} 不可用")

        # 執行預測
        adapter = self.adapters[target_algorithm]
        decision = await adapter.predict(state)

        self.total_decisions += 1

        return decision

    async def update(
        self,
        state: Any,
        action: Any,
        reward: float,
        next_state: Any,
        done: bool,
        algorithm_type: Optional[AlgorithmType] = None,
    ) -> bool:
        """
        更新算法

        Args:
            state: 當前狀態
            action: 執行的動作
            reward: 獲得的獎勵
            next_state: 下一個狀態
            done: 是否結束
            algorithm_type: 指定的算法類型

        Returns:
            bool: 更新是否成功
        """
        if not self.is_initialized:
            return False

        target_algorithm = algorithm_type or self.current_algorithm

        if target_algorithm not in self.adapters:
            return False

        adapter = self.adapters[target_algorithm]
        return await adapter.update(state, action, reward, next_state, done)

    async def switch_algorithm(self, algorithm_type: AlgorithmType) -> bool:
        """
        切換當前算法

        Args:
            algorithm_type: 目標算法類型

        Returns:
            bool: 切換是否成功
        """
        if algorithm_type not in self.adapters:
            logger.error(f"無法切換到算法 {algorithm_type.value}，該算法不可用")
            return False

        old_algorithm = self.current_algorithm
        self.current_algorithm = algorithm_type
        self.algorithm_switch_count += 1

        logger.info(f"算法已從 {old_algorithm.value} 切換到 {algorithm_type.value}")
        return True

    def get_available_algorithms(self) -> List[AlgorithmType]:
        """獲取可用的算法列表"""
        return list(self.adapters.keys())

    def get_algorithm_metrics(self) -> Dict[str, AlgorithmMetrics]:
        """獲取所有算法的性能指標"""
        metrics = {}
        for algorithm_type, adapter in self.adapters.items():
            metrics[algorithm_type.value] = adapter.metrics
        return metrics

    def get_status(self) -> Dict[str, Any]:
        """獲取整合器狀態"""
        return {
            "is_initialized": self.is_initialized,
            "current_algorithm": (
                self.current_algorithm.value if self.current_algorithm else None
            ),
            "available_algorithms": [a.value for a in self.get_available_algorithms()],
            "total_decisions": self.total_decisions,
            "algorithm_switch_count": self.algorithm_switch_count,
            "algorithm_status": {
                algo.value: adapter.status.value
                for algo, adapter in self.adapters.items()
            },
        }

    async def save_all_models(self, base_path: str) -> Dict[str, bool]:
        """保存所有算法的模型"""
        results = {}
        for algorithm_type, adapter in self.adapters.items():
            model_path = f"{base_path}/{algorithm_type.value}_model.pth"
            results[algorithm_type.value] = await adapter.save_model(model_path)
        return results

    async def load_all_models(self, base_path: str) -> Dict[str, bool]:
        """載入所有算法的模型"""
        results = {}
        for algorithm_type, adapter in self.adapters.items():
            model_path = f"{base_path}/{algorithm_type.value}_model.pth"
            results[algorithm_type.value] = await adapter.load_model(model_path)
        return results
