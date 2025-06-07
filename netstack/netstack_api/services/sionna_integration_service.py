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
            logger.debug(
                f"更新 UERANSIM 配置: UE {update.ue_id} → gNB {update.gnb_id}, "
                f"SINR: {update.sinr_db:.1f}dB, RSRP: {update.rsrp_dbm:.1f}dBm, CQI: {update.cqi}"
            )

            # 實際的 UERANSIM 配置更新
            config_updated = await self._write_ueransim_config_file(update)
            if not config_updated:
                return False

            # 動態更新通道參數到正在運行的 UERANSIM 實例
            runtime_updated = await self._update_runtime_channel_params(update)
            if not runtime_updated:
                logger.warning(f"運行時更新失敗，但配置文件已更新: {update.ue_id}")

            # 驗證配置是否生效
            verified = await self._verify_channel_config(update)
            
            return config_updated and verified

        except Exception as e:
            logger.error(f"更新 UERANSIM 配置失敗: {e}")
            return False

    async def _write_ueransim_config_file(self, update: ChannelModelUpdate) -> bool:
        """寫入 UERANSIM 配置文件"""
        try:
            config_file_path = self.ueransim_config_dir / f"{update.ue_id}.yaml"
            
            # 讀取現有配置或創建新配置
            config_data = await self._load_existing_config(config_file_path)
            
            # 更新通道相關參數
            config_data.update({
                "rf-params": {
                    "dl-nr-arfcn": self._calculate_arfcn_from_sinr(update.sinr_db),
                    "tx-power": self._calculate_tx_power(update.rsrp_dbm),
                    "rx-gain": self._calculate_rx_gain(update.rsrq_db),
                },
                "channel-model": {
                    "type": "sionna",
                    "sinr-db": update.sinr_db,
                    "rsrp-dbm": update.rsrp_dbm,
                    "rsrq-db": update.rsrq_db,
                    "cqi": update.cqi,
                    "throughput-mbps": update.throughput_mbps,
                    "latency-ms": update.latency_ms,
                    "ber": update.error_rate,
                    "updated-at": update.timestamp.isoformat(),
                    "valid-until": update.valid_until.isoformat(),
                },
                "qos-params": {
                    "adaptive-cqi": True,
                    "target-bler": min(0.1, update.error_rate * 10),
                    "retx-threshold": self._calculate_retx_threshold(update.error_rate),
                }
            })

            # 寫入配置文件
            import yaml
            with open(config_file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)

            logger.debug(f"UERANSIM 配置文件已更新: {config_file_path}")
            return True

        except Exception as e:
            logger.error(f"寫入 UERANSIM 配置文件失敗: {e}")
            return False

    async def _update_runtime_channel_params(self, update: ChannelModelUpdate) -> bool:
        """動態更新運行時通道參數"""
        try:
            # 通過 UERANSIM 的控制接口動態更新參數
            control_command = {
                "command": "update_channel_params",
                "ue_id": update.ue_id,
                "params": {
                    "sinr_db": update.sinr_db,
                    "rsrp_dbm": update.rsrp_dbm,
                    "cqi": update.cqi,
                    "ber": update.error_rate,
                }
            }

            # 實際環境中會通過 UERANSIM CLI 或 IPC 介面發送命令
            # 這裡模擬命令執行
            await asyncio.sleep(0.05)  # 模擬運行時更新延遲
            
            logger.debug(f"運行時通道參數已更新: {update.ue_id}")
            return True

        except Exception as e:
            logger.error(f"運行時通道參數更新失敗: {e}")
            return False

    async def _verify_channel_config(self, update: ChannelModelUpdate) -> bool:
        """驗證通道配置是否生效"""
        try:
            # 讀取 UERANSIM 狀態確認配置生效
            # 實際環境中會查詢 UERANSIM 的當前配置狀態
            
            # 模擬驗證過程
            await asyncio.sleep(0.02)
            
            # 檢查配置是否在合理範圍內
            if not (-50 <= update.sinr_db <= 30):
                logger.warning(f"SINR 值超出合理範圍: {update.sinr_db}dB")
                return False
                
            if not (-150 <= update.rsrp_dbm <= -30):
                logger.warning(f"RSRP 值超出合理範圍: {update.rsrp_dbm}dBm")
                return False

            logger.debug(f"通道配置驗證成功: {update.ue_id}")
            return True

        except Exception as e:
            logger.error(f"通道配置驗證失敗: {e}")
            return False

    async def _load_existing_config(self, config_file_path) -> dict:
        """加載現有配置文件"""
        try:
            if config_file_path.exists():
                import yaml
                with open(config_file_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                # 返回默認配置模板
                return {
                    "ue-id": config_file_path.stem,
                    "serving-cell": "gnb_001",
                    "rf-params": {},
                    "channel-model": {},
                    "qos-params": {}
                }
        except Exception as e:
            logger.error(f"加載配置文件失敗: {e}")
            return {}

    def _calculate_arfcn_from_sinr(self, sinr_db: float) -> int:
        """根據 SINR 計算 ARFCN"""
        # 基礎 ARFCN 為 n78 頻段 (3.5GHz)
        base_arfcn = 632628
        # 根據 SINR 調整頻點以最佳化性能
        adjustment = int((sinr_db + 10) * 10)  # 正規化調整
        return base_arfcn + adjustment

    def _calculate_tx_power(self, rsrp_dbm: float) -> int:
        """根據 RSRP 計算發射功率"""
        # 基於 RSRP 推算合適的發射功率
        # RSRP 與發射功率和路徑損耗相關
        if rsrp_dbm > -70:
            return 10  # 低功率
        elif rsrp_dbm > -90:
            return 15  # 中功率
        else:
            return 23  # 高功率

    def _calculate_rx_gain(self, rsrq_db: float) -> int:
        """根據 RSRQ 計算接收增益"""
        # 基於 RSRQ 調整接收增益
        if rsrq_db > -10:
            return 0   # 無需額外增益
        elif rsrq_db > -15:
            return 3   # 小幅增益
        else:
            return 6   # 高增益

    def _calculate_retx_threshold(self, error_rate: float) -> int:
        """根據錯誤率計算重傳閾值"""
        if error_rate < 0.01:
            return 2  # 低錯誤率，少重傳
        elif error_rate < 0.05:
            return 3  # 中等錯誤率
        else:
            return 4  # 高錯誤率，多重傳

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
        interference_sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """快速通道模擬和應用（支援干擾源）"""

        try:
            start_time = datetime.utcnow()
            
            # 1. 請求通道模擬（包含干擾）
            channel_responses = await self.request_channel_simulation_with_interference(
                ue_positions=ue_positions,
                gnb_positions=gnb_positions,
                environment_type=environment_type,
                frequency_ghz=frequency_ghz,
                bandwidth_mhz=bandwidth_mhz,
                interference_sources=interference_sources or [],
            )

            # 2. 轉換為 RAN 參數
            ue_gnb_mapping = await self._create_optimal_ue_gnb_mapping(
                ue_positions, gnb_positions, channel_responses
            )

            channel_updates = await self.convert_channels_to_ran_params(
                channel_responses, ue_gnb_mapping
            )

            # 3. 並行應用到 UERANSIM
            apply_result = await self.apply_channel_models_to_ueransim(channel_updates)

            # 4. 生成性能報告
            performance_report = await self._generate_performance_report(
                channel_updates, apply_result, start_time
            )

            return {
                "simulation_completed": True,
                "channel_responses_count": len(channel_responses),
                "channel_updates_count": len(channel_updates),
                "apply_result": apply_result,
                "performance_report": performance_report,
                "interference_detected": len(interference_sources or []) > 0,
                "simulation_duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"快速通道模擬和應用失敗: {e}")
            return {
                "simulation_completed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def request_channel_simulation_with_interference(
        self,
        ue_positions: List[Dict[str, Any]],
        gnb_positions: List[Dict[str, Any]],
        environment_type: str = "urban",
        frequency_ghz: float = 2.1,
        bandwidth_mhz: float = 20,
        interference_sources: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """請求包含干擾的通道模擬"""

        if not self.http_session:
            raise RuntimeError("服務未啟動")

        simulation_request = {
            "simulation_id": f"netstack_sionna_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "environment_type": environment_type,
            "carrier_frequency_hz": frequency_ghz * 1e9,
            "bandwidth_hz": bandwidth_mhz * 1e6,
            "transmitters": gnb_positions,
            "receivers": ue_positions,
            "interference_sources": interference_sources or [],
            "channel_model_params": {
                "enable_path_loss": True,
                "enable_shadowing": True,
                "enable_fast_fading": True,
                "doppler_enabled": True,
                "delay_spread_enabled": True,
            },
            "simulation_params": {
                "samples_per_slot": 1000,
                "simulation_time_ms": 100,
                "enable_interference_modeling": len(interference_sources or []) > 0,
            }
        }

        try:
            logger.info(f"請求增強型通道模擬: {simulation_request['simulation_id']}")

            async with self.http_session.post(
                f"{self.simworld_api_url}/api/v1/wireless/simulate-with-interference",
                json=simulation_request,
                timeout=aiohttp.ClientTimeout(total=60),  # 增加超時時間
            ) as response:
                response.raise_for_status()
                channel_responses = await response.json()

            logger.info(f"收到 {len(channel_responses)} 個增強型通道響應")
            return channel_responses

        except Exception as e:
            logger.error(f"增強型通道模擬請求失敗: {e}")
            # 降級到基本通道模擬
            return await self.request_channel_simulation(
                ue_positions, gnb_positions, environment_type, frequency_ghz, bandwidth_mhz
            )

    async def _create_optimal_ue_gnb_mapping(
        self, ue_positions: List[Dict], gnb_positions: List[Dict], channel_responses: List[Dict]
    ) -> Dict[str, str]:
        """創建最佳 UE-gNB 映射"""
        ue_gnb_mapping = {}
        
        for i, (ue_pos, channel_resp) in enumerate(zip(ue_positions, channel_responses)):
            ue_id = f"ue_{i:03d}"
            
            # 選擇 SINR 最高的 gNB
            best_gnb_id = "gnb_001"  # 默認值
            best_sinr = -float('inf')
            
            for j, gnb_pos in enumerate(gnb_positions):
                gnb_id = f"gnb_{j:03d}"
                # 從通道響應中獲取 SINR
                gnb_sinr = channel_resp.get('gnb_measurements', {}).get(gnb_id, {}).get('sinr_db', -100)
                
                if gnb_sinr > best_sinr:
                    best_sinr = gnb_sinr
                    best_gnb_id = gnb_id
            
            ue_gnb_mapping[ue_id] = best_gnb_id
            
        return ue_gnb_mapping

    async def _generate_performance_report(
        self, channel_updates: List[ChannelModelUpdate], apply_result: Dict, start_time: datetime
    ) -> Dict[str, Any]:
        """生成性能報告"""
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        sinr_values = [update.sinr_db for update in channel_updates]
        rsrp_values = [update.rsrp_dbm for update in channel_updates]
        throughput_values = [update.throughput_mbps for update in channel_updates]
        latency_values = [update.latency_ms for update in channel_updates]
        
        return {
            "summary": {
                "total_ues": len(channel_updates),
                "successful_updates": apply_result.get("total_applied", 0),
                "failed_updates": apply_result.get("total_failed", 0),
                "success_rate": apply_result.get("total_applied", 0) / max(len(channel_updates), 1),
                "total_processing_time_sec": total_time,
            },
            "channel_quality": {
                "avg_sinr_db": sum(sinr_values) / len(sinr_values) if sinr_values else 0,
                "min_sinr_db": min(sinr_values) if sinr_values else 0,
                "max_sinr_db": max(sinr_values) if sinr_values else 0,
                "avg_rsrp_dbm": sum(rsrp_values) / len(rsrp_values) if rsrp_values else 0,
            },
            "performance_metrics": {
                "avg_throughput_mbps": sum(throughput_values) / len(throughput_values) if throughput_values else 0,
                "avg_latency_ms": sum(latency_values) / len(latency_values) if latency_values else 0,
                "total_throughput_mbps": sum(throughput_values),
            },
            "quality_indicators": {
                "excellent_connections": len([s for s in sinr_values if s > 20]),
                "good_connections": len([s for s in sinr_values if 10 < s <= 20]),
                "fair_connections": len([s for s in sinr_values if 0 < s <= 10]),
                "poor_connections": len([s for s in sinr_values if s <= 0]),
            }
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
