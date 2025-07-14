"""
LEO 衛星環境 - Phase 2.1 衛星軌道動力學整合

基於 SimWorld TLE 數據的真實 LEO 衛星換手決策環境
實現了 fallback 機制確保在 SimWorld 服務不可用時的穩定性
"""

import asyncio
import logging
import numpy as np
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import gymnasium as gym
from gymnasium import spaces

logger = logging.getLogger(__name__)


@dataclass
class SatelliteState:
    """衛星狀態資訊"""

    id: int
    name: str
    position: Dict[str, float]  # lat, lon, alt, elevation, azimuth, range
    signal_quality: Dict[str, float]  # rsrp, rsrq, sinr
    load_factor: float
    timestamp: str


@dataclass
class HandoverMetrics:
    """換手指標"""

    rsrp: float  # 接收信號強度
    rsrq: float  # 接收信號品質
    sinr: float  # 信號干擾雜訊比
    load_factor: float  # 負載因子
    handover_probability: float  # 換手機率


@dataclass
class OrbitEvent:
    """軌道事件"""

    event_type: str  # 'elevation_change', 'handover_opportunity', 'signal_degradation'
    timestamp: datetime
    satellite_id: int
    trigger_value: float
    prediction_confidence: float
    event_data: Dict[str, Any]


@dataclass
class CandidateScore:
    """候選衛星評分"""

    satellite_id: int
    signal_score: float
    load_score: float
    elevation_score: float
    distance_score: float
    overall_score: float
    score_breakdown: Dict[str, float]


