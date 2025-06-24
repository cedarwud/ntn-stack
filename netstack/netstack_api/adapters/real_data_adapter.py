"""
真實數據適配器

用於整合 NetStack 和 SimWorld API，提供真實的衛星和 UE 數據
"""

import asyncio
import httpx
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import structlog
import math
import random

from .open5gs_adapter import Open5GSAdapter

logger = structlog.get_logger(__name__)


class RealDataAdapter:
    """真實數據適配器，整合多個數據源"""

    def __init__(
        self,
        netstack_api_url: str = "http://localhost:8080",
        simworld_api_url: str = "http://localhost:8888",
        fallback_to_mock: bool = True,
        timeout: float = 5.0,
    ):
        """
        初始化真實數據適配器

        Args:
            netstack_api_url: NetStack API URL
            simworld_api_url: SimWorld API URL
            fallback_to_mock: 當 API 無法訪問時是否回退到模擬數據
            timeout: API 請求超時時間
        """
        self.netstack_api_url = netstack_api_url
        self.simworld_api_url = simworld_api_url
        self.fallback_to_mock = fallback_to_mock
        self.timeout = timeout
        self.open5gs_adapter = Open5GSAdapter(mongo_host="localhost", mongo_port=27017)

        # 緩存最後的數據以便離線使用
        self._last_satellite_data = None
        self._last_ue_data = None
        self._last_network_data = None

    async def health_check(self) -> Dict[str, Any]:
        """檢查所有數據源的健康狀態"""
        status = {
            "netstack_api": "unknown",
            "simworld_api": "unknown",
            "open5gs": "unknown",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 檢查 NetStack API
            try:
                response = await client.get(f"{self.netstack_api_url}/health")
                status["netstack_api"] = (
                    "healthy" if response.status_code == 200 else "unhealthy"
                )
            except Exception as e:
                status["netstack_api"] = f"error: {str(e)}"

            # 檢查 SimWorld API
            try:
                response = await client.get(f"{self.simworld_api_url}/health")
                status["simworld_api"] = (
                    "healthy" if response.status_code == 200 else "unhealthy"
                )
            except Exception as e:
                status["simworld_api"] = f"error: {str(e)}"

        # 檢查 Open5GS
        try:
            open5gs_status = await self.open5gs_adapter.health_check()
            status["open5gs"] = open5gs_status["status"]
        except Exception as e:
            status["open5gs"] = f"error: {str(e)}"

        return status

    async def get_complete_real_data(self) -> Dict[str, Any]:
        """獲取完整的真實數據"""
        satellites_real = False
        ues_real = False
        network_real = False

        try:
            satellites = await self.get_real_satellite_data()
            satellites_real = not satellites.get("_is_mock", False)
        except Exception:
            satellites = self._generate_mock_satellite_data()
            satellites["_is_mock"] = True

        try:
            ues = await self.get_real_ue_data()
            ues_real = not ues.get("_is_mock", False)
        except Exception:
            ues = self._generate_mock_ue_data()
            ues["_is_mock"] = True

        try:
            network_env = await self.get_real_network_environment()
            network_real = not network_env.get("_is_mock", False)
        except Exception:
            network_env = self._generate_mock_network_data()
            network_env["_is_mock"] = True

        # 確定數據來源
        real_data_count = sum([satellites_real, ues_real, network_real])
        if real_data_count == 3:
            data_source = "real_api"
        elif real_data_count > 0:
            data_source = "partial_real"
        else:
            data_source = "mock_fallback"

        logger.info(
            f"數據來源統計: 衛星={satellites_real}, UE={ues_real}, 網路={network_real}"
        )

        return {
            "satellites": satellites,
            "ues": ues,
            "network_environment": network_env,
            "handover": {"active_handovers": [], "total_count": 0},
            "data_source": data_source,
            "real_data_ratio": real_data_count / 3.0,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_real_satellite_data(self) -> Dict[str, Any]:
        """獲取真實衛星數據 - 使用批量位置API確保總有數據"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 首先獲取衛星列表，選擇前20個衛星
                sat_list_response = await client.get(
                    f"{self.simworld_api_url}/api/v1/satellites/"
                )

                if sat_list_response.status_code == 200:
                    all_satellites = sat_list_response.json()
                    # 選擇不同類型的衛星ID（Starlink, Kuiper等）
                    selected_sat_ids = []
                    for i, sat in enumerate(all_satellites[:100]):  # 從前100個中選擇
                        if i % 5 == 0:  # 每5個選1個，確保多樣性
                            selected_sat_ids.append(sat["id"])
                        if len(selected_sat_ids) >= 20:  # 限制最多20個
                            break

                    if not selected_sat_ids:
                        selected_sat_ids = [sat["id"] for sat in all_satellites[:20]]

                    # 批量獲取衛星位置
                    position_response = await client.post(
                        f"{self.simworld_api_url}/api/v1/satellites/batch-positions",
                        params={
                            "observer_lat": 25.0,  # 台北座標
                            "observer_lon": 121.0,
                            "observer_alt": 0.0,
                        },
                        json=selected_sat_ids,
                        headers={"Content-Type": "application/json"},
                    )

                    if position_response.status_code == 200:
                        satellites_data = position_response.json()

                        # 轉換為環境需要的格式
                        satellites = {}
                        for sat_data in satellites_data:
                            sat_id = sat_data.get(
                                "satellite_name",
                                f"SAT-{sat_data.get('satellite_id', 0)}",
                            )

                            # 計算信號強度 (基於距離和仰角)
                            range_km = sat_data.get("range", 1000.0)
                            elevation = sat_data.get("elevation", 0.0)
                            signal_strength = max(
                                0, 100.0 - (range_km / 50.0) + elevation
                            )
                            path_loss = 150.0 + 20 * math.log10(range_km)

                            satellites[sat_id] = {
                                "satellite_id": sat_id,
                                "latitude": sat_data.get("latitude", 0.0),
                                "longitude": sat_data.get("longitude", 0.0),
                                "altitude": sat_data.get("altitude", 550.0),
                                "velocity": [
                                    sat_data.get("velocity", 0.0),
                                    0.0,
                                    0.0,
                                ],  # 簡化速度向量
                                "elevation_angle": sat_data.get("elevation", 0.0),
                                "azimuth_angle": sat_data.get("azimuth", 0.0),
                                "distance": range_km,
                                "load_factor": random.uniform(0.3, 0.8),  # 模擬負載因子
                                "available_bandwidth": random.uniform(
                                    50.0, 150.0
                                ),  # 模擬可用頻寬
                                "beam_coverage": [],  # 模擬波束覆蓋
                                "handover_count": 0,
                                "is_available": True,
                                "norad_id": str(sat_data.get("satellite_id", "")),
                                "signal_strength": signal_strength,
                                "path_loss_db": path_loss,
                                "doppler_shift": 0.0,  # 可以從速度計算
                                "timestamp": sat_data.get("timestamp", ""),
                                "visible": sat_data.get("visible", False),
                            }

                        self._last_satellite_data = satellites
                        logger.info(f"成功獲取 {len(satellites)} 顆衛星的真實數據")
                        return satellites
                    else:
                        logger.warning(
                            f"批量位置API請求失敗: {position_response.status_code}"
                        )
                else:
                    logger.warning(
                        f"衛星列表API請求失敗: {sat_list_response.status_code}"
                    )

        except Exception as e:
            logger.warning(f"獲取真實衛星數據失敗: {e}")

        # 回退到緩存或模擬數據
        if self._last_satellite_data:
            logger.info("使用緩存的衛星數據")
            return self._last_satellite_data
        elif self.fallback_to_mock:
            logger.info("回退到模擬衛星數據")
            mock_data = self._generate_mock_satellite_data()
            mock_data["_is_mock"] = True
            return mock_data
        else:
            raise Exception("無法獲取衛星數據且不允許回退到模擬數據")

    async def get_real_ue_data(self) -> Dict[str, Any]:
        """獲取真實 UE 數據"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 從 NetStack API 獲取UE列表
                response = await client.get(f"{self.netstack_api_url}/api/v1/ue")

                if response.status_code == 200:
                    ue_list = response.json()

                    # 轉換為環境需要的格式
                    ues = {}
                    for i, ue in enumerate(ue_list[:10]):  # 限制最多10個UE
                        imsi = ue.get("imsi", f"99970000000{i:04d}")
                        ue_id = f"UE-{imsi[-3:]}"  # 使用IMSI後三位作為ID

                        # 嘗試獲取詳細統計
                        ue_metrics = await self._get_ue_metrics_from_netstack(imsi)

                        ues[ue_id] = {
                            "ue_id": ue_id,
                            "imsi": imsi,
                            "latitude": 25.0 + (i * 0.01),  # 台北周邊位置
                            "longitude": 121.0 + (i * 0.01),
                            "altitude": 0.0,
                            "velocity": (0.0, 0.0, 0.0),
                            "current_satellite": None,  # 將由衛星選擇算法決定
                            "signal_strength": ue_metrics.get(
                                "signal_strength", -80.0 + (i * 5)
                            ),
                            "sinr": ue_metrics.get("sinr", 15.0 + (i * 2)),
                            "throughput": ue_metrics.get("throughput", 50.0 + (i * 10)),
                            "latency": ue_metrics.get("latency", 20.0 + (i * 2)),
                            "packet_loss": ue_metrics.get("packet_loss", 0.1),
                            "battery_level": 100.0 - (i * 5),
                            "service_type": ue.get("slice", {}).get(
                                "slice_type", "eMBB"
                            ),
                            "slice_sst": ue.get("slice", {}).get("sst", 1),
                            "apn": ue.get("apn", "internet"),
                            "status": ue.get("status", "registered"),
                            "connection_time": ue_metrics.get("connection_time", 0),
                            "data_usage": {
                                "upload": ue_metrics.get("bytes_uploaded", 0),
                                "download": ue_metrics.get("bytes_downloaded", 0),
                            },
                            "qos_requirements": {
                                "min_throughput": (
                                    50.0
                                    if ue.get("slice", {}).get("sst") == 1
                                    else 10.0
                                ),
                                "max_latency": (
                                    50.0
                                    if ue.get("slice", {}).get("sst") == 2
                                    else 100.0
                                ),
                                "min_reliability": (
                                    0.99
                                    if ue.get("slice", {}).get("sst") == 2
                                    else 0.95
                                ),
                            },
                        }

                    self._last_ue_data = ues
                    logger.info(f"成功獲取 {len(ues)} 個 UE 的真實數據")
                    return ues
                else:
                    logger.warning(
                        f"NetStack API UE端點回應錯誤: {response.status_code}"
                    )

        except Exception as e:
            logger.warning(f"獲取真實 UE 數據失敗: {e}")

        # 回退到緩存或模擬數據
        if self._last_ue_data:
            logger.info("使用緩存的 UE 數據")
            return self._last_ue_data
        elif self.fallback_to_mock:
            logger.info("回退到模擬 UE 數據")
            mock_data = self._generate_mock_ue_data()
            mock_data["_is_mock"] = True
            return mock_data
        else:
            raise Exception("無法獲取 UE 數據且不允許回退到模擬數據")

    async def get_real_network_environment(self) -> Dict[str, Any]:
        """獲取真實網路環境數據"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 獲取核心同步性能指標
                performance_response = await client.get(
                    f"{self.netstack_api_url}/api/v1/core-sync/metrics/performance"
                )

                # 獲取UAV網格故障轉移統計
                uav_stats_response = await client.get(
                    f"{self.netstack_api_url}/api/v1/uav-mesh-failover/stats"
                )

                performance_data = {}
                uav_stats = {}

                if performance_response.status_code == 200:
                    performance_data = performance_response.json()

                if uav_stats_response.status_code == 200:
                    uav_stats = uav_stats_response.json()

                # 從真實數據構建網路環境
                all_components = performance_data.get("all_components", {})
                summary = performance_data.get("summary", {})

                # 提取核心網路指標
                satellite_net = all_components.get("satellite_network", {})
                core_net = all_components.get("core_network", {})
                ground_station = all_components.get("ground_station", {})
                uav_net = all_components.get("uav_network", {})

                network_environment = {
                    "current_time": datetime.utcnow(),
                    "weather_conditions": {
                        # 根據真實性能指標推斷天氣影響
                        "weather_type": self._infer_weather_from_performance(
                            satellite_net
                        ),
                        "visibility": max(
                            0.5, min(1.0, satellite_net.get("availability", 0.95))
                        ),
                        "wind_speed": min(
                            50.0, satellite_net.get("jitter_ms", 1.0) * 10
                        ),
                        "precipitation": max(
                            0.0,
                            min(
                                1.0, (1.0 - satellite_net.get("availability", 0.95)) * 2
                            ),
                        ),
                        "temperature": 20.0
                        + (satellite_net.get("latency_ms", 0.01) * 1000),
                        "humidity": 60.0
                        + (satellite_net.get("packet_loss_rate", 0.01) * 4000),
                    },
                    "interference_sources": [
                        {
                            "source_type": "atmospheric",
                            "strength": satellite_net.get("error_rate", 0.01) * 100,
                            "frequency_band": "Ka",
                            "location": {"latitude": 25.0, "longitude": 121.0},
                        },
                        {
                            "source_type": "urban_noise",
                            "strength": core_net.get("error_rate", 0.01) * 100,
                            "frequency_band": "L",
                            "location": {"latitude": 25.1, "longitude": 121.1},
                        },
                    ],
                    "atmospheric_conditions": {
                        "ionospheric_activity": satellite_net.get("jitter_ms", 1.0)
                        / 10.0,
                        "tropospheric_delay": satellite_net.get("latency_ms", 0.01)
                        * 1000,
                        "rain_attenuation": satellite_net.get("packet_loss_rate", 0.01)
                        * 100,
                        "cloud_coverage": 1.0 - satellite_net.get("availability", 0.95),
                        "atmospheric_pressure": 1013.25
                        + (satellite_net.get("clock_drift_ms", 0.0) * 10),
                    },
                    "satellite_constellation_status": {
                        "total_satellites": 20,  # 與衛星數據一致
                        "active_satellites": int(
                            satellite_net.get("availability", 0.95) * 20
                        ),
                        "average_signal_strength": 100.0
                        - (satellite_net.get("path_loss_db", 150.0) - 150.0),
                        "constellation_health": satellite_net.get("availability", 0.95),
                        "sync_accuracy_ms": satellite_net.get("sync_accuracy_ms", 25.0),
                        "throughput_mbps": satellite_net.get("throughput_mbps", 60.0),
                    },
                    "ground_infrastructure": {
                        "available_ground_stations": int(
                            ground_station.get("availability", 0.99) * 5
                        ),
                        "total_ground_stations": 5,
                        "average_latency": ground_station.get("latency_ms", 0.01),
                        "average_throughput": ground_station.get(
                            "throughput_mbps", 25.0
                        ),
                        "error_rate": ground_station.get("error_rate", 0.01),
                        "jitter_ms": ground_station.get("jitter_ms", 1.0),
                    },
                    "uav_mesh_network": {
                        "service_status": uav_stats.get("service_status", "stopped"),
                        "monitored_uav_count": uav_stats.get("monitored_uav_count", 1),
                        "active_failover_events": uav_stats.get(
                            "active_failover_events", 0
                        ),
                        "total_failovers": uav_stats.get("failover_statistics", {}).get(
                            "total_failovers", 0
                        ),
                        "average_failover_time_ms": uav_stats.get(
                            "failover_statistics", {}
                        ).get("average_failover_time_ms", 0.0),
                        "network_mode_distribution": uav_stats.get(
                            "network_mode_distribution", {}
                        ),
                        "thresholds": uav_stats.get("thresholds", {}),
                        "availability": uav_net.get("availability", 0.98),
                        "throughput_mbps": uav_net.get("throughput_mbps", 45.0),
                    },
                    "overall_performance": {
                        "total_components": summary.get("total_components", 5),
                        "average_accuracy_ms": summary.get("average_accuracy_ms", 8.0),
                        "average_availability": summary.get(
                            "average_availability", 0.98
                        ),
                        "timestamp": performance_data.get(
                            "timestamp", datetime.utcnow().isoformat()
                        ),
                    },
                    "data_freshness": {
                        "last_performance_update": performance_data.get("timestamp"),
                        "last_uav_stats_update": uav_stats.get("last_update"),
                        "data_age_seconds": 0,  # 即時數據
                    },
                }

                self._last_network_data = network_environment
                logger.info("成功獲取真實網路環境數據")
                return network_environment

        except Exception as e:
            logger.warning(f"獲取真實網路環境數據失敗: {e}")

        # 回退到緩存或模擬數據
        if self._last_network_data:
            logger.info("使用緩存的網路環境數據")
            return self._last_network_data
        elif self.fallback_to_mock:
            logger.info("回退到模擬網路環境數據")
            mock_data = self._generate_mock_network_data()
            mock_data["_is_mock"] = True
            return mock_data
        else:
            raise Exception("無法獲取網路環境數據且不允許回退到模擬數據")

    def _infer_weather_from_performance(self, satellite_performance: dict) -> str:
        """根據衛星性能指標推斷天氣條件"""
        availability = satellite_performance.get("availability", 0.95)
        packet_loss = satellite_performance.get("packet_loss_rate", 0.01)

        if availability > 0.98 and packet_loss < 0.005:
            return "clear"
        elif availability > 0.95 and packet_loss < 0.01:
            return "partly_cloudy"
        elif availability > 0.90 and packet_loss < 0.02:
            return "cloudy"
        elif availability > 0.85:
            return "light_rain"
        else:
            return "heavy_rain"

    async def _get_ue_metrics_from_netstack(self, imsi: str) -> Dict[str, Any]:
        """從 NetStack API 獲取 UE 指標"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.netstack_api_url}/api/v1/ue/{imsi}/stats"
                )

                if response.status_code == 200:
                    stats = response.json()
                    # 轉換為環境需要的格式
                    return {
                        "signal_strength": -80.0,  # 需要添加到NetStack API
                        "sinr": 15.0,  # 需要添加到NetStack API
                        "throughput": max(
                            stats.get("bytes_downloaded", 0) / 1000, 50.0
                        ),
                        "latency": stats.get("rtt_ms") or 20.0,
                        "packet_loss": 0.1,  # 需要添加到NetStack API
                        "connection_time": stats.get("connection_time", 0),
                        "bytes_uploaded": stats.get("bytes_uploaded", 0),
                        "bytes_downloaded": stats.get("bytes_downloaded", 0),
                    }
        except Exception as e:
            logger.debug(f"獲取 UE {imsi} 指標失敗: {e}")

        # 返回默認值
        return {
            "signal_strength": -80.0,
            "sinr": 15.0,
            "throughput": 50.0,
            "latency": 20.0,
            "packet_loss": 0.1,
            "connection_time": 0,
            "bytes_uploaded": 0,
            "bytes_downloaded": 0,
        }

    def _calculate_satellite_geometry(
        self, sat_lat: float, sat_lon: float, sat_alt: float
    ) -> Tuple[float, float, float]:
        """計算衛星相對於地面的幾何參數"""
        # 簡化的幾何計算（實際應該使用更精確的軌道力學計算）
        # 假設觀測點在地面 (0, 0, 0)

        # 地球半徑 (km)
        earth_radius = 6371.0

        # 衛星距離地心距離
        sat_distance_from_center = earth_radius + sat_alt / 1000.0

        # 計算距離（簡化計算）
        distance = np.sqrt((sat_lat**2) + (sat_lon**2) + (sat_alt / 1000.0) ** 2)

        # 計算仰角（簡化）
        elevation = np.arcsin(sat_alt / 1000.0 / distance) * 180.0 / np.pi
        elevation = max(0.0, min(90.0, elevation))

        # 計算方位角（簡化）
        azimuth = np.arctan2(sat_lon, sat_lat) * 180.0 / np.pi
        if azimuth < 0:
            azimuth += 360.0

        return elevation, azimuth, distance

    def _generate_mock_satellite_data(self) -> Dict[str, Any]:
        """生成模擬衛星數據（回退選項）"""
        satellites = {}
        for i in range(20):
            sat_id = f"LEO-{i:03d}"
            satellites[sat_id] = {
                "satellite_id": sat_id,
                "latitude": random.uniform(-60, 60),
                "longitude": random.uniform(-180, 180),
                "altitude": random.uniform(500, 1200),
                "velocity": (random.uniform(-7, 7), random.uniform(-7, 7), 0.0),
                "elevation_angle": random.uniform(10, 90),
                "azimuth_angle": random.uniform(0, 360),
                "distance": random.uniform(500, 2000),
                "load_factor": random.uniform(0.1, 0.9),
                "available_bandwidth": random.uniform(10, 100),
                "beam_coverage": [],
                "handover_count": random.randint(0, 10),
                "is_available": random.random() > 0.1,
            }

        return satellites

    def _generate_mock_ue_data(self) -> Dict[str, Any]:
        """生成模擬 UE 數據（回退選項）"""
        ues = {}
        for i in range(5):
            ue_id = f"UE-{i:03d}"
            ues[ue_id] = {
                "ue_id": ue_id,
                "latitude": random.uniform(-45, 45),
                "longitude": random.uniform(-120, 120),
                "altitude": 0.0,
                "velocity": (random.uniform(-50, 50), random.uniform(-50, 50), 0.0),
                "current_satellite": f"LEO-{random.randint(0, 19):03d}",
                "signal_strength": random.uniform(-120, -60),
                "sinr": random.uniform(-5, 30),
                "throughput": random.uniform(1, 100),
                "latency": random.uniform(10, 200),
                "packet_loss": random.uniform(0, 5),
                "battery_level": random.uniform(20, 100),
                "service_type": random.choice(["eMBB", "URLLC", "mMTC"]),
                "qos_requirements": {},
            }

        return ues

    def _generate_mock_network_data(self) -> Dict[str, Any]:
        """生成模擬網路環境數據（回退選項）"""
        return {
            "current_time": datetime.utcnow(),
            "weather_condition": random.choice(["clear", "cloudy", "rainy"]),
            "interference_level": random.uniform(0.0, 0.3),
            "network_congestion": random.uniform(0.0, 0.7),
            "satellite_constellation_size": 20,
            "active_ue_count": 5,
            "total_handover_rate": random.uniform(0.05, 0.2),
            "core_network_status": "healthy",
        }
