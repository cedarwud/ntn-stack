"""
CQRS 衛星位置服務

實現命令查詢責任分離（CQRS）模式，用於衛星位置管理：
- 命令端：處理位置更新、軌道計算等寫操作
- 查詢端：處理位置查詢、範圍搜索等讀操作
- 事件源：記錄所有位置變更事件
- 快取優化：多層次快取策略
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import structlog

from app.domains.satellite.models.satellite_model import Satellite, OrbitPoint
from app.domains.coordinates.models.coordinate_model import GeoCoordinate

logger = structlog.get_logger(__name__)


class SatelliteEventType(Enum):
    """衛星事件類型"""

    POSITION_UPDATED = "satellite.position_updated"
    ORBIT_CALCULATED = "satellite.orbit_calculated"
    VISIBILITY_CHANGED = "satellite.visibility_changed"
    SATELLITE_CREATED = "satellite.created"
    SATELLITE_UPDATED = "satellite.updated"
    TLE_UPDATED = "satellite.tle_updated"
    BATCH_POSITIONS_UPDATED = "satellite.batch_positions_updated"


@dataclass
class SatelliteEvent:
    """衛星事件"""

    id: str
    event_type: SatelliteEventType
    satellite_id: int
    timestamp: datetime
    data: Dict[str, Any]
    version: int = 1
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "satellite_id": self.satellite_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "version": self.version,
            "correlation_id": self.correlation_id,
        }


@dataclass
class SatellitePosition:
    """衛星位置數據"""

    satellite_id: int
    satellite_name: str
    timestamp: datetime
    latitude: float
    longitude: float
    altitude: float  # km
    velocity: Dict[str, float]
    visible: Optional[bool] = None
    elevation: Optional[float] = None
    azimuth: Optional[float] = None
    range_km: Optional[float] = None
    observer_location: Optional[GeoCoordinate] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "satellite_id": self.satellite_id,
            "satellite_name": self.satellite_name,
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "velocity": self.velocity,
            "visible": self.visible,
            "elevation": self.elevation,
            "azimuth": self.azimuth,
            "range_km": self.range_km,
            "observer_location": (
                self.observer_location.dict() if self.observer_location else None
            ),
        }


class SatelliteEventStore:
    """衛星事件存儲"""

    def __init__(self, max_events: int = 100000):
        self.events: Dict[str, SatelliteEvent] = {}
        self.events_by_satellite: Dict[int, List[str]] = {}
        self.max_events = max_events
        self._lock = asyncio.Lock()

    async def append_event(self, event: SatelliteEvent) -> bool:
        """追加事件"""
        async with self._lock:
            # 存儲事件
            self.events[event.id] = event

            # 按衛星索引
            if event.satellite_id not in self.events_by_satellite:
                self.events_by_satellite[event.satellite_id] = []
            self.events_by_satellite[event.satellite_id].append(event.id)

            # 清理舊事件
            if len(self.events) > self.max_events:
                await self._cleanup_old_events()

            return True

    async def get_events_for_satellite(
        self, satellite_id: int, since: Optional[datetime] = None, limit: int = 100
    ) -> List[SatelliteEvent]:
        """獲取衛星的事件"""
        event_ids = self.events_by_satellite.get(satellite_id, [])
        events = []

        for event_id in event_ids[-limit:]:  # 最新的事件
            if event_id in self.events:
                event = self.events[event_id]
                if since is None or event.timestamp >= since:
                    events.append(event)

        return sorted(events, key=lambda e: e.timestamp)

    async def _cleanup_old_events(self):
        """清理舊事件"""
        cleanup_count = int(self.max_events * 0.1)
        sorted_events = sorted(self.events.items(), key=lambda x: x[1].timestamp)

        for event_id, event in sorted_events[:cleanup_count]:
            del self.events[event_id]

            # 從索引刪除
            if event.satellite_id in self.events_by_satellite:
                if event_id in self.events_by_satellite[event.satellite_id]:
                    self.events_by_satellite[event.satellite_id].remove(event_id)


class SatellitePositionCache:
    """衛星位置快取系統"""

    def __init__(self, max_positions: int = 10000, ttl_seconds: int = 60):
        # 當前位置快取
        self.current_positions: Dict[int, SatellitePosition] = {}

        # 觀測者特定位置快取 (satellite_id, observer_hash) -> position
        self.observer_positions: Dict[Tuple[int, str], SatellitePosition] = {}

        # 歷史位置快取 (satellite_id, timestamp_key) -> position
        self.historical_positions: Dict[Tuple[int, str], SatellitePosition] = {}

        # 批量位置快取 (batch_key) -> positions
        self.batch_positions: Dict[str, List[SatellitePosition]] = {}

        self.max_positions = max_positions
        self.ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()

        # 快取統計
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "updates": 0,
        }

    def _observer_hash(self, observer: Optional[GeoCoordinate]) -> str:
        """生成觀測者位置的雜湊"""
        if not observer:
            return "global"
        return f"{observer.latitude:.6f},{observer.longitude:.6f},{observer.altitude or 0:.1f}"

    def _timestamp_key(self, timestamp: datetime) -> str:
        """生成時間戳鍵（分鐘級別）"""
        return timestamp.strftime("%Y%m%d%H%M")

    async def get_current_position(
        self, satellite_id: int, observer: Optional[GeoCoordinate] = None
    ) -> Optional[SatellitePosition]:
        """獲取當前位置"""
        async with self._lock:
            if observer:
                observer_hash = self._observer_hash(observer)
                cache_key = (satellite_id, observer_hash)

                if cache_key in self.observer_positions:
                    position = self.observer_positions[cache_key]
                    # 檢查 TTL
                    if (
                        datetime.utcnow() - position.timestamp
                    ).total_seconds() <= self.ttl_seconds:
                        self.stats["hits"] += 1
                        return position
            else:
                if satellite_id in self.current_positions:
                    position = self.current_positions[satellite_id]
                    # 檢查 TTL
                    if (
                        datetime.utcnow() - position.timestamp
                    ).total_seconds() <= self.ttl_seconds:
                        self.stats["hits"] += 1
                        return position

            self.stats["misses"] += 1
            return None

    async def set_current_position(self, position: SatellitePosition):
        """設置當前位置"""
        async with self._lock:
            # 更新全局位置
            self.current_positions[position.satellite_id] = position

            # 更新觀測者特定位置
            if position.observer_location:
                observer_hash = self._observer_hash(position.observer_location)
                cache_key = (position.satellite_id, observer_hash)
                self.observer_positions[cache_key] = position

            # 更新歷史位置
            timestamp_key = self._timestamp_key(position.timestamp)
            hist_key = (position.satellite_id, timestamp_key)
            self.historical_positions[hist_key] = position

            self.stats["updates"] += 1

            # 檢查快取大小限制
            await self._evict_if_needed()

    async def get_historical_position(
        self, satellite_id: int, timestamp: datetime
    ) -> Optional[SatellitePosition]:
        """獲取歷史位置"""
        async with self._lock:
            timestamp_key = self._timestamp_key(timestamp)
            cache_key = (satellite_id, timestamp_key)

            if cache_key in self.historical_positions:
                self.stats["hits"] += 1
                return self.historical_positions[cache_key]

            self.stats["misses"] += 1
            return None

    async def get_batch_positions(
        self, batch_key: str
    ) -> Optional[List[SatellitePosition]]:
        """獲取批量位置"""
        async with self._lock:
            if batch_key in self.batch_positions:
                self.stats["hits"] += 1
                return self.batch_positions[batch_key]

            self.stats["misses"] += 1
            return None

    async def set_batch_positions(
        self, batch_key: str, positions: List[SatellitePosition]
    ):
        """設置批量位置"""
        async with self._lock:
            self.batch_positions[batch_key] = positions
            self.stats["updates"] += 1
            await self._evict_if_needed()

    async def invalidate_satellite(self, satellite_id: int):
        """使衛星快取失效"""
        async with self._lock:
            # 清除當前位置
            self.current_positions.pop(satellite_id, None)

            # 清除觀測者位置
            keys_to_remove = [
                key for key in self.observer_positions.keys() if key[0] == satellite_id
            ]
            for key in keys_to_remove:
                del self.observer_positions[key]

            # 清除歷史位置
            hist_keys_to_remove = [
                key
                for key in self.historical_positions.keys()
                if key[0] == satellite_id
            ]
            for key in hist_keys_to_remove:
                del self.historical_positions[key]

    async def _evict_if_needed(self):
        """需要時進行快取清理"""
        total_items = (
            len(self.current_positions)
            + len(self.observer_positions)
            + len(self.historical_positions)
            + len(self.batch_positions)
        )

        if total_items > self.max_positions:
            # 簡單 LRU：刪除最舊的歷史位置
            if self.historical_positions:
                oldest_key = min(
                    self.historical_positions.keys(),
                    key=lambda k: self.historical_positions[k].timestamp,
                )
                del self.historical_positions[oldest_key]
                self.stats["evictions"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """獲取快取統計"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_items": (
                len(self.current_positions)
                + len(self.observer_positions)
                + len(self.historical_positions)
                + len(self.batch_positions)
            ),
            "current_positions": len(self.current_positions),
            "observer_positions": len(self.observer_positions),
            "historical_positions": len(self.historical_positions),
            "batch_positions": len(self.batch_positions),
        }


