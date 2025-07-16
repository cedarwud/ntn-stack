"""
🧠 RL 監控路由器

為前端 RL 監控儀表板提供 API 端點，支持訓練狀態監控、算法管理和性能分析。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import psutil

try:
    import GPUtil

    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# 導入新的 RL 訓練模型
from ..models.rl_training_models import (
    TrainingStatus,
    AlgorithmType,
    EnvironmentType,
    ModelStatus,
    RLTrainingSession,
    RLTrainingEpisode,
    RLAlgorithmPerformance,
    RLModelVersion,
    TrainingSessionResponse,
    TrainingEpisodeResponse,
    AlgorithmPerformanceResponse,
    StartTrainingRequest,
    UpdateTrainingRequest,
)

# 嘗試導入算法生態系統組件
try:
    from ..algorithm_ecosystem import AlgorithmEcosystemManager

    ECOSYSTEM_AVAILABLE = True

    # 嘗試導入可選組件
    try:
        from ..algorithm_ecosystem import PerformanceAnalysisEngine

        ANALYSIS_ENGINE_AVAILABLE = True
    except ImportError:
        ANALYSIS_ENGINE_AVAILABLE = False

        class PerformanceAnalysisEngine:
            def __init__(self, *args, **kwargs):
                pass

    try:
        from ..algorithm_ecosystem import RLTrainingPipeline

        TRAINING_PIPELINE_AVAILABLE = True
    except ImportError:
        TRAINING_PIPELINE_AVAILABLE = False

        class RLTrainingPipeline:
            def __init__(self, *args, **kwargs):
                pass

except ImportError:
    ECOSYSTEM_AVAILABLE = False
    ANALYSIS_ENGINE_AVAILABLE = False
    TRAINING_PIPELINE_AVAILABLE = False
    # 定義類型別名避免運行時錯誤
    AlgorithmEcosystemManager = None
    PerformanceAnalysisEngine = None
    RLTrainingPipeline = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rl", tags=["RL 監控"])

# 全局變量
ecosystem_manager: Optional[Any] = None
ecosystem_manager_initialized: bool = False
training_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/training/clear")
async def clear_all_training_sessions() -> Dict[str, Any]:
    """清除所有訓練會話（用於重置）"""
    global training_sessions
    count = len(training_sessions)
    training_sessions.clear()
    return {"message": "所有訓練會話已清除", "count": count}


@router.post("/training/clear/{status}")
async def clear_sessions_by_status(status: str):
    """根據狀態清除訓練會話"""
    global training_sessions
    valid_statuses = ["completed", "stopped", "error"]

    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"無效的狀態: {status}。有效狀態: {', '.join(valid_statuses)}",
        )

    sessions_to_remove = []
    for session_id, session in training_sessions.items():
        if session["status"] == status:
            sessions_to_remove.append(session_id)

    for session_id in sessions_to_remove:
        del training_sessions[session_id]

    return {
        "message": f"已清除 {len(sessions_to_remove)} 個狀態為 '{status}' 的會話",
        "count": len(sessions_to_remove),
        "status": status,
    }


@router.delete("/training/session/{session_id}")
async def delete_training_session(session_id: str):
    """刪除特定的訓練會話"""
    global training_sessions

    if session_id not in training_sessions:
        raise HTTPException(status_code=404, detail=f"訓練會話 '{session_id}' 不存在")

    session_status = training_sessions[session_id]["status"]
    if session_status == "active":
        raise HTTPException(
            status_code=409,
            detail=f"無法刪除活躍的訓練會話。請先停止訓練會話 '{session_id}'",
        )

    del training_sessions[session_id]
    return {
        "message": f"訓練會話 '{session_id}' 已刪除",
        "session_id": session_id,
        "previous_status": session_status,
    }


# 清理舊的訓練會話
def cleanup_old_sessions():
    """清理舊的訓練會話"""
    global training_sessions
    current_time = datetime.now()
    sessions_to_remove = []

    logger.debug(f"開始清理會話檢查，當前時間: {current_time}")

    for session_id, session in training_sessions.items():
        time_diff = current_time - session["start_time"]
        logger.debug(
            f"檢查會話 {session_id}: 狀態={session['status']}, 運行時間={time_diff.total_seconds():.1f}秒"
        )

        # 新的清理策略：
        # 1. 已完成的會話保留 24 小時（讓用戶查看結果）
        # 2. 手動停止的會話保留 1 小時
        # 3. 錯誤狀態的會話保留 30 分鐘（方便除錯）
        # 4. 活躍會話不自動清理（只能手動停止或訓練完成）
        if session["status"] == "completed":
            if time_diff.total_seconds() > 86400:  # 24 小時
                sessions_to_remove.append(session_id)
        elif session["status"] == "stopped":
            if time_diff.total_seconds() > 3600:  # 1 小時
                sessions_to_remove.append(session_id)
        elif session["status"] == "error":
            if time_diff.total_seconds() > 1800:  # 30 分鐘
                sessions_to_remove.append(session_id)
        # 活躍會話永不自動清理 - 只能透過手動停止或自然完成

    for session_id in sessions_to_remove:
        if session_id in training_sessions:
            session_status = training_sessions[session_id]["status"]
            logger.info(f"清理訓練會話: {session_id} (狀態: {session_status})")
            del training_sessions[session_id]


class RLEngineMetrics(BaseModel):
    """RL 引擎指標數據模型"""

    engine_type: str = Field(..., description="引擎類型 (dqn, ppo, sac, null)")
    algorithm: str = Field(..., description="算法名稱")
    environment: str = Field(..., description="環境名稱")
    model_status: str = Field(
        ..., description="模型狀態 (training, inference, idle, error)"
    )
    episodes_completed: int = Field(0, description="已完成回合數")
    average_reward: float = Field(0.0, description="平均獎勵")
    current_epsilon: float = Field(0.0, description="當前探索率")
    training_progress: float = Field(0.0, description="訓練進度 (0-100)")
    prediction_accuracy: float = Field(0.0, description="預測準確率")
    response_time_ms: float = Field(0.0, description="響應時間 (毫秒)")
    memory_usage: float = Field(0.0, description="記憶體使用率")
    gpu_utilization: Optional[float] = Field(None, description="GPU 使用率")


class SystemResourcesModel(BaseModel):
    """系統資源模型"""

    cpu_usage: float = Field(..., description="CPU 使用率")
    memory_usage: float = Field(..., description="記憶體使用率")
    disk_usage: float = Field(..., description="磁碟使用率")
    gpu_utilization: Optional[float] = Field(None, description="GPU 使用率")
    avg_response_time: float = Field(0.0, description="平均響應時間")


class TrainingSessionModel(BaseModel):
    """訓練會話模型"""

    session_id: str = Field(..., description="會話 ID")
    algorithm_name: str = Field(..., description="算法名稱")
    status: str = Field(..., description="狀態 (active, paused, completed, error)")
    start_time: datetime = Field(..., description="開始時間")
    episodes_target: int = Field(..., description="目標回合數")
    episodes_completed: int = Field(0, description="已完成回合數")
    current_reward: float = Field(0.0, description="當前獎勵")
    best_reward: float = Field(0.0, description="最佳獎勵")


class RLStatusResponse(BaseModel):
    """RL 狀態響應模型"""

    engines: Dict[str, RLEngineMetrics] = Field(..., description="RL 引擎指標")
    system_resources: SystemResourcesModel = Field(..., description="系統資源")
    training_active: bool = Field(False, description="是否有活躍的訓練")
    available_algorithms: List[str] = Field([], description="可用算法列表")


class AIDecisionStatusResponse(BaseModel):
    """AI 決策狀態響應模型"""

    environment: str = Field(..., description="環境名稱")
    training_stats: Dict[str, Any] = Field({}, description="訓練統計")
    prediction_accuracy: float = Field(0.0, description="預測準確率")
    training_progress: float = Field(0.0, description="訓練進度")
    model_version: str = Field("1.0.0", description="模型版本")


class MockEcosystemManager:
    """模擬的生態系統管理器"""

    def __init__(self):
        self.initialized = False
        self.algorithms = ["dqn", "ppo", "sac"]

    async def initialize(self):
        """初始化"""
        self.initialized = True

    def get_registered_algorithms(self):
        """獲取已註冊的算法"""
        return self.algorithms

    async def start_training(self, algorithm_name: str, episodes: int):
        """開始訓練"""
        session_id = (
            f"training_{algorithm_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        # 創建模擬訓練會話並返回會話ID
        return session_id

    async def train_rl_algorithm(self, algorithm_name: str, episodes: int):
        """模擬訓練算法"""
        # 模擬訓練過程
        await asyncio.sleep(1)  # 模擬初始化時間

        # 返回模擬的訓練結果
        return {
            "status": "completed",
            "final_stats": {
                "mean_reward": 250.0 + (episodes * 0.1),
                "episodes_completed": episodes,
                "training_time": episodes * 0.1,
            },
            "best_reward": 300.0 + (episodes * 0.05),
        }

    def get_system_status(self):
        """獲取系統狀態"""
        return {
            "status": "healthy",
            "uptime_seconds": 3600,
            "registered_algorithms": self.algorithms,
            "active_ab_tests": {},
        }


async def get_ecosystem_manager() -> Any:
    """獲取生態系統管理器 - 優化版本，避免重複初始化"""
    global ecosystem_manager, ecosystem_manager_initialized

    if ecosystem_manager is None or not ecosystem_manager_initialized:
        if ECOSYSTEM_AVAILABLE and AlgorithmEcosystemManager is not None:
            # 使用真實的生態系統管理器
            ecosystem_manager = AlgorithmEcosystemManager()
            await ecosystem_manager.initialize()
        else:
            # 使用模擬的生態系統管理器
            ecosystem_manager = MockEcosystemManager()
            await ecosystem_manager.initialize()
        
        ecosystem_manager_initialized = True

    return ecosystem_manager


def get_system_resources() -> SystemResourcesModel:
    """獲取系統資源信息"""
    try:
        # CPU 使用率 - 使用非阻塞模式避免 1 秒延遲
        cpu_usage = psutil.cpu_percent(interval=None)

        # 記憶體使用率
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # 磁碟使用率
        disk = psutil.disk_usage("/")
        disk_usage = (disk.used / disk.total) * 100

        # GPU 使用率
        gpu_utilization = None
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_utilization = gpus[0].load * 100
            except Exception:
                pass

        return SystemResourcesModel(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            gpu_utilization=gpu_utilization,
            avg_response_time=50.0,  # 預設值，可以從實際指標中獲取
        )

    except Exception as e:
        logger.error(f"獲取系統資源失敗: {e}")
        return SystemResourcesModel(
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            gpu_utilization=None,
            avg_response_time=0.0,
        )


def create_mock_rl_metrics(engine_type: str, algorithm: str) -> RLEngineMetrics:
    """創建模擬 RL 指標（當實際訓練不活躍時使用）"""
    import random

    base_episode = random.randint(1000, 5000)
    base_reward = random.uniform(-100, 300)

    return RLEngineMetrics(
        engine_type=engine_type,
        algorithm=algorithm,
        environment="LEOSatelliteHandoverEnv-v1",
        model_status="idle",
        episodes_completed=base_episode,
        average_reward=base_reward,
        current_epsilon=random.uniform(0.01, 0.3),
        training_progress=random.uniform(60, 95),
        prediction_accuracy=random.uniform(0.75, 0.92),
        response_time_ms=random.uniform(20, 80),
        memory_usage=random.uniform(30, 70),
        gpu_utilization=random.uniform(0, 20) if GPU_AVAILABLE else None,
    )


@router.get("/status", response_model=RLStatusResponse)
async def get_rl_status():
    """獲取 RL 系統狀態"""
    try:
        manager = await get_ecosystem_manager()

        # 獲取已註冊的算法
        available_algorithms = manager.get_registered_algorithms()

        # 獲取系統狀態
        system_status = manager.get_system_status()

        # 構建引擎指標
        engines = {}
        training_active = False

        # 檢查是否有活躍的訓練
        active_ab_tests = system_status.get("active_ab_tests", {})
        training_active = len(active_ab_tests) > 0 or len(training_sessions) > 0

        # 為主要的 RL 算法創建指標
        rl_algorithms = ["dqn_handover", "ppo_handover", "sac_handover"]

        for algorithm in rl_algorithms:
            if algorithm in available_algorithms:
                engine_type = algorithm.split("_")[0]  # 提取引擎類型

                # 嘗試從訓練會話獲取真實數據
                real_metrics = None
                for session_id, session in training_sessions.items():
                    if session["algorithm_name"] == algorithm:
                        real_metrics = session
                        break

                if real_metrics:
                    engines[engine_type] = RLEngineMetrics(
                        engine_type=engine_type,
                        algorithm=algorithm,
                        environment="LEOSatelliteHandoverEnv-v1",
                        model_status=(
                            "training" if real_metrics["status"] == "active" else "idle"
                        ),
                        episodes_completed=real_metrics["episodes_completed"],
                        average_reward=real_metrics["current_reward"],
                        current_epsilon=0.1,  # 可以從算法實例獲取
                        training_progress=(
                            real_metrics["episodes_completed"]
                            / real_metrics["episodes_target"]
                        )
                        * 100,
                        prediction_accuracy=0.85,  # 可以從性能分析引擎獲取
                        response_time_ms=50.0,
                        memory_usage=psutil.virtual_memory().percent,
                        gpu_utilization=None,
                    )
                else:
                    engines[engine_type] = create_mock_rl_metrics(
                        engine_type, algorithm
                    )

        # 如果沒有 RL 算法，創建空引擎
        if not engines:
            engines["null"] = RLEngineMetrics(
                engine_type="null",
                algorithm="none",
                environment="none",
                model_status="idle",
                episodes_completed=0,
                average_reward=0.0,
                current_epsilon=0.0,
                training_progress=0.0,
                prediction_accuracy=0.0,
                response_time_ms=0.0,
                memory_usage=0.0,
                gpu_utilization=None,
            )

        return RLStatusResponse(
            engines=engines,
            system_resources=get_system_resources(),
            training_active=training_active,
            available_algorithms=available_algorithms,
        )

    except Exception as e:
        logger.error(f"獲取 RL 狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取 RL 狀態失敗: {str(e)}")


@router.get("/ai-decision/status", response_model=AIDecisionStatusResponse)
async def get_ai_decision_status():
    """獲取 AI 決策系統狀態"""
    try:
        manager = await get_ecosystem_manager()
        system_status = manager.get_system_status()

        # 計算整體訓練進度
        total_progress = 0.0
        algorithm_count = 0

        for session in training_sessions.values():
            if session["status"] == "active":
                progress = (
                    session["episodes_completed"] / session["episodes_target"]
                ) * 100
                total_progress += progress
                algorithm_count += 1

        overall_progress = (
            total_progress / algorithm_count if algorithm_count > 0 else 0.0
        )

        # 構建訓練統計
        training_stats = {
            "active_sessions": len(
                [s for s in training_sessions.values() if s["status"] == "active"]
            ),
            "total_sessions": len(training_sessions),
            "algorithms_available": len(system_status.get("registered_algorithms", [])),
            "system_uptime_hours": system_status.get("uptime_seconds", 0) / 3600,
        }

        return AIDecisionStatusResponse(
            environment="LEOSatelliteHandoverEnv-v1",
            training_stats=training_stats,
            prediction_accuracy=0.87,  # 可以從分析引擎獲取實際數據
            training_progress=overall_progress,
            model_version="2.0.0",
        )

    except Exception as e:
        logger.error(f"獲取 AI 決策狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取 AI 決策狀態失敗: {str(e)}")


@router.get("/training/sessions", response_model=List[TrainingSessionModel])
async def get_training_sessions():
    """獲取訓練會話列表 - 使用統一的 RLTrainingEngine"""
    logger.info("📋 [會話列表] 收到前端獲取訓練會話列表請求")
    
    try:
        # 使用統一的 RLTrainingEngine
        from ..rl.training_engine import get_training_engine

        logger.info("🔧 [會話列表] 獲取 RLTrainingEngine...")
        engine = await get_training_engine()
        logger.info("✅ [會話列表] RLTrainingEngine 獲取成功")

        # 獲取所有會話
        logger.info("📊 [會話列表] 調用 engine.get_all_sessions()...")
        sessions_data = engine.get_all_sessions()
        logger.info(f"🔍 [會話列表] 獲取到原始數據: {sessions_data}")
        logger.info(f"✅ [會話列表] 獲取到 {len(sessions_data)} 個會話")

        sessions = []
        for session_data in sessions_data:
            logger.info(f"🔍 [會話列表] 會話數據: {session_data}")
            sessions.append(
                TrainingSessionModel(
                    session_id=session_data["session_id"],
                    algorithm_name=session_data["algorithm_name"],  # 修正：使用正確的鍵名
                    status=session_data["status"],
                    start_time=session_data["start_time"],
                    episodes_target=session_data["episodes_target"],
                    episodes_completed=session_data["episodes_completed"],
                    current_reward=session_data["current_reward"],
                    best_reward=session_data["best_reward"],
                )
            )

        return sessions

    except Exception as e:
        logger.error(f"獲取訓練會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取訓練會話失敗: {str(e)}")


@router.post("/training/start/{algorithm_name}", response_model=None)
async def start_training(
    algorithm_name: str,
    background_tasks: BackgroundTasks,
    episodes: int = Query(1000, description="訓練回合數"),
) -> Dict[str, Any]:
    """啟動算法訓練 - 使用統一的 RLTrainingEngine"""
    logger.info(f"🚀🚀🚀 [RL監控路由] 收到啟動 {algorithm_name} 訓練請求, episodes={episodes}")
    print(f"🚀🚀🚀 [RL監控路由] 收到啟動 {algorithm_name} 訓練請求, episodes={episodes}")
    
    try:
        # 使用統一的 RLTrainingEngine
        from ..rl.training_engine import get_training_engine

        logger.info(f"🔧 [後端] 獲取 RLTrainingEngine...")
        engine = await get_training_engine()
        logger.info(f"✅ [後端] RLTrainingEngine 獲取成功: {type(engine)}")

        # 定義實驗名稱
        experiment_name = f"{algorithm_name.upper()}_前端啟動_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"📝 [後端] 實驗名稱: {experiment_name}")

        # 啟動訓練
        logger.info(f"▶️ [後端] 調用 engine.start_training...")
        result = await engine.start_training(
            algorithm_name=algorithm_name.lower(),
            episodes=episodes,
            experiment_name=experiment_name,
            custom_config={"step_time": 0.1},  # 較快的訓練速度以便前端觀察
        )

        session_id = result.get("session_id")
        logger.info(f"✅ [後端] 訓練啟動成功, session_id={session_id}, result={result}")

        # 記錄到訓練會話（移到 return 之前）
        if session_id:
            training_sessions[session_id] = {
                "algorithm_name": algorithm_name,
                "status": "active",
                "start_time": datetime.now(),
                "episodes_target": episodes,
                "episodes_completed": 0,
                "current_reward": 0.0,
                "best_reward": -1000.0,  # 使用有限的數字而非 -inf
            }
            logger.info(f"📋 [後端] 會話已記錄: {training_sessions[session_id]}")

        # 在背景啟動訓練（如果有額外的訓練任務）
        if 'manager' in globals():
            background_tasks.add_task(
                run_training_session, manager, session_id, algorithm_name, episodes
            )
            logger.info(f"🎯 [後端] 背景任務已添加")

        response = {
            "message": f"演算法 '{algorithm_name}' 的訓練已啟動。",
            "session_id": session_id,
            "algorithm": result.get("algorithm", algorithm_name),
            "status": result.get("status", "queued"),
            "episodes_target": episodes,
            "unified_engine": True,  # 標識使用統一引擎
        }
        
        logger.info(f"📤 [後端] 返回響應: {response}")
        return response

        return {
            "message": f"算法 '{algorithm_name}' 訓練已啟動",
            "session_id": session_id,
            "episodes": episodes,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動訓練失敗: {str(e)}")


@router.post("/training/stop/{session_id}")
async def stop_training(session_id: str) -> Dict[str, Any]:
    """停止訓練會話 - 使用統一的 RLTrainingEngine"""
    try:
        # 使用統一的 RLTrainingEngine
        from ..rl.training_engine import get_training_engine

        engine = await get_training_engine()

        # 停止訓練
        result = await engine.stop_training(session_id)

        return {
            "message": f"訓練會話 '{session_id}' 已停止",
            "session_id": session_id,
            "status": result.get("status", "stopped"),
            "unified_engine": True,  # 標識使用統一引擎
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止訓練失敗: {str(e)}")


@router.post("/training/stop-by-algorithm/{algorithm_name}")
async def stop_training_by_algorithm(algorithm_name: str) -> Dict[str, Any]:
    """根據算法名稱停止訓練"""
    try:
        stopped_sessions = []

        for session_id, session in training_sessions.items():
            if (
                session["algorithm_name"] == algorithm_name
                and session["status"] == "active"
            ):
                session["status"] = "stopped"
                stopped_sessions.append(session_id)
                logger.info(
                    f"根據算法名稱停止訓練會話: {session_id} (算法: {algorithm_name})"
                )

        if not stopped_sessions:
            raise HTTPException(
                status_code=404,
                detail=f"沒有找到算法 '{algorithm_name}' 的活躍訓練會話",
            )

        return {
            "message": f"算法 '{algorithm_name}' 的訓練已停止",
            "algorithm": algorithm_name,
            "stopped_sessions": stopped_sessions,
            "count": len(stopped_sessions),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根據算法停止訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"根據算法停止訓練失敗: {str(e)}")


@router.post("/training/stop-all")
async def stop_all_training() -> Dict[str, Any]:
    """停止所有活躍的訓練會話"""
    try:
        stopped_sessions = []

        for session_id, session in training_sessions.items():
            if session["status"] == "active":
                session["status"] = "stopped"
                stopped_sessions.append(
                    {"session_id": session_id, "algorithm": session["algorithm_name"]}
                )
                logger.info(
                    f"停止所有訓練 - 會話: {session_id} (算法: {session['algorithm_name']})"
                )

        if not stopped_sessions:
            return {
                "message": "沒有活躍的訓練會話需要停止",
                "stopped_sessions": [],
                "count": 0,
            }

        return {
            "message": f"已停止 {len(stopped_sessions)} 個活躍訓練會話",
            "stopped_sessions": stopped_sessions,
            "count": len(stopped_sessions),
        }

    except Exception as e:
        logger.error(f"停止所有訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止所有訓練失敗: {str(e)}")


@router.get("/training/status/{algorithm}")
async def get_training_status(algorithm: str):
    """獲取特定算法的訓練狀態 - 前端所需的關鍵端點"""
    logger.info(f"🔍 [算法狀態] 收到前端查詢 {algorithm} 訓練狀態請求")
    
    try:
        # 使用統一的 RLTrainingEngine 獲取真實狀態
        from ..rl.training_engine import get_training_engine
        
        logger.info("🔧 [算法狀態] 獲取 RLTrainingEngine...")
        engine = await get_training_engine()
        logger.info("✅ [算法狀態] RLTrainingEngine 獲取成功")
        
        # 獲取所有會話
        logger.info("📊 [算法狀態] 調用 engine.get_all_sessions()...")
        sessions_data = engine.get_all_sessions()
        logger.info(f"✅ [算法狀態] 獲取到 {len(sessions_data)} 個會話")
        
        # 查找該算法的最新活躍會話
        algorithm_session = None
        for session_data in sessions_data:
            if session_data["algorithm_name"] == algorithm and session_data["status"] in ["active", "queued"]:
                algorithm_session = session_data
                logger.info(f"✅ [算法狀態] 找到算法 {algorithm} 的活躍會話: {session_data['session_id']}")
                break
        
        if algorithm_session:
            # 構建運行狀態響應
            progress_percentage = (algorithm_session["episodes_completed"] / algorithm_session["episodes_target"] * 100) if algorithm_session["episodes_target"] > 0 else 0
            
            response = {
                "algorithm": algorithm,
                "status": "running", 
                "is_training": True,
                "message": f"演算法 '{algorithm}' 正在訓練中",
                "session_id": algorithm_session["session_id"],
                "training_progress": {
                    "current_episode": algorithm_session["episodes_completed"],
                    "total_episodes": algorithm_session["episodes_target"],
                    "progress_percentage": progress_percentage,
                    "current_reward": algorithm_session["current_reward"],
                    "best_reward": algorithm_session["best_reward"]
                },
                "metrics": {
                    "episodes_completed": algorithm_session["episodes_completed"],
                    "episodes_target": algorithm_session["episodes_target"],
                    "current_reward": algorithm_session["current_reward"],
                    "best_reward": algorithm_session["best_reward"],
                    "start_time": algorithm_session["start_time"].isoformat() if hasattr(algorithm_session["start_time"], 'isoformat') else str(algorithm_session["start_time"])
                },
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📤 [算法狀態] 返回運行狀態: {response}")
            return response
        else:
            # 檢查是否有已完成的會話
            completed_session = None
            for session_data in sessions_data:
                if session_data["algorithm_name"] == algorithm and session_data["status"] in ["completed", "stopped"]:
                    completed_session = session_data
                    break
            
            if completed_session:
                response = {
                    "algorithm": algorithm,
                    "status": "completed",
                    "is_training": False,
                    "message": f"演算法 '{algorithm}' 訓練已完成",
                    "session_id": completed_session["session_id"],
                    "final_results": {
                        "episodes_completed": completed_session["episodes_completed"],
                        "episodes_target": completed_session["episodes_target"],
                        "final_reward": completed_session["current_reward"],
                        "best_reward": completed_session["best_reward"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                response = {
                    "algorithm": algorithm,
                    "status": "not_running",
                    "is_training": False,
                    "message": f"演算法 '{algorithm}' 目前沒有在訓練中",
                    "session_id": None,
                    "training_progress": None,
                    "metrics": None,
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"📤 [算法狀態] 返回非運行狀態: {response}")
            return response
            
    except Exception as e:
        logger.error(f"獲取算法 {algorithm} 狀態失敗: {e}")
        import traceback
        logger.error(f"異常追蹤: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"獲取算法狀態失敗: {str(e)}")


@router.get("/training/status-summary")
async def get_training_status_summary():
    """獲取訓練狀態摘要，用於前端狀態同步 - 使用統一的 RLTrainingEngine"""
    logger.info("📊 [狀態摘要] 收到前端狀態摘要查詢請求")
    
    try:
        # 使用統一的 RLTrainingEngine 獲取真實狀態
        from ..rl.training_engine import get_training_engine
        
        logger.info("🔧 [狀態摘要] 獲取 RLTrainingEngine...")
        engine = await get_training_engine()
        logger.info("✅ [狀態摘要] RLTrainingEngine 獲取成功")
        
        # 獲取所有活躍會話
        logger.info("📊 [狀態摘要] 調用 engine.get_all_sessions()...")
        sessions_data = engine.get_all_sessions()
        logger.info(f"✅ [狀態摘要] 獲取到 {len(sessions_data)} 個會話")
        
        # 分析會話狀態
        active_algorithms = []
        completed_algorithms = []
        
        for session_data in sessions_data:
            logger.info(f"🔍 [狀態摘要] 處理會話數據: {session_data}")
            logger.info(f"🔍 [狀態摘要] 會話數據鍵: {list(session_data.keys())}")
            
            try:
                algorithm_name = session_data["algorithm_name"]
                status = session_data["status"]
                
                logger.info(f"🔍 [狀態摘要] 檢查會話 {session_data['session_id']}: {algorithm_name} - {status}")
                
                if status in ["active", "queued"]:
                    active_algorithms.append(algorithm_name)
                elif status in ["completed", "stopped"]:
                    completed_algorithms.append(algorithm_name)
            except KeyError as e:
                logger.error(f"❌ [狀態摘要] 缺少鍵 {e} 在會話數據中: {session_data}")
                raise
        
        # 去重
        active_algorithms = list(set(active_algorithms))
        completed_algorithms = list(set(completed_algorithms))
        
        logger.info(f"✅ [狀態摘要] 活躍算法: {active_algorithms}")
        logger.info(f"✅ [狀態摘要] 完成算法: {completed_algorithms}")
        
        # 判斷整體狀態
        has_active_training = len(active_algorithms) > 0
        all_algorithms = ["dqn", "ppo", "sac"]
        all_active = all(alg in active_algorithms for alg in all_algorithms)
        
        logger.info(f"📈 [狀態摘要] 整體狀態 - 有活躍訓練: {has_active_training}, 全部算法活躍: {all_active}")
        
        # 構建算法詳細狀態
        algorithms = {}
        for algorithm in all_algorithms:
            # 查找該算法的最新活躍會話 (包括 queued 和 active 狀態)
            algorithm_session = None
            for session_data in sessions_data:
                logger.info(f"🔍 [狀態摘要] 檢查會話數據: {session_data}")
                if session_data["algorithm_name"] == algorithm and session_data["status"] in ["active", "queued"]:
                    algorithm_session = session_data
                    logger.info(f"✅ [狀態摘要] 找到算法 {algorithm} 的活躍會話")
                    break
            
            if algorithm_session:
                logger.info(f"🔧 [狀態摘要] 構建算法 {algorithm} 的運行狀態")
                try:
                    algorithms[algorithm] = {
                        "algorithm": algorithm,
                        "status": "running",
                        "message": f"演算法 '{algorithm}' 正在訓練中",
                        "is_training": True,
                        "training_progress": {
                            "current_episode": algorithm_session["episodes_completed"],
                            "total_episodes": algorithm_session["episodes_target"],
                            "progress_percentage": (algorithm_session["episodes_completed"] / algorithm_session["episodes_target"] * 100) if algorithm_session["episodes_target"] > 0 else 0,
                            "current_reward": algorithm_session["current_reward"],
                            "best_reward": algorithm_session["best_reward"]
                        },
                        "metrics": {
                            "episodes_completed": algorithm_session["episodes_completed"],
                            "episodes_target": algorithm_session["episodes_target"],
                            "current_reward": algorithm_session["current_reward"],
                            "best_reward": algorithm_session["best_reward"]
                        }
                    }
                    logger.info(f"✅ [狀態摘要] 成功構建算法 {algorithm} 的運行狀態")
                except Exception as e:
                    logger.error(f"❌ [狀態摘要] 構建算法 {algorithm} 狀態時出錯: {e}")
                    logger.error(f"❌ [狀態摘要] 會話數據: {algorithm_session}")
                    raise
            else:
                logger.info(f"🔧 [狀態摘要] 構建算法 {algorithm} 的未運行狀態")
                algorithms[algorithm] = {
                    "algorithm": algorithm,
                    "status": "not_running",
                    "message": f"演算法 '{algorithm}' 目前沒有在訓練中",
                    "is_training": False,
                    "training_progress": None,
                    "metrics": None
                }
        
        status_summary = {
            "algorithms": algorithms,
            "total_algorithms": len(all_algorithms),
            "active_algorithms": active_algorithms,
            "active_count": len(active_algorithms),
            "has_active_training": has_active_training,
            "all_algorithms_active": all_active,
            "completed_algorithms": completed_algorithms,
            "total_active_sessions": len([s for s in sessions_data if s["status"] == "active"]),
            "total_sessions": len(sessions_data),
            "recommended_ui_state": {
                "dqn_button": "stop" if "dqn" in active_algorithms else "start",
                "ppo_button": "stop" if "ppo" in active_algorithms else "start",
                "sac_button": "stop" if "sac" in active_algorithms else "start",
                "all_button": "stop" if has_active_training else "start",
            },
            "timestamp": "2025-07-15T10:00:00Z"  # 固定時間戳以保持一致性
        }
        
        logger.info(f"📤 [狀態摘要] 返回狀態摘要: {status_summary}")
        return status_summary
        
    except Exception as e:
        logger.error(f"獲取訓練狀態摘要失敗: {e}")
        import traceback
        logger.error(f"異常追蹤: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"獲取訓練狀態摘要失敗: {str(e)}")





@router.get("/algorithms")
async def get_available_algorithms():
    """獲取可用算法列表"""
    try:
        manager = await get_ecosystem_manager()
        algorithms = manager.get_registered_algorithms()

        return {"algorithms": algorithms, "count": len(algorithms)}

    except Exception as e:
        logger.error(f"獲取算法列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取算法列表失敗: {str(e)}")


@router.get("/performance/report")
async def get_performance_report(
    algorithms: Optional[str] = Query(None, description="算法列表（逗號分隔）"),
    hours: Optional[int] = Query(24, description="時間窗口（小時）"),
):
    """獲取性能分析報告"""
    try:
        manager = await get_ecosystem_manager()

        algorithm_list = algorithms.split(",") if algorithms else None
        time_window = timedelta(hours=hours) if hours else None

        report = manager.generate_performance_report(algorithm_list, time_window)

        return report

    except Exception as e:
        logger.error(f"獲取性能報告失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取性能報告失敗: {str(e)}")


async def run_training_session(
    manager: Any, session_id: str, algorithm_name: str, episodes: int
):
    """在背景執行訓練會話"""
    try:
        logger.info(f"開始訓練會話: {session_id}")

        # 模擬漸進式訓練過程
        import random
        import math

        if session_id in training_sessions:
            session = training_sessions[session_id]

            # 模擬真實的 RL 訓練過程，每次執行 1 個 episode
            for episode in range(1, episodes + 1):
                if (
                    session_id not in training_sessions
                    or training_sessions[session_id]["status"] != "active"
                ):
                    break

                # 真實的 RL 訓練：每次執行 1 個 episode
                episodes_completed = episode
                progress = episodes_completed / episodes

                # 模擬真實的 RL 訓練獎勵特徵
                # 早期訓練：高方差，低平均獎勵
                # 後期訓練：低方差，高平均獎勵
                base_reward = -50.0  # 起始獎勵
                learning_progress = progress * 400.0  # 學習改善

                # 方差隨訓練進度減少（早期波動大，後期穩定）
                variance = max(5, 30 * (1 - progress))
                noise = random.uniform(-variance, variance)

                # 偶爾的突破性改善（模擬學習突破）
                breakthrough = 0
                if random.random() < 0.05:  # 5% 機率
                    breakthrough = random.uniform(10, 30)

                current_reward = base_reward + learning_progress + noise + breakthrough

                # 更新最佳獎勵
                if current_reward > session["best_reward"]:
                    session["best_reward"] = current_reward

                # 更新會話數據
                session["episodes_completed"] = episodes_completed
                session["current_reward"] = current_reward

                # 模擬真實的 episode 執行時間
                # 根據訓練進度調整執行時間（早期較慢，後期較快）
                episode_duration = max(0.5, 2.0 * (1 - progress * 0.5))  # 0.5-2秒
                await asyncio.sleep(episode_duration)

            # 訓練完成
            if session_id in training_sessions:
                session["status"] = "completed"
                session["episodes_completed"] = episodes

        logger.info(f"訓練會話完成: {session_id}")

    except Exception as e:
        logger.error(f"訓練會話執行失敗: {session_id}, 錯誤: {e}")
        if session_id in training_sessions:
            training_sessions[session_id]["status"] = "error"


# 健康檢查端點
@router.get("/health")
async def rl_health_check():
    """RL 系統健康檢查"""
    try:
        status = "healthy"
        details = {}

        # 檢查生態系統是否可用
        if ECOSYSTEM_AVAILABLE:
            try:
                manager = await get_ecosystem_manager()
                system_status = manager.get_system_status()
                details["ecosystem_status"] = system_status["status"]
                details["registered_algorithms"] = len(
                    system_status.get("registered_algorithms", [])
                )
            except Exception as e:
                status = "degraded"
                details["ecosystem_error"] = str(e)
        else:
            status = "degraded"
            details["ecosystem_available"] = False

        # 檢查系統資源
        try:
            resources = get_system_resources()
            details["system_resources"] = {
                "cpu_usage": resources.cpu_usage,
                "memory_usage": resources.memory_usage,
                "gpu_available": GPU_AVAILABLE,
            }
        except Exception as e:
            details["resource_error"] = str(e)

        details["active_training_sessions"] = len(
            [s for s in training_sessions.values() if s["status"] == "active"]
        )

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        }

    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


# 在所有其他路由之後添加新的初始化端點


@router.post("/initialize")
async def initialize_rl_system():
    """手動初始化 RL 系統"""
    try:
        logger.info("🚀 手動初始化 RL 系統...")

        # 重置全局管理器
        global ecosystem_manager
        ecosystem_manager = None

        # 重新初始化
        manager = await get_ecosystem_manager()

        if manager and hasattr(manager, "is_initialized") and manager.is_initialized:
            logger.info("✅ RL 系統初始化成功")

            # 獲取系統狀態
            status = manager.get_system_status()

            return {
                "status": "success",
                "message": "RL 系統初始化成功",
                "system_status": status,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            logger.error("❌ RL 系統初始化失敗")
            return {
                "status": "failed",
                "message": "RL 系統初始化失敗",
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"💥 RL 系統初始化過程失敗: {e}")
        return {
            "status": "error",
            "message": f"初始化過程失敗: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }
