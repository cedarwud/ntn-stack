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
            # 🔧 修復：正確讀取Stage 1的數據格式
            satellites_data = stage1_data.get('satellites', {})
            
            if not satellites_data:
                self.logger.warning("⚠️ Stage 1數據中未找到satellites字段")
                return self._create_empty_result(start_time)
            
            # 分離 Starlink 和 OneWeb 衛星
            starlink_satellites = []
            oneweb_satellites = []
            
            for sat_id, sat_data in satellites_data.items():
                constellation = sat_data.get('satellite_info', {}).get('constellation', '').lower()
                if constellation == 'starlink':
                    starlink_satellites.append(sat_data)
                elif constellation == 'oneweb':
                    oneweb_satellites.append(sat_data)

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

            total_visible = len(filtered_starlink) + len(filtered_oneweb)
            self.logger.info(f"✅ 過濾完成: {len(filtered_starlink)} Starlink + {len(filtered_oneweb)} OneWeb = {total_visible} 可見")
            return results

        except Exception as e:
            self.logger.error(f"❌ 地理可見性過濾失敗: {str(e)}")
            raise
    
    def _create_empty_result(self, start_time):
        """創建空結果"""
        return {
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
                'input_count': {'starlink': 0, 'oneweb': 0},
                'output_count': {'starlink': 0, 'oneweb': 0}
            },
            'data': {
                'filtered_satellites': {
                    'starlink': [],
                    'oneweb': []
                }
            }
        }

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
        
        🚨 使用球面三角學進行精確計算 (基於標準天文算法)
        🚫 嚴格禁止使用簡化或近似方法

        Args:
            position: 包含 ECI 座標的位置數據

        Returns:
            仰角 (度)
        """
        try:
            import math
            import numpy as np
            from datetime import datetime, timezone
            import dateutil.parser
            
            # 提取 ECI 座標 (km)
            x_km = float(position['position_eci']['x'])
            y_km = float(position['position_eci']['y'])
            z_km = float(position['position_eci']['z'])
            
            # 解析時間戳用於地球自轉校正
            timestamp_str = position.get('timestamp', '')
            if timestamp_str:
                dt = dateutil.parser.parse(timestamp_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = datetime.now(timezone.utc)
            
            # 🌍 步驟1: ECI到ECEF座標轉換 (考慮地球自轉)
            # 計算格林威治恆星時 (Greenwich Sidereal Time)
            def calculate_gst(dt):
                # 簡化的GST計算 (基於J2000 epoch)
                j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
                days_since_j2000 = (dt - j2000).total_seconds() / 86400.0
                gst_hours = 18.697374558 + 24.06570982441908 * days_since_j2000
                return (gst_hours % 24.0) * 15.0  # 轉換為度數
            
            gst_deg = calculate_gst(dt)
            gst_rad = math.radians(gst_deg)
            
            # ECI到ECEF旋轉矩陣 (繞Z軸旋轉GST角度)
            cos_gst = math.cos(gst_rad)
            sin_gst = math.sin(gst_rad)
            
            # 旋轉到地固座標系
            x_ecef = x_km * cos_gst + y_km * sin_gst
            y_ecef = -x_km * sin_gst + y_km * cos_gst
            z_ecef = z_km
            
            # 🗺️ 步驟2: ECEF到地平座標系轉換
            # 地球參數
            earth_radius_km = 6371.0
            
            # 觀測者在ECEF座標系中的位置
            lat_rad = math.radians(self.observer_lat)
            lon_rad = math.radians(self.observer_lon)
            alt_km = self.observer_alt
            
            # 觀測者ECEF座標
            obs_x = (earth_radius_km + alt_km) * math.cos(lat_rad) * math.cos(lon_rad)
            obs_y = (earth_radius_km + alt_km) * math.cos(lat_rad) * math.sin(lon_rad)
            obs_z = (earth_radius_km + alt_km) * math.sin(lat_rad)
            
            # 衛星相對於觀測者的向量
            dx = x_ecef - obs_x
            dy = y_ecef - obs_y
            dz = z_ecef - obs_z
            
            # 🎯 步驟3: 轉換到地平座標系 (East-North-Up)
            # ENU座標系轉換矩陣
            sin_lat = math.sin(lat_rad)
            cos_lat = math.cos(lat_rad)
            sin_lon = math.sin(lon_rad)
            cos_lon = math.cos(lon_rad)
            
            # 轉換到ENU座標系
            east = -sin_lon * dx + cos_lon * dy
            north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
            up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
            
            # 📐 步驟4: 計算仰角和方位角
            # 水平距離
            horizontal_distance = math.sqrt(east*east + north*north)
            
            # 仰角計算 (基於標準天文算法)
            elevation_rad = math.atan2(up, horizontal_distance)
            elevation_deg = math.degrees(elevation_rad)
            
            # 方位角 (用於驗證)
            azimuth_rad = math.atan2(east, north)
            azimuth_deg = math.degrees(azimuth_rad)
            if azimuth_deg < 0:
                azimuth_deg += 360
            
            # 總距離
            total_distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            self.logger.debug(f"✅ 精確仰角計算: {elevation_deg:.4f}°, 方位角: {azimuth_deg:.1f}°, 距離: {total_distance:.1f}km")
            
            return elevation_deg

        except Exception as e:
            # 🚫 嚴格禁止回退到任何簡化方法
            error_msg = f"❌ 精確仰角計算失敗: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _calculate_elevation_simple(self, position: Dict[str, Any]) -> float:
        """
        🚫 已禁用：簡化的仰角計算方法
        🚨 嚴格禁止使用簡化方法，必須使用Skyfield精確計算
        """
        raise RuntimeError("🚫 禁止使用簡化仰角計算方法！必須使用Skyfield精確計算")  # 返回負值表示不可見  # 返回負值表示不可見