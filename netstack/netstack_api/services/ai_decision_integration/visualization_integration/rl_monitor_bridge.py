"""
RL 監控橋接器
============

提供與 GymnasiumRLMonitor 的橋接功能。
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .realtime_event_streamer import RealtimeEventStreamer
from ..interfaces.decision_engine import Decision

logger = logging.getLogger(__name__)


class RLMonitorBridge:
    """
    RL 監控橋接器
    
    提供與 GymnasiumRLMonitor 的橋接功能：
    - 訓練進度推送
    - 決策品質評估
    - 算法性能監控
    - 學習曲線更新
    """

    def __init__(self, event_streamer: RealtimeEventStreamer,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化 RL 監控橋接器
        
        Args:
            event_streamer: 事件推送器
            config: 配置參數
        """
        self.event_streamer = event_streamer
        self.config = config or {}
        self.logger = logger.bind(component="rl_monitor_bridge")
        
        # 監控狀態
        self.training_active = False
        self.current_episode = 0
        self.total_episodes = 0
        
        # 算法性能緩存
        self.algorithm_metrics = {}
        self.learning_curves = {}
        
        # 配置參數
        self.update_interval = self.config.get("update_interval", 1.0)
        self.batch_size = self.config.get("batch_size", 10)
        
        self.logger.info("RL 監控橋接器初始化完成")

    async def notify_training_start(self, algorithm: str, config: Dict[str, Any]):
        """
        通知訓練開始
        
        Args:
            algorithm: 算法名稱
            config: 訓練配置
        """
        try:
            self.training_active = True
            self.current_episode = 0
            self.total_episodes = config.get("total_episodes", 1000)
            
            await self.event_streamer.broadcast_event({
                "type": "rl_training_started",
                "algorithm": algorithm,
                "config": config,
                "timestamp": datetime.now().timestamp(),
            })
            
            self.logger.info(
                "RL 訓練開始通知",
                algorithm=algorithm,
                total_episodes=self.total_episodes,
            )
            
        except Exception as e:
            self.logger.error("RL 訓練開始通知失敗", error=str(e))

    async def notify_training_update(self, algorithm: str, metrics: Dict[str, Any]):
        """
        通知 RL 訓練更新
        
        Args:
            algorithm: 算法名稱
            metrics: 訓練指標
        """
        try:
            self.current_episode = metrics.get("episode", self.current_episode)
            
            # 更新算法指標緩存
            if algorithm not in self.algorithm_metrics:
                self.algorithm_metrics[algorithm] = []
            
            self.algorithm_metrics[algorithm].append({
                "episode": self.current_episode,
                "metrics": metrics,
                "timestamp": datetime.now().timestamp(),
            })
            
            # 更新學習曲線
            self._update_learning_curve(algorithm, metrics)
            
            # 推送訓練更新
            await self.event_streamer.broadcast_event({
                "type": "rl_training_update",
                "algorithm": algorithm,
                "episode": self.current_episode,
                "total_episodes": self.total_episodes,
                "progress": self.current_episode / self.total_episodes if self.total_episodes > 0 else 0,
                "metrics": metrics,
                "learning_curve": self.learning_curves.get(algorithm, {}),
                "timestamp": datetime.now().timestamp(),
            })
            
            self.logger.debug(
                "RL 訓練更新通知",
                algorithm=algorithm,
                episode=self.current_episode,
                metrics=list(metrics.keys()),
            )
            
        except Exception as e:
            self.logger.error("RL 訓練更新通知失敗", error=str(e))

    async def notify_training_complete(self, algorithm: str, final_metrics: Dict[str, Any]):
        """
        通知訓練完成
        
        Args:
            algorithm: 算法名稱
            final_metrics: 最終指標
        """
        try:
            self.training_active = False
            
            await self.event_streamer.broadcast_event({
                "type": "rl_training_complete",
                "algorithm": algorithm,
                "final_metrics": final_metrics,
                "total_episodes": self.current_episode,
                "training_duration": final_metrics.get("training_duration", 0),
                "timestamp": datetime.now().timestamp(),
            })
            
            self.logger.info(
                "RL 訓練完成通知",
                algorithm=algorithm,
                total_episodes=self.current_episode,
            )
            
        except Exception as e:
            self.logger.error("RL 訓練完成通知失敗", error=str(e))

    async def notify_decision_quality(self, decision: Decision, performance_score: float):
        """
        通知決策品質評分
        
        Args:
            decision: 決策結果
            performance_score: 性能評分
        """
        try:
            quality_data = {
                "decision_id": decision.selected_satellite,
                "algorithm": decision.algorithm_used,
                "confidence": decision.confidence,
                "performance_score": performance_score,
                "quality_grade": self._calculate_quality_grade(performance_score),
                "reasoning": decision.reasoning,
                "decision_time": decision.decision_time,
            }
            
            await self.event_streamer.broadcast_event({
                "type": "decision_quality_update",
                "quality_data": quality_data,
                "timestamp": datetime.now().timestamp(),
            })
            
            self.logger.debug(
                "決策品質通知",
                decision_id=decision.selected_satellite,
                algorithm=decision.algorithm_used,
                performance_score=performance_score,
            )
            
        except Exception as e:
            self.logger.error("決策品質通知失敗", error=str(e))

    async def notify_algorithm_performance(self, algorithm: str, performance_metrics: Dict[str, Any]):
        """
        通知算法性能
        
        Args:
            algorithm: 算法名稱
            performance_metrics: 性能指標
        """
        try:
            await self.event_streamer.broadcast_event({
                "type": "algorithm_performance_update",
                "algorithm": algorithm,
                "performance_metrics": performance_metrics,
                "benchmark_comparison": self._get_benchmark_comparison(algorithm, performance_metrics),
                "timestamp": datetime.now().timestamp(),
            })
            
            self.logger.debug(
                "算法性能通知",
                algorithm=algorithm,
                metrics=list(performance_metrics.keys()),
            )
            
        except Exception as e:
            self.logger.error("算法性能通知失敗", error=str(e))

    async def notify_model_update(self, algorithm: str, model_info: Dict[str, Any]):
        """
        通知模型更新
        
        Args:
            algorithm: 算法名稱
            model_info: 模型信息
        """
        try:
            await self.event_streamer.broadcast_event({
                "type": "model_update",
                "algorithm": algorithm,
                "model_info": model_info,
                "update_type": model_info.get("update_type", "weights"),
                "timestamp": datetime.now().timestamp(),
            })
            
            self.logger.debug(
                "模型更新通知",
                algorithm=algorithm,
                update_type=model_info.get("update_type"),
            )
            
        except Exception as e:
            self.logger.error("模型更新通知失敗", error=str(e))

    async def notify_hyperparameter_update(self, algorithm: str, hyperparameters: Dict[str, Any]):
        """
        通知超參數更新
        
        Args:
            algorithm: 算法名稱
            hyperparameters: 超參數
        """
        try:
            await self.event_streamer.broadcast_event({
                "type": "hyperparameter_update",
                "algorithm": algorithm,
                "hyperparameters": hyperparameters,
                "update_reason": hyperparameters.get("update_reason", "manual"),
                "timestamp": datetime.now().timestamp(),
            })
            
            self.logger.debug(
                "超參數更新通知",
                algorithm=algorithm,
                params=list(hyperparameters.keys()),
            )
            
        except Exception as e:
            self.logger.error("超參數更新通知失敗", error=str(e))

    async def get_training_status(self) -> Dict[str, Any]:
        """
        獲取訓練狀態
        
        Returns:
            Dict[str, Any]: 訓練狀態
        """
        return {
            "training_active": self.training_active,
            "current_episode": self.current_episode,
            "total_episodes": self.total_episodes,
            "progress": self.current_episode / self.total_episodes if self.total_episodes > 0 else 0,
            "algorithms": list(self.algorithm_metrics.keys()),
            "learning_curves": self.learning_curves,
        }

    async def get_algorithm_metrics(self, algorithm: str) -> Dict[str, Any]:
        """
        獲取算法指標
        
        Args:
            algorithm: 算法名稱
            
        Returns:
            Dict[str, Any]: 算法指標
        """
        return {
            "algorithm": algorithm,
            "metrics_history": self.algorithm_metrics.get(algorithm, []),
            "learning_curve": self.learning_curves.get(algorithm, {}),
            "current_performance": self._get_current_performance(algorithm),
        }

    # 私有方法
    def _update_learning_curve(self, algorithm: str, metrics: Dict[str, Any]):
        """更新學習曲線"""
        if algorithm not in self.learning_curves:
            self.learning_curves[algorithm] = {
                "episodes": [],
                "rewards": [],
                "losses": [],
                "q_values": [],
                "epsilon": [],
            }
        
        curve = self.learning_curves[algorithm]
        episode = self.current_episode
        
        # 添加數據點
        curve["episodes"].append(episode)
        curve["rewards"].append(metrics.get("reward", 0))
        curve["losses"].append(metrics.get("loss", 0))
        curve["q_values"].append(metrics.get("q_value", 0))
        curve["epsilon"].append(metrics.get("epsilon", 0))
        
        # 保持窗口大小
        max_points = 1000
        for key in ["episodes", "rewards", "losses", "q_values", "epsilon"]:
            if len(curve[key]) > max_points:
                curve[key] = curve[key][-max_points:]

    def _calculate_quality_grade(self, performance_score: float) -> str:
        """計算品質等級"""
        if performance_score >= 0.9:
            return "A"
        elif performance_score >= 0.8:
            return "B"
        elif performance_score >= 0.7:
            return "C"
        elif performance_score >= 0.6:
            return "D"
        else:
            return "F"

    def _get_benchmark_comparison(self, algorithm: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """獲取基準對比"""
        # 簡化實現，實際應該與基準數據庫比較
        benchmarks = {
            "DQN": {"avg_reward": 0.75, "avg_loss": 0.05, "convergence_episodes": 800},
            "PPO": {"avg_reward": 0.80, "avg_loss": 0.04, "convergence_episodes": 600},
            "SAC": {"avg_reward": 0.85, "avg_loss": 0.03, "convergence_episodes": 500},
        }
        
        benchmark = benchmarks.get(algorithm, {})
        current_metrics = metrics
        
        comparison = {}
        for metric in ["avg_reward", "avg_loss"]:
            if metric in benchmark and metric in current_metrics:
                benchmark_value = benchmark[metric]
                current_value = current_metrics[metric]
                comparison[metric] = {
                    "benchmark": benchmark_value,
                    "current": current_value,
                    "improvement": (current_value - benchmark_value) / benchmark_value * 100,
                }
        
        return comparison

    def _get_current_performance(self, algorithm: str) -> Dict[str, Any]:
        """獲取當前性能"""
        if algorithm not in self.algorithm_metrics or not self.algorithm_metrics[algorithm]:
            return {}
        
        recent_metrics = self.algorithm_metrics[algorithm][-10:]  # 最近10個數據點
        
        # 計算平均值
        avg_metrics = {}
        for metric_data in recent_metrics:
            metrics = metric_data["metrics"]
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    if key not in avg_metrics:
                        avg_metrics[key] = []
                    avg_metrics[key].append(value)
        
        # 計算平均值
        current_performance = {}
        for key, values in avg_metrics.items():
            if values:
                current_performance[key] = sum(values) / len(values)
        
        return current_performance