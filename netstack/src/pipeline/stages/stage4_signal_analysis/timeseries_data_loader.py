"""
時間序列數據載入器 - Stage 4模組化組件

職責：
1. 載入Stage 3時間序列預處理輸出
2. 驗證時間序列數據完整性
3. 提取衛星動畫和可見性信息
4. 準備供信號分析使用的數據格式
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TimseriesDataLoader:
    """時間序列數據載入器 - 載入Stage 3輸出供信號分析使用"""
    
    def __init__(self):
        """初始化時間序列數據載入器"""
        self.logger = logging.getLogger(f"{__name__}.TimseriesDataLoader")
        
        # 載入統計
        self.load_statistics = {
            "total_satellites_loaded": 0,
            "total_timeseries_points": 0,
            "constellations_loaded": 0,
            "animation_frames_loaded": 0,
            "data_quality_score": 0.0
        }
        
        self.logger.info("✅ 時間序列數據載入器初始化完成")
    
    def load_stage3_output(self) -> Dict[str, Any]:
        """
        載入Stage 3時間序列預處理輸出
        
        Returns:
            Dict包含時間序列數據和動畫信息
        """
        self.logger.info("📥 載入Stage 3時間序列預處理輸出...")
        
        # 嘗試多個可能的Stage 3輸出位置
        possible_paths = [
            Path("/app/data/stage3_outputs/timeseries_preprocessing_output.json"),
            Path("/app/data/timeseries_preprocessing_output.json"),
            Path("/app/data/leo_outputs/timeseries_preprocessing_output.json")
        ]
        
        stage3_data = None
        loaded_from = None
        
        for file_path in possible_paths:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        stage3_data = json.load(f)
                    loaded_from = file_path
                    break
                except Exception as e:
                    self.logger.warning(f"無法讀取 {file_path}: {e}")
                    continue
        
        if not stage3_data:
            self.logger.error("❌ 未找到Stage 3時間序列輸出文件")
            raise FileNotFoundError("Stage 3時間序列預處理輸出文件不存在")
        
        self.logger.info(f"✅ 成功載入Stage 3數據: {loaded_from}")
        
        # 驗證數據格式
        validation_result = self.validate_timeseries_data_format(stage3_data)
        
        if not validation_result["format_valid"]:
            self.logger.error("Stage 3數據格式驗證失敗:")
            for issue in validation_result["format_issues"]:
                self.logger.error(f"  - {issue}")
            raise ValueError("Stage 3時間序列數據格式無效")
        
        # 統計載入信息
        self._update_load_statistics(stage3_data)
        
        return stage3_data
    
    def validate_timeseries_data_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證時間序列數據格式完整性
        
        Args:
            data: Stage 3輸出數據
            
        Returns:
            驗證結果字典
        """
        validation_result = {
            "format_valid": True,
            "format_issues": [],
            "data_quality_metrics": {}
        }
        
        # 檢查基本結構
        required_sections = ["data", "metadata"]
        for section in required_sections:
            if section not in data:
                validation_result["format_issues"].append(f"缺少必要的 {section} 欄位")
                validation_result["format_valid"] = False
        
        if not validation_result["format_valid"]:
            return validation_result
        
        data_section = data["data"]
        
        # 檢查時間序列數據
        if "timeseries_data" not in data_section:
            validation_result["format_issues"].append("缺少時間序列數據")
            validation_result["format_valid"] = False
        else:
            timeseries_data = data_section["timeseries_data"]
            satellites = timeseries_data.get("satellites", [])
            
            if not satellites:
                validation_result["format_issues"].append("時間序列數據中無衛星信息")
                validation_result["format_valid"] = False
            else:
                # 檢查衛星數據完整性
                valid_satellites = 0
                total_timeseries_points = 0
                
                for satellite in satellites:
                    if self._validate_satellite_timeseries(satellite):
                        valid_satellites += 1
                        enhanced_timeseries = satellite.get("enhanced_timeseries", [])
                        total_timeseries_points += len(enhanced_timeseries)
                
                validation_result["data_quality_metrics"] = {
                    "valid_satellites": valid_satellites,
                    "total_satellites": len(satellites),
                    "total_timeseries_points": total_timeseries_points,
                    "validity_rate": valid_satellites / len(satellites) if satellites else 0
                }
        
        # 檢查動畫數據
        if "animation_data" not in data_section:
            validation_result["format_issues"].append("缺少動畫數據")
            validation_result["format_valid"] = False
        else:
            animation_data = data_section["animation_data"]
            required_animation_components = ["global_timeline", "constellation_animations"]
            
            for component in required_animation_components:
                if component not in animation_data:
                    validation_result["format_issues"].append(f"動畫數據缺少 {component} 組件")
                    validation_result["format_valid"] = False
        
        return validation_result
    
    def _validate_satellite_timeseries(self, satellite: Dict[str, Any]) -> bool:
        """驗證單顆衛星的時間序列數據"""
        required_fields = ["satellite_id", "name", "constellation"]
        
        for field in required_fields:
            if field not in satellite:
                return False
        
        # 檢查時間序列數據存在
        enhanced_timeseries = satellite.get("enhanced_timeseries", [])
        if len(enhanced_timeseries) < 10:  # 至少需要10個時間點
            return False
        
        # 檢查時間序列點的基本結構
        for point in enhanced_timeseries[:3]:  # 檢查前3個點
            required_point_fields = ["timestamp", "position", "visibility"]
            for field in required_point_fields:
                if field not in point:
                    return False
        
        return True
    
    def extract_signal_analysis_data(self, stage3_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        從Stage 3數據中提取供信號分析使用的信息
        
        Args:
            stage3_data: Stage 3完整輸出
            
        Returns:
            適合信號分析的數據結構
        """
        self.logger.info("🔄 提取信號分析所需數據...")
        
        data_section = stage3_data.get("data", {})
        timeseries_data = data_section.get("timeseries_data", {})
        animation_data = data_section.get("animation_data", {})
        
        satellites = timeseries_data.get("satellites", [])
        
        # 轉換為信號分析友善的格式
        signal_ready_data = {
            "satellites": [],
            "metadata": {
                "source_stage": 3,
                "data_format": "signal_analysis_ready",
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_satellites": len(satellites)
            }
        }
        
        for satellite in satellites:
            # 提取關鍵信息供信號計算使用
            signal_satellite = {
                "satellite_id": satellite.get("satellite_id"),
                "name": satellite.get("name"),
                "constellation": satellite.get("constellation"),
                "norad_id": satellite.get("norad_id"),
                
                # 時間序列位置數據
                "timeseries_positions": self._extract_position_timeseries(satellite),
                
                # 可見性信息
                "visibility_windows": self._extract_visibility_windows(satellite),
                
                # 軌道參數 (如果存在)
                "orbital_parameters": satellite.get("orbital_parameters", {}),
                
                # 來源時間序列點數
                "timeseries_point_count": len(satellite.get("enhanced_timeseries", []))
            }
            
            signal_ready_data["satellites"].append(signal_satellite)
        
        # 添加動畫相關的全局信息
        global_timeline = animation_data.get("global_timeline", {})
        signal_ready_data["metadata"]["animation_timeline"] = {
            "start_time": global_timeline.get("start_time"),
            "end_time": global_timeline.get("end_time"),
            "total_timepoints": global_timeline.get("total_timepoints", 0)
        }
        
        self.logger.info(f"✅ 信號分析數據提取完成: {len(signal_ready_data['satellites'])} 顆衛星")
        
        return signal_ready_data
    
    def _extract_position_timeseries(self, satellite: Dict[str, Any]) -> List[Dict[str, Any]]:
        """從衛星時間序列中提取位置信息"""
        enhanced_timeseries = satellite.get("enhanced_timeseries", [])
        
        position_timeseries = []
        for point in enhanced_timeseries:
            position_info = {
                "timestamp": point.get("timestamp"),
                "position": point.get("position", {}),
                "velocity": point.get("velocity", {}),
                "elevation_deg": point.get("elevation_deg", 0),
                "azimuth_deg": point.get("azimuth_deg", 0),
                "range_km": point.get("range_km", 0),
                "is_visible": point.get("visibility", {}).get("is_visible", False)
            }
            position_timeseries.append(position_info)
        
        return position_timeseries
    
    def _extract_visibility_windows(self, satellite: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取可見性窗口信息"""
        # 從時間序列中構建可見性窗口
        enhanced_timeseries = satellite.get("enhanced_timeseries", [])
        
        visibility_windows = []
        current_window = None
        
        for point in enhanced_timeseries:
            is_visible = point.get("visibility", {}).get("is_visible", False)
            timestamp = point.get("timestamp")
            elevation = point.get("elevation_deg", 0)
            
            if is_visible and current_window is None:
                # 開始新的可見性窗口
                current_window = {
                    "start_time": timestamp,
                    "max_elevation_deg": elevation,
                    "visibility_points": 1
                }
            elif is_visible and current_window:
                # 繼續當前窗口
                current_window["end_time"] = timestamp
                current_window["max_elevation_deg"] = max(current_window["max_elevation_deg"], elevation)
                current_window["visibility_points"] += 1
            elif not is_visible and current_window:
                # 結束當前窗口
                if "end_time" not in current_window:
                    current_window["end_time"] = current_window["start_time"]
                
                # 計算窗口持續時間
                try:
                    start_dt = datetime.fromisoformat(current_window["start_time"].replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(current_window["end_time"].replace('Z', '+00:00'))
                    duration = (end_dt - start_dt).total_seconds() / 60  # 分鐘
                    current_window["duration_minutes"] = duration
                except:
                    current_window["duration_minutes"] = 0
                
                visibility_windows.append(current_window)
                current_window = None
        
        # 處理未結束的窗口
        if current_window:
            if "end_time" not in current_window:
                current_window["end_time"] = current_window["start_time"]
            visibility_windows.append(current_window)
        
        return visibility_windows
    
    def _update_load_statistics(self, data: Dict[str, Any]):
        """更新載入統計信息"""
        data_section = data.get("data", {})
        timeseries_data = data_section.get("timeseries_data", {})
        animation_data = data_section.get("animation_data", {})
        
        satellites = timeseries_data.get("satellites", [])
        constellation_animations = animation_data.get("constellation_animations", {})
        
        # 統計時間序列點數
        total_points = 0
        for satellite in satellites:
            enhanced_timeseries = satellite.get("enhanced_timeseries", [])
            total_points += len(enhanced_timeseries)
        
        # 統計動畫幀數
        total_frames = 0
        for const_anim in constellation_animations.values():
            keyframes = const_anim.get("keyframes", [])
            total_frames += len(keyframes)
        
        # 更新統計
        self.load_statistics.update({
            "total_satellites_loaded": len(satellites),
            "total_timeseries_points": total_points,
            "constellations_loaded": len(constellation_animations),
            "animation_frames_loaded": total_frames,
            "data_quality_score": self._calculate_data_quality_score(data)
        })
    
    def _calculate_data_quality_score(self, data: Dict[str, Any]) -> float:
        """計算數據質量分數 (0-100)"""
        score = 100.0
        
        # 檢查數據完整性
        data_section = data.get("data", {})
        if not data_section:
            return 0.0
        
        timeseries_data = data_section.get("timeseries_data", {})
        animation_data = data_section.get("animation_data", {})
        
        # 時間序列數據質量 (50%)
        satellites = timeseries_data.get("satellites", [])
        if not satellites:
            score -= 50
        else:
            # 檢查平均時間序列點數
            total_points = sum(len(s.get("enhanced_timeseries", [])) for s in satellites)
            avg_points = total_points / len(satellites)
            
            if avg_points < 50:
                score -= 25  # 時間序列點數不足
            elif avg_points < 100:
                score -= 10  # 時間序列點數偏少
        
        # 動畫數據質量 (30%)
        constellation_animations = animation_data.get("constellation_animations", {})
        if not constellation_animations:
            score -= 30
        elif len(constellation_animations) < 2:
            score -= 15  # 星座數量不足
        
        # 元數據完整性 (20%)
        metadata = data.get("metadata", {})
        required_metadata = ["stage_number", "stage_name", "processing_timestamp"]
        missing_metadata = sum(1 for field in required_metadata if field not in metadata)
        score -= (missing_metadata / len(required_metadata)) * 20
        
        return max(0.0, score)
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """獲取載入統計信息"""
        return self.load_statistics.copy()