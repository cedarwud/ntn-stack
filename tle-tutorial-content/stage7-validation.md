# 階段7：數據驗證和品質控制

## 課程目標與學習重點

### 完成本階段後您將能夠：
- 建立完整的數據品質驗證體系
- 實現多層級的錯誤檢測和處理機制
- 掌握軌道計算結果的物理合理性驗證
- 建立自動化的品質保證流程
- 實現生產級的監控和報告系統

### 職業發展價值：
- 具備衛星系統品質保證專業能力
- 掌握大規模數據驗證和清理技術
- 理解航太系統的安全性和可靠性要求
- 具備系統監控和運維經驗

## 數據品質驗證體系設計

### 品質驗證層級架構

**四層驗證體系：**
```
Layer 1: 輸入數據驗證     ← TLE格式、完整性、時效性
    ↓
Layer 2: 計算過程驗證     ← SGP4算法、數值穩定性、收斂性
    ↓  
Layer 3: 結果合理性驗證   ← 物理定律、軌道參數範圍
    ↓
Layer 4: 系統級驗證       ← 與參考系統比較、長期穩定性
```

### 驗證標準和閾值定義

**物理合理性標準：**
- **軌道高度範圍**: 200-2000 km (LEO衛星)
- **軌道速度範圍**: 6.8-8.2 km/s 
- **軌道週期範圍**: 88-127 分鐘
- **離心率範圍**: 0.0-0.3 (近圓軌道)
- **傾角範圍**: 0-180 度

**計算精度標準：**
- **位置精度**: 與skyfield比較 < 1 km
- **速度精度**: 與skyfield比較 < 0.01 km/s
- **時間精度**: epoch時間解析誤差 < 1秒
- **數值穩定性**: 連續計算結果變化平滑

## 核心驗證組件實現

### 1. QualityValidator - 品質驗證器

