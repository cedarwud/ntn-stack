"""
四場景測試驗證環境
實現城市移動、高速公路、偏遠地區、緊急救援四大場景的換手測試驗證
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)

class TestScenarioType(Enum):
    """測試場景類型"""
    URBAN_MOBILITY = "urban_mobility"           # 城市移動場景
    HIGHWAY_MOBILITY = "highway_mobility"       # 高速公路場景
    RURAL_COVERAGE = "rural_coverage"           # 偏遠地區場景
    EMERGENCY_RESPONSE = "emergency_response"   # 緊急救援場景

class HandoverTriggerType(Enum):
    """換手觸發類型"""
    SIGNAL_QUALITY = "signal_quality"
    PREDICTION_BASED = "prediction_based"
    INTERFERENCE = "interference"
    COVERAGE_LOSS = "coverage_loss"
    LOAD_BALANCING = "load_balancing"

@dataclass
class ScenarioEnvironment:
    """場景環境配置"""
    scenario_id: str
    scenario_type: TestScenarioType
    terrain_type: str  # urban, highway, rural, mountain
    building_density: float  # 0-1, 建築物密度
    interference_level: float  # 0-1, 干擾水平
    weather_conditions: Dict[str, float]  # 天氣條件
    user_density: int  # 用戶密度
    mobility_patterns: List[str]  # 移動模式列表
    simulation_area: Tuple[float, float, float, float]  # lat_min, lat_max, lon_min, lon_max
    duration_hours: float
    created_at: datetime

@dataclass
class UEConfiguration:
    """UE配置"""
    ue_id: str
    initial_position: Tuple[float, float, float]  # lat, lon, alt
    mobility_pattern: str
    velocity: float  # m/s
    service_type: str  # voice, data, video, emergency
    priority_level: int  # 1-5, 優先級
    power_class: int  # UE功率等級
    antenna_gain: float  # dBi
    requirements: Dict[str, float]  # QoS需求

@dataclass
class SatelliteConfiguration:
    """衛星配置"""
    satellite_id: str
    orbital_position: Tuple[float, float, float]  # lat, lon, alt
    beam_coverage: float  # 波束覆蓋半徑(km)
    frequency_band: str  # Ka, Ku, S
    max_capacity: int  # 最大容量
    current_load: float  # 當前負載 0-1
    handover_capability: List[str]  # 支援的換手類型

@dataclass
class HandoverEvent:
    """換手事件"""
    event_id: str
    timestamp: datetime
    ue_id: str
    source_satellite: str
    target_satellite: str
    trigger_type: HandoverTriggerType
    trigger_metrics: Dict[str, float]
    handover_latency: float  # ms
    success: bool
    failure_reason: Optional[str]
    prediction_accuracy: float  # 0-1, 預測準確度
    interference_impact: float  # 干擾影響
    environment_factors: Dict[str, float]

@dataclass
class ScenarioTestResult:
    """場景測試結果"""
    test_id: str
    scenario_id: str
    test_start_time: datetime
    test_duration: float  # seconds
    total_ues: int
    total_handovers: int
    successful_handovers: int
    failed_handovers: int
    handover_events: List[HandoverEvent]
    performance_metrics: Dict[str, float]
    scenario_specific_metrics: Dict[str, Any]
    validation_results: Dict[str, bool]
    recommendations: List[str]

class ScenarioTestEnvironment:
    """四場景測試驗證環境"""
    
    def __init__(self):
        self.scenarios: Dict[str, ScenarioEnvironment] = {}
        self.test_results: Dict[str, List[ScenarioTestResult]] = {}
        self.ue_configurations: Dict[str, List[UEConfiguration]] = {}
        self.satellite_configurations: Dict[str, List[SatelliteConfiguration]] = {}
        
        # 初始化預定義場景
        self._initialize_predefined_scenarios()
    
    def _initialize_predefined_scenarios(self):
        """初始化預定義的四大測試場景"""
        
        # 1. 城市移動場景
        urban_scenario = ScenarioEnvironment(
            scenario_id="urban_mobility_taipei",
            scenario_type=TestScenarioType.URBAN_MOBILITY,
            terrain_type="urban",
            building_density=0.8,
            interference_level=0.6,
            weather_conditions={
                "precipitation": 0.2,
                "cloud_cover": 0.4,
                "temperature": 25.0,
                "humidity": 0.7
            },
            user_density=1000,  # users/km²
            mobility_patterns=["pedestrian", "vehicle_urban", "public_transport"],
            simulation_area=(25.0, 25.1, 121.5, 121.6),  # 台北市區
            duration_hours=12.0,
            created_at=datetime.now()
        )
        
        # 2. 高速公路場景
        highway_scenario = ScenarioEnvironment(
            scenario_id="highway_mobility_freeway",
            scenario_type=TestScenarioType.HIGHWAY_MOBILITY,
            terrain_type="highway",
            building_density=0.1,
            interference_level=0.3,
            weather_conditions={
                "precipitation": 0.1,
                "cloud_cover": 0.2,
                "temperature": 28.0,
                "humidity": 0.6
            },
            user_density=50,  # users/km²
            mobility_patterns=["highway_vehicle", "truck", "motorcycle"],
            simulation_area=(24.5, 25.5, 120.5, 121.5),  # 高速公路路段
            duration_hours=6.0,
            created_at=datetime.now()
        )
        
        # 3. 偏遠地區場景
        rural_scenario = ScenarioEnvironment(
            scenario_id="rural_coverage_mountain",
            scenario_type=TestScenarioType.RURAL_COVERAGE,
            terrain_type="rural",
            building_density=0.05,
            interference_level=0.1,
            weather_conditions={
                "precipitation": 0.3,
                "cloud_cover": 0.6,
                "temperature": 18.0,
                "humidity": 0.8
            },
            user_density=5,  # users/km²
            mobility_patterns=["stationary", "slow_pedestrian", "vehicle_rural"],
            simulation_area=(23.8, 24.2, 120.8, 121.2),  # 山區偏遠地區
            duration_hours=24.0,
            created_at=datetime.now()
        )
        
        # 4. 緊急救援場景
        emergency_scenario = ScenarioEnvironment(
            scenario_id="emergency_response_disaster",
            scenario_type=TestScenarioType.EMERGENCY_RESPONSE,
            terrain_type="disaster_zone",
            building_density=0.3,  # 部分建築物倒塌
            interference_level=0.8,  # 高干擾環境
            weather_conditions={
                "precipitation": 0.8,  # 惡劣天氣
                "cloud_cover": 0.9,
                "temperature": 15.0,
                "humidity": 0.9
            },
            user_density=200,  # 救援人員密集
            mobility_patterns=["uav_patrol", "rescue_vehicle", "emergency_personnel"],
            simulation_area=(23.5, 24.0, 120.0, 120.5),  # 災害區域
            duration_hours=8.0,
            created_at=datetime.now()
        )
        
        self.scenarios.update({
            urban_scenario.scenario_id: urban_scenario,
            highway_scenario.scenario_id: highway_scenario,
            rural_scenario.scenario_id: rural_scenario,
            emergency_scenario.scenario_id: emergency_scenario
        })
        
        # 為每個場景初始化UE和衛星配置
        self._initialize_scenario_configurations()
    
    def _initialize_scenario_configurations(self):
        """為每個場景初始化UE和衛星配置"""
        
        for scenario_id, scenario in self.scenarios.items():
            # 初始化UE配置
            ue_configs = self._generate_ue_configurations(scenario)
            self.ue_configurations[scenario_id] = ue_configs
            
            # 初始化衛星配置
            sat_configs = self._generate_satellite_configurations(scenario)
            self.satellite_configurations[scenario_id] = sat_configs
    
    def _generate_ue_configurations(self, scenario: ScenarioEnvironment) -> List[UEConfiguration]:
        """為場景生成UE配置"""
        
        ue_configs = []
        lat_min, lat_max, lon_min, lon_max = scenario.simulation_area
        
        if scenario.scenario_type == TestScenarioType.URBAN_MOBILITY:
            # 城市場景：多種服務類型的UE
            for i in range(20):
                ue_config = UEConfiguration(
                    ue_id=f"urban_ue_{i}",
                    initial_position=(
                        np.random.uniform(lat_min, lat_max),
                        np.random.uniform(lon_min, lon_max),
                        np.random.uniform(1.5, 50.0)  # 地面到建築物高度
                    ),
                    mobility_pattern=np.random.choice(scenario.mobility_patterns),
                    velocity=np.random.uniform(0.5, 15.0),  # 步行到車輛速度
                    service_type=np.random.choice(["voice", "data", "video"]),
                    priority_level=np.random.randint(1, 4),
                    power_class=np.random.randint(1, 4),
                    antenna_gain=np.random.uniform(0, 3),
                    requirements={
                        "min_throughput": np.random.uniform(1, 50),  # Mbps
                        "max_latency": np.random.uniform(50, 200),   # ms
                        "reliability": np.random.uniform(0.95, 0.99)
                    }
                )
                ue_configs.append(ue_config)
        
        elif scenario.scenario_type == TestScenarioType.HIGHWAY_MOBILITY:
            # 高速公路場景：高速移動的車輛UE
            for i in range(15):
                ue_config = UEConfiguration(
                    ue_id=f"highway_ue_{i}",
                    initial_position=(
                        np.random.uniform(lat_min, lat_max),
                        np.random.uniform(lon_min, lon_max),
                        2.0  # 車輛高度
                    ),
                    mobility_pattern=np.random.choice(scenario.mobility_patterns),
                    velocity=np.random.uniform(60, 120),  # 高速公路速度 km/h
                    service_type=np.random.choice(["data", "voice"]),
                    priority_level=np.random.randint(2, 4),
                    power_class=np.random.randint(2, 4),
                    antenna_gain=np.random.uniform(2, 5),
                    requirements={
                        "min_throughput": np.random.uniform(5, 20),
                        "max_latency": np.random.uniform(100, 300),
                        "reliability": np.random.uniform(0.9, 0.95)
                    }
                )
                ue_configs.append(ue_config)
        
        elif scenario.scenario_type == TestScenarioType.RURAL_COVERAGE:
            # 偏遠地區場景：稀疏分布的UE
            for i in range(8):
                ue_config = UEConfiguration(
                    ue_id=f"rural_ue_{i}",
                    initial_position=(
                        np.random.uniform(lat_min, lat_max),
                        np.random.uniform(lon_min, lon_max),
                        np.random.uniform(1.0, 10.0)
                    ),
                    mobility_pattern=np.random.choice(scenario.mobility_patterns),
                    velocity=np.random.uniform(0, 30),  # 靜止到慢速移動
                    service_type=np.random.choice(["voice", "data"]),
                    priority_level=np.random.randint(1, 3),
                    power_class=np.random.randint(3, 5),  # 更高功率
                    antenna_gain=np.random.uniform(3, 8),  # 更高增益
                    requirements={
                        "min_throughput": np.random.uniform(0.5, 5),
                        "max_latency": np.random.uniform(200, 500),
                        "reliability": np.random.uniform(0.85, 0.9)
                    }
                )
                ue_configs.append(ue_config)
        
        elif scenario.scenario_type == TestScenarioType.EMERGENCY_RESPONSE:
            # 緊急救援場景：UAV和救援裝備
            for i in range(25):
                service_type = np.random.choice(["emergency", "video", "data"])
                ue_config = UEConfiguration(
                    ue_id=f"emergency_ue_{i}",
                    initial_position=(
                        np.random.uniform(lat_min, lat_max),
                        np.random.uniform(lon_min, lon_max),
                        np.random.uniform(1.0, 100.0) if "uav" in scenario.mobility_patterns[i % len(scenario.mobility_patterns)] else 2.0
                    ),
                    mobility_pattern=scenario.mobility_patterns[i % len(scenario.mobility_patterns)],
                    velocity=np.random.uniform(5, 50),  # 救援速度
                    service_type=service_type,
                    priority_level=5 if service_type == "emergency" else np.random.randint(3, 5),
                    power_class=np.random.randint(2, 5),
                    antenna_gain=np.random.uniform(2, 6),
                    requirements={
                        "min_throughput": np.random.uniform(2, 30),
                        "max_latency": np.random.uniform(30, 150),
                        "reliability": np.random.uniform(0.95, 0.99)
                    }
                )
                ue_configs.append(ue_config)
        
        return ue_configs
    
    def _generate_satellite_configurations(self, scenario: ScenarioEnvironment) -> List[SatelliteConfiguration]:
        """為場景生成衛星配置"""
        
        sat_configs = []
        lat_center = (scenario.simulation_area[0] + scenario.simulation_area[1]) / 2
        lon_center = (scenario.simulation_area[2] + scenario.simulation_area[3]) / 2
        
        # 根據場景類型確定衛星數量和配置
        if scenario.scenario_type == TestScenarioType.URBAN_MOBILITY:
            satellite_count = 12  # 城市需要更多衛星覆蓋
            altitudes = [550, 700, 850]  # 多層軌道
        elif scenario.scenario_type == TestScenarioType.HIGHWAY_MOBILITY:
            satellite_count = 8   # 高速公路線性覆蓋
            altitudes = [600, 800]
        elif scenario.scenario_type == TestScenarioType.RURAL_COVERAGE:
            satellite_count = 6   # 偏遠地區衛星較少
            altitudes = [800, 1200]
        else:  # EMERGENCY_RESPONSE
            satellite_count = 10  # 緊急場景需要冗餘覆蓋
            altitudes = [500, 650, 900]
        
        for i in range(satellite_count):
            # 隨機分布在場景區域上空
            lat_offset = np.random.uniform(-2, 2)
            lon_offset = np.random.uniform(-2, 2)
            altitude = np.random.choice(altitudes)
            
            sat_config = SatelliteConfiguration(
                satellite_id=f"{scenario.scenario_id}_sat_{i}",
                orbital_position=(
                    lat_center + lat_offset,
                    lon_center + lon_offset,
                    altitude
                ),
                beam_coverage=np.random.uniform(200, 800),  # km
                frequency_band=np.random.choice(["Ka", "Ku", "S"]),
                max_capacity=np.random.randint(100, 500),
                current_load=np.random.uniform(0.2, 0.8),
                handover_capability=["hard", "soft", "seamless"]
            )
            sat_configs.append(sat_config)
        
        return sat_configs
    
    async def run_scenario_test(
        self,
        scenario_id: str,
        test_duration_override: Optional[float] = None,
        handover_algorithm: str = "ieee_infocom_2024"
    ) -> str:
        """運行場景測試"""
        
        if scenario_id not in self.scenarios:
            raise ValueError(f"場景不存在: {scenario_id}")
        
        scenario = self.scenarios[scenario_id]
        test_id = f"test_{scenario_id}_{int(datetime.now().timestamp())}"
        test_duration = test_duration_override or scenario.duration_hours
        
        logger.info(f"開始場景測試: {test_id}, 場景: {scenario_id}, 算法: {handover_algorithm}")
        
        # 獲取場景配置
        ue_configs = self.ue_configurations[scenario_id]
        sat_configs = self.satellite_configurations[scenario_id]
        
        # 模擬測試過程
        handover_events = await self._simulate_scenario_handovers(
            scenario, ue_configs, sat_configs, test_duration, handover_algorithm
        )
        
        # 分析測試結果
        test_result = await self._analyze_scenario_performance(
            test_id, scenario, handover_events, test_duration, handover_algorithm
        )
        
        # 存儲測試結果
        if scenario_id not in self.test_results:
            self.test_results[scenario_id] = []
        self.test_results[scenario_id].append(test_result)
        
        logger.info(f"完成場景測試: {test_id}, 總換手: {test_result.total_handovers}, 成功率: {test_result.successful_handovers/max(1,test_result.total_handovers)*100:.1f}%")
        
        return test_id
    
    async def _simulate_scenario_handovers(
        self,
        scenario: ScenarioEnvironment,
        ue_configs: List[UEConfiguration],
        sat_configs: List[SatelliteConfiguration],
        duration_hours: float,
        algorithm: str
    ) -> List[HandoverEvent]:
        """模擬場景中的換手事件"""
        
        handover_events = []
        time_steps = int(duration_hours * 60)  # 每分鐘一個時間步
        
        # 為每個UE追踪當前連接的衛星
        ue_connections = {}
        
        for minute in range(time_steps):
            current_time = datetime.now() + timedelta(minutes=minute)
            
            for ue in ue_configs:
                # 計算UE當前位置
                current_position = self._calculate_ue_position(ue, minute, scenario)
                
                # 計算所有可見衛星的信號品質
                satellite_metrics = self._calculate_satellite_metrics(
                    current_position, sat_configs, scenario, minute
                )
                
                # 選擇最佳衛星
                best_satellite = self._select_best_satellite(
                    satellite_metrics, ue, algorithm
                )
                
                # 檢查是否需要換手
                current_satellite = ue_connections.get(ue.ue_id)
                
                if best_satellite != current_satellite:
                    # 確定換手觸發原因
                    trigger_type = self._determine_handover_trigger(
                        current_satellite, best_satellite, satellite_metrics, scenario
                    )
                    
                    # 計算換手性能
                    handover_latency, success, failure_reason = self._calculate_handover_performance(
                        ue, current_satellite, best_satellite, scenario, algorithm
                    )
                    
                    # 創建換手事件
                    handover_event = HandoverEvent(
                        event_id=f"ho_{ue.ue_id}_{minute}",
                        timestamp=current_time,
                        ue_id=ue.ue_id,
                        source_satellite=current_satellite or "initial",
                        target_satellite=best_satellite,
                        trigger_type=trigger_type,
                        trigger_metrics=satellite_metrics.get(best_satellite, {}),
                        handover_latency=handover_latency,
                        success=success,
                        failure_reason=failure_reason,
                        prediction_accuracy=self._calculate_prediction_accuracy(algorithm, scenario),
                        interference_impact=scenario.interference_level,
                        environment_factors={
                            "building_density": scenario.building_density,
                            "weather_impact": sum(scenario.weather_conditions.values()) / len(scenario.weather_conditions),
                            "user_density": scenario.user_density
                        }
                    )
                    
                    handover_events.append(handover_event)
                    
                    # 更新連接
                    if success:
                        ue_connections[ue.ue_id] = best_satellite
        
        return handover_events
    
    def _calculate_ue_position(
        self, 
        ue: UEConfiguration, 
        time_minute: int, 
        scenario: ScenarioEnvironment
    ) -> Tuple[float, float, float]:
        """計算UE在指定時間的位置"""
        
        lat, lon, alt = ue.initial_position
        
        if ue.mobility_pattern == "stationary":
            return lat, lon, alt
        
        elif ue.mobility_pattern == "pedestrian":
            # 行人隨機移動
            speed_ms = ue.velocity / 3.6  # km/h to m/s
            distance = speed_ms * time_minute * 60  # meters
            angle = np.random.uniform(0, 2 * np.pi)
            
            # 簡化的位置更新（忽略地球曲率）
            lat_offset = (distance * np.cos(angle)) / 111320  # 緯度度數
            lon_offset = (distance * np.sin(angle)) / (111320 * np.cos(np.radians(lat)))
            
            return lat + lat_offset, lon + lon_offset, alt
        
        elif ue.mobility_pattern in ["vehicle_urban", "highway_vehicle"]:
            # 車輛線性移動
            speed_ms = ue.velocity / 3.6
            distance = speed_ms * time_minute * 60
            
            # 主要沿著某個方向移動
            if ue.mobility_pattern == "highway_vehicle":
                angle = np.random.normal(0, 0.2)  # 主要沿東西向
            else:
                angle = np.random.uniform(0, 2 * np.pi)
            
            lat_offset = (distance * np.cos(angle)) / 111320
            lon_offset = (distance * np.sin(angle)) / (111320 * np.cos(np.radians(lat)))
            
            return lat + lat_offset, lon + lon_offset, alt
        
        elif ue.mobility_pattern == "uav_patrol":
            # UAV巡邏模式
            patrol_radius = 5000  # 5km巡邏半徑
            angular_speed = 2 * np.pi / (60 * 30)  # 30分鐘一圈
            angle = time_minute * angular_speed
            
            lat_offset = (patrol_radius * np.cos(angle)) / 111320
            lon_offset = (patrol_radius * np.sin(angle)) / (111320 * np.cos(np.radians(lat)))
            
            # UAV高度變化
            altitude_variation = 20 * np.sin(angle * 3)  # 高度波動
            
            return lat + lat_offset, lon + lon_offset, alt + altitude_variation
        
        else:
            # 默認慢速隨機移動
            speed_ms = min(ue.velocity, 5) / 3.6
            distance = speed_ms * time_minute * 60
            angle = np.random.uniform(0, 2 * np.pi)
            
            lat_offset = (distance * np.cos(angle)) / 111320
            lon_offset = (distance * np.sin(angle)) / (111320 * np.cos(np.radians(lat)))
            
            return lat + lat_offset, lon + lon_offset, alt
    
    def _calculate_satellite_metrics(
        self,
        ue_position: Tuple[float, float, float],
        sat_configs: List[SatelliteConfiguration],
        scenario: ScenarioEnvironment,
        time_minute: int
    ) -> Dict[str, Dict[str, float]]:
        """計算UE到各衛星的信號指標"""
        
        metrics = {}
        ue_lat, ue_lon, ue_alt = ue_position
        
        for sat in sat_configs:
            # 計算衛星當前位置（簡化軌道計算）
            sat_lat, sat_lon, sat_alt = self._calculate_satellite_position(sat, time_minute)
            
            # 計算距離和仰角
            distance, elevation = self._calculate_distance_elevation(
                ue_lat, ue_lon, ue_alt, sat_lat, sat_lon, sat_alt
            )
            
            if elevation < 10:  # 仰角太低，不可見
                continue
            
            # 計算信號強度
            rsrp = self._calculate_rsrp(distance, sat.beam_coverage, scenario.interference_level)
            rsrq = self._calculate_rsrq(rsrp, scenario.interference_level, scenario.building_density)
            sinr = self._calculate_sinr(rsrp, scenario.interference_level)
            
            # 計算負載影響
            load_factor = min(1.0, sat.current_load + np.random.uniform(0, 0.1))
            throughput = (1 - load_factor) * 100  # 簡化吞吐量計算
            
            metrics[sat.satellite_id] = {
                "distance": distance,
                "elevation": elevation,
                "rsrp": rsrp,
                "rsrq": rsrq,
                "sinr": sinr,
                "throughput": throughput,
                "load": load_factor,
                "weather_impact": self._calculate_weather_impact(scenario.weather_conditions, elevation)
            }
        
        return metrics
    
    def _calculate_satellite_position(
        self, sat: SatelliteConfiguration, time_minute: int
    ) -> Tuple[float, float, float]:
        """計算衛星當前位置（簡化）"""
        
        # 簡化計算：假設衛星做圓形軌道運動
        orbital_period = 90 + (sat.orbital_position[2] - 500) / 10  # 簡化週期計算
        angular_speed = 2 * np.pi / orbital_period
        angle = time_minute * angular_speed
        
        # 基於初始位置計算偏移
        base_lat, base_lon, altitude = sat.orbital_position
        
        # 簡化的軌道運動
        lat_offset = 2 * np.sin(angle)
        lon_offset = 4 * np.cos(angle)
        
        return base_lat + lat_offset, base_lon + lon_offset, altitude
    
    def _calculate_distance_elevation(
        self, ue_lat: float, ue_lon: float, ue_alt: float,
        sat_lat: float, sat_lon: float, sat_alt: float
    ) -> Tuple[float, float]:
        """計算距離和仰角"""
        
        # 地球半徑
        earth_radius = 6371000  # meters
        
        # 轉換為弧度
        ue_lat_rad = np.radians(ue_lat)
        ue_lon_rad = np.radians(ue_lon)
        sat_lat_rad = np.radians(sat_lat)
        sat_lon_rad = np.radians(sat_lon)
        
        # 計算地面距離
        delta_lat = sat_lat_rad - ue_lat_rad
        delta_lon = sat_lon_rad - ue_lon_rad
        
        a = (np.sin(delta_lat/2)**2 + 
             np.cos(ue_lat_rad) * np.cos(sat_lat_rad) * np.sin(delta_lon/2)**2)
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        ground_distance = earth_radius * c
        
        # 計算仰角
        height_diff = (sat_alt * 1000) - ue_alt  # 轉換為meters
        slant_distance = np.sqrt(ground_distance**2 + height_diff**2)
        elevation = np.degrees(np.arctan(height_diff / ground_distance))
        
        return slant_distance / 1000, max(0, elevation)  # 返回km和度
    
    def _calculate_rsrp(self, distance_km: float, beam_coverage: float, interference: float) -> float:
        """計算RSRP"""
        
        # 簡化的路徑損耗計算
        freq_ghz = 20  # Ka band
        path_loss = 32.45 + 20 * np.log10(freq_ghz) + 20 * np.log10(distance_km)
        
        # 衛星發射功率和天線增益
        tx_power = 50  # dBm
        antenna_gain = 40  # dBi
        
        # 覆蓋範圍影響
        coverage_factor = max(0.1, 1 - (distance_km / beam_coverage))
        
        rsrp = tx_power + antenna_gain - path_loss + 10 * np.log10(coverage_factor)
        
        # 干擾影響
        rsrp -= interference * 10
        
        return rsrp
    
    def _calculate_rsrq(self, rsrp: float, interference: float, building_density: float) -> float:
        """計算RSRQ"""
        
        # RSRQ = RSRP - RSSI (簡化)
        interference_power = -100 + interference * 20 + building_density * 10
        rsrq = rsrp - interference_power
        
        return max(-20, min(-3, rsrq))
    
    def _calculate_sinr(self, rsrp: float, interference: float) -> float:
        """計算SINR"""
        
        noise_power = -110  # thermal noise
        interference_power = -100 + interference * 20
        
        signal_linear = 10**(rsrp/10)
        noise_interference_linear = 10**(noise_power/10) + 10**(interference_power/10)
        
        sinr = 10 * np.log10(signal_linear / noise_interference_linear)
        
        return max(-10, min(30, sinr))
    
    def _calculate_weather_impact(self, weather: Dict[str, float], elevation: float) -> float:
        """計算天氣影響"""
        
        # 降雨衰減
        rain_attenuation = weather["precipitation"] * (2 - elevation / 90)
        
        # 雲層衰減  
        cloud_attenuation = weather["cloud_cover"] * 0.5
        
        total_impact = rain_attenuation + cloud_attenuation
        
        return min(10, total_impact)
    
    def _select_best_satellite(
        self,
        satellite_metrics: Dict[str, Dict[str, float]],
        ue: UEConfiguration,
        algorithm: str
    ) -> Optional[str]:
        """選擇最佳衛星"""
        
        if not satellite_metrics:
            return None
        
        if algorithm == "traditional":
            # 傳統算法：基於RSRP
            best_sat = max(
                satellite_metrics.keys(),
                key=lambda s: satellite_metrics[s]["rsrp"]
            )
        elif algorithm == "ieee_infocom_2024":
            # IEEE INFOCOM 2024算法：綜合考量多個因素
            best_score = -float('inf')
            best_sat = None
            
            for sat_id, metrics in satellite_metrics.items():
                # 權重組合
                score = (
                    metrics["rsrp"] * 0.3 +
                    metrics["sinr"] * 0.25 +
                    metrics["elevation"] * 0.2 +
                    (100 - metrics["load"] * 100) * 0.15 +
                    (10 - metrics["weather_impact"]) * 0.1
                )
                
                if score > best_score:
                    best_score = score
                    best_sat = sat_id
        else:
            # 負載均衡算法
            best_sat = min(
                satellite_metrics.keys(),
                key=lambda s: satellite_metrics[s]["load"]
            )
        
        return best_sat
    
    def _determine_handover_trigger(
        self,
        current_sat: Optional[str],
        target_sat: str,
        metrics: Dict[str, Dict[str, float]],
        scenario: ScenarioEnvironment
    ) -> HandoverTriggerType:
        """確定換手觸發原因"""
        
        if current_sat is None:
            return HandoverTriggerType.SIGNAL_QUALITY
        
        current_metrics = metrics.get(current_sat, {})
        target_metrics = metrics.get(target_sat, {})
        
        # 檢查信號品質
        if current_metrics.get("rsrp", -100) < -90:
            return HandoverTriggerType.SIGNAL_QUALITY
        
        # 檢查負載
        if current_metrics.get("load", 0) > 0.8:
            return HandoverTriggerType.LOAD_BALANCING
        
        # 檢查干擾
        if scenario.interference_level > 0.6:
            return HandoverTriggerType.INTERFERENCE
        
        # 預測型換手
        return HandoverTriggerType.PREDICTION_BASED
    
    def _calculate_handover_performance(
        self,
        ue: UEConfiguration,
        source_sat: Optional[str],
        target_sat: str,
        scenario: ScenarioEnvironment,
        algorithm: str
    ) -> Tuple[float, bool, Optional[str]]:
        """計算換手性能"""
        
        # 基礎延遲
        if algorithm == "ieee_infocom_2024":
            base_latency = 35 + np.random.normal(0, 10)
        else:
            base_latency = 80 + np.random.normal(0, 20)
        
        # 場景影響
        scenario_factor = {
            TestScenarioType.URBAN_MOBILITY: 1.2,
            TestScenarioType.HIGHWAY_MOBILITY: 1.5,
            TestScenarioType.RURAL_COVERAGE: 1.0,
            TestScenarioType.EMERGENCY_RESPONSE: 0.8  # 優先處理
        }
        
        latency = base_latency * scenario_factor[scenario.scenario_type]
        
        # 環境影響
        latency += scenario.interference_level * 20
        latency += scenario.building_density * 15
        latency += sum(scenario.weather_conditions.values()) * 5
        
        # UE優先級影響
        latency *= (6 - ue.priority_level) / 5
        
        # 成功率計算
        success_prob = max(0.5, 1 - (latency / 300))  # 延遲越高成功率越低
        
        if algorithm == "ieee_infocom_2024":
            success_prob += 0.15  # 加速算法提升成功率
        
        success = np.random.random() < success_prob
        failure_reason = None if success else "handover_timeout"
        
        return max(0, latency), success, failure_reason
    
    def _calculate_prediction_accuracy(self, algorithm: str, scenario: ScenarioEnvironment) -> float:
        """計算預測精度"""
        
        base_accuracy = 0.9 if algorithm == "ieee_infocom_2024" else 0.7
        
        # 場景複雜度影響
        complexity_factor = (
            scenario.building_density * 0.3 +
            scenario.interference_level * 0.3 +
            (scenario.user_density / 1000) * 0.2
        )
        
        accuracy = base_accuracy - complexity_factor * 0.2
        
        return max(0.5, min(0.98, accuracy + np.random.normal(0, 0.05)))
    
    async def _analyze_scenario_performance(
        self,
        test_id: str,
        scenario: ScenarioEnvironment,
        handover_events: List[HandoverEvent],
        duration_hours: float,
        algorithm: str
    ) -> ScenarioTestResult:
        """分析場景性能"""
        
        total_handovers = len(handover_events)
        successful_handovers = sum(1 for event in handover_events if event.success)
        failed_handovers = total_handovers - successful_handovers
        
        # 基礎性能指標
        if total_handovers > 0:
            latencies = [event.handover_latency for event in handover_events]
            avg_latency = np.mean(latencies)
            max_latency = np.max(latencies)
            success_rate = successful_handovers / total_handovers
            
            prediction_accuracies = [event.prediction_accuracy for event in handover_events]
            avg_prediction_accuracy = np.mean(prediction_accuracies)
        else:
            avg_latency = max_latency = 0
            success_rate = 1.0
            avg_prediction_accuracy = 0.9
        
        performance_metrics = {
            "handover_success_rate": success_rate * 100,
            "average_handover_latency": avg_latency,
            "max_handover_latency": max_latency,
            "prediction_accuracy": avg_prediction_accuracy * 100,
            "handover_frequency": total_handovers / duration_hours,
            "interference_resilience": self._calculate_interference_resilience(handover_events),
            "mobility_adaptability": self._calculate_mobility_adaptability(handover_events, scenario),
            "environment_robustness": self._calculate_environment_robustness(handover_events, scenario)
        }
        
        # 場景特定指標
        scenario_specific_metrics = await self._calculate_scenario_specific_metrics(
            scenario, handover_events, duration_hours
        )
        
        # 驗證結果
        validation_results = await self._validate_scenario_requirements(
            scenario, performance_metrics, scenario_specific_metrics
        )
        
        # 生成建議
        recommendations = self._generate_scenario_recommendations(
            scenario, performance_metrics, validation_results
        )
        
        return ScenarioTestResult(
            test_id=test_id,
            scenario_id=scenario.scenario_id,
            test_start_time=datetime.now(),
            test_duration=duration_hours * 3600,
            total_ues=len(self.ue_configurations[scenario.scenario_id]),
            total_handovers=total_handovers,
            successful_handovers=successful_handovers,
            failed_handovers=failed_handovers,
            handover_events=handover_events,
            performance_metrics=performance_metrics,
            scenario_specific_metrics=scenario_specific_metrics,
            validation_results=validation_results,
            recommendations=recommendations
        )
    
    def _calculate_interference_resilience(self, events: List[HandoverEvent]) -> float:
        """計算干擾抗性"""
        
        if not events:
            return 100.0
        
        high_interference_events = [
            e for e in events if e.interference_impact > 0.6
        ]
        
        if not high_interference_events:
            return 100.0
        
        success_rate = sum(1 for e in high_interference_events if e.success) / len(high_interference_events)
        return success_rate * 100
    
    def _calculate_mobility_adaptability(self, events: List[HandoverEvent], scenario: ScenarioEnvironment) -> float:
        """計算移動適應性"""
        
        if not events:
            return 100.0
        
        # 根據場景類型計算不同的移動適應性
        if scenario.scenario_type == TestScenarioType.HIGHWAY_MOBILITY:
            # 高速移動場景
            high_speed_events = [e for e in events if "highway" in e.ue_id]
            if high_speed_events:
                success_rate = sum(1 for e in high_speed_events if e.success) / len(high_speed_events)
                return success_rate * 100
        
        # 通用移動適應性
        success_rate = sum(1 for e in events if e.success) / len(events)
        return success_rate * 100
    
    def _calculate_environment_robustness(self, events: List[HandoverEvent], scenario: ScenarioEnvironment) -> float:
        """計算環境魯棒性"""
        
        if not events:
            return 100.0
        
        # 考慮環境因素對成功率的影響
        environment_score = 0
        for event in events:
            env_factors = event.environment_factors
            env_complexity = (
                env_factors.get("building_density", 0) +
                env_factors.get("weather_impact", 0) +
                (env_factors.get("user_density", 0) / 1000)
            ) / 3
            
            if event.success:
                environment_score += (1 - env_complexity)
            else:
                environment_score += env_complexity * 0.2
        
        return min(100, (environment_score / len(events)) * 100)
    
    async def _calculate_scenario_specific_metrics(
        self,
        scenario: ScenarioEnvironment,
        events: List[HandoverEvent],
        duration_hours: float
    ) -> Dict[str, Any]:
        """計算場景特定指標"""
        
        metrics = {}
        
        if scenario.scenario_type == TestScenarioType.URBAN_MOBILITY:
            # 城市場景特定指標
            building_impact_events = [
                e for e in events if e.environment_factors.get("building_density", 0) > 0.5
            ]
            metrics.update({
                "building_shadowing_resilience": len([e for e in building_impact_events if e.success]) / max(1, len(building_impact_events)) * 100,
                "dense_user_performance": self._calculate_dense_user_performance(events),
                "urban_mobility_efficiency": self._calculate_urban_mobility_efficiency(events)
            })
        
        elif scenario.scenario_type == TestScenarioType.HIGHWAY_MOBILITY:
            # 高速公路場景特定指標
            metrics.update({
                "high_speed_handover_efficiency": self._calculate_high_speed_efficiency(events),
                "velocity_impact_factor": self._calculate_velocity_impact(events),
                "linear_coverage_continuity": self._calculate_coverage_continuity(events)
            })
        
        elif scenario.scenario_type == TestScenarioType.RURAL_COVERAGE:
            # 偏遠地區場景特定指標
            metrics.update({
                "sparse_coverage_effectiveness": self._calculate_sparse_coverage_effectiveness(events),
                "long_distance_communication_quality": self._calculate_long_distance_quality(events),
                "resource_efficiency": self._calculate_resource_efficiency(events, scenario)
            })
        
        elif scenario.scenario_type == TestScenarioType.EMERGENCY_RESPONSE:
            # 緊急救援場景特定指標
            emergency_events = [e for e in events if "emergency" in e.ue_id]
            metrics.update({
                "emergency_service_priority": len([e for e in emergency_events if e.success]) / max(1, len(emergency_events)) * 100,
                "disaster_resilience": self._calculate_disaster_resilience(events),
                "uav_coordination_efficiency": self._calculate_uav_coordination_efficiency(events)
            })
        
        return metrics
    
    def _calculate_dense_user_performance(self, events: List[HandoverEvent]) -> float:
        """計算密集用戶場景性能"""
        
        if not events:
            return 100.0
        
        # 模擬用戶密度對性能的影響
        success_rate = sum(1 for e in events if e.success) / len(events)
        return success_rate * 100
    
    def _calculate_urban_mobility_efficiency(self, events: List[HandoverEvent]) -> float:
        """計算城市移動效率"""
        
        if not events:
            return 100.0
        
        # 計算平均換手延遲作為效率指標
        latencies = [e.handover_latency for e in events if e.success]
        if latencies:
            avg_latency = np.mean(latencies)
            efficiency = max(0, 100 - (avg_latency / 5))  # 延遲越低效率越高
            return efficiency
        
        return 100.0
    
    def _calculate_high_speed_efficiency(self, events: List[HandoverEvent]) -> float:
        """計算高速移動效率"""
        
        highway_events = [e for e in events if "highway" in e.ue_id]
        if highway_events:
            success_rate = sum(1 for e in highway_events if e.success) / len(highway_events)
            return success_rate * 100
        
        return 100.0
    
    def _calculate_velocity_impact(self, events: List[HandoverEvent]) -> float:
        """計算速度影響因子"""
        
        if not events:
            return 1.0
        
        # 簡化計算：高速移動對延遲的影響
        highway_events = [e for e in events if "highway" in e.ue_id]
        other_events = [e for e in events if "highway" not in e.ue_id]
        
        if highway_events and other_events:
            highway_avg_latency = np.mean([e.handover_latency for e in highway_events])
            other_avg_latency = np.mean([e.handover_latency for e in other_events])
            
            return highway_avg_latency / other_avg_latency if other_avg_latency > 0 else 1.0
        
        return 1.0
    
    def _calculate_coverage_continuity(self, events: List[HandoverEvent]) -> float:
        """計算覆蓋連續性"""
        
        if not events:
            return 100.0
        
        # 計算成功換手的連續性
        success_rate = sum(1 for e in events if e.success) / len(events)
        return success_rate * 100
    
    def _calculate_sparse_coverage_effectiveness(self, events: List[HandoverEvent]) -> float:
        """計算稀疏覆蓋有效性"""
        
        if not events:
            return 100.0
        
        # 在衛星較少的情況下的覆蓋效果
        success_rate = sum(1 for e in events if e.success) / len(events)
        return success_rate * 100
    
    def _calculate_long_distance_quality(self, events: List[HandoverEvent]) -> float:
        """計算長距離通訊品質"""
        
        if not events:
            return 100.0
        
        # 基於成功率的長距離通訊品質
        success_rate = sum(1 for e in events if e.success) / len(events)
        return success_rate * 100
    
    def _calculate_resource_efficiency(self, events: List[HandoverEvent], scenario: ScenarioEnvironment) -> float:
        """計算資源效率"""
        
        if not events:
            return 100.0
        
        # 偏遠地區的資源使用效率
        total_ues = len(self.ue_configurations[scenario.scenario_id])
        handover_per_ue = len(events) / total_ues if total_ues > 0 else 0
        
        # 換手次數適中表示資源效率高
        optimal_handover_rate = 5  # 每UE每小時5次換手為最佳
        efficiency = max(0, 100 - abs(handover_per_ue - optimal_handover_rate) * 10)
        
        return efficiency
    
    def _calculate_disaster_resilience(self, events: List[HandoverEvent]) -> float:
        """計算災害抗性"""
        
        if not events:
            return 100.0
        
        # 在高干擾環境下的性能
        high_interference_events = [
            e for e in events if e.interference_impact > 0.7
        ]
        
        if high_interference_events:
            success_rate = sum(1 for e in high_interference_events if e.success) / len(high_interference_events)
            return success_rate * 100
        
        return 100.0
    
    def _calculate_uav_coordination_efficiency(self, events: List[HandoverEvent]) -> float:
        """計算UAV協調效率"""
        
        uav_events = [e for e in events if "uav" in e.ue_id]
        if uav_events:
            success_rate = sum(1 for e in uav_events if e.success) / len(uav_events)
            return success_rate * 100
        
        return 100.0
    
    async def _validate_scenario_requirements(
        self,
        scenario: ScenarioEnvironment,
        performance_metrics: Dict[str, float],
        scenario_specific_metrics: Dict[str, Any]
    ) -> Dict[str, bool]:
        """驗證場景需求"""
        
        validation_results = {}
        
        # 通用需求驗證
        validation_results["handover_success_rate_target"] = performance_metrics["handover_success_rate"] >= 90.0
        validation_results["latency_requirement"] = performance_metrics["average_handover_latency"] <= 100.0
        validation_results["prediction_accuracy_target"] = performance_metrics["prediction_accuracy"] >= 85.0
        
        # 場景特定需求驗證
        if scenario.scenario_type == TestScenarioType.URBAN_MOBILITY:
            validation_results["building_interference_resilience"] = scenario_specific_metrics.get("building_shadowing_resilience", 0) >= 80.0
            validation_results["dense_user_handling"] = scenario_specific_metrics.get("dense_user_performance", 0) >= 85.0
        
        elif scenario.scenario_type == TestScenarioType.HIGHWAY_MOBILITY:
            validation_results["high_speed_performance"] = scenario_specific_metrics.get("high_speed_handover_efficiency", 0) >= 75.0
            validation_results["velocity_adaptation"] = scenario_specific_metrics.get("velocity_impact_factor", 10) <= 2.0
        
        elif scenario.scenario_type == TestScenarioType.RURAL_COVERAGE:
            validation_results["sparse_coverage_adequacy"] = scenario_specific_metrics.get("sparse_coverage_effectiveness", 0) >= 70.0
            validation_results["resource_optimization"] = scenario_specific_metrics.get("resource_efficiency", 0) >= 75.0
        
        elif scenario.scenario_type == TestScenarioType.EMERGENCY_RESPONSE:
            validation_results["emergency_priority_handling"] = scenario_specific_metrics.get("emergency_service_priority", 0) >= 95.0
            validation_results["disaster_environment_resilience"] = scenario_specific_metrics.get("disaster_resilience", 0) >= 80.0
        
        return validation_results
    
    def _generate_scenario_recommendations(
        self,
        scenario: ScenarioEnvironment,
        performance_metrics: Dict[str, float],
        validation_results: Dict[str, bool]
    ) -> List[str]:
        """生成場景建議"""
        
        recommendations = []
        
        # 基於驗證結果的建議
        failed_validations = [k for k, v in validation_results.items() if not v]
        
        if "handover_success_rate_target" in failed_validations:
            recommendations.append("建議增加衛星數量或優化換手算法以提升成功率")
        
        if "latency_requirement" in failed_validations:
            recommendations.append("建議調整預測算法參數以降低換手延遲")
        
        if "prediction_accuracy_target" in failed_validations:
            recommendations.append("建議加強機器學習模型訓練以提升預測精度")
        
        # 場景特定建議
        if scenario.scenario_type == TestScenarioType.URBAN_MOBILITY:
            if performance_metrics["average_handover_latency"] > 80:
                recommendations.append("城市場景建議部署更多低軌衛星以減少遮蔽影響")
            
            if performance_metrics.get("interference_resilience", 100) < 80:
                recommendations.append("建議增強干擾抑制技術以應對城市電磁環境")
        
        elif scenario.scenario_type == TestScenarioType.HIGHWAY_MOBILITY:
            if "high_speed_performance" in failed_validations:
                recommendations.append("高速場景建議優化都卜勒頻移補償算法")
            
            recommendations.append("建議沿高速公路部署線性衛星覆蓋模式")
        
        elif scenario.scenario_type == TestScenarioType.RURAL_COVERAGE:
            if "sparse_coverage_adequacy" in failed_validations:
                recommendations.append("偏遠地區建議採用高軌衛星補充覆蓋空隙")
            
            recommendations.append("建議優化功率控制以延長偏遠地區設備電池壽命")
        
        elif scenario.scenario_type == TestScenarioType.EMERGENCY_RESPONSE:
            if "emergency_priority_handling" in failed_validations:
                recommendations.append("緊急場景建議實施優先級排程機制")
            
            recommendations.append("建議部署快速部署衛星以應對災害場景")
        
        # 性能優化建議
        if performance_metrics["handover_frequency"] > 10:
            recommendations.append("換手頻率過高，建議調整換手閾值或增加遲滯機制")
        
        if len(recommendations) == 0:
            recommendations.append("系統性能表現良好，建議持續監控並進行定期優化")
        
        return recommendations
    
    async def get_scenario_test_results(self, scenario_id: str) -> List[Dict[str, Any]]:
        """獲取場景測試結果"""
        
        if scenario_id not in self.test_results:
            return []
        
        results = []
        for test_result in self.test_results[scenario_id]:
            result_summary = {
                "test_id": test_result.test_id,
                "scenario_id": test_result.scenario_id,
                "test_start_time": test_result.test_start_time.isoformat(),
                "total_handovers": test_result.total_handovers,
                "success_rate": round(test_result.performance_metrics["handover_success_rate"], 2),
                "average_latency": round(test_result.performance_metrics["average_handover_latency"], 2),
                "prediction_accuracy": round(test_result.performance_metrics["prediction_accuracy"], 2),
                "validation_passed": sum(test_result.validation_results.values()),
                "validation_total": len(test_result.validation_results),
                "recommendations_count": len(test_result.recommendations)
            }
            results.append(result_summary)
        
        return results
    
    async def get_scenario_summary(self) -> Dict[str, Any]:
        """獲取所有場景的摘要"""
        
        summary = {
            "total_scenarios": len(self.scenarios),
            "scenarios": [],
            "overall_statistics": {
                "total_tests": 0,
                "total_handovers": 0,
                "overall_success_rate": 0.0,
                "average_latency": 0.0
            }
        }
        
        total_tests = 0
        total_handovers = 0
        total_successful = 0
        total_latency = 0
        
        for scenario_id, scenario in self.scenarios.items():
            test_results = self.test_results.get(scenario_id, [])
            
            scenario_stats = {
                "scenario_id": scenario_id,
                "scenario_type": scenario.scenario_type.value,
                "test_count": len(test_results),
                "latest_performance": None
            }
            
            if test_results:
                latest = test_results[-1]
                scenario_stats["latest_performance"] = {
                    "success_rate": round(latest.performance_metrics["handover_success_rate"], 2),
                    "average_latency": round(latest.performance_metrics["average_handover_latency"], 2),
                    "test_time": latest.test_start_time.isoformat()
                }
                
                # 累計統計
                total_tests += len(test_results)
                for result in test_results:
                    total_handovers += result.total_handovers
                    total_successful += result.successful_handovers
                    if result.total_handovers > 0:
                        total_latency += result.performance_metrics["average_handover_latency"]
            
            summary["scenarios"].append(scenario_stats)
        
        # 計算整體統計
        if total_tests > 0:
            summary["overall_statistics"] = {
                "total_tests": total_tests,
                "total_handovers": total_handovers,
                "overall_success_rate": round((total_successful / max(1, total_handovers)) * 100, 2),
                "average_latency": round(total_latency / total_tests, 2)
            }
        
        return summary

# 全域服務實例
scenario_test_environment = ScenarioTestEnvironment()