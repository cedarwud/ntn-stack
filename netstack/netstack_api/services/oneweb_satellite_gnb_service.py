"""
OneWeb 衛星作為 gNodeB 的模擬服務

實現 OneWeb LEO 衛星群作為 5G NTN gNodeB 的完整模擬，包括：
- 實時軌道數據同步
- 動態 UERANSIM 配置生成
- 多普勒效應和傳播延遲模擬
- 動態波束管理
- NTN 特性優化
"""

import asyncio
import math
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import uuid
import structlog
import aiofiles
import aiohttp
from pathlib import Path

# 導入 Skyfield 相關模組
from skyfield.api import load, wgs84, EarthSatellite
from skyfield.timelib import Time
import numpy as np

from .satellite_gnb_mapping_service import SatelliteGnbMappingService
from ..models.ueransim_models import UAVPosition, NetworkParameters

logger = structlog.get_logger(__name__)

class OneWebSatelliteGnbService:
    """OneWeb 衛星作為 gNodeB 的模擬服務"""
    
    def __init__(
        self,
        satellite_mapping_service: SatelliteGnbMappingService,
        simworld_api_url: str = "http://simworld-backend:8000",
        ueransim_config_dir: str = "/tmp/ueransim_configs"
    ):
        self.logger = logger.bind(service="oneweb_satellite_gnb")
        self.satellite_mapping_service = satellite_mapping_service
        self.simworld_api_url = simworld_api_url
        self.ueransim_config_dir = Path(ueransim_config_dir)
        
        # 確保配置目錄存在
        self.ueransim_config_dir.mkdir(parents=True, exist_ok=True)
        
        # OneWeb 衛星群配置
        self.oneweb_constellation = {
            "total_satellites": 648,  # OneWeb Gen1 星座
            "orbital_planes": 18,
            "satellites_per_plane": 36,
            "altitude_km": 1200,  # OneWeb 軌道高度
            "inclination_deg": 87.4,  # OneWeb 軌道傾角
            "frequency_bands": {
                "ka_band_uplink": {"start": 27.5, "end": 30.0, "unit": "GHz"},
                "ka_band_downlink": {"start": 17.8, "end": 20.2, "unit": "GHz"},
                "ku_band": {"start": 10.7, "end": 12.7, "unit": "GHz"}
            }
        }
        
        # 活躍的 gNodeB 追蹤
        self.active_gnodebs: Dict[int, Dict] = {}
        self.tracking_tasks: Dict[str, asyncio.Task] = {}
        
        # NTN 特性參數
        self.ntn_parameters = {
            "max_propagation_delay_ms": 10.0,  # 1200km 高度的最大延遲
            "doppler_shift_tolerance": 50,  # kHz
            "handover_margin_db": 3.0,
            "beam_coverage_radius_km": 500,
            "min_elevation_angle_deg": 10.0
        }

    async def initialize_oneweb_constellation(self) -> Dict[str, any]:
        """
        初始化 OneWeb 衛星群配置
        
        Returns:
            初始化結果和衛星列表
        """
        self.logger.info("初始化 OneWeb 衛星群配置")
        
        try:
            # 從 simworld 獲取 OneWeb 衛星列表
            oneweb_satellites = await self._get_oneweb_satellites_from_simworld()
            
            if not oneweb_satellites:
                # 如果無法從 simworld 獲取，使用預設配置
                oneweb_satellites = self._generate_default_oneweb_satellites()
            
            # 初始化每個衛星的 gNodeB 配置
            gnodeb_configs = {}
            for satellite in oneweb_satellites[:10]:  # 先處理前10個衛星進行測試
                satellite_id = satellite["id"]
                
                # 生成 gNodeB 配置
                gnb_config = await self._create_satellite_gnodeb_config(satellite)
                gnodeb_configs[satellite_id] = gnb_config
                
                # 添加到活躍列表
                self.active_gnodebs[satellite_id] = {
                    "satellite_info": satellite,
                    "gnb_config": gnb_config,
                    "last_update": datetime.utcnow(),
                    "status": "active"
                }
            
            self.logger.info(
                "OneWeb 衛星群初始化完成",
                total_satellites=len(oneweb_satellites),
                active_gnodebs=len(gnodeb_configs)
            )
            
            return {
                "success": True,
                "constellation_info": self.oneweb_constellation,
                "initialized_satellites": len(gnodeb_configs),
                "total_available": len(oneweb_satellites),
                "active_gnodebs": list(gnodeb_configs.keys()),
                "ntn_parameters": self.ntn_parameters
            }
            
        except Exception as e:
            self.logger.error("OneWeb 衛星群初始化失敗", error=str(e))
            raise

    async def _get_oneweb_satellites_from_simworld(self) -> List[Dict]:
        """從 simworld 獲取 OneWeb 衛星數據"""
        try:
            async with aiohttp.ClientSession() as session:
                # 獲取衛星列表
                url = f"{self.simworld_api_url}/api/v1/satellites"
                async with session.get(url) as response:
                    if response.status == 200:
                        satellites_data = await response.json()
                        
                        # 過濾 OneWeb 衛星
                        oneweb_satellites = []
                        for satellite in satellites_data.get("satellites", []):
                            if "oneweb" in satellite.get("name", "").lower():
                                oneweb_satellites.append(satellite)
                        
                        return oneweb_satellites
                    
        except Exception as e:
            self.logger.warning("無法從 simworld 獲取 OneWeb 衛星", error=str(e))
            return []

    def _generate_default_oneweb_satellites(self) -> List[Dict]:
        """生成預設的 OneWeb 衛星配置"""
        satellites = []
        
        for plane in range(3):  # 簡化版本，只生成3個軌道面
            for sat in range(5):  # 每個軌道面5個衛星
                satellite_id = plane * 10 + sat + 1
                
                # 模擬軌道位置
                longitude = (plane * 120) + (sat * 24) - 180  # 分佈在全球
                latitude = math.sin(math.radians(plane * 30)) * 60  # 模擬傾斜軌道
                
                satellite = {
                    "id": satellite_id,
                    "name": f"OneWeb-{satellite_id:03d}",
                    "orbital_plane": plane + 1,
                    "position_in_plane": sat + 1,
                    "current_position": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "altitude": self.oneweb_constellation["altitude_km"]
                    },
                    "tle_data": {
                        "line1": f"1 {satellite_id:05d}U 23001{satellite_id:03d} 23001.00000000  .00000000  00000-0  00000-0 0    90",
                        "line2": f"2 {satellite_id:05d} {self.oneweb_constellation['inclination_deg']:8.4f} {plane * 120:8.4f}   0000000 000.0000 {longitude + 180:8.4f} 00.00000000    10"
                    },
                    "status": "operational"
                }
                satellites.append(satellite)
        
        return satellites

    async def _create_satellite_gnodeb_config(self, satellite: Dict) -> Dict:
        """為單個衛星創建 gNodeB 配置"""
        
        satellite_id = satellite["id"]
        position = satellite["current_position"]
        
        # 使用衛星映射服務生成基本配置
        gnb_result = await self.satellite_mapping_service.convert_satellite_to_gnb_config(
            satellite_id=satellite_id,
            uav_position=None,  # 暫時不指定 UAV 位置
            network_params=NetworkParameters(
                frequency=2100,  # 5G n78 頻段
                bandwidth=20
            )
        )
        
        if not gnb_result.get("success"):
            raise Exception(f"無法為衛星 {satellite_id} 生成 gNodeB 配置")
        
        base_config = gnb_result["gnb_config"]
        
        # 增強配置以支援 OneWeb NTN 特性
        enhanced_config = {
            **base_config,
            
            # OneWeb 特定配置
            "satellite_name": satellite["name"],
            "orbital_plane": satellite.get("orbital_plane", 1),
            "constellation": "OneWeb",
            
            # NTN 增強配置
            "ntn_config": {
                **base_config.get("ntn_config", {}),
                "constellation_type": "LEO",
                "orbital_altitude_km": self.oneweb_constellation["altitude_km"],
                "max_doppler_shift_khz": self._calculate_max_doppler_shift(position["altitude"]),
                "beam_coverage": self._calculate_beam_coverage(position),
                "handover_parameters": {
                    "trigger_threshold_db": -100,
                    "hysteresis_db": self.ntn_parameters["handover_margin_db"],
                    "time_to_trigger_ms": 320
                }
            },
            
            # 動態參數（會隨軌道更新）
            "dynamic_parameters": {
                "current_position": position,
                "coverage_area": self._calculate_coverage_area(position),
                "serving_uavs": [],
                "load_factor": 0.0,
                "last_position_update": datetime.utcnow().isoformat()
            }
        }
        
        return enhanced_config

    def _calculate_max_doppler_shift(self, altitude_km: float) -> float:
        """計算最大多普勒偏移"""
        # OneWeb 衛星軌道速度約 7.5 km/s
        orbital_velocity = 7.5  # km/s
        frequency_ghz = 2.1  # 5G n78 頻段
        speed_of_light = 299792.458  # km/s
        
        # 最大多普勒偏移 = 2 * v * f / c
        max_doppler_khz = 2 * orbital_velocity * frequency_ghz * 1000 / speed_of_light
        return max_doppler_khz

    def _calculate_beam_coverage(self, position: Dict) -> Dict:
        """計算衛星波束覆蓋"""
        altitude_km = position["altitude"]
        earth_radius_km = 6371
        
        # 最大覆蓋角度
        max_coverage_angle = math.acos(earth_radius_km / (earth_radius_km + altitude_km))
        max_coverage_degrees = math.degrees(max_coverage_angle)
        
        # 考慮最小仰角限制的服務覆蓋
        min_elevation_rad = math.radians(self.ntn_parameters["min_elevation_angle_deg"])
        service_radius_km = altitude_km * math.tan(max_coverage_angle - min_elevation_rad)
        
        return {
            "max_coverage_angle_deg": max_coverage_degrees,
            "service_radius_km": min(service_radius_km, self.ntn_parameters["beam_coverage_radius_km"]),
            "coverage_area_km2": math.pi * service_radius_km ** 2,
            "min_elevation_deg": self.ntn_parameters["min_elevation_angle_deg"]
        }

    def _calculate_coverage_area(self, position: Dict) -> List[Dict]:
        """計算衛星覆蓋區域的地理邊界"""
        lat = position["latitude"]
        lon = position["longitude"]
        altitude_km = position["altitude"]
        
        # 簡化的覆蓋圓計算
        coverage_radius_deg = self.ntn_parameters["beam_coverage_radius_km"] / 111.32  # 大約轉換為度
        
        # 生成覆蓋區域的多邊形點
        coverage_polygon = []
        for angle in range(0, 360, 30):  # 每30度一個點
            angle_rad = math.radians(angle)
            point_lat = lat + coverage_radius_deg * math.cos(angle_rad)
            point_lon = lon + coverage_radius_deg * math.sin(angle_rad) / math.cos(math.radians(lat))
            
            coverage_polygon.append({
                "latitude": point_lat,
                "longitude": point_lon
            })
        
        return coverage_polygon

    async def start_orbital_tracking(
        self, 
        satellite_ids: Optional[List[int]] = None,
        update_interval_seconds: int = 30
    ) -> Dict[str, any]:
        """
        啟動衛星軌道追蹤
        
        Args:
            satellite_ids: 要追蹤的衛星 ID 列表，None 表示追蹤所有活躍衛星
            update_interval_seconds: 更新間隔
            
        Returns:
            追蹤任務信息
        """
        
        if satellite_ids is None:
            satellite_ids = list(self.active_gnodebs.keys())
        
        task_id = str(uuid.uuid4())
        
        # 啟動追蹤任務
        tracking_task = asyncio.create_task(
            self._orbital_tracking_loop(satellite_ids, update_interval_seconds, task_id)
        )
        
        self.tracking_tasks[task_id] = tracking_task
        
        self.logger.info(
            "軌道追蹤已啟動",
            task_id=task_id,
            satellites=satellite_ids,
            update_interval=update_interval_seconds
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "tracking_satellites": satellite_ids,
            "update_interval_seconds": update_interval_seconds,
            "status": "active"
        }

    async def _orbital_tracking_loop(
        self, 
        satellite_ids: List[int], 
        update_interval: int, 
        task_id: str
    ):
        """軌道追蹤循環"""
        
        self.logger.info("軌道追蹤循環開始", task_id=task_id)
        
        try:
            while True:
                for satellite_id in satellite_ids:
                    if satellite_id in self.active_gnodebs:
                        await self._update_satellite_position(satellite_id)
                
                # 等待下次更新
                await asyncio.sleep(update_interval)
                
        except asyncio.CancelledError:
            self.logger.info("軌道追蹤任務被取消", task_id=task_id)
        except Exception as e:
            self.logger.error("軌道追蹤錯誤", task_id=task_id, error=str(e))

    async def _update_satellite_position(self, satellite_id: int):
        """更新單個衛星位置和配置"""
        
        try:
            # 從 simworld 獲取最新位置
            new_position = await self._get_satellite_current_position(satellite_id)
            
            if new_position:
                # 更新衛星信息
                gnb_info = self.active_gnodebs[satellite_id]
                old_position = gnb_info["satellite_info"]["current_position"]
                
                # 更新位置
                gnb_info["satellite_info"]["current_position"] = new_position
                gnb_info["last_update"] = datetime.utcnow()
                
                # 重新計算覆蓋區域
                gnb_info["gnb_config"]["dynamic_parameters"]["current_position"] = new_position
                gnb_info["gnb_config"]["dynamic_parameters"]["coverage_area"] = self._calculate_coverage_area(new_position)
                gnb_info["gnb_config"]["dynamic_parameters"]["last_position_update"] = datetime.utcnow().isoformat()
                
                # 如果位置變化顯著，重新生成 UERANSIM 配置
                if self._position_changed_significantly(old_position, new_position):
                    await self._regenerate_ueransim_config(satellite_id)
                
                self.logger.debug(
                    "衛星位置已更新",
                    satellite_id=satellite_id,
                    new_position=new_position
                )
                
        except Exception as e:
            self.logger.error("更新衛星位置失敗", satellite_id=satellite_id, error=str(e))

    async def _get_satellite_current_position(self, satellite_id: int) -> Optional[Dict]:
        """從 simworld 獲取衛星當前位置"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.simworld_api_url}/api/v1/satellites/{satellite_id}/position"
                async with session.get(url) as response:
                    if response.status == 200:
                        position_data = await response.json()
                        
                        return {
                            "latitude": position_data.get("latitude"),
                            "longitude": position_data.get("longitude"),
                            "altitude": position_data.get("altitude")
                        }
                        
        except Exception as e:
            self.logger.warning("無法獲取衛星位置", satellite_id=satellite_id, error=str(e))
            
        return None

    def _position_changed_significantly(self, old_pos: Dict, new_pos: Dict, threshold_km: float = 50) -> bool:
        """檢查位置是否有顯著變化"""
        
        # 簡化的距離計算
        lat_diff = abs(new_pos["latitude"] - old_pos["latitude"])
        lon_diff = abs(new_pos["longitude"] - old_pos["longitude"])
        
        # 轉換為公里（粗略估算）
        distance_km = math.sqrt((lat_diff * 111.32) ** 2 + (lon_diff * 111.32 * math.cos(math.radians(new_pos["latitude"]))) ** 2)
        
        return distance_km > threshold_km

    async def _regenerate_ueransim_config(self, satellite_id: int):
        """重新生成 UERANSIM 配置文件"""
        
        gnb_info = self.active_gnodebs.get(satellite_id)
        if not gnb_info:
            return
        
        gnb_config = gnb_info["gnb_config"]
        
        # 生成 UERANSIM gNodeB 配置文件
        config_content = self._generate_ueransim_gnb_config(gnb_config)
        
        # 寫入配置文件
        config_file = self.ueransim_config_dir / f"gnb-oneweb-{satellite_id}.yaml"
        async with aiofiles.open(config_file, 'w') as f:
            await f.write(config_content)
        
        self.logger.info("UERANSIM 配置已重新生成", satellite_id=satellite_id, config_file=str(config_file))

    def _generate_ueransim_gnb_config(self, gnb_config: Dict) -> str:
        """生成 UERANSIM gNodeB 配置 YAML"""
        
        config = {
            "mcc": gnb_config["mcc"],
            "mnc": gnb_config["mnc"],
            "nci": gnb_config["nci"],
            "idLength": gnb_config["id_length"],
            "tac": gnb_config["tac"],
            "linkIp": gnb_config["link_ip"],
            "ngapIp": gnb_config["ngap_ip"],
            "gtpIp": gnb_config["gtp_ip"],
            
            # OneWeb NTN 特定配置
            "plmns": [{
                "mcc": gnb_config["mcc"],
                "mnc": gnb_config["mnc"],
                "tac": gnb_config["tac"],
                "nssai": [
                    {"sst": 1, "sd": "0x111111"},  # 高優先級切片
                    {"sst": 2, "sd": "0x222222"},  # 標準切片
                    {"sst": 3, "sd": "0x333333"}   # 低延遲切片
                ]
            }],
            
            # NTN 優化參數
            "ntn": {
                "enabled": True,
                "satelliteName": gnb_config.get("satellite_name", f"OneWeb-{gnb_config['nci']}"),
                "constellation": "OneWeb",
                "propagationDelay": gnb_config["ntn_config"]["propagation_delay_ms"],
                "dopplerCompensation": True,
                "beamTracking": True,
                "maxDopplerShift": gnb_config["ntn_config"]["max_doppler_shift_khz"],
                "coverageRadius": gnb_config["ntn_config"]["beam_coverage"]["service_radius_km"]
            }
        }
        
        # 轉換為 YAML 格式
        import yaml
        return yaml.dump(config, default_flow_style=False, indent=2)

    async def get_constellation_status(self) -> Dict[str, any]:
        """獲取 OneWeb 星座狀態"""
        
        active_satellites = len(self.active_gnodebs)
        total_coverage_area = 0
        serving_uavs = 0
        
        satellite_status = []
        for satellite_id, gnb_info in self.active_gnodebs.items():
            gnb_config = gnb_info["gnb_config"]
            dynamic_params = gnb_config["dynamic_parameters"]
            
            coverage_area = gnb_config["ntn_config"]["beam_coverage"]["coverage_area_km2"]
            total_coverage_area += coverage_area
            serving_uavs += len(dynamic_params["serving_uavs"])
            
            satellite_status.append({
                "satellite_id": satellite_id,
                "name": gnb_config.get("satellite_name"),
                "position": dynamic_params["current_position"],
                "coverage_area_km2": coverage_area,
                "serving_uavs": len(dynamic_params["serving_uavs"]),
                "load_factor": dynamic_params["load_factor"],
                "last_update": dynamic_params["last_position_update"],
                "status": gnb_info["status"]
            })
        
        return {
            "constellation_info": self.oneweb_constellation,
            "active_satellites": active_satellites,
            "total_coverage_area_km2": total_coverage_area,
            "total_serving_uavs": serving_uavs,
            "tracking_tasks": len(self.tracking_tasks),
            "satellite_status": satellite_status,
            "ntn_parameters": self.ntn_parameters
        }

    async def stop_orbital_tracking(self, task_id: str) -> bool:
        """停止軌道追蹤任務"""
        
        if task_id in self.tracking_tasks:
            task = self.tracking_tasks[task_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.tracking_tasks[task_id]
            
            self.logger.info("軌道追蹤任務已停止", task_id=task_id)
            return True
        
        return False

    async def shutdown(self):
        """關閉服務，清理資源"""
        
        self.logger.info("正在關閉 OneWeb 衛星 gNodeB 服務")
        
        # 停止所有追蹤任務
        for task_id in list(self.tracking_tasks.keys()):
            await self.stop_orbital_tracking(task_id)
        
        # 清理活躍 gNodeB
        self.active_gnodebs.clear()
        
        self.logger.info("OneWeb 衛星 gNodeB 服務已關閉") 