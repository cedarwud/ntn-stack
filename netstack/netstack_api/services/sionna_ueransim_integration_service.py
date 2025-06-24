"""
Sionna 無線通道模型與 UERANSIM 整合服務

實現 TODO.md 第6項：Sionna 無線通道模型與 UERANSIM 整合
將 Sionna 的無線通道模擬結果應用於 UERANSIM，實現更真實的 5G 無線環境模擬
"""

import asyncio
import aiohttp
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import structlog
import numpy as np

from ..models.sionna_models import (
    SionnaChannelRequest,
    SionnaChannelResponse,
    ChannelCharacteristics,
    PathLossParams,
    SINRParameters,
)
from ..adapters.redis_adapter import RedisAdapter

logger = structlog.get_logger(__name__)


class SionnaUERANSIMIntegrationService:
    """Sionna 與 UERANSIM 整合服務"""

    def __init__(
        self,
        redis_adapter: RedisAdapter,
        simworld_api_url: str = "http://simworld-backend:8000",
        ueransim_config_dir: str = "/tmp/ueransim_configs",
        update_interval_sec: float = 5.0,
    ):
        self.logger = logger.bind(service="sionna_ueransim_integration")
        self.redis_adapter = redis_adapter
        self.simworld_api_url = simworld_api_url
        self.ueransim_config_dir = Path(ueransim_config_dir)
        self.update_interval_sec = update_interval_sec

        # 確保配置目錄存在
        self.ueransim_config_dir.mkdir(parents=True, exist_ok=True)

        # 通道模型緩存
        self.channel_cache = {}
        self.integration_tasks = {}

        # UERANSIM 參數映射配置
        self.parameter_mapping = {
            "path_loss_to_rsrp": self._map_path_loss_to_rsrp,
            "sinr_to_cqi": self._map_sinr_to_cqi,
            "delay_spread_to_timing": self._map_delay_spread_to_timing,
            "doppler_to_frequency_offset": self._map_doppler_to_frequency_offset,
        }

    async def start_channel_integration(
        self,
        scenario_id: str,
        ue_positions: List[Dict],
        gnb_positions: List[Dict],
        environment_params: Dict,
    ) -> Dict:
        """啟動通道整合服務"""
        try:
            integration_config = {
                "scenario_id": scenario_id,
                "ue_positions": ue_positions,
                "gnb_positions": gnb_positions,
                "environment_params": environment_params,
                "start_time": datetime.utcnow().isoformat(),
                "status": "running",
            }

            # 儲存配置到 Redis
            try:
                if self.redis_adapter.client:
                    await self.redis_adapter.client.setex(
                        f"sionna_integration:{scenario_id}",
                        3600,
                        json.dumps(integration_config, default=str)
                    )
            except Exception as e:
                self.logger.warning("Redis 儲存失敗", error=str(e))

            # 啟動背景任務
            task = asyncio.create_task(
                self._integration_worker(scenario_id, integration_config)
            )
            self.integration_tasks[scenario_id] = task

            self.logger.info(
                "Sionna-UERANSIM 整合已啟動",
                scenario_id=scenario_id,
                ue_count=len(ue_positions),
                gnb_count=len(gnb_positions),
            )

            return {
                "success": True,
                "scenario_id": scenario_id,
                "integration_status": "started",
                "message": "通道整合服務已啟動",
            }

        except Exception as e:
            self.logger.error("啟動通道整合失敗", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "啟動通道整合服務失敗",
            }

    async def _integration_worker(self, scenario_id: str, config: Dict):
        """整合工作器 - 持續同步通道模型與 UERANSIM 配置"""
        try:
            while scenario_id in self.integration_tasks:
                # 1. 獲取最新的 Sionna 通道模擬結果
                channel_data = await self._fetch_sionna_channel_data(config)

                if channel_data:
                    # 2. 轉換為 UERANSIM 參數
                    ueransim_params = await self._convert_channel_to_ueransim(
                        channel_data, config
                    )

                    # 3. 更新 UERANSIM 配置
                    await self._update_ueransim_configs(scenario_id, ueransim_params)

                    # 4. 快取結果
                    self.channel_cache[scenario_id] = {
                        "channel_data": channel_data,
                        "ueransim_params": ueransim_params,
                        "update_time": datetime.utcnow().isoformat(),
                    }

                await asyncio.sleep(self.update_interval_sec)

        except asyncio.CancelledError:
            self.logger.info("整合工作器被取消", scenario_id=scenario_id)
        except Exception as e:
            self.logger.error("整合工作器異常", scenario_id=scenario_id, error=str(e))

    async def _fetch_sionna_channel_data(self, config: Dict) -> Optional[Dict]:
        """從 SimWorld 獲取 Sionna 通道模擬數據"""
        try:
            # 準備 Sionna 請求
            sionna_request = {
                "simulation_params": {
                    "ue_positions": config["ue_positions"],
                    "gnb_positions": config["gnb_positions"],
                    "frequency_hz": config["environment_params"].get(
                        "frequency_hz", 2.1e9
                    ),
                    "bandwidth_hz": config["environment_params"].get(
                        "bandwidth_hz", 20e6
                    ),
                    "scenario": config["environment_params"].get(
                        "scenario", "ntn_rural"
                    ),
                    "enable_ray_tracing": True,
                    "enable_multipath": True,
                    "enable_doppler": True,
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.simworld_api_url}/api/v1/wireless/satellite-ntn-simulation",
                    json=sionna_request,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            return data["simulation_result"]

                    self.logger.warning(
                        "Sionna 通道模擬請求失敗",
                        status=response.status,
                        url=response.url,
                    )
                    return None

        except Exception as e:
            self.logger.error("獲取 Sionna 通道數據失敗", error=str(e))
            return None

    async def _convert_channel_to_ueransim(
        self, channel_data: Dict, config: Dict
    ) -> Dict:
        """將 Sionna 通道特性轉換為 UERANSIM 參數"""
        ueransim_params = {"gnbs": {}, "ues": {}, "global_params": {}}

        try:
            # 處理路徑損耗數據
            if "path_loss_db" in channel_data:
                path_loss_matrix = np.array(channel_data["path_loss_db"])

                # 轉換為 RSRP 值
                for gnb_idx, gnb_pos in enumerate(config["gnb_positions"]):
                    gnb_id = gnb_pos.get("id", f"gnb_{gnb_idx}")

                    ueransim_params["gnbs"][gnb_id] = {
                        "position": gnb_pos.get("position", [0, 0, 30]),
                        "tx_power": self._calculate_optimal_tx_power(
                            path_loss_matrix[gnb_idx]
                            if gnb_idx < len(path_loss_matrix)
                            else []
                        ),
                        "antenna_pattern": self._generate_antenna_pattern(
                            channel_data.get("angular_spread", {})
                        ),
                    }

                # 轉換 UE 參數
                for ue_idx, ue_pos in enumerate(config["ue_positions"]):
                    ue_id = ue_pos.get("id", f"ue_{ue_idx}")

                    # 計算最佳服務 gNB
                    best_gnb = self._find_best_serving_gnb(
                        ue_idx, path_loss_matrix, config["gnb_positions"]
                    )

                    ueransim_params["ues"][ue_id] = {
                        "position": ue_pos.get("position", [0, 0, 1.5]),
                        "serving_gnb": best_gnb,
                        "rsrp_dbm": self._map_path_loss_to_rsrp(
                            path_loss_matrix[0][ue_idx]
                            if len(path_loss_matrix) > 0
                            and ue_idx < len(path_loss_matrix[0])
                            else 100
                        ),
                        "sinr_db": (
                            channel_data.get("sinr_db", [15.0])[ue_idx]
                            if ue_idx < len(channel_data.get("sinr_db", []))
                            else 15.0
                        ),
                        "cqi": self._map_sinr_to_cqi(
                            channel_data.get("sinr_db", [15.0])[ue_idx]
                            if ue_idx < len(channel_data.get("sinr_db", []))
                            else 15.0
                        ),
                    }

            # 處理多普勒效應
            if "doppler_shifts_hz" in channel_data:
                doppler_data = channel_data["doppler_shifts_hz"]
                ueransim_params["global_params"]["doppler_compensation"] = {
                    "enabled": True,
                    "max_shift_hz": (
                        max(abs(d) for d in doppler_data) if doppler_data else 0
                    ),
                    "compensation_method": "phase_locked_loop",
                }

            # 處理延遲擴散
            if "delay_spread_ns" in channel_data:
                delay_spread = channel_data["delay_spread_ns"]
                ueransim_params["global_params"]["timing_advance"] = {
                    "enabled": True,
                    "max_delay_ns": max(delay_spread) if delay_spread else 0,
                    "equalization": "mmse",
                }

            self.logger.info(
                "通道參數轉換完成",
                gnb_count=len(ueransim_params["gnbs"]),
                ue_count=len(ueransim_params["ues"]),
            )

            return ueransim_params

        except Exception as e:
            self.logger.error("通道參數轉換失敗", error=str(e))
            return {}

    async def _update_ueransim_configs(self, scenario_id: str, params: Dict):
        """更新 UERANSIM 配置文件"""
        try:
            # 更新 gNB 配置
            for gnb_id, gnb_params in params.get("gnbs", {}).items():
                await self._generate_gnb_config(scenario_id, gnb_id, gnb_params)

            # 更新 UE 配置
            for ue_id, ue_params in params.get("ues", {}).items():
                await self._generate_ue_config(scenario_id, ue_id, ue_params)

            # 儲存整合狀態
            integration_status = {
                "scenario_id": scenario_id,
                "last_update": datetime.utcnow().isoformat(),
                "gnb_count": len(params.get("gnbs", {})),
                "ue_count": len(params.get("ues", {})),
                "global_params": params.get("global_params", {}),
            }

            try:
                if self.redis_adapter.client:
                    await self.redis_adapter.client.setex(
                        f"sionna_ueransim_status:{scenario_id}",
                        3600,
                        json.dumps(integration_status, default=str)
                    )
            except Exception as e:
                self.logger.warning("Redis 狀態儲存失敗", error=str(e))

            self.logger.info(
                "UERANSIM 配置更新完成",
                scenario_id=scenario_id,
                gnb_count=len(params.get("gnbs", {})),
                ue_count=len(params.get("ues", {})),
            )

        except Exception as e:
            self.logger.error("更新 UERANSIM 配置失敗", error=str(e))

    async def _generate_gnb_config(
        self, scenario_id: str, gnb_id: str, gnb_params: Dict
    ):
        """生成 gNB 配置文件"""
        config_content = f"""# gNB Configuration for {gnb_id}
# Generated by Sionna-UERANSIM Integration
# Scenario: {scenario_id}
# Generated at: {datetime.utcnow().isoformat()}

info: [Sionna-Enhanced gNB {gnb_id}]

mcc: 999
mnc: 70
nci: 0x000000010
idLength: 32
tac: 1

# Network interfaces
linkIp: 172.20.0.40
ngapIp: 172.20.0.40
gtpIp: 172.20.0.40

# PLMNs
plmns:
  - mcc: 999
    mnc: 70
    tac: 1
    nssai:
      - sst: 1
        sd: 0x111111
      - sst: 2
        sd: 0x222222
      - sst: 3
        sd: 0x333333

# Radio parameters (from Sionna simulation)
position: {gnb_params.get('position', [0, 0, 30])}
txPower: {gnb_params.get('tx_power', 23)}

# Antenna configuration
antenna:
  pattern: {gnb_params.get('antenna_pattern', 'omni')}
  
# NTN specific parameters
ntn:
  enabled: true
  doppler_compensation: {gnb_params.get('doppler_compensation', True)}
  beam_tracking: true
"""

        config_file = self.ueransim_config_dir / f"gnb_{scenario_id}_{gnb_id}.yaml"
        config_file.write_text(config_content)

    async def _generate_ue_config(self, scenario_id: str, ue_id: str, ue_params: Dict):
        """生成 UE 配置文件"""
        config_content = f"""# UE Configuration for {ue_id}
# Generated by Sionna-UERANSIM Integration
# Scenario: {scenario_id}
# Generated at: {datetime.utcnow().isoformat()}

info: [Sionna-Enhanced UE {ue_id}]

# UE identity
supi: imsi-999700000000{str(hash(ue_id))[-6:]}
mcc: 999
mnc: 70

# Security
key: 465B5CE8B199B49FAA5F0A2EE238A6BC
op: c9e8763286b5b9ffbdf56e1297d0887b
opc: 63BFA50EE6523365FF14C1F45F88737D
amf: 8000

# Default NSSAI
nssai:
  - sst: 1
    sd: 0x111111

# Sessions
sessions:
  - type: IPv4
    apn: internet
    slice:
      sst: 1
      sd: 0x111111

# Position and radio parameters (from Sionna)
position: {ue_params.get('position', [0, 0, 1.5])}

# Radio quality indicators (from Sionna simulation)
rf_params:
  rsrp_dbm: {ue_params.get('rsrp_dbm', -80)}
  sinr_db: {ue_params.get('sinr_db', 15)}
  cqi: {ue_params.get('cqi', 12)}
  serving_gnb: {ue_params.get('serving_gnb', 'gnb_0')}

# gNB search list
gnbSearchList:
  - 172.20.0.40
"""

        config_file = self.ueransim_config_dir / f"ue_{scenario_id}_{ue_id}.yaml"
        config_file.write_text(config_content)

    # 參數映射函數
    def _map_path_loss_to_rsrp(self, path_loss_db: float) -> float:
        """將路徑損耗轉換為 RSRP"""
        # 假設 gNB 發射功率為 23 dBm
        tx_power_dbm = 23
        rsrp_dbm = tx_power_dbm - path_loss_db
        # 限制在合理範圍內
        return max(-140, min(-44, rsrp_dbm))

    def _map_sinr_to_cqi(self, sinr_db: float) -> int:
        """將 SINR 轉換為 CQI 值"""
        # CQI 映射表（簡化版）
        if sinr_db >= 22:
            return 15
        elif sinr_db >= 19:
            return 14
        elif sinr_db >= 16:
            return 13
        elif sinr_db >= 13:
            return 12
        elif sinr_db >= 10:
            return 11
        elif sinr_db >= 7:
            return 10
        elif sinr_db >= 4:
            return 9
        elif sinr_db >= 1:
            return 8
        elif sinr_db >= -2:
            return 7
        elif sinr_db >= -5:
            return 6
        elif sinr_db >= -8:
            return 5
        elif sinr_db >= -11:
            return 4
        elif sinr_db >= -14:
            return 3
        elif sinr_db >= -17:
            return 2
        else:
            return 1

    def _map_delay_spread_to_timing(self, delay_spread_ns: float) -> Dict:
        """將延遲擴散轉換為時序參數"""
        return {
            "timing_advance_enabled": delay_spread_ns > 100,  # 100ns 閾值
            "equalization_mode": "mmse" if delay_spread_ns > 500 else "zf",
            "max_delay_ns": delay_spread_ns,
        }

    def _map_doppler_to_frequency_offset(self, doppler_hz: float) -> Dict:
        """將多普勒頻移轉換為頻率偏移參數"""
        return {
            "frequency_offset_hz": doppler_hz,
            "compensation_enabled": abs(doppler_hz) > 10,  # 10Hz 閾值
            "tracking_bandwidth_hz": min(1000, abs(doppler_hz) * 2),
        }

    def _calculate_optimal_tx_power(self, path_losses: List[float]) -> float:
        """計算最佳發射功率"""
        if not path_losses:
            return 23.0  # 預設值

        # 基於最大路徑損耗調整功率
        max_path_loss = max(path_losses)
        optimal_power = 23 + (max_path_loss - 120) * 0.5  # 動態調整
        return max(10, min(30, optimal_power))  # 限制在 10-30 dBm

    def _generate_antenna_pattern(self, angular_spread: Dict) -> str:
        """根據角度擴散生成天線方向圖"""
        if not angular_spread:
            return "omni"

        azimuth_spread = angular_spread.get("azimuth_deg", 360)
        elevation_spread = angular_spread.get("elevation_deg", 180)

        if azimuth_spread < 60 and elevation_spread < 30:
            return "directional"
        elif azimuth_spread < 120:
            return "sector"
        else:
            return "omni"

    def _find_best_serving_gnb(
        self, ue_idx: int, path_loss_matrix: np.ndarray, gnb_positions: List[Dict]
    ) -> str:
        """找到最佳服務 gNB"""
        if len(path_loss_matrix) == 0 or ue_idx >= path_loss_matrix.shape[1]:
            return gnb_positions[0].get("id", "gnb_0") if gnb_positions else "gnb_0"

        # 選擇路徑損耗最小的 gNB
        best_gnb_idx = np.argmin(path_loss_matrix[:, ue_idx])
        return gnb_positions[best_gnb_idx].get("id", f"gnb_{best_gnb_idx}")

    async def stop_integration(self, scenario_id: str) -> Dict:
        """停止整合服務"""
        try:
            if scenario_id in self.integration_tasks:
                task = self.integration_tasks[scenario_id]
                task.cancel()
                del self.integration_tasks[scenario_id]

                # 清理 Redis 數據
                await self.redis_adapter.delete(f"sionna_integration:{scenario_id}")
                await self.redis_adapter.delete(f"sionna_ueransim_status:{scenario_id}")

                self.logger.info("整合服務已停止", scenario_id=scenario_id)

            return {
                "success": True,
                "scenario_id": scenario_id,
                "message": "整合服務已停止",
            }

        except Exception as e:
            self.logger.error("停止整合服務失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_integration_status(self, scenario_id: str) -> Dict:
        """獲取整合狀態"""
        try:
            status_data = await self.redis_adapter.get(
                f"sionna_ueransim_status:{scenario_id}"
            )
            if status_data:
                status = json.loads(status_data)
                status["is_running"] = scenario_id in self.integration_tasks
                return {"success": True, "status": status}
            else:
                return {"success": False, "message": "找不到整合狀態數據"}

        except Exception as e:
            self.logger.error("獲取整合狀態失敗", error=str(e))
            return {"success": False, "error": str(e)}
