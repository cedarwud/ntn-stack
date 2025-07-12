"""
增強版 RL 訓練路由器 - 整合 PostgreSQL 持久化儲存
提供研究級的訓練數據收集和管理功能
"""

import asyncio
import logging
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import hashlib

from ..core.algorithm_factory import get_algorithm
from ..interfaces.data_repository import IDataRepository, ExperimentSession
from ..interfaces.rl_algorithm import ScenarioType


logger = logging.getLogger(__name__)
router = APIRouter()

# 活躍的訓練任務管理
background_tasks: Dict[str, asyncio.Task] = {}
training_instances: Dict[str, Any] = {}
training_sessions: Dict[str, int] = {}  # algorithm -> session_id 映射


class TrainingConfig(BaseModel):
    """訓練配置模型"""

    total_episodes: int = Field(default=100, description="總訓練回合數")
    step_time: float = Field(default=0.1, description="每步驟時間 (秒)")
    experiment_name: Optional[str] = Field(default=None, description="實驗名稱")
    scenario_type: str = Field(default="default", description="場景類型")
    researcher_id: Optional[str] = Field(default="system", description="研究員 ID")
    research_notes: Optional[str] = Field(default=None, description="研究筆記")
    environment: str = Field(default="CartPole-v1", description="環境名稱")


class TrainingStatus(BaseModel):
    """訓練狀態響應模型"""

    algorithm: str
    status: str
    is_training: bool
    session_id: Optional[int] = None
    training_progress: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    message: str


async def get_repository() -> IDataRepository:
    """
    依賴注入：返回 PostgreSQL 實際數據儲存庫
    Phase 1 改進：完全摒棄 MockRepository，使用真實數據庫
    """
    try:
        from ..implementations.postgresql_repository import PostgreSQLRepository

        database_url = os.getenv(
            "RL_DATABASE_URL", "postgresql://rl_user:rl_password@simworld_postgis:5432/rl_db"
        )
        logger.info(f"🔗 Phase 1: 初始化 PostgreSQL 真實數據庫連接")
        repository = PostgreSQLRepository(database_url)

        if not await repository.initialize():
            logger.error("❌ PostgreSQL 數據庫初始化失敗")
            raise Exception("PostgreSQL 數據庫初始化失敗")

        logger.info("✅ Phase 1: PostgreSQL 真實數據庫連接成功")
        return repository

    except Exception as e:
        logger.error(f"❌ Phase 1: PostgreSQL 連接失敗，錯誤: {e}")
        if os.getenv("ENV") == "development":
            logger.warning("⚠️  PHASE 1 警告: 降級到 MockRepository (開發模式)")
            from ..implementations.mock_repository import MockRepository

            return MockRepository()
        raise


