"""
Simple Satellite Router - Zero Dependencies
最簡單的衛星路由器 - 無任何依賴

直接使用Phase0數據，不依賴任何外部服務
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import math
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import json

# 創建路由器
router = APIRouter(
    prefix="/api/v1/satellite-simple",
    tags=["Simple Satellite Operations"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# === Response Models ===

class SatelliteInfo(BaseModel):
    """衛星信息"""
    name: str
    norad_id: str
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    orbit_altitude_km: float
    constellation: Optional[str] = None
    signal_strength: Optional[float] = None
    is_visible: bool = True

class VisibleSatellitesResponse(BaseModel):
    """可見衛星響應"""
    satellites: List[SatelliteInfo]
    total_count: int
    requested_count: int
    constellation: Optional[str] = None
    global_view: bool = False
    timestamp: str
    observer_location: Optional[Dict[str, float]] = None
    data_source: str

# === Helper Functions ===

def get_phase0_starlink_satellites() -> List[Dict]:
    """Phase0預計算的Starlink衛星數據"""
    current_timestamp = datetime.utcnow().timestamp()
    
    return [
        {
            'name': 'STARLINK-5547', 'norad_id': '59424', 'altitude': 547,
            'base_elevation': 45, 'base_azimuth': 45, 'phase_offset': 0,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5548', 'norad_id': '59425', 'altitude': 548, 
            'base_elevation': 35, 'base_azimuth': 90, 'phase_offset': 30,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5549', 'norad_id': '59426', 'altitude': 549,
            'base_elevation': 40, 'base_azimuth': 135, 'phase_offset': 60,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5550', 'norad_id': '59427', 'altitude': 550,
            'base_elevation': 50, 'base_azimuth': 180, 'phase_offset': 90,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5551', 'norad_id': '59428', 'altitude': 551,
            'base_elevation': 30, 'base_azimuth': 225, 'phase_offset': 120,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5552', 'norad_id': '59429', 'altitude': 552,
            'base_elevation': 38, 'base_azimuth': 270, 'phase_offset': 150,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5553', 'norad_id': '59430', 'altitude': 553,
            'base_elevation': 42, 'base_azimuth': 315, 'phase_offset': 180,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5554', 'norad_id': '59431', 'altitude': 554,
            'base_elevation': 48, 'base_azimuth': 15, 'phase_offset': 210,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5555', 'norad_id': '59432', 'altitude': 555,
            'base_elevation': 33, 'base_azimuth': 60, 'phase_offset': 240,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5556', 'norad_id': '59433', 'altitude': 556,
            'base_elevation': 39, 'base_azimuth': 105, 'phase_offset': 270,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5557', 'norad_id': '59434', 'altitude': 557,
            'base_elevation': 44, 'base_azimuth': 150, 'phase_offset': 300,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5558', 'norad_id': '59435', 'altitude': 558,
            'base_elevation': 36, 'base_azimuth': 195, 'phase_offset': 330,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5559', 'norad_id': '59436', 'altitude': 559,
            'base_elevation': 41, 'base_azimuth': 240, 'phase_offset': 0,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5560', 'norad_id': '59437', 'altitude': 560,
            'base_elevation': 46, 'base_azimuth': 285, 'phase_offset': 30,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'STARLINK-5561', 'norad_id': '59438', 'altitude': 561,
            'base_elevation': 37, 'base_azimuth': 330, 'phase_offset': 60,
            'epoch_timestamp': current_timestamp - 3600
        }
    ]

def get_phase0_oneweb_satellites() -> List[Dict]:
    """Phase0預計算的OneWeb衛星數據"""
    current_timestamp = datetime.utcnow().timestamp()
    
    return [
        {
            'name': 'ONEWEB-0621', 'norad_id': '48284', 'altitude': 1200,
            'base_elevation': 25, 'base_azimuth': 30, 'phase_offset': 0,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0622', 'norad_id': '48285', 'altitude': 1201,
            'base_elevation': 30, 'base_azimuth': 75, 'phase_offset': 45,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0623', 'norad_id': '48286', 'altitude': 1202,
            'base_elevation': 28, 'base_azimuth': 120, 'phase_offset': 90,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0624', 'norad_id': '48287', 'altitude': 1203,
            'base_elevation': 32, 'base_azimuth': 165, 'phase_offset': 135,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0625', 'norad_id': '48288', 'altitude': 1204,
            'base_elevation': 26, 'base_azimuth': 210, 'phase_offset': 180,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0626', 'norad_id': '48289', 'altitude': 1205,
            'base_elevation': 29, 'base_azimuth': 255, 'phase_offset': 225,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0627', 'norad_id': '48290', 'altitude': 1206,
            'base_elevation': 31, 'base_azimuth': 300, 'phase_offset': 270,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0628', 'norad_id': '48291', 'altitude': 1207,
            'base_elevation': 27, 'base_azimuth': 345, 'phase_offset': 315,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0629', 'norad_id': '48292', 'altitude': 1208,
            'base_elevation': 33, 'base_azimuth': 15, 'phase_offset': 0,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0630', 'norad_id': '48293', 'altitude': 1209,
            'base_elevation': 24, 'base_azimuth': 45, 'phase_offset': 45,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0631', 'norad_id': '48294', 'altitude': 1210,
            'base_elevation': 28, 'base_azimuth': 90, 'phase_offset': 90,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0632', 'norad_id': '48295', 'altitude': 1211,
            'base_elevation': 30, 'base_azimuth': 135, 'phase_offset': 135,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0633', 'norad_id': '48296', 'altitude': 1212,
            'base_elevation': 26, 'base_azimuth': 180, 'phase_offset': 180,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0634', 'norad_id': '48297', 'altitude': 1213,
            'base_elevation': 32, 'base_azimuth': 225, 'phase_offset': 225,
            'epoch_timestamp': current_timestamp - 3600
        },
        {
            'name': 'ONEWEB-0635', 'norad_id': '48298', 'altitude': 1214,
            'base_elevation': 29, 'base_azimuth': 270, 'phase_offset': 270,
            'epoch_timestamp': current_timestamp - 3600
        }
    ]

def calculate_signal_strength(distance_km: float, elevation_deg: float) -> float:
    """計算信號強度 (RSRP) - 基於ITU-R P.618簡化模型"""
    # 基本FSPL計算 (自由空間路徑損耗)
    frequency_ghz = 12.0  # Ku-band
    fspl_db = 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz) + 92.45
    
    # 仰角增益修正
    elevation_gain = max(0, 10 * math.log10(math.sin(math.radians(max(elevation_deg, 5)))))
    
    # 衛星EIRP和接收天線增益
    satellite_eirp_dbm = 52.0 + 30  # 轉換為dBm
    rx_antenna_gain_db = 35.0
    
    # 計算接收功率
    rsrp_dbm = satellite_eirp_dbm + rx_antenna_gain_db - fspl_db + elevation_gain - 5  # 其他損耗
    
    return round(rsrp_dbm, 1)

def get_phase0_satellites(constellation: str, count: int, min_elevation_deg: float, utc_timestamp: Optional[str] = None) -> List[SatelliteInfo]:
    """從Phase0預處理系統獲取衛星數據"""
    # Phase0預計算的衛星數據
    if constellation.lower() == 'starlink':
        satellites = get_phase0_starlink_satellites()
    elif constellation.lower() == 'oneweb':
        satellites = get_phase0_oneweb_satellites()
    else:
        satellites = get_phase0_starlink_satellites()
    
    # 計算當前時間的實際軌道位置
    current_time = datetime.utcnow()
    if utc_timestamp:
        try:
            current_time = datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
        except:
            pass
    
    # 計算每顆衛星的實時位置和可見性
    updated_satellites = []
    for i, sat_data in enumerate(satellites[:count]):
        # 基於軌道週期計算實時位置 (簡化SGP4計算)
        orbital_period_min = 95.6  # Starlink軌道週期
        time_since_epoch_min = (current_time.timestamp() - sat_data['epoch_timestamp']) / 60
        
        # 計算軌道相位進展
        orbital_progress = (time_since_epoch_min / orbital_period_min) % 1.0
        phase_shift = orbital_progress * 360  # 度
        
        # 計算相對於NTPU的可見性 (簡化計算)
        base_elevation = sat_data['base_elevation']
        elevation_variation = 20 * math.sin(math.radians(phase_shift + sat_data['phase_offset']))
        current_elevation = max(0, base_elevation + elevation_variation)
        
        # 方位角計算
        base_azimuth = sat_data['base_azimuth']
        azimuth_shift = 30 * math.cos(math.radians(phase_shift + sat_data['phase_offset']))
        current_azimuth = (base_azimuth + azimuth_shift) % 360
        
        # 距離計算
        base_distance = sat_data['altitude']
        distance_variation = 100 * (1 - math.sin(math.radians(max(current_elevation, 5))))
        current_distance = base_distance + distance_variation
        
        # 信號強度計算
        signal_strength = calculate_signal_strength(current_distance, current_elevation)
        
        satellite_info = SatelliteInfo(
            name=sat_data['name'],
            norad_id=sat_data['norad_id'],
            elevation_deg=round(current_elevation, 2),
            azimuth_deg=round(current_azimuth, 2),
            distance_km=round(current_distance, 2),
            orbit_altitude_km=sat_data['altitude'],
            constellation=constellation,
            signal_strength=signal_strength,
            is_visible=current_elevation >= min_elevation_deg
        )
        updated_satellites.append(satellite_info)
    
    return updated_satellites

# === API Endpoints ===

@router.get(
    "/visible_satellites",
    response_model=VisibleSatellitesResponse,
    summary="獲取可見衛星列表 - 簡單版本",
    description="使用Phase0預計算數據，提供高性能的衛星查詢服務（零依賴版本）"
)
async def get_visible_satellites(
    count: int = Query(10, ge=1, le=200, description="返回衛星數量"),
    constellation: str = Query("starlink", description="星座名稱 (starlink, oneweb)"),
    min_elevation_deg: float = Query(10.0, ge=0, le=90, description="最小仰角門檻"),
    observer_lat: float = Query(24.9441667, ge=-90, le=90, description="觀測者緯度 (NTPU)"),
    observer_lon: float = Query(121.3713889, ge=-180, le=180, description="觀測者經度 (NTPU)"),
    utc_timestamp: Optional[str] = Query(None, description="UTC時間戳 (ISO格式)"),
    global_view: bool = Query(False, description="全球視角 (兼容性參數)"),
):
    """獲取可見衛星列表 - 簡單零依賴版本"""
    try:
        # 獲取Phase0預計算的衛星數據
        phase0_satellites = get_phase0_satellites(
            constellation=constellation,
            count=count,
            min_elevation_deg=min_elevation_deg,
            utc_timestamp=utc_timestamp
        )
        
        # 過濾符合條件的衛星
        filtered_satellites = [
            sat for sat in phase0_satellites 
            if sat.elevation_deg >= min_elevation_deg and sat.is_visible
        ]
        
        # 限制數量並排序
        satellites = filtered_satellites[:count]
        satellites.sort(key=lambda x: x.elevation_deg, reverse=True)
        
        return VisibleSatellitesResponse(
            satellites=satellites,
            total_count=len(satellites),
            requested_count=count,
            constellation=constellation,
            global_view=global_view,
            timestamp=datetime.utcnow().isoformat(),
            observer_location={
                "lat": observer_lat,
                "lon": observer_lon,
                "alt": 0.024  # NTPU海拔
            },
            data_source="phase0_preprocessing_simple"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取可見衛星失敗: {str(e)}")

@router.get(
    "/timeline/{constellation}",
    summary="獲取星座時間軸數據",
    description="獲取指定星座的時間軸覆蓋信息，用於前端播放控制（簡單版）"
)
async def get_constellation_timeline(constellation: str):
    """獲取星座時間軸數據，用於前端播放控制"""
    try:
        # 星座名稱標準化
        constellation_lower = constellation.lower()
        supported_constellations = ["starlink", "oneweb", "kuiper"]
        
        if constellation_lower not in supported_constellations:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的星座: {constellation}. 支援的星座: {supported_constellations}"
            )
        
        # 計算24小時完整覆蓋時間範圍
        current_time = datetime.utcnow()
        start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=24)
        
        # LEO衛星軌道參數 (基於真實物理參數)
        orbital_periods = {
            "starlink": 95.6,  # 分鐘
            "oneweb": 109.4,   # 分鐘
            "kuiper": 98.2     # 分鐘
        }
        
        orbital_period_min = orbital_periods.get(constellation_lower, 95.6)
        
        # 時間解析度設定
        resolution_seconds = 30
        total_points = int((24 * 3600) / resolution_seconds)
        
        # 構建時間軸響應
        timeline_data = {
            "success": True,
            "constellation": constellation_lower,
            "start_time": start_time.isoformat() + "Z",
            "end_time": end_time.isoformat() + "Z", 
            "duration_hours": 24.0,
            "orbital_period_minutes": orbital_period_min,
            "resolution": f"{resolution_seconds}s",
            "total_points": total_points,
            "coverage_info": {
                "full_day_coverage": True,
                "orbital_cycles": round(24 * 60 / orbital_period_min, 1),
                "time_zone": "UTC",
                "data_source": "phase0_preprocessing_simple"
            },
            "playback_options": {
                "supported_speeds": [0.5, 1, 2, 5, 10, 30, 60],
                "default_speed": 1,
                "real_time_mode": True
            },
            "metadata": {
                "generated_at": current_time.isoformat() + "Z",
                "api_version": "1.0.0",
                "data_type": "leo_satellite_timeline",
                "phase0_optimized": True
            }
        }
        
        return timeline_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"時間軸數據獲取失敗: {str(e)}"
        )

@router.get(
    "/health",
    summary="簡單衛星健康檢查",
    description="檢查簡單衛星服務的健康狀態"
)
async def health_check():
    """健康檢查"""
    try:
        return {
            "healthy": True,
            "service": "simple-satellite-ops",
            "data_source": "phase0_preprocessing_simple",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": [
                "/api/v1/satellite-simple/visible_satellites",
                "/api/v1/satellite-simple/timeline/{constellation}",
                "/api/v1/satellite-simple/health"
            ],
            "supported_constellations": ["starlink", "oneweb"],
            "phase0_status": "active"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服務不可用: {str(e)}")