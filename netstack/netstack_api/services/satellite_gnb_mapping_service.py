"""
衛星位置轉換為 gNodeB 參數服務

整合 Skyfield 軌道計算，將衛星 ECEF/ENU 坐標轉換為 UERANSIM gNodeB 配置參數
實現真實衛星軌道與 5G 網路模擬的橋接
"""

import asyncio
import math
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import structlog
import aiohttp
import redis.asyncio as redis
from fastapi import HTTPException

# 導入 Skyfield 相關模組
from skyfield.api import load, wgs84, EarthSatellite
from skyfield.timelib import Time
import numpy as np

from ..models.ueransim_models import (
    GNBConfig,
    SatellitePosition,
    UAVPosition,
    NetworkParameters,
)

logger = structlog.get_logger(__name__)

# 全域 Skyfield 時間尺度對象
try:
    ts = load.timescale(builtin=True)
except Exception as e:
    logger.error(f"無法加載 Skyfield 時間尺度: {e}")
    ts = None


class SatelliteGnbMappingService:
    """衛星位置轉換為 gNodeB 參數服務"""

    def __init__(
        self,
        simworld_api_url: str = "http://simworld-backend:8000",
        redis_client: Optional[redis.Redis] = None,
    ):
        self.logger = logger.bind(service="satellite_gnb_mapping")
        self.simworld_api_url = simworld_api_url
        self.redis_client = redis_client

        # 緩存配置
        self.cache_ttl = 30  # 30秒緩存
        self.cache_prefix = "sat_gnb_mapping:"

    async def convert_satellite_to_gnb_config(
        self,
        satellite_id: int,
        uav_position: Optional[UAVPosition] = None,
        network_params: Optional[NetworkParameters] = None,
    ) -> Dict[str, any]:
        """
        將衛星位置轉換為 gNodeB 配置參數

        Args:
            satellite_id: 衛星 ID
            uav_position: UAV 位置（用於相對計算）
            network_params: 網路參數

        Returns:
            gNodeB 配置字典，包含衛星轉換後的參數
        """
        self.logger.info("開始衛星位置轉換", satellite_id=satellite_id)

        try:
            # 1. 從 simworld 獲取衛星當前位置
            satellite_position = await self._get_satellite_position_from_simworld(
                satellite_id, uav_position
            )

            # 2. 計算 ECEF/ENU 坐標
            ecef_coords = await self._calculate_ecef_coordinates(satellite_position)

            # 3. 轉換為無線通信參數
            radio_params = self._convert_to_radio_parameters(
                satellite_position, ecef_coords, uav_position, network_params
            )

            # 4. 生成 gNodeB 配置
            gnb_config = self._generate_gnb_config(
                satellite_position, radio_params, network_params
            )

            # 5. 緩存結果
            await self._cache_mapping_result(satellite_id, gnb_config)

            self.logger.info(
                "衛星位置轉換完成",
                satellite_id=satellite_id,
                gnb_nci=gnb_config.get("nci"),
                tx_power=gnb_config.get("tx_power"),
            )

            return {
                "success": True,
                "satellite_info": satellite_position,
                "ecef_coordinates": ecef_coords,
                "radio_parameters": radio_params,
                "gnb_config": gnb_config,
                "conversion_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(
                "衛星位置轉換失敗", error=str(e), satellite_id=satellite_id
            )
            raise HTTPException(status_code=500, detail=f"衛星位置轉換失敗: {str(e)}")

    async def _get_satellite_position_from_simworld(
        self, satellite_id: int, observer_position: Optional[UAVPosition] = None
    ) -> Dict[str, any]:
        """從 simworld 獲取衛星當前位置"""

        # 先檢查緩存
        if self.redis_client:
            cache_key = f"{self.cache_prefix}position:{satellite_id}"
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                self.logger.debug("使用緩存的衛星位置", satellite_id=satellite_id)
                return json.loads(cached_result)

        try:
            # 構建 simworld API 請求
            async with aiohttp.ClientSession() as session:
                # 獲取衛星當前位置
                url = (
                    f"{self.simworld_api_url}/api/v1/satellites/{satellite_id}/position"
                )

                # 如果有觀測者位置，加入參數
                params = {}
                if observer_position:
                    params.update(
                        {
                            "observer_lat": observer_position.latitude,
                            "observer_lon": observer_position.longitude,
                            "observer_alt": observer_position.altitude
                            / 1000,  # 轉為公里
                        }
                    )

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        position_data = await response.json()

                        # 緩存結果
                        if self.redis_client:
                            await self.redis_client.setex(
                                cache_key, self.cache_ttl, json.dumps(position_data)
                            )

                        return position_data
                    else:
                        raise Exception(f"無法獲取衛星位置，HTTP {response.status}")

        except Exception as e:
            self.logger.error("從 simworld 獲取衛星位置失敗", error=str(e))
            # 如果 simworld 不可用，使用本地 Skyfield 計算
            return await self._calculate_position_locally(
                satellite_id, observer_position
            )

    async def _calculate_position_locally(
        self, satellite_id: int, observer_position: Optional[UAVPosition] = None
    ) -> Dict[str, any]:
        """使用本地 Skyfield 計算衛星位置（備用方案）"""

        if ts is None:
            raise Exception("Skyfield 時間尺度不可用")

        self.logger.warning("使用本地 Skyfield 計算衛星位置", satellite_id=satellite_id)

        # 這裡需要實現本地 TLE 數據獲取和計算
        # 暫時返回模擬數據
        current_time = datetime.utcnow()

        return {
            "satellite_id": satellite_id,
            "satellite_name": f"Satellite-{satellite_id}",
            "timestamp": current_time.isoformat(),
            "latitude": 35.6762,  # 示例位置
            "longitude": 139.6503,
            "altitude": 1200,  # 公里
            "velocity": {"speed": 7.5},  # km/s
            "elevation": 45.0 if observer_position else None,
            "azimuth": 180.0 if observer_position else None,
            "range_km": 1500.0 if observer_position else None,
            "visible": True if observer_position else None,
        }

    async def _calculate_ecef_coordinates(
        self, satellite_position: Dict
    ) -> Dict[str, float]:
        """計算衛星的 ECEF 坐標"""

        if ts is None:
            raise Exception("Skyfield 時間尺度不可用，無法計算 ECEF 坐標")

        try:
            # 使用 WGS84 轉換
            lat = satellite_position["latitude"]
            lon = satellite_position["longitude"]
            alt_km = satellite_position["altitude"]

            # 創建地理位置對象
            geo_location = wgs84.latlon(
                latitude_degrees=lat,
                longitude_degrees=lon,
                elevation_m=alt_km * 1000,  # 轉換為米
            )

            # 獲取 ECEF 坐標 (ITRS)
            x_m, y_m, z_m = geo_location.itrs_xyz.m

            return {"x": x_m, "y": y_m, "z": z_m, "coordinate_system": "ECEF-ITRS"}

        except Exception as e:
            self.logger.error("ECEF 坐標計算失敗", error=str(e))
            # 使用簡化的球面坐標轉換作為備用
            return self._simplified_ecef_conversion(satellite_position)

    def _simplified_ecef_conversion(self, satellite_position: Dict) -> Dict[str, float]:
        """簡化的 ECEF 坐標轉換（備用方案）"""

        lat_rad = math.radians(satellite_position["latitude"])
        lon_rad = math.radians(satellite_position["longitude"])
        alt_m = satellite_position["altitude"] * 1000

        # WGS84 橢球體參數
        a = 6378137.0  # 長半軸 (米)
        f = 1 / 298.257223563  # 扁率
        e2 = 2 * f - f * f  # 第一偏心率平方

        # 計算卯酉圈曲率半徑
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad) ** 2)

        # ECEF 坐標
        x = (N + alt_m) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt_m) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - e2) + alt_m) * math.sin(lat_rad)

        return {"x": x, "y": y, "z": z, "coordinate_system": "ECEF-WGS84"}

    def _convert_to_radio_parameters(
        self,
        satellite_position: Dict,
        ecef_coords: Dict,
        uav_position: Optional[UAVPosition],
        network_params: Optional[NetworkParameters],
    ) -> Dict[str, any]:
        """將座標轉換為無線通信參數"""

        radio_params = {
            "frequency_mhz": network_params.frequency if network_params else 2100,
            "bandwidth_mhz": network_params.bandwidth if network_params else 20,
        }

        if uav_position and satellite_position.get("range_km"):
            # 計算距離相關參數
            distance_km = satellite_position["range_km"]

            # 自由空間路徑損耗
            frequency_hz = radio_params["frequency_mhz"] * 1e6
            path_loss_db = (
                20 * math.log10(distance_km * 1000)
                + 20 * math.log10(frequency_hz)
                + 32.45
            )

            # 視角參數
            elevation_deg = satellite_position.get("elevation", 0)
            azimuth_deg = satellite_position.get("azimuth", 0)

            # 動態功率調整
            # 基準功率 23dBm，根據距離和仰角調整
            base_power = 23
            distance_penalty = min(
                20, distance_km / 100
            )  # 每100km增加1dB損失，最大20dB
            elevation_bonus = elevation_deg / 10  # 仰角越高信號越好

            adjusted_power = base_power - distance_penalty + elevation_bonus
            tx_power = max(10, min(30, adjusted_power))  # 限制在10-30dBm

            radio_params.update(
                {
                    "distance_km": distance_km,
                    "path_loss_db": path_loss_db,
                    "elevation_angle": elevation_deg,
                    "azimuth_angle": azimuth_deg,
                    "tx_power_dbm": tx_power,
                    "link_budget_margin": max(
                        0, tx_power - path_loss_db + 120
                    ),  # 假設接收靈敏度-120dBm
                }
            )
        else:
            # 默認參數（無 UAV 位置時）
            radio_params.update(
                {
                    "tx_power_dbm": 23,
                    "link_budget_margin": 20,
                }
            )

        # 波束覆蓋計算
        altitude_km = satellite_position["altitude"]
        beam_coverage = self._calculate_beam_coverage(altitude_km)
        radio_params.update(beam_coverage)

        return radio_params

    def _calculate_beam_coverage(self, altitude_km: float) -> Dict[str, float]:
        """計算衛星波束覆蓋範圍"""

        # 地球半徑
        earth_radius_km = 6371

        # 計算地平線距離
        horizon_distance_km = math.sqrt(
            altitude_km * (altitude_km + 2 * earth_radius_km)
        )

        # 計算最大覆蓋角度（從衛星到地平線的角度）
        max_coverage_angle = math.acos(
            earth_radius_km / (earth_radius_km + altitude_km)
        )
        max_coverage_degrees = math.degrees(max_coverage_angle)

        # 實際服務覆蓋（考慮最小仰角限制，如10度）
        min_elevation_deg = 10
        min_elevation_rad = math.radians(min_elevation_deg)

        # 服務覆蓋半徑
        service_radius_km = altitude_km * math.tan(
            max_coverage_angle - min_elevation_rad
        )

        return {
            "horizon_distance_km": horizon_distance_km,
            "max_coverage_angle_deg": max_coverage_degrees,
            "service_radius_km": service_radius_km,
            "coverage_area_km2": math.pi * service_radius_km**2,
            "min_elevation_constraint_deg": min_elevation_deg,
        }

    def _generate_gnb_config(
        self,
        satellite_position: Dict,
        radio_params: Dict,
        network_params: Optional[NetworkParameters],
    ) -> Dict[str, any]:
        """生成 gNodeB 配置"""

        # 基於衛星 ID 生成唯一的 NCI
        satellite_id = satellite_position.get("satellite_id", 1)
        nci = f"0x{satellite_id:08x}"

        # 基於位置生成 IP 地址
        lat = satellite_position["latitude"]
        lon = satellite_position["longitude"]
        ip_address = self._generate_ip_from_position(lat, lon)

        gnb_config = {
            "mcc": 999,
            "mnc": 70,
            "nci": nci,
            "id_length": 32,
            "tac": 1,
            "link_ip": ip_address,
            "ngap_ip": ip_address,
            "gtp_ip": ip_address,
            "frequency": radio_params["frequency_mhz"],
            "tx_power": int(radio_params["tx_power_dbm"]),
            "name": f"SAT-gNB-{satellite_id}",
            # 衛星特定配置
            "satellite_specific": {
                "orbit_altitude_km": satellite_position["altitude"],
                "coverage_radius_km": radio_params.get("service_radius_km", 1000),
                "beam_coverage": {
                    "max_angle_deg": radio_params.get("max_coverage_angle_deg", 60),
                    "service_area_km2": radio_params.get("coverage_area_km2", 3141592),
                },
                "link_budget": {
                    "path_loss_db": radio_params.get("path_loss_db", 0),
                    "margin_db": radio_params.get("link_budget_margin", 20),
                },
            },
            # NTN 優化參數
            "ntn_config": {
                "enabled": True,
                "propagation_delay_ms": self._calculate_propagation_delay(
                    satellite_position["altitude"]
                ),
                "doppler_compensation": True,
                "beam_tracking": True,
            },
        }

        return gnb_config

    def _generate_ip_from_position(self, latitude: float, longitude: float) -> str:
        """根據衛星位置生成 IP 地址"""
        # 將緯度經度轉換為 0-255 範圍
        lat_int = int((latitude + 90) * 255 / 180)
        lon_int = int((longitude + 180) * 255 / 360)

        # 使用 172.x.x.x 私有網段
        return f"172.{lat_int}.{lon_int}.1"

    def _calculate_propagation_delay(self, altitude_km: float) -> float:
        """計算衛星通信傳播延遲"""
        # 光速 (km/s)
        speed_of_light = 299792.458

        # 來回傳播時間 (毫秒)
        round_trip_delay_ms = (2 * altitude_km / speed_of_light) * 1000

        return round_trip_delay_ms

    async def _cache_mapping_result(self, satellite_id: int, gnb_config: Dict):
        """緩存映射結果"""
        if not self.redis_client:
            return

        try:
            cache_key = f"{self.cache_prefix}gnb_config:{satellite_id}"
            await self.redis_client.setex(
                cache_key, self.cache_ttl, json.dumps(gnb_config, default=str)
            )
        except Exception as e:
            self.logger.warning("緩存映射結果失敗", error=str(e))

    async def get_multiple_satellite_configs(
        self, satellite_ids: List[int], uav_position: Optional[UAVPosition] = None
    ) -> Dict[int, Dict]:
        """批量獲取多個衛星的 gNodeB 配置"""

        tasks = []
        for sat_id in satellite_ids:
            task = self.convert_satellite_to_gnb_config(sat_id, uav_position)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        configs = {}
        for i, result in enumerate(results):
            sat_id = satellite_ids[i]
            if isinstance(result, Exception):
                self.logger.error(f"衛星 {sat_id} 配置轉換失敗", error=str(result))
                configs[sat_id] = {"success": False, "error": str(result)}
            else:
                configs[sat_id] = result

        return configs

    async def update_gnb_positions_continuously(
        self, satellite_ids: List[int], update_interval: int = 30
    ):
        """持續更新 gNodeB 位置（事件驅動）"""

        self.logger.info(
            "開始持續更新 gNodeB 位置",
            satellite_count=len(satellite_ids),
            interval_seconds=update_interval,
        )

        while True:
            try:
                # 批量更新所有衛星配置
                updated_configs = await self.get_multiple_satellite_configs(
                    satellite_ids
                )

                # 推送配置更新事件
                for sat_id, config in updated_configs.items():
                    if config.get("success"):
                        await self._publish_gnb_update_event(sat_id, config)

                self.logger.debug(f"完成 {len(satellite_ids)} 個衛星的配置更新")

                # 等待下次更新
                await asyncio.sleep(update_interval)

            except Exception as e:
                self.logger.error("持續更新過程中發生錯誤", error=str(e))
                await asyncio.sleep(update_interval)

    async def _publish_gnb_update_event(self, satellite_id: int, config: Dict):
        """發布 gNodeB 更新事件"""
        if not self.redis_client:
            return

        try:
            event_data = {
                "event_type": "gnb_position_update",
                "satellite_id": satellite_id,
                "timestamp": datetime.utcnow().isoformat(),
                "gnb_config": config["gnb_config"],
                "radio_parameters": config["radio_parameters"],
            }

            # 發布到 Redis 頻道
            await self.redis_client.publish(
                f"netstack:gnb_updates:{satellite_id}",
                json.dumps(event_data, default=str),
            )

        except Exception as e:
            self.logger.warning("發布 gNodeB 更新事件失敗", error=str(e))
