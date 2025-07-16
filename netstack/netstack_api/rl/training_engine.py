"""
🤖 RL 訓練引擎 - Phase 1.3a 統一架構實現

將原本在 RL System (port 8001) 中的訓練邏輯整合到 NetStack (port 8080) 中，
實現單一 Port 架構，解決雙重 RL 系統問題。
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import hashlib

# 必要的資料庫導入
try:
    import motor.motor_asyncio
    from bson import ObjectId

    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# 導入 RL System 的核心組件
try:
    from ..services.rl_training.core.algorithm_factory import get_algorithm
    from ..services.rl_training.interfaces.rl_algorithm import ScenarioType, IRLAlgorithm
    from ..services.rl_training.interfaces.data_repository import (
        IDataRepository as RLDataRepository,
        ExperimentSession,
    )

    RL_SYSTEM_AVAILABLE = True
except ImportError as e:
    RL_SYSTEM_AVAILABLE = False
    logging.getLogger(__name__).warning(f"RL System 組件不可用: {e}")
    
    # 提供備用定義以防導入失敗
    from dataclasses import dataclass
    from typing import Any, Dict
    from datetime import datetime
    from enum import Enum
    
    @dataclass
    class ExperimentSession:
        """備用實驗會話實體"""
        id: Optional[int] = None
        experiment_name: str = ""
        algorithm_type: str = ""
        scenario_type: str = "unknown"
        researcher_id: str = ""
        start_time: datetime = None
        total_episodes: int = 0
        session_status: str = "unknown"
        config_hash: str = ""
        hyperparameters: Dict[str, Any] = None
        environment_config: Dict[str, Any] = None
        research_notes: Optional[str] = None
        created_at: datetime = None
        
    class IRLAlgorithm:
        """備用 RL 算法介面"""
        pass
        
    class RLDataRepository:
        """備用資料儲存庫"""
        pass
        
    def get_algorithm(*args, **kwargs):
        """備用算法工廠函數"""
        return None
        
    class ScenarioType(Enum):
        """備用場景類型"""
        UNKNOWN = "unknown"

logger = logging.getLogger(__name__)


class TrainingStatus(Enum):
    """訓練狀態枚舉"""

    IDLE = "idle"
    QUEUED = "queued"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"


class AlgorithmType(Enum):
    """支援的算法類型"""

    DQN = "dqn"
    PPO = "ppo"
    SAC = "sac"


@dataclass
class TrainingConfig:
    """訓練配置"""

    total_episodes: int = 100
    step_time: float = 0.1
    experiment_name: Optional[str] = None
    scenario_type: str = "urban"
    researcher_id: str = "system"
    research_notes: Optional[str] = None
    environment: str = "CartPole-v1"  # 使用標準環境進行測試
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class TrainingSession:
    """訓練會話"""

    session_id: str
    algorithm_name: str
    status: TrainingStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    episodes_target: int = 0
    episodes_completed: int = 0
    current_reward: float = 0.0
    best_reward: float = float("-inf")
    config: Optional[TrainingConfig] = None
    error_message: Optional[str] = None


class IDataRepository(ABC):
    """數據儲存庫抽象介面"""

    @abstractmethod
    async def create_experiment_session(self, session: Any) -> int:
        """創建實驗會話"""
        pass

    @abstractmethod
    async def update_experiment_session(
        self, session_id: int, updates: Dict[str, Any]
    ) -> bool:
        """更新實驗會話"""
        pass

    @abstractmethod
    async def get_database_health(self) -> Dict[str, Any]:
        """獲取數據庫健康狀態"""
        pass


class MongoDBRepository(IDataRepository):
    """MongoDB 數據儲存庫 - Phase 1.3a 新增"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client = None
        self.db = None
        self.initialized = False

    async def initialize(self) -> bool:
        """初始化 MongoDB 連接"""
        try:
            import motor.motor_asyncio

            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            self.db = self.client.rl_system

            # 測試連接
            await self.client.admin.command("ping")
            self.initialized = True

            logger.info("✅ MongoDB 連接成功")
            return True

        except Exception as e:
            logger.error(f"❌ MongoDB 連接失敗: {e}")
            return False

    async def create_experiment_session(self, session: Any) -> int:
        """創建實驗會話"""
        if not self.initialized:
            raise RuntimeError("MongoDB 未初始化")

        session_doc = {
            "experiment_name": session.experiment_name,
            "algorithm_type": session.algorithm_type,
            "scenario_type": (
                session.scenario_type.value
                if hasattr(session.scenario_type, "value")
                else str(session.scenario_type)
            ),
            "researcher_id": session.researcher_id,
            "start_time": session.start_time,
            "total_episodes": session.total_episodes,
            "session_status": session.session_status,
            "config_hash": session.config_hash,
            "hyperparameters": session.hyperparameters,
            "environment_config": session.environment_config,
            "research_notes": session.research_notes,
            "created_at": datetime.now(),
        }

        result = await self.db.experiment_sessions.insert_one(session_doc)
        return str(result.inserted_id)  # MongoDB 使用 ObjectId

    async def update_experiment_session(
        self, session_id: str, updates: Dict[str, Any]
    ) -> bool:
        """更新實驗會話"""
        if not self.initialized:
            raise RuntimeError("MongoDB 未初始化")

        try:
            from bson import ObjectId

            result = await self.db.experiment_sessions.update_one(
                {"_id": ObjectId(session_id)}, {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"更新實驗會話失敗: {e}")
            return False

    async def get_database_health(self) -> Dict[str, Any]:
        """獲取數據庫健康狀態"""
        if not self.initialized:
            return {"status": "disconnected", "error": "MongoDB 未初始化"}

        try:
            server_info = await self.client.admin.command("buildInfo")
            return {
                "status": "healthy",
                "version": server_info.get("version", "unknown"),
                "connection": "active",
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class MockRepository(IDataRepository):
    """模擬數據儲存庫 - 用於測試和開發"""

    def __init__(self):
        self.sessions = {}
        self.session_counter = 1

    async def create_experiment_session(self, session: Any) -> int:
        """創建實驗會話"""
        session_id = self.session_counter
        self.sessions[session_id] = {
            "id": session_id,
            "experiment_name": session.experiment_name,
            "algorithm_type": session.algorithm_type,
            "start_time": session.start_time,
            "status": session.session_status,
            "created_at": datetime.now(),
        }
        self.session_counter += 1
        return session_id

    async def update_experiment_session(
        self, session_id: int, updates: Dict[str, Any]
    ) -> bool:
        """更新實驗會話"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            return True
        return False

    async def get_database_health(self) -> Dict[str, Any]:
        """獲取數據庫健康狀態"""
        return {
            "status": "healthy",
            "type": "mock",
            "sessions_count": len(self.sessions),
        }


class RLTrainingEngine:
    """
    RL 訓練引擎 - Phase 1.3a 統一架構核心

    整合原本分散在 NetStack RL 監控路由器和 RL System 中的功能：
    1. 統一 API 端點管理
    2. 真實的算法訓練邏輯
    3. 數據持久化 (MongoDB)
    4. 訓練會話管理
    """

    def __init__(self):
        self.active_sessions: Dict[str, TrainingSession] = {}
        self.background_tasks: Dict[str, asyncio.Task] = {}
        self.training_instances: Dict[str, Any] = {}
        self.repository: Optional[IDataRepository] = None
        self.initialized = False

    async def initialize(self) -> bool:
        """初始化訓練引擎"""
        try:
            # 優先使用 MongoDB，失敗時降級到 Mock
            mongodb_url = os.getenv(
                "MONGODB_URL", 
                os.getenv("DATABASE_URL", "mongodb://localhost:27017/rl_system")
            )

            try:
                self.repository = MongoDBRepository(mongodb_url)
                if await self.repository.initialize():
                    logger.info("✅ RLTrainingEngine: MongoDB 數據庫已連接")
                else:
                    raise Exception("MongoDB 初始化失敗")
            except Exception as e:
                logger.warning(f"⚠️ MongoDB 不可用，回退到 Mock Repository: {e}")
                # 暫時回退到 Mock Repository 以允許系統運行
                self.repository = MockRepository()
                logger.info("✅ RLTrainingEngine: Mock Repository 已連接")

            self.initialized = True
            logger.info("🚀 RLTrainingEngine 初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ RLTrainingEngine 初始化失敗: {e}")
            return False

    def generate_session_id(self, algorithm_name: str) -> str:
        """生成會話 ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"training_{algorithm_name}_{timestamp}"

    async def start_training(
        self,
        algorithm_name: str,
        episodes: int = 100,
        experiment_name: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        啟動訓練 - 統一的訓練啟動接口

        Args:
            algorithm_name: 算法名稱 (dqn, ppo, sac)
            episodes: 訓練回合數
            experiment_name: 實驗名稱
            custom_config: 自定義配置

        Returns:
            Dict: 包含 session_id 和狀態資訊的字典
        """
        logger.info(f"🚀 [訓練引擎] 收到啟動訓練請求: {algorithm_name}, episodes={episodes}")
        
        if not self.initialized:
            logger.error("❌ [訓練引擎] RLTrainingEngine 未初始化")
            raise RuntimeError("RLTrainingEngine 未初始化")

        logger.info(f"🔍 [訓練引擎] 檢查是否已有 {algorithm_name} 的活躍訓練...")
        # 檢查是否已有相同算法的活躍訓練
        active_session = self._get_active_session_by_algorithm(algorithm_name)
        if active_session:
            logger.warning(f"⚠️ [訓練引擎] 算法 {algorithm_name} 已有活躍會話: {active_session.session_id}")
            raise ValueError(
                f"算法 '{algorithm_name}' 已有活躍的訓練會話: {active_session.session_id}"
            )
        
        logger.info(f"✅ [訓練引擎] 無衝突會話，可以創建新的 {algorithm_name} 訓練會話")

        # 創建訓練配置
        config = TrainingConfig(
            total_episodes=episodes,
            experiment_name=experiment_name
            or f"{algorithm_name}_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            custom_config=custom_config or {},
        )

        # 生成會話 ID
        session_id = self.generate_session_id(algorithm_name)

        # 創建訓練會話
        session = TrainingSession(
            session_id=session_id,
            algorithm_name=algorithm_name,
            status=TrainingStatus.QUEUED,
            start_time=datetime.now(),
            episodes_target=episodes,
            config=config,
        )

        try:
            # 如果有 RL System 組件，使用真實算法
            if RL_SYSTEM_AVAILABLE:
                # 創建數據庫會話記錄
                if hasattr(self.repository, "create_experiment_session"):
                    experiment_session = ExperimentSession(
                        id=None,
                        experiment_name=config.experiment_name,
                        algorithm_type=algorithm_name,
                        scenario_type=ScenarioType.URBAN,  # 默認場景
                        paper_reference=None,
                        researcher_id=config.researcher_id,
                        start_time=session.start_time,
                        end_time=None,
                        total_episodes=episodes,
                        session_status="queued",
                        config_hash=hashlib.sha256(
                            str(config.__dict__).encode()
                        ).hexdigest(),
                        hyperparameters=config.custom_config or {},
                        environment_config={"env_name": config.environment},
                        research_notes=config.research_notes,
                        created_at=datetime.now(),
                    )
                    db_session_id = await self.repository.create_experiment_session(
                        experiment_session
                    )
                    session.session_id = f"{session_id}_{db_session_id}"

                # 創建算法訓練器
                algorithm_config = {
                    "total_episodes": episodes,
                    "step_time": config.step_time,
                    **config.custom_config,
                }
                trainer = get_algorithm(
                    algorithm_name, config.environment, algorithm_config
                )
                self.training_instances[session_id] = trainer

            else:
                # 如果沒有 RL System，使用模擬訓練
                logger.warning(f"⚠️ RL System 不可用，使用模擬訓練: {algorithm_name}")

            # 將會話添加到管理器
            logger.info(f"📝 [訓練引擎] 將會話添加到管理器: {session_id}")
            self.active_sessions[session_id] = session

            # 啟動背景訓練任務
            logger.info(f"🚀 [訓練引擎] 啟動背景訓練任務...")
            task = asyncio.create_task(self._run_training_loop(session))
            self.background_tasks[session_id] = task
            logger.info(f"✅ [訓練引擎] 背景任務已創建並啟動: {session_id}")

            logger.info(f"🏃‍♂️ [訓練引擎] 訓練會話已啟動: {session_id} (算法: {algorithm_name})")
            logger.info(f"📊 [訓練引擎] 當前活躍會話數: {len(self.active_sessions)}")

            return {
                "session_id": session_id,
                "algorithm": algorithm_name,
                "status": "queued",
                "episodes_target": episodes,
                "message": f"算法 '{algorithm_name}' 訓練已啟動",
            }

        except Exception as e:
            logger.error(f"❌ 啟動訓練失敗: {e}")
            # 清理失敗的會話
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            raise

    async def _run_training_loop(self, session: TrainingSession) -> None:
        """執行訓練循環"""
        session_id = session.session_id
        algorithm_name = session.algorithm_name

        try:
            # 更新狀態為活躍
            logger.info(f"🔄 [訓練循環] 更新 {session_id} 狀態為 ACTIVE")
            session.status = TrainingStatus.ACTIVE
            logger.info(f"🏃‍♂️ [訓練循環] 開始訓練循環: {session_id}")

            # 更新數據庫狀態
            if self.repository:
                logger.info(f"💾 [訓練循環] 更新數據庫狀態為 active: {session_id}")
                await self.repository.update_experiment_session(
                    session_id,
                    {"session_status": "active", "start_time": datetime.now()},
                )
                logger.info(f"✅ [訓練循環] 數據庫狀態更新完成: {session_id}")

            # 執行訓練
            if RL_SYSTEM_AVAILABLE and session_id in self.training_instances:
                # 使用真實算法訓練
                logger.info(f"🧠 [訓練循環] 使用真實算法訓練: {algorithm_name}")
                trainer = self.training_instances[session_id]
                await self._run_real_training(session, trainer)
            else:
                # 使用模擬訓練
                logger.info(f"🎭 [訓練循環] 使用模擬訓練: {algorithm_name}")
                await self._run_mock_training(session)

            # 訓練完成
            session.status = TrainingStatus.COMPLETED
            session.end_time = datetime.now()

            if self.repository:
                await self.repository.update_experiment_session(
                    session_id,
                    {
                        "session_status": "completed",
                        "end_time": session.end_time,
                        "episodes_completed": session.episodes_completed,
                        "final_reward": session.current_reward,
                    },
                )

            logger.info(f"✅ 訓練完成: {session_id}")

        except asyncio.CancelledError:
            # 訓練被取消
            session.status = TrainingStatus.STOPPED
            session.end_time = datetime.now()
            logger.info(f"⏹️ 訓練已停止: {session_id}")

        except Exception as e:
            # 訓練出錯
            session.status = TrainingStatus.ERROR
            session.error_message = str(e)
            session.end_time = datetime.now()
            logger.error(f"❌ 訓練出錯: {session_id}, 錯誤: {e}")

        finally:
            # 清理資源
            if session_id in self.training_instances:
                del self.training_instances[session_id]
            if session_id in self.background_tasks:
                del self.background_tasks[session_id]

    async def _run_real_training(self, session: TrainingSession, trainer: Any) -> None:
        """使用真實算法進行訓練"""
        for episode in range(session.episodes_target):
            # 檢查是否需要停止
            if session.status != TrainingStatus.ACTIVE:
                break

            # 執行一個 episode
            trainer.train()
            status = trainer.get_status()

            # 更新進度
            session.episodes_completed = episode + 1
            session.current_reward = status.get("current_reward", 0.0)
            if session.current_reward > session.best_reward:
                session.best_reward = session.current_reward

            # 控制訓練速度
            if session.config and session.config.step_time:
                await asyncio.sleep(session.config.step_time)

    async def _run_mock_training(self, session: TrainingSession) -> None:
        """模擬訓練循環"""
        import random
        import math

        logger.info(f"🎭 [模擬訓練] 開始模擬訓練: {session.session_id}, 目標 episodes: {session.episodes_target}")
        
        for episode in range(session.episodes_target):
            # 檢查是否需要停止
            if session.status != TrainingStatus.ACTIVE:
                logger.info(f"🛑 [模擬訓練] 訓練狀態非 ACTIVE，停止訓練: {session.status}")
                break

            # 模擬訓練進度
            progress = episode / session.episodes_target

            # 模擬獎勵變化
            base_reward = -50.0 + (progress * 400.0)
            variance = max(5, 30 * (1 - progress))
            noise = random.uniform(-variance, variance)
            breakthrough = random.uniform(10, 30) if random.random() < 0.05 else 0

            current_reward = base_reward + noise + breakthrough

            # 更新會話狀態
            session.episodes_completed = episode + 1
            session.current_reward = current_reward
            if current_reward > session.best_reward:
                session.best_reward = current_reward

            # 每10個episode記錄一次詳細進度
            if episode % 10 == 0 or episode == session.episodes_target - 1:
                logger.info(f"📊 [模擬訓練] {session.session_id} - Episode {episode+1}/{session.episodes_target} "
                           f"(進度: {progress:.1%}, 獎勵: {current_reward:.2f}, 最佳: {session.best_reward:.2f})")

            # 控制訓練速度
            step_time = session.config.step_time if session.config else 0.1
            await asyncio.sleep(step_time)
            
        logger.info(f"🏁 [模擬訓練] 訓練完成: {session.session_id}, 最終 episodes: {session.episodes_completed}/{session.episodes_target}")

    async def stop_training(self, session_id: str) -> Dict[str, Any]:
        """停止訓練"""
        if session_id not in self.active_sessions:
            raise ValueError(f"訓練會話 '{session_id}' 不存在")

        session = self.active_sessions[session_id]
        if session.status != TrainingStatus.ACTIVE:
            raise ValueError(f"訓練會話 '{session_id}' 不是活躍狀態")

        # 取消背景任務
        if session_id in self.background_tasks:
            task = self.background_tasks[session_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        return {
            "session_id": session_id,
            "status": "stopped",
            "message": f"訓練會話 '{session_id}' 已停止",
        }

    def get_training_status(self, session_id: str) -> Dict[str, Any]:
        """獲取訓練狀態"""
        logger.info(f"📊 [狀態查詢] 查詢訓練狀態: {session_id}")
        
        if session_id not in self.active_sessions:
            logger.warning(f"⚠️ [狀態查詢] 訓練會話不存在: {session_id}")
            logger.info(f"🔍 [狀態查詢] 當前活躍會話: {list(self.active_sessions.keys())}")
            raise ValueError(f"訓練會話 '{session_id}' 不存在")

        session = self.active_sessions[session_id]
        progress = (
            (session.episodes_completed / session.episodes_target * 100)
            if session.episodes_target > 0
            else 0
        )

        status_data = {
            "session_id": session_id,
            "algorithm_name": session.algorithm_name,
            "status": session.status.value,
            "progress": progress,
            "episodes_completed": session.episodes_completed,
            "episodes_target": session.episodes_target,
            "current_reward": session.current_reward,
            "best_reward": session.best_reward,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "error_message": session.error_message,
        }
        
        logger.info(f"✅ [狀態查詢] 返回狀態: {session_id} - {session.status.value}, 進度: {progress:.1f}%")
        return status_data

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """獲取所有訓練會話"""
        logger.info(f"📋 [全部會話] 查詢所有訓練會話，當前活躍會話數: {len(self.active_sessions)}")
        
        all_sessions = [
            self.get_training_status(session_id)
            for session_id in self.active_sessions.keys()
        ]
        
        logger.info(f"✅ [全部會話] 返回 {len(all_sessions)} 個會話狀態")
        return all_sessions

    def _get_active_session_by_algorithm(
        self, algorithm_name: str
    ) -> Optional[TrainingSession]:
        """根據算法名稱查找活躍會話"""
        for session in self.active_sessions.values():
            if (
                session.algorithm_name == algorithm_name
                and session.status == TrainingStatus.ACTIVE
            ):
                return session
        return None

    async def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        db_health = (
            await self.repository.get_database_health()
            if self.repository
            else {"status": "unavailable"}
        )

        return {
            "status": "healthy" if self.initialized else "unhealthy",
            "engine_initialized": self.initialized,
            "rl_system_available": RL_SYSTEM_AVAILABLE,
            "active_sessions": len(self.active_sessions),
            "available_algorithms": [algo.value for algo in AlgorithmType],
            "database_health": db_health,
        }


# 全局訓練引擎實例
_training_engine: Optional[RLTrainingEngine] = None


async def get_training_engine() -> RLTrainingEngine:
    """獲取訓練引擎實例（單例模式）"""
    global _training_engine

    if _training_engine is None:
        _training_engine = RLTrainingEngine()
        await _training_engine.initialize()
    elif not _training_engine.initialized:
        # 如果實例存在但未初始化，重新初始化
        await _training_engine.initialize()

    return _training_engine


async def cleanup_training_engine():
    """清理訓練引擎資源"""
    global _training_engine

    if _training_engine:
        # 停止所有活躍的訓練會話
        for session_id in list(_training_engine.active_sessions.keys()):
            try:
                await _training_engine.stop_training(session_id)
            except Exception as e:
                logger.error(f"清理訓練會話失敗: {session_id}, 錯誤: {e}")

        _training_engine = None
        logger.info("🧹 RLTrainingEngine 資源已清理")
