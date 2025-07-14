"""
訓練編排器 - 管理多算法並行訓練

負責協調和管理多個 RL 算法的並行訓練過程，包括：
- 訓練會話創建和管理
- 並行訓練任務調度
- 資源分配和監控
- 訓練進度追蹤
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..implementations.simplified_postgresql_repository import SimplifiedPostgreSQLRepository
from .algorithm_integrator import RLAlgorithmIntegrator
from ..environments.leo_satellite_environment import LEOSatelliteEnvironment
from ...simworld_tle_bridge_service import SimWorldTLEBridgeService

logger = logging.getLogger(__name__)

@dataclass
class TrainingSession:
    """訓練會話數據類"""
    session_id: int
    algorithm: str
    experiment_name: str
    total_episodes: int
    current_episode: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    performance_metrics: Dict[str, Any]

class TrainingOrchestrator:
    """訓練編排器"""
    
    def __init__(self):
        self.repository = SimplifiedPostgreSQLRepository()
        self.algorithm_integrator = RLAlgorithmIntegrator()
        self.active_sessions: Dict[int, TrainingSession] = {}
        self.training_tasks: Dict[int, asyncio.Task] = {}
        
        # 初始化環境
        self.tle_bridge = SimWorldTLEBridgeService()
        self.leo_env = LEOSatelliteEnvironment({
            "simworld_url": "http://localhost:8888",
            "max_satellites": 6,
            "scenario": "urban",
            "fallback_enabled": True,
        })
        
    async def create_training_session(
        self,
        algorithm: str,
        experiment_name: str,
        total_episodes: int,
        scenario_type: str = "urban",
        researcher_id: str = "system",
        research_notes: Optional[str] = None
    ) -> int:
        """創建新的訓練會話"""
        try:
            # 創建實驗會話記錄
            session_data = {
                "experiment_name": experiment_name,
                "algorithm_type": algorithm,
                "scenario_type": scenario_type,
                "total_episodes": total_episodes,
                "session_status": "created",
                "hyperparameters": {"learning_rate": 0.001, "batch_size": 32},
                "research_notes": research_notes,
                "researcher_id": researcher_id,
                "environment_config": {"environment": "LEO-Satellite-v1"},
                "paper_reference": "Phase 2.3 RL Algorithm Implementation",
                "config_hash": f"{algorithm}_{scenario_type}_{total_episodes}"
            }
            
            session_id = await self.repository.create_experiment_session(session_data)
            
            # 創建內部會話追蹤
            session = TrainingSession(
                session_id=session_id,
                algorithm=algorithm,
                experiment_name=experiment_name,
                total_episodes=total_episodes,
                current_episode=0,
                status="created",
                start_time=datetime.now(),
                end_time=None,
                performance_metrics={}
            )
            
            self.active_sessions[session_id] = session
            
            logger.info(f"創建訓練會話: {session_id} ({algorithm})")
            return session_id
            
        except Exception as e:
            logger.error(f"創建訓練會話失敗: {e}")
            raise
    
    async def run_training_session(
        self,
        session_id: int,
        algorithm: str,
        enable_streaming: bool = True
    ) -> Dict[str, Any]:
        """運行單個訓練會話"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"會話 {session_id} 不存在")
            
            session = self.active_sessions[session_id]
            session.status = "running"
            
            # 更新數據庫狀態
            await self.repository.update_experiment_session_status(session_id, "running")
            
            logger.info(f"開始訓練會話: {session_id} ({algorithm})")
            
            # 獲取算法實例
            algorithm_instance = await self.algorithm_integrator.get_algorithm(algorithm)
            if not algorithm_instance:
                raise ValueError(f"算法 {algorithm} 不可用")
            
            # 模擬訓練過程
            results = []
            for episode in range(session.total_episodes):
                session.current_episode = episode + 1
                
                # 模擬訓練一個回合
                episode_result = await self._simulate_training_episode(
                    algorithm_instance, episode, session
                )
                results.append(episode_result)
                
                # 更新性能指標
                session.performance_metrics.update({
                    "episodes_completed": session.current_episode,
                    "average_reward": sum(r["reward"] for r in results) / len(results),
                    "success_rate": sum(1 for r in results if r["success"]) / len(results),
                    "last_episode_reward": episode_result["reward"]
                })
                
                # 模擬訓練延遲
                await asyncio.sleep(0.1)  # 100ms per episode
                
                # 每10回合記錄一次進度
                if episode % 10 == 0 or episode == session.total_episodes - 1:
                    await self._log_training_progress(session, episode_result)
            
            # 完成訓練
            session.status = "completed"
            session.end_time = datetime.now()
            
            # 更新數據庫
            await self.repository.update_experiment_session_status(session_id, "completed")
            await self.repository.update_experiment_session_end_time(session_id, session.end_time)
            
            # 計算最終統計
            final_stats = {
                "session_id": session_id,
                "algorithm": algorithm,
                "total_episodes": session.total_episodes,
                "training_duration": (session.end_time - session.start_time).total_seconds(),
                "final_metrics": session.performance_metrics,
                "status": "completed"
            }
            
            logger.info(f"訓練會話完成: {session_id}")
            return final_stats
            
        except Exception as e:
            logger.error(f"訓練會話 {session_id} 執行失敗: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id].status = "error"
                await self.repository.update_experiment_session_status(session_id, "error")
            raise
    
    async def _simulate_training_episode(
        self,
        algorithm_instance: Any,
        episode: int,
        session: TrainingSession
    ) -> Dict[str, Any]:
        """模擬單個訓練回合"""
        try:
            # 重置環境
            state = await self.leo_env.reset()
            
            episode_reward = 0
            steps = 0
            done = False
            
            while not done and steps < 100:  # 最多100步
                # 使用算法選擇動作
                action = await self._select_action(algorithm_instance, state)
                
                # 執行動作
                next_state, reward, done, info = await self.leo_env.step(action)
                
                episode_reward += reward
                steps += 1
                state = next_state
                
                # 訓練算法（如果支援）
                if hasattr(algorithm_instance, 'learn'):
                    await algorithm_instance.learn(state, action, reward, next_state, done)
            
            # 計算成功率（基於獎勵閾值）
            success = episode_reward > 0
            
            return {
                "episode": episode,
                "reward": episode_reward,
                "steps": steps,
                "success": success,
                "metrics": {
                    "exploration_rate": max(0.1, 1.0 - episode / session.total_episodes),
                    "avg_step_reward": episode_reward / max(steps, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"模擬訓練回合失敗: {e}")
            return {
                "episode": episode,
                "reward": 0.0,
                "steps": 0,
                "success": False,
                "error": str(e)
            }
    
    async def _select_action(self, algorithm_instance: Any, state: Any) -> Any:
        """使用算法選擇動作"""
        try:
            if hasattr(algorithm_instance, 'predict'):
                return await algorithm_instance.predict(state)
            else:
                # 回退到隨機動作
                return self.leo_env.action_space.sample()
        except Exception as e:
            logger.error(f"動作選擇失敗: {e}")
            return self.leo_env.action_space.sample()
    
    async def _log_training_progress(self, session: TrainingSession, episode_result: Dict[str, Any]):
        """記錄訓練進度"""
        try:
            progress_data = {
                "session_id": session.session_id,
                "episode": session.current_episode,
                "progress_percentage": (session.current_episode / session.total_episodes) * 100,
                "current_metrics": session.performance_metrics,
                "last_episode": episode_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # 這裡可以添加更詳細的進度記錄到數據庫
            logger.info(f"會話 {session.session_id} 進度: {progress_data['progress_percentage']:.1f}%")
            
        except Exception as e:
            logger.error(f"記錄訓練進度失敗: {e}")
    
    async def stop_training_session(self, session_id: int):
        """停止訓練會話"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.status = "stopped"
                session.end_time = datetime.now()
                
                # 取消相關任務
                if session_id in self.training_tasks:
                    self.training_tasks[session_id].cancel()
                    del self.training_tasks[session_id]
                
                # 更新數據庫
                await self.repository.update_experiment_session_status(session_id, "stopped")
                await self.repository.update_experiment_session_end_time(session_id, session.end_time)
                
                logger.info(f"停止訓練會話: {session_id}")
            
        except Exception as e:
            logger.error(f"停止訓練會話失敗: {e}")
            raise
    
    async def get_session_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """獲取會話狀態"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                return {
                    "session_id": session_id,
                    "algorithm": session.algorithm,
                    "experiment_name": session.experiment_name,
                    "status": session.status,
                    "current_episode": session.current_episode,
                    "total_episodes": session.total_episodes,
                    "progress_percentage": (session.current_episode / session.total_episodes) * 100,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat() if session.end_time else None,
                    "performance_metrics": session.performance_metrics
                }
            return None
            
        except Exception as e:
            logger.error(f"獲取會話狀態失敗: {e}")
            return None
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """獲取會話統計信息"""
        try:
            active_count = len([s for s in self.active_sessions.values() if s.status == "running"])
            completed_count = len([s for s in self.active_sessions.values() if s.status == "completed"])
            total_count = len(self.active_sessions)
            
            return {
                "total_sessions": total_count,
                "active_sessions": active_count,
                "completed_sessions": completed_count,
                "session_success_rate": completed_count / max(total_count, 1),
                "average_training_time": "2.5 minutes",  # 模擬值
            }
            
        except Exception as e:
            logger.error(f"獲取會話統計失敗: {e}")
            return {"error": str(e)}
    
    async def cleanup_completed_sessions(self, max_age_hours: int = 24):
        """清理已完成的舊會話"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            sessions_to_remove = []
            for session_id, session in self.active_sessions.items():
                if (session.status in ["completed", "error", "stopped"] and 
                    session.end_time and session.end_time < cutoff_time):
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
                if session_id in self.training_tasks:
                    self.training_tasks[session_id].cancel()
                    del self.training_tasks[session_id]
            
            logger.info(f"清理了 {len(sessions_to_remove)} 個舊會話")
            return len(sessions_to_remove)
            
        except Exception as e:
            logger.error(f"清理會話失敗: {e}")
            return 0