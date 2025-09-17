"""
可見性數據載入器 - Stage 3模組化組件

職責：
1. 從Stage 2載入可見性過濾結果
2. 解析和驗證時序數據格式
3. 按星座分組組織數據
4. 提供統一的數據訪問接口
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 🚨 Grade A要求：使用學術級仰角標準替代硬編碼
try:
    # 修復導入路徑問題
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.elevation_standards import ELEVATION_STANDARDS
    INVALID_ELEVATION = ELEVATION_STANDARDS.get_safe_default_elevation()
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ 無法載入學術標準配置，使用臨時預設值")
    INVALID_ELEVATION = -999.0  # 學術標準：使用明確的無效值標記

logger = logging.getLogger(__name__)

class VisibilityDataLoader:
    """可見性數據載入器 - 專門處理Stage 2的輸出"""
    
    def __init__(self, input_dir: str = None):
        self.logger = logging.getLogger(f"{__name__}.VisibilityDataLoader")
        
        # 自動檢測環境並設置輸入目錄
        if input_dir is None:
            if os.path.exists("/satellite-processing") or Path(".").exists():
                input_dir = "data/stage2_outputs"  # 容器環境
            else:
                input_dir = "/tmp/ntn-stack-dev/stage2_outputs"  # 開發環境
        
        self.input_dir = Path(input_dir)
        
        # 載入統計
        self.load_statistics = {
            "files_found": 0,
            "satellites_loaded": 0,
            "constellations_found": 0,
            "visibility_windows_total": 0,
            "load_errors": 0
        }
    
    def load_stage2_output(self) -> Dict[str, Any]:
        """
        載入Stage 2的可見性過濾輸出
        
        Returns:
            Stage 2的可見性數據
        """
        self.logger.info("📥 載入Stage 2可見性過濾輸出...")
        
        # 查找Stage 2輸出文件
        possible_files = [
            "satellite_visibility_output.json",
            "visibility_filter_output.json", 
            "stage2_output.json"
        ]
        
        stage2_data = None
        
        for filename in possible_files:
            input_file = self.input_dir / filename
            if input_file.exists():
                self.logger.info(f"找到Stage 2輸出文件: {input_file}")
                try:
                    with open(input_file, 'r', encoding='utf-8') as f:
                        stage2_data = json.load(f)
                    
                    self.load_statistics["files_found"] = 1
                    break
                    
                except Exception as e:
                    self.logger.error(f"載入Stage 2輸出失敗: {e}")
                    self.load_statistics["load_errors"] += 1
                    continue
        
        if stage2_data is None:
            self.logger.error(f"未找到Stage 2輸出文件於: {self.input_dir}")
            raise FileNotFoundError(f"Stage 2輸出文件不存在: {self.input_dir}")
        
        # 驗證並標準化數據格式
        validated_data = self._validate_and_normalize_stage2_data(stage2_data)
        
        self.logger.info(f"✅ Stage 2數據載入成功: {self.load_statistics['satellites_loaded']} 顆衛星")
        return validated_data
    
    def _validate_and_normalize_stage2_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證並標準化Stage 2數據格式"""
        
        if not isinstance(data, dict):
            raise ValueError("Stage 2數據格式錯誤: 必須是字典格式")
        
        # 檢查必要的數據結構
        if "data" not in data:
            raise ValueError("Stage 2數據缺少 'data' 欄位")
        
        data_section = data["data"]
        satellites = data_section.get("satellites", [])
        
        if not satellites:
            raise ValueError("Stage 2數據無衛星信息")
        
        # 標準化衛星數據並統計
        all_satellites = []
        constellation_groups = {}
        total_visibility_windows = 0
        
        for sat_data in satellites:
            # 標準化衛星數據
            normalized_sat = self._normalize_satellite_visibility_data(sat_data)
            if normalized_sat:
                all_satellites.append(normalized_sat)
                
                # 按星座分組
                constellation = normalized_sat.get("constellation", "unknown").lower()
                if constellation not in constellation_groups:
                    constellation_groups[constellation] = []
                constellation_groups[constellation].append(normalized_sat)
                
                # 統計可見性窗口
                windows = normalized_sat.get("enhanced_visibility_windows", [])
                total_visibility_windows += len(windows)
        
        self.load_statistics.update({
            "satellites_loaded": len(all_satellites),
            "constellations_found": len(constellation_groups),
            "visibility_windows_total": total_visibility_windows
        })
        
        # 返回標準化的數據結構
        return {
            "satellites": all_satellites,
            "constellation_groups": constellation_groups,
            "metadata": data.get("metadata", {}),
            "load_statistics": self.load_statistics.copy()
        }
    
    def _normalize_satellite_visibility_data(self, sat_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """標準化單顆衛星的可見性數據格式"""
        
        try:
            # 檢查必要的可見性數據
            position_timeseries = sat_data.get("position_timeseries", [])
            visibility_summary = sat_data.get("visibility_summary", {})
            
            if not position_timeseries:
                self.logger.warning(f"衛星 {sat_data.get('name', 'unknown')} 缺少位置時間序列數據")
                return None
            
            if not visibility_summary:
                self.logger.warning(f"衛星 {sat_data.get('name', 'unknown')} 缺少可見性摘要")
                return None
            
            # 提取衛星基本信息
            normalized_satellite = {
                "satellite_id": sat_data.get("satellite_id", "unknown"),
                "name": sat_data.get("name", "unknown"),
                "constellation": sat_data.get("constellation", "unknown").lower(),
                "norad_id": sat_data.get("norad_id", "unknown"),
                
                # Stage 2可見性數據
                "position_timeseries": self._enhance_position_timeseries(position_timeseries),
                "visibility_summary": visibility_summary,
                
                # 可見性窗口分析數據
                "enhanced_visibility_windows": sat_data.get("enhanced_visibility_windows", []),
                "satellite_visibility_analysis": sat_data.get("satellite_visibility_analysis", {}),
                "handover_recommendations": sat_data.get("handover_recommendations", {}),
                
                # 仰角過濾數據（如果存在）
                "elevation_filtering": sat_data.get("elevation_filtering", {}),
                
                # Stage 2元數據
                "stage2_metadata": sat_data.get("stage2_processing", {})
            }
            
            return normalized_satellite
            
        except Exception as e:
            self.logger.error(f"標準化衛星可見性數據失敗 {sat_data.get('name', 'unknown')}: {e}")
            return None
    
    def _enhance_position_timeseries(self, position_timeseries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """增強位置時間序列數據用於動畫處理"""
        
        enhanced_timeseries = []
        
        for i, pos in enumerate(position_timeseries):
            try:
                # 基本位置信息
                enhanced_point = {
                    "time_index": i,
                    "timestamp": pos.get("timestamp", f"point_{i}"),
                    "latitude": pos.get("latitude", 0.0),
                    "longitude": pos.get("longitude", 0.0),
                    "altitude_km": pos.get("altitude_km", 0.0),
                    "velocity_kmps": pos.get("velocity_kmps", 0.0)
                }
                
                # 相對觀測者的數據
                relative_to_observer = pos.get("relative_to_observer", {})
                if relative_to_observer:
                    enhanced_point["relative_to_observer"] = {
                        # 🚨 Grade A要求：使用學術級仰角標準替代硬編碼
                        "elevation_deg": relative_to_observer.get("elevation_deg", INVALID_ELEVATION),
                        "azimuth_deg": relative_to_observer.get("azimuth_deg", 0),
                        "range_km": relative_to_observer.get("range_km", 0),
                        "is_visible": relative_to_observer.get("is_visible", False)
                    }
                
                # 如果有ECI坐標，保留
                if "eci" in pos:
                    enhanced_point["eci"] = pos["eci"]
                
                # 如果有仰角品質數據，保留
                if "elevation_quality" in pos:
                    enhanced_point["elevation_quality"] = pos["elevation_quality"]
                
                # 如果有ITU-R標準符合性，保留
                if "meets_itu_standard" in pos:
                    enhanced_point["meets_itu_standard"] = pos["meets_itu_standard"]
                
                enhanced_timeseries.append(enhanced_point)
                
            except Exception as e:
                self.logger.warning(f"增強位置點 {i} 時出錯: {e}")
                continue
        
        return enhanced_timeseries
    
    def get_satellites_by_constellation(self, data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """按星座分組衛星數據"""
        return data.get("constellation_groups", {})
    
    def get_visibility_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """獲取可見性統計信息"""
        
        satellites = data.get("satellites", [])
        constellation_groups = data.get("constellation_groups", {})
        
        # 計算總體統計
        total_satellites = len(satellites)
        satellites_with_windows = len([s for s in satellites if s.get("enhanced_visibility_windows")])
        
        total_windows = sum(
            len(s.get("enhanced_visibility_windows", [])) for s in satellites
        )
        
        total_observation_time = sum(
            s.get("satellite_visibility_analysis", {}).get("total_visibility_duration_minutes", 0)
            for s in satellites
        )
        
        # 按星座統計
        constellation_stats = {}
        for const_name, const_satellites in constellation_groups.items():
            constellation_stats[const_name] = {
                "satellite_count": len(const_satellites),
                "satellites_with_windows": len([s for s in const_satellites if s.get("enhanced_visibility_windows")]),
                "total_windows": sum(len(s.get("enhanced_visibility_windows", [])) for s in const_satellites),
                "total_observation_minutes": sum(
                    s.get("satellite_visibility_analysis", {}).get("total_visibility_duration_minutes", 0)
                    for s in const_satellites
                )
            }
        
        return {
            "total_satellites": total_satellites,
            "satellites_with_windows": satellites_with_windows,
            "total_visibility_windows": total_windows,
            "total_observation_time_minutes": round(total_observation_time, 2),
            "constellation_breakdown": constellation_stats,
            "visibility_efficiency": round((satellites_with_windows / total_satellites * 100) if total_satellites > 0 else 0, 2)
        }
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """獲取載入統計信息"""
        return self.load_statistics.copy()
    
    def validate_visibility_data_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證可見性數據的完整性"""
        
        validation_result = {
            "overall_valid": True,
            "total_satellites": len(data.get("satellites", [])),
            "validation_checks": {},
            "issues": []
        }
        
        satellites = data.get("satellites", [])
        
        if not satellites:
            validation_result["overall_valid"] = False
            validation_result["issues"].append("無衛星可見性數據")
            return validation_result
        
        # 檢查位置時間序列完整性
        satellites_with_timeseries = 0
        satellites_with_sufficient_points = 0
        
        for sat in satellites:
            timeseries = sat.get("position_timeseries", [])
            
            if timeseries:
                satellites_with_timeseries += 1
                
                if len(timeseries) >= 50:  # 至少50個位置點
                    satellites_with_sufficient_points += 1
        
        validation_result["validation_checks"]["timeseries_completeness_check"] = {
            "satellites_with_timeseries": satellites_with_timeseries,
            "satellites_with_sufficient_points": satellites_with_sufficient_points,
            "passed": satellites_with_timeseries == len(satellites)
        }
        
        if satellites_with_timeseries < len(satellites):
            validation_result["overall_valid"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_timeseries} 顆衛星缺少位置時間序列")
        
        # 檢查可見性窗口分析
        satellites_with_windows = 0
        satellites_with_analysis = 0
        
        for sat in satellites:
            windows = sat.get("enhanced_visibility_windows", [])
            analysis = sat.get("satellite_visibility_analysis", {})
            
            if windows:
                satellites_with_windows += 1
            
            if analysis:
                satellites_with_analysis += 1
        
        validation_result["validation_checks"]["visibility_analysis_check"] = {
            "satellites_with_windows": satellites_with_windows,
            "satellites_with_analysis": satellites_with_analysis,
            "passed": satellites_with_analysis >= (satellites_with_windows * 0.8)  # 80%的衛星應有分析
        }
        
        if satellites_with_analysis < (satellites_with_windows * 0.8):
            validation_result["overall_valid"] = False
            validation_result["issues"].append("可見性分析數據不完整")
        
        return validation_result