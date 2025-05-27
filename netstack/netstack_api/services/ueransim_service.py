"""
UERANSIM動態配置生成服務

根據衛星和UAV位置信息動態生成UERANSIM配置
"""

import asyncio
import yaml
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import structlog

from ..models.ueransim_models import (
    UERANSIMConfigRequest,
    UERANSIMConfigResponse,
    ScenarioType,
    GNBConfig,
    UEConfig,
    ScenarioInfo,
    SatellitePosition,
    UAVPosition,
    NetworkParameters,
)

logger = structlog.get_logger(__name__)


class UERANSIMConfigService:
    """UERANSIM動態配置生成服務"""

    def __init__(self):
        self.logger = logger.bind(service="ueransim_config_service")

        # 配置模板
        self.gnb_template = {
            "mcc": 999,
            "mnc": 70,
            "nci": "0x000000010",
            "idLength": 32,
            "tac": 1,
            "linkIp": "172.17.0.1",
            "ngapIp": "172.17.0.1",
            "gtpIp": "172.17.0.1",
            "plmns": [
                {
                    "mcc": 999,
                    "mnc": 70,
                    "tac": 1,
                    "nssai": [
                        {"sst": 1, "sd": "0x111111"},
                        {"sst": 2, "sd": "0x222222"},
                        {"sst": 3, "sd": "0x333333"},
                    ],
                }
            ],
        }

        self.ue_template = {
            "supi": "imsi-999700000000001",
            "mcc": 999,
            "mnc": 70,
            "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
            "op": "63bfa50ee6523365ff14c1f45f88737d",
            "amf": "8000",
            "imei": "356938035643803",
            "imeisv": "4370816125816151",
            "sessions": [
                {
                    "type": "IPv4",
                    "apn": "internet",
                    "slice": {"sst": 1, "sd": "0x111111"},
                }
            ],
        }

    async def generate_config(
        self, request: UERANSIMConfigRequest
    ) -> UERANSIMConfigResponse:
        """生成UERANSIM配置"""
        try:
            self.logger.info("開始生成UERANSIM配置", scenario=request.scenario.value)

            # 根據場景類型選擇生成方法
            if request.scenario == ScenarioType.LEO_SATELLITE_PASS:
                return await self._generate_satellite_pass_config(request)
            elif request.scenario == ScenarioType.UAV_FORMATION_FLIGHT:
                return await self._generate_formation_flight_config(request)
            elif request.scenario == ScenarioType.HANDOVER_BETWEEN_SATELLITES:
                return await self._generate_handover_config(request)
            elif request.scenario == ScenarioType.POSITION_UPDATE:
                return await self._generate_position_update_config(request)
            else:
                return await self._generate_default_config(request)

        except Exception as e:
            self.logger.error("配置生成失敗", error=str(e))
            return UERANSIMConfigResponse(
                success=False,
                scenario_type=request.scenario.value,
                scenario_info=ScenarioInfo(
                    scenario_type=request.scenario.value,
                    generation_time=datetime.utcnow().isoformat(),
                ),
                message=f"配置生成失敗: {str(e)}",
            )

    async def _generate_satellite_pass_config(
        self, request: UERANSIMConfigRequest
    ) -> UERANSIMConfigResponse:
        """生成LEO衛星過境場景配置"""
        satellite = request.satellite
        uav = request.uav
        network_params = request.network_params or NetworkParameters()

        # 計算衛星-UAV之間的距離和信號參數
        distance_km = (
            self._calculate_distance(satellite, uav) if satellite and uav else 1200
        )
        signal_loss = self._calculate_path_loss(distance_km, network_params.frequency)

        # 動態調整功率和頻率
        tx_power = min(30, max(10, 23 + signal_loss - 100))  # 根據路徑損耗調整

        # 生成gNB配置（代表衛星）
        gnb_config = GNBConfig(
            mcc=999,
            mnc=70,
            nci=f"0x{satellite.id[-8:].zfill(8)}" if satellite else "0x00000010",
            frequency=network_params.frequency,
            tx_power=int(tx_power),
            link_ip=(
                self._generate_ip_from_position(satellite)
                if satellite
                else "172.17.0.1"
            ),
        )

        # 生成UE配置（代表UAV）
        ue_config = UEConfig(
            supi=(
                f"imsi-999700000{uav.id[-6:].zfill(6)}"
                if uav
                else "imsi-999700000000001"
            ),
            imei=f"35693803{uav.id[-8:].zfill(8)}" if uav else "356938035643803",
        )

        # 生成YAML配置
        config_yaml = self._generate_yaml_config(
            gnb_config, ue_config, request.scenario
        )

        return UERANSIMConfigResponse(
            success=True,
            scenario_type=request.scenario.value,
            gnb_config=gnb_config,
            ue_config=ue_config,
            scenario_info=ScenarioInfo(
                scenario_type=request.scenario.value,
                generation_time=datetime.utcnow().isoformat(),
                satellite_info=satellite.dict() if satellite else None,
                uav_info=uav.dict() if uav else None,
                network_info={
                    "distance_km": distance_km,
                    "path_loss_db": signal_loss,
                    "adjusted_tx_power": tx_power,
                },
            ),
            config_yaml=config_yaml,
            message="LEO衛星過境配置生成成功",
        )

    async def _generate_formation_flight_config(
        self, request: UERANSIMConfigRequest
    ) -> UERANSIMConfigResponse:
        """生成UAV編隊飛行場景配置"""
        satellite = request.satellite
        formation = request.uav_formation or []
        network_params = request.network_params or NetworkParameters()

        # 生成單一gNB配置（衛星）
        gnb_config = GNBConfig(
            mcc=999,
            mnc=70,
            nci=f"0x{satellite.id[-8:].zfill(8)}" if satellite else "0x00000010",
            frequency=network_params.frequency,
            link_ip=(
                self._generate_ip_from_position(satellite)
                if satellite
                else "172.17.0.1"
            ),
        )

        # 為每個UAV生成UE配置，如果沒有編隊則生成默認配置
        ue_configs = []
        if formation:
            for i, uav in enumerate(formation):
                # 根據角色調整優先級
                priority_slice = "01:111111" if uav.role == "leader" else "02:222222"

                ue_config = UEConfig(
                    supi=f"imsi-99970000{str(i+1).zfill(7)}",
                    imei=f"35693803{str(i+1).zfill(8)}",
                    initial_slice=priority_slice,
                )
                ue_configs.append(ue_config)
        else:
            # 如果沒有編隊數據，生成默認的3機編隊配置
            self.logger.warning("沒有提供UAV編隊數據，生成默認3機編隊配置")
            for i in range(3):
                ue_config = UEConfig(
                    supi=f"imsi-99970000{str(i+1).zfill(7)}",
                    imei=f"35693803{str(i+1).zfill(8)}",
                    initial_slice=(
                        "01:111111" if i == 0 else "02:222222"
                    ),  # 第一個為leader
                )
                ue_configs.append(ue_config)

        # 計算編隊中心位置
        if formation:
            center_lat = sum(uav.latitude for uav in formation) / len(formation)
            center_lon = sum(uav.longitude for uav in formation) / len(formation)
        else:
            # 默認編隊中心位置
            center_lat = 25.0
            center_lon = 121.0

        # 生成YAML配置（確保總是有配置）
        config_yaml = None
        try:
            if ue_configs:
                config_yaml = self._generate_formation_yaml_config(
                    gnb_config, ue_configs, request.scenario
                )
                self.logger.info(
                    "UAV編隊YAML配置生成成功",
                    formation_size=len(ue_configs),
                    config_length=len(config_yaml) if config_yaml else 0,
                )
            else:
                self.logger.error("無法生成UE配置，編隊數據無效")
        except Exception as e:
            self.logger.error("UAV編隊YAML配置生成失敗", error=str(e))
            # 生成備用配置
            config_yaml = self._generate_fallback_formation_config(
                gnb_config, request.scenario
            )

        return UERANSIMConfigResponse(
            success=True,
            scenario_type=request.scenario.value,
            gnb_config=gnb_config,
            ue_configs=ue_configs,
            config_yaml=config_yaml,
            scenario_info=ScenarioInfo(
                scenario_type=request.scenario.value,
                generation_time=datetime.utcnow().isoformat(),
                satellite_info=satellite.dict() if satellite else None,
                uav_info={
                    "formation_size": len(ue_configs),
                    "center_position": {"lat": center_lat, "lon": center_lon},
                    "coordination_required": network_params.coordination_required,
                    "is_default_formation": not bool(formation),
                },
            ),
            message=f"UAV編隊配置生成成功，包含{len(ue_configs)}個UE{'（默認配置）' if not formation else ''}",
        )

    async def _generate_handover_config(
        self, request: UERANSIMConfigRequest
    ) -> UERANSIMConfigResponse:
        """生成衛星間切換場景配置"""
        source_sat = request.source_satellite
        target_sat = request.target_satellite
        uav = request.uav
        handover_params = request.handover_params

        # 生成兩個gNB配置
        gnb_configs = []

        if source_sat:
            source_gnb = GNBConfig(
                mcc=999,
                mnc=70,
                nci=f"0x{source_sat.id[-8:].zfill(8)}",
                link_ip=self._generate_ip_from_position(source_sat),
                tx_power=15,  # 較低功率表示信號衰弱
            )
            gnb_configs.append(source_gnb)

        if target_sat:
            target_gnb = GNBConfig(
                mcc=999,
                mnc=70,
                nci=f"0x{target_sat.id[-8:].zfill(8)}",
                link_ip=self._generate_ip_from_position(target_sat),
                tx_power=25,  # 較高功率表示更好信號
            )
            gnb_configs.append(target_gnb)

        # 生成UE配置
        ue_config = UEConfig(
            supi=(
                f"imsi-999700000{uav.id[-6:].zfill(6)}"
                if uav
                else "imsi-999700000000001"
            ),
            imei=f"35693803{uav.id[-8:].zfill(8)}" if uav else "356938035643803",
        )

        # 生成YAML配置（使用第一個gNB作為主配置）
        config_yaml = None
        if gnb_configs:
            try:
                config_yaml = self._generate_handover_yaml_config(
                    gnb_configs, ue_config, request.scenario
                )
                self.logger.info(
                    "切換場景YAML配置生成成功",
                    config_length=len(config_yaml) if config_yaml else 0,
                )
            except Exception as e:
                self.logger.error("切換場景YAML配置生成失敗", error=str(e))
                config_yaml = None

        return UERANSIMConfigResponse(
            success=True,
            scenario_type=request.scenario.value,
            gnb_configs=gnb_configs,
            ue_config=ue_config,
            config_yaml=config_yaml,
            scenario_info=ScenarioInfo(
                scenario_type=request.scenario.value,
                generation_time=datetime.utcnow().isoformat(),
                satellite_info={
                    "source": source_sat.dict() if source_sat else None,
                    "target": target_sat.dict() if target_sat else None,
                },
                uav_info=uav.dict() if uav else None,
                network_info={
                    "handover_threshold": (
                        handover_params.trigger_threshold if handover_params else -90
                    ),
                    "hysteresis": handover_params.hysteresis if handover_params else 3,
                },
            ),
            message="衛星切換配置生成成功",
        )

    async def _generate_position_update_config(
        self, request: UERANSIMConfigRequest
    ) -> UERANSIMConfigResponse:
        """生成位置更新場景配置"""
        return await self._generate_satellite_pass_config(request)

    async def _generate_default_config(
        self, request: UERANSIMConfigRequest
    ) -> UERANSIMConfigResponse:
        """生成默認配置"""
        gnb_config = GNBConfig()
        ue_config = UEConfig(supi="imsi-999700000000001")

        return UERANSIMConfigResponse(
            success=True,
            scenario_type=request.scenario.value,
            gnb_config=gnb_config,
            ue_config=ue_config,
            scenario_info=ScenarioInfo(
                scenario_type=request.scenario.value,
                generation_time=datetime.utcnow().isoformat(),
            ),
            message="默認配置生成成功",
        )

    def _calculate_distance(
        self, satellite: SatellitePosition, uav: UAVPosition
    ) -> float:
        """計算衛星和UAV之間的距離（公里）"""
        # 簡化的3D距離計算
        lat_diff = math.radians(satellite.latitude - uav.latitude)
        lon_diff = math.radians(satellite.longitude - uav.longitude)
        alt_diff = satellite.altitude - (uav.altitude / 1000)  # 轉換為公里

        # 地面距離
        earth_radius = 6371  # 地球半徑（公里）
        surface_dist = earth_radius * math.sqrt(lat_diff**2 + lon_diff**2)

        # 3D距離
        distance = math.sqrt(surface_dist**2 + alt_diff**2)
        return distance

    def _calculate_path_loss(self, distance_km: float, frequency_mhz: int) -> float:
        """計算路徑損耗（dB）"""
        # 自由空間路徑損耗公式
        if distance_km <= 0:
            return 0

        path_loss = (
            20 * math.log10(distance_km * 1000) + 20 * math.log10(frequency_mhz) + 32.45
        )
        return path_loss

    def _generate_ip_from_position(self, position: SatellitePosition) -> str:
        """根據衛星位置生成IP地址"""
        # 將緯度經度轉換為IP地址的簡化方法
        lat_int = int((position.latitude + 90) * 255 / 180)
        lon_int = int((position.longitude + 180) * 255 / 360)
        return f"172.{lat_int}.{lon_int}.1"

    def _generate_yaml_config(
        self, gnb_config: GNBConfig, ue_config: UEConfig, scenario: ScenarioType
    ) -> str:
        """生成YAML格式的配置"""
        config_dict = {
            "scenario": scenario.value,
            "generation_time": datetime.utcnow().isoformat(),
            "gnb": {
                "mcc": gnb_config.mcc,
                "mnc": gnb_config.mnc,
                "nci": gnb_config.nci,
                "idLength": gnb_config.id_length,
                "tac": gnb_config.tac,
                "linkIp": gnb_config.link_ip,
                "ngapIp": gnb_config.ngap_ip,
                "gtpIp": gnb_config.gtp_ip,
                "frequency": gnb_config.frequency,
                "txPower": gnb_config.tx_power,
                "plmns": [
                    {
                        "mcc": gnb_config.mcc,
                        "mnc": gnb_config.mnc,
                        "tac": gnb_config.tac,
                        "nssai": [
                            {"sst": 1, "sd": "0x111111"},
                            {"sst": 2, "sd": "0x222222"},
                            {"sst": 3, "sd": "0x333333"},
                        ],
                    }
                ],
            },
            "ue": {
                "supi": ue_config.supi,
                "mcc": ue_config.mcc,
                "mnc": ue_config.mnc,
                "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                "op": ue_config.op,
                "amf": ue_config.amf,
                "imei": ue_config.imei,
                "imeisv": "4370816125816151",
                "sessions": [
                    {
                        "type": "IPv4",
                        "apn": "internet",
                        "slice": {"sst": 1, "sd": "0x111111"},
                    }
                ],
            },
        }

        return yaml.dump(config_dict, default_flow_style=False, allow_unicode=True)

    def _generate_handover_yaml_config(
        self, gnb_configs: List[GNBConfig], ue_config: UEConfig, scenario: ScenarioType
    ) -> str:
        """生成切換場景的YAML格式配置"""
        config_dict = {
            "scenario": scenario.value,
            "generation_time": datetime.utcnow().isoformat(),
            "handover_config": {
                "source_gnb": (
                    {
                        "mcc": gnb_configs[0].mcc,
                        "mnc": gnb_configs[0].mnc,
                        "nci": gnb_configs[0].nci,
                        "idLength": gnb_configs[0].id_length,
                        "tac": gnb_configs[0].tac,
                        "linkIp": gnb_configs[0].link_ip,
                        "ngapIp": gnb_configs[0].ngap_ip,
                        "gtpIp": gnb_configs[0].gtp_ip,
                        "frequency": gnb_configs[0].frequency,
                        "txPower": gnb_configs[0].tx_power,
                    }
                    if len(gnb_configs) > 0
                    else None
                ),
                "target_gnb": (
                    {
                        "mcc": gnb_configs[1].mcc,
                        "mnc": gnb_configs[1].mnc,
                        "nci": gnb_configs[1].nci,
                        "idLength": gnb_configs[1].id_length,
                        "tac": gnb_configs[1].tac,
                        "linkIp": gnb_configs[1].link_ip,
                        "ngapIp": gnb_configs[1].ngap_ip,
                        "gtpIp": gnb_configs[1].gtp_ip,
                        "frequency": gnb_configs[1].frequency,
                        "txPower": gnb_configs[1].tx_power,
                    }
                    if len(gnb_configs) > 1
                    else None
                ),
            },
            "ue": {
                "supi": ue_config.supi,
                "mcc": ue_config.mcc,
                "mnc": ue_config.mnc,
                "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                "op": ue_config.op,
                "amf": ue_config.amf,
                "imei": ue_config.imei,
                "imeisv": "4370816125816151",
                "sessions": [
                    {
                        "type": "IPv4",
                        "apn": "internet",
                        "slice": {"sst": 1, "sd": "0x111111"},
                    }
                ],
            },
        }

        return yaml.dump(config_dict, default_flow_style=False, allow_unicode=True)

    def _generate_formation_yaml_config(
        self, gnb_config: GNBConfig, ue_configs: List[UEConfig], scenario: ScenarioType
    ) -> str:
        """生成編隊場景的YAML格式配置"""
        config_dict = {
            "scenario": scenario.value,
            "generation_time": datetime.utcnow().isoformat(),
            "gnb": {
                "mcc": gnb_config.mcc,
                "mnc": gnb_config.mnc,
                "nci": gnb_config.nci,
                "idLength": gnb_config.id_length,
                "tac": gnb_config.tac,
                "linkIp": gnb_config.link_ip,
                "ngapIp": gnb_config.ngap_ip,
                "gtpIp": gnb_config.gtp_ip,
                "frequency": gnb_config.frequency,
                "txPower": gnb_config.tx_power,
            },
            "formation": {
                "size": len(ue_configs),
                "ues": [
                    {
                        "supi": ue.supi,
                        "mcc": ue.mcc,
                        "mnc": ue.mnc,
                        "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                        "op": ue.op,
                        "amf": ue.amf,
                        "imei": ue.imei,
                        "initial_slice": ue.initial_slice,
                    }
                    for ue in ue_configs
                ],
            },
        }

        return yaml.dump(config_dict, default_flow_style=False, allow_unicode=True)

    def _generate_fallback_formation_config(
        self, gnb_config: GNBConfig, scenario: ScenarioType
    ) -> str:
        """生成備用編隊配置"""
        fallback_config = {
            "scenario": scenario.value,
            "generation_time": datetime.utcnow().isoformat(),
            "warning": "This is a fallback configuration due to missing UAV formation data",
            "gnb": {
                "mcc": gnb_config.mcc,
                "mnc": gnb_config.mnc,
                "nci": gnb_config.nci,
                "idLength": gnb_config.id_length,
                "tac": gnb_config.tac,
                "linkIp": gnb_config.link_ip,
                "ngapIp": gnb_config.ngap_ip,
                "gtpIp": gnb_config.gtp_ip,
                "frequency": gnb_config.frequency,
                "txPower": gnb_config.tx_power,
            },
            "formation": {
                "size": 3,
                "type": "default_triangle",
                "ues": [
                    {
                        "supi": "imsi-999700000000001",
                        "role": "leader",
                        "mcc": 999,
                        "mnc": 70,
                        "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                        "op": "E8ED289DEBA952E4283B54E88E6183CA",
                        "amf": "8000",
                        "imei": "356938035643801",
                        "initial_slice": "01:111111",
                    },
                    {
                        "supi": "imsi-999700000000002",
                        "role": "follower",
                        "mcc": 999,
                        "mnc": 70,
                        "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                        "op": "E8ED289DEBA952E4283B54E88E6183CA",
                        "amf": "8000",
                        "imei": "356938035643802",
                        "initial_slice": "02:222222",
                    },
                    {
                        "supi": "imsi-999700000000003",
                        "role": "follower",
                        "mcc": 999,
                        "mnc": 70,
                        "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                        "op": "E8ED289DEBA952E4283B54E88E6183CA",
                        "amf": "8000",
                        "imei": "356938035643803",
                        "initial_slice": "02:222222",
                    },
                ],
            },
        }

        return yaml.dump(fallback_config, default_flow_style=False, allow_unicode=True)

    async def get_available_templates(self) -> List[Dict]:
        """獲取可用的配置模板"""
        templates = [
            {
                "template_name": "leo_satellite_basic",
                "scenario_type": ScenarioType.LEO_SATELLITE_PASS.value,
                "description": "基本LEO衛星過境場景",
                "parameters": [
                    "satellite_position",
                    "uav_position",
                    "frequency",
                    "tx_power",
                ],
            },
            {
                "template_name": "uav_formation_3units",
                "scenario_type": ScenarioType.UAV_FORMATION_FLIGHT.value,
                "description": "3機編隊飛行場景",
                "parameters": [
                    "formation_positions",
                    "coordination_mode",
                    "priority_levels",
                ],
            },
            {
                "template_name": "satellite_handover",
                "scenario_type": ScenarioType.HANDOVER_BETWEEN_SATELLITES.value,
                "description": "衛星間切換場景",
                "parameters": [
                    "source_satellite",
                    "target_satellite",
                    "handover_thresholds",
                ],
            },
        ]

        return templates
