"""
Stage 6 Persistence API - v2.0 模組化架構

按照 @docs/stages/stage6-persistence-api.md 重構實現，專注於：
- 數據持久化與存儲管理
- 多層快取策略（L1記憶體、L2 Redis、L3磁碟）
- RESTful API和GraphQL服務
- 實時WebSocket事件推送

v2.0 架構特色：
- 從44個檔案精簡到約10個核心檔案（75%減少）
- 統一存儲管理（替代8個分散的備份模組）
- 服務導向設計（專注於API服務和數據提供）
- 高性能快取和存儲策略

核心模組：
- StorageManager: 統一存儲管理
- CacheManager: 多層快取管理
- APIService: RESTful API服務
- WebSocketService: 實時數據推送
- Stage6PersistenceProcessor: 服務協調
"""

# 🎯 v2.0 核心模組（按照文檔架構）
from .storage_manager import StorageManager
from .cache_manager import CacheManager
from .api_service import APIService
from .websocket_service import WebSocketService
from .stage6_main_processor import Stage6PersistenceProcessor  # 重構後的主處理器

# 📦 向後相容性支援（將逐步淘汰）
try:
    from .pool_generation_engine import PoolGenerationEngine
    from .pool_optimization_engine import PoolOptimizationEngine
    from .coverage_validation_engine import CoverageValidationEngine
    from .scientific_validation_engine import ScientificValidationEngine
    LEGACY_COMPONENTS_AVAILABLE = True
except ImportError:
    LEGACY_COMPONENTS_AVAILABLE = False

# 🏭 工廠函數（推薦使用）
def create_stage6_processor(config=None):
    """
    創建 Stage 6 處理器的工廠函數

    Args:
        config: 配置字典（可選）

    Returns:
        Stage6PersistenceProcessor 實例
    """
    return Stage6PersistenceProcessor(config)

# 📋 導出列表（v2.0 精簡版）
__all__ = [
    # v2.0 核心模組
    "StorageManager",
    "CacheManager",
    "APIService",
    "WebSocketService",
    "Stage6PersistenceProcessor",
    # 工廠函數
    "create_stage6_processor",
    # 向後相容性
    "LEGACY_COMPONENTS_AVAILABLE"
]

# 📊 模組元數據
__version__ = "2.0.0"
__module_type__ = "persistence_api_processor"
__academic_grade__ = "A"
__architecture__ = "v2.0_modular_simplified"
__documentation__ = "@docs/stages/stage6-persistence-api.md"

# 🔧 相容性別名（逐步淘汰）
Stage6MainProcessor = Stage6PersistenceProcessor  # 向後相容性
