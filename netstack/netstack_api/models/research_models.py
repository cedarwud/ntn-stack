"""
研究級 MongoDB 數據模型

專門為學術研究和訓練追蹤設計的高級數據結構
支援 todo.md 所需的決策透明化和訓練復現
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    """訓練狀態"""
    PLANNED = "planned"
    RUNNING = "running" 
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AlgorithmType(str, Enum):
    """算法類型"""
    DQN = "DQN"
    PPO = "PPO"
    SAC = "SAC"
    A3C = "A3C"
    DDPG = "DDPG"


class ScenarioType(str, Enum):
    """場景類型"""
    URBAN = "urban"
    SUBURBAN = "suburban"
    LOW_LATENCY = "low_latency"
    HIGH_THROUGHPUT = "high_throughput"
    MIXED = "mixed"


class DecisionConfidenceLevel(str, Enum):
    """決策信心度級別"""
    VERY_LOW = "very_low"     # < 0.3
    LOW = "low"               # 0.3 - 0.5
    MEDIUM = "medium"         # 0.5 - 0.7
    HIGH = "high"             # 0.7 - 0.9
    VERY_HIGH = "very_high"   # > 0.9


@dataclass
class ResearchMetadata:
    """研究元數據"""
    researcher: str
    institution: str
    project_id: str
    funding_source: Optional[str] = None
    ethics_approval: Optional[str] = None
    publication_intent: bool = False
    data_sharing_consent: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class ExperimentHyperparameters(BaseModel):
    """訓練超參數"""
    learning_rate: float = Field(ge=1e-6, le=1.0)
    batch_size: int = Field(ge=1, le=1024)
    episodes: int = Field(ge=1, le=100000)
    epsilon_start: float = Field(ge=0.0, le=1.0, default=1.0)
    epsilon_end: float = Field(ge=0.0, le=1.0, default=0.01)
    epsilon_decay: float = Field(ge=0.9, le=1.0, default=0.995)
    memory_size: int = Field(ge=1000, le=1000000, default=10000)
    target_update_frequency: int = Field(ge=1, le=10000, default=100)
    
    # 研究級參數
    random_seed: Optional[int] = None
    network_architecture: Dict[str, Any] = Field(default_factory=dict)
    optimization_algorithm: str = "Adam"
    gradient_clipping: Optional[float] = None
    weight_decay: Optional[float] = None


class SatelliteCandidate(BaseModel):
    """候選衛星詳細信息"""
    satellite_id: str
    position: Dict[str, float]  # {lat, lon, alt}
    velocity: Dict[str, float]  # {vx, vy, vz}
    
    # 信號品質指標
    rsrp: float = Field(description="參考信號接收功率 (dBm)")
    rsrq: float = Field(description="參考信號接收品質 (dB)")
    sinr: float = Field(description="信噪干擾比 (dB)")
    
    # 網路負載指標
    load_factor: float = Field(ge=0.0, le=1.0, description="負載因子")
    connected_users: int = Field(ge=0, description="已連接用戶數")
    throughput_capacity: float = Field(description="吞吐量容量 (Mbps)")
    
    # 預測指標
    handover_probability: float = Field(ge=0.0, le=1.0)
    connection_duration_estimate: float = Field(description="預估連接持續時間 (秒)")
    
    # 決策評分
    overall_score: float = Field(ge=0.0, le=100.0)
    score_breakdown: Dict[str, float] = Field(default_factory=dict)


class DecisionReasoning(BaseModel):
    """決策推理詳細記錄"""
    decision_factors: Dict[str, float] = Field(description="決策因子權重")
    candidate_rankings: List[Dict[str, Any]] = Field(description="候選排序詳情")
    
    # Algorithm Explainability
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    decision_tree_path: Optional[List[str]] = None
    attention_weights: Optional[Dict[str, float]] = None
    
    # 不確定性量化
    epistemic_uncertainty: Optional[float] = None
    aleatoric_uncertainty: Optional[float] = None
    
    # 對抗性分析
    robustness_score: Optional[float] = None
    sensitivity_analysis: Dict[str, float] = Field(default_factory=dict)


class RLExperimentSession(BaseModel):
    """研究級 RL 訓練會話"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_name: str
    
    # 基本配置
    algorithm_type: AlgorithmType
    scenario_type: ScenarioType
    hyperparameters: ExperimentHyperparameters
    
    # 研究元數據
    research_metadata: Optional[Dict[str, Any]] = None
    baseline_comparison: Optional[str] = None
    hypothesis: Optional[str] = None
    expected_outcomes: List[str] = Field(default_factory=list)
    
    # 訓練狀態
    status: ExperimentStatus = ExperimentStatus.PLANNED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_episodes: int = 0
    completed_episodes: int = 0
    
    # 性能指標
    current_avg_reward: float = 0.0
    best_avg_reward: float = float('-inf')
    convergence_episode: Optional[int] = None
    convergence_criteria_met: bool = False
    
    # 統計數據
    training_wall_time: float = 0.0  # 實際訓練時間
    total_steps: int = 0
    successful_handovers: int = 0
    failed_handovers: int = 0
    
    # 研究筆記
    research_notes: str = ""
    
    # 時間戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class RLTrainingEpisode(BaseModel):
    """詳細的訓練 episode 數據"""
    episode_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    episode_number: int
    
    # Episode 結果
    total_reward: float
    episode_length: int
    success_rate: float = Field(ge=0.0, le=1.0)
    
    # 性能指標
    handover_latency_ms: List[float] = Field(description="每次切換的延遲")
    avg_handover_latency: float
    throughput_mbps: List[float] = Field(description="每個時間步的吞吐量")
    avg_throughput: float
    
    # 決策統計
    total_decisions: int
    successful_handovers: int
    failed_handovers: int
    no_handover_decisions: int
    
    # 學習統計
    epsilon_value: float
    learning_rate_used: float
    loss_values: List[float] = Field(default_factory=list)
    q_values: List[float] = Field(default_factory=list)
    
    # 時間戳
    timestamp: datetime = Field(default_factory=datetime.now)


