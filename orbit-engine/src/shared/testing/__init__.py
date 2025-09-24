"""
測試基礎設施模組

整合來源：
- tests/conftest.py (測試配置和工具)
- 各Stage的測試輔助函數
- 共同的測試工具和斷言

提供統一的測試基礎設施和工具集
"""

from .base_test import (
    TestMetrics,
    TestConfig,
    BaseTestCase,
    StageTestCase,
    PerformanceTestCase,
    IntegrationTestCase,
    create_test_config,
    run_test_suite
)

from .test_utils import (
    TestDataSpec,
    TestDataGenerator,
    TestFileManager,
    PerformanceMeasurer,
    MockDataService,
    TestAssertion,
    create_test_environment,
    generate_test_satellite_data,
    validate_test_data_academic_compliance
)

__all__ = [
    # 測試基類
    'TestMetrics',
    'TestConfig',
    'BaseTestCase',
    'StageTestCase',
    'PerformanceTestCase',
    'IntegrationTestCase',
    'create_test_config',
    'run_test_suite',

    # 測試工具
    'TestDataSpec',
    'TestDataGenerator',
    'TestFileManager',
    'PerformanceMeasurer',
    'MockDataService',
    'TestAssertion',
    'create_test_environment',
    'generate_test_satellite_data',
    'validate_test_data_academic_compliance'
]