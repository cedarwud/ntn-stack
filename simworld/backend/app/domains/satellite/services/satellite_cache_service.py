"""
衛星位置數據緩存服務
提供多層次的緩存機制以提升性能
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from redis.asyncio import Redis
from app.core.config import settings
import os

logger = logging.getLogger(__name__)

@dataclass
class CachedSatellitePosition:
    """緩存的衛星位置數據"""
    satellite_id: int
    latitude: float
    longitude: float
    altitude: float
    timestamp: datetime
    ecef_x_km: Optional[float] = None
    ecef_y_km: Optional[float] = None
    ecef_z_km: Optional[float] = None
    elevation_deg: Optional[float] = None
    azimuth_deg: Optional[float] = None
    distance_km: Optional[float] = None

@dataclass
class CachedOrbitData:
    """緩存的軌道數據"""
    satellite_id: int
    start_time: datetime
    end_time: datetime
    positions: List[CachedSatellitePosition]
    calculation_time: datetime

class SatelliteCacheService:
    """衛星數據緩存服務"""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client
        self.local_cache: Dict[str, Tuple[datetime, Any]] = {}
        
        # 緩存配置
        self.position_cache_ttl = int(os.getenv('SATELLITE_CACHE_TTL_SECONDS', '300'))  # 5分鐘
        self.orbit_cache_ttl = int(os.getenv('REDIS_SATELLITE_DATA_TTL', '1800'))      # 30分鐘
        self.local_cache_ttl = int(os.getenv('LOCAL_CACHE_TTL_SECONDS', '60'))         # 1分鐘
        
        # 性能配置
        self.max_local_cache_size = int(os.getenv('MAX_LOCAL_CACHE_SIZE', '1000'))
        self.enable_local_cache = os.getenv('ENABLE_LOCAL_CACHE', 'true').lower() == 'true'
        self.enable_redis_cache = os.getenv('ENABLE_REDIS_CACHE', 'true').lower() == 'true'
        
        logger.info(f"衛星緩存服務初始化完成 - 位置緩存TTL: {self.position_cache_ttl}s, "
                   f"軌道緩存TTL: {self.orbit_cache_ttl}s")

    # ===== 位置緩存 =====
    
    async def get_cached_position(
        self, 
        satellite_id: int, 
        max_age_seconds: int = None
    ) -> Optional[CachedSatellitePosition]:
        """獲取緩存的衛星位置"""
        max_age = max_age_seconds or self.position_cache_ttl
        cache_key = f"satellite_position:{satellite_id}"
        
        try:
            # 1. 檢查本地緩存
            if self.enable_local_cache:
                cached_data = self._get_from_local_cache(cache_key)
                if cached_data:
                    position = CachedSatellitePosition(**cached_data)
                    if self._is_position_fresh(position, max_age):
                        logger.debug(f"本地緩存命中 - 衛星 {satellite_id}")
                        return position
            
            # 2. 檢查Redis緩存
            if self.enable_redis_cache and self.redis:
                cached_json = await self.redis.get(cache_key)
                if cached_json:
                    cached_data = json.loads(cached_json)
                    # 處理datetime反序列化
                    cached_data['timestamp'] = datetime.fromisoformat(cached_data['timestamp'])
                    position = CachedSatellitePosition(**cached_data)
                    
                    if self._is_position_fresh(position, max_age):
                        # 同步到本地緩存
                        if self.enable_local_cache:
                            self._set_to_local_cache(cache_key, asdict(position))
                        logger.debug(f"Redis緩存命中 - 衛星 {satellite_id}")
                        return position
                    else:
                        # 數據過期，清理緩存
                        await self.redis.delete(cache_key)
            
            return None
            
        except Exception as e:
            logger.error(f"獲取緩存位置失敗 - 衛星 {satellite_id}: {e}")
            return None

    async def cache_position(self, position: CachedSatellitePosition) -> bool:
        """緩存衛星位置"""
        cache_key = f"satellite_position:{position.satellite_id}"
        
        try:
            position_data = asdict(position)
            # 處理datetime序列化
            position_data['timestamp'] = position.timestamp.isoformat()
            
            # 1. 緩存到本地
            if self.enable_local_cache:
                self._set_to_local_cache(cache_key, position_data)
            
            # 2. 緩存到Redis
            if self.enable_redis_cache and self.redis:
                await self.redis.setex(
                    cache_key,
                    self.position_cache_ttl,
                    json.dumps(position_data)
                )
            
            logger.debug(f"位置數據已緩存 - 衛星 {position.satellite_id}")
            return True
            
        except Exception as e:
            logger.error(f"緩存位置失敗 - 衛星 {position.satellite_id}: {e}")
            return False

    # ===== 批量位置緩存 =====
    
    async def get_cached_positions_batch(
        self, 
        satellite_ids: List[int],
        max_age_seconds: int = None
    ) -> Dict[int, CachedSatellitePosition]:
        """批量獲取緩存的衛星位置"""
        max_age = max_age_seconds or self.position_cache_ttl
        results = {}
        missing_ids = []
        
        # 1. 檢查本地緩存
        if self.enable_local_cache:
            for sat_id in satellite_ids:
                cache_key = f"satellite_position:{sat_id}"
                cached_data = self._get_from_local_cache(cache_key)
                if cached_data:
                    position = CachedSatellitePosition(**cached_data)
                    if self._is_position_fresh(position, max_age):
                        results[sat_id] = position
                    else:
                        missing_ids.append(sat_id)
                else:
                    missing_ids.append(sat_id)
        else:
            missing_ids = satellite_ids.copy()
        
        # 2. 檢查Redis緩存（批量）
        if missing_ids and self.enable_redis_cache and self.redis:
            cache_keys = [f"satellite_position:{sat_id}" for sat_id in missing_ids]
            try:
                cached_values = await self.redis.mget(cache_keys)
                for i, cached_json in enumerate(cached_values):
                    if cached_json:
                        sat_id = missing_ids[i]
                        cached_data = json.loads(cached_json)
                        cached_data['timestamp'] = datetime.fromisoformat(cached_data['timestamp'])
                        position = CachedSatellitePosition(**cached_data)
                        
                        if self._is_position_fresh(position, max_age):
                            results[sat_id] = position
                            # 同步到本地緩存
                            if self.enable_local_cache:
                                cache_key = f"satellite_position:{sat_id}"
                                self._set_to_local_cache(cache_key, asdict(position))
            except Exception as e:
                logger.error(f"批量Redis緩存查詢失敗: {e}")
        
        logger.debug(f"批量緩存查詢 - 請求: {len(satellite_ids)}, 命中: {len(results)}")
        return results

    async def cache_positions_batch(self, positions: List[CachedSatellitePosition]) -> int:
        """批量緩存衛星位置"""
        success_count = 0
        
        try:
            # 準備數據
            cache_data = {}
            for position in positions:
                cache_key = f"satellite_position:{position.satellite_id}"
                position_data = asdict(position)
                position_data['timestamp'] = position.timestamp.isoformat()
                cache_data[cache_key] = position_data
                
                # 本地緩存
                if self.enable_local_cache:
                    self._set_to_local_cache(cache_key, position_data)
                    success_count += 1
            
            # Redis批量緩存
            if self.enable_redis_cache and self.redis and cache_data:
                pipeline = self.redis.pipeline()
                for cache_key, data in cache_data.items():
                    pipeline.setex(cache_key, self.position_cache_ttl, json.dumps(data))
                await pipeline.execute()
                logger.debug(f"批量位置數據已緩存到Redis - 數量: {len(cache_data)}")
            
        except Exception as e:
            logger.error(f"批量緩存位置失敗: {e}")
        
        return success_count

    # ===== 軌道數據緩存 =====
    
    async def get_cached_orbit(
        self, 
        satellite_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> Optional[CachedOrbitData]:
        """獲取緩存的軌道數據"""
        cache_key = f"satellite_orbit:{satellite_id}:{start_time.isoformat()}:{end_time.isoformat()}"
        
        try:
            if self.enable_redis_cache and self.redis:
                cached_json = await self.redis.get(cache_key)
                if cached_json:
                    cached_data = json.loads(cached_json)
                    
                    # 反序列化時間和位置數據
                    cached_data['start_time'] = datetime.fromisoformat(cached_data['start_time'])
                    cached_data['end_time'] = datetime.fromisoformat(cached_data['end_time'])
                    cached_data['calculation_time'] = datetime.fromisoformat(cached_data['calculation_time'])
                    
                    positions = []
                    for pos_data in cached_data['positions']:
                        pos_data['timestamp'] = datetime.fromisoformat(pos_data['timestamp'])
                        positions.append(CachedSatellitePosition(**pos_data))
                    
                    cached_data['positions'] = positions
                    orbit_data = CachedOrbitData(**cached_data)
                    
                    # 檢查軌道數據是否仍然有效
                    if self._is_orbit_fresh(orbit_data):
                        logger.debug(f"軌道緩存命中 - 衛星 {satellite_id}")
                        return orbit_data
                    else:
                        # 數據過期，清理緩存
                        await self.redis.delete(cache_key)
            
            return None
            
        except Exception as e:
            logger.error(f"獲取緩存軌道失敗 - 衛星 {satellite_id}: {e}")
            return None

    async def cache_orbit(self, orbit_data: CachedOrbitData) -> bool:
        """緩存軌道數據"""
        cache_key = f"satellite_orbit:{orbit_data.satellite_id}:{orbit_data.start_time.isoformat()}:{orbit_data.end_time.isoformat()}"
        
        try:
            if self.enable_redis_cache and self.redis:
                # 序列化數據
                serialized_data = asdict(orbit_data)
                serialized_data['start_time'] = orbit_data.start_time.isoformat()
                serialized_data['end_time'] = orbit_data.end_time.isoformat()
                serialized_data['calculation_time'] = orbit_data.calculation_time.isoformat()
                
                # 序列化位置數據
                positions_data = []
                for position in orbit_data.positions:
                    pos_data = asdict(position)
                    pos_data['timestamp'] = position.timestamp.isoformat()
                    positions_data.append(pos_data)
                serialized_data['positions'] = positions_data
                
                await self.redis.setex(
                    cache_key,
                    self.orbit_cache_ttl,
                    json.dumps(serialized_data)
                )
                
                logger.debug(f"軌道數據已緩存 - 衛星 {orbit_data.satellite_id}, "
                           f"位置點數: {len(orbit_data.positions)}")
                return True
                
        except Exception as e:
            logger.error(f"緩存軌道失敗 - 衛星 {orbit_data.satellite_id}: {e}")
            
        return False

    # ===== TLE數據緩存 =====
    
    async def get_cached_tle(self, satellite_id: int) -> Optional[Dict[str, Any]]:
        """獲取緩存的TLE數據"""
        cache_key = f"satellite_tle:{satellite_id}"
        
        try:
            if self.enable_redis_cache and self.redis:
                cached_json = await self.redis.get(cache_key)
                if cached_json:
                    tle_data = json.loads(cached_json)
                    tle_data['epoch'] = datetime.fromisoformat(tle_data['epoch'])
                    tle_data['last_updated'] = datetime.fromisoformat(tle_data['last_updated'])
                    
                    # 檢查TLE數據是否過期（24小時）
                    if (datetime.utcnow() - tle_data['last_updated']).total_seconds() < 86400:
                        logger.debug(f"TLE緩存命中 - 衛星 {satellite_id}")
                        return tle_data
                    else:
                        await self.redis.delete(cache_key)
            
            return None
            
        except Exception as e:
            logger.error(f"獲取緩存TLE失敗 - 衛星 {satellite_id}: {e}")
            return None

    async def cache_tle(self, satellite_id: int, tle_data: Dict[str, Any]) -> bool:
        """緩存TLE數據"""
        cache_key = f"satellite_tle:{satellite_id}"
        
        try:
            if self.enable_redis_cache and self.redis:
                # 序列化時間數據
                serialized_data = tle_data.copy()
                if 'epoch' in serialized_data and isinstance(serialized_data['epoch'], datetime):
                    serialized_data['epoch'] = serialized_data['epoch'].isoformat()
                if 'last_updated' in serialized_data and isinstance(serialized_data['last_updated'], datetime):
                    serialized_data['last_updated'] = serialized_data['last_updated'].isoformat()
                
                await self.redis.setex(
                    cache_key,
                    86400,  # TLE數據緩存24小時
                    json.dumps(serialized_data)
                )
                
                logger.debug(f"TLE數據已緩存 - 衛星 {satellite_id}")
                return True
                
        except Exception as e:
            logger.error(f"緩存TLE失敗 - 衛星 {satellite_id}: {e}")
            
        return False

    # ===== 緩存管理 =====
    
    async def clear_satellite_cache(self, satellite_id: int) -> bool:
        """清理指定衛星的所有緩存"""
        try:
            if self.enable_redis_cache and self.redis:
                # 查找所有相關的緩存鍵
                pattern = f"satellite_*:{satellite_id}*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
                    logger.info(f"已清理衛星 {satellite_id} 的 {len(keys)} 個緩存項")
            
            # 清理本地緩存
            if self.enable_local_cache:
                keys_to_remove = [key for key in self.local_cache.keys() 
                                if f":{satellite_id}" in key]
                for key in keys_to_remove:
                    del self.local_cache[key]
                    
            return True
            
        except Exception as e:
            logger.error(f"清理衛星緩存失敗 - 衛星 {satellite_id}: {e}")
            return False

    async def clear_expired_cache(self) -> int:
        """清理過期的緩存項"""
        cleared_count = 0
        
        try:
            # 清理本地緩存
            if self.enable_local_cache:
                current_time = datetime.utcnow()
                expired_keys = []
                
                for key, (timestamp, _) in self.local_cache.items():
                    if (current_time - timestamp).total_seconds() > self.local_cache_ttl:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.local_cache[key]
                    cleared_count += 1
                
                logger.debug(f"清理了 {len(expired_keys)} 個過期的本地緩存項")
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"清理過期緩存失敗: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        stats = {
            'local_cache_size': len(self.local_cache) if self.enable_local_cache else 0,
            'local_cache_enabled': self.enable_local_cache,
            'redis_cache_enabled': self.enable_redis_cache,
            'position_cache_ttl': self.position_cache_ttl,
            'orbit_cache_ttl': self.orbit_cache_ttl
        }
        
        if self.enable_redis_cache and self.redis:
            try:
                # 統計Redis中的衛星相關緩存
                position_keys = await self.redis.keys("satellite_position:*")
                orbit_keys = await self.redis.keys("satellite_orbit:*")
                tle_keys = await self.redis.keys("satellite_tle:*")
                
                stats.update({
                    'redis_position_cache_count': len(position_keys),
                    'redis_orbit_cache_count': len(orbit_keys),
                    'redis_tle_cache_count': len(tle_keys)
                })
            except Exception as e:
                logger.error(f"獲取Redis統計失敗: {e}")
        
        return stats

    # ===== 私有方法 =====
    
    def _get_from_local_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """從本地緩存獲取數據"""
        if key in self.local_cache:
            timestamp, data = self.local_cache[key]
            if (datetime.utcnow() - timestamp).total_seconds() <= self.local_cache_ttl:
                return data
            else:
                del self.local_cache[key]
        return None

    def _set_to_local_cache(self, key: str, data: Dict[str, Any]) -> None:
        """設置本地緩存數據"""
        # 控制緩存大小
        if len(self.local_cache) >= self.max_local_cache_size:
            # 移除最舊的項目
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k][0])
            del self.local_cache[oldest_key]
        
        self.local_cache[key] = (datetime.utcnow(), data)

    def _is_position_fresh(self, position: CachedSatellitePosition, max_age_seconds: int) -> bool:
        """檢查位置數據是否新鮮"""
        age = (datetime.utcnow() - position.timestamp).total_seconds()
        return age <= max_age_seconds

    def _is_orbit_fresh(self, orbit_data: CachedOrbitData) -> bool:
        """檢查軌道數據是否新鮮"""
        age = (datetime.utcnow() - orbit_data.calculation_time).total_seconds()
        return age <= self.orbit_cache_ttl

# 全局緩存服務實例
_cache_service: Optional[SatelliteCacheService] = None

def get_cache_service(redis_client: Optional[Redis] = None) -> SatelliteCacheService:
    """獲取緩存服務實例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = SatelliteCacheService(redis_client)
    return _cache_service