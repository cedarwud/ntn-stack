"""
重構後的測試 API 路由
使用模組化服務架構
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from .services.test_execution_service import TestExecutionService
from .services.health_check_service import HealthCheckService
from .models.test_models import (
    ComprehensiveTestResult,
    SystemRecommendation,
    TestFrameworkConfig,
    PriorityLevel,
    TestStatus,
)

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter()

# 初始化服務
test_execution_service = TestExecutionService()
health_check_service = HealthCheckService()


@router.get("/frameworks", summary="獲取可用的測試框架")
async def get_test_frameworks():
    """
    獲取所有可用的測試框架列表
    
    Returns:
        Dict: 可用的測試框架信息
    """
    try:
        frameworks = test_execution_service.get_available_frameworks()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": frameworks,
                "total_frameworks": len(frameworks),
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"獲取測試框架列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{framework_id}", summary="執行指定的測試框架")
async def execute_test_framework(
    framework_id: str,
    background_tasks: BackgroundTasks,
    execution_time: int = Query(120, description="執行時間（秒）", ge=10, le=600)
):
    """
    執行指定的測試框架
    
    Args:
        framework_id: 測試框架 ID
        execution_time: 執行時間（秒）
        
    Returns:
        Dict: 測試執行結果
    """
    try:
        logger.info(f"開始執行測試框架: {framework_id}")
        
        # 執行測試框架
        result = await test_execution_service.execute_test_framework(
            framework_id, execution_time
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "message": f"測試框架 {framework_id} 執行完成",
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    except ValueError as e:
        logger.error(f"測試框架參數錯誤: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"執行測試框架失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", summary="批次執行測試框架")
async def execute_batch_tests(
    framework_ids: List[str],
    execution_time: int = Query(120, description="每個測試的執行時間（秒）", ge=10, le=600)
):
    """
    批次執行多個測試框架
    
    Args:
        framework_ids: 測試框架 ID 列表
        execution_time: 每個測試的執行時間
        
    Returns:
        Dict: 批次測試結果
    """
    try:
        if not framework_ids:
            raise HTTPException(status_code=400, detail="測試框架列表不能為空")
        
        logger.info(f"開始批次執行測試: {framework_ids}")
        
        # 執行批次測試
        result = await test_execution_service.run_batch_tests(
            framework_ids, execution_time
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "message": f"批次測試完成，共 {len(framework_ids)} 個框架",
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    except Exception as e:
        logger.error(f"批次測試執行失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="系統健康檢查")
async def system_health_check():
    """
    執行系統健康檢查
    
    Returns:
        Dict: 系統健康狀態
    """
    try:
        logger.info("開始執行系統健康檢查")
        
        # 執行綜合健康檢查
        health_result = await health_check_service.perform_comprehensive_health_check()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": health_result,
                "message": "健康檢查完成",
            }
        )
        
    except Exception as e:
        logger.error(f"系統健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/containers", summary="容器健康檢查")
async def container_health_check():
    """
    檢查容器健康狀態
    
    Returns:
        Dict: 容器健康狀態
    """
    try:
        container_health = await health_check_service.check_container_health()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": container_health.dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    except Exception as e:
        logger.error(f"容器健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/api", summary="API 性能檢查")
async def api_performance_check():
    """
    檢查 API 性能狀態
    
    Returns:
        Dict: API 性能狀態
    """
    try:
        api_performance = await health_check_service.check_api_performance()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": api_performance.dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    except Exception as e:
        logger.error(f"API 性能檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/database", summary="資料庫健康檢查")
async def database_health_check():
    """
    檢查資料庫健康狀態
    
    Returns:
        Dict: 資料庫健康狀態
    """
    try:
        db_performance = await health_check_service.check_database_performance()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": db_performance.dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    except Exception as e:
        logger.error(f"資料庫健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/satellite", summary="衛星處理檢查")
async def satellite_processing_check():
    """
    檢查衛星處理功能
    
    Returns:
        Dict: 衛星處理狀態
    """
    try:
        satellite_processing = await health_check_service.check_satellite_processing()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": satellite_processing.dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    except Exception as e:
        logger.error(f"衛星處理檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/system", summary="系統性能指標")
async def get_system_metrics():
    """
    獲取系統性能指標
    
    Returns:
        Dict: 系統性能指標
    """
    try:
        system_metrics = await health_check_service.get_system_metrics()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": system_metrics.dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    except Exception as e:
        logger.error(f"獲取系統指標失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", summary="系統優化建議")
async def get_system_recommendations():
    """
    獲取基於當前系統狀態的優化建議
    
    Returns:
        Dict: 系統優化建議
    """
    try:
        # 獲取綜合健康檢查結果
        health_result = await health_check_service.perform_comprehensive_health_check()
        
        # 生成建議
        recommendations = generate_system_recommendations(health_result)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "recommendations": [rec.dict() for rec in recommendations],
                    "total_recommendations": len(recommendations),
                    "health_summary": {
                        "overall_health": health_result.get("overall_health"),
                        "health_score": health_result.get("health_score"),
                    },
                },
                "timestamp": datetime.now().isoformat(),
            }
        )
        
    except Exception as e:
        logger.error(f"獲取系統建議失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_system_recommendations(health_data: Dict[str, Any]) -> List[SystemRecommendation]:
    """
    基於健康檢查結果生成系統優化建議
    
    Args:
        health_data: 健康檢查數據
        
    Returns:
        List[SystemRecommendation]: 系統建議列表
    """
    recommendations = []
    
    # 分析容器健康狀態
    container_health = health_data.get("container_health", {})
    if container_health.get("health_percentage", 0) < 100:
        recommendations.append(SystemRecommendation(
            category="容器管理",
            priority=PriorityLevel.HIGH,
            message="部分容器狀態異常，建議檢查容器日誌並重啟異常容器",
            action="docker logs <container_name> && docker restart <container_name>"
        ))
    
    # 分析 API 性能
    api_performance = health_data.get("api_performance", {})
    avg_response = api_performance.get("avg_response_time_ms", 0)
    if avg_response > 1000:
        recommendations.append(SystemRecommendation(
            category="API性能",
            priority=PriorityLevel.MEDIUM,
            message=f"API平均回應時間 {avg_response}ms 較高，建議優化代碼或增加資源",
            action="檢查API端點實現並考慮添加快取機制"
        ))
    
    # 分析系統資源
    system_metrics = health_data.get("system_metrics", {})
    cpu_usage = system_metrics.get("cpu", {}).get("usage_percent", 0)
    memory_usage = system_metrics.get("memory", {}).get("usage_percent", 0)
    
    if cpu_usage > 80:
        recommendations.append(SystemRecommendation(
            category="系統資源",
            priority=PriorityLevel.HIGH,
            message=f"CPU使用率 {cpu_usage}% 過高，建議優化算法或增加運算資源",
            action="監控CPU密集型進程並考慮橫向擴展"
        ))
    
    if memory_usage > 80:
        recommendations.append(SystemRecommendation(
            category="系統資源",
            priority=PriorityLevel.HIGH,
            message=f"記憶體使用率 {memory_usage}% 過高，建議檢查記憶體洩漏或增加記憶體",
            action="分析記憶體使用模式並優化資料結構"
        ))
    
    # 如果一切正常
    if not recommendations:
        recommendations.append(SystemRecommendation(
            category="系統狀態",
            priority=PriorityLevel.INFO,
            message="系統運行狀態良好，所有指標正常",
            action="繼續監控系統性能指標"
        ))
    
    return recommendations