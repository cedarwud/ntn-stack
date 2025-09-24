"""
📡 信號通過評估器 (Signal Pass Evaluator)
Orbit Engine System - Stage 3 Enhanced Module

專門負責評估衛星信號通過品質，支援3GPP換手決策
替代原 advanced_visibility_analyzer.py 中屬於Stage3的功能

版本: v1.0 - Stage3專用版本
最後更新: 2025-09-19
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

class SignalPassEvaluator:
    """
    信號通過評估器

    專門負責Stage3相關的信號品質評估：
    1. 信號通過品質評估
    2. 換手適合性分析
    3. 軌跡信號預測
    4. 通過窗口增強分析
    """

    def __init__(self,
                 min_signal_quality_threshold: float = -120.0,
                 handover_quality_threshold: float = -110.0):
        """
        初始化信號通過評估器

        Args:
            min_signal_quality_threshold: 最小信號品質閾值 (dBm)
            handover_quality_threshold: 換手品質閾值 (dBm)
        """
        self.logger = logging.getLogger(f"{__name__}.SignalPassEvaluator")

        self.min_signal_threshold = min_signal_quality_threshold
        self.handover_threshold = handover_quality_threshold

        # 評估統計
        self.evaluation_stats = {
            "total_passes_evaluated": 0,
            "high_quality_passes": 0,
            "handover_suitable_passes": 0,
            "avg_signal_quality": 0.0
        }

        self.logger.info("✅ SignalPassEvaluator 初始化完成")
        self.logger.info(f"   最小信號閾值: {min_signal_quality_threshold} dBm")
        self.logger.info(f"   換手品質閾值: {handover_quality_threshold} dBm")

    def evaluate_pass_quality(self, visibility_window: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估衛星通過的信號品質

        Args:
            visibility_window: 可見性窗口數據，包含時間序列信號數據

        Returns:
            通過品質評估結果
        """
        self.logger.debug("🔹 評估信號通過品質...")

        quality_result = {
            "pass_quality_score": 0.0,
            "quality_rating": "POOR",
            "signal_metrics": {},
            "quality_issues": [],
            "handover_suitability": False
        }

        try:
            # 提取時間序列信號數據
            timeseries = visibility_window.get("position_timeseries", [])
            if not timeseries:
                quality_result["quality_issues"].append("缺少時間序列數據")
                return quality_result

            # 分析信號品質指標
            signal_qualities = []
            elevations = []
            rsrp_values = []

            for position in timeseries:
                signal_data = position.get("signal_quality", {})
                relative_data = position.get("relative_to_observer", {})

                if isinstance(signal_data, dict):
                    rsrp = signal_data.get("rsrp_dbm")
                    if rsrp is not None:
                        rsrp_values.append(rsrp)

                if isinstance(relative_data, dict):
                    elevation = relative_data.get("elevation_deg")
                    if elevation is not None:
                        elevations.append(elevation)

            # 計算信號品質指標
            if rsrp_values:
                avg_rsrp = sum(rsrp_values) / len(rsrp_values)
                max_rsrp = max(rsrp_values)
                min_rsrp = min(rsrp_values)

                quality_result["signal_metrics"]["avg_rsrp_dbm"] = avg_rsrp
                quality_result["signal_metrics"]["max_rsrp_dbm"] = max_rsrp
                quality_result["signal_metrics"]["min_rsrp_dbm"] = min_rsrp
                quality_result["signal_metrics"]["rsrp_range_db"] = max_rsrp - min_rsrp

                # 計算品質分數 (基於RSRP)
                if avg_rsrp >= self.handover_threshold:
                    quality_result["pass_quality_score"] = 0.9
                    quality_result["quality_rating"] = "EXCELLENT"
                    quality_result["handover_suitability"] = True
                elif avg_rsrp >= self.min_signal_threshold:
                    quality_result["pass_quality_score"] = 0.7
                    quality_result["quality_rating"] = "GOOD"
                elif avg_rsrp >= -130.0:
                    quality_result["pass_quality_score"] = 0.5
                    quality_result["quality_rating"] = "FAIR"
                else:
                    quality_result["pass_quality_score"] = 0.2
                    quality_result["quality_rating"] = "POOR"
                    quality_result["quality_issues"].append(f"信號品質過低: {avg_rsrp:.1f} dBm")

            # 分析仰角影響
            if elevations:
                avg_elevation = sum(elevations) / len(elevations)
                max_elevation = max(elevations)

                quality_result["signal_metrics"]["avg_elevation_deg"] = avg_elevation
                quality_result["signal_metrics"]["max_elevation_deg"] = max_elevation

                # 仰角調整品質分數
                if max_elevation >= 60:  # 高仰角通過
                    quality_result["pass_quality_score"] *= 1.1
                elif max_elevation < 15:  # 低仰角通過
                    quality_result["pass_quality_score"] *= 0.8
                    quality_result["quality_issues"].append(f"仰角過低: {max_elevation:.1f}°")

            # 更新統計
            self.evaluation_stats["total_passes_evaluated"] += 1
            if quality_result["pass_quality_score"] >= 0.7:
                self.evaluation_stats["high_quality_passes"] += 1
            if quality_result["handover_suitability"]:
                self.evaluation_stats["handover_suitable_passes"] += 1

            self.logger.debug(f"🔹 通過品質評估完成: {quality_result['quality_rating']}, "
                            f"分數={quality_result['pass_quality_score']:.2f}")

            return quality_result

        except Exception as e:
            self.logger.error(f"❌ 通過品質評估失敗: {e}")
            quality_result.update({
                "pass_quality_score": 0.0,
                "quality_rating": "ERROR",
                "quality_issues": [f"評估異常: {e}"]
            })
            return quality_result

    def analyze_trajectory_signal_quality(self, satellite_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析衛星軌跡的信號品質變化

        Args:
            satellite_positions: 衛星位置時間序列

        Returns:
            軌跡信號品質分析結果
        """
        self.logger.debug("🔹 分析軌跡信號品質...")

        trajectory_analysis = {
            "signal_trajectory_quality": 0.0,
            "signal_stability": "UNKNOWN",
            "peak_signal_point": {},
            "signal_degradation_points": [],
            "trajectory_recommendations": []
        }

        try:
            if not satellite_positions:
                trajectory_analysis["trajectory_recommendations"].append("缺少軌跡數據")
                return trajectory_analysis

            # 提取信號強度序列
            signal_sequence = []
            elevation_sequence = []

            for position in satellite_positions:
                signal_data = position.get("signal_quality", {})
                relative_data = position.get("relative_to_observer", {})

                rsrp = signal_data.get("rsrp_dbm") if isinstance(signal_data, dict) else None
                elevation = relative_data.get("elevation_deg") if isinstance(relative_data, dict) else None

                if rsrp is not None and elevation is not None:
                    signal_sequence.append(rsrp)
                    elevation_sequence.append(elevation)

            if not signal_sequence:
                trajectory_analysis["trajectory_recommendations"].append("無有效信號數據")
                return trajectory_analysis

            # 分析信號穩定性
            if len(signal_sequence) > 1:
                signal_variance = sum((x - sum(signal_sequence)/len(signal_sequence))**2
                                    for x in signal_sequence) / len(signal_sequence)
                signal_std = math.sqrt(signal_variance)

                if signal_std < 5.0:
                    trajectory_analysis["signal_stability"] = "STABLE"
                    trajectory_analysis["signal_trajectory_quality"] += 0.3
                elif signal_std < 15.0:
                    trajectory_analysis["signal_stability"] = "MODERATE"
                    trajectory_analysis["signal_trajectory_quality"] += 0.2
                else:
                    trajectory_analysis["signal_stability"] = "UNSTABLE"
                    trajectory_analysis["trajectory_recommendations"].append(
                        f"信號不穩定，標準差={signal_std:.1f}dB")

                # 找出峰值信號點
                max_signal_idx = signal_sequence.index(max(signal_sequence))
                trajectory_analysis["peak_signal_point"] = {
                    "rsrp_dbm": signal_sequence[max_signal_idx],
                    "elevation_deg": elevation_sequence[max_signal_idx],
                    "position_index": max_signal_idx
                }

                # 識別信號劣化點
                for i, (rsrp, elevation) in enumerate(zip(signal_sequence, elevation_sequence)):
                    if rsrp < self.min_signal_threshold:
                        trajectory_analysis["signal_degradation_points"].append({
                            "position_index": i,
                            "rsrp_dbm": rsrp,
                            "elevation_deg": elevation,
                            "issue": "信號低於最小閾值"
                        })

            # 基於軌跡特徵調整品質分數
            avg_signal = sum(signal_sequence) / len(signal_sequence)
            max_signal = max(signal_sequence)

            if max_signal >= self.handover_threshold:
                trajectory_analysis["signal_trajectory_quality"] += 0.4
            if avg_signal >= self.min_signal_threshold:
                trajectory_analysis["signal_trajectory_quality"] += 0.3

            trajectory_analysis["signal_trajectory_quality"] = min(1.0, trajectory_analysis["signal_trajectory_quality"])

            self.logger.debug(f"🔹 軌跡信號分析完成: 穩定性={trajectory_analysis['signal_stability']}, "
                            f"品質={trajectory_analysis['signal_trajectory_quality']:.2f}")

            return trajectory_analysis

        except Exception as e:
            self.logger.error(f"❌ 軌跡信號分析失敗: {e}")
            trajectory_analysis.update({
                "signal_trajectory_quality": 0.0,
                "signal_stability": "ERROR",
                "trajectory_recommendations": [f"分析異常: {e}"]
            })
            return trajectory_analysis

    def enhance_visibility_window_with_signal_analysis(self, window_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用信號分析增強可見性窗口數據

        Args:
            window_data: 原始可見性窗口數據

        Returns:
            增強後的窗口數據，包含信號分析結果
        """
        self.logger.debug("🔹 增強可見性窗口信號分析...")

        enhanced_window = window_data.copy()

        try:
            # 執行通過品質評估
            pass_quality = self.evaluate_pass_quality(window_data)
            enhanced_window["signal_pass_quality"] = pass_quality

            # 執行軌跡信號分析
            positions = window_data.get("position_timeseries", [])
            trajectory_analysis = self.analyze_trajectory_signal_quality(positions)
            enhanced_window["signal_trajectory_analysis"] = trajectory_analysis

            # 添加增強標記
            enhanced_window["signal_analysis_enhanced"] = True
            enhanced_window["signal_analysis_timestamp"] = datetime.now(timezone.utc).isoformat()

            # 生成信號分析摘要
            signal_summary = {
                "quality_rating": pass_quality.get("quality_rating", "UNKNOWN"),
                "quality_score": pass_quality.get("pass_quality_score", 0.0),
                "handover_suitable": pass_quality.get("handover_suitability", False),
                "signal_stability": trajectory_analysis.get("signal_stability", "UNKNOWN"),
                "trajectory_quality": trajectory_analysis.get("signal_trajectory_quality", 0.0)
            }
            enhanced_window["signal_analysis_summary"] = signal_summary

            self.logger.debug(f"🔹 窗口信號分析增強完成: {signal_summary['quality_rating']}")

            return enhanced_window

        except Exception as e:
            self.logger.error(f"❌ 窗口信號分析增強失敗: {e}")
            enhanced_window["signal_analysis_error"] = str(e)
            return enhanced_window

    def get_evaluation_statistics(self) -> Dict[str, Any]:
        """
        獲取信號評估統計數據

        Returns:
            評估統計摘要
        """
        stats = self.evaluation_stats.copy()

        # 計算百分比統計
        total = stats["total_passes_evaluated"]
        if total > 0:
            stats["high_quality_rate"] = stats["high_quality_passes"] / total
            stats["handover_suitable_rate"] = stats["handover_suitable_passes"] / total
        else:
            stats["high_quality_rate"] = 0.0
            stats["handover_suitable_rate"] = 0.0

        return stats