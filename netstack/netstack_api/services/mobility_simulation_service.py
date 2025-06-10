"""
IEEE INFOCOM 2024 多使用者移動模式模擬服務
實現各種真實世界移動模式，用於驗證換手機制在不同場景下的性能
"""

import asyncio
import time
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MobilityPattern(Enum):
    """移動模式類型"""
    STATIONARY = "STATIONARY"
    LINEAR = "LINEAR"
    RANDOM_WALK = "RANDOM_WALK"
    CIRCULAR = "CIRCULAR"
    HIGHWAY = "HIGHWAY"
    URBAN = "URBAN"
    MANHATTAN = "MANHATTAN"
    RANDOM_WAYPOINT = "RANDOM_WAYPOINT"
    REFERENCE_POINT_GROUP = "REFERENCE_POINT_GROUP"
    CLUSTER_BASED = "CLUSTER_BASED"


class UAVFlightPattern(Enum):
    """UAV 飛行模式"""
    PATROL = "PATROL"
    SEARCH_RESCUE = "SEARCH_RESCUE"
    SURVEILLANCE = "SURVEILLANCE"
    DELIVERY = "DELIVERY"
    FORMATION_FLIGHT = "FORMATION_FLIGHT"
    EMERGENCY_RESPONSE = "EMERGENCY_RESPONSE"


@dataclass
class Position:
    """位置座標"""
    x: float
    y: float
    z: float
    timestamp: datetime
    
    def distance_to(self, other: 'Position') -> float:
        """計算到另一個位置的距離"""
        return math.sqrt(
            (self.x - other.x) ** 2 + 
            (self.y - other.y) ** 2 + 
            (self.z - other.z) ** 2
        )


@dataclass
class Velocity:
    """速度向量"""
    vx: float  # m/s
    vy: float  # m/s
    vz: float  # m/s
    
    def magnitude(self) -> float:
        """計算速度大小"""
        return math.sqrt(self.vx ** 2 + self.vy ** 2 + self.vz ** 2)


@dataclass
class MobilityParameters:
    """移動參數"""
    max_speed: float = 30.0  # m/s
    min_speed: float = 1.0   # m/s
    acceleration: float = 2.0  # m/s²
    direction_change_probability: float = 0.1
    pause_probability: float = 0.05
    pause_duration_range: Tuple[float, float] = (1.0, 10.0)  # seconds
    boundary_behavior: str = "reflect"  # "reflect", "wrap", "stop"


@dataclass
class MovingEntity:
    """移動實體"""
    entity_id: str
    entity_type: str  # "UE", "UAV", "Vehicle"
    current_position: Position
    current_velocity: Velocity
    target_position: Optional[Position] = None
    mobility_pattern: MobilityPattern = MobilityPattern.RANDOM_WALK
    parameters: MobilityParameters = None
    trajectory_history: List[Position] = None
    is_active: bool = True
    mission_parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = MobilityParameters()
        if self.trajectory_history is None:
            self.trajectory_history = []
        if self.mission_parameters is None:
            self.mission_parameters = {}


@dataclass
class SimulationArea:
    """模擬區域"""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float = 0.0
    max_z: float = 100.0
    
    def is_within_bounds(self, position: Position) -> bool:
        """檢查位置是否在邊界內"""
        return (self.min_x <= position.x <= self.max_x and
                self.min_y <= position.y <= self.max_y and
                self.min_z <= position.z <= self.max_z)
    
    def get_random_position(self) -> Position:
        """獲取隨機位置"""
        return Position(
            x=random.uniform(self.min_x, self.max_x),
            y=random.uniform(self.min_y, self.max_y),
            z=random.uniform(self.min_z, self.max_z),
            timestamp=datetime.utcnow()
        )


class MobilityModel:
    """移動模型基類"""
    
    def __init__(self, parameters: MobilityParameters):
        self.parameters = parameters
    
    async def update_position(self, entity: MovingEntity, dt: float) -> Position:
        """更新位置 - 子類需要實現"""
        raise NotImplementedError


