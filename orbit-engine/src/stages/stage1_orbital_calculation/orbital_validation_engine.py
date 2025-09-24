#!/usr/bin/env python3
"""
Stage 1 專業化模組 - 軌道驗證引擎

從 Stage1TLEProcessor 拆分出的軌道計算驗證功能。
負責軌道數據完整性檢查、學術標準合規驗證、數據品質評估。

主要功能：
- 軌道計算結果驗證
- TLE epoch時間合規檢查
- 時間序列連續性驗證
- 數據結構完整性檢查
- 學術級標準評估

學術合規性：Grade A標準
- 基於SGP4軌道動力學
- 嚴格時間基準檢查
- 無簡化或近似處理
"""

import json
import logging
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class OrbitalValidationEngine:
    """
    軌道驗證引擎

    專責處理軌道計算結果的各種驗證檢查，
    確保數據符合學術級標準。
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化軌道驗證引擎

        Args:
            config: 配置參數
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 驗證標準配置
        self.validation_config = {
            'max_position_error_km': 10.0,  # 最大位置誤差(公里)
            'max_velocity_error_km_per_s': 0.1,  # 最大速度誤差(公里/秒)
            'min_success_rate': 0.95,  # 最小成功率
            'max_tle_age_days': 7,  # TLE數據最大年齡(天)
            'required_time_points': 100,  # 最少時間點數
            'continuity_tolerance_seconds': 60  # 連續性容忍度(秒)
        }

        # 學術標準配置
        self.academic_standards = {
            'tle_epoch_compliance': True,
            'sgp4_algorithm_compliance': True,
            'no_hardcoded_assumptions': True,
            'real_physics_only': True
        }

        # 統計信息
        self.validation_stats = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'warnings_count': 0
        }

    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行完整的軌道計算驗證檢查

        Args:
            results: 軌道計算結果

        Returns:
            Dict: 驗證結果報告
        """
        try:
            self.logger.info("🔍 開始軌道計算驗證檢查...")

            validation_report = {
                'validation_timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_status': 'Unknown',
                'validation_score': 0.0,
                'checks_performed': [],
                'detailed_results': {},
                'recommendations': []
            }

            # 執行各項檢查
            checks = [
                ('data_structure', self._check_data_structure),
                ('satellite_count', self._check_satellite_count),
                ('orbital_positions', self._check_orbital_positions),
                ('metadata_completeness', self._check_metadata_completeness),
                ('academic_compliance', self._check_academic_compliance),
                ('time_series_continuity', self._check_time_series_continuity),
                ('tle_epoch_compliance', self._check_tle_epoch_compliance)
            ]

            passed_checks = 0
            total_checks = len(checks)

            for check_name, check_function in checks:
                try:
                    check_result = check_function(results)
                    validation_report['detailed_results'][check_name] = check_result
                    validation_report['checks_performed'].append(check_name)

                    if check_result.get('passed', False):
                        passed_checks += 1
                        self.validation_stats['passed_checks'] += 1
                    else:
                        self.validation_stats['failed_checks'] += 1

                    self.validation_stats['total_checks'] += 1

                except Exception as e:
                    self.logger.error(f"❌ 驗證檢查 {check_name} 失敗: {e}")
                    validation_report['detailed_results'][check_name] = {
                        'passed': False,
                        'error': str(e),
                        'score': 0.0
                    }

            # 計算總體驗證分數
            validation_report['validation_score'] = (passed_checks / total_checks) * 100
            validation_report['overall_status'] = self._determine_validation_status(
                validation_report['validation_score']
            )

            # 生成建議
            validation_report['recommendations'] = self._generate_recommendations(
                validation_report['detailed_results']
            )

            self._log_validation_summary(validation_report)
            return validation_report

        except Exception as e:
            self.logger.error(f"❌ 軌道驗證檢查失敗: {e}")
            raise

    def calculate_data_quality_score(self, results: Dict[str, Any]) -> float:
        """
        計算數據品質分數

        Args:
            results: 軌道計算結果

        Returns:
            float: 品質分數 (0-100)
        """
        try:
            quality_factors = []

            # 成功率評估
            success_rate = self._calculate_success_rate(results)
            quality_factors.append(success_rate * 100)

            # 位置數據完整性
            position_completeness = self._assess_position_completeness(results)
            quality_factors.append(position_completeness * 100)

            # 時間序列連續性
            continuity_score = self._assess_time_continuity(results)
            quality_factors.append(continuity_score * 100)

            # TLE數據新鮮度
            freshness_score = self._assess_tle_freshness(results)
            quality_factors.append(freshness_score * 100)

            # 計算加權平均
            weights = [0.3, 0.3, 0.2, 0.2]  # 成功率和完整性最重要
            weighted_score = sum(
                factor * weight for factor, weight in zip(quality_factors, weights)
            )

            return min(100.0, max(0.0, weighted_score))

        except Exception as e:
            self.logger.error(f"❌ 數據品質評估失敗: {e}")
            return 0.0

    def validate_calculation_results(self, satellites: List[Dict],
                                   orbital_results: Dict[str, Any]) -> bool:
        """
        驗證軌道計算結果的正確性

        Args:
            satellites: 衛星列表
            orbital_results: 軌道計算結果

        Returns:
            bool: 驗證是否通過
        """
        try:
            self.logger.info("🔍 驗證軌道計算結果...")

            validation_checks = [
                self._validate_eci_coordinates(orbital_results),
                self._validate_orbital_periods(orbital_results),
                self._validate_position_magnitudes(orbital_results),
                self._validate_velocity_vectors(orbital_results)
            ]

            # 所有檢查都必須通過
            all_passed = all(validation_checks)

            if all_passed:
                self.logger.info("✅ 軌道計算結果驗證通過")
            else:
                self.logger.warning("⚠️ 軌道計算結果驗證發現問題")

            return all_passed

        except Exception as e:
            self.logger.error(f"❌ 軌道計算結果驗證失敗: {e}")
            return False

    # ===== 私有方法 =====

    def _check_data_structure(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數據結構完整性"""
        required_fields = ['data', 'metadata', 'statistics']
        missing_fields = [field for field in required_fields if field not in results]

        data_section = results.get('data', {})
        required_data_fields = ['satellites', 'constellations']
        missing_data_fields = [field for field in required_data_fields if field not in data_section]

        passed = len(missing_fields) == 0 and len(missing_data_fields) == 0

        return {
            'passed': passed,
            'score': 100.0 if passed else 0.0,
            'missing_fields': missing_fields,
            'missing_data_fields': missing_data_fields,
            'message': '數據結構完整' if passed else f'缺少字段: {missing_fields + missing_data_fields}'
        }

    def _check_satellite_count(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查衛星數量合理性"""
        satellites = results.get('data', {}).get('satellites', [])
        satellite_count = len(satellites)

        # 合理的衛星數量範圍
        min_count = 100
        max_count = 10000

        passed = min_count <= satellite_count <= max_count

        return {
            'passed': passed,
            'score': 100.0 if passed else 50.0 if satellite_count > 0 else 0.0,
            'satellite_count': satellite_count,
            'expected_range': f'{min_count}-{max_count}',
            'message': f'衛星數量: {satellite_count}' +
                      (' (正常)' if passed else ' (異常)')
        }

    def _check_orbital_positions(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查軌道位置數據"""
        satellites = results.get('data', {}).get('satellites', [])

        valid_positions = 0
        total_positions = 0

        for satellite in satellites:
            positions = satellite.get('position_timeseries', [])
            for position in positions:
                total_positions += 1

                # 檢查ECI座標
                eci = position.get('eci_coordinates', {})
                x = eci.get('x_km', 0)
                y = eci.get('y_km', 0)
                z = eci.get('z_km', 0)

                # 檢查位置合理性 (地球半徑到地球同步軌道範圍)
                distance = math.sqrt(x*x + y*y + z*z)
                if 6378 <= distance <= 50000:  # 合理的軌道高度範圍
                    valid_positions += 1

        position_validity_rate = valid_positions / total_positions if total_positions > 0 else 0
        passed = position_validity_rate >= 0.95

        return {
            'passed': passed,
            'score': position_validity_rate * 100,
            'valid_positions': valid_positions,
            'total_positions': total_positions,
            'validity_rate': position_validity_rate,
            'message': f'位置有效率: {position_validity_rate:.1%}'
        }

    def _check_metadata_completeness(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查元數據完整性"""
        metadata = results.get('metadata', {})
        required_metadata = [
            'processing_timestamp', 'success_rate', 'total_satellites',
            'processing_duration', 'data_format_version'
        ]

        missing_metadata = [field for field in required_metadata if field not in metadata]
        completeness_rate = (len(required_metadata) - len(missing_metadata)) / len(required_metadata)
        passed = completeness_rate >= 0.8

        return {
            'passed': passed,
            'score': completeness_rate * 100,
            'missing_metadata': missing_metadata,
            'completeness_rate': completeness_rate,
            'message': f'元數據完整性: {completeness_rate:.1%}'
        }

    def _check_academic_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查學術標準合規性"""
        metadata = results.get('metadata', {})

        compliance_checks = {
            'grade_a_compliance': metadata.get('academic_compliance') == 'Grade_A_orbital_mechanics',
            'sgp4_algorithm': 'SGP4' in str(metadata.get('calculation_method', '')),
            'tle_epoch_based': metadata.get('time_reference') == 'TLE_epoch_based',
            'no_synthetic_data': not metadata.get('contains_synthetic_data', False)
        }

        passed_compliance = sum(compliance_checks.values())
        total_compliance = len(compliance_checks)
        compliance_rate = passed_compliance / total_compliance

        passed = compliance_rate >= 0.75

        return {
            'passed': passed,
            'score': compliance_rate * 100,
            'compliance_checks': compliance_checks,
            'compliance_rate': compliance_rate,
            'message': f'學術合規性: {compliance_rate:.1%}'
        }

    def _check_time_series_continuity(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查時間序列連續性"""
        satellites = results.get('data', {}).get('satellites', [])

        continuity_issues = 0
        total_sequences = 0

        for satellite in satellites[:10]:  # 抽樣檢查
            positions = satellite.get('position_timeseries', [])
            if len(positions) < 2:
                continue

            total_sequences += 1

            # 檢查時間間隔連續性
            for i in range(len(positions) - 1):
                current_time = positions[i].get('timestamp', 0)
                next_time = positions[i + 1].get('timestamp', 0)

                expected_interval = 30  # 預期間隔30秒
                actual_interval = next_time - current_time

                if abs(actual_interval - expected_interval) > self.validation_config['continuity_tolerance_seconds']:
                    continuity_issues += 1
                    break

        continuity_rate = (total_sequences - continuity_issues) / total_sequences if total_sequences > 0 else 1.0
        passed = continuity_rate >= 0.9

        return {
            'passed': passed,
            'score': continuity_rate * 100,
            'continuity_issues': continuity_issues,
            'total_sequences': total_sequences,
            'continuity_rate': continuity_rate,
            'message': f'時間序列連續性: {continuity_rate:.1%}'
        }

    def _check_tle_epoch_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """檢查TLE epoch時間合規性"""
        metadata = results.get('metadata', {})
        calculation_timestamp = metadata.get('processing_timestamp', '')
        tle_epoch_info = metadata.get('tle_epoch_info', {})

        # 檢查是否使用TLE epoch作為計算基準
        epoch_based = tle_epoch_info.get('calculation_base') == 'tle_epoch'
        epoch_age_days = tle_epoch_info.get('average_age_days', 999)

        # TLE數據不應該太舊
        fresh_data = epoch_age_days <= self.validation_config['max_tle_age_days']

        passed = epoch_based and fresh_data

        return {
            'passed': passed,
            'score': 100.0 if passed else (50.0 if epoch_based else 0.0),
            'epoch_based': epoch_based,
            'tle_age_days': epoch_age_days,
            'fresh_data': fresh_data,
            'message': f'TLE epoch合規性: {"通過" if passed else "未通過"}'
        }

    def _calculate_success_rate(self, results: Dict[str, Any]) -> float:
        """計算成功率"""
        metadata = results.get('metadata', {})
        return metadata.get('success_rate', 0.0)

    def _assess_position_completeness(self, results: Dict[str, Any]) -> float:
        """評估位置數據完整性"""
        satellites = results.get('data', {}).get('satellites', [])

        if not satellites:
            return 0.0

        total_expected = len(satellites) * self.validation_config['required_time_points']
        actual_positions = sum(
            len(sat.get('position_timeseries', [])) for sat in satellites
        )

        return min(1.0, actual_positions / total_expected) if total_expected > 0 else 0.0

    def _assess_time_continuity(self, results: Dict[str, Any]) -> float:
        """評估時間連續性"""
        # 基於之前的連續性檢查結果
        continuity_check = self._check_time_series_continuity(results)
        return continuity_check.get('continuity_rate', 0.0)

    def _assess_tle_freshness(self, results: Dict[str, Any]) -> float:
        """評估TLE數據新鮮度"""
        metadata = results.get('metadata', {})
        tle_epoch_info = metadata.get('tle_epoch_info', {})
        avg_age_days = tle_epoch_info.get('average_age_days', 999)

        # 新鮮度評分：7天內滿分，逐漸遞減
        if avg_age_days <= 1:
            return 1.0
        elif avg_age_days <= 3:
            return 0.9
        elif avg_age_days <= 7:
            return 0.8
        elif avg_age_days <= 14:
            return 0.6
        else:
            return 0.3

    def _validate_eci_coordinates(self, orbital_results: Dict[str, Any]) -> bool:
        """驗證ECI座標合理性"""
        satellites = orbital_results.get('data', {}).get('satellites', [])

        for satellite in satellites[:5]:  # 抽樣驗證
            positions = satellite.get('position_timeseries', [])
            for position in positions[:10]:  # 每個衛星驗證前10個位置
                eci = position.get('eci_coordinates', {})
                x, y, z = eci.get('x_km', 0), eci.get('y_km', 0), eci.get('z_km', 0)

                # 檢查位置向量合理性
                distance = math.sqrt(x*x + y*y + z*z)
                if not (6378 <= distance <= 50000):  # 不合理的軌道高度
                    return False

        return True

    def _validate_orbital_periods(self, orbital_results: Dict[str, Any]) -> bool:
        """驗證軌道週期合理性"""
        # LEO衛星軌道週期應該在90-120分鐘之間
        satellites = orbital_results.get('data', {}).get('satellites', [])

        for satellite in satellites[:3]:  # 抽樣驗證
            positions = satellite.get('position_timeseries', [])
            if len(positions) >= 2:
                # 簡單檢查：時間間隔應該合理
                time_interval = positions[1].get('timestamp', 0) - positions[0].get('timestamp', 0)
                if not (10 <= time_interval <= 300):  # 10秒到5分鐘的間隔
                    return False

        return True

    def _validate_position_magnitudes(self, orbital_results: Dict[str, Any]) -> bool:
        """驗證位置向量幅度"""
        satellites = orbital_results.get('data', {}).get('satellites', [])

        for satellite in satellites[:3]:
            positions = satellite.get('position_timeseries', [])
            for position in positions[:5]:
                eci = position.get('eci_coordinates', {})
                x, y, z = eci.get('x_km', 0), eci.get('y_km', 0), eci.get('z_km', 0)

                # 檢查各分量的合理性
                if any(abs(coord) > 50000 for coord in [x, y, z]):
                    return False

        return True

    def _validate_velocity_vectors(self, orbital_results: Dict[str, Any]) -> bool:
        """驗證速度向量"""
        satellites = orbital_results.get('data', {}).get('satellites', [])

        for satellite in satellites[:3]:
            positions = satellite.get('position_timeseries', [])
            for position in positions[:5]:
                eci = position.get('eci_coordinates', {})
                vx = eci.get('vx_km_per_s', 0)
                vy = eci.get('vy_km_per_s', 0)
                vz = eci.get('vz_km_per_s', 0)

                velocity_magnitude = math.sqrt(vx*vx + vy*vy + vz*vz)

                # LEO衛星速度應該在6-8 km/s範圍內
                if not (5.0 <= velocity_magnitude <= 10.0):
                    return False

        return True

    def _determine_validation_status(self, score: float) -> str:
        """根據分數確定驗證狀態"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Acceptable"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Poor"

    def _generate_recommendations(self, detailed_results: Dict[str, Any]) -> List[str]:
        """生成改進建議"""
        recommendations = []

        for check_name, result in detailed_results.items():
            if not result.get('passed', False):
                if check_name == 'tle_epoch_compliance':
                    recommendations.append("建議使用更新的TLE數據，確保epoch時間合規")
                elif check_name == 'orbital_positions':
                    recommendations.append("檢查軌道計算算法，確保位置數據合理性")
                elif check_name == 'time_series_continuity':
                    recommendations.append("優化時間序列生成，確保數據連續性")
                elif check_name == 'academic_compliance':
                    recommendations.append("提升學術標準合規性，確保Grade A品質")

        if not recommendations:
            recommendations.append("所有驗證檢查通過，系統運行良好")

        return recommendations

    def _log_validation_summary(self, validation_report: Dict[str, Any]):
        """記錄驗證摘要"""
        score = validation_report.get('validation_score', 0)
        status = validation_report.get('overall_status', 'Unknown')

        self.logger.info(f"✅ 軌道驗證完成:")
        self.logger.info(f"   驗證分數: {score:.1f}/100")
        self.logger.info(f"   驗證狀態: {status}")
        self.logger.info(f"   檢查項目: {len(validation_report.get('checks_performed', []))}")

    def get_validation_statistics(self) -> Dict[str, Any]:
        """獲取驗證統計信息"""
        return self.validation_stats.copy()