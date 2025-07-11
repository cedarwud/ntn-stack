"""
🧠 RL 算法核心接口

定義統一的強化學習算法接口，支援插件化擴展和多算法協作。
遵循接口隔離原則，每個接口只包含必要的方法。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ScenarioType(str, Enum):
    """場景類型枚舉"""

    URBAN = "urban"
    SUBURBAN = "suburban"
    LOW_LATENCY = "low_latency"
    HIGH_MOBILITY = "high_mobility"
    DENSE_NETWORK = "dense_network"


@dataclass
class TrainingConfig:
    """訓練配置數據類"""

    episodes: int
    batch_size: int
    learning_rate: float
    max_steps_per_episode: int = 1000
    scenario_type: ScenarioType = ScenarioType.URBAN
    custom_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


@dataclass
class TrainingResult:
    """訓練結果數據類"""

    success: bool
    final_score: float
    episodes_completed: int
    convergence_episode: Optional[int]
    metrics: Dict[str, Any]
    model_path: Optional[str]
    training_duration_seconds: float
    memory_usage_mb: float

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class PredictionContext:
    """預測上下文"""

    satellite_positions: List[Dict[str, float]]
    ue_position: Dict[str, float]
    network_conditions: Dict[str, Any]
    current_serving_satellite: int
    candidate_satellites: List[int]
    timestamp: datetime


@dataclass
class HandoverDecision:
    """換手決策結果"""

    target_satellite_id: int
    confidence_score: float
    estimated_latency_ms: float
    predicted_throughput_mbps: float
    decision_reasoning: Dict[str, Any]
    execution_priority: int = 1  # 1=highest, 5=lowest


class IRLAlgorithm(ABC):
    """
    強化學習演算法的抽象基底類別 (介面)
    """

    @abstractmethod
    def __init__(self, env_name: str, config: Dict[str, Any]):
        """
        初始化演算法

        Args:
            env_name (str): The name of the gymnasium environment.
            config (Dict[str, Any]): A dictionary containing algorithm-specific hyperparameters.
        """
        pass

    @abstractmethod
    def train(self) -> None:
        """
        執行一個訓練循環
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        獲取目前訓練狀態

        Returns:
            Dict[str, Any]: A dictionary containing training status information
                            (e.g., episode, reward, loss).
        """
        pass

    @abstractmethod
    def stop_training(self) -> None:
        """
        停止訓練過程
        """
        pass

    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """加載模型

        Args:
            model_path: 模型檔案路徑

        Returns:
            bool: 是否加載成功
        """
        pass

    @abstractmethod
    def save_model(self, model_path: str) -> bool:
        """保存模型

        Args:
            model_path: 保存路徑

        Returns:
            bool: 是否保存成功
        """
        pass

    @abstractmethod
    def get_hyperparameters(self) -> Dict[str, Any]:
        """獲取當前超參數"""
        pass

    @abstractmethod
    def set_hyperparameters(self, params: Dict[str, Any]) -> bool:
        """設定超參數"""
        pass

    @abstractmethod
    def get_training_metrics(self) -> Dict[str, Any]:
        """獲取訓練指標"""
        pass

    @abstractmethod
    def is_trained(self) -> bool:
        """檢查模型是否已訓練"""
        pass

    @abstractmethod
    def get_memory_usage(self) -> Dict[str, float]:
        """獲取記憶體使用量"""
        pass

    @abstractmethod
    def validate_scenario(self, scenario: ScenarioType) -> bool:
        """驗證場景是否支援"""
        pass


class ITrainingObserver(ABC):
    """訓練觀察者接口"""

    @abstractmethod
    async def on_episode_start(self, episode: int, algorithm_name: str):
        """回合開始事件"""
        pass

    @abstractmethod
    async def on_episode_end(
        self, episode: int, reward: float, metrics: Dict[str, Any]
    ):
        """回合結束事件"""
        pass

    @abstractmethod
    async def on_training_complete(self, result: TrainingResult):
        """訓練完成事件"""
        pass


class IPredictionObserver(ABC):
    """預測觀察者接口"""

    @abstractmethod
    async def on_prediction_made(
        self, context: PredictionContext, decision: HandoverDecision
    ):
        """預測完成事件"""
        pass

    @abstractmethod
    async def on_prediction_error(self, context: PredictionContext, error: Exception):
        """預測錯誤事件"""
        pass


# 異常定義
class RLAlgorithmError(Exception):
    """RL算法基礎異常"""

    pass


class TrainingError(RLAlgorithmError):
    """訓練錯誤"""

    pass


class PredictionError(RLAlgorithmError):
    """預測錯誤"""

    pass


class ModelLoadError(RLAlgorithmError):
    """模型加載錯誤"""

    pass


class UnsupportedScenarioError(RLAlgorithmError):
    """不支援的場景錯誤"""

    pass
