"""
簡化階段二：基本地理可見性過濾
只負責 ECI→地平座標轉換和仰角門檻過濾
"""

import logging
import json
import gzip
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
import numpy as np
from skyfield.api import EarthSatellite, wgs84
from skyfield.timelib import Time
from skyfield import almanac

class SimpleGeographicFilter:
    """簡化地理可見性過濾器 - 只處理座標轉換和仰角過濾"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # NTPU 座標 (固定值，避免依賴配置系統)
        self.observer_lat = 24.9441  # 24°56'39"N
        self.observer_lon = 121.3714  # 121°22'17"E
        self.observer_alt = 0.0  # 海平面

        # 星座仰角門檻 (來自衛星換手標準)
        self.elevation_thresholds = {
            'starlink': 5.0,  # 5度 (低軌高速)
            'oneweb': 10.0    # 10度 (更保守)
        }

        self.logger.info(f"🎯 初始化簡化地理過濾器 - NTPU座標: ({self.observer_lat:.4f}°N, {self.observer_lon:.4f}°E)")

    def filter_visible_satellites(self, stage1_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行基本地理可見性過濾

        Args:
            stage1_data: Stage 1 軌道計算結果

        Returns:
            過濾後的可見衛星數據
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始基本地理可見性過濾")

        try:
            # 使用統一的數據格式適配工具函數
            from ...shared.utils import parse_satellite_data_format
            
            satellites_data = stage1_data.get('data', {})
            starlink_satellites, oneweb_satellites = parse_satellite_data_format(satellites_data)

            self.logger.info(f"📥 輸入數據: {len(starlink_satellites)} Starlink + {len(oneweb_satellites)} OneWeb")

            # 過濾各星座
            filtered_starlink = self._filter_constellation(starlink_satellites, 'starlink')
            filtered_oneweb = self._filter_constellation(oneweb_satellites, 'oneweb')

            # 組織結果
            results = {
                'metadata': {
                    'stage': 'stage2_visibility_filter',
                    'processor': 'SimpleGeographicFilter',
                    'execution_time': (datetime.now(timezone.utc) - start_time).total_seconds(),
                    'observer_coordinates': {
                        'latitude': self.observer_lat,
                        'longitude': self.observer_lon,
                        'altitude_m': self.observer_alt
                    },
                    'elevation_thresholds': self.elevation_thresholds,
                    'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                    'input_count': {
                        'starlink': len(starlink_satellites),
                        'oneweb': len(oneweb_satellites)
                    },
                    'output_count': {
                        'starlink': len(filtered_starlink),
                        'oneweb': len(filtered_oneweb)
                    }
                },
                'data': {
                    'filtered_satellites': {
                        'starlink': filtered_starlink,
                        'oneweb': filtered_oneweb
                    }
                }
            }

            self.logger.info(f"✅ 過濾完成: {len(filtered_starlink)} Starlink + {len(filtered_oneweb)} OneWeb 可見")
            return results

        except Exception as e:
            self.logger.error(f"❌ 地理可見性過濾失敗: {str(e)}")
            raise

    def _filter_constellation(self, satellites: List[Dict], constellation: str) -> List[Dict]:
        """過濾單一星座的可見衛星"""
        threshold = self.elevation_thresholds[constellation]
        visible_satellites = []

        self.logger.info(f"🔍 過濾 {constellation} 星座 (仰角門檻: {threshold}°)")

        for sat_data in satellites:
            try:
                # 提取位置時間序列 - 適配新的數據格式
                position_timeseries = sat_data.get('orbital_positions', [])  # 修正字段名稱
                if not position_timeseries:
                    # 嘗試舊格式
                    position_timeseries = sat_data.get('position_timeseries', [])
                    
                if not position_timeseries:
                    continue

                # 計算地平座標
                visible_positions = []
                for pos in position_timeseries:
                    elevation = self._calculate_elevation(pos)
                    if elevation >= threshold:
                        # 保留可見時刻的位置數據
                        pos_copy = pos.copy()
                        pos_copy['elevation_deg'] = round(elevation, 4)
                        visible_positions.append(pos_copy)

                # 如果有可見時刻，保留該衛星
                if visible_positions:
                    filtered_sat = sat_data.copy()
                    filtered_sat['orbital_positions'] = visible_positions  # 保持原始字段名稱
                    filtered_sat['visibility_summary'] = {
                        'total_positions': len(position_timeseries),
                        'visible_positions': len(visible_positions),
                        'visibility_ratio': round(len(visible_positions) / len(position_timeseries), 4),
                        'max_elevation_deg': round(max(pos['elevation_deg'] for pos in visible_positions), 4)
                    }
                    visible_satellites.append(filtered_sat)

            except Exception as e:
                sat_name = sat_data.get('satellite_info', {}).get('name', 'unknown')
                self.logger.warning(f"⚠️ 衛星 {sat_name} 處理失敗: {str(e)}")
                continue

        self.logger.info(f"📊 {constellation}: {len(visible_satellites)}/{len(satellites)} 衛星可見")
        return visible_satellites

    def _calculate_elevation(self, position: Dict[str, Any]) -> float:
        """
        計算衛星相對於觀測者的仰角

        Args:
            position: 包含 ECI 座標的位置數據

        Returns:
            仰角 (度)
        """
        try:
            # 提取 ECI 座標 (km)
            x_km = position['position_eci']['x']
            y_km = position['position_eci']['y']
            z_km = position['position_eci']['z']

            # 轉換為地平座標系統
            # 簡化計算：使用球面三角學

            # 地球中心到觀測者的向量 (地心地固座標)
            earth_radius_km = 6371.0
            obs_x = earth_radius_km * np.cos(np.radians(self.observer_lat)) * np.cos(np.radians(self.observer_lon))
            obs_y = earth_radius_km * np.cos(np.radians(self.observer_lat)) * np.sin(np.radians(self.observer_lon))
            obs_z = earth_radius_km * np.sin(np.radians(self.observer_lat))

            # 衛星相對於觀測者的向量
            sat_rel_x = x_km - obs_x
            sat_rel_y = y_km - obs_y
            sat_rel_z = z_km - obs_z

            # 計算距離
            distance = np.sqrt(sat_rel_x**2 + sat_rel_y**2 + sat_rel_z**2)

            # 計算仰角 (簡化方法)
            # 地平面法向量 (指向天頂)
            zenith_x = obs_x / earth_radius_km
            zenith_y = obs_y / earth_radius_km
            zenith_z = obs_z / earth_radius_km

            # 衛星方向向量 (單位化)
            sat_unit_x = sat_rel_x / distance
            sat_unit_y = sat_rel_y / distance
            sat_unit_z = sat_rel_z / distance

            # 仰角 = 90° - 天頂角
            cos_zenith_angle = sat_unit_x * zenith_x + sat_unit_y * zenith_y + sat_unit_z * zenith_z
            zenith_angle_rad = np.arccos(np.clip(cos_zenith_angle, -1.0, 1.0))
            elevation_rad = np.pi/2 - zenith_angle_rad
            elevation_deg = np.degrees(elevation_rad)

            return elevation_deg

        except Exception as e:
            self.logger.warning(f"⚠️ 仰角計算失敗: {str(e)}")
            return -90.0  # 返回負值表示不可見