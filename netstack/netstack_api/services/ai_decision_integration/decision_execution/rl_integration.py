"""
強化學習決策引擎實現
====================

整合DQN、PPO、SAC等算法，提供統一的RL決策接口。
"""

import time
import asyncio
import logging
try:
    import numpy as np
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    np = None
    torch = None
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque, defaultdict

from ..interfaces.decision_engine import (
    RLIntegrationInterface,
    Decision,
    RLState,
    RLAction,
)
from ..interfaces.candidate_selector import ScoredCandidate

# 嘗試導入 RL 服務，如果失敗則使用模擬
try:
    from ...rl.manager import UnifiedAIService
    from ...algorithm_ecosystem.registry import AlgorithmRegistry
    RL_SERVICES_AVAILABLE = True
except ImportError:
    RL_SERVICES_AVAILABLE = False
    UnifiedAIService = None
    AlgorithmRegistry = None

logger = logging.getLogger(__name__)


class RLDecisionEngine(RLIntegrationInterface):
    """
    強化學習決策引擎

    整合多種RL算法，提供統一的決策接口：
    - DQN (Deep Q-Network)
    - PPO (Proximal Policy Optimization)
    - SAC (Soft Actor-Critic)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化RL決策引擎

        Args:
            config: 配置參數
        """
        self.config = config or {}
        self.logger = logger

        # 算法管理
        self.available_algorithms = ["DQN", "PPO", "SAC"]
        self.current_algorithm = self.config.get("default_algorithm", "DQN")
        
        # RL服務管理
        if RL_SERVICES_AVAILABLE:
            self.algorithm_registry = AlgorithmRegistry()
            self.rl_service = UnifiedAIService("handover_decision")
        else:
            self.algorithm_registry = None
            self.rl_service = None
            self.logger.warning("RL 服務不可用，將使用模擬模式")

        # 性能統計
        self.decision_count = 0
        self.total_decision_time = 0.0
        self.algorithm_performance = defaultdict(
            lambda: {
                "decisions": 0,
                "avg_time": 0.0,
                "success_rate": 0.0,
                "confidence_scores": deque(maxlen=100),
            }
        )

        # 狀態管理
        self.state_history = deque(maxlen=1000)
        self.action_history = deque(maxlen=1000)

        # 配置參數
        self.confidence_threshold = self.config.get("confidence_threshold", 0.8)
        self.decision_timeout = self.config.get("decision_timeout", 5.0)
        self.exploration_rate = self.config.get("exploration_rate", 0.1)

        self.logger.info(
            "RL決策引擎初始化完成",
            algorithms=self.available_algorithms,
            current_algorithm=self.current_algorithm,
        )

    def make_decision(
        self, candidates: List[ScoredCandidate], context: Dict[str, Any]
    ) -> Decision:
        """
        整合RL系統做出決策

        Args:
            candidates: 評分後的候選列表
            context: 決策上下文

        Returns:
            Decision: 決策結果
        """
        start_time = time.time()
        decision_id = f"decision_{int(time.time() * 1000)}"

        try:
            self.logger.debug(
                "開始RL決策",
                candidates_count=len(candidates),
                algorithm=self.current_algorithm,
            )

            # 1. 準備RL狀態
            rl_state = self.prepare_rl_state(candidates, context)

            # 2. 選擇最佳算法
            best_algorithm = self.select_best_algorithm(context)

            # 3. 執行RL推理
            rl_action = self.execute_rl_action(rl_state)

            # 4. 轉換為決策結果
            decision = self._convert_action_to_decision(
                rl_action, candidates, context, best_algorithm
            )

            # 5. 準備視覺化數據
            decision.visualization_data = self.prepare_visualization_data(
                decision, candidates
            )

            # 6. 記錄性能統計
            decision_time = (time.time() - start_time) * 1000
            decision.decision_time = decision_time
            self._update_performance_stats(
                best_algorithm, decision_time, decision.confidence
            )

            self.logger.info(
                "RL決策完成",
                decision_id=decision_id,
                selected_satellite=decision.selected_satellite,
                confidence=decision.confidence,
                algorithm=best_algorithm,
                decision_time=decision_time,
            )

            return decision

        except Exception as e:
            self.logger.error("RL決策失敗 [%s]: %s", decision_id, str(e))
            return self._create_fallback_decision(candidates, context, str(e))

    def prepare_rl_state(
        self, candidates: List[ScoredCandidate], context: Dict[str, Any]
    ) -> RLState:
        """
        準備強化學習狀態向量

        Args:
            candidates: 候選列表
            context: 上下文信息

        Returns:
            RLState: RL狀態表示
        """
        # 構建衛星狀態向量
        satellite_states = []
        for scored_candidate in candidates:
            candidate = scored_candidate.candidate
            state_vector = {
                "elevation": candidate.elevation / 90.0,  # 標準化到 [0,1]
                "signal_strength": (candidate.signal_strength + 120) / 50.0,  # 標準化
                "load_factor": candidate.load_factor,
                "distance": min(candidate.distance / 2000.0, 1.0),  # 標準化，最大2000km
                "visibility_time": min(
                    candidate.visibility_time / 3600.0, 1.0
                ),  # 標準化，最大1小時
                "doppler_shift": abs(candidate.doppler_shift) / 5000.0,  # 標準化
                "score": scored_candidate.score,
                "confidence": scored_candidate.confidence,
                "ranking": (
                    1.0 / scored_candidate.ranking
                    if scored_candidate.ranking > 0
                    else 0.0
                ),
            }
            satellite_states.append(state_vector)

        # 構建網路條件
        network_conditions = {
            "traffic_load": context.get("traffic_load", 0.5),
            "interference_level": context.get("interference_level", 0.3),
            "weather_condition": context.get("weather_condition", 0.8),
            "time_of_day": self._get_time_feature(),
            "handover_urgency": context.get("handover_urgency", 0.5),
        }

        # 構建用戶上下文
        user_context = {
            "user_id": context.get("user_id", "unknown"),
            "service_type": context.get("service_type", "data"),
            "qos_requirements": context.get("qos_requirements", {}),
            "mobility_pattern": context.get("mobility_pattern", "stationary"),
        }

        # 構建歷史性能
        historical_performance = self._get_recent_performance_metrics()

        # 構建時間特徵
        if PYTORCH_AVAILABLE:
            time_features = {
                "hour_sin": np.sin(2 * np.pi * datetime.now().hour / 24),
                "hour_cos": np.cos(2 * np.pi * datetime.now().hour / 24),
                "day_of_week": datetime.now().weekday() / 6.0,
                "is_weekend": float(datetime.now().weekday() >= 5),
            }
        else:
            import math
            time_features = {
                "hour_sin": math.sin(2 * math.pi * datetime.now().hour / 24),
                "hour_cos": math.cos(2 * math.pi * datetime.now().hour / 24),
                "day_of_week": datetime.now().weekday() / 6.0,
                "is_weekend": float(datetime.now().weekday() >= 5),
            }

        rl_state = RLState(
            satellite_states=satellite_states,
            network_conditions=network_conditions,
            user_context=user_context,
            historical_performance=historical_performance,
            time_features=time_features,
        )

        # 記錄狀態歷史
        self.state_history.append(rl_state)

        return rl_state

    def execute_rl_action(self, state: RLState) -> RLAction:
        """
        執行強化學習推理

        Args:
            state: RL狀態

        Returns:
            RLAction: RL動作
        """
        try:
            # 如果 RL 服務可用，調用真實服務
            if self.rl_service is not None:
                # 轉換狀態為RL服務可識別的格式
                input_data = self._convert_state_to_input(state)

                # 調用RL服務
                rl_result = asyncio.run(self.rl_service.make_decision(input_data))

                if rl_result["status"] == "success":
                    action_data = rl_result["action"]

                    rl_action = RLAction(
                        action_type=action_data.get("action_type", "select_satellite"),
                        target_satellite=action_data.get("target_satellite", ""),
                        parameters=action_data.get("parameters", {}),
                        confidence=action_data.get("confidence", 0.5),
                    )

                    # 記錄動作歷史
                    self.action_history.append(rl_action)

                    return rl_action
                else:
                    self.logger.warning("RL服務決策失敗", result=rl_result)
                    return self._create_fallback_action(state)
            else:
                # 使用模擬決策
                return self._create_mock_action(state)

        except Exception as e:
            self.logger.error("RL推理執行失敗: %s", str(e))
            return self._create_fallback_action(state)

    def update_policy(self, feedback: Dict[str, Any]) -> None:
        """
        根據反饋更新RL策略

        Args:
            feedback: 執行反饋數據
        """
        try:
            # 提取反饋信息
            execution_result = feedback.get("execution_result", {})
            performance_metrics = feedback.get("performance_metrics", {})
            user_satisfaction = feedback.get("user_satisfaction", 0.5)

            # 計算獎勵信號
            reward = self._calculate_reward(
                execution_result, performance_metrics, user_satisfaction
            )

            # 更新算法性能統計
            algorithm_used = feedback.get("algorithm_used", self.current_algorithm)
            self._update_algorithm_feedback(algorithm_used, reward, execution_result)

            # 調整探索率
            self._adjust_exploration_rate(reward)

            self.logger.debug(
                "RL策略更新完成",
                algorithm=algorithm_used,
                reward=reward,
                exploration_rate=self.exploration_rate,
            )

        except Exception as e:
            self.logger.error("RL策略更新失敗: %s", str(e))

    def get_confidence_score(self, decision: Decision) -> float:
        """
        獲取決策的置信度分數

        Args:
            decision: 決策結果

        Returns:
            float: 置信度分數
        """
        base_confidence = decision.confidence

        # 基於歷史性能調整
        algorithm_perf = self.algorithm_performance.get(decision.algorithm_used, {})
        success_rate = algorithm_perf.get("success_rate", 0.5)

        # 基於候選質量調整
        reasoning = decision.reasoning
        candidate_quality = reasoning.get("candidate_quality", 0.5)

        # 綜合置信度計算
        adjusted_confidence = (
            0.5 * base_confidence + 0.3 * success_rate + 0.2 * candidate_quality
        )

        return min(1.0, max(0.0, adjusted_confidence))

    def prepare_visualization_data(
        self, decision: Decision, candidates: List[ScoredCandidate]
    ) -> Dict[str, Any]:
        """
        準備3D視覺化所需數據

        Args:
            decision: 決策結果
            candidates: 候選列表

        Returns:
            Dict[str, Any]: 視覺化數據
        """
        # 選中衛星的詳細信息
        selected_satellite = None
        for scored_candidate in candidates:
            if scored_candidate.candidate.satellite_id == decision.selected_satellite:
                selected_satellite = scored_candidate.candidate
                break

        visualization_data = {
            "selected_satellite": {
                "id": decision.selected_satellite,
                "position": selected_satellite.position if selected_satellite else {},
                "velocity": selected_satellite.velocity if selected_satellite else {},
                "elevation": selected_satellite.elevation if selected_satellite else 0,
                "signal_strength": (
                    selected_satellite.signal_strength if selected_satellite else -100
                ),
            },
            "candidates": [
                {
                    "id": sc.candidate.satellite_id,
                    "score": sc.score,
                    "ranking": sc.ranking,
                    "position": sc.candidate.position,
                    "elevation": sc.candidate.elevation,
                    "signal_strength": sc.candidate.signal_strength,
                }
                for sc in candidates[:5]  # 只顯示前5個候選
            ],
            "decision_metadata": {
                "algorithm": decision.algorithm_used,
                "confidence": decision.confidence,
                "decision_time": decision.decision_time,
                "reasoning": decision.reasoning,
            },
            "animation_config": {
                "handover_duration": 3000,  # 3秒動畫
                "highlight_selected": True,
                "show_signal_lines": True,
                "camera_follow": True,
            },
        }

        return visualization_data

    def get_available_algorithms(self) -> List[str]:
        """
        獲取可用的RL算法列表

        Returns:
            List[str]: 算法名稱列表
        """
        return self.available_algorithms.copy()

    def select_best_algorithm(self, context: Dict[str, Any]) -> str:
        """
        根據上下文選擇最佳算法

        Args:
            context: 決策上下文

        Returns:
            str: 最佳算法名稱
        """
        # 獲取上下文特徵
        urgency = context.get("handover_urgency", 0.5)
        network_stability = context.get("network_stability", 0.8)
        candidate_count = context.get("candidate_count", 5)

        # 算法選擇邏輯
        if urgency > 0.8:
            # 緊急情況，選擇快速算法
            return "DQN"
        elif network_stability < 0.3:
            # 網路不穩定，選擇魯棒算法
            return "SAC"
        elif candidate_count > 10:
            # 候選較多，選擇探索能力強的算法
            return "PPO"
        else:
            # 根據歷史性能選擇
            best_algorithm = self.current_algorithm
            best_performance = 0.0

            for algorithm, stats in self.algorithm_performance.items():
                if algorithm in self.available_algorithms:
                    performance = stats.get("success_rate", 0.0)
                    if performance > best_performance:
                        best_performance = performance
                        best_algorithm = algorithm

            return best_algorithm

    def get_algorithm_performance_history(
        self, algorithm_name: str
    ) -> Dict[str, List[float]]:
        """
        獲取算法性能歷史

        Args:
            algorithm_name: 算法名稱

        Returns:
            Dict[str, List[float]]: 性能歷史數據
        """
        if algorithm_name not in self.algorithm_performance:
            return {"confidence_scores": [], "response_times": [], "success_rates": []}

        stats = self.algorithm_performance[algorithm_name]
        return {
            "confidence_scores": list(stats["confidence_scores"]),
            "avg_response_time": [stats["avg_time"]],
            "success_rate": [stats["success_rate"]],
        }

    # 輔助方法
    def _convert_action_to_decision(
        self,
        action: RLAction,
        candidates: List[ScoredCandidate],
        context: Dict[str, Any],
        algorithm: str,
    ) -> Decision:
        """轉換RL動作為決策結果"""
        # 尋找目標衛星
        target_satellite = action.target_satellite
        if not target_satellite and candidates:
            # 如果RL沒有指定目標，選擇評分最高的
            target_satellite = candidates[0].candidate.satellite_id

        # 生成備選方案
        alternative_options = [
            sc.candidate.satellite_id
            for sc in candidates[1:4]  # 取前3個備選
            if sc.candidate.satellite_id != target_satellite
        ]

        # 構建執行計劃
        execution_plan = {
            "handover_type": context.get("handover_type", "A4"),
            "preparation_time": 500,  # 500ms準備時間
            "execution_time": 2000,  # 2s執行時間
            "verification_time": 500,  # 500ms驗證時間
        }

        # 預期性能指標
        expected_performance = {
            "latency_improvement": action.parameters.get(
                "expected_latency_reduction", 10.0
            ),
            "throughput_improvement": action.parameters.get(
                "expected_throughput_increase", 15.0
            ),
            "signal_quality": action.parameters.get("expected_signal_quality", 0.8),
        }

        decision = Decision(
            selected_satellite=target_satellite,
            confidence=action.confidence,
            reasoning={
                "algorithm": algorithm,
                "action_type": action.action_type,
                "rl_confidence": action.confidence,
                "candidate_ranking": self._get_candidate_ranking(
                    target_satellite, candidates
                ),
            },
            alternative_options=alternative_options,
            execution_plan=execution_plan,
            visualization_data={},  # 將在後續填充
            algorithm_used=algorithm,
            decision_time=0.0,  # 將在外部設置
            context=context,
            expected_performance=expected_performance,
        )

        return decision

    def _create_fallback_decision(
        self,
        candidates: List[ScoredCandidate],
        context: Dict[str, Any],
        error_reason: str,
    ) -> Decision:
        """創建回退決策"""
        if not candidates:
            self.logger.warning("無候選衛星可用於回退決策")
            return Decision(
                selected_satellite="NONE",
                confidence=0.1,
                reasoning={"error": error_reason, "fallback": True},
                alternative_options=[],
                execution_plan={},
                visualization_data={},
                algorithm_used="FALLBACK",
                decision_time=0.0,
                context=context,
                expected_performance={},
            )

        # 選擇評分最高的候選
        best_candidate = candidates[0]

        return Decision(
            selected_satellite=best_candidate.candidate.satellite_id,
            confidence=0.5,  # 中等置信度
            reasoning={
                "fallback": True,
                "error": error_reason,
                "selection_basis": "highest_score",
            },
            alternative_options=[sc.candidate.satellite_id for sc in candidates[1:3]],
            execution_plan={"handover_type": "A4"},
            visualization_data={},
            algorithm_used="FALLBACK",
            decision_time=0.0,
            context=context,
            expected_performance={"latency_improvement": 5.0},
        )

    def _create_fallback_action(self, state: RLState) -> RLAction:
        """創建回退動作"""
        # 選擇第一個候選衛星
        target_satellite = ""
        if state.satellite_states:
            # 找到評分最高的衛星
            best_satellite = max(
                state.satellite_states, key=lambda s: s.get("score", 0.0)
            )
            # 這裡需要從狀態中獲取衛星ID，簡化處理
            target_satellite = f"fallback_satellite"

        return RLAction(
            action_type="fallback_selection",
            target_satellite=target_satellite,
            parameters={"fallback": True},
            confidence=0.3,
        )

    def _create_mock_action(self, state: RLState) -> RLAction:
        """創建模擬動作"""
        # 選擇評分最高的候選衛星
        target_satellite = "SAT_001"  # 預設衛星
        confidence = 0.75  # 模擬置信度
        
        if state.satellite_states:
            # 找到評分最高的衛星
            best_satellite = max(
                state.satellite_states, key=lambda s: s.get("score", 0.0)
            )
            # 簡化處理，實際應該從狀態中獲取正確的衛星ID
            target_satellite = f"MOCK_SAT_{hash(str(best_satellite)) % 1000:03d}"
            confidence = min(0.95, best_satellite.get("score", 0.5) + 0.1)

        return RLAction(
            action_type="mock_selection",
            target_satellite=target_satellite,
            parameters={
                "mock_mode": True,
                "expected_latency_reduction": 12.0,
                "expected_throughput_increase": 8.0,
            },
            confidence=confidence,
        )

    def _convert_state_to_input(self, state: RLState) -> Dict[str, Any]:
        """轉換RL狀態為服務輸入格式"""
        return {
            "satellites": state.satellite_states,
            "network": state.network_conditions,
            "user": state.user_context,
            "history": state.historical_performance,
            "time": state.time_features,
        }

    def _get_time_feature(self) -> float:
        """獲取時間特徵 (0-1)"""
        hour = datetime.now().hour
        return hour / 24.0

    def _get_recent_performance_metrics(self) -> List[float]:
        """獲取最近性能指標"""
        # 簡化實現，返回虛擬數據
        return [0.8, 0.75, 0.82, 0.78, 0.85]

    def _calculate_reward(
        self,
        execution_result: Dict,
        performance_metrics: Dict,
        user_satisfaction: float,
    ) -> float:
        """計算獎勵信號"""
        # 執行成功獎勵
        success_reward = 1.0 if execution_result.get("success", False) else -0.5

        # 性能改善獎勵
        latency_improvement = performance_metrics.get("latency_improvement", 0.0)
        throughput_improvement = performance_metrics.get("throughput_improvement", 0.0)
        performance_reward = (latency_improvement + throughput_improvement) / 100.0

        # 用戶滿意度獎勵
        satisfaction_reward = (user_satisfaction - 0.5) * 2.0  # 標準化到 [-1, 1]

        # 綜合獎勵
        total_reward = (
            0.5 * success_reward + 0.3 * performance_reward + 0.2 * satisfaction_reward
        )

        # 如果 numpy 可用，使用 np.clip，否則使用 Python 內置的 min/max
        if PYTORCH_AVAILABLE:
            return np.clip(total_reward, -1.0, 1.0)
        else:
            return max(-1.0, min(1.0, total_reward))

    def _update_algorithm_feedback(
        self, algorithm: str, reward: float, execution_result: Dict
    ) -> None:
        """更新算法反饋統計"""
        if algorithm not in self.algorithm_performance:
            self.algorithm_performance[algorithm] = {
                "decisions": 0,
                "avg_time": 0.0,
                "success_rate": 0.0,
                "confidence_scores": deque(maxlen=100),
            }

        stats = self.algorithm_performance[algorithm]
        stats["decisions"] += 1

        # 更新成功率
        is_success = execution_result.get("success", False)
        current_success_rate = stats["success_rate"]
        stats["success_rate"] = (
            current_success_rate * (stats["decisions"] - 1)
            + (1.0 if is_success else 0.0)
        ) / stats["decisions"]

    def _adjust_exploration_rate(self, reward: float) -> None:
        """調整探索率"""
        if reward > 0.5:
            # 獎勵高，減少探索
            self.exploration_rate = max(0.01, self.exploration_rate * 0.95)
        elif reward < -0.3:
            # 獎勵低，增加探索
            self.exploration_rate = min(0.3, self.exploration_rate * 1.05)

    def _update_performance_stats(
        self, algorithm: str, decision_time: float, confidence: float
    ) -> None:
        """更新性能統計"""
        self.decision_count += 1
        self.total_decision_time += decision_time

        if algorithm not in self.algorithm_performance:
            self.algorithm_performance[algorithm] = {
                "decisions": 0,
                "avg_time": 0.0,
                "success_rate": 0.0,
                "confidence_scores": deque(maxlen=100),
            }

        stats = self.algorithm_performance[algorithm]
        stats["decisions"] += 1
        stats["confidence_scores"].append(confidence)

        # 更新平均響應時間
        current_avg = stats["avg_time"]
        stats["avg_time"] = (
            current_avg * (stats["decisions"] - 1) + decision_time
        ) / stats["decisions"]

    def _get_candidate_ranking(
        self, satellite_id: str, candidates: List[ScoredCandidate]
    ) -> int:
        """獲取候選衛星排名"""
        for i, scored_candidate in enumerate(candidates):
            if scored_candidate.candidate.satellite_id == satellite_id:
                return i + 1
        return len(candidates) + 1
