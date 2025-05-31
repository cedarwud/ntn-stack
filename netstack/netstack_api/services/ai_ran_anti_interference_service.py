"""
AI-RAN 抗干擾機制服務

實現 TODO.md 第7項：干擾模型與抗干擾機制
支持 AI-RAN 動態頻率選擇，包含完整的 AI 模型訓練和推理功能
"""

import asyncio
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import structlog
import aiohttp
from sklearn.preprocessing import StandardScaler
from collections import deque
import pickle

from ..adapters.redis_adapter import RedisAdapter
from ..models.sionna_models import InterferenceSource, InterferenceSimulationRequest

logger = structlog.get_logger(__name__)


class AIRANNetwork(nn.Module):
    """AI-RAN 深度強化學習網絡"""

    def __init__(
        self, input_size: int = 20, hidden_size: int = 128, output_size: int = 10
    ):
        super(AIRANNetwork, self).__init__()

        # 狀態編碼器
        self.state_encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
        )

        # 動作價值網絡 (DQN)
        self.q_network = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, output_size),
        )

        # 策略網絡 (Actor-Critic)
        self.policy_network = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, output_size),
            nn.Softmax(dim=-1),
        )

        # 價值網絡 (Critic)
        self.value_network = nn.Sequential(
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Linear(hidden_size // 4, 1),
        )

    def forward(self, state):
        """前向傳播"""
        encoded_state = self.state_encoder(state)
        q_values = self.q_network(encoded_state)
        policy = self.policy_network(encoded_state)
        value = self.value_network(encoded_state)

        return q_values, policy, value


class ExperienceReplay:
    """經驗回放緩衝區"""

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """添加經驗"""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> Tuple:
        """抽樣批次經驗"""
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[i] for i in indices]

        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.BoolTensor([e[4] for e in batch])

        return states, actions, rewards, next_states, dones

    def __len__(self):
        return len(self.buffer)


