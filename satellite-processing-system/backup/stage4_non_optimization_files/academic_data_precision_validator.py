"""
Academic Data Precision Validator - Stage 4 Timeseries Preprocessing
專門負責數據精度、格式完整性和時間序列完整性驗證
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class AcademicDataPrecisionValidator:
    """學術數據精度驗證器 - 專門處理數據精度和格式驗證"""

    def __init__(self, config: Optional[Dict] = None):
        """初始化數據精度驗證器"""
        self.logger = logging.getLogger(f"{__name__}.AcademicDataPrecisionValidator")

        # 精度標準配置
        self.precision_standards = {
            'rsrp_decimal_places': 1,      # RSRP精度要求 (小數點後1位)
            'elevation_decimal_places': 2,  # 仰角精度要求 (小數點後2位)
            'distance_decimal_places': 3,   # 距離精度要求 (小數點後3位)
            'doppler_decimal_places': 0,    # 都卜勒頻移精度要求 (整數)
            'snr_decimal_places': 1,        # SNR精度要求 (小數點後1位)
            'time_precision': 'millisecond' # 時間精度要求
        }

        # 數據格式標準
        self.format_standards = {
            'required_fields': ['rsrp_dbm', 'elevation_deg', 'range_km', 'timestamp'],
            'optional_fields': ['doppler_shift_hz', 'snr_db', 'signal_quality_grade'],
            'timeseries_min_length': 10,
            'timeseries_max_gap': 300.0  # 最大時間間隔 (秒)
        }

        # 驗證統計
        self.precision_statistics = {
            'total_validated': 0,
            'precision_violations': 0,
            'format_violations': 0,
            'integrity_violations': 0,
            'grade_a_compliant': 0
        }

        self.logger.info("✅ 學術數據精度驗證器初始化完成")

    def validate_data_precision(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證數據精度要求

        Args:
            timeseries_data: 時間序列數據

        Returns:
            精度驗證結果
        """
        self.logger.info("🔍 開始數據精度驗證...")

        validation_result = {
            'precision_compliant': True,
            'violations': [],
            'precision_scores': {},
            'recommendations': []
        }

        try:
            # 檢查衛星數據精度
            satellites = timeseries_data.get('satellites', [])

            for sat_idx, satellite in enumerate(satellites):
                sat_violations = self._validate_satellite_precision(satellite, sat_idx)
                if sat_violations:
                    validation_result['violations'].extend(sat_violations)
                    validation_result['precision_compliant'] = False

            # 檢查整體數據精度
            overall_score = self._calculate_precision_score(timeseries_data)
            validation_result['precision_scores']['overall'] = overall_score

            # 生成改善建議
            if not validation_result['precision_compliant']:
                validation_result['recommendations'] = self._generate_precision_recommendations(
                    validation_result['violations']
                )

            # 更新統計
            self.precision_statistics['total_validated'] += 1
            if not validation_result['precision_compliant']:
                self.precision_statistics['precision_violations'] += 1
            else:
                self.precision_statistics['grade_a_compliant'] += 1

            self.logger.info(f"✅ 數據精度驗證完成: {'通過' if validation_result['precision_compliant'] else '未通過'}")
            return validation_result

        except Exception as e:
            self.logger.error(f"數據精度驗證失敗: {e}")
            raise RuntimeError(f"數據精度驗證失敗: {e}")

    def _validate_satellite_precision(self, satellite: Dict[str, Any], sat_idx: int) -> List[Dict[str, Any]]:
        """驗證單個衛星的數據精度"""
        violations = []

        signal_timeseries = satellite.get('signal_timeseries', [])

        for time_idx, time_point in enumerate(signal_timeseries):
            # 檢查RSRP精度
            rsrp = time_point.get('rsrp_dbm')
            if rsrp is not None:
                decimal_places = self._count_decimal_places(rsrp)
                if decimal_places > self.precision_standards['rsrp_decimal_places']:
                    violations.append({
                        'type': 'precision_violation',
                        'field': 'rsrp_dbm',
                        'satellite_index': sat_idx,
                        'time_index': time_idx,
                        'value': rsrp,
                        'expected_precision': self.precision_standards['rsrp_decimal_places'],
                        'actual_precision': decimal_places,
                        'severity': 'high'
                    })

            # 檢查仰角精度
            elevation = time_point.get('elevation_deg')
            if elevation is not None:
                decimal_places = self._count_decimal_places(elevation)
                if decimal_places > self.precision_standards['elevation_decimal_places']:
                    violations.append({
                        'type': 'precision_violation',
                        'field': 'elevation_deg',
                        'satellite_index': sat_idx,
                        'time_index': time_idx,
                        'value': elevation,
                        'expected_precision': self.precision_standards['elevation_decimal_places'],
                        'actual_precision': decimal_places,
                        'severity': 'medium'
                    })

            # 檢查距離精度
            distance = time_point.get('range_km')
            if distance is not None:
                decimal_places = self._count_decimal_places(distance)
                if decimal_places > self.precision_standards['distance_decimal_places']:
                    violations.append({
                        'type': 'precision_violation',
                        'field': 'range_km',
                        'satellite_index': sat_idx,
                        'time_index': time_idx,
                        'value': distance,
                        'expected_precision': self.precision_standards['distance_decimal_places'],
                        'actual_precision': decimal_places,
                        'severity': 'medium'
                    })

        return violations

    def validate_timeseries_integrity(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證時間序列完整性

        Args:
            timeseries_data: 時間序列數據

        Returns:
            完整性驗證結果
        """
        self.logger.info("🔍 開始時間序列完整性驗證...")

        integrity_result = {
            'integrity_compliant': True,
            'violations': [],
            'completeness_scores': {},
            'recommendations': []
        }

        try:
            satellites = timeseries_data.get('satellites', [])

            for sat_idx, satellite in enumerate(satellites):
                # 檢查時間序列長度
                signal_timeseries = satellite.get('signal_timeseries', [])

                if len(signal_timeseries) < self.format_standards['timeseries_min_length']:
                    integrity_result['violations'].append({
                        'type': 'length_violation',
                        'satellite_index': sat_idx,
                        'actual_length': len(signal_timeseries),
                        'minimum_required': self.format_standards['timeseries_min_length'],
                        'severity': 'high'
                    })
                    integrity_result['integrity_compliant'] = False

                # 檢查時間間隔一致性
                time_gaps = self._check_time_gaps(signal_timeseries)
                for gap in time_gaps:
                    if gap['gap_seconds'] > self.format_standards['timeseries_max_gap']:
                        integrity_result['violations'].append({
                            'type': 'time_gap_violation',
                            'satellite_index': sat_idx,
                            'gap_start_index': gap['start_index'],
                            'gap_end_index': gap['end_index'],
                            'gap_seconds': gap['gap_seconds'],
                            'maximum_allowed': self.format_standards['timeseries_max_gap'],
                            'severity': 'medium'
                        })
                        integrity_result['integrity_compliant'] = False

                # 檢查必要字段完整性
                missing_fields = self._check_required_fields(signal_timeseries)
                if missing_fields:
                    integrity_result['violations'].append({
                        'type': 'missing_fields_violation',
                        'satellite_index': sat_idx,
                        'missing_fields': missing_fields,
                        'severity': 'high'
                    })
                    integrity_result['integrity_compliant'] = False

            # 計算完整性分數
            integrity_result['completeness_scores'] = self._calculate_completeness_scores(timeseries_data)

            # 更新統計
            if not integrity_result['integrity_compliant']:
                self.precision_statistics['integrity_violations'] += 1

            self.logger.info(f"✅ 時間序列完整性驗證完成: {'通過' if integrity_result['integrity_compliant'] else '未通過'}")
            return integrity_result

        except Exception as e:
            self.logger.error(f"時間序列完整性驗證失敗: {e}")
            raise RuntimeError(f"時間序列完整性驗證失敗: {e}")

    def _check_time_gaps(self, signal_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """檢查時間間隔"""
        gaps = []

        for i in range(len(signal_timeseries) - 1):
            current_time = signal_timeseries[i].get('timestamp')
            next_time = signal_timeseries[i + 1].get('timestamp')

            if current_time and next_time:
                try:
                    # 計算時間差
                    if isinstance(current_time, str):
                        current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                    else:
                        current_dt = current_time

                    if isinstance(next_time, str):
                        next_dt = datetime.fromisoformat(next_time.replace('Z', '+00:00'))
                    else:
                        next_dt = next_time

                    gap_seconds = (next_dt - current_dt).total_seconds()

                    if gap_seconds > self.format_standards['timeseries_max_gap']:
                        gaps.append({
                            'start_index': i,
                            'end_index': i + 1,
                            'gap_seconds': gap_seconds
                        })

                except Exception as e:
                    self.logger.debug(f"時間間隔計算失敗: {e}")
                    continue

        return gaps

    def _check_required_fields(self, signal_timeseries: List[Dict[str, Any]]) -> List[str]:
        """檢查必要字段"""
        missing_fields = set()

        for time_point in signal_timeseries:
            for required_field in self.format_standards['required_fields']:
                if required_field not in time_point or time_point[required_field] is None:
                    missing_fields.add(required_field)

        return list(missing_fields)

    def _calculate_precision_score(self, timeseries_data: Dict[str, Any]) -> float:
        """計算精度分數"""
        total_points = 0
        max_points = 0

        satellites = timeseries_data.get('satellites', [])

        for satellite in satellites:
            signal_timeseries = satellite.get('signal_timeseries', [])

            for time_point in signal_timeseries:
                # RSRP精度檢查
                rsrp = time_point.get('rsrp_dbm')
                if rsrp is not None:
                    max_points += 1
                    if self._count_decimal_places(rsrp) <= self.precision_standards['rsrp_decimal_places']:
                        total_points += 1

                # 仰角精度檢查
                elevation = time_point.get('elevation_deg')
                if elevation is not None:
                    max_points += 1
                    if self._count_decimal_places(elevation) <= self.precision_standards['elevation_decimal_places']:
                        total_points += 1

                # 距離精度檢查
                distance = time_point.get('range_km')
                if distance is not None:
                    max_points += 1
                    if self._count_decimal_places(distance) <= self.precision_standards['distance_decimal_places']:
                        total_points += 1

        return total_points / max_points if max_points > 0 else 1.0

    def _calculate_completeness_scores(self, timeseries_data: Dict[str, Any]) -> Dict[str, float]:
        """計算完整性分數"""
        scores = {}

        satellites = timeseries_data.get('satellites', [])

        if satellites:
            # 長度完整性分數
            length_scores = []
            for satellite in satellites:
                signal_timeseries = satellite.get('signal_timeseries', [])
                length_score = min(1.0, len(signal_timeseries) / self.format_standards['timeseries_min_length'])
                length_scores.append(length_score)

            scores['length_completeness'] = np.mean(length_scores)

            # 字段完整性分數
            field_scores = []
            for satellite in satellites:
                signal_timeseries = satellite.get('signal_timeseries', [])
                total_fields = len(self.format_standards['required_fields']) * len(signal_timeseries)
                missing_count = 0

                for time_point in signal_timeseries:
                    for required_field in self.format_standards['required_fields']:
                        if required_field not in time_point or time_point[required_field] is None:
                            missing_count += 1

                field_score = 1.0 - (missing_count / total_fields) if total_fields > 0 else 1.0
                field_scores.append(field_score)

            scores['field_completeness'] = np.mean(field_scores)
        else:
            scores['length_completeness'] = 0.0
            scores['field_completeness'] = 0.0

        return scores

    def _generate_precision_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """生成精度改善建議"""
        recommendations = []

        # 按字段類型分組違規
        field_violations = {}
        for violation in violations:
            field = violation.get('field', 'unknown')
            if field not in field_violations:
                field_violations[field] = 0
            field_violations[field] += 1

        for field, count in field_violations.items():
            if field == 'rsrp_dbm':
                recommendations.append(
                    f"RSRP值有{count}個精度違規，建議保持小數點後{self.precision_standards['rsrp_decimal_places']}位精度"
                )
            elif field == 'elevation_deg':
                recommendations.append(
                    f"仰角值有{count}個精度違規，建議保持小數點後{self.precision_standards['elevation_decimal_places']}位精度"
                )
            elif field == 'range_km':
                recommendations.append(
                    f"距離值有{count}個精度違規，建議保持小數點後{self.precision_standards['distance_decimal_places']}位精度"
                )

        return recommendations

    def _count_decimal_places(self, value: float) -> int:
        """計算小數點後位數"""
        if isinstance(value, int):
            return 0

        str_value = str(float(value))
        if 'e' in str_value.lower():
            # 科學記號格式
            return 0

        if '.' in str_value:
            return len(str_value.split('.')[1].rstrip('0'))
        else:
            return 0

    def get_precision_statistics(self) -> Dict[str, Any]:
        """獲取精度驗證統計"""
        return self.precision_statistics.copy()

    def get_precision_standards(self) -> Dict[str, Any]:
        """獲取精度標準配置"""
        return {
            'precision_standards': self.precision_standards,
            'format_standards': self.format_standards
        }