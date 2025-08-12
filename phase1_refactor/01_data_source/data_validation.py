#!/usr/bin/env python3
"""
數據完整性驗證系統
確保 TLE 數據和軌道計算符合 CLAUDE.md 嚴格標準
禁止簡化算法和模擬數據
"""

import logging
import math
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from tle_loader import TLERecord

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """驗證嚴重性等級"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """單項驗證結果"""
    check_name: str
    severity: ValidationSeverity
    passed: bool
    message: str
    details: Optional[Dict] = None


@dataclass
class ValidationReport:
    """完整驗證報告"""
    timestamp: datetime
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[ValidationResult]
    overall_status: str
    recommendations: List[str]
    
    @property
    def success_rate(self) -> float:
        """成功率百分比"""
        if self.total_checks == 0:
            return 0.0
        return (self.passed_checks / self.total_checks) * 100


class TLEValidator:
    """TLE 數據驗證器"""
    
    # TLE 格式規範
    LINE_LENGTH = 69
    LINE1_PATTERN = r'^1 \d{5}[A-Z] \d{8}\.\d{8}  [+-]?\.\d{8} [+-]?\d{5}[+-]\d [+-]?\d{5}[+-]\d \d \d{4}$'
    LINE2_PATTERN = r'^2 \d{5} \d{3}\.\d{4} \d{3}\.\d{4} \d{7} \d{3}\.\d{4} \d{3}\.\d{4} \d{2}\.\d{13}\d$'
    
    def __init__(self):
        self.validation_results: List[ValidationResult] = []
        logger.info("TLE 驗證器初始化完成")
    
    def validate_tle_record(self, tle_record: TLERecord) -> List[ValidationResult]:
        """驗證單個 TLE 記錄"""
        self.validation_results.clear()
        
        # 基本格式驗證
        self._validate_basic_format(tle_record)
        
        # 檢查碼驗證
        self._validate_checksums(tle_record)
        
        # 軌道元素合理性驗證
        self._validate_orbital_elements(tle_record)
        
        # 時間新鮮度驗證
        self._validate_epoch_freshness(tle_record)
        
        # 物理合理性驗證
        self._validate_physical_constraints(tle_record)
        
        return self.validation_results.copy()
    
    def _validate_basic_format(self, tle_record: TLERecord):
        """基本格式驗證"""
        # 檢查行長度
        if len(tle_record.line1) != self.LINE_LENGTH:
            self._add_result("line1_length", ValidationSeverity.ERROR, False,
                           f"第1行長度 {len(tle_record.line1)}，應為 {self.LINE_LENGTH}")
        else:
            self._add_result("line1_length", ValidationSeverity.INFO, True, "第1行長度正確")
        
        if len(tle_record.line2) != self.LINE_LENGTH:
            self._add_result("line2_length", ValidationSeverity.ERROR, False,
                           f"第2行長度 {len(tle_record.line2)}，應為 {self.LINE_LENGTH}")
        else:
            self._add_result("line2_length", ValidationSeverity.INFO, True, "第2行長度正確")
        
        # 檢查行標識
        if not tle_record.line1.startswith('1 '):
            self._add_result("line1_prefix", ValidationSeverity.ERROR, False, "第1行應以 '1 ' 開始")
        else:
            self._add_result("line1_prefix", ValidationSeverity.INFO, True, "第1行前綴正確")
        
        if not tle_record.line2.startswith('2 '):
            self._add_result("line2_prefix", ValidationSeverity.ERROR, False, "第2行應以 '2 ' 開始")
        else:
            self._add_result("line2_prefix", ValidationSeverity.INFO, True, "第2行前綴正確")
        
        # 檢查 NORAD ID 一致性
        try:
            norad1 = tle_record.line1[2:7]
            norad2 = tle_record.line2[2:7]
            if norad1 != norad2:
                self._add_result("norad_consistency", ValidationSeverity.ERROR, False,
                               f"NORAD ID 不一致: 行1={norad1}, 行2={norad2}")
            else:
                self._add_result("norad_consistency", ValidationSeverity.INFO, True, "NORAD ID 一致")
        except IndexError:
            self._add_result("norad_consistency", ValidationSeverity.ERROR, False, "無法提取 NORAD ID")
    
    def _validate_checksums(self, tle_record: TLERecord):
        """檢查碼驗證"""
        def calculate_checksum(line: str) -> int:
            """計算 TLE 行的檢查碼"""
            checksum = 0
            for char in line[:-1]:  # 除去最後一位檢查碼
                if char.isdigit():
                    checksum += int(char)
                elif char == '-':
                    checksum += 1
            return checksum % 10
        
        # 驗證第1行檢查碼
        try:
            expected_checksum1 = calculate_checksum(tle_record.line1)
            actual_checksum1 = int(tle_record.line1[-1])
            
            if expected_checksum1 == actual_checksum1:
                self._add_result("line1_checksum", ValidationSeverity.INFO, True, "第1行檢查碼正確")
            else:
                self._add_result("line1_checksum", ValidationSeverity.ERROR, False,
                               f"第1行檢查碼錯誤: 期望={expected_checksum1}, 實際={actual_checksum1}")
        except (ValueError, IndexError):
            self._add_result("line1_checksum", ValidationSeverity.ERROR, False, "第1行檢查碼格式錯誤")
        
        # 驗證第2行檢查碼
        try:
            expected_checksum2 = calculate_checksum(tle_record.line2)
            actual_checksum2 = int(tle_record.line2[-1])
            
            if expected_checksum2 == actual_checksum2:
                self._add_result("line2_checksum", ValidationSeverity.INFO, True, "第2行檢查碼正確")
            else:
                self._add_result("line2_checksum", ValidationSeverity.ERROR, False,
                               f"第2行檢查碼錯誤: 期望={expected_checksum2}, 實際={actual_checksum2}")
        except (ValueError, IndexError):
            self._add_result("line2_checksum", ValidationSeverity.ERROR, False, "第2行檢查碼格式錯誤")
    
    def _validate_orbital_elements(self, tle_record: TLERecord):
        """軌道元素合理性驗證"""
        try:
            # 提取軌道元素
            inclination = float(tle_record.line2[8:16])
            eccentricity_str = tle_record.line2[26:33]
            eccentricity = float(f"0.{eccentricity_str}")
            mean_motion = float(tle_record.line2[52:63])
            
            # 軌道傾角驗證 (0-180度)
            if 0 <= inclination <= 180:
                self._add_result("inclination_range", ValidationSeverity.INFO, True,
                               f"軌道傾角正常: {inclination}°")
            else:
                self._add_result("inclination_range", ValidationSeverity.ERROR, False,
                               f"軌道傾角超出範圍: {inclination}° (應為0-180°)")
            
            # 偏心率驗證 (0-1)
            if 0 <= eccentricity < 1:
                self._add_result("eccentricity_range", ValidationSeverity.INFO, True,
                               f"偏心率正常: {eccentricity}")
            else:
                self._add_result("eccentricity_range", ValidationSeverity.ERROR, False,
                               f"偏心率超出範圍: {eccentricity} (應為0-1)")
            
            # 平均運動驗證 (LEO 衛星應在 10-20 rev/day 範圍內)
            if 10 < mean_motion < 20:
                self._add_result("mean_motion_leo", ValidationSeverity.INFO, True,
                               f"平均運動符合LEO範圍: {mean_motion} rev/day")
            elif 1 < mean_motion <= 10:
                self._add_result("mean_motion_leo", ValidationSeverity.WARNING, True,
                               f"平均運動較低 (可能為MEO/GEO): {mean_motion} rev/day")
            else:
                self._add_result("mean_motion_leo", ValidationSeverity.WARNING, True,
                               f"平均運動異常: {mean_motion} rev/day")
            
            # 計算軌道高度驗證
            altitude_km = self._calculate_altitude_from_mean_motion(mean_motion)
            if 200 <= altitude_km <= 2000:  # LEO 範圍
                self._add_result("altitude_leo", ValidationSeverity.INFO, True,
                               f"軌道高度符合LEO: {altitude_km:.0f}km")
            elif altitude_km > 2000:
                self._add_result("altitude_leo", ValidationSeverity.WARNING, True,
                               f"軌道高度為MEO/GEO: {altitude_km:.0f}km")
            else:
                self._add_result("altitude_leo", ValidationSeverity.ERROR, False,
                               f"軌道高度過低: {altitude_km:.0f}km (低於200km)")
                
        except (ValueError, IndexError) as e:
            self._add_result("orbital_elements_parsing", ValidationSeverity.ERROR, False,
                           f"軌道元素解析失敗: {str(e)}")
    
    def _calculate_altitude_from_mean_motion(self, mean_motion: float) -> float:
        """根據平均運動計算軌道高度"""
        # 使用 Kepler's 第三定律
        mu = 3.986004418e14  # 地球引力參數 (m³/s²)
        earth_radius = 6371000  # 地球半徑 (m)
        
        # 轉換為弧度/秒
        n_rad_per_sec = mean_motion * 2 * math.pi / 86400
        
        # 計算半長軸
        semi_major_axis = (mu / (n_rad_per_sec ** 2)) ** (1/3)
        
        # 計算高度
        altitude_m = semi_major_axis - earth_radius
        return altitude_m / 1000  # 轉換為公里
    
    def _validate_epoch_freshness(self, tle_record: TLERecord):
        """時間新鮮度驗證"""
        now = datetime.now(timezone.utc)
        age = now - tle_record.epoch
        age_days = age.total_seconds() / 86400
        
        if age_days <= 1:
            self._add_result("epoch_freshness", ValidationSeverity.INFO, True,
                           f"數據非常新鮮: {age_days:.1f} 天")
        elif age_days <= 3:
            self._add_result("epoch_freshness", ValidationSeverity.INFO, True,
                           f"數據新鮮: {age_days:.1f} 天")
        elif age_days <= 7:
            self._add_result("epoch_freshness", ValidationSeverity.WARNING, True,
                           f"數據較舊: {age_days:.1f} 天")
        elif age_days <= 14:
            self._add_result("epoch_freshness", ValidationSeverity.WARNING, True,
                           f"數據過舊: {age_days:.1f} 天")
        else:
            self._add_result("epoch_freshness", ValidationSeverity.ERROR, False,
                           f"數據嚴重過期: {age_days:.1f} 天 (超過14天)")
    
    def _validate_physical_constraints(self, tle_record: TLERecord):
        """物理約束驗證"""
        try:
            # 提取拖拽項係數 (BSTAR)
            bstar_str = tle_record.line1[53:61]
            if bstar_str.strip():
                # 解析科學記數法格式
                sign = 1 if bstar_str[0] != '-' else -1
                mantissa = float(f"0.{bstar_str[1:6]}")
                exponent = int(bstar_str[6:8])
                bstar = sign * mantissa * (10 ** exponent)
                
                # BSTAR 係數合理性檢查
                if abs(bstar) < 1e-3:  # 大氣阻力係數通常很小
                    self._add_result("bstar_reasonable", ValidationSeverity.INFO, True,
                                   f"BSTAR係數合理: {bstar:.2e}")
                else:
                    self._add_result("bstar_reasonable", ValidationSeverity.WARNING, True,
                                   f"BSTAR係數較大: {bstar:.2e}")
            
        except (ValueError, IndexError):
            self._add_result("bstar_parsing", ValidationSeverity.WARNING, True, "BSTAR係數解析困難，跳過驗證")
    
    def _add_result(self, check_name: str, severity: ValidationSeverity, 
                   passed: bool, message: str, details: Dict = None):
        """添加驗證結果"""
        result = ValidationResult(
            check_name=check_name,
            severity=severity,
            passed=passed,
            message=message,
            details=details
        )
        self.validation_results.append(result)


class DataIntegrityValidator:
    """數據完整性驗證器"""
    
    def __init__(self):
        self.tle_validator = TLEValidator()
        logger.info("數據完整性驗證器初始化完成")
    
    def validate_tle_dataset(self, tle_records: List[TLERecord]) -> ValidationReport:
        """驗證完整的 TLE 數據集"""
        logger.info(f"開始驗證 {len(tle_records)} 個 TLE 記錄...")
        
        all_results = []
        passed_count = 0
        
        # 逐個驗證 TLE 記錄
        for i, tle_record in enumerate(tle_records):
            try:
                results = self.tle_validator.validate_tle_record(tle_record)
                all_results.extend(results)
                
                # 統計通過的檢查
                record_passed = sum(1 for r in results if r.passed)
                if record_passed == len(results):
                    passed_count += 1
                    
            except Exception as e:
                error_result = ValidationResult(
                    check_name=f"record_{i}_validation",
                    severity=ValidationSeverity.CRITICAL,
                    passed=False,
                    message=f"TLE記錄驗證失敗: {str(e)}",
                    details={"satellite_name": tle_record.satellite_name}
                )
                all_results.append(error_result)
        
        # 數據集級別的驗證
        dataset_results = self._validate_dataset_properties(tle_records)
        all_results.extend(dataset_results)
        
        # 生成最終報告
        total_checks = len(all_results)
        passed_checks = sum(1 for r in all_results if r.passed)
        failed_checks = total_checks - passed_checks
        
        # 確定整體狀態
        critical_failures = sum(1 for r in all_results if r.severity == ValidationSeverity.CRITICAL and not r.passed)
        error_failures = sum(1 for r in all_results if r.severity == ValidationSeverity.ERROR and not r.passed)
        
        if critical_failures > 0:
            overall_status = "CRITICAL"
        elif error_failures > 0:
            overall_status = "ERROR"
        elif failed_checks > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"
        
        # 生成建議
        recommendations = self._generate_recommendations(all_results)
        
        report = ValidationReport(
            timestamp=datetime.now(timezone.utc),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            results=all_results,
            overall_status=overall_status,
            recommendations=recommendations
        )
        
        logger.info(f"驗證完成: {overall_status}, 通過率: {report.success_rate:.1f}%")
        return report
    
    def _validate_dataset_properties(self, tle_records: List[TLERecord]) -> List[ValidationResult]:
        """驗證數據集整體屬性"""
        results = []
        
        # 檢查數據集大小
        if len(tle_records) >= 1000:
            results.append(ValidationResult(
                "dataset_size", ValidationSeverity.INFO, True,
                f"數據集規模良好: {len(tle_records)} 個記錄"
            ))
        elif len(tle_records) >= 100:
            results.append(ValidationResult(
                "dataset_size", ValidationSeverity.WARNING, True,
                f"數據集規模較小: {len(tle_records)} 個記錄"
            ))
        else:
            results.append(ValidationResult(
                "dataset_size", ValidationSeverity.ERROR, False,
                f"數據集規模過小: {len(tle_records)} 個記錄"
            ))
        
        # 檢查星座分佈
        constellation_count = {}
        for record in tle_records:
            constellation = self._determine_constellation(record.satellite_name)
            constellation_count[constellation] = constellation_count.get(constellation, 0) + 1
        
        if len(constellation_count) >= 2:
            results.append(ValidationResult(
                "constellation_diversity", ValidationSeverity.INFO, True,
                f"包含多個星座: {list(constellation_count.keys())}"
            ))
        else:
            results.append(ValidationResult(
                "constellation_diversity", ValidationSeverity.WARNING, True,
                f"星座多樣性較低: {list(constellation_count.keys())}"
            ))
        
        # 檢查數據新鮮度分佈
        now = datetime.now(timezone.utc)
        age_distribution = {"fresh": 0, "acceptable": 0, "stale": 0}
        
        for record in tle_records:
            age_days = (now - record.epoch).total_seconds() / 86400
            if age_days <= 3:
                age_distribution["fresh"] += 1
            elif age_days <= 14:
                age_distribution["acceptable"] += 1
            else:
                age_distribution["stale"] += 1
        
        fresh_ratio = age_distribution["fresh"] / len(tle_records)
        if fresh_ratio >= 0.8:
            results.append(ValidationResult(
                "data_freshness_distribution", ValidationSeverity.INFO, True,
                f"數據新鮮度良好: {fresh_ratio:.1%} 為新鮮數據"
            ))
        elif fresh_ratio >= 0.5:
            results.append(ValidationResult(
                "data_freshness_distribution", ValidationSeverity.WARNING, True,
                f"數據新鮮度一般: {fresh_ratio:.1%} 為新鮮數據"
            ))
        else:
            results.append(ValidationResult(
                "data_freshness_distribution", ValidationSeverity.ERROR, False,
                f"數據新鮮度不足: {fresh_ratio:.1%} 為新鮮數據"
            ))
        
        return results
    
    def _determine_constellation(self, satellite_name: str) -> str:
        """確定星座類型"""
        name_upper = satellite_name.upper()
        if "STARLINK" in name_upper:
            return "starlink"
        elif "ONEWEB" in name_upper:
            return "oneweb"
        else:
            return "other"
    
    def _generate_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        # 統計問題
        critical_count = sum(1 for r in results if r.severity == ValidationSeverity.CRITICAL and not r.passed)
        error_count = sum(1 for r in results if r.severity == ValidationSeverity.ERROR and not r.passed)
        warning_count = sum(1 for r in results if r.severity == ValidationSeverity.WARNING and not r.passed)
        
        if critical_count > 0:
            recommendations.append(f"立即修復 {critical_count} 個嚴重問題，這些會影響系統正常運行")
        
        if error_count > 0:
            recommendations.append(f"修復 {error_count} 個錯誤，確保數據品質")
        
        if warning_count > 0:
            recommendations.append(f"考慮處理 {warning_count} 個警告，提升數據品質")
        
        # 具體建議
        failed_checks = [r.check_name for r in results if not r.passed]
        
        if "epoch_freshness" in failed_checks:
            recommendations.append("更新過期的TLE數據，建議使用7天內的數據")
        
        if any("checksum" in check for check in failed_checks):
            recommendations.append("重新下載校驗錯誤的TLE文件")
        
        if "dataset_size" in failed_checks:
            recommendations.append("增加TLE數據集規模，確保有足夠的衛星數據")
        
        return recommendations


def create_data_validator() -> DataIntegrityValidator:
    """創建數據驗證器實例"""
    return DataIntegrityValidator()


# 測試代碼
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 創建測試實例
    validator = create_data_validator()
    
    # 創建測試 TLE 記錄
    test_tle = TLERecord(
        satellite_id="STARLINK-1007",
        satellite_name="STARLINK-1007",
        line1="1 44713U 19074A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
        line2="2 44713  53.0538 290.5094 0001597  91.8164 268.3516 15.48919103000009",
        epoch=datetime.now(timezone.utc),
        source_file="test.tle"
    )
    
    # 執行驗證
    results = validator.tle_validator.validate_tle_record(test_tle)
    
    print("驗證結果:")
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"{status} {result.check_name}: {result.message}")