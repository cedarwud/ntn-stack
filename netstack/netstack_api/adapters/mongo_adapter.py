"""
MongoDB 適配器

處理與 Open5GS MongoDB 資料庫的連接和操作
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import motor.motor_asyncio
from pymongo.errors import ConnectionFailure, OperationFailure
import structlog

logger = structlog.get_logger(__name__)


class MongoAdapter:
    """MongoDB 資料庫適配器"""

    def __init__(self, connection_string: str):
        """
        初始化 MongoDB 適配器

        Args:
            connection_string: MongoDB 連接字串
        """
        self.connection_string = connection_string
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """建立資料庫連接"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.connection_string, serverSelectionTimeoutMS=5000
            )

            # 測試連接
            await self.client.admin.command("ping")

            # 取得 open5gs 資料庫
            self.db = self.client.open5gs

            logger.info("MongoDB 連接成功", connection_string=self.connection_string)

        except ConnectionFailure as e:
            logger.error("MongoDB 連接失敗", error=str(e))
            raise

    async def disconnect(self) -> None:
        """關閉資料庫連接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 連接已關閉")

    async def health_check(self) -> Dict[str, Any]:
        """檢查資料庫健康狀態"""
        try:
            start_time = datetime.now()
            await self.client.admin.command("ping")
            response_time = (datetime.now() - start_time).total_seconds()

            return {
                "status": "healthy",
                "response_time": response_time,
                "database": "open5gs",
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def get_subscriber(self, imsi: str) -> Optional[Dict[str, Any]]:
        """
        取得用戶資訊

        Args:
            imsi: 用戶 IMSI

        Returns:
            用戶資訊字典，如果不存在則回傳 None
        """
        try:
            subscriber = await self.db.subscribers.find_one({"imsi": imsi})
            return subscriber
        except Exception as e:
            logger.error("取得用戶資訊失敗", imsi=imsi, error=str(e))
            raise

    async def list_subscribers(self) -> List[Dict[str, Any]]:
        """
        列出所有用戶

        Returns:
            用戶資訊列表
        """
        try:
            cursor = self.db.subscribers.find({})
            subscribers = await cursor.to_list(length=None)
            return subscribers
        except Exception as e:
            logger.error("列出用戶失敗", error=str(e))
            raise

    async def update_subscriber_slice(self, imsi: str, sst: int, sd: str) -> bool:
        """
        更新用戶的 Slice 配置

        Args:
            imsi: 用戶 IMSI
            sst: Slice/Service Type
            sd: Slice Differentiator

        Returns:
            更新是否成功
        """
        try:
            # 更新用戶的 slice 配置
            result = await self.db.subscribers.update_one(
                {"imsi": imsi},
                {
                    "$set": {
                        "slice.0.sst": sst,
                        "slice.0.sd": sd,
                        "modified": datetime.utcnow().isoformat(),
                    }
                },
            )

            if result.modified_count > 0:
                logger.info("用戶 Slice 更新成功", imsi=imsi, sst=sst, sd=sd)
                return True
            else:
                logger.warning("用戶 Slice 更新失敗 - 找不到用戶", imsi=imsi)
                return False

        except Exception as e:
            logger.error("更新用戶 Slice 失敗", imsi=imsi, sst=sst, sd=sd, error=str(e))
            raise

    async def get_session_info(self, imsi: str) -> Optional[Dict[str, Any]]:
        """
        取得用戶會話資訊

        Args:
            imsi: 用戶 IMSI

        Returns:
            會話資訊字典
        """
        try:
            # 從 sessions 集合中查找
            session = await self.db.sessions.find_one({"imsi": imsi})
            return session
        except Exception as e:
            logger.error("取得會話資訊失敗", imsi=imsi, error=str(e))
            raise

    async def create_subscriber(
        self,
        imsi: str,
        key: str,
        opc: str,
        apn: str = "internet",
        sst: int = 1,
        sd: str = "0x111111",
    ) -> bool:
        """
        建立新用戶

        Args:
            imsi: 用戶 IMSI
            key: K 金鑰
            opc: OPc 值
            apn: 接入點名稱
            sst: Slice/Service Type
            sd: Slice Differentiator

        Returns:
            建立是否成功
        """
        try:
            subscriber_doc = {
                "imsi": imsi,
                "msisdn": [],
                "imeisv": [],
                "mme_host": [],
                "mme_realm": [],
                "purge_flag": [],
                "security": {
                    "k": key,
                    "amf": "8000",
                    "op": None,
                    "opc": opc,
                    "sqn": 64,
                },
                "ambr": {
                    "downlink": {"value": 1, "unit": 3},
                    "uplink": {"value": 1, "unit": 3},
                },
                "slice": [
                    {
                        "sst": sst,
                        "sd": sd,
                        "default_indicator": True,
                        "session": [
                            {
                                "name": apn,
                                "type": 3,  # IPv4
                                "ambr": {
                                    "downlink": {"value": 1, "unit": 3},
                                    "uplink": {"value": 1, "unit": 3},
                                },
                                "qos": {
                                    "index": 9,
                                    "arp": {
                                        "priority_level": 8,
                                        "pre_emption_capability": 1,
                                        "pre_emption_vulnerability": 1,
                                    },
                                },
                            }
                        ],
                    }
                ],
                "access_restriction_data": 32,
                "subscriber_status": 0,
                "network_access_mode": 0,
                "subscribed_rau_tau_timer": 12,
                "__v": 0,
                "created": datetime.utcnow().isoformat(),
            }

            result = await self.db.subscribers.insert_one(subscriber_doc)

            if result.inserted_id:
                logger.info("用戶建立成功", imsi=imsi)
                return True
            else:
                logger.error("用戶建立失敗", imsi=imsi)
                return False

        except Exception as e:
            logger.error("建立用戶失敗", imsi=imsi, error=str(e))
            raise

    async def delete_subscriber(self, imsi: str) -> bool:
        """
        刪除用戶

        Args:
            imsi: 用戶 IMSI

        Returns:
            刪除是否成功
        """
        try:
            result = await self.db.subscribers.delete_one({"imsi": imsi})

            if result.deleted_count > 0:
                logger.info("用戶刪除成功", imsi=imsi)
                return True
            else:
                logger.warning("用戶刪除失敗 - 找不到用戶", imsi=imsi)
                return False

        except Exception as e:
            logger.error("刪除用戶失敗", imsi=imsi, error=str(e))
            raise

    async def find_one(
        self, collection: str, query: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        在指定集合中查詢單個文檔

        Args:
            collection: 集合名稱
            query: 查詢條件

        Returns:
            查詢結果，如果不存在則回傳 None
        """
        try:
            result = await self.db[collection].find_one(query)
            return result
        except Exception as e:
            logger.error(
                "查詢文檔失敗", collection=collection, query=query, error=str(e)
            )
            raise

    async def update_one(
        self, collection: str, query: Dict[str, Any], update: Dict[str, Any]
    ) -> bool:
        """
        更新指定集合中的單個文檔

        Args:
            collection: 集合名稱
            query: 查詢條件
            update: 更新操作

        Returns:
            更新是否成功
        """
        try:
            result = await self.db[collection].update_one(query, update)
            return result.modified_count > 0
        except Exception as e:
            logger.error(
                "更新文檔失敗", collection=collection, query=query, error=str(e)
            )
            raise

    async def count_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """
        計算符合條件的文檔數量

        Args:
            collection: 集合名稱
            query: 查詢條件

        Returns:
            文檔數量
        """
        try:
            count = await self.db[collection].count_documents(query)
            return count
        except Exception as e:
            logger.error(
                "計算文檔數量失敗", collection=collection, query=query, error=str(e)
            )
            raise
