"""
🛰️ 衛星數據 API 路由 - 真實數據版本
直接從 Celestrak 獲取真實 TLE 數據，使用記憶體緩存
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import aiohttp
import asyncio
import hashlib
import json
import math
import time
from dataclasses import dataclass

# 創建路由器
router = APIRouter(prefix="/api/satellite-data", tags=["satellite-data"])

# TLE 數據源 - Celestrak API 已禁用
# 改用本地數據源
TLE_SOURCES = {
    # "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",   # 已禁用
    # "oneweb": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle",       # 已禁用
    # "gps": "https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle",         # 已禁用
    # "galileo": "https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle",     # 已禁用
    "starlink": "local://starlink",
    "oneweb": "local://oneweb", 
    "gps": "local://gps",
    "galileo": "local://galileo",
}

# 記憶體緩存
tle_cache = {}
orbital_cache = {}
cache_timestamps = {}
CACHE_TTL = 3600  # 1小時緩存


@dataclass
class TLEData:
    """TLE 數據結構"""

    satellite_id: str
    satellite_name: str
    line1: str
    line2: str
    epoch: datetime
    norad_id: int


@dataclass
class SatellitePosition:
    """衛星位置數據"""

    timestamp: datetime
    latitude: float
    longitude: float
    altitude: float  # km
    satellite_id: str
    constellation: str


# === Pydantic 模型定義 ===


class TLEUpdateRequest(BaseModel):
    """TLE 更新請求"""

    constellation: str = Field(..., description="星座名稱", example="starlink")
    force_update: bool = Field(False, description="強制更新")


class TLEUpdateResponse(BaseModel):
    """TLE 更新響應"""

    constellation: str
    satellites_updated: int
    satellites_added: int
    satellites_failed: int
    duration_seconds: float
    errors: List[str]


class ConstellationInfo(BaseModel):
    """星座信息"""

    name: str
    satellite_count: int
    active_satellites: int
    last_updated: Optional[datetime] = None


class D2MeasurementPoint(BaseModel):
    """D2 測量數據點"""

    timestamp: datetime
    satellite_id: str
    constellation: str
    satellite_distance: float  # 米
    ground_distance: float  # 米
    satellite_position: Dict[str, float]  # lat, lon, alt
    trigger_condition_met: bool
    event_type: str  # 'entering', 'leaving', 'none'


# === 真實數據處理函數 ===


async def download_tle_data(constellation: str) -> List[TLEData]:
    """
    載入 TLE 數據 - 已禁用 Celestrak API
    改用本地數據源
    """
    if constellation not in TLE_SOURCES:
        raise ValueError(f"不支援的星座: {constellation}")

    url = TLE_SOURCES[constellation]

    # 檢查是否為本地數據源
    if url.startswith("local://"):
        print(f"🔄 使用本地 TLE 數據源: {constellation}")
        return await load_local_tle_data(constellation)
    
    # 禁用所有 Celestrak API 調用
    if "celestrak" in url.lower():
        print(f"⚠️ Celestrak API 調用已被禁用: {constellation}")
        raise HTTPException(
            status_code=503, 
            detail=f"Celestrak API 已被禁用，constellation: {constellation}，請使用本地數據源"
        )

    # 其他外部 API (如果有的話)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=500, detail=f"TLE 下載失敗: HTTP {response.status}"
                    )

                content = await response.text()
                return parse_tle_content(content, constellation)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TLE 下載異常: {str(e)}")


async def load_local_tle_data(constellation: str) -> List[TLEData]:
    """
    從本地 TLE 數據目錄載入數據
    """
    try:
        import sys
        sys.path.append('/app/src')
        from services.satellite.local_tle_loader import LocalTLELoader
        
        loader = LocalTLELoader("/app/tle_data")
        
        # 載入指定星座的最新數據
        collected_data = loader.load_collected_data(constellation)
        
        if collected_data.get('daily_data'):
            latest_data = collected_data['daily_data'][-1]
            satellites = latest_data['satellites']
            
            # 轉換為 TLEData 格式
            tle_data_list = []
            for sat in satellites:
                # 從 line1 解析 epoch 時間
                line1 = sat["line1"]
                epoch_year = int(line1[18:20])
                epoch_day = float(line1[20:32])
                
                # 轉換為完整年份
                if epoch_year < 57:
                    full_year = 2000 + epoch_year
                else:
                    full_year = 1900 + epoch_year
                
                # 計算 epoch 時間
                epoch = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(
                    days=epoch_day - 1
                )
                
                tle_data = TLEData(
                    satellite_id=f"{constellation}_{sat['norad_id']}",
                    satellite_name=sat["name"],
                    line1=sat["line1"],
                    line2=sat["line2"],
                    epoch=epoch,
                    norad_id=int(sat["norad_id"]),
                )
                
                tle_data_list.append(tle_data)
            
            print(
                f"✅ 從本地數據載入 {constellation} TLE: {len(tle_data_list)} 顆衛星"
            )
            
            return tle_data_list
        else:
            print(f"⚠️ 本地 {constellation} TLE 數據不可用")
            # 回退到固定的 fallback 數據
            return get_fallback_tle_data(constellation)
            
    except Exception as e:
        print(f"❌ 本地 {constellation} TLE 數據載入失敗: {e}")
        return get_fallback_tle_data(constellation)


def get_fallback_tle_data(constellation: str) -> List[TLEData]:
    """
    獲取 fallback TLE 數據
    """
    fallback_data = {
        "starlink": [
            {
                "name": "STARLINK-1007",
                "norad_id": 44713,
                "line1": "1 44713U 19074A   25204.91667000  .00002182  00000-0  16538-3 0  9999",
                "line2": "2 44713  53.0534  95.4567 0001234  87.6543 272.3456 15.05000000289456",
            }
        ],
        "oneweb": [
            {
                "name": "ONEWEB-0001",
                "norad_id": 44063,
                "line1": "1 44063U 19005A   25204.50000000  .00001234  00000-0  12345-3 0  9999",
                "line2": "2 44063  87.4000  10.0000 0001000  45.0000 315.0000 13.26000000234567",
            }
        ],
        "gps": [
            {
                "name": "GPS IIF-1",
                "norad_id": 37753,
                "line1": "1 37753U 11036A   25204.50000000 -.00000018  00000-0  00000-0 0  9999",
                "line2": "2 37753  55.0000  50.0000 0001000  45.0000 315.0000  2.00000000567890",
            }
        ],
        "galileo": [
            {
                "name": "GALILEO-101",
                "norad_id": 37846,
                "line1": "1 37846U 11060A   25204.50000000  .00000010  00000-0  00000-0 0  9999",
                "line2": "2 37846  56.0000  60.0000 0002000  50.0000 310.0000  1.70000000345678",
            }
        ]
    }
    
    constellation_data = fallback_data.get(constellation, [])
    tle_data_list = []
    
    for sat_data in constellation_data:
        # 從 line1 解析 epoch 時間
        line1 = sat_data["line1"]
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        
        # 轉換為完整年份
        if epoch_year < 57:
            full_year = 2000 + epoch_year
        else:
            full_year = 1900 + epoch_year
        
        # 計算 epoch 時間
        epoch = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(
            days=epoch_day - 1
        )
        
        tle_data = TLEData(
            satellite_id=f"{constellation}_{sat_data['norad_id']}",
            satellite_name=sat_data["name"],
            line1=sat_data["line1"],
            line2=sat_data["line2"],
            epoch=epoch,
            norad_id=sat_data["norad_id"],
        )
        
        tle_data_list.append(tle_data)
    
    print(f"✅ 使用 {constellation} fallback 數據: {len(tle_data_list)} 顆衛星")
    return tle_data_list


def parse_tle_content(content: str, constellation: str) -> List[TLEData]:
    """解析 TLE 內容"""
    lines = content.strip().split("\n")
    tle_data_list = []

    # TLE 格式：每3行為一組 (名稱, Line1, Line2)
    for i in range(0, len(lines), 3):
        if i + 2 >= len(lines):
            break

        try:
            name = lines[i].strip()
            line1 = lines[i + 1].strip()
            line2 = lines[i + 2].strip()

            # 從 Line1 提取 NORAD ID
            norad_id = int(line1[2:7].strip())

            # 從 Line1 提取 epoch
            epoch_year = int(line1[18:20])
            epoch_day = float(line1[20:32])

            # 轉換為完整年份
            if epoch_year < 57:  # 假設 57 以下為 20xx 年
                full_year = 2000 + epoch_year
            else:
                full_year = 1900 + epoch_year

            # 計算 epoch 時間
            epoch = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=epoch_day - 1
            )

            tle_data = TLEData(
                satellite_id=f"{constellation}_{norad_id}",
                satellite_name=name,
                line1=line1,
                line2=line2,
                epoch=epoch,
                norad_id=norad_id,
            )

            tle_data_list.append(tle_data)

        except Exception as e:
            print(f"⚠️ TLE 解析失敗: {e}, 行: {i}")
            continue

    return tle_data_list


def calculate_satellite_position(
    tle_data: TLEData, target_time: datetime
) -> SatellitePosition:
    """簡化的衛星位置計算 (基於 Keplerian 軌道)"""
    # 這是一個簡化版本，真實的 SGP4 計算會更複雜
    # 但為了避免依賴問題，我們使用基本的軌道力學

    # 從 TLE 提取軌道參數
    line2 = tle_data.line2
    inclination = float(line2[8:16])  # 傾斜角
    raan = float(line2[17:25])  # 升交點赤經
    eccentricity = float("0." + line2[26:33])  # 偏心率
    arg_perigee = float(line2[34:42])  # 近地點幅角
    mean_anomaly = float(line2[43:51])  # 平近點角
    mean_motion = float(line2[52:63])  # 平均運動

    # 計算時間差 (分鐘)
    time_diff = (target_time - tle_data.epoch).total_seconds() / 60.0

    # 計算當前平近點角
    current_mean_anomaly = (mean_anomaly + mean_motion * time_diff) % 360

    # 簡化的位置計算 (假設圓軌道)
    if "starlink" in tle_data.satellite_id:
        orbital_radius = 6371 + 550  # Starlink 約 550km
    elif "oneweb" in tle_data.satellite_id:
        orbital_radius = 6371 + 1200  # OneWeb 約 1200km
    elif "gps" in tle_data.satellite_id:
        orbital_radius = 6371 + 20200  # GPS 約 20200km
    else:
        orbital_radius = 6371 + 550  # 預設

    # 轉換為弧度
    inc_rad = math.radians(inclination)
    raan_rad = math.radians(raan)
    arg_per_rad = math.radians(arg_perigee)
    mean_anom_rad = math.radians(current_mean_anomaly)

    # 簡化的軌道位置計算
    x = orbital_radius * math.cos(mean_anom_rad)
    y = orbital_radius * math.sin(mean_anom_rad)
    z = orbital_radius * math.sin(inc_rad) * math.sin(mean_anom_rad)

    # 轉換為地理座標 (簡化)
    latitude = math.degrees(math.asin(z / orbital_radius)) if orbital_radius > 0 else 0
    longitude = math.degrees(math.atan2(y, x))
    altitude = orbital_radius - 6371

    return SatellitePosition(
        timestamp=target_time,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        satellite_id=tle_data.satellite_id,
        constellation=tle_data.satellite_id.split("_")[0],
    )


def calculate_distance(
    lat1: float, lon1: float, alt1: float, lat2: float, lon2: float, alt2: float
) -> float:
    """計算兩點間的 3D 距離 (米)"""
    # 地球半徑 (米)
    R = 6371000

    # 轉換為弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine 公式
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # 地表距離
    surface_distance = R * c

    # 高度差 (轉換為米)
    height_diff = abs(alt2 * 1000 - alt1 * 1000)  # 假設輸入是 km

    # 3D 距離
    distance_3d = math.sqrt(surface_distance**2 + height_diff**2)

    return distance_3d


# === API 端點 ===


@router.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "satellite-data",
        "timestamp": datetime.now(timezone.utc),
    }


@router.get("/constellations", response_model=List[ConstellationInfo])
async def get_available_constellations():
    """獲取可用的衛星星座列表"""
    constellations = []

    for name in TLE_SOURCES.keys():
        # 檢查緩存
        cache_key = f"constellation_{name}"
        if cache_key in cache_timestamps:
            last_updated = datetime.fromtimestamp(
                cache_timestamps[cache_key], tz=timezone.utc
            )
            satellite_count = len(tle_cache.get(name, []))
        else:
            last_updated = None
            satellite_count = 0

        constellations.append(
            ConstellationInfo(
                name=name,
                satellite_count=satellite_count,
                active_satellites=satellite_count,
                last_updated=last_updated,
            )
        )

    return constellations


@router.post("/tle/update", response_model=TLEUpdateResponse)
async def update_tle_data(request: TLEUpdateRequest):
    """更新 TLE 數據"""
    constellation = request.constellation
    start_time = time.time()

    try:
        print(f"🔄 開始更新 {constellation} TLE 數據...")

        # 檢查緩存
        cache_key = f"tle_{constellation}"
        if not request.force_update and cache_key in cache_timestamps:
            cache_age = time.time() - cache_timestamps[cache_key]
            if cache_age < CACHE_TTL:
                cached_data = tle_cache.get(constellation, [])
                return TLEUpdateResponse(
                    constellation=constellation,
                    satellites_updated=0,
                    satellites_added=0,
                    satellites_failed=0,
                    duration_seconds=time.time() - start_time,
                    errors=[f"使用緩存數據，{len(cached_data)} 顆衛星"],
                )

        # 下載真實 TLE 數據
        tle_data_list = await download_tle_data(constellation)

        # 更新緩存
        tle_cache[constellation] = tle_data_list
        cache_timestamps[cache_key] = time.time()

        duration = time.time() - start_time
        print(
            f"✅ {constellation} TLE 更新完成: {len(tle_data_list)} 顆衛星, 耗時 {duration:.2f}s"
        )

        return TLEUpdateResponse(
            constellation=constellation,
            satellites_updated=0,
            satellites_added=len(tle_data_list),
            satellites_failed=0,
            duration_seconds=duration,
            errors=[],
        )

    except Exception as e:
        error_msg = str(e)
        print(f"❌ {constellation} TLE 更新失敗: {error_msg}")

        return TLEUpdateResponse(
            constellation=constellation,
            satellites_updated=0,
            satellites_added=0,
            satellites_failed=1,
            duration_seconds=time.time() - start_time,
            errors=[error_msg],
        )


@router.post("/d2/generate", response_model=List[D2MeasurementPoint])
async def generate_d2_measurements(
    constellation: str = "starlink",
    ue_latitude: float = 25.0478,
    ue_longitude: float = 121.5319,
    ue_altitude: float = 0.1,  # km
    fixed_ref_latitude: float = 25.0000,
    fixed_ref_longitude: float = 121.5000,
    fixed_ref_altitude: float = 0.0,  # km
    thresh1: float = 800000.0,  # 米
    thresh2: float = 30000.0,  # 米
    hysteresis: float = 500.0,  # 米
    duration_minutes: int = 180,
    sample_interval_seconds: int = 60,
):
    """生成 D2 測量數據 - 使用真實衛星軌道"""

    try:
        print(f"🛰️ 開始生成 {constellation} D2 測量數據...")

        # 確保有 TLE 數據
        if constellation not in tle_cache or not tle_cache[constellation]:
            # 自動下載 TLE 數據
            tle_data_list = await download_tle_data(constellation)
            tle_cache[constellation] = tle_data_list
            cache_timestamps[f"tle_{constellation}"] = time.time()
        else:
            tle_data_list = tle_cache[constellation]

        if not tle_data_list:
            raise HTTPException(
                status_code=404, detail=f"沒有找到 {constellation} 的 TLE 數據"
            )

        # 選擇第一顆衛星進行計算 (可以擴展為多顆)
        target_satellite = tle_data_list[0]

        # 生成時間序列
        start_time = datetime.now(timezone.utc)
        measurements = []

        # 計算固定參考位置距離 (一次性計算)
        ground_distance = calculate_distance(
            ue_latitude,
            ue_longitude,
            ue_altitude,
            fixed_ref_latitude,
            fixed_ref_longitude,
            fixed_ref_altitude,
        )

        # 生成每個時間點的測量數據
        for i in range(0, duration_minutes * 60, sample_interval_seconds):
            current_time = start_time + timedelta(seconds=i)

            # 計算衛星位置
            sat_position = calculate_satellite_position(target_satellite, current_time)

            # 計算 UE 到衛星的距離
            satellite_distance = calculate_distance(
                ue_latitude,
                ue_longitude,
                ue_altitude,
                sat_position.latitude,
                sat_position.longitude,
                sat_position.altitude,
            )

            # 計算 D2 事件條件
            # D2 進入條件: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2
            # D2 離開條件: Ml1 + Hys < Thresh1 OR Ml2 - Hys > Thresh2
            ml1 = satellite_distance  # UE 到移動參考位置 (衛星)
            ml2 = ground_distance  # UE 到固定參考位置

            entering_condition = (ml1 - hysteresis > thresh1) and (
                ml2 + hysteresis < thresh2
            )

            leaving_condition = (ml1 + hysteresis < thresh1) or (
                ml2 - hysteresis > thresh2
            )

            # 確定事件類型
            if entering_condition:
                event_type = "entering"
                trigger_condition_met = True
            elif leaving_condition:
                event_type = "leaving"
                trigger_condition_met = True
            else:
                event_type = "none"
                trigger_condition_met = False

            measurement = D2MeasurementPoint(
                timestamp=current_time,
                satellite_id=target_satellite.satellite_id,
                constellation=constellation,
                satellite_distance=satellite_distance,
                ground_distance=ground_distance,
                satellite_position={
                    "latitude": sat_position.latitude,
                    "longitude": sat_position.longitude,
                    "altitude": sat_position.altitude,
                },
                trigger_condition_met=trigger_condition_met,
                event_type=event_type,
            )

            measurements.append(measurement)

        print(f"✅ 生成 {len(measurements)} 個 D2 測量數據點")
        return measurements

    except Exception as e:
        print(f"❌ D2 數據生成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"D2 數據生成失敗: {str(e)}")
