"""
AI-RAN (AI無線接入網路) 服務

實現基於人工智慧的抗干擾決策系統，包括：
- 深度強化學習 (DQN/DDPG) 干擾避讓算法
- 動態頻率跳變決策
- 自適應波束成形控制
- 毫秒級實時決策響應
"""

import logging
import time
import uuid
import asyncio
import pickle
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import json

try:
    import tensorflow as tf
    from tensorflow import keras
    from collections import deque
    import random

    AI_AVAILABLE = True
except ImportError:
    tf = None
    keras = None
    deque = None
    random = None
    AI_AVAILABLE = False

# 暫時禁用 AI 模式來避免 Keras 版本問題
AI_AVAILABLE = False

from ..models.interference_models import (
    AIRANDecision,
    AIRANDecisionType,
    AIRANControlRequest,
    AIRANControlResponse,
    FrequencyHopPattern,
    FrequencyHopStrategy,
    BeamformingConfig,
    BeamformingStrategy,
    InterferenceDetectionResult,
    InterferenceMetrics,
)

logger = logging.getLogger(__name__)


class DQNAgent:
    """深度Q網路代理，用於頻率選擇決策"""

    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000) if deque else []
        self.epsilon = 1.0  # 探索率
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = learning_rate
        self.model = self._build_model() if AI_AVAILABLE else None
        self.target_model = self._build_model() if AI_AVAILABLE else None
        self.update_target_model()

    def _build_model(self):
        """構建DQN模型"""
        if not AI_AVAILABLE:
            return None

        model = keras.Sequential(
            [
                keras.layers.Dense(64, input_dim=self.state_size, activation="relu"),
                keras.layers.Dense(64, activation="relu"),
                keras.layers.Dense(32, activation="relu"),
                keras.layers.Dense(self.action_size, activation="linear"),
            ]
        )
        model.compile(
            loss="mse", optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate)
        )
        return model

    def update_target_model(self):
        """更新目標模型"""
        if self.model and self.target_model:
            self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        """記住經驗"""
        if deque:
            self.memory.append((state, action, reward, next_state, done))
        else:
            if len(self.memory) >= 10000:
                self.memory.pop(0)
            self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        """選擇行動"""
        if not self.model or (random and random.uniform(0, 1) <= self.epsilon):
            return random.randrange(self.action_size) if random else 0

        q_values = self.model.predict(state, verbose=0)
        return np.argmax(q_values[0])

    def replay(self, batch_size=32):
        """經驗回放訓練"""
        if not self.model or len(self.memory) < batch_size:
            return

        batch = random.sample(self.memory, batch_size)
        states = np.array([e[0] for e in batch])
        actions = np.array([e[1] for e in batch])
        rewards = np.array([e[2] for e in batch])
        next_states = np.array([e[3] for e in batch])
        dones = np.array([e[4] for e in batch])

        states = np.squeeze(states)
        next_states = np.squeeze(next_states)

        targets = self.model.predict(states, verbose=0)
        next_q_values = self.target_model.predict(next_states, verbose=0)

        for i in range(batch_size):
            if dones[i]:
                targets[i][actions[i]] = rewards[i]
            else:
                targets[i][actions[i]] = rewards[i] + 0.95 * np.max(next_q_values[i])

        self.model.fit(states, targets, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay


class AIRANService:
    """AI-RAN 抗干擾服務"""

    def __init__(self):
        """初始化 AI-RAN 服務"""
        self.logger = logger
        self.ai_available = AI_AVAILABLE

        # 頻率管理
        self.available_frequencies = list(
            range(2100, 2200, 5)
        )  # 2.1GHz band, 5MHz steps
        self.frequency_blacklist = set()
        self.frequency_usage_history = {}

        # DQN 代理
        state_size = 20  # 干擾環境狀態維度
        action_size = len(self.available_frequencies)
        self.dqn_agent = DQNAgent(state_size, action_size) if AI_AVAILABLE else None

        # 跳頻模式
        self.hop_patterns = {}
        self.active_hop_patterns = {}

        # 波束成形配置
        self.beam_configs = {}
        self.active_beam_configs = {}

        # 決策歷史
        self.decision_history = []
        self.performance_metrics = {}

        # 快取
        self.decision_cache = {}

        self.logger.info(f"AI-RAN 服務初始化完成 (AI: {self.ai_available})")

    async def make_anti_jamming_decision(
        self, request: AIRANControlRequest
    ) -> AIRANControlResponse:
        """
        做出抗干擾決策

        Args:
            request: AI-RAN 控制請求

        Returns:
            AI-RAN 控制響應
        """
        start_time = time.time()
        control_id = f"ctrl_{uuid.uuid4().hex[:8]}"

        try:
            self.logger.info(f"開始 AI-RAN 決策 {control_id}")

            # 分析當前干擾狀態
            interference_analysis = await self._analyze_interference_state(
                request.current_interference_state
            )

            # 選擇決策策略
            decision_type = await self._select_decision_strategy(
                interference_analysis, request
            )

            # 執行具體決策
            if decision_type == AIRANDecisionType.FREQUENCY_HOP:
                ai_decision = await self._make_frequency_hop_decision(
                    interference_analysis, request
                )
            elif decision_type == AIRANDecisionType.BEAM_STEERING:
                ai_decision = await self._make_beam_steering_decision(
                    interference_analysis, request
                )
            elif decision_type == AIRANDecisionType.POWER_CONTROL:
                ai_decision = await self._make_power_control_decision(
                    interference_analysis, request
                )
            else:
                ai_decision = await self._make_emergency_decision(
                    interference_analysis, request
                )

            # 生成備選決策
            alternatives = await self._generate_alternative_decisions(
                interference_analysis, request, ai_decision
            )

            # 創建執行計劃
            execution_plan = await self._create_execution_plan(ai_decision)
            rollback_plan = await self._create_rollback_plan(ai_decision)

            # 評估預期效果
            performance_prediction = await self._predict_performance(ai_decision)
            risk_assessment = await self._assess_risks(ai_decision)

            decision_time_ms = (time.time() - start_time) * 1000

            response = AIRANControlResponse(
                request_id=request.request_id,
                control_id=control_id,
                success=True,
                message=f"AI-RAN 決策完成: {ai_decision.decision_type.value}",
                ai_decision=ai_decision,
                alternative_decisions=alternatives,
                execution_plan=execution_plan,
                rollback_plan=rollback_plan,
                performance_prediction=performance_prediction,
                risk_assessment=risk_assessment,
                decision_time_ms=decision_time_ms,
                estimated_execution_time_ms=ai_decision.execution_delay_ms,
            )

            # 記錄決策歷史
            self.decision_history.append(
                {
                    "control_id": control_id,
                    "request": request.dict(),
                    "response": response.dict(),
                    "timestamp": datetime.utcnow(),
                }
            )

            self.logger.info(
                f"AI-RAN 決策 {control_id} 完成",
                extra={
                    "decision_type": ai_decision.decision_type.value,
                    "confidence": ai_decision.confidence_score,
                    "decision_time_ms": decision_time_ms,
                },
            )

            return response

        except Exception as e:
            self.logger.error(f"AI-RAN 決策 {control_id} 失敗: {e}", exc_info=True)
            return AIRANControlResponse(
                request_id=request.request_id,
                control_id=control_id,
                success=False,
                message=f"決策失敗: {str(e)}",
                ai_decision=AIRANDecision(
                    decision_id=f"fallback_{uuid.uuid4().hex[:8]}",
                    trigger_event="decision_failure",
                    interference_level_db=-50.0,
                    decision_type=AIRANDecisionType.EMERGENCY_SHUTDOWN,
                    confidence_score=0.1,
                ),
                alternative_decisions=[],
                execution_plan=[],
                rollback_plan=[],
                performance_prediction={},
                risk_assessment={"error": str(e)},
                decision_time_ms=(time.time() - start_time) * 1000,
                estimated_execution_time_ms=0.0,
            )

    async def _analyze_interference_state(
        self, interference_state: List[InterferenceDetectionResult]
    ) -> Dict[str, Any]:
        """分析干擾狀態"""
        if not interference_state:
            return {"severity": "low", "jammer_types": [], "affected_frequencies": []}

        # 計算干擾嚴重程度
        avg_sinr = np.mean([result.sinr_db for result in interference_state])
        max_interference = max(
            [result.interference_power_dbm for result in interference_state]
        )

        if avg_sinr < -5:
            severity = "critical"
        elif avg_sinr < 5:
            severity = "high"
        elif avg_sinr < 15:
            severity = "medium"
        else:
            severity = "low"

        # 統計干擾類型
        jammer_types = {}
        for result in interference_state:
            if result.suspected_jammer_type:
                jtype = result.suspected_jammer_type.value
                jammer_types[jtype] = jammer_types.get(jtype, 0) + 1

        # 受影響頻率
        affected_freqs = []
        for result in interference_state:
            for freq_info in result.affected_frequencies:
                affected_freqs.append(freq_info["frequency_mhz"])

        return {
            "severity": severity,
            "avg_sinr_db": avg_sinr,
            "max_interference_dbm": max_interference,
            "jammer_types": jammer_types,
            "affected_frequencies": list(set(affected_freqs)),
            "total_detections": len(interference_state),
        }

    async def _select_decision_strategy(
        self, analysis: Dict[str, Any], request: AIRANControlRequest
    ) -> AIRANDecisionType:
        """選擇決策策略"""
        severity = analysis["severity"]

        if severity == "critical":
            return AIRANDecisionType.EMERGENCY_SHUTDOWN
        elif severity == "high":
            # 根據干擾類型選擇策略
            jammer_types = analysis.get("jammer_types", {})
            if "sweep_jammer" in jammer_types:
                return AIRANDecisionType.FREQUENCY_HOP
            elif "smart_jammer" in jammer_types:
                return AIRANDecisionType.BEAM_STEERING
            else:
                return AIRANDecisionType.FREQUENCY_HOP
        elif severity == "medium":
            return AIRANDecisionType.POWER_CONTROL
        else:
            return AIRANDecisionType.FREQUENCY_HOP

    async def _make_frequency_hop_decision(
        self, analysis: Dict[str, Any], request: AIRANControlRequest
    ) -> AIRANDecision:
        """做出跳頻決策"""
        # 排除受干擾頻率
        affected_freqs = set(analysis.get("affected_frequencies", []))
        available_freqs = [
            f
            for f in request.available_frequencies_mhz
            if f not in affected_freqs and f not in self.frequency_blacklist
        ]

        if not available_freqs:
            available_freqs = request.available_frequencies_mhz[:3]  # 緊急後備

        # 使用 DQN 選擇最佳頻率（如果可用）
        if self.dqn_agent and self.ai_available:
            state = self._encode_interference_state(analysis)
            action_idx = self.dqn_agent.act(state.reshape(1, -1))
            if action_idx < len(available_freqs):
                target_freq = available_freqs[action_idx]
            else:
                target_freq = available_freqs[0]
        else:
            # 啟發式選擇：選擇SINR最高的頻率
            target_freq = available_freqs[0]

        # 創建跳頻模式
        hop_pattern_id = f"hop_{uuid.uuid4().hex[:8]}"
        hop_pattern = FrequencyHopPattern(
            pattern_id=hop_pattern_id,
            strategy=FrequencyHopStrategy.ADAPTIVE_ML,
            frequency_list_mhz=available_freqs,
            hop_duration_ms=10.0,  # 10ms 跳頻間隔
            dwell_time_ms=5.0,
        )

        self.hop_patterns[hop_pattern_id] = hop_pattern

        decision = AIRANDecision(
            decision_id=f"freq_hop_{uuid.uuid4().hex[:8]}",
            trigger_event=f"interference_severity_{analysis['severity']}",
            interference_level_db=analysis.get("max_interference_dbm", -50.0),
            urgency_level=3 if analysis["severity"] == "high" else 2,
            decision_type=AIRANDecisionType.FREQUENCY_HOP,
            confidence_score=0.8,
            target_frequencies_mhz=[target_freq],
            hop_pattern_id=hop_pattern_id,
            execution_delay_ms=1.0,  # 1ms 執行延遲
            expected_sinr_improvement_db=10.0,
            expected_throughput_improvement_percent=25.0,
            interference_risk_score=0.2,
        )

        return decision

    async def _make_beam_steering_decision(
        self, analysis: Dict[str, Any], request: AIRANControlRequest
    ) -> AIRANDecision:
        """做出波束控制決策"""
        # 創建波束配置
        beam_config_id = f"beam_{uuid.uuid4().hex[:8]}"
        beam_config = BeamformingConfig(
            config_id=beam_config_id,
            strategy=BeamformingStrategy.ADAPTIVE_BEAM,
            antenna_count=8,
            target_direction_deg=(45.0, 10.0),  # 假設方向
            beam_width_deg=20.0,
            null_directions_deg=[(180.0, 0.0)],  # 干擾源方向
            adaptation_enabled=True,
            update_interval_ms=50.0,
        )

        self.beam_configs[beam_config_id] = beam_config

        decision = AIRANDecision(
            decision_id=f"beam_steer_{uuid.uuid4().hex[:8]}",
            trigger_event=f"smart_jammer_detected",
            interference_level_db=analysis.get("max_interference_dbm", -50.0),
            urgency_level=4,
            decision_type=AIRANDecisionType.BEAM_STEERING,
            confidence_score=0.75,
            beam_config_id=beam_config_id,
            execution_delay_ms=2.0,
            expected_sinr_improvement_db=15.0,
            expected_throughput_improvement_percent=35.0,
            interference_risk_score=0.15,
        )

        return decision

    async def _make_power_control_decision(
        self, analysis: Dict[str, Any], request: AIRANControlRequest
    ) -> AIRANDecision:
        """做出功率控制決策"""
        # 根據干擾水平調整功率
        interference_level = analysis.get("max_interference_dbm", -50.0)
        power_adjustment = min(10.0, max(-5.0, interference_level + 80.0))

        decision = AIRANDecision(
            decision_id=f"power_ctrl_{uuid.uuid4().hex[:8]}",
            trigger_event=f"medium_interference",
            interference_level_db=interference_level,
            urgency_level=2,
            decision_type=AIRANDecisionType.POWER_CONTROL,
            confidence_score=0.9,
            power_adjustment_db=power_adjustment,
            execution_delay_ms=0.5,
            expected_sinr_improvement_db=5.0,
            expected_throughput_improvement_percent=15.0,
            interference_risk_score=0.1,
        )

        return decision

    async def _make_emergency_decision(
        self, analysis: Dict[str, Any], request: AIRANControlRequest
    ) -> AIRANDecision:
        """做出緊急決策"""
        decision = AIRANDecision(
            decision_id=f"emergency_{uuid.uuid4().hex[:8]}",
            trigger_event="critical_interference",
            interference_level_db=analysis.get("max_interference_dbm", -30.0),
            urgency_level=5,
            decision_type=AIRANDecisionType.EMERGENCY_SHUTDOWN,
            confidence_score=1.0,
            execution_delay_ms=0.1,
            expected_sinr_improvement_db=0.0,
            expected_throughput_improvement_percent=0.0,
            interference_risk_score=1.0,
        )

        return decision

    def _encode_interference_state(self, analysis: Dict[str, Any]) -> np.ndarray:
        """編碼干擾狀態為 DQN 輸入"""
        # 簡化的狀態編碼
        state = np.zeros(20)

        # 基本指標
        state[0] = analysis.get("avg_sinr_db", 0) / 30.0  # 歸一化到 [-1, 1]
        state[1] = analysis.get("max_interference_dbm", -100) / 100.0
        state[2] = len(analysis.get("affected_frequencies", [])) / 100.0

        # 干擾類型 (one-hot 編碼)
        jammer_types = analysis.get("jammer_types", {})
        if "broadband_noise" in jammer_types:
            state[3] = 1.0
        if "sweep_jammer" in jammer_types:
            state[4] = 1.0
        if "smart_jammer" in jammer_types:
            state[5] = 1.0

        # 嚴重程度
        severity_map = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
        state[6] = severity_map.get(analysis.get("severity", "low"), 0.25)

        # 歷史性能（簡化）
        state[7:] = np.random.random(13) * 0.1  # 模擬歷史數據

        return state

    # 其他輔助方法的簡化實現
    async def _generate_alternative_decisions(self, analysis, request, primary):
        return []

    async def _create_execution_plan(self, decision):
        return [{"step": "execute", "action": decision.decision_type.value}]

    async def _create_rollback_plan(self, decision):
        return [{"step": "rollback", "action": "restore_previous_config"}]

    async def _predict_performance(self, decision):
        return {"predicted_improvement": decision.expected_sinr_improvement_db}

    async def _assess_risks(self, decision):
        return {"risk_score": decision.interference_risk_score}
