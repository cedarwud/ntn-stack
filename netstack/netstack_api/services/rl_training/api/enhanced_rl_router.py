"""
🧠 增強版 RL API 路由器

整合新的 SOLID 架構和現有 FastAPI 路由器，
提供世界級的 RL 系統 API 接口。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json

from ..core.service_locator import ServiceLocator
from ..core.algorithm_factory import AlgorithmFactory
from ..interfaces.rl_algorithm import ScenarioType, TrainingConfig, PredictionContext
from ..interfaces.training_scheduler import TrainingJob, TrainingPriority
from ..interfaces.performance_monitor import MetricType
from ..interfaces.model_manager import ModelMetadata

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1/rl", tags=["強化學習系統"])


# ===== 請求/響應模型 =====

class SystemStatusResponse(BaseModel):
    """系統狀態響應"""
    status: str = Field(description="系統狀態")
    version: str = Field(description="系統版本")
    uptime_seconds: float = Field(description="運行時間")
    available_algorithms: List[str] = Field(description="可用算法列表")
    active_training_jobs: int = Field(description="活躍訓練任務數")
    total_models: int = Field(description="模型總數")
    system_health: Dict[str, Any] = Field(description="系統健康狀態")


class AlgorithmInfoResponse(BaseModel):
    """算法資訊響應"""
    name: str = Field(description="算法名稱")
    version: str = Field(description="版本號")
    supported_scenarios: List[str] = Field(description="支援場景")
    description: str = Field(description="算法描述")
    author: str = Field(description="作者")
    hyperparameters: Dict[str, Any] = Field(description="超參數")
    training_metrics: Dict[str, Any] = Field(description="訓練指標")


class TrainingRequest(BaseModel):
    """訓練請求"""
    algorithm_name: str = Field(description="算法名稱")
    scenario_type: str = Field(default="urban", description="場景類型")
    episodes: int = Field(default=1000, ge=1, le=10000, description="訓練回合數")
    max_steps_per_episode: int = Field(default=1000, ge=1, description="每回合最大步數")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定義配置")
    priority: str = Field(default="normal", description="訓練優先級")
    experiment_name: Optional[str] = Field(None, description="訓練名稱")


class PredictionRequest(BaseModel):
    """預測請求"""
    algorithm_name: str = Field(description="算法名稱")
    scenario_type: str = Field(default="urban", description="場景類型")
    ue_position: Dict[str, float] = Field(description="用戶設備位置")
    satellite_positions: List[Dict[str, Any]] = Field(description="衛星位置列表")
    network_conditions: Dict[str, Any] = Field(description="網路狀況")
    current_serving_satellite: int = Field(description="當前服務衛星ID")
    candidate_satellites: List[int] = Field(description="候選衛星列表")


class TrainingJobResponse(BaseModel):
    """訓練任務響應"""
    job_id: str = Field(description="任務ID")
    algorithm_name: str = Field(description="算法名稱")
    status: str = Field(description="任務狀態")
    progress_percent: float = Field(description="完成進度")
    episodes_completed: int = Field(description="已完成回合數")
    total_episodes: int = Field(description="總回合數")
    current_score: float = Field(description="當前分數")
    estimated_completion: Optional[str] = Field(None, description="預估完成時間")
    created_at: str = Field(description="創建時間")


class PerformanceMetricsResponse(BaseModel):
    """性能指標響應"""
    algorithm_name: str = Field(description="算法名稱")
    scenario_type: str = Field(description="場景類型")
    metrics: Dict[str, Any] = Field(description="性能指標")
    time_range: Dict[str, str] = Field(description="時間範圍")
    statistical_summary: Dict[str, Any] = Field(description="統計摘要")


# ===== 依賴注入 =====

async def get_algorithm_manager():
    """獲取算法管理器依賴"""
    try:
        # 這裡應該從配置管理器獲取，暫時使用工廠模式
        return AlgorithmFactory
    except Exception as e:
        logger.error(f"獲取算法管理器失敗: {e}")
        raise HTTPException(status_code=500, detail="算法管理器不可用")


async def get_training_scheduler():
    """獲取訓練調度器依賴"""
    try:
        return ServiceLocator.get_training_scheduler()
    except Exception as e:
        logger.error(f"獲取訓練調度器失敗: {e}")
        raise HTTPException(status_code=500, detail="訓練調度器不可用")


async def get_performance_monitor():
    """獲取性能監控器依賴"""
    try:
        return ServiceLocator.get_performance_monitor()
    except Exception as e:
        logger.error(f"獲取性能監控器失敗: {e}")
        raise HTTPException(status_code=500, detail="性能監控器不可用")


async def get_model_manager():
    """獲取模型管理器依賴"""
    try:
        return ServiceLocator.get_model_manager()
    except Exception as e:
        logger.error(f"獲取模型管理器失敗: {e}")
        raise HTTPException(status_code=500, detail="模型管理器不可用")


# ===== API 端點 =====

@router.get("/status", response_model=SystemStatusResponse, summary="獲取系統狀態")
async def get_system_status():
    """
    獲取 RL 系統的整體狀態和健康資訊
    
    返回系統運行狀態、可用算法、活躍任務等資訊
    """
    try:
        # 獲取算法資訊
        available_algorithms = AlgorithmFactory.get_available_algorithms()
        registry_stats = AlgorithmFactory.get_registry_stats()
        
        # 獲取服務健康狀態
        health_status = ServiceLocator.get_health_status()
        
        # 獲取訓練任務狀態
        try:
            scheduler = await get_training_scheduler()
            scheduler_status = await scheduler.get_scheduler_status()
            active_jobs = scheduler_status.active_jobs
        except:
            active_jobs = 0
        
        # 獲取模型統計
        try:
            model_manager = await get_model_manager()
            models = await model_manager.list_models()
            total_models = len(models)
        except:
            total_models = 0
        
        return SystemStatusResponse(
            status="healthy" if health_status["status"] == "healthy" else "degraded",
            version="2.0.0",
            uptime_seconds=0.0,  # 計算實際運行時間
            available_algorithms=available_algorithms,
            active_training_jobs=active_jobs,
            total_models=total_models,
            system_health=health_status
        )
        
    except Exception as e:
        logger.error(f"獲取系統狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取系統狀態失敗: {str(e)}")


@router.get("/algorithms", response_model=List[str], summary="獲取可用算法列表")
async def get_available_algorithms():
    """
    獲取所有已註冊的 RL 算法列表
    """
    try:
        algorithms = AlgorithmFactory.get_available_algorithms()
        return algorithms
    except Exception as e:
        logger.error(f"獲取算法列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取算法列表失敗: {str(e)}")


@router.get("/algorithms/{algorithm_name}", response_model=AlgorithmInfoResponse, summary="獲取算法詳細資訊")
async def get_algorithm_info(algorithm_name: str = Path(description="算法名稱")):
    """
    獲取指定算法的詳細資訊，包括版本、支援場景、超參數等
    """
    try:
        algorithm_info = AlgorithmFactory.get_algorithm_info(algorithm_name)
        if not algorithm_info:
            raise HTTPException(status_code=404, detail=f"算法 {algorithm_name} 不存在")
        
        # 嘗試創建算法實例以獲取運行時資訊
        try:
            algorithm = AlgorithmFactory.create_algorithm(algorithm_name, scenario_type=ScenarioType.URBAN)
            hyperparameters = algorithm.get_hyperparameters()
            training_metrics = algorithm.get_training_metrics()
        except:
            hyperparameters = algorithm_info.default_config
            training_metrics = {}
        
        return AlgorithmInfoResponse(
            name=algorithm_info.name,
            version=algorithm_info.version,
            supported_scenarios=[s.value for s in algorithm_info.supported_scenarios],
            description=algorithm_info.description,
            author=algorithm_info.author,
            hyperparameters=hyperparameters,
            training_metrics=training_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取算法資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取算法資訊失敗: {str(e)}")


@router.get("/algorithms/by-scenario/{scenario_type}", response_model=List[str], summary="根據場景獲取算法")
async def get_algorithms_by_scenario(scenario_type: str = Path(description="場景類型")):
    """
    獲取支援指定場景的算法列表
    """
    try:
        scenario = ScenarioType(scenario_type)
        algorithms = AlgorithmFactory.get_algorithms_by_scenario(scenario)
        return algorithms
    except ValueError:
        raise HTTPException(status_code=400, detail=f"無效的場景類型: {scenario_type}")
    except Exception as e:
        logger.error(f"根據場景獲取算法失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取算法失敗: {str(e)}")


@router.post("/training/start", response_model=Dict[str, Any], summary="開始訓練")
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    scheduler = Depends(get_training_scheduler)
):
    """
    啟動 RL 算法訓練任務
    
    支援後台執行，返回任務ID用於追蹤進度
    """
    try:
        # 驗證算法是否存在
        if request.algorithm_name not in AlgorithmFactory.get_available_algorithms():
            raise HTTPException(status_code=400, detail=f"算法 {request.algorithm_name} 不存在")
        
        # 驗證場景類型
        try:
            scenario_type = ScenarioType(request.scenario_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的場景類型: {request.scenario_type}")
        
        # 創建訓練配置
        training_config = TrainingConfig(
            episodes=request.episodes,
            batch_size=request.custom_config.get('batch_size', 32) if request.custom_config else 32,
            learning_rate=request.custom_config.get('learning_rate', 0.001) if request.custom_config else 0.001,
            max_steps_per_episode=request.max_steps_per_episode,
            scenario_type=scenario_type,
            custom_params=request.custom_config or {}
        )
        
        # 創建訓練任務
        training_job = TrainingJob(
            job_id=f"train_{request.algorithm_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            algorithm_name=request.algorithm_name,
            config=training_config,
            priority=TrainingPriority(request.priority.upper()),
            estimated_duration_minutes=request.episodes // 10,  # 粗略估算
        )
        
        # 提交任務到調度器
        job_id = await scheduler.submit_training_job(training_job)
        
        logger.info(f"訓練任務已提交: {job_id}")
        
        return {
            "job_id": job_id,
            "algorithm_name": request.algorithm_name,
            "scenario_type": request.scenario_type,
            "status": "queued",
            "message": "訓練任務已提交到隊列",
            "config": {
                "episodes": request.episodes,
                "max_steps_per_episode": request.max_steps_per_episode,
                "scenario_type": request.scenario_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"開始訓練失敗: {e}")
        raise HTTPException(status_code=500, detail=f"開始訓練失敗: {str(e)}")


@router.get("/training/jobs", response_model=List[TrainingJobResponse], summary="獲取訓練任務列表")
async def get_training_jobs(
    status: Optional[str] = Query(None, description="任務狀態過濾"),
    algorithm: Optional[str] = Query(None, description="算法名稱過濾"),
    limit: int = Query(10, ge=1, le=100, description="返回數量限制"),
    scheduler = Depends(get_training_scheduler)
):
    """
    獲取訓練任務列表，支援狀態和算法過濾
    """
    try:
        # 獲取訓練隊列
        training_queue = await scheduler.get_training_queue()
        
        # 應用過濾器
        filtered_jobs = training_queue
        if status:
            filtered_jobs = [job for job in filtered_jobs if job.status == status]
        if algorithm:
            filtered_jobs = [job for job in filtered_jobs if job.algorithm_name == algorithm]
        
        # 限制數量
        filtered_jobs = filtered_jobs[:limit]
        
        # 轉換為響應格式
        job_responses = []
        for job in filtered_jobs:
            # 獲取任務詳細狀態
            job_status = await scheduler.get_job_status(job.job_id)
            
            job_responses.append(TrainingJobResponse(
                job_id=job.job_id,
                algorithm_name=job.algorithm_name,
                status=job_status.get("status", "unknown"),
                progress_percent=job_status.get("progress", 0.0),
                episodes_completed=job_status.get("episodes_completed", 0),
                total_episodes=job.config.episodes,
                current_score=job_status.get("current_score", 0.0),
                estimated_completion=job_status.get("estimated_completion"),
                created_at=job.created_at.isoformat() if job.created_at else ""
            ))
        
        return job_responses
        
    except Exception as e:
        logger.error(f"獲取訓練任務列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取任務列表失敗: {str(e)}")


@router.get("/training/jobs/{job_id}", response_model=TrainingJobResponse, summary="獲取訓練任務詳情")
async def get_training_job(
    job_id: str = Path(description="任務ID"),
    scheduler = Depends(get_training_scheduler)
):
    """
    獲取指定訓練任務的詳細狀態和進度
    """
    try:
        job_status = await scheduler.get_job_status(job_id)
        if not job_status:
            raise HTTPException(status_code=404, detail=f"任務 {job_id} 不存在")
        
        return TrainingJobResponse(
            job_id=job_id,
            algorithm_name=job_status.get("algorithm_name", "unknown"),
            status=job_status.get("status", "unknown"),
            progress_percent=job_status.get("progress", 0.0),
            episodes_completed=job_status.get("episodes_completed", 0),
            total_episodes=job_status.get("total_episodes", 0),
            current_score=job_status.get("current_score", 0.0),
            estimated_completion=job_status.get("estimated_completion"),
            created_at=job_status.get("created_at", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取訓練任務詳情失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取任務詳情失敗: {str(e)}")


@router.delete("/training/jobs/{job_id}", summary="取消訓練任務")
async def cancel_training_job(
    job_id: str = Path(description="任務ID"),
    scheduler = Depends(get_training_scheduler)
):
    """
    取消指定的訓練任務
    """
    try:
        success = await scheduler.cancel_training_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"任務 {job_id} 不存在或無法取消")
        
        return {"message": f"任務 {job_id} 已取消"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消訓練任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消任務失敗: {str(e)}")


@router.post("/prediction", response_model=Dict[str, Any], summary="執行換手決策預測")
async def predict_handover(request: PredictionRequest):
    """
    執行 LEO 衛星換手決策預測
    
    根據當前網路狀況和衛星位置，預測最佳的換手目標衛星
    """
    try:
        # 驗證算法
        if request.algorithm_name not in AlgorithmFactory.get_available_algorithms():
            raise HTTPException(status_code=400, detail=f"算法 {request.algorithm_name} 不存在")
        
        # 驗證場景類型
        try:
            scenario_type = ScenarioType(request.scenario_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的場景類型: {request.scenario_type}")
        
        # 創建算法實例
        algorithm = AlgorithmFactory.create_algorithm(
            request.algorithm_name,
            scenario_type=scenario_type
        )
        
        # 檢查模型是否已訓練
        if not algorithm.is_trained():
            logger.warning(f"算法 {request.algorithm_name} 尚未訓練，使用預設模型")
        
        # 創建預測上下文
        context = PredictionContext(
            satellite_positions=request.satellite_positions,
            ue_position=request.ue_position,
            network_conditions=request.network_conditions,
            current_serving_satellite=request.current_serving_satellite,
            candidate_satellites=request.candidate_satellites,
            timestamp=datetime.now()
        )
        
        # 執行預測
        decision = await algorithm.predict(context)
        
        # 記錄預測結果（用於監控和分析）
        try:
            performance_monitor = await get_performance_monitor()
            # 可以在這裡記錄預測指標
        except:
            pass
        
        return {
            "algorithm_name": request.algorithm_name,
            "scenario_type": request.scenario_type,
            "prediction": {
                "target_satellite_id": decision.target_satellite_id,
                "confidence_score": decision.confidence_score,
                "estimated_latency_ms": decision.estimated_latency_ms,
                "predicted_throughput_mbps": decision.predicted_throughput_mbps,
                "execution_priority": decision.execution_priority,
                "reasoning": decision.decision_reasoning
            },
            "context": {
                "current_serving_satellite": request.current_serving_satellite,
                "candidate_satellites": request.candidate_satellites,
                "ue_position": request.ue_position
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"預測失敗: {str(e)}")


@router.get("/performance/{algorithm_name}", response_model=PerformanceMetricsResponse, summary="獲取算法性能指標")
async def get_algorithm_performance(
    algorithm_name: str = Path(description="算法名稱"),
    scenario_type: Optional[str] = Query(None, description="場景類型"),
    time_range_hours: int = Query(24, ge=1, le=168, description="時間範圍（小時）"),
    performance_monitor = Depends(get_performance_monitor)
):
    """
    獲取指定算法的性能指標和統計資訊
    """
    try:
        # 驗證算法
        if algorithm_name not in AlgorithmFactory.get_available_algorithms():
            raise HTTPException(status_code=400, detail=f"算法 {algorithm_name} 不存在")
        
        # 設置時間範圍
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # 轉換場景類型
        scenario = None
        if scenario_type:
            try:
                scenario = ScenarioType(scenario_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無效的場景類型: {scenario_type}")
        
        # 獲取性能摘要
        metric_types = [MetricType.REWARD, MetricType.LATENCY, MetricType.THROUGHPUT, MetricType.SUCCESS_RATE]
        performance_summary = await performance_monitor.get_performance_summary(
            algorithm_name=algorithm_name,
            metric_types=metric_types,
            scenario_type=scenario,
            time_range=(start_time, end_time)
        )
        
        # 轉換為響應格式
        metrics = {}
        statistical_summary = {}
        
        for metric_type, summary in performance_summary.items():
            metrics[metric_type.value] = {
                "count": summary.count,
                "mean": summary.mean,
                "current_value": summary.mean  # 簡化處理
            }
            statistical_summary[metric_type.value] = {
                "std": summary.std,
                "min": summary.min_value,
                "max": summary.max_value,
                "median": summary.percentile_50,
                "p95": summary.percentile_95
            }
        
        return PerformanceMetricsResponse(
            algorithm_name=algorithm_name,
            scenario_type=scenario_type or "all",
            metrics=metrics,
            time_range={
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": time_range_hours
            },
            statistical_summary=statistical_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取性能指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取性能指標失敗: {str(e)}")


@router.get("/performance/compare", summary="比較算法性能")
async def compare_algorithms(
    algorithms: str = Query(description="算法名稱列表，逗號分隔"),
    scenario_type: Optional[str] = Query(None, description="場景類型"),
    metric_types: str = Query("reward,latency,success_rate", description="比較指標，逗號分隔"),
    performance_monitor = Depends(get_performance_monitor)
):
    """
    比較多個算法的性能指標
    """
    try:
        # 解析參數
        algorithm_names = [name.strip() for name in algorithms.split(",")]
        metric_type_list = []
        
        for metric_name in metric_types.split(","):
            try:
                metric_type_list.append(MetricType(metric_name.strip()))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無效的指標類型: {metric_name}")
        
        # 驗證算法
        available_algorithms = AlgorithmFactory.get_available_algorithms()
        for algorithm_name in algorithm_names:
            if algorithm_name not in available_algorithms:
                raise HTTPException(status_code=400, detail=f"算法 {algorithm_name} 不存在")
        
        # 轉換場景類型
        scenario = None
        if scenario_type:
            try:
                scenario = ScenarioType(scenario_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無效的場景類型: {scenario_type}")
        
        # 比較算法
        comparison_results = await performance_monitor.compare_algorithms(
            algorithm_names=algorithm_names,
            metric_types=metric_type_list,
            scenario_type=scenario
        )
        
        return {
            "algorithms": algorithm_names,
            "scenario_type": scenario_type or "all",
            "metrics": [mt.value for mt in metric_type_list],
            "comparison_results": comparison_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"算法比較失敗: {e}")
        raise HTTPException(status_code=500, detail=f"算法比較失敗: {str(e)}")


@router.get("/models", summary="獲取模型列表")
async def get_models(
    algorithm_type: Optional[str] = Query(None, description="算法類型過濾"),
    limit: int = Query(10, ge=1, le=100, description="返回數量限制"),
    model_manager = Depends(get_model_manager)
):
    """
    獲取已註冊的模型列表
    """
    try:
        models = await model_manager.list_models(
            algorithm_name=algorithm_type,
            limit=limit
        )
        
        return {
            "models": [
                {
                    "model_id": model.model_id,
                    "algorithm_name": model.algorithm_name,
                    "version": model.version,
                    "validation_score": model.validation_metrics.get("score", 0.0),
                    "created_at": model.created_at.isoformat(),
                    "tags": model.tags
                }
                for model in models
            ],
            "total": len(models),
            "algorithm_filter": algorithm_type
        }
        
    except Exception as e:
        logger.error(f"獲取模型列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取模型列表失敗: {str(e)}")


@router.get("/health", summary="健康檢查")
async def health_check():
    """
    系統健康檢查端點
    """
    try:
        health_status = ServiceLocator.get_health_status()
        
        return {
            "status": health_status["status"],
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "components": health_status.get("core_services", {}),
            "uptime": health_status.get("container", {}).get("initialization_time")
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )