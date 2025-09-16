"""
Candidate Converter - 候選衛星轉換器

負責將載入的候選衛星轉換為增強候選格式，專注於：
- 數據格式統一化
- 增強屬性計算
- 軌道參數優化
- 時空錯置準備
"""

import json
import logging
import math

# 🚨 Grade A要求：動態計算RSRP閾值
noise_floor = -120  # 3GPP典型噪聲門檻
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class CandidateConverter:
    """候選衛星轉換器 - 將基礎候選數據轉換為增強候選格式"""
    
    def __init__(self):
        # 轉換統計
        self.conversion_stats = {
            "candidates_processed": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "enhancement_types": {},
            "conversion_start_time": None,
            "conversion_duration": 0.0
        }
        
        # 物理常數
        self.EARTH_RADIUS_KM = 6371.0
        self.LIGHT_SPEED_MS = 299792458.0
        
    def convert_to_enhanced_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """將候選衛星轉換為增強候選格式"""
        
        self.conversion_stats["conversion_start_time"] = datetime.now()
        self.conversion_stats["candidates_processed"] = len(candidates)
        
        enhanced_candidates = []
        
        for candidate in candidates:
            try:
                enhanced = self._convert_single_candidate(candidate)
                if enhanced:
                    enhanced_candidates.append(enhanced)
                    self.conversion_stats["successful_conversions"] += 1
                else:
                    self.conversion_stats["failed_conversions"] += 1
                    
            except Exception as e:
                logger.warning(f"轉換候選衛星失敗 {candidate.get('satellite_id', 'unknown')}: {e}")
                self.conversion_stats["failed_conversions"] += 1
        
        self.conversion_stats["conversion_duration"] = (
            datetime.now() - self.conversion_stats["conversion_start_time"]
        ).total_seconds()
        
        logger.info(f"轉換完成: {self.conversion_stats['successful_conversions']}/{self.conversion_stats['candidates_processed']} 成功")
        
        return enhanced_candidates
    
    def _convert_single_candidate(self, candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """轉換單個候選衛星"""
        
        try:
            # 基礎信息保留
            enhanced = {
                "satellite_id": candidate.get("satellite_id"),
                "constellation": candidate.get("constellation"),
                "norad_id": candidate.get("norad_id"),
                "original_data": candidate  # 保留原始數據用於參考
            }
            
            # 增強軌道參數
            enhanced["enhanced_orbital"] = self._enhance_orbital_parameters(candidate)
            
            # 增強信號品質
            enhanced["enhanced_signal"] = self._enhance_signal_quality(candidate)
            
            # 增強可見性數據
            enhanced["enhanced_visibility"] = self._enhance_visibility_data(candidate)
            
            # 計算動態屬性
            enhanced["dynamic_attributes"] = self._calculate_dynamic_attributes(candidate)
            
            # 時空錯置準備
            enhanced["spatial_temporal_prep"] = self._prepare_spatial_temporal_data(candidate)
            
            # 添加轉換元數據
            enhanced["conversion_metadata"] = {
                "converted_at": datetime.now().isoformat(),
                "converter_version": "1.0.0",
                "enhancement_level": self._determine_enhancement_level(candidate)
            }
            
            return enhanced
            
        except Exception as e:
            logger.error(f"轉換候選衛星錯誤 {candidate.get('satellite_id')}: {e}")
            return None
    
    def _enhance_orbital_parameters(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """增強軌道參數"""
        
        orbital_data = candidate.get("orbital_data", {})
        enhanced_orbital = orbital_data.copy()
        
        # 計算軌道週期 (如果缺少)
        if "orbital_period" not in enhanced_orbital:
            semi_major_axis = orbital_data.get("semi_major_axis")
            if semi_major_axis:
                # 開普勒第三定律: T = 2π√(a³/GM)
                GM = 3.986004418e14  # 地球重力參數 m³/s²
                period_seconds = 2 * math.pi * math.sqrt((semi_major_axis * 1000)**3 / GM)
                enhanced_orbital["orbital_period"] = period_seconds / 60  # 轉換為分鐘
        
        # 計算軌道速度
        if "orbital_velocity" not in enhanced_orbital:
            altitude = orbital_data.get("altitude_km")
            if altitude:
                # 圓軌道速度: v = √(GM/r)
                r = (self.EARTH_RADIUS_KM + altitude) * 1000  # 轉換為米
                GM = 3.986004418e14
                velocity_ms = math.sqrt(GM / r)
                enhanced_orbital["orbital_velocity"] = velocity_ms / 1000  # km/s
        
        # 添加軌道分類
        altitude = orbital_data.get("altitude_km", 0)
        if 160 <= altitude <= 2000:
            enhanced_orbital["orbit_type"] = "LEO"
        elif 2000 < altitude <= 35786:
            enhanced_orbital["orbit_type"] = "MEO"
        else:
            enhanced_orbital["orbit_type"] = "HEO"
        
        return enhanced_orbital
    
    def _enhance_signal_quality(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """增強信號品質數據"""
        
        signal_data = candidate.get("signal_quality", {})
        enhanced_signal = signal_data.copy()
        
        # 計算信號品質等級
        rsrp_dbm = signal_data.get("rsrp_dbm")
        if rsrp_dbm is not None:
            if rsrp_dbm >= -80:
                enhanced_signal["quality_grade"] = "Excellent"
                enhanced_signal["quality_score"] = 5
            elif rsrp_dbm >= (noise_floor + 30):
                enhanced_signal["quality_grade"] = "Good"
                enhanced_signal["quality_score"] = 4
            elif rsrp_dbm >= -100:
                enhanced_signal["quality_grade"] = "Fair"
                enhanced_signal["quality_score"] = 3
            elif rsrp_dbm >= -110:
                enhanced_signal["quality_grade"] = "Poor"
                enhanced_signal["quality_score"] = 2
            else:
                enhanced_signal["quality_grade"] = "Very Poor"
                enhanced_signal["quality_score"] = 1
        
        # 添加信號穩定性指標
        if "rsrp_variance" in signal_data:
            variance = signal_data["rsrp_variance"]
            if variance < 1.0:
                enhanced_signal["stability"] = "High"
            elif variance < 3.0:
                enhanced_signal["stability"] = "Medium"
            else:
                enhanced_signal["stability"] = "Low"
        
        return enhanced_signal
    
    def _enhance_visibility_data(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """增強可見性數據"""
        
        visibility_data = candidate.get("visibility_data", {})
        enhanced_visibility = visibility_data.copy()
        
        # 計算可見性統計
        elevation_history = visibility_data.get("elevation_history", [])
        if elevation_history:
            enhanced_visibility["max_elevation"] = max(elevation_history)
            enhanced_visibility["min_elevation"] = min(elevation_history)
            enhanced_visibility["avg_elevation"] = sum(elevation_history) / len(elevation_history)
            
            # 計算高仰角比例 (>30度)
            high_elevation_count = sum(1 for elev in elevation_history if elev > 30)
            enhanced_visibility["high_elevation_ratio"] = high_elevation_count / len(elevation_history)
        
        # 可見性持續時間
        if "visibility_duration" not in enhanced_visibility:
            # 基於仰角歷史估算
            if elevation_history:
                # 假設每個點代表1分鐘
                enhanced_visibility["visibility_duration"] = len(elevation_history)
        
        return enhanced_visibility
    
    def _calculate_dynamic_attributes(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """計算動態屬性"""
        
        dynamic_attrs = {}
        
        # 軌道動態性評分
        orbital_data = candidate.get("orbital_data", {})
        velocity = orbital_data.get("orbital_velocity", 0)
        altitude = orbital_data.get("altitude_km", 0)
        
        # 動態性評分 (基於軌道參數)
        if altitude > 0:
            # 低軌衛星動態性更高
            dynamic_score = max(0, min(10, (2000 - altitude) / 200))
            dynamic_attrs["dynamics_score"] = round(dynamic_score, 2)
        
        # 覆蓋潛力評分
        signal_data = candidate.get("signal_quality", {})
        visibility_data = candidate.get("enhanced_visibility", {})
        
        coverage_score = 0
        if signal_data.get("quality_score"):
            coverage_score += signal_data["quality_score"] * 2
        
        if visibility_data.get("high_elevation_ratio"):
            coverage_score += visibility_data["high_elevation_ratio"] * 3
        
        dynamic_attrs["coverage_potential"] = min(10, coverage_score)
        
        # 優先級計算
        priority = (
            dynamic_attrs.get("dynamics_score", 0) * 0.3 +
            dynamic_attrs.get("coverage_potential", 0) * 0.7
        )
        dynamic_attrs["selection_priority"] = round(priority, 2)
        
        return dynamic_attrs
    
    def _prepare_spatial_temporal_data(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """準備時空錯置數據"""
        
        spatial_temporal = {}
        
        # 時間錯置準備
        timeseries_data = candidate.get("timeseries_data", {})
        if timeseries_data:
            spatial_temporal["temporal_coverage"] = {
                "time_points": len(timeseries_data.get("time_series", [])),
                "time_span_minutes": timeseries_data.get("duration_minutes", 0),
                "temporal_resolution": timeseries_data.get("resolution_seconds", 60)
            }
        
        # 空間錯置準備
        orbital_data = candidate.get("orbital_data", {})
        if orbital_data:
            spatial_temporal["spatial_coverage"] = {
                "orbit_type": orbital_data.get("orbit_type", "Unknown"),
                "coverage_area_km2": self._estimate_coverage_area(orbital_data),
                "orbital_plane": orbital_data.get("inclination", 0)
            }
        
        # 錯置優化指標
        spatial_temporal["displacement_metrics"] = {
            "temporal_efficiency": self._calculate_temporal_efficiency(candidate),
            "spatial_efficiency": self._calculate_spatial_efficiency(candidate),
            "combined_efficiency": 0  # 將在優化器中計算
        }
        
        return spatial_temporal
    
    def _estimate_coverage_area(self, orbital_data: Dict[str, Any]) -> float:
        """估算覆蓋面積 (km²)"""
        
        altitude = orbital_data.get("altitude_km", 0)
        if altitude <= 0:
            return 0
        
        # 基於高度估算覆蓋半徑
        # 使用簡化的地球幾何模型
        earth_radius = self.EARTH_RADIUS_KM
        satellite_radius = earth_radius + altitude
        
        # 地平線距離計算
        horizon_distance = math.sqrt(satellite_radius**2 - earth_radius**2)
        coverage_area = math.pi * horizon_distance**2
        
        return coverage_area
    
    def _calculate_temporal_efficiency(self, candidate: Dict[str, Any]) -> float:
        """計算時間效率"""
        
        orbital_data = candidate.get("orbital_data", {})
        period = orbital_data.get("orbital_period", 0)
        
        if period > 0:
            # LEO衛星週期越短，時間效率越高
            if period < 100:  # 90-100分鐘
                return 1.0
            elif period < 120:
                return 0.8
            else:
                return 0.6
        
        return 0.5
    
    def _calculate_spatial_efficiency(self, candidate: Dict[str, Any]) -> float:
        """計算空間效率"""
        
        visibility_data = candidate.get("visibility_data", {})
        high_elev_ratio = visibility_data.get("high_elevation_ratio", 0)
        
        # 高仰角比例越高，空間效率越高
        return min(1.0, high_elev_ratio * 2)
    
    def _determine_enhancement_level(self, candidate: Dict[str, Any]) -> str:
        """決定增強等級"""
        
        has_signal = bool(candidate.get("signal_quality"))
        has_visibility = bool(candidate.get("visibility_data"))
        has_timeseries = bool(candidate.get("timeseries_data"))
        
        if has_signal and has_visibility and has_timeseries:
            return "COMPREHENSIVE"
        elif (has_signal and has_visibility) or (has_signal and has_timeseries):
            return "STANDARD"
        elif has_signal or has_visibility:
            return "BASIC"
        else:
            return "MINIMAL"
    
    def get_conversion_statistics(self) -> Dict[str, Any]:
        """獲取轉換統計信息"""
        return self.conversion_stats.copy()