class SatelliteCommandService:
    """衛星命令服務（寫端）"""

    def __init__(
        self,
        orbit_service,
        event_store: SatelliteEventStore,
        position_cache: SatellitePositionCache,
    ):
        self.orbit_service = orbit_service
        self.event_store = event_store
        self.position_cache = position_cache
        self.logger = logger.bind(service="satellite_command")

        # 命令統計
        self.stats = {
            "position_updates": 0,
            "orbit_calculations": 0,
            "batch_updates": 0,
            "tle_updates": 0,
        }

    async def update_satellite_position(
        self,
        satellite_id: int,
        observer: Optional[GeoCoordinate] = None,
        force_calculation: bool = False,
    ) -> SatellitePosition:
        """更新衛星位置（命令）"""
        try:
            start_time = time.time()

            # 檢查快取
            if not force_calculation:
                cached_position = await self.position_cache.get_current_position(
                    satellite_id, observer
                )
                if cached_position:
                    return cached_position

            # 計算新位置
            position_data = await self.orbit_service.get_current_position(
                satellite_id, observer
            )

            # 創建位置對象
            position = SatellitePosition(
                satellite_id=position_data["satellite_id"],
                satellite_name=position_data["satellite_name"],
                timestamp=position_data["timestamp"],
                latitude=position_data["latitude"],
                longitude=position_data["longitude"],
                altitude=position_data["altitude"],
                velocity=position_data["velocity"],
                visible=position_data.get("visible"),
                elevation=position_data.get("elevation"),
                azimuth=position_data.get("azimuth"),
                range_km=position_data.get("range_km"),
                observer_location=observer,
            )

            # 更新快取
            await self.position_cache.set_current_position(position)

            # 發布事件
            await self._publish_position_event(position)

            calculation_time = (time.time() - start_time) * 1000
            self.stats["position_updates"] += 1

            self.logger.debug(
                "衛星位置已更新",
                satellite_id=satellite_id,
                calculation_time_ms=f"{calculation_time:.2f}",
            )

            return position

        except Exception as e:
            self.logger.error(
                "更新衛星位置失敗", satellite_id=satellite_id, error=str(e)
            )
            raise

    async def batch_update_positions(
        self, satellite_ids: List[int], observer: Optional[GeoCoordinate] = None
    ) -> List[SatellitePosition]:
        """批量更新衛星位置"""
        try:
            start_time = time.time()

            # 並行計算所有衛星位置
            tasks = [
                self.update_satellite_position(sat_id, observer, force_calculation=True)
                for sat_id in satellite_ids
            ]

            positions = await asyncio.gather(*tasks, return_exceptions=True)

            # 過濾成功的結果
            valid_positions = [
                pos for pos in positions if isinstance(pos, SatellitePosition)
            ]

            # 快取批量結果
            batch_key = self._generate_batch_key(satellite_ids, observer)
            await self.position_cache.set_batch_positions(batch_key, valid_positions)

            # 發布批量更新事件
            await self._publish_batch_event(satellite_ids, len(valid_positions))

            batch_time = (time.time() - start_time) * 1000
            self.stats["batch_updates"] += 1

            self.logger.info(
                "批量位置更新完成",
                satellite_count=len(satellite_ids),
                successful_count=len(valid_positions),
                batch_time_ms=f"{batch_time:.2f}",
            )

            return valid_positions

        except Exception as e:
            self.logger.error("批量更新位置失敗", error=str(e))
            raise

    async def calculate_orbit_propagation(
        self,
        satellite_id: int,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int = 60,
    ) -> List[SatellitePosition]:
        """計算軌道傳播（命令）"""
        try:
            start_calc = time.time()

            # 調用軌道服務
            orbit_result = await self.orbit_service.propagate_orbit(
                satellite_id, start_time, end_time, step_seconds
            )

            # 轉換為位置對象
            positions = []
            for point in orbit_result.points:
                position = SatellitePosition(
                    satellite_id=satellite_id,
                    satellite_name=orbit_result.satellite_name,
                    timestamp=point.timestamp,
                    latitude=point.latitude,
                    longitude=point.longitude,
                    altitude=point.altitude,
                    velocity={"speed": 7.5},  # 從 orbit service 獲取
                )
                positions.append(position)

            # 快取軌道數據
            orbit_key = (
                f"orbit_{satellite_id}_{start_time.isoformat()}_{end_time.isoformat()}"
            )
            await self.position_cache.set_batch_positions(orbit_key, positions)

            # 發布軌道計算事件
            await self._publish_orbit_event(
                satellite_id, start_time, end_time, len(positions)
            )

            calc_time = (time.time() - start_calc) * 1000
            self.stats["orbit_calculations"] += 1

            self.logger.info(
                "軌道傳播計算完成",
                satellite_id=satellite_id,
                points_count=len(positions),
                calc_time_ms=f"{calc_time:.2f}",
            )

            return positions

        except Exception as e:
            self.logger.error(
                "軌道傳播計算失敗", satellite_id=satellite_id, error=str(e)
            )
            raise

    async def invalidate_satellite_cache(self, satellite_id: int):
        """使衛星快取失效（命令）"""
        await self.position_cache.invalidate_satellite(satellite_id)

        self.logger.info("衛星快取已失效", satellite_id=satellite_id)

    def _generate_batch_key(
        self, satellite_ids: List[int], observer: Optional[GeoCoordinate]
    ) -> str:
        """生成批量操作鍵"""
        ids_str = ",".join(map(str, sorted(satellite_ids)))
        observer_str = self.position_cache._observer_hash(observer)
        timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M")
        return f"batch_{ids_str}_{observer_str}_{timestamp_str}"

    async def _publish_position_event(self, position: SatellitePosition):
        """發布位置更新事件"""
        event = SatelliteEvent(
            id=f"evt_{uuid.uuid4().hex}",
            event_type=SatelliteEventType.POSITION_UPDATED,
            satellite_id=position.satellite_id,
            timestamp=datetime.utcnow(),
            data=position.to_dict(),
        )

        await self.event_store.append_event(event)

    async def _publish_batch_event(self, satellite_ids: List[int], success_count: int):
        """發布批量更新事件"""
        event = SatelliteEvent(
            id=f"evt_{uuid.uuid4().hex}",
            event_type=SatelliteEventType.BATCH_POSITIONS_UPDATED,
            satellite_id=0,  # 批量操作
            timestamp=datetime.utcnow(),
            data={
                "satellite_ids": satellite_ids,
                "success_count": success_count,
                "total_count": len(satellite_ids),
            },
        )

        await self.event_store.append_event(event)

    async def _publish_orbit_event(
        self,
        satellite_id: int,
        start_time: datetime,
        end_time: datetime,
        points_count: int,
    ):
        """發布軌道計算事件"""
        event = SatelliteEvent(
            id=f"evt_{uuid.uuid4().hex}",
            event_type=SatelliteEventType.ORBIT_CALCULATED,
            satellite_id=satellite_id,
            timestamp=datetime.utcnow(),
            data={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "points_count": points_count,
            },
        )

        await self.event_store.append_event(event)


