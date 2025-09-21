"""
統一常數模組

整合來源：
- stage3_signal_analysis/stage3_physics_constants.py (物理常數)
- stage6_dynamic_pool_planning/physics_calculation_engine.py (計算常數)
- 各Stage的配置常數

提供統一的常數訪問接口
"""

from .physics_constants import (
    PhysicsConstants,
    SignalConstants,
    ConstellationConstants,
    PhysicsConstantsManager,
    get_physics_constants,
    get_thermal_noise_floor,
    get_free_space_path_loss,
    get_constellation_params,
    get_signal_thresholds,
    SPEED_OF_LIGHT,
    EARTH_RADIUS,
    EARTH_GM,
    BOLTZMANN_CONSTANT
)

from .system_constants import (
    SystemPaths,
    ProcessingConstants,
    ValidationConstants,
    LoggingConstants,
    NetworkConstants,
    SystemConstantsManager,
    get_system_constants,
    get_stage_output_path,
    get_data_root,
    get_shared_root,
    initialize_environment,
    DATA_ROOT,
    OUTPUT_ROOT,
    SHARED_ROOT,
    PROJECT_ROOT
)

__all__ = [
    # 物理常數類
    'PhysicsConstants',
    'SignalConstants',
    'ConstellationConstants',
    'PhysicsConstantsManager',

    # 系統常數類
    'SystemPaths',
    'ProcessingConstants',
    'ValidationConstants',
    'LoggingConstants',
    'NetworkConstants',
    'SystemConstantsManager',

    # 管理器函數
    'get_physics_constants',
    'get_system_constants',

    # 物理計算便捷函數
    'get_thermal_noise_floor',
    'get_free_space_path_loss',
    'get_constellation_params',
    'get_signal_thresholds',

    # 系統路徑便捷函數
    'get_stage_output_path',
    'get_data_root',
    'get_shared_root',
    'initialize_environment',

    # 常用常數
    'SPEED_OF_LIGHT',
    'EARTH_RADIUS',
    'EARTH_GM',
    'BOLTZMANN_CONSTANT',
    'DATA_ROOT',
    'OUTPUT_ROOT',
    'SHARED_ROOT',
    'PROJECT_ROOT'
]