#!/usr/bin/env python3
"""
統一智能衛星篩選系統

整合 @stage2_intelligent_filtering/ 重構架構與現有實現
提供統一的智能篩選接口，符合新的數據處理流程
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 添加重構模組路徑
project_root = Path(__file__).parent.parent.parent.parent
stage2_path = project_root / "stage2_intelligent_filtering"
sys.path.insert(0, str(stage2_path))

# 導入統一智能篩選系統
try:
    from unified_intelligent_filter import create_unified_intelligent_filter
    UNIFIED_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"統一智能篩選系統未找到: {e}")
    UNIFIED_SYSTEM_AVAILABLE = False

# 導入現有實現作為後備
from .preprocessing import IntelligentSatelliteSelector, SatelliteSelectionConfig

logger = logging.getLogger(__name__)


class UnifiedIntelligentSatelliteFilter:
    """統一智能衛星篩選器 - 橋接器版本
    
    將請求重定向到新的完整統一系統
    """
    
    def __init__(self, config: Optional[SatelliteSelectionConfig] = None):
        self.config = config or SatelliteSelectionConfig()
        
        if UNIFIED_SYSTEM_AVAILABLE:
            # 使用新的統一智能篩選系統
            self.filter_system = create_unified_intelligent_filter(
                observer_lat=self.config.observer_lat,
                observer_lon=self.config.observer_lon
            )
            self.use_unified_system = True
            logger.info("🚀 使用新的統一智能篩選系統")
        else:
            # 使用現有實現作為後備
            self.legacy_selector = IntelligentSatelliteSelector(config)
            self.use_unified_system = False
            logger.warning("⚠️ 使用現有智能選擇器 (統一系統不可用)")
    
    def process_f1_to_f2(self, f1_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理F1階段到F2階段的數據轉換
        
        現在重定向到新的統一智能篩選系統
        """
        if self.use_unified_system:
            selection_config = {
                "starlink": self.config.starlink_target,
                "oneweb": self.config.oneweb_target
            }
            
            return self.filter_system.process_complete_filtering(f1_data, selection_config)
        else:
            return self._process_with_legacy_selector(f1_data)
    
    def _process_with_legacy_selector(self, f1_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用現有智能選擇器處理 (後備方案)"""
        logger.info("🔧 使用現有智能選擇器進行處理")
        
        try:
            # 提取衛星數據
            all_satellites = []
            constellations = f1_data.get("constellations", {})
            for constellation_name, constellation_data in constellations.items():
                satellites = constellation_data.get("satellites", [])
                for satellite in satellites:
                    satellite["constellation"] = constellation_name
                    all_satellites.append(satellite)
            
            # 使用現有的智能選擇邏輯
            selected_satellites, selection_stats = self.legacy_selector.select_research_subset(all_satellites)
            
            logger.info(f"✅ 現有選擇器完成: 選擇了 {len(selected_satellites)} 顆衛星")
            
            # 構建輸出數據
            f2_output = f1_data.copy()
            f2_output["metadata"]["f2_completion"] = "legacy_intelligent_selector"
            f2_output["metadata"]["selected_satellites_count"] = len(selected_satellites)
            f2_output["metadata"]["selection_stats"] = selection_stats
            
            # 更新星座數據，只保留選中的衛星
            for constellation in f2_output.get("constellations", {}):
                constellation_sats = [sat for sat in selected_satellites 
                                    if sat.get('constellation', '').lower() == constellation.lower()]
                f2_output["constellations"][constellation]["selected_satellites"] = constellation_sats
            
            return f2_output
            
        except Exception as e:
            logger.error(f"❌ 現有智能選擇器處理失敗: {e}")
            raise


if __name__ == "__main__":
    # 測試統一篩選系統
    logger.info("🧪 測試統一智能衛星篩選系統")
    
    # 模擬階段一數據
    test_phase1_data = {
        "metadata": {
            "version": "2.0.0-phase1",
            "total_satellites": 8715,
            "total_constellations": 2
        },
        "constellations": {
            "starlink": {
                "satellites": [
                    {
                        "satellite_id": "STARLINK-1007",
                        "orbit_data": {
                            "altitude": 550,
                            "inclination": 53,
                            "position": {"x": 1234, "y": 5678, "z": 9012}
                        },
                        "timeseries": [
                            {"time": "2025-08-12T12:00:00Z", "elevation_deg": 45.0, "azimuth_deg": 180.0}
                        ]
                    }
                ]
            },
            "oneweb": {
                "satellites": [
                    {
                        "satellite_id": "ONEWEB-0123", 
                        "orbit_data": {
                            "altitude": 1200,
                            "inclination": 87,
                            "position": {"x": 2345, "y": 6789, "z": 123}
                        },
                        "timeseries": [
                            {"time": "2025-08-12T12:00:00Z", "elevation_deg": 30.0, "azimuth_deg": 90.0}
                        ]
                    }
                ]
            }
        }
    }
    
    # 測試統一篩選
    filter_system = create_unified_intelligent_filter()
    result = filter_system.process_f2_filtering_only(test_phase1_data)
    
    print("✅ 統一智能篩選系統測試完成")
    print(f"處理結果: {result.get('metadata', {}).get('f2_filtering_completion', 'Unknown')}")