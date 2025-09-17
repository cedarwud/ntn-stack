"""
軌道數據載入器 - Stage 2模組化組件

職責：
1. 從Stage 1載入軌道計算結果
2. 解析和驗證軌道數據格式
3. 按星座分組處理數據
4. 提供統一的數據訪問接口
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OrbitalDataLoader:
    """軌道數據載入器 - 專門處理Stage 1的輸出"""
    
    def __init__(self, input_dir: str = None):
        self.logger = logging.getLogger(f"{__name__}.OrbitalDataLoader")
        
        # 自動檢測環境並設置輸入目錄
        if input_dir is None:
            if os.path.exists("/satellite-processing") or Path(".").exists():
                input_dir = "data/stage1_outputs"  # 容器環境
            else:
                input_dir = "/tmp/ntn-stack-dev/stage1_outputs"  # 開發環境
        
        self.input_dir = Path(input_dir)
        
        # 載入統計
        self.load_statistics = {
            "files_found": 0,
            "satellites_loaded": 0,
            "constellations_found": 0,
            "load_errors": 0
        }
    
    def load_stage1_output(self) -> Dict[str, Any]:
        """
        載入Stage 1的軌道計算輸出
        
        Returns:
            Stage 1的軌道數據
        """
        self.logger.info("📥 載入Stage 1軌道計算輸出...")
        
        # 查找Stage 1輸出文件
        possible_files = [
            "orbital_calculation_output.json",
            "tle_calculation_outputs.json", 
            "stage1_output.json"
        ]
        
        stage1_data = None
        
        for filename in possible_files:
            # 🚨 v6.0修復: 使用os.path.join進行路徑拼接，避免str / str錯誤
            import os
            input_file = os.path.join(str(self.input_dir), filename)
            if os.path.exists(input_file):
                self.logger.info(f"找到Stage 1輸出文件: {input_file}")
                try:
                    with open(input_file, 'r', encoding='utf-8') as f:
                        stage1_data = json.load(f)
                    
                    self.load_statistics["files_found"] = 1
                    break
                    
                except Exception as e:
                    self.logger.error(f"載入Stage 1輸出失敗: {e}")
                    self.load_statistics["load_errors"] += 1
                    continue
        
        if stage1_data is None:
            self.logger.error(f"未找到Stage 1輸出文件於: {self.input_dir}")
            raise FileNotFoundError(f"Stage 1輸出文件不存在: {self.input_dir}")
        
        # 驗證數據格式
        validated_data = self._validate_and_normalize_stage1_data(stage1_data)

        # 🚨 v6.0 重構：提取Stage 1時間基準
        stage1_time_base = self._extract_stage1_time_base(stage1_data)
        validated_data["inherited_time_base"] = stage1_time_base

        self.logger.info(f"✅ Stage 1數據載入成功: {self.load_statistics['satellites_loaded']} 顆衛星")
        self.logger.info(f"🎯 繼承Stage 1時間基準: {stage1_time_base}")
        return validated_data
    
    def _validate_and_normalize_stage1_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證並標準化Stage 1數據格式"""
        
        if not isinstance(data, dict):
            raise ValueError("Stage 1數據格式錯誤: 必須是字典格式")
        
        # 檢查必要的數據結構
        if "data" not in data:
            raise ValueError("Stage 1數據缺少 'data' 欄位")
        
        data_section = data["data"]
        all_satellites = []
        
        # 處理新格式：按星座組織的數據
        if "constellations" in data_section:
            self.logger.info("檢測到新格式: 按星座組織的數據")
            
            for constellation_name, constellation_data in data_section["constellations"].items():
                satellites = constellation_data.get("satellites", {})
                
                for sat_id, sat_data in satellites.items():
                    # 標準化衛星數據
                    normalized_sat = self._normalize_satellite_data(sat_data, constellation_name, sat_id)
                    if normalized_sat:
                        all_satellites.append(normalized_sat)
                        
                self.load_statistics["constellations_found"] += 1
        
        # 處理舊格式：直接的衛星數組
        elif "satellites" in data_section:
            self.logger.info("檢測到舊格式: 直接的衛星數組")
            
            satellites = data_section["satellites"]
            
            if isinstance(satellites, dict):
                # 字典格式的衛星數據
                for sat_id, sat_data in satellites.items():
                    normalized_sat = self._normalize_satellite_data(
                        sat_data, 
                        sat_data.get('constellation', 'unknown'), 
                        sat_id
                    )
                    if normalized_sat:
                        all_satellites.append(normalized_sat)
            
            elif isinstance(satellites, list):
                # 列表格式的衛星數據
                for sat_data in satellites:
                    normalized_sat = self._normalize_satellite_data(
                        sat_data,
                        sat_data.get('constellation', 'unknown'),
                        sat_data.get('satellite_id', 'unknown')
                    )
                    if normalized_sat:
                        all_satellites.append(normalized_sat)
        
        else:
            raise ValueError("Stage 1數據格式錯誤: 缺少 'constellations' 或 'satellites' 欄位")
        
        self.load_statistics["satellites_loaded"] = len(all_satellites)
        
        # 返回標準化的數據結構
        return {
            "satellites": all_satellites,
            "metadata": data.get("metadata", {}),
            "load_statistics": self.load_statistics.copy()
        }
    
    def _normalize_satellite_data(self, sat_data: Dict[str, Any], 
                                 constellation: str, sat_id: str) -> Optional[Dict[str, Any]]:
        """標準化單顆衛星的數據格式"""
        
        try:
            # 檢查必要的軌道位置數據
            orbital_positions = sat_data.get("orbital_positions", [])
            
            if not orbital_positions:
                self.logger.warning(f"衛星 {sat_id} 缺少軌道位置數據")
                return None
            
            # 提取衛星基本信息
            satellite_info = sat_data.get("satellite_info", {})
            
            normalized_satellite = {
                "satellite_id": sat_id,
                "name": satellite_info.get("name", sat_id),
                "constellation": constellation.lower(),
                "norad_id": satellite_info.get("norad_id", sat_id),
                
                # 軌道數據
                "orbital_positions": orbital_positions,
                "orbital_elements": sat_data.get("orbital_elements", {}),
                
                # 時間序列數據（用於可見性計算）
                "position_timeseries": self._convert_to_position_timeseries(orbital_positions),
                
                # 原始數據（保留用於高級計算）
                "tle_data": {
                    "line1": satellite_info.get("tle_line1"),
                    "line2": satellite_info.get("tle_line2")
                },
                
                # Stage 1元數據
                "stage1_metadata": sat_data.get("calculation_metadata", {})
            }
            
            return normalized_satellite
            
        except Exception as e:
            self.logger.error(f"標準化衛星數據失敗 {sat_id}: {e}")
            return None
    
    def _convert_to_position_timeseries(self, orbital_positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """將軌道位置轉換為可見性計算所需的時間序列格式"""
        
        timeseries = []
        
        for i, pos in enumerate(orbital_positions):
            try:
                # 基本位置信息
                timeseries_point = {
                    "timestamp": pos.get("timestamp", f"point_{i}"),
                    "latitude": pos.get("latitude", 0.0),
                    "longitude": pos.get("longitude", 0.0),
                    "altitude_km": pos.get("altitude_km", 0.0),
                    "velocity_kmps": pos.get("velocity_kmps", 0.0)
                }
                
                # 如果有ECI坐標，添加它們
                if "eci" in pos:
                    timeseries_point["eci"] = pos["eci"]
                
                # 如果已經有相對於觀測者的數據，保留它們
                if "relative_to_observer" in pos:
                    timeseries_point["relative_to_observer"] = pos["relative_to_observer"]
                elif "elevation" in pos:
                    # 轉換舊格式的仰角數據
                    timeseries_point["relative_to_observer"] = {
                        "elevation_deg": pos.get("elevation", 0.0),
                        "azimuth_deg": pos.get("azimuth", 0.0),
                        "range_km": pos.get("range_km", 0.0)
                    }
                
                timeseries.append(timeseries_point)
                
            except Exception as e:
                self.logger.warning(f"轉換位置點 {i} 時出錯: {e}")
                continue
        
        return timeseries
    
    def get_satellites_by_constellation(self, data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """按星座分組衛星數據"""
        
        constellation_groups = {}
        
        for sat in data.get("satellites", []):
            constellation = sat.get("constellation", "unknown").lower()
            
            if constellation not in constellation_groups:
                constellation_groups[constellation] = []
            
            constellation_groups[constellation].append(sat)
        
        return constellation_groups
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """獲取載入統計信息"""
        return self.load_statistics.copy()
    
    def validate_orbital_data_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證軌道數據的完整性"""
        
        validation_result = {
            "overall_valid": True,
            "total_satellites": len(data.get("satellites", [])),
            "validation_checks": {},
            "issues": []
        }
        
        satellites = data.get("satellites", [])
        
        if not satellites:
            validation_result["overall_valid"] = False
            validation_result["issues"].append("無衛星數據")
            return validation_result
        
        # 檢查軌道位置數據完整性
        satellites_with_positions = 0
        satellites_with_sufficient_positions = 0
        
        for sat in satellites:
            positions = sat.get("orbital_positions", [])
            
            if positions:
                satellites_with_positions += 1
                
                if len(positions) >= 100:  # 至少100個位置點
                    satellites_with_sufficient_positions += 1
        
        validation_result["validation_checks"]["position_data_check"] = {
            "satellites_with_positions": satellites_with_positions,
            "satellites_with_sufficient_positions": satellites_with_sufficient_positions,
            "passed": satellites_with_positions == len(satellites)
        }
        
        if satellites_with_positions < len(satellites):
            validation_result["overall_valid"] = False
            validation_result["issues"].append(f"{len(satellites) - satellites_with_positions} 顆衛星缺少位置數據")
        
        # 檢查時間序列連續性
        time_continuity_issues = 0
        
        for sat in satellites:
            timeseries = sat.get("position_timeseries", [])
            if len(timeseries) > 1:
                # 簡單檢查前幾個時間點
                for i in range(1, min(5, len(timeseries))):
                    prev_ts = timeseries[i-1].get("timestamp", "")
                    curr_ts = timeseries[i].get("timestamp", "")
                    
                    if curr_ts <= prev_ts:
                        time_continuity_issues += 1
                        break
        
        validation_result["validation_checks"]["time_continuity_check"] = {
            "satellites_with_issues": time_continuity_issues,
            "passed": time_continuity_issues == 0
        }
        
        if time_continuity_issues > 0:
            validation_result["overall_valid"] = False
            validation_result["issues"].append(f"{time_continuity_issues} 顆衛星時間序列不連續")

        return validation_result

    def _extract_stage1_time_base(self, stage1_data: Dict[str, Any]) -> str:
        """
        從Stage 1 metadata提取計算基準時間

        v6.0 重構：確保Stage 2正確繼承Stage 1的時間基準
        """
        try:
            metadata = stage1_data.get("metadata", {})

            # 優先使用TLE epoch時間
            tle_epoch_time = metadata.get("tle_epoch_time")
            calculation_base_time = metadata.get("calculation_base_time")

            if tle_epoch_time:
                self.logger.info(f"🎯 使用Stage 1 TLE epoch時間: {tle_epoch_time}")
                return tle_epoch_time
            elif calculation_base_time:
                self.logger.info(f"🎯 使用Stage 1計算基準時間: {calculation_base_time}")
                return calculation_base_time
            else:
                # 檢查data section中的metadata
                data_section = stage1_data.get("data", {})
                if isinstance(data_section, dict) and "metadata" in data_section:
                    data_metadata = data_section["metadata"]
                    tle_epoch_time = data_metadata.get("tle_epoch_time")
                    calculation_base_time = data_metadata.get("calculation_base_time")

                    if tle_epoch_time:
                        self.logger.info(f"🎯 從data section使用TLE epoch時間: {tle_epoch_time}")
                        return tle_epoch_time
                    elif calculation_base_time:
                        self.logger.info(f"🎯 從data section使用計算基準時間: {calculation_base_time}")
                        return calculation_base_time

                # 如果都找不到，這是一個嚴重問題
                self.logger.error("❌ Stage 1 metadata缺失時間基準信息")
                self.logger.error(f"可用metadata欄位: {list(metadata.keys())}")
                if isinstance(data_section, dict) and "metadata" in data_section:
                    self.logger.error(f"data.metadata欄位: {list(data_section['metadata'].keys())}")

                raise ValueError("Stage 1 metadata缺失時間基準信息，無法執行時間基準繼承")

        except Exception as e:
            self.logger.error(f"❌ 提取Stage 1時間基準失敗: {e}")
            raise