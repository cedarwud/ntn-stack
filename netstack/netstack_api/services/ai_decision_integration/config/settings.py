"""
系統設置
========

管理 AI 決策引擎的所有配置參數。
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class EventProcessingConfig:
    """事件處理配置"""
    supported_events: List[str] = field(default_factory=lambda: ["A4", "D1", "D2", "T1"])
    validation_enabled: bool = True
    confidence_threshold: float = 0.7
    processing_timeout: float = 10.0
    
@dataclass
class CandidateSelectionConfig:
    """候選篩選配置"""
    max_candidates: int = 10
    elevation_threshold: float = 10.0  # 最小仰角 (度)
    signal_threshold: float = -100.0   # 最小信號強度 (dBm)
    load_threshold: float = 0.9        # 最大負載因子
    selection_timeout: float = 15.0
    scoring_weights: Dict[str, float] = field(default_factory=lambda: {
        "elevation": 0.3,
        "signal_strength": 0.3,
        "load_factor": 0.2,
        "distance": 0.1,
        "visibility_time": 0.1
    })

@dataclass
class RLDecisionConfig:
    """強化學習決策配置"""
    default_algorithm: str = "DQN"
    available_algorithms: List[str] = field(default_factory=lambda: ["DQN", "PPO", "SAC"])
    decision_timeout: float = 20.0
    confidence_threshold: float = 0.8
    model_update_interval: int = 100
    exploration_rate: float = 0.1
    
@dataclass
class ExecutionConfig:
    """執行配置"""
    execution_timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    rollback_enabled: bool = True
    history_limit: int = 1000

@dataclass
class VisualizationConfig:
    """視覺化配置"""
    websocket_enabled: bool = True
    animation_duration_ms: int = 5000
    update_interval_ms: int = 100
    max_concurrent_animations: int = 10
    
@dataclass
class RedisConfig:
    """Redis 配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = None
    connection_pool_size: int = 10
    key_prefix: str = "ntn:ai_decision:"

@dataclass
class MetricsConfig:
    """指標配置"""
    enabled: bool = True
    collection_interval: float = 1.0
    history_limit: int = 10000
    prometheus_enabled: bool = True
    prometheus_port: int = 8001

class Settings:
    """
    系統設置主類
    
    管理所有配置參數，支持環境變數覆蓋。
    """
    
    def __init__(self):
        """初始化設置"""
        # 基本配置
        self.debug = self._get_env_bool("DEBUG", False)
        self.log_level = self._get_env_str("LOG_LEVEL", "INFO")
        self.service_name = self._get_env_str("SERVICE_NAME", "ai-decision-engine")
        
        # 模組配置
        self.event_processing = EventProcessingConfig()
        self.candidate_selection = CandidateSelectionConfig()
        self.rl_decision = RLDecisionConfig()
        self.execution = ExecutionConfig()
        self.visualization = VisualizationConfig()
        self.redis = RedisConfig()
        self.metrics = MetricsConfig()
        
        # 從環境變數更新配置
        self._update_from_env()
        
        # 功能開關 (Feature Flags)
        self.feature_flags = self._load_feature_flags()
    
    def _update_from_env(self):
        """從環境變數更新配置"""
        # 事件處理配置
        if confidence_threshold := os.getenv("EVENT_CONFIDENCE_THRESHOLD"):
            self.event_processing.confidence_threshold = float(confidence_threshold)
        
        # 候選篩選配置
        if max_candidates := os.getenv("MAX_CANDIDATES"):
            self.candidate_selection.max_candidates = int(max_candidates)
        
        if elevation_threshold := os.getenv("ELEVATION_THRESHOLD"):
            self.candidate_selection.elevation_threshold = float(elevation_threshold)
        
        # RL 決策配置
        if default_algorithm := os.getenv("DEFAULT_RL_ALGORITHM"):
            self.rl_decision.default_algorithm = default_algorithm
        
        if decision_timeout := os.getenv("DECISION_TIMEOUT"):
            self.rl_decision.decision_timeout = float(decision_timeout)
        
        # Redis 配置
        self.redis.host = self._get_env_str("REDIS_HOST", self.redis.host)
        self.redis.port = self._get_env_int("REDIS_PORT", self.redis.port)
        self.redis.password = self._get_env_str("REDIS_PASSWORD", self.redis.password)
        
        # 指標配置
        self.metrics.enabled = self._get_env_bool("METRICS_ENABLED", self.metrics.enabled)
        self.metrics.prometheus_enabled = self._get_env_bool("PROMETHEUS_ENABLED", self.metrics.prometheus_enabled)
        self.metrics.prometheus_port = self._get_env_int("PROMETHEUS_PORT", self.metrics.prometheus_port)
    
    def _load_feature_flags(self) -> Dict[str, bool]:
        """載入功能開關"""
        return {
            "use_new_event_processor": self._get_env_bool("USE_NEW_EVENT_PROCESSOR", False),
            "use_new_candidate_selector": self._get_env_bool("USE_NEW_CANDIDATE_SELECTOR", False), 
            "use_new_rl_engine": self._get_env_bool("USE_NEW_RL_ENGINE", False),
            "use_new_executor": self._get_env_bool("USE_NEW_EXECUTOR", False),
            "enable_3d_visualization": self._get_env_bool("ENABLE_3D_VISUALIZATION", True),
            "enable_websocket_streaming": self._get_env_bool("ENABLE_WEBSOCKET_STREAMING", True),
            "enable_metrics_collection": self._get_env_bool("ENABLE_METRICS_COLLECTION", True),
            "enable_redis_caching": self._get_env_bool("ENABLE_REDIS_CACHING", True)
        }
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        檢查功能是否啟用
        
        Args:
            feature_name: 功能名稱
            
        Returns:
            bool: 是否啟用
        """
        return self.feature_flags.get(feature_name, False)
    
    def enable_feature(self, feature_name: str):
        """啟用功能"""
        self.feature_flags[feature_name] = True
    
    def disable_feature(self, feature_name: str):
        """禁用功能"""
        self.feature_flags[feature_name] = False
    
    def get_model_save_path(self) -> Path:
        """獲取模型保存路徑"""
        base_path = Path(self._get_env_str("MODEL_SAVE_PATH", "./models"))
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path
    
    def get_config_dict(self) -> Dict[str, Any]:
        """獲取配置字典"""
        return {
            "debug": self.debug,
            "log_level": self.log_level,
            "service_name": self.service_name,
            "event_processing": self.event_processing.__dict__,
            "candidate_selection": self.candidate_selection.__dict__,
            "rl_decision": self.rl_decision.__dict__,
            "execution": self.execution.__dict__,
            "visualization": self.visualization.__dict__,
            "redis": self.redis.__dict__,
            "metrics": self.metrics.__dict__,
            "feature_flags": self.feature_flags
        }
    
    @staticmethod
    def _get_env_str(key: str, default: str) -> str:
        """獲取字符串環境變數"""
        return os.getenv(key, default)
    
    @staticmethod 
    def _get_env_int(key: str, default: int) -> int:
        """獲取整數環境變數"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @staticmethod
    def _get_env_float(key: str, default: float) -> float:
        """獲取浮點數環境變數"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @staticmethod
    def _get_env_bool(key: str, default: bool) -> bool:
        """獲取布爾環境變數"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

# 全局設置實例
settings = Settings()