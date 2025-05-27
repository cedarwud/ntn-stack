"""
UE 管理服務

處理 UE 資訊查詢、統計和狀態管理
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

import structlog

from ..adapters.mongo_adapter import MongoAdapter
from ..adapters.redis_adapter import RedisAdapter

logger = structlog.get_logger(__name__)


class UEService:
    """UE 管理服務"""

    def __init__(self, mongo_adapter: MongoAdapter, redis_adapter: RedisAdapter):
        """
        初始化 UE 服務

        Args:
            mongo_adapter: MongoDB 適配器
            redis_adapter: Redis 適配器
        """
        self.mongo_adapter = mongo_adapter
        self.redis_adapter = redis_adapter

    async def get_ue_info(self, imsi: str) -> Optional[Dict[str, Any]]:
        """
        取得 UE 資訊

        Args:
            imsi: UE IMSI

        Returns:
            UE 資訊，如果不存在則回傳 None
        """
        try:
            # 先檢查快取
            cached_info = await self.redis_adapter.get_cached_ue_info(imsi)
            if cached_info:
                logger.debug("從快取取得 UE 資訊", imsi=imsi)
                return cached_info

            # 從資料庫取得用戶資訊
            subscriber = await self.mongo_adapter.get_subscriber(imsi)
            if not subscriber:
                logger.warning("找不到 UE", imsi=imsi)
                return None

            # 轉換為標準格式
            ue_info = self._convert_subscriber_to_ue_info(subscriber)

            # 檢查線上狀態
            is_online = await self.redis_adapter.is_ue_online(imsi)
            ue_info["status"] = "online" if is_online else "registered"

            # 快取結果
            await self.redis_adapter.cache_ue_info(imsi, ue_info)

            logger.info("取得 UE 資訊成功", imsi=imsi)
            return ue_info

        except Exception as e:
            logger.error("取得 UE 資訊失敗", imsi=imsi, error=str(e))
            raise

    async def get_ue_stats(self, imsi: str) -> Optional[Dict[str, Any]]:
        """
        取得 UE 統計資訊

        Args:
            imsi: UE IMSI

        Returns:
            UE 統計資訊
        """
        try:
            # 從 Redis 取得統計資料
            stats = await self.redis_adapter.get_ue_stats(imsi)

            if not stats:
                # 如果沒有統計資料，建立預設值
                stats = {
                    "imsi": imsi,
                    "connection_time": 0,
                    "bytes_uploaded": 0,
                    "bytes_downloaded": 0,
                    "rtt_ms": None,
                    "slice_switches": 0,
                    "last_rtt_test": None,
                }

                # 初始化統計資料
                await self.redis_adapter.update_ue_stats(imsi, stats)

            logger.debug("取得 UE 統計成功", imsi=imsi)
            return stats

        except Exception as e:
            logger.error("取得 UE 統計失敗", imsi=imsi, error=str(e))
            raise

    async def list_all_ues(self) -> List[Dict[str, Any]]:
        """
        列出所有 UE

        Returns:
            UE 資訊列表
        """
        try:
            # 從資料庫取得所有用戶
            subscribers = await self.mongo_adapter.list_subscribers()

            ue_list = []
            for subscriber in subscribers:
                ue_info = self._convert_subscriber_to_ue_info(subscriber)

                # 檢查線上狀態
                is_online = await self.redis_adapter.is_ue_online(ue_info["imsi"])
                ue_info["status"] = "online" if is_online else "registered"

                ue_list.append(ue_info)

            logger.info("列出所有 UE 成功", count=len(ue_list))
            return ue_list

        except Exception as e:
            logger.error("列出所有 UE 失敗", error=str(e))
            raise

    async def update_ue_online_status(self, imsi: str, online: bool) -> None:
        """
        更新 UE 線上狀態

        Args:
            imsi: UE IMSI
            online: 是否線上
        """
        try:
            await self.redis_adapter.set_ue_online_status(imsi, online)

            # 清除快取，強制下次查詢時重新載入
            await self.redis_adapter.client.delete(f"ue:info:{imsi}")

            logger.info("UE 線上狀態已更新", imsi=imsi, online=online)

        except Exception as e:
            logger.error("更新 UE 線上狀態失敗", imsi=imsi, online=online, error=str(e))
            raise

    async def update_ue_traffic_stats(
        self, imsi: str, bytes_uploaded: int = 0, bytes_downloaded: int = 0
    ) -> None:
        """
        更新 UE 流量統計

        Args:
            imsi: UE IMSI
            bytes_uploaded: 上傳位元組數
            bytes_downloaded: 下載位元組數
        """
        try:
            stats_update = {}

            if bytes_uploaded > 0:
                stats_update["bytes_uploaded"] = bytes_uploaded

            if bytes_downloaded > 0:
                stats_update["bytes_downloaded"] = bytes_downloaded

            if stats_update:
                await self.redis_adapter.update_ue_stats(imsi, stats_update)
                logger.debug("UE 流量統計已更新", imsi=imsi, **stats_update)

        except Exception as e:
            logger.error("更新 UE 流量統計失敗", imsi=imsi, error=str(e))
            raise

    async def record_ue_rtt(self, imsi: str, rtt_ms: float, slice_type: str) -> None:
        """
        記錄 UE RTT 測量結果

        Args:
            imsi: UE IMSI
            rtt_ms: RTT 延遲 (毫秒)
            slice_type: Slice 類型
        """
        try:
            await self.redis_adapter.update_rtt_measurement(imsi, rtt_ms, slice_type)
            logger.info(
                "UE RTT 已記錄", imsi=imsi, rtt_ms=rtt_ms, slice_type=slice_type
            )

        except Exception as e:
            logger.error("記錄 UE RTT 失敗", imsi=imsi, rtt_ms=rtt_ms, error=str(e))
            raise

    async def get_ue_slice_history(self, imsi: str) -> List[Dict[str, Any]]:
        """
        取得 UE Slice 切換歷史

        Args:
            imsi: UE IMSI

        Returns:
            Slice 切換歷史列表
        """
        try:
            history = await self.redis_adapter.get_slice_switch_history(imsi)
            logger.debug("取得 UE Slice 歷史成功", imsi=imsi, count=len(history))
            return history

        except Exception as e:
            logger.error("取得 UE Slice 歷史失敗", imsi=imsi, error=str(e))
            raise

    def _convert_subscriber_to_ue_info(
        self, subscriber: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        將資料庫的 subscriber 資料轉換為 UE 資訊格式

        Args:
            subscriber: 資料庫中的用戶資料

        Returns:
            標準化的 UE 資訊
        """
        try:
            # 取得第一個 slice 資訊
            slice_info = subscriber.get("slice", [{}])[0]
            session_info = slice_info.get("session", [{}])[0]

            # 判斷 Slice 類型
            sst = slice_info.get("sst", 1)
            sd = slice_info.get("sd", "0x111111")

            if sst == 1 and sd == "0x111111":
                slice_type = "eMBB"
            elif sst == 2 and sd == "0x222222":
                slice_type = "uRLLC"
            else:
                slice_type = f"Custom(sst={sst},sd={sd})"

            # 處理 created_at 欄位，確保轉換為 ISO 字符串
            created_at = subscriber.get("created")
            if isinstance(created_at, datetime):
                created_at_str = created_at.isoformat()
            elif isinstance(created_at, str):
                created_at_str = created_at
            else:
                created_at_str = datetime.now().isoformat()

            return {
                "imsi": subscriber["imsi"],
                "apn": session_info.get("name", "internet"),
                "slice": {"sst": sst, "sd": sd, "slice_type": slice_type},
                "status": "registered",  # 預設狀態，會在呼叫端更新
                "ip_address": None,  # 需要從會話資訊取得
                "last_seen": None,
                "created_at": created_at_str,
            }

        except Exception as e:
            logger.error(
                "轉換用戶資料失敗", subscriber_id=subscriber.get("_id"), error=str(e)
            )
            # 回傳最基本的資訊
            return {
                "imsi": subscriber.get("imsi", "unknown"),
                "apn": "internet",
                "slice": {"sst": 1, "sd": "0x111111", "slice_type": "eMBB"},
                "status": "unknown",
                "ip_address": None,
                "last_seen": None,
                "created_at": datetime.now().isoformat(),
            }

    async def validate_ue_exists(self, imsi: str) -> bool:
        """
        驗證 UE 是否存在

        Args:
            imsi: UE IMSI

        Returns:
            UE 是否存在
        """
        try:
            subscriber = await self.mongo_adapter.get_subscriber(imsi)
            return subscriber is not None

        except Exception as e:
            logger.error("驗證 UE 存在失敗", imsi=imsi, error=str(e))
            return False
