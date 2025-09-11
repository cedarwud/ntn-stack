"""
Data Integration Loader - 跨階段數據載入器

負責從前階段處理結果載入數據，專注於：
- 跨階段數據整合和載入
- 智能文件發現和驗證  
- 數據完整性檢查
- 載入性能優化
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class DataIntegrationLoader:
    """跨階段數據載入器 - 處理來自階段五的整合數據"""
    
    def __init__(self, base_data_path: str = "data"):
        self.base_data_path = Path(base_data_path)
        self.integration_outputs_path = self.base_data_path / "data_integration_outputs"
        
        # 載入統計
        self.load_stats = {
            "files_loaded": 0,
            "total_satellites": 0,
            "load_start_time": None,
            "load_duration": 0.0
        }
    
    def load_stage5_integration_data(self) -> Dict[str, Any]:
        """載入階段五數據整合結果"""
        self.load_stats["load_start_time"] = datetime.now()
        
        try:
            # 查找整合數據文件
            integration_file = self._find_integration_file()
            if not integration_file:
                raise FileNotFoundError("未找到階段五整合數據文件")
            
            logger.info(f"載入整合數據文件: {integration_file}")
            
            # 載入數據
            with open(integration_file, "r", encoding="utf-8") as f:
                integration_data = json.load(f)
            
            # 驗證數據完整性
            self._validate_integration_data(integration_data)
            
            # 更新統計
            self._update_load_stats(integration_data)
            
            self.load_stats["load_duration"] = (
                datetime.now() - self.load_stats["load_start_time"]
            ).total_seconds()
            
            logger.info(f"成功載入 {self.load_stats['files_loaded']} 個文件，"
                       f"包含 {self.load_stats['total_satellites']} 顆衛星數據")
            
            return integration_data
            
        except Exception as e:
            logger.error(f"載入階段五整合數據失敗: {e}")
            raise
    
    def _find_integration_file(self) -> Optional[Path]:
        """智能文件發現 - 查找最新的整合數據文件"""
        
        # 優先查找標準文件名
        standard_files = [
            "integrated_data_output.json",
            "data_integration_output.json", 
            "stage5_integration_result.json"
        ]
        
        for filename in standard_files:
            file_path = self.integration_outputs_path / filename
            if file_path.exists():
                return file_path
        
        # 查找時間戳文件
        if self.integration_outputs_path.exists():
            json_files = list(self.integration_outputs_path.glob("*.json"))
            if json_files:
                # 按修改時間排序，選擇最新的
                latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"使用最新文件: {latest_file}")
                return latest_file
        
        return None
    
    def _validate_integration_data(self, data: Dict[str, Any]) -> bool:
        """驗證整合數據的完整性和格式"""
        
        required_keys = [
            "metadata", "satellite_data", "layered_coverage_data",
            "handover_scenarios", "processing_summary"
        ]
        
        # 檢查必要字段
        for key in required_keys:
            if key not in data:
                raise ValueError(f"整合數據缺少必要字段: {key}")
        
        # 驗證衛星數據
        satellite_data = data.get("satellite_data", {})
        if not satellite_data:
            raise ValueError("衛星數據為空")
        
        # 驗證元數據
        metadata = data.get("metadata", {})
        if "processing_time" not in metadata:
            logger.warning("元數據缺少處理時間信息")
        
        # 驗證分層覆蓋數據
        layered_data = data.get("layered_coverage_data", {})
        if not layered_data:
            logger.warning("分層覆蓋數據為空")
        
        logger.info("整合數據驗證通過")
        return True
    
    def _update_load_stats(self, data: Dict[str, Any]) -> None:
        """更新載入統計信息"""
        
        self.load_stats["files_loaded"] = 1
        
        # 統計衛星數量
        satellite_data = data.get("satellite_data", {})
        total_satellites = 0
        
        for constellation, satellites in satellite_data.items():
            if isinstance(satellites, list):
                total_satellites += len(satellites)
            elif isinstance(satellites, dict):
                total_satellites += len(satellites.keys())
        
        self.load_stats["total_satellites"] = total_satellites
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """獲取載入統計信息"""
        return self.load_stats.copy()
    
    def extract_candidate_satellites(self, integration_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """從整合數據中提取候選衛星列表"""
        
        candidates = []
        satellite_data = integration_data.get("satellite_data", {})
        
        for constellation, satellites in satellite_data.items():
            if isinstance(satellites, list):
                for satellite in satellites:
                    candidate = self._format_candidate(satellite, constellation)
                    if candidate:
                        candidates.append(candidate)
            
            elif isinstance(satellites, dict):
                for sat_id, satellite in satellites.items():
                    candidate = self._format_candidate(satellite, constellation, sat_id)
                    if candidate:
                        candidates.append(candidate)
        
        logger.info(f"提取到 {len(candidates)} 個候選衛星")
        return candidates
    
    def _format_candidate(self, satellite: Dict[str, Any], 
                         constellation: str, sat_id: str = None) -> Optional[Dict[str, Any]]:
        """格式化候選衛星數據"""
        
        try:
            # 基本信息
            candidate = {
                "satellite_id": sat_id or satellite.get("satellite_id"),
                "constellation": constellation,
                "norad_id": satellite.get("norad_id"),
            }
            
            # 軌道信息
            if "orbital_data" in satellite:
                candidate["orbital_data"] = satellite["orbital_data"]
            
            # 信號品質數據  
            if "signal_quality" in satellite:
                candidate["signal_quality"] = satellite["signal_quality"]
            
            # 可見性數據
            if "visibility_data" in satellite:
                candidate["visibility_data"] = satellite["visibility_data"]
            
            # 時間序列數據
            if "timeseries_data" in satellite:
                candidate["timeseries_data"] = satellite["timeseries_data"]
            
            return candidate
            
        except Exception as e:
            logger.warning(f"格式化候選衛星 {sat_id} 失敗: {e}")
            return None
