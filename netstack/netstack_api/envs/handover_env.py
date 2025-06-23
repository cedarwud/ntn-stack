"""
LEO 衛星切換 Gymnasium 環境

提供標準化的 RL 環境用於 LEO 衛星切換決策優化：
- 狀態空間：UE 位置、衛星狀態、網路負載、信號品質等
- 動作空間：切換決策、目標衛星選擇、時機控制
- 獎勵函數：基於切換延遲、服務品質、用戶滿意度的多目標優化

支援多種切換場景：
- 單UE單衛星切換
- 多UE協調切換  
- 大規模constellation場景
"""

import asyncio
import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import json
import time
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class HandoverScenario(Enum):
    """切換場景類型"""
    SINGLE_UE = "single_ue"  # 單UE場景
    MULTI_UE = "multi_ue"    # 多UE場景  
    EMERGENCY = "emergency"   # 緊急切換
    LOAD_BALANCE = "load_balance"  # 負載平衡


@dataclass
class UEState:
    """UE 狀態資訊"""
    ue_id: str
    latitude: float
    longitude: float 
    altitude: float = 0.0
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (vx, vy, vz)
    current_satellite: Optional[str] = None
    signal_strength: float = 0.0  # dBm
    sinr: float = 0.0  # dB
    throughput: float = 0.0  # Mbps
    latency: float = 0.0  # ms
    packet_loss: float = 0.0  # %
    battery_level: float = 100.0  # %
    service_type: str = "default"  # eMBB, URLLC, mMTC
    qos_requirements: Dict[str, float] = field(default_factory=dict)


@dataclass 
class SatelliteState:
    """衛星狀態資訊"""
    satellite_id: str
    latitude: float
    longitude: float
    altitude: float
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    elevation_angle: float = 0.0  # 相對於UE的仰角
    azimuth_angle: float = 0.0    # 相對於UE的方位角
    distance: float = 0.0         # 與UE的距離 (km)
    load_factor: float = 0.0      # 負載因子 0-1
    available_bandwidth: float = 0.0  # MHz
    beam_coverage: List[Tuple[float, float]] = field(default_factory=list)  # 波束覆蓋範圍
    handover_count: int = 0       # 當前時段切換次數
    is_available: bool = True


@dataclass
class HandoverAction:
    """切換動作"""
    ue_id: str
    action_type: str  # "no_handover", "trigger_handover", "prepare_handover"
    target_satellite: Optional[str] = None
    handover_timing: float = 0.0  # 延遲時間 (秒)
    power_control: float = 1.0    # 功率控制因子 0-1
    priority: float = 0.5         # 切換優先級 0-1
    resource_allocation: Dict[str, float] = field(default_factory=dict)


@dataclass
class NetworkEnvironment:
    """網路環境狀態"""
    current_time: datetime
    weather_condition: str = "clear"  # clear, cloudy, rainy, stormy
    interference_level: float = 0.0   # 干擾水平 0-1
    network_congestion: float = 0.0   # 網路壅塞度 0-1
    satellite_constellation_size: int = 0
    active_ue_count: int = 0
    total_handover_rate: float = 0.0  # 系統整體切換率


