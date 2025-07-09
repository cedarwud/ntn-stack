"""
AI Decision Engine Migration Package
====================================

階段6：新舊系統串接與安全切換模組
"""

from .feature_flag_manager import (
    FeatureFlagManager,
    FeatureFlag,
    FeatureStatus,
    MigrationStep,
    get_feature_flag_manager,
    initialize_feature_flag_manager
)

from .api_proxy import (
    APIProxy,
    ProxyConfig,
    ProxyMetrics,
    get_api_proxy,
    initialize_api_proxy
)

from .orchestrator import (
    MigrationOrchestrator,
    MigrationPhase,
    MigrationResult,
    get_migration_orchestrator
)

__all__ = [
    "FeatureFlagManager",
    "FeatureFlag", 
    "FeatureStatus",
    "MigrationStep",
    "get_feature_flag_manager",
    "initialize_feature_flag_manager",
    "APIProxy",
    "ProxyConfig",
    "ProxyMetrics",
    "get_api_proxy",
    "initialize_api_proxy",
    "MigrationOrchestrator",
    "MigrationPhase",
    "MigrationResult",
    "get_migration_orchestrator"
]