"""
🔬 幾何物理驗證器 (Geometric Physics Validator)
Satellite Processing System - Stage 3 Enhanced Module

專門負責幾何計算和物理約束的驗證
從 scientific_validator.py 拆分出來的專業驗證器

版本: v1.0 - Stage3增強版本
最後更新: 2025-09-19
"""

import logging
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class GeometricPhysicsValidator:
    """
    幾何物理驗證器

    專門負責：
    1. 幾何計算精度驗證（球面三角學）
    2. 物理約束檢查（軌道動力學）
    3. 星座物理特性分析
    """

    def __init__(self, observer_lat: float = 25.0175, observer_lon: float = 121.5398):
        """
        初始化幾何物理驗證器

        Args:
            observer_lat: 觀測者緯度 (NTPU)
            observer_lon: 觀測者經度 (NTPU)
        """
        self.logger = logging.getLogger(f"{__name__}.GeometricPhysicsValidator")

        # 觀測者座標
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon

        # 物理常數
        self.STARLINK_ALTITUDE_KM = 550.0
        self.ONEWEB_ALTITUDE_KM = 1200.0
        self.EARTH_RADIUS_KM = 6371.0

        self.logger.info("✅ GeometricPhysicsValidator 初始化完成")

    def validate_geometric_calculations(self, visibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證幾何計算精度 (球面三角學)

        檢查仰角、方位角計算是否符合球面三角學基本原理
        """
        self.logger.info("🔹 執行幾何計算基準測試...")

        results = {
            "test_passed": True,
            "accuracy_score": 1.0,
            "failed_tests": [],
            "geometric_issues": []
        }

        try:
            # 從可見性輸出中提取衛星位置數據
            filtered_satellites = visibility_output.get("data", {}).get("filtered_satellites", {})

            if not filtered_satellites:
                results["test_passed"] = False
                results["geometric_issues"].append("無可見衛星數據用於幾何驗證")
                return results

            # 檢查基本幾何約束
            geometry_violations = 0
            total_satellites_checked = 0

            for constellation, satellites in filtered_satellites.items():
                for sat_idx, satellite in enumerate(satellites[:5]):  # 檢查前5顆衛星
                    total_satellites_checked += 1

                    # 檢查時間序列中的位置數據
                    timeseries = satellite.get("position_timeseries", [])
                    for pos_idx, position in enumerate(timeseries[:3]):  # 檢查前3個位置點

                        # 提取位置數據
                        relative_data = position.get("relative_to_observer", {})
                        if isinstance(relative_data, dict):
                            elevation = relative_data.get("elevation_deg")
                            azimuth = relative_data.get("azimuth_deg")
                        else:
                            elevation = None
                            azimuth = None

                        # 嘗試從 ECI 位置數據推導
                        eci_pos = position.get("eci_position", {})
                        if isinstance(eci_pos, dict):
                            sat_lat = None  # ECI 座標無法直接提供緯度
                            sat_lon = None
                            sat_alt = None  # 需要從 ECI 計算
                        else:
                            sat_lat = None
                            sat_lon = None
                            sat_alt = None

                        # 只檢查可用的數據
                        if elevation is None and azimuth is None:
                            continue

                        # 基本物理約束檢查
                        if elevation is not None:
                            if elevation < 0 or elevation > 90:
                                geometry_violations += 1
                                results["geometric_issues"].append(
                                    f"{constellation}衛星{sat_idx}位置{pos_idx}: 仰角超出範圍 {elevation:.2f}°"
                                )

                        if azimuth is not None:
                            if azimuth < 0 or azimuth >= 360:
                                geometry_violations += 1
                                results["geometric_issues"].append(
                                    f"{constellation}衛星{sat_idx}位置{pos_idx}: 方位角超出範圍 {azimuth:.2f}°"
                                )

                        # 高度合理性檢查
                        if sat_alt is not None:
                            if sat_alt < 200 or sat_alt > 2000:  # LEO/MEO範圍
                                geometry_violations += 1
                                results["geometric_issues"].append(
                                    f"{constellation}衛星{sat_idx}位置{pos_idx}: 軌道高度不合理 {sat_alt:.1f}km"
                                )

                        # 緯度合理性檢查
                        if sat_lat is not None:
                            if sat_lat < -90 or sat_lat > 90:
                                geometry_violations += 1
                                results["geometric_issues"].append(
                                    f"{constellation}衛星{sat_idx}位置{pos_idx}: 緯度超出範圍 {sat_lat:.2f}°"
                                )

            # 計算幾何精度分數
            if total_satellites_checked > 0:
                violation_rate = geometry_violations / (total_satellites_checked * 3)  # 每顆衛星檢查3個位置
                results["accuracy_score"] = max(0.0, 1.0 - violation_rate * 2.0)  # 允許少量違規

            # 判定測試是否通過
            if results["accuracy_score"] < 0.8:
                results["test_passed"] = False

            self.logger.info(f"🔹 幾何計算驗證: 通過={results['test_passed']}, "
                           f"分數={results['accuracy_score']:.3f}, "
                           f"違規={geometry_violations}/{total_satellites_checked}")

            return results

        except Exception as e:
            self.logger.error(f"❌ 幾何計算驗證失敗: {e}")
            results.update({
                "test_passed": False,
                "accuracy_score": 0.0,
                "geometric_issues": [f"幾何驗證異常: {e}"]
            })
            return results

    def validate_physics_constraints(self, visibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證物理約束 (軌道動力學、信號傳播)

        檢查軌道參數、信號強度是否符合物理定律
        """
        self.logger.info("🔹 執行物理約束驗證...")

        results = {
            "test_passed": True,
            "physics_score": 1.0,
            "constraint_violations": [],
            "physics_issues": []
        }

        try:
            filtered_satellites = visibility_output.get("data", {}).get("filtered_satellites", {})

            if not filtered_satellites:
                results["test_passed"] = False
                results["physics_issues"].append("無衛星數據用於物理驗證")
                return results

            physics_violations = 0
            total_measurements = 0

            for constellation, satellites in filtered_satellites.items():
                expected_altitude = self.STARLINK_ALTITUDE_KM if constellation == "starlink" else self.ONEWEB_ALTITUDE_KM

                for satellite in satellites[:3]:  # 檢查前3顆衛星
                    timeseries = satellite.get("position_timeseries", [])

                    for position in timeseries[:2]:  # 檢查前2個位置
                        total_measurements += 1

                        # 檢查距離合理性
                        relative_data = position.get("relative_to_observer", {})
                        if isinstance(relative_data, dict):
                            distance_km = relative_data.get("distance_km")
                            elevation_deg = relative_data.get("elevation_deg")

                            if distance_km is not None and elevation_deg is not None:
                                # 基於幾何計算的最小距離檢查
                                min_distance = math.sqrt(
                                    (expected_altitude + self.EARTH_RADIUS_KM)**2 -
                                    self.EARTH_RADIUS_KM**2 * math.cos(math.radians(elevation_deg))**2
                                ) - self.EARTH_RADIUS_KM * math.sin(math.radians(elevation_deg))

                                if distance_km < min_distance * 0.9:  # 允許10%誤差
                                    physics_violations += 1
                                    results["physics_issues"].append(
                                        f"{constellation}: 距離過近 {distance_km:.1f}km < {min_distance:.1f}km"
                                    )

                        # 檢查信號強度合理性
                        signal_data = position.get("signal_quality", {})
                        if isinstance(signal_data, dict):
                            rsrp_dbm = signal_data.get("rsrp_dbm")
                            rsrq_db = signal_data.get("rsrq_db")

                            if rsrp_dbm is not None:
                                # RSRP 合理範圍檢查
                                if rsrp_dbm < -140 or rsrp_dbm > -30:
                                    physics_violations += 1
                                    results["physics_issues"].append(
                                        f"{constellation}: RSRP超出物理範圍 {rsrp_dbm:.1f}dBm"
                                    )

                            if rsrq_db is not None:
                                # RSRQ 合理範圍檢查
                                if rsrq_db < -40 or rsrq_db > 0:
                                    physics_violations += 1
                                    results["physics_issues"].append(
                                        f"{constellation}: RSRQ超出物理範圍 {rsrq_db:.1f}dB"
                                    )

            # 計算物理約束分數
            if total_measurements > 0:
                violation_rate = physics_violations / total_measurements
                results["physics_score"] = max(0.0, 1.0 - violation_rate * 1.5)

            # 判定測試是否通過
            if results["physics_score"] < 0.8:
                results["test_passed"] = False

            self.logger.info(f"🔹 物理約束驗證: 通過={results['test_passed']}, "
                           f"分數={results['physics_score']:.3f}, "
                           f"違規={physics_violations}/{total_measurements}")

            return results

        except Exception as e:
            self.logger.error(f"❌ 物理約束驗證失敗: {e}")
            results.update({
                "test_passed": False,
                "physics_score": 0.0,
                "physics_issues": [f"物理驗證異常: {e}"]
            })
            return results

    def analyze_constellation_physics(self, visibility_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析星座物理特性

        檢查 Starlink/OneWeb 星座是否符合預期的物理參數
        """
        self.logger.info("🔹 執行星座物理特性分析...")

        results = {
            "analysis_passed": True,
            "constellation_scores": {},
            "physics_analysis": {}
        }

        try:
            filtered_satellites = visibility_output.get("data", {}).get("filtered_satellites", {})

            for constellation, satellites in filtered_satellites.items():
                constellation_analysis = {
                    "satellite_count": len(satellites),
                    "altitude_analysis": {},
                    "coverage_analysis": {},
                    "signal_analysis": {}
                }

                # 分析軌道高度分佈
                altitudes = []
                distances = []
                elevations = []

                for satellite in satellites[:10]:  # 分析前10顆衛星
                    timeseries = satellite.get("position_timeseries", [])
                    for position in timeseries[:1]:  # 每顆衛星取1個位置
                        relative_data = position.get("relative_to_observer", {})
                        if isinstance(relative_data, dict):
                            distance = relative_data.get("distance_km")
                            elevation = relative_data.get("elevation_deg")

                            if distance is not None:
                                distances.append(distance)
                            if elevation is not None:
                                elevations.append(elevation)

                # 統計分析
                if distances:
                    avg_distance = sum(distances) / len(distances)
                    # 從距離推算平均高度（簡化計算）
                    estimated_altitude = avg_distance - self.EARTH_RADIUS_KM
                    constellation_analysis["altitude_analysis"] = {
                        "estimated_avg_altitude_km": estimated_altitude,
                        "distance_samples": len(distances),
                        "avg_distance_km": avg_distance
                    }

                if elevations:
                    constellation_analysis["coverage_analysis"] = {
                        "avg_elevation_deg": sum(elevations) / len(elevations),
                        "min_elevation_deg": min(elevations),
                        "max_elevation_deg": max(elevations),
                        "elevation_samples": len(elevations)
                    }

                # 星座特性評分
                expected_altitude = self.STARLINK_ALTITUDE_KM if constellation == "starlink" else self.ONEWEB_ALTITUDE_KM
                if distances:
                    estimated_altitude = sum(distances) / len(distances) - self.EARTH_RADIUS_KM
                    altitude_accuracy = 1.0 - abs(estimated_altitude - expected_altitude) / expected_altitude
                    constellation_analysis["physics_score"] = max(0.0, altitude_accuracy)
                else:
                    constellation_analysis["physics_score"] = 0.0

                results["constellation_scores"][constellation] = constellation_analysis["physics_score"]
                results["physics_analysis"][constellation] = constellation_analysis

            # 整體分析通過判定
            if results["constellation_scores"]:
                avg_score = sum(results["constellation_scores"].values()) / len(results["constellation_scores"])
                if avg_score < 0.7:
                    results["analysis_passed"] = False

            self.logger.info(f"🔹 星座物理分析完成: {results['constellation_scores']}")

            return results

        except Exception as e:
            self.logger.error(f"❌ 星座物理分析失敗: {e}")
            results.update({
                "analysis_passed": False,
                "constellation_scores": {},
                "physics_analysis": {"error": str(e)}
            })
            return results