class LEOSatelliteHandoverEnv(gym.Env):
    """LEO 衛星切換 Gymnasium 環境"""
    
    metadata = {"render_modes": ["human", "console"], "render_fps": 4}
    
    def __init__(
        self,
        scenario: HandoverScenario = HandoverScenario.SINGLE_UE,
        max_ues: int = 10,
        max_satellites: int = 50,
        episode_length: int = 1000,
        netstack_api_url: str = "http://netstack-api:8080",
        simworld_api_url: str = "http://simworld_backend:8888",
        config: Optional[Dict] = None
    ):
        super().__init__()
        
        self.scenario = scenario
        self.max_ues = max_ues
        self.max_satellites = max_satellites  
        self.episode_length = episode_length
        self.netstack_api_url = netstack_api_url
        self.simworld_api_url = simworld_api_url
        self.config = config or {}
        
        # 環境狀態
        self.current_step = 0
        self.episode_start_time = None
        self.ue_states: Dict[str, UEState] = {}
        self.satellite_states: Dict[str, SatelliteState] = {}
        self.network_environment = NetworkEnvironment(current_time=datetime.utcnow())
        self.handover_history: List[Dict] = []
        
        # 性能指標
        self.total_handovers = 0
        self.successful_handovers = 0
        self.total_handover_latency = 0.0
        self.service_interruptions = 0
        self.average_sinr = 0.0
        
        # 定義觀測空間和動作空間
        self._setup_spaces()
        
        # HTTP 客戶端
        self.http_client = None
        
    def _setup_spaces(self):
        """設置觀測空間和動作空間"""
        
        # 觀測空間：UE狀態 + 衛星狀態 + 網路環境
        # 每個UE: 位置(3) + 速度(3) + 信號品質(4) + 服務參數(3) = 13個特徵
        # 每顆衛星: 位置(3) + 角度(2) + 距離(1) + 負載(2) + 可用性(1) = 9個特徵  
        # 網路環境: 時間(1) + 天氣(1) + 干擾(1) + 壅塞(1) + 統計(3) = 7個特徵
        
        ue_features = 13
        satellite_features = 9  
        env_features = 7
        
        obs_size = (
            self.max_ues * ue_features + 
            self.max_satellites * satellite_features + 
            env_features
        )
        
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf, 
            shape=(obs_size,),
            dtype=np.float32
        )
        
        # 動作空間：每個UE的切換決策
        # 每個UE動作: 動作類型(3) + 目標衛星ID(max_satellites) + 時機(1) + 功率(1) + 優先級(1)
        if self.scenario == HandoverScenario.SINGLE_UE:
            # 單UE場景：簡化動作空間
            self.action_space = spaces.Dict({
                "handover_decision": spaces.Discrete(3),  # 0: no_handover, 1: trigger, 2: prepare
                "target_satellite": spaces.Discrete(self.max_satellites),
                "timing": spaces.Box(low=0.0, high=10.0, shape=(1,), dtype=np.float32),
                "power_control": spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32),
                "priority": spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
            })
        else:
            # 多UE場景：複雜動作空間
            self.action_space = spaces.Box(
                low=0.0,
                high=1.0,
                shape=(self.max_ues * 6,),  # 每個UE 6個動作參數
                dtype=np.float32
            )
    
    async def _get_http_client(self):
        """獲取HTTP客戶端"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client
    
    async def _fetch_real_data(self) -> Dict[str, Any]:
        """從真實服務獲取數據"""
        try:
            client = await self._get_http_client()
            
            # 並行獲取數據
            tasks = [
                client.get(f"{self.netstack_api_url}/api/v1/satellites/positions"),
                client.get(f"{self.simworld_api_url}/api/handover/status"),
                client.get(f"{self.netstack_api_url}/api/v1/ues/active")
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            satellite_data = responses[0].json() if not isinstance(responses[0], Exception) else {}
            handover_data = responses[1].json() if not isinstance(responses[1], Exception) else {}
            ue_data = responses[2].json() if not isinstance(responses[2], Exception) else {}
            
            return {
                "satellites": satellite_data,
                "handover": handover_data, 
                "ues": ue_data
            }
            
        except Exception as e:
            logger.warning(f"無法獲取真實數據，使用模擬數據: {e}")
            return self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """生成模擬數據"""
        
        # 生成模擬衛星數據
        satellites = {}
        for i in range(min(20, self.max_satellites)):
            sat_id = f"LEO-{i:03d}"
            satellites[sat_id] = SatelliteState(
                satellite_id=sat_id,
                latitude=random.uniform(-60, 60),
                longitude=random.uniform(-180, 180),
                altitude=random.uniform(500, 1200),  # LEO altitude
                elevation_angle=random.uniform(10, 90),
                distance=random.uniform(500, 2000),
                load_factor=random.uniform(0.1, 0.9),
                available_bandwidth=random.uniform(10, 100),
                is_available=random.random() > 0.1
            )
        
        # 生成模擬UE數據
        ues = {}
        for i in range(min(5, self.max_ues)):
            ue_id = f"UE-{i:03d}"
            ues[ue_id] = UEState(
                ue_id=ue_id,
                latitude=random.uniform(-45, 45),
                longitude=random.uniform(-120, 120),
                current_satellite=random.choice(list(satellites.keys())),
                signal_strength=random.uniform(-120, -60),
                sinr=random.uniform(-5, 30),
                throughput=random.uniform(1, 100),
                latency=random.uniform(10, 200)
            )
        
        return {
            "satellites": satellites,
            "ues": ues,
            "handover": {"active_handovers": [], "total_count": 0}
        }
    
    def reset(self, seed=None, options=None):
        """重置環境"""
        super().reset(seed=seed)
        
        self.current_step = 0
        self.episode_start_time = datetime.utcnow()
        self.total_handovers = 0
        self.successful_handovers = 0
        self.total_handover_latency = 0.0
        self.service_interruptions = 0
        self.handover_history.clear()
        
        # 獲取初始數據（同步版本）
        try:
            # 使用 asyncio.run 來運行異步函數
            data = asyncio.run(self._fetch_real_data())
        except Exception as e:
            logger.warning(f"獲取真實數據失敗，使用模擬數據: {e}")
            data = self._generate_mock_data()
        
        # 更新狀態
        self.satellite_states = data.get("satellites", {})
        self.ue_states = data.get("ues", {})
        
        # 更新網路環境
        self.network_environment = NetworkEnvironment(
            current_time=self.episode_start_time,
            satellite_constellation_size=len(self.satellite_states),
            active_ue_count=len(self.ue_states)
        )
        
        observation = self._get_observation()
        info = self._get_info()
        
        logger.info(f"環境重置完成，UE數量: {len(self.ue_states)}, 衛星數量: {len(self.satellite_states)}")
        
        return observation, info
    
    def step(self, action):
        """執行一步環境交互"""
        self.current_step += 1
        
        # 解析動作
        handover_actions = self._parse_action(action)
        
        # 執行切換決策
        handover_results = self._execute_handovers(handover_actions)
        
        # 更新環境狀態
        self._update_environment()
        
        # 計算獎勵
        reward = self._calculate_reward(handover_actions, handover_results)
        
        # 檢查終止條件
        terminated = self.current_step >= self.episode_length
        truncated = False
        
        # 獲取觀測
        observation = self._get_observation()
        info = self._get_info()
        info.update({
            "handover_results": handover_results,
            "step": self.current_step
        })
        
        return observation, reward, terminated, truncated, info
    
    def _parse_action(self, action) -> List[HandoverAction]:
        """解析動作"""
        handover_actions = []
        
        if self.scenario == HandoverScenario.SINGLE_UE:
            # 單UE場景
            ue_id = list(self.ue_states.keys())[0] if self.ue_states else "UE-001"
            
            action_type_map = ["no_handover", "trigger_handover", "prepare_handover"]
            action_type = action_type_map[action["handover_decision"]]
            
            target_satellite = None
            if action_type != "no_handover":
                sat_ids = list(self.satellite_states.keys())
                if sat_ids and action["target_satellite"] < len(sat_ids):
                    target_satellite = sat_ids[action["target_satellite"]]
            
            handover_actions.append(HandoverAction(
                ue_id=ue_id,
                action_type=action_type,
                target_satellite=target_satellite,
                handover_timing=float(action["timing"][0]),
                power_control=float(action["power_control"][0]),
                priority=float(action["priority"][0])
            ))
        else:
            # 多UE場景
            action_array = np.array(action).reshape(-1, 6)
            for i, ue_id in enumerate(list(self.ue_states.keys())[:self.max_ues]):
                if i < len(action_array):
                    act = action_array[i]
                    
                    # 動作類型 (0-1 -> 離散)
                    if act[0] < 0.33:
                        action_type = "no_handover"
                    elif act[0] < 0.67:
                        action_type = "prepare_handover"
                    else:
                        action_type = "trigger_handover"
                    
                    # 目標衛星選擇
                    target_satellite = None
                    if action_type != "no_handover":
                        sat_ids = list(self.satellite_states.keys())
                        if sat_ids:
                            sat_idx = int(act[1] * len(sat_ids))
                            target_satellite = sat_ids[min(sat_idx, len(sat_ids) - 1)]
                    
                    handover_actions.append(HandoverAction(
                        ue_id=ue_id,
                        action_type=action_type,
                        target_satellite=target_satellite,
                        handover_timing=act[2] * 10.0,  # 0-10秒
                        power_control=act[3],
                        priority=act[4]
                    ))
        
        return handover_actions
    
    def _execute_handovers(self, handover_actions: List[HandoverAction]) -> List[Dict]:
        """執行切換操作"""
        results = []
        
        for action in handover_actions:
            if action.action_type == "no_handover":
                results.append({
                    "ue_id": action.ue_id,
                    "status": "no_action",
                    "latency": 0.0,
                    "success": True
                })
                continue
            
            # 模擬切換執行
            success_prob = self._calculate_handover_success_probability(action)
            success = random.random() < success_prob
            
            if success:
                # 成功切換
                latency = self._simulate_handover_latency(action)
                
                # 更新UE狀態
                if action.ue_id in self.ue_states:
                    self.ue_states[action.ue_id].current_satellite = action.target_satellite
                    # 模擬信號品質改善
                    self.ue_states[action.ue_id].sinr += random.uniform(2, 8)
                    self.ue_states[action.ue_id].throughput += random.uniform(5, 20)
                
                self.successful_handovers += 1
                self.total_handover_latency += latency
                
                results.append({
                    "ue_id": action.ue_id,
                    "status": "success",
                    "latency": latency,
                    "success": True,
                    "target_satellite": action.target_satellite
                })
            else:
                # 切換失敗
                self.service_interruptions += 1
                results.append({
                    "ue_id": action.ue_id,
                    "status": "failed", 
                    "latency": 0.0,
                    "success": False
                })
            
            self.total_handovers += 1
        
        # 記錄切換歷史
        self.handover_history.extend([{
            "step": self.current_step,
            "timestamp": datetime.utcnow().isoformat(),
            "action": asdict(action),
            "result": result
        } for action, result in zip(handover_actions, results)])
        
        return results
    
    def _calculate_handover_success_probability(self, action: HandoverAction) -> float:
        """計算切換成功概率"""
        base_prob = 0.95
        
        # 根據目標衛星狀態調整
        if action.target_satellite and action.target_satellite in self.satellite_states:
            sat_state = self.satellite_states[action.target_satellite]
            
            # 負載因子影響
            base_prob *= (1.0 - sat_state.load_factor * 0.2)
            
            # 仰角影響 (低仰角降低成功率)
            if sat_state.elevation_angle < 20:
                base_prob *= 0.8
            
            # 可用性影響
            if not sat_state.is_available:
                base_prob *= 0.1
        
        # 時機影響 (太急或太慢都不好)
        timing_factor = 1.0 - abs(action.handover_timing - 2.0) / 10.0
        base_prob *= max(0.5, timing_factor)
        
        # 優先級影響
        base_prob *= (0.8 + action.priority * 0.2)
        
        return min(1.0, max(0.1, base_prob))
    
    def _simulate_handover_latency(self, action: HandoverAction) -> float:
        """模擬切換延遲"""
        # 基準延遲 (論文目標 20-30ms)
        base_latency = random.uniform(20, 30)
        
        # 時機影響
        timing_penalty = max(0, action.handover_timing - 1.0) * 5  # 延遲時機增加延遲
        
        # 目標衛星負載影響
        load_penalty = 0
        if action.target_satellite and action.target_satellite in self.satellite_states:
            sat_state = self.satellite_states[action.target_satellite]
            load_penalty = sat_state.load_factor * 10
        
        # 網路壅塞影響
        congestion_penalty = self.network_environment.network_congestion * 15
        
        total_latency = base_latency + timing_penalty + load_penalty + congestion_penalty
        
        return max(10.0, total_latency)  # 最小10ms
    
    def _update_environment(self):
        """更新環境狀態"""
        # 更新時間
        self.network_environment.current_time += timedelta(seconds=1)
        
        # 更新UE位置 (簡單的移動模型)
        for ue_state in self.ue_states.values():
            # 模擬UE移動
            ue_state.latitude += random.uniform(-0.001, 0.001)
            ue_state.longitude += random.uniform(-0.001, 0.001)
            
            # 模擬信號品質變化
            ue_state.signal_strength += random.uniform(-2, 2)
            ue_state.sinr += random.uniform(-1, 1)
            
            # 限制範圍
            ue_state.signal_strength = max(-130, min(-50, ue_state.signal_strength))
            ue_state.sinr = max(-10, min(40, ue_state.sinr))
        
        # 更新衛星狀態 (簡化的軌道運動)
        for sat_state in self.satellite_states.values():
            # 模擬衛星軌道運動
            sat_state.longitude += random.uniform(-0.1, 0.1)  # 簡化軌道運動
            
            # 更新負載
            sat_state.load_factor += random.uniform(-0.1, 0.1)
            sat_state.load_factor = max(0.0, min(1.0, sat_state.load_factor))
        
        # 更新網路環境
        self.network_environment.interference_level = max(0.0, min(1.0, 
            self.network_environment.interference_level + random.uniform(-0.1, 0.1)))
        self.network_environment.network_congestion = max(0.0, min(1.0,
            self.network_environment.network_congestion + random.uniform(-0.05, 0.05)))
    
    def _calculate_reward(self, actions: List[HandoverAction], results: List[Dict]) -> float:
        """計算獎勵函數"""
        total_reward = 0.0
        
        for action, result in zip(actions, results):
            if action.action_type == "no_handover":
                # 不切換的獎勵：維持服務連續性
                total_reward += 1.0
                continue
            
            if result["success"]:
                # 成功切換的獎勵
                latency = result.get("latency", 50.0)
                
                # 延遲獎勵 (越低越好)
                latency_reward = max(0, 100 - latency) / 100.0 * 10
                
                # 服務品質改善獎勵
                ue_id = action.ue_id
                if ue_id in self.ue_states:
                    ue_state = self.ue_states[ue_id]
                    sinr_reward = max(0, ue_state.sinr) / 40.0 * 5  # SINR正規化獎勵
                    throughput_reward = min(ue_state.throughput / 100.0, 1.0) * 3
                else:
                    sinr_reward = throughput_reward = 0
                
                # 時機獎勵 (適當的時機)
                timing_reward = max(0, 5 - abs(action.handover_timing - 2.0)) / 5.0 * 2
                
                total_reward += latency_reward + sinr_reward + throughput_reward + timing_reward
                
            else:
                # 切換失敗的懲罰
                total_reward -= 10.0
        
        # 系統級獎勵/懲罰
        
        # 過多切換的懲罰
        handover_rate = len([a for a in actions if a.action_type != "no_handover"]) / len(actions)
        if handover_rate > 0.5:  # 超過50%的UE執行切換
            total_reward -= (handover_rate - 0.5) * 20
        
        # 負載平衡獎勵
        if self.satellite_states:
            load_variance = np.var([s.load_factor for s in self.satellite_states.values()])
            load_balance_reward = max(0, 0.2 - load_variance) * 10
            total_reward += load_balance_reward
        
        # 服務中斷懲罰
        if self.service_interruptions > 0:
            total_reward -= self.service_interruptions * 5
        
        return total_reward
    
    def _get_observation(self) -> np.ndarray:
        """獲取當前觀測"""
        obs = []
        
        # UE狀態特徵
        ue_count = 0
        for ue_id in sorted(self.ue_states.keys())[:self.max_ues]:
            ue_state = self.ue_states[ue_id]
            ue_features = [
                ue_state.latitude / 90.0,  # 正規化緯度
                ue_state.longitude / 180.0,  # 正規化經度  
                ue_state.altitude / 1000.0,  # 正規化高度
                ue_state.velocity[0] / 100.0,  # 正規化速度
                ue_state.velocity[1] / 100.0,
                ue_state.velocity[2] / 100.0,
                (ue_state.signal_strength + 130) / 80.0,  # 正規化信號強度
                (ue_state.sinr + 10) / 50.0,  # 正規化SINR
                ue_state.throughput / 100.0,  # 正規化吞吐量
                ue_state.latency / 200.0,  # 正規化延遲
                ue_state.packet_loss,  # 封包遺失率
                ue_state.battery_level / 100.0,  # 正規化電池電量
                1.0 if ue_state.current_satellite else 0.0  # 是否有連接衛星
            ]
            obs.extend(ue_features)
            ue_count += 1
        
        # 填充剩餘UE位置
        for _ in range(self.max_ues - ue_count):
            obs.extend([0.0] * 13)
        
        # 衛星狀態特徵
        sat_count = 0
        for sat_id in sorted(self.satellite_states.keys())[:self.max_satellites]:
            sat_state = self.satellite_states[sat_id]
            sat_features = [
                sat_state.latitude / 90.0,  # 正規化緯度
                sat_state.longitude / 180.0,  # 正規化經度
                sat_state.altitude / 2000.0,  # 正規化高度 (LEO最高約2000km)
                sat_state.elevation_angle / 90.0,  # 正規化仰角
                sat_state.azimuth_angle / 360.0,  # 正規化方位角
                sat_state.distance / 2000.0,  # 正規化距離
                sat_state.load_factor,  # 負載因子
                sat_state.available_bandwidth / 100.0,  # 正規化頻寬
                1.0 if sat_state.is_available else 0.0  # 可用性
            ]
            obs.extend(sat_features)
            sat_count += 1
        
        # 填充剩餘衛星位置
        for _ in range(self.max_satellites - sat_count):
            obs.extend([0.0] * 9)
        
        # 網路環境特徵
        env_features = [
            self.current_step / self.episode_length,  # 正規化時間進度
            {"clear": 0.0, "cloudy": 0.25, "rainy": 0.5, "stormy": 1.0}.get(
                self.network_environment.weather_condition, 0.0),
            self.network_environment.interference_level,
            self.network_environment.network_congestion,
            self.network_environment.satellite_constellation_size / self.max_satellites,
            self.network_environment.active_ue_count / self.max_ues,
            self.network_environment.total_handover_rate
        ]
        obs.extend(env_features)
        
        return np.array(obs, dtype=np.float32)
    
    def _get_info(self) -> Dict[str, Any]:
        """獲取額外資訊"""
        handover_success_rate = (
            self.successful_handovers / max(1, self.total_handovers)
        )
        average_latency = (
            self.total_handover_latency / max(1, self.successful_handovers)
        )
        
        avg_sinr = 0.0
        if self.ue_states:
            avg_sinr = sum(ue.sinr for ue in self.ue_states.values()) / len(self.ue_states)
        
        return {
            "episode_step": self.current_step,
            "total_handovers": self.total_handovers,
            "successful_handovers": self.successful_handovers,
            "handover_success_rate": handover_success_rate,
            "average_handover_latency": average_latency,
            "service_interruptions": self.service_interruptions,
            "average_sinr": avg_sinr,
            "active_ue_count": len(self.ue_states),
            "active_satellite_count": len(self.satellite_states),
            "network_congestion": self.network_environment.network_congestion,
            "handover_history_length": len(self.handover_history)
        }
    
    def render(self, mode="human"):
        """渲染環境狀態"""
        if mode == "console":
            print(f"\n=== LEO Satellite Handover Environment ===")
            print(f"Step: {self.current_step}/{self.episode_length}")
            print(f"Active UEs: {len(self.ue_states)}")
            print(f"Active Satellites: {len(self.satellite_states)}")
            print(f"Total Handovers: {self.total_handovers}")
            print(f"Success Rate: {self.successful_handovers/max(1,self.total_handovers):.2%}")
            if self.successful_handovers > 0:
                avg_latency = self.total_handover_latency / self.successful_handovers
                print(f"Average Latency: {avg_latency:.1f}ms")
            print(f"Service Interruptions: {self.service_interruptions}")
            print("=" * 45)
    
    def close(self):
        """關閉環境"""
        if self.http_client:
            asyncio.run(self.http_client.aclose())