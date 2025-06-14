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
from typing import Dict, List, Optional, Tuple, Any
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
from .simworld_tle_bridge_service import SimWorldTLEBridgeService

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
        simworld_api_url: str = "http://localhost:8888",
        redis_client: Optional[redis.Redis] = None,
    ):
        self.logger = logger.bind(service="satellite_gnb_mapping")
        self.simworld_api_url = simworld_api_url
        self.redis_client = redis_client

        # 緩存配置
        self.cache_ttl = 30  # 30秒緩存
        self.cache_prefix = "sat_gnb_mapping:"
        
        # 初始化 TLE 橋接服務
        self.tle_bridge = SimWorldTLEBridgeService(
            simworld_api_url=simworld_api_url,
            redis_client=redis_client
        )

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
        """從 simworld 獲取衛星當前位置（透過 TLE 橋接服務）"""

        try:
            # 構建觀測者位置參數
            observer_location = None
            if observer_position:
                observer_location = {
                    "lat": observer_position.latitude,
                    "lon": observer_position.longitude,
                    "alt": observer_position.altitude / 1000,  # 轉為公里
                }

            # 使用 TLE 橋接服務獲取衛星位置
            satellite_id_str = str(satellite_id)
            positions = await self.tle_bridge.get_batch_satellite_positions(
                [satellite_id_str], observer_location=observer_location
            )

            position_data = positions.get(satellite_id_str)
            if position_data and position_data.get("success"):
                self.logger.debug(
                    "透過 TLE 橋接服務獲取衛星位置成功", 
                    satellite_id=satellite_id
                )
                return position_data
            else:
                error_msg = position_data.get("error", "未知錯誤") if position_data else "無資料"
                raise Exception(f"TLE 橋接服務返回錯誤: {error_msg}")

        except Exception as e:
            self.logger.error("透過 TLE 橋接服務獲取衛星位置失敗", error=str(e))
            # 如果 TLE 橋接服務不可用，使用直接 API 呼叫作為備用
            return await self._get_satellite_position_direct_api(
                satellite_id, observer_position
            )

    async def _get_satellite_position_direct_api(
        self, satellite_id: int, observer_position: Optional[UAVPosition] = None
    ) -> Dict[str, any]:
        """直接透過 SimWorld API 獲取衛星位置（備用方案）"""

        # 先檢查緩存
        if self.redis_client:
            cache_key = f"{self.cache_prefix}position_direct:{satellite_id}"
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                self.logger.debug("使用緩存的直接 API 衛星位置", satellite_id=satellite_id)
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
            self.logger.error("直接 API 獲取衛星位置失敗", error=str(e))
            # 如果直接 API 也不可用，使用本地 Skyfield 計算
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

    async def get_satellite_orbit_prediction(
        self,
        satellite_id: int,
        time_range_hours: int = 2,
        step_seconds: int = 60,
        observer_position: Optional[UAVPosition] = None,
    ) -> Dict[str, Any]:
        """
        獲取衛星軌道預測資料
        
        Args:
            satellite_id: 衛星 ID
            time_range_hours: 預測時間範圍（小時）
            step_seconds: 時間步長（秒）
            observer_position: 觀測者位置
            
        Returns:
            軌道預測資料
        """
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=time_range_hours)

        observer_location = None
        if observer_position:
            observer_location = {
                "lat": observer_position.latitude,
                "lon": observer_position.longitude,
                "alt": observer_position.altitude / 1000,
            }

        orbit_data = await self.tle_bridge.get_satellite_orbit_prediction(
            str(satellite_id), start_time, end_time, step_seconds, observer_location
        )

        self.logger.info(
            "獲取衛星軌道預測完成",
            satellite_id=satellite_id,
            prediction_points=len(orbit_data.get("positions", [])),
        )

        return orbit_data

    async def predict_handover_timing(
        self,
        ue_id: str,
        ue_position: UAVPosition,
        current_satellite: int,
        candidate_satellites: List[int],
        search_range_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        預測切換時機
        
        Args:
            ue_id: UE 識別碼
            ue_position: UE 位置
            current_satellite: 當前接入衛星
            candidate_satellites: 候選切換衛星列表
            search_range_seconds: 搜尋範圍（秒）
            
        Returns:
            切換時機預測結果
        """
        self.logger.info(
            "開始預測切換時機",
            ue_id=ue_id,
            current_satellite=current_satellite,
            candidate_count=len(candidate_satellites),
        )

        current_time = time.time()
        search_end_time = current_time + search_range_seconds

        ue_location = {
            "lat": ue_position.latitude,
            "lon": ue_position.longitude,
            "alt": ue_position.altitude / 1000,
        }

        handover_predictions = []

        for target_satellite in candidate_satellites:
            if target_satellite == current_satellite:
                continue

            try:
                # 使用二分搜尋計算精確切換時間
                handover_time = await self.tle_bridge.binary_search_handover_time(
                    ue_id=ue_id,
                    ue_position=ue_location,
                    source_satellite=str(current_satellite),
                    target_satellite=str(target_satellite),
                    t_start=current_time,
                    t_end=search_end_time,
                )

                handover_predictions.append({
                    "target_satellite": target_satellite,
                    "handover_time": datetime.fromtimestamp(handover_time).isoformat(),
                    "handover_timestamp": handover_time,
                    "time_to_handover_seconds": handover_time - current_time,
                })

            except Exception as e:
                self.logger.warning(
                    f"預測到衛星 {target_satellite} 的切換時機失敗",
                    error=str(e)
                )

        # 排序，最近的切換時間在前
        handover_predictions.sort(key=lambda x: x["handover_timestamp"])

        result = {
            "ue_id": ue_id,
            "current_satellite": current_satellite,
            "prediction_time": datetime.utcnow().isoformat(),
            "handover_predictions": handover_predictions,
            "next_handover": handover_predictions[0] if handover_predictions else None,
        }

        self.logger.info(
            "切換時機預測完成",
            ue_id=ue_id,
            predicted_handovers=len(handover_predictions),
            next_handover_seconds=result["next_handover"]["time_to_handover_seconds"] if result["next_handover"] else None,
        )

        return result

    async def sync_tle_data(self) -> Dict[str, Any]:
        """
        同步 TLE 資料
        
        Returns:
            同步結果
        """
        self.logger.info("開始同步 TLE 資料")
        
        sync_result = await self.tle_bridge.sync_tle_updates_from_simworld()
        
        if sync_result.get("success"):
            self.logger.info(
                "TLE 資料同步成功",
                synchronized_count=sync_result.get("synchronized_count"),
            )
        else:
            self.logger.error("TLE 資料同步失敗", error=sync_result.get("error"))
        
        return sync_result

    async def preload_critical_satellites(
        self, critical_satellite_ids: List[int]
    ) -> Dict[str, Any]:
        """
        預載關鍵衛星資料
        
        Args:
            critical_satellite_ids: 關鍵衛星 ID 列表
            
        Returns:
            預載結果
        """
        satellite_ids_str = [str(sid) for sid in critical_satellite_ids]
        
        preload_result = await self.tle_bridge.preload_critical_satellites(
            satellite_ids_str
        )
        
        self.logger.info(
            "關鍵衛星資料預載完成",
            preloaded_count=preload_result.get("preloaded_satellites"),
            success_count=preload_result.get("position_success_count"),
        )
        
        return preload_result

    async def get_tle_health_status(self) -> Dict[str, Any]:
        """
        獲取 TLE 資料健康狀態
        
        Returns:
            健康狀態資訊
        """
        health_status = await self.tle_bridge.get_tle_health_check()
        
        self.logger.debug(
            "TLE 健康狀態檢查",
            simworld_status=health_status.get("simworld_status"),
            success=health_status.get("success"),
        )
        
        return health_status
