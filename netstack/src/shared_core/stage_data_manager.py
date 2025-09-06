"""
多階段數據管理器 - 統一處理六階段LEO衛星數據源
支持自動回退機制和數據格式統一
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class StageStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed" 
    MISSING = "missing"
    PARTIAL = "partial"

@dataclass
class StageInfo:
    stage_number: int
    stage_name: str
    satellite_count: int
    file_path: str
    file_size_mb: float
    processing_time: Optional[datetime]
    status: StageStatus
    data_quality: Dict[str, Any]
    error_message: Optional[str] = None

class StageDataManager:
    """
    六階段LEO衛星數據統一管理器
    
    功能：
    - 自動檢測各階段數據可用性
    - 提供回退機制（Stage 6 → 5 → 4 → 3 → 2 → 1）
    - 統一數據格式轉換
    - 提供數據品質驗證
    """
    
    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = Path(data_dir)
        self.stage_configs = {
            1: {
                "name": "TLE載入與SGP4軌道計算",
                "paths": [
                    self.data_dir / "tle_calculation_outputs" / "tle_orbital_calculation_output.json",
                    self.data_dir / "tle_orbital_calculation_output.json"
                ],
                "data_keys": ["starlink", "oneweb", "satellites"],
                "min_satellites": 8000
            },
            2: {
                "name": "智能衛星篩選", 
                "paths": [
                    self.data_dir / "intelligent_filtering_outputs" / "intelligent_filtered_output.json",
                    self.data_dir / "intelligent_filtered_output.json"
                ],
                "data_keys": ["satellites", "constellations"],
                "min_satellites": 150
            },
            3: {
                "name": "信號品質分析與3GPP事件",
                "paths": [
                    self.data_dir / "signal_analysis_outputs" / "signal_event_analysis_output.json",
                    self.data_dir / "signal_event_analysis_output.json"
                ],
                "data_keys": ["satellites", "constellations"],
                "min_satellites": 150
            },
            4: {
                "name": "時間序列預處理",
                "paths": [
                    self.data_dir / "timeseries_preprocessing_outputs" / "conversion_statistics.json",
                    self.data_dir / "timeseries_preprocessing_outputs" / "starlink_enhanced.json"
                ],
                "data_keys": ["total_satellites", "starlink_count", "oneweb_count"],
                "min_satellites": 150
            },
            5: {
                "name": "數據整合與接口準備",
                "paths": [
                    self.data_dir / "data_integration_outputs" / "data_integration_output.json",
                    self.data_dir / "data_integration_output.json"
                ],
                "data_keys": ["satellites"],
                "min_satellites": 150
            },
            6: {
                "name": "動態池規劃與模擬退火優化",
                "paths": [
                    self.data_dir / "dynamic_pool_planning_outputs" / "enhanced_dynamic_pools_output.json",
                    self.data_dir / "dynamic_pool_planning_outputs" / "dynamic_satellite_pool_optimization_results.json"
                ],
                "data_keys": ["final_solution", "satellites", "starlink_satellites", "oneweb_satellites"],
                "min_satellites": 260
            }
        }
        
        logger.info("✅ 多階段數據管理器初始化完成")
        
    def get_stage_info(self, stage_number: int) -> StageInfo:
        """獲取特定階段的詳細信息"""
        
        if stage_number not in self.stage_configs:
            return StageInfo(
                stage_number=stage_number,
                stage_name="未知階段",
                satellite_count=0,
                file_path="",
                file_size_mb=0.0,
                processing_time=None,
                status=StageStatus.MISSING,
                data_quality={}
            )
            
        config = self.stage_configs[stage_number]
        
        # 嘗試找到可用的數據文件
        for path in config["paths"]:
            if path.exists():
                try:
                    file_size_mb = path.stat().st_size / (1024 * 1024)
                    processing_time = datetime.fromtimestamp(path.stat().st_mtime)
                    
                    # 載入數據並分析
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    satellite_count = self._extract_satellite_count(data, config["data_keys"])
                    data_quality = self._analyze_data_quality(data, stage_number)
                    
                    # 判斷狀態
                    status = StageStatus.SUCCESS
                    if satellite_count < config["min_satellites"]:
                        status = StageStatus.PARTIAL
                    
                    return StageInfo(
                        stage_number=stage_number,
                        stage_name=config["name"],
                        satellite_count=satellite_count,
                        file_path=str(path),
                        file_size_mb=file_size_mb,
                        processing_time=processing_time,
                        status=status,
                        data_quality=data_quality
                    )
                    
                except Exception as e:
                    logger.warning(f"Stage {stage_number} 數據讀取錯誤: {e}")
                    return StageInfo(
                        stage_number=stage_number,
                        stage_name=config["name"],
                        satellite_count=0,
                        file_path=str(path),
                        file_size_mb=0.0,
                        processing_time=None,
                        status=StageStatus.FAILED,
                        data_quality={},
                        error_message=str(e)
                    )
        
        # 沒有找到任何可用文件
        return StageInfo(
            stage_number=stage_number,
            stage_name=config["name"],
            satellite_count=0,
            file_path="",
            file_size_mb=0.0,
            processing_time=None,
            status=StageStatus.MISSING,
            data_quality={}
        )
    
    def get_all_stages_status(self) -> Dict[int, StageInfo]:
        """獲取所有階段的狀態信息"""
        return {stage_num: self.get_stage_info(stage_num) for stage_num in range(1, 7)}
    
    def get_best_available_stage(self) -> Tuple[int, StageInfo]:
        """
        獲取最佳可用階段數據
        優先級：Stage 6 > 5 > 4 > 3 > 2 > 1
        """
        priority_order = [6, 5, 4, 3, 2, 1]  # 修復：包含 Stage 4
        
        for stage_num in priority_order:
            stage_info = self.get_stage_info(stage_num)
            if stage_info.status in [StageStatus.SUCCESS, StageStatus.PARTIAL]:
                logger.info(f"🎯 使用 Stage {stage_num} 數據: {stage_info.satellite_count} 顆衛星")
                return stage_num, stage_info
        
        # 如果都沒有，返回 Stage 1 作為最後選擇
        logger.warning("⚠️ 沒有找到可用的階段數據，返回 Stage 1")
        return 1, self.get_stage_info(1)
    
    def load_stage_data(self, stage_number: int) -> Dict[str, Any]:
        """載入特定階段的數據"""
        stage_info = self.get_stage_info(stage_number)
        
        if stage_info.status == StageStatus.MISSING:
            raise FileNotFoundError(f"Stage {stage_number} 數據不存在")
        
        if not stage_info.file_path:
            raise FileNotFoundError(f"Stage {stage_number} 文件路徑為空")
        
        try:
            with open(stage_info.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"載入 Stage {stage_number} 數據失敗: {e}")
    
    def get_unified_satellite_data(self) -> List[Dict[str, Any]]:
        """
        獲取統一格式的衛星數據
        自動選擇最佳可用階段並轉換為統一格式
        """
        stage_num, stage_info = self.get_best_available_stage()
        
        if stage_info.status == StageStatus.MISSING:
            logger.error("❌ 沒有可用的階段數據")
            return []
        
        data = self.load_stage_data(stage_num)
        return self._convert_to_unified_format(data, stage_num)
    
    def _extract_satellite_count(self, data: Dict[str, Any], data_keys: List[str]) -> int:
        """從數據中提取衛星數量"""
        count = 0
        
        # 嘗試不同的數據結構
        if 'satellites' in data and isinstance(data['satellites'], list):
            count = len(data['satellites'])
        elif 'total_satellites' in data:
            count = data.get('total_satellites', 0)
        elif 'final_solution' in data:
            # Stage 6 格式
            solution = data['final_solution']
            count += len(solution.get('starlink_satellites', []))
            count += len(solution.get('oneweb_satellites', []))
        elif 'constellations' in data:
            # 星座分組格式
            for const_data in data['constellations'].values():
                if isinstance(const_data, dict) and 'satellites' in const_data:
                    count += len(const_data['satellites'])
        else:
            # 直接星座格式
            for key in ['starlink', 'oneweb']:
                if key in data:
                    const_data = data[key]
                    if isinstance(const_data, list):
                        count += len(const_data)
                    elif isinstance(const_data, dict) and 'satellites' in const_data:
                        count += len(const_data['satellites'])
        
        return count
    
    def _analyze_data_quality(self, data: Dict[str, Any], stage_number: int) -> Dict[str, Any]:
        """分析數據品質指標"""
        quality = {
            'has_position_data': False,
            'has_elevation_data': False,
            'has_constellation_info': False,
            'constellation_distribution': {},
            'data_completeness': 0.0
        }
        
        satellites = self._extract_satellites_list(data)
        
        if satellites:
            total_sats = len(satellites)
            position_count = 0
            elevation_count = 0
            constellation_count = {}
            
            for sat in satellites:
                # 檢查位置數據
                if 'positions' in sat or 'position_eci' in sat:
                    position_count += 1
                
                # 檢查仰角數據
                if any(key in sat for key in ['elevation_deg', 'max_elevation', 'positions']):
                    elevation_count += 1
                
                # 統計星座分佈
                constellation = sat.get('constellation', 'unknown').lower()
                constellation_count[constellation] = constellation_count.get(constellation, 0) + 1
            
            quality.update({
                'has_position_data': position_count > 0,
                'has_elevation_data': elevation_count > 0,
                'has_constellation_info': len(constellation_count) > 0,
                'constellation_distribution': constellation_count,
                'data_completeness': min(position_count, elevation_count) / total_sats if total_sats > 0 else 0.0
            })
        
        return quality
    
    def _extract_satellites_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """從不同格式的數據中提取衛星列表"""
        satellites = []
        
        if 'satellites' in data and isinstance(data['satellites'], list):
            satellites = data['satellites']
        elif 'constellations' in data:
            for const_data in data['constellations'].values():
                if isinstance(const_data, dict) and 'satellites' in const_data:
                    satellites.extend(const_data['satellites'])
        else:
            # 直接星座格式
            for key in ['starlink', 'oneweb']:
                if key in data:
                    const_data = data[key]
                    if isinstance(const_data, list):
                        satellites.extend(const_data)
                    elif isinstance(const_data, dict) and 'satellites' in const_data:
                        satellites.extend(const_data['satellites'])
        
        return satellites
    
    def _convert_to_unified_format(self, data: Dict[str, Any], stage_number: int) -> List[Dict[str, Any]]:
        """轉換為統一的前端格式"""
        satellites = self._extract_satellites_list(data)
        unified_satellites = []
        
        for sat in satellites:
            unified_sat = {
                'satellite_id': sat.get('satellite_id', sat.get('name', 'UNKNOWN')),
                'constellation': sat.get('constellation', 'UNKNOWN').upper(),
                'elevation_deg': self._extract_elevation(sat),
                'azimuth_deg': self._extract_azimuth(sat),
                'range_km': self._extract_range(sat),
                'is_visible': self._extract_visibility(sat),
                'altitude_km': sat.get('altitude_km', 0),
                'data_source_stage': stage_number,
                'position_data': self._extract_position_data(sat)
            }
            unified_satellites.append(unified_sat)
        
        return unified_satellites
    
    def _extract_elevation(self, sat: Dict[str, Any]) -> float:
        """提取仰角數據"""
        if 'elevation_deg' in sat:
            return float(sat['elevation_deg'])
        elif 'max_elevation' in sat:
            return float(sat['max_elevation'])
        elif 'positions' in sat and sat['positions']:
            # 使用最大仰角
            positions = sat['positions']
            if positions:
                return max(pos.get('elevation_deg', 0) for pos in positions)
        return 0.0
    
    def _extract_azimuth(self, sat: Dict[str, Any]) -> float:
        """提取方位角數據"""
        if 'azimuth_deg' in sat:
            return float(sat['azimuth_deg'])
        elif 'positions' in sat and sat['positions']:
            # 使用第一個有效方位角
            for pos in sat['positions']:
                if 'azimuth_deg' in pos:
                    return float(pos['azimuth_deg'])
        return 0.0
    
    def _extract_range(self, sat: Dict[str, Any]) -> float:
        """提取距離數據"""
        if 'range_km' in sat:
            return float(sat['range_km'])
        elif 'positions' in sat and sat['positions']:
            # 使用平均距離
            ranges = [pos.get('range_km', 0) for pos in sat['positions'] if 'range_km' in pos]
            if ranges:
                return sum(ranges) / len(ranges)
        return 0.0
    
    def _extract_visibility(self, sat: Dict[str, Any]) -> bool:
        """提取可見性數據"""
        if 'is_visible' in sat:
            return bool(sat['is_visible'])
        elif 'positions' in sat and sat['positions']:
            # 如果有任何時刻可見就算可見
            return any(pos.get('is_visible', False) for pos in sat['positions'])
        # 根據仰角判斷
        elevation = self._extract_elevation(sat)
        return elevation > 5.0
    
    def _extract_position_data(self, sat: Dict[str, Any]) -> Dict[str, Any]:
        """提取位置相關數據"""
        position_data = {}
        
        if 'positions' in sat and sat['positions']:
            positions = sat['positions']
            position_data['positions_count'] = len(positions)
            position_data['max_elevation'] = max(pos.get('elevation_deg', 0) for pos in positions)
            position_data['min_elevation'] = min(pos.get('elevation_deg', 0) for pos in positions)
            
        if 'position_eci' in sat:
            position_data['eci_position'] = sat['position_eci']
            
        return position_data