class RLDecisionAnalysis(BaseModel):
    """RL 決策分析數據（支援 Algorithm Explainability）"""
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    episode_number: int
    step_number: int
    
    # 環境狀態
    current_state: Dict[str, Any]
    available_actions: List[str]
    selected_action: str
    
    # 候選衛星詳情
    candidate_satellites: List[SatelliteCandidate]
    selected_satellite_id: Optional[str] = None
    
    # 決策推理
    decision_reasoning: DecisionReasoning
    confidence_level: DecisionConfidenceLevel
    decision_time_ms: float
    
    # 結果評估
    immediate_reward: float
    long_term_value_estimate: float
    actual_outcome_quality: Optional[float] = None
    
    # 時間戳
    timestamp: datetime = Field(default_factory=datetime.now)


class RLPerformanceMetrics(BaseModel):
    """RL 性能指標追蹤"""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    
    # 計算時間窗口
    window_start_episode: int
    window_end_episode: int
    episodes_in_window: int
    
    # 核心性能指標
    avg_reward: float
    reward_std: float
    max_reward: float
    min_reward: float
    
    # 切換性能
    avg_handover_success_rate: float
    avg_handover_latency_ms: float
    handover_efficiency_score: float
    
    # 網路性能
    avg_throughput_mbps: float
    avg_connection_stability: float
    network_utilization_efficiency: float
    
    # 學習進度
    convergence_indicator: float = Field(ge=0.0, le=1.0, description="收斂指標")
    learning_stability_score: float
    exploration_exploitation_ratio: float
    
    # 比較基準
    baseline_performance_ratio: Optional[float] = None
    improvement_over_random: float
    improvement_over_previous_window: Optional[float] = None
    
    # 統計顯著性
    confidence_interval_95: Dict[str, float] = Field(default_factory=dict)
    statistical_significance: Optional[Dict[str, Any]] = None
    
    # 時間戳
    calculated_at: datetime = Field(default_factory=datetime.now)


class ResearchDataExport(BaseModel):
    """研究數據匯出格式"""
    export_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    
    # 匯出配置
    export_format: str = Field(description="JSON, CSV, HDF5, etc.")
    include_raw_data: bool = True
    include_analysis: bool = True
    include_visualizations: bool = False
    
    # 數據匿名化
    anonymize_data: bool = False
    remove_timestamps: bool = False
    aggregate_level: str = "episode"  # episode, session, experiment
    
    # 匯出統計
    total_episodes: int
    total_decisions: int
    data_size_mb: float
    
    # 驗證
    data_integrity_hash: str
    export_schema_version: str = "1.0.0"
    
    # 時間戳
    exported_at: datetime = Field(default_factory=datetime.now)


# MongoDB 集合定義
RESEARCH_COLLECTIONS = {
    "rl_experiment_sessions": RLExperimentSession,
    "rl_training_episodes": RLTrainingEpisode,
    "rl_decision_analysis": RLDecisionAnalysis,
    "rl_performance_metrics": RLPerformanceMetrics,
    "research_data_exports": ResearchDataExport,
}


# 數據庫索引定義
RESEARCH_INDEXES = {
    "rl_experiment_sessions": [
        {"session_id": 1},
        {"algorithm_type": 1, "scenario_type": 1},
        {"status": 1, "created_at": -1},
        {"research_metadata.researcher": 1},
    ],
    "rl_training_episodes": [
        {"session_id": 1, "episode_number": 1},
        {"session_id": 1, "total_reward": -1},
        {"timestamp": -1},
    ],
    "rl_decision_analysis": [
        {"session_id": 1, "episode_number": 1, "step_number": 1},
        {"selected_satellite_id": 1},
        {"confidence_level": 1},
        {"timestamp": -1},
    ],
    "rl_performance_metrics": [
        {"session_id": 1, "window_end_episode": -1},
        {"avg_reward": -1},
        {"calculated_at": -1},
    ],
}