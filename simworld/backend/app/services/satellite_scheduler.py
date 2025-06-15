"""
衛星數據定期更新調度器
實現每週自動更新 OneWeb TLE 數據
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.satellite.services.tle_service import (
    TLEService,
    synchronize_constellation_tles,
)
from app.domains.satellite.adapters.sqlmodel_satellite_repository import (
    SQLModelSatelliteRepository,
)
from app.db.base import async_session_maker

logger = logging.getLogger(__name__)


class SatelliteScheduler:
    """衛星數據調度器 - 負責定期更新和同步"""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis_client = redis_client
        self.tle_service = TLEService()
        self.update_interval = timedelta(weeks=1)  # 每週更新
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """啟動調度器"""
        if self.is_running:
            logger.warning("調度器已經在運行")
            return

        if not self.redis_client:
            logger.error("Redis 客戶端未設置，調度器無法啟動")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("衛星數據調度器已啟動，更新間隔: 每週")

    async def stop(self):
        """停止調度器"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("衛星數據調度器已停止")

    async def _scheduler_loop(self):
        """調度器主循環"""
        while self.is_running:
            try:
                await self._check_and_update()
                # 等待下次檢查 (每天檢查一次，但只在需要時更新)
                await asyncio.sleep(24 * 60 * 60)  # 24 小時
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"調度器循環中出錯: {e}", exc_info=True)
                await asyncio.sleep(60 * 60)  # 出錯後等待 1 小時

    async def _check_and_update(self):
        """檢查是否需要更新並執行更新"""
        try:
            # 檢查上次更新時間
            last_update = await self._get_last_update_time()
            if last_update:
                time_since_update = datetime.utcnow() - last_update
                if time_since_update < self.update_interval:
                    logger.debug(f"距離上次更新只有 {time_since_update}，跳過本次更新")
                    return

            logger.info("開始定期 Starlink + Kuiper 衛星數據更新...")

            # 1. 同步最新 TLE 數據到 Redis
            from app.domains.satellite.services.tle_service import (
                synchronize_constellation_tles,
            )

            starlink_success = await synchronize_constellation_tles(
                "starlink", async_session_maker, self.redis_client
            )
            kuiper_success = await synchronize_constellation_tles(
                "kuiper", async_session_maker, self.redis_client
            )

            if not (starlink_success or kuiper_success):
                logger.error("Starlink 和 Kuiper TLE 數據同步都失敗")
                return

            # 2. 自動同步 Redis 數據到資料庫
            await self._sync_redis_to_database()

            # 3. 清理過期的 TLE 數據
            await self._cleanup_expired_tle_data()

            logger.info("定期 Starlink + Kuiper 衛星數據更新完成")

        except Exception as e:
            logger.error(f"定期更新過程中出錯: {e}", exc_info=True)

    async def _get_last_update_time(self) -> Optional[datetime]:
        """獲取上次更新時間（檢查 Starlink 和 Kuiper）"""
        try:
            # 檢查兩個星座的更新時間，取較新的一個
            starlink_update = await self.redis_client.get("starlink_tle_last_update")
            kuiper_update = await self.redis_client.get("kuiper_tle_last_update")

            last_updates = []
            if starlink_update:
                last_updates.append(datetime.fromisoformat(starlink_update.decode()))
            if kuiper_update:
                last_updates.append(datetime.fromisoformat(kuiper_update.decode()))

            if last_updates:
                return max(last_updates)  # 返回最新的更新時間

        except Exception as e:
            logger.warning(f"獲取上次更新時間失敗: {e}")
        return None

    async def _sync_redis_to_database(self):
        """將 Redis 中的 Starlink 和 Kuiper 數據同步到資料庫"""
        try:
            logger.info("開始同步 Redis 數據到資料庫...")

            # 支援的星座列表
            constellations = ["starlink", "kuiper"]
            total_satellites_synced = 0

            async with async_session_maker() as session:
                repo = SQLModelSatelliteRepository()
                repo._session = session

                # 獲取現有衛星的 NORAD ID 映射
                existing_satellites = await repo.get_satellites()
                existing_map = {sat.norad_id: sat for sat in existing_satellites}

                for constellation in constellations:
                    try:
                        # 從 Redis 獲取星座數據
                        tle_data = await self.redis_client.get(
                            f"{constellation}_tle_data"
                        )
                        if not tle_data:
                            logger.warning(f"Redis 中沒有 {constellation.upper()} 數據")
                            continue

                        satellites = json.loads(tle_data.decode())
                        logger.info(
                            f"從 Redis 獲取到 {len(satellites)} 個 {constellation.upper()} 衛星"
                        )

                        updated_count = 0
                        added_count = 0
                        error_count = 0

                        for sat_data in satellites:
                            try:
                                norad_id = sat_data["norad_id"]
                                tle_data_json = json.dumps(
                                    {
                                        "line1": sat_data["line1"],
                                        "line2": sat_data["line2"],
                                    }
                                )

                                if norad_id in existing_map:
                                    # 更新現有衛星
                                    satellite = existing_map[norad_id]
                                    if satellite.tle_data != tle_data_json:
                                        update_data = {
                                            "tle_data": tle_data_json,
                                            "last_updated": datetime.utcnow(),
                                        }
                                        await repo.update_tle_data(
                                            satellite.id, update_data
                                        )
                                        updated_count += 1
                                else:
                                    # 添加新衛星
                                    satellite_data = {
                                        "name": sat_data["name"],
                                        "norad_id": norad_id,
                                        "tle_data": tle_data_json,
                                    }
                                    await repo.create_satellite(satellite_data)
                                    added_count += 1

                            except Exception as e:
                                error_count += 1
                                if error_count <= 5:
                                    logger.warning(
                                        f"處理 {constellation.upper()} 衛星 {sat_data['name']} 時出錯: {e}"
                                    )

                        logger.info(
                            f"{constellation.upper()} 同步完成: 新增 {added_count}, 更新 {updated_count}, 錯誤 {error_count}"
                        )
                        total_satellites_synced += added_count + updated_count

                    except Exception as e:
                        logger.error(
                            f"同步 {constellation.upper()} 時出錯: {e}", exc_info=True
                        )

                logger.info(
                    f"全部星座同步完成，總計處理 {total_satellites_synced} 顆衛星"
                )

        except Exception as e:
            logger.error(f"Redis 到資料庫同步失敗: {e}", exc_info=True)

    async def _cleanup_expired_tle_data(self):
        """清理過期的 TLE 數據"""
        try:
            logger.info("開始清理過期的 TLE 數據...")

            # TLE 數據超過 30 天視為過期
            expiry_threshold = datetime.utcnow() - timedelta(days=30)

            async with async_session_maker() as session:
                repo = SQLModelSatelliteRepository()
                repo._session = session

                satellites = await repo.get_satellites()
                expired_count = 0

                for satellite in satellites:
                    if (
                        satellite.last_updated
                        and satellite.last_updated < expiry_threshold
                    ):
                        logger.warning(
                            f"衛星 {satellite.name} 的 TLE 數據已過期 (上次更新: {satellite.last_updated})"
                        )
                        expired_count += 1

                if expired_count > 0:
                    logger.warning(f"發現 {expired_count} 個衛星的 TLE 數據已過期")
                else:
                    logger.info("所有 TLE 數據都在有效期內")

        except Exception as e:
            logger.error(f"清理過期 TLE 數據時出錯: {e}", exc_info=True)

    async def force_update(self):
        """強制執行一次更新"""
        logger.info("執行強制更新...")
        await self._check_and_update()


# 全局調度器實例
scheduler: Optional[SatelliteScheduler] = None


async def initialize_scheduler(redis_client: aioredis.Redis):
    """初始化調度器"""
    global scheduler
    scheduler = SatelliteScheduler(redis_client)
    await scheduler.start()


async def shutdown_scheduler():
    """關閉調度器"""
    global scheduler
    if scheduler:
        await scheduler.stop()
        scheduler = None
