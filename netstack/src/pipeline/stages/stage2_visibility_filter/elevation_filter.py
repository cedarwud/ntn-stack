"""
仰角過濾器 - Stage 2模組化組件

職責：
1. 基於ITU-R標準應用動態仰角門檻
2. 環境調整係數計算（城市、山區、降雨等）
3. 分層仰角門檻過濾（5°/10°/15°）
4. 可見性品質評估
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math

logger = logging.getLogger(__name__)

class ElevationFilter:
    """仰角過濾器 - 基於ITU-R標準的動態門檻系統"""
    
    def __init__(self, 
                 primary_threshold: float = 10.0,
                 environment_type: str = "urban",
                 weather_conditions: str = "clear"):
        """
        初始化仰角過濾器
        
        Args:
            primary_threshold: 主要仰角門檻（度）
            environment_type: 環境類型 (open/urban/mountainous)
            weather_conditions: 天氣條件 (clear/light_rain/heavy_rain)
        """
        self.logger = logging.getLogger(f"{__name__}.ElevationFilter")
        
        self.primary_threshold = primary_threshold
        self.environment_type = environment_type.lower()
        self.weather_conditions = weather_conditions.lower()
        
        # ITU-R標準環境調整係數
        self.environment_factors = {
            "open": 1.0,        # 開闊地區
            "urban": 1.1,       # 城市環境
            "mountainous": 1.3  # 山區環境
        }
        
        # 天氣條件調整係數
        self.weather_factors = {
            "clear": 1.0,
            "light_rain": 1.2,
            "heavy_rain": 1.4
        }
        
        # 分層門檻系統
        self.layered_thresholds = {
            "critical": 5.0,   # 臨界門檻
            "standard": 10.0,  # 標準門檻
            "preferred": 15.0  # 優選門檻
        }
        
        # 計算動態調整後的門檻
        self.adjusted_thresholds = self._calculate_adjusted_thresholds()
        
        self.logger.info("✅ 仰角過濾器初始化完成")
        self.logger.info(f"   環境類型: {self.environment_type} (係數: {self.environment_factors.get(self.environment_type, 1.0)})")
        self.logger.info(f"   天氣條件: {self.weather_conditions} (係數: {self.weather_factors.get(self.weather_conditions, 1.0)})")
        self.logger.info(f"   調整後門檻: {self.adjusted_thresholds}")
        
        # 過濾統計
        self.filter_statistics = {
            "total_positions_checked": 0,
            "positions_above_critical": 0,
            "positions_above_standard": 0,
            "positions_above_preferred": 0,
            "satellites_filtered": 0,
            "average_elevation": 0.0
        }
    
    def apply_elevation_filtering(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        對衛星列表應用仰角過濾
        
        Args:
            satellites: 含可見性計算結果的衛星列表
            
        Returns:
            過濾後的結果和統計信息
        """
        self.logger.info(f"🔍 應用仰角過濾 (門檻: {self.adjusted_thresholds['standard']:.1f}°)...")
        
        filtered_satellites = []
        total_positions = 0
        positions_above_thresholds = {"critical": 0, "standard": 0, "preferred": 0}
        elevation_sum = 0.0
        satellites_passed = 0
        
        for satellite in satellites:
            try:
                # 過濾單顆衛星
                filtered_satellite = self._filter_single_satellite(satellite)
                
                if filtered_satellite:
                    filtered_satellites.append(filtered_satellite)
                    satellites_passed += 1
                    
                    # 統計衛星的仰角數據
                    sat_stats = self._calculate_satellite_elevation_stats(filtered_satellite)
                    total_positions += sat_stats["total_positions"]
                    elevation_sum += sat_stats["elevation_sum"]
                    
                    for threshold_name in positions_above_thresholds.keys():
                        positions_above_thresholds[threshold_name] += sat_stats[f"positions_above_{threshold_name}"]
                        
            except Exception as e:
                self.logger.warning(f"過濾衛星 {satellite.get('name', 'unknown')} 時出錯: {e}")
                continue
        
        # 更新統計
        self.filter_statistics.update({
            "total_positions_checked": total_positions,
            "positions_above_critical": positions_above_thresholds["critical"],
            "positions_above_standard": positions_above_thresholds["standard"], 
            "positions_above_preferred": positions_above_thresholds["preferred"],
            "satellites_filtered": satellites_passed,
            "average_elevation": elevation_sum / total_positions if total_positions > 0 else 0.0
        })
        
        # 構建結果
        filtering_result = {
            "satellites": filtered_satellites,
            "elevation_filtering_metadata": {
                "primary_threshold_deg": self.adjusted_thresholds["standard"],
                "environment_adjustment": {
                    "type": self.environment_type,
                    "factor": self.environment_factors.get(self.environment_type, 1.0)
                },
                "weather_adjustment": {
                    "conditions": self.weather_conditions,
                    "factor": self.weather_factors.get(self.weather_conditions, 1.0)
                },
                "layered_thresholds": self.adjusted_thresholds.copy(),
                "filtering_timestamp": datetime.now().isoformat()
            },
            "filtering_statistics": self.filter_statistics.copy()
        }
        
        self.logger.info(f"✅ 仰角過濾完成: {satellites_passed}/{len(satellites)} 顆衛星通過標準門檻")
        
        return filtering_result
    
    def _filter_single_satellite(self, satellite: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """過濾單顆衛星的可見性時間序列"""
        
        position_timeseries = satellite.get("position_timeseries", [])
        if not position_timeseries:
            return None
        
        # 過濾位置點
        filtered_positions = []
        
        for position in position_timeseries:
            relative_pos = position.get("relative_to_observer", {})
            elevation = relative_pos.get("elevation_deg", -90)
            
            # 應用標準門檻過濾
            if elevation >= self.adjusted_thresholds["standard"]:
                # 添加仰角品質等級
                quality_level = self._determine_elevation_quality(elevation)
                
                enhanced_position = position.copy()
                enhanced_position["elevation_quality"] = quality_level
                enhanced_position["meets_itu_standard"] = elevation >= self.adjusted_thresholds["standard"]
                
                filtered_positions.append(enhanced_position)
        
        # 如果沒有滿足門檻的位置，返回None
        if not filtered_positions:
            return None
        
        # 構建過濾後的衛星數據
        filtered_satellite = satellite.copy()
        filtered_satellite["position_timeseries"] = filtered_positions
        
        # 重新計算可見性摘要（基於過濾後的數據）
        filtered_satellite["visibility_summary"] = self._recalculate_visibility_summary(filtered_positions)
        filtered_satellite["elevation_filtering"] = self._generate_elevation_analysis(filtered_positions)
        
        return filtered_satellite
    
    def _determine_elevation_quality(self, elevation: float) -> str:
        """判斷仰角品質等級"""
        if elevation >= self.adjusted_thresholds["preferred"]:
            return "preferred"
        elif elevation >= self.adjusted_thresholds["standard"]:
            return "standard"
        elif elevation >= self.adjusted_thresholds["critical"]:
            return "critical"
        else:
            return "below_threshold"
    
    def _calculate_adjusted_thresholds(self) -> Dict[str, float]:
        """計算環境和天氣調整後的門檻值"""
        
        env_factor = self.environment_factors.get(self.environment_type, 1.0)
        weather_factor = self.weather_factors.get(self.weather_conditions, 1.0)
        combined_factor = env_factor * weather_factor
        
        adjusted = {}
        for level, base_threshold in self.layered_thresholds.items():
            adjusted[level] = base_threshold * combined_factor
        
        return adjusted
    
    def _calculate_satellite_elevation_stats(self, satellite: Dict[str, Any]) -> Dict[str, Any]:
        """計算單顆衛星的仰角統計信息"""
        
        positions = satellite.get("position_timeseries", [])
        stats = {
            "total_positions": len(positions),
            "elevation_sum": 0.0,
            "positions_above_critical": 0,
            "positions_above_standard": 0,
            "positions_above_preferred": 0
        }
        
        for position in positions:
            elevation = position.get("relative_to_observer", {}).get("elevation_deg", -90)
            stats["elevation_sum"] += elevation
            
            if elevation >= self.adjusted_thresholds["critical"]:
                stats["positions_above_critical"] += 1
            if elevation >= self.adjusted_thresholds["standard"]:
                stats["positions_above_standard"] += 1
            if elevation >= self.adjusted_thresholds["preferred"]:
                stats["positions_above_preferred"] += 1
        
        return stats
    
    def _recalculate_visibility_summary(self, filtered_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """重新計算基於過濾後位置的可見性摘要"""
        
        if not filtered_positions:
            return {
                "total_points": 0,
                "visible_points": 0,
                "visibility_percentage": 0.0,
                "max_elevation": -90.0,
                "avg_elevation": -90.0
            }
        
        elevations = []
        for position in filtered_positions:
            elevation = position.get("relative_to_observer", {}).get("elevation_deg", -90)
            elevations.append(elevation)
        
        return {
            "total_points": len(filtered_positions),
            "visible_points": len(filtered_positions),  # 所有都是可見的
            "visibility_percentage": 100.0,
            "max_elevation": round(max(elevations), 2),
            "min_elevation": round(min(elevations), 2), 
            "avg_elevation": round(sum(elevations) / len(elevations), 2)
        }
    
    def _generate_elevation_analysis(self, filtered_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成仰角分析報告"""
        
        if not filtered_positions:
            return {"quality_distribution": {}, "meets_standards": False}
        
        quality_counts = {"critical": 0, "standard": 0, "preferred": 0}
        
        for position in filtered_positions:
            quality = position.get("elevation_quality", "unknown")
            if quality in quality_counts:
                quality_counts[quality] += 1
        
        total_positions = len(filtered_positions)
        
        return {
            "quality_distribution": {
                level: {
                    "count": count,
                    "percentage": round(count / total_positions * 100, 2)
                }
                for level, count in quality_counts.items()
            },
            "meets_standards": quality_counts["standard"] + quality_counts["preferred"] > 0,
            "itu_compliance": True,  # 所有過濾後的位置都符合ITU-R標準
            "recommended_for_handover": quality_counts["preferred"] / total_positions >= 0.1  # 至少10%優選品質
        }
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """獲取過濾統計信息"""
        return self.filter_statistics.copy()
    
    def validate_elevation_filtering(self, filtering_result: Dict[str, Any]) -> Dict[str, Any]:
        """驗證仰角過濾結果的合理性"""
        
        validation_result = {
            "passed": True,
            "total_satellites": len(filtering_result.get("satellites", [])),
            "validation_checks": {},
            "issues": []
        }
        
        satellites = filtering_result.get("satellites", [])
        
        if not satellites:
            validation_result["passed"] = False
            validation_result["issues"].append("無衛星通過仰角過濾")
            return validation_result
        
        # 檢查1: 仰角門檻合規性
        compliant_satellites = 0
        
        for sat in satellites:
            positions = sat.get("position_timeseries", [])
            if positions:
                # 檢查所有位置是否都滿足門檻要求
                all_compliant = all(
                    pos.get("relative_to_observer", {}).get("elevation_deg", -90) >= self.adjusted_thresholds["standard"]
                    for pos in positions
                )
                
                if all_compliant:
                    compliant_satellites += 1
        
        validation_result["validation_checks"]["threshold_compliance_check"] = {
            "compliant_satellites": compliant_satellites,
            "total_satellites": len(satellites),
            "passed": compliant_satellites == len(satellites)
        }
        
        if compliant_satellites < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - compliant_satellites} 顆衛星存在低於門檻的位置點")
        
        # 檢查2: 品質分析完整性
        satellites_with_quality = 0
        
        for sat in satellites:
            if "elevation_filtering" in sat:
                satellites_with_quality += 1
        
        validation_result["validation_checks"]["quality_analysis_check"] = {
            "satellites_with_analysis": satellites_with_quality,
            "passed": satellites_with_quality == len(satellites)
        }
        
        if satellites_with_quality < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_quality} 顆衛星缺少品質分析")
        
        return validation_result