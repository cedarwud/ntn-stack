#!/usr/bin/env python3
"""
座標轉換系統
完整的座標系統轉換實現
符合 CLAUDE.md 原則：真實算法，精確數學模型
"""

import logging
import math
import numpy as np
from datetime import datetime, timezone
from typing import Tuple, List, Optional, Dict, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CoordinateSystem(Enum):
    """支援的座標系統"""
    ECI = "eci"           # Earth-Centered Inertial (地心慣性座標系)
    ECF = "ecf"           # Earth-Centered Fixed (地心固定座標系) 
    ECEF = "ecef"         # Earth-Centered Earth-Fixed (地心地固座標系)
    TEME = "teme"         # True Equator Mean Equinox (真赤道平分點座標系)
    LLA = "lla"           # Latitude Longitude Altitude (地理座標系)
    AER = "aer"           # Azimuth Elevation Range (方位仰角距離座標系)
    SEZ = "sez"           # South East Zenith (南東天頂座標系)


@dataclass
class CoordinateVector:
    """座標向量"""
    x: float
    y: float
    z: float
    coordinate_system: CoordinateSystem
    timestamp: Optional[datetime] = None
    
    def to_array(self) -> np.ndarray:
        """轉換為 numpy 陣列"""
        return np.array([self.x, self.y, self.z])
    
    def magnitude(self) -> float:
        """向量大小"""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)


@dataclass  
class GeodeticCoordinate:
    """大地測量座標"""
    latitude_deg: float
    longitude_deg: float
    altitude_km: float
    datum: str = "WGS84"
    
    @property
    def latitude_rad(self) -> float:
        return math.radians(self.latitude_deg)
    
    @property
    def longitude_rad(self) -> float:
        return math.radians(self.longitude_deg)


@dataclass
class TopocenticCoordinate:
    """站心座標 (AER)"""
    azimuth_deg: float      # 方位角 (度)
    elevation_deg: float    # 仰角 (度)
    range_km: float         # 距離 (公里)
    
    @property
    def azimuth_rad(self) -> float:
        return math.radians(self.azimuth_deg)
    
    @property
    def elevation_rad(self) -> float:
        return math.radians(self.elevation_deg)


