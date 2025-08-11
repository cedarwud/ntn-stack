"""
精度驗證器 - 與 STK 對比驗證和歷史事件重現

功能：
1. 與 STK 商業軟體對比驗證（目標: ±100m 精度）
2. 已知歷史切換事件重現驗證
3. 統計特性一致性檢查
4. 物理一致性驗證

符合 d2.md 精度驗證要求
"""

import logging
import math
import statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from .sgp4_calculator import SGP4Calculator, OrbitPosition
from .constellation_manager import ConstellationManager
from .distance_calculator import DistanceCalculator, Position

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """驗證結果"""
    test_name: str
    passed: bool
    accuracy_error: float  # 精度誤差（米）
    statistical_score: float  # 統計評分 (0-1)
    details: Dict[str, Any]
    timestamp: datetime

@dataclass
class STKComparisonData:
    """STK 對比數據"""
    timestamp: str
    stk_latitude: float
    stk_longitude: float
    stk_altitude: float
    our_latitude: float
    our_longitude: float
    our_altitude: float
    position_error: float  # 位置誤差（米）

class PrecisionValidator:
    """精度驗證器"""
    
    def __init__(self):
        self.sgp4_calculator = SGP4Calculator()
        self.constellation_manager = ConstellationManager()
        self.distance_calculator = DistanceCalculator()
        
        # 驗證歷史
        self._validation_history: List[ValidationResult] = []
        
        # STK 標準測試數據（模擬）
        self._stk_reference_data = self._load_stk_reference_data()
        
        logger.info("精度驗證器初始化完成")
    
    def _load_stk_reference_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """載入 STK 參考數據（模擬數據）"""
        # 這裡使用模擬的 STK 數據進行驗證
        # 實際應用中應該從 STK 軟體導出真實數據
        return {
            'starlink_test_satellite': [
                {
                    'timestamp': '2024-01-01T00:00:00Z',
                    'latitude': 25.0478,
                    'longitude': 121.5319,
                    'altitude': 547.2,
                    'velocity': [7.5, 0.2, -0.1]
                },
                {
                    'timestamp': '2024-01-01T01:30:00Z',
                    'latitude': 35.2, 
                    'longitude': 139.7,
                    'altitude': 548.1,
                    'velocity': [7.4, 0.3, 0.1]
                }
            ]
        }
    
    async def validate_stk_comparison(
        self,
        satellite_name: str,
        test_duration_hours: int = 3
    ) -> ValidationResult:
        """
        與 STK 軟體對比驗證
        
        Args:
            satellite_name: 衛星名稱
            test_duration_hours: 測試持續時間（小時）
            
        Returns:
            驗證結果
        """
        try:
            logger.info(f"開始 STK 對比驗證: {satellite_name}")
            
            # 獲取參考數據
            if satellite_name not in self._stk_reference_data:
                return ValidationResult(
                    test_name=f"STK_Comparison_{satellite_name}",
                    passed=False,
                    accuracy_error=float('inf'),
                    statistical_score=0.0,
                    details={'error': 'No STK reference data available'},
                    timestamp=datetime.now(timezone.utc)
                )
            
            stk_data = self._stk_reference_data[satellite_name]
            comparison_results = []
            
            # 獲取測試衛星
            satellites = await self.constellation_manager.get_constellation_satellites('starlink')
            test_satellite = None
            
            for sat in satellites:
                if satellite_name.lower() in sat.tle_data.satellite_name.lower():
                    test_satellite = sat
                    break
            
            if not test_satellite:
                return ValidationResult(
                    test_name=f"STK_Comparison_{satellite_name}",
                    passed=False,
                    accuracy_error=float('inf'),
                    statistical_score=0.0,
                    details={'error': 'Test satellite not found'},
                    timestamp=datetime.now(timezone.utc)
                )
            
            # 對比計算
            for stk_point in stk_data:
                timestamp = datetime.fromisoformat(stk_point['timestamp'].replace('Z', '+00:00'))
                
                # 使用我們的算法計算
                our_position = self.sgp4_calculator.propagate_orbit(
                    test_satellite.tle_data, timestamp
                )
                
                if our_position:
                    # 計算位置誤差
                    position_error = self._calculate_position_error(
                        (stk_point['latitude'], stk_point['longitude'], stk_point['altitude']),
                        (our_position.latitude, our_position.longitude, our_position.altitude)
                    )
                    
                    comparison_results.append(STKComparisonData(
                        timestamp=stk_point['timestamp'],
                        stk_latitude=stk_point['latitude'],
                        stk_longitude=stk_point['longitude'],
                        stk_altitude=stk_point['altitude'],
                        our_latitude=our_position.latitude,
                        our_longitude=our_position.longitude,
                        our_altitude=our_position.altitude,
                        position_error=position_error
                    ))
            
            # 計算統計指標
            if comparison_results:
                errors = [result.position_error for result in comparison_results]
                mean_error = statistics.mean(errors)
                max_error = max(errors)
                rms_error = math.sqrt(statistics.mean([e**2 for e in errors]))
                
                # 驗證通過標準：平均誤差 < 100m，最大誤差 < 500m
                passed = mean_error < 100 and max_error < 500
                statistical_score = max(0, 1 - mean_error / 100)
                
                result = ValidationResult(
                    test_name=f"STK_Comparison_{satellite_name}",
                    passed=passed,
                    accuracy_error=mean_error,
                    statistical_score=statistical_score,
                    details={
                        'mean_error_m': mean_error,
                        'max_error_m': max_error,
                        'rms_error_m': rms_error,
                        'comparison_points': len(comparison_results),
                        'error_distribution': {
                            'std_dev': statistics.stdev(errors) if len(errors) > 1 else 0,
                            'percentile_95': np.percentile(errors, 95),
                            'percentile_99': np.percentile(errors, 99)
                        }
                    },
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                result = ValidationResult(
                    test_name=f"STK_Comparison_{satellite_name}",
                    passed=False,
                    accuracy_error=float('inf'),
                    statistical_score=0.0,
                    details={'error': 'No valid comparison points'},
                    timestamp=datetime.now(timezone.utc)
                )
            
            self._validation_history.append(result)
            logger.info(f"STK 對比驗證完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"STK 對比驗證失敗: {e}")
            return ValidationResult(
                test_name=f"STK_Comparison_{satellite_name}",
                passed=False,
                accuracy_error=float('inf'),
                statistical_score=0.0,
                details={'error': str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def validate_historical_events(self) -> ValidationResult:
        """驗證已知歷史切換事件"""
        try:
            logger.info("開始歷史事件重現驗證")
            
            # 模擬已知的歷史切換事件
            historical_events = [
                {
                    'event_time': '2024-01-01T12:00:00Z',
                    'location': {'latitude': 25.0478, 'longitude': 121.5319, 'altitude': 0.1},
                    'expected_handover': True,
                    'expected_satellites': ['STARLINK-30132', 'STARLINK-30133']
                }
            ]
            
            successful_reproductions = 0
            total_events = len(historical_events)
            
            for event in historical_events:
                event_time = datetime.fromisoformat(event['event_time'].replace('Z', '+00:00'))
                observer_pos = Position(**event['location'])
                
                # 獲取該時間點的可見衛星
                visible_satellites = await self.constellation_manager.get_visible_satellites(
                    observer_pos, event_time
                )
                
                # 檢查是否能重現預期的切換事件
                visible_names = [sat.tle_data.satellite_name for sat in visible_satellites]
                expected_found = any(
                    expected in visible_names 
                    for expected in event['expected_satellites']
                )
                
                if expected_found:
                    successful_reproductions += 1
            
            reproduction_rate = successful_reproductions / total_events if total_events > 0 else 0
            passed = reproduction_rate >= 0.8  # 80% 成功率
            
            result = ValidationResult(
                test_name="Historical_Events_Reproduction",
                passed=passed,
                accuracy_error=0.0,  # 不適用於事件重現
                statistical_score=reproduction_rate,
                details={
                    'total_events': total_events,
                    'successful_reproductions': successful_reproductions,
                    'reproduction_rate': reproduction_rate,
                    'events_tested': historical_events
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            self._validation_history.append(result)
            logger.info(f"歷史事件重現驗證完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"歷史事件重現驗證失敗: {e}")
            return ValidationResult(
                test_name="Historical_Events_Reproduction",
                passed=False,
                accuracy_error=float('inf'),
                statistical_score=0.0,
                details={'error': str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def validate_statistical_consistency(self) -> ValidationResult:
        """驗證統計特性一致性"""
        try:
            logger.info("開始統計特性一致性驗證")
            
            # 測試參數
            observer_pos = Position(latitude=25.0478, longitude=121.5319, altitude=0.1)
            test_duration = timedelta(hours=24)  # 24小時測試
            start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            
            # 收集統計數據
            handover_intervals = []
            satellite_counts = []
            elevation_angles = []
            
            current_time = start_time
            end_time = start_time + test_duration
            
            while current_time < end_time:
                visible_satellites = await self.constellation_manager.get_visible_satellites(
                    observer_pos, current_time
                )
                
                satellite_counts.append(len(visible_satellites))
                
                for sat in visible_satellites:
                    elevation_angles.append(sat.elevation_angle)
                
                current_time += timedelta(minutes=30)  # 30分鐘間隔
            
            # 統計分析
            if satellite_counts and elevation_angles:
                avg_satellite_count = statistics.mean(satellite_counts)
                avg_elevation = statistics.mean(elevation_angles)
                elevation_std = statistics.stdev(elevation_angles) if len(elevation_angles) > 1 else 0
                
                # 預期統計特性（基於 LEO 星座理論值）
                expected_avg_satellites = 8.0  # Starlink 預期平均可見衛星數
                expected_avg_elevation = 45.0  # 預期平均仰角
                
                satellite_count_error = abs(avg_satellite_count - expected_avg_satellites) / expected_avg_satellites
                elevation_error = abs(avg_elevation - expected_avg_elevation) / expected_avg_elevation
                
                # 統計一致性評分
                consistency_score = max(0, 1 - (satellite_count_error + elevation_error) / 2)
                passed = consistency_score >= 0.7  # 70% 一致性
                
                result = ValidationResult(
                    test_name="Statistical_Consistency",
                    passed=passed,
                    accuracy_error=0.0,  # 不適用於統計驗證
                    statistical_score=consistency_score,
                    details={
                        'avg_satellite_count': avg_satellite_count,
                        'expected_satellite_count': expected_avg_satellites,
                        'avg_elevation_angle': avg_elevation,
                        'expected_elevation': expected_avg_elevation,
                        'elevation_std_dev': elevation_std,
                        'satellite_count_error': satellite_count_error,
                        'elevation_error': elevation_error,
                        'test_duration_hours': 24,
                        'sample_points': len(satellite_counts)
                    },
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                result = ValidationResult(
                    test_name="Statistical_Consistency",
                    passed=False,
                    accuracy_error=float('inf'),
                    statistical_score=0.0,
                    details={'error': 'No statistical data collected'},
                    timestamp=datetime.now(timezone.utc)
                )
            
            self._validation_history.append(result)
            logger.info(f"統計特性一致性驗證完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"統計特性一致性驗證失敗: {e}")
            return ValidationResult(
                test_name="Statistical_Consistency",
                passed=False,
                accuracy_error=float('inf'),
                statistical_score=0.0,
                details={'error': str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    def _calculate_position_error(
        self,
        stk_position: Tuple[float, float, float],
        our_position: Tuple[float, float, float]
    ) -> float:
        """計算位置誤差（米）"""
        stk_pos = Position(
            latitude=stk_position[0],
            longitude=stk_position[1], 
            altitude=stk_position[2]
        )
        our_pos = Position(
            latitude=our_position[0],
            longitude=our_position[1],
            altitude=our_position[2]
        )
        
        # 使用距離計算器計算 3D 距離
        distance_result = self.distance_calculator.calculate_3d_distance(stk_pos, our_pos)
        return distance_result.distance * 1000  # 轉換為米
    
    async def run_comprehensive_validation(self) -> Dict[str, ValidationResult]:
        """運行綜合驗證"""
        logger.info("開始綜合精度驗證")
        
        results = {}
        
        # STK 對比驗證
        stk_result = await self.validate_stk_comparison('starlink_test_satellite')
        results['stk_comparison'] = stk_result
        
        # 歷史事件重現驗證
        historical_result = await self.validate_historical_events()
        results['historical_events'] = historical_result
        
        # 統計特性一致性驗證
        statistical_result = await self.validate_statistical_consistency()
        results['statistical_consistency'] = statistical_result
        
        # 綜合評分
        all_passed = all(result.passed for result in results.values())
        avg_score = statistics.mean([result.statistical_score for result in results.values()])
        
        logger.info(f"綜合精度驗證完成: 通過率 {sum(r.passed for r in results.values())}/{len(results)}, 平均評分 {avg_score:.3f}")
        
        return results
    
    def get_validation_history(self) -> List[ValidationResult]:
        """獲取驗證歷史"""
        return self._validation_history.copy()
