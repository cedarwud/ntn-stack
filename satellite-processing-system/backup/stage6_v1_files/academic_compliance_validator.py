#!/usr/bin/env python3
"""
Academic Compliance Validator - 學術合規驗證器

專責學術標準和物理合規驗證：
- 物理定律合規性驗證
- 學術標準檢查
- 可靠性評估
- 數據真實性驗證

從 ValidationEngine 中拆分出來，專注於學術合規功能
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np

class AcademicComplianceValidator:
    """
    學術合規驗證器

    專責物理定律和學術標準的合規性驗證
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化學術合規驗證器"""
        self.logger = logging.getLogger(f"{__name__}.AcademicComplianceValidator")
        self.config = config or self._get_default_validation_config()

        self.validation_stats = {
            'physics_checks_performed': 0,
            'physics_checks_passed': 0,
            'academic_checks_performed': 0,
            'academic_checks_passed': 0,
            'reliability_assessments': 0
        }

        # 學術驗證標準
        self.validation_standards = {
            "academic_grade_target": "A+",
            "physics_compliance_required": True,
            "data_authenticity_required": True,
            "calculation_method_verification": True,
            "reproducibility_required": True
        }

        self.logger.info("✅ Academic Compliance Validator 初始化完成")

    def validate_physics_compliance(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證物理定律合規性

        Args:
            pool_data: 衛星池數據

        Returns:
            物理合規驗證結果
        """
        try:
            self.logger.info("🔍 開始物理定律合規性驗證...")

            physics_result = {
                "physics_validation": {
                    "passed": True,
                    "compliance_score": 0.0,
                    "physics_checks": {},
                    "violations": [],
                    "recommendations": []
                }
            }

            satellites = pool_data.get('satellites', [])
            if not satellites:
                physics_result["physics_validation"]["passed"] = False
                return physics_result

            # 驗證RSRP物理合理性
            rsrp_validation = self._validate_rsrp_physics(satellites)
            physics_result["physics_validation"]["physics_checks"]["rsrp_validation"] = rsrp_validation

            # 驗證仰角物理合理性
            elevation_validation = self._validate_elevation_physics(satellites)
            physics_result["physics_validation"]["physics_checks"]["elevation_validation"] = elevation_validation

            # 驗證距離計算合理性
            distance_validation = self._validate_distance_physics(satellites)
            physics_result["physics_validation"]["physics_checks"]["distance_validation"] = distance_validation

            # 驗證軌道參數一致性
            orbital_consistency = self._validate_orbital_consistency(satellites)
            physics_result["physics_validation"]["physics_checks"]["orbital_consistency"] = orbital_consistency

            # 計算整體物理合規分數
            compliance_score = self._calculate_physics_compliance_score([
                rsrp_validation, elevation_validation, distance_validation, orbital_consistency
            ])
            physics_result["physics_validation"]["compliance_score"] = compliance_score

            # 檢查是否通過
            min_compliance_score = self.config.get('min_physics_compliance_score', 0.8)
            if compliance_score < min_compliance_score:
                physics_result["physics_validation"]["passed"] = False
                physics_result["physics_validation"]["violations"].append(
                    f"物理合規分數 {compliance_score:.3f} 低於要求 {min_compliance_score}"
                )

            # 更新統計
            self.validation_stats['physics_checks_performed'] += 1
            if physics_result["physics_validation"]["passed"]:
                self.validation_stats['physics_checks_passed'] += 1

            self.logger.info(f"✅ 物理定律合規性驗證完成，分數: {compliance_score:.3f}")
            return physics_result

        except Exception as e:
            self.logger.error(f"❌ 物理定律合規性驗證失敗: {e}")
            return {
                "physics_validation": {
                    "passed": False,
                    "error": str(e)
                }
            }

    def validate_academic_standards(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證學術標準

        Args:
            pool_data: 衛星池數據

        Returns:
            學術標準驗證結果
        """
        try:
            self.logger.info("🔍 開始學術標準驗證...")

            academic_result = {
                "academic_validation": {
                    "passed": True,
                    "grade_achieved": "Unknown",
                    "standard_checks": {},
                    "compliance_areas": {},
                    "improvement_recommendations": []
                }
            }

            # 檢查數據真實性
            authenticity_result = self._check_data_authenticity(pool_data)
            academic_result["academic_validation"]["standard_checks"]["data_authenticity"] = authenticity_result

            # 檢查計算方法
            calculation_result = self._analyze_calculation_methods(pool_data)
            academic_result["academic_validation"]["standard_checks"]["calculation_methods"] = calculation_result

            # 檢查可重現性
            reproducibility_result = self._assess_reproducibility(pool_data)
            academic_result["academic_validation"]["standard_checks"]["reproducibility"] = reproducibility_result

            # 檢查文檔完整性
            documentation_result = self._check_documentation_completeness(pool_data)
            academic_result["academic_validation"]["standard_checks"]["documentation"] = documentation_result

            # 評估學術等級
            grade_achieved = self._calculate_academic_grade([
                authenticity_result, calculation_result, reproducibility_result, documentation_result
            ])
            academic_result["academic_validation"]["grade_achieved"] = grade_achieved

            # 檢查是否達到目標等級
            target_grade = self.validation_standards.get("academic_grade_target", "A+")
            if not self._is_grade_sufficient(grade_achieved, target_grade):
                academic_result["academic_validation"]["passed"] = False
                academic_result["academic_validation"]["improvement_recommendations"].append(
                    f"當前等級 {grade_achieved} 未達到目標 {target_grade}"
                )

            # 更新統計
            self.validation_stats['academic_checks_performed'] += 1
            if academic_result["academic_validation"]["passed"]:
                self.validation_stats['academic_checks_passed'] += 1

            self.logger.info(f"✅ 學術標準驗證完成，等級: {grade_achieved}")
            return academic_result

        except Exception as e:
            self.logger.error(f"❌ 學術標準驗證失敗: {e}")
            return {
                "academic_validation": {
                    "passed": False,
                    "error": str(e)
                }
            }

    def assess_reliability(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估可靠性

        Args:
            pool_data: 衛星池數據

        Returns:
            可靠性評估結果
        """
        try:
            self.logger.info("🔍 開始可靠性評估...")

            reliability_result = {
                "reliability_assessment": {
                    "overall_reliability": 0.0,
                    "reliability_factors": {},
                    "risk_assessment": {},
                    "recommendations": []
                }
            }

            # 數據一致性可靠性
            data_consistency = self._assess_data_consistency(pool_data)
            reliability_result["reliability_assessment"]["reliability_factors"]["data_consistency"] = data_consistency

            # 計算方法可靠性
            method_reliability = self._assess_method_reliability(pool_data)
            reliability_result["reliability_assessment"]["reliability_factors"]["method_reliability"] = method_reliability

            # 結果重現性可靠性
            reproducibility_reliability = self._assess_reproducibility_reliability(pool_data)
            reliability_result["reliability_assessment"]["reliability_factors"]["reproducibility"] = reproducibility_reliability

            # 計算整體可靠性
            overall_reliability = self._calculate_overall_reliability([
                data_consistency, method_reliability, reproducibility_reliability
            ])
            reliability_result["reliability_assessment"]["overall_reliability"] = overall_reliability

            # 風險評估
            risk_assessment = self._perform_risk_assessment(overall_reliability)
            reliability_result["reliability_assessment"]["risk_assessment"] = risk_assessment

            # 生成可靠性建議
            recommendations = self._generate_reliability_recommendation(overall_reliability, risk_assessment)
            reliability_result["reliability_assessment"]["recommendations"] = recommendations

            # 更新統計
            self.validation_stats['reliability_assessments'] += 1

            self.logger.info(f"✅ 可靠性評估完成，可靠性: {overall_reliability:.3f}")
            return reliability_result

        except Exception as e:
            self.logger.error(f"❌ 可靠性評估失敗: {e}")
            return {
                "reliability_assessment": {
                    "overall_reliability": 0.0,
                    "error": str(e)
                }
            }

    # ===== 私有方法 =====

    def _validate_rsrp_physics(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證RSRP物理合理性"""
        try:
            result = {"passed": True, "violations": [], "metrics": {}}

            rsrp_values = [s.get('rsrp', -120) for s in satellites if 'rsrp' in s]
            if not rsrp_values:
                result["passed"] = False
                result["violations"].append("缺少RSRP數據")
                return result

            # 檢查RSRP範圍合理性
            min_rsrp, max_rsrp = min(rsrp_values), max(rsrp_values)
            if min_rsrp < -140 or max_rsrp > -30:
                result["passed"] = False
                result["violations"].append(f"RSRP範圍異常: {min_rsrp} ~ {max_rsrp} dBm")

            # 檢查RSRP分布合理性
            rsrp_std = np.std(rsrp_values)
            if rsrp_std > 30:  # 標準差過大可能表示數據不一致
                result["violations"].append(f"RSRP分布異常，標準差: {rsrp_std:.2f}")

            result["metrics"] = {
                "min_rsrp": min_rsrp,
                "max_rsrp": max_rsrp,
                "mean_rsrp": np.mean(rsrp_values),
                "std_rsrp": rsrp_std,
                "sample_count": len(rsrp_values)
            }

            return result

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _validate_elevation_physics(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證仰角物理合理性"""
        try:
            result = {"passed": True, "violations": [], "metrics": {}}

            elevations = [s.get('elevation', 0) for s in satellites if 'elevation' in s]
            if not elevations:
                result["passed"] = False
                result["violations"].append("缺少仰角數據")
                return result

            # 檢查仰角範圍
            min_elevation, max_elevation = min(elevations), max(elevations)
            if min_elevation < 0 or max_elevation > 90:
                result["passed"] = False
                result["violations"].append(f"仰角範圍異常: {min_elevation}° ~ {max_elevation}°")

            # 檢查低仰角衛星比例（應該較少）
            low_elevation_count = sum(1 for e in elevations if e < 10)
            if low_elevation_count / len(elevations) > 0.3:
                result["violations"].append(f"低仰角衛星比例過高: {low_elevation_count}/{len(elevations)}")

            result["metrics"] = {
                "min_elevation": min_elevation,
                "max_elevation": max_elevation,
                "mean_elevation": np.mean(elevations),
                "low_elevation_ratio": low_elevation_count / len(elevations)
            }

            return result

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _validate_distance_physics(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證距離計算合理性"""
        try:
            result = {"passed": True, "violations": [], "metrics": {}}

            distances = [s.get('distance', 0) for s in satellites if 'distance' in s]
            if not distances:
                result["violations"].append("缺少距離數據")
                return result

            # LEO衛星典型距離範圍檢查
            min_distance, max_distance = min(distances), max(distances)
            if min_distance < 500000 or max_distance > 2000000:  # 500-2000km
                result["violations"].append(f"衛星距離範圍異常: {min_distance/1000:.1f} ~ {max_distance/1000:.1f} km")

            result["metrics"] = {
                "min_distance_km": min_distance / 1000,
                "max_distance_km": max_distance / 1000,
                "mean_distance_km": np.mean(distances) / 1000
            }

            return result

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _validate_orbital_consistency(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證軌道參數一致性"""
        try:
            result = {"passed": True, "violations": [], "metrics": {}}

            # 檢查不同星座的軌道高度一致性
            starlink_elevations = [s.get('elevation', 0) for s in satellites
                                 if 'starlink' in s.get('constellation', '').lower()]
            oneweb_elevations = [s.get('elevation', 0) for s in satellites
                               if 'oneweb' in s.get('constellation', '').lower()]

            if starlink_elevations and oneweb_elevations:
                starlink_mean = np.mean(starlink_elevations)
                oneweb_mean = np.mean(oneweb_elevations)

                # 同一星座的仰角應該相對集中
                if abs(starlink_mean - oneweb_mean) < 5:  # 太接近可能不正常
                    result["violations"].append("不同星座仰角分布過於相似")

            result["metrics"] = {
                "starlink_mean_elevation": np.mean(starlink_elevations) if starlink_elevations else 0,
                "oneweb_mean_elevation": np.mean(oneweb_elevations) if oneweb_elevations else 0,
                "starlink_count": len(starlink_elevations),
                "oneweb_count": len(oneweb_elevations)
            }

            return result

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _calculate_physics_compliance_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """計算物理合規分數"""
        try:
            passed_count = sum(1 for result in validation_results if result.get("passed", False))
            total_count = len(validation_results)

            if total_count == 0:
                return 0.0

            base_score = passed_count / total_count

            # 根據違規數量調整分數
            total_violations = sum(len(result.get("violations", [])) for result in validation_results)
            violation_penalty = min(0.5, total_violations * 0.1)

            final_score = max(0.0, base_score - violation_penalty)
            return final_score

        except Exception as e:
            self.logger.warning(f"⚠️ 物理合規分數計算失敗: {e}")
            return 0.0

    def _check_data_authenticity(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數據真實性"""
        try:
            result = {
                "passed": True,
                "authenticity_score": 0.0,
                "checks": {},
                "flags": []
            }

            satellites = pool_data.get('satellites', [])

            # 檢查數據來源標記
            has_source_info = any('data_source' in s for s in satellites)
            result["checks"]["source_info"] = has_source_info
            if not has_source_info:
                result["flags"].append("缺少數據來源信息")

            # 檢查時間戳一致性
            timestamps = [s.get('timestamp') for s in satellites if 'timestamp' in s]
            timestamp_consistency = len(set(timestamps)) <= len(satellites) * 0.1  # 時間戳應該相對集中
            result["checks"]["timestamp_consistency"] = timestamp_consistency
            if not timestamp_consistency:
                result["flags"].append("時間戳分布異常")

            # 檢查是否有明顯的模擬數據特徵
            rsrp_values = [s.get('rsrp', -120) for s in satellites if 'rsrp' in s]
            if rsrp_values:
                # 檢查是否有過於規律的數值
                rounded_values = [round(r) for r in rsrp_values]
                unique_ratio = len(set(rounded_values)) / len(rounded_values)
                if unique_ratio < 0.5:  # 獨特值比例過低可能是模擬數據
                    result["flags"].append("數值過於規律，可能為模擬數據")

            # 計算真實性分數
            authenticity_score = len([c for c in result["checks"].values() if c]) / len(result["checks"])
            penalty = len(result["flags"]) * 0.2
            result["authenticity_score"] = max(0.0, authenticity_score - penalty)

            if result["authenticity_score"] < 0.7:
                result["passed"] = False

            return result

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _analyze_calculation_methods(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析計算方法"""
        try:
            result = {
                "passed": True,
                "method_score": 0.0,
                "method_checks": {},
                "recommendations": []
            }

            # 檢查是否使用標準算法
            metadata = pool_data.get('metadata', {})
            calculation_method = metadata.get('calculation_method', '')

            standard_methods = ['sgp4', 'friis', 'itu-r', '3gpp']
            uses_standard_methods = any(method in calculation_method.lower() for method in standard_methods)
            result["method_checks"]["standard_algorithms"] = uses_standard_methods

            if not uses_standard_methods:
                result["recommendations"].append("建議使用標準計算算法 (SGP4, Friis等)")

            # 檢查計算參數的完整性
            has_physics_constants = 'physics_constants' in metadata
            result["method_checks"]["physics_constants"] = has_physics_constants

            if not has_physics_constants:
                result["recommendations"].append("缺少物理常數定義")

            # 計算方法分數
            passed_checks = sum(result["method_checks"].values())
            total_checks = len(result["method_checks"])
            result["method_score"] = passed_checks / total_checks if total_checks > 0 else 0

            if result["method_score"] < 0.8:
                result["passed"] = False

            return result

        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _assess_reproducibility(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """評估可重現性"""
        try:
            result = {
                "reproducible": True,
                "reproducibility_score": 0.0,
                "factors": {}
            }

            metadata = pool_data.get('metadata', {})

            # 檢查配置參數的完整性
            has_config = 'configuration' in metadata or 'config' in metadata
            result["factors"]["configuration_available"] = has_config

            # 檢查版本信息
            has_version = 'version' in metadata or 'algorithm_version' in metadata
            result["factors"]["version_info"] = has_version

            # 檢查隨機種子設定
            has_seed = 'random_seed' in metadata or 'seed' in metadata
            result["factors"]["deterministic_seed"] = has_seed

            # 計算可重現性分數
            reproducibility_score = sum(result["factors"].values()) / len(result["factors"])
            result["reproducibility_score"] = reproducibility_score

            if reproducibility_score < 0.6:
                result["reproducible"] = False

            return result

        except Exception as e:
            return {"reproducible": False, "error": str(e)}

    def _check_documentation_completeness(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查文檔完整性"""
        try:
            result = {
                "complete": True,
                "completeness_score": 0.0,
                "missing_elements": []
            }

            metadata = pool_data.get('metadata', {})

            required_documentation = [
                'description', 'methodology', 'parameters', 'assumptions', 'limitations'
            ]

            available_elements = sum(1 for element in required_documentation if element in metadata)
            result["completeness_score"] = available_elements / len(required_documentation)

            for element in required_documentation:
                if element not in metadata:
                    result["missing_elements"].append(element)

            if result["completeness_score"] < 0.7:
                result["complete"] = False

            return result

        except Exception as e:
            return {"complete": False, "error": str(e)}

    def _calculate_academic_grade(self, validation_results: List[Dict[str, Any]]) -> str:
        """計算學術等級"""
        try:
            # 計算通過的檢查比例
            total_checks = len(validation_results)
            passed_checks = sum(1 for result in validation_results if result.get("passed", result.get("complete", result.get("reproducible", False))))

            if total_checks == 0:
                return "F"

            pass_rate = passed_checks / total_checks

            if pass_rate >= 0.95:
                return "A+"
            elif pass_rate >= 0.9:
                return "A"
            elif pass_rate >= 0.85:
                return "A-"
            elif pass_rate >= 0.8:
                return "B+"
            elif pass_rate >= 0.75:
                return "B"
            elif pass_rate >= 0.7:
                return "B-"
            elif pass_rate >= 0.65:
                return "C+"
            elif pass_rate >= 0.6:
                return "C"
            else:
                return "F"

        except Exception as e:
            self.logger.warning(f"⚠️ 學術等級計算失敗: {e}")
            return "F"

    def _is_grade_sufficient(self, achieved_grade: str, target_grade: str) -> bool:
        """檢查等級是否足夠"""
        grade_values = {
            "A+": 100, "A": 95, "A-": 90, "B+": 85, "B": 80,
            "B-": 75, "C+": 70, "C": 65, "C-": 60, "F": 0
        }

        achieved_value = grade_values.get(achieved_grade, 0)
        target_value = grade_values.get(target_grade, 100)

        return achieved_value >= target_value

    def _assess_data_consistency(self, pool_data: Dict[str, Any]) -> float:
        """評估數據一致性"""
        try:
            satellites = pool_data.get('satellites', [])
            if not satellites:
                return 0.0

            # 檢查必需字段的完整性
            required_fields = ['satellite_id', 'constellation', 'rsrp', 'elevation']
            field_completeness = []

            for field in required_fields:
                complete_count = sum(1 for s in satellites if field in s and s[field] is not None)
                completeness = complete_count / len(satellites)
                field_completeness.append(completeness)

            return np.mean(field_completeness)

        except Exception as e:
            self.logger.warning(f"⚠️ 數據一致性評估失敗: {e}")
            return 0.0

    def _assess_method_reliability(self, pool_data: Dict[str, Any]) -> float:
        """評估方法可靠性"""
        try:
            metadata = pool_data.get('metadata', {})

            reliability_factors = []

            # 檢查是否使用已驗證的算法
            calculation_method = metadata.get('calculation_method', '').lower()
            verified_algorithms = ['sgp4', 'friis', 'itu-r']
            uses_verified = any(alg in calculation_method for alg in verified_algorithms)
            reliability_factors.append(1.0 if uses_verified else 0.5)

            # 檢查是否有誤差分析
            has_error_analysis = 'error_analysis' in metadata or 'uncertainty' in metadata
            reliability_factors.append(1.0 if has_error_analysis else 0.0)

            # 檢查是否有交叉驗證
            has_validation = 'validation' in metadata or 'cross_validation' in metadata
            reliability_factors.append(1.0 if has_validation else 0.0)

            return np.mean(reliability_factors) if reliability_factors else 0.0

        except Exception as e:
            self.logger.warning(f"⚠️ 方法可靠性評估失敗: {e}")
            return 0.0

    def _assess_reproducibility_reliability(self, pool_data: Dict[str, Any]) -> float:
        """評估重現性可靠性"""
        try:
            metadata = pool_data.get('metadata', {})

            reproducibility_factors = []

            # 檢查配置完整性
            has_complete_config = all(key in metadata for key in ['configuration', 'parameters'])
            reproducibility_factors.append(1.0 if has_complete_config else 0.0)

            # 檢查隨機性控制
            has_seed_control = 'random_seed' in metadata or 'deterministic' in str(metadata)
            reproducibility_factors.append(1.0 if has_seed_control else 0.0)

            # 檢查環境信息
            has_environment_info = 'environment' in metadata or 'system_info' in metadata
            reproducibility_factors.append(1.0 if has_environment_info else 0.0)

            return np.mean(reproducibility_factors) if reproducibility_factors else 0.0

        except Exception as e:
            self.logger.warning(f"⚠️ 重現性可靠性評估失敗: {e}")
            return 0.0

    def _calculate_overall_reliability(self, reliability_factors: List[float]) -> float:
        """計算整體可靠性"""
        try:
            if not reliability_factors:
                return 0.0
            return np.mean(reliability_factors)
        except Exception as e:
            self.logger.warning(f"⚠️ 整體可靠性計算失敗: {e}")
            return 0.0

    def _perform_risk_assessment(self, reliability_score: float) -> Dict[str, Any]:
        """執行風險評估"""
        try:
            if reliability_score >= 0.9:
                risk_level = "Low"
                risk_description = "高可靠性，風險極低"
            elif reliability_score >= 0.7:
                risk_level = "Medium"
                risk_description = "中等可靠性，存在一定風險"
            elif reliability_score >= 0.5:
                risk_level = "High"
                risk_description = "低可靠性，存在較高風險"
            else:
                risk_level = "Critical"
                risk_description = "極低可靠性，風險極高"

            return {
                "risk_level": risk_level,
                "risk_score": 1.0 - reliability_score,
                "description": risk_description
            }

        except Exception as e:
            return {"risk_level": "Unknown", "error": str(e)}

    def _generate_reliability_recommendation(self, reliability_score: float,
                                           risk_assessment: Dict[str, Any]) -> List[str]:
        """生成可靠性建議"""
        try:
            recommendations = []

            if reliability_score < 0.7:
                recommendations.append("建議改善數據完整性和一致性")

            if reliability_score < 0.6:
                recommendations.append("建議使用經過驗證的標準算法")

            if reliability_score < 0.5:
                recommendations.append("建議增加誤差分析和不確定性評估")

            if risk_assessment.get("risk_level") in ["High", "Critical"]:
                recommendations.append("建議進行獨立驗證和交叉檢查")

            return recommendations

        except Exception as e:
            return [f"建議生成失敗: {e}"]

    def _get_default_validation_config(self) -> Dict[str, Any]:
        """獲取預設驗證配置"""
        return {
            "min_physics_compliance_score": 0.8,
            "academic_grade_target": "A+",
            "min_reliability_score": 0.7,
            "require_standard_algorithms": True,
            "require_error_analysis": True
        }

    def get_validation_statistics(self) -> Dict[str, Any]:
        """獲取驗證統計信息"""
        return self.validation_stats.copy()