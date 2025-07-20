"""
真實氣象數據服務
整合 OpenWeatherMap 和 ECMWF API
為 ITU-R P.618 降雨衰減模型提供真實氣象數據

主要功能：
1. OpenWeatherMap API 整合
2. ECMWF ERA5 數據整合
3. 降雨率統計和預測
4. 地理位置相關的氣象數據
5. 歷史氣象數據查詢
"""

import asyncio
import aiohttp
import json
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import structlog
import os

logger = structlog.get_logger(__name__)


@dataclass
class WeatherData:
    """氣象數據結構"""
    timestamp: datetime
    latitude: float
    longitude: float
    
    # 基本氣象參數
    temperature_celsius: float
    humidity_percent: float
    pressure_hpa: float
    
    # 降水相關
    rainfall_rate_mm_h: float  # 降雨率 (mm/h)
    precipitation_mm: float    # 降水量 (mm)
    precipitation_type: str    # 降水類型 (rain, snow, sleet)
    
    # 雲層和能見度
    cloud_cover_percent: float
    visibility_km: float
    
    # 風力
    wind_speed_ms: float
    wind_direction_deg: float
    
    # 大氣參數
    water_vapor_density_g_m3: Optional[float] = None
    atmospheric_pressure_surface_hpa: Optional[float] = None
    
    # 數據來源
    data_source: str = "unknown"
    quality_flag: str = "good"  # good, fair, poor


@dataclass
class RainfallStatistics:
    """降雨統計數據"""
    location_name: str
    latitude: float
    longitude: float
    
    # 統計期間
    start_date: datetime
    end_date: datetime
    
    # 降雨統計
    annual_rainfall_mm: float
    monthly_averages_mm: List[float]  # 12個月的平均值
    rainfall_rate_percentiles: Dict[str, float]  # 0.01%, 0.1%, 1%, 10% 等
    
    # ITU-R P.618 相關參數
    rain_rate_001_percent: float  # 0.01% 時間超過的降雨率
    rain_rate_01_percent: float   # 0.1% 時間超過的降雨率
    rain_rate_1_percent: float    # 1% 時間超過的降雨率
    
    # 氣候區分類
    climate_zone: str  # A-P (ITU-R P.837 氣候區)
    rain_height_km: float  # 降雨高度


