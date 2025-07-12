"""
PostgreSQL 資料庫實現
提供研究級 RL 系統的 PostgreSQL 資料儲存功能
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import asyncpg
from contextlib import asynccontextmanager

from ..interfaces.data_repository import IDataRepository

logger = logging.getLogger(__name__)


class PostgreSQLRepository(IDataRepository):
    """PostgreSQL 資料庫儲存庫實現"""

    def __init__(self, database_url: str, max_connections: int = 10):
        """
        初始化 PostgreSQL 儲存庫
        
        Args:
            database_url: PostgreSQL 連接字串
            max_connections: 最大連接數
        """
        self.database_url = database_url
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """初始化資料庫連接池"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=self.max_connections,
                command_timeout=60
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
            raise RuntimeError("資料庫未初始化")
        
        async with self.pool.acquire() as connection:
            yield connection

    # ===== 實驗會話管理 =====

    async def create_experiment_session(
        self,
        experiment_name: str,
        algorithm_type: str,
        scenario_type: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        environment_config: Optional[Dict[str, Any]] = None,
        researcher_id: Optional[str] = None,
        paper_reference: Optional[str] = None,
        research_notes: Optional[str] = None
    ) -> int:
        """創建新的實驗會話"""
        async with self.get_connection() as conn:
            query = """
                INSERT INTO rl_experiment_sessions (
                    experiment_name, algorithm_type, scenario_type,
                    hyperparameters, environment_config, researcher_id,
                    paper_reference, research_notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """
            
            session_id = await conn.fetchval(
                query,
                experiment_name,
                algorithm_type,
                scenario_type,
                json.dumps(hyperparameters) if hyperparameters else None,
                json.dumps(environment_config) if environment_config else None,
                researcher_id,
                paper_reference,
                research_notes
            )
            
            logger.info(f"✅ 創建實驗會話: {session_id} ({algorithm_type})")
            return session_id

    async def update_experiment_session(
        self,
        session_id: int,
        session_status: Optional[str] = None,
        end_time: Optional[datetime] = None,
        total_episodes: Optional[int] = None
    ) -> bool:
        """更新實驗會話狀態"""
        async with self.get_connection() as conn:
            updates = []
            values = []
            param_count = 1

            if session_status:
                updates.append(f"session_status = ${param_count}")
                values.append(session_status)
                param_count += 1

            if end_time:
                updates.append(f"end_time = ${param_count}")
                values.append(end_time)
                param_count += 1

            if total_episodes is not None:
                updates.append(f"total_episodes = ${param_count}")
                values.append(total_episodes)
                param_count += 1

            if not updates:
                return False

            query = f"""
                UPDATE rl_experiment_sessions
                SET {', '.join(updates)}
                WHERE id = ${param_count}
            """
            values.append(session_id)

            result = await conn.execute(query, *values)
            return result == "UPDATE 1"

    async def get_experiment_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """獲取實驗會話資訊"""
        async with self.get_connection() as conn:
            query = """
                SELECT * FROM rl_experiment_sessions
                WHERE id = $1
            """
            
            row = await conn.fetchrow(query, session_id)
            if row:
                return dict(row)
            return None

    # ===== 訓練回合記錄 =====

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
        episode_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """記錄訓練回合數據"""
        async with self.get_connection() as conn:
            query = """
                INSERT INTO rl_training_episodes (
                    session_id, episode_number, total_reward, success_rate,
                    handover_latency_ms, throughput_mbps, packet_loss_rate,
                    convergence_indicator, exploration_rate, episode_metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            
            try:
                await conn.execute(
                    query,
                    session_id,
                    episode_number,
                    total_reward,
                    success_rate,
                    handover_latency_ms,
                    throughput_mbps,
                    packet_loss_rate,
                    convergence_indicator,
                    exploration_rate,
                    json.dumps(episode_metadata) if episode_metadata else None
                )
                return True
            except Exception as e:
                logger.error(f"❌ 記錄回合數據失敗: {e}")
                return False

    async def get_episodes_by_session(
        self,
        session_id: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """獲取會話的訓練回合數據"""
        async with self.get_connection() as conn:
            query = """
                SELECT * FROM rl_training_episodes
                WHERE session_id = $1
                ORDER BY episode_number
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await conn.fetch(query, session_id)
            return [dict(row) for row in rows]

    # ===== 性能時間序列 =====

    async def record_performance_metrics(
        self,
        algorithm_type: str,
        success_rate: Optional[float] = None,
        average_reward: Optional[float] = None,
        response_time_ms: Optional[float] = None,
        stability_score: Optional[float] = None,
        training_progress_percent: Optional[float] = None,
        resource_utilization: Optional[Dict[str, Any]] = None
    ) -> bool:
        """記錄性能指標"""
        async with self.get_connection() as conn:
            query = """
                INSERT INTO rl_performance_timeseries (
                    algorithm_type, success_rate, average_reward,
                    response_time_ms, stability_score, training_progress_percent,
                    resource_utilization
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            
            try:
                await conn.execute(
                    query,
                    algorithm_type,
                    success_rate,
                    average_reward,
                    response_time_ms,
                    stability_score,
                    training_progress_percent,
                    json.dumps(resource_utilization) if resource_utilization else None
                )
                return True
            except Exception as e:
                logger.error(f"❌ 記錄性能指標失敗: {e}")
                return False

    async def get_performance_timeseries(
        self,
        algorithm_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """獲取性能時間序列數據"""
        async with self.get_connection() as conn:
            query = """
                SELECT * FROM rl_performance_timeseries
                WHERE algorithm_type = $1
            """
            params = [algorithm_type]
            param_count = 2

            if start_time:
                query += f" AND measurement_timestamp >= ${param_count}"
                params.append(start_time)
                param_count += 1

            if end_time:
                query += f" AND measurement_timestamp <= ${param_count}"
                params.append(end_time)
                param_count += 1

            query += " ORDER BY measurement_timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"

            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    # ===== 統計分析 =====

    async def get_algorithm_comparison_stats(
        self,
        algorithms: List[str],
        scenario_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """獲取算法比較統計"""
        async with self.get_connection() as conn:
            query = """
                SELECT 
                    s.algorithm_type,
                    COUNT(*) as experiment_count,
                    AVG(s.total_episodes) as avg_episodes,
                    AVG(e.total_reward) as avg_reward,
                    AVG(e.success_rate) as avg_success_rate,
                    STDDEV(e.total_reward) as reward_std
                FROM rl_experiment_sessions s
                LEFT JOIN rl_training_episodes e ON s.id = e.session_id
                WHERE s.algorithm_type = ANY($1)
                AND s.session_status = 'completed'
            """
            params = [algorithms]

            if scenario_type:
                query += " AND s.scenario_type = $2"
                params.append(scenario_type)

            query += " GROUP BY s.algorithm_type"

            rows = await conn.fetch(query, *params)
            
            result = {}
            for row in rows:
                result[row['algorithm_type']] = dict(row)
            
            return result

    # ===== 健康檢查 =====

    async def health_check(self) -> Dict[str, Any]:
        """資料庫健康檢查"""
        if not self._initialized or not self.pool:
            return {
                "status": "unhealthy",
                "error": "資料庫未初始化"
            }

        try:
            async with self.get_connection() as conn:
                # 測試基本查詢
                await conn.fetchval("SELECT 1")
                
                # 檢查 RL 表格是否存在
                table_count = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_name LIKE 'rl_%'
                """)
                
                return {
                    "status": "healthy",
                    "rl_tables_count": table_count,
                    "pool_size": self.pool.get_size(),
                    "pool_idle_size": self.pool.get_idle_size()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    # ===== 模型版本管理 =====

    async def save_model_version(
        self,
        algorithm_type: str,
        version_number: str,
        model_file_path: str,
        training_session_id: Optional[int] = None,
        validation_score: Optional[float] = None,
        test_score: Optional[float] = None,
        model_size_mb: Optional[float] = None,
        inference_time_ms: Optional[float] = None
    ) -> int:
        """保存模型版本"""
        async with self.get_connection() as conn:
            query = """
                INSERT INTO rl_model_versions (
                    algorithm_type, version_number, model_file_path,
                    training_session_id, validation_score, test_score,
                    model_size_mb, inference_time_ms
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """
            
            model_id = await conn.fetchval(
                query,
                algorithm_type,
                version_number,
                model_file_path,
                training_session_id,
                validation_score,
                test_score,
                model_size_mb,
                inference_time_ms
            )
            
            logger.info(f"✅ 保存模型版本: {model_id} ({algorithm_type} v{version_number})")
            return model_id

    async def get_model_versions(
        self,
        algorithm_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """獲取模型版本列表"""
        async with self.get_connection() as conn:
            query = """
                SELECT * FROM rl_model_versions
            """
            params = []

            if algorithm_type:
                query += " WHERE algorithm_type = $1"
                params.append(algorithm_type)

            query += " ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"

            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]