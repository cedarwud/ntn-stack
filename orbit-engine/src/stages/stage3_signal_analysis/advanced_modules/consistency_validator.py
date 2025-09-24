"""
🔄 一致性驗證器 (Consistency Validator)
Orbit Engine System - Stage 3 Enhanced Module

專門負責跨階段數據一致性和錯誤傳播分析
從 scientific_validator.py 拆分出來的專業驗證器

版本: v1.0 - Stage3增強版本
最後更新: 2025-09-19
"""

import logging
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class ConsistencyValidator:
    """
    一致性驗證器

    專門負責：
    1. 跨階段錯誤傳播分析
    2. 時間戳一致性檢查
    3. 座標系統一致性驗證
    """

    def __init__(self):
        """初始化一致性驗證器"""
        self.logger = logging.getLogger(f"{__name__}.ConsistencyValidator")
        self.logger.info("✅ ConsistencyValidator 初始化完成")

    def analyze_error_propagation(self,
                                 visibility_output: Dict[str, Any],
                                 stage1_orbital_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析跨階段錯誤傳播

        檢查從Stage1到Stage3的數據傳遞過程中是否存在系統性錯誤
        """
        self.logger.info("🔹 執行跨階段錯誤傳播分析...")

        results = {
            "propagation_analysis_passed": True,
            "error_propagation_score": 1.0,
            "propagation_issues": [],
            "stage_comparison": {}
        }

        try:
            # 提取Stage1和當前Stage的metadata進行比較
            stage1_metadata = stage1_orbital_data.get("metadata", {})
            stage2_metadata = visibility_output.get("metadata", {})

            # 比較衛星總數的變化
            stage1_total = stage1_metadata.get("total_satellites_processed", 0)
            stage2_total = stage2_metadata.get("total_visible_satellites", 0)

            if stage1_total > 0:
                filtering_rate = stage2_total / stage1_total
                results["stage_comparison"]["filtering_rate"] = filtering_rate

                # 檢查過濾率是否合理（應該在10%-80%之間）
                if filtering_rate < 0.1:
                    results["propagation_issues"].append(f"過濾率過低: {filtering_rate:.1%} - 可能存在系統性錯誤")
                    results["error_propagation_score"] -= 0.3
                elif filtering_rate > 0.8:
                    results["propagation_issues"].append(f"過濾率過高: {filtering_rate:.1%} - 可能篩選條件過鬆")
                    results["error_propagation_score"] -= 0.1

            # 檢查觀測者座標一致性
            stage1_observer = stage1_metadata.get("observer_coordinates", {})
            stage2_observer = stage2_metadata.get("observer_coordinates", {})

            if stage1_observer and stage2_observer:
                lat_diff = abs(stage1_observer.get("latitude", 0) - stage2_observer.get("latitude", 0))
                lon_diff = abs(stage1_observer.get("longitude", 0) - stage2_observer.get("longitude", 0))

                if lat_diff > 0.001 or lon_diff > 0.001:  # 超過1米的差異
                    results["propagation_issues"].append(f"觀測者座標不一致: 緯度差{lat_diff:.6f}°, 經度差{lon_diff:.6f}°")
                    results["error_propagation_score"] -= 0.2

            # 檢查時間基準一致性
            self._analyze_timestamp_consistency(results, stage1_orbital_data, visibility_output)

            # 檢查座標系統一致性
            self._analyze_coordinate_consistency(results, stage1_orbital_data, visibility_output)

            # 判定錯誤傳播分析是否通過
            if results["error_propagation_score"] < 0.7:
                results["propagation_analysis_passed"] = False

            self.logger.info(f"🔹 錯誤傳播分析: 通過={results['propagation_analysis_passed']}, "
                           f"分數={results['error_propagation_score']:.3f}")

            return results

        except Exception as e:
            self.logger.error(f"❌ 錯誤傳播分析失敗: {e}")
            results.update({
                "propagation_analysis_passed": False,
                "error_propagation_score": 0.0,
                "propagation_issues": [f"錯誤傳播分析異常: {e}"]
            })
            return results

    def _analyze_timestamp_consistency(self,
                                     results: Dict,
                                     stage1_data: Dict,
                                     stage2_data: Dict) -> None:
        """分析時間戳一致性"""
        stage1_time = stage1_data.get("metadata", {}).get("processing_timestamp")
        stage2_time = stage2_data.get("metadata", {}).get("processing_timestamp")

        if stage1_time and stage2_time:
            try:
                t1 = datetime.fromisoformat(stage1_time.replace('Z', '+00:00'))
                t2 = datetime.fromisoformat(stage2_time.replace('Z', '+00:00'))

                time_diff = abs((t2 - t1).total_seconds())
                results["stage_comparison"]["processing_time_diff_seconds"] = time_diff

                if time_diff > 3600:  # 超過1小時的處理間隔
                    results["propagation_issues"].append(f"處理時間間隔過長: {time_diff/3600:.1f}小時")
                    results["error_propagation_score"] -= 0.1

            except Exception as e:
                results["propagation_issues"].append(f"時間戳解析錯誤: {e}")
                results["error_propagation_score"] -= 0.1

    def _analyze_coordinate_consistency(self,
                                      results: Dict,
                                      stage1_data: Dict,
                                      stage2_data: Dict) -> None:
        """分析座標系統一致性"""
        # 檢查觀測者座標是否在各階段保持一致
        stage1_observer = stage1_data.get("metadata", {}).get("observer_coordinates", {})
        stage2_observer = stage2_data.get("metadata", {}).get("observer_coordinates", {})

        if stage1_observer and stage2_observer:
            lat_diff = abs(stage1_observer.get("latitude", 0) - stage2_observer.get("latitude", 0))
            lon_diff = abs(stage1_observer.get("longitude", 0) - stage2_observer.get("longitude", 0))

            results["stage_comparison"]["observer_coordinate_drift"] = {
                "latitude_diff_deg": lat_diff,
                "longitude_diff_deg": lon_diff
            }

            if lat_diff > 0.001 or lon_diff > 0.001:
                results["propagation_issues"].append("觀測者座標在階段間發生漂移")
                results["error_propagation_score"] -= 0.2

    def validate_cross_stage_consistency(self,
                                       current_stage_data: Dict[str, Any],
                                       previous_stage_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        驗證跨階段數據一致性

        檢查當前階段數據與前一階段數據的一致性
        """
        self.logger.info("🔹 執行跨階段一致性驗證...")

        results = {
            "consistency_passed": True,
            "consistency_score": 1.0,
            "consistency_issues": [],
            "data_lineage": {}
        }

        try:
            if not previous_stage_data:
                results["consistency_issues"].append("缺少前一階段數據進行比較")
                results["consistency_score"] = 0.8
                return results

            # 檢查數據lineage（數據族系）
            current_metadata = current_stage_data.get("metadata", {})
            previous_metadata = previous_stage_data.get("metadata", {})

            # 驗證數據處理鏈的連續性
            previous_stage_name = previous_metadata.get("stage_name", "unknown")
            current_stage_name = current_metadata.get("stage_name", "unknown")

            results["data_lineage"]["previous_stage"] = previous_stage_name
            results["data_lineage"]["current_stage"] = current_stage_name

            # 檢查數據量的合理變化
            previous_count = previous_metadata.get("total_satellites_processed", 0)
            current_count = current_metadata.get("total_satellites_processed", 0)

            if previous_count > 0 and current_count > 0:
                retention_rate = current_count / previous_count
                results["data_lineage"]["data_retention_rate"] = retention_rate

                # 檢查數據保留率是否合理
                if retention_rate > 1.1:  # 數據不應該增加超過10%
                    results["consistency_issues"].append(f"數據量異常增加: {retention_rate:.1%}")
                    results["consistency_score"] -= 0.2
                elif retention_rate < 0.05:  # 數據不應該減少超過95%
                    results["consistency_issues"].append(f"數據量過度減少: {retention_rate:.1%}")
                    results["consistency_score"] -= 0.3

            # 檢查關鍵配置參數的一致性
            config_consistency = self._check_config_consistency(current_metadata, previous_metadata)
            if not config_consistency["passed"]:
                results["consistency_issues"].extend(config_consistency["issues"])
                results["consistency_score"] -= 0.1

            # 判定一致性驗證是否通過
            if results["consistency_score"] < 0.7:
                results["consistency_passed"] = False

            self.logger.info(f"🔹 跨階段一致性驗證: 通過={results['consistency_passed']}, "
                           f"分數={results['consistency_score']:.3f}")

            return results

        except Exception as e:
            self.logger.error(f"❌ 跨階段一致性驗證失敗: {e}")
            results.update({
                "consistency_passed": False,
                "consistency_score": 0.0,
                "consistency_issues": [f"一致性驗證異常: {e}"]
            })
            return results

    def _check_config_consistency(self,
                                current_metadata: Dict[str, Any],
                                previous_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """檢查配置參數的一致性"""
        consistency_result = {
            "passed": True,
            "issues": []
        }

        # 檢查觀測者座標
        current_observer = current_metadata.get("observer_coordinates", {})
        previous_observer = previous_metadata.get("observer_coordinates", {})

        if current_observer and previous_observer:
            for coord in ["latitude", "longitude", "altitude_m"]:
                current_val = current_observer.get(coord, 0)
                previous_val = previous_observer.get(coord, 0)

                if abs(current_val - previous_val) > 0.001:  # 1米或0.001度的容差
                    consistency_result["passed"] = False
                    consistency_result["issues"].append(f"觀測者{coord}不一致: {previous_val} → {current_val}")

        # 檢查處理時間基準
        current_base_time = current_metadata.get("calculation_base_time")
        previous_base_time = previous_metadata.get("calculation_base_time")

        if current_base_time and previous_base_time:
            if current_base_time != previous_base_time:
                consistency_result["passed"] = False
                consistency_result["issues"].append(f"計算基準時間不一致: {previous_base_time} → {current_base_time}")

        return consistency_result

    def generate_consistency_report(self,
                                  all_stage_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成整體一致性報告

        彙總所有階段的一致性分析結果
        """
        self.logger.info("🔹 生成一致性驗證報告...")

        report = {
            "overall_consistency": "PASSED",
            "total_stages_analyzed": len(all_stage_results),
            "consistency_scores": [],
            "critical_issues": [],
            "recommendations": []
        }

        try:
            for i, stage_result in enumerate(all_stage_results):
                stage_name = f"Stage_{i+1}"

                if isinstance(stage_result, dict):
                    consistency_score = stage_result.get("consistency_score", 0.0)
                    report["consistency_scores"].append({
                        "stage": stage_name,
                        "score": consistency_score,
                        "passed": stage_result.get("consistency_passed", False)
                    })

                    # 收集重要問題
                    issues = stage_result.get("consistency_issues", [])
                    for issue in issues:
                        if any(keyword in issue.lower() for keyword in ["異常", "錯誤", "失敗", "不一致"]):
                            report["critical_issues"].append(f"{stage_name}: {issue}")

            # 計算整體分數
            if report["consistency_scores"]:
                avg_score = sum(s["score"] for s in report["consistency_scores"]) / len(report["consistency_scores"])
                failed_stages = sum(1 for s in report["consistency_scores"] if not s["passed"])

                if avg_score < 0.7 or failed_stages > len(report["consistency_scores"]) * 0.3:
                    report["overall_consistency"] = "FAILED"

                # 生成建議
                if avg_score < 0.8:
                    report["recommendations"].append("建議檢查數據處理鏈的一致性配置")
                if failed_stages > 0:
                    report["recommendations"].append(f"有{failed_stages}個階段存在一致性問題，需要詳細檢查")

            self.logger.info(f"🔹 一致性報告生成完成: {report['overall_consistency']}")

            return report

        except Exception as e:
            self.logger.error(f"❌ 一致性報告生成失敗: {e}")
            return {
                "overall_consistency": "ERROR",
                "error_message": str(e),
                "total_stages_analyzed": 0
            }