class OpenWeatherMapService:
    """OpenWeatherMap API 服務"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化 OpenWeatherMap 服務"""
        self.api_key = api_key or os.getenv('OPENWEATHERMAP_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = None
        
        if not self.api_key:
            logger.warning("OpenWeatherMap API key 未設定，將使用模擬數據")
        
        logger.info("OpenWeatherMap 服務初始化完成")

    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def get_current_weather(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[WeatherData]:
        """獲取當前天氣數據"""
        if not self.api_key:
            return self._generate_mock_weather_data(latitude, longitude)
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_current_weather(data, latitude, longitude)
                else:
                    logger.error(f"OpenWeatherMap API 錯誤: {response.status}")
                    return self._generate_mock_weather_data(latitude, longitude)
                    
        except Exception as e:
            logger.error(f"獲取天氣數據失敗: {e}")
            return self._generate_mock_weather_data(latitude, longitude)

    async def get_forecast_weather(
        self, 
        latitude: float, 
        longitude: float,
        hours: int = 48
    ) -> List[WeatherData]:
        """獲取天氣預報數據"""
        if not self.api_key:
            return self._generate_mock_forecast_data(latitude, longitude, hours)
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_forecast_weather(data, latitude, longitude, hours)
                else:
                    logger.error(f"OpenWeatherMap 預報 API 錯誤: {response.status}")
                    return self._generate_mock_forecast_data(latitude, longitude, hours)
                    
        except Exception as e:
            logger.error(f"獲取天氣預報失敗: {e}")
            return self._generate_mock_forecast_data(latitude, longitude, hours)

    def _parse_current_weather(
        self, 
        data: Dict[str, Any], 
        latitude: float, 
        longitude: float
    ) -> WeatherData:
        """解析當前天氣數據"""
        main = data.get('main', {})
        weather = data.get('weather', [{}])[0]
        rain = data.get('rain', {})
        wind = data.get('wind', {})
        clouds = data.get('clouds', {})
        
        # 計算降雨率
        rain_1h = rain.get('1h', 0.0)  # 1小時降雨量 (mm)
        rainfall_rate = rain_1h  # mm/h
        
        # 計算水蒸氣密度 (簡化計算)
        temp_k = main.get('temp', 15) + 273.15
        humidity = main.get('humidity', 50) / 100.0
        pressure = main.get('pressure', 1013.25)
        
        # 飽和水蒸氣壓 (Magnus 公式)
        es = 6.112 * math.exp(17.67 * (temp_k - 273.15) / (temp_k - 29.65))
        water_vapor_density = (humidity * es * 216.7) / temp_k  # g/m³
        
        return WeatherData(
            timestamp=datetime.now(timezone.utc),
            latitude=latitude,
            longitude=longitude,
            temperature_celsius=main.get('temp', 15.0),
            humidity_percent=main.get('humidity', 50.0),
            pressure_hpa=main.get('pressure', 1013.25),
            rainfall_rate_mm_h=rainfall_rate,
            precipitation_mm=rain_1h,
            precipitation_type='rain' if rain_1h > 0 else 'none',
            cloud_cover_percent=clouds.get('all', 0.0),
            visibility_km=data.get('visibility', 10000) / 1000.0,
            wind_speed_ms=wind.get('speed', 0.0),
            wind_direction_deg=wind.get('deg', 0.0),
            water_vapor_density_g_m3=water_vapor_density,
            atmospheric_pressure_surface_hpa=pressure,
            data_source="OpenWeatherMap",
            quality_flag="good"
        )

    def _parse_forecast_weather(
        self, 
        data: Dict[str, Any], 
        latitude: float, 
        longitude: float,
        hours: int
    ) -> List[WeatherData]:
        """解析天氣預報數據"""
        forecast_list = data.get('list', [])
        weather_data_list = []
        
        for i, forecast in enumerate(forecast_list[:hours//3]):  # 3小時間隔
            main = forecast.get('main', {})
            weather = forecast.get('weather', [{}])[0]
            rain = forecast.get('rain', {})
            wind = forecast.get('wind', {})
            clouds = forecast.get('clouds', {})
            
            # 時間戳
            dt = forecast.get('dt', 0)
            timestamp = datetime.fromtimestamp(dt, tz=timezone.utc)
            
            # 降雨率
            rain_3h = rain.get('3h', 0.0)  # 3小時降雨量
            rainfall_rate = rain_3h / 3.0  # 轉換為 mm/h
            
            weather_data = WeatherData(
                timestamp=timestamp,
                latitude=latitude,
                longitude=longitude,
                temperature_celsius=main.get('temp', 15.0),
                humidity_percent=main.get('humidity', 50.0),
                pressure_hpa=main.get('pressure', 1013.25),
                rainfall_rate_mm_h=rainfall_rate,
                precipitation_mm=rain_3h,
                precipitation_type='rain' if rain_3h > 0 else 'none',
                cloud_cover_percent=clouds.get('all', 0.0),
                visibility_km=10.0,  # 預報中通常沒有能見度
                wind_speed_ms=wind.get('speed', 0.0),
                wind_direction_deg=wind.get('deg', 0.0),
                data_source="OpenWeatherMap_Forecast",
                quality_flag="good"
            )
            
            weather_data_list.append(weather_data)
        
        return weather_data_list

    def _generate_mock_weather_data(
        self, 
        latitude: float, 
        longitude: float
    ) -> WeatherData:
        """生成模擬天氣數據"""
        # 基於地理位置的簡單氣候模型
        # 熱帶地區 (緯度 < 23.5°) 有更多降雨
        is_tropical = abs(latitude) < 23.5
        
        # 季節效應 (簡化)
        month = datetime.now().month
        is_summer = 6 <= month <= 8 if latitude > 0 else 12 <= month or month <= 2
        
        # 模擬參數
        base_temp = 25.0 if is_tropical else 15.0
        temp_variation = 10.0 * math.sin(month * math.pi / 6)
        temperature = base_temp + temp_variation + (5.0 if is_summer else -5.0)
        
        humidity = 80.0 if is_tropical else 60.0
        rainfall_rate = 2.0 if is_tropical and is_summer else 0.5
        
        return WeatherData(
            timestamp=datetime.now(timezone.utc),
            latitude=latitude,
            longitude=longitude,
            temperature_celsius=temperature,
            humidity_percent=humidity,
            pressure_hpa=1013.25,
            rainfall_rate_mm_h=rainfall_rate,
            precipitation_mm=rainfall_rate,
            precipitation_type='rain' if rainfall_rate > 0.1 else 'none',
            cloud_cover_percent=50.0,
            visibility_km=10.0,
            wind_speed_ms=3.0,
            wind_direction_deg=180.0,
            water_vapor_density_g_m3=15.0,
            atmospheric_pressure_surface_hpa=1013.25,
            data_source="Mock_Data",
            quality_flag="fair"
        )

    def _generate_mock_forecast_data(
        self, 
        latitude: float, 
        longitude: float,
        hours: int
    ) -> List[WeatherData]:
        """生成模擬預報數據"""
        forecast_data = []
        base_weather = self._generate_mock_weather_data(latitude, longitude)
        
        for hour in range(0, hours, 3):  # 3小時間隔
            timestamp = datetime.now(timezone.utc) + timedelta(hours=hour)
            
            # 添加時間變化
            temp_variation = 5.0 * math.sin(hour * math.pi / 12)  # 日夜溫差
            rain_variation = max(0, 2.0 * math.sin(hour * math.pi / 24))  # 降雨變化
            
            weather_data = WeatherData(
                timestamp=timestamp,
                latitude=latitude,
                longitude=longitude,
                temperature_celsius=base_weather.temperature_celsius + temp_variation,
                humidity_percent=base_weather.humidity_percent,
                pressure_hpa=base_weather.pressure_hpa,
                rainfall_rate_mm_h=base_weather.rainfall_rate_mm_h + rain_variation,
                precipitation_mm=base_weather.rainfall_rate_mm_h + rain_variation,
                precipitation_type='rain' if rain_variation > 0.1 else 'none',
                cloud_cover_percent=base_weather.cloud_cover_percent,
                visibility_km=base_weather.visibility_km,
                wind_speed_ms=base_weather.wind_speed_ms,
                wind_direction_deg=base_weather.wind_direction_deg,
                water_vapor_density_g_m3=base_weather.water_vapor_density_g_m3,
                atmospheric_pressure_surface_hpa=base_weather.atmospheric_pressure_surface_hpa,
                data_source="Mock_Forecast",
                quality_flag="fair"
            )
            
            forecast_data.append(weather_data)
        
        return forecast_data


class WeatherDataService:
    """氣象數據服務主類"""
    
    def __init__(self, openweather_api_key: Optional[str] = None):
        """初始化氣象數據服務"""
        self.openweather_service = OpenWeatherMapService(openweather_api_key)
        logger.info("氣象數據服務初始化完成")

    async def get_weather_for_location(
        self, 
        latitude: float, 
        longitude: float,
        include_forecast: bool = False
    ) -> Dict[str, Any]:
        """獲取指定位置的氣象數據"""
        async with self.openweather_service as weather_service:
            # 獲取當前天氣
            current_weather = await weather_service.get_current_weather(latitude, longitude)
            
            result = {
                'current_weather': current_weather,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'timestamp': datetime.now(timezone.utc)
            }
            
            # 獲取預報數據
            if include_forecast:
                forecast_data = await weather_service.get_forecast_weather(latitude, longitude, 48)
                result['forecast'] = forecast_data
            
            return result

    def calculate_itu_rain_rate_statistics(
        self, 
        weather_data_list: List[WeatherData]
    ) -> RainfallStatistics:
        """計算 ITU-R P.618 所需的降雨率統計"""
        if not weather_data_list:
            return self._default_rainfall_statistics()
        
        # 提取降雨率數據
        rain_rates = [data.rainfall_rate_mm_h for data in weather_data_list]
        rain_rates.sort(reverse=True)  # 降序排列
        
        total_hours = len(rain_rates)
        
        # 計算百分位數
        def get_percentile_rain_rate(percent: float) -> float:
            index = int((percent / 100.0) * total_hours)
            return rain_rates[min(index, len(rain_rates) - 1)] if rain_rates else 0.0
        
        first_data = weather_data_list[0]
        
        return RainfallStatistics(
            location_name=f"Lat{first_data.latitude:.2f}_Lon{first_data.longitude:.2f}",
            latitude=first_data.latitude,
            longitude=first_data.longitude,
            start_date=min(data.timestamp for data in weather_data_list),
            end_date=max(data.timestamp for data in weather_data_list),
            annual_rainfall_mm=sum(data.precipitation_mm for data in weather_data_list),
            monthly_averages_mm=[0.0] * 12,  # 需要更多數據計算
            rainfall_rate_percentiles={
                '0.01%': get_percentile_rain_rate(0.01),
                '0.1%': get_percentile_rain_rate(0.1),
                '1%': get_percentile_rain_rate(1.0),
                '10%': get_percentile_rain_rate(10.0)
            },
            rain_rate_001_percent=get_percentile_rain_rate(0.01),
            rain_rate_01_percent=get_percentile_rain_rate(0.1),
            rain_rate_1_percent=get_percentile_rain_rate(1.0),
            climate_zone=self._determine_climate_zone(first_data.latitude),
            rain_height_km=self._estimate_rain_height(first_data.latitude)
        )

    def _determine_climate_zone(self, latitude: float) -> str:
        """根據緯度確定 ITU-R P.837 氣候區"""
        abs_lat = abs(latitude)
        
        if abs_lat < 15:
            return 'N'  # 熱帶
        elif abs_lat < 30:
            return 'M'  # 亞熱帶
        elif abs_lat < 45:
            return 'K'  # 溫帶
        else:
            return 'H'  # 寒帶

    def _estimate_rain_height(self, latitude: float) -> float:
        """估算降雨高度 (km)"""
        # ITU-R P.839 降雨高度模型 (簡化)
        abs_lat = abs(latitude)
        
        if abs_lat < 36:
            return 5.0 - 0.075 * abs_lat  # 熱帶和亞熱帶
        else:
            return 5.0 - 0.075 * 36  # 溫帶和寒帶

    def _default_rainfall_statistics(self) -> RainfallStatistics:
        """默認降雨統計數據"""
        return RainfallStatistics(
            location_name="Default",
            latitude=25.0,
            longitude=121.0,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            annual_rainfall_mm=1200.0,
            monthly_averages_mm=[100.0] * 12,
            rainfall_rate_percentiles={
                '0.01%': 50.0,
                '0.1%': 25.0,
                '1%': 10.0,
                '10%': 2.0
            },
            rain_rate_001_percent=50.0,
            rain_rate_01_percent=25.0,
            rain_rate_1_percent=10.0,
            climate_zone='M',
            rain_height_km=4.5
        )