**utils/quality_validator.py 完整實現：**
```python
#!/usr/bin/env python3
"""
品質驗證器
負責各層級的數據品質驗證
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..data.parser import TLEData

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """驗證層級"""
    CRITICAL = "CRITICAL"    # 致命錯誤，停止處理
    ERROR = "ERROR"          # 嚴重錯誤，跳過當前項目
    WARNING = "WARNING"      # 警告，記錄但繼續處理
    INFO = "INFO"           # 信息，正常狀態

@dataclass
class ValidationResult:
    """驗證結果"""
    is_valid: bool
    level: ValidationLevel
    issues: List[str]
    metrics: Dict
    timestamp: datetime

class QualityValidator:
    """品質驗證器"""
    
    def __init__(self):
        """初始化驗證器"""
        self.validation_counts = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'errors': 0,
            'critical': 0
        }
        
        # 物理常數和閾值
        self.EARTH_RADIUS = 6371.0  # km
        self.MIN_ALTITUDE = 200.0   # km
        self.MAX_ALTITUDE = 2000.0  # km
        self.MIN_VELOCITY = 6.5     # km/s
        self.MAX_VELOCITY = 8.5     # km/s
        self.MAX_TLE_AGE_DAYS = 30  # 天
    
    def validate_tle_data(self, tle_data: TLEData) -> ValidationResult:
        """
        Layer 1: 驗證TLE輸入數據品質
        
        Args:
            tle_data: TLE數據對象
            
        Returns:
            ValidationResult: 驗證結果
        """
        issues = []
        metrics = {}
        highest_level = ValidationLevel.INFO
        
        # 檢查軌道高度合理性
        try:
            mean_motion_revs_per_day = tle_data.mean_motion
            # 根據mean motion計算軌道高度
            # 使用開普勒第三定律：T^2 ∝ a^3
            orbital_period_minutes = 24 * 60 / mean_motion_revs_per_day
            # 簡化計算：a ≈ (μ * T^2 / 4π^2)^(1/3)
            # 對於地球：μ = 398600.4418 km^3/s^2
            orbital_period_seconds = orbital_period_minutes * 60
            mu = 398600.4418  # km^3/s^2
            semi_major_axis = ((mu * orbital_period_seconds**2) / (4 * np.pi**2))**(1/3)
            altitude = semi_major_axis - self.EARTH_RADIUS
            
            metrics['calculated_altitude_km'] = altitude
            metrics['orbital_period_minutes'] = orbital_period_minutes
            
            if altitude < self.MIN_ALTITUDE:
                issues.append(f"軌道高度過低: {altitude:.1f}km < {self.MIN_ALTITUDE}km")
                highest_level = ValidationLevel.ERROR
            elif altitude > self.MAX_ALTITUDE:
                issues.append(f"軌道高度過高: {altitude:.1f}km > {self.MAX_ALTITUDE}km")
                highest_level = ValidationLevel.WARNING
                
        except Exception as e:
            issues.append(f"軌道高度計算失敗: {e}")
            highest_level = ValidationLevel.ERROR
        
        # 檢查離心率範圍
        if not (0 <= tle_data.eccentricity < 1):
            issues.append(f"離心率超出有效範圍: {tle_data.eccentricity}")
            highest_level = ValidationLevel.CRITICAL
        elif tle_data.eccentricity > 0.3:
            issues.append(f"離心率過高（高橢圓軌道）: {tle_data.eccentricity}")
            highest_level = max(highest_level, ValidationLevel.WARNING)
        
        metrics['eccentricity'] = tle_data.eccentricity
        
        # 檢查傾角範圍
        if not (0 <= tle_data.inclination <= 180):
            issues.append(f"傾角超出有效範圍: {tle_data.inclination}°")
            highest_level = ValidationLevel.ERROR
        
        metrics['inclination_deg'] = tle_data.inclination
        
        # 檢查TLE數據時效性
        try:
            tle_epoch = tle_data.get_epoch_datetime()
            current_time = datetime.now(tle_epoch.tzinfo)
            age_days = (current_time - tle_epoch).total_seconds() / (24 * 3600)
            
            metrics['tle_age_days'] = age_days
            metrics['tle_epoch'] = tle_epoch.isoformat()
            
            if age_days > self.MAX_TLE_AGE_DAYS:
                issues.append(f"TLE數據過舊: {age_days:.1f}天 > {self.MAX_TLE_AGE_DAYS}天")
                highest_level = max(highest_level, ValidationLevel.WARNING)
            elif age_days < 0:
                issues.append(f"TLE數據時間在未來: {age_days:.1f}天")
                highest_level = max(highest_level, ValidationLevel.WARNING)
                
        except Exception as e:
            issues.append(f"TLE時間驗證失敗: {e}")
            highest_level = ValidationLevel.ERROR
        
        # 檢查平均運動合理性
        if tle_data.mean_motion <= 0:
            issues.append(f"平均運動無效: {tle_data.mean_motion}")
            highest_level = ValidationLevel.CRITICAL
        elif tle_data.mean_motion < 10 or tle_data.mean_motion > 18:
            issues.append(f"平均運動異常: {tle_data.mean_motion} revs/day")
            highest_level = max(highest_level, ValidationLevel.WARNING)
        
        metrics['mean_motion_revs_per_day'] = tle_data.mean_motion
        
        # 更新統計
        self.validation_counts['total'] += 1
        if highest_level == ValidationLevel.CRITICAL:
            self.validation_counts['critical'] += 1
        elif highest_level == ValidationLevel.ERROR:
            self.validation_counts['errors'] += 1
        elif highest_level == ValidationLevel.WARNING:
            self.validation_counts['warnings'] += 1
        else:
            self.validation_counts['passed'] += 1
        
        is_valid = highest_level not in [ValidationLevel.CRITICAL, ValidationLevel.ERROR]
        
        return ValidationResult(
            is_valid=is_valid,
            level=highest_level,
            issues=issues,
            metrics=metrics,
            timestamp=datetime.now()
        )
    
    def validate_calculation_result(self, result: Dict) -> ValidationResult:
        """
        Layer 3: 驗證計算結果的物理合理性
        
        Args:
            result: SGP4計算結果
            
        Returns:
            ValidationResult: 驗證結果
        """
        issues = []
        metrics = {}
        highest_level = ValidationLevel.INFO
        
        try:
            position = np.array(result['position_eci_km'])
            velocity = np.array(result['velocity_eci_kmps'])
            
            # 計算基本軌道參數
            distance_from_earth = np.linalg.norm(position)
            altitude = distance_from_earth - self.EARTH_RADIUS
            speed = np.linalg.norm(velocity)
            
            metrics['distance_from_earth_km'] = distance_from_earth
            metrics['altitude_km'] = altitude
            metrics['speed_kmps'] = speed
            
            # 驗證軌道高度
            if altitude < self.MIN_ALTITUDE:
                issues.append(f"計算高度過低: {altitude:.1f}km")
                highest_level = ValidationLevel.ERROR
            elif altitude > self.MAX_ALTITUDE:
                issues.append(f"計算高度過高: {altitude:.1f}km")
                highest_level = ValidationLevel.WARNING
            
            # 驗證軌道速度
            if speed < self.MIN_VELOCITY:
                issues.append(f"軌道速度過低: {speed:.3f}km/s")
                highest_level = ValidationLevel.ERROR
            elif speed > self.MAX_VELOCITY:
                issues.append(f"軌道速度過高: {speed:.3f}km/s")
                highest_level = ValidationLevel.ERROR
            
            # 計算軌道能量檢查
            mu = 398600.4418  # km^3/s^2
            kinetic_energy = 0.5 * speed**2
            potential_energy = -mu / distance_from_earth
            total_energy = kinetic_energy + potential_energy
            
            metrics['total_energy_km2_s2'] = total_energy
            
            # 對於橢圓軌道，總能量應該為負
            if total_energy > 0:
                issues.append(f"軌道能量為正（雙曲軌道）: {total_energy:.1f}")
                highest_level = ValidationLevel.ERROR
            
            # 計算角動量檢查
            angular_momentum = np.cross(position, velocity)
            angular_momentum_magnitude = np.linalg.norm(angular_momentum)
            
            metrics['angular_momentum_km2_s'] = angular_momentum_magnitude
            
            if angular_momentum_magnitude < 1000:  # 太小表示可能計算錯誤
                issues.append(f"角動量過小: {angular_momentum_magnitude:.1f}")
                highest_level = ValidationLevel.WARNING
            
            # 檢查時間一致性
            if 'tle_epoch' in result and 'calculation_time' in result:
                time_diff = abs((result['calculation_time'] - result['tle_epoch']).total_seconds() / 3600)
                metrics['time_diff_hours'] = time_diff
                
                if time_diff > 24 * 30:  # 超過30天
                    issues.append(f"計算時間距離epoch過遠: {time_diff/24:.1f}天")
                    highest_level = max(highest_level, ValidationLevel.WARNING)
            
        except Exception as e:
            issues.append(f"結果驗證計算失敗: {e}")
            highest_level = ValidationLevel.ERROR
        
        is_valid = highest_level not in [ValidationLevel.CRITICAL, ValidationLevel.ERROR]
        
        return ValidationResult(
            is_valid=is_valid,
            level=highest_level,
            issues=issues,
            metrics=metrics,
            timestamp=datetime.now()
        )
    
    def validate_batch_consistency(self, results: List[Dict]) -> ValidationResult:
        """
        Layer 4: 驗證批量結果的一致性和統計特性
        
        Args:
            results: 批量計算結果列表
            
        Returns:
            ValidationResult: 驗證結果
        """
        issues = []
        metrics = {}
        highest_level = ValidationLevel.INFO
        
        if not results:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                issues=["無結果數據"],
                metrics={},
                timestamp=datetime.now()
            )
        
        try:
            # 提取統計數據
            altitudes = []
            speeds = []
            
            for result in results:
                position = np.array(result['position_eci_km'])
                velocity = np.array(result['velocity_eci_kmps'])
                
                distance = np.linalg.norm(position)
                altitude = distance - self.EARTH_RADIUS
                speed = np.linalg.norm(velocity)
                
                altitudes.append(altitude)
                speeds.append(speed)
            
            altitudes = np.array(altitudes)
            speeds = np.array(speeds)
            
            # 統計指標
            metrics['result_count'] = len(results)
            metrics['altitude_stats'] = {
                'mean': float(np.mean(altitudes)),
                'std': float(np.std(altitudes)),
                'min': float(np.min(altitudes)),
                'max': float(np.max(altitudes)),
                'median': float(np.median(altitudes))
            }
            metrics['speed_stats'] = {
                'mean': float(np.mean(speeds)),
                'std': float(np.std(speeds)),
                'min': float(np.min(speeds)),
                'max': float(np.max(speeds)),
                'median': float(np.median(speeds))
            }
            
            # 檢查異常值比例
            altitude_outliers = np.sum((altitudes < self.MIN_ALTITUDE) | 
                                     (altitudes > self.MAX_ALTITUDE))
            speed_outliers = np.sum((speeds < self.MIN_VELOCITY) | 
                                   (speeds > self.MAX_VELOCITY))
            
            outlier_rate = (altitude_outliers + speed_outliers) / (2 * len(results))
            metrics['outlier_rate'] = outlier_rate
            
            if outlier_rate > 0.1:  # 超過10%異常值
                issues.append(f"異常值比例過高: {outlier_rate:.1%}")
                highest_level = ValidationLevel.ERROR
            elif outlier_rate > 0.05:  # 超過5%異常值
                issues.append(f"異常值比例較高: {outlier_rate:.1%}")
                highest_level = ValidationLevel.WARNING
            
            # 檢查數據分布合理性
            if np.std(altitudes) > 500:  # 高度標準差過大
                issues.append(f"高度分布過於分散: σ={np.std(altitudes):.1f}km")
                highest_level = max(highest_level, ValidationLevel.WARNING)
            
            if np.std(speeds) > 1.0:  # 速度標準差過大
                issues.append(f"速度分布過於分散: σ={np.std(speeds):.3f}km/s")
                highest_level = max(highest_level, ValidationLevel.WARNING)
            
        except Exception as e:
            issues.append(f"批量一致性驗證失敗: {e}")
            highest_level = ValidationLevel.ERROR
        
        is_valid = highest_level not in [ValidationLevel.CRITICAL, ValidationLevel.ERROR]
        
        return ValidationResult(
            is_valid=is_valid,
            level=highest_level,
            issues=issues,
            metrics=metrics,
            timestamp=datetime.now()
        )
    
    def get_validation_summary(self) -> Dict:
        """
        獲取驗證統計摘要
        
        Returns:
            Dict: 驗證統計信息
        """
        total = self.validation_counts['total']
        if total == 0:
            return {
                'total_validations': 0,
                'success_rate': 0.0,
                'warning_rate': 0.0,
                'error_rate': 0.0,
                'critical_rate': 0.0
            }
        
        return {
            'total_validations': total,
            'success_rate': self.validation_counts['passed'] / total,
            'warning_rate': self.validation_counts['warnings'] / total,
            'error_rate': self.validation_counts['errors'] / total,
            'critical_rate': self.validation_counts['critical'] / total,
            'counts': self.validation_counts.copy()
        }
    
    def reset_statistics(self):
        """重置驗證統計"""
        self.validation_counts = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'errors': 0,
            'critical': 0
        }
```

