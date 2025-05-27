"""
NetStack Slice Service - 5G 網路切片管理服務

提供 eMBB 和 uRLLC 切片之間的動態切換功能，
包括 UE 切片配置更新、效能監控和狀態管理。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import structlog
from prometheus_client import Counter, Histogram

from ..adapters.mongo_adapter import MongoAdapter
from ..adapters.open5gs_adapter import Open5GSAdapter
from ..adapters.redis_adapter import RedisAdapter

logger = structlog.get_logger(__name__)

# Prometheus 指標
SLICE_SWITCH_COUNTER = Counter(
    "netstack_slice_switch_total",
    "Total number of slice switches",
    ["from_slice", "to_slice", "status"],
)

SLICE_SWITCH_DURATION = Histogram(
    "netstack_slice_switch_duration_seconds",
    "Time taken to switch slices",
    ["slice_type"],
)

SLICE_PERFORMANCE_HISTOGRAM = Histogram(
    "netstack_slice_performance_seconds",
    "Slice performance metrics",
    ["slice_type", "metric_type"],
)


class SliceType(str, Enum):
    """網路切片類型"""

    EMBB = "eMBB"
    URLLC = "uRLLC"


class SliceConfig:
    """切片配置類別"""

    SLICE_CONFIGS = {
        SliceType.EMBB: {
            "sst": 1,
            "sd": "0x111111",
            "name": "Enhanced Mobile Broadband",
            "description": "高頻寬、低延遲敏感度的服務",
            "max_bandwidth": "1000Mbps",
            "target_latency": "100ms",
            "reliability": "99%",
            "priority": 5,
            "qos_profile": {
                "5qi": 9,
                "arp": {"priority": 8, "preemption_capability": "NOT_PREEMPT"},
                "session_ambr": {"uplink": "1000Mbps", "downlink": "2000Mbps"},
            },
        },
        SliceType.URLLC: {
            "sst": 2,
            "sd": "0x222222",
            "name": "Ultra-Reliable Low Latency Communications",
            "description": "超可靠、超低延遲的關鍵任務服務",
            "max_bandwidth": "100Mbps",
            "target_latency": "1ms",
            "reliability": "99.999%",
            "priority": 1,
            "qos_profile": {
                "5qi": 1,
                "arp": {"priority": 1, "preemption_capability": "MAY_PREEMPT"},
                "session_ambr": {"uplink": "100Mbps", "downlink": "100Mbps"},
            },
        },
    }

    @classmethod
    def get_config(cls, slice_type: SliceType) -> Dict:
        """取得切片配置"""
        return cls.SLICE_CONFIGS.get(slice_type, {})

    @classmethod
    def get_all_configs(cls) -> Dict[SliceType, Dict]:
        """取得所有切片配置"""
        return cls.SLICE_CONFIGS


class SliceService:
    """網路切片管理服務"""

    def __init__(
        self,
        mongo_adapter: MongoAdapter,
        open5gs_adapter: Open5GSAdapter,
        redis_adapter: RedisAdapter,
    ):
        self.mongo_adapter = mongo_adapter
        self.open5gs_adapter = open5gs_adapter
        self.redis_adapter = redis_adapter
        self.logger = logger.bind(service="slice_service")

    async def switch_slice(
        self, imsi: str, target_slice: SliceType, force: bool = False
    ) -> Dict:
        """
        切換 UE 的網路切片

        Args:
            imsi: UE 的 IMSI
            target_slice: 目標切片類型
            force: 是否強制切換（忽略當前狀態）

        Returns:
            切換結果字典
        """
        start_time = datetime.utcnow()
        current_slice = None  # 初始化變數避免作用域問題

        try:
            self.logger.info("開始切片切換", imsi=imsi, target_slice=target_slice.value)

            # 1. 驗證 UE 存在
            ue_info = await self._get_ue_info(imsi)
            if not ue_info:
                raise ValueError(f"UE {imsi} 不存在")

            current_slice = ue_info.get("current_slice")

            # 2. 檢查是否需要切換
            if current_slice == target_slice.value and not force:
                self.logger.info(
                    "UE 已在目標切片，無需切換", imsi=imsi, current_slice=current_slice
                )
                return {
                    "success": True,
                    "message": "UE 已在目標切片",
                    "imsi": imsi,
                    "current_slice": current_slice,
                    "target_slice": target_slice.value,
                    "switch_time": 0,
                }

            # 3. 執行切片切換
            with SLICE_SWITCH_DURATION.labels(slice_type=target_slice.value).time():
                switch_result = await self._perform_slice_switch(
                    imsi, current_slice, target_slice
                )

            # 4. 更新 UE 記錄
            await self._update_ue_slice_info(imsi, target_slice, switch_result)

            # 5. 記錄指標
            SLICE_SWITCH_COUNTER.labels(
                from_slice=current_slice or "none",
                to_slice=target_slice.value,
                status="success",
            ).inc()

            switch_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.info(
                "切片切換成功",
                imsi=imsi,
                from_slice=current_slice,
                to_slice=target_slice.value,
                switch_time=switch_time,
            )

            return {
                "success": True,
                "message": "切片切換成功",
                "imsi": imsi,
                "previous_slice": current_slice,
                "current_slice": target_slice.value,
                "switch_time": switch_time,
                "slice_config": SliceConfig.get_config(target_slice),
            }

        except Exception as e:
            # 記錄失敗指標
            SLICE_SWITCH_COUNTER.labels(
                from_slice=current_slice or "unknown",
                to_slice=target_slice.value,
                status="error",
            ).inc()

            self.logger.error(
                "切片切換失敗", imsi=imsi, target_slice=target_slice.value, error=str(e)
            )

            return {
                "success": False,
                "message": f"切片切換失敗: {str(e)}",
                "imsi": imsi,
                "target_slice": target_slice.value,
                "error": str(e),
            }

    async def get_slice_types(self) -> Dict:
        """取得支援的切片類型和配置"""
        return {
            "slice_types": [slice_type.value for slice_type in SliceType],
            "configurations": SliceConfig.get_all_configs(),
        }

    async def get_slice_statistics(
        self, slice_type: Optional[SliceType] = None
    ) -> Dict:
        """取得切片統計資訊"""
        try:
            stats = {}

            if slice_type:
                # 取得特定切片統計
                stats[slice_type.value] = await self._get_slice_stats(slice_type)
            else:
                # 取得所有切片統計
                for st in SliceType:
                    stats[st.value] = await self._get_slice_stats(st)

            return {
                "success": True,
                "statistics": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error("取得切片統計失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def _get_ue_info(self, imsi: str) -> Optional[Dict]:
        """取得 UE 資訊"""
        try:
            # 使用與 UE service 相同的方法查詢 UE 資訊
            subscriber = await self.mongo_adapter.get_subscriber(imsi)
            if not subscriber:
                self.logger.warning("找不到 UE", imsi=imsi)
                return None

            # 轉換為與 UE service 相同的格式
            ue_info = self._convert_subscriber_to_ue_info(subscriber)

            self.logger.debug(
                "UE 資訊查詢成功",
                imsi=imsi,
                current_slice=ue_info.get("slice", {}).get("slice_type"),
                sst=ue_info.get("slice", {}).get("sst"),
                sd=ue_info.get("slice", {}).get("sd"),
            )

            # 添加 current_slice 欄位以便切換邏輯使用
            ue_info["current_slice"] = ue_info.get("slice", {}).get("slice_type")

            return ue_info
        except Exception as e:
            self.logger.error("查詢 UE 資訊失敗", imsi=imsi, error=str(e))
            return None

    def _convert_subscriber_to_ue_info(
        self, subscriber: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        將資料庫的 subscriber 資料轉換為 UE 資訊格式
        (與 UE service 中的方法相同)
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
                created_at_str = datetime.utcnow().isoformat()

            return {
                "imsi": subscriber["imsi"],
                "apn": session_info.get("name", "internet"),
                "slice": {"sst": sst, "sd": sd, "slice_type": slice_type},
                "status": "registered",  # 預設狀態
                "ip_address": None,  # 需要從會話資訊取得
                "last_seen": None,
                "created_at": created_at_str,
            }

        except Exception as e:
            self.logger.error(
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
                "created_at": datetime.utcnow().isoformat(),
            }

    async def _perform_slice_switch(
        self, imsi: str, current_slice: Optional[str], target_slice: SliceType
    ) -> Dict:
        """執行實際的切片切換操作"""

        target_config = SliceConfig.get_config(target_slice)

        # 1. 更新 AMF 配置
        amf_result = await self.open5gs_adapter.update_ue_slice_config(
            imsi=imsi,
            sst=target_config["sst"],
            sd=target_config["sd"],
            qos_profile=target_config["qos_profile"],
        )

        # 2. 更新 SMF 配置
        smf_result = await self.open5gs_adapter.update_smf_session_config(
            imsi=imsi, slice_config=target_config
        )

        # 3. 觸發 UE 重新註冊（如果需要）
        if current_slice and current_slice != target_slice.value:
            await self.open5gs_adapter.trigger_ue_reregistration(imsi)

        return {
            "amf_update": amf_result,
            "smf_update": smf_result,
            "config_applied": target_config,
        }

    async def _update_ue_slice_info(
        self, imsi: str, target_slice: SliceType, switch_result: Dict
    ) -> None:
        """更新 UE 的切片資訊記錄"""

        target_config = SliceConfig.get_config(target_slice)

        # 使用與 UE service 相同的更新方法
        success = await self.mongo_adapter.update_subscriber_slice(
            imsi=imsi, sst=target_config["sst"], sd=target_config["sd"]
        )

        if not success:
            self.logger.warning("MongoDB 更新失敗，用戶可能不存在", imsi=imsi)

        # 清除 UE 資訊緩存，強制下次查詢時重新載入
        try:
            await self.redis_adapter.client.delete(f"ue:info:{imsi}")
            self.logger.debug("已清除 UE 資訊緩存", imsi=imsi)
        except Exception as e:
            self.logger.warning("清除 UE 資訊緩存失敗", imsi=imsi, error=str(e))

        # 記錄切換歷史（如果 mongo_adapter 支持的話）
        try:
            switch_history = {
                "timestamp": datetime.utcnow().isoformat(),
                "target_slice": target_slice.value,
                "switch_result": switch_result,
            }

            # 嘗試添加到切換歷史
            await self.mongo_adapter.add_slice_switch_history(imsi, switch_history)
        except AttributeError:
            # 如果 mongo_adapter 沒有這個方法，就跳過
            self.logger.debug("mongo_adapter 不支持切換歷史記錄")
        except Exception as e:
            self.logger.warning("記錄切換歷史失敗", imsi=imsi, error=str(e))

        self.logger.info(
            "UE 切片資訊已更新", imsi=imsi, target_slice=target_slice.value
        )

    async def _get_slice_stats(self, slice_type: SliceType) -> Dict:
        """取得特定切片的統計資訊"""

        # 查詢使用該切片的 UE 數量
        ue_count = await self.mongo_adapter.count_documents(
            "subscribers", {"current_slice": slice_type.value}
        )

        # 查詢最近24小時的切換次數
        yesterday = datetime.utcnow() - timedelta(hours=24)
        switch_count = await self.mongo_adapter.count_documents(
            "subscribers",
            {
                "slice_history.timestamp": {"$gte": yesterday},
                "slice_history.target_slice": slice_type.value,
            },
        )

        # 取得切片配置
        config = SliceConfig.get_config(slice_type)

        return {
            "slice_type": slice_type.value,
            "active_ues": ue_count,
            "switches_24h": switch_count,
            "configuration": config,
            "performance_metrics": await self._get_slice_performance_metrics(
                slice_type
            ),
        }

    async def _get_slice_performance_metrics(self, slice_type: SliceType) -> Dict:
        """取得切片效能指標"""

        # 這裡可以整合實際的效能監控系統
        # 目前回傳模擬數據

        if slice_type == SliceType.EMBB:
            return {
                "average_latency_ms": 95,
                "peak_bandwidth_mbps": 950,
                "packet_loss_rate": 0.01,
                "availability_percent": 99.2,
            }
        elif slice_type == SliceType.URLLC:
            return {
                "average_latency_ms": 2,
                "peak_bandwidth_mbps": 85,
                "packet_loss_rate": 0.0001,
                "availability_percent": 99.999,
            }

        return {}
