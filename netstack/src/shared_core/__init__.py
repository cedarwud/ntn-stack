#!/usr/bin/env python3
"""
Shared Core 模組 - UltraThink 修復
=====================================

統一的核心服務模組，為六階段處理器提供共享功能：
- 觀測點配置服務
- 仰角門檻管理器
- 信號品質緩存
- 可見性檢查服務
- 數據模型
- 工具函數

UltraThink 修復: 添加缺失的 __init__.py 文件
"""

__version__ = "3.0.0"
__author__ = "LEO Satellite Research Team"

# 導出主要服務
try:
    from .observer_config_service import get_ntpu_coordinates
    from .elevation_threshold_manager import get_elevation_threshold_manager
    from .signal_quality_cache import get_signal_quality_cache
    from .visibility_service import get_visibility_service, ObserverLocation
    from .data_models import *
    from .utils import setup_logger, calculate_distance_km
    
    __all__ = [
        'get_ntpu_coordinates',
        'get_elevation_threshold_manager', 
        'get_signal_quality_cache',
        'get_visibility_service',
        'ObserverLocation',
        'setup_logger',
        'calculate_distance_km'
    ]
    
except ImportError as e:
    # 優雅降級 - 如果某些模組缺失，不影響整體導入
    import logging
    logging.warning(f"Shared Core 部分模組導入失敗: {e}")
    __all__ = []