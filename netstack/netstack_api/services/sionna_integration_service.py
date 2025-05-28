"""
Sionna Integration Service
負責接收 simworld 的 Sionna 通道模型並應用到 UERANSIM 配置
"""

import asyncio
import logging
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChannelModelUpdate:
    """通道模型更新"""

    ue_id: str
    gnb_id: str
    sinr_db: float
    rsrp_dbm: float
    rsrq_db: float
    cqi: int
    throughput_mbps: float
    latency_ms: float
    error_rate: float
    timestamp: datetime
    valid_until: datetime


class SionnaIntegrationService:
    """Sionna 整合服務"""

    def __init__(
        self,
        simworld_api_url: str = "http://simworld-backend:8000",
        update_interval_sec: int = 30,
        ueransim_config_dir: str = "/tmp/ueransim_configs",
    ):
        self.simworld_api_url = simworld_api_url
        self.update_interval_sec = update_interval_sec
        self.ueransim_config_dir = ueransim_config_dir

        # 活躍的通道模型
        self.active_channel_models: Dict[str, ChannelModelUpdate] = {}

        # 更新任務
        self.update_task: Optional[asyncio.Task] = None
        self.is_running = False

        # HTTP 客戶端
        self.http_session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """啟動服務"""
        if self.is_running:
            logger.warning("Sionna 整合服務已在運行")
            return

        logger.info("啟動 Sionna 整合服務...")

        # 創建 HTTP 客戶端
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )

        self.is_running = True

        # 啟動定期更新任務
        self.update_task = asyncio.create_task(self._periodic_update_loop())

        logger.info("Sionna 整合服務已啟動")

    async def stop(self):
        """停止服務"""
        if not self.is_running:
            return

        logger.info("停止 Sionna 整合服務...")

        self.is_running = False

        # 取消更新任務
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        # 關閉 HTTP 客戶端
        if self.http_session:
            await self.http_session.close()

        logger.info("Sionna 整合服務已停止")

    async def request_channel_simulation(
        self,
        ue_positions: List[Dict[str, Any]],
        gnb_positions: List[Dict[str, Any]],
        environment_type: str = "urban",
        frequency_ghz: float = 2.1,
        bandwidth_mhz: float = 20,
    ) -> List[Dict[str, Any]]:
        """請求通道模擬"""

        if not self.http_session:
            raise RuntimeError("服務未啟動")

        simulation_request = {
            "simulation_id": f"netstack_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "environment_type": environment_type,
            "carrier_frequency_hz": frequency_ghz * 1e9,
            "bandwidth_hz": bandwidth_mhz * 1e6,
            "transmitters": gnb_positions,
            "receivers": ue_positions,
        }

        try:
            logger.info(f"請求通道模擬: {simulation_request['simulation_id']}")

            async with self.http_session.post(
                f"{self.simworld_api_url}/api/v1/wireless/simulate",
                json=simulation_request,
            ) as response:
                response.raise_for_status()
                channel_responses = await response.json()

            logger.info(f"收到 {len(channel_responses)} 個通道響應")
            return channel_responses

        except Exception as e:
            logger.error(f"通道模擬請求失敗: {e}")
            raise

    async def convert_channels_to_ran_params(
        self, channel_responses: List[Dict[str, Any]], ue_gnb_mapping: Dict[str, str]
    ) -> List[ChannelModelUpdate]:
        """將通道響應轉換為 RAN 參數"""

        if not self.http_session:
            raise RuntimeError("服務未啟動")

        conversion_results = []

        for i, channel_response in enumerate(channel_responses):
            # 確定 UE 和 gNodeB ID
            ue_id = f"ue_{i:03d}"
            gnb_id = ue_gnb_mapping.get(ue_id, "gnb_001")

            try:
                # 調用轉換 API
                params = {"ue_id": ue_id, "gnb_id": gnb_id}

                async with self.http_session.post(
                    f"{self.simworld_api_url}/api/v1/wireless/channel-to-ran",
                    json=channel_response,
                    params=params,
                ) as response:
                    response.raise_for_status()
                    conversion_result = await response.json()

                # 提取 RAN 參數
                ran_params = conversion_result["ran_parameters"]

                channel_update = ChannelModelUpdate(
                    ue_id=ran_params["ue_id"],
                    gnb_id=ran_params["gnb_id"],
                    sinr_db=ran_params["sinr_db"],
                    rsrp_dbm=ran_params["rsrp_dbm"],
                    rsrq_db=ran_params["rsrq_db"],
                    cqi=ran_params["cqi"],
                    throughput_mbps=ran_params["throughput_mbps"],
                    latency_ms=ran_params["latency_ms"],
                    error_rate=ran_params["error_rate"],
                    timestamp=datetime.fromisoformat(
                        ran_params["timestamp"].replace("Z", "+00:00")
                    ),
                    valid_until=datetime.fromisoformat(
                        ran_params["valid_until"].replace("Z", "+00:00")
                    ),
                )

                conversion_results.append(channel_update)

            except Exception as e:
                logger.error(f"轉換通道 {i} 失敗: {e}")
                continue

        logger.info(f"成功轉換 {len(conversion_results)} 個通道參數")
        return conversion_results

    async def apply_channel_models_to_ueransim(
        self, channel_updates: List[ChannelModelUpdate]
    ) -> Dict[str, Any]:
        """將通道模型應用到 UERANSIM 配置"""

        applied_updates = {}
        failed_updates = {}

        for update in channel_updates:
            try:
                # 更新 UERANSIM 配置
                success = await self._update_ueransim_config(update)

                if success:
                    # 更新活躍模型
                    key = f"{update.ue_id}_{update.gnb_id}"
                    self.active_channel_models[key] = update
                    applied_updates[key] = {
                        "ue_id": update.ue_id,
                        "gnb_id": update.gnb_id,
                        "sinr_db": update.sinr_db,
                        "rsrp_dbm": update.rsrp_dbm,
                        "cqi": update.cqi,
                        "applied_at": update.timestamp.isoformat(),
                    }
                else:
                    failed_updates[f"{update.ue_id}_{update.gnb_id}"] = "配置更新失敗"

            except Exception as e:
                logger.error(f"應用通道模型失敗 {update.ue_id}: {e}")
                failed_updates[f"{update.ue_id}_{update.gnb_id}"] = str(e)

        return {
            "applied": applied_updates,
            "failed": failed_updates,
            "total_applied": len(applied_updates),
            "total_failed": len(failed_updates),
        }

    async def _update_ueransim_config(self, update: ChannelModelUpdate) -> bool:
        """更新 UERANSIM 配置"""

        try:
            # 這裡實現實際的 UERANSIM 配置更新邏輯
            # 目前先模擬更新過程

            logger.debug(
                f"更新 UERANSIM 配置: UE {update.ue_id} → gNB {update.gnb_id}, "
                f"SINR: {update.sinr_db:.1f}dB, RSRP: {update.rsrp_dbm:.1f}dBm, CQI: {update.cqi}"
            )

            # 模擬配置文件更新
            config_data = {
                "ue_id": update.ue_id,
                "gnb_id": update.gnb_id,
                "channel_params": {
                    "sinr_db": update.sinr_db,
                    "rsrp_dbm": update.rsrp_dbm,
                    "rsrq_db": update.rsrq_db,
                    "cqi": update.cqi,
                    "throughput_mbps": update.throughput_mbps,
                    "latency_ms": update.latency_ms,
                    "error_rate": update.error_rate,
                },
                "updated_at": update.timestamp.isoformat(),
                "valid_until": update.valid_until.isoformat(),
            }

            # 在實際實現中，這裡會：
            # 1. 更新 UERANSIM 配置文件
            # 2. 通知 UERANSIM 重新加載配置
            # 3. 驗證配置是否生效

            # 模擬延遲
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"更新 UERANSIM 配置失敗: {e}")
            return False

    async def _periodic_update_loop(self):
        """定期更新循環"""

        logger.info(f"啟動定期更新循環，間隔: {self.update_interval_sec} 秒")

        while self.is_running:
            try:
                await self._cleanup_expired_models()
                await asyncio.sleep(self.update_interval_sec)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定期更新循環錯誤: {e}")
                await asyncio.sleep(5)  # 錯誤後短暫等待

    async def _cleanup_expired_models(self):
        """清理過期的通道模型"""

        now = datetime.utcnow()
        expired_keys = []

        for key, model in self.active_channel_models.items():
            if model.valid_until < now:
                expired_keys.append(key)

        for key in expired_keys:
            del self.active_channel_models[key]
            logger.debug(f"清理過期通道模型: {key}")

        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 個過期通道模型")

    async def get_active_channel_models(self) -> Dict[str, Dict[str, Any]]:
        """獲取活躍的通道模型"""

        result = {}
        now = datetime.utcnow()

        for key, model in self.active_channel_models.items():
            if model.valid_until > now:
                result[key] = {
                    "ue_id": model.ue_id,
                    "gnb_id": model.gnb_id,
                    "sinr_db": model.sinr_db,
                    "rsrp_dbm": model.rsrp_dbm,
                    "rsrq_db": model.rsrq_db,
                    "cqi": model.cqi,
                    "throughput_mbps": model.throughput_mbps,
                    "latency_ms": model.latency_ms,
                    "error_rate": model.error_rate,
                    "timestamp": model.timestamp.isoformat(),
                    "valid_until": model.valid_until.isoformat(),
                    "remaining_seconds": (model.valid_until - now).total_seconds(),
                }

        return result

    async def quick_channel_simulation_and_apply(
        self,
        ue_positions: List[Dict[str, Any]],
        gnb_positions: List[Dict[str, Any]],
        environment_type: str = "urban",
        frequency_ghz: float = 2.1,
        bandwidth_mhz: float = 20,
    ) -> Dict[str, Any]:
        """快速通道模擬和應用"""

        try:
            # 1. 請求通道模擬
            channel_responses = await self.request_channel_simulation(
                ue_positions=ue_positions,
                gnb_positions=gnb_positions,
                environment_type=environment_type,
                frequency_ghz=frequency_ghz,
                bandwidth_mhz=bandwidth_mhz,
            )

            # 2. 轉換為 RAN 參數
            ue_gnb_mapping = {}
            for i, ue_pos in enumerate(ue_positions):
                ue_id = f"ue_{i:03d}"
                gnb_id = f"gnb_{i % len(gnb_positions):03d}"
                ue_gnb_mapping[ue_id] = gnb_id

            channel_updates = await self.convert_channels_to_ran_params(
                channel_responses, ue_gnb_mapping
            )

            # 3. 應用到 UERANSIM
            apply_result = await self.apply_channel_models_to_ueransim(channel_updates)

            return {
                "simulation_completed": True,
                "channel_responses_count": len(channel_responses),
                "channel_updates_count": len(channel_updates),
                "apply_result": apply_result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"快速通道模擬和應用失敗: {e}")
            return {
                "simulation_completed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""

        return {
            "is_running": self.is_running,
            "simworld_api_url": self.simworld_api_url,
            "update_interval_sec": self.update_interval_sec,
            "active_models_count": len(self.active_channel_models),
            "http_session_active": self.http_session is not None
            and not self.http_session.closed,
        }
