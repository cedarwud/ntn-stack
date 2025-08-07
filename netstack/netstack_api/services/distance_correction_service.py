"""
距離修正服務 - 整合理論驗證和自動修正

功能：
1. 實施理論斜距公式驗證
2. 自動檢測和修正距離異常
3. 提供距離精度監控
4. 修復高仰角距離計算偏差問題
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DistanceCorrectionResult:
    """距離修正結果"""
    original_distance_km: float
    corrected_distance_km: float
    theoretical_distance_km: float
    correction_applied: bool
    correction_method: str
    confidence_level: float
    validation_status: str

class DistanceCorrectionService:
    """距離修正服務"""
    
    def __init__(self):
        # 地球物理參數
        self.EARTH_RADIUS_KM = 6371.0
        self.LEO_ALTITUDE_KM = 550.0
        
        # 修正閾值
        self.MAX_RELATIVE_ERROR_PERCENT = 50.0    # 50%以上誤差需要修正
        self.HIGH_CONFIDENCE_THRESHOLD = 0.8     # 高信心修正閾值
        self.ELEVATION_HIGH_THRESHOLD = 60.0     # 高仰角閾值
        
        logger.info("距離修正服務初始化完成")
    
    def calculate_theoretical_slant_range(
        self, 
        elevation_deg: float, 
        orbit_altitude_km: float = None
    ) -> float:
        """
        計算理論斜距 (用戶提供的正確公式)
        
        公式: d = √[R_e² + (R_e + h)² - 2·R_e·(R_e + h)·sin(ε)]
        """
        if orbit_altitude_km is None:
            orbit_altitude_km = self.LEO_ALTITUDE_KM
            
        R_e = self.EARTH_RADIUS_KM
        h = orbit_altitude_km
        epsilon = math.radians(elevation_deg)
        
        distance_squared = (
            R_e**2 + 
            (R_e + h)**2 - 
            2 * R_e * (R_e + h) * math.sin(epsilon)
        )
        
        if distance_squared < 0:
            logger.warning(f"理論斜距計算得到負值: elevation={elevation_deg}°")
            return orbit_altitude_km  # 回退到軌道高度
            
        return math.sqrt(distance_squared)
    
    def validate_and_correct_distance(
        self,
        satellite_data: Dict[str, Any],
        observer_lat: float = 24.9441667,
        observer_lon: float = 121.3713889
    ) -> DistanceCorrectionResult:
        """
        驗證並修正衛星距離
        
        Args:
            satellite_data: 衛星數據字典
            observer_lat: 觀測者緯度
            observer_lon: 觀測者經度
            
        Returns:
            距離修正結果
        """
        try:
            # 提取基本數據
            satellite_name = satellite_data.get("name", "UNKNOWN")
            original_distance = satellite_data.get("distance_km", 0.0)
            elevation_deg = satellite_data.get("elevation_deg", 0.0)
            orbit_altitude = satellite_data.get("orbit_altitude_km", satellite_data.get("altitude", self.LEO_ALTITUDE_KM))
            
            # 計算理論斜距
            theoretical_distance = self.calculate_theoretical_slant_range(
                elevation_deg, orbit_altitude
            )
            
            # 計算誤差
            if theoretical_distance > 0:
                relative_error_percent = abs(original_distance - theoretical_distance) / theoretical_distance * 100
            else:
                relative_error_percent = 100.0
            
            # 判斷是否需要修正
            needs_correction = relative_error_percent > self.MAX_RELATIVE_ERROR_PERCENT
            
            if needs_correction:
                # 應用修正
                corrected_distance, correction_method, confidence = self._apply_distance_correction(
                    original_distance, theoretical_distance, elevation_deg, satellite_data
                )
                
                validation_status = "CORRECTED"
                logger.info(
                    f"距離修正應用: {satellite_name} | "
                    f"原始={original_distance:.1f}km → 修正={corrected_distance:.1f}km | "
                    f"理論={theoretical_distance:.1f}km | 誤差={relative_error_percent:.1f}% | "
                    f"方法={correction_method}"
                )
            else:
                # 不需要修正
                corrected_distance = original_distance
                correction_method = "NO_CORRECTION"
                confidence = 1.0
                validation_status = "VALIDATED"
                
                logger.debug(
                    f"距離驗證通過: {satellite_name} | "
                    f"距離={original_distance:.1f}km | 理論={theoretical_distance:.1f}km | "
                    f"誤差={relative_error_percent:.1f}%"
                )
            
            return DistanceCorrectionResult(
                original_distance_km=original_distance,
                corrected_distance_km=corrected_distance,
                theoretical_distance_km=theoretical_distance,
                correction_applied=needs_correction,
                correction_method=correction_method,
                confidence_level=confidence,
                validation_status=validation_status
            )
            
        except Exception as e:
            logger.error(f"距離修正失敗 {satellite_data.get('name', 'UNKNOWN')}: {e}")
            
            # 返回錯誤結果
            original_distance = satellite_data.get("distance_km", self.LEO_ALTITUDE_KM)
            return DistanceCorrectionResult(
                original_distance_km=original_distance,
                corrected_distance_km=original_distance,
                theoretical_distance_km=0.0,
                correction_applied=False,
                correction_method="ERROR",
                confidence_level=0.0,
                validation_status="ERROR"
            )
    
    def _apply_distance_correction(
        self,
        original_distance: float,
        theoretical_distance: float,
        elevation_deg: float,
        satellite_data: Dict[str, Any]
    ) -> Tuple[float, str, float]:
        """
        應用距離修正算法
        
        Returns:
            (修正距離, 修正方法, 信心等級)
        """
        
        # 方法1: 高仰角情況 - 優先使用理論公式
        if elevation_deg > self.ELEVATION_HIGH_THRESHOLD:
            # 高仰角時，理論公式更準確
            weight_theoretical = 0.8
            weight_original = 0.2
            corrected_distance = (
                theoretical_distance * weight_theoretical + 
                original_distance * weight_original
            )
            return corrected_distance, "THEORETICAL_WEIGHTED", 0.9
        
        # 方法2: 中仰角情況 - 加權平均
        elif 20 <= elevation_deg <= self.ELEVATION_HIGH_THRESHOLD:
            # 中仰角時，兩者權重相等
            weight_theoretical = 0.6
            weight_original = 0.4
            corrected_distance = (
                theoretical_distance * weight_theoretical + 
                original_distance * weight_original
            )
            return corrected_distance, "BALANCED_WEIGHTED", 0.7
        
        # 方法3: 低仰角情況 - 偏向原始SGP4計算
        else:
            # 低仰角時，SGP4的3D計算可能更準確
            weight_theoretical = 0.3
            weight_original = 0.7
            corrected_distance = (
                theoretical_distance * weight_theoretical + 
                original_distance * weight_original
            )
            return corrected_distance, "SGP4_WEIGHTED", 0.6
    
    def process_satellite_constellation(
        self,
        satellites_data: List[Dict[str, Any]],
        observer_lat: float = 24.9441667,
        observer_lon: float = 121.3713889
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        處理整個衛星星座的距離修正
        
        Returns:
            (修正後的衛星數據, 統計信息)
        """
        corrected_satellites = []
        correction_stats = {
            "total_satellites": len(satellites_data),
            "corrections_applied": 0,
            "high_confidence_corrections": 0,
            "validation_passed": 0,
            "average_original_error": 0.0,
            "average_corrected_error": 0.0,
            "correction_methods": {}
        }
        
        original_errors = []
        corrected_errors = []
        
        for sat_data in satellites_data:
            # 執行距離修正
            correction_result = self.validate_and_correct_distance(
                sat_data, observer_lat, observer_lon
            )
            
            # 更新衛星數據
            corrected_sat_data = sat_data.copy()
            corrected_sat_data["distance_km"] = correction_result.corrected_distance_km
            corrected_sat_data["original_distance_km"] = correction_result.original_distance_km
            corrected_sat_data["theoretical_distance_km"] = correction_result.theoretical_distance_km
            corrected_sat_data["distance_validation_status"] = correction_result.validation_status
            corrected_sat_data["correction_confidence"] = correction_result.confidence_level
            
            corrected_satellites.append(corrected_sat_data)
            
            # 更新統計信息
            if correction_result.correction_applied:
                correction_stats["corrections_applied"] += 1
                
                if correction_result.confidence_level >= self.HIGH_CONFIDENCE_THRESHOLD:
                    correction_stats["high_confidence_corrections"] += 1
                
                # 統計修正方法
                method = correction_result.correction_method
                if method in correction_stats["correction_methods"]:
                    correction_stats["correction_methods"][method] += 1
                else:
                    correction_stats["correction_methods"][method] = 1
            
            if correction_result.validation_status in ["VALIDATED", "CORRECTED"]:
                correction_stats["validation_passed"] += 1
            
            # 計算誤差統計
            if correction_result.theoretical_distance_km > 0:
                original_error = abs(correction_result.original_distance_km - correction_result.theoretical_distance_km)
                corrected_error = abs(correction_result.corrected_distance_km - correction_result.theoretical_distance_km)
                original_errors.append(original_error)
                corrected_errors.append(corrected_error)
        
        # 計算平均誤差
        if original_errors:
            correction_stats["average_original_error"] = sum(original_errors) / len(original_errors)
            correction_stats["average_corrected_error"] = sum(corrected_errors) / len(corrected_errors)
        
        logger.info(
            f"星座距離修正完成: {correction_stats['total_satellites']}顆衛星, "
            f"{correction_stats['corrections_applied']}個修正, "
            f"平均誤差改善: {correction_stats['average_original_error']:.1f}km → "
            f"{correction_stats['average_corrected_error']:.1f}km"
        )
        
        return corrected_satellites, correction_stats
    
    def generate_correction_report(
        self, 
        correction_stats: Dict[str, Any]
    ) -> str:
        """生成距離修正報告"""
        
        report = []
        report.append("# 🔧 距離修正服務報告")
        report.append("")
        
        total = correction_stats["total_satellites"]
        corrected = correction_stats["corrections_applied"]
        validated = correction_stats["validation_passed"]
        
        report.append("## 📊 修正統計")
        report.append(f"- **總衛星數**: {total}顆")
        report.append(f"- **應用修正**: {corrected}顆 ({corrected/total*100:.1f}%)")
        report.append(f"- **高信心修正**: {correction_stats['high_confidence_corrections']}顆")
        report.append(f"- **驗證通過**: {validated}顆 ({validated/total*100:.1f}%)")
        report.append("")
        
        report.append("## 📈 精度改善")
        report.append(f"- **修正前平均誤差**: {correction_stats['average_original_error']:.2f} km")
        report.append(f"- **修正後平均誤差**: {correction_stats['average_corrected_error']:.2f} km")
        
        if correction_stats['average_original_error'] > 0:
            improvement = (1 - correction_stats['average_corrected_error']/correction_stats['average_original_error']) * 100
            report.append(f"- **精度改善**: {improvement:.1f}%")
        
        report.append("")
        
        # 修正方法統計
        if correction_stats['correction_methods']:
            report.append("## 🛠️ 修正方法分佈")
            for method, count in correction_stats['correction_methods'].items():
                report.append(f"- **{method}**: {count}次 ({count/corrected*100:.1f}%)")
            report.append("")
        
        report.append("## 💡 修正策略")
        report.append("- **高仰角(>60°)**: 理論公式加權80%，SGP4加權20%")
        report.append("- **中仰角(20-60°)**: 理論公式加權60%，SGP4加權40%")
        report.append("- **低仰角(<20°)**: 理論公式加權30%，SGP4加權70%")
        report.append("")
        
        report.append("---")
        report.append(f"**報告生成時間**: {datetime.utcnow().isoformat()}")
        
        return "\n".join(report)


def create_distance_correction_service() -> DistanceCorrectionService:
    """創建距離修正服務實例"""
    return DistanceCorrectionService()