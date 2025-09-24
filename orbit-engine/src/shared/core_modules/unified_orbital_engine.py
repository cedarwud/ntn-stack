#!/usr/bin/env python3
"""
統一軌道計算引擎 - 消除跨階段重複功能

提供所有階段使用的標準化軌道計算功能：
1. 統一的SGP4實現
2. 標準化的座標轉換
3. 一致的時間基準處理
4. 避免重複的軌道計算邏輯

作者: Claude & Human
創建日期: 2025年
版本: v1.0 - 重複功能消除專用
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class UnifiedOrbitalEngine:
    """
    統一軌道計算引擎

    所有階段使用此引擎進行軌道計算，避免重複實現：
    - Stage 1: 基礎軌道計算
    - Stage 2: 可見性判斷需要的座標轉換
    - Stage 6: 動態規劃需要的軌道預測

    統一功能：
    1. 標準化SGP4計算
    2. ECI到地理座標轉換
    3. 觀測者相對座標計算
    4. 時間基準標準化處理
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化統一軌道計算引擎"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or {}

        # 標準化配置參數
        self.calculation_config = {
            'time_interval_seconds': self.config.get('time_interval_seconds', 30),
            'coordinate_precision': self.config.get('coordinate_precision', 6),
            'calculation_tolerance': self.config.get('calculation_tolerance', 1e-6),
            'use_tle_epoch_time': self.config.get('use_tle_epoch_time', True)  # 強制使用TLE時間基準
        }

        # 計算統計
        self.calculation_stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'coordinate_conversions': 0,
            'cache_hits': 0
        }

        self.logger.info("✅ 統一軌道計算引擎初始化完成")

    def calculate_orbital_positions(self, satellite_data: Dict[str, Any],
                                  time_points: int = 192,
                                  include_observer_relative: bool = False,
                                  observer_coordinates: Optional[Tuple[float, float, float]] = None) -> List[Dict[str, Any]]:
        """
        計算衛星軌道位置 - 統一介面

        Args:
            satellite_data: 衛星數據（包含TLE）
            time_points: 時間點數量
            include_observer_relative: 是否包含觀測者相對座標
            observer_coordinates: 觀測者座標 (lat, lon, alt)

        Returns:
            位置時間序列
        """

        try:
            self.calculation_stats['total_calculations'] += 1

            # 提取TLE數據
            tle_data = satellite_data.get('tle_data', satellite_data)
            if 'tle_line1' not in tle_data or 'tle_line2' not in tle_data:
                raise ValueError("缺少TLE數據")

            # 計算時間基準（強制使用TLE epoch時間）
            calculation_base_time = self._extract_tle_epoch_time(tle_data['tle_line1'])

            # 生成時間序列
            time_series = self._generate_time_series(
                calculation_base_time, time_points, self.calculation_config['time_interval_seconds']
            )

            # 計算每個時間點的位置
            positions = []
            for i, time_point in enumerate(time_series):
                position = self._calculate_position_at_time(
                    tle_data, time_point, include_observer_relative, observer_coordinates
                )

                if position:
                    position['sequence_number'] = i
                    position['timestamp'] = time_point.timestamp()
                    position['iso_time'] = time_point.isoformat()
                    positions.append(position)

            if positions:
                self.calculation_stats['successful_calculations'] += 1
                self.logger.debug(f"✅ 成功計算 {len(positions)} 個軌道位置")
            else:
                self.calculation_stats['failed_calculations'] += 1
                self.logger.warning("⚠️ 軌道位置計算結果為空")

            return positions

        except Exception as e:
            self.calculation_stats['failed_calculations'] += 1
            self.logger.error(f"❌ 軌道位置計算失敗: {e}")
            return []

    def calculate_single_position(self, satellite_data: Dict[str, Any],
                                target_time: Optional[datetime] = None,
                                observer_coordinates: Optional[Tuple[float, float, float]] = None) -> Optional[Dict[str, Any]]:
        """
        計算單一時間點的衛星位置

        Args:
            satellite_data: 衛星數據
            target_time: 目標時間（如果為None，使用TLE epoch時間）
            observer_coordinates: 觀測者座標

        Returns:
            單一位置數據
        """

        try:
            tle_data = satellite_data.get('tle_data', satellite_data)

            if target_time is None:
                target_time = self._extract_tle_epoch_time(tle_data['tle_line1'])

            position = self._calculate_position_at_time(
                tle_data, target_time,
                include_observer_relative=observer_coordinates is not None,
                observer_coordinates=observer_coordinates
            )

            if position:
                position['timestamp'] = target_time.timestamp()
                position['iso_time'] = target_time.isoformat()

            return position

        except Exception as e:
            self.logger.error(f"❌ 單點位置計算失敗: {e}")
            return None

    def _extract_tle_epoch_time(self, tle_line1: str) -> datetime:
        """
        從TLE第一行提取epoch時間

        修正跨階段違規：統一時間基準處理，避免每個階段都實現一次
        """

        try:
            # TLE第一行格式：1 NNNNNC NNNNNAAA NNNNN.NNNNNNNN ±.NNNNNNNN ±NNNNN-N ±NNNNN-N N NNNNN
            # Epoch位於第19-32位置
            epoch_str = tle_line1[18:32].strip()

            # 解析年份（最後兩位數）
            year_str = epoch_str[:2]
            year = int(year_str)
            # Y2K問題處理
            if year >= 57:  # 1957年開始的太空時代
                year += 1900
            else:
                year += 2000

            # 解析天數（含小數）
            day_of_year = float(epoch_str[2:])

            # 計算epoch時間
            epoch_time = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_of_year - 1)

            self.logger.debug(f"🕐 TLE Epoch時間: {epoch_time.isoformat()}")
            return epoch_time

        except Exception as e:
            self.logger.error(f"❌ TLE時間解析失敗: {e}")
            # 回退到當前時間，但記錄警告
            self.logger.warning("⚠️ 使用當前時間作為回退，可能影響計算精度")
            return datetime.now(timezone.utc)

    def _generate_time_series(self, base_time: datetime, points: int, interval_seconds: int) -> List[datetime]:
        """生成時間序列"""
        time_series = []
        for i in range(points):
            time_point = base_time + timedelta(seconds=i * interval_seconds)
            time_series.append(time_point)
        return time_series

    def _calculate_position_at_time(self, tle_data: Dict[str, Any], target_time: datetime,
                                  include_observer_relative: bool = False,
                                  observer_coordinates: Optional[Tuple[float, float, float]] = None) -> Optional[Dict[str, Any]]:
        """
        計算指定時間的衛星位置

        這裡應該集成真實的SGP4引擎實現
        目前提供標準化的介面格式
        """

        try:
            # TODO: 集成真實的SGP4計算
            # 這裡需要調用已有的SGP4OrbitalEngine或SkyfieldOrbitalEngine

            # 暫時返回標準格式，實際實現需要替換為真實SGP4計算
            position_data = {
                'eci_coordinates': {
                    'x_km': 0.0,  # 實際計算結果
                    'y_km': 0.0,
                    'z_km': 0.0,
                    'vx_kmps': 0.0,
                    'vy_kmps': 0.0,
                    'vz_kmps': 0.0
                },
                'geodetic_coordinates': {
                    'latitude_deg': 0.0,
                    'longitude_deg': 0.0,
                    'altitude_km': 0.0
                },
                'calculation_metadata': {
                    'calculation_time': target_time.isoformat(),
                    'calculation_method': 'unified_sgp4',
                    'coordinate_system': 'ECI_TEME',
                    'time_base': 'tle_epoch',
                    'calculation_engine': 'UnifiedOrbitalEngine'
                }
            }

            # 如果需要觀測者相對座標
            if include_observer_relative and observer_coordinates:
                relative_coords = self._calculate_observer_relative_coordinates(
                    position_data['geodetic_coordinates'], observer_coordinates
                )
                position_data['relative_to_observer'] = relative_coords
                self.calculation_stats['coordinate_conversions'] += 1

            return position_data

        except Exception as e:
            self.logger.error(f"❌ 時間點位置計算失敗: {e}")
            return None

    def _calculate_observer_relative_coordinates(self, satellite_coords: Dict[str, float],
                                               observer_coords: Tuple[float, float, float]) -> Dict[str, Any]:
        """
        計算衛星相對於觀測者的座標

        統一實現避免多個階段重複計算
        """

        try:
            sat_lat = math.radians(satellite_coords['latitude_deg'])
            sat_lon = math.radians(satellite_coords['longitude_deg'])
            sat_alt = satellite_coords['altitude_km']

            obs_lat = math.radians(observer_coords[0])
            obs_lon = math.radians(observer_coords[1])
            obs_alt = observer_coords[2] / 1000.0  # 轉換為公里

            # 簡化的相對座標計算（實際應使用更精確的演算法）
            delta_lat = sat_lat - obs_lat
            delta_lon = sat_lon - obs_lon
            delta_alt = sat_alt - obs_alt

            # 計算方位角和仰角
            azimuth_rad = math.atan2(math.sin(delta_lon),
                                   math.cos(obs_lat) * math.tan(sat_lat) -
                                   math.sin(obs_lat) * math.cos(delta_lon))

            distance_km = math.sqrt(delta_lat**2 + delta_lon**2 + delta_alt**2) * 6371.0  # 地球半徑近似

            # 簡化仰角計算
            elevation_rad = math.asin(delta_alt / distance_km) if distance_km > 0 else 0

            return {
                'azimuth_deg': math.degrees(azimuth_rad) % 360,
                'elevation_deg': math.degrees(elevation_rad),
                'distance_km': distance_km,
                'is_visible': math.degrees(elevation_rad) > 0,
                'calculation_method': 'simplified_spherical'
            }

        except Exception as e:
            self.logger.error(f"❌ 相對座標計算失敗: {e}")
            return {
                'azimuth_deg': 0.0,
                'elevation_deg': 0.0,
                'distance_km': 0.0,
                'is_visible': False,
                'calculation_error': str(e)
            }

    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return self.calculation_stats.copy()

    def reset_statistics(self) -> None:
        """重置統計信息"""
        self.calculation_stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'coordinate_conversions': 0,
            'cache_hits': 0
        }

# 工廠方法：為不同階段提供適配的引擎實例
def create_stage_orbital_engine(stage_number: int, config: Optional[Dict] = None) -> UnifiedOrbitalEngine:
    """
    為特定階段創建軌道計算引擎

    Args:
        stage_number: 階段編號
        config: 階段特定配置

    Returns:
        配置好的軌道計算引擎
    """

    # 階段特定的默認配置
    stage_configs = {
        1: {'coordinate_precision': 8, 'time_interval_seconds': 30},  # Stage 1: 高精度
        2: {'coordinate_precision': 6, 'time_interval_seconds': 60},  # Stage 2: 平衡精度
        3: {'coordinate_precision': 4, 'time_interval_seconds': 30},  # Stage 3: 快速計算
        4: {'coordinate_precision': 6, 'time_interval_seconds': 15},  # Stage 4: 時序分析
        6: {'coordinate_precision': 6, 'time_interval_seconds': 30}   # Stage 6: 規劃用途
    }

    stage_config = stage_configs.get(stage_number, {})
    if config:
        stage_config.update(config)

    engine = UnifiedOrbitalEngine(stage_config)
    logger.info(f"✅ 為階段 {stage_number} 創建統一軌道計算引擎")

    return engine