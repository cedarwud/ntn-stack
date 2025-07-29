#!/usr/bin/env python3
"""
NTPU 可見性篩選器 - Phase 0.4
基於 5 度仰角閾值的衛星可見性篩選，專為 NTPU 觀測點優化
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class NTPUVisibilityFilter:
    """NTPU 座標特定可見性篩選器"""
    
    def __init__(self, coordinate_engine=None, cache_enabled: bool = True):
        """
        初始化 NTPU 可見性篩選器
        
        Args:
            coordinate_engine: CoordinateSpecificOrbitEngine 實例
            cache_enabled: 是否啟用結果緩存
        """
        # NTPU 固定座標
        self.observer_lat = 24.94417   # 24°56'39"N
        self.observer_lon = 121.37139  # 121°22'17"E
        self.observer_alt = 50.0       # 海拔50米
        self.min_elevation = 10.0      # 10度仰角閾值 (ITU-R P.618 合規標準)
        
        self.coordinate_engine = coordinate_engine
        self.cache_enabled = cache_enabled
        self.visibility_cache = {}
        
        # 篩選統計
        self.filter_stats = {
            'total_processed': 0,
            'visible_satellites': 0,
            'filtered_out': 0,
            'cache_hits': 0,
            'processing_time_seconds': 0.0
        }
        
        logger.info(f"NTPUVisibilityFilter 初始化")
        logger.info(f"  NTPU 座標: ({self.observer_lat:.5f}, {self.observer_lon:.5f})")
        logger.info(f"  最小仰角: {self.min_elevation}°")
        logger.info(f"  緩存啟用: {cache_enabled}")
    
    def is_satellite_visible(self, satellite_data: Dict[str, Any], 
                           reference_time: datetime) -> Dict[str, Any]:
        """
        檢查單顆衛星在 NTPU 的可見性
        
        Args:
            satellite_data: 衛星 TLE 數據
            reference_time: 參考時間
            
        Returns:
            Dict: 可見性分析結果
        """
        norad_id = satellite_data.get('norad_id', 0)
        cache_key = f"{norad_id}_{reference_time.strftime('%Y%m%d_%H')}"
        
        # 檢查緩存
        if self.cache_enabled and cache_key in self.visibility_cache:
            self.filter_stats['cache_hits'] += 1
            return self.visibility_cache[cache_key]
        
        try:
            if self.coordinate_engine is None:
                # 如果沒有座標引擎，使用簡化瞬時計算
                visibility_result = self._instantaneous_visibility_check(satellite_data, reference_time)
            else:
                # 使用精確瞬時計算
                visibility_data = self.coordinate_engine.compute_instantaneous_visibility(
                    satellite_data, reference_time
                )
                
                if 'error' not in visibility_data:
                    visibility_result = {
                        'is_visible': visibility_data['is_visible'],
                        'elevation': visibility_data.get('elevation', -90.0),
                        'azimuth': visibility_data.get('azimuth', 0.0),
                        'range_km': visibility_data.get('range_km', 0.0),
                        'calculation_method': 'instantaneous_precise',
                        'observation_time': visibility_data['observation_time']
                    }
                else:
                    visibility_result = {
                        'is_visible': False,
                        'error': visibility_data['error'],
                        'calculation_method': 'instantaneous_error'
                    }
            
            # 添加衛星基本信息
            visibility_result.update({
                'satellite_name': satellite_data.get('name', 'Unknown'),
                'norad_id': norad_id,
                'tle_date': satellite_data.get('tle_date', 'unknown'),
                'filter_timestamp': reference_time.isoformat()
            })
            
            # 緩存結果
            if self.cache_enabled:
                self.visibility_cache[cache_key] = visibility_result
            
            return visibility_result
            
        except Exception as e:
            logger.error(f"可見性檢查失敗 {satellite_data.get('name', 'Unknown')}: {e}")
            return {
                'is_visible': False,
                'error': str(e),
                'satellite_name': satellite_data.get('name', 'Unknown'),
                'norad_id': norad_id,
                'calculation_method': 'error'
            }
    
    def _instantaneous_visibility_check(self, satellite_data: Dict[str, Any], 
                                       reference_time: datetime) -> Dict[str, Any]:
        """
        瞬時可見性檢查 (簡化版本)
        僅計算特定時間點的可見性
        """
        try:
            from sgp4.api import Satrec, jday
            
            # 創建 SGP4 衛星對象
            satellite = Satrec.twoline2rv(satellite_data['line1'], satellite_data['line2'])
            
            # 轉換為 Julian Day
            jd, fr = jday(reference_time.year, reference_time.month, reference_time.day,
                         reference_time.hour, reference_time.minute, 
                         reference_time.second + reference_time.microsecond / 1e6)
            
            # SGP4 計算
            error, position, velocity = satellite.sgp4(jd, fr)
            
            if error == 0:
                # 簡化的仰角計算
                elevation = self._estimate_elevation(position)
                
                return {
                    'is_visible': elevation >= self.min_elevation,
                    'elevation': elevation,
                    'azimuth': 0.0,  # 簡化版本不計算方位角
                    'range_km': 0.0,  # 簡化版本不計算距離
                    'calculation_method': 'instantaneous_simple',
                    'observation_time': reference_time.isoformat()
                }
            else:
                return {
                    'is_visible': False,
                    'error': f'SGP4 calculation error: {error}',
                    'calculation_method': 'instantaneous_simple_error'
                }
            
        except Exception as e:
            return {
                'is_visible': False,
                'error': str(e),
                'calculation_method': 'instantaneous_simple_error'
            }
    
    def _estimate_elevation(self, eci_position: Tuple[float, float, float]) -> float:
        """
        估算仰角 (簡化計算)
        """
        from math import degrees, radians, sin, cos, sqrt, atan2
        
        x, y, z = eci_position
        
        # 轉換為弧度
        lat_rad = radians(self.observer_lat)
        lon_rad = radians(self.observer_lon)
        
        # 地球半徑 (km)
        earth_radius = 6371.0
        
        # 觀測點位置
        observer_x = earth_radius * cos(lat_rad) * cos(lon_rad)
        observer_y = earth_radius * cos(lat_rad) * sin(lon_rad)
        observer_z = earth_radius * sin(lat_rad)
        
        # 相對位置
        dx = x - observer_x
        dy = y - observer_y
        dz = z - observer_z
        
        # 簡化仰角計算
        ground_range = sqrt(dx*dx + dy*dy)
        elevation_rad = atan2(dz, ground_range)
        
        return degrees(elevation_rad)
    
    def filter_satellite_constellation(self, satellites: List[Dict[str, Any]], 
                                     reference_time: datetime = None,
                                     progress_callback: callable = None) -> Dict[str, Any]:
        """
        篩選整個衛星星座
        
        Args:
            satellites: 衛星列表
            reference_time: 參考時間
            progress_callback: 進度回調函數
            
        Returns:
            Dict: 篩選結果
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        
        start_time = datetime.now()
        
        logger.info(f"🔍 開始 NTPU 可見性篩選")
        logger.info(f"  輸入衛星數: {len(satellites)}")
        logger.info(f"  參考時間: {reference_time.isoformat()}")
        
        visible_satellites = []
        filtered_satellites = []
        
        self.filter_stats['total_processed'] = len(satellites)
        
        for i, satellite in enumerate(satellites):
            visibility_result = self.is_satellite_visible(satellite, reference_time)
            
            if visibility_result['is_visible']:
                # 添加可見性分析結果到衛星數據
                satellite_with_visibility = satellite.copy()
                satellite_with_visibility['ntpu_visibility'] = visibility_result
                visible_satellites.append(satellite_with_visibility)
            else:
                filtered_satellites.append({
                    'satellite_name': satellite.get('name', 'Unknown'),
                    'norad_id': satellite.get('norad_id', 0),
                    'filter_reason': visibility_result.get('error', 'Below elevation threshold')
                })
            
            # 進度回調
            if progress_callback and (i + 1) % 100 == 0:
                progress = (i + 1) / len(satellites) * 100
                progress_callback(progress, len(visible_satellites), len(filtered_satellites))
            
            # 進度日誌
            if (i + 1) % 500 == 0:
                progress = (i + 1) / len(satellites) * 100
                logger.info(f"  篩選進度: {i + 1}/{len(satellites)} ({progress:.1f}%)")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 更新統計
        self.filter_stats['visible_satellites'] = len(visible_satellites)
        self.filter_stats['filtered_out'] = len(filtered_satellites)
        self.filter_stats['processing_time_seconds'] = processing_time
        
        # 計算篩選效率
        filter_efficiency = (len(filtered_satellites) / len(satellites)) * 100 if satellites else 0
        
        result = {
            'filtering_completed_at': end_time.isoformat(),
            'reference_time': reference_time.isoformat(),
            'input_statistics': {
                'total_satellites': len(satellites),
                'processing_time_seconds': processing_time
            },
            'filtering_results': {
                'visible_satellites': len(visible_satellites),
                'filtered_out_satellites': len(filtered_satellites),
                'filter_efficiency_percent': filter_efficiency,
                'cache_hit_rate': (self.filter_stats['cache_hits'] / len(satellites) * 100) if satellites else 0
            },
            'visible_satellites': visible_satellites,
            'filtered_satellites': filtered_satellites[:100],  # 限制輸出大小
            'ntpu_observer_config': {
                'latitude': self.observer_lat,
                'longitude': self.observer_lon,
                'altitude_m': self.observer_alt,
                'min_elevation_deg': self.min_elevation
            }
        }
        
        logger.info("✅ NTPU 可見性篩選完成")
        logger.info(f"  可見衛星: {len(visible_satellites)}")
        logger.info(f"  篩選掉: {len(filtered_satellites)}")
        logger.info(f"  篩選效率: {filter_efficiency:.1f}%")
        logger.info(f"  處理時間: {processing_time:.1f} 秒")
        
        return result
    
    def get_visibility_statistics(self) -> Dict[str, Any]:
        """獲取篩選統計信息"""
        return {
            'filter_statistics': self.filter_stats.copy(),
            'cache_statistics': {
                'enabled': self.cache_enabled,
                'cache_size': len(self.visibility_cache) if self.cache_enabled else 0,
                'hit_rate_percent': (self.filter_stats['cache_hits'] / 
                                   max(self.filter_stats['total_processed'], 1)) * 100
            },
            'observer_configuration': {
                'location': 'NTPU',
                'coordinates': {
                    'lat': self.observer_lat,
                    'lon': self.observer_lon,
                    'alt_m': self.observer_alt
                },
                'min_elevation_deg': self.min_elevation
            }
        }
    
    def clear_cache(self):
        """清除可見性緩存"""
        if self.cache_enabled:
            cache_size = len(self.visibility_cache)
            self.visibility_cache.clear()
            logger.info(f"清除可見性緩存: {cache_size} 個條目")
    
    def export_filtering_report(self, output_path: Path) -> bool:
        """導出篩選報告"""
        try:
            report = {
                'report_generated_at': datetime.now(timezone.utc).isoformat(),
                'filter_type': 'NTPU_visibility_filter',
                'statistics': self.get_visibility_statistics(),
                'configuration': {
                    'observer_location': 'NTPU',
                    'coordinates': {
                        'latitude': self.observer_lat,
                        'longitude': self.observer_lon,
                        'altitude_meters': self.observer_alt
                    },
                    'filtering_criteria': {
                        'min_elevation_degrees': self.min_elevation,
                        'cache_enabled': self.cache_enabled
                    }
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"篩選報告已導出: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"導出篩選報告失敗: {e}")
            return False


def create_ntpu_filter(coordinate_engine=None, cache_enabled: bool = True) -> NTPUVisibilityFilter:
    """創建 NTPU 可見性篩選器實例"""
    return NTPUVisibilityFilter(coordinate_engine=coordinate_engine, cache_enabled=cache_enabled)


if __name__ == "__main__":
    # 示例使用
    print("🔍 NTPU 可見性篩選器測試")
    
    # 創建篩選器
    filter_instance = create_ntpu_filter(cache_enabled=True)
    
    print(f"篩選器已初始化")
    print(f"NTPU 座標: ({filter_instance.observer_lat:.5f}, {filter_instance.observer_lon:.5f})")
    print(f"最小仰角: {filter_instance.min_elevation}°")
    
    # 獲取統計信息
    stats = filter_instance.get_visibility_statistics()
    print(f"緩存狀態: {stats['cache_statistics']['enabled']}")