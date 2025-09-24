"""
Reinforcement Learning Extension Interface for Stage 4 Optimization

This module provides extension points for integrating reinforcement learning
algorithms with the existing optimization decision layer, as specified in
@docs/stages/stage4-optimization.md

Key Features:
- RL Agent Interface for custom algorithms
- State representation for satellite environments
- Action space definition for optimization decisions
- Reward function framework
- Experience replay and training coordination
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timezone
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RLState:
    """RL環境狀態表示"""
    satellite_positions: List[Dict[str, float]]
    signal_strengths: List[float]
    coverage_metrics: Dict[str, float]
    handover_history: List[Dict[str, Any]]
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class RLAction:
    """RL動作表示"""
    action_type: str  # 'satellite_selection', 'handover_trigger', 'pool_adjustment'
    target_satellites: List[str]
    parameters: Dict[str, Any]
    confidence: float


@dataclass
class RLReward:
    """RL獎勵信號"""
    total_reward: float
    component_rewards: Dict[str, float]  # signal_quality, coverage, cost, efficiency
    penalty_factors: Dict[str, float]
    normalized_score: float


class RLAgentInterface(ABC):
    """強化學習代理接口"""

    @abstractmethod
    def select_action(self, state: RLState) -> RLAction:
        """根據當前狀態選擇動作"""
        pass

    @abstractmethod
    def update_policy(self, state: RLState, action: RLAction, reward: RLReward, next_state: RLState):
        """更新策略網絡"""
        pass

    @abstractmethod
    def save_model(self, path: str) -> bool:
        """保存模型"""
        pass

    @abstractmethod
    def load_model(self, path: str) -> bool:
        """載入模型"""
        pass


class RLEnvironmentAdapter:
    """RL環境適配器 - 將衛星優化問題轉換為RL環境"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.RLEnvironmentAdapter")

        # RL環境配置
        self.state_dimensions = self.config.get('state_dimensions', 128)
        self.action_space_size = self.config.get('action_space_size', 64)
        self.reward_weights = self.config.get('reward_weights', {
            'signal_quality': 0.4,
            'coverage': 0.3,
            'handover_cost': -0.2,
            'energy_efficiency': 0.1
        })

        # 環境狀態
        self.current_state = None
        self.step_count = 0
        self.episode_reward = 0.0

        self.logger.info("✅ RL環境適配器初始化完成")

    def convert_to_rl_state(self, optimization_data: Dict[str, Any]) -> RLState:
        """將優化數據轉換為RL狀態"""
        try:
            # 提取衛星位置數據
            satellite_positions = []
            signal_strengths = []

            candidates = optimization_data.get('candidates', [])
            for candidate in candidates:
                if 'signal_analysis' in candidate:
                    signal_data = candidate['signal_analysis']

                    # 提取位置信息
                    position_data = {
                        'latitude': signal_data.get('latitude', 0.0),
                        'longitude': signal_data.get('longitude', 0.0),
                        'altitude': signal_data.get('altitude_km', 0.0)
                    }
                    satellite_positions.append(position_data)

                    # 提取信號強度
                    signal_strength = signal_data.get('average_signal_strength', -120.0)
                    signal_strengths.append(signal_strength)

            # 計算覆蓋指標
            coverage_metrics = {
                'total_satellites': len(candidates),
                'average_signal_strength': np.mean(signal_strengths) if signal_strengths else -120.0,
                'coverage_area': self._estimate_coverage_area(satellite_positions),
                'signal_diversity': np.std(signal_strengths) if len(signal_strengths) > 1 else 0.0
            }

            # 構建RL狀態
            rl_state = RLState(
                satellite_positions=satellite_positions,
                signal_strengths=signal_strengths,
                coverage_metrics=coverage_metrics,
                handover_history=optimization_data.get('handover_history', []),
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={
                    'state_id': f"rl_state_{self.step_count}",
                    'environment_version': '1.0.0',
                    'adaptation_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )

            self.current_state = rl_state
            self.step_count += 1

            return rl_state

        except Exception as e:
            self.logger.error(f"RL狀態轉換失敗: {e}")
            raise

    def convert_from_rl_action(self, rl_action: RLAction) -> Dict[str, Any]:
        """將RL動作轉換為優化決策"""
        try:
            optimization_decision = {
                'decision_type': rl_action.action_type,
                'selected_satellites': rl_action.target_satellites,
                'optimization_parameters': rl_action.parameters,
                'confidence_score': rl_action.confidence,
                'rl_generated': True,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            return optimization_decision

        except Exception as e:
            self.logger.error(f"RL動作轉換失敗: {e}")
            raise

    def calculate_reward(self, previous_state: RLState, action: RLAction,
                        current_state: RLState, optimization_results: Dict[str, Any]) -> RLReward:
        """計算獎勵信號"""
        try:
            component_rewards = {}
            penalty_factors = {}

            # 信號品質獎勵
            prev_signal_avg = np.mean(previous_state.signal_strengths) if previous_state.signal_strengths else -120.0
            curr_signal_avg = np.mean(current_state.signal_strengths) if current_state.signal_strengths else -120.0
            signal_improvement = curr_signal_avg - prev_signal_avg
            component_rewards['signal_quality'] = signal_improvement * self.reward_weights['signal_quality']

            # 覆蓋範圍獎勵
            coverage_improvement = (current_state.coverage_metrics.get('coverage_area', 0) -
                                  previous_state.coverage_metrics.get('coverage_area', 0))
            component_rewards['coverage'] = coverage_improvement * self.reward_weights['coverage']

            # 換手成本懲罰
            handover_cost = len(current_state.handover_history) - len(previous_state.handover_history)
            component_rewards['handover_cost'] = handover_cost * self.reward_weights['handover_cost']

            # 能效獎勵
            energy_score = optimization_results.get('energy_efficiency_score', 0.5)
            component_rewards['energy_efficiency'] = energy_score * self.reward_weights['energy_efficiency']

            # 約束違反懲罰
            constraint_violations = optimization_results.get('constraint_violations', 0)
            if constraint_violations > 0:
                penalty_factors['constraint_violation'] = -10.0 * constraint_violations

            # 計算總獎勵
            total_reward = sum(component_rewards.values()) + sum(penalty_factors.values())

            # 標準化分數 (0-1範圍)
            normalized_score = max(0.0, min(1.0, (total_reward + 10.0) / 20.0))

            rl_reward = RLReward(
                total_reward=total_reward,
                component_rewards=component_rewards,
                penalty_factors=penalty_factors,
                normalized_score=normalized_score
            )

            self.episode_reward += total_reward

            return rl_reward

        except Exception as e:
            self.logger.error(f"獎勵計算失敗: {e}")
            raise

    def _estimate_coverage_area(self, satellite_positions: List[Dict[str, float]]) -> float:
        """估算覆蓋面積"""
        if not satellite_positions:
            return 0.0

        # 簡化的覆蓋面積計算 (基於衛星數量和分布)
        num_satellites = len(satellite_positions)

        # 計算位置分散度
        if num_satellites > 1:
            latitudes = [pos['latitude'] for pos in satellite_positions]
            longitudes = [pos['longitude'] for pos in satellite_positions]

            lat_spread = max(latitudes) - min(latitudes)
            lon_spread = max(longitudes) - min(longitudes)

            # 覆蓋面積 = 基礎覆蓋 × 衛星數量 × 分散度因子
            base_coverage = 1000.0  # km²
            spread_factor = 1.0 + (lat_spread + lon_spread) / 180.0
            coverage_area = base_coverage * num_satellites * spread_factor
        else:
            coverage_area = 1000.0  # 單衛星基礎覆蓋

        return coverage_area

    def reset_environment(self):
        """重置環境狀態"""
        self.current_state = None
        self.step_count = 0
        self.episode_reward = 0.0
        self.logger.info("🔄 RL環境已重置")

    def get_environment_info(self) -> Dict[str, Any]:
        """獲取環境信息"""
        return {
            'state_dimensions': self.state_dimensions,
            'action_space_size': self.action_space_size,
            'reward_weights': self.reward_weights,
            'current_step': self.step_count,
            'episode_reward': self.episode_reward,
            'environment_version': '1.0.0'
        }


class RLExtensionCoordinator:
    """RL擴展協調器 - 管理RL與傳統優化的整合"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.RLExtensionCoordinator")

        # RL配置
        self.rl_enabled = self.config.get('rl_enabled', False)
        self.hybrid_mode = self.config.get('hybrid_mode', True)  # RL + 傳統優化混合
        self.rl_confidence_threshold = self.config.get('rl_confidence_threshold', 0.7)

        # 組件初始化
        self.environment_adapter = RLEnvironmentAdapter(config.get('rl_environment', {}))
        self.rl_agent: Optional[RLAgentInterface] = None

        # 協調統計
        self.coordination_stats = {
            'rl_decisions_used': 0,
            'traditional_decisions_used': 0,
            'hybrid_decisions': 0,
            'total_decisions': 0
        }

        self.logger.info(f"✅ RL擴展協調器初始化完成 (RL啟用: {self.rl_enabled})")

    def register_rl_agent(self, agent: RLAgentInterface):
        """註冊RL代理"""
        self.rl_agent = agent
        self.logger.info("🤖 RL代理已註冊")

    def coordinate_decision_making(self, optimization_data: Dict[str, Any],
                                 traditional_results: Dict[str, Any]) -> Dict[str, Any]:
        """協調RL與傳統優化的決策制定"""
        try:
            if not self.rl_enabled or self.rl_agent is None:
                # 僅使用傳統優化
                self.coordination_stats['traditional_decisions_used'] += 1
                return self._wrap_traditional_decision(traditional_results)

            # 轉換為RL狀態
            rl_state = self.environment_adapter.convert_to_rl_state(optimization_data)

            # 獲取RL決策
            rl_action = self.rl_agent.select_action(rl_state)
            rl_decision = self.environment_adapter.convert_from_rl_action(rl_action)

            if self.hybrid_mode:
                # 混合模式：結合RL和傳統優化
                coordinated_decision = self._coordinate_hybrid_decision(
                    rl_decision, traditional_results, rl_action.confidence
                )
                self.coordination_stats['hybrid_decisions'] += 1
            else:
                # 純RL模式
                if rl_action.confidence >= self.rl_confidence_threshold:
                    coordinated_decision = self._wrap_rl_decision(rl_decision, rl_action)
                    self.coordination_stats['rl_decisions_used'] += 1
                else:
                    # RL信心不足，回退到傳統優化
                    coordinated_decision = self._wrap_traditional_decision(traditional_results)
                    self.coordination_stats['traditional_decisions_used'] += 1

            self.coordination_stats['total_decisions'] += 1

            return coordinated_decision

        except Exception as e:
            self.logger.error(f"決策協調失敗: {e}")
            # 錯誤時回退到傳統優化
            self.coordination_stats['traditional_decisions_used'] += 1
            return self._wrap_traditional_decision(traditional_results)

    def _coordinate_hybrid_decision(self, rl_decision: Dict[str, Any],
                                  traditional_results: Dict[str, Any],
                                  rl_confidence: float) -> Dict[str, Any]:
        """協調混合決策"""
        # 基於信心度加權結合決策
        weight_rl = min(rl_confidence, 0.8)  # RL權重上限80%
        weight_traditional = 1.0 - weight_rl

        hybrid_decision = {
            'decision_source': 'hybrid_rl_traditional',
            'rl_weight': weight_rl,
            'traditional_weight': weight_traditional,
            'rl_decision': rl_decision,
            'traditional_decision': traditional_results,
            'final_selection': self._merge_decisions(rl_decision, traditional_results, weight_rl),
            'coordination_metadata': {
                'rl_confidence': rl_confidence,
                'hybrid_strategy': 'confidence_weighted',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }

        return hybrid_decision

    def _merge_decisions(self, rl_decision: Dict[str, Any],
                        traditional_decision: Dict[str, Any],
                        rl_weight: float) -> Dict[str, Any]:
        """合併RL和傳統決策"""
        # 簡化的決策合併邏輯
        merged = {
            'selected_satellites': self._merge_satellite_selections(
                rl_decision.get('selected_satellites', []),
                traditional_decision.get('optimal_pool', {}).get('selected_satellites', []),
                rl_weight
            ),
            'optimization_confidence': (
                rl_weight * rl_decision.get('confidence_score', 0.5) +
                (1 - rl_weight) * traditional_decision.get('metadata', {}).get('confidence', 0.5)
            ),
            'merge_strategy': 'weighted_combination'
        }

        return merged

    def _merge_satellite_selections(self, rl_satellites: List[str],
                                   traditional_satellites: List[Dict[str, Any]],
                                   rl_weight: float) -> List[str]:
        """合併衛星選擇"""
        # 提取傳統選擇的衛星ID
        trad_satellite_ids = [sat.get('satellite_id', '') for sat in traditional_satellites if 'satellite_id' in sat]

        # 簡單策略：優先選擇RL推薦，補充傳統推薦
        merged_selection = []

        # 添加RL推薦 (按權重比例)
        rl_count = int(len(rl_satellites) * rl_weight)
        merged_selection.extend(rl_satellites[:rl_count])

        # 添加傳統推薦 (避免重複)
        trad_count = max(1, len(trad_satellite_ids) - rl_count)
        for sat_id in trad_satellite_ids:
            if sat_id not in merged_selection and len(merged_selection) < rl_count + trad_count:
                merged_selection.append(sat_id)

        return merged_selection

    def _wrap_rl_decision(self, rl_decision: Dict[str, Any], rl_action: RLAction) -> Dict[str, Any]:
        """包裝RL決策"""
        return {
            'decision_source': 'rl_agent',
            'rl_action': rl_action,
            'decision': rl_decision,
            'metadata': {
                'rl_confidence': rl_action.confidence,
                'action_type': rl_action.action_type,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }

    def _wrap_traditional_decision(self, traditional_results: Dict[str, Any]) -> Dict[str, Any]:
        """包裝傳統優化決策"""
        return {
            'decision_source': 'traditional_optimization',
            'decision': traditional_results,
            'metadata': {
                'fallback_reason': 'rl_disabled_or_low_confidence',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }

    def update_rl_agent(self, state: RLState, action: RLAction, reward: RLReward, next_state: RLState):
        """更新RL代理"""
        if self.rl_agent and self.rl_enabled:
            try:
                self.rl_agent.update_policy(state, action, reward, next_state)
                self.logger.debug("🧠 RL代理策略已更新")
            except Exception as e:
                self.logger.error(f"RL代理更新失敗: {e}")

    def get_coordination_statistics(self) -> Dict[str, Any]:
        """獲取協調統計信息"""
        stats = self.coordination_stats.copy()
        if stats['total_decisions'] > 0:
            stats['rl_usage_rate'] = stats['rl_decisions_used'] / stats['total_decisions']
            stats['hybrid_usage_rate'] = stats['hybrid_decisions'] / stats['total_decisions']
            stats['traditional_usage_rate'] = stats['traditional_decisions_used'] / stats['total_decisions']

        return stats

    def save_rl_model(self, path: str) -> bool:
        """保存RL模型"""
        if self.rl_agent:
            return self.rl_agent.save_model(path)
        return False

    def load_rl_model(self, path: str) -> bool:
        """載入RL模型"""
        if self.rl_agent:
            return self.rl_agent.load_model(path)
        return False


# 示例RL代理實現 (可以被替換為更復雜的實現)
class DummyRLAgent(RLAgentInterface):
    """示例RL代理 - 用於測試和開發"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.DummyRLAgent")
        self.policy_version = "dummy_v1.0"

        self.logger.info("🤖 示例RL代理初始化完成")

    def select_action(self, state: RLState) -> RLAction:
        """簡單的動作選擇策略 (實際應用中應替換為神經網絡)"""
        # 基於信號強度選擇最佳衛星
        if state.signal_strengths:
            max_signal_idx = np.argmax(state.signal_strengths)
            selected_satellites = [f"satellite_{max_signal_idx}"]
            confidence = min(0.9, max(0.3, (max(state.signal_strengths) + 120) / 40))
        else:
            selected_satellites = []
            confidence = 0.1

        action = RLAction(
            action_type="satellite_selection",
            target_satellites=selected_satellites,
            parameters={
                "selection_strategy": "max_signal_strength",
                "policy_version": self.policy_version
            },
            confidence=confidence
        )

        return action

    def update_policy(self, state: RLState, action: RLAction, reward: RLReward, next_state: RLState):
        """示例策略更新 (實際應用中應進行神經網絡訓練)"""
        # 在真實實現中，這裡會更新神經網絡權重
        self.logger.debug(f"策略更新: 獎勵={reward.total_reward:.3f}")

    def save_model(self, path: str) -> bool:
        """保存模型 (示例實現)"""
        self.logger.info(f"示例模型保存到: {path}")
        return True

    def load_model(self, path: str) -> bool:
        """載入模型 (示例實現)"""
        self.logger.info(f"示例模型從以下路徑載入: {path}")
        return True