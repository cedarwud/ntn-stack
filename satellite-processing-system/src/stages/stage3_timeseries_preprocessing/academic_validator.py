"""
學術標準驗證器 - Stage 3模組化組件

職責：
1. 確保時間序列數據符合學術標準
2. 驗證動畫數據的精度和完整性
3. 檢查Grade A合規性
4. 防止數據簡化和精度損失
"""

import logging
import math
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class AcademicValidator:
    """學術標準驗證器 - 確保數據符合研究級精度要求"""
    
    def __init__(self, validation_level: str = "COMPREHENSIVE"):
        """
        初始化學術驗證器
        
        Args:
            validation_level: 驗證級別 (FAST/STANDARD/COMPREHENSIVE)
        """
        self.logger = logging.getLogger(f"{__name__}.AcademicValidator")
        
        self.validation_level = validation_level
        
        # 學術標準定義
        self.academic_standards = {
            "grade_a_requirements": {
                "minimum_data_points": 96,  # 軌道週期完整性
                "precision_digits": 6,      # 座標精度
                "time_resolution_max": 30,  # 最大時間間隔（秒）
                "elevation_precision": 0.1, # 仰角精度（度）
                "signal_unit": "dBm",       # 信號單位標準
                "coordinate_system": "WGS84" # 座標系統
            },
            "forbidden_operations": [
                "arbitrary_downsampling",
                "fixed_compression_ratio", 
                "uniform_quantization",
                "simplified_coordinates",
                "mock_timeseries",
                "estimated_positions",
                "rsrp_normalized"
            ]
        }
        
        # 驗證統計
        self.validation_statistics = {
            "total_satellites_validated": 0,
            "grade_a_compliant": 0,
            "grade_b_compliant": 0,
            "non_compliant": 0,
            "critical_violations": 0,
            "validation_errors": 0
        }
        
        self.logger.info("✅ 學術標準驗證器初始化完成")
        self.logger.info(f"   驗證級別: {validation_level}")
    
    def validate_timeseries_academic_compliance(self, 
                                              timeseries_data: Dict[str, Any],
                                              animation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證時間序列數據的學術合規性
        
        Args:
            timeseries_data: 時間序列轉換結果
            animation_data: 動畫建構結果
            
        Returns:
            學術驗證結果報告
        """
        self.logger.info("📚 開始學術標準合規性驗證...")
        
        validation_report = {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_level": self.validation_level,
            "overall_compliance": "UNKNOWN",
            "grade_distribution": {},
            "compliance_checks": {},
            "critical_violations": [],
            "recommendations": [],
            "academic_certification": {}
        }
        
        satellites = timeseries_data.get("satellites", [])
        self.validation_statistics["total_satellites_validated"] = len(satellites)
        
        # 執行各項學術標準檢查
        try:
            # 檢查1: 數據完整性和精度
            precision_check = self._validate_data_precision(satellites)
            validation_report["compliance_checks"]["data_precision"] = precision_check
            
            # 檢查2: 時間序列完整性
            timeseries_check = self._validate_timeseries_integrity(satellites)
            validation_report["compliance_checks"]["timeseries_integrity"] = timeseries_check
            
            # 檢查3: 座標系統和單位標準
            coordinate_check = self._validate_coordinate_standards(satellites)
            validation_report["compliance_checks"]["coordinate_standards"] = coordinate_check
            
            # 檢查4: 禁用操作檢測
            forbidden_ops_check = self._detect_forbidden_operations(timeseries_data, animation_data)
            validation_report["compliance_checks"]["forbidden_operations"] = forbidden_ops_check
            
            # 檢查5: 動畫數據學術合規性
            animation_check = self._validate_animation_academic_compliance(animation_data)
            validation_report["compliance_checks"]["animation_compliance"] = animation_check
            
            # 檢查6: 信號數據完整性（如果存在）
            signal_check = self._validate_signal_data_integrity(satellites)
            validation_report["compliance_checks"]["signal_integrity"] = signal_check
            
        except Exception as e:
            self.logger.error(f"學術驗證執行失敗: {e}")
            validation_report["validation_error"] = str(e)
            self.validation_statistics["validation_errors"] += 1
        
        # 綜合評估學術等級
        validation_report = self._assess_overall_academic_grade(validation_report)
        
        # 更新統計信息
        self._update_validation_statistics(validation_report)
        
        # 生成建議和認證
        validation_report["recommendations"] = self._generate_academic_recommendations(validation_report)
        validation_report["academic_certification"] = self._generate_academic_certification(validation_report)
        
        self.logger.info(f"✅ 學術驗證完成: {validation_report['overall_compliance']} 等級")
        
        return validation_report
    
    def _validate_data_precision(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證數據精度符合學術標準"""
        
        precision_check = {
            "passed": True,
            "satellites_checked": len(satellites),
            "precision_violations": [],
            "precision_statistics": {}
        }
        
        standards = self.academic_standards["grade_a_requirements"]
        
        coordinates_precision_violations = 0
        elevation_precision_violations = 0
        time_resolution_violations = 0
        
        sample_size = min(10, len(satellites)) if self.validation_level == "FAST" else len(satellites)
        
        for i, satellite in enumerate(satellites[:sample_size]):
            sat_name = satellite.get("name", f"satellite_{i}")
            timeseries = satellite.get("timeseries", [])
            
            if not timeseries:
                continue
            
            # 檢查座標精度
            for j, point in enumerate(timeseries[:5]):  # 檢查前5個點
                lat = point.get("latitude", 0.0)
                lon = point.get("longitude", 0.0)
                
                # 檢查小數位數精度
                lat_precision = len(str(lat).split('.')[-1]) if '.' in str(lat) else 0
                lon_precision = len(str(lon).split('.')[-1]) if '.' in str(lon) else 0
                
                if lat_precision < standards["precision_digits"] or lon_precision < standards["precision_digits"]:
                    coordinates_precision_violations += 1
                    precision_check["precision_violations"].append({
                        "satellite": sat_name,
                        "point": j,
                        "violation_type": "coordinate_precision",
                        "lat_precision": lat_precision,
                        "lon_precision": lon_precision,
                        "required": standards["precision_digits"]
                    })
            
            # 檢查仰角精度
            visible_points = [p for p in timeseries if p.get("is_visible", False)]
            for point in visible_points[:3]:  # 檢查前3個可見點
                elevation = point.get("elevation_deg", 0.0)
                
                # 檢查仰角精度是否滿足0.1度要求
                elevation_str = str(elevation)
                if '.' in elevation_str:
                    decimal_places = len(elevation_str.split('.')[-1])
                    if decimal_places == 0:  # 整數，精度不足
                        elevation_precision_violations += 1
                        precision_check["precision_violations"].append({
                            "satellite": sat_name,
                            "violation_type": "elevation_precision",
                            "elevation": elevation,
                            "required_precision": standards["elevation_precision"]
                        })
        
        # 檢查時間解析度
        if satellites:
            sample_satellite = satellites[0]
            timeseries = sample_satellite.get("timeseries", [])
            if len(timeseries) >= 2:
                time_diff = timeseries[1].get("time_offset_seconds", 30) - timeseries[0].get("time_offset_seconds", 0)
                if time_diff > standards["time_resolution_max"]:
                    time_resolution_violations += 1
                    precision_check["precision_violations"].append({
                        "violation_type": "time_resolution",
                        "actual_resolution": time_diff,
                        "required_max": standards["time_resolution_max"]
                    })
        
        precision_check["precision_statistics"] = {
            "coordinate_precision_violations": coordinates_precision_violations,
            "elevation_precision_violations": elevation_precision_violations,
            "time_resolution_violations": time_resolution_violations
        }
        
        # 判斷是否通過
        total_violations = coordinates_precision_violations + elevation_precision_violations + time_resolution_violations
        precision_check["passed"] = total_violations == 0
        
        if not precision_check["passed"]:
            self.validation_statistics["critical_violations"] += total_violations
        
        return precision_check
    
    def _validate_timeseries_integrity(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證時間序列完整性"""
        
        integrity_check = {
            "passed": True,
            "satellites_checked": len(satellites),
            "integrity_violations": [],
            "integrity_statistics": {}
        }
        
        standards = self.academic_standards["grade_a_requirements"]
        min_data_points = standards["minimum_data_points"]
        
        insufficient_data_satellites = 0
        discontinuous_satellites = 0
        missing_visibility_data = 0
        
        for satellite in satellites:
            sat_name = satellite.get("name", "unknown")
            timeseries = satellite.get("timeseries", [])
            
            # 檢查數據點數量
            if len(timeseries) < min_data_points:
                insufficient_data_satellites += 1
                integrity_check["integrity_violations"].append({
                    "satellite": sat_name,
                    "violation_type": "insufficient_data_points",
                    "actual_points": len(timeseries),
                    "required_minimum": min_data_points
                })
            
            # 檢查時間序列連續性
            if len(timeseries) >= 2:
                for i in range(1, len(timeseries)):
                    prev_time = timeseries[i-1].get("time_offset_seconds", 0)
                    curr_time = timeseries[i].get("time_offset_seconds", 0)
                    
                    if curr_time <= prev_time:
                        discontinuous_satellites += 1
                        integrity_check["integrity_violations"].append({
                            "satellite": sat_name,
                            "violation_type": "time_discontinuity",
                            "point_index": i,
                            "prev_time": prev_time,
                            "curr_time": curr_time
                        })
                        break
            
            # 檢查可見性數據完整性
            visible_points = [p for p in timeseries if p.get("is_visible", False)]
            if visible_points:
                for point in visible_points[:3]:  # 檢查前3個可見點
                    required_fields = ["elevation_deg", "azimuth_deg", "range_km"]
                    missing_fields = [f for f in required_fields if f not in point or point[f] is None]
                    
                    if missing_fields:
                        missing_visibility_data += 1
                        integrity_check["integrity_violations"].append({
                            "satellite": sat_name,
                            "violation_type": "missing_visibility_fields",
                            "missing_fields": missing_fields
                        })
                        break
        
        integrity_check["integrity_statistics"] = {
            "insufficient_data_satellites": insufficient_data_satellites,
            "discontinuous_satellites": discontinuous_satellites,
            "missing_visibility_data": missing_visibility_data
        }
        
        # 判斷是否通過
        total_violations = insufficient_data_satellites + discontinuous_satellites + missing_visibility_data
        integrity_check["passed"] = total_violations == 0
        
        return integrity_check
    
    def _validate_coordinate_standards(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證座標系統和單位標準"""
        
        coordinate_check = {
            "passed": True,
            "satellites_checked": len(satellites),
            "coordinate_violations": [],
            "standards_compliance": {}
        }
        
        coordinate_violations = 0
        
        for satellite in satellites:
            sat_name = satellite.get("name", "unknown")
            timeseries = satellite.get("timeseries", [])
            
            # 檢查座標範圍合理性
            for point in timeseries[:5]:  # 檢查前5個點
                lat = point.get("latitude", 0.0)
                lon = point.get("longitude", 0.0)
                alt = point.get("altitude_km", 0.0)
                
                # WGS84座標範圍檢查
                if not (-90 <= lat <= 90):
                    coordinate_violations += 1
                    coordinate_check["coordinate_violations"].append({
                        "satellite": sat_name,
                        "violation_type": "invalid_latitude",
                        "latitude": lat,
                        "valid_range": "[-90, 90]"
                    })
                
                if not (-180 <= lon <= 180):
                    coordinate_violations += 1
                    coordinate_check["coordinate_violations"].append({
                        "satellite": sat_name,
                        "violation_type": "invalid_longitude",
                        "longitude": lon,
                        "valid_range": "[-180, 180]"
                    })
                
                # LEO衛星高度範圍檢查
                if not (200 <= alt <= 2000):
                    coordinate_violations += 1
                    coordinate_check["coordinate_violations"].append({
                        "satellite": sat_name,
                        "violation_type": "invalid_altitude",
                        "altitude_km": alt,
                        "valid_range": "[200, 2000] km"
                    })
        
        coordinate_check["standards_compliance"] = {
            "coordinate_system": "WGS84",
            "coordinate_violations": coordinate_violations,
            "altitude_unit": "km",
            "angle_unit": "degrees"
        }
        
        coordinate_check["passed"] = coordinate_violations == 0
        
        return coordinate_check
    
    def _detect_forbidden_operations(self, timeseries_data: Dict[str, Any], 
                                   animation_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢測禁用的數據處理操作"""
        
        forbidden_check = {
            "passed": True,
            "forbidden_operations_detected": [],
            "data_integrity_score": 100.0
        }
        
        forbidden_ops = self.academic_standards["forbidden_operations"]
        
        # 檢查數據結構中是否包含禁用操作的痕跡
        data_str = str(timeseries_data).lower() + str(animation_data).lower()
        
        for forbidden_op in forbidden_ops:
            if forbidden_op.lower() in data_str:
                forbidden_check["forbidden_operations_detected"].append({
                    "operation": forbidden_op,
                    "detection_location": "data_structure_content",
                    "severity": "critical"
                })
                forbidden_check["passed"] = False
                self.validation_statistics["critical_violations"] += 1
        
        # 檢查是否有可疑的數據模式
        satellites = timeseries_data.get("satellites", [])
        
        # 檢測uniform quantization（統一量化）
        if self._detect_uniform_quantization(satellites):
            forbidden_check["forbidden_operations_detected"].append({
                "operation": "uniform_quantization",
                "detection_location": "coordinate_patterns",
                "severity": "critical"
            })
            forbidden_check["passed"] = False
        
        # 檢測arbitrary downsampling（任意下採樣）
        if self._detect_arbitrary_downsampling(satellites):
            forbidden_check["forbidden_operations_detected"].append({
                "operation": "arbitrary_downsampling",
                "detection_location": "temporal_patterns",
                "severity": "critical"
            })
            forbidden_check["passed"] = False
        
        # 計算數據完整性評分
        violation_count = len(forbidden_check["forbidden_operations_detected"])
        forbidden_check["data_integrity_score"] = max(0, 100 - (violation_count * 25))
        
        return forbidden_check
    
    def _detect_uniform_quantization(self, satellites: List[Dict[str, Any]]) -> bool:
        """檢測uniform quantization（座標統一量化）"""
        
        if not satellites:
            return False
        
        # 檢查座標是否有明顯的量化模式
        sample_coordinates = []
        
        for satellite in satellites[:3]:  # 檢查前3顆衛星
            timeseries = satellite.get("timeseries", [])
            for point in timeseries[:10]:  # 每顆衛星檢查前10個點
                lat = point.get("latitude", 0.0)
                lon = point.get("longitude", 0.0)
                sample_coordinates.extend([lat, lon])
        
        if len(sample_coordinates) < 10:
            return False
        
        # 檢查小數部分的模式
        decimal_parts = []
        for coord in sample_coordinates:
            if '.' in str(coord):
                decimal_part = str(coord).split('.')[-1]
                decimal_parts.append(decimal_part)
        
        # 如果超過80%的座標有相同的小數位數模式，可能存在量化
        if decimal_parts:
            from collections import Counter
            decimal_counts = Counter(len(dp) for dp in decimal_parts)
            most_common_length = decimal_counts.most_common(1)[0]
            
            if most_common_length[1] / len(decimal_parts) > 0.8 and most_common_length[0] <= 3:
                return True  # 可能的量化跡象
        
        return False
    
    def _detect_arbitrary_downsampling(self, satellites: List[Dict[str, Any]]) -> bool:
        """檢測arbitrary downsampling（任意下採樣）"""
        
        if not satellites:
            return False
        
        # 檢查時間間隔是否有不規律的大幅跳躍
        for satellite in satellites[:3]:
            timeseries = satellite.get("timeseries", [])
            
            if len(timeseries) < 3:
                continue
            
            time_intervals = []
            for i in range(1, len(timeseries)):
                prev_time = timeseries[i-1].get("time_offset_seconds", 0)
                curr_time = timeseries[i].get("time_offset_seconds", 0)
                interval = curr_time - prev_time
                time_intervals.append(interval)
            
            if time_intervals:
                # 如果時間間隔變化超過3倍，可能存在任意下採樣
                min_interval = min(time_intervals)
                max_interval = max(time_intervals)
                
                if max_interval > min_interval * 3 and min_interval > 0:
                    return True
        
        return False
    
    def _validate_animation_academic_compliance(self, animation_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證動畫數據的學術合規性"""
        
        animation_check = {
            "passed": True,
            "animation_violations": [],
            "compliance_score": 100.0
        }
        
        constellation_animations = animation_data.get("constellation_animations", {})
        
        if not constellation_animations:
            animation_check["passed"] = False
            animation_check["animation_violations"].append({
                "violation_type": "missing_animation_data",
                "severity": "critical"
            })
            return animation_check
        
        # 檢查每個星座的動畫數據完整性
        for const_name, const_anim in constellation_animations.items():
            satellite_tracks = const_anim.get("satellite_tracks", [])
            
            for track in satellite_tracks:
                # 檢查關鍵幀完整性
                position_keyframes = track.get("position_keyframes", [])
                visibility_keyframes = track.get("visibility_keyframes", [])
                
                if not position_keyframes:
                    animation_check["animation_violations"].append({
                        "constellation": const_name,
                        "satellite": track.get("satellite_id", "unknown"),
                        "violation_type": "missing_position_keyframes",
                        "severity": "major"
                    })
                    animation_check["passed"] = False
                
                # 檢查關鍵幀數據精度
                for keyframe in position_keyframes[:3]:  # 檢查前3幀
                    position = keyframe.get("position", {})
                    lat = position.get("lat", 0.0)
                    lon = position.get("lon", 0.0)
                    
                    # 檢查動畫關鍵幀的座標精度
                    if abs(lat) > 90 or abs(lon) > 180:
                        animation_check["animation_violations"].append({
                            "constellation": const_name,
                            "satellite": track.get("satellite_id", "unknown"),
                            "violation_type": "invalid_animation_coordinates",
                            "frame": keyframe.get("frame", 0),
                            "severity": "critical"
                        })
                        animation_check["passed"] = False
        
        # 計算合規分數
        violation_count = len(animation_check["animation_violations"])
        critical_violations = len([v for v in animation_check["animation_violations"] if v.get("severity") == "critical"])
        
        animation_check["compliance_score"] = max(0, 100 - (critical_violations * 30) - (violation_count * 10))
        
        return animation_check
    
    def _validate_signal_data_integrity(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證信號數據完整性"""
        
        signal_check = {
            "passed": True,
            "signal_violations": [],
            "signal_statistics": {}
        }
        
        satellites_with_signals = 0
        signal_unit_violations = 0
        signal_range_violations = 0
        
        for satellite in satellites:
            sat_name = satellite.get("name", "unknown")
            signal_timeline = satellite.get("signal_timeline", {})
            
            if not signal_timeline:
                continue
            
            satellites_with_signals += 1
            signal_points = signal_timeline.get("signal_points", [])
            
            for point in signal_points[:5]:  # 檢查前5個信號點
                signal_strength = point.get("signal_strength", -140)
                
                # 檢查信號強度範圍（dBm）
                if not (-140 <= signal_strength <= -30):
                    signal_range_violations += 1
                    signal_check["signal_violations"].append({
                        "satellite": sat_name,
                        "violation_type": "invalid_signal_range",
                        "signal_strength": signal_strength,
                        "valid_range": "[-140, -30] dBm"
                    })
        
        signal_check["signal_statistics"] = {
            "satellites_with_signals": satellites_with_signals,
            "signal_unit_violations": signal_unit_violations,
            "signal_range_violations": signal_range_violations
        }
        
        signal_check["passed"] = signal_unit_violations == 0 and signal_range_violations == 0
        
        return signal_check
    
    def _assess_overall_academic_grade(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """評估總體學術等級"""
        
        compliance_checks = validation_report.get("compliance_checks", {})
        
        # 計算各項檢查的通過情況
        checks_passed = sum(1 for check in compliance_checks.values() if check.get("passed", False))
        total_checks = len(compliance_checks)
        
        pass_rate = checks_passed / total_checks if total_checks > 0 else 0
        
        # 檢查是否有關鍵違規
        critical_violations = validation_report.get("critical_violations", [])
        has_critical_violations = len(critical_violations) > 0
        
        # 判定學術等級
        if pass_rate >= 0.95 and not has_critical_violations:
            grade = "GRADE_A"
            self.validation_statistics["grade_a_compliant"] += 1
        elif pass_rate >= 0.8 and len(critical_violations) <= 1:
            grade = "GRADE_B"
            self.validation_statistics["grade_b_compliant"] += 1
        else:
            grade = "NON_COMPLIANT"
            self.validation_statistics["non_compliant"] += 1
        
        validation_report["overall_compliance"] = grade
        validation_report["grade_distribution"] = {
            "grade": grade,
            "pass_rate": round(pass_rate * 100, 2),
            "checks_passed": checks_passed,
            "total_checks": total_checks,
            "critical_violations": len(critical_violations)
        }
        
        return validation_report
    
    def _update_validation_statistics(self, validation_report: Dict[str, Any]) -> None:
        """更新驗證統計信息"""
        
        # 統計信息已在評估函數中更新
        pass
    
    def _generate_academic_recommendations(self, validation_report: Dict[str, Any]) -> List[str]:
        """生成學術標準改進建議"""
        
        recommendations = []
        
        compliance_checks = validation_report.get("compliance_checks", {})
        
        # 基於各項檢查結果生成建議
        if not compliance_checks.get("data_precision", {}).get("passed", True):
            recommendations.append("提高座標和仰角數據精度，確保符合Grade A要求")
        
        if not compliance_checks.get("timeseries_integrity", {}).get("passed", True):
            recommendations.append("增加時間序列數據點數量，確保軌道週期完整性")
        
        if not compliance_checks.get("coordinate_standards", {}).get("passed", True):
            recommendations.append("驗證並修正座標系統標準，確保WGS84合規")
        
        if not compliance_checks.get("forbidden_operations", {}).get("passed", True):
            recommendations.append("移除所有禁用的數據處理操作，維持原始數據精度")
        
        if not compliance_checks.get("animation_compliance", {}).get("passed", True):
            recommendations.append("完善動畫數據結構，確保學術級精度要求")
        
        if not recommendations:
            recommendations.append("數據已符合學術標準要求，可用於研究發表")
        
        return recommendations
    
    def _generate_academic_certification(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """生成學術認證信息"""
        
        grade = validation_report.get("overall_compliance", "UNKNOWN")
        
        certification = {
            "certification_level": grade,
            "certification_timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_framework": "modular_pipeline_v2",
            "compliance_summary": {},
            "research_readiness": grade in ["GRADE_A", "GRADE_B"],
            "publication_ready": grade == "GRADE_A"
        }
        
        if grade == "GRADE_A":
            certification["compliance_summary"] = {
                "data_precision": "high",
                "academic_compliance": "full",
                "research_grade": "journal_publication_ready",
                "zero_tolerance_policy": "enforced"
            }
        elif grade == "GRADE_B":
            certification["compliance_summary"] = {
                "data_precision": "acceptable",
                "academic_compliance": "substantial",
                "research_grade": "conference_ready",
                "minor_issues": "present"
            }
        else:
            certification["compliance_summary"] = {
                "data_precision": "insufficient",
                "academic_compliance": "non_compliant",
                "research_grade": "requires_improvement",
                "critical_issues": "present"
            }
        
        return certification
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """獲取驗證統計信息"""
        return self.validation_statistics.copy()