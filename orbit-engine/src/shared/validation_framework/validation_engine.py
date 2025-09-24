#!/usr/bin/env python3
"""
驗證引擎框架 - 真實業務邏輯驗證系統

替代硬編碼 'passed' 狀態的虛假驗證，建立基於真實業務邏輯的動態驗證系統。

核心原則：
1. 驗證結果必須基於實際數據分析
2. 0顆衛星/0%覆蓋率 = FAILURE
3. 失敗必須提供具體的錯誤描述
4. 成功率基於真實檢查結果計算

作者: Claude & Human
版本: v1.0 - 真實驗證系統
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationStatus(Enum):
    """驗證狀態枚舉"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    WARNING = "WARNING"
    PENDING = "PENDING"

@dataclass
class CheckResult:
    """單個檢查結果"""
    check_name: str
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None

    @property
    def passed(self) -> bool:
        """檢查是否通過"""
        return self.status == ValidationStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'check_name': self.check_name,
            'status': self.status.value,
            'passed': self.passed,
            'message': self.message,
            'details': self.details or {}
        }

class ValidationResult:
    """驗證結果集合"""

    def __init__(self):
        self.checks: List[CheckResult] = []
        self.start_time = datetime.now(timezone.utc)
        self.end_time: Optional[datetime] = None

    def add_check(self, result: CheckResult):
        """添加檢查結果"""
        self.checks.append(result)

    def add_success(self, check_name: str, message: str, details: Optional[Dict] = None):
        """添加成功檢查"""
        self.add_check(CheckResult(check_name, ValidationStatus.SUCCESS, message, details))

    def add_failure(self, check_name: str, message: str, details: Optional[Dict] = None):
        """添加失敗檢查"""
        self.add_check(CheckResult(check_name, ValidationStatus.FAILURE, message, details))

    def add_warning(self, check_name: str, message: str, details: Optional[Dict] = None):
        """添加警告檢查"""
        self.add_check(CheckResult(check_name, ValidationStatus.WARNING, message, details))

    def finalize(self):
        """完成驗證"""
        self.end_time = datetime.now(timezone.utc)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if not self.checks:
            return 0.0
        return sum(1 for check in self.checks if check.passed) / len(self.checks)

    @property
    def passed_count(self) -> int:
        """通過的檢查數量"""
        return sum(1 for check in self.checks if check.passed)

    @property
    def failed_count(self) -> int:
        """失敗的檢查數量"""
        return sum(1 for check in self.checks if check.status == ValidationStatus.FAILURE)

    @property
    def overall_status(self) -> str:
        """整體狀態"""
        if not self.checks:
            return 'PENDING'
        return 'PASS' if self.success_rate >= 0.7 else 'FAIL'  # 70% 通過率門檻

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'validation_status': 'passed' if self.overall_status == 'PASS' else 'failed',
            'overall_status': self.overall_status,
            'success_rate': self.success_rate,
            'total_checks': len(self.checks),
            'passed_checks': self.passed_count,
            'failed_checks': self.failed_count,
            'checks_performed': [check.check_name for check in self.checks],
            'detailed_results': [check.to_dict() for check in self.checks],
            'timestamp': self.end_time.isoformat() if self.end_time else datetime.now(timezone.utc).isoformat()
        }

