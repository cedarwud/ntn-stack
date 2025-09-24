"""
🔄 換手品質分析器 (Handover Quality Analyzer)
Satellite Processing System - Stage 3 Enhanced Module

專門負責3GPP NTN換手決策的品質分析
真正屬於Stage3的換手相關功能

版本: v1.0 - Stage3專用版本
最後更新: 2025-09-19
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

class HandoverQualityAnalyzer:
    """
    換手品質分析器

    專門負責Stage3的換手相關分析：
    1. 換手適合性評估 (基於3GPP標準)
    2. 候選衛星品質分析
    3. 換手時機預測
    4. 換手推薦生成
    """

    def __init__(self,
                 a4_threshold_dbm: float = -110.0,
                 a5_threshold1_dbm: float = -105.0,
                 a5_threshold2_dbm: float = -115.0,
                 hysteresis_db: float = 3.0):
        """
        初始化換手品質分析器

        Args:
            a4_threshold_dbm: A4事件閾值 (鄰居信號強度)
            a5_threshold1_dbm: A5事件閾值1 (服務信號)
            a5_threshold2_dbm: A5事件閾值2 (鄰居信號)
            hysteresis_db: 滯後參數
        """
        self.logger = logging.getLogger(f"{__name__}.HandoverQualityAnalyzer")

        # 3GPP NTN換手參數
        self.a4_threshold = a4_threshold_dbm
        self.a5_threshold1 = a5_threshold1_dbm
        self.a5_threshold2 = a5_threshold2_dbm
        self.hysteresis = hysteresis_db

        # 換手分析統計
        self.handover_stats = {
            "total_candidates_analyzed": 0,
            "suitable_handover_candidates": 0,
            "a4_events_triggered": 0,
            "a5_events_triggered": 0,
            "handover_recommendations_generated": 0
        }

        self.logger.info("✅ HandoverQualityAnalyzer 初始化完成")
        self.logger.info(f"   A4閾值: {a4_threshold_dbm} dBm")
        self.logger.info(f"   A5閾值1/2: {a5_threshold1_dbm}/{a5_threshold2_dbm} dBm")
        self.logger.info(f"   滯後參數: {hysteresis_db} dB")

    def evaluate_handover_suitability(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估衛星的換手適合性

        基於3GPP TS 38.331標準評估衛星是否適合作為換手目標

        Args:
            satellite_data: 衛星數據，包含信號品質時間序列

        Returns:
            換手適合性評估結果
        """
        self.logger.debug("🔹 評估換手適合性...")

        suitability_result = {
            "handover_suitable": False,
            "suitability_score": 0.0,
            "3gpp_events": {
                "a4_triggered": False,
                "a5_triggered": False,
                "d2_applicable": False
            },
            "signal_metrics": {},
            "suitability_issues": []
        }

        try:
            # 提取信號品質時間序列
            timeseries = satellite_data.get("position_timeseries", [])
            if not timeseries:
                suitability_result["suitability_issues"].append("缺少時間序列數據")
                return suitability_result

            # 分析信號品質指標
            rsrp_values = []
            rsrq_values = []
            sinr_values = []

            for position in timeseries:
                signal_data = position.get("signal_quality", {})
                if isinstance(signal_data, dict):
                    rsrp = signal_data.get("rsrp_dbm")
                    rsrq = signal_data.get("rsrq_db")
                    sinr = signal_data.get("rs_sinr_db")

                    if rsrp is not None:
                        rsrp_values.append(rsrp)
                    if rsrq is not None:
                        rsrq_values.append(rsrq)
                    if sinr is not None:
                        sinr_values.append(sinr)

            if not rsrp_values:
                suitability_result["suitability_issues"].append("缺少RSRP數據")
                return suitability_result

            # 計算信號統計
            avg_rsrp = sum(rsrp_values) / len(rsrp_values)
            max_rsrp = max(rsrp_values)
            min_rsrp = min(rsrp_values)

            suitability_result["signal_metrics"] = {
                "avg_rsrp_dbm": avg_rsrp,
                "max_rsrp_dbm": max_rsrp,
                "min_rsrp_dbm": min_rsrp,
                "rsrp_stability": max_rsrp - min_rsrp
            }

            if rsrq_values:
                suitability_result["signal_metrics"]["avg_rsrq_db"] = sum(rsrq_values) / len(rsrq_values)
            if sinr_values:
                suitability_result["signal_metrics"]["avg_sinr_db"] = sum(sinr_values) / len(sinr_values)

            # 評估3GPP事件觸發條件

            # A4事件: 鄰居信號 > 閾值 + 滯後
            if max_rsrp > (self.a4_threshold + self.hysteresis):
                suitability_result["3gpp_events"]["a4_triggered"] = True
                suitability_result["suitability_score"] += 0.4
                self.handover_stats["a4_events_triggered"] += 1

            # A5事件: 服務信號 < 閾值1 && 鄰居信號 > 閾值2
            # 這裡假設當前服務信號較弱（簡化處理）
            if avg_rsrp > self.a5_threshold2:
                suitability_result["3gpp_events"]["a5_triggered"] = True
                suitability_result["suitability_score"] += 0.4
                self.handover_stats["a5_events_triggered"] += 1

            # D2事件: 基於距離的換手（如果有距離數據）
            if self._check_d2_event_conditions(satellite_data):
                suitability_result["3gpp_events"]["d2_applicable"] = True
                suitability_result["suitability_score"] += 0.2

            # 信號品質加分
            if avg_rsrp >= -100:  # 高品質信號
                suitability_result["suitability_score"] += 0.3
            elif avg_rsrp >= -110:  # 中等品質信號
                suitability_result["suitability_score"] += 0.2

            # 信號穩定性加分
            signal_stability = max_rsrp - min_rsrp
            if signal_stability <= 10:  # 穩定信號
                suitability_result["suitability_score"] += 0.1
            elif signal_stability > 20:  # 不穩定信號
                suitability_result["suitability_issues"].append(f"信號不穩定: 變化範圍{signal_stability:.1f}dB")

            # 判定換手適合性
            if suitability_result["suitability_score"] >= 0.6:
                suitability_result["handover_suitable"] = True
                self.handover_stats["suitable_handover_candidates"] += 1

            # 更新統計
            self.handover_stats["total_candidates_analyzed"] += 1

            self.logger.debug(f"🔹 換手適合性評估完成: 適合={suitability_result['handover_suitable']}, "
                            f"分數={suitability_result['suitability_score']:.2f}")

            return suitability_result

        except Exception as e:
            self.logger.error(f"❌ 換手適合性評估失敗: {e}")
            suitability_result.update({
                "handover_suitable": False,
                "suitability_score": 0.0,
                "suitability_issues": [f"評估異常: {e}"]
            })
            return suitability_result

    def _check_d2_event_conditions(self, satellite_data: Dict[str, Any]) -> bool:
        """檢查D2事件條件（基於距離的換手）"""
        try:
            timeseries = satellite_data.get("position_timeseries", [])
            for position in timeseries:
                relative_data = position.get("relative_to_observer", {})
                if isinstance(relative_data, dict):
                    distance = relative_data.get("distance_km")
                    if distance is not None and distance < 1000:  # 1000km內認為適合D2
                        return True
            return False
        except:
            return False

    def analyze_satellite_characteristics(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析衛星特徵對換手決策的影響

        Args:
            satellite: 衛星數據

        Returns:
            衛星特徵分析結果
        """
        self.logger.debug("🔹 分析衛星特徵...")

        characteristics = {
            "constellation": "unknown",
            "orbital_characteristics": {},
            "signal_characteristics": {},
            "handover_advantage_score": 0.0,
            "recommended_usage": []
        }

        try:
            # 識別星座類型
            sat_name = satellite.get("name", "").lower()
            if "starlink" in sat_name:
                characteristics["constellation"] = "starlink"
                characteristics["handover_advantage_score"] += 0.2  # Starlink較密集
            elif "oneweb" in sat_name:
                characteristics["constellation"] = "oneweb"
                characteristics["handover_advantage_score"] += 0.3  # OneWeb較高軌道

            # 分析軌道特徵
            timeseries = satellite.get("position_timeseries", [])
            if timeseries:
                elevations = []
                distances = []

                for position in timeseries:
                    relative_data = position.get("relative_to_observer", {})
                    if isinstance(relative_data, dict):
                        elev = relative_data.get("elevation_deg")
                        dist = relative_data.get("distance_km")
                        if elev is not None:
                            elevations.append(elev)
                        if dist is not None:
                            distances.append(dist)

                if elevations:
                    max_elevation = max(elevations)
                    avg_elevation = sum(elevations) / len(elevations)

                    characteristics["orbital_characteristics"] = {
                        "max_elevation_deg": max_elevation,
                        "avg_elevation_deg": avg_elevation,
                        "elevation_range_deg": max(elevations) - min(elevations)
                    }

                    # 高仰角優勢
                    if max_elevation >= 60:
                        characteristics["handover_advantage_score"] += 0.3
                        characteristics["recommended_usage"].append("高品質通信")
                    elif max_elevation >= 30:
                        characteristics["handover_advantage_score"] += 0.2
                        characteristics["recommended_usage"].append("標準通信")

                if distances:
                    avg_distance = sum(distances) / len(distances)
                    characteristics["orbital_characteristics"]["avg_distance_km"] = avg_distance

                    # 距離優勢
                    if avg_distance < 1000:
                        characteristics["handover_advantage_score"] += 0.2
                        characteristics["recommended_usage"].append("近距離高速通信")

            # 分析信號特徵
            signal_analysis = self._analyze_signal_characteristics(satellite)
            characteristics["signal_characteristics"] = signal_analysis

            # 基於信號品質調整優勢分數
            if signal_analysis.get("avg_rsrp_dbm", -140) >= -110:
                characteristics["handover_advantage_score"] += 0.3

            self.logger.debug(f"🔹 衛星特徵分析完成: {characteristics['constellation']}, "
                            f"優勢分數={characteristics['handover_advantage_score']:.2f}")

            return characteristics

        except Exception as e:
            self.logger.error(f"❌ 衛星特徵分析失敗: {e}")
            characteristics["analysis_error"] = str(e)
            return characteristics

    def _analyze_signal_characteristics(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """分析衛星信號特徵"""
        signal_analysis = {}

        try:
            timeseries = satellite.get("position_timeseries", [])
            rsrp_values = []

            for position in timeseries:
                signal_data = position.get("signal_quality", {})
                if isinstance(signal_data, dict):
                    rsrp = signal_data.get("rsrp_dbm")
                    if rsrp is not None:
                        rsrp_values.append(rsrp)

            if rsrp_values:
                signal_analysis = {
                    "avg_rsrp_dbm": sum(rsrp_values) / len(rsrp_values),
                    "max_rsrp_dbm": max(rsrp_values),
                    "signal_samples": len(rsrp_values)
                }

        except Exception as e:
            signal_analysis["error"] = str(e)

        return signal_analysis

    def generate_handover_recommendations(self, candidate_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成換手推薦

        基於多個候選衛星的分析結果生成優化的換手建議

        Args:
            candidate_satellites: 候選衛星列表

        Returns:
            換手推薦結果
        """
        self.logger.info("🔹 生成換手推薦...")

        recommendations = {
            "primary_recommendation": {},
            "backup_recommendations": [],
            "handover_strategy": "NONE",
            "expected_handover_quality": 0.0,
            "recommendation_confidence": 0.0
        }

        try:
            if not candidate_satellites:
                recommendations["handover_strategy"] = "NO_CANDIDATES"
                return recommendations

            # 評估所有候選衛星
            evaluated_candidates = []

            for satellite in candidate_satellites:
                suitability = self.evaluate_handover_suitability(satellite)
                characteristics = self.analyze_satellite_characteristics(satellite)

                candidate_evaluation = {
                    "satellite": satellite,
                    "suitability": suitability,
                    "characteristics": characteristics,
                    "overall_score": suitability["suitability_score"] + characteristics["handover_advantage_score"]
                }
                evaluated_candidates.append(candidate_evaluation)

            # 按總分排序
            evaluated_candidates.sort(key=lambda x: x["overall_score"], reverse=True)

            # 生成主要推薦
            if evaluated_candidates:
                best_candidate = evaluated_candidates[0]
                if best_candidate["overall_score"] >= 0.8:
                    recommendations["handover_strategy"] = "IMMEDIATE"
                    recommendations["expected_handover_quality"] = best_candidate["overall_score"]
                    recommendations["recommendation_confidence"] = 0.9
                elif best_candidate["overall_score"] >= 0.6:
                    recommendations["handover_strategy"] = "PLANNED"
                    recommendations["expected_handover_quality"] = best_candidate["overall_score"]
                    recommendations["recommendation_confidence"] = 0.7
                else:
                    recommendations["handover_strategy"] = "WAIT_FOR_BETTER"
                    recommendations["recommendation_confidence"] = 0.5

                recommendations["primary_recommendation"] = {
                    "satellite_name": best_candidate["satellite"].get("name", "unknown"),
                    "constellation": best_candidate["characteristics"]["constellation"],
                    "overall_score": best_candidate["overall_score"],
                    "suitability_score": best_candidate["suitability"]["suitability_score"],
                    "3gpp_events": best_candidate["suitability"]["3gpp_events"]
                }

                # 生成備用推薦
                for candidate in evaluated_candidates[1:3]:  # 最多2個備用
                    if candidate["overall_score"] >= 0.5:
                        backup_rec = {
                            "satellite_name": candidate["satellite"].get("name", "unknown"),
                            "constellation": candidate["characteristics"]["constellation"],
                            "overall_score": candidate["overall_score"]
                        }
                        recommendations["backup_recommendations"].append(backup_rec)

            # 更新統計
            self.handover_stats["handover_recommendations_generated"] += 1

            self.logger.info(f"🔹 換手推薦完成: 策略={recommendations['handover_strategy']}, "
                           f"信心度={recommendations['recommendation_confidence']:.2f}")

            return recommendations

        except Exception as e:
            self.logger.error(f"❌ 換手推薦生成失敗: {e}")
            recommendations.update({
                "handover_strategy": "ERROR",
                "error_message": str(e)
            })
            return recommendations

    def get_handover_statistics(self) -> Dict[str, Any]:
        """
        獲取換手分析統計數據

        Returns:
            換手分析統計摘要
        """
        stats = self.handover_stats.copy()

        # 計算百分比統計
        total = stats["total_candidates_analyzed"]
        if total > 0:
            stats["suitability_rate"] = stats["suitable_handover_candidates"] / total
            stats["a4_trigger_rate"] = stats["a4_events_triggered"] / total
            stats["a5_trigger_rate"] = stats["a5_events_triggered"] / total
        else:
            stats["suitability_rate"] = 0.0
            stats["a4_trigger_rate"] = 0.0
            stats["a5_trigger_rate"] = 0.0

        return stats