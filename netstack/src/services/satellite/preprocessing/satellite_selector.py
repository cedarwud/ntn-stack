#!/usr/bin/env python3
"""
統一智能衛星選擇器 - 新的完整實現

此文件替換了舊的 IntelligentSatelliteSelector
現在使用完整的模組化統一智能篩選系統
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# 導入統一智能篩選系統
project_root = Path(__file__).parent.parent.parent.parent.parent
stage2_path = project_root / "stage2_intelligent_filtering"
sys.path.insert(0, str(stage2_path))

try:
    from unified_intelligent_filter import create_unified_intelligent_filter
    UNIFIED_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_SYSTEM_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SatelliteSelectionConfig:
    """衛星選擇配置"""
    starlink_target: int = 555
    oneweb_target: int = 134
    observer_lat: float = 24.9441667  # NTPU 緯度
    observer_lon: float = 121.3713889  # NTPU 經度
    min_elevation: float = 10.0
    version: str = "v2.1.0-unified"


class IntelligentSatelliteSelector:
    """智能衛星選擇器 - 新的統一實現
    
    使用完整的模組化統一智能篩選系統
    向後相容現有的 API
    """
    
    def __init__(self, config: Optional[SatelliteSelectionConfig] = None):
        self.config = config or SatelliteSelectionConfig()
        
        if UNIFIED_SYSTEM_AVAILABLE:
            self.unified_filter = create_unified_intelligent_filter(
                observer_lat=self.config.observer_lat,
                observer_lon=self.config.observer_lon
            )
            logger.info("✅ 使用新的統一智能篩選系統")
        else:
            logger.error("❌ 統一智能篩選系統不可用！")
            raise ImportError("統一智能篩選系統模組不可用")
    
    def select_research_subset(self, all_satellites: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        從完整星座中選擇研究子集
        
        向後相容的 API，內部使用新的統一系統
        
        Args:
            all_satellites: 所有可用衛星列表
            
        Returns:
            選擇的衛星列表和選擇統計
        """
        if not UNIFIED_SYSTEM_AVAILABLE:
            raise RuntimeError("統一智能篩選系統不可用")
        
        # 構建 phase1 格式的數據
        phase1_data = self._build_phase1_format(all_satellites)
        
        # 使用統一篩選系統
        selection_config = {
            "starlink": self.config.starlink_target,
            "oneweb": self.config.oneweb_target
        }
        
        result = self.unified_filter.process_complete_filtering(phase1_data, selection_config)
        
        # 提取選中的衛星和統計信息
        selected_satellites = []
        selection_stats = {
            'starlink': 0,
            'oneweb': 0,
            'total': 0,
            'coverage_quality': {}
        }
        
        for constellation_name, constellation_data in result.get("constellations", {}).items():
            satellites = constellation_data.get("satellites", [])
            selected_satellites.extend(satellites)
            selection_stats[constellation_name] = len(satellites)
            selection_stats['total'] += len(satellites)
        
        # 從結果中提取覆蓋品質信息
        processing_stats = result.get('metadata', {}).get('processing_statistics', {})
        selection_stats['coverage_quality'] = processing_stats.get('selection_summary', {})
        
        logger.info(f"✅ 智能選擇完成: {selection_stats['total']} 顆衛星 "
                   f"(Starlink: {selection_stats['starlink']}, OneWeb: {selection_stats['oneweb']})")
        
        return selected_satellites, selection_stats
    
    def _build_phase1_format(self, all_satellites: List[Dict]) -> Dict[str, Any]:
        """將衛星列表轉換為 phase1 格式"""
        constellations = {}
        
        for satellite in all_satellites:
            constellation = satellite.get('constellation', 'unknown').lower()
            if constellation not in constellations:
                constellations[constellation] = {
                    "satellites": [],
                    "satellite_count": 0
                }
            
            constellations[constellation]["satellites"].append(satellite)
            constellations[constellation]["satellite_count"] += 1
        
        return {
            "metadata": {
                "version": "2.1.0-unified-bridge",
                "total_satellites": len(all_satellites),
                "total_constellations": len(constellations)
            },
            "constellations": constellations
        }
    
    def validate_selection(self, selected_satellites: List[Dict], duration_hours: int = 24) -> Dict[str, bool]:
        """驗證選擇結果"""
        validation_results = {}
        
        # 檢查數量是否符合要求
        starlink_count = sum(1 for sat in selected_satellites if sat.get('constellation', '').lower() == 'starlink')
        oneweb_count = sum(1 for sat in selected_satellites if sat.get('constellation', '').lower() == 'oneweb')
        
        validation_results['starlink_count_ok'] = (starlink_count >= self.config.starlink_target * 0.8)
        validation_results['oneweb_count_ok'] = (oneweb_count >= self.config.oneweb_target * 0.8)
        
        # 檢查信號品質
        signal_quality_count = sum(1 for sat in selected_satellites 
                                 if sat.get('signal_quality', {}).get('mean_rsrp_dbm', -999) > -100)
        validation_results['signal_quality_ok'] = (signal_quality_count >= len(selected_satellites) * 0.7)
        
        # 檢查事件觸發能力
        event_capable = sum(1 for sat in selected_satellites 
                           if sat.get('event_potential', {}).get('composite', 0) > 0.5)
        validation_results['event_capability_ok'] = (event_capable >= len(selected_satellites) * 0.6)
        
        # 整體驗證結果
        validation_results['overall_pass'] = all([
            validation_results['starlink_count_ok'],
            validation_results['oneweb_count_ok'],
            validation_results['signal_quality_ok'],
            validation_results['event_capability_ok']
        ])
        
        return validation_results


if __name__ == "__main__":
    # 測試新的統一實現
    print("🧪 測試新的統一智能衛星選擇器")
    
    if UNIFIED_SYSTEM_AVAILABLE:
        config = SatelliteSelectionConfig()
        selector = IntelligentSatelliteSelector(config)
        
        # 模擬測試數據
        test_satellites = [
            {
                "satellite_id": "STARLINK-1007",
                "constellation": "starlink",
                "orbit_data": {
                    "altitude": 550,
                    "inclination": 53,
                    "position": {"x": 1234, "y": 5678, "z": 9012}
                }
            }
        ]
        
        try:
            selected, stats = selector.select_research_subset(test_satellites)
            print(f"✅ 測試成功: 選擇了 {len(selected)} 顆衛星")
            print(f"統計信息: {stats}")
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
    else:
        print("❌ 統一智能篩選系統不可用")
    
    print("✅ 測試完成")