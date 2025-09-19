"""
🧪 科學驗證引擎主控制器 (Scientific Validation Engine)
Satellite Processing System - Stage 3 Enhanced Module

整合所有專業驗證器的主控制器
重構自原始 scientific_validator.py (832行) → 精簡主控制器 (~100行)

版本: v2.0 - 模組化重構版本
最後更新: 2025-09-19

架構說明：
- ScientificValidationEngine: 主控制器，整合各驗證器
- GeometricPhysicsValidator: 幾何物理驗證專家
- DataQualityValidator: 數據品質驗證專家
- ConsistencyValidator: 一致性驗證專家
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# 導入專業驗證器
try:
    from .geometric_physics_validator import GeometricPhysicsValidator
    from .data_quality_validator import DataQualityValidator
    from .consistency_validator import ConsistencyValidator
except ImportError:
    # 支援直接執行時的絕對導入
    from geometric_physics_validator import GeometricPhysicsValidator
    from data_quality_validator import DataQualityValidator
    from consistency_validator import ConsistencyValidator

class ScientificValidationEngine:
    """
    科學驗證引擎主控制器

    整合所有專業驗證器，提供統一的科學驗證接口：
    1. 幾何物理驗證 (GeometricPhysicsValidator)
    2. 數據品質驗證 (DataQualityValidator)
    3. 一致性驗證 (ConsistencyValidator)
    """

    def __init__(self, observer_lat: float = 25.0175, observer_lon: float = 121.5398):
        """
        初始化科學驗證引擎主控制器

        Args:
            observer_lat: 觀測者緯度 (NTPU)
            observer_lon: 觀測者經度 (NTPU)
        """
        self.logger = logging.getLogger(f"{__name__}.ScientificValidationEngine")

        # 初始化專業驗證器
        try:
            self.geometric_validator = GeometricPhysicsValidator(observer_lat, observer_lon)
            self.quality_validator = DataQualityValidator()
            self.consistency_validator = ConsistencyValidator()

            self.logger.info("✅ ScientificValidationEngine 主控制器初始化完成")
            self.logger.info("📊 已整合: 幾何物理驗證器、數據品質驗證器、一致性驗證器")

        except Exception as e:
            self.logger.error(f"❌ 科學驗證引擎初始化失敗: {e}")
            raise RuntimeError(f"科學驗證引擎初始化失敗: {e}")

    def perform_comprehensive_scientific_validation(self,
                                                   visibility_output: Dict[str, Any],
                                                   stage1_orbital_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        執行全面科學驗證

        Args:
            visibility_output: 階段二可見性輸出數據
            stage1_orbital_data: 階段一軌道計算數據 (用於誤差分析)

        Returns:
            全面的科學驗證結果
        """
        self.logger.info("🔬 開始執行全面科學驗證...")

        comprehensive_results = {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_validation_passed": True,
            "scientific_quality_score": 1.0,
            "validation_modules": {
                "geometric_physics": {},
                "data_quality": {},
                "consistency": {}
            },
            "critical_issues": [],
            "recommendations": []
        }

        try:
            # 1. 幾何物理驗證
            self.logger.info("🔹 執行幾何物理驗證...")
            geometric_results = self._run_geometric_physics_validation(visibility_output)
            comprehensive_results["validation_modules"]["geometric_physics"] = geometric_results

            # 2. 數據品質驗證
            self.logger.info("🔹 執行數據品質驗證...")
            quality_results = self._run_data_quality_validation(visibility_output)
            comprehensive_results["validation_modules"]["data_quality"] = quality_results

            # 3. 一致性驗證 (如果有Stage1數據)
            if stage1_orbital_data:
                self.logger.info("🔹 執行跨階段一致性驗證...")
                consistency_results = self._run_consistency_validation(visibility_output, stage1_orbital_data)
                comprehensive_results["validation_modules"]["consistency"] = consistency_results

            # 4. 計算整體科學品質分數
            overall_score = self._calculate_scientific_quality_score(comprehensive_results)
            comprehensive_results["scientific_quality_score"] = overall_score

            # 5. 判定整體驗證是否通過
            if overall_score < 0.7:
                comprehensive_results["overall_validation_passed"] = False
                comprehensive_results["critical_issues"].append("整體科學品質分數低於閾值")

            # 6. 生成建議
            self._generate_validation_recommendations(comprehensive_results)

            self.logger.info(f"🔬 全面科學驗證完成: 通過={comprehensive_results['overall_validation_passed']}, "
                           f"品質分數={overall_score:.3f}")

            return comprehensive_results

        except Exception as e:
            self.logger.error(f"❌ 全面科學驗證失敗: {e}")
            comprehensive_results.update({
                "overall_validation_passed": False,
                "scientific_quality_score": 0.0,
                "critical_issues": [f"驗證過程異常: {e}"]
            })
            return comprehensive_results

    def _run_geometric_physics_validation(self, visibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """執行幾何物理驗證"""
        geometric_results = {}

        # 幾何計算驗證
        geom_calc_result = self.geometric_validator.validate_geometric_calculations(visibility_output)
        geometric_results["geometric_calculations"] = geom_calc_result

        # 物理約束驗證
        physics_result = self.geometric_validator.validate_physics_constraints(visibility_output)
        geometric_results["physics_constraints"] = physics_result

        # 星座物理分析
        constellation_result = self.geometric_validator.analyze_constellation_physics(visibility_output)
        geometric_results["constellation_physics"] = constellation_result

        return geometric_results

    def _run_data_quality_validation(self, visibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """執行數據品質驗證"""
        quality_results = {}

        # 真實數據採樣驗證
        sampling_result = self.quality_validator.validate_real_data_sampling(visibility_output)
        quality_results["real_data_sampling"] = sampling_result

        # 時間序列品質驗證
        timeseries_result = self.quality_validator.validate_timeseries_quality(visibility_output)
        quality_results["timeseries_quality"] = timeseries_result

        # 星座間統計驗證
        statistics_result = self.quality_validator.validate_inter_constellation_statistics(visibility_output)
        quality_results["inter_constellation_statistics"] = statistics_result

        return quality_results

    def _run_consistency_validation(self,
                                   visibility_output: Dict[str, Any],
                                   stage1_orbital_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行一致性驗證"""
        consistency_results = {}

        # 跨階段錯誤傳播分析
        error_propagation_result = self.consistency_validator.analyze_error_propagation(
            visibility_output, stage1_orbital_data)
        consistency_results["error_propagation"] = error_propagation_result

        # 跨階段數據一致性
        cross_stage_result = self.consistency_validator.validate_cross_stage_consistency(
            visibility_output, stage1_orbital_data)
        consistency_results["cross_stage_consistency"] = cross_stage_result

        return consistency_results

    def _calculate_scientific_quality_score(self, comprehensive_results: Dict[str, Any]) -> float:
        """計算整體科學品質分數"""
        scores = []
        weights = {}

        # 收集各模組分數
        modules = comprehensive_results["validation_modules"]

        # 幾何物理分數 (權重: 0.4)
        geometric = modules.get("geometric_physics", {})
        if geometric:
            geom_scores = []
            for test_result in geometric.values():
                if isinstance(test_result, dict):
                    score = test_result.get("accuracy_score") or test_result.get("physics_score", 0)
                    geom_scores.append(score)
            if geom_scores:
                scores.append(sum(geom_scores) / len(geom_scores))
                weights[len(scores)-1] = 0.4

        # 數據品質分數 (權重: 0.35)
        quality = modules.get("data_quality", {})
        if quality:
            quality_scores = []
            for test_result in quality.values():
                if isinstance(test_result, dict):
                    score = (test_result.get("data_quality_score") or
                           test_result.get("continuity_score") or
                           test_result.get("statistical_score", 0))
                    quality_scores.append(score)
            if quality_scores:
                scores.append(sum(quality_scores) / len(quality_scores))
                weights[len(scores)-1] = 0.35

        # 一致性分數 (權重: 0.25)
        consistency = modules.get("consistency", {})
        if consistency:
            consistency_scores = []
            for test_result in consistency.values():
                if isinstance(test_result, dict):
                    score = (test_result.get("error_propagation_score") or
                           test_result.get("consistency_score", 0))
                    consistency_scores.append(score)
            if consistency_scores:
                scores.append(sum(consistency_scores) / len(consistency_scores))
                weights[len(scores)-1] = 0.25

        # 計算加權平均
        if scores:
            total_weight = sum(weights.values())
            if total_weight > 0:
                weighted_score = sum(score * weights.get(i, 1.0) for i, score in enumerate(scores)) / total_weight
                return max(0.0, min(1.0, weighted_score))

        return 0.0

    def _generate_validation_recommendations(self, comprehensive_results: Dict[str, Any]) -> None:
        """生成驗證建議"""
        recommendations = []

        # 基於各模組結果生成建議
        modules = comprehensive_results["validation_modules"]
        score = comprehensive_results["scientific_quality_score"]

        if score < 0.8:
            recommendations.append("建議檢查數據處理流程，整體科學品質需要改善")

        # 檢查幾何物理問題
        geometric = modules.get("geometric_physics", {})
        for test_name, test_result in geometric.items():
            if isinstance(test_result, dict) and not test_result.get("test_passed", True):
                recommendations.append(f"建議檢查{test_name}的計算精度")

        # 檢查數據品質問題
        quality = modules.get("data_quality", {})
        for test_name, test_result in quality.items():
            if isinstance(test_result, dict) and not test_result.get("sampling_passed", test_result.get("timeseries_passed", True)):
                recommendations.append(f"建議改善{test_name}的數據品質")

        comprehensive_results["recommendations"] = recommendations


def create_scientific_validator(observer_lat: float = 25.0175,
                              observer_lon: float = 121.5398) -> ScientificValidationEngine:
    """
    工廠函數：創建科學驗證引擎實例

    Args:
        observer_lat: 觀測者緯度 (NTPU)
        observer_lon: 觀測者經度 (NTPU)

    Returns:
        配置好的科學驗證引擎實例
    """
    return ScientificValidationEngine(observer_lat, observer_lon)


# 向後兼容性支援
if __name__ == "__main__":
    # 測試科學驗證引擎
    validator = create_scientific_validator()

    # 測試數據
    test_visibility_output = {
        "data": {"filtered_satellites": {"starlink": [], "oneweb": []}},
        "metadata": {"total_visible_satellites": 100}
    }

    results = validator.perform_comprehensive_scientific_validation(test_visibility_output)
    print(f"驗證結果: {results['overall_validation_passed']}")
    print(f"科學品質分數: {results['scientific_quality_score']:.3f}")