class BaseValidator(ABC):
    """基礎驗證器抽象類"""

    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def validate(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> ValidationResult:
        """執行驗證邏輯"""
        pass

class FailureCriteria:
    """動態失敗判定標準"""

    @staticmethod
    def evaluate_stage2(validation_results: List[CheckResult]) -> bool:
        """Stage 2 失敗判定"""
        critical_failures = [
            'zero_output_with_input',
            'elevation_threshold_violation',
            'coordinate_transformation_error'
        ]

        # 檢查關鍵失敗
        for result in validation_results:
            if any(failure in result.check_name for failure in critical_failures):
                if result.status == ValidationStatus.FAILURE:
                    return False  # 任何關鍵失敗都導致整體失敗

        # 計算成功率
        if not validation_results:
            return False

        success_rate = sum(1 for r in validation_results if r.passed) / len(validation_results)
        return success_rate >= 0.7  # 70% 通過率才算成功

    @staticmethod
    def evaluate_stage3(validation_results: List[CheckResult]) -> bool:
        """Stage 3 失敗判定"""
        critical_failures = [
            'zero_satellites_processed',
            'rsrp_range_violation',
            'signal_distance_inconsistency'
        ]

        # 檢查關鍵失敗
        for result in validation_results:
            if any(failure in result.check_name for failure in critical_failures):
                if result.status == ValidationStatus.FAILURE:
                    return False

        # 計算成功率
        if not validation_results:
            return False

        success_rate = sum(1 for r in validation_results if r.passed) / len(validation_results)
        return success_rate >= 0.75  # 75% 通過率

    @staticmethod
    def evaluate_stage4(validation_results: List[CheckResult]) -> bool:
        """Stage 4 失敗判定"""
        critical_failures = [
            'zero_coverage_with_satellites',
            'timeseries_pattern_failure',
            'coverage_analysis_error'
        ]

        # 檢查關鍵失敗
        for result in validation_results:
            if any(failure in result.check_name for failure in critical_failures):
                if result.status == ValidationStatus.FAILURE:
                    return False

        # 計算成功率
        if not validation_results:
            return False

        success_rate = sum(1 for r in validation_results if r.passed) / len(validation_results)
        return success_rate >= 0.75  # 75% 通過率

class ValidationEngine:
    """獨立的驗證引擎"""

    def __init__(self, stage_type: str):
        self.stage_type = stage_type
        self.validators: List[BaseValidator] = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def add_validator(self, validator: BaseValidator):
        """添加驗證器"""
        self.validators.append(validator)

    def validate(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> ValidationResult:
        """執行所有驗證邏輯"""
        result = ValidationResult()

        try:
            self.logger.info(f"🔍 開始 {self.stage_type} 驗證檢查")

            for validator in self.validators:
                try:
                    validator_result = validator.validate(input_data, output_data)
                    # 合併驗證結果
                    for check in validator_result.checks:
                        result.add_check(check)

                except Exception as e:
                    result.add_failure(
                        f"{validator.__class__.__name__}_error",
                        f"驗證器執行失敗: {e}"
                    )

            result.finalize()

            # 應用階段特定的失敗判定標準
            stage_passed = self._evaluate_stage_criteria(result.checks)
            if not stage_passed and result.overall_status == 'PASS':
                # 強制失敗如果不符合階段標準
                result.add_failure(
                    "stage_criteria_violation",
                    f"{self.stage_type} 階段特定標準未達成"
                )

            self.logger.info(f"✅ {self.stage_type} 驗證完成: {result.overall_status}")
            return result

        except Exception as e:
            self.logger.error(f"❌ {self.stage_type} 驗證引擎失敗: {e}")
            result.add_failure("validation_engine_error", f"驗證引擎執行失敗: {e}")
            result.finalize()
            return result

    def _evaluate_stage_criteria(self, checks: List[CheckResult]) -> bool:
        """評估階段特定標準"""
        if self.stage_type == 'stage2':
            return FailureCriteria.evaluate_stage2(checks)
        elif self.stage_type == 'stage3':
            return FailureCriteria.evaluate_stage3(checks)
        elif self.stage_type == 'stage4':
            return FailureCriteria.evaluate_stage4(checks)
        else:
            # 默認使用成功率判定
            if not checks:
                return False
            success_rate = sum(1 for check in checks if check.passed) / len(checks)
            return success_rate >= 0.7

class ValidationRegistry:
    """驗證引擎註冊表"""

    _engines: Dict[str, ValidationEngine] = {}

    @classmethod
    def register_engine(cls, stage_type: str, engine: ValidationEngine):
        """註冊驗證引擎"""
        cls._engines[stage_type] = engine

    @classmethod
    def get_engine(cls, stage_type: str) -> Optional[ValidationEngine]:
        """獲取驗證引擎"""
        return cls._engines.get(stage_type)

    @classmethod
    def create_engine(cls, stage_type: str) -> ValidationEngine:
        """創建並註冊驗證引擎"""
        engine = ValidationEngine(stage_type)
        cls.register_engine(stage_type, engine)
        return engine