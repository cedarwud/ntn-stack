#!/usr/bin/env python3
"""
Stage 4 時序預處理驗證器

移除虛假驗證，建立真實的業務邏輯驗證：
- 時序分析有效性檢查
- 覆蓋率分析驗證 (0% 覆蓋率 → FAILURE)
- 時間序列數據完整性驗證
- 處理結果合理性檢查

作者: Claude & Human
版本: v1.0 - 真實驗證系統
"""

import logging
from typing import Dict, Any, List
from .validation_engine import BaseValidator, ValidationResult, CheckResult, ValidationStatus

logger = logging.getLogger(__name__)

class Stage4TimeseriesValidator(BaseValidator):
    """Stage 4 時序預處理專用驗證器"""

    def __init__(self):
        super().__init__("stage4_timeseries_preprocessing")

    def validate(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> ValidationResult:
        """執行 Stage 4 驗證邏輯"""
        result = ValidationResult()

        # 1. 時序分析有效性檢查
        timeseries_check = self.validate_timeseries_analysis(output_data)
        result.add_check(timeseries_check)

        # 2. 覆蓋率分析驗證 (關鍵檢查)
        coverage_check = self.validate_coverage_analysis(input_data, output_data)
        result.add_check(coverage_check)

        # 3. 時間序列數據完整性
        data_integrity_check = self.validate_data_integrity(output_data)
        result.add_check(data_integrity_check)

        # 4. 處理統計準確性
        statistics_check = self.validate_processing_statistics(output_data)
        result.add_check(statistics_check)

        # 5. 衛星處理數量檢查
        processing_check = self.validate_satellites_processing(input_data, output_data)
        result.add_check(processing_check)

        return result

    def validate_timeseries_analysis(self, output_data: Dict[str, Any]) -> CheckResult:
        """驗證時序分析有效性"""
        try:
            timeseries_data = output_data.get('timeseries_data', {})

            if not timeseries_data:
                return CheckResult(
                    "timeseries_analysis_validity",
                    ValidationStatus.FAILURE,
                    "無時序數據，時序分析未執行"
                )

            satellites = timeseries_data.get('satellites', [])
            if not satellites:
                return CheckResult(
                    "timeseries_analysis_validity",
                    ValidationStatus.FAILURE,
                    "時序數據中無衛星信息"
                )

            # 檢查時序模式識別
            patterns_identified = 0
            for satellite in satellites:
                if satellite.get('timeseries_patterns'):
                    patterns_identified += 1

            pattern_ratio = patterns_identified / len(satellites) if satellites else 0
            if pattern_ratio < 0.1:  # 少於10%的衛星有時序模式
                return CheckResult(
                    "timeseries_pattern_failure",
                    ValidationStatus.FAILURE,
                    f"時序模式識別失敗: 僅{pattern_ratio:.1%}衛星有模式"
                )

            return CheckResult(
                "timeseries_analysis_validity",
                ValidationStatus.SUCCESS,
                f"時序分析有效: {len(satellites)}顆衛星，{pattern_ratio:.1%}有模式"
            )

        except Exception as e:
            return CheckResult(
                "timeseries_analysis_validity",
                ValidationStatus.FAILURE,
                f"時序分析驗證失敗: {e}"
            )

    def validate_coverage_analysis(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> CheckResult:
        """驗證覆蓋率分析 - 關鍵檢查"""
        try:
            coverage_analysis = output_data.get('coverage_analysis', {})

            if not coverage_analysis:
                return CheckResult(
                    "coverage_analysis_error",
                    ValidationStatus.FAILURE,
                    "無覆蓋率分析數據"
                )

            coverage_windows = coverage_analysis.get('coverage_windows', [])
            coverage_count = len(coverage_windows)

            # 關鍵檢查：0% 覆蓋率
            if coverage_count == 0:
                # 檢查是否有輸入衛星
                input_signal_data = input_data.get('signal_quality_data', [])
                if input_signal_data:
                    return CheckResult(
                        "zero_coverage_with_satellites",
                        ValidationStatus.FAILURE,
                        f"關鍵失敗: 有{len(input_signal_data)}顆衛星輸入但覆蓋率=0% - 覆蓋分析失效"
                    )
                else:
                    return CheckResult(
                        "zero_coverage_no_input",
                        ValidationStatus.FAILURE,
                        "無輸入衛星且覆蓋率=0% - 時序預處理未執行"
                    )

            # 檢查覆蓋率統計
            coverage_stats = coverage_analysis.get('coverage_statistics', {})
            coverage_ratio = coverage_stats.get('coverage_ratio', 0)

            if coverage_ratio == 0:
                return CheckResult(
                    "zero_coverage_ratio",
                    ValidationStatus.FAILURE,
                    f"覆蓋率統計異常: {coverage_count}個窗口但覆蓋率=0%"
                )

            return CheckResult(
                "coverage_analysis_validation",
                ValidationStatus.SUCCESS,
                f"覆蓋率分析正常: {coverage_count}個覆蓋窗口，覆蓋率{coverage_ratio:.1%}"
            )

        except Exception as e:
            return CheckResult(
                "coverage_analysis_validation",
                ValidationStatus.FAILURE,
                f"覆蓋率分析驗證失敗: {e}"
            )

    def validate_data_integrity(self, output_data: Dict[str, Any]) -> CheckResult:
        """驗證數據完整性"""
        try:
            timeseries_data = output_data.get('timeseries_data', {})

            if not timeseries_data:
                return CheckResult(
                    "data_integrity_check",
                    ValidationStatus.FAILURE,
                    "無時序數據，無法驗證完整性"
                )

            satellites = timeseries_data.get('satellites', [])
            if not satellites:
                return CheckResult(
                    "data_integrity_check",
                    ValidationStatus.WARNING,
                    "時序數據中無衛星信息"
                )

            # 檢查數據完整性
            integrity_issues = []
            for satellite in satellites:
                sat_id = satellite.get('satellite_id', 'unknown')

                # 檢查必要字段
                required_fields = ['satellite_id', 'position_timeseries']
                missing_fields = [field for field in required_fields if field not in satellite]

                if missing_fields:
                    integrity_issues.append(f"{sat_id}: 缺少字段 {missing_fields}")

                # 檢查時序數據長度
                timeseries = satellite.get('position_timeseries', [])
                if len(timeseries) < 5:  # 時序點太少
                    integrity_issues.append(f"{sat_id}: 時序點過少 ({len(timeseries)})")

            integrity_ratio = 1 - (len(integrity_issues) / len(satellites)) if satellites else 0
            if integrity_ratio < 0.8:
                return CheckResult(
                    "data_integrity_check",
                    ValidationStatus.FAILURE,
                    f"數據完整性不佳: {integrity_ratio:.1%}，{len(integrity_issues)}個問題"
                )

            return CheckResult(
                "data_integrity_check",
                ValidationStatus.SUCCESS,
                f"數據完整性良好: {integrity_ratio:.1%}完整"
            )

        except Exception as e:
            return CheckResult(
                "data_integrity_check",
                ValidationStatus.FAILURE,
                f"數據完整性檢查失敗: {e}"
            )

    def validate_processing_statistics(self, output_data: Dict[str, Any]) -> CheckResult:
        """驗證處理統計準確性"""
        try:
            statistics = output_data.get('statistics', {})

            if not statistics:
                return CheckResult(
                    "processing_statistics",
                    ValidationStatus.WARNING,
                    "無處理統計數據"
                )

            # 檢查統計數據合理性
            satellites_processed = statistics.get('satellites_processed', 0)
            timeseries_patterns = statistics.get('timeseries_patterns_identified', 0)
            coverage_windows = statistics.get('coverage_windows_analyzed', 0)

            # 邏輯一致性檢查
            if satellites_processed > 0:
                if timeseries_patterns == 0 and coverage_windows == 0:
                    return CheckResult(
                        "processing_statistics",
                        ValidationStatus.FAILURE,
                        f"統計不一致: 處理{satellites_processed}顆衛星但無模式和覆蓋分析"
                    )

            return CheckResult(
                "processing_statistics",
                ValidationStatus.SUCCESS,
                f"處理統計正常: {satellites_processed}顆衛星，{timeseries_patterns}個模式，{coverage_windows}個窗口"
            )

        except Exception as e:
            return CheckResult(
                "processing_statistics",
                ValidationStatus.FAILURE,
                f"處理統計驗證失敗: {e}"
            )

    def validate_satellites_processing(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> CheckResult:
        """驗證衛星處理數量"""
        try:
            # 獲取輸入衛星數量
            input_signal_data = input_data.get('signal_quality_data', [])
            input_count = len(input_signal_data)

            # 獲取輸出處理統計
            statistics = output_data.get('statistics', {})
            processed_count = statistics.get('satellites_processed', 0)

            # 關鍵檢查：0 顆衛星處理
            if processed_count == 0:
                if input_count > 0:
                    return CheckResult(
                        "zero_satellites_processing",
                        ValidationStatus.FAILURE,
                        f"關鍵失敗: 輸入{input_count}顆衛星但處理0顆 - 時序預處理完全失效"
                    )
                else:
                    return CheckResult(
                        "zero_satellites_processing",
                        ValidationStatus.FAILURE,
                        "無輸入衛星且無處理結果 - 時序預處理未執行"
                    )

            # 檢查處理效率
            if input_count > 0:
                processing_rate = processed_count / input_count
                if processing_rate < 0.5:  # 處理率過低
                    return CheckResult(
                        "satellites_processing_rate",
                        ValidationStatus.WARNING,
                        f"處理效率偏低: {processing_rate:.2%} ({input_count}→{processed_count})"
                    )

            return CheckResult(
                "satellites_processing",
                ValidationStatus.SUCCESS,
                f"衛星處理正常: {processed_count} 顆衛星完成時序預處理"
            )

        except Exception as e:
            return CheckResult(
                "satellites_processing",
                ValidationStatus.FAILURE,
                f"衛星處理數量檢查失敗: {e}"
            )