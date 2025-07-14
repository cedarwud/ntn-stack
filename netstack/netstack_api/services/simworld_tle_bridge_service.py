"""
SimWorld TLE 資料橋接服務

實現 NetStack ↔ SimWorld TLE 資料同步，提供高效的衛星軌道預測快取機制
整合論文需求的二分搜尋時間預測 API，支援換手時機精確預測
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import structlog
import aiohttp
import redis.asyncio as redis
from fastapi import HTTPException

logger = structlog.get_logger(__name__)


class SimWorldTLEBridgeService:
    """SimWorld TLE 資料橋接服務"""

    def __init__(
        self,
        simworld_api_url: str = "http://simworld_backend:8888",
        redis_client: Optional[redis.Redis] = None,
    ):
        self.logger = logger.bind(service="simworld_tle_bridge")
        self.simworld_api_url = simworld_api_url
        self.redis_client = redis_client

        # 快取配置
        self.orbit_cache_ttl = 300  # 軌道預測快取 5 分鐘
        self.position_cache_ttl = 5  # 位置快取 5 秒 (優化：更短的快取)
        self.tle_cache_ttl = 3600  # TLE 資料快取 1 小時
        self.cache_prefix = "simworld_tle_bridge:"

        # 內存快取（用於二分搜尋優化）
        self._memory_cache = {}
        self._memory_cache_ttl = 10  # 10 秒內存快取

        # 預測配置
        self.prediction_precision_seconds = 0.01  # 二分搜尋精度：10ms
        self.max_prediction_horizon_hours = 6  # 最大預測時間範圍

    async def get_satellite_orbit_prediction(
        self,
        satellite_id: str,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int = 60,
        observer_location: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        獲取衛星軌道預測資料

        Args:
            satellite_id: 衛星 ID
            start_time: 開始時間
            end_time: 結束時間
            step_seconds: 時間步長（秒）
            observer_location: 觀測者位置 {lat, lon, alt}

        Returns:
            軌道預測資料，包含位置、速度、可見性等
        """
        self.logger.info(
            "獲取衛星軌道預測",
            satellite_id=satellite_id,
            start_time=start_time,
            end_time=end_time,
            step_seconds=step_seconds,
        )

        # 檢查快取
        cache_key = self._get_orbit_cache_key(
            satellite_id, start_time, end_time, step_seconds, observer_location
        )

        if self.redis_client:
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                self.logger.debug("使用快取的軌道預測資料", satellite_id=satellite_id)
                return json.loads(cached_result)

        try:
            # 首先嘗試將satellite_id映射到資料庫ID
            db_satellite_id = await self._resolve_satellite_id(satellite_id)

            timeout = aiohttp.ClientTimeout(total=5.0)  # 5秒超時
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 構建 SimWorld API 請求
                url = f"{self.simworld_api_url}/api/v1/satellites/{db_satellite_id}/orbit/propagate"

                params = {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "step_seconds": step_seconds,
                }

                if observer_location:
                    params["observer_lat"] = observer_location["lat"]
                    params["observer_lon"] = observer_location["lon"]
                    params["observer_alt"] = observer_location.get("alt", 0)

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        orbit_data = await response.json()

                        # 快取結果
                        if self.redis_client:
                            await self.redis_client.setex(
                                cache_key, self.orbit_cache_ttl, json.dumps(orbit_data)
                            )

                        self.logger.info(
                            "成功獲取軌道預測資料",
                            satellite_id=satellite_id,
                            data_points=len(orbit_data.get("positions", [])),
                        )

                        return orbit_data
                    else:
                        error_msg = f"SimWorld API 返回錯誤: HTTP {response.status}"
                        raise Exception(error_msg)

        except Exception as e:
            self.logger.error(
                "獲取軌道預測失敗", error=str(e), satellite_id=satellite_id
            )
            raise HTTPException(status_code=500, detail=f"軌道預測失敗: {str(e)}")

    async def get_batch_satellite_positions(
        self,
        satellite_ids: List[str],
        timestamp: Optional[datetime] = None,
        observer_location: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量獲取多個衛星的即時位置

        Args:
            satellite_ids: 衛星 ID 列表
            timestamp: 指定時間點（預設為當前時間）
            observer_location: 觀測者位置

        Returns:
            衛星位置字典 {satellite_id: position_data}
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)

        self.logger.info(
            "批量獲取衛星位置",
            satellite_count=len(satellite_ids),
            timestamp=timestamp,
        )

        # 並行獲取所有衛星位置（限制併發數避免過載）
        sem = asyncio.Semaphore(5)  # 限制同時只有 5 個請求

        async def safe_get_position(sat_id):
            async with sem:
                return await self._get_single_satellite_position(
                    sat_id, timestamp, observer_location
                )

        tasks = [safe_get_position(sat_id) for sat_id in satellite_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理結果
        positions = {}
        for i, result in enumerate(results):
            satellite_id = satellite_ids[i]
            if isinstance(result, Exception):
                self.logger.error(
                    f"獲取衛星 {satellite_id} 位置失敗", error=str(result)
                )
                positions[satellite_id] = {
                    "success": False,
                    "error": str(result),
                    "timestamp": (
                        timestamp.isoformat()
                        if isinstance(timestamp, datetime)
                        else datetime.fromtimestamp(timestamp).isoformat()
                    ),
                }
            else:
                positions[satellite_id] = result

        return positions

    async def _get_single_satellite_position(
        self,
        satellite_id: str,
        timestamp: datetime,
        observer_location: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """獲取單個衛星位置"""

        # 檢查內存快取（更快）
        memory_cache_key = f"position:{satellite_id}:{int(timestamp.timestamp())}"
        if memory_cache_key in self._memory_cache:
            cache_time, cached_data = self._memory_cache[memory_cache_key]
            if time.time() - cache_time < self._memory_cache_ttl:
                # self.logger.debug("使用內存快取", satellite_id=satellite_id)
                return cached_data

        # 檢查 Redis 快取
        cache_key = (
            f"{self.cache_prefix}position:{satellite_id}:{timestamp.isoformat()}"
        )

        if self.redis_client:
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                cached_data = json.loads(cached_result)
                # 確保快取的數據也經過標準化
                normalized_data = self._normalize_position_data(cached_data)
                # 同時存入內存快取
                self._memory_cache[memory_cache_key] = (time.time(), normalized_data)
                return normalized_data

        try:
            # 首先嘗試將satellite_id映射到資料庫ID
            db_satellite_id = await self._resolve_satellite_id(satellite_id)

            # 降低日誌級別，避免過多輸出
            # self.logger.debug(
            #     "衛星ID映射",
            #     input_id=satellite_id,
            #     resolved_id=db_satellite_id
            # )

            timeout = aiohttp.ClientTimeout(total=5.0)  # 5秒超時
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.simworld_api_url}/api/v1/satellites/{db_satellite_id}/position"

                params = {"timestamp": timestamp.isoformat()}
                if observer_location:
                    # 檢查 observer_location 是否包含必要字段
                    if "lat" not in observer_location or "lon" not in observer_location:
                        self.logger.warning(
                            "observer_location 缺少必要字段",
                            satellite_id=satellite_id,
                            observer_location=observer_location,
                        )
                        # 不使用 observer_location
                    else:
                        params["observer_lat"] = str(observer_location["lat"])
                        params["observer_lon"] = str(observer_location["lon"])
                        params["observer_alt"] = str(observer_location.get("alt", 0))

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        position_data = await response.json()
                        position_data["success"] = True

                        # 修正數據格式問題：確保必要字段存在
                        position_data = self._normalize_position_data(position_data)

                        # 快取結果到 Redis
                        if self.redis_client:
                            await self.redis_client.setex(
                                cache_key,
                                self.position_cache_ttl,
                                json.dumps(position_data),
                            )

                        # 同時存入內存快取
                        self._memory_cache[memory_cache_key] = (
                            time.time(),
                            position_data,
                        )

                        return position_data
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            "API 錯誤響應",
                            satellite_id=satellite_id,
                            status=response.status,
                            response_text=error_text,
                        )
                        raise Exception(f"HTTP {response.status}: {error_text}")

        except Exception as e:
            self.logger.error(
                "獲取衛星位置失敗詳細錯誤",
                satellite_id=satellite_id,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise Exception(f"獲取衛星 {satellite_id} 位置失敗: {str(e)}")

    async def _resolve_satellite_id(self, satellite_id: str) -> str:
        """
        將衛星識別符映射到資料庫ID

        Args:
            satellite_id: 可能是NORAD ID、衛星名稱或資料庫ID

        Returns:
            資料庫中的衛星ID
        """
        # 如果已經是數字ID，先嘗試直接使用
        if satellite_id.isdigit():
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.simworld_api_url}/api/v1/satellites/{satellite_id}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            return satellite_id  # 直接是資料庫ID
            except:
                pass

        # 獲取所有衛星列表進行匹配
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.simworld_api_url}/api/v1/satellites/"
                async with session.get(url) as response:
                    if response.status == 200:
                        satellites = await response.json()

                        # 按優先級匹配：NORAD ID > 名稱 > 部分匹配
                        for sat in satellites:
                            # 精確匹配NORAD ID
                            if sat.get("norad_id") == satellite_id:
                                return str(sat["id"])
                            # 精確匹配名稱
                            if sat.get("name") == satellite_id:
                                return str(sat["id"])

                        # 部分匹配名稱（用於處理名稱中的空格和大小寫）
                        for sat in satellites:
                            if satellite_id.upper() in sat.get("name", "").upper():
                                return str(sat["id"])

        except Exception as e:
            self.logger.warning(f"無法解析衛星ID {satellite_id}: {e}")

        # 如果所有方法都失敗，拋出明確的錯誤
        raise ValueError(
            f"無法解析衛星ID: {satellite_id}，未在 SimWorld 資料庫中找到匹配項"
        )

    async def sync_tle_updates_from_simworld(self) -> Dict[str, Any]:
        """
        從 SimWorld 同步 TLE 資料更新

        Returns:
            同步結果統計
        """
        self.logger.info("開始同步 TLE 資料更新")

        try:
            timeout = aiohttp.ClientTimeout(total=5.0)  # 5秒超時
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 獲取 TLE 更新狀態
                url = f"{self.simworld_api_url}/api/v1/satellites/tle/status"

                async with session.get(url) as response:
                    if response.status == 200:
                        tle_status = await response.json()

                        # 檢查是否有更新
                        last_update = tle_status.get("last_update")
                        if last_update:
                            # 獲取最新 TLE 資料列表
                            satellites_url = (
                                f"{self.simworld_api_url}/api/v1/satellites/tle/list"
                            )
                            async with session.get(satellites_url) as sat_response:
                                if sat_response.status == 200:
                                    satellites_data = await sat_response.json()

                                    # 快取 TLE 資料
                                    if self.redis_client:
                                        cache_key = f"{self.cache_prefix}tle_data"
                                        await self.redis_client.setex(
                                            cache_key,
                                            self.tle_cache_ttl,
                                            json.dumps(satellites_data),
                                        )

                                    self.logger.info(
                                        "TLE 資料同步完成",
                                        satellite_count=len(
                                            satellites_data.get("satellites", [])
                                        ),
                                        last_update=last_update,
                                    )

                                    return {
                                        "success": True,
                                        "synchronized_count": len(
                                            satellites_data.get("satellites", [])
                                        ),
                                        "last_update": last_update,
                                        "sync_time": datetime.utcnow().isoformat(),
                                    }

            raise Exception("無法獲取 TLE 狀態資料")

        except Exception as e:
            self.logger.error("TLE 資料同步失敗", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "sync_time": datetime.utcnow().isoformat(),
            }

    async def cache_orbit_predictions(
        self,
        satellite_ids: List[str],
        time_range_hours: int = 2,
        step_seconds: int = 60,
    ) -> Dict[str, Any]:
        """
        批量快取軌道預測資料

        Args:
            satellite_ids: 衛星 ID 列表
            time_range_hours: 預測時間範圍（小時）
            step_seconds: 時間步長（秒）

        Returns:
            快取結果統計
        """
        self.logger.info(
            "開始批量快取軌道預測",
            satellite_count=len(satellite_ids),
            time_range_hours=time_range_hours,
        )

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=time_range_hours)

        cached_count = 0
        failed_count = 0

        # 並行快取所有衛星的軌道預測
        tasks = []
        for satellite_id in satellite_ids:
            task = self._cache_single_orbit_prediction(
                satellite_id, start_time, end_time, step_seconds
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            satellite_id = satellite_ids[i]
            if isinstance(result, Exception):
                self.logger.warning(
                    f"快取衛星 {satellite_id} 軌道預測失敗", error=str(result)
                )
                failed_count += 1
            else:
                cached_count += 1

        self.logger.info(
            "軌道預測快取完成",
            cached_count=cached_count,
            failed_count=failed_count,
            total_count=len(satellite_ids),
        )

        return {
            "success": True,
            "cached_count": cached_count,
            "failed_count": failed_count,
            "total_count": len(satellite_ids),
            "time_range_hours": time_range_hours,
            "cache_time": datetime.utcnow().isoformat(),
        }

    async def _cache_single_orbit_prediction(
        self,
        satellite_id: str,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int,
    ):
        """快取單個衛星的軌道預測"""
        try:
            orbit_data = await self.get_satellite_orbit_prediction(
                satellite_id, start_time, end_time, step_seconds
            )
            return orbit_data
        except Exception as e:
            raise Exception(f"快取衛星 {satellite_id} 軌道預測失敗: {str(e)}")

    async def binary_search_handover_time(
        self,
        ue_id: str,
        ue_position: Dict[str, float],
        source_satellite: str,
        target_satellite: str,
        t_start: float,
        t_end: float,
        precision_seconds: float = None,
    ) -> float:
        """
        使用二分搜尋算法計算精確的換手時間點

        實現論文 Algorithm 1 中的二分搜尋換手時間預測

        Args:
            ue_id: UE 識別碼
            ue_position: UE 位置 {lat, lon, alt}
            source_satellite: 當前接入衛星 ID
            target_satellite: 目標換手衛星 ID
            t_start: 搜尋開始時間戳
            t_end: 搜尋結束時間戳
            precision_seconds: 要求精度（秒，預設 0.01 即 10ms）

        Returns:
            精確的換手時間戳
        """
        if precision_seconds is None:
            precision_seconds = self.prediction_precision_seconds

        self.logger.info(
            "開始二分搜尋換手時間",
            ue_id=ue_id,
            source_satellite=source_satellite,
            target_satellite=target_satellite,
            search_range_seconds=t_end - t_start,
            precision_seconds=precision_seconds,
        )

        search_iterations = 0
        max_iterations = 100  # 防止無限迴圈

        while (
            t_end - t_start
        ) > precision_seconds and search_iterations < max_iterations:
            search_iterations += 1
            t_mid = (t_start + t_end) / 2
            mid_time = datetime.fromtimestamp(t_mid)

            # 在中間時間點計算最佳接入衛星
            best_satellite = await self._calculate_best_access_satellite(
                ue_id, ue_position, [source_satellite, target_satellite], mid_time
            )

            if best_satellite == source_satellite:
                # 中間時間點仍使用源衛星，換手時間在後半段
                t_start = t_mid
            else:
                # 中間時間點已換手到目標衛星，換手時間在前半段
                t_end = t_mid

        handover_time = t_end

        self.logger.info(
            "二分搜尋換手時間完成",
            ue_id=ue_id,
            handover_time=datetime.fromtimestamp(handover_time).isoformat(),
            search_iterations=search_iterations,
            final_precision_seconds=t_end - t_start,
        )

        return handover_time

    async def _calculate_best_access_satellite(
        self,
        ue_id: str,
        ue_position: Dict[str, float],
        candidate_satellites: List[str],
        timestamp: datetime,
    ) -> str:
        """
        計算指定時間點的最佳接入衛星

        Args:
            ue_id: UE 識別碼
            ue_position: UE 位置
            candidate_satellites: 候選衛星列表
            timestamp: 計算時間點

        Returns:
            最佳接入衛星 ID
        """
        try:
            # 獲取所有候選衛星在指定時間的位置
            satellite_positions = await self.get_batch_satellite_positions(
                candidate_satellites, timestamp, ue_position
            )

            best_satellite = None
            best_score = -1
            valid_satellites = 0

            for satellite_id, position_data in satellite_positions.items():
                if not position_data.get("success"):
                    # self.logger.debug(
                    #     "衛星位置獲取失敗",
                    #     satellite_id=satellite_id,
                    #     error=position_data.get("error", "未知錯誤")
                    # )
                    continue

                valid_satellites += 1

                # 檢查位置數據必要字段
                if "lat" not in position_data or "lon" not in position_data:
                    self.logger.warning(
                        "衛星位置數據格式錯誤",
                        satellite_id=satellite_id,
                        available_fields=list(position_data.keys()),
                    )
                    continue

                # 計算接入品質評分（基於仰角、距離等因素）
                score = self._calculate_access_score(position_data, ue_position)

                if score > best_score:
                    best_score = score
                    best_satellite = satellite_id

            # 只在有問題時輸出日誌
            if valid_satellites == 0:
                self.logger.warning(
                    "未找到有效衛星",
                    ue_id=ue_id,
                    total_candidates=len(candidate_satellites),
                )

            # 如果沒有找到有效衛星，返回第一個候選衛星作為備用
            if best_satellite is None and candidate_satellites:
                best_satellite = candidate_satellites[0]
                self.logger.warning(
                    "未找到有效衛星，使用第一個候選衛星",
                    ue_id=ue_id,
                    fallback_satellite=best_satellite,
                )

            return best_satellite or "default_satellite"

        except Exception as e:
            self.logger.error("計算最佳接入衛星失敗", ue_id=ue_id, error=str(e))
            # 返回第一個候選衛星作為備用
            return (
                candidate_satellites[0] if candidate_satellites else "default_satellite"
            )

    def _normalize_position_data(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        標準化位置數據格式，修正字段命名不一致問題

        Args:
            position_data: 原始位置數據

        Returns:
            標準化後的位置數據
        """
        try:
            # 創建新的字典避免修改原始數據
            normalized_data = position_data.copy()

            # 處理經緯度字段命名不一致
            if "latitude" in position_data and "lat" not in position_data:
                normalized_data["lat"] = position_data["latitude"]
            if "longitude" in position_data and "lon" not in position_data:
                normalized_data["lon"] = position_data["longitude"]
            if "altitude" in position_data and "alt" not in position_data:
                normalized_data["alt"] = position_data["altitude"]

            # 確保必要字段存在
            if "lat" not in normalized_data:
                if "latitude" in position_data:
                    normalized_data["lat"] = position_data["latitude"]
                else:
                    normalized_data["lat"] = 0.0

            if "lon" not in normalized_data:
                if "longitude" in position_data:
                    normalized_data["lon"] = position_data["longitude"]
                else:
                    normalized_data["lon"] = 0.0

            if "alt" not in normalized_data:
                if "altitude" in position_data:
                    normalized_data["alt"] = position_data["altitude"]
                else:
                    normalized_data["alt"] = 0.0

            # 確保仰角和距離字段存在 (用於接入品質計算)
            if "elevation" not in normalized_data:
                normalized_data["elevation"] = 0.0
            if "range_km" not in normalized_data:
                normalized_data["range_km"] = 1000.0  # 預設距離
            if "visible" not in normalized_data:
                normalized_data["visible"] = True  # 預設可見

            # 確保必要的數值字段是數字類型
            for field in ["lat", "lon", "alt", "elevation", "range_km"]:
                if field in normalized_data:
                    try:
                        normalized_data[field] = float(normalized_data[field])
                    except (ValueError, TypeError):
                        self.logger.warning(
                            f"無法轉換字段 {field} 為浮點數",
                            field=field,
                            value=normalized_data[field],
                        )
                        normalized_data[field] = 0.0

            return normalized_data

        except Exception as e:
            self.logger.error(
                "數據標準化失敗", error=str(e), original_data=position_data
            )
            # 返回最基本的結構
            return {
                "lat": 0.0,
                "lon": 0.0,
                "alt": 0.0,
                "elevation": 0.0,
                "range_km": 1000.0,
                "visible": True,
                "success": False,
                "error": f"數據標準化失敗: {str(e)}",
            }

    def _calculate_access_score(
        self, satellite_position: Dict[str, Any], ue_position: Dict[str, float]
    ) -> float:
        """
        計算衛星接入品質評分

        Args:
            satellite_position: 衛星位置資料
            ue_position: UE 位置

        Returns:
            接入品質評分（0-100）
        """
        try:
            # 檢查必要字段是否存在
            if "lat" not in satellite_position or "lon" not in satellite_position:
                self.logger.warning(
                    "衛星位置數據缺少必要字段",
                    available_fields=list(satellite_position.keys()),
                )
                return 0

            if not satellite_position.get("visible", True):  # 預設為可見
                return 0

            elevation = satellite_position.get("elevation", 0)
            range_km = satellite_position.get("range_km", 1000.0)  # 預設距離

            # 如果沒有 elevation 或 range_km，使用簡化的距離計算
            if elevation == 0 and range_km == 1000.0:
                # 簡化評分：基於緯度差距（越小越好）
                sat_lat = satellite_position.get("lat", 0)

                # 檢查 ue_position 格式
                if isinstance(ue_position, dict):
                    ue_lat = ue_position.get("lat", ue_position.get("latitude", 0))
                else:
                    self.logger.warning(
                        "ue_position 不是字典格式",
                        ue_position=ue_position,
                        type=type(ue_position),
                    )
                    ue_lat = 0

                lat_diff = abs(sat_lat - ue_lat)

                # 緯度差越小，評分越高（最大差90度）
                simple_score = max(0, (90 - lat_diff) / 90 * 100)

                # self.logger.debug(
                #     "使用簡化評分",
                #     sat_lat=sat_lat,
                #     ue_lat=ue_lat,
                #     lat_diff=lat_diff,
                #     score=simple_score
                # )

                return simple_score

            # 仰角權重（仰角越高越好）
            elevation_score = max(0, min(40, elevation)) / 40 * 60

            # 距離權重（距離越近越好，但有衰減）
            distance_score = max(0, (2000 - range_km) / 2000) * 40

            total_score = elevation_score + distance_score

            # self.logger.debug(
            #     "詳細評分計算",
            #     elevation=elevation,
            #     range_km=range_km,
            #     elevation_score=elevation_score,
            #     distance_score=distance_score,
            #     total_score=total_score
            # )

            return total_score

        except Exception as e:
            self.logger.error(
                "計算接入評分失敗", error=str(e), satellite_position=satellite_position
            )
            return 0

    def _get_orbit_cache_key(
        self,
        satellite_id: str,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int,
        observer_location: Optional[Dict[str, float]],
    ) -> str:
        """生成軌道預測快取鍵"""
        observer_key = ""
        if observer_location:
            observer_key = (
                f":{observer_location['lat']:.2f}:{observer_location['lon']:.2f}"
            )

        return (
            f"{self.cache_prefix}orbit:{satellite_id}:"
            f"{start_time.isoformat()}:{end_time.isoformat()}:"
            f"{step_seconds}{observer_key}"
        )

    async def get_tle_health_check(self) -> Dict[str, Any]:
        """
        檢查 TLE 資料健康狀態

        Returns:
            健康檢查結果
        """
        try:
            timeout = aiohttp.ClientTimeout(total=5.0)  # 5秒超時
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.simworld_api_url}/api/v1/satellites/tle/health"

                async with session.get(url) as response:
                    if response.status == 200:
                        health_data = await response.json()

                        return {
                            "success": True,
                            "simworld_status": "online",
                            "tle_health": health_data,
                            "check_time": datetime.utcnow().isoformat(),
                        }
                    else:
                        return {
                            "success": False,
                            "simworld_status": f"http_error_{response.status}",
                            "check_time": datetime.utcnow().isoformat(),
                        }

        except Exception as e:
            return {
                "success": False,
                "simworld_status": "offline",
                "error": str(e),
                "check_time": datetime.utcnow().isoformat(),
            }

    async def preload_critical_satellites(
        self, critical_satellite_ids: List[str]
    ) -> Dict[str, Any]:
        """
        預載關鍵衛星資料以確保低延遲存取

        Args:
            critical_satellite_ids: 關鍵衛星 ID 列表

        Returns:
            預載結果
        """
        self.logger.info(
            "開始預載關鍵衛星資料", critical_count=len(critical_satellite_ids)
        )

        # 預載未來 2 小時的軌道預測
        cache_result = await self.cache_orbit_predictions(
            critical_satellite_ids, time_range_hours=2, step_seconds=30
        )

        # 預載當前位置
        current_positions = await self.get_batch_satellite_positions(
            critical_satellite_ids
        )

        success_count = sum(
            1 for pos in current_positions.values() if pos.get("success")
        )

        return {
            "success": True,
            "preloaded_satellites": len(critical_satellite_ids),
            "position_success_count": success_count,
            "orbit_cache_result": cache_result,
            "preload_time": datetime.utcnow().isoformat(),
        }

    async def get_satellite_position(
        self,
        satellite_id: str,
        timestamp: Optional[float] = None,
        observer_location: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        獲取單個衛星位置 (測試用方法)

        Args:
            satellite_id: 衛星 ID
            timestamp: 時間戳 (可選)
            observer_location: 觀測者位置 (可選)

        Returns:
            衛星位置資料
        """
        if timestamp is None:
            timestamp = time.time()

        # 轉換為 datetime
        dt_timestamp = (
            datetime.fromtimestamp(timestamp)
            if isinstance(timestamp, (int, float))
            else timestamp
        )

        return await self._get_single_satellite_position(
            satellite_id, dt_timestamp, observer_location
        )

    async def get_service_status(self) -> Dict[str, Any]:
        """
        獲取服務狀態

        Returns:
            服務狀態資訊
        """
        try:
            # 測試 SimWorld 連接
            health_check = await self.get_tle_health_check()

            return {
                "service_name": "SimWorldTLEBridgeService",
                "status": "active",
                "simworld_connection": health_check.get("success", False),
                "cache_prefix": self.cache_prefix,
                "orbit_cache_ttl": self.orbit_cache_ttl,
                "position_cache_ttl": self.position_cache_ttl,
                "prediction_precision_seconds": self.prediction_precision_seconds,
                "max_prediction_horizon_hours": self.max_prediction_horizon_hours,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "service_name": "SimWorldTLEBridgeService",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # 🚀 新增：真實的軌道事件觸發機制
    async def detect_orbit_events(
        self,
        satellite_ids: List[str],
        ue_location: Dict[str, float],
        time_horizon_minutes: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        檢測未來的軌道事件

        Args:
            satellite_ids: 衛星 ID 列表
            ue_location: UE 位置
            time_horizon_minutes: 檢測時間範圍（分鐘）

        Returns:
            軌道事件列表
        """
        events = []
        current_time = datetime.now()
        end_time = current_time + timedelta(minutes=time_horizon_minutes)

        for satellite_id in satellite_ids:
            try:
                # 獲取軌道預測資料
                orbit_data = await self.get_satellite_orbit_prediction(
                    satellite_id,
                    current_time,
                    end_time,
                    step_seconds=60,
                    observer_location=ue_location,
                )

                # 分析軌道事件
                satellite_events = self._analyze_orbit_events(
                    satellite_id, orbit_data, ue_location
                )
                events.extend(satellite_events)

            except Exception as e:
                self.logger.error(f"檢測衛星 {satellite_id} 軌道事件失敗: {e}")

        # 按時間排序
        events.sort(key=lambda x: x.get("timestamp", ""))

        return events

    def _analyze_orbit_events(
        self,
        satellite_id: str,
        orbit_data: Dict[str, Any],
        ue_location: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """
        分析軌道數據以識別事件

        Args:
            satellite_id: 衛星 ID
            orbit_data: 軌道數據
            ue_location: UE 位置

        Returns:
            事件列表
        """
        events = []
        positions = orbit_data.get("positions", [])

        if len(positions) < 2:
            return events

        # 檢測仰角變化事件
        for i in range(1, len(positions)):
            prev_pos = positions[i - 1]
            curr_pos = positions[i]

            prev_elevation = prev_pos.get("elevation", 0)
            curr_elevation = curr_pos.get("elevation", 0)

            elevation_change = curr_elevation - prev_elevation

            # 顯著的仰角變化
            if abs(elevation_change) > 5.0:
                events.append(
                    {
                        "event_type": "elevation_change",
                        "satellite_id": satellite_id,
                        "timestamp": curr_pos.get("timestamp"),
                        "elevation_change": elevation_change,
                        "current_elevation": curr_elevation,
                        "confidence": 0.9,
                    }
                )

            # 檢測可見性變化
            if prev_elevation <= 10 and curr_elevation > 10:
                events.append(
                    {
                        "event_type": "satellite_rise",
                        "satellite_id": satellite_id,
                        "timestamp": curr_pos.get("timestamp"),
                        "elevation": curr_elevation,
                        "confidence": 0.95,
                    }
                )

            if prev_elevation > 10 and curr_elevation <= 10:
                events.append(
                    {
                        "event_type": "satellite_set",
                        "satellite_id": satellite_id,
                        "timestamp": curr_pos.get("timestamp"),
                        "elevation": curr_elevation,
                        "confidence": 0.95,
                    }
                )

        return events

    # 🚀 新增：批量軌道預測
    async def batch_orbit_prediction(
        self,
        satellite_ids: List[str],
        start_time: datetime,
        end_time: datetime,
        step_seconds: int = 60,
        observer_location: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        批量獲取多個衛星的軌道預測

        Args:
            satellite_ids: 衛星 ID 列表
            start_time: 開始時間
            end_time: 結束時間
            step_seconds: 時間步長
            observer_location: 觀測者位置

        Returns:
            批量預測結果
        """
        results = {}
        tasks = []

        # 並行請求所有衛星的軌道預測
        for satellite_id in satellite_ids:
            task = asyncio.create_task(
                self.get_satellite_orbit_prediction(
                    satellite_id,
                    start_time,
                    end_time,
                    step_seconds,
                    observer_location,
                )
            )
            tasks.append((satellite_id, task))

        # 等待所有任務完成
        for satellite_id, task in tasks:
            try:
                result = await task
                results[satellite_id] = result
            except Exception as e:
                self.logger.error(f"批量預測失敗 - 衛星 {satellite_id}: {e}")
                results[satellite_id] = {
                    "error": str(e),
                    "success": False,
                }

        return {
            "batch_results": results,
            "total_satellites": len(satellite_ids),
            "successful_predictions": sum(
                1 for r in results.values() if r.get("success", True)
            ),
            "prediction_time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "step_seconds": step_seconds,
            },
        }
