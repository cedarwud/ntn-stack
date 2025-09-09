"""
學術標準驗證引擎
Academic Standards Validation Engine

實現 Grade A 數據強制檢查、物理參數合理性驗證、時間基準一致性檢查
Based on Phase 2 specifications: academic_standards_engine.py
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import re
from datetime import datetime, timezone
import numpy as np
from dataclasses import dataclass

from ..core.base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationLevel
from ..config.academic_standards_config import (
    AcademicStandardsConfig, GradeLevel, ValidationSeverity,
    get_academic_config
)


@dataclass
class ECICoordinateValidationResult:
    """ECI座標驗證結果"""
    total_coordinates: int
    zero_coordinates: int
    zero_percentage: float
    invalid_ranges: List[Dict[str, Any]]
    is_compliant: bool
    violation_details: List[str]


@dataclass
class TLEValidationResult:
    """TLE驗證結果"""
    total_satellites: int
    valid_tle_count: int
    invalid_tle_count: int
    epoch_time_violations: List[str]
    time_base_compliance: bool
    validation_details: List[str]


@dataclass
class PhysicalParameterValidationResult:
    """物理參數驗證結果"""
    parameter_name: str
    total_values: int
    valid_values: int
    invalid_values: int
    range_violations: List[Dict[str, Any]]
    is_compliant: bool
    validation_summary: str


class GradeADataValidator(BaseValidator):
    """Grade A 數據強制檢查器"""
    
    def __init__(self, config: AcademicStandardsConfig = None):
        self.config = config or get_academic_config()
        self.grade_a_rules = self.config.get_grade_a_requirements()
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """執行 Grade A 數據驗證"""
        validation_errors = []
        validation_warnings = []
        
        try:
            # ECI 座標驗證
            eci_result = self.validate_eci_coordinates(data.get('orbital_data', []))
            if not eci_result.is_compliant:
                validation_errors.extend(eci_result.violation_details)
            
            # TLE 數據驗證  
            tle_result = self.validate_tle_data(data.get('tle_data', []))
            if not tle_result.time_base_compliance:
                validation_errors.extend(tle_result.epoch_time_violations)
            
            # 物理參數驗證
            physics_violations = self.validate_physical_parameters(data)
            validation_errors.extend(physics_violations)
            
            # 禁止模式檢測
            if 'source_code' in data:
                forbidden_violations = self.detect_forbidden_patterns(data['source_code'])
                validation_errors.extend(forbidden_violations)
            
            # 確定驗證狀態
            if validation_errors:
                status = ValidationStatus.FAILED
                level = ValidationLevel.CRITICAL
            else:
                status = ValidationStatus.PASSED
                level = ValidationLevel.INFO
            
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=status,
                level=level,
                message=f"Grade A data validation {'failed' if validation_errors else 'passed'}",
                details={
                    'eci_validation': eci_result,
                    'tle_validation': tle_result,
                    'errors': validation_errors,
                    'warnings': validation_warnings
                },
                errors=validation_errors,
                warnings=validation_warnings,
                metadata={'grade_level': 'A', 'validation_timestamp': datetime.now(timezone.utc).isoformat()}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Grade A validation error: {str(e)}",
                details={'exception': str(e)},
                errors=[f"Validation engine error: {str(e)}"],
                warnings=[],
                metadata={'grade_level': 'A'}
            )
    
    def validate_eci_coordinates(self, orbital_data: List[Dict]) -> ECICoordinateValidationResult:
        """驗證 ECI 座標數據"""
        if not orbital_data:
            return ECICoordinateValidationResult(
                total_coordinates=0,
                zero_coordinates=0,
                zero_percentage=0.0,
                invalid_ranges=[],
                is_compliant=False,
                violation_details=["No orbital data provided"]
            )
        
        total_coords = len(orbital_data)
        zero_coords = 0
        invalid_ranges = []
        violation_details = []
        
        coordinate_range = self.grade_a_rules['eci_coordinates']['range_check']
        mandatory_fields = self.grade_a_rules['eci_coordinates']['mandatory_fields']
        
        for i, coord_data in enumerate(orbital_data):
            # 檢查必需欄位
            for field in mandatory_fields:
                if field not in coord_data:
                    violation_details.append(f"Missing mandatory field '{field}' at index {i}")
                    continue
            
            # 檢查零值
            eci_coords = [
                coord_data.get('x', 0),
                coord_data.get('y', 0), 
                coord_data.get('z', 0)
            ]
            
            if all(coord == 0 for coord in eci_coords):
                zero_coords += 1
                violation_details.append(f"Zero ECI coordinates detected at index {i}")
            
            # 檢查座標範圍
            for coord_name, coord_value in zip(['x', 'y', 'z'], eci_coords):
                if not (coordinate_range[0] <= coord_value <= coordinate_range[1]):
                    invalid_ranges.append({
                        'index': i,
                        'coordinate': coord_name,
                        'value': coord_value,
                        'valid_range': coordinate_range
                    })
                    violation_details.append(
                        f"ECI {coord_name} coordinate {coord_value} out of range {coordinate_range} at index {i}"
                    )
        
        zero_percentage = (zero_coords / total_coords) * 100 if total_coords > 0 else 0
        threshold = self.grade_a_rules['eci_coordinates']['zero_tolerance_threshold'] * 100
        is_compliant = zero_percentage <= threshold
        
        if not is_compliant:
            violation_details.append(
                f"Zero coordinate percentage {zero_percentage:.2f}% exceeds threshold {threshold:.2f}%"
            )
        
        return ECICoordinateValidationResult(
            total_coordinates=total_coords,
            zero_coordinates=zero_coords,
            zero_percentage=zero_percentage,
            invalid_ranges=invalid_ranges,
            is_compliant=is_compliant,
            violation_details=violation_details
        )
    
    def validate_tle_data(self, tle_data: List[Dict]) -> TLEValidationResult:
        """驗證 TLE 數據和時間基準"""
        if not tle_data:
            return TLEValidationResult(
                total_satellites=0,
                valid_tle_count=0,
                invalid_tle_count=0,
                epoch_time_violations=[],
                time_base_compliance=False,
                validation_details=["No TLE data provided"]
            )
        
        total_satellites = len(tle_data)
        valid_tle_count = 0
        invalid_tle_count = 0
        epoch_time_violations = []
        validation_details = []
        
        for i, tle in enumerate(tle_data):
            try:
                # 驗證TLE格式
                if not self._validate_tle_format(tle):
                    invalid_tle_count += 1
                    validation_details.append(f"Invalid TLE format at index {i}")
                    continue
                
                # 驗證 epoch 時間
                if not self._validate_epoch_time(tle):
                    epoch_time_violations.append(f"Invalid epoch time in TLE at index {i}")
                    invalid_tle_count += 1
                    continue
                
                valid_tle_count += 1
                
            except Exception as e:
                invalid_tle_count += 1
                validation_details.append(f"TLE validation error at index {i}: {str(e)}")
        
        time_base_compliance = len(epoch_time_violations) == 0
        
        return TLEValidationResult(
            total_satellites=total_satellites,
            valid_tle_count=valid_tle_count,
            invalid_tle_count=invalid_tle_count,
            epoch_time_violations=epoch_time_violations,
            time_base_compliance=time_base_compliance,
            validation_details=validation_details
        )
    
    def validate_physical_parameters(self, data: Dict[str, Any]) -> List[str]:
        """驗證物理參數合理性"""
        violations = []
        
        # 檢查軌道參數
        if 'orbital_parameters' in data:
            orbital_violations = self._validate_orbital_physics(data['orbital_parameters'])
            violations.extend(orbital_violations)
        
        # 檢查信號參數
        if 'signal_parameters' in data:
            signal_violations = self._validate_signal_physics(data['signal_parameters'])
            violations.extend(signal_violations)
        
        # 檢查時間參數
        if 'time_parameters' in data:
            time_violations = self._validate_time_physics(data['time_parameters'])
            violations.extend(time_violations)
        
        return violations
    
    def detect_forbidden_patterns(self, source_code: str) -> List[str]:
        """檢測禁止的模式和實現"""
        violations = []
        is_forbidden, patterns = self.config.is_forbidden_pattern(source_code)
        
        if is_forbidden:
            for pattern in patterns:
                violations.append(f"Forbidden pattern detected: {pattern}")
        
        # 額外檢查特定的學術違規模式
        academic_violations = self._detect_academic_violations(source_code)
        violations.extend(academic_violations)
        
        return violations
    
    def _validate_tle_format(self, tle: Dict[str, Any]) -> bool:
        """驗證TLE格式"""
        required_fields = ['line1', 'line2', 'satellite_name']
        
        for field in required_fields:
            if field not in tle:
                return False
        
        # 驗證TLE行長度
        if len(tle['line1']) != 69 or len(tle['line2']) != 69:
            return False
        
        # 驗證TLE行格式 (簡化檢查)
        if not tle['line1'].startswith('1 ') or not tle['line2'].startswith('2 '):
            return False
        
        return True
    
    def _validate_epoch_time(self, tle: Dict[str, Any]) -> bool:
        """驗證epoch時間"""
        if 'epoch' not in tle:
            return False
        
        try:
            epoch_str = tle['epoch']
            # 這裡應該根據TLE epoch格式進行詳細驗證
            # 簡化實現：檢查是否為有效的日期字串
            if isinstance(epoch_str, str) and len(epoch_str) > 0:
                return True
            return False
        except Exception:
            return False
    
    def _validate_orbital_physics(self, orbital_params: Dict[str, Any]) -> List[str]:
        """驗證軌道物理參數"""
        violations = []
        
        # 檢查軌道高度範圍 (LEO: 160-2000km)
        if 'altitude' in orbital_params:
            altitude = orbital_params['altitude']
            if not (160 <= altitude <= 2000):
                violations.append(f"Invalid LEO altitude: {altitude} km (expected 160-2000 km)")
        
        # 檢查偏心率範圍
        if 'eccentricity' in orbital_params:
            ecc = orbital_params['eccentricity']
            if not (0 <= ecc < 1):
                violations.append(f"Invalid eccentricity: {ecc} (expected 0 <= e < 1)")
        
        # 檢查傾角範圍
        if 'inclination' in orbital_params:
            inc = orbital_params['inclination']
            if not (0 <= inc <= 180):
                violations.append(f"Invalid inclination: {inc} degrees (expected 0-180)")
        
        return violations
    
    def _validate_signal_physics(self, signal_params: Dict[str, Any]) -> List[str]:
        """驗證信號物理參數"""
        violations = []
        
        # 檢查頻率範圍 (5G NTN 頻段)
        if 'frequency' in signal_params:
            freq = signal_params['frequency']
            # 5G NTN頻段檢查 (GHz)
            valid_bands = [(0.7, 1.0), (1.7, 2.2), (2.5, 2.7), (3.3, 4.2), (24, 29.5)]
            is_valid_band = any(band[0] <= freq <= band[1] for band in valid_bands)
            if not is_valid_band:
                violations.append(f"Invalid 5G NTN frequency: {freq} GHz")
        
        # 檢查功率範圍
        if 'eirp' in signal_params:
            eirp = signal_params['eirp']
            if not (30 <= eirp <= 65):  # dBW, 典型LEO衛星範圍
                violations.append(f"Invalid satellite EIRP: {eirp} dBW (expected 30-65 dBW)")
        
        return violations
    
    def _validate_time_physics(self, time_params: Dict[str, Any]) -> List[str]:
        """驗證時間物理參數"""
        violations = []
        
        # 檢查軌道週期 (LEO: 90-120分鐘)
        if 'orbital_period' in time_params:
            period = time_params['orbital_period']  # minutes
            if not (90 <= period <= 120):
                violations.append(f"Invalid LEO orbital period: {period} minutes (expected 90-120)")
        
        return violations
    
    def _detect_academic_violations(self, source_code: str) -> List[str]:
        """檢測學術違規模式"""
        violations = []
        
        # 檢測時間基準違規
        datetime_now_patterns = [
            r'datetime\.now\(\)',
            r'datetime\.utcnow\(\)',
            r'time\.time\(\)',
            r'當前時間',
            r'current time'
        ]
        
        for pattern in datetime_now_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                violations.append(f"Academic violation: Using current time instead of TLE epoch time - {pattern}")
        
        # 檢測模擬數據違規
        simulation_patterns = [
            r'random\.',
            r'np\.random\.',
            r'假設.*值',
            r'mock.*data',
            r'simulation.*data'
        ]
        
        for pattern in simulation_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                violations.append(f"Academic violation: Using simulated data - {pattern}")
        
        return violations


class PhysicalParameterValidator(BaseValidator):
    """物理參數合理性驗證器"""
    
    def __init__(self, config: AcademicStandardsConfig = None):
        self.config = config or get_academic_config()
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """驗證物理參數合理性"""
        try:
            validation_errors = []
            validation_warnings = []
            
            # 軌道動力學參數驗證
            orbital_result = self._validate_orbital_dynamics(data.get('orbital_data', {}))
            validation_errors.extend(orbital_result.get('errors', []))
            validation_warnings.extend(orbital_result.get('warnings', []))
            
            # 電磁波傳播參數驗證
            propagation_result = self._validate_electromagnetic_propagation(data.get('signal_data', {}))
            validation_errors.extend(propagation_result.get('errors', []))
            validation_warnings.extend(propagation_result.get('warnings', []))
            
            # 幾何計算參數驗證
            geometry_result = self._validate_geometric_calculations(data.get('geometry_data', {}))
            validation_errors.extend(geometry_result.get('errors', []))
            validation_warnings.extend(geometry_result.get('warnings', []))
            
            status = ValidationStatus.FAILED if validation_errors else ValidationStatus.PASSED
            level = ValidationLevel.CRITICAL if validation_errors else ValidationLevel.INFO
            
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=status,
                level=level,
                message=f"Physical parameter validation {'failed' if validation_errors else 'passed'}",
                details={
                    'orbital_validation': orbital_result,
                    'propagation_validation': propagation_result,
                    'geometry_validation': geometry_result
                },
                errors=validation_errors,
                warnings=validation_warnings,
                metadata={'validation_type': 'physical_parameters'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Physical parameter validation error: {str(e)}",
                details={'exception': str(e)},
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                metadata={'validation_type': 'physical_parameters'}
            )
    
    def _validate_orbital_dynamics(self, orbital_data: Dict) -> Dict[str, List[str]]:
        """驗證軌道動力學參數"""
        errors = []
        warnings = []
        
        # Kepler第三定律檢查
        if 'semi_major_axis' in orbital_data and 'orbital_period' in orbital_data:
            a = orbital_data['semi_major_axis']  # km
            T = orbital_data['orbital_period']   # seconds
            
            # μ = 3.986004418e5 km³/s² (地球引力參數)
            expected_period = 2 * np.pi * np.sqrt(a**3 / 3.986004418e5)
            period_diff = abs(T - expected_period) / expected_period
            
            if period_diff > 0.1:  # 10% 容差
                errors.append(f"Orbital period violates Kepler's third law: {period_diff:.2%} deviation")
        
        # 軌道速度檢查
        if 'velocity' in orbital_data and 'altitude' in orbital_data:
            v = orbital_data['velocity']  # km/s
            h = orbital_data['altitude']  # km
            r = h + 6371  # 地球半徑
            
            # 圓軌道速度: v = sqrt(μ/r)
            expected_velocity = np.sqrt(3.986004418e5 / r)
            velocity_diff = abs(v - expected_velocity) / expected_velocity
            
            if velocity_diff > 0.15:  # 15% 容差
                warnings.append(f"Orbital velocity deviation: {velocity_diff:.2%}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_electromagnetic_propagation(self, signal_data: Dict) -> Dict[str, List[str]]:
        """驗證電磁波傳播參數"""
        errors = []
        warnings = []
        
        # Friis公式檢查
        if all(key in signal_data for key in ['tx_power', 'tx_gain', 'rx_gain', 'frequency', 'distance']):
            Pt = signal_data['tx_power']    # dBW
            Gt = signal_data['tx_gain']     # dBi
            Gr = signal_data['rx_gain']     # dBi
            f = signal_data['frequency']    # Hz
            d = signal_data['distance']     # m
            
            # Friis公式: Pr = Pt + Gt + Gr + 20*log10(λ/4πd)
            # λ = c/f, c = 3e8 m/s
            lambda_wave = 3e8 / f
            path_loss_db = 20 * np.log10(4 * np.pi * d / lambda_wave)
            expected_rx_power = Pt + Gt + Gr - path_loss_db
            
            if 'rx_power' in signal_data:
                actual_rx_power = signal_data['rx_power']
                power_diff = abs(actual_rx_power - expected_rx_power)
                if power_diff > 3:  # 3dB 容差
                    errors.append(f"Received power violates Friis formula: {power_diff:.1f} dB deviation")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_geometric_calculations(self, geometry_data: Dict) -> Dict[str, List[str]]:
        """驗證幾何計算參數"""
        errors = []
        warnings = []
        
        # 球面三角學檢查
        if all(key in geometry_data for key in ['elevation', 'azimuth', 'range']):
            elevation = np.radians(geometry_data['elevation'])
            azimuth = np.radians(geometry_data['azimuth'])
            range_km = geometry_data['range']
            
            # 檢查仰角合理性 (不能為負值用於LEO衛星)
            if elevation < 0:
                errors.append(f"Negative elevation angle: {np.degrees(elevation):.1f}°")
            
            # 檢查方位角範圍
            if not (0 <= azimuth <= 2*np.pi):
                warnings.append(f"Azimuth angle out of range: {np.degrees(azimuth):.1f}°")
            
            # 檢查距離合理性 (LEO: 160-2000km + 地球半徑)
            if not (6531 <= range_km <= 8371):  # 6371 + 160 to 6371 + 2000
                warnings.append(f"LEO satellite range out of expected bounds: {range_km:.1f} km")
        
        return {'errors': errors, 'warnings': warnings}


class TimeBaseContinuityChecker(BaseValidator):
    """時間基準一致性檢查器"""
    
    def __init__(self, config: AcademicStandardsConfig = None):
        self.config = config or get_academic_config()
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """檢查時間基準一致性"""
        try:
            validation_errors = []
            validation_warnings = []
            
            # TLE epoch 時間檢查
            tle_time_result = self._validate_tle_epoch_usage(data)
            validation_errors.extend(tle_time_result.get('errors', []))
            validation_warnings.extend(tle_time_result.get('warnings', []))
            
            # 時間序列連續性檢查
            continuity_result = self._validate_time_series_continuity(data)
            validation_errors.extend(continuity_result.get('errors', []))
            validation_warnings.extend(continuity_result.get('warnings', []))
            
            # UTC/GPS時間同步檢查
            sync_result = self._validate_time_synchronization(data)
            validation_errors.extend(sync_result.get('errors', []))
            validation_warnings.extend(sync_result.get('warnings', []))
            
            status = ValidationStatus.FAILED if validation_errors else ValidationStatus.PASSED
            level = ValidationLevel.CRITICAL if validation_errors else ValidationLevel.INFO
            
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=status,
                level=level,
                message=f"Time base continuity validation {'failed' if validation_errors else 'passed'}",
                details={
                    'tle_time_validation': tle_time_result,
                    'continuity_validation': continuity_result,
                    'sync_validation': sync_result
                },
                errors=validation_errors,
                warnings=validation_warnings,
                metadata={'validation_type': 'time_base_continuity'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Time base validation error: {str(e)}",
                details={'exception': str(e)},
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                metadata={'validation_type': 'time_base_continuity'}
            )
    
    def _validate_tle_epoch_usage(self, data: Dict) -> Dict[str, List[str]]:
        """驗證TLE epoch時間使用"""
        errors = []
        warnings = []
        
        # 檢查是否正確使用TLE epoch作為計算基準
        if 'calculation_metadata' in data:
            metadata = data['calculation_metadata']
            
            if 'time_base_source' in metadata:
                time_source = metadata['time_base_source']
                if time_source != 'tle_epoch':
                    errors.append(f"Incorrect time base source: {time_source} (should be 'tle_epoch')")
            else:
                warnings.append("Time base source not documented in metadata")
            
            # 檢查時間基準與當前時間的差異
            if 'calculation_time' in metadata and 'tle_epoch_time' in metadata:
                calc_time = metadata['calculation_time']
                tle_time = metadata['tle_epoch_time']
                
                try:
                    calc_dt = datetime.fromisoformat(calc_time.replace('Z', '+00:00'))
                    tle_dt = datetime.fromisoformat(tle_time.replace('Z', '+00:00'))
                    time_diff = abs((calc_dt - tle_dt).total_seconds())
                    
                    # 警告：時間差超過3天
                    if time_diff > 3 * 24 * 3600:
                        warnings.append(f"Large time difference between calculation and TLE epoch: {time_diff/86400:.1f} days")
                    
                except Exception as e:
                    errors.append(f"Time format parsing error: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_time_series_continuity(self, data: Dict) -> Dict[str, List[str]]:
        """驗證時間序列連續性"""
        errors = []
        warnings = []
        
        # 檢查時間戳序列
        if 'time_series' in data:
            time_series = data['time_series']
            if len(time_series) < 2:
                warnings.append("Insufficient time series data for continuity check")
                return {'errors': errors, 'warnings': warnings}
            
            # 檢查時間戳排序
            timestamps = [entry.get('timestamp') for entry in time_series]
            sorted_timestamps = sorted(timestamps)
            
            if timestamps != sorted_timestamps:
                errors.append("Time series not in chronological order")
            
            # 檢查時間間隔一致性
            try:
                dts = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
                intervals = [(dts[i+1] - dts[i]).total_seconds() for i in range(len(dts)-1)]
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    for i, interval in enumerate(intervals):
                        deviation = abs(interval - avg_interval) / avg_interval
                        if deviation > 0.1:  # 10% 容差
                            warnings.append(f"Time interval deviation at index {i}: {deviation:.2%}")
            
            except Exception as e:
                errors.append(f"Time interval analysis error: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_time_synchronization(self, data: Dict) -> Dict[str, List[str]]:
        """驗證時間同步"""
        errors = []
        warnings = []
        
        # 檢查時區資訊
        if 'time_metadata' in data:
            time_metadata = data['time_metadata']
            
            if 'timezone' in time_metadata:
                timezone_info = time_metadata['timezone']
                if timezone_info != 'UTC':
                    warnings.append(f"Non-UTC timezone used: {timezone_info}")
            
            # 檢查NTP同步狀態
            if 'ntp_sync_status' in time_metadata:
                ntp_status = time_metadata['ntp_sync_status']
                if not ntp_status:
                    errors.append("NTP synchronization not verified")
        
        return {'errors': errors, 'warnings': warnings}


class ZeroValueDetector(BaseValidator):
    """零值檢測專用類別"""
    
    def __init__(self, config: AcademicStandardsConfig = None):
        self.config = config or get_academic_config()
        self.zero_tolerance = self.config.get_grade_a_requirements()['eci_coordinates']['zero_tolerance_threshold']
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """零值檢測驗證"""
        try:
            validation_errors = []
            validation_warnings = []
            
            # ECI座標零值檢測
            eci_result = self._detect_eci_zero_values(data.get('eci_coordinates', []))
            validation_errors.extend(eci_result.get('errors', []))
            validation_warnings.extend(eci_result.get('warnings', []))
            
            # 其他重要數值零值檢測
            general_result = self._detect_general_zero_values(data)
            validation_errors.extend(general_result.get('errors', []))
            validation_warnings.extend(general_result.get('warnings', []))
            
            status = ValidationStatus.FAILED if validation_errors else ValidationStatus.PASSED
            level = ValidationLevel.BLOCKER if validation_errors else ValidationLevel.INFO
            
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=status,
                level=level,
                message=f"Zero value detection {'failed' if validation_errors else 'passed'}",
                details={
                    'eci_zero_detection': eci_result,
                    'general_zero_detection': general_result
                },
                errors=validation_errors,
                warnings=validation_warnings,
                metadata={'validation_type': 'zero_value_detection'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Zero value detection error: {str(e)}",
                details={'exception': str(e)},
                errors=[f"Detection error: {str(e)}"],
                warnings=[],
                metadata={'validation_type': 'zero_value_detection'}
            )
    
    def _detect_eci_zero_values(self, eci_coordinates: List[Dict]) -> Dict[str, List[str]]:
        """檢測ECI座標零值"""
        errors = []
        warnings = []
        
        if not eci_coordinates:
            errors.append("No ECI coordinates provided for zero value detection")
            return {'errors': errors, 'warnings': warnings}
        
        total_coords = len(eci_coordinates)
        zero_coords = 0
        zero_details = []
        
        for i, coord in enumerate(eci_coordinates):
            x = coord.get('x', 0)
            y = coord.get('y', 0)
            z = coord.get('z', 0)
            
            if x == 0 and y == 0 and z == 0:
                zero_coords += 1
                zero_details.append({
                    'index': i,
                    'satellite_id': coord.get('satellite_id', 'unknown'),
                    'timestamp': coord.get('timestamp', 'unknown')
                })
        
        zero_percentage = (zero_coords / total_coords) * 100
        threshold_percentage = self.zero_tolerance * 100
        
        if zero_percentage > threshold_percentage:
            errors.append(
                f"ECI coordinate zero values exceed threshold: {zero_percentage:.2f}% > {threshold_percentage:.2f}%"
            )
            errors.append(f"Zero coordinates found: {zero_coords} out of {total_coords}")
            
            # 詳細違規資訊
            for detail in zero_details[:5]:  # 只報告前5個
                errors.append(f"Zero ECI at index {detail['index']}, satellite: {detail['satellite_id']}")
        
        elif zero_coords > 0:
            warnings.append(f"Found {zero_coords} zero ECI coordinates ({zero_percentage:.2f}%)")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _detect_general_zero_values(self, data: Dict) -> Dict[str, List[str]]:
        """檢測一般重要數值的零值"""
        errors = []
        warnings = []
        
        # 檢測重要的非零欄位
        critical_nonzero_fields = [
            ('distance', '距離'),
            ('elevation', '仰角'),
            ('signal_strength', '信號強度'),
            ('frequency', '頻率'),
            ('velocity', '速度')
        ]
        
        for field, description in critical_nonzero_fields:
            if field in data:
                field_data = data[field]
                if isinstance(field_data, list):
                    zero_count = sum(1 for value in field_data if value == 0)
                    if zero_count > 0:
                        warnings.append(f"Found {zero_count} zero values in {description} ({field})")
                elif field_data == 0:
                    warnings.append(f"Zero value detected in {description} ({field})")
        
        return {'errors': errors, 'warnings': warnings}