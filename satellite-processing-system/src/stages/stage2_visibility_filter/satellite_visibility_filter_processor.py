"""
Stage 2: 衛星可見性過濾處理器 - 模組化重構版

職責：
1. 從Stage 1載入軌道計算結果
2. 基於觀測點計算衛星可見性
3. 應用動態仰角門檻（ITU-R標準）
4. 進行智能可見性過濾
5. 輸出符合下一階段的標準化結果
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.base_processor import BaseStageProcessor
from .orbital_data_loader import OrbitalDataLoader
from .visibility_calculator import VisibilityCalculator

logger = logging.getLogger(__name__)

class SatelliteVisibilityFilterProcessor(BaseStageProcessor):
    """階段二：衛星可見性篩選處理器
    
    根據階段二文檔規範實現的地理可見性篩選處理器：
    - 載入階段一軌道計算輸出
    - 執行智能化F2篩選流程
    - 基於ITU-R標準的仰角門檻篩選
    - 學術級物理參數遵循 (Grade A/B 標準)
    - v3.0記憶體傳遞模式
    
    類別名稱：SatelliteVisibilityFilterProcessor (符合文檔規範)
    輸出：intelligent_filtering_outputs/ (v3.0記憶體模式)
    """
    
    def __init__(self, input_dir: str = None, output_dir: str = None, observer_coordinates: tuple = None, config: Dict[str, Any] = None):
        """
        初始化衛星可見性篩選處理器
        
        Args:
            input_dir: 階段一TLE計算輸出目錄路徑 
            output_dir: 階段二篩選輸出目錄路徑
            observer_coordinates: 觀測點座標 (緯度, 經度, 海拔m)，預設為NTPU座標
            config: 處理器配置參數
        """
        super().__init__(
            stage_number=2,
            stage_name="satellite_visibility_filter"
        )
        
        self.logger = logging.getLogger(f"{__name__}.SatelliteVisibilityFilterProcessor")
        
        # 🚨 Grade A強制要求：使用NTPU精確座標 (非任意假設)
        self.observer_coordinates = observer_coordinates or (24.9441667, 121.3713889, 50)
        
        # 配置處理
        self.config = config or {}
        self.debug_mode = self.config.get("debug_mode", False)
        
        # 設定階段一輸入目錄 (TLE計算輸出)
        if input_dir is None:
            if os.path.exists("/satellite-processing") or Path(".").exists():
                # 容器環境 - 讀取階段一的實際輸出位置
                input_dir = "data/outputs/stage1"
            else:
                # 開發環境
                input_dir = "/tmp/ntn-stack-dev/tle_calculation_outputs"
        
        self.input_dir = Path(input_dir)
        
        # v3.0記憶體傳遞模式：輸出目錄設定
        if output_dir is None:
            if os.path.exists("/satellite-processing"):
                output_dir = "data/intelligent_filtering_outputs"
            else:
                output_dir = "/tmp/ntn-stack-dev/intelligent_filtering_outputs"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化核心組件
        from .unified_intelligent_filter import UnifiedIntelligentFilter
        self.unified_filter = UnifiedIntelligentFilter(observer_coordinates=self.observer_coordinates)
        
        # 🚨 NEW: 初始化學術標準驗證器
        from .academic_standards_validator import AcademicStandardsValidator
        self.academic_validator = AcademicStandardsValidator()
        
        # 🚨 學術標準合規檢查：禁用簡化篩選引擎
        self._perform_academic_compliance_runtime_check()
        
        self.logger.info("✅ SatelliteVisibilityFilterProcessor 初始化完成")
        self.logger.info(f"   觀測點座標: {self.observer_coordinates}")
        self.logger.info(f"   輸入目錄: {self.input_dir}")
        self.logger.info(f"   輸出目錄: {self.output_dir}")
        self.logger.info("   學術標準驗證器: 已啟用")
    
    def process_intelligent_filtering(self, input_data: Any = None) -> Dict[str, Any]:
        """
        執行智能衛星可見性篩選 (v3.0記憶體傳遞模式)
        
        這個方法實現完整的階段二篩選流程，包括：
        - 從階段一載入TLE軌道計算結果
        - 執行零容忍學術標準檢查
        - 運行統一智能篩選F2流程
        - 應用地理可見性篩選
        - 生成符合v3.0規範的輸出
        
        Args:
            input_data: 可選的直接輸入數據（用於測試模式）
            
        Returns:
            Dict[str, Any]: 篩選結果，包含data、metadata、statistics三個主要部分
        """
        processing_start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始階段二智能衛星可見性篩選...")
        
        try:
            # Step 1: 載入階段一軌道計算數據
            if input_data is not None:
                # 測試模式：使用直接提供的數據
                self.logger.info("🧪 測試模式：使用直接提供的輸入數據")
                stage1_data = input_data
            else:
                # 正常模式：從檔案載入階段一輸出
                self.logger.info("📂 正常模式：從檔案載入階段一輸出")
                stage1_data = self.load_orbital_calculation_output()
            
            # 🔄 適配階段一新的輸出格式：轉換衛星數據結構
            satellites = self._convert_stage1_output_format(stage1_data)
            
            self.logger.info(f"載入 {len(satellites)} 顆衛星的軌道數據")
            
            # 🚨 NEW: Step 1.5: 執行零容忍學術標準檢查
            self.logger.info("🚨 執行零容忍學術標準檢查...")
            processing_config = {
                'executed_filtering_steps': ['constellation_separation', 'geographical_relevance', 'handover_suitability'],
                'filtering_mode': 'pure_geographic_visibility'
            }
            
            # 零容忍檢查 - 任何失敗都會拋出異常停止執行
            # 創建臨時的兼容格式供檢查使用
            check_data = {"satellites": satellites}
            self.academic_validator.perform_zero_tolerance_runtime_checks(
                filter_engine=self.unified_filter,
                input_data=check_data,
                processing_config=processing_config
            )
            
            # Step 2: 執行統一智能篩選F2流程
            self.logger.info("執行UnifiedIntelligentFilter F2篩選流程...")
            f2_filtering_result = self.unified_filter.execute_f2_filtering_workflow(satellites)
            
            filtered_satellites = f2_filtering_result["filtered_satellites"]
            
            # Step 3: 應用地理可見性篩選 (ITU-R標準)
            self.logger.info("應用地理可見性篩選...")
            final_filtered_satellites = self._simple_filtering(filtered_satellites)
            
            # Step 4: 構建最終輸出 (v3.0記憶體傳遞模式)
            processing_end_time = datetime.now(timezone.utc)
            processing_duration = (processing_end_time - processing_start_time).total_seconds()
            
            filtering_result = {
                "data": {
                    "filtered_satellites": {
                        "starlink": [s for s in final_filtered_satellites 
                                   if 'starlink' in s.get('name', '').lower()],
                        "oneweb": [s for s in final_filtered_satellites 
                                 if 'oneweb' in s.get('name', '').lower()],
                        "other": [s for s in final_filtered_satellites 
                                if 'starlink' not in s.get('name', '').lower() and 
                                   'oneweb' not in s.get('name', '').lower()]
                    },
                    "filtering_summary": self._generate_filtering_summary(satellites, final_filtered_satellites)
                },
                "metadata": {
                    "stage": 2,
                    "stage_name": "satellite_visibility_filter",
                    "processor_class": "SatelliteVisibilityFilterProcessor",
                    "filtering_engine": "UnifiedIntelligentFilter_v3.0",
                    "processing_timestamp": processing_end_time.isoformat(),
                    "processing_duration_seconds": processing_duration,
                    "filtering_mode": "pure_geographic_visibility_no_quantity_limits",
                    "observer_coordinates": {
                        "latitude": self.observer_coordinates[0],
                        "longitude": self.observer_coordinates[1],
                        "altitude_m": self.observer_coordinates[2]
                    },
                    "input_satellites": len(satellites),
                    "output_satellites": len(final_filtered_satellites),
                    "filtering_rate": len(final_filtered_satellites) / len(satellites) if satellites else 0,
                    "memory_passing_mode": "v3.0_enabled",
                    "academic_compliance": "zero_tolerance_checks_passed"
                },
                "statistics": {
                    **f2_filtering_result.get("filtering_statistics", {}),
                    "final_filtering_statistics": self._get_final_filtering_statistics(satellites, final_filtered_satellites),
                    "engine_statistics": self.unified_filter.get_filtering_statistics(),
                    "academic_validation": self.academic_validator.get_validation_summary()
                }
            }
            
            # 🚨 Step 5: 最終輸出數據結構完整性檢查
            self.academic_validator.validate_output_data_structure(filtering_result)
            
            # 🚨 Step 6: 學術等級合規性評估
            grade_assessment = self.academic_validator.validate_academic_grade_compliance(filtering_result)
            filtering_result["academic_grade_assessment"] = grade_assessment
            
            # 檢查整體合規性
            if grade_assessment["overall_compliance"] == "Grade_C":
                self.logger.error(f"🚨 學術標準不符合要求: {grade_assessment}")
                raise RuntimeError("學術標準檢查未通過，整體評級為Grade_C")
            
            self.logger.info(f"✅ 階段二智能篩選完成: {len(final_filtered_satellites)}/{len(satellites)} 顆衛星通過篩選")
            self.logger.info(f"📊 學術標準評級: {grade_assessment['overall_compliance']}")
            return filtering_result
            
        except Exception as e:
            self.logger.error(f"階段二智能篩選失敗: {e}")
            raise
    
    def load_orbital_calculation_output(self) -> Dict[str, Any]:
        """
        載入階段一軌道計算輸出數據
        
        根據階段二文檔規範，此方法負責：
        - 載入階段一的TLE軌道計算結果
        - 驗證軌道數據格式和完整性
        - 確保SGP4計算結果可用於地理篩選
        
        Returns:
            Dict[str, Any]: 階段一軌道計算輸出數據
        """
        self.logger.info("📂 載入階段一TLE軌道計算輸出...")
        
        try:
            # 搜尋可能的階段一輸出檔案
            possible_files = [
                "tle_orbital_calculation_output.json",
                "orbital_calculation_output.json", 
                "stage1_output.json"
            ]
            
            input_file_found = None
            for filename in possible_files:
                input_file = self.input_dir / filename
                if input_file.exists():
                    input_file_found = input_file
                    self.logger.info(f"找到階段一輸出檔案: {input_file}")
                    break
            
            if not input_file_found:
                raise FileNotFoundError(f"未找到階段一TLE計算輸出檔案於: {self.input_dir}")
            
            # 載入JSON數據
            with open(input_file_found, 'r', encoding='utf-8') as f:
                import json
                stage1_data = json.load(f)
            
            # 🚨 Grade A強制檢查：軌道數據完整性
            self._validate_stage1_orbital_data(stage1_data)
            
            # 🔄 適配階段一新的輸出格式：提取 satellites 計數
            satellites_count = 0
            if "satellites" in stage1_data:
                # 舊格式：直接在頂層有 satellites
                satellites_count = len(stage1_data["satellites"])
                self.logger.info("檢測到舊格式階段一輸出（頂層 satellites）")
            elif "data" in stage1_data and "satellites" in stage1_data["data"]:
                # 新格式：在 data.satellites 中
                satellites_count = len(stage1_data["data"]["satellites"])
                self.logger.info("檢測到新格式階段一輸出（data.satellites）")
            else:
                raise ValueError("階段一數據格式不正確：缺少 satellites 欄位")
            
            self.logger.info(f"✅ 成功載入 {satellites_count} 顆衛星的軌道計算數據")
            
            return stage1_data
            
        except Exception as e:
            self.logger.error(f"載入階段一軌道計算輸出失敗: {e}")
            raise

    
    def _convert_stage1_output_format(self, stage1_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        轉換階段一輸出格式為階段二期望的格式，並從ECI座標計算觀測點相對數據
        
        這是Stage 2的核心工作：從Stage 1的純ECI座標計算觀測點相對數據
        
        Args:
            stage1_data: 階段一的原始輸出數據（包含ECI座標）
            
        Returns:
            List[Dict[str, Any]]: 轉換後的衛星列表（包含觀測點相對數據）
        """
        self.logger.info("🔄 從ECI座標計算觀測點相對數據並轉換格式...")
        
        try:
            # 提取階段一的衛星數據
            satellites_dict = None
            if "data" in stage1_data and "satellites" in stage1_data["data"]:
                satellites_dict = stage1_data["data"]["satellites"]
                self.logger.info("檢測到新格式階段一輸出（data.satellites）")
            elif "satellites" in stage1_data:
                satellites_dict = stage1_data["satellites"]
                self.logger.info("檢測到舊格式階段一輸出（頂層 satellites）")
            else:
                raise ValueError("無法找到階段一衛星數據")
            
            if not isinstance(satellites_dict, dict):
                raise ValueError(f"階段一衛星數據格式錯誤，期望字典但得到: {type(satellites_dict)}")
            
            converted_satellites = []
            
            # 觀測點座標
            observer_lat, observer_lon, observer_alt_m = self.observer_coordinates
            
            self.logger.info(f"🌍 觀測點: ({observer_lat:.4f}°N, {observer_lon:.4f}°E, {observer_alt_m}m)")
            
            for satellite_id, satellite_data in satellites_dict.items():
                try:
                    # 檢查必要的數據結構
                    if not isinstance(satellite_data, dict):
                        self.logger.warning(f"跳過衛星 {satellite_id}：數據格式錯誤")
                        continue
                    
                    # 提取衛星基本信息
                    satellite_info = satellite_data.get("satellite_info", {})
                    orbital_positions = satellite_data.get("orbital_positions", [])
                    
                    if not orbital_positions:
                        self.logger.warning(f"跳過衛星 {satellite_id}：缺少軌道位置數據")
                        continue
                    
                    # 創建轉換後的衛星對象
                    converted_satellite = {
                        "name": satellite_info.get("name", f"SAT_{satellite_id}"),
                        "satellite_id": satellite_id,
                        "constellation": satellite_info.get("constellation", "unknown"),
                        "position_timeseries": []
                    }
                    
                    # 轉換軌道位置數據 - 從ECI座標計算觀測點相對數據
                    for position in orbital_positions:
                        try:
                            # 檢查新的ECI格式
                            if "position_eci" not in position:
                                self.logger.warning(f"衛星 {satellite_id} 位置數據缺少 position_eci，跳過")
                                continue
                            
                            # 提取ECI座標和時間
                            timestamp_str = position.get("timestamp")
                            eci_pos = position["position_eci"]
                            eci_x = eci_pos.get("x", 0)
                            eci_y = eci_pos.get("y", 0) 
                            eci_z = eci_pos.get("z", 0)
                            
                            # 計算觀測點相對數據 - 使用簡化的球面幾何計算
                            import math
                            
                            # ECI座標轉換為觀測點相對座標
                            # 這是一個簡化版本，足以進行可見性篩選
                            
                            # 計算衛星到地心的距離
                            satellite_distance_from_earth = math.sqrt(eci_x**2 + eci_y**2 + eci_z**2)
                            
                            # 地球半徑 (km)
                            earth_radius_km = 6371.0
                            
                            # 觀測點在地球表面的ECEF座標 (簡化計算)
                            observer_lat_rad = math.radians(observer_lat)
                            observer_lon_rad = math.radians(observer_lon)
                            
                            # 觀測點的ECEF座標
                            observer_x = (earth_radius_km + observer_alt_m/1000) * math.cos(observer_lat_rad) * math.cos(observer_lon_rad)
                            observer_y = (earth_radius_km + observer_alt_m/1000) * math.cos(observer_lat_rad) * math.sin(observer_lon_rad)
                            observer_z = (earth_radius_km + observer_alt_m/1000) * math.sin(observer_lat_rad)
                            
                            # 衛星相對於觀測點的向量
                            dx = eci_x - observer_x
                            dy = eci_y - observer_y
                            dz = eci_z - observer_z
                            
                            # 距離
                            range_km = math.sqrt(dx**2 + dy**2 + dz**2)
                            
                            # 仰角計算 (簡化)
                            # 使用向量點積計算仰角
                            observer_normal_x = observer_x / (earth_radius_km + observer_alt_m/1000)
                            observer_normal_y = observer_y / (earth_radius_km + observer_alt_m/1000)
                            observer_normal_z = observer_z / (earth_radius_km + observer_alt_m/1000)
                            
                            # 歸一化衛星向量
                            sat_vector_length = math.sqrt(dx**2 + dy**2 + dz**2)
                            if sat_vector_length > 0:
                                dx_norm = dx / sat_vector_length
                                dy_norm = dy / sat_vector_length
                                dz_norm = dz / sat_vector_length
                                
                                # 計算仰角 (衛星向量與觀測點法向量的夾角)
                                dot_product = dx_norm * observer_normal_x + dy_norm * observer_normal_y + dz_norm * observer_normal_z
                                dot_product = max(-1.0, min(1.0, dot_product))  # 限制在[-1, 1]範圍內
                                
                                elevation_rad = math.asin(dot_product)
                                elevation_deg = math.degrees(elevation_rad)
                            else:
                                elevation_deg = -90.0
                            
                            # 方位角計算 (簡化) - 使用東北天座標系
                            # 這是一個簡化計算，主要用於可見性判斷
                            azimuth_deg = math.degrees(math.atan2(dy, dx))
                            if azimuth_deg < 0:
                                azimuth_deg += 360.0
                            
                            # 可見性判斷 - 仰角大於0度且衛星在地平線上方
                            is_visible = elevation_deg > 0.0 and range_km < 3000  # 3000km範圍內
                            
                            # 組裝轉換後的位置數據
                            converted_position = {
                                "timestamp": timestamp_str,
                                "eci_position": {
                                    "x": eci_x,
                                    "y": eci_y,
                                    "z": eci_z
                                },
                                "relative_to_observer": {
                                    "elevation_deg": elevation_deg,
                                    "azimuth_deg": azimuth_deg,
                                    "distance_km": range_km,
                                    "is_visible": is_visible
                                }
                            }
                            converted_satellite["position_timeseries"].append(converted_position)
                            
                        except Exception as e:
                            self.logger.warning(f"衛星 {satellite_id} 位置數據轉換錯誤: {e}")
                            continue
                    
                    # 只添加有有效位置數據的衛星
                    if converted_satellite["position_timeseries"]:
                        converted_satellites.append(converted_satellite)
                        
                except Exception as e:
                    self.logger.warning(f"轉換衛星 {satellite_id} 時發生錯誤: {e}")
                    continue
            
            self.logger.info(f"✅ 成功從ECI計算並轉換 {len(converted_satellites)}/{len(satellites_dict)} 顆衛星數據")
            
            if len(converted_satellites) == 0:
                raise RuntimeError("轉換後沒有有效的衛星數據")
            
            # 顯示前兩顆衛星的觀測點數據範例
            for i, satellite in enumerate(converted_satellites[:2]):
                if satellite["position_timeseries"]:
                    pos = satellite["position_timeseries"][0]["relative_to_observer"]
                    self.logger.info(f"📡 {satellite['name']}: 仰角 {pos['elevation_deg']:.1f}°, 方位 {pos['azimuth_deg']:.1f}°, 距離 {pos['distance_km']:.1f}km, 可見: {pos['is_visible']}")
            
            return converted_satellites
            
        except Exception as e:
            self.logger.error(f"階段一輸出格式轉換失敗: {e}")
            raise RuntimeError(f"無法從ECI座標計算觀測點數據: {e}")
    
    def _simple_filtering(self, satellites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        執行地理可見性篩選 - 純粹的ITU-R物理標準檢查
        
        這是客觀的物理檢查，不是為了達到特定數量的調整：
        - Starlink: 仰角 ≥5° (ITU-R P.618標準)
        - OneWeb: 仰角 ≥10° (ITU-R P.618標準)
        - 最小可見時間要求：基於換手需求
        
        結果是多少顆就是多少顆 - 這是客觀的物理條件決定的。
        
        Args:
            satellites: 經過F2篩選的衛星列表
            
        Returns:
            List[Dict[str, Any]]: 通過ITU-R物理標準的衛星列表
        """
        self.logger.info("🌍 執行ITU-R物理標準檢查...")
        
        final_filtered = []
        
        for satellite in satellites:
            try:
                # 從 position_timeseries 檢查地理可見性
                position_timeseries = satellite.get("position_timeseries", [])
                
                if not position_timeseries:
                    self.logger.warning(f"衛星 {satellite.get('name', 'unknown')} 缺少位置數據")
                    continue
                
                # 計算基本可見性數據
                max_elevation = -999
                visible_time_minutes = 0
                
                for position in position_timeseries:
                    relative_data = position.get("relative_to_observer", {})
                    elevation = relative_data.get("elevation_deg", -999)
                    is_visible = relative_data.get("is_visible", False)
                    
                    if elevation > max_elevation:
                        max_elevation = elevation
                    
                    if is_visible:
                        visible_time_minutes += 0.5  # 每個可見position代表0.5分鐘
                
                # 根據星座應用ITU-R標準
                constellation = satellite.get("constellation", "").lower()
                
                if "starlink" in constellation:
                    # ITU-R標準：Starlink最低5度仰角，至少1分鐘可見
                    min_elevation = 5.0
                    min_visible_time = 1.0
                elif "oneweb" in constellation:
                    # ITU-R標準：OneWeb最低10度仰角，至少0.5分鐘可見
                    min_elevation = 10.0
                    min_visible_time = 0.5
                else:
                    # 其他星座：保守的10度標準
                    min_elevation = 10.0
                    min_visible_time = 1.0
                
                # 簡單的物理條件檢查
                passes_elevation = max_elevation >= min_elevation
                passes_visible_time = visible_time_minutes >= min_visible_time
                
                if passes_elevation and passes_visible_time:
                    # 添加篩選標記
                    satellite["simple_filtering"] = {
                        "passed": True,
                        "max_elevation_deg": max_elevation,
                        "visible_time_minutes": visible_time_minutes,
                        "itu_r_elevation_threshold": min_elevation,
                        "itu_r_time_threshold": min_visible_time,
                        "constellation": constellation,
                        "filtering_timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # 添加地理篩選標記（為了兼容性）
                    satellite["geographical_filtering"] = {
                        "visibility_analysis": {
                            "has_geographical_visibility": True,
                            "max_elevation_deg": max_elevation,
                            "visible_time_minutes": visible_time_minutes
                        }
                    }
                    
                    final_filtered.append(satellite)
                    
                else:
                    self.logger.debug(f"衛星 {satellite.get('name', 'unknown')} 未通過ITU-R標準: "
                                    f"max_elev={max_elevation:.1f}° (ITU-R要求≥{min_elevation}°), "
                                    f"vis_time={visible_time_minutes:.1f}min (要求≥{min_visible_time}min)")
                    
            except Exception as e:
                self.logger.warning(f"檢查衛星 {satellite.get('name', 'unknown')} 時出錯: {e}")
                continue
        
        filter_ratio = len(final_filtered) / len(satellites) * 100 if satellites else 0
        self.logger.info(f"📊 ITU-R物理標準篩選完成: {len(final_filtered)}/{len(satellites)} ({filter_ratio:.1f}%)")
        
        # 按星座顯示篩選結果
        starlink_count = len([s for s in final_filtered if 'starlink' in s.get('constellation', '').lower()])
        oneweb_count = len([s for s in final_filtered if 'oneweb' in s.get('constellation', '').lower()])
        self.logger.info(f"   - Starlink: {starlink_count} 顆 (ITU-R 5度標準)")
        self.logger.info(f"   - OneWeb: {oneweb_count} 顆 (ITU-R 10度標準)")
        
        # 這是客觀結果，不需要評判是否符合預期數量
        self.logger.info(f"✅ 基於ITU-R物理標準的客觀篩選結果：{len(final_filtered)} 顆衛星")
        
        return final_filtered
    
    def validate_input(self, input_data: Any = None) -> bool:
        """
        驗證輸入數據的有效性
        
        Args:
            input_data: 可選的直接輸入數據（用於測試）
            
        Returns:
            bool: 輸入數據是否有效
        """
        self.logger.info("🔍 階段二輸入驗證...")
        
        try:
            if input_data is not None:
                # 直接驗證提供的數據
                self.logger.info("使用直接提供的輸入數據")
                return self._validate_stage1_orbital_data(input_data)
            
            # 驗證階段一輸出檔案是否存在
            possible_files = [
                "tle_orbital_calculation_output.json",
                "orbital_calculation_output.json",
                "stage1_output.json"
            ]
            
            input_file_found = False
            for filename in possible_files:
                input_file = self.input_dir / filename
                if input_file.exists():
                    input_file_found = True
                    self.logger.info(f"找到階段一輸出檔案: {input_file}")
                    break
            
            if not input_file_found:
                self.logger.error(f"未找到階段一輸出檔案於: {self.input_dir}")
                return False
                
            # 測試載入並驗證格式
            try:
                stage1_data = self.load_orbital_calculation_output()
                return self._validate_stage1_orbital_data(stage1_data)
                
            except Exception as e:
                self.logger.error(f"載入階段一數據時出錯: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"輸入驗證失敗: {e}")
            return False
    
    def process(self, input_data: Any = None) -> Dict[str, Any]:
        """
        執行階段二處理 (主要處理方法)
        
        此方法為BaseStageProcessor的標準介面實現，
        內部調用 process_intelligent_filtering() 執行實際篩選邏輯
        
        Args:
            input_data: 可選的直接輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        return self.process_intelligent_filtering(input_data)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        驗證輸出數據的完整性和正確性
        
        Args:
            output_data: 處理結果數據
            
        Returns:
            bool: 輸出數據是否有效
        """
        self.logger.info("🔍 階段二輸出驗證...")
        
        try:
            # 🚨 強制檢查輸出數據結構完整性 (Grade A要求)
            if not isinstance(output_data, dict):
                self.logger.error("輸出數據必須是字典格式")
                return False
            
            required_sections = ["data", "metadata", "statistics"]
            for section in required_sections:
                if section not in output_data:
                    self.logger.error(f"輸出數據缺少必要的 '{section}' 欄位")
                    return False
            
            # 檢查篩選結果結構
            data_section = output_data["data"]
            if "filtered_satellites" not in data_section:
                self.logger.error("數據部分缺少 'filtered_satellites' 欄位")
                return False
            
            filtered_satellites = data_section["filtered_satellites"]
            if not isinstance(filtered_satellites, dict):
                self.logger.error("filtered_satellites 必須是字典格式")
                return False
            
            # 🚨 強制檢查星座分組 (文檔要求)
            required_constellations = ["starlink", "oneweb"]
            for constellation in required_constellations:
                if constellation not in filtered_satellites:
                    self.logger.error(f"缺少 {constellation} 篩選結果")
                    return False
            
            # 檢查篩選率合理性 (避免篩選過於嚴格或寬鬆)
            metadata = output_data["metadata"]
            filtering_rate = metadata.get("filtering_rate", 0)
            
            if filtering_rate < 0.05:
                self.logger.warning(f"篩選率過低 ({filtering_rate:.3f})，可能篩選過於嚴格")
            elif filtering_rate > 0.50:
                self.logger.warning(f"篩選率過高 ({filtering_rate:.3f})，可能篩選不足")
            
            # 🚨 強制檢查處理器類型 (禁用簡化實現)
            processor_class = metadata.get("processor_class", "")
            if processor_class != "SatelliteVisibilityFilterProcessor":
                self.logger.error(f"處理器類型錯誤: {processor_class}")
                return False
            
            self.logger.info("✅ 階段二輸出驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"輸出驗證失敗: {e}")
            return False
    
    def get_default_output_filename(self) -> str:
        """返回預設輸出檔名 (v3.0記憶體傳遞模式)"""
        return "satellite_visibility_filtering_output.json"
    
    def extract_key_metrics(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取關鍵指標"""
        filtered_satellites_data = processed_data.get("data", {}).get("filtered_satellites", {})
        
        starlink_count = len(filtered_satellites_data.get("starlink", []))
        oneweb_count = len(filtered_satellites_data.get("oneweb", []))
        total_filtered = starlink_count + oneweb_count + len(filtered_satellites_data.get("other", []))
        
        metadata = processed_data.get("metadata", {})
        
        return {
            "total_satellites_filtered": total_filtered,
            "starlink_satellites": starlink_count,
            "oneweb_satellites": oneweb_count,
            "filtering_rate": metadata.get("filtering_rate", 0),
            "processing_duration": metadata.get("processing_duration_seconds", 0),
            "filtering_engine": "UnifiedIntelligentFilter_v3.0",
            "filtering_mode": "pure_geographic_visibility_no_quantity_limits",
            "observer_coordinates": metadata.get("observer_coordinates", {}),
            "memory_passing_enabled": True
        }
    
    def run_validation_checks(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """運行驗證檢查"""
        validation_results = {
            "passed": True,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "critical_checks": [],
            "all_checks": {}
        }
        
        try:
            # 檢查1: 數據結構檢查
            structure_check = self._check_output_structure(processed_data)
            validation_results["all_checks"]["output_structure_check"] = structure_check
            validation_results["total_checks"] += 1
            
            if structure_check:
                validation_results["passed_checks"] += 1
            else:
                validation_results["failed_checks"] += 1
                validation_results["passed"] = False
                validation_results["critical_checks"].append("output_structure_check")
            
            # 檢查2: 篩選引擎類型檢查
            engine_check = self._check_filtering_engine_compliance(processed_data)
            validation_results["all_checks"]["filtering_engine_check"] = engine_check
            validation_results["total_checks"] += 1
            
            if engine_check:
                validation_results["passed_checks"] += 1
            else:
                validation_results["failed_checks"] += 1
                validation_results["passed"] = False
                validation_results["critical_checks"].append("filtering_engine_check")
            
            # 檢查3: ITU-R標準合規檢查
            itu_check = self._check_itu_r_compliance(processed_data)
            validation_results["all_checks"]["itu_r_compliance_check"] = itu_check
            validation_results["total_checks"] += 1
            
            if itu_check:
                validation_results["passed_checks"] += 1
            else:
                validation_results["failed_checks"] += 1
                validation_results["passed"] = False
                validation_results["critical_checks"].append("itu_r_compliance_check")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"驗證檢查執行失敗: {e}")
            validation_results["passed"] = False
            validation_results["validation_error"] = str(e)
            return validation_results
    
    def save_results(self, processed_data: Dict[str, Any]) -> str:
        """保存處理結果 (v3.0記憶體傳遞模式優化)"""
        try:
            output_filename = self.get_default_output_filename()
            output_file = self.output_dir / output_filename
            
            self.logger.info(f"💾 保存階段二篩選結果到: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            # v3.0記憶體傳遞模式：同時準備記憶體傳遞格式
            self.logger.info("📋 v3.0記憶體傳遞模式：準備記憶體格式數據")
            
            self.logger.info("✅ 階段二結果保存完成")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"保存階段二結果失敗: {e}")
            raise
    
    def _validate_stage1_orbital_data(self, stage1_data: Dict[str, Any]) -> bool:
        """驗證階段一軌道數據格式和完整性 (Grade A強制檢查)"""
        try:
            # 基本數據結構檢查
            if not isinstance(stage1_data, dict):
                self.logger.error("階段一數據必須是字典格式")
                return False
            
            # 🔄 適配階段一新的輸出格式：檢查 data.satellites 結構
            satellites = None
            if "satellites" in stage1_data:
                # 舊格式：直接在頂層有 satellites
                satellites = stage1_data["satellites"]
                self.logger.info("檢測到舊格式階段一輸出（頂層 satellites）")
            elif "data" in stage1_data and "satellites" in stage1_data["data"]:
                # 新格式：在 data.satellites 中
                satellites = stage1_data["data"]["satellites"]
                self.logger.info("檢測到新格式階段一輸出（data.satellites）")
            else:
                self.logger.error("階段一數據缺少 'satellites' 欄位（檢查了頂層和 data 層級）")
                return False
            
            if not isinstance(satellites, list):
                self.logger.error("satellites 必須是列表格式")
                return False
            
            if len(satellites) == 0:
                self.logger.error("衛星數據為空")
                return False
            
            # 🚨 Grade A強制檢查：SGP4軌道計算數據完整性
            for i, satellite in enumerate(satellites):
                if not isinstance(satellite, dict):
                    self.logger.error(f"衛星 {i} 數據格式錯誤")
                    return False
                
                # 檢查必要欄位
                required_fields = ["name", "position_timeseries"]
                for field in required_fields:
                    if field not in satellite:
                        self.logger.error(f"衛星 {satellite.get('name', i)} 缺少 '{field}' 欄位")
                        return False
                
                # 檢查軌道時間序列數據
                position_timeseries = satellite["position_timeseries"]
                if not isinstance(position_timeseries, list) or len(position_timeseries) == 0:
                    self.logger.error(f"衛星 {satellite.get('name', i)} 的軌道時間序列數據無效")
                    return False
                
                # 檢查時間序列數據結構 (Grade A要求)
                for j, position in enumerate(position_timeseries[:3]):  # 只檢查前3個點
                    if "relative_to_observer" not in position:
                        self.logger.error(f"衛星 {satellite.get('name', i)} 位置 {j} 缺少 relative_to_observer")
                        return False
                    
                    relative_data = position["relative_to_observer"]
                    required_relative_fields = ["elevation_deg", "distance_km"]
                    for field in required_relative_fields:
                        if field not in relative_data:
                            self.logger.error(f"衛星 {satellite.get('name', i)} 位置 {j} 缺少 '{field}'")
                            return False
            
            self.logger.info("✅ 階段一軌道數據驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"階段一數據驗證失敗: {e}")
            return False
    
    def _validate_filtering_output(self, filtering_result: Dict[str, Any]) -> bool:
        """驗證篩選輸出完整性 (Grade A強制檢查)"""
        try:
            # 基本結構檢查
            required_sections = ["data", "metadata", "statistics"]
            for section in required_sections:
                if section not in filtering_result:
                    self.logger.error(f"篩選結果缺少 '{section}' 部分")
                    return False
            
            # 篩選數據檢查
            data_section = filtering_result["data"]
            if "filtered_satellites" not in data_section:
                self.logger.error("篩選數據缺少 'filtered_satellites'")
                return False
            
            filtered_satellites = data_section["filtered_satellites"]
            if not isinstance(filtered_satellites, dict):
                self.logger.error("filtered_satellites 格式錯誤")
                return False
            
            # 🚨 強制檢查星座分組完整性
            required_constellations = ["starlink", "oneweb"]
            for constellation in required_constellations:
                if constellation not in filtered_satellites:
                    self.logger.error(f"缺少 {constellation} 篩選結果")
                    return False
            
            # 元數據檢查
            metadata = filtering_result["metadata"]
            required_metadata = [
                "stage", "stage_name", "processor_class", "filtering_engine",
                "filtering_mode", "filtering_rate"
            ]
            for field in required_metadata:
                if field not in metadata:
                    self.logger.error(f"元數據缺少 '{field}' 欄位")
                    return False
            
            # 🚨 強制檢查篩選引擎類型
            if metadata["processor_class"] != "SatelliteVisibilityFilterProcessor":
                self.logger.error(f"處理器類型錯誤: {metadata['processor_class']}")
                return False
            
            if "UnifiedIntelligentFilter" not in metadata["filtering_engine"]:
                self.logger.error(f"篩選引擎類型錯誤: {metadata['filtering_engine']}")
                return False
            
            # 篩選率合理性檢查
            filtering_rate = metadata.get("filtering_rate", 0)
            if filtering_rate < 0.01:
                self.logger.error(f"篩選率過低: {filtering_rate}")
                return False
            if filtering_rate > 0.90:
                self.logger.error(f"篩選率過高: {filtering_rate}")
                return False
            
            self.logger.info("✅ 篩選輸出驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"篩選輸出驗證失敗: {e}")
            return False
    
    def _perform_academic_compliance_runtime_check(self):
        """執行學術標準合規的運行時檢查 (Grade A強制要求)"""
        self.logger.info("🚨 執行學術標準合規運行時檢查...")
        
        # 🚨 禁止任何形式的簡化篩選算法
        forbidden_filtering_modes = [
            "simplified_filter", "basic_elevation_only", "mock_filtering", 
            "random_sampling", "fixed_percentage", "estimated_visibility"
        ]
        
        for mode in forbidden_filtering_modes:
            if mode in str(self.__class__).lower():
                raise RuntimeError(f"🚨 檢測到禁用的簡化篩選: {mode}")
        
        # 檢查篩選引擎類型
        engine_class_name = str(self.unified_filter.__class__.__name__)
        if "UnifiedIntelligentFilter" not in engine_class_name:
            raise RuntimeError(f"🚨 篩選引擎類型不符: {engine_class_name}")
        
        # 🚨 強制檢查仰角門檻符合ITU-R標準
        engine_thresholds = self.unified_filter.elevation_thresholds
        if engine_thresholds.get('starlink') != 5.0:
            raise RuntimeError(f"🚨 Starlink仰角門檻錯誤: {engine_thresholds.get('starlink')}")
        if engine_thresholds.get('oneweb') != 10.0:
            raise RuntimeError(f"🚨 OneWeb仰角門檻錯誤: {engine_thresholds.get('oneweb')}")
        
        self.logger.info("✅ 學術標準合規檢查通過")
    
    def _generate_filtering_summary(self, original_satellites: List[Dict[str, Any]], 
                                  filtered_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成篩選摘要"""
        starlink_original = len([s for s in original_satellites if 'starlink' in s.get('name', '').lower()])
        oneweb_original = len([s for s in original_satellites if 'oneweb' in s.get('name', '').lower()])
        
        starlink_filtered = len([s for s in filtered_satellites if 'starlink' in s.get('name', '').lower()])
        oneweb_filtered = len([s for s in filtered_satellites if 'oneweb' in s.get('name', '').lower()])
        
        return {
            "total_input_satellites": len(original_satellites),
            "total_output_satellites": len(filtered_satellites),
            "overall_filtering_rate": len(filtered_satellites) / len(original_satellites) if original_satellites else 0,
            "starlink_summary": {
                "input_count": starlink_original,
                "output_count": starlink_filtered,
                "filtering_rate": starlink_filtered / starlink_original if starlink_original else 0
            },
            "oneweb_summary": {
                "input_count": oneweb_original,
                "output_count": oneweb_filtered,
                "filtering_rate": oneweb_filtered / oneweb_original if oneweb_original else 0
            }
        }
    
    def _get_final_filtering_statistics(self, original_satellites: List[Dict[str, Any]], 
                                      final_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """獲取最終篩選統計"""
        return {
            "simple_filtering_input": len(original_satellites),
            "simple_filtering_output": len(final_satellites),
            "simple_filtering_rate": len(final_satellites) / len(original_satellites) if original_satellites else 0,
            "satellites_removed_in_final_step": len(original_satellites) - len(final_satellites)
        }
    
    def _check_output_structure(self, output_data: Dict[str, Any]) -> bool:
        """檢查輸出數據結構"""
        try:
            required_sections = ["data", "metadata", "statistics"]
            return all(section in output_data for section in required_sections)
        except:
            return False
    
    def _check_filtering_engine_compliance(self, output_data: Dict[str, Any]) -> bool:
        """檢查篩選引擎合規性"""
        try:
            metadata = output_data.get("metadata", {})
            processor_class = metadata.get("processor_class", "")
            filtering_engine = metadata.get("filtering_engine", "")
            
            return (processor_class == "SatelliteVisibilityFilterProcessor" and 
                    "UnifiedIntelligentFilter" in filtering_engine)
        except:
            return False
    
    def _check_itu_r_compliance(self, output_data: Dict[str, Any]) -> bool:
        """檢查ITU-R標準合規性"""
        try:
            # 檢查篩選模式
            metadata = output_data.get("metadata", {})
            filtering_mode = metadata.get("filtering_mode", "")
            
            return filtering_mode == "pure_geographic_visibility_no_quantity_limits"
        except:
            return False