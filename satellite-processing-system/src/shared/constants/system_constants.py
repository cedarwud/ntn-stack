"""
系統常數定義

整合系統級配置常數，包括路徑、時間、處理參數等
"""

import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class SystemPaths:
    """系統路徑常數"""

    # 基礎路徑
    PROJECT_ROOT: str = "/home/sat/ntn-stack"
    SATELLITE_PROCESSING_ROOT: str = "/home/sat/ntn-stack/satellite-processing-system"

    # 數據路徑
    DATA_ROOT: str = "/app/data"
    TLE_DATA_PATH: str = "/app/data/tle_data"
    OUTPUT_ROOT: str = "/app/data/outputs"

    # Stage輸出路徑
    STAGE1_OUTPUT: str = "/app/data/tle_calculation_outputs"
    STAGE2_OUTPUT: str = "/app/data/intelligent_filtering_outputs"
    STAGE3_OUTPUT: str = "/app/data/signal_analysis_outputs"
    STAGE4_OUTPUT: str = "/app/data/timeseries_preprocessing_outputs"
    STAGE5_OUTPUT: str = "/app/data/data_integration_outputs"
    STAGE6_OUTPUT: str = "/app/data/dynamic_pool_planning_outputs"

    # 配置路徑
    CONFIG_ROOT: str = "/app/config"
    LOG_ROOT: str = "/app/logs"

    # 共享模組路徑
    SHARED_ROOT: str = "/home/sat/ntn-stack/satellite-processing-system/src/shared"

    @classmethod
    def ensure_paths_exist(cls) -> Dict[str, bool]:
        """確保所有必要路徑存在"""
        paths_status = {}

        for field_name, field_value in cls.__annotations__.items():
            if field_name.endswith('_PATH') or field_name.endswith('_ROOT') or field_name.endswith('_OUTPUT'):
                path_value = getattr(cls, field_name)
                try:
                    Path(path_value).mkdir(parents=True, exist_ok=True)
                    paths_status[field_name] = True
                except Exception:
                    paths_status[field_name] = False

        return paths_status


@dataclass
class ProcessingConstants:
    """處理參數常數"""

    # 時間相關
    DEFAULT_PREDICTION_HOURS: int = 24
    DEFAULT_TIME_STEP_MINUTES: int = 5
    MAX_PROCESSING_TIMEOUT_SECONDS: int = 300

    # 數據量限制
    MAX_SATELLITES_PER_BATCH: int = 10000
    MAX_TLE_RECORDS: int = 50000
    MAX_VISIBILITY_WINDOWS: int = 1000

    # 性能參數
    PARALLEL_WORKERS: int = 4
    CHUNK_SIZE: int = 100
    MEMORY_LIMIT_MB: int = 2048

    # 重試參數
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 1

    # 緩存參數
    CACHE_TTL_SECONDS: int = 3600
    MAX_CACHE_SIZE: int = 1000


@dataclass
class ValidationConstants:
    """驗證相關常數"""

    # 數據驗證閾值
    MIN_VISIBLE_SATELLITES: int = 1
    MIN_COVERAGE_PERCENTAGE: float = 0.1
    MIN_SIGNAL_QUALITY_SCORE: float = 0.3

    # 精度容忍度
    POSITION_TOLERANCE_KM: float = 1.0
    ANGLE_TOLERANCE_DEG: float = 0.1
    TIME_TOLERANCE_SECONDS: float = 1.0

    # 檢查參數
    ENABLE_STRICT_VALIDATION: bool = True
    ENABLE_ACADEMIC_COMPLIANCE: bool = True
    ENABLE_PHYSICS_VALIDATION: bool = True


@dataclass
class LoggingConstants:
    """日誌相關常數"""

    # 日誌級別
    DEFAULT_LOG_LEVEL: str = "INFO"
    DEBUG_LOG_LEVEL: str = "DEBUG"

    # 日誌格式
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEBUG_LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

    # 日誌檔案
    MAX_LOG_SIZE_MB: int = 10
    BACKUP_COUNT: int = 5

    # 性能日誌
    ENABLE_PERFORMANCE_LOGGING: bool = True
    PERFORMANCE_LOG_THRESHOLD_MS: float = 100.0


@dataclass
class NetworkConstants:
    """網路相關常數"""

    # API端點
    NETSTACK_BASE_URL: str = "http://localhost:8080"
    SIMWORLD_BASE_URL: str = "http://localhost:8888"

    # 超時設定
    DEFAULT_TIMEOUT_SECONDS: int = 30
    LONG_TIMEOUT_SECONDS: int = 120

    # 重試設定
    MAX_HTTP_RETRIES: int = 3
    HTTP_RETRY_BACKOFF: float = 1.0


