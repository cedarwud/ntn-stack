"""
測試基類

整合來源：
- tests/conftest.py (測試配置)
- 各Stage的測試模式

提供統一的測試基礎設施
"""

import unittest
import pytest
import logging
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import sys
import traceback


@dataclass
class TestMetrics:
    """測試指標"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    assertions_count: int = 0
    passed_assertions: int = 0
    failed_assertions: int = 0
    memory_usage_mb: float = 0.0
    errors: List[str] = field(default_factory=list)

    def success_rate(self) -> float:
        """測試成功率"""
        if self.assertions_count == 0:
            return 0.0
        return self.passed_assertions / self.assertions_count


@dataclass
class TestConfig:
    """測試配置"""
    test_name: str
    timeout_seconds: int = 30
    precision_tolerance: float = 1e-6
    enable_performance_tracking: bool = True
    enable_memory_tracking: bool = False
    log_level: str = "INFO"
    output_dir: Optional[Path] = None
    academic_compliance_check: bool = True


class BaseTestCase(unittest.TestCase):
    """測試基類"""

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.config: Optional[TestConfig] = None
        self.metrics = TestMetrics()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.temp_dirs: List[Path] = []

    def setUp(self):
        """測試前設置"""
        self.metrics.start_time = datetime.now(timezone.utc)
        self.metrics.assertions_count = 0
        self.metrics.passed_assertions = 0
        self.metrics.failed_assertions = 0
        self.metrics.errors = []

        # 設置默認配置
        if self.config is None:
            self.config = TestConfig(
                test_name=self.__class__.__name__,
                timeout_seconds=30,
                precision_tolerance=1e-6
            )

        # 設置日誌級別
        self.logger.setLevel(getattr(logging, self.config.log_level))

        self.logger.info(f"開始測試: {self.config.test_name}")

    def tearDown(self):
        """測試後清理"""
        self.metrics.end_time = datetime.now(timezone.utc)
        if self.metrics.start_time:
            duration = self.metrics.end_time - self.metrics.start_time
            self.metrics.duration_seconds = duration.total_seconds()

        # 清理臨時目錄
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception as e:
                self.logger.warning(f"清理臨時目錄失敗: {temp_dir}, error: {e}")

        self.logger.info(f"測試完成: {self.config.test_name}, "
                        f"耗時: {self.metrics.duration_seconds:.3f}秒, "
                        f"成功率: {self.metrics.success_rate():.1%}")

    def create_temp_dir(self) -> Path:
        """創建臨時目錄"""
        temp_dir = Path(tempfile.mkdtemp())
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def assertAlmostEqualWithTolerance(self, first, second, tolerance=None, msg=None):
        """帶容忍度的近似相等斷言"""
        if tolerance is None:
            tolerance = self.config.precision_tolerance

        try:
            if abs(first - second) <= tolerance:
                self.metrics.passed_assertions += 1
            else:
                self.metrics.failed_assertions += 1
                if msg is None:
                    msg = f"{first} and {second} not almost equal within tolerance {tolerance}"
                raise AssertionError(msg)
        except Exception as e:
            self.metrics.errors.append(str(e))
            raise
        finally:
            self.metrics.assertions_count += 1

    def assertValidRange(self, value, min_val, max_val, msg=None):
        """範圍驗證斷言"""
        try:
            if min_val <= value <= max_val:
                self.metrics.passed_assertions += 1
            else:
                self.metrics.failed_assertions += 1
                if msg is None:
                    msg = f"Value {value} not in range [{min_val}, {max_val}]"
                raise AssertionError(msg)
        except Exception as e:
            self.metrics.errors.append(str(e))
            raise
        finally:
            self.metrics.assertions_count += 1

    def assertDataQuality(self, data, quality_checks: Dict[str, Callable], msg=None):
        """數據品質斷言"""
        try:
            failed_checks = []
            for check_name, check_func in quality_checks.items():
                try:
                    if not check_func(data):
                        failed_checks.append(check_name)
                except Exception as e:
                    failed_checks.append(f"{check_name}: {str(e)}")

            if not failed_checks:
                self.metrics.passed_assertions += 1
            else:
                self.metrics.failed_assertions += 1
                if msg is None:
                    msg = f"Data quality checks failed: {', '.join(failed_checks)}"
                raise AssertionError(msg)
        except Exception as e:
            self.metrics.errors.append(str(e))
            raise
        finally:
            self.metrics.assertions_count += 1

    def assertAcademicCompliance(self, data_source: str, algorithm_description: str):
        """學術合規性斷言"""
        if not self.config.academic_compliance_check:
            return

        forbidden_patterns = [
            "mock", "fake", "random", "simulated",
            "simplified", "estimated", "假設", "模擬"
        ]

        violations = []
        for pattern in forbidden_patterns:
            if pattern.lower() in data_source.lower():
                violations.append(f"數據源包含禁用模式: {pattern}")
            if pattern.lower() in algorithm_description.lower():
                violations.append(f"算法描述包含禁用模式: {pattern}")

        if violations:
            self.fail(f"學術合規性檢查失敗: {'; '.join(violations)}")

    def measure_performance(self, func: Callable, *args, **kwargs):
        """性能測量裝飾器"""
        if not self.config.enable_performance_tracking:
            return func(*args, **kwargs)

        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            self.logger.info(f"函數 {func.__name__} 執行時間: {duration:.3f}秒")

    def run_with_timeout(self, func: Callable, timeout_seconds: Optional[int] = None):
        """帶超時的執行"""
        import signal

        if timeout_seconds is None:
            timeout_seconds = self.config.timeout_seconds

        def timeout_handler(signum, frame):
            raise TimeoutError(f"測試超時: {timeout_seconds}秒")

        # 設置超時
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        try:
            return func()
        finally:
            signal.alarm(0)  # 清除超時

    def get_test_metrics(self) -> TestMetrics:
        """獲取測試指標"""
        return self.metrics

    def save_test_report(self, output_path: Optional[Path] = None):
        """保存測試報告"""
        if output_path is None and self.config.output_dir:
            output_path = self.config.output_dir / f"{self.config.test_name}_report.json"

        if output_path:
            report = {
                'test_name': self.config.test_name,
                'start_time': self.metrics.start_time.isoformat() if self.metrics.start_time else None,
                'end_time': self.metrics.end_time.isoformat() if self.metrics.end_time else None,
                'duration_seconds': self.metrics.duration_seconds,
                'assertions_count': self.metrics.assertions_count,
                'passed_assertions': self.metrics.passed_assertions,
                'failed_assertions': self.metrics.failed_assertions,
                'success_rate': self.metrics.success_rate(),
                'errors': self.metrics.errors,
                'config': {
                    'timeout_seconds': self.config.timeout_seconds,
                    'precision_tolerance': self.config.precision_tolerance,
                    'academic_compliance_check': self.config.academic_compliance_check
                }
            }

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"測試報告已保存: {output_path}")


class StageTestCase(BaseTestCase):
    """階段測試基類"""

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.stage_number: Optional[int] = None
        self.stage_name: str = ""
        self.input_data: Optional[Any] = None
        self.expected_output: Optional[Any] = None

    def setUp(self):
        super().setUp()
        if self.stage_number:
            self.config.test_name = f"Stage{self.stage_number}_{self.stage_name}_Test"

    def assertStageOutput(self, actual_output, expected_fields: List[str], msg=None):
        """階段輸出斷言"""
        try:
            # 檢查輸出結構
            if not isinstance(actual_output, dict):
                raise AssertionError("階段輸出必須是字典格式")

            missing_fields = []
            for field in expected_fields:
                if field not in actual_output:
                    missing_fields.append(field)

            if missing_fields:
                if msg is None:
                    msg = f"輸出缺少必要字段: {', '.join(missing_fields)}"
                raise AssertionError(msg)

            self.metrics.passed_assertions += 1
        except Exception as e:
            self.metrics.failed_assertions += 1
            self.metrics.errors.append(str(e))
            raise
        finally:
            self.metrics.assertions_count += 1

    def assertProcessingTime(self, actual_time: float, max_time: float, msg=None):
        """處理時間斷言"""
        try:
            if actual_time <= max_time:
                self.metrics.passed_assertions += 1
            else:
                self.metrics.failed_assertions += 1
                if msg is None:
                    msg = f"處理時間 {actual_time:.3f}s 超過限制 {max_time:.3f}s"
                raise AssertionError(msg)
        except Exception as e:
            self.metrics.errors.append(str(e))
            raise
        finally:
            self.metrics.assertions_count += 1


class PerformanceTestCase(BaseTestCase):
    """性能測試基類"""

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.performance_baselines: Dict[str, float] = {}

    def setUp(self):
        super().setUp()
        self.config.enable_performance_tracking = True

    def assertPerformanceBenchmark(self, operation_name: str, actual_time: float,
                                 baseline_factor: float = 1.5, msg=None):
        """性能基準斷言"""
        baseline_time = self.performance_baselines.get(operation_name)

        if baseline_time is None:
            self.logger.warning(f"未找到操作 {operation_name} 的性能基準")
            return

        max_allowed_time = baseline_time * baseline_factor

        try:
            if actual_time <= max_allowed_time:
                self.metrics.passed_assertions += 1
                self.logger.info(f"性能測試通過: {operation_name}, "
                               f"實際: {actual_time:.3f}s, 基準: {baseline_time:.3f}s")
            else:
                self.metrics.failed_assertions += 1
                if msg is None:
                    msg = (f"性能回歸: {operation_name}, "
                          f"實際: {actual_time:.3f}s > 允許: {max_allowed_time:.3f}s "
                          f"(基準: {baseline_time:.3f}s × {baseline_factor})")
                raise AssertionError(msg)
        except Exception as e:
            self.metrics.errors.append(str(e))
            raise
        finally:
            self.metrics.assertions_count += 1

    def load_performance_baselines(self, baseline_file: Path):
        """載入性能基準"""
        try:
            if baseline_file.exists():
                with open(baseline_file, 'r') as f:
                    self.performance_baselines = json.load(f)
                self.logger.info(f"已載入性能基準: {baseline_file}")
        except Exception as e:
            self.logger.error(f"載入性能基準失敗: {e}")


class IntegrationTestCase(BaseTestCase):
    """集成測試基類"""

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.services: List[Any] = []

    def setUp(self):
        super().setUp()
        self.config.timeout_seconds = 120  # 集成測試需要更長時間

    def tearDown(self):
        # 停止所有服務
        for service in self.services:
            try:
                if hasattr(service, 'stop'):
                    service.stop()
            except Exception as e:
                self.logger.warning(f"停止服務失敗: {e}")

        super().tearDown()

    def start_service(self, service):
        """啟動服務"""
        try:
            if hasattr(service, 'start'):
                service.start()
                self.services.append(service)
                self.logger.info(f"服務已啟動: {service.__class__.__name__}")
        except Exception as e:
            self.logger.error(f"啟動服務失敗: {e}")
            raise

    def assertServiceHealth(self, service, msg=None):
        """服務健康檢查斷言"""
        try:
            if hasattr(service, 'health_check'):
                health_result = service.health_check()
                if health_result.get('healthy', False):
                    self.metrics.passed_assertions += 1
                else:
                    self.metrics.failed_assertions += 1
                    if msg is None:
                        msg = f"服務不健康: {service.__class__.__name__}"
                    raise AssertionError(msg)
            else:
                self.metrics.passed_assertions += 1  # 假設沒有健康檢查的服務是健康的
        except Exception as e:
            self.metrics.errors.append(str(e))
            raise
        finally:
            self.metrics.assertions_count += 1


# 便捷函數
def create_test_config(test_name: str, **kwargs) -> TestConfig:
    """便捷函數：創建測試配置"""
    return TestConfig(test_name=test_name, **kwargs)


def run_test_suite(test_classes: List[type], config: Optional[TestConfig] = None):
    """便捷函數：運行測試套件"""
    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0.0
    }