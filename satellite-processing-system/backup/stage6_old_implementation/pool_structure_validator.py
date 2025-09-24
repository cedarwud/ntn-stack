#!/usr/bin/env python3
"""
Pool Structure Validator - 衛星池結構驗證器

專責衛星池的結構和品質驗證：
- 池結構驗證
- 池品質評估
- 覆蓋需求驗證
- 多樣性需求驗證

從 ValidationEngine 中拆分出來，專注於結構驗證功能
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np

class PoolStructureValidator:
    """
    衛星池結構驗證器

    專責池的結構完整性和品質評估
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化結構驗證器"""
        self.logger = logging.getLogger(f"{__name__}.PoolStructureValidator")
        self.config = config or self._get_default_validation_config()

        self.validation_stats = {
            'validations_performed': 0,
            'structure_checks_passed': 0,
            'quality_checks_passed': 0,
            'coverage_checks_passed': 0,
            'diversity_checks_passed': 0
        }

        self.logger.info("✅ Pool Structure Validator 初始化完成")

    def validate_pool_structure(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證池結構

        Args:
            pool_data: 衛星池數據

        Returns:
            結構驗證結果
        """
        try:
            self.logger.info("🔍 開始池結構驗證...")

            validation_result = {
                "structure_validation": {
                    "passed": True,
                    "errors": [],
                    "warnings": [],
                    "details": {}
                }
            }

            # 檢查基本結構
            basic_structure_result = self._check_basic_structure(pool_data)
            validation_result["structure_validation"]["details"]["basic_structure"] = basic_structure_result

            if not basic_structure_result["passed"]:
                validation_result["structure_validation"]["passed"] = False
                validation_result["structure_validation"]["errors"].extend(basic_structure_result["errors"])

            # 檢查衛星數據完整性
            data_integrity_result = self._check_data_integrity(pool_data)
            validation_result["structure_validation"]["details"]["data_integrity"] = data_integrity_result

            if not data_integrity_result["passed"]:
                validation_result["structure_validation"]["passed"] = False
                validation_result["structure_validation"]["errors"].extend(data_integrity_result["errors"])

            # 檢查數量約束
            quantity_result = self._check_quantity_constraints(pool_data)
            validation_result["structure_validation"]["details"]["quantity_constraints"] = quantity_result

            if not quantity_result["passed"]:
                validation_result["structure_validation"]["passed"] = False
                validation_result["structure_validation"]["warnings"].extend(quantity_result["warnings"])

            # 更新統計
            if validation_result["structure_validation"]["passed"]:
                self.validation_stats['structure_checks_passed'] += 1

            self.validation_stats['validations_performed'] += 1

            self.logger.info(f"✅ 池結構驗證完成，結果: {'通過' if validation_result['structure_validation']['passed'] else '失敗'}")
            return validation_result

        except Exception as e:
            self.logger.error(f"❌ 池結構驗證失敗: {e}")
            return {
                "structure_validation": {
                    "passed": False,
                    "errors": [f"驗證異常: {e}"],
                    "warnings": [],
                    "details": {}
                }
            }

    def validate_pool_quality(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證池品質

        Args:
            pool_data: 衛星池數據

        Returns:
            品質驗證結果
        """
        try:
            self.logger.info("🔍 開始池品質驗證...")

            quality_result = {
                "quality_validation": {
                    "passed": True,
                    "overall_score": 0.0,
                    "quality_metrics": {},
                    "recommendations": []
                }
            }

            satellites = pool_data.get('satellites', [])
            if not satellites:
                quality_result["quality_validation"]["passed"] = False
                return quality_result

            # 分析品質分布
            quality_distribution = self._analyze_quality_distribution(satellites)
            quality_result["quality_validation"]["quality_metrics"]["distribution"] = quality_distribution

            # 計算平均RSRP
            rsrp_values = [s.get('rsrp', -120) for s in satellites if 'rsrp' in s]
            avg_rsrp = np.mean(rsrp_values) if rsrp_values else -120.0
            quality_result["quality_validation"]["quality_metrics"]["avg_rsrp"] = avg_rsrp

            # 計算平均仰角
            elevation_values = [s.get('elevation', 0) for s in satellites if 'elevation' in s]
            avg_elevation = np.mean(elevation_values) if elevation_values else 0.0
            quality_result["quality_validation"]["quality_metrics"]["avg_elevation"] = avg_elevation

            # 評估整體品質分數
            overall_score = self._calculate_overall_quality_score(
                avg_rsrp, avg_elevation, quality_distribution
            )
            quality_result["quality_validation"]["overall_score"] = overall_score

            # 品質門檻檢查
            min_quality_threshold = self.config.get('min_quality_threshold', 0.6)
            if overall_score < min_quality_threshold:
                quality_result["quality_validation"]["passed"] = False
                quality_result["quality_validation"]["recommendations"].append(
                    f"整體品質分數 {overall_score:.3f} 低於門檻 {min_quality_threshold}"
                )

            # 更新統計
            if quality_result["quality_validation"]["passed"]:
                self.validation_stats['quality_checks_passed'] += 1

            self.logger.info(f"✅ 池品質驗證完成，分數: {overall_score:.3f}")
            return quality_result

        except Exception as e:
            self.logger.error(f"❌ 池品質驗證失敗: {e}")
            return {
                "quality_validation": {
                    "passed": False,
                    "overall_score": 0.0,
                    "error": str(e)
                }
            }

    def validate_coverage_requirements(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證覆蓋需求

        Args:
            pool_data: 衛星池數據

        Returns:
            覆蓋驗證結果
        """
        try:
            self.logger.info("🔍 開始覆蓋需求驗證...")

            coverage_result = {
                "coverage_validation": {
                    "passed": True,
                    "coverage_metrics": {},
                    "requirements_check": {},
                    "recommendations": []
                }
            }

            satellites = pool_data.get('satellites', [])
            if not satellites:
                coverage_result["coverage_validation"]["passed"] = False
                return coverage_result

            # 計算覆蓋分數
            coverage_score = self._calculate_coverage_score(satellites)
            coverage_result["coverage_validation"]["coverage_metrics"]["coverage_score"] = coverage_score

            # 分析地理分布
            geographic_distribution = self._analyze_geographic_distribution(satellites)
            coverage_result["coverage_validation"]["coverage_metrics"]["geographic_distribution"] = geographic_distribution

            # 分析時間覆蓋
            temporal_coverage = self._analyze_temporal_coverage(satellites)
            coverage_result["coverage_validation"]["coverage_metrics"]["temporal_coverage"] = temporal_coverage

            # 檢查最小覆蓋需求
            min_coverage_requirement = self.config.get('min_coverage_requirement', 0.85)
            if coverage_score < min_coverage_requirement:
                coverage_result["coverage_validation"]["passed"] = False
                coverage_result["coverage_validation"]["recommendations"].append(
                    f"覆蓋分數 {coverage_score:.3f} 低於需求 {min_coverage_requirement}"
                )

            coverage_result["coverage_validation"]["requirements_check"]["min_coverage"] = {
                "required": min_coverage_requirement,
                "actual": coverage_score,
                "passed": coverage_score >= min_coverage_requirement
            }

            # 更新統計
            if coverage_result["coverage_validation"]["passed"]:
                self.validation_stats['coverage_checks_passed'] += 1

            self.logger.info(f"✅ 覆蓋需求驗證完成，覆蓋分數: {coverage_score:.3f}")
            return coverage_result

        except Exception as e:
            self.logger.error(f"❌ 覆蓋需求驗證失敗: {e}")
            return {
                "coverage_validation": {
                    "passed": False,
                    "error": str(e)
                }
            }

    def validate_diversity_requirements(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證多樣性需求

        Args:
            pool_data: 衛星池數據

        Returns:
            多樣性驗證結果
        """
        try:
            self.logger.info("🔍 開始多樣性需求驗證...")

            diversity_result = {
                "diversity_validation": {
                    "passed": True,
                    "diversity_metrics": {},
                    "requirements_check": {},
                    "recommendations": []
                }
            }

            satellites = pool_data.get('satellites', [])
            if not satellites:
                diversity_result["diversity_validation"]["passed"] = False
                return diversity_result

            # 分析軌道多樣性
            orbital_diversity = self._analyze_orbital_diversity(satellites)
            diversity_result["diversity_validation"]["diversity_metrics"]["orbital_diversity"] = orbital_diversity

            # 分析星座多樣性
            constellation_diversity = self._analyze_constellation_diversity(satellites)
            diversity_result["diversity_validation"]["diversity_metrics"]["constellation_diversity"] = constellation_diversity

            # 檢查多樣性需求
            min_orbital_diversity = self.config.get('min_orbital_diversity', 0.6)
            if orbital_diversity.get('diversity_score', 0) < min_orbital_diversity:
                diversity_result["diversity_validation"]["passed"] = False
                diversity_result["diversity_validation"]["recommendations"].append(
                    f"軌道多樣性 {orbital_diversity.get('diversity_score', 0):.3f} 低於需求 {min_orbital_diversity}"
                )

            diversity_result["diversity_validation"]["requirements_check"]["orbital_diversity"] = {
                "required": min_orbital_diversity,
                "actual": orbital_diversity.get('diversity_score', 0),
                "passed": orbital_diversity.get('diversity_score', 0) >= min_orbital_diversity
            }

            # 檢查星座平衡
            constellation_balance_required = self.config.get('constellation_balance_required', True)
            if constellation_balance_required:
                balance_score = constellation_diversity.get('balance_score', 0)
                min_balance_score = self.config.get('min_balance_score', 0.5)

                if balance_score < min_balance_score:
                    diversity_result["diversity_validation"]["passed"] = False
                    diversity_result["diversity_validation"]["recommendations"].append(
                        f"星座平衡分數 {balance_score:.3f} 低於需求 {min_balance_score}"
                    )

                diversity_result["diversity_validation"]["requirements_check"]["constellation_balance"] = {
                    "required": min_balance_score,
                    "actual": balance_score,
                    "passed": balance_score >= min_balance_score
                }

            # 更新統計
            if diversity_result["diversity_validation"]["passed"]:
                self.validation_stats['diversity_checks_passed'] += 1

            self.logger.info("✅ 多樣性需求驗證完成")
            return diversity_result

        except Exception as e:
            self.logger.error(f"❌ 多樣性需求驗證失敗: {e}")
            return {
                "diversity_validation": {
                    "passed": False,
                    "error": str(e)
                }
            }

    # ===== 私有方法 =====

    def _check_basic_structure(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查基本結構"""
        result = {"passed": True, "errors": [], "details": {}}

        # 檢查必需字段
        required_fields = ['satellites', 'metadata']
        for field in required_fields:
            if field not in pool_data:
                result["passed"] = False
                result["errors"].append(f"缺少必需字段: {field}")

        # 檢查衛星列表
        if 'satellites' in pool_data:
            satellites = pool_data['satellites']
            if not isinstance(satellites, list):
                result["passed"] = False
                result["errors"].append("satellites 字段必須是列表")
            elif len(satellites) == 0:
                result["passed"] = False
                result["errors"].append("衛星列表不能為空")

        result["details"]["satellites_count"] = len(pool_data.get('satellites', []))
        return result

    def _check_data_integrity(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數據完整性"""
        result = {"passed": True, "errors": [], "details": {}}

        satellites = pool_data.get('satellites', [])
        required_satellite_fields = ['satellite_id', 'constellation', 'rsrp', 'elevation']

        incomplete_satellites = 0
        for i, satellite in enumerate(satellites):
            missing_fields = [field for field in required_satellite_fields if field not in satellite]
            if missing_fields:
                incomplete_satellites += 1
                if incomplete_satellites <= 5:  # 只報告前5個錯誤
                    result["errors"].append(f"衛星 {i} 缺少字段: {missing_fields}")

        if incomplete_satellites > 0:
            result["passed"] = False
            result["details"]["incomplete_satellites"] = incomplete_satellites

        result["details"]["total_satellites"] = len(satellites)
        result["details"]["data_completeness"] = (len(satellites) - incomplete_satellites) / len(satellites) if satellites else 0

        return result

    def _check_quantity_constraints(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數量約束"""
        result = {"passed": True, "warnings": [], "details": {}}

        satellites = pool_data.get('satellites', [])
        total_count = len(satellites)

        min_satellites = self.config.get('min_satellites', 8)
        max_satellites = self.config.get('max_satellites', 20)

        result["details"]["total_count"] = total_count
        result["details"]["min_required"] = min_satellites
        result["details"]["max_allowed"] = max_satellites

        if total_count < min_satellites:
            result["passed"] = False
            result["warnings"].append(f"衛星數量 {total_count} 少於最小需求 {min_satellites}")
        elif total_count > max_satellites:
            result["warnings"].append(f"衛星數量 {total_count} 超過建議最大值 {max_satellites}")

        return result

    def _analyze_quality_distribution(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析品質分布"""
        try:
            rsrp_values = [s.get('rsrp', -120) for s in satellites if 'rsrp' in s]

            if not rsrp_values:
                return {"error": "無RSRP數據"}

            return {
                "rsrp_stats": {
                    "mean": np.mean(rsrp_values),
                    "std": np.std(rsrp_values),
                    "min": np.min(rsrp_values),
                    "max": np.max(rsrp_values),
                    "count": len(rsrp_values)
                },
                "quality_categories": {
                    "excellent": sum(1 for r in rsrp_values if r >= -70),
                    "good": sum(1 for r in rsrp_values if -85 <= r < -70),
                    "fair": sum(1 for r in rsrp_values if -100 <= r < -85),
                    "poor": sum(1 for r in rsrp_values if r < -100)
                }
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 品質分布分析失敗: {e}")
            return {"error": str(e)}

    def _calculate_overall_quality_score(self, avg_rsrp: float, avg_elevation: float,
                                       quality_distribution: Dict[str, Any]) -> float:
        """計算整體品質分數"""
        try:
            # RSRP分數 (標準化到0-1)
            rsrp_score = max(0, min(1, (avg_rsrp + 120) / 50))

            # 仰角分數 (標準化到0-1)
            elevation_score = max(0, min(1, avg_elevation / 90))

            # 品質分布分數
            quality_cats = quality_distribution.get('quality_categories', {})
            total_sats = sum(quality_cats.values()) if quality_cats else 1
            distribution_score = (
                quality_cats.get('excellent', 0) * 1.0 +
                quality_cats.get('good', 0) * 0.8 +
                quality_cats.get('fair', 0) * 0.6 +
                quality_cats.get('poor', 0) * 0.3
            ) / total_sats if total_sats > 0 else 0

            # 加權平均
            overall_score = (rsrp_score * 0.4 + elevation_score * 0.3 + distribution_score * 0.3)
            return max(0.0, min(1.0, overall_score))

        except Exception as e:
            self.logger.warning(f"⚠️ 整體品質分數計算失敗: {e}")
            return 0.0

    def _calculate_coverage_score(self, satellites: List[Dict[str, Any]]) -> float:
        """計算覆蓋分數"""
        try:
            if not satellites:
                return 0.0

            # 基於衛星數量和分布的簡化覆蓋分數
            count_factor = min(1.0, len(satellites) / 12)  # 12顆衛星為理想數量

            # 基於仰角分布的覆蓋因子
            elevations = [s.get('elevation', 0) for s in satellites if 'elevation' in s]
            if elevations:
                elevation_diversity = np.std(elevations) / 30.0  # 標準化
                elevation_factor = min(1.0, elevation_diversity)
            else:
                elevation_factor = 0.0

            coverage_score = (count_factor * 0.7 + elevation_factor * 0.3)
            return max(0.0, min(1.0, coverage_score))

        except Exception as e:
            self.logger.warning(f"⚠️ 覆蓋分數計算失敗: {e}")
            return 0.0

    def _analyze_geographic_distribution(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析地理分布"""
        try:
            # 簡化的地理分布分析
            elevation_ranges = {
                "low": sum(1 for s in satellites if s.get('elevation', 0) < 30),
                "medium": sum(1 for s in satellites if 30 <= s.get('elevation', 0) < 60),
                "high": sum(1 for s in satellites if s.get('elevation', 0) >= 60)
            }

            total_sats = len(satellites)
            distribution_score = 1.0 - abs(elevation_ranges["low"] / total_sats - 0.33) - \
                               abs(elevation_ranges["medium"] / total_sats - 0.33) - \
                               abs(elevation_ranges["high"] / total_sats - 0.33) if total_sats > 0 else 0

            return {
                "elevation_ranges": elevation_ranges,
                "distribution_score": max(0.0, distribution_score)
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 地理分布分析失敗: {e}")
            return {"error": str(e)}

    def _analyze_temporal_coverage(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析時間覆蓋"""
        try:
            # 簡化的時間覆蓋分析
            return {
                "estimated_coverage_duration": len(satellites) * 10,  # 假設每顆衛星10分鐘覆蓋
                "estimated_coverage_gaps": max(0, 12 - len(satellites)) * 5,  # 假設每缺少1顆衛星增加5分鐘空隙
                "temporal_efficiency": min(1.0, len(satellites) / 12)
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 時間覆蓋分析失敗: {e}")
            return {"error": str(e)}

    def _analyze_orbital_diversity(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析軌道多樣性"""
        try:
            # 基於仰角的軌道多樣性分析
            elevations = [s.get('elevation', 0) for s in satellites if 'elevation' in s]

            if not elevations:
                return {"diversity_score": 0.0, "error": "無仰角數據"}

            # 計算仰角的標準差作為多樣性指標
            elevation_std = np.std(elevations)
            diversity_score = min(1.0, elevation_std / 30.0)  # 標準化到0-1

            return {
                "diversity_score": diversity_score,
                "elevation_range": {
                    "min": min(elevations),
                    "max": max(elevations),
                    "std": elevation_std
                },
                "unique_elevation_bins": len(set(int(e // 10) for e in elevations))  # 10度為一個bin
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 軌道多樣性分析失敗: {e}")
            return {"diversity_score": 0.0, "error": str(e)}

    def _analyze_constellation_diversity(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析星座多樣性"""
        try:
            constellation_counts = {}
            for satellite in satellites:
                constellation = satellite.get('constellation', 'unknown').lower()
                constellation_counts[constellation] = constellation_counts.get(constellation, 0) + 1

            total_sats = len(satellites)
            if total_sats == 0:
                return {"balance_score": 0.0, "constellation_counts": {}}

            # 計算平衡分數 (越接近均勻分布越好)
            if len(constellation_counts) == 1:
                balance_score = 0.0  # 只有一個星座，平衡分數為0
            else:
                ideal_ratio = 1.0 / len(constellation_counts)
                balance_score = 1.0 - sum(abs(count / total_sats - ideal_ratio)
                                        for count in constellation_counts.values()) / 2

            return {
                "balance_score": max(0.0, balance_score),
                "constellation_counts": constellation_counts,
                "constellation_ratios": {k: v / total_sats for k, v in constellation_counts.items()}
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 星座多樣性分析失敗: {e}")
            return {"balance_score": 0.0, "error": str(e)}

    def _get_default_validation_config(self) -> Dict[str, Any]:
        """獲取預設驗證配置"""
        return {
            "min_satellites": 8,
            "max_satellites": 20,
            "min_quality_threshold": 0.6,
            "min_coverage_requirement": 0.85,
            "min_orbital_diversity": 0.6,
            "constellation_balance_required": True,
            "min_balance_score": 0.5
        }

    def get_validation_statistics(self) -> Dict[str, Any]:
        """獲取驗證統計信息"""
        return self.validation_stats.copy()