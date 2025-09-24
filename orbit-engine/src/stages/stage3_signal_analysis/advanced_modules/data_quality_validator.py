"""
📊 數據品質驗證器 (Data Quality Validator)
Orbit Engine System - Stage 3 Enhanced Module

專門負責數據品質、採樣和時間序列的驗證
從 scientific_validator.py 拆分出來的專業驗證器

版本: v1.0 - Stage3增強版本
最後更新: 2025-09-19
"""

import logging
import json
import statistics
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class DataQualityValidator:
    """
    數據品質驗證器

    專門負責：
    1. 真實數據採樣驗證
    2. 時間序列品質檢查
    3. 星座間統計驗證
    """

    def __init__(self):
        """初始化數據品質驗證器"""
        self.logger = logging.getLogger(f"{__name__}.DataQualityValidator")

        # 預期的可見性統計
        self.EXPECTED_VISIBILITY_STATS = {
            "starlink": {"min_visible": 50, "max_visible": 300, "avg_elevation": 25},
            "oneweb": {"min_visible": 10, "max_visible": 80, "avg_elevation": 35}
        }

        self.logger.info("✅ DataQualityValidator 初始化完成")

    def validate_real_data_sampling(self, visibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證真實數據採樣品質

        檢查數據是否來自真實TLE數據，而非模擬或估算值
        """
        self.logger.info("🔹 執行真實數據採樣驗證...")

        results = {
            "sampling_passed": True,
            "data_quality_score": 1.0,
            "sampling_issues": [],
            "authenticity_indicators": {}
        }

        try:
            # 檢查metadata中的數據來源信息
            metadata = visibility_output.get("metadata", {})

            # 驗證TLE數據來源
            tle_info = metadata.get("tle_data_info", {})
            if tle_info:
                results["authenticity_indicators"]["tle_source"] = "verified"
                if "epoch" in tle_info:
                    results["authenticity_indicators"]["tle_epoch"] = tle_info["epoch"]
            else:
                results["sampling_issues"].append("缺少TLE數據來源驗證")
                results["data_quality_score"] -= 0.2

            # 檢查衛星數據分佈的自然性
            filtered_satellites = visibility_output.get("data", {}).get("filtered_satellites", {})

            for constellation, satellites in filtered_satellites.items():
                if not satellites:
                    continue

                # 檢查衛星分佈的隨機性（真實數據應該有自然變化）
                elevations = []
                azimuths = []
                distances = []

                for satellite in satellites[:20]:  # 檢查前20顆衛星
                    timeseries = satellite.get("position_timeseries", [])
                    for position in timeseries[:1]:  # 每顆衛星取1個位置
                        relative_data = position.get("relative_to_observer", {})
                        if isinstance(relative_data, dict):
                            elev = relative_data.get("elevation_deg")
                            azim = relative_data.get("azimuth_deg")
                            dist = relative_data.get("distance_km")

                            if elev is not None:
                                elevations.append(elev)
                            if azim is not None:
                                azimuths.append(azim)
                            if dist is not None:
                                distances.append(dist)

                # 分析數據分佈的自然性
                if elevations:
                    # 檢查是否存在不自然的數據模式
                    if len(set(elevations)) == 1:  # 所有值相同
                        results["sampling_issues"].append(f"{constellation}: 仰角數據過於一致，可能為模擬數據")
                        results["data_quality_score"] -= 0.3

                    # 檢查數據範圍合理性
                    elev_range = max(elevations) - min(elevations)
                    if elev_range < 5:  # 範圍太小
                        results["sampling_issues"].append(f"{constellation}: 仰角變化範圍過小 {elev_range:.1f}°")
                        results["data_quality_score"] -= 0.1

                if distances:
                    # 檢查距離分佈的合理性
                    dist_std = statistics.stdev(distances) if len(distances) > 1 else 0
                    if dist_std < 100:  # 標準差太小
                        results["sampling_issues"].append(f"{constellation}: 距離變化過小，標準差={dist_std:.1f}km")
                        results["data_quality_score"] -= 0.1

                # 記錄分析指標
                results["authenticity_indicators"][f"{constellation}_data_points"] = len(elevations)
                if elevations:
                    results["authenticity_indicators"][f"{constellation}_elevation_range"] = max(elevations) - min(elevations)
                if distances:
                    results["authenticity_indicators"][f"{constellation}_distance_std"] = statistics.stdev(distances) if len(distances) > 1 else 0

            # 檢查處理時間戳的真實性
            processing_timestamp = metadata.get("processing_timestamp")
            if processing_timestamp:
                try:
                    proc_time = datetime.fromisoformat(processing_timestamp.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    time_diff = abs((now - proc_time).total_seconds())

                    if time_diff > 3600:  # 超過1小時
                        results["sampling_issues"].append(f"處理時間戳異常，時差={time_diff/3600:.1f}小時")
                        results["data_quality_score"] -= 0.1

                    results["authenticity_indicators"]["processing_time_freshness"] = f"{time_diff:.0f}秒前"
                except:
                    results["sampling_issues"].append("處理時間戳格式無效")
                    results["data_quality_score"] -= 0.1

            # 判定採樣品質是否通過
            if results["data_quality_score"] < 0.7:
                results["sampling_passed"] = False

            self.logger.info(f"🔹 真實數據採樣驗證: 通過={results['sampling_passed']}, "
                           f"品質分數={results['data_quality_score']:.3f}")

            return results

        except Exception as e:
            self.logger.error(f"❌ 真實數據採樣驗證失敗: {e}")
            results.update({
                "sampling_passed": False,
                "data_quality_score": 0.0,
                "sampling_issues": [f"採樣驗證異常: {e}"]
            })
            return results

    def validate_timeseries_quality(self, visibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證時間序列數據品質

        檢查時間序列的連續性、完整性和一致性
        """
        self.logger.info("🔹 執行時間序列品質驗證...")

        results = {
            "timeseries_passed": True,
            "continuity_score": 1.0,
            "quality_issues": [],
            "timeseries_stats": {}
        }

        try:
            filtered_satellites = visibility_output.get("data", {}).get("filtered_satellites", {})

            total_satellites = 0
            quality_violations = 0

            for constellation, satellites in filtered_satellites.items():
                constellation_stats = {
                    "satellite_count": len(satellites),
                    "avg_timeseries_length": 0,
                    "continuity_issues": 0
                }

                timeseries_lengths = []

                for satellite in satellites[:10]:  # 檢查前10顆衛星
                    total_satellites += 1

                    timeseries = satellite.get("position_timeseries", [])
                    timeseries_lengths.append(len(timeseries))

                    if len(timeseries) < 2:  # 時間序列太短
                        quality_violations += 1
                        results["quality_issues"].append(f"{constellation}: 時間序列過短 ({len(timeseries)}個點)")
                        constellation_stats["continuity_issues"] += 1
                        continue

                    # 檢查時間序列的時間戳連續性
                    timestamps = []
                    for position in timeseries:
                        timestamp = position.get("timestamp")
                        if timestamp:
                            timestamps.append(timestamp)

                    if len(timestamps) != len(timeseries):
                        quality_violations += 1
                        results["quality_issues"].append(f"{constellation}: 時間戳缺失")
                        constellation_stats["continuity_issues"] += 1

                    # 檢查數據完整性
                    for pos_idx, position in enumerate(timeseries):
                        relative_data = position.get("relative_to_observer", {})
                        if not isinstance(relative_data, dict):
                            quality_violations += 1
                            results["quality_issues"].append(f"{constellation}: 位置{pos_idx}缺少相對觀測者數據")
                            constellation_stats["continuity_issues"] += 1
                            break

                        # 檢查關鍵數據字段
                        required_fields = ["elevation_deg", "azimuth_deg", "distance_km"]
                        missing_fields = [field for field in required_fields if relative_data.get(field) is None]

                        if missing_fields:
                            quality_violations += 1
                            results["quality_issues"].append(f"{constellation}: 位置{pos_idx}缺少字段{missing_fields}")
                            constellation_stats["continuity_issues"] += 1
                            break

                # 統計星座數據品質
                if timeseries_lengths:
                    constellation_stats["avg_timeseries_length"] = sum(timeseries_lengths) / len(timeseries_lengths)
                    constellation_stats["min_timeseries_length"] = min(timeseries_lengths)
                    constellation_stats["max_timeseries_length"] = max(timeseries_lengths)

                results["timeseries_stats"][constellation] = constellation_stats

            # 計算連續性分數
            if total_satellites > 0:
                violation_rate = quality_violations / total_satellites
                results["continuity_score"] = max(0.0, 1.0 - violation_rate * 1.0)

            # 判定時間序列品質是否通過
            if results["continuity_score"] < 0.8:
                results["timeseries_passed"] = False

            self.logger.info(f"🔹 時間序列品質驗證: 通過={results['timeseries_passed']}, "
                           f"連續性分數={results['continuity_score']:.3f}, "
                           f"違規={quality_violations}/{total_satellites}")

            return results

        except Exception as e:
            self.logger.error(f"❌ 時間序列品質驗證失敗: {e}")
            results.update({
                "timeseries_passed": False,
                "continuity_score": 0.0,
                "quality_issues": [f"時間序列驗證異常: {e}"]
            })
            return results

    def validate_inter_constellation_statistics(self, visibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證星座間統計數據

        檢查 Starlink 和 OneWeb 的相對統計是否符合預期
        """
        self.logger.info("🔹 執行星座間統計驗證...")

        results = {
            "statistics_passed": True,
            "statistical_score": 1.0,
            "constellation_comparison": {}
        }

        try:
            filtered_satellites = visibility_output.get("data", {}).get("filtered_satellites", {})

            # 分析各星座統計
            for constellation, satellites in filtered_satellites.items():
                stats = {
                    "satellite_count": len(satellites),
                    "expected_range": self.EXPECTED_VISIBILITY_STATS.get(constellation, {}),
                    "meets_expectations": True
                }

                expected = self.EXPECTED_VISIBILITY_STATS.get(constellation, {})

                # 檢查衛星數量是否在預期範圍內
                if expected:
                    min_expected = expected.get("min_visible", 0)
                    max_expected = expected.get("max_visible", 1000)

                    if len(satellites) < min_expected:
                        stats["meets_expectations"] = False
                        stats["issue"] = f"衛星數量過少: {len(satellites)} < {min_expected}"
                    elif len(satellites) > max_expected:
                        stats["meets_expectations"] = False
                        stats["issue"] = f"衛星數量過多: {len(satellites)} > {max_expected}"

                results["constellation_comparison"][constellation] = stats

            # 檢查Starlink vs OneWeb比例
            starlink_count = len(filtered_satellites.get("starlink", []))
            oneweb_count = len(filtered_satellites.get("oneweb", []))

            if starlink_count > 0 and oneweb_count > 0:
                ratio = starlink_count / oneweb_count
                results["constellation_comparison"]["starlink_to_oneweb_ratio"] = ratio

                # Starlink通常應該比OneWeb多（不同軌道高度）
                if ratio < 2.0:  # 預期比例至少2:1
                    results["statistical_score"] -= 0.2
                    results["constellation_comparison"]["ratio_issue"] = f"Starlink/OneWeb比例偏低: {ratio:.1f}"

            # 計算整體統計分數
            failed_constellations = sum(1 for stats in results["constellation_comparison"].values()
                                      if isinstance(stats, dict) and not stats.get("meets_expectations", True))

            if len(filtered_satellites) > 0:
                success_rate = 1.0 - (failed_constellations / len(filtered_satellites))
                results["statistical_score"] *= success_rate

            # 判定統計驗證是否通過
            if results["statistical_score"] < 0.7:
                results["statistics_passed"] = False

            self.logger.info(f"🔹 星座間統計驗證: 通過={results['statistics_passed']}, "
                           f"統計分數={results['statistical_score']:.3f}")

            return results

        except Exception as e:
            self.logger.error(f"❌ 星座間統計驗證失敗: {e}")
            results.update({
                "statistics_passed": False,
                "statistical_score": 0.0,
                "constellation_comparison": {"error": str(e)}
            })
            return results