class StationaryModel(MobilityModel):
    """靜止模型"""
    
    async def update_position(self, entity: MovingEntity, dt: float) -> Position:
        # 添加小量的隨機抖動模擬真實設備
        jitter_x = random.uniform(-0.1, 0.1)
        jitter_y = random.uniform(-0.1, 0.1)
        
        new_position = Position(
            x=entity.current_position.x + jitter_x,
            y=entity.current_position.y + jitter_y,
            z=entity.current_position.z,
            timestamp=datetime.utcnow()
        )
        
        return new_position


class LinearMotionModel(MobilityModel):
    """線性運動模型"""
    
    async def update_position(self, entity: MovingEntity, dt: float) -> Position:
        # 如果沒有目標，設定隨機目標
        if entity.target_position is None:
            entity.target_position = Position(
                x=entity.current_position.x + random.uniform(-1000, 1000),
                y=entity.current_position.y + random.uniform(-1000, 1000),
                z=entity.current_position.z,
                timestamp=datetime.utcnow()
            )
        
        # 計算朝向目標的方向
        dx = entity.target_position.x - entity.current_position.x
        dy = entity.target_position.y - entity.current_position.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        if distance < 1.0:  # 到達目標
            entity.target_position = None
            return entity.current_position
        
        # 正規化方向向量
        direction_x = dx / distance
        direction_y = dy / distance
        
        # 使用當前速度大小
        speed = entity.current_velocity.magnitude()
        if speed == 0:
            speed = self.parameters.max_speed / 2
        
        # 計算新位置
        new_x = entity.current_position.x + direction_x * speed * dt
        new_y = entity.current_position.y + direction_y * speed * dt
        
        return Position(
            x=new_x,
            y=new_y,
            z=entity.current_position.z,
            timestamp=datetime.utcnow()
        )


class RandomWalkModel(MobilityModel):
    """隨機游走模型"""
    
    async def update_position(self, entity: MovingEntity, dt: float) -> Position:
        # 隨機改變方向
        if random.random() < self.parameters.direction_change_probability:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(self.parameters.min_speed, self.parameters.max_speed)
            
            entity.current_velocity.vx = speed * math.cos(angle)
            entity.current_velocity.vy = speed * math.sin(angle)
        
        # 計算新位置
        new_x = entity.current_position.x + entity.current_velocity.vx * dt
        new_y = entity.current_position.y + entity.current_velocity.vy * dt
        
        return Position(
            x=new_x,
            y=new_y,
            z=entity.current_position.z,
            timestamp=datetime.utcnow()
        )


class CircularMotionModel(MobilityModel):
    """圓形運動模型"""
    
    def __init__(self, parameters: MobilityParameters, radius: float = 500.0):
        super().__init__(parameters)
        self.radius = radius
        self.angular_velocity = parameters.max_speed / radius  # rad/s
    
    async def update_position(self, entity: MovingEntity, dt: float) -> Position:
        # 獲取當前角度
        center_x = entity.mission_parameters.get('center_x', entity.current_position.x)
        center_y = entity.mission_parameters.get('center_y', entity.current_position.y)
        
        # 計算當前相對於中心的角度
        dx = entity.current_position.x - center_x
        dy = entity.current_position.y - center_y
        current_angle = math.atan2(dy, dx)
        
        # 更新角度
        new_angle = current_angle + self.angular_velocity * dt
        
        # 計算新位置
        new_x = center_x + self.radius * math.cos(new_angle)
        new_y = center_y + self.radius * math.sin(new_angle)
        
        return Position(
            x=new_x,
            y=new_y,
            z=entity.current_position.z,
            timestamp=datetime.utcnow()
        )


