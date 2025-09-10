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

class Stage2Processor(BaseStageProcessor):
    """Stage 2: 衛星可見性過濾處理器 - 模組化實現"""
    
    def __init__(self, input_dir: str = None, output_dir: str = None, observer_coordinates: tuple = None, config: Dict[str, Any] = None):
        """
        初始化Stage 2處理器
        
        Args:
            input_dir: Stage 1輸出目錄路徑 
            output_dir: Stage 2輸出目錄路徑
            observer_coordinates: 觀測點座標 (緯度, 經度, 海拔m)
            config: 配置參數
        """
        super().__init__(
            stage_number=2,
            stage_name="visibility_filter"
        )
        
        self.logger = logging.getLogger(f"{__name__}.Stage2Processor")
        
        # 預設觀測點：NTPU座標 (24.9441667, 121.3713889, 50m)
        self.observer_coordinates = observer_coordinates or (24.9441667, 121.3713889, 50)
        
        # 配置處理
        self.config = config or {}
        self.debug_mode = self.config.get("debug_mode", False)
        
        # 設置Stage 1輸入目錄
        if input_dir is None:
            from pathlib import Path
            if os.path.exists("/satellite-processing") or Path(".").exists():
                # 容器環境
                input_dir = "data/stage1_outputs"
            else:
                # 開發環境
                input_dir = "/tmp/ntn-stack-dev/stage1_outputs"
        
        self.input_dir = Path(input_dir)
        
        # 初始化組件
        self.orbital_data_loader = OrbitalDataLoader(input_dir=str(self.input_dir))
        self.visibility_calculator = VisibilityCalculator(observer_coordinates=self.observer_coordinates)
        
        self.logger.info("✅ Stage2Processor 初始化完成")
        self.logger.info(f"   觀測點座標: {self.observer_coordinates}")
    
    def validate_input(self, input_data: Any = None) -> bool:
        """
        驗證輸入數據的有效性
        
        Args:
            input_data: 可選的直接輸入數據（用於測試）
            
        Returns:
            bool: 輸入數據是否有效
        """
        self.logger.info("🔍 Stage 2 輸入驗證...")
        
        try:
            if input_data is not None:
                # 直接驗證提供的數據
                self.logger.info("使用直接提供的輸入數據")
                return self._validate_stage1_output_format(input_data)
            
            # 驗證Stage 1輸出文件是否存在
            possible_files = [
                "orbital_calculation_output.json",
                "tle_calculation_outputs.json",
                "stage1_output.json"
            ]
            
            input_file_found = False
            for filename in possible_files:
                input_file = self.input_dir / filename
                if input_file.exists():
                    input_file_found = True
                    self.logger.info(f"找到Stage 1輸出文件: {input_file}")
                    break
            
            if not input_file_found:
                self.logger.error(f"未找到Stage 1輸出文件於: {self.input_dir}")
                return False
                
            # 測試載入並驗證格式
            try:
                stage1_data = self.orbital_data_loader.load_stage1_output()
                return self._validate_stage1_output_format(stage1_data)
                
            except Exception as e:
                self.logger.error(f"載入Stage 1數據時出錯: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"輸入驗證失敗: {e}")
            return False
    
    def process(self, input_data: Any = None) -> Dict[str, Any]:
        """
        執行Stage 2可見性過濾處理
        
        Args:
            input_data: 可選的直接輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        self.logger.info("🔭 開始執行Stage 2可見性過濾處理...")
        processing_start_time = datetime.now(timezone.utc)
        
        try:
            # 步驟1: 載入Stage 1軌道數據
            if input_data is not None:
                self.logger.info("使用直接提供的輸入數據")
                stage1_data = input_data
            else:
                self.logger.info("從檔案系統載入Stage 1輸出數據")
                stage1_data = self.orbital_data_loader.load_stage1_output()
            
            satellites = stage1_data.get("satellites", [])
            self.logger.info(f"載入 {len(satellites)} 顆衛星的軌道數據")
            
            # 步驟2: 計算衛星可見性
            self.logger.info("計算所有衛星的可見性...")
            visibility_results = self.visibility_calculator.calculate_satellite_visibility(satellites)
            
            # 步驟3: 應用可見性過濾
            filtered_satellites = self._apply_visibility_filtering(visibility_results["satellites"])
            
            # 步驟4: 構建最終輸出
            processing_end_time = datetime.now(timezone.utc)
            processing_duration = (processing_end_time - processing_start_time).total_seconds()
            
            result = {
                "data": {
                    "satellites": filtered_satellites,
                    "visibility_summary": self._generate_visibility_summary(filtered_satellites)
                },
                "metadata": {
                    "stage": 2,
                    "stage_name": "visibility_filter",
                    "processing_timestamp": processing_end_time.isoformat(),
                    "processing_duration_seconds": processing_duration,
                    "observer_coordinates": {
                        "latitude": self.observer_coordinates[0],
                        "longitude": self.observer_coordinates[1],
                        "altitude_m": self.observer_coordinates[2]
                    },
                    "input_satellites": len(satellites),
                    "output_satellites": len(filtered_satellites),
                    "visibility_calculation_method": "spherical_geometry"
                },
                "statistics": {
                    **self.orbital_data_loader.get_load_statistics(),
                    **self.visibility_calculator.get_calculation_statistics(),
                    "visibility_filtering": self._get_filtering_statistics(satellites, filtered_satellites)
                }
            }
            
            self.logger.info(f"✅ Stage 2處理完成: {len(filtered_satellites)}/{len(satellites)} 顆衛星通過可見性過濾")
            return result
            
        except Exception as e:
            self.logger.error(f"Stage 2處理失敗: {e}")
            raise
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        驗證輸出數據的完整性和正確性
        
        Args:
            output_data: 處理結果數據
            
        Returns:
            bool: 輸出數據是否有效
        """
        self.logger.info("🔍 Stage 2 輸出驗證...")
        
        try:
            # 檢查基本數據結構
            if not isinstance(output_data, dict):
                self.logger.error("輸出數據必須是字典格式")
                return False
            
            required_sections = ["data", "metadata", "statistics"]
            for section in required_sections:
                if section not in output_data:
                    self.logger.error(f"輸出數據缺少必要的 '{section}' 欄位")
                    return False
            
            # 驗證數據部分
            data_section = output_data["data"]
            if "satellites" not in data_section:
                self.logger.error("數據部分缺少 'satellites' 欄位")
                return False
            
            satellites = data_section["satellites"]
            if not isinstance(satellites, list):
                self.logger.error("衛星數據必須是列表格式")
                return False
            
            # 驗證衛星可見性數據完整性
            visibility_validation = self.visibility_calculator.validate_visibility_results(
                {"satellites": satellites}
            )
            
            if not visibility_validation["passed"]:
                self.logger.error("衛星可見性數據驗證失敗")
                for issue in visibility_validation["issues"]:
                    self.logger.error(f"  - {issue}")
                return False
            
            # 驗證元數據
            metadata = output_data["metadata"]
            required_metadata = ["stage", "processing_timestamp", "observer_coordinates"]
            for field in required_metadata:
                if field not in metadata:
                    self.logger.error(f"元數據缺少 '{field}' 欄位")
                    return False
            
            self.logger.info("✅ Stage 2輸出驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"輸出驗證失敗: {e}")
            return False
    
    def _validate_stage1_output_format(self, data: Dict[str, Any]) -> bool:
        """驗證Stage 1輸出數據格式"""
        try:
            # 使用orbital_data_loader的驗證功能
            validation_result = self.orbital_data_loader.validate_orbital_data_completeness(data)
            
            if not validation_result["overall_valid"]:
                self.logger.error("Stage 1數據驗證失敗")
                for issue in validation_result["issues"]:
                    self.logger.error(f"  - {issue}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Stage 1數據格式驗證失敗: {e}")
            return False
    
    def _apply_visibility_filtering(self, satellites_with_visibility: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """應用可見性過濾邏輯"""
        self.logger.info("🔍 應用可見性過濾...")
        
        filtered_satellites = []
        
        for satellite in satellites_with_visibility:
            try:
                visibility_summary = satellite.get("visibility_summary", {})
                visible_points = visibility_summary.get("visible_points", 0)
                
                # 過濾條件：至少要有可見位置點
                if visible_points > 0:
                    filtered_satellites.append(satellite)
                    
            except Exception as e:
                self.logger.warning(f"過濾衛星 {satellite.get('name', 'unknown')} 時出錯: {e}")
                continue
        
        self.logger.info(f"可見性過濾完成: {len(filtered_satellites)}/{len(satellites_with_visibility)} 顆衛星通過")
        return filtered_satellites
    
    def _generate_visibility_summary(self, filtered_satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成總體可見性摘要"""
        if not filtered_satellites:
            return {
                "total_satellites": 0,
                "satellites_with_visibility": 0,
                "total_visibility_windows": 0,
                "average_visibility_percentage": 0.0,
                "max_elevation_overall": -90.0
            }
        
        total_windows = 0
        total_visibility_percentages = []
        max_elevation_overall = -90.0
        
        for satellite in filtered_satellites:
            summary = satellite.get("visibility_summary", {})
            
            windows = summary.get("visibility_windows", [])
            total_windows += len(windows)
            
            visibility_percentage = summary.get("visibility_percentage", 0.0)
            total_visibility_percentages.append(visibility_percentage)
            
            max_elevation = summary.get("max_elevation", -90.0)
            max_elevation_overall = max(max_elevation_overall, max_elevation)
        
        avg_visibility = sum(total_visibility_percentages) / len(total_visibility_percentages) if total_visibility_percentages else 0
        
        return {
            "total_satellites": len(filtered_satellites),
            "satellites_with_visibility": len(filtered_satellites),
            "total_visibility_windows": total_windows,
            "average_visibility_percentage": round(avg_visibility, 2),
            "max_elevation_overall": round(max_elevation_overall, 2)
        }
    
    def _get_filtering_statistics(self, original_satellites: List[Dict], filtered_satellites: List[Dict]) -> Dict[str, Any]:
        """獲取過濾統計信息"""
        return {
            "input_satellite_count": len(original_satellites),
            "output_satellite_count": len(filtered_satellites),
            "filtering_ratio": round(len(filtered_satellites) / len(original_satellites) * 100, 2) if original_satellites else 0,
            "satellites_filtered_out": len(original_satellites) - len(filtered_satellites)
        }
    
    def get_default_output_filename(self) -> str:
        """返回預設輸出檔名"""
        return "satellite_visibility_output.json"
    
    def extract_key_metrics(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取關鍵指標"""
        satellites = processed_data.get("data", {}).get("satellites", [])
        statistics = processed_data.get("statistics", {})
        
        total_satellites = len(satellites)
        satellites_with_visibility = len([s for s in satellites if s.get("visibility_summary", {}).get("visible_points", 0) > 0])
        
        return {
            "total_satellites_processed": total_satellites,
            "satellites_with_visibility": satellites_with_visibility,
            "visibility_success_rate": round((satellites_with_visibility / total_satellites * 100) if total_satellites > 0 else 0, 2),
            "total_visibility_windows": sum(len(s.get("enhanced_visibility_windows", [])) for s in satellites),
            "processing_duration": processed_data.get("metadata", {}).get("processing_duration_seconds", 0),
            "observer_coordinates": processed_data.get("metadata", {}).get("observer_coordinates", {}),
            "visibility_calculation_method": "spherical_geometry"
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
        
        satellites = processed_data.get("data", {}).get("satellites", [])
        
        # 檢查1: 數據結構檢查
        structure_check = self._check_data_structure(processed_data)
        validation_results["all_checks"]["data_structure_check"] = structure_check
        validation_results["total_checks"] += 1
        
        if structure_check:
            validation_results["passed_checks"] += 1
        else:
            validation_results["failed_checks"] += 1
            validation_results["passed"] = False
        
        # 檢查2: 可見性計算檢查
        visibility_check = self._check_visibility_calculation(satellites)
        validation_results["all_checks"]["visibility_calculation_check"] = visibility_check
        validation_results["total_checks"] += 1
        
        if visibility_check:
            validation_results["passed_checks"] += 1
        else:
            validation_results["failed_checks"] += 1
            validation_results["passed"] = False
        
        # 檢查3: 仰角過濾檢查
        elevation_check = self._check_elevation_filtering(satellites)
        validation_results["all_checks"]["elevation_filtering_check"] = elevation_check
        validation_results["total_checks"] += 1
        
        if elevation_check:
            validation_results["passed_checks"] += 1
        else:
            validation_results["failed_checks"] += 1
            validation_results["passed"] = False
        
        return validation_results
    
    def save_results(self, processed_data: Dict[str, Any]) -> str:
        """保存處理結果"""
        try:
            output_filename = self.get_default_output_filename()
            output_file = self.output_dir / output_filename
            
            self.logger.info(f"💾 保存Stage 2結果到: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("✅ Stage 2結果保存成功")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"保存Stage 2結果失敗: {e}")
            raise
    
    def _check_data_structure(self, data: Dict[str, Any]) -> bool:
        """檢查數據結構"""
        required_sections = ["data", "metadata", "statistics"]
        return all(section in data for section in required_sections)
    
    def _check_visibility_calculation(self, satellites: List[Dict[str, Any]]) -> bool:
        """檢查可見性計算"""
        if not satellites:
            return False
        
        for sat in satellites:
            if "visibility_summary" not in sat or "position_timeseries" not in sat:
                return False
        
        return True
    
    def _check_elevation_filtering(self, satellites: List[Dict[str, Any]]) -> bool:
        """檢查仰角過濾"""
        if not satellites:
            return True  # 無數據時不算失敗
        
        # 檢查至少有部分衛星有仰角數據
        satellites_with_elevation = 0
        for sat in satellites:
            timeseries = sat.get("position_timeseries", [])
            if any(pos.get("relative_to_observer", {}).get("elevation_deg", -999) > -90 for pos in timeseries):
                satellites_with_elevation += 1
        
        return satellites_with_elevation > 0