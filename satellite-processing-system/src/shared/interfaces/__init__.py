"""
接口定義模組

整合來源：
- shared/core_modules/stage_interface.py (階段接口)
- shared/core_modules/data_flow_protocol.py (數據流協議)
- 各種服務接口定義

提供統一的接口規範
"""

from .processor_interface import (
    ProcessingStatus,
    ProcessingMetrics,
    ProcessingResult,
    BaseProcessor,
    StageProcessor,
    DataProcessor,
    AnalysisProcessor,
    PredictionProcessor,
    ValidationProcessor,
    MonitoringProcessor,
    create_processing_result,
    create_success_result,
    create_error_result
)

from .data_interface import (
    DataFormat,
    DataSourceType,
    DataMetadata,
    DataPacket,
    DataReader,
    DataWriter,
    DataTransformer,
    DataSchema,
    DataValidator,
    DataRepository,
    DataFlowManager,
    create_data_packet,
    create_validation_result,
    estimate_data_size
)

from .service_interface import (
    ServiceStatus,
    ServiceType,
    ServiceMetrics,
    ServiceConfig,
    BaseService,
    MonitoringService,
    PredictionService,
    ValidationService,
    CalculationService,
    NotificationService,
    ServiceRegistry,
    create_service_config,
    create_health_check_result
)

__all__ = [
    # 處理器接口
    'ProcessingStatus',
    'ProcessingMetrics',
    'ProcessingResult',
    'BaseProcessor',
    'StageProcessor',
    'DataProcessor',
    'AnalysisProcessor',
    'PredictionProcessor',
    'ValidationProcessor',
    'MonitoringProcessor',
    'create_processing_result',
    'create_success_result',
    'create_error_result',

    # 數據接口
    'DataFormat',
    'DataSourceType',
    'DataMetadata',
    'DataPacket',
    'DataReader',
    'DataWriter',
    'DataTransformer',
    'DataSchema',
    'DataValidator',
    'DataRepository',
    'DataFlowManager',
    'create_data_packet',
    'create_validation_result',
    'estimate_data_size',

    # 服務接口
    'ServiceStatus',
    'ServiceType',
    'ServiceMetrics',
    'ServiceConfig',
    'BaseService',
    'MonitoringService',
    'PredictionService',
    'ValidationService',
    'CalculationService',
    'NotificationService',
    'ServiceRegistry',
    'create_service_config',
    'create_health_check_result'
]