class HighwayModel(MobilityModel):
    """高速公路模型"""
    
    def __init__(self, parameters: MobilityParameters, lanes: int = 3):
        super().__init__(parameters)
        self.lanes = lanes
        self.lane_width = 3.5  # meters
    
    async def update_position(self, entity: MovingEntity, dt: float) -> Position:
        # 如果是新實體，分配車道
        if 'lane' not in entity.mission_parameters:
            entity.mission_parameters['lane'] = random.randint(0, self.lanes - 1)
            entity.mission_parameters['highway_direction'] = random.choice([1, -1])
        
        lane = entity.mission_parameters['lane']
        direction = entity.mission_parameters['highway_direction']
        
        # 車道變更概率
        if random.random() < 0.01:  # 1% 機率變更車道
            new_lane = max(0, min(self.lanes - 1, lane + random.choice([-1, 1])))
            entity.mission_parameters['lane'] = new_lane
        
        # 設定速度（高速公路通常速度較高且穩定）
        speed = random.uniform(20, 30)  # 20-30 m/s (72-108 km/h)
        
        # 計算新位置
        new_x = entity.current_position.x + direction * speed * dt
        new_y = entity.mission_parameters['lane'] * self.lane_width
        
        return Position(
            x=new_x,
            y=new_y,
            z=entity.current_position.z,
            timestamp=datetime.utcnow()
        )


class UrbanMobilityModel(MobilityModel):
    """都市移動模型"""
    
    def __init__(self, parameters: MobilityParameters, grid_size: float = 100.0):
        super().__init__(parameters)
        self.grid_size = grid_size
        self.intersection_pause_prob = 0.3
        self.speed_variation = 0.2
    
    async def update_position(self, entity: MovingEntity, dt: float) -> Position:
        # 都市環境中速度較慢且變化較大
        base_speed = random.uniform(1, 15)  # 1-15 m/s
        
        # 在路口附近降速
        grid_x = int(entity.current_position.x / self.grid_size)
        grid_y = int(entity.current_position.y / self.grid_size)
        
        # 檢查是否接近路口
        rel_x = (entity.current_position.x % self.grid_size) / self.grid_size
        rel_y = (entity.current_position.y % self.grid_size) / self.grid_size
        
        near_intersection = (abs(rel_x - 0.5) < 0.1 or abs(rel_y - 0.5) < 0.1)
        
        if near_intersection:
            base_speed *= 0.3  # 路口減速
            if random.random() < self.intersection_pause_prob:
                base_speed = 0  # 紅燈停車
        
        # 隨機方向變化
        if random.random() < self.parameters.direction_change_probability * 2:
            angle = random.choice([0, math.pi/2, math.pi, 3*math.pi/2])  # 90度轉彎
            entity.current_velocity.vx = base_speed * math.cos(angle)
            entity.current_velocity.vy = base_speed * math.sin(angle)
        
        # 計算新位置
        new_x = entity.current_position.x + entity.current_velocity.vx * dt
        new_y = entity.current_position.y + entity.current_velocity.vy * dt
        
        return Position(
            x=new_x,
            y=new_y,
            z=entity.current_position.z,
            timestamp=datetime.utcnow()
        )


class UAVPatrolModel(MobilityModel):
    """UAV 巡邏模型"""
    
    def __init__(self, parameters: MobilityParameters, patrol_points: List[Tuple[float, float, float]]):
        super().__init__(parameters)
        self.patrol_points = patrol_points
    
    async def update_position(self, entity: MovingEntity, dt: float) -> Position:
        # 初始化巡邏索引
        if 'patrol_index' not in entity.mission_parameters:
            entity.mission_parameters['patrol_index'] = 0
        
        patrol_index = entity.mission_parameters['patrol_index']
        target_point = self.patrol_points[patrol_index]
        
        # 計算到目標點的距離
        dx = target_point[0] - entity.current_position.x
        dy = target_point[1] - entity.current_position.y
        dz = target_point[2] - entity.current_position.z
        distance = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        
        # 如果接近目標點，切換到下一個點
        if distance < 10.0:
            entity.mission_parameters['patrol_index'] = (patrol_index + 1) % len(self.patrol_points)
            return entity.current_position
        
        # 朝向目標點移動
        direction_x = dx / distance
        direction_y = dy / distance
        direction_z = dz / distance
        
        speed = self.parameters.max_speed * 0.8  # UAV 通常速度較快
        
        new_x = entity.current_position.x + direction_x * speed * dt
        new_y = entity.current_position.y + direction_y * speed * dt
        new_z = entity.current_position.z + direction_z * speed * dt
        
        return Position(
            x=new_x,
            y=new_y,
            z=new_z,
            timestamp=datetime.utcnow()
        )


