# 🛰️ Phase 1: TLE數據驗證模組
"""
Data Validator - TLE數據完整性和精度驗證
功能: 確保Phase 1 TLE數據品質，90%+成功率，檢測異常數據
版本: Phase 1.1 Enhanced
"""

import logging
import re
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum

class ValidationLevel(Enum):
    """驗證等級"""
    BASIC = "basic"           # 基礎格式驗證
    STANDARD = "standard"     # 標準完整性驗證
    ENHANCED = "enhanced"     # 增強精度驗證
    STRICT = "strict"         # 嚴格科學驗證

class ValidationResult(Enum):
    """驗證結果"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    CRITICAL = "critical"

@dataclass
class ValidationReport:
    """驗證報告"""
    satellite_id: str
    overall_result: ValidationResult
    validation_level: ValidationLevel
    issues_found: List[str]
    warnings: List[str]
    quality_score: float  # 0-100
    recommended_action: str
    
    # 詳細驗證結果
    format_validation: bool
    checksum_validation: bool
    epoch_validation: bool
    orbital_parameters_validation: bool
    physical_constraints_validation: bool
    
    # 性能指標
    validation_duration_ms: float

@dataclass
class TLEQualityMetrics:
    """TLE品質指標"""
    epoch_freshness_hours: float
    orbit_determination_accuracy: float  # 估算精度 (km)
    data_completeness: float            # 0-1
    parameter_consistency: float        # 0-1
    constellation_compliance: float     # 0-1

class EnhancedTLEValidator:
    """Phase 1增強TLE數據驗證器"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.logger = logging.getLogger(__name__)
        self.validation_level = validation_level
        
        # 驗證統計
        self.validation_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'warning_validations': 0,
            'critical_failures': 0,
            'average_quality_score': 0.0,
            'success_rate': 0.0
        }
        
        # 物理約束
        self.EARTH_RADIUS_KM = 6371.0
        self.MIN_LEO_ALTITUDE_KM = 160.0    # 最低LEO高度
        self.MAX_LEO_ALTITUDE_KM = 2000.0   # 最高LEO高度
        self.MIN_INCLINATION_DEG = 0.0
        self.MAX_INCLINATION_DEG = 180.0
        self.MIN_ECCENTRICITY = 0.0
        self.MAX_ECCENTRICITY = 0.999
        
        # Starlink特定約束
        self.STARLINK_CONSTRAINTS = {
            'typical_altitude_km': 550.0,
            'altitude_tolerance_km': 100.0,
            'typical_inclination_deg': 53.0,
            'inclination_tolerance_deg': 5.0,
            'typical_eccentricity': 0.0001,
            'max_eccentricity': 0.01
        }
        
        # OneWeb特定約束
        self.ONEWEB_CONSTRAINTS = {
            'typical_altitude_km': 1200.0,
            'altitude_tolerance_km': 50.0,
            'typical_inclination_deg': 87.4,
            'inclination_tolerance_deg': 2.0,
            'typical_eccentricity': 0.0001,
            'max_eccentricity': 0.01
        }
    
    async def validate_tle_data(self, 
                               tle_data,  # TLEData object
                               constellation: str = "unknown") -> ValidationReport:
        """完整TLE數據驗證 - Phase 1規格"""
        
        start_time = datetime.now()
        issues = []
        warnings = []
        quality_score = 100.0
        
        try:
            self.validation_stats['total_validations'] += 1
            
            # 1. 格式驗證 (基礎)
            format_valid = await self._validate_tle_format(tle_data, issues, warnings)
            if not format_valid:
                quality_score -= 30
            
            # 2. 校驗和驗證 (標準)
            checksum_valid = True
            if self.validation_level.value in ['standard', 'enhanced', 'strict']:
                checksum_valid = await self._validate_checksums(tle_data, issues, warnings)
                if not checksum_valid:
                    quality_score -= 20
            
            # 3. Epoch驗證 (增強)
            epoch_valid = True
            if self.validation_level.value in ['enhanced', 'strict']:
                epoch_valid = await self._validate_epoch_freshness(tle_data, issues, warnings)
                if not epoch_valid:
                    quality_score -= 15
            
            # 4. 軌道參數驗證 (嚴格)
            orbital_valid = True
            if self.validation_level.value in ['strict']:
                orbital_valid = await self._validate_orbital_parameters(tle_data, constellation, issues, warnings)
                if not orbital_valid:
                    quality_score -= 25
            
            # 5. 物理約束驗證 (全等級)
            physical_valid = await self._validate_physical_constraints(tle_data, constellation, issues, warnings)
            if not physical_valid:
                quality_score -= 20
            
            # 計算總體結果
            overall_result = self._determine_overall_result(issues, warnings, quality_score)
            
            # 生成建議行動
            recommended_action = self._generate_recommendation(overall_result, issues, warnings, quality_score)
            
            # 更新統計
            self._update_validation_statistics(overall_result, quality_score)
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return ValidationReport(
                satellite_id=tle_data.satellite_id,
                overall_result=overall_result,
                validation_level=self.validation_level,
                issues_found=issues,
                warnings=warnings,
                quality_score=max(0.0, quality_score),
                recommended_action=recommended_action,
                format_validation=format_valid,
                checksum_validation=checksum_valid,
                epoch_validation=epoch_valid,
                orbital_parameters_validation=orbital_valid,
                physical_constraints_validation=physical_valid,
                validation_duration_ms=duration_ms
            )
            
        except Exception as e:
            self.logger.error(f"❌ TLE驗證異常 {tle_data.satellite_id}: {e}")
            self.validation_stats['critical_failures'] += 1
            
            return ValidationReport(
                satellite_id=tle_data.satellite_id,
                overall_result=ValidationResult.CRITICAL,
                validation_level=self.validation_level,
                issues_found=[f"驗證過程異常: {e}"],
                warnings=[],
                quality_score=0.0,
                recommended_action="重新載入TLE數據",
                format_validation=False,
                checksum_validation=False,
                epoch_validation=False,
                orbital_parameters_validation=False,
                physical_constraints_validation=False,
                validation_duration_ms=0.0
            )
    
    async def _validate_tle_format(self, tle_data, issues: List[str], warnings: List[str]) -> bool:
        """驗證TLE格式"""
        
        valid = True
        
        try:
            # 檢查Line1格式
            if not tle_data.line1 or len(tle_data.line1) != 69:
                issues.append(f"Line1長度錯誤: {len(tle_data.line1) if tle_data.line1 else 0} (預期69)")
                valid = False
            elif not tle_data.line1.startswith('1 '):
                issues.append("Line1不以'1 '開始")
                valid = False
            
            # 檢查Line2格式
            if not tle_data.line2 or len(tle_data.line2) != 69:
                issues.append(f"Line2長度錯誤: {len(tle_data.line2) if tle_data.line2 else 0} (預期69)")
                valid = False
            elif not tle_data.line2.startswith('2 '):
                issues.append("Line2不以'2 '開始")
                valid = False
            
            # 檢查衛星編號一致性
            if tle_data.line1 and tle_data.line2:
                sat_num1 = tle_data.line1[2:7]
                sat_num2 = tle_data.line2[2:7]
                if sat_num1 != sat_num2:
                    issues.append(f"衛星編號不一致: Line1={sat_num1}, Line2={sat_num2}")
                    valid = False
            
            # 檢查必要字段
            if not tle_data.satellite_name or len(tle_data.satellite_name.strip()) == 0:
                warnings.append("衛星名稱為空")
            
            if not tle_data.satellite_id or len(tle_data.satellite_id.strip()) == 0:
                issues.append("衛星ID為空")
                valid = False
            
        except Exception as e:
            issues.append(f"格式驗證異常: {e}")
            valid = False
        
        return valid
    
    async def _validate_checksums(self, tle_data, issues: List[str], warnings: List[str]) -> bool:
        """驗證TLE校驗和"""
        
        valid = True
        
        try:
            # Line1校驗和
            if tle_data.line1 and len(tle_data.line1) >= 69:
                calculated_checksum1 = self._calculate_tle_checksum(tle_data.line1[:-1])
                actual_checksum1 = int(tle_data.line1[-1])
                
                if calculated_checksum1 != actual_checksum1:
                    issues.append(f"Line1校驗和錯誤: 計算={calculated_checksum1}, 實際={actual_checksum1}")
                    valid = False
            
            # Line2校驗和
            if tle_data.line2 and len(tle_data.line2) >= 69:
                calculated_checksum2 = self._calculate_tle_checksum(tle_data.line2[:-1])
                actual_checksum2 = int(tle_data.line2[-1])
                
                if calculated_checksum2 != actual_checksum2:
                    issues.append(f"Line2校驗和錯誤: 計算={calculated_checksum2}, 實際={actual_checksum2}")
                    valid = False
                    
        except Exception as e:
            issues.append(f"校驗和驗證異常: {e}")
            valid = False
        
        return valid
    
    def _calculate_tle_checksum(self, line: str) -> int:
        """計算TLE校驗和"""
        
        checksum = 0
        for char in line:
            if char.isdigit():
                checksum += int(char)
            elif char == '-':
                checksum += 1
        
        return checksum % 10
    
    async def _validate_epoch_freshness(self, tle_data, issues: List[str], warnings: List[str]) -> bool:
        """驗證Epoch新鮮度"""
        
        valid = True
        
        try:
            current_time = datetime.now(timezone.utc)
            epoch_age = current_time - tle_data.epoch
            
            # Epoch新鮮度檢查
            if epoch_age.days > 30:
                issues.append(f"Epoch過舊: {epoch_age.days}天 (>30天)")
                valid = False
            elif epoch_age.days > 7:
                warnings.append(f"Epoch較舊: {epoch_age.days}天 (建議<7天)")
            
            # 未來Epoch檢查
            if epoch_age.total_seconds() < -3600:  # 未來1小時以上
                issues.append(f"Epoch為未來時間: {-epoch_age.total_seconds()/3600:.1f}小時")
                valid = False
                
        except Exception as e:
            issues.append(f"Epoch驗證異常: {e}")
            valid = False
        
        return valid
    
    async def _validate_orbital_parameters(self, tle_data, constellation: str, 
                                         issues: List[str], warnings: List[str]) -> bool:
        """驗證軌道參數"""
        
        valid = True
        
        try:
            # 軌道傾角驗證
            if not (self.MIN_INCLINATION_DEG <= tle_data.inclination_deg <= self.MAX_INCLINATION_DEG):
                issues.append(f"軌道傾角超範圍: {tle_data.inclination_deg}° (有效範圍: {self.MIN_INCLINATION_DEG}-{self.MAX_INCLINATION_DEG}°)")
                valid = False
            
            # 偏心率驗證
            if not (self.MIN_ECCENTRICITY <= tle_data.eccentricity <= self.MAX_ECCENTRICITY):
                issues.append(f"偏心率超範圍: {tle_data.eccentricity} (有效範圍: {self.MIN_ECCENTRICITY}-{self.MAX_ECCENTRICITY})")
                valid = False
            
            # 升交點赤經驗證
            if not (0.0 <= tle_data.raan_deg < 360.0):
                issues.append(f"升交點赤經超範圍: {tle_data.raan_deg}° (有效範圍: 0-360°)")
                valid = False
            
            # 近地點幅角驗證
            if not (0.0 <= tle_data.arg_perigee_deg < 360.0):
                issues.append(f"近地點幅角超範圍: {tle_data.arg_perigee_deg}° (有效範圍: 0-360°)")
                valid = False
            
            # 平近點角驗證
            if not (0.0 <= tle_data.mean_anomaly_deg < 360.0):
                issues.append(f"平近點角超範圍: {tle_data.mean_anomaly_deg}° (有效範圍: 0-360°)")
                valid = False
            
            # 平均運動驗證
            if tle_data.mean_motion_revs_per_day <= 0:
                issues.append(f"平均運動異常: {tle_data.mean_motion_revs_per_day} (必須>0)")
                valid = False
            elif tle_data.mean_motion_revs_per_day > 25.0:  # 極限情況
                warnings.append(f"平均運動過高: {tle_data.mean_motion_revs_per_day} rev/day")
            
            # 星座特定驗證
            if constellation.lower() == 'starlink':
                valid &= await self._validate_starlink_parameters(tle_data, issues, warnings)
            elif constellation.lower() == 'oneweb':
                valid &= await self._validate_oneweb_parameters(tle_data, issues, warnings)
                
        except Exception as e:
            issues.append(f"軌道參數驗證異常: {e}")
            valid = False
        
        return valid
    
    async def _validate_starlink_parameters(self, tle_data, issues: List[str], warnings: List[str]) -> bool:
        """驗證Starlink特定參數"""
        
        valid = True
        constraints = self.STARLINK_CONSTRAINTS
        
        try:
            # 高度檢查
            altitude_km = tle_data.semi_major_axis_km - self.EARTH_RADIUS_KM
            expected_alt = constraints['typical_altitude_km']
            tolerance = constraints['altitude_tolerance_km']
            
            if abs(altitude_km - expected_alt) > tolerance:
                warnings.append(f"Starlink高度異常: {altitude_km:.0f}km (典型: {expected_alt}±{tolerance}km)")
            
            # 傾角檢查
            expected_inc = constraints['typical_inclination_deg']
            tolerance = constraints['inclination_tolerance_deg']
            
            if abs(tle_data.inclination_deg - expected_inc) > tolerance:
                warnings.append(f"Starlink傾角異常: {tle_data.inclination_deg:.1f}° (典型: {expected_inc}±{tolerance}°)")
            
            # 偏心率檢查
            if tle_data.eccentricity > constraints['max_eccentricity']:
                issues.append(f"Starlink偏心率過高: {tle_data.eccentricity} (最大: {constraints['max_eccentricity']})")
                valid = False
                
        except Exception as e:
            issues.append(f"Starlink參數驗證異常: {e}")
            valid = False
        
        return valid
    
    async def _validate_oneweb_parameters(self, tle_data, issues: List[str], warnings: List[str]) -> bool:
        """驗證OneWeb特定參數"""
        
        valid = True
        constraints = self.ONEWEB_CONSTRAINTS
        
        try:
            # 高度檢查
            altitude_km = tle_data.semi_major_axis_km - self.EARTH_RADIUS_KM
            expected_alt = constraints['typical_altitude_km']
            tolerance = constraints['altitude_tolerance_km']
            
            if abs(altitude_km - expected_alt) > tolerance:
                warnings.append(f"OneWeb高度異常: {altitude_km:.0f}km (典型: {expected_alt}±{tolerance}km)")
            
            # 傾角檢查 (OneWeb高傾角極地軌道)
            expected_inc = constraints['typical_inclination_deg']
            tolerance = constraints['inclination_tolerance_deg']
            
            if abs(tle_data.inclination_deg - expected_inc) > tolerance:
                warnings.append(f"OneWeb傾角異常: {tle_data.inclination_deg:.1f}° (典型: {expected_inc}±{tolerance}°)")
            
            # 偏心率檢查
            if tle_data.eccentricity > constraints['max_eccentricity']:
                issues.append(f"OneWeb偏心率過高: {tle_data.eccentricity} (最大: {constraints['max_eccentricity']})")
                valid = False
                
        except Exception as e:
            issues.append(f"OneWeb參數驗證異常: {e}")
            valid = False
        
        return valid
    
    async def _validate_physical_constraints(self, tle_data, constellation: str,
                                           issues: List[str], warnings: List[str]) -> bool:
        """驗證物理約束"""
        
        valid = True
        
        try:
            # 高度約束
            altitude_km = tle_data.semi_major_axis_km - self.EARTH_RADIUS_KM
            
            if altitude_km < self.MIN_LEO_ALTITUDE_KM:
                issues.append(f"軌道過低: {altitude_km:.0f}km (<{self.MIN_LEO_ALTITUDE_KM}km)")
                valid = False
            elif altitude_km > self.MAX_LEO_ALTITUDE_KM:
                warnings.append(f"軌道較高: {altitude_km:.0f}km (>{self.MAX_LEO_ALTITUDE_KM}km, 非典型LEO)")
            
            # 軌道週期合理性
            expected_period = 2 * np.pi * np.sqrt(tle_data.semi_major_axis_km**3 / 398600.4418) / 60  # 分鐘
            
            if abs(expected_period - tle_data.orbital_period_minutes) > 5.0:
                warnings.append(f"軌道週期不一致: 計算={expected_period:.1f}min, TLE={tle_data.orbital_period_minutes:.1f}min")
            
            # 遠地點/近地點約束
            if tle_data.perigee_altitude_km < self.MIN_LEO_ALTITUDE_KM:
                issues.append(f"近地點過低: {tle_data.perigee_altitude_km:.0f}km")
                valid = False
            
            if tle_data.apogee_altitude_km > 50000.0:  # 極限檢查
                issues.append(f"遠地點過高: {tle_data.apogee_altitude_km:.0f}km")
                valid = False
                
        except Exception as e:
            issues.append(f"物理約束驗證異常: {e}")
            valid = False
        
        return valid
    
    def _determine_overall_result(self, issues: List[str], warnings: List[str], quality_score: float) -> ValidationResult:
        """決定總體驗證結果"""
        
        if quality_score < 30.0 or len(issues) >= 5:
            return ValidationResult.CRITICAL
        elif quality_score < 60.0 or len(issues) >= 3:
            return ValidationResult.FAIL
        elif quality_score < 80.0 or len(issues) >= 1:
            return ValidationResult.WARNING
        else:
            return ValidationResult.PASS
    
    def _generate_recommendation(self, result: ValidationResult, issues: List[str], 
                               warnings: List[str], quality_score: float) -> str:
        """生成建議行動"""
        
        if result == ValidationResult.CRITICAL:
            return "立即停止使用，重新下載TLE數據"
        elif result == ValidationResult.FAIL:
            return "不建議用於精確計算，檢查數據源"
        elif result == ValidationResult.WARNING:
            return "可用但需密切監控，建議更新數據"
        else:
            return "數據品質良好，適合使用"
    
    def _update_validation_statistics(self, result: ValidationResult, quality_score: float):
        """更新驗證統計"""
        
        if result == ValidationResult.PASS:
            self.validation_stats['passed_validations'] += 1
        elif result == ValidationResult.WARNING:
            self.validation_stats['warning_validations'] += 1
        elif result == ValidationResult.FAIL:
            self.validation_stats['failed_validations'] += 1
        elif result == ValidationResult.CRITICAL:
            self.validation_stats['critical_failures'] += 1
        
        # 更新平均品質分數
        total_validations = self.validation_stats['total_validations']
        current_avg = self.validation_stats['average_quality_score']
        self.validation_stats['average_quality_score'] = (
            (current_avg * (total_validations - 1) + quality_score) / total_validations
        )
        
        # 更新成功率
        successful = (self.validation_stats['passed_validations'] + 
                     self.validation_stats['warning_validations'])
        self.validation_stats['success_rate'] = successful / total_validations * 100.0
    
    def get_validation_statistics(self) -> Dict:
        """獲取驗證統計"""
        return self.validation_stats.copy()
    
    async def batch_validate(self, tle_data_list: List, constellation: str = "unknown") -> List[ValidationReport]:
        """批量驗證TLE數據"""
        
        self.logger.info(f"🔍 開始批量驗證 {len(tle_data_list)} 顆衛星TLE數據...")
        
        reports = []
        
        # 並行驗證 (分批處理)
        batch_size = 50
        for i in range(0, len(tle_data_list), batch_size):
            batch = tle_data_list[i:i + batch_size]
            
            # 並行驗證批次
            batch_tasks = [self.validate_tle_data(tle_data, constellation) for tle_data in batch]
            batch_reports = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 處理結果
            for report in batch_reports:
                if isinstance(report, Exception):
                    self.logger.error(f"批量驗證異常: {report}")
                    continue
                reports.append(report)
        
        # 生成批量統計
        self._generate_batch_statistics(reports)
        
        return reports
    
    def _generate_batch_statistics(self, reports: List[ValidationReport]):
        """生成批量統計"""
        
        if not reports:
            return
        
        total = len(reports)
        passed = sum(1 for r in reports if r.overall_result == ValidationResult.PASS)
        warnings = sum(1 for r in reports if r.overall_result == ValidationResult.WARNING)
        failed = sum(1 for r in reports if r.overall_result == ValidationResult.FAIL)
        critical = sum(1 for r in reports if r.overall_result == ValidationResult.CRITICAL)
        
        avg_quality = sum(r.quality_score for r in reports) / total
        
        self.logger.info(f"📊 批量驗證統計:")
        self.logger.info(f"   總計: {total}顆")
        self.logger.info(f"   通過: {passed}顆 ({passed/total*100:.1f}%)")
        self.logger.info(f"   警告: {warnings}顆 ({warnings/total*100:.1f}%)")
        self.logger.info(f"   失敗: {failed}顆 ({failed/total*100:.1f}%)")
        self.logger.info(f"   嚴重: {critical}顆 ({critical/total*100:.1f}%)")
        self.logger.info(f"   平均品質分數: {avg_quality:.1f}/100")
        
        success_rate = (passed + warnings) / total * 100
        if success_rate >= 90.0:
            self.logger.info(f"✅ Phase 1成功率目標達成: {success_rate:.1f}% (≥90%)")
        else:
            self.logger.warning(f"⚠️ Phase 1成功率不足: {success_rate:.1f}% (<90%)")

