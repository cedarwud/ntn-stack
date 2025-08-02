"""
模擬數據儲存庫實現
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..interfaces.data_repository import (
    IDataRepository,
    ExperimentSession,
    TrainingEpisode,
    ModelVersion,
    QueryFilter,
    PerformanceMetric,
    MetricType,
    ScenarioType,
)

logger = logging.getLogger(__name__)


class MockRepository(IDataRepository):
    """
    模擬數據儲存庫，用於開發和測試。
    實現 IDataRepository 接口，但在內存中操作數據。
    """

    def __init__(self):
        self._experiments: Dict[int, ExperimentSession] = {}
        self._episodes: Dict[int, List[TrainingEpisode]] = {}
        self._models: Dict[int, ModelVersion] = {}
        self._next_session_id = 1
        self._next_episode_id = 1
        self._next_model_id = 1
        logger.info("✅ MockRepository 初始化成功")

    async def create_experiment_session(self, session: ExperimentSession) -> int:
        session.id = self._next_session_id
        self._experiments[session.id] = session
        self._episodes[session.id] = []
        logger.info(f"Mock: 創建訓練會話 #{session.id}")
        self._next_session_id += 1
        return session.id

    async def get_experiment_session(
        self, session_id: int
    ) -> Optional[ExperimentSession]:
        return self._experiments.get(session_id)

    async def update_experiment_session(
        self, session_id: int, updates: Dict[str, Any]
    ) -> bool:
        if session_id in self._experiments:
            session = self._experiments[session_id]
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            logger.info(f"Mock: 更新訓練會話 #{session_id}")
            return True
        return False

    async def delete_experiment_session(self, session_id: int) -> bool:
        if session_id in self._experiments:
            del self._experiments[session_id]
            if session_id in self._episodes:
                del self._episodes[session_id]
            logger.info(f"Mock: 刪除訓練會話 #{session_id}")
            return True
        return False

    async def query_experiment_sessions(
        self, filter_obj: QueryFilter
    ) -> List[ExperimentSession]:
        # 簡化模擬，僅返回所有訓練
        return list(self._experiments.values())

    async def create_training_episode(self, episode: TrainingEpisode) -> int:
        if episode.session_id in self._episodes:
            episode.id = self._next_episode_id
            self._episodes[episode.session_id].append(episode)
            self._next_episode_id += 1
            return episode.id
        return 0

    async def get_training_episodes(
        self, session_id: int, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[TrainingEpisode]:
        episodes = self._episodes.get(session_id, [])
        start = offset or 0
        end = (start + limit) if limit is not None else None
        return episodes[start:end]

    async def get_latest_episode(self, session_id: int) -> Optional[TrainingEpisode]:
        if session_id in self._episodes and self._episodes[session_id]:
            return self._episodes[session_id][-1]
        return None

    async def batch_create_episodes(self, episodes: List[TrainingEpisode]) -> int:
        count = 0
        for episode in episodes:
            if await self.create_training_episode(episode):
                count += 1
        return count

    async def store_performance_metric(self, metric: PerformanceMetric) -> bool:
        logger.info(
            f"Mock: 存儲性能指標 {metric.metric_type.name} for {metric.algorithm_name}"
        )
        return True

    async def batch_store_metrics(self, metrics: List[PerformanceMetric]) -> int:
        for metric in metrics:
            await self.store_performance_metric(metric)
        return len(metrics)

    async def query_performance_metrics(
        self,
        algorithm_names: List[str],
        metric_types: List[MetricType],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[PerformanceMetric]:
        return []

    async def create_model_version(self, model: ModelVersion) -> int:
        model.id = self._next_model_id
        self._models[model.id] = model
        self._next_model_id += 1
        return model.id

    async def get_model_versions(
        self, algorithm_type: str, limit: Optional[int] = None
    ) -> List[ModelVersion]:
        return [m for m in self._models.values() if m.algorithm_type == algorithm_type][
            :limit
        ]

    async def get_best_model(
        self, algorithm_type: str, metric: str = "validation_score"
    ) -> Optional[ModelVersion]:
        models = [
            m for m in self._models.values() if m.algorithm_type == algorithm_type
        ]
        if not models:
            return None
        return max(models, key=lambda m: getattr(m, metric, 0.0))

    async def get_algorithm_statistics(
        self, algorithm_name: str, scenario_type: Optional[ScenarioType] = None
    ) -> Dict[str, Any]:
        return {"avg_reward": 100.0, "episodes": 1000}

    async def get_convergence_analysis(
        self, session_ids: List[int], convergence_threshold: float = 0.95
    ) -> List[Dict[str, Any]]:
        return [{"session_id": sid, "converged_at_episode": 500} for sid in session_ids]

    async def compare_algorithms(
        self,
        algorithm_names: List[str],
        metric_types: List[MetricType],
        scenario_type: Optional[ScenarioType] = None,
    ) -> Dict[str, Any]:
        return {name: {"reward": 100} for name in algorithm_names}

    async def backup_data(self, backup_path: str) -> bool:
        logger.info(f"Mock: 備份數據到 {backup_path}")
        return True

    async def restore_data(self, backup_path: str) -> bool:
        logger.info(f"Mock: 從 {backup_path} 恢復數據")
        return True

    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        logger.info(f"Mock: 清理 {days_to_keep} 天前的舊數據")
        return 0

    async def get_database_health(self) -> Dict[str, Any]:
        return {"status": "healthy", "database": "mock"}