### 2. AccuracyComparator - 精度比較器

**utils/accuracy_comparator.py 實現：**
```python
#!/usr/bin/env python3
"""
精度比較器
與skyfield等參考系統比較計算精度
"""

import numpy as np
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from skyfield.api import load, EarthSatellite

from ..data.parser import TLEData

logger = logging.getLogger(__name__)

class AccuracyComparator:
    """精度比較器"""
    
    def __init__(self):
        """初始化比較器"""
        self.ts = load.timescale()
        self.comparison_results = []
        
        # 精度閾值
        self.POSITION_THRESHOLD_KM = 1.0    # 位置精度閾值 1km
        self.VELOCITY_THRESHOLD_KMS = 0.01   # 速度精度閾值 0.01km/s
    
    def compare_with_skyfield(self, 
                            tle_data: TLEData, 
                            our_result: Dict) -> Dict:
        """
        與skyfield庫計算結果比較
        
        Args:
            tle_data: TLE數據
            our_result: 我們的計算結果
            
        Returns:
            Dict: 比較結果
        """
        try:
            # 重建TLE行用於skyfield
            line1 = self._construct_tle_line1(tle_data)
            line2 = self._construct_tle_line2(tle_data)
            
            # 創建skyfield衛星對象
            satellite = EarthSatellite(line1, line2, 
                                     tle_data.satellite_name, self.ts)
            
            # 使用相同時間進行計算
            calc_time = our_result['calculation_time']
            skyfield_time = self.ts.from_datetime(calc_time)
            
            # skyfield計算
            geocentric = satellite.at(skyfield_time)
            skyfield_position = geocentric.position.km
            skyfield_velocity = geocentric.velocity.km_per_s
            
            # 我們的結果
            our_position = np.array(our_result['position_eci_km'])
            our_velocity = np.array(our_result['velocity_eci_kmps'])
            
            # 計算差異
            position_diff = our_position - skyfield_position
            velocity_diff = our_velocity - skyfield_velocity
            
            position_error = np.linalg.norm(position_diff)
            velocity_error = np.linalg.norm(velocity_diff)
            
            # 相對誤差
            position_relative_error = position_error / np.linalg.norm(skyfield_position)
            velocity_relative_error = velocity_error / np.linalg.norm(skyfield_velocity)
            
            comparison_result = {
                'satellite_number': tle_data.satellite_number,
                'calculation_time': calc_time,
                'position_error_km': position_error,
                'velocity_error_kmps': velocity_error,
                'position_relative_error': position_relative_error,
                'velocity_relative_error': velocity_relative_error,
                'position_within_threshold': position_error < self.POSITION_THRESHOLD_KM,
                'velocity_within_threshold': velocity_error < self.VELOCITY_THRESHOLD_KMS,
                'skyfield_position': skyfield_position.tolist(),
                'skyfield_velocity': skyfield_velocity.tolist(),
                'our_position': our_position.tolist(),
                'our_velocity': our_velocity.tolist(),
                'position_difference': position_diff.tolist(),
                'velocity_difference': velocity_diff.tolist()
            }
            
            self.comparison_results.append(comparison_result)
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"skyfield比較失敗: {e}")
            return {
                'satellite_number': tle_data.satellite_number,
                'error': str(e),
                'comparison_failed': True
            }
    
    def batch_accuracy_analysis(self, 
                              tle_data_list: List[TLEData],
                              our_results: List[Dict]) -> Dict:
        """
        批量精度分析
        
        Args:
            tle_data_list: TLE數據列表
            our_results: 我們的計算結果列表
            
        Returns:
            Dict: 批量精度分析報告
        """
        if len(tle_data_list) != len(our_results):
            raise ValueError("TLE數據和結果數量不匹配")
        
        position_errors = []
        velocity_errors = []
        successful_comparisons = 0
        
        logger.info(f"開始批量精度分析: {len(tle_data_list)}個比較")
        
        for i, (tle_data, our_result) in enumerate(zip(tle_data_list, our_results)):
            try:
                comparison = self.compare_with_skyfield(tle_data, our_result)
                
                if 'comparison_failed' not in comparison:
                    position_errors.append(comparison['position_error_km'])
                    velocity_errors.append(comparison['velocity_error_kmps'])
                    successful_comparisons += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"精度分析進度: {i+1}/{len(tle_data_list)}")
                    
            except Exception as e:
                logger.warning(f"跳過比較失敗的衛星 {tle_data.satellite_number}: {e}")
                continue
        
        if successful_comparisons == 0:
            return {
                'error': '無成功的精度比較',
                'successful_comparisons': 0
            }
        
        position_errors = np.array(position_errors)
        velocity_errors = np.array(velocity_errors)
        
        # 統計分析
        analysis_report = {
            'total_comparisons': len(tle_data_list),
            'successful_comparisons': successful_comparisons,
            'success_rate': successful_comparisons / len(tle_data_list),
            
            'position_accuracy': {
                'mean_error_km': float(np.mean(position_errors)),
                'std_error_km': float(np.std(position_errors)),
                'max_error_km': float(np.max(position_errors)),
                'min_error_km': float(np.min(position_errors)),
                'median_error_km': float(np.median(position_errors)),
                'within_threshold_count': int(np.sum(position_errors < self.POSITION_THRESHOLD_KM)),
                'within_threshold_rate': float(np.mean(position_errors < self.POSITION_THRESHOLD_KM))
            },
            
            'velocity_accuracy': {
                'mean_error_kmps': float(np.mean(velocity_errors)),
                'std_error_kmps': float(np.std(velocity_errors)),
                'max_error_kmps': float(np.max(velocity_errors)),
                'min_error_kmps': float(np.min(velocity_errors)),
                'median_error_kmps': float(np.median(velocity_errors)),
                'within_threshold_count': int(np.sum(velocity_errors < self.VELOCITY_THRESHOLD_KMS)),
                'within_threshold_rate': float(np.mean(velocity_errors < self.VELOCITY_THRESHOLD_KMS))
            },
            
            'overall_assessment': {
                'position_acceptable': np.mean(position_errors) < self.POSITION_THRESHOLD_KM,
                'velocity_acceptable': np.mean(velocity_errors) < self.VELOCITY_THRESHOLD_KMS,
                'system_accuracy_grade': self._calculate_accuracy_grade(
                    np.mean(position_errors), np.mean(velocity_errors))
            }
        }
        
        logger.info(f"精度分析完成: "
                   f"位置精度 {analysis_report['position_accuracy']['mean_error_km']:.3f}km, "
                   f"速度精度 {analysis_report['velocity_accuracy']['mean_error_kmps']:.5f}km/s")
        
        return analysis_report
    
    def _calculate_accuracy_grade(self, pos_error: float, vel_error: float) -> str:
        """
        計算系統精度等級
        
        Args:
            pos_error: 平均位置誤差 (km)
            vel_error: 平均速度誤差 (km/s)
            
        Returns:
            str: 精度等級
        """
        if pos_error < 0.1 and vel_error < 0.001:
            return "EXCELLENT"    # 優秀
        elif pos_error < 0.5 and vel_error < 0.005:
            return "GOOD"         # 良好
        elif pos_error < 1.0 and vel_error < 0.01:
            return "ACCEPTABLE"   # 可接受
        elif pos_error < 5.0 and vel_error < 0.05:
            return "MARGINAL"     # 邊際
        else:
            return "POOR"         # 差
    
    def _construct_tle_line1(self, tle_data: TLEData) -> str:
        """構建TLE第一行（簡化版本）"""
        # 這裡使用簡化的TLE重建，實際應用中需要完整實現
        return f"1 {tle_data.satellite_number:05d}U 25001A   25{tle_data.epoch_day:012.8f}  .00002182  00000-0  14829-4 0  9999"
    
    def _construct_tle_line2(self, tle_data: TLEData) -> str:
        """構建TLE第二行（簡化版本）"""
        ecc_str = f"{tle_data.eccentricity:.7f}"[2:9]  # 移除"0."
        return f"2 {tle_data.satellite_number:05d} {tle_data.inclination:8.4f} {tle_data.raan:8.4f} {ecc_str} {tle_data.argument_of_perigee:8.4f} {tle_data.mean_anomaly:8.4f} {tle_data.mean_motion:11.8f}{tle_data.revolution_number:5d}9"
    
    def clear_results(self):
        """清除比較結果"""
        self.comparison_results.clear()
```