# 使用範例
async def test_tle_validator():
    """測試TLE驗證器"""
    
    validator = EnhancedTLEValidator(ValidationLevel.ENHANCED)
    
    # 模擬TLE數據
    from ..tle_loader_engine import TLEData
    
    test_tle = TLEData(
        satellite_id="STARLINK-TEST",
        satellite_name="STARLINK-1234",
        line1="1 12345U 21001A   21001.50000000  .00000000  00000-0  00000-0 0    00",
        line2="2 12345  53.0000 150.0000 0001000  90.0000  45.0000 15.50000000    00",
        epoch=datetime.now(timezone.utc),
        constellation="starlink",
        inclination_deg=53.0,
        raan_deg=150.0,
        eccentricity=0.0001,
        arg_perigee_deg=90.0,
        mean_anomaly_deg=45.0,
        mean_motion_revs_per_day=15.5,
        semi_major_axis_km=6900.0,
        orbital_period_minutes=96.0,
        apogee_altitude_km=550.0,
        perigee_altitude_km=549.0
    )
    
    # 驗證測試
    report = await validator.validate_tle_data(test_tle, "starlink")
    
    print(f"✅ TLE驗證測試完成")
    print(f"   結果: {report.overall_result.value}")
    print(f"   品質分數: {report.quality_score:.1f}/100")
    print(f"   問題: {len(report.issues_found)}個")
    print(f"   警告: {len(report.warnings)}個")
    print(f"   建議: {report.recommended_action}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tle_validator())