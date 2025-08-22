#!/usr/bin/env python3
"""
Shared Core 模組 - v3.1 數據血統追蹤版
=====================================

統一的核心服務模組，為六階段處理器提供共享功能：
- 觀測點配置服務
- 仰角門檻管理器
- 信號品質緩存
- 可見性檢查服務
- 數據模型
- 工具函數
- 🎯 數據血統追蹤管理器 (v3.1 新增)

v3.1 更新: 添加數據血統追蹤機制，確保數據來源可追蹤性
"""

__version__ = "3.1.0"
__author__ = "LEO Satellite Research Team"

# 導出主要服務
try:
    from .observer_config_service import get_ntpu_coordinates
    from .elevation_threshold_manager import get_elevation_threshold_manager
    from .signal_quality_cache import get_signal_quality_cache
    from .visibility_service import get_visibility_service, ObserverLocation
    from .data_models import *
    from .utils import setup_logger, calculate_distance_km
    # 🎯 v3.1 新增：數據血統追蹤管理器
    from .data_lineage_manager import (
        get_lineage_manager, 
        create_tle_data_source, 
        record_stage_processing,
        DataLineageManager,
        DataSource,
        ProcessingRecord,
        DataLineage
    )
    
    __all__ = [
        'get_ntpu_coordinates',
        'get_elevation_threshold_manager', 
        'get_signal_quality_cache',
        'get_visibility_service',
        'ObserverLocation',
        'setup_logger',
        'calculate_distance_km',
        # 🎯 v3.1 數據血統追蹤
        'get_lineage_manager',
        'create_tle_data_source',
        'record_stage_processing',
        'DataLineageManager',
        'DataSource',
        'ProcessingRecord',
        'DataLineage'
    ]
    
except ImportError as e:
    # 優雅降級 - 如果某些模組缺失，不影響整體導入
    import logging
    logging.warning(f"Shared Core 部分模組導入失敗: {e}")
    __all__ = []