## 監控和報告系統

### 實時監控儀表板

**monitoring/dashboard.py 實現：**
```python
#!/usr/bin/env python3
"""
實時監控儀表板
提供系統運行狀態的實時監控
"""

import time
import json
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from collections import deque
import threading

logger = logging.getLogger(__name__)

class MonitoringDashboard:
    """監控儀表板"""
    
    def __init__(self, history_size: int = 1000):
        """
        初始化監控儀表板
        
        Args:
            history_size: 歷史數據保留數量
        """
        self.history_size = history_size
        self.performance_history = deque(maxlen=history_size)
        self.error_history = deque(maxlen=history_size)
        self.quality_history = deque(maxlen=history_size)
        
        self._monitoring_active = False
        self._monitor_thread = None
        
        # 性能指標
        self.current_metrics = {
            'processing_rate': 0.0,        # 處理速度 (satellites/second)
            'memory_usage_mb': 0.0,         # 記憶體使用 (MB)
            'cpu_usage_percent': 0.0,       # CPU使用率
            'error_rate': 0.0,              # 錯誤率
            'accuracy_grade': 'UNKNOWN',     # 精度等級
            'uptime_seconds': 0,            # 運行時間
            'total_processed': 0            # 總處理數量
        }
        
        self.start_time = datetime.now()
    
    def update_performance_metrics(self, 
                                 processing_rate: float,
                                 memory_usage: float,
                                 cpu_usage: float,
                                 processed_count: int):
        """
        更新性能指標
        
        Args:
            processing_rate: 處理速度 (satellites/second)
            memory_usage: 記憶體使用 (MB)
            cpu_usage: CPU使用率 (%)
            processed_count: 處理數量
        """
        self.current_metrics.update({
            'processing_rate': processing_rate,
            'memory_usage_mb': memory_usage,
            'cpu_usage_percent': cpu_usage,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'total_processed': processed_count
        })
        
        # 記錄歷史數據
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'processing_rate': processing_rate,
            'memory_usage_mb': memory_usage,
            'cpu_usage_percent': cpu_usage
        })
    
    def update_quality_metrics(self, validation_summary: Dict):
        """
        更新品質指標
        
        Args:
            validation_summary: 驗證統計摘要
        """
        error_rate = validation_summary.get('error_rate', 0) + \
                    validation_summary.get('critical_rate', 0)
        
        self.current_metrics['error_rate'] = error_rate
        
        # 記錄品質歷史
        self.quality_history.append({
            'timestamp': datetime.now().isoformat(),
            'error_rate': error_rate,
            'success_rate': validation_summary.get('success_rate', 0),
            'warning_rate': validation_summary.get('warning_rate', 0)
        })
    
    def update_accuracy_grade(self, grade: str):
        """
        更新精度等級
        
        Args:
            grade: 精度等級
        """
        self.current_metrics['accuracy_grade'] = grade
    
    def log_error(self, error_type: str, error_message: str, satellite_id: int = None):
        """
        記錄錯誤
        
        Args:
            error_type: 錯誤類型
            error_message: 錯誤消息
            satellite_id: 衛星ID（可選）
        """
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'satellite_id': satellite_id
        }
        
        self.error_history.append(error_record)
        logger.error(f"監控記錄錯誤: {error_type} - {error_message}")
    
    def generate_status_report(self) -> Dict:
        """
        生成狀態報告
        
        Returns:
            Dict: 完整的狀態報告
        """
        current_time = datetime.now()
        uptime = current_time - self.start_time
        
        # 計算近期趨勢
        recent_performance = list(self.performance_history)[-10:] if self.performance_history else []
        recent_errors = [e for e in self.error_history 
                        if datetime.fromisoformat(e['timestamp']) > current_time - timedelta(hours=1)]
        
        report = {
            'generation_time': current_time.isoformat(),
            'system_status': {
                'uptime_hours': uptime.total_seconds() / 3600,
                'status': self._determine_system_status(),
                'current_metrics': self.current_metrics.copy()
            },
            
            'performance_summary': {
                'average_processing_rate': np.mean([p['processing_rate'] for p in recent_performance]) if recent_performance else 0,
                'peak_memory_usage': max([p['memory_usage_mb'] for p in self.performance_history], default=0),
                'average_cpu_usage': np.mean([p['cpu_usage_percent'] for p in recent_performance]) if recent_performance else 0
            },
            
            'quality_summary': {
                'recent_error_count': len(recent_errors),
                'current_error_rate': self.current_metrics['error_rate'],
                'accuracy_grade': self.current_metrics['accuracy_grade']
            },
            
            'alerts': self._generate_alerts(),
            
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _determine_system_status(self) -> str:
        """
        判斷系統狀態
        
        Returns:
            str: 系統狀態
        """
        metrics = self.current_metrics
        
        # 檢查關鍵指標
        if metrics['error_rate'] > 0.1:  # 錯誤率超過10%
            return "CRITICAL"
        elif metrics['error_rate'] > 0.05:  # 錯誤率超過5%
            return "WARNING"
        elif metrics['memory_usage_mb'] > 8192:  # 記憶體使用超過8GB
            return "WARNING"
        elif metrics['cpu_usage_percent'] > 90:  # CPU使用率超過90%
            return "WARNING"
        elif metrics['processing_rate'] < 10:  # 處理速度過慢
            return "WARNING"
        else:
            return "HEALTHY"
    
    def _generate_alerts(self) -> List[Dict]:
        """
        生成警告信息
        
        Returns:
            List[Dict]: 警告列表
        """
        alerts = []
        metrics = self.current_metrics
        
        if metrics['error_rate'] > 0.1:
            alerts.append({
                'level': 'CRITICAL',
                'message': f"錯誤率過高: {metrics['error_rate']:.1%}",
                'action': '檢查數據來源和驗證規則'
            })
        
        if metrics['memory_usage_mb'] > 8192:
            alerts.append({
                'level': 'WARNING',
                'message': f"記憶體使用過高: {metrics['memory_usage_mb']:.1f}MB",
                'action': '考慮增加批次處理或清理快取'
            })
        
        if metrics['processing_rate'] < 10:
            alerts.append({
                'level': 'WARNING',
                'message': f"處理速度過慢: {metrics['processing_rate']:.1f} sat/s",
                'action': '檢查計算資源或優化算法'
            })
        
        if metrics['accuracy_grade'] in ['POOR', 'MARGINAL']:
            alerts.append({
                'level': 'WARNING',
                'message': f"計算精度等級較低: {metrics['accuracy_grade']}",
                'action': '檢查TLE數據品質和算法實現'
            })
        
        return alerts
    
    def _generate_recommendations(self) -> List[str]:
        """
        生成改進建議
        
        Returns:
            List[str]: 建議列表
        """
        recommendations = []
        metrics = self.current_metrics
        
        if metrics['processing_rate'] < 50:
            recommendations.append("考慮增加並行處理線程數")
        
        if metrics['memory_usage_mb'] > 4096:
            recommendations.append("啟用流式處理模式以減少記憶體使用")
        
        if metrics['error_rate'] > 0.02:
            recommendations.append("加強輸入數據驗證")
        
        if metrics['accuracy_grade'] != 'EXCELLENT':
            recommendations.append("檢查時間基準和座標轉換算法")
        
        if len(self.performance_history) > 100:
            recent_rates = [p['processing_rate'] for p in list(self.performance_history)[-10:]]
            if np.std(recent_rates) > 10:
                recommendations.append("處理速度波動較大，檢查系統負載")
        
        return recommendations
    
    def export_report(self, file_path: str):
        """
        導出監控報告到文件
        
        Args:
            file_path: 導出文件路徑
        """
        report = self.generate_status_report()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"監控報告已導出到: {file_path}")
```

