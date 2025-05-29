"""
UAV UE 模擬服務

提供 UAV 軌跡管理、UE 配置生成、動態位置追蹤、信號質量監測等功能
"""

import asyncio
import json
import logging
import math
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import structlog
import httpx

from ..adapters.mongo_adapter import MongoAdapter
from ..adapters.redis_adapter import RedisAdapter
from ..models.uav_models import (
    UAVTrajectory,
    UAVStatus,
    UAVPosition,
    UAVSignalQuality,
    UAVUEConfig,
    UAVFlightStatus,
    UEConnectionStatus,
    TrajectoryPoint,
    TrajectoryCreateRequest,
    TrajectoryUpdateRequest,
    UAVCreateRequest,
    UAVMissionStartRequest,
    UAVPositionUpdateRequest,
    TrajectoryResponse,
    UAVStatusResponse,
    UAVListResponse,
    TrajectoryListResponse,
)

logger = structlog.get_logger(__name__)


class UAVUEService:
    """UAV UE 模擬服務"""

    def __init__(
        self,
        mongo_adapter: MongoAdapter,
        redis_adapter: RedisAdapter,
        ueransim_config_dir: str = "/tmp/ueransim_configs",
        simworld_api_url: str = "http://simworld-backend:8000",
        update_interval_sec: float = 5.0,
    ):
        self.mongo_adapter = mongo_adapter
        self.redis_adapter = redis_adapter
        self.ueransim_config_dir = Path(ueransim_config_dir)
        self.simworld_api_url = simworld_api_url.rstrip("/")
        self.update_interval_sec = update_interval_sec

        # 確保配置目錄存在
        self.ueransim_config_dir.mkdir(parents=True, exist_ok=True)

        # 追蹤運行中的任務
        self._active_missions: Dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()

        logger.info(
            "UAVUEService 初始化完成",
            config_dir=str(self.ueransim_config_dir),
            simworld_url=self.simworld_api_url,
        )

    async def create_trajectory(
        self, request: TrajectoryCreateRequest
    ) -> TrajectoryResponse:
        """創建新軌跡"""
        trajectory_id = str(uuid.uuid4())
        trajectory = UAVTrajectory(
            trajectory_id=trajectory_id,
            name=request.name,
            description=request.description,
            mission_type=request.mission_type,
            points=request.points,
        )

        # 計算軌跡統計信息
        total_distance_km = self._calculate_trajectory_distance(trajectory.points)
        estimated_duration_minutes = self._estimate_flight_duration(trajectory.points)

        # 儲存到資料庫
        trajectory_doc = trajectory.dict()
        await self.mongo_adapter.insert_one("uav_trajectories", trajectory_doc)

        logger.info("軌跡創建成功", trajectory_id=trajectory_id, name=request.name)

        return TrajectoryResponse(
            **trajectory.dict(),
            total_distance_km=total_distance_km,
            estimated_duration_minutes=estimated_duration_minutes,
        )

    async def get_trajectory(self, trajectory_id: str) -> Optional[TrajectoryResponse]:
        """獲取軌跡詳情"""
        trajectory_doc = await self.mongo_adapter.find_one(
            "uav_trajectories", {"trajectory_id": trajectory_id}
        )

        if not trajectory_doc:
            return None

        trajectory = UAVTrajectory(**trajectory_doc)
        total_distance_km = self._calculate_trajectory_distance(trajectory.points)
        estimated_duration_minutes = self._estimate_flight_duration(trajectory.points)

        return TrajectoryResponse(
            **trajectory.dict(),
            total_distance_km=total_distance_km,
            estimated_duration_minutes=estimated_duration_minutes,
        )

    async def list_trajectories(
        self, limit: int = 100, offset: int = 0
    ) -> TrajectoryListResponse:
        """列出所有軌跡"""
        trajectories_docs = await self.mongo_adapter.find_many(
            "uav_trajectories", {}, limit=limit, skip=offset
        )

        trajectories = []
        for doc in trajectories_docs:
            trajectory = UAVTrajectory(**doc)
            total_distance_km = self._calculate_trajectory_distance(trajectory.points)
            estimated_duration_minutes = self._estimate_flight_duration(
                trajectory.points
            )

            trajectories.append(
                TrajectoryResponse(
                    **trajectory.dict(),
                    total_distance_km=total_distance_km,
                    estimated_duration_minutes=estimated_duration_minutes,
                )
            )

        total = await self.mongo_adapter.count("uav_trajectories", {})

        return TrajectoryListResponse(trajectories=trajectories, total=total)

    async def update_trajectory(
        self, trajectory_id: str, request: TrajectoryUpdateRequest
    ) -> Optional[TrajectoryResponse]:
        """更新軌跡"""
        existing_trajectory = await self.mongo_adapter.find_one(
            "uav_trajectories", {"trajectory_id": trajectory_id}
        )

        if not existing_trajectory:
            return None

        # 準備更新數據
        update_data = {"updated_at": datetime.utcnow()}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.mission_type is not None:
            update_data["mission_type"] = request.mission_type
        if request.points is not None:
            update_data["points"] = [point.dict() for point in request.points]

        await self.mongo_adapter.update_one(
            "uav_trajectories", {"trajectory_id": trajectory_id}, {"$set": update_data}
        )

        # 獲取更新後的軌跡
        return await self.get_trajectory(trajectory_id)

    async def delete_trajectory(self, trajectory_id: str) -> bool:
        """刪除軌跡"""
        result = await self.mongo_adapter.delete_one(
            "uav_trajectories", {"trajectory_id": trajectory_id}
        )

        if result.deleted_count > 0:
            logger.info("軌跡刪除成功", trajectory_id=trajectory_id)
            return True
        return False

    async def create_uav(self, request: UAVCreateRequest) -> UAVStatusResponse:
        """創建新 UAV"""
        uav_id = str(uuid.uuid4())

        uav_status = UAVStatus(
            uav_id=uav_id,
            name=request.name,
            ue_config=request.ue_config,
            current_position=request.initial_position,
        )

        # 儲存到資料庫
        await self.mongo_adapter.insert_one("uav_status", uav_status.dict())

        # 生成 UERANSIM 配置文件
        await self._generate_ueransim_config(uav_status)

        logger.info("UAV 創建成功", uav_id=uav_id, name=request.name)

        return UAVStatusResponse(**uav_status.dict(), mission_progress_percent=0.0)

    async def get_uav_status(self, uav_id: str) -> Optional[UAVStatusResponse]:
        """獲取 UAV 狀態"""
        uav_doc = await self.mongo_adapter.find_one("uav_status", {"uav_id": uav_id})

        if not uav_doc:
            return None

        uav_status = UAVStatus(**uav_doc)

        # 計算任務進度
        mission_progress = await self._calculate_mission_progress(uav_status)

        return UAVStatusResponse(
            **uav_status.dict(), mission_progress_percent=mission_progress
        )

    async def list_uavs(self, limit: int = 100, offset: int = 0) -> UAVListResponse:
        """列出所有 UAV"""
        uav_docs = await self.mongo_adapter.find_many(
            "uav_status", {}, limit=limit, skip=offset
        )

        uavs = []
        for doc in uav_docs:
            uav_status = UAVStatus(**doc)
            mission_progress = await self._calculate_mission_progress(uav_status)
            uavs.append(
                UAVStatusResponse(
                    **uav_status.dict(), mission_progress_percent=mission_progress
                )
            )

        total = await self.mongo_adapter.count("uav_status", {})

        return UAVListResponse(uavs=uavs, total=total)

    async def start_mission(
        self, uav_id: str, request: UAVMissionStartRequest
    ) -> Optional[UAVStatusResponse]:
        """開始 UAV 任務"""
        # 檢查 UAV 存在
        uav_status = await self.get_uav_status(uav_id)
        if not uav_status:
            return None

        # 檢查軌跡存在
        trajectory = await self.get_trajectory(request.trajectory_id)
        if not trajectory:
            raise ValueError(f"軌跡不存在: {request.trajectory_id}")

        # 停止現有任務（如果有）
        if uav_id in self._active_missions:
            await self.stop_mission(uav_id)

        # 更新 UAV 狀態
        start_time = request.start_time or datetime.utcnow()
        update_data = {
            "trajectory_id": request.trajectory_id,
            "mission_start_time": start_time,
            "flight_status": UAVFlightStatus.FLYING.value,
            "ue_connection_status": UEConnectionStatus.CONNECTING.value,
            "last_update": datetime.utcnow(),
        }

        await self.mongo_adapter.update_one(
            "uav_status", {"uav_id": uav_id}, {"$set": update_data}
        )

        # 啟動任務追蹤任務
        mission_task = asyncio.create_task(
            self._run_mission(uav_id, request.trajectory_id, request.speed_factor)
        )
        self._active_missions[uav_id] = mission_task

        logger.info("UAV 任務啟動", uav_id=uav_id, trajectory_id=request.trajectory_id)

        return await self.get_uav_status(uav_id)

    async def stop_mission(self, uav_id: str) -> Optional[UAVStatusResponse]:
        """停止 UAV 任務"""
        # 停止任務追蹤
        if uav_id in self._active_missions:
            task = self._active_missions[uav_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._active_missions[uav_id]

        # 更新 UAV 狀態
        update_data = {
            "flight_status": UAVFlightStatus.HOVERING.value,
            "ue_connection_status": UEConnectionStatus.CONNECTED.value,
            "trajectory_id": None,
            "mission_start_time": None,
            "last_update": datetime.utcnow(),
        }

        await self.mongo_adapter.update_one(
            "uav_status", {"uav_id": uav_id}, {"$set": update_data}
        )

        logger.info("UAV 任務停止", uav_id=uav_id)

        return await self.get_uav_status(uav_id)

    async def update_uav_position(
        self, uav_id: str, request: UAVPositionUpdateRequest
    ) -> Optional[UAVStatusResponse]:
        """更新 UAV 位置"""
        update_data = {
            "current_position": request.position.dict(),
            "last_update": datetime.utcnow(),
        }

        if request.signal_quality:
            update_data["signal_quality"] = request.signal_quality.dict()

            # 根據信號質量自動切換網路
            await self._handle_signal_quality_change(uav_id, request.signal_quality)

        await self.mongo_adapter.update_one(
            "uav_status", {"uav_id": uav_id}, {"$set": update_data}
        )

        # 更新 Sionna 信道模型
        await self._update_sionna_channel_model(uav_id, request.position)

        return await self.get_uav_status(uav_id)

    async def delete_uav(self, uav_id: str) -> bool:
        """刪除 UAV"""
        # 停止任務
        await self.stop_mission(uav_id)

        # 刪除配置文件
        config_file = self.ueransim_config_dir / f"ue_{uav_id}.yaml"
        if config_file.exists():
            config_file.unlink()

        # 從資料庫刪除
        result = await self.mongo_adapter.delete_one("uav_status", {"uav_id": uav_id})

        if result.deleted_count > 0:
            logger.info("UAV 刪除成功", uav_id=uav_id)
            return True
        return False

    async def shutdown(self):
        """關閉服務"""
        self._shutdown_event.set()

        # 停止所有活動任務
        for uav_id, task in self._active_missions.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._active_missions.clear()
        logger.info("UAVUEService 已關閉")

    # 私有方法

    def _calculate_trajectory_distance(self, points: List[TrajectoryPoint]) -> float:
        """計算軌跡總距離（公里）"""
        total_distance = 0.0

        for i in range(1, len(points)):
            p1, p2 = points[i - 1], points[i]
            distance = self._haversine_distance(
                p1.latitude, p1.longitude, p2.latitude, p2.longitude
            )
            total_distance += distance

        return total_distance

    def _estimate_flight_duration(self, points: List[TrajectoryPoint]) -> float:
        """估算飛行時間（分鐘）"""
        if len(points) < 2:
            return 0.0

        total_time = 0.0

        for i in range(1, len(points)):
            p1, p2 = points[i - 1], points[i]
            time_diff = (p2.timestamp - p1.timestamp).total_seconds()
            total_time += time_diff

        return total_time / 60.0  # 轉換為分鐘

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """計算兩點間的 Haversine 距離（公里）"""
        R = 6371  # 地球半徑（公里）

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def _calculate_mission_progress(self, uav_status: UAVStatus) -> float:
        """計算任務進度百分比"""
        if not uav_status.trajectory_id or not uav_status.mission_start_time:
            return 0.0

        # 獲取軌跡資訊
        trajectory = await self.get_trajectory(uav_status.trajectory_id)
        if not trajectory or not uav_status.current_position:
            return 0.0

        # 計算已完成的距離
        completed_distance = 0.0
        current_pos = uav_status.current_position

        # 找到最接近當前位置的軌跡點
        min_distance = float("inf")
        closest_index = 0

        for i, point in enumerate(trajectory.points):
            distance = self._haversine_distance(
                current_pos.latitude,
                current_pos.longitude,
                point.latitude,
                point.longitude,
            )
            if distance < min_distance:
                min_distance = distance
                closest_index = i

        # 計算到最接近點的距離
        for i in range(1, closest_index + 1):
            p1, p2 = trajectory.points[i - 1], trajectory.points[i]
            completed_distance += self._haversine_distance(
                p1.latitude, p1.longitude, p2.latitude, p2.longitude
            )

        # 計算進度百分比
        total_distance = trajectory.total_distance_km or 1.0
        progress = min(100.0, (completed_distance / total_distance) * 100.0)

        return progress

    async def _generate_ueransim_config(self, uav_status: UAVStatus) -> str:
        """生成 UERANSIM UE 配置文件"""
        config_file = self.ueransim_config_dir / f"ue_{uav_status.uav_id}.yaml"

        ue_config = uav_status.ue_config
        config_content = f"""
# UERANSIM UE configuration for UAV {uav_status.name}
# Generated at {datetime.utcnow().isoformat()}

info: 'UERANSIM UE Config for UAV {uav_status.name}'

# UE identity
supi: 'imsi-{ue_config.imsi}'
mcc: '{ue_config.plmn[:3]}'
mnc: '{ue_config.plmn[3:]}'

# Security
key: '{ue_config.key}'
op: 'c9e8763286b5b9ffbdf56e1297d0887b'
opc: '{ue_config.opc}'
amf: '8000'

# 5G-AKA算法
integrity: 'IA2'
ciphering: 'EA0'

# Default NSSAI
nssai:
  - sst: {ue_config.slice_nssai.get('sst', 1)}
    sd: '{ue_config.slice_nssai.get('sd', '000001')}'

# Configured NSSAI
configured-nssai:
  - sst: {ue_config.slice_nssai.get('sst', 1)}
    sd: '{ue_config.slice_nssai.get('sd', '000001')}'

# Default session information
sessions:
  - type: 'IPv4'
    apn: '{ue_config.apn}'
    slice:
      sst: {ue_config.slice_nssai.get('sst', 1)}
      sd: '{ue_config.slice_nssai.get('sd', '000001')}'

# UAV specific parameters for NTN
gnbSearchList:
  - '{ue_config.gnb_ip}:{ue_config.gnb_port}'

# NTN optimized parameters
nas-timer:
  t3502: 720  # 12 minutes for NTN environment
  t3511: 30   # Registration timer
  t3521: 30   # Deregistration timer

# UAV positioning
location:
  latitude: {uav_status.current_position.latitude if uav_status.current_position else 0.0}
  longitude: {uav_status.current_position.longitude if uav_status.current_position else 0.0}
  altitude: {uav_status.current_position.altitude if uav_status.current_position else 0.0}

# Power and RF parameters
rf:
  power: {ue_config.power_dbm}
  frequency: {ue_config.frequency_mhz}
  bandwidth: {ue_config.bandwidth_mhz}
  
# Logging
logs:
  - type: 'console'
    level: 'info'
"""

        config_file.write_text(config_content.strip())
        logger.info(
            "UERANSIM UE 配置文件生成",
            uav_id=uav_status.uav_id,
            config_file=str(config_file),
        )

        return str(config_file)

    async def _run_mission(self, uav_id: str, trajectory_id: str, speed_factor: float):
        """執行 UAV 任務主循環"""
        try:
            trajectory = await self.get_trajectory(trajectory_id)
            if not trajectory:
                return

            logger.info("開始執行 UAV 任務", uav_id=uav_id, trajectory_id=trajectory_id)

            for i, point in enumerate(trajectory.points):
                if self._shutdown_event.is_set():
                    break

                # 更新 UAV 位置
                position = UAVPosition(
                    latitude=point.latitude,
                    longitude=point.longitude,
                    altitude=point.altitude,
                    timestamp=datetime.utcnow(),
                    speed=point.speed,
                    heading=point.heading,
                )

                # 模擬信號質量
                signal_quality = await self._simulate_signal_quality(position)

                # 更新到資料庫
                await self.update_uav_position(
                    uav_id,
                    UAVPositionUpdateRequest(
                        position=position, signal_quality=signal_quality
                    ),
                )

                # 設定下一個目標點
                if i < len(trajectory.points) - 1:
                    next_point = trajectory.points[i + 1]
                    target_position = UAVPosition(
                        latitude=next_point.latitude,
                        longitude=next_point.longitude,
                        altitude=next_point.altitude,
                        timestamp=next_point.timestamp,
                    )

                    await self.mongo_adapter.update_one(
                        "uav_status",
                        {"uav_id": uav_id},
                        {"$set": {"target_position": target_position.dict()}},
                    )

                # 等待到下一個更新時間
                sleep_time = self.update_interval_sec / speed_factor
                await asyncio.sleep(sleep_time)

            # 任務完成
            await self.mongo_adapter.update_one(
                "uav_status",
                {"uav_id": uav_id},
                {
                    "$set": {
                        "flight_status": UAVFlightStatus.HOVERING.value,
                        "target_position": None,
                        "last_update": datetime.utcnow(),
                    }
                },
            )

            logger.info("UAV 任務完成", uav_id=uav_id)

        except asyncio.CancelledError:
            logger.info("UAV 任務被取消", uav_id=uav_id)
            raise
        except Exception as e:
            logger.error("UAV 任務執行錯誤", uav_id=uav_id, error=str(e))
            await self.mongo_adapter.update_one(
                "uav_status",
                {"uav_id": uav_id},
                {
                    "$set": {
                        "flight_status": UAVFlightStatus.EMERGENCY.value,
                        "ue_connection_status": UEConnectionStatus.ERROR.value,
                        "last_update": datetime.utcnow(),
                    }
                },
            )

    async def _simulate_signal_quality(self, position: UAVPosition) -> UAVSignalQuality:
        """模擬信號質量"""
        # 基於高度和位置的簡單信號模型
        altitude_factor = max(
            0.1, 1.0 - (position.altitude / 10000.0)
        )  # 高度越高信號越弱

        # 隨機變化模擬真實環境
        import random

        noise_factor = random.uniform(0.8, 1.2)

        base_rsrp = -70.0  # dBm
        rsrp = base_rsrp * altitude_factor * noise_factor

        rsrq = random.uniform(-15.0, -5.0)
        sinr = random.uniform(0.0, 20.0)
        cqi = min(15, max(0, int((sinr + 5) / 2)))

        return UAVSignalQuality(
            rsrp_dbm=rsrp,
            rsrq_db=rsrq,
            sinr_db=sinr,
            cqi=cqi,
            throughput_mbps=random.uniform(10.0, 100.0),
            latency_ms=random.uniform(20.0, 100.0),
            packet_loss_rate=random.uniform(0.0, 0.05),
        )

    async def _handle_signal_quality_change(
        self, uav_id: str, signal_quality: UAVSignalQuality
    ):
        """處理信號質量變化，實現自動切換"""
        # 如果信號質量太差，觸發切換到地面網路
        if (
            signal_quality.rsrp_dbm is not None and signal_quality.rsrp_dbm < -110.0
        ) or (signal_quality.sinr_db is not None and signal_quality.sinr_db < -5.0):

            logger.warning(
                "UAV 信號質量不佳，考慮切換網路",
                uav_id=uav_id,
                rsrp=signal_quality.rsrp_dbm,
                sinr=signal_quality.sinr_db,
            )

            # 更新連接狀態為切換中
            await self.mongo_adapter.update_one(
                "uav_status",
                {"uav_id": uav_id},
                {"$set": {"ue_connection_status": UEConnectionStatus.SWITCHING.value}},
            )

            # 這裡可以實現具體的切換邏輯
            # 例如調用 Slice Service 進行網路切換

    async def _update_sionna_channel_model(self, uav_id: str, position: UAVPosition):
        """更新 Sionna 信道模型"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.simworld_api_url}/api/v1/uav/position",
                    json={
                        "uav_id": uav_id,
                        "latitude": position.latitude,
                        "longitude": position.longitude,
                        "altitude": position.altitude,
                        "timestamp": position.timestamp.isoformat(),
                    },
                )

                if response.status_code == 200:
                    logger.debug("Sionna 位置更新成功", uav_id=uav_id)
                else:
                    logger.warning(
                        "Sionna 位置更新失敗",
                        uav_id=uav_id,
                        status_code=response.status_code,
                    )

        except Exception as e:
            logger.warning("無法連接到 SimWorld", error=str(e))
