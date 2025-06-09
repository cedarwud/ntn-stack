"""
Fine-Grained Synchronized Algorithm API
提供二點預測和 Binary Search Refinement 的 REST API
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
import logging
import asyncio
import time

from ..services.fine_grained_sync_service import FineGrainedSyncService
from ..models.handover_models import (
    HandoverPredictionRequest,
    HandoverPredictionResponse,
    BinarySearchIteration
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/handover/fine-grained", tags=["Fine-Grained Sync"])

# 全局服務實例
fine_grained_service = FineGrainedSyncService()

@router.post("/prediction", response_model=HandoverPredictionResponse)
async def execute_two_point_prediction(
    request: HandoverPredictionRequest,
    background_tasks: BackgroundTasks
):
    """
    執行二點預測算法
    根據 IEEE INFOCOM 2024 論文實現 Fine-Grained Synchronized Algorithm
    """
    try:
        logger.info(f"收到二點預測請求 - UE: {request.ue_id}")
        
        # 模擬 UE 位置 (在實際系統中應從設備管理服務獲取)
        ue_position = (24.7866, 120.9966, 100.0)  # 新竹地區示例座標
        
        # 執行二點預測
        prediction_result = await fine_grained_service.two_point_prediction(
            str(request.ue_id), ue_position
        )
        
        binary_search_result = None
        handover_trigger_time = None
        
        if prediction_result.handover_needed:
            # 如果需要換手，執行 Binary Search Refinement
            handover_time, iterations = await fine_grained_service.binary_search_refinement(
                str(request.ue_id),
                ue_position,
                prediction_result.current_time,
                prediction_result.future_time
            )
            
            handover_trigger_time = handover_time
            binary_search_result = {
                "handover_time": handover_time,
                "iterations": [iteration.dict() for iteration in iterations],
                "iteration_count": len(iterations),
                "final_precision": iterations[-1].precision if iterations else 0.0
            }
        
        # 準備響應
        response = HandoverPredictionResponse(
            prediction_id=f"pred_{request.ue_id}_{int(time.time())}",
            ue_id=request.ue_id,
            current_time=prediction_result.current_time,
            future_time=prediction_result.future_time,
            delta_t_seconds=fine_grained_service.delta_t,
            current_satellite={
                "satellite_id": prediction_result.current_satellite,
                "name": f"Satellite-{prediction_result.current_satellite}",
                "signal_strength": -65.0,  # 示例值
                "elevation": 45.0
            },
            future_satellite={
                "satellite_id": prediction_result.predicted_satellite,
                "name": f"Satellite-{prediction_result.predicted_satellite}",
                "signal_strength": -70.0,  # 示例值
                "elevation": 40.0
            },
            handover_required=prediction_result.handover_needed,
            handover_trigger_time=handover_trigger_time,
            binary_search_result=binary_search_result,
            prediction_confidence=prediction_result.confidence,
            accuracy_percentage=prediction_result.confidence * 100
        )
        
        # 在背景任務中更新預測記錄
        background_tasks.add_task(
            fine_grained_service.update_prediction_record,
            str(request.ue_id),
            ue_position
        )
        
        logger.info(f"二點預測完成 - UE: {request.ue_id}, 需要換手: {prediction_result.handover_needed}")
        
        return response
        
    except Exception as e:
        logger.error(f"二點預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"預測執行失敗: {str(e)}")


@router.get("/prediction/{ue_id}")
async def get_prediction_record(ue_id: int):
    """
    獲取 UE 的最新預測記錄
    """
    try:
        record = fine_grained_service.get_prediction_record(str(ue_id))
        
        if not record:
            raise HTTPException(status_code=404, detail=f"UE {ue_id} 的預測記錄不存在")
        
        return {
            "ue_id": record.ue_id,
            "current_satellite": record.current_satellite,
            "predicted_satellite": record.predicted_satellite,
            "handover_time": record.handover_time,
            "prediction_confidence": record.prediction_confidence,
            "last_updated": record.last_updated
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取預測記錄失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


@router.post("/binary-search/{ue_id}")
async def execute_binary_search_refinement(
    ue_id: int,
    t_start: float,
    t_end: float,
    precision_threshold: float = 0.1
):
    """
    執行 Binary Search Refinement 精確計算換手時間
    """
    try:
        logger.info(f"執行 Binary Search Refinement - UE: {ue_id}")
        
        # 模擬 UE 位置
        ue_position = (24.7866, 120.9966, 100.0)
        
        # 臨時設置精度門檻
        original_threshold = fine_grained_service.precision_threshold
        fine_grained_service.precision_threshold = precision_threshold
        
        try:
            handover_time, iterations = await fine_grained_service.binary_search_refinement(
                str(ue_id), ue_position, t_start, t_end
            )
        finally:
            # 恢復原始門檻
            fine_grained_service.precision_threshold = original_threshold
        
        return {
            "ue_id": ue_id,
            "handover_time": handover_time,
            "t_start": t_start,
            "t_end": t_end,
            "precision_threshold": precision_threshold,
            "iterations": [iteration.dict() for iteration in iterations],
            "iteration_count": len(iterations),
            "final_precision": iterations[-1].precision if iterations else 0.0
        }
        
    except Exception as e:
        logger.error(f"Binary Search Refinement 失敗: {e}")
        raise HTTPException(status_code=500, detail=f"精確計算失敗: {str(e)}")


@router.post("/continuous-prediction/{ue_id}/start")
async def start_continuous_prediction(
    ue_id: int,
    background_tasks: BackgroundTasks
):
    """
    啟動連續預測模式
    """
    try:
        logger.info(f"啟動 UE {ue_id} 的連續預測模式")
        
        # 模擬 UE 位置
        ue_position = (24.7866, 120.9966, 100.0)
        
        # 在背景任務中啟動連續預測
        background_tasks.add_task(
            fine_grained_service.start_continuous_prediction,
            str(ue_id),
            ue_position
        )
        
        return {
            "ue_id": ue_id,
            "status": "started",
            "prediction_interval_seconds": fine_grained_service.delta_t,
            "message": f"連續預測已啟動，每 {fine_grained_service.delta_t} 秒更新一次"
        }
        
    except Exception as e:
        logger.error(f"啟動連續預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動失敗: {str(e)}")


@router.get("/algorithm-config")
async def get_algorithm_config():
    """
    獲取算法配置參數
    """
    return {
        "delta_t_seconds": fine_grained_service.delta_t,
        "precision_threshold": fine_grained_service.precision_threshold,
        "max_iterations": fine_grained_service.max_iterations,
        "min_elevation_threshold": fine_grained_service.min_elevation_threshold,
        "algorithm_name": "Fine-Grained Synchronized Algorithm",
        "paper_reference": "IEEE INFOCOM 2024 - Accelerating Handover in Mobile Satellite Network"
    }


@router.put("/algorithm-config")
async def update_algorithm_config(
    delta_t_seconds: Optional[int] = None,
    precision_threshold: Optional[float] = None,
    max_iterations: Optional[int] = None,
    min_elevation_threshold: Optional[float] = None
):
    """
    更新算法配置參數
    """
    try:
        updated_params = {}
        
        if delta_t_seconds is not None:
            fine_grained_service.delta_t = delta_t_seconds
            updated_params["delta_t_seconds"] = delta_t_seconds
        
        if precision_threshold is not None:
            fine_grained_service.precision_threshold = precision_threshold
            updated_params["precision_threshold"] = precision_threshold
        
        if max_iterations is not None:
            fine_grained_service.max_iterations = max_iterations
            updated_params["max_iterations"] = max_iterations
        
        if min_elevation_threshold is not None:
            fine_grained_service.min_elevation_threshold = min_elevation_threshold
            updated_params["min_elevation_threshold"] = min_elevation_threshold
        
        logger.info(f"算法配置已更新: {updated_params}")
        
        return {
            "status": "updated",
            "updated_parameters": updated_params,
            "current_config": await get_algorithm_config()
        }
        
    except Exception as e:
        logger.error(f"更新算法配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"配置更新失敗: {str(e)}")


@router.get("/performance-metrics")
async def get_performance_metrics():
    """
    獲取算法性能指標
    """
    try:
        # 計算基本性能指標
        cached_records = len(fine_grained_service.prediction_cache)
        
        # 計算平均置信度
        total_confidence = 0.0
        handover_required_count = 0
        
        for record in fine_grained_service.prediction_cache.values():
            total_confidence += record.prediction_confidence
            if record.handover_time is not None:
                handover_required_count += 1
        
        avg_confidence = total_confidence / cached_records if cached_records > 0 else 0.0
        
        return {
            "active_predictions": cached_records,
            "average_confidence": round(avg_confidence, 3),
            "handover_rate": round(handover_required_count / cached_records * 100, 2) if cached_records > 0 else 0.0,
            "algorithm_efficiency": {
                "prediction_interval": fine_grained_service.delta_t,
                "search_precision": fine_grained_service.precision_threshold,
                "max_search_iterations": fine_grained_service.max_iterations
            },
            "target_accuracy": ">95%",
            "current_accuracy": f"{avg_confidence * 100:.1f}%"
        }
        
    except Exception as e:
        logger.error(f"獲取性能指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"指標計算失敗: {str(e)}")