class SatelliteQueryService:
    """衛星查詢服務（讀端）"""

    def __init__(
        self, position_cache: SatellitePositionCache, event_store: SatelliteEventStore
    ):
        self.position_cache = position_cache
        self.event_store = event_store
        self.logger = logger.bind(service="satellite_query")

        # 查詢統計
        self.stats = {
            "position_queries": 0,
            "batch_queries": 0,
            "range_queries": 0,
            "historical_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    async def get_satellite_position(
        self, satellite_id: int, observer: Optional[GeoCoordinate] = None
    ) -> Optional[SatellitePosition]:
        """查詢衛星當前位置"""
        self.stats["position_queries"] += 1

        position = await self.position_cache.get_current_position(
            satellite_id, observer
        )

        if position:
            self.stats["cache_hits"] += 1
        else:
            self.stats["cache_misses"] += 1

        return position

    async def get_multiple_satellite_positions(
        self, satellite_ids: List[int], observer: Optional[GeoCoordinate] = None
    ) -> List[SatellitePosition]:
        """查詢多個衛星位置"""
        self.stats["batch_queries"] += 1

        # 嘗試從快取獲取批量結果
        batch_key = self._generate_batch_key(satellite_ids, observer)
        cached_positions = await self.position_cache.get_batch_positions(batch_key)

        if cached_positions:
            self.stats["cache_hits"] += 1
            return cached_positions

        # 逐個查詢
        positions = []
        for satellite_id in satellite_ids:
            position = await self.get_satellite_position(satellite_id, observer)
            if position:
                positions.append(position)

        if not cached_positions:
            self.stats["cache_misses"] += 1

        return positions

    async def find_satellites_in_range(
        self, center: GeoCoordinate, radius_km: float, max_results: int = 50
    ) -> List[SatellitePosition]:
        """查詢範圍內的衛星"""
        self.stats["range_queries"] += 1

        # 這需要從所有當前位置中篩選
        # 簡化實現：遍歷快取中的所有位置
        all_positions = list(self.position_cache.current_positions.values())

        results = []
        for position in all_positions:
            distance = self._calculate_distance(
                center.latitude, center.longitude, position.latitude, position.longitude
            )

            if distance <= radius_km:
                # 計算相對於觀測者的數據
                relative_position = await self._calculate_relative_position(
                    position, center
                )
                results.append(relative_position)

                if len(results) >= max_results:
                    break

        # 按距離排序
        results.sort(key=lambda p: p.range_km or float("inf"))

        return results

    async def get_satellite_trajectory(
        self, satellite_id: int, start_time: datetime, end_time: datetime
    ) -> List[SatellitePosition]:
        """查詢衛星軌跡"""
        self.stats["historical_queries"] += 1

        # 嘗試從快取獲取軌道數據
        orbit_key = (
            f"orbit_{satellite_id}_{start_time.isoformat()}_{end_time.isoformat()}"
        )
        cached_trajectory = await self.position_cache.get_batch_positions(orbit_key)

        if cached_trajectory:
            self.stats["cache_hits"] += 1
            return cached_trajectory

        self.stats["cache_misses"] += 1

        # 如果快取中沒有，返回空列表（需要通過命令端計算）
        return []

    async def get_satellite_events(
        self, satellite_id: int, since: Optional[datetime] = None, limit: int = 100
    ) -> List[SatelliteEvent]:
        """查詢衛星事件歷史"""
        return await self.event_store.get_events_for_satellite(
            satellite_id, since, limit
        )

    def _generate_batch_key(
        self, satellite_ids: List[int], observer: Optional[GeoCoordinate]
    ) -> str:
        """生成批量查詢鍵"""
        ids_str = ",".join(map(str, sorted(satellite_ids)))
        observer_str = self.position_cache._observer_hash(observer)
        timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M")
        return f"batch_{ids_str}_{observer_str}_{timestamp_str}"

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """計算兩點間距離（簡化版）"""
        # 簡化的距離計算
        import math

        R = 6371  # 地球半徑 km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def _calculate_relative_position(
        self, position: SatellitePosition, observer: GeoCoordinate
    ) -> SatellitePosition:
        """計算相對於觀測者的位置信息"""
        # 簡化實現：計算距離和可見性
        distance = self._calculate_distance(
            observer.latitude, observer.longitude, position.latitude, position.longitude
        )

        # 創建新的位置對象（包含觀測者相關數據）
        return SatellitePosition(
            satellite_id=position.satellite_id,
            satellite_name=position.satellite_name,
            timestamp=position.timestamp,
            latitude=position.latitude,
            longitude=position.longitude,
            altitude=position.altitude,
            velocity=position.velocity,
            visible=position.altitude > 0,  # 簡化可見性判斷
            elevation=45.0,  # 簡化仰角
            azimuth=180.0,  # 簡化方位角
            range_km=distance,
            observer_location=observer,
        )


