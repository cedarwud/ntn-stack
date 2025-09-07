#!/usr/bin/env python3
"""
地理相關性篩選模組 - 階段二智能篩選系統

依據: @docs/satellite_data_preprocessing.md 階段 2.2 地理相關性篩選
目標位置: 台灣 NTPU (24.9441°N, 121.3713°E)
"""

import math
from typing import Dict, List, Any, Tuple
from shared_core.elevation_threshold_manager import get_elevation_threshold_manager

class GeographicFilter:
    """地理相關性篩選器"""
    
    def __init__(self):
        # NTPU 觀測點座標
        self.observer_location = {
            "name": "National Taipei University",
            "latitude": 24.9441667,  # 度
            "longitude": 121.3713889,  # 度
            "altitude": 100,  # 米，海拔高度
            "timezone": "Asia/Taipei"
        }
        
        # 🔧 統一仰角門檻管理器
        self.elevation_manager = get_elevation_threshold_manager()
        
        # 🔧 星座特定的地理篩選參數 (使用統一管理器)
        self.constellation_filtering_params = {
            "starlink": {
                "min_elevation_deg": self.elevation_manager.get_min_elevation('starlink'),
                "max_range_km": 2000,        # LEO合理服務範圍  
                "geographic_relevance_zone": 10,  # 台灣周邊區域
            },
            "oneweb": {
                "min_elevation_deg": self.elevation_manager.get_min_elevation('oneweb'),
                "max_range_km": 2000,        # LEO合理服務範圍
                "geographic_relevance_zone": 10,  # 台灣周邊區域
            }
        }
        
        # 🔧 通用地理篩選參數（向下兼容，使用統一管理器）
        self.filtering_params = {
            "min_elevation_deg": self.elevation_manager.get_min_elevation('starlink'),  # 預設使用Starlink標準
            "max_range_km": 2000,            # 從5000km縮減到2000km
            "geographic_relevance_zone": 10,  # 從50度縮減到10度
        }
        
        # 📊 理論計算：
        # - Starlink (5度): 較多候選衛星，約50-55顆
        # - OneWeb (10度): 較少候選衛星，約12-15顆
        # - 總動態池：預期約67顆衛星（vs原567顆）
    
    def apply_geographic_filtering(self, constellation_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        應用地理相關性篩選
        
        Args:
            constellation_data: 星座分離後的衛星數據
            
        Returns:
            Dict[str, List[Dict]]: 地理篩選後的衛星數據
        """
        filtered_data = {}
        
        for constellation, satellites in constellation_data.items():
            filtered_satellites = []
            
            for satellite in satellites:
                if self._is_geographically_relevant(satellite):
                    # 計算地理相關性評分
                    geo_score = self._calculate_geographic_relevance_score(satellite)
                    satellite["geographic_relevance_score"] = geo_score
                    filtered_satellites.append(satellite)
            
            filtered_data[constellation] = filtered_satellites
        
        return filtered_data
    
    def _is_geographically_relevant(self, satellite: Dict) -> bool:
        """
        判斷衛星是否與觀測點地理相關
        
        Args:
            satellite: 衛星數據
            
        Returns:
            bool: 是否地理相關
        """
        orbit_data = satellite.get("orbit_data", {})
        
        # 🔧 根據星座確定仰角門檻
        constellation = satellite.get("constellation", "starlink").lower()
        constellation_params = self.constellation_filtering_params.get(
            constellation, 
            self.constellation_filtering_params["starlink"]  # 預設使用Starlink參數
        )
        min_elevation = constellation_params["min_elevation_deg"]
        
        # 軌道傾角匹配檢查
        inclination = orbit_data.get("inclination", 0)
        if not self._check_inclination_coverage(inclination):
            return False
        
        # 軌道高度合理性檢查
        altitude = orbit_data.get("altitude", 0)
        if not self._check_altitude_range(altitude):
            return False
        
        # 檢查是否有時間序列數據
        timeseries = satellite.get("timeseries", [])
        if not timeseries:
            return False
        
        # 🔧 使用星座特定的仰角門檻檢查可見時間點
        visible_points = 0
        for point in timeseries:
            elevation = point.get("elevation_deg", -90)
            if elevation >= min_elevation:  # 使用星座特定門檻
                visible_points += 1
        
        # 至少需要有一些可見時間點
        is_relevant = visible_points > 0
        
        # 記錄使用的參數供調試
        satellite["_filtering_params_used"] = {
            "constellation": constellation,
            "min_elevation_deg": min_elevation,
            "visible_points": visible_points,
            "total_points": len(timeseries)
        }
        
        return is_relevant
    
    def _check_inclination_coverage(self, inclination: float) -> bool:
        """
        檢查軌道傾角是否覆蓋觀測點
        
        軌道傾角必須大於觀測點緯度才能覆蓋
        """
        observer_lat = abs(self.observer_location["latitude"])
        return inclination >= observer_lat
    
    def _check_altitude_range(self, altitude: float) -> bool:
        """
        檢查軌道高度是否在合理範圍內
        """
        return 200 <= altitude <= 2000  # LEO 衛星高度範圍
    
    def _calculate_geographic_relevance_score(self, satellite: Dict) -> float:
        """
        計算地理相關性評分 (0-100)
        
        Args:
            satellite: 衛星數據
            
        Returns:
            float: 地理相關性評分
        """
        score = 0.0
        orbit_data = satellite.get("orbit_data", {})
        timeseries = satellite.get("timeseries", [])
        
        # 1. 軌道傾角適用性 (30分)
        inclination = orbit_data.get("inclination", 0)
        inclination_score = self._evaluate_inclination_suitability(inclination)
        score += inclination_score * 0.30
        
        # 2. 可見性統計 (40分)
        visibility_score = self._evaluate_visibility_statistics(timeseries)
        score += visibility_score * 0.40
        
        # 3. 軌道高度優化 (20分)
        altitude = orbit_data.get("altitude", 0)
        altitude_score = self._evaluate_altitude_optimization(altitude)
        score += altitude_score * 0.20
        
        # 4. 覆蓋持續性 (10分)
        coverage_score = self._evaluate_coverage_continuity(timeseries)
        score += coverage_score * 0.10
        
        return min(100.0, max(0.0, score))
    
    def _evaluate_inclination_suitability(self, inclination: float) -> float:
        """評估軌道傾角適用性 (0-100)"""
        observer_lat = self.observer_location["latitude"]
        
        if inclination < observer_lat:
            return 0.0  # 無法覆蓋
        elif inclination <= observer_lat + 10:
            return 50.0  # 勉強覆蓋
        elif inclination <= observer_lat + 30:
            return 100.0  # 良好覆蓋
        elif inclination <= 90:
            return 80.0  # 極地覆蓋，略過頭
        else:
            return 60.0  # 逆行軌道
    
    def _evaluate_visibility_statistics(self, timeseries: List[Dict]) -> float:
        """評估可見性統計 (0-100)"""
        if not timeseries:
            return 0.0
        
        total_points = len(timeseries)
        visible_points = 0
        max_elevation = 0
        elevation_sum = 0
        
        for point in timeseries:
            elevation = point.get("elevation_deg", -90)
            if elevation >= self.filtering_params["min_elevation_deg"]:
                visible_points += 1
                elevation_sum += elevation
                max_elevation = max(max_elevation, elevation)
        
        if visible_points == 0:
            return 0.0
        
        # 可見性比例 (50%)
        visibility_ratio = (visible_points / total_points) * 50
        
        # 最大仰角 (30%)
        max_elevation_score = min(max_elevation / 90 * 30, 30)
        
        # 平均仰角 (20%)
        avg_elevation = elevation_sum / visible_points
        avg_elevation_score = min(avg_elevation / 45 * 20, 20)
        
        return visibility_ratio + max_elevation_score + avg_elevation_score
    
    def _evaluate_altitude_optimization(self, altitude: float) -> float:
        """評估軌道高度優化 (0-100)"""
        if altitude <= 0:
            return 0.0
        
        # 不同高度區間的優化程度
        if 400 <= altitude <= 600:
            return 100.0  # Starlink 最佳高度
        elif 1100 <= altitude <= 1300:
            return 90.0   # OneWeb 最佳高度
        elif 300 <= altitude <= 800:
            return 80.0   # 良好的 LEO 高度
        elif 800 <= altitude <= 1500:
            return 70.0   # 可接受的 LEO 高度
        else:
            return 30.0   # 非最佳高度
    
    def _evaluate_coverage_continuity(self, timeseries: List[Dict]) -> float:
        """評估覆蓋持續性 (0-100)"""
        if not timeseries:
            return 0.0
        
        # 計算可見性段落的持續性
        visible_segments = []
        current_segment = 0
        
        for point in timeseries:
            elevation = point.get("elevation_deg", -90)
            if elevation >= self.filtering_params["min_elevation_deg"]:
                current_segment += 1
            else:
                if current_segment > 0:
                    visible_segments.append(current_segment)
                    current_segment = 0
        
        if current_segment > 0:
            visible_segments.append(current_segment)
        
        if not visible_segments:
            return 0.0
        
        # 評估段落持續性
        avg_segment_length = sum(visible_segments) / len(visible_segments)
        max_segment_length = max(visible_segments)
        
        # 較長的持續可見時間得分較高
        continuity_score = min((avg_segment_length / 10) * 50, 50)
        continuity_score += min((max_segment_length / 20) * 50, 50)
        
        return continuity_score
    
    def get_filtering_statistics(self, 
                               original_data: Dict[str, List[Dict]], 
                               filtered_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        獲取地理篩選統計信息
        
        Returns:
            Dict: 篩選統計數據
        """
        stats = {
            "observer_location": self.observer_location,
            "filtering_params": self.filtering_params,
            "constellation_stats": {},
            "overall_reduction": {}
        }
        
        total_original = 0
        total_filtered = 0
        
        for constellation in original_data.keys():
            original_count = len(original_data.get(constellation, []))
            filtered_count = len(filtered_data.get(constellation, []))
            
            reduction_rate = ((original_count - filtered_count) / original_count * 100) if original_count > 0 else 0
            
            stats["constellation_stats"][constellation] = {
                "original_count": original_count,
                "filtered_count": filtered_count,
                "reduction_rate_percent": round(reduction_rate, 2),
                "avg_geo_score": self._calculate_average_geo_score(filtered_data.get(constellation, []))
            }
            
            total_original += original_count
            total_filtered += filtered_count
        
        overall_reduction_rate = ((total_original - total_filtered) / total_original * 100) if total_original > 0 else 0
        
        stats["overall_reduction"] = {
            "total_original": total_original,
            "total_filtered": total_filtered,
            "reduction_rate_percent": round(overall_reduction_rate, 2)
        }
        
        return stats
    
    def _calculate_average_geo_score(self, satellites: List[Dict]) -> float:
        """計算平均地理相關性評分"""
        if not satellites:
            return 0.0
        
        total_score = sum(sat.get("geographic_relevance_score", 0) for sat in satellites)
        return round(total_score / len(satellites), 2)


def main():
    """測試地理相關性篩選功能"""
    geo_filter = GeographicFilter()
    
    # 模擬星座分離後的數據
    test_data = {
        "starlink": [
            {
                "satellite_id": "STARLINK-1007",
                "orbit_data": {
                    "altitude": 550,
                    "inclination": 53,
                    "position": {"x": 1234, "y": 5678, "z": 9012}
                },
                "timeseries": [
                    {"time": "2025-08-12T12:00:00Z", "elevation_deg": 45.0, "azimuth_deg": 180.0},
                    {"time": "2025-08-12T12:00:30Z", "elevation_deg": 50.0, "azimuth_deg": 185.0}
                ]
            }
        ],
        "oneweb": [
            {
                "satellite_id": "ONEWEB-0123",
                "orbit_data": {
                    "altitude": 1200,
                    "inclination": 87,
                    "position": {"x": 2345, "y": 6789, "z": 123}
                },
                "timeseries": [
                    {"time": "2025-08-12T12:00:00Z", "elevation_deg": 30.0, "azimuth_deg": 90.0},
                    {"time": "2025-08-12T12:00:30Z", "elevation_deg": 25.0, "azimuth_deg": 95.0}
                ]
            }
        ]
    }
    
    # 執行地理篩選
    filtered_data = geo_filter.apply_geographic_filtering(test_data)
    stats = geo_filter.get_filtering_statistics(test_data, filtered_data)
    
    print("地理相關性篩選測試結果:")
    import json
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()