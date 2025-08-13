#!/usr/bin/env python3
"""
衛星服務模組 - Phase 0 Implementation

本模組包含 NTN Stack 中所有衛星相關的計算和分析功能，專注於 LEO 衛星換手研究。

主要組件:
- StarlinkTLEDownloader: 完整的 Starlink TLE 數據下載器
- SatellitePrefilter: 衛星候選預篩選器，大幅減少計算量
- OptimalTimeframeAnalyzer: 最佳時間段分析器，找出最佳換手時機
- FrontendDataFormatter: 前端數據源格式化器
- Phase0Integration: 完整的 Phase 0 集成系統

Usage:
    from netstack.src.services.satellite import Phase0Integration
    
    enhanced = EnhancedIntegration()
    results = await enhanced.run_complete_analysis(24.9441667, 121.3713889)
"""

from .starlink_tle_downloader import StarlinkTLEDownloader
from .satellite_prefilter import SatellitePrefilter, ObserverLocation
from .optimal_timeframe_analyzer import (
    OptimalTimeframeAnalyzer, 
    OptimalTimeframe, 
    SatelliteTrajectory,
    SatelliteTrajectoryPoint,
    VisibilityWindow
)
from .frontend_data_formatter import (
    FrontendDataFormatter,
    generate_optimal_timeframe_for_coordinates
)
from .starlink_data_downloader import StarlinkDataDownloader

__all__ = [
    # 核心類
    "StarlinkDataDownloader",
    "StarlinkTLEDownloader", 
    "SatellitePrefilter",
    "OptimalTimeframeAnalyzer",
    "FrontendDataFormatter",
    
    # 數據結構
    "ObserverLocation",
    "OptimalTimeframe",
    "SatelliteTrajectory", 
    "SatelliteTrajectoryPoint",
    "VisibilityWindow",
    
    # 便利函數
    "generate_optimal_timeframe_for_coordinates"
]

__version__ = "1.0.0"
__author__ = "NTN Stack Team"
__description__ = "Phase 0 Starlink 換手分析系統"