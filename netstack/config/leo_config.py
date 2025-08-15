#!/usr/bin/env python3
"""
LEO Restructure Configuration Management
P0.2: 統一配置系統整合
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import logging
import json
from pathlib import Path

# Import from existing unified configuration
try:
    from .unified_satellite_config import ObserverLocation, SelectionStrategy
except ImportError:
    # Fallback for direct execution
    from unified_satellite_config import ObserverLocation, SelectionStrategy

logger = logging.getLogger(__name__)

@dataclass
class TLELoaderConfig:
    """TLE Loader 配置"""
    data_sources: Dict[str, str] = field(default_factory=lambda: {
        'starlink_tle_url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink',
        'oneweb_tle_url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb'
    })
    calculation_params: Dict[str, Union[int, float]] = field(default_factory=lambda: {
        'time_range_minutes': 200,
        'time_resolution_seconds': 30
    })
    sample_limits: Optional[Dict[str, int]] = field(default_factory=lambda: {
        'starlink': 10,  # For ultra-fast mode
        'oneweb': 10     # For ultra-fast mode
    })

@dataclass
class SatelliteFilterConfig:
    """Satellite Filter 配置"""
    filtering_params: Dict[str, float] = field(default_factory=lambda: {
        'geographic_threshold': 60.0,
        'min_score_threshold': 70.0
    })
    ntpu_coordinates: Dict[str, float] = field(default_factory=lambda: {
        'latitude': 24.9441667,
        'longitude': 121.3713889
    })

@dataclass
class EventProcessorConfig:
    """Event Processor 配置 (3GPP NTN 事件分析)"""
    event_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'a4_neighbor_threshold_dbm': -100.0,
        'a5_serving_threshold_dbm': -110.0,
        'd2_serving_distance_km': 5000.0
    })
    signal_params: Dict[str, float] = field(default_factory=lambda: {
        'frequency_ghz': 12.0,
        'tx_power_dbm': 43.0
    })

@dataclass
class OptimizerConfig:
    """優化器配置 (動態池規劃)"""
    optimization_params: Dict[str, Union[int, float]] = field(default_factory=lambda: {
        'max_iterations': 5000,
        'initial_temperature': 1000.0,
        'cooling_rate': 0.95
    })
    targets: Dict[str, Union[int, tuple]] = field(default_factory=lambda: {
        'starlink_pool_size': 8085,  # 基於本地TLE數據實際值
        'oneweb_pool_size': 651,    # 基於本地TLE數據實際值
        'starlink_visible_range': (10, 15),
        'oneweb_visible_range': (3, 6)
    })

@dataclass
class ElevationThresholdConfig:
    """
    仰角門檻配置 - 基於 docs/satellite_handover_standards.md
    """
    starlink_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'preparation_trigger': 15.0,  # 預備觸發門檻
        'execution_threshold': 10.0,  # 執行門檻 (預設值)
        'critical_threshold': 5.0     # 臨界門檻
    })
    oneweb_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'preparation_trigger': 20.0,  # OneWeb較高門檻
        'execution_threshold': 15.0,
        'critical_threshold': 10.0
    })
    environmental_factors: Dict[str, float] = field(default_factory=lambda: {
        'open_area_multiplier': 1.0,      # 開闊地區
        'urban_area_multiplier': 1.1,     # 城市地區
        'mountainous_multiplier': 1.3,    # 山區
        'heavy_rain_multiplier': 1.4      # 強降雨
    })

@dataclass
class LEOConfig:
    """
    LEO Restructure 統一配置系統
    整合 leo_restructure 和 netstack 的配置需求
    """
    tle_loader: TLELoaderConfig = field(default_factory=TLELoaderConfig)
    satellite_filter: SatelliteFilterConfig = field(default_factory=SatelliteFilterConfig)
    event_processor: EventProcessorConfig = field(default_factory=EventProcessorConfig)
    optimizer: OptimizerConfig = field(default_factory=OptimizerConfig)
    elevation_thresholds: ElevationThresholdConfig = field(default_factory=ElevationThresholdConfig)
    
    # 運行模式控制
    ultra_fast_mode: bool = False
    fast_mode: bool = False
    production_mode: bool = True
    
    # 輸出控制
    output_dir: str = "/app/data"
    verbose_logging: bool = False

class LEOConfigManager:
    """LEO配置管理器"""
    
    def __init__(self, config: Optional[LEOConfig] = None):
        self.config = config or LEOConfig()
    
    def get_legacy_netstack_format(self) -> Dict[str, Any]:
        """
        轉換為舊版NetStack API兼容格式
        確保P0.3輸出格式對接順利
        """
        return {
            'observer': {
                'latitude': self.config.satellite_filter.ntpu_coordinates['latitude'],
                'longitude': self.config.satellite_filter.ntpu_coordinates['longitude']
            },
            'elevation_thresholds': {
                'starlink': {
                    'min_elevation': self.config.elevation_thresholds.starlink_thresholds['execution_threshold'],
                    'preparation_elevation': self.config.elevation_thresholds.starlink_thresholds['preparation_trigger'],
                    'critical_elevation': self.config.elevation_thresholds.starlink_thresholds['critical_threshold']
                },
                'oneweb': {
                    'min_elevation': self.config.elevation_thresholds.oneweb_thresholds['execution_threshold'],
                    'preparation_elevation': self.config.elevation_thresholds.oneweb_thresholds['preparation_trigger'],
                    'critical_elevation': self.config.elevation_thresholds.oneweb_thresholds['critical_threshold']
                }
            },
            'signal_thresholds': {
                'a4_neighbor_threshold_dbm': self.config.event_processor.event_thresholds['a4_neighbor_threshold_dbm'],
                'a5_serving_threshold_dbm': self.config.event_processor.event_thresholds['a5_serving_threshold_dbm'],
                'd2_serving_distance_km': self.config.event_processor.event_thresholds['d2_serving_distance_km']
            },
            'tle_sources': self.config.tle_loader.data_sources,
            'pool_targets': self.config.optimizer.targets
        }
    
    def get_leo_restructure_format(self) -> Dict[str, Any]:
        """
        轉換為LEO restructure系統原生格式
        """
        return {
            'tle_loader': {
                'data_sources': self.config.tle_loader.data_sources,
                'calculation_params': self.config.tle_loader.calculation_params,
                'sample_limits': self.config.tle_loader.sample_limits
            },
            'satellite_filter': {
                'filtering_params': self.config.satellite_filter.filtering_params,
                'ntpu_coordinates': self.config.satellite_filter.ntpu_coordinates
            },
            'event_processor': {
                'event_thresholds': self.config.event_processor.event_thresholds,
                'signal_params': self.config.event_processor.signal_params
            },
            'optimizer': {
                'optimization_params': self.config.optimizer.optimization_params,
                'targets': self.config.optimizer.targets
            }
        }
    
    def apply_mode_settings(self, ultra_fast: bool = False, fast: bool = False, 
                          production: bool = True):
        """應用運行模式設定"""
        self.config.ultra_fast_mode = ultra_fast
        self.config.fast_mode = fast
        self.config.production_mode = production
        
        if ultra_fast:
            # Ultra-fast mode: 限制衛星數量
            if not self.config.tle_loader.sample_limits:
                self.config.tle_loader.sample_limits = {}
            self.config.tle_loader.sample_limits.update({
                'starlink': 10,
                'oneweb': 10
            })
        elif fast:
            # Fast mode: 中等限制
            if not self.config.tle_loader.sample_limits:
                self.config.tle_loader.sample_limits = {}
            self.config.tle_loader.sample_limits.update({
                'starlink': 100,
                'oneweb': 50
            })
        else:
            # Production mode: 無限制
            self.config.tle_loader.sample_limits = None
    
    def to_json(self, file_path: Optional[str] = None) -> str:
        """導出為JSON格式"""
        config_dict = self.get_leo_restructure_format()
        json_str = json.dumps(config_dict, indent=2, ensure_ascii=False)
        
        if file_path:
            Path(file_path).write_text(json_str, encoding='utf-8')
            logger.info(f"Configuration saved to {file_path}")
        
        return json_str

def create_default_config() -> Dict[str, Any]:
    """
    創建預設配置 - 與leo_restructure兼容
    這是P0.2配置統一的核心函數
    """
    config_manager = LEOConfigManager()
    return config_manager.get_leo_restructure_format()

def create_netstack_compatible_config() -> Dict[str, Any]:
    """
    創建NetStack兼容配置 - 用於P0.3輸出格式對接
    """
    config_manager = LEOConfigManager()
    return config_manager.get_legacy_netstack_format()

def create_unified_config_manager(ultra_fast: bool = False, 
                                fast: bool = False, 
                                production: bool = True) -> LEOConfigManager:
    """
    創建統一配置管理器
    """
    manager = LEOConfigManager()
    manager.apply_mode_settings(ultra_fast, fast, production)
    return manager