class AIRANAntiInterferenceService:
    """AI-RAN 抗干擾服務"""

    def __init__(
        self,
        redis_adapter: RedisAdapter,
        simworld_api_url: str = "http://simworld-backend:8000",
        model_save_path: str = "/tmp/ai_ran_models",
        learning_rate: float = 0.001,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        self.logger = logger.bind(service="ai_ran_anti_interference")
        self.redis_adapter = redis_adapter
        self.simworld_api_url = simworld_api_url
        self.model_save_path = Path(model_save_path)
        self.model_save_path.mkdir(parents=True, exist_ok=True)

        # AI 模型參數
        self.learning_rate = learning_rate
        self.epsilon = epsilon  # 探索率
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = 32
        self.target_update_freq = 100

        # 初始化 AI 網絡
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ai_network = AIRANNetwork().to(self.device)
        self.target_network = AIRANNetwork().to(self.device)
        self.target_network.load_state_dict(self.ai_network.state_dict())

        # 優化器
        self.optimizer = optim.Adam(self.ai_network.parameters(), lr=learning_rate)

        # 經驗回放
        self.experience_replay = ExperienceReplay()

        # 特徵標準化
        self.scaler = StandardScaler()

        # 頻率管理
        self.available_frequencies = list(range(2100, 2200, 5))  # MHz
        self.current_frequency = 2150  # MHz

        # 抗干擾策略
        self.interference_strategies = {
            "frequency_hopping": self._frequency_hopping_strategy,
            "power_control": self._power_control_strategy,
            "beam_forming": self._beam_forming_strategy,
            "spread_spectrum": self._spread_spectrum_strategy,
            "adaptive_coding": self._adaptive_coding_strategy,
        }

        # 訓練統計
        self.training_stats = {
            "episodes": 0,
            "total_reward": 0,
            "average_sinr": 0,
            "success_rate": 0,
            "model_updates": 0,
        }

        # 載入預訓練模型（如果存在）
        self._load_model_if_exists()

    async def detect_interference(
        self,
        ue_positions: List[Dict],
        gnb_positions: List[Dict],
        current_sinr: List[float],
    ) -> Dict:
        """干擾檢測"""
        try:
            # 準備檢測請求
            detection_request = {
                "ue_positions": ue_positions,
                "gnb_positions": gnb_positions,
                "current_sinr_db": current_sinr,
                "frequency_mhz": self.current_frequency,
                "detection_threshold_db": -10.0,  # SINR 閾值
            }

            # 調用 SimWorld 干擾檢測 API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.simworld_api_url}/api/v1/interference/detect",
                    json=detection_request,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        interference_detected = data.get("interference_detected", False)
                        interference_sources = data.get("interference_sources", [])

                        # 分析干擾類型和強度
                        interference_analysis = self._analyze_interference(
                            interference_sources, current_sinr
                        )

                        return {
                            "success": True,
                            "interference_detected": interference_detected,
                            "interference_sources": interference_sources,
                            "interference_analysis": interference_analysis,
                            "detection_time": datetime.utcnow().isoformat(),
                        }
                    else:
                        self.logger.warning(
                            "干擾檢測 API 請求失敗", status=response.status
                        )
                        return {
                            "success": False,
                            "error": f"API 請求失敗: {response.status}",
                        }

        except Exception as e:
            self.logger.error("干擾檢測失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def ai_mitigation_decision(
        self, interference_data: Dict, network_state: Dict
    ) -> Dict:
        """AI 抗干擾決策"""
        try:
            # 準備狀態特徵
            state_features = self._extract_state_features(
                interference_data, network_state
            )
            state_tensor = (
                torch.FloatTensor(state_features).unsqueeze(0).to(self.device)
            )

            # AI 網絡推理
            with torch.no_grad():
                q_values, policy, value = self.ai_network(state_tensor)

                # ε-貪婪策略選擇動作
                if np.random.random() < self.epsilon:
                    # 探索：隨機選擇動作
                    action = np.random.randint(0, len(self.interference_strategies))
                else:
                    # 利用：選擇最佳動作
                    action = torch.argmax(q_values).item()

            # 獲取策略名稱
            strategy_names = list(self.interference_strategies.keys())
            selected_strategy = strategy_names[action % len(strategy_names)]

            # 執行選定的抗干擾策略
            mitigation_result = await self.interference_strategies[selected_strategy](
                interference_data, network_state
            )

            # 記錄決策用於訓練
            decision_record = {
                "state_features": state_features,
                "action": action,
                "strategy": selected_strategy,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": float(torch.max(policy).item()),
                "expected_value": float(value.item()),
            }

            await self.redis_adapter.set(
                f"ai_ran_decision:{datetime.utcnow().timestamp()}",
                json.dumps(decision_record),
                expire=3600,
            )

            return {
                "success": True,
                "selected_strategy": selected_strategy,
                "action_confidence": float(torch.max(policy).item()),
                "expected_value": float(value.item()),
                "mitigation_result": mitigation_result,
                "decision_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error("AI 抗干擾決策失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def execute_mitigation(
        self, strategy: str, mitigation_params: Dict, target_ueransim_configs: List[str]
    ) -> Dict:
        """執行抗干擾措施"""
        try:
            execution_results = []

            for config_file in target_ueransim_configs:
                result = await self._apply_mitigation_to_config(
                    config_file, strategy, mitigation_params
                )
                execution_results.append(result)

            # 更新當前網絡狀態
            if strategy == "frequency_hopping":
                self.current_frequency = mitigation_params.get(
                    "new_frequency", self.current_frequency
                )

            return {
                "success": True,
                "strategy": strategy,
                "execution_results": execution_results,
                "updated_configs": len(execution_results),
                "execution_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error("執行抗干擾措施失敗", error=str(e))
            return {"success": False, "error": str(e)}

    async def train_ai_model(
        self, training_episodes: int = 1000, save_interval: int = 100
    ) -> Dict:
        """訓練 AI 模型"""
        try:
            self.logger.info("開始 AI 模型訓練", episodes=training_episodes)

            training_rewards = []

            for episode in range(training_episodes):
                # 模擬干擾環境
                simulated_state = self._generate_simulation_environment()

                episode_reward = 0
                episode_steps = 0
                max_steps = 50

                while episode_steps < max_steps:
                    # 獲取當前狀態特徵
                    state_features = self._extract_state_features(
                        simulated_state["interference_data"],
                        simulated_state["network_state"],
                    )
                    state_tensor = (
                        torch.FloatTensor(state_features).unsqueeze(0).to(self.device)
                    )

                    # 選擇動作
                    q_values, policy, value = self.ai_network(state_tensor)

                    if np.random.random() < self.epsilon:
                        action = np.random.randint(0, len(self.interference_strategies))
                    else:
                        action = torch.argmax(q_values).item()

                    # 執行動作並獲取獎勵
                    next_state, reward, done = self._simulate_action_outcome(
                        simulated_state, action
                    )

                    # 存儲經驗
                    next_state_features = self._extract_state_features(
                        next_state["interference_data"], next_state["network_state"]
                    )

                    self.experience_replay.push(
                        state_features, action, reward, next_state_features, done
                    )

                    episode_reward += reward
                    episode_steps += 1
                    simulated_state = next_state

                    # 經驗回放學習
                    if len(self.experience_replay) > self.batch_size:
                        await self._replay_learning()

                    if done:
                        break

                training_rewards.append(episode_reward)

                # 更新探索率
                if self.epsilon > self.epsilon_min:
                    self.epsilon *= self.epsilon_decay

                # 更新目標網絡
                if episode % self.target_update_freq == 0:
                    self.target_network.load_state_dict(self.ai_network.state_dict())

                # 保存模型
                if episode % save_interval == 0:
                    await self._save_model(episode)

                # 記錄訓練統計
                if episode % 100 == 0:
                    avg_reward = np.mean(training_rewards[-100:])
                    self.logger.info(
                        "訓練進度",
                        episode=episode,
                        avg_reward=avg_reward,
                        epsilon=self.epsilon,
                    )

            # 更新訓練統計
            self.training_stats.update(
                {
                    "episodes": self.training_stats["episodes"] + training_episodes,
                    "total_reward": sum(training_rewards),
                    "average_reward": np.mean(training_rewards),
                    "final_epsilon": self.epsilon,
                }
            )

            # 保存最終模型
            await self._save_model("final")

            return {
                "success": True,
                "training_episodes": training_episodes,
                "average_reward": np.mean(training_rewards),
                "final_epsilon": self.epsilon,
                "training_stats": self.training_stats,
            }

        except Exception as e:
            self.logger.error("AI 模型訓練失敗", error=str(e))
            return {"success": False, "error": str(e)}

    # 抗干擾策略實現
    async def _frequency_hopping_strategy(
        self, interference_data: Dict, network_state: Dict
    ) -> Dict:
        """頻率跳變策略"""
        try:
            # 分析干擾頻譜
            interfered_frequencies = self._get_interfered_frequencies(interference_data)

            # 選擇最佳頻率
            available_freqs = [
                f for f in self.available_frequencies if f not in interfered_frequencies
            ]

            if available_freqs:
                new_frequency = np.random.choice(available_freqs)

                return {
                    "strategy": "frequency_hopping",
                    "new_frequency": new_frequency,
                    "hop_pattern": self._generate_hop_pattern(available_freqs),
                    "estimated_sinr_improvement": 5.0,  # dB
                    "implementation_delay_ms": 50,
                }
            else:
                # 所有頻率都受干擾，選擇干擾最小的
                freq_interference = {
                    f: self._calculate_frequency_interference(f, interference_data)
                    for f in self.available_frequencies
                }
                best_freq = min(freq_interference, key=freq_interference.get)

                return {
                    "strategy": "frequency_hopping",
                    "new_frequency": best_freq,
                    "hop_pattern": [best_freq],
                    "estimated_sinr_improvement": 2.0,  # dB
                    "implementation_delay_ms": 50,
                }

        except Exception as e:
            self.logger.error("頻率跳變策略失敗", error=str(e))
            return {"error": str(e)}

    async def _power_control_strategy(
        self, interference_data: Dict, network_state: Dict
    ) -> Dict:
        """功率控制策略"""
        try:
            current_power = network_state.get("tx_power_dbm", 23)
            interference_level = interference_data.get("interference_analysis", {}).get(
                "average_level_db", 0
            )

            # 動態調整發射功率
            if interference_level > -80:  # 強干擾
                new_power = min(30, current_power + 3)  # 增加功率
            elif interference_level < -100:  # 弱干擾
                new_power = max(10, current_power - 2)  # 降低功率節能
            else:
                new_power = current_power  # 維持不變

            return {
                "strategy": "power_control",
                "new_tx_power_dbm": new_power,
                "power_adjustment_db": new_power - current_power,
                "estimated_sinr_improvement": abs(new_power - current_power) * 0.8,
                "implementation_delay_ms": 10,
            }

        except Exception as e:
            self.logger.error("功率控制策略失敗", error=str(e))
            return {"error": str(e)}

    async def _beam_forming_strategy(
        self, interference_data: Dict, network_state: Dict
    ) -> Dict:
        """波束賦形策略"""
        try:
            interference_sources = interference_data.get("interference_sources", [])

            # 計算最佳波束方向（避開干擾源）
            optimal_azimuth, optimal_elevation = self._calculate_optimal_beam_direction(
                interference_sources, network_state
            )

            return {
                "strategy": "beam_forming",
                "optimal_azimuth_deg": optimal_azimuth,
                "optimal_elevation_deg": optimal_elevation,
                "beam_width_deg": 30,
                "estimated_sinr_improvement": 8.0,  # dB
                "implementation_delay_ms": 100,
            }

        except Exception as e:
            self.logger.error("波束賦形策略失敗", error=str(e))
            return {"error": str(e)}

    async def _spread_spectrum_strategy(
        self, interference_data: Dict, network_state: Dict
    ) -> Dict:
        """展頻策略"""
        try:
            current_bandwidth = network_state.get("bandwidth_mhz", 20)
            interference_bandwidth = interference_data.get(
                "interference_analysis", {}
            ).get("bandwidth_mhz", 20)

            # 調整展頻參數
            if interference_bandwidth < current_bandwidth:
                # 增加展頻因子
                spreading_factor = min(8, current_bandwidth // interference_bandwidth)
            else:
                spreading_factor = 2  # 最小展頻因子

            return {
                "strategy": "spread_spectrum",
                "spreading_factor": spreading_factor,
                "chip_rate_mcps": current_bandwidth * spreading_factor,
                "estimated_sinr_improvement": 3.0 * np.log2(spreading_factor),
                "implementation_delay_ms": 200,
            }

        except Exception as e:
            self.logger.error("展頻策略失敗", error=str(e))
            return {"error": str(e)}

    async def _adaptive_coding_strategy(
        self, interference_data: Dict, network_state: Dict
    ) -> Dict:
        """自適應編碼策略"""
        try:
            current_sinr = network_state.get("sinr_db", 15)
            interference_impact = interference_data.get(
                "interference_analysis", {}
            ).get("sinr_degradation_db", 0)

            # 根據干擾選擇編碼方案
            if current_sinr - interference_impact > 20:
                coding_scheme = "LDPC_8/9"  # 高效率編碼
                estimated_improvement = 1.0
            elif current_sinr - interference_impact > 10:
                coding_scheme = "LDPC_2/3"  # 平衡編碼
                estimated_improvement = 3.0
            else:
                coding_scheme = "LDPC_1/3"  # 強糾錯編碼
                estimated_improvement = 6.0

            return {
                "strategy": "adaptive_coding",
                "coding_scheme": coding_scheme,
                "error_correction_capability": estimated_improvement,
                "estimated_sinr_improvement": estimated_improvement,
                "implementation_delay_ms": 20,
            }

        except Exception as e:
            self.logger.error("自適應編碼策略失敗", error=str(e))
            return {"error": str(e)}

    # 輔助方法
    def _extract_state_features(
        self, interference_data: Dict, network_state: Dict
    ) -> List[float]:
        """提取狀態特徵"""
        features = [
            network_state.get("sinr_db", 0),
            network_state.get("rsrp_dbm", -100),
            network_state.get("tx_power_dbm", 23),
            network_state.get("frequency_mhz", 2150),
            network_state.get("bandwidth_mhz", 20),
            len(interference_data.get("interference_sources", [])),
            interference_data.get("interference_analysis", {}).get(
                "average_level_db", -120
            ),
            interference_data.get("interference_analysis", {}).get("bandwidth_mhz", 0),
            interference_data.get("interference_analysis", {}).get(
                "sinr_degradation_db", 0
            ),
            network_state.get("ue_count", 1),
            network_state.get("throughput_mbps", 0),
            network_state.get("latency_ms", 50),
            network_state.get("packet_loss_rate", 0),
            network_state.get("doppler_shift_hz", 0),
            network_state.get("distance_km", 1000),
            interference_data.get("interference_analysis", {}).get(
                "frequency_overlap", 0
            ),
            network_state.get("antenna_gain_db", 15),
            network_state.get("elevation_angle_deg", 45),
            network_state.get("weather_factor", 1.0),
            datetime.utcnow().hour / 24.0,  # 時間因子
        ]

        # 標準化特徵
        return self.scaler.fit_transform([features])[0].tolist()

    def _analyze_interference(
        self, interference_sources: List[Dict], current_sinr: List[float]
    ) -> Dict:
        """分析干擾特性"""
        if not interference_sources:
            return {
                "interference_level": "none",
                "average_level_db": -120,
                "sinr_degradation_db": 0,
                "bandwidth_mhz": 0,
                "frequency_overlap": 0,
            }

        total_interference_power = sum(
            10 ** (source["power_dbm"] / 10) for source in interference_sources
        )
        average_level_db = (
            10 * np.log10(total_interference_power)
            if total_interference_power > 0
            else -120
        )

        sinr_degradation = max(0, 15 - np.mean(current_sinr)) if current_sinr else 0

        return {
            "interference_level": (
                "high"
                if average_level_db > -80
                else "medium" if average_level_db > -100 else "low"
            ),
            "average_level_db": average_level_db,
            "sinr_degradation_db": sinr_degradation,
            "bandwidth_mhz": sum(
                source.get("bandwidth_hz", 0) for source in interference_sources
            )
            / 1e6,
            "frequency_overlap": len(
                [
                    s
                    for s in interference_sources
                    if abs(s.get("frequency_hz", 0) - self.current_frequency * 1e6)
                    < 10e6
                ]
            ),
        }

    async def _save_model(self, episode_or_name):
        """保存模型"""
        try:
            model_path = self.model_save_path / f"ai_ran_model_{episode_or_name}.pth"
            torch.save(
                {
                    "model_state_dict": self.ai_network.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "epsilon": self.epsilon,
                    "training_stats": self.training_stats,
                },
                model_path,
            )

            # 保存標準化器
            scaler_path = self.model_save_path / f"scaler_{episode_or_name}.pkl"
            with open(scaler_path, "wb") as f:
                pickle.dump(self.scaler, f)

            self.logger.info("模型已保存", path=str(model_path))

        except Exception as e:
            self.logger.error("保存模型失敗", error=str(e))

    def _load_model_if_exists(self):
        """載入預訓練模型"""
        try:
            model_path = self.model_save_path / "ai_ran_model_final.pth"
            scaler_path = self.model_save_path / "scaler_final.pkl"

            if model_path.exists() and scaler_path.exists():
                checkpoint = torch.load(model_path, map_location=self.device)
                self.ai_network.load_state_dict(checkpoint["model_state_dict"])
                self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
                self.epsilon = checkpoint.get("epsilon", self.epsilon)
                self.training_stats = checkpoint.get(
                    "training_stats", self.training_stats
                )

                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)

                self.logger.info("已載入預訓練模型", path=str(model_path))

        except Exception as e:
            self.logger.warning("載入預訓練模型失敗", error=str(e))

    def _generate_simulation_environment(self) -> Dict:
        """生成模擬環境"""
        # 隨機生成干擾和網絡狀態用於訓練
        num_interferors = np.random.randint(0, 5)
        interference_sources = []

        for i in range(num_interferors):
            interference_sources.append(
                {
                    "source_id": f"jammer_{i}",
                    "power_dbm": np.random.uniform(-100, -60),
                    "frequency_hz": np.random.choice(self.available_frequencies) * 1e6,
                    "bandwidth_hz": np.random.uniform(5e6, 50e6),
                }
            )

        network_state = {
            "sinr_db": np.random.uniform(5, 25),
            "rsrp_dbm": np.random.uniform(-120, -60),
            "tx_power_dbm": np.random.uniform(15, 30),
            "frequency_mhz": self.current_frequency,
            "bandwidth_mhz": 20,
            "ue_count": np.random.randint(1, 10),
            "throughput_mbps": np.random.uniform(10, 100),
            "latency_ms": np.random.uniform(20, 100),
            "packet_loss_rate": np.random.uniform(0, 0.1),
        }

        interference_data = {
            "interference_detected": len(interference_sources) > 0,
            "interference_sources": interference_sources,
            "interference_analysis": self._analyze_interference(
                interference_sources, [network_state["sinr_db"]]
            ),
        }

        return {"interference_data": interference_data, "network_state": network_state}

    async def get_service_status(self) -> Dict:
        """獲取服務狀態"""
        return {
            "service_name": "AI-RAN 抗干擾服務",
            "model_loaded": hasattr(self, "ai_network"),
            "device": str(self.device),
            "current_frequency_mhz": self.current_frequency,
            "epsilon": self.epsilon,
            "training_stats": self.training_stats,
            "available_strategies": list(self.interference_strategies.keys()),
            "experience_buffer_size": len(self.experience_replay),
        }
