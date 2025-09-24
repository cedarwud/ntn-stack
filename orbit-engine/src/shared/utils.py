# 🛰️ 共享工具函數
"""
Shared Utilities - Phase 1系統通用工具函數
功能: 提供跨階段使用的通用工具和輔助函數
"""

import math
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Dict, Optional
import logging
# 🚨 Grade A要求：使用學術級物理常數
from shared.constants.physics_constants import PhysicsConstants
physics_consts = PhysicsConstants()


# 物理常數
EARTH_RADIUS_KM = 6371.0
LIGHT_SPEED_M_S = physics_consts.SPEED_OF_LIGHT
GRAVITATIONAL_PARAMETER = 398600.4418  # km³/s²

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """設置標準化日誌記錄器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重複添加處理器
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """計算兩個地理座標間的距離 (公里)"""
    
    # 轉換為弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine公式
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS_KM * c

def calculate_elevation_azimuth(observer_lat: float, observer_lon: float,
                              satellite_lat: float, satellite_lon: float,
                              satellite_alt_km: float) -> Tuple[float, float, float]:
    """計算衛星的仰角、方位角和距離"""
    
    try:
        # 轉換為弧度
        obs_lat_rad = math.radians(observer_lat)
        obs_lon_rad = math.radians(observer_lon)
        sat_lat_rad = math.radians(satellite_lat)
        sat_lon_rad = math.radians(satellite_lon)
        
        # 計算地面距離
        ground_distance = calculate_distance_km(observer_lat, observer_lon,
                                              satellite_lat, satellite_lon)
        
        # 計算3D距離
        distance_3d = math.sqrt(ground_distance**2 + satellite_alt_km**2)
        
        # 計算仰角
        if ground_distance > 0:
            elevation_rad = math.atan2(satellite_alt_km, ground_distance)
            elevation_deg = math.degrees(elevation_rad)
        else:
            elevation_deg = 90.0  # 衛星直接在頭頂
        
        # 計算方位角
        dlon = sat_lon_rad - obs_lon_rad
        y = math.sin(dlon) * math.cos(sat_lat_rad)
        x = (math.cos(obs_lat_rad) * math.sin(sat_lat_rad) - 
             math.sin(obs_lat_rad) * math.cos(sat_lat_rad) * math.cos(dlon))
        
        azimuth_rad = math.atan2(y, x)
        azimuth_deg = (math.degrees(azimuth_rad) + 360) % 360
        
        return elevation_deg, azimuth_deg, distance_3d
        
    except Exception as e:
        # 計算失敗時返回預設值
        return -90.0, 0.0, float('inf')

def calculate_doppler_shift(satellite_velocity_km_s: float,
                          elevation_deg: float,
                          frequency_hz: float) -> float:
    """計算都卜勒頻移"""
    
    try:
        # 徑向速度分量 (朝向/遠離觀測者)
        radial_velocity_m_s = satellite_velocity_km_s * 1000 * math.cos(math.radians(elevation_deg))
        
        # 都卜勒頻移計算
        doppler_shift = frequency_hz * (radial_velocity_m_s / LIGHT_SPEED_M_S)
        
        return doppler_shift
        
    except Exception:
        return 0.0

def calculate_free_space_path_loss(distance_km: float, frequency_ghz: float) -> float:
    """計算自由空間路徑損耗 (dB)"""
    
    try:
        # FSPL = 20*log10(d) + 20*log10(f) + 32.45
        # d: 距離(km), f: 頻率(GHz)
        fspl_db = (20 * math.log10(distance_km) + 
                  20 * math.log10(frequency_ghz) + 
                  32.45)
        
        return fspl_db
        
    except Exception:
        return 200.0  # 返回高損耗值

def calculate_propagation_delay(distance_km: float) -> float:
    """計算傳播延遲 (毫秒)"""
    
    try:
        delay_ms = (distance_km * 1000) / LIGHT_SPEED_M_S * 1000
        return delay_ms
        
    except Exception:
        return 0.0

def normalize_angle_degrees(angle_deg: float) -> float:
    """正規化角度到 [0, 360) 範圍"""
    return angle_deg % 360.0

def normalize_angle_180(angle_deg: float) -> float:
    """正規化角度到 [-180, 180] 範圍"""
    angle = angle_deg % 360.0
    return angle - 360.0 if angle > 180.0 else angle

def is_satellite_visible(elevation_deg: float, min_elevation_deg: float = 5.0) -> bool:
    """檢查衛星是否可見"""
    return elevation_deg >= min_elevation_deg

def calculate_orbital_period(semi_major_axis_km: float) -> float:
    """計算軌道週期 (分鐘)"""
    
    try:
        # 克卜勒第三定律
        period_seconds = 2 * math.pi * math.sqrt(semi_major_axis_km**3 / GRAVITATIONAL_PARAMETER)
        period_minutes = period_seconds / 60.0
        
        return period_minutes
        
    except Exception:
        return 96.0  # LEO典型週期

def calculate_altitude_from_period(period_minutes: float, eccentricity: float = 0.0) -> float:
    """從軌道週期計算高度"""
    
    try:
        period_seconds = period_minutes * 60.0
        semi_major_axis = (GRAVITATIONAL_PARAMETER * (period_seconds / (2 * math.pi))**2)**(1/3)
        
        # 對於圓軌道 (e≈0)
        altitude_km = semi_major_axis - EARTH_RADIUS_KM
        
        return altitude_km
        
    except Exception:
        return 550.0  # Starlink典型高度

def generate_time_series(start_time: datetime, 
                        duration_minutes: int,
                        resolution_seconds: int) -> List[datetime]:
    """生成時間序列"""
    
    time_points = []
    current_time = start_time
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    while current_time <= end_time:
        time_points.append(current_time)
        current_time += timedelta(seconds=resolution_seconds)
    
    return time_points

def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """計算統計指標"""
    
    if not values:
        return {
            'count': 0,
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'median': 0.0
        }
    
    np_values = np.array(values)
    
    return {
        'count': len(values),
        'mean': float(np.mean(np_values)),
        'std': float(np.std(np_values)),
        'min': float(np.min(np_values)),
        'max': float(np.max(np_values)),
        'median': float(np.median(np_values))
    }

def format_duration(seconds: float) -> str:
    """格式化持續時間"""
    
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分鐘"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小時"

def format_file_size(bytes_size: int) -> str:
    """格式化檔案大小"""
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    
    return f"{bytes_size:.1f}TB"

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """驗證座標有效性"""
    return -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0

def validate_elevation_threshold(threshold: float) -> bool:
    """驗證仰角門檻有效性"""
    return 0.0 <= threshold <= 90.0

def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """創建進度條字符串"""
    
    if total == 0:
        return "[" + "=" * width + "] 100%"
    
    progress = current / total
    filled_width = int(width * progress)
    
    bar = "=" * filled_width + "-" * (width - filled_width)
    percentage = progress * 100
    
    return f"[{bar}] {percentage:.1f}%"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """安全除法，避免除零錯誤"""
    return numerator / denominator if denominator != 0 else default

def clamp(value: float, min_value: float, max_value: float) -> float:
    """將值限制在指定範圍內"""
    return max(min_value, min(value, max_value))

def interpolate_linear(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """線性插值"""
    
    if x2 == x1:
        return y1
    
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

# 時間相關工具
def utc_now() -> datetime:
    """獲取當前UTC時間"""
    return datetime.now(timezone.utc)

def format_utc_time(dt: datetime) -> str:
    """格式化UTC時間"""
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

def parse_iso_time(time_str: str) -> datetime:
    """解析ISO格式時間字符串"""
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    except Exception:
        return utc_now()

# 角度轉換工具
def degrees_to_radians(degrees: float) -> float:
    """度轉弧度"""
    return math.radians(degrees)

def radians_to_degrees(radians: float) -> float:
    """弧度轉度"""
    return math.degrees(radians)

# 數據驗證工具
def validate_rsrp(rsrp_dbm: float) -> bool:
    """驗證RSRP值合理性"""
    return -150.0 <= rsrp_dbm <= -30.0

def validate_distance(distance_km: float) -> bool:
    """驗證距離合理性"""
    return 0.0 <= distance_km <= 50000.0  # LEO衛星最大距離

def validate_elevation(elevation_deg: float) -> bool:
    """驗證仰角合理性"""
    return -90.0 <= elevation_deg <= 90.0

def parse_satellite_data_format(satellites_data: Dict) -> Tuple[List, List]:
    """
    統一處理新舊格式的衛星數據，避免重複的格式適配邏輯
    
    Args:
        satellites_data: 衛星數據字典，可能是新格式或舊格式
        
    Returns:
        Tuple[List, List]: (starlink_satellites, oneweb_satellites)
    """
    starlink_satellites = []
    oneweb_satellites = []
    
    if 'satellites' in satellites_data:
        # 新格式: 所有衛星在 satellites 字典中，按 norad_id 分組
        all_satellites = satellites_data['satellites']
        
        for sat_id, sat_info in all_satellites.items():
            constellation = sat_info.get('satellite_info', {}).get('constellation', '').lower()
            if constellation == 'starlink':
                starlink_satellites.append(sat_info)
            elif constellation == 'oneweb':
                oneweb_satellites.append(sat_info)
                
    elif 'starlink_satellites' in satellites_data and 'oneweb_satellites' in satellites_data:
        # 舊格式: 分別的 starlink_satellites 和 oneweb_satellites 列表
        starlink_satellites = satellites_data.get('starlink_satellites', [])
        oneweb_satellites = satellites_data.get('oneweb_satellites', [])
    else:
        # 無法識別的格式，返回空列表
        pass
        
    return starlink_satellites, oneweb_satellites
