from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class TrainingConfig:
    """訓練配置的數據類"""

    episodes: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    # 允許任何其他自定義參數
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingResult:
    """訓練結果的數據類"""

    success: bool
    final_score: float
    episodes_completed: int
    metrics: Dict[str, Any]
    model_path: Optional[str]


class IRLAlgorithm(ABC):
    """強化學習算法插件的抽象基礎類 (ABC)"""

    @abstractmethod
    def get_name(self) -> str:
        """獲取算法的唯一名稱 (e.g., 'DQN', 'PPO')"""
        pass

    @abstractmethod
    def get_supported_scenarios(self) -> List[str]:
        """獲取此算法支持的場景列表 (e.g., ['urban', 'low_latency'])"""
        pass

    @abstractmethod
    async def train(self, config: TrainingConfig) -> TrainingResult:
        """
        異步執行訓練過程。

        Args:
            config: 包含訓練超參數的配置對象。

        Returns:
            一個包含訓練結果的 TrainingResult 對象。
        """
        pass

    @abstractmethod
    async def predict(self, state: Any) -> Any:
        """
        根據給定的狀態，異步執行預測（推理）。

        Args:
            state: 當前的環境狀態。

        Returns:
            算法計算出的動作。
        """
        pass

    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """
        從指定的路徑加載模型權重。

        Args:
            model_path: 模型檔案的路徑。

        Returns:
            如果加載成功返回 True，否則返回 False。
        """
        pass

    @abstractmethod
    def save_model(self, model_path: str) -> bool:
        """
        將當前的模型權重保存到指定路徑。

        Args:
            model_path: 保存模型檔案的路徑。

        Returns:
            如果保存成功返回 True，否則返回 False。
        """
        pass