class CQRSSatelliteService:
    """CQRS 衛星服務門面"""

    def __init__(self, orbit_service):
        # 初始化存儲組件
        self.event_store = SatelliteEventStore()
        self.position_cache = SatellitePositionCache()

        # 初始化命令和查詢服務
        self.command_service = SatelliteCommandService(
            orbit_service, self.event_store, self.position_cache
        )
        self.query_service = SatelliteQueryService(
            self.position_cache, self.event_store
        )

        self.logger = logger.bind(service="cqrs_satellite")

        # 後台任務
        self.background_tasks: List[asyncio.Task] = []
        self.running = False

    async def start(self):
        """啟動 CQRS 服務"""
        self.running = True

        # 啟動後台任務
        cache_maintenance_task = asyncio.create_task(self._cache_maintenance_loop())
        self.background_tasks.append(cache_maintenance_task)

        self.logger.info("CQRS 衛星服務已啟動")

    async def stop(self):
        """停止 CQRS 服務"""
        self.running = False

        # 停止後台任務
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.logger.info("CQRS 衛星服務已停止")

    # ===== 命令操作（寫端）=====

    async def update_satellite_position(
        self, satellite_id: int, observer: Optional[GeoCoordinate] = None
    ) -> SatellitePosition:
        """更新衛星位置"""
        return await self.command_service.update_satellite_position(
            satellite_id, observer
        )

    async def batch_update_positions(
        self, satellite_ids: List[int], observer: Optional[GeoCoordinate] = None
    ) -> List[SatellitePosition]:
        """批量更新位置"""
        return await self.command_service.batch_update_positions(
            satellite_ids, observer
        )

    async def calculate_orbit(
        self,
        satellite_id: int,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int = 60,
    ) -> List[SatellitePosition]:
        """計算軌道"""
        return await self.command_service.calculate_orbit_propagation(
            satellite_id, start_time, end_time, step_seconds
        )

    # ===== 查詢操作（讀端）=====

    async def get_satellite_position(
        self, satellite_id: int, observer: Optional[GeoCoordinate] = None
    ) -> Optional[SatellitePosition]:
        """查詢衛星位置"""
        # 先嘗試查詢
        position = await self.query_service.get_satellite_position(
            satellite_id, observer
        )

        # 如果快取中沒有，觸發更新
        if not position:
            position = await self.command_service.update_satellite_position(
                satellite_id, observer
            )

        return position

    async def get_multiple_positions(
        self, satellite_ids: List[int], observer: Optional[GeoCoordinate] = None
    ) -> List[SatellitePosition]:
        """查詢多個衛星位置"""
        return await self.query_service.get_multiple_satellite_positions(
            satellite_ids, observer
        )

    async def find_visible_satellites(
        self, observer: GeoCoordinate, radius_km: float = 2000, max_results: int = 50
    ) -> List[SatellitePosition]:
        """查詢可見衛星"""
        return await self.query_service.find_satellites_in_range(
            observer, radius_km, max_results
        )

    async def get_satellite_trajectory(
        self,
        satellite_id: int,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int = 60,
    ) -> List[SatellitePosition]:
        """查詢衛星軌跡"""
        # 先查詢快取
        trajectory = await self.query_service.get_satellite_trajectory(
            satellite_id, start_time, end_time
        )

        # 如果快取中沒有，計算新軌跡
        if not trajectory:
            trajectory = await self.command_service.calculate_orbit_propagation(
                satellite_id, start_time, end_time, step_seconds
            )

        return trajectory

    # ===== 管理操作 =====

    async def get_service_stats(self) -> Dict[str, Any]:
        """獲取服務統計"""
        return {
            "command_stats": self.command_service.stats,
            "query_stats": self.query_service.stats,
            "cache_stats": self.position_cache.get_stats(),
            "event_store_stats": {
                "total_events": len(self.event_store.events),
                "satellites_tracked": len(self.event_store.events_by_satellite),
            },
            "background_tasks": len(self.background_tasks),
            "running": self.running,
        }

    async def _cache_maintenance_loop(self):
        """快取維護循環"""
        while self.running:
            try:
                # 執行快取清理和優化
                await self._perform_cache_maintenance()

                # 每5分鐘執行一次
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("快取維護失敗", error=str(e))
                await asyncio.sleep(60)  # 錯誤後等待1分鐘

    async def _perform_cache_maintenance(self):
        """執行快取維護"""
        # 清理過期的快取項目
        current_time = datetime.utcnow()

        # 清理過期的當前位置
        expired_satellites = []
        for satellite_id, position in self.position_cache.current_positions.items():
            if (
                current_time - position.timestamp
            ).total_seconds() > self.position_cache.ttl_seconds:
                expired_satellites.append(satellite_id)

        for satellite_id in expired_satellites:
            del self.position_cache.current_positions[satellite_id]

        if expired_satellites:
            self.logger.debug("清理過期位置快取", count=len(expired_satellites))

        # 清理事件存儲中的舊事件
        await self.event_store._cleanup_old_events()
