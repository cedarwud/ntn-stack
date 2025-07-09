"""
決策引擎接口定義
================

定義了強化學習決策引擎的統一接口，整合DQN/PPO/SAC等算法。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .candidate_selector import ScoredCandidate


@dataclass
class Decision:
    """決策結果數據結構"""

    selected_satellite: str  # 選中的衛星ID
    confidence: float  # 決策置信度 (0.0-1.0)
    reasoning: Dict[str, Any]  # 決策推理過程
    alternative_options: List[str]  # 備選方案
    execution_plan: Dict[str, Any]  # 執行計劃
    visualization_data: Dict[str, Any]  # 3D視覺化數據
    algorithm_used: str  # 使用的算法名稱
    decision_time: float  # 決策耗時 (毫秒)
    context: Dict[str, Any]  # 決策上下文
    expected_performance: Dict[str, float]  # 預期性能指標

    def __post_init__(self):
        """後處理驗證"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


@dataclass
class RLState:
    """強化學習狀態表示"""

    satellite_states: List[Dict[str, float]]  # 衛星狀態向量
    network_conditions: Dict[str, float]  # 網路條件
    user_context: Dict[str, Any]  # 用戶上下文
    historical_performance: List[float]  # 歷史性能
    time_features: Dict[str, float]  # 時間特徵


@dataclass
class RLAction:
    """強化學習動作表示"""

    action_type: str  # 動作類型
    target_satellite: str  # 目標衛星
    parameters: Dict[str, Any]  # 動作參數
    confidence: float  # 動作置信度


class RLIntegrationInterface(ABC):
    """強化學習整合接口"""

    @abstractmethod
    def make_decision(
        self, candidates: List[ScoredCandidate], context: Dict[str, Any]
    ) -> Decision:
        """
        整合RL系統做出決策

        Args:
            candidates: 評分後的候選列表
            context: 決策上下文

        Returns:
            Decision: 決策結果
        """
        pass

    @abstractmethod
    def prepare_rl_state(
        self, candidates: List[ScoredCandidate], context: Dict[str, Any]
    ) -> RLState:
        """
        準備強化學習狀態向量

        Args:
            candidates: 候選列表
            context: 上下文信息

        Returns:
            RLState: RL狀態表示
        """
        pass

    @abstractmethod
    def execute_rl_action(self, state: RLState) -> RLAction:
        """
        執行強化學習推理

        Args:
            state: RL狀態

        Returns:
            RLAction: RL動作
        """
        pass

    @abstractmethod
    def update_policy(self, feedback: Dict[str, Any]) -> None:
        """
        根據反饋更新RL策略

        Args:
            feedback: 執行反饋數據
        """
        pass

    @abstractmethod
    def get_confidence_score(self, decision: Decision) -> float:
        """
        獲取決策的置信度分數

        Args:
            decision: 決策結果

        Returns:
            float: 置信度分數
        """
        pass

    @abstractmethod
    def prepare_visualization_data(
        self, decision: Decision, candidates: List[ScoredCandidate]
    ) -> Dict[str, Any]:
        """
        準備3D視覺化所需數據

        Args:
            decision: 決策結果
            candidates: 候選列表

        Returns:
            Dict[str, Any]: 視覺化數據
        """
        pass

    @abstractmethod
    def get_available_algorithms(self) -> List[str]:
        """
        獲取可用的RL算法列表

        Returns:
            List[str]: 算法名稱列表
        """
        pass

    @abstractmethod
    def select_best_algorithm(self, context: Dict[str, Any]) -> str:
        """
        根據上下文選擇最佳算法

        Args:
            context: 決策上下文

        Returns:
            str: 最佳算法名稱
        """
        pass

    @abstractmethod
    def get_algorithm_performance_history(
        self, algorithm_name: str
    ) -> Dict[str, List[float]]:
        """
        獲取算法性能歷史

        Args:
            algorithm_name: 算法名稱

        Returns:
            Dict[str, List[float]]: 性能歷史數據
        """
        pass

    @abstractmethod
    async def get_active_algorithm(self) -> str:
        """
        獲取當前活躍的強化學習算法名稱 (例如 'dqn', 'ppo')
        """
        pass

    @abstractmethod
    async def get_algorithm_details(self) -> Dict[str, Any]:
        """
        獲取當前算法的詳細狀態和指標
        """
        pass

    @abstractmethod
    async def start_training(self, algorithm: str) -> Dict[str, Any]:
        """啟動指定算法的訓練"""
        pass

    @abstractmethod
    async def stop_training(self) -> Dict[str, Any]:
        """停止當前的訓練"""
        pass


class DecisionEngineError(Exception):
    """決策引擎錯誤"""

    pass


class AlgorithmNotAvailableError(DecisionEngineError):
    """算法不可用錯誤"""

    pass
