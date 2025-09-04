"""
統一仰角門檻管理器

統一管理系統中所有仰角相關的門檻值和判斷邏輯，
避免在各階段重複定義相同的仰角邏輯。

作者: NTN Stack Team
版本: 1.0.0
創建日期: 2025-08-19
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ConstellationType(Enum):
    """星座類型枚舉"""
    STARLINK = "starlink"
    ONEWEB = "oneweb"


@dataclass
class ElevationThreshold:
    """仰角門檻配置"""
    constellation: ConstellationType
    min_elevation: float
    optimal_elevation: float
    max_useful_elevation: float
    
    def __post_init__(self):
        """驗證仰角範圍合理性"""
        if not (0 <= self.min_elevation <= self.optimal_elevation <= self.max_useful_elevation <= 90):
            raise ValueError(f"仰角範圍不合理: {self.min_elevation} <= {self.optimal_elevation} <= {self.max_useful_elevation}")


class ElevationThresholdManager:
    """
    統一仰角門檻管理器
    
    負責管理整個系統中所有與仰角相關的門檻值和判斷邏輯，
    確保各階段使用一致的仰角標準。
    """
    
    # 基礎仰角門檻配置 (根據 3GPP NTN 標準及用戶需求)
    BASE_THRESHOLDS = {
        ConstellationType.STARLINK: ElevationThreshold(
            constellation=ConstellationType.STARLINK,
            min_elevation=5.0,      # 🔧 修復: 調整為用戶需求的5度仰角
            optimal_elevation=15.0,  # 最佳性能仰角
            max_useful_elevation=75.0 # 最大有效仰角
        ),
        ConstellationType.ONEWEB: ElevationThreshold(
            constellation=ConstellationType.ONEWEB,
            min_elevation=10.0,      # 🔧 修復: 調整為用戶需求的10度仰角
            optimal_elevation=15.0,  # 調整最佳性能仰角
            max_useful_elevation=75.0 # 最大有效仰角
        )
    }
    
    # 分層仰角門檻 (用於階段五的分層數據生成)
    LAYERED_THRESHOLDS = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    
    # 信號品質評估仰角點 (用於階段三的信號計算)
    SIGNAL_EVALUATION_ANGLES = [5, 10, 15, 30, 45, 60, 75, 90]
    
    def __init__(self):
        """初始化仰角門檻管理器"""
        self._thresholds = self.BASE_THRESHOLDS.copy()
        logger.info("✅ 統一仰角門檻管理器初始化完成")
        logger.info(f"  Starlink 最低仰角: {self._thresholds[ConstellationType.STARLINK].min_elevation}°")
        logger.info(f"  OneWeb 最低仰角: {self._thresholds[ConstellationType.ONEWEB].min_elevation}°")
    
    def get_min_elevation(self, constellation: str) -> float:
        """獲取星座的最低仰角門檻"""
        const_type = self._parse_constellation(constellation)
        return self._thresholds[const_type].min_elevation
    
    def get_optimal_elevation(self, constellation: str) -> float:
        """獲取星座的最佳仰角門檻"""
        const_type = self._parse_constellation(constellation)
        return self._thresholds[const_type].optimal_elevation
    
    def get_threshold_config(self, constellation: str) -> ElevationThreshold:
        """獲取星座的完整仰角配置"""
        const_type = self._parse_constellation(constellation)
        return self._thresholds[const_type]
    
    def is_satellite_visible(self, elevation_deg: float, constellation: str) -> bool:
        """判斷衛星是否在最低仰角以上 (基礎可見性)"""
        min_elev = self.get_min_elevation(constellation)
        return elevation_deg >= min_elev
    
    def is_satellite_optimal(self, elevation_deg: float, constellation: str) -> bool:
        """判斷衛星是否在最佳仰角以上 (優質信號)"""
        optimal_elev = self.get_optimal_elevation(constellation)
        return elevation_deg >= optimal_elev
    
    def get_elevation_quality_score(self, elevation_deg: float, constellation: str) -> float:
        """
        計算仰角品質評分 (0.0-1.0)
        
        評分邏輯:
        - 低於最低門檻: 0.0
        - 最低到最佳: 0.5-0.8 線性增長
        - 最佳到最大: 0.8-1.0 線性增長
        """
        config = self.get_threshold_config(constellation)
        
        if elevation_deg < config.min_elevation:
            return 0.0
        elif elevation_deg < config.optimal_elevation:
            # 最低到最佳: 0.5-0.8
            ratio = (elevation_deg - config.min_elevation) / (config.optimal_elevation - config.min_elevation)
            return 0.5 + 0.3 * ratio
        elif elevation_deg <= config.max_useful_elevation:
            # 最佳到最大: 0.8-1.0
            ratio = (elevation_deg - config.optimal_elevation) / (config.max_useful_elevation - config.optimal_elevation)
            return 0.8 + 0.2 * ratio
        else:
            return 1.0
    
    def filter_satellites_by_elevation(self, satellites: List[Dict], constellation: str, 
                                     min_threshold: Optional[float] = None) -> List[Dict]:
        """
        根據仰角門檻過濾衛星列表
        
        Args:
            satellites: 衛星數據列表
            constellation: 星座名稱
            min_threshold: 自定義最低仰角，如果為None則使用預設值
        
        Returns:
            過濾後的衛星列表
        """
        if min_threshold is None:
            min_threshold = self.get_min_elevation(constellation)
        
        filtered_satellites = []
        
        for satellite in satellites:
            # 檢查時序數據中是否有符合仰角要求的點
            timeseries_data = satellite.get('position_timeseries', satellite.get('timeseries', []))
            
            valid_points = []
            for point in timeseries_data:
                elevation = point.get('elevation_deg', 0)
                if elevation >= min_threshold:
                    valid_points.append(point)
            
            # 如果有有效點，保留這顆衛星
            if valid_points:
                filtered_satellite = satellite.copy()
                filtered_satellite['position_timeseries'] = valid_points
                filtered_satellite['elevation_filter_info'] = {
                    'applied_threshold': min_threshold,
                    'original_points': len(timeseries_data),
                    'filtered_points': len(valid_points),
                    'retention_rate': len(valid_points) / len(timeseries_data) if timeseries_data else 0
                }
                filtered_satellites.append(filtered_satellite)
        
        logger.info(f"仰角濾波結果 ({constellation}, {min_threshold}°): {len(satellites)} → {len(filtered_satellites)} 顆衛星")
        
        return filtered_satellites
    
    def get_layered_thresholds(self) -> List[float]:
        """獲取分層門檻列表 (用於階段五)"""
        return self.LAYERED_THRESHOLDS.copy()
    
    def get_signal_evaluation_angles(self) -> List[int]:
        """獲取信號評估仰角點 (用於階段三)"""
        return self.SIGNAL_EVALUATION_ANGLES.copy()
    
    def generate_layered_data(self, satellite_data: Dict[str, Any], 
                            output_thresholds: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        生成分層仰角數據 (替代階段五中的重複邏輯)
        
        Args:
            satellite_data: 原始衛星數據
            output_thresholds: 自定義輸出門檻，如果為None則使用預設分層門檻
        
        Returns:
            分層數據結果
        """
        if output_thresholds is None:
            output_thresholds = self.LAYERED_THRESHOLDS
        
        layered_results = {}
        
        logger.info(f"🔄 使用統一仰角管理器生成分層數據，門檻: {output_thresholds}")
        
        for threshold in output_thresholds:
            layered_results[f"elevation_{threshold}deg"] = {}
            
            for constellation, data in satellite_data.items():
                if not data:
                    continue
                
                # 使用統一的濾波邏輯
                satellites = data.get('satellites', [])
                filtered_satellites = self.filter_satellites_by_elevation(
                    satellites, constellation, threshold
                )
                
                layered_results[f"elevation_{threshold}deg"][constellation] = {
                    "satellites": filtered_satellites,
                    "satellites_count": len(filtered_satellites),
                    "threshold_deg": threshold,
                    "processed_by": "unified_elevation_threshold_manager"
                }
        
        return layered_results
    
    def _parse_constellation(self, constellation: str) -> ConstellationType:
        """解析星座名稱為枚舉類型"""
        constellation_lower = constellation.lower()
        if constellation_lower == "starlink":
            return ConstellationType.STARLINK
        elif constellation_lower == "oneweb":
            return ConstellationType.ONEWEB
        else:
            raise ValueError(f"不支援的星座類型: {constellation}")
    
    def get_filtering_stats(self) -> Dict[str, Any]:
        """獲取濾波統計信息"""
        return {
            "manager_version": "1.0.0",
            "supported_constellations": [c.value for c in ConstellationType],
            "base_thresholds": {
                c.value: {
                    "min_elevation": threshold.min_elevation,
                    "optimal_elevation": threshold.optimal_elevation,
                    "max_useful_elevation": threshold.max_useful_elevation
                }
                for c, threshold in self._thresholds.items()
            },
            "layered_thresholds": self.LAYERED_THRESHOLDS,
            "signal_evaluation_angles": self.SIGNAL_EVALUATION_ANGLES
        }


