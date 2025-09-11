"""
軌道計算器 - Stage 1模組化組件

職責：
1. 使用SGP4引擎進行精確軌道計算
2. 生成192點時間序列軌道數據
3. 計算軌道元素和相位信息
4. 提供學術級別的計算精度
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class MockSGP4Engine:
    """開發環境用的模擬SGP4引擎"""
    
    def __init__(self, observer_coordinates):
        self.observer_coordinates = observer_coordinates
        self.version = "mock_v1.0"
    
    def calculate_satellite_orbit(self, satellite_name: str, tle_data: Dict[str, str], 
                                 time_points: int = 192, time_interval_seconds: int = 30) -> Dict[str, Any]:
        """模擬軌道計算"""
        import random
        
        positions = []
        for i in range(time_points):
            # 生成模擬的軌道位置
            timestamp = f"2021-10-02T10:{i//4:02d}:{(i%4)*15:02d}:00Z"
            positions.append({
                "timestamp": timestamp,
                "latitude": random.uniform(-90, 90),
                "longitude": random.uniform(-180, 180),
                "altitude_km": random.uniform(400, 600),
                "velocity_kmps": random.uniform(7.5, 8.0),
                "elevation": random.uniform(0, 90),
                "azimuth": random.uniform(0, 360)
            })
        
        return {
            "positions": positions,
            "orbital_elements": {
                "semi_major_axis": random.uniform(6800, 7000),
                "eccentricity": random.uniform(0.0001, 0.002),
                "inclination": random.uniform(50, 90),
                "argument_of_perigee": random.uniform(0, 360),
                "longitude_of_ascending_node": random.uniform(0, 360),
                "mean_anomaly": random.uniform(0, 360)
            }
        }

class OrbitalCalculator:
    """軌道計算器 - 使用SGP4引擎"""
    
    def __init__(self, observer_coordinates: Tuple[float, float, float] = (24.9441667, 121.3713889, 50)):
        """
        初始化軌道計算器
        
        Args:
            observer_coordinates: 觀測點坐標 (緯度, 經度, 海拔m)，預設為NTPU
        """
        self.logger = logging.getLogger(f"{__name__}.OrbitalCalculator")
        self.observer_coordinates = observer_coordinates
        
        # 初始化SGP4引擎 - 開發環境使用模擬器
        try:
            if Path("/app/src").exists():
                # 容器環境 - 使用真實的SGP4引擎
                import sys
                sys.path.insert(0, '/app/netstack/src')
                sys.path.insert(0, '/app/netstack/src/pipeline/shared')
                from pipeline.shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine
                self.sgp4_engine = SGP4OrbitalEngine(observer_coordinates=observer_coordinates)
            else:
                # 開發環境 - 使用模擬SGP4引擎
                self.sgp4_engine = MockSGP4Engine(observer_coordinates=observer_coordinates)
            
            self.logger.info(f"✅ SGP4引擎初始化成功，觀測點: {observer_coordinates}")
            
        except Exception as e:
            self.logger.error(f"❌ SGP4引擎初始化失敗: {e}")
            raise RuntimeError(f"SGP4引擎初始化失敗: {e}")
        
        # 計算統計
        self.calculation_statistics = {
            "total_satellites": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "total_position_points": 0,
            "calculation_time": 0.0
        }
    
    def calculate_orbits_for_satellites(self, satellites: List[Dict[str, Any]], 
                                       time_points: int = 192,
                                       time_interval_seconds: int = 30) -> Dict[str, Any]:
        """
        為所有衛星計算軌道
        
        Args:
            satellites: 衛星數據列表
            time_points: 時間點數量，預設192點
            time_interval_seconds: 時間間隔（秒），預設30秒
            
        Returns:
            軌道計算結果
        """
        self.logger.info(f"🚀 開始計算 {len(satellites)} 顆衛星的軌道")
        self.logger.info(f"   時間點: {time_points}, 間隔: {time_interval_seconds}秒")
        
        start_time = datetime.now(timezone.utc)
        
        # 重置統計
        self.calculation_statistics["total_satellites"] = len(satellites)
        
        orbital_results = {
            "satellites": {},
            "constellations": {},
            "calculation_metadata": {
                "time_points": time_points,
                "time_interval_seconds": time_interval_seconds,
                "observer_coordinates": self.observer_coordinates,
                "calculation_start_time": start_time.isoformat(),
                "sgp4_engine_version": getattr(self.sgp4_engine, 'version', 'unknown')
            }
        }
        
        # 按星座分組處理
        constellation_groups = self._group_by_constellation(satellites)
        
        for constellation, sat_list in constellation_groups.items():
            self.logger.info(f"📡 處理 {constellation} 星座: {len(sat_list)} 顆衛星")
            
            constellation_results = self._calculate_constellation_orbits(
                sat_list, time_points, time_interval_seconds
            )
            
            orbital_results["constellations"][constellation] = constellation_results
            
            # 合併到總結果中
            for sat_id, sat_data in constellation_results["satellites"].items():
                orbital_results["satellites"][sat_id] = sat_data
        
        # 完成統計
        end_time = datetime.now(timezone.utc)
        calculation_duration = (end_time - start_time).total_seconds()
        
        self.calculation_statistics["calculation_time"] = calculation_duration
        orbital_results["calculation_metadata"]["calculation_end_time"] = end_time.isoformat()
        orbital_results["calculation_metadata"]["total_duration_seconds"] = calculation_duration
        
        # 添加統計信息
        orbital_results["statistics"] = self.calculation_statistics.copy()
        
        self.logger.info(f"✅ 軌道計算完成: {self.calculation_statistics['successful_calculations']} 成功")
        self.logger.info(f"   失敗: {self.calculation_statistics['failed_calculations']}, 耗時: {calculation_duration:.2f}秒")
        
        return orbital_results
    
    def _group_by_constellation(self, satellites: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按星座分組衛星"""
        groups = {}
        
        for sat in satellites:
            constellation = sat.get('constellation', 'unknown')
            if constellation not in groups:
                groups[constellation] = []
            groups[constellation].append(sat)
        
        return groups
    
    def _calculate_constellation_orbits(self, satellites: List[Dict[str, Any]], 
                                      time_points: int, 
                                      time_interval_seconds: int) -> Dict[str, Any]:
        """計算單個星座的軌道"""
        constellation_result = {
            "satellites": {},
            "constellation_statistics": {
                "total_satellites": len(satellites),
                "successful_calculations": 0,
                "failed_calculations": 0
            }
        }
        
        for satellite in satellites:
            try:
                sat_id = satellite.get('norad_id', satellite.get('name', 'unknown'))
                
                # 計算單顆衛星軌道
                orbital_data = self._calculate_single_satellite_orbit(
                    satellite, time_points, time_interval_seconds
                )
                
                if orbital_data:
                    constellation_result["satellites"][sat_id] = orbital_data
                    constellation_result["constellation_statistics"]["successful_calculations"] += 1
                    self.calculation_statistics["successful_calculations"] += 1
                else:
                    constellation_result["constellation_statistics"]["failed_calculations"] += 1
                    self.calculation_statistics["failed_calculations"] += 1
                    
            except Exception as e:
                self.logger.warning(f"衛星 {satellite.get('name', 'unknown')} 軌道計算失敗: {e}")
                constellation_result["constellation_statistics"]["failed_calculations"] += 1
                self.calculation_statistics["failed_calculations"] += 1
                continue
        
        return constellation_result
    
    def _calculate_single_satellite_orbit(self, satellite: Dict[str, Any], 
                                         time_points: int, 
                                         time_interval_seconds: int) -> Optional[Dict[str, Any]]:
        """計算單顆衛星的軌道"""
        try:
            # 創建TLE數據
            tle_data = {
                "line1": satellite["tle_line1"],
                "line2": satellite["tle_line2"]
            }
            
            # 使用SGP4引擎計算軌道
            orbital_result = self.sgp4_engine.calculate_satellite_orbit(
                satellite_name=satellite["name"],
                tle_data=tle_data,
                time_points=time_points,
                time_interval_seconds=time_interval_seconds
            )
            
            if not orbital_result or "error" in orbital_result:
                self.logger.warning(f"SGP4計算失敗: {satellite['name']}")
                return None
            
            # 格式化結果
            formatted_result = {
                "satellite_info": {
                    "name": satellite["name"],
                    "norad_id": satellite.get("norad_id", "unknown"),
                    "constellation": satellite.get("constellation", "unknown"),
                    "tle_line1": satellite["tle_line1"],
                    "tle_line2": satellite["tle_line2"]
                },
                "orbital_positions": orbital_result.get("positions", []),
                "orbital_elements": orbital_result.get("orbital_elements", {}),
                "calculation_metadata": {
                    "time_points": len(orbital_result.get("positions", [])),
                    "time_interval_seconds": time_interval_seconds,
                    "calculation_method": "SGP4"
                }
            }
            
            # 更新統計
            self.calculation_statistics["total_position_points"] += len(orbital_result.get("positions", []))
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"計算衛星 {satellite.get('name', 'unknown')} 軌道時出錯: {e}")
            return None
    
    def validate_calculation_results(self, orbital_results: Dict[str, Any]) -> Dict[str, Any]:
        """驗證計算結果的完整性和正確性"""
        validation_result = {
            "passed": True,
            "total_satellites": len(orbital_results.get("satellites", {})),
            "validation_checks": {},
            "issues": []
        }
        
        # 檢查1: 基本數據完整性
        satellites = orbital_results.get("satellites", {})
        
        if not satellites:
            validation_result["passed"] = False
            validation_result["issues"].append("無衛星軌道數據")
            return validation_result
        
        # 檢查2: 軌道位置數據完整性
        invalid_positions = 0
        total_positions = 0
        
        for sat_id, sat_data in satellites.items():
            positions = sat_data.get("orbital_positions", [])
            total_positions += len(positions)
            
            if len(positions) < 100:  # 少於100個位置點視為異常
                invalid_positions += 1
                validation_result["issues"].append(f"衛星 {sat_id} 位置點過少: {len(positions)}")
        
        validation_result["validation_checks"]["position_data_check"] = {
            "total_positions": total_positions,
            "invalid_satellites": invalid_positions,
            "passed": invalid_positions == 0
        }
        
        if invalid_positions > 0:
            validation_result["passed"] = False
        
        # 檢查3: 時間連續性
        time_continuity_issues = 0
        for sat_id, sat_data in satellites.items():
            positions = sat_data.get("orbital_positions", [])
            if len(positions) > 1:
                # 檢查時間戳連續性
                prev_time = None
                for pos in positions[:10]:  # 檢查前10個位置
                    if "timestamp" in pos:
                        current_time = pos["timestamp"]
                        if prev_time and current_time <= prev_time:
                            time_continuity_issues += 1
                            break
                        prev_time = current_time
        
        validation_result["validation_checks"]["time_continuity_check"] = {
            "satellites_with_issues": time_continuity_issues,
            "passed": time_continuity_issues == 0
        }
        
        if time_continuity_issues > 0:
            validation_result["passed"] = False
        
        # 檢查4: 物理合理性（軌道高度）
        altitude_issues = 0
        for sat_id, sat_data in satellites.items():
            positions = sat_data.get("orbital_positions", [])
            for pos in positions[:5]:  # 檢查前5個位置
                altitude = pos.get("altitude_km", 0)
                if altitude < 200 or altitude > 2000:  # LEO軌道高度範圍
                    altitude_issues += 1
                    validation_result["issues"].append(f"衛星 {sat_id} 軌道高度異常: {altitude}km")
                    break
        
        validation_result["validation_checks"]["physical_validity_check"] = {
            "satellites_with_issues": altitude_issues,
            "passed": altitude_issues == 0
        }
        
        if altitude_issues > 0:
            validation_result["passed"] = False
        
        return validation_result
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return self.calculation_statistics.copy()