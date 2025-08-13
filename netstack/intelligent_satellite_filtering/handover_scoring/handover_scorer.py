#!/usr/bin/env python3
"""
換手適用性評分系統 - 階段二智能篩選系統

依據: @docs/satellite_data_preprocessing.md 階段 2.3 換手適用性評分
核心功能: 基於星座特性和換手需求進行動態評分
"""

import math
import statistics
from typing import Dict, List, Any, Tuple

class HandoverScorer:
    """換手適用性評分器"""
    
    def __init__(self):
        # Starlink 專用評分配置
        self.starlink_scoring_config = {
            "orbital_inclination_weight": 30,    # 軌道傾角適用性
            "altitude_suitability_weight": 25,   # 高度適用性  
            "phase_distribution_weight": 20,     # 相位分散
            "handover_frequency_weight": 15,     # 換手頻率
            "signal_stability_weight": 10,       # 信號穩定性
            
            "optimal_inclination": 53,           # 最佳傾角
            "optimal_altitude": 550,             # 最佳高度 km
            "orbital_period_min": 96             # 軌道週期
        }
        
        # OneWeb 專用評分配置
        self.oneweb_scoring_config = {
            "orbital_inclination_weight": 25,    # 軌道傾角適用性
            "altitude_suitability_weight": 25,   # 高度適用性
            "polar_coverage_weight": 20,         # 極地覆蓋
            "orbital_shape_weight": 20,          # 軌道形狀
            "phase_distribution_weight": 10,     # 相位分散
            
            "optimal_inclination": 87,           # 最佳傾角 (極地軌道)
            "optimal_altitude": 1200,            # 最佳高度 km
            "orbital_period_min": 109            # 軌道週期
        }
    
    def apply_handover_scoring(self, geographic_filtered_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        應用換手適用性評分
        
        Args:
            geographic_filtered_data: 地理篩選後的衛星數據
            
        Returns:
            Dict[str, List[Dict]]: 評分後的衛星數據
        """
        scored_data = {}
        
        # Starlink 評分
        if "starlink" in geographic_filtered_data:
            scored_data["starlink"] = self._score_starlink_satellites(
                geographic_filtered_data["starlink"]
            )
        
        # OneWeb 評分
        if "oneweb" in geographic_filtered_data:
            scored_data["oneweb"] = self._score_oneweb_satellites(
                geographic_filtered_data["oneweb"]
            )
        
        return scored_data
    
    def _score_starlink_satellites(self, satellites: List[Dict]) -> List[Dict]:
        """
        Starlink 衛星專用評分
        
        針對 53° 傾角、550km 高度、96分鐘軌道週期優化
        """
        scored_satellites = []
        
        for satellite in satellites:
            score = self._calculate_starlink_handover_score(satellite)
            satellite["handover_suitability_score"] = score
            satellite["constellation"] = "starlink"
            scored_satellites.append(satellite)
        
        # 按評分排序
        scored_satellites.sort(key=lambda x: x["handover_suitability_score"], reverse=True)
        
        return scored_satellites
    
    def _score_oneweb_satellites(self, satellites: List[Dict]) -> List[Dict]:
        """
        OneWeb 衛星專用評分
        
        針對 87° 傾角、1200km 高度、109分鐘軌道週期優化
        """
        scored_satellites = []
        
        for satellite in satellites:
            score = self._calculate_oneweb_handover_score(satellite)
            satellite["handover_suitability_score"] = score
            satellite["constellation"] = "oneweb"
            scored_satellites.append(satellite)
        
        # 按評分排序
        scored_satellites.sort(key=lambda x: x["handover_suitability_score"], reverse=True)
        
        return scored_satellites
    
    def _calculate_starlink_handover_score(self, satellite: Dict) -> float:
        """
        計算 Starlink 衛星換手適用性評分 (0-100)
        """
        orbit_data = satellite.get("orbit_data", {})
        timeseries = satellite.get("timeseries", [])
        config = self.starlink_scoring_config
        
        total_score = 0.0
        
        # 1. 軌道傾角適用性 (30分)
        inclination = orbit_data.get("inclination", 0)
        inclination_score = self._evaluate_starlink_inclination(inclination)
        total_score += inclination_score * config["orbital_inclination_weight"] / 100
        
        # 2. 高度適用性 (25分)  
        altitude = orbit_data.get("altitude", 0)
        altitude_score = self._evaluate_starlink_altitude(altitude)
        total_score += altitude_score * config["altitude_suitability_weight"] / 100
        
        # 3. 相位分散 (20分)
        phase_score = self._evaluate_phase_distribution(satellite, timeseries)
        total_score += phase_score * config["phase_distribution_weight"] / 100
        
        # 4. 換手頻率 (15分)
        handover_score = self._evaluate_handover_frequency(timeseries, config["orbital_period_min"])
        total_score += handover_score * config["handover_frequency_weight"] / 100
        
        # 5. 信號穩定性 (10分)
        stability_score = self._evaluate_signal_stability(orbit_data, timeseries)
        total_score += stability_score * config["signal_stability_weight"] / 100
        
        return min(100.0, max(0.0, total_score))
    
    def _calculate_oneweb_handover_score(self, satellite: Dict) -> float:
        """
        計算 OneWeb 衛星換手適用性評分 (0-100)
        """
        orbit_data = satellite.get("orbit_data", {})
        timeseries = satellite.get("timeseries", [])
        config = self.oneweb_scoring_config
        
        total_score = 0.0
        
        # 1. 軌道傾角適用性 (25分)
        inclination = orbit_data.get("inclination", 0)
        inclination_score = self._evaluate_oneweb_inclination(inclination)
        total_score += inclination_score * config["orbital_inclination_weight"] / 100
        
        # 2. 高度適用性 (25分)
        altitude = orbit_data.get("altitude", 0)
        altitude_score = self._evaluate_oneweb_altitude(altitude)
        total_score += altitude_score * config["altitude_suitability_weight"] / 100
        
        # 3. 極地覆蓋 (20分)
        polar_score = self._evaluate_polar_coverage(inclination, timeseries)
        total_score += polar_score * config["polar_coverage_weight"] / 100
        
        # 4. 軌道形狀 (20分)
        shape_score = self._evaluate_orbital_shape(orbit_data)
        total_score += shape_score * config["orbital_shape_weight"] / 100
        
        # 5. 相位分散 (10分)
        phase_score = self._evaluate_phase_distribution(satellite, timeseries)
        total_score += phase_score * config["phase_distribution_weight"] / 100
        
        return min(100.0, max(0.0, total_score))
    
    def _evaluate_starlink_inclination(self, inclination: float) -> float:
        """評估 Starlink 軌道傾角適用性 (0-100)"""
        optimal = self.starlink_scoring_config["optimal_inclination"]
        deviation = abs(inclination - optimal)
        
        if deviation <= 2:
            return 100.0  # 接近最佳傾角
        elif deviation <= 5:
            return 85.0   # 良好傾角
        elif deviation <= 10:
            return 70.0   # 可接受傾角
        else:
            return max(0.0, 50.0 - deviation * 2)  # 偏離較大
    
    def _evaluate_oneweb_inclination(self, inclination: float) -> float:
        """評估 OneWeb 軌道傾角適用性 (0-100)"""
        optimal = self.oneweb_scoring_config["optimal_inclination"]
        
        if inclination >= 85:
            return 100.0  # 極地或準極地軌道
        elif inclination >= 80:
            return 80.0   # 高傾角軌道
        elif inclination >= 70:
            return 60.0   # 中高傾角軌道
        else:
            return 30.0   # 低傾角軌道
    
    def _evaluate_starlink_altitude(self, altitude: float) -> float:
        """評估 Starlink 軌道高度適用性 (0-100)"""
        optimal = self.starlink_scoring_config["optimal_altitude"]
        deviation = abs(altitude - optimal)
        
        if deviation <= 50:
            return 100.0  # 最佳高度範圍
        elif deviation <= 100:
            return 80.0   # 良好高度範圍
        elif deviation <= 200:
            return 60.0   # 可接受高度範圍
        else:
            return max(0.0, 40.0 - deviation * 0.1)
    
    def _evaluate_oneweb_altitude(self, altitude: float) -> float:
        """評估 OneWeb 軌道高度適用性 (0-100)"""
        optimal = self.oneweb_scoring_config["optimal_altitude"]
        deviation = abs(altitude - optimal)
        
        if deviation <= 100:
            return 100.0  # 最佳高度範圍
        elif deviation <= 200:
            return 80.0   # 良好高度範圍
        elif deviation <= 300:
            return 60.0   # 可接受高度範圍
        else:
            return max(0.0, 40.0 - deviation * 0.05)
    
    def _evaluate_phase_distribution(self, satellite: Dict, timeseries: List[Dict]) -> float:
        """評估相位分散度 (0-100)"""
        if not timeseries:
            return 0.0
        
        # 計算時間分佈的均勻性
        visible_times = []
        for point in timeseries:
            elevation = point.get("elevation_deg", -90)
            if elevation >= 0:
                time_offset = point.get("time_offset_seconds", 0)
                visible_times.append(time_offset)
        
        if len(visible_times) < 2:
            return 50.0  # 單次可見，中等評分
        
        # 計算時間間隔的標準差（相位分散度）
        time_intervals = []
        for i in range(1, len(visible_times)):
            interval = visible_times[i] - visible_times[i-1]
            time_intervals.append(interval)
        
        if not time_intervals:
            return 50.0
        
        # 標準差越小，分佈越均勻，評分越高
        std_dev = statistics.stdev(time_intervals) if len(time_intervals) > 1 else 0
        max_std = 1800  # 30分鐘的秒數
        
        uniformity_score = max(0, 100 - (std_dev / max_std * 100))
        return min(100.0, uniformity_score)
    
    def _evaluate_handover_frequency(self, timeseries: List[Dict], orbital_period_min: int) -> float:
        """評估換手頻率適中性 (0-100)"""
        if not timeseries:
            return 0.0
        
        # 計算可見性變化次數
        elevation_changes = 0
        prev_visible = False
        
        for point in timeseries:
            elevation = point.get("elevation_deg", -90)
            current_visible = elevation >= 0
            
            if current_visible != prev_visible:
                elevation_changes += 1
            prev_visible = current_visible
        
        # 換手頻率評分：適中的頻率得分最高
        if elevation_changes <= 2:
            return 30.0  # 太少變化
        elif elevation_changes <= 6:
            return 100.0  # 適中變化
        elif elevation_changes <= 10:
            return 80.0   # 稍多變化
        else:
            return 50.0   # 過多變化
    
    def _evaluate_signal_stability(self, orbit_data: Dict, timeseries: List[Dict]) -> float:
        """評估信號穩定性 (0-100)"""
        # 基於軌道參數的穩定性評估
        eccentricity = orbit_data.get("eccentricity", 0)
        altitude = orbit_data.get("altitude", 0)
        
        # 圓形軌道更穩定
        eccentricity_score = max(0, 100 - eccentricity * 1000)
        
        # 適當高度更穩定
        if 400 <= altitude <= 1500:
            altitude_stability = 100.0
        else:
            altitude_stability = max(0, 100 - abs(altitude - 950) * 0.1)
        
        return (eccentricity_score + altitude_stability) / 2
    
    def _evaluate_polar_coverage(self, inclination: float, timeseries: List[Dict]) -> float:
        """評估極地覆蓋優勢 (0-100)"""
        # 高傾角軌道有極地覆蓋優勢
        if inclination >= 85:
            polar_advantage = 100.0
        elif inclination >= 70:
            polar_advantage = 80.0
        elif inclination >= 50:
            polar_advantage = 60.0
        else:
            polar_advantage = 20.0
        
        return polar_advantage
    
    def _evaluate_orbital_shape(self, orbit_data: Dict) -> float:
        """評估軌道形狀 (0-100)"""
        eccentricity = orbit_data.get("eccentricity", 0)
        
        # 近圓軌道評分更高
        if eccentricity <= 0.001:
            return 100.0  # 非常圓
        elif eccentricity <= 0.005:
            return 90.0   # 接近圓形
        elif eccentricity <= 0.01:
            return 80.0   # 略橢圓
        elif eccentricity <= 0.05:
            return 60.0   # 中等橢圓
        else:
            return 30.0   # 高橢圓
    
    def get_scoring_statistics(self, scored_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        獲取評分統計信息
        
        Returns:
            Dict: 評分統計數據
        """
        stats = {
            "scoring_configs": {
                "starlink": self.starlink_scoring_config,
                "oneweb": self.oneweb_scoring_config
            },
            "constellation_stats": {},
            "overall_stats": {}
        }
        
        all_scores = []
        
        for constellation, satellites in scored_data.items():
            if not satellites:
                continue
            
            scores = [sat.get("handover_suitability_score", 0) for sat in satellites]
            all_scores.extend(scores)
            
            stats["constellation_stats"][constellation] = {
                "count": len(satellites),
                "avg_score": round(statistics.mean(scores), 2),
                "max_score": max(scores),
                "min_score": min(scores),
                "std_dev": round(statistics.stdev(scores) if len(scores) > 1 else 0, 2),
                "top_10_percent_threshold": round(sorted(scores, reverse=True)[len(scores)//10] if len(scores) >= 10 else max(scores), 2)
            }
        
        if all_scores:
            stats["overall_stats"] = {
                "total_satellites": len(all_scores),
                "avg_score": round(statistics.mean(all_scores), 2),
                "max_score": max(all_scores),
                "min_score": min(all_scores),
                "std_dev": round(statistics.stdev(all_scores) if len(all_scores) > 1 else 0, 2)
            }
        
        return stats
    
    def select_top_satellites(self, scored_data: Dict[str, List[Dict]], selection_config: Dict[str, int]) -> Dict[str, List[Dict]]:
        """
        基於評分選擇頂級衛星
        
        Args:
            scored_data: 評分後的衛星數據
            selection_config: 選擇配置，如 {"starlink": 555, "oneweb": 134}
            
        Returns:
            Dict[str, List[Dict]]: 選擇的頂級衛星
        """
        selected_data = {}
        
        for constellation, target_count in selection_config.items():
            if constellation in scored_data:
                satellites = scored_data[constellation]
                # 按評分排序，選擇前 N 個
                selected = sorted(satellites, 
                                key=lambda x: x.get("handover_suitability_score", 0), 
                                reverse=True)[:target_count]
                selected_data[constellation] = selected
        
        return selected_data


def main():
    """測試換手適用性評分功能"""
    scorer = HandoverScorer()
    
    # 模擬地理篩選後的數據
    test_data = {
        "starlink": [
            {
                "satellite_id": "STARLINK-1007",
                "orbit_data": {
                    "altitude": 550,
                    "inclination": 53,
                    "eccentricity": 0.001,
                    "position": {"x": 1234, "y": 5678, "z": 9012}
                },
                "timeseries": [
                    {"time": "2025-08-12T12:00:00Z", "elevation_deg": 45.0, "time_offset_seconds": 0},
                    {"time": "2025-08-12T12:00:30Z", "elevation_deg": 50.0, "time_offset_seconds": 30}
                ],
                "geographic_relevance_score": 85.5
            }
        ],
        "oneweb": [
            {
                "satellite_id": "ONEWEB-0123",
                "orbit_data": {
                    "altitude": 1200,
                    "inclination": 87,
                    "eccentricity": 0.002,
                    "position": {"x": 2345, "y": 6789, "z": 123}
                },
                "timeseries": [
                    {"time": "2025-08-12T12:00:00Z", "elevation_deg": 30.0, "time_offset_seconds": 0},
                    {"time": "2025-08-12T12:00:30Z", "elevation_deg": 25.0, "time_offset_seconds": 30}
                ],
                "geographic_relevance_score": 78.2
            }
        ]
    }
    
    # 執行評分
    scored_data = scorer.apply_handover_scoring(test_data)
    stats = scorer.get_scoring_statistics(scored_data)
    
    print("換手適用性評分測試結果:")
    import json
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 測試選擇功能
    selection_config = {"starlink": 1, "oneweb": 1}
    selected = scorer.select_top_satellites(scored_data, selection_config)
    
    print("\n頂級衛星選擇結果:")
    for constellation, satellites in selected.items():
        for sat in satellites:
            print(f"{constellation}: {sat['satellite_id']} - 評分: {sat['handover_suitability_score']:.1f}")


if __name__ == "__main__":
    main()