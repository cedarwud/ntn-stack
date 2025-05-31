#!/usr/bin/env python3
"""
NetStack 性能優化 API 路由器
根據 TODO.md 第17項「系統性能優化」要求設計

提供性能優化相關的 API 端點：
1. 性能指標查詢
2. 優化操作觸發
3. 性能報告生成
4. 實時監控控制
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import structlog
from datetime import datetime, timedelta
import asyncio

from netstack_api.services.performance_optimizer import performance_optimizer
from netstack_api.models.performance_models import (
    PerformanceOptimizationRequest,
    PerformanceMetricsResponse,
    OptimizationResultResponse,
    PerformanceSummaryResponse,
)

logger = structlog.get_logger(__name__)

performance_router = APIRouter(prefix="/api/v1/performance", tags=["performance"])


@performance_router.on_event("startup")
async def startup_performance_optimizer():
    """啟動時初始化性能優化器"""
    try:
        await performance_optimizer.initialize()
        await performance_optimizer.start_monitoring()
        logger.info("🚀 性能優化器啟動完成")
    except Exception as e:
        logger.error(f"❌ 性能優化器啟動失敗: {e}")


@performance_router.on_event("shutdown")
async def shutdown_performance_optimizer():
    """關閉時停止性能優化器"""
    try:
        await performance_optimizer.stop_monitoring()
        logger.info("🔍 性能優化器已停止")
    except Exception as e:
        logger.error(f"❌ 性能優化器停止失敗: {e}")


@performance_router.get("/health", summary="性能優化器健康檢查")
async def performance_health_check():
    """檢查性能優化器健康狀態"""
    try:
        summary = performance_optimizer.get_performance_summary()

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "optimizer_initialized": performance_optimizer.cache_manager
                is not None,
                "monitoring_active": performance_optimizer._monitoring_active,
                "metrics_count": len(performance_optimizer.metrics_history),
                "optimization_count": len(performance_optimizer.optimization_results),
                "message": "性能優化器運行正常",
            },
        )
    except Exception as e:
        logger.error(f"性能健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"性能健康檢查失敗: {str(e)}")


@performance_router.get(
    "/metrics", response_model=PerformanceMetricsResponse, summary="獲取性能指標"
)
async def get_performance_metrics(category: Optional[str] = None, minutes: int = 10):
    """
    獲取性能指標

    - category: 指標類別 (api, system 等)
    - minutes: 獲取最近幾分鐘的數據
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        # 過濾指標
        filtered_metrics = [
            m
            for m in performance_optimizer.metrics_history
            if m.timestamp > cutoff_time
            and (category is None or m.category == category)
        ]

        # 轉換為響應格式
        metrics_data = [
            {
                "name": m.name,
                "value": m.value,
                "unit": m.unit,
                "category": m.category,
                "timestamp": m.timestamp.isoformat(),
                "target": m.target,
            }
            for m in filtered_metrics
        ]

        return PerformanceMetricsResponse(
            metrics=metrics_data,
            total_count=len(metrics_data),
            time_range_minutes=minutes,
            category=category,
        )

    except Exception as e:
        logger.error(f"獲取性能指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取性能指標失敗: {str(e)}")


@performance_router.get(
    "/summary", response_model=PerformanceSummaryResponse, summary="獲取性能摘要"
)
async def get_performance_summary():
    """獲取性能摘要報告"""
    try:
        summary = performance_optimizer.get_performance_summary()

        return PerformanceSummaryResponse(
            timestamp=summary.get("timestamp"),
            total_optimizations=summary.get("total_optimizations", 0),
            successful_optimizations=summary.get("successful_optimizations", 0),
            current_metrics=summary.get("current_metrics", {}),
            targets_status=summary.get("targets_status", {}),
            status="active" if performance_optimizer._monitoring_active else "inactive",
        )

    except Exception as e:
        logger.error(f"獲取性能摘要失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取性能摘要失敗: {str(e)}")


