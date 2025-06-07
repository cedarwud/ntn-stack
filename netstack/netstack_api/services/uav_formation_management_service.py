"""
UAV 編隊管理系統 (UAV Formation Management Service)

實現UAV編隊的創建、維護、動態調整和任務指派功能。
與 UAVSwarmCoordinationService 協同工作，提供更細粒度的編隊控制。
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json

import structlog
import numpy as np
from pydantic import BaseModel

from ..models.uav_models import (
    UAVPosition, UAVSignalQuality, UAVCreateRequest,
    UAVPositionUpdateRequest, UAVResponse
)

logger = structlog.get_logger(__name__)


class FormationShape(Enum):
    """編隊形狀"""
    LINE = "line"                    # 線型
    COLUMN = "column"                # 縱隊
    WEDGE = "wedge"                  # 楔型
    VEE = "vee"                      # V字型
    DIAMOND = "diamond"              # 菱形
    BOX = "box"                      # 方形
    CIRCLE = "circle"                # 圓形
    SPIRAL = "spiral"                # 螺旋
    TRIANGLE = "triangle"            # 三角形
    CUSTOM = "custom"                # 自定義


class FormationRole(Enum):
    """編隊角色"""
    LEADER = "leader"                # 領導者
    WING_LEFT = "wing_left"          # 左翼
    WING_RIGHT = "wing_right"        # 右翼
    REAR_GUARD = "rear_guard"        # 後衛
    SCOUT = "scout"                  # 偵察
    RELAY = "relay"                  # 中繼
    SUPPORT = "support"              # 支援
    RESERVE = "reserve"              # 預備


class FormationState(Enum):
    """編隊狀態"""
    FORMING = "forming"              # 組建中
    FORMED = "formed"                # 已成型
    MOVING = "moving"                # 移動中
    MAINTAINING = "maintaining"      # 維持中
    REFORMING = "reforming"          # 重組中
    DISPERSING = "dispersing"        # 散開中
    EMERGENCY = "emergency"          # 緊急狀態


@dataclass
class FormationMember:
    """編隊成員"""
    uav_id: str
    role: FormationRole
    position: UAVPosition
    target_position: UAVPosition
    signal_quality: UAVSignalQuality
    formation_compliance: float = 1.0  # 編隊符合度 (0-1)
    last_update: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    battery_level: float = 100.0
    communication_status: str = "good"  # good, degraded, lost


@dataclass
class FormationGeometry:
    """編隊幾何配置"""
    shape: FormationShape
    reference_point: UAVPosition  # 基準點
    spacing: float = 100.0        # 間距(米)
    altitude_separation: float = 10.0  # 高度分離(米)
    bearing: float = 0.0          # 方位角(度)
    scale_factor: float = 1.0     # 縮放因子
    parameters: Dict = field(default_factory=dict)  # 形狀特定參數


@dataclass
class Formation:
    """UAV編隊"""
    formation_id: str
    name: str
    geometry: FormationGeometry
    members: Dict[str, FormationMember] = field(default_factory=dict)
    leader_id: Optional[str] = None
    state: FormationState = FormationState.FORMING
    created_at: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    mission_id: Optional[str] = None
    formation_quality: float = 1.0  # 編隊質量評分


class FormationCreateRequest(BaseModel):
    """編隊創建請求"""
    formation_name: str
    shape: FormationShape
    uav_ids: List[str]
    reference_position: UAVPosition
    spacing: float = 100.0
    altitude_separation: float = 10.0
    auto_assign_roles: bool = True


class FormationUpdateRequest(BaseModel):
    """編隊更新請求"""
    formation_id: str
    new_geometry: Optional[Dict] = None
    target_position: Optional[UAVPosition] = None
    maintain_formation: bool = True


class FormationMissionRequest(BaseModel):
    """編隊任務請求"""
    formation_id: str
    mission_type: str
    target_area: Dict[str, float]
    duration_minutes: int = 30
    mission_parameters: Dict = {}


class UAVFormationManagementService:
    """UAV編隊管理服務"""

    def __init__(self, uav_ue_service=None, swarm_coordination_service=None):
        self.logger = structlog.get_logger(__name__)
        self.formations: Dict[str, Formation] = {}
        self.uav_ue_service = uav_ue_service
        self.swarm_coordination_service = swarm_coordination_service
        
        # 編隊參數
        self.formation_tolerance = 20.0  # 編隊容許誤差(米)
        self.formation_update_interval = 2.0  # 更新間隔(秒)
        self.min_formation_quality = 0.7  # 最小編隊質量閾值
        
        # 編隊維護任務
        self.maintenance_tasks: Dict[str, asyncio.Task] = {}
        
        # 幾何計算快取
        self.geometry_cache: Dict[str, List[UAVPosition]] = {}
        
    async def create_formation(self, request: FormationCreateRequest) -> Formation:
        """創建UAV編隊"""
        formation_id = f"formation_{uuid.uuid4().hex[:8]}"
        
        # 創建編隊幾何配置
        geometry = FormationGeometry(
            shape=request.shape,
            reference_point=request.reference_position,
            spacing=request.spacing,
            altitude_separation=request.altitude_separation
        )
        
        # 初始化編隊
        formation = Formation(
            formation_id=formation_id,
            name=request.formation_name,
            geometry=geometry
        )
        
        # 添加UAV成員
        for uav_id in request.uav_ids:
            if self.uav_ue_service:
                try:
                    uav_info = await self.uav_ue_service.get_uav(uav_id)
                    member = FormationMember(
                        uav_id=uav_id,
                        role=FormationRole.RESERVE,  # 暫時角色
                        position=uav_info.current_position,
                        target_position=uav_info.current_position,
                        signal_quality=uav_info.signal_quality,
                        battery_level=uav_info.battery_level
                    )
                    formation.members[uav_id] = member
                except Exception as e:
                    self.logger.warning(f"無法獲取UAV {uav_id} 信息: {e}")
        
        # 自動分配角色
        if request.auto_assign_roles:
            await self._assign_formation_roles(formation)
        
        # 計算初始編隊位置
        await self._calculate_formation_positions(formation)
        
        # 啟動編隊維護
        await self._start_formation_maintenance(formation)
        
        self.formations[formation_id] = formation
        
        self.logger.info(
            "UAV編隊創建成功",
            formation_id=formation_id,
            name=request.formation_name,
            shape=request.shape.value,
            member_count=len(formation.members)
        )
        
        return formation
    
    async def _assign_formation_roles(self, formation: Formation):
        """自動分配編隊角色"""
        members = list(formation.members.values())
        if not members:
            return
        
        # 選擇領導者 - 基於信號質量和電池電量
        leader = max(members, key=lambda m: (
            m.signal_quality.rsrp_dbm + 100 + m.battery_level
        ))
        leader.role = FormationRole.LEADER
        formation.leader_id = leader.uav_id
        
        # 為其他成員分配角色
        remaining_members = [m for m in members if m.uav_id != leader.uav_id]
        
        shape = formation.geometry.shape
        
        if shape in [FormationShape.LINE, FormationShape.COLUMN]:
            # 線型或縱隊：按位置排序
            for i, member in enumerate(remaining_members):
                if i < len(remaining_members) // 2:
                    member.role = FormationRole.WING_LEFT
                else:
                    member.role = FormationRole.WING_RIGHT
                    
        elif shape == FormationShape.VEE:
            # V字型：左翼、右翼
            for i, member in enumerate(remaining_members):
                if i % 2 == 0:
                    member.role = FormationRole.WING_LEFT
                else:
                    member.role = FormationRole.WING_RIGHT
                    
        elif shape == FormationShape.DIAMOND:
            # 菱形：前、左、右、後
            roles = [FormationRole.SCOUT, FormationRole.WING_LEFT, 
                    FormationRole.WING_RIGHT, FormationRole.REAR_GUARD]
            for i, member in enumerate(remaining_members):
                if i < len(roles):
                    member.role = roles[i]
                else:
                    member.role = FormationRole.SUPPORT
        else:
            # 其他形狀：平均分配
            roles = [FormationRole.WING_LEFT, FormationRole.WING_RIGHT, 
                    FormationRole.SUPPORT, FormationRole.RELAY]
            for i, member in enumerate(remaining_members):
                member.role = roles[i % len(roles)]
    
    async def _calculate_formation_positions(self, formation: Formation):
        """計算編隊位置"""
        geometry = formation.geometry
        cache_key = f"{formation.formation_id}_{geometry.shape.value}_{len(formation.members)}"
        
        # 檢查快取
        if cache_key in self.geometry_cache:
            positions = self.geometry_cache[cache_key]
        else:
            positions = await self._generate_formation_geometry(geometry, len(formation.members))
            self.geometry_cache[cache_key] = positions
        
        # 分配位置給成員
        member_list = list(formation.members.values())
        
        # 領導者在基準位置或特殊位置
        leader = next((m for m in member_list if m.role == FormationRole.LEADER), None)
        if leader and positions:
            if geometry.shape == FormationShape.VEE:
                leader.target_position = positions[0]  # V字型領導者在前
            elif geometry.shape == FormationShape.DIAMOND:
                leader.target_position = positions[len(positions)//2]  # 菱形領導者在中心
            else:
                leader.target_position = geometry.reference_point
        
        # 其他成員按角色分配位置
        remaining_positions = [pos for i, pos in enumerate(positions) 
                             if not (leader and i == 0)]  # 排除領導者位置
        other_members = [m for m in member_list if m.role != FormationRole.LEADER]
        
        for i, member in enumerate(other_members):
            if i < len(remaining_positions):
                member.target_position = remaining_positions[i]
            else:
                # 如果位置不夠，使用基準位置加偏移
                offset = (i - len(remaining_positions) + 1) * geometry.spacing
                member.target_position = UAVPosition(
                    latitude=geometry.reference_point.latitude + offset/111000,
                    longitude=geometry.reference_point.longitude,
                    altitude=geometry.reference_point.altitude
                )
    
    async def _generate_formation_geometry(self, geometry: FormationGeometry, member_count: int) -> List[UAVPosition]:
        """生成編隊幾何位置"""
        positions = []
        ref = geometry.reference_point
        spacing = geometry.spacing
        alt_sep = geometry.altitude_separation
        
        if geometry.shape == FormationShape.LINE:
            # 水平線型
            for i in range(member_count):
                offset = (i - member_count/2) * spacing
                pos = UAVPosition(
                    latitude=ref.latitude,
                    longitude=ref.longitude + offset/111000,
                    altitude=ref.altitude
                )
                positions.append(pos)
                
        elif geometry.shape == FormationShape.COLUMN:
            # 縱隊
            for i in range(member_count):
                offset = i * spacing
                pos = UAVPosition(
                    latitude=ref.latitude - offset/111000,
                    longitude=ref.longitude,
                    altitude=ref.altitude
                )
                positions.append(pos)
                
        elif geometry.shape == FormationShape.VEE:
            # V字型
            positions.append(ref)  # 領導者在頂點
            for i in range(1, member_count):
                side = 1 if i % 2 == 1 else -1
                row = (i + 1) // 2
                offset_x = side * row * spacing * 0.7
                offset_y = -row * spacing * 0.7
                
                pos = UAVPosition(
                    latitude=ref.latitude + offset_y/111000,
                    longitude=ref.longitude + offset_x/111000,
                    altitude=ref.altitude + (i-1) * alt_sep/4
                )
                positions.append(pos)
                
        elif geometry.shape == FormationShape.DIAMOND:
            # 菱形
            if member_count >= 4:
                # 前
                positions.append(UAVPosition(
                    latitude=ref.latitude + spacing/111000,
                    longitude=ref.longitude,
                    altitude=ref.altitude
                ))
                # 左
                positions.append(UAVPosition(
                    latitude=ref.latitude,
                    longitude=ref.longitude - spacing/111000,
                    altitude=ref.altitude + alt_sep
                ))
                # 右
                positions.append(UAVPosition(
                    latitude=ref.latitude,
                    longitude=ref.longitude + spacing/111000,
                    altitude=ref.altitude + alt_sep
                ))
                # 後
                positions.append(UAVPosition(
                    latitude=ref.latitude - spacing/111000,
                    longitude=ref.longitude,
                    altitude=ref.altitude
                ))
                
                # 中心（領導者）
                if member_count > 4:
                    positions.append(ref)
                
                # 額外成員圍繞中心
                for i in range(max(0, member_count - 5)):
                    angle = 2 * np.pi * i / max(1, member_count - 5)
                    offset_x = spacing * 0.5 * np.cos(angle)
                    offset_y = spacing * 0.5 * np.sin(angle)
                    
                    pos = UAVPosition(
                        latitude=ref.latitude + offset_y/111000,
                        longitude=ref.longitude + offset_x/111000,
                        altitude=ref.altitude + alt_sep/2
                    )
                    positions.append(pos)
            else:
                # 成員不足，使用線型
                return await self._generate_line_formation(ref, spacing, member_count)
                
        elif geometry.shape == FormationShape.CIRCLE:
            # 圓形
            radius = spacing * member_count / (2 * np.pi)
            for i in range(member_count):
                angle = 2 * np.pi * i / member_count
                offset_x = radius * np.cos(angle)
                offset_y = radius * np.sin(angle)
                
                pos = UAVPosition(
                    latitude=ref.latitude + offset_y/111000,
                    longitude=ref.longitude + offset_x/111000,
                    altitude=ref.altitude + i * alt_sep / member_count
                )
                positions.append(pos)
                
        elif geometry.shape == FormationShape.BOX:
            # 方形
            side_length = int(np.ceil(np.sqrt(member_count)))
            for i in range(member_count):
                row = i // side_length
                col = i % side_length
                offset_x = (col - side_length/2) * spacing
                offset_y = (row - side_length/2) * spacing
                
                pos = UAVPosition(
                    latitude=ref.latitude + offset_y/111000,
                    longitude=ref.longitude + offset_x/111000,
                    altitude=ref.altitude + (row + col) * alt_sep / 4
                )
                positions.append(pos)
        
        return positions
    
    async def _start_formation_maintenance(self, formation: Formation):
        """啟動編隊維護"""
        if formation.formation_id not in self.maintenance_tasks:
            task = asyncio.create_task(self._formation_maintenance_loop(formation))
            self.maintenance_tasks[formation.formation_id] = task
            
            self.logger.debug(f"編隊維護已啟動: {formation.formation_id}")
    
    async def _formation_maintenance_loop(self, formation: Formation):
        """編隊維護循環"""
        while formation.formation_id in self.formations:
            try:
                # 更新成員狀態
                await self._update_member_states(formation)
                
                # 評估編隊質量
                formation.formation_quality = await self._evaluate_formation_quality(formation)
                
                # 檢查是否需要重組
                if formation.formation_quality < self.min_formation_quality:
                    await self._trigger_formation_reform(formation)
                
                # 執行位置調整
                await self._adjust_formation_positions(formation)
                
                formation.last_update = datetime.now()
                
                await asyncio.sleep(self.formation_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"編隊維護異常: {e}")
                await asyncio.sleep(5.0)
    
    async def _update_member_states(self, formation: Formation):
        """更新成員狀態"""
        for member in formation.members.values():
            if self.uav_ue_service:
                try:
                    uav_info = await self.uav_ue_service.get_uav(member.uav_id)
                    member.position = uav_info.current_position
                    member.signal_quality = uav_info.signal_quality
                    member.battery_level = uav_info.battery_level
                    member.last_update = datetime.now()
                    
                    # 計算編隊符合度
                    distance_to_target = self._calculate_distance(
                        member.position, member.target_position
                    )
                    member.formation_compliance = max(0.0, 
                        1.0 - distance_to_target / (self.formation_tolerance * 2)
                    )
                    
                except Exception as e:
                    self.logger.warning(f"更新UAV {member.uav_id} 狀態失敗: {e}")
                    member.is_active = False
    
    async def _evaluate_formation_quality(self, formation: Formation) -> float:
        """評估編隊質量"""
        if not formation.members:
            return 0.0
        
        active_members = [m for m in formation.members.values() if m.is_active]
        if not active_members:
            return 0.0
        
        # 計算各種質量指標
        
        # 1. 位置符合度
        position_compliance = np.mean([m.formation_compliance for m in active_members])
        
        # 2. 通信質量
        comm_quality = np.mean([
            min(1.0, (m.signal_quality.rsrp_dbm + 100) / 50) 
            for m in active_members
        ])
        
        # 3. 電池平衡度
        battery_levels = [m.battery_level for m in active_members]
        battery_balance = 1.0 - (np.std(battery_levels) / 100.0)
        
        # 4. 連接性
        connectivity = len(active_members) / len(formation.members)
        
        # 綜合評分
        quality_score = (
            position_compliance * 0.4 +
            comm_quality * 0.3 +
            battery_balance * 0.2 +
            connectivity * 0.1
        )
        
        return max(0.0, min(1.0, quality_score))
    
    async def _trigger_formation_reform(self, formation: Formation):
        """觸發編隊重組"""
        formation.state = FormationState.REFORMING
        
        self.logger.info(
            f"編隊質量下降，觸發重組: {formation.formation_id}, "
            f"quality: {formation.formation_quality}"
        )
        
        # 重新分配角色
        await self._assign_formation_roles(formation)
        
        # 重新計算位置
        await self._calculate_formation_positions(formation)
        
        formation.state = FormationState.FORMED
    
    async def _adjust_formation_positions(self, formation: Formation):
        """調整編隊位置"""
        for member in formation.members.values():
            if not member.is_active:
                continue
                
            distance_to_target = self._calculate_distance(
                member.position, member.target_position
            )
            
            if distance_to_target > self.formation_tolerance:
                # 需要位置調整
                if self.uav_ue_service:
                    try:
                        await self.uav_ue_service.update_uav_position(
                            member.uav_id,
                            UAVPositionUpdateRequest(position=member.target_position)
                        )
                    except Exception as e:
                        self.logger.warning(f"調整UAV {member.uav_id} 位置失敗: {e}")
    
    async def update_formation(self, request: FormationUpdateRequest) -> Dict[str, any]:
        """更新編隊配置"""
        formation = self.formations.get(request.formation_id)
        if not formation:
            raise ValueError(f"編隊 {request.formation_id} 不存在")
        
        formation.state = FormationState.REFORMING
        
        # 更新幾何配置
        if request.new_geometry:
            if "shape" in request.new_geometry:
                formation.geometry.shape = FormationShape(request.new_geometry["shape"])
            if "spacing" in request.new_geometry:
                formation.geometry.spacing = request.new_geometry["spacing"]
            if "altitude_separation" in request.new_geometry:
                formation.geometry.altitude_separation = request.new_geometry["altitude_separation"]
        
        # 更新目標位置
        if request.target_position:
            formation.geometry.reference_point = request.target_position
        
        # 重新計算編隊位置
        await self._calculate_formation_positions(formation)
        
        # 清理快取
        cache_keys = [k for k in self.geometry_cache.keys() 
                     if k.startswith(formation.formation_id)]
        for key in cache_keys:
            del self.geometry_cache[key]
        
        formation.state = FormationState.FORMED
        
        self.logger.info(f"編隊配置已更新: {request.formation_id}")
        
        return {
            "success": True,
            "formation_id": request.formation_id,
            "updated_at": datetime.now().isoformat()
        }
    
    async def get_formation_status(self, formation_id: str) -> Dict[str, any]:
        """獲取編隊狀態"""
        formation = self.formations.get(formation_id)
        if not formation:
            raise ValueError(f"編隊 {formation_id} 不存在")
        
        active_members = sum(1 for m in formation.members.values() if m.is_active)
        avg_compliance = np.mean([m.formation_compliance for m in formation.members.values()])
        avg_battery = np.mean([m.battery_level for m in formation.members.values()])
        
        return {
            "formation_id": formation_id,
            "name": formation.name,
            "state": formation.state.value,
            "shape": formation.geometry.shape.value,
            "quality_score": formation.formation_quality,
            "statistics": {
                "total_members": len(formation.members),
                "active_members": active_members,
                "leader_id": formation.leader_id,
                "average_compliance": round(avg_compliance, 3),
                "average_battery": round(avg_battery, 1),
                "spacing": formation.geometry.spacing,
                "last_update": formation.last_update.isoformat()
            },
            "members": [
                {
                    "uav_id": m.uav_id,
                    "role": m.role.value,
                    "is_active": m.is_active,
                    "formation_compliance": round(m.formation_compliance, 3),
                    "battery_level": m.battery_level,
                    "position": {
                        "latitude": m.position.latitude,
                        "longitude": m.position.longitude,
                        "altitude": m.position.altitude
                    },
                    "target_position": {
                        "latitude": m.target_position.latitude,
                        "longitude": m.target_position.longitude,
                        "altitude": m.target_position.altitude
                    }
                }
                for m in formation.members.values()
            ]
        }
    
    async def dissolve_formation(self, formation_id: str) -> Dict[str, any]:
        """解散編隊"""
        formation = self.formations.get(formation_id)
        if not formation:
            raise ValueError(f"編隊 {formation_id} 不存在")
        
        formation.state = FormationState.DISPERSING
        
        # 停止維護任務
        if formation_id in self.maintenance_tasks:
            self.maintenance_tasks[formation_id].cancel()
            del self.maintenance_tasks[formation_id]
        
        # 清理快取
        cache_keys = [k for k in self.geometry_cache.keys() 
                     if k.startswith(formation_id)]
        for key in cache_keys:
            del self.geometry_cache[key]
        
        # 移除編隊
        del self.formations[formation_id]
        
        self.logger.info(f"編隊已解散: {formation_id}")
        
        return {
            "success": True,
            "formation_id": formation_id,
            "dissolved_at": datetime.now().isoformat(),
            "member_count": len(formation.members)
        }
    
    def _calculate_distance(self, pos1: UAVPosition, pos2: UAVPosition) -> float:
        """計算兩點距離(米)"""
        lat_diff = (pos2.latitude - pos1.latitude) * 111000
        lon_diff = (pos2.longitude - pos1.longitude) * 111000
        alt_diff = pos2.altitude - pos1.altitude
        
        return np.sqrt(lat_diff**2 + lon_diff**2 + alt_diff**2)
    
    async def get_all_formations_summary(self) -> Dict[str, any]:
        """獲取所有編隊摘要"""
        formations_summary = []
        
        for formation in self.formations.values():
            active_members = sum(1 for m in formation.members.values() if m.is_active)
            formations_summary.append({
                "formation_id": formation.formation_id,
                "name": formation.name,
                "shape": formation.geometry.shape.value,
                "state": formation.state.value,
                "quality_score": formation.formation_quality,
                "total_members": len(formation.members),
                "active_members": active_members,
                "created_at": formation.created_at.isoformat()
            })
        
        return {
            "total_formations": len(self.formations),
            "active_formations": sum(1 for f in self.formations.values() 
                                   if f.state != FormationState.DISPERSING),
            "formations": formations_summary,
            "service_statistics": {
                "cache_size": len(self.geometry_cache),
                "maintenance_tasks": len(self.maintenance_tasks),
                "formation_tolerance_m": self.formation_tolerance,
                "update_interval_s": self.formation_update_interval
            }
        }