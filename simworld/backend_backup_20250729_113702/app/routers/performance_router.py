#!/usr/bin/env python3
"""
SimWorld 性能優化 API 路由器
根據 TODO.md 第17項「系統性能優化」要求設計

提供SimWorld特定的性能優化API端點：
1. 仿真性能指標
2. Sionna 計算優化
3. UAV 位置更新優化
4. 無線通道計算優化
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import asyncio

from app.services.performance_optimizer import simworld_performance_optimizer
from app.models.performance_models import (
    SimulationOptimizationRequest,
    SimulationPerformanceResponse,
    SimulationOptimizationResult,
    SimulationPerformanceSummary,
)

logger = logging.getLogger(__name__)

performance_router = APIRouter(
    prefix="/api/v1/performance", tags=["simulation-performance"]
)


@performance_router.on_event("startup")
async def startup_simworld_optimizer():
    """啟動時初始化SimWorld性能優化器"""
    try:
        await simworld_performance_optimizer.initialize()
        await simworld_performance_optimizer.start_monitoring()
        logger.info("🚀 SimWorld 性能優化器啟動完成")
    except Exception as e:
        logger.error(f"❌ SimWorld 性能優化器啟動失敗: {e}")


@performance_router.on_event("shutdown")
async def shutdown_simworld_optimizer():
    """關閉時停止SimWorld性能優化器"""
    try:
        await simworld_performance_optimizer.stop_monitoring()
        logger.info("🔍 SimWorld 性能優化器已停止")
    except Exception as e:
        logger.error(f"❌ SimWorld 性能優化器停止失敗: {e}")


@performance_router.get("/health", summary="SimWorld性能優化器健康檢查")
async def simulation_performance_health_check():
    """檢查SimWorld性能優化器健康狀態"""
    try:
        summary = simworld_performance_optimizer.get_performance_summary()

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "optimizer_initialized": len(
                    simworld_performance_optimizer._simulation_cache
                )
                > 0,
                "monitoring_active": simworld_performance_optimizer._monitoring_active,
                "metrics_count": len(simworld_performance_optimizer.metrics_history),
                "optimization_count": len(
                    simworld_performance_optimizer.optimization_results
                ),
                "cache_status": summary.get("cache_status", {}),
                "message": "SimWorld 性能優化器運行正常",
            },
        )
    except Exception as e:
        logger.error(f"SimWorld 性能健康檢查失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"SimWorld 性能健康檢查失敗: {str(e)}"
        )


@performance_router.get("/metrics/simulation", summary="獲取仿真性能指標")
async def get_simulation_metrics(
    simulation_type: Optional[str] = None, minutes: int = 10
):
    """
    獲取仿真性能指標

    - simulation_type: 仿真類型 (sionna, uav, wireless 等)
    - minutes: 獲取最近幾分鐘的數據
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        # 過濾仿真指標
        filtered_metrics = [
            m
            for m in simworld_performance_optimizer.metrics_history
            if m.timestamp > cutoff_time
            and (simulation_type is None or m.simulation_type == simulation_type)
        ]

        # 轉換為響應格式
        metrics_data = [
            {
                "name": m.name,
                "value": m.value,
                "unit": m.unit,
                "category": m.category,
                "simulation_type": m.simulation_type,
                "timestamp": m.timestamp.isoformat(),
                "target": m.target,
            }
            for m in filtered_metrics
        ]

        return JSONResponse(
            status_code=200,
            content={
                "simulation_metrics": metrics_data,
                "total_count": len(metrics_data),
                "time_range_minutes": minutes,
                "simulation_type": simulation_type,
            },
        )

    except Exception as e:
        logger.error(f"獲取仿真性能指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取仿真性能指標失敗: {str(e)}")


@performance_router.get("/summary", summary="獲取SimWorld性能摘要")
async def get_simulation_performance_summary():
    """獲取SimWorld性能摘要報告"""
    try:
        summary = simworld_performance_optimizer.get_performance_summary()

        return JSONResponse(
            status_code=200,
            content={
                **summary,
                "component": "simworld",
                "optimization_capabilities": [
                    "sionna_computation",
                    "uav_position_update",
                    "wireless_channel_calculation",
                    "system_resources",
                ],
            },
        )

    except Exception as e:
        logger.error(f"獲取SimWorld性能摘要失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"獲取SimWorld性能摘要失敗: {str(e)}"
        )


