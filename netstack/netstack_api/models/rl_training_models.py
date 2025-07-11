"""
RL 訓練資料庫模型

定義強化學習訓練相關的資料庫模型，包括：
- 訓練會話 (rl_training_sessions)
- 訓練回合 (rl_training_episodes)
- 算法效能 (rl_algorithm_performance)
- 模型版本 (rl_model_versions)
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TrainingStatus(str, Enum):
    """訓練狀態枚舉"""

    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class AlgorithmType(str, Enum):
    """算法類型枚舉"""

    DQN = "dqn"
    PPO = "ppo"
    SAC = "sac"
    A2C = "a2c"
    DDPG = "ddpg"
    TD3 = "td3"


class EnvironmentType(str, Enum):
    """環境類型枚舉"""

    HANDOVER_SIMULATION = "handover_simulation"
    SATELLITE_NETWORK = "satellite_network"
    BEAM_SELECTION = "beam_selection"
    RESOURCE_ALLOCATION = "resource_allocation"
    CUSTOM = "custom"


class ModelStatus(str, Enum):
    """模型狀態枚舉"""

    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"
    FAILED = "failed"


# ===== 核心資料庫模型 =====


class RLTrainingSession(BaseModel):
    """RL 訓練會話模型 - 對應 rl_training_sessions 表"""

    session_id: str = Field(..., description="訓練會話唯一標識符")
    algorithm_type: AlgorithmType = Field(..., description="使用的算法類型")
    environment_type: EnvironmentType = Field(..., description="訓練環境類型")
    status: TrainingStatus = Field(
        default=TrainingStatus.PENDING, description="訓練狀態"
    )

    # 訓練配置
    total_episodes: int = Field(..., ge=1, description="總訓練回合數")
    episodes_completed: int = Field(default=0, description="已完成回合數")
    max_steps_per_episode: int = Field(default=1000, description="每回合最大步數")

    # 超參數配置
    hyperparameters: Dict[str, Any] = Field(
        default_factory=dict, description="算法超參數"
    )

    # 時間記錄
    start_time: datetime = Field(
        default_factory=datetime.now, description="訓練開始時間"
    )
    end_time: Optional[datetime] = Field(None, description="訓練結束時間")
    last_checkpoint_time: Optional[datetime] = Field(None, description="最後檢查點時間")

    # 效能指標
    current_reward: float = Field(default=0.0, description="當前平均獎勵")
    best_reward: float = Field(default=float("-inf"), description="最佳獎勵")
    average_reward: float = Field(default=0.0, description="平均獎勵")

    # 模型相關
    model_path: Optional[str] = Field(None, description="模型保存路徑")
    best_model_path: Optional[str] = Field(None, description="最佳模型路徑")

    # 訓練配置
    training_config: Dict[str, Any] = Field(
        default_factory=dict, description="訓練配置"
    )

    # 元數據
    created_by: str = Field(default="system", description="創建者")
    notes: Optional[str] = Field(None, description="備註")


class RLTrainingEpisode(BaseModel):
    """RL 訓練回合模型 - 對應 rl_training_episodes 表"""

    episode_id: str = Field(..., description="回合唯一標識符")
    session_id: str = Field(..., description="所屬訓練會話ID")
    episode_number: int = Field(..., ge=1, description="回合編號")

    # 回合結果
    total_reward: float = Field(..., description="總獎勵")
    episode_length: int = Field(..., ge=0, description="回合長度（步數）")
    success: bool = Field(default=False, description="是否成功完成")

    # 詳細指標
    metrics: Dict[str, Any] = Field(default_factory=dict, description="詳細指標")
    handover_count: int = Field(default=0, description="換手次數")
    average_latency: Optional[float] = Field(None, description="平均延遲")
    throughput: Optional[float] = Field(None, description="吞吐量")

    # 時間記錄
    start_time: datetime = Field(
        default_factory=datetime.now, description="回合開始時間"
    )
    end_time: Optional[datetime] = Field(None, description="回合結束時間")
    duration_seconds: Optional[float] = Field(None, description="持續時間（秒）")

    # 狀態和動作統計
    state_stats: Dict[str, Any] = Field(default_factory=dict, description="狀態統計")
    action_stats: Dict[str, Any] = Field(default_factory=dict, description="動作統計")

    # 學習進度
    exploration_rate: Optional[float] = Field(None, description="探索率")
    learning_rate: Optional[float] = Field(None, description="學習率")
    loss_value: Optional[float] = Field(None, description="損失值")


class RLAlgorithmPerformance(BaseModel):
    """RL 算法效能模型 - 對應 rl_algorithm_performance 表"""

    performance_id: str = Field(..., description="效能記錄唯一標識符")
    algorithm_type: AlgorithmType = Field(..., description="算法類型")
    environment_type: EnvironmentType = Field(..., description="環境類型")

    # 基本統計
    total_sessions: int = Field(default=0, description="總訓練會話數")
    successful_sessions: int = Field(default=0, description="成功會話數")
    average_episodes_to_converge: Optional[float] = Field(
        None, description="平均收斂回合數"
    )

    # 效能指標
    best_reward: float = Field(default=float("-inf"), description="最佳獎勵")
    average_reward: float = Field(default=0.0, description="平均獎勵")
    reward_variance: float = Field(default=0.0, description="獎勵方差")

    # 訓練效率
    average_training_time: float = Field(default=0.0, description="平均訓練時間（秒）")
    average_inference_time: float = Field(
        default=0.0, description="平均推理時間（毫秒）"
    )

    # 業務指標
    handover_success_rate: float = Field(default=0.0, description="換手成功率")
    average_handover_latency: float = Field(default=0.0, description="平均換手延遲")
    network_throughput_improvement: float = Field(
        default=0.0, description="網路吞吐量改善"
    )

    # 時間記錄
    last_updated: datetime = Field(
        default_factory=datetime.now, description="最後更新時間"
    )
    measurement_period_start: datetime = Field(
        default_factory=datetime.now, description="測量期間開始"
    )
    measurement_period_end: Optional[datetime] = Field(None, description="測量期間結束")


class RLModelVersion(BaseModel):
    """RL 模型版本模型 - 對應 rl_model_versions 表"""

    version_id: str = Field(..., description="版本唯一標識符")
    session_id: str = Field(..., description="訓練會話ID")
    algorithm_type: AlgorithmType = Field(..., description="算法類型")

    # 版本資訊
    version_number: str = Field(..., description="版本號")
    model_name: str = Field(..., description="模型名稱")
    status: ModelStatus = Field(default=ModelStatus.TRAINING, description="模型狀態")

    # 檔案資訊
    model_file_path: str = Field(..., description="模型檔案路徑")
    model_file_size: int = Field(..., ge=0, description="模型檔案大小（位元組）")
    model_checksum: Optional[str] = Field(None, description="模型檔案校驗和")

    # 效能指標
    validation_reward: float = Field(default=0.0, description="驗證獎勵")
    test_reward: float = Field(default=0.0, description="測試獎勵")
    model_accuracy: Optional[float] = Field(None, description="模型準確率")

    # 部署資訊
    deployed_at: Optional[datetime] = Field(None, description="部署時間")
    deployment_environment: Optional[str] = Field(None, description="部署環境")

    # 元數據
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    created_by: str = Field(default="system", description="創建者")
    description: Optional[str] = Field(None, description="模型描述")
    tags: List[str] = Field(default_factory=list, description="標籤")


class RLHyperparameterConfig(BaseModel):
    """RL 超參數配置模型"""

    config_id: str = Field(..., description="配置唯一標識符")
    algorithm_type: AlgorithmType = Field(..., description="算法類型")
    config_name: str = Field(..., description="配置名稱")

    # 超參數
    learning_rate: float = Field(default=0.001, description="學習率")
    batch_size: int = Field(default=32, description="批次大小")
    gamma: float = Field(default=0.99, description="折扣因子")
    epsilon: float = Field(default=1.0, description="探索率")
    epsilon_min: float = Field(default=0.01, description="最小探索率")
    epsilon_decay: float = Field(default=0.995, description="探索率衰減")

    # 網路架構
    hidden_layers: List[int] = Field(
        default_factory=lambda: [64, 64], description="隱藏層"
    )
    activation_function: str = Field(default="relu", description="激活函數")

    # 算法特定參數
    algorithm_specific_params: Dict[str, Any] = Field(
        default_factory=dict, description="算法特定參數"
    )

    # 元數據
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    is_default: bool = Field(default=False, description="是否為預設配置")
    description: Optional[str] = Field(None, description="配置描述")


# ===== 響應模型 =====


class TrainingSessionResponse(BaseModel):
    """訓練會話響應模型"""

    session_id: str
    algorithm_type: AlgorithmType
    environment_type: EnvironmentType
    status: TrainingStatus
    progress: float = Field(description="訓練進度 (0.0-1.0)")
    episodes_completed: int
    total_episodes: int
    current_reward: float
    best_reward: float
    start_time: datetime
    duration_seconds: Optional[float] = None


class TrainingEpisodeResponse(BaseModel):
    """訓練回合響應模型"""

    episode_id: str
    session_id: str
    episode_number: int
    total_reward: float
    episode_length: int
    success: bool
    duration_seconds: Optional[float] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class AlgorithmPerformanceResponse(BaseModel):
    """算法效能響應模型"""

    algorithm_type: AlgorithmType
    environment_type: EnvironmentType
    total_sessions: int
    success_rate: float
    best_reward: float
    average_reward: float
    average_training_time: float
    handover_success_rate: float
    last_updated: datetime


class ModelVersionResponse(BaseModel):
    """模型版本響應模型"""

    version_id: str
    algorithm_type: AlgorithmType
    version_number: str
    model_name: str
    status: ModelStatus
    validation_reward: float
    test_reward: float
    created_at: datetime
    file_size_mb: float = Field(description="檔案大小 (MB)")


# ===== 請求模型 =====


class StartTrainingRequest(BaseModel):
    """開始訓練請求"""

    algorithm_type: AlgorithmType
    environment_type: EnvironmentType = Field(
        default=EnvironmentType.HANDOVER_SIMULATION
    )
    total_episodes: int = Field(default=1000, ge=1, le=10000)
    max_steps_per_episode: int = Field(default=1000, ge=1)
    hyperparameters: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class UpdateTrainingRequest(BaseModel):
    """更新訓練請求"""

    status: Optional[TrainingStatus] = None
    notes: Optional[str] = None


class CreateModelVersionRequest(BaseModel):
    """創建模型版本請求"""

    model_name: str
    version_number: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class HyperparameterConfigRequest(BaseModel):
    """超參數配置請求"""

    algorithm_type: AlgorithmType
    config_name: str
    learning_rate: float = Field(default=0.001, gt=0)
    batch_size: int = Field(default=32, ge=1)
    gamma: float = Field(default=0.99, ge=0, le=1)
    epsilon: float = Field(default=1.0, ge=0, le=1)
    epsilon_min: float = Field(default=0.01, ge=0, le=1)
    epsilon_decay: float = Field(default=0.995, ge=0, le=1)
    hidden_layers: List[int] = Field(default_factory=lambda: [64, 64])
    activation_function: str = Field(default="relu")
    algorithm_specific_params: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
