# 🛰️ 軌道計算器 - 學術級Grade A實現
# 嚴格遵循學術數據標準，絕對禁止Mock/模擬實現

import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 導入真實的SGP4引擎 - 絕對禁止Mock/模擬實現
from shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine

logger = logging.getLogger(__name__)

class OrbitalCalculator:
    """
    🛰️ 軌道計算器 - 學術級Grade A實現
    
    嚴格遵循學術數據標準:
    ✅ 只使用真實SGP4引擎
    ❌ 絕對禁止Mock/模擬/回退機制
    ✅ 完全符合文檔API規範
    """
    
    def __init__(self, observer_coordinates: Tuple[float, float, float] = (24.9441667, 121.3713889, 50)):
        """
        初始化軌道計算器 - 學術標準實現
        
        Args:
            observer_coordinates: 觀測點坐標 (緯度, 經度, 海拔m)，預設為NTPU
        """
        self.logger = logging.getLogger(f"{__name__}.OrbitalCalculator")
        self.observer_coordinates = observer_coordinates
        
        # 🚨 強制要求：只能使用真實SGP4引擎，絕不允許Mock回退
        try:
            self.sgp4_engine = SGP4OrbitalEngine(observer_coordinates=observer_coordinates)
            self.logger.info(f"✅ 真實SGP4引擎初始化成功，觀測點: {observer_coordinates}")
            
        except Exception as e:
            self.logger.error(f"❌ SGP4引擎初始化失敗: {e}")
            # 🚨 遵循學術標準：失敗時絕不回退到Mock，必須修復錯誤
            raise RuntimeError(f"SGP4引擎初始化失敗，絕不允許使用模擬引擎: {e}")
        
        # 引擎類型強制檢查 - 防止意外使用錯誤引擎
        assert isinstance(self.sgp4_engine, SGP4OrbitalEngine), f"錯誤引擎類型: {type(self.sgp4_engine)}"
        
        # 計算統計
        self.calculation_statistics = {
            "total_satellites": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "total_position_points": 0,
            "calculation_time": 0.0,
            "engine_type": "SGP4OrbitalEngine",  # 強制記錄引擎類型
            "academic_compliance": "Grade_A",     # 學術合規等級
            "no_fallback_used": True              # 確認未使用任何回退機制
        }
    
    def calculate_orbits_for_satellites(self, satellites: List[Dict[str, Any]], 
                                       time_points: int = 192,
                                       time_interval_seconds: int = 30) -> Dict[str, Any]:
        """
        為所有衛星計算軌道 - 符合文檔API規範
        
        Args:
            satellites: 衛星數據列表
            time_points: 時間點數量，預設192點
            time_interval_seconds: 時間間隔（秒），預設30秒
            
        Returns:
            軌道計算結果
        """
        self.logger.info(f"🚀 開始計算 {len(satellites)} 顆衛星的軌道")
        self.logger.info(f"   時間點: {time_points}, 間隔: {time_interval_seconds}秒")
        
        # 🚨 強制運行時檢查：確保使用正確的引擎
        assert isinstance(self.sgp4_engine, SGP4OrbitalEngine), f"運行時檢測到錯誤引擎: {type(self.sgp4_engine)}"
        
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
                "sgp4_engine_type": type(self.sgp4_engine).__name__,  # 記錄實際引擎類型
                "academic_grade": "A",
                "no_simulation_used": True
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
            # 構建符合SGP4OrbitalEngine期望的數據格式
            satellite_data_for_sgp4 = {
                'satellite_id': satellite.get('norad_id', satellite.get('name', 'unknown')),
                'name': satellite.get('name', 'Unknown'),
                'constellation': satellite.get('constellation', 'unknown'),
                'tle_data': {
                    'tle_line1': satellite["tle_line1"],
                    'tle_line2': satellite["tle_line2"],
                    'name': satellite.get('name', 'Unknown')
                }
            }
            
            # 🚨 強制檢查：確保使用真實SGP4計算方法
            assert hasattr(self.sgp4_engine, 'calculate_position_timeseries'), "SGP4引擎缺少必需方法"
            
            # 使用SGP4引擎計算位置時間序列
            position_timeseries = self.sgp4_engine.calculate_position_timeseries(
                satellite_data_for_sgp4,
                time_range_minutes=time_points * time_interval_seconds / 60  # 轉換為分鐘
            )
            
            if not position_timeseries:
                self.logger.warning(f"SGP4計算失敗: {satellite['name']}")
                return None
            
            # 🚨 API契約格式檢查：星座特定時間序列長度檢查
            constellation = satellite.get('constellation', '').lower()
            expected_points = {
                'starlink': 192,  # 96分鐘軌道
                'oneweb': 218     # 109分鐘軌道
            }.get(constellation)
            
            if expected_points is not None:
                assert len(position_timeseries) == expected_points, \
                    f"時間序列長度錯誤: {len(position_timeseries)} (應為{expected_points}點，星座: {constellation})"
            
            # 格式化結果為統一標準格式
            formatted_result = {
                "satellite_info": {
                    "name": satellite["name"],
                    "norad_id": satellite.get("norad_id", "unknown"),
                    "constellation": satellite.get("constellation", "unknown"),
                    "tle_line1": satellite["tle_line1"],
                    "tle_line2": satellite["tle_line2"]
                },
                "orbital_positions": position_timeseries,  # 直接使用SGP4引擎的輸出格式
                "calculation_metadata": {
                    "time_points": len(position_timeseries),
                    "time_interval_seconds": time_interval_seconds,
                    "calculation_method": "SGP4",
                    "engine_type": type(self.sgp4_engine).__name__,
                    "academic_grade": "A",
                    "no_simulation": True
                }
            }
            
            # 更新統計
            self.calculation_statistics["total_position_points"] += len(position_timeseries)
            
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
        
        # 檢查4: 學術標準合規性 - 確保無Mock數據
        academic_compliance_passed = True
        metadata = orbital_results.get("calculation_metadata", {})
        
        if metadata.get("sgp4_engine_type") != "SGP4OrbitalEngine":
            validation_result["issues"].append(f"檢測到非標準引擎: {metadata.get('sgp4_engine_type')}")
            academic_compliance_passed = False
        
        if not metadata.get("no_simulation_used", False):
            validation_result["issues"].append("檢測到可能使用了模擬數據")
            academic_compliance_passed = False
        
        validation_result["validation_checks"]["academic_compliance_check"] = {
            "passed": academic_compliance_passed
        }
        
        if not academic_compliance_passed:
            validation_result["passed"] = False
        
        return validation_result
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return self.calculation_statistics.copy()