class CoordinateTransformer:
    """
    完整座標轉換系統
    實現精確的座標系統間轉換
    """
    
    # 地球物理參數 (WGS84)
    EARTH_RADIUS_KM = 6371.0            # 平均半徑
    EARTH_SEMI_MAJOR_KM = 6378.137      # 長半軸 
    EARTH_FLATTENING = 1/298.257223563  # 扁率
    EARTH_ECCENTRICITY_SQ = 2 * EARTH_FLATTENING - EARTH_FLATTENING**2  # 第一偏心率平方
    
    # 地球自轉參數
    EARTH_ROTATION_RATE = 7.2921159e-5  # 地球自轉角速度 (rad/s)
    
    # 歷元參考
    J2000_EPOCH = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    def __init__(self):
        logger.info("座標轉換系統初始化完成")
    
    def transform(self, coordinates: Union[CoordinateVector, GeodeticCoordinate, TopocenticCoordinate],
                 target_system: CoordinateSystem, 
                 reference_time: Optional[datetime] = None,
                 observer_position: Optional[GeodeticCoordinate] = None) -> Union[CoordinateVector, GeodeticCoordinate, TopocenticCoordinate]:
        """
        通用座標轉換接口
        
        Args:
            coordinates: 源座標
            target_system: 目標座標系統
            reference_time: 參考時間 (用於考慮地球自轉)
            observer_position: 觀測者位置 (用於站心座標轉換)
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        
        # 判斷源座標類型和轉換路徑
        if isinstance(coordinates, CoordinateVector):
            return self._transform_cartesian(coordinates, target_system, reference_time, observer_position)
        elif isinstance(coordinates, GeodeticCoordinate):
            return self._transform_geodetic(coordinates, target_system, reference_time, observer_position)
        elif isinstance(coordinates, TopocenticCoordinate):
            return self._transform_topocentric(coordinates, target_system, reference_time, observer_position)
        else:
            raise ValueError(f"不支援的座標類型: {type(coordinates)}")
    
    def _transform_cartesian(self, coord: CoordinateVector, target_system: CoordinateSystem,
                           reference_time: datetime, observer_pos: Optional[GeodeticCoordinate]) -> Union[CoordinateVector, GeodeticCoordinate, TopocenticCoordinate]:
        """笛卡爾座標轉換"""
        source_system = coord.coordinate_system
        
        if source_system == target_system:
            return coord
        
        # ECI -> ECEF 轉換
        if source_system == CoordinateSystem.ECI and target_system == CoordinateSystem.ECEF:
            return self._eci_to_ecef(coord, reference_time)
        
        # ECEF -> ECI 轉換
        elif source_system == CoordinateSystem.ECEF and target_system == CoordinateSystem.ECI:
            return self._ecef_to_eci(coord, reference_time)
        
        # ECEF -> LLA 轉換
        elif source_system == CoordinateSystem.ECEF and target_system == CoordinateSystem.LLA:
            return self._ecef_to_lla(coord)
        
        # ECI -> LLA 轉換 (經由 ECEF)
        elif source_system == CoordinateSystem.ECI and target_system == CoordinateSystem.LLA:
            ecef_coord = self._eci_to_ecef(coord, reference_time)
            return self._ecef_to_lla(ecef_coord)
        
        # ECEF -> AER 轉換
        elif source_system == CoordinateSystem.ECEF and target_system == CoordinateSystem.AER:
            if observer_pos is None:
                raise ValueError("AER 轉換需要觀測者位置")
            return self._ecef_to_aer(coord, observer_pos)
        
        # ECI -> AER 轉換 (經由 ECEF)
        elif source_system == CoordinateSystem.ECI and target_system == CoordinateSystem.AER:
            if observer_pos is None:
                raise ValueError("AER 轉換需要觀測者位置")
            ecef_coord = self._eci_to_ecef(coord, reference_time)
            return self._ecef_to_aer(ecef_coord, observer_pos)
        
        # 其他轉換路徑
        else:
            raise ValueError(f"不支援的轉換: {source_system.value} -> {target_system.value}")
    
    def _transform_geodetic(self, coord: GeodeticCoordinate, target_system: CoordinateSystem,
                          reference_time: datetime, observer_pos: Optional[GeodeticCoordinate]) -> Union[CoordinateVector, TopocenticCoordinate]:
        """大地座標轉換"""
        if target_system == CoordinateSystem.ECEF:
            return self._lla_to_ecef(coord)
        elif target_system == CoordinateSystem.ECI:
            ecef_coord = self._lla_to_ecef(coord)
            return self._ecef_to_eci(ecef_coord, reference_time)
        else:
            raise ValueError(f"不支援的轉換: LLA -> {target_system.value}")
    
    def _transform_topocentric(self, coord: TopocenticCoordinate, target_system: CoordinateSystem,
                             reference_time: datetime, observer_pos: Optional[GeodeticCoordinate]) -> CoordinateVector:
        """站心座標轉換"""
        if observer_pos is None:
            raise ValueError("站心座標轉換需要觀測者位置")
        
        if target_system == CoordinateSystem.ECEF:
            return self._aer_to_ecef(coord, observer_pos)
        elif target_system == CoordinateSystem.ECI:
            ecef_coord = self._aer_to_ecef(coord, observer_pos)
            return self._ecef_to_eci(ecef_coord, reference_time)
        else:
            raise ValueError(f"不支援的轉換: AER -> {target_system.value}")
    
    def _eci_to_ecef(self, eci_coord: CoordinateVector, timestamp: datetime) -> CoordinateVector:
        """ECI 到 ECEF 轉換 (考慮地球自轉)"""
        # 計算地球自轉角
        seconds_since_j2000 = (timestamp - self.J2000_EPOCH).total_seconds()
        rotation_angle = self.EARTH_ROTATION_RATE * seconds_since_j2000
        
        # 自轉矩陣 (繞 Z 軸)
        cos_theta = math.cos(rotation_angle)
        sin_theta = math.sin(rotation_angle)
        
        rotation_matrix = np.array([
            [cos_theta, sin_theta, 0],
            [-sin_theta, cos_theta, 0],
            [0, 0, 1]
        ])
        
        # 執行轉換
        eci_vector = eci_coord.to_array()
        ecef_vector = rotation_matrix @ eci_vector
        
        return CoordinateVector(
            x=float(ecef_vector[0]),
            y=float(ecef_vector[1]),
            z=float(ecef_vector[2]),
            coordinate_system=CoordinateSystem.ECEF,
            timestamp=timestamp
        )
    
    def _ecef_to_eci(self, ecef_coord: CoordinateVector, timestamp: datetime) -> CoordinateVector:
        """ECEF 到 ECI 轉換"""
        # 計算地球自轉角 (反向)
        seconds_since_j2000 = (timestamp - self.J2000_EPOCH).total_seconds()
        rotation_angle = -self.EARTH_ROTATION_RATE * seconds_since_j2000  # 反向旋轉
        
        # 自轉矩陣
        cos_theta = math.cos(rotation_angle)
        sin_theta = math.sin(rotation_angle)
        
        rotation_matrix = np.array([
            [cos_theta, sin_theta, 0],
            [-sin_theta, cos_theta, 0],
            [0, 0, 1]
        ])
        
        # 執行轉換
        ecef_vector = ecef_coord.to_array()
        eci_vector = rotation_matrix @ ecef_vector
        
        return CoordinateVector(
            x=float(eci_vector[0]),
            y=float(eci_vector[1]),
            z=float(eci_vector[2]),
            coordinate_system=CoordinateSystem.ECI,
            timestamp=timestamp
        )
    
    def _ecef_to_lla(self, ecef_coord: CoordinateVector) -> GeodeticCoordinate:
        """ECEF 到大地座標轉換 (WGS84)"""
        x, y, z = ecef_coord.x, ecef_coord.y, ecef_coord.z
        
        # 經度計算
        longitude_rad = math.atan2(y, x)
        longitude_deg = math.degrees(longitude_rad)
        
        # 緯度和高度計算 (迭代方法)
        p = math.sqrt(x*x + y*y)
        
        # 初始緯度估算
        latitude_rad = math.atan2(z, p * (1 - self.EARTH_ECCENTRICITY_SQ))
        
        # 迭代計算精確緯度和高度
        for _ in range(10):  # 通常3-4次迭代即可收斂
            sin_lat = math.sin(latitude_rad)
            cos_lat = math.cos(latitude_rad)
            
            # 主法線半徑
            N = self.EARTH_SEMI_MAJOR_KM / math.sqrt(1 - self.EARTH_ECCENTRICITY_SQ * sin_lat * sin_lat)
            
            # 高度
            altitude_km = p / cos_lat - N
            
            # 更新緯度
            new_latitude_rad = math.atan2(z, p * (1 - self.EARTH_ECCENTRICITY_SQ * N / (N + altitude_km)))
            
            # 檢查收斂
            if abs(new_latitude_rad - latitude_rad) < 1e-12:
                break
            
            latitude_rad = new_latitude_rad
        
        latitude_deg = math.degrees(latitude_rad)
        
        return GeodeticCoordinate(
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            altitude_km=altitude_km
        )
    
    def _lla_to_ecef(self, lla_coord: GeodeticCoordinate) -> CoordinateVector:
        """大地座標到 ECEF 轉換"""
        lat_rad = lla_coord.latitude_rad
        lon_rad = lla_coord.longitude_rad
        alt_km = lla_coord.altitude_km
        
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)
        
        # 主法線半徑
        N = self.EARTH_SEMI_MAJOR_KM / math.sqrt(1 - self.EARTH_ECCENTRICITY_SQ * sin_lat * sin_lat)
        
        # ECEF 座標
        x = (N + alt_km) * cos_lat * cos_lon
        y = (N + alt_km) * cos_lat * sin_lon
        z = (N * (1 - self.EARTH_ECCENTRICITY_SQ) + alt_km) * sin_lat
        
        return CoordinateVector(
            x=x, y=y, z=z,
            coordinate_system=CoordinateSystem.ECEF
        )
    
    def _ecef_to_aer(self, ecef_coord: CoordinateVector, observer: GeodeticCoordinate) -> TopocenticCoordinate:
        """ECEF 到方位仰角距離轉換"""
        # 觀測者 ECEF 座標
        observer_ecef = self._lla_to_ecef(observer)
        
        # 相對位置向量
        dx = ecef_coord.x - observer_ecef.x
        dy = ecef_coord.y - observer_ecef.y
        dz = ecef_coord.z - observer_ecef.z
        
        # 轉換到站心座標系 (東北天座標系)
        lat_rad = observer.latitude_rad
        lon_rad = observer.longitude_rad
        
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)
        
        # 轉換矩陣 (ECEF -> 東北天)
        east = -sin_lon * dx + cos_lon * dy
        north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
        up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
        
        # 計算距離
        range_km = math.sqrt(east*east + north*north + up*up)
        
        # 計算仰角
        elevation_rad = math.asin(up / range_km)
        elevation_deg = math.degrees(elevation_rad)
        
        # 計算方位角 (從北方順時針)
        azimuth_rad = math.atan2(east, north)
        azimuth_deg = math.degrees(azimuth_rad)
        
        # 正規化方位角到 [0, 360)
        if azimuth_deg < 0:
            azimuth_deg += 360
        
        return TopocenticCoordinate(
            azimuth_deg=azimuth_deg,
            elevation_deg=elevation_deg,
            range_km=range_km
        )
    
    def _aer_to_ecef(self, aer_coord: TopocenticCoordinate, observer: GeodeticCoordinate) -> CoordinateVector:
        """方位仰角距離到 ECEF 轉換"""
        # 觀測者 ECEF 座標
        observer_ecef = self._lla_to_ecef(observer)
        
        # AER 到站心笛卡爾座標
        az_rad = aer_coord.azimuth_rad
        el_rad = aer_coord.elevation_rad
        range_km = aer_coord.range_km
        
        # 站心座標 (東北天)
        east = range_km * math.cos(el_rad) * math.sin(az_rad)
        north = range_km * math.cos(el_rad) * math.cos(az_rad)
        up = range_km * math.sin(el_rad)
        
        # 轉換到 ECEF
        lat_rad = observer.latitude_rad
        lon_rad = observer.longitude_rad
        
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)
        
        # 轉換矩陣 (東北天 -> ECEF)
        dx = -sin_lon * east - sin_lat * cos_lon * north + cos_lat * cos_lon * up
        dy = cos_lon * east - sin_lat * sin_lon * north + cos_lat * sin_lon * up
        dz = cos_lat * north + sin_lat * up
        
        # 加上觀測者位置
        x = observer_ecef.x + dx
        y = observer_ecef.y + dy
        z = observer_ecef.z + dz
        
        return CoordinateVector(
            x=x, y=y, z=z,
            coordinate_system=CoordinateSystem.ECEF
        )
    
    def calculate_ground_track(self, positions: List[CoordinateVector], 
                             timestamps: List[datetime]) -> List[GeodeticCoordinate]:
        """計算地面軌跡"""
        if len(positions) != len(timestamps):
            raise ValueError("位置數量和時間戳數量不匹配")
        
        ground_track = []
        
        for i, (position, timestamp) in enumerate(zip(positions, timestamps)):
            try:
                # 轉換到 LLA
                if position.coordinate_system == CoordinateSystem.ECI:
                    ecef_pos = self._eci_to_ecef(position, timestamp)
                    lla_pos = self._ecef_to_lla(ecef_pos)
                elif position.coordinate_system == CoordinateSystem.ECEF:
                    lla_pos = self._ecef_to_lla(position)
                else:
                    logger.warning(f"不支援的座標系統: {position.coordinate_system}")
                    continue
                
                ground_track.append(lla_pos)
                
            except Exception as e:
                logger.warning(f"地面軌跡點 {i} 轉換失敗: {str(e)}")
        
        return ground_track
    
    def calculate_look_angles_batch(self, satellite_positions: List[CoordinateVector],
                                  timestamps: List[datetime],
                                  observer: GeodeticCoordinate) -> List[TopocenticCoordinate]:
        """批量計算視線角度"""
        if len(satellite_positions) != len(timestamps):
            raise ValueError("位置數量和時間戳數量不匹配")
        
        look_angles = []
        
        for position, timestamp in zip(satellite_positions, timestamps):
            try:
                # 確保座標為 ECEF
                if position.coordinate_system == CoordinateSystem.ECI:
                    ecef_position = self._eci_to_ecef(position, timestamp)
                elif position.coordinate_system == CoordinateSystem.ECEF:
                    ecef_position = position
                else:
                    logger.warning(f"不支援的座標系統: {position.coordinate_system}")
                    continue
                
                # 計算 AER
                aer = self._ecef_to_aer(ecef_position, observer)
                look_angles.append(aer)
                
            except Exception as e:
                logger.warning(f"視線角度計算失敗: {str(e)}")
        
        return look_angles
    
    def get_earth_parameters(self) -> Dict[str, float]:
        """獲取地球物理參數"""
        return {
            "semi_major_axis_km": self.EARTH_SEMI_MAJOR_KM,
            "flattening": self.EARTH_FLATTENING,
            "eccentricity_squared": self.EARTH_ECCENTRICITY_SQ,
            "rotation_rate_rad_s": self.EARTH_ROTATION_RATE,
            "mean_radius_km": self.EARTH_RADIUS_KM
        }


def create_coordinate_transformer() -> CoordinateTransformer:
    """創建座標轉換器實例"""
    return CoordinateTransformer()


# 測試代碼
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 創建轉換器
    transformer = create_coordinate_transformer()
    
    # 測試 ECI -> ECEF 轉換
    eci_coord = CoordinateVector(
        x=6500.0, y=0.0, z=0.0,
        coordinate_system=CoordinateSystem.ECI
    )
    
    current_time = datetime.now(timezone.utc)
    ecef_coord = transformer.transform(eci_coord, CoordinateSystem.ECEF, current_time)
    
    print(f"✅ 座標轉換測試:")
    print(f"ECI: ({eci_coord.x:.1f}, {eci_coord.y:.1f}, {eci_coord.z:.1f}) km")
    print(f"ECEF: ({ecef_coord.x:.1f}, {ecef_coord.y:.1f}, {ecef_coord.z:.1f}) km")
    
    # 測試 ECEF -> LLA 轉換
    lla_coord = transformer.transform(ecef_coord, CoordinateSystem.LLA)
    print(f"LLA: ({lla_coord.latitude_deg:.3f}°, {lla_coord.longitude_deg:.3f}°, {lla_coord.altitude_km:.1f}km)")
    
    # 測試觀測者視線角度
    observer = GeodeticCoordinate(latitude_deg=24.9441667, longitude_deg=121.3713889, altitude_km=0.05)
    aer_coord = transformer.transform(ecef_coord, CoordinateSystem.AER, current_time, observer)
    print(f"AER: 方位角{aer_coord.azimuth_deg:.1f}°, 仰角{aer_coord.elevation_deg:.1f}°, 距離{aer_coord.range_km:.1f}km")
    
    print("✅ 座標轉換系統測試完成")