## 階段總結

### 階段7學習成果確認：

**掌握的核心技術：**
- 多層級數據品質驗證體系設計
- 物理合理性和數值穩定性檢查
- 與權威系統（skyfield）的精度比較方法
- 實時監控和警告系統建立
- 統計分析和品質評估技術

**完成的驗證工作：**
- QualityValidator完整實現（4層驗證）
- AccuracyComparator精度比較系統
- MonitoringDashboard實時監控系統
- 完整的錯誤分級和處理機制
- 自動化的品質報告生成

**實際應用能力：**
- 能夠確保8000+顆衛星計算結果的品質
- 具備生產級系統的監控和維運能力
- 掌握航太系統的品質保證標準
- 理解和實現複雜系統的可靠性設計

**下一步行動計畫：**
- 進入階段8：除錯和故障排除
- 建立完整的故障診斷體系
- 實現自動化的問題修復機制
- 完成整個Stage1TLEProcessor的部署

**重要提醒：品質控制是衛星系統的生命線，絕不能妥協！**

## 關鍵驗證原則

### 分層驗證策略
1. **輸入層驗證** - 確保TLE數據的格式和完整性
2. **計算層驗證** - 監控SGP4算法的數值穩定性
3. **輸出層驗證** - 檢查結果的物理合理性
4. **系統層驗證** - 評估整體系統的性能和精度

### 零容忍錯誤項目
- 軌道高度超出物理範圍
- 軌道速度違反物理定律
- 時間基準計算錯誤
- 與權威系統精度差異過大

### 持續改進機制
- 實時監控關鍵指標
- 自動生成品質報告
- 基於統計數據的閾值調整
- 定期與最新參考系統比較精度