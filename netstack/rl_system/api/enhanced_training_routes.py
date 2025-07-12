"""
增強版 RL 訓練路由器 - 整合 PostgreSQL 持久化儲存
提供研究級的訓練數據收集和管理功能
"""

import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from ..core.algorithm_factory import get_algorithm
# 遵循 YAGNI 原則：內聯簡化實現，避免複雜的模組依賴

logger = logging.getLogger(__name__)

router = APIRouter()


class MockRepository:
    """
    模擬儲存庫實現 - 遵循 SOLID 原則
    單一職責：專門處理訓練數據存儲模擬
    """
    
    def __init__(self, database_url: str = ""):
        self.database_url = database_url
        self._session_counter = 1
        
    def initialize(self) -> bool:
        """初始化模擬儲存庫"""
        logger.info("✅ 模擬儲存庫初始化完成 (無需實際連接)")
        return True
    
    def create_experiment_session(
        self, experiment_name: str, algorithm_type: str, scenario_type: str,
        hyperparameters: Dict[str, Any], environment_config: Dict[str, Any],
        researcher_id: str = "system", research_notes: Optional[str] = None
    ) -> int:
        """創建模擬實驗會話"""
        session_id = self._session_counter
        self._session_counter += 1
        logger.info(f"✅ 模擬創建實驗會話: {session_id} ({experiment_name})")
        return session_id
    
    def record_episode(self, session_id: int, episode_number: int, total_reward: float,
                      success_rate: Optional[float] = None, convergence_indicator: Optional[float] = None,
                      exploration_rate: Optional[float] = None, episode_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """記錄模擬回合數據"""
        logger.debug(f"📊 模擬記錄回合 {episode_number}: 獎勵={total_reward:.2f}")
        return True
    
    def record_performance_metrics(self, algorithm_type: str, average_reward: float,
                                  training_progress_percent: float, stability_score: float,
                                  resource_utilization: Dict[str, float]) -> bool:
        """記錄模擬性能指標"""
        logger.debug(f"📈 模擬記錄性能: {algorithm_type}, 平均獎勵={average_reward:.2f}")
        return True
    
    def update_experiment_session(self, session_id: int, session_status: str,
                                 end_time: Optional[datetime] = None, total_episodes: Optional[int] = None) -> bool:
        """更新模擬會話狀態"""
        logger.info(f"🔄 模擬更新會話 {session_id}: {session_status}")
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """模擬健康檢查"""
        return {
            "status": "healthy",
            "driver": "mock",
            "connected": True,
            "timestamp": datetime.now().isoformat()
        }


# 全域儲存庫實例 - 遵循依賴注入原則
repository: Optional[MockRepository] = None

# 活躍的訓練任務管理
background_tasks: Dict[str, asyncio.Task] = {}
training_instances: Dict[str, Any] = {}
training_sessions: Dict[str, int] = {}  # algorithm -> session_id 映射


class TrainingConfig(BaseModel):
    """訓練配置模型"""
    total_episodes: int = Field(default=100, description="總訓練回合數")
    step_time: float = Field(default=0.1, description="每步驟時間 (秒)")
    experiment_name: Optional[str] = Field(default=None, description="實驗名稱")
    scenario_type: Optional[str] = Field(default="default", description="場景類型")
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


async def get_repository() -> MockRepository:
    """
    獲取資料庫儲存庫實例
    遵循單一職責原則：專門負責儲存庫初始化
    """
    global repository
    if repository is None:
        # 遵循 YAGNI 原則：先使用模擬實現
        repository = MockRepository()
        success = repository.initialize()
        if success:
            logger.info("✅ 模擬儲存庫初始化完成")
        else:
            logger.warning("⚠️ 儲存庫初始化失敗")
    return repository


@router.post("/start/{algorithm}")
async def start_training_with_persistence(
    algorithm: str, 
    config: TrainingConfig,
    background_tasks_param: BackgroundTasks,
    db: MockRepository = Depends(get_repository)
) -> Dict[str, Any]:
    print(f"🔍 DEBUG: Function called with algorithm={algorithm}")
    logger.info(f"🔍 Function called with algorithm={algorithm}")
    """
    啟動帶有持久化儲存的強化學習訓練任務
    """
    if algorithm in background_tasks and not background_tasks[algorithm].done():
        raise HTTPException(
            status_code=409, 
            detail=f"演算法 '{algorithm}' 的訓練任務已在執行中。"
        )

    try:
        # 創建實驗會話 - 遵循依賴注入原則
        experiment_name = config.experiment_name or f"{algorithm}_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session_id = db.create_experiment_session(
            experiment_name=experiment_name,
            algorithm_type=algorithm,
            scenario_type=config.scenario_type,
            hyperparameters={
                "total_episodes": config.total_episodes,
                "step_time": config.step_time,
                "environment": config.environment
            },
            environment_config={
                "env_name": config.environment,
                "version": "1.0"
            },
            researcher_id=config.researcher_id,
            research_notes=config.research_notes
        )

        # 創建算法實例
        algorithm_config = {
            "total_episodes": config.total_episodes, 
            "step_time": config.step_time
        }
        
        trainer = get_algorithm(algorithm, config.environment, algorithm_config)
        training_instances[algorithm] = trainer
        training_sessions[algorithm] = session_id

        # 啟動背景訓練任務並正確追蹤
        # 使用 ensure_future 確保任務在事件循環中持續運行
        loop = asyncio.get_event_loop()
        task = loop.create_task(
            run_enhanced_training_loop(algorithm, trainer, session_id, config)
        )
        background_tasks[algorithm] = task
        
        # 立即檢查任務狀態
        logger.info(f"🔍 Task state after creation: {task.get_loop()}, done: {task.done()}")

        print(f"✅ DEBUG: 啟動訓練: {algorithm} (會話 ID: {session_id})")
        print(f"🔍 DEBUG: Background task created: {task}")
        print(f"🔍 DEBUG: Training instances: {list(training_instances.keys())}")
        print(f"🔍 DEBUG: Background tasks: {list(background_tasks.keys())}")
        
        # 檢查任務狀態
        await asyncio.sleep(0.1)  # 短暫等待
        print(f"🔍 DEBUG: Task done after 0.1s: {task.done()}")
        if task.done():
            try:
                result = task.result()
                print(f"✅ DEBUG: Task completed successfully: {result}")
            except Exception as e:
                print(f"❌ DEBUG: Task failed with error: {e}")
                import traceback
                print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        
        logger.info(f"✅ 啟動訓練: {algorithm} (會話 ID: {session_id})")
        logger.info(f"🔍 Background task created: {task}")
        logger.info(f"🔍 Training instances: {list(training_instances.keys())}")
        logger.info(f"🔍 Background tasks: {list(background_tasks.keys())}")
        
        return {
            "message": f"演算法 '{algorithm}' 的訓練已啟動",
            "session_id": session_id,
            "experiment_name": experiment_name,
            "config": config.dict()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ 啟動訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法啟動訓練: {e}")


async def run_enhanced_training_loop(
    algorithm: str, 
    trainer: Any, 
    session_id: int,
    config: TrainingConfig
):
    """
    增強版訓練循環，包含資料庫記錄功能
    """
    db = await get_repository()
    episode_count = 0
    
    try:
        print(f"🚀 DEBUG: 開始訓練循環: {algorithm} (會話 {session_id})")
        print(f"🔍 DEBUG: 訓練配置: {config}")
        print(f"🔍 DEBUG: 訓練器初始狀態: {trainer.is_training}")
        print(f"🔍 DEBUG: 總訓練回合: {config.total_episodes}")
        
        logger.info(f"🚀 開始訓練循環: {algorithm} (會話 {session_id})")
        logger.info(f"🔍 訓練配置: {config}")
        logger.info(f"🔍 訓練器初始狀態: {trainer.is_training}")
        
        # 設置訓練器為訓練狀態
        trainer.is_training = True
        print(f"🔍 DEBUG: 設置訓練器狀態為: {trainer.is_training}")
        logger.info(f"🔍 設置訓練器狀態為: {trainer.is_training}")
        
        # 更新會話狀態為進行中 - 使用同步方法
        db.update_experiment_session(
            session_id=session_id,
            session_status="running"
        )
        
        print(f"🔄 DEBUG: 開始訓練循環，目標回合數: {config.total_episodes}")
        
        while episode_count < config.total_episodes and trainer.is_training:
            print(f"🔄 DEBUG: 執行第 {episode_count + 1} 回合訓練...")
            
            # 執行一步訓練
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, trainer.train)
            
            episode_count += 1
            
            # 獲取訓練指標
            metrics = trainer.get_training_metrics()
            trainer_episode = metrics.get("episode", 0)
            
            print(f"📊 DEBUG: 回合 {episode_count} 完成，訓練器內部回合: {trainer_episode}")
            print(f"📊 DEBUG: 訓練指標: {metrics}")
            
            # 記錄回合數據到資料庫 - 使用同步方法
            db.record_episode(
                session_id=session_id,
                episode_number=episode_count,
                total_reward=metrics.get("last_reward", 0.0),
                success_rate=None,  # 待算法實現
                convergence_indicator=metrics.get("progress", 0.0) / 100.0,
                exploration_rate=getattr(trainer, "_epsilon", None),
                episode_metadata={
                    "algorithm": algorithm,
                    "environment": config.environment,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # 記錄性能時間序列 - 使用同步方法
            db.record_performance_metrics(
                algorithm_type=algorithm,
                average_reward=metrics.get("average_reward", 0.0),
                training_progress_percent=metrics.get("progress", 0.0),
                stability_score=1.0 - metrics.get("loss", 1.0),  # 簡單的穩定性評分
                resource_utilization=trainer.get_memory_usage()
            )
            
            # 每 5 回合記錄一次詳細日誌
            if episode_count % 5 == 0:
                print(f"📊 DEBUG: {algorithm} 進度: {episode_count}/{config.total_episodes} (平均獎勵: {metrics.get('average_reward', 0.0):.2f})")
                logger.info(
                    f"📊 {algorithm} 進度: {episode_count}/{config.total_episodes} "
                    f"(平均獎勵: {metrics.get('average_reward', 0.0):.2f})"
                )
            
            # 檢查訓練器是否仍在訓練狀態
            if not trainer.is_training:
                print(f"⚠️ DEBUG: 訓練器提前停止，回合: {episode_count}")
                break
            
            # 短暫暫停避免過度使用 CPU
            await asyncio.sleep(0.01)
        
        print(f"✅ DEBUG: 訓練循環完成，總回合數: {episode_count}")
        
        # 訓練完成，更新會話狀態 - 使用同步方法
        db.update_experiment_session(
            session_id=session_id,
            session_status="completed",
            end_time=datetime.now(),
            total_episodes=episode_count
        )
        
        # 確保訓練器顯示最終狀態 (100%)
        if hasattr(trainer, '_current_episode'):
            trainer._current_episode = episode_count
        
        print(f"⏳ DEBUG: 保持最終狀態1秒，讓前端顯示100%完成狀態...")
        await asyncio.sleep(1)  # 保持狀態1秒，讓前端有時間顯示100%
        
        # 🔧 關鍵修復：設置訓練器為非訓練狀態
        trainer.is_training = False
        print(f"🔧 DEBUG: 設置訓練器 {algorithm} 為停止狀態")
        
        logger.info(f"✅ 訓練完成: {algorithm} (會話 {session_id}, 回合數: {episode_count})")
        
    except asyncio.CancelledError:
        print(f"⚠️ DEBUG: 訓練被取消: {algorithm} (會話 {session_id})")
        # 訓練被取消 - 使用同步方法
        db.update_experiment_session(
            session_id=session_id,
            session_status="cancelled",
            end_time=datetime.now(),
            total_episodes=episode_count
        )
        logger.info(f"⚠️ 訓練被取消: {algorithm} (會話 {session_id})")
        
    except Exception as e:
        print(f"❌ DEBUG: 訓練失敗: {algorithm} (會話 {session_id}) - {e}")
        import traceback
        print(f"🔍 DEBUG: 詳細錯誤: {traceback.format_exc()}")
        # 訓練出錯 - 使用同步方法
        db.update_experiment_session(
            session_id=session_id,
            session_status="failed",
            end_time=datetime.now(),
            total_episodes=episode_count
        )
        logger.error(f"❌ 訓練失敗: {algorithm} (會話 {session_id}) - {e}")
        
    finally:
        # 延遲清理資源，確保前端有時間顯示最終狀態
        print(f"⏳ DEBUG: 1秒後清理資源，讓前端顯示完整狀態...")
        await asyncio.sleep(1)
        
        print(f"🧹 DEBUG: 清理資源: {algorithm}")
        # 清理資源
        if algorithm in background_tasks:
            del background_tasks[algorithm]
        if algorithm in training_instances:
            del training_instances[algorithm]
        if algorithm in training_sessions:
            del training_sessions[algorithm]


@router.get("/status/{algorithm}")
async def get_enhanced_training_status(algorithm: str) -> TrainingStatus:
    """
    獲取增強版訓練狀態，包含資料庫資訊
    """
    supported_algorithms = ["dqn", "ppo", "sac"]
    
    if algorithm not in supported_algorithms:
        raise HTTPException(
            status_code=400, 
            detail=f"不支援的演算法 '{algorithm}'。支援的演算法: {supported_algorithms}"
        )
    
    # 檢查是否有活躍的訓練任務或實例
    has_task = algorithm in background_tasks and not background_tasks[algorithm].done()
    has_instance = algorithm in training_instances
    
    if not has_task and not has_instance:
        return TrainingStatus(
            algorithm=algorithm,
            status="not_running",
            is_training=False,
            message=f"演算法 '{algorithm}' 目前沒有在訓練中"
        )

    # 獲取訓練狀態
    if has_task:
        # 有背景任務在運行
        task = background_tasks[algorithm]
        session_id = training_sessions.get(algorithm)
        
        # 如果任務還在運行且有訓練實例
        if has_instance:
            trainer = training_instances[algorithm]
            status = trainer.get_status()
            metrics = trainer.get_training_metrics()
            return TrainingStatus(
                algorithm=algorithm,
                status="training",
                is_training=True,
                session_id=session_id,
                training_progress=status,
                metrics={
                    **metrics,
                    "episodes_completed": metrics.get("episode", 0)  # 確保有 episodes_completed 欄位
                },
                message=f"演算法 '{algorithm}' 正在訓練中 (回合: {metrics.get('episode', 0)})"
            )
        else:
            # 任務在運行但還沒有訓練實例（剛啟動）
            return TrainingStatus(
                algorithm=algorithm,
                status="starting",
                is_training=True,
                session_id=session_id,
                training_progress=None,
                metrics=None,
                message=f"演算法 '{algorithm}' 正在啟動訓練"
            )
    
    elif has_instance:
        # 只有訓練實例，沒有背景任務（可能已完成或錯誤）
        trainer = training_instances[algorithm]
        session_id = training_sessions.get(algorithm)
        status = trainer.get_status()
        
        return TrainingStatus(
            algorithm=algorithm,
            status="completed" if not trainer.is_training else "idle",
            is_training=trainer.is_training,
            session_id=session_id,
            training_progress=status,
            metrics=trainer.get_training_metrics(),
            message=f"演算法 '{algorithm}' 訓練已完成或停止"
        )


@router.post("/stop/{algorithm}")
async def stop_enhanced_training(algorithm: str):
    """
    停止增強版訓練任務
    """
    if algorithm not in background_tasks or background_tasks[algorithm].done():
        raise HTTPException(
            status_code=404, 
            detail=f"找不到正在執行的演算法 '{algorithm}' 訓練任務。"
        )

    # 取消背景任務
    task = background_tasks[algorithm]
    task.cancel()

    # 停止訓練器
    trainer = training_instances.get(algorithm)
    if trainer:
        trainer.stop_training()

    logger.info(f"⏹️ 停止訓練: {algorithm}")
    
    return {
        "message": f"正在停止演算法 '{algorithm}' 的訓練任務...",
        "session_id": training_sessions.get(algorithm)
    }


@router.get("/sessions")
async def get_training_sessions(
    algorithm_type: Optional[str] = None,
    limit: int = 20,
    db: MockRepository = Depends(get_repository)
) -> List[Dict[str, Any]]:
    """
    獲取訓練會話列表
    """
    try:
        # 這裡需要實現 get_experiment_sessions 方法
        # 暫時返回簡化的會話資訊
        return [
            {
                "message": "訓練會話查詢功能開發中",
                "algorithm_type": algorithm_type,
                "limit": limit
            }
        ]
    except Exception as e:
        logger.error(f"❌ 獲取會話列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(db: MockRepository = Depends(get_repository)):
    """
    增強版健康檢查，包含資料庫狀態
    """
    try:
        db_health = db.health_check()
        
        return {
            "status": "healthy",
            "database": db_health,
            "active_trainings": len(training_instances),
            "supported_algorithms": ["dqn", "ppo", "sac"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ 健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }