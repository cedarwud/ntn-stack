"""
🧠 RL 訓練管理路由器

基於新的 RL 資料庫模型，提供完整的 RL 訓練管理 API，包括：
- 訓練會話管理 (CRUD)
- 訓練回合記錄
- 算法效能分析
- 模型版本管理
- 超參數配置管理
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path
from pydantic import BaseModel, Field

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
    RLHyperparameterConfig,
    TrainingSessionResponse,
    TrainingEpisodeResponse,
    AlgorithmPerformanceResponse,
    ModelVersionResponse,
    StartTrainingRequest,
    UpdateTrainingRequest,
    CreateModelVersionRequest,
    HyperparameterConfigRequest,
)

# 嘗試導入算法生態系統組件
try:
    from ..algorithm_ecosystem import AlgorithmEcosystemManager

    ECOSYSTEM_AVAILABLE = True
except ImportError:
    ECOSYSTEM_AVAILABLE = False
    AlgorithmEcosystemManager = None

# 導入訓練編排器
from ..services.rl_training.core.training_orchestrator import TrainingOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["RL 訓練管理"])

# 記憶體存儲（在實際部署中應該使用資料庫）
training_sessions_store: Dict[str, RLTrainingSession] = {}
training_episodes_store: Dict[str, List[RLTrainingEpisode]] = {}
algorithm_performance_store: Dict[str, RLAlgorithmPerformance] = {}
model_versions_store: Dict[str, RLModelVersion] = {}
hyperparameter_configs_store: Dict[str, RLHyperparameterConfig] = {}

# 全局算法生態系統管理器
ecosystem_manager: Optional[Any] = None

# 全局訓練編排器（單例模式）
training_orchestrator: Optional[TrainingOrchestrator] = None


async def get_ecosystem_manager():
    """獲取算法生態系統管理器"""
    global ecosystem_manager
    if ecosystem_manager is None and ECOSYSTEM_AVAILABLE:
        try:
            from ..algorithm_ecosystem import AlgorithmEcosystemManager

            ecosystem_manager = AlgorithmEcosystemManager()
            await ecosystem_manager.initialize()
        except Exception as e:
            logger.warning(f"無法初始化算法生態系統管理器: {e}")
    return ecosystem_manager

async def get_training_orchestrator() -> TrainingOrchestrator:
    """獲取訓練編排器（單例模式）"""
    global training_orchestrator
    if training_orchestrator is None:
        training_orchestrator = TrainingOrchestrator()
        logger.info("訓練編排器已初始化")
    return training_orchestrator


def generate_id(prefix: str = "") -> str:
    """生成唯一 ID"""
    return f"{prefix}{uuid.uuid4().hex[:8]}"


# ===== 訓練會話管理 =====


@router.post("/sessions", response_model=TrainingSessionResponse)
async def create_training_session(request: StartTrainingRequest):
    """創建新的訓練會話"""
    try:
        # 生成會話 ID
        session_id = generate_id("session_")

        # 創建訓練會話
        session = RLTrainingSession(
            session_id=session_id,
            algorithm_type=request.algorithm_type,
            environment_type=request.environment_type,
            total_episodes=request.total_episodes,
            max_steps_per_episode=request.max_steps_per_episode,
            hyperparameters=request.hyperparameters or {},
            notes=request.notes,
        )

        # 存儲會話
        training_sessions_store[session_id] = session
        training_episodes_store[session_id] = []

        logger.info(f"創建訓練會話: {session_id} (算法: {request.algorithm_type})")

        return TrainingSessionResponse(
            session_id=session.session_id,
            algorithm_type=session.algorithm_type,
            environment_type=session.environment_type,
            status=session.status,
            progress=0.0,
            episodes_completed=session.episodes_completed,
            total_episodes=session.total_episodes,
            current_reward=session.current_reward,
            best_reward=session.best_reward,
            start_time=session.start_time,
        )

    except Exception as e:
        logger.error(f"創建訓練會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建訓練會話失敗: {str(e)}")


@router.get("/sessions", response_model=List[TrainingSessionResponse])
async def get_training_sessions(
    status: Optional[TrainingStatus] = Query(None, description="按狀態篩選"),
    algorithm: Optional[AlgorithmType] = Query(None, description="按算法篩選"),
    limit: int = Query(50, ge=1, le=100, description="返回結果數量限制"),
):
    """獲取訓練會話列表"""
    try:
        sessions = list(training_sessions_store.values())

        # 按狀態篩選
        if status:
            sessions = [s for s in sessions if s.status == status]

        # 按算法篩選
        if algorithm:
            sessions = [s for s in sessions if s.algorithm_type == algorithm]

        # 按開始時間排序（最新的在前）
        sessions.sort(key=lambda x: x.start_time, reverse=True)

        # 限制結果數量
        sessions = sessions[:limit]

        # 轉換為響應模型
        response_sessions = []
        for session in sessions:
            progress = (
                (session.episodes_completed / session.total_episodes) * 100
                if session.total_episodes > 0
                else 0
            )
            duration = None
            if session.end_time:
                duration = (session.end_time - session.start_time).total_seconds()

            response_sessions.append(
                TrainingSessionResponse(
                    session_id=session.session_id,
                    algorithm_type=session.algorithm_type,
                    environment_type=session.environment_type,
                    status=session.status,
                    progress=progress,
                    episodes_completed=session.episodes_completed,
                    total_episodes=session.total_episodes,
                    current_reward=session.current_reward,
                    best_reward=session.best_reward,
                    start_time=session.start_time,
                    duration_seconds=duration,
                )
            )

        return response_sessions

    except Exception as e:
        logger.error(f"獲取訓練會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取訓練會話失敗: {str(e)}")


@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_training_session(session_id: str = Path(..., description="訓練會話 ID")):
    """獲取特定訓練會話詳情"""
    try:
        if session_id not in training_sessions_store:
            raise HTTPException(
                status_code=404, detail=f"訓練會話 '{session_id}' 不存在"
            )

        session = training_sessions_store[session_id]
        progress = (
            (session.episodes_completed / session.total_episodes) * 100
            if session.total_episodes > 0
            else 0
        )
        duration = None
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds()

        return TrainingSessionResponse(
            session_id=session.session_id,
            algorithm_type=session.algorithm_type,
            environment_type=session.environment_type,
            status=session.status,
            progress=progress,
            episodes_completed=session.episodes_completed,
            total_episodes=session.total_episodes,
            current_reward=session.current_reward,
            best_reward=session.best_reward,
            start_time=session.start_time,
            duration_seconds=duration,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取訓練會話詳情失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取訓練會話詳情失敗: {str(e)}")


@router.put("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def update_training_session(
    session_id: str = Path(..., description="訓練會話 ID"),
    request: UpdateTrainingRequest = None,
):
    """更新訓練會話"""
    try:
        if session_id not in training_sessions_store:
            raise HTTPException(
                status_code=404, detail=f"訓練會話 '{session_id}' 不存在"
            )

        session = training_sessions_store[session_id]

        # 更新狀態
        if request and request.status:
            session.status = request.status
            if request.status == TrainingStatus.COMPLETED:
                session.end_time = datetime.now()

        # 更新備註
        if request and request.notes:
            session.notes = request.notes

        progress = (
            (session.episodes_completed / session.total_episodes) * 100
            if session.total_episodes > 0
            else 0
        )
        duration = None
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds()

        logger.info(f"更新訓練會話: {session_id} (狀態: {session.status})")

        return TrainingSessionResponse(
            session_id=session.session_id,
            algorithm_type=session.algorithm_type,
            environment_type=session.environment_type,
            status=session.status,
            progress=progress,
            episodes_completed=session.episodes_completed,
            total_episodes=session.total_episodes,
            current_reward=session.current_reward,
            best_reward=session.best_reward,
            start_time=session.start_time,
            duration_seconds=duration,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新訓練會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新訓練會話失敗: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_training_session(
    session_id: str = Path(..., description="訓練會話 ID")
):
    """刪除訓練會話"""
    try:
        if session_id not in training_sessions_store:
            raise HTTPException(
                status_code=404, detail=f"訓練會話 '{session_id}' 不存在"
            )

        session = training_sessions_store[session_id]

        # 檢查是否為活躍狀態
        if session.status == TrainingStatus.ACTIVE:
            raise HTTPException(
                status_code=409,
                detail=f"無法刪除活躍的訓練會話。請先停止訓練會話 '{session_id}'",
            )

        # 刪除相關數據
        del training_sessions_store[session_id]
        if session_id in training_episodes_store:
            del training_episodes_store[session_id]

        logger.info(f"刪除訓練會話: {session_id}")

        return {"message": f"訓練會話 '{session_id}' 已刪除", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除訓練會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除訓練會話失敗: {str(e)}")


# ===== 訓練會話控制 =====


@router.post("/sessions/{session_id}/start", response_model=None)
async def start_training_session(
    session_id: str = Path(..., description="訓練會話 ID"),
    background_tasks: BackgroundTasks = None,
    force: bool = Query(False, description="強制啟動，即使有衝突也繼續"),
) -> Dict[str, Any]:
    """開始訓練會話"""
    try:
        if session_id not in training_sessions_store:
            raise HTTPException(
                status_code=404, detail=f"訓練會話 '{session_id}' 不存在"
            )

        session = training_sessions_store[session_id]

        if session.status == TrainingStatus.ACTIVE:
            raise HTTPException(
                status_code=409, detail=f"訓練會話 '{session_id}' 已在運行中"
            )

        # 獲取訓練編排器
        orchestrator = await get_training_orchestrator()
        
        # 檢查互斥鎖狀態
        active_info = await orchestrator.get_active_algorithm_info()
        if active_info and not force:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "training_conflict",
                    "message": f"算法 '{active_info['active_algorithm']}' 正在運行中",
                    "active_algorithm": active_info['active_algorithm'],
                    "active_session_id": active_info['active_session_id'],
                    "suggestion": "使用 force=true 強制啟動或先停止當前訓練"
                }
            )

        # 嘗試在TrainingOrchestrator中創建會話
        try:
            orchestrator_session_id = await orchestrator.create_training_session(
                algorithm=session.algorithm_type.value,
                experiment_name=f"API_Session_{session_id}",
                total_episodes=session.total_episodes,
                scenario_type="urban",
                researcher_id="api_user",
                research_notes=session.notes
            )
            
            # 存儲orchestrator會話ID的映射
            session.notes = f"orchestrator_session_id: {orchestrator_session_id}"
            
        except ValueError as e:
            if "正在被其他會話使用" in str(e):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "training_conflict",
                        "message": str(e),
                        "suggestion": "使用 force=true 強制啟動或先停止當前訓練"
                    }
                )
            raise

        # 更新狀態
        session.status = TrainingStatus.ACTIVE
        session.start_time = datetime.now()

        # 在背景啟動訓練
        if background_tasks:
            background_tasks.add_task(run_training_session_with_orchestrator, session_id, orchestrator_session_id)
        else:
            asyncio.create_task(run_training_session_with_orchestrator(session_id, orchestrator_session_id))

        logger.info(f"啟動訓練會話: {session_id} (算法: {session.algorithm_type})")

        return {
            "message": f"訓練會話 '{session_id}' 已啟動",
            "session_id": session_id,
            "algorithm": session.algorithm_type.value,
            "total_episodes": session.total_episodes,
            "orchestrator_session_id": orchestrator_session_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動訓練會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動訓練會話失敗: {str(e)}")


@router.post("/sessions/{session_id}/stop")
async def stop_training_session(session_id: str = Path(..., description="訓練會話 ID")):
    """停止訓練會話"""
    try:
        if session_id not in training_sessions_store:
            raise HTTPException(
                status_code=404, detail=f"訓練會話 '{session_id}' 不存在"
            )

        session = training_sessions_store[session_id]

        if session.status != TrainingStatus.ACTIVE:
            raise HTTPException(
                status_code=409, detail=f"訓練會話 '{session_id}' 不是活躍狀態"
            )

        # 獲取訓練編排器
        orchestrator = await get_training_orchestrator()
        
        # 從備註中提取orchestrator會話ID
        orchestrator_session_id = None
        if session.notes and "orchestrator_session_id:" in session.notes:
            try:
                orchestrator_session_id = int(session.notes.split("orchestrator_session_id: ")[1])
            except (ValueError, IndexError):
                logger.warning(f"無法解析orchestrator會話ID: {session.notes}")
        
        # 停止TrainingOrchestrator中的會話
        if orchestrator_session_id:
            try:
                await orchestrator.stop_training_session(orchestrator_session_id)
            except Exception as e:
                logger.warning(f"停止orchestrator會話失敗: {e}")

        # 更新狀態
        session.status = TrainingStatus.CANCELLED
        session.end_time = datetime.now()

        logger.info(f"停止訓練會話: {session_id}")

        return {
            "message": f"訓練會話 '{session_id}' 已停止",
            "session_id": session_id,
            "episodes_completed": session.episodes_completed,
            "orchestrator_session_id": orchestrator_session_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止訓練會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止訓練會話失敗: {str(e)}")


# ===== 訓練回合管理 =====


@router.get(
    "/sessions/{session_id}/episodes", response_model=List[TrainingEpisodeResponse]
)
async def get_training_episodes(
    session_id: str = Path(..., description="訓練會話 ID"),
    limit: int = Query(100, ge=1, le=1000, description="返回結果數量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """獲取訓練回合列表"""
    try:
        if session_id not in training_sessions_store:
            raise HTTPException(
                status_code=404, detail=f"訓練會話 '{session_id}' 不存在"
            )

        episodes = training_episodes_store.get(session_id, [])

        # 按回合編號排序（最新的在前）
        episodes.sort(key=lambda x: x.episode_number, reverse=True)

        # 分頁
        episodes = episodes[offset : offset + limit]

        # 轉換為響應模型
        response_episodes = []
        for episode in episodes:
            duration = None
            if episode.end_time:
                duration = (episode.end_time - episode.start_time).total_seconds()

            response_episodes.append(
                TrainingEpisodeResponse(
                    episode_id=episode.episode_id,
                    session_id=episode.session_id,
                    episode_number=episode.episode_number,
                    total_reward=episode.total_reward,
                    episode_length=episode.episode_length,
                    success=episode.success,
                    duration_seconds=duration,
                    metrics=episode.metrics,
                )
            )

        return response_episodes

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取訓練回合失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取訓練回合失敗: {str(e)}")


# ===== 算法效能分析 =====


@router.get("/performance", response_model=List[AlgorithmPerformanceResponse])
async def get_algorithm_performance(
    algorithm: Optional[AlgorithmType] = Query(None, description="按算法篩選"),
    environment: Optional[EnvironmentType] = Query(None, description="按環境篩選"),
):
    """獲取算法效能分析"""
    try:
        performances = list(algorithm_performance_store.values())

        # 按算法篩選
        if algorithm:
            performances = [p for p in performances if p.algorithm_type == algorithm]

        # 按環境篩選
        if environment:
            performances = [
                p for p in performances if p.environment_type == environment
            ]

        # 轉換為響應模型
        response_performances = []
        for perf in performances:
            success_rate = (
                perf.successful_sessions / perf.total_sessions
                if perf.total_sessions > 0
                else 0
            )

            response_performances.append(
                AlgorithmPerformanceResponse(
                    algorithm_type=perf.algorithm_type,
                    environment_type=perf.environment_type,
                    total_sessions=perf.total_sessions,
                    success_rate=success_rate,
                    best_reward=perf.best_reward,
                    average_reward=perf.average_reward,
                    average_training_time=perf.average_training_time,
                    handover_success_rate=perf.handover_success_rate,
                    last_updated=perf.last_updated,
                )
            )

        return response_performances

    except Exception as e:
        logger.error(f"獲取算法效能分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取算法效能分析失敗: {str(e)}")


@router.get("/performance-metrics")
async def get_training_performance_metrics():
    """獲取訓練性能指標 - 為前端 RL 監控系統提供"""
    try:
        # 獲取訓練編排器來獲取真實訓練數據
        orchestrator = await get_training_orchestrator()
        
        # 獲取所有活動會話
        active_sessions = orchestrator.active_sessions
        
        # 計算真實的性能指標
        algorithm_metrics = {}
        total_sessions = len(active_sessions)
        completed_sessions = 0
        total_success_rate = 0
        total_stability = 0
        total_rewards = 0
        total_training_time = 0
        session_count = 0
        
        # 分析每個會話的性能
        for session_id, session in active_sessions.items():
            algorithm = session.algorithm
            
            # 初始化算法指標
            if algorithm not in algorithm_metrics:
                algorithm_metrics[algorithm] = {
                    "sessions": 0,
                    "total_episodes": 0,
                    "completed_episodes": 0,
                    "success_rate": 0,
                    "stability": 0,
                    "average_reward": 0,
                    "total_rewards": 0,
                    "training_time": 0
                }
            
            # 獲取會話的性能指標
            metrics = session.performance_metrics
            algorithm_metrics[algorithm]["sessions"] += 1
            algorithm_metrics[algorithm]["total_episodes"] += session.total_episodes
            algorithm_metrics[algorithm]["completed_episodes"] += session.current_episode
            
            # 計算真實的成功率和穩定性
            if metrics:
                success_rate = metrics.get("success_rate", 0)
                average_reward = metrics.get("average_reward", 0)
                last_reward = metrics.get("last_episode_reward", 0)
                
                # 計算穩定性（基於獎勵的一致性）
                stability = min(1.0, max(0.0, 1.0 - abs(last_reward - average_reward) / max(abs(average_reward), 1.0)))
                
                algorithm_metrics[algorithm]["success_rate"] += success_rate
                algorithm_metrics[algorithm]["stability"] += stability
                algorithm_metrics[algorithm]["average_reward"] += average_reward
                algorithm_metrics[algorithm]["total_rewards"] += average_reward
                
                total_success_rate += success_rate
                total_stability += stability
                total_rewards += average_reward
                session_count += 1
            
            # 計算訓練時間
            if session.end_time:
                training_time = (session.end_time - session.start_time).total_seconds()
                algorithm_metrics[algorithm]["training_time"] += training_time
                total_training_time += training_time
                completed_sessions += 1
        
        # 計算平均值
        for algorithm in algorithm_metrics:
            sessions = algorithm_metrics[algorithm]["sessions"]
            if sessions > 0:
                algorithm_metrics[algorithm]["success_rate"] /= sessions
                algorithm_metrics[algorithm]["stability"] /= sessions
                algorithm_metrics[algorithm]["average_reward"] /= sessions
                algorithm_metrics[algorithm]["training_time"] /= sessions
        
        # 計算整體平均指標
        avg_success_rate = total_success_rate / session_count if session_count > 0 else 0
        avg_stability = total_stability / session_count if session_count > 0 else 0
        avg_reward = total_rewards / session_count if session_count > 0 else 0
        avg_training_time = total_training_time / completed_sessions if completed_sessions > 0 else 0
        
        # 構建標準性能指標響應
        return {
            "latency": avg_training_time * 1000,  # 轉換為毫秒
            "success_rate": avg_success_rate,
            "stability": avg_stability,  # 添加穩定性指標
            "throughput": completed_sessions,  # 完成的會話數作為吞吐量
            "error_rate": 1 - avg_success_rate,
            "response_time": avg_training_time,
            "resource_utilization": {
                "cpu": 45.2,  # 模擬 CPU 使用率
                "memory": 68.5  # 模擬記憶體使用率
            },
            "handover_metrics": {
                "success_rate": avg_success_rate,
                "average_time": avg_training_time,
                "total_handovers": total_sessions
            },
            "algorithm_breakdown": {
                algorithm: {
                    "success_rate": metrics["success_rate"],
                    "stability": metrics["stability"],
                    "average_reward": metrics["average_reward"],
                    "total_sessions": metrics["sessions"],
                    "completed_episodes": metrics["completed_episodes"],
                    "total_episodes": metrics["total_episodes"],
                    "training_time": metrics["training_time"]
                } for algorithm, metrics in algorithm_metrics.items()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "total_algorithms": len(algorithm_metrics),
            "active_sessions": len(active_sessions)
        }

    except Exception as e:
        logger.error(f"獲取訓練性能指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取訓練性能指標失敗: {str(e)}")


# ===== 超參數配置管理 =====


@router.post("/hyperparameters", response_model=RLHyperparameterConfig)
async def create_hyperparameter_config(request: HyperparameterConfigRequest):
    """創建超參數配置"""
    try:
        config_id = generate_id("config_")

        config = RLHyperparameterConfig(
            config_id=config_id,
            algorithm_type=request.algorithm_type,
            config_name=request.config_name,
            learning_rate=request.learning_rate,
            batch_size=request.batch_size,
            gamma=request.gamma,
            epsilon=request.epsilon,
            epsilon_min=request.epsilon_min,
            epsilon_decay=request.epsilon_decay,
            hidden_layers=request.hidden_layers,
            activation_function=request.activation_function,
            algorithm_specific_params=request.algorithm_specific_params,
            description=request.description,
        )

        hyperparameter_configs_store[config_id] = config

        logger.info(f"創建超參數配置: {config_id} (算法: {request.algorithm_type})")

        return config

    except Exception as e:
        logger.error(f"創建超參數配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建超參數配置失敗: {str(e)}")


@router.get("/hyperparameters", response_model=List[RLHyperparameterConfig])
async def get_hyperparameter_configs(
    algorithm: Optional[AlgorithmType] = Query(None, description="按算法篩選"),
):
    """獲取超參數配置列表"""
    try:
        configs = list(hyperparameter_configs_store.values())

        # 按算法篩選
        if algorithm:
            configs = [c for c in configs if c.algorithm_type == algorithm]

        # 按創建時間排序（最新的在前）
        configs.sort(key=lambda x: x.created_at, reverse=True)

        return configs

    except Exception as e:
        logger.error(f"獲取超參數配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取超參數配置失敗: {str(e)}")


# ===== 背景訓練任務 =====


async def run_training_session(session_id: str):
    """在背景執行訓練會話"""
    try:
        if session_id not in training_sessions_store:
            logger.error(f"訓練會話不存在: {session_id}")
            return

        session = training_sessions_store[session_id]
        logger.info(f"開始執行訓練會話: {session_id}")

        # 模擬訓練過程
        import random

        for episode in range(1, session.total_episodes + 1):
            # 檢查會話是否仍然活躍
            if session.status != TrainingStatus.ACTIVE:
                break

            # 模擬訓練一個回合
            episode_reward = (
                random.uniform(-100, 200) + (episode / session.total_episodes) * 100
            )
            episode_length = random.randint(50, 500)
            success = episode_reward > 0

            # 創建回合記錄
            episode_record = RLTrainingEpisode(
                episode_id=generate_id("episode_"),
                session_id=session_id,
                episode_number=episode,
                total_reward=episode_reward,
                episode_length=episode_length,
                success=success,
                metrics={
                    "loss": random.uniform(0.1, 2.0),
                    "q_value": random.uniform(-10, 10),
                    "exploration_rate": max(
                        0.01, 1.0 - (episode / session.total_episodes)
                    ),
                },
                handover_count=random.randint(0, 5),
                average_latency=random.uniform(10, 100),
                throughput=random.uniform(50, 200),
                end_time=datetime.now(),
                duration_seconds=random.uniform(1, 10),
            )

            # 存儲回合記錄
            if session_id not in training_episodes_store:
                training_episodes_store[session_id] = []
            training_episodes_store[session_id].append(episode_record)

            # 更新會話統計
            session.episodes_completed = episode
            session.current_reward = episode_reward
            if episode_reward > session.best_reward:
                session.best_reward = episode_reward

            # 模擬訓練時間
            await asyncio.sleep(1)  # 每個回合 1 秒

        # 訓練完成
        if session.status == TrainingStatus.ACTIVE:
            session.status = TrainingStatus.COMPLETED
            session.end_time = datetime.now()

        logger.info(f"訓練會話完成: {session_id}")

    except Exception as e:
        logger.error(f"訓練會話執行失敗: {session_id}, 錯誤: {e}")
        if session_id in training_sessions_store:
            training_sessions_store[session_id].status = TrainingStatus.ERROR

async def run_training_session_with_orchestrator(session_id: str, orchestrator_session_id: int):
    """使用TrainingOrchestrator在背景執行訓練會話"""
    try:
        if session_id not in training_sessions_store:
            logger.error(f"訓練會話不存在: {session_id}")
            return

        session = training_sessions_store[session_id]
        orchestrator = await get_training_orchestrator()
        
        logger.info(f"開始執行訓練會話: {session_id} (orchestrator: {orchestrator_session_id})")

        # 使用TrainingOrchestrator執行訓練
        try:
            final_stats = await orchestrator.run_training_session(
                session_id=orchestrator_session_id,
                algorithm=session.algorithm_type.value,
                enable_streaming=True
            )
            
            # 更新API會話狀態
            session.status = TrainingStatus.COMPLETED
            session.end_time = datetime.now()
            session.episodes_completed = final_stats.get("total_episodes", session.total_episodes)
            session.best_reward = final_stats.get("final_metrics", {}).get("last_episode_reward", 0)
            
            logger.info(f"訓練會話完成: {session_id}")
            
        except Exception as e:
            logger.error(f"訓練會話執行失敗: {session_id}, 錯誤: {e}")
            session.status = TrainingStatus.ERROR
            session.end_time = datetime.now()

    except Exception as e:
        logger.error(f"訓練會話執行失敗: {session_id}, 錯誤: {e}")
        if session_id in training_sessions_store:
            training_sessions_store[session_id].status = TrainingStatus.ERROR


# ===== 統計和監控 =====


@router.get("/stats")
async def get_training_stats():
    """獲取訓練統計信息"""
    try:
        total_sessions = len(training_sessions_store)
        active_sessions = len(
            [
                s
                for s in training_sessions_store.values()
                if s.status == TrainingStatus.ACTIVE
            ]
        )
        completed_sessions = len(
            [
                s
                for s in training_sessions_store.values()
                if s.status == TrainingStatus.COMPLETED
            ]
        )

        # 算法分佈
        algorithm_distribution = {}
        for session in training_sessions_store.values():
            alg = session.algorithm_type.value
            algorithm_distribution[alg] = algorithm_distribution.get(alg, 0) + 1

        # 平均訓練時間
        completed_durations = []
        for session in training_sessions_store.values():
            if session.status == TrainingStatus.COMPLETED and session.end_time:
                duration = (session.end_time - session.start_time).total_seconds()
                completed_durations.append(duration)

        avg_training_time = (
            sum(completed_durations) / len(completed_durations)
            if completed_durations
            else 0
        )

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "success_rate": (
                completed_sessions / total_sessions if total_sessions > 0 else 0
            ),
            "algorithm_distribution": algorithm_distribution,
            "average_training_time_seconds": avg_training_time,
            "total_episodes": sum(
                len(episodes) for episodes in training_episodes_store.values()
            ),
            "available_algorithms": [alg.value for alg in AlgorithmType],
            "available_environments": [env.value for env in EnvironmentType],
        }

    except Exception as e:
        logger.error(f"獲取訓練統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取訓練統計失敗: {str(e)}")


@router.get("/mutex/status")
async def get_mutex_status():
    """獲取互斥鎖狀態"""
    try:
        orchestrator = await get_training_orchestrator()
        active_info = await orchestrator.get_active_algorithm_info()
        
        return {
            "mutex_locked": active_info is not None,
            "active_algorithm": active_info['active_algorithm'] if active_info else None,
            "active_session_id": active_info['active_session_id'] if active_info else None,
            "session_info": active_info['session_info'] if active_info else None,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"獲取互斥鎖狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取互斥鎖狀態失敗: {str(e)}")

@router.post("/mutex/release")
async def force_release_mutex():
    """強制釋放互斥鎖（管理員功能）"""
    try:
        orchestrator = await get_training_orchestrator()
        
        # 獲取當前活動算法信息
        active_info = await orchestrator.get_active_algorithm_info()
        
        if not active_info:
            return {
                "message": "沒有活動的訓練會話需要釋放",
                "timestamp": datetime.now().isoformat(),
            }
        
        # 強制停止當前活動的會話
        await orchestrator.stop_training_session(active_info['active_session_id'])
        
        logger.info(f"強制釋放互斥鎖: {active_info['active_algorithm']} (會話 {active_info['active_session_id']})")
        
        return {
            "message": f"已強制釋放算法 '{active_info['active_algorithm']}' 的互斥鎖",
            "released_algorithm": active_info['active_algorithm'],
            "released_session_id": active_info['active_session_id'],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"強制釋放互斥鎖失敗: {e}")
        raise HTTPException(status_code=500, detail=f"強制釋放互斥鎖失敗: {str(e)}")

@router.get("/health")
async def rl_training_health_check():
    """RL 訓練服務健康檢查"""
    try:
        status = "healthy"
        
        # 獲取互斥鎖狀態
        orchestrator = await get_training_orchestrator()
        active_info = await orchestrator.get_active_algorithm_info()
        
        details = {
            "total_sessions": len(training_sessions_store),
            "active_sessions": len(
                [
                    s
                    for s in training_sessions_store.values()
                    if s.status == TrainingStatus.ACTIVE
                ]
            ),
            "ecosystem_available": ECOSYSTEM_AVAILABLE,
            "mutex_locked": active_info is not None,
            "active_algorithm": active_info['active_algorithm'] if active_info else None,
        }

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "service": "rl_training",
            "details": details,
        }

    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "service": "rl_training",
            "error": str(e),
        }
