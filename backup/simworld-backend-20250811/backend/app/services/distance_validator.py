"""
距離計算驗證器 - 理論vs實際對比分析

功能：
1. 實施理論斜距公式作為驗證基準
2. 分析SGP4系統與理論公式的偏差
3. 提供距離計算精度監控
4. 識別系統性偏差問題

修復用戶提出的高仰角距離計算偏差問題
"""

import math
import logging
from typing import Tuple, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from .distance_calculator import DistanceCalculator, Position, DistanceResult
from .sgp4_calculator import OrbitPosition

logger = logging.getLogger(__name__)

@dataclass
class DistanceValidationResult:
    """距離驗證結果"""
    satellite_name: str
    norad_id: str
    
    # 位置信息
    elevation_deg: float
    azimuth_deg: float
    
    # 距離對比
    sgp4_distance_km: float              # SGP4系統計算距離
    theoretical_distance_km: float       # 理論斜距公式距離
    distance_difference_km: float        # 絕對差異
    relative_error_percent: float        # 相對誤差百分比
    
    # 分析結果
    validation_status: str               # PASS/WARNING/FAIL
    error_analysis: str                  # 誤差分析說明
    
    # 原始數據
    timestamp: datetime
    observer_location: Position

@dataclass 
class ValidationSummary:
    """驗證摘要統計"""
    total_satellites: int
    validation_passed: int
    validation_warnings: int
    validation_failed: int
    
    mean_error_km: float
    max_error_km: float
    min_error_km: float
    std_error_km: float
    
    high_elevation_accuracy: float       # 高仰角(>60°)精度
    medium_elevation_accuracy: float     # 中仰角(30-60°)精度  
    low_elevation_accuracy: float        # 低仰角(<30°)精度