class SystemConstantsManager:
    """系統常數管理器"""

    def __init__(self):
        self.paths = SystemPaths()
        self.processing = ProcessingConstants()
        self.validation = ValidationConstants()
        self.logging = LoggingConstants()
        self.network = NetworkConstants()

    def get_system_paths(self) -> SystemPaths:
        """獲取系統路徑常數"""
        return self.paths

    def get_processing_constants(self) -> ProcessingConstants:
        """獲取處理參數常數"""
        return self.processing

    def get_validation_constants(self) -> ValidationConstants:
        """獲取驗證相關常數"""
        return self.validation

    def get_logging_constants(self) -> LoggingConstants:
        """獲取日誌相關常數"""
        return self.logging

    def get_network_constants(self) -> NetworkConstants:
        """獲取網路相關常數"""
        return self.network

    def initialize_system_environment(self) -> Dict[str, Any]:
        """初始化系統環境"""
        result = {
            'paths_created': self.paths.ensure_paths_exist(),
            'environment_ready': True,
            'errors': []
        }

        # 檢查關鍵路徑
        critical_paths = [
            self.paths.DATA_ROOT,
            self.paths.OUTPUT_ROOT,
            self.paths.SHARED_ROOT
        ]

        for path in critical_paths:
            if not Path(path).exists():
                result['errors'].append(f"關鍵路徑不存在: {path}")
                result['environment_ready'] = False

        return result

    def get_stage_output_path(self, stage_number: int) -> str:
        """獲取指定Stage的輸出路徑"""
        stage_paths = {
            1: self.paths.STAGE1_OUTPUT,
            2: self.paths.STAGE2_OUTPUT,
            3: self.paths.STAGE3_OUTPUT,
            4: self.paths.STAGE4_OUTPUT,
            5: self.paths.STAGE5_OUTPUT,
            6: self.paths.STAGE6_OUTPUT
        }
        return stage_paths.get(stage_number, self.paths.OUTPUT_ROOT)

    def export_constants(self) -> Dict[str, Any]:
        """導出所有系統常數"""
        return {
            'system_paths': {
                'project_root': self.paths.PROJECT_ROOT,
                'satellite_processing_root': self.paths.SATELLITE_PROCESSING_ROOT,
                'data_root': self.paths.DATA_ROOT,
                'output_root': self.paths.OUTPUT_ROOT,
                'config_root': self.paths.CONFIG_ROOT,
                'log_root': self.paths.LOG_ROOT,
                'shared_root': self.paths.SHARED_ROOT,
                'stage_outputs': {
                    f'stage{i}': self.get_stage_output_path(i) for i in range(1, 7)
                }
            },
            'processing_constants': {
                'prediction_hours': self.processing.DEFAULT_PREDICTION_HOURS,
                'time_step_minutes': self.processing.DEFAULT_TIME_STEP_MINUTES,
                'max_processing_timeout': self.processing.MAX_PROCESSING_TIMEOUT_SECONDS,
                'max_satellites_per_batch': self.processing.MAX_SATELLITES_PER_BATCH,
                'parallel_workers': self.processing.PARALLEL_WORKERS,
                'chunk_size': self.processing.CHUNK_SIZE,
                'memory_limit_mb': self.processing.MEMORY_LIMIT_MB
            },
            'validation_constants': {
                'min_visible_satellites': self.validation.MIN_VISIBLE_SATELLITES,
                'min_coverage_percentage': self.validation.MIN_COVERAGE_PERCENTAGE,
                'min_signal_quality_score': self.validation.MIN_SIGNAL_QUALITY_SCORE,
                'position_tolerance_km': self.validation.POSITION_TOLERANCE_KM,
                'angle_tolerance_deg': self.validation.ANGLE_TOLERANCE_DEG,
                'enable_strict_validation': self.validation.ENABLE_STRICT_VALIDATION
            },
            'logging_constants': {
                'default_log_level': self.logging.DEFAULT_LOG_LEVEL,
                'log_format': self.logging.LOG_FORMAT,
                'max_log_size_mb': self.logging.MAX_LOG_SIZE_MB,
                'backup_count': self.logging.BACKUP_COUNT,
                'enable_performance_logging': self.logging.ENABLE_PERFORMANCE_LOGGING
            },
            'network_constants': {
                'netstack_base_url': self.network.NETSTACK_BASE_URL,
                'simworld_base_url': self.network.SIMWORLD_BASE_URL,
                'default_timeout': self.network.DEFAULT_TIMEOUT_SECONDS,
                'max_http_retries': self.network.MAX_HTTP_RETRIES
            }
        }


# 全局實例
_system_constants_instance = None


def get_system_constants() -> SystemConstantsManager:
    """獲取系統常數管理器實例 (單例模式)"""
    global _system_constants_instance
    if _system_constants_instance is None:
        _system_constants_instance = SystemConstantsManager()
    return _system_constants_instance


# 便捷訪問函數
def get_stage_output_path(stage_number: int) -> str:
    """便捷函數：獲取Stage輸出路徑"""
    return get_system_constants().get_stage_output_path(stage_number)


def get_data_root() -> str:
    """便捷函數：獲取數據根目錄"""
    return get_system_constants().get_system_paths().DATA_ROOT


def get_shared_root() -> str:
    """便捷函數：獲取共享模組根目錄"""
    return get_system_constants().get_system_paths().SHARED_ROOT


def initialize_environment() -> Dict[str, Any]:
    """便捷函數：初始化系統環境"""
    return get_system_constants().initialize_system_environment()


# 常用路徑的快速訪問
DATA_ROOT = SystemPaths.DATA_ROOT
OUTPUT_ROOT = SystemPaths.OUTPUT_ROOT
SHARED_ROOT = SystemPaths.SHARED_ROOT
PROJECT_ROOT = SystemPaths.PROJECT_ROOT