"""
Phase 3: 跨算法遷移學習引擎

此模組實現強化學習算法間的知識遷移，提供 DQN → PPO → SAC 的智能遷移能力，
大幅減少訓練時間並提升模型性能。

核心功能：
- 算法間知識轉換
- 經驗重用機制
- 權重映射和轉換
- 遷移效果評估

Created for Phase 3: Algorithm Integration Optimization
"""

from .algorithm_migrator import AlgorithmMigrator, MigrationConfig, MigrationResult
from .knowledge_transfer import KnowledgeTransfer, TransferMethod, TransferMetrics
from .weight_converter import WeightConverter, ConversionStrategy, ConversionResult
from .migration_evaluator import MigrationEvaluator, EvaluationMetrics

__all__ = [
    "AlgorithmMigrator",
    "MigrationConfig", 
    "MigrationResult",
    "KnowledgeTransfer",
    "TransferMethod",
    "TransferMetrics",
    "WeightConverter",
    "ConversionStrategy",
    "ConversionResult",
    "MigrationEvaluator",
    "EvaluationMetrics"
]