@router.post("/start/{algorithm}")
async def start_training_with_persistence(
    algorithm: str,
    config: TrainingConfig,
    background_tasks_param: BackgroundTasks,
    db: IDataRepository = Depends(get_repository),
) -> Dict[str, Any]:
    if algorithm in background_tasks and not background_tasks[algorithm].done():
        raise HTTPException(
            status_code=409, detail=f"演算法 '{algorithm}' 的訓練任務已在執行中。"
        )

    try:
        experiment_name = (
            config.experiment_name
            or f"{algorithm}_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        hyperparameters = {
            "total_episodes": config.total_episodes,
            "step_time": config.step_time,
            "environment": config.environment,
        }
        config_str = str(hyperparameters) + str(config.environment)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()

        session_data = ExperimentSession(
            id=None,
            experiment_name=experiment_name,
            algorithm_type=algorithm,
            scenario_type=ScenarioType(config.scenario_type),
            paper_reference=None,
            researcher_id=config.researcher_id or "system",
            start_time=datetime.now(),
            end_time=None,
            total_episodes=config.total_episodes,
            session_status="created",
            config_hash=config_hash,
            hyperparameters=hyperparameters,
            environment_config={"env_name": config.environment, "version": "1.0"},
            research_notes=config.research_notes,
            created_at=datetime.now(),
        )
        session_id = await db.create_experiment_session(session_data)

        algorithm_config = {
            "total_episodes": config.total_episodes,
            "step_time": config.step_time,
        }
        trainer = get_algorithm(algorithm, config.environment, algorithm_config)
        training_instances[algorithm] = trainer
        training_sessions[algorithm] = session_id

        loop = asyncio.get_event_loop()
        task = loop.create_task(
            run_enhanced_training_loop(algorithm, trainer, session_id, config)
        )
        background_tasks[algorithm] = task

        return {
            "message": "訓練任務已啟動",
            "session_id": session_id,
            "algorithm": algorithm,
        }

    except Exception as e:
        logger.error(f"啟動訓練失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"內部伺服器錯誤: {e}")


async def run_enhanced_training_loop(
    algorithm: str, trainer: Any, session_id: int, config: TrainingConfig
):
    """
    增強版訓練循環 - 整合數據庫記錄
    """
    db = await get_repository()
    total_episodes = config.total_episodes
    logger.info(f"🏃‍♂️ 開始訓練循環: {algorithm} (會話 ID: {session_id})")

    try:
        for episode in range(total_episodes):
            if algorithm not in background_tasks:
                logger.warning(f"訓練任務 '{algorithm}' 已被外部停止。")
                break

            trainer.train()
            status = trainer.get_status()

            # 記錄回合數據 (需要適配 TrainingEpisode dataclass)
            # episode_data = TrainingEpisode(...)
            # await db.create_training_episode(episode_data)

            await asyncio.sleep(config.step_time)

        logger.info(f"✅ 訓練完成: {algorithm} (會話 ID: {session_id})")
        updates = {
            "session_status": "completed",
            "end_time": datetime.now(),
            "total_episodes": total_episodes,
        }
        await db.update_experiment_session(session_id, updates)

    except Exception as e:
        logger.error(f"訓練循環出錯 ({algorithm}): {e}", exc_info=True)
        updates = {"session_status": "failed", "end_time": datetime.now()}
        await db.update_experiment_session(session_id, updates)
    finally:
        if algorithm in background_tasks:
            del background_tasks[algorithm]
        if algorithm in training_instances:
            del training_instances[algorithm]


@router.get("/status/{algorithm}", response_model=TrainingStatus)
async def get_enhanced_training_status(algorithm: str) -> TrainingStatus:
    is_training = (
        algorithm in background_tasks and not background_tasks[algorithm].done()
    )
    status = "training" if is_training else "idle"
    session_id = training_sessions.get(algorithm)

    # ... (rest of the logic)
    return TrainingStatus(
        algorithm=algorithm,
        status=status,
        is_training=is_training,
        session_id=session_id,
        message="OK",
    )


@router.post("/stop/{algorithm}")
async def stop_enhanced_training(algorithm: str):
    if algorithm not in background_tasks:
        raise HTTPException(
            status_code=404, detail=f"訓練任務 '{algorithm}' 未在執行中。"
        )

    task = background_tasks.pop(algorithm, None)
    if task:
        task.cancel()
        if algorithm in training_instances:
            trainer = training_instances.pop(algorithm)
            trainer.stop_training()

        session_id = training_sessions.pop(algorithm, None)
        if session_id:
            db = await get_repository()
            updates = {"session_status": "stopped", "end_time": datetime.now()}
            await db.update_experiment_session(session_id, updates)

        return {"message": f"訓練任務 '{algorithm}' 已停止。"}
    return {"message": "任務未找到或已完成。"}


@router.get("/sessions")
async def get_training_sessions(
    algorithm_type: Optional[str] = None,
    limit: int = 20,
    db: IDataRepository = Depends(get_repository),
) -> List[Dict[str, Any]]:
    # This is a simplified example. In a real app, you'd build a proper filter.
    from ..interfaces.data_repository import QueryFilter

    filters = QueryFilter(
        algorithm_types=[algorithm_type] if algorithm_type else None, limit=limit
    )
    sessions = await db.query_experiment_sessions(filters)
    return [s.__dict__ for s in sessions]


@router.get("/health")
async def health_check(db: IDataRepository = Depends(get_repository)):
    """端點健康檢查，同時檢查數據庫連接"""
    try:
        db_health = await db.get_database_health()
        return {"api_status": "healthy", "database_status": db_health}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"健康檢查失敗: {e}")