class MobilitySimulationService:
    """
    移動模擬服務
    
    功能：
    1. 管理多個移動實體
    2. 提供各種移動模式
    3. 實時更新位置
    4. 生成移動軌跡用於測試
    """
    
    def __init__(self):
        self.entities: Dict[str, MovingEntity] = {}
        self.simulation_area = SimulationArea(-2000, 2000, -2000, 2000, 0, 500)
        self.mobility_models = self._initialize_mobility_models()
        self.simulation_running = False
        self.update_interval = 1.0  # seconds
        self.simulation_task: Optional[asyncio.Task] = None
        self.trajectory_logs: Dict[str, List[Position]] = {}
        
    def _initialize_mobility_models(self) -> Dict[MobilityPattern, MobilityModel]:
        """初始化移動模型"""
        default_params = MobilityParameters()
        
        return {
            MobilityPattern.STATIONARY: StationaryModel(default_params),
            MobilityPattern.LINEAR: LinearMotionModel(default_params),
            MobilityPattern.RANDOM_WALK: RandomWalkModel(default_params),
            MobilityPattern.CIRCULAR: CircularMotionModel(default_params),
            MobilityPattern.HIGHWAY: HighwayModel(default_params),
            MobilityPattern.URBAN: UrbanMobilityModel(default_params),
        }
    
    async def start_simulation(self):
        """開始模擬"""
        if self.simulation_running:
            logger.warning("模擬已在運行中")
            return
        
        self.simulation_running = True
        self.simulation_task = asyncio.create_task(self._simulation_loop())
        logger.info("移動模擬已開始")
    
    async def stop_simulation(self):
        """停止模擬"""
        if not self.simulation_running:
            return
        
        self.simulation_running = False
        if self.simulation_task:
            self.simulation_task.cancel()
            try:
                await self.simulation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("移動模擬已停止")
    
    async def _simulation_loop(self):
        """模擬循環"""
        last_update = time.time()
        
        try:
            while self.simulation_running:
                current_time = time.time()
                dt = current_time - last_update
                
                # 更新所有實體位置
                for entity in self.entities.values():
                    if entity.is_active:
                        await self._update_entity_position(entity, dt)
                
                last_update = current_time
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            logger.info("模擬循環已取消")
        except Exception as e:
            logger.error(f"模擬循環錯誤: {e}")
    
    async def _update_entity_position(self, entity: MovingEntity, dt: float):
        """更新實體位置"""
        try:
            # 獲取對應的移動模型
            mobility_model = self.mobility_models.get(entity.mobility_pattern)
            if not mobility_model:
                logger.warning(f"未找到移動模型: {entity.mobility_pattern}")
                return
            
            # 計算新位置
            new_position = await mobility_model.update_position(entity, dt)
            
            # 邊界處理
            new_position = self._handle_boundary(entity, new_position)
            
            # 更新實體位置
            entity.current_position = new_position
            
            # 記錄軌跡
            if entity.entity_id not in self.trajectory_logs:
                self.trajectory_logs[entity.entity_id] = []
            
            self.trajectory_logs[entity.entity_id].append(new_position)
            
            # 限制軌跡歷史長度
            if len(self.trajectory_logs[entity.entity_id]) > 1000:
                self.trajectory_logs[entity.entity_id] = self.trajectory_logs[entity.entity_id][-500:]
            
        except Exception as e:
            logger.error(f"更新實體位置失敗 {entity.entity_id}: {e}")
    
    def _handle_boundary(self, entity: MovingEntity, new_position: Position) -> Position:
        """處理邊界碰撞"""
        if self.simulation_area.is_within_bounds(new_position):
            return new_position
        
        behavior = entity.parameters.boundary_behavior
        
        if behavior == "reflect":
            # 反射邊界
            if new_position.x < self.simulation_area.min_x or new_position.x > self.simulation_area.max_x:
                entity.current_velocity.vx *= -1
                new_position.x = max(self.simulation_area.min_x, 
                                   min(self.simulation_area.max_x, new_position.x))
            
            if new_position.y < self.simulation_area.min_y or new_position.y > self.simulation_area.max_y:
                entity.current_velocity.vy *= -1
                new_position.y = max(self.simulation_area.min_y, 
                                   min(self.simulation_area.max_y, new_position.y))
                
        elif behavior == "wrap":
            # 包裹邊界
            if new_position.x < self.simulation_area.min_x:
                new_position.x = self.simulation_area.max_x
            elif new_position.x > self.simulation_area.max_x:
                new_position.x = self.simulation_area.min_x
            
            if new_position.y < self.simulation_area.min_y:
                new_position.y = self.simulation_area.max_y
            elif new_position.y > self.simulation_area.max_y:
                new_position.y = self.simulation_area.min_y
                
        else:  # "stop"
            # 停止在邊界
            new_position.x = max(self.simulation_area.min_x, 
                               min(self.simulation_area.max_x, new_position.x))
            new_position.y = max(self.simulation_area.min_y, 
                               min(self.simulation_area.max_y, new_position.y))
            entity.current_velocity.vx = 0
            entity.current_velocity.vy = 0
        
        return new_position
    
    async def add_entity(
        self, 
        entity_id: str, 
        entity_type: str,
        initial_position: Position,
        mobility_pattern: MobilityPattern,
        parameters: Optional[MobilityParameters] = None
    ) -> bool:
        """添加移動實體"""
        
        if entity_id in self.entities:
            logger.warning(f"實體 {entity_id} 已存在")
            return False
        
        if parameters is None:
            parameters = MobilityParameters()
        
        entity = MovingEntity(
            entity_id=entity_id,
            entity_type=entity_type,
            current_position=initial_position,
            current_velocity=Velocity(0, 0, 0),
            mobility_pattern=mobility_pattern,
            parameters=parameters
        )
        
        self.entities[entity_id] = entity
        logger.info(f"添加移動實體: {entity_id} ({entity_type}) - {mobility_pattern.value}")
        
        return True
    
    async def remove_entity(self, entity_id: str) -> bool:
        """移除移動實體"""
        if entity_id not in self.entities:
            return False
        
        del self.entities[entity_id]
        if entity_id in self.trajectory_logs:
            del self.trajectory_logs[entity_id]
        
        logger.info(f"移除移動實體: {entity_id}")
        return True
    
    async def update_entity_pattern(
        self, 
        entity_id: str, 
        new_pattern: MobilityPattern,
        new_parameters: Optional[MobilityParameters] = None
    ) -> bool:
        """更新實體移動模式"""
        
        if entity_id not in self.entities:
            return False
        
        entity = self.entities[entity_id]
        entity.mobility_pattern = new_pattern
        
        if new_parameters:
            entity.parameters = new_parameters
        
        logger.info(f"更新實體 {entity_id} 移動模式: {new_pattern.value}")
        return True
    
    def get_entity_position(self, entity_id: str) -> Optional[Position]:
        """獲取實體當前位置"""
        entity = self.entities.get(entity_id)
        return entity.current_position if entity else None
    
    def get_entity_trajectory(self, entity_id: str, limit: int = 100) -> List[Position]:
        """獲取實體軌跡歷史"""
        trajectory = self.trajectory_logs.get(entity_id, [])
        return trajectory[-limit:] if trajectory else []
    
    def get_all_entities_status(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有實體狀態"""
        status = {}
        
        for entity_id, entity in self.entities.items():
            status[entity_id] = {
                'entity_type': entity.entity_type,
                'position': asdict(entity.current_position),
                'velocity': asdict(entity.current_velocity),
                'mobility_pattern': entity.mobility_pattern.value,
                'is_active': entity.is_active,
                'trajectory_length': len(self.trajectory_logs.get(entity_id, []))
            }
        
        return status
    
    async def create_test_scenario(self, scenario_name: str) -> List[str]:
        """創建測試場景"""
        
        entity_ids = []
        
        if scenario_name == "highway_traffic":
            # 高速公路交通場景
            for i in range(10):
                entity_id = f"vehicle_{i}"
                position = Position(
                    x=random.uniform(-1000, 1000),
                    y=random.uniform(0, 10.5),  # 3 車道
                    z=0,
                    timestamp=datetime.utcnow()
                )
                
                await self.add_entity(
                    entity_id, "Vehicle", position, MobilityPattern.HIGHWAY
                )
                entity_ids.append(entity_id)
        
        elif scenario_name == "urban_mixed":
            # 都市混合場景
            for i in range(5):
                entity_id = f"pedestrian_{i}"
                position = self.simulation_area.get_random_position()
                position.z = 0  # 行人在地面
                
                params = MobilityParameters(max_speed=2.0, min_speed=0.5)
                await self.add_entity(
                    entity_id, "Pedestrian", position, MobilityPattern.URBAN, params
                )
                entity_ids.append(entity_id)
            
            for i in range(8):
                entity_id = f"vehicle_{i}"
                position = self.simulation_area.get_random_position()
                position.z = 0
                
                await self.add_entity(
                    entity_id, "Vehicle", position, MobilityPattern.URBAN
                )
                entity_ids.append(entity_id)
        
        elif scenario_name == "uav_patrol":
            # UAV 巡邏場景
            patrol_points = [
                (-500, -500, 100),
                (500, -500, 100),
                (500, 500, 100),
                (-500, 500, 100)
            ]
            
            for i in range(3):
                entity_id = f"uav_{i}"
                position = Position(
                    x=patrol_points[0][0],
                    y=patrol_points[0][1],
                    z=patrol_points[0][2],
                    timestamp=datetime.utcnow()
                )
                
                # 使用自定義 UAV 巡邏模型
                uav_model = UAVPatrolModel(MobilityParameters(max_speed=25.0), patrol_points)
                self.mobility_models[f"UAV_PATROL_{i}"] = uav_model
                
                entity = MovingEntity(
                    entity_id=entity_id,
                    entity_type="UAV",
                    current_position=position,
                    current_velocity=Velocity(0, 0, 0),
                    mobility_pattern=MobilityPattern.CIRCULAR,  # 使用 CIRCULAR 作為佔位符
                    parameters=MobilityParameters(max_speed=25.0)
                )
                
                self.entities[entity_id] = entity
                entity_ids.append(entity_id)
        
        elif scenario_name == "random_mixed":
            # 隨機混合場景
            patterns = [
                MobilityPattern.STATIONARY,
                MobilityPattern.LINEAR,
                MobilityPattern.RANDOM_WALK,
                MobilityPattern.CIRCULAR
            ]
            
            for i in range(15):
                entity_id = f"mixed_{i}"
                position = self.simulation_area.get_random_position()
                pattern = random.choice(patterns)
                
                await self.add_entity(entity_id, "Mixed", position, pattern)
                entity_ids.append(entity_id)
        
        logger.info(f"創建測試場景 '{scenario_name}': {len(entity_ids)} 個實體")
        return entity_ids
    
    async def generate_handover_test_data(
        self, 
        duration: int = 300,  # seconds
        sample_interval: float = 1.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """生成換手測試數據"""
        
        test_data = {}
        start_time = time.time()
        
        logger.info(f"開始生成 {duration} 秒的換手測試數據")
        
        while (time.time() - start_time) < duration:
            timestamp = datetime.utcnow()
            
            for entity_id, entity in self.entities.items():
                if entity_id not in test_data:
                    test_data[entity_id] = []
                
                # 模擬換手觸發條件檢查
                handover_probability = self._calculate_handover_probability(entity)
                
                data_point = {
                    'timestamp': timestamp.isoformat(),
                    'position': asdict(entity.current_position),
                    'velocity': asdict(entity.current_velocity),
                    'handover_probability': handover_probability,
                    'mobility_pattern': entity.mobility_pattern.value,
                    'signal_quality': self._simulate_signal_quality(entity),
                    'network_load': random.uniform(0.3, 0.9)
                }
                
                test_data[entity_id].append(data_point)
            
            await asyncio.sleep(sample_interval)
        
        logger.info(f"測試數據生成完成: {len(test_data)} 個實體")
        return test_data
    
    def _calculate_handover_probability(self, entity: MovingEntity) -> float:
        """計算換手觸發概率"""
        
        # 基於移動速度
        speed = entity.current_velocity.magnitude()
        speed_factor = min(1.0, speed / 30.0)  # 正規化到 0-1
        
        # 基於移動模式
        pattern_factors = {
            MobilityPattern.STATIONARY: 0.1,
            MobilityPattern.LINEAR: 0.4,
            MobilityPattern.RANDOM_WALK: 0.6,
            MobilityPattern.CIRCULAR: 0.3,
            MobilityPattern.HIGHWAY: 0.5,
            MobilityPattern.URBAN: 0.7
        }
        
        pattern_factor = pattern_factors.get(entity.mobility_pattern, 0.5)
        
        # 基於位置（邊界區域換手概率較高）
        edge_distance = min(
            abs(entity.current_position.x - self.simulation_area.min_x),
            abs(entity.current_position.x - self.simulation_area.max_x),
            abs(entity.current_position.y - self.simulation_area.min_y),
            abs(entity.current_position.y - self.simulation_area.max_y)
        )
        
        edge_factor = max(0.1, 1.0 - edge_distance / 500.0)
        
        # 綜合概率
        probability = (speed_factor * 0.4 + pattern_factor * 0.4 + edge_factor * 0.2)
        return min(1.0, probability)
    
    def _simulate_signal_quality(self, entity: MovingEntity) -> Dict[str, float]:
        """模擬信號品質"""
        
        # 基於位置的信號強度模擬
        distance_from_center = math.sqrt(
            entity.current_position.x ** 2 + entity.current_position.y ** 2
        )
        
        # 距離越遠信號越弱
        rsrp = -70 - (distance_from_center / 100.0) + random.uniform(-10, 5)
        rsrq = -10 - (distance_from_center / 200.0) + random.uniform(-5, 2)
        sinr = 20 - (distance_from_center / 150.0) + random.uniform(-8, 5)
        
        # 基於移動速度的信號品質影響
        speed = entity.current_velocity.magnitude()
        doppler_effect = speed * 0.5  # 簡化的都卜勒效應
        
        return {
            'rsrp': max(-140, rsrp - doppler_effect),
            'rsrq': max(-20, rsrq - doppler_effect * 0.3),
            'sinr': max(-10, sinr - doppler_effect * 0.2)
        }
    
    def get_simulation_statistics(self) -> Dict[str, Any]:
        """獲取模擬統計信息"""
        
        total_entities = len(self.entities)
        active_entities = sum(1 for e in self.entities.values() if e.is_active)
        
        pattern_distribution = {}
        for entity in self.entities.values():
            pattern = entity.mobility_pattern.value
            pattern_distribution[pattern] = pattern_distribution.get(pattern, 0) + 1
        
        type_distribution = {}
        for entity in self.entities.values():
            entity_type = entity.entity_type
            type_distribution[entity_type] = type_distribution.get(entity_type, 0) + 1
        
        total_trajectory_points = sum(len(traj) for traj in self.trajectory_logs.values())
        
        return {
            'simulation_running': self.simulation_running,
            'total_entities': total_entities,
            'active_entities': active_entities,
            'pattern_distribution': pattern_distribution,
            'type_distribution': type_distribution,
            'total_trajectory_points': total_trajectory_points,
            'simulation_area': asdict(self.simulation_area),
            'update_interval': self.update_interval
        }


# 全局服務實例
mobility_simulation_service = MobilitySimulationService()