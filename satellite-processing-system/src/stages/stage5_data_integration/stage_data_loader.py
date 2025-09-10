"""
跨階段數據載入器 - Stage 5模組化組件

職責：
1. 載入Stage 1-4的輸出數據
2. 跨階段數據同步
3. 數據格式驗證和轉換
4. 提供統一的數據訪問接口
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class StageDataLoader:
    """跨階段數據載入器 - 載入和整合前四個階段的輸出數據"""
    
    def __init__(self):
        """初始化跨階段數據載入器"""
        self.logger = logging.getLogger(f"{__name__}.StageDataLoader")
        
        # 數據載入統計
        self.loading_statistics = {
            "stages_loaded": 0,
            "total_satellites_loaded": 0,
            "loading_duration": 0,
            "data_size_bytes": 0
        }
        
        # 階段數據存儲
        self.stage_data = {
            "stage1_orbital": None,
            "stage2_visibility": None, 
            "stage3_timeseries": None,
            "stage4_signal_analysis": None
        }
        
        self.logger.info("✅ 跨階段數據載入器初始化完成")
    
    def load_all_stage_outputs(self, 
                             stage1_path: Optional[str] = None,
                             stage2_path: Optional[str] = None, 
                             stage3_path: Optional[str] = None,
                             stage4_path: Optional[str] = None) -> Dict[str, Any]:
        """
        載入所有階段輸出數據
        
        Args:
            stage1_path: Stage 1軌道計算輸出路徑
            stage2_path: Stage 2可見性過濾輸出路徑
            stage3_path: Stage 3時間序列預處理輸出路徑
            stage4_path: Stage 4信號分析輸出路徑
            
        Returns:
            整合的跨階段數據
        """
        start_time = datetime.now()
        self.logger.info("🔄 開始載入所有階段輸出數據...")
        
        # 載入各階段數據
        load_results = {}
        
        # Stage 1: 軌道計算數據
        if stage1_path or self._find_stage_output_path("stage1", "tle_calculation_outputs"):
            path = stage1_path or self._find_stage_output_path("stage1", "tle_calculation_outputs")
            self.stage_data["stage1_orbital"] = self._load_stage_data(path, "Stage 1 軌道計算")
            load_results["stage1_loaded"] = True
            self.loading_statistics["stages_loaded"] += 1
        
        # Stage 2: 可見性過濾數據  
        if stage2_path or self._find_stage_output_path("stage2", "intelligent_filtering_outputs"):
            path = stage2_path or self._find_stage_output_path("stage2", "intelligent_filtering_outputs")
            self.stage_data["stage2_visibility"] = self._load_stage_data(path, "Stage 2 可見性過濾")
            load_results["stage2_loaded"] = True
            self.loading_statistics["stages_loaded"] += 1
        
        # Stage 3: 時間序列預處理數據
        if stage3_path or self._find_stage_output_path("stage3", "timeseries_preprocessing_outputs"):
            path = stage3_path or self._find_stage_output_path("stage3", "timeseries_preprocessing_outputs")
            self.stage_data["stage3_timeseries"] = self._load_enhanced_timeseries(path)
            load_results["stage3_loaded"] = True
            self.loading_statistics["stages_loaded"] += 1
        
        # Stage 4: 信號分析數據 (可選)
        if stage4_path or self._find_stage_output_path("stage4", "signal_analysis_outputs"):
            path = stage4_path or self._find_stage_output_path("stage4", "signal_analysis_outputs")
            self.stage_data["stage4_signal_analysis"] = self._load_stage_data(path, "Stage 4 信號分析")
            load_results["stage4_loaded"] = True
            self.loading_statistics["stages_loaded"] += 1
        
        # 計算載入統計
        self.loading_statistics["loading_duration"] = (datetime.now() - start_time).total_seconds()
        self.loading_statistics["total_satellites_loaded"] = self._count_total_satellites()
        
        self.logger.info(f"✅ 階段數據載入完成: {self.loading_statistics['stages_loaded']} 階段, "
                        f"{self.loading_statistics['total_satellites_loaded']} 衛星, "
                        f"{self.loading_statistics['loading_duration']:.2f}秒")
        
        return {
            "load_results": load_results,
            "stage_data": self.stage_data,
            "loading_statistics": self.loading_statistics
        }
    
    def _find_stage_output_path(self, stage_name: str, output_dir: str) -> Optional[str]:
        """尋找階段輸出路徑"""
        # 優先檢查標準位置
        standard_paths = [
            f"data/{output_dir}/",
            f"data/{stage_name}_outputs/",
            f"data/{stage_name}/"
        ]
        
        for base_path in standard_paths:
            if os.path.exists(base_path):
                # 尋找JSON輸出文件
                for filename in os.listdir(base_path):
                    if filename.endswith('.json'):
                        return os.path.join(base_path, filename)
        
        return None
    
    def _load_stage_data(self, file_path: str, stage_description: str) -> Dict[str, Any]:
        """載入單一階段數據"""
        try:
            self.logger.info(f"📋 載入{stage_description}數據: {file_path}")
            
            if not os.path.exists(file_path):
                self.logger.warning(f"⚠️ {stage_description}文件不存在: {file_path}")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新數據大小統計
            file_size = os.path.getsize(file_path)
            self.loading_statistics["data_size_bytes"] += file_size
            
            self.logger.info(f"✅ {stage_description}數據載入成功 ({file_size} bytes)")
            return data
            
        except Exception as e:
            self.logger.error(f"❌ {stage_description}數據載入失敗: {e}")
            return {}
    
    def _load_enhanced_timeseries(self, file_path: str) -> Dict[str, Any]:
        """載入增強時間序列數據 (Stage 3專用)"""
        try:
            self.logger.info(f"📈 載入增強時間序列數據: {file_path}")
            
            if not os.path.exists(file_path):
                self.logger.warning(f"⚠️ 時間序列文件不存在: {file_path}")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                timeseries_data = json.load(f)
            
            # 驗證時間序列數據格式
            validation_result = self._validate_timeseries_format(timeseries_data)
            
            if not validation_result["valid"]:
                self.logger.warning(f"⚠️ 時間序列數據格式驗證失敗: {validation_result['errors']}")
            
            # 增強處理時間序列數據
            enhanced_data = self._enhance_timeseries_data(timeseries_data)
            
            # 更新統計
            file_size = os.path.getsize(file_path)
            self.loading_statistics["data_size_bytes"] += file_size
            
            self.logger.info(f"✅ 增強時間序列數據載入成功 ({file_size} bytes)")
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"❌ 增強時間序列數據載入失敗: {e}")
            return {}
    
    def _validate_timeseries_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證時間序列數據格式"""
        errors = []
        
        # 檢查必需字段
        required_fields = ["data", "metadata"]
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")
        
        # 檢查數據結構
        if "data" in data:
            if "satellites" not in data["data"]:
                errors.append("數據中缺少衛星信息")
            else:
                satellites = data["data"]["satellites"]
                if not isinstance(satellites, list):
                    errors.append("衛星數據格式錯誤")
                elif len(satellites) == 0:
                    errors.append("衛星數據為空")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "satellite_count": len(data.get("data", {}).get("satellites", []))
        }
    
    def _enhance_timeseries_data(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """增強時間序列數據"""
        enhanced = timeseries_data.copy()
        
        # 添加數據載入時間戳
        enhanced["loading_timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # 計算時間序列統計
        if "data" in enhanced and "satellites" in enhanced["data"]:
            satellites = enhanced["data"]["satellites"]
            
            total_timeseries_points = sum(
                len(sat.get("timeseries_data", [])) for sat in satellites
            )
            
            enhanced["enhanced_statistics"] = {
                "total_satellites": len(satellites),
                "total_timeseries_points": total_timeseries_points,
                "avg_timeseries_per_satellite": total_timeseries_points / max(len(satellites), 1)
            }
        
        return enhanced
    
    def _count_total_satellites(self) -> int:
        """計算總衛星數量"""
        total = 0
        
        for stage_name, data in self.stage_data.items():
            if data and isinstance(data, dict):
                if "data" in data and "satellites" in data["data"]:
                    total = max(total, len(data["data"]["satellites"]))
        
        return total
    
    def get_stage_data(self, stage_name: str) -> Dict[str, Any]:
        """獲取指定階段數據"""
        stage_key = f"stage{stage_name}_" + {
            "1": "orbital",
            "2": "visibility", 
            "3": "timeseries",
            "4": "signal_analysis"
        }.get(stage_name, "unknown")
        
        return self.stage_data.get(stage_key, {})
    
    def get_integrated_satellite_list(self) -> List[Dict[str, Any]]:
        """獲取整合的衛星列表"""
        integrated_satellites = []
        
        # 以Stage 3時間序列數據為基礎
        if self.stage_data["stage3_timeseries"]:
            timeseries_data = self.stage_data["stage3_timeseries"]
            satellites = timeseries_data.get("data", {}).get("satellites", [])
            
            for satellite in satellites:
                satellite_id = satellite.get("satellite_id")
                
                integrated_satellite = {
                    "satellite_id": satellite_id,
                    "constellation": satellite.get("constellation"),
                    "stage3_timeseries": satellite,
                    "stage1_orbital": self._find_satellite_in_stage("stage1_orbital", satellite_id),
                    "stage2_visibility": self._find_satellite_in_stage("stage2_visibility", satellite_id),
                    "stage4_signal_analysis": self._find_satellite_in_stage("stage4_signal_analysis", satellite_id)
                }
                
                integrated_satellites.append(integrated_satellite)
        
        return integrated_satellites
    
    def _find_satellite_in_stage(self, stage_key: str, satellite_id: str) -> Dict[str, Any]:
        """在指定階段中查找衛星數據"""
        stage_data = self.stage_data.get(stage_key, {})
        
        if stage_data and "data" in stage_data and "satellites" in stage_data["data"]:
            for satellite in stage_data["data"]["satellites"]:
                if satellite.get("satellite_id") == satellite_id:
                    return satellite
        
        return {}
    
    def get_loading_statistics(self) -> Dict[str, Any]:
        """獲取載入統計信息"""
        return self.loading_statistics.copy()