@performance_router.post("/optimize/sionna", summary="優化Sionna計算性能")
async def optimize_sionna_computation(background_tasks: BackgroundTasks):
    """觸發Sionna計算性能優化"""
    try:
        logger.info("🔧 觸發 Sionna 計算性能優化")

        result = await simworld_performance_optimizer.optimize_sionna_computation()

        return JSONResponse(
            status_code=200,
            content={
                "success": result.success,
                "optimization_type": "sionna_computation",
                "before_value": result.before_value,
                "after_value": result.after_value,
                "improvement_percent": result.improvement_percent,
                "techniques_applied": result.techniques_applied,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details,
                "message": f"Sionna 計算優化完成，改善: {result.improvement_percent:.1f}%",
            },
        )

    except Exception as e:
        logger.error(f"Sionna 計算優化失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Sionna 計算優化失敗: {str(e)}")


@performance_router.post("/optimize/uav-positions", summary="優化UAV位置更新性能")
async def optimize_uav_position_updates(background_tasks: BackgroundTasks):
    """觸發UAV位置更新性能優化"""
    try:
        logger.info("🚁 觸發 UAV 位置更新性能優化")

        result = await simworld_performance_optimizer.optimize_uav_position_updates()

        return JSONResponse(
            status_code=200,
            content={
                "success": result.success,
                "optimization_type": "uav_position_update",
                "before_value": result.before_value,
                "after_value": result.after_value,
                "improvement_percent": result.improvement_percent,
                "techniques_applied": result.techniques_applied,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details,
                "message": f"UAV 位置更新優化完成，改善: {result.improvement_percent:.1f}%",
            },
        )

    except Exception as e:
        logger.error(f"UAV 位置更新優化失敗: {e}")
        raise HTTPException(status_code=500, detail=f"UAV 位置更新優化失敗: {str(e)}")


@performance_router.post("/optimize/wireless-channel", summary="優化無線通道計算性能")
async def optimize_wireless_channel_calculation(background_tasks: BackgroundTasks):
    """觸發無線通道計算性能優化"""
    try:
        logger.info("📡 觸發無線通道計算性能優化")

        result = (
            await simworld_performance_optimizer.optimize_wireless_channel_calculation()
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": result.success,
                "optimization_type": "wireless_channel_calculation",
                "before_value": result.before_value,
                "after_value": result.after_value,
                "improvement_percent": result.improvement_percent,
                "techniques_applied": result.techniques_applied,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details,
                "message": f"無線通道計算優化完成，改善: {result.improvement_percent:.1f}%",
            },
        )

    except Exception as e:
        logger.error(f"無線通道計算優化失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無線通道計算優化失敗: {str(e)}")


@performance_router.post("/optimize/comprehensive", summary="執行綜合性能優化")
async def run_comprehensive_optimization(background_tasks: BackgroundTasks):
    """執行SimWorld綜合性能優化"""
    try:
        logger.info("🚀 觸發 SimWorld 綜合性能優化")

        result = await simworld_performance_optimizer.run_comprehensive_optimization()

        return JSONResponse(
            status_code=200,
            content={
                "success": "error" not in result,
                "optimization_type": "comprehensive",
                "timestamp": datetime.utcnow().isoformat(),
                "optimization_summary": result,
                "message": f"綜合優化完成，平均改善: {result.get('average_improvement_percent', 0):.1f}%",
            },
        )

    except Exception as e:
        logger.error(f"綜合性能優化失敗: {e}")
        raise HTTPException(status_code=500, detail=f"綜合性能優化失敗: {str(e)}")


@performance_router.get("/cache/status", summary="獲取仿真緩存狀態")
async def get_simulation_cache_status():
    """獲取仿真緩存狀態"""
    try:
        cache_status = {
            "total_cached_items": sum(
                len(cache)
                for cache in simworld_performance_optimizer._simulation_cache.values()
            ),
            "cache_categories": {
                k: len(v)
                for k, v in simworld_performance_optimizer._simulation_cache.items()
            },
            "cache_details": {},
        }

        # 獲取每個緩存類別的詳細信息
        for category, cache in simworld_performance_optimizer._simulation_cache.items():
            if cache:
                # 獲取最近更新的項目
                recent_items = []
                for key, data in list(cache.items())[:5]:  # 只取前5個作為示例
                    if isinstance(data, dict):
                        timestamp_key = next(
                            (k for k in data.keys() if "time" in k.lower()), None
                        )
                        recent_items.append(
                            {
                                "key": key,
                                "last_updated": (
                                    data.get(timestamp_key, "unknown")
                                    if timestamp_key
                                    else "unknown"
                                ),
                            }
                        )

                cache_status["cache_details"][category] = {
                    "size": len(cache),
                    "recent_items": recent_items,
                }

        return JSONResponse(
            status_code=200,
            content={
                "cache_status": cache_status,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "仿真緩存狀態獲取成功",
            },
        )

    except Exception as e:
        logger.error(f"獲取仿真緩存狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取仿真緩存狀態失敗: {str(e)}")


