from typing import Dict, List, Optional, Any
import pymongo
from pymongo.collection import Collection
from pymongo.database import Database


class Open5GSService:
    """與Open5GS MongoDB數據庫交互的服務類"""

    def __init__(self, mongo_uri: str = "mongodb://mongo:27017/open5gs"):
        """初始化與Open5GS MongoDB的連接

        Args:
            mongo_uri: MongoDB連接URI，默認指向Docker網絡中的mongo服務
        """
        self.mongo_client = pymongo.MongoClient(mongo_uri)
        self.db: Database = self.mongo_client.get_database()
        self.subscribers: Collection = self.db.subscribers

    async def get_subscribers(self) -> List[Dict[str, Any]]:
        """獲取所有註冊的用戶

        Returns:
            包含所有用戶信息的列表
        """
        return list(self.subscribers.find({}, {"_id": 0}))

    async def get_subscriber_by_imsi(self, imsi: str) -> Optional[Dict[str, Any]]:
        """通過IMSI獲取特定用戶

        Args:
            imsi: 用戶的IMSI識別碼

        Returns:
            用戶信息字典，如果未找到則返回None
        """
        return self.subscribers.find_one({"imsi": imsi}, {"_id": 0})

    async def add_subscriber(
        self,
        imsi: str,
        key: str,
        opc: str,
        apn: str = "internet",
        sst: int = 1,
        sd: str = "0xffffff",
    ) -> bool:
        """添加新用戶到Open5GS

        Args:
            imsi: 用戶的IMSI識別碼
            key: 用戶的密鑰
            opc: 用戶的OPC值
            apn: 接入點名稱，默認為"internet"
            sst: 切片服務類型，默認為1
            sd: 切片區分符，默認為"0xffffff"

        Returns:
            操作是否成功
        """
        # 此函數僅作為範例，實際實現需要構建完整的用戶文檔
        # 完整實現應該參考open5gs-dbctl中的add命令
        try:
            subscriber_doc = {
                "imsi": imsi,
                "security": {"k": key, "opc": opc, "op": None, "amf": "8000"},
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
                                "type": 1,
                                "qos": {
                                    "index": 9,
                                    "arp": {
                                        "priority_level": 8,
                                        "pre_emption_capability": 1,
                                        "pre_emption_vulnerability": 1,
                                    },
                                },
                                "ambr": {
                                    "downlink": {"value": 1, "unit": 3},
                                    "uplink": {"value": 1, "unit": 3},
                                },
                            }
                        ],
                    }
                ],
                "access_restriction_data": 32,
                "subscriber_status": 0,
                "network_access_mode": 0,
                "subscribed_rau_tau_timer": 12,
            }

            result = self.subscribers.insert_one(subscriber_doc)
            return result.acknowledged
        except Exception as e:
            print(f"添加用戶失敗: {e}")
            return False

    async def remove_subscriber(self, imsi: str) -> bool:
        """移除用戶

        Args:
            imsi: 要移除的用戶的IMSI識別碼

        Returns:
            操作是否成功
        """
        try:
            result = self.subscribers.delete_one({"imsi": imsi})
            return result.deleted_count > 0
        except Exception as e:
            print(f"刪除用戶失敗: {e}")
            return False