class LEOSatelliteEnvironment(gym.Env):
    """
    LEO 衛星換手決策環境

    基於真實 TLE 數據和信號傳播模型的強化學習環境
    支援 DQN、PPO、SAC 算法訓練
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LEO 衛星環境

        Args:
            config: 環境配置
                - simworld_url: SimWorld API 端點
                - max_satellites: 最大候選衛星數量
                - scenario: 場景類型 (urban, suburban, rural)
                - min_elevation: 最小仰角要求
                - fallback_enabled: 是否啟用 fallback 機制
        """
        super().__init__()

        # 配置參數
        self.simworld_url = config.get("simworld_url", "http://localhost:8888")
        self.max_satellites = config.get("max_satellites", 6)
        self.scenario = config.get("scenario", "urban")
        self.min_elevation = config.get("min_elevation", 10.0)
        self.fallback_enabled = config.get("fallback_enabled", True)

        # 🚀 新增：軌道動力學參數
        self.orbit_update_interval = config.get(
            "orbit_update_interval", 5.0
        )  # 軌道更新間隔（秒）
        self.handover_prediction_horizon = config.get(
            "handover_prediction_horizon", 60.0
        )  # 換手預測時間範圍（秒）
        self.signal_degradation_threshold = config.get(
            "signal_degradation_threshold", -85.0
        )  # 信號劣化閾值

        # 🚀 新增：候選衛星評分權重
        self.scoring_weights = config.get(
            "scoring_weights",
            {
                "signal_quality": 0.4,
                "load_factor": 0.25,
                "elevation_angle": 0.2,
                "distance": 0.15,
            },
        )

        # 環境狀態
        self.current_satellites: List[SatelliteState] = []
        self.current_ue_position = {
            "lat": 24.786667,
            "lon": 120.996944,
            "alt": 100.0,
        }  # NYCU 位置
        self.current_serving_satellite_id: Optional[int] = None
        self.episode_steps = 0
        self.max_episode_steps = config.get("max_episode_steps", 500)

        # 🚀 新增：軌道事件追蹤
        self.orbit_events: List[OrbitEvent] = []
        self.last_orbit_update = datetime.now()
        self.satellite_history: Dict[int, List[Dict[str, Any]]] = {}

        # 🚀 新增：動態負載平衡
        self.load_balancer = DynamicLoadBalancer(
            capacity_threshold=config.get("capacity_threshold", 0.8),
            balance_weight=config.get("balance_weight", 0.3),
        )

        # 動作空間：選擇候選衛星的索引
        self.action_space = spaces.Discrete(self.max_satellites)

        # 狀態空間：每個衛星的特徵 [rsrp, rsrq, sinr, load_factor, elevation, distance]
        # 形狀：(max_satellites, 6)
        self.observation_space = spaces.Box(
            low=np.array([[-150, -20, -10, 0, 0, 0] * self.max_satellites]).flatten(),
            high=np.array([[-50, 20, 30, 1, 90, 2000] * self.max_satellites]).flatten(),
            dtype=np.float32,
        )

        # 統計資訊
        self.total_handovers = 0
        self.successful_handovers = 0
        self.total_reward = 0.0

        logger.info(f"LEOSatelliteEnvironment 初始化完成 - 場景: {self.scenario}")

    async def get_satellite_data(self) -> List[SatelliteState]:
        """
        從 SimWorld API 獲取衛星數據

        Returns:
            List[SatelliteState]: 可見衛星列表
        """
        try:
            async with aiohttp.ClientSession() as session:
                # 使用已穩定的 SimWorld satellite API
                url = f"{self.simworld_url}/api/v1/satellites/visible_satellites"
                params = {
                    "count": self.max_satellites,
                    "min_elevation_deg": self.min_elevation,
                    "observer_lat": self.current_ue_position["lat"],
                    "observer_lon": self.current_ue_position["lon"],
                    "observer_alt": self.current_ue_position["alt"],
                }

                timeout = aiohttp.ClientTimeout(total=5.0)
                async with session.get(url, params=params, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        satellites = []

                        for sat_data in data.get("satellites", []):
                            # 計算信號品質指標
                            position = sat_data["position"]
                            signal_quality = sat_data.get("signal_quality", {})

                            # 🚀 新增：使用增強的信號品質預測
                            enhanced_signal_quality = (
                                await self._predict_signal_quality(position)
                            )

                            # 🚀 新增：動態負載計算
                            dynamic_load = await self._calculate_dynamic_load(
                                sat_data["id"]
                            )

                            satellite = SatelliteState(
                                id=sat_data["id"],
                                name=sat_data["name"],
                                position=position,
                                signal_quality=enhanced_signal_quality,
                                load_factor=dynamic_load,
                                timestamp=sat_data["timestamp"],
                            )
                            satellites.append(satellite)

                            # 更新衛星歷史記錄
                            self._update_satellite_history(satellite)

                        # 🚀 新增：檢測軌道事件
                        await self._detect_orbit_events(satellites)

                        logger.info(f"成功獲取 {len(satellites)} 顆衛星數據")
                        return satellites

                    else:
                        logger.warning(f"SimWorld API 響應錯誤: {response.status}")
                        raise aiohttp.ClientError(f"HTTP {response.status}")

        except Exception as e:
            logger.warning(f"SimWorld API 不可用 ({e})，使用 fallback 數據")
            if self.fallback_enabled:
                return self._get_fallback_satellite_data()
            raise

    def _get_fallback_satellite_data(self) -> List[SatelliteState]:
        """
        ✅ 新增：穩定的 fallback 衛星數據
        當 SimWorld API 不可用時確保訓練連續性
        """
        fallback_satellites = []
        base_ids = [44713, 44714, 44715, 44716, 44717, 44718]

        for i, sat_id in enumerate(base_ids[: self.max_satellites]):
            # 生成合理的軌道位置
            lat = -30 + i * 10  # 分散緯度
            lon = -120 + i * 40  # 分散經度
            elevation = 15 + i * 5  # 正仰角
            distance = 800 + i * 100  # 距離變化

            satellite = SatelliteState(
                id=sat_id,
                name=f"STARLINK-{1007 + i}",
                position={
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": 550 + i * 10,
                    "elevation": elevation,
                    "azimuth": i * 60,
                    "range": distance,
                },
                signal_quality={
                    "rsrp": -85 + i * 2,  # 信號強度變化
                    "rsrq": -10 + i * 1,  # 信號品質
                    "sinr": 5 + i * 2,  # 信噪比
                },
                load_factor=0.2 + i * 0.1,  # 負載因子
                timestamp=datetime.now().isoformat(),
            )
            fallback_satellites.append(satellite)

        logger.info(f"使用 fallback 數據：{len(fallback_satellites)} 顆衛星")
        return fallback_satellites

    def _calculate_rsrq(self, position: Dict[str, float]) -> float:
        """計算 RSRQ (參考信號接收品質)"""
        elevation = position.get("elevation", 0)
        distance = position.get("range", 1000)

        # 基於仰角的品質計算
        base_rsrq = -10  # dB
        elevation_bonus = elevation * 0.1
        distance_penalty = distance / 1000.0  # 每1000km降低1dB

        return base_rsrq + elevation_bonus - distance_penalty

    def _calculate_sinr(self, position: Dict[str, float]) -> float:
        """計算 SINR (信號干擾雜訊比)"""
        elevation = position.get("elevation", 0)

        # 基於仰角的簡化 SINR 模型
        base_sinr = 5  # dB
        elevation_bonus = elevation * 0.3
        noise = np.random.normal(0, 1)  # 隨機雜訊

        return base_sinr + elevation_bonus + noise

    def _calculate_handover_metrics(self, satellite: SatelliteState) -> HandoverMetrics:
        """
        計算換手指標
        整合信號傳播模型 (距離、多普勒、陰影衰落)
        """
        position = satellite.position
        signal_quality = satellite.signal_quality

        # 計算換手機率 (基於多個因子)
        elevation_factor = min(position.get("elevation", 0) / 90.0, 1.0)
        signal_factor = (signal_quality["rsrp"] + 150) / 100.0  # 正規化到 0-1
        load_factor = 1.0 - satellite.load_factor  # 負載越低越好

        handover_probability = (
            elevation_factor * 0.4 + signal_factor * 0.4 + load_factor * 0.2
        )
        handover_probability = np.clip(handover_probability, 0.0, 1.0)

        return HandoverMetrics(
            rsrp=signal_quality["rsrp"],
            rsrq=signal_quality["rsrq"],
            sinr=signal_quality["sinr"],
            load_factor=satellite.load_factor,
            handover_probability=handover_probability,
        )

    def _get_observation(self) -> np.ndarray:
        """
        獲取當前環境觀測值

        Returns:
            np.ndarray: 狀態向量 [sat1_features, sat2_features, ...]
        """
        observation = np.zeros((self.max_satellites, 6), dtype=np.float32)

        for i, satellite in enumerate(self.current_satellites[: self.max_satellites]):
            metrics = self._calculate_handover_metrics(satellite)

            observation[i] = [
                metrics.rsrp,
                metrics.rsrq,
                metrics.sinr,
                metrics.load_factor,
                satellite.position.get("elevation", 0),
                satellite.position.get("range", 1000),
            ]

        return observation.flatten()

    def _calculate_reward(
        self, action: int, prev_serving_satellite_id: Optional[int]
    ) -> float:
        """
        計算獎勵函數

        Args:
            action: 選擇的衛星索引
            prev_serving_satellite_id: 前一個服務衛星ID

        Returns:
            float: 獎勵值
        """
        if action >= len(self.current_satellites):
            return -10.0  # 無效動作懲罰

        selected_satellite = self.current_satellites[action]
        metrics = self._calculate_handover_metrics(selected_satellite)

        # 基礎獎勵：基於信號品質和負載
        signal_reward = (metrics.rsrp + 150) / 100.0  # 正規化 RSRP
        load_reward = 1.0 - metrics.load_factor  # 負載越低越好
        elevation_reward = selected_satellite.position.get("elevation", 0) / 90.0

        base_reward = signal_reward * 0.4 + load_reward * 0.3 + elevation_reward * 0.3

        # 換手懲罰：避免不必要的換手
        handover_penalty = 0.0
        if (
            prev_serving_satellite_id is not None
            and selected_satellite.id != prev_serving_satellite_id
        ):
            handover_penalty = -0.2
            self.total_handovers += 1

        # 穩定性獎勵：選擇高品質衛星
        stability_bonus = 0.0
        if metrics.handover_probability > 0.7:
            stability_bonus = 0.1
            if handover_penalty < 0:  # 如果是換手且品質好
                self.successful_handovers += 1

        total_reward = base_reward + handover_penalty + stability_bonus

        return np.clip(total_reward, -1.0, 1.0)

    async def reset(
        self, seed: Optional[int] = None, options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """
        重置環境

        Returns:
            Tuple: (observation, info)
        """
        super().reset(seed=seed)

        try:
            # 獲取初始衛星數據
            self.current_satellites = await self.get_satellite_data()

            # 選擇初始服務衛星（信號最強的）
            if self.current_satellites:
                best_satellite = max(
                    self.current_satellites,
                    key=lambda s: self._calculate_handover_metrics(
                        s
                    ).handover_probability,
                )
                self.current_serving_satellite_id = best_satellite.id
            else:
                self.current_serving_satellite_id = None

            # 重置統計
            self.episode_steps = 0
            self.total_handovers = 0
            self.successful_handovers = 0
            self.total_reward = 0.0

            observation = self._get_observation()
            info = {
                "serving_satellite_id": self.current_serving_satellite_id,
                "available_satellites": len(self.current_satellites),
                "episode_steps": self.episode_steps,
            }

            logger.info(f"環境重置完成 - 服務衛星: {self.current_serving_satellite_id}")
            return observation, info

        except Exception as e:
            logger.error(f"環境重置失敗: {e}")
            # 返回零觀測值以避免崩潰
            obs_shape = self.observation_space.shape
            if obs_shape is not None:
                return np.zeros(obs_shape, dtype=np.float32), {"error": str(e)}
            else:
                return np.zeros((self.max_satellites * 6,), dtype=np.float32), {
                    "error": str(e)
                }

    async def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        執行一步動作

        Args:
            action: 選擇的衛星索引

        Returns:
            Tuple: (observation, reward, terminated, truncated, info)
        """
        prev_serving_satellite_id = self.current_serving_satellite_id

        try:
            # 更新衛星數據（模擬時間推進）
            self.current_satellites = await self.get_satellite_data()

            # 計算獎勵
            reward = self._calculate_reward(action, prev_serving_satellite_id)
            self.total_reward += reward

            # 更新服務衛星
            if action < len(self.current_satellites):
                self.current_serving_satellite_id = self.current_satellites[action].id

            # 檢查終止條件
            self.episode_steps += 1
            terminated = self.episode_steps >= self.max_episode_steps
            truncated = False

            # 獲取新觀測值
            observation = self._get_observation()

            # 構建資訊
            info = {
                "serving_satellite_id": self.current_serving_satellite_id,
                "selected_action": action,
                "reward": reward,
                "total_reward": self.total_reward,
                "total_handovers": self.total_handovers,
                "successful_handovers": self.successful_handovers,
                "handover_success_rate": (
                    self.successful_handovers / max(self.total_handovers, 1)
                ),
                "episode_steps": self.episode_steps,
                "available_satellites": len(self.current_satellites),
            }

            return observation, reward, terminated, truncated, info

        except Exception as e:
            logger.error(f"環境步驟執行失敗: {e}")
            # 返回安全的默認值
            obs_shape = self.observation_space.shape
            if obs_shape is not None:
                observation = np.zeros(obs_shape, dtype=np.float32)
            else:
                observation = np.zeros((self.max_satellites * 6,), dtype=np.float32)
            return observation, -1.0, True, False, {"error": str(e)}

    def render(self, mode: str = "human") -> Optional[np.ndarray]:
        """
        渲染環境（可選實現）
        """
        if mode == "human":
            print(f"Episode Step: {self.episode_steps}")
            print(f"Serving Satellite: {self.current_serving_satellite_id}")
            print(f"Available Satellites: {len(self.current_satellites)}")
            print(f"Total Reward: {self.total_reward:.2f}")
            print(
                f"Handover Success Rate: {self.successful_handovers}/{self.total_handovers}"
            )
            print("-" * 50)

        return None

    def close(self):
        """關閉環境"""
        logger.info("LEOSatelliteEnvironment 已關閉")

    def get_stats(self) -> Dict[str, Any]:
        """
        獲取環境統計資訊
        """
        return {
            "environment_type": "LEOSatelliteEnvironment",
            "scenario": self.scenario,
            "max_satellites": self.max_satellites,
            "current_satellites": len(self.current_satellites),
            "serving_satellite_id": self.current_serving_satellite_id,
            "episode_steps": self.episode_steps,
            "total_handovers": self.total_handovers,
            "successful_handovers": self.successful_handovers,
            "total_reward": self.total_reward,
            "fallback_enabled": self.fallback_enabled,
            "simworld_url": self.simworld_url,
        }

    # 🚀 新增：增強的信號品質預測模型
    async def _predict_signal_quality(
        self, position: Dict[str, float]
    ) -> Dict[str, float]:
        """
        預測信號品質指標 (RSRP/RSRQ/SINR)

        基於：
        - 自由空間路徑損耗
        - 大氣衰減
        - 陰影衰落
        - 都市環境衰減
        """
        elevation = position.get("elevation", 0)
        distance = position.get("range", 1000)  # km

        # 基礎信號功率 (衛星EIRP)
        base_power = 55.0  # dBW

        # 自由空間路徑損耗
        frequency_hz = 20e9  # 20 GHz
        path_loss = (
            20 * np.log10(distance * 1000)
            + 20 * np.log10(frequency_hz)
            + 20 * np.log10(4 * np.pi / 3e8)
        )

        # 大氣衰減 (基於仰角)
        elevation_rad = np.radians(elevation)
        atmospheric_loss = 0.5 / np.sin(elevation_rad) if elevation > 5 else 10.0

        # 陰影衰落 (對數正態分布)
        shadow_fading = np.random.lognormal(0, 0.5)

        # 都市環境衰減 (基於場景)
        urban_loss = {"urban": 5.0, "suburban": 2.0, "rural": 0.5}.get(
            self.scenario, 2.0
        )

        # 計算 RSRP
        rsrp = base_power - path_loss - atmospheric_loss - shadow_fading - urban_loss

        # 計算 RSRQ (基於干擾加雜訊比)
        interference_level = np.random.uniform(0.1, 0.3)  # 模擬干擾
        rsrq = rsrp - 10 * np.log10(1 + interference_level)

        # 計算 SINR (基於雜訊功率)
        noise_power = -174 + 10 * np.log10(20e6)  # 20 MHz 頻寬的雜訊功率
        sinr = rsrp - noise_power - 10 * np.log10(1 + interference_level)

        return {"rsrp": float(rsrp), "rsrq": float(rsrq), "sinr": float(sinr)}

    # 🚀 新增：動態負載計算
    async def _calculate_dynamic_load(self, satellite_id: int) -> float:
        """
        計算衛星的動態負載因子

        考慮：
        - 當前連接用戶數
        - 處理能力
        - 網路流量
        - 歷史負載趨勢
        """
        # 基礎負載 (模擬)
        base_load = 0.3 + (hash(str(satellite_id)) % 50) / 100.0

        # 時間變化負載 (模擬用戶活動週期)
        time_factor = np.sin(datetime.now().hour * np.pi / 12) * 0.2

        # 隨機負載變化
        random_factor = np.random.uniform(-0.1, 0.1)

        # 歷史負載趨勢
        history_factor = 0.0
        if satellite_id in self.satellite_history:
            recent_loads = [
                h.get("load_factor", 0.3)
                for h in self.satellite_history[satellite_id][-5:]
            ]
            if recent_loads:
                history_factor = (np.mean(recent_loads) - 0.3) * 0.1

        dynamic_load = base_load + time_factor + random_factor + history_factor
        return np.clip(dynamic_load, 0.0, 1.0)

    # 🚀 新增：衛星歷史記錄更新
    def _update_satellite_history(self, satellite: SatelliteState):
        """更新衛星歷史記錄"""
        if satellite.id not in self.satellite_history:
            self.satellite_history[satellite.id] = []

        history_entry = {
            "timestamp": datetime.now(),
            "position": satellite.position.copy(),
            "signal_quality": satellite.signal_quality.copy(),
            "load_factor": satellite.load_factor,
        }

        self.satellite_history[satellite.id].append(history_entry)

        # 保持歷史記錄在合理範圍內
        if len(self.satellite_history[satellite.id]) > 100:
            self.satellite_history[satellite.id] = self.satellite_history[satellite.id][
                -50:
            ]

    # 🚀 新增：軌道事件檢測
    async def _detect_orbit_events(self, satellites: List[SatelliteState]):
        """
        檢測軌道事件

        事件類型：
        - elevation_change: 仰角顯著變化
        - handover_opportunity: 換手機會
        - signal_degradation: 信號劣化
        """
        current_time = datetime.now()

        for satellite in satellites:
            # 檢查仰角變化事件
            if satellite.id in self.satellite_history:
                recent_history = self.satellite_history[satellite.id][-10:]
                if len(recent_history) >= 2:
                    prev_elevation = recent_history[-2]["position"].get("elevation", 0)
                    curr_elevation = satellite.position.get("elevation", 0)
                    elevation_change = curr_elevation - prev_elevation

                    if abs(elevation_change) > 5.0:  # 5度變化閾值
                        event = OrbitEvent(
                            event_type="elevation_change",
                            timestamp=current_time,
                            satellite_id=satellite.id,
                            trigger_value=elevation_change,
                            prediction_confidence=0.9,
                            event_data={
                                "prev_elevation": prev_elevation,
                                "curr_elevation": curr_elevation,
                                "change_rate": elevation_change,
                            },
                        )
                        self.orbit_events.append(event)

            # 檢查信號劣化事件
            rsrp = satellite.signal_quality.get("rsrp", -100)
            if rsrp < self.signal_degradation_threshold:
                event = OrbitEvent(
                    event_type="signal_degradation",
                    timestamp=current_time,
                    satellite_id=satellite.id,
                    trigger_value=rsrp,
                    prediction_confidence=0.8,
                    event_data={
                        "rsrp": rsrp,
                        "threshold": self.signal_degradation_threshold,
                        "signal_quality": satellite.signal_quality.copy(),
                    },
                )
                self.orbit_events.append(event)

            # 檢查換手機會事件
            metrics = self._calculate_handover_metrics(satellite)
            if metrics.handover_probability > 0.8:
                event = OrbitEvent(
                    event_type="handover_opportunity",
                    timestamp=current_time,
                    satellite_id=satellite.id,
                    trigger_value=metrics.handover_probability,
                    prediction_confidence=0.85,
                    event_data={
                        "handover_probability": metrics.handover_probability,
                        "metrics": metrics,
                    },
                )
                self.orbit_events.append(event)

        # 清理舊事件
        self.orbit_events = [
            e
            for e in self.orbit_events
            if (current_time - e.timestamp).total_seconds() < 300
        ]  # 保持5分鐘

    # 🚀 新增：統一候選衛星評分系統
    def evaluate_candidate_satellites(
        self, satellites: List[SatelliteState]
    ) -> List[CandidateScore]:
        """
        統一候選衛星評分系統

        Args:
            satellites: 候選衛星列表

        Returns:
            List[CandidateScore]: 評分結果列表
        """
        scored_candidates = []

        for satellite in satellites:
            # 信號品質評分
            signal_score = self._calculate_signal_score(satellite)

            # 負載評分
            load_score = self._calculate_load_score(satellite)

            # 仰角評分
            elevation_score = self._calculate_elevation_score(satellite)

            # 距離評分
            distance_score = self._calculate_distance_score(satellite)

            # 綜合評分
            overall_score = (
                signal_score * self.scoring_weights["signal_quality"]
                + load_score * self.scoring_weights["load_factor"]
                + elevation_score * self.scoring_weights["elevation_angle"]
                + distance_score * self.scoring_weights["distance"]
            )

            score_breakdown = {
                "signal_quality": signal_score,
                "load_factor": load_score,
                "elevation_angle": elevation_score,
                "distance": distance_score,
            }

            candidate_score = CandidateScore(
                satellite_id=satellite.id,
                signal_score=signal_score,
                load_score=load_score,
                elevation_score=elevation_score,
                distance_score=distance_score,
                overall_score=overall_score,
                score_breakdown=score_breakdown,
            )

            scored_candidates.append(candidate_score)

        # 按綜合評分排序
        scored_candidates.sort(key=lambda x: x.overall_score, reverse=True)

        return scored_candidates

    def _calculate_signal_score(self, satellite: SatelliteState) -> float:
        """計算信號品質評分 (0-100)"""
        rsrp = satellite.signal_quality.get("rsrp", -100)
        rsrq = satellite.signal_quality.get("rsrq", -15)
        sinr = satellite.signal_quality.get("sinr", 0)

        # RSRP 評分 (40分)
        rsrp_score = np.clip((rsrp + 120) / 40 * 40, 0, 40)

        # RSRQ 評分 (30分)
        rsrq_score = np.clip((rsrq + 20) / 20 * 30, 0, 30)

        # SINR 評分 (30分)
        sinr_score = np.clip(sinr / 20 * 30, 0, 30)

        return rsrp_score + rsrq_score + sinr_score

    def _calculate_load_score(self, satellite: SatelliteState) -> float:
        """計算負載評分 (0-100)"""
        load_factor = satellite.load_factor

        # 負載越低分數越高
        load_score = (1.0 - load_factor) * 100

        # 加入負載穩定性考慮
        if satellite.id in self.satellite_history:
            recent_loads = [
                h.get("load_factor", 0.5)
                for h in self.satellite_history[satellite.id][-5:]
            ]
            if recent_loads:
                load_variance = np.var(recent_loads)
                stability_bonus = max(
                    0.0, 10.0 - float(load_variance) * 100
                )  # 最多10分穩定性加分
                load_score += stability_bonus

        return np.clip(load_score, 0, 100)

    def _calculate_elevation_score(self, satellite: SatelliteState) -> float:
        """計算仰角評分 (0-100)"""
        elevation = satellite.position.get("elevation", 0)

        # 仰角越高分數越高
        elevation_score = (elevation / 90.0) * 100

        # 低仰角懲罰
        if elevation < 15:
            elevation_score *= 0.5

        return np.clip(elevation_score, 0, 100)

    def _calculate_distance_score(self, satellite: SatelliteState) -> float:
        """計算距離評分 (0-100)"""
        distance = satellite.position.get("range", 1000)

        # 距離越近分數越高
        distance_score = max(0, (2000 - distance) / 2000 * 100)

        return np.clip(distance_score, 0, 100)


class DynamicLoadBalancer:
    """動態負載平衡器"""

    def __init__(self, capacity_threshold: float = 0.8, balance_weight: float = 0.3):
        self.capacity_threshold = capacity_threshold
        self.balance_weight = balance_weight
        self.load_history: Dict[int, List[float]] = {}

    def balance_load(self, satellites: List[SatelliteState]) -> List[SatelliteState]:
        """
        執行動態負載平衡

        Args:
            satellites: 衛星列表

        Returns:
            List[SatelliteState]: 負載平衡後的衛星列表
        """
        # 計算平均負載
        if not satellites:
            return satellites

        total_load = sum(sat.load_factor for sat in satellites)
        avg_load = total_load / len(satellites)

        # 調整負載
        balanced_satellites = []
        for satellite in satellites:
            # 如果負載過高，降低優先級
            if satellite.load_factor > self.capacity_threshold:
                # 通過調整評分來降低選中機率
                adjusted_load = satellite.load_factor * 1.2
            elif satellite.load_factor < avg_load * 0.5:
                # 如果負載過低，稍微提高優先級
                adjusted_load = satellite.load_factor * 0.8
            else:
                adjusted_load = satellite.load_factor

            # 更新負載歷史
            if satellite.id not in self.load_history:
                self.load_history[satellite.id] = []
            self.load_history[satellite.id].append(satellite.load_factor)

            # 保持歷史記錄在合理範圍內
            if len(self.load_history[satellite.id]) > 50:
                self.load_history[satellite.id] = self.load_history[satellite.id][-25:]

            # 創建調整後的衛星狀態
            adjusted_satellite = SatelliteState(
                id=satellite.id,
                name=satellite.name,
                position=satellite.position,
                signal_quality=satellite.signal_quality,
                load_factor=np.clip(adjusted_load, 0.0, 1.0),
                timestamp=satellite.timestamp,
            )

            balanced_satellites.append(adjusted_satellite)

        return balanced_satellites

    def predict_load_trend(self, satellite_id: int) -> float:
        """
        預測負載趨勢

        Args:
            satellite_id: 衛星ID

        Returns:
            float: 負載趨勢預測值 (-1: 下降, 0: 穩定, 1: 上升)
        """
        if satellite_id not in self.load_history:
            return 0.0

        history = self.load_history[satellite_id]
        if len(history) < 3:
            return 0.0

        # 簡單的趨勢分析
        recent_loads = history[-5:]
        if len(recent_loads) >= 3:
            trend = np.polyfit(range(len(recent_loads)), recent_loads, 1)[0]
            return np.clip(trend * 10, -1.0, 1.0)  # 放大並限制範圍

        return 0.0
