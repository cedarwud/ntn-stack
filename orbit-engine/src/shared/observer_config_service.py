"""
統一觀測配置服務 - 消除硬編碼座標重複
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ObserverConfiguration:
    """觀測點配置數據結構"""
    latitude: float
    longitude: float
    altitude_m: float
    location_name: str
    country: str = "Taiwan"
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_m": self.altitude_m,
            "location_name": self.location_name,
            "country": self.country
        }

class ObserverConfigService:
    """統一觀測配置服務 - 消除系統中的硬編碼座標重複"""
    
    _instance: Optional['ObserverConfigService'] = None
    
    def __new__(cls) -> 'ObserverConfigService':
        """單例模式確保配置一致性"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config: Optional[ObserverConfiguration] = None
        logger.info("🎯 統一觀測配置服務初始化")
        
    def get_observer_config(self) -> ObserverConfiguration:
        """獲取觀測點配置 - 統一接口"""
        if self._config is None:
            self._config = self._load_observer_config()
            logger.info(f"✅ 觀測配置載入: {self._config.location_name} ({self._config.latitude}°, {self._config.longitude}°)")
        
        return self._config
    
    def _load_observer_config(self) -> ObserverConfiguration:
        """載入觀測配置 - 優先使用配置文件，降級到標準NTPU位置"""
        # 嘗試從統一配置系統載入
        try:
            from config.unified_satellite_config import get_unified_config
            config = get_unified_config()
            
            return ObserverConfiguration(
                latitude=config.observer.latitude,
                longitude=config.observer.longitude,
                altitude_m=config.observer.altitude_m,
                location_name="NTPU",
                country="Taiwan"
            )
        except Exception as e:
            logger.warning(f"統一配置載入失敗，使用標準NTPU配置: {e}")
            
        # 標準NTPU觀測點配置 (消除硬編碼重複的唯一來源)
        return ObserverConfiguration(
            latitude=24.9441667,    # NTPU標準緯度
            longitude=121.3713889,  # NTPU標準經度  
            altitude_m=50.0,        # 標準海拔高度
            location_name="NTPU",
            country="Taiwan"
        )
    
    def get_coordinates_dict(self) -> Dict[str, float]:
        """返回座標字典格式 - 兼容現有代碼"""
        config = self.get_observer_config()
        return {
            "latitude": config.latitude,
            "longitude": config.longitude,
            "altitude_m": config.altitude_m
        }
    
    def get_lat_lon_tuple(self) -> tuple[float, float]:
        """返回 (緯度, 經度) 元組 - 兼容現有代碼"""
        config = self.get_observer_config()
        return (config.latitude, config.longitude)
    
    def get_lat_lon_alt_tuple(self) -> tuple[float, float, float]:
        """返回 (緯度, 經度, 高度) 元組 - 兼容現有代碼"""
        config = self.get_observer_config()
        return (config.latitude, config.longitude, config.altitude_m)

# 全局訪問函數
_observer_service: Optional[ObserverConfigService] = None

def get_observer_config_service() -> ObserverConfigService:
    """獲取統一觀測配置服務實例 - 全局統一接口"""
    global _observer_service
    if _observer_service is None:
        _observer_service = ObserverConfigService()
    return _observer_service

def get_ntpu_coordinates() -> tuple[float, float, float]:
    """快速獲取NTPU座標 - 消除硬編碼的統一接口"""
    service = get_observer_config_service()
    return service.get_lat_lon_alt_tuple()

def get_observer_config() -> ObserverConfiguration:
    """快速獲取觀測配置 - 統一接口"""
    service = get_observer_config_service()
    return service.get_observer_config()