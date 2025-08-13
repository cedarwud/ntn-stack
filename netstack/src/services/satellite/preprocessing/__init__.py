"""
衛星預處理模組

本模組負責從大規模星座中智能選擇研究級衛星子集，
確保任何時刻都有 8-12 顆可見衛星，支援複雜換手決策研究。
"""

# 新的統一智能篩選系統
from .satellite_selector import IntelligentSatelliteSelector, SatelliteSelectionConfig
from .intelligent_satellite_filtering import UnifiedIntelligentSatelliteFilter, create_unified_intelligent_filter
from .orbital_grouping import OrbitalPlaneGrouper
from .phase_distribution import PhaseDistributionOptimizer
from .visibility_scoring import VisibilityScorer

__all__ = [
    'IntelligentSatelliteSelector',
    'SatelliteSelectionConfig',
    'UnifiedIntelligentSatelliteFilter',
    'create_unified_intelligent_filter',
    'OrbitalPlaneGrouper', 
    'PhaseDistributionOptimizer',
    'VisibilityScorer'
]