class DistanceValidator:
    """距離計算驗證器"""
    
    def __init__(self):
        # 地球物理參數 (與用戶提供的公式一致)
        self.EARTH_RADIUS_KM = 6371.0        # km (標準值)
        self.LEO_ALTITUDE_KM = 550.0         # km (Starlink軌道高度)
        
        # 驗證閾值
        self.ACCURACY_THRESHOLD_PERCENT = 15.0   # 15%誤差閾值
        self.WARNING_THRESHOLD_PERCENT = 10.0    # 10%警告閾值
        
        # 創建距離計算器實例
        self.distance_calculator = DistanceCalculator()
        
        logger.info("距離驗證器初始化完成")
        
    def calculate_theoretical_slant_range(
        self, 
        elevation_deg: float, 
        orbit_altitude_km: float = None
    ) -> float:
        """
        計算理論斜距 (用戶提供的正確公式)
        
        公式: d = √[R_e² + (R_e + h)² - 2·R_e·(R_e + h)·sin(ε)]
        
        Args:
            elevation_deg: 衛星仰角 (度)
            orbit_altitude_km: 軌道高度 (km)，默認使用LEO高度
            
        Returns:
            理論斜距 (km)
        """
        if orbit_altitude_km is None:
            orbit_altitude_km = self.LEO_ALTITUDE_KM
            
        R_e = self.EARTH_RADIUS_KM
        h = orbit_altitude_km
        epsilon = math.radians(elevation_deg)
        
        # 用戶的正確公式
        distance_squared = (
            R_e**2 + 
            (R_e + h)**2 - 
            2 * R_e * (R_e + h) * math.sin(epsilon)
        )
        
        if distance_squared < 0:
            logger.warning(f"理論斜距計算得到負值: elevation={elevation_deg}°")
            return 0.0
            
        theoretical_distance = math.sqrt(distance_squared)
        
        logger.debug(
            f"理論斜距計算: ε={elevation_deg:.2f}°, "
            f"R_e={R_e}km, h={h}km → d={theoretical_distance:.2f}km"
        )
        
        return theoretical_distance
    
    def validate_satellite_distance(
        self,
        satellite_name: str,
        norad_id: str,
        ue_position: Position,
        satellite_position: OrbitPosition,
        sgp4_distance_km: float
    ) -> DistanceValidationResult:
        """
        驗證單顆衛星的距離計算
        
        Args:
            satellite_name: 衛星名稱
            norad_id: NORAD ID
            ue_position: UE觀測者位置
            satellite_position: 衛星位置
            sgp4_distance_km: SGP4系統計算的距離
            
        Returns:
            驗證結果
        """
        try:
            # 計算仰角和方位角
            elevation_deg = self.distance_calculator.calculate_elevation_angle(
                ue_position, satellite_position
            )
            azimuth_deg = self.distance_calculator.calculate_azimuth_angle(
                ue_position, satellite_position  
            )
            
            # 計算理論斜距
            theoretical_distance_km = self.calculate_theoretical_slant_range(
                elevation_deg, satellite_position.altitude
            )
            
            # 計算誤差
            distance_difference_km = abs(sgp4_distance_km - theoretical_distance_km)
            
            if theoretical_distance_km > 0:
                relative_error_percent = (distance_difference_km / theoretical_distance_km) * 100
            else:
                relative_error_percent = 100.0
            
            # 判定驗證狀態
            if relative_error_percent <= self.WARNING_THRESHOLD_PERCENT:
                validation_status = "PASS"
                error_analysis = f"精度良好，誤差{relative_error_percent:.1f}%"
            elif relative_error_percent <= self.ACCURACY_THRESHOLD_PERCENT:
                validation_status = "WARNING"
                error_analysis = f"精度可接受，誤差{relative_error_percent:.1f}%，建議檢查"
            else:
                validation_status = "FAIL"
                error_analysis = f"精度不佳，誤差{relative_error_percent:.1f}%，需要修正"
            
            # 特殊情況分析
            if elevation_deg > 80 and relative_error_percent > 20:
                error_analysis += " (高仰角異常)"
            elif elevation_deg < 20 and relative_error_percent > 30:
                error_analysis += " (低仰角幾何影響)"
            
            logger.info(
                f"距離驗證: {satellite_name} | "
                f"ε={elevation_deg:.1f}° | SGP4={sgp4_distance_km:.1f}km | "
                f"理論={theoretical_distance_km:.1f}km | 誤差={relative_error_percent:.1f}% | "
                f"狀態={validation_status}"
            )
            
            return DistanceValidationResult(
                satellite_name=satellite_name,
                norad_id=norad_id,
                elevation_deg=elevation_deg,
                azimuth_deg=azimuth_deg,
                sgp4_distance_km=sgp4_distance_km,
                theoretical_distance_km=theoretical_distance_km,
                distance_difference_km=distance_difference_km,
                relative_error_percent=relative_error_percent,
                validation_status=validation_status,
                error_analysis=error_analysis,
                timestamp=satellite_position.timestamp,
                observer_location=ue_position
            )
            
        except Exception as e:
            logger.error(f"距離驗證失敗 {satellite_name}: {e}")
            
            return DistanceValidationResult(
                satellite_name=satellite_name,
                norad_id=norad_id,
                elevation_deg=0.0,
                azimuth_deg=0.0,
                sgp4_distance_km=sgp4_distance_km,
                theoretical_distance_km=0.0,
                distance_difference_km=0.0,
                relative_error_percent=100.0,
                validation_status="ERROR",
                error_analysis=f"計算異常: {str(e)}",
                timestamp=datetime.utcnow(),
                observer_location=ue_position
            )
    
    def validate_satellite_constellation(
        self, 
        satellites_data: List[Dict[str, Any]],
        ue_position: Position
    ) -> Tuple[List[DistanceValidationResult], ValidationSummary]:
        """
        驗證整個衛星星座的距離計算
        
        Args:
            satellites_data: 衛星數據列表
            ue_position: UE觀測者位置
            
        Returns:
            (驗證結果列表, 驗證摘要)
        """
        validation_results = []
        
        for sat_data in satellites_data:
            # 構建衛星位置對象
            satellite_position = OrbitPosition(
                latitude=sat_data.get('latitude', 0.0),
                longitude=sat_data.get('longitude', 0.0), 
                altitude=sat_data.get('altitude', self.LEO_ALTITUDE_KM),
                velocity=(0.0, 0.0, 0.0),  # 速度不影響距離計算
                timestamp=datetime.utcnow(),
                satellite_id=str(sat_data.get('norad_id', 'unknown'))
            )
            
            # 驗證距離
            result = self.validate_satellite_distance(
                satellite_name=sat_data.get('name', 'UNKNOWN'),
                norad_id=str(sat_data.get('norad_id', 'unknown')),
                ue_position=ue_position,
                satellite_position=satellite_position,
                sgp4_distance_km=sat_data.get('distance_km', 0.0)
            )
            
            validation_results.append(result)
        
        # 生成驗證摘要
        summary = self._generate_validation_summary(validation_results)
        
        return validation_results, summary
    
    def _generate_validation_summary(
        self, 
        results: List[DistanceValidationResult]
    ) -> ValidationSummary:
        """生成驗證摘要統計"""
        if not results:
            return ValidationSummary(
                total_satellites=0, validation_passed=0, validation_warnings=0,
                validation_failed=0, mean_error_km=0.0, max_error_km=0.0,
                min_error_km=0.0, std_error_km=0.0, high_elevation_accuracy=0.0,
                medium_elevation_accuracy=0.0, low_elevation_accuracy=0.0
            )
        
        total_satellites = len(results)
        passed = sum(1 for r in results if r.validation_status == "PASS")
        warnings = sum(1 for r in results if r.validation_status == "WARNING") 
        failed = sum(1 for r in results if r.validation_status in ["FAIL", "ERROR"])
        
        errors = [r.distance_difference_km for r in results]
        mean_error = sum(errors) / len(errors)
        max_error = max(errors)
        min_error = min(errors)
        
        # 標準差
        variance = sum((e - mean_error) ** 2 for e in errors) / len(errors)
        std_error = math.sqrt(variance)
        
        # 分仰角分析精度
        high_elev = [r for r in results if r.elevation_deg > 60]
        medium_elev = [r for r in results if 30 <= r.elevation_deg <= 60]
        low_elev = [r for r in results if r.elevation_deg < 30]
        
        def calc_accuracy(group):
            if not group:
                return 0.0
            good = sum(1 for r in group if r.validation_status in ["PASS", "WARNING"])
            return (good / len(group)) * 100
        
        high_accuracy = calc_accuracy(high_elev)
        medium_accuracy = calc_accuracy(medium_elev)
        low_accuracy = calc_accuracy(low_elev)
        
        return ValidationSummary(
            total_satellites=total_satellites,
            validation_passed=passed,
            validation_warnings=warnings, 
            validation_failed=failed,
            mean_error_km=mean_error,
            max_error_km=max_error,
            min_error_km=min_error,
            std_error_km=std_error,
            high_elevation_accuracy=high_accuracy,
            medium_elevation_accuracy=medium_accuracy,
            low_elevation_accuracy=low_accuracy
        )
    
    def generate_validation_report(
        self,
        results: List[DistanceValidationResult],
        summary: ValidationSummary
    ) -> str:
        """生成詳細的驗證報告"""
        
        report = []
        report.append("# 🔧 距離計算驗證報告")
        report.append("")
        report.append("## 📊 驗證摘要")
        report.append(f"- **總衛星數**: {summary.total_satellites}顆")
        report.append(f"- **驗證通過**: {summary.validation_passed}顆 ({summary.validation_passed/summary.total_satellites*100:.1f}%)")
        report.append(f"- **精度警告**: {summary.validation_warnings}顆 ({summary.validation_warnings/summary.total_satellites*100:.1f}%)")
        report.append(f"- **精度失敗**: {summary.validation_failed}顆 ({summary.validation_failed/summary.total_satellites*100:.1f}%)")
        report.append("")
        
        report.append("## 📈 誤差統計")
        report.append(f"- **平均誤差**: {summary.mean_error_km:.2f} km")
        report.append(f"- **最大誤差**: {summary.max_error_km:.2f} km")
        report.append(f"- **最小誤差**: {summary.min_error_km:.2f} km")
        report.append(f"- **標準差**: {summary.std_error_km:.2f} km")
        report.append("")
        
        report.append("## 🎯 仰角精度分析")
        report.append(f"- **高仰角(>60°)精度**: {summary.high_elevation_accuracy:.1f}%")
        report.append(f"- **中仰角(30-60°)精度**: {summary.medium_elevation_accuracy:.1f}%")
        report.append(f"- **低仰角(<30°)精度**: {summary.low_elevation_accuracy:.1f}%")
        report.append("")
        
        report.append("## 📋 詳細驗證結果")
        report.append("")
        report.append("| 衛星名稱 | 仰角(°) | SGP4距離(km) | 理論距離(km) | 誤差(km) | 相對誤差(%) | 狀態 |")
        report.append("|---------|---------|-------------|-------------|----------|-------------|------|")
        
        for result in results:
            status_icon = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌", "ERROR": "🚨"}.get(result.validation_status, "❓")
            report.append(
                f"| {result.satellite_name} | "
                f"{result.elevation_deg:.1f} | "
                f"{result.sgp4_distance_km:.1f} | "
                f"{result.theoretical_distance_km:.1f} | "
                f"{result.distance_difference_km:.1f} | "
                f"{result.relative_error_percent:.1f} | "
                f"{status_icon} {result.validation_status} |"
            )
        
        report.append("")
        report.append("## 💡 修復建議")
        
        if summary.validation_failed > 0:
            report.append("### 🚨 嚴重誤差衛星需要修正")
            failed_sats = [r for r in results if r.validation_status == "FAIL"]
            for sat in failed_sats[:3]:  # 顯示前3個
                report.append(f"- **{sat.satellite_name}**: {sat.error_analysis}")
        
        if summary.high_elevation_accuracy < 80:
            report.append("### ⚠️ 高仰角精度問題")
            report.append("- 建議檢查SGP4計算中的座標轉換精度")
            report.append("- 驗證ECEF座標系統的實施")
        
        if summary.low_elevation_accuracy < 60:
            report.append("### 📐 低仰角幾何效應")  
            report.append("- 低仰角誤差較大屬於正常現象")
            report.append("- 考慮增加大氣折射修正")
        
        report.append("")
        report.append("---")
        report.append(f"**報告生成時間**: {datetime.utcnow().isoformat()}")
        
        return "\n".join(report)


def create_distance_validator() -> DistanceValidator:
    """創建距離驗證器實例"""
    return DistanceValidator()
