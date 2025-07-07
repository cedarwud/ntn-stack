"""
🚀 RL 訓練管線

統一管理強化學習算法的訓練過程，包括環境設置、訓練監控、模型保存等。
"""

import asyncio
import logging
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import yaml

try:
    import gymnasium as gym
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False

from .interfaces import RLHandoverAlgorithm, HandoverContext
from .environment_manager import EnvironmentManager
from .registry import AlgorithmRegistry

logger = logging.getLogger(__name__)


class TrainingMetrics:
    """訓練指標收集器"""
    
    def __init__(self):
        self.episode_rewards = []
        self.episode_lengths = []
        self.training_losses = []
        self.success_rates = []
        self.handover_counts = []
        self.start_time = None
        self.end_time = None
    
    def add_episode(self, reward: float, length: int, success: bool, handover_count: int):
        """添加一個 episode 的指標"""
        self.episode_rewards.append(reward)
        self.episode_lengths.append(length)
        self.success_rates.append(1.0 if success else 0.0)
        self.handover_counts.append(handover_count)
    
    def add_training_loss(self, loss: Dict[str, float]):
        """添加訓練損失"""
        self.training_losses.append(loss)
    
    def get_recent_stats(self, window: int = 100) -> Dict[str, float]:
        """獲取最近的統計數據"""
        if not self.episode_rewards:
            return {}
        
        recent_rewards = self.episode_rewards[-window:]
        recent_lengths = self.episode_lengths[-window:]
        recent_success = self.success_rates[-window:]
        recent_handovers = self.handover_counts[-window:]
        
        return {
            'mean_reward': np.mean(recent_rewards),
            'std_reward': np.std(recent_rewards),
            'mean_length': np.mean(recent_lengths),
            'success_rate': np.mean(recent_success),
            'mean_handovers': np.mean(recent_handovers),
            'total_episodes': len(self.episode_rewards)
        }