# 全局實例 (單例模式)
_global_elevation_manager = None

def get_elevation_threshold_manager() -> ElevationThresholdManager:
    """獲取全局仰角門檻管理器實例"""
    global _global_elevation_manager
    if _global_elevation_manager is None:
        _global_elevation_manager = ElevationThresholdManager()
    return _global_elevation_manager


# 便捷函數
def get_min_elevation(constellation: str) -> float:
    """快速獲取最低仰角門檻"""
    return get_elevation_threshold_manager().get_min_elevation(constellation)

def is_satellite_visible(elevation_deg: float, constellation: str) -> bool:
    """快速判斷衛星可見性"""
    return get_elevation_threshold_manager().is_satellite_visible(elevation_deg, constellation)

def filter_by_elevation(satellites: List[Dict], constellation: str, 
                       min_threshold: Optional[float] = None) -> List[Dict]:
    """快速仰角濾波"""
    return get_elevation_threshold_manager().filter_satellites_by_elevation(
        satellites, constellation, min_threshold
    )


if __name__ == "__main__":
    # 測試統一仰角門檻管理器
    manager = get_elevation_threshold_manager()
    
    print("🧪 測試統一仰角門檻管理器")
    print("=" * 50)
    
    # 測試基本功能
    print(f"Starlink 最低仰角: {manager.get_min_elevation('starlink')}°")
    print(f"OneWeb 最低仰角: {manager.get_min_elevation('oneweb')}°")
    
    # 測試可見性判斷
    test_elevations = [3, 7, 12, 18, 25]
    for elev in test_elevations:
        starlink_visible = manager.is_satellite_visible(elev, 'starlink')
        oneweb_visible = manager.is_satellite_visible(elev, 'oneweb')
        print(f"{elev}° - Starlink: {'✅' if starlink_visible else '❌'}, OneWeb: {'✅' if oneweb_visible else '❌'}")
    
    # 測試品質評分
    print("\n仰角品質評分:")
    for elev in [5, 15, 30, 60]:
        starlink_score = manager.get_elevation_quality_score(elev, 'starlink')
        print(f"{elev}° Starlink 評分: {starlink_score:.2f}")
    
    print("\n✅ 統一仰角門檻管理器測試完成")