@performance_router.post("/cache/clear", summary="清理仿真緩存")
async def clear_simulation_cache(category: Optional[str] = None, force: bool = False):
    """
    清理仿真緩存

    - category: 要清理的緩存類別 (如果為空則清理所有)
    - force: 是否強制清理（包括最近的緩存）
    """
    try:
        cleared_count = 0

        if category:
            # 清理特定類別
            if category in simworld_performance_optimizer._simulation_cache:
                cleared_count = len(
                    simworld_performance_optimizer._simulation_cache[category]
                )
                simworld_performance_optimizer._simulation_cache[category] = {}
                logger.info(f"清理 {category} 緩存，共 {cleared_count} 項")
            else:
                raise HTTPException(
                    status_code=400, detail=f"未知的緩存類別: {category}"
                )
        else:
            # 清理所有緩存
            for cat in simworld_performance_optimizer._simulation_cache:
                cleared_count += len(
                    simworld_performance_optimizer._simulation_cache[cat]
                )
                simworld_performance_optimizer._simulation_cache[cat] = {}
            logger.info(f"清理所有緩存，共 {cleared_count} 項")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "cleared_count": cleared_count,
                "category": category or "all",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"緩存清理完成，清理了 {cleared_count} 項",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理仿真緩存失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清理仿真緩存失敗: {str(e)}")


@performance_router.get("/targets", summary="獲取SimWorld性能目標")
async def get_simulation_performance_targets():
    """獲取SimWorld性能目標配置"""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "performance_targets": simworld_performance_optimizer.performance_targets,
                "component": "simworld",
                "timestamp": datetime.utcnow().isoformat(),
                "description": "SimWorld 仿真性能目標配置",
                "target_descriptions": {
                    "sionna_computation_ms": "Sionna 無線通道計算時間目標",
                    "uav_position_update_ms": "UAV 位置更新時間目標",
                    "wireless_channel_calc_ms": "無線通道計算時間目標",
                    "websocket_response_ms": "WebSocket 響應時間目標",
                    "simulation_fps": "仿真幀率目標",
                    "data_processing_throughput_mbps": "數據處理吞吐量目標",
                },
            },
        )

    except Exception as e:
        logger.error(f"獲取SimWorld性能目標失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"獲取SimWorld性能目標失敗: {str(e)}"
        )


@performance_router.get("/benchmark", summary="執行SimWorld性能基準測試")
async def run_simulation_benchmark():
    """執行SimWorld性能基準測試"""
    try:
        benchmark_results = {}

        # Sionna 計算基準測試
        sionna_time = (
            await simworld_performance_optimizer._benchmark_sionna_computation()
        )
        benchmark_results["sionna_computation_ms"] = sionna_time

        # UAV 位置更新基準測試
        uav_time = await simworld_performance_optimizer._benchmark_uav_position_update()
        benchmark_results["uav_position_update_ms"] = uav_time

        # 無線通道計算基準測試
        channel_time = (
            await simworld_performance_optimizer._benchmark_wireless_channel_calculation()
        )
        benchmark_results["wireless_channel_calc_ms"] = channel_time

        # 仿真幀率測量
        fps = await simworld_performance_optimizer._measure_simulation_fps()
        benchmark_results["simulation_fps"] = fps

        # 與目標比較
        targets = simworld_performance_optimizer.performance_targets
        comparison = {}
        for metric, value in benchmark_results.items():
            target = targets.get(metric)
            if target:
                if "fps" in metric or "throughput" in metric:
                    meets_target = value >= target
                else:
                    meets_target = value <= target

                comparison[metric] = {
                    "current": value,
                    "target": target,
                    "meets_target": meets_target,
                    "deviation_percent": (
                        ((value - target) / target) * 100 if target > 0 else 0
                    ),
                }

        return JSONResponse(
            status_code=200,
            content={
                "benchmark_results": benchmark_results,
                "target_comparison": comparison,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_metrics": len(benchmark_results),
                    "targets_met": sum(
                        1 for c in comparison.values() if c["meets_target"]
                    ),
                    "overall_performance": (
                        "good"
                        if all(c["meets_target"] for c in comparison.values())
                        else "needs_optimization"
                    ),
                },
                "message": "SimWorld 性能基準測試完成",
            },
        )

    except Exception as e:
        logger.error(f"SimWorld 性能基準測試失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"SimWorld 性能基準測試失敗: {str(e)}"
        )