class RLTrainingPipeline:
    """RL 訓練管線
    
    負責管理 RL 算法的完整訓練流程，包括：
    - 環境初始化和配置
    - 訓練循環和監控
    - 模型保存和載入
    - 性能評估和分析
    """
    
    def __init__(self, config_path: str = "algorithm_ecosystem_config.yml"):
        """初始化訓練管線
        
        Args:
            config_path: 配置文件路徑
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化組件
        self.environment_manager = EnvironmentManager(self.config.get('environment', {}))
        self.algorithm_registry = AlgorithmRegistry()
        
        # 訓練狀態
        self.is_training = False
        self.current_algorithm = None
        self.current_env = None
        self.training_metrics = TrainingMetrics()
        
        # 模型保存路徑
        self.model_save_dir = Path("models")
        self.model_save_dir.mkdir(exist_ok=True)
        
        logger.info("RL 訓練管線初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"載入配置文件失敗: {e}")
            return {}
    
    async def setup_algorithm(self, algorithm_name: str) -> bool:
        """設置訓練算法
        
        Args:
            algorithm_name: 算法名稱
            
        Returns:
            bool: 設置是否成功
        """
        try:
            # 從註冊中心獲取算法
            algorithm = await self.algorithm_registry.get_algorithm(algorithm_name)
            if not algorithm or not isinstance(algorithm, RLHandoverAlgorithm):
                logger.error(f"算法 '{algorithm_name}' 不是有效的 RL 算法")
                return False
            
            self.current_algorithm = algorithm
            logger.info(f"算法 '{algorithm_name}' 設置完成")
            return True
            
        except Exception as e:
            logger.error(f"設置算法失敗: {e}")
            return False
    
    async def setup_environment(self, env_config: Optional[Dict[str, Any]] = None) -> bool:
        """設置訓練環境
        
        Args:
            env_config: 環境配置（可選）
            
        Returns:
            bool: 設置是否成功
        """
        try:
            if not GYMNASIUM_AVAILABLE:
                logger.error("Gymnasium 不可用，無法創建訓練環境")
                return False
            
            env_config = env_config or self.config.get('environment', {})
            env_id = env_config.get('gymnasium', {}).get('env_name', 'LEOSatelliteHandoverEnv-v1')
            
            self.current_env = await self.environment_manager.create_environment(env_id, env_config)
            if self.current_env is None:
                logger.error("環境創建失敗")
                return False
            
            logger.info(f"訓練環境 '{env_id}' 設置完成")
            return True
            
        except Exception as e:
            logger.error(f"設置環境失敗: {e}")
            return False
    
    async def train_algorithm(self, algorithm_name: str, episodes: int = 1000, 
                            save_interval: int = 100, eval_interval: int = 50) -> Dict[str, Any]:
        """訓練算法
        
        Args:
            algorithm_name: 算法名稱
            episodes: 訓練回合數
            save_interval: 模型保存間隔
            eval_interval: 評估間隔
            
        Returns:
            Dict[str, Any]: 訓練結果
        """
        if self.is_training:
            logger.warning("訓練已在進行中")
            return {'status': 'already_training'}
        
        try:
            self.is_training = True
            self.training_metrics = TrainingMetrics()
            self.training_metrics.start_time = datetime.now()
            
            # 設置算法和環境
            if not await self.setup_algorithm(algorithm_name):
                return {'status': 'algorithm_setup_failed'}
            
            if not await self.setup_environment():
                return {'status': 'environment_setup_failed'}
            
            logger.info(f"開始訓練算法 '{algorithm_name}'，計劃 {episodes} 回合")
            
            best_reward = -float('inf')
            
            for episode in range(episodes):
                try:
                    # 執行一個訓練回合
                    episode_result = await self._run_training_episode()
                    
                    # 記錄指標
                    self.training_metrics.add_episode(
                        episode_result['reward'],
                        episode_result['length'],
                        episode_result['success'],
                        episode_result['handover_count']
                    )
                    
                    # 執行訓練步驟
                    if hasattr(self.current_algorithm, 'train_step'):
                        training_loss = await self.current_algorithm.train_step()
                        self.training_metrics.add_training_loss(training_loss)
                    
                    # 記錄最佳性能
                    if episode_result['reward'] > best_reward:
                        best_reward = episode_result['reward']
                        # 保存最佳模型
                        await self._save_best_model(algorithm_name, episode, best_reward)
                    
                    # 定期保存模型
                    if (episode + 1) % save_interval == 0:
                        await self._save_checkpoint(algorithm_name, episode)
                    
                    # 定期評估
                    if (episode + 1) % eval_interval == 0:
                        eval_results = await self._evaluate_algorithm()
                        logger.info(f"Episode {episode + 1} 評估結果: {eval_results}")
                    
                    # 記錄進度
                    if (episode + 1) % 10 == 0:
                        stats = self.training_metrics.get_recent_stats()
                        logger.info(f"Episode {episode + 1}/{episodes}: {stats}")
                
                except Exception as e:
                    logger.error(f"Episode {episode} 訓練失敗: {e}")
                    continue
            
            self.training_metrics.end_time = datetime.now()
            training_duration = (self.training_metrics.end_time - self.training_metrics.start_time).total_seconds()
            
            # 最終保存
            await self._save_final_model(algorithm_name, episodes)
            
            final_stats = self.training_metrics.get_recent_stats()
            logger.info(f"訓練完成！最終統計: {final_stats}")
            
            return {
                'status': 'completed',
                'episodes': episodes,
                'duration_seconds': training_duration,
                'best_reward': best_reward,
                'final_stats': final_stats,
                'model_saved': True
            }
            
        except Exception as e:
            logger.error(f"訓練過程失敗: {e}")
            return {'status': 'training_failed', 'error': str(e)}
        
        finally:
            self.is_training = False
    
    async def _run_training_episode(self) -> Dict[str, Any]:
        """執行一個訓練回合"""
        observation, _ = self.current_env.reset()
        total_reward = 0.0
        step_count = 0
        handover_count = 0
        done = False
        
        while not done:
            # 將觀察轉換為 HandoverContext
            context = self._observation_to_context(observation)
            
            # 獲取算法決策
            decision = await self.current_algorithm.predict_handover(context)
            
            # 將決策轉換為環境動作
            action = self._decision_to_action(decision)
            
            # 執行動作
            next_observation, reward, terminated, truncated, info = self.current_env.step(action)
            done = terminated or truncated
            
            # 統計換手次數
            if hasattr(decision, 'handover_decision') and decision.handover_decision.name != 'NO_HANDOVER':
                handover_count += 1
            
            # 存儲經驗 (如果算法支持)
            if hasattr(self.current_algorithm, 'store_experience'):
                try:
                    import torch
                    self.current_algorithm.store_experience(
                        torch.tensor(observation, dtype=torch.float32),
                        action,
                        reward,
                        torch.tensor(next_observation, dtype=torch.float32),
                        done
                    )
                except ImportError:
                    # 如果 PyTorch 不可用，跳過經驗存儲
                    pass
            
            total_reward += reward
            step_count += 1
            observation = next_observation
        
        success = info.get('success', total_reward > 0)
        
        return {
            'reward': total_reward,
            'length': step_count,
            'success': success,
            'handover_count': handover_count
        }
    
    def _observation_to_context(self, observation: np.ndarray) -> HandoverContext:
        """將環境觀察轉換為 HandoverContext"""
        # 這裡需要根據具體的環境實現
        # 暫時創建一個簡化的上下文
        from .interfaces import GeoCoordinate, SignalMetrics, SatelliteInfo
        
        return HandoverContext(
            ue_id="training_ue",
            ue_location=GeoCoordinate(latitude=0.0, longitude=0.0),
            current_satellite="satellite_1",
            current_signal_metrics=SignalMetrics(rsrp=-80.0, rsrq=-10.0, sinr=15.0, throughput=100.0, latency=50.0),
            candidate_satellites=[],
            timestamp=datetime.now()
        )
    
    def _decision_to_action(self, decision) -> int:
        """將 HandoverDecision 轉換為環境動作"""
        # 簡化的決策到動作映射
        if hasattr(decision, 'handover_decision'):
            if decision.handover_decision.name == 'NO_HANDOVER':
                return 0
            elif decision.handover_decision.name == 'IMMEDIATE_HANDOVER':
                return 1
            elif decision.handover_decision.name == 'PREPARE_HANDOVER':
                return 2
        return 0
    
    async def _evaluate_algorithm(self, eval_episodes: int = 10) -> Dict[str, float]:
        """評估算法性能"""
        eval_rewards = []
        eval_success = []
        
        for _ in range(eval_episodes):
            try:
                result = await self._run_training_episode()
                eval_rewards.append(result['reward'])
                eval_success.append(result['success'])
            except Exception as e:
                logger.warning(f"評估回合失敗: {e}")
                continue
        
        if eval_rewards:
            return {
                'mean_reward': np.mean(eval_rewards),
                'std_reward': np.std(eval_rewards),
                'success_rate': np.mean(eval_success),
                'episodes_evaluated': len(eval_rewards)
            }
        
        return {'mean_reward': 0.0, 'std_reward': 0.0, 'success_rate': 0.0, 'episodes_evaluated': 0}
    
    async def _save_checkpoint(self, algorithm_name: str, episode: int):
        """保存訓練檢查點"""
        try:
            checkpoint_path = self.model_save_dir / f"{algorithm_name}_checkpoint_ep{episode}.pth"
            await self.current_algorithm.save_model(str(checkpoint_path))
            logger.info(f"檢查點已保存: {checkpoint_path}")
        except Exception as e:
            logger.error(f"保存檢查點失敗: {e}")
    
    async def _save_best_model(self, algorithm_name: str, episode: int, reward: float):
        """保存最佳模型"""
        try:
            best_model_path = self.model_save_dir / f"{algorithm_name}_best.pth"
            await self.current_algorithm.save_model(str(best_model_path))
            logger.info(f"最佳模型已保存: {best_model_path} (Episode {episode}, Reward: {reward:.2f})")
        except Exception as e:
            logger.error(f"保存最佳模型失敗: {e}")
    
    async def _save_final_model(self, algorithm_name: str, episodes: int):
        """保存最終模型"""
        try:
            final_model_path = self.model_save_dir / f"{algorithm_name}_final_ep{episodes}.pth"
            await self.current_algorithm.save_model(str(final_model_path))
            logger.info(f"最終模型已保存: {final_model_path}")
        except Exception as e:
            logger.error(f"保存最終模型失敗: {e}")
    
    def get_training_status(self) -> Dict[str, Any]:
        """獲取當前訓練狀態"""
        stats = self.training_metrics.get_recent_stats()
        
        return {
            'is_training': self.is_training,
            'current_algorithm': self.current_algorithm.name if self.current_algorithm else None,
            'training_metrics': stats,
            'start_time': self.training_metrics.start_time.isoformat() if self.training_metrics.start_time else None,
            'total_episodes': len(self.training_metrics.episode_rewards)
        }
    
    async def stop_training(self):
        """停止訓練"""
        if self.is_training:
            self.is_training = False
            logger.info("訓練已停止")
        else:
            logger.warning("沒有正在進行的訓練")
    
    def cleanup(self):
        """清理資源"""
        if self.current_env:
            self.current_env.close()
            self.current_env = None
        
        self.current_algorithm = None
        logger.info("訓練管線資源已清理")