"""
可見性時間窗口分析器 - Stage 2模組化組件

職責：
1. 分析衛星可見性時間窗口
2. 計算最佳觀測時段
3. 預測衛星過境時間
4. 提供換手決策支援數據
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

class VisibilityAnalyzer:
    """可見性時間窗口分析器 - 提供詳細的可見性分析"""
    
    def __init__(self, min_pass_duration: int = 60, max_gap_seconds: int = 120):
        """
        初始化可見性分析器
        
        Args:
            min_pass_duration: 最小有效過境時間（秒）
            max_gap_seconds: 合併相鄰窗口的最大間隔（秒）
        """
        self.logger = logging.getLogger(f"{__name__}.VisibilityAnalyzer")
        
        self.min_pass_duration = min_pass_duration
        self.max_gap_seconds = max_gap_seconds
        
        # 分析統計
        self.analysis_statistics = {
            "total_satellites_analyzed": 0,
            "total_visibility_windows": 0,
            "total_observation_time_minutes": 0.0,
            "satellites_with_valid_passes": 0,
            "average_pass_duration_minutes": 0.0,
            "best_observation_periods": []
        }
        
        self.logger.info("✅ 可見性分析器初始化完成")
        self.logger.info(f"   最小過境時間: {min_pass_duration}秒")
        self.logger.info(f"   窗口合併間隔: {max_gap_seconds}秒")
    
    def analyze_visibility_windows(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析所有衛星的可見性時間窗口
        
        Args:
            satellites: 含可見性數據的衛星列表
            
        Returns:
            詳細的可見性分析結果
        """
        self.logger.info(f"🔍 分析 {len(satellites)} 顆衛星的可見性時間窗口...")
        
        analyzed_satellites = []
        all_visibility_windows = []
        total_observation_time = 0.0
        satellites_with_passes = 0
        
        for satellite in satellites:
            try:
                # 分析單顆衛星
                analyzed_satellite = self._analyze_single_satellite_visibility(satellite)
                
                if analyzed_satellite:
                    analyzed_satellites.append(analyzed_satellite)
                    
                    # 收集統計信息
                    windows = analyzed_satellite.get("enhanced_visibility_windows", [])
                    all_visibility_windows.extend(windows)
                    
                    valid_passes = [w for w in windows if w.get("is_valid_pass", False)]
                    if valid_passes:
                        satellites_with_passes += 1
                        
                    for window in windows:
                        total_observation_time += window.get("duration_minutes", 0.0)
                        
            except Exception as e:
                self.logger.warning(f"分析衛星 {satellite.get('name', 'unknown')} 時出錯: {e}")
                continue
        
        # 全域時間窗口分析
        global_analysis = self._perform_global_visibility_analysis(all_visibility_windows)
        
        # 更新統計
        self.analysis_statistics.update({
            "total_satellites_analyzed": len(analyzed_satellites),
            "total_visibility_windows": len(all_visibility_windows),
            "total_observation_time_minutes": round(total_observation_time, 2),
            "satellites_with_valid_passes": satellites_with_passes,
            "average_pass_duration_minutes": round(
                total_observation_time / len(all_visibility_windows) if all_visibility_windows else 0, 2
            )
        })
        
        analysis_result = {
            "satellites": analyzed_satellites,
            "global_visibility_analysis": global_analysis,
            "analysis_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "min_pass_duration_seconds": self.min_pass_duration,
                "window_merge_threshold_seconds": self.max_gap_seconds,
                "total_satellites_analyzed": len(analyzed_satellites)
            },
            "analysis_statistics": self.analysis_statistics.copy()
        }
        
        self.logger.info(f"✅ 可見性分析完成: {satellites_with_passes} 顆衛星有有效過境，總觀測時間 {total_observation_time:.1f} 分鐘")
        
        return analysis_result
    
    def _analyze_single_satellite_visibility(self, satellite: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析單顆衛星的可見性特徵"""
        
        position_timeseries = satellite.get("position_timeseries", [])
        if not position_timeseries:
            return None
        
        # 檢測並合併可見性窗口
        raw_windows = self._detect_visibility_windows(position_timeseries)
        merged_windows = self._merge_close_windows(raw_windows)
        
        # 增強窗口信息
        enhanced_windows = []
        for window in merged_windows:
            enhanced_window = self._enhance_visibility_window(window, position_timeseries)
            enhanced_windows.append(enhanced_window)
        
        # 分析衛星特徵
        satellite_analysis = self._analyze_satellite_characteristics(position_timeseries, enhanced_windows)
        
        # 構建增強的衛星數據
        analyzed_satellite = satellite.copy()
        analyzed_satellite["enhanced_visibility_windows"] = enhanced_windows
        analyzed_satellite["satellite_visibility_analysis"] = satellite_analysis
        analyzed_satellite["handover_recommendations"] = self._generate_handover_recommendations(
            enhanced_windows, satellite_analysis
        )
        
        return analyzed_satellite
    
    def _detect_visibility_windows(self, position_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """檢測連續的可見性時間窗口"""
        
        windows = []
        current_window = None
        
        for i, position in enumerate(position_timeseries):
            elevation = position.get("relative_to_observer", {}).get("elevation_deg", -90)
            timestamp = position.get("timestamp", f"point_{i}")
            
            if elevation > 0:  # 可見
                if current_window is None:
                    # 開始新窗口
                    current_window = {
                        "start_index": i,
                        "start_timestamp": timestamp,
                        "start_elevation": elevation,
                        "positions": [position]
                    }
                else:
                    # 繼續當前窗口
                    current_window["positions"].append(position)
            else:  # 不可見
                if current_window is not None:
                    # 結束當前窗口
                    current_window.update({
                        "end_index": i - 1,
                        "end_timestamp": position_timeseries[i-1].get("timestamp", f"point_{i-1}"),
                        "end_elevation": position_timeseries[i-1].get("relative_to_observer", {}).get("elevation_deg", -90)
                    })
                    windows.append(current_window)
                    current_window = None
        
        # 處理序列結束時仍在可見窗口的情況
        if current_window is not None:
            last_position = position_timeseries[-1]
            current_window.update({
                "end_index": len(position_timeseries) - 1,
                "end_timestamp": last_position.get("timestamp", f"point_{len(position_timeseries)-1}"),
                "end_elevation": last_position.get("relative_to_observer", {}).get("elevation_deg", -90)
            })
            windows.append(current_window)
        
        return windows
    
    def _merge_close_windows(self, windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合併相近的可見性窗口"""
        
        if len(windows) <= 1:
            return windows
        
        merged_windows = []
        current_window = windows[0].copy()
        
        for next_window in windows[1:]:
            # 計算時間間隔（簡化版本，實際應解析時間戳）
            gap_positions = next_window["start_index"] - current_window["end_index"] - 1
            
            # 如果間隔小於閾值，合併窗口
            if gap_positions <= self.max_gap_seconds // 30:  # 假設30秒間隔
                # 合併窗口
                current_window["end_index"] = next_window["end_index"]
                current_window["end_timestamp"] = next_window["end_timestamp"] 
                current_window["end_elevation"] = next_window["end_elevation"]
                current_window["positions"].extend(next_window["positions"])
            else:
                # 間隔太大，保存當前窗口並開始新窗口
                merged_windows.append(current_window)
                current_window = next_window.copy()
        
        # 添加最後一個窗口
        merged_windows.append(current_window)
        
        return merged_windows
    
    def _enhance_visibility_window(self, window: Dict[str, Any], 
                                 full_timeseries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """增強可見性窗口信息"""
        
        positions = window["positions"]
        
        # 計算基本統計
        elevations = [pos.get("relative_to_observer", {}).get("elevation_deg", -90) for pos in positions]
        azimuths = [pos.get("relative_to_observer", {}).get("azimuth_deg", 0) for pos in positions]
        ranges = [pos.get("relative_to_observer", {}).get("range_km", 0) for pos in positions]
        
        duration_points = len(positions)
        duration_minutes = duration_points * 0.5  # 假設30秒間隔
        
        # 找到最高仰角點
        max_elevation = max(elevations) if elevations else -90
        max_elevation_index = elevations.index(max_elevation) if elevations else 0
        max_elevation_position = positions[max_elevation_index]
        
        # 計算軌跡特徵
        trajectory_analysis = self._analyze_trajectory(positions)
        
        enhanced_window = {
            **window,
            "duration_minutes": round(duration_minutes, 2),
            "duration_points": duration_points,
            "max_elevation": round(max_elevation, 2),
            "min_elevation": round(min(elevations) if elevations else -90, 2),
            "avg_elevation": round(sum(elevations) / len(elevations) if elevations else -90, 2),
            "max_elevation_timestamp": max_elevation_position.get("timestamp", "unknown"),
            "azimuth_range": {
                "start": round(azimuths[0] if azimuths else 0, 1),
                "peak": round(azimuths[max_elevation_index] if azimuths else 0, 1),
                "end": round(azimuths[-1] if azimuths else 0, 1)
            },
            "range_km": {
                "min": round(min(ranges) if ranges else 0, 1),
                "max": round(max(ranges) if ranges else 0, 1),
                "at_peak": round(ranges[max_elevation_index] if ranges else 0, 1)
            },
            "trajectory_analysis": trajectory_analysis,
            "is_valid_pass": duration_minutes >= (self.min_pass_duration / 60),
            "pass_quality": self._evaluate_pass_quality(max_elevation, duration_minutes),
            "handover_suitability": self._evaluate_handover_suitability(elevations, duration_minutes)
        }
        
        return enhanced_window
    
    def _analyze_trajectory(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析衛星軌跡特徵"""
        
        if len(positions) < 3:
            return {"trajectory_type": "insufficient_data"}
        
        # 提取仰角序列
        elevations = [pos.get("relative_to_observer", {}).get("elevation_deg", -90) for pos in positions]
        
        # 判斷軌跡類型
        mid_point = len(elevations) // 2
        first_half_trend = elevations[mid_point] - elevations[0]
        second_half_trend = elevations[-1] - elevations[mid_point]
        
        if first_half_trend > 5 and second_half_trend < -5:
            trajectory_type = "transit"  # 過境（升高後降低）
        elif first_half_trend > 2:
            trajectory_type = "rising"   # 上升
        elif second_half_trend < -2:
            trajectory_type = "setting"  # 下降
        else:
            trajectory_type = "level"    # 平穩
        
        # 計算仰角變化率
        elevation_rates = []
        for i in range(1, len(elevations)):
            rate = elevations[i] - elevations[i-1]
            elevation_rates.append(rate)
        
        return {
            "trajectory_type": trajectory_type,
            "elevation_change_total": round(elevations[-1] - elevations[0], 2),
            "max_elevation_rate": round(max(elevation_rates) if elevation_rates else 0, 2),
            "min_elevation_rate": round(min(elevation_rates) if elevation_rates else 0, 2),
            "avg_elevation_rate": round(sum(elevation_rates) / len(elevation_rates) if elevation_rates else 0, 2)
        }
    
    def _evaluate_pass_quality(self, max_elevation: float, duration_minutes: float) -> str:
        """評估過境品質"""
        
        if max_elevation >= 60 and duration_minutes >= 8:
            return "excellent"
        elif max_elevation >= 45 and duration_minutes >= 5:
            return "good"
        elif max_elevation >= 30 and duration_minutes >= 3:
            return "fair"
        elif max_elevation >= 15 and duration_minutes >= 1:
            return "poor"
        else:
            return "very_poor"
    
    def _evaluate_handover_suitability(self, elevations: List[float], duration_minutes: float) -> str:
        """評估換手適用性"""
        
        avg_elevation = sum(elevations) / len(elevations) if elevations else 0
        stable_positions = sum(1 for e in elevations if e >= 20)  # 20度以上的穩定位置
        stability_ratio = stable_positions / len(elevations) if elevations else 0
        
        if avg_elevation >= 30 and duration_minutes >= 5 and stability_ratio >= 0.6:
            return "highly_suitable"
        elif avg_elevation >= 20 and duration_minutes >= 3 and stability_ratio >= 0.4:
            return "suitable"
        elif avg_elevation >= 15 and duration_minutes >= 2:
            return "marginally_suitable"
        else:
            return "not_suitable"
    
    def _analyze_satellite_characteristics(self, position_timeseries: List[Dict[str, Any]], 
                                         windows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析衛星整體可見性特徵"""
        
        total_visible_time = sum(window.get("duration_minutes", 0) for window in windows)
        valid_passes = [w for w in windows if w.get("is_valid_pass", False)]
        
        # 計算可見性統計
        all_elevations = []
        for pos in position_timeseries:
            elevation = pos.get("relative_to_observer", {}).get("elevation_deg", -90)
            if elevation > 0:
                all_elevations.append(elevation)
        
        return {
            "total_visibility_duration_minutes": round(total_visible_time, 2),
            "number_of_passes": len(windows),
            "number_of_valid_passes": len(valid_passes),
            "longest_pass_minutes": round(max(w.get("duration_minutes", 0) for w in windows) if windows else 0, 2),
            "highest_elevation_deg": round(max(all_elevations) if all_elevations else -90, 2),
            "average_visible_elevation": round(sum(all_elevations) / len(all_elevations) if all_elevations else -90, 2),
            "visibility_efficiency": round((len(all_elevations) / len(position_timeseries)) * 100, 2) if position_timeseries else 0,
            "best_pass": max(windows, key=lambda w: w.get("max_elevation", -90)) if windows else None
        }
    
    def _generate_handover_recommendations(self, windows: List[Dict[str, Any]], 
                                         satellite_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成換手決策建議"""
        
        suitable_windows = [w for w in windows if w.get("handover_suitability") in ["highly_suitable", "suitable"]]
        
        recommendations = {
            "is_candidate_for_handover": len(suitable_windows) > 0,
            "recommended_windows": suitable_windows[:3],  # 前3個最佳窗口
            "handover_priority": "high" if len(suitable_windows) >= 2 else "medium" if suitable_windows else "low",
            "key_advantages": [],
            "potential_issues": []
        }
        
        # 分析優勢
        if satellite_analysis.get("highest_elevation_deg", -90) >= 45:
            recommendations["key_advantages"].append("高仰角過境，信號品質佳")
        
        if satellite_analysis.get("longest_pass_minutes", 0) >= 8:
            recommendations["key_advantages"].append("長時間可見，適合連續通訊")
        
        if satellite_analysis.get("visibility_efficiency", 0) >= 30:
            recommendations["key_advantages"].append("可見性效率高，覆蓋時間長")
        
        # 分析潛在問題
        if satellite_analysis.get("number_of_valid_passes", 0) <= 2:
            recommendations["potential_issues"].append("有效過境次數較少")
        
        if satellite_analysis.get("average_visible_elevation", -90) < 20:
            recommendations["potential_issues"].append("平均仰角較低，可能影響信號品質")
        
        return recommendations
    
    def _perform_global_visibility_analysis(self, all_windows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """執行全域可見性分析"""
        
        if not all_windows:
            return {
                "optimal_observation_periods": [],
                "coverage_gaps": [],
                "overall_coverage_percentage": 0.0
            }
        
        # 按時間排序窗口（簡化版本）
        sorted_windows = sorted(all_windows, key=lambda w: w.get("start_timestamp", ""))
        
        # 找到最佳觀測時段
        optimal_periods = self._identify_optimal_periods(sorted_windows)
        
        # 計算覆蓋統計
        total_observation_time = sum(window.get("duration_minutes", 0) for window in all_windows)
        
        return {
            "total_visibility_windows": len(all_windows),
            "total_observation_time_minutes": round(total_observation_time, 2),
            "optimal_observation_periods": optimal_periods,
            "average_window_duration": round(
                total_observation_time / len(all_windows) if all_windows else 0, 2
            ),
            "best_windows": sorted(all_windows, key=lambda w: w.get("max_elevation", -90), reverse=True)[:5]
        }
    
    def _identify_optimal_periods(self, sorted_windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """識別最佳觀測時段"""
        
        # 簡化實現：找到高品質的連續時段
        optimal_periods = []
        
        high_quality_windows = [w for w in sorted_windows if w.get("pass_quality") in ["excellent", "good"]]
        
        if high_quality_windows:
            # 按品質分組
            current_period = {
                "start_time": high_quality_windows[0].get("start_timestamp", ""),
                "end_time": high_quality_windows[0].get("end_timestamp", ""),
                "windows": [high_quality_windows[0]],
                "peak_elevation": high_quality_windows[0].get("max_elevation", -90)
            }
            
            for window in high_quality_windows[1:]:
                # 簡化版本：將所有高品質窗口加入同一時段
                current_period["windows"].append(window)
                current_period["end_time"] = window.get("end_timestamp", "")
                current_period["peak_elevation"] = max(
                    current_period["peak_elevation"], 
                    window.get("max_elevation", -90)
                )
            
            optimal_periods.append(current_period)
        
        return optimal_periods
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """獲取分析統計信息"""
        return self.analysis_statistics.copy()
    
    def validate_visibility_analysis(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """驗證可見性分析結果的完整性"""
        
        validation_result = {
            "passed": True,
            "total_satellites": len(analysis_result.get("satellites", [])),
            "validation_checks": {},
            "issues": []
        }
        
        satellites = analysis_result.get("satellites", [])
        
        if not satellites:
            validation_result["passed"] = False
            validation_result["issues"].append("無衛星數據進行可見性分析")
            return validation_result
        
        # 檢查增強窗口完整性
        satellites_with_windows = 0
        satellites_with_analysis = 0
        
        for sat in satellites:
            if "enhanced_visibility_windows" in sat:
                satellites_with_windows += 1
            
            if "satellite_visibility_analysis" in sat:
                satellites_with_analysis += 1
        
        validation_result["validation_checks"]["window_enhancement_check"] = {
            "satellites_with_windows": satellites_with_windows,
            "satellites_with_analysis": satellites_with_analysis,
            "passed": satellites_with_windows == len(satellites) and satellites_with_analysis == len(satellites)
        }
        
        if satellites_with_windows < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_windows} 顆衛星缺少增強可見性窗口")
        
        if satellites_with_analysis < len(satellites):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_analysis} 顆衛星缺少可見性分析")
        
        return validation_result