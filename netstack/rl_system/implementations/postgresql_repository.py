"""
PostgreSQL 資料庫實現
提供研究級 RL 系統的 PostgreSQL 資料儲存功能
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncpg
from contextlib import asynccontextmanager

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


class PostgreSQLRepository(IDataRepository):
    """PostgreSQL 資料庫儲存庫實現"""

    def __init__(self, database_url: str, max_connections: int = 10):
        self.database_url = database_url
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """初始化資料庫連接池"""
        if self._initialized:
            return True
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=self.max_connections,
                command_timeout=60,
            )
            self._initialized = True
            logger.info("✅ PostgreSQL 連接池初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL 連接池初始化失敗: {e}")
            return False

    async def close(self) -> None:
        """關閉資料庫連接池"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("✅ PostgreSQL 連接池已關閉")

    @asynccontextmanager
    async def get_connection(self):
        """獲取資料庫連接的上下文管理器"""
        if not self._initialized or not self.pool:
            await self.initialize()
            if not self._initialized or not self.pool:
                raise RuntimeError("資料庫未初始化")

        async with self.pool.acquire() as connection:
            yield connection

    # ===== 實驗會話管理 =====

    async def create_experiment_session(self, session: ExperimentSession) -> int:
        async with self.get_connection() as conn:
            query = """
                INSERT INTO rl_experiment_sessions (
                    experiment_name, algorithm_type, scenario_type, hyperparameters, 
                    environment_config, researcher_id, paper_reference, research_notes, 
                    session_status, config_hash, start_time, total_episodes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """
            session_id = await conn.fetchval(
                query,
                session.experiment_name,
                session.algorithm_type,
                session.scenario_type.value,
                json.dumps(session.hyperparameters),
                json.dumps(session.environment_config),
                session.researcher_id,
                session.paper_reference,
                session.research_notes,
                session.session_status,
                session.config_hash,
                session.start_time,
                session.total_episodes,
            )
            logger.info(f"✅ 創建實驗會話: {session_id} ({session.algorithm_type})")
            return session_id

    async def get_experiment_session(
        self, session_id: int
    ) -> Optional[ExperimentSession]:
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM rl_experiment_sessions WHERE id = $1", session_id
            )
            if row:
                return ExperimentSession(**dict(row))
            return None

    async def update_experiment_session(
        self, session_id: int, updates: Dict[str, Any]
    ) -> bool:
        async with self.get_connection() as conn:
            fields, values = [], []
            for i, (key, value) in enumerate(updates.items()):
                fields.append(f"{key} = ${i+1}")
                values.append(value)

            if not fields:
                return False

            query = f"UPDATE rl_experiment_sessions SET {', '.join(fields)} WHERE id = ${len(values)+1}"
            values.append(session_id)
            result = await conn.execute(query, *values)
            return result == "UPDATE 1"

    async def delete_experiment_session(self, session_id: int) -> bool:
        async with self.get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM rl_experiment_sessions WHERE id = $1", session_id
            )
            return result == "DELETE 1"

    async def query_experiment_sessions(
        self, filter_obj: QueryFilter
    ) -> List[ExperimentSession]:
        # 此為簡化實現，實際應解析 filter_obj 構建複雜查詢
        async with self.get_connection() as conn:
            rows = await conn.fetch(
                "SELECT * FROM rl_experiment_sessions ORDER BY start_time DESC LIMIT $1",
                filter_obj.limit or 100,
            )
            return [ExperimentSession(**dict(row)) for row in rows]

    # ===== 訓練回合管理 =====

    async def create_training_episode(self, episode: TrainingEpisode) -> int:
        pass  # Placeholder
        return 0

    async def get_training_episodes(
        self, session_id: int, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[TrainingEpisode]:
        return []  # Placeholder

    async def get_latest_episode(self, session_id: int) -> Optional[TrainingEpisode]:
        return None  # Placeholder

    async def batch_create_episodes(self, episodes: List[TrainingEpisode]) -> int:
        return 0  # Placeholder

    # ===== 性能指標管理 =====

    async def store_performance_metric(self, metric: PerformanceMetric) -> bool:
        return False  # Placeholder

    async def batch_store_metrics(self, metrics: List[PerformanceMetric]) -> int:
        return 0  # Placeholder

    async def query_performance_metrics(
        self,
        algorithm_names: List[str],
        metric_types: List[MetricType],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[PerformanceMetric]:
        return []  # Placeholder

    # ===== 模型版本管理 =====

    async def create_model_version(self, model: ModelVersion) -> int:
        return 0  # Placeholder

    async def get_model_versions(
        self, algorithm_type: str, limit: Optional[int] = None
    ) -> List[ModelVersion]:
        return []  # Placeholder

    async def get_best_model(
        self, algorithm_type: str, metric: str = "validation_score"
    ) -> Optional[ModelVersion]:
        return None  # Placeholder

    # ===== 統計分析 =====

    async def get_algorithm_statistics(
        self, algorithm_name: str, scenario_type: Optional[ScenarioType] = None
    ) -> Dict[str, Any]:
        return {}  # Placeholder

    async def get_convergence_analysis(
        self, session_ids: List[int], convergence_threshold: float = 0.95
    ) -> List[Dict[str, Any]]:
        return []  # Placeholder

    async def compare_algorithms(
        self,
        algorithm_names: List[str],
        metric_types: List[MetricType],
        scenario_type: Optional[ScenarioType] = None,
    ) -> Dict[str, Any]:
        return {}  # Placeholder

    # ===== 數據庫維護 =====

    async def backup_data(self, backup_path: str) -> bool:
        return False  # Placeholder

    async def restore_data(self, backup_path: str) -> bool:
        return False  # Placeholder

    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        return 0  # Placeholder

    async def get_database_health(self) -> Dict[str, Any]:
        if not self._initialized or not self.pool:
            return {"status": "unhealthy", "error": "資料庫未初始化"}
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
                return {"status": "healthy", "database": "postgresql"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    # ===== 原有但不符合介面的方法 (待重構) =====
    # 這些方法暫時保留，以便參考，但最終應被重構成符合介面的形式

    async def record_episode(
        self,
        session_id: int,
        episode_number: int,
        total_reward: float,
        success_rate: Optional[float] = None,
        handover_latency_ms: Optional[float] = None,
        throughput_mbps: Optional[float] = None,
        packet_loss_rate: Optional[float] = None,
        convergence_indicator: Optional[float] = None,
        exploration_rate: Optional[float] = None,
        episode_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """(待重構) 記錄訓練回合數據"""
        pass
        return False

    async def get_episodes_by_session(
        self, session_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """(待重構) 獲取會話的訓練回合數據"""
        return []

    async def record_performance_metrics(
        self,
        algorithm_type: str,
        success_rate: Optional[float] = None,
        average_reward: Optional[float] = None,
        response_time_ms: Optional[float] = None,
        stability_score: Optional[float] = None,
        training_progress_percent: Optional[float] = None,
        resource_utilization: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """(待重構) 記錄性能指標"""
        pass
        return False

    async def get_performance_timeseries(
        self,
        algorithm_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """(待重構) 獲取性能時間序列數據"""
        return []

    async def get_algorithm_comparison_stats(
        self, algorithms: List[str], scenario_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """(待重構) 獲取算法比較統計"""
        return {}

    async def save_model_version(
        self,
        algorithm_type: str,
        version_number: str,
        model_file_path: str,
        training_session_id: Optional[int] = None,
        validation_score: Optional[float] = None,
        test_score: Optional[float] = None,
        model_size_mb: Optional[float] = None,
        inference_time_ms: Optional[float] = None,
    ) -> int:
        """(待重構) 保存模型版本"""
        return 0

    async def health_check(self) -> Dict[str, Any]:
        """(待重構) 原有的健康檢查"""
        return await self.get_database_health()
