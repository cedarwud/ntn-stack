#!/usr/bin/env python3
"""
管道驗證 API 端點
==============================
為六階段數據預處理系統提供驗證狀態 REST API

Author: NTN Stack Team
Version: 1.0.0
Date: 2025-09-04

端點列表:
- GET /api/v1/pipeline/validation/stage/{stage_number}  - 獲取特定階段驗證狀態
- GET /api/v1/pipeline/validation/summary             - 獲取管道驗證總覽
- GET /api/v1/pipeline/statistics                    - 獲取管道統計信息（兼容性）
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1", tags=["pipeline", "validation"])

# 驗證快照目錄 - 智能選擇
import os
if os.path.exists("/app"):
    VALIDATION_SNAPSHOTS_DIR = Path("/app/data/validation_snapshots")
else:
    VALIDATION_SNAPSHOTS_DIR = Path("/home/sat/ntn-stack/data/leo_outputs/validation_snapshots")


@router.get("/pipeline/validation/stage/{stage_number}")
async def get_stage_validation(stage_number: int) -> JSONResponse:
    """
    獲取特定階段的驗證狀態
    
    Args:
        stage_number: 階段編號 (1-6)
        
    Returns:
        階段驗證狀態 JSON
        
    Raises:
        HTTPException: 階段編號無效或階段未執行
    """
    if not (1 <= stage_number <= 6):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid stage number: {stage_number}. Must be between 1 and 6."
        )
    
    snapshot_file = VALIDATION_SNAPSHOTS_DIR / f"stage{stage_number}_validation.json"
    
    if not snapshot_file.exists():
        logger.warning(f"Stage {stage_number} validation snapshot not found: {snapshot_file}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Stage not executed",
                "stage": stage_number,
                "message": f"Validation snapshot for Stage {stage_number} does not exist",
                "suggestion": "Execute the processing pipeline first"
            }
        )
    
    try:
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
        
        logger.info(f"✅ Loaded validation data for Stage {stage_number}")
        return JSONResponse(content=validation_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in validation snapshot for Stage {stage_number}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Invalid validation data",
                "stage": stage_number,
                "message": "Validation snapshot file is corrupted"
            }
        )
    except Exception as e:
        logger.error(f"❌ Error loading validation data for Stage {stage_number}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "stage": stage_number,
                "message": str(e)
            }
        )


@router.get("/pipeline/validation/summary")
async def get_pipeline_validation_summary() -> JSONResponse:
    """
    獲取整個管道的驗證總覽
    
    Returns:
        管道驗證總覽 JSON，包含所有階段狀態
    """
    stages = []
    
    for stage_num in range(1, 7):
        snapshot_file = VALIDATION_SNAPSHOTS_DIR / f"stage{stage_num}_validation.json"
        
        if snapshot_file.exists():
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                stages.append({
                    "stage": stage_num,
                    "stageName": data.get("stageName", f"階段 {stage_num}"),
                    "status": data.get("status", "unknown"),
                    "passed": data.get("validation", {}).get("passed", False),
                    "timestamp": data.get("timestamp"),
                    "duration_seconds": data.get("duration_seconds", 0),
                    "checks_passed": data.get("validation", {}).get("passedChecks", 0),
                    "checks_total": data.get("validation", {}).get("totalChecks", 0),
                    "keyMetrics": data.get("keyMetrics", {}),
                    "nextStage": data.get("nextStage", {})
                })
                
            except Exception as e:
                logger.error(f"❌ Error reading Stage {stage_num} snapshot: {e}")
                stages.append({
                    "stage": stage_num,
                    "stageName": f"階段 {stage_num}",
                    "status": "error",
                    "passed": False,
                    "timestamp": None,
                    "duration_seconds": 0,
                    "checks_passed": 0,
                    "checks_total": 0,
                    "keyMetrics": {},
                    "error_message": str(e)
                })
        else:
            stages.append({
                "stage": stage_num,
                "stageName": f"階段 {stage_num}",
                "status": "not_executed",
                "passed": False,
                "timestamp": None,
                "duration_seconds": 0,
                "checks_passed": 0,
                "checks_total": 0,
                "keyMetrics": {}
            })
    
    # 計算管道健康度
    executed_stages = [s for s in stages if s["status"] not in ["not_executed", "error"]]
    successful_stages = [s for s in executed_stages if s["passed"]]
    failed_stages = [s for s in executed_stages if not s["passed"]]
    
    if len(executed_stages) == 0:
        pipeline_health = "not_started"
    elif len(failed_stages) > 0:
        pipeline_health = "degraded"
    elif len(executed_stages) < 6:
        pipeline_health = "partial"
    else:
        pipeline_health = "healthy"
    
    # 計算總處理時間和成功率
    total_duration = sum(s["duration_seconds"] for s in executed_stages)
    success_rate = (len(successful_stages) / max(len(executed_stages), 1)) * 100
    
    summary = {
        "metadata": {
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "analyzer_version": "pipeline_validation_api_v1.0.0",
            "snapshots_directory": str(VALIDATION_SNAPSHOTS_DIR)
        },
        "stages": stages,
        "summary": {
            "total_stages": 6,
            "executed_stages": len(executed_stages),
            "successful_stages": len(successful_stages),
            "failed_stages": len(failed_stages),
            "not_executed_stages": 6 - len(executed_stages),
            "pipeline_health": pipeline_health,
            "success_rate": round(success_rate, 1),
            "total_processing_time": total_duration,
            "average_stage_time": round(total_duration / max(len(executed_stages), 1), 2)
        },
        "healthStatus": {
            "status": pipeline_health,
            "message": _get_health_message(pipeline_health, len(successful_stages), len(failed_stages)),
            "recommendations": _get_health_recommendations(pipeline_health, failed_stages)
        }
    }
    
    logger.info(f"📊 Pipeline validation summary generated: {pipeline_health}")
    return JSONResponse(content=summary)


@router.get("/pipeline/statistics")
async def get_pipeline_statistics() -> JSONResponse:
    """
    獲取管道統計信息（為前端兼容性提供的端點）
    
    Returns:
        管道統計信息，格式與前端 SatelliteVisibilitySimplified.tsx 兼容
    """
    logger.info("📊 Generating pipeline statistics (compatibility endpoint)")
    
    # 重用驗證總覽的邏輯
    validation_summary_response = await get_pipeline_validation_summary()
    validation_data = json.loads(validation_summary_response.body)
    
    # 轉換為前端期望的格式
    stages_statistics = []
    data_flow = []
    
    for stage_data in validation_data["stages"]:
        stage_num = stage_data["stage"]
        key_metrics = stage_data.get("keyMetrics", {})
        
        # 提取衛星數量信息
        if "輸入TLE數量" in key_metrics:
            total_satellites = key_metrics["輸入TLE數量"]
            starlink_count = key_metrics.get("Starlink衛星", 0)
            oneweb_count = key_metrics.get("OneWeb衛星", 0)
        elif "輸入衛星" in key_metrics:
            total_satellites = key_metrics["輸出衛星"]  # Stage 2 輸出作為總數
            starlink_count = key_metrics.get("Starlink篩選", 0)
            oneweb_count = key_metrics.get("OneWeb篩選", 0)
        else:
            total_satellites = 0
            starlink_count = 0
            oneweb_count = 0
        
        stages_statistics.append({
            "stage": stage_num,
            "stage_name": stage_data["stageName"],
            "status": "success" if stage_data["passed"] else ("failed" if stage_data["status"] != "not_executed" else "no_data"),
            "total_satellites": total_satellites,
            "starlink_count": starlink_count,
            "oneweb_count": oneweb_count,
            "processing_time": f"{stage_data['duration_seconds']}秒" if stage_data.get("duration_seconds") else None,
            "last_updated": stage_data.get("timestamp")
        })
        
        # 添加到數據流
        if stage_data["status"] != "not_executed" and total_satellites > 0:
            data_flow.append({
                "stage": stage_num,
                "satellites": total_satellites,
                "starlink": starlink_count,
                "oneweb": oneweb_count
            })
    
    # 計算最終輸出
    final_output = data_flow[-1]["satellites"] if data_flow else 0
    
    # 計算數據保留率
    initial_input = data_flow[0]["satellites"] if data_flow else 0
    data_retention_rate = (final_output / max(initial_input, 1)) * 100 if initial_input > 0 else 0
    
    statistics = {
        "metadata": {
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "analyzer_version": "pipeline_statistics_api_v1.0.0"
        },
        "stages": stages_statistics,
        "summary": {
            "total_stages": 6,
            "successful_stages": len([s for s in stages_statistics if s["status"] == "success"]),
            "failed_stages": len([s for s in stages_statistics if s["status"] == "failed"]),
            "no_data_stages": len([s for s in stages_statistics if s["status"] == "no_data"]),
            "data_flow": data_flow,
            "final_output": final_output,
            "pipeline_health": validation_data["summary"]["pipeline_health"],
            "data_retention_rate": round(data_retention_rate, 1),
            "data_loss_rate": round(100 - data_retention_rate, 1)
        }
    }
    
    logger.info(f"📈 Pipeline statistics generated: {len(data_flow)} stages with data")
    return JSONResponse(content=statistics)


def _get_health_message(health_status: str, successful: int, failed: int) -> str:
    """獲取健康狀態消息"""
    if health_status == "healthy":
        return f"所有 6 個階段成功完成，管道運行正常"
    elif health_status == "degraded":
        return f"{successful} 個階段成功，{failed} 個階段失敗，需要檢查失敗階段"
    elif health_status == "partial":
        return f"{successful} 個階段已執行，管道部分完成"
    elif health_status == "not_started":
        return "管道尚未開始執行"
    else:
        return "管道狀態未知"


def _get_health_recommendations(health_status: str, failed_stages: List[Dict]) -> List[str]:
    """獲取健康改善建議"""
    recommendations = []
    
    if health_status == "not_started":
        recommendations.append("執行 LEO 預處理管道以開始數據處理")
        recommendations.append("確保 TLE 數據可用且格式正確")
    
    elif health_status == "degraded":
        recommendations.append("檢查失敗階段的錯誤日誌")
        recommendations.append("驗證輸入數據的完整性和格式")
        for stage in failed_stages:
            recommendations.append(f"修復階段 {stage['stage']} 的問題")
    
    elif health_status == "partial":
        recommendations.append("繼續執行剩餘的管道階段")
        recommendations.append("檢查系統資源是否充足")
    
    return recommendations


# 健康檢查端點
@router.get("/pipeline/health")
async def get_pipeline_health() -> JSONResponse:
    """
    快速健康檢查端點
    
    Returns:
        簡化的管道健康狀態
    """
    try:
        summary_response = await get_pipeline_validation_summary()
        summary_data = json.loads(summary_response.body)
        
        health_status = summary_data["summary"]["pipeline_health"]
        executed_stages = summary_data["summary"]["executed_stages"]
        successful_stages = summary_data["summary"]["successful_stages"]
        
        return JSONResponse(content={
            "status": health_status,
            "healthy": health_status == "healthy",
            "executed_stages": executed_stages,
            "successful_stages": successful_stages,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            status_code=500
        )


# 批量操作端點
@router.get("/pipeline/validation/stages")
async def get_all_stages_validation() -> JSONResponse:
    """
    批量獲取所有階段的詳細驗證數據
    
    Returns:
        所有階段的完整驗證數據
    """
    all_stages = {}
    
    for stage_num in range(1, 7):
        try:
            stage_response = await get_stage_validation(stage_num)
            all_stages[f"stage{stage_num}"] = json.loads(stage_response.body)
        except HTTPException:
            all_stages[f"stage{stage_num}"] = {
                "stage": stage_num,
                "status": "not_executed",
                "error": "Stage not executed or validation snapshot missing"
            }
    
    return JSONResponse(content={
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_stages": 6,
            "available_stages": len([s for s in all_stages.values() if "error" not in s])
        },
        "stages": all_stages
    })


# 清理端點（開發/調試用）
@router.delete("/pipeline/validation/cleanup")
async def cleanup_validation_snapshots() -> JSONResponse:
    """
    清理所有驗證快照（開發/調試用）
    
    Warning: 此端點將刪除所有驗證快照文件
    """
    try:
        deleted_files = []
        
        if VALIDATION_SNAPSHOTS_DIR.exists():
            for snapshot_file in VALIDATION_SNAPSHOTS_DIR.glob("stage*_validation.json"):
                snapshot_file.unlink()
                deleted_files.append(str(snapshot_file))
        
        logger.warning(f"🗑️ Validation snapshots cleanup: {len(deleted_files)} files deleted")
        
        return JSONResponse(content={
            "message": "Validation snapshots cleaned up",
            "deleted_files": deleted_files,
            "count": len(deleted_files),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Cleanup failed",
                "message": str(e)
            }
        )