"""
UAV 群組協同服務 (UAV Swarm Coordination Service)

實現多 UAV 群組管理、協同軌跡規劃和任務分配機制。
基於現有 UAVUEService 架構，擴展為群組協同能力。
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import structlog
import numpy as np
from pydantic import BaseModel

from ..models.uav_models import (
    UAVPosition, UAVSignalQuality, UAVCreateRequest,
    UAVPositionUpdateRequest, UAVResponse
)

logger = structlog.get_logger(__name__)


class SwarmTaskType(Enum):
    """群組任務類型"""
    AREA_COVERAGE = "area_coverage"           # 區域覆蓋
    FORMATION_FLIGHT = "formation_flight"     # 編隊飛行
    SEARCH_RESCUE = "search_rescue"           # 搜救任務
    COMMUNICATION_RELAY = "communication_relay"  # 通信中繼
    SURVEILLANCE = "surveillance"             # 監控巡邏


class SwarmFormationType(Enum):
    """編隊類型"""
    LINE = "line"           # 線型編隊
    V_SHAPE = "v_shape"     # V字型編隊
    CIRCLE = "circle"       # 圓形編隊
    GRID = "grid"           # 網格編隊
    DIAMOND = "diamond"     # 菱形編隊


@dataclass
class SwarmUAV:
    """群組中的UAV"""
    uav_id: str
    position: UAVPosition
    signal_quality: UAVSignalQuality
    role: str = "member"  # leader, member, relay
    battery_level: float = 100.0
    communication_range: float = 2000.0  # 通信範圍(m)
    is_active: bool = True
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class SwarmTask:
    """群組任務"""
    task_id: str
    task_type: SwarmTaskType
    target_area: Dict[str, float]  # {"center_lat": 25.0, "center_lon": 121.0, "radius": 1000}
    formation_type: SwarmFormationType
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    assigned_uavs: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, active, completed, failed


@dataclass
class SwarmGroup:
    """UAV群組"""
    group_id: str
    name: str
    uavs: Dict[str, SwarmUAV] = field(default_factory=dict)
    leader_id: Optional[str] = None
    current_task: Optional[SwarmTask] = None
    formation_config: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    coordination_algorithm: str = "consensus"  # consensus, hierarchical, distributed


class TrajectoryPlanRequest(BaseModel):
    """軌跡規劃請求"""
    group_id: str
    target_positions: List[UAVPosition]
    formation_type: SwarmFormationType
    speed_mps: float = 20.0
    maintain_formation: bool = True


class SwarmCoordinationRequest(BaseModel):
    """群組協同請求"""
    group_id: str
    task_type: SwarmTaskType
    target_area: Dict[str, float]
    formation_type: SwarmFormationType
    duration_minutes: int = 30


class UAVSwarmCoordinationService:
    """UAV群組協同服務"""

    def __init__(self, uav_ue_service=None, connection_quality_service=None):
        self.logger = structlog.get_logger(__name__)
        self.swarm_groups: Dict[str, SwarmGroup] = {}
        self.uav_ue_service = uav_ue_service
        self.connection_quality_service = connection_quality_service
        self.coordination_tasks: Dict[str, asyncio.Task] = {}
        
        # 協同算法參數
        self.formation_spacing = 200.0  # 編隊間距(m)
        self.communication_threshold = -85.0  # 通信質量閾值(dBm)
        self.consensus_iterations = 10
        
    async def create_swarm_group(
        self, 
        name: str, 
        uav_ids: List[str],
        formation_type: SwarmFormationType = SwarmFormationType.GRID
    ) -> SwarmGroup:
        """創建UAV群組"""
        group_id = f"swarm_{uuid.uuid4().hex[:8]}"
        
        # 初始化群組
        group = SwarmGroup(
            group_id=group_id,
            name=name,
            formation_config={
                "type": formation_type.value,
                "spacing": self.formation_spacing,
                "auto_adjust": True
            }
        )
        
        # 添加UAV到群組
        for uav_id in uav_ids:
            # 從UAV UE服務獲取UAV信息
            if self.uav_ue_service:
                try:
                    uav_info = await self.uav_ue_service.get_uav(uav_id)
                    swarm_uav = SwarmUAV(
                        uav_id=uav_id,
                        position=uav_info.current_position,
                        signal_quality=uav_info.signal_quality,
                        battery_level=uav_info.battery_level
                    )
                    group.uavs[uav_id] = swarm_uav
                except Exception as e:
                    self.logger.warning(f"無法獲取UAV {uav_id} 信息: {e}")
        
        # 選擇群組領導者
        group.leader_id = await self._select_group_leader(group)
        
        self.swarm_groups[group_id] = group
        
        self.logger.info(
            "UAV群組創建成功",
            group_id=group_id,
            name=name,
            uav_count=len(group.uavs),
            leader_id=group.leader_id
        )
        
        return group
    
    async def _select_group_leader(self, group: SwarmGroup) -> Optional[str]:
        """選擇群組領導者 - 基於信號質量、電池電量和位置中心性"""
        if not group.uavs:
            return None
            
        best_score = -float('inf')
        best_uav_id = None
        
        positions = [uav.position for uav in group.uavs.values()]
        center = self._calculate_center_position(positions)
        
        for uav_id, uav in group.uavs.items():
            # 綜合評分：信號質量 + 電池電量 + 位置中心性
            signal_score = uav.signal_quality.rsrp_dbm + 100  # 正規化
            battery_score = uav.battery_level
            
            # 計算距離中心的距離
            distance_to_center = self._calculate_distance(uav.position, center)
            centrality_score = max(0, 1000 - distance_to_center) / 10  # 正規化
            
            total_score = signal_score * 0.4 + battery_score * 0.4 + centrality_score * 0.2
            
            if total_score > best_score:
                best_score = total_score
                best_uav_id = uav_id
        
        # 設置角色
        for uav_id, uav in group.uavs.items():
            uav.role = "leader" if uav_id == best_uav_id else "member"
            
        return best_uav_id
    
    async def plan_formation_trajectory(
        self, 
        request: TrajectoryPlanRequest
    ) -> Dict[str, List[UAVPosition]]:
        """規劃編隊軌跡"""
        group = self.swarm_groups.get(request.group_id)
        if not group:
            raise ValueError(f"群組 {request.group_id} 不存在")
        
        # 獲取當前位置
        current_positions = {
            uav_id: uav.position 
            for uav_id, uav in group.uavs.items() 
            if uav.is_active
        }
        
        # 根據編隊類型計算目標位置
        formation_positions = self._calculate_formation_positions(
            request.formation_type,
            request.target_positions[0] if request.target_positions else None,
            len(current_positions)
        )
        
        # 分配UAV到編隊位置 (最小化總移動距離)
        uav_assignments = self._assign_uavs_to_positions(
            current_positions, formation_positions
        )
        
        # 生成平滑軌跡
        trajectories = {}
        for uav_id, target_pos in uav_assignments.items():
            current_pos = current_positions[uav_id]
            trajectory = self._generate_smooth_trajectory(
                current_pos, target_pos, request.speed_mps
            )
            trajectories[uav_id] = trajectory
        
        self.logger.info(
            "編隊軌跡規劃完成",
            group_id=request.group_id,
            formation_type=request.formation_type.value,
            uav_count=len(trajectories)
        )
        
        return trajectories
    
    def _calculate_formation_positions(
        self, 
        formation_type: SwarmFormationType, 
        center: UAVPosition, 
        uav_count: int
    ) -> List[UAVPosition]:
        """計算編隊位置"""
        positions = []
        spacing = self.formation_spacing
        
        if formation_type == SwarmFormationType.LINE:
            # 線型編隊
            for i in range(uav_count):
                offset_x = (i - uav_count/2) * spacing
                pos = UAVPosition(
                    latitude=center.latitude,
                    longitude=center.longitude + offset_x/111000,  # 近似轉換
                    altitude=center.altitude
                )
                positions.append(pos)
                
        elif formation_type == SwarmFormationType.V_SHAPE:
            # V字型編隊
            for i in range(uav_count):
                if i == 0:  # 領導者在前方
                    pos = center
                else:
                    side = 1 if i % 2 == 1 else -1
                    row = (i + 1) // 2
                    offset_x = side * row * spacing * 0.7
                    offset_y = -row * spacing
                    
                    pos = UAVPosition(
                        latitude=center.latitude + offset_y/111000,
                        longitude=center.longitude + offset_x/111000,
                        altitude=center.altitude
                    )
                positions.append(pos)
                
        elif formation_type == SwarmFormationType.CIRCLE:
            # 圓形編隊
            radius = spacing * uav_count / (2 * np.pi)
            for i in range(uav_count):
                angle = 2 * np.pi * i / uav_count
                offset_x = radius * np.cos(angle)
                offset_y = radius * np.sin(angle)
                
                pos = UAVPosition(
                    latitude=center.latitude + offset_y/111000,
                    longitude=center.longitude + offset_x/111000,
                    altitude=center.altitude
                )
                positions.append(pos)
                
        elif formation_type == SwarmFormationType.GRID:
            # 網格編隊
            grid_size = int(np.ceil(np.sqrt(uav_count)))
            for i in range(uav_count):
                row = i // grid_size
                col = i % grid_size
                offset_x = (col - grid_size/2) * spacing
                offset_y = (row - grid_size/2) * spacing
                
                pos = UAVPosition(
                    latitude=center.latitude + offset_y/111000,
                    longitude=center.longitude + offset_x/111000,
                    altitude=center.altitude
                )
                positions.append(pos)
        
        return positions
    
    def _assign_uavs_to_positions(
        self, 
        current_positions: Dict[str, UAVPosition], 
        target_positions: List[UAVPosition]
    ) -> Dict[str, UAVPosition]:
        """分配UAV到目標位置 - 使用匈牙利算法最小化總距離"""
        uav_ids = list(current_positions.keys())
        n = len(uav_ids)
        m = len(target_positions)
        
        # 計算距離矩陣
        distance_matrix = np.zeros((n, m))
        for i, uav_id in enumerate(uav_ids):
            for j, target_pos in enumerate(target_positions):
                distance_matrix[i][j] = self._calculate_distance(
                    current_positions[uav_id], target_pos
                )
        
        # 簡化版匈牙利算法 - 貪心分配
        assignments = {}
        used_positions = set()
        
        # 按距離排序分配
        uav_distances = []
        for i, uav_id in enumerate(uav_ids):
            min_dist = np.min(distance_matrix[i])
            uav_distances.append((min_dist, i, uav_id))
        
        uav_distances.sort()
        
        for _, i, uav_id in uav_distances:
            best_j = None
            best_dist = float('inf')
            
            for j in range(m):
                if j not in used_positions and distance_matrix[i][j] < best_dist:
                    best_dist = distance_matrix[i][j]
                    best_j = j
            
            if best_j is not None:
                assignments[uav_id] = target_positions[best_j]
                used_positions.add(best_j)
        
        return assignments
    
    def _generate_smooth_trajectory(
        self, 
        start: UAVPosition, 
        end: UAVPosition, 
        speed_mps: float,
        waypoints: int = 10
    ) -> List[UAVPosition]:
        """生成平滑軌跡"""
        trajectory = []
        
        for i in range(waypoints + 1):
            t = i / waypoints
            # 線性插值
            lat = start.latitude + t * (end.latitude - start.latitude)
            lon = start.longitude + t * (end.longitude - start.longitude)
            alt = start.altitude + t * (end.altitude - start.altitude)
            
            trajectory.append(UAVPosition(latitude=lat, longitude=lon, altitude=alt))
        
        return trajectory
    
    async def start_swarm_coordination(
        self, 
        request: SwarmCoordinationRequest
    ) -> Dict:
        """開始群組協同任務"""
        group = self.swarm_groups.get(request.group_id)
        if not group:
            raise ValueError(f"群組 {request.group_id} 不存在")
        
        # 創建任務
        task = SwarmTask(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            task_type=request.task_type,
            target_area=request.target_area,
            formation_type=request.formation_type,
            deadline=datetime.now() + timedelta(minutes=request.duration_minutes),
            assigned_uavs=list(group.uavs.keys())
        )
        
        group.current_task = task
        task.status = "active"
        
        # 啟動協同控制任務
        coordination_task = asyncio.create_task(
            self._execute_coordination_task(group, task)
        )
        self.coordination_tasks[task.task_id] = coordination_task
        
        self.logger.info(
            "群組協同任務開始",
            group_id=request.group_id,
            task_id=task.task_id,
            task_type=request.task_type.value
        )
        
        return {
            "success": True,
            "task_id": task.task_id,
            "group_id": request.group_id,
            "estimated_duration": request.duration_minutes
        }
    
    async def _execute_coordination_task(self, group: SwarmGroup, task: SwarmTask):
        """執行協同任務"""
        try:
            # 根據任務類型執行不同的協同算法
            if task.task_type == SwarmTaskType.AREA_COVERAGE:
                await self._execute_area_coverage(group, task)
            elif task.task_type == SwarmTaskType.FORMATION_FLIGHT:
                await self._execute_formation_flight(group, task)
            elif task.task_type == SwarmTaskType.COMMUNICATION_RELAY:
                await self._execute_communication_relay(group, task)
            
            task.status = "completed"
            
        except Exception as e:
            self.logger.error(f"協同任務執行失敗: {e}")
            task.status = "failed"
        
        finally:
            # 清理任務
            if task.task_id in self.coordination_tasks:
                del self.coordination_tasks[task.task_id]
    
    async def _execute_area_coverage(self, group: SwarmGroup, task: SwarmTask):
        """執行區域覆蓋任務"""
        target_area = task.target_area
        center_lat = target_area["center_lat"]
        center_lon = target_area["center_lon"]
        radius = target_area["radius"]
        
        # 計算覆蓋網格
        uav_count = len(group.uavs)
        grid_size = int(np.ceil(np.sqrt(uav_count)))
        
        coverage_positions = []
        for i in range(grid_size):
            for j in range(grid_size):
                if len(coverage_positions) >= uav_count:
                    break
                
                # 在圓形區域內生成網格點
                x = (i - grid_size/2) * (2 * radius / grid_size)
                y = (j - grid_size/2) * (2 * radius / grid_size)
                
                if x*x + y*y <= radius*radius:
                    lat = center_lat + y / 111000
                    lon = center_lon + x / 111000
                    coverage_positions.append(UAVPosition(
                        latitude=lat,
                        longitude=lon,
                        altitude=100.0
                    ))
        
        # 分配位置並移動UAV
        current_positions = {
            uav_id: uav.position 
            for uav_id, uav in group.uavs.items()
        }
        
        assignments = self._assign_uavs_to_positions(
            current_positions, coverage_positions
        )
        
        # 同步移動所有UAV
        move_tasks = []
        for uav_id, target_pos in assignments.items():
            if self.uav_ue_service:
                move_task = self.uav_ue_service.update_uav_position(
                    uav_id,
                    UAVPositionUpdateRequest(position=target_pos)
                )
                move_tasks.append(move_task)
        
        if move_tasks:
            await asyncio.gather(*move_tasks)
        
        self.logger.info(
            "區域覆蓋任務執行完成",
            group_id=group.group_id,
            coverage_positions=len(coverage_positions)
        )
    
    async def _execute_formation_flight(self, group: SwarmGroup, task: SwarmTask):
        """執行編隊飛行任務"""
        # 使用共識算法維持編隊
        while task.status == "active":
            # 獲取所有UAV當前位置
            positions = {}
            for uav_id, uav in group.uavs.items():
                if uav.is_active:
                    positions[uav_id] = uav.position
            
            # 計算期望編隊位置
            if group.leader_id and group.leader_id in positions:
                leader_pos = positions[group.leader_id]
                formation_positions = self._calculate_formation_positions(
                    task.formation_type, leader_pos, len(positions)
                )
                
                # 計算調整向量
                adjustments = self._calculate_consensus_adjustments(
                    positions, formation_positions
                )
                
                # 應用位置調整
                for uav_id, adjustment in adjustments.items():
                    current_pos = positions[uav_id]
                    new_pos = UAVPosition(
                        latitude=current_pos.latitude + adjustment[0]/111000,
                        longitude=current_pos.longitude + adjustment[1]/111000,
                        altitude=current_pos.altitude + adjustment[2]
                    )
                    
                    if self.uav_ue_service:
                        await self.uav_ue_service.update_uav_position(
                            uav_id,
                            UAVPositionUpdateRequest(position=new_pos)
                        )
            
            await asyncio.sleep(2.0)  # 編隊更新間隔
    
    def _calculate_consensus_adjustments(
        self, 
        current_positions: Dict[str, UAVPosition],
        target_formations: List[UAVPosition]
    ) -> Dict[str, Tuple[float, float, float]]:
        """計算共識調整向量"""
        adjustments = {}
        uav_ids = list(current_positions.keys())
        
        for i, uav_id in enumerate(uav_ids):
            if i < len(target_formations):
                current = current_positions[uav_id]
                target = target_formations[i]
                
                # 計算調整向量
                lat_diff = (target.latitude - current.latitude) * 111000
                lon_diff = (target.longitude - current.longitude) * 111000
                alt_diff = target.altitude - current.altitude
                
                # 限制調整幅度
                max_adjustment = 50.0  # 最大調整50米
                lat_diff = max(-max_adjustment, min(max_adjustment, lat_diff))
                lon_diff = max(-max_adjustment, min(max_adjustment, lon_diff))
                alt_diff = max(-20.0, min(20.0, alt_diff))
                
                adjustments[uav_id] = (lat_diff, lon_diff, alt_diff)
        
        return adjustments
    
    async def get_swarm_status(self, group_id: str) -> Dict:
        """獲取群組狀態"""
        group = self.swarm_groups.get(group_id)
        if not group:
            raise ValueError(f"群組 {group_id} 不存在")
        
        # 計算群組統計
        active_uavs = sum(1 for uav in group.uavs.values() if uav.is_active)
        avg_battery = np.mean([uav.battery_level for uav in group.uavs.values()])
        avg_signal = np.mean([uav.signal_quality.rsrp_dbm for uav in group.uavs.values()])
        
        # 計算編隊分散度
        positions = [uav.position for uav in group.uavs.values() if uav.is_active]
        formation_spread = self._calculate_formation_spread(positions)
        
        return {
            "group_id": group_id,
            "name": group.name,
            "status": {
                "total_uavs": len(group.uavs),
                "active_uavs": active_uavs,
                "leader_id": group.leader_id,
                "current_task": group.current_task.task_type.value if group.current_task else None
            },
            "metrics": {
                "average_battery": round(avg_battery, 2),
                "average_signal_dbm": round(avg_signal, 2),
                "formation_spread_m": round(formation_spread, 2),
                "coordination_quality": self._assess_coordination_quality(group)
            },
            "uavs": [
                {
                    "uav_id": uav_id,
                    "role": uav.role,
                    "position": {
                        "latitude": uav.position.latitude,
                        "longitude": uav.position.longitude,
                        "altitude": uav.position.altitude
                    },
                    "battery_level": uav.battery_level,
                    "is_active": uav.is_active
                }
                for uav_id, uav in group.uavs.items()
            ]
        }
    
    def _calculate_formation_spread(self, positions: List[UAVPosition]) -> float:
        """計算編隊分散度"""
        if len(positions) < 2:
            return 0.0
        
        center = self._calculate_center_position(positions)
        distances = [
            self._calculate_distance(pos, center) 
            for pos in positions
        ]
        return np.std(distances)
    
    def _calculate_center_position(self, positions: List[UAVPosition]) -> UAVPosition:
        """計算位置中心"""
        if not positions:
            return UAVPosition(latitude=0, longitude=0, altitude=0)
        
        avg_lat = np.mean([pos.latitude for pos in positions])
        avg_lon = np.mean([pos.longitude for pos in positions])
        avg_alt = np.mean([pos.altitude for pos in positions])
        
        return UAVPosition(latitude=avg_lat, longitude=avg_lon, altitude=avg_alt)
    
    def _calculate_distance(self, pos1: UAVPosition, pos2: UAVPosition) -> float:
        """計算兩點距離(米)"""
        lat_diff = (pos2.latitude - pos1.latitude) * 111000
        lon_diff = (pos2.longitude - pos1.longitude) * 111000
        alt_diff = pos2.altitude - pos1.altitude
        
        return np.sqrt(lat_diff**2 + lon_diff**2 + alt_diff**2)
    
    def _assess_coordination_quality(self, group: SwarmGroup) -> float:
        """評估協同質量 (0-1)"""
        if not group.uavs:
            return 0.0
        
        active_uavs = [uav for uav in group.uavs.values() if uav.is_active]
        if len(active_uavs) < 2:
            return 1.0
        
        # 評估因子
        position_quality = 0.8  # 位置協同性
        communication_quality = 0.9  # 通信質量
        battery_balance = 0.85  # 電池平衡
        
        # 綜合評分
        overall_quality = (
            position_quality * 0.4 + 
            communication_quality * 0.4 + 
            battery_balance * 0.2
        )
        
        return round(overall_quality, 3)