@performance_router.post(
    "/optimize", response_model=OptimizationResultResponse, summary="觸發性能優化"
)
async def trigger_optimization(
    request: PerformanceOptimizationRequest, background_tasks: BackgroundTasks
):
    """
    觸發性能優化操作

    - optimization_type: 優化類型 (auto, api_response, memory, cpu 等)
    - force: 是否強制執行優化
    """
    try:
        optimization_type = request.optimization_type
        force = request.force

        logger.info(f"🔧 觸發性能優化: {optimization_type}")

        if optimization_type == "auto" or optimization_type == "comprehensive":
            # 運行完整優化循環
            result = await performance_optimizer.run_optimization_cycle()

            return OptimizationResultResponse(
                success=True,
                optimization_type=optimization_type,
                timestamp=datetime.utcnow().isoformat(),
                results=result.get("results", []),
                summary=result.get("analysis", {}),
                message=f"自動優化完成，應用了 {len(result.get('results', []))} 項優化",
            )

        elif optimization_type == "api_response":
            # 針對 API 響應時間的特定優化
            techniques = []

            # 預熱緩存
            await performance_optimizer._warm_cache_for_endpoint("/api/v1/uav")
            await performance_optimizer._warm_cache_for_endpoint("/api/v1/satellite")
            techniques.append("cache_warming")

            # 垃圾回收
            import gc

            gc.collect()
            techniques.append("garbage_collection")

            return OptimizationResultResponse(
                success=True,
                optimization_type=optimization_type,
                timestamp=datetime.utcnow().isoformat(),
                results=[
                    {
                        "optimization_type": "api_response_manual",
                        "techniques_applied": techniques,
                        "success": True,
                    }
                ],
                summary={"manual_optimization": True},
                message=f"API 響應優化完成，應用技術: {', '.join(techniques)}",
            )

        elif optimization_type == "memory":
            # 內存優化
            import gc
            import psutil

            before_memory = psutil.virtual_memory().percent
            gc.collect()
            await asyncio.sleep(1)
            after_memory = psutil.virtual_memory().percent

            improvement = (
                ((before_memory - after_memory) / before_memory) * 100
                if before_memory > 0
                else 0
            )

            return OptimizationResultResponse(
                success=True,
                optimization_type=optimization_type,
                timestamp=datetime.utcnow().isoformat(),
                results=[
                    {
                        "optimization_type": "memory_cleanup",
                        "before_value": before_memory,
                        "after_value": after_memory,
                        "improvement_percent": improvement,
                        "success": improvement > 0,
                    }
                ],
                summary={"memory_optimization": True},
                message=f"內存優化完成，改善: {improvement:.1f}%",
            )

        else:
            raise HTTPException(
                status_code=400, detail=f"不支持的優化類型: {optimization_type}"
            )

    except Exception as e:
        logger.error(f"性能優化執行失敗: {e}")
        raise HTTPException(status_code=500, detail=f"性能優化執行失敗: {str(e)}")


@performance_router.post("/monitoring/start", summary="開始性能監控")
async def start_performance_monitoring():
    """開始性能監控"""
    try:
        if performance_optimizer._monitoring_active:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "already_active",
                    "message": "性能監控已經處於活動狀態",
                },
            )

        await performance_optimizer.start_monitoring()

        return JSONResponse(
            status_code=200,
            content={
                "status": "started",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "性能監控已開始",
            },
        )

    except Exception as e:
        logger.error(f"啟動性能監控失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動性能監控失敗: {str(e)}")


@performance_router.post("/monitoring/stop", summary="停止性能監控")
async def stop_performance_monitoring():
    """停止性能監控"""
    try:
        if not performance_optimizer._monitoring_active:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "already_inactive",
                    "message": "性能監控已經處於非活動狀態",
                },
            )

        await performance_optimizer.stop_monitoring()

        return JSONResponse(
            status_code=200,
            content={
                "status": "stopped",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "性能監控已停止",
            },
        )

    except Exception as e:
        logger.error(f"停止性能監控失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止性能監控失敗: {str(e)}")


@performance_router.get("/optimization-history", summary="獲取優化歷史")
async def get_optimization_history(limit: int = 20):
    """獲取優化操作歷史"""
    try:
        # 獲取最近的優化結果
        recent_results = (
            performance_optimizer.optimization_results[-limit:]
            if performance_optimizer.optimization_results
            else []
        )

        history_data = [
            {
                "optimization_type": result.optimization_type,
                "before_value": result.before_value,
                "after_value": result.after_value,
                "improvement_percent": result.improvement_percent,
                "success": result.success,
                "timestamp": result.timestamp.isoformat(),
                "techniques_applied": result.techniques_applied,
            }
            for result in recent_results
        ]

        return JSONResponse(
            status_code=200,
            content={
                "optimization_history": history_data,
                "total_count": len(performance_optimizer.optimization_results),
                "shown_count": len(history_data),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"獲取優化歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取優化歷史失敗: {str(e)}")


@performance_router.get("/targets", summary="獲取性能目標")
async def get_performance_targets():
    """獲取性能目標配置"""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "performance_targets": performance_optimizer.performance_targets,
                "timestamp": datetime.utcnow().isoformat(),
                "description": "系統性能目標配置",
            },
        )

    except Exception as e:
        logger.error(f"獲取性能目標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取性能目標失敗: {str(e)}")


@performance_router.middleware("http")
async def performance_middleware(request: Request, call_next):
    """性能測量中間件"""
    if request.url.path.startswith("/api/v1/performance"):
        # 不對性能API自身進行測量，避免遞歸
        response = await call_next(request)
        return response

    # 對其他API進行性能測量
    async with performance_optimizer.measure_request_performance(request):
        response = await call_next(request)

    return response
