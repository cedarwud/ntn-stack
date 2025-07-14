"""
實時決策服務 - Phase 2.3 核心組件

提供毫秒級實時決策能力，支援：
- 多算法實時推理
- 狀態預處理和後處理
- 決策解釋和信心度評估
- 性能監控和優化
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
from enum import Enum

from ..algorithms.dqn_algorithm import DQNAlgorithm
from ..algorithms.ppo_algorithm import PPOAlgorithm
from ..algorithms.sac_algorithm import SACAlgorithm
from ..environments.leo_satellite_environment import LEOSatelliteEnvironment
from ..implementations.simplified_postgresql_repository import SimplifiedPostgreSQLRepository

logger = logging.getLogger(__name__)

class DecisionMode(Enum):
    """決策模式"""
    GREEDY = "greedy"           # 貪婪策略
    EPSILON_GREEDY = "epsilon_greedy"  # ε-貪婪策略
    STOCHASTIC = "stochastic"   # 隨機策略
    BEST_ACTION = "best_action" # 最佳動作

class RealTimeDecisionService:
    """
    實時決策服務
    
    提供毫秒級實時決策能力，支援多種強化學習算法
    和決策模式，並提供詳細的決策解釋和性能監控。
    """
    
    def __init__(self, repository: Optional[SimplifiedPostgreSQLRepository] = None):
        self.repository = repository or SimplifiedPostgreSQLRepository()
        self.logger = logging.getLogger(__name__)
        
        # 算法實例緩存
        self.algorithm_cache: Dict[str, Any] = {}
        
        # 性能監控
        self.performance_metrics = {
            "total_decisions": 0,
            "avg_decision_time_ms": 0.0,
            "algorithm_usage": {},
            "decision_mode_usage": {},
            "last_reset": datetime.now()
        }
        
        # 決策歷史（用於分析）
        self.decision_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # 算法配置
        self.algorithm_configs = {
            "dqn": {
                "class": DQNAlgorithm,
                "default_params": {
                    "lr": 0.001,
                    "gamma": 0.99,
                    "epsilon": 0.1,
                    "batch_size": 32,
                    "memory_size": 10000
                }
            },
            "ppo": {
                "class": PPOAlgorithm,
                "default_params": {
                    "lr": 0.0003,
                    "gamma": 0.99,
                    "clip_ratio": 0.2,
                    "epochs": 10,
                    "batch_size": 64
                }
            },
            "sac": {
                "class": SACAlgorithm,
                "default_params": {
                    "lr": 0.0003,
                    "gamma": 0.99,
                    "alpha": 0.2,
                    "tau": 0.005,
                    "batch_size": 256
                }
            }
        }
        
        logger.info("實時決策服務初始化完成")
    
    async def make_decision(
        self,
        algorithm: str,
        current_state: Dict[str, Any],
        scenario_context: Optional[Dict[str, Any]] = None,
        decision_mode: DecisionMode = DecisionMode.BEST_ACTION,
        model_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        執行實時決策
        
        Args:
            algorithm: 使用的算法名稱 (dqn, ppo, sac)
            current_state: 當前狀態字典
            scenario_context: 場景上下文信息
            decision_mode: 決策模式
            model_path: 模型路徑（可選）
            
        Returns:
            決策結果字典，包含動作、信心度、執行時間等
        """
        start_time = time.time()
        
        try:
            # 驗證算法
            if algorithm not in self.algorithm_configs:
                raise ValueError(f"不支援的算法: {algorithm}")
            
            # 獲取或創建算法實例
            algorithm_instance = await self._get_algorithm_instance(algorithm, model_path)
            
            # 預處理狀態
            processed_state = await self._preprocess_state(current_state, scenario_context)
            
            # 執行決策
            decision_result = await self._execute_decision(
                algorithm_instance,
                processed_state,
                decision_mode,
                algorithm
            )
            
            # 後處理決策
            final_decision = await self._postprocess_decision(
                decision_result,
                current_state,
                scenario_context,
                algorithm
            )
            
            # 記錄性能指標
            execution_time = (time.time() - start_time) * 1000  # 毫秒
            await self._record_performance_metrics(algorithm, decision_mode, execution_time)
            
            # 添加到決策歷史
            self._add_to_history(final_decision, current_state, algorithm, execution_time)
            
            return final_decision
            
        except Exception as e:
            logger.error(f"實時決策執行失敗: {e}")
            # 返回安全的默認決策
            return await self._get_fallback_decision(current_state, str(e))
    
    async def _get_algorithm_instance(self, algorithm: str, model_path: Optional[str] = None):
        """獲取算法實例"""
        cache_key = f"{algorithm}:{model_path or 'default'}"
        
        if cache_key in self.algorithm_cache:
            return self.algorithm_cache[cache_key]
        
        # 創建新的算法實例
        config = self.algorithm_configs[algorithm]
        algorithm_class = config["class"]
        
        # 獲取環境配置
        env_config = {
            "simworld_url": "http://localhost:8888",
            "max_satellites": 6,
            "scenario": "realtime_decision",
            "fallback_enabled": True
        }
        environment = LEOSatelliteEnvironment(env_config)
        
        # 創建算法實例
        algorithm_instance = algorithm_class(
            environment=environment,
            **config["default_params"]
        )
        
        # 加載模型（如果指定）
        if model_path:
            await algorithm_instance.load_model(model_path)
        else:
            # 嘗試加載最新的訓練模型
            await self._load_latest_model(algorithm_instance, algorithm)
        
        # 緩存算法實例
        self.algorithm_cache[cache_key] = algorithm_instance
        
        return algorithm_instance
    
    async def _preprocess_state(
        self,
        current_state: Dict[str, Any],
        scenario_context: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """預處理狀態數據"""
        try:
            # 提取關鍵狀態信息
            state_features = []
            
            # 衛星位置信息
            if "satellite_positions" in current_state:
                positions = current_state["satellite_positions"]
                if isinstance(positions, list):
                    # 標準化位置向量
                    position_vector = np.array(positions[:6])  # 取前6個衛星
                    state_features.extend(position_vector.flatten())
            
            # 信號強度
            if "signal_strength" in current_state:
                signal_strength = current_state["signal_strength"]
                if isinstance(signal_strength, (int, float)):
                    state_features.append(signal_strength)
                elif isinstance(signal_strength, list):
                    state_features.extend(signal_strength[:6])
            
            # 用戶位置
            if "user_position" in current_state:
                user_pos = current_state["user_position"]
                if isinstance(user_pos, (list, tuple)) and len(user_pos) >= 2:
                    state_features.extend(user_pos[:2])
            
            # 網絡負載
            if "network_load" in current_state:
                load = current_state["network_load"]
                if isinstance(load, (int, float)):
                    state_features.append(load)
            
            # 時間信息
            if "timestamp" in current_state:
                timestamp = current_state["timestamp"]
                # 轉換為相對時間特徵
                if isinstance(timestamp, (int, float)):
                    hour_feature = (timestamp % 86400) / 86400  # 一天內的時間比例
                    state_features.append(hour_feature)
            
            # 確保特徵向量有固定長度
            if len(state_features) < 20:
                state_features.extend([0.0] * (20 - len(state_features)))
            elif len(state_features) > 20:
                state_features = state_features[:20]
            
            return np.array(state_features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"狀態預處理失敗: {e}")
            # 返回默認狀態向量
            return np.zeros(20, dtype=np.float32)
    
    async def _execute_decision(
        self,
        algorithm_instance: Any,
        processed_state: np.ndarray,
        decision_mode: DecisionMode,
        algorithm: str
    ) -> Dict[str, Any]:
        """執行決策邏輯"""
        try:
            if algorithm == "dqn":
                return await self._execute_dqn_decision(
                    algorithm_instance, processed_state, decision_mode
                )
            elif algorithm == "ppo":
                return await self._execute_ppo_decision(
                    algorithm_instance, processed_state, decision_mode
                )
            elif algorithm == "sac":
                return await self._execute_sac_decision(
                    algorithm_instance, processed_state, decision_mode
                )
            else:
                raise ValueError(f"不支援的算法: {algorithm}")
                
        except Exception as e:
            logger.error(f"決策執行失敗: {e}")
            # 返回隨機決策
            return {
                "action": np.random.randint(0, 6),  # 6個可能的衛星
                "confidence": 0.1,
                "method": "random_fallback",
                "error": str(e)
            }
    
    async def _execute_dqn_decision(
        self,
        dqn_instance: DQNAlgorithm,
        state: np.ndarray,
        decision_mode: DecisionMode
    ) -> Dict[str, Any]:
        """執行 DQN 決策"""
        try:
            # 獲取 Q 值
            q_values = dqn_instance.get_q_values(state)
            
            if decision_mode == DecisionMode.BEST_ACTION:
                action = np.argmax(q_values)
                confidence = float(np.max(q_values)) / (np.sum(np.abs(q_values)) + 1e-8)
            elif decision_mode == DecisionMode.EPSILON_GREEDY:
                epsilon = getattr(dqn_instance, 'epsilon', 0.1)
                if np.random.random() < epsilon:
                    action = np.random.randint(0, len(q_values))
                    confidence = 1.0 / len(q_values)
                else:
                    action = np.argmax(q_values)
                    confidence = float(np.max(q_values)) / (np.sum(np.abs(q_values)) + 1e-8)
            elif decision_mode == DecisionMode.STOCHASTIC:
                # 使用softmax選擇動作
                probs = np.exp(q_values) / np.sum(np.exp(q_values))
                action = np.random.choice(len(q_values), p=probs)
                confidence = float(probs[action])
            else:
                action = np.argmax(q_values)
                confidence = float(np.max(q_values)) / (np.sum(np.abs(q_values)) + 1e-8)
            
            return {
                "action": int(action),
                "confidence": confidence,
                "q_values": q_values.tolist(),
                "method": decision_mode.value
            }
            
        except Exception as e:
            logger.error(f"DQN 決策執行失敗: {e}")
            return {
                "action": 0,
                "confidence": 0.1,
                "method": "dqn_fallback",
                "error": str(e)
            }
    
    async def _execute_ppo_decision(
        self,
        ppo_instance: PPOAlgorithm,
        state: np.ndarray,
        decision_mode: DecisionMode
    ) -> Dict[str, Any]:
        """執行 PPO 決策"""
        try:
            # 獲取動作分佈
            action_probs = ppo_instance.get_action_probabilities(state)
            
            if decision_mode == DecisionMode.BEST_ACTION:
                action = np.argmax(action_probs)
                confidence = float(np.max(action_probs))
            elif decision_mode == DecisionMode.STOCHASTIC:
                action = np.random.choice(len(action_probs), p=action_probs)
                confidence = float(action_probs[action])
            else:
                action = np.argmax(action_probs)
                confidence = float(np.max(action_probs))
            
            return {
                "action": int(action),
                "confidence": confidence,
                "action_probs": action_probs.tolist(),
                "method": decision_mode.value
            }
            
        except Exception as e:
            logger.error(f"PPO 決策執行失敗: {e}")
            return {
                "action": 0,
                "confidence": 0.1,
                "method": "ppo_fallback",
                "error": str(e)
            }
    
    async def _execute_sac_decision(
        self,
        sac_instance: SACAlgorithm,
        state: np.ndarray,
        decision_mode: DecisionMode
    ) -> Dict[str, Any]:
        """執行 SAC 決策"""
        try:
            # 獲取動作和值函數
            action, action_log_prob = sac_instance.get_action_and_log_prob(state)
            q_values = sac_instance.get_q_values(state, action)
            
            # 轉換為離散動作（如果需要）
            if len(action.shape) > 0:
                discrete_action = np.argmax(action)
            else:
                discrete_action = int(action)
            
            confidence = float(1.0 / (1.0 + np.exp(-action_log_prob)))
            
            return {
                "action": discrete_action,
                "confidence": confidence,
                "q_values": q_values.tolist() if hasattr(q_values, 'tolist') else [float(q_values)],
                "action_log_prob": float(action_log_prob),
                "method": decision_mode.value
            }
            
        except Exception as e:
            logger.error(f"SAC 決策執行失敗: {e}")
            return {
                "action": 0,
                "confidence": 0.1,
                "method": "sac_fallback",
                "error": str(e)
            }
    
    async def _postprocess_decision(
        self,
        decision_result: Dict[str, Any],
        original_state: Dict[str, Any],
        scenario_context: Optional[Dict[str, Any]],
        algorithm: str
    ) -> Dict[str, Any]:
        """後處理決策結果"""
        try:
            # 添加時間戳
            decision_result["timestamp"] = datetime.now()
            decision_result["algorithm"] = algorithm
            
            # 添加決策解釋
            explanation = await self._generate_decision_explanation(
                decision_result, original_state, scenario_context
            )
            decision_result["explanation"] = explanation
            
            # 驗證決策的有效性
            if not self._validate_decision(decision_result, original_state):
                logger.warning("決策驗證失敗，使用安全默認值")
                decision_result["action"] = 0
                decision_result["confidence"] = 0.1
                decision_result["validation_failed"] = True
            
            return decision_result
            
        except Exception as e:
            logger.error(f"決策後處理失敗: {e}")
            decision_result["postprocess_error"] = str(e)
            return decision_result
    
    async def _generate_decision_explanation(
        self,
        decision_result: Dict[str, Any],
        original_state: Dict[str, Any],
        scenario_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成決策解釋"""
        try:
            explanation = {
                "chosen_action": decision_result.get("action", 0),
                "confidence_level": decision_result.get("confidence", 0.0),
                "decision_factors": [],
                "alternative_actions": []
            }
            
            # 分析決策因素
            if "signal_strength" in original_state:
                explanation["decision_factors"].append({
                    "factor": "信號強度",
                    "value": original_state["signal_strength"],
                    "influence": "high" if original_state["signal_strength"] > 0.7 else "medium"
                })
            
            if "network_load" in original_state:
                explanation["decision_factors"].append({
                    "factor": "網絡負載",
                    "value": original_state["network_load"],
                    "influence": "high" if original_state["network_load"] > 0.8 else "low"
                })
            
            # 分析替代方案
            if "q_values" in decision_result:
                q_values = decision_result["q_values"]
                sorted_actions = np.argsort(q_values)[::-1]
                for i, action in enumerate(sorted_actions[:3]):
                    explanation["alternative_actions"].append({
                        "action": int(action),
                        "score": float(q_values[action]),
                        "rank": i + 1
                    })
            
            return explanation
            
        except Exception as e:
            logger.error(f"決策解釋生成失敗: {e}")
            return {"error": str(e)}
    
    def _validate_decision(self, decision_result: Dict[str, Any], original_state: Dict[str, Any]) -> bool:
        """驗證決策的有效性"""
        try:
            action = decision_result.get("action")
            confidence = decision_result.get("confidence", 0.0)
            
            # 基本驗證
            if action is None or not isinstance(action, int):
                return False
            
            if action < 0 or action >= 6:  # 假設有6個可能的動作
                return False
            
            if confidence < 0 or confidence > 1:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def _load_latest_model(self, algorithm_instance: Any, algorithm: str):
        """加載最新的訓練模型"""
        try:
            # 從數據庫獲取最新的模型路徑
            latest_session = await self.repository.get_latest_training_session(algorithm)
            if latest_session and latest_session.get("model_path"):
                await algorithm_instance.load_model(latest_session["model_path"])
                logger.info(f"為 {algorithm} 加載最新模型: {latest_session['model_path']}")
            else:
                logger.warning(f"未找到 {algorithm} 的訓練模型，使用隨機初始化")
                
        except Exception as e:
            logger.error(f"加載最新模型失敗: {e}")
    
    async def _get_fallback_decision(self, current_state: Dict[str, Any], error: str) -> Dict[str, Any]:
        """獲取安全的後備決策"""
        # 基於啟發式規則的安全決策
        fallback_action = 0
        
        # 如果有信號強度信息，選擇信號最強的衛星
        if "signal_strength" in current_state:
            signal_strength = current_state["signal_strength"]
            if isinstance(signal_strength, list):
                fallback_action = np.argmax(signal_strength)
        
        return {
            "action": fallback_action,
            "confidence": 0.1,
            "method": "fallback_heuristic",
            "error": error,
            "timestamp": datetime.now(),
            "explanation": {
                "chosen_action": fallback_action,
                "confidence_level": 0.1,
                "decision_factors": [{"factor": "安全後備", "influence": "high"}],
                "alternative_actions": []
            }
        }
    
    async def _record_performance_metrics(self, algorithm: str, decision_mode: DecisionMode, execution_time: float):
        """記錄性能指標"""
        try:
            self.performance_metrics["total_decisions"] += 1
            
            # 更新平均決策時間
            total_decisions = self.performance_metrics["total_decisions"]
            current_avg = self.performance_metrics["avg_decision_time_ms"]
            self.performance_metrics["avg_decision_time_ms"] = (
                (current_avg * (total_decisions - 1) + execution_time) / total_decisions
            )
            
            # 更新算法使用統計
            if algorithm not in self.performance_metrics["algorithm_usage"]:
                self.performance_metrics["algorithm_usage"][algorithm] = 0
            self.performance_metrics["algorithm_usage"][algorithm] += 1
            
            # 更新決策模式使用統計
            mode_str = decision_mode.value
            if mode_str not in self.performance_metrics["decision_mode_usage"]:
                self.performance_metrics["decision_mode_usage"][mode_str] = 0
            self.performance_metrics["decision_mode_usage"][mode_str] += 1
            
        except Exception as e:
            logger.error(f"記錄性能指標失敗: {e}")
    
    def _add_to_history(self, decision: Dict[str, Any], state: Dict[str, Any], algorithm: str, execution_time: float):
        """添加決策到歷史記錄"""
        try:
            history_entry = {
                "timestamp": datetime.now(),
                "algorithm": algorithm,
                "decision": decision,
                "state_keys": list(state.keys()),
                "execution_time_ms": execution_time
            }
            
            self.decision_history.append(history_entry)
            
            # 限制歷史記錄大小
            if len(self.decision_history) > self.max_history_size:
                self.decision_history = self.decision_history[-self.max_history_size:]
                
        except Exception as e:
            logger.error(f"添加決策歷史失敗: {e}")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return {
            **self.performance_metrics,
            "algorithm_cache_size": len(self.algorithm_cache),
            "decision_history_size": len(self.decision_history),
            "uptime": (datetime.now() - self.performance_metrics["last_reset"]).total_seconds()
        }
    
    async def get_decision_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """獲取決策歷史"""
        return self.decision_history[-limit:]
    
    async def clear_cache(self):
        """清除算法緩存"""
        self.algorithm_cache.clear()
        logger.info("算法緩存已清除")
    
    async def reset_metrics(self):
        """重置性能指標"""
        self.performance_metrics = {
            "total_decisions": 0,
            "avg_decision_time_ms": 0.0,
            "algorithm_usage": {},
            "decision_mode_usage": {},
            "last_reset": datetime.now()
        }
        self.decision_history.clear()
        logger.info("性能指標已重置")